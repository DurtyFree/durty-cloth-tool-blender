# SPDX-License-Identifier: GPL-3.0-or-later
"""Check Tears in the game's poses: skinning a garment with the poses of a Reference Data Pack and finding the seams
that open and the cloth that stretches until it tears, on synthetic poses and a synthetic garment (no game data, no
Blender needed)."""

from __future__ import annotations

import numpy as np
import pytest

from durty_cloth_tool_link import garment, garment_reference
from tests.support import synthetic, synthetic_pack


@pytest.fixture(scope="module")
def poses():
    return garment_reference.read_poses(synthetic_pack.files()["poses_male.json"])


def test_each_vertex_moves_with_its_bones_blended_by_their_weights():
    matrices = np.tile(np.eye(4), (2, 1, 1))
    matrices[1, :3, 3] = (0.0, 0.0, 0.1)  # the second bone lifts by 10 cm
    rest = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [2.0, 0.0, 0.0]])
    bones = np.array([[0, 1], [0, 1], [1, 0]])
    weights = np.array([[1.0, 0.0], [0.5, 0.5], [1.0, 0.0]])
    posed = garment.skinned(rest, bones, weights, matrices)
    assert np.allclose(posed, [[0.0, 0.0, 0.0], [1.0, 0.0, 0.05], [2.0, 0.0, 0.1]])


def test_the_heaviest_four_bones_the_poses_know_carry_each_vertex():
    names = ["SKEL_Spine3", "mixamorig:Hips", "SKEL_L_UpperArm", "SKEL_Head", "SKEL_Neck_1", "SKEL_Pelvis"]
    table = np.array([[0.1, 0.9, 0.2, 0.3, 0.4, 0.05],
                      [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]])
    bones = ["SKEL_ROOT", "SKEL_Pelvis", "SKEL_Spine3", "SKEL_L_UpperArm", "SKEL_Neck_1", "SKEL_Head"]
    index, weight = garment.skin_weights(table, names, bones)
    first = dict(zip((bones[i] for i in index[0]), weight[0]))
    assert first == pytest.approx({"SKEL_Neck_1": 0.4, "SKEL_Head": 0.3, "SKEL_L_UpperArm": 0.2,
                                   "SKEL_Spine3": 0.1})  # an unknown bone is left out; the four sum to one
    assert weight[1].sum() == 0.0  # a vertex without weights stays where it is


def test_game_poses_need_a_pack_and_weights_on_its_bones(poses):
    table = np.array([[0.7, 0.3], [0.0, 1.0]])
    assert garment.tear_poses_for(None, ["SKEL_Spine3", "SKEL_L_UpperArm"], table) is None  # no pack: test poses
    assert garment.tear_poses_for(poses, ["mixamorig:Spine", "mixamorig:LeftArm"], table) is None  # another rig
    assert garment.tear_poses_for(poses, ["SKEL_Spine3", "SKEL_L_UpperArm"], table) is poses
    # Weights mostly on bones the poses do not know would leave that cloth behind: the test poses are used.
    assert garment.tear_poses_for(poses, ["SKEL_Spine3", "DCT_Helper"], table) is None


def sleeve_strip():
    """A strip of cloth from the chest out along the left arm, cut in two panels at x 0.2 with a seam: the chest
    panel weighted to the spine, the arm panel to the upper arm."""
    xs = np.linspace(0.0, 0.4, 9)
    rows = []
    for z in (0.40, 0.44):
        rows.append([(x, -0.06, z) for x in xs if x <= 0.2])
    chest = np.array(rows[0] + rows[1])
    arm_rows = [[(x, -0.06, z) for x in xs if x >= 0.2] for z in (0.40, 0.44)]
    arm = np.array(arm_rows[0] + arm_rows[1])
    positions = np.concatenate([chest, arm])
    n_chest, n_arm = len(chest) // 2, len(arm) // 2

    def quads(start, count):
        return [(start + i, start + i + 1, start + count + i + 1, start + count + i) for i in range(count - 1)]

    faces = quads(0, n_chest) + quads(len(chest), n_arm)
    edges = synthetic.Mesh(positions, faces, {}).edges
    seam = np.array([[n_chest - 1, len(chest)], [2 * n_chest - 1, len(chest) + n_arm]])
    names = ["SKEL_Spine3", "SKEL_L_UpperArm"]
    table = np.zeros((len(positions), 2))
    table[: len(chest), 0] = 1.0
    table[len(chest):, 1] = 1.0
    return positions, edges, seam, names, table


def test_a_seam_that_opens_in_one_pose_is_flagged(poses):
    positions, edges, seam, names, table = sleeve_strip()
    index, weight = garment.skin_weights(table, names, poses.bones)
    steps = garment.pose_tear_steps(positions, seam, edges, index, weight, poses.matrices, threshold=0.005)
    rows = []
    while True:
        try:
            rows.append(next(steps))  # one pose per step, so Blender's interface keeps running in between
        except StopIteration as stop:
            result = stop.value
            break
    assert rows == [0, 1, 2]
    by_pose = dict(zip(poses.labels, result.rows))
    assert by_pose["idle@0"]["torn"] == 0 and by_pose["sit@0.5"]["torn"] == 0
    assert by_pose["climb@0.5"]["torn"] > 0 and by_pose["climb@0.5"]["gap"] > 5.0
    torn = set(np.nonzero(result.torn)[0])
    assert set(seam.ravel()) <= torn  # both sides of the opening seam go into DCT Tears


def test_cloth_stretched_past_its_limit_tears_even_without_a_seam(poses):
    positions, edges, _seam, names, table = sleeve_strip()
    # One panel: the seam's arm side is welded onto the chest side, so only the stretch can tear.
    welded = np.arange(len(positions))
    welded[_seam[:, 1]] = _seam[:, 0]
    edges = np.unique(np.sort(welded[edges], axis=1), axis=0)
    edges = edges[edges[:, 0] != edges[:, 1]]
    index, weight = garment.skin_weights(table, names, poses.bones)
    result = garment.run_tear_steps(positions, np.zeros((0, 2), dtype=np.int64), edges, index, weight,
                                    poses.matrices, threshold=0.005)
    climb = result.rows[poses.labels.index("climb@0.5")]
    assert climb["stretched"] > 0 and climb["stretch"] > garment.TEAR_STRETCH and climb["torn"] > 0
    assert result.rows[poses.labels.index("idle@0")]["stretched"] == 0
    smooth = table.copy()
    smooth[:, 0] = np.clip((0.4 - positions[:, 0]) / 0.4, 0.0, 1.0)  # weights that blend along the whole strip
    smooth[:, 1] = 1.0 - smooth[:, 0]
    index, weight = garment.skin_weights(smooth, names, poses.bones)
    calm = garment.run_tear_steps(positions, np.zeros((0, 2), dtype=np.int64), edges, index, weight,
                                  poses.matrices, threshold=0.005)
    assert not calm.torn.any()


def test_the_share_of_cloth_stretched_to_tearing_is_taken_in_the_worst_pose():
    # Five points 10 mm apart in a row and a sixth 1 mm past the end: four edges that count and one too short to.
    rest = np.array([[0.0, 0.0, 0.0], [0.01, 0.0, 0.0], [0.02, 0.0, 0.0], [0.03, 0.0, 0.0], [0.04, 0.0, 0.0],
                     [0.041, 0.0, 0.0]])
    edges = np.array([[0, 1], [1, 2], [2, 3], [3, 4], [4, 5]])
    bones = np.array([[0], [0], [0], [1], [0], [1]])
    weights = np.ones((6, 1))
    still = np.tile(np.eye(4), (2, 1, 1))
    lifted = still.copy()
    lifted[1, :3, 3] = (0.0, 0.0, 0.03)  # the second bone lifts points 3 and 5 by 30 mm
    result = garment.run_tear_steps(rest, np.zeros((0, 2), dtype=np.int64), edges, bones, weights,
                                    np.stack([still, lifted, still]), threshold=0.005)
    assert [row["stretched"] for row in result.rows] == [0, 2, 0]
    assert result.share == pytest.approx(50.0)  # two of the four edges that count, in the worst pose
