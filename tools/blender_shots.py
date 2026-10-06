#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2026 Schmid Software Solutions (https://schmid-software.de)
"""Screenshots of the DCT tab in every state, for interface reviews.

    python tools/blender_shots.py --blender <path to blender> --out <folder>
        [--source <add-on source folder>] [--prefix after] [--expanded] [--language de_DE] [--theme light]
        [--scenario garment]

Builds the extension from ``--source`` (default: this repository's ``durty_cloth_tool_link``), starts a Blender
window with a throw-away user folder (``BLENDER_USER_RESOURCES``), installs the build, and walks the add-on through
its states against the fake Durty Cloth Tool and fake gta.clothing of the tests on 127.0.0.1: Durty Cloth Tool not
running, signing in, connected, live preview, saving, a pushed model, items opened from Durty Cloth Tool, no cloth,
no project, disconnected in Durty Cloth Tool, a Durty Cloth Tool that is too old, and signed out. ``--scenario
garment`` walks Garment Fitting (Experimental) instead, on a synthetic garment and body: Setup before and after a
garment and the hosted body are added, Fit with markers, Fix with the fit check and the problem colours, a sculpt
session, the tear check, Game Ready after the local steps, and Add to Durty Cloth Tool (the skeleton missing and
in place, what blocks an add, Durty Cloth Tool asking, the cloth added, the free limit, no project open, not
connected). Each state is saved as
``<prefix>-<NN>-<state>.png`` in ``--out``, cropped to the sidebar. ``--expanded`` opens every collapsed
panel and settings group first; ``--language`` and ``--theme light`` change Blender's interface for the run. Blender
quits by itself at the end (and is ended after ``--timeout`` seconds otherwise). Your Blender settings and
extensions are never touched, and nothing is sent to gta.clothing.

The same file runs inside Blender (Blender starts it with ``--python``). Standard library only outside Blender.
"""

from __future__ import annotations

import argparse
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import time
import traceback

try:
    import bpy
except ImportError:  # outside Blender: the launcher
    bpy = None

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_SOURCE = REPO_ROOT / "durty_cloth_tool_link"


# --------------------------------------------------------------------------------------------------
# Outside Blender: build, start and wait
# --------------------------------------------------------------------------------------------------


def launch(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--blender", required=True, help="the blender executable")
    parser.add_argument("--out", required=True, type=pathlib.Path, help="the folder for the screenshots")
    parser.add_argument("--source", type=pathlib.Path, default=DEFAULT_SOURCE, help="the add-on source folder")
    parser.add_argument("--prefix", default="shot", help="the start of every file name")
    parser.add_argument("--expanded", action="store_true", help="open every collapsed panel and group")
    parser.add_argument("--language", help="Blender's interface language for the run, for example de_DE")
    parser.add_argument("--theme", choices=("dark", "light"), default="dark")
    parser.add_argument("--size", default="1280x1600", help="the window size, WIDTHxHEIGHT")
    parser.add_argument("--scenario", choices=("link", "garment"), default="link", help="which states to walk")
    parser.add_argument("--timeout", type=float, default=420.0)
    args = parser.parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(REPO_ROOT))
    from tools.blender_smoke import isolated_environment  # never the real Blender profile

    user = tempfile.mkdtemp(prefix="dct_shots_user_")
    env = isolated_environment(user)
    try:
        build = pathlib.Path(user) / "build"
        build.mkdir()
        result = subprocess.run([args.blender, "--factory-startup", "--command", "extension", "build", "--source-dir",
                                 str(args.source.resolve()), "--output-dir", str(build)], env=env, capture_output=True,
                                text=True, encoding="utf-8", errors="replace", timeout=300)
        archives = sorted(build.glob("*.zip"))
        if result.returncode != 0 or not archives:
            print(result.stdout[-3000:], result.stderr[-3000:])
            print("error: the extension did not build")
            return 1
        width, height = (int(v) for v in args.size.lower().split("x"))
        command = [args.blender, "--factory-startup", "--online-mode", "--window-geometry", "0", "0", str(width),
                   str(height), "--python", str(pathlib.Path(__file__).resolve()), "--", "--zip", str(archives[-1]),
                   "--out", str(args.out.resolve()), "--prefix", args.prefix, "--theme", args.theme,
                   "--scenario", args.scenario]
        if args.expanded:
            command.append("--expanded")
        if args.language:
            command += ["--language", args.language]
        process = subprocess.Popen(command, cwd=REPO_ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   text=True, encoding="utf-8", errors="replace")
        try:
            output, _ = process.communicate(timeout=args.timeout)
        except subprocess.TimeoutExpired:
            process.kill()
            output, _ = process.communicate()
            print(output[-4000:])
            print("error: Blender did not finish in time and was ended")
            return 1
        lines = [line for line in output.splitlines() if line.startswith(("SHOT ", "SKIP ", "ERROR "))]
        print("\n".join(lines))
        failed = any(line.startswith("ERROR ") for line in lines) or process.returncode != 0
        if failed:
            print(output[-4000:])
        return 1 if failed else 0
    finally:
        shutil.rmtree(user, ignore_errors=True)


# --------------------------------------------------------------------------------------------------
# Inside Blender: install, drive the states, take the screenshots, quit
# --------------------------------------------------------------------------------------------------


class Shots:
    def __init__(self, args) -> None:
        self.args = args
        self.out = pathlib.Path(args.out)
        self.count = 0
        self.scratch = pathlib.Path(tempfile.mkdtemp(prefix="dct_shots_", dir=os.environ["BLENDER_USER_RESOURCES"]))

    # ---- the window --------------------------------------------------------------------------------

    def view(self):
        window = bpy.context.window_manager.windows[0]
        area = max((a for a in window.screen.areas if a.type == "VIEW_3D"), key=lambda a: a.width * a.height)
        region = next(r for r in area.regions if r.type == "UI")
        return window, area, region

    def prepare_window(self):
        window, area, _ = self.view()
        with bpy.context.temp_override(window=window, screen=window.screen, area=area):
            bpy.ops.screen.screen_full_area()
        window, area, _ = self.view()
        area.spaces.active.show_region_ui = True
        area.spaces.active.show_region_toolbar = False

    def show_tab(self):
        _, _, region = self.view()
        try:
            region.active_panel_category = "DCT"
        except (TypeError, ValueError):
            pass  # the categories appear after the first draw; the next step tries again
        self.redraw()

    def redraw(self):
        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas:
                area.tag_redraw()
                for region in area.regions:
                    region.tag_redraw()

    def shot(self, name: str):
        import numpy as np

        window, area, region = self.view()
        self.count += 1
        full = self.scratch / f"full-{self.count:02d}.png"
        with bpy.context.temp_override(window=window, screen=window.screen, area=area):
            bpy.ops.screen.screenshot_area(filepath=str(full), check_existing=False)
        image = bpy.data.images.load(str(full))
        try:
            width, height = image.size
            pixels = np.empty(width * height * 4, np.float32)
            image.pixels.foreach_get(pixels)
            rows = pixels.reshape(height, width, 4)
            x0 = max(0, region.x - area.x)
            y0 = max(0, region.y - area.y)
            crop = np.ascontiguousarray(rows[y0:y0 + region.height, x0:x0 + region.width])
            out = bpy.data.images.new(f"shot_{self.count}", crop.shape[1], crop.shape[0], alpha=True)
            out.pixels.foreach_set(crop.reshape(-1))
            path = self.out / f"{self.args.prefix}-{self.count:02d}-{name}.png"
            out.filepath_raw = str(path)
            out.file_format = "PNG"
            out.save()
            bpy.data.images.remove(out)
            print(f"SHOT {path.name}")
        finally:
            bpy.data.images.remove(image)

    # ---- the run -----------------------------------------------------------------------------------

    def steps(self):
        args = self.args
        prefs = bpy.context.preferences
        if args.language:
            prefs.view.language = args.language
            prefs.view.use_translate_interface = prefs.view.use_translate_tooltips = True
        if args.theme == "light":
            presets = pathlib.Path(bpy.utils.resource_path("LOCAL")) / "scripts" / "presets" / "interface_theme"
            bpy.ops.script.execute_preset(filepath=str(presets / "Blender_Light.xml"),
                                          menu_idname="USERPREF_MT_interface_theme_presets")
        self.prepare_window()
        yield 0.5

        repo_dir = tempfile.mkdtemp(prefix="dct_shots_repo_", dir=os.environ["BLENDER_USER_RESOURCES"])
        bpy.ops.preferences.extension_repo_add(name="dct_shots", type="LOCAL", use_custom_directory=True,
                                               custom_directory=repo_dir)
        repo = next(r for r in prefs.extensions.repos if r.name == "dct_shots")
        bpy.ops.extensions.package_install_files(filepath=args.zip, repo=repo.module, enable_on_install=False)
        package = f"bl_ext.{repo.module}.durty_cloth_tool_link"

        sys.path.insert(0, str(REPO_ROOT))
        from tests.blender import sollumz_stub
        from tests.support.fake_dct import FakeDct
        from tests.support.fake_link_api import FakeLinkApi

        # Before the add-on is enabled: Durty Cloth Tool "not running" is a port nobody listens on.
        import socket

        probe = socket.socket()
        probe.bind(("127.0.0.1", 0))
        dead_port = probe.getsockname()[1]
        probe.close()
        bpy.ops.preferences.addon_enable(module=package)
        addon = sys.modules[package + ".addon"]
        state = sys.modules[package + ".state"]
        ui = sys.modules[package + ".ui"]
        link = sys.modules[package + ".link"]
        protocol = sys.modules[package + ".dct_link.protocol"]
        ctrl = state.get()
        ctrl.port_override = dead_port
        if args.expanded:
            self.expand(ui)
        dct = FakeDct(protocol=protocol)
        api = FakeLinkApi()
        api.protocol = f"{protocol.PROTOCOL_MAJOR}.0"  # also an older build of the add-on, for comparisons
        ctrl.auth_base_url = api.base_url
        new = hasattr(link.LinkController, "open_map")
        try:
            if args.scenario == "garment":
                yield from self.garment_states(package, ctrl, dct, api, ui, sollumz_stub)
            else:
                yield from self.states(ctrl, dct, api, ui, link, sollumz_stub, new, dead_port)
        finally:
            dct.stop()
            api.stop()

    def expand(self, ui):
        """Opens every collapsed panel and settings group (they are created closed only at their first draw)."""
        original = ui._group

        def group(layout, context, idname, key, icon, info=None, closed=False):
            return original(layout, context, idname, key, icon, info=info, closed=False)

        ui._group = group
        for cls in ui.CLASSES:
            options = getattr(cls, "bl_options", None)
            if isinstance(options, set) and "DEFAULT_CLOSED" in options:
                bpy.utils.unregister_class(cls)
                cls.bl_options = options - {"DEFAULT_CLOSED"}
                bpy.utils.register_class(cls)

    def wait(self, condition, timeout=20.0, what="a state"):
        end = time.monotonic() + timeout
        while not condition():
            if time.monotonic() > end:
                raise TimeoutError(f"timed out waiting for {what}")
            yield 0.1
        self.show_tab()
        yield 0.8  # the timer redraws; let the sidebar draw twice

    def operator(self, call):
        window, area, region = self.view()
        with bpy.context.temp_override(window=window, screen=window.screen, area=area, region=region):
            return call()

    # ---- the garment fitting states (--scenario garment) ---------------------------------------------------

    GARMENT_CHILDREN = ("DCTLINK_PT_garment_setup", "DCTLINK_PT_garment_fit", "DCTLINK_PT_garment_fix",
                        "DCTLINK_PT_garment_ready")

    def show_garment(self, garment_ui, open_child, link_ui=None):
        """Garment Fitting with one child panel open and the others closed (and, with ``link_ui``, the link's working
        panels closed). Blender keeps a panel's open state by its idname, so the classes are registered again under
        new idnames (parents first, in their original order) and start in the state their options give."""
        self.generation = getattr(self, "generation", 0) + 1
        tree = [garment_ui.DCTLINK_PT_garment, garment_ui.DCTLINK_PT_garment_setup, garment_ui.DCTLINK_PT_garment_fit,
                garment_ui.DCTLINK_PT_garment_fix, garment_ui.DCTLINK_PT_garment_ready]
        for cls in reversed(tree):
            bpy.utils.unregister_class(cls)
        if link_ui is not None:
            working = [link_ui.DCTLINK_PT_linked, link_ui.DCTLINK_PT_live, link_ui.DCTLINK_PT_model]
            for cls in reversed(working):
                bpy.utils.unregister_class(cls)
            for cls in working:
                cls.bl_idname = f"{cls.__name__}_shot{self.generation}"
                cls.bl_options = set(getattr(cls, "bl_options", set()) or set()) | {"DEFAULT_CLOSED"}
                bpy.utils.register_class(cls)
        self.scroll(-20)
        parent = f"DCTLINK_PT_garment_shot{self.generation}"
        for cls in tree:
            options = set(getattr(cls, "bl_options", set()) or set())
            closed = cls.__name__ in self.GARMENT_CHILDREN and cls.__name__ != open_child
            cls.bl_options = (options | {"DEFAULT_CLOSED"}) if closed else (options - {"DEFAULT_CLOSED"})
            if cls is tree[0]:
                cls.bl_idname = parent
            else:
                cls.bl_idname = f"{cls.__name__}_shot{self.generation}"
                cls.bl_parent_id = parent
            bpy.utils.register_class(cls)
        self.show_tab()

    def scroll(self, pages):
        """Scrolls the sidebar by whole pages (negative: up), for panels taller than the window."""
        window, area, region = self.view()
        with bpy.context.temp_override(window=window, screen=window.screen, area=area, region=region):
            for _ in range(abs(pages)):
                try:
                    (bpy.ops.view2d.scroll_down if pages > 0 else bpy.ops.view2d.scroll_up)(page=True)
                except RuntimeError:
                    break  # at the end already
        self.redraw()

    def frame_all(self):
        window, area, _ = self.view()
        main = next(r for r in area.regions if r.type == "WINDOW")
        with bpy.context.temp_override(window=window, screen=window.screen, area=area, region=main):
            try:
                bpy.ops.view3d.view_all()
            except RuntimeError:
                pass  # nothing to frame

    def garment_states(self, package, ctrl, dct, api, ui, stub):
        import math

        from tests.blender import garment_smoke

        garment_ui = sys.modules[package + ".ui_garment"]
        gh = sys.modules[package + ".garment_host"]
        stub.register()
        # Signed in and connected: the hosted body needs the sign-in.
        ctrl.shutdown()
        ctrl.port_override = dct.port
        dct.on_assist = api.approve
        dct.focused = None
        ctrl.connect()
        yield from self.wait(lambda: ctrl.ready, 30, "the connection")
        scene = bpy.context.scene
        for obj in list(scene.objects):
            bpy.data.objects.remove(obj)  # the default cube, camera and light
        props = scene.dct_garment

        # 1. Nothing chosen yet: the next step says how to start.
        self.show_garment(garment_ui, "DCTLINK_PT_garment_setup", ui)
        yield from self.wait(lambda: True, 5)
        self.shot("garment-start")

        # 2. A garment and the hosted body (from the fake gta.clothing).
        folder = pathlib.Path(tempfile.mkdtemp(prefix="dct_shots_garment_", dir=os.environ["BLENDER_USER_RESOURCES"]))
        tee = garment_smoke.panel_garment("tshirt_md", "short", 45.0)
        props.garment = tee
        props.gender = "female"
        glb = garment_smoke.body_glb(folder)
        api.body_files = {"freemode_female.glb": glb.read_bytes()}
        garment_ui.BODY_ORIGIN["url"] = api.base_url
        self.operator(lambda: bpy.ops.dct_link.fit_add_body())
        yield from self.wait(lambda: garment_ui.RUNTIME.download is None and props.body is not None, 30,
                             "the hosted body")
        self.frame_all()
        yield from self.wait(lambda: True, 5)
        self.shot("garment-setup")

        # 3. Fit: the markers placed.
        props.category = "tshirt"
        self.operator(lambda: bpy.ops.dct_link.fit_auto_markers())
        self.show_garment(garment_ui, "DCTLINK_PT_garment_fit")
        yield from self.wait(lambda: True, 5)
        self.shot("garment-fit-markers")

        # 4. Fix: aligned to the body, the fit check and the problem colours.
        self.operator(lambda: bpy.ops.dct_link.fit_align())
        self.operator(lambda: bpy.ops.dct_link.fit_check())
        self.operator(lambda: bpy.ops.dct_link.fit_show_problems())
        self.show_garment(garment_ui, "DCTLINK_PT_garment_fix")
        yield from self.wait(lambda: True, 5)
        self.shot("garment-fix-check")
        self.scroll(1)
        yield from self.wait(lambda: True, 5)
        self.shot("garment-fix-check-lower")
        self.scroll(-20)

        # 5. Fix by hand: a sculpt session, then accepted.
        self.operator(lambda: bpy.ops.dct_link.fit_sculpt_start())
        yield from self.wait(lambda: gh.sculpting(tee), 5, "the sculpt session")
        self.shot("garment-fix-sculpting")
        self.operator(lambda: bpy.ops.dct_link.fit_sculpt_accept())
        yield from self.wait(lambda: not gh.sculpting(tee), 5, "the end of the session")
        self.shot("garment-fix-accepted")

        # 6. A garment made in T-pose: brought into the A-pose, rigged by hand, its tears checked.
        tpose = garment_smoke.panel_garment("coat_tpose", "long", 0.0)
        tee.hide_set(True)
        for obj in bpy.context.view_layer.objects:
            obj.select_set(obj == tpose)
        bpy.context.view_layer.objects.active = tpose
        self.operator(lambda: bpy.ops.dct_link.fit_use_garment())
        props.category = "long_sleeve"
        props.source_pose = "t_pose"
        self.operator(lambda: bpy.ops.dct_link.fit_auto_markers())
        self.show_garment(garment_ui, "DCTLINK_PT_garment_fit")
        yield from self.wait(lambda: True, 5)
        self.shot("garment-fit-tpose")
        props.arm_angle = math.radians(40.0)
        self.operator(lambda: bpy.ops.dct_link.fit_tpose_to_apose())
        markers = gh.read_markers(scene)
        rig_data = bpy.data.armatures.new("rig")
        rig = bpy.data.objects.new("rig", rig_data)
        scene.collection.objects.link(rig)
        bpy.context.view_layer.objects.active = rig
        self.operator(lambda: bpy.ops.object.mode_set(mode="EDIT"))
        bones = []
        for name, head, tail, parent in (("SKEL_Spine3", "pelvis", "chest", None),
                                         ("SKEL_L_UpperArm", "shoulder_l", "elbow_l", 0),
                                         ("SKEL_L_Forearm", "elbow_l", "wrist_l", 1),
                                         ("SKEL_R_UpperArm", "shoulder_r", "elbow_r", 0),
                                         ("SKEL_R_Forearm", "elbow_r", "wrist_r", 3)):
            bone = rig_data.edit_bones.new(name)
            bone.head, bone.tail = markers[head], markers[tail]
            if parent is not None:
                bone.parent = bones[parent]
            bones.append(bone)
        self.operator(lambda: bpy.ops.object.mode_set(mode="OBJECT"))
        for obj in bpy.context.view_layer.objects:
            obj.select_set(obj in (tpose, rig))
        bpy.context.view_layer.objects.active = rig
        self.operator(lambda: bpy.ops.object.parent_set(type="ARMATURE_AUTO"))
        garment_smoke.split_weights(tpose)
        self.operator(lambda: bpy.ops.dct_link.fit_check_tears())
        self.show_garment(garment_ui, "DCTLINK_PT_garment_fix")
        yield from self.wait(lambda: True, 5)
        self.scroll(2)  # once the panel has drawn: the sidebar knows its height
        yield from self.wait(lambda: True, 5)
        self.shot("garment-fix-tears")

        # 7. Game ready: prepare, combine materials, levels of detail, validate.
        self.operator(lambda: bpy.ops.dct_link.fit_prepare())
        self.operator(lambda: bpy.ops.dct_link.fit_combine_materials())
        props.lod_medium, props.lod_low = 600, 150
        self.operator(lambda: bpy.ops.dct_link.fit_lods())
        self.operator(lambda: bpy.ops.dct_link.fit_validate())
        self.show_garment(garment_ui, "DCTLINK_PT_garment_ready")
        yield from self.wait(lambda: True, 5)
        self.shot("garment-ready")
        yield from self.garment_add_states(garment_ui, ctrl, dct, tpose, props)

    def garment_add_states(self, garment_ui, ctrl, dct, coat, props):
        """Add to Durty Cloth Tool, at the end of Game Ready, against the fake Durty Cloth Tool."""
        from tests.blender import garment_smoke
        from tests.support import synthetic
        from tests.support.fake_dct import ADDED_BINDING

        dct.skeleton_files = {g: [(synthetic.skeleton_template_file(g), synthetic.skeleton_template_xml(g))]
                              for g in ("male", "female")}
        props.item_name = "Long Coat"
        if not ctrl.ready:  # the long steps before can outlast the connection; it comes back by itself
            ctrl.connect()
            yield from self.wait(lambda: ctrl.ready and ctrl.project is not None, 30, "the connection")

        def show(name, pages=2):
            self.show_garment(garment_ui, "DCTLINK_PT_garment_ready")
            yield from self.wait(lambda: True, 5)
            self.scroll(pages)
            yield from self.wait(lambda: True, 5)
            self.shot(name)

        def run(call):
            try:
                self.operator(call)
            except RuntimeError:
                pass  # an operator that reports why it refused (the panel shows it)

        # 8. The garment is not on the Durty Cloth Tool skeleton yet.
        yield from show("garment-add-skeleton-missing")
        # 9. The skeleton from Durty Cloth Tool, then what blocks an add.
        run(lambda: bpy.ops.dct_link.fit_use_skeleton())
        yield from self.wait(lambda: garment_ui.RUNTIME.job is None and coat.parent is not None
                             and coat.parent.get("dct_skeleton"), 30, "the skeleton")
        yield from show("garment-add-skeleton-ready")
        stray = coat.vertex_groups.new(name="Group")
        props.variations.add()
        run(lambda: bpy.ops.dct_link.fit_add_to_dct())
        yield from show("garment-add-problems")
        coat.vertex_groups.remove(stray)
        props.variations[0].image = garment_smoke.variation_image("coat_blue", 1024, (0.1, 0.2, 0.7))
        props.variations[0].title = "Blue"
        props.first_title = "Sand"
        # 10. Durty Cloth Tool shows the cloth and asks; then the user chooses Add to project.
        dct.hold_adds = True
        run(lambda: bpy.ops.dct_link.fit_add_to_dct())
        yield from self.wait(lambda: bool(dct.item_adds) and ctrl.item_add.adding, 30, "the waiting add")
        yield from show("garment-add-waiting")
        dct.release_adds({"ok": True, "binding": dict(ADDED_BINDING),
                          "findings": [{"code": "non-power-of-two", "severity": "warning"},
                                       {"code": "rig-unchecked", "severity": "info"}]})
        yield from self.wait(lambda: not ctrl.item_add.adding, 20, "the added cloth")
        yield from show("garment-add-added")
        yield from show("garment-add-added-top", pages=-20)
        dct.hold_adds = False
        # 11. Durty Cloth Tool's free limit.
        dct.fail["item.add"] = "item-limit"
        run(lambda: bpy.ops.dct_link.fit_add_to_dct())
        yield from self.wait(lambda: not ctrl.item_add.adding and ctrl.item_add.status is not None
                             and ctrl.item_add.status.message.key == "add.result.item-limit", 20, "the free limit")
        yield from show("garment-add-item-limit")
        del dct.fail["item.add"]
        # 12. No project open in Durty Cloth Tool, then not connected (the next step says what to do).
        del coat["dct_added"]
        ctrl.item_add.forget()
        dct.connections_ready[-1].send({"type": "event.project", "id": "prjg", "project": None})  # the live one
        yield from self.wait(lambda: ctrl.project is None, 10, "no project")
        yield from show("garment-add-no-project", pages=-20)
        ctrl.disconnect()
        yield from self.wait(lambda: not ctrl.ready, 10, "the disconnect")
        yield from show("garment-add-not-connected", pages=-20)

    def states(self, ctrl, dct, api, ui, link, stub, new, dead_port):
        # 1. Durty Cloth Tool is not running: the add-on keeps looking.
        yield from self.wait(lambda: ctrl.search_failed, 30, "the failed search")
        self.shot("dct-not-running")

        # 2. Durty Cloth Tool found, not signed in: Durty Cloth Tool is asked to approve the sign-in (and has not
        #    answered yet: its question is open).
        import threading

        gate = threading.Event()
        answer = {"ok": True}

        def assist(code):
            gate.wait(60)
            return answer["ok"]

        ctrl.shutdown()
        ctrl.port_override = dct.port
        dct.on_assist = assist
        ctrl.connect()
        yield from self.wait(lambda: ctrl.sign_in_prompt is not None and bool(dct.assisted_codes), 30,
                             "the sign-in request")
        self.shot("sign-in-asked-in-dct")

        # 3. Durty Cloth Tool declines: the browser code is what is left.
        answer["ok"] = False
        gate.set()
        yield from self.wait(lambda: ctrl.sign_in_status is not None
                             and ctrl.sign_in_status.message.key == "setup.sign-in.declined", 30, "the refusal")
        self.shot("sign-in-browser-code")

        # 4. Approved: connected, the focused cloth in the Linked Cloth panel.
        api.approve(dct.assisted_codes[-1])
        dct.on_assist = api.approve
        dct.focused = {"clothId": "3f2b8c1e-7a4d-4e8b-9c1f-2d6e5a7b8c90", "name": "jbib_003_u",
                       "selectedTextureId": "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
                       "textures": [{"textureId": "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d", "name": "jbib_diff_003_a_uni",
                                     "width": 2048, "height": 2048},
                                    {"textureId": "b1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d", "name": "jbib_diff_003_b_uni"}],
                       "targets": ["diffuse", "normal"], "drawableType": "jbib", "gender": "female",
                       "collection": "mp_f_freemode_01", "number": 3}
        yield from self.wait(lambda: ctrl.ready and ctrl.focused is not None, 30, "the connection")
        yield 1.0  # the thumbnail
        self.shot("connected")

        # 5. Live preview with the texture checks.
        scene = bpy.context.scene
        image = bpy.data.images.new("jacket_paint", 512, 512, alpha=True)
        scene.dct_link.image = image
        scene.dct_link.target = "diffuse"
        self.operator(lambda: bpy.ops.dct_link.live_start())
        yield from self.wait(lambda: ctrl.stream.live_state == "attached" and ctrl.stream.findings is not None,
                             30, "the live preview")
        self.shot("live")

        # 6. Saving, then saved.
        dct.hold_types = {"live.save"}
        self.operator(lambda: bpy.ops.dct_link.live_save())
        yield from self.wait(lambda: ctrl.stream.saving, 10, "saving")
        self.shot("saving")
        dct.hold_types = set()
        dct.release_held()
        yield from self.wait(lambda: not ctrl.stream.saving, 10, "the save")
        self.shot("saved")
        self.operator(lambda: bpy.ops.dct_link.live_stop())
        yield from self.wait(lambda: not ctrl.stream.active, 10, "the stop")

        # 7. A model pushed with Sollumz (the stand-in).
        stub.register()
        root, part = stub.scene()
        bpy.ops.object.select_all(action="DESELECT")
        part.select_set(True)
        bpy.context.view_layer.objects.active = part
        self.operator(lambda: bpy.ops.dct_link.model_push())
        yield from self.wait(lambda: ctrl.model.lease is not None, 20, "the model push")
        self.shot("model-pushed")
        self.operator(lambda: bpy.ops.dct_link.model_discard())
        yield from self.wait(lambda: ctrl.model.lease is None, 20, "the model discard")

        if new:
            # 8. A normal map opened from Durty Cloth Tool ("Edit in connected app").
            rgba = bytes((x * 7) % 256 for x in range(256 * 256 * 4))
            dct.open_texture(rgba, 256, 256, target="normal", name="jbib_normal_003")
            yield from self.wait(lambda: ctrl.stream.live_state == "attached", 20, "the opened texture")
            self.shot("opened-texture")
            self.operator(lambda: bpy.ops.dct_link.live_stop())
            yield from self.wait(lambda: not ctrl.stream.active, 10, "the stop")

            # 9. A model opened from Durty Cloth Tool.
            dct.open_model([("jbib_003_u.ydd.xml", b"<DrawableDictionary />"),
                            ("jbib_diff_003_a_uni.dds", b"DDS " + bytes(124))])
            yield from self.wait(lambda: ctrl.model.lease is not None and not ctrl.model.pushing, 30, "the opened model")
            self.shot("opened-model")
            self.operator(lambda: bpy.ops.dct_link.model_discard())
            yield from self.wait(lambda: ctrl.model.lease is None, 20, "the model discard")
        else:
            print("SKIP opened-texture and opened-model (this version cannot open items from Durty Cloth Tool)")

        # 10. Sollumz missing.
        for cls in (stub.SOLLUMZ_OT_export_assets, stub.SOLLUMZ_OT_import_assets):
            bpy.utils.unregister_class(cls)
        ctrl.touch()
        yield from self.wait(lambda: True, 5)
        self.shot("sollumz-missing")

        # 11. No cloth selected, then no project open (no image chosen, so nothing is linked).
        bpy.context.scene.dct_link.image = None
        dct.broadcast({"type": "event.selection", "id": "sel1", "focused": None})
        yield from self.wait(lambda: ctrl.focused is None, 10, "no cloth")
        self.shot("no-cloth")
        dct.broadcast({"type": "event.project", "id": "prj1", "project": None})
        yield from self.wait(lambda: ctrl.project is None, 10, "no project")
        self.shot("no-project")

        # 12. Disconnected in Durty Cloth Tool.
        dct.connections_ready[-1].kick("disconnected")
        yield from self.wait(lambda: ctrl.dct_disconnected and ctrl.state == "stopped", 20, "the disconnect")
        self.shot("disconnected-in-dct")

        # 13. A Durty Cloth Tool that needs a newer add-on, and one that speaks an older link protocol.
        dct.incompatible = True
        ctrl.connect()
        yield from self.wait(lambda: ctrl.incompatible is not None, 30, "the incompatible answer")
        self.shot("addon-too-old")
        dct.incompatible = False
        if new:
            dct.major_one = True
            ctrl.connect()
            yield from self.wait(lambda: ctrl.incompatible is not None and ctrl.state == "stopped", 30,
                                 "the older Durty Cloth Tool")
            self.shot("dct-too-old")
            dct.major_one = False

        # 14. Signed out.
        ctrl.connect()
        yield from self.wait(lambda: ctrl.ready, 30, "the connection")
        ctrl.sign_out()
        yield from self.wait(lambda: ctrl.state == "stopped" and ctrl._logout_task is None, 20, "the sign-out")
        self.shot("signed-out")


def run_inside_blender() -> None:
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--prefix", default="shot")
    parser.add_argument("--expanded", action="store_true")
    parser.add_argument("--language")
    parser.add_argument("--theme", default="dark")
    parser.add_argument("--scenario", default="link")
    args = parser.parse_args(argv)
    view = bpy.context.preferences.view
    view.show_splash = False
    if hasattr(view, "use_save_prompt"):
        view.use_save_prompt = False
    shots = Shots(args)
    steps = shots.steps()

    def quit_blender() -> None:
        sys.stdout.flush()
        os._exit(0 if ok["value"] else 1)

    ok = {"value": True}

    def step():
        try:
            return next(steps)
        except StopIteration:
            pass
        except Exception:  # noqa: BLE001 - report, then quit
            ok["value"] = False
            print("ERROR " + traceback.format_exc().replace("\n", "\nERROR "))
        bpy.app.timers.register(quit_blender, first_interval=0.2)
        return None

    bpy.app.timers.register(step, first_interval=1.5)


if __name__ == "__main__":
    if bpy is None:
        sys.exit(launch())
    run_inside_blender()
