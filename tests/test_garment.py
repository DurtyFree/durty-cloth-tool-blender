# SPDX-License-Identifier: GPL-3.0-or-later
"""The garment fitting tools without Blender: marker placement on synthetic garments, regions, the fit check,
the problem colours, moves against the body, seam welding and tears, UV islands and strips, the local checks,
pose presets and the next-step hint."""

from __future__ import annotations

import json
import math

import numpy as np
import pytest

from durty_cloth_tool_link import garment
from tests.support import synthetic


def distance(a, b) -> float:
    return float(np.linalg.norm(np.asarray(a, dtype=float) - np.asarray(b, dtype=float)))


# ---- slots and categories ---------------------------------------------------------------------------------


def test_each_slot_offers_its_categories():
    assert garment.categories_for("jbib") == ("vest", "tshirt", "long_sleeve", "long_jacket")
    assert garment.categories_for("accs") == ("vest", "tshirt", "long_sleeve")
    assert garment.categories_for("lowr") == ("pants", "shorts")
    assert garment.categories_for("feet") == ("shoes",)
    assert {c for slot in garment.SLOTS for c in garment.categories_for(slot)} == set(garment.CATEGORIES)


def test_markers_and_regions_follow_the_category():
    assert garment.markers_for("tshirt") == garment.MARKERS and len(garment.MARKERS) == 11
    assert garment.markers_for("pants") == ("pelvis", "hip_l", "hip_r")
    assert garment.markers_for("shoes") == ()
    assert "upper_arms" not in garment.regions_for("vest") and "legs" not in garment.regions_for("tshirt")
    assert garment.regions_for("long_jacket") == garment.REGIONS
    assert garment.regions_for("shorts") == ("waist", "hips", "legs")


# ---- markers ----------------------------------------------------------------------------------------------


@pytest.mark.parametrize("sleeves, category", [("short", "tshirt"), ("long", "long_sleeve"),
                                               ("long", "long_jacket"), ("none", "vest")])
@pytest.mark.parametrize("angle, pose", [(45.0, "a_pose"), (0.0, "t_pose")])
def test_auto_markers_find_the_joints_of_a_top(sleeves, category, angle, pose):
    top = synthetic.top(sleeves, angle)
    markers = garment.auto_markers(top.positions, category, pose, top.edges)
    assert set(markers) == set(garment.MARKERS)
    assert distance(markers["neck"], top.joints["neck"]) < 0.02
    for suffix in ("l", "r"):
        assert distance(markers[f"shoulder_{suffix}"], top.joints[f"shoulder_{suffix}"]) < 0.04
        assert distance(markers[f"elbow_{suffix}"], top.joints[f"elbow_{suffix}"]) < 0.05
        assert distance(markers[f"wrist_{suffix}"], top.joints[f"wrist_{suffix}"]) < 0.06
    # The ped's left is +X, and the chest lies below the neck, the pelvis below the chest.
    assert markers["shoulder_l"][0] > 0 > markers["shoulder_r"][0]
    assert markers["neck"][2] > markers["chest"][2] > markers["pelvis"][2] > markers["hip_l"][2]


def test_auto_markers_follow_the_garment_where_it_is():
    offset = (0.3, -0.2, 0.5)
    top = synthetic.top("long", 45.0, offset=offset)
    markers = garment.auto_markers(top.positions, "long_sleeve", "a_pose", top.edges)
    assert distance(markers["wrist_l"], top.joints["wrist_l"]) < 0.06
    assert abs(garment.centre_x(markers) - offset[0]) < 1e-6


def test_auto_markers_of_trousers():
    pants = synthetic.pants()
    markers = garment.auto_markers(pants.positions, "pants", "a_pose", pants.edges)
    assert set(markers) == {"pelvis", "hip_l", "hip_r"}
    for name, joint in pants.joints.items():
        assert distance(markers[name], joint) < 0.04, name


def test_auto_markers_refuse_what_they_cannot_place():
    with pytest.raises(garment.MarkerError) as shoes:
        garment.auto_markers(synthetic.pants().positions, "shoes")
    assert shoes.value.code == "no-markers"
    with pytest.raises(garment.MarkerError) as flat:
        garment.auto_markers(np.random.default_rng(1).random((100, 3)) * [1, 1, 0.01], "tshirt")
    assert flat.value.code == "too-small"


def test_mirror_copies_the_left_markers_across_the_centre():
    markers = {"chest": (0.1, 0.0, 0.3), "neck": (0.1, 0.0, 0.5), "shoulder_l": (0.3, 0.02, 0.45),
               "shoulder_r": (-0.5, 0.0, 0.0), "wrist_l": (0.6, 0.0, 0.0)}
    mirrored = garment.mirror_markers(markers)
    assert mirrored["shoulder_r"] == pytest.approx((-0.1, 0.02, 0.45))
    assert mirrored["wrist_r"] == pytest.approx((-0.4, 0.0, 0.0))
    assert mirrored["shoulder_l"] == pytest.approx(markers["shoulder_l"])


# ---- regions ----------------------------------------------------------------------------------------------


def region_at(markers, point) -> str:
    index = int(garment.classify_regions(np.array([point]), markers)[0])
    return garment.REGIONS[index] if index >= 0 else "other"


def test_regions_follow_the_markers():
    top = synthetic.top("long", 45.0)
    markers = garment.auto_markers(top.positions, "long_sleeve", "a_pose", top.edges)
    shoulder = np.asarray(markers["shoulder_l"])
    elbow = np.asarray(markers["elbow_l"])
    assert region_at(markers, shoulder + 0.5 * (elbow - shoulder)) == "upper_arms"
    assert region_at(markers, markers["wrist_l"]) == "other"  # forearms and hands are no fit region
    neck = np.asarray(markers["neck"])
    assert region_at(markers, neck + (0.0, 0.0, 0.02)) == "neck"
    chest = np.asarray(markers["chest"])
    assert region_at(markers, chest + (0.05, -0.12, 0.0)) == "chest"  # the front faces -Y
    assert region_at(markers, chest + (0.05, 0.12, 0.0)) == "back"
    assert region_at(markers, (0.12, 0.0, (neck[2] + shoulder[2]) / 2 - 0.01)) == "shoulders"
    pelvis = np.asarray(markers["pelvis"])
    assert region_at(markers, pelvis + (0.0, -0.1, 0.15)) == "waist"
    assert region_at(markers, pelvis + (0.0, -0.1, 0.0)) == "hips"
    assert region_at(markers, pelvis + (0.1, 0.0, -0.4)) == "legs"


def test_regions_of_trousers_without_upper_markers():
    pants = synthetic.pants()
    regions = garment.classify_regions(pants.positions, pants.joints)
    names = {garment.REGIONS[i] for i in np.unique(regions) if i >= 0}
    assert names == {"waist", "hips", "legs"}
    lowest = int(np.argmin(pants.positions[:, 2]))
    assert garment.REGIONS[regions[lowest]] == "legs"


def test_regions_need_a_pelvis_or_hips():
    with pytest.raises(garment.MarkerError):
        garment.classify_regions(np.zeros((3, 3)), {"neck": (0, 0, 0.5)})


# ---- fit check and problem colours ------------------------------------------------------------------------


def test_fit_report_measures_each_region_in_millimetres():
    regions = np.array([0] * 10 + [2] * 10 + [5] * 3)
    clearance = np.concatenate([np.linspace(0.010, 0.030, 10), np.linspace(-0.004, 0.005, 10), [0.0, 0.0, 0.0]])
    report = garment.fit_report(clearance, regions)
    rows = {row.region: row for row in report.rows}
    assert set(rows) == {"shoulders", "chest"}  # hips have too few vertices to measure
    assert rows["shoulders"].p50 == pytest.approx(20.0, abs=0.1)
    assert rows["shoulders"].p10 < rows["shoulders"].p50 < rows["shoulders"].p90
    assert rows["chest"].inside == 3 and report.inside == 3 and report.vertices == 23
    assert garment.FitReport.from_json(report.to_json()) == report
    assert garment.FitReport.from_json("not json") is None
    assert garment.fit_advice(report) == []  # the report's summary names the vertices inside the body


def test_fit_advice_names_floating_shoulders():
    report = garment.FitReport((garment.RegionFit("shoulders", 40, 20.0, 30.0, 40.0, 0),), 40, 0)
    assert garment.fit_advice(report) == [("garment.advice.shoulders", {})]


def test_problem_colours_put_inside_first():
    shoulders, chest = garment.REGIONS.index("shoulders"), garment.REGIONS.index("chest")
    clearance = np.array([-0.005, 0.001, 0.010, 0.040, 0.040])
    regions = np.array([shoulders, chest, chest, shoulders, chest])
    stretch = np.array([2.0, 2.0, 1.3, 1.0, 1.0])
    classes = garment.problem_classes(clearance, regions, stretch)
    assert [garment.PROBLEMS[c] for c in classes] == ["inside", "close", "stretched", "floating", "none"]
    assert garment.problem_counts(classes) == {"inside": 1, "close": 1, "stretched": 1, "floating": 1}


# ---- moving against the body ------------------------------------------------------------------------------


def test_push_out_moves_close_and_inside_vertices_to_the_gap():
    positions = np.array([[0.0, 0.0, -0.002], [0.0, 0.0, 0.001], [0.0, 0.0, 0.02]])
    nearest = np.zeros((3, 3))
    normals = np.tile([0.0, 0.0, 1.0], (3, 1))
    clearance = positions[:, 2].copy()
    moved = positions + garment.push_out_offsets(positions, nearest, normals, clearance, 0.004)
    assert moved[:2, 2] == pytest.approx([0.004, 0.004])
    assert moved[2, 2] == pytest.approx(0.02)


def test_spread_keeps_the_fixed_offsets_and_fades_around_them():
    edges = np.array([[0, 1], [1, 2], [2, 3]])
    offsets = np.array([[0.0, 0.0, 0.01], [0, 0, 0], [0, 0, 0], [0, 0, 0]])
    spread = garment.spread_offsets(offsets, edges, np.array([True, False, False, False]), iterations=3)
    assert spread[0, 2] == pytest.approx(0.01)
    assert 0 < spread[2, 2] < spread[1, 2] < 0.01


def test_snug_brings_loose_vertices_to_the_gap_by_the_amount():
    positions = np.array([[0.0, 0.0, 0.05], [0.0, 0.0, 0.006]])
    normals = np.tile([0.0, 0.0, 1.0], (2, 1))
    offsets = garment.snug_offsets(positions, np.zeros((2, 3)), normals, positions[:, 2], 0.01, 0.5, np.ones(2))
    assert offsets[0, 2] == pytest.approx(-0.02)  # half of the way from 50 mm to 10 mm
    assert offsets[1] == pytest.approx([0, 0, 0])  # already closer than the gap


def test_relax_shortens_stretched_edges_only():
    positions = np.array([[0.0, 0, 0], [2.0, 0, 0], [2.5, 0, 0]])
    edges = np.array([[0, 1], [1, 2]])
    rest = np.array([1.0, 1.0])
    relaxed = garment.relax_positions(positions, edges, rest, np.ones(3), 1.0, iterations=50)
    lengths = np.linalg.norm(relaxed[edges[:, 1]] - relaxed[edges[:, 0]], axis=1)
    assert lengths[0] == pytest.approx(1.0, abs=0.05)
    assert lengths[1] <= 1.0 + 1e-6


def test_vertex_stretch_and_soft_mask():
    edges = np.array([[0, 1], [1, 2]])
    rest = np.array([[0.0, 0, 0], [1.0, 0, 0], [2.0, 0, 0]])
    now = np.array([[0.0, 0, 0], [1.5, 0, 0], [2.5, 0, 0]])
    assert garment.vertex_stretch(edges, rest, now) == pytest.approx([1.5, 1.5, 1.0])
    weights = garment.soft_mask(np.array([True, False, False]), edges, rings=2)
    assert weights[0] == 1.0 and 0 < weights[2] < weights[1] < 1.0


def test_arm_rotation_lowers_both_arms_to_the_target():
    markers = {"shoulder_l": (0.16, 0, 0.44), "wrist_l": (0.7, 0, 0.44),
               "shoulder_r": (-0.16, 0, 0.44), "wrist_r": (-0.7, 0, 0.44)}
    assert garment.arm_angle(markers, "l") == pytest.approx(0.0)
    rotations = garment.arm_rotations(markers, 40.0)
    assert rotations == pytest.approx({"l": 40.0, "r": -40.0})
    lowered = garment.rotate_about_y(np.array([markers["wrist_l"], markers["wrist_r"]]), markers["shoulder_l"],
                                     rotations["l"])
    assert lowered[0, 2] < 0.44
    left = garment.rotate_about_y(np.array([markers["wrist_l"]]), markers["shoulder_l"], 40.0)[0]
    after = dict(markers, wrist_l=tuple(left))
    assert garment.arm_angle(after, "l") == pytest.approx(40.0)


# ---- seams --------------------------------------------------------------------------------------------------


def two_panels(gap=0.001):
    """Two strips that meet along x = 0, their edge vertices ``gap`` apart (as unwelded panels are)."""
    left = np.array([[-0.1, 0, z] for z in np.linspace(0, 0.3, 7)] + [[-gap / 2, 0, z] for z in np.linspace(0, 0.3, 7)])
    right = np.array([[gap / 2, 0, z] for z in np.linspace(0, 0.3, 7)] + [[0.1, 0, z] for z in np.linspace(0, 0.3, 7)])
    return np.concatenate([left, right])


def test_weld_joins_the_seam_within_the_distance():
    positions = two_panels(0.001)
    target, merged = garment.weld_targets(positions, 0.002)
    joined = np.nonzero(target != np.arange(len(positions)))[0]
    assert len(joined) == 7  # each seam vertex of one panel goes into its partner
    assert all(merged[target[i]][0] == pytest.approx(0.0) for i in joined)
    target, _ = garment.weld_targets(positions, 0.0005)
    assert np.all(target == np.arange(len(positions)))


def test_weld_only_joins_candidates_of_the_same_group():
    positions = two_panels(0.001)
    groups = np.array([0] * 14 + [1] * 14)
    target, _ = garment.weld_targets(positions, 0.002, groups=groups)
    assert np.all(target == np.arange(len(positions)))
    candidates = np.zeros(len(positions), dtype=bool)
    candidates[7:9] = candidates[14:16] = True
    target, _ = garment.weld_targets(positions, 0.002, candidates=candidates)
    assert int((target != np.arange(len(positions))).sum()) == 2


def test_a_lining_is_told_apart_from_a_seam():
    grid = np.array([[x, 0.0, z] for x in np.linspace(-0.2, 0.2, 21) for z in np.linspace(0, 0.4, 21)])
    normals = np.tile([0.0, -1.0, 0.0], (len(grid), 1))
    lining = grid + [0.0, 0.006, 0.0]
    positions = np.concatenate([grid, lining])
    groups = np.array([0] * len(grid) + [1] * len(lining))
    assert garment.lining_pairs(positions, np.concatenate([normals, normals]), groups) == [(0, 1)]
    side = grid + [0.4 + 0.001, 0.0, 0.0]  # a second fabric sewn on beside the first
    positions = np.concatenate([grid, side])
    assert garment.lining_pairs(positions, np.concatenate([normals, normals]), groups) == []


def test_tears_report_seams_that_open_in_a_pose():
    positions = two_panels(0.0)
    pairs = garment.seam_pairs(positions, 0.0005)
    assert len(pairs) == 7
    posed = positions.copy()
    posed[14:21, 0] += 0.01  # the right panel's seam moves away by 10 mm
    torn, separation = garment.tears(pairs, posed, 0.005)
    assert torn.all() and separation.max() == pytest.approx(0.01)
    torn, _ = garment.tears(pairs, positions, 0.005)
    assert not torn.any()


# ---- UV islands and strips ----------------------------------------------------------------------------------


def quad_grid(columns, rows, offset=(0.0, 0.0), vertex_offset=0, scale=0.1):
    """Quads of one UV island: (loop vertices, loop UVs, face starts, face totals)."""
    loops, uvs, starts, totals = [], [], [], []
    for r in range(rows):
        for c in range(columns):
            corners = [(c, r), (c + 1, r), (c + 1, r + 1), (c, r + 1)]
            starts.append(len(loops))
            totals.append(4)
            for x, y in corners:
                loops.append(vertex_offset + y * (columns + 1) + x)
                uvs.append((offset[0] + x * scale, offset[1] + y * scale))
    return loops, uvs, starts, totals


def test_uv_islands_and_long_strips_are_cut():
    strip = quad_grid(20, 1, scale=0.04)  # 0.8 long, 0.04 wide
    square = quad_grid(3, 3, offset=(0.0, 0.5), vertex_offset=1000)
    loops = strip[0] + square[0]
    uvs = strip[1] + square[1]
    starts = strip[2] + [s + len(strip[0]) for s in square[2]]
    totals = strip[3] + square[3]
    islands = garment.uv_islands(loops, uvs, starts, totals)
    assert len(set(islands[:20].tolist())) == 1 and len(set(islands.tolist())) == 2
    uv = np.asarray(uvs)
    centres = np.array([uv[s:s + t].mean(axis=0) for s, t in zip(starts, totals)])
    pieces, cut = garment.strip_segments(islands, centres, uv, totals)
    assert cut == 1
    assert len(set(pieces[:20].tolist())) == 10  # 0.8 long cut into squares of twice the width
    assert set(pieces[20:].tolist()) == {0}


def test_uv_area_and_game_vertices():
    assert garment.uv_area([[[0, 0], [1, 0], [0, 1]], [[1, 0], [1, 1], [0, 1]]]) == pytest.approx(1.0)
    loops = [0, 1, 2, 2, 1, 3]
    assert garment.game_vertex_count(loops) == 4
    uvs = [(0, 0), (1, 0), (0, 1), (0.5, 1), (1, 0), (1, 1)]  # vertex 2 has two UVs: a UV seam
    assert garment.game_vertex_count(loops, uvs) == 5
    assert garment.game_vertex_count(loops, None, [0, 0, 0, 1, 1, 1]) == 6


# ---- local checks -------------------------------------------------------------------------------------------


def test_validate_is_clean_for_a_good_garment():
    stats = {"non_finite": 0, "uv_layers": 1, "uv_outside": 0, "uv_area": 0.6, "weighted": True, "unweighted": 0,
             "over_four": 0, "colour1": "ok", "game_vertices_high": 9000, "inside_share": 0.001, "materials": 1}
    findings = garment.validate(stats)
    assert findings == [] and garment.is_clean(findings)


def test_validate_lists_what_the_game_would_show():
    stats = {"non_finite": 2, "uv_layers": 1, "uv_outside": 5, "uv_area": 0.01, "weighted": True,
             "unweighted": 3, "over_four": 7, "colour1": "missing", "game_vertices_high": 45000,
             "game_vertices_low": 100, "inside_share": 0.05, "materials": 3}
    findings = garment.validate(stats)
    codes = {f.code: f for f in findings}
    assert set(codes) == {"non-finite", "uv-outside", "uv-area", "unweighted", "influences", "colour-missing",
                          "vertices", "inside", "materials"}
    assert codes["vertices"].fields == {"level": "high", "count": 45000, "budget": 30000}
    assert codes["uv-area"].fields == {"area": 1.0}
    assert not garment.is_clean(findings)
    assert garment.findings_from_json(garment.findings_to_json(findings)) == findings


def test_validate_notes_a_garment_that_is_not_rigged_yet():
    findings = garment.validate({"uv_layers": 0, "weighted": False, "colour1": "format"})
    assert [(f.severity, f.code) for f in findings] == [("error", "no-uv"), ("info", "no-weights"),
                                                        ("warning", "colour-format")]
    assert garment.influence_counts([[0.5, 0.5], [], [0.2] * 5, [0.0, 1.0]]) == (1, 1)


# ---- presets and units ----------------------------------------------------------------------------------------


def test_presets_round_trip_and_reject_anything_else():
    markers = {"neck": (0.0, 0.01, 0.55), "pelvis": (0.0, 0.0, 0.0)}
    markers, category, pose = garment.parse_preset(garment.preset_json(markers, "tshirt", "t_pose"))
    assert markers == {"neck": (0.0, 0.01, 0.55), "pelvis": (0.0, 0.0, 0.0)}
    assert (category, pose) == ("tshirt", "t_pose")
    for text in ("[]", json.dumps({"version": 2, "markers": {"neck": [0, 0, 0]}}),
                 json.dumps({"version": 1, "markers": {"nose": [0, 0, 0]}}),
                 json.dumps({"version": 1, "markers": {"neck": [0, 0, "x"]}}),
                 json.dumps({"version": 1, "markers": {"neck": [0, None, 0]}}),
                 json.dumps({"version": 1, "markers": {"neck": [0, 0, 1e9]}})):
        with pytest.raises(ValueError):
            garment.parse_preset(text)
    assert garment.preset_file_name("My Coat / v2..") == "My Coat  v2.json"
    with pytest.raises(ValueError):
        garment.preset_file_name("../..")


@pytest.mark.parametrize("size, category, factor", [
    (0.7, "tshirt", 1.0), (70.0, "tshirt", 0.01), (700.0, "tshirt", 0.001), (160.0, "long_sleeve", 0.01),
    (0.27, "shoes", 1.0), (27.0, "shoes", 0.01), (270.0, "shoes", 0.001), (80.0, "shoes", 0.001),
    (105.0, "pants", 0.01), (1050.0, "pants", 0.001), (190.0, "long_jacket", 0.01), (1e6, "tshirt", 1.0),
])
def test_import_scale_brings_centimetres_and_millimetres_to_metres(size, category, factor):
    assert garment.import_scale(size, category) == factor


def test_the_size_ranges_never_fit_two_units():
    for low, high in [*garment.SIZE_RANGES.values(), garment.TOP_SIZE_RANGE]:
        assert high / low < 10


# ---- the next step ------------------------------------------------------------------------------------------


def test_the_next_step_walks_through_the_local_flow():
    state = garment.FlowState()
    steps = []
    for change in ({}, {"garment": True}, {"body": True}, {"markers": 11}, {"checked": True, "inside": 4},
                   {"prepared": True, "materials": 3}, {"materials": 1}, {"lods": True}, {"validated": True}):
        state = state._replace(**change)
        steps.append(garment.next_step(state))
    assert steps == ["garment.next.import", "garment.next.body", "garment.next.markers", "garment.next.check",
                     "garment.next.push", "garment.next.combine", "garment.next.lods", "garment.next.validate",
                     "garment.next.done"]
    tpose = garment.FlowState(garment=True, body=True, markers=11, source_pose="t_pose")
    assert garment.next_step(tpose) == "garment.next.tpose"
    assert garment.next_step(tpose._replace(sculpting=True)) == "garment.next.sculpting"
    shoes = garment.FlowState(garment=True, body=True, category="shoes", sollumz=False, prepared=True,
                              checked=True)
    assert garment.next_step(shoes) == "garment.next.validate"
    # A prepared garment is past the fitting steps: the hint does not send it back to the fit check.
    prepared = garment.FlowState(garment=True, body=True, markers=11, prepared=True, lods=True)
    assert garment.next_step(prepared) == "garment.next.validate"


def test_pose_angles_are_degrees_below_the_horizontal():
    assert garment.POSE_ARM_ANGLE["t_pose"] == 0.0
    direction = garment._pose_direction(1.0, "a_pose")
    assert math.degrees(math.atan2(-direction[2], direction[0])) == pytest.approx(45.0)
