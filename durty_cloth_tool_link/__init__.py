# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2026 Schmid Software Solutions (https://schmid-software.de)
"""Durty Cloth Tool Link: stream textures and push Sollumz models from Blender into Durty Cloth Tool's preview.

This file imports nothing from Blender, so the add-on's Blender-free modules (``settings``, ``pixels``,
``bundle``, ``link`` and the vendored ``dct_link``) can be tested without Blender.
"""


def register():
    from . import addon

    addon.register()


def unregister():
    from . import addon

    addon.unregister()
