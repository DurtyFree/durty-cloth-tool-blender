# SPDX-License-Identifier: MIT
# Copyright (c) Schmid Software Solutions (https://schmid-software.de)
"""Garment fitting on gta.clothing for Creator Link plugins (the "Garment fitting" routes of the link API).

The Blender add-on uploads a garment (its triangles in ped space, the DCTM mesh format) and gets it back in the
freemode rest pose with the stock body's skin weights. This module is the client side of that contract:

* :func:`fit_request` builds the ``request`` part and checks it with the service's rules before anything is sent;
  :func:`encode_mesh` checks the arrays and frames them as DCTM version 1 without copying them.
* :class:`FitClient` calls the four routes (``fit/jobs``, ``fit/status``, ``fit/cancel``, ``fit/reference``) and
  ``/me`` for the daily allowance, with the signed-in account's access token. The mesh is streamed in chunks from
  the caller's buffers; every answer is bounded in size; every request has an idle timeout. A ``401`` renews the
  access token once. Requests that change nothing on the server (status, cancel, reference, allowance) are tried
  again after a network failure; an upload only when it cannot have reached the service (the connection failed
  before the whole mesh was sent), because a lost answer to a finished upload may hide a job that already counts.
* :func:`parse_status` and :func:`parse_result` read the answers of ``fit/status`` (the job's state, or the binary
  ``application/vnd.dct.fit-result``) with every count and offset checked before it is used.

Every failure is a :class:`FitError` whose ``code`` is the service's ``failureCode`` (``quota_exceeded``,
``fit_busy``, ``mesh_invalid`` with its ``errors`` and so on) or one of the local codes ``network``,
``invalid-response``, ``signed-out``, ``cancelled`` and ``plugin_update_required``. The plain methods block the
calling thread; ``begin_*`` runs the same call on a daemon worker thread and returns a :class:`FitTask` that a host
timer polls without blocking. The worker only talks to gta.clothing and the secret store (for the token), never to
host APIs.

Tokens, meshes and results are never logged. Standard library only.
"""

from __future__ import annotations

import array
import http.client
import json
import math
import re
import secrets
import socket
import ssl
import sys
import threading
import time
import urllib.parse
import urllib.request
from typing import Any, Callable, Dict, Iterable, List, NamedTuple, Optional, Sequence, Tuple, Union

from . import auth

__all__ = [
    "RESULT_TYPE",
    "MARKERS",
    "CHAINS",
    "FITTABLE_TYPES",
    "SOURCE_POSES",
    "OPTIONS",
    "STAGES",
    "OUTCOMES",
    "FAILURE_CODES",
    "INPUT_CODES",
    "WARNING_CODES",
    "LOCAL_CODES",
    "FitError",
    "FitIssue",
    "MeshUpload",
    "FitSubmitted",
    "FitStatus",
    "FitResult",
    "FitRange",
    "FitReference",
    "FitAllowance",
    "FitTask",
    "FitClient",
    "fit_request",
    "encode_mesh",
    "parse_status",
    "parse_result",
    "parse_reference",
    "parse_allowance",
]

#: The media type of a finished job's answer.
RESULT_TYPE = "application/vnd.dct.fit-result"
#: The ``request`` part's limit, and the mesh part's.
MAX_REQUEST_BYTES = 16 * 1024
MAX_MESH_BYTES = 16 * 1024 * 1024
#: A result holds 20 bytes per vertex and a JSON header; 32 MiB leaves room above the 120,000 vertices allowed.
MAX_RESULT_BYTES = 32 * 1024 * 1024
MAX_RESULT_HEADER_BYTES = 1024 * 1024
#: Every JSON answer (states, reference, ``/me``, failures).
MAX_JSON_BYTES = 256 * 1024
MAX_VERTICES = 120_000
MAX_TRIANGLES = 240_000
#: Every coordinate (and every marker coordinate) lies within this many metres of the ped's origin.
MAX_COORDINATE = 3.0
MAX_MARKERS = 32
#: Vertex flag bits of the DCTM mesh.
FLAG_PINNED = 1
FLAG_LINING = 2

#: The marker names: joint positions on the garment in its source pose (ped space metres, X to the ped's left).
MARKERS = ("pelvis", "chest", "neck", "lShoulder", "lElbow", "lWrist", "rShoulder", "rElbow", "rWrist",
           "lHip", "lKnee", "lAnkle", "rHip", "rKnee", "rAnkle")
#: The limb chains: each comes complete or not at all.
CHAINS = (("lShoulder", "lElbow", "lWrist"), ("rShoulder", "rElbow", "rWrist"),
          ("lHip", "lKnee", "lAnkle"), ("rHip", "rKnee", "rAnkle"))
#: The drawable types the service fits (clothing worn on the body), and those that need both arm chains when posed.
FITTABLE_TYPES = ("berd", "uppr", "lowr", "hand", "feet", "teef", "accs", "task", "jbib")
SLEEVED_TYPES = ("jbib", "accs", "uppr")
SOURCE_POSES = ("rest", "a-pose", "t-pose", "custom")
OPERATIONS = ("fit", "weights")
GENDERS = ("male", "female")
#: The options and their ranges (``None``: a boolean). A seam weld is 0 (off) or 0.05 to 3 mm.
OPTIONS: Dict[str, Optional[Tuple[float, float]]] = {
    "seamWeldMm": (0.0, 3.0), "clearanceMm": (0.0, 20.0), "maxPushMm": (1.0, 100.0), "pushOut": None,
    "matchProportions": None,
}
MIN_SEAM_WELD_MM = 0.05
#: With the seam weld on, at most this many open-edge vertices may lie in one cube as wide as the weld
#: (``seam_too_dense`` otherwise).
MAX_SEAM_DENSITY = 128
STAGES = ("validating", "welding", "posing", "transferring", "unposing", "pushingOut", "weighting")
OUTCOMES = ("fitted", "needsReview", "notOnBody")
STATES = ("queued", "running", "failed", "cancelled")

#: The ``failureCode`` values a fitting route or a failed job can answer.
FAILURE_CODES = (
    "invalid_request", "session_invalid", "session_expired", "session_revoked", "feature_not_entitled",
    "feature_unavailable", "not_found", "body_version_mismatch", "mesh_too_large", "unsupported_format",
    "mesh_invalid", "plugin_update_required", "quota_exceeded", "fit_busy", "rate_limited", "server_error",
    "fit_unavailable", "fit_timeout", "account_locked",
)
#: The codes of ``errors[]`` (each with a ``field``): the request's, the mesh reader's and the fitting's.
INPUT_CODES = (
    "request_invalid", "request_part_missing", "mesh_part_missing", "part_unexpected", "operation_invalid",
    "gender_invalid", "drawable_type_invalid", "slot_unsupported", "category_invalid", "source_pose_invalid",
    "source_pose_not_rest", "body_version_invalid", "options_out_of_range", "job_id_invalid",
    "mesh_format_invalid", "mesh_version_unsupported", "mesh_header_invalid", "mesh_truncated",
    "mesh_trailing_data", "mesh_too_large", "positions_invalid", "triangles_invalid", "too_many_vertices",
    "too_many_triangles", "coordinate_not_finite", "coordinate_out_of_range", "triangle_index_out_of_range",
    "triangle_degenerate", "triangle_duplicate", "seam_too_dense", "flags_invalid", "too_many_markers",
    "marker_unknown", "marker_invalid", "marker_out_of_range", "marker_far", "marker_missing", "marker_side",
    "marker_inconsistent", "body_gender_mismatch", "upload_timeout",
)
#: The stable codes of a result's warnings.
WARNING_CODES = ("inside_body", "low_coverage", "marker_offset", "proportion_clamped", "shape_strained",
                 "attachment_fallback", "unweighted")
#: The codes this module gives a failure that has no answer of the service.
LOCAL_CODES = ("network", "invalid-response", "signed-out", "cancelled")

_CODE = re.compile(r"[a-z][a-z_]{0,63}")
_FIELD = re.compile(r"[A-Za-z][A-Za-z0-9_.]{0,63}")
_JOB_ID = re.compile(r"[A-Za-z0-9_-]{22}")
_CATEGORY = re.compile(r"[a-z0-9_-]{1,32}")
_BODY_VERSION = re.compile(r"[A-Za-z0-9._-]{1,32}")
_REGION = re.compile(r"[A-Za-z][A-Za-z0-9_]{0,31}")
_BONE = re.compile(r"[A-Za-z][A-Za-z0-9_]{0,63}")
#: Network failures of a request that changes nothing are tried this many more times, after these pauses.
_RETRY_PAUSES = (0.5, 1.5)


class FitError(Exception):
    """A fitting call failed. ``code`` is the service's ``failureCode`` or a local code (:data:`LOCAL_CODES`);
    ``retry_after`` the seconds the service asked to wait (``quota_exceeded``, ``fit_busy``, ``rate_limited``);
    ``errors`` what the service found wrong (:class:`FitIssue`, codes from :data:`INPUT_CODES`); ``body_version``
    the service's body version (``body_version_mismatch``); ``uploaded`` whether a whole upload went out, so that a
    job may exist although its answer was lost."""

    def __init__(self, code: str, message: str = "", *, status: int = 0, retryable: bool = False,
                 retry_after: Optional[float] = None, errors: Sequence["FitIssue"] = (),
                 body_version: Optional[str] = None, uploaded: bool = False,
                 min_version: Optional[str] = None) -> None:
        super().__init__(f"{code}: {message}" if message else code)
        self.code = code
        self.message = message
        self.status = status
        self.retryable = retryable
        self.retry_after = retry_after
        self.errors = tuple(errors)
        self.body_version = body_version
        self.uploaded = uploaded
        self.min_version = min_version


class FitIssue(NamedTuple):
    """One problem the service found: a stable ``code`` and the ``field`` it concerns (``mesh``, ``markers``,
    ``options.clearanceMm`` and so on)."""

    code: str
    field: str


class FitSubmitted(NamedTuple):
    job_id: str
    state: str
    #: Fits left today after this one (``None`` when the answer did not say).
    remaining_today: Optional[int]


class FitStatus(NamedTuple):
    """A job that has not finished (``queued``, ``running``) or ended without a result (``failed``,
    ``cancelled``)."""

    job_id: str
    state: str
    #: The stage a running job is in (:data:`STAGES`), ``None`` otherwise or for a stage this client does not know.
    stage: Optional[str]
    progress: float
    queue_position: Optional[int]
    failure_code: Optional[str]
    retryable: bool
    #: Whether a failed or cancelled job's use of the daily allowance came back (``None`` when not said).
    refunded: Optional[bool]
    errors: Tuple[FitIssue, ...]

    @property
    def finished(self) -> bool:
        return self.state in ("failed", "cancelled")


class FitResult(NamedTuple):
    """A finished job. ``positions`` (``f32`` x3), ``bones`` (``u8`` x4, freemode skeleton indices, strongest first)
    and ``weights`` (``u8`` x4, 255 per vertex) are little-endian bytes, ``None`` for a ``notOnBody`` result.
    ``bone_names`` maps each bone index the weights use to its freemode name."""

    job_id: str
    operation: str
    outcome: str
    vertex_count: int
    triangle_count: int
    positions: Optional[bytes]
    bones: Optional[bytes]
    weights: Optional[bytes]
    bone_names: Dict[int, str]
    warnings: Tuple[str, ...]
    #: The report's numbers (confidence, insideBodyBefore, insideBodyAfter, pushedVertices, unweightedVertices,
    #: maximumMarkerOffsetMm, matchedAreaShare), each a finite number.
    report: Dict[str, float]

    @property
    def finished(self) -> bool:
        return True

    @property
    def state(self) -> str:
        return "succeeded"


class FitRange(NamedTuple):
    """How far ordinary game clothing of a category sits from one body region (millimetres, positive outside)."""

    p10: float
    p50: float
    p90: float
    samples: int


class FitReference(NamedTuple):
    body_version: str
    gender: str
    category: str
    regions: Dict[str, FitRange]


class FitAllowance(NamedTuple):
    """The account's daily fitting allowance (``limits.pools.fit`` of ``/me``)."""

    per_day: int
    used_today: int
    remaining_today: int


# ---- the request and the mesh ---------------------------------------------------------------------------------


def _number(value: Any) -> bool:
    return type(value) in (int, float) and math.isfinite(value)


def fit_request(operation: str, gender: str, drawable_type: str, body_version: str, *, source_pose: str = "rest",
                category: Optional[str] = None, markers: Optional[Dict[str, Sequence[float]]] = None,
                options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """The ``request`` part of an upload, checked with the service's rules (raises ``ValueError`` naming the rule).

    ``markers`` maps :data:`MARKERS` names to ped space points; a limb chain (:data:`CHAINS`) comes complete or not
    at all, a pose other than ``rest`` needs a chain, and a top, undershirt or body piece posed that way needs both
    arm chains. ``weights`` takes a garment in the rest pose only."""
    if operation not in OPERATIONS:
        raise ValueError("operation is fit or weights")
    if gender not in GENDERS:
        raise ValueError("gender is male or female")
    if drawable_type not in FITTABLE_TYPES:
        raise ValueError("only clothing worn on the body can be fitted (" + ", ".join(FITTABLE_TYPES) + ")")
    if source_pose not in SOURCE_POSES:
        raise ValueError("sourcePose is rest, a-pose, t-pose or custom")
    if operation == "weights" and source_pose != "rest":
        raise ValueError("weights needs a garment in the rest pose")
    if not isinstance(body_version, str) or not _BODY_VERSION.fullmatch(body_version):
        raise ValueError("bodyVersion is 1 to 32 letters, digits, '.', '_' or '-'")
    if category is not None and (not isinstance(category, str) or not _CATEGORY.fullmatch(category)):
        raise ValueError("category is 1 to 32 lower-case letters, digits, '_' or '-'")
    points: Dict[str, List[float]] = {}
    for name, point in (markers or {}).items():
        if name not in MARKERS:
            raise ValueError(f"{name!r} is not a marker name")
        values = list(point) if isinstance(point, (list, tuple)) else None
        if values is None or len(values) != 3 or not all(_number(v) and abs(v) <= MAX_COORDINATE for v in values):
            raise ValueError(f"the {name} marker is not a finite point within {MAX_COORDINATE:g} m of the origin")
        points[name] = [round(float(v), 6) for v in values]
    if len(points) > MAX_MARKERS:
        raise ValueError(f"at most {MAX_MARKERS} markers")
    complete = 0
    arms = 0
    for index, chain in enumerate(CHAINS):
        present = sum(1 for name in chain if name in points)
        if 0 < present < len(chain):
            raise ValueError(f"the chain {'/'.join(chain)} is incomplete")
        if present:
            complete += 1
            arms += 1 if index < 2 else 0
    if source_pose != "rest" and (complete == 0 or (drawable_type in SLEEVED_TYPES and arms < 2)):
        raise ValueError("a posed garment needs its limb chains (a top both arms)")
    chosen: Dict[str, Any] = {}
    for name, value in (options or {}).items():
        if name not in OPTIONS:
            raise ValueError(f"{name!r} is not a fitting option")
        bounds = OPTIONS[name]
        if bounds is None:
            if type(value) is not bool:
                raise ValueError(f"{name} is true or false")
            chosen[name] = value
            continue
        if not _number(value) or not bounds[0] <= value <= bounds[1] or (
                name == "seamWeldMm" and 0 < value < MIN_SEAM_WELD_MM):
            raise ValueError(f"{name} is out of its range")
        chosen[name] = round(float(value), 4)
    request: Dict[str, Any] = {"operation": operation, "gender": gender, "drawableType": drawable_type,
                               "sourcePose": source_pose, "bodyVersion": body_version}
    if category is not None:
        request["category"] = category
    if points:
        request["markers"] = points
    if chosen:
        request["options"] = chosen
    if len(_encode_json(request)) > MAX_REQUEST_BYTES:
        raise ValueError("the request is larger than 16 KiB")
    return request


def _encode_json(value: Any) -> bytes:
    return json.dumps(value, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("ascii")


def _little_endian(values: Any, typecode: str, what: str) -> Tuple[memoryview, array.array]:
    """``values`` as little-endian bytes without a copy where they already are (a numpy array or any buffer of
    ``typecode`` items), plus an :class:`array.array` of the native values to check them."""
    try:
        view = memoryview(values)
    except TypeError:
        view = None
    if view is not None:
        letters = ("f",) if typecode == "f" else ("I", "L")  # uint32 is "L" on Windows, "I" elsewhere
        formats = {prefix + letter for letter in letters for prefix in ("", "<", "=")}
        if view.format not in formats or view.itemsize != 4 or not view.c_contiguous:
            raise ValueError(f"{what} is a contiguous buffer of {'float32' if typecode == 'f' else 'uint32'} values")
        raw = view.cast("B")
        native = array.array(typecode)
        native.frombytes(raw)
        if sys.byteorder != "little":  # a buffer in native order: send its little-endian copy
            native.byteswap()
            raw = memoryview(native.tobytes())
            native.byteswap()
        return raw, native
    try:
        native = array.array(typecode, (float(v) if typecode == "f" else int(v) for v in values))
    except (TypeError, ValueError, OverflowError):
        raise ValueError(f"{what} holds numbers only") from None
    copy = array.array(typecode, native)
    if sys.byteorder != "little":
        copy.byteswap()
    return memoryview(copy.tobytes()), native


class MeshUpload:
    """A garment as the DCTM version 1 mesh part: ``"DCTM"``, ``u16`` version, ``u16`` flags (bit 0: vertex flags
    follow), ``u32`` vertex and triangle counts, ``f32[3N]`` positions, ``u32[3T]`` indices, then ``u8[N]`` flags.
    The arrays are the caller's buffers, not copies: do not change them until the upload finished."""

    def __init__(self, header: bytes, parts: Sequence[memoryview], vertex_count: int, triangle_count: int) -> None:
        self.header = header
        self.parts = (memoryview(header),) + tuple(parts)
        self.vertex_count = vertex_count
        self.triangle_count = triangle_count
        self.length = sum(part.nbytes for part in self.parts)


def encode_mesh(positions: Any, triangles: Any, flags: Any = None) -> MeshUpload:
    """Checks a garment against the service's limits and frames it as a DCTM mesh (raises ``ValueError``).

    ``positions`` are ``x, y, z`` triples in ped space metres (float32), ``triangles`` vertex index triples
    (uint32), ``flags`` one byte per vertex (:data:`FLAG_PINNED`, :data:`FLAG_LINING`) or ``None``. Buffers such as
    numpy arrays are used as they are."""
    position_bytes, values = _little_endian(positions, "f", "positions")
    if len(values) % 3 or len(values) < 9:
        raise ValueError("positions are at least three x, y, z triples")
    vertex_count = len(values) // 3
    if vertex_count > MAX_VERTICES:
        raise ValueError(f"at most {MAX_VERTICES} vertices")
    if not all(-MAX_COORDINATE <= value <= MAX_COORDINATE for value in values):  # NaN fails both comparisons
        raise ValueError(f"every coordinate is finite and within {MAX_COORDINATE:g} m of the origin")
    index_bytes, indices = _little_endian(triangles, "I", "triangles")
    if len(indices) % 3 or not indices:
        raise ValueError("triangles are vertex index triples")
    triangle_count = len(indices) // 3
    if triangle_count > MAX_TRIANGLES:
        raise ValueError(f"at most {MAX_TRIANGLES} triangles")
    if max(indices) >= vertex_count:
        raise ValueError("a triangle names a vertex that does not exist")
    parts = [position_bytes, index_bytes]
    if flags is not None:
        try:
            flag_bytes = memoryview(flags).cast("B")
        except TypeError:
            flag_bytes = memoryview(bytes(flags))
        if flag_bytes.nbytes != vertex_count:
            raise ValueError("flags hold one byte per vertex")
        if any(value & ~(FLAG_PINNED | FLAG_LINING) for value in flag_bytes):
            raise ValueError("a vertex flag uses an unknown bit")
        parts.append(flag_bytes)
    header = b"DCTM" + (1).to_bytes(2, "little") + (1 if flags is not None else 0).to_bytes(2, "little") \
        + vertex_count.to_bytes(4, "little") + triangle_count.to_bytes(4, "little")
    upload = MeshUpload(header, parts, vertex_count, triangle_count)
    if upload.length > MAX_MESH_BYTES:
        raise ValueError("the mesh is larger than 16 MiB")
    return upload


# ---- reading the answers ----------------------------------------------------------------------------------------


def _json_object(payload: bytes) -> Dict[str, Any]:
    if len(payload) > MAX_JSON_BYTES:
        raise FitError("invalid-response", "the answer is too large")
    try:
        value = json.loads(payload.decode("utf-8")) if payload else {}
    except (UnicodeDecodeError, ValueError, RecursionError):
        raise FitError("invalid-response", "the answer is not JSON") from None
    if not isinstance(value, dict):
        raise FitError("invalid-response", "the answer is not a JSON object")
    return value


def _issues(value: Any) -> Tuple[FitIssue, ...]:
    issues = []
    for entry in value[:32] if isinstance(value, list) else []:
        if not isinstance(entry, dict):
            continue
        code, field = entry.get("code"), entry.get("field")
        if isinstance(code, str) and _CODE.fullmatch(code):
            issues.append(FitIssue(code, field if isinstance(field, str) and _FIELD.fullmatch(field) else ""))
    return tuple(issues)


def _retry_after(headers: Dict[str, str], body: Dict[str, Any]) -> Optional[float]:
    for value in (headers.get("retry-after"), body.get("retryAfterSeconds")):
        try:
            seconds = float(value) if value is not None and not isinstance(value, bool) else None
        except (TypeError, ValueError):
            seconds = None  # a date or garbage: the caller's own wait applies
        if seconds is not None and math.isfinite(seconds) and 0 <= seconds <= 2 * 86400:
            return seconds
    return None


def failure(status: int, headers: Dict[str, str], payload: bytes) -> FitError:
    """The :class:`FitError` of a failure answer (the Creator Link failure shape)."""
    try:
        body = _json_object(payload)
    except FitError:
        body = {}
    code = body.get("failureCode")
    if not isinstance(code, str) or not _CODE.fullmatch(code):
        code = {400: "invalid_request", 401: "session_invalid", 403: "feature_not_entitled", 404: "not_found",
                413: "mesh_too_large", 415: "unsupported_format", 422: "mesh_invalid", 426: "plugin_update_required",
                429: "rate_limited", 503: "fit_unavailable"}.get(status, "server_error" if status >= 500 else "http")
    if status == 426:
        code = "plugin_update_required"
    version = body.get("bodyVersion")
    minimum = body.get("minVersion")
    retryable = bool(body.get("retryable")) or status in (429, 503) or status >= 500
    return FitError(code, "gta.clothing refused the request", status=status, retryable=retryable,
                    retry_after=_retry_after(headers, body), errors=_issues(body.get("errors")),
                    body_version=version if isinstance(version, str) and _BODY_VERSION.fullmatch(version) else None,
                    min_version=minimum if isinstance(minimum, str) and len(minimum) <= 64 else None)


def parse_status(status: int, headers: Dict[str, str], payload: bytes,
                 expected_vertices: Optional[int] = None) -> Union[FitStatus, FitResult]:
    """The answer of ``fit/status``: a :class:`FitResult` for a finished job, else its :class:`FitStatus`. A
    failure answer raises its :class:`FitError`."""
    if status != 200:
        raise failure(status, headers, payload)
    media = headers.get("content-type", "").split(";")[0].strip().lower()
    if media == RESULT_TYPE:
        return parse_result(payload, expected_vertices)
    body = _json_object(payload)
    state = body.get("state")
    job_id = body.get("jobId")
    if state not in STATES or not isinstance(job_id, str) or not _JOB_ID.fullmatch(job_id):
        raise FitError("invalid-response", "not a job state")
    progress = body.get("progress", 0)
    progress = min(1.0, max(0.0, float(progress))) if _number(progress) else 0.0
    stage = body.get("stage")
    position = body.get("queuePosition")
    code = body.get("failureCode")
    refunded = body.get("refunded")
    return FitStatus(
        job_id=job_id,
        state=state,
        stage=stage if stage in STAGES else None,
        progress=progress,
        queue_position=position if type(position) is int and 0 <= position <= 100000 else None,
        failure_code=code if isinstance(code, str) and _CODE.fullmatch(code) else (
            "server_error" if state == "failed" else None),
        retryable=body.get("retryable") is True,
        refunded=refunded if type(refunded) is bool else None,
        errors=_issues(body.get("errors")),
    )


_SECTIONS = {"positions": ("f32", 3, 4), "bones": ("u8", 4, 1), "weights": ("u8", 4, 1)}
_REPORT_NUMBERS = ("confidence", "matchedAreaShare", "maximumMarkerOffsetMm", "insideBodyBefore", "insideBodyAfter",
                   "pushedVertices", "unweightedVertices")


def parse_result(data: bytes, expected_vertices: Optional[int] = None) -> FitResult:
    """A finished job's binary answer (``application/vnd.dct.fit-result``), every section checked against the
    vertex count (and, when given, the vertex count that was uploaded) before it is used."""
    def bad(reason: str) -> FitError:
        return FitError("invalid-response", reason)

    if len(data) < 4 or len(data) > MAX_RESULT_BYTES:
        raise bad("the result has no header")
    header_length = int.from_bytes(data[:4], "little")
    if header_length > MAX_RESULT_HEADER_BYTES or 4 + header_length > len(data):
        raise bad("the result header does not fit")
    try:
        header = json.loads(bytes(data[4:4 + header_length]).decode("utf-8"))
    except (UnicodeDecodeError, ValueError, RecursionError):
        raise bad("the result header is not JSON") from None
    if not isinstance(header, dict) or header.get("format") != "dct-fit-result" or header.get("version") != 1:
        raise bad("not a fit result of version 1")
    outcome, operation = header.get("outcome"), header.get("operation")
    vertices, triangles, job_id = header.get("vertexCount"), header.get("triangleCount"), header.get("jobId")
    if outcome not in OUTCOMES or operation not in OPERATIONS or not isinstance(job_id, str) \
            or not _JOB_ID.fullmatch(job_id):
        raise bad("the result header is incomplete")
    if type(vertices) is not int or not 0 < vertices <= MAX_VERTICES or type(triangles) is not int \
            or not 0 <= triangles <= MAX_TRIANGLES:
        raise bad("the result's counts are out of range")
    if expected_vertices is not None and vertices != expected_vertices:
        raise bad("the result is of another mesh")
    payload = memoryview(data)[4 + header_length:]
    sections = header.get("sections")
    if not isinstance(sections, list):
        raise bad("the result has no sections")
    found: Dict[str, bytes] = {}
    for entry in sections:
        if not isinstance(entry, dict) or entry.get("name") not in _SECTIONS or entry.get("name") in found:
            raise bad("an unknown or repeated section")
        kind, components, size = _SECTIONS[entry["name"]]
        offset, length = entry.get("offset"), entry.get("length")
        if entry.get("type") != kind or entry.get("components") != components or type(offset) is not int \
                or type(length) is not int or offset < 0 or offset % size or length != vertices * components * size \
                or offset + length > len(payload):
            raise bad(f"the section {entry['name']} does not fit the result")
        found[entry["name"]] = bytes(payload[offset:offset + length])
    names: Dict[int, str] = {}
    bone_names = header.get("boneNames")
    for key, value in (bone_names.items() if isinstance(bone_names, dict) else ()):
        if not isinstance(key, str) or not key.isdigit() or not isinstance(value, str) or not _BONE.fullmatch(value):
            raise bad("a bone name is not readable")
        index = int(key)
        if index > 127:
            raise bad("a bone index is out of range")
        names[index] = value
    if outcome == "notOnBody":
        positions = bones = weights = None
    else:
        if set(found) != set(_SECTIONS):
            raise bad("the result lacks a section")
        positions, bones, weights = found["positions"], found["bones"], found["weights"]
        if max(bones) > 127:
            raise bad("a bone index is out of range")
        floats = array.array("f")
        floats.frombytes(positions)
        if sys.byteorder != "little":
            floats.byteswap()
        if not all(-MAX_COORDINATE * 2 <= value <= MAX_COORDINATE * 2 for value in floats):
            raise bad("a position is not finite")
        used = {bone for bone, weight in zip(bones, weights) if weight}
        if not used <= set(names):
            raise bad("the weights use a bone the result does not name")
    report_in = header.get("report") if isinstance(header.get("report"), dict) else {}
    report = {key: float(report_in[key]) for key in _REPORT_NUMBERS if _number(report_in.get(key))}
    warnings = []
    for entry in report_in.get("warnings", [])[:32] if isinstance(report_in.get("warnings"), list) else []:
        code = entry.get("code") if isinstance(entry, dict) else entry
        if isinstance(code, str) and _CODE.fullmatch(code) and code not in warnings:
            warnings.append(code)
    return FitResult(job_id, operation, outcome, vertices, triangles, positions, bones, weights, names,
                     tuple(warnings), report)


def parse_reference(payload: bytes) -> FitReference:
    """The answer of ``fit/reference``: the percentiles per body region."""
    body = _json_object(payload)
    version, gender, category, regions = (body.get("bodyVersion"), body.get("gender"), body.get("category"),
                                           body.get("regions"))
    if not isinstance(version, str) or not _BODY_VERSION.fullmatch(version) or gender not in GENDERS \
            or not isinstance(category, str) or not _CATEGORY.fullmatch(category) or not isinstance(regions, dict) \
            or len(regions) > 64:
        raise FitError("invalid-response", "not a fit reference")
    ranges: Dict[str, FitRange] = {}
    for name, value in regions.items():
        if not isinstance(name, str) or not _REGION.fullmatch(name) or not isinstance(value, dict):
            raise FitError("invalid-response", "a reference region is not readable")
        numbers = [value.get(key) for key in ("p10", "p50", "p90")]
        samples = value.get("samples")
        if not all(_number(v) and abs(v) <= 1000.0 for v in numbers) or type(samples) is not int or samples < 0:
            raise FitError("invalid-response", "a reference range is not readable")
        ranges[name] = FitRange(float(numbers[0]), float(numbers[1]), float(numbers[2]), samples)
    return FitReference(version, gender, category, ranges)


def parse_allowance(payload: bytes) -> Optional[FitAllowance]:
    """The fitting allowance from ``/me`` (``limits.pools.fit``), or ``None`` when the answer has none."""
    body = _json_object(payload)
    limits = body.get("limits") if isinstance(body.get("limits"), dict) else {}
    pools = limits.get("pools") if isinstance(limits.get("pools"), dict) else {}
    pool = pools.get("fit")
    if not isinstance(pool, dict):
        return None
    values = [pool.get(key) for key in ("perDay", "usedToday", "remainingToday")]
    if not all(type(v) is int and 0 <= v <= 1_000_000 for v in values):
        return None
    return FitAllowance(*values)


# ---- running calls off the host's thread ------------------------------------------------------------------------


class FitTask:
    """One :class:`FitClient` call on a daemon worker thread. :meth:`poll` never blocks; once it returns True,
    :meth:`result` returns the value or raises the :class:`FitError`. :meth:`cancel` stops an upload between two
    chunks (the call then fails with ``cancelled``) and keeps a network failure from being tried again; a call that
    finished all the same keeps its value, so an upload that made a job still names it (cancel that job).
    :attr:`sent` and :attr:`total` count the bytes of an upload."""

    def __init__(self, call: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
        self.cancel_event = threading.Event()
        self.sent = 0
        self.total = 0
        self._done = threading.Event()
        self._value: Any = None
        self._error: Optional[BaseException] = None

        def progress(sent: int, total: int) -> None:
            self.sent, self.total = sent, total

        def work() -> None:
            try:
                self._value = call(*args, cancel=self.cancel_event, progress=progress, **kwargs)
            except BaseException as exc:  # handed to whoever polls the task
                self._error = exc
            finally:
                self._done.set()

        threading.Thread(target=work, name="dct-link-fit", daemon=True).start()

    @property
    def done(self) -> bool:
        return self._done.is_set()

    def poll(self) -> bool:
        return self._done.is_set()

    def result(self) -> Any:
        if not self._done.is_set():
            raise RuntimeError("the call is still running")
        if self._error is not None:
            raise self._error
        return self._value

    def cancel(self) -> None:
        self.cancel_event.set()

    def wait(self, timeout: Optional[float] = None) -> Any:
        """Blocking helper for scripts and tests."""
        if not self._done.wait(timeout):
            raise FitError("network", "the call did not finish in time", retryable=True)
        return self.result()


class _Response(NamedTuple):
    status: int
    headers: Dict[str, str]
    payload: bytes


class FitClient:
    """The fitting routes for the account signed in through ``link_auth`` (a :class:`dct_link.auth.LinkAuth`).

    ``timeout`` is the idle timeout of every request: a connection that sends or receives nothing for that long
    fails with ``network``. Uploads go out in chunks of ``chunk_bytes``."""

    def __init__(self, link_auth: Any, *, timeout: float = 30.0, chunk_bytes: int = 256 * 1024,
                 sleep: Callable[[float], None] = time.sleep) -> None:
        self.auth = link_auth
        self.http: auth.HttpClient = link_auth.http
        self.timeout = timeout
        self.chunk_bytes = max(4096, int(chunk_bytes))
        self._sleep = sleep

    # ---- the calls (blocking) ----------------------------------------------------------------------

    def submit(self, request: Dict[str, Any], mesh: MeshUpload, *, cancel: Optional[threading.Event] = None,
               progress: Optional[Callable[[int, int], None]] = None) -> FitSubmitted:
        """Uploads a garment (``fit/jobs``). ``request`` comes from :func:`fit_request`. The service may answer
        ``fit_busy`` (wait ``retry_after`` and submit again) or ``quota_exceeded`` (the day's fits are used)."""
        fit_request(request.get("operation"), request.get("gender"), request.get("drawableType"),
                    request.get("bodyVersion"), source_pose=request.get("sourcePose", "rest"),
                    category=request.get("category"), markers=request.get("markers"), options=request.get("options"))
        unknown = set(request) - {"operation", "gender", "drawableType", "sourcePose", "bodyVersion", "category",
                                  "markers", "options"}
        if unknown:
            raise ValueError("the request has members the service does not know")
        boundary = "dctfit" + secrets.token_hex(16)
        head = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"request\"\r\n"
                "Content-Type: application/json\r\n\r\n").encode("ascii") + _encode_json(request) + (
            f"\r\n--{boundary}\r\nContent-Disposition: form-data; name=\"mesh\"; filename=\"garment.dctm\"\r\n"
            "Content-Type: application/octet-stream\r\n\r\n").encode("ascii")
        tail = f"\r\n--{boundary}--\r\n".encode("ascii")
        parts = (memoryview(head),) + mesh.parts + (memoryview(tail),)
        response = self._call("POST", "/link/api/fit/jobs", parts=parts,
                              content_type=f"multipart/form-data; boundary={boundary}", accept="application/json",
                              max_bytes=MAX_JSON_BYTES, safe=False, cancel=cancel, progress=progress)
        if response.status != 202:
            raise failure(response.status, response.headers, response.payload)
        body = _json_object(response.payload)
        job_id, state, remaining = body.get("jobId"), body.get("state", "queued"), body.get("remainingToday")
        if not isinstance(job_id, str) or not _JOB_ID.fullmatch(job_id) or state not in STATES:
            raise FitError("invalid-response", "the upload's answer names no job", uploaded=True)
        return FitSubmitted(job_id, state, remaining if type(remaining) is int and remaining >= 0 else None)

    def status(self, job_id: str, expected_vertices: Optional[int] = None, *,
               cancel: Optional[threading.Event] = None, progress: Any = None) -> Union[FitStatus, FitResult]:
        """A job's state, or its result once it finished (``fit/status``)."""
        response = self._json_call("/link/api/fit/status", {"jobId": self._job(job_id)},
                                   accept=f"{RESULT_TYPE}, application/json", max_bytes=MAX_RESULT_BYTES,
                                   cancel=cancel)
        return parse_status(response.status, response.headers, response.payload, expected_vertices)

    def cancel(self, job_id: str, *, cancel: Optional[threading.Event] = None, progress: Any = None) -> bool:
        """Cancels a job (``fit/cancel``). True when the service took it; False when it no longer knows the job."""
        response = self._json_call("/link/api/fit/cancel", {"jobId": self._job(job_id)}, cancel=cancel)
        if response.status in (200, 204):
            return True
        error = failure(response.status, response.headers, response.payload)
        if error.code == "not_found":
            return False
        raise error

    def reference(self, gender: str, category: str, body_version: str, *,
                  cancel: Optional[threading.Event] = None, progress: Any = None) -> FitReference:
        """How far ordinary game clothing of ``category`` sits from each body region (``fit/reference``)."""
        if gender not in GENDERS or not isinstance(category, str) or not _CATEGORY.fullmatch(category) \
                or not isinstance(body_version, str) or not _BODY_VERSION.fullmatch(body_version):
            raise ValueError("gender, category and bodyVersion as the service names them")
        response = self._json_call("/link/api/fit/reference",
                                   {"gender": gender, "category": category, "bodyVersion": body_version},
                                   cancel=cancel)
        if response.status != 200:
            raise failure(response.status, response.headers, response.payload)
        return parse_reference(response.payload)

    def allowance(self, *, cancel: Optional[threading.Event] = None, progress: Any = None) -> Optional[FitAllowance]:
        """The account's fits left today (``limits.pools.fit`` of ``/me``); ``None`` when the account has none."""
        response = self._call("GET", "/link/api/me", accept="application/json", max_bytes=MAX_JSON_BYTES, safe=True,
                              cancel=cancel)
        if response.status != 200:
            raise failure(response.status, response.headers, response.payload)
        return parse_allowance(response.payload)

    # ---- the same calls on a worker thread ---------------------------------------------------------

    def begin_submit(self, request: Dict[str, Any], mesh: MeshUpload) -> FitTask:
        return FitTask(self.submit, request, mesh)

    def begin_status(self, job_id: str, expected_vertices: Optional[int] = None) -> FitTask:
        return FitTask(self.status, job_id, expected_vertices)

    def begin_cancel(self, job_id: str) -> FitTask:
        return FitTask(self.cancel, job_id)

    def begin_reference(self, gender: str, category: str, body_version: str) -> FitTask:
        return FitTask(self.reference, gender, category, body_version)

    def begin_allowance(self) -> FitTask:
        return FitTask(self.allowance)

    # ---- HTTP ----------------------------------------------------------------------------------------

    @staticmethod
    def _job(job_id: str) -> str:
        if not isinstance(job_id, str) or not _JOB_ID.fullmatch(job_id):
            raise ValueError("a job id is 22 characters of base64url")
        return job_id

    def _json_call(self, path: str, body: Dict[str, Any], *, accept: str = "application/json",
                   max_bytes: int = MAX_JSON_BYTES, cancel: Optional[threading.Event] = None) -> _Response:
        data = _encode_json(body)
        return self._call("POST", path, parts=(memoryview(data),), content_type="application/json", accept=accept,
                          max_bytes=max_bytes, safe=True, cancel=cancel)

    def _token(self) -> str:
        try:
            token = self.auth.access_token()
        except auth.PluginUpdateRequired as exc:
            raise FitError("plugin_update_required", "update the plugin", min_version=exc.min_version) from None
        except auth.AccountBlocked as exc:
            raise FitError(exc.code, "the account cannot use Creator Link") from None
        except auth.SignInRequired:
            raise FitError("signed-out", "sign in again") from None
        except auth.AuthError as exc:
            if exc.code in ("network", "tls", "invalid-response", "refresh_in_progress"):
                raise FitError("network", "gta.clothing could not be reached", retryable=True) from None
            raise FitError("signed-out", "sign in again") from None
        if not token:
            raise FitError("signed-out", "nobody is signed in")
        return token

    def _call(self, method: str, path: str, *, parts: Sequence[memoryview] = (), content_type: Optional[str] = None,
              accept: str, max_bytes: int, safe: bool, cancel: Optional[threading.Event] = None,
              progress: Optional[Callable[[int, int], None]] = None) -> _Response:
        """One request with the access token: a ``401`` renews the token and tries once more; a network failure of
        a request that changes nothing (``safe``), or of an upload that never went out whole, is tried again."""
        renewed = False
        retries = list(_RETRY_PAUSES)
        while True:
            if cancel is not None and cancel.is_set():
                raise FitError("cancelled", "the call was cancelled")
            token = self._token()
            try:
                response = self._exchange(method, path, parts, content_type, token, accept, max_bytes, cancel,
                                          progress)
            except FitError as exc:
                if exc.code == "network" and retries and (safe or not exc.uploaded):
                    pause = retries.pop(0)
                    if cancel is not None:
                        if cancel.wait(pause):
                            raise FitError("cancelled", "the call was cancelled") from None
                    else:
                        self._sleep(pause)
                    continue
                raise
            if response.status == 401:
                if not renewed:
                    renewed = True
                    self.auth.invalidate_access_token()  # renew once: the token may have expired a moment ago
                    continue
                raise FitError("signed-out", "gta.clothing no longer accepts the sign-in", status=401)
            if response.status == 426:
                raise failure(response.status, response.headers, response.payload)
            return response

    def _connection(self) -> http.client.HTTPConnection:
        parts = urllib.parse.urlsplit(self.http.base_url)
        host = parts.hostname or ""
        tls = parts.scheme == "https"
        port = parts.port or (443 if tls else 80)
        proxy = None
        if not self.http.loopback:
            candidate = urllib.request.getproxies().get(parts.scheme)
            if candidate and not urllib.request.proxy_bypass(host):
                proxy = urllib.parse.urlsplit(candidate)
                if proxy.scheme != "http" or not proxy.hostname:
                    proxy = None  # only plain HTTP proxies, as everywhere in dct_link
        if tls:
            context = self.http.ssl_context or ssl.create_default_context()
            if proxy is not None:
                connection = http.client.HTTPSConnection(proxy.hostname, proxy.port or 80, timeout=self.timeout,
                                                         context=context)
                connection.set_tunnel(host, port)
                return connection
            return http.client.HTTPSConnection(host, port, timeout=self.timeout, context=context)
        return http.client.HTTPConnection(host, port, timeout=self.timeout)

    def _exchange(self, method: str, path: str, parts: Sequence[memoryview], content_type: Optional[str], token: str,
                  accept: str, max_bytes: int, cancel: Optional[threading.Event],
                  progress: Optional[Callable[[int, int], None]]) -> _Response:
        url = self.http.url(path)  # checks the path
        target = urllib.parse.urlsplit(url).path
        total = sum(part.nbytes for part in parts)
        connection = self._connection()
        uploaded = False
        try:
            try:
                connection.connect()
            except (OSError, http.client.HTTPException) as exc:
                if isinstance(exc, ssl.SSLCertVerificationError):
                    raise FitError("network", "the gta.clothing certificate could not be verified") from None
                raise FitError("network", "gta.clothing could not be reached", retryable=True) from None
            header = auth.client_header(self.http.info)
            connection.putrequest(method, target, skip_accept_encoding=True)
            connection.putheader("Accept", accept)
            connection.putheader("Accept-Encoding", "identity")
            connection.putheader("Authorization", "Bearer " + token)
            connection.putheader("X-DCT-Link-Client", header)
            connection.putheader("User-Agent", header)
            connection.putheader("Connection", "close")
            if parts or method == "POST":
                connection.putheader("Content-Type", content_type or "application/json")
                connection.putheader("Content-Length", str(total))
            early: Optional[BaseException] = None
            try:
                connection.endheaders()
                sent = 0
                for part in parts:
                    view = part.cast("B") if part.format != "B" else part
                    for start in range(0, view.nbytes, self.chunk_bytes):
                        if cancel is not None and cancel.is_set():
                            raise FitError("cancelled", "the upload was cancelled")
                        piece = view[start:start + self.chunk_bytes]
                        connection.send(piece)
                        sent += piece.nbytes
                        if progress is not None:
                            progress(sent, total)
                uploaded = sent == total
            except (OSError, http.client.HTTPException) as exc:
                early = exc  # the service may have answered before it read everything (a refusal); read it below
            try:
                response = connection.getresponse()
                status = response.status
                headers = {name.lower(): value for name, value in response.getheaders()}
                payload = response.read(max_bytes + 1)
            except (OSError, http.client.HTTPException, ValueError):
                raise FitError("network", "the connection to gta.clothing broke", retryable=True,
                               uploaded=uploaded) from None
            if len(payload) > max_bytes:
                raise FitError("invalid-response", "the answer is too large", uploaded=uploaded)
            if early is not None and 200 <= status < 300:
                raise FitError("network", "the upload did not finish", retryable=True, uploaded=uploaded)
            if 300 <= status < 400:
                raise FitError("invalid-response", "gta.clothing answered with a redirect", uploaded=uploaded)
            return _Response(status, headers, payload)
        finally:
            try:
                connection.close()
            except OSError:
                pass  # already closed
