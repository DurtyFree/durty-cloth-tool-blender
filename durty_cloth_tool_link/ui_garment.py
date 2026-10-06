# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2026 Schmid Software Solutions (https://schmid-software.de)
"""Garment Fitting (Experimental) in the DCT tab: the settings, operators and panel of the local garment tools.

The panel is the DCT tab's Garment Fitting view (Work On), with the next step in its first line and five numbered
stages, like Custom Ped's: Setup (gender, garment type, avatar, source pose, the garment and the freemode body), Fit
(markers, Align to Body, Fit to Body), Fix (Run Fit Check and Push Out of Body, with the problem colours, the region
tools, sculpting by hand and the tear check in closed sections), Game Ready (prepare, combine materials, the freemode
skeleton and the weights, levels of detail, the local checks) and Add to Project (the add of the garment as a new cloth
of the open project). The stage that holds the next step opens and the finished ones fold; each header says how far
its stage is. The button of the next step is the large one, a finished step's button has a tick, and settings that
rarely change sit in closed Options sections. Every operator that changes a mesh can be undone; the garment keeps up to
three backups for Back One Step and Restore Pre-fit, in a closed section after the stages.
"""

from __future__ import annotations

import math
import pathlib
import shutil
import threading
import time
import traceback
from typing import Any, Callable, Dict, List, NamedTuple, Optional, Tuple

import bpy
import numpy as np
from bpy.props import (BoolProperty, CollectionProperty, EnumProperty, FloatProperty, FloatVectorProperty, IntProperty,
                       PointerProperty, StringProperty)
from bpy.types import Menu, Operator, Panel, PropertyGroup

from . import garment, garment_add, garment_avatars, garment_body, garment_fit, host, link, state, strings, ui
from . import settings as addon_settings
from . import garment_dct as gdct
from . import garment_host as gh
from .dct_link import auth, fit, protocol
from .strings import CONTEXT, EN, Msg, UserError, msg, t
from .ui import GAP, GAP_SMALL, guide, heading, info_button, operator, primary, reason_text, subtext, wrapped

#: Where the pose presets are kept, in the add-on's user folder.
PRESETS_FOLDER = "garment-presets"
SEVERITY_ICONS = {"error": "CANCEL", "warning": "ERROR", "info": "INFO"}
PROBLEM_ICONS = {"inside": "COLORSET_01_VEC", "close": "COLORSET_09_VEC", "stretched": "COLORSET_06_VEC",
                 "floating": "COLORSET_04_VEC"}


class _Runtime:
    """What the panels show that is not saved: the last result, a running body download, the tear check, the add."""

    def __init__(self) -> None:
        self.notice: Optional[link.Notice] = None
        self.download: Optional[garment_body.BodyDownload] = None
        self.download_scene: Optional[str] = None
        self.tears: Optional[Dict[str, Any]] = None
        #: The garment the tear check result belongs to (its name).
        self.tears_of: Optional[str] = None
        #: A step that waits for Durty Cloth Tool's skeleton template (:class:`Job`).
        self.job: Optional["Job"] = None
        #: The add while the add-on prepares it (:class:`AddJob`), before Durty Cloth Tool is asked.
        self.add_job: Optional["AddJob"] = None
        #: What blocks the add (from its checks), and what the add-on advises against without blocking it.
        self.add_problems: List[Msg] = []
        self.add_warnings: List[Msg] = []
        #: The garment the add's checks and outcome belong to (its session uid).
        self.add_of: Optional[int] = None
        #: What Auto Markers guessed rather than found, per garment (its session uid).
        self.marker_notes: Dict[int, Tuple[str, ...]] = {}
        #: How the last Fit to Body or Transfer Weights ended (level and text per line), which of the two it was, and
        #: the garment it belongs to (its session uid).
        self.fit_lines: List[Tuple[str, Msg]] = []
        self.fit_operation: Optional[str] = None
        self.fit_of: Optional[int] = None
        #: The step running from the panel stage by stage (Prepare Garment, Combine Materials), by its title: the other
        #: garment tools wait for it.
        self.stepping: Optional[str] = None
        #: The garment's flow while the panel draws (computed once per draw).
        self.flow: Optional[garment.FlowState] = None
        #: The stage that was open at the last draw, and the ids of the stage sections (see :func:`_draw_main`). This
        #: is the add-on's own memory, not Blender data, so the panel may change it while it draws.
        self.opened: Optional[str] = None
        self.layout_generation = 0
        self.layout_session = int(time.time()) % 1000000
        self.redraw: Callable[[], None] = lambda: None


RUNTIME = _Runtime()


def notify(level: str, message: Msg) -> None:
    RUNTIME.notice = link.Notice(level, message)


def props(context: Any) -> Any:
    return context.scene.dct_garment


def current_garment(context: Any) -> Optional[Any]:
    obj = getattr(getattr(context, "scene", None), "dct_garment", None)
    obj = getattr(obj, "garment", None)
    try:
        return obj if obj is not None and obj.type == "MESH" else None
    except ReferenceError:
        return None


def valid_body(context: Any) -> Optional[Any]:
    body = props(context).body
    return body if gh.body_problem(context, body) is None else None


_TEMPLATE_JOINTS: Dict[Tuple[str, int], Dict[str, Any]] = {}


def template_joints(gender: str) -> Optional[Dict[str, Any]]:
    """The joints of Durty Cloth Tool's skeleton template of ``gender`` when it was sent already (kept per template)."""
    ctrl = state.controller
    template = ctrl.skeletons.get(gender) if ctrl is not None else None
    if template is None:
        return None
    key = (gender, id(template))
    if key not in _TEMPLATE_JOINTS:
        try:
            _TEMPLATE_JOINTS.clear()
            _TEMPLATE_JOINTS[key] = garment_add.template_joints(template.files[0].data, garment.JOINTS)
        except garment_add.TemplateError:
            return None
    return _TEMPLATE_JOINTS[key]


def body_gender(context: Any, body: Any) -> str:
    tag = body.get(gh.BODY_TAG) if body is not None else None
    return tag if tag in garment.GENDERS else props(context).gender


def joints(context: Any) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """The body's joints and where they came from (``hosted``, ``dct`` or ``estimate``), or ``(None, None)`` without a
    body."""
    body = valid_body(context)
    if body is None:
        return None, None
    gender = body_gender(context, body)
    try:
        return gh.body_joints(body, gender, template_joints(gender))
    except garment.MarkerError:
        return None, None


# --------------------------------------------------------------------------------------------------
# Settings
# --------------------------------------------------------------------------------------------------


def _items(prefix: str, ids) -> tuple:
    return tuple((value, EN[f"{prefix}.{value}"], EN[f"{prefix}.{value}.desc"]) for value in ids)


GENDER_ITEMS = tuple((g, EN[f"gender.{g}"], EN[f"garment.gender.{g}.desc"]) for g in garment.GENDERS)
#: Every slot with its number (Blender keeps the chosen one by it); a type offers only its own slots.
SLOT_ITEMS = {slot: (slot, EN[f"garment.slot.{slot}"], EN[f"garment.slot.{slot}.desc"], garment.SLOTS.index(slot))
              for slot in garment.SLOTS}
POSE_ITEMS = _items("garment.pose", garment.SOURCE_POSES)
#: The avatars a garment may have been made on: unknown (Auto Markers reads the garment), the one imported with it,
#: and the stock avatars measured so far.
AVATAR_IDS = ("detect", "file", *garment_avatars.AVATARS)
AVATAR_ITEMS = tuple((name, EN[f"garment.avatar.{name}"], EN[f"garment.avatar.{name}.desc"], index)
                     for index, name in enumerate(AVATAR_IDS))
REGION_ITEMS = tuple((r, EN[f"garment.region.{r}"], EN["garment.region.desc"]) for r in garment.REGIONS)
UNIT_ITEMS = tuple((u, EN[f"garment.unit.{u}"], EN["garment.unit.desc"]) for u in ("auto", *garment.UNITS))
#: The garment types in the picker's groups (Blender keeps a dynamic enum's strings only while they are referenced).
CATEGORY_ITEMS = [None if c is None else (c, EN[f"garment.category.{c}"], EN[f"garment.category.{c}.desc"],
                                          garment.CATEGORIES.index(c)) for c in garment.CATEGORY_MENU]
#: The slots each type offers.
TYPE_SLOT_ITEMS = {c: [SLOT_ITEMS[slot] for slot in garment.slots_for(c)] for c in garment.CATEGORIES}
SIZE_ITEMS = (("2048", "2048", EN["garment.size.desc"]), ("4096", "4096", EN["garment.size.desc"]))
#: The ped shader's vertex colours most clothing uses (as Sollumz's clothing tutorial gives them): Color 1 #FF8000,
#: full ambient light and a medium reflection; Color 2 black with no alpha, no vertex wind and no sweat. Both can be
#: changed under Prepare Garment.
DEFAULT_COLOUR_1 = (1.0, 128.0 / 255.0, 0.0, 1.0)
DEFAULT_COLOUR_2 = (0.0, 0.0, 0.0, 0.0)


def _category_items(self: Any, context: Any) -> list:
    return CATEGORY_ITEMS


def _slot_items(self: Any, context: Any) -> list:
    return TYPE_SLOT_ITEMS.get(self.category, TYPE_SLOT_ITEMS["tshirt"])


def _keep_on_garment(settings_: Any) -> None:
    """Each garment keeps its own type, slot, avatar, skin and front, so they come back when it is chosen again."""
    obj = settings_.garment
    try:
        if obj is not None and obj.type == "MESH":
            obj[gh.TYPE_TAG] = settings_.category
            obj[gh.SLOT_TAG] = settings_.slot
            obj[AVATAR_TAG] = settings_.avatar
            obj[SKIN_TAG] = bool(settings_.skin)
            obj[OPEN_FRONT_TAG] = bool(settings_.open_front)
    except (ReferenceError, AttributeError, TypeError):
        pass  # the garment is gone, or this property is set while Blender reads a file


def _choice_changed(self: Any, context: Any) -> None:
    _keep_on_garment(self)


def _category_changed(self: Any, context: Any) -> None:
    """Another type: its usual slot (unless the slot chosen fits it too), its skin and front."""
    kind = garment.garment_type(self.category)
    if self.slot not in kind.slots:
        self.slot = kind.slots[0]
    self.skin = kind.skin
    self.open_front = kind.open_front
    _keep_on_garment(self)


def _avatar_changed(self: Any, context: Any) -> None:
    stock = garment_avatars.avatar(self.avatar)
    if stock is not None:
        self.source_pose = stock.pose
    _keep_on_garment(self)


#: On the garment: the avatar chosen for it, whether it shows skin and whether its front is worn open.
AVATAR_TAG = "dct_avatar"
SKIN_TAG = "dct_skin"
OPEN_FRONT_TAG = "dct_open_front"


def _marker_size_changed(self: Any, context: Any) -> None:
    gh.resize_markers(context.scene, self.marker_size)


def _poll_mesh(self: Any, obj: Any) -> bool:
    return obj.type == "MESH" and not obj.get(gh.BODY_TAG)


def _poll_body(self: Any, obj: Any) -> bool:
    return obj.type == "MESH"


def _garment_changed(self: Any, context: Any) -> None:
    """Another garment: the add's name and colour variations start again from it, and only its markers show."""
    obj = self.garment
    self.item_name = obj.name[: protocol.MAX_TEXT_LENGTH] if obj is not None else ""
    self.first_title = ""
    self.variations.clear()
    if obj is not None:
        category, slot, avatar = obj.get(gh.TYPE_TAG), obj.get(gh.SLOT_TAG), obj.get(AVATAR_TAG)
        skin, open_front = obj.get(SKIN_TAG), obj.get(OPEN_FRONT_TAG)
        # The type sets its usual slot, skin and front; what the garment kept wins over them.
        self.category = category if category in garment.CATEGORIES else self.category
        if slot in garment.slots_for(self.category):
            self.slot = slot
        if skin is not None:
            self.skin = bool(skin)
        if open_front is not None:
            self.open_front = bool(open_front)
        # A garment without an avatar of its own never takes the last one's: its markers would come from elsewhere.
        self.avatar = avatar if avatar in AVATAR_IDS else ("file" if obj.get(gh.AVATAR_MARKERS) else "detect")
        _keep_on_garment(self)
    RUNTIME.add_problems, RUNTIME.add_warnings, RUNTIME.add_of = [], [], None
    layer = getattr(context, "view_layer", None)
    if layer is not None:
        gh.show_markers_of(context.scene, layer, obj)


def _variation_image_changed(self: Any, context: Any) -> None:
    if self.image is not None and not self.title.strip():
        self.title = self.image.name[: protocol.MAX_TEXT_LENGTH]


class DCTLINK_PG_variation(PropertyGroup):
    """One more colour variation of the cloth: an image and the name it gets in Durty Cloth Tool."""

    image: PointerProperty(name=EN["add.prop.image"], type=bpy.types.Image, update=_variation_image_changed,
                           description=EN["add.prop.image.desc"], translation_context=CONTEXT)
    title: StringProperty(name=EN["add.prop.variation-name"], maxlen=protocol.MAX_TEXT_LENGTH,
                          description=EN["add.prop.variation-name.desc"], translation_context=CONTEXT)


class DCTLINK_PG_garment(PropertyGroup):
    garment: PointerProperty(name=EN["garment.prop.garment"], type=bpy.types.Object, poll=_poll_mesh,
                             update=_garment_changed,
                             description=EN["garment.prop.garment.desc"], translation_context=CONTEXT)
    body: PointerProperty(name=EN["garment.prop.body"], type=bpy.types.Object, poll=_poll_body,
                          description=EN["garment.prop.body.desc"], translation_context=CONTEXT)
    gender: EnumProperty(name=EN["garment.prop.gender"], items=GENDER_ITEMS, default="male",
                         description=EN["garment.prop.gender.desc"], translation_context=CONTEXT)
    slot: EnumProperty(name=EN["garment.prop.slot"], items=_slot_items, default=garment.SLOTS.index("jbib"),
                       update=_choice_changed, description=EN["garment.prop.slot.desc"], translation_context=CONTEXT)
    category: EnumProperty(name=EN["garment.prop.category"], items=_category_items,
                           default=garment.CATEGORIES.index("tshirt"), update=_category_changed,
                           description=EN["garment.prop.category.desc"], translation_context=CONTEXT)
    avatar: EnumProperty(name=EN["garment.prop.avatar"], items=AVATAR_ITEMS, default="detect", update=_avatar_changed,
                         description=EN["garment.prop.avatar.desc"], translation_context=CONTEXT)
    open_front: BoolProperty(name=EN["garment.prop.open-front"], default=False, update=_choice_changed,
                             description=EN["garment.prop.open-front.desc"], translation_context=CONTEXT)
    source_pose: EnumProperty(name=EN["garment.prop.pose"], items=POSE_ITEMS, default="a_pose",
                              description=EN["garment.prop.pose.desc"], translation_context=CONTEXT)
    marker_size: FloatProperty(name=EN["garment.prop.marker-size"], default=0.03, min=0.005, max=0.2,
                               subtype="DISTANCE", unit="LENGTH", update=_marker_size_changed,
                               description=EN["garment.prop.marker-size.desc"], translation_context=CONTEXT)
    keep_size: BoolProperty(name=EN["garment.prop.keep-size"], default=True,
                            description=EN["garment.prop.keep-size.desc"], translation_context=CONTEXT)
    arm_angle: FloatProperty(name=EN["garment.prop.arm-angle"], default=math.radians(40.0), min=0.0,
                             max=math.radians(80.0), subtype="ANGLE", unit="ROTATION",
                             description=EN["garment.prop.arm-angle.desc"], translation_context=CONTEXT)
    push_gap: FloatProperty(name=EN["garment.prop.gap"], default=4.0, min=0.0, max=50.0, precision=1,
                            description=EN["garment.prop.push-gap.desc"], translation_context=CONTEXT)
    region: EnumProperty(name=EN["garment.prop.region"], items=REGION_ITEMS, default="shoulders",
                         description=EN["garment.prop.region.desc"], translation_context=CONTEXT)
    snug_gap: FloatProperty(name=EN["garment.prop.gap"], default=8.0, min=0.0, max=80.0, precision=1,
                            description=EN["garment.prop.snug-gap.desc"], translation_context=CONTEXT)
    amount: FloatProperty(name=EN["garment.prop.amount"], default=0.8, min=0.0, max=1.0, subtype="FACTOR",
                          description=EN["garment.prop.amount.desc"], translation_context=CONTEXT)
    sculpt_radius: FloatProperty(name=EN["garment.prop.radius"], default=6.0, min=0.5, max=50.0, precision=1,
                                 description=EN["garment.prop.radius.desc"], translation_context=CONTEXT)
    sculpt_strength: FloatProperty(name=EN["garment.prop.strength"], default=0.5, min=0.0, max=1.0,
                                   subtype="FACTOR", description=EN["garment.prop.strength.desc"],
                                   translation_context=CONTEXT)
    sculpt_mirror: BoolProperty(name=EN["garment.prop.mirror"], default=True,
                                description=EN["garment.prop.mirror.desc"], translation_context=CONTEXT)
    sculpt_keep_out: BoolProperty(name=EN["garment.prop.keep-out"], default=True,
                                  description=EN["garment.prop.keep-out.desc"], translation_context=CONTEXT)
    weld: FloatProperty(name=EN["garment.prop.weld"], default=2.0, min=0.0, max=20.0, precision=1,
                        description=EN["garment.prop.weld.desc"], translation_context=CONTEXT)
    colour_1: FloatVectorProperty(name=EN["garment.prop.colour-1"], size=4, subtype="COLOR_GAMMA", min=0.0,
                                  max=1.0, default=DEFAULT_COLOUR_1, description=EN["garment.prop.colour-1.desc"],
                                  translation_context=CONTEXT)
    colour_2: FloatVectorProperty(name=EN["garment.prop.colour-2"], size=4, subtype="COLOR_GAMMA", min=0.0,
                                  max=1.0, default=DEFAULT_COLOUR_2, description=EN["garment.prop.colour-2.desc"],
                                  translation_context=CONTEXT)
    overwrite_colours: BoolProperty(name=EN["garment.prop.overwrite"], default=False,
                                    description=EN["garment.prop.overwrite.desc"], translation_context=CONTEXT)
    texture_size: EnumProperty(name=EN["garment.prop.size"], items=SIZE_ITEMS, default="2048",
                               description=EN["garment.size.desc"], translation_context=CONTEXT)
    cut_strips: BoolProperty(name=EN["garment.prop.cut"], default=True, description=EN["garment.prop.cut.desc"],
                             translation_context=CONTEXT)
    fit_clearance: FloatProperty(name=EN["garment.prop.clearance"], default=3.0, min=0.0, max=20.0, precision=1,
                                 description=EN["garment.prop.clearance.desc"], translation_context=CONTEXT)
    fit_push: BoolProperty(name=EN["garment.prop.service-push"], default=True,
                           description=EN["garment.prop.service-push.desc"], translation_context=CONTEXT)
    fit_max_push: FloatProperty(name=EN["garment.prop.max-push"], default=30.0, min=1.0, max=100.0, precision=0,
                                description=EN["garment.prop.max-push.desc"], translation_context=CONTEXT)
    fit_seam_gap: FloatProperty(name=EN["garment.prop.seam-gap"], default=1.5, min=0.0, max=3.0, precision=2,
                                description=EN["garment.prop.seam-gap.desc"], translation_context=CONTEXT)
    fit_proportions: BoolProperty(name=EN["garment.prop.proportions"], default=False,
                                  description=EN["garment.prop.proportions.desc"], translation_context=CONTEXT)
    lod_medium: IntProperty(name=EN["garment.prop.lod-medium"], default=0, min=0, max=200000,
                            description=EN["garment.prop.lod.desc"], translation_context=CONTEXT)
    lod_low: IntProperty(name=EN["garment.prop.lod-low"], default=0, min=0, max=100000,
                         description=EN["garment.prop.lod.desc"], translation_context=CONTEXT)
    item_name: StringProperty(name=EN["add.prop.name"], maxlen=protocol.MAX_TEXT_LENGTH,
                              description=EN["add.prop.name.desc"], translation_context=CONTEXT)
    skin: BoolProperty(name=EN["add.prop.skin"], default=False, update=_choice_changed,
                       description=EN["add.prop.skin.desc"], translation_context=CONTEXT)
    first_title: StringProperty(name=EN["add.prop.variation-name"], maxlen=protocol.MAX_TEXT_LENGTH,
                                description=EN["add.prop.first-name.desc"], translation_context=CONTEXT)
    variations: CollectionProperty(type=DCTLINK_PG_variation)


# --------------------------------------------------------------------------------------------------
# Why a button is unavailable
# --------------------------------------------------------------------------------------------------


def _refuse(cls: Any, reason: Optional[Msg]) -> bool:
    if RUNTIME.stepping is not None:
        reason = msg("garment.why.step-running", step=msg(RUNTIME.stepping))  # it changes the garment meanwhile
    return ui._refuse(cls, reason)


def _garment_reason(context: Any, *, sculpting_ok: bool = False) -> Optional[Msg]:
    if state.controller is None:
        return msg("notice.not-ready")
    return gh.garment_problem(context, current_garment(context), sculpting_ok=sculpting_ok)


def _body_reason(context: Any) -> Optional[Msg]:
    return gh.body_problem(context, props(context).body)


def _is_prop(context: Any) -> bool:
    return garment.is_prop(props(context).category)


def _aligned(context: Any) -> bool:
    """The garment sits on the body: aligned (and no marker moved since), a type without markers, or a prop snapped
    to its anchor. Prepare Garment does not count: a garment prepared without Align to Body was never put on the
    body."""
    obj = current_garment(context)
    category = props(context).category
    if garment.is_prop(category):
        return gh.flag(obj, "dct_aligned")  # markers do not count: a prop has none
    return not garment.markers_for(category) or gh.aligned(obj, context.scene)


def _fit_reason(context: Any, *, sculpting_ok: bool = False) -> Optional[Msg]:
    """A step that measures against the body: the garment, the body, and the garment aligned to the body (edits on a
    garment still on its maker's avatar would squash it towards a body it does not sit on). Props keep their shape."""
    reason = _garment_reason(context, sculpting_ok=sculpting_ok) or _body_reason(context)
    if reason is None and _is_prop(context):
        reason = msg("garment.why.prop-fix")
    if reason is None and not _aligned(context):
        reason = msg("garment.why.align-first")
    return reason


def _markers_reason(context: Any) -> Optional[Msg]:
    reason = _garment_reason(context)
    settings_ = props(context)
    if reason is None and not garment.markers_for(settings_.category):
        reason = msg("garment.why.no-markers")
    if reason is None and settings_.avatar == "detect" and not garment.detects_markers(settings_.category):
        reason = _body_reason(context)  # the markers start on the body's joints
    return reason


def _align_reason(context: Any) -> Optional[Msg]:
    reason = _markers_reason(context) or _body_reason(context)
    if reason is None:
        expected = garment.markers_for(props(context).category)
        if any(name not in gh.marker_objects(context.scene) for name in expected):
            reason = msg("garment.why.markers")
    if reason is None and RUNTIME.job is not None:
        reason = msg("add.why.fetching")
    return reason


_KEPT: Dict[str, Any] = {"at": 0.0, "gender": None, "kept": False}


def _body_kept(gender: str) -> bool:
    """Whether a body of this gender was downloaded before (looked up at most every few seconds: panels redraw
    often)."""
    now = time.monotonic()
    if _KEPT["gender"] != gender or now - _KEPT["at"] > 3.0:
        try:
            kept = _kept_body(gender) is not None
        except (OSError, ValueError, TypeError):  # an unreadable folder counts as nothing kept
            kept = False
        _KEPT.update(at=now, gender=gender, kept=kept)
    return bool(_KEPT["kept"])


def _kept_body(gender: str) -> Optional[garment_body.BodyResult]:
    files = garment_body.body_files(gender, tuple(bpy.app.version))
    return garment_body.cached_body(host.data_dir(state.PACKAGE), gender, files=files)


def _download_reason(context: Any) -> Optional[Msg]:
    """Why Add Freemode Body is unavailable: a body kept from before needs neither online access nor a sign-in."""
    if state.controller is None:
        return msg("notice.not-ready")
    if RUNTIME.download is not None:
        return msg("garment.why.downloading")
    if _body_kept(props(context).gender):
        return None
    if not host.online_access():
        return msg("notice.online-off")
    ctrl = state.get()
    if ctrl.user_name is None or ctrl.signed_out:
        return msg("garment.why.sign-in")
    return None


def _object_mode_reason(context: Any) -> Optional[Msg]:
    obj = getattr(context, "active_object", None)
    if obj is not None and obj.mode != "OBJECT":
        return msg("garment.why.object-mode")
    return None


# --------------------------------------------------------------------------------------------------
# Operators
# --------------------------------------------------------------------------------------------------

EXPECTED = ui.EXPECTED_FAILURES + (garment.MarkerError, garment_body.BodyError)


class _Op(Operator):
    bl_translation_context = CONTEXT


class _MeshOp(_Op):
    """An operator that changes the garment: it can be undone, and reports a failure instead of raising it. A step
    that fails halfway puts the garment back from the backup it made first."""

    bl_options = {"REGISTER", "UNDO"}

    def run(self, context: Any, action: Callable[[], Optional[Msg]], backup: bool = True) -> set:
        obj = current_garment(context)
        backed_up = False
        try:
            if backup and obj is not None:
                gh.backup(obj)
                backed_up = True
            message = action()
        except Exception as exc:  # noqa: BLE001 - every failure is reported, and a half-made change undone
            if not isinstance(exc, EXPECTED):
                traceback.print_exc()
            if backed_up:
                try:
                    if obj.mode != "OBJECT":
                        bpy.ops.object.mode_set(mode="OBJECT")
                    gh.roll_back(obj)  # the step's own backup holds the garment from before it
                except Exception:  # noqa: BLE001 - the rollback is best effort; Ctrl+Z still has the garment
                    traceback.print_exc()
            failure = _failure_message(exc)
            self.report({"ERROR"}, strings.text(failure))
            notify("ERROR", failure)
            host.redraw()
            return {"CANCELLED"}
        level = "INFO"
        if isinstance(message, tuple) and not isinstance(message, Msg):  # (level, message)
            level, message = message
        if message is not None:
            self.report({level}, strings.text(message))
            notify(level, message)
        host.redraw()
        return {"FINISHED"}


class _SteppedOp(_MeshOp):
    """A step that takes a while (Prepare Garment, Combine Materials): run from the panel it goes stage by stage on a
    timer, shows each stage in the status bar and stops at Esc, putting the garment back from the backup it made
    first. Run from a script it runs at once. Subclasses give :meth:`steps` (a generator of ``(stage text key, done,
    total)`` that returns the step's result) and :meth:`finished` (the result's message)."""

    title = "garment.op.prepare"
    _steps: Any = None
    _timer: Any = None
    _garment: Any = None

    def steps(self, context: Any) -> Any:
        raise NotImplementedError

    def finished(self, context: Any, result: Any) -> Any:
        raise NotImplementedError

    def execute(self, context):
        return self.run(context, lambda: self.finished(context, gh.run_steps(self.steps(context))))

    def invoke(self, context, event):
        obj = current_garment(context)
        gh.backup(obj)
        self._garment = obj
        self._steps = self.steps(bpy.context)
        self._timer = context.window_manager.event_timer_add(0.05, window=context.window)
        context.window_manager.progress_begin(0, 100)
        context.window_manager.modal_handler_add(self)
        RUNTIME.stepping = self.title
        host.redraw()
        return {"RUNNING_MODAL"}

    def cancel(self, context):
        """Blender ends the step (another file opened, the window closed): the garment goes back as before."""
        self._fail(context, msg("garment.done.step-cancelled", step=msg(self.title)), "INFO")

    def _end(self, context: Any) -> None:
        RUNTIME.stepping = None
        if self._timer is not None:
            context.window_manager.event_timer_remove(self._timer)
            self._timer = None
        context.window_manager.progress_end()
        try:
            context.workspace.status_text_set(None)
        except (AttributeError, TypeError):
            pass  # no status bar to clear (background)
        host.redraw()

    def _fail(self, context: Any, failure: Msg, level: str = "ERROR") -> set:
        if self._steps is None:
            return {"CANCELLED"}  # ended already
        self._steps.close()  # restores what the step changed around the garment (bake settings, materials)
        self._steps = None
        obj = self._garment
        try:
            if obj.mode != "OBJECT":
                bpy.ops.object.mode_set(mode="OBJECT")
            gh.roll_back(obj)
        except Exception:  # noqa: BLE001 - the rollback is best effort; Ctrl+Z still has the garment
            traceback.print_exc()
        self._end(context)
        self.report({"WARNING" if level == "INFO" else level}, strings.text(failure))
        notify(level, failure)
        return {"CANCELLED"}

    def modal(self, context, event):
        if event.type == "ESC" and event.value == "PRESS":
            return self._fail(context, msg("garment.done.step-cancelled", step=msg(self.title)), "INFO")
        if event.type != "TIMER":
            return {"PASS_THROUGH"}
        try:
            stage, done, total = next(self._steps)
        except StopIteration as stop:
            self._steps = None
            self._end(context)
            message = self.finished(context, stop.value)
            level = "INFO"
            if isinstance(message, tuple) and not isinstance(message, Msg):  # (level, message)
                level, message = message
            self.report({level}, strings.text(message))
            notify(level, message)
            return {"FINISHED"}
        except Exception as exc:  # noqa: BLE001 - every failure is reported, and the half-made change undone
            if not isinstance(exc, EXPECTED):
                traceback.print_exc()
            return self._fail(context, _failure_message(exc))
        context.window_manager.progress_update(int(100 * done / max(1, total)))
        try:
            context.workspace.status_text_set(t("garment.step.status", step=msg(self.title), stage=msg(stage),
                                                done=done + 1, total=total))
        except (AttributeError, TypeError):
            pass  # no status bar (background)
        host.redraw()
        return {"RUNNING_MODAL"}


def _use_reason(context: Any) -> Optional[Msg]:
    obj = getattr(context, "active_object", None)
    if state.controller is None:
        return msg("notice.not-ready")
    if obj is None or obj.type != "MESH":
        return msg("garment.why.select-mesh")
    if obj.get(gh.BODY_TAG):
        return msg("garment.why.is-body")
    return None


def _failure_message(exc: BaseException) -> Msg:
    """What the panel says about a step that failed."""
    if isinstance(exc, garment.MarkerError):
        return msg(f"garment.marker-error.{exc.code}")
    if isinstance(exc, garment_body.BodyError):
        return msg(f"garment.body.{exc.code}")
    if isinstance(exc, UserError):
        return exc.message
    if isinstance(exc, OSError):
        return msg("notice.file-error", detail=str(exc.strerror or exc))
    return msg("notice.unexpected", detail=ui._report_text(exc))


class DCTLINK_OT_fit_use_garment(_MeshOp):
    bl_idname = "dct_link.fit_use_garment"
    bl_label = EN["garment.op.use"]
    bl_description = EN["garment.op.use.desc"]

    @classmethod
    def poll(cls, context):
        return _refuse(cls, _use_reason(context))

    def execute(self, context):
        obj = context.active_object

        def use() -> Msg:
            obj[gh.GARMENT_TAG] = 1
            gh.ensure_garment_id(obj)
            props(context).garment = obj
            return msg("garment.done.use", name=obj.name)

        return self.run(context, use, backup=False)


class DCTLINK_OT_fit_import_garment(_MeshOp):
    bl_idname = "dct_link.fit_import_garment"
    bl_label = EN["garment.op.import"]
    bl_description = EN["garment.op.import.desc"]

    filepath: StringProperty(subtype="FILE_PATH", options={"SKIP_SAVE"})
    filter_glob: StringProperty(default="*.fbx;*.obj;*.glb;*.gltf", options={"HIDDEN"})
    ground: BoolProperty(name=EN["garment.prop.ground"], default=True, description=EN["garment.prop.ground.desc"],
                         translation_context=CONTEXT)
    unit: EnumProperty(name=EN["garment.prop.unit"], items=UNIT_ITEMS, default="auto",
                       description=EN["garment.prop.unit.desc"], translation_context=CONTEXT)
    orient: BoolProperty(name=EN["garment.prop.orient"], default=True, description=EN["garment.prop.orient.desc"],
                         translation_context=CONTEXT)

    @classmethod
    def poll(cls, context):
        reason = None if state.controller is not None else msg("notice.not-ready")
        return _refuse(cls, reason or _object_mode_reason(context))

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def draw(self, context):
        ui.checkbox(self.layout, context, self, "ground", "garment.prop.ground")
        ui.checkbox(self.layout, context, self, "orient", "garment.prop.orient")
        self.layout.prop(self, "unit", text=t("garment.prop.unit"), translate=False)

    def execute(self, context):
        path = pathlib.Path(self.filepath)

        def load() -> Msg:
            if not path.is_file():
                raise UserError(msg("garment.why.no-file"))
            settings_ = props(context)
            obj, info = gh.import_garment(context, path, ground=self.ground, category=settings_.category,
                                          unit=self.unit, orient=self.orient)
            settings_.garment = obj
            _add_kept_body(context)
            count = len(obj.data.vertices)
            if not info["plausible"]:
                return "WARNING", msg("garment.done.import-size", name=obj.name, count=count, size=info["size"])
            if self.unit == "auto" and info["unit"] not in garment.USUAL_UNITS:
                return "WARNING", msg("garment.done.import-unit", name=obj.name, count=count,
                                      unit=msg(f"garment.unit.{info['unit']}"))
            key = "garment.done.import-rig" if info["rig"] else "garment.done.import-avatar" if info["avatar"] else (
                "garment.done.import-turned" if info["turned"] else "garment.done.import")
            return msg(key, name=obj.name, count=count)

        return self.run(context, load, backup=False)


def _add_kept_body(context: Any) -> None:
    """Shows the body right after the import when one is kept already (no download, no sign-in needed)."""
    settings_ = props(context)
    if valid_body(context) is not None:
        return
    try:
        kept = _kept_body(settings_.gender)
    except (OSError, ValueError, TypeError):
        return
    if kept is not None:
        settings_.body = gh.import_body(context, kept.path, kept.gender, kept.version, _joints_text(kept))


def _joints_text(result: garment_body.BodyResult) -> Optional[str]:
    try:
        return result.joints.read_text("utf-8") if result.joints is not None else None
    except (OSError, UnicodeDecodeError):
        return None


def _body_version_line(body: Any) -> str:
    gender = body.get(gh.BODY_TAG)
    version = body.get(gh.BODY_VERSION)
    if gender in garment.GENDERS and version:
        return t("garment.body.hosted", gender=t(f"gender.{gender}"), version=version)
    return t("garment.body.object", name=body.name)


def _start_download(context: Any) -> None:
    ctrl = state.get()
    ctrl.prepare()
    link_auth = ctrl.link_auth
    assert link_auth is not None and ctrl.data_dir is not None
    gender = props(context).gender
    download = garment_body.BodyDownload(
        gender=gender,
        channel=ctrl.channel,
        cache_root=ctrl.data_dir,
        client_header=auth.client_header(link_auth.http.info),
        access_token=link_auth.access_token,
        invalidate_token=link_auth.invalidate_access_token,
        blender_version=tuple(bpy.app.version),
        origin=BODY_ORIGIN["url"],
        online=host.online_access(),
    )
    RUNTIME.download = download
    RUNTIME.download_scene = context.scene.name
    download.start()
    if not bpy.app.timers.is_registered(body_tick):
        bpy.app.timers.register(body_tick, first_interval=0.2)


#: The origin of the hosted body (a test seam: the smoke and the screenshots point it at a fake on 127.0.0.1).
BODY_ORIGIN = {"url": garment_body.LINK_ORIGIN}


def body_tick() -> Optional[float]:
    """The timer that finishes a body download: imports the body into the scene it was asked for."""
    download = RUNTIME.download
    if download is None:
        return None
    if not download.poll():
        return 0.2
    if not download.cancelled and download.result is not None and _busy():
        return 0.5  # never import while the user is in Edit or Sculpt Mode, or in the middle of a tool
    RUNTIME.download = None
    _KEPT["at"] = 0.0  # look again: the body may be kept now
    scene = bpy.data.scenes.get(RUNTIME.download_scene or "")
    try:
        if download.cancelled:
            notify("INFO", msg("garment.body.cancelled"))
        elif download.error is not None or download.result is None:
            notify("ERROR", msg(f"garment.body.{download.error or 'invalid'}"))
        elif scene is not None:
            finish_body_import(scene, download.result)
    except EXPECTED as exc:
        notify("ERROR", exc.message if isinstance(exc, UserError) else msg("notice.file-error", detail=str(exc)))
    except Exception as exc:  # noqa: BLE001 - a timer that raises is removed; show the problem instead
        traceback.print_exc()
        notify("ERROR", msg("notice.unexpected", detail=f"{type(exc).__name__}: {exc}"))
    host.redraw()
    return None


def _busy() -> bool:
    """A tool runs, or the active object is not in Object Mode."""
    if host.modal_operator_running():
        return True
    window = host.first_window()
    layer = window.view_layer if window is not None else getattr(bpy.context, "view_layer", None)
    active = layer.objects.active if layer is not None else None
    return active is not None and active.mode != "OBJECT"


def finish_body_import(scene: Any, result: garment_body.BodyResult) -> Any:
    window = host.first_window()
    override: Dict[str, Any] = {"window": window} if window is not None else {}
    if window is None or window.scene != scene:
        override.update(scene=scene, view_layer=scene.view_layers[0])
    with bpy.context.temp_override(**override):
        context = bpy.context
        body = gh.import_body(context, result.path, result.gender, result.version, _joints_text(result))
        scene.dct_garment.body = body
    host.push_undo(t("garment.op.add-body"))
    notify("INFO", msg("garment.done.body", gender=msg(f"gender.{result.gender}"), version=result.version))
    return body


class DCTLINK_OT_fit_add_body(_Op):
    bl_idname = "dct_link.fit_add_body"
    bl_label = EN["garment.op.add-body"]
    bl_description = EN["garment.op.add-body.desc"]

    @classmethod
    def poll(cls, context):
        return _refuse(cls, _download_reason(context) or _object_mode_reason(context))

    def execute(self, context):
        try:
            _start_download(context)
        except ui.EXPECTED_FAILURES as exc:
            self.report({"ERROR"}, ui._report_text(exc))
            return {"CANCELLED"}
        notify("INFO", msg("garment.body.downloading"))
        return {"FINISHED"}


class DCTLINK_OT_fit_cancel_body(_Op):
    bl_idname = "dct_link.fit_cancel_body"
    bl_label = EN["op.cancel-sign-in"]
    bl_description = EN["garment.op.cancel-body.desc"]

    @classmethod
    def poll(cls, context):
        return _refuse(cls, None if RUNTIME.download is not None else msg("garment.why.no-download"))

    def execute(self, context):
        if RUNTIME.download is not None:
            RUNTIME.download.cancel()
        return {"FINISHED"}


class DCTLINK_OT_fit_body_file(_MeshOp):
    bl_idname = "dct_link.fit_body_file"
    bl_label = EN["garment.op.body-file"]
    bl_description = EN["garment.op.body-file.desc"]

    filepath: StringProperty(subtype="FILE_PATH", options={"SKIP_SAVE"})
    filter_glob: StringProperty(default="*.glb;*.gltf;*.fbx;*.obj", options={"HIDDEN"})

    @classmethod
    def poll(cls, context):
        reason = None if state.controller is not None else msg("notice.not-ready")
        return _refuse(cls, reason or _object_mode_reason(context))

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        path = pathlib.Path(self.filepath)

        def load() -> Msg:
            if not path.is_file():
                raise UserError(msg("garment.why.no-file"))
            if path.suffix.lower() == ".glb" and tuple(bpy.app.version[:2]) < garment_body.COMPRESSED_FROM \
                    and garment_body.needs_meshopt(path):
                raise UserError(msg("garment.body.compressed"))
            body = gh.import_body(context, path, props(context).gender)
            props(context).body = body
            return msg("garment.done.body-file", name=body.name)

        return self.run(context, load, backup=False)


class DCTLINK_OT_fit_auto_markers(_MeshOp):
    bl_idname = "dct_link.fit_auto_markers"
    bl_label = EN["garment.op.auto-markers"]
    bl_description = EN["garment.op.auto-markers.desc"]

    @classmethod
    def poll(cls, context):
        return _refuse(cls, _markers_reason(context) or _avatar_moved_reason(context))

    def execute(self, context):
        def place() -> Msg:
            settings_ = props(context)
            obj = current_garment(context)
            names = garment.markers_for(settings_.category)
            markers, notes, source = place_markers(context, obj, names)
            gh.drop_markers(context.scene, obj, names)
            gh.write_markers(context.scene, markers, settings_.marker_size, obj)
            obj[gh.MARKER_SOURCE] = source
            RUNTIME.marker_notes[obj.session_uid] = notes
            gh.clear_flags(obj, "dct_aligned", *gh.STALE)
            return msg("garment.done.markers", count=len(markers))

        return self.run(context, place, backup=False)


def _avatar_moved_reason(context: Any) -> Optional[Msg]:
    """An avatar's markers stand where the garment was imported: once Align to Body, the A-pose turn or a fit moved
    it, they no longer fit it."""
    if props(context).avatar == "detect":
        return None
    obj = current_garment(context)
    if any(gh.flag(obj, name) for name in ("dct_aligned", "dct_converted", "dct_fitted")):
        return msg("garment.why.avatar-moved")
    return None


def place_markers(context: Any, obj: Any, names: Tuple[str, ...]) -> Tuple[Dict[str, Any], Tuple[str, ...], str]:
    """The markers of the garment, their notes and where they came from: the avatar it was made on when one is chosen
    (in the pose it was draped in), else read from its shape (tops and legs), else the body's own joints as a
    starting point to move them from."""
    settings_ = props(context)
    if settings_.avatar != "detect":
        avatar = gh.avatar_markers(obj, settings_.avatar)
        if avatar is None:
            raise UserError(msg("garment.why.no-avatar-file"))
        markers = {name: avatar[name] for name in names if name in avatar}
        if len(markers) < len(names):
            raise UserError(msg("garment.why.avatar-markers"))
        return markers, ("avatar",), "avatar"
    if garment.detects_markers(settings_.category):
        result = garment.place_markers(gh.world_positions(obj), settings_.category, settings_.source_pose,
                                       gh.mesh_edges(obj.data))
        return result.markers, result.notes, "shape"
    found, _source = joints(context)
    if not found:
        raise UserError(msg("garment.why.no-body"))
    return garment.body_markers(found, names), ("from-body",), "body"


class DCTLINK_OT_fit_mirror_markers(_MeshOp):
    bl_idname = "dct_link.fit_mirror_markers"
    bl_label = EN["garment.op.mirror"]
    bl_description = EN["garment.op.mirror.desc"]

    @classmethod
    def poll(cls, context):
        reason = None if state.controller is not None else msg("notice.not-ready")
        if reason is None and not any(name in gh.marker_objects(context.scene) for name in garment.MIRRORED):
            reason = msg("garment.why.markers")
        return _refuse(cls, reason or _object_mode_reason(context))

    def execute(self, context):
        def mirror() -> Msg:
            markers = garment.mirror_markers(gh.read_markers(context.scene))
            gh.write_markers(context.scene, markers, props(context).marker_size)
            return msg("garment.done.mirror")

        return self.run(context, mirror, backup=False)


def presets_folder() -> pathlib.Path:
    return host.data_dir(state.PACKAGE) / PRESETS_FOLDER


class DCTLINK_OT_fit_save_preset(_Op):
    bl_idname = "dct_link.fit_save_preset"
    bl_label = EN["garment.op.save-preset"]
    bl_description = EN["garment.op.save-preset.desc"]

    name: StringProperty(name=EN["garment.prop.preset-name"], default="", options={"SKIP_SAVE"},
                         translation_context=CONTEXT)

    @classmethod
    def poll(cls, context):
        reason = None if state.controller is not None else msg("notice.not-ready")
        if reason is None and not gh.marker_objects(context.scene):
            reason = msg("garment.why.markers")
        return _refuse(cls, reason)

    def invoke(self, context, event):
        if not self.name:
            self.name = props(context).category.replace("_", " ")
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        self.layout.prop(self, "name", text=t("garment.prop.preset-name"), translate=False)

    def execute(self, context):
        try:
            file_name = garment.preset_file_name(self.name)
        except ValueError:
            self.report({"ERROR"}, t("garment.why.preset-name"))
            return {"CANCELLED"}
        settings_ = props(context)
        text = garment.preset_json(gh.read_markers(context.scene), settings_.category, settings_.source_pose)
        try:
            folder = presets_folder()
            folder.mkdir(parents=True, exist_ok=True)
            (folder / file_name).write_text(text, "utf-8")
        except OSError as exc:
            self.report({"ERROR"}, t("notice.file-error", detail=str(exc.strerror or exc)))
            return {"CANCELLED"}
        message = msg("garment.done.preset-saved", name=file_name[:-5])
        self.report({"INFO"}, strings.text(message))
        notify("INFO", message)
        return {"FINISHED"}


def preset_names() -> List[str]:
    try:
        return sorted(p.stem for p in presets_folder().glob("*.json") if p.is_file())
    except OSError:
        return []


class DCTLINK_OT_fit_load_preset(_MeshOp):
    bl_idname = "dct_link.fit_load_preset"
    bl_label = EN["garment.op.load-preset"]
    bl_description = EN["garment.op.load-preset.desc"]

    name: StringProperty(options={"HIDDEN", "SKIP_SAVE"})

    @classmethod
    def poll(cls, context):
        reason = None if state.controller is not None else msg("notice.not-ready")
        return _refuse(cls, reason or _object_mode_reason(context))

    def execute(self, context):
        def load() -> Msg:
            try:
                file_name = garment.preset_file_name(self.name)
                text = (presets_folder() / file_name).read_text("utf-8")
                markers, category, pose = garment.parse_preset(text)
            except (OSError, ValueError, UnicodeDecodeError) as exc:
                raise UserError(msg("garment.why.preset-unreadable", detail=str(exc))) from exc
            settings_ = props(context)
            if category is not None and category in garment.categories_for(settings_.slot):
                settings_.category = category
            if pose is not None:
                settings_.source_pose = pose
            gh.write_markers(context.scene, markers, settings_.marker_size)
            return msg("garment.done.preset-loaded", name=self.name)

        return self.run(context, load, backup=False)


class DCTLINK_MT_fit_presets(Menu):
    bl_idname = "DCTLINK_MT_fit_presets"
    bl_label = EN["garment.op.load-preset"]
    bl_translation_context = CONTEXT

    def draw(self, context):
        names = preset_names()
        if not names:
            self.layout.label(text=t("garment.presets.none"), icon="INFO", translate=False)
            return
        for name in names:
            operator(self.layout, DCTLINK_OT_fit_load_preset.bl_idname, None, "POSE_HLT", text=name, name=name)


def align_now(context: Any) -> Msg:
    """Align to Body with the joints at hand (the hosted body's, Durty Cloth Tool's, or read from the body's shape)."""
    found, _source = joints(context)
    if not found:
        raise UserError(msg("garment.why.no-body"))
    obj = current_garment(context)
    # Markers of the avatar sit on its joints, not on the garment's surface: their size is measured against the
    # body's joints, not against the body's own surface markers.
    from_joints = obj.get(gh.MARKER_SOURCE) in ("avatar", "body")
    result = gh.align(context, obj, gh.read_markers(context.scene), found, props(context).category,
                      keep_size=props(context).keep_size, body=None if from_joints else valid_body(context))
    _after_change(context)
    return msg("garment.done.align", **result)


class DCTLINK_OT_fit_align(_MeshOp):
    bl_idname = "dct_link.fit_align"
    bl_label = EN["garment.op.align"]
    bl_description = EN["garment.op.align.desc"]

    @classmethod
    def poll(cls, context):
        return _refuse(cls, _align_reason(context))

    def execute(self, context):
        found, source = joints(context)
        ctrl = state.controller
        # Without the hosted body's joints, Durty Cloth Tool's skeleton (made from the user's game files) beats the
        # estimate from the body's shape: ask for it first when Durty Cloth Tool is there.
        if source == "estimate" and ctrl is not None and ctrl.ready and ctrl.feature_problem(
                addon_settings.FEATURE_ADD_ITEM) is None:
            gender = body_gender(context, valid_body(context))
            try:
                ctrl.skeletons.fetch(gender)
            except ui.EXPECTED_FAILURES:
                pass  # the estimate it is
            else:
                if ctrl.skeletons.fetching(gender):
                    obj = current_garment(context)
                    RUNTIME.job = Job("align", context.scene.name, obj.session_uid, gender)
                    notify("INFO", msg("garment.align.fetching"))
                    if not bpy.app.timers.is_registered(job_tick):
                        bpy.app.timers.register(job_tick, first_interval=0.1)
                    host.redraw()
                    return {"FINISHED"}
        return self.run(context, lambda: align_now(context))


def _snap_reason(context: Any) -> Optional[Msg]:
    reason = _garment_reason(context) or _body_reason(context)
    if reason is None and not _is_prop(context):
        reason = msg("garment.why.not-prop")
    if reason is None and RUNTIME.job is not None:
        reason = msg("add.why.fetching")
    return reason


def anchor_side(context: Any) -> str:
    return "l" if props(context).slot == "p_lwrist" else "r"


class DCTLINK_OT_fit_snap_anchor(_MeshOp):
    bl_idname = "dct_link.fit_snap_anchor"
    bl_label = EN["garment.op.snap"]
    bl_description = EN["garment.op.snap.desc"]

    @classmethod
    def poll(cls, context):
        return _refuse(cls, _snap_reason(context))

    def execute(self, context):
        def snap() -> Msg:
            settings_ = props(context)
            found, _source = joints(context)
            if not found:
                raise UserError(msg("garment.why.no-body"))
            kind = garment.garment_type(settings_.category).snap
            obj = current_garment(context)
            gh.drop_markers(context.scene, obj, ())  # a prop has none; another type's would only confuse
            result = gh.snap_to_anchor(obj, valid_body(context), found, kind, anchor_side(context))
            _after_change(context)
            return msg("garment.done.snap", anchor=msg(f"garment.slot.{settings_.slot}"), **result)

        return self.run(context, snap)


def _pelvis(context: Any) -> Optional[Tuple[float, float, float]]:
    """The garment's pelvis: its marker, else the body's pelvis joint."""
    markers = gh.read_markers(context.scene)
    if "pelvis" in markers:
        return markers["pelvis"]
    found, _source = joints(context)
    if found and "SKEL_Pelvis" in found:
        return tuple(found["SKEL_Pelvis"])
    return None


def _split_reason(context: Any) -> Optional[Msg]:
    reason = _garment_reason(context)
    if reason is None and props(context).category != "dress":
        reason = msg("garment.why.not-dress")
    if reason is None and _pelvis(context) is None:
        reason = msg("garment.why.markers")
    return reason


class DCTLINK_OT_fit_split_waist(_MeshOp):
    bl_idname = "dct_link.fit_split_waist"
    bl_label = EN["garment.op.split"]
    bl_description = EN["garment.op.split.desc"]

    @classmethod
    def poll(cls, context):
        return _refuse(cls, _split_reason(context))

    def execute(self, context):
        def split() -> Msg:
            obj = current_garment(context)
            level = garment.waist_level(gh.world_positions(obj), _pelvis(context))
            skirt = gh.split_at_waist(context, obj, level, f"{obj.name} Skirt")
            skirt[gh.TYPE_TAG], skirt[gh.SLOT_TAG] = "skirt", "lowr"
            found, _source = joints(context)
            if gh.flag(obj, "dct_aligned") and found:
                # The skirt sits where the dress sat: on the body, its markers on the body's own joints.
                markers = garment.body_markers(found, garment.LOWER_MARKERS)
                gh.write_markers(context.scene, markers, props(context).marker_size, skirt)
                skirt[gh.MARKER_SOURCE] = "body"
                skirt[gh.ALIGNED_MARKERS] = garment.markers_json(gh.read_markers(context.scene, skirt))
                for name in ("dct_aligned", "dct_fitted"):
                    if gh.flag(obj, name):
                        gh.set_flag(skirt, name)
            gh.show_markers_of(context.scene, context.view_layer, obj)
            _after_change(context)
            return msg("garment.done.split", name=obj.name, skirt=skirt.name)

        return self.run(context, split)


def bridge_geometry(context: Any) -> Optional[Tuple[float, float, float]]:
    """Where the legs part: the centre (X), the thigh joints' height and half the distance between them, from the
    body's joints or else the hip markers."""
    found, _source = joints(context)
    full = garment.complete_joints(found) if found else {}
    if "SKEL_L_Thigh" in full and "SKEL_R_Thigh" in full:
        left, right = full["SKEL_L_Thigh"], full["SKEL_R_Thigh"]
    else:
        markers = gh.read_markers(context.scene)
        if "hip_l" not in markers or "hip_r" not in markers:
            return None
        left, right = np.asarray(markers["hip_l"]), np.asarray(markers["hip_r"])
    return (float(left[0] + right[0]) / 2, float(left[2] + right[2]) / 2, float(abs(left[0] - right[0])) / 2)


def _bridge_reason(context: Any) -> Optional[Msg]:
    reason = _garment_reason(context)
    if reason is None and not garment.garment_type(props(context).category).bridge:
        reason = msg("garment.why.no-bridge")
    if reason is None and not gh.weighted(current_garment(context)):
        reason = msg("garment.why.no-leg-weights")
    if reason is None and bridge_geometry(context) is None:
        reason = msg("garment.why.no-body")
    return reason


def bridge_now(context: Any, obj: Any) -> int:
    geometry = bridge_geometry(context)
    return gh.bridge_weights(obj, *geometry) if geometry is not None else 0


class DCTLINK_OT_fit_bridge(_MeshOp):
    bl_idname = "dct_link.fit_bridge"
    bl_label = EN["garment.op.bridge"]
    bl_description = EN["garment.op.bridge.desc"]

    @classmethod
    def poll(cls, context):
        return _refuse(cls, _bridge_reason(context))

    def execute(self, context):
        def bridge() -> Msg:
            changed = bridge_now(context, current_garment(context))
            if not changed:
                raise UserError(msg("garment.why.no-leg-weights"))
            return msg("garment.done.bridge", count=changed)

        return self.run(context, bridge)


def _tpose_reason(context: Any) -> Optional[Msg]:
    reason = _garment_reason(context)
    if reason is None and garment.markers_for(props(context).category) != garment.UPPER_MARKERS:
        reason = msg("garment.why.tops-only")
    if reason is None and any(name not in gh.marker_objects(context.scene) for name in garment.UPPER_MARKERS):
        reason = msg("garment.why.markers")
    return reason


class DCTLINK_OT_fit_tpose_to_apose(_MeshOp):
    bl_idname = "dct_link.fit_tpose_to_apose"
    bl_label = EN["garment.op.tpose"]
    bl_description = EN["garment.op.tpose.desc"]

    @classmethod
    def poll(cls, context):
        return _refuse(cls, _tpose_reason(context))

    def execute(self, context):
        def convert() -> Msg:
            settings_ = props(context)
            found, _source = joints(context)
            result = gh.tpose_to_apose(context, current_garment(context), gh.read_markers(context.scene),
                                       math.degrees(settings_.arm_angle), found)
            if not result["rotated"]:
                return msg("garment.done.tpose-none")
            settings_.source_pose = "a_pose"
            _after_change(context)
            return msg("garment.done.tpose", angle=result["rotated"])

        return self.run(context, convert)


def _backup_reason(context: Any) -> Optional[Msg]:
    reason = _garment_reason(context)
    if reason is None and not gh.backups(current_garment(context)):
        reason = msg("garment.why.no-backup")
    return reason


class DCTLINK_OT_fit_restore(_MeshOp):
    bl_idname = "dct_link.fit_restore"
    bl_label = EN["garment.op.restore"]
    bl_description = EN["garment.op.restore.desc"]

    @classmethod
    def poll(cls, context):
        return _refuse(cls, _backup_reason(context))

    def execute(self, context):
        def restore() -> Msg:
            gh.restore_pre_fit(current_garment(context))
            return msg("garment.done.restore")

        return self.run(context, restore, backup=False)


class DCTLINK_OT_fit_back_step(_MeshOp):
    bl_idname = "dct_link.fit_back_step"
    bl_label = EN["garment.op.back"]
    bl_description = EN["garment.op.back.desc"]

    @classmethod
    def poll(cls, context):
        return _refuse(cls, _backup_reason(context))

    def execute(self, context):
        def back() -> Msg:
            gh.back_one_step(current_garment(context))
            return msg("garment.done.back")

        return self.run(context, back, backup=False)


class DCTLINK_OT_fit_remove_backups(_MeshOp):
    bl_idname = "dct_link.fit_remove_backups"
    bl_label = EN["garment.op.remove-backups"]
    bl_description = EN["garment.op.remove-backups.desc"]

    @classmethod
    def poll(cls, context):
        return _refuse(cls, _backup_reason(context))

    def execute(self, context):
        def remove() -> Msg:
            return msg("garment.done.remove-backups", count=gh.remove_backups(current_garment(context)))

        return self.run(context, remove, backup=False)


class DCTLINK_OT_fit_push_out(_MeshOp):
    bl_idname = "dct_link.fit_push_out"
    bl_label = EN["garment.op.push"]
    bl_description = EN["garment.op.push.desc"]

    @classmethod
    def poll(cls, context):
        return _refuse(cls, _fit_reason(context))

    def execute(self, context):
        def push() -> Msg:
            settings_ = props(context)
            progress = gh.Progress(5)
            try:
                result = gh.push_out(current_garment(context), settings_.body, settings_.push_gap / 1000.0,
                                     progress=progress)
            finally:
                progress.end()
            _after_change(context)
            key = "garment.done.push-deep" if result["deep"] else "garment.done.push"
            return msg(key, moved=result["moved"], before=result["before"], after=result["after"],
                       deep=result["deep"])

        return self.run(context, push)


def _after_change(context: Any) -> None:
    """The shape changed: the problem colours follow; the fit check, the checks and the levels of detail no longer
    apply."""
    obj = current_garment(context)
    if obj is None:
        return
    gh.clear_flags(obj, *gh.STALE)
    if gh.problems_shown(obj) and props(context).body is not None:
        _show_problems(context)


def _region_reason(context: Any, snug: bool) -> Optional[Msg]:
    settings_ = props(context)
    if settings_.region not in garment.regions_for(settings_.category):
        return msg("garment.why.region-category")
    if snug and settings_.region not in garment.snug_regions_for(settings_.category):
        return msg("garment.why.region-snug")
    return None


class DCTLINK_OT_fit_snug(_MeshOp):
    bl_idname = "dct_link.fit_snug"
    bl_label = EN["garment.op.snug"]
    bl_description = EN["garment.op.snug.desc"]

    @classmethod
    def poll(cls, context):
        return _refuse(cls, _fit_reason(context, sculpting_ok=True) or _region_reason(context, True))

    def execute(self, context):
        def snug() -> Msg:
            settings_ = props(context)
            result = gh.snug(context.scene, current_garment(context), settings_.body, settings_.region,
                             settings_.snug_gap / 1000.0, settings_.amount, joints(context)[0])
            _after_change(context)
            return msg("garment.done.snug", moved=result["moved"], region=msg(f"garment.region.{settings_.region}"),
                       mean=result["mean"])

        return _in_object_mode(context, lambda: self.run(context, snug, backup=not gh.sculpting(
            current_garment(context))))


class DCTLINK_OT_fit_relax(_MeshOp):
    bl_idname = "dct_link.fit_relax"
    bl_label = EN["garment.op.relax"]
    bl_description = EN["garment.op.relax.desc"]

    @classmethod
    def poll(cls, context):
        return _refuse(cls, _garment_reason(context, sculpting_ok=True) or _region_reason(context, False))

    def execute(self, context):
        def relax() -> Msg:
            settings_ = props(context)
            body = valid_body(context) if _aligned(context) else None
            result = gh.relax(context.scene, current_garment(context), body, settings_.region, settings_.amount,
                              settings_.push_gap / 1000.0, joints(context)[0] if body is not None else None)
            _after_change(context)
            key = "garment.done.relax-smooth" if result["smoothed"] else "garment.done.relax"
            return msg(key, moved=result["moved"], region=msg(f"garment.region.{settings_.region}"))

        return _in_object_mode(context, lambda: self.run(context, relax, backup=not gh.sculpting(
            current_garment(context))))


def _show_problems(context: Any) -> Dict[str, int]:
    settings_ = props(context)
    obj = current_garment(context)
    data = gh.measure(context.scene, obj, settings_.body, joints(context)[0])
    stretch = gh.stretch(obj, data["positions"], data["edges"])
    classes = garment.problem_classes(data["clearance"], data["regions"], stretch)
    gh.show_problems(context, obj, classes)
    return garment.problem_counts(classes)


def _in_object_mode(context: Any, action: Callable[[], set]) -> set:
    """Runs ``action`` in Object Mode, returning to Sculpt Mode afterwards during a sculpt session (the mesh
    is measured and coloured in Object Mode)."""
    obj = current_garment(context)
    sculpt = obj is not None and obj.mode == "SCULPT"
    if sculpt:
        bpy.ops.object.mode_set(mode="OBJECT")
    try:
        return action()
    finally:
        if sculpt:
            bpy.ops.object.mode_set(mode="SCULPT")


class DCTLINK_OT_fit_show_problems(_MeshOp):
    bl_idname = "dct_link.fit_show_problems"
    bl_label = EN["garment.op.problems"]
    bl_description = EN["garment.op.problems.desc"]

    @classmethod
    def poll(cls, context):
        obj = current_garment(context)
        reason = _garment_reason(context, sculpting_ok=True)
        if reason is None and not gh.problems_shown(obj):
            reason = _fit_reason(context, sculpting_ok=True)
        return _refuse(cls, reason)

    def execute(self, context):
        def toggle() -> Optional[Msg]:
            obj = current_garment(context)
            if gh.problems_shown(obj):
                gh.hide_problems(obj)
                return None
            counts = _show_problems(context)
            return msg("garment.done.problems", inside=counts["inside"], close=counts["close"],
                       stretched=counts["stretched"], floating=counts["floating"])

        return _in_object_mode(context, lambda: self.run(context, toggle, backup=False))


class DCTLINK_OT_fit_refresh_problems(_MeshOp):
    bl_idname = "dct_link.fit_refresh_problems"
    bl_label = EN["garment.op.refresh"]
    bl_description = EN["garment.op.refresh.desc"]

    @classmethod
    def poll(cls, context):
        return _refuse(cls, _fit_reason(context, sculpting_ok=True))

    def execute(self, context):
        def refresh() -> Msg:
            counts = _show_problems(context)
            return msg("garment.done.problems", inside=counts["inside"], close=counts["close"],
                       stretched=counts["stretched"], floating=counts["floating"])

        return _in_object_mode(context, lambda: self.run(context, refresh, backup=False))


class DCTLINK_OT_fit_check(_MeshOp):
    bl_idname = "dct_link.fit_check"
    bl_label = EN["garment.op.check"]
    bl_description = EN["garment.op.check.desc"]

    @classmethod
    def poll(cls, context):
        return _refuse(cls, _fit_reason(context))

    def execute(self, context):
        def check() -> Msg:
            settings_ = props(context)
            obj = current_garment(context)
            data = gh.measure(context.scene, obj, settings_.body, joints(context)[0])
            covered = [garment.REGIONS.index(name) for name in garment.regions_for(settings_.category)]
            regions = np.where(np.isin(data["regions"], covered), data["regions"], garment.OTHER)
            report = garment.fit_report(data["clearance"], regions)
            obj[gh.FIT_REPORT] = report.to_json()
            gh.set_flag(obj, "dct_checked")
            return msg("garment.done.check", inside=report.inside)

        return self.run(context, check, backup=False)


def _ped_centre(context: Any) -> Optional[float]:
    markers = gh.read_markers(context.scene)
    if markers:
        return garment.centre_x(markers)
    body = valid_body(context)
    return float(body.matrix_world.translation.x) if body is not None else None


class DCTLINK_OT_fit_sculpt_start(_MeshOp):
    bl_idname = "dct_link.fit_sculpt_start"
    bl_label = EN["garment.op.sculpt"]
    bl_description = EN["garment.op.sculpt.desc"]

    @classmethod
    def poll(cls, context):
        reason = _garment_reason(context)
        if reason is None and valid_body(context) is not None and not _aligned(context):
            reason = msg("garment.why.align-first")
        return _refuse(cls, reason)

    def execute(self, context):
        def start() -> Msg:
            settings_ = props(context)
            result = gh.start_sculpt(context, current_garment(context), valid_body(context),
                                     settings_.sculpt_radius / 100.0, settings_.sculpt_strength,
                                     settings_.sculpt_mirror, _ped_centre(context))
            return msg("garment.done.sculpt-mirror-off" if result["mirror_off"] else "garment.done.sculpt-start")

        return self.run(context, start)


def _sculpt_reason(context: Any) -> Optional[Msg]:
    obj = current_garment(context)
    if state.controller is None:
        return msg("notice.not-ready")
    if not gh.sculpting(obj) and not gh.session_broken(obj):
        return msg("garment.why.no-session")
    return None


class DCTLINK_OT_fit_sculpt_accept(_MeshOp):
    bl_idname = "dct_link.fit_sculpt_accept"
    bl_label = EN["garment.op.accept"]
    bl_description = EN["garment.op.accept.desc"]

    @classmethod
    def poll(cls, context):
        return _refuse(cls, _sculpt_reason(context))

    def execute(self, context):
        def accept() -> Msg:
            settings_ = props(context)
            result = gh.accept_sculpt(context, current_garment(context), valid_body(context),
                                      settings_.sculpt_keep_out, settings_.push_gap / 1000.0)
            _after_change(context)
            return msg("garment.done.accept", moved=result["moved"], before=result["before"], after=result["after"])

        return self.run(context, accept, backup=False)


class DCTLINK_OT_fit_sculpt_cancel(_MeshOp):
    bl_idname = "dct_link.fit_sculpt_cancel"
    bl_label = EN["op.cancel-sign-in"]
    bl_description = EN["garment.op.cancel-sculpt.desc"]

    @classmethod
    def poll(cls, context):
        return _refuse(cls, _sculpt_reason(context))

    def execute(self, context):
        def cancel() -> Msg:
            restored = gh.cancel_sculpt(context, current_garment(context), valid_body(context))
            return msg("garment.done.cancel-sculpt" if restored else "garment.done.cancel-sculpt-lost")

        return self.run(context, cancel, backup=False)


class DCTLINK_OT_fit_check_tears(_MeshOp):
    bl_idname = "dct_link.fit_check_tears"
    bl_label = EN["garment.op.tears"]
    bl_description = EN["garment.op.tears.desc"]

    @classmethod
    def poll(cls, context):
        reason = _garment_reason(context)
        if reason is None:
            reason = gh.tears_problem(current_garment(context))
        return _refuse(cls, reason)

    def execute(self, context):
        def check() -> Msg:
            result = gh.check_tears(context, current_garment(context))
            RUNTIME.tears = result
            RUNTIME.tears_of = current_garment(context).name
            torn = sum(pose["torn"] for pose in result["poses"])
            if not result["pairs"]:
                return msg("garment.done.tears-welded")
            return msg("garment.done.tears", count=result["vertices"]) if torn else msg("garment.done.no-tears")

        return self.run(context, check, backup=False)


#: Seam vertices that may stay open before Prepare Garment warns: some, and more than a small share of the open edges.
OPEN_SEAMS_WARN = (10, 0.02)


def front_centre(context: Any) -> Tuple[float, float, Optional[float]]:
    """The centre of an open front: X between the markers' sides (else the garment's middle), Y the garment's middle
    from front to back, and the neck marker's height (the opening ends there; ``None`` without it)."""
    positions = gh.world_positions(current_garment(context))
    markers = gh.read_markers(context.scene)
    cx = garment.centre_x(markers) if markers else float(np.median(positions[:, 0]))
    top = float(markers["neck"][2]) if "neck" in markers else None
    return cx, float((positions[:, 1].min() + positions[:, 1].max()) / 2), top


class DCTLINK_OT_fit_prepare(_SteppedOp):
    bl_idname = "dct_link.fit_prepare"
    bl_label = EN["garment.op.prepare"]
    bl_description = EN["garment.op.prepare.desc"]
    title = "garment.op.prepare"

    @classmethod
    def poll(cls, context):
        return _refuse(cls, _garment_reason(context))

    def steps(self, context):
        settings_ = props(context)
        return gh.prepare_steps(context, current_garment(context), settings_.weld / 1000.0,
                                (tuple(settings_.colour_1), tuple(settings_.colour_2)), settings_.overwrite_colours,
                                open_front=front_centre(context) if settings_.open_front else None)

    def finished(self, context, result):
        least, share = OPEN_SEAMS_WARN
        if result["open"] > max(least, share * result["boundary"]):
            return "WARNING", msg("garment.done.prepare-open", welded=result["welded"], count=result["open"])
        if result["thick"]:
            return msg("garment.done.prepare-thick", welded=result["welded"], walls=result["walls"],
                       triangles=result["triangles"])
        key = "garment.done.prepare-lining" if result["lining"] else "garment.done.prepare"
        return msg(key, welded=result["welded"], removed=result["removed"], triangles=result["triangles"])


class DCTLINK_OT_fit_combine(_SteppedOp):
    bl_idname = "dct_link.fit_combine_materials"
    bl_label = EN["garment.op.combine"]
    bl_description = EN["garment.op.combine.desc"]
    title = "garment.op.combine"

    @classmethod
    def poll(cls, context):
        reason = _garment_reason(context)
        if reason is None and not current_garment(context).data.uv_layers:
            reason = msg("garment.why.no-uv")
        return _refuse(cls, reason)

    def steps(self, context):
        settings_ = props(context)
        return gh.combine_steps(context, current_garment(context), int(settings_.texture_size), settings_.cut_strips)

    def finished(self, context, result):
        if result["missing"]:
            return "WARNING", msg("garment.done.combine-missing", count=len(result["missing"]),
                                  names=", ".join(result["missing"][:4]))
        if result["sparse"]:
            return "WARNING", msg("garment.done.combine-sparse", used=result["used"])
        if result["walls"]:
            return msg("garment.done.combine-walls", count=result["materials"], size=result["size"],
                       used=result["used"], density=result["density"], walls=result["walls"])
        return msg("garment.done.combine", count=result["materials"], size=result["size"], used=result["used"],
                   cut=result["cut"], density=result["density"])


class DCTLINK_OT_fit_lods(_MeshOp):
    bl_idname = "dct_link.fit_lods"
    bl_label = EN["garment.op.lods"]
    bl_description = EN["garment.op.lods.desc"]

    @classmethod
    def poll(cls, context):
        reason = _garment_reason(context)
        if reason is None and not gh.sollumz_lods_available():
            reason = msg("garment.why.no-sollumz")
        return _refuse(cls, reason)

    def execute(self, context):
        def lods() -> Msg:
            settings_ = props(context)
            body = None if _is_prop(context) else valid_body(context)  # a prop keeps its shape on every level
            result = gh.generate_lods(context, current_garment(context),
                                      {"medium": settings_.lod_medium, "low": settings_.lod_low},
                                      body, settings_.push_gap / 1000.0)
            return msg("garment.done.lods", high=result["high"], medium=result["medium"], low=result["low"])

        return self.run(context, lods, backup=False)


def anchor_point(context: Any) -> Optional[Tuple[float, float, float]]:
    """Where a prop's anchor is on the body: the head's joint, or the wrist of its side (``None`` without a body)."""
    slot = props(context).slot
    found, _source = joints(context)
    if not found or slot not in garment.PROP_SLOTS:
        return None
    full = garment.complete_joints(found)
    name = "SKEL_Head" if slot in ("p_head", "p_eyes", "p_ears") else f"SKEL_{anchor_side(context).upper()}_Hand"
    point = full.get(name)
    return tuple(float(v) for v in point) if point is not None else None


def stats(context: Any, obj: Any) -> Dict[str, Any]:
    """What Validate measures on the garment (a prop by its anchor instead of the body)."""
    if _is_prop(context):
        return gh.validate_stats(obj, valid_body(context), prop=True, anchor=anchor_point(context))
    return gh.validate_stats(obj, valid_body(context))


class DCTLINK_OT_fit_validate(_MeshOp):
    bl_idname = "dct_link.fit_validate"
    bl_label = EN["garment.op.validate"]
    bl_description = EN["garment.op.validate.desc"]

    @classmethod
    def poll(cls, context):
        return _refuse(cls, _garment_reason(context))

    def execute(self, context):
        def validate() -> Msg:
            obj = current_garment(context)
            findings = garment.validate(stats(context, obj))
            obj[gh.FINDINGS] = garment.findings_to_json(findings)
            gh.set_flag(obj, "dct_validated", garment.is_clean(findings))
            if garment.is_clean(findings):
                return msg("garment.done.clean")
            return msg("garment.done.findings", count=len(findings))

        return self.run(context, validate, backup=False)


# --------------------------------------------------------------------------------------------------
# Fit to Body and Transfer Weights on gta.clothing
# --------------------------------------------------------------------------------------------------


def _hosted_version(body: Optional[Any]) -> Optional[str]:
    """The version of the hosted freemode body (a body from a file has none, and gta.clothing fits to its own)."""
    version = body.get(gh.BODY_VERSION) if body is not None else None
    return version if garment_body.valid_version(version) else None


def _service_reason(context: Any, operation: str) -> Optional[Msg]:
    """Why Fit to Body (``fit``) or Transfer Weights (``weights``) cannot run now."""
    if _is_prop(context):
        return msg("fit.why.prop")
    reason = _fit_reason(context)
    if reason is not None:
        return reason
    if _hosted_version(valid_body(context)) is None:
        return msg("fit.why.hosted-body")
    if not host.online_access():
        return msg("notice.online-off")
    ctrl = state.get()
    if ctrl.user_name is None or ctrl.signed_out:
        return msg("fit.why.sign-in")
    if ctrl.fitting.busy:
        return msg("fit.why.running")
    refused = ctrl.fitting.no_fits_left()
    if refused is not None:
        return msg("fit.why.no-fits", wait=garment_fit.wait_text(refused))
    allowance = ctrl.fitting.allowance
    if allowance is not None and allowance.remaining_today <= 0:
        return msg("fit.why.no-fits", wait=garment_fit.wait_text(_until_midnight_utc()))
    return None


def _until_midnight_utc() -> float:
    """Seconds until the day's fits are given anew (at midnight UTC)."""
    now = time.time()
    return 86400.0 - now % 86400.0


def start_service(context: Any, operation: str) -> Any:
    """Sends the chosen garment to gta.clothing: Fit to Body (``fit``) or Transfer Weights (``weights``). The run goes
    on in the add-on's timer; :func:`fit_ended` applies its result."""
    settings_ = props(context)
    obj = current_garment(context)
    body = valid_body(context)
    positions, triangles, pinned, lining = gh.fit_arrays(obj)
    upload = garment_fit.prepare_upload(positions, triangles, pinned, lining)
    options = garment_fit.fit_options(settings_.fit_clearance, settings_.fit_push, settings_.fit_max_push,
                                      settings_.fit_seam_gap, settings_.fit_proportions)
    crowded, where = garment_fit.densest_seam_cell(upload.positions, upload.triangles, options["seamWeldMm"])
    if crowded > fit.MAX_SEAM_DENSITY:
        gh.select_vertices(obj, where)
        # Before Prepare Garment, the crowd is usually panels whose seams are not joined yet.
        key = "fit.input.seam-crowded" if gh.flag(obj, "dct_prepared") else "fit.input.seam-crowded-prepare"
        raise UserError(msg(key, count=crowded, limit=fit.MAX_SEAM_DENSITY))
    markers = gh.read_markers(context.scene) if garment.markers_for(settings_.category) else {}
    request = garment_fit.build_request(operation, body_gender(context, body), settings_.slot, settings_.category,
                                        _hosted_version(body), markers, options)
    ctrl = state.get()
    ctrl.prepare()
    run = ctrl.fitting.start(operation, request, upload, (context.scene.name, obj.session_uid))
    RUNTIME.fit_lines, RUNTIME.fit_operation, RUNTIME.fit_of = [], operation, obj.session_uid
    ctrl.touch()
    return run


def fit_ended(run: Any) -> bool:
    """A fit ended (the add-on's timer calls this): its result goes onto the garment it was made for, as one step that
    can be undone and with a backup first; otherwise the panel says why not. False while the user is in Edit or Sculpt
    Mode or in the middle of a tool (the timer asks again)."""
    scene_name, uid = run.key
    RUNTIME.fit_operation, RUNTIME.fit_of = run.operation, uid
    if run.state != "done":
        RUNTIME.fit_lines = list(run.lines)
        host.redraw()
        return True
    scene = bpy.data.scenes.get(scene_name)
    obj = host.find_object(uid)
    if scene is None or obj is None or scene.dct_garment.garment != obj:
        RUNTIME.fit_lines = [("WARNING", msg("fit.changed"))]
        host.redraw()
        return True
    if _busy():
        return False
    result = run.result
    if result.outcome == "notOnBody":
        RUNTIME.fit_lines = [("WARNING", msg("fit.done.not-on-body"))]
        host.redraw()
        return True
    if gh.fit_digest(obj) != run.upload.digest:
        RUNTIME.fit_lines = [("WARNING", msg("fit.changed"))]
        host.redraw()
        return True
    try:
        with bpy.context.temp_override(**_job_context(scene)):
            gh.backup(obj)
            try:
                if run.operation == "fit":
                    gh.set_world_positions(obj, garment_fit.result_positions(result))
                groups, unweighted = garment_fit.weight_groups(result)
                bones = gh.apply_weights(obj, groups)
            except Exception:
                gh.roll_back(obj)
                raise
            bridged = 0
            if garment.garment_type(scene.dct_garment.category).bridge:
                bridged = bridge_now(bpy.context, obj)  # a skirt or coat tails do not split between the legs
            if run.operation == "fit":
                gh.set_flag(obj, "dct_fitted")
                _after_change(bpy.context)
            else:
                gh.clear_flags(obj, "dct_lods", "dct_validated", gh.FINDINGS)  # the levels of detail took the old weights
    except Exception as exc:  # noqa: BLE001 - a timer that raises stops; show the problem instead
        traceback.print_exc()
        RUNTIME.fit_lines = [("ERROR", msg("notice.unexpected", detail=f"{type(exc).__name__}: {exc}"))]
        host.redraw()
        return True
    host.push_undo(t("garment.op.service-fit" if run.operation == "fit" else "garment.op.service-weights"))
    warnings = garment_fit.warning_lines(result)
    if run.operation == "weights":
        lines = [("INFO", msg("fit.done.weights", bones=bones))]
    elif warnings or result.outcome == "needsReview":
        lines = [("WARNING", msg("fit.done.review", bones=bones))]
    else:
        lines = [("INFO", msg("fit.done.fit", bones=bones))]
    lines += warnings
    if unweighted:
        lines.append(("WARNING", msg("fit.done.unweighted", count=unweighted)))
    if bridged:
        lines.append(("INFO", msg("garment.done.bridge", count=bridged)))
    RUNTIME.fit_lines = lines
    host.redraw()
    return True


class _ServiceOp(_Op):
    """Fit to Body or Transfer Weights: asks once whether the garment may be uploaded, then starts the run."""

    operation = "fit"
    agreed: BoolProperty(options={"HIDDEN", "SKIP_SAVE"})

    @classmethod
    def poll(cls, context):
        return _refuse(cls, _service_reason(context, cls.operation))

    def invoke(self, context, event):
        prefs = state.preferences()
        if prefs is not None and prefs.fit_upload_consent:
            return self.execute(context)
        self.agreed = True  # confirming the dialog is the consent
        try:
            return context.window_manager.invoke_props_dialog(self, width=420, title=t("fit.consent.title"),
                                                              confirm_text=t("fit.consent.confirm"))
        except TypeError:  # an older Blender without a dialog title
            return context.window_manager.invoke_props_dialog(self, width=420)

    def draw(self, context):
        for key in ("fit.consent.what", "fit.consent.kept", "fit.consent.revoke"):
            wrapped(self.layout, context, t(key), width=400)

    def execute(self, context):
        prefs = state.preferences()
        if prefs is None or not prefs.fit_upload_consent:
            if not self.agreed:
                self.report({"ERROR"}, t("fit.consent.what"))  # a script that never showed the question
                return {"CANCELLED"}
            if prefs is not None:
                prefs.fit_upload_consent = True  # without the preferences, the question comes again next time
        try:
            start_service(context, self.operation)
        except EXPECTED as exc:
            _report_failure(self, exc)
            host.redraw()
            return {"CANCELLED"}
        host.redraw()
        return {"FINISHED"}


class DCTLINK_OT_fit_service_fit(_ServiceOp):
    bl_idname = "dct_link.fit_service_fit"
    bl_label = EN["garment.op.service-fit"]
    bl_description = EN["garment.op.service-fit.desc"]
    operation = "fit"


class DCTLINK_OT_fit_service_weights(_ServiceOp):
    bl_idname = "dct_link.fit_service_weights"
    bl_label = EN["garment.op.service-weights"]
    bl_description = EN["garment.op.service-weights.desc"]
    operation = "weights"


class DCTLINK_OT_fit_service_cancel(_Op):
    bl_idname = "dct_link.fit_service_cancel"
    bl_label = EN["op.cancel-sign-in"]
    bl_description = EN["garment.op.service-cancel.desc"]

    @classmethod
    def poll(cls, context):
        ctrl = state.controller
        running = ctrl is not None and ctrl.fitting.busy and not ctrl.fitting.run.cancel_requested
        return _refuse(cls, None if running else msg("add.why.nothing-running"))

    def execute(self, context):
        state.get().fitting.cancel()
        host.redraw()
        return {"FINISHED"}


# --------------------------------------------------------------------------------------------------
# Adding the garment to Durty Cloth Tool
# --------------------------------------------------------------------------------------------------


class Job(NamedTuple):
    """A step that waits for Durty Cloth Tool's skeleton template: ``skeleton`` (Use Durty Cloth Tool Skeleton),
    ``add`` (Add to Project, which then goes on by itself) or ``align`` (Align to Body with the
    joints of the user's game files)."""

    kind: str
    scene: str
    garment: int  # the garment's session uid
    gender: str


def item_name(context: Any) -> str:
    """The name the cloth gets in Durty Cloth Tool: the field, or the garment's name while the field is empty."""
    settings_ = props(context)
    obj = current_garment(context)
    return settings_.item_name.strip() or (obj.name if obj is not None else "")


def _add_busy() -> Optional[Msg]:
    """A skeleton or an add that is under way."""
    ctrl = state.controller
    if RUNTIME.job is not None or RUNTIME.add_job is not None:
        return msg("add.why.fetching") if RUNTIME.add_job is None else msg("add.why.adding")
    if ctrl is not None and ctrl.item_add.adding:
        return msg("add.why.adding")
    return None


def _skeleton_reason(context: Any) -> Optional[Msg]:
    reason = _garment_reason(context)
    if reason is None and _is_prop(context):
        reason = msg("add.why.prop-skeleton")
    if reason is None and not state.get().ready:
        reason = msg("add.why.connect")
    return reason or host.model_open_problem() or _add_busy()


def _add_reason(context: Any) -> Optional[Msg]:
    """Why Add to Project is unavailable (what its checks find is shown after a click)."""
    reason = _garment_reason(context)
    if reason is not None:
        return reason
    ctrl = state.get()
    if not ctrl.ready:
        return msg("add.why.connect")
    return host.model_open_problem() or _add_busy() or ctrl.item_add.problem()


def _variations(context: Any) -> List[Any]:
    return list(props(context).variations)


def add_checks(context: Any, bones: Optional[List[str]] = None) -> Tuple[List[Msg], List[Msg]]:
    """The add's checks before anything is sent: the local Validate (its errors block), the name, one material with
    its diffuse, the variation pictures, the vertex groups against the skeleton's bones (once they are known), and
    advice on maps the add cannot carry. Returns what blocks the add and what is only advice."""
    obj = current_garment(context)
    problems: List[Msg] = []
    warnings: List[Msg] = []
    reason = _garment_reason(context)
    if reason is not None or obj is None:
        return [reason or msg("garment.why.no-garment")], []
    findings = garment.validate(stats(context, obj))
    obj[gh.FINDINGS] = garment.findings_to_json(findings)
    gh.set_flag(obj, "dct_validated", garment.is_clean(findings))
    for finding in findings:
        key = f"garment.finding.{finding.code}"
        if finding.code in ("no-weights", "materials") or key not in EN:
            continue  # the vertex groups and the materials are checked for the add below
        fields = dict(finding.fields)
        if "level" in fields:
            fields["level"] = msg(f"garment.level.{fields['level']}")
        if finding.severity == "error":
            problems.append(msg(key, **fields))  # its warnings stay under Checks, where Validate lists them
    name_problem = garment_add.name_problem(item_name(context))
    if name_problem is not None:
        problems.append(name_problem)
    materials = gh.material_count(obj)
    if materials > 1:
        problems.append(msg("add.why.combine", count=materials))
    images = gdct.garment_images(obj)
    diffuse = images["diffuse"]
    pictures = [diffuse] if diffuse is not None else []
    if diffuse is None and materials <= 1:
        problems.append(msg("add.why.no-diffuse"))
    for target in ("normal", "specular"):
        image = images.get(target)
        if image is not None and not gdct.is_dds(image):
            warnings.append(msg(f"add.warning.{target}-not-embedded", name=image.name))
    for index, variation in enumerate(_variations(context)):
        if variation.image is None:
            problems.append(msg("add.why.variation-empty", number=index + 2))
        else:
            pictures.append(variation.image)
    if 1 + len(_variations(context)) > garment_add.MAX_VARIATIONS:
        problems.append(msg("add.why.too-many", limit=garment_add.MAX_VARIATIONS))
    seen = set()
    for image in pictures:
        if image.session_uid in seen:
            problems.append(msg("add.why.variation-twice", name=image.name))
            continue
        seen.add(image.session_uid)
        width, height = tuple(image.size)
        check = garment_add.picture_check(width, height, image.name)
        if check.blocking is not None:
            problems.append(check.blocking)
        warnings.extend(check.warnings)
    if _is_prop(context):
        return problems, warnings  # a prop moves with its anchor: it has no weights to check
    groups = [group.name for group in obj.vertex_groups if group.name not in gh.TOOL_GROUPS]
    if bones is not None:
        problems.extend(garment_add.group_problems(garment_add.group_report(groups, bones)))
    elif not [name for name in groups if not garment_add.is_tool_group(name)]:
        problems.append(msg("add.why.no-weights"))
    return problems, warnings


def _show_checks(obj: Any, problems: List[Msg], warnings: List[Msg]) -> None:
    RUNTIME.add_problems = list(problems)
    RUNTIME.add_warnings = list(warnings)
    RUNTIME.add_of = obj.session_uid if obj is not None else None


def ensure_skeleton(context: Any, obj: Any, gender: str) -> gdct.Skeleton:
    """The garment on the Durty Cloth Tool skeleton of ``gender``: imported from the template when the garment is not
    on one yet (or on one that does not match it), checked, and the garment attached."""
    ctrl = state.get()
    template = ctrl.skeletons.get(gender)
    bones = ctrl.skeletons.bones(gender)
    if template is None or bones is None:
        raise UserError(msg("add.why.no-template"))
    skeleton = gdct.skeleton_of(obj)
    if skeleton is None or skeleton.gender != gender or garment_add.armature_problem(
            gdct.armature_bones(skeleton.armature), bones) is not None:
        ctrl.prepare()
        assert ctrl.data_dir is not None
        skeleton = gdct.import_skeleton(context, template, ctrl.data_dir, bones, gender, obj)
    gdct.attach(context, obj, skeleton)
    problem = gdct.skeleton_problem(obj, gender, bones)
    if problem is not None:
        raise UserError(problem)
    return skeleton


def ensure_anchor(context: Any, obj: Any, gender: str, slot: str) -> gdct.Skeleton:
    """The prop hanging from its anchor bone, placed from Durty Cloth Tool's skeleton template of ``gender``."""
    template = state.get().skeletons.get(gender)
    if template is None:
        raise UserError(msg("add.why.no-template"))
    return gdct.attach_prop(context, obj, gdct.anchor_matrix(template, slot), slot)


def use_skeleton(context: Any) -> Msg:
    obj = current_garment(context)
    gender = props(context).gender
    skeleton = ensure_skeleton(context, obj, gender)
    count = len(state.get().skeletons.bones(gender) or [])
    return msg("add.done.skeleton", name=skeleton.root.name, gender=msg(f"gender.{gender}"), count=count)


class AddJob:
    """An add while the add-on prepares it, one stage per timer step so Blender stays responsive and Cancel works:
    the checks against the skeleton's bones, the garment on the skeleton and set up for Sollumz, the export (refused
    when empty or partial), then one picture per step (read here, written as PNG on a worker thread that touches no
    Blender data), and finally ``item.add``. The payload is estimated before any picture is written and checked
    after each one. Changes to the garment are one undo step; a failure or Cancel says Ctrl+Z puts them back."""

    STAGES = ("checks", "skeleton", "prepare", "export", "pictures", "send")

    def __init__(self, scene: str, garment_uid: int, gender: str, slot: str) -> None:
        self.scene = scene
        self.garment = garment_uid
        self.gender = gender
        self.slot = slot
        self.stage = "checks"
        self.cancelled = False
        self.changed = False  # the garment was changed for the add (an undo step was pushed before)
        self.skeleton: Optional[gdct.Skeleton] = None
        self.images: Dict[str, Any] = {}
        self.export: Optional[gdct.Export] = None
        self.queue: List[Tuple[str, Any]] = []  # (title, image) still to write
        self.pictures: List[garment_add.Variation] = []
        self.total = 0
        self.size = 0
        self.worker: Optional[threading.Thread] = None
        self.result: Dict[str, Any] = {}

    @property
    def steps(self) -> int:
        return len(self.STAGES) - 1 + max(1, self.total)

    @property
    def done(self) -> int:
        index = self.STAGES.index(self.stage)
        if self.stage == "pictures":
            return index + len(self.pictures)
        return index + (max(1, self.total) - 1 if index > self.STAGES.index("pictures") else 0)

    def cancel(self) -> None:
        self.cancelled = True

    def text(self) -> str:
        if self.stage == "pictures":
            return t("add.progress.pictures", done=len(self.pictures) + 1, total=max(1, self.total))
        if self.stage in ("prepare", "export"):
            return t(f"add.progress.{self.stage}")
        return t("add.progress.skeleton")

    def tick(self, context: Any) -> Optional[float]:
        """One stage (or one picture). Returns the seconds to the next step, or ``None`` when the job is over."""
        ctrl = state.get()
        settings_ = props(context)
        obj = current_garment(context)
        if self.stage == "checks":
            problems, warnings = add_checks(context, ctrl.skeletons.bones(self.gender))
            _show_checks(obj, problems, warnings)
            if problems:
                raise UserError(msg("add.blocked", count=len(problems)))
            self.stage = "skeleton"
            return 0.0
        if self.stage == "skeleton":
            self._changing()
            if self.slot in garment.PROP_SLOTS:
                self.skeleton = ensure_anchor(context, obj, self.gender, self.slot)
            else:
                self.skeleton = ensure_skeleton(context, obj, self.gender)
            self.stage = "prepare"
            return 0.0
        if self.stage == "prepare":
            self._changing()
            self.images = gdct.prepare_garment(context, obj, self.skeleton)
            if self.slot in garment.PROP_SLOTS:
                problem = gdct.prop_problem(obj, self.slot)
            else:
                problem = gdct.skeleton_problem(obj, self.gender, ctrl.skeletons.bones(self.gender))
            if problem is not None:  # checked again right before the export
                raise UserError(problem)
            self.stage = "export"
            return 0.0
        if self.stage == "export":
            ctrl.prepare()
            assert ctrl.data_dir is not None
            folder = gdct.work_folder(ctrl.data_dir)
            try:
                self.export = gdct.export_garment(self.skeleton, folder)
            finally:
                shutil.rmtree(folder, ignore_errors=True)
            self.queue = [(garment_add.variation_title(settings_.first_title, self.images["diffuse"].name),
                           self.images["diffuse"])]
            self.queue += [(garment_add.variation_title(v.title, v.image.name), v.image) for v in _variations(context)]
            self.total = len(self.queue)
            self.size = garment_add.payload_size([self.export.model, *self.export.textures])
            least, _most = garment_add.payload_estimate(self.size, [tuple(image.size) for _, image in self.queue])
            if least > protocol.MAX_BINARY_PAYLOAD_BYTES:
                raise UserError(msg("add.why.too-large", size=protocol.MAX_BINARY_PAYLOAD_BYTES // (1024 * 1024)))
            self.stage = "pictures"
            return 0.0
        if self.stage == "pictures":
            if self.worker is not None:
                if self.worker.is_alive():
                    return 0.05
                self.worker = None
                if "error" in self.result:
                    raise self.result["error"]
                title, png = self.result["picture"]
                self.pictures.append(garment_add.Variation(title, png))
                self.size += len(png)
                if self.size > protocol.MAX_BINARY_PAYLOAD_BYTES:
                    raise UserError(msg("add.why.too-large", size=protocol.MAX_BINARY_PAYLOAD_BYTES // (1024 * 1024)))
            if self.queue:
                title, image = self.queue.pop(0)
                source = gdct.read_picture(image)  # Blender data: read here, on the main thread
                self.result = {}

                def write(result: Dict[str, Any] = self.result) -> None:
                    try:
                        result["picture"] = (title, gdct.encode_picture(*source))
                    except Exception as exc:  # noqa: BLE001 - handed to the main thread, which reports it
                        result["error"] = exc

                self.worker = threading.Thread(target=write, name="dct-add-picture", daemon=True)
                self.worker.start()
                return 0.05
            self.stage = "send"
            return 0.0
        files, chosen = garment_add.item_files(self.export.model, self.export.textures, self.pictures)
        if self.export.warnings:
            RUNTIME.add_warnings.append(msg("add.export.warnings"))
        name = item_name(context)
        root_uid, garment_uid = self.skeleton.root.session_uid, obj.session_uid

        def added(binding: Dict[str, str]) -> None:
            root, added_garment = host.find_object(root_uid), host.find_object(garment_uid)
            if root is None or added_garment is None:
                raise RuntimeError("the garment or its Drawable Dictionary was removed meanwhile")
            gdct.store_added(root, added_garment, binding, name)
            gh.remove_backups(added_garment)  # the cloth is in the project; its History has the steps now
            host.push_undo(t("add.op.add"))
            host.redraw()

        skin = bool(settings_.skin) and self.slot not in garment.PROP_SLOTS  # a prop never shows skin
        ctrl.item_add.start(self.slot, self.gender, skin, name, chosen, files, on_added=added)
        if self.changed:
            host.push_undo(t("add.op.add"))
        self.result = {"sent": msg("add.sent", name=name, count=len(chosen))}
        return None

    def _changing(self) -> None:
        """An undo step before the add changes the garment (once), so Ctrl+Z goes back to before the add."""
        if not self.changed:
            host.push_undo(t("add.op.add"))
            self.changed = True


def _report_failure(op: Optional[Operator], exc: BaseException) -> None:
    failure = _failure_message(exc)
    if op is not None:
        op.report({"ERROR"}, strings.text(failure))
    notify("ERROR", failure)


def _run_step(context: Any, kind: str, op: Optional[Operator] = None) -> set:
    """Runs a skeleton or align step now that the template is here, or starts the add's own job; failures are
    reported and shown in the panel."""
    if kind == "add":
        settings_ = props(context)
        obj = current_garment(context)
        RUNTIME.add_job = AddJob(context.scene.name, obj.session_uid, settings_.gender, settings_.slot)
        RUNTIME.notice = None  # the add's own status, under Game Ready, follows it from here
        if not bpy.app.timers.is_registered(job_tick):
            bpy.app.timers.register(job_tick, first_interval=0.05)
        host.redraw()
        return {"FINISHED"}
    try:
        message = use_skeleton(context) if kind == "skeleton" else align_now(context)
    except EXPECTED as exc:
        _report_failure(op, exc)
        host.redraw()
        return {"CANCELLED"}
    if op is not None:
        op.report({"INFO"}, strings.text(message))
    notify("INFO", message)
    host.redraw()
    return {"FINISHED"}


def _start_step(context: Any, kind: str, op: Operator) -> set:
    """Runs the step now when the template of the gender is kept, or asks Durty Cloth Tool for it and goes on once it
    arrives (:func:`job_tick`)."""
    ctrl = state.get()
    gender = props(context).gender
    obj = current_garment(context)
    if ctrl.skeletons.get(gender) is not None:
        return _run_step(context, kind, op)
    try:
        ctrl.skeletons.fetch(gender)
    except ui.EXPECTED_FAILURES as exc:
        _report_failure(op, exc)
        return {"CANCELLED"}
    RUNTIME.job = Job(kind, context.scene.name, obj.session_uid, gender)
    notify("INFO", msg("add.fetching", gender=msg(f"gender.{gender}")))
    if not bpy.app.timers.is_registered(job_tick):
        bpy.app.timers.register(job_tick, first_interval=0.1)
    host.redraw()
    return {"FINISHED"}


def _job_context(scene: Any) -> Dict[str, Any]:
    window = host.first_window()
    override: Dict[str, Any] = {"window": window} if window is not None else {}
    if window is None or window.scene != scene:
        override.update(scene=scene, view_layer=scene.view_layers[0])
    return override


def job_tick() -> Optional[float]:
    """The timer that goes on with a step once Durty Cloth Tool sent the skeleton template, and drives the add's own
    job stage by stage."""
    if RUNTIME.add_job is not None:
        return _add_tick()
    job = RUNTIME.job
    ctrl = state.controller
    if job is None or ctrl is None:
        RUNTIME.job = None
        return None
    if ctrl.skeletons.get(job.gender) is None:
        if ctrl.skeletons.fetching(job.gender):
            return 0.2
        RUNTIME.job = None
        problem = ctrl.skeletons.problems.get(job.gender)
        if job.kind != "align":
            notify(problem.level if problem else "ERROR", problem.message if problem else msg("add.why.no-template"))
            host.redraw()
            return None
        # Align goes on with the estimate from the body's shape.
    if _busy():
        return 0.5  # never while the user is in Edit or Sculpt Mode, or in the middle of a tool
    RUNTIME.job = None
    scene = bpy.data.scenes.get(job.scene)
    obj = host.find_object(job.garment)
    if scene is None or obj is None or scene.dct_garment.garment != obj:
        notify("WARNING", msg("add.why.garment-changed"))
        host.redraw()
        return None
    try:
        with bpy.context.temp_override(**_job_context(scene)):
            if job.kind == "align":
                gh.backup(obj)
            result = _run_step(bpy.context, job.kind)
    except Exception as exc:  # noqa: BLE001 - a timer that raises is removed; show the problem instead
        traceback.print_exc()
        notify("ERROR", msg("notice.unexpected", detail=f"{type(exc).__name__}: {exc}"))
        host.redraw()
        return None
    if "FINISHED" in result and job.kind != "add":
        host.push_undo(t("add.op.skeleton" if job.kind == "skeleton" else "garment.op.align"))
    elif "FINISHED" not in result and job.kind == "align":
        gh.drop_newest_backup(obj)
    if RUNTIME.add_job is not None:
        return 0.05
    return None


def _add_tick() -> Optional[float]:
    job = RUNTIME.add_job
    if job.cancelled:
        return _end_add(job, msg("add.cancelled-local") if job.changed else msg("error.cancelled"), "INFO")
    if job.stage != "pictures" and _busy():
        return 0.5
    scene = bpy.data.scenes.get(job.scene)
    obj = host.find_object(job.garment)
    if scene is None or obj is None or scene.dct_garment.garment != obj:
        return _end_add(job, msg("add.why.garment-changed"), "WARNING")
    try:
        with bpy.context.temp_override(**_job_context(scene)):
            delay = job.tick(bpy.context)
    except Exception as exc:  # noqa: BLE001 - a timer that raises is removed; show the problem instead
        if not isinstance(exc, EXPECTED):
            traceback.print_exc()
        failure = _failure_message(exc)
        if job.changed:
            failure = msg("add.failed-undo", problem=failure)
        return _end_add(job, failure, "ERROR")
    host.redraw()
    if delay is None:
        RUNTIME.add_job = None
        sent = job.result.get("sent")
        if sent is not None:
            ctrl = state.get()
            ctrl.touch()
        return None
    return delay


def _end_add(job: AddJob, message: Msg, level: str) -> None:
    """Ends the add before anything was sent: the garment's changes become their own undo step, so Ctrl+Z puts the
    garment back as it was before the add."""
    RUNTIME.add_job = None
    if job.changed:
        host.push_undo(t("add.op.add"))
    notify(level, message)
    host.redraw()
    return None


class DCTLINK_OT_fit_use_skeleton(_Op):
    bl_idname = "dct_link.fit_use_skeleton"
    bl_label = EN["add.op.skeleton"]
    bl_description = EN["add.op.skeleton.desc"]
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return _refuse(cls, _skeleton_reason(context) if state.controller is not None else msg("notice.not-ready"))

    def execute(self, context):
        return _start_step(context, "skeleton", self)


class DCTLINK_OT_fit_add_to_dct(_Op):
    bl_idname = "dct_link.fit_add_to_dct"
    bl_label = EN["add.op.add"]
    bl_description = EN["add.op.add.desc"]
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return _refuse(cls, _add_reason(context) if state.controller is not None else msg("notice.not-ready"))

    def execute(self, context):
        obj = current_garment(context)
        ctrl = state.get()
        ctrl.item_add.forget()
        problems, warnings = add_checks(context, ctrl.skeletons.bones(props(context).gender))
        _show_checks(obj, problems, warnings)
        if problems:
            message = msg("add.blocked", count=len(problems))
            self.report({"ERROR"}, strings.text(message))
            notify("ERROR", message)
            host.redraw()
            return {"CANCELLED"}
        return _start_step(context, "add", self)


class DCTLINK_OT_fit_cancel_add(_Op):
    bl_idname = "dct_link.fit_cancel_add"
    bl_label = EN["op.cancel-sign-in"]
    bl_description = EN["add.op.cancel.desc"]

    @classmethod
    def poll(cls, context):
        ctrl = state.controller
        running = (RUNTIME.job is not None or RUNTIME.add_job is not None
                   or (ctrl is not None and ctrl.item_add.adding))
        if running and ctrl is not None and ctrl.item_add.withdrawing:
            return _refuse(cls, msg("add.withdrawing"))
        return _refuse(cls, None if running else msg("add.why.nothing-running"))

    def execute(self, context):
        ctrl = state.get()
        if RUNTIME.add_job is not None:
            RUNTIME.add_job.cancel()
        elif RUNTIME.job is not None:
            RUNTIME.job = None
            notify("INFO", msg("error.cancelled"))
        elif ctrl.item_add.adding:
            ctrl.item_add.cancel()
        host.redraw()
        return {"FINISHED"}


class DCTLINK_OT_fit_add_variation(_Op):
    bl_idname = "dct_link.fit_add_variation"
    bl_label = EN["add.op.add-variation"]
    bl_description = EN["add.op.add-variation.desc"]
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        reason = None if state.controller is not None else msg("notice.not-ready")
        if reason is None and 1 + len(props(context).variations) >= garment_add.MAX_VARIATIONS:
            reason = msg("add.why.too-many", limit=garment_add.MAX_VARIATIONS)
        return _refuse(cls, reason)

    def execute(self, context):
        props(context).variations.add()
        return {"FINISHED"}


class DCTLINK_OT_fit_remove_variation(_Op):
    bl_idname = "dct_link.fit_remove_variation"
    bl_label = EN["add.op.remove-variation"]
    bl_description = EN["add.op.remove-variation.desc"]
    bl_options = {"REGISTER", "UNDO"}

    index: IntProperty(options={"HIDDEN", "SKIP_SAVE"})

    def execute(self, context):
        variations = props(context).variations
        if 0 <= self.index < len(variations):
            variations.remove(self.index)
        return {"FINISHED"}


# --------------------------------------------------------------------------------------------------
# Drawing
# --------------------------------------------------------------------------------------------------


def findings_state(obj: Optional[Any]) -> str:
    """What the garment's latest Validate found: ``none``, ``blocking``, ``warnings`` or ``clean``."""
    findings = garment.findings_from_json(gh.stored_text(obj, gh.FINDINGS))
    if findings is None:
        return "none"
    if any(f.severity == "error" for f in findings):
        return "blocking"
    return "clean" if garment.is_clean(findings) else "warnings"


def flow_state(context: Any) -> garment.FlowState:
    if RUNTIME.flow is not None:
        return RUNTIME.flow  # the panel being drawn computed it already
    settings_ = props(context)
    obj = current_garment(context)
    report = garment.FitReport.from_json(gh.stored_text(obj, gh.FIT_REPORT))
    ctrl = state.controller
    prop = garment.is_prop(settings_.category)
    skeleton = gdct.skeleton_of(obj)
    expected = garment.markers_for(settings_.category)
    placed = gh.marker_objects(context.scene) if obj is not None else {}
    return garment.FlowState(
        garment=obj is not None,
        body=gh.body_problem(context, settings_.body) is None,
        category=settings_.category,
        source_pose=settings_.source_pose,
        markers=len([name for name in expected if name in placed]),
        aligned=obj is not None and (gh.flag(obj, "dct_aligned") if prop else gh.aligned(obj, context.scene)),
        fitted=gh.flag(obj, "dct_fitted"),
        sculpting=gh.sculpting(obj) or gh.session_broken(obj),
        checked=gh.flag(obj, "dct_checked"),
        inside=report.inside if report is not None else 0,
        prepared=gh.flag(obj, "dct_prepared"),
        materials=gh.material_count(obj),
        weighted=gh.weighted(obj),
        lods=gh.flag(obj, "dct_lods"),
        sollumz=gh.sollumz_lods_available(),
        validated=gh.flag(obj, "dct_validated"),
        findings=findings_state(obj),
        connected=ctrl is not None and ctrl.ready,
        project=ctrl is not None and ctrl.project is not None,
        skeleton=skeleton is not None and skeleton.gender == settings_.gender,
        adding=RUNTIME.job is not None or RUNTIME.add_job is not None or (ctrl is not None and ctrl.item_add.adding),
        added=bool(obj is not None and gh.stored_text(obj, gdct.ADDED)),
        prop=prop,
        gender=settings_.gender,
    )


def next_operator(context: Any) -> Optional[str]:
    """The operator of the next step (drawn as the large button), or ``None``."""
    return garment.STEP_OPERATORS.get(garment.next_step(flow_state(context)))


def step(layout: Any, context: Any, idname: str, key: str, icon: str = "NONE", **properties: Any) -> Any:
    """A tool's button: the large one when it is the next step, an ordinary one otherwise."""
    if next_operator(context) == idname:
        return primary(layout, idname, key, icon, **properties)
    return operator(layout, idname, key, icon, **properties)


def options(layout: Any, context: Any, name: str) -> Optional[Any]:
    """A closed Options section for settings that rarely change; its body, or ``None`` while it is closed."""
    header, body = layout.panel(f"dct_link_garment_{name}", default_closed=True)
    header.label(text=t("garment.heading.options"), icon="PREFERENCES", translate=False)
    return body


def labelled(layout: Any, context: Any, data: Any, name: str, key: str, info: Optional[str] = None) -> None:
    """A property with its label on the left (a dropdown or a field), as the Live Preview's Image and Map rows."""
    row = layout.row(align=True)
    split = row.split(factor=0.4, align=True)
    split.label(text=t(key), translate=False)
    split.prop(data, name, text="")
    if info:
        info_button(row, info)


def tool(layout: Any, context: Any, idname: str, key: str, icon: str = "NONE", info: Optional[str] = None,
         done: bool = False, **properties: Any) -> Any:
    """A one-step tool on one row: its button (the large one when it is the next step, with a tick once its step is
    done) and its help button. The button's label is the tool's only name: no heading repeats it. A label too long to
    share the row with the help button (a narrow sidebar, a longer language) keeps the whole row, and the button's
    tooltip explains it."""
    row = layout.row(align=True)
    if next_operator(context) == idname:
        row.scale_y = ui.PRIMARY_SCALE
    op = operator(row, idname, key, "CHECKMARK" if done else icon, **properties)
    room = ui.content_width(context) - (ui._BUTTON + HELP_WIDTH) * ui._scale(context)  # _BUTTON holds the icon
    if info and ui._measure(context)(t(key)) <= room:
        info_button(row, info)
    return op


#: The width of a help button beside a tool's button (interface units).
HELP_WIDTH = 24


def section(layout: Any, name: str, key: str, icon: str, info: Optional[str] = None) -> Optional[Any]:
    """A closed section for tools most garments do not need: its title (and help) in the header; its body, or
    ``None`` while it is closed."""
    header, body = layout.panel(f"dct_link_garment_section_{name}", default_closed=True)
    header.label(text=t(key), icon=icon, translate=False)
    if info:
        info_button(header, info)
    return body


def open_stage(context: Any) -> str:
    """The stage whose section is open: the one that holds the next step."""
    return garment.stage_of(flow_state(context))


def stage_status(flow: garment.FlowState, stage: str) -> Tuple[str, bool]:
    """A stage's header: its short status (translated) and whether the work has moved past it."""
    found = garment.stage_status(flow, stage)
    if found.key is None:
        return "", found.done
    fields = dict(found.fields, **{name: msg(key) for name, key in found.keys.items()})
    return t(found.key, **fields), found.done


def draw_main(layout: Any, context: Any) -> None:
    RUNTIME.flow = None
    RUNTIME.flow = flow_state(context)  # computed once for the whole panel
    try:
        _draw_main(layout, context)
    finally:
        RUNTIME.flow = None


def _draw_main(layout: Any, context: Any) -> None:
    flow = flow_state(context)
    wrapped(layout, context, t(garment.next_step(flow)), "FORWARD")
    if not flow.garment:
        subtext(layout, context, "experimental.note", indent=True)
    if RUNTIME.notice is not None:
        layout.separator(factor=GAP_SMALL)
        ui.draw_notice(layout, context, RUNTIME.notice)
    # The stage of the next step (open_stage is the panel's choice; the screenshot tool asks it for another stage).
    opened = open_stage(context)
    if opened != RUNTIME.opened:
        # The work moved to another stage: the sections get new ids, so each starts from its default again (the new
        # stage open, the others folded), also when the work goes back to a stage that was open before. Opened by
        # hand, a section stays open until the next move. The ids start with this session's time, so a saved file
        # never brings back the states of an earlier session.
        RUNTIME.opened = opened
        RUNTIME.layout_generation += 1
    generation = f"{RUNTIME.layout_session}_{RUNTIME.layout_generation}"
    for number, stage in enumerate(garment.STAGES, start=1):
        layout.separator(factor=GAP_SMALL)
        header, body = layout.panel(f"dct_link_garment_stage_{stage}_{generation}", default_closed=stage != opened)
        status, done = stage_status(flow, stage)
        ui.stage_header(header, context, t("ped.stage-title", number=number, title=msg(f"garment.panel.{stage}")),
                        status, done)
        if body is not None:
            STAGE_DRAW[stage](body, context)
    if current_garment(context) is not None:
        layout.separator(factor=GAP_SMALL)
        draw_backups(layout, context)


def draw_setup(layout: Any, context: Any) -> None:
    settings_ = props(context)
    kind = garment.garment_type(settings_.category)
    row = layout.row(align=True)
    row.prop(settings_, "gender", expand=True)
    labelled(layout, context, settings_, "category", "garment.prop.category", info="garment.info.type")
    subtext(layout, context, f"garment.category.{settings_.category}.desc")
    if kind.hint:
        wrapped(layout, context, t(kind.hint), "INFO")
    if garment.markers_for(settings_.category):
        layout.separator(factor=GAP_SMALL)
        labelled(layout, context, settings_, "avatar", "garment.prop.avatar", info="garment.info.avatar")
    if kind.family in ("upper", "lower") and settings_.avatar == "detect":
        layout.separator(factor=GAP_SMALL)
        heading(layout, context, "garment.prop.pose", info="garment.info.pose")
        row = layout.row(align=True)
        row.prop(settings_, "source_pose", expand=True)
    if len(kind.slots) > 1 or kind.family == "upper":
        body = options(layout, context, "type")
        if body is not None:
            if len(kind.slots) > 1:
                labelled(body, context, settings_, "slot", "garment.prop.slot")
            if kind.family == "upper":
                ui.checkbox(body, context, settings_, "open_front", "garment.prop.open-front")

    layout.separator(factor=GAP)
    heading(layout, context, "garment.prop.garment", "MOD_CLOTH", info="garment.info.garment")
    layout.prop(settings_, "garment", text="")
    obj = current_garment(context)
    if obj is not None:
        subtext(layout, context, "garment.garment.facts", count=len(obj.data.vertices),
                materials=gh.material_count(obj))
    step(layout, context, DCTLINK_OT_fit_import_garment.bl_idname, "garment.op.import", "IMPORT")
    operator(layout, DCTLINK_OT_fit_use_garment.bl_idname, "garment.op.use", "RESTRICT_SELECT_OFF")
    if obj is None:
        reason_text(layout, context, _use_reason(context))

    layout.separator(factor=GAP)
    heading(layout, context, "garment.prop.body", "OUTLINER_OB_ARMATURE", info="garment.info.body")
    body = settings_.body
    if body is not None and gh.body_problem(context, body) is None:
        wrapped(layout, context, _body_version_line(body), "CHECKMARK")
    if RUNTIME.download is not None:
        wrapped(layout, context, t("garment.body.downloading"), "SORTTIME")
        operator(layout, DCTLINK_OT_fit_cancel_body.bl_idname, "op.cancel-sign-in", "X")
        return
    step(layout, context, DCTLINK_OT_fit_add_body.bl_idname, "garment.op.add-body", "IMPORT")
    reason_text(layout, context, _download_reason(context))
    operator(layout, DCTLINK_OT_fit_body_file.bl_idname, "garment.op.body-file", "FILEBROWSER")


def draw_anchor(layout: Any, context: Any) -> None:
    """A prop's placement: Snap to Anchor, then moved by hand."""
    obj = current_garment(context)
    tool(layout, context, DCTLINK_OT_fit_snap_anchor.bl_idname, "garment.op.snap", "PIVOT_CURSOR",
         info="garment.info.snap", done=flow_state(context).aligned)
    if obj is not None:
        reason_text(layout, context, _snap_reason(context))
    subtext(layout, context, "garment.snap.subtext", anchor=t(f"garment.slot.{props(context).slot}"))


def draw_fit(layout: Any, context: Any) -> None:
    settings_ = props(context)
    obj = current_garment(context)
    if _is_prop(context):
        draw_anchor(layout, context)
        return
    expected = garment.markers_for(settings_.category)
    if not expected:
        wrapped(layout, context, t("garment.why.no-markers"), "INFO")
    else:
        heading(layout, context, "garment.heading.markers", "EMPTY_DATA", info="garment.info.markers")
        step(layout, context, DCTLINK_OT_fit_auto_markers.bl_idname, "garment.op.auto-markers", "EMPTY_DATA")
        reason_text(layout, context, _markers_reason(context))
        markers = gh.read_markers(context.scene) if obj is not None else {}
        placed = len([name for name in expected if name in markers])
        subtext(layout, context, "garment.markers.count", count=placed, total=len(expected))
        for note in RUNTIME.marker_notes.get(obj.session_uid, ()) if obj is not None else ():
            wrapped(layout, context, t(f"garment.marker-note.{note}"), "INFO")
        if placed == len(expected):
            for problem in garment.marker_problems(markers, settings_.category):
                wrapped(layout, context, t(f"garment.marker-problem.{problem}"), "ERROR")
        if expected != garment.HEAD_MARKERS:
            operator(layout, DCTLINK_OT_fit_mirror_markers.bl_idname, "garment.op.mirror", "MOD_MIRROR")
        body = options(layout, context, "markers")
        if body is not None:
            body.prop(settings_, "marker_size", text=t("garment.prop.marker-size"), translate=False)
            row = ui.button_group(body, context, ("garment.op.save-preset", "garment.op.load-preset"))
            operator(row, DCTLINK_OT_fit_save_preset.bl_idname, "garment.op.save-preset", "FILE_TICK")
            row.menu(DCTLINK_MT_fit_presets.bl_idname, text=t("garment.op.load-preset"), icon="FILE_FOLDER",
                     translate=False)

        layout.separator(factor=GAP)
        tool(layout, context, DCTLINK_OT_fit_align.bl_idname, "garment.op.align", "ORIENTATION_GIMBAL",
             info="garment.info.align", done=flow_state(context).aligned)
        reason = _align_reason(context) if obj is not None else None
        if reason is not None and reason.key != "garment.why.markers":  # the markers are right above
            reason_text(layout, context, reason)
        _found, source = joints(context)
        if source is not None:
            wrapped(layout, context, t(f"garment.align.source.{source}"), "INFO" if source == "estimate" else "CHECKMARK",
                    dim=source != "estimate")
        body = options(layout, context, "align")
        if body is not None:
            ui.checkbox(body, context, settings_, "keep_size", "garment.prop.keep-size")
            if expected == garment.UPPER_MARKERS:
                body.separator(factor=GAP_SMALL)
                heading(body, context, "garment.heading.tpose", "ARMATURE_DATA", info="garment.info.tpose")
                body.prop(settings_, "arm_angle", text=t("garment.prop.arm-angle"), translate=False)
                operator(body, DCTLINK_OT_fit_tpose_to_apose.bl_idname, "garment.op.tpose", "POSE_HLT")

    layout.separator(factor=GAP)
    draw_service(layout, context, "fit")
    if settings_.category == "dress":
        layout.separator(factor=GAP)
        tool(layout, context, DCTLINK_OT_fit_split_waist.bl_idname, "garment.op.split", "MOD_EDGESPLIT",
             info="garment.info.split")
        if obj is not None:
            reason_text(layout, context, _split_reason(context))


def draw_backups(layout: Any, context: Any) -> None:
    """The garment's backups, in a closed section after the stages: every stage that changes the garment keeps one."""
    obj = current_garment(context)
    body = section(layout, "backups", "garment.heading.backups", "FILE_BACKUP", info="garment.info.backups")
    if body is None:
        return
    count = len(gh.backups(obj)) if obj is not None else 0
    subtext(body, context, "garment.backups.count", count=count, limit=gh.MAX_BACKUPS)
    row = ui.button_group(body, context, ("garment.op.back", "garment.op.restore"))
    operator(row, DCTLINK_OT_fit_back_step.bl_idname, "garment.op.back", "LOOP_BACK")
    operator(row, DCTLINK_OT_fit_restore.bl_idname, "garment.op.restore", "FILE_REFRESH")
    operator(body, DCTLINK_OT_fit_remove_backups.bl_idname, "garment.op.remove-backups", "TRASH")


def draw_fix(layout: Any, context: Any) -> None:
    """Run Fit Check and Push Out of Body in view; the problem colours, the region tools, sculpting by hand and the
    tear check in closed sections below them."""
    settings_ = props(context)
    obj = current_garment(context)
    if gh.sculpting(obj) or gh.session_broken(obj):
        draw_sculpt_session(layout, context)
        return
    if _is_prop(context):
        wrapped(layout, context, t("garment.why.prop-fix"), "INFO")
        return
    reason = _fit_reason(context) if obj is not None else None
    if reason is not None and reason.key == "garment.why.align-first":
        wrapped(layout, context, strings.text(reason), "INFO")
        layout.separator(factor=GAP_SMALL)

    tool(layout, context, DCTLINK_OT_fit_check.bl_idname, "garment.op.check", "VIEWZOOM", info="garment.info.check")
    draw_report(layout, context)

    layout.separator(factor=GAP)
    layout.prop(settings_, "push_gap", text=t("garment.prop.gap"), translate=False)
    tool(layout, context, DCTLINK_OT_fit_push_out.bl_idname, "garment.op.push", "MOD_SHRINKWRAP",
         info="garment.info.push")

    layout.separator(factor=GAP)
    body = section(layout, "problems", "garment.heading.problems", "COLOR", info="garment.info.problems")
    if body is not None:
        draw_problems(body, context)
    body = section(layout, "regions", "garment.heading.regions", "MOD_SMOOTH", info="garment.info.regions")
    if body is not None:
        draw_region_tools(body, context)
    body = section(layout, "sculpt", "garment.heading.sculpt", "SCULPTMODE_HLT", info="garment.info.sculpt")
    if body is not None:
        operator(body, DCTLINK_OT_fit_sculpt_start.bl_idname, "garment.op.sculpt", "SCULPTMODE_HLT")
        options_body = options(body, context, "sculpt")
        if options_body is not None:
            options_body.prop(settings_, "sculpt_radius", text=t("garment.prop.radius"), translate=False)
            options_body.prop(settings_, "sculpt_strength", text=t("garment.prop.strength"), translate=False)
            ui.checkbox(options_body, context, settings_, "sculpt_mirror", "garment.prop.mirror")
            ui.checkbox(options_body, context, settings_, "sculpt_keep_out", "garment.prop.keep-out")
    body = section(layout, "tears", "garment.heading.tears", "MOD_PHYSICS", info="garment.info.tears")
    if body is not None:
        operator(body, DCTLINK_OT_fit_check_tears.bl_idname, "garment.op.tears", "MOD_PHYSICS")
        if obj is not None:
            reason_text(body, context, gh.tears_problem(obj))
        draw_tears(body, context)


def draw_region_tools(layout: Any, context: Any, title: bool = False) -> None:
    settings_ = props(context)
    if title:
        heading(layout, context, "garment.heading.regions", "MOD_SMOOTH", info="garment.info.regions")
    labelled(layout, context, settings_, "region", "garment.prop.region")
    layout.prop(settings_, "snug_gap", text=t("garment.prop.gap"), translate=False)
    layout.prop(settings_, "amount", text=t("garment.prop.amount"), translate=False)
    row = ui.button_group(layout, context, ("garment.op.snug", "garment.op.relax"))
    operator(row, DCTLINK_OT_fit_snug.bl_idname, "garment.op.snug", "FULLSCREEN_EXIT")
    operator(row, DCTLINK_OT_fit_relax.bl_idname, "garment.op.relax", "MOD_SMOOTH")
    reason_text(layout, context, _region_reason(context, True))


def draw_problems(layout: Any, context: Any, title: bool = False) -> None:
    obj = current_garment(context)
    shown = gh.problems_shown(obj)
    if title:
        heading(layout, context, "garment.heading.problems", "COLOR", info="garment.info.problems")
    row = layout.row(align=True)
    row.operator(DCTLINK_OT_fit_show_problems.bl_idname, text=t("garment.op.problems"),
                 icon="HIDE_OFF" if shown else "HIDE_ON", depress=shown, translate=False)
    row.operator(DCTLINK_OT_fit_refresh_problems.bl_idname, text="", icon="FILE_REFRESH")
    if shown:
        column = layout.column(align=True)
        for name in ("inside", "close", "stretched", "floating"):
            column.label(text=t(f"garment.problem.{name}"), icon=PROBLEM_ICONS[name], translate=False)


def _mm(value: float) -> str:
    """Whole millimetres (the measurement is no finer than that)."""
    return f"{value:.0f}" if round(value) != 0 else "0"


#: Room around a fit check cell's text (interface units): the measurement's column also holds the warning icon.
REPORT_PADDING = (8, 30, 8)
#: The share of the region's column when the usual range goes under each row instead of into its own column.
REPORT_NARROW = 0.42


def _report_row(column: Any, cells: Tuple[str, ...], shares: Optional[Tuple[float, ...]], icon: str = "NONE") -> None:
    """A row of the fit check: region, measurement and, with ``shares`` (the columns' parts of the width), the usual
    range."""
    if shares is None:
        line = column.split(factor=REPORT_NARROW, align=True)
        line.label(text=cells[0], translate=False)
        line.label(text=cells[1], icon=icon, translate=False)
        return
    line = column.split(factor=shares[0], align=True)
    line.label(text=cells[0], translate=False)
    rest = line.split(factor=shares[1] / (1.0 - shares[0]), align=True)
    rest.label(text=cells[1], icon=icon, translate=False)
    rest.label(text=cells[2], translate=False)


def report_columns(context: Any, rows: List[Tuple[str, str, str]]) -> Optional[Tuple[float, float, float]]:
    """The parts of the width the fit check's three columns take, each as wide as its longest text needs with the
    room left over shared out, or ``None`` when the three do not fit side by side without cutting a cell."""
    measure = ui._measure(context)
    scale = ui._scale(context)
    width = ui.content_width(context)
    needed = [max(measure(row[index]) for row in rows) + REPORT_PADDING[index] * scale for index in range(3)]
    if sum(needed) > width:
        return None
    spare = (width - sum(needed)) / 3.0
    return tuple((need + spare) / width for need in needed)


def usual_ranges(context: Any) -> Tuple[Optional[Dict[str, Tuple[float, float, float]]], Optional[str]]:
    """How far game clothing of the garment's kind usually sits from each region (from gta.clothing), or ``None`` with
    the text that says why there is none (``None`` while it is asked for)."""
    settings_ = props(context)
    body = valid_body(context)
    version = _hosted_version(body)
    category = garment_fit.REFERENCE_CATEGORIES.get(settings_.slot)
    if version is None or category is None:
        return None, None
    ctrl = state.get()
    if not ctrl.fitting.ready():
        return None, "garment.check.reference-offline"
    reference = ctrl.fitting.reference(body_gender(context, body), category, version)
    if reference is None:
        return None, None
    return garment_fit.usual_ranges(reference, settings_.category), None


def draw_report(layout: Any, context: Any) -> None:
    """The fit check's table: each region's distance from the body beside the usual range of game clothing. When the
    three columns would cut a value (a narrow sidebar, a longer language), the usual range goes on a dimmed line
    under its region."""
    report = garment.FitReport.from_json(gh.stored_text(current_garment(context), gh.FIT_REPORT))
    if report is None:
        subtext(layout, context, "garment.check.none")
        return
    usual, why = usual_ranges(context)
    none = t("garment.check.reference-none")
    rows = []
    for row in report.rows:
        found = (usual or {}).get(row.region)
        third = t("garment.check.value", p10=_mm(found[0]), p50=_mm(found[1]), p90=_mm(found[2])) if found else none
        rows.append((t(f"garment.region.{row.region}"),
                     t("garment.check.value", p50=_mm(row.p50), p10=_mm(row.p10), p90=_mm(row.p90)), third,
                     "ERROR" if row.inside else "BLANK1"))
    titles = (t("garment.prop.region"), t("garment.check.measured"), t("garment.check.reference"))
    shares = report_columns(context, [titles] + [row[:3] for row in rows])
    column = layout.column(align=True)
    _report_row(column, titles, shares)
    for first, second, third, icon in rows:
        _report_row(column, (first, second, third), shares, icon)
        if shares is None and usual:
            line = column.split(factor=REPORT_NARROW, align=True)
            line.label(text="", translate=False)
            cell = line.row(align=True)
            cell.active = False
            cell.label(text=t("garment.check.usual-line", range=third), icon="BLANK1", translate=False)
    share = round(100.0 * report.inside_share, 1)
    wrapped(layout, context, t("garment.check.inside", count=report.inside, share=share),
            "ERROR" if report.inside else "CHECKMARK")
    for key, fields in garment.fit_advice(report):
        wrapped(layout, context, t(key, **fields), "INFO")
    if usual:
        subtext(layout, context, "garment.check.reference-subtext")
    elif why is not None:
        subtext(layout, context, why)


def draw_sculpt_session(layout: Any, context: Any) -> None:
    """A sculpt session: Accept or Cancel, Keep Out of Body, and the problem colours and region tools to work with."""
    settings_ = props(context)
    obj = current_garment(context)
    heading(layout, context, "garment.heading.sculpt", "SCULPTMODE_HLT", info="garment.info.sculpt")
    if gh.session_broken(obj):
        wrapped(layout, context, t("garment.sculpt.broken"), "ERROR")
    else:
        guide(layout, context, "garment.sculpt.running")
    row = ui.button_group(layout, context, ("garment.op.accept", "op.cancel-sign-in"))
    row.scale_y = ui.PRIMARY_SCALE
    operator(row, DCTLINK_OT_fit_sculpt_accept.bl_idname, "garment.op.accept", "CHECKMARK")
    operator(row, DCTLINK_OT_fit_sculpt_cancel.bl_idname, "op.cancel-sign-in", "X")
    subtext(layout, context, "garment.sculpt.subtext")
    layout.separator(factor=GAP_SMALL)
    ui.checkbox(layout, context, settings_, "sculpt_keep_out", "garment.prop.keep-out")
    layout.separator(factor=GAP)
    draw_problems(layout, context, title=True)
    if not gh.session_broken(obj):
        layout.separator(factor=GAP)
        draw_region_tools(layout, context, title=True)


def draw_tears(layout: Any, context: Any) -> None:
    result = RUNTIME.tears
    obj = current_garment(context)
    if not result or obj is None or RUNTIME.tears_of != obj.name:
        return
    for pose in result["poses"]:
        if pose.get("skipped"):
            wrapped(layout, context, t("garment.tears.pose-skipped", pose=t(pose["pose"])), "INFO")
            continue
        icon = "ERROR" if pose["torn"] else "CHECKMARK"
        key = "garment.tears.pose" if pose["torn"] else "garment.tears.pose-clean"
        wrapped(layout, context, t(key, pose=t(pose["pose"]), count=pose["torn"], gap=_mm(pose["gap"]),
                                   stretched=pose["stretched"]), icon)


def draw_ready(layout: Any, context: Any) -> None:
    """Game Ready's steps in their order, one row each, with a tick once done: Prepare Garment, Combine Materials, the
    skeleton and the weights (a prop: its anchor), Generate LODs and Validate."""
    settings_ = props(context)
    flow = flow_state(context)
    tool(layout, context, DCTLINK_OT_fit_prepare.bl_idname, "garment.op.prepare", "MODIFIER",
         info="garment.info.prepare", done=flow.prepared)
    body = options(layout, context, "prepare")
    if body is not None:
        body.prop(settings_, "weld", text=t("garment.prop.weld"), translate=False)
        for name, key in (("colour_1", "garment.prop.colour-1"), ("colour_2", "garment.prop.colour-2")):
            labelled(body, context, settings_, name, key)
        ui.checkbox(body, context, settings_, "overwrite_colours", "garment.prop.overwrite")

    layout.separator(factor=GAP)
    tool(layout, context, DCTLINK_OT_fit_combine.bl_idname, "garment.op.combine", "NODE_TEXTURE",
         info="garment.info.combine", done=flow.prepared and flow.materials <= 1)
    body = options(layout, context, "combine")
    if body is not None:
        row = body.row(align=True)
        row.prop(settings_, "texture_size", expand=True)
        ui.checkbox(body, context, settings_, "cut_strips", "garment.prop.cut")

    layout.separator(factor=GAP)
    if _is_prop(context):
        draw_anchor_status(layout, context)
    else:
        draw_skeleton(layout, context)
        layout.separator(factor=GAP)
        draw_service(layout, context, "weights")
        if garment.garment_type(settings_.category).bridge:
            operator(layout, DCTLINK_OT_fit_bridge.bl_idname, "garment.op.bridge", "MOD_VERTEX_WEIGHT")

    layout.separator(factor=GAP)
    tool(layout, context, DCTLINK_OT_fit_lods.bl_idname, "garment.op.lods", "MOD_DECIM", info="garment.info.lods",
         done=flow.lods)
    if not gh.sollumz_lods_available():
        reason_text(layout, context, msg("garment.why.no-sollumz"))
    body = options(layout, context, "lods")
    if body is not None:
        body.prop(settings_, "lod_medium", text=t("garment.prop.lod-medium"), translate=False)
        body.prop(settings_, "lod_low", text=t("garment.prop.lod-low"), translate=False)

    layout.separator(factor=GAP)
    tool(layout, context, DCTLINK_OT_fit_validate.bl_idname, "garment.op.validate", "CHECKMARK",
         info="garment.info.validate", done=flow.validated)
    draw_findings(layout, context)


def draw_service(layout: Any, context: Any, operation: str) -> None:
    """Fit to Body (under Fit) or Transfer Weights (under Game Ready): the button, the run's progress with Cancel, the
    fits left today, how the last run ended, and (Fit to Body) its options."""
    ctrl = state.get()
    obj = current_garment(context)
    flow = flow_state(context)
    if operation == "fit":
        idname, key, icon = DCTLINK_OT_fit_service_fit.bl_idname, "garment.op.service-fit", "WORLD"
        info, done = "garment.info.service", flow.fitted
    else:
        idname, key, icon = DCTLINK_OT_fit_service_weights.bl_idname, "garment.op.service-weights", "MOD_VERTEX_WEIGHT"
        info, done = "garment.info.weights", flow.weighted
    run = ctrl.fitting.run
    if run is not None and not run.handled and run.operation == operation:
        if hasattr(layout, "progress"):
            layout.progress(factor=run.fraction(), text=strings.text(run.status_text()))
        else:
            wrapped(layout, context, strings.text(run.status_text()), "SORTTIME")
        operator(layout, DCTLINK_OT_fit_service_cancel.bl_idname, "op.cancel-sign-in", "X")
    else:
        tool(layout, context, idname, key, icon, info=info, done=done)
        if obj is not None:
            reason = _service_reason(context, operation)
            if reason is not None and reason.key != "garment.why.align-first":
                reason_text(layout, context, reason)
    if ctrl.fitting.ready():
        ctrl.fitting.want_allowance()
        allowance = ctrl.fitting.allowance
        if allowance is not None:
            subtext(layout, context, "fit.left", left=allowance.remaining_today, total=allowance.per_day)
    if obj is not None and RUNTIME.fit_operation == operation and RUNTIME.fit_of == obj.session_uid:
        for level, line in RUNTIME.fit_lines:
            wrapped(layout, context, strings.text(line), ui.LEVEL_ICONS.get(level, "INFO"), alert=level == "ERROR")
    if operation == "fit":
        settings_ = props(context)
        body = options(layout, context, "service")
        if body is not None:
            body.prop(settings_, "fit_clearance", text=t("garment.prop.clearance"), translate=False)
            ui.checkbox(body, context, settings_, "fit_push", "garment.prop.service-push")
            body.prop(settings_, "fit_max_push", text=t("garment.prop.max-push"), translate=False)
            body.prop(settings_, "fit_seam_gap", text=t("garment.prop.seam-gap"), translate=False)
            ui.checkbox(body, context, settings_, "fit_proportions", "garment.prop.proportions")


def draw_findings(layout: Any, context: Any) -> None:
    findings = garment.findings_from_json(gh.stored_text(current_garment(context), gh.FINDINGS))
    if findings is None:
        return
    if not findings:
        wrapped(layout, context, t("garment.validate.clean"), "CHECKMARK")
        return
    if garment.is_clean(findings):
        wrapped(layout, context, t("garment.validate.clean"), "CHECKMARK")
    for finding in findings:
        fields = dict(finding.fields)
        if "level" in fields:
            fields["level"] = t(f"garment.level.{fields['level']}")
        key = f"garment.finding.{finding.code}"
        text = t(key, **fields) if key in EN else finding.code
        wrapped(layout, context, text, SEVERITY_ICONS.get(finding.severity, "INFO"))


def _skeleton_line(layout: Any, context: Any, obj: Any) -> None:
    gender = props(context).gender
    skeleton = gdct.skeleton_of(obj)
    bones = state.get().skeletons.bones(gender)
    problem = gdct.skeleton_problem(obj, gender, bones)
    if skeleton is not None and problem is None:
        wrapped(layout, context, t("add.skeleton.ready", name=skeleton.root.name, gender=t(f"gender.{gender}"),
                                   count=len(gdct.armature_bones(skeleton.armature))), "CHECKMARK")
    else:
        wrapped(layout, context, strings.text(problem or msg("add.skeleton.missing")), "INFO")


def draw_anchor_status(layout: Any, context: Any) -> None:
    """Where a prop goes into the game from: its anchor (the add hangs it there)."""
    obj = current_garment(context)
    slot = props(context).slot
    rig = gdct.prop_rig_of(obj)
    row = layout.row()
    if rig is not None and rig.gender == slot:
        wrapped(row.column(), context, t("add.anchor.ready", name=rig.root.name, anchor=t(f"garment.slot.{slot}")),
                "CHECKMARK", reserve=24)
    else:
        wrapped(row.column(), context, t("add.anchor.missing", anchor=t(f"garment.slot.{slot}")), "INFO", reserve=24)
    info_button(row, "add.info.anchor")


def draw_skeleton(layout: Any, context: Any) -> None:
    """The freemode skeleton the garment is weighted to: before the levels of detail, which take the weights over."""
    obj = current_garment(context)
    if obj is not None:
        _skeleton_line(layout, context, obj)
    tool(layout, context, DCTLINK_OT_fit_use_skeleton.bl_idname, "add.op.skeleton", "ARMATURE_DATA",
         info="add.info.skeleton", done=flow_state(context).skeleton)


def draw_add(layout: Any, context: Any) -> None:
    """Add to Project: the cloth's name, slot and gender (from Setup), Shows Skin, the colour variations (a closed
    section), the button, its progress and Durty Cloth Tool's answer."""
    settings_ = props(context)
    ctrl = state.get()
    obj = current_garment(context)
    if not ctrl.ready:
        wrapped(layout, context, t("add.why.connect"), "UNLINKED")
        if not ctrl.connecting and not ctrl.setup_needed:  # while setup is needed, Get Connected has the buttons
            operator(layout, "dct_link.connect", "op.connect", "LINKED")
    elif ctrl.project is None:
        wrapped(layout, context, t("add.why.no-project"), "INFO")
    else:
        wrapped(layout, context, t("linked.project", name=str(ctrl.project.get("name") or "")), "FILE_BLEND")
    if ui._measure(context)(t("add.prop.name")) + 12 * ui._scale(context) <= 0.4 * ui.content_width(context):
        labelled(layout, context, settings_, "item_name", "add.prop.name")
    else:  # a long label (in some languages) goes above the field instead of being cut off
        column = layout.column(align=True)
        wrapped(column, context, t("add.prop.name"))
        column.prop(settings_, "item_name", text="")
    subtext(layout, context, "add.target", slot=t(f"garment.slot.{settings_.slot}"),
            gender=t(f"gender.{settings_.gender}"))
    if not _is_prop(context):  # a prop never shows skin
        ui.checkbox(layout, context, settings_, "skin", "add.prop.skin")

    layout.separator(factor=GAP_SMALL)
    body = section(layout, "variations", "add.heading.variations", "IMAGE_DATA", info="add.info.variations")
    if body is not None:
        diffuse = gdct.garment_images(obj)["diffuse"] if obj is not None else None
        column = body.column(align=True)
        row = column.row(align=True)
        split = row.split(factor=0.45, align=True)
        split.label(text=diffuse.name if diffuse is not None else t("add.variation.none"),
                    icon="IMAGE_DATA" if diffuse is not None else "ERROR", translate=False)
        split.prop(settings_, "first_title", text="")
        for index, variation in enumerate(settings_.variations):
            row = column.row(align=True)
            split = row.split(factor=0.45, align=True)
            split.prop(variation, "image", text="")
            split.prop(variation, "title", text="")
            operator(row, DCTLINK_OT_fit_remove_variation.bl_idname, None, "X", text="", index=index)
        operator(body, DCTLINK_OT_fit_add_variation.bl_idname, "add.op.add-variation", "ADD")
        subtext(body, context, "add.variations.subtext", count=1 + len(settings_.variations),
                limit=garment_add.MAX_VARIATIONS)

    layout.separator(factor=GAP)
    adding = ctrl.item_add.adding
    job, add_job = RUNTIME.job, RUNTIME.add_job
    if job is not None or add_job is not None or adding:
        # Where the add is (the skeleton, the export and pictures, then Durty Cloth Tool's answer), and what now.
        if add_job is not None:
            done, total, text = add_job.done, add_job.steps + 1, add_job.text()
        elif job is not None:
            done, total, text = 0, 3, t("add.progress.skeleton")
        else:
            done, total = 2, 3
            text = t("add.withdrawing") if ctrl.item_add.withdrawing else t("add.waiting")
        if hasattr(layout, "progress"):
            layout.progress(factor=min(1.0, (done + 1) / total), text=f"{done + 1} / {total}")
        wrapped(layout, context, text, "SORTTIME")
        if adding:
            subtext(layout, context, "add.waiting.subtext")
        operator(layout, DCTLINK_OT_fit_cancel_add.bl_idname, "op.cancel-sign-in", "X")
    else:
        tool(layout, context, DCTLINK_OT_fit_add_to_dct.bl_idname, "add.op.add", "EXPORT", info="add.info",
             done=flow_state(context).added)
        reason = _add_reason(context) if obj is not None else None
        if reason is not None and reason.key not in ("add.why.connect", "add.why.no-project"):
            reason_text(layout, context, reason)  # the connection and the project are said above already
    draw_add_outcome(layout, context, obj)


def draw_add_outcome(layout: Any, context: Any, obj: Optional[Any]) -> None:
    """What the add's checks found, and Durty Cloth Tool's answer with its findings."""
    ctrl = state.get()
    if obj is not None and RUNTIME.add_of == obj.session_uid:
        if RUNTIME.add_problems:
            layout.separator(factor=GAP_SMALL)
            wrapped(layout, context, t("add.problems", count=len(RUNTIME.add_problems)), "CANCEL", alert=True)
            for problem in RUNTIME.add_problems:
                wrapped(layout, context, strings.text(problem), "BLANK1")
        for warning in RUNTIME.add_warnings:
            wrapped(layout, context, strings.text(warning), "ERROR")
    status = ctrl.item_add.status
    if status is None or ctrl.item_add.adding:
        return  # while Durty Cloth Tool asks, the step above says it
    layout.separator(factor=GAP_SMALL)
    ui.draw_notice(layout, context, status)
    findings = ctrl.item_add.findings
    if findings:
        wrapped(layout, context, t("add.findings", count=len(findings)), "INFO")
        for finding in findings:
            severity = str(finding.get("severity"))
            wrapped(layout, context, t(f"severity.{severity}") + ": " + strings.text(
                garment_add.finding_text(str(finding.get("code")))), SEVERITY_ICONS.get(severity, "INFO"), indent=True)
    if ctrl.item_add.added is not None:
        subtext(layout, context, "add.added.subtext")


STAGE_DRAW = {"setup": draw_setup, "fit": draw_fit, "fix": draw_fix, "ready": draw_ready, "add": draw_add}


# --------------------------------------------------------------------------------------------------
# The markers' stick figure in the 3D view
# --------------------------------------------------------------------------------------------------

_STICK: Dict[str, Any] = {"handle": None, "shader": None}


def _draw_stick_figure() -> None:
    """Lines between the chosen garment's markers, green while they look plausible and orange when not, so a marker
    that sits on the wrong joint stands out."""
    context = bpy.context
    scene = getattr(context, "scene", None)
    settings_ = getattr(scene, "dct_garment", None) if scene is not None else None
    if settings_ is None or current_garment(context) is None or ui.workspace(context) != "GARMENT":
        return  # the lines belong to Garment Fitting, as Custom Ped's markers belong to Custom Ped
    try:
        markers = gh.read_markers(scene)
        lines = garment.stick_figure(markers)
        if not lines:
            return
        import gpu
        from gpu_extras.batch import batch_for_shader

        expected = garment.markers_for(settings_.category)
        complete = all(name in markers for name in expected)
        bad = complete and bool(garment.marker_problems(markers, settings_.category))
        colour = (1.0, 0.55, 0.1, 0.9) if bad else (0.2, 0.85, 0.35, 0.9)
        points = [p for line in lines for p in line]
        shader = _STICK["shader"]
        if shader is None:
            try:
                shader = gpu.shader.from_builtin("POLYLINE_UNIFORM_COLOR")
            except (ValueError, SystemError):
                shader = gpu.shader.from_builtin("UNIFORM_COLOR")
            _STICK["shader"] = shader
        batch = batch_for_shader(shader, "LINES", {"pos": points})
        gpu.state.depth_test_set("NONE")
        gpu.state.blend_set("ALPHA")
        shader.bind()
        try:
            region = context.region
            shader.uniform_float("viewportSize", (region.width, region.height))
            shader.uniform_float("lineWidth", 2.5)
        except (AttributeError, ValueError):
            pass  # the plain shader has neither
        shader.uniform_float("color", colour)
        batch.draw(shader)
        gpu.state.blend_set("NONE")
    except (ReferenceError, AttributeError, ImportError, ValueError, SystemError):
        return  # nothing to draw on (background mode, a scene being freed)


def _register_stick_figure() -> None:
    if _STICK["handle"] is None and not bpy.app.background:
        _STICK["handle"] = bpy.types.SpaceView3D.draw_handler_add(_draw_stick_figure, (), "WINDOW", "POST_VIEW")


def _unregister_stick_figure() -> None:
    if _STICK["handle"] is not None:
        bpy.types.SpaceView3D.draw_handler_remove(_STICK["handle"], "WINDOW")
        _STICK["handle"] = None
    _STICK["shader"] = None


# --------------------------------------------------------------------------------------------------
# Panels
# --------------------------------------------------------------------------------------------------


class DCTLINK_PT_garment(ui._SubPanel, Panel):
    bl_label = EN["garment.panel"]
    bl_order = 0

    @classmethod
    def poll(cls, context):
        return (state.controller is not None and getattr(context.scene, "dct_garment", None) is not None
                and ui.workspace(context) == "GARMENT")

    def draw_header(self, context):
        self.layout.label(text="", icon="MOD_CLOTH")

    def draw(self, context):
        draw_main(self.layout, context)


CLASSES = (
    DCTLINK_PG_variation,
    DCTLINK_PG_garment,
    DCTLINK_OT_fit_use_garment,
    DCTLINK_OT_fit_import_garment,
    DCTLINK_OT_fit_add_body,
    DCTLINK_OT_fit_cancel_body,
    DCTLINK_OT_fit_body_file,
    DCTLINK_OT_fit_auto_markers,
    DCTLINK_OT_fit_mirror_markers,
    DCTLINK_OT_fit_save_preset,
    DCTLINK_OT_fit_load_preset,
    DCTLINK_MT_fit_presets,
    DCTLINK_OT_fit_align,
    DCTLINK_OT_fit_snap_anchor,
    DCTLINK_OT_fit_split_waist,
    DCTLINK_OT_fit_bridge,
    DCTLINK_OT_fit_tpose_to_apose,
    DCTLINK_OT_fit_restore,
    DCTLINK_OT_fit_back_step,
    DCTLINK_OT_fit_remove_backups,
    DCTLINK_OT_fit_push_out,
    DCTLINK_OT_fit_snug,
    DCTLINK_OT_fit_relax,
    DCTLINK_OT_fit_show_problems,
    DCTLINK_OT_fit_refresh_problems,
    DCTLINK_OT_fit_check,
    DCTLINK_OT_fit_sculpt_start,
    DCTLINK_OT_fit_sculpt_accept,
    DCTLINK_OT_fit_sculpt_cancel,
    DCTLINK_OT_fit_check_tears,
    DCTLINK_OT_fit_prepare,
    DCTLINK_OT_fit_combine,
    DCTLINK_OT_fit_lods,
    DCTLINK_OT_fit_validate,
    DCTLINK_OT_fit_service_fit,
    DCTLINK_OT_fit_service_weights,
    DCTLINK_OT_fit_service_cancel,
    DCTLINK_OT_fit_use_skeleton,
    DCTLINK_OT_fit_add_to_dct,
    DCTLINK_OT_fit_cancel_add,
    DCTLINK_OT_fit_add_variation,
    DCTLINK_OT_fit_remove_variation,
    DCTLINK_PT_garment,
)


def register() -> None:
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    bpy.types.Scene.dct_garment = PointerProperty(type=DCTLINK_PG_garment)
    _register_stick_figure()


def unregister() -> None:
    _unregister_stick_figure()
    if RUNTIME.download is not None:
        RUNTIME.download.cancel()
        RUNTIME.download = None
    if bpy.app.timers.is_registered(body_tick):
        bpy.app.timers.unregister(body_tick)
    RUNTIME.job = None
    RUNTIME.add_job = None
    if bpy.app.timers.is_registered(job_tick):
        bpy.app.timers.unregister(job_tick)
    del bpy.types.Scene.dct_garment
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)


def on_load_pre() -> None:
    """Another file is opened: a running download is dropped and the results shown belong to the old file."""
    if RUNTIME.download is not None:
        RUNTIME.download.cancel()
        RUNTIME.download = None
    RUNTIME.notice = None
    RUNTIME.tears = RUNTIME.tears_of = None
    RUNTIME.job = None
    if RUNTIME.add_job is not None:
        RUNTIME.add_job.cancel()
        RUNTIME.add_job = None
    RUNTIME.marker_notes.clear()
    RUNTIME.stepping = None  # Blender ends a running step with the old file
    RUNTIME.add_problems, RUNTIME.add_warnings, RUNTIME.add_of = [], [], None
    RUNTIME.fit_lines, RUNTIME.fit_operation, RUNTIME.fit_of = [], None, None
    if state.controller is not None:
        state.controller.fitting.forget()  # a running fit is cancelled on gta.clothing and never applied
        state.controller.item_add.forget()
