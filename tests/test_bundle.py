# SPDX-License-Identifier: GPL-3.0-or-later
"""Collecting a Sollumz export into a model push (no Blender needed)."""

from __future__ import annotations

import pathlib

import pytest

from durty_cloth_tool_link import bundle
from durty_cloth_tool_link.dct_link import protocol


def write(path: pathlib.Path, data: bytes = b"x") -> pathlib.Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


def sollumz_export(folder: pathlib.Path) -> None:
    """The layout Sollumz writes for a drawable dictionary with embedded textures (CodeWalker XML, one target)."""
    write(folder / "jbib_003_u.ydd.xml", b"<DrawableDictionary />")
    write(folder / "jbib_003_u" / "jbib_diff_003_a_uni.dds", b"DDS a")
    write(folder / "jbib_003_u" / "jbib_normal_003.dds", b"DDS n")


def test_model_and_textures_are_collected_under_bare_names(tmp_path):
    sollumz_export(tmp_path)
    write(tmp_path / "jbib_003_u.ytyp.xml")
    model_bundle, collected = bundle.build_bundle(tmp_path)
    assert model_bundle.format == "ydd-xml"
    assert [entry["name"] for entry in model_bundle.entries()] == [
        "jbib_003_u.ydd.xml",
        "jbib_diff_003_a_uni.dds",
        "jbib_normal_003.dds",
    ]
    assert bytes(model_bundle.files[0][1]) == b"<DrawableDictionary />"
    assert model_bundle.size == len(b"<DrawableDictionary />") + 10
    assert collected.ignored == ["jbib_003_u.ytyp.xml"]
    assert protocol.model_push_problem("ydd-xml", model_bundle.entries()) is None


def test_a_model_without_textures_is_fine(tmp_path):
    write(tmp_path / "hat.ydd.xml")
    model_bundle, _ = bundle.build_bundle(tmp_path)
    assert [e["name"] for e in model_bundle.entries()] == ["hat.ydd.xml"]


def test_nothing_exported(tmp_path):
    with pytest.raises(bundle.BundleError, match="did not export a model"):
        bundle.collect(tmp_path)


def test_a_drawable_without_dictionary_is_explained(tmp_path):
    write(tmp_path / "jbib_003_u.ydr.xml")
    with pytest.raises(bundle.BundleError, match="Drawable Dictionary"):
        bundle.collect(tmp_path)


def test_two_dictionaries_are_refused(tmp_path):
    write(tmp_path / "a.ydd.xml")
    write(tmp_path / "b.ydd.xml")
    with pytest.raises(bundle.BundleError, match=r"several drawable dictionaries \(2\)"):
        bundle.collect(tmp_path)


@pytest.mark.parametrize("name", ["jbib diff.dds", "über.dds", ".hidden.dds", "a..b.dds", "x" * 126 + ".dds"])
def test_names_the_protocol_refuses_are_explained(tmp_path, name):
    write(tmp_path / "m.ydd.xml")
    write(tmp_path / "m" / name)
    with pytest.raises(bundle.BundleError, match="cannot be sent"):
        bundle.collect(tmp_path)


def test_texture_names_must_differ_ignoring_case(tmp_path):
    write(tmp_path / "m.ydd.xml")
    write(tmp_path / "m" / "Diff.dds")
    write(tmp_path / "other" / "diff.DDS")
    with pytest.raises(bundle.BundleError, match="Two textures"):
        bundle.collect(tmp_path)


def test_empty_files_are_refused(tmp_path):
    write(tmp_path / "m.ydd.xml")
    write(tmp_path / "m" / "a.dds", b"")
    with pytest.raises(bundle.BundleError, match="is empty"):
        bundle.collect(tmp_path)


def test_at_most_256_files(tmp_path):
    write(tmp_path / "m.ydd.xml")
    for index in range(protocol.MAX_MODEL_FILES):
        write(tmp_path / "m" / f"t{index}.dds")
    with pytest.raises(bundle.BundleError, match="at most 255"):
        bundle.collect(tmp_path)


def test_255_textures_fit(tmp_path):
    write(tmp_path / "m.ydd.xml")
    for index in range(protocol.MAX_MODEL_FILES - 1):
        write(tmp_path / "m" / f"t{index}.dds")
    model_bundle, _ = bundle.build_bundle(tmp_path)
    assert len(model_bundle.entries()) == protocol.MAX_MODEL_FILES


def test_the_size_limit_is_enforced(tmp_path, monkeypatch):
    monkeypatch.setattr(protocol, "MAX_BINARY_PAYLOAD_BYTES", 10)
    write(tmp_path / "m.ydd.xml", b"123456")
    write(tmp_path / "m" / "a.dds", b"12345")
    with pytest.raises(bundle.BundleError, match="larger than"):
        bundle.collect(tmp_path)


def test_bundle_error_is_a_value_error():
    assert issubclass(bundle.BundleError, ValueError)
