# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2026 Schmid Software Solutions (https://schmid-software.de)
"""The garment fitting tools in Blender: reading and writing the garment's mesh, the body, markers, backups, the
problem colours, the sculpt session, the moves against the body, the T-pose conversion, checking tears, and the
game-ready steps (prepare, combine materials, levels of detail, the local checks).

Only the garment chosen in the panel, the markers and the body the add-on added are changed; the maths lives in
:mod:`garment`.
"""

from __future__ import annotations

import math
import pathlib
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

from . import garment
from .strings import UserError, msg

#: Custom properties the add-on keeps on the garment (and the .blend file keeps with it).
GARMENT_TAG = "dct_garment"
BACKUPS = "dct_fit_backups"
FLAGS = ("dct_converted", "dct_checked", "dct_prepared", "dct_lods", "dct_validated")
#: The garment's latest fit check and local checks (JSON), kept with it so they always belong to this garment.
FIT_REPORT = "dct_fit_report"
FINDINGS = "dct_findings"
#: The body the add-on added: its gender, and the hosted version it came from.
BODY_TAG = "dct_body"
BODY_VERSION = "dct_body_version"
MARKER_TAG = "dct_marker"
MARKER_COLLECTION = "DCT Garment Markers"
BODY_COLLECTION = "DCT Freemode Body"
MARKER_PREFIX = "DCT_"
#: The problem colours (a colour attribute the panel adds and removes; Prepare removes it too).
PROBLEMS = "DCT Problems"
#: The garment's shape before a sculpt session (a point attribute while the session runs).
PRESCULPT = "dct_presculpt"
SCULPT_STATE = "dct_sculpt"
#: The UV layout Combine Materials bakes into, as Sollumz names the first UV map, and the one it keeps.
PACKED_UV = "UVMap 0"
SOURCE_UV = "DCT Source UV"
#: The vertex colours the ped shader reads, as Sollumz names them.
COLOUR_ATTRIBUTES = ("Color 1", "Color 2")
TEARS_GROUP = "DCT Tears"
#: The most backups kept per garment: the first (the shape before any fitting) and the newest ones.
MAX_BACKUPS = 3


def fail(key: str, **fields: Any) -> UserError:
    return UserError(msg(key, **fields))


# --------------------------------------------------------------------------------------------------
# The garment's mesh
# --------------------------------------------------------------------------------------------------


def world_positions(obj: Any) -> np.ndarray:
    mesh = obj.data
    local = np.empty(len(mesh.vertices) * 3, dtype=np.float64)
    mesh.vertices.foreach_get("co", local)
    local = local.reshape(-1, 3)
    matrix = np.array(obj.matrix_world, dtype=np.float64)
    return local @ matrix[:3, :3].T + matrix[:3, 3]


def set_world_positions(obj: Any, positions: np.ndarray) -> None:
    matrix = np.array(obj.matrix_world.inverted(), dtype=np.float64)
    local = np.asarray(positions, dtype=np.float64) @ matrix[:3, :3].T + matrix[:3, 3]
    obj.data.vertices.foreach_set("co", local.astype(np.float32).reshape(-1))
    obj.data.update()


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


def boundary_vertices(mesh: Any) -> np.ndarray:
    """The vertices on open edges (the edges of a panel)."""
    loop_edges = np.empty(len(mesh.loops), dtype=np.int64)
    mesh.loops.foreach_get("edge_index", loop_edges)
    uses = np.bincount(loop_edges, minlength=len(mesh.edges))
    edges = mesh_edges(mesh)
    mask = np.zeros(len(mesh.vertices), dtype=bool)
    open_edges = edges[uses == 1]
    mask[open_edges.reshape(-1)] = True
    return mask


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


# --------------------------------------------------------------------------------------------------
# Backups
# --------------------------------------------------------------------------------------------------


def backups(obj: Any) -> List[Any]:
    names = [name for name in str(obj.get(BACKUPS, "")).split("\n") if name]
    return [bpy.data.meshes[name] for name in names if name in bpy.data.meshes]


def backup(obj: Any) -> None:
    """Keeps a copy of the garment's mesh: the first one (the shape before any fitting) and the newest ones, at most
    :data:`MAX_BACKUPS` in all. A backup holds world positions, so it still fits after the object's transform
    changed (Prepare applies it)."""
    kept = backups(obj)
    copy = obj.data.copy()
    copy.transform(obj.matrix_world)
    copy.name = f"DCT Backup {obj.name}"
    copy.use_fake_user = True
    kept.append(copy)
    while len(kept) > MAX_BACKUPS:
        dropped = kept.pop(1)
        dropped.use_fake_user = False
        if dropped.users == 0:
            bpy.data.meshes.remove(dropped)
    obj[BACKUPS] = "\n".join(mesh.name for mesh in kept)


def drop_newest_backup(obj: Any) -> None:
    """Removes the backup a step made before it failed (the garment did not change)."""
    kept = backups(obj)
    if not kept:
        return
    newest = kept.pop()
    newest.use_fake_user = False
    if newest.users == 0:
        bpy.data.meshes.remove(newest)
    obj[BACKUPS] = "\n".join(mesh.name for mesh in kept)


def restore_pre_fit(obj: Any) -> None:
    """Puts the shape from before the first fitting step back (the backups are kept)."""
    kept = backups(obj)
    if not kept:
        raise fail("garment.why.no-backup")
    old = obj.data
    restored = kept[0].copy()
    restored.use_fake_user = False
    restored.transform(obj.matrix_world.inverted())
    restored.name = old.name
    obj.data = restored
    if old.users == 0:
        bpy.data.meshes.remove(old)
    clear_flags(obj)


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

_TREE: Dict[str, Any] = {"key": None, "tree": None}


def _body_key(body: Any) -> tuple:
    mesh = body.data
    return (body.session_uid, mesh.session_uid, len(mesh.vertices), len(mesh.polygons),
            tuple(round(v, 6) for row in body.matrix_world for v in row),
            tuple(round(c, 5) for c in mesh.vertices[0].co) if len(mesh.vertices) else ())


def body_tree(body: Any) -> BVHTree:
    """The body as a BVH tree in world space (kept while the body does not change)."""
    key = _body_key(body)
    if _TREE["key"] != key:
        positions = world_positions(body)
        triangles = mesh_triangles(body.data)
        _TREE["tree"] = BVHTree.FromPolygons(positions.tolist(), triangles.tolist(), all_triangles=True)
        _TREE["key"] = key
    return _TREE["tree"]


def clearance(tree: BVHTree, positions: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Each point's signed distance to the body (negative inside), the nearest body point and its outward
    normal."""
    count = len(positions)
    signed = np.empty(count)
    nearest = np.empty((count, 3))
    normals = np.empty((count, 3))
    find = tree.find_nearest
    for index, point in enumerate(positions):
        location, normal, _face, distance = find(Vector(point))
        if location is None:
            signed[index] = np.inf
            nearest[index] = point
            normals[index] = (0.0, 0.0, 1.0)
            continue
        nearest[index] = location
        normals[index] = normal
        offset = point - np.asarray(location)
        signed[index] = distance if float(offset @ np.asarray(normal)) >= 0.0 else -distance
    return signed, nearest, normals


def scene_body(scene: Any) -> Optional[Any]:
    props = getattr(scene, "dct_garment", None)
    body = getattr(props, "body", None) if props is not None else None
    try:
        return body if body is not None and body.type == "MESH" else None
    except ReferenceError:
        return None


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
    """One mesh in world space from several mesh objects (their materials kept in order)."""
    bm = bmesh.new()
    materials: List[Any] = []
    for obj in objects:
        mesh = obj.data.copy()
        mesh.transform(obj.matrix_world)
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


def import_body(context: Any, path: pathlib.Path, gender: str, version: Optional[str] = None) -> Any:
    """Imports a body file as one mesh object in the add-on's body collection, replacing the body the add-on
    added before. Returns the body object."""
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
    _collection(scene, BODY_COLLECTION).objects.link(body)
    _TREE["key"] = None
    return body


def import_garment(context: Any, path: pathlib.Path, *, ground: bool, category: str = "tshirt") -> Any:
    """Imports a garment file (FBX, OBJ, glTF): converted to metres, joined into one mesh object, its transform
    applied, and moved down by the ped's ground height when it was made on an avatar standing on the ground."""
    new = _import_file(path)
    meshes = [obj for obj in new if obj.type == "MESH"]
    if not meshes:
        _remove_objects(new)
        raise fail("garment.error.no-mesh")
    corners = np.concatenate([np.array([obj.matrix_world @ Vector(c) for c in obj.bound_box]) for obj in meshes])
    size = float((corners.max(axis=0) - corners.min(axis=0)).max())
    factor = garment.import_scale(size, category)
    rigged = [obj for obj in new if obj.type == "ARMATURE"]
    move = Matrix.Translation((0.0, 0.0, -GROUND_DEPTH if ground else 0.0)) @ Matrix.Scale(factor, 4)
    if rigged:
        # A rigged import stays as it is, only scaled and moved as a whole.
        for obj in new:
            if obj.parent is None:
                obj.matrix_world = move @ obj.matrix_world
        chosen = max(meshes, key=lambda o: len(o.data.vertices))
    else:
        mesh = _merged_mesh(meshes, path.stem)
        mesh.transform(move)
        target = _collection_of(meshes[0], context)
        _remove_objects(new)
        chosen = bpy.data.objects.new(path.stem, mesh)
        target.objects.link(chosen)
    chosen[GARMENT_TAG] = 1
    layer = context.view_layer
    deselect_all(layer)
    if layer.objects.get(chosen.name) is not None:
        chosen.select_set(True)
        layer.objects.active = chosen
    return chosen


#: How far below the ped's origin its soles are (metres): the freemode body stands with its soles at z -1.
GROUND_DEPTH = 1.0


def _collection_of(obj: Any, context: Any) -> Any:
    collections = list(obj.users_collection)
    return collections[0] if collections else context.scene.collection


# --------------------------------------------------------------------------------------------------
# Markers
# --------------------------------------------------------------------------------------------------


def marker_objects(scene: Any) -> Dict[str, Any]:
    found = {}
    for obj in scene.objects:
        name = obj.get(MARKER_TAG)
        if name in garment.MARKERS:
            found[name] = obj
    return found


def read_markers(scene: Any) -> Dict[str, Tuple[float, float, float]]:
    return {name: tuple(obj.matrix_world.translation) for name, obj in marker_objects(scene).items()}


def write_markers(scene: Any, markers: Dict[str, Any], size: float) -> List[Any]:
    """Creates or moves the marker empties (spheres in the markers collection)."""
    existing = marker_objects(scene)
    collection = _collection(scene, MARKER_COLLECTION)
    written = []
    for name in garment.MARKERS:
        if name not in markers:
            continue
        obj = existing.get(name)
        if obj is None:
            obj = bpy.data.objects.new(f"{MARKER_PREFIX}{name}", None)
            obj.empty_display_type = "SPHERE"
            obj[MARKER_TAG] = name
            obj.show_in_front = True
            collection.objects.link(obj)
        obj.empty_display_size = size
        obj.matrix_world = Matrix.Translation(Vector(markers[name]))
        written.append(obj)
    return written


def resize_markers(scene: Any, size: float) -> None:
    for obj in marker_objects(scene).values():
        obj.empty_display_size = size


# --------------------------------------------------------------------------------------------------
# Regions, the fit check and the problem colours
# --------------------------------------------------------------------------------------------------


def regions(scene: Any, obj: Any, category: str, positions: np.ndarray, edges: np.ndarray) -> np.ndarray:
    """The region of each garment vertex, from the markers in the scene (placed now when there are none)."""
    if category == "shoes":
        return np.full(len(positions), garment.REGIONS.index("legs"))
    markers = read_markers(scene)
    if "pelvis" not in markers:
        markers = garment.auto_markers(positions, category if category != "shoes" else "pants",
                                       scene.dct_garment.source_pose, edges)
    return garment.classify_regions(positions, markers)


def measure(scene: Any, obj: Any, body: Any) -> Dict[str, Any]:
    """The garment against the body: clearance, nearest points, normals and regions."""
    positions = world_positions(obj)
    edges = mesh_edges(obj.data)
    signed, nearest, normals = clearance(body_tree(body), positions)
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
# Moves against the body
# --------------------------------------------------------------------------------------------------


def push_out(obj: Any, body: Any, gap: float, passes: int = 3) -> Dict[str, int]:
    """Moves every vertex closer to the body than ``gap`` to ``gap`` outside it; the vertices around follow
    softly, so no crease forms. Returns how many vertices were inside before and after, and how many moved."""
    tree = body_tree(body)
    positions = world_positions(obj)
    edges = mesh_edges(obj.data)
    start = positions.copy()
    before = None
    for _ in range(max(1, passes)):
        signed, nearest, normals = clearance(tree, positions)
        if before is None:
            before = int((signed < -garment.INSIDE_MM / 1000.0).sum())
        needs = signed < gap - 1e-5
        if not np.any(needs):
            break
        offsets = garment.push_out_offsets(positions, nearest, normals, signed, gap)
        offsets = garment.spread_offsets(offsets, edges, needs, iterations=3)
        positions = positions + offsets
    signed, _, _ = clearance(tree, positions)
    set_world_positions(obj, positions)
    moved = int((np.linalg.norm(positions - start, axis=1) > 1e-4).sum())
    return {"before": before or 0, "after": int((signed < -garment.INSIDE_MM / 1000.0).sum()), "moved": moved}


def region_weights(data: Dict[str, Any], region: str) -> np.ndarray:
    mask = data["regions"] == garment.REGIONS.index(region)
    return garment.soft_mask(mask, data["edges"], rings=3)


def snug(scene: Any, obj: Any, body: Any, region: str, gap: float, amount: float) -> Dict[str, Any]:
    data = measure(scene, obj, body)
    weights = region_weights(data, region)
    if not np.any(data["regions"] == garment.REGIONS.index(region)):
        raise fail("garment.why.region-empty", region=msg(f"garment.region.{region}"))
    offsets = garment.snug_offsets(data["positions"], data["nearest"], data["normals"], data["clearance"], gap,
                                   amount, weights)
    positions = data["positions"] + offsets
    set_world_positions(obj, positions)
    moved = np.linalg.norm(offsets, axis=1)
    count = int((moved > 1e-4).sum())
    return {"moved": count, "mean": round(float(moved[moved > 1e-4].mean() * 1000.0), 1) if count else 0.0}


def relax(scene: Any, obj: Any, body: Optional[Any], region: str, amount: float, gap: float) -> Dict[str, Any]:
    positions = world_positions(obj)
    edges = mesh_edges(obj.data)
    try:
        markers_region = regions(scene, obj, scene.dct_garment.category, positions, edges)
    except garment.MarkerError:
        markers_region = np.full(len(positions), garment.OTHER)
    mask = markers_region == garment.REGIONS.index(region)
    if not np.any(mask):
        raise fail("garment.why.region-empty", region=msg(f"garment.region.{region}"))
    weights = garment.soft_mask(mask, edges, rings=3)
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


#: Blender's own Grab brush among its essentials brushes (Blender 4.3 and later).
GRAB_BRUSH = "brushes/essentials_brushes-mesh_sculpt.blend/Brush/Grab"


def _set_grab_brush(context: Any, radius: float, strength: float) -> None:
    """Chooses the Grab brush (an essentials asset from Blender 4.3 on, a tool in 4.2) and sets its size and
    strength in scene units."""
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
    for settings in (brush, getattr(tool, "unified_paint_settings", None),
                     getattr(sculpt, "unified_paint_settings", None)):
        if settings is None:
            continue
        try:
            if hasattr(settings, "use_locked_size"):
                settings.use_locked_size = "SCENE"
            if hasattr(settings, "unprojected_radius"):
                settings.unprojected_radius = radius
            if hasattr(settings, "strength"):
                settings.strength = strength
        except (AttributeError, TypeError, RuntimeError):
            continue  # an asset brush that cannot be changed here keeps its own settings


def start_sculpt(context: Any, obj: Any, body: Optional[Any], radius: float, strength: float, mirror_x: bool) -> int:
    """Keeps the garment's shape, then switches it to Sculpt Mode with the Grab brush. Returns how many vertices
    are inside the body now."""
    mesh = obj.data
    attribute = mesh.attributes.get(PRESCULPT) or mesh.attributes.new(PRESCULPT, "FLOAT_VECTOR", "POINT")
    co = np.empty(len(mesh.vertices) * 3, dtype=np.float32)
    mesh.vertices.foreach_get("co", co)
    attribute.data.foreach_set("vector", co)
    inside = 0
    if body is not None:
        signed, _, _ = clearance(body_tree(body), world_positions(obj))
        inside = int((signed < -garment.INSIDE_MM / 1000.0).sum())
    obj[SCULPT_STATE] = {"inside": inside, "mirror": int(bool(mesh.use_mirror_x)),
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
        raise fail("garment.error.mode", detail=str(exc)) from exc
    _set_grab_brush(context, radius, strength)
    return inside


def _end_sculpt(context: Any, obj: Any, body: Optional[Any]) -> Dict[str, Any]:
    state = dict(obj.get(SCULPT_STATE, {}) or {})
    if obj.mode != "OBJECT":
        layer = context.view_layer
        layer.objects.active = obj
        bpy.ops.object.mode_set(mode="OBJECT")
    obj.data.use_mirror_x = bool(state.get("mirror", 0))
    if body is not None and state.get("body_display") in ("BOUNDS", "WIRE", "SOLID", "TEXTURED"):
        body.display_type = state["body_display"]
    if SCULPT_STATE in obj:
        del obj[SCULPT_STATE]
    return state


def accept_sculpt(context: Any, obj: Any, body: Optional[Any], keep_out: bool, gap: float) -> Dict[str, int]:
    """Keeps the sculpted shape (moving what went into the body back out when ``keep_out``) and ends the
    session."""
    state = _end_sculpt(context, obj, body)
    mesh = obj.data
    now = np.empty(len(mesh.vertices) * 3, dtype=np.float32)
    mesh.vertices.foreach_get("co", now)
    snapshot = mesh.attributes.get(PRESCULPT)
    before = now.copy()  # without the snapshot (a remesh drops it) nothing counts as moved
    if snapshot is not None:
        snapshot.data.foreach_get("vector", before)
        mesh.attributes.remove(snapshot)
    moved_mask = np.linalg.norm((now - before).reshape(-1, 3), axis=1) > 1e-4
    inside_after = 0
    if body is not None:
        tree = body_tree(body)
        positions = world_positions(obj)
        signed, _, _ = clearance(tree, positions)
        if keep_out and np.any(moved_mask):
            fix = np.nonzero(moved_mask & (signed < gap))[0]
            if len(fix):
                matrix = np.array(obj.matrix_world, dtype=np.float64)
                start = before.reshape(-1, 3)[fix].astype(np.float64) @ matrix[:3, :3].T + matrix[:3, 3]
                positions[fix] = _back_out(tree, start, positions[fix], gap)
                set_world_positions(obj, positions)
                signed, _, _ = clearance(tree, positions)
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


def cancel_sculpt(context: Any, obj: Any, body: Optional[Any]) -> None:
    """Puts the shape from before the session back and ends it."""
    _end_sculpt(context, obj, body)
    mesh = obj.data
    snapshot = mesh.attributes.get(PRESCULPT)
    if snapshot is None:
        raise fail("garment.why.no-session")  # the shape from before is gone (a remesh drops it); Ctrl+Z still has it
    before = np.empty(len(mesh.vertices) * 3, dtype=np.float32)
    snapshot.data.foreach_get("vector", before)
    mesh.vertices.foreach_set("co", before)
    mesh.attributes.remove(snapshot)
    mesh.update()


# --------------------------------------------------------------------------------------------------
# T-pose to A-pose and the tear check (armatures)
# --------------------------------------------------------------------------------------------------

_ARM_BONES = (("spine", "pelvis", "chest", None), ("neck", "chest", "neck", "spine"),
              ("clavicle_L", "chest", "shoulder_l", "spine"), ("upperarm_L", "shoulder_l", "elbow_l", "clavicle_L"),
              ("forearm_L", "elbow_l", "wrist_l", "upperarm_L"),
              ("clavicle_R", "chest", "shoulder_r", "spine"), ("upperarm_R", "shoulder_r", "elbow_r", "clavicle_R"),
              ("forearm_R", "elbow_r", "wrist_r", "upperarm_R"))
TEMP_PREFIX = "DCT_tmp_"


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


def tpose_to_apose(context: Any, obj: Any, markers: Dict[str, Any], target: float) -> Dict[str, Any]:
    """Lowers the arms of a garment modelled in T-pose to ``target`` degrees below the horizontal: a temporary
    armature from the markers, Blender's automatic weights, the upper arms rotated down, the result applied and
    the armature removed. The markers follow."""
    needed = ("pelvis", "chest", "neck", "shoulder_l", "elbow_l", "wrist_l", "shoulder_r", "elbow_r", "wrist_r")
    missing = [name for name in needed if name not in markers]
    if missing:
        raise fail("garment.why.markers")
    rotations = garment.arm_rotations(markers, target)
    if all(abs(angle) < 1.0 for angle in rotations.values()):
        return {"rotated": 0.0, "filled": 0}
    scene = context.scene
    data = bpy.data.armatures.new(TEMP_PREFIX + "rig")
    rig = bpy.data.objects.new(TEMP_PREFIX + "rig", data)
    scene.collection.objects.link(rig)
    saved_matrix = obj.matrix_world.copy()
    saved_parent = (obj.parent, obj.parent_type, obj.parent_bone, obj.matrix_parent_inverse.copy())
    saved_groups = {group.name for group in obj.vertex_groups}
    # The garment's own modifiers stay off while the arms are read, so only the temporary armature counts.
    shown = [(modifier, modifier.show_viewport) for modifier in obj.modifiers]
    for modifier, _ in shown:
        modifier.show_viewport = False
    try:
        layer = context.view_layer
        layer.objects.active = rig
        with context.temp_override(**_override(rig)):
            bpy.ops.object.mode_set(mode="EDIT")
            bones = {}
            for name, head, tail, parent in _ARM_BONES:
                bone = data.edit_bones.new(TEMP_PREFIX + name)
                bone.head = Vector(markers[head])
                bone.tail = Vector(markers[tail])
                if (bone.tail - bone.head).length < 1e-3:
                    bone.tail = bone.head + Vector((0.0, 0.0, 0.05))
                if parent is not None:
                    bone.parent = bones[parent]
                bones[name] = bone
            bpy.ops.object.mode_set(mode="OBJECT")
        deselect_all(layer)
        obj.select_set(True)
        rig.select_set(True)
        layer.objects.active = rig
        with context.temp_override(**_override(rig, obj, rig)):
            bpy.ops.object.parent_set(type="ARMATURE_AUTO")
        filled = _fill_missing_weights(obj, rig)
        layer.update()
        for suffix, angle in rotations.items():
            pose = rig.pose.bones[TEMP_PREFIX + f"upperarm_{suffix.upper()}"]
            head = pose.bone.head_local
            pose.matrix = (Matrix.Translation(head) @ Matrix.Rotation(math.radians(angle), 4, "Y")
                           @ Matrix.Translation(-head) @ pose.bone.matrix_local)
        layer.update()
        evaluated = obj.evaluated_get(context.evaluated_depsgraph_get())
        posed = np.array([evaluated.matrix_world @ v.co for v in evaluated.data.vertices], dtype=np.float64)
        if len(posed) != len(obj.data.vertices):
            raise fail("garment.why.modifiers")
    finally:
        for modifier in [m for m in obj.modifiers if m.type == "ARMATURE" and m.object == rig]:
            obj.modifiers.remove(modifier)
        for modifier, visible in shown:
            modifier.show_viewport = visible
        obj.parent, obj.parent_type, obj.parent_bone = saved_parent[:3]
        obj.matrix_parent_inverse = saved_parent[3]
        obj.matrix_world = saved_matrix
        for group in list(obj.vertex_groups):
            if group.name.startswith(TEMP_PREFIX) and group.name not in saved_groups:
                obj.vertex_groups.remove(group)
        _remove_objects([rig])
    set_world_positions(obj, posed)
    moved = dict(markers)
    for suffix, angle in rotations.items():
        pivot = markers[f"shoulder_{suffix}"]
        for joint in ("elbow", "wrist"):
            point = garment.rotate_about_y(np.array([markers[f"{joint}_{suffix}"]]), pivot, angle)[0]
            moved[f"{joint}_{suffix}"] = tuple(point)
    write_markers(scene, moved, scene.dct_garment.marker_size)
    set_flag(obj, "dct_converted")
    return {"rotated": round(max(abs(a) for a in rotations.values()), 1), "filled": filled}


def _fill_missing_weights(obj: Any, rig: Any) -> int:
    """Vertices Blender's automatic weights left empty (separate panels, for example) get the nearest bone."""
    groups = {group.index: group for group in obj.vertex_groups if group.name.startswith(TEMP_PREFIX)}
    empty = [v.index for v in obj.data.vertices
             if not any(g.group in groups and g.weight > 1e-6 for g in v.groups)]
    if not empty:
        return 0
    positions = world_positions(obj)[empty]
    segments = []
    for bone in rig.data.bones:
        group = obj.vertex_groups.get(bone.name)
        if group is not None:
            head = np.asarray(rig.matrix_world @ bone.head_local)
            tail = np.asarray(rig.matrix_world @ bone.tail_local)
            segments.append((group, head, tail))
    if not segments:
        return 0
    distances = []
    for _group, head, tail in segments:
        axis = tail - head
        t = np.clip((positions - head) @ axis / max(float(axis @ axis), 1e-12), 0.0, 1.0)
        distances.append(np.linalg.norm(positions - (head + t[:, None] * axis), axis=1))
    nearest = np.argmin(np.array(distances), axis=0)
    for index, choice in zip(empty, nearest):
        segments[int(choice)][0].add([index], 1.0, "REPLACE")
    return len(empty)


#: Synthetic test poses: (text key, [(bone name parts, world axis, degrees for the left side)]).
TEST_POSES = (
    ("garment.pose.arms-up", [(("upperarm", "upper_arm"), "Y", -75.0)]),
    ("garment.pose.arms-forward", [(("upperarm", "upper_arm"), "Z", -70.0)]),
    ("garment.pose.legs-forward", [(("thigh",), "X", -60.0)]),
    ("garment.pose.twist", [(("spine3", "spine2", "spine"), "Z", 25.0)]),
)


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
        matching = [pose for pose in rig.pose.bones if part in pose.name.lower()]
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


def check_tears(context: Any, obj: Any, threshold: float = 0.005, seam: float = 0.001) -> Dict[str, Any]:
    """Poses the garment's armature through a few test poses and reports where neighbouring vertices separate
    (open seams that tear) and how far, and which edges stretch a lot. The torn vertices go into the vertex group
    ``DCT Tears``; the pose is put back afterwards."""
    rig = armature_of(obj)
    mesh = obj.data
    rest = world_positions(obj)
    pairs = garment.seam_pairs(rest, seam, boundary_vertices(mesh))
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
    return {"poses": results, "pairs": int(len(pairs)), "vertices": len(torn_vertices)}


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


def prepare(context: Any, obj: Any, weld: float, colours: Sequence[Sequence[float]], overwrite: bool) -> Dict[str, Any]:
    """Welds the panel seams within ``weld`` metres (never a lining onto its shell), removes loose and degenerate
    geometry, triangulates, shades smooth and adds the ped vertex colours."""
    hide_problems(obj)
    applied = apply_transform(obj)
    mesh = obj.data
    tears_group = obj.vertex_groups.get(TEARS_GROUP)
    if tears_group is not None:
        obj.vertex_groups.remove(tears_group)
    if mesh.attributes.get(PRESCULPT) is not None:
        mesh.attributes.remove(mesh.attributes[PRESCULPT])
    matrix = obj.matrix_world
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.verts.ensure_lookup_table()
    bm.normal_update()
    count = len(bm.verts)
    positions = np.array([matrix @ v.co for v in bm.verts], dtype=np.float64).reshape(-1, 3)
    turn = matrix.to_3x3().inverted().transposed()  # normals follow the object's rotation and scale
    normals = np.array([(turn @ v.normal).normalized() for v in bm.verts], dtype=np.float64).reshape(-1, 3)
    boundary = np.array([v.is_boundary for v in bm.verts], dtype=bool)
    material = np.array([v.link_faces[0].material_index if v.link_faces else -1 for v in bm.verts])
    linings = garment.lining_pairs(positions, normals, material) if len(set(material.tolist())) > 1 else []
    target, merged = garment.weld_targets(positions, weld, boundary, material if linings else None)
    inverse = matrix.inverted()
    targetmap = {}
    for index in np.nonzero(target != np.arange(count))[0]:
        root = int(target[index])
        targetmap[bm.verts[int(index)]] = bm.verts[root]
    for root in set(int(t) for t in target[target != np.arange(count)]):
        bm.verts[root].co = inverse @ Vector(merged[root])
    welded = len(targetmap)
    if targetmap:
        bmesh.ops.weld_verts(bm, targetmap=targetmap)
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
    clear_flags(obj, "dct_validated", "dct_lods", FINDINGS)
    return {"welded": welded, "removed": removed, "triangles": triangles, "lining": bool(linings),
            "colours": colours_written, "applied": applied}


def _texture_nodes(material: Any) -> List[Any]:
    if material is None or not material.use_nodes or material.node_tree is None:
        return []
    return [node for node in material.node_tree.nodes if node.type == "TEX_IMAGE" and node.image is not None]


def combine_materials(context: Any, obj: Any, size: int, cut_strips: bool) -> Dict[str, Any]:
    """Packs every UV island of the garment into one 0 to 1 layout (long thin strips cut into pieces first) and
    bakes the base colour of all its materials into one image of ``size`` pixels, which becomes the garment's only
    material. The original UV layout is kept as ``DCT Source UV``."""
    mesh = obj.data
    if not mesh.uv_layers:
        raise fail("garment.why.no-uv")
    if any(slot.material is None for slot in obj.material_slots) or not obj.material_slots:
        raise fail("garment.why.empty-slot")
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
    margin = 4.0 / size * 2
    with context.temp_override(**_override(obj)):
        bpy.ops.object.mode_set(mode="EDIT")
        try:
            bpy.ops.mesh.select_all(action="SELECT")
            bpy.ops.uv.select_all(action="SELECT")
            bpy.ops.uv.average_islands_scale()
            bpy.ops.uv.pack_islands(rotate=True, scale=True, margin_method="FRACTION", margin=margin,
                                    shape_method="CONCAVE")
        finally:
            bpy.ops.object.mode_set(mode="OBJECT")

    image = bpy.data.images.new(f"{obj.name}_diffuse", size, size, alpha=False)
    added: List[Tuple[Any, Any]] = []
    materials = []
    for slot in obj.material_slots:
        if slot.material is not None and slot.material not in materials:
            materials.append(slot.material)
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
        bake_node = tree.nodes.new("ShaderNodeTexImage")
        bake_node.image = image
        bake_uv = tree.nodes.new("ShaderNodeUVMap")
        bake_uv.uv_map = PACKED_UV
        tree.links.new(bake_uv.outputs["UV"], bake_node.inputs["Vector"])
        for node in tree.nodes:
            node.select = False
        bake_node.select = True
        tree.nodes.active = bake_node
        added += [(material, bake_node), (material, bake_uv)]

    scene = context.scene
    render = scene.render
    saved = {"engine": render.engine}
    bake = render.bake
    saved_bake = {name: getattr(bake, name) for name in ("use_pass_direct", "use_pass_indirect", "use_pass_color",
                                                         "margin", "margin_type", "use_clear", "target")}
    try:
        render.engine = "CYCLES"
        cycles = getattr(scene, "cycles", None)
        if cycles is not None:
            saved["samples"] = cycles.samples
            cycles.samples = 1
        bake.use_pass_direct = False
        bake.use_pass_indirect = False
        bake.use_pass_color = True
        bake.margin = 8
        bake.margin_type = "EXTEND"
        bake.use_clear = True
        bake.target = "IMAGE_TEXTURES"
        with context.temp_override(**_override(obj)):
            result = bpy.ops.object.bake(type="DIFFUSE", uv_layer=PACKED_UV)
        if "FINISHED" not in result:
            raise fail("garment.error.bake", detail=", ".join(sorted(result)))
    except RuntimeError as exc:
        raise fail("garment.error.bake", detail=str(exc).strip()) from exc
    finally:
        render.engine = saved["engine"]
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
    image.pack()

    combined = bpy.data.materials.new(f"{obj.name}_combined")
    combined.use_nodes = True
    tree = combined.node_tree
    shader = next((n for n in tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
    texture = tree.nodes.new("ShaderNodeTexImage")
    texture.image = image
    uv_node = tree.nodes.new("ShaderNodeUVMap")
    uv_node.uv_map = PACKED_UV
    tree.links.new(uv_node.outputs["UV"], texture.inputs["Vector"])
    if shader is not None:
        tree.links.new(texture.outputs["Color"], shader.inputs["Base Color"])
    mesh.materials.clear()
    mesh.materials.append(combined)
    mesh.polygons.foreach_set("material_index", np.zeros(len(mesh.polygons), dtype=np.int32))
    mesh.update()
    triangles_uv = _triangle_uv(mesh, PACKED_UV)
    clear_flags(obj, "dct_validated", "dct_lods", FINDINGS)  # levels of detail made before keep the old materials
    return {"materials": len(materials), "size": size, "cut": cut,
            "used": round(100.0 * min(1.0, garment.uv_area(triangles_uv)), 1), "image": image.name}


def _triangle_uv(mesh: Any, name: str) -> np.ndarray:
    uv = read_uv(mesh, name)
    mesh.calc_loop_triangles()
    loops = np.empty(len(mesh.loop_triangles) * 3, dtype=np.int64)
    mesh.loop_triangles.foreach_get("loops", loops)
    return uv[loops].reshape(-1, 3, 2)


def sollumz_lods_available() -> bool:
    return hasattr(bpy.types.Object, "sz_lods")


LOD_LEVELS = (("sollumz_medium", "medium"), ("sollumz_low", "low"))


def generate_lods(context: Any, obj: Any, budgets: Dict[str, int]) -> Dict[str, Any]:
    """Medium and Low levels of detail in Sollumz's LOD slots: the High mesh decimated to the triangle budgets,
    and the weights taken over from High with a Data Transfer."""
    if not sollumz_lods_available():
        raise fail("garment.why.no-sollumz")
    lods = obj.sz_lods
    high = lods.get_lod("sollumz_high")
    if high.mesh is None:  # as Sollumz converts an object to a drawable model
        high.mesh = obj.data
        lods.active_lod_level = "sollumz_high"
    if lods.active_lod_level != "sollumz_high":
        raise fail("garment.why.show-high")
    source = obj.data
    triangles = len(mesh_triangles(source))
    results = {"high": triangles}
    collection = context.scene.collection
    for level, short in LOD_LEVELS:
        budget = max(4, int(budgets[short]))
        copy = source.copy()
        helper = bpy.data.objects.new(TEMP_PREFIX + short, copy)
        collection.objects.link(helper)
        try:
            for group in obj.vertex_groups:
                if helper.vertex_groups.get(group.name) is None:  # the mesh copy carries the names already
                    helper.vertex_groups.new(name=group.name)
            ratio = min(1.0, budget / max(1, triangles))
            if ratio < 1.0:
                decimate = helper.modifiers.new("DCT Decimate", "DECIMATE")
                decimate.ratio = ratio
                decimate.use_collapse_triangulate = True
            if obj.vertex_groups:
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
            lod_mesh = bpy.data.meshes.new_from_object(evaluated, preserve_all_data_layers=True, depsgraph=depsgraph)
            lod_mesh.name = f"{obj.name}_{short}"
        finally:
            _remove_objects([helper])
        old = lods.get_lod(level).mesh
        lods.get_lod(level).mesh = lod_mesh
        if old is not None and old != source and old.users == 0:
            bpy.data.meshes.remove(old)
        results[short] = len(mesh_triangles(lod_mesh))
    set_flag(obj, "dct_lods")
    clear_flags(obj, "dct_validated", FINDINGS)
    return results


def _tool_groups(obj: Any) -> set:
    """The add-on's own vertex groups (the tear check's, a conversion's leftovers), which are no bone weights."""
    return {g.index for g in obj.vertex_groups if g.name == TEARS_GROUP or g.name.startswith(TEMP_PREFIX)}


def _influences(obj: Any, mesh: Any) -> Tuple[int, int]:
    tools = _tool_groups(obj)
    return garment.influence_counts([[g.weight for g in v.groups if g.group not in tools] for v in mesh.vertices])


def _weights(obj: Any, mesh: Any) -> Tuple[Optional[bool], int, int]:
    if len(obj.vertex_groups) == len(_tool_groups(obj)):
        return False, 0, 0
    unweighted, over = _influences(obj, mesh)
    return True, unweighted, over


def validate_stats(obj: Any, body: Optional[Any]) -> Dict[str, Any]:
    """What :func:`garment.validate` checks, measured on the garment (and its Sollumz levels of detail)."""
    mesh = obj.data
    positions = world_positions(obj)
    stats: Dict[str, Any] = {"vertices": len(positions), "triangles": len(mesh_triangles(mesh))}
    stats["non_finite"] = int((~np.isfinite(positions)).any(axis=1).sum())
    stats["uv_layers"] = len(mesh.uv_layers)
    loop_vertex, _start, total = loop_arrays(mesh)
    material_of_face = np.empty(len(mesh.polygons), dtype=np.int64)
    mesh.polygons.foreach_get("material_index", material_of_face)
    loop_material = np.repeat(material_of_face, total)
    uv = None
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
    stats["weighted"], stats["unweighted"], stats["over_four"] = _weights(obj, mesh)
    stats["game_vertices_high"] = garment.game_vertex_count(loop_vertex, uv, loop_material)
    if sollumz_lods_available():
        for level, short in LOD_LEVELS:
            lod_mesh = obj.sz_lods.get_lod(level).mesh
            if lod_mesh is not None and lod_mesh != mesh:
                lod_vertex, _s, lod_total = loop_arrays(lod_mesh)
                lod_uv = read_uv(lod_mesh, lod_mesh.uv_layers[0].name) if lod_mesh.uv_layers else None
                stats[f"game_vertices_{short}"] = garment.game_vertex_count(lod_vertex, lod_uv)
                if stats["weighted"]:
                    unweighted, over = _influences(obj, lod_mesh)
                    stats["unweighted"] += unweighted
                    stats["over_four"] += over
    if body is not None:
        signed, _, _ = clearance(body_tree(body), positions)
        stats["inside_share"] = float((signed < -garment.INSIDE_MM / 1000.0).mean()) if len(signed) else 0.0
    stats["materials"] = material_count(obj)
    return stats
