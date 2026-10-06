# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2026 Schmid Software Solutions (https://schmid-software.de)
"""Custom Ped (Experimental) in the DCT tab: turning your own character into a custom ped, in five stages.

The panel shows when the DCT tab's Work On is Custom Ped (the other views then hide). Its first line names the next
step, and below it each stage is a section that opens when it is the next one and folds to its header (with a check
mark) once done: Character (the meshes, their checks with a fix each, the part roles), Markers (the click guide, Auto
Markers, markers from an old rig, mirror), Rig (the template, the rights notice, the rig in Durty Cloth Tool with its
progress, the refined markers to approve, the report), Check (test poses and the local checks) and Create (name, model
name and the custom ped project Durty Cloth Tool creates). Only the next step's button is large; rarely used settings
sit in closed Options sections. Every change to the character can be undone.
"""

from __future__ import annotations

import json
import math
import shutil
import time
import traceback
from typing import Any, Callable, Dict, List, Optional, Tuple

import bpy
import numpy as np
from bpy.app.handlers import persistent
from bpy.props import BoolProperty, EnumProperty, FloatProperty, PointerProperty, StringProperty
from bpy.types import Menu, Operator, Panel, PropertyGroup

from . import host, ped, ped_link, state, strings, ui
from . import ped_host as ph
from .dct_link import auth, protocol
from .strings import CONTEXT, EN, Msg, UserError, msg, t, tt
from .ui import GAP, GAP_SMALL, guide, heading, info_button, operator, primary, reason_text, subtext, wrapped

LEVEL_ICONS = {"ok": "CHECKMARK", "warning": "ERROR", "error": "CANCEL", "INFO": "INFO", "WARNING": "ERROR",
               "ERROR": "CANCEL"}
#: Failures an operator reports instead of raising.
EXPECTED = (UserError, ped.MarkerError, ValueError, OSError, RuntimeError, auth.AuthError)


class _Runtime:
    """What the panel shows that is not saved: the last result, the cached facts, the auto marker notes, the local
    checks' findings, the markers last seen (for the elbow and knee that follow), and the click guide."""

    def __init__(self) -> None:
        self.notice: Optional[Tuple[str, Msg]] = None
        self.facts: Dict[str, Tuple[tuple, ped.Facts]] = {}
        self.marker_notes: Dict[str, Tuple[str, ...]] = {}
        self.findings: Dict[str, List[ped.Finding]] = {}
        self.last_markers: Dict[str, Dict[str, Tuple[float, float, float]]] = {}
        self.writing = False
        self.guide: Optional[Any] = None
        #: When the facts were last read (they are read at most once a second, never during a transform), and the
        #: flow of the panel being drawn (computed once per draw).
        self.facts_at = 0.0
        self.flow: Optional[ped.Flow] = None


RUNTIME = _Runtime()


def notify(level: str, message: Msg) -> None:
    RUNTIME.notice = (level, message)


def props(context: Any) -> Any:
    return context.scene.dct_ped


def character(context: Any) -> Optional[Any]:
    collection = getattr(getattr(context, "scene", None), "dct_ped", None)
    collection = getattr(collection, "character", None) if collection is not None else None
    try:
        return collection if collection is not None and collection.name else None
    except ReferenceError:
        return None


def ident(collection: Optional[Any]) -> str:
    return str(collection.get(ph.CHARACTER, "")) if collection is not None else ""


def controller() -> Optional[Any]:
    return state.controller


def peds() -> Optional[ped_link.PedLink]:
    ctrl = state.controller
    return getattr(ctrl, "peds", None) if ctrl is not None else None


#: The facts of a character that keeps changing (a part being dragged) are read again at most this often (seconds).
FACTS_INTERVAL = 1.0


def _redraw_later() -> None:
    host.redraw()
    return None


def facts(context: Any, collection: Optional[Any]) -> ped.Facts:
    """The character's facts, read again when its objects changed: right away after a pause, at most once a second
    while they keep changing, and never during a transform (the panel shows the last facts and catches up after)."""
    if collection is None:
        return ped.Facts()
    key = ph.facts_key(collection)
    cached = RUNTIME.facts.get(ident(collection))
    if cached is not None and cached[0] == key:
        return cached[1]
    now = time.monotonic()
    if cached is not None and (now - RUNTIME.facts_at < FACTS_INTERVAL or host.modal_operator_running()):
        if not bpy.app.timers.is_registered(_redraw_later):
            bpy.app.timers.register(_redraw_later, first_interval=FACTS_INTERVAL)
        return cached[1]
    found = ph.facts(context, collection)
    RUNTIME.facts[ident(collection)] = (key, found)
    RUNTIME.facts_at = time.monotonic()
    return found


def character_checks(context: Any, collection: Optional[Any]) -> List[ped.Check]:
    return ped.checks(facts(context, collection), facing_confirmed=bool(collection is not None
                                                                        and collection.get(ph.FACING)))


def rigged(collection: Optional[Any]) -> bool:
    return ph.armature(collection) is not None


def waiting_rig(collection: Optional[Any]) -> Optional[Any]:
    """The rig Durty Cloth Tool sent for this character that waits to be applied."""
    link = peds()
    if link is None or link.rig is None or link.rig_sent is None or collection is None:
        return None
    return link.rig if link.rig_sent.get("character") == ident(collection) else None


def flow(context: Any) -> ped.Flow:
    if RUNTIME.flow is not None:
        return RUNTIME.flow  # the panel being drawn computed it already
    collection = character(context)
    ctrl = controller()
    link = peds()
    markers = ph.read_markers(collection)
    sent = collection.get(ph.SENT) if collection is not None else None
    return ped.Flow(
        character=collection is not None and bool(ph.parts(collection)),
        checks_ok=ped.checks_pass(character_checks(context, collection)) if collection is not None else False,
        markers=len(markers),
        marker_problems=bool(ped.marker_problems(markers)) if len(markers) == len(ped.BODY_MARKERS) else False,
        connected=ctrl is not None and ctrl.ready,
        template=bool(props(context).template),
        rigging=link is not None and link.rigging and (link.rig_sent or {}).get("character") == ident(collection),
        result=waiting_rig(collection) is not None,
        rigged=rigged(collection),
        checked=bool(collection is not None and collection.get(ph.CHECKED)),
        sending=link is not None and link.sending and (link.add_sent or {}).get("character") == ident(collection),
        sent=bool(sent),
    )


def sent_project(collection: Optional[Any]) -> Dict[str, str]:
    """The project Durty Cloth Tool created from the character (``name``, ``model``, ``template``), or nothing."""
    try:
        sent = json.loads(collection.get(ph.SENT, "") or "{}") if collection is not None else {}
    except ValueError:
        return {}
    return sent if isinstance(sent, dict) else {}


def next_operator(context: Any) -> Optional[str]:
    return ped.STEP_OPERATORS.get(ped.next_step(flow(context)))


def step(layout: Any, context: Any, idname: str, key: str, icon: str = "NONE", **properties: Any) -> Any:
    """A tool's button: the large one when it is the next step."""
    if next_operator(context) == idname:
        return primary(layout, idname, key, icon, **properties)
    return operator(layout, idname, key, icon, **properties)


def advance(context: Any) -> None:
    """Opens the section of the next step and folds the finished ones before it."""
    settings_ = props(context)
    current = ped.stage_of(ped.next_step(flow(context)))
    index = ped.STAGES.index(current)
    for position, stage in enumerate(ped.STAGES):
        if position == index:
            setattr(settings_, f"open_{stage}", True)
        elif position < index:
            setattr(settings_, f"open_{stage}", False)
    host.redraw()


def options_section(layout: Any, name: str) -> Optional[Any]:
    header, body = layout.panel(f"dct_link_ped_{name}", default_closed=True)
    header.label(text=t("garment.heading.options"), icon="PREFERENCES", translate=False)
    return body


def show_button(layout: Any, idname: str, **properties: Any) -> None:
    """A small Show button at the right, under the text it belongs to (beside it, the text would be squeezed)."""
    row = layout.row()
    row.alignment = "RIGHT"
    operator(row, idname, "ped.op.show", "RESTRICT_SELECT_OFF", **properties)


def labelled(layout: Any, data: Any, name: str, key: str) -> None:
    row = layout.row(align=True)
    split = row.split(factor=0.4, align=True)
    split.label(text=t(key), translate=False)
    split.prop(data, name, text="")


def marker_names(names: Any) -> str:
    return ", ".join(t(f"ped.marker.{name}") for name in names if f"ped.marker.{name}" in EN)


# --------------------------------------------------------------------------------------------------
# Settings
# --------------------------------------------------------------------------------------------------


def _items(prefix: str, ids: Tuple[str, ...]) -> tuple:
    return tuple((value, EN[f"{prefix}.{value}"], EN[f"{prefix}.{value}.desc"]) for value in ids)


ROLE_ITEMS = tuple([("auto", EN["ped.role.auto"], EN["ped.role.auto.desc"])]
                   + [(role, EN[f"ped.role.{role}"], EN[f"ped.role.{role}.desc"]) for role in ped.ROLES])


def _marker_size_changed(self: Any, context: Any) -> None:
    ph.resize_markers(character(context), self.marker_size)


def _filter_changed(self: Any, context: Any) -> None:
    link = peds()
    ctrl = controller()
    if link is not None and ctrl is not None and ctrl.ready:
        try:
            link.fetch_templates(None if self.gender == "any" else self.gender, self.show_all)
        except UserError:
            pass  # the Rig section says why


def _template_filters(settings_: Any) -> Tuple[Optional[str], bool]:
    return None if settings_.gender == "any" else settings_.gender, bool(settings_.show_all)


def _auto_templates() -> Optional[float]:
    """Asks Durty Cloth Tool for the template list by itself while the Rig stage shows it (a timer, because drawing a
    panel never sends anything); see :meth:`ped_link.PedLink.auto_templates`."""
    link = peds()
    settings_ = getattr(getattr(bpy.context, "scene", None), "dct_ped", None)
    if link is None or settings_ is None:
        return None
    try:
        return link.auto_templates(*_template_filters(settings_))
    except Exception:  # noqa: BLE001 - Blender drops a timer that raises; Refresh still asks
        traceback.print_exc()
        return None


def _character_changed(self: Any, context: Any) -> None:
    RUNTIME.notice = None
    collection = self.character
    if collection is not None and not self.ped_name:
        self.ped_name = collection.name


class DCTLINK_PG_ped(PropertyGroup):
    character: PointerProperty(name=EN["ped.prop.character"], type=bpy.types.Collection,
                               description=EN["ped.prop.character.desc"], update=_character_changed,
                               translation_context=CONTEXT)
    template: StringProperty(name=EN["ped.prop.template"], description=EN["ped.prop.template.desc"],
                             translation_context=CONTEXT)
    gender: EnumProperty(name=EN["ped.prop.gender"], items=(("any", EN["ped.gender.any"], EN["ped.gender.any.desc"]),
                                                             ("male", EN["gender.male"], EN["ped.gender.male.desc"]),
                                                             ("female", EN["gender.female"],
                                                              EN["ped.gender.female.desc"])),
                         default="any", update=_filter_changed, translation_context=CONTEXT)
    show_all: BoolProperty(name=EN["ped.prop.show-all"], description=EN["ped.prop.show-all.desc"], default=False,
                           update=_filter_changed, translation_context=CONTEXT)
    marker_size: FloatProperty(name=EN["ped.prop.marker-size"], description=EN["ped.prop.marker-size.desc"],
                               default=0.03, min=0.005, max=0.2, unit="LENGTH", update=_marker_size_changed,
                               translation_context=CONTEXT)
    follow: BoolProperty(name=EN["ped.prop.follow"], description=EN["ped.prop.follow.desc"], default=True,
                         translation_context=CONTEXT)
    refine: BoolProperty(name=EN["ped.prop.refine"], description=EN["ped.prop.refine.desc"], default=True,
                         translation_context=CONTEXT)
    fingers: EnumProperty(name=EN["ped.prop.fingers"], items=_items("ped.fingers", protocol.PED_DETAIL_MODES),
                          default="off", translation_context=CONTEXT)
    face: EnumProperty(name=EN["ped.prop.face"], items=_items("ped.face", protocol.PED_DETAIL_MODES), default="off",
                       translation_context=CONTEXT)
    roll_bones: BoolProperty(name=EN["ped.prop.roll"], description=EN["ped.prop.roll.desc"], default=True,
                             translation_context=CONTEXT)
    helper_bones: BoolProperty(name=EN["ped.prop.helpers"], description=EN["ped.prop.helpers.desc"], default=True,
                               translation_context=CONTEXT)
    rest_model: EnumProperty(name=EN["ped.prop.rest"], items=_items("ped.rest", protocol.PED_REST_MODELS),
                             default="volume", translation_context=CONTEXT)
    ped_name: StringProperty(name=EN["ped.prop.name"], description=EN["ped.prop.name.desc"], maxlen=128,
                             translation_context=CONTEXT)
    model_name: StringProperty(name=EN["ped.prop.model"], description=EN["ped.prop.model.desc"], maxlen=32,
                               translation_context=CONTEXT)
    ragdoll: EnumProperty(name=EN["ped.prop.ragdoll"], items=_items("ped.ragdoll", ("template",) + ped.RAGDOLLS),
                          default="template", translation_context=CONTEXT)
    open_character: BoolProperty(default=True, options={"SKIP_SAVE"})
    open_markers: BoolProperty(default=False, options={"SKIP_SAVE"})
    open_rig: BoolProperty(default=False, options={"SKIP_SAVE"})
    open_check: BoolProperty(default=False, options={"SKIP_SAVE"})
    open_send: BoolProperty(default=False, options={"SKIP_SAVE"})


# --------------------------------------------------------------------------------------------------
# Operators
# --------------------------------------------------------------------------------------------------


def _refuse(cls: Any, reason: Optional[Msg]) -> bool:
    if reason is None:
        return True
    cls.poll_message_set(strings.tip(reason))
    return False


def _failure(exc: BaseException) -> Msg:
    if isinstance(exc, ped.MarkerError):
        return msg(f"ped.marker-error.{exc.code}")
    if isinstance(exc, UserError):
        return exc.message
    if isinstance(exc, OSError):
        return msg("notice.file-error", detail=str(exc.strerror or exc))
    return msg("notice.unexpected", detail=ui._report_text(exc))


def _character_reason(context: Any) -> Optional[Msg]:
    if state.controller is None:
        return msg("notice.not-ready")
    collection = character(context)
    if collection is None or not ph.parts(collection):
        return msg("ped.why.no-character")
    if context.mode not in ("OBJECT", "POSE"):
        return msg("ped.why.object-mode")
    return None


def _unrigged_reason(context: Any) -> Optional[Msg]:
    reason = _character_reason(context)
    if reason is None and rigged(character(context)):
        return msg("ped.why.rigged")
    return reason


def _placed_reason(context: Any) -> Optional[Msg]:
    """Why the character cannot be scaled, turned or moved now: a part still has a transform of its own (applied
    first, every part moves exactly once)."""
    reason = _unrigged_reason(context)
    if reason is None and facts(context, character(context)).transformed:
        return msg("ped.why.transforms-first")
    return reason


def _confirm(op: Operator, context: Any, event: Any, key: str, **fields: Any) -> set:
    """Asks before a change to the character's size, direction or data."""
    try:
        return context.window_manager.invoke_confirm(op, event, message=t(key, **fields), translate=False)
    except TypeError:  # an older Blender without a message
        return context.window_manager.invoke_confirm(op, event)


class _Op(Operator):
    bl_translation_context = CONTEXT


class _CharacterOp(_Op):
    """An operator that changes the character: it can be undone and reports failures instead of raising them."""

    bl_options = {"REGISTER", "UNDO"}

    def run(self, context: Any, action: Callable[[], Optional[Any]]) -> set:
        try:
            message = action()
        except EXPECTED as exc:
            if not isinstance(exc, (UserError, ped.MarkerError)):
                traceback.print_exc()
            failure = _failure(exc)
            self.report({"ERROR"}, strings.text(failure))
            notify("ERROR", failure)
            host.redraw()
            return {"CANCELLED"}
        level = "INFO"
        if isinstance(message, tuple) and not isinstance(message, Msg):
            level, message = message
        if message is not None:
            self.report({level}, strings.text(message))
            notify(level, message)
        RUNTIME.facts.pop(ident(character(context)), None)
        advance(context)
        return {"FINISHED"}


class DCTLINK_OT_ped_use_selected(_CharacterOp):
    bl_idname = "dct_link.ped_use_selected"
    bl_label = EN["ped.op.use-selected"]
    bl_description = EN["ped.op.use-selected.desc"]

    @classmethod
    def poll(cls, context):
        if state.controller is None:
            return _refuse(cls, msg("notice.not-ready"))
        if not any(obj.type == "MESH" for obj in context.selected_objects):
            return _refuse(cls, msg("ped.why.select-meshes"))
        return _refuse(cls, None if context.mode == "OBJECT" else msg("ped.why.object-mode"))

    def execute(self, context):
        def action():
            collection = ph.use_selected(context)
            settings_ = props(context)
            settings_.character = collection
            if not settings_.ped_name:
                settings_.ped_name = collection.name
            if not settings_.model_name:
                settings_.model_name = ped.suggest_model(collection.name)
            RUNTIME.last_markers.pop(ident(collection), None)
            return msg("ped.done.use-selected", name=collection.name, count=len(ph.parts(collection)))

        return self.run(context, action)


class DCTLINK_OT_ped_apply_transforms(_CharacterOp):
    bl_idname = "dct_link.ped_apply_transforms"
    bl_label = EN["ped.op.apply-transforms"]
    bl_description = EN["ped.op.apply-transforms.desc"]

    @classmethod
    def poll(cls, context):
        return _refuse(cls, _unrigged_reason(context))

    def execute(self, context):
        return self.run(context, lambda: msg("ped.done.transforms", count=ph.apply_transforms(ph.parts(character(context)))))


class DCTLINK_OT_ped_apply_modifiers(_CharacterOp):
    bl_idname = "dct_link.ped_apply_modifiers"
    bl_label = EN["ped.op.apply-modifiers"]
    bl_description = EN["ped.op.apply-modifiers.desc"]

    @classmethod
    def poll(cls, context):
        return _refuse(cls, _unrigged_reason(context))

    def invoke(self, context, event):
        return _confirm(self, context, event, "ped.confirm.modifiers")

    def execute(self, context):
        return self.run(context, lambda: msg("ped.done.modifiers",
                                             count=ph.apply_modifiers(context, ph.parts(character(context)))))


class DCTLINK_OT_ped_remove_old_rig(_CharacterOp):
    bl_idname = "dct_link.ped_remove_old_rig"
    bl_label = EN["ped.op.remove-old-rig"]
    bl_description = EN["ped.op.remove-old-rig.desc"]

    @classmethod
    def poll(cls, context):
        return _refuse(cls, _unrigged_reason(context))

    def invoke(self, context, event):
        return _confirm(self, context, event, "ped.confirm.old-rig")

    def execute(self, context):
        def action():
            names = ph.remove_old_rig(context, character(context))
            return msg("ped.done.old-rig", name=", ".join(names)) if names else None

        return self.run(context, action)


class DCTLINK_OT_ped_remove_shape_keys(_CharacterOp):
    bl_idname = "dct_link.ped_remove_shape_keys"
    bl_label = EN["ped.op.remove-shape-keys"]
    bl_description = EN["ped.op.remove-shape-keys.desc"]

    @classmethod
    def poll(cls, context):
        return _refuse(cls, _unrigged_reason(context))

    def invoke(self, context, event):
        return _confirm(self, context, event, "ped.confirm.shape-keys")

    def execute(self, context):
        return self.run(context, lambda: msg("ped.done.shape-keys",
                                             count=ph.remove_shape_keys(ph.parts(character(context)))))


class DCTLINK_OT_ped_scale(_CharacterOp):
    bl_idname = "dct_link.ped_scale"
    bl_label = EN["ped.op.scale"]
    bl_description = EN["ped.op.scale.desc"]

    factor: FloatProperty(default=1.0, min=1e-4, max=1e4, options={"HIDDEN", "SKIP_SAVE"})

    @classmethod
    def poll(cls, context):
        return _refuse(cls, _placed_reason(context))

    def invoke(self, context, event):
        return _confirm(self, context, event, "ped.confirm.scale", factor=f"{self.factor:g}")

    def execute(self, context):
        def action():
            ph.scale(character(context), self.factor)
            return msg("ped.done.scaled", factor=f"{self.factor:g}")

        return self.run(context, action)


TURN_KEYS = {("X", 90.0): "ped.op.stand-up", ("X", -90.0): "ped.op.stand-up-other", ("Y", 180.0): "ped.op.turn-over",
             ("Z", 90.0): "ped.op.turn-left", ("Z", -90.0): "ped.op.turn-right", ("Z", 180.0): "ped.op.turn-around"}


class DCTLINK_OT_ped_turn(_CharacterOp):
    bl_idname = "dct_link.ped_turn"
    bl_label = EN["ped.op.turn"]
    bl_description = EN["ped.op.turn.desc"]

    axis: EnumProperty(items=(("X", "X", ""), ("Y", "Y", ""), ("Z", "Z", "")), default="Z",
                       options={"HIDDEN", "SKIP_SAVE"})
    degrees: FloatProperty(default=90.0, options={"HIDDEN", "SKIP_SAVE"})

    @classmethod
    def poll(cls, context):
        return _refuse(cls, _placed_reason(context))

    def invoke(self, context, event):
        return _confirm(self, context, event, "ped.confirm.turn")

    def execute(self, context):
        def action():
            ph.turn(character(context), self.axis, self.degrees)
            return msg("ped.done.turned")

        return self.run(context, action)


class DCTLINK_OT_ped_to_origin(_CharacterOp):
    bl_idname = "dct_link.ped_to_origin"
    bl_label = EN["ped.op.to-origin"]
    bl_description = EN["ped.op.to-origin.desc"]

    @classmethod
    def poll(cls, context):
        return _refuse(cls, _placed_reason(context))

    def execute(self, context):
        def action():
            ph.to_origin(character(context))
            return msg("ped.done.origin")

        return self.run(context, action)


class DCTLINK_OT_ped_confirm_facing(_CharacterOp):
    bl_idname = "dct_link.ped_confirm_facing"
    bl_label = EN["ped.op.confirm-facing"]
    bl_description = EN["ped.op.confirm-facing.desc"]

    @classmethod
    def poll(cls, context):
        return _refuse(cls, _unrigged_reason(context))

    def invoke(self, context, event):
        return _confirm(self, context, event, "ped.confirm.facing")

    def execute(self, context):
        def action():
            character(context)[ph.FACING] = 1
            return None

        return self.run(context, action)


# ---- markers ----------------------------------------------------------------------------------------


def _markers_reason(context: Any) -> Optional[Msg]:
    reason = _character_reason(context)
    if reason is None and context.mode != "OBJECT":
        reason = msg("ped.why.object-mode")
    return reason


def write_markers(context: Any, markers: Dict[str, Any]) -> None:
    collection = character(context)
    RUNTIME.writing = True
    try:
        ph.write_markers(collection, markers, props(context).marker_size)
    finally:
        RUNTIME.writing = False
    RUNTIME.last_markers[ident(collection)] = ph.read_markers(collection)


def character_mesh(context: Any) -> Tuple[np.ndarray, np.ndarray]:
    """The character's surface as it stands (world positions and triangles of all its parts)."""
    data = ph.rig_parts(context, character(context))
    positions, triangles, offset = [], [], 0
    for part in data:
        positions.append(part.positions)
        triangles.append(part.triangles + offset)
        offset += len(part.positions)
    if not positions:
        raise UserError(msg("ped.why.no-character"))
    return np.concatenate(positions), np.concatenate(triangles)


class DCTLINK_OT_ped_auto_markers(_CharacterOp):
    bl_idname = "dct_link.ped_auto_markers"
    bl_label = EN["ped.op.auto-markers"]
    bl_description = EN["ped.op.auto-markers.desc"]

    @classmethod
    def poll(cls, context):
        return _refuse(cls, _markers_reason(context))

    def execute(self, context):
        def action():
            positions, triangles = character_mesh(context)
            result = ped.auto_markers(positions, triangles)
            write_markers(context, result.markers)
            RUNTIME.marker_notes[ident(character(context))] = result.notes
            return msg("ped.done.auto-markers")

        return self.run(context, action)


def _rig_joints(context: Any) -> Dict[str, Tuple[float, float, float]]:
    return ph.old_joints(character(context))


class DCTLINK_OT_ped_from_rig(_CharacterOp):
    bl_idname = "dct_link.ped_from_rig"
    bl_label = EN["ped.op.from-rig"]
    bl_description = EN["ped.op.from-rig.desc"]

    @classmethod
    def poll(cls, context):
        reason = _markers_reason(context)
        if reason is None and ped.rig_kind(_rig_joints(context)) is None:
            reason = msg("ped.marker-error.no-rig")
        return _refuse(cls, reason)

    def execute(self, context):
        def action():
            positions, _ = character_mesh(context)
            kind, markers = ped.markers_from_rig(_rig_joints(context), positions)
            write_markers(context, markers)
            RUNTIME.marker_notes[ident(character(context))] = ()
            return msg("ped.done.from-rig", rig=msg(f"ped.rig-kind.{kind}"))

        return self.run(context, action)


class DCTLINK_OT_ped_mirror(_CharacterOp):
    bl_idname = "dct_link.ped_mirror"
    bl_label = EN["ped.op.mirror"]
    bl_description = EN["ped.op.mirror.desc"]

    source: EnumProperty(items=(("L", EN["ped.op.mirror-left"], ""), ("R", EN["ped.op.mirror-right"], "")),
                         default="L", options={"HIDDEN", "SKIP_SAVE"}, translation_context=CONTEXT)

    @classmethod
    def poll(cls, context):
        reason = _markers_reason(context)
        if reason is None and not ph.marker_objects(character(context)):
            reason = msg("ped.why.no-markers")
        return _refuse(cls, reason)

    def execute(self, context):
        def action():
            markers = ph.read_markers(character(context))
            write_markers(context, ped.mirror_markers(markers, self.source))
            return msg("ped.done.mirrored")

        return self.run(context, action)


class DCTLINK_OT_ped_show_markers(_Op):
    bl_idname = "dct_link.ped_show_markers"
    bl_label = EN["ped.op.show"]
    bl_description = EN["ped.op.show-markers.desc"]
    bl_options = {"INTERNAL"}

    names: StringProperty(options={"HIDDEN", "SKIP_SAVE"})

    @classmethod
    def poll(cls, context):
        return _refuse(cls, _character_reason(context))

    def execute(self, context):
        wanted = [name for name in self.names.split(",") if name]
        objs = [obj for name, obj in ph.marker_objects(character(context)).items() if name in wanted]
        ph.select_objects(context, objs)
        host.redraw()
        return {"FINISHED"}


# ---- the click guide --------------------------------------------------------------------------------


class Guide:
    """The click guide's state while it runs: the points placed so far, the one under the mouse, the character's
    search tree and its vertices (for the top of the head)."""

    def __init__(self, tree: Any, positions: np.ndarray) -> None:
        self.tree = tree
        self.positions = positions
        self.points: Dict[str, Tuple[float, float, float]] = {}
        self.preview: Optional[Tuple[float, float, float]] = None
        self.missed = False

    @property
    def index(self) -> int:
        return len(self.points)

    @property
    def current(self) -> Optional[str]:
        return ped.GUIDE[self.index] if self.index < len(ped.GUIDE) else None

    def point(self, origin: Any, direction: Any) -> Optional[Tuple[float, float, float]]:
        name = self.current
        if name is None:
            return None
        hits = ph.ray_hits(self.tree, origin, direction)
        found = ped.guide_point(hits, origin, direction, name)
        if found is not None and name == "headTop" and len(self.positions):
            near = self.positions[np.linalg.norm(self.positions[:, :2] - np.asarray(found[:2]), axis=1) < 0.05]
            if len(near):
                found = (found[0], found[1], float(near[:, 2].max()))
        return found


_NAVIGATION = {"MIDDLEMOUSE", "WHEELUPMOUSE", "WHEELDOWNMOUSE", "TRACKPADPAN", "TRACKPADZOOM", "MOUSEROTATE",
               "NDOF_MOTION"} | {f"NUMPAD_{n}" for n in ("0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "PERIOD",
                                                             "PLUS", "MINUS")}


class DCTLINK_OT_ped_guide(_Op):
    bl_idname = "dct_link.ped_guide"
    bl_label = EN["ped.op.guide"]
    bl_description = EN["ped.op.guide.desc"]
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        reason = _markers_reason(context)
        if reason is None and RUNTIME.guide is not None:
            reason = msg("ped.why.guide-running")
        return _refuse(cls, reason)

    @staticmethod
    def _windows(area: Any) -> List[Any]:
        return [region for region in area.regions if region.type == "WINDOW"] if area is not None else []

    def invoke(self, context, event):
        if context.area is None or context.area.type != "VIEW_3D" or not self._windows(context.area):
            self.report({"ERROR"}, t("ped.why.view3d"))
            return {"CANCELLED"}
        collection = character(context)
        tree = ph.character_tree(context, collection)
        if tree is None:
            self.report({"ERROR"}, t("ped.why.no-character"))
            return {"CANCELLED"}
        positions, _ = character_mesh(context)
        RUNTIME.guide = Guide(tree, positions)
        main = max(self._windows(context.area), key=lambda region: region.width * region.height)
        try:
            with context.temp_override(area=context.area, region=main):
                bpy.ops.view3d.view_axis(type="FRONT")
        except (RuntimeError, TypeError):
            pass  # the view stays as it is
        _guide_handlers(True)
        context.window_manager.modal_handler_add(self)
        self._status(context)
        context.area.tag_redraw()
        return {"RUNNING_MODAL"}

    def _status(self, context: Any) -> None:
        try:
            context.workspace.status_text_set(t("ped.guide.keys"))
        except (AttributeError, TypeError):
            pass

    def _ray(self, context: Any, event: Any) -> Optional[Tuple[Any, Any]]:
        """The ray under the mouse through the 3D view's region it is over (the guide may have been started from the
        sidebar, whose own region has no view); ``None`` outside the 3D view."""
        from bpy_extras import view3d_utils

        def holds(region: Any) -> bool:
            return (region.width > 1 and region.height > 1 and region.x <= event.mouse_x < region.x + region.width
                    and region.y <= event.mouse_y < region.y + region.height)

        area = context.area
        if area is None or any(region.type != "WINDOW" and holds(region) for region in area.regions):
            return None  # the sidebar, a header or the toolbar (drawn over the view with Region Overlap)
        for region in self._windows(area):
            if holds(region) and region.data is not None:
                coord = (event.mouse_x - region.x, event.mouse_y - region.y)
                return (view3d_utils.region_2d_to_origin_3d(region, region.data, coord),
                        view3d_utils.region_2d_to_vector_3d(region, region.data, coord))
        return None

    def _end(self, context: Any, finished: bool) -> set:
        guide_state = RUNTIME.guide
        RUNTIME.guide = None
        _guide_handlers(False)
        try:
            context.workspace.status_text_set(None)
        except (AttributeError, TypeError):
            pass
        if guide_state is not None and finished:
            try:
                positions, triangles = character_mesh(context)
                markers = ped.derive_markers(guide_state.points, positions, triangles)
            except EXPECTED as exc:
                failure = _failure(exc)
                self.report({"ERROR"}, strings.text(failure))
                notify("ERROR", failure)
                host.redraw()
                return {"CANCELLED"}
            write_markers(context, markers)
            RUNTIME.marker_notes[ident(character(context))] = ()
            notify("INFO", msg("ped.guide.done"))
            self.report({"INFO"}, t("ped.guide.done"))
            advance(context)
        if context.area is not None:
            context.area.tag_redraw()
        host.redraw()
        return {"FINISHED"} if finished else {"CANCELLED"}

    def modal(self, context, event):
        guide_state = RUNTIME.guide
        if guide_state is None:
            return {"CANCELLED"}
        if context.area is not None:
            context.area.tag_redraw()
        if event.type in _NAVIGATION:
            return {"PASS_THROUGH"}
        ray = self._ray(context, event) if event.type in ("MOUSEMOVE", "LEFTMOUSE", "RIGHTMOUSE") else None
        if event.type in ("MOUSEMOVE", "LEFTMOUSE", "RIGHTMOUSE") and ray is None:
            return {"PASS_THROUGH"}  # over the sidebar or a header: those keep working
        if event.type == "MOUSEMOVE":
            guide_state.preview = guide_state.point(*ray)
            return {"RUNNING_MODAL"}
        if event.value != "PRESS":
            return {"RUNNING_MODAL"}
        if event.type == "ESC":
            if guide_state.points:
                write_markers(context, guide_state.points)  # what was placed stays, as an undo step
                self._end(context, False)
                return {"FINISHED"}
            return self._end(context, False)
        if event.type in ("RIGHTMOUSE", "BACK_SPACE"):
            if guide_state.points:
                guide_state.points.pop(ped.GUIDE[guide_state.index - 1])
            guide_state.missed = False
            return {"RUNNING_MODAL"}
        if event.type == "LEFTMOUSE":
            point = guide_state.point(*ray)
            if point is None:
                guide_state.missed = True
                return {"RUNNING_MODAL"}
            guide_state.missed = False
            guide_state.points[guide_state.current] = point
            if guide_state.current is None:
                return self._end(context, True)
            return {"RUNNING_MODAL"}
        if event.type in ("RET", "NUMPAD_ENTER") and guide_state.current is None:
            return self._end(context, True)
        return {"RUNNING_MODAL"}

    def cancel(self, context):
        RUNTIME.guide = None
        _guide_handlers(False)


# ---- the rig ----------------------------------------------------------------------------------------


def _connected_reason() -> Optional[Msg]:
    ctrl = controller()
    if ctrl is None:
        return msg("notice.not-ready")
    return None if ctrl.ready else msg("ped.why.connect")


class DCTLINK_OT_ped_refresh_templates(_Op):
    bl_idname = "dct_link.ped_refresh_templates"
    bl_label = EN["ped.op.refresh"]
    bl_description = EN["ped.op.refresh.desc"]

    @classmethod
    def poll(cls, context):
        reason = _connected_reason()
        link = peds()
        if reason is None and link is not None:
            reason = link.feature(ped_link.FEATURE_TEMPLATES)
        return _refuse(cls, reason)

    def execute(self, context):
        settings_ = props(context)
        try:
            peds().fetch_templates(None if settings_.gender == "any" else settings_.gender, settings_.show_all)
        except EXPECTED as exc:
            self.report({"ERROR"}, strings.text(_failure(exc)))
            return {"CANCELLED"}
        host.redraw()
        return {"FINISHED"}


class DCTLINK_OT_ped_use_template(_Op):
    bl_idname = "dct_link.ped_use_template"
    bl_label = EN["ped.op.use-template"]
    bl_description = EN["ped.op.use-template.desc"]
    bl_options = {"REGISTER", "UNDO"}

    model: StringProperty(options={"HIDDEN", "SKIP_SAVE"})

    def execute(self, context):
        if not protocol.is_ped_model(self.model):
            return {"CANCELLED"}
        props(context).template = self.model
        advance(context)
        return {"FINISHED"}


class DCTLINK_MT_ped_templates(Menu):
    bl_idname = "DCTLINK_MT_ped_templates"
    bl_label = EN["ped.prop.template"]
    bl_translation_context = CONTEXT

    def draw(self, context):
        link = peds()
        templates = (link.templates if link is not None else None) or []
        if not templates:
            self.layout.label(text=t("ped.templates.none"), translate=False)
            return
        for entry in templates:
            label = entry["model"]
            if entry.get("recommended"):
                label = t("ped.template.recommended", model=label)
            operator(self.layout, DCTLINK_OT_ped_use_template.bl_idname, None,
                     "SOLO_ON" if entry.get("recommended") else "USER", text=label, model=entry["model"])


def template_line(entry: Dict[str, Any]) -> str:
    """A template's facts: gender, group and layout."""
    parts = []
    if entry.get("gender") in ("male", "female"):
        parts.append(t(f"gender.{entry['gender']}"))
    group = entry.get("group")
    if f"ped.group.{group}" in EN:
        parts.append(t(f"ped.group.{group}"))
    layout = entry.get("layout")
    if f"ped.layout.{layout}" in EN:
        parts.append(t(f"ped.layout.{layout}"))
    return ", ".join(parts)


def _rig_reason(context: Any) -> Optional[Msg]:
    reason = _character_reason(context)
    if reason is not None:
        return reason
    collection = character(context)
    if not ped.checks_pass(character_checks(context, collection)) and not rigged(collection):
        return msg("ped.why.checks")
    markers = ph.read_markers(collection)
    if len(markers) < len(ped.BODY_MARKERS):
        return msg("ped.why.markers")
    reason = _connected_reason()
    if reason is not None:
        return reason
    if not props(context).template:
        return msg("ped.why.template")
    link = peds()
    return link.rig_problem() if link is not None else msg("notice.not-ready")


class DCTLINK_OT_ped_rig(_Op):
    """Rig in Durty Cloth Tool: asks once per character for the rights confirmation, then sends the rig."""

    bl_idname = "dct_link.ped_rig"
    bl_label = EN["ped.op.rig"]
    bl_description = EN["ped.op.rig.desc"]
    bl_options = {"REGISTER", "UNDO"}  # the rights confirmation is kept with the character

    agree: BoolProperty(name=EN["ped.rights.check"], default=False, options={"SKIP_SAVE"}, translation_context=CONTEXT)

    @classmethod
    def poll(cls, context):
        return _refuse(cls, _rig_reason(context))

    def invoke(self, context, event):
        collection = character(context)
        if collection is not None and collection.get(ph.RIGHTS):
            return self.execute(context)
        try:
            return context.window_manager.invoke_props_dialog(self, width=440, title=t("ped.rights.title"),
                                                              confirm_text=t("ped.op.rig"))
        except TypeError:  # an older Blender without a dialog title
            return context.window_manager.invoke_props_dialog(self, width=440)

    def draw(self, context):
        wrapped(self.layout, context, t("ped.rights.text"), width=420)
        self.layout.separator(factor=GAP_SMALL)
        ui.checkbox(self.layout, context, self, "agree", "ped.rights.check")

    def execute(self, context):
        collection = character(context)
        if not collection.get(ph.RIGHTS):
            if not self.agree:
                self.report({"ERROR"}, t("ped.why.rights"))
                return {"CANCELLED"}
            collection[ph.RIGHTS] = 1
        settings_ = props(context)
        try:
            data = ped.rig_input(ph.rig_parts(context, collection))
            options = ped.rig_options(settings_.fingers, settings_.face, settings_.roll_bones, settings_.helper_bones,
                                      settings_.refine, settings_.rest_model)
            peds().start_rig(settings_.template, ph.read_markers(collection), data, options, rights=True,
                             character=ident(collection))
        except EXPECTED as exc:
            failure = _failure(exc)
            self.report({"ERROR"}, strings.text(failure))
            notify("ERROR", failure)
            host.redraw()
            return {"CANCELLED"}
        RUNTIME.notice = None
        advance(context)
        return {"FINISHED"}


class DCTLINK_OT_ped_cancel_rig(_Op):
    bl_idname = "dct_link.ped_cancel_rig"
    bl_label = EN["op.cancel-sign-in"]
    bl_description = EN["ped.op.cancel-rig.desc"]

    @classmethod
    def poll(cls, context):
        link = peds()
        return _refuse(cls, None if link is not None and link.rigging else msg("ped.why.not-rigging"))

    def execute(self, context):
        peds().cancel_rig()
        host.redraw()
        return {"FINISHED"}


def _result_reason(context: Any) -> Optional[Msg]:
    reason = _character_reason(context)
    if reason is None and waiting_rig(character(context)) is None:
        reason = msg("ped.why.no-result")
    return reason


class DCTLINK_OT_ped_apply_rig(_CharacterOp):
    bl_idname = "dct_link.ped_apply_rig"
    bl_label = EN["ped.op.apply-rig"]
    bl_description = EN["ped.op.apply-rig.desc"]

    @classmethod
    def poll(cls, context):
        return _refuse(cls, _result_reason(context))

    def execute(self, context):
        def action():
            collection = character(context)
            link = peds()
            rig_result, sent = link.rig, link.rig_sent
            rig = ph.apply_rig(context, collection, rig_result, sent)
            link.take_rig()
            RUNTIME.findings.pop(ident(collection), None)
            return msg("ped.done.applied", name=rig.name, bones=len(rig.data.bones))

        return self.run(context, action)


class DCTLINK_OT_ped_use_refined(_CharacterOp):
    bl_idname = "dct_link.ped_use_refined"
    bl_label = EN["ped.op.use-refined"]
    bl_description = EN["ped.op.use-refined.desc"]

    @classmethod
    def poll(cls, context):
        return _refuse(cls, _result_reason(context))

    def execute(self, context):
        def action():
            refined = ped.markers_from_json(json.dumps(waiting_rig(character(context)).report.get("markers") or {}))
            current = ph.read_markers(character(context))
            current.update({k: v for k, v in refined.items() if k in ped.BODY_MARKERS})
            write_markers(context, current)
            return msg("ped.done.refined")

        return self.run(context, action)


class DCTLINK_OT_ped_discard_rig(_Op):
    bl_idname = "dct_link.ped_discard_rig"
    bl_label = EN["ped.op.discard-rig"]
    bl_description = EN["ped.op.discard-rig.desc"]

    @classmethod
    def poll(cls, context):
        return _refuse(cls, _result_reason(context))

    def execute(self, context):
        peds().discard_rig()
        advance(context)
        return {"FINISHED"}


class DCTLINK_OT_ped_previous_rig(_CharacterOp):
    bl_idname = "dct_link.ped_previous_rig"
    bl_label = EN["ped.op.previous-rig"]
    bl_description = EN["ped.op.previous-rig.desc"]

    @classmethod
    def poll(cls, context):
        reason = _character_reason(context)
        if reason is None and ph.previous_armature(character(context)) is None:
            reason = msg("ped.why.no-previous")
        return _refuse(cls, reason)

    def execute(self, context):
        def action():
            ph.restore_previous(context, character(context))
            RUNTIME.findings.pop(ident(character(context)), None)
            return msg("ped.done.previous")

        return self.run(context, action)


class DCTLINK_OT_ped_remove_rig(_CharacterOp):
    bl_idname = "dct_link.ped_remove_rig"
    bl_label = EN["ped.op.remove-rig"]
    bl_description = EN["ped.op.remove-rig.desc"]

    @classmethod
    def poll(cls, context):
        reason = _character_reason(context)
        if reason is None and not rigged(character(context)):
            reason = msg("ped.why.not-rigged")
        return _refuse(cls, reason)

    def invoke(self, context, event):
        return _confirm(self, context, event, "ped.confirm.remove-rig")

    def execute(self, context):
        def action():
            ph.remove_rig(context, character(context))
            RUNTIME.findings.pop(ident(character(context)), None)
            return msg("ped.done.removed")

        return self.run(context, action)


# ---- check ------------------------------------------------------------------------------------------


def _rigged_reason(context: Any) -> Optional[Msg]:
    reason = _character_reason(context)
    if reason is None and not rigged(character(context)):
        reason = msg("ped.why.not-rigged")
    return reason


POSE_ITEMS = tuple((name, EN[f"ped.pose.{name}"], "") for name in ped.POSES)


class DCTLINK_OT_ped_pose(_Op):
    bl_idname = "dct_link.ped_pose"
    bl_label = EN["ped.op.pose"]
    bl_description = EN["ped.op.pose.desc"]
    bl_options = {"REGISTER", "UNDO"}

    pose: EnumProperty(items=POSE_ITEMS, default="yours",
                       options={"HIDDEN", "SKIP_SAVE"}, translation_context=CONTEXT)

    @classmethod
    def poll(cls, context):
        return _refuse(cls, _rigged_reason(context))

    def execute(self, context):
        ph.set_pose(context, ph.armature(character(context)), self.pose)
        host.redraw()
        return {"FINISHED"}


class DCTLINK_OT_ped_run_checks(_CharacterOp):
    bl_idname = "dct_link.ped_run_checks"
    bl_label = EN["ped.op.run-checks"]
    bl_description = EN["ped.op.run-checks.desc"]

    @classmethod
    def poll(cls, context):
        return _refuse(cls, _rigged_reason(context))

    def execute(self, context):
        def action():
            collection = character(context)
            manager = context.window_manager
            manager.progress_begin(0, 100)
            try:
                findings = ph.run_checks(context, collection, lambda f: manager.progress_update(int(100 * f)))
            finally:
                manager.progress_end()
            RUNTIME.findings[ident(collection)] = findings
            refused = [f for f in findings if f.code in ped.REFUSED_CODES]
            collection[ph.CHECKED] = 0 if refused else 1
            if refused:
                return "WARNING", msg("ped.done.checks-refused", count=len(refused))
            return msg("ped.done.checks", count=len(findings))

        return self.run(context, action)


class DCTLINK_OT_ped_show_finding(_Op):
    bl_idname = "dct_link.ped_show_finding"
    bl_label = EN["ped.op.show"]
    bl_description = EN["ped.op.show-finding.desc"]
    bl_options = {"INTERNAL"}

    index: bpy.props.IntProperty(options={"HIDDEN", "SKIP_SAVE"})

    @classmethod
    def poll(cls, context):
        return _refuse(cls, _character_reason(context))

    def execute(self, context):
        findings = RUNTIME.findings.get(ident(character(context))) or []
        if not 0 <= self.index < len(findings):
            return {"CANCELLED"}
        finding = findings[self.index]
        if finding.pose:
            ph.set_pose(context, ph.armature(character(context)), finding.pose)
        ph.select_vertices(context, finding.vertices or {})
        host.redraw()
        return {"FINISHED"}


# ---- send -------------------------------------------------------------------------------------------


def _send_reason(context: Any) -> Optional[Msg]:
    reason = _rigged_reason(context)
    if reason is not None:
        return reason
    settings_ = props(context)
    problem = ped.model_problem(settings_.model_name)
    if problem is not None:
        return msg(problem[0], **problem[1])
    if not settings_.ped_name.strip():
        return msg("ped.why.name")
    collection = character(context)
    findings = RUNTIME.findings.get(ident(collection))
    if findings is not None and any(f.code in ped.REFUSED_CODES for f in findings):
        return msg("ped.why.refused-checks")
    if any(code in ("too-large", "not-multiple-of-four") for _, code in ph.texture_problems(ph.parts(collection))):
        return msg("ped.why.textures")
    reason = _connected_reason()
    if reason is not None:
        return reason
    link = peds()
    return link.add_problem() if link is not None else msg("notice.not-ready")


class DCTLINK_OT_ped_send(_Op):
    bl_idname = "dct_link.ped_send"
    bl_label = EN["ped.op.send"]
    bl_description = EN["ped.op.send.desc"]

    @classmethod
    def poll(cls, context):
        return _refuse(cls, _send_reason(context))

    def execute(self, context):
        collection = character(context)
        settings_ = props(context)
        ctrl = controller()
        folder = None
        try:
            if not collection.get(ph.RIGHTS):
                raise UserError(msg("ped.why.rights"))
            info = ph.rig_info(collection)
            template = info.get("template") or settings_.template
            folder = ph.work_folder(ctrl.data_dir)
            context.window_manager.progress_begin(0, 1)  # the export can take a while: the cursor says so
            try:
                glb = ph.export_glb(context, collection, folder)
            finally:
                context.window_manager.progress_end()
            roles = [(obj.name, ph.role_of(obj)) for obj in ph.parts(collection)]
            parts = [(name, role) for name, role in roles if role != "body"]
            rig_job = (peds().rig_job(info.get("job"), ident(collection))
                       if info.get("template", "").lower() == template.lower() else None)
            ragdoll = None if settings_.ragdoll == "template" else settings_.ragdoll
            peds().start_add(template, settings_.ped_name.strip(), settings_.model_name, glb, rights=True, rig=rig_job,
                             ragdoll=ragdoll, parts=parts, character=ident(collection))
        except EXPECTED as exc:
            if not isinstance(exc, UserError):
                traceback.print_exc()
            failure = _failure(exc)
            self.report({"ERROR"}, strings.text(failure))
            notify("ERROR", failure)
            host.redraw()
            return {"CANCELLED"}
        finally:
            if folder is not None:
                shutil.rmtree(folder, ignore_errors=True)
        RUNTIME.notice = None
        advance(context)
        return {"FINISHED"}


class DCTLINK_OT_ped_cancel_send(_Op):
    bl_idname = "dct_link.ped_cancel_send"
    bl_label = EN["op.cancel-sign-in"]
    bl_description = EN["ped.op.cancel-send.desc"]

    @classmethod
    def poll(cls, context):
        link = peds()
        return _refuse(cls, None if link is not None and link.sending else msg("ped.why.not-sending"))

    def execute(self, context):
        peds().cancel_add()
        host.redraw()
        return {"FINISHED"}


# --------------------------------------------------------------------------------------------------
# Drawing
# --------------------------------------------------------------------------------------------------


def _row_icon(level: str) -> str:
    return LEVEL_ICONS.get(level, "INFO")


def _fix_button(layout: Any, idname: str, values: Dict[str, Any]) -> None:
    if idname == "dct_link.ped_turn":
        key = TURN_KEYS.get((values.get("axis"), float(values.get("degrees", 0.0))), "ped.op.turn")
        operator(layout, idname, key, "ORIENTATION_GIMBAL", **values)
    elif idname == "dct_link.ped_scale":
        factor = float(values.get("factor", 1.0))
        operator(layout, idname, None, "FULLSCREEN_ENTER", text=t("ped.op.scale-by", factor=f"{factor:g}"), **values)
    else:
        keys = {"dct_link.ped_apply_transforms": ("ped.op.apply-transforms", "OBJECT_ORIGIN"),
                "dct_link.ped_apply_modifiers": ("ped.op.apply-modifiers", "MODIFIER"),
                "dct_link.ped_remove_old_rig": ("ped.op.remove-old-rig", "ARMATURE_DATA"),
                "dct_link.ped_remove_shape_keys": ("ped.op.remove-shape-keys", "SHAPEKEY_DATA"),
                "dct_link.ped_to_origin": ("ped.op.to-origin", "PIVOT_CURSOR"),
                "dct_link.ped_confirm_facing": ("ped.op.confirm-facing", "CHECKMARK")}
        key, icon = keys[idname]
        operator(layout, idname, key, icon, **values)


def _check_fields(row: ped.Check) -> Dict[str, Any]:
    fields = dict(row.fields or {})
    for name in ("unit", "direction"):
        if name in fields and isinstance(fields[name], str) and fields[name] in EN:
            fields[name] = msg(fields[name])
    return fields


def draw_character(layout: Any, context: Any) -> None:
    collection = character(context)
    if collection is None or not ph.parts(collection):
        guide(layout, context, "ped.character.none")
        step(layout, context, DCTLINK_OT_ped_use_selected.bl_idname, "ped.op.use-selected", "RESTRICT_SELECT_OFF")
        return
    # The character's name with Use Selected beside it, or Use Selected under it when the two would be cut.
    side_by_side = ui.fits_side_by_side(context, (collection.name, t("ped.op.use-selected")))
    row = layout.row() if side_by_side else layout.column(align=True)
    row.label(text=collection.name, icon="OUTLINER_COLLECTION", translate=False)
    operator(row, DCTLINK_OT_ped_use_selected.bl_idname, "ped.op.use-selected", "RESTRICT_SELECT_OFF")
    found = facts(context, collection)
    subtext(layout, context, "ped.character.facts", objects=found.objects, vertices=found.vertices,
            triangles=found.triangles, materials=found.materials)
    layout.separator(factor=GAP_SMALL)
    for row_ in character_checks(context, collection):
        wrapped(layout, context, strings.text(msg(row_.key, **_check_fields(row_))), _row_icon(row_.level),
                alert=row_.level == "error")
        if row_.fixes:
            buttons = layout.column(align=True)
            for idname, values in row_.fixes:
                _fix_button(buttons, idname, values)
    layout.separator(factor=GAP_SMALL)
    objs = ph.parts(collection)
    header, body = layout.panel("dct_link_ped_parts", default_closed=True)
    header.label(text=t("ped.heading.parts", count=len(objs)), icon="OUTLINER_OB_MESH", translate=False)
    if body is not None:
        subtext(body, context, "ped.parts.subtext")
        for obj in objs:
            split = body.split(factor=0.45, align=True)
            split.label(text=obj.name, translate=False)
            split.prop(obj, "dct_ped_role", text="")
            if getattr(obj, "dct_ped_role", "auto") == "auto":
                subtext(body, context, "ped.parts.guess", role=msg(f"ped.role.{ph.role_of(obj)}"), indent=True)


def draw_markers(layout: Any, context: Any) -> None:
    collection = character(context)
    if collection is None:
        reason_text(layout, context, msg("ped.why.no-character"))
        return
    markers = ph.read_markers(collection)
    heading(layout, context, "ped.heading.markers", "EMPTY_DATA", info="ped-markers")
    subtext(layout, context, "ped.markers.placed", placed=len(markers), total=len(ped.BODY_MARKERS))
    step(layout, context, DCTLINK_OT_ped_guide.bl_idname, "ped.op.guide", "RESTRICT_SELECT_OFF")
    row = layout.row(align=True)
    operator(row, DCTLINK_OT_ped_auto_markers.bl_idname, "ped.op.auto-markers", "EMPTY_DATA")
    if ped.rig_kind(_rig_joints(context)) is not None:
        operator(row, DCTLINK_OT_ped_from_rig.bl_idname, "ped.op.from-rig", "ARMATURE_DATA")
    if markers:
        row = layout.row(align=True)
        operator(row, DCTLINK_OT_ped_mirror.bl_idname, "ped.op.mirror-left", "MOD_MIRROR", source="L")
        operator(row, DCTLINK_OT_ped_mirror.bl_idname, "ped.op.mirror-right", "MOD_MIRROR", source="R")
    for note in RUNTIME.marker_notes.get(ident(collection), ()):
        wrapped(layout, context, t(f"ped.marker-note.{note}"), "INFO")
    if markers:
        for problem in ped.marker_problems(markers):
            wrapped(layout, context, t(f"ped.marker-problem.{problem.code}", names=marker_names(problem.markers)),
                    "ERROR")
            if problem.code != "missing":
                show_button(layout, DCTLINK_OT_ped_show_markers.bl_idname, names=",".join(problem.markers))
    body = options_section(layout, "markers")
    if body is not None:
        body.prop(props(context), "marker_size", text=t("ped.prop.marker-size"), translate=False)
        ui.checkbox(body, context, props(context), "follow", "ped.prop.follow")


def _report(layout: Any, context: Any, lines: List[ped.ReportLine]) -> None:
    for line in lines:
        fields = dict(line.fields)
        text = strings.text(msg(line.key, **fields))
        if line.markers:
            text += " " + t("ped.result.markers", names=marker_names(line.markers))
        wrapped(layout, context, text, LEVEL_ICONS.get(line.level, "INFO"))
        if line.markers:
            show_button(layout, DCTLINK_OT_ped_show_markers.bl_idname, names=",".join(line.markers))
        if line.key == "ped.suggest" and line.template:
            operator(layout, DCTLINK_OT_ped_use_template.bl_idname, None, "FORWARD",
                     text=t("ped.op.use-template-named", template=line.template), model=line.template)


def draw_rig(layout: Any, context: Any) -> None:
    collection = character(context)
    settings_ = props(context)
    link = peds()
    ctrl = controller()
    if collection is None:
        reason_text(layout, context, msg("ped.why.no-character"))
        return
    # The template.
    heading(layout, context, "ped.heading.template", "OUTLINER_OB_ARMATURE", info="ped-template")
    if ctrl is None or not ctrl.ready:
        wrapped(layout, context, t("ped.why.connect"), "UNLINKED")
    else:
        wanted = link is not None and link.wants_templates(*_template_filters(settings_))
        if wanted and not bpy.app.timers.is_registered(_auto_templates):
            bpy.app.timers.register(_auto_templates, first_interval=0.0)
        row = layout.row(align=True)
        row.prop(settings_, "gender", expand=True)
        ui.checkbox(layout, context, settings_, "show_all", "ped.prop.show-all")
        row = layout.row(align=True)
        row.menu(DCTLINK_MT_ped_templates.bl_idname, text=settings_.template or t("ped.template.choose"),
                 icon="OUTLINER_OB_ARMATURE")
        operator(row, DCTLINK_OT_ped_refresh_templates.bl_idname, None, "FILE_REFRESH", text="")
        entry = link.template(settings_.template) if link is not None and settings_.template else None
        if entry is not None:
            subtext(layout, context, "ped.template.facts", facts=template_line(entry))
        if link is not None and link.loading_templates:
            wrapped(layout, context, t("ped.templates.loading"), "SORTTIME")
        elif link is not None and link.templates_problem is not None:
            ui.draw_notice(layout, context, link.templates_problem)
        elif link is not None and link.templates is None:
            subtext(layout, context, "ped.templates.refresh")
        elif link is not None and not link.templates:
            wrapped(layout, context, t("ped.templates.none"), "INFO")
        elif link is not None and link.truncated:
            subtext(layout, context, "ped.templates.truncated", count=len(link.templates or ()))
        plan = link.feature(ped_link.FEATURE_RIG) if link is not None else None
        if plan is not None:
            wrapped(layout, context, strings.text(plan), "INFO")
    layout.separator(factor=GAP)
    if collection.get(ph.RIGHTS):
        subtext(layout, context, "ped.rights.done")
    rigging = link is not None and link.rigging and (link.rig_sent or {}).get("character") == ident(collection)
    if rigging:
        stage = ped_link.stage_text(link.stage)
        layout.progress(factor=link.fraction, text=strings.text(msg("ped.rig.progress", stage=stage,
                                                                     percent=int(link.fraction * 100))))
        if link.rig_status is not None:
            ui.draw_notice(layout, context, link.rig_status)
        operator(layout, DCTLINK_OT_ped_cancel_rig.bl_idname, "op.cancel-sign-in", "X")
        return
    waiting = waiting_rig(collection)
    if waiting is not None:
        draw_result(layout, context, collection, waiting)
        return
    key = "ped.op.rig-again" if rigged(collection) else "ped.op.rig"
    step(layout, context, DCTLINK_OT_ped_rig.bl_idname, key, "ARMATURE_DATA")
    reason = _rig_reason(context)
    if reason is not None and reason.key not in ("ped.why.connect",):
        reason_text(layout, context, reason)
    if link is not None and (link.rig_sent or {}).get("character") == ident(collection):
        if link.rig_status is not None:
            ui.draw_notice(layout, context, link.rig_status)
        _report(layout, context, link.refusal)
    if rigged(collection):
        info = ph.rig_info(collection)
        layout.separator(factor=GAP_SMALL)
        wrapped(layout, context, t("ped.rigged.line", template=info.get("template", "?"), bones=info.get("bones", 0)),
                "CHECKMARK")
        report = info.get("report") or {}
        if report:
            _report(layout, context, ped.report_lines(report))
        row = layout.row(align=True)
        if ph.previous_armature(collection) is not None:
            operator(row, DCTLINK_OT_ped_previous_rig.bl_idname, "ped.op.previous-rig", "LOOP_BACK")
        operator(row, DCTLINK_OT_ped_remove_rig.bl_idname, "ped.op.remove-rig", "TRASH")
    body = options_section(layout, "rig")
    if body is not None:
        ui.checkbox(body, context, settings_, "refine", "ped.prop.refine")
        labelled(body, settings_, "fingers", "ped.prop.fingers")
        labelled(body, settings_, "face", "ped.prop.face")
        ui.checkbox(body, context, settings_, "roll_bones", "ped.prop.roll")
        ui.checkbox(body, context, settings_, "helper_bones", "ped.prop.helpers")
        labelled(body, settings_, "rest_model", "ped.prop.rest")


def draw_result(layout: Any, context: Any, collection: Any, waiting: Any) -> None:
    """A rig that arrived: its report, the markers Durty Cloth Tool moved (yellow in the 3D view), Apply Rig."""
    _report(layout, context, ped.report_lines(waiting.report))
    sent = (peds().rig_sent or {}).get("markers") or {}
    moves = ped.refined_moves(waiting.report, sent)
    if moves:
        layout.separator(factor=GAP_SMALL)
        wrapped(layout, context, t("ped.result.moved", count=len(moves)), "EMPTY_DATA")
        column = layout.column(align=True)
        for name, distance in moves[:6]:
            column.label(text=t("ped.result.move", marker=msg(f"ped.marker.{name}"), cm=f"{distance * 100:.1f}"),
                         icon="BLANK1", translate=False)
        operator(layout, DCTLINK_OT_ped_use_refined.bl_idname, "ped.op.use-refined", "EMPTY_DATA")
    layout.separator(factor=GAP_SMALL)
    step(layout, context, DCTLINK_OT_ped_apply_rig.bl_idname, "ped.op.apply-rig", "CHECKMARK")
    operator(layout, DCTLINK_OT_ped_discard_rig.bl_idname, "ped.op.discard-rig", "X")
    subtext(layout, context, "ped.result.subtext")


POSE_ICONS = {"yours": "POSE_HLT", "rest": "ARMATURE_DATA", "arms_up": "OUTLINER_OB_ARMATURE",
              "arms_forward": "OUTLINER_OB_ARMATURE", "squat": "OUTLINER_OB_ARMATURE", "walk": "OUTLINER_OB_ARMATURE",
              "twist": "OUTLINER_OB_ARMATURE"}


def draw_check(layout: Any, context: Any) -> None:
    collection = character(context)
    if collection is None or not rigged(collection):
        reason_text(layout, context, msg("ped.why.not-rigged"))
        return
    heading(layout, context, "ped.heading.poses", "POSE_HLT", info="ped-poses")
    grid = layout.grid_flow(columns=2, even_columns=True, align=True) if hasattr(layout, "grid_flow") else \
        layout.column(align=True)
    for pose in ped.POSES:
        operator(grid, DCTLINK_OT_ped_pose.bl_idname, f"ped.pose.{pose}", POSE_ICONS[pose], pose=pose)
    layout.separator(factor=GAP)
    step(layout, context, DCTLINK_OT_ped_run_checks.bl_idname, "ped.op.run-checks", "CHECKMARK")
    findings = RUNTIME.findings.get(ident(collection))
    if findings is None:
        return
    if not findings:
        wrapped(layout, context, t("ped.local.none"), "CHECKMARK")
        return
    for index, finding in enumerate(findings):
        refused = finding.code in ped.REFUSED_CODES
        fields: Dict[str, Any] = {"count": finding.count, "names": ", ".join(finding.names[:5])}
        if finding.pose:
            fields["pose"] = msg(f"ped.pose.{finding.pose}")
        wrapped(layout, context, t(f"ped.local.{finding.code}", **fields), "CANCEL" if refused else "ERROR",
                alert=refused)
        if finding.vertices:
            show_button(layout, DCTLINK_OT_ped_show_finding.bl_idname, index=index)
    subtext(layout, context, "ped.local.hint")


def draw_send(layout: Any, context: Any) -> None:
    collection = character(context)
    settings_ = props(context)
    link = peds()
    if collection is None or not rigged(collection):
        reason_text(layout, context, msg("ped.why.not-rigged"))
        return
    labelled(layout, settings_, "ped_name", "ped.prop.name")
    labelled(layout, settings_, "model_name", "ped.prop.model")
    problem = ped.model_problem(settings_.model_name)
    if problem is not None:
        wrapped(layout, context, t(problem[0], **problem[1]), "ERROR")
    for name, code in ph.texture_problems(ph.parts(collection)):
        refused = code in ("too-large", "not-multiple-of-four")
        wrapped(layout, context, t(f"ped.texture.{code}", name=name), "CANCEL" if refused else "ERROR", alert=refused)
    body = options_section(layout, "send")
    if body is not None:
        labelled(body, settings_, "ragdoll", "ped.prop.ragdoll")
        subtext(body, context, "ped.ragdoll.subtext")
    layout.separator(factor=GAP_SMALL)
    plan = link.feature(ped_link.FEATURE_ADD) if link is not None else None
    if plan is not None and plan.key != "ped.why.connect":
        wrapped(layout, context, strings.text(plan), "INFO")
    sending = link is not None and link.sending and (link.add_sent or {}).get("character") == ident(collection)
    if sending:
        ui.draw_notice(layout, context, link.add_status)
        operator(layout, DCTLINK_OT_ped_cancel_send.bl_idname, "op.cancel-sign-in", "X")
        return
    step(layout, context, DCTLINK_OT_ped_send.bl_idname, "ped.op.send", "EXPORT")
    reason = _send_reason(context)
    if reason is not None and reason.key != "ped.why.connect":
        reason_text(layout, context, reason)
    subtext(layout, context, "ped.send.subtext")
    if link is None or (link.add_sent or {}).get("character") != ident(collection) or link.add_status is None:
        return
    layout.separator(factor=GAP_SMALL)
    ui.draw_notice(layout, context, link.add_status)
    if link.findings:
        wrapped(layout, context, t("ped.send.findings", count=len(link.findings)), "INFO")
        for finding in link.findings:
            severity = str(finding.get("severity"))
            wrapped(layout, context, t(f"severity.{severity}") + ": " + strings.text(
                ped_link.finding_text(str(finding.get("code")))), ui.SEVERITY_ICONS.get(severity, "INFO"), indent=True)
    if link.created is not None:
        subtext(layout, context, "ped.send.next")


STAGE_DRAW = {"character": draw_character, "markers": draw_markers, "rig": draw_rig, "check": draw_check,
              "send": draw_send}


def stage_status(context: Any, stage: str) -> Tuple[str, bool]:
    """A section's header: its short status and whether the stage is done."""
    collection = character(context)
    current = flow(context)
    if stage == "character":
        if not current.character:
            return t("ped.status.none"), False
        return t("ped.status.vertices", count=facts(context, collection).vertices), current.checks_ok or current.rigged
    if stage == "markers":
        return (t("ped.status.markers", placed=current.markers, total=len(ped.BODY_MARKERS)),
                current.markers == len(ped.BODY_MARKERS) and not current.marker_problems)
    if stage == "rig":
        if current.rigging:
            return t("ped.status.rigging"), False
        if current.result:
            return t("ped.status.waiting"), False
        if current.rigged:
            report = ph.rig_info(collection).get("report") or {}
            return t("ped.status.ready" if report.get("outcome") == "ready" else "ped.status.review"), True
        return t("ped.status.not-rigged"), False
    if stage == "check":
        findings = RUNTIME.findings.get(ident(collection))
        if findings is None:
            return t("ped.status.not-checked"), current.checked
        return (t("ped.status.no-problems") if not findings else t("ped.status.problems", count=len(findings)),
                current.checked)
    if current.sent:
        return sent_project(collection).get("name") or t("ped.status.sent"), True
    if current.sending:
        return t("ped.status.sending"), False
    return t("ped.status.not-sent"), False


def draw_main(layout: Any, context: Any) -> None:
    RUNTIME.flow = None
    RUNTIME.flow = flow(context)
    try:
        _draw_main(layout, context)
    finally:
        RUNTIME.flow = None


def _draw_main(layout: Any, context: Any) -> None:
    key = ped.next_step(flow(context))
    collection = character(context)
    created = sent_project(collection)
    if key == "ped.next.done" and created:
        wrapped(layout, context, t(key, name=created.get("name", "")), "FORWARD")
    elif key == "ped.next.done":
        wrapped(layout, context, t("ped.next.done-before"), "FORWARD")
    else:
        wrapped(layout, context, t(key), "FORWARD")
    if collection is None:
        subtext(layout, context, "experimental.note", indent=True)
    if RUNTIME.notice is not None:
        layout.separator(factor=GAP_SMALL)
        level, message = RUNTIME.notice
        wrapped(layout, context, strings.text(message), LEVEL_ICONS.get(level, "INFO"), alert=level == "ERROR")
    settings_ = props(context)
    for number, stage in enumerate(ped.STAGES, start=1):
        layout.separator(factor=GAP_SMALL)
        header, body = layout.panel_prop(settings_, f"open_{stage}")
        status, done = stage_status(context, stage)
        ui.stage_header(header, context, t("ped.stage-title", number=number, title=msg(f"ped.section.{stage}")),
                        status, done)
        if body is not None:
            STAGE_DRAW[stage](body, context)
    if collection is not None:
        layout.separator(factor=GAP_SMALL)
        subtext(layout, context, "ped.privacy")


# --------------------------------------------------------------------------------------------------
# The 3D view: markers, refined markers and the click guide
# --------------------------------------------------------------------------------------------------

_DRAW: Dict[str, Any] = {"markers": None, "guide_view": None, "guide_pixel": None, "shaders": {}}
LEFT_COLOUR = (0.25, 0.55, 1.0, 0.95)
RIGHT_COLOUR = (1.0, 0.55, 0.15, 0.95)
CENTRE_COLOUR = (0.92, 0.92, 0.92, 0.95)
REFINED_COLOUR = (1.0, 0.9, 0.15, 0.95)
PROBLEM_COLOUR = (1.0, 0.25, 0.2, 0.95)


def _shader(name: str) -> Any:
    import gpu

    shaders = _DRAW["shaders"]
    if name not in shaders:
        try:
            shaders[name] = gpu.shader.from_builtin(name)
        except (ValueError, SystemError):
            shaders[name] = gpu.shader.from_builtin("UNIFORM_COLOR")
    return shaders[name]


def _lines(points: List[Any], colour: Tuple[float, ...], width: float = 2.0) -> None:
    import gpu
    from gpu_extras.batch import batch_for_shader

    if not points:
        return
    shader = _shader("POLYLINE_UNIFORM_COLOR")
    batch = batch_for_shader(shader, "LINES", {"pos": points})
    shader.bind()
    try:
        region = bpy.context.region
        shader.uniform_float("viewportSize", (region.width, region.height))
        shader.uniform_float("lineWidth", width)
    except (AttributeError, ValueError):
        pass  # the plain shader has neither
    shader.uniform_float("color", colour)
    batch.draw(shader)


def _dots(points: List[Any], colour: Tuple[float, ...], size: float = 8.0) -> None:
    import gpu
    from gpu_extras.batch import batch_for_shader

    if not points:
        return
    shader = _shader("POINT_UNIFORM_COLOR")
    batch = batch_for_shader(shader, "POINTS", {"pos": points})
    gpu.state.point_size_set(size)
    shader.bind()
    shader.uniform_float("color", colour)
    batch.draw(shader)
    gpu.state.point_size_set(1.0)


def _marker_colour(name: str) -> Tuple[float, ...]:
    return {"L": LEFT_COLOUR, "R": RIGHT_COLOUR}.get(ped.side(name), CENTRE_COLOUR)


def _draw_markers() -> None:
    """The character's markers: lines between them, dots coloured by side (left blue, right orange), and where Durty
    Cloth Tool moved them (yellow) while a rig waits to be applied."""
    context = bpy.context
    scene = getattr(context, "scene", None)
    if scene is None or getattr(getattr(scene, "dct_link", None), "workspace", "CLOTHING") != "PED":
        return
    collection = character(context)
    if collection is None:
        return
    try:
        import gpu

        markers = ph.read_markers(collection)
        gpu.state.depth_test_set("NONE")
        gpu.state.blend_set("ALPHA")
        bad = set()
        if len(markers) == len(ped.BODY_MARKERS):
            for problem in ped.marker_problems(markers):
                bad |= set(problem.markers)
        for colour_side in ("", "L", "R"):
            lines = []
            for a, b in ped.STICK:
                if a in markers and b in markers and ped.side(b) == colour_side:
                    lines += [markers[a], markers[b]]
            colour = {"": CENTRE_COLOUR, "L": LEFT_COLOUR, "R": RIGHT_COLOUR}[colour_side]
            _lines(lines, colour)
        for name, point in markers.items():
            _dots([point], PROBLEM_COLOUR if name in bad else _marker_colour(name), 9.0)
        waiting = waiting_rig(collection)
        if waiting is not None:
            refined = ped.markers_from_json(json.dumps(waiting.report.get("markers") or {}))
            moved = [(markers.get(name), point) for name, point in refined.items() if name in markers]
            _lines([p for pair in moved for p in pair if pair[0] is not None], REFINED_COLOUR, 1.5)
            _dots(list(refined.values()), REFINED_COLOUR, 7.0)
        gpu.state.blend_set("NONE")
    except (ReferenceError, AttributeError, ImportError, ValueError, SystemError):
        return  # nothing to draw on (background mode, a scene being freed)


def _draw_guide_view() -> None:
    """The click guide's points in the 3D view: those placed (green) and where the next click would land (orange)."""
    guide_state = RUNTIME.guide
    if guide_state is None:
        return
    try:
        import gpu

        gpu.state.depth_test_set("NONE")
        gpu.state.blend_set("ALPHA")
        _dots(list(guide_state.points.values()), (0.3, 0.9, 0.4, 0.95), 9.0)
        if guide_state.preview is not None:
            _dots([guide_state.preview], RIGHT_COLOUR, 12.0)
        gpu.state.blend_set("NONE")
    except (ReferenceError, AttributeError, ImportError, ValueError, SystemError):
        return


def _draw_guide_pixel() -> None:
    """The click guide's figure in the corner of the 3D view: the points placed, the next one large, and what to
    click."""
    guide_state = RUNTIME.guide
    if guide_state is None:
        return
    try:
        import blf
        import gpu

        region = bpy.context.region
        scale = ui._scale(bpy.context)
        size = 220 * scale
        left, bottom = 20 * scale, 40 * scale
        gpu.state.blend_set("ALPHA")
        shader = _shader("UNIFORM_COLOR")
        from gpu_extras.batch import batch_for_shader

        box = [(left - 10 * scale, bottom - 10 * scale), (left + size * 0.6, bottom - 10 * scale),
               (left + size * 0.6, bottom + size + 10 * scale), (left - 10 * scale, bottom + size + 10 * scale)]
        batch = batch_for_shader(shader, "TRI_FAN", {"pos": box})
        shader.bind()
        shader.uniform_float("color", (0.05, 0.05, 0.05, 0.6))
        batch.draw(shader)

        def at(name: str) -> Tuple[float, float]:
            x, y = ped.FIGURE[name]
            return (left + size * 0.3 + x * size * 0.9, bottom + y * size * 0.95)

        _lines([at(n) for pair in ped.FIGURE_LINES for n in pair], (0.7, 0.7, 0.7, 0.8), 2.0)
        top, chin = at("headTop"), at("chin")
        centre = ((top[0] + chin[0]) / 2, (top[1] + chin[1]) / 2)
        radius = (top[1] - chin[1]) / 2
        ring = [(centre[0] + radius * 0.8 * math.cos(a), centre[1] + radius * math.sin(a))
                for a in np.linspace(0.0, 2 * math.pi, 25)]
        _lines([p for pair in zip(ring, ring[1:]) for p in pair], (0.7, 0.7, 0.7, 0.8), 2.0)
        _dots([at(n) for n in guide_state.points], (0.3, 0.9, 0.4, 1.0), 8.0 * scale)
        current = guide_state.current
        if current is not None:
            _dots([at(current)], RIGHT_COLOUR, 14.0 * scale)
        font = 0
        blf.size(font, 13 * scale)
        blf.color(font, 1.0, 1.0, 1.0, 1.0)
        lines = [t("ped.guide.title", index=min(guide_state.index + 1, len(ped.GUIDE)), total=len(ped.GUIDE))]
        lines.append(t(f"ped.guide.{current}") if current is not None else t("ped.guide.finish"))
        if guide_state.missed:
            lines.append(t("ped.guide.missed"))
        y = bottom + size + 30 * scale
        width = max(200 * scale, region.width - left - 20 * scale)
        for line in reversed(lines):
            for part in reversed(strings.wrap_text(line, width, lambda text: blf.dimensions(font, text)[0])):
                blf.position(font, left, y, 0)
                blf.draw(font, part)
                y += 18 * scale
        gpu.state.blend_set("NONE")
    except (ReferenceError, AttributeError, ImportError, ValueError, SystemError):
        return


def _guide_handlers(on: bool) -> None:
    if bpy.app.background:
        return
    space = bpy.types.SpaceView3D
    if on:
        if _DRAW["guide_view"] is None:
            _DRAW["guide_view"] = space.draw_handler_add(_draw_guide_view, (), "WINDOW", "POST_VIEW")
        if _DRAW["guide_pixel"] is None:
            _DRAW["guide_pixel"] = space.draw_handler_add(_draw_guide_pixel, (), "WINDOW", "POST_PIXEL")
    else:
        for key in ("guide_view", "guide_pixel"):
            if _DRAW[key] is not None:
                space.draw_handler_remove(_DRAW[key], "WINDOW")
                _DRAW[key] = None


def _register_drawing() -> None:
    if _DRAW["markers"] is None and not bpy.app.background:
        _DRAW["markers"] = bpy.types.SpaceView3D.draw_handler_add(_draw_markers, (), "WINDOW", "POST_VIEW")


def _unregister_drawing() -> None:
    _guide_handlers(False)
    if _DRAW["markers"] is not None:
        bpy.types.SpaceView3D.draw_handler_remove(_DRAW["markers"], "WINDOW")
        _DRAW["markers"] = None
    _DRAW["shaders"] = {}


# --------------------------------------------------------------------------------------------------
# The elbow and knee that follow their limb
# --------------------------------------------------------------------------------------------------


def follow_limbs(scene: Any) -> bool:
    """Moves an elbow or a knee with its limb when the user moved a wrist, shoulder, ankle or hip marker. True when
    it moved one."""
    settings_ = getattr(scene, "dct_ped", None)
    collection = getattr(settings_, "character", None) if settings_ is not None else None
    if collection is None or RUNTIME.writing:
        return False
    key = ident(collection)
    current = ph.read_markers(collection)
    before = RUNTIME.last_markers.get(key)
    RUNTIME.last_markers[key] = current
    if before is None or not settings_.follow:
        return False
    moves = ped.moved_middles(before, current)
    if not moves:
        return False
    from mathutils import Matrix, Vector

    objects = ph.marker_objects(collection)
    RUNTIME.writing = True
    try:
        for name, point in moves.items():
            objects[name].matrix_world = Matrix.Translation(Vector(point))
            current[name] = point
    finally:
        RUNTIME.writing = False
    RUNTIME.last_markers[key] = current
    return True


@persistent
def _on_undo_redo(*_args) -> None:
    """Undo and redo replace the markers: what was last seen of them no longer tells what the user moved."""
    RUNTIME.last_markers.clear()
    RUNTIME.facts.clear()


@persistent
def _on_depsgraph_update(scene, depsgraph) -> None:
    try:
        if RUNTIME.writing or getattr(getattr(scene, "dct_link", None), "workspace", "CLOTHING") != "PED":
            return
        if any(isinstance(update.id, bpy.types.Object) and update.id.get(ph.MARKER) and update.is_updated_transform
               for update in depsgraph.updates):
            follow_limbs(scene)
    except Exception:  # noqa: BLE001 - never let a handler problem repeat on every update
        traceback.print_exc()


# --------------------------------------------------------------------------------------------------
# Panels
# --------------------------------------------------------------------------------------------------


class DCTLINK_PT_ped(ui._SubPanel, Panel):
    bl_label = EN["ped.panel"]
    bl_order = 0

    @classmethod
    def poll(cls, context):
        return (state.controller is not None and getattr(context.scene, "dct_ped", None) is not None
                and ui.workspace(context) == "PED")

    def draw_header(self, context):
        self.layout.label(text="", icon="OUTLINER_OB_ARMATURE")

    def draw(self, context):
        draw_main(self.layout, context)


CLASSES = (
    DCTLINK_PG_ped,
    DCTLINK_OT_ped_use_selected,
    DCTLINK_OT_ped_apply_transforms,
    DCTLINK_OT_ped_apply_modifiers,
    DCTLINK_OT_ped_remove_old_rig,
    DCTLINK_OT_ped_remove_shape_keys,
    DCTLINK_OT_ped_scale,
    DCTLINK_OT_ped_turn,
    DCTLINK_OT_ped_to_origin,
    DCTLINK_OT_ped_confirm_facing,
    DCTLINK_OT_ped_auto_markers,
    DCTLINK_OT_ped_from_rig,
    DCTLINK_OT_ped_mirror,
    DCTLINK_OT_ped_show_markers,
    DCTLINK_OT_ped_guide,
    DCTLINK_OT_ped_refresh_templates,
    DCTLINK_OT_ped_use_template,
    DCTLINK_MT_ped_templates,
    DCTLINK_OT_ped_rig,
    DCTLINK_OT_ped_cancel_rig,
    DCTLINK_OT_ped_apply_rig,
    DCTLINK_OT_ped_use_refined,
    DCTLINK_OT_ped_discard_rig,
    DCTLINK_OT_ped_previous_rig,
    DCTLINK_OT_ped_remove_rig,
    DCTLINK_OT_ped_pose,
    DCTLINK_OT_ped_run_checks,
    DCTLINK_OT_ped_show_finding,
    DCTLINK_OT_ped_send,
    DCTLINK_OT_ped_cancel_send,
    DCTLINK_PT_ped,
)


def register() -> None:
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    bpy.types.Scene.dct_ped = PointerProperty(type=DCTLINK_PG_ped)
    bpy.types.Object.dct_ped_role = EnumProperty(name=EN["ped.prop.role"], items=ROLE_ITEMS, default="auto",
                                                 description=EN["ped.prop.role.desc"], translation_context=CONTEXT)
    bpy.app.handlers.depsgraph_update_post.append(_on_depsgraph_update)
    bpy.app.handlers.undo_post.append(_on_undo_redo)
    bpy.app.handlers.redo_post.append(_on_undo_redo)
    _register_drawing()


def unregister() -> None:
    _unregister_drawing()
    if _on_depsgraph_update in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(_on_depsgraph_update)
    for handlers in (bpy.app.handlers.undo_post, bpy.app.handlers.redo_post):
        if _on_undo_redo in handlers:
            handlers.remove(_on_undo_redo)
    for timer in (_redraw_later, _auto_templates):
        if bpy.app.timers.is_registered(timer):
            bpy.app.timers.unregister(timer)
    RUNTIME.guide = None
    del bpy.types.Object.dct_ped_role
    del bpy.types.Scene.dct_ped
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)


def on_created(created: Dict[str, str]) -> None:
    """Durty Cloth Tool created a project from a character: the character keeps it (the panel says it is done)."""
    for collection in bpy.data.collections:
        if collection.get(ph.CHARACTER) == created.get("character"):
            collection[ph.SENT] = json.dumps({k: created.get(k, "") for k in ("name", "model", "template")})
    host.push_undo(strings.english(msg("ped.op.send")))  # so Ctrl+Z never takes the note of the project back
    host.redraw()


def on_load_pre() -> None:
    """Another file is opened: the results shown and a waiting rig belong to the old one."""
    RUNTIME.notice = None
    RUNTIME.facts.clear()
    RUNTIME.marker_notes.clear()
    RUNTIME.findings.clear()
    RUNTIME.last_markers.clear()
    RUNTIME.guide = None
    link = peds()
    if link is not None:
        link.forget()
