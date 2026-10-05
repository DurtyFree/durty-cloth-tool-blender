#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2026 Schmid Software Solutions (https://schmid-software.de)
"""The release workflow's checks (.github/workflows/release.yml), runnable anywhere:

    python tools/release_tool.py identity --tag v0.1.0
    python tools/release_tool.py stamp --time <commit time, Unix seconds>
    python tools/release_tool.py archive dist/durty_cloth_tool_link-0.1.0.zip --version 0.1.0
    python tools/release_tool.py notes --version 0.1.0 --sha256 <hex> --size <bytes> --commit <sha> --blender 4.5.9

``identity`` refuses a tag that is not ``v`` plus the version in blender_manifest.toml (which must also equal
VERSION in settings.py and follow the plugin version grammar, X.Y.Z or X.Y.Z-experimental.N) and prints the
release identity as ``key=value`` lines for $GITHUB_OUTPUT. ``stamp`` gives every file of the add-on the same
modification time, so the archive does not depend on when the files were checked out: Blender's build stores each
file's local modification time, and the stamp makes that read as the commit time in UTC in any time zone.
``archive`` checks the archive Blender built: its name, the manifest inside it, the licence and notice files, the
logo, and that nothing excluded slipped in; it prints its size and SHA-256. ``notes`` prints the release notes.

Durty Cloth Tool's plugin release pins this archive by version, URL, size and SHA-256 (its plugins/release/
blender.json), so a published asset is never replaced. Standard library only (Python 3.11 or later).
"""

from __future__ import annotations

import argparse
import hashlib
import os
import pathlib
import sys
import time
import tomllib
import zipfile
from typing import Dict, List

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from tools import check_manifest  # noqa: E402

EXTENSION_ID = check_manifest.EXPECTED["id"]
MAX_ARCHIVE_BYTES = 256 * 1024 * 1024  # what Durty Cloth Tool's pin accepts
#: Files every archive must carry at its root (Blender extensions keep the manifest at the root).
REQUIRED_FILES = ("blender_manifest.toml", "__init__.py", "LICENSE", "NOTICE", "icons/dct-mark.png",
                  "dct_link/LICENSE", "translations/__init__.py")


class ReleaseError(Exception):
    pass


def archive_name(version: str) -> str:
    return f"{EXTENSION_ID}-{version}.zip"


def identity(tag: str, manifest_path: pathlib.Path = check_manifest.MANIFEST) -> Dict[str, str]:
    problems = check_manifest.check(manifest_path)
    if problems:
        raise ReleaseError("the manifest is not releasable: " + "; ".join(problems))
    version = tomllib.loads(manifest_path.read_text("utf-8"))["version"]
    match = check_manifest.VERSION_PATTERN.fullmatch(version)
    if match is None:  # check() refuses it already; kept for a direct call
        raise ReleaseError(f"version {version!r} is not X.Y.Z or X.Y.Z-experimental.N")
    if tag != f"v{version}":
        raise ReleaseError(f"the tag {tag!r} is not v{version}, the version in blender_manifest.toml")
    experimental = match.group("ordinal") is not None
    return {
        "version": version,
        "file": archive_name(version),
        "channel": "experimental" if experimental else "release",
        "prerelease": "true" if experimental else "false",
    }


def stamp(commit_time: int, package_dir: pathlib.Path = check_manifest.PACKAGE_DIR) -> int:
    """Sets every file under ``package_dir`` to a modification time that the local time zone shows as the commit
    time in UTC (what a zip entry records). Returns the number of files."""
    if not 315532800 <= commit_time < 4102444800:  # zip timestamps start in 1980; refuse nonsense
        raise ReleaseError(f"the commit time {commit_time} is out of range")
    local = time.mktime(time.gmtime(commit_time)[:8] + (-1,))
    count = 0
    for path in sorted(package_dir.rglob("*")):
        if path.is_file():
            os.utime(path, (local, local))
            count += 1
    return count


def sha256_of(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def archive_problems(path: pathlib.Path, version: str) -> List[str]:
    """Why the archive Blender built is not the release archive of ``version``."""
    problems = []
    if path.name != archive_name(version):
        problems.append(f"the archive is named {path.name}, expected {archive_name(version)}")
    size = path.stat().st_size
    if not 0 < size <= MAX_ARCHIVE_BYTES:
        problems.append(f"the archive is {size} bytes; it must be between 1 byte and {MAX_ARCHIVE_BYTES}")
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        for name in names:
            parts = name.split("/")
            if name.startswith("/") or ".." in parts or "\\" in name:
                problems.append(f"{name!r} is not a plain relative path")
            if "__pycache__" in parts or name.endswith((".pyc", ".pyo")) or any(p.startswith(".") for p in parts if p):
                problems.append(f"{name!r} should have been excluded")
        for required in REQUIRED_FILES:
            if required not in names:
                problems.append(f"the archive has no {required}")
        if "blender_manifest.toml" in names:
            manifest = tomllib.loads(archive.read("blender_manifest.toml").decode("utf-8"))
            for key in ("id", "blender_version_min", "platforms", "license"):
                if manifest.get(key) != check_manifest.EXPECTED[key]:
                    problems.append(f"the archive's {key} is {manifest.get(key)!r}")
            if manifest.get("version") != version:
                problems.append(f"the archive's version is {manifest.get('version')!r}, not {version}")
        if "LICENSE" in names and b"GNU GENERAL PUBLIC LICENSE" not in archive.read("LICENSE"):
            problems.append("the archive's LICENSE is not the GPL")
    return problems


def notes(version: str, sha256: str, size: int, commit: str, blender: str) -> str:
    experimental = "-experimental." in version
    channel = "Experimental" if experimental else "Release"
    return "\n".join([
        f"Durty Cloth Tool Link {version} ({channel}) for Blender 4.2 or later on Windows (x64).",
        "",
        "| Asset | Size | SHA-256 |",
        "|---|---|---|",
        f"| `{archive_name(version)}` | {size} bytes | `{sha256}` |",
        "",
        "Install it by dragging the Blender install link from the plugins page of your gta.clothing account "
        "(https://gta.clothing/account/plugins/) onto Blender; Blender then keeps it up to date. This archive is "
        "the same add-on for Install from Disk.",
        "",
        f"Built from {commit} with Blender {blender} (`blender --command extension build`), file times set to the "
        "commit time.",
        "",
    ])


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    command = commands.add_parser("identity")
    command.add_argument("--tag", required=True)
    command = commands.add_parser("stamp")
    command.add_argument("--time", required=True, type=int)
    command = commands.add_parser("archive")
    command.add_argument("path", type=pathlib.Path)
    command.add_argument("--version", required=True)
    command = commands.add_parser("notes")
    command.add_argument("--version", required=True)
    command.add_argument("--sha256", required=True)
    command.add_argument("--size", required=True, type=int)
    command.add_argument("--commit", required=True)
    command.add_argument("--blender", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "identity":
            for key, value in identity(args.tag).items():
                print(f"{key}={value}")
        elif args.command == "stamp":
            print(f"stamped {stamp(args.time)} files")
        elif args.command == "archive":
            problems = archive_problems(args.path, args.version)
            if problems:
                raise ReleaseError("; ".join(problems))
            print(f"sha256={sha256_of(args.path)}")
            print(f"size={args.path.stat().st_size}")
        else:
            sys.stdout.write(notes(args.version, args.sha256, args.size, args.commit, args.blender))
    except ReleaseError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
