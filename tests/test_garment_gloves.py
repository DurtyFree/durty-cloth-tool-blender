# SPDX-License-Identifier: GPL-3.0-or-later
"""The Gloves type without Blender: its slot and markers, the type guess from a file name, the two-gloves check of
Validate, Align to Body on the wrist markers, the next step without markers, and the bare-arms Body Cut (on synthetic
gloves and a synthetic pack, nothing of the game)."""

from __future__ import annotations

import numpy as np
import pytest

from durty_cloth_tool_link import garment
from durty_cloth_tool_link.dct_link import protocol
from tests.support import synthetic


# ---- the type ------------------------------------------------------------------------------------------------


def test_gloves_go_into_the_arms_slot_appended_after_every_saved_type_and_slot():
    # Blender keeps a choice by its place in the list: what earlier versions saved keeps its meaning.
    assert garment.CATEGORIES[-1] == "gloves" and garment.CATEGORIES[:-1] == (
        "vest", "tshirt", "long_sleeve", "long_jacket", "pants", "shorts", "shoes", "hoodie", "open_jacket",
        "long_coat", "dress", "skirt", "sandals", "mask", "armour", "bag", "hat", "glasses", "ears", "watch",
        "bracelet")
    assert garment.SLOTS[-1] == "uppr" and garment.SLOTS[:-1] == (
        "jbib", "accs", "lowr", "feet", "berd", "hand", "task", "p_head", "p_eyes", "p_ears", "p_lwrist", "p_rwrist")
    assert garment.slots_for("gloves") == ("uppr",) and garment.categories_for("uppr") == ("gloves",)
    assert "gloves" in garment.CATEGORY_MENU and not garment.is_prop("gloves")


def test_gloves_have_the_two_wrist_markers_only_and_auto_markers_never_runs_for_them():
    assert garment.markers_for("gloves") == ("wrist_l", "wrist_r")
    assert not garment.detects_markers("gloves") and not garment.runs_auto_markers("gloves")
    for category in ("tshirt", "pants", "mask", "bag"):
        assert garment.runs_auto_markers(category)
    with pytest.raises(garment.MarkerError):
        garment.auto_markers(synthetic.gloves().positions, "gloves")


def test_gloves_show_skin_locked_on_without_thickness_or_a_push_out_region():
    assert garment.garment_type("gloves").skin and garment.skin_locked("gloves")
    assert not garment.offers_thickness("gloves") and not garment.offers_push_region("gloves")
    for category in ("tshirt", "pants", "shorts", "shoes", "bag"):
        assert not garment.skin_locked(category)
        assert garment.offers_thickness(category) and garment.offers_push_region(category)


def test_only_gloves_are_a_pair_and_carry_the_bare_arms_skin():
    assert garment.is_pair("gloves") and garment.garment_type("gloves").arm_skin in protocol.ARM_SKINS
    for category in garment.TYPES:
        if category != "gloves":
            assert not garment.is_pair(category) and garment.garment_type(category).arm_skin is None, category


def test_a_garment_goes_without_markers_only_when_its_type_may_and_none_is_placed():
    assert garment.markers_skipped("gloves", 0)
    assert not garment.markers_skipped("gloves", 1) and not garment.markers_skipped("tshirt", 0)


# ---- the type guess ------------------------------------------------------------------------------------------


@pytest.mark.parametrize("name", [
    "gloves", "Glove", "leather_gloves_v2", "BlackGloves.fbx", "winter mittens", "Mitten", "iron gauntlets",
    "Gauntlet_01", "eldiven", "deri eldivenler", "siyah eldiveni", "Eldivenleri",
])
def test_glove_file_names_guess_gloves(name):
    assert garment.guess_category(name) == "gloves"


@pytest.mark.parametrize("name", ["glovebox", "Glovebox_v2", "mittenwald", "gauntleted", "eldivenci", "foxglove"])
def test_words_that_only_start_or_end_with_a_glove_word_guess_nothing(name):
    assert garment.guess_category(name) is None


# ---- Validate: two gloves ------------------------------------------------------------------------------------


def two_gloves_finding(mesh: synthetic.Mesh):
    stats = {"two_gloves": garment.two_gloves(mesh.positions, mesh.edges)}
    return [f for f in garment.validate(stats) if f.code == "two-gloves"]


@pytest.mark.parametrize("mesh", [synthetic.gloves(), synthetic.gloves(arm_angle=0.0), synthetic.gloves(upright=True)])
def test_a_left_and_a_right_glove_pass(mesh):
    assert two_gloves_finding(mesh) == []


@pytest.mark.parametrize("mesh", [
    synthetic.gloves(sides=(1.0,)),  # one glove
    synthetic.gloves(sides=(1.0, 1.0)),  # two on the same side
    synthetic.gloves(sides=(-1.0, -1.0)),
    synthetic.gloves(joined=True),  # a piece across the centre: one piece of the two
])
def test_one_piece_or_gloves_on_one_side_are_warned_about(mesh):
    found = two_gloves_finding(mesh)
    assert [(f.severity, f.fields) for f in found] == [("warning", {})]


def test_other_types_are_not_checked_for_two_gloves():
    assert not [f for f in garment.validate({}) if f.code == "two-gloves"]


# ---- markers and Align to Body -------------------------------------------------------------------------------


def skeleton_joints():
    heads = {name: head for name, _, head in synthetic.SKELETON_BONES}
    return {name: heads[name] for name in garment.JOINTS if name in heads}


def test_align_to_body_puts_each_glove_on_its_own_wrist():
    mesh = synthetic.gloves()
    left = mesh.positions[:, 0] > 0
    shifts = {True: np.array([0.03, -0.02, 0.04]), False: np.array([-0.05, 0.01, -0.02])}
    moved = mesh.positions + np.where(left[:, None], shifts[True], shifts[False])
    markers = {"wrist_l": np.asarray(mesh.joints["wrist_l"]) + shifts[True],
               "wrist_r": np.asarray(mesh.joints["wrist_r"]) + shifts[False]}
    plan = garment.align_plan(markers, skeleton_joints(), "gloves")
    aligned, placed = garment.apply_align(moved, markers, plan)
    assert np.allclose(aligned, mesh.positions, atol=1e-3)  # each glove back where the hand is (within 1 mm)
    joints = skeleton_joints()
    assert np.allclose(placed["wrist_l"], joints["SKEL_L_Hand"])
    assert np.allclose(placed["wrist_r"], joints["SKEL_R_Hand"])


def test_wrist_markers_far_from_the_hands_or_missing_are_refused():
    mesh = synthetic.gloves()
    far = {"wrist_l": np.asarray(mesh.joints["wrist_l"]) + [0.0, 0.0, 0.8], "wrist_r": mesh.joints["wrist_r"]}
    with pytest.raises(garment.MarkerError):
        garment.align_plan(far, skeleton_joints(), "gloves")
    with pytest.raises(garment.MarkerError):
        garment.align_plan({"wrist_l": mesh.joints["wrist_l"]}, skeleton_joints(), "gloves")


def test_wrist_markers_that_are_no_mirror_images_are_named():
    mesh = synthetic.gloves()
    assert garment.marker_problems(mesh.joints, "gloves") == []
    crooked = {**mesh.joints, "wrist_r": tuple(np.asarray(mesh.joints["wrist_r"]) + [0.0, 0.0, 0.1])}
    assert garment.marker_problems(crooked, "gloves") == ["symmetry"]


def test_gloves_without_markers_go_to_the_fit_and_with_markers_through_align():
    state = garment.FlowState(garment=True, body=True, category="gloves")
    assert garment.next_step(state) == "garment.next.fit"  # upright gloves: gta.clothing places them
    assert garment.next_step(state._replace(markers=1)) == "garment.next.markers"
    assert garment.next_step(state._replace(markers=2)) == "garment.next.align"
    assert garment.next_step(state._replace(markers=2, aligned=True)) == "garment.next.fit"
    assert garment.markers_optional("gloves") and not garment.markers_optional("bag")


def test_the_fit_stage_counts_no_markers_for_gloves_that_need_none():
    state = garment.FlowState(garment=True, body=True, category="gloves")
    assert garment.stage_status(state, "fit").key is None
    status = garment.stage_status(state._replace(markers=1), "fit")
    assert (status.key, status.fields) == ("garment.status.markers", {"count": 1, "total": 2})
