# SPDX-License-Identifier: GPL-3.0-or-later
"""The garment types without Blender: the UV layout Combine Materials packs (islands without room, stray points,
stacked sides of a thick export), open fronts, thigh weights bridged across the legs, the waist a dress is split at,
props snapped to their anchor, masks aligned by the head, and the Marvelous Designer and CLO avatars."""

from __future__ import annotations

import math

import numpy as np
import pytest

from durty_cloth_tool_link import garment, garment_add, garment_avatars
from tests.support import synthetic


def skeleton_joints():
    heads = {name: head for name, _, head in synthetic.SKELETON_BONES}
    return {name: heads[name] for name in garment.JOINTS if name in heads}


# ---- Combine Materials: the layout ---------------------------------------------------------------------------


def test_an_island_mapped_onto_a_line_has_no_room_in_the_texture():
    """The cause of a combined texture that used 0 to 0.8 % of its pixels (a Marvelous Designer thick export,
    2026-10-06): the side walls of every panel are mapped onto a line, and packing blew each one up to its full
    length."""
    uv_area = np.array([0.2, 0.25, 0.0, 1e-9, 0.1])
    surface = np.array([0.4, 0.5, 0.01, 0.02, 0.0])
    usable = garment.usable_islands(uv_area, surface)
    assert usable.tolist() == [True, True, False, False, False]  # a line, a sliver of a line, no surface at all
    # An island with broken UVs has no room either, and a garment with none at all has a degenerate layout.
    assert not garment.usable_islands(uv_area, surface, finite=[False, True, True, True, True])[0]
    assert not garment.usable_islands(np.zeros(3), np.ones(3)).any()


def test_strips_without_width_are_never_cut_and_cuts_are_bounded():
    # A strip whose UVs lie on a line (width zero) once fell into millions of pieces, pushed far outside 0 to 1.
    loops, uvs, starts, totals = [], [], [], []
    for i in range(30):
        starts.append(len(loops))
        totals.append(4)
        for x in (i, i + 1, i + 1, i):
            loops.append(len(loops))
            uvs.append((x * 0.02, 0.5))
    uv = np.asarray(uvs)
    islands = np.zeros(30, dtype=np.int64)
    centres = np.array([uv[s:s + t].mean(axis=0) for s, t in zip(starts, totals)])
    pieces, cut = garment.strip_segments(islands, centres, uv, totals)
    assert cut == 0 and not pieces.any()
    # A very long strip with some width is cut, into at most MAX_STRIP_PIECES pieces, unless it has no room.
    long = uv.copy()
    long[2::4, 1] += 1e-4
    long[3::4, 1] += 1e-4
    centres = np.array([long[s:s + t].mean(axis=0) for s, t in zip(starts, totals)])
    pieces, cut = garment.strip_segments(islands, centres, long, totals)
    assert cut == 1 and 1 < pieces.max() + 1 <= garment.MAX_STRIP_PIECES
    pieces, cut = garment.strip_segments(islands, centres, long, totals, usable=np.array([False]))
    assert cut == 0 and not pieces.any()


def test_island_areas_add_up_the_triangles_of_each_island():
    tri_uv = np.array([[[0, 0], [1, 0], [0, 1]], [[0, 0], [0.5, 0], [0, 0.5]], [[0, 0], [1, 0], [2, 0]]], float)
    tri_pos = np.array([[[0, 0, 0], [1, 0, 0], [0, 1, 0]]] * 3, float)
    uv_area, surface = garment.island_areas(np.array([0, 0, 1]), np.array([0, 1, 2]), tri_uv, tri_pos)
    assert uv_area.tolist() == pytest.approx([0.625, 0.0]) and surface.tolist() == pytest.approx([1.0, 0.5])


def test_stray_points_are_found_far_outside_their_island():
    uv = np.array([[0.1, 0.1], [0.2, 0.1], [0.2, 0.2], [0.1, 0.2], [40.0, 40.0], [np.nan, 0.0]])
    island = np.zeros(6, dtype=np.int64)
    stray = garment.stray_loops(uv, island, np.array([0.01]))
    assert stray.tolist() == [False, False, False, False, True, True]


def test_faces_without_room_borrow_the_uvs_of_the_panel_edge_next_to_them():
    positions = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0.001, 0, 0.002], [1.001, 0, 0.002]], float)
    loop_vertex = np.array([0, 1, 2, 3, 4, 0])
    uv = np.array([[0.1, 0.1], [0.9, 0.1], [0.1, 0.9], [5.0, 5.0], [6.0, 6.0], [7.0, 7.0]])
    keep = np.array([True, True, True, False, False, False])
    borrowed = garment.borrow_uvs(loop_vertex, uv, keep, positions)
    assert borrowed[:3].tolist() == uv[:3].tolist()
    assert borrowed[5].tolist() == [0.1, 0.1]  # the same vertex as a kept loop
    assert borrowed[3].tolist() == [0.1, 0.1] and borrowed[4].tolist() == [0.9, 0.1]  # the nearest kept vertex


def test_a_borrowed_face_covers_no_pixels():
    """A side wall's corners near two different panels would stretch it across the texture and bake over them: every
    corner of a borrowed face takes one UV."""
    positions = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0.001, 0, 0], [0.999, 0, 0]], float)
    loop_vertex = np.array([0, 1, 2, 3, 4, 4])
    uv = np.array([[0.1, 0.1], [0.9, 0.1], [0.1, 0.9], [5.0, 5.0], [6.0, 6.0], [6.0, 6.0]])
    keep = np.array([True, True, True, False, False, False])
    borrowed = garment.borrow_uvs(loop_vertex, uv, keep, positions, loop_face=[0, 0, 0, 1, 1, 1])
    assert borrowed[3].tolist() == borrowed[4].tolist() == borrowed[5].tolist() == [0.1, 0.1]


def test_thin_islands_with_little_room_and_folded_islands_are_told_apart():
    # A hair-wide strip (what welding leaves of a thick export's walls) has no room; a band of the usual density does.
    uv_area = np.array([0.3, 0.004, 2e-5])  # the last: a sixtieth of the usual room, yet above the hard limit
    surface = np.array([0.5, 0.008, 0.002])
    extent = np.array([0.7, 0.4, 0.3])
    assert garment.usable_islands(uv_area, surface, extent=extent).tolist() == [True, True, False]
    # Two sides of one panel with opposite winding on one place in the UV map: their areas cancel.
    tri_uv = np.array([[[0, 0], [1, 0], [0, 1]], [[0, 0], [0, 1], [1, 0]], [[0, 0], [1, 0], [0, 1]]], float)
    folded = garment.folded_islands(np.array([0, 0, 1]), np.array([0, 1, 2]), tri_uv)
    assert folded.tolist() == [True, False]


def test_a_layout_outside_the_square_is_moved_into_it_keeping_its_shape():
    uv = np.array([[2.0, 3.0], [2.5, 3.0], [2.5, 4.0], [9.0, 9.0]])
    fitted = garment.fit_unit_square(uv, [True, True, True, False])
    assert fitted[:3].min() >= 0 and fitted[:3].max() <= 1 and fitted[3].tolist() == [9.0, 9.0]
    ratio = (fitted[1, 0] - fitted[0, 0]) / (fitted[2, 1] - fitted[1, 1])
    assert ratio == pytest.approx(0.5)
    inside = np.array([[0.2, 0.2], [0.4, 0.6]])
    assert garment.fit_unit_square(inside, [True, True]).tolist() == inside.tolist()


def test_the_two_sides_of_a_thick_panel_share_one_place_in_the_texture():
    loop_island = np.array([0, 0, 0, 1, 1, 1, 2, 2, 2])
    source = np.array([[0, 0], [1, 0], [0, 1], [0, 0], [1, 0], [0, 1], [5, 5], [6, 5], [5, 6]], float) * 0.1
    stacked = garment.stacked_islands(np.arange(3), loop_island, source)
    assert stacked.tolist() == [0, 0, 2]  # island 1 has island 0's UVs; island 2 is its own
    packed = source.copy()
    packed[:3] = [[0.5, 0.5], [0.7, 0.5], [0.5, 0.7]]
    result = garment.copy_stacked_uvs(loop_island, stacked, source, packed)
    assert result[3:6].tolist() == result[:3].tolist() and result[6:].tolist() == packed[6:].tolist()


# ---- open fronts --------------------------------------------------------------------------------------------


def test_the_two_fronts_of_an_open_jacket_are_never_joined():
    # The left and right fronts meet on the centre front, their edges on top of each other; the back is behind.
    column = np.linspace(0.0, 0.4, 9)
    left = [(x, -0.1, z) for x in (0.0, 0.05) for z in column]
    right = [(x, -0.1, z) for x in (-0.0, -0.05) for z in column]
    back = [(0.0, 0.1, z) for z in column] + [(0.05, 0.1, z) for z in column]
    positions = np.array(left + right + back)

    def strip(first):  # the edges of a two-column panel starting at vertex ``first``
        edges = [(first + i, first + i + 1) for i in range(8)] + [(first + 9 + i, first + 10 + i) for i in range(8)]
        return edges + [(first + i, first + 9 + i) for i in range(9)]

    edges = np.array(strip(0) + strip(18) + strip(36))
    parts = garment.components(len(positions), edges)
    sides = garment.front_sides(positions, edges, (0.0, 0.0))
    assert set(sides[:18]) == {1} and set(sides[18:36]) == {-1} and set(sides[36:]) == {0}
    a, b, _ = garment.seam_candidates(positions, 0.005, components=parts)
    assert any({parts[i], parts[j]} == {parts[0], parts[18]} for i, j in zip(a, b))  # without the rule: joined
    a, b, _ = garment.seam_candidates(positions, 0.005, components=parts, sides=sides)
    assert not any({parts[i], parts[j]} == {parts[0], parts[18]} for i, j in zip(a, b))


# ---- thigh weights bridged across the legs -------------------------------------------------------------------


def test_thigh_weights_are_bridged_across_the_legs_without_splitting_the_cloth():
    positions = np.array([[0.0, -0.1, -0.3], [0.2, -0.1, -0.3], [-0.2, -0.1, -0.3], [0.0, -0.1, 0.1],
                          [0.0, -0.1, -0.12]])
    names = ["SKEL_Pelvis", "SKEL_L_Thigh", "SKEL_L_Calf"]
    # Each vertex follows one leg only, as a fit gives a skirt: the middle one splits it between the legs.
    table = np.array([[0.2, 0.8, 0.0], [0.0, 0.6, 0.4], [0.2, 0.8, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
    bridged, names, changed = garment.bridge_leg_weights(positions, table, names, 0.0, -0.1, 0.09)
    assert names == ["SKEL_Pelvis", "SKEL_L_Thigh", "SKEL_L_Calf", "SKEL_R_Thigh", "SKEL_R_Calf"]
    columns = {name: i for i, name in enumerate(names)}
    middle = bridged[0]
    assert middle[columns["SKEL_L_Thigh"]] == pytest.approx(0.4)
    assert middle[columns["SKEL_R_Thigh"]] == pytest.approx(0.4)
    assert middle[columns["SKEL_Pelvis"]] == pytest.approx(0.2)
    # Far to the left all of it stays on the left leg, thigh and calf as they were; far to the right it moves over.
    assert bridged[1, columns["SKEL_L_Calf"]] == pytest.approx(0.4) and bridged[1, columns["SKEL_R_Thigh"]] == 0
    assert bridged[2, columns["SKEL_R_Thigh"]] == pytest.approx(0.8) and bridged[2, columns["SKEL_L_Thigh"]] == 0
    assert bridged[3].tolist() == pytest.approx([1.0, 0, 0, 0, 0])  # above the thighs nothing changes
    assert 0 < bridged[4, columns["SKEL_R_Thigh"]] < 0.5  # just below them it fades in
    assert np.allclose(bridged.sum(axis=1), 1.0) and ((bridged > 1e-9).sum(axis=1) <= 4).all()
    assert changed == 3


def test_leg_bones_are_found_by_their_side():
    assert garment.leg_side("SKEL_L_Thigh") == "l" and garment.leg_side("RB_R_ThighRoll") == "r"
    assert garment.leg_side("SKEL_L_Hand") is None and garment.leg_side("SKEL_Pelvis") is None
    assert garment.mirrored_bone("MH_L_Knee") == "MH_R_Knee" and garment.mirrored_bone("SKEL_R_Foot") == "SKEL_L_Foot"


# ---- the waist of a dress -----------------------------------------------------------------------------------


def test_a_dress_is_split_where_it_is_narrowest_above_the_pelvis():
    points = []
    for z in np.linspace(-0.6, 0.5, 56):
        radius = 0.12 + 0.6 * (z - 0.14) ** 2  # narrowest 14 cm above the pelvis, flaring into the skirt
        for angle in np.linspace(0, 2 * math.pi, 24, endpoint=False):
            points.append((radius * math.cos(angle), radius * math.sin(angle), z))
    assert garment.waist_level(points, (0.0, 0.0, 0.0)) == pytest.approx(0.14, abs=0.02)


# ---- props on their anchor and masks on the head ---------------------------------------------------------------


def test_a_hat_sits_where_the_head_is_as_wide_as_its_crown():
    body = synthetic.body()
    joints = skeleton_joints()
    hat = synthetic._Builder()
    levels = np.linspace(0.0, 0.12, 8)
    hat.tube(np.column_stack([np.zeros(8), np.zeros(8), levels]) + [0.3, 0.2, 1.5], np.full((8, 2), 0.085),
             np.array([1.0, 0, 0]), np.array([0, 1.0, 0]))
    points = hat.mesh({}).positions
    snap = garment.snap_to_anchor("hat", points, body.positions, joints)
    placed = snap.apply(points)
    band = placed[placed[:, 2] < placed[:, 2].min() + 0.01]
    assert abs(band[:, 0].mean()) < 0.01 and abs(band[:, 1].mean()) < 0.01  # centred on the head
    head = body.positions[body.positions[:, 2] > 0.55]
    level = head[np.abs(head[:, 2] - band[:, 2].mean()) < 0.01]
    assert np.ptp(level[:, 0]) / 2 == pytest.approx(0.085, abs=0.012)  # the head there is as wide as the hat


def test_glasses_sit_in_front_of_the_eyes_and_a_watch_around_the_wrist():
    body = synthetic.body()
    joints = skeleton_joints()
    glasses = np.array([[x, y, z] for x in (-0.07, 0.07) for y in (0.0, 0.15) for z in (0.0, 0.04)]) + [0, 0, 1.0]
    placed = garment.snap_to_anchor("glasses", glasses, body.positions, joints).apply(glasses)
    head = body.positions[body.positions[:, 2] > 0.55]
    assert placed[:, 1].min() < head[:, 1].min()  # in front of the face
    assert placed[:, 2].mean() == pytest.approx(head[:, 2].max() - garment.EYES_BELOW_CROWN, abs=0.03)
    # A band lying flat (its axis up) is turned onto the forearm and moved around the wrist.
    angles = np.linspace(0, 2 * math.pi, 16, endpoint=False)
    band = np.array([[0.035 * math.cos(a), 0.035 * math.sin(a), h] for a in angles for h in (0.0, 0.015)])
    snap = garment.snap_to_anchor("wrist", band, body.positions, joints, "l")
    placed = snap.apply(band)
    hand, fore = np.asarray(joints["SKEL_L_Hand"]), np.asarray(joints["SKEL_L_Forearm"])
    along = (hand - fore) / np.linalg.norm(hand - fore)
    values, vectors = np.linalg.eigh(np.cov((placed - placed.mean(axis=0)).T))
    assert abs(vectors[:, 0] @ along) > 0.99
    assert np.linalg.norm(placed.mean(axis=0) - (hand - along * garment.WATCH_ABOVE_WRIST)) < 1e-6
    with pytest.raises(garment.MarkerError):
        garment.snap_to_anchor("hat", band, body.positions[body.positions[:, 2] < 0.3], joints)


def test_a_mask_is_moved_onto_the_head_joint_as_it_is():
    joints = skeleton_joints()
    head = np.asarray(joints["SKEL_Head"])
    plan = garment.align_plan({"head": tuple(head + [0.01, 0.02, 0.1])}, joints, "mask")
    assert plan.similarity.scale == 1.0 and plan.similarity.turn == pytest.approx(0.0) and not plan.limbs
    moved, markers = garment.apply_align(np.array([head + [0.01, 0.02, 0.1]]), {"head": head + [0.01, 0.02, 0.1]},
                                         plan)
    assert np.allclose(moved[0], head) and np.allclose(markers["head"], head)
    with pytest.raises(garment.MarkerError):
        garment.align_plan({"head": tuple(head + [0, 0, 0.8])}, joints, "mask")
    # Types whose markers are not read from the shape start them on the body's own joints.
    started = garment.body_markers(joints, garment.TORSO_MARKERS)
    assert set(started) == set(garment.TORSO_MARKERS) and started["neck"] == pytest.approx(joints["SKEL_Neck_1"])


def test_a_prop_needs_no_weights_but_its_anchor_nearby():
    clean = {"uv_layers": 1, "uv_area": 0.6, "weighted": None, "colour1": "ok", "anchor": 0.1}
    assert garment.is_clean(garment.validate(clean))
    far = garment.validate({**clean, "anchor": 0.6})
    assert [f.code for f in far] == ["anchor-far"] and far[0].fields == {"distance": 60}
    assert any(f.code == "no-weights" for f in garment.validate({**clean, "weighted": False}))


def test_the_anchor_bone_comes_from_the_skeleton_template_turned_as_it_is():
    bones = list(synthetic.SKELETON_BONES)
    xml = synthetic.skeleton_template_xml("male", bones).decode("utf-8")
    # Turn the head 90 degrees about Z (as the game's head bone is turned): its matrix keeps the turn.
    xml = xml.replace("<Name>SKEL_Head</Name>", "<Name>SKEL_Head</Name>", 1)
    head_item = xml.index("<Name>SKEL_Head</Name>")
    rotation = xml.index("<Rotation", head_item)
    end = xml.index("/>", rotation) + 2
    xml = xml[:rotation] + '<Rotation x="0" y="0" z="0.7071068" w="0.7071068" />' + xml[end:]
    matrices = garment_add.template_matrices(xml.encode("utf-8"), ["SKEL_Head"])
    matrix = matrices["SKEL_Head"]
    assert matrix[:3, 3].tolist() == pytest.approx(list(synthetic.joints_of()["SKEL_Head"]), abs=1e-6)
    assert matrix[:3, 0].tolist() == pytest.approx([0.0, 1.0, 0.0], abs=1e-6)  # its X now points along +Y
    assert garment_add.template_joints(xml.encode("utf-8"), ["SKEL_Head"])["SKEL_Head"] == pytest.approx(
        tuple(matrix[:3, 3]))


# ---- Marvelous Designer and CLO avatars ---------------------------------------------------------------------


def test_the_joints_of_an_exported_avatar_rig_become_markers():
    bones = {name[0]: (i * 0.01, 0.0, 0.5) for i, name in enumerate(garment_avatars.AVATAR_BONES.values())}
    markers = garment_avatars.avatar_markers(bones)
    assert set(markers) == set(garment_avatars.AVATAR_BONES)
    assert garment_avatars.parse_markers(garment_avatars.markers_json(markers)) == pytest.approx(markers)
    assert garment_avatars.avatar_markers({"Pelvis": (0, 0, 0), "Neck": (0, 0, 0.5)}) is None  # not such a rig
    assert garment_avatars.parse_markers('{"pelvis": [0, 0, "x"]}') is None
    assert garment_avatars.parse_markers('{"elbow": [0, 0, 0]}') is None


def test_the_stock_avatars_are_plausible_and_in_ped_space():
    assert garment_avatars.TO_MEASURE  # the avatars not measured yet are named
    for name, avatar in garment_avatars.AVATARS.items():
        markers = avatar.markers
        assert set(markers) == set(garment.MARKERS), name
        for category in ("tshirt", "pants"):
            subset = {m: markers[m] for m in garment.markers_for(category)}
            assert garment.marker_problems(subset, category) == [], (name, category)
        assert garment_avatars.source_pose(markers) == avatar.pose
        assert garment_avatars.arm_angle(markers) == pytest.approx(avatar.arm_angle, abs=0.2)
        # The soles are at the ped's ground: the ankles a few centimetres above z -1.
        assert -1.0 < markers["ankle_l"][2] < -0.85, name
    manne = garment_avatars.AVATARS["manne"]
    assert manne.pose == "a_pose" and manne.markers["shoulder_r"] == (-0.1757, 0.042, 0.5149)
