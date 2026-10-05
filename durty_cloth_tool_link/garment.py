# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2026 Schmid Software Solutions (https://schmid-software.de)
"""The garment fitting tools without Blender: slots and categories, the next-step hint, marker placement, body
regions, the fit check, the problem colours, mesh moves, seam welding, strip cutting, the local checks and pose
presets.

Positions are in ped space, in metres: Z up, the ped facing -Y and its left side at +X. That is the space of the
freemode body and of a garment imported from Marvelous Designer. Nothing here imports Blender; numpy does the
arithmetic, so the tests run without Blender.
"""

from __future__ import annotations

import json
import math
import re
from typing import Any, Dict, Iterable, List, Mapping, NamedTuple, Optional, Sequence, Tuple

import numpy as np

# --------------------------------------------------------------------------------------------------
# Slots, categories, markers and regions
# --------------------------------------------------------------------------------------------------

GENDERS = ("male", "female")
#: The component slots the tools support, with Durty Cloth Tool's drawable type names.
SLOTS = ("jbib", "accs", "lowr", "feet")
CATEGORIES = ("vest", "tshirt", "long_sleeve", "long_jacket", "pants", "shorts", "shoes")
SLOT_CATEGORIES: Dict[str, Tuple[str, ...]] = {
    "jbib": ("vest", "tshirt", "long_sleeve", "long_jacket"),
    "accs": ("vest", "tshirt", "long_sleeve"),
    "lowr": ("pants", "shorts"),
    "feet": ("shoes",),
}
#: How far the sleeves of a top reach.
SLEEVES = {"vest": "none", "tshirt": "short", "long_sleeve": "long", "long_jacket": "long"}
LOWER = frozenset({"pants", "shorts"})
SOURCE_POSES = ("a_pose", "t_pose", "custom")

MARKERS = ("chest", "neck", "pelvis", "shoulder_l", "elbow_l", "wrist_l", "hip_l",
           "shoulder_r", "elbow_r", "wrist_r", "hip_r")
_LEFT = ("shoulder_l", "elbow_l", "wrist_l", "hip_l")
MIRRORED = {name: name[:-1] + "r" for name in _LEFT}
#: The markers of the lower categories (legs); shoes need none.
LOWER_MARKERS = ("pelvis", "hip_l", "hip_r")

#: Body regions, in the order the panels list them.
REGIONS = ("shoulders", "upper_arms", "chest", "back", "waist", "hips", "neck", "legs")
OTHER = -1

#: The arm angle below the horizontal that each source pose starts from (degrees).
POSE_ARM_ANGLE = {"a_pose": 45.0, "t_pose": 0.0, "custom": 45.0}

# Body proportions relative to the distance between the shoulder joints (the span); they place what a garment
# does not show (a short sleeve's wrist, the pelvis under a cropped top).
UPPER_ARM_PER_SPAN = 0.78
FOREARM_PER_SPAN = 0.72
NECK_TO_PELVIS_PER_SPAN = 1.45
CHEST_BELOW_SHOULDERS_PER_SPAN = 0.33
HIP_OFFSET_PER_SPAN = 0.25
#: The span assumed when nothing gives it (metres).
DEFAULT_SPAN = 0.36
#: The neck-to-pelvis height assumed for the legs' regions when the garment has no upper markers.
DEFAULT_TORSO = 0.52


def categories_for(slot: str) -> Tuple[str, ...]:
    return SLOT_CATEGORIES.get(slot, ())


def markers_for(category: str) -> Tuple[str, ...]:
    """The markers Auto Markers places for a category (none for shoes)."""
    if category == "shoes":
        return ()
    if category in LOWER:
        return LOWER_MARKERS
    return MARKERS


def regions_for(category: str) -> Tuple[str, ...]:
    """The regions a garment of this category covers, in panel order."""
    if category == "shoes":
        return ("legs",)
    if category in LOWER:
        return ("waist", "hips", "legs")
    if category == "long_jacket":
        return REGIONS
    covered = tuple(region for region in REGIONS if region != "legs")
    return covered if SLEEVES.get(category) != "none" else tuple(r for r in covered if r != "upper_arms")


# --------------------------------------------------------------------------------------------------
# The next step
# --------------------------------------------------------------------------------------------------


class FlowState(NamedTuple):
    """What the panel knows about the garment, for the next-step hint."""

    garment: bool = False
    body: bool = False
    category: str = "tshirt"
    source_pose: str = "a_pose"
    markers: int = 0
    converted: bool = False
    sculpting: bool = False
    checked: bool = False
    inside: int = 0
    prepared: bool = False
    materials: int = 1
    lods: bool = False
    sollumz: bool = True
    validated: bool = False
    #: What the latest Validate found: ``none`` (not run), ``blocking`` (errors), ``warnings`` or ``clean``.
    findings: str = "none"
    #: The add to a Durty Cloth Tool project: connected, a project open there, the garment on the Durty Cloth Tool
    #: skeleton of its gender, an add running, the garment added.
    connected: bool = False
    project: bool = False
    skeleton: bool = False
    adding: bool = False
    added: bool = False


def next_step(state: FlowState) -> str:
    """The text key of what to do next."""
    if state.sculpting:
        return "garment.next.sculpting"
    if not state.garment:
        return "garment.next.import"
    if not state.body:
        return "garment.next.body"
    if state.markers < len(markers_for(state.category)):
        return "garment.next.markers"
    if state.source_pose == "t_pose" and not state.converted:
        return "garment.next.tpose"
    if not state.checked and not state.prepared:
        return "garment.next.check"
    if state.inside > 0 and not state.prepared:
        return "garment.next.push"
    if not state.prepared:
        return "garment.next.prepare"
    if state.materials > 1:
        return "garment.next.combine"
    if state.sollumz and not state.lods:
        return "garment.next.lods"
    if not state.validated:
        if state.findings == "blocking":
            return "garment.next.validate-problems"
        if state.findings != "warnings":
            return "garment.next.validate"
    if state.added:
        return "garment.next.done"
    if state.adding:
        return "garment.next.adding"
    if not state.connected:
        return "garment.next.connect"
    if not state.project:
        return "garment.next.project"
    if not state.sollumz:
        return "garment.next.sollumz"
    if not state.skeleton:
        return "garment.next.skeleton"
    return "garment.next.add"


# --------------------------------------------------------------------------------------------------
# Mesh helpers
# --------------------------------------------------------------------------------------------------


def as_points(positions: Any) -> np.ndarray:
    points = np.asarray(positions, dtype=np.float64).reshape(-1, 3)
    return points


def median_edge_length(positions: np.ndarray, edges: Optional[np.ndarray]) -> float:
    if edges is None or len(edges) == 0:
        return 0.0
    edges = np.asarray(edges).reshape(-1, 2)
    lengths = np.linalg.norm(positions[edges[:, 1]] - positions[edges[:, 0]], axis=1)
    return float(np.median(lengths)) if lengths.size else 0.0


def neighbour_lists(count: int, edges: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """``(order, starts)``: the neighbours of vertex ``i`` are ``order[starts[i]:starts[i + 1]]``."""
    edges = np.asarray(edges, dtype=np.int64).reshape(-1, 2)
    a = np.concatenate([edges[:, 0], edges[:, 1]])
    b = np.concatenate([edges[:, 1], edges[:, 0]])
    order = np.argsort(a, kind="stable")
    starts = np.zeros(count + 1, dtype=np.int64)
    np.add.at(starts, a + 1, 1)
    return b[order], np.cumsum(starts)


def neighbour_mean(field: np.ndarray, edges: np.ndarray, count: int) -> np.ndarray:
    """The mean of each vertex's neighbours (the vertex itself where it has none)."""
    edges = np.asarray(edges, dtype=np.int64).reshape(-1, 2)
    field = np.asarray(field, dtype=np.float64)
    total = np.zeros_like(field)
    hits = np.zeros(count, dtype=np.float64)
    np.add.at(total, edges[:, 0], field[edges[:, 1]])
    np.add.at(total, edges[:, 1], field[edges[:, 0]])
    np.add.at(hits, edges[:, 0], 1.0)
    np.add.at(hits, edges[:, 1], 1.0)
    shape = (-1,) + (1,) * (field.ndim - 1)
    lonely = hits == 0
    hits[lonely] = 1.0
    mean = total / hits.reshape(shape)
    mean[lonely] = field[lonely]
    return mean


def soft_mask(mask: np.ndarray, edges: np.ndarray, rings: int = 3) -> np.ndarray:
    """Weights 1 on ``mask`` that fade out over ``rings`` rings of neighbours, so a moved region blends in."""
    weights = np.asarray(mask, dtype=np.float64).copy()
    count = weights.size
    for _ in range(max(0, rings)):
        spread = neighbour_mean(weights, edges, count)
        weights = np.maximum(weights, spread * 0.85)
    return np.clip(weights, 0.0, 1.0)


def spread_offsets(offsets: np.ndarray, edges: np.ndarray, fixed: np.ndarray, iterations: int = 3,
                   falloff: float = 0.6) -> np.ndarray:
    """Offsets of ``fixed`` vertices kept, the others take a fading share of their neighbours', so a local move
    leaves no crease."""
    result = np.asarray(offsets, dtype=np.float64).copy()
    fixed = np.asarray(fixed, dtype=bool)
    count = len(result)
    for _ in range(max(0, iterations)):
        mean = neighbour_mean(result, edges, count) * falloff
        free = ~fixed
        longer = np.linalg.norm(mean, axis=1) > np.linalg.norm(result, axis=1)
        update = free & longer
        result[update] = mean[update]
    return result


def vertex_stretch(edges: np.ndarray, rest: np.ndarray, current: np.ndarray) -> np.ndarray:
    """Per vertex, the largest length ratio (now / rest) of the edges around it (1 where it has none)."""
    edges = np.asarray(edges, dtype=np.int64).reshape(-1, 2)
    count = len(current)
    stretch = np.ones(count, dtype=np.float64)
    if not len(edges):
        return stretch
    before = np.linalg.norm(rest[edges[:, 1]] - rest[edges[:, 0]], axis=1)
    after = np.linalg.norm(current[edges[:, 1]] - current[edges[:, 0]], axis=1)
    ratio = np.where(before > 1e-9, after / np.maximum(before, 1e-9), 1.0)
    np.maximum.at(stretch, edges[:, 0], ratio)
    np.maximum.at(stretch, edges[:, 1], ratio)
    return stretch


# --------------------------------------------------------------------------------------------------
# Markers
# --------------------------------------------------------------------------------------------------


class MarkerError(ValueError):
    """The markers could not be placed; ``code`` names the reason for the panel."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


Vector = Tuple[float, float, float]


def _vec(value: Any) -> np.ndarray:
    return np.asarray(value, dtype=np.float64).reshape(3)


def centre_x(markers: Mapping[str, Any]) -> float:
    """The x of the garment's centre plane: the centre markers, else the middle between paired markers, else 0."""
    centre = [float(_vec(markers[name])[0]) for name in ("chest", "neck", "pelvis") if name in markers]
    if centre:
        return float(np.mean(centre))
    pairs = [(name, MIRRORED[name]) for name in _LEFT if name in markers and MIRRORED[name] in markers]
    if pairs:
        return float(np.mean([(_vec(markers[a])[0] + _vec(markers[b])[0]) / 2 for a, b in pairs]))
    return 0.0


def mirror_markers(markers: Mapping[str, Any]) -> Dict[str, Vector]:
    """The markers with each right one replaced by its left one mirrored across the centre plane."""
    cx = centre_x(markers)
    result = {name: tuple(float(v) for v in _vec(value)) for name, value in markers.items()}
    for left, right in MIRRORED.items():
        if left in markers:
            x, y, z = (float(v) for v in _vec(markers[left]))
            result[right] = (2 * cx - x, y, z)
    return result  # type: ignore[return-value]


def _gap_extent(values: np.ndarray, gap: float) -> float:
    """How far sorted distances from the centre reach before the first gap wider than ``gap``."""
    if values.size == 0:
        return 0.0
    ordered = np.sort(values)
    jumps = np.nonzero(np.diff(ordered) > gap)[0]
    return float(ordered[jumps[0]] if jumps.size else ordered[-1])


def _y_centre(points: np.ndarray, fallback: float) -> float:
    if not len(points):
        return fallback
    return float((points[:, 1].min() + points[:, 1].max()) / 2)


def _slice(points: np.ndarray, z: float, half: float) -> np.ndarray:
    return points[np.abs(points[:, 2] - z) <= half]


def _unit(vector: np.ndarray) -> np.ndarray:
    length = float(np.linalg.norm(vector))
    return vector / length if length > 1e-9 else vector


def _pose_direction(side: float, source_pose: str) -> np.ndarray:
    angle = math.radians(POSE_ARM_ANGLE.get(source_pose, 45.0))
    return np.array([side * math.cos(angle), 0.0, -math.sin(angle)])


def auto_markers(positions: Any, category: str, source_pose: str = "a_pose",
                 edges: Optional[np.ndarray] = None) -> Dict[str, Vector]:
    """Joint markers for a garment from cross-sections of its mesh. Raises :class:`MarkerError` when the mesh
    does not look like the category."""
    points = as_points(positions)
    if category == "shoes":
        raise MarkerError("no-markers")
    if len(points) < 30 or not np.all(np.isfinite(points)):
        raise MarkerError("too-small")
    low, high = points.min(axis=0), points.max(axis=0)
    if high[2] - low[2] < 0.05:
        raise MarkerError("too-small")
    spacing = median_edge_length(points, edges)
    gap = max(0.025, 2.5 * spacing)
    if category in LOWER:
        return _lower_markers(points, gap)
    return _upper_markers(points, category, source_pose, gap)


def _upper_markers(points: np.ndarray, category: str, source_pose: str, gap: float) -> Dict[str, Vector]:
    low, high = points.min(axis=0), points.max(axis=0)
    height = high[2] - low[2]
    cx = float((low[0] + high[0]) / 2)
    dx = points[:, 0] - cx
    lateral = np.abs(dx)
    z = points[:, 2]

    # The torso's half-width: the lower part of a top, where sleeves (if they hang down) stand apart.
    widths = []
    for level in np.linspace(low[2] + 0.12 * height, low[2] + 0.5 * height, 9):
        band = np.abs(z - level) <= max(0.01, height / 60)
        for side in (1.0, -1.0):
            values = lateral[band & (np.sign(dx) == side)]
            if values.size >= 4:
                widths.append(_gap_extent(values, gap))
    if not widths:
        raise MarkerError("not-a-top")
    torso = float(np.median(widths))
    if torso < 0.05:
        raise MarkerError("not-a-top")

    # The neck opening: the highest vertices near the centre.
    near_centre = lateral < 0.45 * torso
    if not np.any(near_centre):
        raise MarkerError("not-a-top")
    top = float(z[near_centre].max())
    ring = points[near_centre & (z > top - 0.03)]
    neck = np.array([cx, float(ring[:, 1].mean()), float(ring[:, 2].mean()) - 0.01])

    # Shoulders: where the top's upper outline reaches the torso's width.
    sleeves = SLEEVES.get(category, "short")
    result: Dict[str, Vector] = {}
    shoulders: Dict[float, np.ndarray] = {}
    for side in (1.0, -1.0):
        outer = (np.sign(dx) == side) & (np.abs(lateral - torso) < max(0.03, gap))
        if not np.any(outer):
            raise MarkerError("not-a-top")
        upper_edge = float(z[outer].max())
        shoulder_z = min(upper_edge - 0.05, neck[2] - 0.03)
        near = outer & (np.abs(z - shoulder_z) < 0.06)
        y = _y_centre(points[near], float(neck[1]))
        shoulders[side] = np.array([cx + side * torso, y, shoulder_z])
    span = abs(shoulders[1.0][0] - shoulders[-1.0][0])

    # Sleeves: what stands apart from the torso in its cross-section, or reaches well beyond it higher up.
    torso_extent = np.zeros(len(points))
    levels = np.linspace(low[2], high[2], 61)
    half = (levels[1] - levels[0]) / 2 + 1e-9
    for level in levels:
        band = np.abs(z - level) <= half
        for side in (1.0, -1.0):
            selected = band & (np.sign(dx) == side)
            torso_extent[selected] = _gap_extent(lateral[selected], gap)
    apart = lateral > torso_extent + 1e-9
    wide = (lateral > 1.35 * torso + 0.01) & (z > low[2] + 0.45 * height)
    sleeve_mask = apart | wide

    arms: Dict[float, Tuple[np.ndarray, np.ndarray, np.ndarray]] = {}
    for side in (1.0, -1.0):
        shoulder = shoulders[side]
        own = sleeve_mask & (np.sign(dx) == side)
        enough = int(own.sum()) >= max(12, int(0.004 * len(points)))
        direction = _pose_direction(side, source_pose)
        if sleeves != "none" and enough:
            sleeve = points[own]
            distance = np.linalg.norm(sleeve - shoulder, axis=1)
            cuff = sleeve[distance >= distance.max() - 0.02]
            cuff_centre = cuff.mean(axis=0)
            candidate = _unit(cuff_centre - shoulder)
            down = math.degrees(math.atan2(-candidate[2], abs(candidate[0]) + 1e-12))
            if candidate[0] * side > 0 and -15.0 <= down <= 85.0:
                direction = candidate
            if sleeves == "long":
                wrist = cuff_centre - direction * 0.02
                elbow = shoulder + 0.53 * (wrist - shoulder)
                arms[side] = (shoulder, elbow, wrist)
                continue
        elif sleeves != "none":
            arms[side] = None  # type: ignore[assignment]
            continue
        elbow = shoulder + direction * UPPER_ARM_PER_SPAN * span
        wrist = elbow + direction * FOREARM_PER_SPAN * span
        arms[side] = (shoulder, elbow, wrist)
    if arms.get(1.0) is None and arms.get(-1.0) is None:
        raise MarkerError("no-sleeves")
    for side, other in ((1.0, -1.0), (-1.0, 1.0)):
        if arms.get(side) is None:  # a sleeve was not found on one side: mirror the other one
            arms[side] = tuple(np.array([2 * cx - p[0], p[1], p[2]]) for p in arms[other])  # type: ignore[index]

    shoulder_z = (shoulders[1.0][2] + shoulders[-1.0][2]) / 2
    chest_z = shoulder_z - CHEST_BELOW_SHOULDERS_PER_SPAN * span
    torso_points = points[lateral < torso]
    chest = np.array([cx, _y_centre(_slice(torso_points, chest_z, 0.02), float(neck[1])), chest_z])
    pelvis_z = float(neck[2] - NECK_TO_PELVIS_PER_SPAN * span)
    pelvis = np.array([cx, _y_centre(_slice(torso_points, pelvis_z, 0.02), float(chest[1])), pelvis_z])
    hip_z = pelvis_z - 0.06 * span

    result["chest"] = _tuple(chest)
    result["neck"] = _tuple(neck)
    result["pelvis"] = _tuple(pelvis)
    for side, suffix in ((1.0, "l"), (-1.0, "r")):
        shoulder, elbow, wrist = arms[side]  # type: ignore[misc]
        result[f"shoulder_{suffix}"] = _tuple(shoulder)
        result[f"elbow_{suffix}"] = _tuple(elbow)
        result[f"wrist_{suffix}"] = _tuple(wrist)
        result[f"hip_{suffix}"] = (cx + side * HIP_OFFSET_PER_SPAN * span, float(pelvis[1]), hip_z)
    return result


def _lower_markers(points: np.ndarray, gap: float) -> Dict[str, Vector]:
    low, high = points.min(axis=0), points.max(axis=0)
    cx = float((low[0] + high[0]) / 2)
    dx = points[:, 0] - cx
    z = points[:, 2]
    waist = float(high[2])
    pelvis_z = waist - 0.05
    top = _slice(points, waist - 0.01, 0.015)
    pelvis_y = _y_centre(top, float(points[:, 1].mean()))
    middle = np.abs(dx) < 0.015
    crotch = float(z[middle].min()) if np.any(middle) else waist - 0.25
    if crotch >= pelvis_z - 0.03:
        crotch = pelvis_z - 0.15  # no inseam found near the centre: assume an ordinary rise
    legs = points[np.abs(z - (crotch - 0.08)) <= 0.02]
    offsets = []
    for side in (1.0, -1.0):
        own = legs[np.sign(legs[:, 0] - cx) == side]
        offsets.append(abs(float(own[:, 0].mean()) - cx) if len(own) else 0.09)
    offset = 0.9 * float(np.mean(offsets))
    if not 0.03 <= offset <= 0.3:
        raise MarkerError("not-legs")
    hip_z = crotch + 0.7 * (pelvis_z - crotch)
    return {
        "pelvis": (cx, pelvis_y, pelvis_z),
        "hip_l": (cx + offset, pelvis_y, hip_z),
        "hip_r": (cx - offset, pelvis_y, hip_z),
    }


def _tuple(vector: np.ndarray) -> Vector:
    return (float(vector[0]), float(vector[1]), float(vector[2]))


# --------------------------------------------------------------------------------------------------
# Regions
# --------------------------------------------------------------------------------------------------


def classify_regions(positions: Any, markers: Mapping[str, Any]) -> np.ndarray:
    """The region of each point (an index into :data:`REGIONS`, or :data:`OTHER` for forearms and hands).

    Needs the pelvis (or both hips); missing upper markers are filled in from ordinary proportions."""
    points = as_points(positions)
    found = {name: _vec(value) for name, value in markers.items() if name in MARKERS}
    if "pelvis" not in found:
        if "hip_l" in found and "hip_r" in found:
            found["pelvis"] = (found["hip_l"] + found["hip_r"]) / 2 + np.array([0.0, 0.0, 0.03])
        else:
            raise MarkerError("no-markers")
    pelvis = found["pelvis"]
    cx = centre_x({k: tuple(v) for k, v in found.items()})
    if "shoulder_l" in found and "shoulder_r" in found:
        span = float(abs(found["shoulder_l"][0] - found["shoulder_r"][0]))
    elif "hip_l" in found and "hip_r" in found:
        span = float(abs(found["hip_l"][0] - found["hip_r"][0])) / (2 * HIP_OFFSET_PER_SPAN)
    else:
        span = DEFAULT_SPAN
    span = max(span, 0.1)
    lower = "neck" not in found  # trousers: their top is the waist, just above the pelvis
    neck = found.get("neck", pelvis + np.array([0.0, 0.0, DEFAULT_TORSO]))
    chest = found.get("chest", pelvis + 0.67 * (neck - pelvis))
    height = max(float(neck[2] - pelvis[2]), 0.1)

    region = np.full(len(points), OTHER, dtype=np.int64)
    x, y, z = points[:, 0], points[:, 1], points[:, 2]
    lateral = np.abs(x - cx)
    arm = np.zeros(len(points), dtype=bool)
    for side, suffix in ((1.0, "l"), (-1.0, "r")):
        shoulder, elbow = found.get(f"shoulder_{suffix}"), found.get(f"elbow_{suffix}")
        if shoulder is None or elbow is None:
            continue
        upper = elbow - shoulder
        length = float(np.linalg.norm(upper))
        if length < 1e-6:
            continue
        along = (points - shoulder) @ upper / (length * length)
        closest = shoulder + np.clip(along, 0.0, 1.0)[:, None] * upper
        distance = np.linalg.norm(points - closest, axis=1)
        reach = abs(float(shoulder[0]) - cx)
        mine = (np.sign(x - cx) == side) & (lateral > 0.9 * reach) & (along > 0.08)
        upper_arm = mine & (along <= 1.0) & (distance < 0.6 * length)
        forearm = mine & (along > 1.0)
        region[upper_arm] = REGIONS.index("upper_arms")
        arm |= upper_arm | forearm

    t = (z - pelvis[2]) / height
    torso = ~arm
    neck_mask = torso & (((t > 0.92) & (lateral < 0.33 * span)) | (t > 1.0))
    region[neck_mask] = REGIONS.index("neck")
    rest = torso & ~neck_mask
    region[rest & (t > 0.78)] = REGIONS.index("shoulders")
    trunk = rest & (t > 0.45) & (t <= 0.78)
    region[trunk & (y < chest[1])] = REGIONS.index("chest")
    region[trunk & (y >= chest[1])] = REGIONS.index("back")
    waist = 0.0 if lower else 0.12
    region[rest & (t > waist) & (t <= 0.45)] = REGIONS.index("waist")
    region[rest & (t > -0.25) & (t <= waist)] = REGIONS.index("hips")
    region[rest & (t <= -0.25)] = REGIONS.index("legs")
    return region


# --------------------------------------------------------------------------------------------------
# Fit check and problem colours
# --------------------------------------------------------------------------------------------------

#: Inside the body by more than this (millimetres) counts as inside.
INSIDE_MM = 1.0
#: Closer to the body than this (millimetres) counts as too close.
CLOSE_MM = 3.0
#: A shoulder further off the body than this (millimetres) floats.
FLOATING_MM = 25.0
#: Edges longer than this share of their length before the changes count as stretched.
STRETCH_LIMIT = 1.15


class RegionFit(NamedTuple):
    region: str
    count: int
    p10: float  # millimetres
    p50: float
    p90: float
    inside: int


class FitReport(NamedTuple):
    rows: Tuple[RegionFit, ...]
    vertices: int
    inside: int

    @property
    def inside_share(self) -> float:
        return self.inside / self.vertices if self.vertices else 0.0

    def to_json(self) -> str:
        return json.dumps({"version": 1, "vertices": self.vertices, "inside": self.inside,
                           "rows": [list(row) for row in self.rows]}, separators=(",", ":"))

    @staticmethod
    def from_json(text: str) -> Optional["FitReport"]:
        try:
            data = json.loads(text) if text else None
            if not isinstance(data, dict) or data.get("version") != 1:
                return None
            rows = tuple(RegionFit(str(r[0]), int(r[1]), float(r[2]), float(r[3]), float(r[4]), int(r[5]))
                         for r in data["rows"] if r[0] in REGIONS)
            return FitReport(rows, int(data["vertices"]), int(data["inside"]))
        except (ValueError, TypeError, KeyError, IndexError):
            return None


def fit_report(clearance: Any, regions: Any, minimum: int = 5) -> FitReport:
    """Per region: how far the garment stands off the body (10th, 50th and 90th percentile, in millimetres) and
    how many vertices are inside it. ``clearance`` is signed, in metres (negative inside)."""
    millimetres = np.asarray(clearance, dtype=np.float64) * 1000.0
    regions = np.asarray(regions)
    rows = []
    for index, name in enumerate(REGIONS):
        values = millimetres[regions == index]
        values = values[np.isfinite(values)]
        if values.size < minimum:
            continue
        p10, p50, p90 = np.percentile(values, [10, 50, 90])
        rows.append(RegionFit(name, int(values.size), round(float(p10), 1), round(float(p50), 1),
                              round(float(p90), 1), int((values < -INSIDE_MM).sum())))
    finite = millimetres[np.isfinite(millimetres)]
    return FitReport(tuple(rows), int(finite.size), int((finite < -INSIDE_MM).sum()))


def fit_advice(report: FitReport) -> List[Tuple[str, Dict[str, Any]]]:
    """Advice from the measured values alone: ``(text key, fields)``. Vertices inside the body are not advised on
    here: the report's own summary line and the next-step hint name them."""
    advice: List[Tuple[str, Dict[str, Any]]] = []
    for row in report.rows:
        if row.region == "shoulders" and row.p50 > FLOATING_MM:
            advice.append(("garment.advice.shoulders", {}))
    return advice


#: Problem classes, in order of priority, and the colours of the overlay (linear RGBA).
PROBLEMS = ("none", "inside", "close", "stretched", "floating")
PROBLEM_COLOURS = {
    "none": (0.8, 0.8, 0.8, 1.0),
    "inside": (0.9, 0.05, 0.05, 1.0),
    "close": (0.95, 0.8, 0.05, 1.0),
    "stretched": (0.55, 0.15, 0.8, 1.0),
    "floating": (0.1, 0.35, 0.95, 1.0),
}


def problem_classes(clearance: Any, regions: Any, stretch: Optional[Any] = None, *, close_mm: float = CLOSE_MM,
                    floating_mm: float = FLOATING_MM, stretch_limit: float = STRETCH_LIMIT) -> np.ndarray:
    """Each vertex's problem (an index into :data:`PROBLEMS`): inside the body beats too close, which beats
    stretched, which beats a floating shoulder."""
    millimetres = np.asarray(clearance, dtype=np.float64) * 1000.0
    regions = np.asarray(regions)
    classes = np.zeros(len(millimetres), dtype=np.int64)
    floating = (regions == REGIONS.index("shoulders")) & (millimetres > floating_mm)
    classes[floating] = PROBLEMS.index("floating")
    if stretch is not None:
        classes[np.asarray(stretch) > stretch_limit] = PROBLEMS.index("stretched")
    classes[(millimetres >= -INSIDE_MM) & (millimetres < close_mm)] = PROBLEMS.index("close")
    classes[millimetres < -INSIDE_MM] = PROBLEMS.index("inside")
    return classes


def problem_counts(classes: np.ndarray) -> Dict[str, int]:
    return {name: int((classes == index).sum()) for index, name in enumerate(PROBLEMS) if index}


# --------------------------------------------------------------------------------------------------
# Moving the garment against the body
# --------------------------------------------------------------------------------------------------


def push_out_offsets(positions: Any, nearest: Any, normals: Any, clearance: Any, gap: float) -> np.ndarray:
    """Offsets that move every vertex closer to the body than ``gap`` (metres, also those inside) to ``gap``
    outside it, along the body's surface normal."""
    points = as_points(positions)
    clearance = np.asarray(clearance, dtype=np.float64)
    target = as_points(nearest) + as_points(normals) * gap
    offsets = np.zeros_like(points)
    needs = clearance < gap
    offsets[needs] = target[needs] - points[needs]
    return offsets


def snug_offsets(positions: Any, nearest: Any, normals: Any, clearance: Any, gap: float, amount: float,
                 weights: Any, max_move: float = 0.15) -> np.ndarray:
    """Offsets that bring vertices further off the body than ``gap`` towards it, by ``amount`` (0 to 1) of the
    way and each vertex's weight; no vertex moves more than ``max_move`` metres."""
    points = as_points(positions)
    clearance = np.asarray(clearance, dtype=np.float64)
    weights = np.asarray(weights, dtype=np.float64)
    target = as_points(nearest) + as_points(normals) * gap
    offsets = (target - points) * (np.clip(amount, 0.0, 1.0) * weights)[:, None]
    offsets[clearance <= gap] = 0.0
    length = np.linalg.norm(offsets, axis=1)
    too_far = length > max_move
    offsets[too_far] *= (max_move / length[too_far])[:, None]
    return offsets


def relax_positions(positions: Any, edges: Any, rest_lengths: Any, weights: Any, amount: float,
                    iterations: int = 20) -> np.ndarray:
    """Shortens stretched edges back towards their rest length, moving each vertex by its weight; edges at or
    below their rest length are left alone."""
    points = as_points(positions).copy()
    edges = np.asarray(edges, dtype=np.int64).reshape(-1, 2)
    rest = np.asarray(rest_lengths, dtype=np.float64)
    weights = np.clip(np.asarray(weights, dtype=np.float64), 0.0, 1.0) * float(np.clip(amount, 0.0, 1.0))
    count = len(points)
    for _ in range(max(1, iterations)):
        delta = points[edges[:, 1]] - points[edges[:, 0]]
        length = np.linalg.norm(delta, axis=1)
        excess = np.where((length > rest) & (length > 1e-12), (length - rest) / np.maximum(length, 1e-12), 0.0)
        correction = delta * (0.5 * excess)[:, None]
        moves = np.zeros_like(points)
        hits = np.zeros(count)
        np.add.at(moves, edges[:, 0], correction)
        np.add.at(moves, edges[:, 1], -correction)
        np.add.at(hits, edges[:, 0], excess > 0)
        np.add.at(hits, edges[:, 1], excess > 0)
        hits[hits == 0] = 1.0
        points += moves / hits[:, None] * weights[:, None]
    return points


def rotate_about_y(points: Any, pivot: Any, degrees: float) -> np.ndarray:
    """Points rotated about the axis through ``pivot`` along +Y (front to back). A positive angle lowers a point
    on the ped's left (+X) side."""
    points = as_points(points)
    pivot = _vec(pivot)
    angle = math.radians(degrees)
    c, s = math.cos(angle), math.sin(angle)
    local = points - pivot
    rotated = np.empty_like(local)
    rotated[:, 0] = local[:, 0] * c + local[:, 2] * s
    rotated[:, 1] = local[:, 1]
    rotated[:, 2] = -local[:, 0] * s + local[:, 2] * c
    return rotated + pivot


def arm_angle(markers: Mapping[str, Any], suffix: str) -> Optional[float]:
    """The arm's angle below the horizontal, in degrees (shoulder to wrist, else shoulder to elbow)."""
    shoulder = markers.get(f"shoulder_{suffix}")
    end = markers.get(f"wrist_{suffix}", markers.get(f"elbow_{suffix}"))
    if shoulder is None or end is None:
        return None
    direction = _vec(end) - _vec(shoulder)
    sideways = math.hypot(direction[0], direction[1])
    if sideways < 1e-6 and abs(direction[2]) < 1e-6:
        return None
    return math.degrees(math.atan2(-direction[2], sideways))


def arm_rotations(markers: Mapping[str, Any], target: float) -> Dict[str, float]:
    """The rotation about Y (degrees) that brings each arm to ``target`` degrees below the horizontal."""
    rotations = {}
    for suffix, side in (("l", 1.0), ("r", -1.0)):
        current = arm_angle(markers, suffix)
        if current is not None:
            rotations[suffix] = side * (target - current)
    return rotations


# --------------------------------------------------------------------------------------------------
# Seams: welding and tears
# --------------------------------------------------------------------------------------------------


def _close_pairs(points: np.ndarray, distance: float, indices: np.ndarray) -> List[Tuple[int, int]]:
    """Pairs of ``indices`` whose points are at most ``distance`` apart (a grid of ``distance`` cells)."""
    if distance <= 0 or len(indices) < 2:
        return []
    cells = np.floor(points[indices] / distance).astype(np.int64)
    buckets: Dict[Tuple[int, int, int], List[int]] = {}
    for position, cell in enumerate(map(tuple, cells)):
        buckets.setdefault(cell, []).append(position)  # type: ignore[arg-type]
    offsets = [(a, b, c) for a in (-1, 0, 1) for b in (-1, 0, 1) for c in (-1, 0, 1)]
    limit = distance * distance
    pairs = []
    for position, cell in enumerate(map(tuple, cells)):
        i = int(indices[position])
        p = points[i]
        for da, db, dc in offsets:
            for other in buckets.get((cell[0] + da, cell[1] + db, cell[2] + dc), ()):
                if other <= position:
                    continue
                j = int(indices[other])
                d = points[j] - p
                if float(d @ d) <= limit:
                    pairs.append((i, j))
    return pairs


def weld_targets(positions: Any, distance: float, candidates: Optional[Any] = None,
                 groups: Optional[Any] = None) -> Tuple[np.ndarray, np.ndarray]:
    """Which vertex each vertex merges into (itself when it stays) and where the merged vertices go (the mean of
    their group). Only ``candidates`` (for example the open edges of panels) are welded, and with ``groups`` only
    vertices of the same group."""
    points = as_points(positions)
    count = len(points)
    target = np.arange(count)
    merged = points.copy()
    indices = np.nonzero(np.asarray(candidates, dtype=bool))[0] if candidates is not None else np.arange(count)
    parent = {int(i): int(i) for i in indices}

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    group_of = np.asarray(groups) if groups is not None else None
    for i, j in _close_pairs(points, distance, indices):
        if group_of is not None and group_of[i] != group_of[j]:
            continue
        a, b = find(i), find(j)
        if a != b:
            parent[max(a, b)] = min(a, b)
    members: Dict[int, List[int]] = {}
    for i in parent:
        members.setdefault(find(i), []).append(i)
    for root, group in members.items():
        if len(group) > 1:
            target[group] = root
            merged[group] = points[group].mean(axis=0)
    return target, merged


def lining_pairs(positions: Any, normals: Any, groups: Any, *, weld: float = 0.002, near: float = 0.03,
                 share: float = 0.4, sample: int = 3000) -> List[Tuple[int, int]]:
    """Groups (materials) that lie as a layer over another group: most of a group's vertices have a vertex of
    another group a few millimetres away along the surface normal. A seam between two fabrics only touches along
    its edge, so it is not a lining."""
    points = as_points(positions)
    normals = as_points(normals)
    groups = np.asarray(groups)
    found: List[Tuple[int, int]] = []
    names = [g for g in np.unique(groups) if (groups == g).sum() >= 30]
    if len(names) < 2:
        return found
    cells = np.floor(points / near).astype(np.int64)
    buckets: Dict[Tuple[int, int, int], List[int]] = {}
    for index, cell in enumerate(map(tuple, cells)):
        buckets.setdefault(cell, []).append(index)  # type: ignore[arg-type]
    offsets = [(a, b, c) for a in (-1, 0, 1) for b in (-1, 0, 1) for c in (-1, 0, 1)]
    rng = np.random.default_rng(7)
    for group in names:
        own = np.nonzero(groups == group)[0]
        if len(own) > sample:
            own = rng.choice(own, sample, replace=False)
        layered: Dict[Any, int] = {}
        for i in own:
            cell = cells[i]
            best, best_j = near, -1
            for da, db, dc in offsets:
                for j in buckets.get((cell[0] + da, cell[1] + db, cell[2] + dc), ()):
                    if groups[j] == group:
                        continue
                    d = float(np.linalg.norm(points[j] - points[i]))
                    if d < best:
                        best, best_j = d, j
            if best_j < 0 or best <= weld:
                continue
            offset = (points[best_j] - points[i]) / best
            if abs(float(offset @ normals[i])) > 0.7 and abs(float(normals[i] @ normals[best_j])) > 0.7:
                layered[groups[best_j]] = layered.get(groups[best_j], 0) + 1
        for other, hits in layered.items():
            if hits >= share * len(own):
                pair = (min(int(group), int(other)), max(int(group), int(other)))
                if pair not in found:
                    found.append(pair)
    return found


def seam_pairs(positions: Any, distance: float, candidates: Optional[Any] = None) -> np.ndarray:
    """Pairs of separate vertices that sit on top of each other (the open seams of unwelded panels)."""
    points = as_points(positions)
    indices = np.nonzero(np.asarray(candidates, dtype=bool))[0] if candidates is not None else np.arange(len(points))
    pairs = _close_pairs(points, distance, indices)
    return np.asarray(pairs, dtype=np.int64).reshape(-1, 2)


def tears(pairs: np.ndarray, posed: Any, threshold: float) -> Tuple[np.ndarray, np.ndarray]:
    """Which seam pairs separate by more than ``threshold`` metres in a pose, and every pair's separation."""
    points = as_points(posed)
    pairs = np.asarray(pairs, dtype=np.int64).reshape(-1, 2)
    if not len(pairs):
        return np.zeros(0, dtype=bool), np.zeros(0)
    separation = np.linalg.norm(points[pairs[:, 0]] - points[pairs[:, 1]], axis=1)
    return separation > threshold, separation


# --------------------------------------------------------------------------------------------------
# UV islands and strip cutting
# --------------------------------------------------------------------------------------------------


def uv_islands(loop_vertex: Any, loop_uv: Any, face_start: Any, face_total: Any, precision: float = 1e-5) -> np.ndarray:
    """The UV island of every face: faces that share an edge with the same UVs on both sides belong together."""
    loop_vertex = np.asarray(loop_vertex, dtype=np.int64)
    uv = np.round(np.asarray(loop_uv, dtype=np.float64).reshape(-1, 2) / precision).astype(np.int64)
    face_start = np.asarray(face_start, dtype=np.int64)
    face_total = np.asarray(face_total, dtype=np.int64)
    faces = len(face_start)
    face_of_loop = np.repeat(np.arange(faces), face_total)
    following = np.arange(len(loop_vertex)) + 1
    ends = face_start + face_total
    last = following == np.repeat(ends, face_total)
    following[last] = np.repeat(face_start, face_total)[last]
    a, b = loop_vertex, loop_vertex[following]
    ua, ub = uv, uv[following]
    swap = a > b
    lo = np.where(swap, b, a)
    hi = np.where(swap, a, b)
    ulo = np.where(swap[:, None], ub, ua)
    uhi = np.where(swap[:, None], ua, ub)
    keys = np.column_stack([lo, hi, ulo, uhi])
    order = np.lexsort(keys.T[::-1])
    sorted_keys = keys[order]
    same = np.all(sorted_keys[1:] == sorted_keys[:-1], axis=1)
    parent = np.arange(faces)

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for position in np.nonzero(same)[0]:
        f1, f2 = int(face_of_loop[order[position]]), int(face_of_loop[order[position + 1]])
        r1, r2 = find(f1), find(f2)
        if r1 != r2:
            parent[max(r1, r2)] = min(r1, r2)
    roots = np.array([find(i) for i in range(faces)])
    _, island = np.unique(roots, return_inverse=True)
    return island


def strip_segments(island: Any, face_uv_centre: Any, loop_uv: Any, face_total: Any,
                   aspect: float = 4.0) -> Tuple[np.ndarray, int]:
    """Cuts long thin UV islands (hem bands, waistbands, straps) into roughly square pieces, so the packer does
    not shrink every island to fit their length. Returns each face's piece number (0 for uncut islands) and how
    many islands were cut."""
    island = np.asarray(island, dtype=np.int64)
    centres = np.asarray(face_uv_centre, dtype=np.float64).reshape(-1, 2)
    uv = np.asarray(loop_uv, dtype=np.float64).reshape(-1, 2)
    loop_face = np.repeat(np.arange(len(island)), np.asarray(face_total, dtype=np.int64))
    pieces = np.zeros(len(island), dtype=np.int64)
    cut = 0
    for value in np.unique(island):
        faces = island == value
        points = uv[faces[loop_face]]
        if len(points) < 6:
            continue
        mean = points.mean(axis=0)
        values, vectors = np.linalg.eigh(np.cov((points - mean).T))
        axis, across = vectors[:, 1], vectors[:, 0]
        along = (points - mean) @ axis
        side = (points - mean) @ across
        length = float(along.max() - along.min())
        width = max(float(side.max() - side.min()), 1e-9)
        if length / width <= aspect:
            continue
        count = int(math.ceil(length / (2 * width)))
        step = length / count
        position = ((centres[faces] - mean) @ axis - along.min()) / step
        pieces[faces] = np.clip(position.astype(np.int64), 0, count - 1)
        cut += 1
    return pieces, cut


def uv_area(triangle_uv: Any) -> float:
    """The UV area the triangles cover (overlaps count twice), in units of the 0 to 1 square."""
    tri = np.asarray(triangle_uv, dtype=np.float64).reshape(-1, 3, 2)
    if not len(tri):
        return 0.0
    a, b, c = tri[:, 0], tri[:, 1], tri[:, 2]
    cross = (b[:, 0] - a[:, 0]) * (c[:, 1] - a[:, 1]) - (c[:, 0] - a[:, 0]) * (b[:, 1] - a[:, 1])
    return float(np.abs(cross).sum() / 2)


def game_vertex_count(loop_vertex: Any, loop_uv: Optional[Any] = None, loop_material: Optional[Any] = None) -> int:
    """How many vertices the game draws for a smooth shaded mesh: one per vertex, UV and material."""
    columns = [np.asarray(loop_vertex, dtype=np.int64)]
    if loop_uv is not None:
        uv = np.round(np.asarray(loop_uv, dtype=np.float64).reshape(-1, 2) * 65536).astype(np.int64)
        columns += [uv[:, 0], uv[:, 1]]
    if loop_material is not None:
        columns.append(np.asarray(loop_material, dtype=np.int64))
    if not len(columns[0]):
        return 0
    return int(len(np.unique(np.column_stack(columns), axis=0)))


# --------------------------------------------------------------------------------------------------
# Local checks
# --------------------------------------------------------------------------------------------------

#: Game vertices per level of detail above which the add-on advises reducing the model. This is rounded guidance
#: for performance, not a format limit: Sollumz splits larger geometries.
GAME_VERTEX_BUDGET = {"high": 30000, "medium": 10000, "low": 4000}
#: The game skins each vertex with at most this many bones.
MAX_INFLUENCES = 4
#: More of the garment inside the body than this share is worth fixing before the game shows it.
INSIDE_SHARE_LIMIT = 0.02


class Finding(NamedTuple):
    severity: str  # "error", "warning" or "info"
    code: str
    fields: Dict[str, Any]


def validate(stats: Mapping[str, Any]) -> List[Finding]:
    """The local checks of a prepared garment. ``stats`` holds what Blender measured (see the keys below);
    keys that are missing are not checked."""
    findings: List[Finding] = []

    def add(severity: str, code: str, **fields: Any) -> None:
        findings.append(Finding(severity, code, fields))

    if stats.get("non_finite"):
        add("error", "non-finite", count=int(stats["non_finite"]))
    if stats.get("uv_layers") == 0:
        add("error", "no-uv")
    else:
        if stats.get("uv_outside", 0) > 0:
            add("warning", "uv-outside", count=int(stats["uv_outside"]))
        area = stats.get("uv_area")
        if area is not None and area < 0.05:
            add("warning", "uv-area", area=round(100.0 * float(area), 1))
    if stats.get("weighted") is False:
        add("info", "no-weights")
    else:
        if stats.get("unweighted", 0) > 0:
            add("error", "unweighted", count=int(stats["unweighted"]))
        if stats.get("over_four", 0) > 0:
            add("warning", "influences", count=int(stats["over_four"]), limit=MAX_INFLUENCES)
    colour = stats.get("colour1")
    if colour == "missing":
        add("warning", "colour-missing")
    elif colour == "format":
        add("warning", "colour-format")
    for level, budget in GAME_VERTEX_BUDGET.items():
        count = stats.get(f"game_vertices_{level}")
        if count is not None and count > budget:
            add("warning", "vertices", level=level, count=int(count), budget=budget)
    share = stats.get("inside_share")
    if share is not None and share > INSIDE_SHARE_LIMIT:
        add("warning", "inside", share=round(100.0 * float(share), 1))
    if stats.get("materials", 1) > 1:
        add("info", "materials", count=int(stats["materials"]))
    return findings


def is_clean(findings: Iterable[Finding]) -> bool:
    return not any(f.severity in ("error", "warning") for f in findings)


def findings_to_json(findings: Iterable[Finding]) -> str:
    return json.dumps([[f.severity, f.code, f.fields] for f in findings], separators=(",", ":"))


def findings_from_json(text: str) -> Optional[List[Finding]]:
    try:
        data = json.loads(text) if text else None
        if not isinstance(data, list):
            return None
        return [Finding(str(s), str(c), dict(f)) for s, c, f in data]
    except (ValueError, TypeError):
        return None


def influence_counts(weights_per_vertex: Sequence[Sequence[float]]) -> Tuple[int, int]:
    """``(unweighted, over four)``: vertices without any weight, and vertices with more than four."""
    unweighted = over = 0
    for weights in weights_per_vertex:
        used = sum(1 for w in weights if w > 1e-6)
        if used == 0:
            unweighted += 1
        elif used > MAX_INFLUENCES:
            over += 1
    return unweighted, over


# --------------------------------------------------------------------------------------------------
# Pose presets
# --------------------------------------------------------------------------------------------------

PRESET_VERSION = 1
_PRESET_NAME = re.compile(r"[^A-Za-z0-9 _-]+")


def preset_file_name(name: str) -> str:
    """A file name for a preset: letters, digits, spaces, '_' and '-' only, at most 64 characters."""
    cleaned = _PRESET_NAME.sub("", name).strip()[:64].strip()
    if not cleaned:
        raise ValueError("empty preset name")
    return cleaned + ".json"


def preset_json(markers: Mapping[str, Any], category: str, source_pose: str) -> str:
    data = {
        "version": PRESET_VERSION,
        "category": category,
        "sourcePose": source_pose,
        "markers": {name: [round(float(v), 5) for v in _vec(markers[name])] for name in MARKERS if name in markers},
    }
    return json.dumps(data, indent=1, sort_keys=True)


def parse_preset(text: str) -> Tuple[Dict[str, Vector], Optional[str], Optional[str]]:
    """``(markers, category, source pose)`` from a preset file; raises ``ValueError`` for anything else."""
    data = json.loads(text)
    if not isinstance(data, dict) or data.get("version") != PRESET_VERSION:
        raise ValueError("not a pose preset")
    raw = data.get("markers")
    if not isinstance(raw, dict) or not raw:
        raise ValueError("a pose preset needs markers")
    markers: Dict[str, Vector] = {}
    for name, value in raw.items():
        if name not in MARKERS:
            raise ValueError(f"unknown marker {name!r}")
        if not isinstance(value, list) or len(value) != 3:
            raise ValueError(f"marker {name!r} needs three numbers")
        try:
            numbers = [float(v) for v in value]
        except (TypeError, ValueError):
            raise ValueError(f"marker {name!r} needs three numbers") from None
        if not all(math.isfinite(v) and abs(v) <= 10.0 for v in numbers):
            raise ValueError(f"marker {name!r} is out of range")
        markers[name] = (numbers[0], numbers[1], numbers[2])
    category = data.get("category") if data.get("category") in CATEGORIES else None
    pose = data.get("sourcePose") if data.get("sourcePose") in SOURCE_POSES else None
    return markers, category, pose


# --------------------------------------------------------------------------------------------------
# Units
# --------------------------------------------------------------------------------------------------


#: The largest dimension, in metres, a garment of each kind has (with the arms of an A-pose or a T-pose). Each range
#: spans less than a factor of 10, the step from centimetres to millimetres, so at most one unit fits.
SIZE_RANGES = {"shoes": (0.08, 0.5), "pants": (0.25, 1.6), "shorts": (0.25, 1.6), "long_jacket": (0.4, 2.2)}
TOP_SIZE_RANGE = (0.3, 1.8)


def import_scale(size: float, category: str = "tshirt") -> float:
    """The factor that brings an imported garment whose largest dimension is ``size`` (Blender units) to metres:
    Marvelous Designer files are often in centimetres or millimetres. The unit whose size fits the category wins;
    a size that fits none is kept as it is."""
    low, high = SIZE_RANGES.get(category, TOP_SIZE_RANGE)
    for factor in (1.0, 0.01, 0.001):
        if low <= size * factor <= high:
            return factor
    return 1.0
