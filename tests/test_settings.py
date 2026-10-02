# SPDX-License-Identifier: GPL-3.0-or-later
"""Settings, public addresses and the user-facing text (no Blender needed)."""

from __future__ import annotations

import pathlib
import re

import pytest

from durty_cloth_tool_link import settings
from durty_cloth_tool_link.dct_link import protocol

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
VENDORED = REPO_ROOT / "durty_cloth_tool_link" / "dct_link"
EM_DASH = chr(0x2014)
# Assembled from pieces so this file does not match itself. The add-on and its vendored dct_link are public: they
# may name gta.clothing's public routes, nothing behind them and nothing of Durty Cloth Tool's own repository.
PRIVATE = re.compile("|".join([
    "api" + "-next", "plebmasters" + r"\.de", "local" + r"host:\d", "DurtyClothTool" + r"\.App",
    "eng" + "/", r"\.ps" + "1", r"\bV" + r"3\b", "link" + r"-api\.md",
]), re.IGNORECASE)
#: In the vendored copy also no paths into the Durty Cloth Tool repository (its VENDORED.md names the source).
PRIVATE_VENDORED = re.compile("|".join(["plugins" + "/", "tests" + "/"]))


def test_repository_addresses_per_channel():
    assert settings.repository_url("release") == "https://gta.clothing/link/blender/release/index.json"
    assert settings.repository_url("experimental") == "https://gta.clothing/link/blender/experimental/index.json"
    assert settings.repository_url("development") == settings.repository_url("release")  # never offered
    for channel in settings.CHANNEL_IDS:
        assert settings.repository_channel(settings.repository_url(channel)) == channel
    assert settings.repository_channel("https://extensions.blender.org/api/v1/extensions/") is None
    assert settings.repository_channel("https://gta.clothing/link/blender/development/index.json") is None
    assert settings.repository_channel(None) is None


def test_only_gta_clothing_links_are_opened():
    assert settings.is_gta_clothing_url("https://gta.clothing/account/link/?code=BDWPHQPK")
    assert not settings.is_gta_clothing_url("http://gta.clothing/account/link/")
    assert not settings.is_gta_clothing_url("https://gta.clothing.example.com/")
    assert not settings.is_gta_clothing_url("https://evil.example/?https://gta.clothing/")
    assert not settings.is_gta_clothing_url(None)


@pytest.mark.parametrize("typed,code", [("048213", "048213"), (" 048 213 ", "048213"), ("048-213", "048213"),
                                        ("48213", None), ("0482134", None), ("abcdef", None), ("", None)])
def test_pairing_codes(typed, code):
    assert settings.normalize_pairing_code(typed) == code


def test_sign_in_codes_show_like_on_gta_clothing():
    assert settings.display_user_code("BDWPHQPK") == "BDWP-HQPK"
    assert settings.display_user_code("bdwp-hqpk") == "BDWP-HQPK"


def test_stream_size_limits():
    assert settings.check_stream_size(4096, 4096) is None
    assert settings.check_stream_size(1, 1) is None
    assert "4096" in settings.check_stream_size(4097, 16)
    assert settings.check_stream_size(0, 16) is not None


def test_auto_push_delay_is_clamped():
    assert settings.clamp_auto_push_delay(0) == settings.AUTO_PUSH_DELAY_MIN
    assert settings.clamp_auto_push_delay(100) == settings.AUTO_PUSH_DELAY_MAX
    assert settings.clamp_auto_push_delay(2.5) == 2.5


def test_every_protocol_error_code_has_text():
    missing = [code for code in protocol.ERROR_CODES if code not in settings.ERROR_TEXT]
    assert missing == []


def test_every_live_state_and_close_reason_has_text():
    assert set(protocol.LIVE_STATES) <= set(settings.LIVE_STATE_TEXT)
    assert set(protocol.LIVE_CLOSE_REASONS) <= set(settings.CLOSE_REASON_TEXT)
    assert set(protocol.MODEL_CLOSE_REASONS) <= set(settings.CLOSE_REASON_TEXT)
    assert set(protocol.FEATURE_STATES) - {"entitled"} <= set(settings.FEATURE_STATE_TEXT)


def test_unknown_codes_still_get_a_sentence():
    assert settings.describe_error("something-new") == "Something went wrong (something-new)."
    assert settings.describe_error(None, "fallback") == "fallback"
    assert settings.describe_feature("entitled") is None
    assert settings.describe_feature(None) is None
    assert settings.describe_feature("needsUltimate") == "Needs Durty Cloth Tool Ultimate"


def test_targets_match_the_protocol():
    assert tuple(target for target, _, _ in settings.TARGETS) == protocol.LIVE_TARGETS


def text_files(include_vendored: bool = False):
    for path in sorted(REPO_ROOT.rglob("*")):
        if not path.is_file() or path.name == "LICENSE" or (VENDORED in path.parents and not include_vendored):
            continue
        if any(part in {".git", "dist", "__pycache__", ".smoke", ".pytest_cache"} or part.startswith(".venv")
               for part in path.relative_to(REPO_ROOT).parts):
            continue
        if path.suffix in {".py", ".md", ".toml", ".yml", ".txt", ".json"} or path.name.startswith("."):
            yield path


def test_no_em_dashes_in_the_repository():
    offenders = [p.relative_to(REPO_ROOT).as_posix() for p in text_files() if EM_DASH in p.read_text("utf-8")]
    assert offenders == []


def test_no_private_addresses_or_internals_in_the_repository():
    offenders = [p.relative_to(REPO_ROOT).as_posix() for p in text_files(include_vendored=True)
                 if PRIVATE.search(p.read_text("utf-8"))]
    assert offenders == []


def test_the_vendored_copy_names_no_private_repository_paths():
    offenders = [p.name for p in VENDORED.glob("*.py") if PRIVATE_VENDORED.search(p.read_text("utf-8"))]
    assert offenders == []


def test_only_the_modules_the_add_on_uses_are_shipped():
    shipped = {p.name for p in VENDORED.iterdir() if p.is_file()}
    assert shipped == {"__init__.py", "auth.py", "protocol.py", "session.py", "tokens.py", "ws.py", "LICENSE",
                       "VENDORED.md"}
