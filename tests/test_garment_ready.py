# SPDX-License-Identifier: GPL-3.0-or-later
"""Game Ready's steps without Blender: Prepare Garment's faces turned away from the body and its back shell, on
synthetic garments."""

from __future__ import annotations

import numpy as np

from durty_cloth_tool_link import garment
from tests.support import synthetic
from tests.test_garment_fix import loose_body


def face_normals(points: np.ndarray, triangles: np.ndarray) -> np.ndarray:
    a, b, c = (points[triangles[:, i]] for i in range(3))
    normals = np.cross(b - a, c - a)
    return normals / np.linalg.norm(normals, axis=1, keepdims=True)


def facing_body(points: np.ndarray, triangles: np.ndarray, body) -> np.ndarray:
    """How each triangle faces the body: the dot product of its normal with the body's outward normal nearest to
    its centre (positive: it faces away from the body)."""
    _signed, _nearest, normals = body(points[triangles].mean(axis=1))
    return np.einsum("ij,ij->i", face_normals(points, triangles), normals)


#: The torso of the synthetic top: its first 40 rings of 48 vertices, two triangles per quad.
TORSO = 40 * 48


def trunk(points: np.ndarray, triangles: np.ndarray) -> np.ndarray:
    """The torso triangles in front of and behind the loose body's torso (below its shoulders, away from its arms),
    where the body's normal there is clear."""
    centres = points[triangles].mean(axis=1)
    return (np.arange(len(triangles)) < 2 * TORSO) & (centres[:, 2] < 0.36) & (np.abs(centres[:, 0]) < 0.12)


def flipped_tee():
    tee = synthetic.top("long")
    triangles = synthetic.triangles(tee.faces)
    flipped = triangles.copy()
    chosen = np.arange(0, len(triangles), 4)  # a quarter of the faces wound the other way
    flipped[chosen] = flipped[chosen][:, ::-1]
    return tee, flipped, chosen


def test_prepare_turns_every_face_of_a_top_away_from_the_body():
    tee, triangles, chosen = flipped_tee()
    body = loose_body()
    beside = trunk(tee.positions, triangles)
    assert (facing_body(tee.positions, triangles, body)[chosen[beside[chosen]]] < 0).all()
    _signed, _nearest, normals = body(tee.positions[triangles].mean(axis=1))
    turn = garment.faces_to_turn(tee.positions, triangles, normals)
    assert np.array_equal(np.nonzero(turn)[0], chosen)  # exactly the faces wound the wrong way
    triangles[turn] = triangles[turn][:, ::-1]
    assert (facing_body(tee.positions, triangles, body)[beside] > 0).all()


def test_a_closed_part_and_a_lining_keep_their_faces():
    tee, triangles, chosen = flipped_tee()
    body = loose_body()
    # A closed box (a buckle) wound the right way: its faces facing the body are its inside walls, which stay.
    box = np.array([(x, y, z) for x in (-0.03, 0.03) for y in (-0.16, -0.14) for z in (0.0, 0.05)])
    box_triangles = len(tee.positions) + np.array([
        (0, 1, 3), (0, 3, 2), (4, 6, 7), (4, 7, 5), (0, 4, 5), (0, 5, 1),
        (2, 3, 7), (2, 7, 6), (0, 2, 6), (0, 6, 4), (1, 5, 7), (1, 7, 3)])
    points = np.concatenate([tee.positions, box])
    every = np.concatenate([triangles, box_triangles])
    lining = np.zeros(len(every), dtype=bool)
    lining[: 2 * TORSO] = True  # the torso as a lining: its faces face the body
    _signed, _nearest, normals = body(points[every].mean(axis=1))
    turn = garment.faces_to_turn(points, every, normals, lining=lining)
    assert not turn[len(triangles):].any()
    every[turn] = every[turn][:, ::-1]
    facing = facing_body(points, every, body)
    beside = np.concatenate([trunk(tee.positions, triangles), np.zeros(len(box_triangles), dtype=bool)])
    sleeves = np.arange(len(every)) >= 2 * TORSO
    sleeves[len(triangles):] = False
    assert (facing[beside] < 0).all()
    assert np.array_equal(turn[sleeves], np.isin(np.nonzero(sleeves)[0], chosen))  # the sleeves face out


def test_thickness_zero_leaves_the_mesh_and_thickness_adds_a_back_shell():
    tee = synthetic.top("short")
    triangles = synthetic.triangles(tee.faces)
    body = loose_body()
    same = garment.back_shell(tee.positions, triangles, 0.0)
    assert np.array_equal(same.positions, tee.positions) and np.array_equal(same.triangles, triangles)
    shell = garment.back_shell(tee.positions, triangles, 0.003)
    count = len(tee.positions)
    inner = shell.positions[count:]
    assert len(inner) == count and np.array_equal(shell.source, np.arange(count))
    # Every shell vertex lies the thickness behind its own, nearer the body; the shell's faces face the body.
    assert np.allclose(np.linalg.norm(inner - tee.positions, axis=1), 0.003)
    low = (tee.positions[:, 2] < 0.36) & (np.abs(tee.positions[:, 0]) < 0.12)
    low[TORSO:] = False
    assert (body(inner[low])[0] < body(tee.positions[low])[0]).all()
    back = shell.triangles[len(triangles): 2 * len(triangles)]
    beside = trunk(tee.positions, triangles)
    assert (back >= count).all() and (facing_body(shell.positions, back[beside], body) < 0).all()
    # The open edges (hems, cuffs, the neck) are closed by a rim between the two layers.
    rim = shell.triangles[2 * len(triangles):]
    open_edges = int(garment.open_edge_vertices(triangles, count).sum())
    assert len(rim) == 2 * open_edges
    assert not garment.open_edge_vertices(shell.triangles, len(shell.positions)).any()
