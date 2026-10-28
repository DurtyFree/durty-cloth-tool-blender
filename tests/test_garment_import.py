# SPDX-License-Identifier: GPL-3.0-or-later
"""Import Garment without Blender: the garment type guessed from the file name, and exports normalised to about
1 m tall scaled to body size."""

from __future__ import annotations

import numpy as np
import pytest

from durty_cloth_tool_link import garment
from tests.support import synthetic


@pytest.mark.parametrize("name, category", [
    ("hoodie", "hoodie"), ("Black_Hoodie_v2", "hoodie"), ("kapüşonlu sweatshirt", "hoodie"),
    ("cargo pants", "pants"), ("JEANS-blue", "pants"), ("pantolon_01", "pants"),
    ("ayakkabı", "shoes"), ("Sneakers", "shoes"), ("leather boots", "shoes"), ("Ayakkabi", "shoes"),
    ("summer_sandals", "sandals"), ("t-shirt basic", "tshirt"), ("tişört", "tshirt"), ("Tee", "tshirt"),
    ("short sleeve shirt", "tshirt"), ("shirt", "long_sleeve"), ("sweatshirt", "long_sleeve"), ("kazak", "long_sleeve"),
    ("tank top", "vest"), ("yelek", "vest"), ("tactical vest", "armour"), ("plate carrier", "armour"),
    ("çanta", "bag"), ("backpack", "bag"), ("shorts", "shorts"), ("şort", "shorts"),
    ("trench coat", "long_coat"), ("palto", "long_coat"), ("biker jacket", "long_jacket"), ("ceket", "long_jacket"),
    ("cardigan", "open_jacket"), ("summer dress", "dress"), ("etek", "skirt"), ("skirt", "skirt"),
    ("ski mask", "mask"), ("baseball cap", "hat"), ("şapka", "hat"), ("sunglasses", "glasses"),
    ("gözlük", "glasses"), ("earrings", "ears"), ("wrist watch", "watch"), ("bracelet", "bracelet"),
    ("ShortSleeveShirt.fbx", "tshirt"), ("ShortSleeveTee", "tshirt"), ("BlackHoodie", "hoodie"),
    ("CargoPants", "pants"), ("LeatherJacket_v2", "long_jacket"), ("watchman_hoodie", "hoodie"),
    ("masked_rider_jacket", "long_jacket"), ("shortcut_jacket", "long_jacket"), ("siyah maskesi", "mask"),
    ("ayakkabılar", "shoes"), ("ceketi", "long_jacket"), ("pantolonlar", "pants"),
])
def test_the_type_is_guessed_from_whole_words_of_the_file_name(name, category):
    assert garment.guess_category(name) == category


@pytest.mark.parametrize("name", [
    "robot", "baggy_thing", "chatter", "upshot", "garment_01", "", "1234", "mantle", "watchman", "masked_rider",
    "shortcut", "Shortcut_v2", "Watchtower", "MaskedRider", "bootcamp", "capital",
])
def test_parts_of_words_and_unknown_names_guess_nothing(name):
    assert garment.guess_category(name) is None


def test_a_type_already_chosen_is_kept():
    assert garment.guess_category("cargo pants", chosen="hoodie") is None
    assert garment.guess_category("cargo pants", chosen=None) == "pants"


def normalised(positions: np.ndarray) -> np.ndarray:
    """``positions`` as a generator exports them: moved to the origin and scaled so the longest side is 1 m."""
    low, high = positions.min(axis=0), positions.max(axis=0)
    return (positions - (low + high) / 2) / float((high - low).max())


@pytest.mark.parametrize("mesh, category", [(synthetic.top("long"), "hoodie"), (synthetic.top("short"), "tshirt"),
                                            (synthetic.top("none"), "vest")])
def test_a_garment_normalised_to_1_m_is_scaled_to_body_size(mesh, category):
    points = normalised(mesh.positions)
    factor = garment.normalised_scale(points, category)
    assert factor is not None
    height = float(np.ptp(points[:, 2])) * factor
    assert height == pytest.approx(garment.garment_type(category).height)
    assert garment.plausible_size(float(np.ptp(points, axis=0).max()) * factor, category)


def test_a_garment_of_body_size_is_kept():
    assert garment.normalised_scale(synthetic.top("long").positions, "hoodie") is None
    assert garment.normalised_scale(synthetic.pants().positions, "pants") is None
    # Trousers 1 m long are as tall as trousers are, normalised or not.
    assert garment.normalised_scale(normalised(synthetic.pants().positions), "pants") is None


def test_only_automatic_rescales_a_normalised_garment():
    points = normalised(synthetic.top("long").positions)
    assert garment.normalised_scale(points, "hoodie", "auto") is not None
    for unit in garment.UNITS:
        assert garment.normalised_scale(points, "hoodie", unit) is None


def test_every_type_has_a_usual_height_of_its_own_size():
    for name, kind in garment.TYPES.items():
        low, high = kind.size
        assert low <= kind.height <= high, name
