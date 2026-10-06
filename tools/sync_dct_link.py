#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2026 Schmid Software Solutions (https://schmid-software.de)
"""Vendors dct_link, the Creator Link client, from a Durty Cloth Tool checkout.

    python tools/sync_dct_link.py <path to the Durty Cloth Tool checkout>
    python tools/sync_dct_link.py --check [<path to the Durty Cloth Tool checkout>]

The first form replaces ``durty_cloth_tool_link/dct_link`` with the modules the add-on uses from the dct_link
package in the checkout: the allowlist in ``ROOT_MODULES`` plus every module they import, nothing else. The
package is the one folder named dct_link that the checkout tracks in Git; the path of that folder works in place of
the checkout. The MIT ``LICENSE`` beside the package is copied next to the modules and ``VENDORED.md`` records the
dct_link version, the Creator Link protocol version, the date of the sync and the SHA-256 of every copied file.
Each file is copied byte for byte: never edit the vendored files by hand, change dct_link upstream and sync again.

``--check`` verifies the vendored copy against ``VENDORED.md`` (the hashes, and that the recorded versions are
the ones of the copied modules; the test suite runs the same check), and also against the upstream files when a
Durty Cloth Tool checkout is given or sits beside this repository, so a change upstream that was not synced yet is
caught.

Standard library only.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import pathlib
import re
import shutil
import subprocess
import sys
from typing import Dict, List, Optional, Tuple

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
VENDOR_DIR = REPO_ROOT / "durty_cloth_tool_link" / "dct_link"
RECORD_NAME = "VENDORED.md"
PACKAGE_NAME = "dct_link"
#: The modules the add-on imports; whatever they import from dct_link is added automatically.
ROOT_MODULES = ("__init__", "protocol", "ws", "session", "auth", "tokens", "fit")
SPDX_MIT = "# SPDX-License-Identifier: MIT"
#: Where a Durty Cloth Tool checkout usually sits: next to this repository.
SIBLING_CHECKOUT = REPO_ROOT.parent / "durty-cloth-tool"
_ROW = re.compile(r"^\| `([^`]+)` \| `([0-9a-f]{64})` \|$")
_VERSION_LINE = re.compile(r"^- dct_link version: (\S+)$", re.MULTILINE)
_PROTOCOL_LINE = re.compile(r"^- Creator Link protocol: (\d+\.\d+)$", re.MULTILINE)
_SYNCED_LINE = re.compile(r"^- Synced: (\d{4}-\d{2}-\d{2})$", re.MULTILINE)
#: The protocol version in the constants of ``protocol.py`` (``"major": 2, "minor": 0`` in its protocol block).
_PROTOCOL_VERSION = re.compile(r'"protocol":\s*\{[^}]*?"major":\s*(\d+),\s*"minor":\s*(\d+)')
_RELATIVE_IMPORT = re.compile(r"^[ \t]*from[ \t]+\.(\w*)[ \t]+import[ \t]+(\([^)]*\)|[\w \t,]+)", re.MULTILINE)


class SyncError(Exception):
    """The source or the vendored copy is not what the tool expects."""


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def find_package(source: pathlib.Path) -> pathlib.Path:
    """The dct_link package folder for ``source``: that folder itself, or the one a Durty Cloth Tool checkout
    tracks. Git is asked where it is, so the tool does not depend on the layout of the checkout."""
    source = source.resolve()
    if source.name == PACKAGE_NAME and (source / "__init__.py").is_file():
        package = source
    else:
        patterns = [f"{PACKAGE_NAME}/__init__.py", f"*/{PACKAGE_NAME}/__init__.py"]
        try:
            listed = subprocess.run(["git", "-C", str(source), "ls-files", "-z", "--", *patterns],
                                    capture_output=True, text=True, check=True, timeout=30).stdout
        except (OSError, subprocess.SubprocessError):
            raise SyncError(f"{source} is neither the dct_link package nor a Git checkout") from None
        found = [name for name in listed.split("\0") if name]
        if len(found) != 1:
            raise SyncError(f"{source} tracks {len(found)} dct_link packages; pass the folder of the one to vendor")
        package = (source / found[0]).parent.resolve()
    if package == VENDOR_DIR.resolve():
        raise SyncError(f"{package} is the vendored copy itself, not its source")
    return package


def sibling_package() -> Optional[pathlib.Path]:
    """The dct_link package of a Durty Cloth Tool checkout beside this repository, when there is one."""
    if not SIBLING_CHECKOUT.is_dir():
        return None
    try:
        return find_package(SIBLING_CHECKOUT)
    except SyncError:
        return None


def imported_modules(source: str) -> List[str]:
    """The dct_link modules a module imports with relative imports (``from . import x``, ``from . import x as y``,
    ``from .x import y``)."""
    names = []
    for module, imported in _RELATIVE_IMPORT.findall(source):
        if module:
            names.append(module)
        else:
            names.extend(n.split()[0] for n in imported.replace("(", "").replace(")", "").split(",") if n.strip())
    return names


def source_files(package: pathlib.Path) -> List[pathlib.Path]:
    """The modules of the dct_link package the add-on needs (the roots and what they import), sorted by name."""
    if not (package / "__init__.py").is_file():
        raise SyncError(f"{package} is not the dct_link package (no __init__.py)")
    wanted, pending = set(), list(ROOT_MODULES)
    while pending:
        name = pending.pop()
        if name in wanted:
            continue
        path = package / f"{name}.py"
        if not path.is_file():
            raise SyncError(f"dct_link has no module {name}, which the add-on needs")
        wanted.add(name)
        pending.extend(imported_modules(path.read_text("utf-8")))
    return [package / f"{name}.py" for name in sorted(wanted)]


def check_source(files: List[pathlib.Path], license_file: pathlib.Path) -> None:
    if not license_file.is_file() or b"MIT License" not in license_file.read_bytes():
        raise SyncError(f"{license_file} is not the MIT licence of dct_link")
    for path in [license_file, *files]:
        data = path.read_bytes()
        if b"\r" in data:
            raise SyncError(f"{path.name} has CR line endings; dct_link is LF only")
        if path.suffix == ".py" and not data.decode("utf-8").startswith(SPDX_MIT):
            raise SyncError(f"{path.name} lacks the MIT SPDX header")


def package_version(init_file: pathlib.Path) -> str:
    match = re.search(r'^__version__ = "([^"]+)"', init_file.read_text("utf-8"), re.MULTILINE)
    if match is None:
        raise SyncError("dct_link/__init__.py has no __version__")
    return match.group(1)


def protocol_version(protocol_file: pathlib.Path) -> str:
    """The Creator Link protocol version (``major.minor``) of a dct_link ``protocol.py``."""
    match = _PROTOCOL_VERSION.search(protocol_file.read_text("utf-8"))
    if match is None:
        raise SyncError("dct_link/protocol.py names no protocol version")
    return f"{match.group(1)}.{match.group(2)}"


def render_record(version: str, protocol: str, synced: str, hashes: List[Tuple[str, str]]) -> str:
    lines = [
        "# Vendored dct_link",
        "",
        "This folder holds byte-for-byte copies of the `dct_link` modules the add-on uses. `dct_link` is the Creator",
        "Link client. It is developed together with Durty Cloth Tool and synced into this folder with",
        "`tools/sync_dct_link.py`. It is MIT licensed (see `LICENSE` in this folder); every module keeps its SPDX",
        "header. The rest of the add-on is GPL-3.0-or-later.",
        "",
        "Do not edit these files by hand. Change dct_link upstream, then run",
        "`python tools/sync_dct_link.py <Durty Cloth Tool checkout>`, which rewrites this folder and this record.",
        "`python tools/sync_dct_link.py --check` and the test suite verify the hashes below.",
        "",
        "- Source: the `dct_link` package and its `LICENSE` in the Durty Cloth Tool repository",
        f"- dct_link version: {version}",
        f"- Creator Link protocol: {protocol}",
        f"- Synced: {synced}",
        "",
        "| File | SHA-256 |",
        "|---|---|",
    ]
    lines += [f"| `{name}` | `{digest}` |" for name, digest in hashes]
    return "\n".join(lines) + "\n"


def read_record(record: pathlib.Path) -> Dict[str, str]:
    if not record.is_file():
        raise SyncError(f"{record} is missing; run the sync first")
    hashes: Dict[str, str] = {}
    for line in record.read_text("utf-8").splitlines():
        match = _ROW.match(line)
        if match:
            hashes[match.group(1)] = match.group(2)
    if not hashes:
        raise SyncError(f"{record} lists no files")
    return hashes


def verify(vendor_dir: pathlib.Path = VENDOR_DIR) -> List[str]:
    """Problems with the vendored copy (empty when it matches its record)."""
    try:
        expected = read_record(vendor_dir / RECORD_NAME)
    except SyncError as exc:
        return [str(exc)]
    problems = []
    present = {
        path.name: path
        for path in vendor_dir.iterdir()
        if path.is_file() and path.name != RECORD_NAME
    }
    for name, digest in sorted(expected.items()):
        path = present.pop(name, None)
        if path is None:
            problems.append(f"{name} is listed in {RECORD_NAME} but missing")
        elif sha256(path) != digest:
            problems.append(f"{name} differs from the synced copy; do not edit vendored files by hand")
    for name in sorted(present):
        problems.append(f"{name} is not part of the synced copy")
    for path in vendor_dir.iterdir():
        if path.is_dir() and path.name != "__pycache__":
            problems.append(f"unexpected folder {path.name}")
    problems += record_problems(vendor_dir)
    return problems


def record_problems(vendor_dir: pathlib.Path = VENDOR_DIR) -> List[str]:
    """Problems with the record's details (empty when it names the dct_link version and the protocol version of the
    copied modules, and a sync date)."""
    text = (vendor_dir / RECORD_NAME).read_text("utf-8")
    problems = []
    recorded = _VERSION_LINE.search(text)
    try:
        actual = package_version(vendor_dir / "__init__.py")
        protocol = protocol_version(vendor_dir / "protocol.py")
    except (OSError, SyncError) as exc:
        return [str(exc)]
    if recorded is None or recorded.group(1) != actual:
        problems.append(f"{RECORD_NAME} does not record dct_link version {actual}; sync again")
    recorded = _PROTOCOL_LINE.search(text)
    if recorded is None or recorded.group(1) != protocol:
        problems.append(f"{RECORD_NAME} does not record protocol {protocol}; sync again")
    synced = _SYNCED_LINE.search(text)
    try:
        if synced is None:
            raise ValueError("no sync date")
        datetime.date.fromisoformat(synced.group(1))
    except ValueError:
        problems.append(f"{RECORD_NAME} records no sync date; sync again")
    return problems


def verify_upstream(source: pathlib.Path, vendor_dir: pathlib.Path = VENDOR_DIR) -> List[str]:
    """Differences between the vendored copy and the dct_link files in a Durty Cloth Tool checkout (empty when the
    copy is up to date): changed or missing files, and modules the add-on now needs or no longer needs."""
    try:
        package = find_package(source)
        wanted = {path.name: path for path in source_files(package)}
    except SyncError as exc:
        return [str(exc)]
    wanted["LICENSE"] = package.parent / "LICENSE"
    vendored = {path.name: path for path in vendor_dir.iterdir() if path.is_file() and path.name != RECORD_NAME}
    problems = []
    for name, upstream in sorted(wanted.items()):
        copy = vendored.pop(name, None)
        if copy is None:
            problems.append(f"{name} is needed upstream but not vendored; sync again")
        elif not upstream.is_file() or upstream.read_bytes() != copy.read_bytes():
            problems.append(f"{name} differs from the upstream file; sync again")
    for name in sorted(vendored):
        problems.append(f"{name} is vendored but no longer needed upstream; sync again")
    return problems


def sync(source: pathlib.Path, vendor_dir: pathlib.Path = VENDOR_DIR,
         today: Optional[datetime.date] = None) -> List[Tuple[str, str]]:
    package = find_package(source)
    license_file = package.parent / "LICENSE"
    files = source_files(package)
    check_source(files, license_file)
    version = package_version(package / "__init__.py")
    protocol = protocol_version(package / "protocol.py")
    synced = (today or datetime.datetime.now(datetime.timezone.utc).date()).isoformat()

    if vendor_dir.exists():
        shutil.rmtree(vendor_dir)
    vendor_dir.mkdir(parents=True)
    hashes = []
    for path in [*files, license_file]:
        target = vendor_dir / path.name
        shutil.copyfile(path, target)
        digest = sha256(path)
        if sha256(target) != digest:
            raise SyncError(f"copying {path.name} changed its bytes")
        hashes.append((path.name, digest))
    hashes.sort()
    record = render_record(version, protocol, synced, hashes)
    (vendor_dir / RECORD_NAME).write_bytes(record.encode("utf-8"))
    return hashes


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("checkout", nargs="?", type=pathlib.Path,
                        help="the Durty Cloth Tool checkout, or the dct_link package folder in it")
    parser.add_argument("--check", action="store_true",
                        help="verify the vendored copy against VENDORED.md and, when available, the checkout")
    args = parser.parse_args(argv)
    try:
        if args.check:
            problems = verify()
            source = args.checkout.resolve() if args.checkout is not None else sibling_package()
            if source is not None:
                problems += verify_upstream(source)
            for problem in problems:
                print(f"error: {problem}", file=sys.stderr)
            if not problems:
                against = f" and {source}" if source is not None else ""
                print(f"dct_link matches VENDORED.md{against}")
            return 1 if problems else 0
        if args.checkout is None:
            parser.error("pass the Durty Cloth Tool checkout, or --check")
        hashes = sync(args.checkout)
    except SyncError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"vendored {len(hashes)} files into {VENDOR_DIR.relative_to(REPO_ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
