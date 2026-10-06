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


def test_each_type_names_its_slots_and_each_slot_its_types():
    assert garment.categories_for("jbib") == ("vest", "tshirt", "long_sleeve", "long_jacket", "hoodie",
                                             "open_jacket", "long_coat", "dress")
    assert garment.categories_for("accs") == ("vest", "tshirt", "long_sleeve")
    assert garment.categories_for("lowr") == ("pants", "shorts", "skirt")
    assert garment.categories_for("feet") == ("shoes", "sandals")
    assert garment.categories_for("berd") == ("mask",) and garment.categories_for("hand") == ("bag",)
    assert garment.categories_for("task") == ("armour",)
    assert garment.slots_for("watch") == ("p_lwrist", "p_rwrist") and garment.slots_for("bracelet")[0] == "p_rwrist"
    # Every type is offered, in the picker too, and every slot it names is one the tools add to.
    assert {c for slot in garment.SLOTS for c in garment.categories_for(slot)} == set(garment.CATEGORIES)
    assert [c for c in garment.CATEGORY_MENU if c] == sorted(garment.CATEGORIES, key=garment.CATEGORY_MENU.index)
    assert set(garment.TYPES) == set(garment.CATEGORIES)
    # Blender keeps a choice by its place in the list: the types and slots of earlier versions keep theirs.
    assert garment.CATEGORIES[:7] == ("vest", "tshirt", "long_sleeve", "long_jacket", "pants", "shorts", "shoes")
    assert garment.SLOTS[:4] == ("jbib", "accs", "lowr", "feet")
    assert garment.REGIONS[:10] == ("shoulders", "upper_arms", "forearms", "cuffs", "chest", "back", "waist", "hips",
                                    "neck", "legs")


def test_props_hang_from_their_anchor_and_are_never_fitted():
    props = [c for c in garment.CATEGORIES if garment.is_prop(c)]
    assert props == ["hat", "glasses", "ears", "watch", "bracelet"]
    for category in props:
        kind = garment.garment_type(category)
        assert set(kind.slots) <= garment.PROP_SLOTS and garment.markers_for(category) == ()
        assert all(slot in garment.ANCHOR_BONES for slot in kind.slots) and kind.snap and not kind.skin
    assert garment.ANCHOR_BONES["p_head"] == garment.ANCHOR_BONES["p_eyes"] == "SKEL_Head"
    assert not any(garment.is_prop(c) for c in ("mask", "bag", "armour", "shoes"))


def test_markers_and_regions_follow_the_category():
    assert garment.markers_for("tshirt") == garment.UPPER_MARKERS and len(garment.UPPER_MARKERS) == 11
    assert garment.markers_for("pants") == ("pelvis", "hip_l", "hip_r", "knee_l", "knee_r", "ankle_l", "ankle_r")
    assert garment.markers_for("shoes") == () == garment.markers_for("sandals") == garment.markers_for("hat")
    assert garment.markers_for("mask") == ("head",) and garment.markers_for("bag") == garment.TORSO_MARKERS
    assert garment.markers_for("hoodie") == garment.markers_for("armour") == garment.UPPER_MARKERS
    assert garment.markers_for("skirt") == garment.LOWER_MARKERS
    assert set(garment.MARKERS) == set(garment.UPPER_MARKERS) | set(garment.LOWER_MARKERS) | {"head"}
    assert set(garment.MARKERS) == set(garment.MARKER_JOINTS)
    assert "upper_arms" not in garment.regions_for("vest") and "legs" not in garment.regions_for("tshirt")
    assert "forearms" not in garment.regions_for("tshirt") and "cuffs" in garment.regions_for("long_sleeve")
    assert garment.regions_for("long_jacket") == tuple(r for r in garment.REGIONS if r != "head")
    assert garment.regions_for("shorts") == ("waist", "hips", "legs") and garment.regions_for("mask")[0] == "head"
    # Snug never pulls the tails of a coat or a skirt onto the legs; the legs of trousers are snugged.
    assert "legs" not in garment.snug_regions_for("long_jacket") and "legs" in garment.snug_regions_for("pants")
    assert "legs" not in garment.snug_regions_for("skirt") and "legs" not in garment.snug_regions_for("long_coat")
    # Auto Markers reads tops and legs from their shape; masks and bags take an avatar's or the body's joints.
    assert garment.detects_markers("hoodie") and garment.detects_markers("skirt")
    assert not garment.detects_markers("mask") and not garment.detects_markers("bag")


def test_type_presets():
    """The type presets: open fronts, bridged thigh weights, bare skin, and what a type hints at."""
    assert garment.garment_type("open_jacket").open_front and not garment.garment_type("hoodie").open_front
    assert {c for c in garment.CATEGORIES if garment.garment_type(c).bridge} == {"long_coat", "dress", "skirt"}
    assert {c for c in garment.CATEGORIES if garment.garment_type(c).skin} == {"shorts", "skirt", "sandals"}
    assert garment.garment_type("shorts").hint == garment.garment_type("skirt").hint == "garment.hint.bare-legs"
    assert garment.garment_type("dress").hint == "garment.hint.dress"
    # An unknown name falls back to a T-shirt rather than failing.
    assert garment.garment_type("nonsense") == garment.TYPES["tshirt"]


# ---- markers ----------------------------------------------------------------------------------------------


@pytest.mark.parametrize("sleeves, category", [("short", "tshirt"), ("long", "long_sleeve"),
                                               ("long", "long_jacket"), ("none", "vest")])
@pytest.mark.parametrize("angle, pose", [(45.0, "a_pose"), (0.0, "t_pose")])
def test_auto_markers_find_the_joints_of_a_top(sleeves, category, angle, pose):
    top = synthetic.top(sleeves, angle)
    markers = garment.auto_markers(top.positions, category, pose, top.edges)
    assert set(markers) == set(garment.UPPER_MARKERS)
    assert garment.marker_problems(markers, category) == []
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
    assert set(markers) == set(garment.LOWER_MARKERS)
    for name, joint in pants.joints.items():
        assert distance(markers[name], joint) < 0.04, name
    # The knees lie between the hips and the ankles, and the ankles sit at the hems.
    for side in ("l", "r"):
        assert markers[f"hip_{side}"][2] > markers[f"knee_{side}"][2] > markers[f"ankle_{side}"][2]
        assert markers[f"ankle_{side}"][2] == pytest.approx(pants.positions[:, 2].min(), abs=0.03)
    assert garment.marker_problems(markers, "pants") == []


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
    assert region_at(markers, markers["wrist_l"]) == "cuffs"
    middle = np.asarray(markers["elbow_l"]) * 0.6 + np.asarray(markers["wrist_l"]) * 0.4
    assert region_at(markers, middle) == "forearms"
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
    regions = np.array([garment.REGIONS.index("shoulders")] * 10 + [garment.REGIONS.index("chest")] * 10
                       + [garment.REGIONS.index("hips")] * 3)
    clearance = np.concatenate([np.linspace(0.005, 0.020, 10), np.linspace(-0.004, 0.005, 10), [0.0, 0.0, 0.0]])
    report = garment.fit_report(clearance, regions)
    rows = {row.region: row for row in report.rows}
    assert set(rows) == {"shoulders", "chest"}  # hips have too few vertices to measure
    assert rows["shoulders"].p50 == pytest.approx(12.5, abs=0.1)
    assert rows["shoulders"].p10 < rows["shoulders"].p50 < rows["shoulders"].p90
    assert rows["chest"].inside == 3 and report.inside == 3 and report.vertices == 23
    assert garment.FitReport.from_json(report.to_json()) == report
    assert garment.FitReport.from_json("not json") is None
    assert garment.fit_advice(report) == []  # the report's summary names the vertices inside the body


def test_fit_advice_names_floating_shoulders():
    report = garment.FitReport((garment.RegionFit("shoulders", 40, 15.0, 22.0, 30.0, 0),), 40, 0)
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
             "unweighted": 3, "over_four": 7, "colour1": "missing", "triangles_high": 45000,
             "triangles_low": 100, "inside_share": 0.05, "materials": 3, "placement": 0.9, "inward_share": 0.8}
    findings = garment.validate(stats)
    codes = {f.code: f for f in findings}
    assert set(codes) == {"non-finite", "uv-outside", "uv-area", "unweighted", "influences", "colour-missing",
                          "triangles", "inside", "materials", "placement", "normals-inward"}
    # The same triangle budgets as the checks of Durty Cloth Tool.
    assert codes["triangles"].fields == {"level": "high", "count": 45000, "budget": 30000}
    assert garment.TRIANGLE_BUDGET == {"high": 30000, "medium": 15000, "low": 7500}
    assert codes["placement"].severity == "error" and codes["placement"].fields == {"distance": 90}
    assert codes["uv-area"].fields == {"area": 1.0}
    assert not garment.is_clean(findings)
    assert garment.findings_from_json(garment.findings_to_json(findings)) == findings


def test_validate_never_calls_a_garment_without_weights_clean():
    findings = garment.validate({"uv_layers": 0, "weighted": False, "colour1": "format"})
    assert [(f.severity, f.code) for f in findings] == [("error", "no-uv"), ("error", "no-weights"),
                                                        ("warning", "colour-format")]
    assert not garment.is_clean(garment.validate({"uv_layers": 1, "weighted": False, "colour1": "ok"}))
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
    for low, high in garment.SIZE_RANGES.values():
        assert high / low < 10


# ---- the next step ------------------------------------------------------------------------------------------


def test_the_next_step_walks_through_the_local_flow():
    state = garment.FlowState()
    steps = []
    for change in ({}, {"garment": True}, {"body": True}, {"markers": 11}, {"aligned": True}, {"fitted": True},
                   {"checked": True, "inside": 4}, {"prepared": True, "materials": 3}, {"materials": 1},
                   {"weighted": True}, {"lods": True}, {"findings": "blocking"},
                   {"validated": True, "findings": "clean"}, {"connected": True}, {"project": True},
                   {"skeleton": True}, {"adding": True}, {"adding": False, "added": True}):
        state = state._replace(**change)
        steps.append(garment.next_step(state))
    # The levels of detail come after the weights, which they take over.
    # Fit on gta.clothing is the next step after Align to Body (the fit check by hand skips it).
    assert steps == ["garment.next.import", "garment.next.body", "garment.next.markers", "garment.next.align",
                     "garment.next.fit", "garment.next.check", "garment.next.push", "garment.next.combine",
                     "garment.next.weights",
                     "garment.next.lods", "garment.next.validate",
                     "garment.next.validate-problems", "garment.next.connect", "garment.next.project",
                     "garment.next.add-skeleton", "garment.next.add", "garment.next.adding", "garment.next.done"]
    # Warnings do not hold the add back; without Sollumz there is nothing to export.
    warned = garment.FlowState(garment=True, body=True, markers=11, prepared=True, lods=True, findings="warnings",
                               connected=True, project=True, weighted=True)
    assert garment.next_step(warned) == "garment.next.add-skeleton"
    assert garment.next_step(warned._replace(sollumz=False)) == "garment.next.sollumz"
    # A T-pose garment is aligned like any other: Align to Body turns its arms to the body.
    tpose = garment.FlowState(garment=True, body=True, markers=11, source_pose="t_pose")
    assert garment.next_step(tpose) == "garment.next.align"
    assert garment.next_step(tpose._replace(sculpting=True)) == "garment.next.sculpting"
    shoes = garment.FlowState(garment=True, body=True, category="shoes", sollumz=False, prepared=True,
                              checked=True, weighted=True)
    assert garment.next_step(shoes) == "garment.next.validate"
    # A prepared garment is past the fitting steps: the hint does not send it back to the fit check.
    prepared = garment.FlowState(garment=True, body=True, markers=11, prepared=True, lods=True, weighted=True)
    assert garment.next_step(prepared) == "garment.next.validate"
    # Connected but not weighted yet: the Durty Cloth Tool skeleton gives the bones to weight to.
    unweighted = garment.FlowState(garment=True, body=True, markers=11, prepared=True, connected=True)
    assert garment.next_step(unweighted) == "garment.next.skeleton"
    assert garment.next_step(unweighted._replace(skeleton=True)) == "garment.next.weights"
    assert garment.next_step(prepared._replace(prepared=False, aligned=True, checked=True)) == "garment.next.prepare"
    assert set(garment.STEP_OPERATORS) <= set(steps) | {"garment.next.prepare", "garment.next.snap",
                                                        "garment.next.skeleton"}


def test_an_added_garment_is_done_whatever_steps_it_skipped():
    """A model opened from Durty Cloth Tool goes straight to Add to Project: no body, markers or fit. Once it is
    added, the hint says so instead of sending the user back to the body, and Setup does not report the body as
    missing beside its tick."""
    added = garment.FlowState(garment=True, weighted=True, connected=True, project=True, skeleton=True, added=True)
    assert garment.next_step(added) == "garment.next.done"
    assert garment.stage_of(added) == "add"
    setup = garment.stage_status(added, "setup")
    assert setup.done and setup.key != "garment.status.no-body"
    assert garment.stage_status(added, "add").key == "garment.status.added"
    # Another add of the same garment shows its progress; before the first add the steps still lead to it.
    assert garment.next_step(added._replace(adding=True)) == "garment.next.adding"
    assert garment.next_step(added._replace(added=False)) == "garment.next.body"


def test_the_open_stage_is_the_one_that_holds_the_next_step():
    """The panel opens the stage of the next step and folds the others: a step mapped to the wrong stage would put
    its large button into a closed section, and a stage that went back would fold the work in progress."""
    state = garment.FlowState()
    stages = []
    for change in ({}, {"garment": True}, {"body": True}, {"markers": 11}, {"aligned": True}, {"fitted": True},
                   {"checked": True, "inside": 4}, {"inside": 0}, {"prepared": True, "materials": 3},
                   {"materials": 1}, {"connected": True}, {"skeleton": True}, {"weighted": True}, {"lods": True},
                   {"validated": True, "findings": "clean"}, {"project": True, "skeleton": False},
                   {"skeleton": True}, {"adding": True}, {"adding": False, "added": True}):
        state = state._replace(**change)
        stages.append(garment.stage_of(state))
    assert stages == ["setup", "setup", "fit", "fit", "fit", "fix", "fix", "ready", "ready", "ready", "ready",
                      "ready", "ready", "ready", "add", "add", "add", "add", "add"]
    # Use Durty Cloth Tool Skeleton is part of Game Ready before the weights; after them the add does it.
    assert garment.stage_of(garment.FlowState(garment=True, body=True, markers=11, prepared=True,
                                              connected=True)) == "ready"
    assert garment.stage_of(state._replace(sculpting=True)) == "fix"
    assert set(garment.STAGES) == set(stages)
    # Every step's button lives in its stage's section: the large button is never in a folded one.
    assert garment.STEP_OPERATORS["garment.next.add-skeleton"] == garment.STEP_OPERATORS["garment.next.add"]


def test_a_finished_stage_never_says_what_was_left_out():
    """A ticked stage beside "Not checked" or "3 of 11 markers" contradicts itself: Prepare Garment clears the fit
    check, so every garment that reaches Game Ready would show it under Fix."""
    prepared = garment.FlowState(garment=True, body=True, markers=11, aligned=True, fitted=True, prepared=True,
                                 checked=False, gender="female")
    fix = garment.stage_status(prepared, "fix")
    assert fix.done and fix.key is None
    assert garment.stage_status(prepared._replace(checked=True), "fix").key == "ped.status.no-problems"
    fit = garment.stage_status(prepared._replace(markers=3, aligned=False, fitted=False), "fit")
    assert fit.done and fit.key is None
    setup = garment.stage_status(prepared, "setup")
    assert setup.done and setup.keys == {"type": "garment.category.tshirt", "gender": "gender.female"}
    # The stage in progress says what is still open.
    checking = garment.FlowState(garment=True, body=True, markers=11, aligned=True, fitted=True)
    assert garment.stage_status(checking, "fix") == garment.StageStatus("ped.status.not-checked", {}, {}, False)
    assert garment.stage_status(checking._replace(markers=3, aligned=False, fitted=False), "fit").fields == {
        "count": 3, "total": 11}
    added = garment.stage_status(checking._replace(added=True), "add")
    assert added.done and added.key == "garment.status.added"


def test_a_prop_is_snapped_and_added_without_weights_or_skeleton():
    state = garment.FlowState(garment=True, body=True, category="hat", prop=True)
    assert garment.next_step(state) == "garment.next.snap"
    state = state._replace(aligned=True)
    assert garment.next_step(state) == "garment.next.prepare"
    state = state._replace(prepared=True, lods=True, findings="clean", validated=True, connected=True, project=True)
    # No weights and no skeleton: a prop hangs from its anchor.
    assert garment.next_step(state) == "garment.next.add"
    assert garment.STEP_OPERATORS["garment.next.snap"] == "dct_link.fit_snap_anchor"


def test_pose_angles_are_degrees_below_the_horizontal():
    assert garment.POSE_ARM_ANGLE["t_pose"] == 0.0
    direction = garment._pose_direction(1.0, "a_pose")
    assert math.degrees(math.atan2(-direction[2], direction[0])) == pytest.approx(45.0)


# ---- the review cases: seams ---------------------------------------------------------------------------------


def ring(count, radius=0.05, z=0.0, centre=(0.0, 0.0)):
    angles = np.linspace(0, 2 * math.pi, count, endpoint=False)
    return np.column_stack([centre[0] + radius * np.cos(angles), centre[1] + radius * np.sin(angles),
                            np.full(count, z)])


def loop_edges(count, offset=0):
    return np.array([[offset + i, offset + (i + 1) % count] for i in range(count)])


def test_close_pairs_find_exactly_the_pairs_within_the_distance():
    points = np.random.default_rng(3).random((400, 3)) * 0.05
    a, b, d = garment.close_pairs(points, 0.006)
    brute = {(i, j) for i in range(400) for j in range(i + 1, 400) if distance(points[i], points[j]) <= 0.006}
    assert set(zip(a.tolist(), b.tolist())) == brute and np.allclose(d, np.linalg.norm(points[a] - points[b], axis=1))
    q, t, _ = garment.grid_pairs(points[:5], points, 0.006, block=7)  # tiny blocks give the same answer
    assert {(int(x), int(y)) for x, y in zip(q, t)} == {(i, j) for i in range(5) for j in range(400)
                                                         if distance(points[i], points[j]) <= 0.006}


def test_a_dense_hem_is_never_welded_into_a_point():
    # A 300-vertex open loop with 1.05 mm spacing and the default 2 mm weld collapsed into one vertex before.
    hem = ring(300)
    chains = garment.boundary_chains(loop_edges(300), 300, hem)
    target, merged = garment.weld_targets(hem, 0.002, chains=chains)
    assert len(np.unique(target)) == 300
    # Even without the open-edge rule no joined group is wider than the weld distance.
    target, merged = garment.weld_targets(hem, 0.002)
    assert len(np.unique(target)) >= 150
    for root in np.unique(target):
        group = hem[target == root]
        assert np.linalg.norm(group[:, None] - group[None], axis=2).max() <= 0.002 + 1e-9


def test_two_panels_sewn_along_their_edges_are_welded_pairwise():
    left, right = ring(120, z=0.0), ring(120, z=0.0005)  # two panels whose edges meet 0.5 mm apart
    points = np.concatenate([left, right])
    edges = np.concatenate([loop_edges(120), loop_edges(120, 120)])
    chains = garment.boundary_chains(edges, 240, points)
    target, merged = garment.weld_targets(points, 0.002, chains=chains)
    assert len(np.unique(target)) == 120
    assert all(target[i] == target[i + 120] for i in range(120))


def test_a_seam_between_different_fabrics_welds_unless_they_are_lining_and_shell():
    a = np.column_stack([np.linspace(0, 0.1, 21), np.zeros(21), np.zeros(21)])
    points = np.vstack([a, a + [0, 0, 0.0003]])
    fabrics = np.array([0] * 21 + [1] * 21)
    joined, _ = garment.weld_targets(points, 0.002, fabrics=fabrics, apart=[(2, 3)])
    assert len(np.unique(joined)) <= 22  # a pocket or a lining elsewhere no longer keeps this seam open
    kept, _ = garment.weld_targets(points, 0.002, fabrics=fabrics, apart=[(0, 1)])
    assert np.all(kept == np.arange(42))


def test_surfaces_facing_apart_and_corners_of_one_face_are_never_welded():
    points = np.array([[0.0, 0, 0], [0.0, 0.0005, 0], [0.001, 0, 0]])
    normals = np.array([[0.0, -1, 0], [0.0, 1, 0], [0.0, -1, 0]])
    target, _ = garment.weld_targets(points, 0.002, normals=normals, face_pairs=np.array([[0, 2]]))
    assert np.all(target == np.arange(3))


def test_a_thick_export_welds_across_panels_only():
    slab = np.array([[0.0, 0, 0], [0.0, 0.002, 0], [0.1, 0, 0], [0.1, 0.002, 0]])
    points = np.vstack([slab, slab + [0.1005, 0, 0]])  # two slabs whose side walls touch at x = 0.1
    edges = np.array([[0, 1], [0, 2], [1, 3], [2, 3], [4, 5], [4, 6], [5, 7], [6, 7]])
    parts = garment.components(8, edges)
    assert len(set(parts.tolist())) == 2
    target, _ = garment.weld_targets(points, 0.002, components=parts, cross_components_only=True,
                                     face_pairs=edges)
    assert sorted(int(i) for i in np.nonzero(target != np.arange(8))[0]) == [4, 5]


def sheet(z_offset, width, height, fabric, step=0.01):
    xs, zs = np.meshgrid(np.arange(0, width, step), np.arange(0, height, step))
    return np.column_stack([xs.ravel(), np.full(xs.size, z_offset), zs.ravel()]), np.full(xs.size, fabric)


def test_a_pocket_or_a_collar_is_no_lining_but_a_lining_is():
    shell, shell_fabric = sheet(0.0, 0.4, 0.5, 0)
    lining, lining_fabric = sheet(0.006, 0.38, 0.48, 1)
    pocket, pocket_fabric = sheet(-0.004, 0.15, 0.15, 2)
    points = np.concatenate([shell, lining, pocket + [0.1, 0, 0.1]])
    fabrics = np.concatenate([shell_fabric, lining_fabric, pocket_fabric])
    normals = np.tile([0.0, -1.0, 0.0], (len(points), 1))
    assert garment.lining_pairs(points, normals, fabrics) == [(0, 1)]
    beside = np.concatenate([shell, shell + [0.4 + 0.001, 0, 0]])  # a second fabric sewn on beside the first
    assert garment.lining_pairs(beside, np.tile([0.0, -1.0, 0.0], (len(beside), 1)),
                                np.concatenate([shell_fabric, shell_fabric + 1])) == []


# ---- the review cases: markers -----------------------------------------------------------------------------------


def hoodie():
    tee = synthetic.top("short", 45.0)
    hood = []
    for z in np.linspace(0.55, 0.85, 12):
        r = 0.10 * math.sqrt(max(0.0, 1 - ((z - 0.70) / 0.17) ** 2)) + 0.02
        hood.append(ring(32, r, z, (0.0, 0.02)))
    return tee, np.vstack([tee.positions] + hood)


def test_the_neck_of_a_hoodie_is_under_its_hood():
    tee, points = hoodie()
    result = garment.place_markers(points, "tshirt", "a_pose", tee.edges)
    assert "hood" in result.notes
    assert abs(result.markers["neck"][2] - tee.joints["neck"][2]) < 0.03
    assert distance(result.markers["shoulder_l"], tee.joints["shoulder_l"]) < 0.04


def test_a_flared_coat_measures_its_torso_below_the_armholes():
    coat = synthetic.top("long", 45.0, hem_z=-0.75)
    points = coat.positions.copy()
    low = points[:, 2] < -0.05
    flare = 1.0 + np.clip((-0.05 - points[:, 2]) / 0.7, 0, 1) * 0.8  # the hem 1.8 times as wide
    points[low, 0] *= flare[low]
    points[low, 1] *= flare[low]
    markers = garment.auto_markers(points, "long_jacket", "a_pose", coat.edges)
    assert abs(markers["shoulder_l"][0] - coat.joints["shoulder_l"][0]) < 0.03


def test_an_asymmetric_top_keeps_its_centre_on_the_torso():
    top = synthetic.top("short", 45.0)
    strap = ring(24, 0.03, 0.0, (0.0, 0.0))[:, [2, 1, 0]] * [1, 1, 1] + [0.45, 0.0, 0.2]  # a bag strap on one side
    markers = garment.auto_markers(np.vstack([top.positions, strap]), "tshirt", "a_pose", top.edges)
    assert abs(garment.centre_x(markers)) < 0.02


def test_cap_sleeves_place_the_arms_from_the_pose():
    vest = synthetic.top("none", 45.0)
    result = garment.place_markers(vest.positions, "tshirt", "a_pose", vest.edges)
    assert "arms-estimated" in result.notes and set(result.markers) == set(garment.UPPER_MARKERS)


def test_overalls_and_skirts_put_the_pelvis_at_the_hips():
    pants = synthetic.pants()
    bib = np.array([[x, -0.13, z] for x in np.linspace(-0.12, 0.12, 9) for z in np.linspace(0.05, 0.4, 15)])
    markers = garment.auto_markers(np.vstack([pants.positions, bib]), "pants")
    assert abs(markers["pelvis"][2] - pants.joints["pelvis"][2]) < 0.05
    skirt = synthetic.top("none", 45.0, hem_z=-0.6).positions
    skirt = skirt[skirt[:, 2] < 0.05]
    result = garment.place_markers(skirt, "shorts")
    assert "skirt" in result.notes and result.markers["pelvis"][2] < 0.05


def test_implausible_markers_are_named():
    top = synthetic.top("long", 45.0)
    good = garment.auto_markers(top.positions, "long_sleeve", "a_pose", top.edges)
    assert garment.marker_problems(good, "long_sleeve") == []
    lopsided = dict(good, shoulder_r=(-0.4, 0.0, 0.44))
    assert "symmetry" in garment.marker_problems(lopsided, "long_sleeve")
    upside_down = dict(good, neck=(0.0, 0.0, -0.5))
    assert "order" in garment.marker_problems(upside_down, "long_sleeve")
    bent = dict(good, wrist_l=good["shoulder_l"])
    assert "arms" in garment.marker_problems(bent, "long_sleeve")
    assert len(garment.stick_figure(good)) == 10  # spine, arms and hips


# ---- the review cases: regions ---------------------------------------------------------------------------------


def skeleton_joints():
    heads = {name: head for name, _, head in synthetic.SKELETON_BONES}
    return {name: heads[name] for name in garment.JOINTS if name in heads}


def test_the_sides_of_an_a_pose_torso_are_no_upper_arms():
    tee = synthetic.top("short", 45.0)
    markers = garment.auto_markers(tee.positions, "tshirt", "a_pose", tee.edges)
    torso = np.arange(len(tee.positions)) < 48 * 40
    upper_arms = garment.REGIONS.index("upper_arms")
    by_markers = garment.classify_regions(tee.positions, markers)
    shoulder_z = markers["shoulder_l"][2]
    for labels in (by_markers, garment.body_regions(tee.positions, skeleton_joints())):
        wrong = torso & (labels == upper_arms)
        # 152 of 1,920 before, down to 25 cm below the shoulders; only the armhole itself may go either way now.
        assert int(wrong.sum()) < 76 and (not wrong.any() or tee.positions[wrong, 2].min() > shoulder_z - 0.12)
    arms = np.isin(by_markers[~torso], [upper_arms, garment.REGIONS.index("forearms"), garment.REGIONS.index("cuffs")])
    assert arms.mean() > 0.8


def test_body_regions_name_each_part():
    joints = skeleton_joints()
    regions = {name: garment.REGIONS.index(name) for name in garment.REGIONS}
    points = {"chest": (0.05, -0.12, 0.25), "back": (0.05, 0.12, 0.25), "waist": (0.0, -0.12, 0.1),
              "hips": (0.0, -0.12, -0.02), "neck": (0.0, -0.05, 0.57), "legs": (0.1, -0.07, -0.5),
              "shoulders": (0.1, 0.0, 0.45), "cuffs": joints["SKEL_L_Hand"]}
    labels = garment.body_regions(np.array(list(points.values())), joints)
    assert [garment.REGIONS[i] for i in labels] == list(points)
    # The head (where a hood lies, or a mask): no top covers it, so its fit check leaves it out.
    assert garment.REGIONS[garment.body_regions(np.array([[0.0, 0.0, 0.75]]), joints)[0]] == "head"
    assert "head" not in garment.regions_for("hoodie")
    assert set(regions) == set(garment.REGIONS)


# ---- the review cases: Align to Body ------------------------------------------------------------------------


def on_joints(joints):
    """Markers exactly on the joints they stand for."""
    return {name: joints[bone] for name, bone in garment.MARKER_JOINTS.items() if bone in joints}


def test_align_brings_a_garment_made_on_another_avatar_onto_the_joints():
    joints = skeleton_joints()
    tee = synthetic.top("short", 45.0)
    markers = {name: value for name, value in on_joints(joints).items() if name in garment.UPPER_MARKERS}
    turn = math.radians(6.0)
    rotation = np.array([[math.cos(turn), -math.sin(turn), 0], [math.sin(turn), math.cos(turn), 0], [0, 0, 1]])
    moved = garment.Similarity(1.1, rotation, np.array([0.02, -0.03, 0.04]))
    elsewhere = moved.apply(tee.positions)
    their = {name: tuple(moved.apply([value])[0]) for name, value in markers.items()}
    plan = garment.align_plan(their, joints, "tshirt")
    back, placed = garment.apply_align(elsewhere, their, plan)
    assert np.abs(back - tee.positions).max() < 0.001 and plan.residual < 1.0 and not plan.limbs
    assert distance(placed["neck"], markers["neck"]) < 0.001
    kept = garment.align_plan(their, joints, "tshirt", scale=False)
    assert kept.similarity.scale == 1.0 and kept.similarity.turn == pytest.approx(6.0, abs=0.1)
    # With markers from Auto Markers (on the surface, not on the joints) the fit stays close.
    auto = garment.auto_markers(elsewhere, "tshirt", "a_pose", tee.edges)
    back, _ = garment.apply_align(elsewhere, auto, garment.align_plan(auto, joints, "tshirt"))
    assert np.abs(back - tee.positions).max() < 0.05


def test_align_lowers_t_pose_arms_without_tearing_a_seam():
    joints = skeleton_joints()
    tpose = synthetic.top("long", 0.0)
    markers = dict(on_joints(joints), **tpose.joints)  # its own arms, out to the sides
    markers = {name: value for name, value in markers.items() if name in garment.UPPER_MARKERS}
    plan = garment.align_plan(markers, joints, "long_sleeve")
    assert {side for side, *_ in plan.limbs} == {"l", "r"}
    assert all(abs(limb[4] - 45.0) < 1.0 for limb in plan.limbs)
    # An unwelded seam: every vertex has a twin on top of it, as two panels have. They must stay together.
    doubled = np.vstack([tpose.positions, tpose.positions + 1e-5])
    moved, placed = garment.apply_align(doubled, markers, plan)
    count = len(tpose.positions)
    assert np.linalg.norm(moved[:count] - moved[count:], axis=1).max() < 1e-4
    assert abs(garment.arm_angle(placed, "l") - 45.0) < 1.0 and abs(garment.arm_angle(placed, "r") - 45.0) < 1.0
    torso = np.arange(count) < 48 * 40
    assert np.abs(moved[:count][torso & (tpose.positions[:, 2] < 0.3)] - tpose.positions[torso & (
        tpose.positions[:, 2] < 0.3)]).max() < 0.01  # the torso below the arms stays where it is


def test_align_refuses_markers_that_would_need_a_wild_fit():
    joints = skeleton_joints()
    tee = synthetic.top("short", 45.0)
    markers = garment.auto_markers(tee.positions, "tshirt", "a_pose", tee.edges)
    shrunk = {name: tuple(np.asarray(value) * 0.5) for name, value in markers.items()}
    with pytest.raises(garment.MarkerError) as refused:
        garment.align_plan(shrunk, joints, "tshirt")
    assert refused.value.code == "align-markers"


def test_joints_files_are_read_strictly():
    joints = skeleton_joints()
    text = garment.joints_json(joints, "male")
    parsed = garment.parse_joints(text, "male")
    assert set(parsed) == set(joints) and all(distance(parsed[n], joints[n]) < 1e-5 for n in joints)
    assert garment.parse_joints(text, "female") is None
    data = json.loads(text)
    data["male"]["SKEL_Pelvis"] = [0, 0, 99]
    assert garment.parse_joints(json.dumps(data), "male") is None
    assert garment.parse_joints("not json", "male") is None


def test_joints_can_be_estimated_from_the_body_shape():
    body = synthetic.body(45.0)
    joints = garment.estimate_body_joints(body.positions, body.edges)
    assert abs(joints["SKEL_L_UpperArm"][0] - synthetic.SHOULDER) < 0.04
    assert joints["SKEL_Neck_1"][2] > joints["SKEL_Pelvis"][2] > joints["SKEL_L_Calf"][2]


# ---- the review cases: moves, checks and units --------------------------------------------------------------------


def test_push_out_leaves_what_runs_deep_through_the_body_and_what_is_pinned():
    positions = np.array([[0.0, 0.0, -0.002], [0.0, 0.0, -0.05], [0.0, 0.0, 0.001]])
    normals = np.tile([0.0, 0.0, 1.0], (3, 1))
    offsets = garment.push_out_offsets(positions, np.zeros((3, 3)), normals, positions[:, 2], 0.004,
                                       locked=[False, False, True])
    assert offsets[0, 2] == pytest.approx(0.006) and not offsets[1:].any()


def test_a_shell_follows_its_pushed_lining():
    positions = np.array([[0.0, 0.0, 0.001], [0.0, 0.0, 0.007]])  # the lining, and the shell 6 mm outside it
    offsets = np.array([[0.0, 0.0, 0.003], [0.0, 0.0, 0.0]])
    followed = garment.layer_follow(positions, offsets, positions[:, 2])
    assert followed[1] == pytest.approx([0.0, 0.0, 0.003])


def test_snug_leaves_a_hanging_hood_alone():
    positions = np.array([[0.0, 0.0, 0.03], [0.0, 0.0, 0.2]])
    normals = np.tile([0.0, 0.0, 1.0], (2, 1))
    offsets = garment.snug_offsets(positions, np.zeros((2, 3)), normals, positions[:, 2], 0.005, 1.0, np.ones(2))
    assert offsets[0, 2] < 0 and offsets[1, 2] == 0.0


def test_inches_and_a_chosen_unit():
    assert garment.import_scale(27.5, "tshirt") == pytest.approx(0.0254)
    assert garment.import_scale(70.0, "tshirt", "in") == pytest.approx(0.0254)
    assert garment.import_scale(70.0, "tshirt", "mm") == pytest.approx(0.001)


def test_a_garment_facing_backwards_or_lying_down_is_turned():
    tee = synthetic.top("short", 45.0).positions.copy()
    front = (tee[:, 1] < 0) & (tee[:, 2] > 0.45)
    tee[front, 2] -= np.clip(0.08 - np.abs(tee[front, 0]), 0, None)  # the front of the neckline dips
    assert garment.upright_turn(tee, "tshirt") is None
    backwards = tee * [-1, -1, 1]
    assert garment.upright_turn(backwards, "tshirt") == ("z", 180.0)
    lying = tee[:, [0, 2, 1]] * [1, 1, -1]  # its height along +Y
    assert garment.upright_turn(lying, "tshirt") == ("x", 90.0)


def test_weights_keep_four_bones_and_lod_budgets_follow_high():
    table = garment.limit_influences([[0.1, 0.2, 0.3, 0.15, 0.25], [0, 0, 0, 0, 0]])
    assert (table[0] > 0).sum() == 4 and table[0].sum() == pytest.approx(1.0) and not table[1].any()
    assert garment.lod_budget("medium", 12000) == 6000 and garment.lod_budget("low", 100000) == 7500
    assert garment.lod_budget("medium", 12000, 900) == 900


def test_texel_density_in_pixels_per_centimetre():
    triangles = np.array([[[0, 0, 0], [0.1, 0, 0], [0, 0.1, 0]]])  # 50 square centimetres
    uv = np.array([[[0, 0], [0.5, 0], [0, 0.5]]])  # an eighth of the texture
    assert garment.texel_density(uv, triangles, 2048) == pytest.approx(2048 * math.sqrt(0.125 / 50), abs=0.1)
