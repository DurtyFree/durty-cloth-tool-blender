# SPDX-License-Identifier: MIT
# Copyright (c) Schmid Software Solutions (https://schmid-software.de)
"""gta.clothing sign-in for Creator Link plugins.

* Device sign-in (OAuth 2.0 Device Authorization Grant): :meth:`LinkAuth.start_device_sign_in` returns a
  :class:`DeviceFlow`; :meth:`DeviceFlow.poll` asks the token route no more often than ``interval`` (plus
  five seconds after every ``slow_down``) and returns the access token once the user approved it.
* Refresh with rotation: every refresh returns a new refresh token, which is stored before the access token
  is used. Refreshes are serialized inside the process (one network call however many threads ask) and
  across processes with a lock file, so two copies of a host never spend the same refresh token.
* Sign-in assertions: :meth:`LinkAuth.mint_assertion` trades the access token for a short-lived assertion
  bound to one DCT connection (its ``serverNonce``). Only the assertion goes to DCT; access and refresh tokens
  never leave the plugin except to gta.clothing.
* Every request carries ``X-DCT-Link-Client: <kind>/<version> (protocol <major>.<minor>; channel <channel>)``
  and goes to ``https://gta.clothing`` only (see :func:`check_base_url`).

Every operation exists twice. The plain methods (``mint_assertion``, ``access_token``, ``start_device_sign_in``,
``logout``) block the calling thread for each HTTP request, bounded by ``timeout``. The ``begin_*`` methods return
an :class:`AuthTask` that a host timer polls; :meth:`AuthTask.poll` never blocks. By default the task's steps
run on a short-lived worker thread that only talks to gta.clothing and the secret store (never to host APIs).
With ``worker_threads=False`` no thread is used: requests run on non-blocking sockets driven by ``poll`` (name
resolution, once per request, is then the only call that may wait). Both forms run the same steps.

After :meth:`LinkAuth.logout` the account stays signed out (``signed_out_by_user``) until the user signs in
again or calls :meth:`LinkAuth.allow_sign_in`, so a host that connects automatically does not start a device
sign-in on its own.

Tokens, codes and account ids are never logged.
"""

from __future__ import annotations

import base64
import http.client
import json
import logging
import os
import pathlib
import re
import select
import socket
import ssl
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Callable, Dict, Generator, NamedTuple, Optional, Tuple, Union

from . import protocol

__all__ = [
    "BASE_URL",
    "AuthError",
    "SignInRequired",
    "AccountBlocked",
    "PluginUpdateRequired",
    "ClientInfo",
    "DeviceFlow",
    "LinkAuth",
    "LogoutResult",
    "AuthTask",
    "FileLock",
    "HttpClient",
    "HttpJob",
    "check_base_url",
    "client_header",
]

BASE_URL = "https://gta.clothing"
_log = logging.getLogger(__name__)
_MAX_RESPONSE_BYTES = 256 * 1024
_REFRESH_MARGIN_SECONDS = 60
Response = Tuple[int, Dict[str, str], bytes]

_FRIENDLY = {
    "account_locked": "This account is locked and cannot use Creator Link.",
    "discord_membership_required": "Join the Pleb Masters Community Discord server to use Creator Link.",
    "plugin_update_required": "Update the plugin to keep using Creator Link.",
}


class AuthError(Exception):
    """A sign-in failure. ``code`` is the server's ``error``/``failureCode`` (or a local code such as
    ``network`` or ``invalid-response``); ``retryable`` says whether trying again later can help."""

    def __init__(self, code: str, message: str = "", *, status: int = 0, retryable: bool = False,
                 min_version: Optional[str] = None, retry_after: Optional[float] = None) -> None:
        super().__init__(f"{code}: {message}" if message else code)
        self.code = code
        self.message = message
        self.status = status
        self.retryable = retryable
        self.min_version = min_version
        self.retry_after = retry_after


class LogoutResult(NamedTuple):
    """What :meth:`LinkAuth.logout` achieved. The local sign-out is remembered in every case.

    ``had_session`` is false when nothing was stored (nothing to end on the server). ``reached`` is true when
    gta.clothing answered the logout request: the session is ended there (or was no longer valid). It is false
    when the request did not get through (network trouble, a timeout, ``429`` or a server error); the session
    then ends on its own when it expires, or the user ends it on their gta.clothing account page.
    """

    had_session: bool
    reached: bool

    @property
    def ended_on_server(self) -> bool:
        """True unless a stored session could not be ended on gta.clothing (show a hint then)."""
        return self.reached or not self.had_session


class SignInRequired(AuthError):
    """The session or device code is gone (expired, revoked, denied): sign in again."""


class AccountBlocked(AuthError):
    """``account_locked`` or ``discord_membership_required``: show ``message`` to the user; retrying does not
    help. Discord membership means the Pleb Masters Community Discord server."""


class PluginUpdateRequired(AuthError):
    """HTTP 426: the plugin is below the server's minimum version (``min_version``)."""


class ClientInfo(NamedTuple):
    kind: str
    plugin_version: str
    host_version: str
    channel: str
    install_id: str
    device_name: Optional[str] = None

    @property
    def client_id(self) -> str:
        return f"dct-link-{self.kind}"


def client_header(info: ClientInfo) -> str:
    """The ``X-DCT-Link-Client`` value."""
    return (
        f"{info.kind}/{info.plugin_version} "
        f"(protocol {protocol.PROTOCOL_MAJOR}.{protocol.PROTOCOL_MINOR}; channel {info.channel})"
    )


def _is_loopback_host(host: Optional[str]) -> bool:
    if not host:
        return False
    if host.lower() == "localhost":
        return True
    import ipaddress

    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def check_base_url(url: str) -> str:
    """Allows ``https://gta.clothing`` and, for tests only, a loopback ``http(s)://127.0.0.1:port``."""
    url = url.rstrip("/")
    if url == BASE_URL:
        return url
    parsed = urllib.parse.urlsplit(url)
    if (
        parsed.scheme in ("http", "https")
        and _is_loopback_host(parsed.hostname)
        and not parsed.path
        and not parsed.query
        and "@" not in parsed.netloc
    ):
        return url
    raise ValueError("Creator Link talks to https://gta.clothing only")


def _read_limited(response: Any, limit: int) -> bytes:
    data = response.read(limit + 1)
    if len(data) > limit:
        raise AuthError("invalid-response", "response too large", retryable=True)
    return data


def _json_body(payload: bytes) -> Dict[str, Any]:
    if not payload:
        return {}
    try:
        value = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, ValueError, RecursionError):
        return {}
    return value if isinstance(value, dict) else {}


def _failure(status: int, headers: Dict[str, str], body: Dict[str, Any]) -> AuthError:
    """Maps a failure answer (``failureCode``, plus the RFC 8628 ``error`` on the token route) to an exception."""
    code = body.get("error") if isinstance(body.get("error"), str) else body.get("failureCode")
    code = code if isinstance(code, str) and re.fullmatch(r"[a-z_]{1,64}", code) else f"http_{status}"
    retry_after = None
    try:
        retry_after = float(headers.get("retry-after", ""))
    except ValueError:
        pass  # absent or a date: use the default backoff
    if status == 426 or code == "plugin_update_required":
        minimum = body.get("minVersion")
        return PluginUpdateRequired(code, _FRIENDLY["plugin_update_required"], status=status,
                                    min_version=minimum if protocol.is_semver(minimum) else None)
    if code in ("account_locked", "discord_membership_required"):
        return AccountBlocked(code, _FRIENDLY[code], status=status)
    if code in ("expired_token", "access_denied", "invalid_grant", "session_invalid", "session_expired", "session_revoked"):
        return SignInRequired(code, "sign in again", status=status)
    retryable = bool(body.get("retryable")) or status in (409, 429) or status >= 500
    return AuthError(code, "gta.clothing refused the request", status=status, retryable=retryable, retry_after=retry_after)


# ---- HTTP: blocking (urllib) and non-blocking (HttpJob) ----------------------------------------------------


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: D401 - urllib hook
        return None  # a redirect is answered as the 3xx error it is; tokens never follow it elsewhere


class HttpClient:
    """JSON requests with a fixed base URL, no redirects, bounded responses and the client header."""

    def __init__(self, info: ClientInfo, base_url: str = BASE_URL, *, timeout: float = 15.0,
                 ssl_context: Optional[ssl.SSLContext] = None) -> None:
        self.info = info
        self.base_url = check_base_url(base_url)
        self.timeout = timeout
        self.loopback = _is_loopback_host(urllib.parse.urlsplit(self.base_url).hostname)
        self.ssl_context = ssl_context or (ssl.create_default_context() if self.base_url.startswith("https://") else None)
        handlers: list = [_NoRedirect()]
        if self.loopback:
            handlers.append(urllib.request.ProxyHandler({}))  # a test server is never behind a proxy
        if self.ssl_context is not None:
            handlers.append(urllib.request.HTTPSHandler(context=self.ssl_context))
        self._opener = urllib.request.build_opener(*handlers)

    def url(self, path: str) -> str:
        if not path.startswith("/") or ".." in path or "//" in path:
            raise ValueError("invalid API path")
        return self.base_url + path

    def _headers(self, body: Optional[Dict[str, Any]], bearer: Optional[str], accept: str) -> Tuple[Dict[str, str], Optional[bytes]]:
        data = None
        headers = {"Accept": accept, "X-DCT-Link-Client": client_header(self.info), "User-Agent": client_header(self.info)}
        if body is not None:
            data = json.dumps(body, separators=(",", ":")).encode("utf-8")
            if len(data) > 4096:
                raise ValueError("request body too large")
            headers["Content-Type"] = "application/json"
        if bearer is not None:
            headers["Authorization"] = "Bearer " + bearer
        return headers, data

    def request(self, method: str, path: str, body: Optional[Dict[str, Any]] = None, *, bearer: Optional[str] = None,
                accept: str = "application/json", max_bytes: int = _MAX_RESPONSE_BYTES) -> Response:
        """One blocking request. Network trouble raises a retryable :class:`AuthError` (``network``)."""
        headers, data = self._headers(body, bearer, accept)
        request = urllib.request.Request(self.url(path), data=data, headers=headers, method=method)
        try:
            with self._opener.open(request, timeout=self.timeout) as response:
                return response.status, {k.lower(): v for k, v in response.headers.items()}, _read_limited(response, max_bytes)
        except urllib.error.HTTPError as error:
            try:
                payload = _read_limited(error, max_bytes)
            except (OSError, AuthError, http.client.HTTPException):
                payload = b""
            return error.code, {k.lower(): v for k, v in (error.headers or {}).items()}, payload
        except (urllib.error.URLError, OSError, ValueError, http.client.HTTPException) as exc:
            raise AuthError("network", "gta.clothing could not be reached", retryable=True) from exc

    def start(self, method: str, path: str, body: Optional[Dict[str, Any]] = None, *, bearer: Optional[str] = None,
              accept: str = "application/json", max_bytes: int = _MAX_RESPONSE_BYTES) -> "HttpJob":
        """The same request as :meth:`request`, as a non-blocking :class:`HttpJob`."""
        headers, data = self._headers(body, bearer, accept)
        proxy = None
        if not self.loopback:
            host = urllib.parse.urlsplit(self.base_url).hostname or ""
            candidate = urllib.request.getproxies().get(urllib.parse.urlsplit(self.base_url).scheme)
            if candidate and not urllib.request.proxy_bypass(host):
                proxy = candidate
        return HttpJob(method, self.url(path), headers, data, timeout=self.timeout, ssl_context=self.ssl_context,
                       max_bytes=max_bytes, proxy=proxy)


#: How long :class:`HttpJob` waits for one resolved address to accept the connection before it tries the next one.
CONNECT_BUDGET_SECONDS = 2.0


class HttpJob:
    """One HTTP/1.1 request on a non-blocking socket. :meth:`poll` advances it without waiting and returns True
    once :meth:`result` is ready. TLS uses the given context (certificates and host names are verified), and an
    ``http://`` proxy from the system settings is used through ``CONNECT``."""

    def __init__(self, method: str, url: str, headers: Dict[str, str], body: Optional[bytes], *, timeout: float,
                 ssl_context: Optional[ssl.SSLContext], max_bytes: int = _MAX_RESPONSE_BYTES,
                 proxy: Optional[str] = None, clock: Callable[[], float] = time.monotonic) -> None:
        parts = urllib.parse.urlsplit(url)
        if parts.scheme not in ("http", "https") or not parts.hostname:
            raise ValueError("unsupported URL")
        self.tls = parts.scheme == "https"
        self.host = parts.hostname
        self.port = parts.port or (443 if self.tls else 80)
        self.ssl_context = ssl_context
        self.max_bytes = max_bytes
        self.method = method
        self._clock = clock
        self._deadline = clock() + timeout
        self._proxy = urllib.parse.urlsplit(proxy) if proxy else None
        if self._proxy is not None and (self._proxy.scheme != "http" or not self._proxy.hostname):
            self._proxy = None  # only plain HTTP proxies are supported here
        target = (parts.path or "/") + (f"?{parts.query}" if parts.query else "")
        host_header = self.host if parts.port is None else f"{self.host}:{self.port}"
        lines = [f"{method} {target} HTTP/1.1", f"Host: {host_header}", "Connection: close", "Accept-Encoding: identity"]
        lines += [f"{name}: {value}" for name, value in headers.items()]
        if body is not None or method in ("POST", "PUT"):
            lines.append(f"Content-Length: {len(body or b'')}")
        self._request = ("\r\n".join(lines) + "\r\n\r\n").encode("latin-1") + (body or b"")
        self._state = "resolve"
        self._addresses: list = []
        self._connect_deadline = 0.0
        self._sock: Any = None
        self._out = memoryview(b"")
        self._in = bytearray()
        self._status = 0
        self._headers: Dict[str, str] = {}
        self._body = bytearray()
        self._chunk_left: Optional[int] = None
        self._result: Optional[Response] = None
        self._error: Optional[AuthError] = None

    @property
    def done(self) -> bool:
        return self._result is not None or self._error is not None

    def result(self) -> Response:
        if self._error is not None:
            raise self._error
        if self._result is None:
            raise RuntimeError("the request is still running")
        return self._result

    def close(self) -> None:
        if self._sock is not None:
            try:
                self._sock.close()
            except OSError:
                pass  # already closed
            self._sock = None

    def _fail(self, error: AuthError) -> bool:
        self._error = error
        self.close()
        return True

    def poll(self) -> bool:
        if self.done:
            return True
        if self._clock() > self._deadline:
            return self._fail(AuthError("network", "gta.clothing did not answer in time", retryable=True))
        try:
            return self._step()
        except AuthError as exc:
            return self._fail(exc)
        except ssl.SSLCertVerificationError as exc:
            return self._fail(AuthError("tls", "the gta.clothing certificate could not be verified"))
        except (OSError, ValueError, UnicodeError, http.client.HTTPException) as exc:
            return self._fail(AuthError("network", f"gta.clothing could not be reached ({type(exc).__name__})", retryable=True))

    # The states run in order; each returns False while it waits for the socket.
    def _step(self) -> bool:
        if self._state == "resolve":
            host, port = (self._proxy.hostname, self._proxy.port or 80) if self._proxy else (self.host, self.port)
            self._addresses = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
            self._state = "connect-next"
        if self._state == "connect-next":
            if not self._addresses:
                raise AuthError("network", "gta.clothing could not be reached", retryable=True)
            family, kind, proto, _, address = self._addresses.pop(0)
            self.close()
            self._sock = socket.socket(family, kind, proto)
            self._sock.setblocking(False)
            self._sock.connect_ex(address)
            self._connect_deadline = self._clock() + CONNECT_BUDGET_SECONDS
            self._state = "connecting"
        if self._state == "connecting":
            _, writable, failed = select.select([], [self._sock], [self._sock], 0)
            if not writable and not failed:
                if self._addresses and self._clock() > self._connect_deadline:
                    self._state = "connect-next"  # an address that does not answer (an unrouted IPv6 one): next
                    return self._step()
                return False
            if failed or self._sock.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR):
                self._state = "connect-next"
                return self._step()
            if self._proxy is not None and self.tls:
                self._out = memoryview(f"CONNECT {self.host}:{self.port} HTTP/1.1\r\nHost: {self.host}:{self.port}\r\n\r\n".encode("latin-1"))
                self._state = "proxy-send"
            else:
                self._state = "tls-start" if self.tls else "send-start"
        if self._state == "proxy-send":
            if not self._send_pending():
                return False
            self._state = "proxy-recv"
        if self._state == "proxy-recv":
            if not self._recv_into_buffer() and b"\r\n\r\n" not in self._in:
                return False
            if b"\r\n\r\n" not in self._in:
                return False
            head, _, rest = bytes(self._in).partition(b"\r\n\r\n")
            if not re.match(rb"HTTP/1\.[01] 200", head):
                raise AuthError("network", "the proxy refused the connection", retryable=True)
            self._in = bytearray(rest)
            self._state = "tls-start"
        if self._state == "tls-start":
            assert self.ssl_context is not None
            self._sock = self.ssl_context.wrap_socket(self._sock, server_hostname=self.host, do_handshake_on_connect=False)
            self._state = "tls"
        if self._state == "tls":
            try:
                self._sock.do_handshake()
            except (ssl.SSLWantReadError, ssl.SSLWantWriteError):
                return False
            self._state = "send-start"
        if self._state == "send-start":
            self._out = memoryview(self._request)
            self._in = bytearray()
            self._state = "send"
        if self._state == "send":
            if not self._send_pending():
                return False
            self._state = "head"
        if self._state in ("head", "body"):
            eof = self._recv_into_buffer()
            if self._state == "head" and not self._parse_head(eof):
                return False
            return self._parse_body(eof)
        return False

    def _send_pending(self) -> bool:
        while self._out:
            try:
                sent = self._sock.send(self._out)
            except (BlockingIOError, InterruptedError, ssl.SSLWantWriteError, ssl.SSLWantReadError):
                return False
            self._out = self._out[sent:]
        return True

    def _recv_into_buffer(self) -> bool:
        """Reads what is available; True when the server closed the connection."""
        while True:
            try:
                data = self._sock.recv(65536)
            except (BlockingIOError, InterruptedError, ssl.SSLWantReadError, ssl.SSLWantWriteError):
                return False
            except (ssl.SSLZeroReturnError, ssl.SSLEOFError):
                return True
            if not data:
                return True
            self._in += data
            if len(self._in) > self.max_bytes + 65536:
                raise AuthError("invalid-response", "response too large", retryable=True)

    def _parse_head(self, eof: bool) -> bool:
        while True:
            end = self._in.find(b"\r\n\r\n")
            if end < 0:
                if eof:
                    raise AuthError("network", "the connection closed early", retryable=True)
                if len(self._in) > 65536:
                    raise AuthError("invalid-response", "response headers too large", retryable=True)
                return False
            head = bytes(self._in[:end]).decode("latin-1").split("\r\n")
            del self._in[: end + 4]
            status = re.match(r"HTTP/1\.[01] ([0-9]{3})", head[0])
            if status is None:
                raise AuthError("invalid-response", "not an HTTP response", retryable=True)
            code = int(status.group(1))
            if 100 <= code < 200:
                continue  # an interim answer; the real one follows
            self._status = code
            for line in head[1:]:
                name, sep, value = line.partition(":")
                if sep:
                    self._headers[name.strip().lower()] = value.strip()
            self._state = "body"
            if "chunked" in self._headers.get("transfer-encoding", "").lower():
                self._chunk_left = -1
            return True

    def _parse_body(self, eof: bool) -> bool:
        if self.method == "HEAD" or self._status in (204, 304):
            return self._finish()
        if self._chunk_left is not None:
            while True:
                if self._chunk_left == -1:  # expecting a size line
                    line_end = self._in.find(b"\r\n")
                    if line_end < 0:
                        break
                    size = int(bytes(self._in[:line_end]).split(b";")[0].strip() or b"0", 16)
                    del self._in[: line_end + 2]
                    if size == 0:
                        return self._finish()
                    self._chunk_left = size
                if len(self._in) < self._chunk_left + 2:
                    break
                self._body += self._in[: self._chunk_left]
                del self._in[: self._chunk_left + 2]
                self._chunk_left = -1
                self._check_size()
            if eof:
                raise AuthError("network", "the connection closed inside a chunked body", retryable=True)
            return False
        self._body += self._in
        self._in = bytearray()
        self._check_size()
        length = self._headers.get("content-length")
        if length is not None and length.isdigit():
            if len(self._body) >= int(length):
                del self._body[int(length):]
                return self._finish()
            if eof:
                raise AuthError("network", "the connection closed early", retryable=True)
            return False
        return self._finish() if eof else False

    def _check_size(self) -> None:
        if len(self._body) > self.max_bytes:
            raise AuthError("invalid-response", "response too large", retryable=True)

    def _finish(self) -> bool:
        self._result = (self._status, dict(self._headers), bytes(self._body))
        self.close()
        return True


# ---- locking ------------------------------------------------------------------------------------------


class FileLock:
    """An exclusive lock on a file, shared by every process on the machine (msvcrt or fcntl)."""

    def __init__(self, path: Union[str, os.PathLike], timeout: float = 30.0, poll: float = 0.05) -> None:
        self.path = pathlib.Path(path)
        self.timeout = timeout
        self.poll = poll
        self._handle: Any = None

    def try_acquire(self) -> bool:
        """One attempt that never waits."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        handle = open(self.path, "a+b")
        try:
            if os.name == "nt":
                import msvcrt

                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            handle.close()
            return False
        self._handle = handle
        return True

    def acquire(self) -> None:
        deadline = time.monotonic() + self.timeout
        while not self.try_acquire():
            if time.monotonic() >= deadline:
                raise AuthError("refresh_in_progress", "another process holds the sign-in lock", retryable=True)
            time.sleep(self.poll)

    def release(self) -> None:
        handle, self._handle = self._handle, None
        if handle is None:
            return
        try:
            if os.name == "nt":
                import msvcrt

                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        finally:
            handle.close()

    def __enter__(self) -> "FileLock":
        self.acquire()
        return self

    def __exit__(self, *exc: Any) -> None:
        self.release()


# ---- steps and their drivers ------------------------------------------------------------------------------


class _Call(NamedTuple):
    """Step: one HTTP request; the step receives ``(status, headers, payload)`` or an :class:`AuthError`."""

    method: str
    path: str
    body: Optional[Dict[str, Any]] = None
    bearer: Optional[str] = None


class _Sleep(NamedTuple):
    seconds: float


_ACQUIRE = "acquire-refresh-lock"
_RELEASE = "release-refresh-lock"
Steps = Generator[Any, Any, Any]


class AuthTask:
    """A sign-in operation that never blocks its caller. Call :meth:`poll` until it returns True, then
    :meth:`result` returns the value or raises the :class:`AuthError`. :meth:`cancel` abandons it."""

    def __init__(self, auth: "LinkAuth", steps: Steps, lock_timeout: float = 5.0, threaded: bool = True) -> None:
        self._threaded = threaded
        self._finished: Optional[threading.Event] = None
        if threaded:
            self._finished = threading.Event()
            self.done = False
            self._value: Any = None
            self._error: Optional[BaseException] = None
            self._cancelled = False

            def work() -> None:
                try:
                    value = auth._run(steps)
                    error = None
                except BaseException as exc:  # handed to whoever polls the task
                    value, error = None, exc
                if not self._cancelled:
                    self._value, self._error = value, error
                self._finished.set()

            threading.Thread(target=work, name="dct-link-sign-in", daemon=True).start()
            return
        self._auth = auth
        self._steps = steps
        self._job: Optional[HttpJob] = None
        self._sleep_until: Optional[float] = None
        self._lock_deadline: Optional[float] = None
        self._lock: Optional[FileLock] = None
        self._lock_timeout = lock_timeout
        self._send: Any = None
        self._throw: Optional[BaseException] = None
        self._value: Any = None
        self._error: Optional[BaseException] = None
        self.done = False

    def poll(self) -> bool:
        if self.done:
            return True
        if self._finished is not None:
            if self._finished.is_set():
                self.done = True
            return self.done
        try:
            return self._advance()
        except Exception as exc:  # the steps raised: the task failed
            self._end(error=exc)
            return True

    def _advance(self) -> bool:
        while True:
            if self._job is not None:
                if not self._job.poll():
                    return False
                try:
                    self._send = self._job.result()
                except AuthError as exc:
                    self._throw = exc
                self._job = None
            if self._sleep_until is not None:
                if time.monotonic() < self._sleep_until:
                    return False
                self._sleep_until = None
            if self._lock_deadline is not None:
                if not self._try_lock():
                    if time.monotonic() < self._lock_deadline:
                        return False
                    self._throw = AuthError("refresh_in_progress", "the sign-in lock is busy", retryable=True)
                self._lock_deadline = None
            try:
                if self._throw is not None:
                    error, self._throw = self._throw, None
                    step = self._steps.throw(error)
                else:
                    value, self._send = self._send, None
                    step = self._steps.send(value)
            except StopIteration as stop:
                self._end(value=stop.value)
                return True
            if isinstance(step, _Call):
                self._job = self._auth.http.start(step.method, step.path, step.body, bearer=step.bearer)
            elif isinstance(step, _Sleep):
                self._sleep_until = time.monotonic() + step.seconds
            elif step == _ACQUIRE:
                self._lock_deadline = time.monotonic() + self._lock_timeout
            elif step == _RELEASE:
                self._release_lock()

    def _try_lock(self) -> bool:
        if not self._auth._refresh_lock.acquire(blocking=False):
            return False
        lock = FileLock(self._auth.lock_path)
        if not lock.try_acquire():
            self._auth._refresh_lock.release()
            return False
        self._lock = lock
        return True

    def _release_lock(self) -> None:
        if self._lock is not None:
            lock, self._lock = self._lock, None
            lock.release()
            self._auth._refresh_lock.release()

    def _end(self, value: Any = None, error: Optional[BaseException] = None) -> None:
        self._release_lock()
        if self._job is not None:
            self._job.close()
            self._job = None
        self._value, self._error, self.done = value, error, True

    def result(self) -> Any:
        if not self.done:
            raise RuntimeError("the task has not finished")
        if self._error is not None:
            raise self._error
        return self._value

    def cancel(self) -> None:
        if self.done:
            return
        if self._finished is not None:
            self._cancelled = True  # the worker finishes its request; nobody uses the result
            self._value, self._error, self.done = None, AuthError("cancelled", "the sign-in step was cancelled"), True
            return
        self._steps.close()
        self._end(error=AuthError("cancelled", "the sign-in step was cancelled"))


# ---- device sign-in ---------------------------------------------------------------------------------------


class DeviceFlow:
    """A device sign-in waiting for approval (in the browser or by DCT through ``account.assist``).

    :attr:`access_token` is set by :meth:`poll` on the thread that polls, in the same call that returns the token.
    Until then the flow is :attr:`active`, even when a worker already received and stored the approved tokens: a
    host that checks ``active`` (or ``access_token is None``) keeps polling until it consumed the result.
    """

    def __init__(self, auth: "LinkAuth", body: Dict[str, Any], nonblocking: bool = False) -> None:
        device_code = body.get("deviceCode")
        user_code = body.get("userCode")
        normalized = user_code.replace("-", "").upper() if isinstance(user_code, str) else ""
        uri, complete = body.get("verificationUri"), body.get("verificationUriComplete")
        expires, interval = body.get("expiresIn", 600), body.get("interval", 5)
        if not isinstance(device_code, str) or not re.fullmatch(r"[A-Za-z0-9_-]{16,512}", device_code):
            raise AuthError("invalid-response", "no device code", retryable=True)
        if not protocol.is_user_code(normalized):
            raise AuthError("invalid-response", "the user code is not a sign-in code", retryable=True)
        if not auth._browser_url_ok(uri) or (complete is not None and not auth._browser_url_ok(complete)):
            raise AuthError("invalid-response", "the verification link is not a gta.clothing link", retryable=True)
        self._auth = auth
        self._device_code = device_code
        self.nonblocking = nonblocking
        self.user_code = normalized
        self.display_code = normalized[:4] + "-" + normalized[4:]
        self.verification_uri: str = uri
        self.verification_uri_complete: Optional[str] = complete
        self.interval = float(interval if type(interval) is int and 1 <= interval <= 60 else 5)
        self.expires_at = auth._clock() + (expires if type(expires) is int and 1 <= expires <= 3600 else 600)
        self._next_poll = auth._clock() + self.interval
        self._task: Optional[AuthTask] = None
        self.cancelled = False
        self.access_token: Optional[str] = None

    @property
    def active(self) -> bool:
        """True while the sign-in is still to be finished by :meth:`poll`: not cancelled, not expired, and the
        token not yet handed over (an approval that a worker stored but :meth:`poll` has not returned counts)."""
        return not self.cancelled and self.access_token is None and self._auth._clock() < self.expires_at

    def cancel(self) -> None:
        """Stops polling. The code expires on the server by itself."""
        self.cancelled = True
        if self._task is not None:
            self._task.cancel()

    def _token_steps(self, now: float) -> Steps:
        body = {"grantType": "device_code", "deviceCode": self._device_code, "clientId": self._auth.info.client_id}
        response = yield _Call("POST", "/link/api/auth/token", body)
        return self._handle(response, now)  # stores approved tokens here, on the worker when there is one

    def poll(self) -> Optional[str]:
        """Returns the access token once approved, ``None`` while pending (or before the next poll is due).

        Raises :class:`SignInRequired` when the code expired or was denied, :class:`AccountBlocked` and
        :class:`PluginUpdateRequired` as the server says. Network trouble only delays the next poll. A flow from
        :meth:`LinkAuth.begin_device_sign_in` never blocks on the network.
        """
        if self.access_token is not None:
            return self.access_token
        if self.cancelled:
            raise AuthError("cancelled", "the sign-in was cancelled")
        now = self._auth._clock()
        if now >= self.expires_at:
            raise SignInRequired("expired_token", "the sign-in code expired")
        if self._task is None:
            if now < self._next_poll:
                return None
            self._next_poll = now + self.interval
            if not self.nonblocking:
                try:
                    return self._hand_over(self._auth._run(self._token_steps(now)))
                except AuthError as exc:
                    if exc.retryable:
                        return None
                    raise
            self._task = self._auth._task(self._token_steps(now))
        if not self._task.poll():
            return None
        task, self._task = self._task, None
        try:
            return self._hand_over(task.result())
        except AuthError as exc:
            if exc.retryable:
                return None  # offline for a moment; try again at the next interval
            raise

    def _hand_over(self, token: Optional[str]) -> Optional[str]:
        if token is not None:
            self.access_token = token  # set here, on the polling thread, as the token is returned
        return token

    def _handle(self, response: Response, now: float) -> Optional[str]:
        status, headers, payload = response
        data = _json_body(payload)
        if status == 200 and data.get("successful", True) is not False:
            tokens = _validate_tokens(data, self._auth._clock())
            self._auth._store(tokens)
            return tokens["accessToken"]  # poll() hands it over and only then sets access_token
        error = _failure(status, headers, data)
        if error.code == "authorization_pending":
            return None
        if error.code == "slow_down":
            suggested = data.get("interval")
            self.interval = float(suggested) if type(suggested) is int and suggested > self.interval else self.interval + 5
            self._next_poll = now + self.interval
            return None
        if error.retryable:
            return None
        raise error

    def wait(self, timeout: Optional[float] = None, sleep: Callable[[float], None] = time.sleep) -> str:
        """Blocking helper for hosts with a worker thread: polls until approved, expired or ``timeout``."""
        end = None if timeout is None else self._auth._clock() + timeout
        while True:
            token = self.poll()
            if token:
                return token
            now = self._auth._clock()
            if end is not None and now >= end:
                raise AuthError("timeout", "the sign-in was not approved in time", retryable=True)
            sleep(max(0.05, min(self._next_poll - now, 0.25 if self._task is not None else 1.0)))


def _validate_tokens(body: Dict[str, Any], now: float) -> Dict[str, Any]:
    access, refresh, expires = body.get("accessToken"), body.get("refreshToken"), body.get("expiresIn")
    if not protocol.is_access_token(access) or not isinstance(refresh, str) or not re.fullmatch(r"[A-Za-z0-9_-]{16,512}", refresh):
        raise AuthError("invalid-response", "the token response is incomplete", retryable=True)
    if type(expires) is not int or not 1 <= expires <= 86400:
        raise AuthError("invalid-response", "the token lifetime is invalid", retryable=True)
    user = body.get("user") if isinstance(body.get("user"), dict) else {}
    entitlement = body.get("entitlement") if isinstance(body.get("entitlement"), dict) else {}
    expires_at = body.get("refreshSessionExpiresAtUtc")
    session_id = body.get("sessionId")
    return {
        "accessToken": access,
        "accessExpiresAt": now + expires,
        "refreshToken": refresh,
        "refreshSessionExpiresAtUtc": expires_at if isinstance(expires_at, str) else None,
        "sessionId": session_id if isinstance(session_id, str) else None,
        "user": {k: user[k] for k in ("id", "name", "avatarUrl") if isinstance(user.get(k), str)},
        "entitlement": entitlement,
    }


def _is_signed_out_marker(data: Any) -> bool:
    return bool(isinstance(data, dict) and data.get("signedOut") is True and not data.get("refreshToken"))


def assertion_claims(assertion: str) -> Dict[str, Any]:
    """The (unverified) claims of a sign-in assertion; ``{}`` when they cannot be read."""
    try:
        payload = assertion.split(".")[1]
        value = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)).decode("utf-8"))
    except (ValueError, IndexError, UnicodeDecodeError, AttributeError):
        return {}
    return value if isinstance(value, dict) else {}


# ---- the session object -------------------------------------------------------------------------------------


class LinkAuth:
    """A plugin's gta.clothing link session. Implements the token source :class:`LinkSession` expects."""

    def __init__(
        self,
        info: ClientInfo,
        token_store: Any,
        lock_path: Union[str, os.PathLike],
        *,
        base_url: str = BASE_URL,
        timeout: float = 8.0,
        lock_timeout: float = 5.0,
        worker_threads: bool = True,
        clock: Callable[[], float] = time.time,
        sleep: Callable[[float], None] = time.sleep,
        ssl_context: Optional[ssl.SSLContext] = None,
    ) -> None:
        if info.kind not in protocol.PLUGIN_KINDS or not protocol.is_semver(info.plugin_version):
            raise ValueError("invalid plugin kind or version")
        if info.channel not in protocol.CHANNELS:
            raise ValueError("unknown channel")
        self.info = info
        self.store = token_store
        self.lock_path = pathlib.Path(lock_path)
        self.http = HttpClient(info, base_url, timeout=timeout, ssl_context=ssl_context)
        self._clock = clock
        self._sleep = sleep
        self.lock_timeout = lock_timeout
        self.worker_threads = worker_threads
        self._refresh_lock = threading.Lock()
        self._invalidated: Optional[str] = None

    def _task(self, steps: Steps) -> AuthTask:
        return AuthTask(self, steps, lock_timeout=self.lock_timeout, threaded=self.worker_threads)

    # ---- state ---------------------------------------------------------------------------------------

    @property
    def tokens(self) -> Optional[Dict[str, Any]]:
        data = self.store.load()
        return data if data and data.get("refreshToken") else None

    @property
    def signed_out_by_user(self) -> bool:
        """True after :meth:`logout` until the user signs in again (or :meth:`allow_sign_in`)."""
        return _is_signed_out_marker(self.store.load())

    def allow_sign_in(self) -> None:
        """Forgets a remembered sign-out, so a device sign-in may start again."""
        if self.signed_out_by_user:
            self.store.clear()

    @property
    def signed_in(self) -> bool:
        return self.tokens is not None

    @property
    def user(self) -> Optional[Dict[str, Any]]:
        tokens = self.tokens
        return tokens.get("user") if tokens else None

    def _store(self, tokens: Dict[str, Any]) -> None:
        self.store.save(tokens)

    def _browser_url_ok(self, url: Any) -> bool:
        """Links shown to the user start exactly with ``https://gta.clothing/`` (or the loopback test server)."""
        if not isinstance(url, str) or len(url) > 512 or not re.fullmatch(r"[!-~]+", url) or "\\" in url or "@" in url:
            return False
        prefix = BASE_URL + "/" if self.http.base_url == BASE_URL else self.http.base_url + "/"
        return url.startswith(prefix)

    def invalidate_access_token(self) -> None:
        """Forces the next :meth:`access_token` to refresh."""
        tokens = self.tokens
        self._invalidated = tokens.get("accessToken") if tokens else None

    # ---- the steps (shared by the blocking and the non-blocking forms) -------------------------------

    def _access_token_steps(self, min_validity: float) -> Steps:
        tokens = self.tokens
        if not tokens:
            return None
        if tokens.get("accessToken") != self._invalidated and tokens.get("accessExpiresAt", 0) - self._clock() > min_validity:
            return tokens["accessToken"]
        try:
            fresh = yield from self._refresh_steps(tokens.get("refreshToken"), min_validity)
        except SignInRequired:
            return None  # the session ended (expired, revoked, signed out); the refresh forgot it under the lock
        return fresh["accessToken"]

    def _refresh_steps(self, seen_refresh_token: Optional[str], min_validity: float) -> Steps:
        yield _ACQUIRE
        try:
            result = yield from self._refresh_locked_steps(seen_refresh_token, min_validity)
        except Exception:
            yield _RELEASE
            raise
        yield _RELEASE
        return result

    def _refresh_locked_steps(self, seen_refresh_token: Optional[str], min_validity: float) -> Steps:
        for attempt in range(4):
            current = self.store.load()
            if not current or not current.get("refreshToken"):
                # Nothing to refresh: never signed in, signed out, or forgotten meanwhile. The store (and a sign-out
                # marker in it) stays as it is.
                raise SignInRequired("session_invalid", "no stored session")
            fresh = current.get("accessExpiresAt", 0) - self._clock() > min_validity
            if fresh and current.get("accessToken") != self._invalidated and (
                seen_refresh_token is None or current["refreshToken"] != seen_refresh_token
            ):
                return current  # another thread or process refreshed meanwhile
            body = {"grantType": "refresh_token", "refreshToken": current["refreshToken"], "clientId": self.info.client_id}
            status, headers, payload = yield _Call("POST", "/link/api/auth/token", body)
            data = _json_body(payload)
            if status == 200 and data.get("successful", True) is not False:
                tokens = _validate_tokens(data, self._clock())
                latest = self.store.load() or {}
                if latest.get("refreshToken") != current["refreshToken"]:
                    # The user signed out, or signed in again, while the request ran: keep what they did.
                    if latest.get("refreshToken") and latest.get("accessToken"):
                        return latest
                    raise SignInRequired("session_invalid", "the session was ended meanwhile")
                self._store(tokens)  # the old refresh token is spent: keep the new one before anything else
                self._invalidated = None
                return tokens
            error = _failure(status, headers, data)
            if error.code == "refresh_in_progress" and attempt < 3:
                yield _Sleep(0.25 * (attempt + 1))
                seen_refresh_token = current["refreshToken"]
                continue
            if isinstance(error, SignInRequired):
                # The session is over (expired after its lifetime, revoked, or refused). Forget it, but only if it is
                # still the one stored: a sign-out marker or a newer sign-in stays.
                if (self.store.load() or {}).get("refreshToken") == current["refreshToken"]:
                    self.store.clear()
            raise error
        raise AuthError("refresh_in_progress", "the refresh did not finish", retryable=True)

    def _mint_steps(self, nonce: str) -> Steps:
        if not protocol.is_bytes32(nonce):
            raise ValueError("the nonce is the 43-character serverNonce from DCT's challenge")
        for attempt in range(2):
            token = yield from self._access_token_steps(_REFRESH_MARGIN_SECONDS)
            if token is None:
                return None
            status, headers, payload = yield _Call("POST", "/link/api/assertions", {"nonce": nonce}, token)
            data = _json_body(payload)
            if status == 200 and data.get("successful", True) is not False:
                assertion = data.get("assertion")
                if not protocol.is_access_token(assertion):
                    raise AuthError("invalid-response", "the assertion is not a signed token", retryable=True)
                return assertion
            error = _failure(status, headers, data)
            if status == 401:
                if attempt == 0:
                    self.invalidate_access_token()  # any 401: refresh, then try once more
                    continue
                # Refused even with a fresh token: sign in again. Forget the session only if it is still the one
                # stored, under the lock a sign-out also takes.
                try:
                    yield _ACQUIRE
                except AuthError:
                    return None  # someone else holds the lock; they decide what is stored
                try:
                    if (self.store.load() or {}).get("accessToken") == token:
                        self.store.clear()
                finally:
                    yield _RELEASE
                return None
            raise error
        return None

    def _device_start_steps(self, nonblocking: bool) -> Steps:
        self.allow_sign_in()  # an explicit user action; runs on the worker, like every other store access
        body: Dict[str, Any] = {
            "clientId": self.info.client_id,
            "pluginVersion": self.info.plugin_version,
            "hostVersion": self.info.host_version,
            "protocol": f"{protocol.PROTOCOL_MAJOR}.{protocol.PROTOCOL_MINOR}",
            "channel": self.info.channel,
            "installId": self.info.install_id,
        }
        if self.info.device_name and protocol.is_text(self.info.device_name):
            body["deviceName"] = self.info.device_name
        status, headers, payload = yield _Call("POST", "/link/api/auth/device", body)
        data = _json_body(payload)
        if status != 200:
            raise _failure(status, headers, data)
        return DeviceFlow(self, data, nonblocking=nonblocking)

    def _logout_steps(self) -> Steps:
        try:
            yield _ACQUIRE
            locked = True
        except AuthError:
            # A refresh holds the lock (a slow request). The sign-out is written anyway; that refresh checks the
            # store again before it stores anything and then keeps the sign-out.
            locked = False
        current = self.store.load()
        self.store.save({"signedOut": True})  # remembered until the user signs in again
        if locked:
            yield _RELEASE
        if not (current and current.get("refreshToken")):
            return LogoutResult(had_session=False, reached=False)
        try:
            status, _, _ = yield _Call("POST", "/link/api/auth/logout", {"refreshToken": current["refreshToken"]})
        except AuthError:
            status = 0
        reached = 200 <= status < 300 or (400 <= status < 500 and status not in (408, 429))
        if not reached:
            _log.info("logout did not reach gta.clothing; the session expires by itself")
        return LogoutResult(had_session=True, reached=reached)

    def _run(self, steps: Steps) -> Any:
        """Runs steps to the end on this thread, blocking for each request, lock and pause."""
        lock: Optional[FileLock] = None
        send: Any = None
        throw: Optional[BaseException] = None
        try:
            while True:
                try:
                    if throw is not None:
                        error, throw = throw, None
                        step = steps.throw(error)
                    else:
                        step = steps.send(send)
                except StopIteration as stop:
                    return stop.value
                send = None
                if isinstance(step, _Call):
                    try:
                        send = self.http.request(step.method, step.path, step.body, bearer=step.bearer)
                    except AuthError as exc:
                        throw = exc
                elif isinstance(step, _Sleep):
                    self._sleep(step.seconds)
                elif step == _ACQUIRE:
                    if not self._refresh_lock.acquire(timeout=self.lock_timeout):
                        throw = AuthError("refresh_in_progress", "the sign-in lock is busy", retryable=True)
                        continue
                    candidate = FileLock(self.lock_path, timeout=self.lock_timeout)
                    try:
                        candidate.acquire()
                    except AuthError as exc:
                        self._refresh_lock.release()
                        throw = exc
                        continue
                    lock = candidate
                elif step == _RELEASE and lock is not None:
                    lock.release()
                    lock = None
                    self._refresh_lock.release()
        finally:
            if lock is not None:
                lock.release()
                self._refresh_lock.release()
            steps.close()

    # ---- blocking API ----------------------------------------------------------------------------------

    def access_token(self, min_validity: float = _REFRESH_MARGIN_SECONDS) -> Optional[str]:
        """A usable access token, refreshing it when it expires within ``min_validity`` seconds; ``None``
        without a session. For gta.clothing calls only; DCT gets assertions (:meth:`mint_assertion`)."""
        return self._run(self._access_token_steps(min_validity))

    def refresh(self, seen_refresh_token: Optional[str] = None, min_validity: float = _REFRESH_MARGIN_SECONDS) -> Dict[str, Any]:
        """Rotates the refresh token once, however many threads and processes ask at the same time.

        ``seen_refresh_token`` is the refresh token the caller saw. When the stored one differs, another thread
        or process refreshed meanwhile and its result is used instead of spending a token again.
        """
        return self._run(self._refresh_steps(seen_refresh_token, min_validity))

    def mint_assertion(self, nonce: str) -> Optional[str]:
        """A sign-in assertion for one DCT connection: ``POST /link/api/assertions`` with the access token and
        ``{"nonce": serverNonce}``. Mint a new one for every connection; never reuse one.

        Returns ``None`` when nobody is signed in (start a device sign-in). Any ``401`` answer refreshes the access
        token and tries once more. Raises :class:`AccountBlocked`, :class:`PluginUpdateRequired` or
        :class:`AuthError` (``retryable`` for network trouble and ``429``).
        """
        return self._run(self._mint_steps(nonce))

    def start_device_sign_in(self) -> DeviceFlow:
        """Starts a device sign-in (an explicit user action: it also clears a remembered sign-out)."""
        return self._run(self._device_start_steps(nonblocking=False))

    def logout(self) -> LogoutResult:
        """Ends the session on gta.clothing, forgets it here and remembers the sign-out. The local part always
        happens; the result says whether gta.clothing could be told (see :class:`LogoutResult`)."""
        return self._run(self._logout_steps())

    # ---- non-blocking API ------------------------------------------------------------------------------

    def begin_access_token(self, min_validity: float = _REFRESH_MARGIN_SECONDS) -> AuthTask:
        return self._task(self._access_token_steps(min_validity))

    def begin_mint_assertion(self, nonce: str) -> AuthTask:
        return self._task(self._mint_steps(nonce))

    def begin_device_sign_in(self) -> AuthTask:
        """Resolves with a :class:`DeviceFlow` whose :meth:`DeviceFlow.poll` never blocks. Clearing a remembered
        sign-out happens in the task, like every other secret-store access."""
        return self._task(self._device_start_steps(nonblocking=True))

    def begin_logout(self) -> AuthTask:
        """Resolves with a :class:`LogoutResult` (see :meth:`logout`)."""
        return self._task(self._logout_steps())
