# SPDX-License-Identifier: GPL-3.0-or-later
"""Reading the Reference Data Pack's files: the index, the cuts GLB and the poses, on a synthetic pack made in the
tests (no game data, no Blender needed)."""

from __future__ import annotations

import json

import numpy as np
import pytest

from durty_cloth_tool_link import garment_reference as ref
from tests.support import synthetic, synthetic_pack


@pytest.fixture(scope="module")
def pack():
    return synthetic_pack.files()


def test_the_index_names_the_files_and_the_cuts_of_each_gender(pack):
    index = ref.parse_index(pack["reference.json"])
    assert index.notice == "NOTICE.txt" and index.skeleton == "skeleton.json"
    assert set(index.genders) == {"female", "male"}
    assert index.files() == ["NOTICE.txt", "skeleton.json", "cuts_female.glb", "poses_female.json",
                             "cuts_male.glb", "poses_male.json"]
    male = index.genders["male"]
    assert male.default_cut == "full" and male.parts == ("head", "lowr", "feet")
    assert male.upper_body[0] == ref.Cut("full", "uppr_full", "uppr_full_arms", "full_body", 1)
    assert male.upper_body[-1] == ref.Cut("heist_02", "uppr_heist_02", None, "long_sleeves_open_neck", 1)


@pytest.mark.parametrize("change", [
    lambda v: v.update(format=2),
    lambda v: v["genders"].update(other=v["genders"]["male"]),
    lambda v: v["genders"]["male"].update(cuts="../cuts.glb"),
    lambda v: v["genders"]["male"].update(defaultCut="missing"),
    lambda v: v["genders"]["male"]["upperBody"][1].update(node="uppr_other"),
    lambda v: v["genders"]["male"]["upperBody"][1].update(armsNode="uppr_full_arms"),
    lambda v: v["genders"]["male"]["upperBody"][1].update(id="Bad Id"),
    lambda v: v["genders"]["male"]["upperBody"][1].update(displayIndex=0),
    lambda v: v["genders"]["male"]["upperBody"].append(dict(v["genders"]["male"]["upperBody"][0])),
    lambda v: v.update(genders={}),
    # A name that is the index's or the add-on's record in another case would overwrite it on Windows.
    lambda v: v["genders"]["male"].update(cuts="Reference.json"),
    lambda v: v.update(skeleton="REFERENCE.json"),
    # Two names that differ only in case are one file on Windows.
    lambda v: v["genders"]["male"].update(poses="Poses_female.json"),
    lambda v: v.update(notice="Skeleton.json"),
])
def test_an_index_outside_format_1_is_refused(pack, change):
    value = json.loads(pack["reference.json"])
    change(value)
    with pytest.raises(ref.PackError):
        ref.parse_index(json.dumps(value).encode())


def test_a_file_both_genders_share_by_the_same_name_is_read(pack):
    value = json.loads(pack["reference.json"])
    value["genders"]["male"]["poses"] = value["genders"]["female"]["poses"]
    index = ref.parse_index(json.dumps(value).encode())
    assert index.genders["male"].poses == index.genders["female"].poses == "poses_female.json"


def test_the_cuts_come_back_in_ped_space_by_node(pack):
    cuts = ref.read_cuts(pack["cuts_male.glb"])
    assert {"head", "lowr", "feet", "uppr_full", "uppr_full_arms", "uppr_heist_02"} <= set(cuts)
    assert "uppr_heist_02_arms" not in cuts
    expected, faces = synthetic_pack.box((0, -0.04, -0.97), (0.3, 0.2, 0.06))
    positions, triangles = cuts["feet"]
    assert np.allclose(positions, expected, atol=1e-6)  # back from the glTF space, Z up again
    assert np.array_equal(triangles, faces)


def test_a_cuts_file_that_is_not_a_plain_glb_is_refused(pack):
    with pytest.raises(ref.PackError):
        ref.read_cuts(b"<html>")
    data = bytearray(pack["cuts_male.glb"])
    data[-200:] = bytes(200)  # the data ends early: triangles point past the vertices or past the end
    cut_short = bytes(data[:-100])
    with pytest.raises(ref.PackError):
        ref.read_cuts(cut_short)


def test_the_poses_are_skinning_matrices_per_pose_and_bone(pack):
    poses = ref.read_poses(pack["poses_male.json"])
    assert poses.labels == ("idle@0", "climb@0.5", "sit@0.5")
    assert poses.bones == tuple(synthetic.skeleton_names())
    assert poses.matrices.shape == (3, len(synthetic.SKELETON_BONES), 4, 4)
    assert np.allclose(poses.matrices[0], np.eye(4))
    hand = poses.bones.index("SKEL_L_Hand")
    shoulder = np.array([*synthetic.joints_of()["SKEL_L_UpperArm"], 1.0])
    assert np.allclose(poses.matrices[1, hand] @ shoulder, shoulder)  # the arm turns about its shoulder
    assert not np.allclose(poses.matrices[1, hand], np.eye(4))


@pytest.mark.parametrize("change", [
    lambda v: v.update(matrix="column-major"),
    lambda v: v["poses"][0]["matrices"].pop(),
    lambda v: v["poses"][0]["matrices"][0].append(1.0),
    lambda v: v.update(poses=[]),
])
def test_poses_outside_format_1_are_refused(pack, change):
    value = json.loads(pack["poses_male.json"])
    change(value)
    with pytest.raises(ref.PackError):
        ref.read_poses(json.dumps(value).encode())


def test_a_kept_pack_is_used_only_while_its_files_match_their_record(pack, tmp_path):
    version = tmp_path / "body" / "1"
    assert ref.kept_pack(version) is None
    folder = ref.keep_pack(version, pack)
    kept = ref.kept_pack(version)
    assert kept is not None and kept.folder == folder and kept.version == "1"
    (folder / "skeleton.json").write_bytes(b"{}")
    assert ref.kept_pack(version) is None
    ref.keep_pack(version, pack)  # a new download replaces it whole
    (folder / "NOTICE.txt").unlink()
    assert ref.kept_pack(version) is None


def test_only_the_current_versions_pack_stays(pack, tmp_path):
    root = tmp_path / "body"
    for version in ("1", "2"):
        ref.keep_pack(root / version, pack)
    (root / "2" / ".reference-left").mkdir()  # what a broken download left
    assert ref.remove_withdrawn(root, "2") == ["1"]
    assert ref.kept_pack(root / "2") is not None and not (root / "1" / "reference").exists()
    assert not (root / "2" / ".reference-left").exists()
    assert ref.remove_withdrawn(root, None) == ["2"]
