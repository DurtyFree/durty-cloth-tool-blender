# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2026 Schmid Software Solutions (https://schmid-software.de)
"""Everything that touches Blender: where files are kept, reading images, detecting paint strokes, exporting
with Sollumz and redrawing the panels."""

from __future__ import annotations

import hashlib
import pathlib
import socket
import sys
from typing import Any, Dict, Iterable, List, NamedTuple, Optional, Set, Tuple

import bpy

from . import link, pixels, settings
from .dct_link import protocol, tokens
from .strings import Msg, UserError, msg

# --------------------------------------------------------------------------------------------------
# Environment
# --------------------------------------------------------------------------------------------------


def data_dir(package: str) -> pathlib.Path:
    """The add-on's user folder (Blender keeps it across updates of the same installation). Holds the install
    id and the protected sign-in."""
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
    """Blender's own name of the object's mode, in Blender's language ("Edit Mode")."""
    try:
        name = obj.bl_rna.properties["mode"].enum_items[obj.mode].name
    except (KeyError, AttributeError):
        return obj.mode.replace("_", " ").title()
    try:
        return bpy.app.translations.pgettext_iface(name)
    except (AttributeError, TypeError, ValueError):
        return name


def auto_push_blocker(root: Any) -> Optional[Msg]:
    """Why an automatic push of ``root`` has to wait right now, or ``None``: a tool runs, or the view layer that
    holds the model is not in Object Mode (an export then would miss the newest edits)."""
    if modal_operator_running():
        return msg("model.wait.tool")
    window = window_for(root)
    layer = window.view_layer if window is not None else getattr(bpy.context, "view_layer", None)
    active = layer.objects.active if layer is not None else None
    if active is not None and active.mode != "OBJECT":
        return msg("model.wait.mode", mode=_mode_name(active))
    return None


# --------------------------------------------------------------------------------------------------
# Images
# --------------------------------------------------------------------------------------------------


def image_problem(image: Optional[Any], load: bool = True) -> Optional[Msg]:
    """Why an image cannot be used for the live preview, or ``None``. ``load=False`` (for drawing) skips loading
    the pixels."""
    if image is None:
        return msg("image.none")
    if image.source == "TILED":
        return msg("image.tiled")
    if image.source not in {"FILE", "GENERATED"}:
        return msg("image.source")
    if not load:
        return None
    try:
        len(image.pixels)  # loads the pixels when they are not in memory yet
    except (RuntimeError, ReferenceError):
        return msg("image.unreadable")
    if not image.has_data:
        return msg("image.not-loaded")
    if image.channels not in (1, 3, 4):
        return msg("image.channels")
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

    def problem(self) -> Optional[Msg]:
        image = self.image()
        if image is None:
            return msg("live.image-removed")
        if tuple(image.size) != (self.width, self.height) or image.channels != self.channels:
            return msg("live.image-changed")
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


# --------------------------------------------------------------------------------------------------
# Images and models linked to a cloth
# --------------------------------------------------------------------------------------------------

#: The custom properties that link an image or a Drawable Dictionary to its cloth in Durty Cloth Tool: the cloth's
#: id, the variation's id and (images only) the map the image is. Blender keeps them in the .blend file.
CLOTH_ID = "dct_cloth_id"
TEXTURE_ID = "dct_texture_id"
MAP = "dct_map"
#: On an image opened from Durty Cloth Tool: the SHA-256 of the pixels it was filled with (RGBA8, rows top to
#: bottom). The image is reused for the same map only while its pixels still are exactly those.
PIXELS = "dct_pixels"
#: On a Drawable Dictionary opened from (or added to) Durty Cloth Tool: the cloth's name there, which the panel shows
#: until the cloth itself is known (the model's own name is that of the project's data file).
CLOTH_NAME = "dct_cloth_name"
#: On a Drawable Dictionary opened from Durty Cloth Tool: the skeleton in it was lent by Durty Cloth Tool (the ped's
#: own, because the cloth is stored without one), so every push leaves it out again.
LENT_SKELETON = "dct_lent_skeleton"
#: Sollumz's settings for a model whose skeleton is lent: exported without it, as the cloth is stored.
LENT_SKELETON_EXPORT: Dict[str, Any] = {"exclude_skeleton": True}
#: And for importing it: its own skeleton, never an external one from the user's import settings.
LENT_SKELETON_IMPORT: Dict[str, Any] = {"dwd_import_external_skeleton": "NO"}


def stored_binding(data: Optional[Any]) -> Optional[Dict[str, str]]:
    """The cloth an image or object is linked to (``clothId``, ``textureId``), or ``None``."""
    if data is None:
        return None
    try:
        return link.binding_of(data.get(CLOTH_ID), data.get(TEXTURE_ID))
    except (AttributeError, ReferenceError, TypeError):
        return None


def stored_map(image: Optional[Any]) -> Optional[str]:
    """The map a linked image is (``diffuse``, ``normal`` or ``specular``), or ``None``."""
    try:
        value = image.get(MAP) if image is not None else None
    except (AttributeError, ReferenceError):
        return None
    return value if value in protocol.LIVE_TARGETS else None


def store_binding(data: Any, binding: Dict[str, str], target: Optional[str] = None, name: Optional[str] = None) -> None:
    """Links an image or a Drawable Dictionary to its cloth; ``name`` is the cloth's name in Durty Cloth Tool."""
    data[CLOTH_ID] = binding["clothId"]
    data[TEXTURE_ID] = binding["textureId"]
    if target is not None:
        data[MAP] = target
    if name:
        data[CLOTH_NAME] = name
    elif CLOTH_NAME in data:
        del data[CLOTH_NAME]


def clear_binding(data: Any) -> None:
    for key in (CLOTH_ID, TEXTURE_ID, MAP, PIXELS, CLOTH_NAME):
        if key in data:
            del data[key]


def stored_cloth_name(data: Optional[Any]) -> Optional[str]:
    """The cloth's name Durty Cloth Tool gave a linked Drawable Dictionary, or ``None``."""
    try:
        value = data.get(CLOTH_NAME) if data is not None else None
    except (AttributeError, ReferenceError):
        return None
    return value if isinstance(value, str) and value else None


def push_settings(root: Any) -> Optional[Dict[str, Any]]:
    """The Sollumz export settings a push of ``root`` needs on top of the user's: a model whose skeleton Durty Cloth
    Tool lent goes back without it."""
    try:
        return dict(LENT_SKELETON_EXPORT) if root.get(LENT_SKELETON) else None
    except (AttributeError, ReferenceError):
        return None


def push_undo(message: str) -> None:
    """An undo step after the add-on changed the file by itself (an image or model opened and linked), so undo and
    redo keep the link with what it belongs to."""
    window = getattr(bpy.context, "window", None) or first_window()
    try:
        with bpy.context.temp_override(**({"window": window} if window is not None else {})):
            bpy.ops.ed.undo_push(message=message)
    except (RuntimeError, TypeError):
        pass  # no undo stack (background mode); nothing to keep in step with


def _rgba_digest(rows_top_down: Any) -> str:
    return hashlib.sha256(memoryview(rows_top_down).cast("B")).hexdigest()


def _image_digest(image: Any) -> Optional[str]:
    """The digest of an image's pixels as :data:`PIXELS` records them, or ``None`` for an image that cannot hold
    exactly those (float or not RGBA)."""
    import numpy as np

    if image.is_float or image.channels != 4:
        return None
    width, height = tuple(image.size)
    values = np.empty(width * height * 4, np.float32)
    image.pixels.foreach_get(values)
    rgba = np.floor(values * np.float32(255) + np.float32(0.5)).astype(np.uint8).reshape(height, width, 4)[::-1]
    return _rgba_digest(np.ascontiguousarray(rgba))


def _reusable(image: Any) -> bool:
    """The image still holds exactly what was opened into it: not changed, saved over, repacked or appended."""
    try:
        recorded = image.get(PIXELS)
        if not recorded or image.is_dirty or image.channels != 4 or image_problem(image, load=False):
            return False
        return _image_digest(image) == recorded
    except (RuntimeError, ReferenceError):
        return False


def _linked_image(binding: Dict[str, str], target: str) -> Optional[Any]:
    for image in bpy.data.images:
        if stored_map(image) == target and link.same_binding(stored_binding(image), binding):
            return image
    return None


def open_texture_image(document: "link.TextureDocument") -> Tuple[Any, bool]:
    """The image for a cloth's map from Durty Cloth Tool, filled with its pixels and linked to the cloth, and
    whether it was made now.

    The image linked to the same cloth, variation and map is reused only while its pixels are exactly what was
    opened into it last time (:data:`PIXELS`); otherwise (and the first time) a new image is made, named after the
    cloth, variation and map, so paint, a saved or repacked file and an appended image are never overwritten.
    Normal and specular maps are set to Non-Color."""
    import numpy as np

    width, height = document.width, document.height
    problem = settings.check_stream_size(width, height)
    if problem is not None:
        raise UserError(problem)
    rgba = np.frombuffer(document.pixels, dtype=np.uint8)
    if rgba.size != width * height * 4:
        raise ValueError("the texture has the wrong number of pixels")
    image = _linked_image(document.binding, document.target)
    created = image is None or not _reusable(image)
    if created:
        image = bpy.data.images.new(document.name, width, height, alpha=True)
    # The colour space first: assigning it reloads a packed image from its packed pixels (at their old size).
    space = "sRGB" if document.target == "diffuse" else "Non-Color"
    if image.colorspace_settings.name != space:
        image.colorspace_settings.name = space
    if tuple(image.size) != (width, height):
        image.scale(width, height)
    rows = rgba.reshape(height, width, 4)[::-1]  # Blender's rows start at the bottom
    image.pixels.foreach_set((rows.astype(np.float32) / np.float32(255)).reshape(-1))
    store_binding(image, document.binding, document.target)
    image[PIXELS] = _rgba_digest(rgba)
    return image, created


def remove_image(image: Any) -> None:
    try:
        bpy.data.images.remove(image)
    except (ReferenceError, RuntimeError):
        pass  # removed meanwhile


def keep_image(image: Any) -> None:
    """Packs an image the add-on made or packed before into the .blend file, so it keeps its pixels (and its link)
    when the file is saved and opened again; painting on it later marks it changed as usual. An image saved as its
    own file stays that file: Blender asks to save its changes."""
    try:
        if image.source == "GENERATED" or image.packed_file is not None:
            image.pack()
    except ReferenceError:
        pass  # removed meanwhile


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
# A Drawable Dictionary that stands where a prop hangs (a ped prop anchor) and whose model is exported relative to it.
ANCHORED_ROOT = "dct_prop"
_VERSION_CACHE: Dict[Tuple[str, int], Optional[str]] = {}


class ExportError(UserError):
    """The model could not be exported; the message is shown to the user."""


def _export_error(key: str, **fields: Any) -> ExportError:
    return ExportError(msg(key, **fields))


class ExportResult(NamedTuple):
    #: Sollumz logged warnings or errors during the export.
    warnings: bool
    #: Sollumz logged errors: part of the model may be missing from the export (``False`` when this Sollumz cannot
    #: tell; check the exported file then).
    errors: bool = False


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


#: Sollumz's export operator properties this add-on needs (Sollumz 2.8.0 and later have them all).
REQUIRED_PROPERTIES = frozenset({"directory", "direct_export", "use_custom_settings"})


def sollumz_status() -> Tuple[bool, Msg]:
    """Whether models can be pushed, and a line for the panel."""
    properties = sollumz_operator_properties()
    if properties is None:
        return False, msg("sollumz.missing", version=settings.SOLLUMZ_MINIMUM)
    if not REQUIRED_PROPERTIES <= properties:
        return False, msg("sollumz.too-old", version=settings.SOLLUMZ_MINIMUM)
    version = sollumz_version()
    return True, msg("sollumz.ready", version=version) if version else msg("sollumz.ready-unknown")


#: Sollumz's import operator properties the add-on needs to import a model DCT sent.
REQUIRED_IMPORT_PROPERTIES = frozenset({"directory", "files"})
_NOT_COPIED_IMPORT = {"rna_type", "directory", "files", "filter_glob", "use_custom_settings", "import_as_asset",
                      "textures_mode", "textures_extract_custom_directory"}


def sollumz_import_properties() -> Optional[Set[str]]:
    """The properties of Sollumz's import operator, or ``None`` when Sollumz does not have it (or is not enabled)."""
    try:
        rna = bpy.ops.sollumz.import_assets.get_rna_type()
    except (AttributeError, KeyError, RuntimeError):
        return None
    return {prop.identifier for prop in rna.properties}


def model_open_problem() -> Optional[Msg]:
    """Why a model from Durty Cloth Tool cannot be opened (Sollumz missing or too old), or ``None``. Opening needs
    Sollumz's import, and pushing the model back needs its export."""
    ready, status = sollumz_status()
    if not ready:
        return status
    properties = sollumz_import_properties()
    if properties is None or not REQUIRED_IMPORT_PROPERTIES <= properties:
        return msg("sollumz.too-old", version=settings.SOLLUMZ_MINIMUM)
    return None


def _import_settings(properties: Set[str], overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """The user's Sollumz import settings, with the textures packed into the .blend file (the imported files are
    temporary) and ``overrides`` on top (those this Sollumz has)."""
    if not {"use_custom_settings", "textures_mode"} <= properties:
        return {}  # an older Sollumz imports with its own settings; the textures are packed afterwards
    values: Dict[str, Any] = {}
    addon = _sollumz_addon()
    prefs = getattr(getattr(addon, "preferences", None), "import_settings", None) if addon is not None else None
    if prefs is not None:
        for prop in prefs.bl_rna.properties:
            name = prop.identifier
            if name in properties and name not in _NOT_COPIED_IMPORT and not prop.is_readonly:
                values[name] = getattr(prefs, name)
    values.update({k: v for k, v in (overrides or {}).items() if k in properties})
    values.update(use_custom_settings=True, textures_mode="PACK")
    return values


def import_with_sollumz(folder: pathlib.Path, model_file: str,
                        overrides: Optional[Dict[str, Any]] = None) -> Tuple[Any, bool]:
    """Imports ``folder/model_file`` (CodeWalker XML of a Drawable Dictionary, its textures in the folder named after
    it) with Sollumz into the active collection of the first window. Returns the new Drawable Dictionary and whether
    Sollumz logged warnings. Every image the import read from ``folder`` is packed into the .blend file, so the files
    can be deleted afterwards.

    Sollumz finishes even when an asset failed; its log tells. Errors there (or no Drawable Dictionary) raise
    :class:`ExportError`, so a partial import is never linked to the cloth."""
    problem = model_open_problem()
    if problem is not None:
        raise ExportError(problem)
    properties = sollumz_import_properties() or set()
    arguments = dict(_import_settings(properties, overrides), directory=str(folder), files=[{"name": model_file}])
    window = getattr(bpy.context, "window", None) or first_window()
    override: Dict[str, Any] = {"window": window} if window is not None else {}
    before = {obj.session_uid for obj in bpy.data.objects}
    images_before = {image.session_uid for image in bpy.data.images}
    use_logger, counter = _sollumz_log_counter()
    windows_before, logs_before = len(windows()), _info_log_count()
    with bpy.context.temp_override(**override):
        layer = bpy.context.view_layer
        active = layer.objects.active if layer is not None else None
        if active is not None and active.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")  # Sollumz imports in Object Mode
        try:
            if use_logger is not None and counter is not None:
                with use_logger(counter):
                    result = bpy.ops.sollumz.import_assets("EXEC_DEFAULT", **arguments)
            else:
                result = bpy.ops.sollumz.import_assets("EXEC_DEFAULT", **arguments)
        except (RuntimeError, TypeError, ValueError) as exc:
            raise _export_error("open.import-failed", detail=str(exc)) from exc
        if "FINISHED" not in result:
            raise _export_error("open.import-failed", detail=", ".join(sorted(result)))
        if counter is not None and counter.errors:
            raise _export_error("open.import-errors")
        new = [obj for obj in bpy.data.objects if obj.session_uid not in before]
        roots = [obj for obj in new if obj.parent is None and getattr(obj, "sollum_type", None) == DRAWABLE_DICTIONARY]
        if not roots:
            raise _export_error("open.no-dictionary")
        root = roots[0]
        _pack_imported_images(folder, images_before)
        for obj in layer.objects if layer is not None else ():
            if obj.select_get():
                obj.select_set(False)
        try:
            root.select_set(True)
            layer.objects.active = root
        except (RuntimeError, AttributeError):
            pass  # not in the view layer that is shown; it is still linked to its cloth
    if counter is not None:
        return root, counter.problems > 0
    return root, len(windows()) > windows_before or _info_log_count() > logs_before


def drawable_dictionaries() -> List[Any]:
    """Every Drawable Dictionary (a Sollumz root object) of the file."""
    return [obj for obj in bpy.data.objects
            if obj.parent is None and getattr(obj, "sollum_type", None) == DRAWABLE_DICTIONARY]


def others_linked_alike(root: Any) -> List[Any]:
    """Other Drawable Dictionaries linked to the same cloth as ``root`` (a copy made with Duplicate copies the
    link): each cloth takes one model, so the user decides which one stays linked."""
    binding = stored_binding(root)
    if binding is None:
        return []
    return [obj for obj in drawable_dictionaries()
            if obj.session_uid != root.session_uid and link.same_binding(stored_binding(obj), binding)]


def selected_dictionary(context: Any) -> Optional[Any]:
    """The Drawable Dictionary the active object belongs to, or ``None``."""
    obj = getattr(context, "active_object", None)
    if obj is None:
        return None
    root = top_parent(obj)
    return root if getattr(root, "sollum_type", None) == DRAWABLE_DICTIONARY else None


def _pack_imported_images(folder: pathlib.Path, images_before: Set[int]) -> None:
    base = folder.resolve()
    for image in bpy.data.images:
        if image.session_uid in images_before or image.packed_file is not None or image.source != "FILE":
            continue
        try:
            path = pathlib.Path(bpy.path.abspath(image.filepath)).resolve()
        except (OSError, ValueError):
            continue
        if base in path.parents and path.is_file():
            try:
                image.pack()
            except RuntimeError:
                continue  # not loadable; Sollumz has reported it


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
        raise _export_error("model.select")
    if len(roots) > 1:
        raise _export_error("model.one-root")
    root = roots[0]
    kind = getattr(root, "sollum_type", None)
    if kind == DRAWABLE_DICTIONARY:
        return root
    if kind == DRAWABLE:
        raise _export_error("model.needs-dictionary")
    raise _export_error("model.not-sollumz")


def _export_settings(properties: Set[str], overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """The operator arguments for this Sollumz version: the user's Sollumz export settings (for example Exclude
    Skeleton) with the forced settings and ``overrides`` on top."""
    values: Dict[str, Any] = {}
    addon = _sollumz_addon()
    prefs = getattr(getattr(addon, "preferences", None), "export_settings", None) if addon is not None else None
    if prefs is not None:
        for prop in prefs.bl_rna.properties:
            name = prop.identifier
            if name not in _NOT_COPIED and not prop.is_readonly:
                values[name] = getattr(prefs, name)
    values.update(FORCED_SETTINGS)
    values.update(overrides or {})
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
    raise _export_error("model.unhide")


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
                self.errors = 0

            def do_log(self, msg: str, level: str) -> None:
                if level in ("WARNING", "ERROR"):
                    self.problems += 1
                if level == "ERROR":
                    self.errors += 1

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


def _stand_at_origin(root: Any, layer: Any) -> Optional[Any]:
    """Moves an anchored prop's Drawable Dictionary to the origin for the export and returns where it stood (``None``
    when it is not one or already there). Sollumz takes a model relative to its dictionary only when its own Apply
    Parent Transforms preference is off (it reads the preference, not the export's settings), so at the origin the
    prop leaves relative to its anchor whatever that preference says."""
    if not root.get(ANCHORED_ROOT) or root.matrix_world.is_identity:
        return None
    placed = root.matrix_world.copy()
    root.matrix_world = type(placed).Identity(4)
    layer.update()
    return placed


def export_with_sollumz(root: Any, folder: str, overrides: Optional[Dict[str, Any]] = None) -> ExportResult:
    """Exports ``root`` with Sollumz into ``folder``, in the window whose view layer holds it. Selects only what
    the export needs and restores the selection afterwards. Reports whether Sollumz logged warnings or errors.
    ``overrides`` are export settings that win over the user's (those this Sollumz has)."""
    ready, problem = sollumz_status()
    if not ready:
        raise ExportError(problem)
    properties = sollumz_operator_properties() or set()
    arguments = dict(_export_settings(properties, overrides), directory=folder, direct_export=True)

    override = {}
    window = window_for(root)
    if window is not None:
        override["window"] = window  # also its screen, scene and view layer
    elif windows():
        raise _export_error("model.not-shown")
    use_logger, counter = _sollumz_log_counter()
    windows_before, logs_before = len(windows()), _info_log_count()
    with bpy.context.temp_override(**override):
        layer = bpy.context.view_layer
        if layer.objects.get(root.name) is None:
            raise _export_error("model.not-in-layer")
        selected = [obj for obj in layer.objects if obj.select_get()]
        active = layer.objects.active
        chosen = None
        placed = _stand_at_origin(root, layer)
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
                raise _export_error("model.export-failed", detail=str(exc)) from exc
        finally:
            _restore_selection(layer, chosen, selected, active)
            if placed is not None:
                root.matrix_world = placed
                layer.update()
            _consume_updates(window)
    if "FINISHED" not in result:
        raise _export_error("model.not-exported")
    if counter is not None:
        return ExportResult(counter.problems > 0, counter.errors > 0)
    return ExportResult(len(windows()) > windows_before or _info_log_count() > logs_before)


def sollumz_module(suffix: str) -> Optional[Any]:
    """A module of the enabled Sollumz (``suffix`` such as ``ydr.shader_materials``), or ``None``."""
    addon = _sollumz_addon()
    if addon is None:
        return None
    return sys.modules.get(f"{addon.module}.{suffix}")


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
