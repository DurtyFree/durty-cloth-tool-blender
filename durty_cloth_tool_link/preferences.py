# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2026 Schmid Software Solutions (https://schmid-software.de)
"""The add-on preferences: connection, pairing, account, update channel and the update repository."""

from __future__ import annotations

from typing import Any, Optional

import bpy
from bpy.props import BoolProperty, EnumProperty, FloatProperty, StringProperty
from bpy.types import AddonPreferences, Operator

from . import host, settings, state, ui

DISK_INSTALL = ("This copy was installed from a file, so Blender cannot update it. To get updates, add the "
                "repository, uninstall this copy, and install Durty Cloth Tool Link from the Durty Cloth Tool "
                "repository in Get Extensions. Blender keeps the sign-in and pairing per installation, so pair and "
                "sign in again afterwards.")


def _delay_changed(self: Any, context: Any) -> None:
    if state.controller is not None:
        state.controller.model.delay = self.auto_push_delay


def _repository_url(self: Any) -> str:
    # A module-level function, not a lambda: annotations are evaluated without this module's globals.
    return settings.repository_url(self.channel)


def dct_repositories() -> list:
    """Blender extension repositories that point at a Durty Cloth Tool channel."""
    return [repo for repo in bpy.context.preferences.extensions.repos if settings.repository_channel(repo.remote_url)]


class DCTLINK_AddonPreferences(AddonPreferences):
    bl_idname = state.PACKAGE

    channel: EnumProperty(
        name="Update Channel",
        items=settings.CHANNELS,
        default=settings.CHANNEL,
        description="Which repository Add Update Repository adds: stable Release versions or early Experimental ones",
    )
    auto_connect: BoolProperty(
        name="Connect Automatically",
        default=True,
        description="Look for Durty Cloth Tool on this computer when Blender starts",
    )
    share_device_name: BoolProperty(
        name="Show This Computer's Name When Signing In",
        default=True,
        description=("Send this computer's name with a sign-in request, so the gta.clothing approval page can show "
                     "which computer asks"),
    )
    auto_push_delay: FloatProperty(
        name="Automatic Push Delay",
        default=settings.AUTO_PUSH_DELAY_DEFAULT,
        min=settings.AUTO_PUSH_DELAY_MIN,
        max=settings.AUTO_PUSH_DELAY_MAX,
        precision=1,
        update=_delay_changed,
        description="Seconds a pushed model must stay unchanged before Push Automatically sends it again",
    )
    repository_url: StringProperty(
        name="Repository URL",
        get=_repository_url,
        description="The extension repository for the chosen channel. Hover and press Ctrl+C to copy it",
    )

    def draw(self, context):
        layout = self.layout
        if state.controller is None:
            layout.label(text="The add-on is not ready")
            return

        box = layout.box()
        box.label(text="Durty Cloth Tool", icon="LINKED")
        ui.draw_connection(box, context)
        box.prop(self, "auto_connect")
        ui.wrapped(box, context, "Needs Durty Cloth Tool running on this computer with Creator Link turned on in its "
                                 "options. The connection stays on this computer; gta.clothing confirms your sign-in "
                                 "for each connection.")

        box = layout.box()
        box.label(text="Pairing", icon="LINKED")
        ui.draw_pairing_status(box, context)

        box = layout.box()
        box.label(text="Account", icon="USER")
        ui.draw_account(box, context)
        box.prop(self, "share_device_name")

        box = layout.box()
        box.label(text="Models", icon="EXPORT")
        box.prop(self, "auto_push_delay")

        box = layout.box()
        box.label(text="Updates", icon="FILE_REFRESH")
        box.label(text=f"This version: {settings.VERSION} ({settings.CHANNEL.capitalize()})")
        if not host.installed_from_dct_repository(state.PACKAGE):
            ui.wrapped(box, context, DISK_INSTALL, "ERROR")
        box.row().prop(self, "channel", expand=True)
        repositories = dct_repositories()
        if repositories:
            for repo in repositories:
                channel = settings.repository_channel(repo.remote_url)
                text = f"Repository added: {repo.name} ({channel})"
                box.label(text=text, icon="CHECKMARK" if channel == self.channel else "INFO")
            if all(settings.repository_channel(r.remote_url) != self.channel for r in repositories):
                ui.wrapped(box, context, "Your repository follows another channel. Add Update Repository switches it.")
        else:
            ui.wrapped(box, context, "Updates come from the Durty Cloth Tool extension repository. Create a "
                                     "repository token on gta.clothing, then add the repository with it.")
        row = box.row(align=True)
        row.operator("wm.url_open", text="Create Repository Token", icon="URL").url = settings.PLUGINS_PAGE_URL
        row.operator("dct_link.add_repository", icon="ADD")
        box.prop(self, "repository_url")
        ui.wrapped(box, context, "To add it by hand: Preferences > Get Extensions > Repositories > + > Add Remote "
                                 "Repository, paste the URL above, turn on Requires Access Token and paste the token "
                                 "as Secret.")


class DCTLINK_OT_add_repository(Operator):
    bl_idname = "dct_link.add_repository"
    bl_label = "Add Update Repository"
    bl_description = ("Add the Durty Cloth Tool extension repository to Blender with your repository token, so "
                      "Blender can update the add-on")

    token: StringProperty(
        name="Repository Token",
        subtype="PASSWORD",
        options={"SKIP_SAVE"},
        description="The repository token you created on the plugins page of your gta.clothing account",
    )
    channel: EnumProperty(name="Channel", items=settings.CHANNELS, options={"SKIP_SAVE"})

    def invoke(self, context, event):
        prefs = state.preferences(context)
        if prefs is not None:
            self.channel = prefs.channel
        return context.window_manager.invoke_props_dialog(self, width=460)

    def draw(self, context):
        layout = self.layout
        ui.wrapped(layout, context, "Paste the repository token from the plugins page of your gta.clothing "
                                    "account. Blender keeps it with its repository settings.")
        layout.prop(self, "token")
        layout.prop(self, "channel", expand=True)

    def execute(self, context):
        token = self.token.strip()
        self.token = ""
        if not token:
            self.report({"ERROR"}, "Paste the repository token first")
            return {"CANCELLED"}
        if len(token) > 512 or any(c.isspace() or not c.isprintable() for c in token):
            self.report({"ERROR"}, "That does not look like a repository token")
            return {"CANCELLED"}
        problem = add_repository(self.channel, token)
        if problem:
            self.report({"ERROR"}, problem)
            return {"CANCELLED"}
        if host.installed_from_dct_repository(state.PACKAGE):
            self.report({"INFO"}, "Added the Durty Cloth Tool repository. Check for updates in Get Extensions")
        else:
            self.report({"WARNING"}, "Added the repository. " + DISK_INSTALL)
        return {"FINISHED"}


def add_repository(channel: str, token: str) -> Optional[str]:
    """Adds (or updates) the Durty Cloth Tool repository with an access token. Returns a problem or ``None``."""
    url = settings.repository_url(channel)
    existing = dct_repositories()
    if existing:
        repo = existing[0]
        repo.remote_url = url
        repo.use_access_token = True
        repo.access_token = token
        return None
    operator = bpy.ops.preferences.extension_repo_add
    properties = {p.identifier for p in operator.get_rna_type().properties}
    if not {"remote_url", "use_access_token", "access_token"} <= properties:
        return ("This Blender version cannot add the repository with a token. Add it by hand in Preferences > Get "
                "Extensions > Repositories.")
    arguments = dict(name=settings.REPOSITORY_NAME, remote_url=url, use_access_token=True, access_token=token)
    if "use_sync_on_startup" in properties:
        arguments["use_sync_on_startup"] = True
    if "type" in properties:
        arguments["type"] = "REMOTE"
    try:
        result = operator("EXEC_DEFAULT", **arguments)
    except RuntimeError as exc:
        return f"Blender could not add the repository: {exc}"
    if "FINISHED" not in result:
        return "Blender could not add the repository."
    return None


CLASSES = (DCTLINK_AddonPreferences, DCTLINK_OT_add_repository)


def register() -> None:
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
