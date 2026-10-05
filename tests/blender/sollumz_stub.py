# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2026 Schmid Software Solutions (https://schmid-software.de)
"""Stand-ins for Sollumz's export and import operators and its LOD slots, for the Blender smoke and the interface
screenshots.

They have the operator properties of Sollumz 2.8.1 and later (``sollumz.export_assets``) and of Sollumz 2.9
(``sollumz.import_assets``), write and read what Sollumz writes (a ``*.ydd.xml`` and its ``*.dds`` textures in a
folder named after the model), and record every call in :data:`STUB`. ``Object.sz_lods`` keeps a mesh per level of
detail as Sollumz 2.9 does (the active level's mesh is the object's own). Only for use inside Blender.
"""

from __future__ import annotations

import pathlib

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

    def execute(self, context):
        selected = [o for o in context.view_layer.objects if o.select_get()]
        call = {
            "directory": self.directory, "custom": self.use_custom_settings,
            "formats": sorted(self.target_formats), "versions": sorted(self.target_versions),
            "limit": self.limit_to_selected, "selected": [o.name for o in selected], "poses": [],
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
        (folder / f"{name}.ydd.xml").write_text(f"<DrawableDictionary revision='{len(STUB['calls'])}' />")
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
    for cls in (SOLLUMZ_OT_export_assets, SOLLUMZ_OT_import_assets, SZ_LODLevel, SZ_LODLevels):
        bpy.utils.register_class(cls)
    bpy.types.Object.sz_lods = PointerProperty(type=SZ_LODLevels)
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
