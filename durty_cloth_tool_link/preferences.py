# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2026 Schmid Software Solutions (https://schmid-software.de)
"""The add-on preferences: the same groups as the sidebar's Settings (Connection, Account, Models, Updates,
Privacy), and the setup steps while setup is incomplete."""

from __future__ import annotations

from typing import Any

import bpy
from bpy.props import BoolProperty, FloatProperty
from bpy.types import AddonPreferences

from . import settings, state, ui
from .strings import CONTEXT, EN, t


def _delay_changed(self: Any, context: Any) -> None:
    if state.controller is not None:
        state.controller.model.delay = self.auto_push_delay


class DCTLINK_AddonPreferences(AddonPreferences):
    bl_idname = state.PACKAGE

    auto_connect: BoolProperty(
        name=EN["prop.auto-connect"],
        default=True,
        description=EN["prop.auto-connect.desc"],
        translation_context=CONTEXT,
    )
    share_device_name: BoolProperty(
        name=EN["prop.device-name"],
        default=True,
        description=EN["prop.device-name.desc"],
        translation_context=CONTEXT,
    )
    fit_upload_consent: BoolProperty(
        name=EN["prop.fit-consent"],
        default=False,
        description=EN["prop.fit-consent.desc"],
        translation_context=CONTEXT,
    )
    auto_push_delay: FloatProperty(
        name=EN["prop.delay"],
        default=settings.AUTO_PUSH_DELAY_DEFAULT,
        min=settings.AUTO_PUSH_DELAY_MIN,
        max=settings.AUTO_PUSH_DELAY_MAX,
        precision=1,
        subtype="TIME_ABSOLUTE",
        unit="TIME_ABSOLUTE",
        update=_delay_changed,
        description=EN["prop.delay.desc"],
        translation_context=CONTEXT,
    )

    def draw(self, context):
        layout = self.layout
        if state.controller is None:
            layout.label(text=t("notice.not-ready"), translate=False)
            return
        row = layout.row()
        icon = ui._logo_icon()
        if icon:
            row.label(text=t("panel.main"), icon_value=icon, translate=False)
        else:
            row.label(text=t("panel.main"), icon="LINKED", translate=False)
        ui.draw_status(layout, context)
        if state.controller.setup_needed:
            layout.separator(factor=ui.GAP)
            ui.heading(layout, context, "panel.setup", "CHECKBOX_HLT")
            ui.draw_setup(layout, context)
        layout.separator(factor=ui.GAP)
        ui.draw_settings(layout, context, self)


CLASSES = (DCTLINK_AddonPreferences,)


def register() -> None:
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
