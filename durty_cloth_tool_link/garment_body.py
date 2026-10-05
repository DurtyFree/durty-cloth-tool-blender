# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2026 Schmid Software Solutions (https://schmid-software.de)
"""The hosted freemode body: downloading it for the signed-in account and keeping it in the add-on's user folder.

The body is served by gta.clothing's link origin for a short-lived ticket, as the Creator Link panel loads it:
the channel manifest names the body version and the panel version, ``POST /link/panel/ticket`` (with the sign-in)
returns a ticket, and ``GET /link/assets/body/<version>/<file>`` (``Authorization: Ticket``) the file. Each version
is kept in ``body/<version>/`` and never downloaded again. Without online access, or when gta.clothing cannot be
reached, the newest kept version is used. The requests run on a worker thread; :meth:`BodyDownload.poll` never
blocks. Nothing here imports Blender.
"""

from __future__ import annotations

import http.client
import ipaddress
import json
import os
import pathlib
import re
import ssl
import tempfile
import threading
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Callable, Dict, List, NamedTuple, Optional, Tuple

#: The origin that serves the hosted body and its tickets.
LINK_ORIGIN = "https://link.gta.clothing"
#: The folder of the add-on's user folder that keeps the downloaded bodies.
CACHE_FOLDER = "body"
#: The hosted body of each gender (compressed with meshopt, which Blender's glTF importer reads from 5.2 on).
BODY_FILES = {"male": "freemode_male.glb", "female": "freemode_female.glb"}
#: An uncompressed copy, for Blender versions that cannot read the compressed body (used when it is served).
PLAIN_FILES = {"male": "freemode_male_plain.glb", "female": "freemode_female_plain.glb"}
#: The first Blender version known to import the compressed body.
COMPRESSED_FROM = (5, 2)
MAX_BODY_BYTES = 32 * 1024 * 1024
_MAX_JSON_BYTES = 256 * 1024
_VERSION = re.compile(r"[A-Za-z0-9._-]{1,32}")
_TICKET = re.compile(r"v1\.[A-Za-z0-9_-]{40,3000}")


class BodyError(Exception):
    """The body could not be had; ``code`` names the reason (a ``garment.body.<code>`` text)."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


class BodyResult(NamedTuple):
    path: pathlib.Path
    version: str
    gender: str
    #: The file was kept from an earlier download.
    cached: bool


def check_origin(url: str) -> str:
    """``https://link.gta.clothing`` or, for tests, a loopback ``http(s)://127.0.0.1:port``."""
    url = url.rstrip("/")
    if url == LINK_ORIGIN:
        return url
    parts = urllib.parse.urlsplit(url)
    host = parts.hostname or ""
    try:
        loopback = host == "localhost" or ipaddress.ip_address(host).is_loopback
    except ValueError:
        loopback = False
    if parts.scheme in ("http", "https") and loopback and not parts.path and "@" not in parts.netloc:
        return url
    raise ValueError("the hosted body comes from https://link.gta.clothing only")


def valid_version(value: Any) -> bool:
    return isinstance(value, str) and _VERSION.fullmatch(value) is not None and ".." not in value


def body_files(gender: str, blender_version: Tuple[int, ...]) -> List[str]:
    """The files to ask for, in order: older Blender versions take the uncompressed copy first."""
    if gender not in BODY_FILES:
        raise ValueError(gender)
    if tuple(blender_version[:2]) >= COMPRESSED_FROM:
        return [BODY_FILES[gender]]
    return [PLAIN_FILES[gender], BODY_FILES[gender]]


def is_glb(data: bytes) -> bool:
    return len(data) >= 20 and data[:4] == b"glTF"


def _version_key(name: str) -> tuple:
    return tuple(int(part) if part.isdigit() else part for part in re.split(r"[._-]", name))


def cached_body(cache_root: pathlib.Path, gender: str, version: Optional[str] = None,
                files: Optional[List[str]] = None) -> Optional[BodyResult]:
    """A kept body: of ``version``, or the newest one kept."""
    folder = cache_root / CACHE_FOLDER
    if not folder.is_dir():
        return None
    names = files or [PLAIN_FILES[gender], BODY_FILES[gender]]
    versions = [version] if version else sorted((p.name for p in folder.iterdir() if p.is_dir()
                                                 and valid_version(p.name)), key=_version_key, reverse=True)
    for candidate in versions:
        for name in names:
            path = folder / candidate / name
            try:
                if path.is_file() and is_glb(path.read_bytes()[:20]):
                    return BodyResult(path, candidate, gender, True)
            except OSError:
                continue
    return None


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: D401 - urllib hook
        return None  # a ticket never follows a redirect elsewhere


class BodyDownload:
    """Gets the hosted body of one gender for the signed-in account (see the module text)."""

    def __init__(self, *, gender: str, channel: str, cache_root: pathlib.Path, client_header: str,
                 access_token: Callable[[], Optional[str]], blender_version: Tuple[int, ...],
                 origin: str = LINK_ORIGIN, timeout: float = 20.0, online: bool = True) -> None:
        if gender not in BODY_FILES:
            raise ValueError(gender)
        self.gender = gender
        self.channel = channel
        self.cache_root = pathlib.Path(cache_root)
        self.client_header = client_header
        self.access_token = access_token
        self.blender_version = tuple(blender_version)
        self.origin = check_origin(origin)
        self.timeout = timeout
        self.online = online
        self.result: Optional[BodyResult] = None
        self.error: Optional[str] = None
        self.cancelled = False
        self._thread: Optional[threading.Thread] = None
        handlers: list = [_NoRedirect()]
        if not self.origin.startswith("https://"):
            handlers.append(urllib.request.ProxyHandler({}))  # a test server is never behind a proxy
        else:
            handlers.append(urllib.request.HTTPSHandler(context=ssl.create_default_context()))
        self._opener = urllib.request.build_opener(*handlers)

    # ---- running -------------------------------------------------------------------------------------

    def start(self) -> "BodyDownload":
        self._thread = threading.Thread(target=self._work, name="dct-body-download", daemon=True)
        self._thread.start()
        return self

    def run(self) -> "BodyDownload":
        """The same work on the calling thread (tests)."""
        self._work()
        return self

    @property
    def done(self) -> bool:
        return self.result is not None or self.error is not None

    def poll(self) -> bool:
        """Whether the download has finished (never blocks)."""
        return self.done

    def cancel(self) -> None:
        self.cancelled = True

    def _work(self) -> None:
        try:
            self.result = self._fetch()
        except BodyError as exc:
            self.error = exc.code
        except Exception:  # noqa: BLE001 - every failure ends the download with a message, never a dead thread
            self.error = "invalid"

    # ---- the requests --------------------------------------------------------------------------------

    def _request(self, method: str, path: str, *, body: Optional[Dict[str, Any]] = None,
                 authorization: Optional[str] = None, accept: str = "application/json",
                 limit: int = _MAX_JSON_BYTES) -> Tuple[int, bytes]:
        if self.cancelled:
            raise BodyError("cancelled")
        headers = {"Accept": accept, "X-DCT-Link-Client": self.client_header, "User-Agent": self.client_header}
        data = None
        if body is not None:
            data = json.dumps(body, separators=(",", ":")).encode("utf-8")
            headers["Content-Type"] = "application/json"
        if authorization:
            headers["Authorization"] = authorization
        request = urllib.request.Request(self.origin + path, data=data, headers=headers, method=method)
        try:
            with self._opener.open(request, timeout=self.timeout) as response:
                payload = response.read(limit + 1)
                status = response.status
        except urllib.error.HTTPError as error:
            try:
                payload = error.read(_MAX_JSON_BYTES)
            except (OSError, http.client.HTTPException):
                payload = b""
            status = error.code
        except (urllib.error.URLError, OSError, ValueError, http.client.HTTPException) as exc:
            raise BodyError("network") from exc
        if len(payload) > limit:
            raise BodyError("invalid")
        return status, payload

    @staticmethod
    def _json(payload: bytes) -> Dict[str, Any]:
        try:
            value = json.loads(payload.decode("utf-8"))
        except (UnicodeDecodeError, ValueError):
            raise BodyError("invalid") from None
        if not isinstance(value, dict):
            raise BodyError("invalid")
        return value

    @staticmethod
    def _failure(status: int, payload: bytes) -> BodyError:
        try:
            code = json.loads(payload.decode("utf-8")).get("failureCode")
        except (UnicodeDecodeError, ValueError, AttributeError):
            code = None
        if status == 401:
            return BodyError("signed-out")
        if status == 403:
            return BodyError("not-entitled" if code == "feature_not_entitled" else "refused")
        if status == 426:
            return BodyError("update")
        if status == 429:
            return BodyError("busy")
        if status >= 500:
            return BodyError("unavailable")
        return BodyError("invalid")

    def _fetch(self) -> BodyResult:
        files = body_files(self.gender, self.blender_version)
        if not self.online:
            kept = cached_body(self.cache_root, self.gender, files=files)
            if kept is None:
                raise BodyError("offline")
            return kept
        try:
            status, payload = self._request("GET", f"/link/manifest/{urllib.parse.quote(self.channel)}.json")
        except BodyError as exc:
            kept = cached_body(self.cache_root, self.gender, files=files) if exc.code == "network" else None
            if kept is None:
                raise
            return kept
        if status == 404:
            raise BodyError("no-body")
        if status != 200:
            raise self._failure(status, payload)
        manifest = self._json(payload)
        body = manifest.get("body") if isinstance(manifest.get("body"), dict) else None
        panel = manifest.get("panel") if isinstance(manifest.get("panel"), dict) else None
        version = body.get("version") if body else None
        if not valid_version(version):
            raise BodyError("no-body")
        kept = cached_body(self.cache_root, self.gender, version, files)
        if kept is not None:
            return kept
        panel_version = panel.get("version") if panel else None
        if not isinstance(panel_version, str) or not re.fullmatch(r"[0-9A-Za-z.+-]{1,64}", panel_version):
            raise BodyError("unavailable")

        token = self.access_token()
        if not token:
            older = cached_body(self.cache_root, self.gender, files=files)  # signed out: a body kept before
            if older is None:
                raise BodyError("signed-out")
            return older
        status, payload = self._request("POST", "/link/panel/ticket", body={"channel": self.channel,
                                                                            "version": panel_version},
                                        authorization="Bearer " + token)
        if status != 200:
            raise self._failure(status, payload)
        ticket = self._json(payload).get("ticket")
        if not isinstance(ticket, str) or not _TICKET.fullmatch(ticket):
            raise BodyError("invalid")

        for name in files:
            status, payload = self._request("GET", f"/link/assets/body/{version}/{name}",
                                            authorization="Ticket " + ticket, accept="model/gltf-binary",
                                            limit=MAX_BODY_BYTES)
            if status == 404:
                continue
            if status != 200:
                raise self._failure(status, payload)
            if not is_glb(payload):
                raise BodyError("invalid")
            return BodyResult(self._keep(version, name, payload), version, self.gender, False)
        raise BodyError("no-body")

    def _keep(self, version: str, name: str, data: bytes) -> pathlib.Path:
        folder = self.cache_root / CACHE_FOLDER / version
        try:
            folder.mkdir(parents=True, exist_ok=True)
            handle, temporary = tempfile.mkstemp(prefix=".download-", dir=folder)
            with os.fdopen(handle, "wb") as stream:
                stream.write(data)
            target = folder / name
            os.replace(temporary, target)
        except OSError as exc:
            raise BodyError("disk") from exc
        return target
