# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2026 Schmid Software Solutions (https://schmid-software.de)
"""The "DCT" tab in the 3D View sidebar and the operators behind its buttons.

Panels, in the order every Creator Link plugin uses: Durty Cloth Tool (the logo, the connection status with the
details in a popover, and the Help menu with Help, Community, Copy Diagnostics and About), Get Connected (only while
setup is incomplete), Linked Cloth (the cloth's picture and details, and its maps to open), Live Preview (with the
Texture Checks while it runs), Model and Settings. Garment Fitting (:mod:`ui_garment`) sits between Model and
Settings. A switch under the status chooses what the tab works on: Clothing (Linked Cloth, Live Preview, Model and
Garment Fitting) or Custom Ped (:mod:`ui_ped`), so the two never show together. Every text comes from :mod:`strings` in Blender's interface
language; texts drawn here are translated already, so layouts get ``translate=False``.

Layout rules (the Creator Link spacing intent, in Blender's own means): one enlarged primary action per panel
(:data:`PRIMARY_SCALE`); groups are separated by space (:data:`GAP`), never by extra frames; prose wraps to the
measured width of the sidebar and never runs wider than about 70 characters; a sentence that explains an icon
row starts where that row's text starts; buttons that would be cut off side by side are stacked instead.
"""

from __future__ import annotations

from typing import Any, Callable, Iterable, List, Optional

import bpy
from bpy.props import BoolProperty, EnumProperty, PointerProperty, StringProperty
from bpy.types import Operator, Panel, PropertyGroup

from . import host, link, settings, state, strings
from .dct_link import auth, tokens
from .dct_link.session import SIGNING_IN, LinkError
from .strings import CONTEXT, EN, Msg, UserError, msg, t, tt, wrap_text

LEVEL_ICONS = {"INFO": "INFO", "WARNING": "ERROR", "ERROR": "CANCEL"}
CHIP_ICONS = {
    "connected": "CHECKMARK",
    "live": "RECORD_ON",
    "connecting": "SORTTIME",
    "action": "ERROR",
    "offline": "UNLINKED",
    "problem": "CANCEL",
}
SEVERITY_ICONS = {"error": "CANCEL", "warning": "ERROR", "info": "INFO"}
#: The help button after a label (passive notices use INFO).
HELP_ICON = "QUESTION"

#: The height of the one primary action of a panel.
PRIMARY_SCALE = 1.4
#: Space between two groups of a panel, and a smaller step inside a group (``layout.separator`` factors).
GAP = 1.0
GAP_SMALL = 0.5
#: Wrapped lines sit a little closer than control rows.
PROSE_LINE_SCALE = 0.85
#: Prose never runs wider than this many average characters, even in a wide sidebar or the preferences.
PROSE_MEASURE = 70
# Sizes in interface units (pixels at a scale of 1, measured in Blender 4.5 and 5.2): the panel content's left
# inset, its right inset including the sidebar's tab column, an icon with its gap, the room a label keeps free at
# its end, and a button's padding around its icon and text.
_LEFT = 16
_RIGHT = 36
_ICON = 26
_TEXT_END = 6
_BUTTON = 30

#: Failures an operator reports to the user instead of raising.
EXPECTED_FAILURES = (LinkError, auth.AuthError, tokens.SecretStoreError, ValueError, OSError)


# --------------------------------------------------------------------------------------------------
# Drawing helpers (shared with the preferences)
# --------------------------------------------------------------------------------------------------


def _scale(context: Any) -> float:
    system = getattr(getattr(context, "preferences", None), "system", None)
    return getattr(system, "ui_scale", 1.0) or 1.0  # includes the monitor's DPI scaling


def _measure(context: Any) -> Callable[[str], float]:
    """A text's drawn width in pixels, with the font size Blender uses for labels and buttons."""
    scale = _scale(context)
    try:
        import blf

        styles = context.preferences.ui_styles
        size = (styles[0].widget.points if len(styles) else 11) * scale
        blf.size(0, size)

        def width(text: str) -> float:
            return blf.dimensions(0, text)[0]

        width("x")
        return width
    except (ImportError, AttributeError, TypeError, ValueError):  # background mode without fonts, or an old API
        return lambda text: strings.character_width(text) * 6.5 * scale


def content_width(context: Any, width: Optional[float] = None) -> float:
    """The width, in pixels, a row of the current panel can use. ``width`` (interface units) is a popup's own."""
    scale = _scale(context)
    if width is not None:
        return width * scale
    region = getattr(context, "region", None)
    total = region.width if region is not None and region.width > 1 else 300 * scale
    return max(120 * scale, total - (_LEFT + _RIGHT) * scale)


def wrapped(layout: Any, context: Any, text: str, icon: str = "NONE", *, dim: bool = False, alert: bool = False,
            indent: bool = False, width: Optional[float] = None, reserve: float = 0) -> None:
    """A paragraph that wraps to the panel's measured width (Blender labels do not wrap by themselves). ``icon``
    leads the first line; ``indent`` starts the text where the text of an icon row above starts; ``reserve``
    (interface units) leaves room for a button drawn beside the paragraph."""
    measure = _measure(context)
    scale = _scale(context)
    leading = icon != "NONE" or indent
    limit = content_width(context, width) - ((_ICON if leading else 0) + _TEXT_END + reserve) * scale
    limit = min(limit, measure("n" * PROSE_MEASURE))
    lines = wrap_text(text, max(limit, 40 * scale), measure)
    column = layout.column(align=True)
    column.active = not dim
    column.alert = alert
    if len(lines) > 1:
        column.scale_y = PROSE_LINE_SCALE
    first = icon if icon != "NONE" else ("BLANK1" if indent else "NONE")
    for index, line in enumerate(lines):
        column.label(text=line, icon=first if index == 0 else ("BLANK1" if leading else "NONE"), translate=False)


def subtext(layout: Any, context: Any, key: str, *, indent: bool = False, **fields: Any) -> None:
    """A dimmed sentence under a control or title, for what a beginner needs to act."""
    wrapped(layout, context, t(key, **fields), dim=True, indent=indent)


def guide(layout: Any, context: Any, key: str, *, indent: bool = False, **fields: Any) -> None:
    """A sentence a beginner needs to act, at full contrast (dimmed text is too faint on light themes)."""
    wrapped(layout, context, t(key, **fields), indent=indent)


def reason_text(layout: Any, context: Any, reason: Optional[Msg]) -> None:
    """Why the button above is unavailable (the button's tooltip says the same)."""
    if reason is not None:
        wrapped(layout, context, strings.text(reason))


def number(layout: Any, context: Any, data: Any, name: str, key: str) -> None:
    """A number field whose label goes above it when label and value would not fit in one field."""
    text = t(key)
    if _measure(context)(text) + 70 * _scale(context) <= content_width(context):
        layout.prop(data, name, text=text, translate=False)
        return
    column = layout.column(align=True)
    wrapped(column, context, text)
    column.prop(data, name, text="")


def checkbox(layout: Any, context: Any, data: Any, name: str, key: str) -> None:
    """A checkbox whose label wraps instead of being cut off in a narrow sidebar."""
    text = t(key)
    scale = _scale(context)
    if _measure(context)(text) + (_ICON + _TEXT_END) * scale <= content_width(context):
        layout.prop(data, name, text=text, translate=False)
        return
    row = layout.row()
    row.prop(data, name, text="")
    wrapped(row.column(), context, text, reserve=_ICON)


def draw_notice(layout: Any, context: Any, notice: Optional[link.Notice]) -> None:
    if notice is not None:
        wrapped(layout, context, strings.text(notice.message), LEVEL_ICONS.get(notice.level, "INFO"),
                alert=notice.level == "ERROR")
        if notice.message.key == "error.discord_membership_required":
            operator(layout, "dct_link.join_discord", "op.join-discord", "COMMUNITY")


def info_button(layout: Any, topic: str) -> None:
    """The small help button after a label: its tooltip is the help text, a click shows it in a popup."""
    layout.operator("dct_link.info", text="", icon=HELP_ICON, emboss=False).topic = topic


def heading(layout: Any, context: Any, key: str, icon: str = "NONE", info: Optional[str] = None) -> None:
    """A title row (wrapping when it is long) with an optional help button at its right end."""
    row = layout.row()
    wrapped(row.column(), context, t(key), icon, reserve=24 if info else 0)
    if info:
        info_button(row, info)


def operator(layout: Any, idname: str, key: Optional[str], icon: str = "NONE", *, text: Optional[str] = None,
             **properties: Any) -> Any:
    """An operator button with the translated text of ``key`` (or ``text``, translated already)."""
    op = layout.operator(idname, text=text if text is not None else t(key), icon=icon, translate=False)
    for name, value in properties.items():
        setattr(op, name, value)
    return op


def primary(layout: Any, idname: str, key: str, icon: str = "NONE", **properties: Any) -> Any:
    """The panel's primary action: a full-width button at :data:`PRIMARY_SCALE`."""
    row = layout.row()
    row.scale_y = PRIMARY_SCALE
    return operator(row, idname, key, icon, **properties)


def fits_side_by_side(context: Any, labels: Iterable[str], width: Optional[float] = None) -> bool:
    """Whether buttons with these labels (and icons) fit next to each other without being cut off."""
    labels = list(labels)
    measure = _measure(context)
    each = content_width(context, width) / max(1, len(labels))
    return all(measure(label) + _BUTTON * _scale(context) <= each for label in labels)


def button_group(layout: Any, context: Any, keys: Iterable[str], width: Optional[float] = None) -> Any:
    """A row for buttons that fit side by side, otherwise a column that stacks them."""
    texts = [t(key) for key in keys]
    return layout.row(align=True) if fits_side_by_side(context, texts, width) else layout.column(align=True)


def _logo_icon() -> int:
    import importlib

    return importlib.import_module(__package__ + ".addon").logo_icon()


def _sign_in_code() -> Optional[tuple]:
    ctrl = state.get()
    active = ctrl.active_sign_in()
    if active is not None:
        return active
    prompt = ctrl.sign_in_prompt
    if prompt is not None:
        return settings.display_user_code(prompt.user_code), prompt.verification_uri_complete or prompt.verification_uri
    return None


# ---- the connection -----------------------------------------------------------------------------------


def draw_status(layout: Any, context: Any) -> None:
    """The status row: the one-word state as a button that opens the connection details, the detail below it,
    and what to do when the connection needs the user."""
    ctrl = state.get()
    chip = ctrl.chip()
    layout.popover(panel="DCTLINK_PT_details", text=t(f"chip.{chip}"), icon=CHIP_ICONS[chip], translate=False)
    # The detail line is left out where a message below (or the setup steps) says the same.
    explained = (ctrl.dct_signed_out or ctrl.dct_disconnected or ctrl.incompatible is not None
                 or (ctrl.setup_needed and not ctrl.ready))
    if not explained:
        wrapped(layout, context, strings.text(ctrl.status()), dim=True)
    messages = layout.column()
    if not host.online_access():
        messages.separator(factor=GAP_SMALL)
        wrapped(messages, context, t("online.off"), "ERROR", alert=True)
        messages.operator("screen.userpref_show", icon="PREFERENCES").section = "SYSTEM"
    if ctrl.incompatible is not None:
        messages.separator(factor=GAP_SMALL)
        code = ctrl.incompatible.get("code")
        wrapped(messages, context, strings.text(settings.describe_error(code)), "CANCEL", alert=True)
        if code == "dct-too-old":
            primary(messages, "dct_link.connect", "op.connect", "LINKED")  # Durty Cloth Tool updates itself
        else:
            primary(messages, "dct_link.open_update_page", "op.update-page", "URL")
    if ctrl.dct_signed_out:
        messages.separator(factor=GAP_SMALL)
        wrapped(messages, context, t("dct-signed-out"), "ERROR")
        primary(messages, "dct_link.connect", "op.connect", "LINKED")  # tries at once; on its own it waits longer
    if ctrl.dct_disconnected and not ctrl.connecting:
        messages.separator(factor=GAP_SMALL)
        wrapped(messages, context, t("dct-disconnected"), "UNLINKED")
        primary(messages, "dct_link.connect", "op.connect", "LINKED")
    said_by_setup = ctrl.setup_needed and ctrl.notice is not None and ctrl.notice.message.key == "notice.signed-out"
    if ctrl.notice is not None and not said_by_setup:  # the Sign In step says "You signed out" itself
        messages.separator(factor=GAP_SMALL)
        draw_notice(messages, context, ctrl.notice)


def draw_details(layout: Any, context: Any) -> None:
    ctrl = state.get()
    column = layout.column(align=True)
    column.label(text=t("details.status", state=strings.text(ctrl.status())), icon=CHIP_ICONS[ctrl.chip()],
                 translate=False)
    if ctrl.user_name and not ctrl.signed_out:
        column.label(text=t("details.account", name=ctrl.user_name), icon="USER", translate=False)
    else:
        column.label(text=t("details.not-signed-in"), icon="USER", translate=False)
    if ctrl.project:
        column.label(text=t("details.project", name=ctrl.project.get("name") or ""), icon="FILE_FOLDER",
                     translate=False)
    column.label(text=t("details.addon", version=settings.VERSION, channel=t(f"channel.{settings.CHANNEL}")),
                 icon="BLENDER", translate=False)
    layout.separator(factor=GAP_SMALL)
    if ctrl.connecting:
        operator(layout, "dct_link.disconnect", "op.disconnect", "UNLINKED")
    else:
        operator(layout, "dct_link.connect", "op.connect", "LINKED")


# ---- setup --------------------------------------------------------------------------------------------


def _step_row(layout: Any, context: Any, number: int, done: bool, current: bool, title: str, done_title: str,
              info: str) -> None:
    row = layout.row()
    icon = "CHECKMARK" if done else "RADIOBUT_ON" if current else "RADIOBUT_OFF"
    wrapped(row.column(), context, f"{number}. {t(done_title if done else title)}", icon, reserve=24)
    info_button(row, info)


def draw_setup(layout: Any, context: Any) -> None:
    """The two setup steps; only the current one shows its controls, done steps show their title."""
    ctrl = state.get()
    found, signed_in = ctrl.setup_steps()
    current = 1 if not found else 2 if not signed_in else 0

    _step_row(layout, context, 1, found, current == 1, "setup.find.title", "setup.find.done", "find")
    if current == 1:
        guide(layout, context, "setup.find.subtext", indent=True)
        layout.separator(factor=GAP_SMALL)
        if ctrl.connecting:
            key = "setup.find.waiting" if ctrl.search_failed else "setup.find.searching"  # steady while retrying
            wrapped(layout, context, t(key), "SORTTIME")
        else:
            primary(layout, "dct_link.connect", "op.connect", "LINKED")
        layout.separator(factor=GAP)

    _step_row(layout, context, 2, signed_in, current == 2, "setup.sign-in.title", "setup.sign-in.done", "sign-in")
    if current == 2:
        draw_sign_in_step(layout.column(), context)


def draw_code(layout: Any, code: str) -> None:
    """The sign-in code, as large as Blender allows (an add-on cannot change the font size): its two groups of
    letters, spaced for reading aloud."""
    box = layout.box()
    row = box.row()
    row.alignment = "CENTER"
    row.scale_y = 1.6
    groups = code.split("-")
    row.label(text="     ".join(" ".join(group) for group in groups), translate=False)


def _draw_browser_sign_in(layout: Any, context: Any, code: tuple, lead: bool) -> None:
    """The browser path: the code to compare, Open Sign-in Page (the primary action when ``lead``) and Copy Code."""
    guide(layout, context, "setup.sign-in.browser-subtext")
    draw_code(layout, code[0])
    if lead:
        primary(layout, "dct_link.open_sign_in_page", "op.open-sign-in", "URL")
        operator(layout, "dct_link.copy_code", "op.copy-code", "COPYDOWN")
    else:
        row = button_group(layout, context, ("op.open-sign-in", "op.copy-code"))
        operator(row, "dct_link.open_sign_in_page", "op.open-sign-in", "URL")
        operator(row, "dct_link.copy_code", "op.copy-code", "COPYDOWN")


def draw_sign_in_step(layout: Any, context: Any) -> None:
    ctrl = state.get()
    code = _sign_in_code()
    if code is not None or ctrl.state == SIGNING_IN:
        status = ctrl.sign_in_status
        if status is not None:
            draw_notice(layout, context, status)
        else:
            wrapped(layout, context, t("setup.sign-in.waiting"), "SORTTIME")
        if code is not None:
            layout.separator(factor=GAP_SMALL)
            in_dct = status is not None and status.message.key in ("setup.sign-in.asked", "setup.sign-in.approved")
            if in_dct:
                # Durty Cloth Tool is handling it: the browser is the fallback, one click away.
                header, body = layout.panel("dct_link_sign_in_browser", default_closed=True)
                header.label(text=t("op.sign-in-browser"), icon="URL", translate=False)
                if body is not None:
                    _draw_browser_sign_in(body, context, code, lead=False)
            else:
                _draw_browser_sign_in(layout, context, code, lead=True)
        layout.separator(factor=GAP_SMALL)
        operator(layout, "dct_link.cancel_sign_in", "op.cancel-sign-in", "X")
        return
    if ctrl.starting_sign_in or ctrl.finding_for_sign_in:
        key = "setup.sign-in.finding" if ctrl.finding_for_sign_in else "setup.sign-in.starting"
        wrapped(layout, context, t(key), "SORTTIME")
        operator(layout, "dct_link.cancel_sign_in", "op.cancel-sign-in", "X")
        return
    if ctrl.signed_out:
        wrapped(layout, context, t("setup.sign-in.signed-out"), "USER")
    else:
        guide(layout, context, "setup.sign-in.subtext", indent=True)
    layout.separator(factor=GAP_SMALL)
    draw_sign_in_buttons(layout, context)


def draw_sign_in_buttons(layout: Any, context: Any) -> None:
    """Sign In (Durty Cloth Tool approves it; the browser code follows when it is not running) and the browser as
    the second choice."""
    primary(layout, "dct_link.sign_in", "op.sign-in", "USER")
    subtext(layout, context, "setup.sign-in.how")
    layout.separator(factor=GAP_SMALL)
    operator(layout, "dct_link.sign_in_browser", "op.sign-in-browser", "URL")


# ---- linked cloth -------------------------------------------------------------------------------------


def map_label(target: str) -> str:
    """A map's short name for a row of three buttons ("Diffuse", "Normal", "Specular")."""
    return t(f"map.{target}-short") if f"map.{target}-short" in EN else t(f"map.{target}")


def draw_map_row(layout: Any, context: Any, props: Any, stream: link.TextureStream) -> None:
    """Which map the chosen image replaces: the one a linked image belongs to, the running preview's, or a choice
    (a labelled list, so it does not look like the Linked Cloth panel's buttons that open a map)."""
    ctrl = state.get()
    binding = host.stored_binding(props.image)
    linked_map = host.stored_map(props.image) if binding else None
    if linked_map is not None:
        name = ctrl.cloth_label(binding)
        map_name = t(f"map.{linked_map}")
        text = t("live.linked", name=name, map=map_name) if name else t("live.map", map=map_name)
        wrapped(layout, context, text, "LINKED")
        return
    if stream.active:
        wrapped(layout, context, t("live.map", map=t(f"map.{stream.target}")), "TEXTURE", dim=True)
        return
    row = layout.row(align=True)
    split = row.split(factor=MAP_LABEL_FACTOR, align=True)
    split.label(text=t("linked.map"), translate=False)
    split.prop(props, "target", text="")
    info_button(row, "map")
    info = ctrl.focus_info()
    if info is not None and info.targets and props.target not in info.targets:
        wrapped(layout, context, t(f"linked.map-missing.{props.target}"), "ERROR")


#: The share of a row the label takes in the Live Preview panel's Image and Map rows.
MAP_LABEL_FACTOR = 0.3


def cloth_details(info: link.FocusInfo) -> str:
    """The cloth's facts in one line, as Durty Cloth Tool names them: "jbib · Female · mp_f_freemode_01 · #3". The
    game's tokens and the collection are shown as they are, never translated."""
    parts = []
    if info.drawable_type:
        parts.append(str(info.drawable_type))
    if info.gender in ("male", "female"):
        parts.append(t(f"gender.{info.gender}"))
    if info.collection:
        parts.append(str(info.collection))
    if info.number is not None:
        parts.append(t("linked.number", number=info.number))
    return " · ".join(parts)


#: The size of the cloth's picture in the Linked Cloth panel (``template_icon`` scale; one unit is 20 pixels).
THUMBNAIL_SCALE = 4.0


def _thumbnail_icon() -> int:
    import importlib

    return importlib.import_module(__package__ + ".addon").thumbnail_icon()


def draw_card(layout: Any, context: Any, info: link.FocusInfo) -> None:
    """The cloth: its picture beside its name, variation and facts."""
    icon = _thumbnail_icon()
    row = layout.row()
    if icon:
        picture = row.column()
        picture.template_icon(icon_value=icon, scale=THUMBNAIL_SCALE)
    text = row.column(align=True)
    reserve = THUMBNAIL_SCALE * 20 + 8 if icon else 0
    lead = "NONE" if icon else "MOD_CLOTH"
    if info.name:
        wrapped(text, context, info.name, lead, reserve=reserve)
        if info.letter:
            wrapped(text, context, t("linked.variation", letter=info.letter), indent=not icon, reserve=reserve)
    else:
        wrapped(text, context, t("linked.unknown"), lead, reserve=reserve)
        wrapped(text, context, t("linked.unknown-subtext"), dim=True, indent=not icon, reserve=reserve)
    details = cloth_details(info)
    if details:
        wrapped(text, context, details, dim=True, indent=not icon, reserve=reserve)


def draw_linked(layout: Any, context: Any) -> None:
    ctrl = state.get()
    project = ctrl.project
    if not project:
        wrapped(layout, context, t("linked.no-project"), "INFO")
        return
    wrapped(layout, context, t("linked.project", name=project.get("name") or ""), "FILE_FOLDER")
    info = ctrl.card_info()
    if info is None:
        wrapped(layout, context, t("linked.no-cloth"), "INFO")
        draw_notice(layout, context, ctrl.open_notice)
        return
    layout.separator(factor=GAP_SMALL)
    draw_card(layout, context, info)
    layout.separator(factor=GAP_SMALL)
    row = layout.row()
    if info.linked:
        # The image chosen below belongs to this cloth: Unlink lets it follow the selection again.
        wrapped(row.column(), context, t("linked.image"), "LINKED", reserve=2 * 24)
        row.operator("dct_link.unlink_image", text="", icon="UNLINKED")
    else:
        wrapped(row.column(), context, t("linked.follows"), "LINKED", dim=True, reserve=24)
    info_button(row, "linked")

    layout.separator(factor=GAP)
    heading(layout, context, "linked.open-map", info="open-map")
    labels = [map_label(target) for target, _, _ in settings.TARGETS]
    group = layout.row(align=True) if fits_side_by_side(context, labels) else layout.column(align=True)
    for target, _, _ in settings.TARGETS:
        cell = group.row(align=True)
        cell.enabled = ctrl.open_map_problem(target) is None  # the tooltip says why
        operator(cell, "dct_link.open_map", None, "IMAGE_DATA", text=map_label(target), target=target)
    general = ctrl.open_map_problem("diffuse" if not info.targets or "diffuse" in info.targets else info.targets[0])
    if ctrl.opening_map is not None:
        wrapped(layout, context, t("open.reading"), "SORTTIME")
    elif general is not None:
        reason_text(layout, context, general)
    draw_notice(layout, context, ctrl.open_notice)


# ---- live preview -------------------------------------------------------------------------------------


def live_state(stream: link.TextureStream) -> tuple:
    """The live preview's state line: (text key, icon)."""
    if not stream.active:
        return "live.off", "RECORD_OFF"
    if stream.saving:
        return "live.saving", "SORTTIME"
    if stream.reading:
        return "live.reading", "SORTTIME"
    if not stream.is_open:
        return "live.starting", "SORTTIME"
    if stream.paused:
        return "live.paused", "PAUSE"
    if stream.live_state == "attached":
        return "live.on", "RECORD_ON"
    if stream.live_state == "notWorn":
        return "live.not-worn", "INFO"
    if stream.live_state == "paused":
        return "live.paused-dct", "PAUSE"
    return "live.sending", "SORTTIME"


def draw_live(layout: Any, context: Any) -> None:
    ctrl = state.get()
    stream = ctrl.stream
    props = context.scene.dct_link
    problem = ctrl.feature_problem(settings.FEATURE_LIVE_TEXTURE) if ctrl.ready else None
    if problem:
        wrapped(layout, context, t("live.upsell") if problem.key == "feature.needsUltimate" else strings.text(problem),
                "INFO")
        layout.separator(factor=GAP_SMALL)
    row = layout.row(align=True)
    split = row.split(factor=MAP_LABEL_FACTOR, align=True)
    split.label(text=t("prop.image"), translate=False)
    image = split.row(align=True)
    image.enabled = not stream.active
    image.prop(props, "image", text="")
    image.operator("dct_link.use_paint_image", text="", icon="EYEDROPPER")
    info_button(row, "live")

    draw_map_row(layout, context, props, stream)
    layout.separator(factor=GAP_SMALL)

    key, icon = live_state(stream)
    wrapped(layout, context, t(key), icon)
    progress = stream.progress
    if progress is not None and hasattr(layout, "progress"):
        layout.progress(factor=progress, type="BAR", text=f"{int(progress * 100)} %", translate=False)
    if stream.warning is not None:
        wrapped(layout, context, strings.text(stream.warning), "ERROR")

    layout.separator(factor=GAP_SMALL)
    if not stream.active:
        primary(layout, "dct_link.live_start", "op.live-start", "PLAY")
        reason_text(layout, context, _live_start_reason(context))
        if stream.status is not None:
            layout.separator(factor=GAP_SMALL)
            draw_notice(layout, context, stream.status)
        return

    # Running: Stop takes Start's place, the controls for the stream follow, then saving (the primary action).
    operator(layout, "dct_link.live_stop", "op.live-stop", "X")
    row = button_group(layout, context, ("op.live-resume", "op.live-send"))
    operator(row, "dct_link.live_pause", "op.live-resume" if stream.paused else "op.live-pause",
             "PLAY" if stream.paused else "PAUSE")
    operator(row, "dct_link.live_send_now", "op.live-send", "FILE_REFRESH")

    # The checks come before saving, so an error is read before the map goes into the project.
    layout.separator(factor=GAP)
    header, body = layout.panel("dct_link_checks", default_closed=False)
    header.label(text=t("panel.checks"), translate=False)
    if body is None:
        draw_checks_summary(header, stream)  # closed: the counts stand in for the list
    else:
        draw_checks(body, context)

    layout.separator(factor=GAP)
    if stream.unsaved:
        wrapped(layout, context, t("live.unsaved"), "DOT")
    primary(layout, "dct_link.live_save", "op.live-save", "CHECKMARK")
    operator(layout, "dct_link.live_save_variation", "op.live-save-variation", "ADD")
    operator(layout, "dct_link.live_discard", "op.live-discard", "TRASH")
    guide(layout, context, "live.save-subtext")
    if stream.status is not None:
        layout.separator(factor=GAP_SMALL)
        draw_notice(layout, context, stream.status)


# ---- texture checks -----------------------------------------------------------------------------------


def checks_counts(findings: Optional[list]) -> List[tuple]:
    """``(severity, count)`` for each severity present, errors first."""
    counts = []
    for severity in ("error", "warning", "info"):
        count = sum(1 for f in findings or () if f.get("severity") == severity)
        if count:
            counts.append((severity, count))
    return counts


def draw_checks_summary(layout: Any, stream: link.TextureStream) -> None:
    """The counts in the Texture Checks header: an icon and a number per severity (short in every language)."""
    row = layout.row(align=True)
    row.alignment = "RIGHT"
    if stream.checking:
        row.label(text="", icon="SORTTIME")
        return
    counts = checks_counts(stream.findings)
    for severity, count in counts:
        row.label(text=str(count), icon=SEVERITY_ICONS[severity], translate=False)
    if stream.findings == []:
        row.label(text="", icon="CHECKMARK")


def draw_checks(layout: Any, context: Any) -> None:
    stream = state.get().stream
    if stream.checking:
        wrapped(layout, context, t("checks.checking"), "SORTTIME")
    elif stream.checks_problem is not None:
        wrapped(layout, context, strings.text(stream.checks_problem), "INFO")
    elif stream.findings is None:
        subtext(layout, context, "checks.not-checked")
    elif not stream.findings:
        wrapped(layout, context, t("checks.clean"), "CHECKMARK")
    for finding in stream.findings or ():
        code = str(finding.get("code") or "")
        severity = finding.get("severity") if finding.get("severity") in SEVERITY_ICONS else "info"
        key = f"finding.{code}"
        sentence = t(key) if key in EN else t("finding.unknown", code=code)
        row = layout.row()
        row.label(text=t(f"severity.{severity}"), icon=SEVERITY_ICONS[severity], translate=False)
        if f"finding-fix.{code}" in EN:
            info_button(row, f"finding-fix.{code}")
        wrapped(layout, context, sentence, indent=True)
    layout.separator(factor=GAP_SMALL)
    row = layout.row(align=True)
    if stream.is_open:
        operator(row, "dct_link.check_again", "op.check-again", "FILE_REFRESH")
    info_button(row, "checks")


# ---- model --------------------------------------------------------------------------------------------


def draw_model(layout: Any, context: Any) -> None:
    ctrl = state.get()
    model = ctrl.model
    available, status = host.sollumz_status()
    if not available:
        # One calm line: models need Sollumz; everything else in the tab works without it.
        row = layout.row()
        wrapped(row.column(), context, strings.text(status), "ERROR", reserve=24)
        info_button(row, "model")
        if model.open_notice is not None:
            layout.separator(factor=GAP_SMALL)
            draw_notice(layout, context, model.open_notice)
        return
    row = layout.row()
    wrapped(row.column(), context, strings.text(status), "CHECKMARK", reserve=24)
    info_button(row, "model")
    subtext(layout, context, "sollumz.tested", indent=True, version=settings.SOLLUMZ_TESTED)
    problem = ctrl.feature_problem(settings.FEATURE_MODEL) if ctrl.ready else None
    if problem:
        wrapped(layout, context, strings.text(problem), "INFO")
    if model.open_notice is not None:
        layout.separator(factor=GAP_SMALL)
        draw_notice(layout, context, model.open_notice)
    draw_model_link(layout, context)

    layout.separator(factor=GAP)
    if model.lease is not None:
        if model.root_name:
            wrapped(layout, context, t("model.name", name=model.root_name), "OUTLINER_OB_EMPTY")
        draw_notice(layout, context, model.status)
        if model.findings:
            wrapped(layout, context, t("model.findings", count=len(model.findings)), "INFO")
        layout.separator(factor=GAP_SMALL)
        primary(layout, "dct_link.model_save", "op.model-save", "CHECKMARK")
        operator(layout, "dct_link.model_discard", "op.model-discard", "TRASH")
        layout.separator(factor=GAP_SMALL)
        operator(layout, "dct_link.model_push", "op.model-push", "EXPORT")
    else:
        primary(layout, "dct_link.model_push", "op.model-push", "EXPORT")
        reason_text(layout, context, _push_reason())
        draw_notice(layout, context, model.status)

    layout.separator(factor=GAP)
    props = context.scene.dct_link
    checkbox(layout, context, props, "auto_push", "prop.auto-push")
    subtext(layout, context, "model.subtext")
    if model.waiting is not None and model.due_at is not None:
        wrapped(layout, context, strings.text(model.waiting), "TIME")
    draw_notice(layout, context, model.note)


def model_root(context: Any) -> Optional[Any]:
    """The Drawable Dictionary the Model panel talks about: the selected one, else the one pushed last."""
    root = host.selected_dictionary(context)
    return root if root is not None else state.watcher.root()


def draw_model_link(layout: Any, context: Any) -> None:
    """The cloth the Drawable Dictionary is linked to (a model opened from Durty Cloth Tool) with Unlink, and a
    warning when a copy carries the same link."""
    root = model_root(context)
    binding = host.stored_binding(root)
    if binding is None:
        return
    layout.separator(factor=GAP_SMALL)
    name = state.get().cloth_label(binding) or t("linked.unknown")
    row = layout.row()
    wrapped(row.column(), context, t("model.linked", name=name), "LINKED", reserve=2 * 24)
    row.operator("dct_link.unlink_model", text="", icon="UNLINKED")
    info_button(row, "model-linked")
    others = host.others_linked_alike(root)
    if others:
        wrapped(layout, context, t("model.linked-twice", name=others[0].name), "ERROR", alert=True)


# ---- settings -----------------------------------------------------------------------------------------


def _group(layout: Any, context: Any, idname: str, key: str, icon: str, info: Optional[str] = None,
           closed: bool = False) -> Any:
    """A settings group as a native collapsible section (``closed``: closed until the user opens it); returns its
    body, or ``None`` while it is closed."""
    header, body = layout.panel(f"dct_link_settings_{idname}", default_closed=closed)
    header.label(text=t(key), icon=icon, translate=False)
    if info:
        info_button(header, info)
    return body


def draw_settings(layout: Any, context: Any, prefs: Any) -> None:
    """The settings groups: Connection, Account, Models, Updates and Privacy (the add-on preferences
    show the same)."""
    ctrl = state.get()

    body = _group(layout, context, "connection", "settings.connection", "LINKED")
    if body is not None:
        if prefs is not None:
            checkbox(body, context, prefs, "auto_connect", "prop.auto-connect")
        subtext(body, context, "settings.connect-subtext")
        if ctrl.connecting:
            operator(body, "dct_link.disconnect", "op.disconnect", "UNLINKED")
        else:
            operator(body, "dct_link.connect", "op.connect", "LINKED")

    body = _group(layout, context, "account", "settings.account", "USER", info="sign-in")
    if body is not None:
        if ctrl.user_name and not ctrl.signed_out:
            wrapped(body, context, t("settings.signed-in-as", name=ctrl.user_name))
            operator(body, "dct_link.sign_out", "op.sign-out", "X")
            subtext(body, context, "settings.sign-out-subtext")
        else:
            # Signing in is a setup step: Get Connected shows its buttons, so they are not repeated here.
            wrapped(body, context, t("settings.signed-out" if ctrl.signed_out else "settings.not-signed-in"), "USER")

    if prefs is not None:
        body = _group(layout, context, "models", "settings.models", "EXPORT", closed=True)
        if body is not None:
            number(body, context, prefs, "auto_push_delay", "prop.delay")

    updating = host.installed_from_dct_repository(state.PACKAGE)
    # Open while Blender cannot update this copy, so that the way to get updates is seen.
    body = _group(layout, context, "updates", "settings.updates", "FILE_REFRESH", info="channel", closed=updating)
    if body is not None:
        wrapped(body, context, t("settings.this-version", version=settings.VERSION,
                                 channel=t(f"channel.{settings.CHANNEL}")))
        if updating:
            subtext(body, context, "settings.updates-on")
        else:
            wrapped(body, context, t("settings.disk-install"), "ERROR")
            operator(body, "dct_link.open_plugins_page", "op.plugins-page", "URL")

    body = _group(layout, context, "privacy", "settings.privacy", "HIDE_ON", info="privacy", closed=True)
    if body is not None:
        if prefs is not None:
            checkbox(body, context, prefs, "share_device_name", "prop.device-name")
        subtext(body, context, "settings.device-name-subtext")
        if prefs is not None:
            checkbox(body, context, prefs, "fit_upload_consent", "prop.fit-consent")
        subtext(body, context, "settings.fit-consent-subtext")


def draw_help_menu(layout: Any) -> None:
    """Help, the community, support details and About, in the one place they live: the menu in the header."""
    operator(layout, "dct_link.open_help", "op.help", "HELP")
    operator(layout, "dct_link.open_community", "op.community", "COMMUNITY")
    layout.separator()
    operator(layout, "dct_link.diagnostics", "op.diagnostics", "COPYDOWN")
    layout.separator()
    operator(layout, "dct_link.about", "op.about", "INFO")


# --------------------------------------------------------------------------------------------------
# Scene settings
# --------------------------------------------------------------------------------------------------


def _auto_push_changed(self: Any, context: Any) -> None:
    if state.controller is not None and not self.auto_push:
        state.controller.model.due_at = None


class DCTLINK_PG_scene(PropertyGroup):
    image: PointerProperty(
        name=EN["prop.image"],
        type=bpy.types.Image,
        description=EN["prop.image.desc"],
        translation_context=CONTEXT,
    )
    target: EnumProperty(
        name=EN["prop.map"],
        items=settings.TARGETS,
        default="diffuse",
        description=EN["prop.map.desc"],
        translation_context=CONTEXT,
    )
    auto_push: BoolProperty(
        name=EN["prop.auto-push"],
        default=False,
        update=_auto_push_changed,
        description=EN["prop.auto-push.desc"],
        translation_context=CONTEXT,
    )
    workspace: EnumProperty(
        name=EN["workspace.prop"],
        items=(("CLOTHING", EN["workspace.clothing"], EN["workspace.clothing.desc"], "MOD_CLOTH", 0),
               ("PED", EN["workspace.ped"], EN["workspace.ped.desc"], "OUTLINER_OB_ARMATURE", 1)),
        default="CLOTHING",
        description=EN["workspace.prop.desc"],
        translation_context=CONTEXT,
    )


def workspace(context: Any) -> str:
    """What the DCT tab works on: ``CLOTHING`` or ``PED``."""
    settings_ = getattr(getattr(context, "scene", None), "dct_link", None)
    return getattr(settings_, "workspace", "CLOTHING") if settings_ is not None else "CLOTHING"


# --------------------------------------------------------------------------------------------------
# Operators
# --------------------------------------------------------------------------------------------------


def _report_text(exc: BaseException) -> str:
    if isinstance(exc, UserError):
        return strings.text(exc.message)
    if isinstance(exc, (LinkError, auth.AuthError)):
        return strings.text(settings.describe_error(exc.code))
    if isinstance(exc, tokens.SecretStoreError):
        return t("notice.secret-store")
    if isinstance(exc, OSError):
        return t("notice.file-error", detail=str(exc.strerror or exc))
    return str(exc)


def _run(op: Operator, action: Callable[[], Any]) -> set:
    """Runs an operator's work and reports the failures a user can act on instead of raising them."""
    try:
        action()
    except EXPECTED_FAILURES as exc:
        op.report({"ERROR"}, _report_text(exc))
        return {"CANCELLED"}
    return {"FINISHED"}


def _refuse(cls: Any, reason: Optional[Msg]) -> bool:
    """For ``poll``: ``True`` without a reason; otherwise Blender's tooltip says why and ``False`` is returned."""
    if reason is None:
        return True
    cls.poll_message_set(strings.tip(reason))
    return False


def _controller_reason() -> Optional[Msg]:
    return None if state.controller is not None else msg("notice.not-ready")


def _ready_reason() -> Optional[Msg]:
    reason = _controller_reason()
    if reason is None and not state.get().ready:
        reason = msg("notice.connect-first")
    return reason


def _online_reason() -> Optional[Msg]:
    return None if host.online_access() else msg("notice.online-off")


class _Op(Operator):
    bl_translation_context = CONTEXT


class DCTLINK_OT_connect(_Op):
    bl_idname = "dct_link.connect"
    bl_label = EN["op.connect"]
    bl_description = EN["op.connect.desc"]

    @classmethod
    def poll(cls, context):
        return _refuse(cls, _controller_reason() or _online_reason())

    def execute(self, context):
        return _run(self, lambda: state.get().connect())


class DCTLINK_OT_disconnect(_Op):
    bl_idname = "dct_link.disconnect"
    bl_label = EN["op.disconnect"]
    bl_description = EN["op.disconnect.desc"]

    @classmethod
    def poll(cls, context):
        return _refuse(cls, _controller_reason())

    def execute(self, context):
        return _run(self, lambda: state.get().disconnect())


class DCTLINK_OT_sign_in(_Op):
    """Sign In: Durty Cloth Tool's approval window asks; without Durty Cloth Tool the browser code follows."""

    bl_idname = "dct_link.sign_in"
    bl_label = EN["op.sign-in"]
    bl_description = EN["op.sign-in.desc"]

    @classmethod
    def poll(cls, context):
        return _refuse(cls, _controller_reason() or _online_reason())

    def execute(self, context):
        return _run(self, lambda: state.get().sign_in())


class DCTLINK_OT_sign_in_browser(_Op):
    bl_idname = "dct_link.sign_in_browser"
    bl_label = EN["op.sign-in-browser"]
    bl_description = EN["op.sign-in-browser.desc"]

    @classmethod
    def poll(cls, context):
        return _refuse(cls, _controller_reason() or _online_reason())

    def execute(self, context):
        result = _run(self, lambda: state.get().start_sign_in())
        if "FINISHED" in result:
            self.report({"INFO"}, t("notice.browser-opens"))
        return result


def _code_reason() -> Optional[Msg]:
    reason = _controller_reason()
    if reason is None and _sign_in_code() is None:
        reason = msg("notice.no-sign-in")
    return reason


class DCTLINK_OT_open_sign_in_page(_Op):
    bl_idname = "dct_link.open_sign_in_page"
    bl_label = EN["op.open-sign-in"]
    bl_description = EN["op.open-sign-in.desc"]

    @classmethod
    def poll(cls, context):
        return _refuse(cls, _code_reason())

    def execute(self, context):
        code = _sign_in_code()
        if code is None:
            self.report({"WARNING"}, t("notice.no-sign-in"))
            return {"CANCELLED"}
        if not settings.is_gta_clothing_url(code[1]):
            self.report({"ERROR"}, t("notice.not-gta-clothing"))
            return {"CANCELLED"}
        bpy.ops.wm.url_open(url=code[1])
        return {"FINISHED"}


class DCTLINK_OT_copy_code(_Op):
    bl_idname = "dct_link.copy_code"
    bl_label = EN["op.copy-code"]
    bl_description = EN["op.copy-code.desc"]

    @classmethod
    def poll(cls, context):
        return _refuse(cls, _code_reason())

    def execute(self, context):
        code = _sign_in_code()
        if code is None:
            return {"CANCELLED"}
        context.window_manager.clipboard = code[0]
        self.report({"INFO"}, t("settings.code-copied"))
        return {"FINISHED"}


class DCTLINK_OT_cancel_sign_in(_Op):
    bl_idname = "dct_link.cancel_sign_in"
    bl_label = EN["op.cancel-sign-in"]
    bl_description = EN["op.cancel-sign-in.desc"]

    @classmethod
    def poll(cls, context):
        return _refuse(cls, _controller_reason())

    def execute(self, context):
        def cancel() -> None:
            ctrl = state.get()
            ctrl.cancel_sign_in()
            if ctrl.state == SIGNING_IN:
                ctrl.disconnect()  # the session itself waits for the sign-in; stop it

        return _run(self, cancel)


class DCTLINK_OT_sign_out(_Op):
    bl_idname = "dct_link.sign_out"
    bl_label = EN["op.sign-out"]
    bl_description = EN["op.sign-out.desc"]

    @classmethod
    def poll(cls, context):
        reason = _controller_reason()
        if reason is None and not state.get().user_name:
            reason = msg("settings.not-signed-in")
        return _refuse(cls, reason)

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        return _run(self, lambda: state.get().sign_out())


class DCTLINK_OT_open_update_page(_Op):
    bl_idname = "dct_link.open_update_page"
    bl_label = EN["op.update-page"]
    bl_description = EN["op.update-page.desc"]

    def execute(self, context):
        incompatible = (state.controller.incompatible if state.controller is not None else None) or {}
        url = incompatible.get("updateUrl")
        bpy.ops.wm.url_open(url=url if settings.is_gta_clothing_url(url) else settings.PLUGINS_PAGE_URL)
        return {"FINISHED"}


class DCTLINK_OT_open_plugins_page(_Op):
    bl_idname = "dct_link.open_plugins_page"
    bl_label = EN["op.plugins-page"]
    bl_description = EN["op.plugins-page.desc"]

    def execute(self, context):
        bpy.ops.wm.url_open(url=settings.PLUGINS_PAGE_URL)
        return {"FINISHED"}


class DCTLINK_OT_open_help(_Op):
    bl_idname = "dct_link.open_help"
    bl_label = EN["op.help"]
    bl_description = EN["op.help.desc"]

    def execute(self, context):
        bpy.ops.wm.url_open(url=settings.HELP_URL)
        return {"FINISHED"}


class DCTLINK_OT_open_community(_Op):
    bl_idname = "dct_link.open_community"
    bl_label = EN["op.community"]
    bl_description = EN["op.community.desc"]

    def execute(self, context):
        bpy.ops.wm.url_open(url=settings.COMMUNITY_URL)
        return {"FINISHED"}


class DCTLINK_OT_join_discord(_Op):
    bl_idname = "dct_link.join_discord"
    bl_label = EN["op.join-discord"]
    bl_description = EN["op.join-discord.desc"]

    def execute(self, context):
        bpy.ops.wm.url_open(url=settings.DISCORD_INVITE_URL)
        return {"FINISHED"}


class DCTLINK_OT_diagnostics(_Op):
    bl_idname = "dct_link.diagnostics"
    bl_label = EN["op.diagnostics"]
    bl_description = EN["op.diagnostics.desc"]

    @classmethod
    def poll(cls, context):
        return _refuse(cls, _controller_reason())

    def execute(self, context):
        context.window_manager.clipboard = diagnostics(context)
        self.report({"INFO"}, t("settings.diagnostics-copied"))
        return {"FINISHED"}


def diagnostics(context: Any) -> str:
    view = context.preferences.view
    extra = {
        "sollumz": host.sollumz_version() or ("enabled" if host.sollumz_operator_properties() else "none"),
        "language": f"{view.language}; interface translated: {getattr(view, 'use_translate_interface', None)}",
        "installed from repository": str(host.installed_from_dct_repository(state.PACKAGE)),
        "stroke detection": str(host.modal_operators_known()),
    }
    return state.get().diagnostics(extra)


def info_key(topic: str) -> str:
    """The text key behind an info button: ``map`` means ``info.map``; a full key such as ``finding-fix.too-large``
    is used as it is."""
    if topic in EN:
        return topic
    key = f"info.{topic}"
    return key if key in EN else "info.find"


class DCTLINK_OT_info(_Op):
    bl_idname = "dct_link.info"
    bl_label = EN["op.info"]
    bl_options = {"INTERNAL"}

    topic: StringProperty(options={"HIDDEN", "SKIP_SAVE"})

    @classmethod
    def description(cls, context, properties):
        return tt(info_key(properties.topic))

    def invoke(self, context, event):
        return context.window_manager.invoke_popup(self, width=360)

    def draw(self, context):
        wrapped(self.layout, context, t(info_key(self.topic)), "INFO", width=340)

    def execute(self, context):
        return {"FINISHED"}


class DCTLINK_OT_about(_Op):
    bl_idname = "dct_link.about"
    bl_label = EN["op.about"]
    bl_description = EN["op.about.desc"]

    def invoke(self, context, event):
        return context.window_manager.invoke_popup(self, width=380)

    def draw(self, context):
        layout = self.layout
        icon = _logo_icon()
        title = t("about.title", version=settings.VERSION, channel=t(f"channel.{settings.CHANNEL}"))
        if icon:
            layout.label(text=title, icon_value=icon, translate=False)
        else:
            layout.label(text=title, icon="INFO", translate=False)
        wrapped(layout, context, t("settings.licence"), dim=True, width=360)
        layout.separator(factor=GAP_SMALL)
        wrapped(layout, context, t("info.privacy"), width=360)

    def execute(self, context):
        return {"FINISHED"}


class DCTLINK_MT_help(bpy.types.Menu):
    bl_idname = "DCTLINK_MT_help"
    bl_label = EN["op.help"]
    bl_translation_context = CONTEXT

    def draw(self, context):
        draw_help_menu(self.layout)


def _open_map_reason(target: str) -> Optional[Msg]:
    reason = _controller_reason()
    if reason is None:
        reason = state.get().open_map_problem(target)
    return reason


class DCTLINK_OT_open_map(_Op):
    bl_idname = "dct_link.open_map"
    bl_label = EN["op.open-map"]
    bl_description = EN["op.open-map.desc"]

    target: EnumProperty(items=settings.TARGETS, options={"HIDDEN", "SKIP_SAVE"}, translation_context=CONTEXT)

    @classmethod
    def poll(cls, context):
        return state.controller is not None and state.controller.ready

    @classmethod
    def description(cls, context, properties):
        reason = _open_map_reason(properties.target)
        text = tt("op.open-map.desc")
        return f"{text}.\n{strings.tip(reason)}" if reason is not None else text

    def execute(self, context):
        reason = _open_map_reason(self.target)
        if reason is not None:
            self.report({"WARNING"}, strings.text(reason))
            return {"CANCELLED"}
        return _run(self, lambda: state.get().open_map(self.target))


class DCTLINK_OT_unlink_image(_Op):
    bl_idname = "dct_link.unlink_image"
    bl_label = EN["op.unlink"]
    bl_description = EN["op.unlink.desc"]

    @classmethod
    def poll(cls, context):
        reason = _controller_reason()
        if reason is None and state.get().stream.active:
            reason = msg("open.stop-live-first")
        return _refuse(cls, reason)

    def execute(self, context):
        image = context.scene.dct_link.image
        if image is not None:
            host.clear_binding(image)
            state.get().touch()
        return {"FINISHED"}


class DCTLINK_OT_unlink_model(_Op):
    bl_idname = "dct_link.unlink_model"
    bl_label = EN["op.unlink"]
    bl_description = EN["op.unlink-model.desc"]

    @classmethod
    def poll(cls, context):
        reason = _controller_reason()
        if reason is None and host.stored_binding(model_root(context)) is None:
            reason = msg("model.not-linked")
        return _refuse(cls, reason)

    def execute(self, context):
        root = model_root(context)
        if root is not None:
            host.clear_binding(root)
            host.push_undo(t("op.unlink"))
            state.get().touch()
        return {"FINISHED"}


class DCTLINK_OT_use_paint_image(_Op):
    bl_idname = "dct_link.use_paint_image"
    bl_label = EN["op.use-paint-image"]
    bl_description = EN["op.use-paint-image.desc"]

    def execute(self, context):
        image = host.painted_image(context)
        if image is None:
            self.report({"WARNING"}, t("image.no-painted"))
            return {"CANCELLED"}
        context.scene.dct_link.image = image
        return {"FINISHED"}


def _live_start_reason(context: Any) -> Optional[Msg]:
    reason = _ready_reason()
    if reason is not None:
        return reason
    ctrl = state.get()
    if ctrl.focused is None and host.stored_binding(context.scene.dct_link.image) is None:
        return msg("notice.select-cloth")  # an image linked to its cloth needs no selection
    problem = ctrl.feature_problem(settings.FEATURE_LIVE_TEXTURE)
    if problem is not None:
        return msg("live.upsell") if problem.key == "feature.needsUltimate" else problem
    return host.image_problem(context.scene.dct_link.image, load=False)


class DCTLINK_OT_live_start(_Op):
    bl_idname = "dct_link.live_start"
    bl_label = EN["op.live-start"]
    bl_description = EN["op.live-start.desc"]

    @classmethod
    def poll(cls, context):
        return _refuse(cls, _live_start_reason(context))

    def execute(self, context):
        props = context.scene.dct_link
        image = props.image
        problem = host.image_problem(image)
        if problem:
            self.report({"ERROR"}, strings.text(problem))
            return {"CANCELLED"}

        # An image opened from Durty Cloth Tool always goes to its own cloth and map, also after reconnecting.
        binding = host.stored_binding(image)
        target = (host.stored_map(image) or props.target) if binding else props.target

        def start() -> None:
            source = host.BlenderImageSource(image, target)
            state.get().stream.start(source, target, source.width, source.height, source.conversion,
                                     document=image.name, warning=source.warning, binding=binding)

        try:
            return _run(self, start)
        except MemoryError:
            self.report({"ERROR"}, t("live.no-memory"))
            return {"CANCELLED"}


def _live_reason() -> Optional[Msg]:
    reason = _controller_reason()
    if reason is None and not state.get().stream.is_open:
        reason = msg("notice.start-live-first")
    return reason


class DCTLINK_OT_live_stop(_Op):
    bl_idname = "dct_link.live_stop"
    bl_label = EN["op.live-stop"]
    bl_description = EN["op.live-stop.desc"]

    @classmethod
    def poll(cls, context):
        reason = _controller_reason()
        if reason is None and not state.get().stream.active:
            reason = msg("notice.start-live-first")
        return _refuse(cls, reason)

    def execute(self, context):
        return _run(self, lambda: state.get().stream.stop())


class DCTLINK_OT_live_pause(_Op):
    bl_idname = "dct_link.live_pause"
    bl_label = EN["op.live-pause"]
    bl_description = EN["op.live-pause.desc"]

    @classmethod
    def poll(cls, context):
        return _refuse(cls, _live_reason())

    @classmethod
    def description(cls, context, properties):
        paused = state.controller is not None and state.controller.stream.paused
        return tt("op.live-resume.desc" if paused else "op.live-pause.desc")

    def execute(self, context):
        stream = state.get().stream
        return _run(self, stream.resume if stream.paused else stream.pause)


class DCTLINK_OT_live_send_now(_Op):
    bl_idname = "dct_link.live_send_now"
    bl_label = EN["op.live-send"]
    bl_description = EN["op.live-send.desc"]

    @classmethod
    def poll(cls, context):
        reason = _live_reason()
        if reason is None and state.get().stream.paused:
            reason = msg("live.paused")
        return _refuse(cls, reason)

    def execute(self, context):
        return _run(self, lambda: state.get().stream.send_now())


def _save_reason(variation: bool) -> Optional[Msg]:
    reason = _live_reason()
    if reason is not None:
        return reason
    ctrl = state.get()
    stream = ctrl.stream
    if stream.saving:
        return msg("notice.wait-saving")
    problem = ctrl.feature_problem(settings.FEATURE_SAVE)
    if problem is not None:
        return msg("live.save-upsell") if problem.key == "feature.needsUltimate" else problem
    if variation and stream.target != "diffuse":
        return msg("notice.diffuse-only")
    return None


class DCTLINK_OT_live_save(_Op):
    bl_idname = "dct_link.live_save"
    bl_label = EN["op.live-save"]
    bl_description = EN["op.live-save.desc"]

    @classmethod
    def poll(cls, context):
        return _refuse(cls, _save_reason(False))

    def execute(self, context):
        return _run(self, lambda: state.get().stream.save("replace"))


class DCTLINK_OT_live_save_variation(_Op):
    bl_idname = "dct_link.live_save_variation"
    bl_label = EN["op.live-save-variation"]
    bl_description = EN["op.live-save-variation.desc"]

    @classmethod
    def poll(cls, context):
        return _refuse(cls, _save_reason(True))

    @classmethod
    def description(cls, context, properties):
        return f"{tt('op.live-save-variation.desc')}.\n{tt('info.variation')}"

    def execute(self, context):
        return _run(self, lambda: state.get().stream.save("newVariation"))


class DCTLINK_OT_live_discard(_Op):
    bl_idname = "dct_link.live_discard"
    bl_label = EN["op.live-discard"]
    bl_description = EN["op.live-discard.desc"]

    @classmethod
    def poll(cls, context):
        return _refuse(cls, _live_reason())

    def execute(self, context):
        return _run(self, lambda: state.get().stream.discard())


class DCTLINK_OT_check_again(_Op):
    bl_idname = "dct_link.check_again"
    bl_label = EN["op.check-again"]
    bl_description = EN["op.check-again.desc"]

    @classmethod
    def poll(cls, context):
        reason = _live_reason()
        if reason is None and state.get().stream.checking:
            reason = msg("checks.checking")
        return _refuse(cls, reason)

    def execute(self, context):
        return _run(self, lambda: state.get().stream.check_texture())


def _push_reason() -> Optional[Msg]:
    reason = _ready_reason()
    if reason is not None:
        return reason
    ctrl = state.get()
    available, status = host.sollumz_status()
    if not available:
        return status
    problem = ctrl.feature_problem(settings.FEATURE_MODEL)
    if problem is not None:
        return problem
    if ctrl.model.pushing:
        return msg("notice.pushing")
    return None


class DCTLINK_OT_model_push(_Op):
    bl_idname = "dct_link.model_push"
    bl_label = EN["op.model-push"]
    bl_description = EN["op.model-push.desc"]

    @classmethod
    def poll(cls, context):
        return _refuse(cls, _push_reason())

    def execute(self, context):
        objects = list(context.selected_objects) or ([context.active_object] if context.active_object else [])
        return _run(self, lambda: state.push_model(host.drawable_root(objects)))


class DCTLINK_OT_model_save(_Op):
    bl_idname = "dct_link.model_save"
    bl_label = EN["op.model-save"]
    bl_description = EN["op.model-save.desc"]

    @classmethod
    def poll(cls, context):
        return _refuse(cls, _ready_reason() or state.get().model.save_blocker)

    def execute(self, context):
        return _run(self, lambda: state.get().model.save())


class DCTLINK_OT_model_discard(_Op):
    bl_idname = "dct_link.model_discard"
    bl_label = EN["op.model-discard"]
    bl_description = EN["op.model-discard.desc"]

    @classmethod
    def poll(cls, context):
        reason = _ready_reason()
        if reason is None:
            model = state.get().model
            if model.lease is None:
                reason = msg("model.block.no-model")
            elif model.busy is not None:
                reason = msg("model.block.waiting")
        return _refuse(cls, reason)

    def execute(self, context):
        return _run(self, lambda: state.get().model.discard())


# --------------------------------------------------------------------------------------------------
# Panels
# --------------------------------------------------------------------------------------------------


class _DCTPanel:
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "DCT"
    bl_translation_context = CONTEXT


class DCTLINK_PT_main(_DCTPanel, Panel):
    bl_label = EN["panel.main"]

    def draw_header(self, context):
        icon = _logo_icon()
        if icon:
            self.layout.label(text="", icon_value=icon)
        else:
            self.layout.label(text="", icon="LINKED")

    def draw_header_preset(self, context):
        self.layout.menu(DCTLINK_MT_help.bl_idname, text="", icon="HELP")

    def draw(self, context):
        if state.controller is None:
            self.layout.label(text=t("notice.not-ready"), translate=False)
            return
        draw_status(self.layout, context)
        settings_ = getattr(context.scene, "dct_link", None)
        if settings_ is not None:
            self.layout.separator(factor=GAP_SMALL)
            self.layout.row(align=True).prop(settings_, "workspace", expand=True)


class DCTLINK_PT_details(Panel):
    """The connection details, opened from the status button."""

    bl_space_type = "VIEW_3D"
    bl_region_type = "HEADER"
    bl_label = EN["panel.details"]
    bl_translation_context = CONTEXT
    bl_ui_units_x = 16

    def draw(self, context):
        if state.controller is None:
            return
        self.layout.label(text=t("panel.details"), translate=False)
        draw_details(self.layout, context)


class _SubPanel(_DCTPanel):
    bl_parent_id = "DCTLINK_PT_main"


class DCTLINK_PT_setup(_SubPanel, Panel):
    bl_label = EN["panel.setup"]

    @classmethod
    def poll(cls, context):
        return state.controller is not None and state.controller.setup_needed

    def draw(self, context):
        draw_setup(self.layout, context)


class DCTLINK_PT_linked(_SubPanel, Panel):
    bl_label = EN["panel.linked"]

    @classmethod
    def poll(cls, context):
        return state.is_ready() and workspace(context) == "CLOTHING"

    def draw(self, context):
        draw_linked(self.layout, context)


def _working_panels_shown(context: Any = None) -> bool:
    """Linked work (live preview, model) is shown once setup is done, while the tab works on clothing; until then Get
    Connected has the focus."""
    return (state.controller is not None and not state.controller.setup_needed
            and workspace(context or bpy.context) == "CLOTHING")


class DCTLINK_PT_live(_SubPanel, Panel):
    bl_label = EN["panel.live"]

    @classmethod
    def poll(cls, context):
        return _working_panels_shown(context)

    def draw(self, context):
        draw_live(self.layout, context)


class DCTLINK_PT_model(_SubPanel, Panel):
    bl_label = EN["panel.model"]

    @classmethod
    def poll(cls, context):
        return _working_panels_shown(context)

    def draw(self, context):
        draw_model(self.layout, context)


class DCTLINK_PT_settings(_SubPanel, Panel):
    bl_label = EN["panel.settings"]
    bl_options = {"DEFAULT_CLOSED"}
    bl_order = 1  # last, after Garment Fitting and Custom Ped (registered later by ui_garment and ui_ped)

    @classmethod
    def poll(cls, context):
        return state.controller is not None

    def draw(self, context):
        draw_settings(self.layout, context, state.preferences(context))


CLASSES = (
    DCTLINK_PG_scene,
    DCTLINK_OT_connect,
    DCTLINK_OT_disconnect,
    DCTLINK_OT_sign_in,
    DCTLINK_OT_sign_in_browser,
    DCTLINK_OT_open_sign_in_page,
    DCTLINK_OT_copy_code,
    DCTLINK_OT_cancel_sign_in,
    DCTLINK_OT_sign_out,
    DCTLINK_OT_open_update_page,
    DCTLINK_OT_open_plugins_page,
    DCTLINK_OT_open_help,
    DCTLINK_OT_open_community,
    DCTLINK_OT_join_discord,
    DCTLINK_OT_diagnostics,
    DCTLINK_OT_info,
    DCTLINK_OT_about,
    DCTLINK_MT_help,
    DCTLINK_OT_open_map,
    DCTLINK_OT_unlink_image,
    DCTLINK_OT_unlink_model,
    DCTLINK_OT_use_paint_image,
    DCTLINK_OT_live_start,
    DCTLINK_OT_live_stop,
    DCTLINK_OT_live_pause,
    DCTLINK_OT_live_send_now,
    DCTLINK_OT_live_save,
    DCTLINK_OT_live_save_variation,
    DCTLINK_OT_live_discard,
    DCTLINK_OT_check_again,
    DCTLINK_OT_model_push,
    DCTLINK_OT_model_save,
    DCTLINK_OT_model_discard,
    DCTLINK_PT_main,
    DCTLINK_PT_details,
    DCTLINK_PT_setup,
    DCTLINK_PT_linked,
    DCTLINK_PT_live,
    DCTLINK_PT_model,
    DCTLINK_PT_settings,
)


def register() -> None:
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    bpy.types.Scene.dct_link = PointerProperty(type=DCTLINK_PG_scene)


def unregister() -> None:
    del bpy.types.Scene.dct_link
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
