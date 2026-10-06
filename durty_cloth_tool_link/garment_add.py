# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2026 Schmid Software Solutions (https://schmid-software.de)
"""Adding a game-ready garment to the project open in Durty Cloth Tool, without Blender: the skeleton template's bones,
the rules the add-on checks before anything is sent (names, the variation pictures, the vertex groups), the Sollumz
export it checks, the variation pictures written as PNG, the files and variations of the add, and Durty Cloth Tool's
answer in words.

Nothing here imports Blender; numpy and the standard library do the work, so the tests run without Blender.
"""

from __future__ import annotations

import re
import struct
import zlib
from typing import Any, Dict, Iterable, List, NamedTuple, Optional, Sequence, Tuple
from xml.etree import ElementTree

import numpy as np

from . import garment
from .dct_link import protocol
from .strings import EN, Msg, msg

#: The colour variations one add may carry (the game's variation limit per drawable).
MAX_VARIATIONS = protocol.MAX_ITEM_VARIATIONS
#: The longest edge a variation picture may have, and the edge above which Durty Cloth Tool advises against it.
MAX_PICTURE_EDGE = protocol.MAX_TEXTURE_EDGE
ADVISED_PICTURE_EDGE = 2048
MIN_PICTURE_EDGE = 16
#: The add-on's own vertex groups (the tear check's and a conversion's leftovers): no bone weights, never sent.
TEARS_GROUP = "DCT Tears"
PINNED_GROUP = "DCT Pinned"
LINING_GROUP = "DCT Lining"
TOOL_GROUPS = (TEARS_GROUP, PINNED_GROUP, LINING_GROUP)
TOOL_GROUP_PREFIX = "DCT_tmp_"
#: The slots the garment tools add: components (which may show skin) and props (which never do).
SLOTS = garment.SLOTS


# --------------------------------------------------------------------------------------------------
# The skeleton template
# --------------------------------------------------------------------------------------------------


class TemplateError(ValueError):
    """The skeleton template Durty Cloth Tool sent is not what the add-on expects."""


def template_bones(xml: bytes) -> List[str]:
    """The bone names of the skeleton template, in their order (the first drawable that has bones). The order is the
    game's: a bone's position in it is the index the exported weights use. Raises :class:`TemplateError` for XML that
    is not a skeleton template."""
    try:
        root = ElementTree.fromstring(xml)
    except ElementTree.ParseError as exc:
        raise TemplateError(f"the skeleton template is not XML ({exc})") from None
    if root.tag != "DrawableDictionary":
        raise TemplateError("the skeleton template is not a drawable dictionary")
    for drawable in root.findall("Item"):
        bones = drawable.find("Skeleton/Bones")
        if bones is None:
            continue
        names = [(item.findtext("Name") or "").strip() for item in bones.findall("Item")]
        if not names:
            continue
        if any(not name for name in names) or len(set(names)) != len(names):
            raise TemplateError("the skeleton template has unnamed or repeated bones")
        return names
    raise TemplateError("the skeleton template has no bones")


def _numbers(element: Any, names: str, default: Tuple[float, ...]) -> Tuple[float, ...]:
    if element is None:
        return default
    try:
        values = tuple(float(element.get(name, value)) for name, value in zip(names, default))
    except (TypeError, ValueError):
        raise TemplateError("the skeleton template has a bone transform that is no number") from None
    if not all(np.isfinite(values)):
        raise TemplateError("the skeleton template has a bone transform that is no number")
    return values


def _bone_matrix(translation: Tuple[float, ...], rotation: Tuple[float, ...], scale: Tuple[float, ...]) -> np.ndarray:
    x, y, z, w = rotation
    norm = float(np.sqrt(x * x + y * y + z * z + w * w)) or 1.0
    x, y, z, w = x / norm, y / norm, z / norm, w / norm
    turn = np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
    matrix = np.eye(4)
    matrix[:3, :3] = turn * np.asarray(scale)
    matrix[:3, 3] = translation
    return matrix


def template_matrices(xml: bytes, names: Optional[Iterable[str]] = None) -> Dict[str, np.ndarray]:
    """Where the skeleton template's bones (``names``, all by default) sit in ped space at rest, as 4 by 4 matrices
    (their position and how they are turned): each bone's translation, rotation and scale applied down from the root.
    Raises :class:`TemplateError` for XML that is not a skeleton template."""
    try:
        root = ElementTree.fromstring(xml)
    except ElementTree.ParseError as exc:
        raise TemplateError(f"the skeleton template is not XML ({exc})") from None
    for drawable in root.findall("Item"):
        items = drawable.findall("Skeleton/Bones/Item")
        if not items:
            continue
        bones = []
        for item in items:
            parent = item.find("ParentIndex")
            try:
                parent_index = int(parent.get("value", "-1")) if parent is not None else -1
            except (TypeError, ValueError):
                raise TemplateError("the skeleton template has a parent index that is no number") from None
            local = _bone_matrix(_numbers(item.find("Translation"), "xyz", (0.0, 0.0, 0.0)),
                                 _numbers(item.find("Rotation"), "xyzw", (0.0, 0.0, 0.0, 1.0)),
                                 _numbers(item.find("Scale"), "xyz", (1.0, 1.0, 1.0)))
            bones.append(((item.findtext("Name") or "").strip(), parent_index, local))
        world: List[Optional[np.ndarray]] = [None] * len(bones)

        def placed(index: int, depth: int = 0) -> np.ndarray:
            if world[index] is None:
                _, parent_index, local = bones[index]
                if 0 <= parent_index < len(bones) and parent_index != index and depth < len(bones):
                    world[index] = placed(parent_index, depth + 1) @ local
                else:
                    world[index] = local
            return world[index]  # type: ignore[return-value]

        wanted = set(names) if names is not None else None
        return {name: placed(i) for i, (name, _, _) in enumerate(bones)
                if name and (wanted is None or name in wanted)}
    raise TemplateError("the skeleton template has no bones")


def template_joints(xml: bytes, names: Optional[Iterable[str]] = None) -> Dict[str, Tuple[float, float, float]]:
    """Where the skeleton template's bones (``names``, all by default) sit in ped space at rest (their positions,
    :func:`template_matrices`). Raises :class:`TemplateError` for XML that is not a skeleton template."""
    return {name: tuple(float(v) for v in matrix[:3, 3])  # type: ignore[misc]
            for name, matrix in template_matrices(xml, names).items()}


def armature_problem(armature_bones: Sequence[str], template: Sequence[str]) -> Optional[Msg]:
    """Why the armature cannot carry the garment into the game, or ``None``: it must hold exactly the template's bones in
    the template's order, because each exported weight names its bone by its position in the armature."""
    if list(armature_bones) == list(template):
        return None
    if sorted(armature_bones) == sorted(template):
        return msg("add.skeleton.order")
    return msg("add.skeleton.bones", count=len(armature_bones), expected=len(template))


def is_tool_group(name: str) -> bool:
    return name in TOOL_GROUPS or name.startswith(TOOL_GROUP_PREFIX)


class GroupReport(NamedTuple):
    """The garment's vertex groups compared with the skeleton's bones."""

    bones: List[str]  # groups named after a bone: the weights the game uses
    unknown: List[str]  # groups that are no bone (the export would put their weight on the root bone)
    tools: List[str]  # the add-on's own groups, left out


def group_report(groups: Iterable[str], bones: Iterable[str]) -> GroupReport:
    known = set(bones)
    matched, unknown, tools = [], [], []
    for name in groups:
        if is_tool_group(name):
            tools.append(name)
        elif name in known:
            matched.append(name)
        else:
            unknown.append(name)
    return GroupReport(matched, unknown, tools)


def group_problems(report: GroupReport) -> List[Msg]:
    """What the vertex groups block: no weights for the skeleton at all, or groups that are no bone."""
    problems: List[Msg] = []
    if not report.bones:
        problems.append(msg("add.why.no-weights"))
    if report.unknown:
        shown = ", ".join(report.unknown[:5]) + (" …" if len(report.unknown) > 5 else "")
        problems.append(msg("add.why.unknown-groups", count=len(report.unknown), names=shown))
    return problems


# --------------------------------------------------------------------------------------------------
# What the user enters, and the pictures
# --------------------------------------------------------------------------------------------------


def name_problem(name: Any) -> Optional[Msg]:
    """Why the cloth's name cannot be sent, or ``None`` (1 to 128 characters of text, no control characters)."""
    if not isinstance(name, str) or not name.strip():
        return msg("add.why.name-empty")
    if not protocol.is_text(name):
        return msg("add.why.name-invalid", limit=protocol.MAX_TEXT_LENGTH)
    return None


def variation_title(name: Any, fallback: str) -> str:
    """The name a variation is sent with: the user's, or ``fallback`` (the image's name) when the field is empty, cut to
    the protocol's limit."""
    text = name.strip() if isinstance(name, str) else ""
    if not text:
        text = fallback.strip() or "A"
    text = re.sub(r"[\x00-\x1f\x7f-\x9f]", " ", text)
    return text[: protocol.MAX_TEXT_LENGTH]


class PictureCheck(NamedTuple):
    blocking: Optional[Msg]
    warnings: List[Msg]


def picture_check(width: int, height: int, label: str) -> PictureCheck:
    """Durty Cloth Tool's rules for a variation picture, checked before anything is sent: an edge above 4096 or a size
    that is not a multiple of four refuses the add; other sizes are advice."""
    if width < 1 or height < 1:
        return PictureCheck(msg("add.picture.empty", name=label), [])
    if width > MAX_PICTURE_EDGE or height > MAX_PICTURE_EDGE:
        return PictureCheck(msg("add.picture.too-large", name=label, size=MAX_PICTURE_EDGE), [])
    if width % 4 or height % 4:
        return PictureCheck(msg("add.picture.not-multiple-of-four", name=label, width=width, height=height), [])
    warnings: List[Msg] = []
    if width & (width - 1) or height & (height - 1):
        warnings.append(msg("add.picture.non-power-of-two", name=label, width=width, height=height))
    if width > ADVISED_PICTURE_EDGE or height > ADVISED_PICTURE_EDGE:
        warnings.append(msg("add.picture.large", name=label, size=ADVISED_PICTURE_EDGE))
    if width < MIN_PICTURE_EDGE or height < MIN_PICTURE_EDGE:
        warnings.append(msg("add.picture.small", name=label, size=MIN_PICTURE_EDGE))
    return PictureCheck(None, warnings)


def png_bytes(rgba: Any, width: int, height: int, level: int = 6) -> bytes:
    """An RGBA8 picture (rows from top to bottom, tightly packed) as a PNG file: 8 bits per channel, every row with the
    Sub filter, which suits painted and baked textures."""
    pixels = np.frombuffer(memoryview(rgba).cast("B"), dtype=np.uint8)
    if pixels.size != width * height * 4:
        raise ValueError("the picture has the wrong number of pixels")
    rows = pixels.reshape(height, width * 4)
    filtered = np.empty((height, width * 4 + 1), dtype=np.uint8)
    filtered[:, 0] = 1  # Sub: each byte minus the same channel of the pixel to its left
    filtered[:, 1:5] = rows[:, :4]
    filtered[:, 5:] = rows[:, 4:] - rows[:, :-4]  # uint8 arithmetic wraps, as the filter needs

    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

    header = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", zlib.compress(filtered.tobytes(), level))
            + chunk(b"IEND", b""))


# --------------------------------------------------------------------------------------------------
# The export
# --------------------------------------------------------------------------------------------------


class ExportSummary(NamedTuple):
    """What a Sollumz export of the Drawable Dictionary holds."""

    drawables: int
    models: int  # High level models of the first drawable
    geometries: int  # their geometries
    skeleton_bones: int  # bones of a skeleton left in the export (Exclude Skeleton removes it)


def export_summary(xml_file: Any) -> ExportSummary:
    """Reads the exported ``*.ydd.xml`` (a path or a file object) as a stream. Raises ``ValueError`` when it is not a
    drawable dictionary."""
    drawables = models = geometries = bones = 0
    path: List[str] = []
    try:
        for event, element in ElementTree.iterparse(xml_file, events=("start", "end")):
            if event == "start":
                path.append(element.tag)
                if len(path) == 1 and element.tag != "DrawableDictionary":
                    raise ValueError("the export is not a drawable dictionary")
                if path == ["DrawableDictionary", "Item"]:
                    drawables += 1
                elif drawables == 1 and path == ["DrawableDictionary", "Item", "DrawableModelsHigh", "Item"]:
                    models += 1
                elif drawables == 1 and path == ["DrawableDictionary", "Item", "DrawableModelsHigh", "Item",
                                                 "Geometries", "Item"]:
                    geometries += 1
                elif path[1:] == ["Item", "Skeleton", "Bones", "Item"]:
                    bones += 1
                continue
            path.pop()
            if len(path) <= 3:
                element.clear()  # the big buffers are inside; keep the memory flat
    except ElementTree.ParseError as exc:
        raise ValueError(f"the export is not readable XML ({exc})") from None
    return ExportSummary(drawables, models, geometries, bones)


def export_problem(summary: ExportSummary) -> Optional[Msg]:
    """Why the export cannot become a cloth, or ``None``: exactly one drawable whose High level has geometry, without
    the skeleton (the cloth uses the ped's own)."""
    if summary.drawables == 0 or summary.models == 0 or summary.geometries == 0:
        return msg("add.export.empty")
    if summary.drawables > 1:
        return msg("add.export.several", count=summary.drawables)
    if summary.skeleton_bones:
        return msg("add.export.skeleton")
    return None


# --------------------------------------------------------------------------------------------------
# The add
# --------------------------------------------------------------------------------------------------


def variation_file(index: int) -> str:
    """The file name of a variation's picture in the add (``variation_a.png`` ...)."""
    letter = chr(ord("a") + index) if 0 <= index < 26 else str(index + 1)
    return f"variation_{letter}.png"


class Variation(NamedTuple):
    title: str
    png: bytes


def item_files(model: Tuple[str, bytes], textures: Sequence[Tuple[str, bytes]],
               variations: Sequence[Variation]) -> Tuple[List[Tuple[str, bytes]], List[Tuple[str, str]]]:
    """The files and variations of the add, in the order Durty Cloth Tool reads them: the model, its textures, then one
    picture per variation. A picture's name never repeats a texture's (names compare without regard to case)."""
    if not 1 <= len(variations) <= MAX_VARIATIONS:
        raise ValueError(f"an add has 1 to {MAX_VARIATIONS} colour variations")
    taken = {model[0].lower(), *(name.lower() for name, _ in textures)}
    files: List[Tuple[str, bytes]] = [model, *textures]
    chosen: List[Tuple[str, str]] = []
    for index, variation in enumerate(variations):
        name = variation_file(index)
        while name.lower() in taken:
            name = "dct_" + name
        taken.add(name.lower())
        files.append((name, variation.png))
        chosen.append((name, variation.title))
    return files, chosen


def payload_size(files: Sequence[Tuple[str, Any]]) -> int:
    return sum(memoryview(data).nbytes for _, data in files)


#: Durty Cloth Tool's finding codes the panel explains; the texture codes share the Texture Checks' texts.
MODEL_FINDINGS = ("rig-invalid", "rig-unchecked", "single-bone-rig", "hair-tint-unsupported")
PICTURE_FINDINGS = ("non-power-of-two", "not-multiple-of-four", "too-large", "too-small")
SEVERITY_ORDER = {"error": 0, "warning": 1, "info": 2}


def finding_text(code: str) -> Msg:
    """A finding Durty Cloth Tool returned with the add, in words."""
    if code in MODEL_FINDINGS:
        return msg(f"add.finding.{code}")
    if code in PICTURE_FINDINGS:
        return msg(f"add.finding.picture.{code}")
    return msg("finding.unknown", code=code)


def sorted_findings(findings: Iterable[Dict[str, str]]) -> List[Dict[str, str]]:
    """Errors first, then warnings, then notes (each code once, as Durty Cloth Tool sends them)."""
    return sorted(findings, key=lambda f: SEVERITY_ORDER.get(str(f.get("severity")), 3))


#: Durty Cloth Tool's answers that the panel explains in their own words (everything else: the error's text).
RESULT_KEYS = {
    "request-denied": "add.result.denied",
    "item-limit": "add.result.item-limit",
    "model-rejected": "add.result.rejected",
    "no-project": "add.result.no-project",
    "item-refused": "add.result.item-refused",
    "busy": "add.result.busy",
    "rate-limited": "add.result.rate-limited",
    "save-failed": "add.result.save-failed",
    "needs-license": "error.needs-license",
    "needs-ultimate": "error.needs-ultimate",
    # A Durty Cloth Tool that cannot read the add answers it by its id (since 2026-10-06) instead of never.
    "unknown-message-type": "add.dct-too-old",
}
#: The level each answer is shown with.
RESULT_LEVELS = {"request-denied": "INFO", "item-limit": "WARNING", "busy": "WARNING", "rate-limited": "WARNING"}


def result_message(code: Optional[str], *, withdrawn: bool = False) -> Tuple[str, Msg]:
    """``(level, message)`` for an add Durty Cloth Tool did not make. ``withdrawn``: the add-on cancelled it."""
    if code == "request-denied" and withdrawn:
        return "INFO", msg("add.result.withdrawn")
    key = RESULT_KEYS.get(code or "")
    if key is not None:
        return RESULT_LEVELS.get(code or "", "ERROR"), msg(key)
    if code and f"error.{code}" in EN:
        return "ERROR", msg(f"error.{code}")
    return "ERROR", msg("error.generic-code", code=code) if code else msg("error.generic")


def failure_message(code: str) -> Tuple[str, Msg]:
    """``(level, message)`` for an add that got no answer from Durty Cloth Tool."""
    if code == "cancelled":
        return "WARNING", msg("add.result.cancel-unanswered")
    if code == "timeout":
        return "WARNING", msg("add.result.timeout")
    if code == "disconnected":
        return "WARNING", msg("add.result.disconnected")
    return result_message(code)


#: How big a picture's PNG can get at most, per pixel (zlib stores what it cannot compress with a small overhead,
#: plus the filter byte of each row).
PNG_BYTES_PER_PIXEL = 4.01


def payload_estimate(model_bytes: int, sizes: Sequence[Tuple[int, int]]) -> Tuple[int, int]:
    """``(at least, at most)`` bytes an add will carry before its pictures are written: the model and its textures,
    plus each picture's PNG between nothing and its worst case."""
    most = model_bytes + sum(int(w * h * PNG_BYTES_PER_PIXEL) + h + 1024 for w, h in sizes)
    return model_bytes, most


def template_refusal(code: Optional[str]) -> Msg:
    """Why Durty Cloth Tool sent no skeleton template."""
    if code == "game-required":
        return msg("add.skeleton.game-required")
    if code == "busy":
        return msg("add.skeleton.busy")
    if code == "unknown-message-type":
        return msg("add.dct-too-old")
    if code in ("needs-license", "needs-ultimate"):
        return msg(f"error.{code}")
    if code and f"error.{code}" in EN:
        return msg(f"error.{code}")
    return msg("error.generic-code", code=code) if code else msg("error.generic")


__all__ = [
    "ExportSummary",
    "GroupReport",
    "PictureCheck",
    "TemplateError",
    "Variation",
    "armature_problem",
    "export_problem",
    "export_summary",
    "failure_message",
    "finding_text",
    "group_problems",
    "group_report",
    "item_files",
    "name_problem",
    "payload_estimate",
    "payload_size",
    "picture_check",
    "png_bytes",
    "result_message",
    "sorted_findings",
    "template_bones",
    "template_joints",
    "template_matrices",
    "template_refusal",
    "variation_file",
    "variation_title",
]
