# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2026 Schmid Software Solutions (https://schmid-software.de)
"""A synthetic character for the Custom Ped tests: a mannequin of tubes standing on the ground in ped space (Z up,
facing -Y, its left at +X), 1.8 m tall, with the joints it was built around. Its body, head, hair and eyes are
separate parts, as a character from a modelling app usually is. Made from nothing of the game: the proportions are
the usual human figure's. numpy only, so the Blender smoke builds the same character."""

from __future__ import annotations

import math
from typing import Dict, List, NamedTuple, Tuple

import numpy as np

HEIGHT = 1.8


class Part(NamedTuple):
    name: str
    role: str
    positions: np.ndarray  # (N, 3)
    faces: List[Tuple[int, ...]]

    @property
    def triangles(self) -> np.ndarray:
        tris = []
        for face in self.faces:
            for i in range(1, len(face) - 1):
                tris.append((face[0], face[i], face[i + 1]))
        return np.array(tris, dtype=np.int64)

    @property
    def edges(self) -> np.ndarray:
        found = set()
        for face in self.faces:
            for a, b in zip(face, face[1:] + face[:1]):
                found.add((min(a, b), max(a, b)))
        return np.array(sorted(found), dtype=np.int64)


class Character(NamedTuple):
    parts: List[Part]
    joints: Dict[str, Tuple[float, float, float]]

    @property
    def positions(self) -> np.ndarray:
        return np.concatenate([part.positions for part in self.parts])

    @property
    def triangles(self) -> np.ndarray:
        result, offset = [], 0
        for part in self.parts:
            result.append(part.triangles + offset)
            offset += len(part.positions)
        return np.concatenate(result)


class _Builder:
    def __init__(self) -> None:
        self.points: List[np.ndarray] = []
        self.faces: List[Tuple[int, ...]] = []
        self.count = 0

    def tube(self, centres, radii, axis_u, axis_v, segments: int = 16, closed: bool = True) -> None:
        """Rings around ``centres`` in the plane of ``axis_u`` and ``axis_v`` (their cross product points along the
        tube), capped at both ends."""
        centres = np.asarray(centres, dtype=np.float64)
        axis_u, axis_v = np.asarray(axis_u, dtype=np.float64), np.asarray(axis_v, dtype=np.float64)
        start = self.count
        angles = np.linspace(0, 2 * math.pi, segments, endpoint=False)
        for centre, (ru, rv) in zip(centres, radii):
            self.points.append(centre + np.outer(np.cos(angles) * ru, axis_u) + np.outer(np.sin(angles) * rv, axis_v))
        rings = len(centres)
        for r in range(rings - 1):
            for s in range(segments):
                a = start + r * segments + s
                b = start + r * segments + (s + 1) % segments
                self.faces.append((a, b, b + segments, a + segments))
        self.count += rings * segments
        if closed:
            ends = self.count
            self.points.append(np.asarray([centres[0], centres[-1]], dtype=np.float64))
            last = start + (rings - 1) * segments
            for s in range(segments):
                self.faces.append((start + (s + 1) % segments, start + s, ends))
                self.faces.append((last + s, last + (s + 1) % segments, ends + 1))
            self.count += 2

    def sphere(self, centre, radius: float, rings: int = 8, segments: int = 12) -> None:
        heights = np.linspace(-0.95, 0.95, rings)
        centres = [np.asarray(centre) + np.array([0.0, 0.0, h * radius]) for h in heights]
        radii = [(radius * math.sqrt(1 - h * h),) * 2 for h in heights]
        self.tube(centres, radii, (1.0, 0, 0), (0, 1.0, 0), segments=segments)

    def part(self, name: str, role: str) -> Part:
        return Part(name, role, np.concatenate(self.points), list(self.faces))


def _limb(builder: _Builder, start, end, r0: float, r1: float, steps: int = 12, segments: int = 14) -> None:
    start, end = np.asarray(start, dtype=np.float64), np.asarray(end, dtype=np.float64)
    axis = (end - start) / np.linalg.norm(end - start)
    helper = np.array([0.0, 1.0, 0.0]) if abs(axis[1]) < 0.9 else np.array([1.0, 0.0, 0.0])
    u = np.cross(helper, axis)
    u /= np.linalg.norm(u)
    v = np.cross(axis, u)
    t = np.linspace(0, 1, steps)
    centres = start + np.outer(t, end - start)
    radii = [(r0 + (r1 - r0) * f,) * 2 for f in t]
    builder.tube(centres, radii, u, v, segments=segments)


def mannequin(arm_angle: float = 45.0, offset=(0.0, 0.0, 0.0), turn: float = 0.0, scale: float = 1.0) -> Character:
    """The mannequin with its arms ``arm_angle`` degrees below the horizontal (45 an A-pose, 0 a T-pose), moved by
    ``offset``, turned ``turn`` degrees about Z (counter-clockwise seen from above) and scaled by ``scale``."""
    joints: Dict[str, np.ndarray] = {
        "headTop": np.array([0.0, 0.0, 1.8]), "chin": np.array([0.0, -0.088, 1.585]),
        "neck": np.array([0.0, 0.0, 1.5]), "chest": np.array([0.0, 0.0, 1.31]), "pelvis": np.array([0.0, 0.0, 0.96]),
    }
    body = _Builder()
    # Torso: hips, waist, chest, shoulders; an ellipse wider than deep.
    levels = np.linspace(0.84, 1.48, 18)
    widths = np.interp(levels, [0.84, 1.0, 1.08, 1.28, 1.42, 1.48], [0.16, 0.165, 0.14, 0.17, 0.165, 0.09])
    depths = np.interp(levels, [0.84, 1.08, 1.28, 1.48], [0.11, 0.1, 0.115, 0.07])
    body.tube(np.column_stack([np.zeros_like(levels), np.zeros_like(levels), levels]),
              list(zip(widths, depths)), (1.0, 0, 0), (0, 1.0, 0), segments=28)
    neck = np.linspace(1.46, 1.6, 5)
    body.tube(np.column_stack([np.zeros_like(neck), np.zeros_like(neck), neck]), [(0.055, 0.055)] * 5,
              (1.0, 0, 0), (0, 1.0, 0), segments=16)
    a = math.radians(arm_angle)
    for sign, suffix in ((1.0, "L"), (-1.0, "R")):
        shoulder = np.array([sign * 0.185, 0.0, 1.455])
        direction = np.array([sign * math.cos(a), 0.0, -math.sin(a)])
        elbow = shoulder + direction * 0.335
        wrist = elbow + direction * 0.26
        tip = wrist + direction * 0.19
        _limb(body, shoulder - direction * 0.03, elbow, 0.055, 0.045)
        _limb(body, elbow, wrist, 0.045, 0.033)
        _limb(body, wrist, tip, 0.04, 0.022, steps=6)
        hip = np.array([sign * 0.09, 0.0, 0.92])
        knee = np.array([sign * 0.095, 0.0, 0.5])
        ankle = np.array([sign * 0.1, 0.0, 0.085])
        _limb(body, hip + np.array([0, 0, 0.06]), knee, 0.08, 0.055, steps=14)
        _limb(body, knee, ankle, 0.055, 0.04, steps=14)
        foot = np.linspace(0.06, -0.19, 8)
        body.tube(np.column_stack([np.full(8, sign * 0.1), foot, np.interp(foot, [-0.19, 0.06], [0.025, 0.045])]),
                  [(0.045, 0.035)] * 8, (1.0, 0, 0), (0, 0, 1.0), segments=12)
        joints.update({f"shoulder{suffix}": shoulder, f"elbow{suffix}": elbow, f"wrist{suffix}": wrist,
                       f"hip{suffix}": hip, f"knee{suffix}": knee, f"ankle{suffix}": ankle,
                       f"toe{suffix}": np.array([sign * 0.1, -0.12, 0.025])})
    parts = [body.part("Body", "body")]
    head = _Builder()
    levels = np.linspace(1.565, 1.8, 10)
    profile = np.sin(np.linspace(0.55, math.pi - 0.15, 10))
    head.tube(np.column_stack([np.zeros(10), np.full(10, -0.01), levels]),
              [(0.09 * p, 0.1 * p) for p in profile], (1.0, 0, 0), (0, 1.0, 0), segments=20)
    parts.append(head.part("Head", "head"))
    hair = _Builder()
    levels = np.linspace(1.7, 1.81, 5)
    profile = np.sin(np.linspace(1.2, math.pi - 0.05, 5))
    hair.tube(np.column_stack([np.zeros(5), np.full(5, 0.005), levels]), [(0.094 * p, 0.104 * p) for p in profile],
              (1.0, 0, 0), (0, 1.0, 0), segments=16)
    parts.append(hair.part("Hair", "hair"))
    eyes = _Builder()
    for sign in (1.0, -1.0):
        eyes.sphere((sign * 0.033, -0.088, 1.69), 0.012, rings=5, segments=8)
    parts.append(eyes.part("Eyes", "eyes"))

    angle = math.radians(turn)
    rotation = np.array([[math.cos(angle), -math.sin(angle), 0.0], [math.sin(angle), math.cos(angle), 0.0],
                         [0.0, 0.0, 1.0]])
    shift = np.asarray(offset, dtype=np.float64)

    def place(points: np.ndarray) -> np.ndarray:
        return (np.asarray(points) * scale) @ rotation.T + shift

    moved = [Part(p.name, p.role, place(p.positions), p.faces) for p in parts]
    return Character(moved, {name: tuple(float(c) for c in place(point[None])[0]) for name, point in joints.items()})
