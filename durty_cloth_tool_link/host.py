# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2026 Schmid Software Solutions (https://schmid-software.de)
"""Everything that touches Blender: where files are kept, reading images, detecting paint strokes, exporting
with Sollumz and redrawing the panels."""

from __future__ import annotations

import pathlib
import socket
import sys
from typing import Any, Dict, Iterable, List, NamedTuple, Optional, Set, Tuple

import bpy

from . import pixels, settings
from .dct_link import protocol, tokens

# --------------------------------------------------------------------------------------------------
# Environment
# --------------------------------------------------------------------------------------------------


def data_dir(package: str) -> pathlib.Path:
    """The add-on's user folder (Blender keeps it across updates of the same installation). Holds the install
    id, the protected sign-in and the protected pairing secret."""
    try:
        return pathlib.Path(bpy.utils.extension_path_user(package, create=True))
    except (ValueError, AttributeError, OSError):
        return tokens.plugin_data_dir(settings.PLUGIN_KIND)  # not installed as an extension


def host_version() -> str:
    major, minor, patch = tuple(bpy.app.version)[:3]
    return f"{major}.{minor}.{patch}"


def online_access() -> bool:
    """Blender's "Allow Online Access" (Preferences > System > Network). gta.clothing is only asked when it is on.
    The connection to Durty Cloth Tool stays on this computer, but every connection is confirmed with a sign-in
    assertion from gta.clothing, so connecting needs it too."""
    return bool(getattr(bpy.app, "online_access", True))


def computer_name() -> Optional[str]:
    name = socket.gethostname().strip()
    return name[: protocol.MAX_TEXT_LENGTH] if protocol.is_text(name) else None


def installed_repository(package: str) -> Optional[Any]:
    """The extension repository this copy of the add-on was installed into (``bl_ext.<repository>.<id>``)."""
    parts = package.split(".")
    if len(parts) < 3 or parts[0] != "bl_ext":
        return None
    for repo in bpy.context.preferences.extensions.repos:
        if repo.module == parts[1]:
            return repo
    return None


def installed_from_dct_repository(package: str) -> bool:
    """Whether Blender can update this copy: it came from a Durty Cloth Tool extension repository."""
    repo = installed_repository(package)
    return repo is not None and settings.repository_channel(repo.remote_url) is not None


def redraw() -> None:
    """Redraws the sidebars of the 3D Views and the preferences, nothing else."""
    wm = getattr(bpy.context, "window_manager", None)
    if wm is None:
        return
    for window in wm.windows:
        screen = window.screen
        if screen is None:
            continue
        for area in screen.areas:
            if area.type == "VIEW_3D":
                for region in area.regions:
                    if region.type == "UI":
                        region.tag_redraw()
            elif area.type == "PREFERENCES":
                area.tag_redraw()


def windows() -> List[Any]:
    wm = getattr(bpy.context, "window_manager", None)
    return list(wm.windows) if wm is not None else []


def first_window() -> Optional[Any]:
    found = windows()
    return found[0] if found else None


_MODAL_OPERATORS: Optional[bool] = None


def modal_operators_known() -> bool:
    """Whether this Blender lists the running modal operators of a window (``Window.modal_operators``). Without
    it, paint strokes and running tools cannot be seen; the first check says so once in the console."""
    global _MODAL_OPERATORS
    if _MODAL_OPERATORS is None:
        window = first_window()
        if window is None:
            return False  # no window yet (or background mode): nothing runs; check again later
        _MODAL_OPERATORS = "modal_operators" in window.bl_rna.properties
        if not _MODAL_OPERATORS:
            print("Durty Cloth Tool Link: this Blender does not report running tools, so texture captures wait for a "
                  "quiet moment instead of the end of each stroke, and automatic pushes only wait for the delay.")
    return _MODAL_OPERATORS


def _modal_operator_names() -> List[str]:
    if not modal_operators_known():
        return []
    names = []
    for window in windows():
        for operator in window.modal_operators:
            names.append(str(getattr(operator, "bl_idname", "")))
    return names


def paint_stroke_running() -> bool:
    """A paint stroke (or another painting tool drag) is in progress in some window."""
    return any(name.startswith("PAINT_OT_") or name.startswith("paint.") for name in _modal_operator_names())


def modal_operator_running() -> bool:
    """Any modal operator runs (a stroke, a transform, a file browser ...)."""
    return bool(_modal_operator_names())


def window_for(obj: Any) -> Optional[Any]:
    """The window whose view layer holds ``obj``: the active window when it does, otherwise the first one."""
    context_window = getattr(bpy.context, "window", None)
    candidates = ([context_window] if context_window is not None else []) + windows()
    uid = obj.session_uid
    for window in candidates:
        layer = window.view_layer
        found = layer.objects.get(obj.name) if layer is not None else None
        if found is not None and found.session_uid == uid:
            return window
    return None


def _mode_name(obj: Any) -> str:
    try:
        return obj.bl_rna.properties["mode"].enum_items[obj.mode].name
    except (KeyError, AttributeError):
        return obj.mode.replace("_", " ").title()


def auto_push_blocker(root: Any) -> Optional[str]:
    """Why an automatic push of ``root`` has to wait right now, or ``None``: a tool runs, or the view layer that
    holds the model is not in Object Mode (an export then would miss the newest edits)."""
    if modal_operator_running():
        return "The automatic push waits until the running tool finishes."
    window = window_for(root)
    layer = window.view_layer if window is not None else getattr(bpy.context, "view_layer", None)
    active = layer.objects.active if layer is not None else None
    if active is not None and active.mode != "OBJECT":
        return f"The automatic push waits until you leave {_mode_name(active)}."
    return None


# --------------------------------------------------------------------------------------------------
# Images
# --------------------------------------------------------------------------------------------------


def image_problem(image: Optional[Any]) -> Optional[str]:
    """Why an image cannot be streamed, or ``None``."""
    if image is None:
        return "Choose an image to stream."
    if image.source == "TILED":
        return "UDIM (tiled) images cannot be streamed. Use a single image."
    if image.source not in {"FILE", "GENERATED"}:
        return "Only image files and generated images can be streamed."
    try:
        len(image.pixels)  # loads the pixels when they are not in memory yet
    except (RuntimeError, ReferenceError):
        return "The image could not be read."
    if not image.has_data:
        return "The image could not be loaded. Check that its file exists."
    if image.channels not in (1, 3, 4):
        return "Only grey, RGB and RGBA images can be streamed."
    width, height = tuple(image.size)
    return settings.check_stream_size(width, height)


class BlenderImageSource:
    """One Blender image as the texture stream reads it (see ``link.ImageSource``)."""

    def __init__(self, image: Any, target: str) -> None:
        self.name = image.name
        self.uid = getattr(image, "session_uid", None)
        self.width, self.height = tuple(image.size)
        self.channels = image.channels
        self.target = target
        colour = image.colorspace_settings
        is_data = bool(getattr(colour, "is_data", colour.name == "Non-Color"))
        plan = pixels.colour_plan(target, self.channels, bool(image.is_float), colour.name, is_data,
                                  str(getattr(image, "alpha_mode", "STRAIGHT")))
        self.conversion = plan.conversion
        self.warning = plan.warning

    def image(self) -> Optional[Any]:
        image = bpy.data.images.get(self.name)
        if image is not None and (self.uid is None or getattr(image, "session_uid", None) == self.uid):
            return image
        if self.uid is not None:
            for candidate in bpy.data.images:
                if getattr(candidate, "session_uid", None) == self.uid:
                    self.name = candidate.name  # renamed
                    return candidate
        return None

    def problem(self) -> Optional[str]:
        image = self.image()
        if image is None:
            return "The streamed image was removed."
        if tuple(image.size) != (self.width, self.height) or image.channels != self.channels:
            return "The image size changed. Start streaming again."
        return None

    def is_dirty(self) -> bool:
        image = self.image()
        return image is not None and bool(image.is_dirty)

    def stroke_active(self) -> bool:
        return paint_stroke_running()

    def strokes_known(self) -> bool:
        return modal_operators_known()

    def read_into(self, buffer: Any) -> None:
        image = self.image()
        if image is None:
            raise RuntimeError("the streamed image was removed")
        image.pixels.foreach_get(buffer)


def painted_image(context: Any) -> Optional[Any]:
    """The image the user is painting or looking at: the Image Editor's image, the active paint slot, or the
    single-image canvas."""
    space = getattr(context, "space_data", None)
    if space is not None and getattr(space, "type", None) == "IMAGE_EDITOR" and space.image is not None:
        return space.image
    obj = getattr(context, "active_object", None)
    material = obj.active_material if obj is not None else None
    if material is not None:
        images = list(getattr(material, "texture_paint_images", []) or [])
        slot = getattr(material, "paint_active_slot", 0)
        if 0 <= slot < len(images):
            return images[slot]
    paint = getattr(getattr(context, "tool_settings", None), "image_paint", None)
    return getattr(paint, "canvas", None)


# --------------------------------------------------------------------------------------------------
# Sollumz
# --------------------------------------------------------------------------------------------------

DRAWABLE_DICTIONARY = "sollumz_drawable_dictionary"
DRAWABLE = "sollumz_drawable"

#: Settings the push always uses: CodeWalker XML for GTA V Legacy (gen8), the selected model only, nothing else.
FORCED_SETTINGS: Dict[str, Any] = {
    "target_formats": {"CWXML"},
    "target_versions": {"GEN8"},
    "limit_to_selected": True,
    "export_ytyps": False,
    "export_ymaps": False,
    "export_ytds": False,
}
_NOT_COPIED = {"rna_type", "directory", "direct_export", "use_custom_settings", "custom_settings", "filter_glob"}
_VERSION_CACHE: Dict[Tuple[str, int], Optional[str]] = {}


class ExportError(ValueError):
    """The model could not be exported; the message is shown to the user."""


class ExportResult(NamedTuple):
    #: Sollumz logged warnings or errors during the export.
    warnings: bool


def sollumz_operator_properties() -> Optional[Set[str]]:
    """The properties of Sollumz's export operator, or ``None`` when Sollumz is not enabled."""
    try:
        rna = bpy.ops.sollumz.export_assets.get_rna_type()
    except (AttributeError, KeyError, RuntimeError):
        return None
    return {prop.identifier for prop in rna.properties}


def _sollumz_addon() -> Optional[Any]:
    for addon in bpy.context.preferences.addons:
        if addon.module.rsplit(".", 1)[-1].lower() == "sollumz":
            return addon
    return None


def sollumz_version() -> Optional[str]:
    """Sollumz's version, looked up once per loaded Sollumz module (panels draw often)."""
    addon = _sollumz_addon()
    if addon is None:
        return None
    key = (addon.module, id(sys.modules.get(addon.module)))
    if key in _VERSION_CACHE:
        return _VERSION_CACHE[key]
    version: Optional[str] = None
    try:
        import addon_utils

        for module in addon_utils.modules():
            if module.__name__ == addon.module:
                info = addon_utils.module_bl_info(module).get("version")
                version = ".".join(str(part) for part in info) if info else None
                break
    except Exception:  # noqa: BLE001 - the version is display text only; show "Sollumz" without it
        version = None
    _VERSION_CACHE[key] = version
    return version


def sollumz_status() -> Tuple[bool, str]:
    """Whether models can be pushed, and a line for the panel."""
    properties = sollumz_operator_properties()
    if properties is None:
        return False, "Install and enable Sollumz to push models."
    if not {"directory", "direct_export"} <= properties:
        return False, "This Sollumz version cannot export without a file browser. Update Sollumz."
    version = sollumz_version()
    return True, f"Sollumz {version}" if version else "Sollumz"


def top_parent(obj: Any) -> Any:
    while obj.parent is not None:
        obj = obj.parent
    return obj


def drawable_root(objects: Iterable[Any]) -> Any:
    """The Sollumz Drawable Dictionary the objects belong to (the topmost parent, as Sollumz exports it)."""
    roots = []
    for obj in objects:
        top = top_parent(obj)
        if top not in roots:
            roots.append(top)
    if not roots:
        raise ExportError("Select the model to push (a Sollumz Drawable Dictionary or an object inside one).")
    if len(roots) > 1:
        raise ExportError("Select objects of one Drawable Dictionary only.")
    root = roots[0]
    kind = getattr(root, "sollum_type", None)
    if kind == DRAWABLE_DICTIONARY:
        return root
    if kind == DRAWABLE:
        raise ExportError("Durty Cloth Tool needs a Drawable Dictionary. Parent the Drawable to one "
                          "(Sollumz: Create Drawable Dictionary) and push again.")
    raise ExportError("Select a Sollumz Drawable Dictionary, or an object inside one.")


def _export_settings(properties: Set[str]) -> Dict[str, Any]:
    """The operator arguments for this Sollumz version: the user's Sollumz export settings (for example Exclude
    Skeleton) with the forced settings on top."""
    values: Dict[str, Any] = {}
    addon = _sollumz_addon()
    prefs = getattr(getattr(addon, "preferences", None), "export_settings", None) if addon is not None else None
    if prefs is not None:
        for prop in prefs.bl_rna.properties:
            name = prop.identifier
            if name not in _NOT_COPIED and not prop.is_readonly:
                values[name] = getattr(prefs, name)
    values.update(FORCED_SETTINGS)
    if "use_custom_settings" in properties and "target_formats" in properties:
        # Sollumz 2.8.1 and later: the settings are operator properties.
        return dict({k: v for k, v in values.items() if k in properties}, use_custom_settings=True)
    if "use_custom_settings" in properties and "custom_settings" in properties:
        # Sollumz 2.8.0: the settings are a group inside the operator.
        rna = bpy.ops.sollumz.export_assets.get_rna_type()
        group = {p.identifier for p in rna.properties["custom_settings"].fixed_type.properties}
        return {"use_custom_settings": True, "custom_settings": {k: v for k, v in values.items() if k in group}}
    # Older Sollumz exports CodeWalker XML with the user's settings; bundle collection checks the result.
    return {}


def _select_for_export(root: Any) -> Any:
    """Selects ``root`` or, when it cannot be selected (hidden or unselectable), a visible object inside it.
    Sollumz exports the topmost parent of what is selected, so either way ``root`` is exported."""
    for candidate in [root, *root.children_recursive]:
        try:
            candidate.select_set(True)
        except RuntimeError:
            continue  # not in the view layer
        if candidate.select_get() and candidate.visible_get():
            return candidate
        try:
            candidate.select_set(False)
        except RuntimeError:
            pass  # could not be selected in the first place
    raise ExportError("Unhide the Drawable Dictionary (or an object inside it) and make it selectable, then push "
                      "again.")


def _info_log_count() -> int:
    count = 0
    for window in windows():
        if window.screen is not None:
            count += sum(1 for area in window.screen.areas if area.type == "INFO")
    return count


_COUNTER_CLASSES: Dict[int, Any] = {}


def _sollumz_log_counter() -> Tuple[Optional[Any], Optional[Any]]:
    """Sollumz's ``use_logger`` and a logger that counts warnings and errors, when this Sollumz has them (2.7 and
    later route every export message through its root logger). ``(None, None)`` otherwise."""
    addon = _sollumz_addon()
    module = sys.modules.get(f"{addon.module}.logger") if addon is not None else None
    use_logger = getattr(module, "use_logger", None)
    base = getattr(module, "LoggerBase", None)
    if not callable(use_logger) or not isinstance(base, type):
        return None, None
    counter_class = _COUNTER_CLASSES.get(id(base))
    if counter_class is None:

        class Counter(base):  # type: ignore[misc, valid-type]
            def __init__(self) -> None:
                self.problems = 0

            def do_log(self, msg: str, level: str) -> None:
                if level in ("WARNING", "ERROR"):
                    self.problems += 1

        counter_class = _COUNTER_CLASSES[id(base)] = Counter
    try:
        return use_logger, counter_class()
    except TypeError:
        return None, None  # the logger base changed shape; fall back to watching the Info log


def _consume_updates(window: Optional[Any]) -> None:
    """Evaluates what the export changed (Sollumz switches armatures to the rest pose and back) while the push is
    still marked as running, so those updates do not look like edits and schedule another automatic push."""
    layers = [window.view_layer] if window is not None and window.view_layer is not None else []
    layers += [w.view_layer for w in windows() if w.view_layer is not None and w.view_layer not in layers]
    if not layers and getattr(bpy.context, "view_layer", None) is not None:
        layers = [bpy.context.view_layer]
    for layer in layers:
        try:
            layer.update()
        except (RuntimeError, ReferenceError):
            pass  # the view layer went away meanwhile; nothing of it is left to evaluate


def export_with_sollumz(root: Any, folder: str) -> ExportResult:
    """Exports ``root`` with Sollumz into ``folder``, in the window whose view layer holds it. Selects only what
    the export needs and restores the selection afterwards. Reports whether Sollumz logged warnings or errors."""
    properties = sollumz_operator_properties()
    if properties is None:
        raise ExportError("Install and enable Sollumz to push models.")
    if not {"directory", "direct_export"} <= properties:
        raise ExportError("This Sollumz version cannot export without a file browser. Update Sollumz.")
    arguments = dict(_export_settings(properties), directory=folder, direct_export=True)

    override = {}
    window = window_for(root)
    if window is not None:
        override["window"] = window  # also its screen, scene and view layer
    elif windows():
        raise ExportError("The model is not in a scene shown in a Blender window. Show its scene, then push again.")
    use_logger, counter = _sollumz_log_counter()
    windows_before, logs_before = len(windows()), _info_log_count()
    with bpy.context.temp_override(**override):
        layer = bpy.context.view_layer
        if layer.objects.get(root.name) is None:
            raise ExportError("The model is not in the current view layer. Show it, then push again.")
        selected = [obj for obj in layer.objects if obj.select_get()]
        active = layer.objects.active
        chosen = None
        try:
            for obj in selected:
                obj.select_set(False)
            chosen = _select_for_export(root)
            layer.objects.active = chosen
            try:
                if use_logger is not None and counter is not None:
                    with use_logger(counter):
                        result = bpy.ops.sollumz.export_assets("EXEC_DEFAULT", **arguments)
                else:
                    result = bpy.ops.sollumz.export_assets("EXEC_DEFAULT", **arguments)
            except (RuntimeError, TypeError, ValueError) as exc:
                raise ExportError(f"Sollumz could not export the model: {exc}") from exc
        finally:
            _restore_selection(layer, chosen, selected, active)
            _consume_updates(window)
    if "FINISHED" not in result:
        raise ExportError("Sollumz did not export the model. Its Info log has the details.")
    if counter is not None:
        return ExportResult(counter.problems > 0)
    return ExportResult(len(windows()) > windows_before or _info_log_count() > logs_before)


def _restore_selection(layer: Any, chosen: Any, selected: List[Any], active: Any) -> None:
    if chosen is not None:
        try:
            chosen.select_set(False)
        except (RuntimeError, ReferenceError):
            pass  # it left the view layer during the export
    for obj in selected:
        try:
            obj.select_set(True)
        except (RuntimeError, ReferenceError):
            pass  # removed or hidden meanwhile; nothing to restore
    try:
        layer.objects.active = active
    except (RuntimeError, ReferenceError):
        pass  # the previously active object is gone


def find_object(uid: Optional[int]) -> Optional[Any]:
    if uid is None:
        return None
    for obj in bpy.data.objects:
        if obj.session_uid == uid:
            return obj
    return None


class AutoPushWatcher:
    """Turns depsgraph updates of the pushed model into debounced pushes.

    The model is identified by its root's ``session_uid`` (stable while Blender runs, also across renames and
    undo). Only geometry and transform changes of objects whose topmost parent is the root, and changes of their
    meshes, count. Selecting objects (which the push does around the export) changes neither, so a push never
    triggers the next one.
    """

    def __init__(self) -> None:
        self.exporting = False
        self.root_uid: Optional[int] = None
        self._root: Any = None
        self._objects: Set[int] = set()
        self._meshes: Set[int] = set()
        self._stale = True

    def watch(self, root: Any) -> None:
        self.root_uid = root.session_uid
        self._root = root
        self._stale = True

    def forget(self) -> None:
        """Re-reads the hierarchy at the next update (after a push, an undo or a file load)."""
        self._root = None
        self._stale = True

    def clear(self) -> None:
        self.root_uid = None
        self.forget()

    def root(self) -> Optional[Any]:
        if self.root_uid is None:
            return None
        if self._root is not None:
            try:
                if self._root.session_uid == self.root_uid:
                    return self._root
            except ReferenceError:
                pass  # freed by an undo step or a file load; look it up again
        self._root = find_object(self.root_uid)
        return self._root

    def _rebuild(self, root: Any) -> None:
        self._objects, self._meshes = set(), set()
        for obj in [root, *root.children_recursive]:
            self._objects.add(obj.session_uid)
            if obj.type == "MESH" and obj.data is not None:
                self._meshes.add(obj.data.session_uid)
        self._stale = False

    def relevant(self, depsgraph: Any) -> bool:
        if self.root_uid is None or self.exporting:
            return False
        root = self.root()
        if root is None:
            return False
        if self._stale:
            self._rebuild(root)
        for update in depsgraph.updates:
            data = update.id
            original = getattr(data, "original", data)
            if isinstance(original, bpy.types.Object):
                if not (update.is_updated_geometry or update.is_updated_transform):
                    continue
                if original.session_uid in self._objects:
                    return True
                if top_parent(original).session_uid == self.root_uid:
                    self._stale = True  # a new or re-parented object joined the model
                    return True
            elif isinstance(original, bpy.types.Mesh) and original.session_uid in self._meshes:
                return True
        return False
