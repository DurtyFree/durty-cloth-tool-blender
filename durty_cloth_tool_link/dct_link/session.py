# SPDX-License-Identifier: MIT
# Copyright (c) Schmid Software Solutions (https://schmid-software.de)
"""The Creator Link session: finding DCT, the hello/challenge/pairing/auth flow, requests, events, live texture
streaming and model pushes.

A :class:`LinkSession` is driven in one of two ways (the same object supports both):

* **Polling** (Blender): call :meth:`LinkSession.poll` from ``bpy.app.timers`` every 20 to 50 ms. Every call
  does bounded work and returns quickly; callbacks run inside it, on the calling thread. Sign-in work
  (assertions, refresh, device sign-in) runs on a short-lived worker thread that only talks to gta.clothing and
  the secret store and never touches host APIs; ``poll`` picks up its result.
* **Background thread** (GIMP, Krita, Substance): call :meth:`LinkSession.start_thread`. Callbacks then run on
  that thread unless a ``dispatch`` function moves them (for example onto the Qt or GLib main loop). Every
  public method is safe to call from any thread.

Threading contract for hosts: callbacks and ``pixel_source`` functions run on the thread that drives the
session (:meth:`LiveSurface.save` reads pending pixels on the calling thread). Token source calls and every
pairing store access run on a short-lived worker thread, never on the thread that drives the session
(``token_threads=False`` runs them inline instead, for hosts without threads). A host whose own API may only be
used on its UI thread (GIMP, Krita, Substance 3D Painter) reads its pixels on that thread and hands them over with
:meth:`LiveSurface.update` or from a snapshot, or passes a ``dispatch`` function for callbacks; it never calls its
host API from the session thread. A ``pixel_source`` must never wait for a thread that may call
:meth:`LiveSurface.save`, because a save waits for a pixel read that is in progress. An exception raised by a
callback or a ``pixel_source`` is logged and reported through the ``error`` event; it never stops the session.

Host calls are never made while the session holds its internal lock, so a callback may call back into the
session.
"""

from __future__ import annotations

import base64
import collections
import hashlib
import hmac
import json
import logging
import os
import pathlib
import random
import re
import secrets
import socket
import struct
import threading
import time
from typing import Any, Callable, Dict, Iterable, List, NamedTuple, Optional, Sequence, Set, Tuple, Union

from . import protocol
from .protocol import ProtocolError
from .ws import Event, WebSocketClient, WebSocketError

__all__ = [
    "LinkSession",
    "LinkError",
    "PluginInfo",
    "Request",
    "LiveSurface",
    "ModelBundle",
    "PairingPrompt",
    "PairingRequired",
    "SignInPrompt",
    "Pairing",
    "DiscoveredEndpoint",
    "ASSERTION_AUDIENCE",
    "discovery_file_path",
    "installed_user_data_dir",
    "read_discovery_file",
    "trusted_update_url",
    "server_proof",
    "client_proof",
    "b64url_encode",
    "b64url_decode",
]

_log = logging.getLogger(__name__)
Rect = Tuple[int, int, int, int]
Handler = Callable[..., Any]

#: The audience of a sign-in assertion meant for DCT.
ASSERTION_AUDIENCE = "dct-creator-link-assertion"
#: Update and download links a host may open for the user.
UPDATE_URL_PREFIXES = ("https://gta.clothing/", "https://link.gta.clothing/")

# --------------------------------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------------------------------


def b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def b64url_decode(text: str) -> bytes:
    if not isinstance(text, str) or not re.fullmatch(r"[A-Za-z0-9_-]*", text) or len(text) % 4 == 1:
        raise ValueError("not unpadded base64url")
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def server_proof(secret: bytes, client_nonce: bytes, server_nonce: bytes) -> bytes:
    """DCT's proof: HMAC-SHA256(secret, b"srv" + clientNonce + serverNonce), 67 message bytes."""
    return hmac.new(secret, b"srv" + client_nonce + server_nonce, hashlib.sha256).digest()


def client_proof(secret: bytes, server_nonce: bytes, client_nonce: bytes) -> bytes:
    """The plugin's proof: HMAC-SHA256(secret, b"cli" + serverNonce + clientNonce), 67 message bytes."""
    return hmac.new(secret, b"cli" + server_nonce + client_nonce, hashlib.sha256).digest()


def trusted_update_url(url: Any) -> Optional[str]:
    """``url`` when it is a link a host may open (``https://gta.clothing/...`` or ``https://link.gta.clothing/...``,
    printable ASCII, no backslash or ``@``), otherwise ``None``."""
    if (
        isinstance(url, str)
        and len(url) <= protocol.MAX_UPDATE_URL_LENGTH
        and re.fullmatch(r"[!-~]+", url)
        and "\\" not in url
        and "@" not in url
        and url.startswith(UPDATE_URL_PREFIXES)
    ):
        return url
    return None


def _assertion_claims(assertion: str) -> Dict[str, Any]:
    try:
        payload = assertion.split(".")[1]
        value = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)).decode("utf-8"))
    except (ValueError, IndexError, UnicodeDecodeError, AttributeError):
        return {}
    return value if isinstance(value, dict) else {}


class LinkError(Exception):
    """A request or session failure. ``code`` is a protocol error code or one of the local codes
    ``disconnected``, ``timeout``, ``superseded``, ``cancelled``, ``closed``, ``server-proof-invalid``,
    ``assertion-invalid``, ``untrusted-endpoint``, ``pairing-expired``, ``pairing-not-saved``,
    ``pairing-store-failed``, ``pixel-source-failed``, ``callback-failed`` and ``internal-error``."""

    def __init__(self, code: str, message: str = "") -> None:
        super().__init__(f"{code}: {message}" if message else code)
        self.code = code
        self.message = message


class PluginInfo(NamedTuple):
    """Who is connecting. ``kind`` is one of :data:`protocol.PLUGIN_KINDS`."""

    kind: str
    version: str
    channel: str
    host_name: str
    host_version: str
    display_name: Optional[str] = None

    def check(self) -> None:
        if self.kind not in protocol.PLUGIN_KINDS:
            raise ValueError("unknown plugin kind")
        if not protocol.is_semver(self.version):
            raise ValueError("plugin version must be semantic (major.minor.patch)")
        if self.channel not in protocol.CHANNELS:
            raise ValueError("unknown channel")
        if not protocol.is_text(self.host_name) or not protocol.is_host_version(self.host_version):
            raise ValueError("invalid host name or version")


class Pairing(NamedTuple):
    """What DCT granted when the user paired this plugin. The secret is 32 raw bytes."""

    client_id: str
    secret: bytes


class PairingPrompt(NamedTuple):
    """Ask the user for the six-digit code DCT shows. ``error`` is set after a wrong code."""

    expires_in: int
    attempts_left: int
    error: Optional[str] = None


class PairingRequired(NamedTuple):
    """A DCT did not accept this plugin's stored pairing. ``reason`` is ``not-recognized`` (DCT does not know the
    plugin), ``refused`` (DCT proved the old secret but refused the plugin) or ``removed`` (the user removed the
    plugin in DCT). ``endpoint_trusted`` is true for the DCT named by the discovery file (or an explicit ``port``)
    and false for one found by probing ``port``. Nothing changes until the user agrees: then
    :meth:`LinkSession.confirm_repair` pairs again with that DCT (the discovery file's DCT when there is one,
    otherwise the probed ``port`` of this event)."""

    reason: str
    endpoint_trusted: bool
    port: int


class SignInPrompt(NamedTuple):
    """A gta.clothing device sign-in is waiting. DCT was asked to approve it; the user may also open the link."""

    user_code: str
    verification_uri: str
    verification_uri_complete: Optional[str]
    assisted_by_dct: Optional[bool] = None


def _sanitize_text(value: str, limit: int = protocol.MAX_TEXT_LENGTH) -> str:
    cleaned = re.sub("[\u0000-\u001f\u007f-\u009f\ud800-\udfff]", "", value).strip()
    return cleaned[:limit] or "Creator Link plugin"


# --------------------------------------------------------------------------------------------------
# DCT discovery
# --------------------------------------------------------------------------------------------------

LINK_PORTS: Tuple[int, ...] = tuple(range(protocol.DEFAULT_PORT, protocol.PORT_RANGE_END + 1))


class DiscoveredEndpoint(NamedTuple):
    port: int
    pid: Optional[int]
    path: str
    protocol_min: int
    protocol_max: int


def installed_user_data_dir() -> Optional[pathlib.Path]:
    """An installed DCT's user data folder, ``%LOCALAPPDATA%\\DurtyClothTool\\UserData`` (Windows only)."""
    if os.name != "nt":
        return None
    base = os.environ.get("LOCALAPPDATA")
    if not base:
        return None
    return pathlib.Path(base) / "DurtyClothTool" / "UserData"


def discovery_file_path(user_data_dir: Optional[Union[str, os.PathLike]] = None) -> Optional[pathlib.Path]:
    """``<user data>\\CreatorLink\\endpoint.json``. Without ``user_data_dir`` this is the installed DCT's folder;
    a portable DCT keeps its user data in ``<portable folder>\\UserData``, which a host may pass instead. DCT
    deletes the file when the link stops, so a missing file only means the plugin probes the port range."""
    base = pathlib.Path(user_data_dir) if user_data_dir is not None else installed_user_data_dir()
    if base is None:
        return None
    return base / "CreatorLink" / "endpoint.json"


def _process_alive(pid: int) -> bool:
    """Best effort. Unknown answers count as alive, so a doubtful file is still tried."""
    if os.name == "nt":
        try:
            import ctypes
            from ctypes import wintypes

            kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
            kernel32.OpenProcess.restype = wintypes.HANDLE
            kernel32.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
            kernel32.GetExitCodeProcess.argtypes = (wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD))
            kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
            handle = kernel32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
            if not handle:
                return ctypes.get_last_error() != 87  # ERROR_INVALID_PARAMETER: no such process
            try:
                code = wintypes.DWORD()
                if not kernel32.GetExitCodeProcess(handle, ctypes.byref(code)):
                    return True
                return code.value == 259  # STILL_ACTIVE
            finally:
                kernel32.CloseHandle(handle)
        except (OSError, AttributeError, ValueError):
            return True
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except OSError:
        return True
    return True


def read_discovery_file(
    path: Optional[Union[str, os.PathLike]] = None, ports: Sequence[int] = LINK_PORTS
) -> Optional[DiscoveredEndpoint]:
    """Reads DCT's discovery file. It is a hint and untrusted input: anything unexpected yields ``None`` and the
    plugin probes the port range instead.

    Expected content: ``{"port": 47820, "pid": 1234, "path": "/dct/link/v1", "protocolMin": 1, "protocolMax": 1}``.
    The file is at most 4 KiB, the port is one of ``ports`` (the link range), the path is the link path, the
    protocol range includes a major this client speaks, and the process is still running.
    """
    target = pathlib.Path(path) if path is not None else discovery_file_path()
    if target is None:
        return None
    try:
        if not target.is_file() or target.stat().st_size > 4096:
            return None
        data = json.loads(target.read_bytes().decode("utf-8"))
    except (OSError, ValueError, RecursionError):
        return None
    if not isinstance(data, dict):
        return None
    port, pid, link_path = data.get("port"), data.get("pid"), data.get("path")
    low, high = data.get("protocolMin"), data.get("protocolMax")
    if type(port) is not int or port not in ports:
        return None
    if link_path != protocol.PATH:
        return None
    if type(low) is not int or type(high) is not int or not 1 <= low <= high <= protocol.MAX_PROTOCOL_MAJOR:
        return None
    if high < protocol.MIN_SUPPORTED_MAJOR or low > protocol.MAX_SUPPORTED_MAJOR:
        return None  # no major in common: nothing to gain from connecting there
    if pid is not None and (type(pid) is not int or pid <= 0 or pid > 0xFFFFFFFF):
        return None
    if pid is not None and not _process_alive(pid):
        return None  # a file left behind by a DCT that exited
    return DiscoveredEndpoint(port, pid, link_path, low, high)


def _port_from(raw: bytes) -> int:
    return (raw[0] << 8) | raw[1]  # network byte order in the low 16 bits of a DWORD


def _tcp_owner_pid(local: Tuple[Any, ...], remote: Tuple[Any, ...]) -> Optional[int]:
    """Windows only: the process that owns the TCP connection whose local end is ``local`` and whose remote end is
    ``remote`` (``GetExtendedTcpTable``). For our connection to DCT, ``local`` is DCT's address and ``remote`` is
    ours. ``None`` when it cannot be told."""
    if os.name != "nt":
        return None
    try:
        import ctypes
        from ctypes import wintypes

        v6 = ":" in str(local[0])
        family = 23 if v6 else 2  # AF_INET6, AF_INET
        get_table = ctypes.WinDLL("iphlpapi").GetExtendedTcpTable
        get_table.restype = wintypes.DWORD
        get_table.argtypes = (ctypes.c_void_p, ctypes.POINTER(wintypes.DWORD), wintypes.BOOL, wintypes.ULONG,
                              ctypes.c_int, wintypes.ULONG)
        size = wintypes.DWORD(0)
        result = get_table(None, ctypes.byref(size), False, family, 4, 0)  # TCP_TABLE_OWNER_PID_CONNECTIONS
        buffer = None
        for _ in range(4):
            if result != 122:  # ERROR_INSUFFICIENT_BUFFER
                break
            size = wintypes.DWORD(size.value + 4096)  # the table can grow between the two calls
            buffer = ctypes.create_string_buffer(size.value)
            result = get_table(buffer, ctypes.byref(size), False, family, 4, 0)
        if result != 0 or buffer is None:
            return None
        raw = buffer.raw
        count = struct.unpack_from("<I", raw, 0)[0]
        if v6:
            want_local = socket.inet_pton(socket.AF_INET6, str(local[0]).split("%")[0])
            want_remote = socket.inet_pton(socket.AF_INET6, str(remote[0]).split("%")[0])
            layout, row_size = "<16sI4s16sI4sII", 56
        else:
            want_local, want_remote = socket.inet_aton(local[0]), socket.inet_aton(remote[0])
            layout, row_size = "<I4s4s4s4sI", 24
        for index in range(count):
            offset = 4 + index * row_size
            if offset + row_size > len(raw):
                break
            row = struct.unpack_from(layout, raw, offset)
            if v6:
                l_addr, _, l_port, r_addr, _, r_port, _, pid = row
            else:
                _, l_addr, l_port, r_addr, r_port, pid = row
            if (l_addr == want_local and _port_from(l_port) == local[1] and r_addr == want_remote
                    and _port_from(r_port) == remote[1]):
                return int(pid)
        return None
    except (OSError, AttributeError, ValueError, struct.error, TypeError):
        return None


def _session_id(pid: int) -> Optional[int]:
    """Windows only: the Windows session ``pid`` runs in, or ``None``."""
    if os.name != "nt":
        return None
    try:
        import ctypes
        from ctypes import wintypes

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.ProcessIdToSessionId.restype = wintypes.BOOL
        kernel32.ProcessIdToSessionId.argtypes = (wintypes.DWORD, ctypes.POINTER(wintypes.DWORD))
        session = wintypes.DWORD()
        if not kernel32.ProcessIdToSessionId(pid, ctypes.byref(session)):
            return None
        return int(session.value)
    except (OSError, AttributeError, ValueError):
        return None


def _same_session(pid: int) -> Optional[bool]:
    """Whether ``pid`` runs in this process's Windows session (``None`` when that cannot be told)."""
    if pid == os.getpid():
        return True
    theirs, ours = _session_id(pid), _session_id(os.getpid())
    if theirs is None or ours is None:
        return None
    return theirs == ours


# --------------------------------------------------------------------------------------------------
# Requests
# --------------------------------------------------------------------------------------------------


class Request:
    """A pending request. Resolves with the response message (a dict, a :class:`protocol.BinaryMessage`, or for
    ``open_live`` a :class:`LiveSurface`) or fails with :class:`LinkError`."""

    def __init__(self, session: "LinkSession", request_id: str, message_type: str, timeout: Optional[float]) -> None:
        self.session = session
        self.id = request_id
        self.type = message_type
        self.lease: Optional[str] = None
        self.timeout = timeout
        self.deadline = None if timeout is None else session._clock() + timeout
        self._done = threading.Event()
        self._result: Any = None
        self._error: Optional[LinkError] = None
        self._callbacks: List[Callable[["Request"], Any]] = []
        self.transform: Optional[Callable[[Any], Any]] = None

    @property
    def done(self) -> bool:
        return self._done.is_set()

    @property
    def error(self) -> Optional[LinkError]:
        return self._error

    def result(self) -> Any:
        """The result of a finished request; raises its :class:`LinkError`."""
        if not self._done.is_set():
            raise RuntimeError("the request has not finished")
        if self._error is not None:
            raise self._error
        return self._result

    def add_done_callback(self, callback: Callable[["Request"], Any]) -> None:
        """Runs ``callback(request)`` when the request finishes (at once when it already has)."""
        with self.session._lock:
            if not self._done.is_set():
                self._callbacks.append(callback)
                return
        self.session._dispatch(callback, self)

    def wait(self, timeout: Optional[float] = None) -> Any:
        """Waits for the result. With a background thread this blocks on an event; without one it drives
        :meth:`LinkSession.poll` itself (convenient in scripts, but it blocks a host's UI while it waits)."""
        session = self.session
        if session._thread is not None and threading.current_thread() is session._thread:
            raise RuntimeError("wait() would deadlock on the session thread; use add_done_callback")
        end = None if timeout is None else session._clock() + timeout
        while not self._done.is_set():
            remaining = None if end is None else end - session._clock()
            if remaining is not None and remaining <= 0:
                raise LinkError("timeout", f"{self.type} did not finish in time")
            if session._thread is not None:
                self._done.wait(0.1 if remaining is None else min(remaining, 0.1))
            else:
                session.poll()
                if not self._done.is_set():
                    session._wait_io(0.01 if remaining is None else min(remaining, 0.01))
        return self.result()

    def _finish(self, result: Any = None, error: Optional[LinkError] = None) -> List[Callable[["Request"], Any]]:
        if self._done.is_set():
            return []
        if error is None and self.transform is not None:
            try:
                result = self.transform(result)
            except LinkError as exc:
                error = exc
        self._result, self._error = result, error
        self._done.set()
        callbacks, self._callbacks = self._callbacks, []
        return callbacks


#: Requests DCT runs as services: at most ``MAX_SERVICE_IN_FLIGHT`` of them (model pushes included) are in
#: flight per connection; DCT answers more with ``busy``, so the session queues the rest.
SERVICE_TYPES = frozenset({"texture.read", "texture.validate", "uv.layout", "model.glb", "body.glb", "model.push"})
MAX_SERVICE_IN_FLIGHT = 2

# Which response types finish which request types (always matched by `re`).
_RESPONSES: Dict[str, Tuple[str, ...]] = {
    "context.get": ("context.snapshot",),
    "live.open": ("live.opened",),
    "live.save": ("live.saveResult",),
    "live.discard": ("live.closed",),
    "live.close": ("live.closed",),
    "texture.read": ("texture.data",),
    "texture.validate": ("texture.findings",),
    "uv.layout": ("uv.layout.image",),
    "model.glb": ("model.glb.data",),
    "body.glb": ("body.glb.data",),
    "model.push": ("model.applied",),
    "model.save": ("model.saveResult",),
    "model.discard": ("model.closed",),
}


class _ThreadTask:
    """Runs a plain (blocking) token source call on a daemon worker thread. The worker only does that call; the
    session polls :attr:`done` from the thread that drives it."""

    def __init__(self, call: Callable[[], Any]) -> None:
        self._value: Any = None
        self._error: Optional[BaseException] = None
        self._finished = threading.Event()

        def work() -> None:
            try:
                self._value = call()
            except BaseException as exc:  # handed back to the session, which reports it
                self._error = exc
            finally:
                self._finished.set()

        threading.Thread(target=work, name="dct-link-sign-in", daemon=True).start()

    @property
    def done(self) -> bool:
        return self._finished.is_set()

    def poll(self) -> bool:
        return self._finished.is_set()

    def result(self) -> Any:
        if self._error is not None:
            raise self._error
        return self._value

    def cancel(self) -> None:
        pass  # the worker finishes its one call; the session ignores the result


class _CallTask:
    """Adapts a plain (blocking) token source call to the task shape the session drives, inline."""

    def __init__(self, call: Callable[[], Any]) -> None:
        self._call = call
        self.done = False
        self._value: Any = None
        self._error: Optional[BaseException] = None

    def poll(self) -> bool:
        if not self.done:
            try:
                self._value = self._call()
            except Exception as exc:
                self._error = exc
            self.done = True
        return True

    def result(self) -> Any:
        if self._error is not None:
            raise self._error
        return self._value

    def cancel(self) -> None:
        self.done = True


# --------------------------------------------------------------------------------------------------
# Live surfaces
# --------------------------------------------------------------------------------------------------

_MAX_DIRTY_RECTS = 8


def _union(a: Rect, b: Rect) -> Rect:
    x0, y0 = min(a[0], b[0]), min(a[1], b[1])
    x1, y1 = max(a[0] + a[2], b[0] + b[2]), max(a[1] + a[3], b[1] + b[3])
    return (x0, y0, x1 - x0, y1 - y0)


def _area(rect: Rect) -> int:
    return rect[2] * rect[3]


def _merge_rect(rects: List[Rect], rect: Rect) -> List[Rect]:
    """Adds ``rect`` to a small set of dirty rectangles. Rectangles that overlap or nearly touch merge (one
    frame is then cheaper than two); distant strokes stay separate; past eight they become one bounding box."""
    pending = rect
    rest = list(rects)
    merged = True
    while merged:
        merged = False
        for index, other in enumerate(rest):
            union = _union(other, pending)
            if _area(union) <= (_area(other) + _area(pending)) * 1.25:
                pending = union
                del rest[index]
                merged = True
                break
    rest.append(pending)
    if len(rest) > _MAX_DIRTY_RECTS:
        box = rest[0]
        for other in rest[1:]:
            box = _union(box, other)
        rest = [box]
    return rest


class LiveSurface:
    """A live texture in DCT's preview, identified by its lease.

    Feed it pixels with :meth:`update` (the surface keeps a full RGBA8 copy, ``width * height * 4`` bytes) or with
    :meth:`mark_dirty` plus the ``pixel_source`` given to :meth:`LinkSession.open_live` (no copy; the source is asked
    for each dirty rectangle when frames are sent, on the thread that drives the session, never while the session
    holds its lock). Changes made while frames are still being sent merge, so DCT always receives the newest
    pixels and never a backlog.

    DCT shows and saves a lease only after one frame covering the whole surface, so the first frame of every lease
    is full bounds whatever was marked dirty. Start with a full :meth:`update`. :meth:`resend_full` makes the next
    frame full bounds again.

    A failing ``pixel_source`` keeps its dirty area for a later try (after a second), sets :attr:`last_error` and
    is reported through the session's ``live-error`` and ``error`` events.
    """

    def __init__(
        self,
        session: "LinkSession",
        message: Dict[str, Any],
        pixel_source: Optional[Callable[[int, int, int, int], Union[bytes, bytearray, memoryview]]],
    ) -> None:
        self.session = session
        self.lease: str = message["lease"]
        self.binding: Dict[str, str] = dict(message["binding"])
        self.target: str = message["target"]
        self.width: int = message["width"]
        self.height: int = message["height"]
        self.revision = 0
        self.applied_revision = 0
        self.state: Optional[str] = None
        self.closed = False
        self.close_reason: Optional[str] = None
        self.frames_sent = 0
        self.last_error: Optional[BaseException] = None
        self._pixel_source = pixel_source
        self._pixels: Optional[bytearray] = None
        self._dirty: List[Rect] = []
        self._full_sent = False
        self._in_flight = False
        self._retry_at = 0.0
        self._ending: Optional[str] = None  # "live.close" or "live.discard" once one was sent
        self._lock = threading.Lock()
        # Held from taking the dirty area until its frames are queued, so a save never overtakes a frame that is
        # being read (taken before the session lock, never while holding it).
        self._producing = threading.RLock()

    @property
    def ending(self) -> bool:
        """True once :meth:`close` or :meth:`discard` was sent; no more frames go out for this lease."""
        return self._ending is not None or self.closed

    def _check_open(self) -> None:
        if self.closed:
            raise LinkError("closed", "the live surface is closed")
        if self._ending is not None:
            raise LinkError("closed", "the live surface is closing")

    def _check_rect(self, rect: Optional[Rect]) -> Rect:
        if rect is None:
            return (0, 0, self.width, self.height)
        x, y, w, h = (int(v) for v in rect)
        if x < 0 or y < 0 or w < 1 or h < 1 or x + w > self.width or y + h > self.height:
            raise ValueError("the rectangle is outside the surface")
        return (x, y, w, h)

    def update(self, pixels: Union[bytes, bytearray, memoryview], rect: Optional[Rect] = None) -> None:
        """Copies ``pixels`` (RGBA8 rows top to bottom, ``w * h * 4`` bytes) into ``rect`` (default: all)."""
        self._check_open()
        x, y, w, h = self._check_rect(rect)
        source = memoryview(pixels).cast("B")
        if source.nbytes != w * h * 4:
            raise ValueError("pixels must hold w * h * 4 bytes")
        stride, row = self.width * 4, w * 4
        with self._lock:
            if self._pixels is None:
                self._pixels = bytearray(self.width * self.height * 4)
            target = self._pixels
            if x == 0 and w == self.width:
                start = y * stride
                target[start : start + row * h] = source
            else:
                for line in range(h):
                    start = (y + line) * stride + x * 4
                    target[start : start + row] = source[line * row : (line + 1) * row]
            self._dirty = _merge_rect(self._dirty, (x, y, w, h))
        self.session._wake()

    def mark_dirty(self, rect: Optional[Rect] = None) -> None:
        """Marks ``rect`` changed; the ``pixel_source`` supplies its pixels when the next frame is sent."""
        self._check_open()
        if self._pixel_source is None and self._pixels is None:
            raise RuntimeError("mark_dirty needs a pixel_source or an earlier update()")
        checked = self._check_rect(rect)
        with self._lock:
            self._dirty = _merge_rect(self._dirty, checked)
        self.session._wake()

    def resend_full(self) -> None:
        """Sends the whole surface with the next frame (for example after DCT lost the preview)."""
        with self._lock:
            self._full_sent = False
            self._dirty = [(0, 0, self.width, self.height)]
        self.session._wake()

    def save(self, mode: str = "replace", timeout: Optional[float] = 60.0) -> Request:
        """Saves the surface into the project (``replace`` or ``newVariation``). A frame the session is reading at
        this moment is finished first, then the pending pixels are read on the calling thread and sent, and then
        the save: it always covers the newest pixels."""
        if mode not in protocol.SAVE_MODES:
            raise ValueError("mode must be 'replace' or 'newVariation'")
        return self.session._live_save(self, mode, timeout)

    def discard(self, timeout: Optional[float] = 10.0) -> Request:
        """Drops unsaved changes in DCT's preview. It ends the lease; resolves with ``live.closed``. Pending
        pixels are dropped and nothing more is sent for this lease."""
        return self.session._live_end(self, "live.discard", timeout)

    def close(self, timeout: Optional[float] = 10.0) -> Request:
        """Ends the lease; resolves with ``live.closed``. Pending pixels are dropped. After :meth:`discard` (or a
        first :meth:`close`) it sends nothing and waits for the same ``live.closed``."""
        return self.session._live_end(self, "live.close", timeout)

    def _take_dirty(self) -> List[Rect]:
        with self._lock:
            if not self._dirty or self.closed or self._ending is not None:
                return []
            rects, self._dirty = self._dirty, []
            if not self._full_sent:
                return [(0, 0, self.width, self.height)]
            return rects

    def _restore_dirty(self, rects: Iterable[Rect]) -> None:
        with self._lock:
            if self._ending is not None or self.closed:
                return
            for rect in rects:
                self._dirty = _merge_rect(self._dirty, rect)

    def _pixels_for(self, rect: Rect) -> bytes:
        x, y, w, h = rect
        if self._pixel_source is not None:
            payload = bytes(self._pixel_source(x, y, w, h))
            if len(payload) != w * h * 4:
                raise ValueError("pixel_source returned the wrong number of bytes")
            return payload
        with self._lock:
            stride, row = self.width * 4, w * 4
            if self._pixels is None:
                return bytes(w * h * 4)
            if x == 0 and w == self.width:
                return bytes(self._pixels[y * stride : (y + h) * stride])
            view = memoryview(self._pixels)
            return b"".join(view[(y + line) * stride + x * 4 : (y + line) * stride + x * 4 + row] for line in range(h))


# --------------------------------------------------------------------------------------------------
# Model bundles
# --------------------------------------------------------------------------------------------------


class ModelBundle:
    """The files of one ``model.push``: ``ydd-xml`` (one ``*.ydd.xml`` and any ``*.dds``) or ``glb`` (one
    ``*.glb``). Names are bare file names, unique ignoring case."""

    def __init__(self, fmt: str, files: Sequence[Tuple[str, Union[bytes, bytearray, memoryview]]]) -> None:
        self.format = fmt
        self.files = [(name, memoryview(data).cast("B")) for name, data in files]
        entries = [{"name": name, "length": data.nbytes} for name, data in self.files]
        if protocol.model_push_problem(fmt, entries) is not None:
            raise ValueError(
                "a model push needs bare, unique file names: ydd-xml takes one *.ydd.xml plus *.dds files, "
                "glb takes exactly one *.glb, and no file may be empty"
            )
        self.size = sum(entry["length"] for entry in entries)
        if self.size > protocol.MAX_BINARY_PAYLOAD_BYTES:
            raise ValueError("the model is larger than one binary frame allows (64 MiB)")

    @classmethod
    def from_paths(cls, fmt: str, paths: Iterable[Union[str, os.PathLike]]) -> "ModelBundle":
        files = []
        for path in paths:
            p = pathlib.Path(path)
            files.append((p.name, p.read_bytes()))
        if fmt == protocol.MODEL_YDD_XML:
            files.sort(key=lambda item: (not item[0].lower().endswith(".ydd.xml"), item[0].lower()))
        return cls(fmt, files)

    def entries(self) -> List[Dict[str, Any]]:
        return [{"name": name, "length": data.nbytes} for name, data in self.files]


# --------------------------------------------------------------------------------------------------
# The session
# --------------------------------------------------------------------------------------------------

_BACKOFF = (0.5, 1.0, 2.0, 4.0, 8.0, 15.0, 30.0)
#: The longest wait a server's Retry-After may impose before the next connection.
_MAX_RETRY_AFTER = 300.0
#: How long a request that timed out locally keeps its service slot while DCT has not answered it yet.
_SLOT_HOLD_SECONDS = 120.0

# Session states.
IDLE = "idle"
CONNECTING = "connecting"
HELLO = "hello"
PAIRING = "pairing"
SIGNING_IN = "signing-in"
AUTHENTICATING = "authenticating"
READY = "ready"
WAITING = "waiting"
STOPPED = "stopped"
_HANDSHAKE_STATES = (HELLO, PAIRING, SIGNING_IN, AUTHENTICATING)


class LinkSession:
    """One plugin's link to DCT. See the module documentation for threading.

    ``pairing_store`` has ``load() -> Pairing | None``, ``save(Pairing)`` and ``clear()``; the session never clears
    it and replaces it only with a newly granted pairing. It is used on a worker thread (see the module
    documentation).

    ``token_source`` has ``mint_assertion(server_nonce) -> str | None`` (a sign-in assertion bound to this
    connection, or ``None`` when nobody is signed in) and ``start_device_sign_in()`` returning a flow with
    ``user_code``, ``verification_uri``, ``verification_uri_complete``, ``expires_at`` (optional) and ``poll()``
    (truthy once approved; it must not block). Optional: ``begin_mint_assertion(nonce)`` and
    ``begin_device_sign_in()`` returning tasks (``poll() -> bool``, ``result()``, ``cancel()``), used instead of
    running the plain calls on a worker thread; ``signed_out_by_user`` (true after an explicit sign-out: the
    session then waits for :meth:`sign_in` instead of starting a device sign-in); ``allow_sign_in()``.
    :class:`dct_link.auth.LinkAuth` implements all of it. The session never sends an access or refresh token to
    DCT, and it checks each assertion's audience and nonce before sending it.

    ``discovery_path`` is one discovery file or several to try in order (for example
    ``discovery_file_path(<portable folder>/UserData)`` before the installed one); by default the installed DCT's
    file is read. ``port`` skips discovery and connects to that port only. ``link_ports`` replaces the probed
    port range (tests use it to stay off the real ports).

    Pairing safety: a new pairing (the first one, or one the user agreed to) is requested only from the DCT named
    by a discovery file when one exists. On Windows the session also checks that the process behind the
    connection is that DCT (its process id) and runs in the same Windows session; when a discovery file exists and
    this cannot be confirmed, it does not pair. After DCT answered ``pairing-not-started`` (nobody clicked "Connect
    an app"), the session asks for a code again only when the user asks (:meth:`retry_pairing`), so an unpaired
    plugin never takes a code meant for another one.

    Events (``session.on(name, handler)``): ``state(state)``, ``ready(welcome)``, ``pairing(PairingPrompt)``,
    ``pairing-required(PairingRequired)``, ``sign-in(SignInPrompt)``, ``selection(message)``, ``project(message)``,
    ``entitlement(message)``, ``open-texture(BinaryMessage)``, ``live-status(surface, message)``,
    ``live-closed(surface, reason)``, ``live-error(surface, LinkError)``, ``model-applied(message)``,
    ``model-closed(message)``, ``incompatible(message)`` (``updateUrl`` only when it is a trusted link),
    ``signed-out()`` (the user signed out; call :meth:`sign_in` when they want to sign in again),
    ``dct-signed-out()`` (DCT itself is signed out; the session keeps trying about every 30 seconds and connects
    once DCT is signed in again, or at once after :meth:`start`), ``error(LinkError)``,
    ``disconnected(code, reason)``.
    """

    def __init__(
        self,
        plugin: PluginInfo,
        *,
        pairing_store: Any,
        token_source: Any,
        port: Optional[int] = None,
        host: str = "127.0.0.1",
        discovery_path: Optional[Union[str, os.PathLike, Sequence[Union[str, os.PathLike]]]] = None,
        use_discovery_file: bool = True,
        link_ports: Optional[Sequence[int]] = None,
        reconnect: bool = True,
        dispatch: Optional[Callable[..., Any]] = None,
        request_timeout: float = 30.0,
        handshake_timeout: float = 15.0,
        max_auth_refusals: int = 3,
        token_threads: bool = True,
        clock: Callable[[], float] = time.monotonic,
        ws_options: Optional[Dict[str, Any]] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        plugin.check()
        self.plugin = plugin
        self.pairing_store = pairing_store
        self.token_source = token_source
        self.host = host
        self.fixed_port = port
        self.discovery_path = discovery_path
        self.use_discovery_file = use_discovery_file
        self.link_ports: Tuple[int, ...] = tuple(link_ports) if link_ports else LINK_PORTS
        self.reconnect = reconnect
        self.request_timeout = request_timeout
        self.handshake_timeout = handshake_timeout
        self.max_auth_refusals = max_auth_refusals
        self.token_threads = token_threads
        self._dispatcher = dispatch
        self._clock = clock
        self._ws_options = dict(ws_options or {})
        self._log = logger or _log

        self._lock = threading.RLock()
        self._handlers: Dict[str, List[Handler]] = collections.defaultdict(list)
        self._calls: List[Tuple[Callable[..., Any], Tuple[Any, ...]]] = []
        self._thread: Optional[threading.Thread] = None
        self._stop_thread = threading.Event()

        self.state = IDLE
        self.welcome: Optional[Dict[str, Any]] = None
        self.features: Dict[str, str] = {}
        self.account_name: Optional[str] = None
        self.endpoint_port: Optional[int] = None
        self.last_error: Optional[LinkError] = None
        self._ws: Optional[WebSocketClient] = None
        self._endpoint_source = "probe"
        self._probes: List[Tuple[WebSocketClient, str]] = []
        self._closing: List[WebSocketClient] = []
        self._want = False
        self._retry_at = 0.0
        self._attempt = 0
        self._epoch = 0
        self._next_id = 0
        self._pending: Dict[str, Request] = {}
        self._surfaces: Dict[str, LiveSurface] = {}
        self._skip_ports: Set[int] = set()  # probed ports that are not (or not our) DCT
        self._answered = False
        self._deadline: Optional[float] = None
        self._client_nonce = b""
        self._server_nonce = b""
        self._pairing: Optional[Pairing] = None
        self._hello_paired = False
        self._server_proved = False
        self._handshake_ids: Dict[str, str] = {}
        self._pair_attempts = 0
        self._pairing_pending = False
        self._repair_confirmed = False
        self._pairing_required_sent = False
        self._token_task: Optional[Tuple[int, str, Any]] = None
        self._sign_in: Any = None
        self._auth_refusals = 0
        self._refusal_epoch = -1
        self._model_lease: Optional[str] = None
        self._push_request: Optional[Request] = None
        self._push_waiting: Optional[Tuple[ModelBundle, Optional[Dict[str, str]], Request]] = None
        self._service_queue: "collections.deque[Tuple[Request, Dict[str, Any]]]" = collections.deque()
        self._service_in_flight: Set[str] = set()
        self._close_hint: Optional[str] = None
        self._not_started_reported = False
        self._awaiting_pair_click = False  # DCT said pairing-not-started: only the user asks for a code again
        self._discovered: Optional[DiscoveredEndpoint] = None  # the discovery file read for this connection
        self._repair_port: Optional[int] = None  # a probed DCT the user agreed to pair with again
        self._last_required: Optional[PairingRequired] = None
        self._unsaved_pairing: Optional[Pairing] = None  # granted, but the pairing store could not keep it
        self._sign_in_requested = False  # sign_in() was called; the next sign-in check clears a remembered sign-out
        self._assisted_flow: Any = None  # the device sign-in DCT was already asked to approve
        self._dct_signed_out = False
        self._slot_release_at: Dict[str, float] = {}  # timed-out service requests DCT has not answered yet
        self._push_id: Optional[str] = None  # the model push DCT has not answered yet
        self._saves_waiting: List[Request] = []  # model saves waiting for a push in flight
        self._thread_generation = 0

    # ---- events and host calls ---------------------------------------------------------------------

    def on(self, event: str, handler: Handler) -> Handler:
        """Registers ``handler`` for ``event``; returns it so it can be used as a decorator."""
        with self._lock:
            self._handlers[event].append(handler)
        return handler

    def off(self, event: str, handler: Handler) -> None:
        with self._lock:
            if handler in self._handlers.get(event, []):
                self._handlers[event].remove(handler)

    def _emit(self, event: str, *args: Any) -> None:
        for handler in list(self._handlers.get(event, [])):
            self._calls.append((handler, args))

    def _invoke(self, fn: Callable[..., Any], args: Tuple[Any, ...]) -> None:
        """Runs a host callback; its exception is logged and reported, never propagated into the session."""
        try:
            fn(*args)
        except Exception as exc:
            self._log.exception("a Creator Link callback raised")
            with self._lock:
                if fn not in self._handlers.get("error", []):
                    self._report(LinkError("callback-failed", f"{type(exc).__name__}: {exc}"))
            self._wake()

    def _dispatch(self, fn: Callable[..., Any], *args: Any) -> None:
        if self._dispatcher is None:
            self._invoke(fn, args)
            return
        try:
            self._dispatcher(self._invoke, fn, args)
        except Exception:
            self._log.exception("the Creator Link dispatch function raised")

    def _run_calls(self) -> None:
        for _ in range(4):  # a failing callback may queue an error event; deliver that too
            thread = self._thread
            if thread is not None and threading.current_thread() is not thread:
                self._wake()  # callbacks run on the session thread (or wherever dispatch sends them)
                return
            with self._lock:
                calls, self._calls = self._calls, []
            if not calls:
                return
            for fn, args in calls:
                self._dispatch(fn, *args)

    def _set_state(self, state: str) -> None:
        if self.state != state:
            self.state = state
            self._emit("state", state)

    def _report(self, error: LinkError) -> None:
        self.last_error = error
        self._emit("error", error)

    # ---- lifecycle -----------------------------------------------------------------------------------

    def start(self) -> None:
        """Starts connecting (and reconnecting while ``reconnect`` is on). Non-blocking."""
        with self._lock:
            self._want = True
            self._pairing_required_sent = False
            self._not_started_reported = False
            if self.state in (IDLE, STOPPED, WAITING):
                self._attempt = 0
                self._auth_refusals = 0
                self._begin_connect()
        self._run_calls()

    def stop(self) -> None:
        """Says ``bye`` and closes. Pending requests fail with ``disconnected``."""
        with self._lock:
            self._want = False
            ws, self._ws = self._ws, None
            if ws is not None and ws.is_open:
                if self.state == READY:
                    try:
                        ws.send_text(protocol.encode_text({"type": "bye", "id": self._new_id()}))
                    except (WebSocketError, ProtocolError):
                        pass  # closing anyway
                ws.close(1000, "bye")
                ws.poll()  # hand bye and the close frame to the OS now; poll() finishes the handshake
                if ws.state != WebSocketClient.CLOSED:
                    self._closing.append(ws)
            elif ws is not None:
                ws.abort("stopped")
            for probe, _ in self._probes:
                probe.abort()
            self._probes = []
            self._drop_connection("stopped", 1000)
            self._set_state(STOPPED)
        self._run_calls()

    def shutdown(self) -> None:
        """Stops and drops every socket at once (a closing connection is not waited for). For a host that unloads
        the plugin and will not call :meth:`poll` again; :meth:`stop` alone lets ``poll`` finish the close."""
        if self._thread is not None:
            self.stop_thread()
        else:
            self.stop()
        with self._lock:
            closing, self._closing = self._closing, []
        for ws in closing:
            ws.abort("shut down")

    def sign_in(self) -> None:
        """The user wants to sign in (after a ``signed-out`` event, or at any time): connects; a device sign-in
        starts when no session is stored, and a remembered sign-out is cleared then (on the worker thread). DCT is
        asked again to approve the sign-in."""
        with self._lock:
            self._sign_in_requested = True
            self._assisted_flow = None
        self.start()

    def confirm_repair(self, required: Optional[PairingRequired] = None) -> None:
        """The user agreed to pair this plugin again after a ``pairing-required`` event (``required``, by default
        the latest one). The next connection asks that DCT for a pairing code: the one named by the discovery file
        when there is one, otherwise the port of the event (a DCT found by probing, for example a portable one).
        The stored pairing stays until a new one is granted."""
        with self._lock:
            event = required if required is not None else self._last_required
            self._repair_confirmed = True
            self._awaiting_pair_click = False
            self._not_started_reported = False
            self._repair_port = event.port if event is not None and not event.endpoint_trusted and event.port else None
            self._skip_ports.clear()
            self._attempt = 0
        self.start()

    def start_thread(self, name: str = "dct-link") -> threading.Thread:
        """Runs the session on a daemon thread until :meth:`stop_thread`. For hosts that allow threads."""
        with self._lock:
            if self._thread is not None:
                return self._thread
            self._stop_thread.clear()
            self._thread_generation += 1
            thread = threading.Thread(target=self._run_loop, args=(self._thread_generation,), name=name, daemon=True)
            self._thread = thread
        self.start()
        thread.start()
        return thread

    def stop_thread(self, timeout: float = 5.0) -> None:
        self.stop()
        with self._lock:
            self._thread_generation += 1  # an old thread still busy in a callback exits as soon as it returns
        self._stop_thread.set()
        self._wake()
        thread = self._thread
        if thread is not None and thread is not threading.current_thread():
            thread.join(timeout)
        self._thread = None

    def _run_loop(self, generation: int) -> None:
        while not self._stop_thread.is_set() and self._thread_generation == generation:
            self.poll()
            self._wait_io(0.5)
        if self._thread_generation != generation + 1 or self._thread not in (None, threading.current_thread()):
            return  # a newer thread drives the session now
        self.poll()  # deliver the last callbacks and let a graceful close go out
        with self._lock:
            closing, self._closing = self._closing, []
        for ws in closing:
            ws.abort("stopped")

    def _wait_io(self, timeout: float) -> None:
        with self._lock:
            ws = self._ws
            probes = [probe for probe, _ in self._probes]
            waiting = self.state == WAITING
            delay = max(0.0, self._retry_at - self._clock()) if waiting else timeout
            busy = self._has_live_work()
            # Sign-in work polls a socket of its own: come back soon.
            if self._token_task is not None or (self.state == SIGNING_IN and self._sign_in is not None):
                timeout = min(timeout, 0.02)
        if busy:
            timeout = 0.0
        if ws is not None:
            ws.wait(min(timeout, delay))
        elif probes:
            probes[0].wait(min(timeout, 0.02))
        else:
            self._stop_thread.wait(min(timeout, delay))

    def _wake(self) -> None:
        ws = self._ws
        if ws is not None:
            ws._wake()

    # ---- polling -------------------------------------------------------------------------------------

    def poll(self, budget: int = 1 << 20) -> None:
        """Does a bounded amount of work: connection progress, I/O, sign-in steps, live frames, timeouts and
        callbacks. Host code (callbacks, pixel sources, token sources) runs outside the session's lock."""
        with self._lock:
            try:
                self._step_io(budget)
            except Exception as exc:  # keep the driving timer or thread alive
                self._contain(exc)
        self._step_token_work()
        self._step_live_frames()
        self._run_calls()

    def _contain(self, exc: BaseException) -> None:
        """A step failed (under the lock): report it, drop the connection and try again later. A ``LinkError`` is
        an expected failure (for example the socket closed while a message was sent); anything else is a defect."""
        if isinstance(exc, LinkError):
            self._report(exc)
            self._drop_connection(exc.code, 1011)
        else:
            self._log.exception("Creator Link session step failed")
            self._report(LinkError("internal-error", f"{type(exc).__name__}: {exc}"))
            self._drop_connection("internal-error", 1011)
        self._schedule_retry()

    def _step_io(self, budget: int) -> None:
        now = self._clock()
        for closing in list(self._closing):
            closing.poll(budget)
            if closing.state == WebSocketClient.CLOSED:
                self._closing.remove(closing)
        if self.state == WAITING and self._want and now >= self._retry_at:
            self._begin_connect()
        if self._probes:
            self._step_probes(budget)
        ws = self._ws
        if ws is not None:
            for event in ws.poll(budget):
                self._on_ws_event(event)
                if self._ws is not ws:
                    break
        if self._deadline is not None and self._clock() > self._deadline:
            self._on_deadline()
        self._expire_requests(self._clock())
        if self.state == READY:
            self._pump_services()

    # ---- connecting ----------------------------------------------------------------------------------

    def _new_ws(self, port: int) -> WebSocketClient:
        ws = WebSocketClient(self.host, port, protocol.PATH, **self._ws_options)
        ws.start()
        return ws

    def _discovery_candidates(self) -> List[Optional[Union[str, os.PathLike]]]:
        configured = self.discovery_path
        if configured is None:
            return [None]  # the installed DCT's file
        if isinstance(configured, (str, os.PathLike)):
            return [configured]
        return list(configured)

    def _begin_connect(self) -> None:
        self._set_state(CONNECTING)
        self._epoch += 1
        self._discovered = None
        if self.fixed_port is not None:
            self._probes = [(self._new_ws(self.fixed_port), "fixed")]
            return
        discovered = None
        if self.use_discovery_file:
            for candidate in self._discovery_candidates():
                discovered = read_discovery_file(candidate, self.link_ports)
                if discovered is not None:
                    break
        self._discovered = discovered
        if discovered is not None and (self._attempt % 2 == 0 or self._repair_confirmed):
            self._probes = [(self._new_ws(discovered.port), "discovery")]
            return
        if discovered is None and self._repair_confirmed and self._repair_port is not None and self._attempt % 2 == 0:
            # The user agreed to pair again with the DCT that a probe found (no discovery file names one).
            self._probes = [(self._new_ws(self._repair_port), "repair")]
            return
        # Probe the whole range at once: a refused loopback connect can take a second on Windows.
        ports = [p for p in self.link_ports if p not in self._skip_ports]
        if not ports:
            self._skip_ports.clear()
            ports = list(self.link_ports)
        self._probes = [(self._new_ws(port), "probe") for port in ports]

    def _step_probes(self, budget: int) -> None:
        for probe, source in list(self._probes):
            for event in probe.poll(budget):
                if event.kind == "open" and self._ws is None:
                    self._ws = probe
                    self._endpoint_source = source
                    self.endpoint_port = probe.port
                    for other, _ in self._probes:
                        if other is not probe:
                            other.abort()
                    self._probes = []
                    self._start_hello()
                    return
            if probe.state == WebSocketClient.CLOSED:
                self._probes = [entry for entry in self._probes if entry[0] is not probe]
        if not self._probes and self._ws is None:
            self._schedule_retry()

    def _schedule_retry(self, delay: Optional[float] = None, at_least: float = 0.0) -> None:
        if not self._want or not self.reconnect:
            self._set_state(STOPPED)
            return
        if delay is None:
            delay = _BACKOFF[min(self._attempt, len(_BACKOFF) - 1)] * (1.0 + random.random() * 0.25)
            self._attempt += 1
        self._retry_at = self._clock() + max(delay, min(at_least, _MAX_RETRY_AFTER))
        self._set_state(WAITING)

    def _drop_connection(self, reason: str, code: Optional[int]) -> None:
        """Forgets the connection and everything bound to it."""
        ws, self._ws = self._ws, None
        self._epoch += 1
        if ws is not None and ws.state == WebSocketClient.CLOSING:
            ws.poll()  # let the close frame go out; poll() keeps driving it until the handshake ends
            if ws.state != WebSocketClient.CLOSED:
                self._closing.append(ws)
        elif ws is not None and ws.state != WebSocketClient.CLOSED:
            ws.abort(reason)
        if ws is not None and self.state == HELLO and not self._answered and self._endpoint_source == "probe":
            self._skip_ports.add(ws.port)  # it did not speak Creator Link
        for request in list(self._pending.values()):
            self._finish_request(request, error=LinkError("disconnected", reason))
        self._pending.clear()
        self._service_queue.clear()
        self._service_in_flight.clear()
        self._slot_release_at.clear()
        self._push_id = None
        for surface in list(self._surfaces.values()):
            self._close_surface(surface, "disconnected")
        if self._push_waiting is not None:
            self._finish_request(self._push_waiting[2], error=LinkError("disconnected", reason))
            self._push_waiting = None
        saves, self._saves_waiting = self._saves_waiting, []
        for request in saves:
            self._finish_request(request, error=LinkError("disconnected", reason))
        self._close_hint = None
        if self._token_task is not None:
            _, _, task = self._token_task
            self._token_task = None
            try:
                task.cancel()
            except Exception:
                self._log.debug("cancelling a sign-in task failed", exc_info=True)
        self._push_request = None
        self._model_lease = None
        self._deadline = None
        self._handshake_ids = {}
        self._pairing_pending = False
        was_connected = self.state in _HANDSHAKE_STATES + (READY,)
        self.welcome = None
        if was_connected:
            self._emit("disconnected", code, reason)

    def _on_ws_event(self, event: Event) -> None:
        if event.kind == "text":
            self._on_text(event.data or b"")
        elif event.kind == "binary":
            self._on_binary(event.data or b"")
        elif event.kind == "closed":
            code = event.code
            hint, self._close_hint = self._close_hint, None
            if code == protocol.CLOSE_CODES["authenticationFailed"] and self.state == AUTHENTICATING:
                if self._count_refusal():
                    return
            if hint is not None and self.state == READY:
                self._closed_after(hint, event.reason or "closed", code)
                return
            if code == protocol.CLOSE_CODES["incompatible"] and self._others_to_try():
                self._untrusted_endpoint(LinkError("incompatible", "a probed endpoint refused this plugin"))
                return
            # After pairing-not-started DCT closes the idle connection; only the user asks for a code again.
            waiting_for_user = self.state == PAIRING and self._awaiting_pair_click and not self._pairing_pending
            stop = waiting_for_user or code in (protocol.CLOSE_CODES["incompatible"], protocol.CLOSE_CODES["pairingDenied"])
            self._drop_connection(event.reason or "closed", code)
            if code == protocol.CLOSE_CODES["rateLimited"]:
                self._attempt = max(self._attempt, len(_BACKOFF) - 2)
            if stop or self.state == STOPPED:
                self._want = False
                self._set_state(STOPPED)
            else:
                self._schedule_retry()

    def _closed_after(self, hint: str, reason: str, code: Optional[int]) -> None:
        """DCT announced why it is closing a ready connection (then closes with 4003)."""
        trusted = self._endpoint_trusted()
        port = self.endpoint_port or 0
        self._drop_connection(reason, code)
        if hint == "not-paired":
            # The user removed this plugin in DCT, over a connection that proved the pairing. Only the user re-pairs.
            self._emit_pairing_required(PairingRequired("removed", trusted, port))
            self._want = False
            self._set_state(STOPPED)
        elif hint == "account-mismatch":
            self._want = False
            self._set_state(STOPPED)
        else:
            self._dct_is_signed_out()  # the error message was reported when it arrived

    def _dct_is_signed_out(self, error: Optional[LinkError] = None) -> None:
        """DCT is signed out (it answered ``dct-signed-out`` and closes). Not a refusal of this plugin: keep the
        session, tell the host once, and try again now and then; DCT accepts the plugin once it is signed in."""
        if not self._dct_signed_out:
            self._dct_signed_out = True
            self._emit("dct-signed-out")
            if error is not None:
                self._report(error)
        if self._ws is not None:
            self._close_connection(1000, "dct-signed-out")
        self._attempt = max(self._attempt, len(_BACKOFF) - 1)
        self._schedule_retry()

    def _send(self, message: Dict[str, Any]) -> None:
        ws = self._ws
        if ws is None or not ws.is_open:
            raise LinkError("disconnected", "not connected to DCT")
        try:
            data = protocol.encode_text(message)
        except ProtocolError as exc:  # never send what DCT would refuse
            raise LinkError(exc.code, f"refused to send an invalid {message.get('type')} message") from exc
        try:
            ws.send_text(data)
        except WebSocketError as exc:
            raise LinkError("disconnected", str(exc)) from exc

    def _new_id(self) -> str:
        self._next_id += 1
        return f"r{self._next_id}"

    def _close_connection(self, close_code: int, reason: str) -> None:
        ws = self._ws
        if ws is not None:
            ws.close(close_code, reason)
        self._drop_connection(reason, close_code)

    def _fail_handshake(self, error: LinkError, close_code: int = 1008, retry: bool = True,
                        delay: Optional[float] = None) -> None:
        self._report(error)
        self._close_connection(close_code, error.code)
        if retry:
            self._schedule_retry(delay)
        else:
            self._want = False
            self._set_state(STOPPED)

    # ---- handshake -----------------------------------------------------------------------------------

    def _send_handshake(self, kind: str, fields: Dict[str, Any]) -> str:
        message_id = self._new_id()
        self._handshake_ids[message_id] = kind
        self._send(dict(fields, type=kind, id=message_id))
        return message_id

    def _start_hello(self) -> None:
        """The socket is open: read the stored pairing (on a worker), then say hello."""
        self._set_state(HELLO)
        self._answered = False
        self._server_proved = False
        self._handshake_ids = {}
        self._close_hint = None
        self._deadline = None  # the hello deadline starts when the hello is sent
        store = self.pairing_store
        self._token_task = (self._epoch, "pairing-load", self._worker(store.load))

    def _send_hello(self, pairing: Optional[Pairing]) -> None:
        self._client_nonce = secrets.token_bytes(protocol.NONCE_BYTES)
        self._pairing = pairing
        self._hello_paired = self._pairing is not None
        message: Dict[str, Any] = {
            "protocol": {
                "min": protocol.MIN_SUPPORTED_MAJOR,
                "max": protocol.MAX_SUPPORTED_MAJOR,
                "minor": protocol.PROTOCOL_MINOR,
            },
            "plugin": {"kind": self.plugin.kind, "version": self.plugin.version, "channel": self.plugin.channel},
            "host": {"name": self.plugin.host_name, "version": self.plugin.host_version},
            "clientNonce": b64url_encode(self._client_nonce),
        }
        if self._pairing is not None:
            message["clientId"] = self._pairing.client_id
        self._send_handshake("hello", message)
        self._deadline = self._clock() + self.handshake_timeout

    def _endpoint_trusted(self) -> bool:
        return self._endpoint_source in ("discovery", "fixed")

    def _skip_endpoint(self) -> None:
        if self._endpoint_source in ("probe", "repair") and self.endpoint_port is not None:
            self._skip_ports.add(self.endpoint_port)

    def _others_to_try(self) -> bool:
        """True on a probed endpoint (one that proved nothing) while other ports of the range are still untried."""
        if self._endpoint_source not in ("probe", "repair") or self._server_proved:
            return False
        current = self.endpoint_port
        return any(port not in self._skip_ports and port != current for port in self.link_ports)

    def _untrusted_endpoint(self, error: LinkError) -> None:
        """The endpoint did not prove our pairing or behaved like something else: leave it, try others first."""
        others = self._others_to_try()
        self._skip_endpoint()
        self._fail_handshake(error, 1008, retry=True, delay=0.0 if others else None)

    def _peer_owner(self) -> Optional[int]:
        """Windows: the process id behind this connection (``None`` when it cannot be told)."""
        ws = self._ws
        sock = getattr(ws, "_sock", None) if ws is not None else None
        if sock is None:
            return None
        try:
            ours, theirs = sock.getsockname(), sock.getpeername()
        except OSError:
            return None
        return _tcp_owner_pid(theirs, ours)

    def _pairing_endpoint_problem(self) -> Optional[str]:
        """Why this connection must not ask for a pairing code, or ``None``.

        Loopback ports are shared by every Windows session, so another user's program could listen on a link port
        and relay a first pairing. When DCT announced itself in a discovery file, pair only there, and on Windows
        only when the process behind the connection is that DCT in this session (fail closed). Without a discovery
        file, refuse a peer that is known to run in another session.
        """
        discovered = self._discovered
        if discovered is not None and self._endpoint_source != "discovery":
            return "Durty Cloth Tool announced another endpoint"
        if os.name != "nt":
            return None
        owner = self._peer_owner()
        if discovered is not None:
            if owner is None:
                return "the program behind this endpoint cannot be identified"
            if discovered.pid is not None and owner != discovered.pid:
                return "this endpoint is not the Durty Cloth Tool named by its discovery file"
            if _same_session(owner) is not True:
                return "this endpoint runs in another Windows session"
            return None
        if owner is not None and _same_session(owner) is False:
            return "this endpoint runs in another Windows session"
        return None

    def _on_challenge(self, message: Dict[str, Any]) -> None:
        self._server_nonce = b64url_decode(message["serverNonce"])
        if self._hello_paired:
            assert self._pairing is not None
            if message["paired"]:
                expected = server_proof(self._pairing.secret, self._client_nonce, self._server_nonce)
                if not hmac.compare_digest(expected, b64url_decode(message["proof"])):
                    # Not the DCT this plugin paired with: say nothing more, and never send a token.
                    self._untrusted_endpoint(LinkError("server-proof-invalid", "DCT did not prove the pairing"))
                    return
                self._server_proved = True
                self._begin_auth()
            elif self._repair_confirmed and self._is_repair_target():
                self._begin_pairing()  # the user agreed; the stored pairing stays until a new one is granted
            else:
                self._pairing_required("not-recognized")
        else:
            if message["paired"]:
                self._untrusted_endpoint(LinkError("server-proof-invalid", "unexpected pairing claim"))
                return
            self._begin_pairing()

    def _is_repair_target(self) -> bool:
        """The DCT the user agreed to pair with again: the trusted one, or the probed port of the event."""
        if self._endpoint_trusted():
            return True
        return self._repair_port is not None and self.endpoint_port == self._repair_port

    def _begin_pairing(self) -> None:
        """Asks this DCT for a pairing code when that is safe and wanted."""
        problem = self._pairing_endpoint_problem()
        if problem is not None:
            self._untrusted_endpoint(LinkError("untrusted-endpoint", problem))
            return
        if self._awaiting_pair_click:  # cleared only by retry_pairing() and confirm_repair(), both user actions
            # DCT said nobody clicked "Connect an app": ask again only when the user does (retry_pairing), so this
            # plugin never takes a code meant for another one.
            self._report_not_started()
            self._close_connection(1000, "waiting for the user")
            self._want = False
            self._set_state(STOPPED)
            return
        self._request_pairing()

    def _report_not_started(self) -> None:
        if not self._not_started_reported:
            self._not_started_reported = True
            self._report(LinkError("pairing-not-started", 'click "Connect an app" in DCT, then request a code'))

    def _emit_pairing_required(self, required: PairingRequired) -> None:
        self._last_required = required
        self._emit("pairing-required", required)

    def _pairing_required(self, reason: str) -> None:
        """A DCT does not accept the stored pairing. Never re-pair on our own: tell the host, and either stop (the
        trusted DCT, until the user confirms) or try the other endpoints first."""
        trusted = self._endpoint_trusted()
        port = self.endpoint_port or 0
        if trusted or not self._pairing_required_sent:
            self._pairing_required_sent = True
            self._emit_pairing_required(PairingRequired(reason, trusted, port))
        error = LinkError("not-paired", "DCT does not accept this plugin's pairing")
        if trusted:
            self._fail_handshake(error, 1000, retry=False)
        else:
            self._untrusted_endpoint(error)

    def _request_pairing(self) -> None:
        self._set_state(PAIRING)
        self._pair_attempts = 0
        self._pairing_pending = False
        name = self.plugin.display_name or f"{self.plugin.host_name} on {socket.gethostname()}"
        self._send_handshake("pair.request", {"displayName": _sanitize_text(name)})
        self._deadline = self._clock() + self.handshake_timeout

    def retry_pairing(self) -> None:
        """The user asks for a pairing code (for example after clicking "Connect an app" in DCT). Connects first
        when needed. Does nothing while a code is already waiting to be entered."""
        with self._lock:
            self._not_started_reported = False
            self._awaiting_pair_click = False
            if self.state == PAIRING and self._pairing_pending:
                pass  # a code is waiting; asking again would replace it
            elif self.state == PAIRING and self._ws is not None and self._ws.is_open:
                self._request_pairing()
            elif self.state in (STOPPED, WAITING, IDLE):
                self._want = True
                self._attempt = 0
                self._begin_connect()
        self._run_calls()

    def submit_pairing_code(self, code: str) -> None:
        """Sends the six-digit code the user read in DCT."""
        code = (code or "").strip().replace(" ", "")
        if not protocol.is_pairing_code(code):
            raise ValueError("the pairing code has six digits")
        with self._lock:
            if self.state != PAIRING or not self._pairing_pending:
                raise LinkError("pairing-not-started", "DCT is not waiting for a pairing code")
            self._send_handshake("pair.complete", {"code": code})
        self._run_calls()

    def cancel_pairing(self) -> None:
        with self._lock:
            if self.state == PAIRING:
                self._fail_handshake(LinkError("cancelled", "pairing cancelled"), 1000, retry=False)
        self._run_calls()

    def _on_pair_pending(self, message: Dict[str, Any]) -> None:
        self._pairing_pending = True
        expires = message["expiresInSeconds"]
        self._deadline = self._clock() + expires + 2.0  # bounded by the pairing lifetime
        self._emit("pairing", PairingPrompt(expires, protocol.MAX_PAIRING_ATTEMPTS - self._pair_attempts))

    def _on_pair_granted(self, message: Dict[str, Any]) -> None:
        pairing = Pairing(message["clientId"], b64url_decode(message["secret"]))
        self._pairing = pairing
        self._pairing_pending = False
        self._repair_confirmed = False
        self._repair_port = None
        self._last_required = None
        self._server_proved = False  # this connection has not proved the new secret
        self._deadline = None
        store = self.pairing_store
        # The only place a stored pairing is ever replaced; written on a worker, then sign-in goes on.
        self._token_task = (self._epoch, "pairing-save", self._worker(lambda: store.save(pairing)))

    def _on_pair_denied(self, code: str) -> None:
        if code == "pairing-code-invalid":
            self._pair_attempts += 1
            left = protocol.MAX_PAIRING_ATTEMPTS - self._pair_attempts
            if left > 0:
                self._emit("pairing", PairingPrompt(0, left, code))
                return
        if code == "pairing-not-started":
            # DCT shows a code only after the user clicked "Connect an app". Keep the connection, so a click in DCT
            # and then retry_pairing() pairs at once; DCT closes an idle unauthenticated connection after about a
            # minute, and the session then waits for the user instead of asking again on its own.
            self._pairing_pending = False
            self._awaiting_pair_click = True
            self._deadline = None
            self._report_not_started()
            return
        retry = code not in ("pairing-locked", "request-denied", "pairing-code-invalid")
        self._fail_handshake(LinkError(code, "pairing failed"), protocol.CLOSE_CODES["pairingDenied"], retry=retry)

    def _on_deadline(self) -> None:
        state = self.state
        self._deadline = None
        if state == PAIRING and self._pairing_pending:
            self._pairing_pending = False
            self._report(LinkError("pairing-expired", "the pairing code expired; start pairing in DCT again"))
            return
        if state == HELLO:
            self._skip_endpoint()
        if state in _HANDSHAKE_STATES:
            self._fail_handshake(LinkError("timeout", f"DCT did not answer during {state}"), 1000)

    # ---- sign-in (assertions and device sign-in) -------------------------------------------------------

    def _worker(self, call: Callable[[], Any]) -> Any:
        """Runs a blocking call (token source, pairing store) on a worker thread, or inline without threads."""
        return _ThreadTask(call) if self.token_threads else _CallTask(call)

    def _make_task(self, kind: str) -> Any:
        source = self.token_source
        wrap = _ThreadTask if self.token_threads else _CallTask
        if kind == "mint":
            nonce = b64url_encode(self._server_nonce)
            begin = getattr(source, "begin_mint_assertion", None)
            return begin(nonce) if begin is not None else wrap(lambda: source.mint_assertion(nonce))
        begin = getattr(source, "begin_device_sign_in", None)
        return begin() if begin is not None else wrap(source.start_device_sign_in)

    def _begin_auth(self) -> None:
        assert self._pairing is not None
        self._set_state(AUTHENTICATING)
        self._deadline = None  # the sign-in work has its own network timeouts
        self._token_task = (self._epoch, "mint", self._make_task("mint"))

    def _step_token_work(self) -> None:
        """Advances sign-in work outside the session lock, then feeds the result back."""
        with self._lock:
            entry = self._token_task
            flow = self._sign_in if self.state == SIGNING_IN and entry is None else None
            epoch = self._epoch
        if entry is not None:
            _, kind, task = entry
            try:
                done = task.poll()
            except Exception as exc:  # a custom task that raises: treat it as finished with that error
                done = True
                task = _FailedTask(exc)
            if done:
                with self._lock:
                    if self._token_task is entry:
                        self._token_task = None
                        try:
                            self._on_token_done(kind, task)
                        except Exception as exc:  # for example the socket closed while the result was sent
                            self._contain(exc)
        elif flow is not None:
            error: Optional[BaseException] = None
            try:
                approved = flow.poll()
            except Exception as exc:  # the flow failed for good (expired, denied, account locked ...)
                approved, error = None, exc
            if error is not None or approved:
                with self._lock:
                    if self._sign_in is not flow or self._epoch != epoch or self.state != SIGNING_IN:
                        return
                    self._sign_in = None
                    self._assisted_flow = None
                    try:
                        if error is not None:
                            self._fail_sign_in(error)
                        else:
                            self._set_state(AUTHENTICATING)
                            self._token_task = (self._epoch, "mint", self._make_task("mint"))
                    except Exception as exc:
                        self._contain(exc)
        self._run_calls()

    def _fail_sign_in(self, error: BaseException) -> None:
        """A sign-in step failed: retry later when it may help (honouring the server's Retry-After), else stop."""
        code = str(getattr(error, "code", "") or "authentication-failed")
        retryable = bool(getattr(error, "retryable", False))
        retry_after = getattr(error, "retry_after", None)
        self._report(LinkError(code, str(error)))
        self._close_connection(1000, code)
        if retryable:
            wait = float(retry_after) if isinstance(retry_after, (int, float)) and retry_after > 0 else 0.0
            self._schedule_retry(at_least=wait)
        else:
            self._want = False
            self._set_state(STOPPED)

    def _on_token_done(self, kind: str, task: Any) -> None:
        if kind == "pairing-load":
            try:
                pairing = task.result()
            except Exception as exc:
                self._log.warning("reading the stored pairing failed", exc_info=True)
                self._fail_handshake(LinkError("pairing-store-failed", f"{type(exc).__name__}: {exc}"), 1000, retry=True)
                return
            if self._unsaved_pairing is not None:
                pairing = self._unsaved_pairing  # granted in this session but not stored: still the newest one
            self._send_hello(pairing)
            return
        if kind == "pairing-save":
            try:
                task.result()
                self._unsaved_pairing = None
            except Exception as exc:  # kept in memory for this session; the user pairs again after a restart
                self._log.warning("storing the new pairing failed", exc_info=True)
                self._unsaved_pairing = self._pairing
                self._report(LinkError("pairing-not-saved", f"{type(exc).__name__}: {exc}"))
            self._begin_auth()
            return
        try:
            value = task.result()
        except Exception as exc:  # network trouble, account locked, update required, rate limited ...
            self._fail_sign_in(exc)
            return
        if kind == "signed-out":
            if value:
                # The user signed out: wait for them to sign in instead of starting a device sign-in on our own.
                self._emit("signed-out")
                self._fail_handshake(LinkError("signed-out", "sign in to connect to DCT"), 1000, retry=False)
            else:
                self._sign_in_without_session()
            return
        if kind == "mint":
            if value:
                self._send_auth(value)
                return
            # Nobody is signed in. Whether the user signed out is read from the secret store, on a worker; after
            # sign_in() that check clears the remembered sign-out instead.
            source, requested = self.token_source, self._sign_in_requested
            self._sign_in_requested = False
            self._token_task = (self._epoch, "signed-out", self._worker(lambda: _signed_out_check(source, requested)))
        else:
            self._assist(value)

    def _sign_in_without_session(self) -> None:
        if not self._server_proved:
            # A fresh pairing: reconnect so DCT proves the new secret before it is asked to approve a sign-in.
            self._close_connection(1000, "checking the new pairing")
            self._schedule_retry(0.0)
            return
        flow = self._sign_in
        if flow is not None and getattr(flow, "expires_at", None) is not None and not getattr(flow, "cancelled", False):
            self._assist(flow)  # a sign-in started on an earlier connection is still running
            return
        self._token_task = (self._epoch, "device", self._make_task("device"))

    def _assist(self, flow: Any) -> None:
        if not self._server_proved:  # never ask an endpoint that did not prove the pairing
            self._close_connection(1000, "checking the pairing")
            self._schedule_retry(0.0)
            return
        self._sign_in = flow
        self._set_state(SIGNING_IN)
        if self._assisted_flow is not flow:
            # DCT is asked once per device sign-in (until the user asks again with sign_in()): a user who declined
            # in DCT is not asked again on every reconnect.
            self._assisted_flow = flow
            self._send_handshake("account.assist", {"proof": self._proof(), "userCode": flow.user_code})
        self._emit(
            "sign-in",
            SignInPrompt(flow.user_code, flow.verification_uri, getattr(flow, "verification_uri_complete", None)),
        )

    def _proof(self) -> str:
        assert self._pairing is not None
        return b64url_encode(client_proof(self._pairing.secret, self._server_nonce, self._client_nonce))

    def _send_auth(self, assertion: str) -> None:
        claims = _assertion_claims(assertion)
        if claims.get("aud") != ASSERTION_AUDIENCE or claims.get("nonce") != b64url_encode(self._server_nonce):
            self._fail_handshake(LinkError("assertion-invalid", "the assertion is not for this connection"), 1000,
                                 retry=not self._count_refusal(close=False))
            return
        self._set_state(AUTHENTICATING)
        self._send_handshake("auth", {"proof": self._proof(), "assertion": assertion})
        self._deadline = self._clock() + self.handshake_timeout

    def _count_refusal(self, close: bool = True) -> bool:
        """Counts one refused sign-in for this connection. True when the session stopped (too many in a row)."""
        if self._refusal_epoch == self._epoch:
            return False
        self._refusal_epoch = self._epoch
        self._auth_refusals += 1
        if self._auth_refusals < self.max_auth_refusals:
            return False
        if close:
            self._fail_handshake(LinkError("token-invalid", "DCT refused the sign-in repeatedly; sign in again"), 1000,
                                 retry=False)
        return True

    def _on_welcome(self, message: Dict[str, Any]) -> None:
        self._deadline = None
        self._auth_refusals = 0
        self._dct_signed_out = False
        self._sign_in_requested = False
        self._awaiting_pair_click = False
        if self.endpoint_port is not None:
            self._skip_ports.discard(self.endpoint_port)
        self.welcome = message
        self.features = {f["id"]: f["state"] for f in message["features"]}
        self.account_name = message["account"]["userName"]
        self._attempt = 0
        self._set_state(READY)
        self._emit("ready", message)

    def _on_handshake_error(self, answered: Optional[str], message: Dict[str, Any]) -> None:
        code = message["code"]
        error = LinkError(code, message.get("message") or "")
        if answered in ("pair.request", "pair.complete"):
            self._on_pair_denied(code)
            return
        if answered == "account.assist":
            # DCT could not prompt now (busy, rate-limited, another prompt open). The device sign-in goes on; the
            # user can approve it in the browser.
            flow = self._sign_in
            if flow is not None and self.state == SIGNING_IN:
                self._emit("sign-in", SignInPrompt(flow.user_code, flow.verification_uri,
                                                   getattr(flow, "verification_uri_complete", None), False))
            return
        if answered == "auth" and code == "token-invalid":
            # A refused assertion ends this connection; the next one mints a fresh assertion.
            if not self._count_refusal():
                self._fail_handshake(error, 1000, retry=True)
            return
        if code in ("not-paired", "authentication-failed"):
            if self._server_proved:
                self._pairing_required("refused")  # DCT knows the secret yet refuses: only the user can fix it
            else:
                self._untrusted_endpoint(error)
            return
        if code == "dct-signed-out":
            self._dct_is_signed_out(error)  # not a refusal of this plugin: keep trying now and then
            return
        stop = code in ("account-mismatch", "plugin-too-old", "dct-too-old", "unsupported-protocol")
        if code == "rate-limited":
            self._attempt = max(self._attempt, len(_BACKOFF) - 2)
        self._fail_handshake(error, 1000, retry=not stop)

    # ---- incoming messages ---------------------------------------------------------------------------

    def _on_text(self, data: bytes) -> None:
        try:
            message = protocol.decode_text(data, protocol.TO_CLIENT)
        except ProtocolError as exc:
            if self.state != READY:
                self._untrusted_endpoint(LinkError(exc.code, "DCT sent an unreadable message"))
            else:
                self._report(LinkError(exc.code, "ignored an unreadable message from DCT"))
            return
        kind = message["type"]
        self._answered = True
        if self.state != READY:
            self._on_handshake_message(kind, message)
            return
        re_id = message.get("re")
        if re_id:
            self._release_slot(re_id)
        request = self._pending.get(re_id) if re_id else None
        if kind == "error":
            if request is not None:
                self._pending.pop(re_id, None)
                self._finish_request(request, error=LinkError(message["code"], message.get("message") or ""))
            else:
                if message["code"] in ("dct-signed-out", "account-mismatch", "not-paired"):
                    self._close_hint = message["code"]  # DCT closes with 4003 next
                self._report(LinkError(message["code"], message.get("message") or ""))
            return
        # Every reply carries `re`; a message without one (or with an unknown one) is an event.
        if request is not None and kind in _RESPONSES.get(request.type, ()):
            self._pending.pop(request.id, None)
            self._finish_request(request, result=message)
        elif kind == "live.opened":
            # A lease nobody waits for (its request timed out): give it back so DCT does not keep it.
            try:
                self._send({"type": "live.close", "id": self._new_id(), "lease": message["lease"]})
            except LinkError:
                self._log.debug("could not return an unexpected lease")
            return
        handler = _EVENT_HANDLERS.get(kind)
        if handler is not None:
            handler(self, message)

    def _on_handshake_message(self, kind: str, message: Dict[str, Any]) -> None:
        re_id = message.get("re")
        answered = self._handshake_ids.get(re_id) if re_id else None
        if kind == "incompatible" and (answered == "hello" or re_id is None):
            if self._others_to_try():
                # Proves nothing: another program on a probed port could say this to keep the plugin away.
                self._untrusted_endpoint(LinkError(message["code"], "a probed endpoint refused this plugin"))
                return
            event = dict(message)
            if trusted_update_url(event.get("updateUrl")) is None:
                event.pop("updateUrl", None)
            self._emit("incompatible", event)
            self._fail_handshake(LinkError(message["code"], "versions do not meet"), 1000, retry=False)
            return
        if answered is None:
            if kind == "error" and re_id is None:
                self._on_handshake_error(None, message)  # a connection-level refusal (busy, connection limit)
            else:
                self._log.debug("ignored %s without a matching re during %s", kind, self.state)
            return
        if kind == "error":
            self._on_handshake_error(answered, message)
        elif answered == "hello" and kind == "challenge" and self.state == HELLO:
            self._deadline = None
            self._on_challenge(message)
        elif answered == "pair.request" and kind == "pair.pending" and self.state == PAIRING:
            self._on_pair_pending(message)
        elif answered in ("pair.request", "pair.complete") and kind == "pair.denied" and self.state == PAIRING:
            self._on_pair_denied(message["code"])
        elif answered == "pair.complete" and kind == "pair.granted" and self.state == PAIRING:
            self._on_pair_granted(message)
        elif answered == "account.assist" and kind == "account.assistResult":
            flow = self._sign_in
            if flow is not None and self.state == SIGNING_IN:
                self._emit(
                    "sign-in",
                    SignInPrompt(flow.user_code, flow.verification_uri,
                                 getattr(flow, "verification_uri_complete", None), bool(message["ok"])),
                )
        elif answered == "auth" and kind == "welcome" and self.state == AUTHENTICATING:
            self._on_welcome(message)
        else:
            self._log.debug("ignored %s answering %s during %s", kind, answered, self.state)

    def _on_binary(self, data: bytes) -> None:
        try:
            frame = protocol.decode_binary(data, protocol.TO_CLIENT)
        except ProtocolError as exc:
            self._report(LinkError(exc.code, "ignored an unreadable binary frame from DCT"))
            return
        if self.state != READY:
            self._log.debug("ignored a binary frame before welcome")
            return
        header = frame.header
        kind = header["type"]
        re_id = header.get("re")
        if re_id:
            self._release_slot(re_id)
        request = self._pending.get(re_id) if re_id else None
        if request is not None and kind in _RESPONSES.get(request.type, ()):
            self._pending.pop(request.id, None)
            self._finish_request(request, result=frame)
            return
        if kind == "host.openTexture":
            self._emit("open-texture", frame)

    def _on_live_status(self, message: Dict[str, Any]) -> None:
        surface = self._surfaces.get(message["lease"])
        if surface is not None:
            surface.applied_revision = message["appliedRevision"]
            surface.state = message["state"]
            self._emit("live-status", surface, message)

    def _on_live_closed(self, message: Dict[str, Any]) -> None:
        surface = self._surfaces.get(message["lease"])
        if surface is not None:
            self._close_surface(surface, message["reason"])

    def _close_surface(self, surface: LiveSurface, reason: str) -> None:
        if surface.closed:
            return
        surface.closed = True
        surface.close_reason = reason
        self._surfaces.pop(surface.lease, None)
        with surface._lock:
            # Nothing more is sent for this lease: let go of the host's pixels and its pixel source.
            surface._dirty = []
            surface._pixels = None
            surface._pixel_source = None
        # DCT ended the lease (a reply or an event): a close or discard the plugin asked for has nothing left to wait for.
        for request in [r for r in self._pending.values() if r.type in ("live.close", "live.discard") and r.lease == surface.lease]:
            self._pending.pop(request.id, None)
            self._finish_request(request, result={"type": "live.closed", "lease": surface.lease, "reason": reason})
        self._emit("live-closed", surface, reason)

    def _on_model_applied(self, message: Dict[str, Any]) -> None:
        self._model_lease = message["lease"]
        self._emit("model-applied", message)

    def _on_model_closed(self, message: Dict[str, Any]) -> None:
        if self._model_lease == message["lease"]:
            self._model_lease = None
        self._emit("model-closed", message)

    # ---- requests ------------------------------------------------------------------------------------

    def _finish_request(self, request: Request, result: Any = None, error: Optional[LinkError] = None) -> None:
        for callback in request._finish(result, error):
            self._calls.append((callback, (request,)))

    def _release_slot(self, request_id: str) -> None:
        """DCT answered ``request_id`` (or it never got there): its service slot is free again."""
        self._service_in_flight.discard(request_id)
        self._slot_release_at.pop(request_id, None)
        if request_id == self._push_id:
            self._push_id = None

    def _push_busy(self) -> bool:
        return self._push_id is not None and self._push_id in self._service_in_flight

    def _pump_services(self) -> None:
        """Sends queued service requests and the waiting model push while fewer than two are in flight (a request
        that timed out keeps its slot until DCT answers it), then model saves that waited for a push."""
        while len(self._service_in_flight) < MAX_SERVICE_IN_FLIGHT:
            if self._service_queue:
                request, message = self._service_queue.popleft()
                if request.done:
                    continue  # it timed out while it waited; it never reached DCT
                try:
                    self._send(message)
                    self._service_in_flight.add(request.id)
                except LinkError as exc:
                    self._pending.pop(request.id, None)
                    self._finish_request(request, error=exc)
            elif self._push_waiting is not None and not self._push_busy():
                self._send_waiting_push()
            else:
                break
        if self._saves_waiting and not self._push_busy() and self._push_waiting is None:
            saves, self._saves_waiting = self._saves_waiting, []
            for request in saves:
                self._send_model_save(request)

    def _expire_requests(self, now: float) -> None:
        for request in [r for r in self._pending.values() if r.deadline is not None and now > r.deadline]:
            self._pending.pop(request.id, None)
            if request.id in self._service_in_flight:
                # DCT is still working on it; another request now would be answered busy.
                self._slot_release_at[request.id] = now + _SLOT_HOLD_SECONDS
            self._finish_request(request, error=LinkError("timeout", f"{request.type} got no answer"))
            if request.type in ("live.close", "live.discard") and request.lease is not None:
                surface = self._surfaces.get(request.lease)
                if surface is not None:
                    self._close_surface(surface, "timeout")  # ended here: nothing more is sent for it
        for request_id, release_at in list(self._slot_release_at.items()):
            if now >= release_at:
                self._release_slot(request_id)
        for request in [r for r in self._saves_waiting if r.deadline is not None and now > r.deadline]:
            self._saves_waiting.remove(request)
            self._finish_request(request, error=LinkError("timeout", "model.save waited too long for the model push"))

    def request(
        self,
        message_type: str,
        fields: Optional[Dict[str, Any]] = None,
        *,
        timeout: Optional[float] = None,
        transform: Optional[Callable[[Any], Any]] = None,
    ) -> Request:
        """Sends a text request and returns its :class:`Request`. Needs a ready session."""
        with self._lock:
            request = self._register(message_type, timeout)
            request.transform = transform
            message = dict(fields or {}, type=message_type, id=request.id)
            if message_type in SERVICE_TYPES:
                try:
                    protocol.encode_text(message)  # refuse an invalid request now, not when its turn comes
                except ProtocolError as exc:
                    self._pending.pop(request.id, None)
                    self._finish_request(request, error=LinkError(exc.code, str(exc)))
                else:
                    self._service_queue.append((request, message))
                    self._pump_services()
            else:
                try:
                    self._send(message)
                except (LinkError, ProtocolError) as exc:
                    self._pending.pop(request.id, None)
                    error = exc if isinstance(exc, LinkError) else LinkError(exc.code, str(exc))
                    self._finish_request(request, error=error)
        self._run_calls()
        return request

    def _register(self, message_type: str, timeout: Optional[float]) -> Request:
        if self.state != READY:
            raise LinkError("not-authenticated", "the link is not ready")
        request = Request(self, self._new_id(), message_type, self.request_timeout if timeout is None else timeout)
        self._pending[request.id] = request
        return request

    def context(self, timeout: Optional[float] = None) -> Request:
        """``context.get``: the open project and the focused item (resolves with ``context.snapshot``)."""
        return self.request("context.get", timeout=timeout)

    def read_texture(self, target: str = "diffuse", binding: Optional[Dict[str, str]] = None, timeout: Optional[float] = 60.0) -> Request:
        """``texture.read``: resolves with a :class:`protocol.BinaryMessage` (``texture.data``, RGBA8 pixels)."""
        return self.request("texture.read", {"target": target, "binding": binding}, timeout=timeout)

    def validate_texture(
        self, target: str, width: int, height: int, binding: Optional[Dict[str, str]] = None, timeout: Optional[float] = None
    ) -> Request:
        """``texture.validate``: resolves with ``texture.findings``."""
        return self.request(
            "texture.validate", {"target": target, "width": width, "height": height, "binding": binding}, timeout=timeout
        )

    def uv_layout(self, size: int = 2048, binding: Optional[Dict[str, str]] = None, timeout: Optional[float] = 60.0) -> Request:
        """``uv.layout``: resolves with a :class:`protocol.BinaryMessage` (``uv.layout.image``)."""
        return self.request("uv.layout", {"size": size, "binding": binding}, timeout=timeout)

    def model_glb(self, binding: Optional[Dict[str, str]] = None, timeout: Optional[float] = 120.0) -> Request:
        """``model.glb``: resolves with a :class:`protocol.BinaryMessage` (``model.glb.data``)."""
        return self.request("model.glb", {"binding": binding}, timeout=timeout)

    def body_glb(self, gender: str, timeout: Optional[float] = 120.0) -> Request:
        """``body.glb``: resolves with a :class:`protocol.BinaryMessage` (``body.glb.data``)."""
        return self.request("body.glb", {"gender": gender}, timeout=timeout)

    # ---- live textures -------------------------------------------------------------------------------

    def open_live(
        self,
        target: str,
        width: int,
        height: int,
        *,
        binding: Optional[Dict[str, str]] = None,
        document: Optional[str] = None,
        pixel_source: Optional[Callable[[int, int, int, int], Union[bytes, bytearray, memoryview]]] = None,
        timeout: Optional[float] = None,
    ) -> Request:
        """``live.open``: resolves with a :class:`LiveSurface`. ``pixel_source(x, y, w, h)`` returns RGBA8 rows; it
        runs on the thread that drives the session (see the module documentation)."""
        fields: Dict[str, Any] = {"target": target, "width": width, "height": height, "binding": binding}
        if document:
            fields["document"] = _sanitize_text(document)

        def make_surface(message: Dict[str, Any]) -> LiveSurface:
            surface = LiveSurface(self, message, pixel_source)
            self._surfaces[surface.lease] = surface
            return surface

        return self.request("live.open", fields, timeout=timeout, transform=make_surface)

    def _has_live_work(self) -> bool:
        now = self._clock()
        return any(s._dirty and not s._in_flight and s._retry_at <= now and not s.ending for s in self._surfaces.values())

    def _step_live_frames(self) -> None:
        with self._lock:
            ws = self._ws
            if self.state != READY or ws is None or not ws.is_open:
                return
            now = self._clock()
            candidates = [
                s for s in self._surfaces.values() if s._dirty and not s._in_flight and not s.ending and s._retry_at <= now
            ]
            epoch = self._epoch
        for surface in candidates:
            if not surface._producing.acquire(blocking=False):
                continue  # a save on another thread is sending this surface's pixels right now
            try:
                self._produce_frames(surface, epoch)
            except Exception as exc:
                with self._lock:
                    self._contain(exc)
            finally:
                surface._producing.release()

    def _produce_frames(self, surface: LiveSurface, epoch: int) -> Optional[LinkError]:
        """Reads the dirty pixels (outside the session lock) and queues one frame per dirty rectangle. The caller
        holds ``surface._producing`` from here until the frames are queued."""
        rects = surface._take_dirty()
        if not rects:
            return None
        try:
            payloads = [(rect, surface._pixels_for(rect)) for rect in rects]
        except Exception as exc:
            surface._restore_dirty(rects)
            surface.last_error = exc
            surface._retry_at = self._clock() + 1.0
            self._log.warning("a pixel source failed for live surface %s", surface.lease, exc_info=True)
            error = LinkError("pixel-source-failed", f"{type(exc).__name__}: {exc}")
            with self._lock:
                self._emit("live-error", surface, error)
                self._report(error)
            return error
        with self._lock:
            ws = self._ws
            if surface.ending:
                return LinkError("closed", "the live surface is closing")  # its pixels are no longer wanted
            if epoch != self._epoch or ws is None or not ws.is_open:
                return LinkError("disconnected", "the connection changed while pixels were read")
            count = len(payloads)

            def sent() -> None:
                surface._in_flight = False
                surface.frames_sent += count

            for index, ((x, y, w, h), payload) in enumerate(payloads):
                surface.revision += 1
                header = {
                    "type": "live.frame",
                    "lease": surface.lease,
                    "revision": surface.revision,
                    "rect": {"x": x, "y": y, "w": w, "h": h},
                    "format": protocol.FORMAT_RGBA8,
                }
                prefix, view = protocol.encode_binary_parts(header, payload)
                ws.send_binary(prefix, view, on_sent=sent if index == count - 1 else None)
            surface._in_flight = True
            surface._full_sent = True
            surface.last_error = None
        return None

    def _live_save(self, surface: LiveSurface, mode: str, timeout: Optional[float]) -> Request:
        surface._check_open()
        # Frames and the save travel in order on one connection, so queueing the pending pixels first makes the
        # save cover them. A frame the session thread is reading now is finished first (the producing lock); the
        # rest is read here, on the caller's thread. The save then names the newest revision.
        with surface._producing:
            with self._lock:
                epoch = self._epoch
            problem = self._produce_frames(surface, epoch) if surface._dirty else None
            with self._lock:
                request = self._register("live.save", timeout)
                request.lease = surface.lease
                if problem is not None:
                    self._pending.pop(request.id, None)
                    self._finish_request(request, error=problem)
                else:
                    try:
                        self._send({"type": "live.save", "id": request.id, "lease": surface.lease,
                                    "revision": surface.revision, "mode": mode})
                    except LinkError as exc:
                        self._pending.pop(request.id, None)
                        self._finish_request(request, error=exc)
        self._run_calls()
        return request

    def _live_end(self, surface: LiveSurface, message_type: str, timeout: Optional[float]) -> Request:
        """Sends ``live.close`` or ``live.discard`` once per lease; later calls wait for the same ``live.closed``."""
        with self._lock:
            if surface.closed:
                raise LinkError("closed", "the live surface is closed")
            request = self._register(message_type, timeout)
            request.lease = surface.lease
            if surface._ending is None:
                with surface._lock:
                    surface._ending = message_type
                    surface._dirty = []  # nothing more is sent for this lease
                try:
                    self._send({"type": message_type, "id": request.id, "lease": surface.lease})
                except LinkError as exc:
                    self._pending.pop(request.id, None)
                    self._finish_request(request, error=exc)
        self._run_calls()
        return request

    # ---- models (Blender) ----------------------------------------------------------------------------

    def push_model(
        self, bundle: ModelBundle, binding: Optional[Dict[str, str]] = None, timeout: Optional[float] = 120.0
    ) -> Request:
        """``model.push``: resolves with ``model.applied``. The first push of a session may name a
        ``binding``; later pushes reuse the lease DCT returned. One push is in flight at a time (until DCT
        answers it); a newer push waits, and a newer one still replaces the waiting one (which then fails with
        ``superseded``), so DCT always gets the latest model and never a backlog. A waiting push does not time out
        before it is sent; its ``timeout`` counts from then."""
        with self._lock:
            request = self._register("model.push", timeout)
            del self._pending[request.id]  # registered when it is actually sent
            if self._push_waiting is not None:
                self._finish_request(self._push_waiting[2], error=LinkError("superseded", "a newer model replaced it"))
            self._push_waiting = (bundle, binding, request)
            self._pump_services()
        self._run_calls()
        return request

    def _send_waiting_push(self) -> None:
        """Sends the waiting push; :meth:`_pump_services` calls it when a service slot is free."""
        if self._push_busy() or self._push_waiting is None:
            return
        bundle, binding, request = self._push_waiting
        self._push_waiting = None
        header: Dict[str, Any] = {"type": "model.push", "id": request.id, "format": bundle.format, "files": bundle.entries()}
        if self._model_lease is not None:
            header["lease"] = self._model_lease
        elif binding is not None:
            header["binding"] = binding
        ws = self._ws
        try:
            # The files are written one after another; they are never joined in memory.
            prefix = protocol.encode_binary_header(header, bundle.size)
            if ws is None or not ws.is_open:
                raise LinkError("disconnected", "not connected to DCT")
            if request.deadline is not None and request.timeout is not None:
                request.deadline = self._clock() + request.timeout  # counted from now: it waited for its turn
            self._pending[request.id] = request
            self._push_request = request
            self._push_id = request.id
            self._service_in_flight.add(request.id)
            ws.send_binary(prefix, *(data for _, data in bundle.files))
        except (LinkError, ProtocolError, WebSocketError) as exc:
            self._release_slot(request.id)
            self._pending.pop(request.id, None)
            if isinstance(exc, LinkError):
                error = exc
            elif isinstance(exc, ProtocolError):
                error = LinkError(exc.code, str(exc))
            else:
                error = LinkError("disconnected", str(exc))
            self._finish_request(request, error=error)

    def save_model(self, timeout: Optional[float] = 120.0) -> Request:
        """``model.save``: resolves with ``model.saveResult``. While a push is still on its way or converting
        (DCT would answer ``busy``), the save waits for it and then saves what DCT shows."""
        with self._lock:
            if self._model_lease is None and not self._push_busy() and self._push_waiting is None:
                raise LinkError("lease-not-found", "push a model first")
            request = self._register("model.save", timeout)
            if self._push_busy() or self._push_waiting is not None:
                del self._pending[request.id]  # registered when it is sent
                self._saves_waiting.append(request)
            else:
                self._send_model_save(request)
        self._run_calls()
        return request

    def _send_model_save(self, request: Request) -> None:
        lease = self._model_lease
        self._pending.pop(request.id, None)
        if lease is None:
            self._finish_request(request, error=LinkError("lease-not-found", "the model push did not create a lease"))
            return
        try:
            self._send({"type": "model.save", "id": request.id, "lease": lease})
        except LinkError as exc:
            self._finish_request(request, error=exc)
            return
        self._pending[request.id] = request

    def discard_model(self, timeout: Optional[float] = 30.0) -> Request:
        """``model.discard``: resolves with ``model.closed``."""
        with self._lock:
            lease = self._model_lease
        if lease is None:
            raise LinkError("lease-not-found", "push a model first")
        return self.request("model.discard", {"lease": lease}, timeout=timeout)


def _signed_out_check(source: Any, requested: bool) -> bool:
    """On a worker: after sign_in() clear a remembered sign-out; otherwise say whether the user signed out."""
    if requested:
        allow = getattr(source, "allow_sign_in", None)
        if allow is not None:
            allow()
        return False
    return bool(getattr(source, "signed_out_by_user", False))


class _FailedTask:
    def __init__(self, error: BaseException) -> None:
        self._error = error

    def result(self) -> Any:
        raise self._error

    def cancel(self) -> None:
        pass


_EVENT_HANDLERS: Dict[str, Callable[[LinkSession, Dict[str, Any]], None]] = {
    "event.selection": lambda s, m: s._emit("selection", m),
    "event.project": lambda s, m: s._emit("project", m),
    "event.entitlement": lambda s, m: (
        s.features.update({f["id"]: f["state"] for f in m["features"]}),
        s._emit("entitlement", m),
    ),
    "live.status": LinkSession._on_live_status,
    "live.closed": LinkSession._on_live_closed,
    "model.applied": LinkSession._on_model_applied,
    "model.closed": LinkSession._on_model_closed,
}
