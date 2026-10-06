# SPDX-License-Identifier: GPL-3.0-or-later
"""The nine interface languages: every text in every language, the same fields, the protected names unchanged,
and the table Blender registers (no Blender needed)."""

from __future__ import annotations

import re
import string
import unicodedata

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


def test_the_nine_languages_are_registered_for_blender():
    assert LANGUAGES == ("de", "fr", "ru", "es", "pt_BR", "zh_HANS", "hi", "ar")
    tables = translations.blender_tables()
    assert set(tables) == {"de", "fr", "ru", "es", "pt_BR", "pt", "zh_HANS", "hi", "ar"}
    assert "zh" not in tables and "zh_HANT" not in tables  # Traditional Chinese readers get English
    for locale, entries in tables.items():
        assert len(entries) == len({text for text in EN.values()}), locale
        assert all(context == strings.CONTEXT for context, _ in entries)


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
SCRIPTS = {"ru": "CYRILLIC", "zh_HANS": "CJK", "hi": "DEVANAGARI", "ar": "ARABIC"}


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
