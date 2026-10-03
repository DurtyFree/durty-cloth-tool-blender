# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2026 Schmid Software Solutions (https://schmid-software.de)
"""Collecting a Sollumz export into a Creator Link model push.

Durty Cloth Tool takes a model as ``ydd-xml``: exactly one ``*.ydd.xml`` (CodeWalker XML, as Sollumz writes it)
and any number of ``*.dds`` textures, all under bare file names (letters, digits, ``_ - .``, not starting with a
dot, no ``..``) that are unique ignoring case, at most 256 files and 64 MiB together. Sollumz writes embedded
textures into a folder named after the model; they are sent under their bare names.

No Blender imports, so the tests can run without Blender.
"""

from __future__ import annotations

import os
import pathlib
from typing import List, NamedTuple, Tuple, Union

from .dct_link import protocol
from .dct_link.session import ModelBundle
from .strings import UserError, msg

MODEL_SUFFIX = ".ydd.xml"
TEXTURE_SUFFIX = ".dds"
OTHER_MODEL_SUFFIXES = (".ydr.xml", ".yft.xml", ".ybn.xml")
MAX_DEPTH = 3


class BundleError(UserError):
    """The export cannot be pushed; the message is shown to the user."""


def _error(key: str, **fields) -> BundleError:
    return BundleError(msg(key, **fields))


class CollectedFiles(NamedTuple):
    model: pathlib.Path
    textures: List[pathlib.Path]
    ignored: List[str]


def _walk(directory: pathlib.Path, depth: int = 0) -> List[pathlib.Path]:
    files: List[pathlib.Path] = []
    try:
        entries = sorted(os.scandir(directory), key=lambda e: e.name.lower())
    except OSError as exc:
        raise _error("bundle.unreadable", detail=str(exc.strerror or exc)) from exc
    for entry in entries:
        if entry.is_symlink():
            continue
        if entry.is_dir(follow_symlinks=False):
            if depth < MAX_DEPTH:
                files.extend(_walk(pathlib.Path(entry.path), depth + 1))
        elif entry.is_file(follow_symlinks=False):
            files.append(pathlib.Path(entry.path))
    return files


def collect(directory: Union[str, os.PathLike]) -> CollectedFiles:
    """Finds the model and its textures in an export folder, applying the push rules.

    Raises :class:`BundleError` with a message for the user when the folder does not hold exactly one
    drawable dictionary, a name is not allowed, two textures share a name, or the limits are exceeded.
    """
    root = pathlib.Path(directory)
    files = _walk(root)
    models = [f for f in files if f.name.lower().endswith(MODEL_SUFFIX)]
    textures = [f for f in files if f.name.lower().endswith(TEXTURE_SUFFIX)]
    others = [f for f in files if f not in models and f not in textures]

    if not models:
        if any(f.name.lower().endswith(OTHER_MODEL_SUFFIXES) for f in others):
            raise _error("bundle.not-dictionary")
        raise _error("bundle.no-model")
    if len(models) > 1:
        raise _error("bundle.several", count=len(models))

    seen = {}
    for path in [models[0], *textures]:
        name = path.name
        if not protocol.is_file_name(name):
            raise _error("bundle.bad-name", name=name)
        folded = name.lower()
        if folded in seen:
            raise _error("bundle.duplicate", name=name)
        seen[folded] = path

    if 1 + len(textures) > protocol.MAX_MODEL_FILES:
        raise _error("bundle.too-many", count=len(textures), limit=protocol.MAX_MODEL_FILES - 1)

    total = 0
    for path in [models[0], *textures]:
        try:
            size = path.stat().st_size
        except OSError as exc:
            raise _error("bundle.unreadable", detail=str(exc.strerror or exc)) from exc
        if size == 0:
            raise _error("bundle.empty-file", name=path.name)
        total += size
    if total > protocol.MAX_BINARY_PAYLOAD_BYTES:
        raise _error("bundle.too-large", size=protocol.MAX_BINARY_PAYLOAD_BYTES // (1024 * 1024))

    ignored = sorted(p.relative_to(root).as_posix() for p in others)
    return CollectedFiles(models[0], sorted(textures, key=lambda p: p.name.lower()), ignored)


def read_files(collected: CollectedFiles) -> List[Tuple[str, bytes]]:
    """The files as ``(bare name, bytes)``, the model first."""
    try:
        return [(path.name, path.read_bytes()) for path in [collected.model, *collected.textures]]
    except OSError as exc:
        raise _error("bundle.unreadable", detail=str(exc.strerror or exc)) from exc


def build_bundle(directory: Union[str, os.PathLike]) -> Tuple[ModelBundle, CollectedFiles]:
    """Collects and reads an export folder into a ``ydd-xml`` :class:`ModelBundle`."""
    collected = collect(directory)
    files = read_files(collected)
    try:
        bundle = ModelBundle(protocol.MODEL_YDD_XML, files)
    except ValueError as exc:  # the link client applies the same rules; keep its verdict
        raise _error("bundle.invalid", detail=str(exc)) from exc
    return bundle, collected
