# SPDX-License-Identifier: MIT
# Copyright (c) Schmid Software Solutions (https://schmid-software.de)
"""Where a plugin keeps its secrets: the gta.clothing link tokens.

Backends, chosen by :func:`default_secret_store`:

* Windows: DPAPI (``CryptProtectData`` in the user scope) via ctypes.
* macOS: the login Keychain through the Security framework via ctypes (``SecItemAdd``,
  ``SecItemCopyMatching``, ``SecItemUpdate``). The secret never appears on a command line.
* Linux: ``secret-tool`` (libsecret) with the secret written to its standard input.
* Anywhere else, or when the backend is unavailable: a file only the user can read (mode 0600), with an
  :class:`InsecureStorageWarning`.

Secrets are never logged. Stores hold bytes; :class:`TokenStore` adds the format.
"""

from __future__ import annotations

import base64
import json
import logging
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import uuid
import warnings
from typing import Any, Dict, Optional, Union

__all__ = [
    "SecretStore",
    "MemorySecretStore",
    "FileSecretStore",
    "DpapiSecretStore",
    "KeychainSecretStore",
    "SecretToolSecretStore",
    "InsecureStorageWarning",
    "SecretStoreError",
    "TokenStore",
    "default_secret_store",
    "plugin_data_dir",
    "load_install_id",
    "write_private_file",
    "read_private_file",
]

_log = logging.getLogger(__name__)
_SERVICE = "dct-link"


class SecretStoreError(Exception):
    """The backend refused to store or read a secret."""


class InsecureStorageWarning(UserWarning):
    """Secrets are kept in a plain file because no protected store is available."""


def read_private_file(path: Union[str, os.PathLike]) -> Optional[bytes]:
    """Reads a secret file, or ``None`` when it does not exist. On Windows a file that another process is
    replacing at that moment refuses access briefly; the read waits for it instead of failing."""
    target = pathlib.Path(path)
    for attempt in range(10):
        try:
            return target.read_bytes()
        except FileNotFoundError:
            return None
        except PermissionError:
            if os.name != "nt" or attempt == 9:
                raise
            time.sleep(0.02 * (attempt + 1))
    return None


def write_private_file(path: Union[str, os.PathLike], data: bytes) -> None:
    """Writes ``data`` atomically to ``path``, readable only by the current user where the OS supports it."""
    target = pathlib.Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix=".tmp-", dir=str(target.parent))
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        if os.name != "nt":
            os.chmod(temp, 0o600)
        for attempt in range(10):
            try:
                os.replace(temp, target)
                break
            except PermissionError:
                if os.name != "nt" or attempt == 9:
                    raise
                time.sleep(0.05 * (attempt + 1))  # a scanner may still hold the old file for a moment
    except BaseException:
        try:
            os.unlink(temp)
        except OSError:
            pass  # the temporary file is gone already
        raise


class SecretStore:
    """Stores one secret value (bytes)."""

    def load(self) -> Optional[bytes]:
        raise NotImplementedError

    def save(self, data: bytes) -> None:
        raise NotImplementedError

    def clear(self) -> None:
        raise NotImplementedError


class MemorySecretStore(SecretStore):
    """Keeps the secret in memory only (tests, or a host that must not persist anything)."""

    def __init__(self, data: Optional[bytes] = None) -> None:
        self._data = data

    def load(self) -> Optional[bytes]:
        return self._data

    def save(self, data: bytes) -> None:
        self._data = bytes(data)

    def clear(self) -> None:
        self._data = None


class FileSecretStore(SecretStore):
    """A plain file with mode 0600. Used only when nothing better exists; warns once per process."""

    _warned = False

    def __init__(self, path: Union[str, os.PathLike], warn: bool = True) -> None:
        self.path = pathlib.Path(path)
        self.warn = warn

    def _warn(self) -> None:
        if self.warn and not FileSecretStore._warned:
            FileSecretStore._warned = True
            message = "Creator Link secrets are stored in a file without OS protection (no keychain available)."
            warnings.warn(message, InsecureStorageWarning, stacklevel=3)
            _log.warning(message)

    def load(self) -> Optional[bytes]:
        return read_private_file(self.path)

    def save(self, data: bytes) -> None:
        self._warn()
        write_private_file(self.path, data)

    def clear(self) -> None:
        try:
            self.path.unlink()
        except FileNotFoundError:
            pass


# ---- Windows DPAPI ------------------------------------------------------------------------------------


class DpapiSecretStore(SecretStore):
    """Encrypts with DPAPI for the current Windows user. ``entropy`` (the install id) must match to decrypt."""

    _MAGIC = b"DCTDPAPI1\n"

    def __init__(self, path: Union[str, os.PathLike], entropy: bytes, description: str = "Creator Link") -> None:
        if os.name != "nt":
            raise SecretStoreError("DPAPI exists on Windows only")
        self.path = pathlib.Path(path)
        self.entropy = bytes(entropy)
        self.description = description

    @staticmethod
    def _api():
        import ctypes
        from ctypes import wintypes

        class Blob(ctypes.Structure):
            _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_ubyte))]

        crypt32 = ctypes.WinDLL("crypt32", use_last_error=True)
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        protect = crypt32.CryptProtectData
        protect.argtypes = [ctypes.POINTER(Blob), wintypes.LPCWSTR, ctypes.POINTER(Blob), ctypes.c_void_p,
                            ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(Blob)]
        protect.restype = wintypes.BOOL
        unprotect = crypt32.CryptUnprotectData
        unprotect.argtypes = [ctypes.POINTER(Blob), ctypes.c_void_p, ctypes.POINTER(Blob), ctypes.c_void_p,
                              ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(Blob)]
        unprotect.restype = wintypes.BOOL
        kernel32.LocalFree.argtypes = [ctypes.c_void_p]
        kernel32.LocalFree.restype = ctypes.c_void_p
        return ctypes, Blob, protect, unprotect, kernel32.LocalFree

    def _call(self, encrypt: bool, data: bytes) -> bytes:
        ctypes, Blob, protect, unprotect, local_free = self._api()
        source = (ctypes.c_ubyte * max(len(data), 1)).from_buffer_copy(data or b"\0")
        extra = (ctypes.c_ubyte * max(len(self.entropy), 1)).from_buffer_copy(self.entropy or b"\0")
        in_blob = Blob(len(data), ctypes.cast(source, ctypes.POINTER(ctypes.c_ubyte)))
        entropy = Blob(len(self.entropy), ctypes.cast(extra, ctypes.POINTER(ctypes.c_ubyte)))
        out_blob = Blob()
        flags = 0x1  # CRYPTPROTECT_UI_FORBIDDEN; user scope (no CRYPTPROTECT_LOCAL_MACHINE)
        if encrypt:
            ok = protect(ctypes.byref(in_blob), self.description, ctypes.byref(entropy), None, None, flags, ctypes.byref(out_blob))
        else:
            ok = unprotect(ctypes.byref(in_blob), None, ctypes.byref(entropy), None, None, flags, ctypes.byref(out_blob))
        if not ok:
            raise SecretStoreError(f"DPAPI failed (error {ctypes.get_last_error()})")
        try:
            return ctypes.string_at(out_blob.pbData, out_blob.cbData)
        finally:
            local_free(ctypes.cast(out_blob.pbData, ctypes.c_void_p))

    def load(self) -> Optional[bytes]:
        raw = read_private_file(self.path)
        if raw is None:
            return None
        if not raw.startswith(self._MAGIC):
            raise SecretStoreError("not a DPAPI secret file")
        return self._call(False, raw[len(self._MAGIC) :])

    def save(self, data: bytes) -> None:
        write_private_file(self.path, self._MAGIC + self._call(True, bytes(data)))

    def clear(self) -> None:
        try:
            self.path.unlink()
        except FileNotFoundError:
            pass


# ---- macOS Keychain -----------------------------------------------------------------------------------


class KeychainSecretStore(SecretStore):
    """A generic password item in the user's login Keychain, through the Security framework."""

    _ERR_ITEM_NOT_FOUND = -25300

    def __init__(self, service: str, account: str) -> None:
        if sys.platform != "darwin":
            raise SecretStoreError("the Keychain exists on macOS only")
        self.service = service
        self.account = account
        self._lib = _KeychainApi.get()

    def _query(self, extra: Dict[Any, Any]) -> Any:
        lib = self._lib
        items = {lib.kSecClass: lib.kSecClassGenericPassword, lib.kSecAttrService: self.service, lib.kSecAttrAccount: self.account}
        items.update(extra)
        return lib.dictionary(items)

    def load(self) -> Optional[bytes]:
        lib = self._lib
        query = self._query({lib.kSecReturnData: lib.kCFBooleanTrue, lib.kSecMatchLimit: lib.kSecMatchLimitOne})
        result = lib.ctypes.c_void_p()
        try:
            status = lib.SecItemCopyMatching(query, lib.ctypes.byref(result))
        finally:
            lib.CFRelease(query)
        if status == self._ERR_ITEM_NOT_FOUND:
            return None
        if status != 0 or not result.value:
            raise SecretStoreError(f"Keychain read failed ({status})")
        try:
            length = lib.CFDataGetLength(result)
            return lib.ctypes.string_at(lib.CFDataGetBytePtr(result), length)
        finally:
            lib.CFRelease(result)

    def save(self, data: bytes) -> None:
        lib = self._lib
        value = lib.data(bytes(data))
        try:
            query = self._query({})
            update = lib.dictionary({lib.kSecValueData: value})
            try:
                status = lib.SecItemUpdate(query, update)
            finally:
                lib.CFRelease(query)
                lib.CFRelease(update)
            if status == self._ERR_ITEM_NOT_FOUND:
                attributes = self._query({lib.kSecValueData: value})
                try:
                    status = lib.SecItemAdd(attributes, None)
                finally:
                    lib.CFRelease(attributes)
            if status != 0:
                raise SecretStoreError(f"Keychain write failed ({status})")
        finally:
            lib.CFRelease(value)

    def clear(self) -> None:
        lib = self._lib
        query = self._query({})
        try:
            status = lib.SecItemDelete(query)
        finally:
            lib.CFRelease(query)
        if status not in (0, self._ERR_ITEM_NOT_FOUND):
            raise SecretStoreError(f"Keychain delete failed ({status})")


class _KeychainApi:
    """ctypes bindings for the few CoreFoundation and Security calls the Keychain store needs."""

    _instance: Optional["_KeychainApi"] = None
    _lock = threading.Lock()

    @classmethod
    def get(cls) -> "_KeychainApi":
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def __init__(self) -> None:
        import ctypes

        self.ctypes = ctypes
        cf = ctypes.CDLL("/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation")
        sec = ctypes.CDLL("/System/Library/Frameworks/Security.framework/Security")
        vp, index = ctypes.c_void_p, ctypes.c_long  # CFIndex is a signed long

        def fn(lib: Any, name: str, restype: Any, *argtypes: Any) -> Any:
            func = getattr(lib, name)
            func.restype = restype
            func.argtypes = list(argtypes)
            return func

        self.CFRelease = fn(cf, "CFRelease", None, vp)
        self.CFDataCreate = fn(cf, "CFDataCreate", vp, vp, ctypes.c_char_p, index)
        self.CFDataGetLength = fn(cf, "CFDataGetLength", index, vp)
        self.CFDataGetBytePtr = fn(cf, "CFDataGetBytePtr", vp, vp)
        self.CFStringCreateWithCString = fn(cf, "CFStringCreateWithCString", vp, vp, ctypes.c_char_p, ctypes.c_uint32)
        self.CFDictionaryCreate = fn(cf, "CFDictionaryCreate", vp, vp, vp, vp, index, vp, vp)
        self.SecItemAdd = fn(sec, "SecItemAdd", ctypes.c_int32, vp, vp)
        self.SecItemUpdate = fn(sec, "SecItemUpdate", ctypes.c_int32, vp, vp)
        self.SecItemCopyMatching = fn(sec, "SecItemCopyMatching", ctypes.c_int32, vp, ctypes.POINTER(vp))
        self.SecItemDelete = fn(sec, "SecItemDelete", ctypes.c_int32, vp)
        self._key_callbacks = ctypes.addressof(ctypes.c_char.in_dll(cf, "kCFTypeDictionaryKeyCallBacks"))
        self._value_callbacks = ctypes.addressof(ctypes.c_char.in_dll(cf, "kCFTypeDictionaryValueCallBacks"))
        self.kCFBooleanTrue = vp.in_dll(cf, "kCFBooleanTrue").value
        for name in ("kSecClass", "kSecClassGenericPassword", "kSecAttrService", "kSecAttrAccount", "kSecValueData",
                     "kSecReturnData", "kSecMatchLimit", "kSecMatchLimitOne"):
            setattr(self, name, vp.in_dll(sec, name).value)

    def string(self, text: str) -> int:
        return self.CFStringCreateWithCString(None, text.encode("utf-8"), 0x08000100)  # kCFStringEncodingUTF8

    def data(self, raw: bytes) -> int:
        return self.CFDataCreate(None, raw, len(raw))

    def dictionary(self, items: Dict[Any, Any]) -> int:
        ctypes = self.ctypes
        owned = []
        keys, values = [], []
        for key, value in items.items():
            if isinstance(value, str):
                value = self.string(value)
                owned.append(value)
            keys.append(key)
            values.append(value)
        key_array = (ctypes.c_void_p * len(keys))(*keys)
        value_array = (ctypes.c_void_p * len(values))(*values)
        try:
            return self.CFDictionaryCreate(None, key_array, value_array, len(keys), self._key_callbacks, self._value_callbacks)
        finally:
            for ref in owned:  # the dictionary retained them
                self.CFRelease(ref)


# ---- Linux libsecret ----------------------------------------------------------------------------------


class SecretToolSecretStore(SecretStore):
    """libsecret through ``secret-tool``. The secret travels on standard input and output only."""

    def __init__(self, service: str, account: str, label: str = "Creator Link", timeout: float = 15.0) -> None:
        self.tool = shutil.which("secret-tool")
        if self.tool is None:
            raise SecretStoreError("secret-tool is not installed")
        self.service = service
        self.account = account
        self.label = label
        self.timeout = timeout

    def _run(self, args: list, data: Optional[bytes] = None) -> subprocess.CompletedProcess:
        try:
            return subprocess.run(
                [self.tool, *args, "service", self.service, "account", self.account],
                input=data,
                capture_output=True,
                timeout=self.timeout,
                check=False,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise SecretStoreError("secret-tool failed") from exc

    def load(self) -> Optional[bytes]:
        result = self._run(["lookup"])
        if result.returncode != 0 or not result.stdout.strip():
            return None
        try:
            return base64.b64decode(result.stdout.strip(), validate=True)
        except ValueError as exc:
            raise SecretStoreError("unreadable secret-tool value") from exc

    def save(self, data: bytes) -> None:
        result = self._run(["store", f"--label={self.label}"], base64.b64encode(bytes(data)))
        if result.returncode != 0:
            raise SecretStoreError("secret-tool could not store the secret")

    def clear(self) -> None:
        self._run(["clear"])


# ---- choosing a backend -------------------------------------------------------------------------------


def plugin_data_dir(kind: str) -> pathlib.Path:
    """The default per-user folder for a plugin kind (``kind`` is a protocol plugin kind)."""
    if not re.fullmatch(r"[a-z]{1,32}", kind or ""):
        raise ValueError("invalid plugin kind")
    if os.name == "nt":
        base = pathlib.Path(os.environ.get("LOCALAPPDATA") or pathlib.Path.home() / "AppData" / "Local")
        return base / "DurtyClothTool" / "Plugins" / kind
    if sys.platform == "darwin":
        return pathlib.Path.home() / "Library" / "Application Support" / "DurtyClothTool" / "Plugins" / kind
    base = pathlib.Path(os.environ.get("XDG_DATA_HOME") or pathlib.Path.home() / ".local" / "share")
    return base / "DurtyClothTool" / "plugins" / kind


def load_install_id(directory: Union[str, os.PathLike]) -> str:
    """Returns this installation's random id, creating it on first use. It is not a secret."""
    path = pathlib.Path(directory) / "install-id"
    try:
        value = path.read_text("ascii").strip()
        return str(uuid.UUID(value))
    except (OSError, ValueError):
        pass  # missing or damaged: make a new one
    value = str(uuid.uuid4())
    write_private_file(path, value.encode("ascii"))
    return value


def default_secret_store(
    name: str, directory: Union[str, os.PathLike], install_id: str, *, allow_file_fallback: bool = True
) -> SecretStore:
    """The best available store for the secret called ``name`` (for example ``tokens``)."""
    if not re.fullmatch(r"[a-z][a-z0-9-]{0,31}", name):
        raise ValueError("invalid secret name")
    folder = pathlib.Path(directory)
    account = f"{folder.name}-{name}-{install_id}"
    try:
        if os.name == "nt":
            return DpapiSecretStore(folder / f"{name}.dpapi", install_id.encode("utf-8"))
        if sys.platform == "darwin":
            return KeychainSecretStore(_SERVICE, account)
        if sys.platform.startswith("linux"):
            return SecretToolSecretStore(_SERVICE, account)
    except (SecretStoreError, OSError, AttributeError, ValueError) as exc:
        _log.info("no protected secret store: %s", type(exc).__name__)
    if not allow_file_fallback:
        raise SecretStoreError("no protected secret store is available")
    return FileSecretStore(folder / f"{name}.secret")


# ---- typed wrappers -----------------------------------------------------------------------------------


class TokenStore:
    """The gta.clothing link session (a JSON object) in a :class:`SecretStore`."""

    def __init__(self, store: SecretStore) -> None:
        self.store = store

    def load(self) -> Optional[Dict[str, Any]]:
        try:
            raw = self.store.load()
        except SecretStoreError:
            _log.warning("the stored sign-in could not be read; signing in again")
            return None
        if not raw:
            return None
        try:
            value = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, ValueError):
            return None
        return value if isinstance(value, dict) else None

    def save(self, tokens: Dict[str, Any]) -> None:
        self.store.save(json.dumps(tokens, separators=(",", ":"), sort_keys=True).encode("utf-8"))

    def clear(self) -> None:
        self.store.clear()
