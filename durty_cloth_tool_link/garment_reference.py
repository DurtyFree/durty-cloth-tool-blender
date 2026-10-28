# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2026 Schmid Software Solutions (https://schmid-software.de)
# Copyright (c) 2026 muto
"""The Reference Data Pack: reference data for the local garment tools that comes only with the hosted freemode body.

A hosted body version may list a ``reference`` folder: an index (``reference.json``), the notice that names who owns
the data and who prepared it, a skeleton, and per gender the upper-body cuts as a plain GLB and a set of poses. The
add-on keeps it in ``body/<version>/reference/`` with a record of every file's size and SHA-256, uses it only while
that record still matches, and deletes it once the current body version no longer lists it (a withdrawal). Nothing
of it is ever part of the add-on or of this repository. This module reads and checks the files; it does no network
work and imports nothing from Blender.
"""

from __future__ import annotations

import hashlib
import json
import os
import pathlib
import re
import shutil
import struct
import tempfile
import time
from typing import Any, Dict, List, Mapping, NamedTuple, Optional, Tuple

import numpy as np

#: The pack format this add-on reads.
FORMAT = 1
#: The pack's folder below a body version, its index, and the add-on's record of what it kept.
FOLDER = "reference"
INDEX = "reference.json"
STAMP = ".kept.json"
GENDERS = ("female", "male")
#: Size limits per file kind and for the whole pack (the pack of 2026 is about 3.4 MB in all).
MAX_INDEX_BYTES = 256 * 1024
MAX_JSON_BYTES = 16 * 1024 * 1024
MAX_GLB_BYTES = 32 * 1024 * 1024
MAX_TEXT_BYTES = 64 * 1024
MAX_PACK_BYTES = 128 * 1024 * 1024
#: The plain names of what skin a cut shows, which the panel translates.
DISPLAY_KEYS = ("full_body", "bare_arms", "bare_arms_open_neck", "short_sleeves", "short_sleeves_open_neck",
                "long_sleeves", "long_sleeves_open_neck")
FULL_CUT = "full"
_NAME = re.compile(r"[A-Za-z0-9_]{1,40}\.(json|glb|txt)")
_ID = re.compile(r"[a-z0-9_]{1,32}")
_KEY = re.compile(r"[a-z0-9_]{1,40}")
_TEMPORARY = ".reference-"


class PackError(ValueError):
    """A pack file that is not what format 1 describes."""


class Cut(NamedTuple):
    """One upper-body cut: the node with its torso and hands, the node with its arms (``None`` when no arm shows),
    the plain name of what skin shows and its number among cuts with that name."""

    id: str
    node: str
    arms_node: Optional[str]
    display: str
    display_index: int


class GenderPack(NamedTuple):
    cuts: str
    poses: str
    parts: Tuple[str, ...]
    default_cut: str
    upper_body: Tuple[Cut, ...]


class ReferenceIndex(NamedTuple):
    notice: str
    skeleton: str
    genders: Dict[str, GenderPack]

    def files(self) -> List[str]:
        """Every file the index names besides itself, the notice first."""
        names = [self.notice, self.skeleton]
        for gender in sorted(self.genders):
            names += [self.genders[gender].cuts, self.genders[gender].poses]
        return list(dict.fromkeys(names))


class Pack(NamedTuple):
    """A kept pack: its folder, the body version it came with and its index."""

    folder: pathlib.Path
    version: str
    index: ReferenceIndex


def _name(value: Any) -> str:
    # Windows ignores case in file names: a name that is the index's or the record's in any case would overwrite it.
    if not isinstance(value, str) or not _NAME.fullmatch(value) or value.lower() in (INDEX.lower(), STAMP.lower()):
        raise PackError("a file name the pack may not use")
    return value


def _json(data: bytes, limit: int) -> Any:
    if len(data) > limit:
        raise PackError("too large")
    try:
        return json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        raise PackError("not JSON") from None


def _cut(value: Any) -> Cut:
    if not isinstance(value, dict) or not isinstance(value.get("id"), str) or not _ID.fullmatch(value["id"]):
        raise PackError("a cut without a valid id")
    node = f"uppr_{value['id']}"
    arms = value.get("armsNode")
    display, number = value.get("display"), value.get("displayIndex")
    if value.get("node") != node or arms not in (None, node + "_arms"):
        raise PackError("a cut whose nodes do not follow its id")
    if not isinstance(display, str) or not _KEY.fullmatch(display):
        raise PackError("a cut without a display name")
    if not isinstance(number, int) or isinstance(number, bool) or not 1 <= number <= 999:
        raise PackError("a cut without a display number")
    return Cut(value["id"], node, arms, display, number)


def parse_index(data: bytes) -> ReferenceIndex:
    """Reads ``reference.json`` (format 1); raises :class:`PackError` for anything else."""
    value = _json(data, MAX_INDEX_BYTES)
    if not isinstance(value, dict) or value.get("format") != FORMAT or not isinstance(value.get("genders"), dict):
        raise PackError("not a format 1 index")
    genders: Dict[str, GenderPack] = {}
    for gender, entry in value["genders"].items():
        if gender not in GENDERS or not isinstance(entry, dict):
            raise PackError("an unknown gender")
        cuts = tuple(_cut(c) for c in entry.get("upperBody") or [])
        ids = [cut.id for cut in cuts]
        parts = entry.get("parts")
        if not cuts or len(set(ids)) != len(ids) or entry.get("defaultCut") not in ids:
            raise PackError("cuts without a default or with an id twice")
        if not isinstance(parts, list) or not all(isinstance(p, str) and _ID.fullmatch(p) for p in parts):
            raise PackError("parts that are not names")
        genders[gender] = GenderPack(_name(entry.get("cuts")), _name(entry.get("poses")), tuple(parts),
                                     entry["defaultCut"], cuts)
    if not genders:
        raise PackError("no gender")
    index = ReferenceIndex(_name(value.get("notice")), _name(value.get("skeleton")), genders)
    names = index.files()
    if len({name.lower() for name in names}) != len(names):
        raise PackError("two file names that differ only in case")  # one file on Windows
    return index


def limit_of(name: str) -> int:
    """The most bytes a pack file of this name may have."""
    return {".glb": MAX_GLB_BYTES, ".txt": MAX_TEXT_BYTES}.get(pathlib.PurePath(name).suffix, MAX_JSON_BYTES)


def check_file(name: str, data: bytes) -> None:
    """Raises :class:`PackError` unless ``data`` is a file of the kind its name says, within its limit: a notice in
    UTF-8, a JSON object, or a plain GLB (no required extension)."""
    if len(data) > limit_of(name):
        raise PackError("too large")
    suffix = pathlib.PurePath(name).suffix
    if suffix == ".txt":
        try:
            data.decode("utf-8")
        except UnicodeDecodeError:
            raise PackError("a notice that is not text") from None
    elif suffix == ".json":
        if not isinstance(_json(data, MAX_JSON_BYTES), dict):
            raise PackError("not a JSON object")
    else:
        header = _glb_json(data)
        if header.get("extensionsRequired"):
            raise PackError("a GLB that needs an extension")


def _record(files: Mapping[str, bytes]) -> bytes:
    entries = {name: {"size": len(data), "sha256": hashlib.sha256(data).hexdigest()}
               for name, data in sorted(files.items())}
    return json.dumps({"format": FORMAT, "files": entries}, separators=(",", ":")).encode("ascii")


def keep_pack(version_folder: pathlib.Path, files: Mapping[str, bytes]) -> pathlib.Path:
    """Writes a downloaded pack into ``<version_folder>/reference`` all at once: into a temporary folder first, with
    the record of every file's size and SHA-256, which then replaces any pack kept there."""
    version_folder.mkdir(parents=True, exist_ok=True)
    temporary = pathlib.Path(tempfile.mkdtemp(prefix=_TEMPORARY, dir=version_folder))
    target = version_folder / FOLDER
    try:
        for name, data in files.items():
            (temporary / name).write_bytes(data)
        (temporary / STAMP).write_bytes(_record(files))
        if target.exists():
            shutil.rmtree(target)
        for attempt in range(20):
            try:
                os.replace(temporary, target)
                break
            except PermissionError:
                if attempt == 19:
                    raise
                time.sleep(0.1)  # a virus scanner may still hold a file it was just handed (worker thread only)
    except OSError:
        shutil.rmtree(temporary, ignore_errors=True)
        raise
    return target


def kept_pack(version_folder: pathlib.Path, verify: bool = True) -> Optional[Pack]:
    """The pack kept with a body version while every file still matches its record (with ``verify``, also its
    SHA-256); ``None`` otherwise."""
    folder = version_folder / FOLDER
    try:
        record = json.loads((folder / STAMP).read_text("utf-8"))
        entries = record["files"]
        if record.get("format") != FORMAT or not isinstance(entries, dict) or INDEX not in entries:
            return None
        for name, entry in entries.items():
            path = folder / (name if name == INDEX else _name(name))
            if path.stat().st_size != entry["size"]:
                return None
            if verify and hashlib.sha256(path.read_bytes()).hexdigest() != entry["sha256"]:
                return None
        index = parse_index((folder / INDEX).read_bytes())
        if any(name not in entries for name in index.files()):
            return None
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return None
    return Pack(folder, version_folder.name, index)


def remove_withdrawn(body_root: pathlib.Path, current: Optional[str]) -> List[str]:
    """Deletes every kept pack but the one of the ``current`` body version (``None``: every one), and what a broken
    download left. Returns the versions whose pack was deleted."""
    removed: List[str] = []
    try:
        versions = [p for p in body_root.iterdir() if p.is_dir()]
    except OSError:
        return removed
    for version in versions:
        try:
            for leftover in version.glob(_TEMPORARY + "*"):
                shutil.rmtree(leftover, ignore_errors=True)
            if version.name != current and (version / FOLDER).exists():
                shutil.rmtree(version / FOLDER)
                removed.append(version.name)
        except OSError:
            continue  # tried again with the next body download
    return removed


# --------------------------------------------------------------------------------------------------
# The body view: Body Cut, Arms and Legs
# --------------------------------------------------------------------------------------------------

# The body view (a cut's torso, its arms solid, as a wireframe or hidden, and the legs alike) follows Muto
# Cloth's reference body view by muto.

#: How the body's arms and its legs can show.
VIEW_MODES = ("solid", "wire", "hidden")
#: The part the Legs setting shows.
LEGS_PART = "lowr"


class CutChoice(NamedTuple):
    """One Body Cut choice: the cut, the plain name of what skin shows (``other`` for a name the add-on does not
    know), and its number when several cuts show the same skin (``None`` otherwise)."""

    id: str
    display: str
    number: Optional[int]


def cut_choices(index: Optional[ReferenceIndex], gender: str) -> List[CutChoice]:
    """Body Cut's choices for a gender in the pack's order (the full body first); none without a pack."""
    entry = index.genders.get(gender) if index is not None else None
    if entry is None:
        return []
    shared: Dict[str, int] = {}
    for cut in entry.upper_body:
        shared[cut.display] = shared.get(cut.display, 0) + 1
    return [CutChoice(cut.id, cut.display if cut.display in DISPLAY_KEYS else "other",
                      cut.display_index if shared[cut.display] > 1 else None) for cut in entry.upper_body]


#: The plain name of the cut gloves are judged against: the bare arms they carry in the game.
GLOVES_DISPLAY = "bare_arms"


def gloves_cut(index: Optional[ReferenceIndex], gender: str) -> Optional[str]:
    """The Body Cut picking Gloves switches to: the pack's first bare-arms cut of the gender, or ``None`` (no pack, or
    none in it), when Body Cut stays as it is."""
    return next((choice.id for choice in cut_choices(index, gender) if choice.display == GLOVES_DISPLAY), None)


class ViewParts(NamedTuple):
    """The pack's nodes a view shows solid and as a wireframe."""

    solid: Tuple[str, ...]
    wire: Tuple[str, ...]


def _cut_of(entry: GenderPack, cut_id: str) -> Cut:
    for cut in entry.upper_body:
        if cut.id == cut_id:
            return cut
    return next(cut for cut in entry.upper_body if cut.id == entry.default_cut)


def standard_view(entry: GenderPack, cut_id: str, arms: str, legs: str) -> bool:
    """Whether the settings ask for the body as it is: the default cut (or none chosen yet), arms and legs solid."""
    return _cut_of(entry, cut_id).id == entry.default_cut and arms == "solid" and legs == "solid"


def view_parts(entry: GenderPack, cut_id: str, arms: str, legs: str) -> ViewParts:
    """Which nodes show for a Body Cut (an unknown one is the default cut) and the Arms and Legs settings: the parts
    and the cut's torso with its hands always solid, its arms and the legs as their setting says."""
    if arms not in VIEW_MODES or legs not in VIEW_MODES:
        raise ValueError("unknown view mode")
    cut = _cut_of(entry, cut_id)
    solid = [part for part in entry.parts if part != LEGS_PART] + [cut.node]
    wire: List[str] = []
    for node, mode in ((cut.arms_node, arms), (LEGS_PART if LEGS_PART in entry.parts else None, legs)):
        if node is not None and mode != "hidden":
            (solid if mode == "solid" else wire).append(node)
    return ViewParts(tuple(solid), tuple(wire))


# --------------------------------------------------------------------------------------------------
# Reading the pack's files
# --------------------------------------------------------------------------------------------------


def _glb_json(data: bytes) -> Dict[str, Any]:
    try:
        magic, _version, total = struct.unpack_from("<4sII", data, 0)
        length, kind = struct.unpack_from("<I4s", data, 12)
        if magic != b"glTF" or kind != b"JSON" or total > len(data) or 20 + length > len(data):
            raise PackError("not a GLB")
        header = json.loads(bytes(data[20:20 + length]).decode("utf-8"))
    except (struct.error, UnicodeDecodeError, ValueError) as exc:
        raise PackError("not a GLB") from exc
    if not isinstance(header, dict):
        raise PackError("not a GLB")
    return header


_COMPONENTS = {5121: "<u1", 5123: "<u2", 5125: "<u4", 5126: "<f4"}
_WIDTH = {"SCALAR": 1, "VEC3": 3}


def _accessor(header: Dict[str, Any], binary: memoryview, index: Any, kind: str) -> np.ndarray:
    accessor = header["accessors"][index]
    view = header["bufferViews"][accessor["bufferView"]]
    dtype = np.dtype(_COMPONENTS[accessor["componentType"]])
    width = _WIDTH[kind]
    if accessor.get("type") != kind or view.get("byteStride", dtype.itemsize * width) != dtype.itemsize * width:
        raise PackError("an accessor of another kind")
    start = view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
    count = accessor["count"] * width
    if start + count * dtype.itemsize > len(binary):
        raise PackError("an accessor past the end of the data")
    return np.frombuffer(binary, dtype=dtype, count=count, offset=start).reshape(-1, width)


def read_cuts(data: bytes) -> Dict[str, Tuple[np.ndarray, np.ndarray]]:
    """The meshes of a cuts GLB by node name: positions in ped space (Z up, metres) and triangles."""
    check_file("cuts.glb", data)
    header = _glb_json(data)
    offset = 20 + struct.unpack_from("<I", data, 12)[0]
    try:
        length, kind = struct.unpack_from("<I4s", data, offset)
    except struct.error:
        raise PackError("a GLB without data") from None
    if kind != b"BIN\0" or offset + 8 + length > len(data):
        raise PackError("a GLB without data")
    binary = memoryview(data)[offset + 8:offset + 8 + length]
    meshes: Dict[str, Tuple[np.ndarray, np.ndarray]] = {}
    try:
        for node in header.get("nodes", []):
            if "mesh" not in node or not isinstance(node.get("name"), str):
                continue
            if any(key in node for key in ("matrix", "rotation", "scale", "translation", "children")):
                raise PackError("a node that is moved")
            positions, triangles = [], []
            count = 0
            for primitive in header["meshes"][node["mesh"]]["primitives"]:
                if primitive.get("mode", 4) != 4:
                    raise PackError("a primitive that is not triangles")
                gl = _accessor(header, binary, primitive["attributes"]["POSITION"], "VEC3").astype(np.float64)
                faces = _accessor(header, binary, primitive["indices"], "SCALAR").astype(np.int64).reshape(-1, 3)
                if len(faces) and (faces.min() < 0 or faces.max() >= len(gl)):
                    raise PackError("a triangle past the vertices")
                positions.append(np.column_stack([gl[:, 0], -gl[:, 2], gl[:, 1]]))  # glTF Y up to ped Z up
                triangles.append(faces + count)
                count += len(gl)
            if positions:
                meshes[node["name"]] = (np.concatenate(positions), np.concatenate(triangles))
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        if isinstance(exc, PackError):
            raise
        raise PackError("a GLB that is not what the pack describes") from exc
    return meshes


class PoseSet(NamedTuple):
    """The poses of one gender: their labels, the bone order, and one skinning matrix per pose and bone ``(P, B, 4,
    4)`` that moves a rest position weighted to that bone into the pose."""

    labels: Tuple[str, ...]
    bones: Tuple[str, ...]
    matrices: np.ndarray


def read_poses(data: bytes) -> PoseSet:
    """Reads a ``poses_<gender>.json`` of format 1."""
    value = _json(data, MAX_JSON_BYTES)
    if (not isinstance(value, dict) or value.get("format") != FORMAT or value.get("space") != "ped"
            or value.get("units") != "m" or value.get("matrix") != "skinning-row-major"):
        raise PackError("not format 1 poses")
    bones, poses = value.get("bones"), value.get("poses")
    if not isinstance(bones, list) or not bones or not all(isinstance(b, str) for b in bones):
        raise PackError("poses without bones")
    if not isinstance(poses, list) or not poses:
        raise PackError("no poses")
    labels: List[str] = []
    rows = []
    for pose in poses:
        if not isinstance(pose, dict) or not isinstance(pose.get("label"), str):
            raise PackError("a pose without a label")
        labels.append(pose["label"])
        rows.append(pose.get("matrices"))
    try:
        matrices = np.asarray(rows, dtype=np.float64)
    except (TypeError, ValueError):
        raise PackError("matrices that are not numbers") from None
    if matrices.shape != (len(poses), len(bones), 16) or not np.isfinite(matrices).all():
        raise PackError("not one matrix per pose and bone")
    return PoseSet(tuple(labels), tuple(bones), matrices.reshape(len(poses), len(bones), 4, 4))
