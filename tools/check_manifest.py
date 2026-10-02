#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2026 Schmid Software Solutions (https://schmid-software.de)
"""Checks blender_manifest.toml without Blender: TOML syntax, the values the gta.clothing repository listing
must match, the version, and the rules Blender applies to taglines and permission texts.

    python tools/check_manifest.py

Standard library only (Python 3.11 or later for tomllib). ``blender --command extension validate`` is the
full check; this one runs anywhere, including CI.
"""

from __future__ import annotations

import pathlib
import re
import sys
import tomllib
from typing import Any, Dict, List

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
PACKAGE_DIR = REPO_ROOT / "durty_cloth_tool_link"
MANIFEST = PACKAGE_DIR / "blender_manifest.toml"

#: What the Durty Cloth Tool extension repository on gta.clothing lists for this add-on (BLENDER_EXTENSION in the
#: website's worker/link/hosts.js; the website's tests compare every field with this manifest).
EXPECTED: Dict[str, Any] = {
    "schema_version": "1.0.0",
    "id": "durty_cloth_tool_link",
    "name": "Durty Cloth Tool Link",
    "tagline": "Preview and save your models in Durty Cloth Tool",
    "maintainer": "DurtyFree (Pleb Masters)",
    "type": "add-on",
    "license": ["SPDX:GPL-3.0-or-later"],
    "website": "https://docs.gta.clothing/creator-link/blender",
    "tags": ["Import-Export", "Paint"],
    "platforms": ["windows-x64"],
    "blender_version_min": "4.2.0",
    "copyright": ["2026 Schmid Software Solutions"],
    "permissions": {
        "network": "Durty Cloth Tool on this computer and gta.clothing for sign-in",
        "files": "Reads Durty Cloth Tool's endpoint file, writes temporary exports",
    },
}
TERSE_LIMIT = 64  # Blender's limit for taglines and permission texts


def _terse_problem(field: str, value: Any) -> List[str]:
    if not isinstance(value, str) or not value.strip():
        return [f"{field} must be a non-empty string"]
    problems = []
    if len(value) > TERSE_LIMIT:
        problems.append(f"{field} is {len(value)} characters; Blender allows {TERSE_LIMIT}")
    if not (value[-1].isalnum() or value[-1] in ")]}"):
        problems.append(f"{field} must not end with punctuation")
    if chr(0x2014) in value:  # an em dash
        problems.append(f"{field} contains an em dash")
    return problems


def code_version() -> str:
    text = (PACKAGE_DIR / "settings.py").read_text("utf-8")
    match = re.search(r'^VERSION = "([^"]+)"', text, re.MULTILINE)
    return match.group(1) if match else ""


def check(manifest_path: pathlib.Path = MANIFEST) -> List[str]:
    try:
        data = tomllib.loads(manifest_path.read_text("utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        return [f"{manifest_path.name} cannot be read: {exc}"]
    problems = []
    for key, value in EXPECTED.items():
        if data.get(key) != value:
            problems.append(f"{key} is {data.get(key)!r}, expected {value!r}")
    version = data.get("version")
    if not isinstance(version, str) or not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+(-experimental\.[0-9]+)?", version):
        problems.append(f"version {version!r} is not major.minor.patch (optionally -experimental.N)")
    elif version != code_version():
        problems.append(f"version {version} differs from VERSION {code_version()!r} in settings.py")
    problems += _terse_problem("tagline", data.get("tagline"))
    for name, text in (data.get("permissions") or {}).items():
        problems += _terse_problem(f"permissions.{name}", text)
    for copyright_text in data.get("copyright", []):
        if not re.fullmatch(r"[0-9]{4}(-[0-9]{4})? \S.*", copyright_text):
            problems.append(f"copyright {copyright_text!r} must be 'YEAR Name'")
    if (PACKAGE_DIR / "LICENSE").read_bytes() != (REPO_ROOT / "LICENSE").read_bytes():
        problems.append("durty_cloth_tool_link/LICENSE must equal the repository's LICENSE")
    return problems


def main() -> int:
    problems = check()
    for problem in problems:
        print(f"error: {problem}", file=sys.stderr)
    if not problems:
        print(f"{MANIFEST.relative_to(REPO_ROOT).as_posix()} is valid")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
