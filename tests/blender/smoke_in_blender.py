# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2026 Schmid Software Solutions (https://schmid-software.de)
"""Headless smoke test that runs inside Blender. Start it through ``tools/blender_smoke.py``, which sets up a
throw-away Blender user folder; by hand:

    set BLENDER_USER_RESOURCES=<empty temporary folder>
    blender --background --factory-startup --online-mode --python tests/blender/smoke_in_blender.py
        -- --zip dist/durty_cloth_tool_link-0.1.0.zip --report smoke.json
        [--sollumz <Sollumz extension folder> --sollumz-site <folder holding Sollumz's szio package>]

(one command line).

It installs the built extension into a temporary local repository, enables it, and drives it through its
operators against a fake Durty Cloth Tool and a fake gta.clothing on 127.0.0.1: sign-in approved in DCT, texture
streaming (checking the vertical flip and dirty rectangles), saving and discarding, a model push
through Sollumz's export operator (a stand-in by default, the real Sollumz with ``--sollumz``), an automatic
push after a mesh change, a skinned model whose export switches the armature to its rest pose and back, a texture
and a model Durty Cloth Tool sends (the model imported with Sollumz's import operator, with the real Sollumz a round
trip of its own export), the garment fitting tools on a synthetic body and garments (``garment_smoke.py``), adding
a garment to the open project, Custom Ped on a synthetic mannequin (``ped_smoke.py``), the update repository, sign-out and disabling the add-on. Blender's timers do not run
in background mode, so the script calls the add-on's timer function itself, and evaluates the view layer where
Blender's main loop would.
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import shutil
import sys
import tempfile
import time
import traceback

import bpy

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
from tests.blender import garment_smoke, ped_smoke, sollumz_stub  # noqa: E402 - needs the repository on the path
from tests.blender.sollumz_stub import STUB  # noqa: E402

RESULTS = []


class SmokeFailure(Exception):
    pass


def check(name, condition, detail=""):
    RESULTS.append({"check": name, "ok": bool(condition), "detail": str(detail)})
    print(("PASS " if condition else "FAIL ") + name + (f" ({detail})" if detail and not condition else ""))
    if not condition:
        raise SmokeFailure(name)


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", required=True)
    parser.add_argument("--report", required=True)
    parser.add_argument("--sollumz")
    parser.add_argument("--sollumz-site")
    return parser.parse_args(argv)


def install(zip_path):
    user = pathlib.Path(bpy.utils.resource_path("USER")).resolve()
    expected = pathlib.Path(os.environ.get("BLENDER_USER_RESOURCES", "")).resolve()
    check("Blender uses the throw-away user folder", os.environ.get("BLENDER_USER_RESOURCES") and user == expected,
          f"{user} vs {expected}")
    repo_dir = tempfile.mkdtemp(prefix="dct_smoke_repo_", dir=str(expected))  # removed with the user folder
    bpy.ops.preferences.extension_repo_add(name="dct_smoke", type="LOCAL", use_custom_directory=True,
                                           custom_directory=repo_dir)
    repo = next(r for r in bpy.context.preferences.extensions.repos if r.name == "dct_smoke")
    result = bpy.ops.extensions.package_install_files(filepath=zip_path, repo=repo.module, enable_on_install=True)
    package = f"bl_ext.{repo.module}.durty_cloth_tool_link"
    check("the built extension installs and enables", "FINISHED" in result and package in bpy.context.preferences.addons,
          result)
    return repo, repo_dir, package


def refused(operator, needle):
    """Background Blender raises the operator's error report as RuntimeError."""
    try:
        result = operator()
    except RuntimeError as exc:
        return needle in str(exc)
    return "CANCELLED" in result


def pump(addon, until, timeout=20.0, what="condition"):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        addon.tick()
        if until():
            return
        time.sleep(0.005)
    raise SmokeFailure(f"timed out waiting for {what}")


# ---- Sollumz ------------------------------------------------------------------------------------------

def install_real_sollumz(repo, repo_dir, source, site):
    target = pathlib.Path(repo_dir) / "sollumz"
    shutil.copytree(source, target, ignore=shutil.ignore_patterns("__pycache__"))
    module = f"bl_ext.{repo.module}.sollumz"
    data = pathlib.Path(bpy.utils.extension_path_user(module, create=True))
    packages = data / "lib" / f"python{sys.version_info[0]}.{sys.version_info[1]}" / "site-packages"
    packages.mkdir(parents=True, exist_ok=True)
    for entry in pathlib.Path(site).iterdir():
        if entry.name.startswith("szio"):
            copy = shutil.copytree if entry.is_dir() else shutil.copy2
            copy(entry, packages / entry.name)
    bpy.ops.extensions.repo_refresh_all()
    bpy.ops.preferences.addon_enable(module=module)
    check("the real Sollumz is enabled", module in bpy.context.preferences.addons)


def real_sollumz_scene():
    bpy.ops.mesh.primitive_plane_add()
    part = bpy.context.active_object
    part.name = "smoke_part"
    bpy.ops.object.select_all(action="DESELECT")
    part.select_set(True)
    bpy.context.view_layer.objects.active = part
    bpy.ops.sollumz.converttodrawable()
    drawable = part.parent
    # A model without a Sollumz shader is skipped by the export; give it the ped shader clothing uses.
    shaders = next(m for name, m in sys.modules.items() if name.endswith("sollumz.ydr.shader_materials"))
    names = [getattr(s, "value", s) for s in shaders.shadermats]
    index = names.index("ped.sps") if "ped.sps" in names else 0
    bpy.ops.object.select_all(action="DESELECT")
    part.select_set(True)
    bpy.context.view_layer.objects.active = part
    bpy.ops.sollumz.createshadermaterial(shader_index=index)
    bpy.ops.object.select_all(action="DESELECT")
    bpy.ops.sollumz.createdrawabledict()
    root = next(o for o in bpy.data.objects if getattr(o, "sollum_type", "") == "sollumz_drawable_dictionary")
    root.name = "smoke_ydd"
    drawable.parent = root
    bpy.ops.object.select_all(action="DESELECT")
    part.select_set(True)
    bpy.context.view_layer.objects.active = part
    return root, part


def skinned_model(real):
    """A Drawable Dictionary whose root is an armature, with a mesh skinned to one bone (as ped clothing is)."""
    scene = bpy.context.scene
    armature = bpy.data.armatures.new("smoke_skeleton")
    root = bpy.data.objects.new("smoke_skinned_ydd", armature)
    root.sollum_type = "sollumz_drawable_dictionary"
    scene.collection.objects.link(root)
    bpy.ops.object.select_all(action="DESELECT")
    root.select_set(True)
    bpy.context.view_layer.objects.active = root
    bpy.ops.object.mode_set(mode="EDIT")
    bone = armature.edit_bones.new("SKEL_ROOT")
    bone.head, bone.tail = (0.0, 0.0, 0.0), (0.0, 0.0, 0.5)
    bpy.ops.object.mode_set(mode="OBJECT")
    if real:
        bpy.ops.object.select_all(action="DESELECT")
        bpy.ops.mesh.primitive_plane_add(location=(3.0, 0.0, 0.0))
        part = bpy.context.active_object
        bpy.ops.sollumz.converttodrawable()
        drawable = part.parent
        shaders = next(m for name, m in sys.modules.items() if name.endswith("sollumz.ydr.shader_materials"))
        names = [getattr(s, "value", s) for s in shaders.shadermats]
        bpy.ops.object.select_all(action="DESELECT")
        part.select_set(True)
        bpy.context.view_layer.objects.active = part
        bpy.ops.sollumz.createshadermaterial(shader_index=names.index("ped.sps") if "ped.sps" in names else 0)
    else:
        drawable = bpy.data.objects.new("smoke_skinned_drawable", None)
        drawable.sollum_type = "sollumz_drawable"
        mesh = bpy.data.meshes.new("smoke_skinned_mesh")
        mesh.from_pydata([(3, 0, 0), (4, 0, 0), (3, 1, 0)], [], [(0, 1, 2)])
        part = bpy.data.objects.new("smoke_skinned_part", mesh)
        part.sollum_type = "sollumz_drawable_model"
        part.parent = drawable
        for obj in (drawable, part):
            scene.collection.objects.link(obj)
    drawable.parent = root
    group = part.vertex_groups.new(name="SKEL_ROOT")
    group.add(list(range(len(part.data.vertices))), 1.0, "REPLACE")
    part.modifiers.new("Armature", "ARMATURE").object = root
    bpy.context.view_layer.update()
    return root, part


def idle(addon, seconds):
    """Runs the timer for a while, evaluating the view layer as Blender's main loop does between events."""
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        bpy.context.view_layer.update()
        addon.tick()
        time.sleep(0.02)


# ---- drawing the panels without a window ------------------------------------------------------------------


class FakeLayout:
    """Records what a panel draws and checks it against Blender: icons, operators and properties must exist.
    Background Blender has no regions, so this is how the smoke runs the draw code."""

    icons = None

    def __init__(self, log):
        self.log = log
        self.enabled = True
        self.active = True
        self.alert = False
        self.scale_y = 1.0
        self.alignment = "EXPAND"
        if FakeLayout.icons is None:
            items = bpy.types.UILayout.bl_rna.functions["label"].parameters["icon"].enum_items
            FakeLayout.icons = {item.identifier for item in items}

    def _icon(self, icon):
        if icon not in FakeLayout.icons:
            raise AssertionError(f"unknown icon {icon}")

    def column(self, **_kw):
        return FakeLayout(self.log)

    row = box = split = column

    def separator(self, **_kw):
        pass

    def template_icon(self, icon_value=0, scale=1.0, **_kw):
        if not isinstance(icon_value, int) or icon_value <= 0:
            raise AssertionError(f"template_icon needs an icon id, got {icon_value!r}")
        self.log.append(("template_icon", scale))

    def menu(self, menu, text="", icon="NONE", **_kw):
        self._icon(icon)
        cls = getattr(bpy.types, menu, None)
        if cls is None:
            raise AssertionError(f"unknown menu {menu}")
        cls.draw(type("M", (), {"layout": FakeLayout(self.log)})(), bpy.context)  # its items are checked too
        self.log.append(("menu", menu))

    def panel(self, idname, default_closed=False, **_kw):
        if not isinstance(idname, str) or not idname:
            raise AssertionError("a layout panel needs an id")
        return FakeLayout(self.log), FakeLayout(self.log)  # drawn open, so its content is checked too

    def panel_prop(self, data, name, **_kw):
        if name not in data.bl_rna.properties:
            raise AssertionError(f"{type(data).__name__} has no property {name}")
        return FakeLayout(self.log), FakeLayout(self.log)  # drawn open, so its content is checked too

    def grid_flow(self, **_kw):
        return FakeLayout(self.log)

    def label(self, text="", icon="NONE", icon_value=0, **_kw):
        self._icon(icon)
        self.log.append(("label", text))

    def prop(self, data, name, icon="NONE", **_kw):
        self._icon(icon)
        if name not in data.bl_rna.properties:
            raise AssertionError(f"{type(data).__name__} has no property {name}")
        getattr(data, name)  # runs getters, as drawing does
        self.log.append(("prop", name))

    def prop_enum(self, data, name, value, icon="NONE", **_kw):
        self._icon(icon)
        items = {item.identifier for item in data.bl_rna.properties[name].enum_items}
        if value not in items:
            raise AssertionError(f"{name} has no item {value}")
        self.log.append(("prop_enum", f"{name}={value}"))

    def popover(self, panel, text="", icon="NONE", **_kw):
        self._icon(icon)
        if not hasattr(bpy.types, panel):
            raise AssertionError(f"unknown panel {panel}")
        self.log.append(("popover", text))

    def progress(self, factor=0.0, text="", **_kw):
        if not 0.0 <= factor <= 1.0:
            raise AssertionError(f"progress {factor} outside 0 to 1")
        self.log.append(("progress", text))

    def operator(self, idname, text=None, icon="NONE", **_kw):
        if text is not None and not isinstance(text, str):
            raise AssertionError(f"{idname}: text must be a string")
        self._icon(icon)
        module, name = idname.split(".")
        rna = getattr(getattr(bpy.ops, module), name).get_rna_type()  # KeyError for an unknown operator
        self.log.append(("operator", idname))
        return FakeOperatorProperties(idname, {p.identifier for p in rna.properties})


class FakeOperatorProperties:
    def __init__(self, idname, names):
        object.__setattr__(self, "_idname", idname)
        object.__setattr__(self, "_names", names)

    def __setattr__(self, name, value):
        if name not in self._names:
            raise AssertionError(f"{self._idname} has no property {name}")


class PreferencesProxy:
    """The add-on preferences with a fake layout (their own ``layout`` is read-only outside drawing)."""

    def __init__(self, prefs, layout):
        object.__setattr__(self, "_prefs", prefs)
        object.__setattr__(self, "layout", layout)

    def __getattr__(self, name):
        return getattr(self._prefs, name)


def draw_everything(package, state, label):
    ui = sys.modules[package + ".ui"]
    garment_ui = sys.modules[package + ".ui_garment"]
    ped_ui = sys.modules[package + ".ui_ped"]
    log = []
    panels = (ui.DCTLINK_PT_main, ui.DCTLINK_PT_details, ui.DCTLINK_PT_setup, ui.DCTLINK_PT_linked,
              ui.DCTLINK_PT_live, ui.DCTLINK_PT_model, garment_ui.DCTLINK_PT_garment, ped_ui.DCTLINK_PT_ped,
              ui.DCTLINK_PT_settings)
    for panel in panels:
        if panel.poll(bpy.context) if hasattr(panel, "poll") else True:
            instance = type("P", (), {"layout": FakeLayout(log)})()
            for method in ("draw_header", "draw_header_preset", "draw"):
                if hasattr(panel, method):
                    getattr(panel, method)(instance, bpy.context)
    prefs = state.preferences()
    type(prefs).draw(PreferencesProxy(prefs, FakeLayout(log)), bpy.context)
    check(f"every panel draws ({label})", any(entry[0] == "operator" for entry in log), log[:5])
    return log


# ---- the smoke --------------------------------------------------------------------------------------------


def run(args):
    print("Blender", bpy.app.version_string, "Python", sys.version.split()[0])
    repo, repo_dir, package = install(args.zip)
    addon = sys.modules[package + ".addon"]
    state = sys.modules[package + ".state"]
    protocol = sys.modules[package + ".dct_link.protocol"]
    preferences = sys.modules[package + ".preferences"]
    check("the link timer is registered", bpy.app.timers.is_registered(addon.tick))
    ctrl = state.get()

    from tests.support.fake_dct import FakeDct
    from tests.support.fake_link_api import FakeLinkApi

    dct = FakeDct(protocol=protocol)
    api = FakeLinkApi()
    dct.on_assist = api.approve
    ctrl.port_override = dct.port
    ctrl.auth_base_url = api.base_url
    try:
        smoke(args, repo, repo_dir, package, addon, state, preferences, ctrl, dct, api)
    finally:
        dct.stop()
        api.stop()
        if dct.errors:
            raise dct.errors[0]


def stream_image(addon, ctrl, dct, image, target="diffuse"):
    """Starts streaming ``image`` through the operator and waits for the first frame."""
    scene = bpy.context.scene
    scene.dct_link.image = image
    scene.dct_link.target = target
    frames = len(dct.frames)
    check(f"Start Live Preview runs ({image.name})", "FINISHED" in bpy.ops.dct_link.live_start())
    pump(addon, lambda: len(dct.frames) > frames and ctrl.stream.live_state == "attached", what="the first frame")
    frame = dct.frames[frames]
    return frame, dct.connections_ready[-1].leases[frame[0]]


def open_from_dct(args, addon, state, package, ctrl, dct, scene, rng):
    """Edit in connected app: textures and models Durty Cloth Tool sends, through the add-on's Blender side."""
    import numpy as np
    from tests.support.fake_dct import BINDING

    host = sys.modules[package + ".host"]
    link = sys.modules[package + ".link"]
    images_before = len(bpy.data.images)
    rgba = rng.integers(0, 256, size=(32, 64, 4), dtype=np.uint8)
    request_id = dct.open_texture(rgba.tobytes(), 64, 32, target="normal", name="jbib_normal_003")
    pump(addon, lambda: dct.host_result(request_id) is not None and ctrl.stream.live_state == "attached",
         what="the texture opened from DCT")
    check("DCT hears ok for the texture it sent", dct.host_result(request_id)["ok"] is True, dct.host_result(request_id))
    opened = scene.dct_link.image
    check("the texture became an image named after the cloth, variation and map, linked to it",
          opened is not None and opened.name == "jbib_003_u A Normal" and host.stored_map(opened) == "normal"
          and link.same_binding(host.stored_binding(opened), BINDING), opened and dict(opened.items()))
    check("a normal map opens as Non-Color", opened.colorspace_settings.is_data)
    live_open = [m for m in dct.received if m.get("type") == "live.open"][-1]
    lease = list(dct.connections_ready[-1].leases.values())[-1]
    check("the live preview is bound to the cloth DCT sent and shows its pixels unchanged",
          live_open["binding"] == BINDING and live_open["target"] == "normal"
          and bytes(lease["canvas"]) == rgba.tobytes())
    pump(addon, lambda: opened.packed_file is not None, what="the opened image to be kept with the file")
    log = draw_everything(package, state, "opened texture")
    check("the linked image offers Unlink", ("operator", "dct_link.unlink_image") in log)
    check("Stop Live Preview runs (opened texture)", "FINISHED" in bpy.ops.dct_link.live_stop())
    pump(addon, lambda: not dct.connections_ready[-1].leases, what="the opened live texture to close")

    # Start Live Preview sends the image's stored binding, whatever DCT has selected now.
    dct.broadcast({"type": "event.selection", "id": "smoke-sel", "focused": None})
    pump(addon, lambda: ctrl.focused is None, what="the empty selection")
    frames = len(dct.frames)
    check("Start Live Preview runs for the linked image without a selection", "FINISHED" in bpy.ops.dct_link.live_start())
    pump(addon, lambda: len(dct.frames) > frames, what="the linked image's frame")
    live_open = [m for m in dct.received if m.get("type") == "live.open"][-1]
    check("a linked image always goes to its own cloth and map",
          live_open["binding"] == BINDING and live_open["target"] == "normal", live_open)
    bpy.ops.dct_link.live_stop()
    pump(addon, lambda: not dct.connections_ready[-1].leases, what="the linked live texture to close")
    dct.broadcast({"type": "event.selection", "id": "smoke-sel2", "focused": {
        "clothId": BINDING["clothId"], "name": "jbib_003_u", "selectedTextureId": BINDING["textureId"],
        "textures": [{"textureId": BINDING["textureId"], "name": "jbib_diff_003_a_uni"}],
        "targets": ["diffuse", "normal", "specular"]}})
    pump(addon, lambda: ctrl.focused is not None, what="the selection")

    # The same map again reuses the image (nothing changed in it); a busy live preview refuses the next one.
    request_id = dct.open_texture(rgba[::-1].copy().tobytes(), 64, 32, target="normal", name="jbib_normal_003")
    pump(addon, lambda: dct.host_result(request_id) is not None and ctrl.stream.live_state == "attached",
         what="the texture opened again")
    check("opening the same map again reuses its image", len(bpy.data.images) == images_before + 1
          and scene.dct_link.image == opened)
    busy = dct.open_texture(rgba.tobytes(), 64, 32, target="diffuse")
    pump(addon, lambda: dct.host_result(busy) is not None, what="the busy answer")
    check("a texture sent during a live preview is refused as busy", dct.host_result(busy).get("code") == "busy")
    bpy.ops.dct_link.live_stop()
    pump(addon, lambda: not dct.connections_ready[-1].leases, what="the live texture to close")
    pump(addon, lambda: not opened.is_dirty, what="the image to be kept with the file again")

    # Reopen a map at another size: the packed image is scaled and filled, and stays usable for the next open.
    smaller = rng.integers(0, 256, size=(16, 32, 4), dtype=np.uint8)
    request_id = dct.open_texture(smaller.tobytes(), 32, 16, target="normal", name="jbib_normal_003")
    pump(addon, lambda: dct.host_result(request_id) is not None, what="the answer at another size")
    check("a map reopened at another size is accepted", dct.host_result(request_id)["ok"] is True,
          (dct.host_result(request_id), ctrl.open_notice))
    pump(addon, lambda: ctrl.stream.live_state == "attached", what="the live preview at another size")
    lease = list(dct.connections_ready[-1].leases.values())[-1]
    check("a map reopened at another size reuses the image, at the new size and with the new pixels",
          scene.dct_link.image == opened and tuple(opened.size) == (32, 16)
          and bytes(lease["canvas"]) == smaller.tobytes(), tuple(opened.size))
    bpy.ops.dct_link.live_stop()
    pump(addon, lambda: not dct.connections_ready[-1].leases, what="the live texture to close")
    pump(addon, lambda: not opened.is_dirty, what="the resized image to be kept with the file")

    # An image changed since it was opened (here changed and packed again, so Blender sees nothing unsaved) is never
    # overwritten: the next open makes a new image.
    values = np.empty(32 * 16 * 4, np.float32)
    opened.pixels.foreach_get(values)
    values[:4] = [1.0, 0.0, 1.0, 1.0]
    opened.pixels.foreach_set(values)
    opened.pack()
    check("the changed image counts as saved for Blender", not opened.is_dirty)
    request_id = dct.open_texture(smaller.tobytes(), 32, 16, target="normal", name="jbib_normal_003")
    pump(addon, lambda: dct.host_result(request_id) is not None and ctrl.stream.live_state == "attached",
         what="the open after a change")
    changed = np.empty(32 * 16 * 4, np.float32)
    opened.pixels.foreach_get(changed)
    check("an image changed since it was opened is never overwritten",
          scene.dct_link.image != opened and list(changed[:4]) == [1.0, 0.0, 1.0, 1.0]
          and host.stored_map(scene.dct_link.image) == "normal")
    bpy.ops.dct_link.live_stop()
    pump(addon, lambda: not dct.connections_ready[-1].leases, what="the live texture to close")
    newer = scene.dct_link.image
    check("Unlink runs", "FINISHED" in bpy.ops.dct_link.unlink_image() and host.stored_binding(newer) is None)

    # A model: without a usable Sollumz DCT hears dependency-missing.
    if not args.sollumz:
        bpy.utils.unregister_class(sollumz_stub.SOLLUMZ_OT_import_assets)
        request_id = dct.open_model([("smoke_open.ydd.xml", b"<DrawableDictionary />")])
        pump(addon, lambda: dct.host_result(request_id) is not None, what="the refusal without Sollumz")
        check("a model without Sollumz's import is refused as dependency-missing",
              dct.host_result(request_id).get("code") == "dependency-missing"
              and ctrl.model.open_notice.message.key == "open.model-needs-sollumz", ctrl.model.open_notice)
        bpy.utils.register_class(sollumz_stub.SOLLUMZ_OT_import_assets)
        files = [("smoke_open.ydd.xml", b"<DrawableDictionary />"), ("smoke_diff_000_a_uni.dds", b"DDS " + bytes(124))]
    else:
        # What the real Sollumz exported earlier, sent back as the model to open (the full round trip), with its
        # diffuse sampler naming a texture that comes as a DDS file in the folder named after the model.
        exported = dict(dct.pushes[0][1])
        model = next(name for name in exported if name.endswith(".ydd.xml"))
        xml = exported[model].replace(b'<Item name="DiffuseSampler" type="Texture" />',
                                      b'<Item name="DiffuseSampler" type="Texture"><Name>smoke_open_diff</Name></Item>')
        check("the exported model has a diffuse sampler to name a texture in", xml != exported[model])
        files = [("smoke_open.ydd.xml", xml), ("smoke_open_diff.dds", rgba_dds(4, 4, (40, 80, 160)))]
        files += [(n, d) for n, d in sorted(exported.items()) if n != model]

    # A model whose import fails is never linked.
    broken = [("smoke_broken.ydd.xml", b"<DrawableDictionary><Item>")]
    if not args.sollumz:
        STUB["mode"] = "fail-import"
    objects_before = {obj.session_uid for obj in bpy.data.objects}
    dct.open_model(broken)
    pump(addon, lambda: ctrl.model.open_notice is not None and ctrl.model.open_notice.level == "ERROR",
         timeout=60, what="the failed import")
    STUB["mode"] = "ydd"
    linked = [obj for obj in bpy.data.objects if obj.session_uid not in objects_before and host.stored_binding(obj)]
    check("a model whose import failed is not linked, and the panel says so",
          not linked and ctrl.model.open_notice.message.key == "open.model-failed", ctrl.model.open_notice)

    root, folder = open_model_from_dct(addon, ctrl, dct, files, host, link, BINDING)
    scene = bpy.context.scene
    check("the opened model is selected and pushed automatically",
          root.select_get() and bpy.context.view_layer.objects.active == root and scene.dct_link.auto_push)
    if not args.sollumz:
        imported = sollumz_stub.STUB["imports"][-1]
        check("the files were written where Sollumz reads them, and its textures are packed",
              imported["found"] == ["smoke_open.ydd.xml", "smoke_open/smoke_diff_000_a_uni.dds"]
              and imported["textures_mode"] == "PACK" and imported["custom"], imported)
    check("the opened model's files exist while it is on the ped", folder.is_dir())
    log = draw_everything(package, state, "opened model")
    labels = " ".join(entry[1] for entry in log if entry[0] == "label")
    check("the opened model says where it came from and which cloth it is linked to",
          "Opened from Durty Cloth Tool: smoke_open" in labels and "Linked to jbib_003_u" in labels
          and ("operator", "dct_link.unlink_model") in log, labels)

    # Undo and redo keep the link (the add-on records an undo step after linking).
    root_name = root.name
    try:
        bpy.ops.ed.undo()
        bpy.ops.ed.redo()
        again = bpy.data.objects.get(root_name)
        check("after an undo and a redo the opened model is still linked",
              again is not None and link.same_binding(host.stored_binding(again), BINDING))
        root = again
    except RuntimeError as exc:
        RESULTS.append({"check": "undo of the link (not available in background mode)", "ok": True, "detail": str(exc)})
    scene = bpy.context.scene  # an undo step replaces the data blocks

    # A copy made with Duplicate carries the link: pushing it is refused until one of them is unlinked.
    copy = root.copy()
    scene.collection.objects.link(copy)
    bpy.ops.object.select_all(action="DESELECT")
    copy.select_set(True)
    bpy.context.view_layer.objects.active = copy
    pushes = len(dct.pushes)
    check("a copy linked to the same cloth is not pushed", refused(bpy.ops.dct_link.model_push, "same cloth")
          and len(dct.pushes) == pushes)
    log = draw_everything(package, state, "copied model")
    labels = " ".join(entry[1] for entry in log if entry[0] == "label")
    check("the Model panel says that two models are linked to one cloth", "is linked to the same cloth" in labels,
          labels)
    check("Unlink (model) runs for the copy", "FINISHED" in bpy.ops.dct_link.unlink_model()
          and host.stored_binding(copy) is None and link.same_binding(host.stored_binding(root), BINDING))
    bpy.data.objects.remove(copy)

    scene.dct_link.auto_push = False
    bpy.ops.object.select_all(action="DESELECT")
    root.select_set(True)
    bpy.context.view_layer.objects.active = root
    check("Discard (opened model) runs", "FINISHED" in bpy.ops.dct_link.model_discard())
    pump(addon, lambda: ctrl.model.lease is None, what="the opened model's discard")
    check("discarding the opened model removes its temporary files", not folder.exists())
    texture = "smoke_open_diff" if args.sollumz else "smoke_diff_000_a_uni"
    images = [image for image in bpy.data.images if image.name.lower().startswith(texture)]
    check("the opened model's texture was read from the model's folder and stays in Blender, packed",
          images and all(image.packed_file is not None for image in images)
          and (not args.sollumz or tuple(images[0].size) == (4, 4)),
          [(image.name, tuple(image.size), image.packed_file is not None) for image in images])

    if args.sollumz:
        # Open the same model twice with a changed diffuse: the second import shows the new pixels, never the
        # image Sollumz loaded for the first one.
        files = [(n, rgba_dds(4, 4, (200, 30, 90)) if n == "smoke_open_diff.dds" else d) for n, d in files]
        first_name = root.name
        second, folder = open_model_from_dct(addon, ctrl, dct, files, host, link, BINDING)
        check("the model opened again takes the link from the one opened before",
              host.stored_binding(bpy.data.objects[first_name]) is None)
        node = next((n for obj in second.children_recursive if obj.type == "MESH" for slot in obj.material_slots
                     if slot.material is not None and slot.material.node_tree is not None
                     for n in slot.material.node_tree.nodes if n.name == "DiffuseSampler"), None)
        image = node.image if node is not None else None
        rgba = list(image.pixels[:4]) if image is not None else []
        check("a model opened again with a changed diffuse shows the new diffuse",
              image is not None and image.packed_file is not None
              and abs(rgba[0] - 200 / 255) < 0.02 and abs(rgba[1] - 30 / 255) < 0.02 and abs(rgba[2] - 90 / 255) < 0.02,
              (image and image.name, rgba))
        scene.dct_link.auto_push = False
        bpy.ops.object.select_all(action="DESELECT")
        second.select_set(True)
        bpy.context.view_layer.objects.active = second
        bpy.ops.dct_link.model_discard()
        pump(addon, lambda: ctrl.model.lease is None, what="the second model's discard")


def open_model_from_dct(addon, ctrl, dct, files, host, link, binding):
    """Sends ``files`` as Edit in connected app does and waits for the import and the first push. Returns the new
    Drawable Dictionary and the folder its files were written to."""
    pushes = len(dct.pushes)
    objects_before = {obj.session_uid for obj in bpy.data.objects}
    request_id = dct.open_model(files)
    pump(addon, lambda: dct.host_result(request_id) is not None, what="the answer to the model")
    check("DCT hears ok for the model it sent", dct.host_result(request_id)["ok"] is True, dct.host_result(request_id))
    pump(addon, lambda: len(dct.pushes) > pushes and ctrl.model.lease is not None and not ctrl.model.pushing,
         timeout=60, what="the push of the opened model")
    roots = [obj for obj in bpy.data.objects if obj.session_uid not in objects_before and obj.parent is None
             and getattr(obj, "sollum_type", "") == "sollumz_drawable_dictionary"]
    check("Sollumz imported the model as a Drawable Dictionary linked to its cloth",
          len(roots) == 1 and link.same_binding(host.stored_binding(roots[0]), binding), [o.name for o in roots])
    header = dct.pushes[pushes][0]
    check("the first push of the opened model names its cloth", header.get("binding") == binding
          and "lease" not in header, header)
    base = pathlib.Path(ctrl.data_dir) / link.MODELS_FOLDER
    folders = [d for d in base.iterdir() if d.name.startswith(request_id + "-")]
    check("each open of a model gets a folder of its own",
          len(folders) == 1 and (folders[0] / "smoke_open" / "smoke_open.ydd.xml").is_file(), sorted(base.iterdir()))
    return roots[0], folders[0]


def rgba_dds(width, height, rgb):
    """An uncompressed 32-bit DDS file (what CodeWalker writes for small textures), filled with one colour."""
    import struct

    header = struct.pack("<4s7I44x", b"DDS ", 124, 0x100F, height, width, width * 4, 0, 0)
    pixel_format = struct.pack("<8I", 32, 0x41, 0, 32, 0x00FF0000, 0x0000FF00, 0x000000FF, 0xFF000000)
    caps = struct.pack("<5I", 0x1000, 0, 0, 0, 0)
    red, green, blue = rgb
    return header + pixel_format + caps + bytes((blue, green, red, 255)) * (width * height)


def smoke(args, repo, repo_dir, package, addon, state, preferences, ctrl, dct, api):
    import numpy as np

    scene = bpy.context.scene
    host = sys.modules[package + ".host"]

    draw_everything(package, state, "before connecting")
    # Connecting and signing in (the first timer step connects because Connect Automatically is on). Nobody is
    # signed in yet, so the session asks Durty Cloth Tool to approve a sign-in; the user approves it a moment later.
    dct.on_assist = lambda code: True
    pump(addon, lambda: ctrl.sign_in_prompt is not None and bool(dct.assisted_codes), what="the sign-in request")
    log = draw_everything(package, state, "signing in")
    check("the sign-in step waits for the approval, with Cancel", ("operator", "dct_link.cancel_sign_in") in log)
    check("the data folder is the extension's user folder",
          pathlib.Path(ctrl.data_dir).resolve() == pathlib.Path(bpy.utils.extension_path_user(package)).resolve())
    api.approve(dct.assisted_codes[-1])
    dct.on_assist = api.approve
    pump(addon, lambda: ctrl.ready and ctrl.focused is not None, what="the welcome")
    check("signed in through DCT and connected", ctrl.account_name == "Durty" and dct.assisted_codes,
          ctrl.notice)
    # The interface follows Blender's language (German here) and every panel still draws.
    strings = sys.modules[package + ".strings"]
    view = bpy.context.preferences.view
    languages = [item.identifier for item in view.bl_rna.properties["language"].enum_items]
    german = next((code for code in languages if code.startswith("de")), None)
    if bpy.app.build_options.international and german:
        before = (view.language, view.use_translate_interface, view.use_translate_tooltips)
        view.language = german
        view.use_translate_interface = view.use_translate_tooltips = True
        try:
            check("the add-on speaks Blender's language", strings.t("panel.live") == "Live-Vorschau"
                  and strings.tt("op.live-start.desc").startswith("Dieses Bild"), strings.t("panel.live"))
            check("Blender translates the add-on's labels in its own context",
                  bpy.app.translations.pgettext_iface("Start Live Preview", strings.CONTEXT) == "Live-Vorschau starten")
            draw_everything(package, state, "German")
        finally:
            view.language, view.use_translate_interface, view.use_translate_tooltips = before
        check("English is back after switching", strings.t("panel.live") == "Live Preview")
    else:
        RESULTS.append({"check": "translations (Blender built without international support)", "ok": True,
                        "detail": str(german)})

    paths = set(api.paths())
    check("only the public sign-in routes were called",
          {"POST /link/api/auth/device", "POST /link/api/assertions"} <= paths <= {
              "POST /link/api/auth/device", "POST /link/api/auth/token", "POST /link/api/assertions"}, paths)
    names = sorted(p.name for p in ctrl.data_dir.iterdir())
    check("the sign-in is stored protected in the user folder",
          {"install-id", "tokens.dpapi"} <= set(names) if os.name == "nt" else len(names) >= 1, names)

    # Texture streaming of a byte image through the operators.
    width, height = 256, 128
    image = bpy.data.images.new("smoke_diffuse", width, height, alpha=True)
    rng = np.random.default_rng(5)
    top_down = rng.integers(0, 256, size=(height, width, 4), dtype=np.uint8)
    image.pixels.foreach_set((top_down[::-1].astype(np.float32) / 255).reshape(-1))
    frame, lease = stream_image(addon, ctrl, dct, image)
    log = draw_everything(package, state, "streaming")
    check("the save buttons are shown during the live preview",
          ("operator", "dct_link.live_save") in log and ("operator", "dct_link.live_save_variation") in log)
    check("the first frame is the whole image, rows top to bottom",
          frame[2] == {"x": 0, "y": 0, "w": width, "h": height} and bytes(lease["canvas"]) == top_down.tobytes())

    # Paint near Blender's bottom-left corner (Blender rows start at the bottom).
    pixels = np.empty(width * height * 4, np.float32)
    image.pixels.foreach_get(pixels)
    rows = pixels.reshape(height, width, 4)
    rows[2:6, 3:9] = [1.0, 0.0, 0.0, 1.0]
    image.pixels.foreach_set(pixels)
    top_down[height - 6 : height - 2, 3:9] = [255, 0, 0, 255]
    frames = len(dct.frames)
    pump(addon, lambda: len(dct.frames) > frames, what="the painted frame")
    check("a change near the bottom arrives as a dirty rectangle at the bottom",
          dct.frames[frames][2] == {"x": 0, "y": 64, "w": 64, "h": 64}, dct.frames[frames][2])
    check("the preview has the painted pixels", bytes(lease["canvas"]) == top_down.tobytes())

    check("Pause and Resume run", "FINISHED" in bpy.ops.dct_link.live_pause() and ctrl.stream.paused
          and "FINISHED" in bpy.ops.dct_link.live_pause() and not ctrl.stream.paused)
    diagnostics = sys.modules[package + ".ui"].diagnostics(bpy.context)  # background Blender has no clipboard
    check("Copy Diagnostics runs", "FINISHED" in bpy.ops.dct_link.diagnostics()
          and diagnostics.startswith("Durty Cloth Tool Creator Link diagnostics") and "sollumz:" in diagnostics)
    pump(addon, lambda: ctrl.stream.findings is not None, what="the texture checks")
    log = draw_everything(package, state, "texture checks")
    check("the texture checks are shown", ("operator", "dct_link.check_again") in log, ctrl.stream.findings)
    check("Save to Cloth runs", "FINISHED" in bpy.ops.dct_link.live_save())
    pump(addon, lambda: not ctrl.stream.saving, what="the save")
    check("the texture was saved", dct.saves and dct.saves[-1][2] == "replace" and
          ctrl.stream.status.message.key == "live.saved", ctrl.stream.status)
    check("Save as New Variation runs", "FINISHED" in bpy.ops.dct_link.live_save_variation())
    pump(addon, lambda: not ctrl.stream.saving, what="the second save")
    check("the variation was saved", dct.saves[-1][2] == "newVariation")
    check("Discard Changes runs", "FINISHED" in bpy.ops.dct_link.live_discard())
    pump(addon, lambda: not dct.connections_ready[-1].leases, what="the live texture to close")
    check("discarding drops the changes and closes the live texture", dct.discards and not ctrl.stream.active)

    # A float image painted with half-transparent colour: Blender keeps it premultiplied and linear.
    size = 64
    floats = bpy.data.images.new("smoke_float", size, size, alpha=True, float_buffer=True)
    straight = rng.random((size, size, 4), dtype=np.float32)
    straight[..., 3] = 0.5
    premultiplied = straight.copy()
    premultiplied[..., :3] *= 0.5
    floats.pixels.foreach_set(premultiplied[::-1].reshape(-1))
    source = host.BlenderImageSource(floats, "diffuse")
    check("a float diffuse image is unpremultiplied and encoded as sRGB",
          source.conversion.unpremultiply and source.conversion.encode_srgb, source.conversion)
    floats.alpha_mode = "CHANNEL_PACKED"
    packed = host.BlenderImageSource(floats, "diffuse")
    check("a Channel Packed float image is not divided by alpha",
          not packed.conversion.unpremultiply and packed.conversion.encode_srgb, packed.conversion)
    floats.alpha_mode = "STRAIGHT"
    frame, lease = stream_image(addon, ctrl, dct, floats)
    pixels_module = sys.modules[package + ".pixels"]
    expected = np.empty((size, size, 4), np.uint8)
    expected[..., :3] = np.floor(pixels_module.srgb_reference(straight[..., :3]) * 255 + 0.5)
    expected[..., 3] = 128
    received = np.frombuffer(bytes(lease["canvas"]), np.uint8).reshape(size, size, 4)
    check("a half-transparent float image arrives as straight sRGB colour",
          int(np.abs(received.astype(int) - expected.astype(int)).max()) <= 1,
          int(np.abs(received.astype(int) - expected.astype(int)).max()))
    check("Stop Live Preview runs", "FINISHED" in bpy.ops.dct_link.live_stop())
    pump(addon, lambda: not dct.connections_ready[-1].leases, what="the float live texture to close")

    # Model push through Sollumz's export operator.
    if args.sollumz:
        install_real_sollumz(repo, repo_dir, args.sollumz, args.sollumz_site)
        root, part = real_sollumz_scene()
    else:
        sollumz_stub.register()
        root, part = sollumz_stub.scene()
    available, text = host.sollumz_status()
    check("Sollumz is detected", available, text)
    use_logger, counter = host._sollumz_log_counter()
    if args.sollumz:
        check("Sollumz's warnings are counted through its logger", use_logger is not None and counter is not None)
    else:
        check("without Sollumz's logger the Info log is watched instead", use_logger is None and counter is None)
    bpy.ops.object.select_all(action="DESELECT")
    part.select_set(True)
    bpy.context.view_layer.objects.active = part
    check("Push Model runs", "FINISHED" in bpy.ops.dct_link.model_push(), ctrl.model.status)
    pump(addon, lambda: ctrl.model.lease is not None, what="model.applied")
    log = draw_everything(package, state, "model pushed")
    check("the model save button is shown", ("operator", "dct_link.model_save") in log)
    header, files = dct.pushes[0]
    model_name = next(name for name in files if name.endswith(".ydd.xml"))
    check("the push is ydd-xml with bare file names", header["format"] == "ydd-xml" and
          model_name == "smoke_ydd.ydd.xml" and all("/" not in n and "\\" not in n for n in files), sorted(files))
    RESULTS.append({"check": "pushed files", "ok": True,
                    "detail": ", ".join(f"{name} ({len(data)} bytes)" for name, data in sorted(files.items()))})
    if args.sollumz:
        xml = files[model_name]
        check("Sollumz wrote CodeWalker XML of a drawable dictionary holding the drawable",
              b"<DrawableDictionary" in xml[:4096] and b"<Item" in xml and b"ped.sps" in xml, xml[:300])
    else:
        call = STUB["calls"][0]
        check("Sollumz was asked for CodeWalker XML, gen8, the model only",
              call["custom"] and call["formats"] == ["CWXML"] and call["versions"] == ["GEN8"] and call["limit"]
              and call["selected"] == ["smoke_ydd"], call)
        check("the embedded texture was sent", files.get("smoke_diff_000_a_uni.dds", b"")[:4] == b"DDS ")
    check("the selection was restored", part.select_get() and not root.select_get())

    # Automatic pushes: not by the push itself, after a mesh change, and for an object added to the model later.
    ctrl.model.delay = 0.5
    scene.dct_link.auto_push = True
    bpy.context.view_layer.update()  # evaluates what the push itself changed (the selection)
    end = time.monotonic() + 1.5
    while time.monotonic() < end:
        addon.tick()
        time.sleep(0.01)
    check("a push does not trigger an automatic push by itself", len(dct.pushes) == 1, len(dct.pushes))
    part.data.vertices[0].co.x += 0.25
    part.data.update()
    bpy.context.view_layer.update()
    pump(addon, lambda: len(dct.pushes) >= 2 and not ctrl.model.pushing, what="the automatic push")
    check("a mesh change pushes again with the lease", dct.pushes[1][0].get("lease") == ctrl.model.lease)
    mesh = bpy.data.meshes.new("smoke_late_mesh")
    mesh.from_pydata([(0, 0, 1), (1, 0, 1), (0, 1, 1)], [], [(0, 1, 2)])
    late = bpy.data.objects.new("smoke_late_part", mesh)
    if args.sollumz:
        late.sollum_type = "sollumz_drawable_model"
    else:
        late.sollum_type = "sollumz_drawable_model"
    late.parent = part.parent
    scene.collection.objects.link(late)
    bpy.context.view_layer.update()
    pump(addon, lambda: len(dct.pushes) >= 3 and not ctrl.model.pushing, what="the push for the new object")
    late.location.x += 0.5
    bpy.context.view_layer.update()
    pump(addon, lambda: len(dct.pushes) >= 4 and not ctrl.model.pushing, what="the push after moving the new object")
    check("an object added to the model later is watched too", len(dct.pushes) >= 4, len(dct.pushes))
    scene.dct_link.auto_push = False

    check("Save to Cloth (model) runs", "FINISHED" in bpy.ops.dct_link.model_save())
    pump(addon, lambda: ctrl.model.busy is None, what="the model save")
    check("the model was saved", ctrl.model.status.message.key == "model.saved", ctrl.model.status)
    check("Discard (model) runs", "FINISHED" in bpy.ops.dct_link.model_discard())
    pump(addon, lambda: ctrl.model.lease is None, what="model.closed")

    # A skinned model: the export switches its armature to the rest pose and back, which must not count as an edit.
    skinned_root, skinned_part = skinned_model(bool(args.sollumz))
    bpy.ops.object.select_all(action="DESELECT")
    skinned_part.select_set(True)
    bpy.context.view_layer.objects.active = skinned_part
    pushes = len(dct.pushes)
    check("Push Model runs for a skinned model", "FINISHED" in bpy.ops.dct_link.model_push(), ctrl.model.status)
    pump(addon, lambda: ctrl.model.lease is not None and not ctrl.model.pushing, what="the skinned model.applied")
    if not args.sollumz:
        check("the stand-in exported the armature in its rest pose and switched it back",
              STUB["calls"][-1]["poses"] == ["REST", "POSE"], STUB["calls"][-1]["poses"])
    check("the skinned model was pushed", "smoke_skinned_ydd.ydd.xml" in dct.pushes[-1][1], sorted(dct.pushes[-1][1]))
    scene.dct_link.auto_push = True
    idle(addon, 3.0)
    check("a skinned model is not pushed again by its own export", len(dct.pushes) == pushes + 1,
          len(dct.pushes) - pushes)
    skinned_part.data.vertices[0].co.z += 0.1
    skinned_part.data.update()
    bpy.context.view_layer.update()
    pump(addon, lambda: len(dct.pushes) >= pushes + 2 and not ctrl.model.pushing, what="the skinned automatic push")
    idle(addon, 3.0)
    check("one change of a skinned model gives exactly one automatic push", len(dct.pushes) == pushes + 2,
          len(dct.pushes) - pushes)
    check("the automatic pushes did not pause", not ctrl.model.paused or bool(args.sollumz), ctrl.model.status)
    scene.dct_link.auto_push = False
    check("Discard (skinned model) runs", "FINISHED" in bpy.ops.dct_link.model_discard())
    pump(addon, lambda: ctrl.model.lease is None, what="the skinned model.closed")
    bpy.ops.object.select_all(action="DESELECT")
    part.select_set(True)
    bpy.context.view_layer.objects.active = part

    if not args.sollumz:
        root.hide_set(True)  # a hidden Drawable Dictionary is exported through a visible object inside it
        bpy.ops.object.select_all(action="DESELECT")
        part.select_set(True)
        calls = len(STUB["calls"])
        check("Push Model works with the Drawable Dictionary hidden", "FINISHED" in bpy.ops.dct_link.model_push())
        pump(addon, lambda: ctrl.model.lease is not None, what="the push of the hidden model")
        check("the hidden model was exported through a visible object",
              len(STUB["calls"]) == calls + 1 and STUB["calls"][-1]["selected"] != ["smoke_ydd"]
              and "smoke_ydd.ydd.xml" in dct.pushes[-1][1], STUB["calls"][-1])
        root.hide_set(False)
        bpy.ops.dct_link.model_discard()
        pump(addon, lambda: ctrl.model.lease is None, what="model.closed")
        pushes = len(dct.pushes)
        STUB["mode"] = "ydr"
        check("an export without a .ydd.xml is refused with an explanation",
              refused(bpy.ops.dct_link.model_push, "not a drawable dictionary"))
        STUB["mode"] = "ydd"
        calls = len(STUB["calls"])
        orphan = bpy.data.objects.new("orphan_drawable", None)
        orphan.sollum_type = "sollumz_drawable"
        scene.collection.objects.link(orphan)
        bpy.ops.object.select_all(action="DESELECT")
        orphan.select_set(True)
        check("a Drawable outside a Drawable Dictionary is refused before exporting",
              refused(bpy.ops.dct_link.model_push, "needs a Drawable Dictionary") and len(STUB["calls"]) == calls)
        check("nothing was pushed for the refused exports", len(dct.pushes) == pushes)

    # Edit in connected app (protocol 2): a normal map DCT sends opens as an image linked to its cloth and its live
    # preview starts at once; a model DCT sends is imported with Sollumz, linked and pushed back bound to its cloth.
    open_from_dct(args, addon, state, package, ctrl, dct, scene, rng)
    scene = bpy.context.scene  # undo steps there replace the data blocks

    # Undo: Push Automatically is read from the scene when it is used.
    try:
        bpy.ops.ed.undo_push(message="smoke: before Push Automatically")
        scene.dct_link.auto_push = True
        bpy.ops.ed.undo_push(message="smoke: Push Automatically on")
        bpy.ops.ed.undo()
        undone = not state.scene_auto_push(bpy.context.scene)
        check("after an undo Push Automatically follows the scene", undone and state.watcher._stale)
    except RuntimeError as exc:
        RESULTS.append({"check": "undo (not available in background mode)", "ok": True, "detail": str(exc)})
    bpy.context.scene.dct_link.auto_push = False

    # Loading another file stops the stream and forgets the pushed model.
    stream_image(addon, ctrl, dct, bpy.data.images["smoke_diffuse"])
    blend = pathlib.Path(tempfile.mkdtemp(prefix="dct_smoke_blend_", dir=os.environ["BLENDER_USER_RESOURCES"]))
    bpy.ops.wm.save_as_mainfile(filepath=str(blend / "smoke.blend"))
    bpy.ops.wm.open_mainfile(filepath=str(blend / "smoke.blend"))
    pump(addon, lambda: not dct.connections_ready[-1].leases, what="the live texture to close after loading")
    check("loading a file stops streaming and forgets the pushed model",
          not ctrl.stream.active and state.watcher.root_uid is None and ctrl.model.root_name is None)

    # Updates come from the public repository Blender adds when the install link is dragged onto it; a copy
    # installed from a file says how to switch.
    check("this test copy counts as installed from a file", not host.installed_from_dct_repository(package))
    log = draw_everything(package, state, "installed from a file")
    labels = " ".join(entry[1] for entry in log if entry[0] == "label")
    check("the settings explain how to get updates for a copy installed from a file",
          "installed from a file" in labels and ("operator", "dct_link.open_plugins_page") in log)

    # The user disconnects Blender in Durty Cloth Tool: nothing connects again until Connect.
    dct.connections_ready[-1].kick("disconnected")
    pump(addon, lambda: ctrl.dct_disconnected and ctrl.state == "stopped", what="the disconnect in DCT")
    log = draw_everything(package, state, "disconnected in DCT")
    labels = " ".join(entry[1] for entry in log if entry[0] == "label")
    check("a disconnect in DCT is explained, with Connect",
          "disconnected in Durty Cloth Tool" in labels and ("operator", "dct_link.connect") in log, labels)
    check("Connect runs after the disconnect", "FINISHED" in bpy.ops.dct_link.connect())
    pump(addon, lambda: ctrl.ready, what="connecting again after the disconnect")

    # The garment fitting tools, while signed in (the hosted body comes from the fake gta.clothing).
    RESULTS.extend(garment_smoke.run(package, addon, state, ctrl, api, check, refused, pump, draw_everything, dct=dct,
                                     real=bool(args.sollumz)))

    # Custom Ped: a synthetic character rigged and sent to the fake Durty Cloth Tool.
    RESULTS.extend(ped_smoke.run(package, addon, state, ctrl, check, refused, pump, draw_everything, dct))

    # Signing out (the network part runs on a worker thread), then disabling and enabling again.
    check("Sign Out runs", "FINISHED" in bpy.ops.dct_link.sign_out("EXEC_DEFAULT"))
    pump(addon, lambda: api.logouts == 1, what="the sign-out at gta.clothing")
    check("signing out ends the session on gta.clothing", ctrl.user_name is None and ctrl.signed_out)
    log = draw_everything(package, state, "signed out")
    check("the sign-in buttons are shown", ("operator", "dct_link.sign_in") in log)
    session = ctrl.session
    result = bpy.ops.preferences.addon_disable(module=package)
    check("the add-on disables cleanly", "FINISHED" in result and not bpy.app.timers.is_registered(addon.tick)
          and (session is None or not session._closing))

    devices = len([r for r in api.requests if r["path"] == "/link/api/auth/device"])
    check("the add-on enables again", "FINISHED" in bpy.ops.preferences.addon_enable(module=package))
    addon = sys.modules[package + ".addon"]
    state = sys.modules[package + ".state"]
    ctrl = state.get()
    ctrl.port_override = dct.port
    ctrl.auth_base_url = api.base_url
    pump(addon, lambda: ctrl.state == "stopped" and ctrl.signed_out, what="the remembered sign-out")
    check("after a sign-out no sign-in starts by itself",
          len([r for r in api.requests if r["path"] == "/link/api/auth/device"]) == devices)
    check("Sign In (approved in Durty Cloth Tool) runs", "FINISHED" in bpy.ops.dct_link.sign_in())
    pump(addon, lambda: ctrl.ready, what="the sign-in after enabling again")
    check("connected again after enabling the add-on again", ctrl.account_name == "Durty")
    result = bpy.ops.preferences.addon_disable(module=package)
    check("the add-on disables cleanly again", "FINISHED" in result)

    # Whether uninstalling removes the add-on's user folder (reported, not required).
    data_dir = pathlib.Path(ctrl.data_dir)
    try:
        index = list(bpy.context.preferences.extensions.repos).index(repo)
        bpy.ops.extensions.package_uninstall(repo_directory=repo.directory, repo_index=index,
                                             pkg_id="durty_cloth_tool_link")
        RESULTS.append({"check": "uninstalling removes the user folder", "ok": True,
                        "detail": str(not data_dir.exists())})
    except (RuntimeError, TypeError, ValueError) as exc:
        RESULTS.append({"check": "uninstalling removes the user folder", "ok": True, "detail": f"not checked: {exc}"})


def main():
    args = parse_args()
    ok = False
    try:
        run(args)
        ok = True
    except Exception as exc:  # noqa: BLE001 - report every failure in the JSON report
        traceback.print_exc()
        RESULTS.append({"check": "exception", "ok": False, "detail": f"{type(exc).__name__}: {exc}"})
    report = {
        "blender": bpy.app.version_string,
        "python": sys.version.split()[0],
        "sollumz": "real" if args.sollumz else "stand-in",
        "ok": ok and all(r["ok"] for r in RESULTS),
        "results": RESULTS,
    }
    pathlib.Path(args.report).write_text(json.dumps(report, indent=2), "utf-8")
    sys.stdout.flush()
    os._exit(0 if report["ok"] else 1)


main()
