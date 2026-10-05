# SPDX-License-Identifier: GPL-3.0-or-later
"""Settings, public addresses and the user-facing text (no Blender needed)."""

from __future__ import annotations

import pathlib
import re

from durty_cloth_tool_link import settings, strings
from durty_cloth_tool_link.dct_link import protocol

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
VENDORED = REPO_ROOT / "durty_cloth_tool_link" / "dct_link"
EM_DASH = chr(0x2014)
# Assembled from pieces so this file does not match itself. The add-on and its vendored dct_link are public: they
# may name gta.clothing's public routes, nothing behind them and nothing of Durty Cloth Tool's own repository.
PRIVATE = re.compile("|".join([
    "api" + "-next", r"(?<!discord\.)" + "plebmasters" + r"\.de", "local" + r"host:\d", "DurtyClothTool" + r"\.App",
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
    # The rules dct_link applies to update links: printable ASCII, no spaces, backslash or @, and the exact prefix.
    for url in ("https://gta.clothing\\@evil.example/", "https://gta.clothing/@evil.example",
                "https://gta.clothing/a b", "https://gta.clothing/a\tb", "https://gta.clothing/\x00",
                "https://gta.clothing/\u00e9", "https://gta.clothing", "https://gta.clothing:443/",
                "https://link.gta.clothing/", "https://gta.clothing/" + "a" * 2048):
        assert not settings.is_gta_clothing_url(url), url


def test_sign_in_codes_show_like_on_gta_clothing():
    assert settings.display_user_code("BDWPHQPK") == "BDWP-HQPK"
    assert settings.display_user_code("bdwp-hqpk") == "BDWP-HQPK"


def test_stream_size_limits():
    assert settings.check_stream_size(4096, 4096) is None
    assert settings.check_stream_size(1, 1) is None
    assert "4096" in strings.english(settings.check_stream_size(4097, 16))
    assert settings.check_stream_size(0, 16) is not None


def test_auto_push_delay_is_clamped():
    assert settings.clamp_auto_push_delay(0) == settings.AUTO_PUSH_DELAY_MIN
    assert settings.clamp_auto_push_delay(100) == settings.AUTO_PUSH_DELAY_MAX
    assert settings.clamp_auto_push_delay(2.5) == 2.5


#: dct_link's local error codes (LinkError in dct_link/session.py).
LOCAL_CODES = ("disconnected", "timeout", "superseded", "cancelled", "closed", "assertion-invalid",
               "untrusted-endpoint", "signed-out", "pixel-source-failed", "callback-failed", "internal-error")


def test_every_protocol_and_session_error_code_has_text():
    missing = [code for code in (*protocol.ERROR_CODES, *LOCAL_CODES) if f"error.{code}" not in strings.EN]
    assert missing == []


def test_every_close_reason_and_plan_state_has_text():
    reasons = set(protocol.LIVE_CLOSE_REASONS) | set(protocol.MODEL_CLOSE_REASONS) | {"disconnected"}
    assert {f"close.{reason}" for reason in reasons} <= set(strings.EN)
    assert {f"feature.{state}" for state in protocol.FEATURE_STATES if state != "entitled"} <= set(strings.EN)


def test_unknown_codes_still_get_a_sentence():
    assert strings.english(settings.describe_error("something-new")) == "Something went wrong (something-new)."
    assert strings.english(settings.describe_error(None)) == "Something went wrong."
    assert settings.describe_feature("entitled") is None
    assert settings.describe_feature(None) is None
    assert strings.english(settings.describe_feature("needsUltimate")) == "This is included in Durty Cloth Tool Ultimate."


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
