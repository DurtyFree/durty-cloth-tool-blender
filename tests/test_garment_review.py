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


def _dense_seam(count: int = 49, step: float = 0.0008, gap: float = 0.0003, shift: float = 0.0004):
    """The open edges of two panels sewn together, their vertices closer along the edge than the weld distance and
    the second panel's set off by half a step (a dense seam out of a clothing app): positions, panel of each vertex,
    the chains of their open edges and the edges along them."""
    first = _strip(0.0, 0.0, count, step)
    second = _strip(gap, 0.0, count, step) + [shift, 0.0, 0.0]
    positions = np.concatenate([first, second])
    parts = np.repeat([0, 1], count)
    along = np.array([[i, i + 1] for i in range(count - 1)])
    edges = np.concatenate([along, along + count])
    chains = garment.boundary_chains(edges, len(positions), positions)
    return positions, parts, chains, edges


def _collapsed(target: np.ndarray, edges: np.ndarray) -> int:
    return int((target[edges[:, 0]] == target[edges[:, 1]]).sum())


def test_the_weld_never_joins_neighbours_along_one_panels_own_edge():
    """Joining two groups across the seam brought two neighbours of one panel's edge together (29 of the 96 edges
    along this seam collapsed): every two vertices that become one must be allowed to, not only the closest pair."""
    positions, parts, chains, edges = _dense_seam()
    target, merged = garment.weld_targets(positions, 0.0015, chains=chains, components=parts)
    assert _collapsed(target, edges) == 0
    for group in np.unique(target):
        members = np.nonzero(target == group)[0]
        assert len(members) <= 2 and len(np.unique(parts[members])) == len(members)  # one vertex of each panel
    # Nearly every vertex found a partner on the other panel (the half-step offset leaves a few without one), and
    # only those count as open.
    joined = garment.joined_across(target, parts)
    assert joined.sum() >= 0.9 * len(positions)
    assert garment.open_seam_count(positions, 0.0015, np.ones(len(positions), bool), parts, target,
                                   chains=chains) == int((~joined).sum())


def test_a_seam_vertex_joined_across_once_is_not_counted_open():
    """The old count called a vertex open unless it was joined to every close vertex of the other panel: this fully
    sewn seam, where each vertex has two or three such neighbours, counted 58 of its 60 vertices open."""
    positions, parts, chains, _edges = _dense_seam(count=30, step=0.001, gap=0.0002, shift=0.0)
    target, _ = garment.weld_targets(positions, 0.0015, chains=chains, components=parts)
    assert garment.joined_across(target, parts).all()
    boundary = np.ones(len(positions), bool)
    assert garment.open_seam_count(positions, 0.0015, boundary, parts, target, chains=chains) == 0
    # Without a weld, every vertex that has a partner is open.
    assert garment.open_seam_count(positions, 0.0015, boundary, parts, np.arange(len(positions)),
                                   chains=chains) == 60
    # A lining and its shell are never a seam: lying close, they are not open either.
    fabrics = parts.copy()
    assert garment.open_seam_count(positions, 0.0015, boundary, parts, np.arange(len(positions)), chains=chains,
                                   fabrics=fabrics, apart=[(0, 1)]) == 0


def test_a_seam_vertex_lying_on_the_other_panels_edge_is_not_counted_open():
    """One side of a seam often has twice the vertices of the other: the extra ones cannot be joined (each partner
    is taken) but lie on the other panel's edge, so the seam is closed there. Only a vertex off that edge is a gap."""
    coarse = _strip(0.0, 0.0, 20, 0.001)
    fine = _strip(0.00005, 0.0, 39, 0.0005)
    fine[17] += [0.0, 0.00025, 0.0]  # one vertex of the fine side stands 0.3 mm off the seam: a real gap
    positions = np.concatenate([coarse, fine])
    parts = np.repeat([0, 1], [20, 39])
    edges = np.concatenate([[[i, i + 1] for i in range(19)], [[20 + i, 21 + i] for i in range(38)]])
    chains = garment.boundary_chains(edges, len(positions), positions)
    target, _ = garment.weld_targets(positions, 0.0006, chains=chains, components=parts)
    assert _collapsed(target, edges) == 0
    boundary = np.ones(len(positions), bool)
    unjoined = garment.open_seams(positions, 0.0006, boundary, parts, target, chains=chains)
    assert len(unjoined) >= 18  # the fine side's extra vertices have no partner of their own
    gaps = garment.open_seams(positions, 0.0006, boundary, parts, target, edges=edges, chains=chains)
    assert gaps.tolist() == [20 + 17]


def _split_seam(crowd: int = 12):
    """Two panels of a game mesh meeting at a UV seam, which the game splits on purpose: the seam's vertices are there
    twice, on top of each other, one copy per UV island. At the seam's first vertex ``crowd`` more islands meet (a
    small panel each), as at the points of a game-ready T-shirt where up to 104 copies lie on top of each other.
    Positions, panel of each vertex, the open edges, their chains, and the vertices at that point."""
    count = 40
    seam = _strip(0.0, 0.0, count)
    angles = np.linspace(0.0, math.pi, crowd)
    spokes = seam[0] + 0.005 * np.column_stack([np.cos(angles), -np.sin(angles), np.zeros(crowd)])
    positions = np.concatenate([seam, seam, np.repeat(seam[:1], crowd, axis=0), spokes])
    islands = np.arange(crowd) + 2
    parts = np.concatenate([np.zeros(count, int), np.ones(count, int), islands, islands])
    along = np.array([[i, i + 1] for i in range(count - 1)])
    edges = np.concatenate([along, along + count,
                            np.column_stack([2 * count + np.arange(crowd), 2 * count + crowd + np.arange(crowd)])])
    chains = garment.boundary_chains(edges, len(positions), positions)
    point = np.nonzero(np.linalg.norm(positions - seam[0], axis=1) < 1e-9)[0]
    return positions, parts, edges, chains, point


def test_the_split_uv_seams_of_a_game_mesh_are_no_open_seams_but_a_gap_is():
    """Prepare Garment warned about open seams on a game-ready mesh. Where the weld cannot join every copy of a split
    vertex (a weld group holds eight), the copies still lie on top of each other: the seam is closed. Only a side
    standing apart from the other is a gap, on both sides of it."""
    positions, parts, edges, chains, point = _split_seam()
    boundary = np.ones(len(positions), bool)
    target, _ = garment.weld_targets(positions, 0.001, boundary, chains=chains, components=parts)
    assert (~garment.joined_across(target, parts)[point]).any()  # copies the weld could not join
    assert garment.open_seams(positions, 0.001, boundary, parts, target, edges=edges, chains=chains).size == 0
    unwelded = np.arange(len(positions))
    assert garment.open_seams(positions, 0.001, boundary, parts, unwelded, edges=edges, chains=chains).size == 0
    apart = positions.copy()
    apart[40 + 20] += [0.0, 0.0, 0.0005]  # one side of the seam half a millimetre off the other
    gaps = garment.open_seams(apart, 0.001, boundary, parts, unwelded, edges=edges, chains=chains)
    assert gaps.tolist() == [20, 40 + 20]


def test_a_move_spread_along_the_edges_keeps_the_sides_of_a_split_together():
    """Push Out of Body spreads each push along the mesh's edges, which the two sides of a split never share: on the
    game-ready T-shirt it parted 66 pairs of its UV seams by more than the weld distance (up to 27 mm) and left the
    open seams Prepare Garment then warned about. The vertices lying on top of each other now move alike."""
    count = 20
    seam = _strip(0.0, 0.0, count)
    # Panel A: the seam and a row inside it; panel B: its own copy of the seam and a row on the other side.
    positions = np.concatenate([seam, _strip(-0.01, 0.0, count), seam, _strip(0.01, 0.0, count)])
    along = np.array([[i, i + 1] for i in range(count - 1)])
    rungs = np.column_stack([np.arange(count), np.arange(count) + count])
    panel = np.concatenate([along, along + count, rungs])
    edges = np.concatenate([panel, panel + 2 * count])
    offsets = np.zeros_like(positions)
    pushed = np.zeros(len(positions), bool)
    pushed[count + 8:count + 12] = True  # only panel A's inner row lay inside the body
    offsets[pushed] = [0.0, 0.0, 0.003]
    moved = positions + garment.spread_offsets(offsets, edges, pushed)
    side_a, side_b = np.arange(count), np.arange(count) + 2 * count
    assert np.linalg.norm(moved[side_a] - moved[side_b], axis=1).max() > 0.0005  # the split tore open
    groups = garment.stacked_groups(positions)
    assert len(np.unique(groups)) == 3 * count  # only the seam's copies lie on top of each other
    kept = garment.keep_stacked(positions, moved, groups)
    assert np.allclose(kept[side_a], kept[side_b], atol=1e-12)
    assert np.allclose(kept[side_a] - positions[side_a], (moved[side_a] + moved[side_b]) / 2 - positions[side_a])
    assert np.array_equal(kept[pushed], moved[pushed])  # what lies on nothing moves as it was moved
    # A pinned side holds its copy too.
    pinned = np.zeros(len(positions), bool)
    pinned[side_b[10]] = True
    held = garment.keep_stacked(positions, moved, groups, pinned)
    assert np.array_equal(held[[side_a[10], side_b[10]]], positions[[side_a[10], side_b[10]]])


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


def test_the_rigged_avatar_of_a_marvelous_designer_fbx_is_left_out():
    """Marvelous Designer exports its avatar rigged: a body with open edges (so not closed) and eyes, lashes and teeth
    on the same armature, beside the garment."""
    mesh = garment.ImportedMesh
    parts = [
        mesh("Armature body", ("face", "body2", "arm", "leg"), 1.88, 1.88, False, "Armature"),
        mesh("eye_L.001", ("eye",), 0.03, 0.03, True, "Armature"),
        mesh("eyelash_R.001", ("eyelash.001",), 0.02, 0.03, False, "Armature"),
        mesh("tooth.001", ("toothSG1",), 0.08, 0.08, False, "Armature"),
        mesh("Men's Shirt FBX", ("Cotton_Twill_FRONT_289623", "Material15575"), 0.77, 1.16, False, ""),
    ]
    assert garment.avatar_meshes(parts) == [0, 1, 2, 3]
    # A garment exported with skin weights on the avatar's armature stays.
    skinned = parts[:4] + [parts[4]._replace(rig="Armature")]
    assert garment.avatar_meshes(skinned) == [0, 1, 2, 3]
    # Without an avatar, nothing is left out: a rigged garment, a coat taller than the shirt, fabric named Body.
    coat = mesh("Long Coat", ("Wool_FRONT",), 1.4, 1.4, False, "Armature")
    lining = mesh("Lining", ("Body_FRONT",), 1.2, 1.2, False, "Armature")
    assert garment.avatar_meshes([coat, lining]) == []
    # The older rules still hold: named avatar, only skin, a closed figure as tall as a person.
    assert garment.avatar_meshes([mesh("Avatar", (), 1.7, 1.7, False), parts[4]]) == [0]
    assert garment.avatar_meshes([mesh("Mesh", ("Skin_Mat",), 1.7, 1.7, False), parts[4]]) == [0]
    assert garment.avatar_meshes([mesh("Figure", ("Mat",), 1.7, 1.7, True), parts[4]]) == [0]


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
