# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2026 Schmid Software Solutions (https://schmid-software.de)
"""The add-on's eight translations and their registration with Blender.

Each language has three modules, ``<language>`` (the link), ``garment_<language>`` (the garment fitting tools) and
``ped_<language>`` (Custom Ped), each holding ``TEXT``; together they have the keys of :data:`strings.EN`. Blender looks texts up by their English
text in the add-on's own translation context (:data:`strings.CONTEXT`), so Blender's translations
of common words never replace the add-on's wording. The module names follow Blender's locale codes; Blender
falls back from a full locale (``de_DE``) to its language (``de``), so one table serves every country variant.
Portuguese from Portugal gets the Brazilian table, as Durty Cloth Tool does; Traditional Chinese gets English.
Nothing here imports Blender.
"""

from __future__ import annotations

import importlib
from typing import Dict, Mapping, Tuple

from ..strings import CONTEXT, EN

#: Translation modules and the Blender locales each one is registered for.
LOCALES: Dict[str, Tuple[str, ...]] = {
    "de": ("de",),
    "fr": ("fr",),
    "ru": ("ru",),
    "es": ("es",),
    "pt_BR": ("pt_BR", "pt"),
    "zh_HANS": ("zh_HANS",),
    "hi": ("hi",),
    "ar": ("ar",),
}


def table(language: str) -> Mapping[str, str]:
    """Every text of one language: its link module's ``TEXT``, its garment module's and its Custom Ped module's."""
    if language not in LOCALES:
        raise KeyError(language)
    texts: Dict[str, str] = {}
    for name in (language, f"garment_{language}", f"ped_{language}"):
        texts.update(importlib.import_module(f"{__name__}.{name}").TEXT)
    return texts


def blender_tables() -> Dict[str, Dict[Tuple[str, str], str]]:
    """The dictionary ``bpy.app.translations.register`` takes: locale to ``{(context, English): translation}``."""
    tables: Dict[str, Dict[Tuple[str, str], str]] = {}
    for language, locales in LOCALES.items():
        text = table(language)
        entries = {(CONTEXT, english): text[key] for key, english in EN.items() if text.get(key)}
        for locale in locales:
            tables[locale] = entries
    return tables
