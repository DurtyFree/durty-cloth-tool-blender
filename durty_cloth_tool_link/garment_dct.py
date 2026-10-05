# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2026 Schmid Software Solutions (https://schmid-software.de)
"""Adding the garment to a Durty Cloth Tool project, the Blender side: the freemode skeleton Durty Cloth Tool sends,
imported with Sollumz and checked against the template; the garment set up as a Sollumz drawable model on it (the ped
shader with its images, its levels of detail, smooth shading); the export with Exclude Skeleton into a folder of the
add-on's own; and the colour variations as PNG pictures.

The rules and the checks of the export live in :mod:`garment_add`; this module only touches Blender.
"""

from __future__ import annotations

import pathlib
import re
import secrets
import shutil
import time
from typing import Any, Dict, List, NamedTuple, Optional, Sequence, Tuple

import bpy
import numpy as np
from mathutils import Matrix

from . import bundle, garment, garment_add, host, pixels
from . import garment_host as gh
from .link import _is_link
from .strings import Msg, UserError, msg

#: On the Drawable Dictionary and the Drawable the skeleton template became: the gender of that template.
SKELETON_TAG = "dct_skeleton"
#: On the garment once Durty Cloth Tool added it: the name it was added under.
ADDED = "dct_added"
#: The add-on's folder (inside its data folder) for the skeleton template and the export of an add, one folder per
#: use, removed right after.
WORK_FOLDER = "garment-add"
WORK_PREFIX = "add-"
STALE_SECONDS = 600.0
PED_SHADER = "ped.sps"
#: The Sollumz settings every add uses, whatever the user chose: the ped's own skeleton (Exclude Skeleton), one
#: vertex per face corner (UV seams stay seams), no parent transform baked in.
EXPORT_OVERRIDES: Dict[str, Any] = {"exclude_skeleton": True, "mesh_domain": "FACE_CORNER", "apply_transforms": False}
#: The skeleton template carries its own skeleton: never an external one from the user's import settings.
IMPORT_OVERRIDES: Dict[str, Any] = {"dwd_import_external_skeleton": "NO"}
DRAWABLE_MODEL = "sollumz_drawable_model"
SHADER_MATERIAL = "sollumz_material_shader"
#: The ped shader's samplers for the diffuse, normal and specular images.
SAMPLERS = {"diffuse": "DiffuseSampler", "normal": "BumpSampler", "specular": "SpecSampler"}


def fail(key: str, **fields: Any) -> UserError:
    return UserError(msg(key, **fields))


def _override(context: Any, obj: Any) -> Dict[str, Any]:
    window = getattr(context, "window", None) or host.first_window()
    values: Dict[str, Any] = {"active_object": obj, "object": obj, "selected_objects": [obj],
                              "selected_editable_objects": [obj]}
    if window is not None:
        values["window"] = window
    return values


# --------------------------------------------------------------------------------------------------
# Work folders
# --------------------------------------------------------------------------------------------------


def work_folder(data_dir: pathlib.Path) -> pathlib.Path:
    """A new, empty folder for one use inside the add-on's data folder (never through a link)."""
    base = data_dir / WORK_FOLDER
    if _is_link(base):
        raise fail("add.why.work-folder")
    base.mkdir(parents=True, exist_ok=True)
    folder = base / f"{WORK_PREFIX}{secrets.token_hex(6)}"
    folder.mkdir()
    return folder


def remove_stale_work(data_dir: Optional[pathlib.Path]) -> None:
    """Work folders a Blender that closed in the middle of an add left behind (only the add-on's own)."""
    base = data_dir / WORK_FOLDER if data_dir is not None else None
    if base is None or _is_link(base) or not base.is_dir():
        return
    cutoff = time.time() - STALE_SECONDS
    for entry in base.iterdir():
        try:
            if (entry.name.startswith(WORK_PREFIX) and not _is_link(entry) and entry.is_dir()
                    and entry.stat().st_mtime < cutoff):
                shutil.rmtree(entry, ignore_errors=True)
        except OSError:
            continue  # another Blender may be using it; it goes with the next start


# --------------------------------------------------------------------------------------------------
# The skeleton
# --------------------------------------------------------------------------------------------------


class Skeleton(NamedTuple):
    root: Any  # the Drawable Dictionary
    armature: Any  # its Drawable, an armature with the template's bones
    gender: str


def skeleton_of(obj: Optional[Any]) -> Optional[Skeleton]:
    """The Durty Cloth Tool skeleton the garment sits on, or ``None``."""
    try:
        parent = obj.parent if obj is not None else None
        if parent is None or parent.type != "ARMATURE":
            return None
        gender = parent.get(SKELETON_TAG)
        root = parent.parent
        if gender not in garment.GENDERS or root is None or root.get(SKELETON_TAG) != gender:
            return None
        return Skeleton(root, parent, gender)
    except ReferenceError:
        return None


def armature_bones(armature: Any) -> List[str]:
    """The armature's bones in its own order, which is the index each exported weight names."""
    return [bone.name for bone in armature.data.bones]


def skeleton_problem(obj: Optional[Any], gender: str, bones: Optional[Sequence[str]]) -> Optional[Msg]:
    """Why the garment's skeleton cannot carry it into the game as ``gender``, or ``None``. ``bones``: the template's
    bones (``None`` while the template has not arrived: then only the link to a skeleton is checked)."""
    skeleton = skeleton_of(obj)
    if skeleton is None:
        return msg("add.skeleton.missing")
    if skeleton.gender != gender:
        return msg("add.skeleton.other-gender", gender=msg(f"gender.{skeleton.gender}"))
    if not any(m.type == "ARMATURE" and m.object == skeleton.armature for m in obj.modifiers):
        return msg("add.skeleton.modifier")
    if bones is not None:
        return garment_add.armature_problem(armature_bones(skeleton.armature), bones)
    return None


def safe_name(name: str) -> str:
    """A name Sollumz can use for the exported file: letters, digits, ``_`` and ``-`` only."""
    text = re.sub(r"[^A-Za-z0-9_-]+", "_", name).strip("_") or "garment"
    return text[:48]


def _collection_of(obj: Any, context: Any) -> Any:
    collections = list(getattr(obj, "users_collection", ()) or ())
    return collections[0] if collections else context.scene.collection


def _move_to(objects: Sequence[Any], collection: Any) -> None:
    for obj in objects:
        if collection.objects.get(obj.name) is None:
            collection.objects.link(obj)
        for other in list(obj.users_collection):
            if other != collection:
                other.objects.unlink(obj)


def import_skeleton(context: Any, template: Any, data_dir: pathlib.Path, bones: Sequence[str], gender: str,
                    garment_obj: Any) -> Skeleton:
    """Imports the skeleton template with Sollumz (its own skeleton, never an external one), checks the armature against
    the template and moves it into the garment's collection. Raises :class:`UserError` when Sollumz did not import
    the template as one armature with the template's bones in order."""
    file = template.files[0]
    folder = work_folder(data_dir)
    try:
        (folder / file.name).write_bytes(file.data)
        root, _warnings = host.import_with_sollumz(folder, file.name, IMPORT_OVERRIDES)
    finally:
        shutil.rmtree(folder, ignore_errors=True)
    armatures = [child for child in root.children if child.type == "ARMATURE"]
    problem = None if len(armatures) == 1 else msg("add.skeleton.import")
    if problem is None:
        problem = garment_add.armature_problem(armature_bones(armatures[0]), bones)
    if problem is not None:
        gh._remove_objects([*root.children_recursive, root])
        raise UserError(problem)
    armature = armatures[0]
    base = safe_name(garment_obj.name)
    root.name = f"{base}_ydd"
    armature.name = f"{base}_skel"  # never the dictionary's name (Blender would rename one of them)
    root[SKELETON_TAG] = gender
    armature[SKELETON_TAG] = gender
    _move_to([root, armature], _collection_of(garment_obj, context))
    return Skeleton(root, armature, gender)


def _remove_skeleton_if_empty(skeleton: Skeleton) -> None:
    """A Durty Cloth Tool skeleton the garment left that holds nothing else goes."""
    try:
        others = [child for child in skeleton.armature.children]
        if others or len(skeleton.root.children) != 1:
            return
        gh._remove_objects([skeleton.armature, skeleton.root])
    except ReferenceError:
        return


def attach(context: Any, obj: Any, skeleton: Skeleton) -> Dict[str, Any]:
    """Parents the garment to the skeleton's armature (keeping where it is), points its Armature modifier at it (its
    vertex groups keep their bone names), leaves out the add-on's own vertex groups, and makes it a Sollumz drawable
    model. Returns what changed."""
    previous = skeleton_of(obj)
    world = obj.matrix_world.copy()
    obj.parent = skeleton.armature
    obj.parent_type = "OBJECT"
    obj.matrix_parent_inverse = Matrix.Identity(4)
    obj.matrix_world = world
    modifiers = [m for m in obj.modifiers if m.type == "ARMATURE"]
    if modifiers:
        modifier = modifiers[0]
    else:
        modifier = obj.modifiers.new("Armature", "ARMATURE")
        try:
            obj.modifiers.move(len(obj.modifiers) - 1, 0)  # the skin deforms first, as in game clothing
        except (AttributeError, RuntimeError, TypeError):
            pass  # an older Blender without moving modifiers: the order stays as it is
    modifier.object = skeleton.armature
    modifier.use_vertex_groups = True
    removed = []
    for group in list(obj.vertex_groups):
        if garment_add.is_tool_group(group.name):
            removed.append(group.name)
            obj.vertex_groups.remove(group)
    convert_to_model(context, obj)
    if previous is not None and previous.root != skeleton.root:
        _remove_skeleton_if_empty(previous)
    return {"removed": removed}


def convert_to_model(context: Any, obj: Any) -> None:
    """Makes the garment a Sollumz drawable model the way Sollumz converts an object (its High level of detail is the
    garment's mesh); setting the object type alone would leave the High level empty and the export empty."""
    lods = getattr(obj, "sz_lods", None)
    if lods is not None and lods.active_lod_level != "sollumz_high" and lods.get_lod("sollumz_high").mesh is not None:
        lods.active_lod_level = "sollumz_high"
    layer = context.view_layer
    selected = [o for o in layer.objects if o is not None and o.select_get()]
    active = layer.objects.active
    try:
        gh.deselect_all(layer)
        obj.select_set(True)
        layer.objects.active = obj
        with context.temp_override(**_override(context, obj)):
            result = bpy.ops.sollumz.converttodrawablemodel()
    except (AttributeError, RuntimeError, TypeError) as exc:
        raise fail("add.why.convert", detail=str(exc).strip()) from exc
    finally:
        gh.deselect_all(layer)
        for other in selected:
            try:
                other.select_set(True)
            except (ReferenceError, RuntimeError):
                pass  # removed meanwhile
        try:
            layer.objects.active = active
        except (ReferenceError, RuntimeError):
            pass
    lods = getattr(obj, "sz_lods", None)
    if ("FINISHED" not in result or getattr(obj, "sollum_type", None) != DRAWABLE_MODEL or lods is None
            or lods.get_lod("sollumz_high").mesh is None):
        raise fail("add.why.convert", detail=", ".join(sorted(result)))


# --------------------------------------------------------------------------------------------------
# Materials and levels of detail
# --------------------------------------------------------------------------------------------------


def _linked_image(socket: Any, depth: int = 0) -> Optional[Any]:
    """The image behind a node socket: an image texture linked to it, also through a Normal Map node or one other node
    in between."""
    if socket is None or not socket.is_linked or depth > 2:
        return None
    node = socket.links[0].from_node
    if node.type == "TEX_IMAGE":
        return node.image
    for name in ("Color", "Base Color", "Image"):
        found = _linked_image(node.inputs.get(name), depth + 1) if hasattr(node, "inputs") else None
        if found is not None:
            return found
    return None


def is_ped_material(material: Optional[Any]) -> bool:
    filename = getattr(getattr(material, "shader_properties", None), "filename", "") or ""
    return getattr(material, "sollum_type", None) == SHADER_MATERIAL and filename.startswith("ped")


def garment_images(obj: Any) -> Dict[str, Optional[Any]]:
    """The garment's diffuse, normal and specular images: a ped shader's samplers, or what feeds the Principled BSDF's
    Base Color, Normal and specular inputs (the material Combine Materials made has the diffuse)."""
    material = next((slot.material for slot in obj.material_slots if slot.material is not None), None)
    found: Dict[str, Optional[Any]] = {"diffuse": None, "normal": None, "specular": None}
    tree = getattr(material, "node_tree", None)
    if tree is None:
        return found
    if is_ped_material(material):
        for target, sampler in SAMPLERS.items():
            node = tree.nodes.get(sampler)
            found[target] = getattr(node, "image", None) if node is not None else None
        return found
    shader = next((n for n in tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
    if shader is not None:
        found["diffuse"] = _linked_image(shader.inputs.get("Base Color"))
        found["normal"] = _linked_image(shader.inputs.get("Normal"))
        for name in ("Specular IOR Level", "Specular"):
            found["specular"] = found["specular"] or _linked_image(shader.inputs.get(name))
    if found["diffuse"] is None:
        images = [n.image for n in tree.nodes if n.type == "TEX_IMAGE" and n.image is not None]
        if len(images) == 1:
            found["diffuse"] = images[0]
    return found


def is_dds(image: Optional[Any]) -> bool:
    """An image Sollumz can embed in the model: a DDS file, or packed DDS data."""
    if image is None:
        return False
    packed = getattr(image, "packed_file", None)
    if packed is not None:
        try:
            return bytes(packed.data[:4]) == b"DDS "
        except (AttributeError, TypeError, ValueError):
            return False
    return str(getattr(image, "filepath", "")).lower().endswith(".dds")


def ped_shader_index() -> int:
    module = host.sollumz_module("ydr.shader_materials")
    names = [getattr(s, "value", s) for s in getattr(module, "shadermats", ())] if module is not None else []
    return names.index(PED_SHADER) if PED_SHADER in names else 0


def _used_layer_names(mesh: Any) -> Tuple[List[str], List[str]]:
    uv = [layer.name for layer in mesh.uv_layers if re.fullmatch(r"UVMap \d+", layer.name)]
    colours = [c.name for c in mesh.color_attributes if re.fullmatch(r"Color \d+", c.name)]
    return uv, colours


def _add_layers(mesh: Any, uv_names: Sequence[str], colour_names: Sequence[str]) -> None:
    """Adds the Sollumz UV maps and colours another level of detail has (empty), so the export finds every one."""
    for name in uv_names:
        if mesh.uv_layers.get(name) is None and mesh.attributes.get(name) is None:
            mesh.attributes.new(name=name, type="FLOAT2", domain="CORNER")
    for name in colour_names:
        if mesh.color_attributes.get(name) is None:
            mesh.color_attributes.new(name, "BYTE_COLOR", "CORNER")


def lod_meshes(obj: Any) -> List[Any]:
    """The meshes of the garment's other levels of detail in Sollumz's slots (not the High one)."""
    lods = getattr(obj, "sz_lods", None)
    found = []
    if lods is None:
        return found
    for level in ("sollumz_veryhigh", "sollumz_medium", "sollumz_low", "sollumz_verylow"):
        try:
            mesh = lods.get_lod(level).mesh
        except (AttributeError, KeyError, TypeError):
            continue
        if mesh is not None and mesh != obj.data and mesh not in found:
            found.append(mesh)
    return found


def shade_smooth(mesh: Any) -> None:
    """Smooth shading: Sollumz exports one vertex per face corner, so flat faces would multiply the vertices."""
    try:
        mesh.shade_smooth()
    except AttributeError:  # an older Blender without Mesh.shade_smooth
        mesh.polygons.foreach_set("use_smooth", np.ones(len(mesh.polygons), dtype=bool))
        mesh.update()


def setup_material(context: Any, obj: Any, images: Dict[str, Optional[Any]]) -> Any:
    """Gives the garment the ped shader Sollumz uses for clothing, with the diffuse, normal and specular images (normal
    and specular are embedded in the model when they are DDS files). Every level of detail gets the same material."""
    mesh = obj.data
    material = obj.material_slots[0].material if obj.material_slots else None
    if not is_ped_material(material):
        # Sollumz names UV maps by order when it adds a shader: an unused layer such as DCT Source UV would become
        # UVMap 1. Adding the ped shader's second UV map first leaves the garment's own layers as they are.
        if mesh.uv_layers.get(gh.SOURCE_UV) is not None and mesh.uv_layers.get("UVMap 1") is None:
            mesh.attributes.new(name="UVMap 1", type="FLOAT2", domain="CORNER")
        images_before = set(bpy.data.images[:])
        count = len(mesh.materials)
        layer = context.view_layer
        try:
            gh.deselect_all(layer)
            obj.select_set(True)
            layer.objects.active = obj
            with context.temp_override(**_override(context, obj)):
                result = bpy.ops.sollumz.createshadermaterial(shader_index=ped_shader_index())
        except (AttributeError, RuntimeError, TypeError) as exc:
            raise fail("add.why.material", detail=str(exc).strip()) from exc
        if "FINISHED" not in result or len(mesh.materials) != count + 1:
            raise fail("add.why.material", detail=", ".join(sorted(result)))
        material = mesh.materials[count]
        if count:
            mesh.materials[0] = material
            mesh.materials.pop(index=count)
        placeholders = [image for image in bpy.data.images[:] if image not in images_before]
    else:
        placeholders = []
    tree = material.node_tree
    for target, sampler in SAMPLERS.items():
        node = tree.nodes.get(sampler)
        if node is None:
            continue
        image = images.get(target)
        node.image = image
        properties = getattr(node, "texture_properties", None)
        if properties is not None and hasattr(properties, "embedded") and target != "diffuse":
            properties.embedded = is_dds(image)
    for node in tree.nodes:
        if node.type == "TEX_IMAGE" and node.image in placeholders:
            node.image = None
    for image in placeholders:
        if image.users == 0:
            bpy.data.images.remove(image)
    uv_names, colour_names = _used_layer_names(mesh)
    for lod_mesh in lod_meshes(obj):
        if len(lod_mesh.materials):
            lod_mesh.materials[0] = material
            for index in range(len(lod_mesh.materials) - 1, 0, -1):
                lod_mesh.materials.pop(index=index)
        else:
            lod_mesh.materials.append(material)
        _add_layers(lod_mesh, uv_names, colour_names)
    return material


def prepare_garment(context: Any, obj: Any, skeleton: Skeleton) -> Dict[str, Any]:
    """Everything the export needs on a garment that sits on its skeleton: the drawable model, the ped material with
    the images, smooth shading on every level of detail. Returns the images it found."""
    gh.hide_problems(obj)
    images = garment_images(obj)
    if images["diffuse"] is None:
        raise fail("add.why.no-diffuse")
    convert_to_model(context, obj)
    setup_material(context, obj, images)
    for mesh in [obj.data, *lod_meshes(obj)]:
        shade_smooth(mesh)
    return images


# --------------------------------------------------------------------------------------------------
# The export and the pictures
# --------------------------------------------------------------------------------------------------


class Export(NamedTuple):
    model: Tuple[str, bytes]
    textures: List[Tuple[str, bytes]]
    warnings: bool
    summary: garment_add.ExportSummary


def export_garment(skeleton: Skeleton, folder: pathlib.Path) -> Export:
    """Exports the skeleton's Drawable Dictionary (the garment on it) with Sollumz as CodeWalker XML with Exclude Skeleton
    into ``folder`` and reads the files. An export Sollumz logged errors for, or one without the garment's geometry,
    is refused (Sollumz reports success for an empty dictionary)."""
    result = host.export_with_sollumz(skeleton.root, str(folder), EXPORT_OVERRIDES)
    if result.errors:
        raise fail("add.export.errors")
    collected = bundle.collect(folder)
    try:
        with open(collected.model, "rb") as handle:
            summary = garment_add.export_summary(handle)
    except (OSError, ValueError) as exc:
        raise fail("add.export.unreadable", detail=str(exc)) from exc
    problem = garment_add.export_problem(summary)
    if problem is not None:
        raise UserError(problem)
    files = bundle.read_files(collected)
    return Export(files[0], files[1:], bool(result.warnings), summary)


def picture(image: Any) -> Tuple[int, int, bytes]:
    """A colour variation's image as a PNG (sRGB colour, 8 bits per channel), with its size."""
    problem = host.image_problem(image)
    if problem is not None:
        raise UserError(msg("add.picture.unusable", name=image.name if image is not None else "", problem=problem))
    width, height = tuple(image.size)
    channels = image.channels
    source = np.empty(width * height * channels, np.float32)
    image.pixels.foreach_get(source)
    colour = image.colorspace_settings
    plan = pixels.colour_plan("diffuse", channels, bool(image.is_float), colour.name,
                              bool(getattr(colour, "is_data", colour.name == "Non-Color")),
                              str(getattr(image, "alpha_mode", "STRAIGHT")))
    rgba = np.empty(width * height * 4, np.uint8)
    pixels.to_rgba8(source, rgba, width, height, plan.conversion)
    return width, height, garment_add.png_bytes(rgba, width, height)


def store_added(root: Any, obj: Any, binding: Dict[str, str], name: str) -> None:
    """Links the Drawable Dictionary to the cloth Durty Cloth Tool added (as a model opened from it is linked), so Push
    Model and Save Model to Cloth go to that cloth, and marks the garment as added."""
    host.store_binding(root, binding)
    for other in host.others_linked_alike(root):
        host.clear_binding(other)
    obj[ADDED] = name


__all__ = [
    "ADDED",
    "Export",
    "SKELETON_TAG",
    "Skeleton",
    "attach",
    "export_garment",
    "garment_images",
    "import_skeleton",
    "picture",
    "prepare_garment",
    "remove_stale_work",
    "skeleton_of",
    "skeleton_problem",
    "store_added",
    "work_folder",
]
