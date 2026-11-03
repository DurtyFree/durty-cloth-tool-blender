# SPDX-License-Identifier: GPL-3.0-or-later
"""Every shipped interface language: every text in every language, the same fields, the protected names unchanged,
and the table Blender registers (no Blender needed)."""

from __future__ import annotations

import ast
import re
import string
import unicodedata
from pathlib import Path
from typing import Optional

import pytest

from durty_cloth_tool_link import strings, translations
from durty_cloth_tool_link.strings import EN

LANGUAGES = tuple(translations.LOCALES)
#: Names that stay as they are in every language when the English text uses them.
PROTECTED = ("Durty Cloth Tool", "Creator Link", "gta.clothing", "Discord", "Blender", "Sollumz", "CodeWalker",
             "YDD", "XML", "UDIM", "RGBA", "sRGB", "Non-Color", "Pleb Masters", "GTA V", "Ultimate", "ped",
             "MiB", "URL")


def fields(text: str) -> set:
    return {name for _, name, _, _ in string.Formatter().parse(text) if name}


def test_every_shipped_language_is_registered_for_blender():
    assert LANGUAGES == ("de", "fr", "ru", "es", "pt_BR", "zh_HANS", "hi", "ar", "it", "pl", "tr", "id", "th")
    tables = translations.blender_tables()
    assert set(tables) == {"de", "fr", "ru", "es", "pt_BR", "pt", "zh_HANS", "hi", "ar", "it", "it_IT", "pl", "pl_PL", "tr", "tr_TR", "id", "id_ID", "th", "th_TH"}
    assert "zh" not in tables and "zh_HANT" not in tables  # Traditional Chinese readers get English
    descriptions = {text for key, text in EN.items() if key.endswith(translations.DESCRIPTION)}
    for locale, entries in tables.items():
        assert len(entries) == len(set(EN.values())) + len(descriptions), locale
        assert {context for context, _ in entries} == {strings.CONTEXT, translations.DEFAULT_CONTEXT}
        # Labels and messages stay in the add-on's own context, so Blender's words never replace them.
        assert {text for context, text in entries if context == translations.DEFAULT_CONTEXT} == descriptions


@pytest.mark.parametrize("language", LANGUAGES)
def test_every_tooltip_is_registered_where_blender_looks_it_up(language):
    """Blender looks tooltips up in its default context whatever context a property has: a description registered
    only in the add-on's own context stayed English in every language."""
    table = translations.table(language)
    descriptions = [key for key in EN if key.endswith(translations.DESCRIPTION)]
    assert descriptions
    tables = translations.blender_tables()
    for locale in translations.LOCALES[language]:
        entries = tables[locale]
        for key in descriptions:
            for context in (translations.DEFAULT_CONTEXT, strings.CONTEXT):
                assert entries.get((context, EN[key])) == table[key], (locale, context, key)


ADDON = Path(translations.__file__).resolve().parents[1]


def _description_key(node: ast.AST, translated: bool = False) -> Optional[str]:
    """The key of ``EN["...desc"]`` or ``EN[f"...desc"]`` (the key's last literal part for an f-string), or ``None``
    when the node is no description key. With ``translated``, also ``t("...desc")``: a dynamic enum item translates
    when Blender asks for the items, while a ``description=`` or ``bl_description`` would freeze the language of the
    moment the class is defined."""
    if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name) and node.value.id == "EN":
        key = node.slice
    elif (translated and isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in ("t", "tt")
          and node.args):
        key = node.args[0]
    else:
        return None
    if isinstance(key, ast.Constant) and isinstance(key.value, str):
        text = key.value
    elif isinstance(key, ast.JoinedStr) and key.values and isinstance(key.values[-1], ast.Constant):
        text = key.values[-1].value
    else:
        return None
    return text if text.endswith(translations.DESCRIPTION) else None


def _is_text(node: ast.AST) -> bool:
    """An interface text: ``EN[...]`` or a call of the add-on's translator."""
    return ((isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name) and node.value.id == "EN")
            or (isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in ("t", "tt")))


def _is_name(node: ast.AST) -> bool:
    """An enum item's name inside an item list: an interface text, a literal or a helper's result."""
    return _is_text(node) or isinstance(node, ast.Call) or (isinstance(node, ast.Constant) and isinstance(node.value,
                                                                                                          str))


def _item_lists(tree: ast.AST) -> set:
    """The tuples inside an ``items=`` argument or an assignment to a name ending in ``ITEMS``: there any tuple of an
    identifier, a name and a third field is an enum item, whatever its name is."""
    roots = []
    for node in ast.walk(tree):
        if isinstance(node, ast.keyword) and node.arg == "items":
            roots.append(node.value)
        elif isinstance(node, (ast.Assign, ast.AnnAssign)) and node.value is not None:
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if any(isinstance(target, ast.Name) and target.id.endswith("ITEMS") for target in targets):
                roots.append(node.value)
    return {id(inner) for root in roots for inner in ast.walk(root) if isinstance(inner, ast.Tuple)}


def _is_identifier(node: ast.AST) -> bool:
    """An enum item's identifier: a string literal or a variable, never an interface text (a row of a drawn table)."""
    return (isinstance(node, ast.Constant) and isinstance(node.value, str)) or isinstance(node, (ast.Name,
                                                                                                 ast.Attribute))


def _tooltips_outside_the_convention(source: str) -> list:
    """Every ``description=``, ``bl_description =`` and enum item description (the third field of a tuple of an
    identifier and an interface text, or of an identifier and any name inside an item list) that does not take a
    ``.desc`` key. An empty item description shows no tooltip."""
    found = []
    tree = ast.parse(source)
    listed = _item_lists(tree)
    for node in ast.walk(tree):
        if isinstance(node, ast.keyword) and node.arg == "description":
            if _description_key(node.value) is None:
                found.append(("description=", node.value.lineno))
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if any(isinstance(target, ast.Name) and target.id == "bl_description" for target in targets):
                if node.value is None or _description_key(node.value) is None:
                    found.append(("bl_description", node.lineno))
        elif (isinstance(node, ast.Tuple) and len(node.elts) >= 3 and _is_identifier(node.elts[0])
              and (_is_text(node.elts[1]) or id(node) in listed and _is_name(node.elts[1]))):
            third = node.elts[2]
            if not (isinstance(third, ast.Constant) and third.value == "") and _description_key(third, True) is None:
                found.append(("enum item", node.lineno))
    return found


def test_every_tooltip_takes_a_description_key():
    """Only ``.desc`` keys reach Blender's default context, so a tooltip outside the convention would stay English."""
    modules = sorted(path for path in ADDON.rglob("*.py") if "dct_link" not in path.relative_to(ADDON).parts)
    assert modules
    found = {}
    for path in modules:
        outside = _tooltips_outside_the_convention(path.read_text(encoding="utf-8"))
        if outside:
            found[path.relative_to(ADDON).as_posix()] = outside
    assert not found


@pytest.mark.parametrize("source, outside", [
    ('X = EnumProperty(items=(("a", EN["x.a"], EN["x.a.desc"]),), description=EN["x.desc"])', []),
    ('items = [(v, EN[f"x.{v}"], EN[f"x.{v}.desc"], 0) for v in ids]', []),
    ('items = (("a", EN["x.a"], ""),)', []),
    ('class Op:\n    bl_description = EN["op.x.desc"]', []),
    ('X = BoolProperty(description="Hard-coded words")', [("description=", 1)]),
    ('X = BoolProperty(description=EN["x.label"])', [("description=", 1)]),
    ('class Op:\n    bl_description = "Hard-coded words"', [("bl_description", 2)]),
    ('items = (("a", EN["x.a"], EN["x.a"]),)', [("enum item", 1)]),
    ('items = ((value, t("x.a"), "Hard-coded words", 0),)', [("enum item", 1)]),
    ('row = (t("x.region"), t("x.value"), third)', []),  # a drawn table row, no enum item
    ('SIZE_ITEMS = (("4096", "4096", "Hard-coded words"),)', [("enum item", 1)]),
    ('X = EnumProperty(items=(("4096", "4096", "Hard-coded words"),))', [("enum item", 1)]),
    ('SIZES = (("4096", "4096", "plain data"),)', []),  # no item list
    ('ITEMS = [(c.id, label(c), t("x.cut.desc"), n) for n, c in enumerate(cuts)]', []),
    ('X = BoolProperty(description=t("x.desc"))', [("description=", 1)]),  # frozen at class definition
])
def test_the_tooltip_scan_finds_texts_outside_the_convention(source, outside):
    assert _tooltips_outside_the_convention(source) == outside


@pytest.mark.parametrize("language", LANGUAGES)
def test_every_text_has_a_translation_with_the_same_fields(language):
    table = translations.table(language)
    assert set(table) == set(EN), (sorted(set(EN) - set(table)), sorted(set(table) - set(EN)))
    for key, english in EN.items():
        translated = table[key]
        assert translated.strip(), key
        assert fields(translated) == fields(english), key
        translated.format(**{name: "x" for name in fields(english)})


@pytest.mark.parametrize("language", LANGUAGES)
def test_protected_names_stay_unchanged(language):
    table = translations.table(language)
    for key, english in EN.items():
        for name in PROTECTED:
            if re.search(rf"(?<![\w.]){re.escape(name)}(?![\w])", english):
                found = name.lower() in table[key].lower() if name == "ped" else name in table[key]  # Ped in German
                assert found, (key, name)


@pytest.mark.parametrize("language", LANGUAGES)
def test_the_same_english_text_has_the_same_translation(language):
    """Blender looks texts up by their English text, so two keys with one English text share a translation."""
    table = translations.table(language)
    seen: dict = {}
    for key, english in EN.items():
        if english in seen:
            assert table[key] == table[seen[english]], (key, seen[english])
        else:
            seen[english] = key


@pytest.mark.parametrize("language", ("en", *LANGUAGES))
def test_no_em_dashes(language):
    table = EN if language == "en" else translations.table(language)
    assert not [key for key, text in table.items() if chr(0x2014) in text]


def test_texts_render_through_the_installed_translator():
    german = translations.table("de")
    by_english = {EN[key]: text for key, text in german.items()}
    strings.set_translators(lambda text: by_english.get(text, text))
    try:
        # Durty Cloth Tool's own German label of its Connected apps page.
        assert strings.t("info.sign-in").endswith(
            "Durty Cloth Tool zeigt diese App unter Optionen > Verbundene Apps, wo du sie trennen kannst.")
        nested = strings.msg("details.status", state=strings.msg("state.ready", name="Durty"))
        assert strings.text(nested) == "Status: Angemeldet als Durty"
        assert strings.english(nested) == "Status: Signed in as Durty"
    finally:
        strings.set_translators(None)
    assert strings.t("info.sign-in").endswith(
        "Durty Cloth Tool lists this app under Options > Connected apps, where you can disconnect it.")


#: The script each translation is written in; Latin letters are allowed everywhere (product names, Blender terms).
SCRIPTS = {"ru": "CYRILLIC", "zh_HANS": "CJK", "hi": "DEVANAGARI", "ar": "ARABIC", "th": "THAI"}


@pytest.mark.parametrize("language", LANGUAGES)
def test_no_letters_from_another_script(language):
    """A letter of another script inside a word (a slip while typing) reads as a typo to every speaker."""
    expected = SCRIPTS.get(language, "LATIN")
    for key, text in translations.table(language).items():
        for character in text:
            if character.isalpha():
                script = unicodedata.name(character, "?").split()[0]
                assert script in ("LATIN", expected), (key, character)


def test_a_count_of_one_reads_in_the_singular():
    """The add listed "1 vertex groups are no bones of the freemode skeleton": a text about a number of things shows
    its .one form when the count is exactly 1, in English and through a translation."""
    one = strings.msg("add.why.unknown-groups", count=1, names="Group")
    assert strings.english(one).startswith("1 vertex group is not a bone of the freemode skeleton: Group.")
    assert strings.english(strings.msg("add.why.unknown-groups", count=2, names="A, B")).startswith(
        "2 vertex groups are not bones")
    assert strings.english(strings.msg("fit.wait.minutes", count=1)) == "in about 1 minute"
    assert strings.english(strings.msg("fit.wait.minutes", count=0)) == "in about 0 minutes"
    german = translations.table("de")
    by_english = {EN[key]: text for key, text in german.items()}
    strings.set_translators(lambda text: by_english.get(text, text))
    try:
        assert strings.text(one).startswith("1 Punktgruppe ist kein Knochen des Freemode-Skeletts: Group.")
    finally:
        strings.set_translators(None)


def test_every_form_for_one_has_the_fields_of_its_other_form():
    """The .one form replaces its other form only by the count, so it may neither lose nor need a field."""
    for key, english in EN.items():
        if key.endswith(strings.ONE):
            other = key[:-len(strings.ONE)]
            assert other in EN, key
            assert "count" in fields(english) and fields(english) == fields(EN[other]), key


def test_a_broken_translation_falls_back_to_english():
    strings.set_translators(lambda text: "{missing}" if text == EN["details.status"] else text)
    try:
        assert strings.t("details.status", state="ok") == "Status: ok"
    finally:
        strings.set_translators(None)


@pytest.mark.parametrize("text, columns, lines", [
    ("Durty Cloth Tool did not show a code. Choose Tools now.", 20,
     ["Durty Cloth Tool did", "not show a code.", "Choose Tools now."]),
    ("short", 20, ["short"]),
    ("", 20, [""]),
    (chr(0x6F02) * 12, 10, [chr(0x6F02) * 5, chr(0x6F02) * 5, chr(0x6F02) * 2]),  # wide characters count twice
    ("aaa bbb ccc ddd", 11, ["aaa bbb", "ccc ddd"]),  # no lone last word when the word before it fits along
    ("Start the Durty Cloth Tool now", 16, ["Start the", "Durty Cloth Tool", "now"]),  # the name stays whole
])
def test_wrapping(text, columns, lines):
    assert strings.wrap_text(text, columns) == lines


def test_wrapping_uses_the_measured_width():
    """The panels wrap by Blender's font metrics: here a wide "W" counts three times."""
    def measure(text):
        return sum(3 if c == "W" else 1 for c in text)

    assert strings.wrap_text("WWW aaa bbb", 8, measure) == ["WWW", "aaa bbb"]
