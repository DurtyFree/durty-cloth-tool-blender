# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2026 Schmid Software Solutions (https://schmid-software.de)
"""Synthetic garments and a synthetic body for the garment fitting tests: tubes and rings in ped space (Z up, the
ped facing -Y, its left at +X), with the joints they were built around. numpy only, so the Blender smoke can
build the same meshes."""

from __future__ import annotations

import math
from typing import Dict, List, NamedTuple, Tuple

import numpy as np

SHOULDER = 0.16
SHOULDER_Z = 0.44
NECK_Z = 0.55
HEM_Z = -0.08


class Mesh(NamedTuple):
    positions: np.ndarray  # (N, 3)
    faces: List[Tuple[int, ...]]
    joints: Dict[str, Tuple[float, float, float]]

    @property
    def edges(self) -> np.ndarray:
        found = set()
        for face in self.faces:
            for a, b in zip(face, face[1:] + face[:1]):
                found.add((min(a, b), max(a, b)))
        return np.array(sorted(found), dtype=np.int64)


class _Builder:
    def __init__(self) -> None:
        self.points: List[np.ndarray] = []
        self.faces: List[Tuple[int, ...]] = []

    def tube(self, centres: np.ndarray, radii: np.ndarray, axis_u: np.ndarray, axis_v: np.ndarray,
             segments: int = 24, closed: bool = False) -> None:
        """A tube of rings around ``centres`` (each ring in the plane of ``axis_u`` and ``axis_v``; ``axis_u`` x
        ``axis_v`` points along the tube, so the faces face outwards). ``closed`` caps both ends."""
        start = sum(len(p) for p in self.points)
        angles = np.linspace(0, 2 * math.pi, segments, endpoint=False)
        rings = []
        for centre, (ru, rv) in zip(centres, radii):
            ring = centre + np.outer(np.cos(angles) * ru, axis_u) + np.outer(np.sin(angles) * rv, axis_v)
            rings.append(ring)
        self.points.append(np.concatenate(rings))
        for r in range(len(rings) - 1):
            for s in range(segments):
                a = start + r * segments + s
                b = start + r * segments + (s + 1) % segments
                self.faces.append((a, b, b + segments, a + segments))
        if closed:
            first = sum(len(p) for p in self.points)
            self.points.append(np.asarray([centres[0], centres[-1]], dtype=np.float64).reshape(2, 3))
            last = start + (len(rings) - 1) * segments
            for s in range(segments):
                self.faces.append((start + (s + 1) % segments, start + s, first))
                self.faces.append((last + s, last + (s + 1) % segments, first + 1))

    def mesh(self, joints: Dict[str, Tuple[float, float, float]]) -> Mesh:
        return Mesh(np.concatenate(self.points), self.faces, joints)


def _direction(side: float, angle: float) -> np.ndarray:
    a = math.radians(angle)
    return np.array([side * math.cos(a), 0.0, -math.sin(a)])


def top(sleeves: str = "short", arm_angle: float = 45.0, scale: float = 1.0, offset=(0.0, 0.0, 0.0),
        hem_z: float = HEM_Z) -> Mesh:
    """A top: an elliptic torso that narrows to the neck, and sleeves (``none``, ``short`` or ``long``) along
    arms at ``arm_angle`` degrees below the horizontal (45 for an A-pose, 0 for a T-pose)."""
    builder = _Builder()
    levels = np.linspace(hem_z, NECK_Z, 40)
    radii = []
    for z in levels:
        if z <= SHOULDER_Z - 0.02:
            radii.append((0.175, 0.125))
        else:
            t = (z - (SHOULDER_Z - 0.02)) / (NECK_Z - (SHOULDER_Z - 0.02))
            radii.append((0.175 - 0.105 * t, 0.125 - 0.06 * t))
    centres = np.column_stack([np.zeros_like(levels), np.zeros_like(levels), levels])
    builder.tube(centres, np.array(radii), np.array([1.0, 0, 0]), np.array([0, 1.0, 0]), segments=48)
    joints: Dict[str, Tuple[float, float, float]] = {"neck": (0.0, 0.0, NECK_Z - 0.01)}
    upper, fore = 0.28, 0.26
    for side, suffix in ((1.0, "l"), (-1.0, "r")):
        shoulder = np.array([side * SHOULDER, 0.0, SHOULDER_Z])
        direction = _direction(side, arm_angle)
        elbow = shoulder + direction * upper
        wrist = elbow + direction * fore
        joints[f"shoulder_{suffix}"] = tuple(shoulder)
        joints[f"elbow_{suffix}"] = tuple(elbow)
        joints[f"wrist_{suffix}"] = tuple(wrist)
        length = {"none": 0.0, "short": 0.2, "long": upper + fore + 0.02}[sleeves]
        if length:
            steps = np.linspace(0.02, length, max(4, int(length / 0.025)))
            ring_centres = shoulder + np.outer(steps, direction)
            normal = np.cross(np.array([0, 1.0, 0]), direction)
            builder.tube(ring_centres, np.full((len(steps), 2), 0.065), normal, np.array([0, 1.0, 0]), segments=20)
    mesh = builder.mesh(joints)
    positions = mesh.positions * scale + np.asarray(offset)
    joints = {k: tuple(np.asarray(v) * scale + np.asarray(offset)) for k, v in joints.items()}
    return Mesh(positions, mesh.faces, joints)


def pants(length: float = 0.95, offset=(0.0, 0.0, 0.0)) -> Mesh:
    """Trousers: a pelvis tube from the waistband to the crotch and two leg tubes (``length`` below the waist)."""
    builder = _Builder()
    waist, crotch = 0.05, -0.13
    levels = np.linspace(crotch, waist, 10)
    centres = np.column_stack([np.zeros_like(levels), np.zeros_like(levels), levels])
    builder.tube(centres, np.full((len(levels), 2), (0.18, 0.13)), np.array([1.0, 0, 0]), np.array([0, 1.0, 0]),
                 segments=48)
    joints = {"pelvis": (0.0, 0.0, waist - 0.05)}
    for side, suffix in ((1.0, "l"), (-1.0, "r")):
        top_centre = np.array([side * 0.095, 0.0, crotch])
        bottom = np.array([side * 0.12, 0.0, waist - length])
        steps = np.linspace(0.0, 1.0, 30)
        ring_centres = top_centre + np.outer(steps, bottom - top_centre)
        builder.tube(ring_centres, np.full((len(steps), 2), 0.08), np.array([0, 1.0, 0]), np.array([1.0, 0, 0]),
                     segments=24)
        joints[f"hip_{suffix}"] = (side * 0.09, 0.0, -0.04)
    mesh = builder.mesh(joints)
    return Mesh(mesh.positions + np.asarray(offset), mesh.faces,
                {k: tuple(np.asarray(v) + np.asarray(offset)) for k, v in joints.items()})


def body(arm_angle: float = 45.0) -> Mesh:
    """A mannequin a little smaller than :func:`top`: torso, head, arms at ``arm_angle`` and legs, closed at
    the ends, with the sole at z -1.0."""
    builder = _Builder()
    levels = np.linspace(-0.15, 0.5, 30)
    radii = []
    for z in levels:
        if z <= 0.40:
            radii.append((0.155, 0.105))
        else:
            t = (z - 0.40) / 0.10
            radii.append((0.155 - 0.095 * t, 0.105 - 0.05 * t))
    centres = np.column_stack([np.zeros_like(levels), np.zeros_like(levels), levels])
    builder.tube(centres, np.array(radii), np.array([1.0, 0, 0]), np.array([0, 1.0, 0]), segments=40,
                 closed=True)
    head = np.linspace(0.5, 0.78, 10)
    head_centres = np.column_stack([np.zeros_like(head), np.zeros_like(head), head])
    head_radii = np.column_stack([0.06 + 0.04 * np.sin(np.linspace(0.3, 2.8, 10))] * 2)
    builder.tube(head_centres, head_radii, np.array([1.0, 0, 0]), np.array([0, 1.0, 0]), segments=24,
                 closed=True)
    joints: Dict[str, Tuple[float, float, float]] = {}
    for side in (1.0, -1.0):
        shoulder = np.array([side * SHOULDER, 0.0, SHOULDER_Z])
        direction = _direction(side, arm_angle)
        steps = np.linspace(0.0, 0.58, 24)
        ring_centres = shoulder + np.outer(steps, direction)
        normal = np.cross(np.array([0, 1.0, 0]), direction)
        builder.tube(ring_centres, np.full((len(steps), 2), 0.045), normal, np.array([0, 1.0, 0]), segments=16,
                     closed=True)
        leg_top = np.array([side * 0.09, 0.0, -0.1])
        leg_bottom = np.array([side * 0.11, 0.0, -1.0])
        steps = np.linspace(0.0, 1.0, 30)
        builder.tube(leg_top + np.outer(steps, leg_bottom - leg_top), np.full((30, 2), 0.065),
                     np.array([0, 1.0, 0]), np.array([1.0, 0, 0]), segments=16, closed=True)
    return builder.mesh(joints)


#: A small skeleton in the shape of a freemode skeleton (made up, nothing of the game): (name, parent index, head in
#: ped space). The bones are listed depth first with each bone's children in order, as a ped skeleton lists them,
#: so a bone's index is its position in the armature Sollumz imports.
SKELETON_BONES = (
    ("SKEL_ROOT", -1, (0.0, 0.0, 0.0)),
    ("SKEL_Pelvis", 0, (0.0, 0.0, -0.02)),
    ("SKEL_L_Thigh", 1, (0.09, 0.0, -0.1)),
    ("SKEL_L_Calf", 2, (0.1, 0.0, -0.55)),
    ("SKEL_L_Foot", 3, (0.11, 0.0, -0.95)),
    ("SKEL_R_Thigh", 1, (-0.09, 0.0, -0.1)),
    ("SKEL_R_Calf", 5, (-0.1, 0.0, -0.55)),
    ("SKEL_R_Foot", 6, (-0.11, 0.0, -0.95)),
    ("SKEL_Spine_Root", 0, (0.0, 0.0, 0.0)),
    ("SKEL_Spine0", 8, (0.0, 0.0, 0.08)),
    ("SKEL_Spine1", 9, (0.0, 0.0, 0.16)),
    ("SKEL_Spine2", 10, (0.0, 0.0, 0.26)),
    ("SKEL_Spine3", 11, (0.0, 0.0, 0.36)),
    ("SKEL_L_Clavicle", 12, (0.04, 0.0, 0.44)),
    ("SKEL_L_UpperArm", 13, (SHOULDER, 0.0, SHOULDER_Z)),
    ("SKEL_L_Forearm", 14, (SHOULDER + 0.198, 0.0, SHOULDER_Z - 0.198)),
    ("SKEL_L_Hand", 15, (SHOULDER + 0.382, 0.0, SHOULDER_Z - 0.382)),
    ("SKEL_R_Clavicle", 12, (-0.04, 0.0, 0.44)),
    ("SKEL_R_UpperArm", 17, (-SHOULDER, 0.0, SHOULDER_Z)),
    ("SKEL_R_Forearm", 18, (-SHOULDER - 0.198, 0.0, SHOULDER_Z - 0.198)),
    ("SKEL_R_Hand", 19, (-SHOULDER - 0.382, 0.0, SHOULDER_Z - 0.382)),
    ("SKEL_Neck_1", 12, (0.0, 0.0, NECK_Z - 0.01)),
    ("SKEL_Head", 21, (0.0, 0.0, 0.62)),
)


def skeleton_names() -> List[str]:
    return [name for name, _, _ in SKELETON_BONES]


def skeleton_template_xml(gender: str = "male", bones=SKELETON_BONES) -> bytes:
    """A skeleton template as Durty Cloth Tool sends it for ``skeleton.template``, in CodeWalker XML: one drawable named
    after the freemode ped of ``gender`` that holds only the skeleton and an empty shader group. The skeleton is
    :data:`SKELETON_BONES` (synthetic; no game data)."""
    ped = "mp_m_freemode_01" if gender == "male" else "mp_f_freemode_01"
    children: Dict[int, List[int]] = {}
    for index, (_, parent, _) in enumerate(bones):
        children.setdefault(parent, []).append(index)
    items = []
    for index, (name, parent, head) in enumerate(bones):
        siblings = children[parent]
        position = siblings.index(index)
        sibling = siblings[position + 1] if position + 1 < len(siblings) else -1
        origin = bones[parent][2] if parent >= 0 else (0.0, 0.0, 0.0)
        x, y, z = (round(head[i] - origin[i], 6) for i in range(3))
        items.append(
            f"        <Item>\n"
            f"          <Name>{name}</Name>\n"
            f"          <Tag value=\"{1000 + index}\" />\n"
            f"          <Index value=\"{index}\" />\n"
            f"          <ParentIndex value=\"{parent}\" />\n"
            f"          <SiblingIndex value=\"{sibling}\" />\n"
            f"          <Flags>RotX, RotY, RotZ</Flags>\n"
            f"          <Translation x=\"{x}\" y=\"{y}\" z=\"{z}\" />\n"
            f"          <Rotation x=\"0\" y=\"0\" z=\"0\" w=\"1\" />\n"
            f"          <Scale x=\"1\" y=\"1\" z=\"1\" />\n"
            f"          <TransformUnk x=\"0\" y=\"0\" z=\"0\" w=\"0\" />\n"
            f"        </Item>\n")
    text = (
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
        "<DrawableDictionary>\n"
        "  <Item>\n"
        f"    <Name>{ped}</Name>\n"
        "    <BoundingSphereCenter x=\"0\" y=\"0\" z=\"-0.2\" />\n"
        "    <BoundingSphereRadius value=\"1.1\" />\n"
        "    <BoundingBoxMin x=\"-0.6\" y=\"-0.2\" z=\"-1\" />\n"
        "    <BoundingBoxMax x=\"0.6\" y=\"0.2\" z=\"0.7\" />\n"
        "    <LodDistHigh value=\"9998\" />\n"
        "    <LodDistMed value=\"9998\" />\n"
        "    <LodDistLow value=\"9998\" />\n"
        "    <LodDistVlow value=\"9998\" />\n"
        "    <ShaderGroup>\n"
        "      <Shaders />\n"
        "    </ShaderGroup>\n"
        "    <Skeleton>\n"
        "      <Unknown1C value=\"0\" />\n"
        "      <Unknown50 value=\"0\" />\n"
        "      <Unknown54 value=\"0\" />\n"
        "      <Unknown58 value=\"0\" />\n"
        "      <Bones>\n"
        + "".join(items) +
        "      </Bones>\n"
        "    </Skeleton>\n"
        "  </Item>\n"
        "</DrawableDictionary>\n"
    )
    return text.encode("utf-8")


def skeleton_template_file(gender: str = "male") -> str:
    """The file name Durty Cloth Tool gives the template (the drawable is named after the ped, the file differs)."""
    return ("mp_m_freemode_01" if gender == "male" else "mp_f_freemode_01") + "_skeleton.ydd.xml"


def triangles(faces: List[Tuple[int, ...]]) -> np.ndarray:
    tris = []
    for face in faces:
        for i in range(1, len(face) - 1):
            tris.append((face[0], face[i], face[i + 1]))
    return np.array(tris, dtype=np.int64)
