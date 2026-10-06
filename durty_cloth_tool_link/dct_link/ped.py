# SPDX-License-Identifier: MIT
# Copyright (c) Schmid Software Solutions (https://schmid-software.de)
"""Custom peds from a character (protocol README "Custom peds"): the payloads of ``ped.rig``, ``ped.skeleton.data``
and ``ped.rig.result``, and how a GLB travels in ``ped.add.chunk`` frames.

Coordinates are ped space metres: +Z up, the ped facing -Y, its left at +X. Matrices are 16 floats, row major, in the
row-vector convention (a point is the row ``[x y z 1]`` times the matrix; the last row is the bone's position).
Standard library only.
"""

from __future__ import annotations

import array
import hashlib
import struct
import sys
from typing import Any, Dict, List, Mapping, NamedTuple, Optional, Sequence, Tuple, Union

from . import protocol

__all__ = [
    "PedBone",
    "PedSkeleton",
    "PedRig",
    "PedRigPayload",
    "decode_ped_skeleton",
    "decode_ped_rig",
    "prepare_ped_rig",
    "plan_ped_add_upload",
]

_RECORD = struct.Struct("<HhI4f3f16f")  # tag, parent, flags, rotation, translation, world: 100 bytes
_POSE = struct.Struct("<16f")


class PedBone(NamedTuple):
    """One bone of a template or a rig, in the skeleton's order. ``parent`` is the parent's index (-1 for the root);
    ``rotation`` (x, y, z, w) is the local rest rotation, always the template's own; ``translation`` the local rest
    translation; ``world`` the rest world matrix (16 floats)."""

    name: str
    tag: int
    parent: int
    flags: int
    rotation: Tuple[float, float, float, float]
    translation: Tuple[float, float, float]
    world: Tuple[float, ...]


class PedSkeleton(NamedTuple):
    """A template's rest skeleton (``ped.skeleton.data``)."""

    model: str
    gender: Optional[str]
    layout: str
    ragdoll: str
    bones: List[PedBone]
    ok: bool = True


class PedRig(NamedTuple):
    """A computed rig (``ped.rig.result``). ``bones`` carry the fitted local translations and the rest world matrices G;
    ``poses`` holds each bone's world matrix P in the character's own pose. Per vertex, in the request's vertex order:
    ``rest_positions`` (x, y, z floats: the character in the game's rest pose), ``bone_indices`` and ``weights`` (four
    bytes each, strongest first, a vertex's weights summing to 255). ``report`` is DCT's quality report as sent."""

    job: str
    template: str
    ragdoll: str
    bones: List[PedBone]
    poses: List[Tuple[float, ...]]
    rest_positions: "array.array[float]"
    bone_indices: bytes
    weights: bytes
    report: Dict[str, Any]
    ok: bool = True


def _bones(names: Sequence[str], payload: memoryview) -> List[PedBone]:
    bones = []
    for index, name in enumerate(names):
        values = _RECORD.unpack_from(payload, index * protocol.PED_BONE_RECORD_BYTES)
        bones.append(PedBone(name, values[0], values[1], values[2], values[3:7], values[7:10], values[10:26]))
    return bones


def decode_ped_skeleton(frame: protocol.BinaryMessage) -> PedSkeleton:
    """A template's skeleton from a decoded ``ped.skeleton.data`` frame (the codec checked the payload's size)."""
    header = frame.header
    return PedSkeleton(header["model"], header.get("gender"), header["layout"], header["ragdoll"],
                       _bones(header["bones"], memoryview(frame.payload).cast("B")))


def decode_ped_rig(frame: protocol.BinaryMessage) -> PedRig:
    """A rig from a decoded ``ped.rig.result`` frame with ``ok`` true (the codec checked the payload's size)."""
    header = frame.header
    if not header.get("ok"):
        raise ValueError("only a successful ped.rig.result carries a rig")
    names, vertices = header["bones"], header["vertices"]
    payload = memoryview(frame.payload).cast("B")
    bones = _bones(names, payload)
    offset = len(names) * protocol.PED_BONE_RECORD_BYTES
    poses = []
    for _ in names:
        poses.append(_POSE.unpack_from(payload, offset))
        offset += _POSE.size
    rest = array.array("f")
    rest.frombytes(payload[offset : offset + 12 * vertices].tobytes())
    if sys.byteorder == "big":
        rest.byteswap()
    offset += 12 * vertices
    indices = payload[offset : offset + 4 * vertices].tobytes()
    offset += 4 * vertices
    weights = payload[offset : offset + 4 * vertices].tobytes()
    return PedRig(header["job"], header["template"], header["ragdoll"], bones, poses, rest, indices, weights,
                  dict(header["report"]))


Numbers = Union[Sequence[float], Any]


def _little_endian(values: Any, typecode: str, formats: Tuple[str, ...], what: str) -> memoryview:
    """``values`` as little-endian 4-byte items: a buffer of that type (a NumPy ``float32`` or ``uint32`` array,
    ``array.array``) without a copy, anything else converted."""
    try:
        view = memoryview(values)
    except TypeError:
        view = None
    if view is not None and view.itemsize == 4 and view.format.lstrip("<=@") in formats and sys.byteorder == "little":
        return view.cast("B") if view.c_contiguous else memoryview(view.tobytes())
    try:
        converted = array.array(typecode, values if view is None else view.tolist())
    except (TypeError, OverflowError, ValueError):
        raise ValueError(f"{what} holds numbers of the wrong kind") from None
    if converted.itemsize != 4:
        raise ValueError(f"{what} needs 4-byte items")
    if sys.byteorder == "big":
        converted.byteswap()
    return memoryview(converted).cast("B")


class PedRigPayload(NamedTuple):
    """The checked parts of a ``ped.rig``: its header (without an id) and its payload as views, in order."""

    header: Dict[str, Any]
    parts: Tuple[memoryview, ...]
    size: int


def prepare_ped_rig(
    template: str,
    markers: Mapping[str, Sequence[float]],
    positions: Numbers,
    triangles: Numbers,
    *,
    rights_confirmed: bool,
    parts: Optional[Sequence[str]] = None,
    part_ids: Optional[Any] = None,
    options: Optional[Mapping[str, Any]] = None,
) -> PedRigPayload:
    """Checks a rig request with the codec's rules before anything is sent and lays out its payload: positions (x, y,
    z per vertex), triangles (three vertex indices each) and, with ``parts``, one part id per vertex indexing them.
    Raises ``ValueError`` with the rule that failed."""
    if rights_confirmed is not True:
        raise ValueError("the user has not confirmed the rights notice for this character; DCT refuses a rig without it")
    if not protocol.is_ped_model(template):
        raise ValueError("template is a ped model name (a ped.templates.list model)")
    problem = protocol.ped_markers_problem(markers)
    if problem is not None or not markers:
        raise ValueError(problem or "a rig needs its markers")
    point_bytes = _little_endian(positions, "f", ("f",), "positions")
    index_bytes = _little_endian(triangles, "I", ("I", "L", "i", "l"), "triangles")
    if point_bytes.nbytes % 12 or index_bytes.nbytes % 12:
        raise ValueError("positions hold x, y and z per vertex and triangles three indices each")
    vertices, count = point_bytes.nbytes // 12, index_bytes.nbytes // 12
    if vertices > protocol.MAX_PED_RIG_VERTICES or count > protocol.MAX_PED_RIG_TRIANGLES:
        raise ValueError(f"a rig takes at most {protocol.MAX_PED_RIG_VERTICES} vertices and "
                         f"{protocol.MAX_PED_RIG_TRIANGLES} triangles; decimate a copy first")
    indices = index_bytes.cast("I")
    if any(index >= vertices for index in indices):
        raise ValueError("a triangle addresses a vertex that does not exist")
    roles = list(parts or [])
    payload: List[memoryview] = [point_bytes, index_bytes]
    if roles:
        if len(roles) > protocol.MAX_PED_RIG_PARTS or any(role not in protocol.PED_PART_ROLES for role in roles):
            raise ValueError("parts lists up to 64 part roles (protocol.PED_PART_ROLES)")
        if part_ids is None:
            raise ValueError("with parts, every vertex names its part")
        ids = memoryview(bytes(part_ids)) if not isinstance(part_ids, (bytes, bytearray, memoryview)) else memoryview(part_ids).cast("B")
        if ids.nbytes != vertices or any(part >= len(roles) for part in ids):
            raise ValueError("part ids name one listed part per vertex")
        payload.append(ids)
    elif part_ids is not None:
        raise ValueError("part ids need parts")
    header: Dict[str, Any] = {
        "type": "ped.rig", "template": template, "rights": True,
        "markers": {name: [float(c) for c in point] for name, point in markers.items()},
        "mesh": {"vertices": vertices, "triangles": count, "parts": roles},
    }
    if options:
        header["options"] = dict(options)
    size = sum(part.nbytes for part in payload)
    try:
        protocol.encode_binary_header(dict(header, id="x" * protocol.MAX_ID_LENGTH), size)
    except protocol.ProtocolError as exc:
        raise ValueError(f"DCT would refuse this ped.rig ({exc.code})") from None
    return PedRigPayload(header, tuple(payload), size)


def plan_ped_add_upload(glb: Any) -> Tuple[str, List[memoryview]]:
    """The SHA-256 (lowercase hex) of ``glb`` and its fewest chunks of at most ``MAX_PED_ADD_CHUNK_BYTES``, of nearly
    equal size, as views (no copy). Raises ``ValueError`` beyond the limits."""
    view = memoryview(glb).cast("B")
    size = view.nbytes
    if not 20 <= size <= protocol.MAX_PED_ADD_BYTES:
        raise ValueError(f"a ped.add GLB is 20 bytes to {protocol.MAX_PED_ADD_BYTES // (1024 * 1024)} MiB")
    count = -(-size // protocol.MAX_PED_ADD_CHUNK_BYTES)
    step = -(-size // count)
    return hashlib.sha256(view).hexdigest(), [view[start : start + step] for start in range(0, size, step)]
