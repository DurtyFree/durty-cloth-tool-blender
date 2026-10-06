# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2026 Schmid Software Solutions (https://schmid-software.de)
"""Registration: translations, the logo icon, classes (the link's, the garment fitting tools' and Custom Ped's), the
timer that drives the link, and the handlers for file loads, undo and model changes."""

from __future__ import annotations

import pathlib
import time
import traceback

import bpy
from bpy.app.handlers import persistent

from . import garment_dct, host, link, ped_link, preferences, settings, state, strings, translations, ui, ui_garment
from . import ped_host, ui_ped
from .strings import msg

_started = False
_icons = None


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
        if ctrl.peds.busy:  # a rig reports its progress, a ped's upload goes out
            interval = min(interval, 0.05)
    except Exception as exc:  # noqa: BLE001 - keep the timer alive and show the problem
        traceback.print_exc()
        ctrl.notice = link.Notice("ERROR", msg("notice.unexpected", detail=f"{type(exc).__name__}: {exc}"))
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
        ctrl.notice = link.Notice("ERROR", msg("notice.secrets-unreadable", detail=type(exc).__name__))
    try:
        garment_dct.remove_stale_work(ctrl.data_dir)  # left over from a Blender that closed during an add
        ped_host.remove_stale_work(ctrl.data_dir)  # or while it created a custom ped
    except OSError:
        traceback.print_exc()
    if prefs is not None and prefs.auto_connect:
        ctrl.connect()


def _device_name():
    prefs = state.preferences()
    return host.computer_name() if prefs is None or prefs.share_device_name else None


def _open_url(url: str) -> None:
    if settings.is_gta_clothing_url(url):
        bpy.ops.wm.url_open(url=url)


def logo_icon() -> int:
    """The icon id of the Durty Cloth Tool mark (0 when it could not be loaded)."""
    if _icons is None or "dct_mark" not in _icons:
        return 0
    return _icons["dct_mark"].icon_id


def thumbnail_icon() -> int:
    """The icon id of the cloth's picture in the Linked Cloth panel (0 while there is none)."""
    ctrl = state.controller
    if _icons is None or ctrl is None or ctrl.thumbnail is None or THUMBNAIL not in _icons:
        return 0
    return _icons[THUMBNAIL].icon_id


#: The preview that shows the cloth's picture (rows from DCT arrive top to bottom; previews start at the bottom).
THUMBNAIL = "cloth_thumbnail"


def _show_thumbnail(thumbnail) -> None:
    if _icons is None or thumbnail is None:
        return
    import numpy as np

    preview = _icons[THUMBNAIL] if THUMBNAIL in _icons else _icons.new(THUMBNAIL)
    rgba = np.frombuffer(thumbnail.pixels, dtype=np.uint8).reshape(thumbnail.height, thumbnail.width, 4)[::-1]
    values = (rgba.astype(np.float32) / np.float32(255)).reshape(-1)
    size = (thumbnail.width, thumbnail.height)
    preview.image_size = size
    preview.image_pixels_float.foreach_set(values)
    preview.icon_size = size
    preview.icon_pixels_float.foreach_set(values)


def _load_icons() -> None:
    global _icons
    try:
        import bpy.utils.previews

        _icons = bpy.utils.previews.new()
        _icons.load("dct_mark", str(pathlib.Path(__file__).parent / "icons" / "dct-mark.png"), "IMAGE")
    except (OSError, RuntimeError, KeyError) as exc:  # the panels fall back to a Blender icon
        print(f"Durty Cloth Tool Link: the logo could not be loaded ({exc})")
        _icons = None


def _free_icons() -> None:
    global _icons
    if _icons is not None:
        import bpy.utils.previews

        bpy.utils.previews.remove(_icons)
    _icons = None


def _install_translations() -> None:
    try:
        bpy.app.translations.register(state.PACKAGE, translations.blender_tables())
    except ValueError:  # registered already (a reload); the old tables stay in use
        pass

    def iface(text: str) -> str:
        return bpy.app.translations.pgettext_iface(text, strings.CONTEXT)

    def tooltip(text: str) -> str:
        return bpy.app.translations.pgettext_tip(text, strings.CONTEXT)

    strings.set_translators(iface, tooltip)


def _remove_translations() -> None:
    strings.set_translators(None)
    try:
        bpy.app.translations.unregister(state.PACKAGE)
    except (ValueError, RuntimeError):  # never registered
        pass


@persistent
def _on_load_pre(*_args) -> None:
    ui_garment.on_load_pre()
    ui_ped.on_load_pre()
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
    _install_translations()
    _load_icons()
    preferences.register()
    ui.register()
    ui_garment.register()
    ui_ped.register()
    ctrl = link.LinkController(
        lambda: host.data_dir(state.PACKAGE),
        host.host_version(),
        online=host.online_access,
        device_name=_device_name,
        open_url=_open_url,
    )
    ctrl.model.on_auto_push = state.auto_push
    ctrl.model.auto_enabled = state.scene_auto_push
    ctrl.documents = state.BlenderDocuments()
    ctrl.linked_binding = state.linked_binding
    ctrl.on_thumbnail = _show_thumbnail
    ctrl.fitting.on_ended = ui_garment.fit_ended
    ctrl.peds = ped_link.PedLink(ctrl)
    ctrl.peds.on_created = ui_ped.on_created
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
    ui_ped.unregister()
    ui_garment.unregister()
    ui.unregister()
    preferences.unregister()
    _free_icons()
    _remove_translations()
