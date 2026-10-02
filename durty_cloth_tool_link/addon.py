# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2026 Schmid Software Solutions (https://schmid-software.de)
"""Registration: classes, the timer that drives the link, and the handlers for file loads, undo and model
changes."""

from __future__ import annotations

import time
import traceback

import bpy
from bpy.app.handlers import persistent

from . import host, link, preferences, settings, state, ui

_started = False


def tick() -> float:
    """The ``bpy.app.timers`` step: drives the link session. Everything is caught here, because Blender removes a
    timer that raises."""
    global _started
    ctrl = state.controller
    if ctrl is None:
        return 1.0
    try:
        if not _started:
            _started = True
            _start(ctrl)
        interval = ctrl.poll()
    except Exception as exc:  # noqa: BLE001 - keep the timer alive and show the problem
        traceback.print_exc()
        ctrl.notice = link.Notice("ERROR", f"The add-on hit an unexpected problem: {type(exc).__name__}: {exc}")
        ctrl.touch()
        interval = 0.25
    if ctrl.changed:
        ctrl.changed = False
        try:
            host.redraw()
        except Exception:  # noqa: BLE001 - a redraw problem must not stop the link
            traceback.print_exc()
    return interval


def _start(ctrl: link.LinkController) -> None:
    prefs = state.preferences()
    if prefs is not None:
        ctrl.model.delay = prefs.auto_push_delay
    try:
        ctrl.prepare()
    except Exception as exc:  # noqa: BLE001 - a damaged secret store must not stop the add-on; signing in fixes it
        traceback.print_exc()
        ctrl.notice = link.Notice("ERROR", f"The stored sign-in or pairing could not be read ({type(exc).__name__}). "
                                           "Sign in or pair again.")
    if prefs is not None and prefs.auto_connect:
        ctrl.connect()


def _device_name():
    prefs = state.preferences()
    return host.computer_name() if prefs is None or prefs.share_device_name else None


def _open_url(url: str) -> None:
    if settings.is_gta_clothing_url(url):
        bpy.ops.wm.url_open(url=url)


@persistent
def _on_load_pre(*_args) -> None:
    ctrl = state.controller
    if ctrl is not None:
        ctrl.stream.stop()
        ctrl.model.due_at = None
        ctrl.model.root_name = None  # the pushed objects belong to the file being closed
        state.watcher.clear()


@persistent
def _on_undo_redo(*_args) -> None:
    state.watcher.forget()  # undo replaces the objects; look the model up again


@persistent
def _on_depsgraph_update(scene, depsgraph) -> None:
    ctrl = state.controller
    try:
        if ctrl is None or ctrl.model.lease is None or not state.scene_auto_push(scene):
            return
        if state.watcher.relevant(depsgraph):
            ctrl.model.schedule(time.monotonic())
    except Exception:  # noqa: BLE001 - never let a handler problem repeat on every update
        traceback.print_exc()


_HANDLERS = (
    ("load_pre", _on_load_pre),
    ("undo_post", _on_undo_redo),
    ("redo_post", _on_undo_redo),
    ("depsgraph_update_post", _on_depsgraph_update),
)


def register() -> None:
    global _started
    preferences.register()
    ui.register()
    ctrl = link.LinkController(
        lambda: host.data_dir(state.PACKAGE),
        host.host_version(),
        online=host.online_access,
        device_name=_device_name,
        open_url=_open_url,
    )
    ctrl.model.on_auto_push = state.auto_push
    ctrl.model.auto_enabled = state.scene_auto_push
    state.controller = ctrl
    state.watcher.clear()
    _started = False
    bpy.app.timers.register(tick, first_interval=0.5, persistent=True)
    for name, handler in _HANDLERS:
        getattr(bpy.app.handlers, name).append(handler)


def unregister() -> None:
    for name, handler in _HANDLERS:
        handlers = getattr(bpy.app.handlers, name)
        if handler in handlers:
            handlers.remove(handler)
    if bpy.app.timers.is_registered(tick):
        bpy.app.timers.unregister(tick)
    ctrl, state.controller = state.controller, None
    if ctrl is not None:
        try:
            ctrl.shutdown()
        except Exception:  # noqa: BLE001 - disabling must always finish
            traceback.print_exc()
    state.watcher.clear()
    ui.unregister()
    preferences.unregister()
