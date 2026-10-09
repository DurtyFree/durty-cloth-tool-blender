# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2026 Schmid Software Solutions (https://schmid-software.de)
"""Constants and public addresses, and the mapping from codes to the texts in :mod:`strings`. No Blender imports,
so the tests can run without Blender."""

from __future__ import annotations

import re
from typing import Optional, Tuple

from .dct_link import protocol
from .strings import EN, Msg, msg

#: The add-on version. ``blender_manifest.toml`` must say the same (the tests check it). Experimental builds
#: carry ``-experimental.N``.
VERSION = "0.1.0-experimental.4"
EXTENSION_ID = "durty_cloth_tool_link"
PLUGIN_KIND = "blender"
HOST_NAME = "Blender"

PLUGINS_PAGE_URL = "https://gta.clothing/account/plugins/"
HELP_URL = "https://docs.gta.clothing/"
#: The Pleb Masters Community Discord server's help channel (the same link the other Creator Link plugins use).
COMMUNITY_URL = "https://discord.com/channels/1074580032258854954/1176840388863086624"
#: The public invitation to the Pleb Masters Community Discord server (for accounts that are not members yet).
DISCORD_INVITE_URL = "https://discord.plebmasters.de"
#: The Sollumz version the add-on is tested with, and the oldest one whose export settings the add-on can set.
SOLLUMZ_TESTED = "2.9.0"
SOLLUMZ_MINIMUM = "2.8.0"
REPOSITORY_URL_PREFIX = "https://gta.clothing/link/blender/"

#: The public channels of the extension repository (development builds are never handed out). Blender adds the
#: repository itself when the install link from gta.clothing is dragged onto it.
CHANNEL_IDS = ("release", "experimental")


def channel_of_version(version: str) -> str:
    """The channel a build belongs to: Experimental versions carry ``-experimental.N``."""
    return "experimental" if "-experimental." in version else "release"


#: The channel of this build, reported to Durty Cloth Tool and gta.clothing.
CHANNEL = channel_of_version(VERSION)

#: The maps of a cloth (Blender enum items: identifier, English name, English description).
TARGETS: Tuple[Tuple[str, str, str], ...] = tuple(
    (target, EN[f"map.{target}"], EN[f"map.{target}.desc"]) for target in ("diffuse", "normal", "specular")
)

FEATURE_LIVE_TEXTURE = "dct.link.liveTexture"
FEATURE_SAVE = "dct.link.save"
FEATURE_MODEL = "dct.link.model"
FEATURE_SERVICES = "dct.link.services"
#: Adding a new cloth to the open project (every plan; Durty Cloth Tool applies its own project limits).
FEATURE_ADD_ITEM = "dct.link.addItem"

MAX_TEXTURE_EDGE = protocol.MAX_TEXTURE_EDGE
AUTO_PUSH_DELAY_DEFAULT = 1.5
AUTO_PUSH_DELAY_MIN = 0.5
AUTO_PUSH_DELAY_MAX = 30.0


def normalize_channel(channel: Optional[str]) -> str:
    return channel if channel in CHANNEL_IDS else "release"


def repository_url(channel: str) -> str:
    """The Blender extension repository of a channel (used to recognise an installation from it)."""
    return f"{REPOSITORY_URL_PREFIX}{normalize_channel(channel)}/index.json"


def repository_channel(url: Optional[str]) -> Optional[str]:
    """The channel of a Durty Cloth Tool repository address, or ``None`` for any other address."""
    if not url:
        return None
    for channel in CHANNEL_IDS:
        if url.rstrip("/") == repository_url(channel):
            return channel
    return None


#: Links the add-on opens in the browser start with this.
GTA_CLOTHING_PREFIX = "https://gta.clothing/"
MAX_LINK_LENGTH = 2048


def is_gta_clothing_url(url: Optional[str]) -> bool:
    """Whether the add-on may open ``url`` in the browser: ``https://gta.clothing/...`` in printable ASCII, without
    spaces, a backslash or ``@`` (the rules dct_link applies to update links)."""
    return (
        isinstance(url, str)
        and len(url) <= MAX_LINK_LENGTH
        and re.fullmatch(r"[!-~]+", url) is not None
        and "\\" not in url
        and "@" not in url
        and url.startswith(GTA_CLOTHING_PREFIX)
    )


def display_user_code(code: Optional[str]) -> str:
    """A sign-in code as gta.clothing shows it: four letters, a hyphen, four letters."""
    code = (code or "").replace("-", "").upper()
    return f"{code[:4]}-{code[4:]}" if len(code) == 8 else code


def check_stream_size(width: int, height: int) -> Optional[Msg]:
    """Why an image of this size cannot be streamed, or ``None``."""
    if width < 1 or height < 1:
        return msg("image.empty")
    if width > MAX_TEXTURE_EDGE or height > MAX_TEXTURE_EDGE:
        return msg("image.too-large", size=MAX_TEXTURE_EDGE)
    return None


def clamp_auto_push_delay(seconds: float) -> float:
    return min(AUTO_PUSH_DELAY_MAX, max(AUTO_PUSH_DELAY_MIN, float(seconds)))


#: Codes after which the stored gta.clothing sign-in is gone.
SIGNED_OUT_CODES = frozenset(
    {"expired_token", "access_denied", "invalid_grant", "session_invalid", "session_expired", "session_revoked"}
)


def describe_error(code: Optional[str]) -> Msg:
    """The text for an error code (Creator Link, the link session or gta.clothing's sign-in)."""
    if code and f"error.{code}" in EN:
        return msg(f"error.{code}")
    return msg("error.generic-code", code=code) if code else msg("error.generic")


def describe_close_reason(reason: Optional[str]) -> Msg:
    return msg(f"close.{reason}") if reason and f"close.{reason}" in EN else msg("close.closed")


def describe_feature(state: Optional[str]) -> Optional[Msg]:
    """``None`` when the feature is available, otherwise why not."""
    if state is None or state == "entitled":
        return None
    return msg(f"feature.{state}") if f"feature.{state}" in EN else msg("feature.unavailable")


def variation_letter(index: int) -> str:
    """Durty Cloth Tool's letter of a texture variation (a to z, shown in capitals)."""
    return chr(ord("A") + index) if 0 <= index < 26 else str(index + 1)
