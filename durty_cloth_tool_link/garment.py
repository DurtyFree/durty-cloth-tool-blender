# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2026 Schmid Software Solutions (https://schmid-software.de)
"""The garment fitting tools without Blender: slots and categories, the next-step hint, marker placement and its
plausibility, aligning the garment to the body's joints, body regions, the fit check, the problem colours, mesh moves,
seam welding, strip cutting, the local checks and pose presets.

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
#: The slots the tools add to, with Durty Cloth Tool's drawable type names: the components first, then the props.
#: Blender keeps the chosen slot by its place in this list, so new slots go at the end.
SLOTS = ("jbib", "accs", "lowr", "feet", "berd", "hand", "task", "p_head", "p_eyes", "p_ears", "p_lwrist", "p_rwrist")
#: The props among them: rigid pieces that hang from one bone (their anchor), never fitted to the body or weighted.
PROP_SLOTS = frozenset(slot for slot in SLOTS if slot.startswith("p_"))
#: The bone each prop slot hangs from in the game (its anchor): the head for hats, glasses and ear pieces, the
#: forearm's roll bone at the wrist for watches and bracelets.
ANCHOR_BONES = {"p_head": "SKEL_Head", "p_eyes": "SKEL_Head", "p_ears": "SKEL_Head",
                "p_lwrist": "RB_L_ForeArmRoll", "p_rwrist": "RB_R_ForeArmRoll"}
#: The garment types (Blender keeps the chosen type by its place in this list, so new types go at the end).
CATEGORIES = ("vest", "tshirt", "long_sleeve", "long_jacket", "pants", "shorts", "shoes", "hoodie", "open_jacket",
              "long_coat", "dress", "skirt", "sandals", "mask", "armour", "bag", "hat", "glasses", "ears", "watch",
              "bracelet")
#: The order the type picker lists them in, in groups (``None`` separates two groups).
CATEGORY_MENU = ("tshirt", "long_sleeve", "vest", "hoodie", "open_jacket", "long_jacket", "long_coat", "dress", None,
                 "pants", "shorts", "skirt", None, "shoes", "sandals", None, "mask", "armour", "bag", None,
                 "hat", "glasses", "ears", "watch", "bracelet")
SOURCE_POSES = ("a_pose", "t_pose", "custom")

#: The markers of a top.
UPPER_MARKERS = ("chest", "neck", "pelvis", "shoulder_l", "elbow_l", "wrist_l", "hip_l",
                 "shoulder_r", "elbow_r", "wrist_r", "hip_r")
#: The markers of the lower categories (legs); shoes need none.
LOWER_MARKERS = ("pelvis", "hip_l", "hip_r", "knee_l", "knee_r", "ankle_l", "ankle_r")
#: The markers of a bag: the torso its straps hang on, without the arms.
TORSO_MARKERS = ("chest", "neck", "pelvis", "shoulder_l", "shoulder_r", "hip_l", "hip_r")
#: The marker of a mask: the head's joint (where the head turns on the neck).
HEAD_MARKERS = ("head",)
#: Every marker name (new ones go at the end).
MARKERS = UPPER_MARKERS + ("knee_l", "ankle_l", "knee_r", "ankle_r", "head")
_LEFT = ("shoulder_l", "elbow_l", "wrist_l", "hip_l", "knee_l", "ankle_l")
MIRRORED = {name: name[:-1] + "r" for name in _LEFT}
#: The freemode bone each marker stands for (Align to Body moves the markers onto these joints).
MARKER_JOINTS = {
    "neck": "SKEL_Neck_1", "chest": "SKEL_Spine3", "pelvis": "SKEL_Pelvis",
    "shoulder_l": "SKEL_L_UpperArm", "elbow_l": "SKEL_L_Forearm", "wrist_l": "SKEL_L_Hand",
    "hip_l": "SKEL_L_Thigh", "knee_l": "SKEL_L_Calf", "ankle_l": "SKEL_L_Foot",
    "shoulder_r": "SKEL_R_UpperArm", "elbow_r": "SKEL_R_Forearm", "wrist_r": "SKEL_R_Hand",
    "hip_r": "SKEL_R_Thigh", "knee_r": "SKEL_R_Calf", "ankle_r": "SKEL_R_Foot", "head": "SKEL_Head",
}
#: The joints the add-on reads (from the hosted body, Durty Cloth Tool's skeleton or the body's shape).
JOINTS = ("SKEL_Pelvis", "SKEL_Spine0", "SKEL_Spine1", "SKEL_Spine2", "SKEL_Spine3", "SKEL_Neck_1", "SKEL_Head",
          "SKEL_L_Clavicle", "SKEL_L_UpperArm", "SKEL_L_Forearm", "SKEL_L_Hand",
          "SKEL_R_Clavicle", "SKEL_R_UpperArm", "SKEL_R_Forearm", "SKEL_R_Hand",
          "SKEL_L_Thigh", "SKEL_L_Calf", "SKEL_L_Foot", "SKEL_R_Thigh", "SKEL_R_Calf", "SKEL_R_Foot")

#: Body regions, in the order the panels list them (new ones go at the end).
REGIONS = ("shoulders", "upper_arms", "forearms", "cuffs", "chest", "back", "waist", "hips", "neck", "legs", "head")
OTHER = -1
_TOP_REGIONS = tuple(region for region in REGIONS if region not in ("legs", "head"))
_NO_SLEEVES = tuple(r for r in _TOP_REGIONS if r not in ("upper_arms", "forearms", "cuffs"))
_SHORT_SLEEVES = tuple(r for r in _TOP_REGIONS if r not in ("forearms", "cuffs"))
_LONG_REGIONS = _TOP_REGIONS + ("legs",)
_LOWER_REGIONS = ("waist", "hips", "legs")


class GarmentType(NamedTuple):
    """What a garment type sets up: the slots it may go into (the first is the usual one), how its markers are found
    (``family``: ``upper``, ``lower``, ``torso``, ``head``, ``none``, or ``anchor`` for a prop), its sleeves, the
    regions the tools offer and those Snug to Body works on, whether its front is open (never welded across the centre
    front), whether its thigh weights are bridged across the legs (a skirt or coat tails that hang between the legs
    must not split), whether it usually shows skin, the extra hint the panel shows (a text key), the largest dimension
    it has (metres, for the units of an import) and how a prop is snapped to its anchor."""

    slots: Tuple[str, ...]
    family: str
    sleeves: str = "none"
    regions: Tuple[str, ...] = ()
    snug: Tuple[str, ...] = ()
    open_front: bool = False
    bridge: bool = False
    skin: bool = False
    hint: str = ""
    size: Tuple[float, float] = (0.3, 1.8)
    snap: str = ""


_TOPS = ("jbib", "accs")
#: Every garment type. Nothing here is measured from the game: the slots, markers and regions are the add-on's own
#: choices, and the sizes are generic human proportions.
TYPES: Dict[str, GarmentType] = {
    "tshirt": GarmentType(_TOPS, "upper", "short", _SHORT_SLEEVES, _SHORT_SLEEVES),
    "long_sleeve": GarmentType(_TOPS, "upper", "long", _TOP_REGIONS, _TOP_REGIONS),
    "vest": GarmentType(_TOPS, "upper", "none", _NO_SLEEVES, _NO_SLEEVES),
    "hoodie": GarmentType(("jbib",), "upper", "long", _TOP_REGIONS, _TOP_REGIONS, hint="garment.hint.hood"),
    "open_jacket": GarmentType(("jbib",), "upper", "long", _TOP_REGIONS, _TOP_REGIONS, open_front=True,
                               hint="garment.hint.open-front"),
    "long_jacket": GarmentType(("jbib",), "upper", "long", _LONG_REGIONS, _TOP_REGIONS, size=(0.4, 2.2)),
    "long_coat": GarmentType(("jbib",), "upper", "long", _LONG_REGIONS, _TOP_REGIONS, bridge=True,
                             hint="garment.hint.coat", size=(0.5, 2.4)),
    "dress": GarmentType(("jbib",), "upper", "short", _LONG_REGIONS, _TOP_REGIONS, bridge=True,
                         hint="garment.hint.dress", size=(0.4, 2.4)),
    "pants": GarmentType(("lowr",), "lower", regions=_LOWER_REGIONS, snug=_LOWER_REGIONS, size=(0.25, 1.6)),
    "shorts": GarmentType(("lowr",), "lower", regions=_LOWER_REGIONS, snug=_LOWER_REGIONS, skin=True,
                          hint="garment.hint.bare-legs", size=(0.25, 1.6)),
    "skirt": GarmentType(("lowr",), "lower", regions=_LOWER_REGIONS, snug=("waist", "hips"), bridge=True, skin=True,
                         hint="garment.hint.bare-legs", size=(0.2, 1.6)),
    "shoes": GarmentType(("feet",), "none", regions=("legs",), snug=("legs",), size=(0.08, 0.5)),
    "sandals": GarmentType(("feet",), "none", regions=("legs",), snug=("legs",), skin=True,
                           hint="garment.hint.bare-feet", size=(0.08, 0.5)),
    "mask": GarmentType(("berd",), "head", regions=("head", "neck"), snug=("head", "neck"),
                        hint="garment.hint.avatar", size=(0.08, 0.6)),
    "armour": GarmentType(("task",), "upper", "none", _NO_SLEEVES, _NO_SLEEVES, size=(0.2, 1.2)),
    "bag": GarmentType(("hand",), "torso", regions=("shoulders", "chest", "back", "waist"), snug=("shoulders",),
                       hint="garment.hint.avatar", size=(0.15, 1.4)),
    "hat": GarmentType(("p_head",), "anchor", hint="garment.hint.prop", size=(0.1, 0.8), snap="hat"),
    "glasses": GarmentType(("p_eyes",), "anchor", hint="garment.hint.prop", size=(0.05, 0.4), snap="glasses"),
    "ears": GarmentType(("p_ears",), "anchor", hint="garment.hint.prop", size=(0.02, 0.19), snap="ears"),
    "watch": GarmentType(("p_lwrist", "p_rwrist"), "anchor", hint="garment.hint.prop", size=(0.03, 0.25),
                         snap="wrist"),
    "bracelet": GarmentType(("p_rwrist", "p_lwrist"), "anchor", hint="garment.hint.prop", size=(0.03, 0.25),
                            snap="wrist"),
}
#: How far the sleeves of a top reach.
SLEEVES = {name: kind.sleeves for name, kind in TYPES.items() if kind.family == "upper"}
LOWER = frozenset(name for name, kind in TYPES.items() if kind.family == "lower")

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
#: Thigh and shin lengths assumed when a garment does not reach the knee or the ankle (metres).
THIGH = 0.45
SHIN = 0.42


def garment_type(category: str) -> GarmentType:
    """The type's settings (a T-shirt's for a name the add-on does not know)."""
    return TYPES.get(category, TYPES["tshirt"])


def slots_for(category: str) -> Tuple[str, ...]:
    """The slots a garment of this type may go into, the usual one first."""
    return garment_type(category).slots


def categories_for(slot: str) -> Tuple[str, ...]:
    """The types that may go into a slot, in the order of :data:`CATEGORIES`."""
    return tuple(name for name in CATEGORIES if slot in TYPES[name].slots)


def is_prop(category: str) -> bool:
    """Whether the type is a prop (snapped to its anchor, never fitted to the body or weighted)."""
    return garment_type(category).family == "anchor"


def markers_for(category: str) -> Tuple[str, ...]:
    """The markers a garment of this type has (none for shoes and props)."""
    family = garment_type(category).family
    return {"upper": UPPER_MARKERS, "lower": LOWER_MARKERS, "torso": TORSO_MARKERS,
            "head": HEAD_MARKERS}.get(family, ())


def detects_markers(category: str) -> bool:
    """Whether Auto Markers can find the markers from the garment's shape (tops and legs); the other types take them
    from the avatar the garment was made on, or start from the body's joints."""
    return garment_type(category).family in ("upper", "lower")


def regions_for(category: str) -> Tuple[str, ...]:
    """The regions a garment of this type covers, in panel order."""
    return garment_type(category).regions


def snug_regions_for(category: str) -> Tuple[str, ...]:
    """The regions Snug to Body works on: never the coat tails or skirt of a top, which hang free of the legs."""
    return garment_type(category).snug


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
    aligned: bool = False
    #: Fit to Body on gta.clothing put the garment on the body (with weights).
    fitted: bool = False
    sculpting: bool = False
    checked: bool = False
    inside: int = 0
    prepared: bool = False
    materials: int = 1
    #: The garment has bone weights; the levels of detail take them over, so they come after the weights.
    weighted: bool = False
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
    #: A prop: snapped to its anchor (``aligned``) instead of fitted, never weighted, added without the skeleton.
    prop: bool = False
    #: The gender chosen under Setup (for the stage's status).
    gender: str = "male"


#: The operator each step's hint points at (the panel draws that button as the one to press next).
STEP_OPERATORS = {
    "garment.next.import": "dct_link.fit_import_garment",
    "garment.next.body": "dct_link.fit_add_body",
    "garment.next.markers": "dct_link.fit_auto_markers",
    "garment.next.align": "dct_link.fit_align",
    "garment.next.snap": "dct_link.fit_snap_anchor",
    "garment.next.fit": "dct_link.fit_service_fit",
    "garment.next.weights": "dct_link.fit_service_weights",
    "garment.next.check": "dct_link.fit_check",
    "garment.next.push": "dct_link.fit_push_out",
    "garment.next.prepare": "dct_link.fit_prepare",
    "garment.next.combine": "dct_link.fit_combine_materials",
    "garment.next.lods": "dct_link.fit_lods",
    "garment.next.validate": "dct_link.fit_validate",
    "garment.next.skeleton": "dct_link.fit_use_skeleton",
    "garment.next.add-skeleton": "dct_link.fit_add_to_dct",
    "garment.next.add": "dct_link.fit_add_to_dct",
}


def next_step(state: FlowState) -> str:
    """The text key of what to do next."""
    if state.sculpting:
        return "garment.next.sculpting"
    if not state.garment:
        return "garment.next.import"
    if not state.body:
        return "garment.next.body"
    if not state.prepared:
        if state.prop:
            return "garment.next.prepare" if state.aligned else "garment.next.snap"
        if state.markers < len(markers_for(state.category)):
            return "garment.next.markers"
        if markers_for(state.category) and not state.aligned:
            return "garment.next.align"
        if not state.fitted and not state.checked:
            return "garment.next.fit"
        if not state.checked:
            return "garment.next.check"
        if state.inside > 0:
            return "garment.next.push"
        return "garment.next.prepare"
    if state.materials > 1:
        return "garment.next.combine"
    if not state.weighted and not state.prop:
        if state.sollumz and state.connected and not state.skeleton:
            return "garment.next.skeleton"
        return "garment.next.weights"
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
    if not state.skeleton and not state.prop:
        return "garment.next.add-skeleton"  # the add puts the weighted garment on the skeleton itself
    return "garment.next.add"


#: The panel's stages, in order: each is a section that opens while it holds the next step.
STAGES = ("setup", "fit", "fix", "ready", "add")
_STAGE_OF_STEP = {
    "garment.next.import": "setup", "garment.next.body": "setup",
    "garment.next.markers": "fit", "garment.next.align": "fit", "garment.next.snap": "fit", "garment.next.fit": "fit",
    "garment.next.check": "fix", "garment.next.push": "fix", "garment.next.sculpting": "fix",
    "garment.next.prepare": "ready", "garment.next.combine": "ready", "garment.next.weights": "ready",
    "garment.next.lods": "ready", "garment.next.validate": "ready", "garment.next.validate-problems": "ready",
    "garment.next.skeleton": "ready",
}


def stage_of(state: FlowState) -> str:
    """The stage whose section holds the next step (Use Durty Cloth Tool Skeleton, before the weights, is Game
    Ready's; everything after Validate is Add to Project's)."""
    return _STAGE_OF_STEP.get(next_step(state), "add")


class StageStatus(NamedTuple):
    """A stage header's short status: its text key and fields (``None``: no status), the fields that are text keys
    themselves, and whether the work has moved past the stage (its tick)."""

    key: Optional[str]
    fields: Dict[str, Any]
    keys: Dict[str, str]
    done: bool


def stage_status(state: FlowState, stage: str) -> StageStatus:
    """What a stage's header says. A stage the work has moved past says only what it finished, never what was left
    out (Prepare Garment clears the fit check, so a done Fix never says "Not checked" beside its tick)."""
    current = stage_of(state)
    done = STAGES.index(stage) < STAGES.index(current) or (stage == "add" and state.added)

    def status(key: Optional[str], **fields: Any) -> StageStatus:
        return StageStatus(key, fields, {}, done)

    if stage == "setup":
        if not state.garment:
            return status("garment.status.no-garment")
        if not state.body:
            return status("garment.status.no-body")
        return StageStatus("garment.status.setup", {}, {"type": f"garment.category.{state.category}",
                                                         "gender": f"gender.{state.gender}"}, done)
    if stage == "fit":
        total = len(markers_for(state.category))
        if state.prop:
            return status("garment.status.snapped" if state.aligned else None if done else "garment.status.not-snapped")
        if state.fitted:
            return status("garment.status.fitted")
        if state.aligned and total:
            return status("garment.status.aligned")
        if total and not done:
            return status("garment.status.markers", count=min(state.markers, total), total=total)
        return status(None)
    if stage == "fix":
        if state.prop or (done and (not state.checked or state.inside)):
            return status(None)
        if not state.checked:
            return status("ped.status.not-checked")
        if state.inside:
            return status("garment.status.inside", count=state.inside)
        return status("ped.status.no-problems")
    if stage == "ready":
        if state.findings == "blocking":
            return status("garment.status.blocking")
        if state.validated or state.findings in ("clean", "warnings"):
            return status("garment.status.validated")
        return status(None if done else "garment.status.not-validated")
    if state.added:
        return status("garment.status.added")
    if state.adding:
        return status("garment.status.adding")
    return status("garment.status.not-added")


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


#: Vertices closer than this (metres) lie on top of each other: the two sides of a UV seam of a game mesh (its
#: vertices are split there on purpose, one per UV island), of an open seam, or a point where many such sides meet.
STACKED = 1e-5


def stacked_groups(positions: Any, tolerance: float = STACKED) -> np.ndarray:
    """The group of each vertex: the vertices that lie on top of it share one (a vertex alone has its own). Moves
    that spread along the mesh's edges (:func:`spread_offsets`, :func:`soft_mask`, relaxing) would part them, because
    the two sides of a split share no edge; :func:`keep_stacked` moves them together again."""
    points = as_points(positions)
    a, b, _d = close_pairs(points, tolerance)
    return components(len(points), np.column_stack([a, b]))


def keep_stacked(start: Any, moved: Any, groups: Any, fixed: Optional[Any] = None) -> np.ndarray:
    """``moved`` with the vertices of each group (:func:`stacked_groups` of ``start``) moved alike: by the mean of
    their moves, or not at all when one of them is ``fixed`` (pinned), so a split never tears into a gap."""
    start, moved = as_points(start), as_points(moved)
    groups = np.asarray(groups, dtype=np.int64)
    count = int(groups.max()) + 1 if len(groups) else 0
    sizes = np.bincount(groups, minlength=count)
    shared = sizes[groups] > 1
    if not shared.any():
        return moved.copy()
    moves = moved - start
    mean = np.zeros((count, 3))
    for axis in range(3):
        mean[:, axis] = np.bincount(groups, weights=moves[:, axis], minlength=count)
    mean /= np.maximum(sizes, 1)[:, None]
    if fixed is not None:
        held = np.bincount(groups, weights=np.asarray(fixed, dtype=np.float64), minlength=count) > 0
        mean[held] = 0.0
    result = moved.copy()
    result[shared] = start[shared] + mean[groups[shared]]
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


def _smoothstep(values: Any) -> np.ndarray:
    t = np.clip(np.asarray(values, dtype=np.float64), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


#: How many candidate pairs one block of the neighbour search compares at most (bounds its memory).
PAIR_BLOCK = 1_000_000


def grid_pairs(query: Any, target: Any, distance: float,
               block: int = PAIR_BLOCK) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Every pair of a ``query`` point and a ``target`` point at most ``distance`` apart: ``(query index, target
    index, distance)``. A grid of ``distance`` cells sorted by cell, searched with ``np.searchsorted`` in blocks, so
    it stays fast and bounded in memory on garments of 100,000 vertices."""
    query, target = as_points(query), as_points(target)
    empty = (np.zeros(0, np.int64), np.zeros(0, np.int64), np.zeros(0))
    if distance <= 0 or not len(query) or not len(target):
        return empty
    origin = np.minimum(query.min(axis=0), target.min(axis=0))
    query_cells = np.floor((query - origin) / distance).astype(np.int64) + 1
    target_cells = np.floor((target - origin) / distance).astype(np.int64) + 1
    dims = np.maximum(query_cells.max(axis=0), target_cells.max(axis=0)) + 2

    def keys(cells: np.ndarray) -> np.ndarray:
        return (cells[:, 0] * dims[1] + cells[:, 1]) * dims[2] + cells[:, 2]

    # Queries in cell order too: every shifted search then runs over sorted keys, which keeps it fast.
    query_order = np.argsort(keys(query_cells), kind="stable")
    query_keys = keys(query_cells)[query_order]
    order = np.argsort(keys(target_cells), kind="stable")
    sorted_keys = keys(target_cells)[order]
    limit = distance * distance
    found_q, found_t, found_d = [], [], []
    for da in (-1, 0, 1):
        for db in (-1, 0, 1):
            for dc in (-1, 0, 1):
                shifted = query_keys + (da * dims[1] + db) * dims[2] + dc
                low = np.searchsorted(sorted_keys, shifted, "left")
                counts = np.searchsorted(sorted_keys, shifted, "right") - low
                totals = np.cumsum(counts)
                start, count = 0, len(query)
                while start < count:
                    base = totals[start - 1] if start else 0
                    end = min(count, max(start + 1, int(np.searchsorted(totals, base + block, "right"))))
                    chunk = counts[start:end]
                    total = int(chunk.sum())
                    if total:
                        q = query_order[np.repeat(np.arange(start, end), chunk)]
                        steps = np.arange(total) - np.repeat(np.cumsum(chunk) - chunk, chunk)
                        t = order[np.repeat(low[start:end], chunk) + steps]
                        diff = query[q] - target[t]
                        squared = np.einsum("ij,ij->i", diff, diff)
                        near = squared <= limit
                        found_q.append(q[near])
                        found_t.append(t[near])
                        found_d.append(np.sqrt(squared[near]))
                    start = end
    if not found_q:
        return empty
    return np.concatenate(found_q), np.concatenate(found_t), np.concatenate(found_d)


def close_pairs(positions: Any, distance: float, indices: Optional[Any] = None) -> Tuple[np.ndarray, np.ndarray,
                                                                                          np.ndarray]:
    """Pairs of separate vertices (of ``indices``, all by default) at most ``distance`` apart, each pair once with
    the lower vertex first: ``(first, second, distance)``."""
    points = as_points(positions)
    chosen = np.arange(len(points)) if indices is None else np.asarray(indices, dtype=np.int64).reshape(-1)
    if len(chosen) < 2:
        return np.zeros(0, np.int64), np.zeros(0, np.int64), np.zeros(0)
    q, t, d = grid_pairs(points[chosen], points[chosen], distance)
    a, b = chosen[q], chosen[t]
    keep = a < b
    return a[keep], b[keep], d[keep]


def boundary_chains(edges: Any, count: int, positions: Any) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Walks the open edges (``edges``: the boundary edges) into chains. Returns each vertex's chain (-1 off the
    boundary), its distance along the chain (metres) and each chain's length (the full loop for a closed chain, a
    negative length for an open one)."""
    points = as_points(positions)
    edges = np.asarray(edges, dtype=np.int64).reshape(-1, 2)
    chain = np.full(count, -1, dtype=np.int64)
    arc = np.zeros(count)
    lengths: List[float] = []
    if not len(edges):
        return chain, arc, np.zeros(0)
    order, starts = neighbour_lists(count, edges)
    degree = np.diff(starts)
    candidates = list(np.nonzero(degree == 1)[0]) + list(np.nonzero(degree >= 2)[0])
    for start in candidates:
        start = int(start)
        if chain[start] >= 0:
            continue
        index = len(lengths)
        previous, current, travelled = -1, start, 0.0
        while True:
            chain[current] = index
            arc[current] = travelled
            following = -1
            for neighbour in order[starts[current]:starts[current + 1]]:
                neighbour = int(neighbour)
                if neighbour != previous and chain[neighbour] < 0:
                    following = neighbour
                    break
            if following < 0:
                break
            travelled += float(np.linalg.norm(points[following] - points[current]))
            previous, current = current, following
        closes = current != start and start in set(int(n) for n in order[starts[current]:starts[current + 1]])
        lengths.append(travelled + float(np.linalg.norm(points[start] - points[current])) if closes else -travelled)
    return chain, arc, np.asarray(lengths)


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


def markers_json(markers: Mapping[str, Any]) -> str:
    """The markers as Align to Body left them, to tell later whether one was moved."""
    return json.dumps({name: [round(float(v), 5) for v in _vec(value)] for name, value in sorted(markers.items())})


def markers_moved(markers: Mapping[str, Any], aligned: str, tolerance: float = 0.0005) -> bool:
    """Whether a marker was moved, added or removed since Align to Body (``aligned``: :func:`markers_json`)."""
    try:
        before = json.loads(aligned) if aligned else None
    except ValueError:
        before = None
    if not isinstance(before, dict):
        return False  # aligned before this was recorded: nothing to compare with
    if set(before) != set(markers):
        return True
    return any(float(np.linalg.norm(_vec(markers[name]) - _vec(before[name]))) > tolerance for name in markers)


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


#: Notes Auto Markers leaves for the panel when it had to guess (text keys ``garment.marker-note.<code>``).
MARKER_NOTES = ("arms-estimated", "hood", "skirt", "legs-estimated")


class MarkerResult(NamedTuple):
    markers: Dict[str, Vector]
    notes: Tuple[str, ...]


def auto_markers(positions: Any, category: str, source_pose: str = "a_pose",
                 edges: Optional[np.ndarray] = None) -> Dict[str, Vector]:
    """Joint markers for a garment from cross-sections of its mesh. Raises :class:`MarkerError` when the mesh
    does not look like the category."""
    return place_markers(positions, category, source_pose, edges).markers


def place_markers(positions: Any, category: str, source_pose: str = "a_pose",
                  edges: Optional[np.ndarray] = None) -> MarkerResult:
    """:func:`auto_markers` with the notes on what was guessed rather than found (``MARKER_NOTES``)."""
    points = as_points(positions)
    if not detects_markers(category):
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


def _side_extents(points: np.ndarray, cx: float, z: float, half: float, gap: float) -> Tuple[float, float]:
    """How far the part of the garment around the centre reaches to the left and to the right at height ``z``
    (sleeves that hang apart from it are left out)."""
    band = points[np.abs(points[:, 2] - z) <= half]
    dx = band[:, 0] - cx
    extents = []
    for values in (dx[dx >= 0], -dx[dx < 0]):
        # A slice that misses the torso (coarse rings) would measure a sleeve: the torso starts at the centre.
        extents.append(_gap_extent(values, gap) if values.size and values.min() <= gap else 0.0)
    return extents[0], extents[1]


def _neck(points: np.ndarray, cx: float, torso: float, gap: float) -> Tuple[np.ndarray, bool]:
    """The centre of the neck opening, and whether a hood sits on it. Going up the centre of the garment, the neck is
    where it is narrowest above the shoulders; a hood (or the body's head) widens again above it."""
    low, high = points[:, 2].min(), points[:, 2].max()
    levels = np.arange(high, low, -0.01)
    widths = []
    for level in levels:
        left, right = _side_extents(points, cx, level, 0.006, gap)
        widths.append(max(left, right) if left or right else 0.0)
    widths = np.asarray(widths)
    narrow = (widths > 0) & (widths < 0.8 * torso)
    run = 0
    while run < len(levels) and (narrow[run] or widths[run] == 0):
        run += 1
    top = float(points[:, 2].max())
    shoulder_line = float(levels[run - 1]) if run else top
    hood = top - shoulder_line > 0.15
    if hood:
        # The narrowest level in the lower part of the narrow run is where the hood (or head) meets the garment.
        window = [i for i in range(run) if levels[i] <= shoulder_line + 0.18 and widths[i] > 0]
        choice = min(window, key=lambda i: widths[i]) if window else run - 1
        level = float(levels[choice])
        ring = points[np.abs(points[:, 2] - level) <= 0.012]
        ring = ring[np.abs(ring[:, 0] - cx) <= widths[choice] + 0.01]
        return np.array([cx, _y_centre(ring, float(points[:, 1].mean())), level - 0.01]), True
    near_centre = np.abs(points[:, 0] - cx) < 0.45 * torso
    if not np.any(near_centre):
        raise MarkerError("not-a-top")
    z = points[:, 2]
    highest = float(z[near_centre].max())
    ring = points[near_centre & (z > highest - 0.03)]
    return np.array([cx, float(ring[:, 1].mean()), float(ring[:, 2].mean()) - 0.01]), False


def _upper_markers(points: np.ndarray, category: str, source_pose: str, gap: float) -> MarkerResult:
    low, high = points.min(axis=0), points.max(axis=0)
    height = high[2] - low[2]
    z = points[:, 2]
    notes: List[str] = []

    # A first centre and torso width from the lower part, then the neck, then both again just below the armholes,
    # where neither a flared skirt nor a hood nor a one-sided strap can pull them.
    band = (z >= low[2] + 0.12 * height) & (z <= low[2] + 0.5 * height)
    cx = float(np.median(points[band, 0])) if np.any(band) else float((low[0] + high[0]) / 2)
    widths = []
    for level in np.linspace(low[2] + 0.12 * height, low[2] + 0.5 * height, 9):
        left, right = _side_extents(points, cx, level, max(0.01, height / 60), gap)
        widths += [w for w in (left, right) if w > 0]
    if not widths:
        raise MarkerError("not-a-top")
    torso = float(np.median(widths))
    if torso < 0.05:
        raise MarkerError("not-a-top")
    neck, hood = _neck(points, cx, torso, gap)
    if hood:
        notes.append("hood")
    upper = np.arange(neck[2] - 0.18, max(low[2] + 0.01, neck[2] - 0.42), -0.02)
    sides, centres = [], []
    for level in upper:
        left, right = _side_extents(points, cx, level, 0.01, gap)
        if left > 0.04 and right > 0.04:
            sides += [left, right]
            centres.append(cx + (left - right) / 2)
    # Short sleeves that hang against the torso widen these sections: the re-measure counts only when it is narrower
    # than the first estimate (it is there for a flared hem, a hood or a strap that widen the lower part).
    if len(sides) >= 4 and float(np.median(sides)) <= torso * 1.02:
        torso = float(np.median(sides))
        cx = float(np.median(centres))
    neck[0] = cx
    dx = points[:, 0] - cx
    lateral = np.abs(dx)

    # Shoulders: where the top's upper outline reaches the torso's width.
    sleeves = SLEEVES.get(category, "short")
    result: Dict[str, Vector] = {}
    shoulders: Dict[float, np.ndarray] = {}
    for side in (1.0, -1.0):
        outer = (np.sign(dx) == side) & (np.abs(lateral - torso) < max(0.03, gap)) & (z < neck[2] + 0.02)
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
    levels = np.linspace(low[2], min(high[2], neck[2] + 0.05), 61)
    half = (levels[1] - levels[0]) / 2 + 1e-9
    for level in levels:
        in_band = np.abs(z - level) <= half
        for side in (1.0, -1.0):
            selected = in_band & (np.sign(dx) == side)
            torso_extent[selected] = _gap_extent(lateral[selected], gap)
    apart = (lateral > torso_extent + 1e-9) & (z < neck[2] + 0.05)
    wide = (lateral > 1.35 * torso + 0.01) & (z > low[2] + 0.45 * height) & (z < neck[2] + 0.05)
    sleeve_mask = apart | wide

    arms: Dict[float, Optional[Tuple[np.ndarray, np.ndarray, np.ndarray]]] = {}
    for side in (1.0, -1.0):
        shoulder = shoulders[side]
        own = sleeve_mask & (np.sign(dx) == side)
        enough = int(own.sum()) >= max(8, int(0.002 * len(points)))
        direction = _pose_direction(side, source_pose)
        if sleeves != "none" and enough:
            sleeve = points[own]
            # A hem that flares out at the torso's side is no sleeve: the cuff is looked for beyond the torso's width.
            beyond = sleeve[np.abs(sleeve[:, 0] - cx) > torso + 0.01]
            if len(beyond) >= max(8, int(0.002 * len(points))):
                sleeve = beyond
            distance = np.linalg.norm(sleeve - shoulder, axis=1)
            cuff = sleeve[distance >= distance.max() - 0.02]
            cuff_centre = cuff.mean(axis=0)
            candidate = _unit(cuff_centre - shoulder)
            down = math.degrees(math.atan2(-candidate[2], abs(candidate[0]) + 1e-12))
            if candidate[0] * side > 0 and -15.0 <= down <= 85.0:
                direction = candidate
            if sleeves == "long" and float(np.linalg.norm(cuff_centre - shoulder)) > 0.3:
                wrist = cuff_centre - direction * 0.02
                elbow = shoulder + 0.53 * (wrist - shoulder)
                arms[side] = (shoulder, elbow, wrist)
                continue
        elif sleeves != "none":
            arms[side] = None
            continue
        elbow = shoulder + direction * UPPER_ARM_PER_SPAN * span
        wrist = elbow + direction * FOREARM_PER_SPAN * span
        arms[side] = (shoulder, elbow, wrist)
    if arms.get(1.0) is None and arms.get(-1.0) is None:
        # Cap sleeves or sleeves too short to see: the arms follow the source pose from the shoulders.
        notes.append("arms-estimated")
        for side in (1.0, -1.0):
            direction = _pose_direction(side, source_pose)
            elbow = shoulders[side] + direction * UPPER_ARM_PER_SPAN * span
            arms[side] = (shoulders[side], elbow, elbow + direction * FOREARM_PER_SPAN * span)
    for side, other in ((1.0, -1.0), (-1.0, 1.0)):
        if arms.get(side) is None:  # a sleeve was not found on one side: mirror the other one
            arms[side] = tuple(np.array([2 * cx - p[0], p[1], p[2]]) for p in arms[other])  # type: ignore[union-attr]

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
    return MarkerResult(result, tuple(notes))


def _lower_markers(points: np.ndarray, gap: float) -> MarkerResult:
    low, high = points.min(axis=0), points.max(axis=0)
    z = points[:, 2]
    notes: List[str] = []
    top_band = points[z > high[2] - 0.04]
    cx = float((top_band[:, 0].min() + top_band[:, 0].max()) / 2) if len(top_band) else float((low[0] + high[0]) / 2)
    dx = points[:, 0] - cx
    top = float(high[2])
    middle = np.abs(dx) < 0.015
    crotch = float(z[middle].min()) if np.any(middle) else top - 0.25
    skirt = crotch <= low[2] + 0.03  # the centre reaches the hem: no inseam
    if skirt:
        notes.append("skirt")
    if skirt or crotch >= top - 0.08:
        crotch = top - 0.2  # no inseam found: assume an ordinary rise
    # Bib trousers and overalls reach far above the waist; the pelvis sits a rise above the crotch.
    pelvis_z = min(top - 0.05, crotch + 0.13)
    top_y = _slice(points, min(top, pelvis_z + 0.05), 0.02)
    pelvis_y = _y_centre(top_y, float(points[:, 1].mean()))
    legs = points[np.abs(z - (crotch - 0.08)) <= 0.02]
    offsets = []
    for side in (1.0, -1.0):
        own = legs[np.sign(legs[:, 0] - cx) == side]
        offsets.append(abs(float(own[:, 0].mean()) - cx) if len(own) and not skirt else 0.09)
    offset = 0.9 * float(np.mean(offsets))
    if not 0.03 <= offset <= 0.3:
        raise MarkerError("not-legs")
    hip_z = crotch + 0.7 * (pelvis_z - crotch)
    result: Dict[str, Vector] = {"pelvis": (cx, pelvis_y, pelvis_z)}
    estimated = skirt
    for side, suffix in ((1.0, "l"), (-1.0, "r")):
        hip = np.array([cx + side * offset, pelvis_y, hip_z])
        result[f"hip_{suffix}"] = _tuple(hip)
        own = points[(np.sign(dx) == side) & (z < crotch - 0.05)] if not skirt else points[:0]
        bottom = float(own[:, 2].min()) if len(own) else hip_z
        if len(own) and hip_z - bottom > THIGH + 0.25:  # the leg reaches the ankle
            cuff = own[own[:, 2] < bottom + 0.02]
            ankle = cuff.mean(axis=0)
            knee = hip + (THIGH / (THIGH + SHIN)) * (ankle - hip)
        else:
            estimated = True
            knee = hip + np.array([0.0, 0.0, -THIGH])
            ankle = knee + np.array([0.0, 0.0, -SHIN])
        result[f"knee_{suffix}"] = _tuple(knee)
        result[f"ankle_{suffix}"] = _tuple(ankle)
    if estimated and not skirt:
        notes.append("legs-estimated")
    return MarkerResult(result, tuple(notes))


def _tuple(vector: np.ndarray) -> Vector:
    return (float(vector[0]), float(vector[1]), float(vector[2]))


#: What makes a set of markers implausible (text keys ``garment.marker-problem.<code>``).
MARKER_PROBLEMS = ("order", "span", "symmetry", "arms", "legs")


def marker_problems(markers: Mapping[str, Any], category: str) -> List[str]:
    """What looks wrong with the markers before anything is fitted to them: the joints out of order from top to
    bottom, a shoulder span no person has, the two sides not mirror images of each other, arm or leg segments of
    impossible lengths or bent back on themselves. Empty when they look plausible."""
    found = {name: _vec(value) for name, value in markers.items() if name in MARKERS}
    problems: List[str] = []
    expected = markers_for(category)
    family = garment_type(category).family
    if not expected or family == "head" or any(name not in found for name in expected):
        return problems

    def length(a: str, b: str) -> float:
        return float(np.linalg.norm(found[a] - found[b]))

    if category in LOWER:
        if not found["pelvis"][2] > max(found["hip_l"][2], found["hip_r"][2]) - 0.02:
            problems.append("order")
        for side in ("l", "r"):
            thigh, shin = length(f"hip_{side}", f"knee_{side}"), length(f"knee_{side}", f"ankle_{side}")
            if not (0.25 <= thigh <= 0.65 and 0.25 <= shin <= 0.65):
                problems.append("legs")
                break
    else:
        neck, chest, pelvis = found["neck"][2], found["chest"][2], found["pelvis"][2]
        shoulders = (found["shoulder_l"][2] + found["shoulder_r"][2]) / 2
        if not (neck > shoulders > chest > pelvis) or neck - pelvis > 1.0:
            problems.append("order")
        span = abs(found["shoulder_l"][0] - found["shoulder_r"][0])
        if not 0.22 <= span <= 0.6:
            problems.append("span")
        for side in ("l", "r") if family == "upper" else ():
            upper, fore = length(f"shoulder_{side}", f"elbow_{side}"), length(f"elbow_{side}", f"wrist_{side}")
            bend = _vec(found[f"wrist_{side}"]) - found[f"elbow_{side}"]
            back = found[f"shoulder_{side}"] - found[f"elbow_{side}"]
            angle = math.degrees(math.acos(float(np.clip(_unit(bend) @ _unit(back), -1.0, 1.0))))
            if not (0.12 <= upper <= 0.5 and 0.1 <= fore <= 0.45) or angle < 100.0:
                problems.append("arms")
                break
    cx = centre_x(found)
    for left, right in MIRRORED.items():
        if left in found and right in found and left in expected:
            mirrored = np.array([2 * cx - found[left][0], found[left][1], found[left][2]])
            if float(np.linalg.norm(mirrored - found[right])) > 0.06:
                problems.append("symmetry")
                break
    return problems


#: The lines the stick figure draws between markers.
STICK_FIGURE = (("neck", "chest"), ("chest", "pelvis"), ("neck", "shoulder_l"), ("shoulder_l", "elbow_l"),
                ("elbow_l", "wrist_l"), ("neck", "shoulder_r"), ("shoulder_r", "elbow_r"), ("elbow_r", "wrist_r"),
                ("pelvis", "hip_l"), ("hip_l", "knee_l"), ("knee_l", "ankle_l"), ("pelvis", "hip_r"),
                ("hip_r", "knee_r"), ("knee_r", "ankle_r"), ("neck", "head"))


def stick_figure(markers: Mapping[str, Any]) -> List[Tuple[Vector, Vector]]:
    """The line segments between the markers that are there."""
    return [(_tuple(_vec(markers[a])), _tuple(_vec(markers[b]))) for a, b in STICK_FIGURE
            if a in markers and b in markers]


# --------------------------------------------------------------------------------------------------
# Joints and Align to Body
# --------------------------------------------------------------------------------------------------


def parse_joints(text: str, gender: str) -> Optional[Dict[str, Vector]]:
    """The joints of one gender from a hosted body's joints file (``{"schema": 1, "space": "ped", "units": "m",
    "<gender>": {bone: [x, y, z]}}``), or ``None`` for anything else. Bones the add-on does not read are left out;
    a coordinate outside 3 m refuses the whole file."""
    try:
        data = json.loads(text)
    except (TypeError, ValueError):
        return None
    if not isinstance(data, dict) or data.get("schema") != 1 or data.get("space") != "ped" or data.get("units") != "m":
        return None
    raw = data.get(gender)
    if not isinstance(raw, dict):
        return None
    joints: Dict[str, Vector] = {}
    for name in JOINTS:
        value = raw.get(name)
        if value is None:
            continue
        if not isinstance(value, list) or len(value) != 3 or not all(
                isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) and abs(v) <= 3.0
                for v in value):
            return None
        joints[name] = (float(value[0]), float(value[1]), float(value[2]))
    return joints if {"SKEL_Pelvis", "SKEL_Neck_1", "SKEL_L_UpperArm", "SKEL_R_UpperArm"} <= set(joints) else None


def joints_json(joints: Mapping[str, Any], gender: str) -> str:
    """Joints written as :func:`parse_joints` reads them (kept on the body object)."""
    return json.dumps({"schema": 1, "space": "ped", "units": "m",
                       gender: {name: [round(float(v), 5) for v in _vec(joints[name])] for name in JOINTS
                                if name in joints}}, separators=(",", ":"))


def complete_joints(joints: Mapping[str, Any]) -> Dict[str, np.ndarray]:
    """The joints with what is missing filled in from the others: the spine between the pelvis and the chest, the
    clavicles between the neck and the shoulders, the head above the neck."""
    found = {name: _vec(value) for name, value in joints.items()}
    pelvis, neck = found.get("SKEL_Pelvis"), found.get("SKEL_Neck_1")
    if pelvis is not None and neck is not None:
        chest = found.get("SKEL_Spine3", pelvis + 0.75 * (neck - pelvis))
        found.setdefault("SKEL_Spine3", chest)
        for index, share in ((0, 0.2), (1, 0.45), (2, 0.7)):
            found.setdefault(f"SKEL_Spine{index}", pelvis + share * (chest - pelvis))
        found.setdefault("SKEL_Head", neck + np.array([0.0, 0.0, 0.1]))
    for side in ("L", "R"):
        shoulder = found.get(f"SKEL_{side}_UpperArm")
        if shoulder is not None and neck is not None:
            found.setdefault(f"SKEL_{side}_Clavicle", neck + 0.3 * (shoulder - neck) - np.array([0.0, 0.0, 0.04]))
    return found


def joints_from_markers(markers: Mapping[str, Any]) -> Dict[str, Vector]:
    """Joints named after the freemode bones from markers (what Align to Body falls back to: the body's own shape)."""
    return {MARKER_JOINTS[name]: _tuple(_vec(value)) for name, value in markers.items() if name in MARKER_JOINTS}


def estimate_body_joints(positions: Any, edges: Optional[np.ndarray] = None) -> Dict[str, Vector]:
    """Joints read from the shape of a body mesh in the game's pose, when neither the hosted body nor Durty Cloth Tool
    gives them: the markers a long-sleeved top would get (the head counts as a hood), and the legs below the pelvis.
    An estimate: Align to Body says so."""
    points = as_points(positions)
    upper = _upper_markers(points, "long_sleeve", "a_pose", 0.025).markers
    below = points[points[:, 2] < upper["pelvis"][2] + 0.12]
    joints = joints_from_markers(upper)
    if len(below) >= 30:
        try:
            lower = _lower_markers(below, 0.025).markers
        except MarkerError:
            lower = {}
        for name in ("hip_l", "hip_r", "knee_l", "knee_r", "ankle_l", "ankle_r"):
            if name in lower:
                joints[MARKER_JOINTS[name]] = lower[name]
        if "ankle_l" in lower:  # the soles are the bottom of the body; the ankle joint sits above them
            for side in ("L", "R"):
                x, y, z = joints[f"SKEL_{side}_Foot"]
                joints[f"SKEL_{side}_Foot"] = (x, y, z + 0.08)
    return joints


#: How much each marker pulls when the garment is fitted to the joints: the neck and shoulders (or pelvis and hips)
#: are what a garment hangs from; markers placed from proportions count less.
ALIGN_WEIGHTS = {
    "upper": {"neck": 1.0, "shoulder_l": 1.0, "shoulder_r": 1.0, "pelvis": 0.3, "hip_l": 0.15, "hip_r": 0.15},
    "lower": {"pelvis": 1.0, "hip_l": 1.0, "hip_r": 1.0, "knee_l": 0.4, "knee_r": 0.4, "ankle_l": 0.2,
              "ankle_r": 0.2},
}
#: The most Align to Body scales (either way) and turns the garment before it says the markers look wrong. Markers
#: sit on the garment's surface, not on the joints inside the body, so a larger scale means misplaced markers.
ALIGN_MAX_SCALE = 1.15
ALIGN_MAX_TURN = 20.0
#: An arm or leg closer than this to its target direction (degrees) is left as it is.
LIMB_TOLERANCE = 2.0


class Similarity(NamedTuple):
    scale: float
    rotation: np.ndarray  # 3x3
    translation: np.ndarray

    def apply(self, points: Any) -> np.ndarray:
        return self.scale * as_points(points) @ self.rotation.T + self.translation

    @property
    def turn(self) -> float:
        """The rotation's angle, in degrees."""
        return math.degrees(math.acos(float(np.clip((np.trace(self.rotation) - 1.0) / 2.0, -1.0, 1.0))))


def similarity_fit(source: Any, target: Any, weights: Any) -> Similarity:
    """The scale, rotation and translation that best bring ``source`` points onto ``target`` points (weighted least
    squares, Umeyama's method)."""
    src, dst = as_points(source), as_points(target)
    w = np.asarray(weights, dtype=np.float64)
    w = w / w.sum()
    mean_src, mean_dst = w @ src, w @ dst
    a, b = src - mean_src, dst - mean_dst
    covariance = (b * w[:, None]).T @ a
    u, singular, vt = np.linalg.svd(covariance)
    d = np.diag([1.0, 1.0, float(np.sign(np.linalg.det(u @ vt)) or 1.0)])
    rotation = u @ d @ vt
    variance = float((w * np.einsum("ij,ij->i", a, a)).sum())
    scale = float(np.trace(np.diag(singular) @ d) / variance) if variance > 1e-12 else 1.0
    return Similarity(scale, rotation, mean_dst - scale * rotation @ mean_src)


class AlignPlan(NamedTuple):
    """What Align to Body does: the garment as a whole onto the joints, then each arm (or leg) turned about its
    shoulder (or hip) onto the body's. ``limbs`` holds ``(side, kind, pivot, axis, degrees)``."""

    similarity: Similarity
    limbs: Tuple[Tuple[str, str, Vector, Vector, float], ...]
    residual: float  # millimetres, the weighted mean distance of the markers from their joints after the fit


def align_plan(markers: Mapping[str, Any], joints: Mapping[str, Any], category: str,
               scale: bool = True, reference: Optional[Mapping[str, Any]] = None) -> AlignPlan:
    """How to align a garment with these markers to a body with these joints. Raises :class:`MarkerError`
    (``align-markers``) when the fit would scale or turn the garment more than a garment ever needs, which means
    the markers are not on the garment's joints.

    Markers sit on the garment's surface, joints inside the body, so the size is measured against ``reference``: the
    markers Auto Markers gives the body itself (surface against surface). Without it the joints' own span is used,
    which reads every garment as too wide and shrinks it.

    A mask has one marker, the head's joint: it is moved onto the body's head joint as it is, without turning or
    scaling it."""
    family = garment_type(category).family
    if family == "head":
        return _head_plan(markers, joints)
    kind = "lower" if family == "lower" else "upper"
    weights = ALIGN_WEIGHTS[kind]
    full = complete_joints(joints)
    names = [n for n in weights if n in markers and MARKER_JOINTS[n] in full]
    if len(names) < 3:
        raise MarkerError("align-markers")
    source = np.array([_vec(markers[n]) for n in names])
    target = np.array([full[MARKER_JOINTS[n]] for n in names])
    fit = similarity_fit(source, target, [weights[n] for n in names])
    size = fit.scale
    if reference:
        alike = [n for n in names if n in reference]
        if len(alike) >= 3:
            size = similarity_fit(np.array([_vec(markers[n]) for n in alike]),
                                  np.array([_vec(reference[n]) for n in alike]), [weights[n] for n in alike]).scale
    if not (1.0 / ALIGN_MAX_SCALE <= size <= ALIGN_MAX_SCALE) or fit.turn > ALIGN_MAX_TURN:
        raise MarkerError("align-markers")
    w = np.array([weights[n] for n in names]) / sum(weights[n] for n in names)
    chosen = size if scale else 1.0  # without scaling: the best rotation and translation alone
    fit = Similarity(chosen, fit.rotation, w @ target - chosen * fit.rotation @ (w @ source))
    moved = fit.apply(source)
    w = np.array([weights[n] for n in names])
    residual = float((w * np.linalg.norm(moved - target, axis=1)).sum() / w.sum() * 1000.0)
    limbs = []
    chains = (("shoulder", "wrist", "elbow", "UpperArm", "Hand", "Forearm", "arm"),
              ("hip", "ankle", "knee", "Thigh", "Foot", "Calf", "leg"))
    for root, end, middle, root_joint, end_joint, middle_joint, limb in chains:
        if (limb == "arm") != (kind == "upper"):
            continue
        for side, bone_side in (("l", "L"), ("r", "R")):
            start_marker = markers.get(f"{root}_{side}")
            end_marker = markers.get(f"{end}_{side}", markers.get(f"{middle}_{side}"))
            start_joint = full.get(f"SKEL_{bone_side}_{root_joint}")
            end_target = full.get(f"SKEL_{bone_side}_{end_joint}", full.get(f"SKEL_{bone_side}_{middle_joint}"))
            if start_marker is None or end_marker is None or start_joint is None or end_target is None:
                continue
            pivot, tip = fit.apply([start_marker, end_marker])
            current, wanted = _unit(tip - pivot), _unit(end_target - start_joint)
            axis = np.cross(current, wanted)
            angle = math.degrees(math.atan2(float(np.linalg.norm(axis)), float(current @ wanted)))
            if angle < LIMB_TOLERANCE or float(np.linalg.norm(axis)) < 1e-9:
                continue
            limbs.append((side, limb, _tuple(pivot), _tuple(_unit(axis)), angle))
    return AlignPlan(fit, tuple(limbs), residual)


#: The furthest Align to Body moves a mask onto the body's head (metres): further means the marker is not on the head.
HEAD_ALIGN_LIMIT = 0.5


def _head_plan(markers: Mapping[str, Any], joints: Mapping[str, Any]) -> AlignPlan:
    full = complete_joints(joints)
    if "head" not in markers or "SKEL_Head" not in full:
        raise MarkerError("align-markers")
    shift = full["SKEL_Head"] - _vec(markers["head"])
    if float(np.linalg.norm(shift)) > HEAD_ALIGN_LIMIT:
        raise MarkerError("align-markers")
    return AlignPlan(Similarity(1.0, np.eye(3), shift), (), 0.0)


def body_markers(joints: Mapping[str, Any], names: Iterable[str]) -> Dict[str, Vector]:
    """Markers on the body's own joints (``names`` of :data:`MARKER_JOINTS`): where Auto Markers starts a type it cannot
    read from the garment's shape when the avatar the garment was made on is not known."""
    full = complete_joints(joints)
    return {name: _tuple(full[MARKER_JOINTS[name]]) for name in names
            if name in MARKER_JOINTS and MARKER_JOINTS[name] in full}


def limb_weights(points: Any, markers: Mapping[str, Any], side: str, limb: str) -> np.ndarray:
    """How much each point follows a turned arm or leg (0 to 1). A smooth function of the position only, so the two
    sides of an open seam (which lie on top of each other) always move together and the seam cannot tear: points
    closer to the limb than to the torso, from just before the shoulder (or hip) on."""
    pts = as_points(points)
    if limb == "arm":
        root, middle, end = (_vec(markers[f"{n}_{side}"]) for n in ("shoulder", "elbow", "wrist"))
        cx = centre_x(markers)
        span = abs(_vec(markers["shoulder_l"])[0] - _vec(markers["shoulder_r"])[0]) if (
            "shoulder_l" in markers and "shoulder_r" in markers) else DEFAULT_SPAN
        torso_radius, limb_radius = max(0.5 * span, 0.08), max(0.25 * span, 0.05)
        torso_distance = np.abs(pts[:, 0] - cx) / torso_radius
    else:
        root, middle, end = (_vec(markers[f"{n}_{side}"]) for n in ("hip", "knee", "ankle"))
        other = _vec(markers[f"hip_{'r' if side == 'l' else 'l'}"])
        limb_radius = torso_radius = max(0.5 * float(np.linalg.norm(root - other)), 0.06)
        torso_distance = np.linalg.norm(pts - other, axis=1) / torso_radius  # closer to the other leg
    segment = end - root
    length = max(float(np.linalg.norm(segment)), 1e-6)
    along = (pts - root) @ segment / (length * length)
    closest = root + np.clip(along, 0.0, 1.0)[:, None] * segment
    limb_distance = np.linalg.norm(pts - closest, axis=1) / limb_radius
    membership = _smoothstep((torso_distance - limb_distance) / 0.8 + 0.5)
    lead = 0.06 / length  # the blend starts a few centimetres before the joint
    return membership * _smoothstep((along + lead) / (2 * lead))


def rotate_weighted(points: Any, pivot: Any, axis: Any, degrees: float, weights: Any) -> np.ndarray:
    """Points turned about ``axis`` through ``pivot`` by ``degrees`` times each point's weight."""
    pts = as_points(points)
    k = _unit(_vec(axis))
    angle = np.radians(degrees) * np.asarray(weights, dtype=np.float64)
    local = pts - _vec(pivot)
    cos, sin = np.cos(angle)[:, None], np.sin(angle)[:, None]
    rotated = local * cos + np.cross(k, local) * sin + np.outer(local @ k, k) * (1.0 - cos)
    return rotated + _vec(pivot)


def apply_align(points: Any, markers: Mapping[str, Any], plan: AlignPlan) -> Tuple[np.ndarray, Dict[str, Vector]]:
    """The garment's points and its markers moved by an :class:`AlignPlan`."""
    moved = plan.similarity.apply(points)
    names = list(markers)
    placed = plan.similarity.apply([markers[n] for n in names]) if names else np.zeros((0, 3))
    new_markers = {name: _tuple(placed[i]) for i, name in enumerate(names)}
    for side, limb, pivot, axis, degrees in plan.limbs:
        weights = limb_weights(moved, new_markers, side, limb)
        moved = rotate_weighted(moved, pivot, axis, degrees, weights)
        chain = ("elbow", "wrist") if limb == "arm" else ("knee", "ankle")
        for joint in chain:
            name = f"{joint}_{side}"
            if name in new_markers:
                new_markers[name] = _tuple(rotate_weighted([new_markers[name]], pivot, axis, degrees, [1.0])[0])
    return moved, new_markers


def arm_turn(markers: Mapping[str, Any], target: float, joints: Optional[Mapping[str, Any]] = None
             ) -> List[Tuple[str, Vector, Vector, float]]:
    """``(side, pivot, axis, degrees)`` that turn each arm to the body's arms (``joints``, also forward and back) or,
    without joints, to ``target`` degrees below the horizontal."""
    turns = []
    full = complete_joints(joints) if joints else {}
    for side, bone_side, sign in (("l", "L", 1.0), ("r", "R", -1.0)):
        shoulder = markers.get(f"shoulder_{side}")
        end = markers.get(f"wrist_{side}", markers.get(f"elbow_{side}"))
        if shoulder is None or end is None:
            continue
        current = _unit(_vec(end) - _vec(shoulder))
        if f"SKEL_{bone_side}_UpperArm" in full and f"SKEL_{bone_side}_Hand" in full:
            wanted = _unit(full[f"SKEL_{bone_side}_Hand"] - full[f"SKEL_{bone_side}_UpperArm"])
        else:
            angle = math.radians(target)
            sideways = math.hypot(current[0], current[1]) or 1.0
            wanted = np.array([current[0] / sideways * math.cos(angle), current[1] / sideways * math.cos(angle),
                               -math.sin(angle)])
            if abs(current[0]) < 1e-6 and abs(current[1]) < 1e-6:
                wanted = np.array([sign * math.cos(angle), 0.0, -math.sin(angle)])
        axis = np.cross(current, wanted)
        degrees = math.degrees(math.atan2(float(np.linalg.norm(axis)), float(current @ wanted)))
        if degrees >= 0.5 and float(np.linalg.norm(axis)) > 1e-9:
            turns.append((side, _tuple(_vec(shoulder)), _tuple(_unit(axis)), degrees))
    return turns


# --------------------------------------------------------------------------------------------------
# Regions
# --------------------------------------------------------------------------------------------------

#: The body's parts by bone: (from joint, to joint, radius in metres, part). A point belongs to the part whose bone
#: is nearest relative to the part's thickness, so the thin arm never claims the side of the wide torso. Generic
#: human proportions, nothing measured from the game.
BODY_SEGMENTS = (
    ("SKEL_Pelvis", "SKEL_Spine0", 0.15, "torso"), ("SKEL_Spine0", "SKEL_Spine1", 0.15, "torso"),
    ("SKEL_Spine1", "SKEL_Spine2", 0.15, "torso"), ("SKEL_Spine2", "SKEL_Spine3", 0.15, "torso"),
    ("SKEL_Spine3", "SKEL_Neck_1", 0.14, "torso"), ("SKEL_Neck_1", "SKEL_Head", 0.06, "neck"),
    ("SKEL_Head", "head-top", 0.1, "head"),
    ("SKEL_L_Clavicle", "SKEL_L_UpperArm", 0.07, "clavicle"), ("SKEL_R_Clavicle", "SKEL_R_UpperArm", 0.07, "clavicle"),
    ("SKEL_L_UpperArm", "SKEL_L_Forearm", 0.055, "upper_arm"), ("SKEL_R_UpperArm", "SKEL_R_Forearm", 0.055, "upper_arm"),
    ("SKEL_L_Forearm", "SKEL_L_Hand", 0.045, "forearm"), ("SKEL_R_Forearm", "SKEL_R_Hand", 0.045, "forearm"),
    ("SKEL_L_Hand", "L-fingers", 0.04, "hand"), ("SKEL_R_Hand", "R-fingers", 0.04, "hand"),
    ("SKEL_L_Thigh", "SKEL_L_Calf", 0.085, "leg"), ("SKEL_R_Thigh", "SKEL_R_Calf", 0.085, "leg"),
    ("SKEL_L_Calf", "SKEL_L_Foot", 0.06, "leg"), ("SKEL_R_Calf", "SKEL_R_Foot", 0.06, "leg"),
    ("SKEL_L_Foot", "L-toes", 0.05, "leg"), ("SKEL_R_Foot", "R-toes", 0.05, "leg"),
)
#: How far below the shoulder joints the shoulders region reaches on the torso, and how far before the wrist a
#: sleeve counts as its cuff (metres).
SHOULDER_DEPTH = 0.07
CUFF_LENGTH = 0.07


def _segment_end(name: str, joints: Mapping[str, np.ndarray]) -> Optional[np.ndarray]:
    if name in joints:
        return joints[name]
    if name == "head-top" and "SKEL_Head" in joints:
        return joints["SKEL_Head"] + np.array([0.0, 0.0, 0.16])
    if name.endswith("-fingers"):
        side = name[0]
        hand, fore = joints.get(f"SKEL_{side}_Hand"), joints.get(f"SKEL_{side}_Forearm")
        if hand is not None and fore is not None:
            return hand + 0.4 * (hand - fore)
    if name.endswith("-toes"):
        foot = joints.get(f"SKEL_{name[0]}_Foot")
        if foot is not None:
            return foot + np.array([0.0, -0.15, -0.05])
    return None


def body_regions(points: Any, joints: Mapping[str, Any]) -> np.ndarray:
    """The region of each point on or near the body (an index into :data:`REGIONS`, or :data:`OTHER` for the head
    and the hands' fingers), from the body's joints: the nearest bone relative to its part's thickness, the torso
    then split by height and front to back. A garment vertex takes the region of the body point nearest to it."""
    pts = as_points(points)
    full = complete_joints(joints)
    segments = []
    for start, end, radius, part in BODY_SEGMENTS:
        a, b = full.get(start), _segment_end(end, full)
        if a is not None and b is not None:
            segments.append((a, b, radius, part))
    region = np.full(len(pts), OTHER, dtype=np.int64)
    if not segments or not len(pts):
        return region
    best = np.full(len(pts), np.inf)
    part_of = np.zeros(len(pts), dtype=np.int64)
    parts = [part for _, _, _, part in segments]
    for index, (a, b, radius, _part) in enumerate(segments):
        segment = b - a
        length = max(float(segment @ segment), 1e-12)
        t = np.clip((pts - a) @ segment / length, 0.0, 1.0)
        distance = np.linalg.norm(pts - (a + t[:, None] * segment), axis=1) / radius
        closer = distance < best
        best[closer] = distance[closer]
        part_of[closer] = index
    named = np.array(parts)[part_of]
    pelvis, neck = full["SKEL_Pelvis"], full["SKEL_Neck_1"]
    shoulder_z = float(np.mean([full[n][2] for n in ("SKEL_L_UpperArm", "SKEL_R_UpperArm") if n in full]
                               or [neck[2] - 0.1]))
    height = max(float(neck[2] - pelvis[2]), 0.1)
    z = pts[:, 2]
    t = (z - pelvis[2]) / height
    spine = sorted((full[n] for n in ("SKEL_Pelvis", "SKEL_Spine0", "SKEL_Spine1", "SKEL_Spine2", "SKEL_Spine3",
                                      "SKEL_Neck_1") if n in full), key=lambda p: p[2])
    spine_y = np.interp(z, [p[2] for p in spine], [p[1] for p in spine])
    torso = named == "torso"
    region[(named == "clavicle") | (torso & (z >= shoulder_z - SHOULDER_DEPTH))] = REGIONS.index("shoulders")
    trunk = torso & (z < shoulder_z - SHOULDER_DEPTH)
    region[trunk & (t > 0.45) & (pts[:, 1] < spine_y)] = REGIONS.index("chest")  # the ped faces -Y
    region[trunk & (t > 0.45) & (pts[:, 1] >= spine_y)] = REGIONS.index("back")
    region[trunk & (t > 0.12) & (t <= 0.45)] = REGIONS.index("waist")
    region[trunk & (t <= 0.12)] = REGIONS.index("hips")
    region[(named == "neck") | (torso & (z > neck[2]))] = REGIONS.index("neck")
    region[named == "upper_arm"] = REGIONS.index("upper_arms")
    region[named == "forearm"] = REGIONS.index("forearms")
    region[named == "leg"] = REGIONS.index("legs")
    region[named == "head"] = REGIONS.index("head")
    for side in ("L", "R"):
        hand = full.get(f"SKEL_{side}_Hand")
        if hand is not None:
            near_wrist = np.isin(named, ("forearm", "hand")) & (np.linalg.norm(pts - hand, axis=1) < CUFF_LENGTH)
            region[near_wrist] = REGIONS.index("cuffs")
    return region


def classify_regions(positions: Any, markers: Mapping[str, Any]) -> np.ndarray:
    """The region of each point (an index into :data:`REGIONS`, or :data:`OTHER` for hands) from the markers alone,
    for when there is no body to measure against. Needs the pelvis (or both hips); missing upper markers are filled in
    from ordinary proportions."""
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
    # A point belongs to an arm when it is nearer the arm's bone than the torso's centre line, relative to how
    # thick each is: the side of the torso under the armpit of an A-pose stays torso.
    torso_radius, arm_radius = 0.5 * span, 0.2 * span
    arm = np.zeros(len(points), dtype=bool)
    for side, suffix in ((1.0, "l"), (-1.0, "r")):
        shoulder, elbow = found.get(f"shoulder_{suffix}"), found.get(f"elbow_{suffix}")
        if shoulder is None or elbow is None:
            continue
        wrist = found.get(f"wrist_{suffix}", elbow + (elbow - shoulder))
        upper, fore = elbow - shoulder, wrist - elbow
        length, fore_length = float(np.linalg.norm(upper)), float(np.linalg.norm(fore))
        if length < 1e-6:
            continue
        along = (points - shoulder) @ upper / (length * length)
        to_upper = np.linalg.norm(points - (shoulder + np.clip(along, 0.0, 1.0)[:, None] * upper), axis=1)
        along_fore = (points - elbow) @ fore / max(fore_length * fore_length, 1e-12)
        to_fore = np.linalg.norm(points - (elbow + np.clip(along_fore, 0.0, 1.0)[:, None] * fore), axis=1)
        mine = (np.sign(x - cx) == side) & (along > 0.0)
        nearer = np.minimum(to_upper, to_fore) / arm_radius < lateral / torso_radius
        upper_arm = mine & nearer & (along <= 1.0)
        forearm = mine & nearer & (along > 1.0)
        cuff = forearm & (np.linalg.norm(points - wrist, axis=1) < CUFF_LENGTH)
        region[upper_arm] = REGIONS.index("upper_arms")
        region[forearm] = REGIONS.index("forearms")
        region[cuff] = REGIONS.index("cuffs")
        region[forearm & (along_fore > 1.15)] = OTHER  # the hand
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
FLOATING_MM = 18.0
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

#: The furthest Push Out of Body moves a vertex (metres). Deeper than this the garment does not just touch the body:
#: a sleeve runs through the torso, or the garment sits in the wrong place, and moving it out would pull it onto the
#: wrong surface. Those vertices stay and are reported.
MAX_PUSH = 0.03
#: Snug to Body leaves alone what hangs further than this from the body (metres): hoods, skirts, coat tails.
SNUG_REACH = 0.08
#: How far outside a pushed vertex another layer still counts as lying on it and moves with it (metres).
LAYER_REACH = 0.012


def push_out_offsets(positions: Any, nearest: Any, normals: Any, clearance: Any, gap: float,
                     max_push: float = MAX_PUSH, locked: Optional[Any] = None) -> np.ndarray:
    """Offsets that move every vertex closer to the body than ``gap`` (metres, also those inside) to ``gap``
    outside it, along the body's surface normal. Vertices deeper inside than ``max_push`` and ``locked`` ones stay."""
    points = as_points(positions)
    clearance = np.asarray(clearance, dtype=np.float64)
    target = as_points(nearest) + as_points(normals) * gap
    offsets = np.zeros_like(points)
    needs = (clearance < gap) & (clearance > -max_push)
    if locked is not None:
        needs &= ~np.asarray(locked, dtype=bool)
    offsets[needs] = target[needs] - points[needs]
    return offsets


def clamp_moves(start: Any, positions: Any, limit: float) -> np.ndarray:
    """``positions`` with no vertex further than ``limit`` from where it started (the passes of a push add up)."""
    start, positions = as_points(start), as_points(positions)
    moves = positions - start
    lengths = np.linalg.norm(moves, axis=1)
    over = lengths > limit
    result = positions.copy()
    result[over] = start[over] + moves[over] * (limit / lengths[over])[:, None]
    return result


def layer_follow(positions: Any, offsets: Any, clearance: Any, reach: float = LAYER_REACH) -> np.ndarray:
    """Offsets with the layers that lie over a pushed vertex (a shell over its lining, a pocket over the front) moved
    along by at least as much, so the layers keep their order and their distance."""
    points = as_points(positions)
    offsets = as_points(offsets).copy()
    clearance = np.asarray(clearance, dtype=np.float64)
    moved = np.nonzero(np.linalg.norm(offsets, axis=1) > 1e-6)[0]
    if not len(moved):
        return offsets
    q, t, _d = grid_pairs(points[moved], points, reach)
    source, other = moved[q], t
    outer = (clearance[other] > clearance[source] + 1e-4) & (np.linalg.norm(offsets[other], axis=1) < 1e-6)
    source, other = source[outer], other[outer]
    if not len(other):
        return offsets
    lengths = np.linalg.norm(offsets[source], axis=1)
    order = np.lexsort((-lengths, other))  # the largest push behind each outer vertex first
    other, source = other[order], source[order]
    first = np.ones(len(other), dtype=bool)
    first[1:] = other[1:] != other[:-1]
    offsets[other[first]] = offsets[source[first]]
    return offsets


def snug_offsets(positions: Any, nearest: Any, normals: Any, clearance: Any, gap: float, amount: float,
                 weights: Any, max_move: float = 0.15, reach: float = SNUG_REACH) -> np.ndarray:
    """Offsets that bring vertices further off the body than ``gap`` towards it, by ``amount`` (0 to 1) of the
    way and each vertex's weight; no vertex moves more than ``max_move`` metres, and what hangs further than ``reach``
    from the body (a hood, a skirt) is left alone."""
    points = as_points(positions)
    clearance = np.asarray(clearance, dtype=np.float64)
    weights = np.asarray(weights, dtype=np.float64) * (1.0 - _smoothstep((clearance - reach) / 0.02 + 0.5))
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

#: Two vertices of the same open edge closer along that edge than this many weld distances (and never less than a
#: centimetre) are neighbours on one hem or cuff, not two sides of a seam: they are never joined.
CHAIN_GAP_FACTOR = 10.0
#: Surfaces facing more than this far apart (degrees) are two sides of a fold or slab, never a seam.
FACING_LIMIT = 120.0


def _pair_keys(a: np.ndarray, b: np.ndarray, count: int) -> np.ndarray:
    return np.minimum(a, b).astype(np.int64) * count + np.maximum(a, b)


def face_vertex_pairs(loop_vertex: Any, face_start: Any, face_total: Any) -> np.ndarray:
    """Every pair of vertices that share a face (the corners of each polygon), as ``(N, 2)``."""
    loop_vertex = np.asarray(loop_vertex, dtype=np.int64)
    start = np.asarray(face_start, dtype=np.int64)
    total = np.asarray(face_total, dtype=np.int64)
    if not len(total):
        return np.zeros((0, 2), dtype=np.int64)
    position = np.arange(len(loop_vertex)) - np.repeat(start, total)
    size = np.repeat(total, total)
    pairs = []
    for step in range(1, int(total.max())):
        valid = position + step < size
        first = np.nonzero(valid)[0]
        pairs.append(np.column_stack([loop_vertex[first], loop_vertex[first + step]]))
    return np.concatenate(pairs) if pairs else np.zeros((0, 2), dtype=np.int64)


class PairRules:
    """What keeps two vertices from being two sides of one seam, as a test on any pairs of vertices (see
    :func:`seam_candidates`): sharing a face, lying next to each other on one open edge (``chains``), surfaces facing
    apart within one part (``normals``, ``components``; a thick export keeps the rule across parts and joins only
    across them), a lining and its shell (``fabrics`` and the pairs named in ``apart``), different ``groups``, and the
    two sides of an open front (``sides`` of opposite sign, see :func:`front_sides`).
    The weld applies them to every two vertices that would become one, not only to the closest pair, so joining two
    groups never joins neighbours along one panel's own edge."""

    def __init__(self, count: int, distance: float, *, chains: Optional[Tuple[np.ndarray, np.ndarray, np.ndarray]] = None,
                 face_pairs: Optional[Any] = None, normals: Optional[Any] = None, components: Optional[Any] = None,
                 cross_components_only: bool = False, fabrics: Optional[Any] = None,
                 apart: Iterable[Tuple[Any, Any]] = (), groups: Optional[Any] = None,
                 sides: Optional[Any] = None) -> None:
        self.count = count
        self.gap = max(CHAIN_GAP_FACTOR * distance, 0.01)
        self.chains = chains
        self.face_keys: Optional[np.ndarray] = None
        if face_pairs is not None:
            shared = np.asarray(face_pairs, dtype=np.int64).reshape(-1, 2)
            self.face_keys = np.unique(_pair_keys(shared[:, 0], shared[:, 1], count))
        self.normals = as_points(normals) if normals is not None else None
        self.components = np.asarray(components) if components is not None else None
        self.cross_components_only = cross_components_only
        self.fabrics = np.asarray(fabrics) if fabrics is not None else None
        self.apart = list(apart)
        self.groups = np.asarray(groups) if groups is not None else None
        self.sides = np.asarray(sides, dtype=np.int64) if sides is not None else None

    def allowed(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        """Which pairs ``(a[i], b[i])`` may be two sides of one seam (distance aside)."""
        a = np.asarray(a, dtype=np.int64)
        b = np.asarray(b, dtype=np.int64)
        keep = np.ones(len(a), dtype=bool)
        if not len(a):
            return keep
        if self.face_keys is not None and len(self.face_keys):
            keys = _pair_keys(a, b, self.count)
            at = np.minimum(np.searchsorted(self.face_keys, keys), len(self.face_keys) - 1)
            keep &= self.face_keys[at] != keys
        if self.chains is not None:
            chain, arc, lengths = self.chains
            same = (chain[a] >= 0) & (chain[a] == chain[b])
            along = np.abs(arc[a] - arc[b])
            loop = lengths[np.maximum(chain[a], 0)] if len(lengths) else np.zeros(len(a))
            along = np.where(same & (loop > 0), np.minimum(along, np.abs(loop) - along), along)
            keep &= ~(same & (along < self.gap))
        comp = self.components
        if self.normals is not None:
            n = self.normals
            facing = np.einsum("ij,ij->i", n[a], n[b]) > math.cos(math.radians(FACING_LIMIT))
            if comp is not None and not self.cross_components_only:
                facing |= comp[a] != comp[b]  # two panels: their normals may be flipped against each other
            keep &= facing
        if self.cross_components_only and comp is not None:
            keep &= comp[a] != comp[b]
        if self.fabrics is not None:
            labels = self.fabrics
            for first, second in self.apart:
                keep &= ~(((labels[a] == first) & (labels[b] == second))
                          | ((labels[a] == second) & (labels[b] == first)))
        if self.groups is not None:
            keep &= self.groups[a] == self.groups[b]
        if self.sides is not None:
            keep &= self.sides[a] * self.sides[b] >= 0
        return keep


def seam_candidates(positions: Any, distance: float, candidates: Optional[Any] = None, **rules: Any
                    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Pairs of vertices that may be two sides of one seam: closer than ``distance`` and allowed by :class:`PairRules`
    (``rules`` are its keyword arguments): never two vertices of one face, never neighbours along the same open edge,
    never across a pair of ``fabrics`` named in ``apart`` (a lining and its shell), and with ``groups`` only within one
    group. Surfaces facing apart are a fold or a slab, never a seam, within one part of the garment (``components``)
    and in a thick export (``cross_components_only``); two separate panels may face apart at their seam, because
    exports often flip some panels' normals, so the rule does not part them. ``(first, second, distance)``."""
    points = as_points(positions)
    indices = np.nonzero(np.asarray(candidates, dtype=bool))[0] if candidates is not None else None
    a, b, d = close_pairs(points, distance, indices)
    keep = PairRules(len(points), distance, **rules).allowed(a, b)
    return a[keep], b[keep], d[keep]


#: A weld group (the vertices that become one) holds at most this many: where several panels meet in one corner.
MAX_WELD_GROUP = 8
#: Rounds of joining each group to its mutual nearest neighbour group.
WELD_ROUNDS = 12
#: Group pairs measured at once (bounds the memory of a round).
WELD_BLOCK = 20000


def _joinable(points: np.ndarray, root: np.ndarray, first: np.ndarray, second: np.ndarray, distance: float,
              rules: PairRules) -> np.ndarray:
    """Whether group ``first[i]`` may join group ``second[i]`` (groups named by their root, each of at most
    :data:`MAX_WELD_GROUP` vertices): the joined group is no wider than ``distance``, and every vertex of the one may
    become one with every vertex of the other (:class:`PairRules`)."""
    roots = np.unique(np.concatenate([first, second]))
    involved = np.nonzero(np.isin(root, roots))[0]
    order = involved[np.argsort(root[involved], kind="stable")]
    sorted_roots = root[order]
    starts = np.searchsorted(sorted_roots, roots)
    sizes = np.searchsorted(sorted_roots, roots, "right") - starts
    rank = np.arange(len(order)) - np.repeat(starts, sizes)
    table = np.full((len(roots), MAX_WELD_GROUP), -1, dtype=np.int64)
    slot = np.searchsorted(roots, sorted_roots)
    table[slot, np.minimum(rank, MAX_WELD_GROUP - 1)] = order
    ok = np.zeros(len(first), dtype=bool)
    for begin in range(0, len(first), WELD_BLOCK):
        left = table[np.searchsorted(roots, first[begin:begin + WELD_BLOCK])]
        right = table[np.searchsorted(roots, second[begin:begin + WELD_BLOCK])]
        valid = (left >= 0)[:, :, None] & (right >= 0)[:, None, :]
        la = np.broadcast_to(np.maximum(left, 0)[:, :, None], valid.shape)
        rb = np.broadcast_to(np.maximum(right, 0)[:, None, :], valid.shape)
        squared = ((points[la] - points[rb]) ** 2).sum(axis=3)
        narrow = np.sqrt(np.where(valid, squared, 0.0).max(axis=(1, 2))) <= distance + 1e-9
        allowed = rules.allowed(la.reshape(-1), rb.reshape(-1)).reshape(valid.shape)
        ok[begin:begin + WELD_BLOCK] = narrow & (allowed | ~valid).all(axis=(1, 2))
    return ok


def weld_steps(positions: Any, distance: float, candidates: Optional[Any] = None, groups: Optional[Any] = None,
               **rules: Any) -> Any:
    """Which vertex each vertex merges into (itself when it stays) and where the merged vertices go (the mean of
    their group), as a generator that yields after each round and returns ``(target, merged)``. Pairs come from
    :func:`seam_candidates` (``rules`` are the keyword arguments of :class:`PairRules`). Each round joins every group
    to the group nearest to it when that one's nearest is it too, only when the joined group is no wider than
    ``distance`` (so a dense hem cannot collapse into a point) and only when the rules allow every two of its vertices
    to become one (so two neighbours along one panel's edge never do, whichever panel's vertex brought them together);
    a corner where several panels meet grows over the rounds. Everything runs on whole arrays: a shirt with half a
    million candidate pairs takes seconds."""
    points = as_points(positions)
    count = len(points)
    target = np.arange(count)
    merged = points.copy()
    pair_rules = PairRules(count, distance, groups=groups, **rules)
    indices = np.nonzero(np.asarray(candidates, dtype=bool))[0] if candidates is not None else None
    a, b, d = close_pairs(points, distance, indices)
    keep = pair_rules.allowed(a, b)
    a, b, d = a[keep], b[keep], d[keep]
    if not len(a):
        return target, merged
    root = np.arange(count)
    size = np.ones(count, dtype=np.int64)
    for _ in range(WELD_ROUNDS):
        ra, rb = root[a], root[b]
        apart = ra != rb
        ra, rb, dd = ra[apart], rb[apart], d[apart]
        if not len(ra):
            break
        # Each group's nearest other group (by its closest vertex pair) that it may still join.
        first = np.concatenate([ra, rb])
        second = np.concatenate([rb, ra])
        gap = np.concatenate([dd, dd])
        order = np.lexsort((second, gap, first))
        first, second = first[order], second[order]
        lead = np.ones(len(first), dtype=bool)
        lead[1:] = first[1:] != first[:-1]
        best = np.full(count, -1, dtype=np.int64)
        best[first[lead]] = second[lead]
        mine = first[lead]
        mutual = mine[(best[best[mine]] == mine) & (mine < best[mine])]
        partner = best[mutual]
        refused = False
        if len(mutual):
            joinable = size[mutual] + size[partner] <= MAX_WELD_GROUP
            joinable[joinable] = _joinable(points, root, mutual[joinable], partner[joinable], distance, pair_rules)
            if not joinable.all():
                # Two groups that may not join never will: drop the candidate pairs between them, so each can look
                # for its next nearest group in the next round.
                refused_keys = np.unique(_pair_keys(mutual[~joinable], partner[~joinable], count))
                keys = _pair_keys(root[a], root[b], count)
                drop = np.isin(keys, refused_keys)
                a, b, d = a[~drop], b[~drop], d[~drop]
                refused = True
            mutual, partner = mutual[joinable], partner[joinable]
        if not len(mutual) and not refused:
            break
        if len(mutual):
            remap = np.arange(count)
            remap[partner] = mutual
            root = remap[root]
            size[mutual] += size[partner]
            size[partner] = 0
        yield
    joined = np.nonzero(np.bincount(root, minlength=count) > 1)[0]
    if not len(joined):
        return target, merged
    lowest = np.full(count, count, dtype=np.int64)
    np.minimum.at(lowest, root, np.arange(count))
    members = np.nonzero(np.isin(root, joined))[0]
    target[members] = lowest[root[members]]
    sums = np.zeros((count, 3))
    np.add.at(sums, root[members], points[members])
    totals = np.bincount(root[members], minlength=count).astype(np.float64)
    merged[members] = sums[root[members]] / totals[root[members], None]
    return target, merged


def weld_targets(positions: Any, distance: float, candidates: Optional[Any] = None,
                 groups: Optional[Any] = None, progress: Optional[Any] = None,
                 **rules: Any) -> Tuple[np.ndarray, np.ndarray]:
    """:func:`weld_steps` run to its end; ``progress`` is called after each round."""
    steps = weld_steps(positions, distance, candidates, groups, **rules)
    while True:
        try:
            next(steps)
        except StopIteration as stop:
            return stop.value
        if progress is not None:
            progress()


def joined_across(target: Any, parts: Any) -> np.ndarray:
    """Whether each vertex was joined to a vertex of another part (its weld group spans two parts or more)."""
    target = np.asarray(target, dtype=np.int64)
    parts = np.asarray(parts, dtype=np.int64)
    pairs = np.unique(np.column_stack([target, parts]), axis=0)
    spans = np.bincount(pairs[:, 0], minlength=len(target))
    return spans[target] > 1


#: An unjoined seam vertex closer than this share of the weld distance to the other panel's open edge lies on that
#: edge (a seam whose sides have different numbers of vertices): the seam is closed there.
ON_EDGE_SHARE = 0.125


def _segment_distance(points: np.ndarray, start: np.ndarray, end: np.ndarray) -> np.ndarray:
    span = end - start
    length = np.einsum("ij,ij->i", span, span)
    t = np.clip(np.einsum("ij,ij->i", points - start, span) / np.maximum(length, 1e-18), 0.0, 1.0)
    return np.linalg.norm(points - (start + t[:, None] * span), axis=1)


def open_seams(positions: Any, distance: float, boundary: Any, parts: Any, target: Any,
               edges: Optional[Any] = None, **rules: Any) -> np.ndarray:
    """The vertices on open edges that have a seam partner on another part (within ``distance`` and allowed by
    :class:`PairRules`, ``rules`` its keyword arguments) yet were joined to no vertex of another part: where a seam
    stayed open. A vertex joined across at least once is sewn, even when more vertices lie close to it. With the open
    ``edges``, a vertex that lies on the other part's open edge (where one side of a seam has more vertices than the
    other) is sewn too: only a real gap counts."""
    points = as_points(positions)
    parts = np.asarray(parts)
    rules.setdefault("components", parts)
    a, b, _d = seam_candidates(points, distance, boundary, **rules)
    across = parts[a] != parts[b]
    a, b = a[across], b[across]
    near = np.unique(np.concatenate([a, b]))
    unjoined = near[~joined_across(target, parts)[near]]
    if edges is None or not len(unjoined):
        return unjoined
    # The open edges at each vertex (two along a panel's edge).
    edges = np.asarray(edges, dtype=np.int64).reshape(-1, 2)
    ends = np.concatenate([edges, edges[:, ::-1]])
    ends = ends[np.argsort(ends[:, 0], kind="stable")]
    first = np.searchsorted(ends[:, 0], np.arange(len(points)))
    last = np.searchsorted(ends[:, 0], np.arange(len(points)), "right")
    vertex = np.concatenate([a, b])
    partner = np.concatenate([b, a])
    keep = np.isin(vertex, unjoined)
    vertex, partner = vertex[keep], partner[keep]
    gap = np.full(len(points), np.inf)
    for slot in range(2):
        has = first[partner] + slot < last[partner]
        v, u = vertex[has], partner[has]
        other = ends[first[u] + slot, 1]
        np.minimum.at(gap, v, _segment_distance(points[v], points[u], points[other]))
    return unjoined[gap[unjoined] >= ON_EDGE_SHARE * distance]


def open_seam_count(positions: Any, distance: float, boundary: Any, parts: Any, target: Any, **rules: Any) -> int:
    """How many seam vertices stayed open after the weld (:func:`open_seams`)."""
    return int(len(open_seams(positions, distance, boundary, parts, target, **rules)))


def lining_pairs(positions: Any, normals: Any, groups: Any, *, weld: float = 0.002, near: float = 0.03,
                 share: float = 0.4, sample: int = 3000, areas: Optional[Any] = None,
                 cover: float = 0.25) -> List[Tuple[int, int]]:
    """Groups (fabrics) that lie as a lining under another: most of the group lies a few millimetres from the other
    along the surface normal, and the group is big compared with it (a quarter of its area by default). A seam
    between two fabrics only touches along its edge, and a patch pocket, a turned-down collar, a placket or an elbow
    patch is small next to the fabric it lies on: none of them is a lining. ``areas`` is each vertex's share of the
    surface (vertex counts otherwise)."""
    points = as_points(positions)
    normals = as_points(normals)
    groups = np.asarray(groups)
    weights = np.ones(len(points)) if areas is None else np.asarray(areas, dtype=np.float64)
    found: List[Tuple[int, int]] = []
    names = [g for g in np.unique(groups) if (groups == g).sum() >= 30]
    if len(names) < 2:
        return found
    size = {g: float(weights[groups == g].sum()) for g in names}
    rng = np.random.default_rng(7)
    queries, owners = [], []
    for group in names:
        own = np.nonzero(groups == group)[0]
        if len(own) > sample:
            own = rng.choice(own, sample, replace=False)
        queries.append(own)
        owners.append(np.full(len(own), group))
    query = np.concatenate(queries)
    owner = np.concatenate(owners)
    # Each group's sample is searched among the other groups' vertices only, and only each sampled vertex's nearest
    # one beyond the weld is kept (sorting every pair took seconds on a detailed garment).
    found_q, found_t, found_d = [], [], []
    offset = 0
    for group, own in zip(names, queries):
        others = np.nonzero(groups != group)[0]
        gq, gt, gd = grid_pairs(points[own], points[others], near)
        apart = gd > weld
        gq, gt, gd = gq[apart], gt[apart], gd[apart]
        if len(gq):
            best = np.full(len(own), np.inf)
            np.minimum.at(best, gq, gd)
            nearest = np.nonzero(gd == best[gq])[0]
            _, first = np.unique(gq[nearest], return_index=True)  # one per sampled vertex (the first of a tie)
            pick = nearest[first]
            found_q.append(gq[pick] + offset)
            found_t.append(others[gt[pick]])
            found_d.append(gd[pick])
        offset += len(own)
    if not found_q:
        return found
    q, t, d = np.concatenate(found_q), np.concatenate(found_t), np.concatenate(found_d)
    i = query[q]
    direction = (points[t] - points[i]) / d[:, None]
    layered = (np.abs(np.einsum("ij,ij->i", direction, normals[i])) > 0.7) & (
        np.abs(np.einsum("ij,ij->i", normals[i], normals[t])) > 0.7)
    for group, own in zip(names, queries):
        mine = owner[q] == group
        hits: Dict[Any, int] = {}
        for other_group in groups[t[mine & layered]]:
            hits[other_group] = hits.get(other_group, 0) + 1
        for other_group, count in hits.items():
            if count >= share * len(own) and other_group in size and size[group] >= cover * size[other_group]:
                pair = (min(int(group), int(other_group)), max(int(group), int(other_group)))
                if pair not in found:
                    found.append(pair)
    return found


def seam_pairs(positions: Any, distance: float, candidates: Optional[Any] = None, **rules: Any) -> np.ndarray:
    """Pairs of separate vertices that sit on top of each other (the open seams of unwelded panels), by the rules of
    :func:`seam_candidates`."""
    a, b, _d = seam_candidates(positions, distance, candidates, **rules)
    return np.column_stack([a, b]).astype(np.int64).reshape(-1, 2)


def tears(pairs: np.ndarray, posed: Any, threshold: float) -> Tuple[np.ndarray, np.ndarray]:
    """Which seam pairs separate by more than ``threshold`` metres in a pose, and every pair's separation."""
    points = as_points(posed)
    pairs = np.asarray(pairs, dtype=np.int64).reshape(-1, 2)
    if not len(pairs):
        return np.zeros(0, dtype=bool), np.zeros(0)
    separation = np.linalg.norm(points[pairs[:, 0]] - points[pairs[:, 1]], axis=1)
    return separation > threshold, separation


def components(count: int, edges: Any) -> np.ndarray:
    """The connected part (panel) each vertex belongs to."""
    edges = np.asarray(edges, dtype=np.int64).reshape(-1, 2)
    label = np.arange(count)
    if not len(edges):
        return label
    changed = True
    while changed:  # label propagation; each round halves the remaining distance on long panels
        low = np.minimum(label[edges[:, 0]], label[edges[:, 1]])
        before = label.copy()
        np.minimum.at(label, edges[:, 0], low)
        np.minimum.at(label, edges[:, 1], low)
        label = label[label]
        changed = bool(np.any(label != before))
    _, compact = np.unique(label, return_inverse=True)
    return compact


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


#: The most pieces one strip is cut into (a strip a hundred times longer than wide does not need a hundred pieces).
MAX_STRIP_PIECES = 32


def strip_segments(island: Any, face_uv_centre: Any, loop_uv: Any, face_total: Any,
                   aspect: float = 4.0, usable: Optional[Any] = None) -> Tuple[np.ndarray, int]:
    """Cuts long thin UV islands (hem bands, waistbands, straps) into roughly square pieces, so the packer does
    not shrink every island to fit their length. Islands ``usable`` marks False (no room in the texture, see
    :func:`usable_islands`) are never cut: a strip without width would otherwise fall into millions of pieces. Returns
    each face's piece number (0 for uncut islands) and how many islands were cut."""
    island = np.asarray(island, dtype=np.int64)
    centres = np.asarray(face_uv_centre, dtype=np.float64).reshape(-1, 2)
    uv = np.asarray(loop_uv, dtype=np.float64).reshape(-1, 2)
    loop_face = np.repeat(np.arange(len(island)), np.asarray(face_total, dtype=np.int64))
    pieces = np.zeros(len(island), dtype=np.int64)
    cut = 0
    for value in np.unique(island):
        if usable is not None and not usable[value]:
            continue
        faces = island == value
        points = uv[faces[loop_face]]
        if len(points) < 6 or not np.isfinite(points).all():
            continue
        mean = points.mean(axis=0)
        values, vectors = np.linalg.eigh(np.cov((points - mean).T))
        axis, across = vectors[:, 1], vectors[:, 0]
        along = (points - mean) @ axis
        side = (points - mean) @ across
        length = float(along.max() - along.min())
        width = float(side.max() - side.min())
        if width <= 1e-6 * max(length, 1e-9) or length / width <= aspect:
            continue
        count = min(MAX_STRIP_PIECES, int(math.ceil(length / (2 * width))))
        step = length / count
        position = ((centres[faces] - mean) @ axis - along.min()) / step
        pieces[faces] = np.clip(position.astype(np.int64), 0, count - 1)
        cut += 1
    return pieces, cut


#: An island whose UV area per square metre of surface is below this share of the garment's usual one has no room in
#: the texture: a strip mapped onto a line, as Marvelous Designer maps the side walls of a thick export.
DEGENERATE_UV_SHARE = 1e-3
#: A thin island (its UV area below this share of its longest UV extent squared: narrower than about a hundredth of
#: its length) with less than this share of the usual UV area per square metre has no room either: welding a thick
#: export's walls to its panels leaves them a hair wide, and packing would blow them up to their full length.
THIN_UV_SHARE = 0.01
THIN_DENSITY_SHARE = 0.1
#: A UV point further than this many times the square root of its island's UV area from the island's middle is a
#: stray point (a broken export): it is moved into the island before packing.
STRAY_FACTOR = 50.0
#: A combined layout that uses less of the texture than this share is worth a warning.
SPARSE_LAYOUT_SHARE = 0.15


def triangle_areas(triangle_uv: Any, triangle_positions: Any) -> Tuple[np.ndarray, np.ndarray]:
    """Each triangle's UV area and its surface (square metres); a triangle with a broken coordinate has neither."""
    uv = np.asarray(triangle_uv, dtype=np.float64).reshape(-1, 3, 2)
    tri = np.asarray(triangle_positions, dtype=np.float64).reshape(-1, 3, 3)
    a, b, c = uv[:, 0], uv[:, 1], uv[:, 2]
    cross = np.abs((b[:, 0] - a[:, 0]) * (c[:, 1] - a[:, 1]) - (c[:, 0] - a[:, 0]) * (b[:, 1] - a[:, 1])) / 2
    surface = np.linalg.norm(np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]), axis=1) / 2
    return np.nan_to_num(cross, nan=0.0, posinf=0.0), np.nan_to_num(surface, nan=0.0, posinf=0.0)


def island_areas(island: Any, triangle_face: Any, triangle_uv: Any, triangle_positions: Any
                 ) -> Tuple[np.ndarray, np.ndarray]:
    """Each UV island's area in the texture and the surface it covers on the garment (``island``: each face's island,
    ``triangle_face``: each triangle's face)."""
    island = np.asarray(island, dtype=np.int64)
    count = int(island.max()) + 1 if len(island) else 0
    uv, surface = triangle_areas(triangle_uv, triangle_positions)
    owner = island[np.asarray(triangle_face, dtype=np.int64)]
    return np.bincount(owner, uv, minlength=count), np.bincount(owner, surface, minlength=count)


def usable_islands(uv_area: Any, surface: Any, finite: Optional[Any] = None,
                   extent: Optional[Any] = None) -> np.ndarray:
    """Which islands have room in the texture: some UV area for their surface, compared with the garment's usual UV
    area per square metre (the median over the surface). An island mapped onto a line or a point, or with broken UVs
    (``finite`` False), has none, nor has a thin one (``extent``: its longest UV side) with little UV area: packing
    would blow it up to its full length and squeeze every other island. All False when no island has any UV area."""
    uv_area = np.asarray(uv_area, dtype=np.float64)
    surface = np.asarray(surface, dtype=np.float64)
    good = (uv_area > 0) & (surface > 0)
    if finite is not None:
        good &= np.asarray(finite, dtype=bool)
    if not good.any():
        return good
    ratio = uv_area[good] / surface[good]
    order = np.argsort(ratio)
    weights = np.cumsum(surface[good][order])
    usual = float(ratio[order][np.searchsorted(weights, weights[-1] / 2)])
    usable = good & (uv_area >= DEGENERATE_UV_SHARE * usual * surface)
    if extent is not None:
        extent = np.nan_to_num(np.asarray(extent, dtype=np.float64))
        thin = uv_area < THIN_UV_SHARE * extent * extent
        usable &= ~(thin & (uv_area < THIN_DENSITY_SHARE * usual * surface))
    return usable


#: An island whose triangles' UV areas cancel out to below this share of their sum when their winding is counted folds
#: over itself.
FOLDED_SHARE = 0.5


def folded_islands(island: Any, triangle_face: Any, triangle_uv: Any) -> np.ndarray:
    """Which islands fold over themselves in the UV map: the two sides of a thick export's panel, joined at its walls
    by Prepare Garment, lie on one place with opposite winding, so their areas cancel when the winding counts. Blender's
    Average Islands Scale measures that way and blows such an island up without end, so it leaves them out."""
    island = np.asarray(island, dtype=np.int64)
    count = int(island.max()) + 1 if len(island) else 0
    uv = np.nan_to_num(np.asarray(triangle_uv, dtype=np.float64).reshape(-1, 3, 2))
    a, b, c = uv[:, 0], uv[:, 1], uv[:, 2]
    signed = ((b[:, 0] - a[:, 0]) * (c[:, 1] - a[:, 1]) - (c[:, 0] - a[:, 0]) * (b[:, 1] - a[:, 1])) / 2
    owner = island[np.asarray(triangle_face, dtype=np.int64)]
    net = np.abs(np.bincount(owner, signed, minlength=count))
    total = np.bincount(owner, np.abs(signed), minlength=count)
    return (total > 0) & (net < FOLDED_SHARE * total)


def stray_loops(loop_uv: Any, loop_island: Any, uv_area: Any, factor: float = STRAY_FACTOR) -> np.ndarray:
    """The UV points that lie far outside their island (further than ``factor`` times the square root of its UV area
    from its middle, the median of its points), or are not numbers at all."""
    uv = np.asarray(loop_uv, dtype=np.float64).reshape(-1, 2)
    island = np.asarray(loop_island, dtype=np.int64)
    finite = np.isfinite(uv).all(axis=1)
    stray = ~finite
    if not len(uv):
        return stray
    order = np.argsort(island, kind="stable")
    starts = np.searchsorted(island[order], np.arange(int(island.max()) + 2))
    reach = factor * np.sqrt(np.maximum(np.asarray(uv_area, dtype=np.float64), 0.0))
    for value in np.unique(island):
        members = order[starts[value]:starts[value + 1]]
        members = members[finite[members]]
        if len(members) < 3 or reach[value] <= 0:
            continue
        middle = np.median(uv[members], axis=0)
        stray[members] |= np.linalg.norm(uv[members] - middle, axis=1) > reach[value]
    return stray


def stacked_islands(island: Any, loop_island: Any, loop_uv: Any, precision: float = 1e-5) -> np.ndarray:
    """For each island, the first island with exactly the same UVs (itself when none comes before it): the two sides
    of a panel in a thick export, which share one place in the texture and keep sharing it when packed."""
    count = int(np.max(island)) + 1 if len(island) else 0
    loop_island = np.asarray(loop_island, dtype=np.int64)
    uv = np.round(np.nan_to_num(np.asarray(loop_uv, dtype=np.float64).reshape(-1, 2)) / precision).astype(np.int64)
    rows = np.unique(np.column_stack([loop_island, uv]), axis=0)
    first = np.full(count, -1, dtype=np.int64)
    seen: Dict[bytes, int] = {}
    starts = np.searchsorted(rows[:, 0], np.arange(count + 1))
    for value in range(count):
        key = rows[starts[value]:starts[value + 1], 1:].tobytes()
        first[value] = seen.setdefault(key, value)
    return first


def copy_stacked_uvs(loop_island: Any, stacked: Any, source_uv: Any, packed_uv: Any,
                     precision: float = 1e-5) -> np.ndarray:
    """``packed_uv`` with each stacked island (``stacked`` names its first, :func:`stacked_islands`) given the packed
    place of its first island: every corner where the first island had the same UV."""
    loop_island = np.asarray(loop_island, dtype=np.int64)
    stacked = np.asarray(stacked, dtype=np.int64)
    packed = np.asarray(packed_uv, dtype=np.float64).reshape(-1, 2).copy()
    owner = stacked[loop_island]
    copies = np.nonzero(owner != loop_island)[0]
    if not len(copies):
        return packed
    uv = np.round(np.nan_to_num(np.asarray(source_uv, dtype=np.float64).reshape(-1, 2)) / precision).astype(np.int64)
    originals = np.nonzero(owner == loop_island)[0]
    # Each row (island, u, v) compares as one value: a view of its three integers as one record, sorted as bytes.
    record = np.dtype((np.void, 3 * 8))

    def records(rows: np.ndarray) -> np.ndarray:
        return np.ascontiguousarray(rows.astype(np.int64)).view(record).reshape(-1)

    keys = records(np.column_stack([loop_island[originals], uv[originals]]))
    order = np.argsort(keys, kind="stable")
    flat = keys[order]
    probe = records(np.column_stack([owner[copies], uv[copies]]))
    found = np.minimum(np.searchsorted(flat, probe), len(flat) - 1)
    hit = flat[found] == probe
    packed[copies[hit]] = packed[originals[order[found[hit]]]]
    return packed


def nearest_points(query: Any, target: Any, start: float = 0.005) -> np.ndarray:
    """For each ``query`` point, the index of the nearest ``target`` point (searched in growing radii)."""
    query, target = as_points(query), as_points(target)
    found = np.full(len(query), -1, dtype=np.int64)
    if not len(query) or not len(target):
        return found
    extent = float(np.ptp(np.concatenate([query, target]), axis=0).max()) or 1.0
    radius = start
    left = np.arange(len(query))
    while len(left):
        q, t, d = grid_pairs(query[left], target, radius)
        if len(q):
            best = np.full(len(left), np.inf)
            np.minimum.at(best, q, d)
            pick = np.nonzero(d == best[q])[0]
            _, first = np.unique(q[pick], return_index=True)
            chosen = pick[first]
            found[left[q[chosen]]] = t[chosen]
        left = left[found[left] < 0]
        if radius > 2 * extent:
            break
        radius *= 2
    return found


def borrow_uvs(loop_vertex: Any, loop_uv: Any, keep: Any, positions: Any,
               loop_face: Optional[Any] = None) -> np.ndarray:
    """``loop_uv`` with every loop ``keep`` marks False given the UV of a kept loop: one on the same vertex when there
    is one, else one on the vertex nearest to it. With ``loop_face`` every corner of such a face takes the UV of its
    first corner, so the face covers no pixels and bakes over nothing. Faces without room in the layout (the side
    walls of a thick export) so take the colour of the panel edge next to them."""
    loop_vertex = np.asarray(loop_vertex, dtype=np.int64)
    uv = np.asarray(loop_uv, dtype=np.float64).reshape(-1, 2).copy()
    keep = np.asarray(keep, dtype=bool)
    if keep.all() or not keep.any():
        return uv
    points = as_points(positions)
    kept = np.nonzero(keep)[0]
    first = np.full(len(points), -1, dtype=np.int64)
    first[loop_vertex[kept[::-1]]] = kept[::-1]  # each vertex's first kept loop
    moved = np.nonzero(~keep)[0]
    source = first[loop_vertex[moved]]
    lonely = np.unique(loop_vertex[moved[source < 0]])
    if len(lonely):
        donors = np.nonzero(first >= 0)[0]
        nearest = nearest_points(points[lonely], points[donors])
        lookup = np.full(len(points), -1, dtype=np.int64)
        lookup[lonely] = np.where(nearest >= 0, first[donors[np.maximum(nearest, 0)]], kept[0])
        source = np.where(source >= 0, source, lookup[loop_vertex[moved]])
    uv[moved] = uv[source]
    if loop_face is not None:
        faces = np.asarray(loop_face, dtype=np.int64)[moved]
        _, first_corner = np.unique(faces, return_index=True)
        corner = np.full(int(faces.max()) + 1, -1, dtype=np.int64)
        corner[faces[first_corner]] = moved[first_corner]
        uv[moved] = uv[corner[faces]]
    return uv


def fit_unit_square(loop_uv: Any, chosen: Any, margin: float = 0.002) -> np.ndarray:
    """``loop_uv`` with the ``chosen`` loops moved and scaled together (keeping their shape) into the 0 to 1 square
    when they reach outside it: the packer may leave a layout in another UDIM tile."""
    uv = np.asarray(loop_uv, dtype=np.float64).reshape(-1, 2).copy()
    chosen = np.asarray(chosen, dtype=bool)
    if not chosen.any():
        return uv
    points = uv[chosen]
    low, high = points.min(axis=0), points.max(axis=0)
    if low.min() >= -1e-6 and high.max() <= 1.0 + 1e-6:
        return uv
    size = float((high - low).max()) or 1.0
    scale = min(1.0, (1.0 - 2 * margin) / size)
    uv[chosen] = (points - low) * scale + margin
    return uv


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


def texel_density(triangle_uv: Any, triangle_positions: Any, size: int) -> float:
    """Texture pixels per centimetre on the garment: the texture's area the UV layout uses against the surface it
    covers. 0 for a garment without surface."""
    uv = np.asarray(triangle_uv, dtype=np.float64).reshape(-1, 3, 2)
    tri = np.asarray(triangle_positions, dtype=np.float64).reshape(-1, 3, 3)
    if not len(tri):
        return 0.0
    surface = float(np.linalg.norm(np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]), axis=1).sum() / 2)
    if surface <= 1e-12:
        return 0.0
    return round(math.sqrt(uv_area(uv) * size * size / (surface * 1e4)), 1)


# --------------------------------------------------------------------------------------------------
# Garment types: open fronts, bridged thigh weights, the waist, props on their anchor
# --------------------------------------------------------------------------------------------------

#: How far from the centre plane (metres) a vertex can be one of an open front's two edges.
FRONT_BAND = 0.05


def front_sides(positions: Any, edges: Any, centre: Tuple[float, float], top: Optional[float] = None,
                band: float = FRONT_BAND) -> np.ndarray:
    """For an open front: +1 for a vertex in front (towards -Y of ``centre``'s Y), near the centre plane (within
    ``band`` of ``centre``'s X) and below ``top`` (the neck, when known) whose neighbours lie on the ped's left of the
    centre plane, -1 for one whose neighbours lie on its right, 0 for every other vertex. The two edges of an open front
    lie on top of each other at the centre, but each has its own panel beside it, so they get opposite sides, and two
    sides of one open front are never joined (:class:`PairRules` ``sides``). Seams above the neck (a hood's centre
    seam) and away from the centre weld as usual."""
    points = as_points(positions)
    if not len(points):
        return np.zeros(0, dtype=np.int64)
    cx, cy = centre
    beside = neighbour_mean(points[:, 0], edges, len(points)) - cx
    side = np.where(beside > 1e-6, 1, np.where(beside < -1e-6, -1, 0))
    front = (points[:, 1] < cy) & (np.abs(points[:, 0] - cx) <= band)
    if top is not None:
        front &= points[:, 2] < top
    return np.where(front, side, 0).astype(np.int64)


#: The words that name the bones of a leg in the freemode skeleton (``SKEL_L_Thigh``, ``RB_R_ThighRoll``,
#: ``MH_L_Knee``, ``SKEL_R_Calf``, ``SKEL_L_Foot``, ``SKEL_R_Toe0``); the side is the ``_L_`` or ``_R_`` in the name.
LEG_WORDS = ("Thigh", "Calf", "Knee", "Foot", "Toe")


def leg_side(name: str) -> Optional[str]:
    """``l`` or ``r`` for a bone of the left or right leg, else ``None``."""
    if not any(word in name for word in LEG_WORDS):
        return None
    if "_L_" in name:
        return "l"
    if "_R_" in name:
        return "r"
    return None


def mirrored_bone(name: str) -> str:
    return name.replace("_L_", "_\0_").replace("_R_", "_L_").replace("_\0_", "_R_")


def bridge_leg_weights(positions: Any, table: Any, names: Sequence[str], centre_x: float, top: float, width: float,
                       fade: float = 0.05) -> Tuple[np.ndarray, List[str], int]:
    """Weights of a skirt, a dress or coat tails bridged across the thighs: below ``top`` (the thigh joints; fully from
    ``fade`` metres below it) each vertex's leg weight is shared between the left and right leg by where it is across
    the centre (``centre_x``), from all left at ``width`` to the left of the centre to all right at ``width`` to the
    right, so the cloth between the legs follows both and does not split. How each side's share is spread over
    thigh, calf and so on stays as it was; pelvis and spine weights stay. ``table`` holds the weights (vertices by
    groups, ``names`` the groups); a mirrored bone a side lacks is added. Returns the table, its group names and how
    many vertices changed; each vertex keeps its four strongest weights."""
    points = as_points(positions)
    table = np.asarray(table, dtype=np.float64).reshape(len(points), -1).copy()
    names = list(names)
    columns = {name: index for index, name in enumerate(names)}
    for name in list(names):
        if leg_side(name) is not None and mirrored_bone(name) not in columns:
            columns[mirrored_bone(name)] = len(names)
            names.append(mirrored_bone(name))
            table = np.concatenate([table, np.zeros((len(points), 1))], axis=1)
    pairs = sorted({(columns[n], columns[mirrored_bone(n)]) for n in names if leg_side(n) == "l"})
    if not pairs or not len(points):
        return table, names, 0
    share = _smoothstep((points[:, 0] - centre_x) / (2.0 * max(width, 1e-3)) + 0.5)  # 1: all to the left leg
    blend = _smoothstep((top - points[:, 2]) / max(fade, 1e-3))
    before = table.copy()
    for left, right in pairs:
        both = table[:, left] + table[:, right]
        table[:, left] = (1 - blend) * table[:, left] + blend * share * both
        table[:, right] = (1 - blend) * table[:, right] + blend * (1 - share) * both
    changed = np.abs(table - before).max(axis=1) > 1e-4
    if changed.any():
        table[changed] = limit_influences(table[changed])
    return table, names, int(changed.sum())


def waist_level(positions: Any, pelvis: Any, below: float = 0.02, above: float = 0.3) -> float:
    """Where a dress is narrowest between ``below`` metres under the pelvis marker and ``above`` over it (its waist):
    the level Split at Waist cuts at. Sleeves and anything further than 0.3 m from the centre are left out."""
    points = as_points(positions)
    pelvis = _vec(pelvis)
    near = points[np.abs(points[:, 0] - pelvis[0]) < 0.3]
    best, level = np.inf, float(pelvis[2] + 0.1)
    for z in np.arange(pelvis[2] - below, pelvis[2] + above, 0.01):
        band = near[np.abs(near[:, 2] - z) < 0.006]
        if len(band) < 6:
            continue
        width = float(np.ptp(band[:, 0])) + float(np.ptp(band[:, 1]))
        if width < best:
            best, level = width, float(z)
    return level


#: Generic adult head proportions (metres), nothing measured from the game: the eyes lie this far below the crown, the
#: ear lobes this far below the eyes, the front of a pair of glasses this far in front of the eyes, a watch this far
#: up the forearm from the wrist joint, and a hat's band this much narrower than the head where it sits.
EYES_BELOW_CROWN = 0.115
LOBES_BELOW_EYES = 0.045
GLASSES_AHEAD = 0.012
WATCH_ABOVE_WRIST = 0.035
HAT_EASE = 0.06
#: A slice of a hat goes around the head when its points lie in at least this many of eight directions around the
#: hat's middle. A band does; a chin strap, a chain or cloth hanging down the back does not.
BAND_DIRECTIONS = 7
#: The crown a hat's inside rests on: the top of the head within this distance of its middle seen from above
#: (metres), and the gap the hat keeps above it.
CROWN_RADIUS = 0.03
HAT_CLEARANCE = 0.005


class Snap(NamedTuple):
    """How Snap to Anchor moves a prop: turned by ``degrees`` about ``axis`` through ``pivot`` (the prop's own
    reference point), then moved by ``offset``."""

    offset: Vector
    pivot: Vector
    axis: Vector = (0.0, 0.0, 1.0)
    degrees: float = 0.0

    def apply(self, points: Any) -> np.ndarray:
        turned = rotate_weighted(points, self.pivot, self.axis, self.degrees, np.ones(len(as_points(points))))
        return turned + _vec(self.offset)


def _head(body: np.ndarray, joints: Mapping[str, Any]) -> np.ndarray:
    """The body's head: what lies above the neck joint, near the head joint."""
    full = complete_joints(joints)
    neck, head = full["SKEL_Neck_1"], full["SKEL_Head"]
    near = (body[:, 2] > neck[2] + 0.03) & (np.linalg.norm(body[:, :2] - head[:2], axis=1) < 0.16)
    found = body[near]
    if len(found) < 20:
        raise MarkerError("no-head")
    return found


def _section(points: np.ndarray, z: float, half: float = 0.005) -> Optional[Tuple[np.ndarray, float]]:
    """The middle and half width (across X) of a horizontal slice, or ``None`` when it is (nearly) empty."""
    band = points[np.abs(points[:, 2] - z) <= half]
    if len(band) < 4:
        return None
    return (band[:, :2].min(axis=0) + band[:, :2].max(axis=0)) / 2, float(np.ptp(band[:, 0])) / 2


def _middle(points: np.ndarray) -> np.ndarray:
    """The middle of what ``points`` cover seen from above."""
    return (points[:, :2].min(axis=0) + points[:, :2].max(axis=0)) / 2


def _directions(band: np.ndarray, middle: np.ndarray) -> int:
    """In how many of eight directions around ``middle`` a slice has points."""
    angles = np.arctan2(band[:, 1] - middle[1], band[:, 0] - middle[0])
    return len(np.unique(np.floor((angles + math.pi) / (2 * math.pi) * 8).astype(np.int64).clip(0, 7)))


def _hat_band(points: np.ndarray) -> Tuple[float, float, np.ndarray]:
    """Where a hat sits on the head: its band, the narrowest slice that goes around the head in the lower 40 % of the
    hat (a brim is wider than the band above it). A chin strap, a chain or cloth hanging below the hat does not go
    around the head, so it is never taken for the band. Returns the band's level and half width, and the middle of the
    hat's top (where it covers the crown)."""
    low, high = points.min(axis=0), points.max(axis=0)
    middle = _middle(points[points[:, 2] >= high[2] - 0.3 * (high[2] - low[2])])
    slices = []
    for z in np.arange(low[2] + 0.005, high[2] + 1e-9, 0.005):
        band = points[np.abs(points[:, 2] - z) <= 0.005]
        if len(band) >= 4:
            slices.append((float(z), float(np.ptp(band[:, 0])) / 2, _directions(band, middle)))
    if not slices:
        raise MarkerError("too-small")
    widest = max(half for _, half, _ in slices)
    around = [(z, half) for z, half, directions in slices if directions >= BAND_DIRECTIONS and half >= 0.5 * widest]
    around = around or [(z, half) for z, half, _ in slices]  # nothing goes around the head: the whole prop counts
    bottom = around[0][0]
    lower = [entry for entry in around if entry[0] <= bottom + 0.4 * (high[2] - bottom) + 1e-9]
    level, half = min(lower, key=lambda entry: (entry[1], entry[0]))
    return level, half, _middle(points[points[:, 2] >= high[2] - 0.3 * (high[2] - bottom)])


def _hat_lift(points: np.ndarray, head: np.ndarray, level: float, half: float) -> float:
    """How far up a hat (already over the middle of the head) moves so that its band at ``level`` sits where the
    head is as wide as the band, and so that nothing of the hat above its band sinks into the top of the head: a
    loose helmet rests on the crown, a tall hat on the sides of the head."""
    crown = float(head[:, 2].max())
    sections = []
    for z in np.arange(crown - 0.002, crown - 0.2, -0.005):
        found = _section(head, float(z))
        if found is not None:
            sections.append((float(z), found[1]))
    if not sections:
        raise MarkerError("no-head")
    fitting = [entry for entry in sections if entry[1] >= half * (1.0 - HAT_EASE)]
    lift = (fitting[0] if fitting else max(sections, key=lambda entry: entry[1]))[0] - level
    middle = _middle(head[head[:, 2] >= crown - 0.04])
    over = points[(points[:, 2] >= level) & (np.linalg.norm(points[:, :2] - middle, axis=1) < CROWN_RADIUS)]
    if len(over):
        lift = max(lift, crown + HAT_CLEARANCE - float(over[:, 2].min()))
    return lift


def snap_to_anchor(kind: str, positions: Any, body: Any, joints: Mapping[str, Any], side: str = "l") -> Snap:
    """How to put a prop onto its anchor on the body (``body``: the body's points, ``joints``: its joints), by the
    prop's kind (``hat``, ``glasses``, ``ears`` or ``wrist``; ``side`` of a wrist ``l`` or ``r``). A hat goes over the
    middle of the head and down until its band sits where the head is as wide as it or its inside rests on the crown
    (:func:`_hat_band`, :func:`_hat_lift`), glasses in front of the eyes, ear pieces at the lobes, a watch or bracelet
    around the wrist along the forearm. A starting point to move by hand from. Raises :class:`MarkerError` when the
    body has no head or arm to snap to."""
    points = as_points(positions)
    body = as_points(body)
    if len(points) < 3:
        raise MarkerError("too-small")
    low, high = points.min(axis=0), points.max(axis=0)
    if kind == "wrist":
        full = complete_joints(joints)
        bone = "L" if side == "l" else "R"
        hand, fore = full.get(f"SKEL_{bone}_Hand"), full.get(f"SKEL_{bone}_Forearm")
        if hand is None or fore is None:
            raise MarkerError("no-arm")
        along = _unit(hand - fore)
        target = hand - along * WATCH_ABOVE_WRIST
        centre = points.mean(axis=0)
        values, vectors = np.linalg.eigh(np.cov((points - centre).T))
        normal = vectors[:, 0]  # a band's axis: the direction its points spread least along
        if normal @ along < 0:
            normal = -normal
        axis = np.cross(normal, along)
        degrees = math.degrees(math.atan2(float(np.linalg.norm(axis)), float(np.clip(normal @ along, -1.0, 1.0))))
        if float(np.linalg.norm(axis)) < 1e-9:
            axis, degrees = np.array([0.0, 0.0, 1.0]), 0.0
        return Snap(_tuple(target - centre), _tuple(centre), _tuple(_unit(axis)), degrees)
    head = _head(body, joints)
    crown = float(head[:, 2].max())
    eyes = crown - EYES_BELOW_CROWN
    if kind == "hat":
        level, half, middle = _hat_band(points)
        shift = _middle(head[head[:, 2] >= crown - 0.04]) - middle
        over = points + np.array([shift[0], shift[1], 0.0])
        lift = _hat_lift(over, head, level, half)
        return Snap(_tuple(np.array([shift[0], shift[1], lift])), _tuple(np.array([middle[0], middle[1], level])))
    found = _section(head, eyes, 0.01)
    if found is None:
        raise MarkerError("no-head")
    middle, half = found
    if kind == "glasses":
        level = head[np.abs(head[:, 2] - eyes) < 0.01]
        eye_line = level[np.abs(np.abs(level[:, 0] - middle[0]) - 0.033) < 0.012]
        face = float(eye_line[:, 1].min()) if len(eye_line) else float(level[:, 1].min())
        front = points[points[:, 1] < low[1] + 0.02]
        reference = np.array([(low[0] + high[0]) / 2, low[1], float(front[:, 2].mean())])
        target = np.array([middle[0], face - GLASSES_AHEAD, eyes])
        return Snap(_tuple(target - reference), _tuple(reference))
    lobes = eyes - LOBES_BELOW_EYES
    found = _section(head, lobes, 0.01) or found
    middle, half = found
    reference = np.array([(low[0] + high[0]) / 2, (low[1] + high[1]) / 2, high[2]])
    if float(high[0] - low[0]) > half:  # wider than half the head: a pair for both ears, centred on the head
        x = middle[0]
    else:  # one ear piece: onto the ear on the side it was made on
        x = middle[0] + (half if reference[0] >= middle[0] else -half)
    target = np.array([x, middle[1], lobes])
    return Snap(_tuple(target - reference), _tuple(reference))


#: The furthest a prop's middle may lie from its anchor bone (metres) before Validate says it is not on its anchor.
ANCHOR_LIMIT = 0.35


# --------------------------------------------------------------------------------------------------
# Local checks
# --------------------------------------------------------------------------------------------------

#: Triangles per level of detail above which Durty Cloth Tool's own checks advise reducing the model (its default
#: triangle budgets); the add-on uses the same numbers so it never says clean where Durty Cloth Tool would not.
TRIANGLE_BUDGET = {"high": 30000, "medium": 15000, "low": 7500}
#: The share of High each lower level keeps when its triangle budget is left at 0 (automatic).
LOD_SHARE = {"medium": 0.5, "low": 0.25}
#: The game skins each vertex with at most this many bones.
MAX_INFLUENCES = 4
#: More of the garment inside the body than this share is worth fixing before the game shows it.
INSIDE_SHARE_LIMIT = 0.02
#: A garment whose middle stands further than this from the body (metres) is not on the body at all.
PLACEMENT_LIMIT = 0.15
#: More vertices near the body facing into it than this share means the normals are flipped.
INWARD_LIMIT = 0.5


def lod_budget(level: str, high_triangles: int, chosen: int = 0) -> int:
    """The triangle budget of a lower level of detail: the chosen number, or (0) its share of High, at most the
    budget the checks advise."""
    if chosen > 0:
        return int(chosen)
    return max(4, min(TRIANGLE_BUDGET[level], int(round(LOD_SHARE[level] * high_triangles))))


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
    if stats.get("placement") is not None and stats["placement"] > PLACEMENT_LIMIT:
        add("error", "placement", distance=int(round(float(stats["placement"]) * 100)))
    if stats.get("uv_layers") == 0:
        add("error", "no-uv")
    else:
        if stats.get("uv_outside", 0) > 0:
            add("warning", "uv-outside", count=int(stats["uv_outside"]))
        area = stats.get("uv_area")
        if area is not None and area < 0.05:
            add("warning", "uv-area", area=round(100.0 * float(area), 1))
    if stats.get("prop"):
        pass  # a prop moves with its anchor and has no weights
    elif stats.get("weighted") is False:
        add("error", "no-weights")  # the garment would stay in its rest pose in the game: never clean
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
    for level, budget in TRIANGLE_BUDGET.items():
        count = stats.get(f"triangles_{level}")
        if count is not None and count > budget:
            add("warning", "triangles", level=level, count=int(count), budget=budget)
    share = stats.get("inside_share")
    if share is not None and share > INSIDE_SHARE_LIMIT:
        add("warning", "inside", share=round(100.0 * float(share), 1))
    inward = stats.get("inward_share")
    if inward is not None and inward > INWARD_LIMIT:
        add("warning", "normals-inward", share=int(round(100.0 * float(inward))))
    anchor = stats.get("anchor")
    if anchor is not None and anchor > ANCHOR_LIMIT:
        add("warning", "anchor-far", distance=int(round(float(anchor) * 100)))
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


def limit_influences(weights: Any, limit: int = MAX_INFLUENCES) -> np.ndarray:
    """A vertices-by-groups weight table with only each vertex's ``limit`` strongest weights kept and those summing to
    1 (rows without weight stay empty)."""
    table = np.asarray(weights, dtype=np.float64).copy()
    if table.ndim != 2 or not table.size:
        return table
    if table.shape[1] > limit:
        smallest = np.argsort(table, axis=1)[:, : table.shape[1] - limit]
        np.put_along_axis(table, smallest, 0.0, axis=1)
    table[table < 1e-6] = 0.0
    total = table.sum(axis=1, keepdims=True)
    return np.divide(table, total, out=np.zeros_like(table), where=total > 0)


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
# Units and orientation
# --------------------------------------------------------------------------------------------------


#: The largest dimension, in metres, a garment of each type has (with the arms of an A-pose or a T-pose; see
#: :attr:`GarmentType.size`). Each range spans less than a factor of 10, the step from centimetres to millimetres, so at
#: most one of those units fits.
SIZE_RANGES = {name: kind.size for name, kind in TYPES.items()}
#: The units Import Garment knows, with their factor to metres. Decimetres stand for the FBX files of Marvelous
#: Designer and CLO that Blender reads ten times too large. Inches are tried last: a size that fits both centimetres
#: and inches is far more often centimetres (Marvelous Designer's default).
UNITS = {"m": 1.0, "cm": 0.01, "mm": 0.001, "dm": 0.1, "in": 0.0254}
#: The units Automatic picks without saying so (the usual units of garment files).
USUAL_UNITS = ("m", "cm", "mm")


class ImportedMesh(NamedTuple):
    """One mesh of an imported file, as :func:`avatar_meshes` judges it (sizes in metres)."""

    name: str
    materials: Tuple[str, ...]
    height: float
    largest: float
    #: Closed all round (no open edge), as an avatar's body is and a garment never is.
    closed: bool
    #: The armature that deforms it ("" when none).
    rig: str = ""


#: Words in the names of an avatar's meshes and materials (Marvelous Designer's and CLO's avatars: the body with its
#: face, arms and legs, the eyes, lashes and teeth).
AVATAR_WORDS = frozenset({
    "avatar", "skin", "body", "face", "head", "eye", "eyes", "eyeball", "eyelash", "eyelashes", "eyebrow",
    "eyebrows", "tooth", "teeth", "tongue", "mouth", "arm", "arms", "leg", "legs", "hand", "hands", "foot", "feet",
    "nail", "nails", "hair",
})
#: An avatar's small parts (eyes, lashes, teeth) are no larger than this (metres).
AVATAR_PART_SIZE = 0.25
#: A figure at least this tall (metres) without an open edge is an avatar.
AVATAR_HEIGHT = 1.3


def _avatar_worded(text: str) -> bool:
    return any(word in AVATAR_WORDS for word in re.findall(r"[a-z]+", text.lower()))


def avatar_meshes(meshes: Sequence[ImportedMesh]) -> List[int]:
    """Which meshes of one import are the avatar a clothing app exported with the garment: one named as an avatar or
    wearing only skin, a closed figure as tall as a person, and a rigged avatar: the tallest mesh, deformed by an
    armature and named (or dressed) like a body, with the small parts and the body parts that armature also deforms
    (eyes, lashes, teeth). A garment the same armature deforms (exported with skin weights) stays."""
    found = set()
    for index, mesh in enumerate(meshes):
        materials = [m.lower() for m in mesh.materials]
        if "avatar" in mesh.name.lower() or (materials and all("avatar" in m or "skin" in m for m in materials)):
            found.add(index)
        elif mesh.closed and mesh.height > AVATAR_HEIGHT:
            found.add(index)
    if meshes:
        tallest = max(range(len(meshes)), key=lambda i: meshes[i].height)
        figure = meshes[tallest]
        worded = sum(1 for m in figure.materials if _avatar_worded(m))
        if figure.rig and (_avatar_worded(figure.name) or (figure.materials and 2 * worded >= len(figure.materials))):
            found.add(tallest)
            for index, mesh in enumerate(meshes):
                if mesh.rig != figure.rig or index == tallest:
                    continue
                dressed = bool(mesh.materials) and all(_avatar_worded(m) for m in mesh.materials)
                if mesh.largest < AVATAR_PART_SIZE or dressed or (_avatar_worded(mesh.name) and not mesh.materials):
                    found.add(index)
    return sorted(found)


def import_scale(size: float, category: str = "tshirt", unit: str = "auto") -> float:
    """The factor that brings an imported garment whose largest dimension is ``size`` (Blender units) to metres.
    With ``unit`` ``auto``, the unit whose size fits the category wins (Marvelous Designer files are often in
    centimetres or millimetres, other tools' in inches); a size that fits none is kept as it is."""
    return UNITS[import_unit(size, category, unit) or "m"]


def import_unit(size: float, category: str = "tshirt", unit: str = "auto") -> Optional[str]:
    """The unit :func:`import_scale` reads the garment in, or ``None`` when no unit gives it a garment's size."""
    if unit in UNITS:
        return unit
    for name, factor in UNITS.items():
        if plausible_size(size * factor, category):
            return name
    return None


def plausible_size(size: float, category: str = "tshirt") -> bool:
    """Whether a garment of ``category`` can be ``size`` metres at its largest."""
    low, high = garment_type(category).size
    return low <= size <= high


def upright_turn(positions: Any, category: str) -> Optional[Tuple[str, float]]:
    """How to turn an imported garment that does not stand in ped space: ``("x", ±90)`` for one lying on its back or
    front (its height along Y, from a Y-up export read as Z-up), ``("z", 180)`` for a top facing +Y (its front, where
    the neckline dips lower, at the back). ``None`` when it stands as the ped does, or nothing tells."""
    points = as_points(positions)
    if len(points) < 30 or garment_type(category).family not in ("upper", "lower", "torso"):
        return None
    low, high = points.min(axis=0), points.max(axis=0)
    extent = high - low
    if extent[1] > 1.5 * extent[2] and extent[1] > 0.5 * extent[0]:
        # Lying: which end of Y is the top? Trousers fill their middle at the waist only; a top carries its
        # shoulders, sleeves and collar in its upper half, else (a vest) it is narrower at the neck.
        cx = float(np.median(points[:, 0]))
        middle = (low[1] + high[1]) / 2
        if category in LOWER:
            centre = points[np.abs(points[:, 0] - cx) < 0.02]
            top_is_high_y = bool(len(centre)) and float(centre[:, 1].mean()) > middle
        else:
            lean = (float(points[:, 1].mean()) - middle) / extent[1]
            if abs(lean) > 0.015:
                top_is_high_y = lean > 0
            else:
                widths = []
                for end in (low[1], high[1]):
                    band = points[np.abs(points[:, 1] - end) < 0.15 * extent[1]]
                    widths.append(float(band[:, 0].max() - band[:, 0].min()) if len(band) else 0.0)
                top_is_high_y = widths[1] < widths[0]
        return ("x", 90.0 if top_is_high_y else -90.0)
    if garment_type(category).family != "upper":
        return None  # which way trousers or a bag face, their shape does not tell
    cx = float(np.median(points[:, 0]))
    cy = float((low[1] + high[1]) / 2)
    # A hood or a high collar is the top of the garment and hangs at the back: where the top band sits says which way
    # the garment faces, whatever the neckline under it does.
    band = points[points[:, 2] > high[2] - 0.08]
    if len(band) >= 10 and float(np.ptp(band[:, 0])) < 0.6 * extent[0]:
        lean = (float(band[:, 1].mean()) - cy) / max(extent[1], 1e-6)
        if abs(lean) > 0.12:
            return ("z", 180.0) if lean < 0 else None
    column = points[(np.abs(points[:, 0] - cx) < 0.03) & (points[:, 2] > high[2] - 0.35)]
    front, back = column[column[:, 1] < cy], column[column[:, 1] >= cy]
    if len(front) < 3 or len(back) < 3:
        return None
    if float(front[:, 2].max()) > float(back[:, 2].max()) + 0.02:
        return ("z", 180.0)  # the side towards -Y reaches higher: that is the back of the neckline
    return None
