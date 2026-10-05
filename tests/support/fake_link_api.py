# SPDX-License-Identifier: MIT
# Copyright (c) Schmid Software Solutions (https://schmid-software.de)
"""A fake of gta.clothing's public Creator Link sign-in routes on 127.0.0.1 for tests: device sign-in, token
rotation, sign-in assertions and logout, and the link origin's channel manifest, panel tickets and hosted body. It is
strict where the real service is strict (a spent refresh token revokes the session, a ticket opens only the body of
the version the manifest names).

Adapted from the dct_link test suite (MIT, like dct_link itself), reduced to the routes the add-on calls.
Standard library only, so the Blender smoke can use it too.
"""

from __future__ import annotations

import base64
import json
import os
import re
import secrets
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, List, Optional


def header_pattern(protocol: str) -> "re.Pattern[str]":
    """The X-DCT-Link-Client header of the Blender add-on speaking ``protocol`` (for example "2.0")."""
    return re.compile(r"blender/[0-9]+\.[0-9]+\.[0-9]+\S* \(protocol " + re.escape(protocol)
                      + r"; channel (release|experimental|development)\)")


def _token(prefix: str) -> str:
    return prefix + base64.urlsafe_b64encode(os.urandom(24)).rstrip(b"=").decode()


def _part(obj: Dict[str, Any]) -> str:
    return base64.urlsafe_b64encode(json.dumps(obj).encode()).rstrip(b"=").decode()


def make_jwt() -> str:
    return _part({"alg": "ES256", "kid": "link-1"}) + "." + _part({"UserId": "u1", "jti": os.urandom(4).hex()}) + "." + _token("")


def make_assertion(nonce: str, user: str = "u1") -> str:
    """Shape and claims of a sign-in assertion (the fake does not sign; the fake DCT checks the claims)."""
    claims = {"aud": "dct-creator-link-assertion", "UserId": user, "nonce": nonce, "jti": secrets.token_hex(8)}
    return _part({"alg": "ES256", "kid": "link-1"}) + "." + _part(claims) + ".c2ln"


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

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
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
                "user": {"id": "u1", "name": "Durty", "avatarUrl": "https://cdn.discordapp.com/x.png"},
                "entitlement": {"tier": "ultimate", "featureTableVersion": "0.1", "features": []}}

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
        body = json.loads(raw) if raw else None
        path = handler.path
        headers = {k.lower(): v for k, v in handler.headers.items()}
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
        self._send(handler, 200, {"ticket": ticket, "expiresAtUtc": "2026-10-05T12:30:00Z",
                                  "base": f"/link/panel/{body['channel']}/{body['version']}/app/{ticket}/"})

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


__all__ = ["FakeLinkApi", "make_assertion"]
