# SPDX-License-Identifier: GPL-3.0-or-later
"""The Fix stage's tools without Blender: Fix Spikes against the pre-fit shape, on synthetic garments."""

from __future__ import annotations

import math

import numpy as np

from durty_cloth_tool_link import garment
from tests.support import synthetic


def fitted(points: np.ndarray) -> np.ndarray:
    """A smooth fit of ``points``: turned a little, scaled, moved and gently bent, as fitting changes a garment
    without breaking its local shape."""
    angle = math.radians(6.0)
    turn = np.array([[math.cos(angle), -math.sin(angle), 0.0], [math.sin(angle), math.cos(angle), 0.0], [0, 0, 1.0]])
    moved = points @ turn.T * 0.96 + np.array([0.01, -0.02, 0.03])
    moved[:, 0] += 0.015 * np.sin(points[:, 2] * 3.0)
    return moved


def spiked(points: np.ndarray, chosen: np.ndarray, length: float = 0.025) -> np.ndarray:
    """``points`` with the ``chosen`` vertices thrown out sideways, as a fit gone wrong leaves single vertices."""
    result = points.copy()
    outward = result[chosen] * np.array([1.0, 1.0, 0.0])
    outward /= np.linalg.norm(outward, axis=1, keepdims=True)
    result[chosen] += outward * length
    return result


def torso_vertices(count: int) -> np.ndarray:
    """Vertices well inside the torso tube (away from its hem and neck and from each other)."""
    rows = np.linspace(8, 30, count).astype(int)
    return rows * 48 + (np.arange(count) * 11) % 48


def test_fix_spikes_brings_spiked_vertices_back_to_their_neighbourhood():
    tee = synthetic.top("short")
    triangles = synthetic.triangles(tee.faces)
    good = fitted(tee.positions)
    chosen = torso_vertices(6)
    result = garment.fix_spikes(tee.positions, spiked(good, chosen), triangles, tee.edges)
    assert result.found >= len(chosen)
    assert np.linalg.norm(result.positions[chosen] - good[chosen], axis=1).max() < 0.003
    assert np.linalg.norm(result.positions - good, axis=1).max() < 0.003
    assert 0.02 < result.most < 0.03 and result.moved >= len(chosen)


def test_fix_spikes_leaves_a_garment_without_spikes_as_it_is():
    tee = synthetic.top("long")
    good = fitted(tee.positions)
    result = garment.fix_spikes(tee.positions, good, synthetic.triangles(tee.faces), tee.edges)
    assert np.array_equal(result.positions, good)
    assert result.found == 0 and result.moved == 0 and result.most == 0.0


def split_seam(mesh: synthetic.Mesh) -> synthetic.Mesh:
    """``mesh`` with its torso tube cut open along one column, the cut's vertices doubled as a game mesh splits a UV
    seam: the faces on one side use the copies."""
    rings, segments = 40, 48
    column = np.arange(rings) * segments
    copies = len(mesh.positions) + np.arange(rings)
    copy_of = dict(zip(column.tolist(), copies.tolist()))
    faces = []
    for face in mesh.faces:
        if face[0] < rings * segments and face[0] % segments == segments - 1:  # the faces closing the tube
            face = tuple(copy_of.get(v, v) for v in face)
        faces.append(face)
    return synthetic.Mesh(np.concatenate([mesh.positions, mesh.positions[column]]), faces, mesh.joints)


def test_fix_spikes_keeps_pinned_vertices_and_moves_the_sides_of_a_seam_together():
    tee = split_seam(synthetic.top("short"))
    good = fitted(tee.positions)
    seam = 20 * 48
    pinned = 12 * 48 + 7
    chosen = np.array([seam, len(tee.positions) - 40 + 20, pinned])
    locked = np.zeros(len(good), dtype=bool)
    locked[pinned] = True
    bad = spiked(good, chosen)
    result = garment.fix_spikes(tee.positions, bad, synthetic.triangles(tee.faces), tee.edges, locked=locked)
    assert np.array_equal(result.positions[pinned], bad[pinned])
    assert np.array_equal(result.positions[chosen[0]], result.positions[chosen[1]])
    assert np.linalg.norm(result.positions[chosen[0]] - good[chosen[0]]) < 0.003


# ---- Push Out of Body by region -----------------------------------------------------------------------------


class Capsules:
    """A body of capsules (segments with a radius) and balls, measured exactly: each point's signed distance to the
    nearest surface, the nearest point on it and its outward normal, as the body's measurement in Blender gives
    them."""

    def __init__(self, capsules, balls=()):
        self.capsules = [(np.asarray(a, float), np.asarray(b, float), r) for a, b, r in capsules]
        self.balls = [(np.asarray(c, float), r) for c, r in balls]

    def __call__(self, points):
        points = np.asarray(points, float)
        best = np.full(len(points), np.inf)
        nearest = np.zeros_like(points)
        normals = np.tile([0.0, 0.0, 1.0], (len(points), 1))
        shapes = [(a, b, r) for a, b, r in self.capsules] + [(c, c, r) for c, r in self.balls]
        for a, b, radius in shapes:
            axis = b - a
            t = np.clip((points - a) @ axis / max(float(axis @ axis), 1e-12), 0.0, 1.0)
            foot = a + t[:, None] * axis
            off = points - foot
            length = np.linalg.norm(off, axis=1)
            signed = length - radius
            closer = signed < best
            direction = off[closer] / np.maximum(length[closer], 1e-12)[:, None]
            best[closer] = signed[closer]
            normals[closer] = direction
            nearest[closer] = foot[closer] + direction * radius
        return best, nearest, normals


def arm_axis(side: float) -> tuple:
    """The synthetic arm's axis from its shoulder, 45 degrees down."""
    start = np.array([side * synthetic.SHOULDER, 0.0, synthetic.SHOULDER_Z])
    direction = np.array([side * math.cos(math.radians(45)), 0.0, -math.sin(math.radians(45))])
    return start, direction


def loose_body(**balls) -> Capsules:
    """A body the synthetic top hangs loosely around: the torso 2.5 cm and the arms 3 cm inside the cloth."""
    capsules = [((0, 0, -0.15), (0, 0, 0.38), 0.10)]
    for side in (1.0, -1.0):
        start, direction = arm_axis(side)
        capsules.append((start + direction * 0.12, start + direction * 0.6, 0.035))
    return Capsules(capsules, balls.get("balls", ()))


def dent(points: np.ndarray, chosen: np.ndarray, depth: float, measure: Capsules) -> np.ndarray:
    """``points`` with the ``chosen`` vertices pressed ``depth`` towards the body."""
    result = points.copy()
    _signed, _nearest, normals = measure(points[chosen])
    result[chosen] -= normals * depth
    return result


TORSO_COUNT = 40 * 48


def tee_with_dents():
    """The synthetic long-sleeved top on the loose body, with a patch of its front and of its left sleeve pressed
    into the body, and each vertex's region."""
    tee = synthetic.top("long")
    body = loose_body()
    front = np.array([row * 48 + column for row in (20, 21, 22) for column in (35, 36, 37)])  # facing -Y
    sleeve = TORSO_COUNT + np.array([ring * 20 + column for ring in (8, 9) for column in (4, 5, 6)])
    points = dent(dent(tee.positions, front, 0.03, body), sleeve, 0.035, body)
    _signed, nearest, _normals = body(points)
    regions = garment.body_regions(nearest, synthetic.joints_of())
    return tee, body, points, front, sleeve, regions


def test_push_out_of_the_torso_only_leaves_the_sleeves_untouched():
    tee, body, points, front, sleeve, regions = tee_with_dents()
    assert body(points[front])[0].max() < 0 and body(points[sleeve])[0].max() < 0
    within = garment.push_region(regions, "torso")
    arms = np.isin(regions, [garment.REGIONS.index(r) for r in ("upper_arms", "forearms", "cuffs")])
    assert within[front].all() and not within[sleeve].any() and not (within & arms).any()
    assert arms[TORSO_COUNT:].mean() > 0.9  # the sleeves (but their start at the shoulder)
    result = garment.push_out_positions(points, tee.edges, body, 0.004, within=within)
    assert np.array_equal(result.positions[arms], points[arms])
    assert body(result.positions[front])[0].min() > 0.004 - 1e-4
    assert result.before == len(front) + len(sleeve) and result.after == len(sleeve)


def test_push_out_of_the_whole_garment_clears_the_body_by_the_gap():
    tee, body, points, front, sleeve, regions = tee_with_dents()
    assert garment.push_region(regions, "whole").all()
    result = garment.push_out_positions(points, tee.edges, body, 0.004)
    assert body(result.positions)[0].min() > 0.004 - 1e-4
    assert result.after == 0 and result.moved >= len(front) + len(sleeve)
    torso_and_arms = garment.push_region(regions, "torso_arms")
    assert torso_and_arms[front].all() and torso_and_arms[sleeve].all()


def test_pinned_vertices_and_layers_keep_their_rules_in_a_region():
    tee, body, points, front, sleeve, regions = tee_with_dents()
    pinned = np.zeros(len(points), dtype=bool)
    pinned[front[:3]] = True
    # A second layer 1 cm outside the front patch: it needs no push of its own, and follows the patch out.
    outer = points[front[3:]] + body(points[front[3:]])[2] * 0.01
    layered = np.concatenate([points, outer])
    edges = np.concatenate([tee.edges, len(points) + np.array([[0, 1], [1, 2], [3, 4], [4, 5]])])
    locked = np.concatenate([pinned, np.zeros(len(outer), dtype=bool)])
    within = np.concatenate([garment.push_region(regions, "torso"), np.ones(len(outer), dtype=bool)])
    result = garment.push_out_positions(layered, edges, body, 0.004, locked=locked, within=within)
    assert np.array_equal(result.positions[front[:3]], points[front[:3]])
    lifted = np.linalg.norm(result.positions[len(points):] - outer, axis=1)
    assert lifted.min() > 0.007
    assert np.array_equal(result.positions[sleeve], points[sleeve])


def test_the_push_spreads_into_the_cloth_around_without_a_step():
    # Cloth lying 5 mm over the torso, and a small hard point of the body 9 mm under the surface of one vertex.
    rings, segments = 30, 48
    levels = np.linspace(0.0, 0.3, rings)
    angles = np.linspace(0, 2 * math.pi, segments, endpoint=False)
    points = np.array([(0.125 * math.cos(a), 0.125 * math.sin(a), z) for z in levels for a in angles])
    edges = np.array([(r * segments + s, r * segments + (s + 1) % segments) for r in range(rings)
                      for s in range(segments)] + [(r * segments + s, (r + 1) * segments + s)
                                                   for r in range(rings - 1) for s in range(segments)])
    poked = 15 * segments + 12
    tip = points[poked] / np.linalg.norm(points[poked] * [1, 1, 0]) * [1, 1, 0] * 0.122 + [0, 0, points[poked][2]]
    body = Capsules([((0, 0, -0.5), (0, 0, 0.8), 0.12)], [(tip, 0.008)])
    result = garment.push_out_positions(points, edges, body, 0.004)
    moves = np.linalg.norm(result.positions - points, axis=1)
    assert body(result.positions)[0].min() > 0.004 - 1e-4
    steps = np.abs(moves[edges[:, 0]] - moves[edges[:, 1]])
    assert steps.max() < 0.5 * moves[poked]
    unspread = garment.push_out_positions(points, edges, body, 0.004, spread=0)
    unspread_moves = np.linalg.norm(unspread.positions - points, axis=1)
    assert np.abs(unspread_moves[edges[:, 0]] - unspread_moves[edges[:, 1]]).max() > 0.8 * unspread_moves[poked]
