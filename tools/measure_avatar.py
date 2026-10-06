#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2026 Schmid Software Solutions (https://schmid-software.de)
"""Measures a Marvelous Designer or CLO stock avatar for the add-on's avatar presets.

    blender --background --factory-startup --python tools/measure_avatar.py -- <garment.fbx exported with the rigged
        avatar> [--category tshirt]

Imports the file as Import Garment does (in metres, the avatar's soles moved to the ped's ground, turned upright and to
the front), reads the joints of the rigged avatar exported with the garment in the pose it stands in, and prints them
as markers in ped space, with the pose's arm angle, ready for ``AVATARS`` in
``durty_cloth_tool_link/garment_avatars.py``.
Only these numbers belong in the repository: never the avatar, its mesh or the file. Runs inside Blender only.
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent


def main() -> int:
    import bpy  # noqa: F401 - only inside Blender

    sys.path.insert(0, str(REPO_ROOT))
    from durty_cloth_tool_link import garment_avatars
    from durty_cloth_tool_link import garment_host as gh

    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("file", help="an FBX exported with the rigged avatar")
    parser.add_argument("--category", default="tshirt", help="the garment's type, for its units (default tshirt)")
    args = parser.parse_args(argv)
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj)
    obj, info = gh.import_garment(bpy.context, pathlib.Path(args.file), ground=True, category=args.category)
    markers = garment_avatars.parse_markers(gh.stored_text(obj, gh.AVATAR_MARKERS))
    if markers is None:
        print("No rigged Marvelous Designer or CLO avatar was found in the file.")
        return 1
    print(json.dumps({"markers": {name: [round(v, 4) for v in markers[name]] for name in sorted(markers)},
                      "pose": garment_avatars.source_pose(markers), "armAngle": garment_avatars.arm_angle(markers),
                      "import": {"unit": info["unit"], "turned": info["turned"]}}, indent=1))
    return 0


if __name__ == "__main__":
    code = main()
    sys.stdout.flush()
    os._exit(code)
