# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2026 Schmid Software Solutions (https://schmid-software.de)
"""Garment Fitting (Experimental) in the DCT tab: the settings, operators and panels of the local garment tools.

The panel sits after Model, with the next step in its first line and four child panels, one per stage of the work:
Setup (gender, slot, category, source pose, the garment and the freemode body), Fit (markers, Align to Body,
backups), Fix (push out, region tools, problem colours, the fit check, the sculpt session, the tear check) and Game
Ready (prepare, combine materials, levels of detail, the local checks, and Add to Durty Cloth Tool: the freemode
skeleton from Durty Cloth Tool and the add of the garment as a new cloth of the open project). The button of the next
step is the large one; settings that rarely change sit in closed Options sections. Every operator that changes a mesh
can be undone; the garment keeps up to three backups for Back One Step and Restore Pre-fit.
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

from . import garment, garment_add, garment_body, host, link, state, strings, ui
from . import settings as addon_settings
from . import garment_dct as gdct
from . import garment_host as gh
from .dct_link import auth, protocol
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
SLOT_ITEMS = _items("garment.slot", garment.SLOTS)
POSE_ITEMS = _items("garment.pose", garment.SOURCE_POSES)
REGION_ITEMS = tuple((r, EN[f"garment.region.{r}"], EN["garment.region.desc"]) for r in garment.REGIONS)
UNIT_ITEMS = tuple((u, EN[f"garment.unit.{u}"], EN["garment.unit.desc"]) for u in ("auto", *garment.UNITS))
#: The categories of each slot (Blender keeps a dynamic enum's strings only while they are referenced).
CATEGORY_ITEMS = {
    slot: [(c, EN[f"garment.category.{c}"], EN[f"garment.category.{c}.desc"], garment.CATEGORIES.index(c))
           for c in garment.categories_for(slot)]
    for slot in garment.SLOTS
}
SIZE_ITEMS = (("2048", "2048", EN["garment.size.desc"]), ("4096", "4096", EN["garment.size.desc"]))
#: The ped shader's vertex colours most clothing uses (as Sollumz's clothing tutorial gives them): Color 1 #FF8000,
#: full ambient light and a medium reflection; Color 2 black with no alpha, no vertex wind and no sweat. Both can be
#: changed under Prepare Garment.
DEFAULT_COLOUR_1 = (1.0, 128.0 / 255.0, 0.0, 1.0)
DEFAULT_COLOUR_2 = (0.0, 0.0, 0.0, 0.0)


def _category_items(self: Any, context: Any) -> list:
    return CATEGORY_ITEMS.get(self.slot, CATEGORY_ITEMS["jbib"])


def _slot_changed(self: Any, context: Any) -> None:
    allowed = garment.categories_for(self.slot)
    if allowed and self.category not in allowed:
        self.category = allowed[0]


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
    slot: EnumProperty(name=EN["garment.prop.slot"], items=SLOT_ITEMS, default="jbib", update=_slot_changed,
                       description=EN["garment.prop.slot.desc"], translation_context=CONTEXT)
    category: EnumProperty(name=EN["garment.prop.category"], items=_category_items,
                           default=garment.CATEGORIES.index("tshirt"),
                           description=EN["garment.prop.category.desc"], translation_context=CONTEXT)
    source_pose: EnumProperty(name=EN["garment.prop.pose"], items=POSE_ITEMS, default="a_pose",
                              description=EN["garment.prop.pose.desc"], translation_context=CONTEXT)
    marker_size: FloatProperty(name=EN["garment.prop.marker-size"], default=0.03, min=0.005, max=0.2,
                               subtype="DISTANCE", unit="LENGTH", update=_marker_size_changed,
                               description=EN["garment.prop.marker-size.desc"], translation_context=CONTEXT)
    keep_size: BoolProperty(name=EN["garment.prop.keep-size"], default=False,
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
    lod_medium: IntProperty(name=EN["garment.prop.lod-medium"], default=0, min=0, max=200000,
                            description=EN["garment.prop.lod.desc"], translation_context=CONTEXT)
    lod_low: IntProperty(name=EN["garment.prop.lod-low"], default=0, min=0, max=100000,
                         description=EN["garment.prop.lod.desc"], translation_context=CONTEXT)
    item_name: StringProperty(name=EN["add.prop.name"], maxlen=protocol.MAX_TEXT_LENGTH,
                              description=EN["add.prop.name.desc"], translation_context=CONTEXT)
    skin: BoolProperty(name=EN["add.prop.skin"], default=False, description=EN["add.prop.skin.desc"],
                       translation_context=CONTEXT)
    first_title: StringProperty(name=EN["add.prop.variation-name"], maxlen=protocol.MAX_TEXT_LENGTH,
                                description=EN["add.prop.first-name.desc"], translation_context=CONTEXT)
    variations: CollectionProperty(type=DCTLINK_PG_variation)


# --------------------------------------------------------------------------------------------------
# Why a button is unavailable
# --------------------------------------------------------------------------------------------------


def _refuse(cls: Any, reason: Optional[Msg]) -> bool:
    return ui._refuse(cls, reason)


def _garment_reason(context: Any, *, sculpting_ok: bool = False) -> Optional[Msg]:
    if state.controller is None:
        return msg("notice.not-ready")
    return gh.garment_problem(context, current_garment(context), sculpting_ok=sculpting_ok)


def _body_reason(context: Any) -> Optional[Msg]:
    return gh.body_problem(context, props(context).body)


def _aligned(context: Any) -> bool:
    """The garment sits on the body: aligned, past the fitting steps (prepared), or a category without markers."""
    obj = current_garment(context)
    return (not garment.markers_for(props(context).category) or gh.flag(obj, "dct_aligned")
            or gh.flag(obj, "dct_prepared"))


def _fit_reason(context: Any, *, sculpting_ok: bool = False) -> Optional[Msg]:
    """A step that measures against the body: the garment, the body, and the garment aligned to the body (edits on a
    garment still on its maker's avatar would squash it towards a body it does not sit on)."""
    reason = _garment_reason(context, sculpting_ok=sculpting_ok) or _body_reason(context)
    if reason is None and not _aligned(context):
        reason = msg("garment.why.align-first")
    return reason


def _markers_reason(context: Any) -> Optional[Msg]:
    reason = _garment_reason(context)
    if reason is None and not garment.markers_for(props(context).category):
        reason = msg("garment.why.no-markers")
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
        if message is not None:
            self.report({"INFO"}, strings.text(message))
            notify("INFO", message)
        host.redraw()
        return {"FINISHED"}


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
            key = "garment.done.import-avatar" if info["avatar"] else (
                "garment.done.import-turned" if info["turned"] else "garment.done.import")
            return msg(key, name=obj.name, count=len(obj.data.vertices))

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
        return _refuse(cls, _markers_reason(context))

    def execute(self, context):
        def place() -> Msg:
            settings_ = props(context)
            obj = current_garment(context)
            positions = gh.world_positions(obj)
            result = garment.place_markers(positions, settings_.category, settings_.source_pose,
                                           gh.mesh_edges(obj.data))
            gh.write_markers(context.scene, result.markers, settings_.marker_size, obj)
            RUNTIME.marker_notes[obj.session_uid] = result.notes
            gh.clear_flags(obj, "dct_aligned", *gh.STALE)
            return msg("garment.done.markers", count=len(result.markers))

        return self.run(context, place, backup=False)


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
    result = gh.align(context, obj, gh.read_markers(context.scene), found, props(context).category,
                      keep_size=props(context).keep_size)
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


class DCTLINK_OT_fit_prepare(_MeshOp):
    bl_idname = "dct_link.fit_prepare"
    bl_label = EN["garment.op.prepare"]
    bl_description = EN["garment.op.prepare.desc"]

    @classmethod
    def poll(cls, context):
        return _refuse(cls, _garment_reason(context))

    def execute(self, context):
        def prepare() -> Msg:
            settings_ = props(context)
            result = gh.prepare(context, current_garment(context), settings_.weld / 1000.0,
                                (tuple(settings_.colour_1), tuple(settings_.colour_2)), settings_.overwrite_colours)
            if result["thick"]:
                return msg("garment.done.prepare-thick", welded=result["welded"], walls=result["walls"],
                           triangles=result["triangles"])
            key = "garment.done.prepare-lining" if result["lining"] else "garment.done.prepare"
            return msg(key, welded=result["welded"], removed=result["removed"], triangles=result["triangles"])

        return self.run(context, prepare)


class DCTLINK_OT_fit_combine(_MeshOp):
    bl_idname = "dct_link.fit_combine_materials"
    bl_label = EN["garment.op.combine"]
    bl_description = EN["garment.op.combine.desc"]

    @classmethod
    def poll(cls, context):
        reason = _garment_reason(context)
        if reason is None and not current_garment(context).data.uv_layers:
            reason = msg("garment.why.no-uv")
        return _refuse(cls, reason)

    def execute(self, context):
        def combine() -> Msg:
            settings_ = props(context)
            progress = gh.Progress(5)
            try:
                result = gh.combine_materials(context, current_garment(context), int(settings_.texture_size),
                                              settings_.cut_strips, progress)
            finally:
                progress.end()
            return msg("garment.done.combine", count=result["materials"], size=result["size"], used=result["used"],
                       cut=result["cut"], density=result["density"])

        return self.run(context, combine)


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
            result = gh.generate_lods(context, current_garment(context),
                                      {"medium": settings_.lod_medium, "low": settings_.lod_low},
                                      valid_body(context), settings_.push_gap / 1000.0)
            return msg("garment.done.lods", high=result["high"], medium=result["medium"], low=result["low"])

        return self.run(context, lods, backup=False)


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
            findings = garment.validate(gh.validate_stats(obj, valid_body(context)))
            obj[gh.FINDINGS] = garment.findings_to_json(findings)
            gh.set_flag(obj, "dct_validated", garment.is_clean(findings))
            if garment.is_clean(findings):
                return msg("garment.done.clean")
            return msg("garment.done.findings", count=len(findings))

        return self.run(context, validate, backup=False)


# --------------------------------------------------------------------------------------------------
# Adding the garment to Durty Cloth Tool
# --------------------------------------------------------------------------------------------------


class Job(NamedTuple):
    """A step that waits for Durty Cloth Tool's skeleton template: ``skeleton`` (Use Durty Cloth Tool Skeleton),
    ``add`` (Add to Durty Cloth Tool Project, which then goes on by itself) or ``align`` (Align to Body with the
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
    if reason is None and not state.get().ready:
        reason = msg("add.why.connect")
    return reason or host.model_open_problem() or _add_busy()


def _add_reason(context: Any) -> Optional[Msg]:
    """Why Add to Durty Cloth Tool Project is unavailable (what its checks find is shown after a click)."""
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
    findings = garment.validate(gh.validate_stats(obj, valid_body(context)))
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
            self.skeleton = ensure_skeleton(context, obj, self.gender)
            self.stage = "prepare"
            return 0.0
        if self.stage == "prepare":
            self._changing()
            self.images = gdct.prepare_garment(context, obj, self.skeleton)
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

        ctrl.item_add.start(self.slot, self.gender, bool(settings_.skin), name, chosen, files, on_added=added)
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
    settings_ = props(context)
    obj = current_garment(context)
    report = garment.FitReport.from_json(gh.stored_text(obj, gh.FIT_REPORT))
    ctrl = state.controller
    skeleton = gdct.skeleton_of(obj)
    expected = garment.markers_for(settings_.category)
    placed = gh.marker_objects(context.scene) if obj is not None else {}
    return garment.FlowState(
        garment=obj is not None,
        body=gh.body_problem(context, settings_.body) is None,
        category=settings_.category,
        source_pose=settings_.source_pose,
        markers=len([name for name in expected if name in placed]),
        aligned=gh.flag(obj, "dct_aligned"),
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


def draw_main(layout: Any, context: Any) -> None:
    key = garment.next_step(flow_state(context))
    wrapped(layout, context, t(key), "FORWARD")
    if RUNTIME.notice is not None:
        layout.separator(factor=GAP_SMALL)
        ui.draw_notice(layout, context, RUNTIME.notice)


def draw_setup(layout: Any, context: Any) -> None:
    settings_ = props(context)
    row = layout.row(align=True)
    row.prop(settings_, "gender", expand=True)
    labelled(layout, context, settings_, "slot", "garment.prop.slot")
    labelled(layout, context, settings_, "category", "garment.prop.category")
    layout.separator(factor=GAP_SMALL)
    heading(layout, context, "garment.prop.pose", info="garment.info.pose")
    row = layout.row(align=True)
    row.prop(settings_, "source_pose", expand=True)

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
    subtext(layout, context, "garment.body.subtext")


def draw_fit(layout: Any, context: Any) -> None:
    settings_ = props(context)
    obj = current_garment(context)
    heading(layout, context, "garment.heading.markers", "EMPTY_DATA", info="garment.info.markers")
    expected = garment.markers_for(settings_.category)
    if not expected:
        wrapped(layout, context, t("garment.why.no-markers"), "INFO")
    else:
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
        operator(layout, DCTLINK_OT_fit_mirror_markers.bl_idname, "garment.op.mirror", "MOD_MIRROR")
        body = options(layout, context, "markers")
        if body is not None:
            body.prop(settings_, "marker_size", text=t("garment.prop.marker-size"), translate=False)
            row = ui.button_group(body, context, ("garment.op.save-preset", "garment.op.load-preset"))
            operator(row, DCTLINK_OT_fit_save_preset.bl_idname, "garment.op.save-preset", "FILE_TICK")
            row.menu(DCTLINK_MT_fit_presets.bl_idname, text=t("garment.op.load-preset"), icon="FILE_FOLDER",
                     translate=False)

        layout.separator(factor=GAP)
        heading(layout, context, "garment.heading.align", "ORIENTATION_GIMBAL", info="garment.info.align")
        step(layout, context, DCTLINK_OT_fit_align.bl_idname, "garment.op.align", "ORIENTATION_GIMBAL")
        if obj is not None:
            reason_text(layout, context, _align_reason(context))
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
    heading(layout, context, "garment.heading.backups", "FILE_BACKUP", info="garment.info.backups")
    count = len(gh.backups(obj)) if obj is not None else 0
    subtext(layout, context, "garment.backups.count", count=count, limit=gh.MAX_BACKUPS)
    row = ui.button_group(layout, context, ("garment.op.back", "garment.op.restore"))
    operator(row, DCTLINK_OT_fit_back_step.bl_idname, "garment.op.back", "LOOP_BACK")
    operator(row, DCTLINK_OT_fit_restore.bl_idname, "garment.op.restore", "FILE_REFRESH")
    body = options(layout, context, "backups")
    if body is not None:
        operator(body, DCTLINK_OT_fit_remove_backups.bl_idname, "garment.op.remove-backups", "TRASH")


def draw_fix(layout: Any, context: Any) -> None:
    settings_ = props(context)
    obj = current_garment(context)
    if gh.sculpting(obj) or gh.session_broken(obj):
        draw_sculpt(layout, context)
        return
    reason = _fit_reason(context) if obj is not None else None
    if reason is not None and reason.key == "garment.why.align-first":
        wrapped(layout, context, strings.text(reason), "INFO")
        layout.separator(factor=GAP_SMALL)

    heading(layout, context, "garment.heading.check", "VIEWZOOM", info="garment.info.check")
    step(layout, context, DCTLINK_OT_fit_check.bl_idname, "garment.op.check", "VIEWZOOM")
    draw_report(layout, context)

    layout.separator(factor=GAP)
    heading(layout, context, "garment.heading.push", "MOD_SHRINKWRAP", info="garment.info.push")
    layout.prop(settings_, "push_gap", text=t("garment.prop.gap"), translate=False)
    step(layout, context, DCTLINK_OT_fit_push_out.bl_idname, "garment.op.push", "MOD_SHRINKWRAP")

    layout.separator(factor=GAP)
    draw_problems(layout, context)

    layout.separator(factor=GAP)
    draw_region_tools(layout, context)

    layout.separator(factor=GAP)
    draw_sculpt(layout, context)

    layout.separator(factor=GAP)
    heading(layout, context, "garment.heading.tears", "MOD_PHYSICS", info="garment.info.tears")
    operator(layout, DCTLINK_OT_fit_check_tears.bl_idname, "garment.op.tears", "MOD_PHYSICS")
    if obj is not None:
        reason_text(layout, context, gh.tears_problem(obj))
    draw_tears(layout, context)


def draw_region_tools(layout: Any, context: Any) -> None:
    settings_ = props(context)
    heading(layout, context, "garment.heading.regions", "MOD_SMOOTH", info="garment.info.regions")
    labelled(layout, context, settings_, "region", "garment.prop.region")
    layout.prop(settings_, "snug_gap", text=t("garment.prop.gap"), translate=False)
    layout.prop(settings_, "amount", text=t("garment.prop.amount"), translate=False)
    row = ui.button_group(layout, context, ("garment.op.snug", "garment.op.relax"))
    operator(row, DCTLINK_OT_fit_snug.bl_idname, "garment.op.snug", "FULLSCREEN_EXIT")
    operator(row, DCTLINK_OT_fit_relax.bl_idname, "garment.op.relax", "MOD_SMOOTH")
    reason_text(layout, context, _region_reason(context, True))


def draw_problems(layout: Any, context: Any) -> None:
    obj = current_garment(context)
    shown = gh.problems_shown(obj)
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


#: The share of the fit check table's width that the region column takes; the measurement takes the rest.
REPORT_REGION_SHARE = 0.4


def _report_row(column: Any, first: str, second: str, icon: str = "NONE") -> None:
    line = column.split(factor=REPORT_REGION_SHARE, align=True)
    line.label(text=first, translate=False)
    line.label(text=second, icon=icon, translate=False)


def draw_report(layout: Any, context: Any) -> None:
    report = garment.FitReport.from_json(gh.stored_text(current_garment(context), gh.FIT_REPORT))
    if report is None:
        subtext(layout, context, "garment.check.none")
        return
    column = layout.column(align=True)
    _report_row(column, t("garment.prop.region"), t("garment.check.measured"))
    for row in report.rows:
        _report_row(column, t(f"garment.region.{row.region}"),
                    t("garment.check.value", p50=_mm(row.p50), p10=_mm(row.p10), p90=_mm(row.p90)),
                    "ERROR" if row.inside else "BLANK1")
    share = round(100.0 * report.inside_share, 1)
    wrapped(layout, context, t("garment.check.inside", count=report.inside, share=share),
            "ERROR" if report.inside else "CHECKMARK")
    for key, fields in garment.fit_advice(report):
        wrapped(layout, context, t(key, **fields), "INFO")


def draw_sculpt(layout: Any, context: Any) -> None:
    settings_ = props(context)
    obj = current_garment(context)
    heading(layout, context, "garment.heading.sculpt", "SCULPTMODE_HLT", info="garment.info.sculpt")
    if gh.sculpting(obj) or gh.session_broken(obj):
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
        draw_problems(layout, context)
        if not gh.session_broken(obj):
            layout.separator(factor=GAP_SMALL)
            draw_region_tools(layout, context)
        return
    operator(layout, DCTLINK_OT_fit_sculpt_start.bl_idname, "garment.op.sculpt", "SCULPTMODE_HLT")
    body = options(layout, context, "sculpt")
    if body is not None:
        body.prop(settings_, "sculpt_radius", text=t("garment.prop.radius"), translate=False)
        body.prop(settings_, "sculpt_strength", text=t("garment.prop.strength"), translate=False)
        ui.checkbox(body, context, settings_, "sculpt_mirror", "garment.prop.mirror")
        ui.checkbox(body, context, settings_, "sculpt_keep_out", "garment.prop.keep-out")


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
    settings_ = props(context)
    heading(layout, context, "garment.heading.prepare", "MODIFIER", info="garment.info.prepare")
    step(layout, context, DCTLINK_OT_fit_prepare.bl_idname, "garment.op.prepare", "MODIFIER")
    body = options(layout, context, "prepare")
    if body is not None:
        body.prop(settings_, "weld", text=t("garment.prop.weld"), translate=False)
        for name, key in (("colour_1", "garment.prop.colour-1"), ("colour_2", "garment.prop.colour-2")):
            labelled(body, context, settings_, name, key)
        ui.checkbox(body, context, settings_, "overwrite_colours", "garment.prop.overwrite")

    layout.separator(factor=GAP)
    heading(layout, context, "garment.heading.combine", "NODE_TEXTURE", info="garment.info.combine")
    step(layout, context, DCTLINK_OT_fit_combine.bl_idname, "garment.op.combine", "NODE_TEXTURE")
    body = options(layout, context, "combine")
    if body is not None:
        row = body.row(align=True)
        row.prop(settings_, "texture_size", expand=True)
        ui.checkbox(body, context, settings_, "cut_strips", "garment.prop.cut")

    layout.separator(factor=GAP)
    draw_skeleton(layout, context)

    layout.separator(factor=GAP)
    heading(layout, context, "garment.heading.lods", "MOD_DECIM", info="garment.info.lods")
    step(layout, context, DCTLINK_OT_fit_lods.bl_idname, "garment.op.lods", "MOD_DECIM")
    if not gh.sollumz_lods_available():
        reason_text(layout, context, msg("garment.why.no-sollumz"))
    body = options(layout, context, "lods")
    if body is not None:
        body.prop(settings_, "lod_medium", text=t("garment.prop.lod-medium"), translate=False)
        body.prop(settings_, "lod_low", text=t("garment.prop.lod-low"), translate=False)

    layout.separator(factor=GAP)
    heading(layout, context, "garment.heading.validate", "CHECKMARK", info="garment.info.validate")
    step(layout, context, DCTLINK_OT_fit_validate.bl_idname, "garment.op.validate", "CHECKMARK")
    draw_findings(layout, context)
    layout.separator(factor=GAP)
    draw_add(layout, context)


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


def draw_skeleton(layout: Any, context: Any) -> None:
    """The freemode skeleton the garment is weighted to: before the levels of detail, which take the weights over."""
    obj = current_garment(context)
    heading(layout, context, "add.heading.skeleton", "ARMATURE_DATA", info="add.info.skeleton")
    if obj is not None:
        _skeleton_line(layout, context, obj)
    step(layout, context, DCTLINK_OT_fit_use_skeleton.bl_idname, "add.op.skeleton", "ARMATURE_DATA")


def draw_add(layout: Any, context: Any) -> None:
    """Add to Durty Cloth Tool: the cloth's name, slot and gender (from Setup), Shows Skin, the colour variations, the
    button, its progress and Durty Cloth Tool's answer."""
    settings_ = props(context)
    ctrl = state.get()
    obj = current_garment(context)
    heading(layout, context, "add.heading", "EXPORT", info="add.info")
    if not ctrl.ready:
        wrapped(layout, context, t("add.why.connect"), "UNLINKED")
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
    ui.checkbox(layout, context, settings_, "skin", "add.prop.skin")

    layout.separator(factor=GAP_SMALL)
    heading(layout, context, "add.heading.variations", "IMAGE_DATA", info="add.info.variations")
    diffuse = gdct.garment_images(obj)["diffuse"] if obj is not None else None
    column = layout.column(align=True)
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
    operator(layout, DCTLINK_OT_fit_add_variation.bl_idname, "add.op.add-variation", "ADD")
    subtext(layout, context, "add.variations.subtext", count=1 + len(settings_.variations),
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
        step(layout, context, DCTLINK_OT_fit_add_to_dct.bl_idname, "add.op.add", "EXPORT")
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
    if settings_ is None or current_garment(context) is None:
        return
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
        return state.controller is not None and getattr(context.scene, "dct_garment", None) is not None

    def draw_header(self, context):
        self.layout.label(text="", icon="MOD_CLOTH")

    def draw(self, context):
        draw_main(self.layout, context)


class _GarmentChild(ui._DCTPanel):
    bl_parent_id = "DCTLINK_PT_garment"

    @classmethod
    def poll(cls, context):
        return DCTLINK_PT_garment.poll(context)


class DCTLINK_PT_garment_setup(_GarmentChild, Panel):
    bl_label = EN["garment.panel.setup"]

    def draw(self, context):
        draw_setup(self.layout, context)


class DCTLINK_PT_garment_fit(_GarmentChild, Panel):
    bl_label = EN["garment.panel.fit"]
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        draw_fit(self.layout, context)


class DCTLINK_PT_garment_fix(_GarmentChild, Panel):
    bl_label = EN["garment.panel.fix"]
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        draw_fix(self.layout, context)


class DCTLINK_PT_garment_ready(_GarmentChild, Panel):
    bl_label = EN["garment.panel.ready"]
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        draw_ready(self.layout, context)


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
    DCTLINK_OT_fit_use_skeleton,
    DCTLINK_OT_fit_add_to_dct,
    DCTLINK_OT_fit_cancel_add,
    DCTLINK_OT_fit_add_variation,
    DCTLINK_OT_fit_remove_variation,
    DCTLINK_PT_garment,
    DCTLINK_PT_garment_setup,
    DCTLINK_PT_garment_fit,
    DCTLINK_PT_garment_fix,
    DCTLINK_PT_garment_ready,
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
    RUNTIME.add_problems, RUNTIME.add_warnings, RUNTIME.add_of = [], [], None
    if state.controller is not None:
        state.controller.item_add.forget()
