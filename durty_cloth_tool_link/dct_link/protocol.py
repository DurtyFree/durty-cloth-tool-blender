# SPDX-License-Identifier: MIT
# Copyright (c) Schmid Software Solutions (https://schmid-software.de)
"""Creator Link protocol 2 wire format: constants, validation and the frame codecs.

Everything a peer sends is untrusted. Decoding runs in this order:

1. the frame size is checked before anything is parsed;
2. nesting is bounded (16 levels, the root object is level 1) before the JSON parser runs, the whole frame
   must be UTF-8, and no string or property name may escape an unpaired surrogate;
3. the envelope (``v``, ``type``, ``id``, ``re``) is read before the message type is trusted;
4. every known property must have the JSON kind the message declares (a wrong kind is
   ``invalid-message``), unknown properties are ignored;
5. the message rules the schema cannot express run last and may report a specific code.

Decoding raises :class:`ProtocolError` whose ``code`` is one of :data:`ERROR_CODES`. Encoding runs the
same validation on the outgoing message and raises :class:`ProtocolError` for an invalid one.

The constants are embedded so the package works on its own.
"""

from __future__ import annotations

import json
import math
import re
from typing import Any, Callable, Dict, Iterable, List, Mapping, NamedTuple, Optional, Tuple, Union

__all__ = [
    "CONSTANTS",
    "ERROR_CODES",
    "MESSAGES",
    "TO_DCT",
    "TO_CLIENT",
    "TEXT",
    "BINARY",
    "ProtocolError",
    "BinaryMessage",
    "decode_text",
    "decode_binary",
    "encode_text",
    "encode_binary",
    "message_direction",
    "message_frame",
    "is_id",
    "is_guid",
    "is_bytes32",
    "is_user_code",
    "is_file_name",
    "is_install_id",
    "is_text",
    "is_semver",
    "is_host_version",
    "is_access_token",
    "is_feature_id",
    "is_https_url",
    "is_ped_model",
    "is_new_ped_model",
    "is_ped_type",
    "is_bone_name",
    "is_sha256_hex",
    "json_depth_exceeds",
]

# --------------------------------------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------------------------------------

CONSTANTS: Dict[str, Any] = {
    "protocol": {
        "name": "dct-creator-link",
        "major": 2,
        "minor": 0,
        "supportedMajors": {"min": 2, "max": 2},
    },
    "transport": {
        "path": "/dct/link/v1",
        "defaultPort": 47820,
        "portRangeEnd": 47829,
        "keepAliveSeconds": 15,
        "keepAliveTimeoutSeconds": 30,
    },
    "limits": {
        "maxControlMessageBytes": 65536,
        "maxBinaryHeaderBytes": 16384,
        "maxBinaryPayloadBytes": 67108864,
        "maxTextureEdge": 4096,
        "maxReportedTextureEdge": 16384,
        "maxJsonDepth": 16,
        "maxIdLength": 64,
        "maxTextLength": 128,
        "maxVersionLength": 64,
        "maxDiagnosticLength": 512,
        "maxAccessTokenLength": 8192,
        "maxFocusedTextures": 26,
        "maxFeatureStates": 64,
        "nonceBytes": 32,
        "maxModelFiles": 256,
        "maxFindings": 64,
        "minUvLayoutSize": 256,
        "userCodeLength": 8,
        "maxSwapMaterials": 64,
        "maxMaterialIndex": 1023,
        "maxThumbnailEdge": 256,
        "minThumbnailEdge": 16,
        "maxDrawableNumber": 65535,
        "openTextureAnswerSeconds": 20,
        "openModelAnswerSeconds": 60,
        "maxItemVariations": 26,
        "maxPedTemplates": 200,
        "maxPedBones": 255,
        "maxPedMarkers": 64,
        "maxPedRigParts": 64,
        "maxPedRigVertices": 300000,
        "maxPedRigTriangles": 600000,
        "maxPedRigReasons": 32,
        "maxPedRigWarnings": 32,
        "pedRigResultMinutes": 30,
        "maxPedAddBytes": 268435456,
        "maxPedAddChunkBytes": 33554432,
        "maxPedAddChunks": 8,
        "maxPedAddParts": 64,
    },
    "values": {
        "pluginKinds": ["photoshop", "photopea", "blender", "gimp", "krita", "substance"],
        "channels": ["release", "experimental", "development"],
        "liveTargets": ["diffuse", "normal", "specular"],
        "frameFormats": ["rgba8"],
        "saveModes": ["replace", "newVariation"],
        "featureStates": ["entitled", "needsLicense", "needsUltimate"],
        "liveStates": ["attached", "notWorn", "paused"],
        "liveCloseReasons": ["closed", "replaced", "itemRemoved", "projectClosed", "entitlementLost", "signedOut"],
        "incompatibleCodes": ["plugin-too-old", "dct-too-old", "unsupported-protocol"],
        "modelFormats": ["ydd-xml", "glb"],
        "genders": ["male", "female"],
        "findingSeverities": ["error", "warning", "info"],
        "findingCodes": [
            "non-power-of-two",
            "not-multiple-of-four",
            "too-large",
            "too-small",
            "size-changed",
            "palette-alpha",
            "cutout-alpha",
            "hair-ramp",
            "bc1-alpha",
            "rig-invalid",
            "rig-unchecked",
            "single-bone-rig",
            "hair-tint-unsupported",
            "rig-mismatch",
            "ped-budget",
            "ped-ragdoll-mismatch",
            "ped-rest-strain",
        ],
        "modelCloseReasons": ["closed", "replaced", "itemRemoved", "projectClosed", "entitlementLost", "signedOut"],
        "hostResultCodes": ["open-failed", "not-supported", "dependency-missing", "busy"],
        "drawableTypes": [
            "head",
            "berd",
            "hair",
            "uppr",
            "lowr",
            "hand",
            "feet",
            "teef",
            "accs",
            "task",
            "decl",
            "jbib",
            "p_head",
            "p_eyes",
            "p_ears",
            "p_mouth",
            "p_lhand",
            "p_rhand",
            "p_lwrist",
            "p_rwrist",
            "p_hip",
            "p_lfoot",
            "p_rfoot",
            "p_unk1",
            "p_unk2",
        ],
        "pedBodyMarkers": [
            "headTop",
            "chin",
            "neck",
            "chest",
            "pelvis",
            "shoulderL",
            "shoulderR",
            "elbowL",
            "elbowR",
            "wristL",
            "wristR",
            "hipL",
            "hipR",
            "kneeL",
            "kneeR",
            "ankleL",
            "ankleR",
            "toeL",
            "toeR",
        ],
        "pedOptionalMarkers": [
            "thumbBaseL",
            "thumbBaseR",
            "thumbTipL",
            "thumbTipR",
            "indexBaseL",
            "indexBaseR",
            "indexTipL",
            "indexTipR",
            "middleBaseL",
            "middleBaseR",
            "middleTipL",
            "middleTipR",
            "ringBaseL",
            "ringBaseR",
            "ringTipL",
            "ringTipR",
            "pinkyBaseL",
            "pinkyBaseR",
            "pinkyTipL",
            "pinkyTipR",
            "eyeL",
            "eyeR",
            "mouthL",
            "mouthR",
            "chinTip",
        ],
        "pedPartRoles": [
            "body",
            "head",
            "hair",
            "eyes",
            "teeth",
            "accessory",
        ],
        "pedDetailModes": [
            "off",
            "auto",
        ],
        "pedRestModels": [
            "volume",
            "linear",
        ],
        "pedRigStages": [
            "template",
            "markers",
            "skeleton",
            "weights",
            "rest",
            "report",
        ],
        "pedRigRefusals": [
            "marker_missing",
            "marker_invalid",
            "marker_degenerate",
            "marker_side",
            "not_upright",
            "limb_length",
            "asymmetric",
            "pose_unsupported",
            "marker_outside_body",
            "mesh_invalid",
            "mesh_too_large",
            "options_invalid",
            "template_invalid",
            "template_not_found",
            "game_required",
            "fit_invalid",
        ],
        "pedRigWarnings": [
            "marker_offset",
            "asymmetric_markers",
            "proportion_out_of_range",
            "ragdoll_mismatch",
            "low_coverage",
            "inpainted_large",
            "non_deforming_moved",
            "empty_rows_refilled",
            "floating_parts",
            "rest_strain",
            "fingers_fallback",
        ],
        "pedRigOutcomes": [
            "ready",
            "needsReview",
        ],
        "pedLayouts": [
            "packed",
            "streamed",
        ],
        "pedRagdolls": [
            "fred",
            "wilma",
            "fred-large",
            "wilma-large",
            "alien",
        ],
        "pedTemplateGroups": [
            "ambient",
            "freemode",
            "player",
            "cutscene",
            "story",
        ],
    },
    "errorCodes": [
        "malformed-message",
        "invalid-message",
        "unknown-message-type",
        "unexpected-message",
        "message-too-large",
        "unsupported-protocol",
        "plugin-too-old",
        "dct-too-old",
        "not-authenticated",
        "authentication-failed",
        "account-mismatch",
        "dct-signed-out",
        "disconnected",
        "token-invalid",
        "needs-license",
        "needs-ultimate",
        "no-project",
        "no-focused-item",
        "binding-in-use",
        "binding-not-found",
        "lease-not-found",
        "lease-limit",
        "budget-exceeded",
        "frame-out-of-bounds",
        "frame-size-mismatch",
        "unsupported-format",
        "stale-revision",
        "item-refused",
        "game-required",
        "save-failed",
        "busy",
        "rate-limited",
        "connection-limit",
        "request-denied",
        "model-rejected",
        "internal-error",
        "item-limit",
        "cancelled",
        "template-not-found",
        "mesh-too-large",
        "rig-refused",
        "upload-incomplete",
    ],
    "closeCodes": {
        "normal": 1000,
        "policyViolation": 1008,
        "messageTooBig": 1009,
        "internalError": 1011,
        "incompatible": 4001,
        "authenticationFailed": 4003,
        "rateLimited": 4008,
    },
}

_P = CONSTANTS["protocol"]
_T = CONSTANTS["transport"]
_L = CONSTANTS["limits"]
_V = CONSTANTS["values"]

PROTOCOL_NAME: str = _P["name"]
PROTOCOL_MAJOR: int = _P["major"]
PROTOCOL_MINOR: int = _P["minor"]
MIN_SUPPORTED_MAJOR: int = _P["supportedMajors"]["min"]
MAX_SUPPORTED_MAJOR: int = _P["supportedMajors"]["max"]

PATH: str = _T["path"]
DEFAULT_PORT: int = _T["defaultPort"]
PORT_RANGE_END: int = _T["portRangeEnd"]
KEEP_ALIVE_SECONDS: int = _T["keepAliveSeconds"]
KEEP_ALIVE_TIMEOUT_SECONDS: int = _T["keepAliveTimeoutSeconds"]

MAX_CONTROL_MESSAGE_BYTES: int = _L["maxControlMessageBytes"]
MAX_BINARY_HEADER_BYTES: int = _L["maxBinaryHeaderBytes"]
MAX_BINARY_PAYLOAD_BYTES: int = _L["maxBinaryPayloadBytes"]
MAX_TEXTURE_EDGE: int = _L["maxTextureEdge"]
MAX_REPORTED_TEXTURE_EDGE: int = _L["maxReportedTextureEdge"]
MAX_JSON_DEPTH: int = _L["maxJsonDepth"]
MAX_ID_LENGTH: int = _L["maxIdLength"]
MAX_TEXT_LENGTH: int = _L["maxTextLength"]
MAX_VERSION_LENGTH: int = _L["maxVersionLength"]
MAX_DIAGNOSTIC_LENGTH: int = _L["maxDiagnosticLength"]
MAX_ACCESS_TOKEN_LENGTH: int = _L["maxAccessTokenLength"]
MAX_FOCUSED_TEXTURES: int = _L["maxFocusedTextures"]
MAX_FEATURE_STATES: int = _L["maxFeatureStates"]
NONCE_BYTES: int = _L["nonceBytes"]
MAX_MODEL_FILES: int = _L["maxModelFiles"]
MAX_FINDINGS: int = _L["maxFindings"]
MIN_UV_LAYOUT_SIZE: int = _L["minUvLayoutSize"]
USER_CODE_LENGTH: int = _L["userCodeLength"]
MAX_SWAP_MATERIALS: int = _L["maxSwapMaterials"]
MAX_MATERIAL_INDEX: int = _L["maxMaterialIndex"]
MAX_THUMBNAIL_EDGE: int = _L["maxThumbnailEdge"]
MIN_THUMBNAIL_EDGE: int = _L["minThumbnailEdge"]
MAX_DRAWABLE_NUMBER: int = _L["maxDrawableNumber"]
#: How long DCT waits for the ``host.result`` that answers a ``host.openTexture`` or a ``host.openModel``.
OPEN_TEXTURE_ANSWER_SECONDS: int = _L["openTextureAnswerSeconds"]
OPEN_MODEL_ANSWER_SECONDS: int = _L["openModelAnswerSeconds"]
#: The colour variations one ``item.add`` may carry (the game's variation limit per drawable).
MAX_ITEM_VARIATIONS: int = _L["maxItemVariations"]
#: Custom peds: the template list, the skeleton, the rig request and its result, the upload.
MAX_PED_TEMPLATES: int = _L["maxPedTemplates"]
MAX_PED_BONES: int = _L["maxPedBones"]
MAX_PED_MARKERS: int = _L["maxPedMarkers"]
MAX_PED_RIG_PARTS: int = _L["maxPedRigParts"]
MAX_PED_RIG_VERTICES: int = _L["maxPedRigVertices"]
MAX_PED_RIG_TRIANGLES: int = _L["maxPedRigTriangles"]
MAX_PED_RIG_REASONS: int = _L["maxPedRigReasons"]
MAX_PED_RIG_WARNINGS: int = _L["maxPedRigWarnings"]
PED_RIG_RESULT_MINUTES: int = _L["pedRigResultMinutes"]
MAX_PED_ADD_BYTES: int = _L["maxPedAddBytes"]
MAX_PED_ADD_CHUNK_BYTES: int = _L["maxPedAddChunkBytes"]
MAX_PED_ADD_CHUNKS: int = _L["maxPedAddChunks"]
MAX_PED_ADD_PARTS: int = _L["maxPedAddParts"]
#: The fixed record sizes of the custom ped payloads: one bone record, one bone of a rig result (its record and its
#: pose matrix), one vertex of a rig result (rest position, four bone indices, four weights).
PED_BONE_RECORD_BYTES: int = 100
PED_RIG_BONE_BYTES: int = 164
PED_RIG_VERTEX_BYTES: int = 20

# Further wire limits.
MAX_REVISION: int = 9007199254740991  # JavaScript's largest safe integer
BINARY_LENGTH_PREFIX_BYTES: int = 4
MAX_UPDATE_URL_LENGTH: int = 512
MAX_PROTOCOL_MAJOR: int = 255
#: A whole binary frame: the length prefix, the largest header and the largest payload.
MAX_BINARY_FRAME_BYTES: int = BINARY_LENGTH_PREFIX_BYTES + MAX_BINARY_HEADER_BYTES + MAX_BINARY_PAYLOAD_BYTES

PLUGIN_KINDS: Tuple[str, ...] = tuple(_V["pluginKinds"])
CHANNELS: Tuple[str, ...] = tuple(_V["channels"])
LIVE_TARGETS: Tuple[str, ...] = tuple(_V["liveTargets"])
FRAME_FORMATS: Tuple[str, ...] = tuple(_V["frameFormats"])
SAVE_MODES: Tuple[str, ...] = tuple(_V["saveModes"])
FEATURE_STATES: Tuple[str, ...] = tuple(_V["featureStates"])
LIVE_STATES: Tuple[str, ...] = tuple(_V["liveStates"])
LIVE_CLOSE_REASONS: Tuple[str, ...] = tuple(_V["liveCloseReasons"])
INCOMPATIBLE_CODES: Tuple[str, ...] = tuple(_V["incompatibleCodes"])
MODEL_FORMATS: Tuple[str, ...] = tuple(_V["modelFormats"])
GENDERS: Tuple[str, ...] = tuple(_V["genders"])
FINDING_SEVERITIES: Tuple[str, ...] = tuple(_V["findingSeverities"])
FINDING_CODES: Tuple[str, ...] = tuple(_V["findingCodes"])
MODEL_CLOSE_REASONS: Tuple[str, ...] = tuple(_V["modelCloseReasons"])
#: Why a plugin could not open what DCT sent (``host.result.code``).
HOST_RESULT_CODES: Tuple[str, ...] = tuple(_V["hostResultCodes"])
#: The game's tokens for components and props (``focused.drawableType``).
DRAWABLE_TYPES: Tuple[str, ...] = tuple(_V["drawableTypes"])
PED_BODY_MARKERS: Tuple[str, ...] = tuple(_V["pedBodyMarkers"])
PED_OPTIONAL_MARKERS: Tuple[str, ...] = tuple(_V["pedOptionalMarkers"])
#: Every marker name a ``ped.rig`` may carry: the required body markers, then the optional finger and face markers.
PED_MARKERS: Tuple[str, ...] = PED_BODY_MARKERS + PED_OPTIONAL_MARKERS
PED_PART_ROLES: Tuple[str, ...] = tuple(_V["pedPartRoles"])
PED_DETAIL_MODES: Tuple[str, ...] = tuple(_V["pedDetailModes"])
PED_REST_MODELS: Tuple[str, ...] = tuple(_V["pedRestModels"])
PED_RIG_STAGES: Tuple[str, ...] = tuple(_V["pedRigStages"])
PED_RIG_REFUSALS: Tuple[str, ...] = tuple(_V["pedRigRefusals"])
PED_RIG_WARNINGS: Tuple[str, ...] = tuple(_V["pedRigWarnings"])
PED_RIG_OUTCOMES: Tuple[str, ...] = tuple(_V["pedRigOutcomes"])
PED_LAYOUTS: Tuple[str, ...] = tuple(_V["pedLayouts"])
PED_RAGDOLLS: Tuple[str, ...] = tuple(_V["pedRagdolls"])
PED_TEMPLATE_GROUPS: Tuple[str, ...] = tuple(_V["pedTemplateGroups"])
ERROR_CODES: Tuple[str, ...] = tuple(CONSTANTS["errorCodes"])
CLOSE_CODES: Dict[str, int] = dict(CONSTANTS["closeCodes"])

FORMAT_RGBA8 = "rgba8"
MODEL_YDD_XML = "ydd-xml"
MODEL_GLB = "glb"

MALFORMED_MESSAGE = "malformed-message"
INVALID_MESSAGE = "invalid-message"
UNKNOWN_MESSAGE_TYPE = "unknown-message-type"
UNEXPECTED_MESSAGE = "unexpected-message"
MESSAGE_TOO_LARGE = "message-too-large"
UNSUPPORTED_PROTOCOL = "unsupported-protocol"
FRAME_OUT_OF_BOUNDS = "frame-out-of-bounds"
FRAME_SIZE_MISMATCH = "frame-size-mismatch"
UNSUPPORTED_FORMAT = "unsupported-format"

TO_DCT = "toDct"
TO_CLIENT = "toClient"
TEXT = "text"
BINARY = "binary"

_ERROR_CODE_SET = frozenset(ERROR_CODES)


class ProtocolError(Exception):
    """A frame or message that breaks the Creator Link rules. ``code`` is a stable error code. For
    ``unsupported-protocol``, ``version`` is the major the frame was written in."""

    def __init__(self, code: str, detail: str = "", version: Optional[int] = None) -> None:
        super().__init__(f"{code}: {detail}" if detail else code)
        self.code = code
        self.detail = detail
        self.version = version


class BinaryMessage(NamedTuple):
    """A decoded binary frame: the validated header and a zero-copy view of the payload."""

    header: Dict[str, Any]
    payload: memoryview


# --------------------------------------------------------------------------------------------------
# Field shapes (mirror the schema patterns; lengths count code points)
# --------------------------------------------------------------------------------------------------

_ID_RE = re.compile(r"[A-Za-z0-9_-]{1,64}")
_GUID_RE = re.compile(r"[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}")
_BYTES32_RE = re.compile(r"[A-Za-z0-9_-]{43}")
_USER_CODE_RE = re.compile(r"[BCDFGHJKLMNPQRSTVWXZ]{8}")
_FILE_NAME_RE = re.compile(r"[A-Za-z0-9_-][A-Za-z0-9_.-]{0,127}")
#: Windows device names: a file whose name before the first ``.`` is one of them cannot be written.
_RESERVED_NAME_RE = re.compile(r"(?:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\.|$)", re.IGNORECASE | re.ASCII)
_SEMVER_RE = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?")
_HOST_VERSION_RE = re.compile(r"[0-9A-Za-z._+ -]{1,64}")
_ACCESS_TOKEN_RE = re.compile(r"[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]*")
_FEATURE_ID_RE = re.compile(r"[a-z]+(?:\.[A-Za-z]+)+")
# C0, DEL and C1 controls, plus unpaired surrogates (a JSON escape can produce one).
_NOT_PRINTABLE_RE = re.compile("[\u0000-\u001f\u007f-\u009f\ud800-\udfff]")
_SURROGATE_RE = re.compile("[\ud800-\udfff]")
_HTTPS_URL_RE = re.compile(r"https://[!-~]+")
_PED_MODEL_RE = re.compile(r"[A-Za-z0-9_]{1,63}")
_NEW_PED_MODEL_RE = re.compile(r"[a-z][a-z0-9_]{2,31}")
_PED_TYPE_RE = re.compile(r"[A-Za-z0-9_]{1,32}")
_BONE_NAME_RE = re.compile(r"[!-~]{1,64}")
_SHA256_RE = re.compile(r"[0-9a-f]{64}")


def is_id(value: Any) -> bool:
    return isinstance(value, str) and _ID_RE.fullmatch(value) is not None


def is_guid(value: Any) -> bool:
    """Hex digits in the hyphenated 8-4-4-4-12 layout only (no braces, signs or 0x prefixes)."""
    return isinstance(value, str) and _GUID_RE.fullmatch(value) is not None


def is_bytes32(value: Any) -> bool:
    """32 bytes as unpadded base64url: exactly 43 characters of the URL-safe alphabet."""
    return isinstance(value, str) and _BYTES32_RE.fullmatch(value) is not None


def is_user_code(value: Any) -> bool:
    return isinstance(value, str) and _USER_CODE_RE.fullmatch(value) is not None


def is_file_name(value: Any) -> bool:
    """A bare file name: letters, digits, ``_ - .``, not starting with ``.``, no ``..``, 1 to 128 chars, and the part
    before the first ``.`` is not a Windows reserved device name (``CON``, ``PRN``, ``AUX``, ``NUL``, ``COM1`` to
    ``COM9``, ``LPT1`` to ``LPT9``, any case)."""
    return (
        isinstance(value, str)
        and ".." not in value
        and _FILE_NAME_RE.fullmatch(value) is not None
        and _RESERVED_NAME_RE.match(value) is None
    )


def is_install_id(value: Any) -> bool:
    """A plugin installation's random id: a GUID (see :func:`is_guid`)."""
    return is_guid(value)


def _is_printable(value: str, max_code_points: int) -> bool:
    return len(value) <= max_code_points and _NOT_PRINTABLE_RE.search(value) is None


def is_text(value: Any, max_length: int = MAX_TEXT_LENGTH) -> bool:
    """Display text: 1 to ``max_length`` code points, no C0, DEL or C1 control characters."""
    return isinstance(value, str) and len(value) > 0 and _is_printable(value, max_length)


def is_diagnostic(value: Any) -> bool:
    """An English diagnostic: may be empty, no control characters, at most 512 code points."""
    return isinstance(value, str) and _is_printable(value, MAX_DIAGNOSTIC_LENGTH)


def is_semver(value: Any) -> bool:
    return (
        isinstance(value, str)
        and 0 < len(value) <= MAX_VERSION_LENGTH
        and _SEMVER_RE.fullmatch(value) is not None
    )


def is_host_version(value: Any) -> bool:
    return isinstance(value, str) and _HOST_VERSION_RE.fullmatch(value) is not None


def is_access_token(value: Any) -> bool:
    """A compact JWT (a link access token or a sign-in assertion): three base64url segments, the first two
    non-empty, at most 8192 characters."""
    return (
        isinstance(value, str)
        and 0 < len(value) <= MAX_ACCESS_TOKEN_LENGTH
        and _ACCESS_TOKEN_RE.fullmatch(value) is not None
    )


def is_feature_id(value: Any) -> bool:
    return isinstance(value, str) and len(value) <= MAX_ID_LENGTH and _FEATURE_ID_RE.fullmatch(value) is not None


def is_ped_model(value: Any) -> bool:
    """A ped model name as the game names it: 1 to 63 letters, digits and underscores."""
    return isinstance(value, str) and _PED_MODEL_RE.fullmatch(value) is not None


def is_new_ped_model(value: Any) -> bool:
    """The model name of a new custom ped: a lowercase letter, then 2 to 31 lowercase letters, digits or underscores."""
    return isinstance(value, str) and _NEW_PED_MODEL_RE.fullmatch(value) is not None


def is_ped_type(value: Any) -> bool:
    """A ped type as ``peds.meta`` names it (CIVMALE, GANG_1)."""
    return isinstance(value, str) and _PED_TYPE_RE.fullmatch(value) is not None


def is_bone_name(value: Any) -> bool:
    """A bone name: 1 to 64 printable ASCII characters without spaces."""
    return isinstance(value, str) and _BONE_NAME_RE.fullmatch(value) is not None


def is_sha256_hex(value: Any) -> bool:
    """A SHA-256 as 64 lowercase hex digits."""
    return isinstance(value, str) and _SHA256_RE.fullmatch(value) is not None


def is_https_url(value: Any) -> bool:
    """``https://`` followed by printable ASCII without spaces, at most 512 characters."""
    return isinstance(value, str) and len(value) <= MAX_UPDATE_URL_LENGTH and _HTTPS_URL_RE.fullmatch(value) is not None


def _in_range(value: Any, minimum: int, maximum: int) -> bool:
    return value is not None and minimum <= value <= maximum


# --------------------------------------------------------------------------------------------------
# Bounded JSON parsing
# --------------------------------------------------------------------------------------------------


class _JsonObject(dict):
    """A parsed JSON object. ``earlier`` keeps values of a repeated property that a later one replaced.

    The last occurrence wins, but every occurrence must have the right kind, so the kind check below
    looks at the earlier values too.
    """

    __slots__ = ("earlier",)

    def __init__(self) -> None:
        super().__init__()
        self.earlier: Optional[Dict[str, List[Any]]] = None


class _JsonBigInteger:
    """An integer literal too long for an exact int conversion. It is never a valid field value."""

    __slots__ = ("text",)

    def __init__(self, text: str) -> None:
        self.text = text

    def __repr__(self) -> str:
        return f"_JsonBigInteger({self.text[:24]}...)"


def _object_pairs(pairs: List[Tuple[str, Any]]) -> _JsonObject:
    obj = _JsonObject()
    for key, value in pairs:
        if key in obj:
            if obj.earlier is None:
                obj.earlier = {}
            obj.earlier.setdefault(key, []).append(obj[key])
        obj[key] = value
    return obj


def _parse_int(text: str) -> Union[int, _JsonBigInteger]:
    # Every integer field fits in a signed 64-bit value (at most 19 digits). Much longer literals never
    # reach int(), which refuses very long literals since Python 3.10.7 and would make valid JSON look broken.
    if len(text.lstrip("-")) > 20:
        return _JsonBigInteger(text)
    return int(text)


def _reject_constant(name: str) -> Any:
    raise ValueError(f"{name} is not JSON")


_DECODER = json.JSONDecoder(object_pairs_hook=_object_pairs, parse_int=_parse_int, parse_constant=_reject_constant)

# The bytes that matter for nesting: quotes, backslashes and the four brackets.
_SIGNIFICANT_RE = re.compile(rb'["\\\[\]{}]')


def json_depth_exceeds(data: Union[bytes, bytearray, memoryview], limit: int) -> bool:
    """True when objects and arrays in ``data`` nest deeper than ``limit`` (the root is level 1).

    One pass over the significant bytes, so the cost grows linearly with the input whatever it contains
    (unterminated strings and long runs of escaped quotes included). Brackets inside strings do not count. The
    input need not be valid JSON; the parser that runs afterwards rejects anything else.
    """
    depth = 0
    in_string = False
    skip = -1  # the position of a byte escaped by a backslash
    for match in _SIGNIFICANT_RE.finditer(bytes(data)):
        position = match.start()
        if position == skip:
            continue
        byte = data[position]
        if in_string:
            if byte == 0x5C:  # backslash: the next byte is escaped
                skip = position + 1
            elif byte == 0x22:
                in_string = False
        elif byte == 0x22:
            in_string = True
        elif byte == 0x7B or byte == 0x5B:
            depth += 1
            if depth > limit:
                return True
        elif byte == 0x7D or byte == 0x5D:
            depth -= 1
    return False


def _holds_only_text(value: Any) -> bool:
    """False when any string or property name holds an unpaired surrogate. A JSON escape can produce one; it is
    valid JSON syntax but not text. The parser has already joined every valid escaped pair into one code point."""
    stack = [value]
    while stack:
        item = stack.pop()
        if isinstance(item, str):
            if _SURROGATE_RE.search(item) is not None:
                return False
        elif isinstance(item, dict):
            for key, child in item.items():
                if _SURROGATE_RE.search(key) is not None:
                    return False
                stack.append(child)
            earlier = getattr(item, "earlier", None)
            if earlier:
                for values in earlier.values():
                    stack.extend(values)
        elif isinstance(item, list):
            stack.extend(item)
    return True


def _parse_json(data: bytes) -> Any:
    if json_depth_exceeds(data, MAX_JSON_DEPTH):
        raise ProtocolError(MALFORMED_MESSAGE, "nesting is deeper than 16 levels")
    try:
        text = data.decode("utf-8")  # the whole frame, including strings nobody reads
        value = _DECODER.decode(text)
    except (UnicodeDecodeError, ValueError, RecursionError) as exc:
        raise ProtocolError(MALFORMED_MESSAGE, "not UTF-8 JSON") from exc
    if not _holds_only_text(value):
        raise ProtocolError(MALFORMED_MESSAGE, "a string escapes an unpaired surrogate")
    return value


# --------------------------------------------------------------------------------------------------
# Known-property kinds (the JSON kind each property must have)
# --------------------------------------------------------------------------------------------------

_STR = "str"
_INT32 = "int32"
_INT64 = "int64"
_INT32_REQUIRED = "int32!"
_BOOL = "bool"
#: Any finite JSON number (coordinates, fractions, measures); never a bool.
_NUMBER = "number"

_INT32_MIN, _INT32_MAX = -(2**31), 2**31 - 1
_INT64_MIN, _INT64_MAX = -(2**63), 2**63 - 1

Kind = Union[str, Tuple[str, Any]]


def _obj(spec: Dict[str, Kind]) -> Tuple[str, Dict[str, Kind]]:
    return ("obj", spec)


def _list(item: Kind) -> Tuple[str, Kind]:
    return ("list", item)


def _map(value: Kind) -> Tuple[str, Kind]:
    """An object whose keys are data (marker names) and whose values all have one kind."""
    return ("map", value)


def _is_integer(value: Any) -> bool:
    return type(value) is int  # bool is an int subclass and is not a JSON number


def _kind_ok(value: Any, kind: Kind) -> bool:
    if value is None:
        return kind != _INT32_REQUIRED
    if kind == _STR:
        # A known string must be text: an unpaired surrogate escape is refused.
        return isinstance(value, str) and _SURROGATE_RE.search(value) is None
    if kind == _INT32 or kind == _INT32_REQUIRED:
        return _is_integer(value) and _INT32_MIN <= value <= _INT32_MAX
    if kind == _INT64:
        return _is_integer(value) and _INT64_MIN <= value <= _INT64_MAX
    if kind == _BOOL:
        return isinstance(value, bool)
    if kind == _NUMBER:
        return type(value) in (int, float) and math.isfinite(value)
    tag, inner = kind  # type: ignore[misc]
    if tag == "obj":
        return isinstance(value, dict) and _kinds_ok(value, inner)
    if tag == "list":
        return isinstance(value, list) and all(_kind_ok(item, inner) for item in value)
    if tag == "map":
        if not isinstance(value, dict):
            return False
        earlier = getattr(value, "earlier", None) or {}
        return all(_kind_ok(item, inner) for item in value.values()) and all(
            _kind_ok(item, inner) for items in earlier.values() for item in items
        )
    raise AssertionError(f"unknown kind {kind!r}")


def _kinds_ok(obj: Mapping[str, Any], spec: Mapping[str, Kind]) -> bool:
    earlier = getattr(obj, "earlier", None)
    for name, kind in spec.items():
        if name in obj and not _kind_ok(obj[name], kind):
            return False
        if earlier and name in earlier and not all(_kind_ok(v, kind) for v in earlier[name]):
            return False
    return True


_ENVELOPE: Dict[str, Kind] = {"v": _INT32_REQUIRED, "type": _STR, "id": _STR, "re": _STR}
_BINARY_ENVELOPE: Dict[str, Kind] = dict(_ENVELOPE, payloadLength=_INT64)

_BINDING = _obj({"clothId": _STR, "textureId": _STR})
_RECT = _obj({"x": _INT32, "y": _INT32, "w": _INT32, "h": _INT32})
_FEATURE_STATES = _list(_obj({"id": _STR, "state": _STR}))
_FINDINGS = _list(_obj({"code": _STR, "severity": _STR}))
_PROJECT = _obj({"name": _STR})
_FOCUSED = _obj(
    {
        "clothId": _STR,
        "name": _STR,
        "selectedTextureId": _STR,
        "textures": _list(_obj({"textureId": _STR, "name": _STR, "width": _INT32, "height": _INT32})),
        "targets": _list(_STR),
        "drawableType": _STR,
        "gender": _STR,
        "collection": _STR,
        "number": _INT32,
    }
)
_MODEL_FILES = _list(_obj({"name": _STR, "length": _INT64}))
_PED_MARKERS_KIND = _map(_list(_NUMBER))
_PED_PROPORTIONS = _obj({"height": _NUMBER, "shoulders": _NUMBER, "hips": _NUMBER, "arm": _NUMBER, "leg": _NUMBER, "torso": _NUMBER})
_PED_REPORT = _obj(
    {
        "outcome": _STR,
        "confidence": _NUMBER,
        "warnings": _list(_obj({"code": _STR, "count": _INT32, "value": _NUMBER, "markers": _list(_STR), "template": _STR})),
        "markers": _PED_MARKERS_KIND,
        "markerMoves": _map(_NUMBER),
        "character": _PED_PROPORTIONS,
        "template": _PED_PROPORTIONS,
        "suggestedTemplate": _STR,
        "proxy": _BOOL,
    }
)


# --------------------------------------------------------------------------------------------------
# Message rules (what the schema cannot express)
# --------------------------------------------------------------------------------------------------

Validator = Callable[[Mapping[str, Any]], Optional[str]]


def _check(valid: bool) -> Optional[str]:
    return None if valid else INVALID_MESSAGE


def _binding_ok(binding: Any) -> bool:
    return binding is not None and is_guid(binding.get("clothId")) and is_guid(binding.get("textureId"))


def _optional_binding_ok(binding: Any) -> bool:
    return binding is None or _binding_ok(binding)


def _one_of(value: Any, allowed: Iterable[str]) -> bool:
    return isinstance(value, str) and value in allowed


def _feature_states_ok(states: Any) -> bool:
    if states is None or len(states) > MAX_FEATURE_STATES:
        return False
    return all(
        state is not None and is_feature_id(state.get("id")) and _one_of(state.get("state"), FEATURE_STATES)
        for state in states
    )


def _findings_ok(findings: Any) -> bool:
    if findings is None or len(findings) > MAX_FINDINGS:
        return False
    return all(
        finding is not None
        and _one_of(finding.get("code"), FINDING_CODES)
        and _one_of(finding.get("severity"), FINDING_SEVERITIES)
        for finding in findings
    )


def _project_ok(project: Any) -> bool:
    return project is None or is_text(project.get("name"))


def _focused_ok(item: Any) -> bool:
    if item is None:
        return True
    if not is_guid(item.get("clothId")) or not is_text(item.get("name")):
        return False
    selected = item.get("selectedTextureId")
    if selected is not None and not is_guid(selected):
        return False
    # Item metadata: each optional, each valid when present.
    drawable_type, gender = item.get("drawableType"), item.get("gender")
    collection, number = item.get("collection"), item.get("number")
    if (
        (drawable_type is not None and not _one_of(drawable_type, DRAWABLE_TYPES))
        or (gender is not None and not _one_of(gender, GENDERS))
        or (collection is not None and not is_text(collection))
        or (number is not None and not _in_range(number, 0, MAX_DRAWABLE_NUMBER))
    ):
        return False
    textures = item.get("textures")
    if textures is None or len(textures) > MAX_FOCUSED_TEXTURES:
        return False
    for texture in textures:
        # width and height are optional (DCT may not know a texture's size); when present they are 1..16384.
        width, height = texture.get("width") if texture else None, texture.get("height") if texture else None
        if (
            texture is None
            or not is_guid(texture.get("textureId"))
            or not is_text(texture.get("name"))
            or (width is not None and not _in_range(width, 1, MAX_REPORTED_TEXTURE_EDGE))
            or (height is not None and not _in_range(height, 1, MAX_REPORTED_TEXTURE_EDGE))
        ):
            return False
    targets = item.get("targets")
    if targets is None or len(targets) > len(LIVE_TARGETS):
        return False
    seen = set()
    for target in targets:
        if not _one_of(target, LIVE_TARGETS) or target in seen:
            return False
        seen.add(target)
    return True


def _ok_code_ok(message: Mapping[str, Any], codes: Iterable[str] = _ERROR_CODE_SET) -> bool:
    """``code`` is present exactly when ``ok`` is false, and is one of ``codes``."""
    ok = message.get("ok")
    if ok is None:
        return False
    code = message.get("code")
    return code is None if ok else _one_of(code, codes)


def _payload_in(message: Mapping[str, Any], minimum: int) -> bool:
    return _in_range(message.get("payloadLength"), minimum, MAX_BINARY_PAYLOAD_BYTES)


def _image_code(message: Mapping[str, Any]) -> Optional[str]:
    width, height, payload = message.get("width"), message.get("height"), message.get("payloadLength")
    if not _in_range(width, 1, MAX_TEXTURE_EDGE) or not _in_range(height, 1, MAX_TEXTURE_EDGE) or payload is None:
        return INVALID_MESSAGE
    if not _one_of(message.get("format"), FRAME_FORMATS):
        return UNSUPPORTED_FORMAT
    return None if payload == width * height * 4 else FRAME_SIZE_MISMATCH


def _hello(m: Mapping[str, Any]) -> Optional[str]:
    protocol, plugin, host = m.get("protocol"), m.get("plugin"), m.get("host")
    return _check(
        protocol is not None
        and _in_range(protocol.get("min"), 1, MAX_PROTOCOL_MAJOR)
        and _in_range(protocol.get("max"), protocol.get("min"), MAX_PROTOCOL_MAJOR)
        and _in_range(protocol.get("minor"), 0, MAX_PROTOCOL_MAJOR)
        and plugin is not None
        and _one_of(plugin.get("kind"), PLUGIN_KINDS)
        and is_semver(plugin.get("version"))
        and _one_of(plugin.get("channel"), CHANNELS)
        and host is not None
        and is_text(host.get("name"))
        and is_host_version(host.get("version"))
        and is_install_id(m.get("installId"))
        and is_bytes32(m.get("clientNonce"))
    )


def _live_frame(m: Mapping[str, Any]) -> Optional[str]:
    rect = m.get("rect")
    if (
        not is_id(m.get("lease"))
        or not _in_range(m.get("revision"), 1, MAX_REVISION)
        or m.get("payloadLength") is None
        or rect is None
        or any(rect.get(k) is None for k in ("x", "y", "w", "h"))
    ):
        return INVALID_MESSAGE
    if not _one_of(m.get("format"), FRAME_FORMATS):
        return UNSUPPORTED_FORMAT
    x, y, w, h = rect["x"], rect["y"], rect["w"], rect["h"]
    if x < 0 or y < 0 or w < 1 or h < 1 or x + w > MAX_TEXTURE_EDGE or y + h > MAX_TEXTURE_EDGE:
        return FRAME_OUT_OF_BOUNDS
    return None if m["payloadLength"] == w * h * 4 else FRAME_SIZE_MISMATCH


def model_push_problem(fmt: Any, files: Any, lease: Any = None, binding: Any = None) -> Optional[str]:
    """Checks a model push's file list. Returns ``None`` or ``invalid-message``; shared with the encoder."""
    if (
        (lease is not None and not is_id(lease))
        or (binding is not None and not _binding_ok(binding))
        or (lease is not None and binding is not None)
        or not _one_of(fmt, MODEL_FORMATS)
    ):
        return INVALID_MESSAGE
    return model_files_problem(fmt, files)


def model_files_problem(fmt: str, files: Any) -> Optional[str]:
    """The file rules of a model frame (``model.push``, ``host.openModel``): bare names, unique ignoring case,
    exactly one model file of the format and otherwise only ``*.dds`` (nothing beside a GLB). Returns ``None`` or
    ``invalid-message``; the caller checks the lengths against the payload."""
    if files is None or len(files) == 0 or len(files) > MAX_MODEL_FILES:
        return INVALID_MESSAGE
    names = set()
    models = 0
    for entry in files:
        if entry is None:
            return INVALID_MESSAGE
        name, length = entry.get("name"), entry.get("length")
        if not is_file_name(name) or not _in_range(length, 1, MAX_BINARY_PAYLOAD_BYTES):
            return INVALID_MESSAGE
        folded = name.lower()  # names are ASCII, so this is ordinal ignore-case
        if folded in names:
            return INVALID_MESSAGE
        names.add(folded)
        is_model = folded.endswith(".glb") if fmt == MODEL_GLB else folded.endswith(".ydd.xml")
        if is_model:
            models += 1
        elif fmt == MODEL_GLB or not folded.endswith(".dds"):
            return INVALID_MESSAGE
    return None if models == 1 else INVALID_MESSAGE


def _model_push(m: Mapping[str, Any]) -> Optional[str]:
    if not _payload_in(m, 1):
        return INVALID_MESSAGE
    files = m.get("files")
    problem = model_push_problem(m.get("format"), files, m.get("lease"), m.get("binding"))
    if problem is not None:
        return problem
    total = sum(entry["length"] for entry in files)
    return None if total == m.get("payloadLength") else FRAME_SIZE_MISMATCH


def _host_open_model(m: Mapping[str, Any]) -> Optional[str]:
    """Always with an id (what ``host.result`` answers), XML drawables only, the file rules of ``model.push``."""
    if (
        not is_id(m.get("id"))
        or not _payload_in(m, 1)
        or not _binding_ok(m.get("binding"))
        or not is_text(m.get("name"))
        or m.get("format") != MODEL_YDD_XML
    ):
        return INVALID_MESSAGE
    files = m.get("files")
    problem = model_files_problem(MODEL_YDD_XML, files)
    if problem is not None:
        return problem
    total = sum(entry["length"] for entry in files)
    return None if total == m.get("payloadLength") else FRAME_SIZE_MISMATCH


def _skeleton_template_data(m: Mapping[str, Any]) -> Optional[str]:
    """Exactly one file, a ``*.ydd.xml`` under the file rules of ``model.push``, whose length is the payload."""
    files = m.get("files")
    if (
        not _one_of(m.get("gender"), GENDERS)
        or m.get("format") != MODEL_YDD_XML
        or not _payload_in(m, 1)
        or files is None
        or len(files) != 1
    ):
        return INVALID_MESSAGE
    problem = model_files_problem(MODEL_YDD_XML, files)  # one file of the ydd-xml rules is exactly the model XML
    if problem is not None:
        return problem
    return None if files[0]["length"] == m.get("payloadLength") else FRAME_SIZE_MISMATCH


def is_prop_type(drawable_type: Any) -> bool:
    """A prop's token (``p_head``, ``p_eyes`` ...): props take no skin."""
    return isinstance(drawable_type, str) and drawable_type.startswith("p_")


def item_files_reason(files: Any, variations: Any) -> Optional[str]:
    """Why the files and variations of an ``item.add`` break the rules, as an English sentence for a developer, or
    ``None``. The rules: the bare-name rules of ``model.push`` (unique ignoring case, no empty file), exactly one
    ``*.ydd.xml`` and otherwise only ``*.dds`` and ``*.png``; 1 to :data:`MAX_ITEM_VARIATIONS` variations, each with a
    display name and naming a ``*.png`` or ``*.dds`` of the files (never the model), no two the same file ignoring
    case, and every ``*.png`` named by a variation. The caller checks the lengths against the payload."""
    if files is None or len(files) == 0 or len(files) > MAX_MODEL_FILES:
        return f"an item carries 1 to {MAX_MODEL_FILES} files"
    if variations is None or not 1 <= len(variations) <= MAX_ITEM_VARIATIONS:
        return f"an item has 1 to {MAX_ITEM_VARIATIONS} colour variations"
    names = set()
    pictures = set()
    models = 0
    for entry in files:
        if entry is None:
            return "a file entry is missing"
        name, length = entry.get("name"), entry.get("length")
        if not is_file_name(name):
            return (
                f"{name!r} is not a bare file name (letters, digits, _ - ., not starting with '.', no '..', "
                "not a Windows device name)"
            )
        if not _in_range(length, 1, MAX_BINARY_PAYLOAD_BYTES):
            return f"{name} is empty or larger than one binary frame allows"
        folded = name.lower()  # names are ASCII, so this is ordinal ignore-case
        if folded in names:
            return f"two files are named {name} (names are unique ignoring case)"
        names.add(folded)
        if folded.endswith(".ydd.xml"):
            models += 1
        elif folded.endswith(".png"):
            pictures.add(folded)
        elif not folded.endswith(".dds"):
            return f"{name} is neither the model (*.ydd.xml) nor a texture (*.dds) or variation picture (*.png)"
    if models != 1:
        return "an item carries exactly one model file (*.ydd.xml)"
    used = set()
    for variation in variations:
        if variation is None:
            return "a variation is missing"
        file, title = variation.get("file"), variation.get("name")
        if not is_text(title):
            return "a variation's name is 1 to 128 characters of display text"
        if not is_file_name(file) or file.lower() not in names:
            return f"the variation {title} names {file!r}, which is not one of the files"
        folded = file.lower()
        if folded.endswith(".ydd.xml"):
            return f"the variation {title} names the model file; it names its diffuse (*.png or *.dds)"
        if folded in used:
            return f"two variations name {file} (each variation has a diffuse of its own)"
        used.add(folded)
    unnamed = sorted(pictures - used)
    if unnamed:
        return f"{unnamed[0]} is a picture no variation names (a *.png is always a variation's diffuse)"
    return None


def item_files_problem(files: Any, variations: Any) -> Optional[str]:
    """The file and variation rules of ``item.add`` (see :func:`item_files_reason`). Returns ``None`` or
    ``invalid-message``; the caller checks the lengths against the payload."""
    return None if item_files_reason(files, variations) is None else INVALID_MESSAGE


def _item_add(m: Mapping[str, Any]) -> Optional[str]:
    """Always with an id (what ``item.addResult`` names), XML drawables only, skin only on a component, the file and
    variation rules of :func:`item_files_reason`; the lengths add up to the payload."""
    drawable_type, skin = m.get("drawableType"), m.get("skin")
    if (
        not is_id(m.get("id"))
        or not _payload_in(m, 1)
        or m.get("format") != MODEL_YDD_XML
        or not _one_of(drawable_type, DRAWABLE_TYPES)
        or not _one_of(m.get("gender"), GENDERS)
        or skin is None
        or (skin and is_prop_type(drawable_type))
        or not is_text(m.get("name"))
    ):
        return INVALID_MESSAGE
    files = m.get("files")
    problem = item_files_problem(files, m.get("variations"))
    if problem is not None:
        return problem
    total = sum(entry["length"] for entry in files)
    return None if total == m.get("payloadLength") else FRAME_SIZE_MISMATCH


def _item_add_result(m: Mapping[str, Any]) -> Optional[str]:
    """``binding`` present and ``code`` absent exactly when ``ok`` is true; ``code`` (any protocol error code) present
    and ``binding`` absent exactly when it is false. ``findings`` is always there."""
    ok, code, binding = m.get("ok"), m.get("code"), m.get("binding")
    if ok is None or not is_id(m.get("re")):
        return INVALID_MESSAGE
    paired = (code is None and _binding_ok(binding)) if ok else (_one_of(code, _ERROR_CODE_SET) and binding is None)
    return _check(paired and _findings_ok(m.get("findings")))


def _thumbnail_image(m: Mapping[str, Any]) -> Optional[str]:
    if (
        _binding_ok(m.get("binding"))
        and _in_range(m.get("width"), 1, MAX_THUMBNAIL_EDGE)
        and _in_range(m.get("height"), 1, MAX_THUMBNAIL_EDGE)
    ):
        return _image_code(m)
    return INVALID_MESSAGE


def _model_glb_data(m: Mapping[str, Any]) -> Optional[str]:
    swap = m.get("swapMaterials")
    if not _binding_ok(m.get("binding")) or not _payload_in(m, 1) or swap is None or len(swap) > MAX_SWAP_MATERIALS:
        return INVALID_MESSAGE
    seen = set()
    for index in swap:
        if index < 0 or index > MAX_MATERIAL_INDEX or index in seen:
            return INVALID_MESSAGE
        seen.add(index)
    return None


def _textured_image(m: Mapping[str, Any]) -> Optional[str]:
    if _binding_ok(m.get("binding")) and _one_of(m.get("target"), LIVE_TARGETS) and is_text(m.get("name")):
        return _image_code(m)
    return INVALID_MESSAGE


def _incompatible(m: Mapping[str, Any]) -> Optional[str]:
    dct = m.get("dct")
    if dct is None:
        return INVALID_MESSAGE
    protocol = dct.get("protocol")
    minimum, url = m.get("minimumPluginVersion"), m.get("updateUrl")
    return _check(
        _one_of(m.get("code"), INCOMPATIBLE_CODES)
        and is_semver(dct.get("version"))
        and protocol is not None
        and _in_range(protocol.get("min"), 1, MAX_PROTOCOL_MAJOR)
        and _in_range(protocol.get("max"), protocol.get("min"), MAX_PROTOCOL_MAJOR)
        and (minimum is None or is_semver(minimum))
        and (url is None or is_https_url(url))
    )


def _welcome(m: Mapping[str, Any]) -> Optional[str]:
    dct, protocol, account = m.get("dct"), m.get("protocol"), m.get("account")
    return _check(
        dct is not None
        and is_semver(dct.get("version"))
        and protocol is not None
        and _in_range(protocol.get("major"), 1, MAX_PROTOCOL_MAJOR)
        and _in_range(protocol.get("minor"), 0, MAX_PROTOCOL_MAJOR)
        and account is not None
        and is_text(account.get("userName"))
        and _feature_states_ok(m.get("features"))
    )


# ---- custom peds ----


def _bounded(value: Any, limit: float) -> bool:
    return type(value) in (int, float) and math.isfinite(value) and abs(value) <= limit


def _marker_names_ok(markers: Any) -> bool:
    """Known marker names, at most ``MAX_PED_MARKERS``."""
    return markers is not None and len(markers) <= MAX_PED_MARKERS and all(_one_of(name, PED_MARKERS) for name in markers)


def ped_markers_problem(markers: Any) -> Optional[str]:
    """Why ``markers`` (name to ``[x, y, z]``) break the rules of ``ped.rig``, as an English sentence, or ``None``:
    known names (:data:`PED_MARKERS`), at most :data:`MAX_PED_MARKERS`, each three finite numbers within 3 m."""
    if not isinstance(markers, Mapping) or len(markers) > MAX_PED_MARKERS:
        return f"markers maps up to {MAX_PED_MARKERS} marker names to points"
    for name, point in markers.items():
        if name not in PED_MARKERS:
            return f"{name!r} is not a marker name"
        if not isinstance(point, (list, tuple)) or len(point) != 3 or not all(_bounded(c, 3) for c in point):
            return f"the marker {name} is not three finite numbers within 3 m of the ped's origin"
    return None


def _bone_names_ok(bones: Any) -> bool:
    if bones is None or not 1 <= len(bones) <= MAX_PED_BONES:
        return False
    return all(is_bone_name(bone) for bone in bones) and len(set(bones)) == len(bones)


def _ped_template_ok(entry: Any) -> bool:
    return (
        entry is not None
        and is_ped_model(entry.get("model"))
        and (entry.get("gender") is None or _one_of(entry.get("gender"), GENDERS))
        and is_ped_type(entry.get("pedType"))
        and _one_of(entry.get("layout"), PED_LAYOUTS)
        and _one_of(entry.get("group"), PED_TEMPLATE_GROUPS)
        and entry.get("recommended") is not None
    )


def _ped_templates_list(m: Mapping[str, Any]) -> Optional[str]:
    templates = m.get("templates")
    if not is_id(m.get("re")) or m.get("truncated") is None or templates is None or len(templates) > MAX_PED_TEMPLATES:
        return INVALID_MESSAGE
    models = set()
    for entry in templates:
        if not _ped_template_ok(entry) or entry["model"].lower() in models:
            return INVALID_MESSAGE
        models.add(entry["model"].lower())
    return None


def _ped_skeleton_data(m: Mapping[str, Any]) -> Optional[str]:
    bones = m.get("bones")
    if (
        not is_id(m.get("re"))
        or not is_ped_model(m.get("model"))
        or (m.get("gender") is not None and not _one_of(m.get("gender"), GENDERS))
        or not _one_of(m.get("layout"), PED_LAYOUTS)
        or not _one_of(m.get("ragdoll"), PED_RAGDOLLS)
        or not _bone_names_ok(bones)
        or m.get("payloadLength") is None
    ):
        return INVALID_MESSAGE
    return None if m.get("payloadLength") == PED_BONE_RECORD_BYTES * len(bones) else FRAME_SIZE_MISMATCH


def _ped_rig_options_ok(options: Any) -> bool:
    if options is None:
        return True
    return (
        (options.get("fingers") is None or _one_of(options.get("fingers"), PED_DETAIL_MODES))
        and (options.get("face") is None or _one_of(options.get("face"), PED_DETAIL_MODES))
        and (options.get("restModel") is None or _one_of(options.get("restModel"), PED_REST_MODELS))
    )


def ped_rig_payload_length(vertices: int, triangles: int, has_parts: bool) -> int:
    """The payload a ``ped.rig`` header describes: positions, triangles and one part id per vertex with parts."""
    return 12 * vertices + 12 * triangles + (vertices if has_parts else 0)


def _ped_rig(m: Mapping[str, Any]) -> Optional[str]:
    markers, mesh = m.get("markers"), m.get("mesh")
    if (
        not is_id(m.get("id"))
        or not is_ped_model(m.get("template"))
        or m.get("rights") is not True
        or not markers
        or ped_markers_problem(markers) is not None
        or not _ped_rig_options_ok(m.get("options"))
        or mesh is None
    ):
        return INVALID_MESSAGE
    vertices, triangles, parts = mesh.get("vertices"), mesh.get("triangles"), mesh.get("parts")
    if (
        not _in_range(vertices, 0, 16777216)
        or not _in_range(triangles, 0, 16777216)
        or parts is None
        or len(parts) > MAX_PED_RIG_PARTS
        or not all(_one_of(role, PED_PART_ROLES) for role in parts)
        or m.get("payloadLength") is None
    ):
        return INVALID_MESSAGE
    expected = ped_rig_payload_length(vertices, triangles, len(parts) > 0)
    return None if m.get("payloadLength") == expected else FRAME_SIZE_MISMATCH


def _proportions_ok(value: Any) -> bool:
    if value is None:
        return True
    return all(
        type(value.get(key)) in (int, float) and math.isfinite(value.get(key)) and 0 <= value.get(key) <= 10
        for key in ("height", "shoulders", "hips", "arm", "leg", "torso")
    )


def _ped_rig_report_ok(report: Any) -> bool:
    if report is None:
        return False
    confidence, warnings, moves = report.get("confidence"), report.get("warnings"), report.get("markerMoves")
    if (
        not _one_of(report.get("outcome"), PED_RIG_OUTCOMES)
        or type(confidence) not in (int, float)
        or not math.isfinite(confidence)
        or not 0 <= confidence <= 1
        or warnings is None
        or len(warnings) > MAX_PED_RIG_WARNINGS
        or (report.get("markers") is not None and ped_markers_problem(report.get("markers")) is not None)
        or not _proportions_ok(report.get("character"))
        or not _proportions_ok(report.get("template"))
        or (report.get("suggestedTemplate") is not None and not is_ped_model(report.get("suggestedTemplate")))
    ):
        return False
    for warning in warnings:
        if (
            warning is None
            or not _one_of(warning.get("code"), PED_RIG_WARNINGS)
            or (warning.get("count") is not None and not _in_range(warning.get("count"), 0, 16777216))
            or (warning.get("value") is not None and not _bounded(warning.get("value"), 1000000))
            or (warning.get("markers") is not None and not _marker_names_ok(warning.get("markers")))
            or (warning.get("template") is not None and not is_ped_model(warning.get("template")))
        ):
            return False
    if moves is not None:
        if len(moves) > MAX_PED_MARKERS:
            return False
        for name, move in moves.items():
            if name not in PED_MARKERS or type(move) not in (int, float) or not math.isfinite(move) or not 0 <= move <= 10000:
                return False
    return True


def _ped_rig_result(m: Mapping[str, Any]) -> Optional[str]:
    ok, job = m.get("ok"), m.get("job")
    if not is_id(m.get("re")) or ok is None or m.get("payloadLength") is None or (job is not None and not is_id(job)):
        return INVALID_MESSAGE
    if ok:
        bones, vertices = m.get("bones"), m.get("vertices")
        if (
            m.get("code") is not None
            or m.get("reasons") is not None
            or job is None
            or not is_ped_model(m.get("template"))
            or not _one_of(m.get("ragdoll"), PED_RAGDOLLS)
            or not _bone_names_ok(bones)
            or not _in_range(vertices, 3, MAX_PED_RIG_VERTICES)
            or not _ped_rig_report_ok(m.get("report"))
        ):
            return INVALID_MESSAGE
        expected = PED_RIG_BONE_BYTES * len(bones) + PED_RIG_VERTEX_BYTES * vertices
        return None if m.get("payloadLength") == expected else FRAME_SIZE_MISMATCH
    if not _one_of(m.get("code"), _ERROR_CODE_SET) or any(
        m.get(key) is not None for key in ("template", "ragdoll", "bones", "vertices", "report")
    ):
        return INVALID_MESSAGE
    reasons = m.get("reasons")
    if reasons is not None:
        if len(reasons) > MAX_PED_RIG_REASONS:
            return INVALID_MESSAGE
        for reason in reasons:
            if (
                reason is None
                or not _one_of(reason.get("code"), PED_RIG_REFUSALS)
                or (reason.get("markers") is not None and not _marker_names_ok(reason.get("markers")))
                or (reason.get("message") is not None and not is_diagnostic(reason.get("message")))
            ):
                return INVALID_MESSAGE
    return None if m.get("payloadLength") == 0 else FRAME_SIZE_MISMATCH


def ped_add_problem(m: Mapping[str, Any]) -> Optional[str]:
    """Why the fields of a ``ped.add`` break the rules, as an English sentence, or ``None``."""
    if not is_ped_model(m.get("template")):
        return "template is a ped model name"
    if not is_text(m.get("name")):
        return "the name is 1 to 128 characters of display text"
    if not is_new_ped_model(m.get("model")):
        return "the model name is a lowercase letter, then 2 to 31 lowercase letters, digits or underscores"
    if m.get("rights") is not True:
        return "the user did not confirm the rights notice for this character"
    if m.get("rig") is not None and not is_id(m.get("rig")):
        return "rig names the job of a ped.rig.result"
    ragdoll = m.get("ragdoll")
    if ragdoll is not None and (not _one_of(ragdoll, PED_RAGDOLLS) or ragdoll == "alien"):
        return "ragdoll is fred, wilma, fred-large or wilma-large"
    glb_length, chunks = m.get("glbLength"), m.get("chunks")
    if not _in_range(glb_length, 20, MAX_PED_ADD_BYTES):
        return f"a GLB is 20 bytes to {MAX_PED_ADD_BYTES // (1024 * 1024)} MiB"
    if not _in_range(chunks, 1, MAX_PED_ADD_CHUNKS) or chunks < -(-glb_length // MAX_PED_ADD_CHUNK_BYTES):
        return f"a GLB travels in 1 to {MAX_PED_ADD_CHUNKS} chunks of at most {MAX_PED_ADD_CHUNK_BYTES // (1024 * 1024)} MiB"
    if not is_sha256_hex(m.get("sha256")):
        return "sha256 is 64 lowercase hex digits"
    parts = m.get("parts")
    if parts is not None:
        if len(parts) > MAX_PED_ADD_PARTS:
            return f"at most {MAX_PED_ADD_PARTS} parts"
        meshes = set()
        for part in parts:
            if part is None or not is_text(part.get("mesh")) or not _one_of(part.get("role"), PED_PART_ROLES):
                return "each part names a mesh and a part role"
            if part["mesh"] in meshes:
                return f"two parts name the mesh {part['mesh']}"
            meshes.add(part["mesh"])
    return None


def _ped_add_result(m: Mapping[str, Any]) -> Optional[str]:
    ok, project = m.get("ok"), m.get("project")
    if ok is None or not is_id(m.get("re")):
        return INVALID_MESSAGE
    if ok:
        paired = (
            m.get("code") is None
            and project is not None
            and is_text(project.get("name"))
            and is_new_ped_model(project.get("model"))
            and is_ped_model(project.get("template"))
        )
    else:
        paired = _one_of(m.get("code"), _ERROR_CODE_SET) and project is None
    return _check(paired and _findings_ok(m.get("findings")))


class MessageDef(NamedTuple):
    type: str
    direction: str
    frame: str
    kinds: Dict[str, Kind]
    validate: Validator


def _text(direction: str, kinds: Dict[str, Kind], validate: Validator) -> Tuple[str, str, Dict[str, Kind], Validator]:
    return (direction, TEXT, dict(_ENVELOPE, **kinds), validate)


def _binary(direction: str, kinds: Dict[str, Kind], validate: Validator) -> Tuple[str, str, Dict[str, Kind], Validator]:
    return (direction, BINARY, dict(_BINARY_ENVELOPE, **kinds), validate)


_DEFS: Dict[str, Tuple[str, str, Dict[str, Kind], Validator]] = {
    # Plugin to DCT
    "hello": _text(
        TO_DCT,
        {
            "protocol": _obj({"min": _INT32, "max": _INT32, "minor": _INT32}),
            "plugin": _obj({"kind": _STR, "version": _STR, "channel": _STR}),
            "host": _obj({"name": _STR, "version": _STR}),
            "installId": _STR,
            "clientNonce": _STR,
        },
        _hello,
    ),
    "auth": _text(TO_DCT, {"assertion": _STR}, lambda m: _check(is_access_token(m.get("assertion")))),
    "account.assist": _text(TO_DCT, {"userCode": _STR}, lambda m: _check(is_user_code(m.get("userCode")))),
    "context.get": _text(TO_DCT, {}, lambda m: None),
    "live.open": _text(
        TO_DCT,
        {"target": _STR, "binding": _BINDING, "width": _INT32, "height": _INT32, "document": _STR},
        lambda m: _check(
            _one_of(m.get("target"), LIVE_TARGETS)
            and _optional_binding_ok(m.get("binding"))
            and _in_range(m.get("width"), 1, MAX_TEXTURE_EDGE)
            and _in_range(m.get("height"), 1, MAX_TEXTURE_EDGE)
            and (m.get("document") is None or is_text(m.get("document")))
        ),
    ),
    "live.frame": _binary(TO_DCT, {"lease": _STR, "revision": _INT64, "rect": _RECT, "format": _STR}, _live_frame),
    "live.save": _text(
        TO_DCT,
        {"lease": _STR, "revision": _INT64, "mode": _STR},
        lambda m: _check(
            is_id(m.get("lease")) and _in_range(m.get("revision"), 0, MAX_REVISION) and _one_of(m.get("mode"), SAVE_MODES)
        ),
    ),
    "live.discard": _text(TO_DCT, {"lease": _STR}, lambda m: _check(is_id(m.get("lease")))),
    "live.close": _text(TO_DCT, {"lease": _STR}, lambda m: _check(is_id(m.get("lease")))),
    "texture.read": _text(
        TO_DCT,
        {"target": _STR, "binding": _BINDING},
        lambda m: _check(_one_of(m.get("target"), LIVE_TARGETS) and _optional_binding_ok(m.get("binding"))),
    ),
    "texture.validate": _text(
        TO_DCT,
        {"target": _STR, "binding": _BINDING, "width": _INT32, "height": _INT32},
        lambda m: _check(
            _one_of(m.get("target"), LIVE_TARGETS)
            and _optional_binding_ok(m.get("binding"))
            and _in_range(m.get("width"), 1, MAX_TEXTURE_EDGE)
            and _in_range(m.get("height"), 1, MAX_TEXTURE_EDGE)
        ),
    ),
    "uv.layout": _text(
        TO_DCT,
        {"binding": _BINDING, "size": _INT32},
        lambda m: _check(
            _optional_binding_ok(m.get("binding")) and _in_range(m.get("size"), MIN_UV_LAYOUT_SIZE, MAX_TEXTURE_EDGE)
        ),
    ),
    "model.glb": _text(TO_DCT, {"binding": _BINDING}, lambda m: _check(_optional_binding_ok(m.get("binding")))),
    "body.glb": _text(TO_DCT, {"gender": _STR}, lambda m: _check(_one_of(m.get("gender"), GENDERS))),
    "model.push": _binary(
        TO_DCT,
        {"lease": _STR, "binding": _BINDING, "format": _STR, "files": _MODEL_FILES},
        _model_push,
    ),
    "model.save": _text(TO_DCT, {"lease": _STR}, lambda m: _check(is_id(m.get("lease")))),
    "model.discard": _text(TO_DCT, {"lease": _STR}, lambda m: _check(is_id(m.get("lease")))),
    "host.result": _text(
        TO_DCT,
        {"ok": _BOOL, "code": _STR},
        lambda m: _check(is_id(m.get("re")) and _ok_code_ok(m, HOST_RESULT_CODES)),
    ),
    "item.thumbnail": _text(
        TO_DCT,
        {"binding": _BINDING, "size": _INT32},
        lambda m: _check(
            _optional_binding_ok(m.get("binding")) and _in_range(m.get("size"), MIN_THUMBNAIL_EDGE, MAX_THUMBNAIL_EDGE)
        ),
    ),
    "skeleton.template": _text(TO_DCT, {"gender": _STR}, lambda m: _check(_one_of(m.get("gender"), GENDERS))),
    "item.add": _binary(
        TO_DCT,
        {
            "format": _STR,
            "drawableType": _STR,
            "gender": _STR,
            "skin": _BOOL,
            "name": _STR,
            "variations": _list(_obj({"file": _STR, "name": _STR})),
            "files": _MODEL_FILES,
        },
        _item_add,
    ),
    # The cancel names the add it withdraws; it has no reply of its own.
    "item.addCancel": _text(TO_DCT, {}, lambda m: _check(is_id(m.get("re")))),
    "ped.templates": _text(
        TO_DCT,
        {"gender": _STR, "all": _BOOL},
        lambda m: _check(m.get("gender") is None or _one_of(m.get("gender"), GENDERS)),
    ),
    "ped.skeleton": _text(TO_DCT, {"model": _STR}, lambda m: _check(is_ped_model(m.get("model")))),
    "ped.rig": _binary(
        TO_DCT,
        {
            "template": _STR,
            "rights": _BOOL,
            "markers": _PED_MARKERS_KIND,
            "options": _obj(
                {"fingers": _STR, "face": _STR, "rollBones": _BOOL, "helperBones": _BOOL, "refineMarkers": _BOOL, "restModel": _STR}
            ),
            "mesh": _obj({"vertices": _INT32, "triangles": _INT32, "parts": _list(_STR)}),
        },
        _ped_rig,
    ),
    "ped.rig.cancel": _text(TO_DCT, {}, lambda m: _check(is_id(m.get("re")))),
    "ped.add": _text(
        TO_DCT,
        {
            "template": _STR,
            "name": _STR,
            "model": _STR,
            "rights": _BOOL,
            "rig": _STR,
            "ragdoll": _STR,
            "parts": _list(_obj({"mesh": _STR, "role": _STR})),
            "glbLength": _INT64,
            "chunks": _INT32,
            "sha256": _STR,
        },
        lambda m: _check(ped_add_problem(m) is None),
    ),
    "ped.add.chunk": _binary(
        TO_DCT,
        {"index": _INT32},
        lambda m: _check(
            is_id(m.get("re"))
            and _in_range(m.get("index"), 0, MAX_PED_ADD_CHUNKS - 1)
            and _in_range(m.get("payloadLength"), 1, MAX_PED_ADD_CHUNK_BYTES)
        ),
    ),
    "ped.addCancel": _text(TO_DCT, {}, lambda m: _check(is_id(m.get("re")))),
    "bye": _text(TO_DCT, {}, lambda m: None),
    # DCT to plugin
    "challenge": _text(TO_CLIENT, {"serverNonce": _STR}, lambda m: _check(is_bytes32(m.get("serverNonce")))),
    "welcome": _text(
        TO_CLIENT,
        {
            "dct": _obj({"version": _STR}),
            "protocol": _obj({"major": _INT32, "minor": _INT32}),
            "account": _obj({"userName": _STR}),
            "features": _FEATURE_STATES,
        },
        _welcome,
    ),
    "incompatible": _text(
        TO_CLIENT,
        {
            "code": _STR,
            "dct": _obj({"version": _STR, "protocol": _obj({"min": _INT32, "max": _INT32})}),
            "minimumPluginVersion": _STR,
            "updateUrl": _STR,
        },
        _incompatible,
    ),
    "account.assistResult": _text(TO_CLIENT, {"ok": _BOOL, "code": _STR}, lambda m: _check(_ok_code_ok(m))),
    "context.snapshot": _text(
        TO_CLIENT,
        {"project": _PROJECT, "focused": _FOCUSED},
        lambda m: _check(_project_ok(m.get("project")) and _focused_ok(m.get("focused"))),
    ),
    "event.selection": _text(TO_CLIENT, {"focused": _FOCUSED}, lambda m: _check(_focused_ok(m.get("focused")))),
    "event.project": _text(TO_CLIENT, {"project": _PROJECT}, lambda m: _check(_project_ok(m.get("project")))),
    "event.entitlement": _text(
        TO_CLIENT, {"features": _FEATURE_STATES}, lambda m: _check(_feature_states_ok(m.get("features")))
    ),
    "live.opened": _text(
        TO_CLIENT,
        {"lease": _STR, "binding": _BINDING, "target": _STR, "width": _INT32, "height": _INT32},
        lambda m: _check(
            is_id(m.get("lease"))
            and _binding_ok(m.get("binding"))
            and _one_of(m.get("target"), LIVE_TARGETS)
            and _in_range(m.get("width"), 1, MAX_TEXTURE_EDGE)
            and _in_range(m.get("height"), 1, MAX_TEXTURE_EDGE)
        ),
    ),
    "live.status": _text(
        TO_CLIENT,
        {"lease": _STR, "appliedRevision": _INT64, "state": _STR},
        lambda m: _check(
            is_id(m.get("lease"))
            and _in_range(m.get("appliedRevision"), 0, MAX_REVISION)
            and _one_of(m.get("state"), LIVE_STATES)
        ),
    ),
    "live.saveResult": _text(
        TO_CLIENT,
        {"lease": _STR, "ok": _BOOL, "code": _STR, "textureId": _STR},
        lambda m: _check(
            is_id(m.get("lease"))
            and _ok_code_ok(m)
            and (m.get("textureId") is None or is_guid(m.get("textureId")))
        ),
    ),
    "live.closed": _text(
        TO_CLIENT,
        {"lease": _STR, "reason": _STR},
        lambda m: _check(is_id(m.get("lease")) and _one_of(m.get("reason"), LIVE_CLOSE_REASONS)),
    ),
    "texture.findings": _text(
        TO_CLIENT,
        {"binding": _BINDING, "target": _STR, "findings": _FINDINGS},
        lambda m: _check(
            _binding_ok(m.get("binding")) and _one_of(m.get("target"), LIVE_TARGETS) and _findings_ok(m.get("findings"))
        ),
    ),
    "texture.data": _binary(
        TO_CLIENT,
        {"binding": _BINDING, "target": _STR, "name": _STR, "width": _INT32, "height": _INT32, "format": _STR},
        _textured_image,
    ),
    "uv.layout.image": _binary(
        TO_CLIENT,
        {"binding": _BINDING, "width": _INT32, "height": _INT32, "format": _STR},
        lambda m: _image_code(m) if _binding_ok(m.get("binding")) else INVALID_MESSAGE,
    ),
    "model.glb.data": _binary(
        TO_CLIENT, {"binding": _BINDING, "swapMaterials": _list(_INT32_REQUIRED)}, _model_glb_data
    ),
    "body.glb.data": _binary(
        TO_CLIENT,
        {"gender": _STR},
        lambda m: _check(_one_of(m.get("gender"), GENDERS) and _payload_in(m, 1)),
    ),
    "model.applied": _text(
        TO_CLIENT,
        {"lease": _STR, "revision": _INT64, "binding": _BINDING, "findings": _FINDINGS},
        lambda m: _check(
            is_id(m.get("lease"))
            and _in_range(m.get("revision"), 1, MAX_REVISION)
            and _binding_ok(m.get("binding"))
            and _findings_ok(m.get("findings"))
        ),
    ),
    "model.saveResult": _text(
        TO_CLIENT,
        {"lease": _STR, "ok": _BOOL, "code": _STR},
        lambda m: _check(is_id(m.get("lease")) and _ok_code_ok(m)),
    ),
    "model.closed": _text(
        TO_CLIENT,
        {"lease": _STR, "reason": _STR},
        lambda m: _check(is_id(m.get("lease")) and _one_of(m.get("reason"), MODEL_CLOSE_REASONS)),
    ),
    "host.openTexture": _binary(
        TO_CLIENT,
        {"binding": _BINDING, "target": _STR, "name": _STR, "width": _INT32, "height": _INT32, "format": _STR},
        # Always with an id: the plugin's host.result names it.
        lambda m: _textured_image(m) if is_id(m.get("id")) else INVALID_MESSAGE,
    ),
    "host.openModel": _binary(
        TO_CLIENT,
        {"binding": _BINDING, "name": _STR, "format": _STR, "files": _MODEL_FILES},
        _host_open_model,
    ),
    "item.thumbnail.data": _binary(
        TO_CLIENT,
        {"binding": _BINDING, "width": _INT32, "height": _INT32, "format": _STR},
        _thumbnail_image,
    ),
    "skeleton.template.data": _binary(
        TO_CLIENT, {"gender": _STR, "format": _STR, "files": _MODEL_FILES}, _skeleton_template_data
    ),
    "item.addResult": _text(
        TO_CLIENT,
        {"ok": _BOOL, "code": _STR, "binding": _BINDING, "findings": _FINDINGS},
        _item_add_result,
    ),
    "ped.templates.list": _text(
        TO_CLIENT,
        {
            "templates": _list(
                _obj({"model": _STR, "gender": _STR, "pedType": _STR, "layout": _STR, "group": _STR, "recommended": _BOOL})
            ),
            "truncated": _BOOL,
        },
        _ped_templates_list,
    ),
    "ped.skeleton.data": _binary(
        TO_CLIENT,
        {"model": _STR, "gender": _STR, "layout": _STR, "ragdoll": _STR, "bones": _list(_STR)},
        _ped_skeleton_data,
    ),
    "ped.rig.accepted": _text(TO_CLIENT, {"job": _STR}, lambda m: _check(is_id(m.get("re")) and is_id(m.get("job")))),
    "ped.rig.progress": _text(
        TO_CLIENT,
        {"job": _STR, "stage": _STR, "fraction": _NUMBER},
        lambda m: _check(
            is_id(m.get("job"))
            and _one_of(m.get("stage"), PED_RIG_STAGES)
            and m.get("fraction") is not None
            and 0 <= m.get("fraction") <= 1
        ),
    ),
    "ped.rig.result": _binary(
        TO_CLIENT,
        {
            "ok": _BOOL,
            "code": _STR,
            "reasons": _list(_obj({"code": _STR, "markers": _list(_STR), "message": _STR})),
            "job": _STR,
            "template": _STR,
            "ragdoll": _STR,
            "bones": _list(_STR),
            "vertices": _INT32,
            "report": _PED_REPORT,
        },
        _ped_rig_result,
    ),
    "ped.addResult": _text(
        TO_CLIENT,
        {"ok": _BOOL, "code": _STR, "project": _obj({"name": _STR, "model": _STR, "template": _STR}), "findings": _FINDINGS},
        _ped_add_result,
    ),
    "error": _text(
        TO_CLIENT,
        {"code": _STR, "message": _STR},
        lambda m: _check(
            _one_of(m.get("code"), _ERROR_CODE_SET) and (m.get("message") is None or is_diagnostic(m.get("message")))
        ),
    ),
}

#: hello and incompatible: the negotiation, read in any major so peers of different majors can say why.
_NEGOTIATION = frozenset({"hello", "incompatible"})

#: Every Creator Link protocol 2 message by wire type.
MESSAGES: Dict[str, MessageDef] = {name: MessageDef(name, *spec) for name, spec in _DEFS.items()}


def message_direction(message_type: str) -> str:
    return MESSAGES[message_type].direction


def message_frame(message_type: str) -> str:
    return MESSAGES[message_type].frame


# --------------------------------------------------------------------------------------------------
# Decoding
# --------------------------------------------------------------------------------------------------


def _decode_message(json_bytes: bytes, direction: str, frame: str) -> Dict[str, Any]:
    root = _parse_json(json_bytes)
    if not isinstance(root, dict):
        raise ProtocolError(MALFORMED_MESSAGE, "the root is not an object")

    version = root.get("v")
    message_type = root.get("type")
    if not _is_integer(version) or not _INT32_MIN <= version <= _INT32_MAX or not isinstance(message_type, str):
        raise ProtocolError(MALFORMED_MESSAGE, "the envelope is missing or mistyped")
    # Text messages carry an id; binary headers may, and it must then be well formed.
    if (frame == TEXT and "id" not in root) or ("id" in root and not is_id(root["id"])):
        raise ProtocolError(MALFORMED_MESSAGE, "id")
    if "re" in root and not is_id(root["re"]):
        raise ProtocolError(MALFORMED_MESSAGE, "re")

    # hello and incompatible, the negotiation, are read in any major; everything else only in the current one.
    if version != PROTOCOL_MAJOR and not (message_type in _NEGOTIATION and 1 <= version <= MAX_PROTOCOL_MAJOR):
        raise ProtocolError(UNSUPPORTED_PROTOCOL, f"v={version}", version=version)
    definition = MESSAGES.get(message_type)
    if definition is None:
        raise ProtocolError(UNKNOWN_MESSAGE_TYPE, "unknown type")
    if definition.direction != direction or definition.frame != frame:
        raise ProtocolError(UNEXPECTED_MESSAGE, message_type)

    if not _kinds_ok(root, definition.kinds):
        raise ProtocolError(INVALID_MESSAGE, f"{message_type}: a field has the wrong JSON type")
    code = definition.validate(root)
    if code is not None:
        raise ProtocolError(code, message_type)
    return root


def _check_direction(direction: str) -> None:
    if direction not in (TO_DCT, TO_CLIENT):
        raise ValueError(f"direction must be {TO_DCT!r} or {TO_CLIENT!r}")


def decode_text(data: Union[bytes, bytearray, memoryview], direction: str) -> Dict[str, Any]:
    """Decodes one text frame travelling in ``direction`` (``toDct`` or ``toClient``)."""
    _check_direction(direction)
    if len(data) > MAX_CONTROL_MESSAGE_BYTES:
        raise ProtocolError(MESSAGE_TOO_LARGE, "text frame")
    return _decode_message(bytes(data), direction, TEXT)


def decode_binary(frame: Union[bytes, bytearray, memoryview], direction: str) -> BinaryMessage:
    """Decodes one binary frame: a little-endian u32 header length, a JSON header and the raw payload.

    The payload is not copied; :attr:`BinaryMessage.payload` is a view into ``frame``.
    """
    _check_direction(direction)
    view = memoryview(frame)
    if view.format != "B" or view.ndim != 1:
        view = view.cast("B")
    size = view.nbytes
    if size < BINARY_LENGTH_PREFIX_BYTES:
        raise ProtocolError(MALFORMED_MESSAGE, "shorter than the length prefix")
    header_length = int.from_bytes(view[:BINARY_LENGTH_PREFIX_BYTES], "little")
    if header_length > MAX_BINARY_HEADER_BYTES:
        raise ProtocolError(MESSAGE_TOO_LARGE, "binary header")
    if header_length == 0 or header_length > size - BINARY_LENGTH_PREFIX_BYTES:
        raise ProtocolError(MALFORMED_MESSAGE, "header length")
    payload_offset = BINARY_LENGTH_PREFIX_BYTES + header_length
    payload_length = size - payload_offset
    if payload_length > MAX_BINARY_PAYLOAD_BYTES:
        raise ProtocolError(MESSAGE_TOO_LARGE, "binary payload")

    header = _decode_message(bytes(view[BINARY_LENGTH_PREFIX_BYTES:payload_offset]), direction, BINARY)
    # Every binary message declares the payload it carries.
    if header.get("payloadLength") != payload_length:
        raise ProtocolError(FRAME_SIZE_MISMATCH, "payloadLength")
    return BinaryMessage(header, view[payload_offset:])


# --------------------------------------------------------------------------------------------------
# Encoding
# --------------------------------------------------------------------------------------------------


def _without_nulls(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {k: _without_nulls(v) for k, v in value.items() if v is not None}
    if isinstance(value, (list, tuple)):
        return [_without_nulls(v) for v in value]
    return value


def _ordered(message: Mapping[str, Any], frame: str) -> Tuple[str, Dict[str, Any]]:
    message_type = message.get("type")
    definition = MESSAGES.get(message_type) if isinstance(message_type, str) else None
    if definition is None:
        raise ProtocolError(UNKNOWN_MESSAGE_TYPE, f"cannot encode {message_type!r}")
    if definition.frame != frame:
        raise ProtocolError(UNEXPECTED_MESSAGE, f"{message_type} is not a {frame} message")
    # An incompatible answer is written in the major of the hello it answers when the sender names one.
    given = message.get("v")
    keep = message_type == "incompatible" and _is_integer(given) and 1 <= given <= MAX_PROTOCOL_MAJOR
    ordered: Dict[str, Any] = {"v": given if keep else PROTOCOL_MAJOR, "type": message_type}
    for key in ("id", "re"):
        if message.get(key) is not None:
            ordered[key] = message[key]
    for key, value in message.items():
        if key not in ("v", "type", "id", "re") and value is not None:
            ordered[key] = _without_nulls(value)
    return definition.direction, ordered


def _dumps(obj: Mapping[str, Any]) -> bytes:
    try:
        return json.dumps(obj, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError) as exc:
        raise ProtocolError(INVALID_MESSAGE, "not encodable as JSON") from exc


def encode_text(message: Mapping[str, Any]) -> bytes:
    """Encodes a text message (``v`` is set; ``None`` values are left out). Raises :class:`ProtocolError`
    when the result would be refused by a receiver."""
    direction, ordered = _ordered(message, TEXT)
    data = _dumps(ordered)
    if len(data) > MAX_CONTROL_MESSAGE_BYTES:
        raise ProtocolError(MESSAGE_TOO_LARGE, f"{ordered['type']} exceeds the control frame limit")
    _decode_message(data, direction, TEXT)
    return data


def encode_binary_header(header: Mapping[str, Any], payload_length: int) -> bytes:
    """Validates a binary header for a payload of ``payload_length`` bytes and returns the u32 length prefix
    plus the header JSON. The payload follows it on the wire; it may be written in several pieces."""
    if not _is_integer(payload_length) or not 0 <= payload_length <= MAX_BINARY_PAYLOAD_BYTES:
        raise ProtocolError(MESSAGE_TOO_LARGE, "binary payload")
    fields = dict(header)
    fields["payloadLength"] = payload_length
    direction, ordered = _ordered(fields, BINARY)
    data = _dumps(ordered)
    if len(data) > MAX_BINARY_HEADER_BYTES:
        raise ProtocolError(MESSAGE_TOO_LARGE, f"{ordered['type']} exceeds the binary header limit")
    _decode_message(data, direction, BINARY)
    return len(data).to_bytes(BINARY_LENGTH_PREFIX_BYTES, "little") + data


def encode_binary_parts(
    header: Mapping[str, Any], payload: Union[bytes, bytearray, memoryview]
) -> Tuple[bytes, memoryview]:
    """Validates and encodes a binary header for ``payload``. Returns the length prefix plus header bytes and
    the payload view, so a sender can write both without first joining them."""
    view = memoryview(payload)
    if view.format != "B" or view.ndim != 1:
        view = view.cast("B")
    return encode_binary_header(header, view.nbytes), view


def encode_binary(header: Mapping[str, Any], payload: Union[bytes, bytearray, memoryview]) -> bytes:
    """Encodes a binary frame. ``payloadLength`` is set from ``payload``."""
    prefix, view = encode_binary_parts(header, payload)
    return prefix + view.tobytes()
