# SPDX-License-Identifier: GPL-3.0-or-later
"""The extension manifest and the vendored dct_link copy (no Blender needed)."""

from __future__ import annotations

import pathlib
import shutil
import subprocess
import tomllib

import pytest

from durty_cloth_tool_link import settings
from tools import check_manifest, sync_dct_link


def test_manifest_matches_the_repository_listing_and_blender_rules():
    assert check_manifest.check() == []


def test_manifest_version_is_the_code_version():
    data = tomllib.loads(check_manifest.MANIFEST.read_text("utf-8"))
    assert data["version"] == settings.VERSION
    assert data["id"] == settings.EXTENSION_ID


def test_the_check_notices_a_wrong_manifest(tmp_path):
    text = check_manifest.MANIFEST.read_text("utf-8")
    broken = tmp_path / "blender_manifest.toml"
    broken.write_text(text.replace('maintainer = "DurtyFree (Pleb Masters)"', 'maintainer = "Someone"').replace(
        '''files = "Reads Durty Cloth Tool's endpoint file, writes temporary exports"''',
        'files = "Writes exported models."'), "utf-8")
    problems = check_manifest.check(broken)
    assert any(p.startswith("maintainer") for p in problems)
    assert any("punctuation" in p for p in problems)


def test_vendored_dct_link_matches_its_record():
    assert sync_dct_link.verify() == []


def upstream_package(checkout: pathlib.Path) -> pathlib.Path:
    """A stand-in for the dct_link package in a Durty Cloth Tool checkout, a few folders below its root."""
    package = checkout / "some" / "folder" / sync_dct_link.PACKAGE_NAME
    package.mkdir(parents=True)
    for path in sync_dct_link.VENDOR_DIR.iterdir():
        if path.suffix == ".py":
            (package / path.name).write_bytes(path.read_bytes())
    (package.parent / "LICENSE").write_bytes((sync_dct_link.VENDOR_DIR / "LICENSE").read_bytes())
    return package


def test_the_check_catches_upstream_changes_that_were_not_synced(tmp_path):
    """--check also compares with a Durty Cloth Tool checkout, so a dct_link change upstream is not missed."""
    package = upstream_package(tmp_path)
    assert sync_dct_link.verify_upstream(package) == []

    session = package / "session.py"
    session.write_bytes(session.read_bytes() + b"# changed upstream\n")
    problems = sync_dct_link.verify_upstream(package)
    assert len(problems) == 1 and problems[0].startswith("session.py differs")


def test_the_package_is_found_in_a_checkout(tmp_path):
    """Given a checkout instead of the package folder, the tool asks Git where dct_link is."""
    if shutil.which("git") is None:
        pytest.skip("needs Git")
    package = upstream_package(tmp_path)
    for arguments in (["init", "--quiet"], ["add", "--all"]):
        subprocess.run(["git", "-C", str(tmp_path), *arguments], check=True, capture_output=True, timeout=60)
    assert sync_dct_link.find_package(tmp_path) == package.resolve()
    assert sync_dct_link.verify_upstream(tmp_path) == []

    shutil.copytree(package, tmp_path / "other" / sync_dct_link.PACKAGE_NAME)
    subprocess.run(["git", "-C", str(tmp_path), "add", "--all"], check=True, capture_output=True, timeout=60)
    with pytest.raises(sync_dct_link.SyncError, match="2 dct_link packages"):
        sync_dct_link.find_package(tmp_path)


def test_the_vendored_copy_keeps_its_licence_and_headers():
    vendored = sync_dct_link.VENDOR_DIR
    assert b"MIT License" in (vendored / "LICENSE").read_bytes()
    for module in vendored.glob("*.py"):
        assert module.read_text("utf-8").startswith("# SPDX-License-Identifier: MIT"), module.name


def test_add_on_modules_carry_the_gpl_header():
    package = pathlib.Path(settings.__file__).parent
    for module in package.glob("*.py"):
        assert module.read_text("utf-8").startswith("# SPDX-License-Identifier: GPL-3.0-or-later"), module.name
