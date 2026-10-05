# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2026 Schmid Software Solutions (https://schmid-software.de)
"""The garment fitting tools in Blender, on a synthetic body and synthetic garments (no game files): importing a
garment, the hosted body from the fake gta.clothing and a body file, markers and presets, the fit check and the
problem colours, push out, snug, relax, the sculpt session, T-pose to A-pose, the tear check, prepare, combine
materials, levels of detail, validate, backups, and that nothing else in the scene changes.

Called by ``smoke_in_blender.py`` while the add-on is signed in to the fake gta.clothing. Only for use inside
Blender.
"""

from __future__ import annotations

import math
import pathlib
import sys
import tempfile

import bmesh
import bpy
import numpy as np

from tests.support import synthetic


def mesh_object(name, mesh_data, collection=None):
    """A Blender mesh object from a :class:`synthetic.Mesh`."""
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(mesh_data.positions.tolist(), [], [tuple(f) for f in mesh_data.faces])
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    (collection or bpy.context.scene.collection).objects.link(obj)
    return obj


def body_glb(folder):
    """The synthetic body written as a GLB file (what gta.clothing serves, made from nothing of the game)."""
    body = mesh_object("smoke_body_source", synthetic.body(45.0))
    path = folder / "freemode_male.glb"
    for obj in bpy.context.view_layer.objects:
        obj.select_set(False)
    body.select_set(True)
    bpy.context.view_layer.objects.active = body
    bpy.ops.export_scene.gltf(filepath=str(path), use_selection=True, export_format="GLB")
    bpy.data.objects.remove(body)
    return path


def textured_material(name, rgb):
    image = bpy.data.images.new(f"{name}_tex", 64, 64)
    pixels = np.tile(np.array([*rgb, 1.0], dtype=np.float32), 64 * 64)
    pixels.reshape(64, 64, 4)[::8, :, :3] = 0.1  # stripes, so the bake has something to copy
    image.pixels.foreach_set(pixels)
    image.pack()
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    tree = material.node_tree
    shader = next(n for n in tree.nodes if n.type == "BSDF_PRINCIPLED")
    texture = tree.nodes.new("ShaderNodeTexImage")
    texture.image = image
    tree.links.new(texture.outputs["Color"], shader.inputs["Base Color"])
    return material


def panel_garment(name, sleeves, angle, collection=None):
    """A synthetic top made like a Marvelous Designer export: front, back and hem band as separate panels (three
    materials, open seams where they meet) with their own UV islands, the hem band a long thin strip."""
    obj = mesh_object(name, synthetic.top(sleeves, angle), collection)
    mesh = obj.data
    for material, rgb in (("front", (0.8, 0.2, 0.2)), ("back", (0.2, 0.3, 0.8)), ("band", (0.9, 0.9, 0.2))):
        mesh.materials.append(textured_material(f"{name}_{material}", rgb))
    bm = bmesh.new()
    bm.from_mesh(mesh)
    hem = min(v.co.z for v in bm.verts) + 0.04
    for face in bm.faces:
        centre = face.calc_center_median()
        face.material_index = 2 if centre.z < hem else (0 if centre.y < 0 else 1)
    seams = [e for e in bm.edges if len(e.link_faces) == 2
             and e.link_faces[0].material_index != e.link_faces[1].material_index]
    bmesh.ops.split_edges(bm, edges=seams)
    uv = bm.loops.layers.uv.new("UVMap")
    for face in bm.faces:
        for loop in face.loops:
            co = loop.vert.co
            if face.material_index == 2:
                loop[uv].uv = ((math.atan2(co.y, co.x) / (2 * math.pi)) % 1.0, (co.z - hem + 0.04) * 0.5)
            elif face.material_index == 0:
                loop[uv].uv = (co.x * 0.7 + 0.5, co.z * 0.7 + 0.35)
            else:  # the back panel has a pattern piece of its own, mirrored as seen from behind
                loop[uv].uv = (1.6 - co.x * 0.7, co.z * 0.7 + 0.35)
    bm.to_mesh(mesh)
    bm.free()
    return obj


def split_weights(obj):
    """Weights the front panel's left shoulder to the chest only, as separately weighted panels can be, so the
    seam to the back panel opens when the arm moves."""
    spine = obj.vertex_groups["SKEL_Spine3"]
    arm = obj.vertex_groups["SKEL_L_UpperArm"]
    front = {v for p in obj.data.polygons if p.material_index == 0 for v in p.vertices}
    chosen = [v.index for v in obj.data.vertices if v.index in front and v.co.x > 0.12 and v.co.z > 0.3]
    arm.remove(chosen)
    spine.add(chosen, 1.0, "REPLACE")
    return chosen


def positions(obj):
    values = np.empty(len(obj.data.vertices) * 3)
    obj.data.vertices.foreach_get("co", values)
    return values.reshape(-1, 3) @ np.array(obj.matrix_world)[:3, :3].T + np.array(obj.matrix_world)[:3, 3]


def run(package, addon, state, ctrl, api, check, refused, pump, draw_everything):
    ui_garment = sys.modules[package + ".ui_garment"]
    gh = sys.modules[package + ".garment_host"]
    garment = sys.modules[package + ".garment"]
    scene = bpy.context.scene
    props = scene.dct_garment
    folder = pathlib.Path(tempfile.mkdtemp(prefix="dct_smoke_garment_", dir=str(pathlib.Path(ctrl.data_dir).parent)))

    # Something of the user's that the tools must never touch.
    bpy.ops.mesh.primitive_cube_add(location=(3.0, 0.0, 0.0))
    users_cube = bpy.context.active_object
    users_cube.name = "users_cube"
    users_shape = positions(users_cube).copy()

    log = draw_everything(package, state, "garment fitting, nothing chosen")
    labels = " ".join(entry[1] for entry in log if entry[0] == "label")
    check("the garment panels draw and say how to start", "Import a garment" in labels
          and ("operator", "dct_link.fit_import_garment") in log, labels[:300])
    check("every garment operator that changes a mesh can be undone",
          all("UNDO" in cls.bl_options for cls in ui_garment.CLASSES
              if getattr(cls, "bl_idname", "").startswith("dct_link.fit_")
              and cls.bl_idname not in ("dct_link.fit_add_body", "dct_link.fit_cancel_body",
                                        "dct_link.fit_save_preset")))

    # Import: a garment exported in centimetres on an avatar standing on the ground arrives in metres, in ped space.
    source = panel_garment("smoke_tee_source", "short", 45.0)
    source.location = (0.0, 0.0, 100.0)  # the avatar stood on the ground: 1 m in centimetres
    source.scale = (100.0, 100.0, 100.0)
    for obj in bpy.context.view_layer.objects:
        obj.select_set(obj == source)
    bpy.context.view_layer.objects.active = source
    obj_path = folder / "smoke_tee.obj"
    bpy.ops.wm.obj_export(filepath=str(obj_path), export_selected_objects=True, export_materials=True)
    expected = positions(source) / 100.0 - [0.0, 0.0, 1.0]
    materials = list(source.data.materials)
    bpy.data.objects.remove(source)
    check("Import Garment runs", "FINISHED" in bpy.ops.dct_link.fit_import_garment(filepath=str(obj_path),
                                                                                    ground=True))
    tee = props.garment
    check("the imported garment is in metres and in ped space",
          tee is not None and abs(positions(tee)[:, 2].max() - expected[:, 2].max()) < 1e-3
          and abs(positions(tee)[:, 0].max() - expected[:, 0].max()) < 1e-3,
          (positions(tee).max(axis=0), expected.max(axis=0)))
    # The OBJ importer makes its own materials; the fabrics' textures are put back for the bake later.
    for index, material in enumerate(materials):
        if index < len(tee.data.materials):
            tee.data.materials[index] = material

    # The hosted body: downloaded from the fake gta.clothing for the signed-in account and kept per version.
    glb = body_glb(folder)
    api.body_files = {"freemode_male.glb": glb.read_bytes()}
    ui_garment.BODY_ORIGIN["url"] = api.base_url
    props.gender = "male"
    check("Add Freemode Body runs", "FINISHED" in bpy.ops.dct_link.fit_add_body())
    pump(addon, lambda: ui_garment.RUNTIME.download is None or (ui_garment.body_tick() is None), timeout=30,
         what="the body download")
    ui_garment.body_tick()
    body = props.body
    version = api.manifest["body"]["version"]
    check("the hosted body was downloaded with a ticket, kept and added",
          body is not None and body.get(gh.BODY_TAG) == "male" and body.get(gh.BODY_VERSION) == version
          and (pathlib.Path(ctrl.data_dir) / "body" / version / "freemode_male.glb").is_file()
          and "POST /link/panel/ticket" in api.paths(), (ui_garment.RUNTIME.notice, api.paths()[-3:]))
    tickets = len(api.tickets)
    check("Add Freemode Body runs again", "FINISHED" in bpy.ops.dct_link.fit_add_body())
    pump(addon, lambda: ui_garment.RUNTIME.download is None or (ui_garment.body_tick() is None), timeout=30,
         what="the second body download")
    ui_garment.body_tick()
    bodies = [o for o in scene.objects if o.get(gh.BODY_TAG)]
    check("a kept body version is not downloaded again and replaces the one before",
          len(api.tickets) == tickets and len(bodies) == 1 and props.body == bodies[0], len(bodies))
    check("Use a Body File runs", "FINISHED" in bpy.ops.dct_link.fit_body_file(filepath=str(glb)))
    check("a body file replaces the added body", len([o for o in scene.objects if o.get(gh.BODY_TAG)]) == 1
          and props.body is not None and len(props.body.data.polygons) > 100)
    body = props.body

    # Markers.
    props.slot = "jbib"
    props.category = "tshirt"
    props.source_pose = "a_pose"
    check("Auto Markers runs", "FINISHED" in bpy.ops.dct_link.fit_auto_markers())
    markers = gh.read_markers(scene)
    joints = synthetic.top("short", 45.0).joints
    check("the 11 markers sit on the garment's joints", len(markers) == 11 and all(
        np.linalg.norm(np.array(markers[name]) - np.array(joints[name])) < 0.06 for name in joints),
        {k: np.round(v, 3).tolist() for k, v in markers.items()})
    marker_objects = gh.marker_objects(scene)
    marker_objects["shoulder_l"].location.x += 0.02
    check("Mirror L to R runs", "FINISHED" in bpy.ops.dct_link.fit_mirror_markers())
    mirrored = gh.read_markers(scene)
    check("the right shoulder mirrors the left one",
          abs(mirrored["shoulder_r"][0] + mirrored["shoulder_l"][0] - 2 * garment.centre_x(mirrored)) < 1e-5)
    check("Save Pose Preset runs", "FINISHED" in bpy.ops.dct_link.fit_save_preset(name="smoke tee"))
    preset = pathlib.Path(ctrl.data_dir) / "garment-presets" / "smoke tee.json"
    check("the preset is saved in the add-on's folder", preset.is_file())
    marker_objects["neck"].location.z += 0.2
    check("Load Pose Preset runs", "FINISHED" in bpy.ops.dct_link.fit_load_preset(name="smoke tee"))
    check("loading the preset puts the markers back",
          abs(gh.read_markers(scene)["neck"][2] - mirrored["neck"][2]) < 1e-4)
    props.marker_size = 0.05
    check("Marker Size resizes the markers", all(abs(o.empty_display_size - 0.05) < 1e-6
                                                 for o in gh.marker_objects(scene).values()))

    # The fit check and the problem colours; the neck of the synthetic tee sits inside the head.
    check("Run Fit Check runs", "FINISHED" in bpy.ops.dct_link.fit_check())
    report = garment.FitReport.from_json(tee.get(gh.FIT_REPORT, ""))
    rows = {row.region: row for row in report.rows} if report else {}
    check("the fit check measures the regions in millimetres",
          report is not None and {"chest", "back", "shoulders", "upper_arms"} <= set(rows)
          and 5.0 < rows["chest"].p50 < 40.0 and report.inside > 0,
          report)
    RESULT = {"check": "fit check (synthetic tee)", "ok": True,
              "detail": ", ".join(f"{r.region} {r.p50}" for r in report.rows) + f"; inside {report.inside}"}
    check("Show Problems runs", "FINISHED" in bpy.ops.dct_link.fit_show_problems())
    attribute = tee.data.color_attributes.get(gh.PROBLEMS)
    colours = np.empty(len(tee.data.vertices) * 4, dtype=np.float32)
    attribute.data.foreach_get("color", colours) if attribute is not None else None
    reds = int((np.abs(colours.reshape(-1, 4)[:, :3] - garment.PROBLEM_COLOURS["inside"][:3]).max(axis=1)
                < 0.02).sum()) if attribute is not None else 0
    check("the problem colours show the vertices inside the body in red", attribute is not None and reds > 0, reds)
    log = draw_everything(package, state, "garment with problems shown")
    labels = " ".join(entry[1] for entry in log if entry[0] == "label")
    check("the Fix panel shows the report and the colour legend",
          "Inside the body" in labels and "Floating shoulder" in labels and "Measured (mm)" in labels, labels[-400:])
    check("Refresh runs", "FINISHED" in bpy.ops.dct_link.fit_refresh_problems())

    # Push out, snug and relax (each keeps a backup).
    check("Push Out of Body runs", "FINISHED" in bpy.ops.dct_link.fit_push_out())
    signed, _, _ = gh.clearance(gh.body_tree(body), positions(tee))
    check("nothing is inside the body after Push Out of Body", int((signed < -0.001).sum()) == 0,
          int((signed < -0.001).sum()))
    check("the problem colours follow the change", tee.data.color_attributes.get(gh.PROBLEMS) is not None)
    check("Show Problems hides the colours again", "FINISHED" in bpy.ops.dct_link.fit_show_problems()
          and tee.data.color_attributes.get(gh.PROBLEMS) is None)
    before = positions(tee)
    props.region = "shoulders"
    props.snug_gap = 5.0
    check("Snug to Body runs", "FINISHED" in bpy.ops.dct_link.fit_snug())
    moved = np.linalg.norm(positions(tee) - before, axis=1)
    check("Snug to Body moved the shoulders towards the body", int((moved > 1e-4).sum()) > 0)
    props.region = "legs"
    check("a region the category does not cover is refused", refused(bpy.ops.dct_link.fit_snug, "not part"))
    props.region = "chest"
    check("Relax Stretched runs", "FINISHED" in bpy.ops.dct_link.fit_relax())
    check("three backups are kept at most", len(gh.backups(tee)) == gh.MAX_BACKUPS, len(gh.backups(tee)))

    # The sculpt session: Cancel puts the shape back, Accept keeps it and moves what went inside back out.
    shape = positions(tee)
    check("Start Sculpting runs", "FINISHED" in bpy.ops.dct_link.fit_sculpt_start())
    check("the sculpt session runs in Sculpt Mode", gh.sculpting(tee) and tee.mode == "SCULPT", tee.mode)
    log = draw_everything(package, state, "sculpting")
    check("the session offers Accept and Cancel", ("operator", "dct_link.fit_sculpt_accept") in log
          and ("operator", "dct_link.fit_sculpt_cancel") in log)
    check("other garment steps wait for the session", refused(bpy.ops.dct_link.fit_push_out, "sculpt session"))
    bpy.ops.object.mode_set(mode="OBJECT")
    tee.data.vertices[0].co.x += 0.05
    check("Cancel runs", "FINISHED" in bpy.ops.dct_link.fit_sculpt_cancel())
    check("Cancel puts back the shape from before the session",
          np.abs(positions(tee) - shape).max() < 1e-6 and not gh.sculpting(tee) and tee.mode == "OBJECT")
    bpy.ops.dct_link.fit_sculpt_start()
    bpy.ops.object.mode_set(mode="OBJECT")
    chest = np.array(gh.read_markers(scene)["chest"])
    centre = chest + [0.0, -0.13, 0.0]
    near = np.argsort(np.linalg.norm(positions(tee) - centre, axis=1))[:6]
    for index in near:
        tee.data.vertices[int(index)].co.y = float(chest[1])  # pushed deep into the body
    check("Accept runs", "FINISHED" in bpy.ops.dct_link.fit_sculpt_accept())
    notice = ui_garment.RUNTIME.notice
    dragged = positions(tee)[near]
    signed, _, _ = gh.clearance(gh.body_tree(body), dragged)
    check("Accept reports the moved vertices and puts what went into the body back out, on its own side",
          notice is not None and notice.message.key == "garment.done.accept"
          and notice.message.fields["moved"] >= 6 and notice.message.fields["after"] <= notice.message.fields["before"]
          and bool(np.all(signed > 0.003)) and bool(np.all(dragged[:, 1] < chest[1]))
          and not gh.sculpting(tee), (notice, signed, dragged[:, 1]))

    # Restore Pre-fit.
    check("Restore Pre-fit runs", "FINISHED" in bpy.ops.dct_link.fit_restore())
    check("Restore Pre-fit puts back the imported shape", np.abs(positions(tee) - expected).max() < 1e-4)

    # T-pose to A-pose on a garment made in T-pose.
    tpose = panel_garment("smoke_tpose", "long", 0.0)
    for obj in bpy.context.view_layer.objects:
        obj.select_set(obj == tpose)
    bpy.context.view_layer.objects.active = tpose
    check("Use Selected Garment runs", "FINISHED" in bpy.ops.dct_link.fit_use_garment())
    props.category = "long_sleeve"
    props.source_pose = "t_pose"
    bpy.ops.dct_link.fit_auto_markers()
    props.arm_angle = math.radians(40.0)
    reach = positions(tpose)[:, 0].max()
    check("T-pose to A-pose runs", "FINISHED" in bpy.ops.dct_link.fit_tpose_to_apose())
    after = gh.read_markers(scene)
    check("T-pose to A-pose lowers the arms and the markers to the arm angle",
          abs(garment.arm_angle(after, "l") - 40.0) < 2.0 and abs(garment.arm_angle(after, "r") - 40.0) < 2.0
          and positions(tpose)[:, 0].max() < reach - 0.05 and props.source_pose == "a_pose"
          and not any(o.name.startswith(gh.TEMP_PREFIX) for o in bpy.data.objects)
          and not any(g.name.startswith(gh.TEMP_PREFIX) for g in tpose.vertex_groups),
          (garment.arm_angle(after, "l"), reach, positions(tpose)[:, 0].max()))

    # The tear check needs an armature and weights: a small freemode-like rig with Blender's automatic weights.
    rig_data = bpy.data.armatures.new("smoke_rig")
    rig = bpy.data.objects.new("smoke_rig", rig_data)
    scene.collection.objects.link(rig)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode="EDIT")
    bones = {}
    for name, head, tail, parent in (("SKEL_Spine3", "pelvis", "chest", None), ("SKEL_Neck_1", "chest", "neck", 0),
                                     ("SKEL_L_UpperArm", "shoulder_l", "elbow_l", 0),
                                     ("SKEL_L_Forearm", "elbow_l", "wrist_l", 2),
                                     ("SKEL_R_UpperArm", "shoulder_r", "elbow_r", 0),
                                     ("SKEL_R_Forearm", "elbow_r", "wrist_r", 4)):
        bone = rig_data.edit_bones.new(name)
        bone.head, bone.tail = after[head], after[tail]
        if parent is not None:
            bone.parent = list(bones.values())[parent]
        bones[name] = bone
    bpy.ops.object.mode_set(mode="OBJECT")
    for obj in bpy.context.view_layer.objects:
        obj.select_set(obj in (tpose, rig))
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.parent_set(type="ARMATURE_AUTO")
    split_weights(tpose)
    check("Check Tears runs", "FINISHED" in bpy.ops.dct_link.fit_check_tears())
    tears = ui_garment.RUNTIME.tears
    torn = {pose["pose"]: pose["torn"] for pose in tears["poses"]} if tears else {}
    check("the tear check poses the garment and finds the seams that open",
          tears is not None and len(tears["poses"]) == 3 and tears["pairs"] > 0  # no thigh bones: no leg pose
          and torn.get("garment.pose.arms-up", 0) > 0 and tpose.vertex_groups.get(gh.TEARS_GROUP) is not None,
          tears)
    RESULT2 = {"check": "tears (synthetic, unwelded)", "ok": True,
               "detail": "; ".join(f"{p['pose']}: {p['torn']} torn, {p['gap']} mm" for p in tears["poses"])}
    rest_pose = [pose.matrix_basis.copy() for pose in rig.pose.bones]
    check("the tear check puts the pose back", all(
        (pose.matrix_basis - before).to_translation().length < 1e-6 for pose, before in zip(rig.pose.bones, rest_pose)))

    # Game ready: prepare (welds the seams), combine materials (bake), levels of detail, validate.
    props.weld = 2.0
    check("Prepare Garment runs", "FINISHED" in bpy.ops.dct_link.fit_prepare())
    mesh = tpose.data
    colour = mesh.color_attributes.get("Color 1")
    values = np.empty(len(mesh.loops) * 4, dtype=np.float32)
    colour.data.foreach_get("color_srgb", values) if colour is not None else None
    notice = ui_garment.RUNTIME.notice
    check("Prepare welds the seams, triangulates and adds the ped vertex colours",
          notice.message.key == "garment.done.prepare" and notice.message.fields["welded"] > 0
          and all(len(p.vertices) == 3 for p in mesh.polygons)
          and colour is not None and colour.domain == "CORNER" and colour.data_type == "BYTE_COLOR"
          and mesh.color_attributes.get("Color 2") is not None
          and np.allclose(values.reshape(-1, 4)[0], (1.0, 128 / 255, 0.0, 1.0), atol=0.01), notice)
    check("Check Tears runs on the welded garment", "FINISHED" in bpy.ops.dct_link.fit_check_tears())
    check("a welded garment has no open seams left", ui_garment.RUNTIME.tears["pairs"] == 0)
    props.texture_size = "2048"
    check("Combine Materials runs", "FINISHED" in bpy.ops.dct_link.fit_combine_materials())
    notice = ui_garment.RUNTIME.notice
    material = mesh.materials[0] if len(mesh.materials) == 1 else None
    image = next((n.image for n in material.node_tree.nodes if n.type == "TEX_IMAGE"), None) if material else None
    check("Combine Materials bakes one texture onto one material and cuts the hem strip",
          material is not None and image is not None and tuple(image.size) == (2048, 2048)
          and image.packed_file is not None and mesh.uv_layers.active.name == "UVMap 0"
          and mesh.uv_layers.get("DCT Source UV") is not None and notice.message.fields["cut"] >= 1, notice)
    baked = np.empty(2048 * 2048 * 4, dtype=np.float32)
    image.pixels.foreach_get(baked)
    check("the baked texture holds the fabrics' colours", float(baked.reshape(-1, 4)[:, 0].max()) > 0.5)
    RESULT3 = {"check": "combine materials (synthetic)", "ok": True,
               "detail": f"layout uses {notice.message.fields['used']} %, {notice.message.fields['cut']} strips cut"}
    props.lod_medium = 600
    props.lod_low = 150
    check("Generate LODs runs", "FINISHED" in bpy.ops.dct_link.fit_lods())
    lods = tpose.sz_lods
    medium, low = lods.get_lod("sollumz_medium").mesh, lods.get_lod("sollumz_low").mesh
    weighted = medium is not None and sum(1 for v in medium.vertices if v.groups) == len(medium.vertices)
    check("the levels of detail are in Sollumz's slots, decimated and weighted",
          medium is not None and low is not None and len(medium.polygons) <= 700 and len(low.polygons) <= 200
          and lods.get_lod("sollumz_high").mesh == tpose.data and weighted,
          (len(medium.polygons) if medium else None, len(low.polygons) if low else None, weighted))
    check("Validate runs", "FINISHED" in bpy.ops.dct_link.fit_validate())
    findings = garment.findings_from_json(tpose.get(gh.FINDINGS, ""))
    check("Validate lists its findings with the garment", findings is not None, tpose.get(gh.FINDINGS))
    RESULT4 = {"check": "validate (synthetic)", "ok": True,
               "detail": "CLEAN" if garment.is_clean(findings) else ", ".join(f.code for f in findings)}
    log = draw_everything(package, state, "garment game ready")
    check("the Game Ready panel shows the result of Validate",
          any(entry[0] == "label" and ("CLEAN" in entry[1] or "Validate" in entry[1]) for entry in log))

    # Nothing else in the scene changed.
    check("the user's other objects are untouched", np.abs(positions(users_cube) - users_shape).max() == 0
          and users_cube.name == "users_cube")
    return [RESULT, RESULT2, RESULT3, RESULT4]
