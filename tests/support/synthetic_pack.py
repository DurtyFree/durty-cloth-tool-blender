# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2026 Schmid Software Solutions (https://schmid-software.de)
"""A synthetic Reference Data Pack in format 1, made from nothing of the game: boxes for the body parts and the
upper-body cuts, a few poses of the synthetic skeleton, and the index and notice that go with them. numpy, json and
struct only, so the Blender smoke can serve the same files from the fake gta.clothing."""

from __future__ import annotations

import json
import math
import struct
from typing import Dict, Iterable, List, Sequence, Tuple

import numpy as np

from tests.support import synthetic

#: The cuts of the synthetic pack: (id, display key, display index, has arms).
CUTS = (
    ("full", "full_body", 1, True),
    ("base", "bare_arms", 1, True),
    ("heist_00", "short_sleeves", 1, True),
    ("heist_01", "short_sleeves", 2, True),
    ("heist_02", "long_sleeves_open_neck", 1, False),
)
#: The poses: (label, the bones each turns with their children, axis, degrees).
POSES = (
    ("idle@0", (), "Z", 0.0),
    ("climb@0.5", ("SKEL_L_UpperArm",), "Y", -70.0),
    ("sit@0.5", ("SKEL_L_Thigh", "SKEL_R_Thigh"), "X", -80.0),
)
FOLDER = "reference"
NOTICE = b"A synthetic Reference Data Pack for the add-on's tests. It holds no game data.\n"


def _json(value: object) -> bytes:
    return (json.dumps(value, separators=(",", ":")) + "\n").encode("ascii")


def box(centre: Sequence[float], size: Sequence[float]) -> Tuple[np.ndarray, np.ndarray]:
    """A closed box in ped space: 8 corners and 12 outward triangles."""
    c, s = np.asarray(centre, dtype=np.float64), np.asarray(size, dtype=np.float64) / 2
    corners = np.array([[x, y, z] for z in (-1, 1) for y in (-1, 1) for x in (-1, 1)], dtype=np.float64) * s + c
    faces = np.array([(0, 2, 1), (1, 2, 3), (4, 5, 6), (5, 7, 6), (0, 1, 4), (1, 5, 4), (2, 6, 3), (3, 6, 7),
                      (0, 4, 2), (2, 4, 6), (1, 3, 5), (3, 7, 5)], dtype=np.int64)
    return corners, faces


def glb(nodes: Iterable[Tuple[str, Dict[str, object], np.ndarray, np.ndarray]]) -> bytes:
    """A plain glTF binary with one node and mesh per ``(name, extras, positions in ped space, triangles)``, in the
    glTF space of the hosted body (Y up)."""
    binary = bytearray()
    views: List[Dict[str, int]] = []
    accessors: List[Dict[str, object]] = []
    meshes: List[Dict[str, object]] = []
    gltf_nodes: List[Dict[str, object]] = []

    def view(data: bytes, target: int) -> int:
        while len(binary) % 4:
            binary.append(0)
        views.append({"buffer": 0, "byteOffset": len(binary), "byteLength": len(data), "target": target})
        binary.extend(data)
        return len(views) - 1

    for name, extras, positions, faces in nodes:
        gl = np.column_stack([positions[:, 0], positions[:, 2], -positions[:, 1]]).astype("<f4")
        accessors.append({"bufferView": view(gl.tobytes(), 34962), "componentType": 5126, "count": len(gl),
                          "type": "VEC3", "min": gl.min(axis=0).tolist(), "max": gl.max(axis=0).tolist()})
        accessors.append({"bufferView": view(np.asarray(faces, dtype="<u2").tobytes(), 34963),
                          "componentType": 5123, "count": int(np.size(faces)), "type": "SCALAR"})
        meshes.append({"name": name, "primitives": [{"attributes": {"POSITION": len(accessors) - 2},
                                                     "indices": len(accessors) - 1, "material": 0}]})
        gltf_nodes.append({"name": name, "mesh": len(meshes) - 1, "extras": extras})
    while len(binary) % 4:
        binary.append(0)
    document = {"asset": {"version": "2.0", "extras": {"referenceFormat": 1}}, "scene": 0,
                "scenes": [{"nodes": list(range(len(gltf_nodes)))}], "nodes": gltf_nodes, "meshes": meshes,
                "materials": [{"name": "dct_skin"}], "accessors": accessors, "bufferViews": views,
                "buffers": [{"byteLength": len(binary)}]}
    text = json.dumps(document, separators=(",", ":")).encode("ascii")
    text += b" " * (-len(text) % 4)
    total = 12 + 8 + len(text) + 8 + len(binary)
    return (struct.pack("<4sII", b"glTF", 2, total) + struct.pack("<I4s", len(text), b"JSON") + text
            + struct.pack("<I4s", len(binary), b"BIN\0") + bytes(binary))


def cut_nodes() -> List[Tuple[str, Dict[str, object], np.ndarray, np.ndarray]]:
    """The parts and cuts as boxes where the synthetic body has them."""
    nodes = [("head", {"part": "head"}, *box((0, 0, 0.64), (0.14, 0.16, 0.28))),
             ("lowr", {"part": "lowr"}, *box((0, 0, -0.5), (0.3, 0.16, 0.9))),
             ("feet", {"part": "feet"}, *box((0, -0.04, -0.97), (0.3, 0.2, 0.06)))]
    for number, (cut, _display, _index, arms) in enumerate(CUTS):
        torso = box((0, 0, 0.17), (0.31 - 0.01 * number, 0.21, 0.65))
        nodes.append((f"uppr_{cut}", {"part": "uppr", "cut": cut, "arms": False}, *torso))
        if arms:
            nodes.append((f"uppr_{cut}_arms", {"part": "uppr", "cut": cut, "arms": True},
                          *box((0.3, 0, 0.3), (0.2 - 0.02 * number, 0.09, 0.09))))
    return nodes


def _turn(head: Sequence[float], axis: str, degrees: float) -> np.ndarray:
    """The skinning matrix of a turn by ``degrees`` about ``axis`` through ``head``."""
    a = math.radians(degrees)
    c, s = math.cos(a), math.sin(a)
    rotation = {"X": [[1, 0, 0], [0, c, -s], [0, s, c]], "Y": [[c, 0, s], [0, 1, 0], [-s, 0, c]],
                "Z": [[c, -s, 0], [s, c, 0], [0, 0, 1]]}[axis]
    matrix = np.eye(4)
    matrix[:3, :3] = rotation
    matrix[:3, 3] = np.asarray(head) - np.asarray(rotation) @ np.asarray(head)
    return matrix


def pose_matrices(turned: Sequence[str], axis: str, degrees: float,
                  bones=synthetic.SKELETON_BONES) -> np.ndarray:
    """One skinning matrix per bone: the bones in ``turned`` and every bone below them turn about their head."""
    names = [name for name, _, _ in bones]
    matrices = np.tile(np.eye(4), (len(bones), 1, 1))
    for start in turned:
        root = names.index(start)
        turn = _turn(bones[root][2], axis, degrees)
        below = {root}
        for index, (_name, parent, _head) in enumerate(bones):
            if parent in below:
                below.add(index)
        for index in below:
            matrices[index] = turn
    return matrices


def poses_file(gender: str, poses=POSES, bones=synthetic.SKELETON_BONES) -> bytes:
    entries = []
    for label, turned, axis, degrees in poses:
        clip, _, phase = label.partition("@")
        matrices = pose_matrices(turned, axis, degrees, bones)
        entries.append({"label": label, "clip": clip, "phase": float(phase),
                        "matrices": [[round(float(v), 6) + 0.0 for v in m.reshape(16)] for m in matrices]})
    return _json({"format": 1, "gender": gender, "space": "ped", "units": "m", "matrix": "skinning-row-major",
                  "bones": [name for name, _, _ in bones], "poses": entries})


def index_entry(gender: str) -> Dict[str, object]:
    return {"cuts": f"cuts_{gender}.glb", "poses": f"poses_{gender}.json", "parts": ["head", "lowr", "feet"],
            "defaultCut": "full", "upperBody": [
                {"id": cut, "node": f"uppr_{cut}", "armsNode": f"uppr_{cut}_arms" if arms else None,
                 "display": display, "displayIndex": index, "skin": ["neck", "hands"]}
                for cut, display, index, arms in CUTS]}


def files(genders: Sequence[str] = ("female", "male")) -> Dict[str, bytes]:
    """Every file of the pack by its name in the ``reference`` folder."""
    skeleton: Dict[str, object] = {"format": 1, "space": "ped", "units": "m"}
    out: Dict[str, bytes] = {"NOTICE.txt": NOTICE}
    cuts = glb(cut_nodes())
    for gender in genders:
        skeleton[gender] = {"ped": f"test_{gender}", "bones": [
            {"name": name, "parent": parent, "tag": index, "head": list(head)}
            for index, (name, parent, head) in enumerate(synthetic.SKELETON_BONES)]}
        out[f"cuts_{gender}.glb"] = cuts
        out[f"poses_{gender}.json"] = poses_file(gender)
    out["skeleton.json"] = _json(skeleton)
    out["reference.json"] = _json({"format": 1, "notice": "NOTICE.txt", "skeleton": "skeleton.json",
                                   "genders": {gender: index_entry(gender) for gender in genders}})
    return out


def body_files(genders: Sequence[str] = ("female", "male")) -> Dict[str, bytes]:
    """The pack as the fake gta.clothing serves it: in the ``reference`` folder of the body version."""
    return {served(name): data for name, data in files(genders).items()}


def served(name: str) -> str:
    """A pack file's name below the body version."""
    return f"{FOLDER}/{name}"
