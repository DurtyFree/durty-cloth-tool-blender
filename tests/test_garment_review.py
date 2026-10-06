# SPDX-License-Identifier: GPL-3.0-or-later
"""The garment tools on what real Marvelous Designer and CLO exports do, rebuilt from scratch (no exported file is
used): panels whose normals are flipped against each other, dense seams, short sleeves hanging against the torso,
FBX files read ten times too large, hoods, markers on the garment's surface, pushes that add up, markers moved after
Align to Body, the add-on's own vertex groups and a skeleton template with turned bones."""

from __future__ import annotations

import math
import time

import numpy as np
import pytest

from durty_cloth_tool_link import garment, garment_add
from tests.support import synthetic


def _strip(y: float, z: float, count: int = 40, step: float = 0.01) -> np.ndarray:
    return np.column_stack([np.arange(count) * step, np.full(count, y), np.full(count, z)])


def _two_panels(gap: float = 0.0005, flipped: bool = True):
    """The edges of two panels meeting at a seam ``gap`` apart: the second panel's normals face the other way, as in
    exports where some panels come flipped."""
    first, second = _strip(0.0, 0.0), _strip(gap, 0.0)
    positions = np.concatenate([first, second])
    normals = np.concatenate([np.tile([0.0, 0.0, 1.0], (40, 1)),
                              np.tile([0.0, 0.0, -1.0 if flipped else 1.0], (40, 1))])
    parts = np.concatenate([np.zeros(40, int), np.ones(40, int)])
    return positions, normals, parts


# ---- welding ----------------------------------------------------------------------------------------------------------


def test_panels_whose_normals_are_flipped_against_each_other_are_still_sewn():
    positions, normals, parts = _two_panels()
    target, merged = garment.weld_targets(positions, 0.001, normals=normals, components=parts)
    assert (target[40:] == np.arange(40)).all()  # every vertex of the second panel joins its partner
    assert garment.open_seam_count(positions, 0.001, np.ones(80, bool), parts, target) == 0
    # Within one panel, surfaces facing apart are a fold (a hem turned back), never a seam.
    folded = garment.weld_targets(positions, 0.001, normals=normals, components=np.zeros(80, int))[0]
    assert (folded == np.arange(80)).all()
    assert garment.open_seam_count(positions, 0.001, np.ones(80, bool), parts, folded) == 80
    # A thick export (slabs, welded across parts only) keeps the rule: its front and back walls face apart.
    slab = garment.weld_targets(positions, 0.001, normals=normals, components=parts, cross_components_only=True)[0]
    assert (slab == np.arange(80)).all()


def test_a_corner_where_three_panels_meet_becomes_one_vertex_and_no_group_is_wider_than_the_weld():
    corner = np.array([[0.0, 0.0, 0.0], [0.0004, 0.0, 0.0], [0.0002, 0.0005, 0.0]])
    target, merged = garment.weld_targets(corner, 0.001, components=np.array([0, 1, 2]))
    assert (target == 0).all() and np.allclose(merged[0], corner.mean(axis=0))
    # A row of points 0.6 mm apart (a dense hem across panels): pairs at most, never a chain wider than 1 mm.
    row = _strip(0.0, 0.0, count=30, step=0.0006)
    target, _ = garment.weld_targets(row, 0.001, components=np.arange(30))
    for group in np.unique(target):
        members = row[target == group]
        assert float(np.ptp(members[:, 0])) <= 0.001 + 1e-9


def test_half_a_million_candidate_pairs_weld_in_seconds():
    rng = np.random.default_rng(3)
    # 40,000 seam vertices crowded 0.3 mm apart on a sheet: each has about thirty partners within 1 mm.
    grid = np.stack(np.meshgrid(np.arange(200), np.arange(200)), axis=-1).reshape(-1, 2) * 0.0003
    positions = np.column_stack([grid, np.zeros(len(grid))]) + rng.normal(0, 1e-5, (len(grid), 3))
    parts = rng.integers(0, 4, len(positions))
    a, _b, _d = garment.seam_candidates(positions, 0.001, components=parts)
    assert len(a) > 400_000
    started = time.monotonic()
    rounds = []
    target, merged = garment.weld_targets(positions, 0.001, components=parts, progress=lambda: rounds.append(1))
    took = time.monotonic() - started
    assert took < 30.0 and rounds, took  # the greedy walk of before took minutes on this
    sizes = np.bincount(target)
    assert sizes.max() <= garment.MAX_WELD_GROUP and (sizes > 1).sum() > 5000
    for group in np.unique(target)[:2000]:
        members = positions[target == group]
        diff = members[:, None, :] - members[None, :, :]
        assert float(np.sqrt((diff ** 2).sum(axis=2)).max()) <= 0.001 + 1e-9


# ---- markers ----------------------------------------------------------------------------------------------------------


def test_short_sleeves_hanging_against_the_torso_do_not_widen_it():
    mesh = synthetic.top("short", 60.0)  # the sleeves touch the torso's sides below the shoulders
    markers = garment.auto_markers(mesh.positions, "tshirt", "a_pose", mesh.edges)
    for side, suffix in ((1.0, "l"), (-1.0, "r")):
        assert abs(markers[f"shoulder_{suffix}"][0] - side * 0.175) < 0.015, markers[f"shoulder_{suffix}"]
        assert abs(markers[f"wrist_{suffix}"][0]) < 0.75, markers[f"wrist_{suffix}"]
    assert garment.marker_problems(markers, "tshirt") == []


# ---- import ------------------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("size, category, unit", [
    (7.49, "tshirt", "dm"),  # a Marvelous Designer FBX that Blender reads ten times too large
    (8.45, "long_sleeve", "dm"),
    (0.75, "tshirt", "m"), (75.0, "tshirt", "cm"), (750.0, "tshirt", "mm"),
    (2.7, "shoes", "dm"), (50000.0, "tshirt", None), (0.01, "tshirt", None),
])
def test_the_unit_follows_the_size_a_garment_can_have(size, category, unit):
    assert garment.import_unit(size, category) == unit
    assert garment.import_scale(size, category) == (garment.UNITS[unit] if unit else 1.0)
    assert garment.import_unit(size, category, "cm") == "cm"  # a unit the user chose is kept


def _hooded_top() -> np.ndarray:
    mesh = synthetic.top("long", 45.0)
    angles = np.linspace(0, math.pi, 30)
    hood = []
    for z in np.linspace(synthetic.NECK_Z, synthetic.NECK_Z + 0.3, 12):
        hood.append(np.column_stack([np.cos(angles) * 0.11, 0.06 + np.sin(angles) * 0.12, np.full(30, z)]))
    return np.concatenate([mesh.positions, *hood])


def test_a_hood_at_the_back_keeps_the_garment_as_it_stands_and_one_at_the_front_turns_it():
    hooded = _hooded_top()
    assert garment.upright_turn(hooded, "long_sleeve") is None
    backwards = hooded * np.array([-1.0, -1.0, 1.0])  # turned 180 degrees about Z: the hood in front
    assert garment.upright_turn(backwards, "long_sleeve") == ("z", 180.0)


# ---- Align to Body -------------------------------------------------------------------------------------------------


def test_align_measures_the_size_surface_against_surface():
    # A garment that fits snugly: its markers are where Auto Markers puts them on the body itself (the surface); the
    # body's joints lie inside it, closer together.
    surface = {name: np.asarray(value, dtype=float) for name, value in synthetic.top().joints.items()}
    surface["chest"] = np.array([0.0, 0.0, 0.3])
    surface["pelvis"] = np.array([0.0, 0.0, 0.0])
    joints = {garment.MARKER_JOINTS[name]: tuple(value * np.array([0.85, 1.0, 1.0]))
              for name, value in surface.items()}
    biased = garment.align_plan(surface, joints, "tshirt", scale=True)
    alike = garment.align_plan(surface, joints, "tshirt", scale=True, reference=surface)
    assert biased.similarity.scale < 0.97  # the joints' span shrinks a garment that fits
    assert abs(alike.similarity.scale - 1.0) < 1e-6
    kept = garment.align_plan(surface, joints, "tshirt", scale=False, reference=surface)
    assert kept.similarity.scale == 1.0


def test_markers_moved_after_align_are_noticed():
    markers = {"neck": (0.0, 0.0, 0.6), "chest": (0.0, 0.0, 0.4)}
    record = garment.markers_json(markers)
    assert not garment.markers_moved(markers, record)
    assert not garment.markers_moved({"neck": (0.0, 0.0002, 0.6), "chest": (0.0, 0.0, 0.4)}, record)
    assert garment.markers_moved({"neck": (0.0, 0.01, 0.6), "chest": (0.0, 0.0, 0.4)}, record)
    assert garment.markers_moved({"neck": (0.0, 0.0, 0.6)}, record)
    assert not garment.markers_moved(markers, "")  # aligned by an older version: nothing to compare with


def test_the_passes_of_a_push_never_add_up_past_its_limit():
    start = np.zeros((3, 3))
    moved = np.array([[0.0, 0.0, 0.054], [0.0, 0.02, 0.0], [0.03, 0.04, 0.0]])
    clamped = garment.clamp_moves(start, moved, 0.034)
    assert np.allclose(np.linalg.norm(clamped, axis=1), [0.034, 0.02, 0.034])
    assert np.allclose(clamped[2] / np.linalg.norm(clamped[2]), moved[2] / np.linalg.norm(moved[2]))


# ---- the add ---------------------------------------------------------------------------------------------------------


def test_the_add_ons_own_vertex_groups_never_reach_the_export():
    for name in ("DCT Tears", "DCT Pinned", "DCT Lining", "DCT_tmp_lod"):
        assert garment_add.is_tool_group(name), name
    assert not garment_add.is_tool_group("SKEL_Spine3")


def test_the_skeleton_templates_joints_follow_turned_bones():
    quarter = math.sqrt(0.5)
    bones = [("SKEL_ROOT", -1, (0.0, 0.0, 0.0), (0.0, 0.0, 0.0, 1.0)),
             # turned a quarter about Z: its child's offset along X ends up along Y
             ("SKEL_Pelvis", 0, (0.0, 0.0, 0.1), (0.0, 0.0, quarter, quarter)),
             ("SKEL_Spine0", 1, (0.2, 0.0, 0.0), (quarter, 0.0, 0.0, quarter)),
             # turned again about X by its parent: the offset along Y ends up along Z
             ("SKEL_Spine1", 2, (0.0, 0.3, 0.0), (0.0, 0.0, 0.0, 1.0))]
    items = "".join(
        f"<Item><Name>{name}</Name><ParentIndex value=\"{parent}\" />"
        f"<Translation x=\"{t[0]}\" y=\"{t[1]}\" z=\"{t[2]}\" />"
        f"<Rotation x=\"{q[0]}\" y=\"{q[1]}\" z=\"{q[2]}\" w=\"{q[3]}\" /><Scale x=\"1\" y=\"1\" z=\"1\" /></Item>"
        for name, parent, t, q in bones)
    xml = f"<DrawableDictionary><Item><Skeleton><Bones>{items}</Bones></Skeleton></Item></DrawableDictionary>".encode()
    joints = garment_add.template_joints(xml)
    assert np.allclose(joints["SKEL_Pelvis"], (0.0, 0.0, 0.1))
    assert np.allclose(joints["SKEL_Spine0"], (0.0, 0.2, 0.1), atol=1e-6)
    # Spine0 carries the pelvis's quarter turn about Z and its own about X: its local Y points along world Z.
    assert np.allclose(joints["SKEL_Spine1"], (0.0, 0.2, 0.4), atol=1e-6)
