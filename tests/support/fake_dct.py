# SPDX-License-Identifier: MIT
# Copyright (c) Schmid Software Solutions (https://schmid-software.de)
"""A fake Durty Cloth Tool link server for tests: an independent server-side RFC 6455 implementation on a thread
per connection, plus enough DCT behaviour (hello, challenge, auth, account assist, disconnecting an app, live
surfaces, models, services, thumbnails and opening items in the plugin) to drive the add-on end to end.

MIT licensed, like dct_link. The protocol module is passed in, so the same file serves pytest and the Blender
smoke (which uses the add-on's vendored copy). A ``glb`` model push is answered with ``unsupported-format``;
``save_busy`` makes ``model.save`` answer ``busy`` that many times; ``texture.read`` answers for the cloth and map
asked for; ``open_texture`` and ``open_model`` send ``host.openTexture`` and ``host.openModel`` ("Edit in connected
app"); ``skeleton.template`` answers with a synthetic skeleton template (or ``skeleton_files``), and ``item.add``
with ``add_result`` (``hold_adds`` keeps it waiting, ``item.addCancel`` answers it as refused unless
``ignore_cancels``). The custom ped messages: ``ped.templates`` lists ``ped_templates``, ``ped.skeleton`` and
``ped.rig`` use a made-up skeleton (:func:`ped_skeleton`), the rig reports its progress over ``ped_rig_seconds`` and
stops at ``ped.rig.cancel``, and ``ped.add`` collects the chunks, checks the SHA-256 and answers with
``ped_add_result`` (``hold_ped_adds`` keeps it waiting). A request the fake cannot decode, or whose type is in
``unknown_types`` (a DCT older than the add-on), gets an error answered by its id when the id can be read, and the
connection stays once signed in.
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
    """A stand-in for a sign-in assertion with the claims the fake checks (audience, nonce, id); not signed."""
    part = lambda obj: base64.urlsafe_b64encode(json.dumps(obj).encode()).rstrip(b"=").decode()  # noqa: E731
    claims = {"aud": "dct-creator-link-assertion", "sub": user, "nonce": nonce, "jti": jti or secrets.token_hex(8)}
    return part({"alg": "none", "typ": "test"}) + "." + part(claims) + ".c2ln"


def assertion_claims(assertion: str) -> Dict[str, Any]:
    try:
        return json.loads(base64.urlsafe_b64decode(assertion.split(".")[1] + "=="))
    except (ValueError, IndexError):
        return {}
BINDING = {"clothId": "3f2b8c1e-7a4d-4e8b-9c1f-2d6e5a7b8c90", "textureId": "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d"}
#: The cloth an item.add creates (and its first variation).
ADDED_BINDING = {"clothId": "5e6f7a8b-9c0d-4e1f-8a2b-3c4d5e6f7a8b", "textureId": "6f7a8b9c-0d1e-4f2a-9b3c-4d5e6f7a8b9c"}
#: What skeleton.template.data carries unless ``skeleton_files`` says otherwise (a drawable dictionary without
#: bones; the tests and the smoke give it a synthetic skeleton).
SKELETON_XML = b'<?xml version="1.0" encoding="UTF-8"?>\n<DrawableDictionary><Item><Skeleton /></Item></DrawableDictionary>\n'
#: The feature states the fake reports in welcome and event.entitlement (the features the add-on reads).
DCT_FEATURES = ("dct.link.connect", "dct.link.context", "dct.link.liveTexture", "dct.link.save", "dct.link.model",
                "dct.link.services", "dct.link.addItem", "dct.link.pedTemplates", "dct.link.pedRig", "dct.link.pedAdd")
#: The requests the fake refuses while their feature is not entitled (the ones the tests exercise).
GATED_REQUESTS = {"texture.read": "dct.link.services", "texture.validate": "dct.link.services",
                  "item.thumbnail": "dct.link.services", "ped.templates": "dct.link.pedTemplates",
                  "ped.skeleton": "dct.link.pedTemplates"}
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


# ---- custom peds: a made-up template skeleton (nothing of the game: names as every human ped skeleton uses them,
# tags of its own, positions of a person 1.8 m tall standing with the root between the hips, turned rest rotations) ----

#: (name, tag, parent index, rest position in ped space) in the skeleton's order, parents first.
PED_BONES = (
    ("SKEL_ROOT", 0, -1, (0.0, 0.0, 0.0)),
    ("SKEL_Pelvis", 101, 0, (0.0, 0.0, -0.02)),
    ("SKEL_L_Thigh", 102, 1, (0.09, 0.0, -0.06)),
    ("SKEL_L_Calf", 103, 2, (0.1, 0.0, -0.5)),
    ("SKEL_L_Foot", 104, 3, (0.11, 0.0, -0.92)),
    ("SKEL_L_Toe0", 105, 4, (0.11, -0.12, -0.98)),
    ("SKEL_R_Thigh", 106, 1, (-0.09, 0.0, -0.06)),
    ("SKEL_R_Calf", 107, 6, (-0.1, 0.0, -0.5)),
    ("SKEL_R_Foot", 108, 7, (-0.11, 0.0, -0.92)),
    ("SKEL_R_Toe0", 109, 8, (-0.11, -0.12, -0.98)),
    ("SKEL_Spine_Root", 110, 0, (0.0, 0.0, 0.0)),
    ("SKEL_Spine0", 111, 10, (0.0, 0.0, 0.08)),
    ("SKEL_Spine1", 112, 11, (0.0, 0.0, 0.17)),
    ("SKEL_Spine2", 113, 12, (0.0, 0.0, 0.26)),
    ("SKEL_Spine3", 114, 13, (0.0, 0.0, 0.35)),
    ("SKEL_L_Clavicle", 115, 14, (0.03, 0.0, 0.47)),
    ("SKEL_L_UpperArm", 116, 15, (0.18, 0.0, 0.49)),
    ("SKEL_L_Forearm", 117, 16, (0.41, 0.0, 0.26)),
    ("SKEL_L_Hand", 118, 17, (0.6, 0.0, 0.07)),
    ("PH_L_Hand", 119, 18, (0.66, -0.02, 0.02)),
    ("SKEL_R_Clavicle", 120, 14, (-0.03, 0.0, 0.47)),
    ("SKEL_R_UpperArm", 121, 20, (-0.18, 0.0, 0.49)),
    ("SKEL_R_Forearm", 122, 21, (-0.41, 0.0, 0.26)),
    ("SKEL_R_Hand", 123, 22, (-0.6, 0.0, 0.07)),
    ("PH_R_Hand", 124, 23, (-0.66, -0.02, 0.02)),
    ("SKEL_Neck_1", 125, 14, (0.0, 0.0, 0.53)),
    ("SKEL_Head", 126, 25, (0.0, 0.0, 0.62)),
    ("IK_Head", 127, 26, (0.0, 0.0, 0.62)),
)
#: The bones that never move the mesh (no weight goes on them).
PED_NON_DEFORMING = frozenset(name for name, _, _, _ in PED_BONES if name == "SKEL_ROOT" or name[:3] in ("IK_", "PH_"))
_RECORD = struct.Struct("<HhI4f3f16f")
_MATRIX = struct.Struct("<16f")


def _quaternion(index: int) -> tuple:
    """A made-up local rest rotation for bone ``index`` (x, y, z, w): every bone is turned, as in a real skeleton."""
    import math

    axis = (math.sin(index * 1.7), math.cos(index * 1.3), 0.5 + 0.3 * math.sin(index))
    length = math.sqrt(sum(c * c for c in axis))
    half = 0.15 * ((index * 37) % 11 - 5)
    s = math.sin(half) / length
    return (axis[0] * s, axis[1] * s, axis[2] * s, math.cos(half))


def _rotation_of(q: tuple) -> list:
    x, y, z, w = q
    return [[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
            [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
            [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]]


def _mul(a: list, b: list) -> list:
    return [[sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]


def _row_major(rotation: list, position: tuple) -> list:
    """A world matrix in the protocol's form: row major, row vectors (rows 1 to 3 the bone's axes, row 4 its
    position), from a rotation that takes the bone's local axes to the armature's (column vectors)."""
    return [rotation[0][0], rotation[1][0], rotation[2][0], 0.0,
            rotation[0][1], rotation[1][1], rotation[2][1], 0.0,
            rotation[0][2], rotation[1][2], rotation[2][2], 0.0,
            position[0], position[1], position[2], 1.0]


def ped_skeleton(offset: tuple = (0.0, 0.0, 0.0)) -> List[Dict[str, Any]]:
    """The made-up template skeleton: per bone its name, tag, parent, flags, local rest rotation (x, y, z, w) and
    translation, and rest world matrix (protocol form), moved by ``offset``."""
    bones: List[Dict[str, Any]] = []
    worlds: List[list] = []
    for index, (name, tag, parent, position) in enumerate(PED_BONES):
        local = _quaternion(index)
        turn = _rotation_of(local)
        if parent < 0:
            world, translation = turn, tuple(position[i] + offset[i] for i in range(3))
        else:
            world = _mul(worlds[parent], turn)
            delta = [position[i] - PED_BONES[parent][3][i] for i in range(3)]
            axes = worlds[parent]  # the parent's axes as columns; the translation is in its frame
            translation = tuple(sum(axes[k][i] * delta[k] for k in range(3)) for i in range(3))
        worlds.append(world)
        bones.append({"name": name, "tag": tag, "parent": parent, "flags": 0x1F, "rotation": local,
                      "translation": translation,
                      "world": _row_major(world, tuple(position[i] + offset[i] for i in range(3)))})
    return bones


def ped_bone_records(bones: List[Dict[str, Any]]) -> bytes:
    return b"".join(_RECORD.pack(b["tag"], b["parent"], b["flags"], *b["rotation"], *b["translation"], *b["world"])
                    for b in bones)


def fake_ped_rig(header: Dict[str, Any], payload: bytes, warnings: List[Dict[str, Any]], outcome: str,
                 suggested: Optional[str]) -> tuple:
    """A stand-in for DCT's rig: the template's rest skeleton is the rest pose G, the pose P is G moved so the
    template's pelvis sits on the pelvis marker, the rest positions are the character moved back by the same, and
    each vertex is weighted to its two nearest bones (200 and 55 of 255). The elbow markers come back refined by 2 cm.
    Returns ``(result header, payload)``."""
    mesh = header["mesh"]
    count = mesh["vertices"]
    positions = struct.unpack_from(f"<{3 * count}f", payload, 0)
    markers = header["markers"]
    template = ped_skeleton()
    pelvis = next(b for b in template if b["name"] == "SKEL_Pelvis")["world"][12:15]
    shift = tuple(markers["pelvis"][i] - pelvis[i] for i in range(3))
    heads = [(i, tuple(b["world"][12 + k] + shift[k] for k in range(3))) for i, b in enumerate(template)
             if b["name"] not in PED_NON_DEFORMING]
    poses = b""
    for bone in template:
        world = list(bone["world"])
        for k in range(3):
            world[12 + k] += shift[k]
        poses += _MATRIX.pack(*world)
    rest, indices, weights = [], bytearray(), bytearray()
    for v in range(count):
        point = positions[3 * v: 3 * v + 3]
        ranked = sorted(heads, key=lambda h: sum((h[1][k] - point[k]) ** 2 for k in range(3)))
        indices += bytes((ranked[0][0], ranked[1][0], 0, 0))
        weights += bytes((200, 55, 0, 0))
        rest.extend(point[k] - shift[k] for k in range(3))
    refined = {name: list(point) for name, point in markers.items()}
    moves = {}
    for name in ("elbowL", "elbowR"):
        if name in refined:
            refined[name][1] += 0.02
            moves[name] = 20.0
    report = {"outcome": outcome, "confidence": 0.91 if outcome == "ready" else 0.62, "warnings": warnings,
              "markers": refined, "markerMoves": moves,
              "character": {"height": 1.8, "shoulders": 0.37, "hips": 0.18, "arm": 0.6, "leg": 0.84, "torso": 0.55},
              "template": {"height": 1.8, "shoulders": 0.36, "hips": 0.18, "arm": 0.6, "leg": 0.86, "torso": 0.55}}
    if suggested:
        report["suggestedTemplate"] = suggested
    result = {"type": "ped.rig.result", "re": header["id"], "ok": True, "job": "j1", "template": header["template"],
              "ragdoll": "fred", "bones": [b["name"] for b in template], "vertices": count, "report": report}
    body = (ped_bone_records(template) + poses + struct.pack(f"<{3 * count}f", *rest) + bytes(indices)
            + bytes(weights))
    return result, body


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
        self.waiting_adds: Dict[str, Dict[str, Any]] = {}  # item.add headers by id while "the user" decides
        self.rig_cancels: set = set()  # ped.rig ids the plugin cancelled
        self.ped_upload: Optional[Dict[str, Any]] = None  # the ped.add whose chunks arrive
        self.waiting_ped_adds: Dict[str, Dict[str, Any]] = {}  # ped.add headers by id while "the user" decides

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
                if self.refuse_unreadable(data, binary=opcode != 0x1):
                    continue
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

    def refuse_unreadable(self, data: bytes, binary: bool) -> bool:
        """A frame the fake cannot decode (or a type it does not know) gets an ``error`` whose ``re`` is the frame's id
        whenever that id can still be read. Before the sign-in the connection closes instead."""
        header: Any = None
        try:
            if binary:
                length = int.from_bytes(data[:4], "little")
                header = json.loads(bytes(data[4:4 + length]).decode("utf-8"))
            else:
                header = json.loads(bytes(data).decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            header = None
        if not isinstance(header, dict):
            header = {}
        if header.get("type") in self.server.unknown_types:
            code = "unknown-message-type"
        else:
            try:
                if binary:
                    p.decode_binary(data, p.TO_DCT)
                else:
                    p.decode_text(data, p.TO_DCT)
                return False
            except p.ProtocolError as exc:
                code = exc.code
        self.server.refused_frames.append((header.get("type"), code))
        if not self.authenticated:
            self.close(1008, code)
            return True
        reply: Dict[str, Any] = {"type": "error", "id": "u" + secrets.token_hex(3), "code": code}
        if p.is_id(header.get("id")):
            reply["re"] = header["id"]
        self.send(reply)
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
                               "dct": {"version": "99.0.0", "protocol": {"min": 99, "max": 99}},
                               "minimumPluginVersion": "99.0.0", "updateUrl": "https://gta.clothing/account/plugins/"})
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
                if code != "busy":  # busy keeps the connection
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
            self.reply(m, {"type": "welcome", "dct": {"version": "9.9.9"},
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
            # The fake refuses a gated request whatever the add-on believes about its features.
            self.reply(m, {"type": "error", "code": server.refusal(kind)})
        elif kind == "context.get":
            focused = server.focused or {"clothId": BINDING["clothId"], "name": "jbib_003_u",
                                         "selectedTextureId": BINDING["textureId"],
                                         "textures": [{"textureId": BINDING["textureId"], "name": "jbib_diff_003_a_uni",
                                                       "width": 2048, "height": 2048}],
                                         "targets": ["diffuse", "normal", "specular"]}
            self.reply(m, {"type": "context.snapshot", "project": {"name": "Sample Clothing"}, "focused": focused})
        elif kind == "host.result":
            server.host_results.append(m)  # the answer to host.openTexture or host.openModel; nothing goes back
        elif kind == "ped.templates":
            server.ped_template_requests.append(m)
            listed = [t for t in server.ped_templates if (m.get("all") or t["group"] == "ambient")
                      and (m.get("gender") is None or t.get("gender") == m["gender"])]
            listed.sort(key=lambda t: not t["recommended"])
            offset = m.get("offset", 0)
            self.reply(m, {"type": "ped.templates.list", "offset": offset, "total": len(listed),
                           "templates": listed[offset:offset + p.PED_TEMPLATES_PER_PAGE], "truncated": False})
        elif kind == "ped.skeleton":
            bones = ped_skeleton()
            header = {"type": "ped.skeleton.data", "re": m["id"], "model": m["model"], "gender": "male",
                      "layout": "packed", "ragdoll": "fred", "bones": [b["name"] for b in bones]}
            self.send_binary(header, ped_bone_records(bones))
        elif kind == "ped.rig.cancel":
            server.ped_rig_cancels.append(m["re"])
            self.rig_cancels.add(m["re"])
        elif kind == "ped.add":
            server.ped_add_headers.append(m)
            code = REFUSALS.get(server.feature_states.get("dct.link.pedAdd", "entitled")) or server.fail.get("ped.add")
            if code is not None:
                self.answer_ped_add(m["id"], {"ok": False, "code": code, "findings": []})
            elif self.ped_upload is not None or self.waiting_ped_adds:
                self.answer_ped_add(m["id"], {"ok": False, "code": "busy", "findings": []})
            else:
                self.ped_upload = {"header": m, "chunks": []}
        elif kind == "ped.addCancel":
            server.ped_add_cancels.append(m["re"])
            if server.ignore_cancels and m["re"] in self.waiting_ped_adds:
                return  # "the user" chose Create a moment before: release_ped_adds() answers later
            upload = self.ped_upload
            if upload is not None and upload["header"]["id"] == m["re"]:
                self.ped_upload = None
                self.answer_ped_add(m["re"], {"ok": False, "code": "request-denied", "findings": []})
            elif self.waiting_ped_adds.pop(m["re"], None) is not None:
                self.answer_ped_add(m["re"], {"ok": False, "code": "request-denied", "findings": []})
        elif kind == "skeleton.template":
            # The skeleton template of the gender asked for (skeleton_files: other files, any gender).
            server.templates_sent.append(m["gender"])
            gender = m["gender"]
            files = server.skeleton_files.get(gender) if server.skeleton_files else None
            files = files or [(f"mp_{gender[0]}_freemode_01_skeleton.ydd.xml", SKELETON_XML)]
            header = {"type": "skeleton.template.data", "re": m["id"], "gender": gender, "format": "ydd-xml",
                      "files": [{"name": name, "length": len(data)} for name, data in files]}
            self.send_binary(header, b"".join(data for _, data in files))
        elif kind == "item.addCancel":
            server.add_cancels.append(m["re"])
            if server.ignore_cancels:
                return  # "the user" chose Add a moment before: the import goes on and answers later
            # Like the user choosing Cancel: the add answers request-denied. A cancel for an add that already
            # answered, or that never was, has no reply of its own.
            if self.waiting_adds.pop(m["re"], None) is not None:
                self.answer_add(m["re"], {"ok": False, "code": "request-denied", "findings": []})
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

    def answer_ped_add(self, add_id: str, result: Optional[Dict[str, Any]] = None) -> None:
        """Answers the ped.add ``add_id`` with ped.addResult (the server's ``ped_add_result`` unless one is given)."""
        message: Dict[str, Any] = {"type": "ped.addResult", "id": "pr" + secrets.token_hex(3), "re": add_id}
        if result is None:
            header = next(h for h in reversed(self.server.ped_add_headers) if h["id"] == add_id)
            result = dict(self.server.ped_add_result)
            if result.get("ok"):
                result.setdefault("project", {"name": header["name"], "model": header["model"],
                                              "template": header["template"]})
        message.update(result)
        self.send(message)

    def rig(self, header: Dict[str, Any], payload: bytes) -> None:
        """Runs a ped.rig on a thread of its own: accepted, progress, then the result (or ``cancelled``)."""
        server = self.server
        try:
            refusal = server.ped_rig_refusal
            if refusal is not None:
                code, reasons = refusal
                result = {"type": "ped.rig.result", "re": header["id"], "ok": False, "code": code}
                if reasons:
                    result["reasons"] = reasons
                self.send_binary(result, b"")
                return
            self.send({"type": "ped.rig.accepted", "id": "ra" + secrets.token_hex(3), "re": header["id"], "job": "j1"})
            stages = ("template", "markers", "skeleton", "weights", "rest", "report")
            for index, stage in enumerate(stages):
                time.sleep(server.ped_rig_seconds / len(stages))
                if header["id"] in self.rig_cancels:
                    self.send_binary({"type": "ped.rig.result", "re": header["id"], "ok": False, "code": "cancelled",
                                      "job": "j1"}, b"")
                    return
                self.send({"type": "ped.rig.progress", "id": "rp" + secrets.token_hex(3), "job": "j1", "stage": stage,
                           "fraction": round((index + 1) / len(stages), 3)})
            result, body = fake_ped_rig(header, payload, server.ped_rig_warnings, server.ped_rig_outcome,
                                        server.ped_rig_suggestion)
            self.send_binary(result, body)
        except OSError:
            pass  # the client went away
        except Exception as exc:  # surface the fake's own failures to the test
            server.errors.append(exc)

    def answer_add(self, add_id: str, result: Optional[Dict[str, Any]] = None) -> None:
        """Answers the item.add ``add_id`` with item.addResult (the server's ``add_result`` unless one is given)."""
        message: Dict[str, Any] = {"type": "item.addResult", "id": "ar" + secrets.token_hex(3), "re": add_id}
        message.update(result if result is not None else self.server.add_result)
        self.send(message)

    def kick(self, code: str) -> None:
        """Ends the connection as for a sign-out in DCT (``dct-signed-out``), an account switch (``account-mismatch``)
        or the app disconnected there (``disconnected``)."""
        self.send({"type": "error", "id": "k" + secrets.token_hex(3), "code": code})
        self.close(4003, code)

    def on_binary(self, header: Dict[str, Any], payload: bytes) -> None:
        server = self.server
        if not self.authenticated:
            return
        if header["type"] == "live.frame":
            lease = self.leases.get(header["lease"])
            if lease is None:
                # An error without re (a frame has no id), and the connection stays.
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
            self.converting.add(lease)  # the push is answered later; model.save meanwhile is answered busy

            def finish() -> None:
                self.converting.discard(lease)
                try:
                    self.send(applied)
                except OSError:
                    pass  # the client went away

            timer = threading.Timer(server.push_delay, finish)
            timer.daemon = True
            timer.start()
        elif header["type"] == "ped.rig":
            server.ped_rigs.append((header, len(payload)))
            code = REFUSALS.get(server.feature_states.get("dct.link.pedRig", "entitled"))
            if code is not None:
                self.send_binary({"type": "ped.rig.result", "re": header["id"], "ok": False, "code": code}, b"")
                return
            threading.Thread(target=self.rig, args=(header, payload), daemon=True).start()
        elif header["type"] == "ped.add.chunk":
            upload = self.ped_upload
            if upload is None or upload["header"]["id"] != header["re"]:
                return  # a chunk of an add that already answered: dropped
            add = upload["header"]
            if header["index"] != len(upload["chunks"]):
                self.ped_upload = None
                self.answer_ped_add(add["id"], {"ok": False, "code": "upload-incomplete", "findings": []})
                return
            upload["chunks"].append(payload)
            if len(upload["chunks"]) < add["chunks"]:
                return
            self.ped_upload = None
            glb = b"".join(upload["chunks"])
            if len(glb) != add["glbLength"] or hashlib.sha256(glb).hexdigest() != add["sha256"]:
                self.answer_ped_add(add["id"], {"ok": False, "code": "upload-incomplete", "findings": []})
                return
            server.ped_adds.append((add, glb))
            if server.hold_ped_adds:
                self.waiting_ped_adds[add["id"]] = add
            else:
                self.answer_ped_add(add["id"])
        elif header["type"] == "item.add":
            files, offset = [], 0
            for entry in header["files"]:
                files.append((entry["name"], payload[offset : offset + entry["length"]]))
                offset += entry["length"]
            server.item_adds.append((header, files))
            code = server.fail.get("item.add") or server.refusal("item.add")
            if code is not None:  # busy, rate-limited, no-project ...: an error that answers the add
                self.send({"type": "error", "id": "e" + secrets.token_hex(3), "re": header["id"], "code": code})
            elif server.hold_adds:
                self.waiting_adds[header["id"]] = header  # "the user" decides later (release_adds or a cancel)
            else:
                self.answer_add(header["id"])


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
        #: The files skeleton.template answers with, per gender (``None``: a stand-in without bones). An error answer
        #: (game-required, busy) goes through ``fail`` like any other request.
        self.skeleton_files: Optional[Dict[str, List[Any]]] = None
        self.templates_sent: List[str] = []  # the gender of every skeleton.template answered
        #: The fields of the item.addResult that answers an item.add (default: added, no findings).
        self.add_result: Dict[str, Any] = {"ok": True, "binding": dict(ADDED_BINDING), "findings": []}
        #: Keep every item.add waiting, as while a dialog is open: release_adds() answers them with
        #: add_result, an item.addCancel with request-denied.
        self.hold_adds = False
        self.item_adds: List[Any] = []  # (header, [(name, data)]) per item.add received
        #: Message types the fake answers as unknown, as a DCT older than the add-on does.
        self.unknown_types: set = set()
        #: Leave item.addCancel (and the ped.addCancel of a waiting ped.add) unanswered (DCT already adds the cloth or
        #: creates the project); release_adds() and release_ped_adds() answer later.
        self.ignore_cancels = False
        #: The templates ped.templates lists (made-up models; ``group`` decides whether Show All is needed).
        self.ped_templates: List[Dict[str, Any]] = [
            {"model": "a_m_y_tester_01", "gender": "male", "pedType": "CIVMALE", "layout": "packed", "group": "ambient",
             "recommended": True},
            {"model": "a_m_m_tester_02", "gender": "male", "pedType": "CIVMALE", "layout": "packed",
             "group": "ambient", "recommended": False},
            {"model": "a_f_y_tester_01", "gender": "female", "pedType": "CIVFEMALE", "layout": "packed",
             "group": "ambient", "recommended": True},
            {"model": "mp_m_freemode_01", "gender": "male", "pedType": "CIVMALE", "layout": "streamed",
             "group": "freemode", "recommended": False},
        ]
        self.ped_template_requests: List[Dict[str, Any]] = []
        #: How long a ped.rig takes (it reports its six stages along the way), what its report says, and a refusal
        #: ``(code, reasons)`` instead of a rig.
        self.ped_rig_seconds = 0.3
        self.ped_rig_warnings: List[Dict[str, Any]] = []
        self.ped_rig_outcome = "ready"
        self.ped_rig_suggestion: Optional[str] = None
        self.ped_rig_refusal: Optional[Any] = None
        self.ped_rigs: List[Any] = []  # (header, payload length) per ped.rig received
        self.ped_rig_cancels: List[str] = []
        #: The fields of the ped.addResult that answers a ped.add (default: created, no findings).
        self.ped_add_result: Dict[str, Any] = {"ok": True, "findings": []}
        #: Keep every complete ped.add waiting, as while a dialog is open (release_ped_adds answers).
        self.hold_ped_adds = False
        self.ped_add_headers: List[Dict[str, Any]] = []
        self.ped_adds: List[Any] = []  # (header, GLB bytes) per complete upload
        self.ped_add_cancels: List[str] = []
        self.refused_frames: List[Any] = []  # (type, error code) of every frame refused undecoded
        self.add_cancels: List[str] = []  # the add ids item.addCancel named
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
        self.push_delay = 0.0
        self.lease_numbers = itertools.count(1)
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
        #: Feature id to state. welcome and event.entitlement report these rows, and gated requests are refused
        #: accordingly.
        self.feature_states: Dict[str, str] = {feature: "entitled" for feature in DCT_FEATURES}
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
        """The fake accepts an assertion for its audience and this connection's nonce, each one once."""
        claims = assertion_claims(assertion)
        if claims.get("aud") != "dct-creator-link-assertion" or claims.get("nonce") != server_nonce:
            return False
        if claims.get("jti") in self.used_jti:
            return False
        self.used_jti.add(claims.get("jti"))
        return True

    def feature_rows(self) -> List[Dict[str, str]]:
        """The feature states for welcome and event.entitlement."""
        return [{"id": feature, "state": state} for feature, state in self.feature_states.items()]

    def refusal(self, kind: str) -> Optional[str]:
        """The error code the fake answers a gated request with, or None when its feature is entitled."""
        return REFUSALS.get(self.feature_states.get(GATED_REQUESTS.get(kind, ""), "entitled"))

    def set_features(self, **states: str) -> None:
        """``set_features(services="needsUltimate")`` changes ``dct.link.services`` and tells every connected plugin
        (event.entitlement)."""
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

    def release_adds(self, result: Optional[Dict[str, Any]] = None) -> int:
        """The user chose Add for every waiting item.add: each answers with ``result`` (default ``add_result``)."""
        count = 0
        for connection in list(self.all_connections):
            waiting, connection.waiting_adds = connection.waiting_adds, {}
            for add_id in waiting:
                connection.answer_add(add_id, result)
                count += 1
        return count

    def release_ped_adds(self, result: Optional[Dict[str, Any]] = None) -> int:
        """The user chose Create (or, with ``result``, something else) for every waiting ped.add."""
        count = 0
        for connection in list(self.all_connections):
            waiting, connection.waiting_ped_adds = connection.waiting_ped_adds, {}
            for add_id in waiting:
                connection.answer_ped_add(add_id, result)
                count += 1
        return count

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
                   request_id: Optional[str] = None, lent_skeleton: bool = False) -> str:
        """Edit in connected app for a model: ``host.openModel`` with ``files`` as ``(name, bytes)``, the
        ``*.ydd.xml`` first; ``lent_skeleton`` says the model carries the ped's skeleton, lent because the cloth is
        stored without one. Returns the request id."""
        request_id = request_id or "om" + secrets.token_hex(3)
        header = {"type": "host.openModel", "id": request_id, "binding": binding or BINDING, "name": name,
                  "format": "ydd-xml", "files": [{"name": n, "length": len(data)} for n, data in files]}
        if lent_skeleton:
            header["lentSkeleton"] = True
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
