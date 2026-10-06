# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2026 Schmid Software Solutions (https://schmid-software.de)
"""The garment fitting tools in Blender, on a synthetic body and synthetic garments (no game files): importing a
garment, the hosted body with its joints from the fake gta.clothing and a body file, markers and presets, Align to
Body and the tools that wait for it, the fit check and the problem colours, push out, snug, relax, the sculpt session,
T-pose to A-pose without tearing a seam, the tear check, prepare, combine materials (with transparency and a normal
map), levels of detail, validate, backups, adding the coat to the project open in the fake Durty Cloth Tool (a
128-bone skeleton template, the checks, the export, the add, an add that fails after the garment changed, Cancel and
the free limit), a one-material garment whose levels of detail keep their UVs, the garment types (an open jacket, a
skirt's bridged weights, a dress split at its waist, a mask aligned from an avatar, a thick export's walls, a hat added
as a prop), and that nothing else in the scene changes.

Called by ``smoke_in_blender.py`` while the add-on is signed in to the fake gta.clothing. Only for use inside
Blender.
"""

from __future__ import annotations

import math
import pathlib
import sys
import tempfile
import types

import bmesh
import bpy
from mathutils import Matrix
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


def textured_material(name, rgb, alpha=1.0, normal=False):
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
    shader.inputs["Alpha"].default_value = alpha  # a see-through fabric (lace, mesh)
    if normal:  # a woven fabric's normal map
        bumps = bpy.data.images.new(f"{name}_normal", 64, 64)
        values = np.tile(np.array([0.5, 0.5, 1.0, 1.0], dtype=np.float32), 64 * 64).reshape(64, 64, 4)
        values[::4, :, 0] = 0.8
        bumps.pixels.foreach_set(values.reshape(-1))
        bumps.colorspace_settings.name = "Non-Color"
        bumps.pack()
        node = tree.nodes.new("ShaderNodeTexImage")
        node.image = bumps
        normal_map = tree.nodes.new("ShaderNodeNormalMap")
        tree.links.new(node.outputs["Color"], normal_map.inputs["Color"])
        tree.links.new(normal_map.outputs["Normal"], shader.inputs["Normal"])
    return material


def panel_garment(name, sleeves, angle, collection=None, maps=False):
    """A synthetic top made like a Marvelous Designer export: front, back and hem band as separate panels (three
    materials, open seams where they meet) with their own UV islands, the hem band a long thin strip. With ``maps``
    the band is half see-through and the front has a normal map."""
    obj = mesh_object(name, synthetic.top(sleeves, angle), collection)
    mesh = obj.data
    for material, rgb in (("front", (0.8, 0.2, 0.2)), ("back", (0.2, 0.3, 0.8)), ("band", (0.9, 0.9, 0.2))):
        mesh.materials.append(textured_material(f"{name}_{material}", rgb, alpha=0.5 if maps and material == "band"
                                                else 1.0, normal=maps and material == "front"))
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


def joints_file():
    """The hosted body's joints (``freemode_joints.json``) for the synthetic body: its skeleton's bone heads."""
    import json

    heads = synthetic.joints_of()
    return json.dumps({"schema": 1, "space": "ped", "units": "m",
                       **{gender: {name: list(head) for name, head in heads.items() if name.startswith("SKEL_")}
                          for gender in ("male", "female")}}).encode("utf-8")


def positions(obj):
    values = np.empty(len(obj.data.vertices) * 3)
    obj.data.vertices.foreach_get("co", values)
    return values.reshape(-1, 3) @ np.array(obj.matrix_world)[:3, :3].T + np.array(obj.matrix_world)[:3, 3]


def run(package, addon, state, ctrl, api, check, refused, pump, draw_everything, dct=None, real=False):
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

    scene.dct_link.workspace = "GARMENT"  # the DCT tab's Garment Fitting view, until the end of this smoke
    log = draw_everything(package, state, "garment fitting, nothing chosen")
    labels = " ".join(entry[1] for entry in log if entry[0] == "label")
    check("the garment panels draw and say how to start", "Import a garment" in labels
          and ("operator", "dct_link.fit_import_garment") in log, labels[:300])
    check("every garment operator that changes a mesh can be undone",
          all("UNDO" in cls.bl_options for cls in ui_garment.CLASSES
              if getattr(cls, "bl_idname", "").startswith("dct_link.fit_")
              and cls.bl_idname not in ("dct_link.fit_add_body", "dct_link.fit_cancel_body",
                                        "dct_link.fit_save_preset", "dct_link.fit_cancel_add",
                                        # These start a run on gta.clothing; its result is an undo step of its own.
                                        "dct_link.fit_service_fit", "dct_link.fit_service_weights",
                                        "dct_link.fit_service_cancel")))

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
    api.body_files = {"freemode_male.glb": glb.read_bytes(), "freemode_joints.json": joints_file()}
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
    check("the hosted body brought its joints", body is not None and body.get(gh.JOINTS_TAG)
          and ui_garment.joints(bpy.context)[1] == "hosted", ui_garment.joints(bpy.context)[1])
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
    check("without the hosted joints Align to Body reads them from the body's shape",
          ui_garment.joints(bpy.context)[1] == "estimate")
    check("Add Freemode Body runs once more (the kept body with its joints)",
          "FINISHED" in bpy.ops.dct_link.fit_add_body())
    pump(addon, lambda: ui_garment.RUNTIME.download is None or (ui_garment.body_tick() is None), timeout=30,
         what="the kept body")
    ui_garment.body_tick()
    body = props.body
    check("the kept body has its joints again", ui_garment.joints(bpy.context)[1] == "hosted")

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
    check("the markers belong to the garment", all(o.get(gh.MARKER_OWNER) == tee.get(gh.GARMENT_ID)
                                                    for o in gh.marker_objects(scene).values()))

    # Align to Body: the tools that measure against the body wait for it.
    check("the fit check waits for Align to Body", refused(bpy.ops.dct_link.fit_check, "Align the garment"))
    check("Push Out of Body waits for Align to Body", refused(bpy.ops.dct_link.fit_push_out, "Align the garment"))
    before_align = positions(tee)
    check("Align to Body keeps the garment's size unless asked", props.keep_size)
    check("Align to Body runs", "FINISHED" in bpy.ops.dct_link.fit_align())
    aligned = gh.read_markers(scene)
    check("Align to Body puts the markers on the joints and leaves a garment that sits there almost as it is",
          tee.get("dct_aligned") and np.abs(positions(tee) - before_align).max() < 0.03
          and abs(aligned["neck"][2] - synthetic.joints_of()["SKEL_Neck_1"][2]) < 0.03,
          (ui_garment.RUNTIME.notice, np.abs(positions(tee) - before_align).max()))

    # Fit to Body on the fake gta.clothing: nothing goes out before the user agreed once; the garment comes back moved
    # by the fake's offset and weighted by bone name, as one step Back One Step takes back.
    prefs = state.preferences()
    prefs.fit_upload_consent = False
    check("without consent Fit to Body uploads nothing",
          refused(bpy.ops.dct_link.fit_service_fit, "send the garment to gta.clothing") and not api.fit.uploads)
    prefs.fit_upload_consent = True
    api.fit.position_offset = (0.0, 0.0, 0.004)
    api.fit.body_version = body.get(gh.BODY_VERSION)  # the fake fits to the hosted body the smoke added
    before_fit = positions(tee)
    check("Fit to Body runs", "FINISHED" in bpy.ops.dct_link.fit_service_fit())
    log = draw_everything(package, state, "garment being fitted")
    labels = " ".join(entry[1] for entry in log if entry[0] == "label")
    check("the Fit panel shows the run with Cancel", ("operator", "dct_link.fit_service_cancel") in log, labels[-300:])
    pump(addon, lambda: not ctrl.fitting.busy, timeout=60, what="the fit on gta.clothing")
    sent_request, _ = api.fit.uploads[-1]
    groups = {group.name for group in tee.vertex_groups}
    check("the fit uploaded the aligned garment with its markers in the rest pose",
          sent_request["sourcePose"] == "rest" and "lShoulder" in sent_request.get("markers", {})
          and "lKnee" not in sent_request.get("markers", {}), sent_request)
    check("Fit to Body moves the garment as gta.clothing answered and weights it by bone name, never to the root",
          np.allclose(positions(tee), before_fit + [0.0, 0.0, 0.004], atol=1e-4) and "SKEL_Spine3" in groups
          and "SKEL_ROOT" not in groups and tee.get("dct_fitted"),
          (ui_garment.RUNTIME.fit_lines, sorted(groups)))
    log = draw_everything(package, state, "garment fitted")
    labels = " ".join(entry[1] for entry in log if entry[0] == "label")
    check("the panel says the fit worked and how many fits are left today",
          "Fitted to the body" in labels and "Fits left today" in labels, labels[-500:])
    check("Back One Step takes the fit back", "FINISHED" in bpy.ops.dct_link.fit_back_step()
          and np.allclose(positions(tee), before_fit, atol=1e-5))
    for group in [g for g in tee.vertex_groups if g.name.startswith("SKEL_")]:
        tee.vertex_groups.remove(group)  # the later steps start from an unweighted garment
    del tee["dct_fitted"]

    # A fit's end that cannot go onto the garment: the panel says why and the garment stays as it is.
    fit_ended = ui_garment.fit_ended
    garment_fit = sys.modules[package + ".garment_fit"]
    key = (scene.name, tee.session_uid)
    digest = gh.fit_digest(tee)
    shape = positions(tee)

    def ended(**fields):
        run = types.SimpleNamespace(key=key, operation="fit", state="done", lines=[],
                                    result=types.SimpleNamespace(outcome="fitted"),
                                    upload=types.SimpleNamespace(digest=digest))
        for name, value in fields.items():
            setattr(run, name, value)
        return run

    def said():
        return [line.key for _, line in ui_garment.RUNTIME.fit_lines]

    failed = ended(state="failed", lines=garment_fit.failure_lines("server_error", refunded=False))
    check("a failed fit shows its lines", fit_ended(failed) and said() == ["fit.error.server", "fit.counted"], said())
    check("a fit for a scene that is gone is not applied",
          fit_ended(ended(key=("No such scene", tee.session_uid))) and said() == ["fit.changed"], said())
    check("a fit for another garment is not applied",
          fit_ended(ended(key=(scene.name, body.session_uid))) and said() == ["fit.changed"], said())
    check("a fit that did not find the body changes nothing",
          fit_ended(ended(result=types.SimpleNamespace(outcome="notOnBody"))) and said() == ["fit.done.not-on-body"]
          and np.allclose(positions(tee), shape), said())
    check("a fit of a shape that changed since the upload is not applied",
          fit_ended(ended(upload=types.SimpleNamespace(digest="0" * 64))) and said() == ["fit.changed"]
          and np.allclose(positions(tee), shape), said())
    layer = bpy.context.view_layer
    layer.objects.active = tee
    bpy.ops.object.mode_set(mode="EDIT")
    check("a fit waits while the garment is in Edit Mode", fit_ended(ended()) is False)
    bpy.ops.object.mode_set(mode="OBJECT")
    ui_garment.RUNTIME.fit_lines = []
    check("the refusals left the garment as it was", np.allclose(positions(tee), shape) and not tee.get("dct_fitted"))

    # While Prepare Garment or Combine Materials runs from the panel, the other garment tools wait for it.
    ui_garment.RUNTIME.stepping = "garment.op.prepare"
    check("the garment tools wait while Prepare Garment runs",
          refused(bpy.ops.dct_link.fit_push_out, "is running") and refused(bpy.ops.dct_link.fit_align, "is running"))
    ui_garment.RUNTIME.stepping = None

    # The fit check and the problem colours; the neck of the synthetic tee sits inside the head.
    check("Run Fit Check runs", "FINISHED" in bpy.ops.dct_link.fit_check())
    report = garment.FitReport.from_json(tee.get(gh.FIT_REPORT, ""))
    rows = {row.region: row for row in report.rows} if report else {}
    check("the fit check measures the regions in millimetres",
          report is not None and {"chest", "back", "shoulders", "upper_arms"} <= set(rows)
          and 5.0 < rows["chest"].p50 < 40.0 and report.inside > 0,
          report)
    pump(addon, lambda: ui_garment.usual_ranges(bpy.context)[0] is not None, timeout=30, what="the usual ranges")
    log = draw_everything(package, state, "fit check with the usual ranges")
    labels = " ".join(entry[1] for entry in log if entry[0] == "label")
    check("the fit check compares with game clothing from gta.clothing",
          "Usual" in labels and "19 (5 to 32)" in labels, labels[-600:])
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
    before_push = positions(tee)
    check("Push Out of Body runs", "FINISHED" in bpy.ops.dct_link.fit_push_out())
    pushed = np.linalg.norm(positions(tee) - before_push, axis=1).max()
    check("no vertex moves further than the deepest push to the gap", pushed <= garment.MAX_PUSH
          + props.push_gap / 1000.0 + 1e-5, pushed)
    check("a change makes the fit check stale", not tee.get("dct_checked") and not tee.get(gh.FIT_REPORT))
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
    check("the garment holds its backups itself (no fake users)",
          all(not mesh.use_fake_user for mesh in gh.backups(tee)) and tee.get(gh.BACKUP_SLOTS[0]) is not None)
    relaxed = positions(tee)
    check("Back One Step runs", "FINISHED" in bpy.ops.dct_link.fit_back_step())
    check("Back One Step puts back the shape from before the last step",
          np.abs(positions(tee) - relaxed).max() > 1e-5 and len(gh.backups(tee)) == gh.MAX_BACKUPS - 1)

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
    # A garment whose origin is off the ped's centre is shifted onto it for Mirror X; Cancel puts it back exactly.
    tee.data.transform(Matrix.Translation((-0.2, 0.0, 0.0)))
    tee.location.x += 0.2
    bpy.context.view_layer.update()
    shape = positions(tee)
    props.sculpt_mirror = True
    check("Start Sculpting runs on a garment with its origin off the centre",
          "FINISHED" in bpy.ops.dct_link.fit_sculpt_start())
    bpy.ops.object.mode_set(mode="OBJECT")
    check("Cancel puts an off-centre garment back where it was, origin and all",
          "FINISHED" in bpy.ops.dct_link.fit_sculpt_cancel() and np.abs(positions(tee) - shape).max() < 1e-5
          and abs(tee.location.x - 0.2) < 1e-6, (np.abs(positions(tee) - shape).max(), tee.location.x))
    tee.data.transform(Matrix.Translation((0.2, 0.0, 0.0)))
    tee.location.x -= 0.2
    bpy.context.view_layer.update()
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

    # T-pose to A-pose on a garment made in T-pose (its panels unwelded): the arms go onto the body's, and no seam opens.
    tpose = panel_garment("smoke_tpose", "long", 0.0, maps=True)
    for obj in bpy.context.view_layer.objects:
        obj.select_set(obj == tpose)
    bpy.context.view_layer.objects.active = tpose
    check("Use Selected Garment runs", "FINISHED" in bpy.ops.dct_link.fit_use_garment())
    props.category = "long_sleeve"
    props.source_pose = "t_pose"
    bpy.ops.dct_link.fit_auto_markers()
    props.arm_angle = math.radians(40.0)
    reach = positions(tpose)[:, 0].max()
    seams = garment.seam_pairs(positions(tpose), 0.0005, gh.boundary_vertices(tpose.data))
    check("T-pose to A-pose runs", "FINISHED" in bpy.ops.dct_link.fit_tpose_to_apose())
    after = gh.read_markers(scene)
    opened = np.linalg.norm(positions(tpose)[seams[:, 0]] - positions(tpose)[seams[:, 1]], axis=1).max() \
        if len(seams) else 0.0
    check("T-pose to A-pose lowers the arms and the markers onto the body's arms without opening a seam",
          abs(garment.arm_angle(after, "l") - 45.0) < 2.0 and abs(garment.arm_angle(after, "r") - 45.0) < 2.0
          and positions(tpose)[:, 0].max() < reach - 0.05 and props.source_pose == "a_pose"
          and len(seams) > 0 and opened < 0.0005
          and not any(o.name.startswith(gh.TEMP_PREFIX) for o in bpy.data.objects)
          and not any(g.name.startswith(gh.TEMP_PREFIX) for g in tpose.vertex_groups),
          (garment.arm_angle(after, "l"), reach, positions(tpose)[:, 0].max(), len(seams), opened))
    RESULT_TPOSE = {"check": "tears (T-pose to A-pose, unwelded)", "ok": True,
                    "detail": f"{len(seams)} seam pairs, widest gap after the turn {opened * 1000:.3f} mm"}

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
    check("the tear check poses the garment, finds the seams that open and names the pose it skipped",
          tears is not None and len(tears["poses"]) == 4 and tears["skipped"] == 1 and tears["pairs"] > 0
          and torn.get("garment.pose.arms-up", 0) > 0 and tpose.vertex_groups.get(gh.TEARS_GROUP) is not None,
          tears)
    RESULT2 = {"check": "tears (synthetic, unwelded)", "ok": True,
               "detail": "; ".join(f"{p['pose']}: {p['torn']} torn, {p['gap']} mm" for p in tears["poses"]
                                   if not p.get("skipped"))}
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
          and mesh.uv_layers.get("DCT Source UV") is not None and notice.message.fields["cut"] >= 1
          and notice.message.fields["density"] > 0, notice)
    baked = np.empty(2048 * 2048 * 4, dtype=np.float32)
    image.pixels.foreach_get(baked)
    check("the baked texture holds the fabrics' colours", float(baked.reshape(-1, 4)[:, 0].max()) > 0.5)
    shader = next(n for n in material.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    alpha = baked.reshape(-1, 4)[:, 3]
    check("Combine Materials keeps the see-through fabric in the alpha and bakes the normal map",
          shader.inputs["Alpha"].is_linked and shader.inputs["Normal"].is_linked
          and float(alpha.min()) < 0.75 and float(alpha.max()) > 0.95
          and bpy.data.images.get("smoke_tpose_normal") is not None, (float(alpha.min()), float(alpha.max())))
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

    results = [RESULT, RESULT_TPOSE, RESULT2, RESULT3, RESULT4]
    if dct is not None:
        results.append(add_to_dct(package, addon, state, ctrl, dct, check, refused, pump, draw_everything, tpose,
                                  real))
        results.append(add_one_material(package, addon, state, ctrl, dct, check, pump, folder, real))
    results.append(types_smoke(package, addon, state, ctrl, dct, check, refused, pump, draw_everything, real))

    # Nothing else in the scene changed.
    check("the user's other objects are untouched", np.abs(positions(users_cube) - users_shape).max() == 0
          and users_cube.name == "users_cube")
    scene.dct_link.workspace = "CLOTHING"
    log = draw_everything(package, state, "linked cloth again")
    check("Linked Cloth hides Garment Fitting", not any(entry[0] == "operator" and entry[1].startswith("dct_link.fit_")
                                                        for entry in log))
    return results


def choose(obj):
    for other in bpy.context.view_layer.objects:
        other.select_set(other == obj)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.dct_link.fit_use_garment()


def uv_by_position(obj, scale=0.7):
    mesh = obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)
    uv = bm.loops.layers.uv.new("UVMap")
    for face in bm.faces:
        for loop in face.loops:
            loop[uv].uv = (loop.vert.co.x * scale + 0.5, loop.vert.co.z * scale + 0.5)
    bm.to_mesh(mesh)
    bm.free()


def tube(name, levels, radius, segments=32):
    """A tube around the Z axis: a ring of ``segments`` points at each level, ``radius(z)`` wide."""
    builder = synthetic._Builder()
    builder.tube(np.column_stack([np.zeros(len(levels)), np.zeros(len(levels)), levels]),
                 np.array([(radius(z), radius(z) * 0.75) for z in levels]), np.array([1.0, 0, 0]),
                 np.array([0, 1.0, 0]), segments=segments)
    return mesh_object(name, builder.mesh({}))


def types_smoke(package, addon, state, ctrl, dct, check, refused, pump, draw_everything, real):
    """The garment types: the picker and what a type sets, each garment keeping its own; an open jacket whose fronts
    Prepare never joins; a skirt's thigh weights bridged across the legs; a dress split at its waist; a mask aligned
    from Marvelous Designer's Manne avatar; Combine Materials on a thick export whose side walls have no room in the UV
    map; and a hat snapped to its anchor and added as a prop."""
    ui_garment = sys.modules[package + ".ui_garment"]
    gh = sys.modules[package + ".garment_host"]
    gdct = sys.modules[package + ".garment_dct"]
    host = sys.modules[package + ".host"]
    garment = sys.modules[package + ".garment"]
    scene = bpy.context.scene
    props = scene.dct_garment
    props.gender = "male"

    # The picker: a type sets its usual slot, its skin and its front; each garment keeps its own.
    jacket = mesh_object("smoke_open_jacket", synthetic.top("long", 45.0))
    choose(jacket)
    props.category = "open_jacket"
    check("a type sets its slot and front", props.slot == "jbib" and props.open_front and not props.skin)
    log = draw_everything(package, state, "garment type picker")
    labels = " ".join(entry[1] for entry in log if entry[0] == "label")
    check("Setup shows the type with its description and hint",
          ("prop", "category") in log and "worn open" in labels and "never joins the two fronts" in labels,
          labels[labels.find("Garment Type"):][:400])
    watch = mesh_object("smoke_watch", synthetic.pants())
    choose(watch)
    props.category = "watch"
    props.slot = "p_rwrist"
    check("a watch is a prop on a wrist, never showing skin", props.slot == "p_rwrist" and not props.skin)
    choose(jacket)
    check("each garment keeps its own type and slot", props.category == "open_jacket" and props.slot == "jbib")
    # What the user changed on a garment stays with it, and a garment without an avatar never takes another's.
    props.open_front, props.skin, props.avatar = False, True, "manne"
    choose(watch)
    check("the watch kept its right wrist and its own avatar", props.category == "watch"
          and props.slot == "p_rwrist" and props.avatar == "detect", (props.category, props.slot, props.avatar))
    choose(jacket)
    check("the jacket kept its front, skin and avatar", not props.open_front and props.skin and props.avatar == "manne",
          (props.open_front, props.skin, props.avatar))
    props.open_front, props.skin, props.avatar = True, False, "detect"
    choose(watch)
    bpy.data.objects.remove(watch)
    props.category = "shorts"
    check("shorts show skin", props.skin and props.slot == "lowr")

    # An open jacket: its two fronts meet at the centre front and are never joined.
    choose(jacket)
    props.category = "open_jacket"
    bm = bmesh.new()
    bm.from_mesh(jacket.data)
    centre = [e for e in bm.edges if all(abs(v.co.x) < 1e-6 and v.co.y < 0 for v in e.verts)]
    bmesh.ops.split_edges(bm, edges=centre)
    bm.to_mesh(jacket.data)
    bm.free()
    uv_by_position(jacket)
    front_before = int((np.abs(positions(jacket)[:, 0]) < 1e-6).sum())
    check("Prepare Garment runs on the open jacket", "FINISHED" in bpy.ops.dct_link.fit_prepare())
    front = positions(jacket)
    opening = int(((np.abs(front[:, 0]) < 1e-4) & (front[:, 1] < 0)).sum())
    check("the open jacket's two fronts stay apart", front_before > 0 and opening >= 2 * len(centre) - 4,
          (front_before, opening, len(centre)))

    # A skirt: its thigh weights are bridged across the legs, so it does not split between them.
    skirt = tube("smoke_skirt", np.linspace(-0.55, 0.05, 16), lambda z: 0.17 + 0.25 * max(0.0, -z) ** 1.2)
    for name in ("SKEL_Pelvis", "SKEL_L_Thigh", "SKEL_R_Thigh"):
        skirt.vertex_groups.new(name=name)
    for vertex in skirt.data.vertices:
        if vertex.co.z > -0.05:
            skirt.vertex_groups["SKEL_Pelvis"].add([vertex.index], 1.0, "REPLACE")
        else:
            side = "SKEL_L_Thigh" if vertex.co.x >= 0 else "SKEL_R_Thigh"
            skirt.vertex_groups[side].add([vertex.index], 1.0, "REPLACE")
    choose(skirt)
    props.category = "skirt"
    check("Bridge Thigh Weights runs", "FINISHED" in bpy.ops.dct_link.fit_bridge())
    middle = [v for v in skirt.data.vertices if abs(v.co.x) < 1e-4 and v.co.y < 0 and v.co.z < -0.3][0]
    weights = {skirt.vertex_groups[g.group].name: g.weight for g in middle.groups if g.weight > 1e-4}
    check("the middle of the skirt follows both thighs", abs(weights.get("SKEL_L_Thigh", 0) - 0.5) < 0.05
          and abs(weights.get("SKEL_R_Thigh", 0) - 0.5) < 0.05, weights)

    # A dress, split at its waist into a top and a skirt for the Legs slot.
    dress = tube("smoke_dress", np.linspace(-0.6, 0.5, 34), lambda z: 0.12 + 0.6 * (z - 0.14) ** 2)
    choose(dress)
    props.category = "dress"
    check("Split at Waist runs", "FINISHED" in bpy.ops.dct_link.fit_split_waist())
    lower = bpy.data.objects.get("smoke_dress Skirt")
    top, bottom = positions(dress), positions(lower) if lower is not None else np.zeros((1, 3))
    check("the dress keeps its top and a new skirt garment goes to the Legs slot",
          lower is not None and lower.get(gh.TYPE_TAG) == "skirt" and lower.get(gh.SLOT_TAG) == "lowr"
          and abs(top[:, 2].min() - bottom[:, 2].max()) < 0.03 and 0.0 < top[:, 2].min() < 0.3,
          (top[:, 2].min(), bottom[:, 2].max()))

    # A mask made on Marvelous Designer's Manne avatar: its head marker comes from the avatar, Align moves it.
    avatar_head = np.array([0.0, -0.0046, 0.7309])
    mask = tube("smoke_mask", np.linspace(-0.06, 0.08, 8), lambda z: 0.095)
    mask.location = tuple(avatar_head)
    bpy.context.view_layer.update()
    gh.apply_transform(mask)
    choose(mask)
    props.category = "mask"
    props.avatar = "manne"
    check("Auto Markers places the mask's head marker from the avatar",
          "FINISHED" in bpy.ops.dct_link.fit_auto_markers()
          and np.allclose(gh.read_markers(scene)["head"], avatar_head, atol=1e-4), gh.read_markers(scene))
    before = positions(mask).mean(axis=0)
    check("Align to Body runs on the mask", "FINISHED" in bpy.ops.dct_link.fit_align())
    head = np.asarray(ui_garment.joints(bpy.context)[0]["SKEL_Head"])
    check("the mask moved onto the body's head joint as it is",
          np.allclose(positions(mask).mean(axis=0) - before, head - avatar_head, atol=1e-3)
          and gh.aligned(mask, scene), (positions(mask).mean(axis=0) - before, head - avatar_head))
    props.avatar = "detect"

    # A thick export: two sides of a panel share their UVs, and the side walls between them lie on a line.
    thick = bpy.data.meshes.new("smoke_thick")
    grid = [(x, 0.0, z) for z in np.linspace(-0.2, 0.3, 11) for x in np.linspace(-0.15, 0.15, 7)]
    back = [(x, 0.004, z) for x, _, z in grid]
    faces = [(r * 7 + c, r * 7 + c + 1, (r + 1) * 7 + c + 1, (r + 1) * 7 + c) for r in range(10) for c in range(6)]
    wall_start = len(grid) * 2
    wall = [(x, y, -0.2) for x in np.linspace(-0.15, 0.15, 7) for y in (0.0, 0.004)]
    thick.from_pydata(grid + back + wall, [], faces + [tuple(i + len(grid) for i in reversed(f)) for f in faces]
                      + [(wall_start + 2 * c, wall_start + 2 * c + 2, wall_start + 2 * c + 3, wall_start + 2 * c + 1)
                         for c in range(6)])
    slab = bpy.data.objects.new("smoke_thick", thick)
    scene.collection.objects.link(slab)
    bm = bmesh.new()
    bm.from_mesh(thick)
    uv = bm.loops.layers.uv.new("UVMap")
    for face in bm.faces:
        for loop in face.loops:
            co = loop.vert.co
            # The walls are mapped onto the panel's lower edge, a line without area.
            loop[uv].uv = (co.x + 0.5, 0.3 if face.index >= 120 else co.z + 0.5)
    bm.to_mesh(thick)
    bm.free()
    thick.materials.append(textured_material("smoke_thick_fabric", (0.6, 0.4, 0.2)))
    choose(slab)
    props.category = "tshirt"
    check("Combine Materials runs on the thick export", "FINISHED" in bpy.ops.dct_link.fit_combine_materials())
    notice = ui_garment.RUNTIME.notice
    packed = gh.read_uv(thick, gh.PACKED_UV)
    check("the walls take the panel edge's colour and the panel fills the texture",
          notice is not None and notice.message.key == "garment.done.combine-walls"
          and notice.message.fields["walls"] == 6 and notice.message.fields["used"] > 30
          and packed.min() >= 0 and packed.max() <= 1, notice)

    # A hat: snapped to its anchor on the body, never fitted, and added as a prop that hangs from its anchor.
    hat = tube("smoke_hat", np.linspace(0.0, 0.12, 8), lambda z: 0.085 - 0.2 * max(0.0, z - 0.08))
    hat.location = (0.3, 0.2, 1.5)
    bpy.context.view_layer.update()
    gh.apply_transform(hat)
    uv_by_position(hat, 2.0)
    hat.data.materials.append(textured_material("smoke_hat_felt", (0.2, 0.2, 0.2)))
    choose(hat)
    props.category = "hat"
    check("a hat is a prop on the head", props.slot == "p_head" and not props.skin)
    check("the hat waits for Snap to Anchor", ui_garment.next_operator(bpy.context) == "dct_link.fit_snap_anchor")
    check("Snap to Anchor runs", "FINISHED" in bpy.ops.dct_link.fit_snap_anchor())
    placed = positions(hat)
    check("the hat sits on the head", abs(placed[:, 0].mean()) < 0.02 and abs(placed[:, 1].mean()) < 0.02
          and 0.55 < placed[:, 2].min() < 0.8 and gh.aligned(hat, scene),
          (placed.mean(axis=0).round(3).tolist(), round(float(placed[:, 2].min()), 3), gh.aligned(hat, scene)))
    check("a prop is not pushed out of the body", refused(bpy.ops.dct_link.fit_push_out, "keep their own shape"))
    check("a prop is not fitted on gta.clothing", refused(bpy.ops.dct_link.fit_service_fit, "not fitted"))
    check("a prop goes onto no skeleton", refused(bpy.ops.dct_link.fit_use_skeleton, "anchor"))
    check("Validate needs no weights for a prop", "FINISHED" in bpy.ops.dct_link.fit_validate()
          and not any(f.code == "no-weights" for f in garment.findings_from_json(hat.get(gh.FINDINGS, ""))),
          hat.get(gh.FINDINGS))
    log = draw_everything(package, state, "garment prop")
    labels = " ".join(entry[1] for entry in log if entry[0] == "label")
    check("the panels show the anchor instead of markers and weights", ("operator", "dct_link.fit_snap_anchor") in log
          and ("operator", "dct_link.fit_service_weights") not in log and "Anchor" in labels, labels[-500:])
    detail = "no add (no Durty Cloth Tool)"
    if dct is not None:
        pump(addon, lambda: ctrl.ready and ctrl.project is not None, timeout=60, what="the link before the hat")
        adds = len(dct.item_adds)
        props.item_name = "Smoke Hat"
        dct.add_result = {"ok": True, "binding": dict(ADDED_BINDING_HAT), "findings": []}
        check("the hat is added", "FINISHED" in bpy.ops.dct_link.fit_add_to_dct())
        pump(addon, lambda: ui_garment.job_tick() is None and ui_garment.RUNTIME.add_job is None, timeout=60,
             what="the hat's add")
        pump(addon, lambda: len(dct.item_adds) > adds and not ctrl.item_add.adding, timeout=30, what="the hat's answer")
        header, files = dct.item_adds[-1]
        model = bytes(files[0][1])
        rig = gdct.prop_rig_of(hat)
        anchor = np.array(rig.armature.matrix_world) if rig is not None else np.eye(4)
        check("the hat goes in as a head prop without skin or skeleton, hanging from its anchor",
              header["drawableType"] == "p_head" and header["skin"] is False and b"<Skeleton" not in model
              and rig is not None and hat.parent == rig.armature
              and not any(m.type == "ARMATURE" for m in hat.modifiers)
              and np.allclose(anchor[:3, 3], synthetic.joints_of()["SKEL_Head"], atol=1e-4)
              and hat.get(gdct.ADDED) == "Smoke Hat", (header, ui_garment.RUNTIME.notice))
        if real:
            import re

            centre = re.search(rb'<BoundingSphereCenter x="([-\d.e]+)" y="([-\d.e]+)" z="([-\d.e]+)"', model)
            local = np.array([float(v) for v in centre.groups()]) if centre else np.full(3, 9.0)
            check("the real Sollumz exported the hat rigid and around its anchor",
                  b"<BlendWeights" not in model and float(np.linalg.norm(local)) < 0.3, local.tolist())
            # A turned anchor with Sollumz's own Apply Parent Transforms preference on (Sollumz reads the preference,
            # not the export's settings): the hat still leaves relative to its anchor, and the anchor stays turned.
            preferences = host._sollumz_addon().preferences.export_settings
            preference = preferences.apply_transforms
            stood = rig.root.matrix_world.copy()
            turned = stood @ Matrix.Rotation(0.6, 4, "X") @ Matrix.Rotation(0.4, 4, "Z")
            rig.root.matrix_world = turned
            bpy.context.view_layer.update()
            try:
                preferences.apply_transforms = True
                with tempfile.TemporaryDirectory() as folder:
                    turned_model = gdct.export_garment(rig, pathlib.Path(folder)).model[1]
            finally:
                preferences.apply_transforms = preference
            kept = np.allclose(np.array(rig.root.matrix_world), np.array(turned), atol=1e-6)
            rig.root.matrix_world = stood
            bpy.context.view_layer.update()
            centre = re.search(rb'<BoundingSphereCenter x="([-\d.e]+)" y="([-\d.e]+)" z="([-\d.e]+)"', turned_model)
            again = np.array([float(v) for v in centre.groups()]) if centre else np.full(3, 9.0)
            check("a turned anchor exports the hat the same with Apply Parent Transforms on",
                  kept and np.allclose(again, local, atol=1e-4), (again.tolist(), local.tolist(), kept))
        detail = f"{header['drawableType']}, {len(model)} bytes of XML"
    return {"check": "garment types (" + ("real Sollumz" if real else "stand-in") + ")", "ok": True, "detail": detail}


ADDED_BINDING_HAT = {"clothId": "9c0d1e2f-3a4b-4c5d-8e6f-7a8b9c0d1e2f", "textureId": "0d1e2f3a-4b5c-4d6e-9f7a-8b9c0d1e2f3a"}


def add_one_material(package, addon, state, ctrl, dct, check, pump, folder, real):
    """A garment with one material (no Combine Materials) whose levels of detail were made first: Sollumz renames only
    the High mesh's UV map, so the add names each level's maps as High's are named and no level exports without UVs."""
    ui_garment = sys.modules[package + ".ui_garment"]
    gh = sys.modules[package + ".garment_host"]
    scene = bpy.context.scene
    props = scene.dct_garment
    shirt = mesh_object("smoke_shirt", synthetic.top("short", 45.0))
    mesh = shirt.data
    mesh.materials.append(textured_material("smoke_shirt_fabric", (0.3, 0.7, 0.3)))
    bm = bmesh.new()
    bm.from_mesh(mesh)
    uv = bm.loops.layers.uv.new("UVMap")
    for face in bm.faces:
        for loop in face.loops:
            loop[uv].uv = (loop.vert.co.x * 0.7 + 0.5, loop.vert.co.z * 0.7 + 0.35)
    bm.to_mesh(mesh)
    bm.free()
    for name, side in (("SKEL_Spine3", 0), ("SKEL_L_UpperArm", 1), ("SKEL_R_UpperArm", -1)):
        group = shirt.vertex_groups.new(name=name)
        chosen = [v.index for v in mesh.vertices if (side == 0 and abs(v.co.x) <= 0.17)
                  or (side and v.co.x * side > 0.17)]
        group.add(chosen, 1.0, "REPLACE")
    for obj in bpy.context.view_layer.objects:
        obj.select_set(obj == shirt)
    bpy.context.view_layer.objects.active = shirt
    bpy.ops.dct_link.fit_use_garment()
    check("choosing another garment starts its add afresh", props.item_name == "smoke_shirt" and not props.variations)
    props.slot, props.gender, props.item_name = "jbib", "female", "Smoke Shirt"
    props.lod_medium, props.lod_low = 300, 100
    check("Generate LODs runs on the one-material shirt", "FINISHED" in bpy.ops.dct_link.fit_lods())
    adds = len(dct.item_adds)
    dct.add_result = {"ok": True, "binding": dict(ADDED_BINDING_SHIRT), "findings": []}
    check("the one-material shirt is added", "FINISHED" in bpy.ops.dct_link.fit_add_to_dct())
    pump(addon, lambda: ui_garment.job_tick() is None and ui_garment.RUNTIME.add_job is None, timeout=60,
         what="the shirt's add")
    pump(addon, lambda: len(dct.item_adds) > adds and not ctrl.item_add.adding, timeout=30, what="the shirt's answer")
    levels = [m for _, m in gh.lod_meshes(shirt)]
    names = [layer.name for layer in mesh.uv_layers]

    def spread(lod):
        values = np.empty(len(lod.loops) * 2, dtype=np.float32)
        lod.uv_layers[names[0]].data.foreach_get("uv", values)
        return float(np.ptp(values)) if len(values) else 0.0

    check("every level of detail names its UV maps as High does and keeps its UVs",
          len(levels) == 2 and names[0] == "UVMap 0"
          and all([layer.name for layer in lod.uv_layers][:1] == names[:1] and spread(lod) > 0.1 for lod in levels),
          (names, [[layer.name for layer in lod.uv_layers] for lod in levels]))
    model = bytes(dct.item_adds[-1][1][0][1])
    if real:
        check("the real Sollumz exported the shirt's levels of detail", b"<DrawableModelsMedium>" in model
              and b"<DrawableModelsLow>" in model)
    return {"check": "add one-material garment with LODs (" + ("real Sollumz" if real else "stand-in") + ")",
            "ok": True, "detail": f"High UV maps {names}, levels {[[l.name for l in lod.uv_layers] for lod in levels]}"}


ADDED_BINDING_SHIRT = {"clothId": "7a8b9c0d-1e2f-4a3b-8c4d-5e6f7a8b9c0d", "textureId": "8b9c0d1e-2f3a-4b4c-9d5e-6f7a8b9c0d1e"}


def png_size(data):
    """The width and height in a PNG's header (the full pictures are checked by the pytest suite)."""
    assert bytes(data[:8]) == b"\x89PNG\r\n\x1a\n" and bytes(data[12:16]) == b"IHDR"
    return int.from_bytes(bytes(data[16:20]), "big"), int.from_bytes(bytes(data[20:24]), "big")


def variation_image(name, size, rgb):
    image = bpy.data.images.new(name, size, size)
    pixels = np.tile(np.array([*rgb, 1.0], dtype=np.float32), size * size)
    image.pixels.foreach_set(pixels)
    image.pack()
    return image


def add_to_dct(package, addon, state, ctrl, dct, check, refused, pump, draw_everything, coat, real):
    """Adding the game-ready coat to the project open in the fake Durty Cloth Tool: the skeleton template, the checks,
    an empty export refused, the add with a second colour variation, Cancel while Durty Cloth Tool asks, the free
    limit, and Push Model on the added cloth."""
    ui_garment = sys.modules[package + ".ui_garment"]
    gdct = sys.modules[package + ".garment_dct"]
    gh = sys.modules[package + ".garment_host"]
    host = sys.modules[package + ".host"]
    from tests.support.fake_dct import ADDED_BINDING
    from tests.blender.sollumz_stub import STUB

    scene = bpy.context.scene
    props = scene.dct_garment
    bones_128 = synthetic.skeleton_bones_128()
    dct.skeleton_files = {gender: [(synthetic.skeleton_template_file(gender),
                                    synthetic.skeleton_template_xml(gender, bones_128))]
                          for gender in ("male", "female")}
    ctrl.skeletons.forget()
    props.gender = "female"
    props.slot = "jbib"
    props.item_name = "Smoke Coat"
    old_rig = coat.parent

    # The bakes above kept Blender busy for longer than the link's keepalive: like the panel's timer in a real
    # session, let the link notice and connect again before the next request.
    import time

    end = time.monotonic() + 1.0
    while time.monotonic() < end:
        addon.tick()
        time.sleep(0.01)
    pump(addon, lambda: ctrl.ready and ctrl.project is not None, timeout=60, what="the link after the long steps")

    def finish_job(what):
        pump(addon, lambda: ui_garment.job_tick() is None and ui_garment.RUNTIME.add_job is None, timeout=60,
             what=what)

    def add(what):
        """Add to Project, and the add's own job until it has sent the add or stopped."""
        result = bpy.ops.dct_link.fit_add_to_dct()
        finish_job(what)
        return result

    log = draw_everything(package, state, "garment ready to add")
    labels = " ".join(entry[1] for entry in log if entry[0] == "label")
    check("Add to Project offers the add with its name and variations, Game Ready the skeleton",
          "Add to Project" in labels and ("operator", "dct_link.fit_add_to_dct") in log
          and ("operator", "dct_link.fit_use_skeleton") in log and ("prop", "item_name") in log
          and ("prop", "first_title") in log and "not on the Durty Cloth Tool skeleton" in labels, labels[-600:])

    # Durty Cloth Tool without the game files: the skeleton is refused, and the panel says what to do.
    dct.fail["skeleton.template"] = "game-required"
    check("Use Durty Cloth Tool Skeleton runs", "FINISHED" in bpy.ops.dct_link.fit_use_skeleton())
    finish_job("the refused skeleton")
    notice = ui_garment.RUNTIME.notice
    check("a refused skeleton says to set up the game in Durty Cloth Tool",
          notice is not None and notice.message.key == "add.skeleton.game-required" and gdct.skeleton_of(coat) is None,
          notice)
    del dct.fail["skeleton.template"]

    # The skeleton: imported with Sollumz, checked, the coat parented to it with its weights kept.
    groups_before = sorted(g.name for g in coat.vertex_groups)
    check("Use Durty Cloth Tool Skeleton runs again", "FINISHED" in bpy.ops.dct_link.fit_use_skeleton())
    finish_job("the skeleton")
    skeleton = gdct.skeleton_of(coat)
    bones = [b.name for b in skeleton.armature.data.bones] if skeleton else []
    modifiers = [m for m in coat.modifiers if m.type == "ARMATURE"]
    check("the coat sits on the female Durty Cloth Tool skeleton, all 128 bones in the game's order",
          skeleton is not None and skeleton.gender == "female" and bones == [n for n, _, _ in bones_128]
          and coat.parent == skeleton.armature and modifiers and modifiers[0].object == skeleton.armature
          and coat.sollum_type == "sollumz_drawable_model"
          and sorted(g.name for g in coat.vertex_groups) == groups_before
          and skeleton.root.sollum_type == "sollumz_drawable_dictionary" and skeleton.root.name != skeleton.armature.name
          and old_rig is not None and old_rig.name in bpy.data.objects, (ui_garment.RUNTIME.notice, bones[:4]))
    check("the template arrived once", dct.templates_sent.count("female") == 1)  # the refusal sends none
    log = draw_everything(package, state, "garment on the skeleton")
    labels = " ".join(entry[1] for entry in log if entry[0] == "label")
    check("the panel shows the skeleton and the next step", "On the Female Durty Cloth Tool skeleton" in labels
          and "Next: Add to Project" in labels, labels[labels.find("Garment Fitting"):][:300]
          + " ... " + labels[labels.find("Freemode Skeleton"):][:300])

    # What blocks the add is listed before anything is sent.
    stray = coat.vertex_groups.new(name="Group")
    props.variations.add()
    check("an add with problems is refused", refused(bpy.ops.dct_link.fit_add_to_dct, "blocked"))
    keys = [p.key for p in ui_garment.RUNTIME.add_problems]
    check("the add lists a vertex group that is no bone and a variation without an image",
          "add.why.unknown-groups" in keys and "add.why.variation-empty" in keys and not dct.item_adds, keys)
    log = draw_everything(package, state, "add problems")
    labels = " ".join(entry[1] for entry in log if entry[0] == "label")
    check("the panel lists what blocks the add", "Fix these first" in labels and "Group" in labels, labels[-500:])
    coat.vertex_groups.remove(stray)
    props.variations[0].image = variation_image("smoke_coat_red", 64, (0.8, 0.1, 0.1))
    check("a picked image names its variation", props.variations[0].title == "smoke_coat_red")

    # Sollumz reports success for an empty dictionary: the add-on reads what it wrote and refuses it.
    if not real:
        STUB["mode"] = "empty"
        old_material = coat.data.materials[0]
        check("an add whose export fails runs", "FINISHED" in add("the failing add"))
        notice = ui_garment.RUNTIME.notice
        check("an empty export is refused after the garment changed, and Ctrl+Z is named",
              notice is not None and notice.message.key == "add.failed-undo"
              and notice.message.fields["problem"].key == "add.export.empty" and not dct.item_adds
              and ui_garment.RUNTIME.add_job is None, notice)
        check("the garment's old material stays in the file with it",
              coat.get(gdct.SOURCE_MATERIAL) == old_material and old_material.users > 0)
        STUB["mode"] = "ydd"
        check("nothing is sent for an empty export", not dct.item_adds)

    # The add: Durty Cloth Tool adds the cloth and answers with its binding and findings.
    dct.add_result = {"ok": True, "binding": dict(ADDED_BINDING),
                      "findings": [{"code": "non-power-of-two", "severity": "warning"}]}
    check("Add to Project runs", "FINISHED" in add("the add"))
    pump(addon, lambda: not ctrl.item_add.adding, timeout=30, what="the add")
    header, files = dct.item_adds[-1]
    names = [name for name, _ in files]
    model = bytes(files[0][1])
    pictures = {name: png_size(data) for name, data in files if name.endswith(".png")}
    check("the add carries the model without its skeleton, and two variations as PNG",
          header["drawableType"] == "jbib" and header["gender"] == "female" and header["skin"] is False
          and header["name"] == "Smoke Coat" and names[0].endswith(".ydd.xml")
          and b"<DrawableModelsHigh>" in model and b"<Skeleton" not in model
          and [v["name"] for v in header["variations"]] == [coat.data.materials[0].node_tree.nodes[
              "DiffuseSampler"].image.name, "smoke_coat_red"]
          and sorted(pictures.values()) == [(64, 64), (2048, 2048)], (header, names, pictures))
    if real:
        check("the real Sollumz exported the coat with the ped shader", b"ped.sps" in model and b"<Geometries>" in model)
    else:
        call = STUB["calls"][-1]
        check("the export used Exclude Skeleton and face corners", call["exclude_skeleton"] is True
              and call["mesh_domain"] == "FACE_CORNER")
    material = coat.data.materials[0]
    check("the coat has the ped shader with its diffuse on every level of detail",
          material.sollum_type == "sollumz_material_shader" and material.shader_properties.filename == "ped.sps"
          and material.node_tree.nodes["DiffuseSampler"].image is not None
          and all(m.materials[0] == material for m in gdct.lod_meshes(coat))
          and coat.data.uv_layers.get(gh.SOURCE_UV) is not None
          and all(p.use_smooth for p in coat.data.polygons), [l.name for l in coat.data.uv_layers])
    status = ctrl.item_add.status
    check("the added cloth is linked to the Drawable Dictionary for Push Model and Save Model to Cloth",
          status is not None and status.message.key == "add.result.added"
          and host.stored_binding(skeleton.root) == ADDED_BINDING and coat.get(gdct.ADDED) == "Smoke Coat", status)
    check("the backups go once the cloth is in the project", not gh.backups(coat))
    work = pathlib.Path(ctrl.data_dir) / gdct.WORK_FOLDER
    check("the add leaves no files behind", not any(work.iterdir()) if work.is_dir() else True)
    log = draw_everything(package, state, "garment added")
    labels = " ".join(entry[1] for entry in log if entry[0] == "label")
    check("the panel says what was added, with Durty Cloth Tool's checks",
          "Added Smoke Coat to the project as Top (jbib)." in labels and "power of two" in labels
          and "Done: the garment is in your Durty Cloth Tool project" in labels, labels[-700:])

    # Cancel while Durty Cloth Tool's dialog is open withdraws the add.
    dct.hold_adds = True
    adds = len(dct.item_adds)
    check("another add runs", "FINISHED" in add("another add"))
    pump(addon, lambda: len(dct.item_adds) > adds, what="the waiting add")
    log = draw_everything(package, state, "add waiting in DCT")
    check("the waiting add shows its progress and Cancel", ("operator", "dct_link.fit_cancel_add") in log
          and any(entry[0] == "progress" for entry in log))
    check("Cancel runs", "FINISHED" in bpy.ops.dct_link.fit_cancel_add())
    pump(addon, lambda: not ctrl.item_add.adding, what="the withdrawn add")
    check("a withdrawn add changes nothing", ctrl.item_add.status.message.key == "add.result.withdrawn"
          and dct.add_cancels == [dct.item_adds[-1][0]["id"]])
    dct.hold_adds = False

    # Durty Cloth Tool's free limit: Durty Cloth Tool decides, the panel says it plainly.
    dct.fail["item.add"] = "item-limit"
    check("an add over the limit runs", "FINISHED" in add("the add over the limit"))
    pump(addon, lambda: not ctrl.item_add.adding, what="the refused add")
    check("the free limit is explained", ctrl.item_add.status.message.key == "add.result.item-limit")
    del dct.fail["item.add"]

    # Push Model on the added cloth goes to that cloth.
    pushes = len(dct.pushes)
    for obj in bpy.context.view_layer.objects:
        obj.select_set(obj == skeleton.root)
    bpy.context.view_layer.objects.active = skeleton.root
    check("Push Model runs on the added cloth", "FINISHED" in bpy.ops.dct_link.model_push())
    pump(addon, lambda: len(dct.pushes) > pushes and not ctrl.model.pushing, timeout=30, what="the push")
    check("the push names the added cloth", dct.pushes[-1][0].get("binding") == ADDED_BINDING, dct.pushes[-1][0])
    check("the template was kept for every add", dct.templates_sent.count("female") == 1, dct.templates_sent)
    return {"check": "add to Durty Cloth Tool (" + ("real Sollumz" if real else "stand-in") + ")", "ok": True,
            "detail": f"{len(model)} bytes of XML, files {names}"}
