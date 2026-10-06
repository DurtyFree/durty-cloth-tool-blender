# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2026 Schmid Software Solutions (https://schmid-software.de)
"""Custom Ped in Blender, on a synthetic mannequin (no game files) against the fake Durty Cloth Tool: the switch in
the DCT tab, the character's checks and fixes (transforms, an old Mixamo-named rig, centimetres, the facing), the
markers (From Old Rig, Auto Markers, the click guide's rays, mirror, the elbow that follows its arm), the template
list, the rights confirmation, the rig with its progress and Cancel, the refined markers, Apply Rig (the armature with
the rig's exact rest matrices, the weights, the character's own pose), the poses, Run Checks, Rig Again with Previous
Rig and Remove Rig, and Create Custom Ped (the GLB in the rest pose with every bone as a joint, the part roles, the
answer, Cancel).

Called by ``smoke_in_blender.py`` while the add-on is connected to the fake Durty Cloth Tool. Only for use inside
Blender.
"""

from __future__ import annotations

import json
import math
import struct
import sys

import bpy
import numpy as np
from mathutils import Matrix, Vector

from tests.support import fake_dct, mannequin

MIXAMO = {"pelvis": "Hips", "chest": "Spine2", "neck": "Neck", "headTop": "HeadTop_End", "shoulderL": "LeftArm",
          "elbowL": "LeftForeArm", "wristL": "LeftHand", "hipL": "LeftUpLeg", "kneeL": "LeftLeg", "ankleL": "LeftFoot",
          "toeL": "LeftToeBase", "shoulderR": "RightArm", "elbowR": "RightForeArm", "wristR": "RightHand",
          "hipR": "RightUpLeg", "kneeR": "RightLeg", "ankleR": "RightFoot", "toeR": "RightToeBase"}


def labels(log):
    return " ".join(entry[1] for entry in log if entry[0] == "label")


def build_character(collection):
    """The mannequin as a modeller might hand it over: in centimetres, turned to face +X, moved off the origin by its
    objects' locations, and rigged to a Mixamo-named armature."""
    character = mannequin.mannequin(45.0, turn=90.0)
    objects = []
    for part in character.parts:
        mesh = bpy.data.meshes.new(part.name)
        mesh.from_pydata((part.positions * 100.0).tolist(), [], [tuple(face) for face in part.faces])
        mesh.update()
        obj = bpy.data.objects.new(part.name, mesh)
        obj.location = (50.0, 0.0, 0.0)
        collection.objects.link(obj)
        objects.append(obj)
    material = bpy.data.materials.new("M_Hair_Strands")
    objects[2].data.materials.append(material)
    data = bpy.data.armatures.new("mixamo")
    rig = bpy.data.objects.new("mixamo_rig", data)
    bpy.context.scene.collection.objects.link(rig)
    rig.location = (50.0, 0.0, 0.0)
    bpy.context.view_layer.objects.active = rig
    rig.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    head = (np.asarray(character.joints["chin"]) + np.asarray(character.joints["neck"])) / 2
    points = dict(character.joints, head=tuple(head))
    for marker, bone in list(MIXAMO.items()) + [("head", "Head")]:
        edit = data.edit_bones.new("mixamorig:" + bone)
        point = Vector(points[marker]) * 100.0
        edit.head = point
        edit.tail = point + Vector((0.0, 0.0, 5.0))
    bpy.ops.object.mode_set(mode="OBJECT")
    body = objects[0]
    body.parent = rig
    body.matrix_parent_inverse = rig.matrix_world.inverted()  # parented where it stands
    modifier = body.modifiers.new("Armature", "ARMATURE")
    modifier.object = rig
    group = body.vertex_groups.new(name="mixamorig:Hips")
    group.add(list(range(len(body.data.vertices))), 1.0, "REPLACE")
    return character, objects, rig


def rig_shows_pose(rig, bone):
    """Whether a pose other than the character's own is shown on ``bone``."""
    stored = rig.data.bones[bone].get("dct_pose")
    posed = np.array(rig.pose.bones[bone].matrix)
    return stored is not None and not np.allclose(posed, np.asarray(list(stored)).reshape(4, 4), atol=1e-4)


def select_only(objects):
    for obj in bpy.context.view_layer.objects:
        obj.select_set(obj in objects)
    bpy.context.view_layer.objects.active = objects[0]


def glb_json(data: bytes):
    length = struct.unpack_from("<I", data, 12)[0]
    return json.loads(data[20:20 + length].decode("utf-8"))


def quaternion_angle(a, b) -> float:
    """The angle between two rotations given as quaternions (x, y, z, w), robust to float32 noise."""
    a, b = np.asarray(a, dtype=np.float64), np.asarray(b, dtype=np.float64)
    a, b = a / np.linalg.norm(a), b / np.linalg.norm(b)
    if np.dot(a, b) < 0:
        b = -b
    return math.degrees(4 * math.asin(min(1.0, float(np.linalg.norm(a - b)) / 2)))


def run(package, addon, state, ctrl, check, refused, pump, draw_everything, dct):
    ped = sys.modules[package + ".ped"]
    ph = sys.modules[package + ".ped_host"]
    ui_ped = sys.modules[package + ".ui_ped"]
    scene = bpy.context.scene
    props = scene.dct_ped
    results = []

    # The switch: Custom Ped shows its own panel and hides the clothing panels.
    scene.dct_link.workspace = "PED"
    log = draw_everything(package, state, "custom ped, no character")
    check("Custom Ped shows its panel and says how to start",
          "Use Selected" in labels(log) and ("operator", "dct_link.ped_use_selected") in log, labels(log)[:300])
    check("Custom Ped hides the clothing panels",
          not any(entry[0] == "operator" and entry[1].startswith(("dct_link.fit_", "dct_link.live_", "dct_link.model_"))
                  for entry in log))
    check("every Custom Ped operator that changes the character can be undone",
          all("UNDO" in cls.bl_options for cls in ui_ped.CLASSES if getattr(cls, "bl_idname", "").startswith(
              ("dct_link.ped_apply", "dct_link.ped_remove", "dct_link.ped_scale", "dct_link.ped_turn",
               "dct_link.ped_auto", "dct_link.ped_from", "dct_link.ped_mirror", "dct_link.ped_previous"))))

    holder = bpy.data.collections.new("smoke_import")
    scene.collection.children.link(holder)
    character, objects, old_rig = build_character(holder)
    select_only(objects)
    check("Use Selected runs", "FINISHED" in bpy.ops.dct_link.ped_use_selected())
    collection = props.character
    check("the collection that holds exactly the selected meshes became the character",
          collection == holder and set(ph.parts(collection)) == set(objects), collection)
    check("the ped name and model name are suggested", props.ped_name == collection.name
          and ped.model_problem(props.model_name) is None, (props.ped_name, props.model_name))
    rows = {row.code: row for row in ui_ped.character_checks(bpy.context, collection)}
    check("the checks find the transforms, the old rig, the centimetres and the facing",
          {"transforms", "rig", "height", "facing"} <= set(rows) and rows["height"].key == "ped.check.unit"
          and rows["facing"].fields.get("direction") == "ped.direction.screen-right", sorted(rows))
    check("the roles are guessed from the names",
          [ph.role_of(obj) for obj in objects] == ["body", "head", "hair", "eyes"])
    log = draw_everything(package, state, "custom ped, character checks")
    check("each check offers its fix", all(("operator", op) in log for op in (
        "dct_link.ped_apply_transforms", "dct_link.ped_remove_old_rig", "dct_link.ped_scale", "dct_link.ped_turn",
        "dct_link.ped_confirm_facing")))
    check("nothing can be rigged before the checks pass", refused(bpy.ops.dct_link.ped_rig, "Character"))

    check("Apply Transforms runs", "FINISHED" in bpy.ops.dct_link.ped_apply_transforms())
    check("Remove Old Rig runs", "FINISHED" in bpy.ops.dct_link.ped_remove_old_rig())
    body = objects[0]
    check("the old rig is off and its joints are kept",
          body.parent is None and not any(m.type == "ARMATURE" for m in body.modifiers)
          and "mixamorig:Hips" not in body.vertex_groups and old_rig.hide_get()
          and ped.rig_kind(ph.old_joints(collection)) == "mixamo")
    check("Scale (to metres) runs", "FINISHED" in bpy.ops.dct_link.ped_scale(factor=0.01))
    check("Turn 90 degrees right runs", "FINISHED" in bpy.ops.dct_link.ped_turn(axis="Z", degrees=-90.0))
    rows = {row.code: row for row in ui_ped.character_checks(bpy.context, collection)}
    check("the character is 1.8 m tall and its feet point to the front now",
          rows["height"].level == "ok" and rows["facing"].key == "ped.check.facing"
          and abs(ui_ped.facts(bpy.context, collection).facing or 0.0) < 5.0, rows)
    check("It Faces the Front runs", "FINISHED" in bpy.ops.dct_link.ped_confirm_facing())
    check("the checks pass", ped.checks_pass(ui_ped.character_checks(bpy.context, collection)))
    objects[0].vertex_groups.new(name="DCT_user_group")  # a group of the user's own, which no rig takes away

    # Markers.
    check("From Old Rig runs", "FINISHED" in bpy.ops.dct_link.ped_from_rig())
    from_rig = ph.read_markers(collection)
    joints = ph.old_joints(collection)
    check("From Old Rig put the markers on the old rig's joints, moved and scaled with the character",
          len(from_rig) == 19 and np.allclose(from_rig["shoulderL"], joints["mixamorig:LeftArm"], atol=1e-4)
          and from_rig["shoulderL"][0] > from_rig["shoulderR"][0], from_rig.get("shoulderL"))
    positions = np.concatenate([ph.world_positions(obj) for obj in ph.parts(collection)])
    check("the markers are plausible", ped.marker_problems(from_rig, positions) == [],
          ped.marker_problems(from_rig, positions))
    check("Auto Markers runs", "FINISHED" in bpy.ops.dct_link.ped_auto_markers())
    auto = ph.read_markers(collection)
    worst = max(float(np.linalg.norm(np.subtract(auto[n], from_rig[n]))) for n in ped.BODY_MARKERS)
    check("Auto Markers lands near the rig's joints", worst < 0.06, f"{worst * 100:.1f} cm")
    results.append({"check": "auto markers (largest distance to the old rig's joints)", "ok": True,
                    "detail": f"{worst * 100:.1f} cm"})
    # The click guide's rays, as a click in the front view would cast them.
    tree = ph.character_tree(bpy.context, collection)
    guide = ui_ped.Guide(tree, positions)
    for name in ped.GUIDE:
        x, _, z = from_rig[name]
        point = guide.point((x, -5.0, z), (0.0, 1.0, 0.0))
        check(f"the click guide places {name} inside the body", point is not None, name)
        guide.points[name] = point
    derived = ped.derive_markers(guide.points, *ui_ped.character_mesh(bpy.context))
    check("the click guide's points place every marker plausibly", ped.marker_problems(derived, positions) == [],
          ped.marker_problems(derived, positions))
    ui_ped.write_markers(bpy.context, from_rig)
    markers = ph.marker_objects(collection)
    markers["wristR"].location.z += 0.2
    check("Mirror runs", "FINISHED" in bpy.ops.dct_link.ped_mirror(source="L"))
    mirrored = ph.read_markers(collection)
    check("mirror puts the right wrist opposite the left one",
          abs(mirrored["wristR"][2] - mirrored["wristL"][2]) < 1e-5)
    ui_ped.RUNTIME.last_markers[ui_ped.ident(collection)] = ph.read_markers(collection)
    elbow = Vector(mirrored["elbowL"])
    markers["wristL"].location = Vector(mirrored["wristL"]) + Vector((0.05, 0.0, 0.1))
    bpy.context.view_layer.update()
    ui_ped.follow_limbs(scene)
    check("the elbow follows its arm when the wrist moves",
          (Vector(ph.read_markers(collection)["elbowL"]) - elbow).length > 0.01)
    ui_ped.write_markers(bpy.context, from_rig)
    log = draw_everything(package, state, "custom ped, markers placed")
    check("the markers section counts the markers", "19 of 19 placed" in labels(log))

    # The template and the rig.
    check("Refresh (templates) runs", "FINISHED" in bpy.ops.dct_link.ped_refresh_templates())
    pump(addon, lambda: ctrl.peds.templates is not None, what="the template list")
    log = draw_everything(package, state, "custom ped, templates")
    check("the template list is offered with the recommended ones first",
          ("operator", "dct_link.ped_use_template") in log and ("menu", "DCTLINK_MT_ped_templates") in log)
    check("Use Template runs", "FINISHED" in bpy.ops.dct_link.ped_use_template(model="a_m_y_tester_01"))
    check("a rig without the rights confirmation is refused", refused(lambda: bpy.ops.dct_link.ped_rig(agree=False),
                                                                      "rights"))
    dct.ped_rig_seconds = 2.0
    check("Rig in Durty Cloth Tool runs (rights confirmed)", "FINISHED" in bpy.ops.dct_link.ped_rig(agree=True))
    check("the rights confirmation is kept on the character", bool(collection.get(ph.RIGHTS)))
    pump(addon, lambda: ctrl.peds.stage is not None, what="the rig's progress")
    log = draw_everything(package, state, "custom ped, rigging")
    check("the rig shows its progress with Cancel",
          ("operator", "dct_link.ped_cancel_rig") in log and any(e[0] == "progress" for e in log))
    check("Cancel (rig) runs", "FINISHED" in bpy.ops.dct_link.ped_cancel_rig())
    pump(addon, lambda: not ctrl.peds.rigging, what="the cancelled rig")
    check("a cancelled rig leaves the character as it was", ph.armature(collection) is None
          and ctrl.peds.rig is None and ctrl.peds.rig_status.message.key == "ped.error.rig-cancelled")
    dct.ped_rig_seconds = 0.3
    check("Rig again runs", "FINISHED" in bpy.ops.dct_link.ped_rig())
    pump(addon, lambda: ctrl.peds.rig is not None, what="the rig")
    log = draw_everything(package, state, "custom ped, rig waiting")
    check("the rig waits for approval with the moved markers",
          ("operator", "dct_link.ped_apply_rig") in log and ("operator", "dct_link.ped_use_refined") in log
          and "Left Elbow: 2.0 cm" in labels(log), labels(log)[-400:])
    check("Use These Markers runs", "FINISHED" in bpy.ops.dct_link.ped_use_refined())
    check("the markers moved where Durty Cloth Tool put them",
          abs(ph.read_markers(collection)["elbowL"][1] - from_rig["elbowL"][1] - 0.02) < 1e-5)
    before = {obj.name: ph.world_positions(obj) for obj in ph.parts(collection)}
    check("Apply Rig runs", "FINISHED" in bpy.ops.dct_link.ped_apply_rig())
    rig = ph.armature(collection)
    template = fake_dct.ped_skeleton()
    check("the armature has every bone of the template", rig is not None
          and [b.name for b in rig.data.bones] == [b["name"] for b in template])
    worst = 0.0
    for bone, record in zip(rig.data.bones, template):
        expected = np.asarray(record["world"], dtype=np.float64).reshape(4, 4).T
        actual = np.array(bone.matrix_local)
        worst = max(worst, ped.rotation_degrees(expected[:3, :3], actual[:3, :3]))
        check(f"{bone.name} sits where the rig put it", np.allclose(actual[:3, 3], expected[:3, 3], atol=1e-4))
    check("no bone is turned against the rig (0.01 degrees)", worst < 0.01, f"{worst:.5f}")
    results.append({"check": "apply rig (largest bone turn against the rig)", "ok": True, "detail": f"{worst:.5f} deg"})
    bpy.context.view_layer.update()
    after = {obj.name: ph.evaluated_positions(bpy.context, obj) for obj in ph.parts(collection)}
    moved = max(float(np.abs(after[name] - before[name]).max()) for name in before)
    check("the rigged character looks as before in its own pose", moved < 1e-3, moved)
    weights = []
    for vertex in body.data.vertices:
        weights.append(sum(g.weight for g in vertex.groups))
    check("every vertex of the body is weighted in full", min(weights) > 0.99 and max(weights) < 1.01)
    check("the meshes are in the game's rest pose", np.allclose(
        ph.world_positions(body), before[body.name] - (np.asarray(from_rig["pelvis"])
                                                       - np.asarray(template[1]["world"][12:15])), atol=1e-4))
    log = draw_everything(package, state, "custom ped, rigged")
    check("the rig section shows the applied rig", "Rigged from a_m_y_tester_01" in labels(log), labels(log)[-300:])

    # Check.
    check("Pose (Game Rest Pose) runs", "FINISHED" in bpy.ops.dct_link.ped_pose(pose="rest"))
    check("the rest pose shows the meshes unmoved", np.allclose(ph.evaluated_positions(bpy.context, body),
                                                                ph.world_positions(body), atol=1e-5))
    check("Pose (Arms Up) runs", "FINISHED" in bpy.ops.dct_link.ped_pose(pose="arms_up"))
    hand = rig.pose.bones["SKEL_L_Hand"]
    check("Arms Up raises the hands", (rig.matrix_world @ hand.head).z > (rig.matrix_world @ hand.bone.head_local).z + 0.2)
    check("Pose (Your Pose) runs", "FINISHED" in bpy.ops.dct_link.ped_pose(pose="yours"))
    check("Run Checks runs", "FINISHED" in bpy.ops.dct_link.ped_run_checks())
    findings = ui_ped.RUNTIME.findings[ui_ped.ident(collection)]
    check("Run Checks finds nothing Durty Cloth Tool would refuse",
          not [f for f in findings if f.code in ped.REFUSED_CODES] and collection.get(ph.CHECKED) == 1,
          [(f.code, f.count) for f in findings])
    # A moved armature moves every bone the GLB carries: Durty Cloth Tool would refuse it.
    rig.location.x += 0.05
    bpy.context.view_layer.update()
    check("Run Checks (armature moved) runs", "FINISHED" in bpy.ops.dct_link.ped_run_checks())
    moved_rig = {f.code: f for f in ui_ped.RUNTIME.findings[ui_ped.ident(collection)]}
    check("Run Checks says a moved armature is refused", "armature-changed" in moved_rig
          and moved_rig["armature-changed"].count == len(rig.data.bones) and collection.get(ph.CHECKED) == 0,
          sorted(moved_rig))
    rig.location.x -= 0.05
    bpy.context.view_layer.update()
    check("Run Checks (armature back) runs", "FINISHED" in bpy.ops.dct_link.ped_run_checks())
    check("Run Checks passes again", collection.get(ph.CHECKED) == 1)
    log = draw_everything(package, state, "custom ped, checked")
    check("the next step is Send", ("operator", "dct_link.ped_send") in log)

    # Rig again: the applied rig becomes the previous one.
    check("Rig Again runs", "FINISHED" in bpy.ops.dct_link.ped_rig())
    pump(addon, lambda: ctrl.peds.rig is not None, what="the second rig")
    check("Apply Rig (again) runs", "FINISHED" in bpy.ops.dct_link.ped_apply_rig())
    previous = ph.previous_armature(collection)
    check("the rig before is kept as the previous one", previous is not None and previous != ph.armature(collection)
          and previous.hide_get())
    check("Previous Rig runs", "FINISHED" in bpy.ops.dct_link.ped_previous_rig())
    check("the previous rig is back", ph.armature(collection) == previous)

    def fully_weighted():
        return all(0.99 < sum(g.weight for g in v.groups) < 1.01 for obj in ph.parts(collection)
                   for v in obj.data.vertices)

    check("the previous rig keeps its weights", fully_weighted())
    check("Previous Rig (back again) runs", "FINISHED" in bpy.ops.dct_link.ped_previous_rig())
    check("swapping back keeps the weights too", fully_weighted() and ph.armature(collection) != previous)
    check("Previous Rig (once more) runs", "FINISHED" in bpy.ops.dct_link.ped_previous_rig())
    bpy.context.view_layer.update()
    after = {obj.name: ph.evaluated_positions(bpy.context, obj) for obj in ph.parts(collection)}
    check("the character still looks as before", max(float(np.abs(after[n] - before[n]).max()) for n in before) < 1e-3)
    # The rig is read as the character stands, whatever pose is shown.
    standing = ui_ped.character_mesh(bpy.context)[0]
    check("Pose (Squat) runs", "FINISHED" in bpy.ops.dct_link.ped_pose(pose="squat"))
    check("the character is read in its own pose while a test pose shows",
          np.allclose(ui_ped.character_mesh(bpy.context)[0], standing, atol=1e-5))
    check("reading it leaves the test pose showing", rig_shows_pose(ph.armature(collection), "SKEL_L_Thigh"))
    bpy.ops.dct_link.ped_pose(pose="yours")
    check("Remove Rig runs", "FINISHED" in bpy.ops.dct_link.ped_remove_rig())
    check("removing the rig gives back the character from before the first rig, with its own groups",
          ph.armature(collection) is None and ph.previous_armature(collection) is None
          and np.allclose(ph.world_positions(body), before[body.name], atol=1e-5)
          and [g.name for g in body.vertex_groups] == ["DCT_user_group"], [g.name for g in body.vertex_groups])
    check("Rig (after removing) runs", "FINISHED" in bpy.ops.dct_link.ped_rig())
    pump(addon, lambda: ctrl.peds.rig is not None, what="the third rig")
    check("Apply Rig (third) runs", "FINISHED" in bpy.ops.dct_link.ped_apply_rig())

    # Send.
    props.ped_name = "Smoke Hero"
    props.model_name = "a_m_y_smoke"
    check("a model name like the game's own peds is refused", refused(bpy.ops.dct_link.ped_send, "game"))
    props.model_name = "smoke_hero"
    check("Create Custom Ped runs", "FINISHED" in bpy.ops.dct_link.ped_send())
    pump(addon, lambda: not ctrl.peds.sending, what="the custom ped project", timeout=60)
    header, glb = dct.ped_adds[-1]
    check("Durty Cloth Tool created the project", ctrl.peds.created is not None
          and ctrl.peds.created["model"] == "smoke_hero", ctrl.peds.add_status)
    check("the add names the template, the rig, the rights and the part roles",
          header["template"] == "a_m_y_tester_01" and header["rig"] == "j1" and header["rights"] is True
          and {(p["mesh"], p["role"]) for p in header.get("parts", [])} == {("Head", "head"), ("Hair", "hair"),
                                                                             ("Eyes", "eyes")}, header)
    document = glb_json(glb)
    nodes = document["nodes"]
    skin = document["skins"][0]
    joint_names = [nodes[i]["name"] for i in skin["joints"]]
    check("the GLB's joints are the template's bones, every one", sorted(joint_names)
          == sorted(b["name"] for b in template), joint_names[:5])
    check("the GLB holds the four parts, skinned", {nodes[i]["name"] for i, n in enumerate(nodes) if "mesh" in n}
          == {"Body", "Head", "Hair", "Eyes"} and all("skin" in n for n in nodes if "mesh" in n))
    by_name = {b["name"]: b for b in template}
    turned = 0.0
    for index in skin["joints"]:
        node = nodes[index]
        record = by_name[node["name"]]
        if record["parent"] < 0:
            continue  # the root joint carries the axis conversion
        turned = max(turned, quaternion_angle(node.get("rotation", [0, 0, 0, 1]), record["rotation"]))
    check("every joint keeps the template's rest rotation (0.01 degrees)", turned < 0.01, f"{turned:.5f}")
    results.append({"check": "send (largest joint turn against the template)", "ok": True, "detail": f"{turned:.5f} deg"})
    check("the export put the pose back", ph.armature(collection).data.pose_position == "POSE")
    log = draw_everything(package, state, "custom ped, created")
    check("the panel says the project was created, and the character keeps it",
          "created the project" in labels(log) and "Done: Durty Cloth Tool created the project Smoke Hero" in labels(log)
          and json.loads(collection.get(ph.SENT))["model"] == "smoke_hero", labels(log)[-300:])

    dct.hold_ped_adds = True
    check("Create Custom Ped (to cancel) runs", "FINISHED" in bpy.ops.dct_link.ped_send())
    pump(addon, lambda: len(dct.ped_adds) == 2, what="the second upload")
    check("Cancel (send) runs", "FINISHED" in bpy.ops.dct_link.ped_cancel_send())
    pump(addon, lambda: not ctrl.peds.sending, what="the withdrawn add")
    check("a withdrawn add creates nothing", ctrl.peds.add_status.message.key == "ped.send.withdrawn")
    dct.hold_ped_adds = False

    # Undo takes the rig back.
    scene.dct_link.workspace = "CLOTHING"
    log = draw_everything(package, state, "clothing again")
    check("Clothing hides the Custom Ped panel again", not any(e[0] == "operator" and e[1].startswith("dct_link.ped_")
                                                               for e in log))
    for obj in list(collection.all_objects) + [old_rig]:
        bpy.data.objects.remove(obj)
    for child in list(collection.children):
        bpy.data.collections.remove(child)
    bpy.data.collections.remove(collection)
    return results
