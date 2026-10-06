# SPDX-License-Identifier: MIT
# Copyright (c) Schmid Software Solutions (https://schmid-software.de)
"""A fake of the gta.clothing routes the add-on calls, on 127.0.0.1 for tests: device sign-in, token renewal, sign-in
assertions and logout, the link origin's channel manifest, tickets and hosted body, ``/me`` and garment fitting. It only
checks what the tests need to see the add-on handle: the add-on's own requests and each refusal it must explain to the
user.

Garment fitting (:class:`FakeFitService`) follows the website's mock of the link API: the daily ``fit`` allowance of
the account's plan (free 10, Advanced 30, Ultimate 100), one job at a time without a licence, the ``request`` part and
the DCTM mesh read with the service's rules, the body version, cancelling (a job that has not started gives its use
back) and the binary result. Nothing is fitted: a job moves one stage per status request (queued, validating,
transferring, weighting), then answers its result: the positions as sent (moved by ``position_offset``) with every
vertex weighted 255 to one bone chosen by where it is. A request whose ``category`` is ``mock-invalid``,
``mock-timeout``, ``mock-error`` or ``mock-not-on-body`` ends that way instead.

MIT licensed, like dct_link. Standard library only, so the Blender smoke can use it too.
"""

from __future__ import annotations

import base64
import datetime
import json
import math
import os
import re
import secrets
import struct
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, List, Optional, Tuple


def header_pattern(protocol: str) -> "re.Pattern[str]":
    """The X-DCT-Link-Client header of the Blender add-on speaking ``protocol`` (for example "2.0")."""
    return re.compile(r"blender/[0-9]+\.[0-9]+\.[0-9]+\S* \(protocol " + re.escape(protocol)
                      + r"; channel (release|experimental|development)\)")


def _token(prefix: str) -> str:
    return prefix + base64.urlsafe_b64encode(os.urandom(24)).rstrip(b"=").decode()


def _part(obj: Dict[str, Any]) -> str:
    return base64.urlsafe_b64encode(json.dumps(obj).encode()).rstrip(b"=").decode()


def make_jwt() -> str:
    """An opaque access token in three dot-separated parts; the add-on never reads it."""
    return _part({"alg": "none", "typ": "test"}) + "." + _part({"sub": "u1", "jti": os.urandom(4).hex()}) + "." + _token("")


def make_assertion(nonce: str, user: str = "u1") -> str:
    """A stand-in for a sign-in assertion with the claims the add-on checks (audience and nonce); not signed."""
    claims = {"aud": "dct-creator-link-assertion", "sub": user, "nonce": nonce, "jti": secrets.token_hex(8)}
    return _part({"alg": "none", "typ": "test"}) + "." + _part(claims) + ".c2ln"


class FakeLinkApi:
    def __init__(self) -> None:
        api = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args: Any) -> None:
                pass  # quiet

            def do_GET(self) -> None:
                api._handle(self, "GET")

            def do_POST(self) -> None:
                api._handle(self, "POST")

        class Server(ThreadingHTTPServer):
            def handle_error(self, request: Any, client_address: Any) -> None:
                if not isinstance(sys.exc_info()[1], ConnectionError):
                    super().handle_error(request, client_address)  # a client that went away is no failure

        self.server = Server(("127.0.0.1", 0), Handler)
        self.port = self.server.server_address[1]
        self.base_url = f"http://127.0.0.1:{self.port}"
        self.lock = threading.Lock()
        self.requests: List[Dict[str, Any]] = []
        self.devices: Dict[str, Dict[str, Any]] = {}
        self.refresh_tokens: Dict[str, Dict[str, Any]] = {}
        self.access_tokens: List[str] = []
        self.revoked_sessions: set = set()
        self.interval = 1
        self.account_locked = False
        self.assertions: Dict[str, str] = {}
        self.logouts = 0
        self.logout_failure: Optional[int] = None  # an HTTP status for every logout, to test a failed sign-out
        #: The link protocol the add-on must report (the interface screenshots of an older version change it).
        self.protocol = "2.0"
        #: The channel manifest the link origin serves (``None``: 404), the hosted body files of its body version,
        #: whether the account may download the body, and the tickets handed out.
        self.manifest: Optional[Dict[str, Any]] = {"schema": 1, "panel": {"version": "1.2.0"},
                                                   "body": {"version": "2026.10.03.1"}}
        self.body_files: Dict[str, bytes] = {}
        self.body_entitled = True
        self.tickets: List[str] = []
        #: gta.clothing's garment fitting routes and /me, and the access tokens they refuse as expired.
        self.fit = FakeFitService()
        self.expired_access: set = set()
        self.thread = threading.Thread(target=self.server.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True)
        self.thread.start()

    def stop(self) -> None:
        self.server.shutdown()
        self.server.server_close()

    def __enter__(self) -> "FakeLinkApi":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.stop()

    def approve(self, user_code: str) -> bool:
        with self.lock:
            for device in self.devices.values():
                if device["userCode"].replace("-", "") == user_code.replace("-", ""):
                    device["approved"] = True
                    return True
        return False

    def paths(self) -> List[str]:
        with self.lock:
            return [f"{r['method']} {r['path']}" for r in self.requests]

    # ---- request handling ----------------------------------------------------------------------------

    def _tokens(self, session: str) -> Dict[str, Any]:
        refresh = _token("r")
        access = make_jwt()
        self.refresh_tokens[refresh] = {"session": session, "spent": False}
        self.access_tokens.append(access)
        return {"successful": True, "accessToken": access, "tokenType": "Bearer", "expiresIn": 900,
                "refreshToken": refresh, "refreshSessionExpiresAtUtc": "2026-11-01T12:00:00Z", "sessionId": session,
                "user": {"id": "u1", "name": "Durty", "avatarUrl": "https://avatar.example/x.png"},
                "entitlement": {"features": []}}

    def _send_bytes(self, handler: BaseHTTPRequestHandler, data: bytes, content_type: str) -> None:
        handler.send_response(200)
        handler.send_header("Content-Length", str(len(data)))
        handler.send_header("Content-Type", content_type)
        handler.end_headers()
        handler.wfile.write(data)

    def _send(self, handler: BaseHTTPRequestHandler, status: int, body: Any = None) -> None:
        data = json.dumps(body).encode() if body is not None else b""
        handler.send_response(status)
        handler.send_header("Content-Length", str(len(data)))
        handler.send_header("Cache-Control", "no-store")
        handler.end_headers()
        handler.wfile.write(data)

    def _fail(self, handler: BaseHTTPRequestHandler, status: int, code: str, retryable: bool = False) -> None:
        self._send(handler, status, {"successful": False, "failureCode": code, "error": code, "retryable": retryable,
                                     "errorMessage": code})

    def _handle(self, handler: BaseHTTPRequestHandler, method: str) -> None:
        length = int(handler.headers.get("Content-Length") or 0)
        raw = handler.rfile.read(length) if length else b""
        path = handler.path
        headers = {k.lower(): v for k, v in handler.headers.items()}
        if path == "/link/api/me" or path.startswith("/link/api/fit/"):
            with self.lock:
                self.requests.append({"method": method, "path": path, "headers": headers, "body": None})
            if not header_pattern(self.protocol).fullmatch(headers.get("x-dct-link-client", "")):
                return self._fail(handler, 400, "bad_client_header")
            authorization = headers.get("authorization", "")
            token = authorization[7:] if authorization.startswith("Bearer ") else ""
            authorized = token in self.access_tokens and token not in self.expired_access
            answer = self.fit.handle(method, path, headers, raw, authorized)
            if answer is not None:
                status, extra, data = answer
                handler.send_response(status)
                handler.send_header("Content-Length", str(len(data)))
                for name, value in extra.items():
                    handler.send_header(name, value)
                handler.end_headers()
                handler.wfile.write(data)
                return
        body = json.loads(raw) if raw else None
        with self.lock:
            self.requests.append({"method": method, "path": path, "headers": headers, "body": body})
        if not header_pattern(self.protocol).fullmatch(headers.get("x-dct-link-client", "")):
            return self._fail(handler, 400, "bad_client_header")
        if method == "POST" and path == "/link/api/auth/device":
            return self._device(handler, body or {})
        if method == "POST" and path == "/link/api/auth/token":
            return self._token(handler, body or {})
        if method == "POST" and path == "/link/api/auth/logout":
            if self.logout_failure is not None:
                return self._fail(handler, self.logout_failure, "unavailable", retryable=True)
            with self.lock:
                self.logouts += 1
                entry = self.refresh_tokens.get((body or {}).get("refreshToken"))
                if entry:
                    self.revoked_sessions.add(entry["session"])
            return self._send(handler, 204)
        if method == "GET" and path.startswith("/link/manifest/") and path.endswith(".json"):
            if self.manifest is None:
                return self._fail(handler, 404, "not_found")
            return self._send(handler, 200, self.manifest)
        if method == "POST" and path == "/link/panel/ticket":
            return self._ticket(handler, headers, body or {})
        if method == "GET" and path.startswith("/link/assets/body/"):
            return self._body(handler, headers, path[len("/link/assets/body/"):])
        if method == "POST" and path == "/link/api/assertions":
            if self.account_locked:
                return self._fail(handler, 403, "account_locked")
            authorization = headers.get("authorization", "")
            token = authorization[7:] if authorization.startswith("Bearer ") else ""
            if token not in self.access_tokens:
                return self._fail(handler, 401, "session_invalid")
            nonce = (body or {}).get("nonce")
            if not isinstance(nonce, str) or not re.fullmatch(r"[A-Za-z0-9_-]{43}", nonce):
                return self._fail(handler, 400, "invalid_request")
            assertion = make_assertion(nonce)
            with self.lock:
                self.assertions[assertion] = nonce
            return self._send(handler, 200, {"assertion": assertion, "expiresIn": 120})
        self._send(handler, 404)

    def _ticket(self, handler: BaseHTTPRequestHandler, headers: Dict[str, str], body: Dict[str, Any]) -> None:
        authorization = headers.get("authorization", "")
        token = authorization[7:] if authorization.startswith("Bearer ") else ""
        if token not in self.access_tokens:
            return self._fail(handler, 401, "session_invalid")
        panel = (self.manifest or {}).get("panel") or {}
        if body.get("channel") not in ("release", "experimental") or not isinstance(body.get("version"), str):
            return self._fail(handler, 400, "invalid_request")
        if body["version"] != panel.get("version"):
            return self._fail(handler, 426, "plugin_update_required")
        if not self.body_entitled:
            return self._fail(handler, 403, "feature_not_entitled")
        ticket = "v1." + base64.urlsafe_b64encode(os.urandom(40)).rstrip(b"=").decode()
        with self.lock:
            self.tickets.append(ticket)
        self._send(handler, 200, {"ticket": ticket})

    def _body(self, handler: BaseHTTPRequestHandler, headers: Dict[str, str], rest: str) -> None:
        authorization = headers.get("authorization", "")
        ticket = authorization[7:] if authorization.startswith("Ticket ") else ""
        if ticket not in self.tickets:
            return self._fail(handler, 401, "ticket_invalid")
        version, _, name = rest.partition("/")
        if version != ((self.manifest or {}).get("body") or {}).get("version") or name not in self.body_files:
            return self._fail(handler, 404, "not_found")
        self._send_bytes(handler, self.body_files[name], "model/gltf-binary")

    def _device(self, handler: BaseHTTPRequestHandler, body: Dict[str, Any]) -> None:
        if body.get("clientId") != "dct-link-blender" or body.get("protocol") != self.protocol:
            return self._fail(handler, 400, "invalid_request")
        if not re.fullmatch(r"[0-9a-f-]{36}", str(body.get("installId"))):
            return self._fail(handler, 400, "invalid_request")
        code = "".join(secrets.choice("BCDFGHJKLMNPQRSTVWXZ") for _ in range(8))
        device = _token("dev")
        with self.lock:
            self.devices[device] = {"userCode": code[:4] + "-" + code[4:], "approved": False, "used": False}
        self._send(handler, 200, {"deviceCode": device, "userCode": code[:4] + "-" + code[4:],
                                  "verificationUri": self.base_url + "/account/link/",
                                  "verificationUriComplete": self.base_url + "/account/link/?code=" + code,
                                  "expiresIn": 600, "interval": self.interval})

    def _token(self, handler: BaseHTTPRequestHandler, body: Dict[str, Any]) -> None:
        if self.account_locked:
            return self._fail(handler, 403, "account_locked")
        grant = body.get("grantType")
        with self.lock:
            if grant == "device_code":
                device = self.devices.get(body.get("deviceCode"))
                if device is None or device["used"]:
                    return self._fail(handler, 400, "invalid_grant")
                if not device["approved"]:
                    return self._fail(handler, 400, "authorization_pending")
                device["used"] = True
                return self._send(handler, 200, self._tokens(_token("sess")))
            if grant == "refresh_token":
                entry = self.refresh_tokens.get(body.get("refreshToken"))
                if entry is None or entry["session"] in self.revoked_sessions:
                    return self._fail(handler, 401, "session_revoked")
                if entry["spent"]:
                    self.revoked_sessions.add(entry["session"])
                    return self._fail(handler, 401, "session_revoked")
                entry["spent"] = True
                return self._send(handler, 200, self._tokens(entry["session"]))
        self._fail(handler, 400, "unsupported_grant_type")


Answer = Tuple[int, Dict[str, str], bytes]

BODY_VERSION = "1"
PER_DAY = {"free": 10, "advanced": 30, "ultimate": 100}
STAGES = (("validating", 0.05), ("transferring", 0.2), ("weighting", 0.95))
DRAWABLE_TYPES = ("head", "berd", "hair", "uppr", "lowr", "hand", "feet", "teef", "accs", "task", "decl", "jbib")
FITTABLE = ("berd", "uppr", "lowr", "hand", "feet", "teef", "accs", "task", "jbib")
MARKERS = ("pelvis", "chest", "neck", "lShoulder", "lElbow", "lWrist", "rShoulder", "rElbow", "rWrist", "lHip",
           "lKnee", "lAnkle", "rHip", "rKnee", "rAnkle")
CHAINS = (("lShoulder", "lElbow", "lWrist"), ("rShoulder", "rElbow", "rWrist"), ("lHip", "lKnee", "lAnkle"),
          ("rHip", "rKnee", "rAnkle"))
OPTIONS = {"seamWeldMm": (0, 3), "clearanceMm": (0, 20), "maxPushMm": (1, 100), "pushOut": None,
           "matchProportions": None}
BONE_NAMES = {35: "SKEL_Spine0", 36: "SKEL_Spine1", 37: "SKEL_Spine2", 38: "SKEL_Spine3", 40: "SKEL_L_UpperArm",
              69: "SKEL_R_UpperArm", 2: "SKEL_L_Thigh", 14: "SKEL_R_Thigh", 1: "SKEL_Pelvis"}
#: Made-up clearance in millimetres, not measured on anything.
REFERENCE = {
    "top": {"chest": (4.8, 19.1, 31.5, 2140), "back": (6.2, 21.4, 38.0, 2210), "upperArmL": (5.5, 17.9, 29.3, 1180),
            "upperArmR": (5.5, 17.9, 29.3, 1175)},
    "undershirt": {"chest": (1.9, 6.4, 11.7, 1820), "back": (2.1, 7.0, 12.9, 1905)},
    "legs": {"pelvis": (3.1, 12.6, 24.8, 1540), "thighL": (4.0, 15.2, 27.7, 980), "thighR": (4.0, 15.2, 27.7, 975)},
    "shoes": {"footL": (1.2, 4.9, 9.8, 610), "footR": (1.2, 4.9, 9.8, 612)},
}
OUTCOMES = {"mock-not-on-body": "notOnBody", "mock-invalid": "invalid", "mock-timeout": "timeout",
            "mock-error": "error"}
RESULT_TYPE = "application/vnd.dct.fit-result"


def _issue(code: str, field: str) -> Dict[str, str]:
    return {"code": code, "message": code, "field": field}


def bone_of(x: float, z: float) -> int:
    """The bone a vertex at (x, y, z) leans on in the fake's result."""
    if z < -0.05:
        return 2 if x >= 0 else 14
    if abs(x) > 0.2 and z > 0.2:
        return 40 if x >= 0 else 69
    if z > 0.4:
        return 38
    if z > 0.3:
        return 37
    if z > 0.2:
        return 36
    return 35 if z > 0.1 else 1


class FakeFitService:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        #: The plan of the signed-in account (free, advanced or ultimate) and whether it may fit at all.
        self.tier = "free"
        self.entitled = True
        #: Fitting switched off (feature_unavailable) or its reference pack missing (fit_unavailable).
        self.enabled = True
        self.available = True
        self.used = 0
        #: The hosted body version the fitting runs on (a request for another is refused).
        self.body_version = BODY_VERSION
        self.jobs: Dict[str, Dict[str, Any]] = {}
        self.uploads: List[Tuple[Dict[str, Any], bytes]] = []
        self.cancels: List[str] = []
        self.position_offset = (0.0, 0.0, 0.0)
        #: The next uploads are answered fit_busy (each takes one).
        self.busy = 0
        #: Polls that answer queued before a job starts running.
        self.queued_polls = 0
        #: Answer every request on these paths with (status, failureCode).
        self.refuse: Dict[str, Tuple[int, str]] = {}

    # ---- helpers ------------------------------------------------------------------------------------------

    @staticmethod
    def _json(status: int, body: Any, headers: Optional[Dict[str, str]] = None) -> Answer:
        out = {"Content-Type": "application/json", "Cache-Control": "no-store"}
        out.update(headers or {})
        return status, out, json.dumps(body).encode()

    def _fail(self, status: int, code: str, errors: Optional[List[Dict[str, str]]] = None, retry: Optional[int] = None,
              **extra: Any) -> Answer:
        body: Dict[str, Any] = {"successful": False, "failureCode": code, "retryable": retry is not None,
                                "errorMessage": code}
        if errors:
            body["errors"] = errors
        body.update(extra)
        headers = {"Retry-After": str(retry)} if retry is not None else {}
        if retry is not None:
            body["retryAfterSeconds"] = retry
        return self._json(status, body, headers)

    def per_day(self) -> int:
        return PER_DAY.get(self.tier, PER_DAY["free"])

    def allowance(self) -> Dict[str, Any]:
        return {"perDay": self.per_day(), "usedToday": self.used, "remainingToday": max(0, self.per_day() - self.used),
                "features": ["fit.garment", "fit.weights"]}

    # ---- routes -------------------------------------------------------------------------------------------

    def handle(self, method: str, path: str, headers: Dict[str, str], raw: bytes, authorized: bool) -> Optional[Answer]:
        if path == "/link/api/me" and method == "GET":
            if not authorized:
                return self._fail(401, "session_invalid")
            limits: Dict[str, Any] = {"convertRemainingToday": 20, "quotas": {}, "pools": {}}
            if self.entitled:
                limits["pools"]["fit"] = self.allowance()
            return self._json(200, {"user": {"id": "u1", "name": "Durty", "avatarUrl": None},
                                    "entitlement": {"tier": self.tier if self.tier != "free" else "none",
                                                    "features": ["fit.garment", "fit.weights"] if self.entitled else []},
                                    "limits": limits})
        if not path.startswith("/link/api/fit/") or method != "POST":
            return None
        if path in self.refuse:
            status, code = self.refuse[path]
            return self._fail(status, code, retry=5 if status in (429, 503) else None)
        if not authorized:
            return self._fail(401, "session_invalid")
        if not self.enabled:
            return self._fail(403, "feature_unavailable")
        if not self.entitled:
            return self._fail(403, "feature_not_entitled")
        with self.lock:
            if path == "/link/api/fit/jobs":
                return self._start(headers, raw)
            if path == "/link/api/fit/reference":
                return self._reference(raw)
            body = self._body(raw)
            job_id = body.get("jobId") if isinstance(body, dict) else None
            if not isinstance(job_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]{22}", job_id):
                return self._fail(400, "invalid_request", [_issue("job_id_invalid", "jobId")])
            job = self.jobs.get(job_id)
            if job is None:
                return self._fail(404, "not_found")
            if path == "/link/api/fit/status":
                return self._status(job)
            if path == "/link/api/fit/cancel":
                self.cancels.append(job_id)
                if job["finished"]:
                    del self.jobs[job_id]
                else:
                    if job["state"] == "queued":
                        self._refund(job)
                    job.update(state="cancelled", finished=True)
                return 204, {"Cache-Control": "no-store"}, b""
        return self._fail(404, "not_found")

    @staticmethod
    def _body(raw: bytes) -> Any:
        try:
            return json.loads(raw.decode("utf-8")) if raw else None
        except (UnicodeDecodeError, ValueError):
            return None

    def _start(self, headers: Dict[str, str], raw: bytes) -> Answer:
        content_type = headers.get("content-type", "")
        match = re.match(r"multipart/form-data;\s*boundary=(\S+)$", content_type, re.IGNORECASE)
        if not match:
            return self._fail(415, "unsupported_format")
        if not self.available:
            return self._fail(503, "fit_unavailable", retry=60)
        parts = self._parts(raw, match.group(1).strip('"').encode())
        if parts is None or set(parts) - {"request", "mesh"}:
            return self._fail(400, "invalid_request", [_issue("part_unexpected", "request")])
        if "request" not in parts:
            return self._fail(400, "invalid_request", [_issue("request_part_missing", "request")])
        if "mesh" not in parts:
            return self._fail(400, "invalid_request", [_issue("mesh_part_missing", "mesh")])
        if len(parts["request"]) > 16 * 1024:
            return self._fail(400, "invalid_request", [_issue("request_invalid", "request")])
        if len(parts["mesh"]) > 16 * 1024 * 1024:
            return self._fail(413, "mesh_too_large", [_issue("mesh_too_large", "mesh")])
        mesh = self._mesh(parts["mesh"])
        if isinstance(mesh, tuple):
            return mesh
        request = self._request(parts["request"])
        if isinstance(request, tuple):
            return request
        if request["bodyVersion"] != self.body_version:
            return self._fail(409, "body_version_mismatch", bodyVersion=self.body_version)
        if self.busy > 0:
            self.busy -= 1
            return self._fail(429, "fit_busy", retry=5)
        running = sum(1 for job in self.jobs.values() if not job["finished"])
        if running >= (2 if self.tier in ("advanced", "ultimate") else 1):
            return self._fail(429, "fit_busy", retry=5)
        if self.used >= self.per_day():
            now = datetime.datetime.now(datetime.timezone.utc)
            midnight = (now + datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            return self._fail(429, "quota_exceeded", retry=max(1, math.ceil((midnight - now).total_seconds())))
        self.used += 1
        self.uploads.append((request, parts["mesh"]))
        job_id = secrets.token_urlsafe(16)[:22].ljust(22, "A")
        self.jobs[job_id] = {"id": job_id, "request": request, "mesh": mesh, "polls": 0, "state": "queued",
                             "finished": False, "refunded": False,
                             "outcome": OUTCOMES.get(request.get("category"), "fitted")}
        return self._json(202, {"jobId": job_id, "state": "queued", "remainingToday": self.per_day() - self.used})

    @staticmethod
    def _parts(raw: bytes, boundary: bytes) -> Optional[Dict[str, bytes]]:
        delimiter = b"--" + boundary
        if not raw.startswith(delimiter):
            return None
        parts: Dict[str, bytes] = {}
        for chunk in raw.split(delimiter)[1:]:
            if chunk.startswith(b"--"):
                break
            if not chunk.startswith(b"\r\n") or not chunk.endswith(b"\r\n"):
                return None
            head, separator, body = chunk[2:-2].partition(b"\r\n\r\n")
            if not separator:
                return None
            name = re.search(rb'name="([^"]+)"', head)
            if name is None or name.group(1).decode() in parts:
                return None
            parts[name.group(1).decode()] = body
        return parts

    def _mesh(self, data: bytes) -> Any:
        def invalid(code: str) -> Answer:
            return self._fail(422, "mesh_invalid", [_issue(code, "mesh")])

        if len(data) < 16:
            return invalid("mesh_truncated")
        if data[:4] != b"DCTM":
            return invalid("mesh_format_invalid")
        version, flags, vertices, triangles = struct.unpack_from("<HHII", data, 4)
        if version != 1:
            return invalid("mesh_version_unsupported")
        if flags & ~1:
            return invalid("mesh_header_invalid")
        too_large = [code for code, over in (("too_many_vertices", vertices > 120000),
                                             ("too_many_triangles", triangles > 240000)) if over]
        if too_large:
            return self._fail(413, "mesh_too_large", [_issue(code, "mesh") for code in too_large])
        if vertices < 3:
            return invalid("positions_invalid")
        if triangles < 1:
            return invalid("triangles_invalid")
        length = 16 + vertices * 12 + triangles * 12 + (vertices if flags & 1 else 0)
        if len(data) < length:
            return invalid("mesh_truncated")
        if len(data) > length:
            return invalid("mesh_trailing_data")
        positions = struct.unpack_from(f"<{vertices * 3}f", data, 16)
        for value in positions:
            if not math.isfinite(value):
                return invalid("coordinate_not_finite")
            if abs(value) > 3:
                return invalid("coordinate_out_of_range")
        indices = struct.unpack_from(f"<{triangles * 3}I", data, 16 + vertices * 12)
        if max(indices) >= vertices:
            return invalid("triangle_index_out_of_range")
        if flags & 1 and any(flag & ~3 for flag in data[16 + vertices * 12 + triangles * 12:]):
            return invalid("flags_invalid")
        return {"positions": positions, "vertices": vertices, "triangles": triangles}

    def _request(self, data: bytes) -> Any:
        def refuse(errors: List[Dict[str, str]]) -> Answer:
            return self._fail(400, "invalid_request", errors)

        known = ("operation", "gender", "drawableType", "category", "sourcePose", "bodyVersion", "markers", "options")
        value = self._body(data)
        if not isinstance(value, dict) or set(value) - set(known):
            return refuse([_issue("request_invalid", "request")])
        errors = []
        if value.get("operation") not in ("fit", "weights"):
            errors.append(_issue("operation_invalid", "operation"))
        if value.get("gender") not in ("male", "female"):
            errors.append(_issue("gender_invalid", "gender"))
        drawable = value.get("drawableType")
        if drawable not in DRAWABLE_TYPES and not re.fullmatch(r"p_[a-z0-9]+", str(drawable)):
            errors.append(_issue("drawable_type_invalid", "drawableType"))
        elif drawable not in FITTABLE:
            errors.append(_issue("slot_unsupported", "drawableType"))
        category = value.get("category")
        if category is not None and not re.fullmatch(r"[a-z0-9_-]{1,32}", str(category)):
            errors.append(_issue("category_invalid", "category"))
        pose = value.get("sourcePose", "rest")
        if pose not in ("rest", "a-pose", "t-pose", "custom"):
            errors.append(_issue("source_pose_invalid", "sourcePose"))
        elif value.get("operation") == "weights" and pose != "rest":
            errors.append(_issue("source_pose_not_rest", "sourcePose"))
        version = value.get("bodyVersion")
        if not isinstance(version, str) or not re.fullmatch(r"[A-Za-z0-9._-]{1,32}", version):
            errors.append(_issue("body_version_invalid", "bodyVersion"))
        markers = value.get("markers", {})
        if not isinstance(markers, dict) or len(markers) > 32:
            errors.append(_issue("too_many_markers", "markers"))
        else:
            for name, point in markers.items():
                if name not in MARKERS:
                    errors.append(_issue("marker_unknown", "markers"))
                elif not isinstance(point, list) or len(point) != 3 or not all(
                        isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) and abs(v) <= 3
                        for v in point):
                    errors.append(_issue("marker_invalid", f"markers.{name}"))
            counts = [sum(1 for name in chain if name in markers) for chain in CHAINS]
            arms = sum(1 for count in counts[:2] if count == 3)
            sleeves = drawable in ("jbib", "accs", "uppr")
            if any(0 < count < 3 for count in counts) or (pose != "rest" and (3 not in counts or (sleeves and arms < 2))):
                errors.append(_issue("marker_missing", "markers"))
        options = value.get("options", {})
        if not isinstance(options, dict):
            errors.append(_issue("request_invalid", "options"))
        else:
            for name, option in options.items():
                if name not in OPTIONS:
                    errors.append(_issue("request_invalid", f"options.{name}"))
                    continue
                bounds = OPTIONS[name]
                if bounds is None:
                    if not isinstance(option, bool):
                        errors.append(_issue("options_out_of_range", f"options.{name}"))
                elif isinstance(option, bool) or not isinstance(option, (int, float)) \
                        or not bounds[0] <= option <= bounds[1]:
                    errors.append(_issue("options_out_of_range", f"options.{name}"))
        if errors:
            return refuse(errors)
        return dict(value, sourcePose=pose)

    def _refund(self, job: Dict[str, Any]) -> None:
        self.used = max(0, self.used - 1)
        job["refunded"] = True

    def _status(self, job: Dict[str, Any]) -> Answer:
        if not job["finished"]:
            job["polls"] += 1
            running_polls = job["polls"] - self.queued_polls
            if running_polls <= 0:
                job["state"] = "queued"
            elif running_polls <= len(STAGES):
                job["state"] = "running"
            else:
                job["finished"] = True
                outcome = job["outcome"]
                if outcome == "invalid":
                    job.update(state="failed", failureCode="mesh_invalid", retryable=False,
                               errors=[_issue("marker_far", "markers")])
                    self._refund(job)
                elif outcome == "error":
                    job.update(state="failed", failureCode="server_error", retryable=True)
                    self._refund(job)
                elif outcome == "timeout":
                    job.update(state="failed", failureCode="fit_timeout", retryable=False)
                else:
                    job.update(state="succeeded", result=self._result(job))
        if job["state"] == "succeeded":
            return 200, {"Content-Type": RESULT_TYPE, "Cache-Control": "no-store"}, job["result"]
        if job["state"] in ("failed", "cancelled"):
            body = {"jobId": job["id"], "state": job["state"], "progress": 0, "refunded": job["refunded"]}
            if job["state"] == "failed":
                body.update(failureCode=job["failureCode"], retryable=job["retryable"])
                if job.get("errors"):
                    body["errors"] = job["errors"]
            return self._json(200, body)
        if job["state"] == "queued":
            return self._json(200, {"jobId": job["id"], "state": "queued", "progress": 0, "queuePosition": 1})
        stage, progress = STAGES[job["polls"] - self.queued_polls - 1]
        return self._json(200, {"jobId": job["id"], "state": "running", "stage": stage, "progress": progress})

    def _result(self, job: Dict[str, Any]) -> bytes:
        mesh = job["mesh"]
        vertices = mesh["vertices"]
        not_on_body = job["outcome"] == "notOnBody"
        positions = list(mesh["positions"])
        if job["request"]["operation"] == "fit":
            for index in range(len(positions)):
                positions[index] += self.position_offset[index % 3]
        bones = bytearray(0 if not_on_body else vertices * 4)
        weights = bytearray(0 if not_on_body else vertices * 4)
        used = set()
        for vertex in range(0 if not_on_body else vertices):
            bone = bone_of(positions[vertex * 3], positions[vertex * 3 + 2])
            bones[vertex * 4] = bone
            weights[vertex * 4] = 255
            used.add(bone)
        positions_length = 0 if not_on_body else vertices * 12
        sections = [] if not_on_body else [
            {"name": "positions", "offset": 0, "length": positions_length, "type": "f32", "components": 3},
            {"name": "bones", "offset": positions_length, "length": vertices * 4, "type": "u8", "components": 4},
            {"name": "weights", "offset": positions_length + vertices * 4, "length": vertices * 4, "type": "u8",
             "components": 4},
        ]
        header = {
            "format": "dct-fit-result", "version": 1, "jobId": job["id"], "operation": job["request"]["operation"],
            "outcome": job["outcome"], "vertexCount": vertices, "triangleCount": mesh["triangles"],
            "sections": sections, "boneNames": {str(bone): BONE_NAMES[bone] for bone in sorted(used)},
            "report": {"outcome": job["outcome"], "confidence": 0 if not_on_body else 0.92,
                       "matchedAreaShare": 0.12 if not_on_body else 0.97,
                       "reposed": job["request"]["operation"] == "fit" and job["request"]["sourcePose"] != "rest",
                       "maximumMarkerOffsetMm": 0, "insideBodyBefore": 0, "insideBodyAfter": 0, "pushedVertices": 0,
                       "unweightedVertices": 0, "influenceCounts": [0, 0 if not_on_body else vertices, 0, 0, 0],
                       "warnings": [] if not_on_body else [{"code": "marker_offset", "message": "marker_offset"}],
                       "elapsedMs": 1200},
        }
        text = json.dumps(header)
        text += " " * (-len(text) % 4)
        head = text.encode()
        payload = b"" if not_on_body else struct.pack(f"<{vertices * 3}f", *positions) + bytes(bones) + bytes(weights)
        return struct.pack("<I", len(head)) + head + payload

    def _reference(self, raw: bytes) -> Answer:
        body = self._body(raw)
        body = body if isinstance(body, dict) else {}
        errors = []
        if body.get("gender") not in ("male", "female"):
            errors.append(_issue("gender_invalid", "gender"))
        if not re.fullmatch(r"[a-z0-9_-]{1,32}", str(body.get("category"))):
            errors.append(_issue("category_invalid", "category"))
        if not isinstance(body.get("bodyVersion"), str) or not re.fullmatch(r"[A-Za-z0-9._-]{1,32}", body["bodyVersion"]):
            errors.append(_issue("body_version_invalid", "bodyVersion"))
        if errors:
            return self._fail(400, "invalid_request", errors)
        if body["bodyVersion"] != self.body_version:
            return self._fail(409, "body_version_mismatch", bodyVersion=self.body_version)
        regions = REFERENCE.get(body["category"])
        if regions is None:
            return self._fail(404, "not_found")
        return self._json(200, {"bodyVersion": self.body_version, "gender": body["gender"], "category": body["category"],
                                "regions": {name: {"p10": p10, "p50": p50, "p90": p90, "samples": samples}
                                            for name, (p10, p50, p90, samples) in regions.items()}})


__all__ = ["FakeLinkApi", "FakeFitService", "make_assertion"]
