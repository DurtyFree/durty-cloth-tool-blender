# SPDX-License-Identifier: GPL-3.0-or-later
"""Combine Materials' Pack Without Baking without Blender: the atlas grid, the images placed in it, the gaps filled
from neighbouring colours, the UVs moved into their squares, and which method Automatic picks."""

from __future__ import annotations

import numpy as np

from durty_cloth_tool_link import garment_atlas


def power_of_two(value: int) -> bool:
    return value > 0 and value & (value - 1) == 0


def overlaps(a, b) -> bool:
    (ax, ay, aw, ah), (bx, by, bw, bh) = a, b
    return ax < bx + bw and bx < ax + aw and ay < by + bh and by < ay + ah


def test_every_image_gets_its_own_square_of_a_power_of_two_atlas_within_the_texture_size():
    for sizes, limit in (([(1024, 1024), (1024, 1024)], 2048), ([(512, 256)] * 5, 2048),
                         ([(4096, 4096), (64, 64), (300, 700)], 2048), ([(2048, 2048)] * 9, 4096),
                         ([(128, 128)], 2048)):
        layout = garment_atlas.atlas_layout(sizes, limit)
        assert power_of_two(layout.size) and layout.size <= limit, (sizes, layout)
        assert len(layout.tiles) == len(sizes)
        for index, (x, y, w, h) in enumerate(layout.tiles):
            assert w == h and 0 <= x and 0 <= y and x + w <= layout.size and y + h <= layout.size, (sizes, layout)
            for other in layout.tiles[index + 1:]:
                assert not overlaps(layout.tiles[index], other), (sizes, layout)


def test_two_large_images_share_the_texture_size_and_small_ones_are_not_blown_up():
    two = garment_atlas.atlas_layout([(1024, 1024), (1024, 1024)], 2048)
    assert two.size == 2048 and two.tiles[0][2] == 1024
    small = garment_atlas.atlas_layout([(256, 256), (256, 256)], 4096)
    assert small.size == 512 and small.tiles[0][2] == 256


RED, BLUE = np.array([0.9, 0.1, 0.1, 1.0]), np.array([0.1, 0.2, 0.8, 1.0])


def test_gaps_take_the_colours_next_to_them_and_the_images_stay_as_they_are():
    pixels = np.zeros((32, 32, 4), dtype=np.float32)
    valid = np.zeros((32, 32), dtype=bool)
    pixels[:8, :8], valid[:8, :8] = RED, True
    pixels[24:, 24:], valid[24:, 24:] = BLUE, True
    filled = garment_atlas.fill_gaps(pixels, valid)
    assert np.allclose(filled[valid], pixels[valid])
    rgb = filled[..., :3]
    # Nothing stays black: every gap is a mix of the two colours around it.
    assert float(rgb.sum(axis=2).min()) > 0.9
    # Next to the red square the gap is red, next to the blue one blue.
    assert np.allclose(filled[3, 8], RED, atol=0.05) and np.allclose(filled[8, 3], RED, atol=0.05)
    assert np.allclose(filled[23, 28], BLUE, atol=0.05) and np.allclose(filled[28, 23], BLUE, atol=0.05)


def test_an_image_without_any_pixels_to_borrow_from_is_left_alone():
    pixels = np.full((8, 8, 4), 0.25, dtype=np.float32)
    assert np.array_equal(garment_atlas.fill_gaps(pixels, np.zeros((8, 8), dtype=bool)), pixels)


def quadrants(size: int) -> np.ndarray:
    """An image whose lower half is red and upper half blue, with a white right column."""
    image = np.empty((size, size, 4), dtype=np.float32)
    image[: size // 2], image[size // 2:] = RED, BLUE
    image[:, -1] = 1.0
    return image


def test_each_image_fills_its_square_inside_the_padding_and_only_that():
    layout = garment_atlas.atlas_layout([(512, 512), (300, 300), (64, 64)], 2048)
    pixels, valid = garment_atlas.blank_atlas(layout)
    garment_atlas.place_image(pixels, valid, layout, 0, quadrants(512))
    garment_atlas.place_image(pixels, valid, layout, 1, quadrants(300))
    garment_atlas.place_image(pixels, valid, layout, 2, (0.2, 0.6, 0.3, 1.0))  # a material without an image
    expected = np.zeros_like(valid)
    pad = layout.pad
    for x, y, w, h in layout.tiles:
        expected[y + pad:y + h - pad, x + pad:x + w - pad] = True
        bottom, top = y + pad, y + h - pad - 1
        left, right = x + pad, x + w - pad - 2
        if (x, y) == layout.tiles[2][:2]:
            assert np.allclose(pixels[bottom:top + 1, left:right + 2], (0.2, 0.6, 0.3, 1.0))
        else:
            assert np.allclose(pixels[bottom, left], RED, atol=0.02) and np.allclose(pixels[top, left], BLUE, atol=0.02)
            assert np.allclose(pixels[bottom, right + 1], 1.0, atol=0.02)
    assert np.array_equal(valid, expected)


def test_uvs_land_inside_their_images_square_and_repeats_beyond_the_image_are_counted():
    layout = garment_atlas.atlas_layout([(1024, 1024)] * 3, 2048)
    rng = np.random.default_rng(7)
    uv = rng.uniform(0.0, 1.0, (300, 2))
    uv[:3] = [(0.0, 0.0), (1.0, 1.0), (0.5, 0.5)]
    uv[3:5] = [(1.7, 0.2), (-0.4, 0.5)]  # a repeating texture
    image = np.repeat([0, 2, 1], 100)
    packed, outside = garment_atlas.remap_uvs(uv, image, layout)
    assert outside == 2
    for index in range(3):
        x, y, w, h = layout.tiles[index]
        chosen = packed[image == index] * layout.size
        assert (chosen[:, 0] >= x + layout.pad).all() and (chosen[:, 0] <= x + w - layout.pad).all()
        assert (chosen[:, 1] >= y + layout.pad).all() and (chosen[:, 1] <= y + h - layout.pad).all()
    first = layout.tiles[0]
    assert np.allclose(packed[0] * layout.size, (first[0] + layout.pad, first[1] + layout.pad))
    assert np.allclose(packed[1] * layout.size, (first[0] + first[2] - layout.pad, first[1] + first[3] - layout.pad))
    assert np.allclose(packed[2] * layout.size, (first[0] + first[2] / 2, first[1] + first[3] / 2))


def test_automatic_packs_when_every_material_has_exactly_one_image_and_bakes_otherwise():
    choose = garment_atlas.choose_method
    assert choose("auto", [1, 1]) == "pack" and choose("auto", [1, 1, 1, 1, 1]) == "pack"
    assert choose("auto", [1, 2]) == "bake"  # a normal map besides the colour
    assert choose("auto", [1, 0]) == "bake"  # a plain colour without an image
    assert choose("auto", [1]) == "bake"  # one material: nothing to pack, the layout is packed and baked
    assert choose("auto", [1, 1], plain=False) == "bake"  # an image read through a mapping or another UV map
    assert choose("auto", [1, 1], outside=4) == "bake"  # a repeating texture keeps its repeat only when baked
    assert choose("bake", [1, 1]) == "bake"
    assert choose("pack", [1, 2]) == "pack" and choose("pack", [0]) == "pack"


def test_linear_colours_are_stored_as_the_combined_textures_srgb_values():
    linear = np.array([[0.0, 0.0031308, 0.2140, 1.0]])
    assert np.allclose(garment_atlas.linear_to_srgb(linear), [[0.0, 0.0404, 0.5, 1.0]], atol=1e-3)
