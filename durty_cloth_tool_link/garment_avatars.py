# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2026 Schmid Software Solutions (https://schmid-software.de)
"""The avatars of Marvelous Designer and CLO, without Blender: where their joints are, as markers in ped space.

A garment draped in Marvelous Designer or CLO hangs on the joints of the avatar it was made on. When that avatar is
known, its joints are the garment's markers, exactly and in the pose it was draped in, whatever the garment's shape:

* :data:`AVATAR_BONES` names the bones of the avatars' rig (as an FBX export with the avatar carries it) behind each
  marker, and :func:`avatar_markers` turns those bones' positions into markers. Import Garment uses it when the file
  holds the rigged avatar; ``tools/measure_avatar.py`` uses it to measure a stock avatar for :data:`AVATARS`.
* :data:`AVATARS` holds the stock avatars measured so far: their markers in ped space (metres, the ped facing -Y,
  its left at +X, the avatar's soles moved to the ped's, 1 m below its origin, as Import Garment moves a garment made
  on an avatar standing on the ground), the pose they stand in and where each was measured. Only the joint positions
  derived from the avatar's rig are kept here, never the avatar itself.

Nothing here imports Blender.
"""

from __future__ import annotations

import json
import math
from typing import Any, Dict, Mapping, NamedTuple, Optional, Tuple

from . import garment

#: The bones of the Marvelous Designer and CLO avatars' rig behind each marker (the first name the rig has wins): the
#: pelvis, the upper chest, the base of the neck, the head's joint, and each arm and leg joint.
AVATAR_BONES: Dict[str, Tuple[str, ...]] = {
    "pelvis": ("Pelvis",),
    "chest": ("Spine3", "Spine2"),
    "neck": ("Neck",),
    "head": ("Head",),
    "shoulder_l": ("Left_Arm",), "elbow_l": ("Left_ForeArm",), "wrist_l": ("Left_Hand",),
    "hip_l": ("Left_thigh",), "knee_l": ("Left_shin",), "ankle_l": ("Left_ankle",),
    "shoulder_r": ("Right_Arm",), "elbow_r": ("Right_ForeArm",), "wrist_r": ("Right_Hand",),
    "hip_r": ("Right_thigh",), "knee_r": ("Right_shin",), "ankle_r": ("Right_ankle",),
}
#: The markers a rig must give before it counts as such an avatar: the torso and both arms.
REQUIRED = ("pelvis", "neck", "shoulder_l", "elbow_l", "wrist_l", "shoulder_r", "elbow_r", "wrist_r")


def avatar_markers(bones: Mapping[str, Any]) -> Optional[Dict[str, garment.Vector]]:
    """The markers of an avatar from its bones' positions (``bones``: bone name to its head, in ped space), or
    ``None`` when the rig is not one of these avatars'."""
    found: Dict[str, garment.Vector] = {}
    for marker, names in AVATAR_BONES.items():
        for name in names:
            if name in bones:
                x, y, z = (float(v) for v in bones[name])
                if all(math.isfinite(v) for v in (x, y, z)):
                    found[marker] = (x, y, z)
                break
    if any(name not in found for name in REQUIRED):
        return None
    return found


def arm_angle(markers: Mapping[str, Any]) -> Optional[float]:
    """The pose's arm angle below the horizontal (degrees, both arms' mean)."""
    angles = [a for a in (garment.arm_angle(markers, "l"), garment.arm_angle(markers, "r")) if a is not None]
    return round(sum(angles) / len(angles), 1) if angles else None


def source_pose(markers: Mapping[str, Any]) -> str:
    """``t_pose`` for arms within 15 degrees of the horizontal, ``a_pose`` otherwise."""
    angle = arm_angle(markers)
    return "t_pose" if angle is not None and abs(angle) < 15.0 else "a_pose"


def markers_json(markers: Mapping[str, Any]) -> str:
    return json.dumps({name: [round(float(v), 4) for v in markers[name]] for name in sorted(markers)},
                      separators=(",", ":"))


def parse_markers(text: str) -> Optional[Dict[str, garment.Vector]]:
    """Markers :func:`markers_json` wrote (kept on a garment imported with its avatar), or ``None``."""
    try:
        data = json.loads(text) if text else None
    except (TypeError, ValueError):
        return None
    if not isinstance(data, dict):
        return None
    found: Dict[str, garment.Vector] = {}
    for name, value in data.items():
        if name not in garment.MARKERS or not isinstance(value, list) or len(value) != 3:
            return None
        if not all(isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) and abs(v) <= 10
                   for v in value):
            return None
        found[name] = (float(value[0]), float(value[1]), float(value[2]))
    return found if all(name in found for name in REQUIRED) else None


class Avatar(NamedTuple):
    """A stock avatar: its markers in ped space, the pose it stands in, its gender and where it was measured."""

    markers: Dict[str, garment.Vector]
    pose: str
    arm_angle: float
    gender: str
    measured: str


def _mirrored(left: Dict[str, garment.Vector]) -> Dict[str, garment.Vector]:
    markers = dict(left)
    for name, (x, y, z) in left.items():
        if name in garment.MIRRORED:
            markers[garment.MIRRORED[name]] = (-x, y, z)
    return markers


#: The stock avatars measured so far (``tools/measure_avatar.py``), by the add-on's own id. Their markers are the
#: joints of the avatar as it stands when the garment is draped, moved to the ped's ground.
AVATARS: Dict[str, Avatar] = {
    # MaleTemplate_Manne_01, the male template of CLO and Marvelous Designer, in the A-pose it stands in: measured
    # from the rigged avatar exported with a sample garment (CLO 2024.2), 2026-10-06. Symmetric to 0.1 mm.
    "manne": Avatar(_mirrored({
        "pelvis": (0.0, 0.0023, 0.0499),
        "chest": (0.0, -0.0055, 0.4813),
        "neck": (0.0, 0.0216, 0.6111),
        "head": (0.0, -0.0046, 0.7309),
        "shoulder_l": (0.1757, 0.042, 0.5149),
        "elbow_l": (0.3845, 0.0305, 0.2605),
        "wrist_l": (0.556, -0.0311, 0.0722),
        "hip_l": (0.0998, 0.0142, -0.0438),
        "knee_l": (0.0994, 0.0203, -0.4748),
        "ankle_l": (0.0999, 0.0342, -0.9267),
    }), "a_pose", 48.8, "male", "2026-10-06"),
}
#: The stock avatars still to measure (by their template ids): seen in sample projects, but never exported with their
#: rig on this machine.
TO_MEASURE = ("5.1_MaleTemplate_09",)


def avatar(name: str) -> Optional[Avatar]:
    return AVATARS.get(name)


__all__ = ["AVATARS", "AVATAR_BONES", "Avatar", "REQUIRED", "TO_MEASURE", "arm_angle", "avatar", "avatar_markers",
           "markers_json", "parse_markers", "source_pose"]
