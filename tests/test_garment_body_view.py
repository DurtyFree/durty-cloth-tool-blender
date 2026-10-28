# SPDX-License-Identifier: GPL-3.0-or-later
"""The freemode body's view options: the Body Cut choices a Reference Data Pack offers, and which of its parts each
Body Cut, Arms and Legs setting shows (on a synthetic pack, no Blender needed)."""

from __future__ import annotations

import json

import pytest

from durty_cloth_tool_link import garment_reference as ref
from tests.support import synthetic_pack


@pytest.fixture(scope="module")
def index():
    return ref.parse_index(synthetic_pack.files()["reference.json"])


def test_body_cut_offers_each_cut_by_what_skin_shows(index):
    assert ref.cut_choices(index, "male") == [
        ref.CutChoice("full", "full_body", None),
        ref.CutChoice("base", "bare_arms", None),
        ref.CutChoice("heist_00", "short_sleeves", 1),  # two cuts show the same skin: they are numbered
        ref.CutChoice("heist_01", "short_sleeves", 2),
        ref.CutChoice("heist_02", "long_sleeves_open_neck", None),
    ]
    assert ref.cut_choices(index, "female")[0].id == "full"
    assert ref.cut_choices(None, "male") == [] and ref.cut_choices(index, "other") == []


def test_a_display_name_the_add_on_does_not_know_falls_back_to_the_cut_id():
    value = json.loads(synthetic_pack.files()["reference.json"])
    value["genders"]["male"]["upperBody"][1]["display"] = "gloves_only"
    choices = ref.cut_choices(ref.parse_index(json.dumps(value).encode()), "male")
    assert choices[1] == ref.CutChoice("base", "other", None)


def test_the_standard_view_shows_the_standard_body(index):
    male = index.genders["male"]
    assert ref.standard_view(male, "full", "solid", "solid")
    assert ref.standard_view(male, "", "solid", "solid")  # nothing chosen yet
    assert not ref.standard_view(male, "base", "solid", "solid")
    assert not ref.standard_view(male, "full", "wire", "solid")
    assert not ref.standard_view(male, "full", "solid", "hidden")


@pytest.mark.parametrize("cut, arms, legs, solid, wire", [
    ("full", "wire", "solid", ["head", "feet", "uppr_full", "lowr"], ["uppr_full_arms"]),
    ("base", "hidden", "wire", ["head", "feet", "uppr_base"], ["lowr"]),
    ("heist_01", "solid", "hidden", ["head", "feet", "uppr_heist_01", "uppr_heist_01_arms"], []),
    ("heist_02", "wire", "solid", ["head", "feet", "uppr_heist_02", "lowr"], []),  # this cut shows no arm
    ("missing", "solid", "solid", ["head", "feet", "uppr_full", "uppr_full_arms", "lowr"], []),  # the default cut
])
def test_each_setting_shows_its_parts(index, cut, arms, legs, solid, wire):
    view = ref.view_parts(index.genders["male"], cut, arms, legs)
    assert (sorted(view.solid), sorted(view.wire)) == (sorted(solid), sorted(wire))


def test_an_unknown_view_mode_is_refused(index):
    with pytest.raises(ValueError):
        ref.view_parts(index.genders["male"], "full", "ghost", "solid")


def test_gloves_are_judged_against_the_bare_arms_cut_when_the_pack_has_one(index):
    assert ref.gloves_cut(index, "male") == "base"
    assert ref.gloves_cut(None, "male") is None  # without the pack Body Cut stays as it is
    value = json.loads(synthetic_pack.files()["reference.json"])
    for cut in value["genders"]["male"]["upperBody"]:
        if cut["display"] == "bare_arms":
            cut["display"] = "short_sleeves"
    assert ref.gloves_cut(ref.parse_index(json.dumps(value).encode()), "male") is None
