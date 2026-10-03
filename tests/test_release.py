# SPDX-License-Identifier: GPL-3.0-or-later
"""The release checks (tools/release_tool.py) the release workflow relies on. Durty Cloth Tool pins a released
archive by version, URL, size and SHA-256, so a release under the wrong version, a wrong archive or a build that
depends on the checkout time would break or poison that pin."""

from __future__ import annotations

import pathlib
import time
import zipfile

import pytest

from tools import check_manifest, release_tool


def _manifest_with_version(tmp_path, monkeypatch, version):
    text = check_manifest.MANIFEST.read_text("utf-8")
    current = f'version = "{check_manifest.code_version()}"'
    assert current in text
    manifest = tmp_path / "blender_manifest.toml"
    manifest.write_text(text.replace(current, f'version = "{version}"'), "utf-8")
    monkeypatch.setattr(check_manifest, "code_version", lambda: version)
    return manifest


def test_the_tag_must_be_v_plus_the_manifest_version(tmp_path, monkeypatch):
    manifest = _manifest_with_version(tmp_path, monkeypatch, "1.2.3")
    assert release_tool.identity("v1.2.3", manifest) == {
        "version": "1.2.3", "file": "durty_cloth_tool_link-1.2.3.zip", "channel": "release", "prerelease": "false"}
    for tag in ("1.2.3", "v1.2.4", "v1.2.3-experimental.1", "refs/tags/v1.2.3"):
        with pytest.raises(release_tool.ReleaseError):
            release_tool.identity(tag, manifest)


def test_an_experimental_version_is_a_prerelease(tmp_path, monkeypatch):
    manifest = _manifest_with_version(tmp_path, monkeypatch, "1.3.0-experimental.2")
    identity = release_tool.identity("v1.3.0-experimental.2", manifest)
    assert identity["channel"] == "experimental" and identity["prerelease"] == "true"
    assert identity["file"] == "durty_cloth_tool_link-1.3.0-experimental.2.zip"


@pytest.mark.parametrize("version", ["1.2", "01.2.3", "1.2.3-beta.1", "1.2.3-experimental.0", "1.2.3-experimental"])
def test_versions_outside_the_plugin_grammar_are_refused(tmp_path, monkeypatch, version):
    manifest = _manifest_with_version(tmp_path, monkeypatch, version)
    with pytest.raises(release_tool.ReleaseError):
        release_tool.identity(f"v{version}", manifest)


def _archive(path: pathlib.Path, version: str, extra: dict | None = None) -> pathlib.Path:
    manifest = check_manifest.MANIFEST.read_text("utf-8").replace(
        f'version = "{check_manifest.code_version()}"', f'version = "{version}"')
    files = {name: b"x" for name in release_tool.REQUIRED_FILES}
    files["blender_manifest.toml"] = manifest.encode("utf-8")
    files["LICENSE"] = (check_manifest.REPO_ROOT / "LICENSE").read_bytes()
    files.update(extra or {})
    with zipfile.ZipFile(path, "w") as archive:
        for name, data in files.items():
            archive.writestr(name, data)
    return path


def test_the_release_archive_is_checked(tmp_path):
    good = _archive(tmp_path / "durty_cloth_tool_link-1.2.3.zip", "1.2.3")
    assert release_tool.archive_problems(good, "1.2.3") == []

    problems = release_tool.archive_problems(good, "1.2.4")
    assert any("named" in p for p in problems) and any("version" in p for p in problems)

    (tmp_path / "leaky").mkdir()
    leaky = _archive(tmp_path / "leaky" / "durty_cloth_tool_link-1.2.3.zip", "1.2.3", {
        "__pycache__/link.cpython-313.pyc": b"x", ".env": b"x"})
    problems = release_tool.archive_problems(leaky, "1.2.3")
    assert len([p for p in problems if "excluded" in p]) == 2


def test_stamped_files_read_as_the_commit_time_in_utc(tmp_path):
    package = tmp_path / "package"
    (package / "sub").mkdir(parents=True)
    (package / "a.py").write_text("a", "utf-8")
    (package / "sub" / "b.py").write_text("b", "utf-8")
    commit_time = 1790000000
    assert release_tool.stamp(commit_time, package) == 2
    for path in (package / "a.py", package / "sub" / "b.py"):
        # What zipfile records for the file: its local modification time.
        assert zipfile.ZipInfo.from_file(path).date_time == time.gmtime(commit_time)[:6]
    with pytest.raises(release_tool.ReleaseError):
        release_tool.stamp(0, package)
