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
