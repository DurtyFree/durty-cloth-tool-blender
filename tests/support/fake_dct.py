# SPDX-License-Identifier: MIT
# Copyright (c) Schmid Software Solutions (https://schmid-software.de)
"""A fake Durty Cloth Tool link server for tests: an independent server-side RFC 6455 implementation on a thread
per connection, plus enough DCT behaviour (hello, challenge, auth, account assist, disconnecting an app, live
surfaces, models, services, thumbnails and opening items in the plugin) to drive the add-on end to end.

Adapted from the dct_link test suite (MIT, like dct_link itself). Changes: the protocol module is passed in, so the
same file serves pytest and the Blender smoke (which uses the add-on's vendored copy); a ``glb`` model push is
answered with ``unsupported-format`` as Durty Cloth Tool does today; ``save_busy`` makes ``model.save`` answer
``busy`` that many times; ``texture.read`` answers for the cloth and map asked for; ``open_texture`` and
``open_model`` send ``host.openTexture`` and ``host.openModel`` as Durty Cloth Tool's "Edit in connected app" does.
Standard library only.
"""

from __future__ import annotations

import base64
import hashlib
import itertools
import json
import os
import secrets
import socket
import struct
import threading
import time
from typing import Any, Callable, Dict, List, Optional

try:  # pytest: the add-on's vendored copy; the Blender smoke passes the module to FakeDct instead
    from durty_cloth_tool_link.dct_link import protocol as p
except ImportError:  # pragma: no cover - inside Blender the package has another name
    p = None  # type: ignore[assignment]

GUID = b"258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
def make_assertion(nonce: str, user: str = "u1", jti: Optional[str] = None) -> str:
    """A stand-in for gta.clothing's sign-in assertion (shape and claims only; the fake does not sign)."""
    part = lambda obj: base64.urlsafe_b64encode(json.dumps(obj).encode()).rstrip(b"=").decode()  # noqa: E731
    claims = {"aud": "dct-creator-link-assertion", "UserId": user, "nonce": nonce, "jti": jti or secrets.token_hex(8)}
    return part({"alg": "ES256", "kid": "link-1"}) + "." + part(claims) + ".c2ln"


def assertion_claims(assertion: str) -> Dict[str, Any]:
    try:
        return json.loads(base64.urlsafe_b64decode(assertion.split(".")[1] + "=="))
    except (ValueError, IndexError):
        return {}
BINDING = {"clothId": "3f2b8c1e-7a4d-4e8b-9c1f-2d6e5a7b8c90", "textureId": "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d"}
#: The features Durty Cloth Tool checks itself and reports in welcome and event.entitlement, in its order.
DCT_FEATURES = ("dct.link.connect", "dct.link.context", "dct.link.liveTexture", "dct.link.save", "dct.link.model",
                "dct.link.services", "dct.studio.edit", "dct.studio.materials")
#: The request types DCT checks against a feature before it does anything (answered with needs-license or
#: needs-ultimate otherwise).
GATED_REQUESTS = {"live.open": "dct.link.liveTexture", "live.save": "dct.link.save",
                  "texture.read": "dct.link.services", "texture.validate": "dct.link.services",
                  "uv.layout": "dct.link.services", "model.glb": "dct.link.services", "body.glb": "dct.link.services",
                  "item.thumbnail": "dct.link.services", "model.save": "dct.link.model"}
REFUSALS = {"needsLicense": "needs-license", "needsUltimate": "needs-ultimate"}


def b64u(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def unb64u(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def _xor(data: bytes, mask: bytes) -> bytes:
    if not data:
        return b""
    key = (mask * (len(data) // 4 + 1))[: len(data)]
    return (int.from_bytes(data, "big") ^ int.from_bytes(key, "big")).to_bytes(len(data), "big")


class ClientGone(Exception):
    pass


class Connection:
    """One accepted client. Blocking socket I/O on its own thread."""

    def __init__(self, server: "FakeDct", sock: socket.socket) -> None:
        self.server = server
        self.sock = sock
        self.send_lock = threading.Lock()
        self.client_nonce = b""
        self.server_nonce = b""
        self.install_id: Optional[str] = None
        self.authenticated = False
        self.leases: Dict[str, Dict[str, Any]] = {}
        self.closed = False
        self.close_code: Optional[int] = None
        self.model_revision = 0
        self.converting: set = set()  # model leases whose push is still converting
        # DCT's message budget: about 1000 messages a second, bursts up to 2000, then close 4008.
        self.message_tokens = float(server.message_burst)
        self.message_clock = time.monotonic()

    # ---- raw I/O --------------------------------------------------------------------------------------

    def recv_exact(self, count: int) -> bytes:
        chunks = []
        while count:
            data = self.sock.recv(min(count, 1 << 20))
            if not data:
                raise ClientGone()
            chunks.append(data)
            count -= len(data)
        return b"".join(chunks)

    def handshake(self) -> None:
        data = b""
        while b"\r\n\r\n" not in data:
            chunk = self.sock.recv(4096)
            if not chunk:
                raise ClientGone()
            data += chunk
        head = data.split(b"\r\n\r\n", 1)[0].decode("latin-1").split("\r\n")
        request_line = head[0].split(" ")
        headers = {}
        for line in head[1:]:
            name, _, value = line.partition(":")
            headers[name.strip().lower()] = value.strip()
        self.server.handshake_headers.append(headers)
        assert request_line[0] == "GET" and request_line[1] == p.PATH, request_line
        assert headers["upgrade"].lower() == "websocket"
        assert headers["sec-websocket-version"] == "13"
        assert "origin" not in headers, "native hosts send no Origin"
        assert "sec-websocket-extensions" not in headers, "no compression"
        host = headers["host"]
        assert host.rsplit(":", 1)[0] in ("127.0.0.1", "[::1]"), host
        accept = base64.b64encode(hashlib.sha1(headers["sec-websocket-key"].encode() + GUID).digest()).decode()
        if self.server.bad_accept:
            accept = base64.b64encode(os.urandom(20)).decode()
        extra = self.server.handshake_extra_header
        response = (
            "HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
            f"Sec-WebSocket-Accept: {accept}\r\n{extra}\r\n"
        )
        self.sock.sendall(response.encode())

    def send_frame(self, opcode: int, payload: bytes, fin: bool = True) -> None:
        first = (0x80 if fin else 0) | opcode
        n = len(payload)
        if n < 126:
            head = bytes((first, n))
        elif n < 65536:
            head = bytes((first, 126)) + struct.pack(">H", n)
        else:
            head = bytes((first, 127)) + struct.pack(">Q", n)
        with self.send_lock:
            self.sock.sendall(head + payload)

    def send_message(self, opcode: int, payload: bytes) -> None:
        size = self.server.fragment_size
        if size and len(payload) > size:
            chunks = [payload[i : i + size] for i in range(0, len(payload), size)]
            for index, chunk in enumerate(chunks):
                self.send_frame(opcode if index == 0 else 0, chunk, fin=index == len(chunks) - 1)
                if index == 0:
                    self.send_frame(0x9, b"mid-message ping")  # control frames may interleave
        else:
            self.send_frame(opcode, payload)

    def send(self, message: Dict[str, Any]) -> None:
        self.send_message(0x1, p.encode_text(message))

    def send_binary(self, header: Dict[str, Any], payload: bytes) -> None:
        self.send_message(0x2, p.encode_binary(header, payload))

    def send_raw(self, frame: bytes) -> None:
        """A binary frame exactly as given (no codec), for example a malformed one from the shared fixtures."""
        self.send_message(0x2, frame)

    def close(self, code: int, reason: str = "") -> None:
        if not self.closed:
            self.closed = True
            self.close_code = code
            try:
                self.send_frame(0x8, struct.pack(">H", code) + reason.encode())
            except OSError:
                pass

    def read_message(self):
        message = []
        opcode = None
        while True:
            first, second = self.recv_exact(2)
            fin, op, masked, length = first & 0x80, first & 0x0F, second & 0x80, second & 0x7F
            assert masked, "client frames must be masked"
            assert first & 0x70 == 0
            if length == 126:
                length = struct.unpack(">H", self.recv_exact(2))[0]
            elif length == 127:
                length = struct.unpack(">Q", self.recv_exact(8))[0]
            mask = self.recv_exact(4)
            payload = _xor(self.recv_exact(length), mask)
            if op == 0x9:
                self.send_frame(0xA, payload)
                self.server.pings += 1
                continue
            if op == 0xA:
                continue
            if op == 0x8:
                code = struct.unpack(">H", payload[:2])[0] if len(payload) >= 2 else None
                self.server.close_codes.append(code)
                if not self.closed:
                    self.closed = True
                    self.send_frame(0x8, payload[:2])
                raise ClientGone()
            if op != 0:
                opcode = op
            else:
                self.server.continuation_frames += 1
            message.append(payload)
            if fin:
                return opcode, b"".join(message)

    # ---- DCT behaviour ---------------------------------------------------------------------------------

    def run(self) -> None:
        try:
            if self.server.handshake_delay:
                time.sleep(self.server.handshake_delay)
            self.handshake()
            if self.server.scenario is not None:
                self.server.scenario(self)
                return
            while not self.closed:
                opcode, data = self.read_message()
                self.server.raw_frames.append(data)
                if not self.take_message_token():
                    self.server.rate_limited += 1
                    self.close(4008, "rate limited")
                    return
                if opcode == 0x1:
                    message = p.decode_text(data, p.TO_DCT)
                    self.server.received.append(message)
                    self.on_text(message)
                else:
                    frame = p.decode_binary(data, p.TO_DCT)
                    self.server.received.append(frame.header)
                    self.on_binary(frame.header, bytes(frame.payload))
        except (ClientGone, ConnectionError, OSError):
            pass
        except Exception as exc:  # surface server-side assertion failures to the test
            self.server.errors.append(exc)
        finally:
            try:
                self.sock.close()
            except OSError:
                pass

    def take_message_token(self) -> bool:
        now = time.monotonic()
        burst = float(self.server.message_burst)
        self.message_tokens = min(burst, self.message_tokens + (now - self.message_clock) * self.server.message_rate)
        self.message_clock = now
        if self.message_tokens < 1.0:
            return False
        self.message_tokens -= 1.0
        return True

    def reply(self, request: Dict[str, Any], message: Dict[str, Any]) -> None:
        message.setdefault("id", "s" + secrets.token_hex(3))
        message["re"] = request["id"]
        self.send(message)

    def on_text(self, m: Dict[str, Any]) -> None:
        server = self.server
        kind = m["type"]
        if kind == "hello":
            if server.major_one:
                # A DCT of protocol 1 cannot read this hello: it refuses it in its own major and closes.
                self.send_message(0x1, b'{"v":1,"type":"error","id":"e1","code":"unsupported-protocol"}')
                self.close(1008, "unsupported protocol")
                return
            if server.incompatible:
                self.reply(m, {"type": "incompatible", "code": "plugin-too-old",
                               "dct": {"version": "4.1.0", "protocol": {"min": 3, "max": 3}},
                               "minimumPluginVersion": "9.0.0", "updateUrl": "https://gta.clothing/account/plugins/"})
                self.close(4001, "incompatible")
                return
            self.client_nonce = unb64u(m["clientNonce"])
            self.server_nonce = os.urandom(32)
            self.install_id = m["installId"]
            server.install_ids.append(self.install_id)
            self.reply(m, {"type": "challenge", "serverNonce": b64u(self.server_nonce)})
        elif kind in ("auth", "account.assist"):
            if not self.server_nonce:
                self.reply(m, {"type": "error", "code": "not-authenticated"})
                return
            if kind == "account.assist":
                server.assisted_codes.append(m["userCode"])
                ok = server.on_assist(m["userCode"]) if server.on_assist else True
                if isinstance(ok, str):  # a refusal code, for example busy or rate-limited
                    if server.assist_refusal_as_error:
                        self.reply(m, {"type": "error", "code": ok})
                    else:  # what DCT sends: account.assistResult with ok false and the code
                        self.reply(m, {"type": "account.assistResult", "ok": False, "code": ok})
                    return
                result = {"type": "account.assistResult", "ok": bool(ok)}
                if not ok:
                    result["code"] = server.assist_declined_code
                self.reply(m, result)
                return
            server.assertions_seen.append(m["assertion"])
            if server.auth_error_codes:
                # DCT refuses this sign-in with an error (for example "disconnected": the user disconnected the
                # app in DCT) and closes the connection.
                code = server.auth_error_codes.pop(0)
                self.reply(m, {"type": "error", "code": code})
                if code != "busy":  # busy: DCT could not reach the account service and keeps the connection
                    self.close(4003, code)
                return
            if server.signed_out_auths > 0:
                # DCT itself is signed out: its account check answers dct-signed-out and closes the connection.
                server.signed_out_auths -= 1
                self.reply(m, {"type": "error", "code": "dct-signed-out"})
                self.close(4003, "dct-signed-out")
                return
            refused = server.refuse_assertions > 0
            if refused:
                server.refuse_assertions -= 1
            if refused or not server.check_assertion(m["assertion"], b64u(self.server_nonce)):
                self.reply(m, {"type": "error", "code": "token-invalid"})
                self.close(4003, "authentication failed")
                return
            self.authenticated = True
            server.connections_ready.append(self)  # before the welcome, so a test can broadcast right after it
            self.reply(m, {"type": "welcome", "dct": {"version": "4.0.60"},
                           "protocol": {"major": p.PROTOCOL_MAJOR, "minor": p.PROTOCOL_MINOR},
                           "account": {"userName": server.account}, "features": server.feature_rows()})
        elif not self.authenticated:
            self.reply(m, {"type": "error", "code": "not-authenticated"})
        elif kind in server.ignore:
            return
        elif kind in server.hold_types:
            server.held.append((self, m))
        elif kind in server.fail:
            self.reply(m, {"type": "error", "code": server.fail[kind], "message": "refused by the fake"})
        elif server.refusal(kind) is not None:
            # DCT enforces every gated action itself, whatever the plugin believes.
            self.reply(m, {"type": "error", "code": server.refusal(kind)})
        elif kind == "context.get":
            focused = server.focused or {"clothId": BINDING["clothId"], "name": "jbib_003_u",
                                         "selectedTextureId": BINDING["textureId"],
                                         "textures": [{"textureId": BINDING["textureId"], "name": "jbib_diff_003_a_uni",
                                                       "width": 2048, "height": 2048}],
                                         "targets": ["diffuse", "normal", "specular"]}
            self.reply(m, {"type": "context.snapshot", "project": {"name": "FS Studio Clothing"}, "focused": focused})
        elif kind == "host.result":
            server.host_results.append(m)  # the answer to host.openTexture or host.openModel; nothing goes back
        elif kind == "item.thumbnail":
            # DCT's picture: its longest edge is at most the size asked for (here 2:1, at most 8 wide).
            reply = server.thumbnail_reply or {}
            width = reply.get("width") or min(m["size"], 8)
            height = reply.get("height") or max(1, width // 2)
            header = {"type": "item.thumbnail.data", "binding": reply.get("binding") or m.get("binding") or BINDING,
                      "width": width, "height": height, "format": "rgba8", "re": m["id"]}
            self.send_binary(header, bytes(i % 251 for i in range(width * height * 4)))
        elif kind == "live.open":
            lease = "L%d" % next(server.lease_numbers)  # unique on the server, like DCT's opaque ids
            self.leases[lease] = {"width": m["width"], "height": m["height"],
                                  "canvas": bytearray(m["width"] * m["height"] * 4), "revision": 0}
            self.reply(m, {"type": "live.opened", "lease": lease, "binding": m.get("binding") or BINDING,
                           "target": m["target"], "width": m["width"], "height": m["height"]})
        elif kind == "live.save":
            lease = self.leases.get(m["lease"])
            if lease is None:
                self.reply(m, {"type": "error", "code": "lease-not-found"})
                return
            ok = m["revision"] == lease["revision"]
            server.saves.append((m["lease"], m["revision"], m["mode"], bytes(lease["canvas"])))
            result = {"type": "live.saveResult", "lease": m["lease"], "ok": ok}
            if ok:
                result["textureId"] = BINDING["textureId"]
            else:
                result["code"] = "stale-revision"
            self.reply(m, result)
        elif kind == "live.close":
            self.leases.pop(m["lease"], None)
            self.reply(m, {"type": "live.closed", "lease": m["lease"], "reason": "closed"})
        elif kind == "live.discard":
            server.discards.append(m["lease"])
            self.leases.pop(m["lease"], None)
            self.reply(m, {"type": "live.closed", "lease": m["lease"], "reason": "closed"})
        elif kind == "texture.read":
            server.texture_reads.append(m)
            width, height = server.texture_size
            name = {"diffuse": "jbib_diff_003_a_uni", "normal": "jbib_normal_003", "specular": "jbib_spec_003"}[m["target"]]
            header = {"type": "texture.data", "binding": m.get("binding") or BINDING, "target": m["target"],
                      "name": name, "width": width, "height": height, "format": "rgba8", "re": m["id"]}
            self.send_binary(header, bytes(i % 251 for i in range(width * height * 4)))
        elif kind == "texture.validate":
            self.reply(m, {"type": "texture.findings", "binding": BINDING, "target": m["target"],
                           "findings": [{"code": "non-power-of-two", "severity": "warning"}]})
        elif kind == "uv.layout":
            size = m["size"]
            header = {"type": "uv.layout.image", "binding": BINDING, "width": size, "height": size, "format": "rgba8",
                      "re": m["id"]}
            self.send_binary(header, bytes(i % 251 for i in range(size * size * 4)))
        elif kind == "model.glb":
            self.send_binary({"type": "model.glb.data", "binding": BINDING, "swapMaterials": [0], "re": m["id"]}, b"glTF" * 16)
        elif kind == "body.glb":
            self.send_binary({"type": "body.glb.data", "gender": m["gender"], "re": m["id"]}, b"glTF" * 8)
        elif kind == "model.save" and server.save_busy > 0:
            server.save_busy -= 1  # forced, on top of the busy answers while a push converts
            server.busy_saves += 1
            self.send({"type": "error", "id": "sb" + secrets.token_hex(3), "re": m["id"], "code": "busy"})
        elif kind == "model.save":
            if m["lease"] in self.converting:
                self.reply(m, {"type": "error", "code": "busy"})  # save after model.applied
                return
            server.model_saves.append(m["lease"])
            self.reply(m, {"type": "model.saveResult", "lease": m["lease"], "ok": True})
        elif kind == "model.discard":
            server.model_discards.append(m["lease"])
            self.reply(m, {"type": "model.closed", "lease": m["lease"], "reason": "closed"})
        elif kind == "bye":
            server.byes += 1
            self.close(1000, "bye")

    def kick(self, code: str) -> None:
        """What DCT does when it signs out (``dct-signed-out``), switches account (``account-mismatch``) or the user
        disconnects the app in DCT (``disconnected``)."""
        self.send({"type": "error", "id": "k" + secrets.token_hex(3), "code": code})
        self.close(4003, code)

    def on_binary(self, header: Dict[str, Any], payload: bytes) -> None:
        server = self.server
        if not self.authenticated:
            return
        if header["type"] == "live.frame":
            lease = self.leases.get(header["lease"])
            if lease is None:
                # Like DCT: an error without re (a frame has no id), and the connection stays.
                server.unknown_lease_frames += 1
                self.send({"type": "error", "id": "e" + secrets.token_hex(3), "code": "lease-not-found"})
                return
            rect = header["rect"]
            assert header["revision"] > lease["revision"], "revisions only grow"
            lease["revision"] = header["revision"]
            stride, row = lease["width"] * 4, rect["w"] * 4
            for line in range(rect["h"]):
                start = (rect["y"] + line) * stride + rect["x"] * 4
                lease["canvas"][start : start + row] = payload[line * row : (line + 1) * row]
            server.frames.append((header["lease"], header["revision"], dict(rect)))
            if server.frame_delay:
                time.sleep(server.frame_delay)
            self.send({"type": "live.status", "id": "st%d" % header["revision"], "lease": header["lease"],
                       "appliedRevision": header["revision"], "state": "attached"})
        elif header["type"] == "model.push" and header["format"] != "ydd-xml":
            server.pushes.append((header, {}))
            reply = {"type": "error", "id": "mx%d" % len(server.pushes), "code": "unsupported-format",
                     "message": "only ydd-xml models are accepted"}
            if "id" in header:
                reply["re"] = header["id"]
            self.send(reply)
        elif header["type"] == "model.push":
            files, offset = {}, 0
            for entry in header["files"]:
                files[entry["name"]] = payload[offset : offset + entry["length"]]
                offset += entry["length"]
            server.pushes.append((header, files))
            self.model_revision += 1
            lease = header.get("lease") or "M%d" % next(server.model_numbers)  # opaque, unique like DCT's
            applied = {"type": "model.applied", "lease": lease, "revision": self.model_revision,
                       "binding": header.get("binding") or BINDING, "findings": []}
            if "id" in header:
                applied["re"] = header["id"]
            applied["id"] = "ma%d" % self.model_revision
            if not server.push_delay:
                self.send(applied)
                return
            self.converting.add(lease)  # DCT converts on a worker; model.save meanwhile is answered busy

            def finish() -> None:
                self.converting.discard(lease)
                try:
                    self.send(applied)
                except OSError:
                    pass  # the client went away

            timer = threading.Timer(server.push_delay, finish)
            timer.daemon = True
            timer.start()


class FakeDct:
    """Listens on 127.0.0.1 (an ephemeral port unless one is given)."""

    def __init__(self, port: int = 0, protocol: Any = None) -> None:
        global p
        if protocol is not None:
            p = protocol
        if p is None:
            raise RuntimeError("pass the dct_link protocol module")
        self.listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listener.bind(("127.0.0.1", port))
        self.listener.listen(16)
        self.port = self.listener.getsockname()[1]
        self.install_ids: List[str] = []
        self.used_jti: set = set()
        self.check_assertion: Callable[[str, str], bool] = self._check_assertion
        self.account = "Durty"
        self.incompatible = False
        #: Behave like a Durty Cloth Tool of protocol 1, which cannot read a protocol 2 hello.
        self.major_one = False
        #: The focused item context.get reports (default: one without the optional metadata).
        self.focused: Optional[Dict[str, Any]] = None
        #: Answer item.thumbnail with a picture of this width, height or binding, whatever was asked for.
        self.thumbnail_reply: Optional[Dict[str, Any]] = None
        self.host_results: List[Dict[str, Any]] = []
        self.fragment_size = 0
        self.frame_delay = 0.0
        self.handshake_extra_header = ""
        self.bad_accept = False
        self.ignore: set = set()
        self.fail: Dict[str, str] = {}
        self.hold_types: set = set()
        self.held: List[Any] = []
        self.refuse_assertions = 0
        self.message_rate = 1000.0
        self.message_burst = 2000.0
        self.push_delay = 0.0
        self.lease_numbers = itertools.count(1)
        self.rate_limited = 0
        self.unknown_lease_frames = 0
        self.signed_out_auths = 0
        self.auth_error_codes: List[str] = []
        self.handshake_delay = 0.0
        self.drop_connections = 0
        self.all_connections: List[Connection] = []
        self.model_saves: List[str] = []
        self.model_discards: List[str] = []
        self.model_numbers = itertools.count(1)
        self.save_busy = 0
        self.busy_saves = 0
        #: The size of the picture texture.read answers with.
        self.texture_size = (2, 2)
        self.texture_reads: List[Dict[str, Any]] = []
        self.scenario: Optional[Callable[[Connection], None]] = None
        self.on_assist: Optional[Callable[[str], bool]] = None
        self.received: List[Dict[str, Any]] = []
        self.frames: List[Any] = []
        self.saves: List[Any] = []
        self.pushes: List[Any] = []
        self.discards: List[str] = []
        self.assist_declined_code = "request-denied"
        #: An on_assist answer that is a code is sent as account.assistResult (like DCT); True sends an error.
        self.assist_refusal_as_error = False
        #: What DCT's licence allows: feature id to state. welcome and event.entitlement report these rows, and
        #: gated requests are refused accordingly.
        self.feature_states: Dict[str, str] = {feature: "entitled" for feature in DCT_FEATURES}
        #: Features welcome and event.entitlement leave out (DCT still enforces them).
        self.unreported_features: set = set()
        self.assisted_codes: List[str] = []
        self.assertions_seen: List[str] = []
        self.raw_frames: List[bytes] = []
        self.handshake_headers: List[Dict[str, str]] = []
        self.close_codes: List[Optional[int]] = []
        self.connections_ready: List[Connection] = []
        self.errors: List[BaseException] = []
        self.pings = 0
        self.byes = 0
        self.continuation_frames = 0
        self.connections = 0
        self._stop = False
        self._thread = threading.Thread(target=self._accept, daemon=True)
        self._thread.start()

    def _accept(self) -> None:
        while not self._stop:
            try:
                sock, _ = self.listener.accept()
            except OSError:
                return
            self.connections += 1
            if self.drop_connections > 0:  # DCT not ready yet: the connection closes at once
                self.drop_connections -= 1
                sock.close()
                continue
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            connection = Connection(self, sock)
            self.all_connections.append(connection)
            threading.Thread(target=connection.run, daemon=True).start()

    def _check_assertion(self, assertion: str, server_nonce: str) -> bool:
        """Like DCT: the audience is the assertion audience, the nonce is this connection's, and once only."""
        claims = assertion_claims(assertion)
        if claims.get("aud") != "dct-creator-link-assertion" or claims.get("nonce") != server_nonce:
            return False
        if claims.get("jti") in self.used_jti:
            return False
        self.used_jti.add(claims.get("jti"))
        return True

    def report_no_features(self) -> None:
        """Behaves like a Durty Cloth Tool that reports no feature states: welcome and event.entitlement carry
        ``"features": []``, while every gated request is still enforced."""
        self.unreported_features = set(DCT_FEATURES)

    def feature_rows(self) -> List[Dict[str, str]]:
        """The feature states as DCT sends them in welcome and event.entitlement."""
        return [{"id": feature, "state": state} for feature, state in self.feature_states.items()
                if feature not in self.unreported_features]

    def refusal(self, kind: str) -> Optional[str]:
        """The error code DCT answers a gated request with, or None when the licence allows it."""
        return REFUSALS.get(self.feature_states.get(GATED_REQUESTS.get(kind, ""), "entitled"))

    def set_features(self, **states: str) -> None:
        """The licence changed in DCT: ``set_features(liveTexture="needsUltimate")`` changes ``dct.link.liveTexture``
        and tells every connected plugin (event.entitlement), as DCT does."""
        for name, state in states.items():
            matches = [feature for feature in DCT_FEATURES if feature.rsplit(".", 1)[-1] == name]
            self.feature_states[matches[0]] = state
        self.broadcast({"type": "event.entitlement", "id": "ent" + secrets.token_hex(3), "features": self.feature_rows()})

    def release_held(self) -> int:
        """Answers every held service request (in the order received)."""
        held, self.held = self.held, []
        for connection, message in held:
            server_hold, self.hold_types = self.hold_types, set()
            try:
                connection.on_text(message)
            finally:
                self.hold_types = server_hold
        return len(held)

    def broadcast(self, message: Dict[str, Any]) -> None:
        for connection in list(self.connections_ready):
            connection.send(message)

    def broadcast_binary(self, header: Dict[str, Any], payload: bytes) -> None:
        for connection in list(self.connections_ready):
            connection.send_binary(header, payload)

    def broadcast_raw(self, frame: bytes) -> None:
        for connection in list(self.connections_ready):
            connection.send_raw(frame)

    def open_texture(self, rgba: bytes, width: int, height: int, *, target: str = "diffuse",
                     binding: Optional[Dict[str, str]] = None, name: str = "jbib_diff_003_a_uni",
                     request_id: Optional[str] = None) -> str:
        """Edit in connected app for a texture map: ``host.openTexture`` with RGBA8 rows top to bottom. Returns the
        request id the plugin's ``host.result`` names."""
        request_id = request_id or "ot" + secrets.token_hex(3)
        header = {"type": "host.openTexture", "id": request_id, "binding": binding or BINDING, "target": target,
                  "name": name, "width": width, "height": height, "format": "rgba8"}
        self.connections_ready[-1].send_binary(header, rgba)
        return request_id

    def open_model(self, files: List[Any], *, binding: Optional[Dict[str, str]] = None, name: str = "jbib_003_u",
                   request_id: Optional[str] = None) -> str:
        """Edit in connected app for a model: ``host.openModel`` with ``files`` as ``(name, bytes)``, the
        ``*.ydd.xml`` first. Returns the request id."""
        request_id = request_id or "om" + secrets.token_hex(3)
        header = {"type": "host.openModel", "id": request_id, "binding": binding or BINDING, "name": name,
                  "format": "ydd-xml", "files": [{"name": n, "length": len(data)} for n, data in files]}
        self.connections_ready[-1].send_binary(header, b"".join(bytes(data) for _, data in files))
        return request_id

    def host_result(self, request_id: str) -> Optional[Dict[str, Any]]:
        """The plugin's answer to one of the requests above, once it arrived."""
        return next((m for m in self.host_results if m.get("re") == request_id), None)

    def drop_all(self) -> None:
        """Simulates DCT going away without a close frame."""
        for connection in list(self.connections_ready):
            try:
                connection.sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
        self.connections_ready.clear()

    def stop(self) -> None:
        self._stop = True
        try:
            self.listener.close()
        except OSError:
            pass
        self.drop_all()

    def __enter__(self) -> "FakeDct":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.stop()
        if self.errors:
            raise self.errors[0]
