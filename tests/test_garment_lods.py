# SPDX-License-Identifier: GPL-3.0-or-later
"""Generate LODs' choice without Blender: the size of a level's holes against High, and the candidate kept."""

from __future__ import annotations

import numpy as np
import pytest

from durty_cloth_tool_link import garment


def gaps(count: int, holes: int, size: float) -> np.ndarray:
    """Distances from ``count`` points of High's surface to a level: a millimetre everywhere, ``size`` where the
    level has a hole (``holes`` points)."""
    distances = np.full(count, 0.001)
    distances[:holes] = size
    return distances


def test_the_hole_size_is_the_gap_of_the_largest_holes_not_of_a_few_stray_points():
    assert garment.hole_size(gaps(1000, 50, 0.03)) == pytest.approx(0.03)  # 5 % of the surface open: a hole
    assert garment.hole_size(gaps(1000, 10, 0.03)) == pytest.approx(0.001)  # 1 %: a few stray points
    assert garment.hole_size([]) == 0.0


def test_of_two_candidates_the_one_with_the_smaller_large_holes_wins():
    welded = garment.LodCandidate(weld=0.008, triangles=600, hole=garment.hole_size(gaps(1000, 50, 0.03)))
    plain = garment.LodCandidate(weld=0.0, triangles=590, hole=garment.hole_size(gaps(1000, 50, 0.012)))
    assert garment.choose_lod([welded, plain], budget=600) == 1
    assert garment.choose_lod([plain, welded], budget=600) == 0


def test_a_candidate_over_the_triangle_budget_is_never_chosen():
    tight = garment.LodCandidate(weld=0.0, triangles=640, hole=0.001)
    within = garment.LodCandidate(weld=0.004, triangles=598, hole=0.02)
    assert garment.choose_lod([tight, within], budget=600) == 1
    # When every candidate is over the budget, the smallest one is kept.
    assert garment.choose_lod([tight, within._replace(triangles=620)], budget=600) == 1


def test_holes_alike_keep_the_larger_weld():
    small = garment.LodCandidate(weld=0.004, triangles=600, hole=0.0060)
    large = garment.LodCandidate(weld=0.008, triangles=600, hole=0.0070)
    assert garment.choose_lod([small, large], budget=600) == 1  # within the tie: the joined surface holds in a pose
    assert garment.choose_lod([small, large._replace(hole=0.02)], budget=600) == 0
