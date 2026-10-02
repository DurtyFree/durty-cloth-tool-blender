# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2026 Schmid Software Solutions (https://schmid-software.de)
"""The add-on's single link controller and the helpers the panels, operators and timers share."""

from __future__ import annotations

import time
import traceback
from typing import Any, Optional

import bpy

from . import host, link

#: The extension's package name (``bl_ext.<repository>.durty_cloth_tool_link``).
PACKAGE = __package__

controller: Optional[link.LinkController] = None
watcher = host.AutoPushWatcher()


def get() -> link.LinkController:
    if controller is None:
        raise RuntimeError("the Durty Cloth Tool add-on is not registered")
    return controller


def preferences(context: Optional[Any] = None) -> Optional[Any]:
    addon = (context or bpy.context).preferences.addons.get(PACKAGE)
    return addon.preferences if addon is not None else None


def is_ready() -> bool:
    return controller is not None and controller.ready


def current_scene() -> Optional[Any]:
    window = getattr(bpy.context, "window", None) or host.first_window()
    return window.scene if window is not None else getattr(bpy.context, "scene", None)


def model_scene() -> Optional[Any]:
    """The scene that holds the pushed model, as shown in a window (the active one first); the current scene
    when no model is pushed or it is not shown."""
    root = watcher.root()
    if root is not None:
        window = host.window_for(root)
        if window is not None:
            return window.scene
        scenes = list(getattr(root, "users_scene", ()))
        if scenes:
            return scenes[0]
    return current_scene()


def scene_auto_push(scene: Optional[Any] = None) -> bool:
    """Push Automatically of the scene that holds the pushed model, read when it is needed (undo, redo and
    switching scenes change it without telling the add-on)."""
    scene = scene if scene is not None else model_scene()
    settings = getattr(scene, "dct_link", None) if scene is not None else None
    return bool(settings is not None and settings.auto_push)


def push_model(root: Any, automatic: bool = False) -> None:
    """Exports ``root`` with Sollumz and pushes it. Raises ``ValueError`` with a message for the user."""
    ctrl = get()
    watcher.exporting = True
    try:
        ctrl.model.push(lambda folder: host.export_with_sollumz(root, folder), root.name, automatic=automatic)
        watcher.watch(root)
    finally:
        watcher.exporting = False
        watcher.forget()  # the hierarchy may have changed; read it again at the next update


def auto_push() -> None:
    """Called by the controller when the pushed model changed and stayed unchanged for the delay."""
    ctrl = get()
    root = watcher.root()
    if root is None:
        ctrl.model.status = link.Notice("WARNING", "The pushed model is no longer in this file. Push it again.")
        ctrl.touch()
        return
    blocker = host.auto_push_blocker(root)
    if blocker is not None:
        ctrl.model.postpone(time.monotonic(), blocker)  # not while a tool runs or outside Object Mode
        return
    try:
        push_model(root, automatic=True)
    except ValueError as exc:
        ctrl.model.status = link.Notice("ERROR", str(exc))
        ctrl.touch()
    except Exception as exc:  # noqa: BLE001 - an automatic push must never break the timer
        traceback.print_exc()
        ctrl.model.status = link.Notice("ERROR", f"The automatic push failed: {type(exc).__name__}: {exc}")
        ctrl.touch()
