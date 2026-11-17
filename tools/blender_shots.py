#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2026 Schmid Software Solutions (https://schmid-software.de)
"""Screenshots of the DCT tab in every state, for interface reviews.

    python tools/blender_shots.py --blender <path to blender> --out <folder>
        [--source <add-on source folder>] [--prefix after] [--expanded] [--language de_DE] [--theme light]
        [--scenario garment|gloves|ped] [--text-size 14] [--scale 1.5]
        [--content content.json] [--body <folder>] [--garment <file> --garment-type hoodie] [--docs]

Builds the extension from ``--source`` (default: this repository's ``durty_cloth_tool_link``), starts a Blender
window with a throw-away user folder (``BLENDER_USER_RESOURCES``), installs the build, and walks the add-on through
its states against the fake Durty Cloth Tool and fake gta.clothing of the tests on 127.0.0.1: Durty Cloth Tool not
running, signing in, connected, live preview, saving, a pushed model, items opened from Durty Cloth Tool, no cloth,
no project, disconnected in Durty Cloth Tool, a Durty Cloth Tool that is too old, and signed out. ``--scenario
garment`` walks Garment Fitting (Experimental) instead, on a synthetic garment and body: Setup before and after a
garment and the hosted body are added, the body's view options, Fit with markers, a fit whose report names where
weights were repaired, Fix with the fit check and the problem colours, a sculpt session, the tear check beside the
game's own clothing, Game Ready after the local steps, and Add to Project (the skeleton missing and
in place, what blocks an add, Durty Cloth Tool asking, the cloth added, the free limit, no project open, not
connected). ``--scenario gloves`` walks the Gloves type (Experimental) on synthetic gloves: Setup with Body Cut on the
bare arms, Fit without markers, Fix, Game Ready with Prepare's options and Validate's two-gloves finding, and Add to
Project with Shows Skin locked on. ``--scenario ped`` walks Custom Ped (Experimental) on a synthetic mannequin: no
character, the character's checks, the markers (with the 3D view), the click guide (with the 3D view), a rig waiting
to be applied, the rigged character with its checks, and the project Durty Cloth Tool created. Each state is saved as
``<prefix>-<NN>-<state>.png`` in ``--out``, cropped to the sidebar. ``--expanded`` opens every collapsed
panel and settings group first; ``--language`` and ``--theme light`` change Blender's interface for the run;
``--text-size`` sets the interface text size in points (Blender's is 11): larger text in the same sidebar shows what
a narrower sidebar cuts off or wraps (14 points is about a sidebar a fifth narrower). ``--content``, ``--body`` and
``--garment`` show a real cloth, body and garment instead of the stand-ins, and ``--docs`` writes the figures of the
public documentation under their file names (docs/DEVELOPMENT.md, "Screenshots"). Blender
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
#: With --docs, the documentation figures that show part of the sidebar: the rows (top, bottom) in pixels from its top,
#: at Blender's default interface scale on a 175 % display. They follow the layout of the current panels and content:
#: look at each figure after a change and move the rows when the panels moved.
DOCS_ROWS = {
    "garment-fit-check": (650, 1505),
    "garment-transfer-weights": (805, 1065),
    "garment-add": (680, 1150),
    "garment-add-problems": (1180, 1420),
    "garment-add-waiting": (1030, 1262),
    "garment-add-added": (1140, 1435),
}


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
    parser.add_argument("--size", help="the window size, WIDTHxHEIGHT (default 1280x1600, with --docs 1280x2100)")
    parser.add_argument("--scenario", choices=("link", "garment", "gloves", "ped"), default="link",
                        help="which states to walk")
    parser.add_argument("--text-size", type=float, default=0.0,
                        help="the interface text size in points (default: Blender's own)")
    parser.add_argument("--scale", type=float, default=0.0,
                        help="Blender's interface resolution scale for the run (default: Blender's own)")
    parser.add_argument("--content", type=pathlib.Path,
                        help="a content.json naming the project, the cloth, its picture and paint to show")
    parser.add_argument("--body", type=pathlib.Path,
                        help="a folder with a locally built hosted body (freemode_*.glb, freemode_joints.json)")
    parser.add_argument("--garment", type=pathlib.Path, help="a .glb, .gltf or .fbx garment for Garment Fitting")
    parser.add_argument("--garment-type", default="tshirt", help="the Garment Type of --garment, for example hoodie")
    parser.add_argument("--docs", action="store_true",
                        help="write only the documentation figures, under their documentation file names")
    parser.add_argument("--timeout", type=float, default=420.0)
    args = parser.parse_args(argv)
    if args.docs and args.scenario not in ("link", "garment"):
        print("error: --docs makes figures only with the link and garment scenarios")
        return 1
    if args.size is None:
        args.size = "1280x2100" if args.docs else "1280x1600"
    for path in (args.content, args.body, args.garment):
        if path is not None and not path.exists():
            print(f"error: {path} does not exist")
            return 1
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
                   str(height)]
        if args.docs:
            command.append("--enable-event-simulate")  # to close a dialog after its figure; ignores real input
        command += ["--python", str(pathlib.Path(__file__).resolve()), "--", "--zip", str(archives[-1]),
                   "--out", str(args.out.resolve()), "--prefix", args.prefix, "--theme", args.theme,
                   "--scenario", args.scenario]
        if args.expanded:
            command.append("--expanded")
        if args.language:
            command += ["--language", args.language]
        if args.text_size:
            command += ["--text-size", str(args.text_size)]
        if args.scale:
            command += ["--scale", str(args.scale)]
        for option, path in (("--content", args.content), ("--body", args.body), ("--garment", args.garment)):
            if path is not None:
                command += [option, str(path.resolve())]
        command += ["--garment-type", args.garment_type]
        if args.docs:
            command.append("--docs")
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
        lines = [line for line in output.splitlines()
                 if line.startswith(("SHOT ", "SKIP ", "ERROR ", "CHECK "))]
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

    def capture(self, window_too: bool = False):
        """The 3D view (``window_too``: the whole window, with any open popup) as float RGBA rows, bottom row first."""
        import numpy as np

        window, area, _ = self.view()
        full = self.scratch / f"full-{self.count:02d}-{len(os.listdir(self.scratch))}.png"
        with bpy.context.temp_override(window=window, screen=window.screen, area=area):
            if window_too:
                bpy.ops.screen.screenshot(filepath=str(full), check_existing=False)
            else:
                bpy.ops.screen.screenshot_area(filepath=str(full), check_existing=False)
        image = bpy.data.images.load(str(full))
        try:
            width, height = image.size
            pixels = np.empty(width * height * 4, np.float32)
            image.pixels.foreach_get(pixels)
            return pixels.reshape(height, width, 4).copy()
        finally:
            bpy.data.images.remove(image)

    def save(self, rows, path: pathlib.Path):
        import numpy as np

        rows = np.ascontiguousarray(rows)
        out = bpy.data.images.new(f"shot_{self.count}", rows.shape[1], rows.shape[0], alpha=True)
        out.pixels.foreach_set(rows.reshape(-1))
        out.filepath_raw = str(path)
        out.file_format = "PNG"
        out.save()
        bpy.data.images.remove(out)
        print(f"SHOT {path.name}")

    def target(self, name: str, docs: "str | None") -> "pathlib.Path | None":
        """Where a shot goes: numbered by its state, or with ``--docs`` under its documentation name (``None``: a
        shot the documentation does not use, not written)."""
        self.count += 1
        if self.args.docs:
            return self.out / f"{docs}.png" if docs else None
        return self.out / f"{self.args.prefix}-{self.count:02d}-{name}.png"

    def shot(self, name: str, whole: bool = False, docs: "str | None" = None, rows: "tuple | None" = None,
             box: "tuple | None" = None):
        """Saves the sidebar (``whole``: the whole 3D view with its sidebar) as a numbered picture, or with ``--docs``
        as the documentation figure ``docs``: the sidebar down to the end of its panels, ``rows`` (top, bottom) of it
        in pixels from its top, or ``box`` (left, top, width, height) of the whole 3D view."""
        path = self.target(name, docs)
        if path is None:
            return
        window, area, region = self.view()
        pixels = self.capture()
        x0 = 0 if whole else max(0, region.x - area.x)
        y0 = 0 if whole else max(0, region.y - area.y)
        w, h = (area.width, area.height) if whole else (region.width, region.height)
        crop = pixels[y0:y0 + h, x0:x0 + w]
        if self.args.docs and box is not None:
            left, top, bw, bh = box
            crop = crop[max(0, crop.shape[0] - top - bh):crop.shape[0] - top, left:left + bw]
        elif self.args.docs and rows is not None:
            top, bottom = rows
            tabs = int(crop.shape[1] * 0.075)  # the category tabs on the right belong to the whole sidebar
            crop = crop[max(0, crop.shape[0] - bottom):crop.shape[0] - top, :crop.shape[1] - tabs]
        elif self.args.docs and not whole:
            crop = self.trim(self.whole_sidebar(crop, name), name)
        self.save(crop, path)

    @staticmethod
    def empty_rows(crop):
        """Rows (bottom row first) that equal the sidebar's plain background (Region Overlap is off with ``--docs``):
        the colour of each column in its bottom rows."""
        import numpy as np

        reference = crop[2:3, :, :3]  # the lowest rows can carry the region's edge
        return np.all(np.abs(crop[:, :, :3] - reference) < 0.004, axis=(1, 2))

    def trim(self, crop, name: str):
        """The sidebar without the empty space under its panels, apart from a small margin."""
        import numpy as np

        used = np.nonzero(~self.empty_rows(crop)[2:])[0]
        if used.size == 0:
            return crop
        margin = int(8 * bpy.context.preferences.system.ui_scale)
        return crop[max(0, used[0] + 2 - margin):]

    def whole_sidebar(self, crop, name: str):
        """The sidebar with all of its panels: when they reach its end, it is scrolled down a page at a time and the
        pictures are joined where they overlap (matched by the rows' brightness, away from the tabs on the right)."""
        import numpy as np

        if self.empty_rows(crop)[2:12].all():
            return crop  # room to spare under the panels
        window, area, region = self.view()
        tabs = int(48 * bpy.context.preferences.system.ui_scale)
        joined = crop[::-1]  # top row first from here on
        last = joined
        for _ in range(12):
            self.scroll(1)
            with bpy.context.temp_override(window=window, screen=window.screen, area=area, region=region):
                bpy.ops.wm.redraw_timer(type="DRAW_WIN_SWAP", iterations=1)
            pixels = self.capture()
            x0, y0 = max(0, region.x - area.x), max(0, region.y - area.y)
            piece = pixels[y0:y0 + region.height, x0:x0 + region.width][::-1]
            height = min(piece.shape[0], last.shape[0])
            a = last[-height:, :-tabs:3, :3].mean(axis=2)
            b = piece[:height, :-tabs:3, :3].mean(axis=2)
            best, shift = None, 0
            for d in range(0, height - 40):  # the shift that lines last's lower rows up with piece's upper rows
                error = float(np.abs(a[d:] - b[:height - d]).mean())
                if best is None or error < best - 1e-6:
                    best, shift = error, d
            if shift == 0:
                break  # the sidebar did not move: its end
            joined = np.concatenate([joined, piece[height - shift:]])
            last = piece
            if self.empty_rows(piece[::-1])[2:12].all():
                break
        else:
            print(f"CHECK {name} may be cut off: the sidebar did not end after 12 pages")
        self.scroll(-40)
        return np.ascontiguousarray(joined[::-1])

    def popup_shot(self, name: str, docs: str, before, margin: int = 0):
        """Saves the popup (a dialog or an open menu) that appeared since ``before`` (a ``capture(True)``): the box
        of the pixels that changed, ``margin`` pixels wider."""
        import numpy as np

        path = self.target(name, docs)
        if path is None:
            return
        after = self.capture(window_too=True)
        if after.shape != before.shape:
            raise RuntimeError(f"the window changed its size while {name} opened")
        changed = np.any(np.abs(after[:, :, :3] - before[:, :, :3]) > 0.004, axis=2)
        ys, xs = np.nonzero(changed)
        if ys.size == 0:
            raise RuntimeError(f"no popup appeared for {name}")
        y0, y1 = max(0, ys.min() - margin), min(after.shape[0], ys.max() + 1 + margin)
        x0, x1 = max(0, xs.min() - margin), min(after.shape[1], xs.max() + 1 + margin)
        self.save(after[y0:y1, x0:x1], path)

    # ---- the run -----------------------------------------------------------------------------------

    def steps(self):
        args = self.args
        prefs = bpy.context.preferences
        prefs.view.show_tooltips = False  # a tooltip under the pointer would cover the sidebar in a shot
        if args.language:
            prefs.view.language = args.language
            prefs.view.use_translate_interface = prefs.view.use_translate_tooltips = True
        if args.text_size:
            for style in prefs.ui_styles:
                style.widget.points = style.panel_title.points = args.text_size
        if args.scale:
            prefs.view.ui_scale = args.scale
        if args.docs:
            # A plain sidebar background, so a figure ends where the panels end (see trim).
            prefs.system.use_region_overlap = False
        self.content = self.load_content()
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
        # The install can finish after the operator returns: wait for the package before enabling it.
        installed = pathlib.Path(repo_dir) / "durty_cloth_tool_link" / "blender_manifest.toml"
        end = time.monotonic() + 30.0
        while not installed.exists() and time.monotonic() < end:
            yield 0.2
        for attempt in range(5):
            try:
                bpy.ops.preferences.addon_enable(module=package)
                break
            except RuntimeError:  # now and then the new repository's package is not importable at once
                if attempt == 4:
                    raise
                import importlib

                importlib.invalidate_caches()
                bpy.ops.extensions.repo_refresh_all()  # Blender 5.2 imports a new repository's packages only then
                yield 1.0
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
        # The fake gta.clothing expects the protocol the installed build speaks, also an older one, for comparisons.
        api.protocol = f"{protocol.PROTOCOL_MAJOR}.{getattr(protocol, 'PROTOCOL_MINOR', 0)}"
        ctrl.auth_base_url = api.base_url
        new = hasattr(link.LinkController, "open_map")
        try:
            if args.scenario == "garment" and args.docs:
                yield from self.garment_docs_states(package, ctrl, dct, api, ui, sollumz_stub)
            elif args.scenario == "garment":
                yield from self.garment_states(package, ctrl, dct, api, ui, sollumz_stub)
            elif args.scenario == "gloves":
                yield from self.gloves_states(package, ctrl, dct, api, sollumz_stub)
            elif args.scenario == "ped":
                yield from self.ped_states(package, ctrl, dct, api)
            else:
                yield from self.states(ctrl, dct, api, ui, link, sollumz_stub, new, dead_port)
        finally:
            dct.stop()
            api.stop()

    # ---- real content (--content, --body, --garment) ---------------------------------------------------

    def load_content(self):
        """The cloth of ``--content`` (the content.json of Durty Cloth Tool's panel figure recipe): its project and
        cloth names, picture (``thumbnailRgba``), texture size (``size``) and paint (a texture variation as PNG), or
        ``None``. The model comes from ``--garment``."""
        import json

        if not self.args.content:
            return None
        path = pathlib.Path(self.args.content)
        content = json.loads(path.read_text(encoding="utf-8"))
        content["folder"] = path.parent
        return content

    def content_model(self) -> str:
        """The drawable's name, for example ``jbib_016_u``."""
        c = self.content
        return f"{c['drawableType']}_{int(c['number']):03d}_u"

    def content_focused(self, binding):
        """The cloth selected in the fake Durty Cloth Tool, as context.get and event.selection report it: the
        content's last texture variation is selected, which is the one ``paint`` shows."""
        import re

        c = self.content
        textures = []
        for index, name in enumerate(c["textures"]):
            last = index == len(c["textures"]) - 1
            texture_id = binding["textureId"] if last else f"0000000{index}-1111-4222-8333-444455556666"
            textures.append({"textureId": texture_id, "name": name, "width": c["size"], "height": c["size"]})
        return {"clothId": binding["clothId"], "name": c["cloth"], "selectedTextureId": binding["textureId"],
                "textures": textures, "targets": ["diffuse", "normal"], "drawableType": c["drawableType"],
                "gender": c["gender"], "collection": re.sub(r"^mp_[mf]_freemode_01_", "", c["collection"]),
                "number": int(c["number"])}

    def content_thumbnail(self):
        c = self.content
        size = int(c["thumbnailSize"])
        return {"width": size, "height": size, "rgba": (c["folder"] / c["thumbnailRgba"]).read_bytes()}

    def content_paint(self):
        """The content's paint as a Blender image named after its texture variation."""
        c = self.content
        image = bpy.data.images.load(str(c["folder"] / c["paint"]), check_existing=False)
        image.name = c["textures"][-1]
        return image

    @staticmethod
    def rgba_rows(image) -> bytes:
        """A Blender image as RGBA8 rows, top row first (what host.openTexture carries)."""
        import numpy as np

        width, height = image.size
        pixels = np.empty(width * height * 4, np.float32)
        image.pixels.foreach_get(pixels)
        rows = pixels.reshape(height, width, 4)[::-1]
        return (np.clip(rows, 0.0, 1.0) * 255.0 + 0.5).astype(np.uint8).tobytes()

    def body_files(self):
        """The files of ``--body`` as the fake gta.clothing serves them for its body version."""
        folder = pathlib.Path(self.args.body)
        return {path.name: path.read_bytes() for path in sorted(folder.iterdir())
                if path.name.startswith("freemode") and path.suffix in (".glb", ".json")}

    def import_garment(self, name: str):
        """The garment of ``--garment`` imported as one mesh object called ``name``."""
        path = pathlib.Path(self.args.garment)
        before = set(bpy.data.objects)
        if path.suffix.lower() == ".fbx":
            bpy.ops.import_scene.fbx(filepath=str(path))
        else:
            bpy.ops.import_scene.gltf(filepath=str(path))
        added = [obj for obj in bpy.data.objects if obj not in before]
        meshes = [obj for obj in added if obj.type == "MESH"]
        others = [obj for obj in added if obj.type != "MESH"]  # named before the join frees the merged meshes
        if not meshes:
            raise RuntimeError(f"{path.name} holds no mesh")
        for obj in bpy.context.view_layer.objects:
            obj.select_set(obj in meshes)
        bpy.context.view_layer.objects.active = meshes[0]
        if len(meshes) > 1:
            self.operator(lambda: bpy.ops.object.join())
        garment = bpy.context.view_layer.objects.active
        world = garment.matrix_world.copy()  # a scaled or turned root node keeps the garment where it was
        garment.parent = None
        garment.matrix_world = world
        for obj in others:
            bpy.data.objects.remove(obj)
        garment.name = garment.data.name = name
        for material in garment.data.materials:  # the colour texture only: a normal map in a .glb is no DDS file
            tree = material.node_tree if material is not None and material.use_nodes else None
            for node in [n for n in tree.nodes if n.type == "NORMAL_MAP"] if tree is not None else ():
                for link in list(node.inputs["Color"].links):
                    tree.nodes.remove(link.from_node)
                tree.nodes.remove(node)
        return garment

    def view_shot(self, name: str, docs: str, objects, size=(1030, 1100), zoom=1.1, lift=-0.1):
        """The 3D view alone, looking at ``objects`` from the front, as the documentation figure ``docs`` (a box of
        ``size`` pixels in its middle)."""
        window, area, _ = self.view()
        space = area.spaces.active
        space.show_region_ui = False
        space.overlay.show_floor = space.overlay.show_axis_x = space.overlay.show_axis_y = False
        space.overlay.show_cursor = False
        main = next(r for r in area.regions if r.type == "WINDOW")
        for obj in bpy.context.view_layer.objects:
            obj.select_set(obj in objects)
        with bpy.context.temp_override(window=window, screen=window.screen, area=area, region=main):
            bpy.ops.view3d.view_axis(type="FRONT")
            bpy.ops.view3d.view_selected()
        for obj in objects:
            obj.select_set(False)
        r3d = space.region_3d
        r3d.view_perspective = "PERSP"
        r3d.view_distance *= zoom
        r3d.view_location.z += lift
        yield from self.wait(lambda: True, 5)
        width, height = min(size[0], main.width), min(size[1], main.height)
        self.shot(name, whole=True, docs=docs,
                  box=((area.width - width) // 2, (area.height - height) // 2, width, height))
        space.show_region_ui = True
        space.overlay.show_floor = space.overlay.show_axis_x = space.overlay.show_axis_y = True
        space.overlay.show_cursor = True
        yield from self.wait(lambda: True, 5)

    def work_on_shot(self):
        """The Work On list opened by a click on it (with --docs only, which can simulate the click)."""
        window, area, region = self.view()
        scale = bpy.context.preferences.system.ui_scale
        print(f"CHECK the interface scale is {scale:.2f}")
        # Work On is the third row of the Durty Cloth Tool panel: its list button sits at 59 % of the sidebar's
        # width, 103 interface units below its top.
        x = region.x + int(region.width * 0.59)
        y = region.y + region.height - int(103.4 * scale)
        window.event_simulate(type="MOUSEMOVE", value="NOTHING", x=x, y=y)
        yield from self.wait(lambda: True, 3)
        window.event_simulate(type="LEFTMOUSE", value="PRESS", x=x, y=y)
        window.event_simulate(type="LEFTMOUSE", value="RELEASE", x=x, y=y)
        yield 0.5
        self.redraw()
        yield 0.5
        self.shot("work-on", docs="blender-work-on", rows=(0, int(188 * scale)))
        self.press("ESC")
        window.event_simulate(type="MOUSEMOVE", value="NOTHING", x=area.x + 20, y=area.y + 20)
        yield from self.wait(lambda: True, 3)

    def press(self, key: str):
        """A key press in the window (needs Blender started with --enable-event-simulate, as --docs does)."""
        window = bpy.context.window_manager.windows[0]
        window.event_simulate(type=key, value="PRESS")
        window.event_simulate(type=key, value="RELEASE")

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
        for _ in range(4):  # let the sidebar draw a few times, so panels that move have arrived
            yield 0.2
            self.redraw()

    def operator(self, call):
        window, area, region = self.view()
        with bpy.context.temp_override(window=window, screen=window.screen, area=area, region=region):
            return call()

    # ---- the garment fitting states (--scenario garment) ---------------------------------------------------

    def show_garment(self, garment_ui, stage=None, sections=(), options=()):
        """The Garment Fitting view with ``stage`` open and the closed ``sections`` (``problems``, ``tears``...) and
        Options sections (``service``...) open too. The panel opens the stage of the next step by itself; a shot of
        another stage asks for that one instead (``None``: the panel's own choice)."""
        if not hasattr(self, "open_stage"):
            self.open_stage, self.section = garment_ui.open_stage, garment_ui.section
            self.options = garment_ui.options
        garment_ui.open_stage = self.open_stage if stage is None else (lambda context, stage=stage: stage)
        self.generation = getattr(self, "generation", 0) + 1
        original, generation = self.section, self.generation

        def section(layout, name, key, icon, info=None):
            if name not in sections:
                return original(layout, name, key, icon, info)
            header, body = layout.panel(f"dct_link_garment_section_{name}_shot{generation}", default_closed=False)
            header.label(text=garment_ui.t(key), icon=icon, translate=False)
            if info:
                garment_ui.info_button(header, info)
            return body

        def options_section(layout, context, name, original=self.options):
            if name not in options:
                return original(layout, context, name)
            header, body = layout.panel(f"dct_link_garment_{name}_shot{generation}", default_closed=False)
            header.label(text=garment_ui.t("garment.heading.options"), icon="PREFERENCES", translate=False)
            return body

        garment_ui.section = section
        garment_ui.options = options_section
        bpy.context.scene.dct_link.workspace = "GARMENT"
        self.scroll(-20)
        self.show_tab()

    def scroll(self, pages, page=True, ticks=1):
        """Scrolls the sidebar by whole pages (negative: up), for panels taller than the window; with ``page``
        False, by ``ticks`` small steps per page instead."""
        window, area, region = self.view()
        with bpy.context.temp_override(window=window, screen=window.screen, area=area, region=region):
            for _ in range(abs(pages) * (1 if page else ticks)):
                try:
                    (bpy.ops.view2d.scroll_down if pages > 0 else bpy.ops.view2d.scroll_up)(page=page)
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
        yield from self.wait(lambda: ctrl.state == "signing-in" or ctrl.ready, 30, "the sign-in")
        if not ctrl.ready:
            ctrl.sign_in()
        yield from self.wait(lambda: ctrl.ready, 30, "the connection")
        scene = bpy.context.scene
        for obj in list(scene.objects):
            bpy.data.objects.remove(obj)  # the default cube, camera and light
        props = scene.dct_garment

        # 1. Nothing chosen yet: the next step says how to start.
        self.show_garment(garment_ui, "setup")
        yield from self.wait(lambda: True, 5)
        self.shot("garment-start")

        # 2. A garment and the hosted body (from the fake gta.clothing).
        folder = pathlib.Path(tempfile.mkdtemp(prefix="dct_shots_garment_", dir=os.environ["BLENDER_USER_RESOURCES"]))
        tee = garment_smoke.panel_garment("tshirt_md", "short", 45.0)
        props.garment = tee
        props.gender = "female"
        glb = garment_smoke.body_glb(folder)
        api.body_files = {"freemode_female.glb": glb.read_bytes(),
                          **garment_smoke.synthetic_pack.body_files(("female",))}  # no game data
        garment_ui.BODY_ORIGIN["url"] = api.base_url
        self.operator(lambda: bpy.ops.dct_link.fit_add_body())
        yield from self.wait(lambda: garment_ui.RUNTIME.download is None and props.body is not None, 30,
                             "the hosted body")
        self.frame_all()
        yield from self.wait(lambda: True, 5)
        self.shot("garment-setup")
        # The panel's own choice: Setup is done (ticked and folded), and Fit opens with Auto Markers.
        self.show_garment(garment_ui)
        yield from self.wait(lambda: True, 5)
        self.shot("garment-next-stage")

        # The body's Options with the Reference Data Pack: another Body Cut, the arms as a wireframe, no legs.
        props.body_cut = "heist_00"
        props.body_arms = "wire"
        props.body_legs = "hidden"
        self.show_garment(garment_ui, "setup", options=("body",))
        yield from self.wait(lambda: True, 5)
        self.scroll(3)  # once the open Options have drawn: down to the note under them
        yield from self.wait(lambda: True, 5)
        self.shot("garment-body-view")
        props.body_cut = "full"
        props.body_arms = "solid"
        props.body_legs = "solid"
        self.show_garment(garment_ui)

        # 3. Fit: the markers placed.
        props.category = "tshirt"
        self.operator(lambda: bpy.ops.dct_link.fit_auto_markers())
        self.show_garment(garment_ui, "fit")
        yield from self.wait(lambda: True, 5)
        self.shot("garment-fit-markers")

        # 4. Aligned to the body: Fit on gta.clothing is next. Align to Body asks Durty Cloth Tool for its skeleton
        # first.
        self.operator(lambda: bpy.ops.dct_link.fit_align())
        yield from self.wait(lambda: garment_ui.RUNTIME.job is None and gh.flag(tee, "dct_aligned"), 30,
                             "the alignment")
        self.show_garment(garment_ui, "fit")
        yield from self.wait(lambda: True, 5)
        self.shot("garment-fit-aligned")

        # Fit on gta.clothing's options with Match Proportions on, so Proportion Strength shows too.
        bpy.context.scene.dct_garment.fit_proportions = True
        self.show_garment(garment_ui, "fit", options=("service",))
        self.scroll(1, page=False, ticks=12)
        yield from self.wait(lambda: True, 5)
        self.shot("garment-fit-options")
        bpy.context.scene.dct_garment.fit_proportions = False
        self.show_garment(garment_ui, "fit")

        # Fit on gta.clothing whose report says where it repaired weights that tore the garment, then taken back.
        sys.modules[package + ".state"].preferences().fit_upload_consent = True
        api.fit.body_version = props.body.get(gh.BODY_VERSION)
        api.fit.warnings = ["weights_repaired_neck", "weights_repaired_arms", "marker_offset"]
        self.operator(lambda: bpy.ops.dct_link.fit_service_fit())
        yield from self.wait(lambda: not ctrl.fitting.busy and garment_ui.RUNTIME.fit_lines, 60, "the fit")
        self.show_garment(garment_ui, "fit")
        yield from self.wait(lambda: True, 5)
        self.scroll(1)
        yield from self.wait(lambda: True, 5)
        self.shot("garment-fit-repaired")
        self.operator(lambda: bpy.ops.dct_link.fit_back_step())
        for group in [g for g in tee.vertex_groups if g.name.startswith("SKEL_")]:
            tee.vertex_groups.remove(group)
        tee.pop("dct_fitted", None)
        garment_ui.RUNTIME.fit_lines = []
        self.show_garment(garment_ui, "fit")

        # 5. Fix: the fit check and the problem colours.
        self.operator(lambda: bpy.ops.dct_link.fit_check())
        self.operator(lambda: bpy.ops.dct_link.fit_show_problems())
        self.show_garment(garment_ui, "fix", sections=("problems",))
        yield from self.wait(lambda: True, 5)
        self.shot("garment-fix-check")
        self.show_garment(garment_ui, "fix", sections=("problems", "regions", "sculpt"))
        yield from self.wait(lambda: True, 5)
        self.scroll(1)
        yield from self.wait(lambda: True, 5)
        self.shot("garment-fix-check-lower")
        self.scroll(-20)

        # 6. Fix by hand: a sculpt session, then accepted.
        self.operator(lambda: bpy.ops.dct_link.fit_sculpt_start())
        yield from self.wait(lambda: gh.sculpting(tee), 5, "the sculpt session")
        self.shot("garment-fix-sculpting")
        self.operator(lambda: bpy.ops.dct_link.fit_sculpt_accept())
        yield from self.wait(lambda: not gh.sculpting(tee), 5, "the end of the session")
        self.shot("garment-fix-accepted")

        # 7. A garment made in T-pose: brought into the A-pose, rigged by hand, its tears checked.
        tpose = garment_smoke.panel_garment("coat_tpose", "long", 0.0)
        tee.hide_set(True)
        for obj in bpy.context.view_layer.objects:
            obj.select_set(obj == tpose)
        bpy.context.view_layer.objects.active = tpose
        self.operator(lambda: bpy.ops.dct_link.fit_use_garment())
        props.category = "long_sleeve"
        props.source_pose = "t_pose"
        self.operator(lambda: bpy.ops.dct_link.fit_auto_markers())
        self.show_garment(garment_ui, "fit")
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
        self.show_garment(garment_ui, "fix", sections=("tears",))
        # The summary compares the stretch with the game's own clothing once gta.clothing's statistics arrived.
        yield from self.wait(lambda: garment_ui.game_reference(bpy.context)[0] is not None, 20, "the statistics")
        self.redraw()
        yield from self.wait(lambda: True, 5)
        self.scroll(2)  # once the panel has drawn: the sidebar knows its height
        yield from self.wait(lambda: True, 5)
        self.shot("garment-fix-tears")

        # 8. Game ready: prepare, combine materials, levels of detail, validate.
        self.operator(lambda: bpy.ops.dct_link.fit_prepare())
        self.operator(lambda: bpy.ops.dct_link.fit_combine_materials())
        props.lod_medium, props.lod_low = 600, 150
        self.operator(lambda: bpy.ops.dct_link.fit_lods())
        self.operator(lambda: bpy.ops.dct_link.fit_validate())
        self.show_garment(garment_ui, "ready")
        yield from self.wait(lambda: True, 5)
        self.shot("garment-ready")
        yield from self.garment_add_states(garment_ui, ctrl, dct, tpose, props)

    def garment_docs_states(self, package, ctrl, dct, api, ui, stub):
        """``--docs --scenario garment``: the Garment Fitting figures of the documentation, on the garment of
        ``--garment`` (or the synthetic T-shirt) and the body of ``--body`` (or the synthetic one), one garment from
        Setup to Add to Project."""
        from tests.blender import garment_smoke
        from tests.support import synthetic
        from tests.support.fake_dct import ADDED_BINDING

        garment_ui = sys.modules[package + ".ui_garment"]
        gh = sys.modules[package + ".garment_host"]
        stub.register()
        ctrl.shutdown()
        ctrl.port_override = dct.port
        dct.on_assist = api.approve
        dct.focused = None
        if self.content is not None:
            dct.project_name = self.content["project"]
        ctrl.connect()
        yield from self.wait(lambda: ctrl.state == "signing-in" or ctrl.ready, 30, "the sign-in")
        if not ctrl.ready:
            ctrl.sign_in()
        yield from self.wait(lambda: ctrl.ready, 30, "the connection")
        scene = bpy.context.scene
        for obj in list(scene.objects):
            bpy.data.objects.remove(obj)  # the default cube, camera and light
        props = scene.dct_garment
        space = self.view()[1].spaces.active
        space.shading.type = "SOLID"
        space.shading.color_type = "TEXTURE"  # the garment's own colours

        # Setup: the garment and the hosted body.
        gender = self.content["gender"] if self.content is not None else "female"
        if self.args.garment:
            name = self.content_model() if self.content is not None else pathlib.Path(self.args.garment).stem
            garment = self.import_garment(name)
        else:
            garment = garment_smoke.panel_garment("tshirt_md", "short", 45.0)
        props.garment = garment
        props.gender = gender
        if self.args.body:
            api.body_files = self.body_files()
        else:
            folder = pathlib.Path(tempfile.mkdtemp(prefix="dct_shots_garment_",
                                                   dir=os.environ["BLENDER_USER_RESOURCES"]))
            api.body_files = {f"freemode_{gender}.glb": garment_smoke.body_glb(folder).read_bytes(),
                              **garment_smoke.synthetic_pack.body_files((gender,))}  # no game data
        garment_ui.BODY_ORIGIN["url"] = api.base_url
        api.fit.per_day = 10
        props.category = self.args.garment_type
        self.operator(lambda: bpy.ops.dct_link.fit_add_body())
        yield from self.wait(lambda: garment_ui.RUNTIME.download is None and props.body is not None, 60,
                             "the hosted body")
        self.show_garment(garment_ui, "setup")
        yield from self.wait(lambda: True, 5)
        self.shot("garment-setup", docs="garment-setup")

        # Fit: the markers placed and aligned to the body. A garment made for the freemode body (a real cloth from a
        # Durty Cloth Tool project) sits on it already: the elbow and wrist markers, which Auto Markers places in the
        # middle of a loose sleeve, are moved onto the body's joints, as the panel asks a user to check them, so Align
        # to Body keeps the sleeves on the arms.
        self.operator(lambda: bpy.ops.dct_link.fit_auto_markers())
        if self.args.body and self.args.garment:
            body_joints, _ = garment_ui.joints(bpy.context)
            markers = gh.read_markers(scene, garment)
            bones = sys.modules[package + ".garment"].MARKER_JOINTS
            moved = {name: tuple(body_joints[bones[name]]) for name in markers
                     if name.startswith(("elbow", "wrist")) and body_joints and bones.get(name) in body_joints}
            gh.write_markers(scene, {**markers, **moved}, props.marker_size, garment)
            print(f"CHECK {len(moved)} of {len(markers)} markers moved onto the body's joints")
        self.operator(lambda: bpy.ops.dct_link.fit_align())
        yield from self.wait(lambda: garment_ui.RUNTIME.job is None and gh.flag(garment, "dct_aligned"), 60,
                             "the alignment")
        self.show_garment(garment_ui, "fit")
        yield from self.wait(lambda: True, 5)
        self.shot("garment-fit-aligned", docs="garment-fit")

        # Fit on gta.clothing: the question before the first upload, then the fit on its way.
        sys.modules[package + ".state"].preferences().fit_upload_consent = False
        api.fit.body_version = props.body.get(gh.BODY_VERSION)
        api.fit.warnings = []  # the markers sit on the body's joints
        api.fit.queued_polls = 0
        before = self.capture(window_too=True)
        window, area, region = self.view()
        with bpy.context.temp_override(window=window, screen=window.screen, area=area, region=region):
            bpy.ops.dct_link.fit_service_fit("INVOKE_DEFAULT")
        yield from self.wait(lambda: True, 5)
        self.popup_shot("garment-fit-consent", "garment-fit-consent", before)
        self.press("ESC")
        yield from self.wait(lambda: True, 5)
        sys.modules[package + ".state"].preferences().fit_upload_consent = True
        self.operator(lambda: bpy.ops.dct_link.fit_service_fit())
        yield from self.wait(lambda: ctrl.fitting.busy, 30, "the fit to start")
        self.show_garment(garment_ui, "fit")
        yield from self.wait(lambda: True, 3)
        self.shot("garment-fit-running", docs="garment-fit-service")
        yield from self.wait(lambda: not ctrl.fitting.busy and garment_ui.RUNTIME.fit_lines, 60, "the fit")

        # Fix: the fit check, the problem colours on the garment, Push Out of Body.
        self.operator(lambda: bpy.ops.dct_link.fit_check())
        self.operator(lambda: bpy.ops.dct_link.fit_show_problems())
        self.show_garment(garment_ui, "fix", sections=("problems",))
        yield from self.wait(lambda: True, 5)
        self.shot("garment-fix-check", docs="garment-fix")
        yield from self.view_shot("garment-problems", "garment-problems", [garment])
        self.operator(lambda: bpy.ops.dct_link.fit_push_out())
        self.operator(lambda: bpy.ops.dct_link.fit_check())
        self.show_garment(garment_ui, "fix", sections=("problems",))
        yield from self.wait(lambda: True, 5)
        self.shot("garment-fit-check", docs="garment-fit-check", rows=DOCS_ROWS["garment-fit-check"])
        if gh.problems_shown(garment):
            self.operator(lambda: bpy.ops.dct_link.fit_show_problems())  # off again
        space.shading.color_type = "TEXTURE"  # the garment's own colours
        yield from self.view_shot("garment-fit-view", "garment-fit-view", [garment])

        # Fix by hand: a sculpt session.
        self.operator(lambda: bpy.ops.dct_link.fit_sculpt_start())
        yield from self.wait(lambda: gh.sculpting(garment), 5, "the sculpt session")
        self.show_garment(garment_ui, "fix")
        yield from self.wait(lambda: True, 5)
        self.shot("garment-fix-sculpting", docs="garment-sculpting")
        self.operator(lambda: bpy.ops.dct_link.fit_sculpt_accept())
        yield from self.wait(lambda: not gh.sculpting(garment), 5, "the end of the session")

        # Game Ready: prepare and combine materials, the Durty Cloth Tool skeleton and Transfer Weights, levels of
        # detail, validate.
        dct.skeleton_files = {g: [(synthetic.skeleton_template_file(g), synthetic.skeleton_template_xml(g))]
                              for g in ("male", "female")}

        def run(call):
            try:
                self.operator(call)
            except RuntimeError:
                pass  # an operator that reports why it refused (the panel shows it)

        self.operator(lambda: bpy.ops.dct_link.fit_prepare())
        self.operator(lambda: bpy.ops.dct_link.fit_combine_materials())
        if not ctrl.ready:  # the long steps before can outlast the connection; it comes back by itself
            ctrl.connect()
            yield from self.wait(lambda: ctrl.ready and ctrl.project is not None, 30, "the connection")
        run(lambda: bpy.ops.dct_link.fit_use_skeleton())
        yield from self.wait(lambda: garment_ui.RUNTIME.job is None and garment.parent is not None
                             and garment.parent.get("dct_skeleton"), 30, "the skeleton")
        run(lambda: bpy.ops.dct_link.fit_service_weights())
        yield from self.wait(lambda: not ctrl.fitting.busy, 60, "the weights")
        self.operator(lambda: bpy.ops.dct_link.fit_lods())
        self.operator(lambda: bpy.ops.dct_link.fit_validate())
        self.show_garment(garment_ui, "ready")
        yield from self.wait(lambda: True, 5)
        self.shot("garment-ready", docs="garment-game-ready")
        self.shot("garment-weights", docs="garment-transfer-weights", rows=DOCS_ROWS["garment-transfer-weights"])
        self.show_garment(garment_ui, "none")
        yield from self.wait(lambda: True, 5)
        self.shot("garment-stages", docs="garment-stages")
        yield from self.garment_docs_add(garment_ui, ctrl, dct, garment, props, ADDED_BINDING, run)

    def garment_docs_add(self, garment_ui, ctrl, dct, garment, props, added_binding, run):
        """The Add to Project figures."""
        props.item_name = self.content["cloth"] if self.content is not None else "Top 2 T-shirt"

        def show(name, docs):
            self.show_garment(garment_ui, "add", sections=("variations",))
            yield from self.wait(lambda: True, 5)
            self.shot(name, docs=docs, rows=DOCS_ROWS.get(docs))

        # What blocks an add: a vertex group that is no bone, a colour variation without an image.
        stray = garment.vertex_groups.new(name="Group")
        props.variations.add()
        run(lambda: bpy.ops.dct_link.fit_add_to_dct())
        yield from show("garment-add-problems", "garment-add-problems")
        garment.vertex_groups.remove(stray)
        props.variations.remove(0)  # the garment's own texture is the only colour variation
        props.first_title = self.content.get("colour", "") if self.content is not None else "Black"
        ctrl.item_add.forget()  # the refused add's list goes once the problems are fixed and the add is asked again
        yield from show("garment-add", "garment-add")
        # Durty Cloth Tool shows the cloth and asks; then the user chooses Add to project.
        dct.hold_adds = True
        run(lambda: bpy.ops.dct_link.fit_add_to_dct())
        yield from self.wait(lambda: bool(dct.item_adds) and ctrl.item_add.adding, 30, "the waiting add")
        yield from show("garment-add-waiting", "garment-add-waiting")
        dct.release_adds({"ok": True, "binding": dict(added_binding),
                          "findings": []})
        yield from self.wait(lambda: not ctrl.item_add.adding, 20, "the added cloth")
        yield from show("garment-add-added", "garment-add-added")
        dct.hold_adds = False

    def garment_add_states(self, garment_ui, ctrl, dct, coat, props):
        """Add to Project, the last stage, against the fake Durty Cloth Tool."""
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
            self.show_garment(garment_ui, "add")
            yield from self.wait(lambda: True, 5)
            self.scroll(pages)
            yield from self.wait(lambda: True, 5)
            self.shot(name)

        def run(call):
            try:
                self.operator(call)
            except RuntimeError:
                pass  # an operator that reports why it refused (the panel shows it)

        # 9. The garment is not on the Durty Cloth Tool skeleton yet.
        yield from show("garment-add-skeleton-missing")
        # 10. The skeleton from Durty Cloth Tool, then what blocks an add.
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
        # 11. Durty Cloth Tool shows the cloth and asks; then the user chooses Add to project.
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
        # 12. Durty Cloth Tool's free limit.
        dct.fail["item.add"] = "item-limit"
        run(lambda: bpy.ops.dct_link.fit_add_to_dct())
        yield from self.wait(lambda: not ctrl.item_add.adding and ctrl.item_add.status is not None
                             and ctrl.item_add.status.message.key == "add.result.item-limit", 20, "the free limit")
        yield from show("garment-add-item-limit")
        del dct.fail["item.add"]
        # 13. No project open in Durty Cloth Tool, then not connected (the next step says what to do).
        del coat["dct_added"]
        ctrl.item_add.forget()
        dct.connections_ready[-1].send({"type": "event.project", "id": "prjg", "project": None})  # the live one
        yield from self.wait(lambda: ctrl.project is None, 10, "no project")
        yield from show("garment-add-no-project", pages=-20)
        ctrl.disconnect()
        yield from self.wait(lambda: not ctrl.ready, 10, "the disconnect")
        yield from show("garment-add-not-connected", pages=-20)

    # ---- the gloves states (--scenario gloves) -----------------------------------------------------------

    def gloves_states(self, package, ctrl, dct, api, stub):
        from tests.blender import garment_smoke
        from tests.support import synthetic

        garment_ui = sys.modules[package + ".ui_garment"]
        stub.register()
        ctrl.shutdown()
        ctrl.port_override = dct.port
        dct.on_assist = api.approve
        dct.focused = None
        ctrl.connect()
        yield from self.wait(lambda: ctrl.state == "signing-in" or ctrl.ready, 30, "the sign-in")
        if not ctrl.ready:
            ctrl.sign_in()
        yield from self.wait(lambda: ctrl.ready, 30, "the connection")
        scene = bpy.context.scene
        for obj in list(scene.objects):
            bpy.data.objects.remove(obj)  # the default cube, camera and light
        props = scene.dct_garment

        # 1. Gloves on the hands of the hosted body (with the synthetic Reference Data Pack): picking the type shows
        # the body with bare arms.
        folder = pathlib.Path(tempfile.mkdtemp(prefix="dct_shots_gloves_", dir=os.environ["BLENDER_USER_RESOURCES"]))
        gloves = garment_smoke.mesh_object("gloves", synthetic.gloves())
        bpy.context.view_layer.update()  # the removed objects leave the view layer
        props.garment = gloves
        props.gender = "male"
        glb = garment_smoke.body_glb(folder)
        api.body_files = {"freemode_male.glb": glb.read_bytes(),
                          **garment_smoke.synthetic_pack.body_files(("male",))}  # no game data
        garment_ui.BODY_ORIGIN["url"] = api.base_url
        self.operator(lambda: bpy.ops.dct_link.fit_add_body())
        yield from self.wait(lambda: garment_ui.RUNTIME.download is None and props.body is not None, 30,
                             "the hosted body")
        props.category = "gloves"
        self.frame_all()
        self.show_garment(garment_ui, "setup", options=("body",))
        yield from self.wait(lambda: True, 5)
        self.shot("gloves-setup")
        self.scroll(3)
        yield from self.wait(lambda: True, 5)
        self.shot("gloves-setup-body-cut")

        # 2. Fit: no markers needed; Fit on gta.clothing is next.
        self.show_garment(garment_ui, "fit")
        yield from self.wait(lambda: True, 5)
        self.shot("gloves-fit")

        # 3. Fix: Push Out of Body without a region.
        self.show_garment(garment_ui, "fix")
        yield from self.wait(lambda: True, 5)
        self.shot("gloves-fix")

        # 4. Game Ready: Prepare's options without Thickness, and Validate on a pair joined across the centre.
        joined = garment_smoke.mesh_object("gloves_joined", synthetic.gloves(joined=True))
        gloves.hide_set(True)
        props.garment = joined
        self.operator(lambda: bpy.ops.dct_link.fit_validate())
        self.show_garment(garment_ui, "ready", options=("prepare",))
        yield from self.wait(lambda: True, 5)
        self.shot("gloves-ready")
        self.scroll(2)
        yield from self.wait(lambda: True, 5)
        self.shot("gloves-ready-validate")

        # 5. Add to Project: Shows Skin on and locked.
        self.show_garment(garment_ui, "add")
        yield from self.wait(lambda: True, 5)
        self.scroll(2)
        yield from self.wait(lambda: True, 5)
        self.shot("gloves-add")

    # ---- the custom ped states (--scenario ped) -----------------------------------------------------------

    def ped_states(self, package, ctrl, dct, api):
        from tests.blender import ped_smoke

        ph = sys.modules[package + ".ped_host"]
        ui_ped = sys.modules[package + ".ui_ped"]
        ctrl.shutdown()
        ctrl.port_override = dct.port
        dct.on_assist = api.approve
        ctrl.connect()
        yield from self.wait(lambda: ctrl.state == "signing-in" or ctrl.ready, 30, "the sign-in")
        if not ctrl.ready:
            ctrl.sign_in()
        yield from self.wait(lambda: ctrl.ready, 30, "the connection")
        scene = bpy.context.scene
        scene.dct_link.workspace = "PED"
        for obj in list(bpy.data.objects):
            bpy.data.objects.remove(obj)
        yield from self.wait(lambda: True, 5, "the empty scene")
        self.shot("ped-start")

        holder = bpy.data.collections.new("Hero")
        scene.collection.children.link(holder)
        _, objects, _ = ped_smoke.build_character(holder)
        ped_smoke.select_only(objects)
        self.operator(lambda: bpy.ops.dct_link.ped_use_selected())
        self.frame_all()
        yield from self.wait(lambda: True, 5, "the character")
        self.shot("ped-checks")

        for call in (lambda: bpy.ops.dct_link.ped_apply_transforms(), lambda: bpy.ops.dct_link.ped_remove_old_rig(),
                     lambda: bpy.ops.dct_link.ped_scale(factor=0.01),
                     lambda: bpy.ops.dct_link.ped_turn(axis="Z", degrees=-90.0),
                     lambda: bpy.ops.dct_link.ped_confirm_facing(), lambda: bpy.ops.dct_link.ped_auto_markers()):
            self.operator(call)
        self.frame_all()
        yield from self.wait(lambda: True, 5, "the markers")
        self.shot("ped-markers", whole=True)

        # Started from its button in the sidebar, as a user starts it: the clicks still land in the 3D view.
        window, area, region = self.view()
        with bpy.context.temp_override(window=window, screen=window.screen, area=area, region=region):
            bpy.ops.dct_link.ped_guide("INVOKE_DEFAULT")
        guide = ui_ped.RUNTIME.guide
        if guide is None:
            raise RuntimeError("the click guide did not start from the sidebar")
        yield from self.wait(lambda: True, 3, "the front view")
        from bpy_extras import view3d_utils
        import types

        main = max((r for r in area.regions if r.type == "WINDOW"), key=lambda r: r.width * r.height)
        markers = ph.read_markers(scene.dct_ped.character)
        spot = view3d_utils.location_3d_to_region_2d(main, main.data, markers["chest"])
        event = types.SimpleNamespace(mouse_x=main.x + int(spot.x), mouse_y=main.y + int(spot.y))
        ray = ui_ped.DCTLINK_OT_ped_guide._ray(ui_ped.DCTLINK_OT_ped_guide, types.SimpleNamespace(area=area), event)
        if ray is None or guide.point(*ray) is None:
            raise RuntimeError("a click on the character in the 3D view did not reach it")
        outside = types.SimpleNamespace(mouse_x=region.x + 5, mouse_y=region.y + 5)
        if ui_ped.DCTLINK_OT_ped_guide._ray(ui_ped.DCTLINK_OT_ped_guide, types.SimpleNamespace(area=area), outside):
            raise RuntimeError("a click on the sidebar was taken as one in the 3D view")
        print("CHECK the click guide started from the sidebar reaches the character in the 3D view")
        if guide is not None:
            for name in ("headTop", "chin", "shoulderL"):
                guide.points[name] = markers[name]
            guide.preview = markers["shoulderR"]
        yield from self.wait(lambda: True, 5, "the click guide")
        self.shot("ped-guide", whole=True)
        if guide is not None:
            ui_ped.RUNTIME.guide = None
            ui_ped._guide_handlers(False)
            try:
                bpy.context.workspace.status_text_set(None)
            except (AttributeError, TypeError):
                pass

        self.operator(lambda: bpy.ops.dct_link.ped_refresh_templates())
        yield from self.wait(lambda: ctrl.peds.templates is not None, 30, "the templates")
        self.operator(lambda: bpy.ops.dct_link.ped_use_template(model="a_m_y_tester_01"))
        dct.ped_rig_warnings = [{"code": "marker_offset", "count": 2, "value": 31.0, "markers": ["elbowL", "elbowR"]}]
        dct.ped_rig_suggestion = "a_m_m_tester_02"
        dct.ped_rig_outcome = "needsReview"
        self.operator(lambda: bpy.ops.dct_link.ped_rig(agree=True))
        yield from self.wait(lambda: ctrl.peds.rig is not None, 30, "the rig")
        self.shot("ped-rig-waiting", whole=True)

        self.operator(lambda: bpy.ops.dct_link.ped_apply_rig())
        self.operator(lambda: bpy.ops.dct_link.ped_run_checks())
        yield from self.wait(lambda: True, 5, "the rigged character")
        self.shot("ped-checked", whole=True)

        self.operator(lambda: bpy.ops.dct_link.ped_send())
        yield from self.wait(lambda: ctrl.peds.created is not None, 60, "the created project")
        self.shot("ped-created")

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
        self.shot("sign-in-asked-in-dct", docs="blender-get-connected")

        # 3. Durty Cloth Tool declines: the browser code is what is left.
        answer["ok"] = False
        gate.set()
        yield from self.wait(lambda: ctrl.sign_in_status is not None
                             and ctrl.sign_in_status.message.key == "setup.sign-in.declined", 30, "the refusal")
        self.shot("sign-in-browser-code")

        # 4. Approved: connected, the focused cloth in the Linked Cloth panel.
        api.approve(dct.assisted_codes[-1])
        dct.on_assist = api.approve
        from tests.support.fake_dct import BINDING

        if self.content is not None:
            dct.project_name = self.content["project"]
            dct.thumbnail_reply = self.content_thumbnail()
            dct.texture_findings = []  # the real paint has the sizes the game expects
        dct.focused = self.content_focused(BINDING) if self.content is not None else {"clothId": "3f2b8c1e-7a4d-4e8b-9c1f-2d6e5a7b8c90", "name": "jbib_003_u",
                       "selectedTextureId": "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
                       "textures": [{"textureId": "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d", "name": "jbib_diff_003_a_uni",
                                     "width": 2048, "height": 2048},
                                    {"textureId": "b1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d", "name": "jbib_diff_003_b_uni"}],
                       "targets": ["diffuse", "normal"], "drawableType": "jbib", "gender": "female",
                       "collection": "mp_f_freemode_01", "number": 3}
        yield from self.wait(lambda: ctrl.ready and ctrl.focused is not None, 30, "the connection")
        yield 1.0  # the thumbnail
        self.shot("connected")
        if self.args.docs:
            yield from self.work_on_shot()

        # 5. Live preview with the texture checks (with --docs, Sollumz is installed already, so the Model panel shows
        #    what a user with Sollumz sees).
        if self.args.docs:
            stub.register()
        scene = bpy.context.scene
        if self.content is not None:
            image = self.content_paint()
        else:
            image = bpy.data.images.new("jacket_paint", 512, 512, alpha=True)
        scene.dct_link.image = image
        scene.dct_link.target = "diffuse"
        self.operator(lambda: bpy.ops.dct_link.live_start())
        yield from self.wait(lambda: ctrl.stream.live_state == "attached" and ctrl.stream.findings is not None,
                             30, "the live preview")
        self.shot("live", docs="blender-live-preview")

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

        # 7. A model made with Sollumz (the stand-in): not linked to a cloth yet, then linked to the cloth selected in
        #    Durty Cloth Tool, which pushes it.
        if not self.args.docs:
            stub.register()
        root, part = stub.scene()
        if self.content is not None:
            root.name = self.content_model()
        bpy.ops.object.select_all(action="DESELECT")
        part.select_set(True)
        bpy.context.view_layer.objects.active = part
        if hasattr(bpy.ops.dct_link, "model_link_focused"):
            yield from self.wait(lambda: True, 5)
            self.shot("model-not-linked")
            self.operator(lambda: bpy.ops.dct_link.model_link_focused())
        else:  # a version without Link to DCT pushes any model
            self.operator(lambda: bpy.ops.dct_link.model_push())
        yield from self.wait(lambda: ctrl.model.lease is not None, 20, "the model push")
        self.shot("model-pushed")
        self.operator(lambda: bpy.ops.dct_link.model_discard())
        yield from self.wait(lambda: ctrl.model.lease is None, 20, "the model discard")

        if new:
            # 8. A normal map opened from Durty Cloth Tool ("Edit in connected app").
            if self.content is not None:  # the paint as the diffuse map, as Edit in connected app sends it
                paint = self.content_paint()
                dct.open_texture(self.rgba_rows(paint), *paint.size, target="diffuse", name=paint.name)
                bpy.data.images.remove(paint)
            else:
                rgba = bytes((x * 7) % 256 for x in range(256 * 256 * 4))
                dct.open_texture(rgba, 256, 256, target="normal", name="jbib_normal_003")
            yield from self.wait(lambda: ctrl.stream.live_state == "attached", 20, "the opened texture")
            self.shot("opened-texture")
            self.operator(lambda: bpy.ops.dct_link.live_stop())
            yield from self.wait(lambda: not ctrl.stream.active, 10, "the stop")

            # 9. A model opened from Durty Cloth Tool.
            model, texture = ((self.content_model(), self.content["textures"][-1]) if self.content is not None
                              else ("jbib_003_u", "jbib_diff_003_a_uni"))
            dct.open_model([(f"{model}.ydd.xml", b"<DrawableDictionary />"), (f"{texture}.dds", b"DDS " + bytes(124))],
                           name=model)
            yield from self.wait(lambda: ctrl.model.lease is not None and not ctrl.model.pushing, 30, "the opened model")
            self.shot("opened-model", docs="blender-opened-from-dct")
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
    parser.add_argument("--text-size", type=float, default=0.0)
    parser.add_argument("--scale", type=float, default=0.0)
    parser.add_argument("--content")
    parser.add_argument("--body")
    parser.add_argument("--garment")
    parser.add_argument("--garment-type", default="tshirt")
    parser.add_argument("--docs", action="store_true")
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
