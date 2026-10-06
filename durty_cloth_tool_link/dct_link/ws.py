# SPDX-License-Identifier: MIT
# Copyright (c) Schmid Software Solutions (https://schmid-software.de)
"""A small RFC 6455 WebSocket client for the Creator Link loopback connection.

Only what Creator Link needs: ``ws://`` to a loopback address, no extensions (no compression), no
subprotocols, masked client frames, fragmented messages in both directions, ping and pong, the close
handshake and size limits that match the protocol constants.

One non-blocking core serves two ways of driving it:

* **Polling** (Blender, which has no supported threads): call :meth:`WebSocketClient.poll` regularly, for
  example from ``bpy.app.timers``. Each call does a bounded amount of work and returns the events it produced:
  connect progress, at most ``budget`` bytes handed to the operating system, at most ``budget`` bytes read,
  and at most one outgoing fragment (``fragment_bytes``, 1 MiB by default) masked ahead of what was written.
* **Blocking** (a host that runs the link on a background thread): call :meth:`WebSocketClient.connect` and then
  :meth:`WebSocketClient.receive` in a loop. Other threads may call the ``send_*`` methods at any time; a
  wakeup socket interrupts the waiting thread so queued data goes out at once.
"""

from __future__ import annotations

import base64
import collections
import errno
import hashlib
import ipaddress
import os
import select
import socket
import threading
import time
from typing import Callable, Deque, List, NamedTuple, Optional, Sequence, Union

from . import protocol

__all__ = [
    "WebSocketClient",
    "WebSocketError",
    "HandshakeError",
    "Event",
    "check_loopback_host",
    "mask_payload",
]

OP_CONTINUATION = 0x0
OP_TEXT = 0x1
OP_BINARY = 0x2
OP_CLOSE = 0x8
OP_PING = 0x9
OP_PONG = 0xA

CLOSE_NORMAL = 1000
CLOSE_GOING_AWAY = 1001
CLOSE_PROTOCOL_ERROR = 1002
CLOSE_NO_STATUS = 1005
CLOSE_ABNORMAL = 1006
CLOSE_INVALID_DATA = 1007
CLOSE_POLICY = 1008
CLOSE_TOO_BIG = 1009

_ACCEPT_GUID = b"258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
_MAX_HANDSHAKE_BYTES = 16384
_DEFAULT_FRAGMENT = 1 << 20
_DEFAULT_BUDGET = 1 << 20

Buffer = Union[bytes, bytearray, memoryview]


class WebSocketError(Exception):
    """A connection, handshake or framing failure."""


class HandshakeError(WebSocketError):
    """The server did not upgrade the connection the way RFC 6455 requires."""


class Event(NamedTuple):
    """Something :meth:`WebSocketClient.poll` observed.

    ``kind`` is ``"open"``, ``"text"`` (``data`` is UTF-8 bytes), ``"binary"``, ``"pong"`` or ``"closed"``
    (``code`` and ``reason`` describe the close; ``CLOSE_ABNORMAL`` when the connection simply dropped).
    """

    kind: str
    data: Optional[bytes] = None
    code: Optional[int] = None
    reason: str = ""


def check_loopback_host(host: str) -> str:
    """Returns the IP literal to connect to, or raises ``ValueError`` for anything that is not loopback.

    Names are not resolved (``localhost`` maps to ``127.0.0.1`` without DNS), so a hosts file or resolver
    can never point the link at another machine.
    """
    candidate = host.strip("[]") if isinstance(host, str) else ""
    if candidate.lower() == "localhost":
        return "127.0.0.1"
    try:
        address = ipaddress.ip_address(candidate)
    except ValueError:
        raise ValueError("Creator Link connects to a loopback IP address only") from None
    if not address.is_loopback:
        raise ValueError("Creator Link connects to a loopback IP address only")
    return str(address)


def mask_payload(data: Buffer, mask: bytes) -> bytes:
    """XORs ``data`` with the repeating four-byte ``mask`` (RFC 6455 section 5.3)."""
    length = len(data)
    if length == 0:
        return b""
    key = (mask * ((length >> 2) + 1))[:length]
    return (int.from_bytes(data, "little") ^ int.from_bytes(key, "little")).to_bytes(length, "little")


def _frame_header(opcode: int, length: int, fin: bool, mask: bytes) -> bytes:
    first = (0x80 if fin else 0) | opcode
    if length < 126:
        return bytes((first, 0x80 | length)) + mask
    if length < 65536:
        return bytes((first, 0x80 | 126)) + length.to_bytes(2, "big") + mask
    return bytes((first, 0x80 | 127)) + length.to_bytes(8, "big") + mask


def _close_payload(code: Optional[int], reason: str = "") -> bytes:
    if code is None or code == CLOSE_NO_STATUS:
        return b""
    return code.to_bytes(2, "big") + reason.encode("utf-8")[:123]


def _valid_close_code(code: int) -> bool:
    return code in (1000, 1001, 1002, 1003, 1007, 1008, 1009, 1010, 1011, 1012, 1013, 1014) or 3000 <= code <= 4999


class _Outgoing:
    """One queued message, written as one or more fragments."""

    __slots__ = ("opcode", "parts", "part", "offset", "remaining", "started", "on_sent")

    def __init__(self, opcode: int, parts: Sequence[Buffer], on_sent: Optional[Callable[[], None]]) -> None:
        self.opcode = opcode
        self.parts = [memoryview(p).cast("B") if not isinstance(p, memoryview) or p.format != "B" else p for p in parts]
        self.part = 0
        self.offset = 0
        self.remaining = sum(p.nbytes for p in self.parts)
        self.started = False
        self.on_sent = on_sent

    def take(self, count: int) -> bytes:
        chunks = []
        while count > 0 and self.part < len(self.parts):
            view = self.parts[self.part]
            piece = view[self.offset : self.offset + count]
            chunks.append(piece)
            count -= piece.nbytes
            self.offset += piece.nbytes
            self.remaining -= piece.nbytes
            if self.offset >= view.nbytes:
                self.part += 1
                self.offset = 0
        return b"".join(chunks)


class WebSocketClient:
    """An RFC 6455 client on a loopback TCP connection. See the module documentation for the two modes."""

    CONNECTING = "connecting"
    HANDSHAKE = "handshake"
    OPEN = "open"
    CLOSING = "closing"
    CLOSED = "closed"

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = protocol.DEFAULT_PORT,
        path: str = protocol.PATH,
        *,
        max_text_bytes: int = protocol.MAX_CONTROL_MESSAGE_BYTES,
        max_binary_bytes: int = protocol.MAX_BINARY_FRAME_BYTES,
        fragment_bytes: Optional[int] = _DEFAULT_FRAGMENT,
        connect_timeout: float = 5.0,
        close_timeout: float = 5.0,
        keepalive_interval: float = protocol.KEEP_ALIVE_SECONDS,
        keepalive_timeout: float = protocol.KEEP_ALIVE_TIMEOUT_SECONDS,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.host = check_loopback_host(host)
        if not isinstance(port, int) or not 0 < port < 65536:
            raise ValueError("port must be 1 to 65535")
        if not path.startswith("/") or any(c in path for c in " \r\n"):
            raise ValueError("path must be an absolute request path")
        self.port = port
        self.path = path
        self.max_text_bytes = max_text_bytes
        self.max_binary_bytes = max_binary_bytes
        self.fragment_bytes = fragment_bytes if fragment_bytes else None
        self.connect_timeout = connect_timeout
        self.close_timeout = close_timeout
        self.keepalive_interval = keepalive_interval
        self.keepalive_timeout = keepalive_timeout
        self._clock = clock

        self._lock = threading.RLock()
        self._sock: Optional[socket.socket] = None
        self._wake_r: Optional[socket.socket] = None
        self._wake_w: Optional[socket.socket] = None
        self.state = self.CLOSED
        self._started = False
        self._deadline = 0.0
        self._key = b""
        self._rbuf = bytearray()
        self._wbuf = memoryview(b"")
        self._wbuf_done: Optional[Callable[[], None]] = None
        self._sent_later: List[Callable[[], None]] = []
        self._queue: Deque[_Outgoing] = collections.deque()
        self._control: Deque[bytes] = collections.deque()
        self._message_opcode: Optional[int] = None
        self._message_parts: List[bytes] = []
        self._message_size = 0
        self._events: List[Event] = []
        self._close_sent = False
        self._close_received = False
        self._drop_after_flush = False
        self.close_code: Optional[int] = None
        self.close_reason = ""
        self._last_received = 0.0
        self._last_ping = 0.0

    # ---- lifecycle -------------------------------------------------------------------------------

    @property
    def is_open(self) -> bool:
        return self.state == self.OPEN

    @property
    def closed(self) -> bool:
        return self.state == self.CLOSED and self._started

    def start(self) -> None:
        """Begins a non-blocking connect. Progress happens in :meth:`poll`."""
        with self._lock:
            if self._started:
                raise WebSocketError("a WebSocketClient connects once; create a new one to reconnect")
            self._started = True
            family = socket.AF_INET6 if ":" in self.host else socket.AF_INET
            sock = socket.socket(family, socket.SOCK_STREAM)
            sock.setblocking(False)
            try:
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            except OSError:
                pass  # an optimisation only; Nagle merely adds latency
            self._sock = sock
            self.state = self.CONNECTING
            self._deadline = self._clock() + self.connect_timeout
            result = sock.connect_ex((self.host, self.port))
            if result not in (0, errno.EINPROGRESS, errno.EWOULDBLOCK, getattr(errno, "WSAEWOULDBLOCK", -1)):
                self._fail_connect(f"connect failed ({errno.errorcode.get(result, result)})")

    def connect(self, timeout: Optional[float] = None) -> None:
        """Connects and completes the handshake, blocking the calling thread. Raises :class:`WebSocketError`."""
        if not self._started:
            self.start()
        end = self._clock() + (self.connect_timeout if timeout is None else timeout)
        while True:
            events = self.poll()
            for index, event in enumerate(events):
                if event.kind == "open":
                    with self._lock:  # frames that arrived with the handshake stay queued for receive()
                        self._events[:0] = events[index + 1 :]
                    return
                if event.kind == "closed":
                    raise WebSocketError(f"connection failed: {event.reason or event.code}")
            if self.state == self.OPEN:
                return
            remaining = end - self._clock()
            if remaining <= 0:
                self.abort("connect timed out")
                raise WebSocketError("connect timed out")
            self.wait(min(remaining, 0.25))

    def fileno(self) -> int:
        return self._sock.fileno() if self._sock is not None else -1

    # ---- sending -----------------------------------------------------------------------------------

    def send_text(self, data: Union[str, Buffer], on_sent: Optional[Callable[[], None]] = None) -> None:
        payload = data.encode("utf-8") if isinstance(data, str) else bytes(data)
        if len(payload) > self.max_text_bytes:
            raise WebSocketError("text message exceeds the limit")
        self._enqueue(_Outgoing(OP_TEXT, [payload], on_sent))

    def send_binary(self, *parts: Buffer, on_sent: Optional[Callable[[], None]] = None) -> None:
        """Queues one binary message made of ``parts`` in order (they are not joined in memory)."""
        message = _Outgoing(OP_BINARY, parts, on_sent)
        if message.remaining > self.max_binary_bytes:
            raise WebSocketError("binary message exceeds the limit")
        self._enqueue(message)

    def ping(self, payload: bytes = b"") -> None:
        if len(payload) > 125:
            raise ValueError("a ping carries at most 125 bytes")
        with self._lock:
            if self.state == self.OPEN:
                self._queue_control(OP_PING, payload)
        self._wake()

    def close(self, code: int = CLOSE_NORMAL, reason: str = "") -> None:
        """Starts the close handshake. The ``closed`` event arrives from :meth:`poll` once it completes."""
        with self._lock:
            if self.state in (self.CONNECTING, self.HANDSHAKE):
                self._finish(code, reason)
            elif self.state == self.OPEN:
                # A graceful close follows the data already queued; protocol errors use _send_close instead.
                self._queue.append(_Outgoing(OP_CLOSE, [_close_payload(code, reason)], None))
                self.state = self.CLOSING
                self._deadline = self._clock() + self.close_timeout
        self._wake()

    def abort(self, reason: str = "aborted") -> None:
        """Drops the connection without a close handshake."""
        with self._lock:
            if self.state != self.CLOSED:
                self._finish(CLOSE_ABNORMAL, reason)

    @property
    def pending_bytes(self) -> int:
        """Bytes queued but not yet handed to the operating system."""
        with self._lock:
            return len(self._wbuf) + sum(m.remaining for m in self._queue) + sum(len(c) for c in self._control)

    def _enqueue(self, message: _Outgoing) -> None:
        with self._lock:
            if self.state != self.OPEN:
                raise WebSocketError("the connection is not open")
            self._queue.append(message)
        self._wake()

    def _queue_control(self, opcode: int, payload: bytes) -> None:
        mask = os.urandom(4)
        self._control.append(_frame_header(opcode, len(payload), True, mask) + mask_payload(payload, mask))

    def _send_close(self, code: Optional[int], reason: str = "") -> None:
        if self._close_sent:
            return
        self._close_sent = True
        self._queue_control(OP_CLOSE, _close_payload(code, reason))

    # ---- polling -----------------------------------------------------------------------------------

    def poll(self, budget: int = _DEFAULT_BUDGET) -> List[Event]:
        """Does a bounded amount of non-blocking work and returns the events it produced."""
        with self._lock:
            try:
                self._run_sent_callbacks()
                self._step(budget)
            except OSError as exc:
                self._finish(CLOSE_ABNORMAL, f"socket error: {exc.strerror or exc}")
            events, self._events = self._events, []
            return events

    def service(self, budget: int = _DEFAULT_BUDGET) -> None:
        """Keeps an open connection alive while the thread that polls it is busy elsewhere (Blender's main thread
        during a long bake): reads what arrived, answers pings, sends the keep-alive ping, and writes control
        frames and the rest of a frame already started. It starts no new message and runs no ``on_sent``
        callback, and the events it reads stay queued for the next :meth:`poll`, so the host still sees
        everything on its own thread. Safe to call from another thread."""
        with self._lock:
            if self.state not in (self.OPEN, self.CLOSING):
                return
            try:
                if self._queued_event_bytes() <= self.max_binary_bytes + self.max_text_bytes:
                    self._flush(budget, control_only=True)
                    if self.state != self.CLOSED and not self._drop_after_flush:
                        self._read(budget)
                if self.state == self.OPEN:
                    self._keepalive(self._clock())
                if self.state != self.CLOSED:
                    self._flush(budget, control_only=True)
                if self.state != self.CLOSED and self._drop_after_flush and not self._has_output():
                    self._finish(self.close_code or CLOSE_ABNORMAL, self.close_reason)
            except OSError as exc:
                self._finish(CLOSE_ABNORMAL, f"socket error: {exc.strerror or exc}")

    def _queued_event_bytes(self) -> int:
        """What :meth:`service` read that no :meth:`poll` has taken yet (it stops reading past a bound)."""
        return len(self._rbuf) + sum(len(event.data or b"") for event in self._events)

    def wait(self, timeout: Optional[float]) -> None:
        """Blocks until the socket is ready, another thread queued data, or ``timeout`` passes."""
        with self._lock:
            sock = self._sock
            if sock is None or self.state == self.CLOSED or self._events:
                return
            if self._wake_r is None:
                self._wake_r, self._wake_w = socket.socketpair()
                self._wake_r.setblocking(False)
                self._wake_w.setblocking(False)
            readers = [sock, self._wake_r]
            writers = [sock] if self.state == self.CONNECTING or self._has_output() else []
            wake = self._wake_r
        try:
            readable, _, _ = select.select(readers, writers, [sock], timeout)
        except (OSError, ValueError):
            return  # the socket closed underneath; the next poll reports it
        if wake in readable:
            try:
                while wake.recv(4096):
                    pass
            except (BlockingIOError, OSError):
                pass  # drained

    def receive(self, timeout: Optional[float] = None) -> Optional[Event]:
        """Blocking helper: returns the next event, or ``None`` when ``timeout`` passes first."""
        end = None if timeout is None else self._clock() + timeout
        while True:
            events = self.poll()
            if events:
                with self._lock:
                    self._events[:0] = events[1:]
                return events[0]
            if self.state == self.CLOSED:
                return None
            remaining = None if end is None else end - self._clock()
            if remaining is not None and remaining <= 0:
                return None
            self.wait(1.0 if remaining is None else min(remaining, 1.0))

    def _wake(self) -> None:
        writer = self._wake_w
        if writer is not None:
            try:
                writer.send(b"\0")
            except OSError:
                pass  # the pair is full or closed; the waiting thread wakes anyway

    def _has_output(self) -> bool:
        return bool(self._wbuf) or bool(self._control) or bool(self._queue)

    def _step(self, budget: int) -> None:
        if self.state == self.CLOSED:
            return
        now = self._clock()
        if self.state == self.CONNECTING:
            self._progress_connect(now)
            if self.state != self.HANDSHAKE:
                return
        if self.state in (self.HANDSHAKE, self.CLOSING) and now > self._deadline:
            if self.state == self.HANDSHAKE:
                self._fail_connect("handshake timed out")
            else:
                self._finish(self.close_code or CLOSE_ABNORMAL, "close handshake timed out")
            return
        written = self._flush(budget)
        if self.state != self.CLOSED and not self._drop_after_flush:
            self._read(budget)
        if self.state == self.OPEN:
            self._keepalive(self._clock())
        if self.state != self.CLOSED:
            self._flush(budget - written)  # one budget for everything written in this call
        if self.state != self.CLOSED and self._drop_after_flush and not self._has_output():
            self._finish(self.close_code or CLOSE_ABNORMAL, self.close_reason)

    def _progress_connect(self, now: float) -> None:
        sock = self._sock
        assert sock is not None
        _, writable, failed = select.select([], [sock], [sock], 0)
        if writable or failed:
            error = sock.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
            if error or failed:
                self._fail_connect(f"connect failed ({errno.errorcode.get(error, error)})")
                return
            peer = sock.getpeername()[0]
            if not ipaddress.ip_address(peer.split("%")[0]).is_loopback:
                self._fail_connect("peer is not a loopback address")
                return
            self._begin_handshake()
        elif now > self._deadline:
            self._fail_connect("connect timed out")

    def _begin_handshake(self) -> None:
        self._key = base64.b64encode(os.urandom(16))
        host = f"[{self.host}]" if ":" in self.host else self.host
        request = (
            f"GET {self.path} HTTP/1.1\r\n"
            f"Host: {host}:{self.port}\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {self._key.decode('ascii')}\r\n"
            "Sec-WebSocket-Version: 13\r\n"
            "\r\n"
        ).encode("ascii")
        self._wbuf = memoryview(request)
        self._wbuf_done = None
        self.state = self.HANDSHAKE
        self._deadline = self._clock() + self.connect_timeout

    def _fail_connect(self, reason: str) -> None:
        self._finish(CLOSE_ABNORMAL, reason)

    def _finish(self, code: Optional[int], reason: str) -> None:
        if self.state == self.CLOSED:
            return
        self.state = self.CLOSED
        self.close_code = code
        self.close_reason = reason
        for sock in (self._sock, self._wake_r, self._wake_w):
            if sock is not None:
                try:
                    sock.close()
                except OSError:
                    pass  # already gone
        self._sock = self._wake_r = self._wake_w = None
        self._queue.clear()
        self._control.clear()
        self._wbuf = memoryview(b"")
        self._rbuf = bytearray()
        self._events.append(Event("closed", code=code, reason=reason))

    # ---- writing -----------------------------------------------------------------------------------

    def _next_chunk(self) -> bool:
        """Fills the write buffer with the next control frame or data fragment. False when idle."""
        if self._control:
            self._wbuf = memoryview(self._control.popleft())
            self._wbuf_done = None
            return True
        if self.state == self.HANDSHAKE or not self._queue or self._close_sent:
            if self._close_sent:
                self._queue.clear()  # nothing may follow a close frame
            return False
        message = self._queue[0]
        if message.opcode == OP_CLOSE:
            self._queue.clear()  # nothing may follow a close frame
            self._close_sent = True
            mask = os.urandom(4)
            payload = message.take(message.remaining)
            self._wbuf = memoryview(_frame_header(OP_CLOSE, len(payload), True, mask) + mask_payload(payload, mask))
            self._wbuf_done = None
            return True
        size = message.remaining if self.fragment_bytes is None else min(message.remaining, self.fragment_bytes)
        payload = message.take(size)
        opcode = OP_CONTINUATION if message.started else message.opcode
        message.started = True
        fin = message.remaining == 0
        mask = os.urandom(4)
        self._wbuf = memoryview(_frame_header(opcode, len(payload), fin, mask) + mask_payload(payload, mask))
        self._wbuf_done = None
        if fin:
            self._queue.popleft()
            self._wbuf_done = message.on_sent
        return True

    def _flush(self, budget: int, control_only: bool = False) -> int:
        """Writes up to ``budget`` bytes; returns how many were written. ``control_only`` (:meth:`service`) finishes
        the frame in progress but starts control frames only, and keeps a finished message's ``on_sent`` for the
        next :meth:`poll`."""
        sock = self._sock
        written = 0
        while written < budget and sock is not None and self.state != self.CLOSED:
            if not self._wbuf:
                if control_only:
                    if not self._control:
                        return written
                    self._wbuf = memoryview(self._control.popleft())
                    self._wbuf_done = None
                elif not self._next_chunk():
                    return written
            try:
                sent = sock.send(self._wbuf[: budget - written])
            except (BlockingIOError, InterruptedError):
                return written
            written += sent
            self._wbuf = self._wbuf[sent:]
            if not self._wbuf and self._wbuf_done is not None:
                done, self._wbuf_done = self._wbuf_done, None
                if control_only:
                    self._sent_later.append(done)
                else:
                    done()
        return written

    def _run_sent_callbacks(self) -> None:
        """The ``on_sent`` callbacks of messages :meth:`service` finished writing, on the polling thread."""
        while self._sent_later:
            self._sent_later.pop(0)()

    # ---- reading -----------------------------------------------------------------------------------

    def _read(self, budget: int) -> None:
        sock = self._sock
        while budget > 0 and sock is not None and self.state != self.CLOSED:
            try:
                data = sock.recv(min(budget, 1 << 20))
            except (BlockingIOError, InterruptedError):
                break
            if not data:
                if self._close_received:
                    self._finish(self.close_code, self.close_reason)  # the peer closed after its close frame
                else:
                    self._finish(CLOSE_ABNORMAL, "the connection closed without a close frame")
                return
            budget -= len(data)
            self._last_received = self._clock()
            self._rbuf += data
            if self.state == self.HANDSHAKE:
                self._parse_handshake()
            if self.state in (self.OPEN, self.CLOSING):
                self._parse_frames()
            if self._drop_after_flush:
                return  # a close frame or a protocol error ends reading; the close goes out next
            sock = self._sock

    def _parse_handshake(self) -> None:
        end = self._rbuf.find(b"\r\n\r\n")
        if end < 0:
            if len(self._rbuf) > _MAX_HANDSHAKE_BYTES:
                self._fail_connect("handshake response too large")
            return
        head = bytes(self._rbuf[:end]).decode("latin-1")
        del self._rbuf[: end + 4]
        lines = head.split("\r\n")
        status = lines[0].split(" ", 2)
        if len(status) < 2 or not status[0].startswith("HTTP/1.") or status[1] != "101":
            self._fail_connect(f"server answered {lines[0][:64]!r} instead of upgrading")
            return
        headers = {}
        for line in lines[1:]:
            name, sep, value = line.partition(":")
            if not sep:
                self._fail_connect("malformed handshake header")
                return
            headers[name.strip().lower()] = value.strip()
        expected = base64.b64encode(hashlib.sha1(self._key + _ACCEPT_GUID).digest()).decode("ascii")
        connection = {token.strip().lower() for token in headers.get("connection", "").split(",")}
        if (
            headers.get("upgrade", "").lower() != "websocket"
            or "upgrade" not in connection
            or headers.get("sec-websocket-accept") != expected
        ):
            self._fail_connect("invalid upgrade response")
            return
        if headers.get("sec-websocket-extensions") or headers.get("sec-websocket-protocol"):
            self._fail_connect("the server negotiated an extension or subprotocol nobody asked for")
            return
        self.state = self.OPEN
        now = self._clock()
        self._last_received = self._last_ping = now
        self._events.append(Event("open"))

    def _protocol_error(self, code: int, reason: str) -> None:
        self.close_code, self.close_reason = code, reason
        if not self._close_sent:
            self._send_close(code, reason)
        self._drop_after_flush = True
        self.state = self.CLOSING
        self._deadline = self._clock() + self.close_timeout
        self._rbuf = bytearray()

    def _parse_frames(self) -> None:
        buf = self._rbuf
        while not self._drop_after_flush and self.state != self.CLOSED:
            if len(buf) < 2:
                return
            first, second = buf[0], buf[1]
            fin, opcode, length = first & 0x80, first & 0x0F, second & 0x7F
            offset = 2
            if first & 0x70:
                return self._protocol_error(CLOSE_PROTOCOL_ERROR, "reserved bits set")
            if second & 0x80:
                return self._protocol_error(CLOSE_PROTOCOL_ERROR, "a server frame was masked")
            if length == 126:
                if len(buf) < 4:
                    return
                length, offset = int.from_bytes(buf[2:4], "big"), 4
                if length < 126:
                    return self._protocol_error(CLOSE_PROTOCOL_ERROR, "non-minimal length")
            elif length == 127:
                if len(buf) < 10:
                    return
                length, offset = int.from_bytes(buf[2:10], "big"), 10
                if length >> 63 or length < 65536:
                    return self._protocol_error(CLOSE_PROTOCOL_ERROR, "invalid length")
            if opcode >= 0x8:
                if opcode not in (OP_CLOSE, OP_PING, OP_PONG):
                    return self._protocol_error(CLOSE_PROTOCOL_ERROR, "unknown control opcode")
                if not fin or length > 125:
                    return self._protocol_error(CLOSE_PROTOCOL_ERROR, "invalid control frame")
            else:
                if opcode not in (OP_CONTINUATION, OP_TEXT, OP_BINARY):
                    return self._protocol_error(CLOSE_PROTOCOL_ERROR, "unknown data opcode")
                if opcode == OP_CONTINUATION and self._message_opcode is None:
                    return self._protocol_error(CLOSE_PROTOCOL_ERROR, "continuation without a message")
                if opcode != OP_CONTINUATION and self._message_opcode is not None:
                    return self._protocol_error(CLOSE_PROTOCOL_ERROR, "a new message interrupted a fragmented one")
                message_opcode = self._message_opcode if opcode == OP_CONTINUATION else opcode
                limit = self.max_text_bytes if message_opcode == OP_TEXT else self.max_binary_bytes
                if self._message_size + length > limit:
                    return self._protocol_error(CLOSE_TOO_BIG, "message too large")
            if len(buf) < offset + length:
                return
            payload = bytes(buf[offset : offset + length])
            del buf[: offset + length]
            if opcode >= 0x8:
                self._control_frame(opcode, payload)
            else:
                self._data_frame(opcode, bool(fin), payload)

    def _data_frame(self, opcode: int, fin: bool, payload: bytes) -> None:
        if opcode != OP_CONTINUATION:
            self._message_opcode = opcode
        self._message_parts.append(payload)
        self._message_size += len(payload)
        if not fin:
            return
        data = self._message_parts[0] if len(self._message_parts) == 1 else b"".join(self._message_parts)
        message_opcode = self._message_opcode
        self._message_opcode, self._message_parts, self._message_size = None, [], 0
        if self._close_received:
            return
        if message_opcode == OP_TEXT:
            try:
                data.decode("utf-8")
            except UnicodeDecodeError:
                return self._protocol_error(CLOSE_INVALID_DATA, "text message is not UTF-8")
            self._events.append(Event("text", data))
        else:
            self._events.append(Event("binary", data))

    def _control_frame(self, opcode: int, payload: bytes) -> None:
        if opcode == OP_PING:
            if not self._close_sent:
                self._queue_control(OP_PONG, payload)
        elif opcode == OP_PONG:
            self._events.append(Event("pong", payload))
        else:
            code: Optional[int] = None
            reason = ""
            if len(payload) == 1:
                return self._protocol_error(CLOSE_PROTOCOL_ERROR, "one-byte close payload")
            if len(payload) >= 2:
                code = int.from_bytes(payload[:2], "big")
                if not _valid_close_code(code):
                    return self._protocol_error(CLOSE_PROTOCOL_ERROR, "invalid close code")
                try:
                    reason = payload[2:].decode("utf-8")
                except UnicodeDecodeError:
                    return self._protocol_error(CLOSE_INVALID_DATA, "close reason is not UTF-8")
            self._close_received = True
            self.close_code = code if code is not None else CLOSE_NO_STATUS
            self.close_reason = reason
            if not self._close_sent:
                self._send_close(code)
            self._drop_after_flush = True
            self.state = self.CLOSING
            self._deadline = self._clock() + self.close_timeout

    def _keepalive(self, now: float) -> None:
        if self.keepalive_timeout and now - self._last_received > self.keepalive_timeout:
            self._finish(CLOSE_ABNORMAL, "the peer stopped answering")
            return
        if self.keepalive_interval and now - self._last_ping >= self.keepalive_interval:
            self._last_ping = now
            self._queue_control(OP_PING, b"")
