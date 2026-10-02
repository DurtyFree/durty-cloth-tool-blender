#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2026 Schmid Software Solutions (https://schmid-software.de)
"""Vendors dct_link, the Creator Link client, from a Durty Cloth Tool checkout.

    python tools/sync_dct_link.py <path to the Durty Cloth Tool checkout>
    python tools/sync_dct_link.py --check

The first form replaces ``durty_cloth_tool_link/dct_link`` with the modules the add-on uses from
``plugins/python/dct_link`` in the checkout: the allowlist in ``ROOT_MODULES`` plus every module they import.
The self-update modules (updater, loader, signed manifests and their keys) are left out because Blender updates
the add-on itself. The MIT ``LICENSE`` is copied next to them and ``VENDORED.md`` records the SHA-256 of every
copied file. Each file is copied byte for byte: never edit the vendored files by hand, change dct_link upstream
and sync again.

``--check`` verifies the vendored copy against ``VENDORED.md`` (the test suite runs the same check).

Standard library only.
"""

from __future__ import annotations

import argparse
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
SOURCE_PACKAGE = pathlib.PurePosixPath("plugins/python/dct_link")
SOURCE_LICENSE = pathlib.PurePosixPath("plugins/python/LICENSE")
#: The modules the add-on imports; whatever they import from dct_link is added automatically.
ROOT_MODULES = ("__init__", "protocol", "ws", "session", "auth", "tokens")
SPDX_MIT = "# SPDX-License-Identifier: MIT"
NOT_RECORDED = ("not recorded yet: the sync records the Durty Cloth Tool commit once plugins/python/dct_link is "
                "committed there unchanged")
_ROW = re.compile(r"^\| `([^`]+)` \| `([0-9a-f]{64})` \|$")
_RELATIVE_IMPORT = re.compile(r"^[ \t]*from[ \t]+\.(\w*)[ \t]+import[ \t]+(\([^)]*\)|[\w \t,]+)", re.MULTILINE)


class SyncError(Exception):
    """The source or the vendored copy is not what the tool expects."""


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def imported_modules(source: str) -> List[str]:
    """The dct_link modules a module imports with relative imports (``from . import x``, ``from .x import y``)."""
    names = []
    for module, imported in _RELATIVE_IMPORT.findall(source):
        if module:
            names.append(module)
        else:
            names.extend(n.strip() for n in imported.replace("(", "").replace(")", "").split(",") if n.strip())
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


def source_revision(checkout: pathlib.Path) -> str:
    """The checkout's commit when the package is committed there unchanged, otherwise a plain note."""
    try:
        head = subprocess.run(["git", "-C", str(checkout), "rev-parse", "HEAD"], capture_output=True, text=True,
                              check=True, timeout=30).stdout.strip()
        tracked = subprocess.run(["git", "-C", str(checkout), "ls-files", "--", str(SOURCE_PACKAGE)],
                                 capture_output=True, text=True, check=True, timeout=30).stdout.strip()
        changes = subprocess.run(["git", "-C", str(checkout), "status", "--porcelain", "--", str(SOURCE_PACKAGE)],
                                 capture_output=True, text=True, check=True, timeout=30).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return NOT_RECORDED
    if not re.fullmatch(r"[0-9a-f]{40}", head) or not tracked or changes:
        return NOT_RECORDED
    return head


def left_out_files(package: pathlib.Path, shipped: List[pathlib.Path]) -> List[str]:
    """The package's modules and data files that are not vendored (the self-update parts)."""
    names = {path.name for path in shipped}
    return sorted(
        path.name
        for path in package.iterdir()
        if path.is_file() and path.suffix in (".py", ".json") and path.name not in names
    )


def render_record(version: str, revision: str, hashes: List[Tuple[str, str]], left_out: List[str]) -> str:
    lines = [
        "# Vendored dct_link",
        "",
        "This folder holds byte-for-byte copies of the `dct_link` modules the add-on uses. `dct_link` is the Creator",
        "Link client that Durty Cloth Tool shares between its Python host plugins; its self-update modules are left",
        "out because Blender updates the add-on. It is MIT licensed (see `LICENSE` in this folder); every module",
        "keeps its SPDX header. The rest of the add-on is GPL-3.0-or-later.",
        "",
        "Do not edit these files by hand. Change dct_link upstream, then run",
        "`python tools/sync_dct_link.py <Durty Cloth Tool checkout>`, which rewrites this folder and this record.",
        "`python tools/sync_dct_link.py --check` and the test suite verify the hashes below.",
        "",
        f"- Source: `{SOURCE_PACKAGE}` and `{SOURCE_LICENSE}` in the Durty Cloth Tool repository",
        f"- dct_link version: {version}",
        f"- Source revision: {revision}",
    ]
    if left_out:
        lines += [
            "- Left out: " + ", ".join(f"`{name}`" for name in left_out) + ". The package description in",
            "  `__init__.py` still names them, because it describes the whole dct_link package; nothing in the add-on",
            "  imports them.",
        ]
    lines += [
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
    return problems


def sync(checkout: pathlib.Path, vendor_dir: pathlib.Path = VENDOR_DIR) -> List[Tuple[str, str]]:
    checkout = checkout.resolve()
    package = checkout / SOURCE_PACKAGE
    license_file = checkout / SOURCE_LICENSE
    files = source_files(package)
    check_source(files, license_file)
    version = package_version(package / "__init__.py")
    revision = source_revision(checkout)

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
    record = render_record(version, revision, hashes, left_out_files(package, files))
    (vendor_dir / RECORD_NAME).write_bytes(record.encode("utf-8"))
    return hashes


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("checkout", nargs="?", type=pathlib.Path, help="the Durty Cloth Tool checkout")
    parser.add_argument("--check", action="store_true", help="verify the vendored copy against VENDORED.md")
    args = parser.parse_args(argv)
    try:
        if args.check:
            problems = verify()
            for problem in problems:
                print(f"error: {problem}", file=sys.stderr)
            if not problems:
                print("dct_link matches VENDORED.md")
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
