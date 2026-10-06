# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2026 Schmid Software Solutions (https://schmid-software.de)
"""The garment fitting tools in Blender: reading and writing the garment's mesh, the body and its joints, markers,
aligning the garment to the body, backups, the problem colours, the sculpt session, the moves against the body, the
T-pose conversion, checking tears, and the game-ready steps (prepare, combine materials, levels of detail, the local
checks).

Only the garment chosen in the panel, its markers and the body the add-on added are changed; the maths lives in
:mod:`garment`.
"""

from __future__ import annotations

import math
import pathlib
import secrets
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

from . import garment, garment_fit
from .strings import UserError, msg

#: Custom properties the add-on keeps on the garment (and the .blend file keeps with it).
GARMENT_TAG = "dct_garment"
#: A garment's own id (its markers carry it), kept across renames and file reloads.
GARMENT_ID = "dct_garment_id"
#: The backups: up to :data:`MAX_BACKUPS` meshes the garment references (so they go with it when it is deleted).
BACKUP_SLOTS = ("dct_backup_0", "dct_backup_1", "dct_backup_2")
#: Older files listed their backups by name (with fake users); they are taken over by the slots.
BACKUPS = "dct_fit_backups"
FLAGS = ("dct_aligned", "dct_converted", "dct_fitted", "dct_checked", "dct_prepared", "dct_lods", "dct_validated")
#: The garment's latest fit check and local checks (JSON), kept with it so they always belong to this garment.
FIT_REPORT = "dct_fit_report"
FINDINGS = "dct_findings"
#: What the latest changes leave stale: the fit check, the local checks and the levels of detail.
STALE = ("dct_checked", FIT_REPORT, "dct_validated", FINDINGS, "dct_lods")
#: The body the add-on added: its gender, the hosted version it came from, and its joints (JSON, see
#: :func:`garment.parse_joints`) with where they came from.
BODY_TAG = "dct_body"
BODY_VERSION = "dct_body_version"
JOINTS_TAG = "dct_joints"
MARKER_TAG = "dct_marker"
MARKER_OWNER = "dct_marker_of"
MARKER_COLLECTION = "DCT Garment Markers"
BODY_COLLECTION = "DCT Freemode Body"
MARKER_PREFIX = "DCT_"
#: The problem colours (a colour attribute the panel adds and removes; Prepare removes it too).
PROBLEMS = "DCT Problems"
#: The garment's shape before a sculpt session (a point attribute while the session runs).
PRESCULPT = "dct_presculpt"
SCULPT_STATE = "dct_sculpt"
SCULPT_MASK = ".sculpt_mask"
#: The UV layout Combine Materials bakes into, as Sollumz names the first UV map, and the one it keeps.
PACKED_UV = "UVMap 0"
SOURCE_UV = "DCT Source UV"
#: The vertex colours the ped shader reads, as Sollumz names them.
COLOUR_ATTRIBUTES = ("Color 1", "Color 2")
TEARS_GROUP = "DCT Tears"
#: Vertex groups the user can set: vertices the tools never move, and a lining that is never welded to its shell.
PINNED_GROUP = "DCT Pinned"
LINING_GROUP = "DCT Lining"
TOOL_GROUPS = (TEARS_GROUP, PINNED_GROUP, LINING_GROUP)
#: The most backups kept per garment: the first (the shape before any fitting) and the newest ones.
MAX_BACKUPS = len(BACKUP_SLOTS)


def fail(key: str, **fields: Any) -> UserError:
    return UserError(msg(key, **fields))


class Progress:
    """Blender's progress indicator (the cursor shows the percentage) for a step that takes a while."""

    def __init__(self, steps: int) -> None:
        self.steps = max(1, steps)
        self.done = 0
        self.wm = getattr(bpy.context, "window_manager", None)
        if self.wm is not None:
            try:
                self.wm.progress_begin(0, self.steps)
            except (RuntimeError, AttributeError):
                self.wm = None

    def step(self, count: int = 1) -> None:
        self.done = min(self.steps, self.done + count)
        if self.wm is not None:
            self.wm.progress_update(self.done)

    def end(self) -> None:
        if self.wm is not None:
            self.wm.progress_end()
            self.wm = None


# --------------------------------------------------------------------------------------------------
# The garment's mesh
# --------------------------------------------------------------------------------------------------


def world_positions(obj: Any) -> np.ndarray:
    return mesh_positions(obj.data, obj.matrix_world)


def mesh_positions(mesh: Any, matrix: Any) -> np.ndarray:
    local = np.empty(len(mesh.vertices) * 3, dtype=np.float64)
    mesh.vertices.foreach_get("co", local)
    local = local.reshape(-1, 3)
    m = np.array(matrix, dtype=np.float64)
    return local @ m[:3, :3].T + m[:3, 3]


def set_world_positions(obj: Any, positions: np.ndarray) -> None:
    set_mesh_positions(obj.data, obj.matrix_world, positions)


def set_mesh_positions(mesh: Any, matrix: Any, positions: np.ndarray) -> None:
    inverse = np.array(matrix.inverted(), dtype=np.float64)
    local = np.asarray(positions, dtype=np.float64) @ inverse[:3, :3].T + inverse[:3, 3]
    mesh.vertices.foreach_set("co", local.astype(np.float32).reshape(-1))
    mesh.update()


def vertex_normals(obj: Any) -> np.ndarray:
    """Unit vertex normals in world space."""
    mesh = obj.data
    values = np.empty(len(mesh.vertices) * 3, dtype=np.float64)
    try:
        mesh.vertex_normals.foreach_get("vector", values)
    except AttributeError:  # an older Blender: the normals live on the vertices
        mesh.vertices.foreach_get("normal", values)
    turn = np.array(obj.matrix_world.to_3x3().inverted().transposed(), dtype=np.float64)
    normals = values.reshape(-1, 3) @ turn.T
    lengths = np.linalg.norm(normals, axis=1, keepdims=True)
    return np.divide(normals, lengths, out=np.zeros_like(normals), where=lengths > 1e-12)


def mesh_edges(mesh: Any) -> np.ndarray:
    edges = np.empty(len(mesh.edges) * 2, dtype=np.int64)
    mesh.edges.foreach_get("vertices", edges)
    return edges.reshape(-1, 2)


def mesh_triangles(mesh: Any) -> np.ndarray:
    mesh.calc_loop_triangles()
    triangles = np.empty(len(mesh.loop_triangles) * 3, dtype=np.int64)
    mesh.loop_triangles.foreach_get("vertices", triangles)
    return triangles.reshape(-1, 3)


def loop_arrays(mesh: Any) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Each loop's vertex, and each face's first loop and loop count."""
    loop_vertex = np.empty(len(mesh.loops), dtype=np.int64)
    mesh.loops.foreach_get("vertex_index", loop_vertex)
    start = np.empty(len(mesh.polygons), dtype=np.int64)
    total = np.empty(len(mesh.polygons), dtype=np.int64)
    mesh.polygons.foreach_get("loop_start", start)
    mesh.polygons.foreach_get("loop_total", total)
    return loop_vertex, start, total


def read_uv(mesh: Any, name: str) -> np.ndarray:
    """A UV layer's coordinates per loop, read before any layer is added (Blender 5.2 crashes when a UV layer
    taken before ``uv_layers.new()`` is read afterwards)."""
    values = np.empty(len(mesh.loops) * 2, dtype=np.float32)
    mesh.uv_layers[name].data.foreach_get("uv", values)
    return values.reshape(-1, 2)


def open_edges(mesh: Any) -> np.ndarray:
    """The edges used by one face only (the edges of a panel)."""
    loop_edges = np.empty(len(mesh.loops), dtype=np.int64)
    mesh.loops.foreach_get("edge_index", loop_edges)
    uses = np.bincount(loop_edges, minlength=len(mesh.edges))
    return mesh_edges(mesh)[uses == 1]


def boundary_vertices(mesh: Any) -> np.ndarray:
    """The vertices on open edges (the edges of a panel)."""
    mask = np.zeros(len(mesh.vertices), dtype=bool)
    mask[open_edges(mesh).reshape(-1)] = True
    return mask


def seam_rules(obj: Any, positions: np.ndarray, normals: Optional[np.ndarray] = None) -> Dict[str, Any]:
    """What keeps two vertices from counting as two sides of one seam (:func:`garment.seam_candidates`): sharing a
    face, lying next to each other on one open edge, facing apart."""
    mesh = obj.data
    loop_vertex, start, total = loop_arrays(mesh)
    rules: Dict[str, Any] = {
        "chains": garment.boundary_chains(open_edges(mesh), len(positions), positions),
        "face_pairs": garment.face_vertex_pairs(loop_vertex, start, total),
    }
    if normals is not None:
        rules["normals"] = normals
    return rules


def vertex_areas(positions: np.ndarray, triangles: np.ndarray) -> np.ndarray:
    """Each vertex's share of the surface (a third of each triangle around it)."""
    areas = np.zeros(len(positions))
    if len(triangles):
        a, b, c = (positions[triangles[:, i]] for i in range(3))
        third = np.linalg.norm(np.cross(b - a, c - a), axis=1) / 6.0
        for i in range(3):
            np.add.at(areas, triangles[:, i], third)
    return areas


def group_weights(obj: Any, name: str) -> np.ndarray:
    """Each vertex's weight in one vertex group (0 where the vertex is not in it, or the group is missing)."""
    weights = np.zeros(len(obj.data.vertices))
    group = obj.vertex_groups.get(name)
    if group is None:
        return weights
    index = group.index
    for vertex in obj.data.vertices:
        for element in vertex.groups:
            if element.group == index:
                weights[vertex.index] = element.weight
                break
    return weights


def locked_vertices(obj: Any) -> np.ndarray:
    """The vertices the tools leave where they are: the vertex group DCT Pinned and Blender's sculpt mask."""
    mesh = obj.data
    locked = group_weights(obj, PINNED_GROUP) > 0.5
    mask = mesh.attributes.get(SCULPT_MASK)
    if mask is not None and mask.domain == "POINT" and len(mask.data) == len(mesh.vertices):
        values = np.empty(len(mesh.vertices), dtype=np.float32)
        mask.data.foreach_get("value", values)
        locked |= values > 0.5
    return locked


def deselect_all(layer: Any, keep: Optional[Any] = None) -> None:
    """Deselects every object of the view layer but ``keep`` (a view layer can list an object removed a moment
    ago as ``None`` until it updates)."""
    for other in layer.objects:
        if other is not None and other != keep and other.select_get():
            other.select_set(False)


def in_view_layer(context: Any, obj: Any) -> bool:
    layer = getattr(context, "view_layer", None)
    if layer is None or obj is None:
        return False
    try:
        return layer.objects.get(obj.name) is not None
    except ReferenceError:
        return False


def garment_problem(context: Any, obj: Optional[Any], *, sculpting_ok: bool = False) -> Optional[Any]:
    """Why the garment cannot be changed right now, or ``None``."""
    if obj is None:
        return msg("garment.why.no-garment")
    try:
        if obj.type != "MESH":
            return msg("garment.why.no-garment")
    except ReferenceError:
        return msg("garment.why.no-garment")
    if not in_view_layer(context, obj):
        return msg("garment.why.not-shown")
    if sculpting(obj) and not sculpting_ok:
        return msg("garment.why.sculpting")
    if obj.mode != "OBJECT" and not (sculpting_ok and obj.mode == "SCULPT"):
        return msg("garment.why.object-mode")
    if obj.data.shape_keys is not None:
        return msg("garment.why.shape-keys")
    if len(obj.data.vertices) < 3:
        return msg("garment.why.empty")
    return None


def body_problem(context: Any, body: Optional[Any]) -> Optional[Any]:
    if body is None:
        return msg("garment.why.no-body")
    try:
        if body.type != "MESH" or len(body.data.polygons) == 0:
            return msg("garment.why.no-body")
    except ReferenceError:
        return msg("garment.why.no-body")
    return None


def set_flag(obj: Any, name: str, value: bool = True) -> None:
    obj[name] = 1 if value else 0


def flag(obj: Optional[Any], name: str) -> bool:
    try:
        return bool(obj is not None and obj.get(name))
    except ReferenceError:
        return False


def clear_flags(obj: Any, *names: str) -> None:
    for name in names or FLAGS + (FIT_REPORT, FINDINGS):
        if name in obj:
            del obj[name]


def stored_text(obj: Optional[Any], name: str) -> str:
    try:
        value = obj.get(name) if obj is not None else None
    except ReferenceError:
        return ""
    return value if isinstance(value, str) else ""


def material_count(obj: Optional[Any]) -> int:
    if obj is None:
        return 0
    return len({slot.material.name for slot in obj.material_slots if slot.material is not None}) or 1


def ensure_garment_id(obj: Any) -> str:
    """The garment's own id, given to it now when it has none or another object carries the same one (a copy)."""
    current = obj.get(GARMENT_ID)
    taken = isinstance(current, str) and any(
        other != obj and other.get(GARMENT_ID) == current for other in bpy.data.objects)
    if not isinstance(current, str) or not current or taken:
        current = secrets.token_hex(6)
        obj[GARMENT_ID] = current
    return current


# --------------------------------------------------------------------------------------------------
# Backups
# --------------------------------------------------------------------------------------------------


def backups(obj: Optional[Any]) -> List[Any]:
    """The garment's backups, oldest first (also those an older version listed by name)."""
    if obj is None:
        return []
    try:
        kept = [obj.get(slot) for slot in BACKUP_SLOTS]
        kept = [mesh for mesh in kept if isinstance(mesh, bpy.types.Mesh)]
        names = [name for name in str(obj.get(BACKUPS, "")).split("\n") if name]
    except ReferenceError:
        return []
    legacy = [bpy.data.meshes[name] for name in names if name in bpy.data.meshes]
    return legacy + [mesh for mesh in kept if mesh not in legacy]


def _store_backups(obj: Any, kept: List[Any]) -> None:
    for mesh in kept:
        if mesh.use_fake_user:
            mesh.use_fake_user = False  # the garment's reference keeps it now
    for slot in BACKUP_SLOTS:
        if slot in obj:
            del obj[slot]
    for slot, mesh in zip(BACKUP_SLOTS, kept):
        obj[slot] = mesh
    if BACKUPS in obj:
        del obj[BACKUPS]


def _forget(mesh: Any) -> None:
    mesh.use_fake_user = False
    if mesh.users == 0:
        bpy.data.meshes.remove(mesh)


def backup(obj: Any) -> None:
    """Keeps a copy of the garment's mesh: the first one (the shape before any fitting) and the newest ones, at most
    :data:`MAX_BACKUPS` in all. A backup holds world positions, so it still fits after the object's transform
    changed (Prepare applies it). The garment references its backups, so they go when it is deleted."""
    kept = backups(obj)
    copy = obj.data.copy()
    copy.transform(obj.matrix_world)
    copy.name = f"DCT Backup {obj.name}"
    kept.append(copy)
    dropped = []
    while len(kept) > MAX_BACKUPS:
        dropped.append(kept.pop(1))
    _store_backups(obj, kept)
    for mesh in dropped:
        _forget(mesh)


def drop_newest_backup(obj: Any) -> None:
    """Removes the backup a step made before it failed (the garment did not change)."""
    kept = backups(obj)
    if not kept:
        return
    newest = kept.pop()
    _store_backups(obj, kept)
    _forget(newest)


def remove_backups(obj: Any) -> int:
    """Drops every backup of the garment; returns how many."""
    kept = backups(obj)
    _store_backups(obj, [])
    for mesh in kept:
        _forget(mesh)
    return len(kept)


def _put_back(obj: Any, source: Any) -> None:
    """Gives the garment a copy of a backup as its mesh (Sollumz's High level follows it)."""
    old = obj.data
    restored = source.copy()
    restored.use_fake_user = False
    restored.transform(obj.matrix_world.inverted())
    restored.name = old.name
    obj.data = restored
    lods = getattr(obj, "sz_lods", None)
    if lods is not None:
        try:
            high = lods.get_lod("sollumz_high")
            if high.mesh == old or high.mesh is None:
                high.mesh = restored
        except (AttributeError, KeyError, TypeError, RuntimeError):
            pass  # a Sollumz without LOD slots
    if old.users == 0:
        bpy.data.meshes.remove(old)


def restore_pre_fit(obj: Any) -> None:
    """Puts the shape from before the first fitting step back (the backups are kept)."""
    kept = backups(obj)
    if not kept:
        raise fail("garment.why.no-backup")
    _put_back(obj, kept[0])
    clear_flags(obj)


def back_one_step(obj: Any) -> None:
    """Puts the newest backup back (the shape before the last step that changed the garment) and drops it."""
    kept = backups(obj)
    if not kept:
        raise fail("garment.why.no-backup")
    _put_back(obj, kept[-1])
    if len(kept) > 1:
        drop_newest_backup(obj)
    clear_flags(obj, *STALE)


def roll_back(obj: Any) -> None:
    """Undoes a step that failed halfway: the garment's mesh from its newest backup, which the step made and which is
    dropped again."""
    kept = backups(obj)
    if kept:
        _put_back(obj, kept[-1])
        drop_newest_backup(obj)


def reference_shape(obj: Any) -> Optional[np.ndarray]:
    """The positions before any fitting (the first backup), when the topology still matches."""
    kept = backups(obj)
    if not kept or len(kept[0].vertices) != len(obj.data.vertices) or len(kept[0].edges) != len(obj.data.edges):
        return None
    positions = np.empty(len(kept[0].vertices) * 3, dtype=np.float64)
    kept[0].vertices.foreach_get("co", positions)  # backups hold world positions
    return positions.reshape(-1, 3)


# --------------------------------------------------------------------------------------------------
# The body
# --------------------------------------------------------------------------------------------------

_TREE: Dict[str, Any] = {"key": None, "tree": None, "centres": None}
_LABELS: Dict[str, Any] = {"key": None, "labels": None}
_ESTIMATE: Dict[str, Any] = {"key": None, "joints": None}


def _body_key(body: Any) -> tuple:
    """What identifies the body's current shape: the object, its mesh and transform, and a digest of every vertex
    (a sculpted body is measured again)."""
    mesh = body.data
    co = np.empty(len(mesh.vertices) * 3, dtype=np.float32)
    mesh.vertices.foreach_get("co", co)
    return (body.session_uid, mesh.session_uid, len(mesh.vertices), len(mesh.polygons),
            tuple(round(v, 6) for row in body.matrix_world for v in row), hash(co.tobytes()))


def body_tree(body: Any) -> BVHTree:
    """The body as a BVH tree in world space (kept while the body does not change)."""
    key = _body_key(body)
    if _TREE["key"] != key:
        positions = world_positions(body)
        triangles = mesh_triangles(body.data)
        _TREE["tree"] = BVHTree.FromPolygons(positions.tolist(), triangles.tolist(), all_triangles=True)
        _TREE["centres"] = positions[triangles].mean(axis=1) if len(triangles) else np.zeros((0, 3))
        _TREE["key"] = key
    return _TREE["tree"]


def clearance(tree: BVHTree, positions: np.ndarray, faces: bool = False):
    """Each point's signed distance to the body (negative inside), the nearest body point and its outward
    normal; with ``faces`` also the body triangle it lies on (-1 without one)."""
    count = len(positions)
    signed = np.empty(count)
    nearest = np.empty((count, 3))
    normals = np.empty((count, 3))
    found = np.full(count, -1, dtype=np.int64)
    find = tree.find_nearest
    for index, point in enumerate(positions):
        location, normal, face, distance = find(Vector(point))
        if location is None:
            signed[index] = np.inf
            nearest[index] = point
            normals[index] = (0.0, 0.0, 1.0)
            continue
        nearest[index] = location
        normals[index] = normal
        found[index] = face if face is not None else -1
        offset = point - np.asarray(location)
        signed[index] = distance if float(offset @ np.asarray(normal)) >= 0.0 else -distance
    if faces:
        return signed, nearest, normals, found
    return signed, nearest, normals


def scene_body(scene: Any) -> Optional[Any]:
    props = getattr(scene, "dct_garment", None)
    body = getattr(props, "body", None) if props is not None else None
    try:
        return body if body is not None and body.type == "MESH" else None
    except ReferenceError:
        return None


def stored_joints(body: Optional[Any], gender: str) -> Optional[Dict[str, Any]]:
    """The joints kept on the body (from the hosted body's joints file or Durty Cloth Tool's skeleton)."""
    text = stored_text(body, JOINTS_TAG)
    return garment.parse_joints(text, gender) if text else None


def body_joints(body: Any, gender: str, template_joints: Optional[Dict[str, Any]] = None) -> Tuple[Dict[str, Any], str]:
    """The joints the garment is aligned to and its regions come from, with where they came from: ``hosted`` (the
    hosted body's joints file), ``dct`` (Durty Cloth Tool's skeleton of the user's game files) or ``estimate`` (read
    from the body's shape)."""
    joints = stored_joints(body, gender)
    if joints:
        return joints, "hosted"
    if template_joints:
        return dict(template_joints), "dct"
    key = _body_key(body)
    if _ESTIMATE["key"] != key:
        _ESTIMATE["joints"] = garment.estimate_body_joints(world_positions(body), mesh_edges(body.data))
        _ESTIMATE["key"] = key
    return dict(_ESTIMATE["joints"]), "estimate"


def body_triangle_regions(body: Any, joints: Dict[str, Any]) -> np.ndarray:
    """The region of each of the body's triangles (as :func:`body_tree` numbers them)."""
    body_tree(body)
    key = (_TREE["key"], tuple(sorted((name, tuple(np.round(value, 5))) for name, value in joints.items())))
    if _LABELS["key"] != key:
        _LABELS["labels"] = garment.body_regions(_TREE["centres"], joints)
        _LABELS["key"] = key
    return _LABELS["labels"]


def _collection(scene: Any, name: str) -> Any:
    collection = bpy.data.collections.get(name)
    if collection is None:
        collection = bpy.data.collections.new(name)
    if scene.collection.children.get(collection.name) is None:
        scene.collection.children.link(collection)
    return collection


def _import_file(path: pathlib.Path) -> List[Any]:
    """Imports a GLB/glTF, FBX or OBJ file with Blender's own importers; returns the new objects."""
    before = {obj.session_uid for obj in bpy.data.objects}
    suffix = path.suffix.lower()
    try:
        if suffix in (".glb", ".gltf"):
            result = bpy.ops.import_scene.gltf(filepath=str(path))
        elif suffix == ".fbx":
            result = bpy.ops.import_scene.fbx(filepath=str(path))
        elif suffix == ".obj":
            result = bpy.ops.wm.obj_import(filepath=str(path))
        else:
            raise fail("garment.why.file-type")
    except (RuntimeError, AttributeError) as exc:
        raise fail("garment.error.import", detail=str(exc).strip().splitlines()[-1] if str(exc).strip() else "") \
            from exc
    if "FINISHED" not in result:
        raise fail("garment.error.import", detail=", ".join(sorted(result)))
    return [obj for obj in bpy.data.objects if obj.session_uid not in before]


def _remove_objects(objects: Iterable[Any]) -> None:
    for obj in list(objects):
        try:
            data = obj.data
            bpy.data.objects.remove(obj)
            if data is not None and data.users == 0:
                if isinstance(data, bpy.types.Mesh):
                    bpy.data.meshes.remove(data)
                elif isinstance(data, bpy.types.Armature):
                    bpy.data.armatures.remove(data)
        except ReferenceError:
            continue


def _merged_mesh(objects: Sequence[Any], name: str) -> Any:
    """One mesh in world space from several mesh objects (their materials kept in order). The UV maps of every part
    are named alike first, so each part keeps its UVs whatever its exporter called them."""
    bm = bmesh.new()
    materials: List[Any] = []
    for obj in objects:
        mesh = obj.data.copy()
        mesh.transform(obj.matrix_world)
        for index, layer in enumerate(list(mesh.uv_layers)):
            layer.name = "UVMap" if index == 0 else f"UVMap.{index:03d}"
        offset = len(materials)
        for material in mesh.materials:
            materials.append(material)
        if offset:
            indices = np.empty(len(mesh.polygons), dtype=np.int64)
            mesh.polygons.foreach_get("material_index", indices)
            mesh.polygons.foreach_set("material_index", (indices + offset).astype(np.int32))
        bm.from_mesh(mesh)
        bpy.data.meshes.remove(mesh)
    merged = bpy.data.meshes.new(name)
    bm.to_mesh(merged)
    bm.free()
    for material in materials:
        merged.materials.append(material)
    return merged


def import_body(context: Any, path: pathlib.Path, gender: str, version: Optional[str] = None,
                joints: Optional[str] = None) -> Any:
    """Imports a body file as one mesh object in the add-on's body collection, replacing the body the add-on
    added before, with its joints when the hosted body has them. Returns the body object."""
    new = _import_file(path)
    meshes = [obj for obj in new if obj.type == "MESH"]
    if not meshes:
        _remove_objects(new)
        raise fail("garment.error.no-mesh")
    scene = context.scene
    mesh = _merged_mesh(meshes, f"DCT Body ({gender})")
    _remove_objects(new)
    for obj in list(bpy.data.objects):
        if obj.get(BODY_TAG) and scene.objects.get(obj.name) is not None:
            _remove_objects([obj])
    body = bpy.data.objects.new(f"DCT_Body_{gender}", mesh)
    body[BODY_TAG] = gender
    if version:
        body[BODY_VERSION] = version
    if joints and garment.parse_joints(joints, gender):
        body[JOINTS_TAG] = joints
    _collection(scene, BODY_COLLECTION).objects.link(body)
    _TREE["key"] = None
    return body


#: How far below the ped's origin its soles are (metres): the freemode body stands with its soles at z -1.
GROUND_DEPTH = 1.0
#: Material names that are the avatar's, not the garment's.
AVATAR_WORDS = ("avatar", "skin")


def _looks_like_avatar(obj: Any, factor: float) -> bool:
    """A mesh Marvelous Designer exported with the garment: named like an avatar, wearing skin, or a closed figure
    as tall as a person."""
    name = obj.name.lower()
    materials = [slot.material.name.lower() for slot in obj.material_slots if slot.material is not None]
    if "avatar" in name or (materials and all(any(word in m for word in AVATAR_WORDS) for m in materials)):
        return True
    corners = np.array([obj.matrix_world @ Vector(c) for c in obj.bound_box]) * factor
    tall = float(corners[:, 2].max() - corners[:, 2].min()) > 1.3
    return tall and not boundary_vertices(obj.data).any()


def _turn_matrix(turn: Optional[Tuple[str, float]]) -> Matrix:
    if turn is None:
        return Matrix.Identity(4)
    return Matrix.Rotation(math.radians(turn[1]), 4, turn[0].upper())


def import_garment(context: Any, path: pathlib.Path, *, ground: bool, category: str = "tshirt", unit: str = "auto",
                   orient: bool = True) -> Tuple[Any, Dict[str, Any]]:
    """Imports a garment file (FBX, OBJ, glTF): converted to metres, an avatar exported with it left out, joined into
    one mesh object, turned upright and to the front when it lies or faces backwards, its transform applied, and
    moved down by the ped's ground height when it was made on an avatar standing on the ground. Returns the garment
    and what was done (``factor``, ``turned``, ``avatar``)."""
    new = _import_file(path)
    meshes = [obj for obj in new if obj.type == "MESH"]
    if not meshes:
        _remove_objects(new)
        raise fail("garment.error.no-mesh")
    corners = np.concatenate([np.array([obj.matrix_world @ Vector(c) for c in obj.bound_box]) for obj in meshes])
    size = float((corners.max(axis=0) - corners.min(axis=0)).max())
    factor = garment.import_scale(size, category, unit)
    avatars = [obj for obj in meshes if _looks_like_avatar(obj, factor)] if len(meshes) > 1 else []
    if avatars and len(avatars) < len(meshes):
        meshes = [obj for obj in meshes if obj not in avatars]
        corners = np.concatenate([np.array([obj.matrix_world @ Vector(c) for c in obj.bound_box]) for obj in meshes])
        size = float((corners.max(axis=0) - corners.min(axis=0)).max())
        factor = garment.import_scale(size, category, unit)
    else:
        avatars = []
    rigged = [obj for obj in new if obj.type == "ARMATURE"]
    scale = Matrix.Scale(factor, 4)
    turns: List[Tuple[str, float]] = []
    if orient:
        points = np.concatenate([world_positions(obj) for obj in meshes]) * factor
        first = garment.upright_turn(points, category)
        if first is not None and first[0] == "x":
            turns.append(first)
            points = points @ np.array(_turn_matrix(first).to_3x3()).T
            first = garment.upright_turn(points, category)
        if first is not None and first[0] == "z":
            turns.append(first)
    turn = Matrix.Identity(4)
    for step in turns:
        turn = _turn_matrix(step) @ turn
    move = Matrix.Translation((0.0, 0.0, -GROUND_DEPTH if ground else 0.0)) @ turn @ scale
    if rigged:
        # A rigged import stays as it is, only scaled, turned and moved as a whole.
        for obj in new:
            if obj.parent is None and obj not in avatars:
                obj.matrix_world = move @ obj.matrix_world
        _remove_objects(avatars)
        chosen = max(meshes, key=lambda o: len(o.data.vertices))
    else:
        mesh = _merged_mesh(meshes, path.stem)
        mesh.transform(move)
        target = _collection_of(meshes[0], context)
        _remove_objects(new)
        chosen = bpy.data.objects.new(path.stem, mesh)
        target.objects.link(chosen)
    chosen[GARMENT_TAG] = 1
    ensure_garment_id(chosen)
    layer = context.view_layer
    deselect_all(layer)
    if layer.objects.get(chosen.name) is not None:
        chosen.select_set(True)
        layer.objects.active = chosen
    return chosen, {"factor": factor, "turned": [step[0] for step in turns], "avatar": bool(avatars)}


def _collection_of(obj: Any, context: Any) -> Any:
    collections = list(obj.users_collection)
    return collections[0] if collections else context.scene.collection


# --------------------------------------------------------------------------------------------------
# Markers
# --------------------------------------------------------------------------------------------------


def _current(scene: Any) -> Optional[Any]:
    props = getattr(scene, "dct_garment", None)
    obj = getattr(props, "garment", None) if props is not None else None
    try:
        return obj if obj is not None and obj.type == "MESH" else None
    except ReferenceError:
        return None


def marker_objects(scene: Any, obj: Optional[Any] = None) -> Dict[str, Any]:
    """The markers of one garment (the garment chosen in the panel unless ``obj`` is given). Markers an older version
    placed carry no garment and count for a garment without markers of its own."""
    obj = obj if obj is not None else _current(scene)
    owner = obj.get(GARMENT_ID) if obj is not None else None
    found: Dict[str, Any] = {}
    unowned: Dict[str, Any] = {}
    for marker in scene.objects:
        name = marker.get(MARKER_TAG)
        if name not in garment.MARKERS:
            continue
        mark = marker.get(MARKER_OWNER)
        if owner and mark == owner:
            found[name] = marker
        elif not mark:
            unowned[name] = marker
    return found or unowned


def read_markers(scene: Any, obj: Optional[Any] = None) -> Dict[str, Tuple[float, float, float]]:
    return {name: tuple(marker.matrix_world.translation) for name, marker in marker_objects(scene, obj).items()}


def write_markers(scene: Any, markers: Dict[str, Any], size: float, obj: Optional[Any] = None) -> List[Any]:
    """Creates or moves the garment's marker empties (spheres in the markers collection)."""
    obj = obj if obj is not None else _current(scene)
    owner = ensure_garment_id(obj) if obj is not None else ""
    existing = marker_objects(scene, obj)
    collection = _collection(scene, MARKER_COLLECTION)
    written = []
    for name in garment.MARKERS:
        if name not in markers:
            continue
        marker = existing.get(name)
        if marker is None:
            marker = bpy.data.objects.new(f"{MARKER_PREFIX}{name}", None)
            marker.empty_display_type = "SPHERE"
            marker[MARKER_TAG] = name
            marker.show_in_front = True
            collection.objects.link(marker)
        marker[MARKER_OWNER] = owner
        marker.empty_display_size = size
        marker.matrix_world = Matrix.Translation(Vector(markers[name]))
        written.append(marker)
    return written


def show_markers_of(scene: Any, layer: Any, obj: Optional[Any]) -> None:
    """Shows the chosen garment's markers and hides those of other garments."""
    mine = set(marker_objects(scene, obj).values()) if obj is not None else set()
    for marker in scene.objects:
        if marker.get(MARKER_TAG) in garment.MARKERS:
            try:
                if layer.objects.get(marker.name) is not None:
                    marker.hide_set(marker not in mine)
            except (RuntimeError, ReferenceError):
                continue


def resize_markers(scene: Any, size: float) -> None:
    for marker in marker_objects(scene).values():
        marker.empty_display_size = size


# --------------------------------------------------------------------------------------------------
# Regions, the fit check and the problem colours
# --------------------------------------------------------------------------------------------------


def regions(scene: Any, obj: Any, category: str, positions: np.ndarray, edges: np.ndarray) -> np.ndarray:
    """The region of each garment vertex from the markers alone (placed now when there are none): for when there is
    no body to measure against."""
    if category == "shoes":
        return np.full(len(positions), garment.REGIONS.index("legs"))
    markers = read_markers(scene, obj)
    if "pelvis" not in markers:
        markers = garment.auto_markers(positions, category if category != "shoes" else "pants",
                                       scene.dct_garment.source_pose, edges)
    return garment.classify_regions(positions, markers)


def measure(scene: Any, obj: Any, body: Any, joints: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """The garment against the body: clearance, nearest points, normals and regions (each vertex takes the region of
    the body point nearest to it when the body's joints are known)."""
    positions = world_positions(obj)
    edges = mesh_edges(obj.data)
    signed, nearest, normals, faces = clearance(body_tree(body), positions, faces=True)
    region = None
    if joints and scene.dct_garment.category != "shoes":
        labels = body_triangle_regions(body, joints)
        region = np.where(faces >= 0, labels[np.clip(faces, 0, max(len(labels) - 1, 0))], garment.OTHER) \
            if len(labels) else None
    if region is None:
        try:
            region = regions(scene, obj, scene.dct_garment.category, positions, edges)
        except garment.MarkerError:
            region = np.full(len(positions), garment.OTHER)
    return {"positions": positions, "edges": edges, "clearance": signed, "nearest": nearest, "normals": normals,
            "regions": region}


def show_problems(context: Any, obj: Any, classes: np.ndarray) -> None:
    mesh = obj.data
    attribute = mesh.color_attributes.get(PROBLEMS)
    if attribute is not None and (attribute.domain != "POINT" or attribute.data_type != "BYTE_COLOR"):
        mesh.color_attributes.remove(attribute)
        attribute = None
    if attribute is None:
        attribute = mesh.color_attributes.new(PROBLEMS, "BYTE_COLOR", "POINT")
    palette = np.array([garment.PROBLEM_COLOURS[name] for name in garment.PROBLEMS], dtype=np.float32)
    attribute.data.foreach_set("color", palette[classes].reshape(-1))
    mesh.color_attributes.active_color = mesh.color_attributes[PROBLEMS]
    mesh.update()
    _shading("VERTEX")


def hide_problems(obj: Optional[Any]) -> None:
    if obj is not None:
        try:
            attribute = obj.data.color_attributes.get(PROBLEMS)
            if attribute is not None:
                obj.data.color_attributes.remove(attribute)
                obj.data.update()
        except (ReferenceError, AttributeError):
            pass  # the garment is gone; nothing to remove
    _shading("MATERIAL", only_from="VERTEX")


def problems_shown(obj: Optional[Any]) -> bool:
    try:
        return obj is not None and obj.type == "MESH" and obj.data.color_attributes.get(PROBLEMS) is not None
    except ReferenceError:
        return False


def _shading(color_type: str, only_from: Optional[str] = None) -> None:
    """The colour source of the Solid view in the 3D views (``VERTEX``, shown as Attribute, shows the problems)."""
    wm = getattr(bpy.context, "window_manager", None)
    for window in wm.windows if wm is not None else ():
        for area in window.screen.areas if window.screen is not None else ():
            if area.type != "VIEW_3D":
                continue
            shading = area.spaces.active.shading
            if only_from is None or shading.color_type == only_from:
                shading.color_type = color_type


# --------------------------------------------------------------------------------------------------
# Align to Body and the arms
# --------------------------------------------------------------------------------------------------


def align(context: Any, obj: Any, markers: Dict[str, Any], joints: Dict[str, Any], category: str,
          keep_size: bool = False) -> Dict[str, Any]:
    """Moves, turns and (unless ``keep_size``) scales the garment so its markers sit on the body's joints, then turns
    each arm (or leg) onto the body's; the markers follow. Raises :class:`garment.MarkerError` when the markers
    would need a fit no garment needs."""
    plan = garment.align_plan(markers, joints, category, scale=not keep_size)
    positions = world_positions(obj)
    moved, placed = garment.apply_align(positions, markers, plan)
    set_world_positions(obj, moved)
    write_markers(context.scene, placed, context.scene.dct_garment.marker_size, obj)
    set_flag(obj, "dct_aligned")
    clear_flags(obj, *STALE)
    shift = float(np.linalg.norm(moved.mean(axis=0) - positions.mean(axis=0)))
    return {"scale": round(100.0 * plan.similarity.scale), "turn": round(plan.similarity.turn, 1),
            "shift": round(shift * 100.0, 1), "limbs": len(plan.limbs), "residual": round(plan.residual)}


def tpose_to_apose(context: Any, obj: Any, markers: Dict[str, Any], target: float,
                   joints: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Turns the arms of a garment to ``target`` degrees below the horizontal (or onto the body's arms when its
    joints are known, forward and back too). Each vertex follows by a weight that depends on where it is only, so
    the two sides of an open seam move together and no seam tears. The markers follow."""
    needed = ("shoulder_l", "elbow_l", "wrist_l", "shoulder_r", "elbow_r", "wrist_r")
    if any(name not in markers for name in needed):
        raise fail("garment.why.markers")
    turns = garment.arm_turn(markers, target, joints)
    if all(abs(degrees) < 1.0 for _, _, _, degrees in turns):
        return {"rotated": 0.0}
    positions = world_positions(obj)
    moved = dict(markers)
    for side, pivot, axis, degrees in turns:
        weights = garment.limb_weights(positions, moved, side, "arm")
        positions = garment.rotate_weighted(positions, pivot, axis, degrees, weights)
        for joint in ("elbow", "wrist"):
            name = f"{joint}_{side}"
            moved[name] = tuple(garment.rotate_weighted([moved[name]], pivot, axis, degrees, [1.0])[0])
    set_world_positions(obj, positions)
    write_markers(context.scene, moved, context.scene.dct_garment.marker_size, obj)
    set_flag(obj, "dct_converted")
    clear_flags(obj, *STALE)
    return {"rotated": round(max(abs(degrees) for _, _, _, degrees in turns), 1)}


# --------------------------------------------------------------------------------------------------
# Moves against the body
# --------------------------------------------------------------------------------------------------


def push_out(obj: Any, body: Any, gap: float, passes: int = 4, progress: Optional[Progress] = None) -> Dict[str, int]:
    """Moves every vertex closer to the body than ``gap`` to ``gap`` outside it; the vertices around follow
    softly, so no crease forms, and layers lying over a moved vertex (a shell over its lining) move with it. Vertices
    deeper inside than :data:`garment.MAX_PUSH`, pinned ones and those under the sculpt mask stay. After the first pass
    only the vertices that moved are measured again. Returns how many vertices were inside before and after, how
    many moved, and how many were too deep to move."""
    tree = body_tree(body)
    positions = world_positions(obj)
    edges = mesh_edges(obj.data)
    locked = locked_vertices(obj)
    start = positions.copy()
    signed, nearest, normals = clearance(tree, positions)
    before = int((signed < -garment.INSIDE_MM / 1000.0).sum())
    if progress is not None:
        progress.step()
    for _ in range(max(1, passes)):
        needs = (signed < gap - 1e-5) & (signed > -garment.MAX_PUSH) & ~locked
        if not np.any(needs):
            break
        offsets = garment.push_out_offsets(positions, nearest, normals, signed, gap, locked=locked)
        offsets = garment.layer_follow(positions, offsets, signed)
        offsets = garment.spread_offsets(offsets, edges, needs, iterations=3)
        offsets[locked] = 0.0
        changed = np.nonzero(np.linalg.norm(offsets, axis=1) > 1e-7)[0]
        positions = positions + offsets
        if len(changed):
            s, n, nn = clearance(tree, positions[changed])
            signed[changed], nearest[changed], normals[changed] = s, n, nn
        if progress is not None:
            progress.step()
    set_world_positions(obj, positions)
    moved = int((np.linalg.norm(positions - start, axis=1) > 1e-4).sum())
    inside = signed < -garment.INSIDE_MM / 1000.0
    return {"before": before, "after": int(inside.sum()), "moved": moved,
            "deep": int((signed <= -garment.MAX_PUSH).sum())}


def region_weights(data: Dict[str, Any], names: Sequence[str]) -> np.ndarray:
    mask = np.isin(data["regions"], [garment.REGIONS.index(name) for name in names])
    return garment.soft_mask(mask, data["edges"], rings=3)


def snug(scene: Any, obj: Any, body: Any, region: str, gap: float, amount: float,
         joints: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    data = measure(scene, obj, body, joints)
    if not np.any(data["regions"] == garment.REGIONS.index(region)):
        raise fail("garment.why.region-empty", region=msg(f"garment.region.{region}"))
    weights = region_weights(data, [region]) * ~locked_vertices(obj)
    offsets = garment.snug_offsets(data["positions"], data["nearest"], data["normals"], data["clearance"], gap,
                                   amount, weights)
    positions = data["positions"] + offsets
    set_world_positions(obj, positions)
    moved = np.linalg.norm(offsets, axis=1)
    count = int((moved > 1e-4).sum())
    return {"moved": count, "mean": round(float(moved[moved > 1e-4].mean() * 1000.0), 1) if count else 0.0}


def relax(scene: Any, obj: Any, body: Optional[Any], region: str, amount: float, gap: float,
          joints: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    positions = world_positions(obj)
    edges = mesh_edges(obj.data)
    if body is not None:
        markers_region = measure(scene, obj, body, joints)["regions"]
    else:
        try:
            markers_region = regions(scene, obj, scene.dct_garment.category, positions, edges)
        except garment.MarkerError:
            markers_region = np.full(len(positions), garment.OTHER)
    mask = markers_region == garment.REGIONS.index(region)
    if not np.any(mask):
        raise fail("garment.why.region-empty", region=msg(f"garment.region.{region}"))
    weights = garment.soft_mask(mask, edges, rings=3) * ~locked_vertices(obj)
    reference = reference_shape(obj)
    if reference is not None:
        rest = np.linalg.norm(reference[edges[:, 1]] - reference[edges[:, 0]], axis=1)
        relaxed = garment.relax_positions(positions, edges, rest, weights, amount, iterations=30)
        smoothed = False
    else:
        relaxed = positions.copy()
        for _ in range(3):
            mean = garment.neighbour_mean(relaxed, edges, len(relaxed))
            relaxed += (mean - relaxed) * (weights * float(np.clip(amount, 0.0, 1.0)))[:, None]
        smoothed = True
    set_world_positions(obj, relaxed)
    moved = int((np.linalg.norm(relaxed - positions, axis=1) > 1e-4).sum())
    if body is not None:
        push_out(obj, body, gap)
    return {"moved": moved, "smoothed": smoothed}


def stretch(obj: Any, positions: np.ndarray, edges: np.ndarray) -> Optional[np.ndarray]:
    reference = reference_shape(obj)
    if reference is None:
        return None
    return garment.vertex_stretch(edges, reference, positions)


# --------------------------------------------------------------------------------------------------
# The sculpt session
# --------------------------------------------------------------------------------------------------


def sculpting(obj: Optional[Any]) -> bool:
    try:
        return obj is not None and obj.type == "MESH" and obj.data.attributes.get(PRESCULPT) is not None
    except ReferenceError:
        return False


def session_broken(obj: Optional[Any]) -> bool:
    """A sculpt session whose starting shape is gone (Dyntopo or a remesh drops it): only ending it is left."""
    try:
        return obj is not None and obj.type == "MESH" and SCULPT_STATE in obj and not sculpting(obj)
    except ReferenceError:
        return False


#: Blender's own Grab brush among its essentials brushes (Blender 4.3 and later).
GRAB_BRUSH = "brushes/essentials_brushes-mesh_sculpt.blend/Brush/Grab"
#: The brush settings a session changes, and what they were (put back when it ends).
_BRUSH: List[Tuple[Any, str, Any]] = []


def _set_grab_brush(context: Any, radius: float, strength: float) -> None:
    """Chooses the Grab brush (an essentials asset from Blender 4.3 on, a tool in 4.2) and sets its size and
    strength in scene units, keeping what they were."""
    try:
        if hasattr(bpy.ops.brush, "asset_activate"):
            bpy.ops.brush.asset_activate(asset_library_type="ESSENTIALS", relative_asset_identifier=GRAB_BRUSH)
        else:
            bpy.ops.wm.tool_set_by_id(name="builtin_brush.Grab")
    except (RuntimeError, TypeError, AttributeError):
        pass  # no window to switch the tool in (background mode); the session works with any brush
    tool = context.tool_settings
    sculpt = getattr(tool, "sculpt", None)
    brush = getattr(sculpt, "brush", None)
    _BRUSH.clear()
    for settings in (brush, getattr(tool, "unified_paint_settings", None),
                     getattr(sculpt, "unified_paint_settings", None)):
        if settings is None:
            continue
        for name, value in (("use_locked_size", "SCENE"), ("unprojected_radius", radius), ("strength", strength)):
            if not hasattr(settings, name):
                continue
            try:
                before = getattr(settings, name)
                setattr(settings, name, value)
                _BRUSH.append((settings, name, before))
            except (AttributeError, TypeError, RuntimeError):
                continue  # an asset brush that cannot be changed here keeps its own settings


def _restore_brush() -> None:
    for settings, name, value in reversed(_BRUSH):
        try:
            setattr(settings, name, value)
        except (AttributeError, TypeError, RuntimeError, ReferenceError):
            continue  # the brush is gone or cannot be changed now
    _BRUSH.clear()


def start_sculpt(context: Any, obj: Any, body: Optional[Any], radius: float, strength: float, mirror_x: bool,
                 centre: Optional[float] = None) -> Dict[str, Any]:
    """Keeps the garment's shape, then switches it to Sculpt Mode with the Grab brush. Mirror X works about the
    object's own X = 0, so a garment whose origin is off the ped's centre (``centre``, world X) is shifted onto it
    for the session (its world shape stays). Returns how many vertices are inside the body now and whether the mirror
    plane had to be moved or could not be."""
    mesh = obj.data
    attribute = mesh.attributes.get(PRESCULPT) or mesh.attributes.new(PRESCULPT, "FLOAT_VECTOR", "POINT")
    co = np.empty(len(mesh.vertices) * 3, dtype=np.float32)
    mesh.vertices.foreach_get("co", co)
    attribute.data.foreach_set("vector", co)
    inside = 0
    if body is not None:
        signed, _, _ = clearance(body_tree(body), world_positions(obj))
        inside = int((signed < -garment.INSIDE_MM / 1000.0).sum())
    shift, mirror_off = 0.0, False
    if mirror_x and centre is not None:
        offset = centre - float(obj.matrix_world.translation.x)
        plain = obj.parent is None and all(abs(obj.matrix_world[i][j] - (1.0 if i == j else 0.0)) < 1e-6
                                           for i in range(3) for j in range(3))
        if abs(offset) > 0.001:
            if plain:
                mesh.transform(Matrix.Translation((-offset, 0.0, 0.0)))
                obj.location.x += offset
                shift = offset
            else:
                mirror_off = True
    obj[SCULPT_STATE] = {"inside": inside, "mirror": int(bool(mesh.use_mirror_x)), "shift": shift,
                         "body_display": body.display_type if body is not None else ""}
    mesh.use_mirror_x = mirror_x
    if body is not None:
        body.display_type = "WIRE"
    layer = context.view_layer
    deselect_all(layer, keep=obj)
    obj.select_set(True)
    layer.objects.active = obj
    try:
        bpy.ops.object.mode_set(mode="SCULPT")
    except RuntimeError as exc:
        _end_sculpt(context, obj, body)
        raise fail("garment.error.mode", detail=str(exc)) from exc
    _set_grab_brush(context, radius, strength)
    return {"inside": inside, "shifted": bool(shift), "mirror_off": mirror_off}


def _end_sculpt(context: Any, obj: Any, body: Optional[Any]) -> Dict[str, Any]:
    state = dict(obj.get(SCULPT_STATE, {}) or {})
    if obj.mode != "OBJECT":
        layer = context.view_layer
        layer.objects.active = obj
        bpy.ops.object.mode_set(mode="OBJECT")
    _restore_brush()
    obj.data.use_mirror_x = bool(state.get("mirror", 0))
    shift = float(state.get("shift", 0.0) or 0.0)
    if shift:
        obj.data.transform(Matrix.Translation((shift, 0.0, 0.0)))
        obj.location.x -= shift
        snapshot = obj.data.attributes.get(PRESCULPT)
        if snapshot is not None and len(snapshot.data) == len(obj.data.vertices):
            before = np.empty(len(obj.data.vertices) * 3, dtype=np.float32)
            snapshot.data.foreach_get("vector", before)
            before = before.reshape(-1, 3)
            before[:, 0] += shift
            snapshot.data.foreach_set("vector", before.reshape(-1))
    if body is not None and state.get("body_display") in ("BOUNDS", "WIRE", "SOLID", "TEXTURED"):
        body.display_type = state["body_display"]
    if SCULPT_STATE in obj:
        del obj[SCULPT_STATE]
    return state


def accept_sculpt(context: Any, obj: Any, body: Optional[Any], keep_out: bool, gap: float) -> Dict[str, int]:
    """Keeps the sculpted shape (moving what was dragged into the body back out when ``keep_out``) and ends the
    session. A vertex the user only brought closer than the gap, but not into the body, stays where it was put."""
    state = _end_sculpt(context, obj, body)
    mesh = obj.data
    now = np.empty(len(mesh.vertices) * 3, dtype=np.float32)
    mesh.vertices.foreach_get("co", now)
    snapshot = mesh.attributes.get(PRESCULPT)
    before = now.copy()  # without the snapshot (a remesh drops it) nothing counts as moved
    if snapshot is not None and len(snapshot.data) == len(mesh.vertices):
        snapshot.data.foreach_get("vector", before)
    if snapshot is not None:
        mesh.attributes.remove(snapshot)
    moved_mask = np.linalg.norm((now - before).reshape(-1, 3), axis=1) > 1e-4
    inside_after = 0
    if body is not None:
        tree = body_tree(body)
        positions = world_positions(obj)
        signed, _, _ = clearance(tree, positions)
        if keep_out and np.any(moved_mask):
            fix = np.nonzero(moved_mask & (signed < -garment.INSIDE_MM / 1000.0))[0]
            if len(fix):
                matrix = np.array(obj.matrix_world, dtype=np.float64)
                start = before.reshape(-1, 3)[fix].astype(np.float64) @ matrix[:3, :3].T + matrix[:3, 3]
                positions[fix] = _back_out(tree, start, positions[fix], gap)
                set_world_positions(obj, positions)
                signed[fix], _, _ = clearance(tree, positions[fix])
        inside_after = int((signed < -garment.INSIDE_MM / 1000.0).sum())
    mesh.update()
    return {"moved": int(moved_mask.sum()), "before": int(state.get("inside", 0)), "after": inside_after}


def _back_out(tree: BVHTree, start: np.ndarray, end: np.ndarray, gap: float, steps: int = 14) -> np.ndarray:
    """Points dragged from ``start`` to ``end`` into the body, moved back along their drag to the last place at
    least ``gap`` outside it. A point that started inside is pushed out along the body's normal instead."""
    result = end.copy()
    signed, nearest, normals = clearance(tree, start)
    outside = signed >= gap
    if np.any(~outside):
        result[~outside] = nearest[~outside] + normals[~outside] * gap
    low = np.zeros(int(outside.sum()))  # a share of the drag that is known to stay outside
    high = np.ones_like(low)
    a, b = start[outside], end[outside]
    for _ in range(steps):
        middle = (low + high) / 2
        ok = clearance(tree, a + (b - a) * middle[:, None])[0] >= gap
        low = np.where(ok, middle, low)
        high = np.where(ok, high, middle)
    result[outside] = a + (b - a) * low[:, None]
    return result


def cancel_sculpt(context: Any, obj: Any, body: Optional[Any]) -> bool:
    """Puts the shape from before the session back and ends it. False when that shape is gone (Dyntopo or a remesh
    dropped it): the session ends anyway, and Ctrl+Z still has the shape."""
    _end_sculpt(context, obj, body)
    mesh = obj.data
    snapshot = mesh.attributes.get(PRESCULPT)
    if snapshot is None or len(snapshot.data) != len(mesh.vertices):
        if snapshot is not None:
            mesh.attributes.remove(snapshot)
        return False
    before = np.empty(len(mesh.vertices) * 3, dtype=np.float32)
    snapshot.data.foreach_get("vector", before)
    mesh.vertices.foreach_set("co", before)
    mesh.attributes.remove(snapshot)
    mesh.update()
    return True


# --------------------------------------------------------------------------------------------------
# The tear check (armatures)
# --------------------------------------------------------------------------------------------------

TEMP_PREFIX = "DCT_tmp_"

#: Synthetic test poses: (text key, [(bone name parts, world axis, degrees for the left side)]). The name parts cover
#: the freemode skeleton and the common rigs of other tools (Mixamo, Marvelous Designer's avatars).
TEST_POSES = (
    ("garment.pose.arms-up", [(("upperarm", "upper_arm", "leftarm", "rightarm", "arm.l", "arm.r", "arm_l", "arm_r"),
                               "Y", -75.0)]),
    ("garment.pose.arms-forward", [(("upperarm", "upper_arm", "leftarm", "rightarm", "arm.l", "arm.r", "arm_l",
                                     "arm_r"), "Z", -70.0)]),
    ("garment.pose.legs-forward", [(("thigh", "upleg", "upperleg", "upper_leg"), "X", -60.0)]),
    ("garment.pose.twist", [(("spine3", "spine2", "spine1", "spine"), "Z", 25.0)]),
)
#: Seam sides further apart than this at rest (metres) are not tested: Marvelous Designer's seams lie within it.
SEAM_REACH = 0.003


def _override(obj: Any, *selected: Any) -> Dict[str, Any]:
    window = getattr(bpy.context, "window", None)
    if window is None:
        wm = getattr(bpy.context, "window_manager", None)
        window = wm.windows[0] if wm is not None and len(wm.windows) else None
    values: Dict[str, Any] = {"active_object": obj, "object": obj, "selected_objects": list(selected) or [obj],
                              "selected_editable_objects": list(selected) or [obj]}
    if window is not None:
        values["window"] = window
    return values


def armature_of(obj: Any) -> Optional[Any]:
    for modifier in obj.modifiers:
        if modifier.type == "ARMATURE" and modifier.object is not None and modifier.object.type == "ARMATURE":
            return modifier.object
    if obj.parent is not None and obj.parent.type == "ARMATURE":
        return obj.parent
    return None


def tears_problem(obj: Optional[Any]) -> Optional[Any]:
    if obj is None:
        return msg("garment.why.no-garment")
    if armature_of(obj) is None or not any(m.type == "ARMATURE" for m in obj.modifiers):
        return msg("garment.why.no-armature")
    if not obj.vertex_groups:
        return msg("garment.why.no-weights")
    return None


def _side(name: str, head_x: float, centre: float) -> float:
    lowered = name.lower()
    for token, side in (("_l_", 1.0), ("_r_", -1.0), (".l", 1.0), (".r", -1.0), ("_l", 1.0), ("_r", -1.0),
                        ("left", 1.0), ("right", -1.0)):
        if token in lowered:
            return side
    return 1.0 if head_x >= centre else -1.0


def _test_bones(rig: Any, parts: Sequence[str], centre: float) -> List[Tuple[Any, float]]:
    """The bone a test pose moves on each side: the first name part that matches decides, and of several
    matching bones (roll and helper bones) the one with the shortest name."""
    for part in parts:
        matching = [pose for pose in rig.pose.bones if part in pose.name.lower() and "roll" not in pose.name.lower()]
        if not matching:
            continue
        chosen: Dict[float, Any] = {}
        for pose in sorted(matching, key=lambda p: len(p.name)):
            side = _side(pose.name, float((rig.matrix_world @ pose.bone.head_local).x), centre)
            if part.startswith("spine"):
                side = 1.0  # one spine bone twists the whole chest
            chosen.setdefault(side, pose)
        return [(pose, side) for side, pose in chosen.items()]
    return []


def check_tears(context: Any, obj: Any, threshold: float = 0.005, seam: float = SEAM_REACH) -> Dict[str, Any]:
    """Poses the garment's armature through a few test poses and reports where the two sides of an open seam separate
    and how far, which edges stretch a lot, and which poses found no bone to move. The torn vertices go into the vertex
    group ``DCT Tears``; the pose is put back afterwards."""
    rig = armature_of(obj)
    mesh = obj.data
    rest = world_positions(obj)
    pairs = garment.seam_pairs(rest, seam, boundary_vertices(mesh), **seam_rules(obj, rest))
    edges = mesh_edges(mesh)
    rest_lengths = np.linalg.norm(rest[edges[:, 1]] - rest[edges[:, 0]], axis=1)
    centre = float(rig.matrix_world.translation.x)
    saved = {pose.name: pose.matrix_basis.copy() for pose in rig.pose.bones}
    position = rig.data.pose_position
    rig.data.pose_position = "POSE"
    results = []
    torn_vertices: set = set()
    layer = context.view_layer
    to_rig = rig.matrix_world.to_3x3().inverted()
    try:
        for key, moves in TEST_POSES:
            for pose in rig.pose.bones:
                pose.matrix_basis = saved[pose.name]
            touched = 0
            for parts, axis, degrees in moves:
                for pose, side in _test_bones(rig, parts, centre):
                    world_axis = Vector({"X": (1, 0, 0), "Y": (0, 1, 0), "Z": (0, 0, 1)}[axis])
                    local_axis = (to_rig @ world_axis).normalized()
                    angle = math.radians(degrees * (side if axis != "X" else 1.0))
                    head = pose.head.copy()
                    pose.matrix = (Matrix.Translation(head) @ Matrix.Rotation(angle, 4, local_axis)
                                   @ Matrix.Translation(-head) @ pose.matrix)
                    layer.update()
                    touched += 1
            if not touched:
                results.append({"pose": key, "skipped": True, "torn": 0, "gap": 0.0, "stretched": 0})
                continue
            layer.update()
            evaluated = obj.evaluated_get(context.evaluated_depsgraph_get())
            posed_mesh = evaluated.to_mesh()
            try:
                if len(posed_mesh.vertices) != len(rest):
                    raise fail("garment.why.modifiers")
                local = np.empty(len(posed_mesh.vertices) * 3, dtype=np.float64)
                posed_mesh.vertices.foreach_get("co", local)
            finally:
                evaluated.to_mesh_clear()
            matrix = np.array(obj.matrix_world, dtype=np.float64)
            posed = local.reshape(-1, 3) @ matrix[:3, :3].T + matrix[:3, 3]
            torn, separation = garment.tears(pairs, posed, threshold)
            lengths = np.linalg.norm(posed[edges[:, 1]] - posed[edges[:, 0]], axis=1)
            stretched = int((lengths > 1.5 * np.maximum(rest_lengths, 1e-9)).sum())
            for a, b in pairs[torn]:
                torn_vertices.update((int(a), int(b)))
            results.append({"pose": key, "torn": int(torn.sum()),
                            "gap": round(float(separation.max() * 1000.0), 1) if len(separation) else 0.0,
                            "stretched": stretched})
    finally:
        for pose in rig.pose.bones:
            pose.matrix_basis = saved[pose.name]
        rig.data.pose_position = position
        layer.update()
    group = obj.vertex_groups.get(TEARS_GROUP)
    if group is not None:
        obj.vertex_groups.remove(group)
    if torn_vertices:
        group = obj.vertex_groups.new(name=TEARS_GROUP)
        group.add(sorted(torn_vertices), 1.0, "REPLACE")
    return {"poses": results, "pairs": int(len(pairs)), "vertices": len(torn_vertices),
            "skipped": sum(1 for pose in results if pose.get("skipped"))}


# --------------------------------------------------------------------------------------------------
# Game ready
# --------------------------------------------------------------------------------------------------


def apply_transform(obj: Any) -> bool:
    """Bakes the object's transform into its mesh when it is a standalone object (no parent, no children)."""
    if obj.parent is not None or obj.children or obj.matrix_world == Matrix.Identity(4):
        return False
    obj.data.transform(obj.matrix_world)
    obj.matrix_world = Matrix.Identity(4)
    return True


def _colour_values(colour: Sequence[float], count: int) -> np.ndarray:
    return np.tile(np.asarray(colour, dtype=np.float32).reshape(1, 4), (count, 1)).reshape(-1)


def _srgb_to_linear(values: np.ndarray) -> np.ndarray:
    rgb = values.reshape(-1, 4).copy()
    c = rgb[:, :3]
    rgb[:, :3] = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    return rgb.reshape(-1)


def set_vertex_colours(mesh: Any, colours: Sequence[Sequence[float]], overwrite: bool) -> int:
    """Gives the mesh the ped shader's vertex colours (``Color 1``, ``Color 2``: face corner, byte colour, sRGB
    values). Existing ones in that format are kept unless ``overwrite``. Returns how many were written."""
    written = 0
    for name, colour in zip(COLOUR_ATTRIBUTES, colours):
        attribute = mesh.color_attributes.get(name)
        if attribute is not None and (attribute.domain != "CORNER" or attribute.data_type != "BYTE_COLOR"):
            mesh.color_attributes.remove(attribute)
            attribute = None
        if attribute is not None and not overwrite:
            continue
        if attribute is None:
            attribute = mesh.color_attributes.new(name, "BYTE_COLOR", "CORNER")
        values = _colour_values(colour, len(mesh.loops))
        attribute = mesh.color_attributes[name]
        try:
            attribute.data.foreach_set("color_srgb", values)
        except (AttributeError, TypeError):
            attribute.data.foreach_set("color", _srgb_to_linear(values))
        written += 1
    if mesh.color_attributes.get(COLOUR_ATTRIBUTES[0]) is not None:
        mesh.color_attributes.active_color = mesh.color_attributes[COLOUR_ATTRIBUTES[0]]
        try:
            mesh.color_attributes.render_color_index = mesh.color_attributes.active_color_index
        except (AttributeError, TypeError):
            pass  # an older Blender without a separate render colour
    return written


def _vertex_materials(mesh: Any) -> np.ndarray:
    """The material of a face around each vertex (-1 for a vertex without faces)."""
    loop_vertex, _start, total = loop_arrays(mesh)
    face_material = np.empty(len(mesh.polygons), dtype=np.int64)
    mesh.polygons.foreach_get("material_index", face_material)
    material = np.full(len(mesh.vertices), -1, dtype=np.int64)
    material[loop_vertex] = np.repeat(face_material, total)
    return material


def _remove_interior_walls(bm: Any) -> int:
    """Faces left twice on the same corners after welding a thick export: two walls facing each other inside the
    garment go; a face that only appears twice the same way keeps one copy."""
    seen: Dict[frozenset, List[Any]] = {}
    for face in bm.faces:
        seen.setdefault(frozenset(v.index for v in face.verts), []).append(face)
    doomed = []
    for faces in seen.values():
        if len(faces) < 2:
            continue
        first = faces[0]
        opposite = [f for f in faces[1:] if f.normal.dot(first.normal) < 0]
        doomed += [first, *opposite] if opposite else faces[1:]
    if doomed:
        bmesh.ops.delete(bm, geom=list(set(doomed)), context="FACES")
    return len(doomed)


def prepare(context: Any, obj: Any, weld: float, colours: Sequence[Sequence[float]], overwrite: bool) -> Dict[str, Any]:
    """Welds the panel seams within ``weld`` metres (never a lining onto its shell, never a hem onto itself), removes
    loose and degenerate geometry, triangulates, shades smooth and adds the ped vertex colours. A thick export (panels
    closed into slabs, without open edges) is welded across panels and the walls between them are removed."""
    hide_problems(obj)
    applied = apply_transform(obj)
    mesh = obj.data
    tears_group = obj.vertex_groups.get(TEARS_GROUP)
    if tears_group is not None:
        obj.vertex_groups.remove(tears_group)
    if mesh.attributes.get(PRESCULPT) is not None:
        mesh.attributes.remove(mesh.attributes[PRESCULPT])
    positions = world_positions(obj)
    count = len(positions)
    normals = vertex_normals(obj)
    edges = mesh_edges(mesh)
    boundary = boundary_vertices(mesh)
    material = _vertex_materials(mesh)
    parts = garment.components(count, edges)
    thick = int(boundary.sum()) <= max(2, int(0.002 * count)) and len(np.unique(parts)) > 1
    lining_flags = group_weights(obj, LINING_GROUP) > 0.5
    if lining_flags.any():
        fabrics, apart, lining = lining_flags.astype(np.int64), [(0, 1)], True
    else:
        apart = garment.lining_pairs(positions, normals, material, areas=vertex_areas(positions, mesh_triangles(mesh))) \
            if len(set(material.tolist())) > 1 else []
        fabrics, lining = material, bool(apart)
    rules = seam_rules(obj, positions, normals)
    target, merged = garment.weld_targets(positions, weld, None if thick else boundary, fabrics=fabrics, apart=apart,
                                          components=parts, cross_components_only=thick, **rules)
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.verts.ensure_lookup_table()
    inverse = obj.matrix_world.inverted()
    targetmap = {}
    for index in np.nonzero(target != np.arange(count))[0]:
        targetmap[bm.verts[int(index)]] = bm.verts[int(target[index])]
    for root in set(int(t) for t in target[target != np.arange(count)]):
        bm.verts[root].co = inverse @ Vector(merged[root])
    welded = len(targetmap)
    if targetmap:
        bmesh.ops.weld_verts(bm, targetmap=targetmap)
    walls = 0
    if thick:
        bm.verts.index_update()
        bm.normal_update()
        walls = _remove_interior_walls(bm)
    loose_verts = [v for v in bm.verts if not v.link_faces]
    loose_edges = [e for e in bm.edges if not e.link_faces]
    removed = len(loose_verts)
    if loose_edges:
        bmesh.ops.delete(bm, geom=loose_edges, context="EDGES")
    loose_verts = [v for v in bm.verts if not v.link_faces]
    if loose_verts:
        bmesh.ops.delete(bm, geom=loose_verts, context="VERTS")
    bmesh.ops.dissolve_degenerate(bm, dist=1e-6, edges=bm.edges[:])
    bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method="BEAUTY", ngon_method="BEAUTY")
    for face in bm.faces:
        face.smooth = True
    for edge in bm.edges:
        edge.smooth = True
    bm.to_mesh(mesh)
    triangles = len(bm.faces)
    bm.free()
    for name in ("sharp_edge", "sharp_face"):
        attribute = mesh.attributes.get(name)
        if attribute is not None:
            mesh.attributes.remove(attribute)
    if getattr(mesh, "has_custom_normals", False):
        try:
            with context.temp_override(**_override(obj)):
                bpy.ops.mesh.customdata_custom_splitnormals_clear()
        except RuntimeError:
            pass  # the custom normals stay; Sollumz exports them as they are
    colours_written = set_vertex_colours(mesh, colours, overwrite)
    mesh.update()
    set_flag(obj, "dct_prepared")
    clear_flags(obj, *STALE)
    return {"welded": welded, "removed": removed, "triangles": triangles, "lining": lining,
            "colours": colours_written, "applied": applied, "thick": thick, "walls": walls}


def _texture_nodes(material: Any) -> List[Any]:
    if material is None or not material.use_nodes or material.node_tree is None:
        return []
    return [node for node in material.node_tree.nodes if node.type == "TEX_IMAGE" and node.image is not None]


def _principled(material: Any) -> Optional[Any]:
    tree = getattr(material, "node_tree", None)
    return next((n for n in tree.nodes if n.type == "BSDF_PRINCIPLED"), None) if tree is not None else None


def _input(shader: Any, *names: str) -> Optional[Any]:
    for name in names:
        socket = shader.inputs.get(name) if shader is not None else None
        if socket is not None:
            return socket
    return None


def _output(material: Any) -> Optional[Any]:
    tree = material.node_tree
    outputs = [n for n in tree.nodes if n.type == "OUTPUT_MATERIAL"]
    return next((n for n in outputs if getattr(n, "is_active_output", False)), outputs[0] if outputs else None)


def _maps_present(materials: Sequence[Any]) -> Dict[str, bool]:
    """Which maps besides the colour the materials have: see-through parts, a normal map, a specular map, a glow."""
    found = {"alpha": False, "normal": False, "specular": False, "emission": False}
    for material in materials:
        shader = _principled(material)
        if shader is None:
            continue
        alpha = _input(shader, "Alpha")
        found["alpha"] |= bool(alpha is not None and (alpha.is_linked or alpha.default_value < 0.999))
        normal = _input(shader, "Normal")
        found["normal"] |= bool(normal is not None and normal.is_linked)
        specular = _input(shader, "Specular IOR Level", "Specular")
        found["specular"] |= bool(specular is not None and specular.is_linked)
        colour, strength = _input(shader, "Emission Color", "Emission"), _input(shader, "Emission Strength")
        glows = strength is None or strength.is_linked or strength.default_value > 0.0
        lit = colour is not None and (colour.is_linked or any(c > 0.001 for c in list(colour.default_value)[:3]))
        found["emission"] |= bool(glows and lit)
    return found


class _Rewire:
    """Shows one input of every material as its emission for an EMIT bake (alpha or specular into an image) and puts
    every material back afterwards."""

    def __init__(self, materials: Sequence[Any], names: Sequence[str]) -> None:
        self.changes: List[Tuple[Any, Any, Any, List[Any]]] = []
        for material in materials:
            tree, shader, output = material.node_tree, _principled(material), _output(material)
            if output is None:
                continue
            surface = output.inputs["Surface"]
            before = surface.links[0].from_socket if surface.is_linked else None
            emission = tree.nodes.new("ShaderNodeEmission")
            added = [emission]
            source = _input(shader, *names)
            if source is not None and source.is_linked:
                tree.links.new(source.links[0].from_socket, emission.inputs["Color"])
            else:
                value = tree.nodes.new("ShaderNodeValue")
                value.outputs[0].default_value = float(source.default_value) if source is not None else 1.0
                tree.links.new(value.outputs[0], emission.inputs["Color"])
                added.append(value)
            tree.links.new(emission.outputs["Emission"], surface)
            self.changes.append((material, surface, before, added))

    def undo(self) -> None:
        for material, surface, before, added in self.changes:
            try:
                tree = material.node_tree
                for node in added:
                    tree.nodes.remove(node)
                if before is not None:
                    tree.links.new(before, surface)
            except (ReferenceError, RuntimeError):
                continue
        self.changes = []


def _bake(context: Any, obj: Any, kind: str) -> None:
    with context.temp_override(**_override(obj)):
        result = bpy.ops.object.bake(type=kind, uv_layer=PACKED_UV, normal_space="TANGENT")
    if "FINISHED" not in result:
        raise fail("garment.error.bake", detail=", ".join(sorted(result)))


def _bake_into(context: Any, obj: Any, materials: Sequence[Any], name: str, size: int, kind: str,
               data: bool = False) -> np.ndarray:
    """Bakes one pass into a new image of ``size`` (every material's bake target) and returns its pixels."""
    image = bpy.data.images.new(name, size, size, alpha=True, float_buffer=False)
    if data:
        image.colorspace_settings.name = "Non-Color"
    nodes = []
    try:
        for material in materials:
            tree = material.node_tree
            node = tree.nodes.new("ShaderNodeTexImage")
            node.image = image
            uv = tree.nodes.new("ShaderNodeUVMap")
            uv.uv_map = PACKED_UV
            tree.links.new(uv.outputs["UV"], node.inputs["Vector"])
            for other in tree.nodes:
                other.select = False
            node.select = True
            tree.nodes.active = node
            nodes += [(material, node), (material, uv)]
        _bake(context, obj, kind)
        pixels = np.empty(size * size * 4, dtype=np.float32)
        image.pixels.foreach_get(pixels)
        return pixels.reshape(size, size, 4)
    finally:
        for material, node in nodes:
            try:
                material.node_tree.nodes.remove(node)
            except (ReferenceError, RuntimeError):
                continue
        bpy.data.images.remove(image)


def _downsample(pixels: np.ndarray, factor: int) -> np.ndarray:
    if factor == 1:
        return pixels
    size = pixels.shape[0] // factor
    return pixels.reshape(size, factor, size, factor, 4).mean(axis=(1, 3))


def _image(name: str, pixels: np.ndarray, data: bool = False) -> Any:
    size = pixels.shape[0]
    image = bpy.data.images.new(name, size, size, alpha=True)
    if data:
        image.colorspace_settings.name = "Non-Color"
    image.pixels.foreach_set(np.ascontiguousarray(pixels, dtype=np.float32).reshape(-1))
    image.pack()
    return image


#: Texture sizes Combine Materials bakes at twice their size and scales down, for a sharper result (each pixel
#: averages four samples).
SUPERSAMPLED = (512, 1024, 2048)
#: The space between packed UV islands, in pixels of the texture.
PACK_MARGIN = 16


def combine_materials(context: Any, obj: Any, size: int, cut_strips: bool,
                      progress: Optional[Progress] = None) -> Dict[str, Any]:
    """Packs every UV island of the garment into one 0 to 1 layout (long thin strips cut into pieces first) and
    bakes all its materials into one material of ``size`` pixels: the colour with the see-through parts in its alpha,
    and a normal, a specular and an emission map where a material has one. The original UV layout is kept as
    ``DCT Source UV``."""
    mesh = obj.data
    if not mesh.uv_layers:
        raise fail("garment.why.no-uv")
    if any(slot.material is None for slot in obj.material_slots) or not obj.material_slots:
        raise fail("garment.why.empty-slot")
    if any(getattr(slot.material, "sollum_type", None) == "sollumz_material_shader" for slot in obj.material_slots):
        raise fail("garment.why.ped-material")
    hide_problems(obj)
    source = mesh.uv_layers.active.name if mesh.uv_layers.active is not None else mesh.uv_layers[0].name
    source_uv = read_uv(mesh, source)  # before a layer is added (the Blender 5.2 crash)
    if source != SOURCE_UV:
        if mesh.uv_layers.get(SOURCE_UV) is not None:
            mesh.uv_layers[SOURCE_UV].name = SOURCE_UV + " (old)"
        mesh.uv_layers[source].name = SOURCE_UV
    if mesh.uv_layers.get(PACKED_UV) is not None:
        mesh.uv_layers[PACKED_UV].name = PACKED_UV + " (old)"
    if len(mesh.uv_layers) >= 8:
        raise fail("garment.why.uv-full")
    mesh.uv_layers.new(name=PACKED_UV)
    packed = mesh.uv_layers[PACKED_UV]  # fetched again by name after adding it
    layout = source_uv.copy()
    cut = 0
    if cut_strips:
        loop_vertex, start, total = loop_arrays(mesh)
        islands = garment.uv_islands(loop_vertex, source_uv, start, total)
        loop_face = np.repeat(np.arange(len(start)), total)
        centres = np.zeros((len(start), 2))
        np.add.at(centres, loop_face, source_uv)
        centres /= total[:, None]
        pieces, cut = garment.strip_segments(islands, centres, source_uv, total)
        layout[:, 0] += (pieces[loop_face] * 1e-3).astype(np.float32)  # tears the pieces apart for the packer
    packed.data.foreach_set("uv", layout.reshape(-1))
    mesh.uv_layers.active = mesh.uv_layers[PACKED_UV]
    # While baking, every texture reads the original layout (also through the render UV map and nodes that named
    # it); the packed layout becomes the render UV map afterwards.
    mesh.uv_layers[SOURCE_UV].active_render = True

    layer = context.view_layer
    deselect_all(layer, keep=obj)
    obj.select_set(True)
    layer.objects.active = obj
    with context.temp_override(**_override(obj)):
        bpy.ops.object.mode_set(mode="EDIT")
        try:
            bpy.ops.mesh.select_all(action="SELECT")
            bpy.ops.uv.select_all(action="SELECT")
            bpy.ops.uv.average_islands_scale()
            bpy.ops.uv.pack_islands(rotate=True, scale=True, margin_method="FRACTION", margin=PACK_MARGIN / size,
                                    shape_method="CONCAVE")
        finally:
            bpy.ops.object.mode_set(mode="OBJECT")
    if progress is not None:
        progress.step()

    materials = []
    for slot in obj.material_slots:
        if slot.material is not None and slot.material not in materials:
            materials.append(slot.material)
    maps = _maps_present(materials)
    factor = 2 if size in SUPERSAMPLED else 1
    bake_size = size * factor
    added: List[Tuple[Any, Any]] = []
    renamed: List[Tuple[Any, str]] = []
    for material in materials:
        material.use_nodes = True
        tree = material.node_tree
        for node in tree.nodes:
            if node.type == "UVMAP" and node.uv_map == source and source != SOURCE_UV:
                renamed.append((node, node.uv_map))
                node.uv_map = SOURCE_UV
        for texture in _texture_nodes(material):
            if not texture.inputs["Vector"].is_linked:
                uv_node = tree.nodes.new("ShaderNodeUVMap")
                uv_node.uv_map = SOURCE_UV
                tree.links.new(uv_node.outputs["UV"], texture.inputs["Vector"])
                added.append((material, uv_node))

    scene = context.scene
    render = scene.render
    saved = {"engine": render.engine}
    bake = render.bake
    saved_bake = {name: getattr(bake, name) for name in ("use_pass_direct", "use_pass_indirect", "use_pass_color",
                                                         "margin", "margin_type", "use_clear", "target")
                  if hasattr(bake, name)}
    results: Dict[str, np.ndarray] = {}
    try:
        try:
            render.engine = "CYCLES"
        except TypeError as exc:  # Cycles is turned off in the Preferences
            raise fail("garment.error.cycles") from exc
        cycles = getattr(scene, "cycles", None)
        if cycles is not None:
            saved["samples"] = cycles.samples
            cycles.samples = 1
        bake.use_pass_direct = False
        bake.use_pass_indirect = False
        bake.use_pass_color = True
        bake.margin = PACK_MARGIN * factor
        bake.margin_type = "EXTEND"
        bake.use_clear = True
        bake.target = "IMAGE_TEXTURES"
        results["diffuse"] = _bake_into(context, obj, materials, f"{obj.name}_bake", bake_size, "DIFFUSE")
        if progress is not None:
            progress.step()
        for key, kind, names in (("alpha", "EMIT", ("Alpha",)), ("specular", "EMIT", ("Specular IOR Level", "Specular"))):
            if not maps[key]:
                continue
            rewire = _Rewire(materials, names)
            try:
                results[key] = _bake_into(context, obj, materials, f"{obj.name}_bake", bake_size, kind, data=True)
            finally:
                rewire.undo()
            if progress is not None:
                progress.step()
        if maps["normal"]:
            results["normal"] = _bake_into(context, obj, materials, f"{obj.name}_bake", bake_size, "NORMAL",
                                           data=True)
        if maps["emission"]:
            results["emission"] = _bake_into(context, obj, materials, f"{obj.name}_bake", bake_size, "EMIT")
    except RuntimeError as exc:
        raise fail("garment.error.bake", detail=str(exc).strip()) from exc
    finally:
        try:
            render.engine = saved["engine"]
        except TypeError:
            pass  # the engine that was set is gone; Blender keeps its own choice
        if "samples" in saved:
            scene.cycles.samples = saved["samples"]
        for name, value in saved_bake.items():
            setattr(bake, name, value)
        for material, node in added:
            try:
                material.node_tree.nodes.remove(node)
            except (ReferenceError, RuntimeError):
                continue
        for node, name in renamed:
            try:
                node.uv_map = name  # the materials stay as they were (other objects may use them)
            except ReferenceError:
                continue
    mesh.uv_layers[PACKED_UV].active_render = True

    diffuse = _downsample(results["diffuse"], factor)
    if "alpha" in results:
        diffuse[..., 3] = _downsample(results["alpha"], factor)[..., 0]
    else:
        diffuse[..., 3] = 1.0
    images = {"diffuse": _image(f"{obj.name}_diffuse", diffuse)}
    for key in ("normal", "specular", "emission"):
        if key in results:
            images[key] = _image(f"{obj.name}_{key}", _downsample(results[key], factor), data=key != "emission")
    combined = _combined_material(obj.name, images, "alpha" in results)
    mesh.materials.clear()
    mesh.materials.append(combined)
    mesh.polygons.foreach_set("material_index", np.zeros(len(mesh.polygons), dtype=np.int32))
    mesh.update()
    triangles_uv = _triangle_uv(mesh, PACKED_UV)
    triangles = world_positions(obj)[mesh_triangles(mesh)]
    clear_flags(obj, "dct_validated", "dct_lods", FINDINGS)  # levels of detail made before keep the old materials
    return {"materials": len(materials), "size": size, "cut": cut,
            "used": round(100.0 * min(1.0, garment.uv_area(triangles_uv)), 1),
            "density": garment.texel_density(triangles_uv, triangles, size), "image": images["diffuse"].name,
            "maps": sorted(key for key in images if key != "diffuse") + (["alpha"] if "alpha" in results else [])}


def _combined_material(name: str, images: Dict[str, Any], alpha: bool) -> Any:
    combined = bpy.data.materials.new(f"{name}_combined")
    combined.use_nodes = True
    tree = combined.node_tree
    shader = _principled(combined)
    uv_node = tree.nodes.new("ShaderNodeUVMap")
    uv_node.uv_map = PACKED_UV

    def texture(image: Any) -> Any:
        node = tree.nodes.new("ShaderNodeTexImage")
        node.image = image
        tree.links.new(uv_node.outputs["UV"], node.inputs["Vector"])
        return node

    colour = texture(images["diffuse"])
    if shader is None:
        return combined
    tree.links.new(colour.outputs["Color"], shader.inputs["Base Color"])
    if alpha:
        tree.links.new(colour.outputs["Alpha"], shader.inputs["Alpha"])
        for name_, value in (("surface_render_method", "DITHERED"), ("blend_method", "HASHED")):
            try:
                setattr(combined, name_, value)
                break
            except (AttributeError, TypeError):
                continue
    if "normal" in images:
        normal_map = tree.nodes.new("ShaderNodeNormalMap")
        normal_map.uv_map = PACKED_UV
        tree.links.new(texture(images["normal"]).outputs["Color"], normal_map.inputs["Color"])
        tree.links.new(normal_map.outputs["Normal"], shader.inputs["Normal"])
    if "specular" in images:
        target = _input(shader, "Specular IOR Level", "Specular")
        if target is not None:
            tree.links.new(texture(images["specular"]).outputs["Color"], target)
    if "emission" in images:
        target = _input(shader, "Emission Color", "Emission")
        if target is not None:
            tree.links.new(texture(images["emission"]).outputs["Color"], target)
            strength = _input(shader, "Emission Strength")
            if strength is not None:
                strength.default_value = 1.0
    return combined


def _triangle_uv(mesh: Any, name: str) -> np.ndarray:
    uv = read_uv(mesh, name)
    mesh.calc_loop_triangles()
    loops = np.empty(len(mesh.loop_triangles) * 3, dtype=np.int64)
    mesh.loop_triangles.foreach_get("loops", loops)
    return uv[loops].reshape(-1, 3, 2)


def sollumz_lods_available() -> bool:
    return hasattr(bpy.types.Object, "sz_lods")


LOD_LEVELS = (("sollumz_medium", "medium"), ("sollumz_low", "low"))


def _bone_groups(obj: Any) -> List[int]:
    """The indices of the garment's vertex groups that are bone weights (not the add-on's own)."""
    return [g.index for g in obj.vertex_groups if g.name not in TOOL_GROUPS and not g.name.startswith(TEMP_PREFIX)]


def _limit_weights(obj: Any, mesh: Any) -> None:
    """Leaves each vertex of ``mesh`` (deformed by ``obj``'s vertex groups) its four strongest bone weights, summing to
    one, and drops the weights of the add-on's own groups."""
    bones = set(_bone_groups(obj))
    bm = bmesh.new()
    bm.from_mesh(mesh)
    layer = bm.verts.layers.deform.verify()
    for vertex in bm.verts:
        weights = vertex[layer]
        items = [(g, w) for g, w in weights.items() if g in bones and w > 1e-6]
        items.sort(key=lambda item: item[1], reverse=True)
        kept = items[: garment.MAX_INFLUENCES]
        total = sum(w for _, w in kept)
        weights.clear()
        for group, weight in kept:
            weights[group] = weight / total if total > 0 else weight
    bm.to_mesh(mesh)
    bm.free()


def _transfer(context: Any, obj: Any, mesh: Any, decimate: Optional[float] = None,
              protect: Optional[np.ndarray] = None) -> Any:
    """A new mesh from ``mesh`` (decimated to ``decimate`` of its triangles when given, ``protect`` vertices kept as
    far as the decimation allows) with the bone weights of the garment's High level taken over, at most four per
    vertex."""
    helper = bpy.data.objects.new(TEMP_PREFIX + "lod", mesh)
    context.scene.collection.objects.link(helper)
    try:
        helper.matrix_world = obj.matrix_world
        for group in obj.vertex_groups:
            if helper.vertex_groups.get(group.name) is None:  # the mesh copy carries the names already
                helper.vertex_groups.new(name=group.name)
        if decimate is not None and decimate < 1.0:
            modifier = helper.modifiers.new("DCT Decimate", "DECIMATE")
            modifier.ratio = decimate
            modifier.use_collapse_triangulate = True
            if protect is not None and protect.any():
                # The weight says how freely a vertex is decimated (0 keeps it entirely, which could miss the
                # budget): open edges and UV seams get a low one, so they go last.
                group = helper.vertex_groups.new(name=TEMP_PREFIX + "protect")
                group.add([int(i) for i in np.nonzero(~protect)[0]], 1.0, "REPLACE")
                group.add([int(i) for i in np.nonzero(protect)[0]], 0.3, "REPLACE")
                modifier.vertex_group = group.name
                modifier.vertex_group_factor = 1.0
        if _bone_groups(obj):
            transfer = helper.modifiers.new("DCT Weights", "DATA_TRANSFER")
            transfer.object = obj
            transfer.use_object_transform = True
            transfer.use_vert_data = True
            transfer.data_types_verts = {"VGROUP_WEIGHTS"}
            transfer.vert_mapping = "POLYINTERP_NEAREST"
            transfer.layers_vgroup_select_src = "ALL"
            transfer.layers_vgroup_select_dst = "NAME"
        depsgraph = context.evaluated_depsgraph_get()
        evaluated = helper.evaluated_get(depsgraph)
        result = bpy.data.meshes.new_from_object(evaluated, preserve_all_data_layers=True, depsgraph=depsgraph)
    finally:
        bpy.data.objects.remove(helper)  # the mesh stays: the caller owns it
    if _bone_groups(obj):
        _limit_weights(obj, result)
    return result


def _protected(mesh: Any) -> np.ndarray:
    """The vertices on open edges and on UV seams, which decimation would wear away."""
    protect = boundary_vertices(mesh)
    if mesh.uv_layers:
        loop_vertex, start, total = loop_arrays(mesh)
        uv = read_uv(mesh, mesh.uv_layers[0].name)
        islands = garment.uv_islands(loop_vertex, uv, start, total)
        face_of_loop = np.repeat(np.arange(len(start)), total)
        first = np.full(len(mesh.vertices), -1)
        first[loop_vertex] = islands[face_of_loop]
        last = np.full(len(mesh.vertices), -1)
        last[loop_vertex[::-1]] = islands[face_of_loop[::-1]]
        protect |= first != last  # a vertex on two UV islands lies on a seam
    return protect


def generate_lods(context: Any, obj: Any, budgets: Dict[str, int], body: Optional[Any] = None,
                  gap: float = 0.004) -> Dict[str, Any]:
    """Medium and Low levels of detail in Sollumz's LOD slots: the High mesh decimated to the triangle budgets (0: a
    share of High, never more than the budgets Durty Cloth Tool advises), open edges and UV seams kept as far as
    possible, the bone weights taken over from High (four per vertex), and pushed out of the body like High."""
    if not sollumz_lods_available():
        raise fail("garment.why.no-sollumz")
    hide_problems(obj)
    lods = obj.sz_lods
    high = lods.get_lod("sollumz_high")
    if high.mesh is None:  # as Sollumz converts an object to a drawable model
        high.mesh = obj.data
        lods.active_lod_level = "sollumz_high"
    if lods.active_lod_level != "sollumz_high":
        raise fail("garment.why.show-high")
    source = obj.data
    triangles = len(mesh_triangles(source))
    results: Dict[str, Any] = {"high": triangles}
    protect = _protected(source)
    tree = body_tree(body) if body is not None else None
    for level, short in LOD_LEVELS:
        budget = garment.lod_budget(short, triangles, int(budgets.get(short, 0)))
        copy = source.copy()
        lod_mesh = _transfer(context, obj, copy, min(1.0, budget / max(1, triangles)), protect)
        bpy.data.meshes.remove(copy)
        lod_mesh.name = f"{obj.name}_{short}"
        if tree is not None:
            positions = mesh_positions(lod_mesh, obj.matrix_world)
            signed, nearest, normals = clearance(tree, positions)
            offsets = garment.push_out_offsets(positions, nearest, normals, signed, gap)
            if np.any(offsets):
                set_mesh_positions(lod_mesh, obj.matrix_world, positions + offsets)
        old = lods.get_lod(level).mesh
        lods.get_lod(level).mesh = lod_mesh
        if old is not None and old != source and old.users == 0:
            bpy.data.meshes.remove(old)
        results[short] = len(mesh_triangles(lod_mesh))
    set_flag(obj, "dct_lods")
    clear_flags(obj, "dct_validated", FINDINGS)
    return results


def lod_meshes(obj: Any) -> List[Tuple[str, Any]]:
    lods = getattr(obj, "sz_lods", None)
    found = []
    if lods is None:
        return found
    for level, short in LOD_LEVELS:
        try:
            mesh = lods.get_lod(level).mesh
        except (AttributeError, KeyError, TypeError):
            continue
        if mesh is not None and mesh != obj.data:
            found.append((level, mesh))
    return found


def retransfer_lod_weights(context: Any, obj: Any) -> int:
    """Gives the levels of detail High's bone weights again (levels made before the garment was weighted carry
    none). Returns how many levels it changed."""
    if not _bone_groups(obj):
        return 0
    changed = 0
    for level, mesh in lod_meshes(obj):
        fresh = _transfer(context, obj, mesh)
        fresh.name = mesh.name
        obj.sz_lods.get_lod(level).mesh = fresh
        if mesh.users == 0:
            bpy.data.meshes.remove(mesh)
        changed += 1
    return changed


def _influences(obj: Any, mesh: Any) -> Tuple[int, int]:
    bones = set(_bone_groups(obj))
    return garment.influence_counts([[g.weight for g in v.groups if g.group in bones] for v in mesh.vertices])


def fit_arrays(obj: Any) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """What Fit to Body and Transfer Weights send: the garment's world positions, its triangles, the vertices the tools
    leave where they are (Pinned, the sculpt mask) and those of a lining."""
    return (world_positions(obj), mesh_triangles(obj.data), locked_vertices(obj),
            group_weights(obj, LINING_GROUP) > 0.5)


def fit_digest(obj: Any) -> str:
    """The digest of the garment's shape as Fit to Body sent it (a result is applied only to the same shape)."""
    return garment_fit.mesh_digest(world_positions(obj), mesh_triangles(obj.data))


def apply_weights(obj: Any, groups: Dict[str, List[Tuple[float, np.ndarray]]]) -> int:
    """Gives the garment the weights of a fit: one vertex group per bone name. The weights of the garment's other bone
    groups are cleared but the groups stay (so a backup's weights still name the right groups); the add-on's own
    groups are kept. Returns how many bones the garment is weighted to."""
    every = list(range(len(obj.data.vertices)))
    for group in list(obj.vertex_groups):
        if group.name not in TOOL_GROUPS and not group.name.startswith(TEMP_PREFIX):
            group.remove(every)
    for name, entries in groups.items():
        group = obj.vertex_groups.get(name) or obj.vertex_groups.new(name=name)
        for weight, indices in entries:
            group.add(indices.tolist(), float(weight), "ADD")
    obj.data.update()
    return len(groups)


def weighted(obj: Optional[Any]) -> bool:
    """Whether the garment has bone weights (vertex groups besides the add-on's own)."""
    try:
        return obj is not None and bool(_bone_groups(obj))
    except ReferenceError:
        return False


def validate_stats(obj: Any, body: Optional[Any]) -> Dict[str, Any]:
    """What :func:`garment.validate` checks, measured on the garment (and its Sollumz levels of detail)."""
    mesh = obj.data
    positions = world_positions(obj)
    stats: Dict[str, Any] = {"vertices": len(positions), "triangles_high": len(mesh_triangles(mesh))}
    stats["non_finite"] = int((~np.isfinite(positions)).any(axis=1).sum())
    stats["uv_layers"] = len(mesh.uv_layers)
    if mesh.uv_layers:
        layer = next((l for l in mesh.uv_layers if l.active_render), mesh.uv_layers[0])
        uv = read_uv(mesh, layer.name)
        stats["non_finite"] += int((~np.isfinite(uv)).any(axis=1).sum())
        outside = (uv < -0.001) | (uv > 1.001)
        stats["uv_outside"] = int(outside.any(axis=1).sum())
        stats["uv_area"] = garment.uv_area(_triangle_uv(mesh, layer.name))
    colour = mesh.color_attributes.get(COLOUR_ATTRIBUTES[0])
    if colour is None:
        stats["colour1"] = "missing"
    elif colour.domain != "CORNER" or colour.data_type != "BYTE_COLOR":
        stats["colour1"] = "format"
    else:
        stats["colour1"] = "ok"
    stats["weighted"] = weighted(obj)
    stats["unweighted"], stats["over_four"] = _influences(obj, mesh) if stats["weighted"] else (0, 0)
    for _level, lod_mesh in lod_meshes(obj):
        short = "medium" if _level == "sollumz_medium" else "low"
        stats[f"triangles_{short}"] = len(mesh_triangles(lod_mesh))
        # Levels made before the garment was weighted get High's weights when it is added; only those made after
        # count here.
        if stats["weighted"] and any(v.groups for v in lod_mesh.vertices):
            unweighted, over = _influences(obj, lod_mesh)
            stats["unweighted"] += unweighted
            stats["over_four"] += over
    if body is not None and len(positions):
        signed, nearest, body_normals = clearance(body_tree(body), positions)
        finite = np.isfinite(signed)
        stats["inside_share"] = float((signed < -garment.INSIDE_MM / 1000.0).mean())
        stats["placement"] = float(np.median(np.abs(signed[finite]))) if finite.any() else None
        near = finite & (np.abs(signed) < 0.05) & (signed > -garment.INSIDE_MM / 1000.0)
        if near.sum() >= 20:
            facing = np.einsum("ij,ij->i", vertex_normals(obj)[near], body_normals[near])
            stats["inward_share"] = float((facing < -0.2).mean())
    stats["materials"] = material_count(obj)
    return stats
