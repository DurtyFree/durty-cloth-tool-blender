# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2026 Schmid Software Solutions (https://schmid-software.de)
# Copyright (c) 2026 muto
"""Combine Materials' Pack Without Baking, without Blender: each material's image goes into its own square of one
square texture, the UVs of its faces move into that square, and the pixels between the images take the colours next
to them, so no dark seam bleeds in when the game filters or shrinks the texture.

Pixel arrays are ``(rows, columns, channels)`` float arrays with the bottom row first, as Blender stores an image's
pixels, so a square's ``(x, y)`` is its lower left corner and UV ``(0, 0)`` is the texture's lower left corner.
Nothing here imports Blender; numpy does the arithmetic, so the tests run without Blender. The grid and the gap fill
follow Muto Cloth by muto.
"""

from __future__ import annotations

from typing import Any, NamedTuple, Sequence, Tuple, Union

import numpy as np

#: Combine Materials' methods: Automatic, Bake (Cycles) and Pack Without Baking.
METHODS = ("auto", "bake", "pack")
#: The smallest square an image gets (pixels), unless the texture size leaves less: small images are not packed
#: into squares too small to filter well.
MIN_TILE = 256


class AtlasLayout(NamedTuple):
    """Where the images go: the texture's side ``size`` in pixels, ``grid`` squares of ``tile`` pixels per side, the
    ``pad`` pixels at each square's edge that the gap fill gives the image's edge colour (so the game's filtering
    never reaches the next image), and each image's square as ``(x, y, width, height)`` in pixels."""

    size: int
    grid: int
    tile: int
    pad: int
    tiles: Tuple[Tuple[int, int, int, int], ...]


def _power_of_two_at_most(value: int) -> int:
    return 1 << max(0, int(value).bit_length() - 1)


def atlas_layout(sizes: Sequence[Tuple[int, int]], limit: int) -> AtlasLayout:
    """The atlas for images of ``sizes`` (width, height) within a texture of ``limit`` pixels: a grid of a power of
    two squares per side, as few as hold every image, each square a power of two as large as the largest image
    (at least :data:`MIN_TILE`) where the texture size leaves room. The texture is square and a power of two, and
    never larger than ``limit``; image ``i`` goes into square ``i``, row by row from the bottom left."""
    count = max(1, len(sizes))
    grid = 1
    while grid * grid < count:
        grid *= 2
    largest = max((max(int(w), int(h)) for w, h in sizes), default=MIN_TILE)
    room = max(1, int(limit) // grid)
    tile = _power_of_two_at_most(min(max(largest, MIN_TILE), room))
    pad = max(2, tile // 128) if tile >= 16 else 0
    tiles = tuple(((index % grid) * tile, (index // grid) * tile, tile, tile) for index in range(len(sizes)))
    return AtlasLayout(grid * tile, grid, tile, pad, tiles)


def blank_atlas(layout: AtlasLayout, channels: int = 4) -> Tuple[np.ndarray, np.ndarray]:
    """The atlas's pixels (all 0) and its mask of pixels that hold an image (none yet)."""
    return (np.zeros((layout.size, layout.size, channels), dtype=np.float32),
            np.zeros((layout.size, layout.size), dtype=bool))


def resample(image: Any, rows: int, columns: int) -> np.ndarray:
    """``image`` (bottom row first) scaled to ``rows`` by ``columns`` pixels: averaged over whole blocks first where
    it shrinks to half or less, then sampled between the four nearest pixels."""
    image = np.asarray(image, dtype=np.float32)
    if image.ndim == 2:
        image = image[..., None]
    step_y, step_x = max(1, image.shape[0] // max(1, rows)), max(1, image.shape[1] // max(1, columns))
    if step_y > 1 or step_x > 1:
        height, width = image.shape[0] // step_y * step_y, image.shape[1] // step_x * step_x
        image = image[:height, :width].reshape(height // step_y, step_y, width // step_x, step_x, -1).mean(axis=(1, 3))
    if image.shape[:2] == (rows, columns):
        return image.astype(np.float32)

    def axis(target: int, source: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        place = np.clip((np.arange(target) + 0.5) * source / target - 0.5, 0.0, source - 1)
        low = np.floor(place).astype(np.int64)
        return low, np.minimum(low + 1, source - 1), (place - low).astype(np.float32)

    y0, y1, fy = axis(rows, image.shape[0])
    x0, x1, fx = axis(columns, image.shape[1])
    fy, fx = fy[:, None, None], fx[None, :, None]
    lower = image[y0][:, x0] * (1 - fx) + image[y0][:, x1] * fx
    upper = image[y1][:, x0] * (1 - fx) + image[y1][:, x1] * fx
    return (lower * (1 - fy) + upper * fy).astype(np.float32)


def place_image(pixels: np.ndarray, valid: np.ndarray, layout: AtlasLayout, index: int,
                image: Union[np.ndarray, Sequence[float]]) -> None:
    """Puts ``image`` (pixels, bottom row first, or one colour for a material without an image) into square ``index``
    of the atlas, inside its padding, and marks those pixels as holding an image."""
    x, y, width, height = layout.tiles[index]
    pad = layout.pad
    rows, columns = height - 2 * pad, width - 2 * pad
    target = (slice(y + pad, y + pad + rows), slice(x + pad, x + pad + columns))
    channels = pixels.shape[2]
    source = np.asarray(image, dtype=np.float32)
    if source.ndim == 1:
        colour = np.zeros(channels, dtype=np.float32)
        colour[:min(channels, len(source))] = source[:channels]
        if len(source) < channels:
            colour[len(source):] = 1.0
        pixels[target] = colour
    else:
        scaled = resample(source, rows, columns)
        if scaled.shape[2] < channels:  # an image without alpha is opaque
            scaled = np.concatenate([scaled, np.ones((rows, columns, channels - scaled.shape[2]), np.float32)], 2)
        pixels[target] = scaled[..., :channels]
    valid[target] = True


def fill_gaps(pixels: Any, valid: Any) -> np.ndarray:
    """``pixels`` with every pixel outside ``valid`` (a ``(rows, columns)`` mask) taking the colours of the valid
    pixels around it, the nearer ones counting most: the valid pixels are averaged into ever coarser levels (push),
    and each gap takes its colour from the finest level that holds any (pull). Valid pixels keep their values; without
    any valid pixel the pixels are returned as they are."""
    image = np.array(pixels, dtype=np.float32)
    valid = np.asarray(valid, dtype=bool)
    if valid.all() or not valid.any():
        return image
    weight = valid.astype(np.float32)
    levels = [(image * weight[..., None], weight)]
    colour = levels[0][0]
    while min(weight.shape) > 1:
        rows, columns = (weight.shape[0] + 1) // 2, (weight.shape[1] + 1) // 2
        padded = np.zeros((rows * 2, columns * 2, colour.shape[2]), dtype=np.float32)
        padded[:colour.shape[0], :colour.shape[1]] = colour
        padded_weight = np.zeros((rows * 2, columns * 2), dtype=np.float32)
        padded_weight[:weight.shape[0], :weight.shape[1]] = weight
        colour = padded.reshape(rows, 2, columns, 2, -1).sum(axis=(1, 3))
        weight = padded_weight.reshape(rows, 2, columns, 2).sum(axis=(1, 3))
        levels.append((colour, weight))
    colour, weight = levels[-1]
    average = colour / np.maximum(weight, 1e-12)[..., None]
    for colour, weight in reversed(levels[:-1]):
        above = np.repeat(np.repeat(average, 2, axis=0), 2, axis=1)[:weight.shape[0], :weight.shape[1]]
        own = colour / np.maximum(weight, 1e-12)[..., None]
        share = np.clip(weight, 0.0, 1.0)[..., None]  # a cell with some valid pixels mixes its own colour in
        average = own * share + above * (1.0 - share)
    image[~valid] = average[~valid]
    return image


#: How far a UV point may lie beyond its image (in UV units) before it counts as a repeating texture.
OUTSIDE_TOLERANCE = 0.01


def remap_uvs(uv: Any, image: Any, layout: AtlasLayout) -> Tuple[np.ndarray, int]:
    """Each UV point (``(points, 2)``) moved into the square of its image (``image``, one index per point), onto the
    pixels :func:`place_image` filled, and how many points lay beyond their image (a repeating texture), which go to
    the image's edge."""
    uv = np.nan_to_num(np.asarray(uv, dtype=np.float64).reshape(-1, 2))
    image = np.asarray(image, dtype=np.int64)
    outside = outside_count(uv)
    tiles = np.asarray(layout.tiles, dtype=np.float64).reshape(-1, 4)
    corner = tiles[image, :2] + layout.pad
    inner = tiles[image, 2:] - 2 * layout.pad
    return (corner + np.clip(uv, 0.0, 1.0) * inner) / layout.size, outside


def choose_method(method: str, images: Sequence[int], plain: bool = True, outside: int = 0) -> str:
    """``"pack"`` or ``"bake"`` for Combine Materials' ``method`` (one of :data:`METHODS`), given how many images each
    material of the garment uses. Automatic packs when there are several materials and each has exactly one image,
    read ``plain`` through the garment's UV map (no mapping, no other UV map) with no UV point ``outside`` the image;
    it bakes otherwise (a normal map besides the colour, a plain colour, a repeating texture, one material whose
    layout is better packed and baked)."""
    if method in ("bake", "pack"):
        return method
    packable = len(images) >= 2 and all(count == 1 for count in images) and plain and outside == 0
    return "pack" if packable else "bake"


def outside_count(uv: Any) -> int:
    """How many UV points (``(points, 2)``) lie beyond the image they read, as a repeating texture's do."""
    uv = np.nan_to_num(np.asarray(uv, dtype=np.float64).reshape(-1, 2))
    return int(((uv < -OUTSIDE_TOLERANCE) | (uv > 1.0 + OUTSIDE_TOLERANCE)).any(axis=1).sum())


def linear_to_srgb(values: Any) -> np.ndarray:
    """Linear colour values in the sRGB encoding the combined texture stores (a float image holds linear values)."""
    values = np.clip(np.asarray(values, dtype=np.float32), 0.0, 1.0)
    return np.where(values <= 0.0031308, values * 12.92, 1.055 * np.power(values, 1.0 / 2.4) - 0.055).astype(np.float32)
