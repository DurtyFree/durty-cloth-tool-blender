# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2026 Schmid Software Solutions (https://schmid-software.de)
"""Custom Ped's part of the link to Durty Cloth Tool: the template list (``ped.templates``), the rig (``ped.rig`` with
its progress, Cancel and result) and sending the rigged character (``ped.add``: the GLB in chunks, Cancel and Durty
Cloth Tool's answer).

The link controller's timer drives the session, so the callbacks here run on Blender's main thread; they only keep
what arrived and mark the panels for a redraw. Applying a rig to the character is the Blender side's
(:mod:`ped_host`), on the user's click. Texts are :class:`strings.Msg` values. Nothing here imports Blender.
"""

from __future__ import annotations

import time
import traceback
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from . import garment_add, ped, settings
from .dct_link.session import PedAddResult, PedRefusal, PedRigRefusal, PedTemplates, Request
from .link import Notice
from .strings import EN, Msg, UserError, msg

#: The Creator Link features of the custom ped flow: the template list (every plan), the rig (Ultimate) and creating
#: the custom ped project (Advanced or Ultimate).
FEATURE_TEMPLATES = "dct.link.pedTemplates"
FEATURE_RIG = "dct.link.pedRig"
FEATURE_ADD = "dct.link.pedAdd"


def feature_problem(state: Optional[str], feature: str) -> Optional[Msg]:
    """Why a custom ped feature is not available with this plan, or ``None``: the plan it needs, in words."""
    if state is None or state == "entitled":
        return None
    if feature == FEATURE_RIG:
        return msg("ped.plan.rig")
    if feature == FEATURE_ADD:
        return msg("ped.plan.add")
    return settings.describe_feature(state)


#: Durty Cloth Tool's answers to a rig that the panel explains in their own words.
RIG_KEYS = {
    "needs-license": "ped.plan.rig",
    "needs-ultimate": "ped.plan.rig",
    "busy": "ped.error.rig-busy",
    "cancelled": "ped.error.rig-cancelled",
    "rig-refused": "ped.error.rig-refused",
    "unknown-message-type": "ped.error.dct-too-old",
    "disconnected": "ped.error.rig-disconnected",
    "timeout": "ped.error.rig-timeout",
}
#: Durty Cloth Tool's answers to a ped.add that the panel explains in their own words.
ADD_KEYS = {
    "needs-license": "ped.plan.add",
    "needs-ultimate": "ped.plan.add",
    "busy": "ped.error.add-busy",
    "rate-limited": "ped.error.add-busy",
    "request-denied": "ped.error.add-denied",
    "model-rejected": "ped.error.model-rejected",
    "upload-incomplete": "error.upload-incomplete",
    "save-failed": "ped.error.save-failed",
    "unknown-message-type": "ped.error.dct-too-old",
    "disconnected": "ped.error.add-disconnected",
    "timeout": "ped.error.add-timeout",
    "cancelled": "ped.error.add-unanswered",
}
#: The level each answer is shown with (everything else is an error).
LEVELS = {"cancelled": "INFO", "request-denied": "INFO", "busy": "WARNING", "rate-limited": "WARNING",
          "needs-license": "WARNING", "needs-ultimate": "WARNING", "disconnected": "WARNING", "timeout": "WARNING"}


def describe(code: Optional[str], keys: Mapping[str, str]) -> Notice:
    """``(level, message)`` for a code Durty Cloth Tool answered (or dct_link's own, such as ``disconnected``)."""
    key = keys.get(code or "")
    level = LEVELS.get(code or "", "ERROR")
    if key is not None:
        return Notice(level, msg(key))
    return Notice(level, settings.describe_error(code))


#: Findings of a ped.add that the panel explains; the texture codes are the add's (``garment_add``).
FINDING_KEYS = ("rig-mismatch", "ped-budget", "ped-ragdoll-mismatch", "ped-rest-strain")


def finding_text(code: str) -> Msg:
    if code in FINDING_KEYS:
        return msg(f"ped.finding.{code}")
    return garment_add.finding_text(code)


class PedLink:
    """The custom ped requests of one link controller and what came back, for the panels."""

    #: How long a rig may take, and how long Durty Cloth Tool may ask its user about an add, before they are withdrawn
    #: (seconds).
    RIG_TIMEOUT = 600.0
    ADD_TIMEOUT = 900.0

    def __init__(self, controller: Any) -> None:
        self.controller = controller
        # The template list.
        self.templates: Optional[List[Dict[str, Any]]] = None
        self.templates_for: Optional[Tuple[Optional[str], bool]] = None
        self.truncated = False
        self.templates_request: Optional[Request] = None
        self.templates_problem: Optional[Notice] = None
        # The rig.
        self.rig_request: Optional[Request] = None
        self.stage: Optional[str] = None
        self.fraction = 0.0
        self.job: Optional[str] = None
        #: The rig waiting for the user to apply it (a dct_link ``PedRig``), and what was sent for it.
        self.rig: Optional[Any] = None
        self.rig_sent: Optional[Dict[str, Any]] = None
        self.rig_status: Optional[Notice] = None
        #: Why Durty Cloth Tool refused the last rig, line by line (:class:`ped.ReportLine`).
        self.refusal: List[ped.ReportLine] = []
        # Sending.
        self.add_request: Optional[Request] = None
        self.add_sent: Optional[Dict[str, Any]] = None
        self.add_status: Optional[Notice] = None
        self.findings: List[Dict[str, str]] = []
        #: The project Durty Cloth Tool created from the last add (``name``, ``model``, ``template``) and the character
        #: it was made from; ``on_created`` hears of it (Blender keeps it on the character).
        self.created: Optional[Dict[str, str]] = None
        self.on_created: Optional[Any] = None

    # ---- state ---------------------------------------------------------------------------------------

    @property
    def rigging(self) -> bool:
        return self.rig_request is not None and not self.rig_request.done

    @property
    def sending(self) -> bool:
        return self.add_request is not None and not self.add_request.done

    @property
    def busy(self) -> bool:
        """A rig or an add is under way (the link polls faster meanwhile)."""
        return self.rigging or self.sending

    def feature(self, feature: str) -> Optional[Msg]:
        """Why ``feature`` cannot be used now: the connection, or the plan it needs."""
        ctrl = self.controller
        if not ctrl.ready or ctrl.session is None:
            return msg("ped.why.connect")
        return feature_problem(ctrl.session.features.get(feature), feature)

    def _session(self, feature: str) -> Any:
        session = self.controller.ready_session()
        problem = self.feature(feature)
        if problem is not None:
            raise UserError(problem)
        return session

    # ---- templates -----------------------------------------------------------------------------------

    @property
    def loading_templates(self) -> bool:
        return self.templates_request is not None and not self.templates_request.done

    def fetch_templates(self, gender: Optional[str], show_all: bool) -> None:
        """Asks Durty Cloth Tool for the templates of ``gender`` (``None``: both); ``show_all`` adds freemode, player,
        cutscene and story peds. Raises :class:`strings.UserError` when it cannot ask now."""
        if self.loading_templates:
            return
        session = self._session(FEATURE_TEMPLATES)
        key = (gender, bool(show_all))
        self.templates_problem = None
        request = session.list_ped_templates(gender, bool(show_all))
        self.templates_request = request
        request.add_done_callback(lambda done: self._on_templates(done, key))
        self.controller.touch()

    def _on_templates(self, request: Request, key: Tuple[Optional[str], bool]) -> None:
        if request is not self.templates_request:
            return
        self.templates_request = None
        if request.error is not None:
            code = request.error.code
            self.controller._remember_error(code)
            self.templates_problem = describe(code, {"unknown-message-type": "ped.error.dct-too-old"})
        else:
            result = request.result()
            if isinstance(result, PedRefusal) or not getattr(result, "ok", False):
                self.controller._remember_error(result.code)
                self.templates_problem = describe(result.code, {"unknown-message-type": "ped.error.dct-too-old"})
            elif isinstance(result, PedTemplates):
                self.templates = list(result.templates)
                self.truncated = bool(result.truncated)
                self.templates_for = key
        self.controller.touch()

    def template(self, model: str) -> Optional[Dict[str, Any]]:
        """The listed template of this model name (ignoring case), or ``None``."""
        for entry in self.templates or ():
            if str(entry.get("model", "")).lower() == model.lower():
                return entry
        return None

    # ---- the rig -------------------------------------------------------------------------------------

    def rig_problem(self) -> Optional[Msg]:
        """Why a rig cannot start now, or ``None``."""
        if self.rigging:
            return msg("ped.why.rigging")
        return self.feature(FEATURE_RIG)

    def start_rig(self, template: str, markers: Mapping[str, Any], data: ped.RigInput, options: Mapping[str, Any], *,
                  rights: bool, character: str) -> Request:
        """Sends the character to be rigged from ``template``. Raises :class:`strings.UserError` when it cannot be
        sent, with what to do."""
        problem = self.rig_problem()
        if problem is not None:
            raise UserError(problem)
        session = self._session(FEATURE_RIG)
        sent_markers = ped.tuples(markers)
        try:
            request = session.rig_ped(template, sent_markers, data.positions, data.triangles, rights_confirmed=rights,
                                      parts=data.roles or None, part_ids=data.part_ids, options=dict(options),
                                      on_accepted=self._on_accepted, on_progress=self._on_progress,
                                      timeout=self.RIG_TIMEOUT)
        except ValueError as exc:
            raise UserError(msg("ped.invalid", detail=str(exc))) from exc
        self.rig_request = request
        self.rig = None
        self.refusal = []
        self.stage, self.fraction, self.job = None, 0.0, None
        self.rig_sent = {"template": template, "markers": sent_markers, "topology": data.topology,
                         "ranges": list(data.ranges), "options": dict(options), "character": character,
                         "time": time.time()}
        self.rig_status = Notice("INFO", msg("ped.rig.waiting"))
        request.add_done_callback(self._on_rig)
        self.controller.touch()
        return request

    def cancel_rig(self) -> bool:
        request = self.rig_request
        if request is None or request.done:
            return False
        sent = bool(request.cancel())  # type: ignore[attr-defined]
        if sent:
            self.rig_status = Notice("INFO", msg("ped.rig.cancelling"))
            self.controller.touch()
        return sent

    def _on_accepted(self, job: str) -> None:
        self.job = job
        self.rig_status = None
        self.controller.touch()

    def _on_progress(self, stage: str, fraction: float) -> None:
        self.stage, self.fraction = stage, max(0.0, min(1.0, float(fraction)))
        self.rig_status = None
        self.controller.touch()

    def _on_rig(self, request: Request) -> None:
        if request is not self.rig_request:
            return
        self.stage = None
        if request.error is not None:
            code = request.error.code
            self.controller._remember_error(code)
            withdrawn = bool(getattr(request, "withdrawn", False))
            self.rig_status = describe("cancelled" if withdrawn and code in ("cancelled", "timeout") else code,
                                       RIG_KEYS)
        else:
            result = request.result()
            if isinstance(result, PedRigRefusal) or not getattr(result, "ok", False):
                self.controller._remember_error(result.code)
                self.rig_status = describe(result.code, RIG_KEYS)
                self.refusal = ped.refusal_lines(getattr(result, "reasons", None) or [])
            else:
                self.rig = result
                self.job = result.job
                self.rig_status = None
        self.controller.touch()

    def take_rig(self) -> Tuple[Any, Dict[str, Any]]:
        """The rig waiting to be applied and what was sent for it; it is no longer waiting afterwards."""
        if self.rig is None or self.rig_sent is None:
            raise UserError(msg("ped.why.no-result"))
        rig, sent = self.rig, self.rig_sent
        self.rig = None
        self.controller.touch()
        return rig, sent

    def discard_rig(self) -> None:
        self.rig = None
        self.refusal = []
        self.rig_status = None
        self.controller.touch()

    # ---- sending -------------------------------------------------------------------------------------

    def add_problem(self) -> Optional[Msg]:
        """Why the character cannot be sent now, or ``None``."""
        if self.sending:
            return msg("ped.why.sending")
        return self.feature(FEATURE_ADD)

    def start_add(self, template: str, name: str, model: str, glb: Any, *, rights: bool, rig: Optional[str],
                  ragdoll: Optional[str], parts: Sequence[Tuple[str, str]], character: str) -> Request:
        """Sends the character's GLB to Durty Cloth Tool, which creates a custom ped project from it once its user
        confirms there. Raises :class:`strings.UserError` when it cannot be sent, with what to do."""
        problem = self.add_problem()
        if problem is not None:
            raise UserError(problem)
        session = self._session(FEATURE_ADD)
        try:
            request = session.add_ped(template, name, model, glb, rights_confirmed=rights, rig=rig, ragdoll=ragdoll,
                                      parts=list(parts) or None, timeout=self.ADD_TIMEOUT)
        except ValueError as exc:
            raise UserError(msg("ped.invalid", detail=str(exc))) from exc
        size = len(memoryview(glb).cast("B"))
        self.add_request = request
        self.add_sent = {"template": template, "name": name, "model": model, "character": character, "size": size}
        self.findings = []
        self.created = None
        self.add_status = Notice("INFO", msg("ped.send.waiting", size=f"{size / (1024 * 1024):.1f}"))
        request.add_done_callback(self._on_add)
        self.controller.touch()
        return request

    def cancel_add(self) -> bool:
        request = self.add_request
        if request is None or request.done:
            return False
        sent = bool(request.cancel())  # type: ignore[attr-defined]
        if sent:
            self.add_status = Notice("INFO", msg("ped.send.withdrawing"))
            self.controller.touch()
        return sent

    def _on_add(self, request: Request) -> None:
        if request is not self.add_request:
            return
        withdrawn = bool(getattr(request, "withdrawn", False))
        if request.error is not None:
            code = request.error.code
            self.controller._remember_error(code)
            self.add_status = describe(code, ADD_KEYS)
            self.findings = []
        else:
            result: PedAddResult = request.result()
            self.findings = garment_add.sorted_findings(result.findings)
            if result.ok and result.project is not None:
                self.created = dict(result.project, character=(self.add_sent or {}).get("character", ""))
                if self.on_created is not None:
                    try:
                        self.on_created(dict(self.created))
                    except Exception:  # noqa: BLE001 - the project exists; only Blender's note of it failed
                        traceback.print_exc()
                self.add_status = Notice("INFO", msg("ped.send.created", name=result.project.get("name", ""),
                                                     model=result.project.get("model", ""),
                                                     template=result.project.get("template", "")))
            else:
                self.controller._remember_error(result.code)
                if result.code == "request-denied" and withdrawn:
                    self.add_status = Notice("INFO", msg("ped.send.withdrawn"))
                else:
                    self.add_status = describe(result.code, ADD_KEYS)
        self.controller.touch()

    # ---- another file --------------------------------------------------------------------------------

    def forget(self) -> None:
        """Another file was opened: a waiting rig and the outcomes shown belong to the old one. A running rig or add is
        withdrawn."""
        if self.rigging:
            self.cancel_rig()
        if self.sending:
            self.cancel_add()
        self.rig = None
        self.rig_sent = None
        self.rig_status = None
        self.refusal = []
        self.add_status = None
        self.findings = []
        self.created = None
        self.controller.touch()


def stage_text(stage: Optional[str]) -> Msg:
    """A rig stage in words."""
    return msg(f"ped.stage.{stage}") if stage and f"ped.stage.{stage}" in EN else msg("ped.rig.working")


__all__ = ["FEATURE_ADD", "FEATURE_RIG", "FEATURE_TEMPLATES", "Notice", "PedLink", "describe", "feature_problem",
           "finding_text", "stage_text"]
