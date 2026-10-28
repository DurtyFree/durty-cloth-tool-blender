# SPDX-License-Identifier: GPL-3.0-or-later
"""Validate's checks of what the game needs from a finished garment: weights that sum to one on every level of
detail, the ped shader, a square power-of-two diffuse and an armature at the origin."""

from __future__ import annotations

import numpy as np
import pytest

from durty_cloth_tool_link import garment, strings
from tests.support import synthetic

#: What a finished garment measures with none of the problems (see ``garment_host.validate_stats``).
CLEAN = {"non_finite": 0, "uv_layers": 1, "uv_outside": 0, "uv_area": 0.6, "weighted": True, "unweighted": 0,
         "over_four": 0, "colour1": "ok", "inside_share": 0.001, "materials": 1}


def top_weights(mesh: synthetic.Mesh) -> np.ndarray:
    """Two-bone weights for a synthetic top, blended from the spine at the hem to the neck at the collar."""
    z = mesh.positions[:, 2]
    upper = np.clip((z - z.min()) / np.ptp(z), 0.0, 1.0)
    return np.column_stack([1.0 - upper, upper])


def codes(stats) -> dict:
    return {f.code: f for f in garment.validate(stats)}


def test_weights_that_do_not_sum_to_one_are_counted_and_warned_about():
    table = top_weights(synthetic.top("short"))
    assert garment.weight_sum_count(table) == 0
    table[:25] *= 0.8  # 25 vertices that only move 80 % with the ped
    assert garment.weight_sum_count(table) == 25
    table[25:30] = 0.0  # vertices without weights are counted as unweighted, not here
    assert garment.weight_sum_count(table) == 25
    finding = codes({**CLEAN, "weight_sum": 25})["weight-sum"]
    assert finding.severity == "warning" and finding.fields == {"count": 25}
    assert "weight-sum" not in codes({**CLEAN, "weight_sum": 0})


def test_vertices_without_weights_are_named_by_their_level_of_detail():
    high = top_weights(synthetic.top("short"))
    medium = high[::2].copy()
    medium[:7] = 0.0  # a level made after the weights that lost some
    assert garment.influence_counts(medium)[0] == 7
    found = codes({**CLEAN, "unweighted_medium": 7, "unweighted_low": 0})
    assert found["lod-unweighted"].severity == "warning"
    assert found["lod-unweighted"].fields == {"level": "medium", "count": 7}
    assert "lod-unweighted" not in codes({**CLEAN, "unweighted_medium": 0, "unweighted_low": 0})
    both = [f for f in garment.validate({**CLEAN, "unweighted_medium": 3, "unweighted_low": 4})
            if f.code == "lod-unweighted"]
    assert [f.fields["level"] for f in both] == ["medium", "low"]


def test_a_sollumz_material_without_the_ped_shader_is_warned_about():
    assert garment.non_ped_materials([("Cloth", "ped.sps"), ("Fabric", "")]) == []
    assert garment.non_ped_materials([("Cloth", "ped_decal.sps"), ("Glass", "default.sps")]) == ["Glass"]
    finding = codes({**CLEAN, "non_ped": ["Glass"]})["shader"]
    assert finding.severity == "warning" and finding.fields == {"name": "Glass"}
    assert "shader" not in codes({**CLEAN, "non_ped": []})


@pytest.mark.parametrize("width, height, good", [
    (1024, 1024, True), (2048, 2048, True), (512, 512, True), (1024, 512, False), (1000, 1000, False),
    (1536, 1536, False),
])
def test_a_diffuse_must_be_square_and_a_power_of_two(width, height, good):
    assert garment.square_power_of_two(width, height) is good
    found = codes({**CLEAN, "diffuse_size": (width, height)})
    assert ("diffuse-size" not in found) is good
    if not good:
        assert found["diffuse-size"].severity == "warning"
        assert found["diffuse-size"].fields == {"width": width, "height": height}


def test_an_armature_away_from_the_origin_is_warned_about():
    found = codes({**CLEAN, "armature_offset": 0.253})
    assert found["armature-offset"].severity == "warning" and found["armature-offset"].fields == {"distance": 25.3}
    assert "armature-offset" not in codes({**CLEAN, "armature_offset": 0.0005})
    assert "armature-offset" not in codes(CLEAN)


def test_every_new_finding_has_words():
    stats = {**CLEAN, "weight_sum": 2, "unweighted_medium": 1, "non_ped": ["Glass"], "diffuse_size": (100, 50),
             "armature_offset": 1.0, "two_gloves": False}
    for finding in garment.validate(stats):
        assert f"garment.finding.{finding.code}" in strings.EN, finding.code
