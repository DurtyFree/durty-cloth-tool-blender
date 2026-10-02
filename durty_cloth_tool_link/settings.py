# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2026 Schmid Software Solutions (https://schmid-software.de)
"""Constants, public addresses and the English text the add-on shows. No Blender imports, so the tests can run
without Blender."""

from __future__ import annotations

import re
import urllib.parse
from typing import Dict, Optional, Tuple

from .dct_link import protocol

#: The add-on version. ``blender_manifest.toml`` must say the same (the tests check it). Experimental builds
#: carry ``-experimental.N``.
VERSION = "0.1.0"
EXTENSION_ID = "durty_cloth_tool_link"
PLUGIN_KIND = "blender"
HOST_NAME = "Blender"

SITE = "https://gta.clothing"
PLUGINS_PAGE_URL = "https://gta.clothing/account/plugins/"
#: The public guide for this add-on (the manifest's website). It is being written; the add-on links it
#: nowhere until it exists.
DOCS_URL = "https://docs.gta.clothing/creator-link/blender"
REPOSITORY_URL_PREFIX = "https://gta.clothing/link/blender/"
REPOSITORY_NAME = "Durty Cloth Tool"

#: Channels whose repository the add-on can add (development builds are never handed out).
CHANNELS: Tuple[Tuple[str, str, str], ...] = (
    ("release", "Release", "Stable versions"),
    ("experimental", "Experimental", "Early versions with the newest features"),
)
CHANNEL_IDS = tuple(channel for channel, _, _ in CHANNELS)


def channel_of_version(version: str) -> str:
    """The channel a build belongs to: Experimental versions carry ``-experimental.N``."""
    return "experimental" if "-experimental." in version else "release"


#: The channel of this build, reported to Durty Cloth Tool and gta.clothing.
CHANNEL = channel_of_version(VERSION)

TARGETS: Tuple[Tuple[str, str, str], ...] = (
    ("diffuse", "Diffuse", "The colour texture"),
    ("normal", "Normal", "The normal map"),
    ("specular", "Specular", "The specular map"),
)

FEATURE_LIVE_TEXTURE = "dct.link.liveTexture"
FEATURE_SAVE = "dct.link.save"
FEATURE_MODEL = "dct.link.model"

MAX_TEXTURE_EDGE = protocol.MAX_TEXTURE_EDGE
AUTO_PUSH_DELAY_DEFAULT = 1.5
AUTO_PUSH_DELAY_MIN = 0.5
AUTO_PUSH_DELAY_MAX = 30.0


def normalize_channel(channel: Optional[str]) -> str:
    return channel if channel in CHANNEL_IDS else "release"


def repository_url(channel: str) -> str:
    """The Blender extension repository for a channel."""
    return f"{REPOSITORY_URL_PREFIX}{normalize_channel(channel)}/index.json"


def repository_channel(url: Optional[str]) -> Optional[str]:
    """The channel of a Durty Cloth Tool repository address, or ``None`` for any other address."""
    if not url:
        return None
    for channel in CHANNEL_IDS:
        if url.rstrip("/") == repository_url(channel):
            return channel
    return None


def is_gta_clothing_url(url: Optional[str]) -> bool:
    """Links the add-on opens in the browser must stay on gta.clothing."""
    if not isinstance(url, str):
        return False
    parsed = urllib.parse.urlsplit(url)
    return parsed.scheme == "https" and parsed.hostname == "gta.clothing"


def normalize_pairing_code(text: Optional[str]) -> Optional[str]:
    """The six digits of a pairing code typed with or without spaces, or ``None``."""
    code = re.sub(r"[\s-]", "", text or "")
    return code if protocol.is_pairing_code(code) else None


def display_user_code(code: Optional[str]) -> str:
    """A sign-in code as gta.clothing shows it: four letters, a hyphen, four letters."""
    code = (code or "").replace("-", "").upper()
    return f"{code[:4]}-{code[4:]}" if len(code) == 8 else code


def check_stream_size(width: int, height: int) -> Optional[str]:
    """Why an image of this size cannot be streamed, or ``None``."""
    if width < 1 or height < 1:
        return "The image has no pixels. Open or create it first."
    if width > MAX_TEXTURE_EDGE or height > MAX_TEXTURE_EDGE:
        return f"Images larger than {MAX_TEXTURE_EDGE} pixels on a side cannot be streamed."
    return None


def clamp_auto_push_delay(seconds: float) -> float:
    return min(AUTO_PUSH_DELAY_MAX, max(AUTO_PUSH_DELAY_MIN, float(seconds)))


# ---- text -------------------------------------------------------------------------------------------

ONLINE_ACCESS_OFF = ("Blender's online access is off, so Durty Cloth Tool cannot be connected: every connection is "
                     "confirmed with your gta.clothing sign-in. Allow it in Preferences > System > Network.")
CONNECT_AN_APP = "In Durty Cloth Tool, click Connect an app (Options > Creator Link)"

STATE_TEXT: Dict[str, str] = {
    "idle": "Not connected",
    "connecting": "Looking for Durty Cloth Tool",
    "waiting": "Durty Cloth Tool not found, trying again",
    "hello": "Connecting",
    "pairing": "Waiting for pairing",
    "signing-in": "Waiting for sign-in",
    "authenticating": "Signing in",
    "ready": "Connected",
    "stopped": "Not connected",
}

LIVE_STATE_TEXT: Dict[str, str] = {
    "attached": "Showing on the ped",
    "notWorn": "The cloth is not worn in the preview",
    "paused": "Paused in Durty Cloth Tool",
}

CLOSE_REASON_TEXT: Dict[str, str] = {
    "closed": "Stopped",
    "replaced": "Another app took over",
    "itemRemoved": "The cloth was removed in Durty Cloth Tool",
    "projectClosed": "The project was closed in Durty Cloth Tool",
    "entitlementLost": "Your plan no longer includes this feature",
    "signedOut": "Durty Cloth Tool signed out",
    "disconnected": "The connection to Durty Cloth Tool was lost",
}

FEATURE_STATE_TEXT: Dict[str, str] = {
    "needsLicense": "Needs a Durty Cloth Tool license",
    "needsUltimate": "Needs Durty Cloth Tool Ultimate",
}

ERROR_TEXT: Dict[str, str] = {
    # Creator Link error codes (constants.json errorCodes)
    "malformed-message": "Durty Cloth Tool could not read a message from the add-on.",
    "invalid-message": "Durty Cloth Tool refused a message from the add-on as invalid.",
    "unknown-message-type": "Durty Cloth Tool does not know this request. Update Durty Cloth Tool.",
    "unexpected-message": "Durty Cloth Tool did not expect this request right now. Try again.",
    "message-too-large": "The data is too large to send.",
    "unsupported-protocol": "This add-on and Durty Cloth Tool use different link versions. Update both.",
    "plugin-too-old": "This add-on is too old for your Durty Cloth Tool. Update the add-on.",
    "dct-too-old": "Your Durty Cloth Tool is too old for this add-on. Update Durty Cloth Tool.",
    "not-authenticated": "The add-on is not signed in to Durty Cloth Tool yet.",
    "authentication-failed": "Durty Cloth Tool did not accept this Blender. Pair again.",
    "pairing-not-started": CONNECT_AN_APP + ", then click Request Code here within two minutes.",
    "pairing-expired": "The pairing code expired. " + CONNECT_AN_APP + " again, then click Request Code.",
    "pairing-code-invalid": "That is not the code Durty Cloth Tool shows.",
    "pairing-locked": "Too many wrong codes. Start pairing again in Durty Cloth Tool.",
    "account-mismatch": "Blender is signed in with another account than Durty Cloth Tool. Sign out here and sign in "
                        "with the account Durty Cloth Tool uses.",
    "dct-signed-out": "Durty Cloth Tool is signed out. Sign in to Durty Cloth Tool first.",
    "token-invalid": "Your sign-in was not accepted. Sign in again.",
    "needs-license": "This needs a Durty Cloth Tool license.",
    "needs-ultimate": "This needs Durty Cloth Tool Ultimate.",
    "no-project": "Open a project in Durty Cloth Tool first.",
    "no-focused-item": "Select a cloth in Durty Cloth Tool first.",
    "binding-in-use": "Another app is already editing this cloth texture or model.",
    "binding-not-found": "The cloth or texture no longer exists in Durty Cloth Tool.",
    "lease-not-found": "Durty Cloth Tool closed this preview. Start again.",
    "lease-limit": "Too many live previews are open. Stop one first.",
    "budget-exceeded": "Durty Cloth Tool has no room for another live preview. Stop one first.",
    "frame-out-of-bounds": "The image update did not fit the texture.",
    "frame-size-mismatch": "The image data did not match its size.",
    "unsupported-format": "Durty Cloth Tool does not accept this format here. Push models as Sollumz YDD XML.",
    "stale-revision": "The texture changed while saving. Save again.",
    "item-refused": "Durty Cloth Tool cannot change this item.",
    "game-required": "Durty Cloth Tool needs your GTA V installation for this. Set it up in Durty Cloth Tool.",
    "save-failed": "Durty Cloth Tool could not save. Its status bar has the details.",
    "busy": "Durty Cloth Tool is busy. Try again in a moment.",
    "rate-limited": "Too many requests. Wait a moment and try again.",
    "connection-limit": "Too many apps are connected to Durty Cloth Tool.",
    "not-paired": "Durty Cloth Tool no longer knows this Blender. Pair again.",
    "request-denied": "The request was refused in Durty Cloth Tool.",
    "model-rejected": "Durty Cloth Tool could not use this model. Check it in Sollumz and push again.",
    "internal-error": "Something went wrong. Try again, and restart Blender and Durty Cloth Tool if it keeps happening.",
    # Local codes of the link session
    "disconnected": "The connection to Durty Cloth Tool was lost.",
    "timeout": "Durty Cloth Tool did not answer in time.",
    "superseded": "A newer push replaced this one.",
    "cancelled": "Cancelled.",
    "closed": "The live preview is closed.",
    "server-proof-invalid": "The program on the link port is not the Durty Cloth Tool this Blender paired with. "
                            "Remove the pairing and pair again if you reinstalled Durty Cloth Tool.",
    "signed-out": "You signed out. Sign in to connect to Durty Cloth Tool.",
    "assertion-invalid": "gta.clothing sent an unexpected sign-in answer. Try again later.",
    "pixel-source-failed": "The image could not be read for streaming.",
    "callback-failed": "The add-on hit an unexpected problem. Try again.",
    # gta.clothing sign-in
    "offline": "Blender's online access is off. Allow it in Preferences > System > Network to sign in and connect.",
    "network": "gta.clothing could not be reached. Check your internet connection.",
    "invalid-response": "gta.clothing sent an unexpected answer. Try again later.",
    "tls": "The secure connection to gta.clothing failed. Check your network, proxy or antivirus settings.",
    "account_locked": "Your account is locked.",
    "discord_membership_required": "Your Discord account must be a member of the Pleb Masters Community Discord "
                                   "server.",
    "discord_unavailable": "Discord sign-in is unavailable right now. Try again later.",
    "plugin_update_required": "gta.clothing needs a newer version of this add-on. Update it.",
    "expired_token": "The sign-in code expired. Sign in again.",
    "access_denied": "The sign-in was denied.",
    "invalid_grant": "The sign-in code is no longer valid. Sign in again.",
    "session_invalid": "You were signed out. Sign in again.",
    "session_expired": "Your sign-in expired. Sign in again.",
    "session_revoked": "Your sign-in was ended on gta.clothing. Sign in again.",
    "refresh_in_progress": "Another program is renewing your sign-in. Try again in a moment.",
}

#: Codes after which the stored gta.clothing sign-in is gone.
SIGNED_OUT_CODES = frozenset(
    {"expired_token", "access_denied", "invalid_grant", "session_invalid", "session_expired", "session_revoked"}
)


def describe_pairing_required(reason: str, trusted: bool) -> str:
    """Why Durty Cloth Tool does not accept this Blender's pairing (dct_link's ``pairing-required`` event)."""
    if not trusted:
        return ("A program on the link port does not know this Blender's pairing. If you use more than one Durty "
                "Cloth Tool, start the one you paired with.")
    if reason == "removed":
        return "The pairing was removed in Durty Cloth Tool. Pair again to connect."
    if reason == "refused":
        return "Durty Cloth Tool refused this Blender's pairing. Pair again to connect."
    return "Durty Cloth Tool no longer knows this Blender (the pairing was removed there). Pair again to connect."


def describe_error(code: Optional[str], fallback: str = "") -> str:
    """English text for an error code. Unknown codes fall back to ``fallback`` or a generic sentence."""
    if code and code in ERROR_TEXT:
        return ERROR_TEXT[code]
    if fallback:
        return fallback
    return f"Something went wrong ({code})." if code else "Something went wrong."


def describe_state(state: Optional[str]) -> str:
    return STATE_TEXT.get(state or "idle", "Not connected")


def describe_live_state(state: Optional[str]) -> str:
    return LIVE_STATE_TEXT.get(state or "", "Sending")


def describe_close_reason(reason: Optional[str]) -> str:
    return CLOSE_REASON_TEXT.get(reason or "", "Stopped")


def describe_feature(state: Optional[str]) -> Optional[str]:
    """``None`` when the feature is available, otherwise why not."""
    if state is None or state == "entitled":
        return None
    return FEATURE_STATE_TEXT.get(state, "Not available with your Durty Cloth Tool plan")
