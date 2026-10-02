# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2026 Schmid Software Solutions (https://schmid-software.de)
"""Pixel capture for texture streaming: Blender float pixels to RGBA8, change detection and dirty rectangles.

Blender's ``Image.pixels`` holds floats with the first row at the bottom. Creator Link frames carry RGBA8 rows
from top to bottom. :class:`StreamBuffers` reads the image into a preallocated float buffer and then works
through it in small units (one tile row high, as wide as fits a few milliseconds), so one Blender timer step
stays short:

* byte images without colour conversion: the unit is converted (with the vertical flip) and compared with the
  pixels already known, tile by tile;
* everything else (float images, colour conversion): each tile of the unit is fingerprinted from its raw values,
  and only the tiles whose fingerprint changed are converted, in steps of their own. The fingerprint is a
  weighted sum with random odd weights, so a change of any single value always changes it.

Painted float images hold premultiplied colour; it is divided by alpha before encoding. Linear colour is
encoded as sRGB through a lookup table. Only numpy (bundled with Blender) is needed; nothing here imports
Blender.
"""

from __future__ import annotations

import time
from collections import deque
from typing import Callable, Deque, Dict, List, NamedTuple, Optional, Sequence, Tuple

import numpy as np

Rect = Tuple[int, int, int, int]

#: Tile edge for change detection. Smaller tiles give tighter rectangles but cost more to compare.
DEFAULT_TILE = 64
#: Rows converted at once by the whole-image helper.
BAND_ROWS = 256
#: Starting unit size in pixels: byte images compare cheaply; conversion costs about ten times more per pixel.
#: Units then grow or shrink so each takes about a quarter of the step budget.
UNIT_PIXELS_DIRECT = 1 << 18
UNIT_PIXELS_CONVERTED = 1 << 16
#: More rectangles than this from one step are merged.
MAX_RECTS = 32
#: Entries of the linear to sRGB lookup table (the error stays below a tenth of a byte step).
LUT_SIZE = 65536

_SRGB_LUT: Optional[np.ndarray] = None


def srgb_reference(linear: np.ndarray) -> np.ndarray:
    """The sRGB transfer function in float64 (values clipped to 0..1). Used to build the lookup table."""
    value = np.clip(np.asarray(linear, dtype=np.float64), 0.0, 1.0)
    return np.where(value <= 0.0031308, value * 12.92, 1.055 * np.power(value, 1.0 / 2.4) - 0.055)


def srgb_lut() -> np.ndarray:
    """Linear 0..1 in ``LUT_SIZE`` steps to sRGB bytes."""
    global _SRGB_LUT
    if _SRGB_LUT is None:
        steps = np.linspace(0.0, 1.0, LUT_SIZE)
        _SRGB_LUT = np.floor(srgb_reference(steps) * 255.0 + 0.5).astype(np.uint8)
    return _SRGB_LUT


class Conversion(NamedTuple):
    """How Blender's values become RGBA8. ``encode_srgb``: colour is linear and must be encoded as sRGB.
    ``unpremultiply``: colour is premultiplied by alpha (painted float images). ``sanitize``: NaN and infinity
    can occur (float images)."""

    channels: int = 4
    encode_srgb: bool = False
    unpremultiply: bool = False
    sanitize: bool = False


def _work_buffer(scratch: Optional[np.ndarray], rows: int, width: int) -> np.ndarray:
    """A contiguous (rows, width, 4) float32 view of ``scratch`` (contiguous arrays are many times faster)."""
    size = rows * width * 4
    if scratch is None or scratch.size < size:
        return np.empty((rows, width, 4), np.float32)
    return scratch.reshape(-1)[:size].reshape(rows, width, 4)


def convert(source: np.ndarray, target: np.ndarray, conversion: Conversion, scratch: Optional[np.ndarray] = None) -> None:
    """Converts ``source`` (rows, width, channels) float32, already in the target's row order, into ``target``
    (rows, width, 4) uint8. Values round to the nearest byte, so byte images (``value / 255``) come back exactly.

    Every operation works on whole contiguous pixels; per-channel views are avoided because numpy is far slower
    on them.
    """
    rows, width = source.shape[0], source.shape[1]
    work = _work_buffer(scratch, rows, width)
    channels = conversion.channels
    if channels == 4:
        np.copyto(work, source)
    else:
        np.copyto(work[..., :3], source[..., :3] if channels == 3 else source[..., :1])
        work[..., 3] = 1.0
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        if conversion.sanitize:
            np.clip(work, -1e30, 1e30, out=work)  # infinity becomes large but finite
            np.copyto(work, 0.0, where=np.isnan(work))
        alpha = None
        if conversion.encode_srgb or (conversion.unpremultiply and channels == 4):
            alpha = work[..., 3].copy()  # a copy: a view would change with the colour below
        if conversion.unpremultiply and channels == 4:
            inverse = np.zeros_like(alpha)
            np.divide(1.0, alpha, out=inverse, where=alpha > 0.0)
            np.multiply(work, inverse[..., None], out=work)  # alpha becomes 1 here and is restored below
        if conversion.encode_srgb:
            np.clip(work, 0.0, 1.0, out=work)
            np.multiply(work, LUT_SIZE - 1, out=work)
            np.add(work, 0.5, out=work)
            encoded = srgb_lut()[work.astype(np.uint16)]
        else:
            if alpha is not None:
                work[..., 3] = alpha
            np.multiply(work, 255.0, out=work)
            np.add(work, 0.5, out=work)
            np.clip(work, 0.0, 255.0, out=work)
            np.copyto(target, work, casting="unsafe")
            return
        np.multiply(alpha, 255.0, out=alpha)
        np.add(alpha, 0.5, out=alpha)
        np.clip(alpha, 0.0, 255.0, out=alpha)
        np.copyto(encoded[..., 3], alpha, casting="unsafe")  # alpha is linear, never encoded
    np.copyto(target, encoded)


def to_rgba8(source: np.ndarray, target: np.ndarray, width: int, height: int, conversion: Conversion = Conversion()) -> None:
    """Converts a whole image: ``source`` holds Blender's flat float pixels (rows bottom to top), ``target``
    receives flat RGBA8 rows top to bottom."""
    channels = conversion.channels
    if channels not in (1, 3, 4):
        raise ValueError("images with 1, 3 or 4 channels are supported")
    if source.size != width * height * channels or target.size != width * height * 4:
        raise ValueError("buffer sizes do not match the image size")
    rows_in = source.reshape(height, width, channels)
    rows_out = target.reshape(height, width, 4)
    scratch = np.empty(min(BAND_ROWS, height) * width * 4, np.float32)
    for top in range(0, height, BAND_ROWS):
        rows = min(BAND_ROWS, height - top)
        convert(rows_in[height - top - rows : height - top][::-1], rows_out[top : top + rows], conversion, scratch)


def tile_runs(changed_columns: np.ndarray) -> List[Tuple[int, int]]:
    """Runs ``(first, end)`` of true tiles in one tile row."""
    runs = []
    column, count = 0, changed_columns.shape[0]
    while column < count:
        if changed_columns[column]:
            start = column
            while column < count and changed_columns[column]:
                column += 1
            runs.append((start, column))
        else:
            column += 1
    return runs


def changed_tiles(current: np.ndarray, known: np.ndarray, width: int, height: int, tile: int = DEFAULT_TILE) -> np.ndarray:
    """A boolean grid (tile rows by tile columns) that is true where any pixel differs. Both buffers are RGBA8
    with ``width * height * 4`` bytes."""
    if tile < 1:
        raise ValueError("tile must be positive")
    now = current.view(np.uint32).reshape(height, width)
    before = known.view(np.uint32).reshape(height, width)
    columns = np.arange(0, width, tile)
    grid = np.zeros(((height + tile - 1) // tile, len(columns)), dtype=bool)
    for row, top in enumerate(range(0, height, tile)):
        differs = np.not_equal(now[top : top + tile], before[top : top + tile]).any(axis=0)
        grid[row] = np.logical_or.reduceat(differs, columns)
    return grid


def tiles_to_rects(grid: np.ndarray, tile: int, width: int, height: int, max_rects: int = MAX_RECTS,
                   y_offset: int = 0, x_offset: int = 0) -> List[Rect]:
    """Rectangles ``(x, y, w, h)`` covering the true tiles of ``grid``, clipped to ``width`` and ``height`` (the
    area the grid covers, starting at the offsets). Runs of changed tiles in a tile row become one rectangle, and
    identical runs in consecutive tile rows merge. More than ``max_rects`` rectangles collapse into their
    bounding box."""
    rects: List[Rect] = []
    open_runs: dict = {}

    def close(run: Tuple[int, int], first_row: int, end_row: int) -> None:
        x = run[0] * tile
        y = first_row * tile
        rects.append((x + x_offset, y + y_offset, min(width, run[1] * tile) - x, min(height, end_row * tile) - y))

    for row_index in range(grid.shape[0]):
        still_open = {}
        for run in tile_runs(grid[row_index]):
            still_open[run] = open_runs.pop(run, row_index)
        for run, first in open_runs.items():
            close(run, first, row_index)
        open_runs = still_open
    for run, first in open_runs.items():
        close(run, first, grid.shape[0])
    rects.sort(key=lambda r: (r[1], r[0]))
    if len(rects) > max_rects:
        return [bounding_rect(rects)]
    return rects


def bounding_rect(rects: Sequence[Rect]) -> Rect:
    x0 = min(r[0] for r in rects)
    y0 = min(r[1] for r in rects)
    x1 = max(r[0] + r[2] for r in rects)
    y1 = max(r[1] + r[3] for r in rects)
    return (x0, y0, x1 - x0, y1 - y0)


def limit_rects(rects: Sequence[Rect], limit: int) -> List[Rect]:
    """At most ``limit`` rectangles covering ``rects``: the pair whose union adds the least area is merged first
    (fewer, larger frames when many small areas changed at once)."""
    merged = list(rects)
    while len(merged) > limit:
        best = None
        for i in range(len(merged)):
            for j in range(i + 1, len(merged)):
                union = bounding_rect((merged[i], merged[j]))
                cost = union[2] * union[3] - merged[i][2] * merged[i][3] - merged[j][2] * merged[j][3]
                if best is None or cost < best[0]:
                    best = (cost, i, j, union)
        assert best is not None
        _, i, j, union = best
        merged = [r for k, r in enumerate(merged) if k not in (i, j)] + [union]
    return sorted(merged, key=lambda r: (r[1], r[0]))


class StreamBuffers:
    """Preallocated buffers for one streamed image, with captures spread over several steps.

    ``read_into(buffer)`` fills a float32 buffer of ``width * height * channels`` values in Blender's layout (in
    Blender: ``image.pixels.foreach_get``). :meth:`begin` reads the image (the one step that cannot be split);
    :meth:`step` then works through it until :attr:`busy` is false. ``begin(full=True)`` converts everything
    (the first capture); otherwise only what changed is reported.

    The work comes in units one tile row high. Byte images are converted and compared unit by unit. Converted
    images are first fingerprinted unit by unit; the tiles whose fingerprint changed are queued and converted in
    chunks of their own, so a capture where everything changed still keeps every step short. Each kind of work
    sizes its units by how long the last one took, and a step stops before a unit that would overrun it.

    Memory: the float buffer (4 bytes per value), the RGBA8 pixels (4 bytes per pixel), one tile row of working
    space and, for converted images, the weights of the fingerprints (8 bytes per value of one tile row).
    """

    def __init__(
        self,
        width: int,
        height: int,
        read_into: Callable[[np.ndarray], None],
        conversion: Conversion = Conversion(),
        *,
        tile: int = DEFAULT_TILE,
        unit_pixels: Optional[int] = None,
        clock: Callable[[], float] = time.perf_counter,
    ) -> None:
        channels = conversion.channels
        if channels not in (1, 3, 4):
            raise ValueError("images with 1, 3 or 4 channels are supported")
        self.width = width
        self.height = height
        self.conversion = conversion
        self.tile = tile
        self.read_into = read_into
        self.clock = clock
        self.last_read_cost = 0.0
        self.last_cycle_cost = 0.0
        self.captures = 0
        self._direct = channels == 4 and not (conversion.encode_srgb or conversion.unpremultiply or conversion.sanitize)
        self._adaptive = unit_pixels is None
        self._min_unit = tile * tile
        self._max_unit = tile * (-(-width // tile) * tile)
        start = unit_pixels or (UNIT_PIXELS_DIRECT if self._direct else UNIT_PIXELS_CONVERTED)
        first = max(self._min_unit, min(self._max_unit, start))
        #: Pixels per unit for each kind of work: "full" (byte images: convert), "scan" (byte images: convert and
        #: compare; converted images: fingerprint) and "convert" (converted images: convert changed tiles).
        self._units: Dict[str, int] = {"full": first, "scan": first, "convert": first}
        self._costs: Dict[str, float] = {}
        self._raw = np.empty(width * height * channels, np.float32)
        self._known = np.zeros(width * height * 4, np.uint8)
        self._scratch = np.empty(tile * width * 4, np.float32)
        self._unit_u8 = np.empty(tile * width * 4, np.uint8) if self._direct else None
        tiles = (-(-height // tile), -(-width // tile))
        self._prints = None if self._direct else np.zeros(tiles, np.uint64)
        self._weights = None
        if not self._direct:
            rng = np.random.default_rng(0x5EED)
            pattern = rng.integers(1, 1 << 62, size=(tile, tile, channels), dtype=np.uint64) * np.uint64(2) + np.uint64(1)
            self._weights = np.tile(pattern, (1, tiles[1], 1))[:, :width]  # odd weights, the same in every tile
        self._cursor: Optional[Tuple[int, int]] = None
        self._pending: Deque[Tuple[int, int, int]] = deque()  # (top, first column, end column) to convert
        self._full = False
        self._cycle_spent = 0.0

    @property
    def busy(self) -> bool:
        """True while a capture is being worked through."""
        return self._cursor is not None or bool(self._pending)

    @property
    def unit_pixels(self) -> int:
        """Pixels per unit when looking for changes."""
        return self._units["scan"]

    @property
    def nbytes(self) -> int:
        total = self._raw.nbytes + self._known.nbytes + self._scratch.nbytes
        for extra in (self._unit_u8, self._prints, self._weights):
            if extra is not None:
                total += extra.nbytes
        return total

    def begin(self, full: bool = False) -> None:
        """Reads the image and starts working through it. ``full`` converts everything instead of comparing."""
        start = self.clock()
        self.read_into(self._raw)
        self.last_read_cost = self.clock() - start
        self._cursor = (0, 0)
        self._pending.clear()
        self._full = full
        self._cycle_spent = self.last_read_cost

    def _columns(self, kind: str) -> int:
        tile = self.tile
        return max(tile, min(self._max_unit, self._units[kind]) // tile // tile * tile)

    def _next_kind(self) -> str:
        if self._pending:
            return "convert"
        return "full" if self._full and self._direct else "scan"

    def step(self, budget: float = 0.006) -> List[Rect]:
        """Works through units for about ``budget`` seconds (at least one unit, and none that would overrun the
        budget judging by the last of its kind). Returns the rectangles whose pixels changed (in a full capture:
        were converted) in this step."""
        if not self.busy:
            return []
        start = self.clock()
        rects: List[Rect] = []
        while self.busy:
            kind = self._next_kind()
            began = self.clock()
            done = self._convert_next(rects) if kind == "convert" else self._scan_next(kind, rects)
            spent = self.clock() - began
            self._costs[kind] = spent
            self._adapt(kind, spent, done, budget)
            if not self.busy:
                self.captures += 1
                break
            elapsed = self.clock() - start
            if elapsed + self._costs.get(self._next_kind(), 0.0) > budget:
                break
        self._cycle_spent += self.clock() - start
        if not self.busy:
            self.last_cycle_cost = self._cycle_spent
        return rects

    def _adapt(self, kind: str, spent: float, pixels: int, budget: float) -> None:
        """Keeps one unit of each kind at a fifth to a third of the step budget."""
        if not self._adaptive or budget == float("inf"):
            return
        size = self._units[kind]
        if spent > budget * 0.34 and size > self._min_unit:
            self._units[kind] = max(self._min_unit, min(size, pixels) // 2)
        elif spent < budget * 0.1 and pixels >= size:
            self._units[kind] = min(self._max_unit, size * 2)

    def finish(self) -> List[Rect]:
        """Works through the rest of a capture at once."""
        rects: List[Rect] = []
        while self.busy:
            rects.extend(self.step(float("inf")))
        return rects

    def baseline(self) -> Rect:
        """A whole first capture at once; returns the full rectangle."""
        self.begin(full=True)
        self.finish()
        return (0, 0, self.width, self.height)

    def check(self) -> List[Rect]:
        """A whole capture at once: the rectangles that changed since the last capture."""
        self.begin()
        return self.finish()

    def cancel(self) -> None:
        self._cursor = None
        self._pending.clear()

    def release(self) -> None:
        """Frees the buffers (the stream ended); the object must not be used again."""
        self.cancel()
        self._raw = self._known = self._scratch = np.empty(0, np.float32)
        self._unit_u8 = self._prints = self._weights = None

    def _fingerprints(self, raw_unit: np.ndarray, x0: int) -> np.ndarray:
        """One fingerprint per tile of a unit: the bits of its raw values, weighted and summed (a change to any
        single value always changes it)."""
        assert self._weights is not None
        rows, columns = raw_unit.shape[0], raw_unit.shape[1]
        values = raw_unit.view(np.uint32).astype(np.uint64)
        # The unit's rows are in Blender's order (bottom row first); weights follow the same rows each time.
        np.multiply(values, self._weights[:rows, x0 : x0 + columns], out=values)
        per_column = values.sum(axis=(0, 2), dtype=np.uint64)
        return np.add.reduceat(per_column, np.arange(0, columns, self.tile), dtype=np.uint64)

    def _scan_next(self, kind: str, rects: List[Rect]) -> int:
        """Works through the unit at the cursor and moves the cursor on. Returns the pixels worked through."""
        assert self._cursor is not None
        height, width, tile = self.height, self.width, self.tile
        top, x0 = self._cursor
        x1 = min(width, x0 + self._columns(kind))
        bottom = min(height, top + tile)
        rows, columns = bottom - top, x1 - x0
        raw = self._raw.reshape(height, width, self.conversion.channels)
        raw_unit = raw[height - bottom : height - top, x0:x1]  # Blender order: the unit's last row comes first
        known_unit = self._known.reshape(height, width, 4)[top:bottom, x0:x1]
        if self._direct:
            if kind == "full":
                convert(raw_unit[::-1], known_unit, self.conversion, self._scratch)
                rects.append((x0, top, columns, rows))
            else:
                assert self._unit_u8 is not None
                unit = self._unit_u8[: rows * columns * 4].reshape(rows, columns, 4)
                convert(raw_unit[::-1], unit, self.conversion, self._scratch)
                now = unit.view(np.uint32)[..., 0]
                before = self._known.view(np.uint32).reshape(height, width)[top:bottom, x0:x1]
                differs = np.not_equal(now, before).any(axis=0)
                changed = np.logical_or.reduceat(differs, np.arange(0, columns, tile))
                if changed.any():
                    np.copyto(known_unit, unit)
                    rects.extend(tiles_to_rects(changed[None, :], tile, columns, rows, y_offset=top, x_offset=x0))
        else:
            assert self._prints is not None
            prints = self._fingerprints(raw_unit, x0)
            stored = self._prints[top // tile, x0 // tile : x0 // tile + len(prints)]
            changed = np.ones(len(prints), bool) if self._full else np.not_equal(prints, stored)
            stored[changed] = prints[changed]
            for start, end in tile_runs(changed):
                self._pending.append((top, x0 + start * tile, min(x1, x0 + end * tile)))
        self._cursor = (top, x1) if x1 < width else ((top + tile, 0) if top + tile < height else None)
        return rows * columns

    def _convert_next(self, rects: List[Rect]) -> int:
        """Converts the next queued chunk of changed tiles. Returns the pixels converted."""
        top, c0, c1 = self._pending[0]
        end = min(c1, c0 + self._columns("convert"))
        if end < c1:
            self._pending[0] = (top, end, c1)
        else:
            self._pending.popleft()
        height, width = self.height, self.width
        bottom = min(height, top + self.tile)
        raw = self._raw.reshape(height, width, self.conversion.channels)
        known = self._known.reshape(height, width, 4)
        convert(raw[height - bottom : height - top, c0:end][::-1], known[top:bottom, c0:end], self.conversion,
                self._scratch)
        rects.append((c0, top, end - c0, bottom - top))
        return (bottom - top) * (end - c0)

    def pixels(self, x: int, y: int, w: int, h: int) -> bytes:
        """RGBA8 rows top to bottom of a rectangle of the known pixels (the link session's pixel source)."""
        if x < 0 or y < 0 or w < 1 or h < 1 or x + w > self.width or y + h > self.height:
            raise ValueError("the rectangle is outside the image")
        rows = self._known.reshape(self.height, self.width, 4)
        return rows[y : y + h, x : x + w].tobytes()

    def known_rgba8(self) -> bytes:
        return self._known.tobytes()


# --------------------------------------------------------------------------------------------------
# Colour handling
# --------------------------------------------------------------------------------------------------

LINEAR_SPACES = frozenset({"Linear Rec.709", "Linear", "scene_linear", "Linear CIE-XYZ E", "Linear CIE-XYZ D65"})
SRGB_SPACES = frozenset({"sRGB"})
#: Alpha modes whose float pixels Blender keeps premultiplied (Channel Packed and None are stored as they are).
PREMULTIPLIED_ALPHA_MODES = frozenset({"STRAIGHT", "PREMUL"})


class ColourPlan(NamedTuple):
    conversion: Conversion
    warning: Optional[str]


def colour_plan(target: str, channels: int, is_float: bool, colour_space: str, is_data: bool,
                alpha_mode: str = "STRAIGHT") -> ColourPlan:
    """How to turn an image's pixels into what Durty Cloth Tool expects for ``target``.

    The diffuse texture is sRGB colour; normal and specular maps are data, sent as the values the file holds.
    Blender keeps byte images as stored (in their colour space) and float images in scene-linear colour (data
    images unchanged). Float colour is premultiplied by alpha unless the image is data or its alpha mode is
    Channel Packed or None.
    """
    unpremultiply = is_float and channels == 4 and not is_data and alpha_mode in PREMULTIPLIED_ALPHA_MODES
    sanitize = is_float
    if target == "diffuse":
        if is_data:
            return ColourPlan(Conversion(channels, False, False, sanitize),
                              "The image is set to Non-Color; its values are sent as colour unchanged.")
        if is_float or colour_space in LINEAR_SPACES:
            return ColourPlan(Conversion(channels, True, unpremultiply, sanitize), None)
        if colour_space in SRGB_SPACES:
            return ColourPlan(Conversion(channels, False, False, False), None)
        return ColourPlan(Conversion(channels, False, False, False),
                          f"The image's colour space {colour_space} is sent unconverted; use sRGB for exact colours.")
    # Normal and specular maps.
    if not is_float or is_data:
        return ColourPlan(Conversion(channels, False, False, sanitize), None)
    if colour_space in SRGB_SPACES:
        # Blender linearised the stored sRGB values; encoding restores them.
        return ColourPlan(Conversion(channels, True, unpremultiply, sanitize), None)
    if colour_space in LINEAR_SPACES:
        return ColourPlan(Conversion(channels, False, unpremultiply, sanitize), None)
    return ColourPlan(Conversion(channels, False, unpremultiply, sanitize),
                      f"Set the map's colour space to Non-Color; {colour_space} values are sent as they are in Blender.")
