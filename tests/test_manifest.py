# SPDX-License-Identifier: GPL-3.0-or-later
"""The extension manifest and the vendored dct_link copy (no Blender needed)."""

from __future__ import annotations

import pathlib
import tomllib

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


def test_the_vendored_copy_keeps_its_licence_and_headers():
    vendored = sync_dct_link.VENDOR_DIR
    assert b"MIT License" in (vendored / "LICENSE").read_bytes()
    for module in vendored.glob("*.py"):
        assert module.read_text("utf-8").startswith("# SPDX-License-Identifier: MIT"), module.name


def test_add_on_modules_carry_the_gpl_header():
    package = pathlib.Path(settings.__file__).parent
    for module in package.glob("*.py"):
        assert module.read_text("utf-8").startswith("# SPDX-License-Identifier: GPL-3.0-or-later"), module.name
