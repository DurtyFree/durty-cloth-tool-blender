# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2026 Schmid Software Solutions (https://schmid-software.de)
"""Custom Ped in Blender: the character's collection and parts, the facts its checks read and their fixes, the markers
(empties), the ray casts of the click guide, the meshes a rig request carries, applying a rig (the armature from the
rig's bones without turning any of them, the weights as vertex groups by bone name, the game's rest pose and the
character's own pose), the poses, the local checks, the backups and the GLB export for Durty Cloth Tool.

Only the character's own objects, its markers and the armature the add-on made are changed; the maths lives in
:mod:`ped`.
"""

from __future__ import annotations

import json
import pathlib
import secrets
import time
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

from . import ped
from .strings import UserError, msg

#: On the character's collection: its id, the confirmations (rights, facing), the old rig's joints, the applied rig
#: (JSON), whether Run Checks passed, and the project Durty Cloth Tool created.
CHARACTER = "dct_ped_character"
RIGHTS = "dct_ped_rights"
FACING = "dct_ped_facing"
OLD_JOINTS = "dct_ped_old_joints"
RIG_INFO = "dct_ped_rig"
CHECKED = "dct_ped_checked"
SENT = "dct_ped_sent"
PREVIOUS_RIG = "dct_ped_previous_rig"
#: On the armature the add-on made: the character's id (``PREVIOUS_OF`` while it is the previous rig's).
ARMATURE = "dct_ped_armature"
PREVIOUS_OF = "dct_ped_previous_of"
#: On each bone: the rig's rest matrix and the character's pose (16 floats each, Blender's 4x4 row by row) and the
#: bone's tag.
BONE_REST = "dct_rest"
BONE_POSE = "dct_pose"
BONE_TAG = "dct_tag"
#: On each part: its mesh before the first rig, and the previous rig's mesh with its vertex group names.
ORIGINAL = "dct_ped_original"
PREVIOUS_MESH = "dct_ped_previous"
PREVIOUS_GROUPS = "dct_ped_previous_groups"
#: On a marker empty: its name and the character's id.
MARKER = "dct_ped_marker"
MARKER_OF = "dct_ped_marker_of"
MARKER_PREFIX = "DCT_ped_"
MODIFIER = "DCT Rig"
#: The glTF exporter's settings for the GLB Durty Cloth Tool reads (spike S3, Blender 5.2: joints keep their names and
#: exact rest transforms, at most four weights, images embedded, every bone exported even without weights).
GLB_OPTIONS: Dict[str, Any] = {
    "export_format": "GLB", "export_image_format": "AUTO", "export_image_add_webp": False,
    "export_keep_originals": False, "export_texcoords": True, "export_normals": True, "export_tangents": False,
    "export_materials": "EXPORT", "export_vertex_color": "NONE", "export_attributes": False, "export_extras": False,
    "export_yup": True, "export_apply": True, "export_shared_accessors": False,
    "export_draco_mesh_compression_enable": False, "export_meshopt_compression_enable": False,
    "export_use_gltfpack": False, "export_gn_mesh": False, "use_mesh_edges": False, "use_mesh_vertices": False,
    "export_cameras": False, "export_lights": False, "use_selection": True, "use_visible": False,
    "use_renderable": False, "use_active_collection": False, "use_active_scene": False, "export_skins": True,
    "export_influence_nb": 4, "export_all_influences": False, "export_def_bones": False, "export_leaf_bone": False,
    "export_hierarchy_flatten_bones": False, "export_hierarchy_flatten_objs": False,
    "export_armature_object_remove": False, "export_rest_position_armature": True, "export_animations": False,
    "export_morph": False, "export_current_frame": False, "will_save_settings": False, "check_existing": False,
}
#: The add-on's folder (inside its data folder) for the export of a send, one folder per send, removed right after.
WORK_FOLDER = "ped-send"


def fail(key: str, **fields: Any) -> UserError:
    return UserError(msg(key, **fields))


def _alive(obj: Any) -> bool:
    try:
        obj.name
        return True
    except (ReferenceError, AttributeError):
        return False


# --------------------------------------------------------------------------------------------------
# The character
# --------------------------------------------------------------------------------------------------


def character_id(collection: Any) -> str:
    """The character's own id, given to it now when it has none or another collection has the same one (a copy)."""
    current = collection.get(CHARACTER)
    taken = isinstance(current, str) and any(other != collection and other.get(CHARACTER) == current
                                             for other in bpy.data.collections)
    if not isinstance(current, str) or not current or taken:
        current = secrets.token_hex(6)
        collection[CHARACTER] = current
    return current


def parts(collection: Optional[Any]) -> List[Any]:
    """The character's meshes, by name (never its markers or backups)."""
    if collection is None or not _alive(collection):
        return []
    return sorted((obj for obj in collection.all_objects if obj.type == "MESH" and not obj.get(MARKER)),
                  key=lambda obj: obj.name)


def armature(collection: Optional[Any]) -> Optional[Any]:
    """The armature the add-on made for the character (its current rig), or ``None``."""
    if collection is None or not _alive(collection):
        return None
    ident = collection.get(CHARACTER)
    for obj in collection.all_objects:
        if obj.type == "ARMATURE" and ident and obj.get(ARMATURE) == ident:
            return obj
    return None


def previous_armature(collection: Optional[Any]) -> Optional[Any]:
    if collection is None or not _alive(collection):
        return None
    ident = collection.get(CHARACTER)
    for obj in bpy.data.objects:
        if obj.type == "ARMATURE" and ident and obj.get(PREVIOUS_OF) == ident:
            return obj
    return None


def role_of(obj: Any) -> str:
    """A part's role: the one chosen in the panel, or the one its names suggest."""
    chosen = getattr(obj, "dct_ped_role", ped.AUTO_ROLE)
    if chosen in ped.ROLES:
        return chosen
    materials = [slot.material.name for slot in obj.material_slots if slot.material is not None]
    return ped.guess_role(obj.name, materials)


def use_selected(context: Any) -> Any:
    """The selected meshes become the character: the collection that holds exactly them, or a new one named after
    the active object that they move into."""
    meshes = [obj for obj in context.selected_objects if obj.type == "MESH" and not obj.get(MARKER)]
    if not meshes:
        raise fail("ped.why.select-meshes")
    scene = context.scene
    shared = set(meshes[0].users_collection)
    for obj in meshes[1:]:
        shared &= set(obj.users_collection)
    for collection in shared:
        if collection != scene.collection and {o for o in collection.all_objects if o.type == "MESH"
                                               and not o.get(MARKER)} == set(meshes):
            character_id(collection)
            return collection
    active = context.active_object if context.active_object in meshes else meshes[0]
    collection = bpy.data.collections.new(active.name)
    scene.collection.children.link(collection)
    for obj in meshes:
        for old in list(obj.users_collection):
            old.objects.unlink(obj)
        collection.objects.link(obj)
    character_id(collection)
    return collection


def mesh_triangles(mesh: Any) -> np.ndarray:
    mesh.calc_loop_triangles()
    triangles = np.empty(len(mesh.loop_triangles) * 3, dtype=np.int64)
    mesh.loop_triangles.foreach_get("vertices", triangles)
    return triangles.reshape(-1, 3)


def mesh_edges(mesh: Any) -> np.ndarray:
    edges = np.empty(len(mesh.edges) * 2, dtype=np.int64)
    mesh.edges.foreach_get("vertices", edges)
    return edges.reshape(-1, 2)


def local_positions(mesh: Any) -> np.ndarray:
    values = np.empty(len(mesh.vertices) * 3, dtype=np.float64)
    mesh.vertices.foreach_get("co", values)
    return values.reshape(-1, 3)


def world_positions(obj: Any) -> np.ndarray:
    m = np.array(obj.matrix_world, dtype=np.float64)
    return local_positions(obj.data) @ m[:3, :3].T + m[:3, 3]


def set_local_positions(mesh: Any, positions: np.ndarray) -> None:
    mesh.vertices.foreach_set("co", np.asarray(positions, dtype=np.float32).reshape(-1))
    if mesh.shape_keys is not None and len(mesh.shape_keys.key_blocks):
        mesh.shape_keys.key_blocks[0].data.foreach_set("co", np.asarray(positions, dtype=np.float32).reshape(-1))
    mesh.update()


def evaluated_positions(context: Any, obj: Any) -> Optional[np.ndarray]:
    """The object's vertices as Blender shows them (modifiers applied) in world space, when the modifiers keep the
    vertex count; otherwise ``None``."""
    depsgraph = context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    try:
        if len(mesh.vertices) != len(obj.data.vertices):
            return None
        m = np.array(evaluated.matrix_world, dtype=np.float64)
        return local_positions(mesh) @ m[:3, :3].T + m[:3, 3]
    finally:
        evaluated.to_mesh_clear()


def _identity(obj: Any) -> bool:
    return obj.parent is None and np.allclose(np.array(obj.matrix_world), np.eye(4), atol=1e-6)


def _old_rigs(obj: Any, ident: Optional[str]) -> List[Any]:
    rigs = []
    for modifier in obj.modifiers:
        if modifier.type == "ARMATURE" and modifier.object is not None and modifier.object.get(ARMATURE) != ident:
            rigs.append(modifier.object)
    parent = obj.parent
    if parent is not None and parent.type == "ARMATURE" and parent.get(ARMATURE) != ident and parent not in rigs:
        rigs.append(parent)
    return rigs


def facts(context: Any, collection: Optional[Any]) -> ped.Facts:
    """What the character checks read (counts, bounds, transforms, modifiers, shape keys, old rigs, facing)."""
    objs = parts(collection)
    if not objs:
        return ped.Facts()
    ident = collection.get(CHARACTER)
    rig = armature(collection)
    rigged = rig is not None
    vertices = triangles = 0
    materials = set()
    transformed, modified, keys, rigs = [], [], [], []
    points, tris, offset = [], [], 0
    for obj in objs:
        mesh = obj.data
        vertices += len(mesh.vertices)
        totals = np.empty(len(mesh.polygons), dtype=np.int64)
        mesh.polygons.foreach_get("loop_total", totals)
        triangles += int(np.maximum(totals - 2, 0).sum())
        materials |= {slot.material.name for slot in obj.material_slots if slot.material is not None}
        if not _identity(obj) and not (rigged and obj.parent == rig):
            transformed.append(obj.name)
        if any(m.type != "ARMATURE" and m.show_viewport for m in obj.modifiers):
            modified.append(obj.name)
        if mesh.shape_keys is not None and len(mesh.shape_keys.key_blocks) > 0:
            keys.append(obj.name)
        rigs += [r.name for r in _old_rigs(obj, ident) if r.name not in rigs]
        if not rigged:
            world = world_positions(obj)
            points.append(world)
            if len(world):
                tris.append(mesh_triangles(mesh) + offset)
            offset += len(world)
    if rigged:
        positions = np.concatenate([world_positions(obj) for obj in objs])
    else:
        positions = np.concatenate(points) if points else np.zeros((0, 3))
    lower = positions.min(axis=0) if len(positions) else np.zeros(3)
    upper = positions.max(axis=0) if len(positions) else np.zeros(3)
    facing = upside_down = None
    if not rigged and len(positions):
        all_tris = np.concatenate(tris) if tris else np.zeros((0, 3), dtype=np.int64)
        facing = ped.facing_guess(positions)
        upside_down = ped.stands_on_head(positions, all_tris)
    return ped.Facts(len(objs), vertices, triangles, len(materials), tuple(float(v) for v in lower),
                     tuple(float(v) for v in upper), tuple(transformed), tuple(modified), tuple(keys), tuple(rigs),
                     rigged, facing, bool(upside_down))


def facts_key(collection: Optional[Any]) -> tuple:
    """A cheap fingerprint of what the facts read, so the panel recomputes them only when it changed."""
    key: List[Any] = [collection.name if collection is not None and _alive(collection) else None]
    rig = armature(collection)
    key.append(rig.name if rig is not None else None)
    for obj in parts(collection):
        mesh = obj.data
        key.append((obj.name, len(mesh.vertices), len(mesh.polygons), tuple(round(v, 5) for row in obj.matrix_world
                                                                              for v in row),
                    tuple(round(c, 4) for corner in obj.bound_box for c in corner),
                    tuple((m.type, m.show_viewport, getattr(m, "object", None) and m.object.name) for m in obj.modifiers),
                    obj.parent.name if obj.parent is not None else None,
                    len(mesh.shape_keys.key_blocks) if mesh.shape_keys is not None else 0))
    return tuple(key)


# --------------------------------------------------------------------------------------------------
# Fixes
# --------------------------------------------------------------------------------------------------


def _single_user(obj: Any) -> None:
    if obj.data.users > 1:
        obj.data = obj.data.copy()


def apply_transforms(objs: Iterable[Any]) -> int:
    """Bakes each part's transform (and its parent's) into its mesh, so the part sits at the origin unmoved. A mirrored
    part keeps its faces pointing outwards."""
    count = 0
    for obj in objs:
        if _identity(obj):
            continue
        world = obj.matrix_world.copy()
        _single_user(obj)
        obj.parent = None
        obj.data.transform(world, shape_keys=True)
        if world.determinant() < 0:
            obj.data.flip_normals()
        obj.matrix_world = Matrix.Identity(4)
        obj.data.update()
        count += 1
    return count


def apply_modifiers(context: Any, objs: Iterable[Any]) -> int:
    """Applies every modifier but an Armature, so the rig sees the mesh as Blender shows it."""
    count = 0
    for obj in objs:
        for modifier in list(obj.modifiers):
            if modifier.type == "ARMATURE":
                continue
            if not modifier.show_viewport:
                obj.modifiers.remove(modifier)  # hidden: it does not show, so it goes
                continue
            if obj.data.shape_keys is not None:
                raise fail("ped.why.modifiers-shape-keys", name=obj.name)
            _single_user(obj)
            with context.temp_override(object=obj, active_object=obj, selected_objects=[obj],
                                       selected_editable_objects=[obj]):
                bpy.ops.object.modifier_apply(modifier=modifier.name)
            count += 1
    return count


def _move(objs: Sequence[Any], matrix: Matrix, markers: Iterable[Any] = (), collection: Optional[Any] = None) -> None:
    """Moves the character's meshes (into their data when they sit unmoved at the origin), its markers and the joints
    kept from its old rig by ``matrix``."""
    if collection is not None and collection.get(OLD_JOINTS):
        try:
            joints = json.loads(collection[OLD_JOINTS])
        except ValueError:
            joints = {}
        m = np.array(matrix, dtype=np.float64)
        collection[OLD_JOINTS] = json.dumps({name: list(m[:3, :3] @ np.asarray(point, dtype=np.float64) + m[:3, 3])
                                             for name, point in joints.items()})
    for obj in objs:
        if _identity(obj):
            _single_user(obj)
            obj.data.transform(matrix, shape_keys=True)
            if matrix.determinant() < 0:
                obj.data.flip_normals()
            obj.data.update()
        else:
            obj.matrix_world = matrix @ obj.matrix_world
    for marker in markers:
        marker.matrix_world = matrix @ marker.matrix_world


def _bounds(objs: Sequence[Any]) -> Tuple[np.ndarray, np.ndarray]:
    points = np.concatenate([world_positions(obj) for obj in objs]) if objs else np.zeros((1, 3))
    return points.min(axis=0), points.max(axis=0)


def scale(collection: Any, factor: float) -> None:
    """Scales the character about the origin, as a change of units does: its size and its place change together."""
    _move(parts(collection), Matrix.Scale(factor, 4), marker_objects(collection).values(), collection)


def turn(collection: Any, axis: str, degrees: float) -> None:
    """Turns the character about its middle; after a turn about X or Y it stands on the ground again."""
    objs = parts(collection)
    lower, upper = _bounds(objs)
    centre = Vector(((lower + upper) / 2).tolist())
    matrix = Matrix.Translation(centre) @ Matrix.Rotation(np.radians(degrees), 4, axis) @ Matrix.Translation(-centre)
    markers = marker_objects(collection).values()
    _move(objs, matrix, markers, collection)
    if axis in ("X", "Y"):
        new_lower, _ = _bounds(objs)
        _move(objs, Matrix.Translation((0.0, 0.0, -float(new_lower[2]))), markers, collection)
    collection[FACING] = 0


def to_origin(collection: Any) -> None:
    """Moves the character so it stands on the ground at the origin."""
    objs = parts(collection)
    lower, upper = _bounds(objs)
    shift = Vector((-(lower[0] + upper[0]) / 2, -(lower[1] + upper[1]) / 2, -lower[2]))
    _move(objs, Matrix.Translation(shift), marker_objects(collection).values(), collection)


def remove_old_rig(context: Any, collection: Any) -> List[str]:
    """Takes the character off the rig it came with: it keeps its current pose (baked into its meshes), loses the
    Armature modifiers, the parent and the rig's vertex groups, and the rig's joints are kept for From Old Rig. The old
    armature stays in the file, hidden. Returns the armatures' names."""
    objs = parts(collection)
    ident = collection.get(CHARACTER)
    rigs: List[Any] = []
    for obj in objs:
        rigs += [r for r in _old_rigs(obj, ident) if r not in rigs]
    if not rigs:
        return []
    joints: Dict[str, List[float]] = {}
    for rig in rigs:
        for bone in rig.pose.bones:
            joints[bone.name] = list(rig.matrix_world @ bone.head)
    collection[OLD_JOINTS] = json.dumps(joints)
    for obj in objs:
        others = [m for m in obj.modifiers if m.type != "ARMATURE"]
        shown = [m.show_viewport for m in others]
        for m in others:
            m.show_viewport = False
        try:
            context.view_layer.update()
            posed = evaluated_positions(context, obj)
        finally:
            for m, value in zip(others, shown):
                m.show_viewport = value
        bones = {b.name for rig in rigs for b in rig.data.bones}
        for modifier in list(obj.modifiers):
            if modifier.type == "ARMATURE" and modifier.object in rigs:
                obj.modifiers.remove(modifier)
        world = obj.matrix_world.copy()
        if obj.parent in rigs:
            obj.parent = None
            obj.matrix_world = world
        if posed is not None:
            _single_user(obj)
            inverse = np.array(obj.matrix_world.inverted(), dtype=np.float64)
            set_local_positions(obj.data, posed @ inverse[:3, :3].T + inverse[:3, 3])
        for group in list(obj.vertex_groups):
            if group.name in bones:
                obj.vertex_groups.remove(group)
    for rig in rigs:
        try:
            rig.hide_set(True)
        except RuntimeError:
            rig.hide_viewport = True
    return [rig.name for rig in rigs]


def remove_shape_keys(objs: Iterable[Any]) -> int:
    """Removes the shape keys, keeping the shape they show now."""
    count = 0
    for obj in objs:
        keys = obj.data.shape_keys
        if keys is None:
            continue
        mix = obj.shape_key_add(name="DCT mix", from_mix=True)
        values = np.empty(len(obj.data.vertices) * 3, dtype=np.float32)
        mix.data.foreach_get("co", values)
        obj.shape_key_clear()
        obj.data.vertices.foreach_set("co", values)
        obj.data.update()
        count += 1
    return count


def old_joints(collection: Optional[Any]) -> Dict[str, Tuple[float, float, float]]:
    """The joints of the character's old rig: of the armature that still moves it, or those kept when it was
    removed."""
    if collection is None:
        return {}
    ident = collection.get(CHARACTER)
    joints: Dict[str, Tuple[float, float, float]] = {}
    for obj in parts(collection):
        for rig in _old_rigs(obj, ident):
            for bone in rig.pose.bones:
                joints[bone.name] = tuple(rig.matrix_world @ bone.head)
    if joints:
        return joints
    try:
        stored = json.loads(collection.get(OLD_JOINTS, "") or "{}")
    except ValueError:
        return {}
    return {name: tuple(point) for name, point in stored.items() if isinstance(point, list) and len(point) == 3}


# --------------------------------------------------------------------------------------------------
# Markers
# --------------------------------------------------------------------------------------------------


def _marker_collection(collection: Any) -> Any:
    name = f"{collection.name} Markers"
    for child in collection.children:
        if child.get(MARKER_OF) == collection.get(CHARACTER):
            return child
    child = bpy.data.collections.new(name)
    child[MARKER_OF] = collection.get(CHARACTER)
    collection.children.link(child)
    return child


def marker_objects(collection: Optional[Any]) -> Dict[str, Any]:
    if collection is None or not _alive(collection):
        return {}
    ident = collection.get(CHARACTER)
    found = {}
    for obj in collection.all_objects:
        name = obj.get(MARKER)
        if name in ped.BODY_MARKERS and obj.get(MARKER_OF) == ident:
            found[name] = obj
    return found


def read_markers(collection: Optional[Any]) -> Dict[str, Tuple[float, float, float]]:
    return {name: tuple(obj.matrix_world.translation) for name, obj in marker_objects(collection).items()}


def write_markers(collection: Any, markers: Dict[str, Any], size: float) -> List[Any]:
    """Creates or moves the character's marker empties (spheres drawn in front of the mesh)."""
    ident = character_id(collection)
    existing = marker_objects(collection)
    target = None
    written = []
    for name in ped.BODY_MARKERS:
        if name not in markers:
            continue
        marker = existing.get(name)
        if marker is None:
            target = target or _marker_collection(collection)
            marker = bpy.data.objects.new(f"{MARKER_PREFIX}{name}", None)
            marker.empty_display_type = "SPHERE"
            marker[MARKER] = name
            marker[MARKER_OF] = ident
            marker.show_in_front = True
            target.objects.link(marker)
        marker.empty_display_size = size
        marker.matrix_world = Matrix.Translation(Vector(markers[name]))
        written.append(marker)
    return written


def resize_markers(collection: Optional[Any], size: float) -> None:
    for marker in marker_objects(collection).values():
        marker.empty_display_size = size


def select_objects(context: Any, objs: Sequence[Any]) -> None:
    if context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    for obj in context.view_layer.objects:
        obj.select_set(False)
    for obj in objs:
        if context.view_layer.objects.get(obj.name) is not None:
            obj.hide_set(False)
            obj.select_set(True)
    if objs:
        context.view_layer.objects.active = objs[0]


def select_vertices(context: Any, vertices: Dict[str, np.ndarray]) -> Optional[Any]:
    """Selects the given vertices of each part and opens Edit Mode on the part with the most, so they show."""
    objs = {obj.name: obj for obj in bpy.data.objects if obj.type == "MESH"}
    chosen = [objs[name] for name in vertices if name in objs]
    if not chosen:
        return None
    select_objects(context, [])
    for obj in chosen:
        mesh = obj.data
        flags = np.zeros(len(mesh.vertices), dtype=bool)
        wanted = np.asarray(vertices[obj.name], dtype=np.int64)
        flags[wanted[(wanted >= 0) & (wanted < len(flags))]] = True
        mesh.vertices.foreach_set("select", flags)
        for collection_name in ("edges", "polygons"):
            items = getattr(mesh, collection_name)
            items.foreach_set("select", np.zeros(len(items), dtype=bool))
        obj.select_set(True)
    main = max(chosen, key=lambda o: len(vertices[o.name]))
    context.view_layer.objects.active = main
    try:
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_mode(type="VERT")
    except RuntimeError:
        pass  # no view to edit in (background)
    return main


# --------------------------------------------------------------------------------------------------
# The click guide's rays
# --------------------------------------------------------------------------------------------------


def character_tree(context: Any, collection: Any) -> Optional[BVHTree]:
    """A search tree of the character's surface as Blender shows it, in world space."""
    points, polygons, offset = [], [], 0
    depsgraph = context.evaluated_depsgraph_get()
    for obj in parts(collection):
        evaluated = obj.evaluated_get(depsgraph)
        mesh = evaluated.to_mesh()
        try:
            m = np.array(evaluated.matrix_world, dtype=np.float64)
            world = local_positions(mesh) @ m[:3, :3].T + m[:3, 3]
            tris = mesh_triangles(mesh)
        finally:
            evaluated.to_mesh_clear()
        points.append(world)
        polygons.append(tris + offset)
        offset += len(world)
    if not points or offset == 0:
        return None
    return BVHTree.FromPolygons(np.concatenate(points).tolist(), np.concatenate(polygons).tolist())


def ray_hits(tree: BVHTree, origin: Any, direction: Any, limit: int = 12) -> List[float]:
    """The distances along a ray at which it crosses the character's surface, nearest first."""
    start = Vector(origin)
    way = Vector(direction).normalized()
    hits: List[float] = []
    travelled = 0.0
    for _ in range(limit):
        location, _normal, _index, distance = tree.ray_cast(start + way * travelled, way)
        if location is None:
            break
        travelled += distance
        hits.append(travelled)
        travelled += 1e-4
    return hits


# --------------------------------------------------------------------------------------------------
# The rig request
# --------------------------------------------------------------------------------------------------


def rig_parts(context: Any, collection: Any) -> List[ped.Part]:
    """The character's meshes as a rig request carries them: as the character stands (a rigged character in its own
    pose, never in the rest pose)."""
    rig = armature(collection)
    restore = None
    if rig is not None and rig.data.pose_position != "POSE":
        restore = rig.data.pose_position
        rig.data.pose_position = "POSE"
        context.view_layer.update()
    try:
        result = []
        for obj in parts(collection):
            positions = evaluated_positions(context, obj) if rig is not None else world_positions(obj)
            if positions is None:
                raise fail("ped.why.vertex-count", name=obj.name)
            result.append(ped.Part(obj.name, role_of(obj), positions, mesh_triangles(obj.data)))
        return result
    finally:
        if restore is not None:
            rig.data.pose_position = restore
            context.view_layer.update()


def current_topology(collection: Any) -> str:
    return ped.topology_hash([(obj.name, len(obj.data.vertices), mesh_triangles(obj.data)) for obj in parts(collection)])


# --------------------------------------------------------------------------------------------------
# Applying a rig
# --------------------------------------------------------------------------------------------------


def _flat(matrix: Any) -> List[float]:
    return [float(v) for v in np.asarray(matrix, dtype=np.float64).reshape(-1)]


def _matrix(values: Any) -> np.ndarray:
    return np.asarray(list(values), dtype=np.float64).reshape(4, 4)


def _object_mode(context: Any) -> None:
    if context.mode != "OBJECT" and context.view_layer.objects.active is not None:
        bpy.ops.object.mode_set(mode="OBJECT")


def build_armature(context: Any, collection: Any, plan: Sequence[ped.BonePlan], name: str) -> Any:
    """An armature with the plan's bones: each bone's rest matrix is exactly the rig's (its joint moved, never turned),
    drawn along its own Y axis towards its child."""
    data = bpy.data.armatures.new(name)
    data.display_type = "OCTAHEDRAL"
    rig = bpy.data.objects.new(name, data)
    rig.show_in_front = True
    collection.objects.link(rig)
    rig[ARMATURE] = character_id(collection)
    layer = context.view_layer
    if layer.objects.get(rig.name) is None:
        context.scene.collection.objects.link(rig)
    selected = [obj for obj in layer.objects if obj.select_get()]
    active = layer.objects.active
    for obj in selected:
        obj.select_set(False)
    rig.select_set(True)
    layer.objects.active = rig
    bpy.ops.object.mode_set(mode="EDIT")
    try:
        if rig.mode != "EDIT":
            raise fail("ped.why.object-mode")
        bones = []
        for bone in plan:
            edit = data.edit_bones.new(bone.name)
            edit.head = (0.0, 0.0, 0.0)
            edit.tail = (0.0, bone.length, 0.0)
            edit.matrix = Matrix(bone.rest.tolist())
            edit.use_connect = False
            edit.use_deform = not ped.non_deforming(bone.name)
            bones.append(edit)
        for edit, bone in zip(bones, plan):
            if bone.parent >= 0:
                edit.parent = bones[bone.parent]
    finally:
        bpy.ops.object.mode_set(mode="OBJECT")
        rig.select_set(False)
        for obj in selected:
            obj.select_set(True)
        layer.objects.active = active if active is not None else rig
    for bone in plan:
        target = data.bones[bone.name]
        target[BONE_REST] = _flat(bone.rest)
        target[BONE_TAG] = int(bone.tag)
        if bone.pose is not None:
            target[BONE_POSE] = _flat(bone.pose)
    return rig


def rest_matrices(rig: Any) -> Tuple[List[str], List[np.ndarray], List[int]]:
    """The rig's bones (names in order), their rest matrices as the rig gave them, and their parents."""
    names = [bone.name for bone in rig.data.bones]
    index = {name: i for i, name in enumerate(names)}
    rests = []
    for bone in rig.data.bones:
        stored = bone.get(BONE_REST)
        rests.append(_matrix(stored) if stored is not None and len(stored) == 16 else np.array(bone.matrix_local))
    parents = [index[bone.parent.name] if bone.parent is not None else -1 for bone in rig.data.bones]
    return names, rests, parents


def set_bases(rig: Any, names: Sequence[str], bases: Sequence[np.ndarray]) -> None:
    for name, basis in zip(names, bases):
        rig.pose.bones[name].matrix_basis = Matrix(np.asarray(basis).tolist())


def set_pose(context: Any, rig: Any, pose: str) -> None:
    """Shows the character in its own pose (``yours``), the game's rest pose (``rest``) or a test pose."""
    if pose == "rest":
        rig.data.pose_position = "REST"
    else:
        rig.data.pose_position = "POSE"
        names, rests, parents = rest_matrices(rig)
        if pose == "yours":
            posed = []
            for name, rest in zip(names, rests):
                stored = rig.data.bones[name].get(BONE_POSE)
                posed.append(_matrix(stored) if stored is not None and len(stored) == 16 else rest)
        else:
            posed = ped.test_pose(pose, names, rests, parents)
        set_bases(rig, names, ped.pose_bases(rests, posed, parents))
    context.view_layer.update()


def _clear_groups(obj: Any, names: Iterable[str]) -> None:
    wanted = set(names)
    for group in list(obj.vertex_groups):
        if group.name in wanted:
            obj.vertex_groups.remove(group)


def _keep_previous(context: Any, collection: Any, current: Any) -> None:
    """Keeps the applied rig as the previous one (its armature, hidden, and each part's mesh with its groups)."""
    old = previous_armature(collection)
    if old is not None:
        data = old.data
        bpy.data.objects.remove(old)
        if data.users == 0:
            bpy.data.armatures.remove(data)
    for obj in parts(collection):
        stale = obj.get(PREVIOUS_MESH)
        copy = obj.data.copy()
        copy.name = f"DCT Previous {obj.name}"
        obj[PREVIOUS_MESH] = copy
        obj[PREVIOUS_GROUPS] = json.dumps([group.name for group in obj.vertex_groups])
        if isinstance(stale, bpy.types.Mesh) and stale.users == 0:
            bpy.data.meshes.remove(stale)
    del current[ARMATURE]
    current[PREVIOUS_OF] = character_id(collection)
    current.name = f"{collection.name} Rig (Previous)"
    for obj in parts(collection):
        if obj.parent == current:
            obj.parent = None
        for modifier in list(obj.modifiers):
            if modifier.type == "ARMATURE" and modifier.object == current:
                obj.modifiers.remove(modifier)
    collection[PREVIOUS_RIG] = collection.get(RIG_INFO, "")
    try:
        current.hide_set(True)
    except RuntimeError:
        current.hide_viewport = True


def _attach(obj: Any, rig: Any, preserve_volume: bool) -> None:
    modifier = obj.modifiers.new(MODIFIER, "ARMATURE")
    modifier.object = rig
    modifier.use_deform_preserve_volume = preserve_volume
    obj.parent = rig
    obj.matrix_parent_inverse = rig.matrix_world.inverted()


def apply_rig(context: Any, collection: Any, rig_result: Any, sent: Dict[str, Any]) -> Any:
    """Applies a rig Durty Cloth Tool computed: the character's meshes take the game's rest pose and the weights as
    vertex groups by bone name, an armature with the rig's bones moves them, and its pose is the character's own, so
    the character looks as before. The rig is refused when the meshes changed since it was asked for. The applied rig
    before it is kept as the previous one, and each part's mesh from before the first rig as its original."""
    _object_mode(context)
    objs = {obj.name: obj for obj in parts(collection)}
    ranges = sent["ranges"]
    if set(objs) != {name for name, _, _ in ranges} or current_topology(collection) != sent["topology"]:
        raise fail("ped.why.mesh-changed")
    current = armature(collection)
    for obj in objs.values():
        if not isinstance(obj.get(ORIGINAL), bpy.types.Mesh):
            original = obj.data.copy()
            original.name = f"DCT Original {obj.name}"
            obj[ORIGINAL] = original
    if current is not None:
        _keep_previous(context, collection, current)
    names = [bone.name for bone in rig_result.bones]
    plan = ped.armature_plan(rig_result.bones, rig_result.poses)
    rig = build_armature(context, collection, plan, f"{collection.name} Rig")
    rest = ped.rest_parts(rig_result.rest_positions, ranges)
    preserve = sent.get("options", {}).get("restModel", "volume") == "volume"
    for name, start, count in ranges:
        obj = objs[name]
        _single_user(obj)
        for modifier in list(obj.modifiers):
            if modifier.type == "ARMATURE":
                obj.modifiers.remove(modifier)
        obj.parent = None
        inverse = np.array(obj.matrix_world.inverted(), dtype=np.float64)
        set_local_positions(obj.data, rest[name] @ inverse[:3, :3].T + inverse[:3, 3])
        _clear_groups(obj, names)
        for bone, entries in ped.vertex_groups(rig_result.bone_indices, rig_result.weights, names, start, count).items():
            group = obj.vertex_groups.get(bone) or obj.vertex_groups.new(name=bone)
            for weight, vertices in entries:
                group.add(vertices.tolist(), weight, "REPLACE")
        _attach(obj, rig, preserve)
    set_pose(context, rig, "yours")
    info = {"template": rig_result.template, "job": rig_result.job, "ragdoll": rig_result.ragdoll,
            "time": time.time(), "topology": sent["topology"], "options": sent.get("options", {}),
            "markers": {k: list(v) for k, v in sent.get("markers", {}).items()}, "report": rig_result.report,
            "bones": len(names)}
    collection[RIG_INFO] = json.dumps(info)
    for key in (CHECKED, SENT):
        if key in collection:
            del collection[key]
    return rig


def rig_info(collection: Optional[Any]) -> Dict[str, Any]:
    if collection is None or not _alive(collection):
        return {}
    try:
        info = json.loads(collection.get(RIG_INFO, "") or "{}")
    except ValueError:
        return {}
    return info if isinstance(info, dict) else {}


def restore_previous(context: Any, collection: Any) -> None:
    """Swaps the applied rig and the previous one."""
    _object_mode(context)
    old = previous_armature(collection)
    if old is None:
        raise fail("ped.why.no-previous")
    current = armature(collection)
    info, previous_info = collection.get(RIG_INFO, ""), collection.get(PREVIOUS_RIG, "")
    swaps = []
    for obj in parts(collection):
        mesh = obj.get(PREVIOUS_MESH)
        if not isinstance(mesh, bpy.types.Mesh):
            raise fail("ped.why.no-previous")
        swaps.append((obj, mesh, json.loads(obj.get(PREVIOUS_GROUPS, "[]") or "[]")))
    for obj, mesh, groups in swaps:
        keep = obj.data
        keep_groups = [group.name for group in obj.vertex_groups]
        for modifier in list(obj.modifiers):
            if modifier.type == "ARMATURE":
                obj.modifiers.remove(modifier)
        obj.parent = None
        obj.vertex_groups.clear()
        for name in groups:
            obj.vertex_groups.new(name=name)
        restored = mesh.copy()
        restored.name = keep.name
        obj.data = restored
        stale = obj.get(PREVIOUS_MESH)
        obj[PREVIOUS_MESH] = keep
        obj[PREVIOUS_GROUPS] = json.dumps(keep_groups)
        if isinstance(stale, bpy.types.Mesh) and stale.users == 0:
            bpy.data.meshes.remove(stale)
    ident = character_id(collection)
    if current is not None:
        del current[ARMATURE]
        current[PREVIOUS_OF] = ident
        current.name = f"{collection.name} Rig (Previous)"
        try:
            current.hide_set(True)
        except RuntimeError:
            current.hide_viewport = True
    del old[PREVIOUS_OF]
    old[ARMATURE] = ident
    old.name = f"{collection.name} Rig"
    try:
        old.hide_set(False)
    except RuntimeError:
        old.hide_viewport = False
    info_now = json.loads(previous_info or "{}") if previous_info else {}
    preserve = info_now.get("options", {}).get("restModel", "volume") == "volume"
    for obj in parts(collection):
        _attach(obj, old, preserve)
    collection[RIG_INFO], collection[PREVIOUS_RIG] = previous_info, info
    for key in (CHECKED, SENT):
        if key in collection:
            del collection[key]
    set_pose(context, old, "yours")


def remove_rig(context: Any, collection: Any) -> None:
    """Takes the rig off: each part gets its mesh from before the first rig back, the armatures go."""
    _object_mode(context)
    for obj in parts(collection):
        original = obj.get(ORIGINAL)
        for modifier in list(obj.modifiers):
            if modifier.type == "ARMATURE" and modifier.object is not None and (
                    modifier.object.get(ARMATURE) or modifier.object.get(PREVIOUS_OF)):
                obj.modifiers.remove(modifier)
        world = obj.matrix_world.copy()
        obj.parent = None
        obj.matrix_world = world
        if isinstance(original, bpy.types.Mesh):
            keep = obj.data
            restored = original.copy()
            restored.name = keep.name
            obj.data = restored
            if keep.users == 0:
                bpy.data.meshes.remove(keep)
        for key in (ORIGINAL, PREVIOUS_MESH, PREVIOUS_GROUPS):
            stored = obj.get(key)
            if key in obj:
                del obj[key]
            if isinstance(stored, bpy.types.Mesh) and stored.users == 0:
                bpy.data.meshes.remove(stored)
        obj.vertex_groups.clear()
    for rig in (armature(collection), previous_armature(collection)):
        if rig is not None:
            data = rig.data
            bpy.data.objects.remove(rig)
            if data.users == 0:
                bpy.data.armatures.remove(data)
    for key in (RIG_INFO, PREVIOUS_RIG, CHECKED, SENT):
        if key in collection:
            del collection[key]


# --------------------------------------------------------------------------------------------------
# Local checks
# --------------------------------------------------------------------------------------------------


def weight_data(obj: Any, bones: Sequence[str]) -> Dict[str, Any]:
    """Per vertex: how many bones weight it, its total weight, and whether a bone that never deforms carries weight."""
    names = [group.name for group in obj.vertex_groups]
    known = set(bones)
    count = len(obj.data.vertices)
    counts = np.zeros(count, dtype=np.int64)
    totals = np.zeros(count, dtype=np.float64)
    bad = np.zeros(count, dtype=bool)
    deforming = [name in known and not ped.non_deforming(name) for name in names]
    never = [ped.non_deforming(name) for name in names]
    for vertex in obj.data.vertices:
        for element in vertex.groups:
            if element.weight <= 0.0 or element.group >= len(names):
                continue
            if deforming[element.group]:
                counts[vertex.index] += 1
                totals[vertex.index] += element.weight
            elif never[element.group]:
                bad[vertex.index] = True
    return {"counts": counts, "totals": totals, "bad": bad, "groups": names}


def run_checks(context: Any, collection: Any) -> List[ped.Finding]:
    """The local checks of the rigged character: weights (every vertex weighted, at most four bones, nothing on bones
    that never move the mesh, no stray groups), the armature against the rig, the meshes against the rig, and how
    the test poses stretch it."""
    rig = armature(collection)
    if rig is None:
        raise fail("ped.why.not-rigged")
    info = rig_info(collection)
    names, rests, parents = rest_matrices(rig)
    findings = ped.weight_findings({obj.name: weight_data(obj, names) for obj in parts(collection)}, names)
    actual = {bone.name: np.array(bone.matrix_local) for bone in rig.data.bones}
    changed = ped.armature_changes(dict(zip(names, rests)), actual)
    if changed:
        findings.append(ped.Finding("armature-changed", len(changed), changed))
    if info.get("topology") and current_topology(collection) != info["topology"]:
        findings.append(ped.Finding("mesh-changed", 1))
    objs = parts(collection)
    rest_positions = {obj.name: world_positions(obj) for obj in objs}
    edges = {obj.name: mesh_edges(obj.data) for obj in objs}
    current = rig.data.pose_position
    try:
        for pose in ped.TEST_POSES:
            set_pose(context, rig, pose)
            stretched = {}
            for obj in objs:
                posed = evaluated_positions(context, obj)
                if posed is None:
                    continue
                bad = ped.strain(rest_positions[obj.name], posed, edges[obj.name])
                if len(bad):
                    stretched[obj.name] = bad
            if stretched:
                findings.append(ped.Finding("strain", int(sum(len(v) for v in stretched.values())), (), stretched,
                                            pose))
    finally:
        set_pose(context, rig, "rest" if current == "REST" else "yours")
    return findings


def texture_problems(objs: Iterable[Any]) -> List[Tuple[str, str]]:
    """The images of the character's materials Durty Cloth Tool would refuse or warn about: ``(name, code)``."""
    seen, problems = set(), []
    for obj in objs:
        for slot in obj.material_slots:
            material = slot.material
            if material is None or not material.use_nodes or material.node_tree is None:
                continue
            for node in material.node_tree.nodes:
                image = getattr(node, "image", None) if node.type == "TEX_IMAGE" else None
                if image is None or image.name in seen:
                    continue
                seen.add(image.name)
                width, height = image.size
                code = ped.texture_problem(int(width), int(height))
                if code is not None:
                    problems.append((image.name, code))
    return problems


# --------------------------------------------------------------------------------------------------
# The GLB
# --------------------------------------------------------------------------------------------------


def gltf_options(path: pathlib.Path) -> Dict[str, Any]:
    """The pinned exporter settings this Blender's glTF exporter knows."""
    try:
        known = {p.identifier for p in bpy.ops.export_scene.gltf.get_rna_type().properties}
    except (AttributeError, KeyError):
        known = set(GLB_OPTIONS)
    options = {key: value for key, value in GLB_OPTIONS.items() if key in known}
    options["filepath"] = str(path)
    return options


def export_glb(context: Any, collection: Any, folder: pathlib.Path) -> bytes:
    """The rigged character as a GLB in the game's rest pose: the armature with every bone (named as the template's)
    and the parts skinned to it, images embedded. Selection, the active object and the pose shown are put back."""
    rig = armature(collection)
    if rig is None:
        raise fail("ped.why.not-rigged")
    objs = parts(collection)
    layer = context.view_layer
    selected = [obj for obj in layer.objects if obj.select_get()]
    active = layer.objects.active
    position = rig.data.pose_position
    _object_mode(context)
    hidden = [obj for obj in [rig, *objs] if obj.hide_get()]
    try:
        for obj in hidden:
            obj.hide_set(False)
        for obj in layer.objects:
            obj.select_set(False)
        for obj in [rig, *objs]:
            obj.select_set(True)
        layer.objects.active = rig
        rig.data.pose_position = "REST"
        layer.update()
        path = folder / "character.glb"
        with context.temp_override(active_object=rig, object=rig, selected_objects=[rig, *objs]):
            result = bpy.ops.export_scene.gltf(**gltf_options(path))
        if "FINISHED" not in result or not path.is_file():
            raise fail("ped.why.export-failed")
        return path.read_bytes()
    finally:
        rig.data.pose_position = position
        for obj in layer.objects:
            obj.select_set(obj in selected)
        for obj in hidden:
            obj.hide_set(True)
        layer.objects.active = active
        layer.update()


def work_folder(data_dir: pathlib.Path) -> pathlib.Path:
    base = data_dir / WORK_FOLDER
    base.mkdir(parents=True, exist_ok=True)
    folder = base / f"send-{secrets.token_hex(6)}"
    folder.mkdir()
    return folder
