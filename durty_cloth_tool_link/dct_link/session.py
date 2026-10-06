# SPDX-License-Identifier: MIT
# Copyright (c) Schmid Software Solutions (https://schmid-software.de)
"""The Creator Link session: finding DCT, the hello/challenge/auth flow (with a device sign-in that DCT can
approve), requests, events, live texture streaming and model pushes.

A :class:`LinkSession` is driven in one of two ways (the same object supports both):

* **Polling** (Blender): call :meth:`LinkSession.poll` from ``bpy.app.timers`` every 20 to 50 ms. Every call
  does bounded work and returns quickly; callbacks run inside it, on the calling thread. Sign-in work
  (assertions, refresh, device sign-in) runs on a short-lived worker thread that only talks to gta.clothing and
  the secret store and never touches host APIs; ``poll`` picks up its result.
* **Background thread** (hosts that allow threads): call :meth:`LinkSession.start_thread`. Callbacks then run on
  that thread unless a ``dispatch`` function moves them (for example onto the Qt or GLib main loop). Every
  public method is safe to call from any thread.

Threading contract for hosts: callbacks and ``pixel_source`` functions run on the thread that drives the
session (:meth:`LiveSurface.save` reads pending pixels on the calling thread). Token source calls (and with them
every secret-store access) run on a short-lived worker thread, never on the thread that drives the session
(``token_threads=False`` runs them inline instead, for hosts without threads). A host whose own API may only be
used on its UI thread reads its pixels on that thread and hands them over with :meth:`LiveSurface.update` or from
a snapshot, or passes a ``dispatch`` function for callbacks; it never calls its host API from the session thread.
A ``pixel_source`` must never wait for a thread that may call :meth:`LiveSurface.save`, because a save waits for a
pixel read that is in progress. An exception raised by a callback or a ``pixel_source`` is logged and reported
through the ``error`` event; it never stops the session.

Host calls are never made while the session holds its internal lock, so a callback may call back into the
session.
"""

from __future__ import annotations

import base64
import collections
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
from typing import Any, Callable, Dict, Iterable, List, Mapping, NamedTuple, Optional, Sequence, Set, Tuple, Union

from . import ped as ped_module
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
    "HostRequest",
    "HostOpenTexture",
    "HostOpenModel",
    "Thumbnail",
    "ThumbnailRefusal",
    "ModelFile",
    "SkeletonTemplate",
    "SkeletonTemplateRefusal",
    "ItemAddRequest",
    "ItemAddResult",
    "SignInPrompt",
    "DiscoveredEndpoint",
    "ASSERTION_AUDIENCE",
    "discovery_file_path",
    "installed_user_data_dir",
    "read_discovery_file",
    "trusted_update_url",
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
    ``disconnected``, ``timeout``, ``superseded``, ``cancelled``, ``closed``, ``assertion-invalid``,
    ``untrusted-endpoint``, ``signed-out``, ``pixel-source-failed``, ``callback-failed`` and
    ``internal-error``."""

    def __init__(self, code: str, message: str = "") -> None:
        super().__init__(f"{code}: {message}" if message else code)
        self.code = code
        self.message = message


class PluginInfo(NamedTuple):
    """Who is connecting. ``kind`` is one of :data:`protocol.PLUGIN_KINDS`; ``install_id`` is this installation's
    random id (:func:`dct_link.tokens.load_install_id`, the same one :class:`dct_link.auth.ClientInfo` carries)."""

    kind: str
    version: str
    channel: str
    host_name: str
    host_version: str
    install_id: str

    def check(self) -> None:
        if self.kind not in protocol.PLUGIN_KINDS:
            raise ValueError("unknown plugin kind")
        if not protocol.is_semver(self.version):
            raise ValueError("plugin version must be semantic (major.minor.patch)")
        if self.channel not in protocol.CHANNELS:
            raise ValueError("unknown channel")
        if not protocol.is_text(self.host_name) or not protocol.is_host_version(self.host_version):
            raise ValueError("invalid host name or version")
        if not protocol.is_install_id(self.install_id):
            raise ValueError("the install id is a random GUID (tokens.load_install_id)")


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

    Expected content: ``{"port": 47820, "pid": 1234, "path": "/dct/link/v1", "protocolMin": 2, "protocolMax": 2}``.
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


def _wts_session_ids() -> Optional[Dict[int, int]]:
    """Windows only: the Windows session of every process (process id to session id), or ``None``.

    ``WTSEnumerateProcessesW`` lists the session of every process without opening it, so it also answers for a
    process of another user (``ProcessIdToSessionId`` fails with access denied there).
    """
    if os.name != "nt":
        return None
    try:
        import ctypes
        from ctypes import wintypes

        class _ProcessInfo(ctypes.Structure):
            _fields_ = [("SessionId", wintypes.DWORD), ("ProcessId", wintypes.DWORD),
                        ("pProcessName", wintypes.LPWSTR), ("pUserSid", ctypes.c_void_p)]

        wtsapi = ctypes.WinDLL("wtsapi32")
        enumerate_processes = wtsapi.WTSEnumerateProcessesW
        enumerate_processes.restype = wintypes.BOOL
        enumerate_processes.argtypes = (wintypes.HANDLE, wintypes.DWORD, wintypes.DWORD,
                                        ctypes.POINTER(ctypes.POINTER(_ProcessInfo)), ctypes.POINTER(wintypes.DWORD))
        free_memory = wtsapi.WTSFreeMemory
        free_memory.restype = None
        free_memory.argtypes = (ctypes.c_void_p,)
        table = ctypes.POINTER(_ProcessInfo)()
        count = wintypes.DWORD()
        if not enumerate_processes(None, 0, 1, ctypes.byref(table), ctypes.byref(count)):  # this server
            return None
        try:
            return {int(table[i].ProcessId): int(table[i].SessionId) for i in range(count.value)}
        finally:
            free_memory(table)
    except (OSError, AttributeError, ValueError, TypeError):
        return None


def _session_id(pid: int) -> Optional[int]:
    """Windows only: the Windows session ``pid`` runs in, or ``None``."""
    sessions = _wts_session_ids()
    return None if sessions is None else sessions.get(pid)


def _same_session(pid: int) -> Optional[bool]:
    """Whether ``pid`` runs in this process's Windows session (``None`` when that cannot be told)."""
    if pid == os.getpid():
        return True
    sessions = _wts_session_ids()
    if sessions is None:
        return None
    theirs, ours = sessions.get(pid), sessions.get(os.getpid())
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
        #: The session's own next steps once the request finished (:meth:`LinkSession._then`), never dispatched.
        self._continuations: List[Callable[["Request"], Any]] = []
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


#: At most ``MAX_SERVICE_IN_FLIGHT`` of these requests (model pushes included) are in flight per connection;
#: the session queues the rest.
SERVICE_TYPES = frozenset(
    {"texture.read", "texture.validate", "uv.layout", "model.glb", "body.glb", "model.push", "item.thumbnail",
     "skeleton.template", "ped.templates", "ped.skeleton"}
)
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
    "item.thumbnail": ("item.thumbnail.data",),
    "skeleton.template": ("skeleton.template.data",),
    "item.add": ("item.addResult",),
    "ped.templates": ("ped.templates.list",),
    "ped.skeleton": ("ped.skeleton.data",),
    "ped.rig": ("ped.rig.result",),
    "ped.add": ("ped.addResult",),
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
# Requests from DCT and thumbnails
# --------------------------------------------------------------------------------------------------

class HostRequest:
    """Something DCT asked this plugin to open (``host.openTexture`` or ``host.openModel``) and the way to answer it.

    Call :meth:`accept` as soon as the plugin has taken the item and started opening it (not after a long import),
    or :meth:`refuse` with a code from :data:`protocol.HOST_RESULT_CODES` as soon as it knows it cannot. DCT waits
    :data:`protocol.OPEN_TEXTURE_ANSWER_SECONDS` (20) for a texture and :data:`protocol.OPEN_MODEL_ANSWER_SECONDS`
    (60) for a model, then tells the user the app did not answer; a failure after :meth:`accept` is the plugin's to
    show. Only the first call counts, and either may be called from any thread, also after the handler returned.

    The session answers by itself in two cases: with no handler for the event it refuses with ``not-supported`` at
    once, and when a handler raises before anything answered it refuses with ``open-failed``. A handler that
    returns without answering is left alone; it must answer later.

    ``header`` and ``payload`` are the frame as received (``payload`` is a view of it). ``request_id`` is DCT's
    message id, which ``host.result`` names.
    """

    def __init__(self, session: "LinkSession", header: Dict[str, Any], payload: memoryview, epoch: int) -> None:
        self.header = header
        self.payload = payload
        self.binding: Dict[str, str] = dict(header["binding"])
        self.name: str = header["name"]
        self.request_id: str = header["id"]
        self._session = session
        self._epoch = epoch
        self._lock = threading.Lock()
        self._answered = False

    @property
    def answered(self) -> bool:
        """``accept`` or ``refuse`` was called (by the host, or by the session in the cases above)."""
        return self._answered

    def accept(self) -> bool:
        """The document opened. True when a ``host.result`` was sent."""
        return self._answer(None)

    def refuse(self, code: str) -> bool:
        """The document did not open; ``code`` is one of :data:`protocol.HOST_RESULT_CODES` (``ValueError``
        otherwise). True when a ``host.result`` was sent."""
        if code not in protocol.HOST_RESULT_CODES:
            raise ValueError(f"{code!r} is not a host.result code")
        return self._answer(code)

    def _answer(self, code: Optional[str]) -> bool:
        with self._lock:
            if self._answered:
                return False
            self._answered = True
        return self._session._answer_host_request(self._epoch, self.request_id, code)

    def _handler_failed(self) -> None:
        if not self._answered:
            self._answer("open-failed")


class HostOpenTexture(HostRequest):
    """``host.openTexture``: a texture to open as a new document bound to its cloth. ``pixels`` (the same view as
    ``payload``) is RGBA8, ``width * height * 4`` bytes, rows top to bottom; ``target`` is the map DCT chose."""

    def __init__(self, session: "LinkSession", header: Dict[str, Any], payload: memoryview, epoch: int) -> None:
        super().__init__(session, header, payload, epoch)
        self.target: str = header["target"]
        self.width: int = header["width"]
        self.height: int = header["height"]
        self.pixels = payload


class HostOpenModel(HostRequest):
    """``host.openModel``: a cloth's model to open. ``files`` lists ``(name, data)`` in DCT's
    order: one ``*.ydd.xml`` and its ``*.dds`` textures, among them the variation's diffuse; each ``data`` is a view
    of the payload. ``format`` is ``ydd-xml``."""

    def __init__(self, session: "LinkSession", header: Dict[str, Any], payload: memoryview, epoch: int) -> None:
        super().__init__(session, header, payload, epoch)
        self.format: str = header["format"]
        self.files: List[Tuple[str, memoryview]] = []
        offset = 0
        for entry in header["files"]:  # the codec checked the names and that the lengths add up
            self.files.append((entry["name"], payload[offset : offset + entry["length"]]))
            offset += entry["length"]


class Thumbnail(NamedTuple):
    """A small picture of a cloth (``item.thumbnail.data``). ``binding`` is the cloth and variation
    DCT pictured (the focused one when the request named none); ``pixels`` is RGBA8, ``width * height * 4`` bytes,
    rows top to bottom."""

    binding: Dict[str, str]
    width: int
    height: int
    pixels: bytes
    ok: bool = True


class ThumbnailRefusal(NamedTuple):
    """Why :meth:`LinkSession.request_thumbnail` got no picture: DCT's error code (for example ``item-refused``,
    ``needs-ultimate``, ``no-focused-item``)."""

    code: str
    ok: bool = False


def _thumbnail_answer(size: int, binding: Optional[Dict[str, str]]) -> Callable[[Any], Union[Thumbnail, ThumbnailRefusal]]:
    """Turns DCT's answer to one ``item.thumbnail`` into its result. A picture larger than ``size`` or of another
    cloth than ``binding`` does not answer the request: ``protocol-violation``."""

    def result(answer: Any) -> Union[Thumbnail, ThumbnailRefusal]:
        if isinstance(answer, ThumbnailRefusal):
            return answer
        header = answer.header
        if max(header["width"], header["height"]) > size or (
            binding is not None and not _same_binding(header["binding"], binding)
        ):
            raise LinkError("protocol-violation", "DCT answered item.thumbnail with a picture it was not asked for")
        return Thumbnail(dict(header["binding"]), header["width"], header["height"], bytes(answer.payload))

    return result


def _same_binding(a: Dict[str, str], b: Dict[str, str]) -> bool:
    """The same cloth and variation (GUIDs compare without regard to case)."""
    return a["clothId"].lower() == b["clothId"].lower() and a["textureId"].lower() == b["textureId"].lower()


def _is_binding(value: Any) -> bool:
    return isinstance(value, dict) and protocol.is_guid(value.get("clothId")) and protocol.is_guid(value.get("textureId"))


# --------------------------------------------------------------------------------------------------
# Adding an item (Blender): the skeleton template and item.add
# --------------------------------------------------------------------------------------------------


class ModelFile(NamedTuple):
    """One file of a model DCT sent: a bare file name and its bytes."""

    name: str
    data: bytes


class SkeletonTemplate(NamedTuple):
    """The freemode skeleton of one gender (``skeleton.template.data``). ``files`` holds one ``*.ydd.xml`` whose only
    drawable is the skeleton (its bones in the game's order) with an empty shader group, nothing else; Sollumz
    imports it as an armature."""

    gender: str
    files: List[ModelFile]
    ok: bool = True


class SkeletonTemplateRefusal(NamedTuple):
    """Why :meth:`LinkSession.request_skeleton_template` got no skeleton: DCT's error code (for example
    ``game-required`` when DCT has no game files, ``busy`` while it still reads them)."""

    code: str
    ok: bool = False


def _skeleton_answer(gender: str) -> Callable[[Any], Union[SkeletonTemplate, SkeletonTemplateRefusal]]:
    """Turns DCT's answer to one ``skeleton.template`` into its result. A skeleton of the other gender does not answer
    the request: ``protocol-violation``."""

    def result(answer: Any) -> Union[SkeletonTemplate, SkeletonTemplateRefusal]:
        if isinstance(answer, SkeletonTemplateRefusal):
            return answer
        header = answer.header
        if header["gender"] != gender:
            raise LinkError("protocol-violation", "DCT answered skeleton.template with the skeleton of another gender")
        files, offset = [], 0
        for entry in header["files"]:  # the codec checked the names and that the lengths add up
            files.append(ModelFile(entry["name"], bytes(answer.payload[offset : offset + entry["length"]])))
            offset += entry["length"]
        return SkeletonTemplate(header["gender"], files)

    return result


class ItemAddResult(NamedTuple):
    """DCT's answer to :meth:`LinkSession.add_item` (``item.addResult``, or an ``error`` that answered the add).

    ``ok`` true: the cloth was added. ``binding`` names it and its first variation (``clothId``, ``textureId``), and
    this connection may now read it and push and save its model. ``ok`` false: ``code`` says why, for example
    ``request-denied`` (the user chose Cancel, or the add was withdrawn), ``item-limit`` (the project cannot take more
    clothes), ``model-rejected`` (the model or a picture did not convert), ``busy``, ``rate-limited``, ``no-project``,
    ``item-refused`` or ``save-failed``. ``findings`` are DCT's checks of the model and the variations (each a
    ``code`` and a ``severity``), also when the add failed; empty when DCT answered with an error."""

    ok: bool
    code: Optional[str]
    binding: Optional[Dict[str, str]]
    findings: List[Dict[str, str]]


def _item_add_answer(answer: Any) -> ItemAddResult:
    if isinstance(answer, ItemAddResult):
        return answer
    binding = answer.get("binding")
    return ItemAddResult(
        bool(answer["ok"]),
        answer.get("code"),
        None if binding is None else {"clothId": binding["clothId"], "textureId": binding["textureId"]},
        [{"code": finding["code"], "severity": finding["severity"]} for finding in answer["findings"]],
    )


# ---- custom peds ----


class PedTemplates(NamedTuple):
    """Every human ped template DCT lists (the pages of ``ped.templates.list`` joined): each a dict with ``model``,
    ``gender`` (absent when DCT cannot tell it), ``pedType``, ``layout``, ``group`` and ``recommended``, recommended
    entries first, at most :data:`protocol.MAX_PED_TEMPLATES`. ``truncated`` says more matched than DCT lists."""

    templates: List[Dict[str, Any]]
    truncated: bool
    ok: bool = True


class PedRefusal(NamedTuple):
    """Why :meth:`LinkSession.list_ped_templates` or :meth:`LinkSession.request_ped_skeleton` got nothing: DCT's error
    code (``game-required`` without a GTA V Legacy folder, ``template-not-found``, ``busy`` ...)."""

    code: str
    ok: bool = False


class PedRigRefusal(NamedTuple):
    """Why a rig produced nothing: DCT's code (``needs-license``, ``needs-ultimate``, ``busy``, ``game-required``,
    ``template-not-found``, ``mesh-too-large``, ``rig-refused``, ``cancelled`` ...) and, for a refusal, its reasons
    (dicts with ``code`` from :data:`protocol.PED_RIG_REFUSALS`, optional ``markers`` and an English ``message``).
    ``job`` names the rig when DCT had accepted it."""

    code: str
    reasons: List[Dict[str, Any]]
    job: Optional[str] = None
    ok: bool = False


class PedAddResult(NamedTuple):
    """DCT's answer to :meth:`LinkSession.add_ped` (``ped.addResult``, or an ``error`` that answered the add).

    ``ok`` true: DCT created and opened the custom ped project; ``project`` holds its ``name``, ``model`` and
    ``template``. ``ok`` false: ``code`` says why (``request-denied`` when the user chose Cancel or the add was
    withdrawn, ``needs-license``, ``model-rejected``, ``upload-incomplete``, ``busy``, ``rate-limited``,
    ``game-required``, ``template-not-found``, ``save-failed``). ``findings`` are DCT's checks of the character."""

    ok: bool
    code: Optional[str]
    project: Optional[Dict[str, str]]
    findings: List[Dict[str, str]]


#: How often :meth:`LinkSession.list_ped_templates` starts again when the installed peds changed while it read the pages.
_PED_TEMPLATE_RESTARTS = 2


class _PedTemplatePages:
    """Asks DCT for one page of ``ped.templates`` after the other and finishes ``listing`` with every template: a
    :class:`PedTemplates`, DCT's :class:`PedRefusal`, a page's :class:`LinkError`, or ``protocol-violation`` when the
    pages do not join up. When the list's ``total`` changes between pages, or a model comes twice, the installed peds
    changed meanwhile and it starts again (at most :data:`_PED_TEMPLATE_RESTARTS` times). Each page has its own
    timeout; the codec has checked that every page but the last is full."""

    def __init__(self, session: "LinkSession", listing: Request, fields: Dict[str, Any], timeout: Optional[float]) -> None:
        self.session = session
        self.listing = listing
        self.fields = fields
        self.timeout = timeout
        self.restarts = 0
        self.templates: List[Dict[str, Any]] = []
        self.models: set = set()
        self.total: Optional[int] = None

    def ask(self) -> None:
        fields = dict(self.fields)
        if self.templates:
            fields["offset"] = len(self.templates)
        try:
            page = self.session.request("ped.templates", fields, timeout=self.timeout)
        except LinkError as exc:
            # The link was ready when the list started: not ready now means the connection ended between pages.
            self.finish(error=LinkError("disconnected", str(exc)) if exc.code == "not-authenticated" else exc)
            return
        # The session's own path, not dispatch: a host that waits for the list on the thread dispatch runs on would
        # otherwise never see the next page asked for.
        self.session._then(page, self.on_page)

    def on_page(self, page: Request) -> None:
        try:
            self._on_page(page)
        except Exception as exc:  # nothing else would end the list, which has no deadline of its own
            self.session._log.exception("the ped template list failed")
            self.finish(error=LinkError("protocol-violation", f"{type(exc).__name__}: {exc}"))

    def _on_page(self, page: Request) -> None:
        if page.error is not None:
            self.finish(error=page.error)
            return
        answer = page.result()
        if isinstance(answer, PedRefusal):
            self.finish(answer)
            return
        if answer["offset"] != len(self.templates):
            self.finish(error=LinkError("protocol-violation", "DCT answered ped.templates with another page of the list"))
            return
        entries = [dict(entry) for entry in answer["templates"]]
        if (self.total is not None and answer["total"] != self.total) or any(
                entry["model"].lower() in self.models for entry in entries):
            if self.restarts >= _PED_TEMPLATE_RESTARTS:
                self.finish(error=LinkError("protocol-violation",
                                            "the installed ped templates kept changing while DCT listed them"))
                return
            self.restarts += 1
            self.templates, self.models, self.total = [], set(), None
            self.ask()
            return
        self.total = answer["total"]
        self.templates.extend(entries)
        self.models.update(entry["model"].lower() for entry in entries)
        if len(self.templates) < self.total:
            self.ask()
        else:
            self.finish(PedTemplates(self.templates, bool(answer["truncated"])))

    def finish(self, result: Any = None, error: Optional[LinkError] = None) -> None:
        session = self.session
        with session._lock:
            session._finish_request(self.listing, result, error)
        session._run_calls()


def _ped_skeleton_answer(model: str) -> Callable[[Any], Union[ped_module.PedSkeleton, PedRefusal]]:
    def result(answer: Any) -> Union[ped_module.PedSkeleton, PedRefusal]:
        if isinstance(answer, PedRefusal):
            return answer
        if answer.header["model"].lower() != model.lower():
            raise LinkError("protocol-violation", "DCT answered ped.skeleton with the skeleton of another template")
        return ped_module.decode_ped_skeleton(answer)

    return result


def _ped_rig_answer(template: str, vertices: int) -> Callable[[Any], Union[ped_module.PedRig, PedRigRefusal]]:
    def result(answer: Any) -> Union[ped_module.PedRig, PedRigRefusal]:
        if isinstance(answer, PedRigRefusal):
            return answer
        header = answer.header
        if not header["ok"]:
            reasons = [dict(reason) for reason in header.get("reasons") or []]
            return PedRigRefusal(header["code"], reasons, header.get("job"))
        if header["vertices"] != vertices or header["template"].lower() != template.lower():
            raise LinkError("protocol-violation", "DCT answered ped.rig with a rig of another mesh or template")
        return ped_module.decode_ped_rig(answer)

    return result


def _ped_add_answer(answer: Any) -> PedAddResult:
    if isinstance(answer, PedAddResult):
        return answer
    project = answer.get("project")
    return PedAddResult(
        bool(answer["ok"]),
        answer.get("code"),
        None if project is None else {"name": project["name"], "model": project["model"], "template": project["template"]},
        [{"code": finding["code"], "severity": finding["severity"]} for finding in answer["findings"]],
    )


#: Requests whose ``error`` answer is a typed refusal (a result of the request), not a failure of it.
_REFUSALS: Dict[str, Callable[[str], Any]] = {
    "item.thumbnail": ThumbnailRefusal,
    "skeleton.template": SkeletonTemplateRefusal,
    "item.add": lambda code: ItemAddResult(False, code, None, []),
    "ped.templates": PedRefusal,
    "ped.skeleton": PedRefusal,
    "ped.rig": lambda code: PedRigRefusal(code, []),
    "ped.add": lambda code: PedAddResult(False, code, None, []),
}

#: How long a withdrawn request (``item.add``, ``ped.rig``, ``ped.add``) waits for DCT's answer before it fails.
_ADD_CANCEL_GRACE_SECONDS = 10.0


class WithdrawableRequest(Request):
    """A request DCT may work on, or ask its user about, for a long time: ``item.add``, ``ped.rig`` and ``ped.add``.
    It resolves with DCT's answer, whatever it says, and fails with :class:`LinkError` only when DCT gave no answer:
    ``disconnected``, or ``cancelled`` / ``timeout`` when a withdrawn request got no answer in time.

    When it times out, the session first withdraws it (its cancel message) and waits a short grace for DCT's answer,
    exactly as :meth:`cancel` does. When DCT answers a withdrawn ``item.add`` or ``ped.add`` after the grace, on the
    same connection, the session emits ``item-add-late(request, ItemAddResult)`` or ``ped-add-late(request,
    PedAddResult)``: the user may have chosen Add (or created the project) just as the withdrawal arrived, so a host
    keeps listening for that event rather than for the request. A rig has no late event: a late rig changes
    nothing in DCT."""

    #: The message that withdraws this request.
    cancel_type = "item.addCancel"

    def __init__(self, session: "LinkSession", request_id: str, message_type: str, timeout: Optional[float]) -> None:
        super().__init__(session, request_id, message_type, timeout)
        self._withdrawn: Optional[str] = None  # "cancelled" or "timeout" once the cancel was sent

    @property
    def withdrawn(self) -> bool:
        """The cancel was sent for this request (by :meth:`cancel`, or when it timed out)."""
        return self._withdrawn is not None

    def cancel(self) -> bool:
        """Withdraws the request while DCT still works on it or asks its user: sends the cancel once and keeps waiting
        up to 10 seconds for DCT's answer (``request-denied`` for an add, ``cancelled`` for a rig). When DCT finished at
        that moment the answer is the finished result; the result says which. Without an answer in time the request
        fails with ``cancelled``. True when the cancel was sent now; False when the request has finished or was
        withdrawn already. Callable from any thread."""
        session = self.session
        with session._lock:
            sent = session._withdraw(self, "cancelled")
        session._run_calls()
        return sent


class ItemAddRequest(WithdrawableRequest):
    """A pending ``item.add`` (:meth:`LinkSession.add_item`). Resolves with an :class:`ItemAddResult`, whatever DCT
    decided; :meth:`cancel` sends ``item.addCancel``."""

    cancel_type = "item.addCancel"


class PedRigRequest(WithdrawableRequest):
    """A pending ``ped.rig`` (:meth:`LinkSession.rig_ped`). Resolves with a :class:`ped.PedRig` or a
    :class:`PedRigRefusal`; :meth:`cancel` sends ``ped.rig.cancel``. ``job`` is DCT's id for the rig once it
    accepted it (``ped.rig.accepted``)."""

    cancel_type = "ped.rig.cancel"

    def __init__(self, session: "LinkSession", request_id: str, message_type: str, timeout: Optional[float]) -> None:
        super().__init__(session, request_id, message_type, timeout)
        self.job: Optional[str] = None
        self.on_accepted: Optional[Callable[[str], Any]] = None
        self.on_progress: Optional[Callable[[str, float], Any]] = None


class PedAddRequest(WithdrawableRequest):
    """A pending ``ped.add`` (:meth:`LinkSession.add_ped`). Resolves with a :class:`PedAddResult`; :meth:`cancel`
    sends ``ped.addCancel``."""

    cancel_type = "ped.addCancel"


def _pairs(values: Any, what: str, shape: str) -> List[Tuple[Any, Any]]:
    try:
        items = list(values)
    except TypeError:
        raise ValueError(f"{what} is a sequence of {shape} pairs") from None
    for item in items:
        if not isinstance(item, (tuple, list)) or len(item) != 2:
            raise ValueError(f"each of {what} is a {shape} pair (a tuple of two)")
    return [(item[0], item[1]) for item in items]


def _prepare_item(
    drawable_type: Any, gender: Any, skin: Any, name: Any, variations: Any, files: Any
) -> Tuple[Dict[str, Any], List[Tuple[str, memoryview]], int]:
    """Checks an ``item.add`` with the codec's rules before anything is sent. Returns its header (without an id), the
    files as ``(name, view)`` and the payload size; raises ``ValueError`` with the rule that failed."""
    if not isinstance(drawable_type, str) or drawable_type not in protocol.DRAWABLE_TYPES:
        raise ValueError("drawable_type is one of protocol.DRAWABLE_TYPES (the game's tokens, such as jbib or p_head)")
    if not isinstance(gender, str) or gender not in protocol.GENDERS:
        raise ValueError("gender is 'male' or 'female'")
    if type(skin) is not bool:
        raise ValueError("skin is True or False")
    if skin and protocol.is_prop_type(drawable_type):
        raise ValueError("only a component shows skin; a prop (p_...) takes skin=False")
    if not protocol.is_text(name):
        raise ValueError("the name is 1 to 128 characters of display text without control characters")
    prepared: List[Tuple[str, memoryview]] = []
    for file_name, data in _pairs(files, "files", "(name, data)"):
        try:
            view = memoryview(data).cast("B")
        except TypeError:
            raise ValueError(f"the data of {file_name!r} is not bytes") from None
        prepared.append((file_name, view))
    entries = [{"name": file_name, "length": view.nbytes} for file_name, view in prepared]
    chosen = [{"file": file, "name": title} for file, title in _pairs(variations, "variations", "(file, name)")]
    reason = protocol.item_files_reason(entries, chosen)
    if reason is not None:
        raise ValueError(reason)
    size = sum(entry["length"] for entry in entries)
    if size > protocol.MAX_BINARY_PAYLOAD_BYTES:
        raise ValueError("the item is larger than one binary frame allows (64 MiB)")
    header: Dict[str, Any] = {"type": "item.add", "format": protocol.MODEL_YDD_XML, "drawableType": drawable_type,
                              "gender": gender, "skin": skin, "name": name, "variations": chosen, "files": entries}
    try:
        # The whole codec, with the longest id the session could give it (the header has a size limit).
        protocol.encode_binary_header(dict(header, id="x" * protocol.MAX_ID_LENGTH), size)
    except ProtocolError as exc:
        if exc.code == protocol.MESSAGE_TOO_LARGE:
            raise ValueError("the file and variation lists do not fit one binary header (16 KiB)") from None
        raise ValueError(f"DCT would refuse this item.add ({exc.code})") from None
    return header, prepared, size


# --------------------------------------------------------------------------------------------------
# The session
# --------------------------------------------------------------------------------------------------

_BACKOFF = (0.5, 1.0, 2.0, 4.0, 8.0, 15.0, 30.0)
#: The longest wait a server's Retry-After may impose before the next connection.
_MAX_RETRY_AFTER = 300.0
#: How long a request that timed out locally keeps its service slot while DCT has not answered it yet.
_SLOT_HOLD_SECONDS = 120.0
#: How many answered DCT requests a connection remembers, so a second answer to one of them is not sent.
_MAX_ANSWERED_HOST_REQUESTS = 256
#: How many withdrawn adds that got no answer in time a connection remembers, so a late answer is still reported.
_MAX_LATE_ADDS = 8
#: When the host's thread has not polled for this long (a long bake in Blender), a background thread keeps the
#: connection alive: it answers DCT's keep-alive pings and reads what arrives, looking every
#: ``_KEEPALIVE_PUMP_SECONDS``, so a long block of the host's thread does not drop the connection.
_KEEPALIVE_IDLE_SECONDS = 2.0
_KEEPALIVE_PUMP_SECONDS = 1.0
#: When DCT answers ``auth`` with ``busy`` the connection stays; the session sends a fresh assertion after these
#: waits, one after another.
_AUTH_BUSY_WAITS = (2.0, 4.0, 8.0, 15.0)
#: When DCT answers ``account.assist`` with ``busy`` or ``rate-limited`` the session asks again for the same device
#: sign-in after these waits, one after another, before it settles on the browser code.
_ASSIST_RETRY_WAITS = (3.0, 10.0)
_ASSIST_RETRY_CODES = frozenset({"busy", "rate-limited"})
#: While DCT answers ``dct-signed-out``, each try mints an assertion with gta.clothing: wait longer each time, up to
#: about five minutes. start() (a user action) tries at once and starts over.
_SIGNED_OUT_WAITS = (30.0, 60.0, 120.0, 240.0, 300.0)

# Session states.
IDLE = "idle"
CONNECTING = "connecting"
HELLO = "hello"
SIGNING_IN = "signing-in"
AUTHENTICATING = "authenticating"
READY = "ready"
WAITING = "waiting"
STOPPED = "stopped"
_HANDSHAKE_STATES = (HELLO, SIGNING_IN, AUTHENTICATING)


class LinkSession:
    """One plugin's link to DCT. See the module documentation for threading.

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
    port range.

    Endpoint safety: an assertion or a sign-in request (``account.assist``) goes only to a Durty Cloth Tool the
    session has verified on this machine; an endpoint it cannot verify is skipped.

    Events (``session.on(name, handler)``): ``state(state)``, ``ready(welcome)``, ``sign-in(SignInPrompt)``,
    ``selection(message)``, ``project(message)``, ``entitlement(message)``, ``open-texture(HostOpenTexture)``,
    ``open-model(HostOpenModel)`` (answer both through the :class:`HostRequest`),
    ``live-status(surface, message)``, ``live-closed(surface, reason)``, ``live-error(surface, LinkError)``,
    ``model-applied(message)``, ``model-closed(message)``, ``incompatible(message)`` (``updateUrl`` only when it
    is a trusted link), ``signed-out()`` (the user signed out; call :meth:`sign_in` when they want to sign in
    again), ``dct-signed-out()`` (DCT itself is signed out; the session keeps trying, waiting 30 seconds and then
    longer, up to about five minutes, and connects once DCT is signed in again, or at once after :meth:`start`),
    ``dct-disconnected()`` (the user disconnected this app in DCT, said over a connection DCT had welcomed; the
    session stopped and connects again only after :meth:`start`), ``item-add-late(request, ItemAddResult)`` (DCT
    answered a withdrawn :meth:`add_item` after the request had failed for want of an answer, on the same
    connection: the cloth may have been added after all), ``ped-add-late(request, PedAddResult)`` (the same for a
    withdrawn :meth:`add_ped`: the custom ped project may have been created after all), ``error(LinkError)``,
    ``disconnected(code, reason)``.

    ``keepalive_thread`` (polling mode only): when the host's thread does not poll for a while, a daemon thread
    answers DCT's keep-alive pings and reads what arrives, so a long block of the host's thread (a bake) does not
    drop a healthy connection. It never runs a callback: everything it read is delivered by the next :meth:`poll`.
    """

    def __init__(
        self,
        plugin: PluginInfo,
        *,
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
        keepalive_thread: bool = True,
        clock: Callable[[], float] = time.monotonic,
        ws_options: Optional[Dict[str, Any]] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        plugin.check()
        self.plugin = plugin
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
        self.keepalive_thread = keepalive_thread
        self._dispatcher = dispatch
        self._clock = clock
        self._ws_options = dict(ws_options or {})
        self._log = logger or _log

        self._lock = threading.RLock()
        self._handlers: Dict[str, List[Handler]] = collections.defaultdict(list)
        self._calls: List[Tuple[Callable[..., Any], Tuple[Any, ...]]] = []
        #: The session's own steps after a finished request (:meth:`_then`), run where the session runs, never dispatched.
        self._steps: List[Tuple[Callable[[Request], Any], Request]] = []
        self._thread: Optional[threading.Thread] = None
        self._stop_thread = threading.Event()
        self._pump: Optional[threading.Thread] = None
        self._stop_pump = threading.Event()
        self._last_poll = clock()

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
        self._handshake_ids: Dict[str, str] = {}
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
        self._discovered: Optional[DiscoveredEndpoint] = None  # the discovery file read for this connection
        self._sign_in_requested = False  # sign_in() was called; the next sign-in check clears a remembered sign-out
        self._assisted_flow: Any = None  # the device sign-in DCT was already asked to approve
        self._assist_retry_at: Optional[float] = None  # DCT could not ask just now: ask again then
        self._assist_retries = 0  # how often DCT was asked again for this device sign-in
        self._dct_signed_out = False
        self._slot_release_at: Dict[str, float] = {}  # timed-out service requests DCT has not answered yet
        self._push_id: Optional[str] = None  # the model push DCT has not answered yet
        self._saves_waiting: List[Request] = []  # model saves waiting for a push in flight
        self._thread_generation = 0
        self._reauth_at: Optional[float] = None  # DCT answered auth with busy: sign in again then
        self._busy_auths = 0
        self._signed_out_tries = 0  # dct-signed-out answers in a row (for the growing wait)
        # DCT requests answered with host.result on one connection (its epoch), oldest first.
        self._answered_host_requests: Tuple[int, "collections.OrderedDict[str, None]"] = (-1, collections.OrderedDict())
        # Withdrawn adds (item.add, ped.add) that failed for want of an answer on this connection, oldest first
        # (item-add-late, ped-add-late).
        self._late_adds: "collections.OrderedDict[str, Union[ItemAddRequest, PedAddRequest]]" = collections.OrderedDict()

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
                steps, self._steps = self._steps, []
                calls, self._calls = self._calls, []
            for step, request in steps:
                step(request)
            if not calls and not steps:
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

    def feature_states(self) -> Dict[str, str]:
        """What DCT last said about its features (``welcome``, then every ``event.entitlement``): feature id to
        ``entitled``, ``needsLicense`` or ``needsUltimate``. A feature DCT did not name is missing. A copy, safe to
        read from any thread."""
        with self._lock:
            return dict(self.features)

    @property
    def endpoint_source(self) -> Optional[str]:
        """How the current (or last) endpoint was found: ``discovery`` (DCT's discovery file), ``probe`` (the port
        range was tried) or ``fixed`` (the ``port`` option); ``None`` before the first connection."""
        return self._endpoint_source if self.endpoint_port is not None else None

    # ---- lifecycle -----------------------------------------------------------------------------------

    def start(self) -> None:
        """Starts connecting (and reconnecting while ``reconnect`` is on). Non-blocking. This is also how the
        user connects again after a ``dct-disconnected`` or ``signed-out`` stop."""
        with self._lock:
            self._want = True
            if self.state in (IDLE, STOPPED, WAITING):
                self._attempt = 0
                self._auth_refusals = 0
                self._signed_out_tries = 0
                self._dct_signed_out = False  # a fresh start tells the host again when DCT is still signed out
                self._begin_connect()
            self._start_pump()
        self._run_calls()

    def _start_pump(self) -> None:
        """Starts the keep-alive thread (polling mode, see the class text) unless it runs. Under the lock."""
        if not self.keepalive_thread or (self._pump is not None and self._pump.is_alive()):
            return
        self._stop_pump = threading.Event()
        self._pump = threading.Thread(target=self._pump_loop, args=(self._stop_pump,), name="dct-link-keepalive",
                                      daemon=True)
        self._pump.start()

    def _pump_loop(self, stop: threading.Event) -> None:
        """Keeps the connection alive while the host's thread does not poll (see the class text). It only touches the
        socket of the current connection, under that socket's own lock, never the session's state."""
        while not stop.wait(_KEEPALIVE_PUMP_SECONDS):
            if self._thread is not None or self._clock() - self._last_poll < _KEEPALIVE_IDLE_SECONDS:
                continue  # a session thread drives the session, or the host polls
            ws = self._ws
            if ws is None:
                continue
            try:
                ws.service()
            except Exception:  # never let the helper die; the next poll reports what is wrong with the socket
                self._log.debug("the keep-alive thread could not service the connection", exc_info=True)

    def _stop_pump_thread(self) -> None:
        self._stop_pump.set()
        pump, self._pump = self._pump, None
        if pump is not None and pump is not threading.current_thread():
            pump.join(2.0)

    def stop(self) -> None:
        """Says ``bye`` and closes. Pending requests fail with ``disconnected``."""
        with self._lock:
            self._want = False
            self._dct_signed_out = False  # the next start reports a signed-out DCT again
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
        self._stop_pump_thread()
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
            self._assist_retry_at = None
            self._assist_retries = 0
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
            if self._reauth_at is not None:
                timeout = min(timeout, max(0.0, self._reauth_at - self._clock()))
            # Sign-in work polls a socket of its own: come back soon (this also keeps an assist retry on time).
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
        self._last_poll = self._clock()
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
        if self._reauth_at is not None and self.state == AUTHENTICATING and self._clock() >= self._reauth_at:
            self._reauth_at = None
            self._begin_auth()  # a fresh assertion for the same connection
        if self._assist_retry_at is not None and self._clock() >= self._assist_retry_at:
            self._retry_assist()
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
        if discovered is not None and self._attempt % 2 == 0:
            self._probes = [(self._new_ws(discovered.port), "discovery")]
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
                    if self._discovered is not None and probe.port == self._discovered.port:
                        source = "discovery"  # a probe that reached the announced port is that endpoint
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
        self._late_adds.clear()  # a later connection cannot answer them
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
        self._reauth_at = None
        self._busy_auths = 0
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
            stop = code == protocol.CLOSE_CODES["incompatible"]
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
        self._drop_connection(reason, code)
        if hint == "disconnected":
            self._dct_disconnected()
        elif hint == "account-mismatch":
            self._want = False
            self._set_state(STOPPED)
        else:
            self._dct_is_signed_out()  # the error message was reported when it arrived

    def _dct_disconnected(self) -> None:
        """The user disconnected this app in DCT: stop, and connect again only when the user asks (start())."""
        if self._ws is not None:
            self._close_connection(1000, "disconnected in DCT")
        self._want = False
        self._set_state(STOPPED)
        self._emit("dct-disconnected")

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
        wait = _SIGNED_OUT_WAITS[min(self._signed_out_tries, len(_SIGNED_OUT_WAITS) - 1)]
        self._signed_out_tries += 1
        self._attempt = max(self._attempt, len(_BACKOFF) - 1)
        self._schedule_retry(wait * (1.0 + random.random() * 0.1))

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
        """The socket is open: say hello."""
        self._set_state(HELLO)
        self._answered = False
        self._handshake_ids = {}
        self._close_hint = None
        self._client_nonce = secrets.token_bytes(protocol.NONCE_BYTES)
        message: Dict[str, Any] = {
            "protocol": {
                "min": protocol.MIN_SUPPORTED_MAJOR,
                "max": protocol.MAX_SUPPORTED_MAJOR,
                "minor": protocol.PROTOCOL_MINOR,
            },
            "plugin": {"kind": self.plugin.kind, "version": self.plugin.version, "channel": self.plugin.channel},
            "host": {"name": self.plugin.host_name, "version": self.plugin.host_version},
            "installId": self.plugin.install_id,
            "clientNonce": b64url_encode(self._client_nonce),
        }
        self._send_handshake("hello", message)
        self._deadline = self._clock() + self.handshake_timeout

    def _endpoint_trusted(self) -> bool:
        return self._endpoint_source in ("discovery", "fixed")

    def _skip_endpoint(self) -> None:
        if self._endpoint_source == "probe" and self.endpoint_port is not None:
            self._skip_ports.add(self.endpoint_port)

    def _others_to_try(self) -> bool:
        """True on a probed endpoint (one that has not welcomed the plugin) while other ports are still untried."""
        if self._endpoint_source != "probe" or self.state == READY:
            return False
        current = self.endpoint_port
        return any(port not in self._skip_ports and port != current for port in self.link_ports)

    def _untrusted_endpoint(self, error: LinkError) -> None:
        """The endpoint behaved like something else, or is not one to sign in with: leave it, try others first."""
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

    def _endpoint_problem(self) -> Optional[str]:
        """Why this connection must not receive an assertion or a sign-in request, or ``None``.

        Loopback ports are shared by every Windows session, so another user's program could listen on a link port.
        When DCT announced itself in a discovery file, sign in only there. On Windows the process behind the
        connection must also run in this Windows session (and be the discovery file's process when there is one);
        when that cannot be determined the endpoint is refused (fail closed).
        """
        discovered = self._discovered
        if discovered is not None and self._endpoint_source != "discovery":
            return "Durty Cloth Tool announced another endpoint"
        if os.name != "nt":
            return None
        owner = self._peer_owner()
        if owner is None:
            return "the program behind this endpoint cannot be identified"
        if discovered is not None and discovered.pid is not None and owner != discovered.pid:
            return "this endpoint is not the Durty Cloth Tool named by its discovery file"
        if _same_session(owner) is not True:
            return "this endpoint does not run in this Windows session"
        return None

    def _on_challenge(self, message: Dict[str, Any]) -> None:
        self._server_nonce = b64url_decode(message["serverNonce"])
        problem = self._endpoint_problem()
        if problem is not None:
            self._untrusted_endpoint(LinkError("untrusted-endpoint", problem))
            return
        self._begin_auth()

    def _on_deadline(self) -> None:
        state = self.state
        self._deadline = None
        if state == HELLO:
            self._skip_endpoint()
        if state in _HANDSHAKE_STATES:
            self._fail_handshake(LinkError("timeout", f"DCT did not answer during {state}"), 1000)

    # ---- sign-in (assertions and device sign-in) -------------------------------------------------------

    def _worker(self, call: Callable[[], Any]) -> Any:
        """Runs a blocking call (token source, secret store) on a worker thread, or inline without threads."""
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
                    self._assist_retry_at = None
                    self._assist_retries = 0
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
        flow = self._sign_in
        if flow is not None and getattr(flow, "expires_at", None) is not None and not getattr(flow, "cancelled", False):
            self._assist(flow)  # a sign-in started on an earlier connection is still running
            return
        self._token_task = (self._epoch, "device", self._make_task("device"))

    def _assist(self, flow: Any) -> None:
        self._sign_in = flow
        self._set_state(SIGNING_IN)
        if self._assisted_flow is not flow:
            # DCT is asked once per device sign-in (until the user asks again with sign_in()): a user who declined
            # in DCT is not asked again on every reconnect.
            self._assisted_flow = flow
            self._assist_retry_at = None
            self._assist_retries = 0
            self._send_handshake("account.assist", {"userCode": flow.user_code})
        self._emit(
            "sign-in",
            SignInPrompt(flow.user_code, flow.verification_uri, getattr(flow, "verification_uri_complete", None)),
        )

    def _assist_answered(self, ok: bool, code: Optional[str]) -> None:
        """DCT answered ``account.assist``. ``busy`` and ``rate-limited`` mean DCT could not ask just now: ask again
        for the same device sign-in after 3 and then 10 seconds. Any other refusal, and a third one of these, leaves
        the sign-in to the browser code."""
        flow = self._sign_in
        if flow is None or self.state != SIGNING_IN:
            return
        if not ok and code in _ASSIST_RETRY_CODES and self._assist_retries < len(_ASSIST_RETRY_WAITS):
            self._assist_retry_at = self._clock() + _ASSIST_RETRY_WAITS[self._assist_retries]
            self._assist_retries += 1
            return  # the prompt keeps saying that DCT is being asked
        self._assist_retry_at = None
        self._emit("sign-in", SignInPrompt(flow.user_code, flow.verification_uri,
                                           getattr(flow, "verification_uri_complete", None), ok))

    def _retry_assist(self) -> None:
        """Asks DCT again to approve the running device sign-in (a wait after ``busy`` or ``rate-limited`` ended).
        Without a connection in the sign-in step the retry waits for the next one."""
        flow = self._sign_in
        if flow is None or flow is not self._assisted_flow or getattr(flow, "cancelled", False):
            self._assist_retry_at = None
            return
        ws = self._ws
        if self.state != SIGNING_IN or ws is None or not ws.is_open:
            return
        self._assist_retry_at = None
        self._send_handshake("account.assist", {"userCode": flow.user_code})

    def _send_auth(self, assertion: str) -> None:
        claims = _assertion_claims(assertion)
        if claims.get("aud") != ASSERTION_AUDIENCE or claims.get("nonce") != b64url_encode(self._server_nonce):
            self._fail_handshake(LinkError("assertion-invalid", "the assertion is not for this connection"), 1000,
                                 retry=not self._count_refusal(close=False))
            return
        self._set_state(AUTHENTICATING)
        self._send_handshake("auth", {"assertion": assertion})
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
        self._signed_out_tries = 0
        self._dct_signed_out = False
        self._sign_in_requested = False
        if self.endpoint_port is not None:
            self._skip_ports.discard(self.endpoint_port)
        self._assist_retry_at = None
        self._assist_retries = 0
        self.welcome = message
        # Replaced as a whole, never changed in place: another thread reading it sees the old or the new states.
        self.features = {f["id"]: f["state"] for f in message["features"]}
        self.account_name = message["account"]["userName"]
        self._attempt = 0
        self._set_state(READY)
        self._emit("ready", message)

    def _on_handshake_error(self, answered: Optional[str], message: Dict[str, Any]) -> None:
        code = message["code"]
        error = LinkError(code, message.get("message") or "")
        if code == "disconnected":
            # DCT sends "disconnected" only to a connection it welcomed (handled in _closed_after), never during the
            # handshake. Here it proves nothing (a program squatting on a link port could say it to stop the plugin
            # for good): leave this endpoint like any other unproven refusal, try the others, keep the session.
            self._untrusted_endpoint(LinkError("untrusted-endpoint", "an endpoint sent disconnected before welcome"))
            return
        if answered == "account.assist":
            # DCT could not prompt now (busy, rate-limited). The device sign-in goes on: DCT is
            # asked again a little later, and the user can approve it in the browser meanwhile.
            self._assist_answered(False, code)
            return
        if answered == "auth" and code == "busy":
            # DCT keeps the connection: sign in again a little later.
            self._reauth_at = self._clock() + _AUTH_BUSY_WAITS[min(self._busy_auths, len(_AUTH_BUSY_WAITS) - 1)]
            self._busy_auths += 1
            self._deadline = None
            return
        if answered == "auth" and code in ("token-invalid", "authentication-failed"):
            # A refused assertion ends this connection; the next one mints a fresh assertion.
            if not self._count_refusal():
                self._fail_handshake(error, 1000, retry=True)
            return
        if code == "dct-signed-out":
            self._dct_is_signed_out(error)  # not a refusal of this plugin: keep trying now and then
            return
        stop = code in ("account-mismatch", "plugin-too-old", "dct-too-old", "unsupported-protocol")
        if stop and self._others_to_try():
            # A probed endpoint proved nothing: leave it and try the others before giving up.
            self._untrusted_endpoint(error)
            return
        if code == "rate-limited":
            self._attempt = max(self._attempt, len(_BACKOFF) - 2)
        self._fail_handshake(error, 1000, retry=not stop)

    # ---- incoming messages ---------------------------------------------------------------------------

    def _on_text(self, data: bytes) -> None:
        try:
            message = protocol.decode_text(data, protocol.TO_CLIENT)
        except ProtocolError as exc:
            if (
                self.state != READY
                and exc.code == protocol.UNSUPPORTED_PROTOCOL
                and exc.version is not None
                and 1 <= exc.version <= protocol.MAX_PROTOCOL_MAJOR
            ):
                # A DCT of another major cannot read this hello and refuses it in its own major: it is incompatible.
                older = exc.version < protocol.PROTOCOL_MAJOR
                self._on_handshake_message("incompatible", {
                    "type": "incompatible", "code": "dct-too-old" if older else "plugin-too-old",
                    "dct": {"protocol": {"min": exc.version, "max": exc.version}},
                })
            elif self.state != READY:
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
        late = self._late_adds.get(re_id) if re_id else None
        if late is not None and kind in ("error", "item.addResult" if isinstance(late, ItemAddRequest) else "ped.addResult"):
            del self._late_adds[re_id]
            if isinstance(late, ItemAddRequest):
                item = ItemAddResult(False, message["code"], None, []) if kind == "error" else _item_add_answer(message)
                self._emit("item-add-late", late, item)
            else:
                ped = PedAddResult(False, message["code"], None, []) if kind == "error" else _ped_add_answer(message)
                self._emit("ped-add-late", late, ped)
            return
        request = self._pending.get(re_id) if re_id else None
        if kind == "error":
            if request is not None:
                self._pending.pop(re_id, None)
                refusal = _REFUSALS.get(request.type)
                if refusal is not None:
                    # DCT refused the picture, the skeleton or the add: an answer, not a failure of the request.
                    self._finish_request(request, result=refusal(message["code"]))
                else:
                    self._finish_request(request, error=LinkError(message["code"], message.get("message") or ""))
            else:
                if message["code"] in ("dct-signed-out", "account-mismatch", "disconnected"):
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
        elif answered == "account.assist" and kind == "account.assistResult":
            self._assist_answered(bool(message["ok"]), message.get("code"))
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
            self._emit_host_request("open-texture", HostOpenTexture(self, header, frame.payload, self._epoch))
        elif kind == "host.openModel":
            self._emit_host_request("open-model", HostOpenModel(self, header, frame.payload, self._epoch))

    def _emit_host_request(self, event: str, request: HostRequest) -> None:
        """Raises a request from DCT. Without a handler DCT hears ``not-supported`` at once; a handler that raises
        before anything answered makes it ``open-failed``. Any other handler answers itself."""
        handlers = list(self._handlers.get(event, []))
        if not handlers:
            request._answer("not-supported")
            return
        for handler in handlers:
            self._calls.append((_answering_on_failure(handler), (request,)))

    def _answer_host_request(self, epoch: int, request_id: str, code: Optional[str]) -> bool:
        """Sends ``host.result`` on the connection the request came from, while it is the current one, once per
        request id."""
        with self._lock:
            if epoch != self._epoch or self.state != READY:
                return False
            answered = self._answered_host_requests
            if answered[0] != epoch:  # a new connection remembers nothing of the last one
                answered = self._answered_host_requests = (epoch, collections.OrderedDict())
            if request_id in answered[1]:
                return False
            message: Dict[str, Any] = {"type": "host.result", "id": self._new_id(), "re": request_id, "ok": code is None}
            if code is not None:
                message["code"] = code
            try:
                self._send(message)
            except LinkError as exc:
                if exc.code != "disconnected":
                    self._report(exc)
                return False
            answered[1][request_id] = None
            if len(answered[1]) > _MAX_ANSWERED_HOST_REQUESTS:
                answered[1].popitem(last=False)
            return True

    def send_host_result(self, request_id: str, ok: bool, code: Optional[str] = None) -> bool:
        """Answers DCT's ``host.openTexture`` or ``host.openModel`` (``request_id`` is its ``id``) with
        ``host.result``: ``ok`` true without a code, or false with one of :data:`protocol.HOST_RESULT_CODES`. The
        events hand out a :class:`HostRequest` that does this; call it directly only for a request kept elsewhere.
        Raises ``ValueError`` for an invalid id or code. Returns ``True`` when it was sent, ``False`` when nothing was
        sent: the link is not ready, or this connection already answered that id."""
        if not protocol.is_id(request_id):
            raise ValueError("a request id is 1 to 64 of A-Z a-z 0-9 _ -")
        if ok and code is not None:
            raise ValueError("an accepted request carries no code")
        if not ok and code not in protocol.HOST_RESULT_CODES:
            raise ValueError(f"{code!r} is not a host.result code")
        with self._lock:
            return self._answer_host_request(self._epoch, request_id, None if ok else code)

    def _on_entitlement(self, message: Dict[str, Any]) -> None:
        # A new dict, never an update in place (see _on_welcome). Features the event does not name keep their state.
        self.features = dict(self.features, **{f["id"]: f["state"] for f in message["features"]})
        self._emit("entitlement", message)

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
        steps, request._continuations = request._continuations, []
        self._steps.extend((step, request) for step in steps)

    def _then(self, request: Request, step: Callable[[Request], Any]) -> None:
        """Runs ``step(request)`` once ``request`` finished, on the session's own path (its thread, or whoever polls
        it) rather than through ``dispatch``; ``step`` must not raise."""
        with self._lock:
            if not request.done:
                request._continuations.append(step)
                return
        step(request)

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
            if isinstance(request, WithdrawableRequest):
                if request._withdrawn is None:
                    # DCT may still be working or asking the user: withdraw it and wait a short grace for its answer.
                    self._withdraw(request, "timeout")
                else:
                    self._pending.pop(request.id, None)
                    self._finish_request(request, error=LinkError(
                        request._withdrawn, f"DCT did not answer the withdrawn {request.type}"))
                    if isinstance(request, (ItemAddRequest, PedAddRequest)):
                        # DCT may still answer it (the user chose Add, or created the ped project, as the withdrawal
                        # arrived): report that answer.
                        self._late_adds[request.id] = request
                        while len(self._late_adds) > _MAX_LATE_ADDS:
                            self._late_adds.popitem(last=False)
                continue
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

    def _register(self, message_type: str, timeout: Optional[float], kind: Callable[..., Request] = Request) -> Request:
        if self.state != READY:
            raise LinkError("not-authenticated", "the link is not ready")
        request = kind(self, self._new_id(), message_type, self.request_timeout if timeout is None else timeout)
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

    def request_thumbnail(self, size: int = 128, binding: Optional[Dict[str, str]] = None,
                          timeout: Optional[float] = 30.0) -> Request:
        """``item.thumbnail``: a small RGBA8 picture of a cloth, the focused item without ``binding``. ``size`` is the
        longest edge wanted, 16 to 256 (``ValueError`` otherwise). Resolves with a :class:`Thumbnail`, or with a
        :class:`ThumbnailRefusal` when DCT refused (its error code). Fails with :class:`LinkError` when the request
        itself failed (``timeout``, ``disconnected``), and with ``protocol-violation`` when DCT's picture is larger
        than ``size`` or of another cloth than ``binding``. It counts as a service request (two at a time)."""
        if type(size) is not int or not protocol.MIN_THUMBNAIL_EDGE <= size <= protocol.MAX_THUMBNAIL_EDGE:
            raise ValueError("a thumbnail is 16 to 256 pixels on its longest edge")
        if binding is not None and not _is_binding(binding):
            raise ValueError("a binding names a cloth and a texture variation by their ids (8-4-4-4-12 hex digits)")
        return self.request("item.thumbnail", {"size": size, "binding": binding}, timeout=timeout,
                            transform=_thumbnail_answer(size, binding))

    # ---- adding an item (Blender) --------------------------------------------------------------------

    def request_skeleton_template(self, gender: str, timeout: Optional[float] = 90.0) -> Request:
        """``skeleton.template``: the freemode skeleton of ``gender`` (``male`` or ``female``, ``ValueError``
        otherwise), which DCT builds from the user's own game files. Resolves with a :class:`SkeletonTemplate` (one
        ``*.ydd.xml`` in ``files``), or with a :class:`SkeletonTemplateRefusal` when DCT refused (its error code:
        ``game-required`` without the game files, ``busy`` when DCT still reads them after a minute). Fails with
        :class:`LinkError` when the request itself failed (``timeout``, ``disconnected``), and with
        ``protocol-violation`` when DCT sends the skeleton of the other gender. It counts as a service request (two
        at a time); DCT may wait up to a minute for its game files before it answers."""
        if not isinstance(gender, str) or gender not in protocol.GENDERS:
            raise ValueError("gender is 'male' or 'female'")
        return self.request("skeleton.template", {"gender": gender}, timeout=timeout, transform=_skeleton_answer(gender))

    def add_item(
        self,
        drawable_type: str,
        gender: str,
        skin: bool,
        name: str,
        variations: Sequence[Tuple[str, str]],
        files: Sequence[Tuple[str, Union[bytes, bytearray, memoryview]]],
        timeout: Optional[float] = 900.0,
    ) -> ItemAddRequest:
        """``item.add``: adds a new cloth to the open project. DCT shows the user what arrives and adds nothing unless
        the user chooses Add there, so the answer can take minutes.

        ``drawable_type`` is the slot (one of :data:`protocol.DRAWABLE_TYPES`, such as ``jbib`` or ``p_head``),
        ``gender`` is ``male`` or ``female``, ``skin`` says the cloth shows skin (components only, never a ``p_``
        prop) and ``name`` is the name the user sees. ``files`` lists ``(name, data)`` in payload order: one
        ``*.ydd.xml``, its ``*.dds`` textures, then the variation diffuses as ``*.png`` or ``*.dds``; names are bare
        and unique ignoring case, and no file is empty. ``variations`` lists ``(file, name)`` per colour variation,
        1 to :data:`protocol.MAX_ITEM_VARIATIONS` (26) in order: ``file`` names that variation's diffuse among
        ``files`` (never the model, no two the same), ``name`` is its display name; every ``*.png`` is some
        variation's diffuse. A broken rule raises ``ValueError`` before anything is sent. The data is sent as given,
        without a copy: do not change it until the request finishes.

        Resolves with an :class:`ItemAddResult`, whatever DCT decided (also when DCT answered with an error such as
        ``busy`` or ``rate-limited``). Fails with :class:`LinkError` only when no answer came: ``disconnected``, or
        ``timeout`` / ``cancelled`` when the withdrawn add (see :meth:`ItemAddRequest.cancel`; a timeout withdraws
        it too) got no answer within 10 seconds; DCT's answer after that arrives as the ``item-add-late`` event. It
        does not take a service slot. Callable from any thread."""
        header, files_out, size = _prepare_item(drawable_type, gender, skin, name, variations, files)
        with self._lock:
            request = self._register("item.add", timeout, ItemAddRequest)
            request.transform = _item_add_answer
            header["id"] = request.id
            ws = self._ws
            try:
                # The files are written one after another; they are never joined in memory.
                prefix = protocol.encode_binary_header(header, size)
                if ws is None or not ws.is_open:
                    raise LinkError("disconnected", "not connected to DCT")
                ws.send_binary(prefix, *(data for _, data in files_out))
            except (LinkError, ProtocolError, WebSocketError) as exc:
                self._pending.pop(request.id, None)
                if isinstance(exc, LinkError):
                    error = exc
                elif isinstance(exc, ProtocolError):
                    error = LinkError(exc.code, str(exc))
                else:
                    error = LinkError("disconnected", str(exc))
                self._finish_request(request, error=error)
        self._run_calls()
        return request  # type: ignore[return-value]

    def _withdraw(self, request: WithdrawableRequest, reason: str) -> bool:
        """Sends the cancel of a request that still waits, once, and gives DCT a short grace to answer it (its answer
        then resolves the request as usual). Under the lock."""
        if request.done or request._withdrawn is not None or self._pending.get(request.id) is not request:
            return False
        request._withdrawn = reason
        request.deadline = self._clock() + _ADD_CANCEL_GRACE_SECONDS
        try:
            self._send({"type": request.cancel_type, "id": self._new_id(), "re": request.id})
        except LinkError as exc:
            self._pending.pop(request.id, None)
            self._finish_request(request, error=exc)
            return False
        return True

    # ---- custom peds (Blender) ------------------------------------------------------------------------

    def list_ped_templates(self, gender: Optional[str] = None, show_all: bool = False, timeout: Optional[float] = 120.0) -> Request:
        """``ped.templates``: every human ped template installed in the GTA V Legacy folder DCT uses, recommended entries
        first. Without ``show_all`` only ambient peds; ``show_all`` adds freemode, player, cutscene and story templates. ``gender``
        filters by gender (``ValueError`` for another value). DCT answers in pages
        (:data:`protocol.PED_TEMPLATES_PER_PAGE`); the request asks for one after the other and resolves with
        :class:`PedTemplates` holding them all, or with a :class:`PedRefusal` when DCT refused (``game-required``). It
        starts again when the installed peds change meanwhile, and fails with ``protocol-violation`` when DCT's pages
        do not join up. Each page is a service request (two at a time) with its own ``timeout``; DCT reads its game
        files the first time."""
        if gender is not None and gender not in protocol.GENDERS:
            raise ValueError("gender is 'male', 'female' or None")
        if type(show_all) is not bool:
            raise ValueError("show_all is True or False")
        fields: Dict[str, Any] = {"all": show_all}
        if gender is not None:
            fields["gender"] = gender
        with self._lock:
            if self.state != READY:
                raise LinkError("not-authenticated", "the link is not ready")
            listing = Request(self, self._new_id(), "ped.templates", None)
        _PedTemplatePages(self, listing, fields, timeout).ask()
        return listing

    def request_ped_skeleton(self, model: str, timeout: Optional[float] = 120.0) -> Request:
        """``ped.skeleton``: the rest skeleton of an installed human template (``ValueError`` for a name that is not a
        ped model name). Resolves with a :class:`ped.PedSkeleton` (every bone with its tag, parent, flags, local rest
        transform and rest world matrix, in the skeleton's order), or with a :class:`PedRefusal` (``game-required``,
        ``template-not-found``). Fails with ``protocol-violation`` when DCT answers with another template. A service
        request."""
        if not protocol.is_ped_model(model):
            raise ValueError("model is a ped model name")
        return self.request("ped.skeleton", {"model": model}, timeout=timeout, transform=_ped_skeleton_answer(model))

    def rig_ped(
        self,
        template: str,
        markers: Mapping[str, Sequence[float]],
        positions: Any,
        triangles: Any,
        *,
        rights_confirmed: bool,
        parts: Optional[Sequence[str]] = None,
        part_ids: Any = None,
        options: Optional[Mapping[str, Any]] = None,
        on_accepted: Optional[Callable[[str], Any]] = None,
        on_progress: Optional[Callable[[str, float], Any]] = None,
        timeout: Optional[float] = 600.0,
    ) -> PedRigRequest:
        """``ped.rig`` (Ultimate): DCT fits the template's skeleton to the character's markers and computes weights and
        the rest pose from the user's own game files. ``positions`` holds x, y, z per vertex and ``triangles`` three
        vertex indices each (sequences, or buffers such as NumPy ``float32`` and ``uint32`` arrays, sent without a
        copy: do not change them until the request finishes); with ``parts`` (part roles) ``part_ids`` names each
        vertex's part. ``rights_confirmed`` must be True: the user confirmed the rights notice for this character.
        A broken rule raises ``ValueError`` before anything is sent.

        Resolves with a :class:`ped.PedRig`, or with a :class:`PedRigRefusal` whatever DCT refused with.
        ``on_accepted(job)`` runs once DCT started the rig, ``on_progress(stage, fraction)`` at most four times a second
        while it runs. It takes no service slot; :meth:`PedRigRequest.cancel` (or a timeout) sends ``ped.rig.cancel``.
        Callable from any thread."""
        prepared = ped_module.prepare_ped_rig(template, markers, positions, triangles, rights_confirmed=rights_confirmed,
                                             parts=parts, part_ids=part_ids, options=options)
        vertices = prepared.header["mesh"]["vertices"]
        with self._lock:
            request = self._register("ped.rig", timeout, PedRigRequest)
            request.transform = _ped_rig_answer(template, vertices)
            request.on_accepted, request.on_progress = on_accepted, on_progress
            header = dict(prepared.header, id=request.id)
            ws = self._ws
            try:
                prefix = protocol.encode_binary_header(header, prepared.size)
                if ws is None or not ws.is_open:
                    raise LinkError("disconnected", "not connected to DCT")
                ws.send_binary(prefix, *prepared.parts)
            except (LinkError, ProtocolError, WebSocketError) as exc:
                self._pending.pop(request.id, None)
                self._finish_request(request, error=_link_error(exc))
        self._run_calls()
        return request  # type: ignore[return-value]

    def add_ped(
        self,
        template: str,
        name: str,
        model: str,
        glb: Any,
        *,
        rights_confirmed: bool,
        rig: Optional[str] = None,
        ragdoll: Optional[str] = None,
        parts: Optional[Sequence[Tuple[str, str]]] = None,
        timeout: Optional[float] = 900.0,
    ) -> PedAddRequest:
        """``ped.add`` (Advanced or Ultimate): uploads the rigged character as a GLB in chunks; DCT builds the ped, shows
        it to its user and asks where to create the project, so the answer can take minutes. ``name`` is the name the
        user sees, ``model`` the new ped's model name, ``rig`` the job of the rig the GLB carries, ``ragdoll`` another
        shared ragdoll body (``fred``, ``wilma``, ``fred-large``, ``wilma-large``), ``parts`` ``(mesh name, role)``
        pairs (a mesh not listed is ``body``). ``rights_confirmed`` must be True. A broken rule raises ``ValueError``
        before anything is sent; the GLB is sent without a copy.

        Resolves with a :class:`PedAddResult`, whatever DCT decided. Fails with :class:`LinkError` only when no answer
        came: ``disconnected``, or ``timeout`` / ``cancelled`` when the withdrawn add (:meth:`PedAddRequest.cancel`, or
        a timeout, sends ``ped.addCancel``) got no answer within 10 seconds; DCT's answer after that arrives as the
        ``ped-add-late`` event. It takes no service slot. Callable from any thread."""
        if rights_confirmed is not True:
            raise ValueError("the user has not confirmed the rights notice for this character; DCT refuses an add without it")
        sha256, chunks = ped_module.plan_ped_add_upload(glb)
        message: Dict[str, Any] = {"type": "ped.add", "template": template, "name": name, "model": model, "rights": True,
                                   "glbLength": sum(chunk.nbytes for chunk in chunks), "chunks": len(chunks), "sha256": sha256}
        if rig is not None:
            message["rig"] = rig
        if ragdoll is not None:
            message["ragdoll"] = ragdoll
        if parts is not None:
            message["parts"] = [{"mesh": mesh, "role": role} for mesh, role in _pairs(parts, "parts", "(mesh, role)")]
        problem = protocol.ped_add_problem(message)
        if problem is not None:
            raise ValueError(problem)
        with self._lock:
            request = self._register("ped.add", timeout, PedAddRequest)
            request.transform = _ped_add_answer
            message["id"] = request.id
            ws = self._ws
            try:
                self._send(message)
                if ws is None or not ws.is_open:
                    raise LinkError("disconnected", "not connected to DCT")
                for index, chunk in enumerate(chunks):
                    prefix = protocol.encode_binary_header({"type": "ped.add.chunk", "re": request.id, "index": index}, chunk.nbytes)
                    ws.send_binary(prefix, chunk)
            except (LinkError, ProtocolError, WebSocketError) as exc:
                self._pending.pop(request.id, None)
                self._finish_request(request, error=_link_error(exc))
        self._run_calls()
        return request  # type: ignore[return-value]

    def _on_ped_rig_accepted(self, message: Dict[str, Any]) -> None:
        request = self._pending.get(message["re"])
        if isinstance(request, PedRigRequest):
            request.job = message["job"]
            if request.on_accepted is not None:
                self._calls.append((request.on_accepted, (message["job"],)))

    def _on_ped_rig_progress(self, message: Dict[str, Any]) -> None:
        for request in list(self._pending.values()):
            if isinstance(request, PedRigRequest) and request.job == message["job"] and request.on_progress is not None:
                self._calls.append((request.on_progress, (message["stage"], float(message["fraction"]))))

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


def _answering_on_failure(handler: Handler) -> Handler:
    """Runs a host request handler; when it raises before anything answered, DCT hears ``open-failed``. The error is
    raised on, so the session logs and reports it like any failing callback."""

    def call(request: HostRequest) -> None:
        try:
            handler(request)
        except Exception:
            request._handler_failed()
            raise

    return call


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
    "event.entitlement": LinkSession._on_entitlement,
    "live.status": LinkSession._on_live_status,
    "live.closed": LinkSession._on_live_closed,
    "model.applied": LinkSession._on_model_applied,
    "model.closed": LinkSession._on_model_closed,
    "ped.rig.accepted": LinkSession._on_ped_rig_accepted,
    "ped.rig.progress": LinkSession._on_ped_rig_progress,
}


def _link_error(exc: BaseException) -> LinkError:
    """A send that failed, as the error that ends its request."""
    if isinstance(exc, LinkError):
        return exc
    if isinstance(exc, ProtocolError):
        return LinkError(exc.code, str(exc))
    return LinkError("disconnected", str(exc))
