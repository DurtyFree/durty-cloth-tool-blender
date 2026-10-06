# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2026 Schmid Software Solutions (https://schmid-software.de)
"""Custom Ped without Blender: turning your own character into a custom ped.

The markers (their names, the click guide and the joints placed from it, Auto Markers, markers from an existing rig by
public bone-name conventions, mirroring, the elbow or knee that moves with its limb, the plausibility checks), the
character checks (units, upright, facing, size budget, part roles), the mesh a rig request carries with its topology
hash, the rig result turned into an armature plan, vertex groups and poses, the test poses, the local checks of the
rigged character, the model name rules and the next-step hint.

Positions are in ped space, in metres: Z up, the character facing -Y and its left side at +X (Blender's front view
looks at its face). Everything here is geometry: no data from the game and no calibration taken from game bodies.
Nothing here imports Blender; numpy does the arithmetic, so the tests run without Blender.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from typing import Any, Dict, Iterable, List, Mapping, NamedTuple, Optional, Sequence, Tuple

import numpy as np

from .dct_link import protocol

# --------------------------------------------------------------------------------------------------
# Markers
# --------------------------------------------------------------------------------------------------

#: The 19 body markers a rig needs, in the protocol's order.
BODY_MARKERS: Tuple[str, ...] = protocol.PED_BODY_MARKERS
CENTRE_MARKERS = ("headTop", "chin", "neck", "chest", "pelvis")
JOINTS = ("shoulder", "elbow", "wrist", "hip", "knee", "ankle", "toe")
LEFT = tuple(f"{joint}L" for joint in JOINTS)
RIGHT = tuple(f"{joint}R" for joint in JOINTS)
#: Each sided marker and its mirror.
MIRROR: Dict[str, str] = {**dict(zip(LEFT, RIGHT)), **dict(zip(RIGHT, LEFT))}
#: The points the click guide asks for, in order; the other markers are placed from them.
GUIDE = ("headTop", "chin", "shoulderL", "shoulderR", "wristL", "wristR", "hipL", "hipR", "ankleL", "ankleR",
         "toeL", "toeR")
DERIVED = ("neck", "chest", "pelvis", "elbowL", "elbowR", "kneeL", "kneeR")
#: Where a click lands between the surface the ray enters and the one it leaves: 0 on the surface (the top of the
#: head and the chin are surface points), 0.5 in the middle of the limb, toes towards their front.
GUIDE_DEPTH = {"headTop": 0.0, "chin": 0.0, "toeL": 0.3, "toeR": 0.3}
#: A middle joint and the two ends of its limb: moving an end moves the middle joint with the limb.
LIMBS: Dict[str, Tuple[str, str]] = {"elbowL": ("shoulderL", "wristL"), "elbowR": ("shoulderR", "wristR"),
                                     "kneeL": ("hipL", "ankleL"), "kneeR": ("hipR", "ankleR")}
#: The lines the 3D view draws between markers.
STICK = (("headTop", "chin"), ("chin", "neck"), ("neck", "chest"), ("chest", "pelvis"),
         ("neck", "shoulderL"), ("shoulderL", "elbowL"), ("elbowL", "wristL"),
         ("neck", "shoulderR"), ("shoulderR", "elbowR"), ("elbowR", "wristR"),
         ("pelvis", "hipL"), ("hipL", "kneeL"), ("kneeL", "ankleL"), ("ankleL", "toeL"),
         ("pelvis", "hipR"), ("hipR", "kneeR"), ("kneeR", "ankleR"), ("ankleR", "toeR"))
#: Where each marker sits on the guide's figure, seen from the front (the character's left on the right), in units of
#: the figure's height with the feet at 0.
FIGURE: Dict[str, Tuple[float, float]] = {
    "headTop": (0.0, 1.0), "chin": (0.0, 0.875), "neck": (0.0, 0.84), "chest": (0.0, 0.72), "pelvis": (0.0, 0.54),
    "shoulderL": (0.11, 0.81), "elbowL": (0.2, 0.66), "wristL": (0.29, 0.52),
    "hipL": (0.055, 0.51), "kneeL": (0.065, 0.28), "ankleL": (0.07, 0.045), "toeL": (0.1, 0.012),
}
FIGURE.update({MIRROR[name]: (-x, y) for name, (x, y) in list(FIGURE.items()) if name in MIRROR})
#: The figure's lines, as :data:`STICK`, plus the outline of the head.
FIGURE_LINES = STICK


def side(name: str) -> str:
    """``L``, ``R`` or ``""`` for a centre marker."""
    return name[-1] if name in MIRROR else ""


class MarkerError(ValueError):
    """Markers could not be placed; ``code`` names why (a text key ``ped.marker-error.<code>``)."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def _vec(value: Any) -> np.ndarray:
    return np.asarray(value, dtype=np.float64).reshape(3)


def _unit(vector: np.ndarray, fallback: Sequence[float] = (0.0, 0.0, 1.0)) -> np.ndarray:
    length = float(np.linalg.norm(vector))
    return vector / length if length > 1e-12 else np.asarray(fallback, dtype=np.float64)


def as_points(positions: Any) -> np.ndarray:
    return np.asarray(positions, dtype=np.float64).reshape(-1, 3)


def tuples(markers: Mapping[str, Any]) -> Dict[str, Tuple[float, float, float]]:
    """Markers as plain float tuples (for JSON and the protocol), in the protocol's order."""
    order = {name: index for index, name in enumerate(protocol.PED_MARKERS)}
    return {name: tuple(float(c) for c in _vec(markers[name]))
            for name in sorted(markers, key=lambda n: order.get(n, len(order)))}


def markers_json(markers: Mapping[str, Any]) -> str:
    return json.dumps({name: [round(c, 6) for c in point] for name, point in tuples(markers).items()},
                      sort_keys=True)


def markers_from_json(text: str) -> Dict[str, Tuple[float, float, float]]:
    try:
        data = json.loads(text) if text else {}
    except ValueError:
        return {}
    found = {}
    if isinstance(data, dict):
        for name, point in data.items():
            if name in protocol.PED_MARKERS and isinstance(point, list) and len(point) == 3:
                try:
                    found[name] = tuple(float(c) for c in point)
                except (TypeError, ValueError):
                    continue
    return found


def centre_x(markers: Mapping[str, Any]) -> float:
    """The x of the character's middle: the centre markers, or the middle between left and right pairs."""
    values = [_vec(markers[name])[0] for name in CENTRE_MARKERS if name in markers]
    if values:
        return float(np.mean(values))
    pairs = [(_vec(markers[a])[0] + _vec(markers[b])[0]) / 2 for a, b in zip(LEFT, RIGHT) if a in markers and b in markers]
    return float(np.mean(pairs)) if pairs else 0.0


def mirror_markers(markers: Mapping[str, Any], source: str = "L") -> Dict[str, Tuple[float, float, float]]:
    """The markers of the ``source`` side (``L`` or ``R``) mirrored onto the other side across the character's middle;
    centre markers move onto the middle."""
    if source not in ("L", "R"):
        raise ValueError("source is L or R")
    cx = centre_x(markers)
    result = {name: tuple(_vec(point)) for name, point in markers.items()}
    for name, point in markers.items():
        if side(name) == source:
            p = _vec(point)
            result[MIRROR[name]] = (2 * cx - p[0], p[1], p[2])
    for name in CENTRE_MARKERS:
        if name in result:
            result[name] = (cx, result[name][1], result[name][2])
    return result


def follow_middle(start: Any, old_end: Any, new_end: Any, middle: Any) -> Tuple[float, float, float]:
    """Where the middle joint of a limb goes when one end moves from ``old_end`` to ``new_end`` and the other end
    (``start``) stays: it keeps its place along the limb and its offset from it, turned and stretched with the limb."""
    s, a, b, m = _vec(start), _vec(old_end), _vec(new_end), _vec(middle)
    before, after = a - s, b - s
    lb, la = float(np.linalg.norm(before)), float(np.linalg.norm(after))
    if lb < 1e-6 or la < 1e-6:
        return tuple(m)
    u, v = before / lb, after / la
    axis = np.cross(u, v)
    sin, cos = float(np.linalg.norm(axis)), float(np.dot(u, v))
    if sin < 1e-9:
        turn = np.eye(3) if cos > 0 else _rotation(_unit(np.cross(u, [1.0, 0, 0]) if abs(u[0]) < 0.9
                                                         else np.cross(u, [0, 1.0, 0])), math.pi)
    else:
        turn = _rotation(axis / sin, math.atan2(sin, cos))
    return tuple(s + (la / lb) * (turn @ (m - s)))


def _rotation(axis: Sequence[float], angle: float) -> np.ndarray:
    """The rotation matrix about a unit ``axis`` by ``angle`` radians (right-handed)."""
    x, y, z = _unit(np.asarray(axis, dtype=np.float64))
    c, s = math.cos(angle), math.sin(angle)
    t = 1 - c
    return np.array([[t * x * x + c, t * x * y - s * z, t * x * z + s * y],
                     [t * x * y + s * z, t * y * y + c, t * y * z - s * x],
                     [t * x * z - s * y, t * y * z + s * x, t * z * z + c]])


def moved_middles(before: Mapping[str, Any], after: Mapping[str, Any], *, tolerance: float = 1e-5
                  ) -> Dict[str, Tuple[float, float, float]]:
    """The elbows and knees to move after markers moved from ``before`` to ``after``: for each limb whose one end moved
    while its middle joint and its other end did not, the middle joint's new place (:func:`follow_middle`)."""
    def moved(name: str) -> bool:
        return name in before and name in after and float(np.linalg.norm(_vec(before[name]) - _vec(after[name]))) > tolerance

    result = {}
    for middle, (first, second) in LIMBS.items():
        if middle not in after or moved(middle):
            continue
        if moved(first) and not moved(second) and second in after:
            result[middle] = follow_middle(after[second], before[first], after[first], after[middle])
        elif moved(second) and not moved(first) and first in after:
            result[middle] = follow_middle(after[first], before[second], after[second], after[middle])
    return result


def guide_point(hits: Sequence[float], origin: Any, direction: Any, name: str) -> Optional[Tuple[float, float, float]]:
    """Where a click of the click guide lands. ``hits`` are the distances along the ray at which it crosses the
    character's surface, sorted; the point lies between the first entry and the next exit (``GUIDE_DEPTH``), so
    it is inside the body even where the mesh is open or another part is in front. ``None`` when the ray missed."""
    if not hits:
        return None
    o, d = _vec(origin), _unit(_vec(direction))
    entry = float(hits[0])
    exit_ = float(hits[1]) if len(hits) > 1 else entry
    depth = GUIDE_DEPTH.get(name, 0.5)
    return tuple(o + d * (entry + (exit_ - entry) * depth))


def derive_markers(clicked: Mapping[str, Any], positions: Optional[Any] = None,
                   triangles: Optional[Any] = None) -> Dict[str, Tuple[float, float, float]]:
    """The 19 body markers from the 12 points of the click guide: the neck, chest and pelvis on the line of the body,
    the elbows and knees in the middle of their limbs. With the character's mesh, the derived joints move to the middle
    of the body's or the limb's cross-section. Raises :class:`MarkerError` (``guide-incomplete``) when a point is
    missing."""
    if any(name not in clicked for name in GUIDE):
        raise MarkerError("guide-incomplete")
    m = {name: _vec(clicked[name]) for name in GUIDE}
    shoulders = (m["shoulderL"] + m["shoulderR"]) / 2
    hips = (m["hipL"] + m["hipR"]) / 2
    up = _unit(shoulders - hips)
    width = float(np.linalg.norm(m["hipL"] - m["hipR"]))
    pelvis = hips + up * (0.25 * width)
    neck = shoulders + (m["chin"] - shoulders) * 0.35
    chest = shoulders + (pelvis - shoulders) * 0.28
    result = {name: m[name] for name in GUIDE}
    result.update(neck=neck, chest=chest, pelvis=pelvis)
    for middle, (first, second) in LIMBS.items():
        result[middle] = m[first] + (m[second] - m[first]) * 0.52
    if positions is not None and triangles is not None:
        points, tris = as_points(positions), np.asarray(triangles, dtype=np.int64).reshape(-1, 3)
        height = float(np.ptp(points[:, 2])) if len(points) else 1.0
        for name in ("neck", "chest", "pelvis"):
            centre = section_centre(points, tris, result[name], up, 0.25 * height, outer=True)
            if centre is not None:
                result[name] = centre
        for middle, (first, second) in LIMBS.items():
            axis = _unit(result[second] - result[first])
            reach = 0.35 * float(np.linalg.norm(result[second] - result[first]))
            centre = section_centre(points, tris, result[middle], axis, reach)
            if centre is not None:
                result[middle] = centre
    return {name: tuple(float(c) for c in result[name]) for name in BODY_MARKERS}


# --------------------------------------------------------------------------------------------------
# Cross-sections
# --------------------------------------------------------------------------------------------------


def section(points: np.ndarray, triangles: np.ndarray, origin: Any, normal: Any) -> np.ndarray:
    """The segments where the mesh crosses the plane through ``origin`` with ``normal``: an array ``(S, 2, 3)``."""
    n = _unit(_vec(normal))
    d = (points - _vec(origin)) @ n
    above = d >= 0
    t = np.asarray(triangles, dtype=np.int64)
    if not len(t):
        return np.zeros((0, 2, 3))
    s = above[t]
    crossing = s.any(axis=1) & ~s.all(axis=1)
    t = t[crossing]
    if not len(t):
        return np.zeros((0, 2, 3))
    ends = []
    for a, b in ((0, 1), (1, 2), (2, 0)):
        ia, ib = t[:, a], t[:, b]
        cut = above[ia] != above[ib]
        da, db = d[ia], d[ib]
        f = np.divide(da, da - db, out=np.zeros_like(da), where=cut)
        point = points[ia] + (points[ib] - points[ia]) * f[:, None]
        ends.append((cut, point))
    first = np.where(ends[0][0][:, None], ends[0][1], ends[1][1])
    second = np.where(ends[2][0][:, None], ends[2][1], ends[1][1])
    return np.stack([first, second], axis=1)


class Outline(NamedTuple):
    """One piece of a horizontal cross-section: its extent in x and the middle of its outline."""

    lo: float
    hi: float
    centre: np.ndarray
    front: np.ndarray  # its point furthest towards -Y

    @property
    def width(self) -> float:
        return self.hi - self.lo


def outlines(segments: np.ndarray, tolerance: float = 1e-5) -> List[Outline]:
    """The pieces of a cross-section by their extent in x (pieces whose extents overlap count as one), left to
    right."""
    if not len(segments):
        return []
    lo = segments[:, :, 0].min(axis=1)
    hi = segments[:, :, 0].max(axis=1)
    order = np.argsort(lo)
    groups: List[List[int]] = []
    current_hi = -math.inf
    for index in order:
        if not groups or lo[index] > current_hi + tolerance:
            groups.append([index])
            current_hi = hi[index]
        else:
            groups[-1].append(index)
            current_hi = max(current_hi, hi[index])
    result = []
    for group in groups:
        pieces = segments[group]
        lengths = np.linalg.norm(pieces[:, 1] - pieces[:, 0], axis=1)
        mids = pieces.mean(axis=1)
        total = float(lengths.sum())
        centre = (mids * lengths[:, None]).sum(axis=0) / total if total > 1e-12 else mids.mean(axis=0)
        flat = pieces.reshape(-1, 3)
        result.append(Outline(float(lo[group].min()), float(hi[group].max()), centre, flat[int(np.argmin(flat[:, 1]))]))
    return result


def loops(segments: np.ndarray) -> np.ndarray:
    """Which closed outline each segment of a cross-section belongs to (segments that share an end are one)."""
    count = len(segments)
    if not count:
        return np.zeros(0, dtype=np.int64)
    keys = np.round(segments.reshape(-1, 3) * 1e6).astype(np.int64)
    _, ends = np.unique(keys, axis=0, return_inverse=True)
    ends = ends.reshape(-1, 2)
    parent = list(range(int(ends.max()) + 1))

    def root(item: int) -> int:
        while parent[item] != item:
            parent[item] = parent[parent[item]]
            item = parent[item]
        return item

    for a, b in ends.tolist():
        ra, rb = root(a), root(b)
        if ra != rb:
            parent[ra] = rb
    return np.array([root(a) for a in ends[:, 0].tolist()], dtype=np.int64)


def _inside(segments: np.ndarray, point: np.ndarray, u: np.ndarray, v: np.ndarray) -> bool:
    """Whether ``point`` lies inside the closed outline ``segments`` (in the plane of ``u`` and ``v``): a ray along
    ``u`` crosses it an odd number of times."""
    a = (segments[:, 0] - point) @ np.stack([u, v], axis=1)
    b = (segments[:, 1] - point) @ np.stack([u, v], axis=1)
    straddles = (a[:, 1] > 0) != (b[:, 1] > 0)
    with np.errstate(divide="ignore", invalid="ignore"):
        cross = a[:, 0] + (b[:, 0] - a[:, 0]) * (-a[:, 1]) / (b[:, 1] - a[:, 1])
    return int(np.count_nonzero(straddles & (cross > 0))) % 2 == 1


def section_centre(points: np.ndarray, triangles: np.ndarray, near: Any, normal: Any, reach: float, *,
                   outer: bool = False) -> Optional[np.ndarray]:
    """The middle of the closed outline around ``near`` in the cross-section through it with ``normal``: the outline
    that holds ``near`` (the largest with ``outer``, the body; else the smallest, a limb), or else the outline nearest
    to it within ``reach``; ``None`` when nothing is there. Another limb cut by the same plane has an outline of its
    own and never counts."""
    segments = section(points, triangles, near, normal)
    if not len(segments):
        return None
    point = _vec(near)
    n = _unit(_vec(normal))
    u = _unit(np.cross(n, [1.0, 0.0, 0.0]) if abs(n[0]) < 0.9 else np.cross(n, [0.0, 1.0, 0.0]))
    v = np.cross(n, u)
    mids = segments.mean(axis=1)
    labels = loops(segments)
    holding = []
    for label in np.unique(labels):
        mine = labels == label
        if _inside(segments[mine], point, u, v):
            size = float(np.linalg.norm(segments[mine][:, 1] - segments[mine][:, 0], axis=1).sum())
            holding.append((size, label))
    if holding:
        chosen = max(holding)[1] if outer else min(holding)[1]
    else:
        distances = np.linalg.norm(mids - point, axis=1)
        nearest = int(np.argmin(distances))
        if distances[nearest] > reach:
            return None
        chosen = labels[nearest]
    own = labels == chosen
    pieces, mids = segments[own], mids[own]
    lengths = np.linalg.norm(pieces[:, 1] - pieces[:, 0], axis=1)
    total = float(lengths.sum())
    return (mids * lengths[:, None]).sum(axis=0) / total if total > 1e-12 else mids.mean(axis=0)


def _containing(pieces: List[Outline], x: float) -> Optional[Outline]:
    inside = [piece for piece in pieces if piece.lo - 1e-6 <= x <= piece.hi + 1e-6]
    if inside:
        return max(inside, key=lambda piece: piece.width)
    return min(pieces, key=lambda piece: min(abs(piece.lo - x), abs(piece.hi - x))) if pieces else None


# --------------------------------------------------------------------------------------------------
# Auto Markers
# --------------------------------------------------------------------------------------------------

#: What Auto Markers had to guess rather than find (text keys ``ped.marker-note.<note>``).
MARKER_NOTES = ("arms", "legs", "neck")


class MarkerResult(NamedTuple):
    markers: Dict[str, Tuple[float, float, float]]
    notes: Tuple[str, ...]


def auto_markers(positions: Any, triangles: Any) -> MarkerResult:
    """Places the 19 body markers from the character's shape alone: a person standing upright in ped space, in an
    A-pose, a T-pose or with the arms hanging. Cross-sections find the neck (the narrowest part under the head), the
    legs (two pieces below the crotch) and the middle of the torso; the arms are found by their farthest point from
    the shoulder. Proportions between these come from the usual human figure, never from game bodies. The result is
    a starting point for the user to check. Raises :class:`MarkerError` (``too-small``) for a mesh that is not a
    standing figure."""
    points = as_points(positions)
    tris = np.asarray(triangles, dtype=np.int64).reshape(-1, 3)
    if len(points) < 8 or not len(tris):
        raise MarkerError("too-small")
    z0, top = float(points[:, 2].min()), float(points[:, 2].max())
    height = top - z0
    if height < 0.2:
        raise MarkerError("too-small")
    notes: List[str] = []

    def at(fraction: float) -> float:
        return z0 + fraction * height

    def pieces(z: float) -> List[Outline]:
        return outlines(section(points, tris, (0.0, 0.0, z), (0.0, 0.0, 1.0)))

    torso = points[(points[:, 2] > at(0.55)) & (points[:, 2] < at(0.75))]
    cx = float(np.median(torso[:, 0])) if len(torso) else float(np.median(points[:, 0]))

    # The legs: below the crotch no piece of the cross-section spans the middle.
    crotch = None
    for fraction in np.arange(0.12, 0.62, 0.01):
        middle = [p for p in pieces(at(fraction)) if p.lo <= cx <= p.hi]
        if middle and fraction > 0.2:
            crotch = at(fraction)
            break
    if crotch is None:
        crotch = at(0.47)
        notes.append("legs")
    leg = crotch - z0

    def leg_centre(z: float, sign: float) -> np.ndarray:
        side_pieces = [p for p in pieces(z) if (p.centre[0] - cx) * sign > 0 and not p.lo <= cx <= p.hi]
        if not side_pieces:
            return np.array([cx + sign * 0.06 * height, float(np.median(points[:, 1])), z])
        piece = min(side_pieces, key=lambda p: abs(p.centre[0] - cx))  # the innermost: a hand may hang beside it
        return np.array([piece.centre[0], piece.centre[1], z])

    markers: Dict[str, np.ndarray] = {}
    for sign, suffix in ((1.0, "L"), (-1.0, "R")):
        thigh = leg_centre(crotch - 0.06 * leg, sign)
        markers[f"hip{suffix}"] = np.array([thigh[0], thigh[1], crotch + 0.085 * leg])
        knee = leg_centre(z0 + 0.6 * leg, sign)
        markers[f"knee{suffix}"] = knee
        shin = leg_centre(z0 + 0.16 * leg, sign)
        markers[f"ankle{suffix}"] = np.array([shin[0], shin[1], z0 + 0.095 * leg])
        sole = points[(points[:, 2] < at(0.035)) & ((points[:, 0] - cx) * sign > 0)]
        if len(sole):
            front, back = float(sole[:, 1].min()), float(sole[:, 1].max())
            markers[f"toe{suffix}"] = np.array([float(np.median(sole[:, 0])), back + 0.73 * (front - back),
                                                z0 + 0.015 * height])
        else:
            markers[f"toe{suffix}"] = markers[f"ankle{suffix}"] + np.array([0.0, -0.1 * height, -0.03 * height])

    # The neck: the middle of the narrowest stretch of the piece through the middle, between the shoulders and the
    # top of the head.
    widths = []
    for fraction in np.arange(0.72, 0.96, 0.005):
        piece = _containing(pieces(at(fraction)), cx)
        if piece is not None:
            widths.append((at(fraction), piece.width))
    if not widths:
        raise MarkerError("too-small")
    narrowest = min(range(len(widths)), key=lambda i: widths[i][1])
    limit = widths[narrowest][1] * 1.1
    first = last = narrowest
    while first > 0 and widths[first - 1][1] <= limit:
        first -= 1
    while last < len(widths) - 1 and widths[last + 1][1] <= limit:
        last += 1
    neck_z = (widths[first][0] + widths[last][0]) / 2
    if not at(0.75) < neck_z < at(0.94):
        notes.append("neck")
    span = top - neck_z
    crown = points[points[:, 2] > top - 0.01 * height]
    markers["headTop"] = np.array([float(crown[:, 0].mean()), float(crown[:, 1].mean()), top])
    chin_piece = _containing(pieces(neck_z + 0.15 * span), cx)
    chin = chin_piece.front if chin_piece is not None else np.array([cx, 0.0, neck_z + 0.15 * span])
    markers["chin"] = np.array([chin[0], chin[1], neck_z + 0.15 * span])
    neck_z_marker = neck_z - 0.15 * span
    pelvis_z = markers["hipL"][2] * 0.5 + markers["hipR"][2] * 0.5 + 0.02 * height
    chest_z = pelvis_z + 0.6 * (neck_z_marker - pelvis_z)
    for name, z in (("neck", neck_z_marker), ("chest", chest_z), ("pelvis", pelvis_z)):
        piece = _containing(pieces(z), cx)
        markers[name] = np.array([piece.centre[0], piece.centre[1], z]) if piece is not None else np.array([cx, 0.0, z])

    # The arms: the shoulder a little inside the chest's side, the hand at the point farthest from it.
    shoulder_z = neck_z - 0.3 * span
    chest_piece = _containing(pieces(chest_z), cx)
    half = chest_piece.width / 2 if chest_piece is not None else 0.1 * height
    reach = min(max(half, 0.07 * height), 0.13 * height)
    if chest_piece is None or half > 0.13 * height:
        notes.append("arms")
    depth = markers["chest"][1]
    for sign, suffix in ((1.0, "L"), (-1.0, "R")):
        shoulder = np.array([cx + sign * reach, depth, shoulder_z])
        lateral = (points[:, 0] - cx) * sign
        candidates = points[(lateral > reach + 0.02 * height) & (points[:, 2] > at(0.36))]
        if len(candidates):
            tip = candidates[int(np.argmax(np.linalg.norm(candidates - shoulder, axis=1)))]
        else:
            tip = shoulder + np.array([sign * 0.3 * height, 0.0, -0.3 * height])
            if "arms" not in notes:
                notes.append("arms")
        arm = tip - shoulder
        markers[f"shoulder{suffix}"] = shoulder
        for name, share in ((f"elbow{suffix}", 0.42), (f"wrist{suffix}", 0.76)):
            guess = shoulder + arm * share
            centre = section_centre(points, tris, guess, arm, 0.08 * height)
            markers[name] = centre if centre is not None else guess
    for middle, (first, second) in LIMBS.items():
        if middle.startswith("knee"):
            axis = markers[second] - markers[first]
            centre = section_centre(points, tris, markers[middle], axis, 0.08 * height)
            if centre is not None:
                markers[middle] = centre
    return MarkerResult({name: tuple(float(c) for c in markers[name]) for name in BODY_MARKERS},
                        tuple(dict.fromkeys(notes)))


# --------------------------------------------------------------------------------------------------
# Markers from an existing rig
# --------------------------------------------------------------------------------------------------

#: Public naming conventions of common character rigs: marker to bone, whose head is the joint. ``headTop`` names a
#: bone whose head is the top of the head; without one it is the top of the mesh above the head. The chin is never a
#: bone: it is found on the face below the head joint.
RIG_TABLES: Dict[str, Dict[str, Tuple[str, ...]]] = {
    "mixamo": {
        "headTop": ("HeadTop_End",), "head": ("Head",), "neck": ("Neck",), "chest": ("Spine2",), "pelvis": ("Hips",),
        "shoulderL": ("LeftArm",), "elbowL": ("LeftForeArm",), "wristL": ("LeftHand",), "hipL": ("LeftUpLeg",),
        "kneeL": ("LeftLeg",), "ankleL": ("LeftFoot",), "toeL": ("LeftToeBase",),
        "shoulderR": ("RightArm",), "elbowR": ("RightForeArm",), "wristR": ("RightHand",), "hipR": ("RightUpLeg",),
        "kneeR": ("RightLeg",), "ankleR": ("RightFoot",), "toeR": ("RightToeBase",),
    },
    "unreal": {
        "head": ("head",), "neck": ("neck_01",), "chest": ("spine_05", "spine_03"), "pelvis": ("pelvis",),
        "shoulderL": ("upperarm_l",), "elbowL": ("lowerarm_l",), "wristL": ("hand_l",), "hipL": ("thigh_l",),
        "kneeL": ("calf_l",), "ankleL": ("foot_l",), "toeL": ("ball_l",),
        "shoulderR": ("upperarm_r",), "elbowR": ("lowerarm_r",), "wristR": ("hand_r",), "hipR": ("thigh_r",),
        "kneeR": ("calf_r",), "ankleR": ("foot_r",), "toeR": ("ball_r",),
    },
    "rigify": {
        "head": ("DEF-spine.006", "spine.006"), "neck": ("DEF-spine.004", "spine.004"),
        "chest": ("DEF-spine.003", "spine.003"), "pelvis": ("DEF-spine", "spine"),
        "shoulderL": ("DEF-upper_arm.L", "upper_arm.L"), "elbowL": ("DEF-forearm.L", "forearm.L"),
        "wristL": ("DEF-hand.L", "hand.L"), "hipL": ("DEF-thigh.L", "thigh.L"), "kneeL": ("DEF-shin.L", "shin.L"),
        "ankleL": ("DEF-foot.L", "foot.L"), "toeL": ("DEF-toe.L", "toe.L"),
        "shoulderR": ("DEF-upper_arm.R", "upper_arm.R"), "elbowR": ("DEF-forearm.R", "forearm.R"),
        "wristR": ("DEF-hand.R", "hand.R"), "hipR": ("DEF-thigh.R", "thigh.R"), "kneeR": ("DEF-shin.R", "shin.R"),
        "ankleR": ("DEF-foot.R", "foot.R"), "toeR": ("DEF-toe.R", "toe.R"),
    },
    "cc": {
        "head": ("CC_Base_Head",), "neck": ("CC_Base_NeckTwist01",), "chest": ("CC_Base_Spine02",),
        "pelvis": ("CC_Base_Hip",),
        "shoulderL": ("CC_Base_L_Upperarm",), "elbowL": ("CC_Base_L_Forearm",), "wristL": ("CC_Base_L_Hand",),
        "hipL": ("CC_Base_L_Thigh",), "kneeL": ("CC_Base_L_Calf",), "ankleL": ("CC_Base_L_Foot",),
        "toeL": ("CC_Base_L_ToeBase",),
        "shoulderR": ("CC_Base_R_Upperarm",), "elbowR": ("CC_Base_R_Forearm",), "wristR": ("CC_Base_R_Hand",),
        "hipR": ("CC_Base_R_Thigh",), "kneeR": ("CC_Base_R_Calf",), "ankleR": ("CC_Base_R_Foot",),
        "toeR": ("CC_Base_R_ToeBase",),
    },
    "vrm": {
        "head": ("J_Bip_C_Head", "head"), "neck": ("J_Bip_C_Neck", "neck"),
        "chest": ("J_Bip_C_UpperChest", "J_Bip_C_Chest", "upperChest", "chest"), "pelvis": ("J_Bip_C_Hips", "hips"),
        "shoulderL": ("J_Bip_L_UpperArm", "leftUpperArm"), "elbowL": ("J_Bip_L_LowerArm", "leftLowerArm"),
        "wristL": ("J_Bip_L_Hand", "leftHand"), "hipL": ("J_Bip_L_UpperLeg", "leftUpperLeg"),
        "kneeL": ("J_Bip_L_LowerLeg", "leftLowerLeg"), "ankleL": ("J_Bip_L_Foot", "leftFoot"),
        "toeL": ("J_Bip_L_ToeBase", "leftToes"),
        "shoulderR": ("J_Bip_R_UpperArm", "rightUpperArm"), "elbowR": ("J_Bip_R_LowerArm", "rightLowerArm"),
        "wristR": ("J_Bip_R_Hand", "rightHand"), "hipR": ("J_Bip_R_UpperLeg", "rightUpperLeg"),
        "kneeR": ("J_Bip_R_LowerLeg", "rightLowerLeg"), "ankleR": ("J_Bip_R_Foot", "rightFoot"),
        "toeR": ("J_Bip_R_ToeBase", "rightToes"),
    },
}
RIG_KINDS = tuple(RIG_TABLES)
#: The markers a rig must give for the markers to be read from it (the rest are found on the mesh).
RIG_REQUIRED = tuple(name for name in BODY_MARKERS if name not in ("headTop", "chin")) + ("head",)


def bone_key(name: str) -> str:
    """A bone name without a namespace (``mixamorig:``, ``mixamorig1:``) and case, for matching."""
    return name.rsplit(":", 1)[-1].lower()


def rig_kind(bone_names: Iterable[str]) -> Optional[str]:
    """The naming convention most of a rig's bones follow, or ``None`` when no convention names every joint."""
    keys = {bone_key(name) for name in bone_names}
    best, best_count = None, 0
    for kind, table in RIG_TABLES.items():
        found = [marker for marker in RIG_REQUIRED if any(bone_key(b) in keys for b in table[marker])]
        if len(found) == len(RIG_REQUIRED) and len(found) > best_count:
            best, best_count = kind, len(found)
    return best


def markers_from_rig(joints: Mapping[str, Any], positions: Optional[Any] = None) -> Tuple[str, Dict[str, Tuple[float, float, float]]]:
    """The body markers from the joints of an existing rig (bone name to the world position of its head, as the
    character stands). ``positions`` (the character's vertices) give the top of the head when the rig names none and
    the chin on the face. Returns the rig's convention and the markers; raises :class:`MarkerError` (``no-rig``) when
    no known convention names every joint."""
    kind = rig_kind(joints)
    if kind is None:
        raise MarkerError("no-rig")
    table = RIG_TABLES[kind]
    by_key = {bone_key(name): _vec(point) for name, point in joints.items()}

    def joint(marker: str) -> Optional[np.ndarray]:
        for bone in table.get(marker, ()):
            if bone_key(bone) in by_key:
                return by_key[bone_key(bone)]
        return None

    found = {marker: joint(marker) for marker in BODY_MARKERS if marker not in ("headTop", "chin")}
    head, neck = joint("head"), found["neck"]
    assert head is not None and neck is not None
    top = joint("headTop")
    points = as_points(positions) if positions is not None else None
    if top is None:
        if points is not None and len(points):
            column = points[np.linalg.norm(points[:, :2] - head[:2], axis=1) < 0.12]
            column = column if len(column) else points
            top = np.array([head[0], head[1], float(column[:, 2].max())])
        else:
            top = head + _unit(head - neck) * 2.2 * float(np.linalg.norm(head - neck))
    chin = head + (neck - head) * 0.15
    if points is not None and len(points):
        near = points[(np.abs(points[:, 2] - chin[2]) < 0.015) & (np.abs(points[:, 0] - head[0]) < 0.05)]
        if len(near):
            chin = np.array([head[0], float(near[:, 1].min()), chin[2]])
    found["headTop"], found["chin"] = top, chin
    return kind, {name: tuple(float(c) for c in found[name]) for name in BODY_MARKERS}


# --------------------------------------------------------------------------------------------------
# Marker checks
# --------------------------------------------------------------------------------------------------

#: Problems the add-on finds in the markers before a rig (text keys ``ped.marker-problem.<code>``).
MARKER_PROBLEMS = ("missing", "side", "order", "asymmetric", "outside")


class MarkerProblem(NamedTuple):
    code: str
    markers: Tuple[str, ...]


def _length(markers: Mapping[str, Any], a: str, b: str) -> float:
    return float(np.linalg.norm(_vec(markers[a]) - _vec(markers[b])))


def marker_problems(markers: Mapping[str, Any], positions: Optional[Any] = None) -> List[MarkerProblem]:
    """What looks wrong with the markers: missing ones, the left side not at +X, the head not above the neck and the
    neck not above the pelvis, limbs whose left and right lengths differ by more than 30 %, markers far from every
    vertex (with ``positions``). Durty Cloth Tool checks the same and more; this only answers sooner."""
    missing = tuple(name for name in BODY_MARKERS if name not in markers)
    if missing:
        return [MarkerProblem("missing", missing)]
    problems = []
    cx = centre_x(markers)
    wrong = tuple(name for name in LEFT + RIGHT if (_vec(markers[name])[0] - cx) * (1 if side(name) == "L" else -1) <= 0)
    if wrong:
        problems.append(MarkerProblem("side", wrong))
    z = {name: _vec(markers[name])[2] for name in BODY_MARKERS}
    order = []
    if not z["headTop"] > z["chin"] > z["pelvis"]:
        order += ["headTop", "chin"]
    if not z["neck"] > z["chest"] > z["pelvis"]:
        order += ["neck", "chest", "pelvis"]
    for suffix in "LR":
        if not z[f"hip{suffix}"] > z[f"knee{suffix}"] > z[f"ankle{suffix}"]:
            order += [f"hip{suffix}", f"knee{suffix}", f"ankle{suffix}"]
    if order:
        problems.append(MarkerProblem("order", tuple(dict.fromkeys(order))))
    uneven = []
    for chain in (("shoulder", "elbow", "wrist"), ("hip", "knee", "ankle")):
        for a, b in zip(chain, chain[1:]):
            left, right = _length(markers, f"{a}L", f"{b}L"), _length(markers, f"{a}R", f"{b}R")
            if max(left, right) > 1e-6 and abs(left - right) / max(left, right) > 0.3:
                uneven += [f"{a}L", f"{b}L", f"{a}R", f"{b}R"]
    if uneven:
        problems.append(MarkerProblem("asymmetric", tuple(dict.fromkeys(uneven))))
    if positions is not None:
        points = as_points(positions)
        if len(points):
            sample = points[:: max(1, len(points) // 60000)]
            far = []
            for name in BODY_MARKERS:
                distance = float(np.min(np.linalg.norm(sample - _vec(markers[name]), axis=1)))
                if distance > 0.3:
                    far.append(name)
            if far:
                problems.append(MarkerProblem("outside", tuple(far)))
    return problems


# --------------------------------------------------------------------------------------------------
# The character
# --------------------------------------------------------------------------------------------------

#: The part roles the rig knows (``protocol.PED_PART_ROLES``) and the add-on's own "guess it".
ROLES: Tuple[str, ...] = protocol.PED_PART_ROLES
AUTO_ROLE = "auto"
#: Words in an object's or its materials' names that suggest its role, checked in this order.
ROLE_WORDS: Tuple[Tuple[str, Tuple[str, ...]], ...] = (
    ("eyes", ("eye", "eyeball", "iris", "cornea", "pupil", "sclera")),
    ("teeth", ("teeth", "tooth", "tongue", "gum")),
    ("hair", ("hair", "ponytail", "braid", "bang", "fringe", "pigtail")),
    ("head", ("head", "face", "eyebrow", "brow", "eyelash", "lash", "eyelid", "beard", "moustache", "mustache")),
    ("accessory", ("glasses", "hat", "cap", "earring", "necklace", "watch", "helmet", "mask", "jewel")),
)
#: Words of a name: CamelCase and lowercase runs of letters (digits, ``_``, ``.`` and ``-`` separate them).
_WORD = re.compile(r"[A-Z]?[a-z]+|[A-Z]+(?![a-z])")
#: Words about the eyes that belong to the head ("EyeBrow" splits into "eye" and "brow").
_AROUND_EYES = ("eyebrow", "eyelash", "eyelid", "brow", "lash", "lid")


def _matches(word: str, key: str) -> bool:
    """A word names a key: exactly, as a plural, or (for keys of four letters or more) as its start."""
    return word in (key, key + "s", key + "es") or (len(key) >= 4 and word.startswith(key))


def guess_role(object_name: str, material_names: Iterable[str] = ()) -> str:
    """The role a part probably has, from the words in its name and then its materials' names (``body`` when none
    fits). Eyebrows, eyelashes and eyelids belong to the head, never to the eyes."""
    for names in ([object_name], list(material_names)):
        words = [word.lower() for name in names for word in _WORD.findall(name)]
        around_eyes = any(word.startswith(_AROUND_EYES) for word in words)
        for role, keys in ROLE_WORDS:
            if role == "eyes" and around_eyes:
                continue
            for word in words:
                if any(_matches(word, key) for key in keys):
                    return role
    return "body"


#: The most vertices and triangles a rig takes (Durty Cloth Tool's limits), and the most a ped should carry in its
#: most detailed level (Durty Cloth Tool warns above it).
MAX_VERTICES = protocol.MAX_PED_RIG_VERTICES
MAX_TRIANGLES = protocol.MAX_PED_RIG_TRIANGLES
PED_BUDGET = 80_000
#: The usual height of a ped, and the range that needs no question.
USUAL_HEIGHT = 1.8
HEIGHT_RANGE = (1.4, 2.2)
#: How far the character may stand from the origin: every marker must lie within 3 m of it.
MAX_REACH = 3.0


class Facts(NamedTuple):
    """What the character checks read from Blender."""

    objects: int = 0
    vertices: int = 0
    triangles: int = 0
    materials: int = 0
    lower: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    upper: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    #: Objects that are moved, turned or scaled (their transforms are not applied), and those mirrored by a negative
    #: scale.
    transformed: Tuple[str, ...] = ()
    #: Objects with modifiers that add or change geometry (anything but an Armature).
    modified: Tuple[str, ...] = ()
    #: Objects with shape keys.
    shape_keys: Tuple[str, ...] = ()
    #: The armatures an old rig moves the character with (names).
    rigs: Tuple[str, ...] = ()
    #: The add-on's own rig is applied.
    rigged: bool = False
    #: Where the feet point, in degrees about Z from the front (-Y), counter-clockwise seen from above; ``None`` when
    #: the shape does not say.
    facing: Optional[float] = None
    #: The legs look like they are at the top (the character stands on its head).
    upside_down: bool = False

    @property
    def size(self) -> np.ndarray:
        return np.asarray(self.upper, dtype=np.float64) - np.asarray(self.lower, dtype=np.float64)

    @property
    def height(self) -> float:
        return float(self.size[2])


class Check(NamedTuple):
    """One row of the character checks: ``level`` (``ok``, ``warning`` or ``error``), the text key and its fields,
    and the fixes offered (operator ids of the panel, with their properties)."""

    code: str
    level: str
    key: str
    fields: Optional[Dict[str, Any]] = None
    fixes: Tuple[Tuple[str, Dict[str, Any]], ...] = ()


#: Units a character may have been exported in by mistake: their name, the factor to metres and the height range of
#: a person in them.
UNITS = (("cm", 0.01, (120.0, 230.0)), ("mm", 0.001, (1200.0, 2300.0)), ("in", 0.0254, (48.0, 90.0)))


def unit_guess(height: float) -> Optional[Tuple[str, float]]:
    """The unit a character of this height was probably made in, when it is not metres: ``(unit, factor)``."""
    for name, factor, (low, high) in UNITS:
        if low <= height <= high:
            return name, factor
    return None


def facing_guess(positions: Any) -> Optional[float]:
    """Where the feet point, in degrees about Z from -Y (counter-clockwise seen from above: 90 is +X), from the toes
    reaching further than the heels; ``None`` when the feet do not say."""
    points = as_points(positions)
    if len(points) < 8:
        return None
    z0 = float(points[:, 2].min())
    height = float(np.ptp(points[:, 2]))
    if height < 0.2:
        return None
    soles = points[points[:, 2] < z0 + 0.03 * height]
    shins = points[(points[:, 2] > z0 + 0.08 * height) & (points[:, 2] < z0 + 0.14 * height)]
    if len(soles) < 4 or len(shins) < 4:
        return None
    offset = soles[:, :2].mean(axis=0) - shins[:, :2].mean(axis=0)
    if float(np.linalg.norm(offset)) < 0.01 * height:
        return None
    return math.degrees(math.atan2(offset[0], -offset[1]))


def stands_on_head(positions: Any, triangles: Any) -> bool:
    """Whether the legs (two pieces with nothing between them) are at the top of the shape and not at the bottom."""
    points = as_points(positions)
    tris = np.asarray(triangles, dtype=np.int64).reshape(-1, 3)
    if len(points) < 8 or not len(tris):
        return False
    z0, height = float(points[:, 2].min()), float(np.ptp(points[:, 2]))
    cx = float(np.median(points[:, 0]))

    def legs(fraction: float) -> bool:
        pieces = outlines(section(points, tris, (0.0, 0.0, z0 + fraction * height), (0.0, 0.0, 1.0)))
        sides = {np.sign(p.centre[0] - cx) for p in pieces if not p.lo <= cx <= p.hi}
        return len(pieces) >= 2 and not any(p.lo <= cx <= p.hi for p in pieces) and sides == {-1.0, 1.0}

    bottom = legs(0.2) or legs(0.3)
    top = legs(0.8) or legs(0.7)
    return top and not bottom


def checks(facts: Facts, *, facing_confirmed: bool = False) -> List[Check]:
    """The character checks, in the order the panel shows them. Fixes that change the character's size or turn it
    ask first (the panel's buttons confirm); nothing is changed without the user's click."""
    rows: List[Check] = []
    if facts.objects == 0:
        return [Check("character", "error", "ped.check.none")]
    if facts.rigged:  # the character stands in the game's rest pose now; what was checked before still holds
        rows.append(Check("rigged", "ok", "ped.check.rigged"))
        if facts.transformed or facts.modified:
            rows.append(Check("changed", "warning", "ped.check.rigged-changed"))
        return rows
    if facts.transformed:
        rows.append(Check("transforms", "warning", "ped.check.transforms", {"count": len(facts.transformed)},
                          (("dct_link.ped_apply_transforms", {}),)))
    if facts.modified:
        rows.append(Check("modifiers", "warning", "ped.check.modifiers",
                          {"count": len(facts.modified), "names": ", ".join(facts.modified[:3])},
                          (("dct_link.ped_apply_modifiers", {}),)))
    if facts.rigs and not facts.rigged:
        rows.append(Check("rig", "warning", "ped.check.old-rig", {"name": facts.rigs[0]},
                          (("dct_link.ped_remove_old_rig", {}),)))
    if facts.shape_keys and not facts.rigged:
        rows.append(Check("shape-keys", "warning", "ped.check.shape-keys", {"count": len(facts.shape_keys)},
                          (("dct_link.ped_remove_shape_keys", {}),)))
    size = facts.size
    height = facts.height
    upright = height >= 0.6 * max(float(size[0]), float(size[1]), 1e-9)
    if not upright:
        rows.append(Check("upright", "error", "ped.check.lying",
                          fixes=(("dct_link.ped_turn", {"axis": "X", "degrees": 90.0}),
                                 ("dct_link.ped_turn", {"axis": "X", "degrees": -90.0}))))
    elif facts.upside_down:
        rows.append(Check("upright", "error", "ped.check.upside-down",
                          fixes=(("dct_link.ped_turn", {"axis": "Y", "degrees": 180.0}),)))
    unit = unit_guess(height)
    wrong_size = (unit is not None and not HEIGHT_RANGE[0] <= height <= HEIGHT_RANGE[1]) or height > MAX_REACH * 0.95
    if unit is not None and not HEIGHT_RANGE[0] <= height <= HEIGHT_RANGE[1]:
        name, factor = unit
        rows.append(Check("height", "error", "ped.check.unit",
                          {"height": f"{height:.1f}", "unit": f"ped.unit.{name}", "metres": f"{height * factor:.2f}"},
                          (("dct_link.ped_scale", {"factor": factor}),)))
    elif height > MAX_REACH * 0.95:
        rows.append(Check("height", "error", "ped.check.too-tall", {"height": f"{height:.2f}"},
                          (("dct_link.ped_scale", {"factor": USUAL_HEIGHT / height}),)))
    elif not HEIGHT_RANGE[0] <= height <= HEIGHT_RANGE[1]:
        rows.append(Check("height", "warning", "ped.check.height-unusual", {"height": f"{height:.2f}"},
                          (("dct_link.ped_scale", {"factor": USUAL_HEIGHT / max(height, 1e-6)}),)))
    else:
        rows.append(Check("height", "ok", "ped.check.height", {"height": f"{height:.2f}"}))
    lower, upper = np.asarray(facts.lower), np.asarray(facts.upper)
    middle = (lower + upper) / 2
    reach = float(np.max(np.abs(np.concatenate([lower, upper])))) if upright else 0.0
    if upright and not wrong_size and (reach > MAX_REACH * 0.9 or float(np.hypot(middle[0], middle[1])) > 1.0
                                       or abs(lower[2]) > 1.0):
        rows.append(Check("origin", "warning", "ped.check.origin",
                          {"distance": f"{float(np.linalg.norm(middle)):.1f}"}, (("dct_link.ped_to_origin", {}),)))
    if upright and not facts.rigged:
        if facing_confirmed:
            rows.append(Check("facing", "ok", "ped.check.facing-done"))
        else:
            guess = facts.facing
            fixes = (("dct_link.ped_confirm_facing", {}), ("dct_link.ped_turn", {"axis": "Z", "degrees": 90.0}),
                     ("dct_link.ped_turn", {"axis": "Z", "degrees": -90.0}),
                     ("dct_link.ped_turn", {"axis": "Z", "degrees": 180.0}))
            if guess is None or abs(guess) <= 45.0:
                rows.append(Check("facing", "warning", "ped.check.facing", fixes=fixes))
            else:
                # Seen in the front view, +X is on the user's right.
                direction = "back" if abs(guess) > 135.0 else ("screen-right" if guess > 0 else "screen-left")
                rows.append(Check("facing", "warning", "ped.check.facing-other",
                                  {"direction": f"ped.direction.{direction}"}, fixes))
    if facts.vertices > MAX_VERTICES or facts.triangles > MAX_TRIANGLES:
        rows.append(Check("size", "error", "ped.check.size-limit",
                          {"vertices": facts.vertices, "triangles": facts.triangles, "max_vertices": MAX_VERTICES,
                           "max_triangles": MAX_TRIANGLES}))
    elif facts.vertices > PED_BUDGET:
        rows.append(Check("size", "warning", "ped.check.size-budget",
                          {"vertices": facts.vertices, "budget": PED_BUDGET}))
    else:
        rows.append(Check("size", "ok", "ped.check.size", {"vertices": facts.vertices}))
    return rows


def checks_pass(rows: Sequence[Check]) -> bool:
    """Whether the character may be rigged: no error, and the transforms, modifiers, an old rig and the facing
    settled."""
    blocking = {"transforms", "modifiers", "rig", "shape-keys", "facing", "character"}
    return all(row.level != "error" and not (row.level == "warning" and row.code in blocking) for row in rows)


# --------------------------------------------------------------------------------------------------
# The rig request
# --------------------------------------------------------------------------------------------------


class Part(NamedTuple):
    """One mesh of the character as the rig request carries it: its object name, role, world positions ``(n, 3)``
    and triangles ``(t, 3)`` (indices into its own positions)."""

    name: str
    role: str
    positions: np.ndarray
    triangles: np.ndarray


class RigInput(NamedTuple):
    """The character as one mesh for ``ped.rig``: positions (float32, x y z per vertex), triangles (uint32), the part
    roles with each vertex's part id (empty when every part is ``body``), each object's vertex range, and the topology
    hash that tells later whether the meshes are still the ones rigged."""

    positions: np.ndarray
    triangles: np.ndarray
    roles: List[str]
    part_ids: Optional[bytes]
    ranges: List[Tuple[str, int, int]]
    topology: str

    @property
    def vertices(self) -> int:
        return len(self.positions) // 3

    @property
    def triangle_count(self) -> int:
        return len(self.triangles) // 3


def topology_hash(parts: Sequence[Tuple[str, int, Any]]) -> str:
    """A hash of each part's name, vertex count and triangles: it changes when a mesh is edited (not when it only
    moves)."""
    digest = hashlib.sha256()
    for name, count, triangles in parts:
        digest.update(name.encode("utf-8") + b"\0" + int(count).to_bytes(4, "little"))
        digest.update(np.ascontiguousarray(np.asarray(triangles, dtype=np.uint32)).tobytes())
    return digest.hexdigest()


def rig_input(parts: Sequence[Part]) -> RigInput:
    """Joins the parts into the one mesh ``ped.rig`` carries."""
    positions, triangles, ids, ranges = [], [], [], []
    roles: List[str] = []
    offset = 0
    for part in parts:
        points = np.asarray(part.positions, dtype=np.float64).reshape(-1, 3)
        tris = np.asarray(part.triangles, dtype=np.int64).reshape(-1, 3)
        role = part.role if part.role in ROLES else "body"
        if role not in roles:
            roles.append(role)
        positions.append(points)
        triangles.append(tris + offset)
        ids.append(np.full(len(points), roles.index(role), dtype=np.uint8))
        ranges.append((part.name, offset, len(points)))
        offset += len(points)
    if not positions:
        raise ValueError("a rig needs at least one mesh")
    all_points = np.concatenate(positions).astype(np.float32)
    all_triangles = np.concatenate(triangles).astype(np.uint32) if triangles else np.zeros((0, 3), dtype=np.uint32)
    part_ids = np.concatenate(ids).tobytes() if roles != ["body"] else None
    topology = topology_hash([(p.name, len(np.asarray(p.positions).reshape(-1, 3)), p.triangles) for p in parts])
    return RigInput(all_points.reshape(-1), all_triangles.reshape(-1), roles if part_ids is not None else [],
                    part_ids, ranges, topology)


#: The rig options and their defaults (the protocol's).
DEFAULT_OPTIONS = {"fingers": "off", "face": "off", "rollBones": True, "helperBones": True, "refineMarkers": True,
                   "restModel": "volume"}


def rig_options(fingers: str = "off", face: str = "off", roll_bones: bool = True, helper_bones: bool = True,
                refine_markers: bool = True, rest_model: str = "volume") -> Dict[str, Any]:
    """The ``options`` of a ``ped.rig``, only those that differ from the defaults."""
    chosen = {"fingers": fingers if fingers in protocol.PED_DETAIL_MODES else "off",
              "face": face if face in protocol.PED_DETAIL_MODES else "off",
              "rollBones": bool(roll_bones), "helperBones": bool(helper_bones),
              "refineMarkers": bool(refine_markers),
              "restModel": rest_model if rest_model in protocol.PED_REST_MODELS else "volume"}
    return {key: value for key, value in chosen.items() if DEFAULT_OPTIONS[key] != value}


# --------------------------------------------------------------------------------------------------
# Applying a rig
# --------------------------------------------------------------------------------------------------


def blender_matrix(row_major: Sequence[float]) -> np.ndarray:
    """A protocol matrix (16 floats, row major, row-vector convention: the last row is the position) as Blender's 4x4
    (column vectors: the last column is the position)."""
    return np.asarray(row_major, dtype=np.float64).reshape(4, 4).T


def protocol_matrix(matrix: Any) -> Tuple[float, ...]:
    """Blender's 4x4 back as the protocol's 16 floats."""
    return tuple(float(v) for v in np.asarray(matrix, dtype=np.float64).reshape(4, 4).T.reshape(-1))


class BonePlan(NamedTuple):
    """One bone of the armature to build: its name, parent index, rest matrix in armature space (Blender's
    convention, rotation and position from the rig, never changed), the length it is drawn with, and its pose matrix
    (the character's own pose) when the rig gives one."""

    name: str
    parent: int
    rest: np.ndarray
    length: float
    pose: Optional[np.ndarray]
    tag: int
    flags: int


#: Drawn lengths of bones: the distance to their first child, within these bounds; leaves get the default.
MIN_BONE = 0.01
MAX_BONE = 0.6
LEAF_BONE = 0.05
#: A bone whose own Y axis does not point at its child within about 30 degrees (game rest frames often do not) is
#: drawn this short instead, so it never reaches into nowhere.
SHORT_BONE = 0.03
POINTING = math.cos(math.radians(30.0))


def armature_plan(bones: Sequence[Any], poses: Optional[Sequence[Sequence[float]]] = None) -> List[BonePlan]:
    """The armature for a template or a rig: one :class:`BonePlan` per bone in the skeleton's order. ``bones`` are
    dct_link ``PedBone`` values (name, tag, parent, flags, rotation, translation, world)."""
    rests = [blender_matrix(bone.world) for bone in bones]
    children: Dict[int, List[int]] = {}
    for index, bone in enumerate(bones):
        if bone.parent >= 0:
            children.setdefault(bone.parent, []).append(index)
    plan = []
    for index, bone in enumerate(bones):
        length = LEAF_BONE
        for child in children.get(index, []):
            offset = rests[child][:3, 3] - rests[index][:3, 3]
            distance = float(np.linalg.norm(offset))
            if distance >= MIN_BONE:
                along = float(np.dot(rests[index][:3, 1], offset)) / distance
                length = min(distance, MAX_BONE) if along > POINTING else SHORT_BONE
                break
        pose = blender_matrix(poses[index]) if poses is not None else None
        plan.append(BonePlan(bone.name, int(bone.parent), rests[index], length, pose, int(bone.tag), int(bone.flags)))
    return plan


def _inverse_rigid(matrix: np.ndarray) -> np.ndarray:
    inverse = np.eye(4)
    rotation = matrix[:3, :3]
    inverse[:3, :3] = rotation.T
    inverse[:3, 3] = -rotation.T @ matrix[:3, 3]
    return inverse


def _inverse(matrix: np.ndarray) -> np.ndarray:
    return np.linalg.inv(matrix)


def pose_bases(rest: Sequence[np.ndarray], posed: Sequence[np.ndarray], parents: Sequence[int]) -> List[np.ndarray]:
    """Each pose bone's ``matrix_basis`` that puts the bones at ``posed`` (armature space) from ``rest``: Blender
    composes a bone's pose as its parent's pose times its rest offset from the parent times its basis."""
    bases = []
    for index, parent in enumerate(parents):
        if parent < 0:
            local_rest, local_pose = rest[index], posed[index]
        else:
            local_rest = _inverse(rest[parent]) @ rest[index]
            local_pose = _inverse(posed[parent]) @ posed[index]
        bases.append(_inverse(local_rest) @ local_pose)
    return bases


def rest_parts(rest_positions: Any, ranges: Sequence[Tuple[str, int, int]]) -> Dict[str, np.ndarray]:
    """Each object's vertices in the game's rest pose, from a rig's rest positions (in the request's vertex order)."""
    points = np.asarray(rest_positions, dtype=np.float64).reshape(-1, 3)
    return {name: points[start:start + count] for name, start, count in ranges}


def vertex_groups(bone_indices: bytes, weights: bytes, bone_names: Sequence[str], start: int, count: int
                  ) -> Dict[str, List[Tuple[float, np.ndarray]]]:
    """The vertex groups of one object from a rig's four bone indices and weights per vertex (weights in 255ths):
    bone name to ``(weight, vertex indices)`` pairs, so Blender adds each weight to all its vertices at once."""
    indices = np.frombuffer(bone_indices, dtype=np.uint8).reshape(-1, 4)[start:start + count]
    values = np.frombuffer(weights, dtype=np.uint8).reshape(-1, 4)[start:start + count]
    groups: Dict[str, List[Tuple[float, np.ndarray]]] = {}
    vertices = np.arange(count)
    for slot in range(4):
        used = values[:, slot] > 0
        if not used.any():
            continue
        bones, amounts, which = indices[used, slot], values[used, slot], vertices[used]
        for bone in np.unique(bones):
            of_bone = bones == bone
            for amount in np.unique(amounts[of_bone]):
                chosen = which[of_bone & (amounts == amount)]
                groups.setdefault(bone_names[int(bone)], []).append((float(amount) / 255.0, chosen))
    return groups


# --------------------------------------------------------------------------------------------------
# Poses
# --------------------------------------------------------------------------------------------------

#: The test poses, applied from the game's rest pose down the chain, in the armature's axes (X to the character's
#: left, Y to its back, Z up): ``("aim", bone, child, direction)`` turns a bone the shortest way so that its child's
#: joint lies in ``direction`` (so the pose does not depend on how the template's rest pose holds the limb), and
#: ``("turn", bone, axis, degrees)`` turns a bone about an axis through its joint. Generic bends by bone name, not game
#: animations.
_L, _R = "SKEL_L_", "SKEL_R_"
TEST_POSES: Dict[str, Tuple[Tuple[Any, ...], ...]] = {
    "arms_up": (("aim", _L + "UpperArm", _L + "Forearm", (0.35, 0.0, 1.0)),
                ("aim", _L + "Forearm", _L + "Hand", (0.35, 0.0, 1.0)),
                ("aim", _R + "UpperArm", _R + "Forearm", (-0.35, 0.0, 1.0)),
                ("aim", _R + "Forearm", _R + "Hand", (-0.35, 0.0, 1.0))),
    "arms_forward": (("aim", _L + "UpperArm", _L + "Forearm", (0.25, -1.0, -0.1)),
                     ("aim", _L + "Forearm", _L + "Hand", (0.15, -1.0, 0.0)),
                     ("aim", _R + "UpperArm", _R + "Forearm", (-0.25, -1.0, -0.1)),
                     ("aim", _R + "Forearm", _R + "Hand", (-0.15, -1.0, 0.0))),
    "squat": (("turn", "SKEL_Spine1", "X", 20.0),
              ("aim", _L + "Thigh", _L + "Calf", (0.2, -1.0, -0.25)),
              ("aim", _L + "Calf", _L + "Foot", (0.05, 0.4, -1.0)),
              ("aim", _R + "Thigh", _R + "Calf", (-0.2, -1.0, -0.25)),
              ("aim", _R + "Calf", _R + "Foot", (-0.05, 0.4, -1.0))),
    "walk": (("aim", _L + "Thigh", _L + "Calf", (0.03, -0.55, -1.0)),
             ("aim", _L + "Calf", _L + "Foot", (0.03, -0.2, -1.0)),
             ("aim", _R + "Thigh", _R + "Calf", (-0.03, 0.35, -1.0)),
             ("aim", _R + "Calf", _R + "Foot", (-0.03, 0.75, -1.0)),
             ("aim", _L + "UpperArm", _L + "Forearm", (0.25, 0.35, -1.0)),
             ("aim", _R + "UpperArm", _R + "Forearm", (-0.25, -0.35, -1.0))),
    "twist": (("turn", "SKEL_Spine1", "Z", 15.0), ("turn", "SKEL_Spine2", "Z", 15.0),
              ("turn", "SKEL_Spine3", "Z", 15.0), ("turn", "SKEL_Neck_1", "Z", 10.0)),
}
POSES = ("yours", "rest") + tuple(TEST_POSES)
_AXES = {"X": (1.0, 0.0, 0.0), "Y": (0.0, 1.0, 0.0), "Z": (0.0, 0.0, 1.0)}


def shortest_turn(start: Any, end: Any) -> np.ndarray:
    """The rotation that turns the direction ``start`` onto ``end`` the shortest way."""
    a, b = _unit(_vec(start)), _unit(_vec(end))
    axis = np.cross(a, b)
    sin, cos = float(np.linalg.norm(axis)), float(np.dot(a, b))
    if sin < 1e-9:
        if cos > 0:
            return np.eye(3)
        other = np.array([1.0, 0.0, 0.0]) if abs(a[0]) < 0.9 else np.array([0.0, 1.0, 0.0])
        return _rotation(np.cross(a, other), math.pi)
    return _rotation(axis / sin, math.atan2(sin, cos))


def posed_world(rest: Sequence[np.ndarray], parents: Sequence[int], turns: Mapping[int, Any]) -> List[np.ndarray]:
    """The bones' armature-space matrices after turning some of them; children follow their parents. A turn is a 3x3
    rotation about the armature's axes through the bone's joint, or ``(child index, direction)``: the shortest turn
    that puts the child's joint in that direction. Bones must come after their parents, as in a ped skeleton."""
    result: List[np.ndarray] = []
    for index, parent in enumerate(parents):
        if parent >= index:
            raise ValueError("a bone comes before its parent")
        world = rest[index].copy() if parent < 0 else result[parent] @ (_inverse(rest[parent]) @ rest[index])
        turn = turns.get(index)
        if isinstance(turn, tuple):
            child, direction = turn
            offset = world[:3, :3] @ (_inverse(rest[index]) @ rest[child])[:3, 3]
            turn = shortest_turn(offset, direction) if float(np.linalg.norm(offset)) > 1e-6 else None
        if turn is not None:
            world[:3, :3] = turn @ world[:3, :3]
        result.append(world)
    return result


def test_pose(name: str, names: Sequence[str], rest: Sequence[np.ndarray], parents: Sequence[int]) -> List[np.ndarray]:
    """The armature-space matrices of a test pose (bones the skeleton lacks are left out)."""
    index = {bone: i for i, bone in enumerate(names)}
    turns: Dict[int, Any] = {}
    for entry in TEST_POSES[name]:
        if entry[0] == "aim":
            _, bone, child, direction = entry
            if bone in index and child in index:
                turns[index[bone]] = (index[child], tuple(direction))
        else:
            _, bone, axis, degrees = entry
            if bone in index:
                turns[index[bone]] = _rotation(_AXES[axis], math.radians(degrees))
    return posed_world(rest, parents, turns)


def strain(rest_positions: Any, posed_positions: Any, edges: Any, *, stretched: float = 1.6,
           squashed: float = 0.35) -> np.ndarray:
    """The vertices of edges that a pose stretches beyond ``stretched`` times or squashes below ``squashed`` times
    their length in the rest pose."""
    rest = as_points(rest_positions)
    posed = as_points(posed_positions)
    pairs = np.asarray(edges, dtype=np.int64).reshape(-1, 2)
    if not len(pairs) or len(rest) != len(posed):
        return np.zeros(0, dtype=np.int64)
    before = np.linalg.norm(rest[pairs[:, 0]] - rest[pairs[:, 1]], axis=1)
    after = np.linalg.norm(posed[pairs[:, 0]] - posed[pairs[:, 1]], axis=1)
    ratio = np.divide(after, before, out=np.ones_like(after), where=before > 1e-7)
    bad = (ratio > stretched) | (ratio < squashed)
    return np.unique(pairs[bad].reshape(-1))


# --------------------------------------------------------------------------------------------------
# Local checks of the rigged character
# --------------------------------------------------------------------------------------------------

#: Bones that never move the mesh: weights on them are moved to their parents in Durty Cloth Tool.
def non_deforming(name: str) -> bool:
    return name == "SKEL_ROOT" or name.startswith(("IK_", "PH_"))


#: Findings of Run Checks (text keys ``ped.check.<code>``) and whether Durty Cloth Tool refuses the character for them.
CHECK_CODES = ("unweighted", "too-many", "non-deforming", "unknown-groups", "armature-changed", "mesh-changed",
               "strain")
REFUSED_CODES = frozenset({"unweighted", "armature-changed", "mesh-changed"})


class Finding(NamedTuple):
    """One finding of Run Checks: its code, how many, the names it concerns, and per object the vertices to show."""

    code: str
    count: int
    names: Tuple[str, ...] = ()
    vertices: Optional[Dict[str, np.ndarray]] = None
    pose: str = ""


def weight_findings(objects: Mapping[str, Mapping[str, Any]], bones: Sequence[str]) -> List[Finding]:
    """The weight checks per object: ``objects`` maps an object name to its ``counts`` (bones with weight per vertex),
    ``totals`` (summed weight per vertex), ``bad`` (weight on a bone that never deforms, per vertex) and ``groups``
    (its vertex group names)."""
    known = set(bones)
    unweighted, too_many, bad = {}, {}, {}
    unknown: List[str] = []
    for name, data in objects.items():
        counts = np.asarray(data["counts"])
        totals = np.asarray(data["totals"], dtype=np.float64)
        flagged = np.asarray(data["bad"], dtype=bool)
        empty = np.nonzero(((counts == 0) | (totals <= 1e-6)) & ~flagged)[0]  # flagged: DCT moves it up the chain
        if len(empty):
            unweighted[name] = empty
        many = np.nonzero(counts > 4)[0]
        if len(many):
            too_many[name] = many
        wrong = np.nonzero(flagged)[0]
        if len(wrong):
            bad[name] = wrong
        unknown += [group for group in data.get("groups", ()) if group not in known and not group.startswith("DCT")]
    findings = []
    for code, found in (("unweighted", unweighted), ("too-many", too_many), ("non-deforming", bad)):
        if found:
            findings.append(Finding(code, int(sum(len(v) for v in found.values())), (), found))
    if unknown:
        unique = tuple(dict.fromkeys(unknown))
        findings.append(Finding("unknown-groups", len(unique), unique))
    return findings


def armature_changes(expected: Mapping[str, Any], actual: Mapping[str, Any], *, distance: float = 0.0001,
                     degrees: float = 0.01) -> Tuple[str, ...]:
    """The bones whose rest matrix (Blender's 4x4, armature space) moved more than ``distance`` metres or turned more
    than ``degrees`` from the rig's, the rig's bones that are gone, and bones the rig does not have (each would be a
    joint Durty Cloth Tool refuses)."""
    changed = [name for name in actual if name not in expected]
    for name, matrix in expected.items():
        found = actual.get(name)
        if found is None:
            changed.append(name)
            continue
        a, b = np.asarray(matrix, dtype=np.float64).reshape(4, 4), np.asarray(found, dtype=np.float64).reshape(4, 4)
        if float(np.linalg.norm(a[:3, 3] - b[:3, 3])) > distance:
            changed.append(name)
            continue
        if rotation_degrees(a[:3, :3], b[:3, :3]) > degrees:
            changed.append(name)
    return tuple(changed)


def rotation_degrees(first: Any, second: Any) -> float:
    """The angle between two rotation matrices, in degrees. Measured from their difference, so the float32 noise of
    matrices that went through Blender or the wire does not read as a turn (an angle from the trace would: 1e-7 of
    noise in the trace looks like 0.02 degrees)."""
    difference = float(np.linalg.norm(np.asarray(first, dtype=np.float64) - np.asarray(second, dtype=np.float64)))
    return math.degrees(2.0 * math.asin(min(1.0, difference / (2.0 * math.sqrt(2.0)))))


# --------------------------------------------------------------------------------------------------
# The report
# --------------------------------------------------------------------------------------------------


class ReportLine(NamedTuple):
    """One line of a rig's report or refusal: its level, text key and fields, and the markers it concerns."""

    level: str
    key: str
    fields: Dict[str, Any]
    markers: Tuple[str, ...] = ()
    template: Optional[str] = None


#: Warnings that are only notes (the rig is ready with them).
NOTE_WARNINGS = frozenset({"fingers_fallback"})


def report_lines(report: Mapping[str, Any]) -> List[ReportLine]:
    """A rig's report as the panel shows it: the outcome, each warning, the closer template."""
    lines: List[ReportLine] = []
    confidence = report.get("confidence")
    percent = int(round(float(confidence) * 100)) if isinstance(confidence, (int, float)) else 0
    ready = report.get("outcome") == "ready"
    lines.append(ReportLine("INFO" if ready else "WARNING", "ped.result.ready" if ready else "ped.result.review",
                            {"percent": percent}))
    for warning in report.get("warnings") or []:
        code = str(warning.get("code"))
        key = f"ped.warning.{code}" if code in protocol.PED_RIG_WARNINGS else "ped.warning.other"
        fields: Dict[str, Any] = {"code": code, "count": int(warning.get("count") or 0),
                                  "value": int(round(float(warning.get("value") or 0)))}
        level = "INFO" if code in NOTE_WARNINGS else "WARNING"
        lines.append(ReportLine(level, key, fields, tuple(m for m in warning.get("markers") or () if m in BODY_MARKERS),
                                warning.get("template")))
    suggested = report.get("suggestedTemplate")
    if suggested:
        lines.append(ReportLine("WARNING", "ped.suggest", {"template": suggested}, (), suggested))
    if report.get("proxy"):
        lines.append(ReportLine("INFO", "ped.result.proxy", {}))
    return lines


#: How far Durty Cloth Tool must move a marker (metres) before it counts as moved: the panel lists it and the 3D view
#: shows it yellow. The rig reports every marker, most of them where they were sent.
MOVED = 0.01


def refined_moves(report: Mapping[str, Any], markers: Mapping[str, Any], *, minimum: float = MOVED
                  ) -> List[Tuple[str, float]]:
    """The markers Durty Cloth Tool moved by more than ``minimum`` metres (``report.markers`` against the markers that
    were sent), largest first."""
    refined = report.get("markers") or {}
    moves = []
    for name, point in refined.items():
        if name in markers and isinstance(point, (list, tuple)) and len(point) == 3:
            distance = float(np.linalg.norm(_vec(point) - _vec(markers[name])))
            if distance > minimum:
                moves.append((name, distance))
    return sorted(moves, key=lambda move: -move[1])


def moved_markers(report: Mapping[str, Any], markers: Mapping[str, Any]) -> Dict[str, Tuple[float, float, float]]:
    """Where Durty Cloth Tool put the markers it moved (:func:`refined_moves`), by name: what the 3D view shows
    yellow, the same markers the panel lists."""
    refined = markers_from_json(json.dumps(report.get("markers") or {}))
    return {name: refined[name] for name, _ in refined_moves(report, markers) if name in refined}


#: Refusal codes whose text explains them; others get the general one.
REFUSAL_CODES = frozenset(protocol.PED_RIG_REFUSALS)


def refusal_lines(reasons: Sequence[Mapping[str, Any]]) -> List[ReportLine]:
    """A refused rig's reasons as the panel shows them (each code once, with every marker it named)."""
    by_code: Dict[str, List[str]] = {}
    for reason in reasons:
        code = str(reason.get("code"))
        by_code.setdefault(code, [])
        for marker in reason.get("markers") or ():
            if marker in protocol.PED_MARKERS and marker not in by_code[code]:
                by_code[code].append(marker)
    lines = []
    for code, markers in by_code.items():
        key = f"ped.refusal.{code}" if code in REFUSAL_CODES else "ped.refusal.other"
        lines.append(ReportLine("ERROR", key, {"code": code}, tuple(markers)))
    return lines


# --------------------------------------------------------------------------------------------------
# Sending
# --------------------------------------------------------------------------------------------------

#: Model name beginnings of the game's own peds (ambient, story, service, gang, cutscene, multiplayer and players):
#: a new ped's model never starts like them.
GAME_PREFIXES = ("a_m_", "a_f_", "a_c_", "s_m_", "s_f_", "u_m_", "u_f_", "g_m_", "g_f_", "ig_", "csb_", "cs_", "hc_",
                 "mp_", "player_")


def model_problem(model: str) -> Optional[Tuple[str, Dict[str, Any]]]:
    """Why ``model`` cannot be a new ped's model name, as a text key and its fields, or ``None``."""
    if not protocol.is_new_ped_model(model):
        return "ped.why.model", {}
    for prefix in GAME_PREFIXES:
        if model.startswith(prefix):
            return "ped.why.model-game", {"prefix": prefix, "suggestion": suggest_model("my_" + model[len(prefix):])}
    return None


def suggest_model(name: str) -> str:
    """A model name made from a character's name: lowercase letters, digits and underscores, starting with a letter,
    3 to 32 characters, never like a game ped's."""
    text = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    text = re.sub(r"^[^a-z]+", "", text)
    if any(text.startswith(prefix) for prefix in GAME_PREFIXES):
        text = "my_" + text
    if len(text) < 3:
        text = (text + "_ped") if text else "my_ped"
    return text[:32].rstrip("_") if len(text[:32].rstrip("_")) >= 3 else "my_ped"


#: The shared ragdoll bodies the user may choose instead of the template's (the protocol's names).
RAGDOLLS = ("fred", "wilma", "fred-large", "wilma-large")

#: The longest edge of a texture Durty Cloth Tool takes.
MAX_TEXTURE_EDGE = 4096


def texture_problem(width: int, height: int) -> Optional[str]:
    """What Durty Cloth Tool says about a texture of this size: ``too-large`` and ``not-multiple-of-four`` refuse the
    character, ``non-power-of-two`` is a warning; ``None`` for a good size."""
    if width > MAX_TEXTURE_EDGE or height > MAX_TEXTURE_EDGE:
        return "too-large"
    if width % 4 or height % 4:
        return "not-multiple-of-four"
    if width & (width - 1) or height & (height - 1):
        return "non-power-of-two"
    return None


# --------------------------------------------------------------------------------------------------
# The next step
# --------------------------------------------------------------------------------------------------

STAGES = ("character", "markers", "rig", "check", "send")


class Flow(NamedTuple):
    """What the panel knows about the character, for the next-step hint."""

    character: bool = False
    checks_ok: bool = False
    markers: int = 0
    marker_problems: bool = False
    connected: bool = False
    template: bool = False
    rigging: bool = False
    result: bool = False
    rigged: bool = False
    checked: bool = False
    sending: bool = False
    sent: bool = False


STEP_OPERATORS = {
    "ped.next.character": "dct_link.ped_use_selected",
    "ped.next.markers": "dct_link.ped_guide",
    "ped.next.template": "dct_link.ped_refresh_templates",
    "ped.next.rig": "dct_link.ped_rig",
    "ped.next.approve": "dct_link.ped_apply_rig",
    "ped.next.check": "dct_link.ped_run_checks",
    "ped.next.send": "dct_link.ped_send",
}


def next_step(flow: Flow) -> str:
    """The text key of what to do next."""
    if not flow.character:
        return "ped.next.character"
    if flow.sending:
        return "ped.next.sending"
    if flow.sent:
        return "ped.next.done"
    if flow.rigging:
        return "ped.next.rigging"
    if flow.result:
        return "ped.next.approve"
    if not flow.rigged:
        if not flow.checks_ok:
            return "ped.next.fix"
        if flow.markers < len(BODY_MARKERS):
            return "ped.next.markers"
        if flow.marker_problems:
            return "ped.next.marker-problems"
        if not flow.connected:
            return "ped.next.connect"
        if not flow.template:
            return "ped.next.template"
        return "ped.next.rig"
    if not flow.checked:
        return "ped.next.check"
    if not flow.connected:
        return "ped.next.connect"
    return "ped.next.send"


def stage_of(step: str) -> str:
    """The stage whose section holds the next step."""
    return {"ped.next.character": "character", "ped.next.fix": "character", "ped.next.markers": "markers",
            "ped.next.marker-problems": "markers", "ped.next.connect": "rig", "ped.next.template": "rig",
            "ped.next.rig": "rig", "ped.next.rigging": "rig", "ped.next.approve": "rig", "ped.next.check": "check",
            "ped.next.send": "send", "ped.next.sending": "send", "ped.next.done": "send"}.get(step, "character")


__all__ = [
    "BODY_MARKERS",
    "BonePlan",
    "Check",
    "Facts",
    "Finding",
    "Flow",
    "MarkerError",
    "MarkerProblem",
    "MarkerResult",
    "Part",
    "ReportLine",
    "RigInput",
    "armature_changes",
    "armature_plan",
    "auto_markers",
    "checks",
    "derive_markers",
    "follow_middle",
    "guess_role",
    "marker_problems",
    "markers_from_rig",
    "mirror_markers",
    "model_problem",
    "next_step",
    "pose_bases",
    "posed_world",
    "report_lines",
    "rig_input",
    "rig_kind",
    "strain",
    "suggest_model",
    "test_pose",
    "topology_hash",
    "vertex_groups",
    "weight_findings",
]
