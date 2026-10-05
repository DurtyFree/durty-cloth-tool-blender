#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2026 Schmid Software Solutions (https://schmid-software.de)
"""Validates, builds and smoke-tests the extension with installed Blender versions.

    python tools/blender_smoke.py --blender "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe"
        [--blender <another blender>] [--sollumz <Sollumz extension folder> --sollumz-site <its site-packages>]

For each Blender: ``blender --command extension validate`` on the source, ``blender --command extension build``
into ``dist/``, ``validate`` on the archive, then ``tests/blender/smoke_in_blender.py`` in
``--background --factory-startup --online-mode`` with ``BLENDER_USER_RESOURCES`` pointing at a fresh temporary
folder, so the run never touches your Blender settings or extensions. The fakes listen on 127.0.0.1 only and
nothing is sent to gta.clothing.

With ``--sollumz`` the smoke also runs against a real Sollumz copied from an existing installation (the folder
that holds Sollumz's ``blender_manifest.toml``; ``--sollumz-site`` is the folder with its ``szio`` package).
Standard library only.
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
from typing import Dict, List, Optional

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
SOURCE = REPO_ROOT / "durty_cloth_tool_link"
DIST = REPO_ROOT / "dist"
SMOKE = REPO_ROOT / "tests" / "blender" / "smoke_in_blender.py"


#: Blender's variables that point single user folders elsewhere; each would beat BLENDER_USER_RESOURCES and could
#: reach the real profile, so the child never inherits them.
USER_FOLDER_VARIABLES = ("BLENDER_USER_CONFIG", "BLENDER_USER_SCRIPTS", "BLENDER_USER_EXTENSIONS",
                         "BLENDER_USER_DATAFILES")


def isolated_environment(user: str) -> Dict[str, str]:
    """The environment for a Blender that must use only the throw-away user folder ``user``."""
    env = dict(os.environ, BLENDER_USER_RESOURCES=user)
    for name in ("PYTHONPATH", *USER_FOLDER_VARIABLES):
        env.pop(name, None)
    return env


def run(command: List[str], env: Dict[str, str], timeout: float = 300) -> subprocess.CompletedProcess:
    return subprocess.run(command, cwd=REPO_ROOT, env=env, capture_output=True, text=True, timeout=timeout,
                          encoding="utf-8", errors="replace")


def blender_version(blender: str, env: Dict[str, str]) -> str:
    result = run([blender, "--factory-startup", "--version"], env, timeout=120)
    lines = [line for line in result.stdout.splitlines() if line.startswith("Blender ")]
    return lines[0].strip() if lines else "unknown"


def smoke_one(blender: str, sollumz: Optional[str], sollumz_site: Optional[str], verbose: bool) -> Dict[str, object]:
    user = tempfile.mkdtemp(prefix="dct_smoke_user_")
    env = isolated_environment(user)
    summary: Dict[str, object] = {"blender": blender_version(blender, env), "steps": []}
    steps: List[Dict[str, object]] = summary["steps"]  # type: ignore[assignment]

    def step(name: str, result: subprocess.CompletedProcess) -> bool:
        ok = result.returncode == 0
        steps.append({"step": name, "ok": ok})
        print(f"  {'ok  ' if ok else 'FAIL'} {name}")
        if not ok or verbose:
            print(result.stdout[-4000:])
            print(result.stderr[-4000:])
        return ok

    try:
        command = [blender, "--factory-startup", "--command", "extension"]
        if not step("validate source", run(command + ["validate", str(SOURCE)], env)):
            return summary
        DIST.mkdir(exist_ok=True)
        if not step("build", run(command + ["build", "--source-dir", str(SOURCE), "--output-dir", str(DIST)], env)):
            return summary
        archives = sorted(DIST.glob("durty_cloth_tool_link-*.zip"), key=lambda p: p.stat().st_mtime)
        archive = archives[-1]
        summary["archive"] = archive.name
        if not step("validate archive", run(command + ["validate", str(archive)], env)):
            return summary
        report = pathlib.Path(user) / "smoke-report.json"
        smoke = [blender, "--background", "--factory-startup", "--online-mode", "--python", str(SMOKE), "--",
                 "--zip", str(archive), "--report", str(report)]
        if sollumz:
            smoke += ["--sollumz", sollumz, "--sollumz-site", sollumz_site or ""]
        result = run(smoke, env, timeout=600)
        step("smoke (Sollumz: " + ("real" if sollumz else "stand-in") + ")", result)
        if report.is_file():
            data = json.loads(report.read_text("utf-8"))
            summary["smoke"] = data
            failed = [r for r in data["results"] if not r["ok"]]
            print(f"  {len(data['results']) - len(failed)} checks passed, {len(failed)} failed")
            for failure in failed:
                print(f"    FAIL {failure['check']}: {failure['detail']}")
            for entry in data["results"]:
                reported = ("pushed files", "uninstalling removes the user folder")
                if entry["check"] in reported or entry["check"].startswith("undo"):
                    print(f"  {entry['check']}: {entry['detail']}")
        return summary
    finally:
        shutil.rmtree(user, ignore_errors=True)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--blender", action="append", required=True, help="a blender executable (repeatable)")
    parser.add_argument("--sollumz", help="an installed Sollumz extension folder (optional)")
    parser.add_argument("--sollumz-site", help="the folder with Sollumz's szio package (with --sollumz)")
    parser.add_argument("--verbose", action="store_true", help="print Blender's output for every step")
    args = parser.parse_args(argv)
    if args.sollumz and not args.sollumz_site:
        parser.error("--sollumz needs --sollumz-site")
    all_ok = True
    for blender in args.blender:
        print(f"{blender}")
        runs = [None] + ([args.sollumz] if args.sollumz else [])
        for sollumz in runs:
            summary = smoke_one(blender, sollumz, args.sollumz_site, args.verbose)
            print(f"  {summary['blender']}")
            steps = summary["steps"]
            ok = bool(steps) and all(s["ok"] for s in steps) and len(steps) == 4  # type: ignore[union-attr]
            all_ok = all_ok and ok
    print("all smoke runs passed" if all_ok else "a smoke run failed")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
