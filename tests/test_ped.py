# SPDX-License-Identifier: GPL-3.0-or-later
"""Custom Ped without Blender: markers (the click guide, Auto Markers on a synthetic mannequin, markers from rigs by
their public bone names, mirror, the elbow and knee that follow their limb, the checks), the character checks, part
roles, the rig request's mesh and topology hash, a rig turned into an armature, vertex groups and poses, the test
poses, the local checks, the report, model names and the next-step hint."""

from __future__ import annotations

import json
import math
import pathlib
import re

import numpy as np
import pytest

from durty_cloth_tool_link import ped, strings
from durty_cloth_tool_link.dct_link import ped as dct_ped
from durty_cloth_tool_link.dct_link import protocol
from tests.support import fake_dct, mannequin


def distance(a, b) -> float:
    return float(np.linalg.norm(np.asarray(a, dtype=float) - np.asarray(b, dtype=float)))


# ---- markers ----------------------------------------------------------------------------------------------


def test_the_markers_are_the_protocols():
    assert ped.BODY_MARKERS == protocol.PED_BODY_MARKERS and len(ped.BODY_MARKERS) == 19
    assert set(ped.GUIDE) | set(ped.DERIVED) == set(ped.BODY_MARKERS) and not set(ped.GUIDE) & set(ped.DERIVED)
    assert set(ped.FIGURE) == set(ped.BODY_MARKERS)
    assert all(ped.MIRROR[ped.MIRROR[name]] == name for name in ped.MIRROR)
    # The figure shows the character from the front: its left on the right.
    assert ped.FIGURE["shoulderL"][0] > 0 > ped.FIGURE["shoulderR"][0]


@pytest.mark.parametrize("angle", [45.0, 0.0, 70.0])
def test_auto_markers_find_the_joints_of_a_standing_person(angle):
    character = mannequin.mannequin(angle)
    result = ped.auto_markers(character.positions, character.triangles)
    assert set(result.markers) == set(ped.BODY_MARKERS) and result.notes == ()
    for name in ped.BODY_MARKERS:
        assert distance(result.markers[name], character.joints[name]) < 0.04, name
    assert ped.marker_problems(result.markers, character.positions) == []


@pytest.mark.parametrize("offset, scale", [((0.4, -0.3, 0.0), 1.0), ((0.0, 0.0, 0.0), 0.9), ((0.0, 0.0, 0.0), 1.1)])
def test_auto_markers_follow_the_character_where_it_stands_and_at_its_size(offset, scale):
    character = mannequin.mannequin(45.0, offset=offset, scale=scale)
    result = ped.auto_markers(character.positions, character.triangles)
    for name in ped.BODY_MARKERS:
        assert distance(result.markers[name], character.joints[name]) < 0.045 * scale, name


def test_auto_markers_refuse_what_is_not_a_person():
    with pytest.raises(ped.MarkerError) as refused:
        ped.auto_markers(np.zeros((3, 3)), np.array([[0, 1, 2]]))
    assert refused.value.code == "too-small"


def test_the_click_guide_lands_inside_the_body_except_on_the_head_and_chin():
    origin, direction = (0.0, -5.0, 1.0), (0.0, 1.0, 0.0)
    assert ped.guide_point([], origin, direction, "wristL") is None
    assert ped.guide_point([4.9, 5.1], origin, direction, "wristL") == pytest.approx((0.0, 0.0, 1.0))
    assert ped.guide_point([4.9, 5.1], origin, direction, "headTop") == pytest.approx((0.0, -0.1, 1.0))
    assert ped.guide_point([4.9, 5.1], origin, direction, "toeL") == pytest.approx((0.0, -0.04, 1.0))
    assert ped.guide_point([4.9], origin, direction, "hipL") == pytest.approx((0.0, -0.1, 1.0))  # an open mesh


def test_the_guides_points_place_the_other_markers():
    character = mannequin.mannequin(45.0)
    clicked = {name: character.joints[name] for name in ped.GUIDE}
    markers = ped.derive_markers(clicked, character.positions, character.triangles)
    assert set(markers) == set(ped.BODY_MARKERS)
    for name in ped.GUIDE:
        assert markers[name] == pytest.approx(character.joints[name])
    for name in ped.DERIVED:
        assert distance(markers[name], character.joints[name]) < 0.05, name
    with pytest.raises(ped.MarkerError):
        ped.derive_markers({"headTop": (0, 0, 1)})


def test_mirror_copies_one_side_onto_the_other_across_the_middle():
    character = mannequin.mannequin(45.0, offset=(0.2, 0.0, 0.0))
    markers = dict(character.joints)
    markers["elbowR"] = (0.0, 0.5, 1.0)  # misplaced
    mirrored = ped.mirror_markers(markers, "L")
    for name in ped.LEFT:
        right = ped.MIRROR[name]
        assert mirrored[right] == pytest.approx(character.joints[right], abs=1e-9)
    assert mirrored["neck"][0] == pytest.approx(0.2)
    with pytest.raises(ValueError):
        ped.mirror_markers(markers, "X")


def test_the_elbow_moves_with_its_arm():
    shoulder, wrist, elbow = (0.2, 0, 1.4), (0.6, 0, 1.0), (0.4, 0.02, 1.2)
    # The wrist swings up to a T-pose: the elbow keeps its place on the arm and its offset from it.
    moved = ped.follow_middle(shoulder, wrist, (0.2 + 0.4 * math.sqrt(2), 0.0, 1.4), elbow)
    assert moved == pytest.approx((0.2 + 0.2 * math.sqrt(2), 0.02, 1.4), abs=1e-9)
    # A longer arm stretches it.
    assert ped.follow_middle(shoulder, wrist, (1.0, 0, 0.6), elbow) == pytest.approx((0.6, 0.04, 1.0), abs=1e-9)
    before = {"shoulderL": shoulder, "wristL": wrist, "elbowL": elbow, "hipL": (0.1, 0, 0.9), "kneeL": (0.1, 0, 0.5),
              "ankleL": (0.1, 0, 0.1)}
    after = dict(before, wristL=(0.2 + 0.4 * math.sqrt(2), 0.0, 1.4))
    assert set(ped.moved_middles(before, after)) == {"elbowL"}
    # Moving the elbow itself, or both ends at once, moves nothing else.
    assert ped.moved_middles(before, dict(after, elbowL=(0.5, 0, 1.3))) == {}
    assert ped.moved_middles(before, dict(after, shoulderL=(0.25, 0, 1.4))) == {}


def test_marker_problems_name_the_markers():
    character = mannequin.mannequin(45.0)
    good = dict(character.joints)
    assert ped.marker_problems(good, character.positions) == []
    missing = {k: v for k, v in good.items() if k != "chin"}
    assert ped.marker_problems(missing) == [ped.MarkerProblem("missing", ("chin",))]
    swapped = dict(good, shoulderL=good["shoulderR"], shoulderR=good["shoulderL"])
    assert ped.marker_problems(swapped)[0] == ped.MarkerProblem("side", ("shoulderL", "shoulderR"))
    upside = dict(good, headTop=(0.0, 0.0, 0.5))
    assert ped.marker_problems(upside)[0].code == "order"
    long_arm = dict(good, wristL=(0.9, 0.0, 0.7))
    assert ped.marker_problems(long_arm)[0].code == "asymmetric"
    far = dict(good, kneeL=(1.5, 0.0, 0.5))
    codes = {p.code: p.markers for p in ped.marker_problems(far, character.positions)}
    assert codes["outside"] == ("kneeL",)


# ---- markers from a rig ----------------------------------------------------------------------------------


def rig_joints(kind):
    """The mannequin's joints named as a rig of ``kind`` names its bones (the head bone at the base of the skull)."""
    character = mannequin.mannequin(45.0)
    table = ped.RIG_TABLES[kind]
    joints = {}
    for marker, bones in table.items():
        if marker == "head":
            point = (0.0, 0.0, 1.6)
        else:
            point = character.joints[marker]
        name = bones[0]
        joints["mixamorig:" + name if kind == "mixamo" else name] = point
    joints["SomethingElse"] = (0.0, 0.0, 0.0)
    return character, joints


@pytest.mark.parametrize("kind", ped.RIG_KINDS)
def test_markers_come_from_the_joints_of_a_known_rig(kind):
    character, joints = rig_joints(kind)
    assert ped.rig_kind(joints) == kind
    found, markers = ped.markers_from_rig(joints, character.positions)
    assert found == kind
    for name in ped.BODY_MARKERS:
        if name not in ("headTop", "chin"):
            assert markers[name] == pytest.approx(character.joints[name]), name
    assert distance(markers["headTop"], character.joints["headTop"]) < 0.03
    assert markers["chin"][1] < -0.05 and 1.5 < markers["chin"][2] < 1.62  # on the face, below the head joint


def test_an_unknown_rig_gives_no_markers():
    assert ped.rig_kind({"Bone": (0, 0, 0), "Bone.001": (0, 0, 1)}) is None
    with pytest.raises(ped.MarkerError) as refused:
        ped.markers_from_rig({"Bone": (0, 0, 0)})
    assert refused.value.code == "no-rig"
    # A rig that lacks a joint (here the left foot) is not used.
    _, joints = rig_joints("unreal")
    del joints["foot_l"]
    assert ped.rig_kind(joints) is None


# ---- the character ---------------------------------------------------------------------------------------


def facts_of(character, **changes):
    points = character.positions
    values = dict(objects=len(character.parts), vertices=len(points), triangles=len(character.triangles),
                  materials=1, lower=tuple(points.min(axis=0)), upper=tuple(points.max(axis=0)),
                  facing=ped.facing_guess(points), upside_down=ped.stands_on_head(points, character.triangles))
    values.update(changes)
    return ped.Facts(**values)


def codes(rows):
    return {row.code: row for row in rows}


def test_a_good_character_passes_once_its_facing_is_confirmed():
    character = mannequin.mannequin(45.0)
    rows = codes(ped.checks(facts_of(character)))
    assert rows["height"].level == "ok" and rows["size"].level == "ok"
    assert rows["facing"].key == "ped.check.facing" and not ped.checks_pass(list(rows.values()))
    confirmed = ped.checks(facts_of(character), facing_confirmed=True)
    assert codes(confirmed)["facing"].level == "ok" and ped.checks_pass(confirmed)


@pytest.mark.parametrize("unit, factor", [("cm", 100.0), ("mm", 1000.0), ("in", 1 / 0.0254)])
def test_a_character_in_other_units_is_asked_about(unit, factor):
    character = mannequin.mannequin(45.0, scale=factor)
    row = codes(ped.checks(facts_of(character), facing_confirmed=True))["height"]
    assert row.level == "error" and row.key == "ped.check.unit" and row.fields["unit"] == f"ped.unit.{unit}"
    assert row.fixes == (("dct_link.ped_scale", {"factor": pytest.approx(1 / factor, rel=1e-3)}),)


def test_an_unusual_height_warns_and_offers_the_usual_one():
    row = codes(ped.checks(facts_of(mannequin.mannequin(45.0, scale=0.6)), facing_confirmed=True))["height"]
    assert row.level == "warning" and row.key == "ped.check.height-unusual"
    assert row.fixes[0][1]["factor"] == pytest.approx(1.8 / 1.08, rel=0.02)


def test_a_lying_or_upside_down_character_is_offered_a_turn():
    character = mannequin.mannequin(45.0)
    lying = character.positions[:, [0, 2, 1]]  # exported with Y up
    rows = codes(ped.checks(facts_of(character, lower=tuple(lying.min(axis=0)), upper=tuple(lying.max(axis=0)))))
    assert rows["upright"].key == "ped.check.lying" and rows["upright"].level == "error"
    assert [f[1] for f in rows["upright"].fixes] == [{"axis": "X", "degrees": 90.0}, {"axis": "X", "degrees": -90.0}]
    flipped = character.positions * np.array([1.0, 1.0, -1.0])
    assert ped.stands_on_head(flipped, character.triangles)
    assert not ped.stands_on_head(character.positions, character.triangles)
    rows = codes(ped.checks(facts_of(character, upside_down=True)))
    assert rows["upright"].key == "ped.check.upside-down"


@pytest.mark.parametrize("turn, direction", [(90.0, "screen-right"), (-90.0, "screen-left"), (180.0, "back")])
def test_the_feet_tell_where_the_character_faces(turn, direction):
    character = mannequin.mannequin(45.0, turn=turn)
    assert ped.facing_guess(character.positions) == pytest.approx(turn if turn != 180.0 else 180.0, abs=1.0) or \
        abs(ped.facing_guess(character.positions)) == pytest.approx(180.0, abs=1.0)
    row = codes(ped.checks(facts_of(character)))["facing"]
    assert row.key == "ped.check.facing-other" and row.fields["direction"] == f"ped.direction.{direction}"
    assert abs(ped.facing_guess(mannequin.mannequin(45.0).positions)) < 1.0


def test_the_size_budget():
    character = mannequin.mannequin(45.0)
    rows = codes(ped.checks(facts_of(character, vertices=120_000), facing_confirmed=True))
    assert rows["size"].level == "warning" and rows["size"].fields["budget"] == ped.PED_BUDGET
    assert ped.checks_pass(list(rows.values()))  # a warning only
    rows = codes(ped.checks(facts_of(character, vertices=300_001), facing_confirmed=True))
    assert rows["size"].level == "error" and not ped.checks_pass(list(rows.values()))


def test_what_has_to_be_fixed_before_a_rig():
    character = mannequin.mannequin(45.0)
    for change, code in ((dict(transformed=("Body",)), "transforms"), (dict(modified=("Body",)), "modifiers"),
                         (dict(rigs=("Armature",)), "rig"), (dict(shape_keys=("Head",)), "shape-keys")):
        rows = ped.checks(facts_of(character, **change), facing_confirmed=True)
        assert code in codes(rows) and not ped.checks_pass(rows), code
    far = facts_of(mannequin.mannequin(45.0, offset=(2.5, 0.0, 0.0)))
    assert codes(ped.checks(far, facing_confirmed=True))["origin"].fixes == (("dct_link.ped_to_origin", {}),)
    # In centimetres the distance would be in the wrong unit: the unit comes first.
    far_cm = facts_of(mannequin.mannequin(45.0, offset=(2.5, 0.0, 0.0), scale=100.0))
    assert "origin" not in codes(ped.checks(far_cm, facing_confirmed=True))
    assert ped.checks(ped.Facts())[0].code == "character"
    rigged = ped.checks(facts_of(character, rigged=True, rigs=("Armature",)))
    assert [row.code for row in rigged] == ["rigged"] and ped.checks_pass(rigged)


@pytest.mark.parametrize("name, materials, role", [
    ("Body", [], "body"), ("Hair_Long", [], "hair"), ("EyeLeft", [], "eyes"), ("eyes.001", [], "eyes"),
    ("EyeBrows", [], "head"), ("Eyelashes", [], "head"), ("Teeth_Lower", [], "teeth"), ("Tongue", [], "teeth"),
    ("Head", [], "head"), ("Mesh.004", ["M_Hair"], "hair"), ("Mesh.005", ["Cornea"], "eyes"),
    ("Glasses", [], "accessory"), ("Bunny_Suit", [], "body"), ("Capsule", [], "body"),
])
def test_part_roles_are_guessed_from_names(name, materials, role):
    assert ped.guess_role(name, materials) == role


# ---- the rig request -------------------------------------------------------------------------------------


def parts_of(character):
    return [ped.Part(p.name, p.role, p.positions, p.triangles) for p in character.parts]


def test_the_rig_request_joins_the_parts():
    character = mannequin.mannequin(45.0)
    data = ped.rig_input(parts_of(character))
    assert data.vertices == len(character.positions) and data.triangle_count == len(character.triangles)
    assert data.positions.dtype == np.float32 and data.triangles.dtype == np.uint32
    assert data.roles == ["body", "head", "hair", "eyes"]
    ids = np.frombuffer(data.part_ids, dtype=np.uint8)
    starts = [start for _, start, _ in data.ranges]
    assert [int(ids[s]) for s in starts] == [0, 1, 2, 3]
    assert data.ranges[0] == ("Body", 0, len(character.parts[0].positions))
    # The payload dct_link would send is valid.
    prepared = dct_ped.prepare_ped_rig("a_m_y_tester_01", character.joints, data.positions, data.triangles,
                                       rights_confirmed=True, parts=data.roles, part_ids=data.part_ids)
    assert prepared.size == 12 * data.vertices + 12 * data.triangle_count + data.vertices


def test_a_body_only_character_sends_no_parts():
    character = mannequin.mannequin(45.0)
    body = ped.Part("Body", "body", character.parts[0].positions, character.parts[0].triangles)
    data = ped.rig_input([body])
    assert data.roles == [] and data.part_ids is None


def test_the_topology_hash_changes_with_the_mesh_not_its_pose():
    character = mannequin.mannequin(45.0)
    parts = parts_of(character)
    first = ped.rig_input(parts).topology
    moved = [p._replace(positions=p.positions + 0.1) for p in parts]
    assert ped.rig_input(moved).topology == first
    edited = list(parts)
    edited[0] = edited[0]._replace(triangles=edited[0].triangles[:-1])
    assert ped.rig_input(edited).topology != first
    renamed = list(parts)
    renamed[1] = renamed[1]._replace(name="Head.001")
    assert ped.rig_input(renamed).topology != first


def test_rig_options_send_only_what_differs():
    assert ped.rig_options() == {}
    assert ped.rig_options(fingers="auto", refine_markers=False, rest_model="linear") == {
        "fingers": "auto", "refineMarkers": False, "restModel": "linear"}
    assert ped.rig_options(fingers="nonsense") == {}


# ---- applying a rig --------------------------------------------------------------------------------------


def skeleton():
    return [dct_ped.PedBone(b["name"], b["tag"], b["parent"], b["flags"], tuple(b["rotation"]), tuple(b["translation"]),
                            tuple(b["world"])) for b in fake_dct.ped_skeleton()]


def test_the_armature_plan_keeps_every_rest_matrix():
    bones = skeleton()
    plan = ped.armature_plan(bones)
    assert [b.name for b in plan] == [b.name for b in bones]
    for planned, bone in zip(plan, bones):
        assert planned.rest[:3, 3] == pytest.approx(bone.world[12:15])
        assert planned.rest[:3, :3] @ planned.rest[:3, :3].T == pytest.approx(np.eye(3), abs=1e-6)
        assert ped.protocol_matrix(planned.rest) == pytest.approx(bone.world)
        assert ped.MIN_BONE <= planned.length <= ped.MAX_BONE
    assert next(p for p in plan if p.name == "IK_Head").length == ped.LEAF_BONE
    # A bone is drawn to its child when its own Y axis points there, short otherwise.
    straight = []
    for index, (name, parent, head) in enumerate([("A", -1, (0, 0, 0)), ("B", 0, (0, 0.3, 0)), ("C", 0, (0.3, 0, 0))]):
        world = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, *head, 1]
        straight.append(dct_ped.PedBone(name, index, parent, 0, (0, 0, 0, 1), head, tuple(world)))
    assert ped.armature_plan(straight)[0].length == pytest.approx(0.3)
    sideways = [straight[0], straight[2]._replace(parent=0)]
    assert ped.armature_plan(sideways)[0].length == ped.SHORT_BONE


def forward(rest, parents, bases):
    """What Blender does with the bases: each bone's pose from its parent's, its rest offset and its basis."""
    world = []
    for index, parent in enumerate(parents):
        local = rest[index] if parent < 0 else np.linalg.inv(rest[parent]) @ rest[index]
        world.append((local if parent < 0 else world[parent] @ local) @ bases[index])
    return world


def test_pose_bases_give_back_the_characters_pose():
    bones = skeleton()
    rest = [ped.blender_matrix(b.world) for b in bones]
    parents = [b.parent for b in bones]
    shift = np.eye(4)
    shift[:3, 3] = (0.3, -0.2, 1.0)
    turn = np.eye(4)
    turn[:3, :3] = ped._rotation((0, 0, 1), 0.4)
    posed = [shift @ turn @ m for m in rest]
    posed[17] = posed[17] @ np.array([[1, 0, 0, 0], [0, 0, -1, 0], [0, 1, 0, 0], [0, 0, 0, 1.0]])  # a bent forearm
    bases = ped.pose_bases(rest, posed, parents)
    for got, want in zip(forward(rest, parents, bases), posed):
        assert got == pytest.approx(want, abs=1e-9)
    assert ped.pose_bases(rest, rest, parents)[5] == pytest.approx(np.eye(4), abs=1e-9)


def test_vertex_groups_carry_the_weights_by_bone_name():
    names = ["A", "B", "C"]
    indices = bytes([0, 1, 0, 0, 2, 0, 0, 0, 1, 2, 0, 0])
    weights = bytes([200, 55, 0, 0, 255, 0, 0, 0, 128, 127, 0, 0])
    groups = ped.vertex_groups(indices, weights, names, 0, 3)
    flat = {(bone, int(v)): round(w * 255) for bone, entries in groups.items() for w, vs in entries for v in vs}
    assert flat == {("A", 0): 200, ("B", 0): 55, ("C", 1): 255, ("B", 2): 128, ("C", 2): 127}
    # An object's range: its own vertex numbers from 0.
    second = ped.vertex_groups(indices, weights, names, 1, 2)
    assert {(b, int(v)) for b, e in second.items() for _, vs in e for v in vs} == {("C", 0), ("B", 1), ("C", 1)}
    rest = ped.rest_parts(np.arange(9, dtype=np.float32), [("One", 0, 1), ("Two", 1, 2)])
    assert rest["Two"].tolist() == [[3, 4, 5], [6, 7, 8]]


def t_posed(rest, names, parents):
    """The skeleton's rest pose with the arms held out straight to the sides (a T-pose)."""
    index = {name: i for i, name in enumerate(names)}
    turns = {}
    for side, sign in (("L", 1.0), ("R", -1.0)):
        turns[index[f"SKEL_{side}_UpperArm"]] = (index[f"SKEL_{side}_Forearm"], (sign, 0.0, 0.0))
        turns[index[f"SKEL_{side}_Forearm"]] = (index[f"SKEL_{side}_Hand"], (sign, 0.0, 0.0))
    return ped.posed_world(rest, parents, turns)


@pytest.mark.parametrize("arms", ["a-pose", "t-pose"])
def test_test_poses_bend_the_limbs_the_right_way(arms):
    """The poses aim the limbs, so they look the same whatever pose the template's rest pose holds the arms in."""
    bones = skeleton()
    names = [b.name for b in bones]
    rest = [ped.blender_matrix(b.world) for b in bones]
    parents = [b.parent for b in bones]
    if arms == "t-pose":
        rest = t_posed(rest, names, parents)
        assert rest[names.index("SKEL_L_Hand")][2, 3] == pytest.approx(rest[names.index("SKEL_L_UpperArm")][2, 3])
    position = {name: (lambda world, i=i: world[i][:3, 3]) for i, name in enumerate(names)}
    up = ped.test_pose("arms_up", names, rest, parents)
    shoulder = position["SKEL_L_UpperArm"](rest)
    assert position["SKEL_L_Hand"](up)[2] > shoulder[2] + 0.4 and position["SKEL_R_Hand"](up)[2] > shoulder[2] + 0.4
    assert position["SKEL_L_UpperArm"](up) == pytest.approx(shoulder)
    forward_ = ped.test_pose("arms_forward", names, rest, parents)
    for side in "LR":
        hand, root = position[f"SKEL_{side}_Hand"](forward_), position[f"SKEL_{side}_UpperArm"](rest)
        assert hand[1] < root[1] - 0.4 and abs(hand[2] - root[2]) < 0.15  # in front, at shoulder height
    squat = ped.test_pose("squat", names, rest, parents)
    assert position["SKEL_L_Calf"](squat)[1] < position["SKEL_L_Calf"](rest)[1] - 0.2  # the knees come forward
    assert position["SKEL_R_Calf"](squat)[1] < position["SKEL_R_Calf"](rest)[1] - 0.2
    assert position["SKEL_Neck_1"](squat)[1] < position["SKEL_Neck_1"](rest)[1] - 0.05  # the body leans forward
    walk = ped.test_pose("walk", names, rest, parents)
    assert position["SKEL_L_Foot"](walk)[1] < position["SKEL_R_Foot"](walk)[1] - 0.3  # the left foot steps out
    assert position["SKEL_R_Hand"](walk)[1] < position["SKEL_L_Hand"](walk)[1]  # the opposite arm swings forward
    twist = ped.test_pose("twist", names, rest, parents)
    assert position["SKEL_L_UpperArm"](twist)[1] != pytest.approx(position["SKEL_L_UpperArm"](rest)[1], abs=0.02)
    for pose in ped.TEST_POSES:
        world = ped.test_pose(pose, names, rest, parents)
        for m in world:  # rigid: rotations stay rotations
            assert m[:3, :3] @ m[:3, :3].T == pytest.approx(np.eye(3), abs=1e-9)
    assert set(ped.POSES) == {"yours", "rest"} | set(ped.TEST_POSES)


def test_strain_finds_stretched_and_squashed_edges():
    rest = np.array([[0, 0, 0], [1, 0, 0], [2, 0, 0], [3, 0, 0.0]])
    posed = np.array([[0, 0, 0], [1, 0, 0], [3, 0, 0], [3.1, 0, 0.0]])
    edges = np.array([[0, 1], [1, 2], [2, 3]])
    assert ped.strain(rest, posed, edges).tolist() == [1, 2, 3]
    assert ped.strain(rest, rest, edges).tolist() == []


# ---- local checks and the report -------------------------------------------------------------------------


def test_weight_findings():
    # The fourth body vertex is weighted only on a bone that never deforms: Durty Cloth Tool moves that weight up the
    # chain, so it is no unweighted vertex.
    data = {"Body": {"counts": np.array([1, 0, 5, 0]), "totals": np.array([1.0, 0.0, 1.0, 0.0]),
                     "bad": np.array([False, False, False, True]), "groups": ["SKEL_Head", "Unknown", "DCT Tears"]},
            "Hair": {"counts": np.array([1, 1]), "totals": np.array([1.0, 0.0]), "bad": np.zeros(2, dtype=bool),
                     "groups": ["SKEL_Head"]}}
    found = {f.code: f for f in ped.weight_findings(data, ["SKEL_Head", "SKEL_ROOT"])}
    assert found["unweighted"].count == 2 and found["unweighted"].vertices["Hair"].tolist() == [1]
    assert found["unweighted"].vertices["Body"].tolist() == [1]
    assert found["too-many"].vertices == {"Body": pytest.approx(np.array([2]))}
    assert found["non-deforming"].count == 1
    assert found["unknown-groups"].names == ("Unknown",)
    assert ped.non_deforming("SKEL_ROOT") and ped.non_deforming("IK_Head") and ped.non_deforming("PH_L_Hand")
    assert not ped.non_deforming("SKEL_Head")


def test_the_armature_must_keep_the_rigs_bones_within_tolerance():
    rest = np.eye(4)
    rest[:3, 3] = (0.1, 0.2, 0.3)
    nudged = rest.copy()
    nudged[0, 3] += 0.00005
    assert ped.armature_changes({"A": rest}, {"A": nudged}) == ()
    nudged[0, 3] += 0.0002
    assert ped.armature_changes({"A": rest}, {"A": nudged}) == ("A",)
    turned = rest.copy()
    turned[:3, :3] = ped._rotation((0, 0, 1), math.radians(0.005))
    assert ped.armature_changes({"A": rest}, {"A": turned}) == ()
    turned[:3, :3] = ped._rotation((0, 0, 1), math.radians(0.02))
    assert ped.armature_changes({"A": rest}, {"A": turned}) == ("A",)
    assert ped.armature_changes({"A": rest, "B": rest}, {"A": rest}) == ("B",)
    # A bone the rig does not have would be a joint Durty Cloth Tool refuses.
    assert ped.armature_changes({"A": rest}, {"A": rest, "Extra": rest}) == ("Extra",)


def test_the_report_in_lines():
    report = {"outcome": "needsReview", "confidence": 0.62,
              "warnings": [{"code": "marker_offset", "count": 2, "value": 31.4, "markers": ["elbowL", "kneeR"]},
                           {"code": "fingers_fallback"}, {"code": "something_new"}],
              "suggestedTemplate": "a_m_m_tester_02", "proxy": True}
    lines = ped.report_lines(report)
    assert lines[0] == ped.ReportLine("WARNING", "ped.result.review", {"percent": 62})
    assert lines[1].key == "ped.warning.marker_offset" and lines[1].fields["value"] == 31
    assert lines[1].markers == ("elbowL", "kneeR")
    assert lines[2].level == "INFO" and lines[2].fields["count"] == 0  # every field is there for the text
    assert lines[3].key == "ped.warning.other" and lines[3].fields["code"] == "something_new"
    assert lines[4].key == "ped.suggest" and lines[4].template == "a_m_m_tester_02"
    assert lines[5].key == "ped.result.proxy"
    assert ped.report_lines({"outcome": "ready", "confidence": 1, "warnings": []})[0].key == "ped.result.ready"


def test_refusals_and_refined_markers():
    lines = ped.refusal_lines([{"code": "marker_side", "markers": ["shoulderL", "shoulderR"]},
                               {"code": "marker_side", "markers": ["hipL", "shoulderL"]},
                               {"code": "brand_new", "message": "x"}])
    assert [(l.key, l.markers) for l in lines] == [("ped.refusal.marker_side", ("shoulderL", "shoulderR", "hipL")),
                                                   ("ped.refusal.other", ())]
    sent = {"elbowL": (0.4, 0.0, 1.2), "kneeL": (0.1, 0.0, 0.5)}
    report = {"markers": {"elbowL": [0.4, 0.03, 1.2], "kneeL": [0.1, 0.005, 0.5]}}
    assert ped.refined_moves(report, sent) == [("elbowL", pytest.approx(0.03))]
    assert ped.markers_from_json(json.dumps(report["markers"])) == {"elbowL": (0.4, 0.03, 1.2),
                                                                     "kneeL": (0.1, 0.005, 0.5)}
    assert ped.markers_from_json("not json") == {}


# ---- sending ---------------------------------------------------------------------------------------------


def test_model_names():
    assert ped.model_problem("my_hero") is None
    assert ped.model_problem("Hero")[0] == "ped.why.model"
    assert ped.model_problem("ab")[0] == "ped.why.model"
    key, fields = ped.model_problem("a_m_y_hero")
    assert key == "ped.why.model-game" and fields == {"prefix": "a_m_", "suggestion": "my_y_hero"}
    assert ped.suggest_model("Hero Character 2") == "hero_character_2"
    assert ped.suggest_model("2 Fast") == "fast"
    assert ped.suggest_model("Ü") == "my_ped"
    assert ped.suggest_model("mp_m_freemode_01") == "my_mp_m_freemode_01"
    for name in ("Hero Character 2", "2 Fast", "Ü", "x" * 80, "mp_m_freemode_01"):
        assert ped.model_problem(ped.suggest_model(name)) is None, name


def test_texture_sizes():
    assert ped.texture_problem(2048, 1024) is None
    assert ped.texture_problem(8192, 1024) == "too-large"
    assert ped.texture_problem(1022, 1024) == "not-multiple-of-four"
    assert ped.texture_problem(1000, 1000) == "non-power-of-two"


# ---- the next step ---------------------------------------------------------------------------------------


def test_the_next_step_follows_the_stages():
    flow = ped.Flow()
    assert ped.next_step(flow) == "ped.next.character"
    flow = flow._replace(character=True)
    assert ped.next_step(flow) == "ped.next.fix"
    flow = flow._replace(checks_ok=True)
    assert ped.next_step(flow) == "ped.next.markers"
    flow = flow._replace(markers=19, marker_problems=True)
    assert ped.next_step(flow) == "ped.next.marker-problems"
    flow = flow._replace(marker_problems=False)
    assert ped.next_step(flow) == "ped.next.connect"
    flow = flow._replace(connected=True)
    assert ped.next_step(flow) == "ped.next.template"
    flow = flow._replace(template=True)
    assert ped.next_step(flow) == "ped.next.rig"
    assert ped.next_step(flow._replace(rigging=True)) == "ped.next.rigging"
    assert ped.next_step(flow._replace(result=True)) == "ped.next.approve"
    flow = flow._replace(rigged=True)
    assert ped.next_step(flow) == "ped.next.check"
    flow = flow._replace(checked=True)
    assert ped.next_step(flow) == "ped.next.send"
    assert ped.next_step(flow._replace(sending=True)) == "ped.next.sending"
    assert ped.next_step(flow._replace(sent=True)) == "ped.next.done"
    assert [ped.stage_of(ped.next_step(f)) for f in (ped.Flow(), flow)] == ["character", "send"]
    for key in ped.STEP_OPERATORS:
        assert key.startswith("ped.next.")


def test_every_text_the_custom_ped_code_names_exists():
    """A text key that does not exist only fails when Blender draws it; the code's literal keys are checked here."""
    package = pathlib.Path(ped.__file__).parent
    source = "".join((package / name).read_text("utf-8") for name in ("ped.py", "ped_link.py", "ped_host.py",
                                                                       "ui_ped.py", "ui.py"))
    keys = set(re.findall(r'"((?:ped|workspace|info\.ped)[\w.\-]*\.[\w\-]+)"', source))
    prefixes = {"ped.fingers", "ped.face", "ped.rest", "ped.ragdoll"}  # completed in the code (_items)
    assert sorted(key for key in keys if key not in strings.EN and key not in prefixes) == []
