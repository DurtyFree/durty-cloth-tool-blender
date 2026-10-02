# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2026 Schmid Software Solutions (https://schmid-software.de)
"""The "DCT" tab in the 3D View sidebar and the operators behind its buttons."""

from __future__ import annotations

import textwrap
from typing import Any, Callable, Optional

import bpy
from bpy.props import BoolProperty, EnumProperty, PointerProperty, StringProperty
from bpy.types import Operator, Panel, PropertyGroup

from . import host, link, settings, state
from .dct_link import auth, tokens
from .dct_link.session import PAIRING, SIGNING_IN, LinkError

LEVEL_ICONS = {"INFO": "INFO", "WARNING": "ERROR", "ERROR": "CANCEL"}

#: Failures an operator reports to the user instead of raising.
EXPECTED_FAILURES = (LinkError, auth.AuthError, tokens.SecretStoreError, ValueError, OSError)


# --------------------------------------------------------------------------------------------------
# Drawing helpers (shared with the preferences)
# --------------------------------------------------------------------------------------------------


def wrapped(layout: Any, context: Any, text: str, icon: str = "NONE") -> None:
    """A label that wraps to the region width (Blender labels do not wrap by themselves)."""
    region = getattr(context, "region", None)
    width = region.width if region is not None and region.width > 1 else 300
    system = getattr(getattr(context, "preferences", None), "system", None)
    scale = getattr(system, "ui_scale", 1.0) or 1.0  # includes the monitor's DPI scaling
    chars = max(20, int(width / (7.0 * scale)) - (8 if icon != "NONE" else 4))
    column = layout.column(align=True)
    for index, line in enumerate(textwrap.wrap(text, chars) or [""]):
        column.label(text=line, icon=icon if index == 0 else "BLANK1" if icon != "NONE" else "NONE")


def draw_notice(layout: Any, context: Any, notice: Optional[link.Notice]) -> None:
    if notice is not None and notice.text:
        wrapped(layout, context, notice.text, LEVEL_ICONS.get(notice.level, "INFO"))


def draw_connection(layout: Any, context: Any) -> None:
    ctrl = state.get()
    column = layout.column()
    column.label(text=ctrl.status_text(), icon="LINKED" if ctrl.ready else "UNLINKED")
    if not host.online_access():
        wrapped(column, context, settings.ONLINE_ACCESS_OFF, "ERROR")
    row = column.row(align=True)
    if ctrl.session is None or ctrl.state in ("idle", "stopped"):
        row.operator("dct_link.connect", icon="LINKED")
    else:
        row.operator("dct_link.disconnect", icon="UNLINKED")
    if ctrl.state == "waiting" and not ctrl.dct_seen:
        wrapped(column, context, "Start Durty Cloth Tool and turn on Creator Link in its options.")
    if ctrl.incompatible is not None:
        box = column.box()
        wrapped(box, context, settings.describe_error(ctrl.incompatible.get("code")), "ERROR")
        box.operator("dct_link.open_update_page", icon="URL")
    if ctrl.pairing_required is not None:
        box = column.box()
        wrapped(box, context, settings.describe_pairing_required(ctrl.pairing_required.reason,
                                                                 ctrl.pairing_required.endpoint_trusted), "ERROR")
        if ctrl.pairing_required.endpoint_trusted:
            box.operator("dct_link.request_pairing", text="Pair Again", icon="LINKED")
    elif ctrl.state == PAIRING or ctrl.pairing_not_started:
        draw_pairing(column.box(), context)
    if ctrl.state == SIGNING_IN or ctrl.active_sign_in() is not None or ctrl.starting_sign_in:
        draw_sign_in_code(column.box(), context)
    elif ctrl.signed_out:
        box = column.box()
        box.label(text="Signed out", icon="USER")
        draw_sign_in_buttons(box)
    draw_notice(column, context, ctrl.notice)


def draw_pairing(layout: Any, context: Any) -> None:
    ctrl = state.get()
    layout.label(text="Pair with Durty Cloth Tool", icon="LINKED")
    if ctrl.pairing_prompt is not None:
        wrapped(layout, context, "Type the six-digit code Durty Cloth Tool shows:")
        row = layout.row(align=True)
        row.prop(context.window_manager, "dct_link_pairing_code", text="")
        row.operator("dct_link.pair", icon="CHECKMARK")
    else:
        wrapped(layout, context, settings.CONNECT_AN_APP + ", then click Request Code.")
        layout.operator("dct_link.request_pairing", icon="FILE_REFRESH")


def _sign_in_code() -> Optional[tuple]:
    ctrl = state.get()
    active = ctrl.active_sign_in()
    if active is not None:
        return active
    prompt = ctrl.sign_in_prompt
    if prompt is not None:
        return settings.display_user_code(prompt.user_code), prompt.verification_uri_complete or prompt.verification_uri
    return None


def draw_sign_in_code(layout: Any, context: Any) -> None:
    code = _sign_in_code()
    layout.label(text="Sign in", icon="USER")
    if code is None:
        layout.label(text="Starting the sign-in")
        layout.operator("dct_link.cancel_sign_in", icon="X")
        return
    layout.label(text=f"Code: {code[0]}")
    wrapped(layout, context, "Approve it in Durty Cloth Tool when it asks, or open the sign-in page and check that "
                             "it shows the same code.")
    row = layout.row(align=True)
    row.operator("dct_link.open_sign_in_page", icon="URL")
    row.operator("dct_link.cancel_sign_in", icon="X", text="")


def draw_sign_in_buttons(layout: Any) -> None:
    row = layout.row(align=True)
    row.operator("dct_link.sign_in", icon="URL")
    row.operator("dct_link.sign_in_dct", icon="LINKED")


def draw_account(layout: Any, context: Any) -> None:
    ctrl = state.get()
    if ctrl.user_name:
        row = layout.row()
        row.label(text=f"Signed in as {ctrl.user_name}", icon="USER")
        row.operator("dct_link.sign_out", icon="X")
        return
    if ctrl.active_sign_in() is not None or ctrl.state == SIGNING_IN or ctrl.starting_sign_in:
        draw_sign_in_code(layout, context)
        return
    layout.label(text="Signed out" if ctrl.signed_out else "Not signed in", icon="USER")
    draw_sign_in_buttons(layout)


def draw_pairing_status(layout: Any, context: Any) -> None:
    ctrl = state.get()
    if ctrl.state == PAIRING or ctrl.pairing_not_started:
        draw_pairing(layout, context)
        return
    row = layout.row()
    if ctrl.paired:
        row.label(text="Paired with Durty Cloth Tool", icon="CHECKMARK")
        row.operator("dct_link.remove_pairing", icon="TRASH")
    else:
        row.label(text="Not paired", icon="UNLINKED")
        row.operator("dct_link.request_pairing", text="Pair", icon="LINKED")


# --------------------------------------------------------------------------------------------------
# Scene settings
# --------------------------------------------------------------------------------------------------


def _auto_push_changed(self: Any, context: Any) -> None:
    if state.controller is not None and not self.auto_push:
        state.controller.model.due_at = None


class DCTLINK_PG_scene(PropertyGroup):
    image: PointerProperty(
        name="Image",
        type=bpy.types.Image,
        description="The image to show on the cloth selected in Durty Cloth Tool",
    )
    target: EnumProperty(
        name="Texture",
        items=settings.TARGETS,
        default="diffuse",
        description="Which texture of the cloth the image replaces in the preview",
    )
    auto_push: BoolProperty(
        name="Push Automatically",
        default=False,
        update=_auto_push_changed,
        description="Push the model again shortly after you change it (after the first push)",
    )


# --------------------------------------------------------------------------------------------------
# Operators
# --------------------------------------------------------------------------------------------------


def _fail(operator: Operator, exc: BaseException) -> set:
    if isinstance(exc, LinkError):
        text = settings.describe_error(exc.code, exc.message)
    elif isinstance(exc, auth.AuthError):
        text = settings.describe_error(exc.code, str(exc))
    elif isinstance(exc, tokens.SecretStoreError):
        text = "The protected sign-in or pairing could not be read or written. Sign in or pair again."
    elif isinstance(exc, OSError):
        text = f"A file could not be read or written: {exc.strerror or exc}"
    else:
        text = str(exc)
    operator.report({"ERROR"}, text)
    return {"CANCELLED"}


def _run(operator: Operator, action: Callable[[], Any]) -> set:
    """Runs an operator's work and reports the failures a user can act on instead of raising them."""
    try:
        action()
    except EXPECTED_FAILURES as exc:
        return _fail(operator, exc)
    return {"FINISHED"}


class DCTLINK_OT_connect(Operator):
    bl_idname = "dct_link.connect"
    bl_label = "Connect"
    bl_description = "Connect to Durty Cloth Tool on this computer"

    def execute(self, context):
        return _run(self, lambda: state.get().connect())


class DCTLINK_OT_disconnect(Operator):
    bl_idname = "dct_link.disconnect"
    bl_label = "Disconnect"
    bl_description = "Disconnect from Durty Cloth Tool (live textures stop)"

    def execute(self, context):
        return _run(self, lambda: state.get().disconnect())


class DCTLINK_OT_request_pairing(Operator):
    bl_idname = "dct_link.request_pairing"
    bl_label = "Request Code"
    bl_description = ("Ask Durty Cloth Tool for a pairing code. Click Connect an app in Durty Cloth Tool "
                      "(Options > Creator Link) first")

    def execute(self, context):
        return _run(self, lambda: state.get().request_pairing())


class DCTLINK_OT_pair(Operator):
    bl_idname = "dct_link.pair"
    bl_label = "Pair"
    bl_description = "Send the six-digit code Durty Cloth Tool shows"

    def execute(self, context):
        wm = context.window_manager
        result = _run(self, lambda: state.get().submit_pairing_code(wm.dct_link_pairing_code))
        if "FINISHED" in result:
            wm.dct_link_pairing_code = ""
        return result


class DCTLINK_OT_remove_pairing(Operator):
    bl_idname = "dct_link.remove_pairing"
    bl_label = "Remove Pairing"
    bl_description = "Forget the pairing with Durty Cloth Tool on this computer. You need a new code to connect again"

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        return _run(self, lambda: state.get().remove_pairing())


class DCTLINK_OT_sign_in(Operator):
    bl_idname = "dct_link.sign_in"
    bl_label = "Sign In with Browser"
    bl_description = ("Sign in with your Durty Cloth Tool account (Discord) on gta.clothing in your browser. Needs "
                      "Blender's online access")

    def execute(self, context):
        result = _run(self, lambda: state.get().start_sign_in())
        if "FINISHED" in result:
            self.report({"INFO"}, "Your browser opens the sign-in page in a moment")
        return result


class DCTLINK_OT_sign_in_dct(Operator):
    bl_idname = "dct_link.sign_in_dct"
    bl_label = "Sign In through Durty Cloth Tool"
    bl_description = ("Connect to Durty Cloth Tool (pairing first if needed) and let it approve the sign-in with "
                      "the account it is signed in with")

    def execute(self, context):
        return _run(self, lambda: state.get().sign_in_with_dct())


class DCTLINK_OT_open_sign_in_page(Operator):
    bl_idname = "dct_link.open_sign_in_page"
    bl_label = "Open Sign-in Page"
    bl_description = "Open the gta.clothing page that approves this sign-in"

    def execute(self, context):
        code = _sign_in_code()
        if code is None:
            self.report({"WARNING"}, "No sign-in is waiting")
            return {"CANCELLED"}
        if not settings.is_gta_clothing_url(code[1]):
            self.report({"ERROR"}, "The sign-in link is not a gta.clothing link")
            return {"CANCELLED"}
        bpy.ops.wm.url_open(url=code[1])
        return {"FINISHED"}


class DCTLINK_OT_cancel_sign_in(Operator):
    bl_idname = "dct_link.cancel_sign_in"
    bl_label = "Cancel Sign-in"
    bl_description = "Stop waiting for the sign-in"

    def execute(self, context):
        return _run(self, lambda: state.get().cancel_sign_in())


class DCTLINK_OT_sign_out(Operator):
    bl_idname = "dct_link.sign_out"
    bl_label = "Sign Out"
    bl_description = "Sign out of your Durty Cloth Tool account in Blender and disconnect"

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        return _run(self, lambda: state.get().sign_out())


class DCTLINK_OT_open_update_page(Operator):
    bl_idname = "dct_link.open_update_page"
    bl_label = "Get the Update"
    bl_description = "Open the page with the current versions of Durty Cloth Tool and its plugins"

    def execute(self, context):
        incompatible = state.get().incompatible or {}
        url = incompatible.get("updateUrl")
        bpy.ops.wm.url_open(url=url if settings.is_gta_clothing_url(url) else settings.PLUGINS_PAGE_URL)
        return {"FINISHED"}


class DCTLINK_OT_use_paint_image(Operator):
    bl_idname = "dct_link.use_paint_image"
    bl_label = "Use Painted Image"
    bl_description = "Use the image you are painting on (or the one in the Image Editor)"

    def execute(self, context):
        image = host.painted_image(context)
        if image is None:
            self.report({"WARNING"}, "No painted image found. Choose the image in the list")
            return {"CANCELLED"}
        context.scene.dct_link.image = image
        return {"FINISHED"}


class DCTLINK_OT_stream_start(Operator):
    bl_idname = "dct_link.stream_start"
    bl_label = "Start Streaming"
    bl_description = ("Show this image on the cloth selected in Durty Cloth Tool and update it after each paint "
                      "stroke. Nothing is saved until you save")

    @classmethod
    def poll(cls, context):
        return state.is_ready()

    def execute(self, context):
        props = context.scene.dct_link
        image = props.image
        problem = host.image_problem(image)
        if problem:
            self.report({"ERROR"}, problem)
            return {"CANCELLED"}

        def start() -> None:
            source = host.BlenderImageSource(image, props.target)
            state.get().stream.start(source, props.target, source.width, source.height, source.conversion,
                                     document=image.name, warning=source.warning)

        try:
            return _run(self, start)
        except MemoryError:
            self.report({"ERROR"}, "Not enough memory to stream an image this large")
            return {"CANCELLED"}


class DCTLINK_OT_stream_stop(Operator):
    bl_idname = "dct_link.stream_stop"
    bl_label = "Stop"
    bl_description = "Stop streaming. Unsaved changes stay in the preview until Durty Cloth Tool drops them"

    def execute(self, context):
        return _run(self, lambda: state.get().stream.stop())


class DCTLINK_OT_stream_send_now(Operator):
    bl_idname = "dct_link.stream_send_now"
    bl_label = "Send Now"
    bl_description = "Send the image again now (for changes made by scripts, baking or reloading)"

    @classmethod
    def poll(cls, context):
        return state.controller is not None and state.controller.stream.is_open

    def execute(self, context):
        return _run(self, lambda: state.get().stream.send_now())


class DCTLINK_OT_stream_save(Operator):
    bl_idname = "dct_link.stream_save"
    bl_label = "Save"
    bl_description = "Save the streamed texture in the Durty Cloth Tool project"

    mode: EnumProperty(
        items=(
            ("replace", "Save to Cloth", "Replace the cloth's texture with this image"),
            ("newVariation", "Save as New Variation", "Add this image as a new texture variation (diffuse only)"),
        ),
        default="replace",
        options={"SKIP_SAVE"},
    )

    @classmethod
    def description(cls, context, properties):
        if properties.mode == "newVariation":
            return "Add this image to the cloth as a new texture variation (diffuse only)"
        return "Replace the cloth's texture with this image in the Durty Cloth Tool project"

    @classmethod
    def poll(cls, context):
        return state.controller is not None and state.controller.stream.is_open and not state.controller.stream.saving

    def execute(self, context):
        return _run(self, lambda: state.get().stream.save(self.mode))


class DCTLINK_OT_stream_discard(Operator):
    bl_idname = "dct_link.stream_discard"
    bl_label = "Discard"
    bl_description = "Drop the unsaved changes in Durty Cloth Tool's preview and stop streaming"

    @classmethod
    def poll(cls, context):
        return state.controller is not None and state.controller.stream.is_open

    def execute(self, context):
        return _run(self, lambda: state.get().stream.discard())


class DCTLINK_OT_model_push(Operator):
    bl_idname = "dct_link.model_push"
    bl_label = "Push Model"
    bl_description = ("Export the selected Sollumz Drawable Dictionary as CodeWalker XML and show it on the cloth "
                      "selected in Durty Cloth Tool. Nothing is saved until you save")

    @classmethod
    def poll(cls, context):
        return state.is_ready() and not state.get().model.pushing

    def execute(self, context):
        objects = list(context.selected_objects) or ([context.active_object] if context.active_object else [])
        return _run(self, lambda: state.push_model(host.drawable_root(objects)))


class DCTLINK_OT_model_save(Operator):
    bl_idname = "dct_link.model_save"
    bl_label = "Save to Cloth"
    bl_description = "Save the pushed model in the Durty Cloth Tool project (the old model stays in History)"

    @classmethod
    def poll(cls, context):
        if not state.is_ready():
            return False
        blocker = state.get().model.save_blocker
        if blocker is not None:
            cls.poll_message_set(blocker)
        return blocker is None

    def execute(self, context):
        return _run(self, lambda: state.get().model.save())


class DCTLINK_OT_model_discard(Operator):
    bl_idname = "dct_link.model_discard"
    bl_label = "Discard"
    bl_description = "Drop the pushed model from Durty Cloth Tool's preview"

    @classmethod
    def poll(cls, context):
        return state.is_ready() and state.get().model.lease is not None and state.get().model.busy is None

    def execute(self, context):
        return _run(self, lambda: state.get().model.discard())


# --------------------------------------------------------------------------------------------------
# Panels
# --------------------------------------------------------------------------------------------------


class _DCTPanel:
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "DCT"


class DCTLINK_PT_main(_DCTPanel, Panel):
    bl_label = "Durty Cloth Tool"

    def draw(self, context):
        if state.controller is None:
            self.layout.label(text="The add-on is not ready")
            return
        draw_connection(self.layout, context)


class DCTLINK_PT_focus(_DCTPanel, Panel):
    bl_label = "Selected in Durty Cloth Tool"
    bl_parent_id = "DCTLINK_PT_main"

    @classmethod
    def poll(cls, context):
        return state.is_ready()

    def draw(self, context):
        ctrl = state.get()
        column = self.layout.column(align=True)
        project = ctrl.project
        column.label(text=f"Project: {project.get('name')}" if project else "No project open", icon="FILE")
        for line in link.describe_focus(ctrl.focused):
            column.label(text=line)


class DCTLINK_PT_texture(_DCTPanel, Panel):
    bl_label = "Texture Streaming"
    bl_parent_id = "DCTLINK_PT_main"

    def draw(self, context):
        layout = self.layout
        ctrl = state.get()
        stream = ctrl.stream
        props = context.scene.dct_link
        problem = ctrl.feature_problem(settings.FEATURE_LIVE_TEXTURE) if ctrl.ready else None
        if problem:
            wrapped(layout, context, problem, "LOCKED")
        row = layout.row(align=True)
        row.enabled = not stream.active
        row.prop(props, "image", text="")
        row.operator("dct_link.use_paint_image", text="", icon="EYEDROPPER")
        row = layout.row()
        row.enabled = not stream.active
        row.prop(props, "target", expand=True)
        if not stream.active:
            layout.operator("dct_link.stream_start", icon="PLAY")
            if not ctrl.ready:
                layout.label(text="Connect to Durty Cloth Tool first")
        else:
            row = layout.row(align=True)
            row.operator("dct_link.stream_stop", icon="PAUSE")
            row.operator("dct_link.stream_send_now", icon="FILE_REFRESH")
            column = layout.column(align=True)
            column.operator("dct_link.stream_save", text="Save to Cloth", icon="CHECKMARK").mode = "replace"
            variation = column.row(align=True)
            variation.enabled = stream.target == "diffuse"
            variation.operator("dct_link.stream_save", text="Save as New Variation", icon="ADD").mode = "newVariation"
            column.operator("dct_link.stream_discard", icon="TRASH")
            if stream.live_state:
                layout.label(text=settings.describe_live_state(stream.live_state), icon="CHECKMARK"
                             if stream.live_state == "attached" else "INFO")
        draw_notice(layout, context, stream.status)


class DCTLINK_PT_model(_DCTPanel, Panel):
    bl_label = "Model Push"
    bl_parent_id = "DCTLINK_PT_main"

    def draw(self, context):
        layout = self.layout
        ctrl = state.get()
        model = ctrl.model
        available, text = host.sollumz_status()
        wrapped(layout, context, text, "CHECKMARK" if available else "ERROR")
        problem = ctrl.feature_problem(settings.FEATURE_MODEL) if ctrl.ready else None
        if problem:
            wrapped(layout, context, problem, "LOCKED")
        column = layout.column()
        column.enabled = available
        column.operator("dct_link.model_push", icon="EXPORT")
        column.prop(context.scene.dct_link, "auto_push")
        if model.lease is not None:
            row = layout.row(align=True)
            row.operator("dct_link.model_save", icon="CHECKMARK")
            row.operator("dct_link.model_discard", icon="TRASH")
            if model.root_name:
                layout.label(text=f"Model: {model.root_name}", icon="OUTLINER_OB_EMPTY")
        elif not ctrl.ready:
            layout.label(text="Connect to Durty Cloth Tool first")
        if model.waiting and model.due_at is not None:
            wrapped(layout, context, model.waiting, "TIME")
        draw_notice(layout, context, model.status)


CLASSES = (
    DCTLINK_PG_scene,
    DCTLINK_OT_connect,
    DCTLINK_OT_disconnect,
    DCTLINK_OT_request_pairing,
    DCTLINK_OT_pair,
    DCTLINK_OT_remove_pairing,
    DCTLINK_OT_sign_in,
    DCTLINK_OT_sign_in_dct,
    DCTLINK_OT_open_sign_in_page,
    DCTLINK_OT_cancel_sign_in,
    DCTLINK_OT_sign_out,
    DCTLINK_OT_open_update_page,
    DCTLINK_OT_use_paint_image,
    DCTLINK_OT_stream_start,
    DCTLINK_OT_stream_stop,
    DCTLINK_OT_stream_send_now,
    DCTLINK_OT_stream_save,
    DCTLINK_OT_stream_discard,
    DCTLINK_OT_model_push,
    DCTLINK_OT_model_save,
    DCTLINK_OT_model_discard,
    DCTLINK_PT_main,
    DCTLINK_PT_focus,
    DCTLINK_PT_texture,
    DCTLINK_PT_model,
)


def register() -> None:
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    bpy.types.Scene.dct_link = PointerProperty(type=DCTLINK_PG_scene)
    bpy.types.WindowManager.dct_link_pairing_code = StringProperty(
        name="Pairing Code",
        description="The six-digit code Durty Cloth Tool shows",
        maxlen=16,
    )


def unregister() -> None:
    del bpy.types.WindowManager.dct_link_pairing_code
    del bpy.types.Scene.dct_link
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
