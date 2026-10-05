# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2026 Schmid Software Solutions (https://schmid-software.de)
"""Stand-ins for Sollumz's export and import operators, its conversion to a drawable model, its shader materials and
its LOD slots, for the Blender smoke and the interface screenshots.

They have the operator properties of Sollumz 2.8.1 and later (``sollumz.export_assets``) and of Sollumz 2.9
(``sollumz.import_assets``), write and read what Sollumz writes (a ``*.ydd.xml`` and its ``*.dds`` textures in a
folder named after the model), and record every call in :data:`STUB`. The export writes one ``Item`` per drawable
with its models' geometry (and the skeleton of an armature drawable unless Exclude Skeleton is on); in the mode
``empty`` it writes an empty dictionary and still reports success, as Sollumz does for a drawable without its High
level. The import makes an armature drawable from a skeleton in the XML (as for Durty Cloth Tool's skeleton template).
``sollumz.createshadermaterial`` adds a ped shader material with its samplers and placeholder images and names UV maps
and colours by order, as Sollumz does. ``Object.sz_lods`` keeps a mesh per level of detail as Sollumz 2.9 does (the
active level's mesh is the object's own). Only for use inside Blender.
"""

from __future__ import annotations

import pathlib
from xml.etree import ElementTree

import bpy
from bpy.props import (BoolProperty, CollectionProperty, EnumProperty, PointerProperty,  # module level: annotations
                       StringProperty)

STUB = {"mode": "ydd", "calls": [], "imports": []}


class SOLLUMZ_OT_export_assets(bpy.types.Operator):
    bl_idname = "sollumz.export_assets"
    bl_label = "Export (stand-in)"
    directory: StringProperty(subtype="DIR_PATH")
    direct_export: BoolProperty()
    use_custom_settings: BoolProperty()
    target_formats: EnumProperty(items=(("NATIVE", "Native", ""), ("CWXML", "CW XML", "")), options={"ENUM_FLAG"},
                                 default={"NATIVE", "CWXML"})
    target_versions: EnumProperty(items=(("GEN8", "Gen8", ""), ("GEN9", "Gen9", "")), options={"ENUM_FLAG"},
                                  default={"GEN8", "GEN9"})
    limit_to_selected: BoolProperty(default=False)
    exclude_skeleton: BoolProperty()
    apply_transforms: BoolProperty()
    mesh_domain: EnumProperty(items=(("FACE_CORNER", "Face Corner", ""), ("VERTEX", "Vertex", "")),
                              default="FACE_CORNER")

    def execute(self, context):
        selected = [o for o in context.view_layer.objects if o.select_get()]
        call = {
            "directory": self.directory, "custom": self.use_custom_settings,
            "formats": sorted(self.target_formats), "versions": sorted(self.target_versions),
            "limit": self.limit_to_selected, "selected": [o.name for o in selected], "poses": [],
            "exclude_skeleton": self.exclude_skeleton, "mesh_domain": self.mesh_domain,
        }
        STUB["calls"].append(call)
        folder = pathlib.Path(self.directory)
        top = selected[0]
        while top.parent is not None:
            top = top.parent
        # Like Sollumz: every armature of the model is exported in its rest pose, then switched back.
        for armature in [o for o in [top, *top.children_recursive] if o.type == "ARMATURE"]:
            previous = armature.data.pose_position
            armature.data.pose_position = "REST"
            context.evaluated_depsgraph_get()
            call["poses"].append(armature.data.pose_position)
            armature.data.pose_position = previous
            call["poses"].append(armature.data.pose_position)
        name = top.name.lower()
        if STUB["mode"] == "ydr":
            (folder / f"{name}.ydr.xml").write_text("<Drawable />")
            return {"FINISHED"}
        xml = "<DrawableDictionary />" if STUB["mode"] == "empty" else dictionary_xml(top, self.exclude_skeleton)
        call["xml"] = xml
        (folder / f"{name}.ydd.xml").write_text(xml)
        (folder / name).mkdir(exist_ok=True)
        (folder / name / "smoke_diff_000_a_uni.dds").write_bytes(b"DDS " + bytes(124))
        return {"FINISHED"}


class SOLLUMZ_OT_import_assets(bpy.types.Operator):
    """Creates a Drawable Dictionary named after the ``*.ydd.xml`` with one Drawable and one mesh, and an image
    for every ``*.dds`` in the folder named after the model (packed in ``PACK`` mode, as Sollumz does)."""

    bl_idname = "sollumz.import_assets"
    bl_label = "Import (stand-in)"
    bl_options = {"UNDO"}
    directory: StringProperty(subtype="DIR_PATH", options={"HIDDEN", "SKIP_SAVE"})
    files: CollectionProperty(type=bpy.types.OperatorFileListElement, options={"HIDDEN", "SKIP_SAVE"})
    use_custom_settings: BoolProperty(options={"HIDDEN", "SKIP_SAVE"})
    textures_mode: EnumProperty(items=(("PACK", "Pack", ""), ("IMPORT_DIR", "Import Directory", ""),
                                       ("CUSTOM_DIR", "Custom Directory", "")), default="PACK")
    split_by_group: BoolProperty(default=True)

    def execute(self, context):
        folder = pathlib.Path(self.directory)
        names = [f.name for f in self.files]
        skeletons = {name: skeleton_of(folder / name) for name in names}
        STUB["imports"].append({"directory": self.directory, "files": names, "custom": self.use_custom_settings,
                                "textures_mode": self.textures_mode,
                                "found": sorted(p.relative_to(folder).as_posix() for p in folder.rglob("*")
                                                if p.is_file())})
        if STUB["mode"] == "fail-import":
            self.report({"ERROR"}, "stand-in import failure")
            return {"CANCELLED"}
        for name in names:
            stem = name.split(".", 1)[0]
            root = bpy.data.objects.new(stem, None)
            root.sollum_type = "sollumz_drawable_dictionary"
            if skeletons[name] is not None:
                drawable_name, bones = skeletons[name]
                armature = armature_drawable(context, drawable_name, bones)
                armature.parent = root
                context.collection.objects.link(root)
                continue
            drawable = bpy.data.objects.new(f"{stem}_drawable", None)
            drawable.sollum_type = "sollumz_drawable"
            drawable.parent = root
            mesh = bpy.data.meshes.new(f"{stem}_mesh")
            mesh.from_pydata([(0, 0, 0), (1, 0, 0), (0, 1, 0)], [], [(0, 1, 2)])
            part = bpy.data.objects.new(f"{stem}_part", mesh)
            part.sollum_type = "sollumz_drawable_model"
            part.parent = drawable
            for obj in (root, drawable, part):
                context.collection.objects.link(obj)
            for texture in sorted((folder / stem).glob("*.dds")):
                image = bpy.data.images.new(texture.name, 4, 4)
                image.filepath = str(texture)
                if self.textures_mode == "PACK":
                    image.pack()
        return {"FINISHED"}


def skeleton_of(path: pathlib.Path):
    """``(drawable name, [(bone, parent index, (x, y, z))])`` of the first drawable with bones in a CodeWalker XML."""
    try:
        root = ElementTree.parse(path).getroot()
    except (OSError, ElementTree.ParseError):
        return None
    for item in root.findall("Item"):
        bones = item.findall("Skeleton/Bones/Item")
        if bones:
            found = []
            for bone in bones:
                t = bone.find("Translation")
                found.append((bone.findtext("Name"), int(bone.find("ParentIndex").get("value")),
                              tuple(float(t.get(axis)) for axis in "xyz")))
            return item.findtext("Name"), found
    return None


def armature_drawable(context, name, bones):
    """A Drawable that is an armature with ``bones`` in their order (heads from the parents' offsets)."""
    data = bpy.data.armatures.new(f"{name}.skel")
    obj = bpy.data.objects.new(name, data)
    obj.sollum_type = "sollumz_drawable"
    context.collection.objects.link(obj)
    view_layer = context.view_layer
    previous = view_layer.objects.active
    view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode="EDIT")
    heads, edit = [], []
    for bone_name, parent, offset in bones:
        head = [a + b for a, b in zip(heads[parent], offset)] if parent >= 0 else list(offset)
        heads.append(head)
        bone = data.edit_bones.new(bone_name)
        bone.head = head
        bone.tail = (head[0], head[1] + 0.05, head[2])
        if parent >= 0:
            bone.parent = edit[parent]
        edit.append(bone)
    bpy.ops.object.mode_set(mode="OBJECT")
    view_layer.objects.active = previous
    return obj


def dictionary_xml(top, exclude_skeleton):
    """What Sollumz writes for a Drawable Dictionary: one Item per drawable, with the geometry of its models' High
    level, and an armature drawable's skeleton unless it is excluded."""
    items = []
    for drawable in [c for c in top.children if getattr(c, "sollum_type", "") == "sollumz_drawable"]:
        models = [c for c in drawable.children if getattr(c, "sollum_type", "") == "sollumz_drawable_model"
                  and c.type == "MESH" and len(c.data.polygons)]
        skeleton = ""
        if drawable.type == "ARMATURE" and not exclude_skeleton:
            skeleton = "<Skeleton><Bones>" + "".join(f"<Item><Name>{b.name}</Name></Item>"
                                                     for b in drawable.data.bones) + "</Bones></Skeleton>"
        geometry = "".join("<Item><Geometries><Item><VertexBuffer /></Item></Geometries></Item>" for _ in models)
        items.append(f"<Item><Name>{drawable.name}</Name>{skeleton}<DrawableModelsHigh>{geometry}"
                     f"</DrawableModelsHigh></Item>")
    return "<?xml version='1.0' encoding='UTF-8'?>\n<DrawableDictionary>" + "".join(items) + "</DrawableDictionary>\n"


class SOLLUMZ_OT_convert_to_drawable_model(bpy.types.Operator):
    """Makes every selected mesh a Drawable Model whose High level is its own mesh."""

    bl_idname = "sollumz.converttodrawablemodel"
    bl_label = "Convert to Drawable Model (stand-in)"
    bl_options = {"UNDO"}

    def execute(self, context):
        meshes = [o for o in context.selected_objects if o.type == "MESH"]
        STUB.setdefault("converted", []).extend(o.name for o in meshes)
        if not meshes:
            return {"CANCELLED"}
        for obj in meshes:
            obj.sollum_type = "sollumz_drawable_model"
            obj.sz_lods.high.has_mesh = True
            obj.sz_lods.active_lod_level = "sollumz_high"
        return {"FINISHED"}


#: The ped shader's samplers, in Sollumz's order.
PED_SAMPLERS = ("DiffuseSampler", "TextureSamplerDiffPal", "VolumeSampler", "BumpSampler", "SpecSampler")


class SZ_ShaderProperties(bpy.types.PropertyGroup):
    filename: StringProperty()


class SZ_TextureProperties(bpy.types.PropertyGroup):
    embedded: BoolProperty(default=False)


def _name_by_order(collection, used, new):
    """Sollumz's naming: unused layers take the missing names in order, then the rest are added."""
    missing = [name for name in used if collection.get(name) is None]
    for layer in list(collection):
        if not missing:
            break
        if layer.name not in used:
            layer.name = missing.pop(0)
    for name in missing:
        new(name)


class SOLLUMZ_OT_create_shader_material(bpy.types.Operator):
    """Adds a ped shader material with placeholder images to every selected mesh, as Sollumz does."""

    bl_idname = "sollumz.createshadermaterial"
    bl_label = "Create Shader Material (stand-in)"
    bl_options = {"UNDO"}
    shader_index: bpy.props.IntProperty()

    def execute(self, context):
        for obj in [o for o in bpy.context.selected_objects if o.type == "MESH"]:
            material = bpy.data.materials.new("ped")
            material.use_nodes = True
            material.sollum_type = "sollumz_material_shader"
            material.shader_properties.filename = "ped.sps"
            for sampler in PED_SAMPLERS:
                node = material.node_tree.nodes.new("ShaderNodeTexImage")
                node.name = sampler
                node.image = bpy.data.images.new("Texture", 8, 8)
            mesh = obj.data
            mesh.materials.append(material)
            _name_by_order(mesh.uv_layers, ("UVMap 0", "UVMap 1"),
                           lambda name: mesh.attributes.new(name=name, type="FLOAT2", domain="CORNER"))
            _name_by_order(mesh.color_attributes, ("Color 1", "Color 2"),
                           lambda name: mesh.color_attributes.new(name, "BYTE_COLOR", "CORNER"))
        return {"FINISHED"}


LOD_LEVELS = (("sollumz_high", "High", ""), ("sollumz_medium", "Medium", ""), ("sollumz_low", "Low", ""),
              ("sollumz_verylow", "Very Low", ""), ("sollumz_veryhigh", "Very High", ""))


class SZ_LODLevel(bpy.types.PropertyGroup):
    mesh_ref: PointerProperty(type=bpy.types.Mesh)
    has_mesh: BoolProperty(default=False)

    def _active(self):
        lods = self.id_data.sz_lods
        return lods.get_lod(lods.active_lod_level) == self

    @property
    def mesh(self):
        if not self.has_mesh:
            return None
        return self.id_data.data if self._active() else self.mesh_ref

    @mesh.setter
    def mesh(self, value):
        self.has_mesh = value is not None
        if self._active():
            self.mesh_ref = None
            if value is not None:
                self.id_data.data = value
        else:
            self.mesh_ref = value


class SZ_LODLevels(bpy.types.PropertyGroup):
    active_lod_level: EnumProperty(items=LOD_LEVELS, default="sollumz_high")
    very_high: PointerProperty(type=SZ_LODLevel)
    high: PointerProperty(type=SZ_LODLevel)
    medium: PointerProperty(type=SZ_LODLevel)
    low: PointerProperty(type=SZ_LODLevel)
    very_low: PointerProperty(type=SZ_LODLevel)

    def get_lod(self, level):
        return {"sollumz_veryhigh": self.very_high, "sollumz_high": self.high, "sollumz_medium": self.medium,
                "sollumz_low": self.low, "sollumz_verylow": self.very_low}[level]


def register():
    for cls in (SOLLUMZ_OT_export_assets, SOLLUMZ_OT_import_assets, SOLLUMZ_OT_convert_to_drawable_model,
                SZ_ShaderProperties, SZ_TextureProperties, SOLLUMZ_OT_create_shader_material, SZ_LODLevel, SZ_LODLevels):
        bpy.utils.register_class(cls)
    bpy.types.Object.sz_lods = PointerProperty(type=SZ_LODLevels)
    bpy.types.Material.sollum_type = EnumProperty(items=(
        ("sollumz_material_none", "None", ""), ("sollumz_material_shader", "Shader", ""),
    ), default="sollumz_material_none")
    bpy.types.Material.shader_properties = PointerProperty(type=SZ_ShaderProperties)
    bpy.types.ShaderNodeTexImage.texture_properties = PointerProperty(type=SZ_TextureProperties)
    bpy.types.Object.sollum_type = EnumProperty(items=(
        ("sollumz_none", "None", ""), ("sollumz_drawable_dictionary", "Drawable Dictionary", ""),
        ("sollumz_drawable", "Drawable", ""), ("sollumz_drawable_model", "Drawable Model", ""),
    ), default="sollumz_none")


def scene():
    """A Drawable Dictionary with one Drawable and a one-triangle mesh, linked into the current scene."""
    collection = bpy.context.scene.collection
    root = bpy.data.objects.new("smoke_ydd", None)
    root.sollum_type = "sollumz_drawable_dictionary"
    drawable = bpy.data.objects.new("smoke_drawable", None)
    drawable.sollum_type = "sollumz_drawable"
    drawable.parent = root
    mesh = bpy.data.meshes.new("smoke_mesh")
    mesh.from_pydata([(0, 0, 0), (1, 0, 0), (0, 1, 0)], [], [(0, 1, 2)])
    part = bpy.data.objects.new("smoke_part", mesh)
    part.sollum_type = "sollumz_drawable_model"
    part.parent = drawable
    for obj in (root, drawable, part):
        collection.objects.link(obj)
    return root, part
