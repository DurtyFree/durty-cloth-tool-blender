# SPDX-License-Identifier: GPL-3.0-or-later
"""Pixel conversion, the vertical flip, colour handling, tile comparison, dirty rectangles and spreading a
capture over several timer steps (no Blender needed)."""

from __future__ import annotations

import warnings

import numpy as np
import pytest

from durty_cloth_tool_link import pixels
from durty_cloth_tool_link.pixels import Conversion

FLOAT_DIFFUSE = Conversion(4, encode_srgb=True, unpremultiply=True, sanitize=True)


def blender_floats(rgba_top_down: np.ndarray) -> np.ndarray:
    """What Blender's Image.pixels holds for an RGBA8 image given top to bottom: value / 255, rows bottom up."""
    return (rgba_top_down[::-1].astype(np.float32) / np.float32(255.0)).reshape(-1)


def random_image(width: int, height: int, seed: int = 1) -> np.ndarray:
    return np.random.default_rng(seed).integers(0, 256, size=(height, width, 4), dtype=np.uint8)


def test_every_byte_level_survives_the_round_trip():
    levels = np.repeat(np.arange(256, dtype=np.uint8), 4).reshape(1, 256, 4)
    target = np.empty(256 * 4, np.uint8)
    pixels.to_rgba8(blender_floats(levels), target, 256, 1)
    assert np.array_equal(target, levels.reshape(-1))


def test_rows_are_flipped_to_top_down():
    # Blender rows bottom up: row 0 (bottom) is 10s, row 1 is 20s, row 2 (top) is 30s.
    source = np.array([[10] * 8, [20] * 8, [30] * 8], dtype=np.float32).reshape(-1) / 255
    target = np.empty(2 * 3 * 4, np.uint8)
    pixels.to_rgba8(source.astype(np.float32), target, 2, 3)
    assert target.reshape(3, 2, 4)[:, 0, 0].tolist() == [30, 20, 10]


@pytest.mark.parametrize("height", [1, 255, 256, 257, 600])
def test_flip_is_exact_across_conversion_bands(height):
    image = random_image(37, height, seed=height)
    target = np.empty(image.size, np.uint8)
    pixels.to_rgba8(blender_floats(image), target, 37, height)
    assert np.array_equal(target.reshape(image.shape), image)


def test_rgb_and_grey_images_get_opaque_alpha():
    target = np.empty(4, np.uint8)
    pixels.to_rgba8(np.array([0.0, 0.5, 1.0], dtype=np.float32), target, 1, 1, Conversion(3))
    assert target.tolist() == [0, 128, 255, 255]
    pixels.to_rgba8(np.array([0.25], dtype=np.float32), target, 1, 1, Conversion(1))
    assert target.tolist() == [64, 64, 64, 255]


def test_the_srgb_lookup_matches_the_transfer_function():
    values = np.random.default_rng(2).random(200_000, dtype=np.float32)
    values[:5] = [0.0, 1.0, 0.0031308, 0.5, 0.2140411]
    linear = np.repeat(values, 4)
    target = np.empty(linear.size, np.uint8)
    pixels.to_rgba8(linear, target, values.size, 1, Conversion(4, encode_srgb=True))
    encoded = target.reshape(-1, 4)[:, 0].astype(int)
    expected = np.floor(pixels.srgb_reference(values) * 255 + 0.5).astype(int)
    assert np.abs(encoded - expected).max() <= 1
    assert np.mean(encoded == expected) > 0.995  # off by one only right at a rounding boundary
    assert encoded[:2].tolist() == [0, 255]
    alpha = target.reshape(-1, 4)[:, 3].astype(int)
    assert np.abs(alpha - values.astype(np.float64) * 255).max() <= 0.5 + 1e-3  # alpha is not encoded


def test_premultiplied_float_colour_is_divided_by_alpha():
    # Blender stores painted float pixels premultiplied: pure red at half alpha reads (0.5, 0, 0, 0.5).
    premultiplied = np.array([0.5, 0.0, 0.0, 0.5, 0.1, 0.05, 0.02, 0.5, 0.3, 0.3, 0.3, 0.0], dtype=np.float32)
    target = np.empty(12, np.uint8)
    pixels.to_rgba8(premultiplied, target, 3, 1, FLOAT_DIFFUSE)
    rgba = target.reshape(3, 4)
    assert rgba[0].tolist() == [255, 0, 0, 128]
    expected = np.floor(pixels.srgb_reference(np.array([0.2, 0.1, 0.04])) * 255 + 0.5).astype(int).tolist()
    assert rgba[1, :3].tolist() == expected and rgba[1, 3] == 128
    assert rgba[2, 3] == 0  # fully transparent: colour is left alone, not divided by zero


def test_nan_and_infinity_do_not_break_the_conversion():
    source = np.array([np.nan, np.inf, -np.inf, 0.5], dtype=np.float32)
    target = np.empty(4, np.uint8)
    pixels.to_rgba8(source, target, 1, 1, Conversion(4, sanitize=True))
    assert target.tolist() == [0, 255, 0, 128]


def test_infinite_colour_without_alpha_converts_without_warnings():
    # Infinity times a zero inverse alpha is NaN; it must neither warn nor reach the bytes.
    source = np.array([np.inf, -np.inf, np.nan, 0.0, np.inf, 0.5, 0.25, 1.0], dtype=np.float32)
    target = np.empty(8, np.uint8)
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        pixels.to_rgba8(source, target, 2, 1, FLOAT_DIFFUSE)
    rgba = target.reshape(2, 4)
    assert rgba[0, 3] == 0 and rgba[1, 3] == 255
    assert rgba[1, :3].tolist() == [255, 188, 137]  # an opaque pixel: infinity is white, the rest is encoded


def test_mismatched_buffers_are_refused():
    with pytest.raises(ValueError):
        pixels.to_rgba8(np.zeros(15, np.float32), np.zeros(16, np.uint8), 2, 2)
    with pytest.raises(ValueError):
        pixels.to_rgba8(np.zeros(8, np.float32), np.zeros(16, np.uint8), 2, 2, Conversion(2))


@pytest.mark.parametrize(
    "target, is_float, space, is_data, alpha, encode, unpremultiply, warns",
    [
        ("diffuse", False, "sRGB", False, "STRAIGHT", False, False, False),
        ("diffuse", False, "Linear Rec.709", False, "STRAIGHT", True, False, False),
        ("diffuse", False, "Non-Color", True, "STRAIGHT", False, False, True),
        ("diffuse", False, "ACES2065-1", False, "STRAIGHT", False, False, True),
        ("diffuse", True, "Linear Rec.709", False, "STRAIGHT", True, True, False),
        ("diffuse", True, "Linear Rec.709", False, "PREMUL", True, True, False),
        # Blender keeps these float pixels as they are: dividing by alpha would brighten them.
        ("diffuse", True, "Linear Rec.709", False, "CHANNEL_PACKED", True, False, False),
        ("diffuse", True, "sRGB", False, "NONE", True, False, False),
        ("diffuse", True, "Non-Color", True, "STRAIGHT", False, False, True),
        ("normal", False, "sRGB", False, "STRAIGHT", False, False, False),
        ("normal", True, "Non-Color", True, "STRAIGHT", False, False, False),
        ("normal", True, "Non-Color", True, "CHANNEL_PACKED", False, False, False),
        ("normal", True, "sRGB", False, "STRAIGHT", True, True, False),
        ("specular", True, "Linear Rec.709", False, "STRAIGHT", False, True, False),
        ("specular", True, "Filmic Log", False, "STRAIGHT", False, True, True),
    ],
)
def test_colour_plans(target, is_float, space, is_data, alpha, encode, unpremultiply, warns):
    plan = pixels.colour_plan(target, 4, is_float, space, is_data, alpha)
    assert plan.conversion.encode_srgb is encode
    assert plan.conversion.unpremultiply is unpremultiply
    assert plan.conversion.sanitize is is_float
    assert (plan.warning is not None) is warns


def test_changed_tiles_marks_only_the_tile_with_the_change():
    width, height = 100, 70  # not a multiple of the tile size
    known = random_image(width, height).reshape(-1)
    current = known.copy()
    assert not pixels.changed_tiles(current, known, width, height, 32).any()
    current.reshape(height, width, 4)[69, 99, 2] ^= 1  # last pixel, one channel
    grid = pixels.changed_tiles(current, known, width, height, 32)
    assert grid.shape == (3, 4)
    assert np.argwhere(grid).tolist() == [[2, 3]]


def test_tiles_become_clipped_rectangles():
    grid = np.zeros((3, 4), bool)
    grid[2, 3] = True
    assert pixels.tiles_to_rects(grid, 32, 100, 70) == [(96, 64, 4, 6)]
    assert pixels.tiles_to_rects(grid[2:], 32, 100, 6, y_offset=64) == [(96, 64, 4, 6)]


def test_runs_merge_horizontally_and_vertically():
    grid = np.array(
        [
            [1, 1, 0, 0, 1],
            [1, 1, 0, 0, 0],
            [0, 0, 0, 1, 0],
        ],
        dtype=bool,
    )
    rects = pixels.tiles_to_rects(grid, 10, 50, 30)
    assert rects == [(0, 0, 20, 20), (40, 0, 10, 10), (30, 20, 10, 10)]
    covered = np.zeros((30, 50), bool)
    for x, y, w, h in rects:
        covered[y : y + h, x : x + w] = True
    assert np.array_equal(covered, np.kron(grid, np.ones((10, 10), bool)))


def test_limit_rects_merges_the_cheapest_pairs_and_covers_everything():
    rects = [(0, 0, 8, 8), (8, 0, 8, 8), (100, 100, 8, 8), (108, 100, 8, 8), (0, 200, 8, 8), (300, 0, 8, 8)]
    merged = pixels.limit_rects(rects, 4)
    assert len(merged) == 4
    assert (0, 0, 16, 8) in merged and (100, 100, 16, 8) in merged  # neighbours merge first
    for x, y, w, h in rects:
        assert any(mx <= x and my <= y and x + w <= mx + mw and y + h <= my + mh for mx, my, mw, mh in merged)
    assert pixels.limit_rects(rects[:3], 4) == sorted(rects[:3], key=lambda r: (r[1], r[0]))


def test_too_many_rectangles_collapse_into_their_bounding_box():
    grid = np.zeros((10, 10), bool)
    grid[::2, ::2] = True  # 25 separate tiles
    rects = pixels.tiles_to_rects(grid, 8, 80, 80, max_rects=24)
    assert rects == [(0, 0, 72, 72)]
    assert pixels.tiles_to_rects(np.zeros((2, 2), bool), 8, 16, 16) == []


class FakeImage:
    """Stands in for a Blender image: holds RGBA8 top-down pixels and reads them like Image.pixels does."""

    def __init__(self, width: int, height: int) -> None:
        self.width, self.height = width, height
        self.rgba = random_image(width, height, seed=7)
        self.reads = 0

    def read_into(self, buffer: np.ndarray) -> None:
        self.reads += 1
        buffer[:] = blender_floats(self.rgba)


def test_stream_buffers_report_changes_and_serve_the_newest_pixels():
    image = FakeImage(200, 150)
    buffers = pixels.StreamBuffers(200, 150, image.read_into, tile=64)
    assert buffers.baseline() == (0, 0, 200, 150)
    assert buffers.known_rgba8() == image.rgba.tobytes()
    assert buffers.check() == []

    image.rgba[140:145, 10:12] = 7  # near the bottom, top-down coordinates
    assert buffers.check() == [(0, 128, 64, 22)]
    assert buffers.pixels(10, 140, 2, 5) == bytes([7]) * 2 * 5 * 4
    assert buffers.pixels(0, 0, 200, 150) == image.rgba.tobytes()

    image.rgba[0, 199] = 1
    image.rgba[149, 0] = 2
    assert buffers.check() == [(192, 0, 8, 64), (0, 128, 64, 22)]
    assert buffers.pixels(199, 0, 1, 1) == bytes([1, 1, 1, 1])
    assert buffers.check() == []


@pytest.mark.parametrize("conversion, expected_steps", [(Conversion(), 30), (FLOAT_DIFFUSE, 32)],
                         ids=["bytes", "converted"])
def test_a_capture_is_spread_over_steps_of_one_unit(conversion, expected_steps):
    image = FakeImage(96, 300)
    buffers = pixels.StreamBuffers(96, 300, image.read_into, conversion, tile=32, unit_pixels=32 * 32)
    buffers.baseline()
    image.rgba[0, 0] = 1
    image.rgba[299, 95] = 2
    reads = image.reads
    buffers.begin()
    assert image.reads == reads + 1 and buffers.busy
    found, steps = [], 0
    while buffers.busy:
        found += buffers.step(budget=0.0)  # a zero budget still works through one unit
        steps += 1
    assert steps == expected_steps  # 10 tile rows of three one-tile units (plus one per changed tile to convert)
    assert image.reads == reads + 1  # the image is read once per capture
    assert found == [(0, 0, 32, 32), (64, 288, 32, 12)]
    if conversion == Conversion():
        assert buffers.known_rgba8() == image.rgba.tobytes()


def test_slow_units_shrink_until_a_step_fits_its_budget():
    image = FakeImage(1024, 128)
    now = [0.0]

    def clock() -> float:
        now[0] += 0.003  # every reading of the clock costs time, so each unit looks slow
        return now[0]

    buffers = pixels.StreamBuffers(1024, 128, image.read_into, tile=64, clock=clock)
    buffers.baseline()
    first = buffers.unit_pixels
    buffers.begin()
    buffers.step(budget=0.006)
    assert buffers.unit_pixels < first
    while buffers.busy:
        buffers.step(budget=0.006)
    assert buffers.unit_pixels == 64 * 64  # never below one tile


def test_a_change_of_one_float_bit_is_found():
    values = np.random.default_rng(4).random(70 * 70 * 4, dtype=np.float32)
    buffers = pixels.StreamBuffers(70, 70, lambda buffer: np.copyto(buffer, values), FLOAT_DIFFUSE, tile=64)
    buffers.baseline()
    index = ((69 - 3) * 70 + 66) * 4  # top-down row 3, column 66, red (Blender rows go bottom up)
    values[index] = np.nextafter(values[index], np.float32(2))
    assert buffers.check() == [(64, 0, 6, 64)]


def test_a_one_pixel_tile_keeps_its_own_alpha():
    image = FloatImage(65, 65)
    buffers = pixels.StreamBuffers(65, 65, image.read_into, FLOAT_DIFFUSE, tile=64)
    buffers.baseline()
    image.straight[64, 64] = [1.0, 0.0, 0.0, 0.5]  # the bottom-right corner is a tile of its own
    assert buffers.check() == [(64, 64, 1, 1)]
    assert buffers.pixels(64, 64, 1, 1) == bytes([255, 0, 0, 128])


def test_released_buffers_hold_no_pixels():
    buffers = pixels.StreamBuffers(256, 256, lambda buffer: buffer.fill(0.5), FLOAT_DIFFUSE)
    buffers.baseline()
    assert buffers.nbytes > 256 * 256 * 8
    buffers.release()
    assert buffers.nbytes == 0 and not buffers.busy


class FloatImage:
    """A painted float image: premultiplied linear floats, rows bottom up, as Image.pixels returns them."""

    def __init__(self, width: int, height: int) -> None:
        rng = np.random.default_rng(11)
        self.width, self.height = width, height
        self.straight = rng.random((height, width, 4), dtype=np.float32)
        self.straight[..., 3] = np.clip(self.straight[..., 3], 0.2, 1.0)

    def read_into(self, buffer: np.ndarray) -> None:
        premultiplied = self.straight.copy()
        premultiplied[..., :3] *= premultiplied[..., 3:4]
        buffer[:] = premultiplied[::-1].reshape(-1)

    def expected(self) -> bytes:
        rgba = np.empty(self.straight.shape, np.uint8)
        rgba[..., :3] = np.floor(pixels.srgb_reference(self.straight[..., :3]) * 255 + 0.5)
        rgba[..., 3] = np.floor(self.straight[..., 3] * 255 + 0.5)
        return rgba.tobytes()


def test_float_images_convert_only_the_changed_tiles():
    image = FloatImage(130, 140)
    buffers = pixels.StreamBuffers(130, 140, image.read_into, FLOAT_DIFFUSE, tile=64)
    buffers.baseline()
    known = np.frombuffer(buffers.known_rgba8(), np.uint8)
    assert np.abs(known.astype(int) - np.frombuffer(image.expected(), np.uint8)).max() <= 1
    assert buffers.check() == []
    image.straight[70:75, 129] = [1.0, 0.0, 0.0, 0.5]  # top-down rows 70..74, last column
    assert buffers.check() == [(128, 64, 2, 64)]
    assert buffers.pixels(129, 70, 1, 1) == bytes([255, 0, 0, 128])
    after = np.frombuffer(buffers.known_rgba8(), np.uint8)
    assert np.abs(after.astype(int) - np.frombuffer(image.expected(), np.uint8)).max() <= 1


def test_stream_buffers_refuse_rectangles_outside_the_image():
    buffers = pixels.StreamBuffers(4, 4, lambda buffer: buffer.fill(0))
    buffers.baseline()
    with pytest.raises(ValueError):
        buffers.pixels(3, 3, 2, 1)
