# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2026 Schmid Software Solutions (https://schmid-software.de)
"""Fit on gta.clothing and Transfer Weights, without Blender.

Fit on gta.clothing sends the garment as it sits after Align to Body (its triangles in ped space, the markers, the
gender, slot and category) to gta.clothing, which puts it in the game's pose, gives it the freemode body's weights and
pushes it out of the body. Transfer Weights sends a garment that already sits on the body and gets the weights only.
Both use one of the account's fits for the day.

* :func:`prepare_upload` turns the garment's arrays into what the service takes (float32 positions, triangles without
  the ones it refuses, the Pinned and Lining flags) and a digest, so a result is applied only to the shape it was made
  for.
* :class:`FitRun` is one run: the upload, waiting when gta.clothing is busy, polling the job once a second, Cancel.
  :class:`FitService` keeps the run, the fits left today and the usual ranges of game clothing for the fit check. Both
  are driven by the add-on's timer (:meth:`FitService.tick`) and never block it: the requests run on dct_link's worker
  threads.
* :func:`weight_groups` turns the result's weights into vertex groups by bone name, never on the root bone.
* :func:`failure_lines` words every failure the service can answer for a beginner.

Nothing here imports Blender; numpy does the arithmetic.
"""

from __future__ import annotations

import hashlib
import math
import time
from typing import Any, Callable, Dict, List, NamedTuple, Optional, Sequence, Tuple

import numpy as np

from .dct_link import fit
from .strings import Msg, UserError, msg

OPERATIONS = ("fit", "weights")
#: The service's name of each marker of the add-on.
SERVICE_MARKERS = {
    "pelvis": "pelvis", "chest": "chest", "neck": "neck",
    "shoulder_l": "lShoulder", "elbow_l": "lElbow", "wrist_l": "lWrist",
    "shoulder_r": "rShoulder", "elbow_r": "rElbow", "wrist_r": "rWrist",
    "hip_l": "lHip", "knee_l": "lKnee", "ankle_l": "lAnkle",
    "hip_r": "rHip", "knee_r": "rKnee", "ankle_r": "rAnkle",
}
#: The game clothing a slot is compared with in the fit check (gta.clothing's reference categories).
REFERENCE_CATEGORIES = {"jbib": "top", "accs": "undershirt", "lowr": "legs", "feet": "shoes"}
#: The body regions of gta.clothing's reference behind each region of the fit check.
REFERENCE_REGIONS = {
    "shoulders": ("shoulderL", "shoulderR"),
    "upper_arms": ("upperArmL", "upperArmR"),
    "forearms": ("forearmL", "forearmR"),
    "cuffs": ("forearmL", "forearmR"),
    "chest": ("chest",),
    "back": ("back",),
    "waist": ("abdomen", "lowerBack"),
    "hips": ("pelvis",),
    "neck": ("neck",),
    "legs": ("thighL", "thighR", "calfL", "calfR"),
}
#: Shoes measure their single region against the feet.
SHOE_REGIONS = ("footL", "footR")
#: The options of Fit on gta.clothing, as the panel offers them, with the service's defaults.
DEFAULT_OPTIONS = {"clearanceMm": 3.0, "pushOut": True, "maxPushMm": 30.0, "seamWeldMm": 1.5,
                   "matchProportions": False}
#: Bones the add-on never weights to: the skeleton's root (index 0) moves the whole ped.
ROOT_BONE = 0
ROOT_NAMES = frozenset({"SKEL_ROOT"})
#: A triangle whose doubled area is below this (square metres, squared) has no area for the service.
DEGENERATE_CROSS_SQUARED = 1e-20


# --------------------------------------------------------------------------------------------------
# The upload
# --------------------------------------------------------------------------------------------------


def service_markers(markers: Dict[str, Sequence[float]]) -> Dict[str, List[float]]:
    """The markers in the service's names: the torso markers and each limb chain that is complete (a top has its hip
    markers but no knees, so its leg chains stay home)."""
    named = {SERVICE_MARKERS[name]: [float(v) for v in point] for name, point in markers.items()
             if name in SERVICE_MARKERS}
    for chain in fit.CHAINS:
        if not all(name in named for name in chain):
            for name in chain:
                named.pop(name, None)
    return named


def mesh_digest(positions: np.ndarray, triangles: np.ndarray) -> str:
    """What identifies the garment's shape: its float32 positions and its triangles."""
    digest = hashlib.sha256()
    digest.update(np.ascontiguousarray(positions, dtype="<f4").tobytes())
    digest.update(np.ascontiguousarray(triangles, dtype="<u4").tobytes())
    return digest.hexdigest()


class Upload(NamedTuple):
    positions: np.ndarray
    triangles: np.ndarray
    flags: Optional[np.ndarray]
    #: Triangles left out because the service refuses them (no area, or a repeat of another).
    dropped: int
    digest: str

    def mesh(self) -> fit.MeshUpload:
        return fit.encode_mesh(self.positions.reshape(-1), self.triangles.reshape(-1),
                               None if self.flags is None else self.flags)


def usable_triangles(positions: np.ndarray, triangles: np.ndarray) -> np.ndarray:
    """Which triangles the service accepts: each has an area and none repeats another's corners in the same order (the
    back face of a double-sided panel, the same corners the other way round, is fine)."""
    tris = np.asarray(triangles, dtype=np.int64).reshape(-1, 3)
    if not len(tris):
        return np.zeros(0, dtype=bool)
    points = np.asarray(positions, dtype=np.float32).reshape(-1, 3)
    a, b, c = (points[tris[:, i]].astype(np.float64) for i in range(3))
    cross = np.cross(b - a, c - a)
    keep = ((cross * cross).sum(axis=1) >= DEGENERATE_CROSS_SQUARED) & (tris[:, 0] != tris[:, 1]) \
        & (tris[:, 1] != tris[:, 2]) & (tris[:, 0] != tris[:, 2])
    # Corners compare by position: vertices at the same place count as one corner.
    _, ids = np.unique(np.ascontiguousarray(points).view(np.dtype((np.void, 12))).reshape(-1), return_inverse=True)
    corners = ids.reshape(-1)[tris]
    first = np.argmin(corners, axis=1)
    rotated = np.take_along_axis(corners, (first[:, None] + np.arange(3)) % 3, axis=1)
    candidates = np.nonzero(keep)[0]
    if len(candidates):
        _, first_seen = np.unique(rotated[candidates], axis=0, return_index=True)
        unique = np.zeros(len(tris), dtype=bool)
        unique[candidates[first_seen]] = True
        keep &= unique
    return keep


def prepare_upload(positions: Any, triangles: Any, pinned: Optional[np.ndarray] = None,
                   lining: Optional[np.ndarray] = None) -> Upload:
    """The garment as the service takes it. Raises :class:`UserError` with what to do when it cannot be sent."""
    points = np.ascontiguousarray(np.asarray(positions, dtype=np.float64).reshape(-1, 3), dtype=np.float32)
    tris = np.asarray(triangles, dtype=np.int64).reshape(-1, 3)
    digest = mesh_digest(points, tris)
    if len(points) > fit.MAX_VERTICES or len(tris) > fit.MAX_TRIANGLES:
        raise UserError(msg("fit.input.too-large", vertices=len(points), triangles=len(tris)))
    if len(points) < 3 or not len(tris):
        raise UserError(msg("garment.why.empty"))
    if not np.isfinite(points).all():
        raise UserError(msg("fit.input.broken"))
    if (np.abs(points) > fit.MAX_COORDINATE).any():
        raise UserError(msg("fit.input.far"))
    keep = usable_triangles(points, tris)
    if not keep.any():
        raise UserError(msg("fit.input.degenerate"))
    flags = np.zeros(len(points), dtype=np.uint8)
    if pinned is not None:
        flags[np.asarray(pinned, dtype=bool)] |= fit.FLAG_PINNED
    if lining is not None:
        flags[np.asarray(lining, dtype=bool)] |= fit.FLAG_LINING
    kept = np.ascontiguousarray(tris[keep], dtype=np.uint32)
    return Upload(points, kept, flags if flags.any() else None, int((~keep).sum()), digest)


def densest_seam_cell(positions: Any, triangles: Any, seam_weld_mm: float) -> Tuple[int, np.ndarray]:
    """The spot where the most open-edge vertices crowd (the vertices on an edge only one triangle uses), counted in
    cubes as wide as the seam weld, as gta.clothing counts them before it fits: how many lie in the fullest cube and
    which. Nothing is counted while the seam weld is off."""
    tris = np.asarray(triangles, dtype=np.int64).reshape(-1, 3)
    if seam_weld_mm <= 0 or not len(tris):
        return 0, np.zeros(0, dtype=np.int64)
    points = np.asarray(positions, dtype=np.float32).reshape(-1, 3)
    edges = np.sort(np.concatenate([tris[:, [0, 1]], tris[:, [1, 2]], tris[:, [2, 0]]]), axis=1)
    keys = edges[:, 0] * (len(points) + 1) + edges[:, 1]
    unique, first, uses = np.unique(keys, return_index=True, return_counts=True)
    single = edges[first[uses == 1]]
    boundary = np.unique(single.reshape(-1))
    if not len(boundary):
        return 0, np.zeros(0, dtype=np.int64)
    size = np.float32(seam_weld_mm / 1000.0)
    cells = np.floor(points[boundary] / size).astype(np.int64)
    _, inverse, counts = np.unique(cells, axis=0, return_inverse=True, return_counts=True)
    fullest = int(np.argmax(counts))
    return int(counts[fullest]), boundary[inverse.reshape(-1) == fullest]


def fit_options(clearance: float, push_out: bool, max_push: float, seam_weld: float,
                match_proportions: bool) -> Dict[str, Any]:
    """The options of Fit on gta.clothing, each kept within the service's range."""
    weld = min(3.0, max(0.0, float(seam_weld)))
    if 0.0 < weld < fit.MIN_SEAM_WELD_MM:
        weld = fit.MIN_SEAM_WELD_MM
    return {"clearanceMm": round(min(20.0, max(0.0, float(clearance))), 3), "pushOut": bool(push_out),
            "maxPushMm": round(min(100.0, max(1.0, float(max_push))), 3), "seamWeldMm": round(weld, 3),
            "matchProportions": bool(match_proportions)}


def build_request(operation: str, gender: str, slot: str, category: str, body_version: str,
                  markers: Dict[str, Sequence[float]], options: Dict[str, Any]) -> Dict[str, Any]:
    """The request part of a run: the garment sits on the body (Align to Body put it in the game's pose), so the source
    pose is the rest pose, and the markers tell the service where its joints are. Raises :class:`UserError`."""
    if operation not in OPERATIONS:
        raise ValueError(operation)
    chosen = dict(options) if operation == "fit" else {"seamWeldMm": options.get("seamWeldMm", 1.5)}
    try:
        return fit.fit_request(operation, gender, slot, body_version, source_pose="rest",
                               category=REFERENCE_CATEGORIES.get(slot),
                               markers=service_markers(markers) if operation == "fit" else None, options=chosen)
    except ValueError as exc:
        raise UserError(msg("fit.input.marker-far")) from exc


# --------------------------------------------------------------------------------------------------
# The result
# --------------------------------------------------------------------------------------------------


def result_positions(result: fit.FitResult) -> Optional[np.ndarray]:
    if result.positions is None:
        return None
    return np.frombuffer(result.positions, dtype="<f4").astype(np.float64).reshape(-1, 3)


def weight_groups(result: fit.FitResult) -> Tuple[Dict[str, List[Tuple[float, np.ndarray]]], int]:
    """The result's weights as vertex groups: bone name to ``(weight, vertex indices)`` pairs, the weights of each vertex
    summing to one. Influences on the root bone or on a bone without a name are left out (the vertex's other influences
    take their share). Also returns how many vertices are left without weights."""
    if result.bones is None or result.weights is None:
        return {}, result.vertex_count
    bones = np.frombuffer(result.bones, dtype=np.uint8).reshape(-1, 4).astype(np.int64)
    weights = np.frombuffer(result.weights, dtype=np.uint8).reshape(-1, 4).astype(np.float64)
    usable = np.zeros(256, dtype=bool)
    for index, name in result.bone_names.items():
        usable[index] = index != ROOT_BONE and name not in ROOT_NAMES
    weights = np.where(usable[bones], weights, 0.0)
    totals = weights.sum(axis=1)
    weights = np.divide(weights, totals[:, None], out=np.zeros_like(weights), where=totals[:, None] > 0)
    groups: Dict[str, List[Tuple[float, np.ndarray]]] = {}
    for slot in range(4):
        rows = np.nonzero(weights[:, slot] > 0)[0]
        if not len(rows):
            continue
        quantized = np.round(weights[rows, slot] * 1_000_000).astype(np.int64)
        keys = bones[rows, slot] * 2_000_000 + quantized
        order = np.argsort(keys, kind="stable")
        keys = keys[order]
        starts = np.concatenate(([0], np.nonzero(np.diff(keys))[0] + 1, [len(keys)]))
        for start, end in zip(starts[:-1], starts[1:]):
            bone, weight = divmod(int(keys[start]), 2_000_000)
            groups.setdefault(result.bone_names[bone], []).append((weight / 1_000_000, rows[order[start:end]]))
    return groups, int((totals <= 0).sum())


# --------------------------------------------------------------------------------------------------
# Texts
# --------------------------------------------------------------------------------------------------

#: The text of each failure the service (or the connection to it) can end a run with.
FAILURE_TEXTS = {
    "invalid_request": "fit.error.update",
    "unsupported_format": "fit.error.update",
    "plugin_update_required": "fit.error.plugin-update",
    "invalid-response": "fit.error.update",
    "session_invalid": "fit.error.signed-out",
    "session_expired": "fit.error.signed-out",
    "session_revoked": "fit.error.signed-out",
    "signed-out": "fit.error.signed-out",
    "account_locked": "fit.error.locked",
    "feature_not_entitled": "fit.error.not-entitled",
    "feature_unavailable": "fit.error.switched-off",
    "fit_unavailable": "fit.error.unavailable",
    "not_found": "fit.error.not-found",
    "body_version_mismatch": "fit.error.body-version",
    "mesh_too_large": "fit.error.too-large",
    "mesh_invalid": "fit.error.mesh-invalid",
    "quota_exceeded": "fit.error.quota",
    "fit_busy": "fit.error.busy",
    "rate_limited": "fit.error.rate-limited",
    "server_error": "fit.error.server",
    "fit_timeout": "fit.error.timeout",
    "network": "fit.error.network",
    "cancelled": "fit.error.cancelled",
}
#: The text of each problem the service names in ``errors``. Problems only a broken add-on could cause share one text.
INPUT_TEXTS = {
    **{code: "fit.input.add-on" for code in (
        "request_invalid", "request_part_missing", "mesh_part_missing", "part_unexpected", "operation_invalid",
        "gender_invalid", "drawable_type_invalid", "category_invalid", "source_pose_invalid", "source_pose_not_rest",
        "body_version_invalid", "job_id_invalid", "mesh_format_invalid", "mesh_version_unsupported",
        "mesh_header_invalid", "mesh_truncated", "mesh_trailing_data", "positions_invalid", "triangles_invalid",
        "flags_invalid", "triangle_index_out_of_range", "too_many_markers", "marker_unknown", "marker_invalid")},
    "slot_unsupported": "fit.input.slot",
    "options_out_of_range": "fit.input.options",
    "mesh_too_large": "fit.error.too-large",
    "too_many_vertices": "fit.error.too-large",
    "too_many_triangles": "fit.error.too-large",
    "coordinate_not_finite": "fit.input.broken",
    "coordinate_out_of_range": "fit.input.far",
    "triangle_degenerate": "fit.input.degenerate",
    "triangle_duplicate": "fit.input.duplicate",
    "seam_too_dense": "fit.input.seam-dense",
    "marker_out_of_range": "fit.input.marker-far",
    "marker_far": "fit.input.marker-far",
    "marker_missing": "fit.input.marker-missing",
    "marker_side": "fit.input.marker-side",
    "marker_inconsistent": "fit.input.marker-length",
    "body_gender_mismatch": "fit.input.gender",
    "upload_timeout": "fit.error.upload-timeout",
}
WARNING_TEXTS = {code: f"fit.warning.{code.replace('_', '-')}" for code in fit.WARNING_CODES}
#: What the panel says a run is doing, by stage: the check of the garment, then "Fitting" for the rest (the panel names
#: no step of the work on gta.clothing).
STAGE_TEXTS = {stage: "fit.stage.validating" if stage == "validating" else "fit.stage.running" for stage in fit.STAGES}


def wait_text(seconds: Optional[float]) -> Msg:
    """``in about N hours`` (or minutes) for a wait the service asked for."""
    if seconds is None or seconds <= 0:
        return msg("fit.wait.later")
    if seconds < 90 * 60:
        return msg("fit.wait.minutes", count=max(1, int(math.ceil(seconds / 60.0))))
    return msg("fit.wait.hours", count=int(round(seconds / 3600.0)))


def failure_lines(code: str, issues: Sequence[fit.FitIssue] = (), *, retry_after: Optional[float] = None,
                  refunded: Optional[bool] = None, uploaded: bool = False,
                  started: bool = False) -> List[Tuple[str, Msg]]:
    """What the panel says about a run that ended without a result: the failure, each problem the service named (once
    per text), and whether the fit counts against today's fits. ``started``: a cancelled fit had begun on gta.clothing,
    so it counts even when the service's answer did not say."""
    key = FAILURE_TEXTS.get(code)
    level = "INFO" if code == "cancelled" else "ERROR"
    if code == "quota_exceeded":
        lines = [(level, msg(key, wait=wait_text(retry_after)))]
    elif code == "network" and uploaded:
        lines = [(level, msg("fit.error.network-uploaded"))]
    elif any(issue.code == "upload_timeout" for issue in issues):
        lines = [(level, msg("fit.error.upload-timeout"))]  # a slow connection, not an add-on gta.clothing cannot read
        issues = [issue for issue in issues if issue.code != "upload_timeout"]
    elif key is not None:
        lines = [(level, msg(key))]
    else:
        lines = [(level, msg("fit.error.other", code=code))]
    seen = set()
    for issue in issues:
        text = INPUT_TEXTS.get(issue.code)
        if text is None:
            text = "fit.input.other"
        if text not in seen:
            seen.add(text)
            lines.append(("ERROR", msg(text, code=issue.code) if text == "fit.input.other" else msg(text)))
    if refunded is True:
        lines.append(("INFO", msg("fit.refunded")))
    elif code == "cancelled" and (refunded is False or (refunded is None and started)):
        lines.append(("INFO", msg("fit.cancelled-counted")))
    elif refunded is False:
        lines.append(("INFO", msg("fit.counted")))
    return lines


def warning_lines(result: fit.FitResult) -> List[Tuple[str, Msg]]:
    return [("WARNING", msg(WARNING_TEXTS[code])) for code in result.warnings if code in WARNING_TEXTS]


# --------------------------------------------------------------------------------------------------
# The fit check's usual ranges
# --------------------------------------------------------------------------------------------------


def usual_ranges(reference: fit.FitReference, category: str) -> Dict[str, Tuple[float, float, float]]:
    """The usual ``(p10, p50, p90)`` of game clothing for each region of the fit check: the reference regions behind it,
    each weighted by how many points were measured there."""
    ranges: Dict[str, Tuple[float, float, float]] = {}
    for region, names in REFERENCE_REGIONS.items():
        if category == "shoes" and region == "legs":
            names = SHOE_REGIONS
        found = [reference.regions[name] for name in names if name in reference.regions
                 and reference.regions[name].samples > 0]
        total = sum(r.samples for r in found)
        if total:
            ranges[region] = tuple(sum(getattr(r, key) * r.samples for r in found) / total
                                   for key in ("p10", "p50", "p90"))  # type: ignore[assignment]
    return ranges


# --------------------------------------------------------------------------------------------------
# One run
# --------------------------------------------------------------------------------------------------


class FitRun:
    """One Fit on gta.clothing or Transfer Weights: the upload, a wait while gta.clothing is busy, polling once a
    second, Cancel. :meth:`tick` advances it without blocking; once :attr:`ended`, :attr:`result` holds the garment or
    :attr:`lines` say why not."""

    POLL_SECONDS = 1.0
    #: How long the run keeps trying while gta.clothing is busy, and the wait between tries (the service's hint, kept
    #: within these bounds).
    BUSY_LIMIT_SECONDS = 300.0
    BUSY_WAIT = (2.0, 120.0)
    #: Polls in a row that may fail (the network, gta.clothing answering busy or with a server error) before the run
    #: gives up, and the longest wait between two of them.
    MAX_POLL_FAILURES = 5
    POLL_RETRY_LIMIT = 120.0

    def __init__(self, client: fit.FitClient, operation: str, request: Dict[str, Any], upload: Upload, key: Any,
                 clock: Callable[[], float] = time.monotonic) -> None:
        self.client = client
        self.operation = operation
        self.request = request
        self.upload = upload
        self.mesh = upload.mesh()
        #: What the run belongs to (the garment, in the add-on); the result is applied only to it.
        self.key = key
        self.clock = clock
        self.state = "uploading"
        self.job_id: Optional[str] = None
        self.stage: Optional[str] = None
        self.progress = 0.0
        self.queue_position: Optional[int] = None
        self.result: Optional[fit.FitResult] = None
        self.error: Optional[fit.FitError] = None
        self.refunded: Optional[bool] = None
        self.lines: List[Tuple[str, Msg]] = []
        self.remaining_today: Optional[int] = None
        #: Set by the service once the add-on has dealt with the end of the run.
        self.handled = False
        self.cancel_requested = False
        #: The run had reached ``running`` when Cancel was chosen: the fit had begun and counts.
        self.cancelled_running = False
        #: The cancel sent when the run gave up on a job gta.clothing still has (nobody waits for its answer).
        self.abandoned: Optional[fit.FitTask] = None
        self._started = clock()
        self._busy_since: Optional[float] = None
        self._retry_at = 0.0
        self._next_poll = 0.0
        self._poll_failures = 0
        self._task: Optional[fit.FitTask] = client.begin_submit(request, self.mesh)

    @property
    def ended(self) -> bool:
        return self.state in ("done", "failed", "cancelled")

    def fraction(self) -> float:
        """How far the run is, for the panel's progress bar."""
        if self.state == "uploading" and self._task is not None and self._task.total:
            return 0.1 * self._task.sent / self._task.total
        if self.state in ("waiting", "queued"):
            return 0.1
        if self.state == "running":
            return 0.1 + 0.85 * self.progress
        return 1.0 if self.state == "done" else 0.0

    def status_text(self) -> Msg:
        """What the run is doing, for the panel."""
        if self.cancel_requested and not self.ended:
            return msg("fit.stage.cancelling-counted" if self.cancelled_running else "fit.stage.cancelling")
        if self.state == "uploading":
            share = int(100 * self._task.sent / self._task.total) if self._task and self._task.total else 0
            return msg("fit.stage.uploading", percent=share)
        if self.state == "waiting":
            return msg("fit.stage.busy")
        if self.state == "queued":
            return msg("fit.stage.queued")
        if self.state == "running":
            return msg(STAGE_TEXTS.get(self.stage or "", "fit.stage.running"))
        return msg("fit.stage.running")

    def cancel(self) -> None:
        """Stops the run: an upload stops between two chunks, and a job gta.clothing has is cancelled there (a job
        that has not started gives the day's fit back)."""
        if self.ended or self.cancel_requested:
            return
        self.cancel_requested = True
        self.cancelled_running = self.state == "running"
        if self.state == "uploading" and self._task is not None:
            self._task.cancel()  # the upload task ends; a job that came about anyway is cancelled when it does
        elif self.state == "waiting":
            self._end("cancelled", code="cancelled")
        elif self.job_id is not None:
            if self._task is not None:
                self._task.cancel()  # a status request in flight is dropped
            self._task = self.client.begin_cancel(self.job_id)
            self.state = "cancelling"

    def _end(self, state: str, code: Optional[str] = None, error: Optional[fit.FitError] = None,
             issues: Sequence[fit.FitIssue] = ()) -> None:
        self.state = state
        self.error = error
        self._task = None
        if state == "done":
            return
        code = code or (error.code if error is not None else "server_error")
        uploaded = bool(error is not None and (error.uploaded or self.job_id is not None))
        self.lines = failure_lines(code, issues or (error.errors if error is not None else ()),
                                   retry_after=error.retry_after if error is not None else None,
                                   refunded=self.refunded, uploaded=uploaded, started=self.cancelled_running)

    def tick(self, now: Optional[float] = None) -> bool:
        """Advances the run; True when something the panel shows changed."""
        now = self.clock() if now is None else now
        if self.ended:
            return False
        task = self._task
        if self.state == "uploading":
            if not task.poll():
                return True  # the upload share moves
            try:
                submitted = task.result()
            except fit.FitError as exc:
                if self.cancel_requested:
                    self._end("cancelled", code="cancelled")
                elif exc.code == "fit_busy":
                    self._busy(now, exc)
                else:
                    self._end("failed", error=exc)
                return True
            self.job_id = submitted.job_id
            self.remaining_today = submitted.remaining_today
            self.state = "queued"
            self._task = None
            self._next_poll = now + self.POLL_SECONDS
            if self.cancel_requested:  # the upload finished as Cancel was chosen: cancel the job it made
                self.cancel_requested = False
                self.cancel()
            return True
        if self.state == "waiting":
            if now >= self._retry_at:
                self.state = "uploading"
                self._task = self.client.begin_submit(self.request, self.mesh)
                return True
            return False
        if self.state == "cancelling":
            if not task.poll():
                return False
            try:
                task.result()
            except fit.FitError:
                pass  # the service no longer has the job, or could not be told: it ends on its own
            # One last look tells whether the day's fit came back.
            self._task = self.client.begin_status(self.job_id, self.mesh.vertex_count)
            self.state = "confirming"
            return True
        if self.state == "confirming":
            if not task.poll():
                return False
            try:
                answer = task.result()
                if isinstance(answer, fit.FitStatus):
                    self.refunded = answer.refunded
            except fit.FitError:
                pass  # unknown whether it came back: the fits left today will tell
            self._end("cancelled", code="cancelled")
            return True
        # queued or running: one status request a second
        if task is None:
            if now < self._next_poll:
                return False
            self._task = self.client.begin_status(self.job_id, self.mesh.vertex_count)
            return False
        if not task.poll():
            return False
        self._task = None
        self._next_poll = now + self.POLL_SECONDS
        try:
            answer = task.result()
        except fit.FitError as exc:
            if self.passing(exc) and self._poll_failures < self.MAX_POLL_FAILURES:
                self._poll_failures += 1
                wait = max(self.POLL_SECONDS * (1 + self._poll_failures), exc.retry_after or 0.0)
                self._next_poll = now + min(self.POLL_RETRY_LIMIT, wait)
                return False
            if self.passing(exc):
                # The job may still run on gta.clothing: cancel it there (one that has not started is not counted).
                self.abandoned = self.client.begin_cancel(self.job_id)
            self._end("failed", error=exc)
            return True
        self._poll_failures = 0
        if isinstance(answer, fit.FitResult):
            self.result = answer
            self.progress = 1.0
            self._end("done")
            return True
        self.stage = answer.stage
        self.progress = answer.progress
        self.queue_position = answer.queue_position
        if answer.state == "failed":
            self.refunded = answer.refunded
            self._end("failed", code=answer.failure_code or "server_error", issues=answer.errors)
        elif answer.state == "cancelled":
            self.refunded = answer.refunded
            self._end("cancelled", code="cancelled")
        else:
            self.state = answer.state
        return True

    @staticmethod
    def passing(error: fit.FitError) -> bool:
        """A status request failed in a way that may pass: the network, gta.clothing busy or rate limiting
        (``429``), or a server error (``5xx``)."""
        return error.code == "network" or error.status == 429 or error.status >= 500

    def _busy(self, now: float, error: fit.FitError) -> None:
        if self._busy_since is None:
            self._busy_since = now
        low, high = self.BUSY_WAIT
        wait = min(high, max(low, error.retry_after if error.retry_after is not None else 5.0))
        if now + wait - self._busy_since > self.BUSY_LIMIT_SECONDS:
            self._end("failed", error=error)  # the next try would come too late: say so now
            return
        self._retry_at = now + wait
        self.state = "waiting"
        self._task = None


# --------------------------------------------------------------------------------------------------
# The service
# --------------------------------------------------------------------------------------------------


class FitService:
    """The add-on's side of gta.clothing's garment fitting: the running :class:`FitRun`, the fits left today and the
    usual ranges of game clothing. ``client()`` gives a :class:`dct_link.fit.FitClient` for the signed-in account;
    ``ready()`` says whether gta.clothing may be asked now (online access on, signed in)."""

    #: How long the fits left today are shown before they are asked for again.
    ALLOWANCE_SECONDS = 120.0
    #: How long a failed reference is not asked for again.
    REFERENCE_RETRY_SECONDS = 60.0

    def __init__(self, client: Callable[[], fit.FitClient], ready: Callable[[], bool] = lambda: True,
                 clock: Callable[[], float] = time.monotonic) -> None:
        self._client = client
        self.ready = ready
        self.clock = clock
        self.run: Optional[FitRun] = None
        #: Called with a run that ended; True once the add-on dealt with it (False: try again at the next tick, for
        #: example while the user is in Edit Mode).
        self.on_ended: Optional[Callable[[FitRun], bool]] = None
        self.allowance: Optional[fit.FitAllowance] = None
        self._allowance_task: Optional[fit.FitTask] = None
        self._allowance_at: Optional[float] = None
        self._allowance_wanted = False
        self.references: Dict[Tuple[str, str, str], fit.FitReference] = {}
        self._reference_tasks: Dict[Tuple[str, str, str], fit.FitTask] = {}
        self._reference_failed: Dict[Tuple[str, str, str], float] = {}
        #: Runs cancelled when another file was opened, still being cancelled on gta.clothing.
        self._abandoned: List[FitRun] = []
        #: When gta.clothing last refused a fit for today (``quota_exceeded``): no fit starts before this (clock time),
        #: whatever the fits left today say.
        self.no_fits_until: Optional[float] = None

    @property
    def busy(self) -> bool:
        return self.run is not None and not self.run.handled

    def start(self, operation: str, request: Dict[str, Any], upload: Upload, key: Any) -> FitRun:
        if self.busy:
            raise UserError(msg("fit.why.running"))
        self.run = FitRun(self._client(), operation, request, upload, key, self.clock)
        return self.run

    def cancel(self) -> bool:
        run = self.run
        if run is None or run.ended or run.cancel_requested:
            return False
        run.cancel()
        return True

    def no_fits_left(self) -> Optional[float]:
        """Seconds until fits can start again when gta.clothing has none left today (the fits left today at zero, or
        a refusal for today), else ``None``."""
        now = self.clock()
        if self.no_fits_until is not None:
            if now < self.no_fits_until:
                return self.no_fits_until - now
            self.no_fits_until = None
        return None

    def want_allowance(self) -> None:
        """The panel shows the fits left today: ask for them when they are older than :attr:`ALLOWANCE_SECONDS`."""
        self._allowance_wanted = True

    def allowance_stale(self) -> None:
        self._allowance_at = None

    def reference(self, gender: str, category: str, body_version: str) -> Optional[fit.FitReference]:
        """The usual ranges of ``category``, or ``None`` while they are asked for (or cannot be had)."""
        key = (gender, category, body_version)
        found = self.references.get(key)
        if found is not None or key in self._reference_tasks:
            return found
        failed = self._reference_failed.get(key)
        if failed is not None and self.clock() - failed < self.REFERENCE_RETRY_SECONDS:
            return None
        if self.ready():
            try:
                self._reference_tasks[key] = self._client().begin_reference(gender, category, body_version)
            except ValueError:
                self._reference_failed[key] = self.clock()
        return None

    def reference_pending(self, gender: str, category: str, body_version: str) -> bool:
        return (gender, category, body_version) in self._reference_tasks

    def forget(self) -> None:
        """Another file is opened: a running fit is cancelled (on gta.clothing too) and its result never applied."""
        run = self.run
        if run is not None and not run.ended:
            run.cancel()
            self._abandoned.append(run)
        self.run = None

    def tick(self, now: Optional[float] = None) -> bool:
        """Advances the run and the background requests; True when the panel should be drawn again."""
        now = self.clock() if now is None else now
        changed = False
        for run in list(self._abandoned):
            run.tick(now)
            if run.ended:
                self._abandoned.remove(run)
        run = self.run
        if run is not None and not run.handled:
            changed |= run.tick(now)
            if run.remaining_today is not None and self.allowance is not None:
                self.allowance = self.allowance._replace(remaining_today=run.remaining_today,
                                                         used_today=self.allowance.per_day - run.remaining_today)
                run.remaining_today = None
                changed = True
            if run.ended and (self.on_ended is None or self.on_ended(run)):
                run.handled = True
                self._allowance_at = None  # a refund or a used fit: look again
                if run.error is not None and run.error.code == "quota_exceeded":
                    self.no_fits_until = now + (run.error.retry_after if run.error.retry_after else 3600.0)
                changed = True
        changed |= self._tick_allowance(now)
        for key, task in list(self._reference_tasks.items()):
            if task.poll():
                del self._reference_tasks[key]
                try:
                    self.references[key] = task.result()
                except (fit.FitError, ValueError):
                    self._reference_failed[key] = now
                changed = True
        return changed

    def _tick_allowance(self, now: float) -> bool:
        task = self._allowance_task
        if task is not None:
            if not task.poll():
                return False
            self._allowance_task = None
            self._allowance_at = now
            try:
                self.allowance = task.result()
            except fit.FitError as exc:
                if exc.code in ("signed-out", "session_invalid", "session_expired", "session_revoked"):
                    self.allowance = None
            return True
        if not self._allowance_wanted:
            return False
        self._allowance_wanted = False
        if self._allowance_at is not None and now - self._allowance_at < self.ALLOWANCE_SECONDS:
            return False
        if not self.ready():
            return False
        self._allowance_task = self._client().begin_allowance()
        self._allowance_at = now
        return False
