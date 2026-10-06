# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2026 Schmid Software Solutions (https://schmid-software.de)
"""Every user-facing text of the add-on, in English (the neutral table and the fallback).

Logic never stores or compares displayed text: it passes keys and :class:`Msg` values (a key plus its fields),
and the interface renders them in Blender's interface language when it draws. The English text is also the
message id Blender's translation system looks up (``translations`` registers the eight other languages under
:data:`CONTEXT`). Texts use ``str.format`` fields (``{name}``); a translation keeps exactly the fields of the
English text. Logs, the system console and Copy Diagnostics stay English.

Blender conventions: labels, buttons and panel titles in Title Case; descriptions, tooltips and messages are
sentences. Product, platform and format names are never translated (Durty Cloth Tool, Creator Link,
gta.clothing, Discord, Blender, Sollumz, CodeWalker, YDD, XML, DDS, UDIM, RGB, RGBA, sRGB, Non-Color).
Nothing here imports Blender.
"""

from __future__ import annotations

import re
from typing import Any, Callable, Dict, List, Mapping, NamedTuple, Optional, Union

#: The translation context of every add-on text, so Blender's own translations of common words never apply.
CONTEXT = "DurtyClothTool"


EN: Dict[str, str] = {
    # Durty Cloth Tool's Options page that lists the connected apps (View > Connect an app opens it too), in its own
    # words and language. Texts use it as the field {apps}.
    "path.connected-apps": "Options > Connected apps",
    # Durty Cloth Tool's menu item that sends a cloth's map or model to a connected app, in its own words. Texts use
    # it as the field {edit}.
    "path.edit-in-app": "Edit in connected app",
    # ---- panels -------------------------------------------------------------------------------------------
    "panel.main": "Durty Cloth Tool",
    "panel.details": "Connection",
    "panel.setup": "Get Connected",
    "panel.linked": "Linked Cloth",
    "panel.live": "Live Preview",
    "panel.checks": "Texture Checks",
    "panel.model": "Model",
    "panel.settings": "Settings",
    # ---- header -------------------------------------------------------------------------------------------
    "chip.connected": "Connected",
    "chip.live": "Live",
    "chip.connecting": "Connecting",
    "chip.action": "Action Needed",
    "chip.offline": "Offline",
    "chip.problem": "Problem",
    "state.idle": "Not connected",
    "state.connecting": "Looking for Durty Cloth Tool",
    "state.waiting": "Durty Cloth Tool not found. Trying again",
    "state.reconnecting": "Reconnecting to Durty Cloth Tool",
    "state.hello": "Connecting",
    "state.signing-in": "Waiting for the sign-in",
    "state.authenticating": "Signing in",
    "state.ready": "Signed in as {name}",
    "state.signed-out": "Signed out",
    "state.dct-signed-out": "Durty Cloth Tool is signed out",
    "state.dct-disconnected": "Disconnected in Durty Cloth Tool",
    "details.status": "Status: {state}",
    "details.account": "Signed in as {name}",
    "details.not-signed-in": "Not signed in",
    "details.project": "Project: {name}",
    "details.addon": "Add-on {version} ({channel})",
    "online.off": (
        "Blender's online access is off, so Durty Cloth Tool cannot be connected: each connection is confirmed with "
        "your gta.clothing sign-in. Allow it in Preferences > System > Network."
    ),
    "dct-signed-out": (
        "Durty Cloth Tool is signed out. Sign in to Durty Cloth Tool, then select Connect. The add-on also tries again "
        "by itself now and then."
    ),
    "dct-disconnected": "This app was disconnected in Durty Cloth Tool. Select Connect to connect it again.",
    # ---- setup --------------------------------------------------------------------------------------------
    "setup.find.title": "Find Durty Cloth Tool",
    "setup.find.done": "Durty Cloth Tool Found",
    "setup.find.subtext": "Start Durty Cloth Tool on this computer. The add-on finds it automatically.",
    "setup.find.searching": "Looking for Durty Cloth Tool…",
    "setup.find.waiting": "Durty Cloth Tool is not running yet. The add-on keeps looking…",
    "setup.sign-in.title": "Sign In with gta.clothing",
    "setup.sign-in.done": "Signed In",
    "setup.sign-in.subtext": "Creator Link uses your gta.clothing account (Discord). You sign in once on this computer.",
    "setup.sign-in.starting": "Starting the sign-in…",
    "setup.sign-in.finding": "Looking for Durty Cloth Tool to approve the sign-in…",
    "setup.sign-in.how": "Durty Cloth Tool asks you to approve it. When it is not running, you get a code for your browser.",
    "setup.sign-in.waiting": "Waiting for approval…",
    "setup.sign-in.asked": "Durty Cloth Tool shows a sign-in request. Approve it there.",
    "setup.sign-in.approved": "Durty Cloth Tool approved the sign-in. Finishing…",
    "setup.sign-in.declined": "Durty Cloth Tool did not approve the sign-in. Sign in in the browser instead.",
    "setup.sign-in.browser-subtext": "Open the sign-in page and check that it shows this code:",
    "setup.sign-in.signed-out": "You signed out. Sign in again to use Creator Link.",
    # ---- linked cloth -------------------------------------------------------------------------------------
    "linked.project": "Project: {name}",
    "linked.no-project": "Open a project in Durty Cloth Tool.",
    "linked.no-cloth": "Select a cloth in Durty Cloth Tool to work on it here.",
    "linked.variation": "Variation {letter}",
    "linked.number": "#{number}",
    "linked.unknown": "Linked cloth",
    "linked.unknown-subtext": "Select it in Durty Cloth Tool once to see its name here.",
    "linked.map": "Map",
    "linked.follows": "Follows your selection in Durty Cloth Tool",
    "linked.image": "Linked to the image below",
    "linked.open-map": "Open a Map in Blender",
    "linked.map-missing.diffuse": "This cloth has no diffuse map.",
    "linked.map-missing.normal": "This cloth has no normal map.",
    "linked.map-missing.specular": "This cloth has no specular map.",
    "map.diffuse": "Diffuse (Colour)",
    "map.diffuse-short": "Diffuse",
    "map.diffuse.desc": "The colour texture of the cloth",
    "map.normal": "Normal",
    "map.normal.desc": "The normal map of the cloth",
    "map.specular": "Specular",
    "map.specular.desc": "The specular map of the cloth",
    "gender.male": "Male",
    "gender.female": "Female",
    # ---- opened from Durty Cloth Tool ---------------------------------------------------------------------
    "open.opened": "Opened from Durty Cloth Tool: {name}",
    "open.texture-busy": (
        "Durty Cloth Tool sent {name}, but a live preview is running or saving. Stop it, then send the map again."
    ),
    "open.texture-failed": "{name} could not be opened: {detail}",
    "open.stop-live-first": "Stop the live preview first.",
    "open.reading": "Reading the map from Durty Cloth Tool…",
    "open.map-upsell": "Opening a cloth's maps here is included in Durty Cloth Tool Ultimate.",
    "open.model-importing": "Importing {name} with Sollumz…",
    "open.model-needs-sollumz": "Durty Cloth Tool sent the model {name}. {problem}",
    "open.model-busy": (
        "Durty Cloth Tool sent the model {name}, but another model is still being pushed or saved. Send it again in "
        "a moment."
    ),
    "open.model-failed": "The model {name} could not be opened: {detail}",
    "open.import-failed": "Sollumz could not import the model ({detail}). Its Info log has the details.",
    "open.no-dictionary": "Sollumz did not import a Drawable Dictionary. Its Info log has the details.",
    "open.import-errors": (
        "Sollumz reported errors while importing the model, so it was not linked to the cloth. Its Info log has the "
        "details."
    ),
    "open.model-warnings": (
        "Opened from Durty Cloth Tool: {name}. Sollumz reported warnings; its Info log has the details."
    ),
    # ---- live preview -------------------------------------------------------------------------------------
    "live.off": "Start the live preview to see your paint on the ped.",
    "live.reading": "Reading the image…",
    "live.starting": "Starting the live preview…",
    "live.on": "Live on the ped",
    "live.sending": "Sending the image…",
    "live.not-worn": "Put this cloth on the ped in Durty Cloth Tool to see it.",
    "live.paused-dct": "The 3D preview is paused in Durty Cloth Tool.",
    "live.paused": "Paused. Your changes are sent when you resume.",
    "live.saving": "Saving…",
    "live.unsaved": "Not saved in the project yet",
    "live.linked": "Linked to {name} · {map}",
    "live.map": "Map: {map}",
    "live.save-subtext": (
        "Saving writes this map into your project. You can undo it in the cloth's History in Durty Cloth Tool."
    ),
    "live.saved": "Saved to {name}. You can undo it in History.",
    "live.saved-unnamed": "Saved to the cloth. You can undo it in History.",
    "live.saved-variation": "Saved as a new variation of {name}.",
    "live.saved-variation-unnamed": "Saved as a new variation.",
    "live.discarded": "Discarded the changes in Durty Cloth Tool.",
    "live.stopped": "Live preview stopped.",
    "live.stopped-unsaved": (
        "Live preview stopped. The changes were not saved in the project; the image in Blender keeps them."
    ),
    "live.failed": "The live preview stopped after an unexpected problem: {detail}",
    "live.upsell": "Live preview is included in Durty Cloth Tool Ultimate.",
    "live.save-upsell": "Saving to the cloth is included in Durty Cloth Tool Ultimate.",
    "live.image-changed": "The image size changed. Start the live preview again.",
    "live.image-removed": "The image was removed.",
    "live.no-memory": "Not enough memory for an image this large.",
    "colour.non-color-diffuse": "The image is set to Non-Color; its values are sent as colour unchanged.",
    "colour.unknown-diffuse": "The image's colour space {space} is sent unconverted; use sRGB for exact colours.",
    "colour.unknown-data": "Set the map's colour space to Non-Color; {space} values are sent as they are in Blender.",
    "image.none": "Choose an image first.",
    "image.tiled": "UDIM (tiled) images cannot be used. Use a single image.",
    "image.source": "Only image files and generated images can be used.",
    "image.unreadable": "The image could not be read.",
    "image.not-loaded": "The image could not be loaded. Check that its file exists.",
    "image.channels": "Only grey, RGB and RGBA images can be used.",
    "image.empty": "The image has no pixels. Open or create it first.",
    "image.too-large": "Images larger than {size} pixels on a side cannot be used.",
    "image.no-painted": "No painted image found. Choose the image in the list.",
    # ---- texture checks -----------------------------------------------------------------------------------
    "checks.errors": "Errors: {count}",
    "checks.warnings": "Warnings: {count}",
    "checks.notes": "Notes: {count}",
    "checks.clean": "No problems found.",
    "checks.not-checked": "Durty Cloth Tool checks the texture when the live preview starts.",
    "checks.checking": "Checking the texture…",
    "checks.unavailable": "Texture checks are included in Durty Cloth Tool Ultimate.",
    "severity.error": "Error",
    "severity.warning": "Warning",
    "severity.info": "Note",
    "finding.unknown": "Durty Cloth Tool reported {code}.",
    "finding.non-power-of-two": "The size is not a power of two (for example 1024 or 2048).",
    "finding.not-multiple-of-four": "The size is not a multiple of four, which compressed textures need.",
    "finding.too-large": "The texture is larger than 2048 pixels on a side, which uses a lot of game memory.",
    "finding.too-small": "The texture is smaller than 16 pixels on a side.",
    "finding.size-changed": "The size differs from the texture saved in the project.",
    "finding.palette-alpha": (
        "This cloth uses a colour palette: its alpha channel picks palette colours, so paint alpha with care."
    ),
    "finding.cutout-alpha": "This cloth uses alpha as a cut-out: transparent pixels are hidden on the ped.",
    "finding.hair-ramp": "This is hair: the game colours it with the hair colour the player picks.",
    "finding.bc1-alpha": "The saved texture keeps only fully transparent or fully opaque alpha.",
    "finding-fix.non-power-of-two": "Resize to a power of two, for example 1024 x 1024, before saving.",
    "finding-fix.not-multiple-of-four": "Resize so that both sides divide by four, for example 1024 x 512.",
    "finding-fix.too-large": "Use 2048 pixels or less on a side unless the cloth needs the extra detail.",
    "finding-fix.too-small": "Use at least 16 pixels on a side.",
    "finding-fix.size-changed": (
        "Saving replaces the texture at this size. Resize to the saved size if you did not mean to change it."
    ),
    "finding-fix.palette-alpha": "Keep the alpha values as they are unless you mean to change the palette colours.",
    "finding-fix.cutout-alpha": "Paint transparency only where the cloth should be hidden.",
    "finding-fix.hair-ramp": (
        "Paint the shading in the green channel and the highlights in the red channel, not the final colour."
    ),
    "finding-fix.bc1-alpha": "Use fully transparent or fully opaque alpha; soft edges are lost when saving.",
    # ---- model --------------------------------------------------------------------------------------------
    "model.subtext": "Sends the model again a moment after you stop editing.",
    "model.name": "Model: {name}",
    "model.sending": "Sending {name} (textures: {count})",
    "model.previewing": "Showing on the ped in Durty Cloth Tool. Save or discard it there or here.",
    "model.findings": "Durty Cloth Tool reported findings: {count}.",
    "model.warnings-paused": (
        "Sollumz reported warnings, so automatic pushing is paused. Check Sollumz's Info log, then push again to resume."
    ),
    "model.warnings": "Sollumz reported warnings; its Info log has the details.",
    "model.saving": "Saving the model in Durty Cloth Tool…",
    "model.saved": "Saved the model to the cloth. You can undo it in History.",
    "model.discarded": "Discarded the model in Durty Cloth Tool.",
    "model.save-retry": "Durty Cloth Tool is still loading the model. Saving in a moment…",
    "model.save-busy": "Durty Cloth Tool is still busy with the model. Save again in a moment.",
    "model.block.no-model": "Push a model first.",
    "model.block.saving": "Saving already.",
    "model.block.waiting": "Wait until Durty Cloth Tool answered.",
    "model.block.pushing": "Wait until the newest push shows in Durty Cloth Tool, then save.",
    "model.block.due": "Your newest changes are about to be pushed. Save once they show in Durty Cloth Tool.",
    "model.wait.tool": "The automatic push waits until the running tool finishes.",
    "model.wait.mode": "The automatic push waits until you leave {mode}.",
    "model.gone": "The pushed model is no longer in this file. Push it again.",
    "model.linked": "Linked to {name}",
    "model.linked-twice": "{name} is linked to the same cloth. Unlink one of them: each cloth takes one model.",
    "model.not-linked": "This Drawable Dictionary is not linked to a cloth.",
    "model.failed": "The automatic push failed: {detail}",
    "model.select": "Select the model to push: a Sollumz Drawable Dictionary or an object inside one.",
    "model.one-root": "Select objects of one Drawable Dictionary only.",
    "model.needs-dictionary": (
        "Durty Cloth Tool needs a Drawable Dictionary. Parent the Drawable to one (Sollumz: Create Drawable "
        "Dictionary) and push again."
    ),
    "model.not-sollumz": "Select a Sollumz Drawable Dictionary, or an object inside one.",
    "model.unhide": "Unhide the Drawable Dictionary (or an object inside it) and make it selectable, then push again.",
    "model.not-shown": "The model is not in a scene shown in a Blender window. Show its scene, then push again.",
    "model.not-in-layer": "The model is not in the current view layer. Show it, then push again.",
    "model.export-failed": "Sollumz could not export the model: {detail}",
    "model.not-exported": "Sollumz did not export the model. Its Info log has the details.",
    "sollumz.ready": "Sollumz {version}",
    "sollumz.ready-unknown": "Sollumz",
    "sollumz.missing": "Install and enable Sollumz {version} or later to open and push models.",
    "sollumz.too-old": "This Sollumz is too old to export for Durty Cloth Tool. Update to Sollumz {version} or later.",
    "sollumz.tested": "Tested with Sollumz {version}.",
    "bundle.unreadable": "The export folder could not be read ({detail}).",
    "bundle.not-dictionary": (
        "Sollumz exported a drawable or fragment, not a drawable dictionary. Durty Cloth Tool needs a Drawable "
        "Dictionary: parent your Drawable to one (Sollumz: Create Drawable Dictionary) and push again."
    ),
    "bundle.no-model": "Sollumz did not export a model. Check Sollumz's Info log for the reason.",
    "bundle.several": "Sollumz exported several drawable dictionaries ({count}). Select objects of one only.",
    "bundle.bad-name": (
        "'{name}' cannot be sent: file names may only use letters, digits, '_', '-' and '.', must not start with '.' "
        "or contain '..', and must be at most 128 characters. Rename the texture or model in Blender."
    ),
    "bundle.duplicate": "Two textures are called '{name}'. Give every texture a different name.",
    "bundle.too-many": "The model uses {count} textures; at most {limit} can be sent.",
    "bundle.empty-file": "'{name}' is empty. Export the model again.",
    "bundle.too-large": "The model and its textures are larger than {size} MiB together and cannot be sent.",
    "bundle.invalid": "The export cannot be sent: {detail}",
    # ---- settings -----------------------------------------------------------------------------------------
    "settings.connection": "Connection",
    "settings.account": "Account",
    "settings.updates": "Updates",
    "settings.privacy": "Privacy",
    "settings.models": "Models",
    "settings.connect-subtext": (
        "Needs Durty Cloth Tool on this computer. The connection stays on this computer; gta.clothing confirms your "
        "sign-in for each connection."
    ),
    "settings.signed-in-as": "Signed in as {name}",
    "settings.not-signed-in": "Not signed in",
    "settings.signed-out": "Signed out",
    "settings.sign-out-subtext": "Signing out ends the gta.clothing sign-in of this add-on on this computer.",
    "settings.device-name-subtext": "The gta.clothing approval page shows it, so you can tell your computers apart.",
    "settings.licence": "GPL-3.0-or-later, Schmid Software Solutions. Maintained by DurtyFree (Pleb Masters).",
    "settings.this-version": "This version: {version} ({channel})",
    "settings.diagnostics-copied": (
        "Diagnostics copied. Paste them in the Pleb Masters Community Discord server when you ask for help. They "
        "contain versions and status codes, no file paths and no sign-in data."
    ),
    "settings.disk-install": (
        "This copy was installed from a file, so Blender cannot update it. To get updates, drag the install "
        "link from the plugins page on gta.clothing onto Blender."
    ),
    "settings.updates-on": "Blender updates this add-on from the Durty Cloth Tool extension repository.",
    "op.plugins-page": "Get the Install Link",
    "op.plugins-page.desc": "Open the plugins page on gta.clothing, where you drag the install link onto Blender",
    "info.channel": (
        "Experimental gets new features and fixes first and changes more often. Release gets them once they "
        "are tested. You choose the channel with the install link you drag onto Blender."
    ),
    "settings.code-copied": "Code copied.",
    "channel.release": "Release",
    "channel.experimental": "Experimental",
    # ---- info popups --------------------------------------------------------------------------------------
    "info.find": (
        "Creator Link only talks to Durty Cloth Tool on this computer. Nothing is sent over the internet except your "
        "sign-in."
    ),
    "info.sign-in": (
        "Signing in shows Durty Cloth Tool that this add-on belongs to your account. The add-on never sees your "
        "Discord password. Durty Cloth Tool lists this app under {apps}, where you can disconnect it."
    ),
    "info.map": (
        "Choose which map of the cloth the image replaces in the preview: Diffuse (Colour), Normal or Specular. "
        "Diffuse images are sRGB colour; set normal and specular maps to Non-Color."
    ),
    "info.variation": (
        "Normal and specular maps belong to the model and are shared by every variation, so only Diffuse (Colour) "
        "can become a new variation."
    ),
    "info.live": (
        "The add-on reads the image when a paint stroke ends and sends what changed. Nothing is saved in your project "
        "until you choose Save to Cloth or Save as New Variation."
    ),
    "info.model": (
        "Push Model exports the selected Sollumz Drawable Dictionary as CodeWalker XML (YDD) with its textures and "
        "shows it on the linked cloth. A model sent from Durty Cloth Tool is imported, linked to its cloth and sent "
        "again after each change. Nothing is saved until you choose Save Model to Cloth."
    ),
    "info.open-map": (
        "Opens this map of the cloth from your project as an image in Blender, linked to the cloth, and starts its "
        "live preview. Durty Cloth Tool can send a map too: {edit} in the cloth's menu."
    ),
    "info.model-linked": (
        "A model opened from Durty Cloth Tool remembers its cloth, also in the saved .blend file, so its pushes always "
        "go to that cloth. A copy made with Duplicate carries the link too: unlink the one that should not be linked."
    ),
    "info.linked": (
        "An image opened from Durty Cloth Tool remembers its cloth and map, also in the saved .blend file, so its "
        "live preview always goes to that cloth. Unlink it under Live Preview to use it for the cloth selected in "
        "Durty Cloth Tool."
    ),
    "info.checks": (
        "Durty Cloth Tool checks the image against what GTA V and the cloth need, like its Error List does. Fix "
        "errors before saving; warnings and notes are advice."
    ),
    "info.privacy": (
        "Stays on this computer: your images, models and the pixels of the live preview. They go only to Durty "
        "Cloth Tool. Goes to gta.clothing: your sign-in (with this computer's name unless you turn that off), a "
        "confirmation for each connection, your sign-out and Blender's update checks."
    ),
    # ---- operators ----------------------------------------------------------------------------------------
    "op.connect": "Connect",
    "op.connect.desc": "Connect to Durty Cloth Tool on this computer",
    "op.disconnect": "Disconnect",
    "op.disconnect.desc": "Disconnect from Durty Cloth Tool. A running live preview stops",
    "op.sign-in": "Sign In",
    "op.sign-in.desc": (
        "Sign in with your gta.clothing account (Discord). Durty Cloth Tool asks you to approve it; when it is not "
        "running, you get a code for your browser"
    ),
    "op.sign-in-browser": "Sign In in the Browser",
    "op.sign-in-browser.desc": "Sign in with your gta.clothing account (Discord) on the gta.clothing page in your browser",
    "op.open-sign-in": "Open Sign-in Page",
    "op.open-sign-in.desc": "Open the gta.clothing page that approves this sign-in",
    "op.copy-code": "Copy Code",
    "op.copy-code.desc": "Copy the sign-in code to the clipboard",
    "op.cancel-sign-in": "Cancel",
    "op.cancel-sign-in.desc": "Stop waiting for the sign-in",
    "op.sign-out": "Sign Out",
    "op.sign-out.desc": "Sign out of gta.clothing in this add-on and disconnect",
    "op.update-page": "Get the Update",
    "op.update-page.desc": "Open the page with the current versions of Durty Cloth Tool and its plugins",
    "op.open-map": "Open Map",
    "op.open-map.desc": (
        "Open this map of the cloth from your project as an image linked to the cloth, and start its live preview"
    ),
    "op.unlink": "Unlink",
    "op.unlink.desc": "Stop linking this image to its cloth, so it follows your selection in Durty Cloth Tool",
    "op.unlink-model.desc": (
        "Stop linking this Drawable Dictionary to its cloth. Its next first push goes to the cloth selected in Durty "
        "Cloth Tool"
    ),
    "op.use-paint-image": "Use Painted Image",
    "op.use-paint-image.desc": "Use the image you are painting on, or the one in the Image Editor",
    "op.live-start": "Start Live Preview",
    "op.live-start.desc": "Show this image on the linked cloth and update it after each paint stroke. Nothing is saved until you save",
    "op.live-stop": "Stop Live Preview",
    "op.live-stop.desc": "Stop sending the image. The changes stay on the ped until you discard them or Durty Cloth Tool drops them",
    "op.live-pause": "Pause",
    "op.live-pause.desc": "Stop sending changes for now. The ped keeps showing the last update",
    "op.live-resume": "Resume",
    "op.live-resume.desc": "Send changes again, starting with everything changed while paused",
    "op.live-send": "Send Now",
    "op.live-send.desc": "Send the image again now, for changes made by scripts, baking or reloading",
    "op.live-save": "Save to Cloth",
    "op.live-save.desc": "Replace the map of the linked cloth with this image in your project. You can undo it in History",
    "op.live-save-variation": "Save as New Variation",
    "op.live-save-variation.desc": "Add this image to the linked cloth as a new texture variation (Diffuse (Colour) only)",
    "op.live-discard": "Discard Changes",
    "op.live-discard.desc": "Drop the changes shown on the ped and stop. Your project keeps its saved texture",
    "op.check-again": "Check Again",
    "op.check-again.desc": "Ask Durty Cloth Tool to check the image again",
    "op.model-push": "Push Model",
    "op.model-push.desc": "Export the selected Sollumz Drawable Dictionary and show it on the linked cloth. Nothing is saved until you save",
    "op.model-save": "Save Model to Cloth",
    "op.model-save.desc": "Save the pushed model in your project. The previous model stays in the cloth's History",
    "op.model-discard": "Discard",
    "op.model-discard.desc": "Drop the pushed model from the ped. Your project keeps its saved model",
    "op.diagnostics": "Copy Diagnostics",
    "op.diagnostics.desc": "Copy versions and status codes for support (no file paths and no sign-in data)",
    "op.help": "Help",
    "op.help.desc": "Open the Durty Cloth Tool documentation",
    "op.community": "Pleb Masters Community Discord",
    "op.community.desc": "Open the Pleb Masters Community Discord server, where you can ask for help",
    "op.info": "More Information",
    "op.about": "About",
    "op.about.desc": "The add-on's version, its licence, and what it sends where",
    "about.title": "Durty Cloth Tool Link {version} ({channel})",
    "op.join-discord": "Join the Discord Server",
    "op.join-discord.desc": "Open the invitation to the Pleb Masters Community Discord server in your browser",
    # ---- properties ---------------------------------------------------------------------------------------
    "prop.image": "Image",
    "prop.image.desc": "The image to show on the linked cloth",
    "prop.map": "Map",
    "prop.map.desc": "Which map of the linked cloth the image replaces in the preview",
    "prop.auto-push": "Push Automatically",
    "prop.auto-push.desc": "Send the model again a moment after you stop editing (after the first push)",
    "prop.auto-connect": "Connect Automatically",
    "prop.auto-connect.desc": "Look for Durty Cloth Tool on this computer when Blender starts",
    "prop.device-name": "Show This Computer's Name When Signing In",
    "prop.device-name.desc": "Send this computer's name with a sign-in, so the gta.clothing approval page can show which computer asks",
    "prop.delay": "Automatic Push Delay",
    "prop.delay.desc": "Seconds a pushed model must stay unchanged before Push Automatically sends it again",
    # ---- notices ------------------------------------------------------------------------------------------
    "notice.signed-in": "Signed in as {name}.",
    "notice.signing-out": "Signing out…",
    "notice.signed-out": "Signed out.",
    "notice.signed-out-local": (
        "Signed out on this computer. Allow online access in Blender's preferences to also end the session on "
        "gta.clothing."
    ),
    "notice.signed-out-unreached": (
        "Signed out on this computer; gta.clothing could not be reached. The session there ends by itself, or end it "
        "on your account page."
    ),
    "notice.browser-opens": "Your browser opens the sign-in page in a moment.",
    "notice.no-sign-in": "No sign-in is waiting.",
    "notice.not-gta-clothing": "The sign-in link is not a gta.clothing link.",
    "notice.unexpected": "The add-on hit an unexpected problem: {detail}",
    "notice.secrets-unreadable": "The stored sign-in could not be read ({detail}). Sign in again.",
    "notice.secret-store": "The protected sign-in could not be read or written. Sign in again.",
    "notice.file-error": "A file could not be read or written: {detail}",
    "notice.not-ready": "The add-on is not ready.",
    "notice.connect-first": "Connect to Durty Cloth Tool first.",
    "notice.select-cloth": "Select a cloth in Durty Cloth Tool first.",
    "notice.start-live-first": "Start the live preview first.",
    "notice.wait-saving": "Wait until saving finishes.",
    "notice.diffuse-only": "Only Diffuse (Colour) can become a new variation.",
    "notice.pushing": "A push is on its way.",
    "notice.online-off": "Blender's online access is off.",
    # ---- error codes --------------------------------------------------------------------------------------
    "error.generic": "Something went wrong.",
    "error.generic-code": "Something went wrong ({code}).",
    "error.malformed-message": "Durty Cloth Tool and this add-on did not understand each other. Update both, then try again.",
    "error.invalid-message": "Durty Cloth Tool and this add-on did not understand each other. Update both, then try again.",
    "error.unknown-message-type": "Durty Cloth Tool does not know this request. Update Durty Cloth Tool.",
    "error.unexpected-message": "Durty Cloth Tool did not expect this request right now. Try again.",
    "error.message-too-large": "The image or model was too large to send.",
    "error.unsupported-protocol": "This add-on and Durty Cloth Tool use different link versions. Update both.",
    "error.plugin-too-old": "This add-on is too old for your Durty Cloth Tool. Update the add-on.",
    "error.dct-too-old": "This Durty Cloth Tool is older than this add-on. Update Durty Cloth Tool, then select Connect.",
    "error.not-authenticated": "Sign in first.",
    "error.authentication-failed": "Durty Cloth Tool did not accept the sign-in. Trying again…",
    "error.untrusted-endpoint": (
        "A program that is not your Durty Cloth Tool answered, so nothing was sent. The add-on keeps looking for Durty "
        "Cloth Tool."
    ),
    "error.account-mismatch": "Durty Cloth Tool is signed in with another account. Sign out here and sign in with the account Durty Cloth Tool uses.",
    "error.dct-signed-out": "Durty Cloth Tool is signed out. Sign in to Durty Cloth Tool; the add-on connects by itself.",
    "error.token-invalid": "The sign-in expired. Signing in again…",
    "error.needs-license": "This needs a Durty Cloth Tool license.",
    "error.needs-ultimate": "This is included in Durty Cloth Tool Ultimate.",
    "error.no-project": "Open a project in Durty Cloth Tool first.",
    "error.no-focused-item": "Select a cloth in Durty Cloth Tool first.",
    "error.binding-in-use": "Another app is already working on this texture or model.",
    "error.binding-not-found": "The cloth or texture no longer exists in Durty Cloth Tool.",
    "error.lease-not-found": "Durty Cloth Tool ended this preview. Start it again.",
    "error.lease-limit": "Too many live previews are open. Stop one first.",
    "error.budget-exceeded": "Durty Cloth Tool's live preview memory is full. Stop another live preview.",
    "error.frame-out-of-bounds": "The image update did not fit the texture.",
    "error.frame-size-mismatch": "The image could not be sent.",
    "error.unsupported-format": "Durty Cloth Tool does not accept this format here. Push models as Sollumz YDD XML.",
    "error.stale-revision": "Newer pixels were still on their way. Save again.",
    "error.item-refused": "Durty Cloth Tool cannot edit this item (dummy, locked or protected).",
    "error.game-required": "Durty Cloth Tool needs your GTA V installation for this. Set it up in Durty Cloth Tool.",
    "error.save-failed": "Durty Cloth Tool could not save. Its status bar has the details.",
    "error.busy": "Durty Cloth Tool is busy. Try again in a moment.",
    "error.rate-limited": "Too many requests. Wait a moment and try again.",
    "error.connection-limit": "Too many apps are connected to Durty Cloth Tool.",
    "error.request-denied": "Durty Cloth Tool refused the request.",
    "error.model-rejected": "Durty Cloth Tool could not use this model. Check it in Sollumz and push again.",
    "error.internal-error": "Something went wrong. Try again, and restart Blender and Durty Cloth Tool if it keeps happening.",
    "error.item-limit": "The project has as many clothes as the free version of Durty Cloth Tool allows.",
    "error.disconnected": "The connection to Durty Cloth Tool was lost.",
    "error.timeout": "Durty Cloth Tool did not answer in time.",
    "error.superseded": "A newer request replaced this one.",
    "error.cancelled": "Cancelled.",
    "error.closed": "The live preview is closed.",
    "error.signed-out": "You signed out. Sign in to use Creator Link again.",
    "error.assertion-invalid": "The sign-in could not be confirmed. Trying again…",
    "error.pixel-source-failed": "The image could not be read for the live preview. Trying again…",
    "error.callback-failed": "Something went wrong in the add-on. Try again.",
    "error.offline": "Blender's online access is off. Allow it in Preferences > System > Network to sign in and connect.",
    "error.network": "gta.clothing could not be reached. Check the internet connection.",
    "error.invalid-response": "gta.clothing sent an unexpected answer. Try again later.",
    "error.tls": "The secure connection to gta.clothing failed. Check your network, proxy or antivirus settings.",
    "error.account_locked": "Your gta.clothing account is locked.",
    "error.discord_membership_required": "Creator Link needs your Discord account to be a member of the Pleb Masters Community Discord server.",
    "error.discord_unavailable": "Discord sign-in is unavailable right now. Try again later.",
    "error.plugin_update_required": "gta.clothing needs a newer version of this add-on. Update it.",
    "error.expired_token": "The sign-in code expired. Sign in again.",
    "error.access_denied": "The sign-in was denied.",
    "error.invalid_grant": "The sign-in was not accepted. Sign in again.",
    "error.session_invalid": "The sign-in is no longer valid. Sign in again.",
    "error.session_expired": "The sign-in expired. Sign in again.",
    "error.session_revoked": "The sign-in was ended on gta.clothing. Sign in again.",
    "error.refresh_in_progress": "Another program is renewing your sign-in. Try again in a moment.",
    # ---- closing reasons and plans ------------------------------------------------------------------------
    "close.closed": "Live preview stopped.",
    "close.replaced": "Another app took over this texture.",
    "close.itemRemoved": "The cloth was removed in Durty Cloth Tool.",
    "close.projectClosed": "The project was closed in Durty Cloth Tool.",
    "close.entitlementLost": "Your plan no longer includes this feature.",
    "close.signedOut": "Durty Cloth Tool was signed out, so the preview ended.",
    "close.disconnected": "The connection to Durty Cloth Tool was lost.",
    "feature.needsLicense": "This needs a Durty Cloth Tool license.",
    "feature.needsUltimate": "This is included in Durty Cloth Tool Ultimate.",
    "feature.unavailable": "This is not included in your Durty Cloth Tool plan.",
    # ---- garment fitting: panels and the next step ----------------------------------------------------------
    "garment.panel": "Garment Fitting (Experimental)",
    "garment.panel.setup": "Setup",
    "garment.panel.fit": "Fit",
    "garment.panel.fix": "Fix",
    "garment.panel.ready": "Game Ready",
    "garment.next.import": "Import a garment, or select yours and choose Use Selected Garment.",
    "garment.next.body": "Next: add the freemode body under Setup.",
    "garment.next.markers": "Next: place the markers with Auto Markers under Fit, then check where they are.",
    "garment.next.tpose": "Next: bring the T-pose into an A-pose under Fit.",
    "garment.next.check": "Next: run the fit check under Fix.",
    "garment.next.push": "Next: parts of the garment are inside the body. Use Push Out of Body under Fix.",
    "garment.next.prepare": "Next: Prepare Garment under Game Ready.",
    "garment.next.combine": "Next: Combine Materials under Game Ready, so the garment uses one texture.",
    "garment.next.lods": "Next: Generate LODs under Game Ready.",
    "garment.next.validate": "Next: Validate under Game Ready.",
    "garment.next.done": (
        "Done: the garment is in your Durty Cloth Tool project. Push Model and Save Model to Cloth under Model update "
        "it (included in Durty Cloth Tool Ultimate)."
    ),
    "garment.next.sculpting": "Sculpting: drag with the Grab brush, then choose Accept or Cancel under Fix.",
    # ---- garment fitting: choices -------------------------------------------------------------------------
    "garment.gender.male.desc": "The male freemode ped (mp_m_freemode_01)",
    "garment.gender.female.desc": "The female freemode ped (mp_f_freemode_01)",
    "garment.slot.jbib": "Top (jbib)",
    "garment.slot.jbib.desc": "Jackets and tops",
    "garment.slot.accs": "Undershirt (accs)",
    "garment.slot.accs.desc": "Undershirts, worn under a top",
    "garment.slot.lowr": "Legs (lowr)",
    "garment.slot.lowr.desc": "Trousers, shorts and skirts",
    "garment.slot.feet": "Shoes (feet)",
    "garment.slot.feet.desc": "Shoes and boots",
    "garment.category.vest": "Vest",
    "garment.category.vest.desc": "A top without sleeves",
    "garment.category.tshirt": "T-shirt",
    "garment.category.tshirt.desc": "A top with short sleeves",
    "garment.category.long_sleeve": "Long Sleeve",
    "garment.category.long_sleeve.desc": "A top with sleeves to the wrists",
    "garment.category.long_jacket": "Long Jacket or Tunic",
    "garment.category.long_jacket.desc": "A top with long sleeves that reaches below the hips",
    "garment.category.pants": "Pants",
    "garment.category.pants.desc": "Trousers that reach the ankles",
    "garment.category.shorts": "Shorts",
    "garment.category.shorts.desc": "Trousers that end at or above the knees",
    "garment.category.shoes": "Shoes",
    "garment.category.shoes.desc": "Shoes, boots and sandals",
    "garment.pose.a_pose": "A-pose",
    "garment.pose.a_pose.desc": "The arms point down at an angle, as the ped stands in the game",
    "garment.pose.t_pose": "T-pose",
    "garment.pose.t_pose.desc": "The arms point straight out to the sides",
    "garment.pose.custom": "Custom",
    "garment.pose.custom.desc": "Another pose: check the markers and move them to the joints by hand",
    "garment.region.shoulders": "Shoulders",
    "garment.region.upper_arms": "Upper Arms",
    "garment.region.chest": "Chest",
    "garment.region.back": "Back",
    "garment.region.waist": "Waist",
    "garment.region.hips": "Hips",
    "garment.region.neck": "Neck",
    "garment.region.legs": "Legs",
    "garment.region.desc": "A part of the garment, found from the markers",
    "garment.level.high": "High",
    "garment.level.medium": "Medium",
    "garment.level.low": "Low",
    # ---- garment fitting: properties ----------------------------------------------------------------------
    "garment.prop.garment": "Garment",
    "garment.prop.garment.desc": "The garment the tools work on. Only this object is changed",
    "garment.prop.body": "Body",
    "garment.prop.body.desc": "The freemode body the garment is measured against",
    "garment.prop.gender": "Gender",
    "garment.prop.gender.desc": "Which freemode ped the garment is for",
    "garment.prop.slot": "Slot",
    "garment.prop.slot.desc": "The clothing slot the garment goes into in Durty Cloth Tool",
    "garment.prop.category": "Category",
    "garment.prop.category.desc": "What kind of garment it is: it sets where the markers go and which regions the tools offer",
    "garment.prop.pose": "Source Pose",
    "garment.prop.pose.desc": "The pose of the avatar the garment was made on",
    "garment.prop.marker-size": "Marker Size",
    "garment.prop.marker-size.desc": "How large the marker spheres are drawn",
    "garment.prop.arm-angle": "Arm Angle",
    "garment.prop.arm-angle.desc": "How far below the horizontal T-pose to A-pose lowers the arms",
    "garment.prop.gap": "Gap (mm)",
    "garment.prop.push-gap.desc": "How far outside the body Push Out of Body moves the garment, in millimetres",
    "garment.prop.snug-gap.desc": "How far off the body Snug to Body leaves the region, in millimetres",
    "garment.prop.region": "Region",
    "garment.prop.region.desc": "The part of the garment Snug to Body and Relax Stretched work on",
    "garment.prop.amount": "Amount",
    "garment.prop.amount.desc": "How much of the way the region moves: 1 moves it all the way",
    "garment.prop.radius": "Radius (cm)",
    "garment.prop.radius.desc": "The size of the Grab brush, in centimetres",
    "garment.prop.strength": "Strength",
    "garment.prop.strength.desc": "How strongly the Grab brush moves the garment",
    "garment.prop.mirror": "Mirror X",
    "garment.prop.mirror.desc": "Sculpt both sides of the garment at once",
    "garment.prop.keep-out": "Keep Out of Body",
    "garment.prop.keep-out.desc": (
        "When you accept, move what you pushed into the body back out, to the gap of Push Out of Body"
    ),
    "garment.prop.weld": "Weld Distance (mm)",
    "garment.prop.weld.desc": "Panel edges closer than this, in millimetres, are joined into one seam",
    "garment.prop.colour-1": "Color 1",
    "garment.prop.colour-1.desc": (
        "The ped shader's first vertex colour (Sollumz's Color 1): the light the garment receives. #FF8000 suits "
        "most clothing; #FFBAFF lets emissive materials glow"
    ),
    "garment.prop.colour-2": "Color 2",
    "garment.prop.colour-2.desc": (
        "The ped shader's second vertex colour (Sollumz's Color 2): wind and sweat. Black without alpha turns both off"
    ),
    "garment.prop.overwrite": "Replace Existing Vertex Colours",
    "garment.prop.overwrite.desc": "Also replace Color 1 and Color 2 when the garment has them already",
    "garment.prop.size": "Texture Size",
    "garment.size.desc": "The size of the combined texture in pixels. Durty Cloth Tool's texture checks advise 2048 or less",
    "garment.prop.cut": "Cut Long Strips",
    "garment.prop.cut.desc": (
        "Cut long thin UV islands, such as hems and waistbands, into pieces, so the rest of the garment gets more of "
        "the texture"
    ),
    "garment.prop.lod-medium": "Medium Triangles",
    "garment.prop.lod-low": "Low Triangles",
    "garment.prop.lod.desc": "The most triangles this level of detail keeps",
    "garment.prop.ground": "Avatar Stood on the Ground",
    "garment.prop.ground.desc": (
        "The garment was made on an avatar standing at height 0, as in Marvelous Designer: move it down to the ped, "
        "whose soles are 1 m below its origin"
    ),
    "garment.prop.preset-name": "Name",
    # ---- garment fitting: headings ------------------------------------------------------------------------
    "garment.heading.markers": "Markers",
    "garment.heading.tpose": "Model in T-pose",
    "garment.heading.backups": "Backups",
    "garment.heading.push": "Clearance",
    "garment.heading.regions": "Region Tools",
    "garment.heading.problems": "Problems",
    "garment.heading.check": "Fit Check",
    "garment.heading.sculpt": "Fix by Hand",
    "garment.heading.tears": "Tears",
    "garment.heading.prepare": "Prepare",
    "garment.heading.combine": "Materials",
    "garment.heading.lods": "Levels of Detail",
    "garment.heading.validate": "Checks",
    # ---- garment fitting: operators -----------------------------------------------------------------------
    "garment.op.use": "Use Selected Garment",
    "garment.op.use.desc": "Work on the selected mesh object",
    "garment.op.import": "Import Garment",
    "garment.op.import.desc": (
        "Import a garment from an FBX, OBJ or glTF file (for example from Marvelous Designer), in metres and as one "
        "object"
    ),
    "garment.op.add-body": "Add Freemode Body",
    "garment.op.add-body.desc": (
        "Download the freemode body of the chosen gender from gta.clothing for your account (once per body version) "
        "and add it to the scene"
    ),
    "garment.op.cancel-body.desc": "Stop downloading the body",
    "garment.op.body-file": "Use a Body File",
    "garment.op.body-file.desc": "Add a body from a GLB, glTF, FBX or OBJ file instead, in metres and in the game's pose",
    "garment.op.auto-markers": "Auto Markers",
    "garment.op.auto-markers.desc": (
        "Place the joint markers (neck, chest, pelvis, shoulders, elbows, wrists, hips) from the garment's shape. Move "
        "any marker that is off"
    ),
    "garment.op.mirror": "Mirror L to R",
    "garment.op.mirror.desc": "Copy the markers of the ped's left side to its right side",
    "garment.op.save-preset": "Save Pose Preset",
    "garment.op.save-preset.desc": "Save the markers as a preset in the add-on's folder, for similar garments",
    "garment.op.load-preset": "Load Pose Preset",
    "garment.op.load-preset.desc": "Place the markers from a saved preset",
    "garment.op.tpose": "T-pose to A-pose",
    "garment.op.tpose.desc": "Lower the arms of a garment made in T-pose to the arm angle, using the markers",
    "garment.op.restore": "Restore Pre-fit",
    "garment.op.restore.desc": "Put back the garment's shape from before the first fitting step",
    "garment.op.push": "Push Out of Body",
    "garment.op.push.desc": "Move every part of the garment that is inside the body, or closer than the gap, out to the gap",
    "garment.op.snug": "Snug to Body",
    "garment.op.snug.desc": "Bring the chosen region closer to the body, down to the gap",
    "garment.op.relax": "Relax Stretched",
    "garment.op.relax.desc": "Ease stretched parts of the chosen region back towards their original size",
    "garment.op.problems": "Show Problems",
    "garment.op.problems.desc": (
        "Colour the garment: red inside the body, yellow too close, purple stretched, blue a floating shoulder. "
        "Select again to hide the colours"
    ),
    "garment.op.refresh": "Refresh",
    "garment.op.refresh.desc": "Colour the problems again after a change",
    "garment.op.check": "Run Fit Check",
    "garment.op.check.desc": "Measure how far each region of the garment stands off the body",
    "garment.op.sculpt": "Start Sculpting",
    "garment.op.sculpt.desc": "Fix the shape by hand with the Grab brush. Accept keeps the result, Cancel puts the shape back",
    "garment.op.accept": "Accept",
    "garment.op.accept.desc": "Keep the sculpted shape and end the session",
    "garment.op.cancel-sculpt.desc": "Put back the shape from before the session and end it",
    "garment.op.tears": "Check Tears",
    "garment.op.tears.desc": "Pose the garment's armature through a few test poses and show where seams open up",
    "garment.op.prepare": "Prepare Garment",
    "garment.op.prepare.desc": (
        "Join the panel seams, remove loose parts, triangulate, shade smooth and add the ped vertex colours"
    ),
    "garment.op.combine": "Combine Materials",
    "garment.op.combine.desc": "Pack all UV islands into one layout and bake the colour of every material into one texture",
    "garment.op.lods": "Generate LODs",
    "garment.op.lods.desc": (
        "Make the Medium and Low levels of detail in Sollumz's LOD slots, with the weights of the High level"
    ),
    "garment.op.validate": "Validate",
    "garment.op.validate.desc": "Check the garment for problems the game would show",
    # ---- garment fitting: setup ---------------------------------------------------------------------------
    "garment.garment.facts": "{count} vertices · materials: {materials}",
    "garment.body.hosted": "Freemode body: {gender}, version {version}",
    "garment.body.object": "Body: {name}",
    "garment.body.downloading": "Downloading the freemode body…",
    "garment.body.subtext": (
        "The body comes from gta.clothing for your signed-in account and is kept in the add-on's folder, so each "
        "version is downloaded once."
    ),
    "garment.body.cancelled": "The body download was cancelled.",
    "garment.body.offline": (
        "Blender's online access is off and no body was downloaded before. Allow online access, or use a body file."
    ),
    "garment.body.network": "gta.clothing could not be reached. Check the internet connection, or use a body file.",
    "garment.body.no-body": "gta.clothing has no freemode body for this channel yet. Use a body file for now.",
    "garment.body.signed-out": "The sign-in is no longer valid. Sign in again, then add the body.",
    "garment.body.not-entitled": "Your account cannot download the freemode body.",
    "garment.body.refused": "gta.clothing refused the download.",
    "garment.body.update": "gta.clothing needs a newer version of this add-on for the body. Update it.",
    "garment.body.busy": "Too many downloads at once. Wait a moment and try again.",
    "garment.body.unavailable": "The freemode body is unavailable right now. Try again later.",
    "garment.body.invalid": "gta.clothing sent something that is not a body. Try again later.",
    "garment.body.disk": "The body could not be saved in the add-on's folder.",
    # ---- garment fitting: fit -----------------------------------------------------------------------------
    "garment.markers.count": "Markers placed: {count} of {total}",
    "garment.presets.none": "No saved presets yet",
    "garment.backups.count": "Backups kept: {count} of {limit}",
    # ---- garment fitting: fix -----------------------------------------------------------------------------
    "garment.problem.inside": "Inside the body",
    "garment.problem.close": "Too close to the body",
    "garment.problem.stretched": "Stretched",
    "garment.problem.floating": "Floating shoulder",
    "garment.check.none": "Run the fit check to see how far each region stands off the body.",
    "garment.check.measured": "Measured (mm)",
    "garment.check.value": "{p50} ({p10} to {p90})",
    "garment.check.inside": "Inside the body: {count} vertices ({share} %)",
    "garment.advice.shoulders": "The shoulders stand off the body: Snug to Body with Shoulders brings them down.",
    "garment.sculpt.running": "Drag with the Grab brush to move the garment. The body shows as a wireframe.",
    "garment.sculpt.subtext": "Accept keeps the shape; Cancel puts back the shape from before the session.",
    "garment.pose.arms-up": "Arms up",
    "garment.pose.arms-forward": "Arms forward",
    "garment.pose.legs-forward": "Legs forward",
    "garment.pose.twist": "Twist",
    "garment.tears.pose": "{pose}: {count} seam points open, up to {gap} mm",
    "garment.tears.pose-clean": "{pose}: no seam opens",
    # ---- garment fitting: game ready ----------------------------------------------------------------------
    "garment.validate.clean": "CLEAN: nothing to fix.",
    "garment.finding.non-finite": "{count} points have broken coordinates.",
    "garment.finding.no-uv": "The garment has no UV map, so it cannot show a texture.",
    "garment.finding.uv-outside": "{count} UV points lie outside the 0 to 1 square; the game repeats the texture there.",
    "garment.finding.uv-area": "The UV layout uses only {area} % of the texture.",
    "garment.finding.no-weights": "Not rigged yet: weight the garment to the freemode skeleton's bones.",
    "garment.finding.unweighted": "{count} vertices have no weights; the game leaves them behind when the ped moves.",
    "garment.finding.influences": "{count} vertices are moved by more than {limit} bones; the game uses only {limit}.",
    "garment.finding.colour-missing": "Color 1 is missing. Prepare Garment adds it.",
    "garment.finding.colour-format": (
        "Color 1 is not a face corner byte colour, as Sollumz needs it. Prepare Garment replaces it."
    ),
    "garment.finding.vertices": (
        "The {level} level has {count} game vertices, more than the {budget} the add-on advises."
    ),
    "garment.finding.inside": "{share} % of the garment is inside the body.",
    "garment.finding.materials": "The garment has {count} materials. Combine Materials makes one texture of them.",
    # ---- garment fitting: why a button is unavailable -----------------------------------------------------
    "garment.why.no-garment": "Import a garment or choose one under Setup first.",
    "garment.why.not-shown": "The garment is not in the current view layer.",
    "garment.why.sculpting": "Accept or cancel the sculpt session first.",
    "garment.why.object-mode": "Switch to Object Mode first.",
    "garment.why.shape-keys": "The garment has shape keys. Apply or remove them first.",
    "garment.why.empty": "The garment has no geometry.",
    "garment.why.no-body": "Add the freemode body under Setup first.",
    "garment.why.no-markers": "Shoes need no markers.",
    "garment.why.downloading": "The body is being downloaded.",
    "garment.why.sign-in": "Sign in with gta.clothing first (Get Connected), or use a body file.",
    "garment.why.select-mesh": "Select a mesh object first.",
    "garment.why.is-body": "This is the freemode body, not a garment.",
    "garment.why.no-file": "Choose a file.",
    "garment.why.file-type": "Only FBX, OBJ, GLB and glTF files can be imported.",
    "garment.why.markers": "Place the markers under Fit first.",
    "garment.why.preset-name": "Give the preset a name with letters or digits.",
    "garment.why.preset-unreadable": "The preset could not be read: {detail}",
    "garment.why.tops-only": "Only tops have arms to lower.",
    "garment.why.no-backup": "There is no backup yet. One is kept before each step that changes the garment.",
    "garment.why.region-category": "This region is not part of the chosen category.",
    "garment.why.region-empty": "The garment has nothing in the region {region}.",
    "garment.why.no-session": "No sculpt session is running.",
    "garment.why.no-armature": "Checking tears needs an armature and weights on the garment.",
    "garment.why.no-weights": "The garment has no weights to pose it with.",
    "garment.why.modifiers": "A modifier changes the garment's geometry. Tears can only be checked without it.",
    "garment.why.no-uv": "The garment has no UV map.",
    "garment.why.empty-slot": "Every material slot of the garment needs a material.",
    "garment.why.uv-full": "The garment has as many UV maps as Blender allows. Remove one first.",
    "garment.why.no-sollumz": "Generating LODs needs Sollumz.",
    "garment.why.show-high": "Show the High level of detail in Sollumz first.",
    "garment.why.no-download": "No body is being downloaded.",
    "garment.error.import": "The file could not be imported: {detail}",
    "garment.error.no-mesh": "The file holds no mesh.",
    "garment.error.mode": "Sculpt Mode could not be started: {detail}",
    "garment.error.bake": "Baking failed: {detail}",
    "garment.marker-error.no-markers": "This category needs no markers.",
    "garment.marker-error.too-small": "The garment is too small or too flat for markers. Check that it is in metres.",
    "garment.marker-error.not-a-top": (
        "The garment does not look like a top. Check the category, or place the markers by hand."
    ),
    "garment.marker-error.no-sleeves": "No sleeves were found. Choose Vest, or place the arm markers by hand.",
    "garment.marker-error.not-legs": (
        "No trouser legs were found. Check the category, or place the markers by hand."
    ),
    # ---- garment fitting: results -------------------------------------------------------------------------
    "garment.done.use": "Working on {name}.",
    "garment.done.import": "Imported {name} ({count} vertices).",
    "garment.done.body": "Added the freemode body ({gender}, version {version}).",
    "garment.done.body-file": "Added {name} as the body.",
    "garment.done.markers": "Placed {count} markers. Move any that are off before fitting.",
    "garment.done.mirror": "Mirrored the left markers to the right.",
    "garment.done.preset-saved": "Saved the pose preset {name}.",
    "garment.done.preset-loaded": "Loaded the pose preset {name}.",
    "garment.done.tpose": "Lowered the arms by {angle}°. A backup was kept.",
    "garment.done.tpose-none": "The arms are at the arm angle already.",
    "garment.done.restore": "Put back the shape from before the first fitting step.",
    "garment.done.push": "Moved {moved} vertices. Inside the body: {before} before, {after} now.",
    "garment.done.snug": "Brought {moved} vertices of {region} closer to the body ({mean} mm on average).",
    "garment.done.relax": "Relaxed {moved} vertices of {region}.",
    "garment.done.relax-smooth": (
        "Smoothed {moved} vertices of {region} (the shape from before fitting is not there to compare with)."
    ),
    "garment.done.problems": "Inside: {inside}, too close: {close}, stretched: {stretched}, floating: {floating}.",
    "garment.done.check": "Fit check done. Inside the body: {inside} vertices.",
    "garment.done.sculpt-start": "Sculpt session started.",
    "garment.done.accept": "Kept the sculpted shape: moved {moved} vertices. Inside the body: {before} before, {after} now.",
    "garment.done.cancel-sculpt": "Sculpting cancelled: the garment is back to its shape from before the session.",
    "garment.done.tears": "{count} seam vertices open up in a test pose. They are in the vertex group DCT Tears.",
    "garment.done.no-tears": "No seam opens in the test poses.",
    "garment.done.tears-welded": "The garment has no open seams that could tear.",
    "garment.done.prepare": (
        "Prepared: joined {welded} seam vertices, removed {removed} loose vertices, {triangles} triangles."
    ),
    "garment.done.prepare-lining": (
        "Prepared: joined {welded} seam vertices (a lining was found and kept apart), removed {removed} loose "
        "vertices, {triangles} triangles."
    ),
    "garment.done.combine": (
        "Combined {count} materials into one texture of {size} pixels; the layout uses {used} % of it ({cut} strips "
        "cut)."
    ),
    "garment.done.lods": "Levels of detail: High {high}, Medium {medium}, Low {low} triangles.",
    "garment.done.clean": "Validate: CLEAN.",
    "garment.done.findings": "Validate found things to look at: {count}.",
    # ---- garment fitting: help ----------------------------------------------------------------------------
    "garment.info.pose": (
        "Choose the pose of the avatar the garment was made on. A garment made in T-pose can be brought into the "
        "game's A-pose under Fit."
    ),
    "garment.info.garment": (
        "The tools change only this object. Import Garment converts centimetres and millimetres (as Marvelous "
        "Designer exports them) to metres. Each step that changes the garment keeps a backup, and Ctrl+Z undoes it."
    ),
    "garment.info.body": (
        "The freemode body is downloaded from gta.clothing once per version and kept in the add-on's folder. It is "
        "added to the scene as its own object, and the tools never change it."
    ),
    "garment.info.markers": (
        "The markers stand for the ped's joints: neck, chest, pelvis, shoulders, elbows, wrists and hips. Auto "
        "Markers places them from the garment's shape; move any that are off. Mirror L to R copies the left side to "
        "the right."
    ),
    "garment.info.tpose": (
        "For garments made in T-pose: a temporary armature built from the markers lowers the arms to the arm angle "
        "and is removed afterwards. The markers follow."
    ),
    "garment.info.backups": (
        "Before each step that changes the garment, a copy of its mesh is kept in the .blend file (the first one "
        "and the newest ones). Restore Pre-fit puts the first one back."
    ),
    "garment.info.push": (
        "Moves everything inside the body, or closer than the gap, to the gap outside it. The vertices around "
        "follow, so no crease forms."
    ),
    "garment.info.regions": (
        "Snug to Body pulls a loose region towards the body, down to the gap. Relax Stretched eases stretched parts "
        "back towards their original size. The edges of the region blend in."
    ),
    "garment.info.problems": (
        "Colours the garment while you work: red inside the body, yellow too close, purple stretched compared with "
        "its original shape, blue a shoulder that floats off the body."
    ),
    "garment.info.check": (
        "Measures how far each region of the garment stands off the body: the middle value and the range of most "
        "of its vertices, in millimetres. Negative values are inside the body."
    ),
    "garment.info.sculpt": (
        "Sculpt Mode with the Grab brush, the body as a wireframe. Accept keeps the shape (and moves what went into "
        "the body back out when Keep Out of Body is on); Cancel puts back the shape from before."
    ),
    "garment.info.tears": (
        "Needs an armature and weights on the garment. The garment is posed through a few test poses (arms up, arms "
        "forward, legs forward, a twist), and the seams that open are reported."
    ),
    "garment.info.prepare": (
        "Joins the seams between panels (never a lining onto its shell), removes loose parts, triangulates, shades "
        "smooth and gives the garment Sollumz's vertex colours Color 1 and Color 2 with the values above."
    ),
    "garment.info.combine": (
        "Packs all UV islands into one square and bakes the colour of every material into one texture, which "
        "becomes the garment's only material. The original UV map is kept as DCT Source UV. Transparency is not "
        "baked."
    ),
    "garment.info.lods": (
        "Decimates a copy of the garment to each triangle budget and puts it into Sollumz's Medium and Low LOD "
        "slots; their weights come from the High level."
    ),
    "garment.info.validate": (
        "Quick local checks: weights, more than four bones per vertex, broken coordinates, the UV layout, vertex "
        "colours, the vertices of each level of detail and how much is inside the body."
    ),
    # ---- garment fitting: adding to Durty Cloth Tool --------------------------------------------------------
    "garment.next.validate-problems": "Next: fix what Validate lists under Game Ready, then validate again.",
    "garment.next.adding": "Adding: Durty Cloth Tool shows the cloth. Choose Add to project or Cancel there.",
    "garment.next.connect": "Next: connect to Durty Cloth Tool (Get Connected) to add the garment to a project.",
    "garment.next.project": "Next: open a project in Durty Cloth Tool, then add the garment under Game Ready.",
    "garment.next.sollumz": "Next: install Sollumz to add the garment to Durty Cloth Tool.",
    "garment.next.skeleton": (
        "Next: Use Durty Cloth Tool Skeleton under Game Ready, or Add to Durty Cloth Tool Project, which does it too."
    ),
    "garment.next.add": "Next: Add to Durty Cloth Tool Project under Game Ready.",
    "add.heading": "Add to Durty Cloth Tool",
    "add.heading.variations": "Colour Variations",
    "add.heading.skeleton": "Freemode Skeleton",
    "add.target": "It goes in as {slot}, {gender}. Change both under Setup.",
    "add.variation.none": "No colour texture yet",
    "add.variations.subtext": "Variations: {count} of at most {limit}.",
    "add.prop.name": "Cloth Name",
    "add.prop.name.desc": "The name the cloth gets in Durty Cloth Tool. Empty: the garment's name",
    "add.prop.skin": "Shows Skin",
    "add.prop.skin.desc": (
        "The cloth shows some of the ped's skin, so the game colours it with the ped's skin tone (the _r variant)"
    ),
    "add.prop.image": "Variation Image",
    "add.prop.image.desc": "The colour texture of this variation, in the layout of the garment's own texture",
    "add.prop.variation-name": "Variation Name",
    "add.prop.variation-name.desc": "The name of this colour variation in Durty Cloth Tool. Empty: the image's name",
    "add.prop.first-name.desc": (
        "The name of the first colour variation (the garment's own texture) in Durty Cloth Tool. Empty: the image's name"
    ),
    "add.op.skeleton": "Use Durty Cloth Tool Skeleton",
    "add.op.skeleton.desc": (
        "Get the freemode skeleton of the gender under Setup from Durty Cloth Tool and put the garment on it, ready "
        "for Sollumz"
    ),
    "add.op.add": "Add to Durty Cloth Tool Project",
    "add.op.add.desc": (
        "Check the garment, export it with Sollumz and add it as a new cloth to the project open in Durty Cloth Tool. "
        "Durty Cloth Tool asks you first"
    ),
    "add.op.cancel.desc": "Stop the add. While Durty Cloth Tool still asks, nothing is added",
    "add.op.add-variation": "Add Colour Variation",
    "add.op.add-variation.desc": "Add another image as a colour variation of the cloth",
    "add.op.remove-variation": "Remove",
    "add.op.remove-variation.desc": "Remove this colour variation",
    "add.info": (
        "Adds the garment as a new cloth to the project open in Durty Cloth Tool. Durty Cloth Tool shows it first, "
        "and nothing is added unless you choose Add to project there. It needs Durty Cloth Tool with a project open "
        "and the game set up there, and Sollumz."
    ),
    "add.info.variations": (
        "The garment's own texture is the first colour variation. Add more with other images in the same layout; "
        "each becomes a colour variation of the cloth, with the name you give it."
    ),
    "add.info.skeleton": (
        "Durty Cloth Tool sends the freemode skeleton of the gender under Setup, made from your game files. Sollumz "
        "imports it as an armature, and the garment is parented to it with an Armature modifier; its vertex groups "
        "keep their bone names. Add does this for you when it is needed."
    ),
    "add.skeleton.ready": "On the {gender} Durty Cloth Tool skeleton ({count} bones): {name}",
    "add.skeleton.missing": (
        "The garment is not on the Durty Cloth Tool skeleton yet. Use Durty Cloth Tool Skeleton, or Add, which does it "
        "for you."
    ),
    "add.skeleton.other-gender": (
        "The garment is on the {gender} skeleton. Use Durty Cloth Tool Skeleton to move it to the skeleton of the "
        "gender under Setup."
    ),
    "add.skeleton.modifier": (
        "The garment's Armature modifier does not use its Durty Cloth Tool skeleton. Use Durty Cloth Tool Skeleton "
        "again."
    ),
    "add.skeleton.order": (
        "The skeleton's bones are not in the game's order, so the weights would move the wrong bones. Use Durty Cloth "
        "Tool Skeleton again instead of changing its bones."
    ),
    "add.skeleton.bones": (
        "The skeleton has {count} bones, but the freemode skeleton has {expected}. Use Durty Cloth Tool Skeleton again "
        "instead of changing its bones."
    ),
    "add.skeleton.import": "Sollumz did not import the skeleton as one armature. Its Info log has the details.",
    "add.skeleton.invalid": "Durty Cloth Tool sent a skeleton the add-on cannot read. Update both, then try again.",
    "add.skeleton.game-required": (
        "Durty Cloth Tool needs your GTA V installation for the freemode skeleton. Set up the game in Durty Cloth "
        "Tool, then try again."
    ),
    "add.skeleton.busy": "Durty Cloth Tool is still reading the game files. Try again in a moment.",
    "add.dct-too-old": "This Durty Cloth Tool cannot add clothes from Blender yet. Update Durty Cloth Tool.",
    "add.done.skeleton": "The garment is on the {gender} Durty Cloth Tool skeleton ({count} bones): {name}.",
    "add.fetching": "Getting the {gender} freemode skeleton from Durty Cloth Tool…",
    "add.progress.skeleton": "Getting the freemode skeleton from Durty Cloth Tool…",
    "add.sent": "Sent {name} with {count} colour variations. Choose Add to project in Durty Cloth Tool.",
    "add.waiting": "Durty Cloth Tool shows the cloth. Choose Add to project or Cancel there.",
    "add.waiting.subtext": (
        "Nothing is added until you choose Add to project in Durty Cloth Tool. Cancel here withdraws the add."
    ),
    "add.withdrawing": "Cancelling the add…",
    "add.blocked": "The add is blocked: {count} problems to fix first, listed under Game Ready.",
    "add.problems": "Fix these first ({count}):",
    "add.findings": "Durty Cloth Tool's checks: {count}",
    "add.added.subtext": (
        "The Drawable Dictionary is linked to the new cloth: Push Model and Save Model to Cloth under Model update it "
        "(included in Durty Cloth Tool Ultimate)."
    ),
    "add.invalid": "The add cannot be sent: {detail}",
    "add.why.connect": "Connect to Durty Cloth Tool to add the garment to a project.",
    "add.why.no-project": "Open a project in Durty Cloth Tool to add the garment to it.",
    "add.why.adding": "An add is waiting for Durty Cloth Tool.",
    "add.why.fetching": "Waiting for the freemode skeleton from Durty Cloth Tool.",
    "add.why.nothing-running": "Nothing is running.",
    "add.why.no-template": "Durty Cloth Tool sent no freemode skeleton. Try again.",
    "add.why.garment-changed": "Another garment was chosen meanwhile, so the step did not run. Run it again.",
    "add.why.no-weights": (
        "The garment has no weights for the freemode skeleton yet. Weight it to the skeleton's bones (vertex groups "
        "named after them, such as SKEL_Spine3)."
    ),
    "add.why.unknown-groups": (
        "{count} vertex groups are no bones of the freemode skeleton: {names}. Rename or remove them; the game would "
        "move them with the root."
    ),
    "add.why.name-empty": "Give the cloth a name.",
    "add.why.name-invalid": "The cloth's name may have at most {limit} characters and no control characters.",
    "add.why.combine": (
        "The garment has {count} materials. Combine Materials first: each colour variation is one texture."
    ),
    "add.why.no-diffuse": "The garment's material has no colour texture. Combine Materials makes one.",
    "add.why.variation-empty": "Colour variation {number} has no image. Choose one, or remove the row.",
    "add.why.too-many": "A cloth has at most {limit} colour variations.",
    "add.why.variation-twice": "The image {name} is used for two colour variations. Each needs its own.",
    "add.why.too-large": (
        "The model and its pictures are larger than {size} MiB together and cannot be sent. Use smaller images or fewer "
        "colour variations."
    ),
    "add.why.work-folder": "The add-on's folder for the export is a link to another place, so it is not used.",
    "add.why.convert": "Sollumz could not make the garment a Drawable Model ({detail}).",
    "add.why.material": "Sollumz could not give the garment the ped shader ({detail}).",
    "add.picture.empty": "The image {name} has no pixels.",
    "add.picture.too-large": (
        "The image {name} is larger than {size} pixels on a side, which Durty Cloth Tool does not take."
    ),
    "add.picture.not-multiple-of-four": (
        "The image {name} is {width} x {height}: Durty Cloth Tool needs both sides to divide by four."
    ),
    "add.picture.non-power-of-two": (
        "The image {name} is {width} x {height}, not a power of two (for example 1024 or 2048)."
    ),
    "add.picture.large": "The image {name} is larger than {size} pixels on a side, which uses a lot of game memory.",
    "add.picture.small": "The image {name} is smaller than {size} pixels on a side.",
    "add.picture.unusable": "The image {name} cannot be sent: {problem}",
    "add.export.empty": (
        "Sollumz exported the Drawable Dictionary without the garment's geometry. Its Info log has the details."
    ),
    "add.export.several": "Sollumz exported {count} drawables; Durty Cloth Tool takes one per cloth.",
    "add.export.skeleton": "The export still holds the skeleton. Update Sollumz, then try again.",
    "add.export.errors": (
        "Sollumz reported errors while exporting, so part of the garment may be missing. Its Info log has the details."
    ),
    "add.export.unreadable": "The export could not be read ({detail}).",
    "add.export.warnings": "Sollumz reported warnings while exporting; its Info log has the details.",
    "add.result.added": "Added {name} to the project as {slot}.",
    "add.result.added-unlinked": (
        "Added {name} to the project, but the model in Blender could not be linked to it ({detail})."
    ),
    "add.result.denied": "Durty Cloth Tool did not add the cloth: Cancel was chosen there. The project is unchanged.",
    "add.result.withdrawn": "The add was cancelled. The project is unchanged.",
    "add.result.cancel-unanswered": (
        "The add was cancelled, but Durty Cloth Tool did not confirm it. Check the project in Durty Cloth Tool."
    ),
    "add.result.timeout": "Durty Cloth Tool did not answer the add in time. Check the project in Durty Cloth Tool.",
    "add.result.disconnected": (
        "The connection to Durty Cloth Tool was lost during the add. Check the project in Durty Cloth Tool before you "
        "add the garment again."
    ),
    "add.result.item-limit": (
        "Durty Cloth Tool did not add the cloth: the project already has as many clothes as your plan in Durty Cloth "
        "Tool allows, or the cloth has more colour variations than the plan allows for one cloth. Durty Cloth Tool "
        "sets and checks these limits, not the add-on."
    ),
    "add.result.rejected": (
        "Durty Cloth Tool could not use the model or a colour variation, so nothing was added. Its checks below say why."
    ),
    "add.result.no-project": "Open a project in Durty Cloth Tool first, then add the garment again.",
    "add.result.item-refused": (
        "This project takes no freemode clothes this way (for example a custom ped project). Open a freemode project in "
        "Durty Cloth Tool."
    ),
    "add.result.busy": (
        "Durty Cloth Tool is busy (a build runs, or another add waits for an answer). Try again in a moment."
    ),
    "add.result.rate-limited": "Too many adds in a short time. Wait a few seconds, then try again.",
    "add.result.save-failed": "Durty Cloth Tool could not add the cloth. Its status bar has the details.",
    "add.finding.rig-invalid": (
        "The weights or bone indices do not fit the freemode skeleton: the cloth would move wrongly in the game."
    ),
    "add.finding.rig-unchecked": "Durty Cloth Tool could not read the weights to check them.",
    "add.finding.single-bone-rig": (
        "One bone carries nearly all of a level of detail's weight, so the cloth would hardly move with the body."
    ),
    "add.finding.hair-tint-unsupported": "This hair cannot take the hair colour the player picks.",
    "add.finding.picture.non-power-of-two": (
        "A colour variation's size is not a power of two (for example 1024 or 2048)."
    ),
    "add.finding.picture.not-multiple-of-four": "A colour variation's size does not divide by four.",
    "add.finding.picture.too-large": (
        "A colour variation is larger than Durty Cloth Tool advises (2048 pixels on a side; it takes at most 4096)."
    ),
    "add.finding.picture.too-small": "A colour variation is smaller than 16 pixels on a side.",
    "garment.body.compressed": (
        "This Blender cannot read the compressed freemode body. Use Blender 5.2 or later, or a body file, until "
        "gta.clothing offers the uncompressed body."
    ),
    "add.result.added-late": (
        "Durty Cloth Tool added {name} after all: Add to project was chosen there before the cancel arrived. It is "
        "linked here now."
    ),
    "add.warning.normal-not-embedded": (
        "The normal map {name} is not a DDS file, so it is not sent with the model. Add it in Durty Cloth Tool after "
        "the add."
    ),
    "add.warning.specular-not-embedded": (
        "The specular map {name} is not a DDS file, so it is not sent with the model. Add it in Durty Cloth Tool after "
        "the add."
    ),
    "add.why.no-ped-shader": (
        "Sollumz has no ped shader (ped.sps), so the garment cannot get the clothing material. Update or reinstall "
        "Sollumz."
    ),
    "add.progress.prepare": "Putting the garment on the skeleton and setting up its material…",
    "add.progress.export": "Exporting the garment with Sollumz…",
    "add.progress.pictures": "Writing the colour variations ({done} of {total})…",
    "add.cancelled-local": (
        "The add was cancelled before anything was sent. Ctrl+Z undoes what it changed on the garment."
    ),
    "add.failed-undo": "{problem} Ctrl+Z puts the garment back as it was before the add.",
}


class Msg(NamedTuple):
    """A text to show: a key of :data:`EN` and its fields (which may be other messages)."""

    key: str
    fields: Mapping[str, Any] = {}

    def __str__(self) -> str:
        return english(self)


def msg(key: str, **fields: Any) -> Msg:
    if key not in EN:
        raise KeyError(f"no text {key!r}")
    return Msg(key, fields)


Text = Union[Msg, str]


def _identity(text: str) -> str:
    return text


_iface: Callable[[str], str] = _identity
_tip: Callable[[str], str] = _identity


def set_translators(iface: Optional[Callable[[str], str]], tip: Optional[Callable[[str], str]] = None) -> None:
    """Installs Blender's translation of interface texts and tooltips (``None`` restores English)."""
    global _iface, _tip
    _iface = iface or _identity
    _tip = tip or iface or _identity


def _render(message: Text, translate: Callable[[str], str]) -> str:
    if isinstance(message, str):
        return message  # already a finished text (a name, a number, a detail from another program)
    fields: Dict[str, Any] = {"apps": translate(EN["path.connected-apps"]), "edit": translate(EN["path.edit-in-app"])}
    for name, value in message.fields.items():
        fields[name] = _render(value, translate) if isinstance(value, Msg) else value
    english_text = EN[message.key]
    try:
        return translate(english_text).format(**fields)
    except (KeyError, IndexError, ValueError):
        return english_text.format(**fields)  # a broken translation never hides the message


def english(message: Text) -> str:
    """The English text (logs, tests and Copy Diagnostics)."""
    return _render(message, _identity)


def text(message: Text) -> str:
    """The text in Blender's interface language."""
    return _render(message, _iface)


def tip(message: Text) -> str:
    """A tooltip or description in Blender's interface language (follows Blender's Tooltips setting)."""
    return _render(message, _tip)


def t(key: str, **fields: Any) -> str:
    """Shortcut: the interface text of ``key``."""
    return text(msg(key, **fields))


def tt(key: str, **fields: Any) -> str:
    """Shortcut: the tooltip text of ``key``."""
    return tip(msg(key, **fields))


class UserError(ValueError):
    """A problem the user can act on; ``message`` is shown in the interface language, ``str()`` is English."""

    def __init__(self, message: Msg) -> None:
        super().__init__(english(message))
        self.message = message


def fail(key: str, **fields: Any) -> UserError:
    return UserError(msg(key, **fields))


#: Scripts whose characters are about twice as wide as Latin ones (Hangul, CJK, fullwidth forms).
_WIDE_RANGES = ((0x1100, 0x115F), (0x2E80, 0xA4CF), (0xAC00, 0xD7A3), (0xF900, 0xFAFF), (0xFE30, 0xFE4F),
                (0xFF00, 0xFF60), (0xFFE0, 0xFFE6))
_WIDE_CHARS = "".join(f"{chr(first)}-{chr(last)}" for first, last in _WIDE_RANGES)
_WIDE = re.compile(f"[{_WIDE_CHARS}]")
_TOKENS = re.compile(f"[{_WIDE_CHARS}]|[ \\t]+|[^ \\t{_WIDE_CHARS}]+")
#: Names a line never breaks inside.
NAMES_KEPT_TOGETHER = ("Durty Cloth Tool", "Pleb Masters Community", "Creator Link")
_KEEP = " "


def character_width(text: str) -> int:
    """A text's width in average characters; Chinese characters count twice."""
    return sum(2 if _WIDE.match(c) else 1 for c in text)


def wrap_text(text: str, limit: float, measure: Optional[Callable[[str], float]] = None) -> List[str]:
    """Lines no wider than ``limit``, as ``measure`` reports a text's width (the panels pass Blender's font
    metrics); without it ``limit`` counts average characters (:func:`character_width`). Chinese characters may
    break anywhere; other scripts break at spaces, never inside :data:`NAMES_KEPT_TOGETHER`, and a longer word gets
    a line of its own. A last line holding a single word takes the word before it along when that fits, so a
    paragraph does not end on a lone word."""
    width_of = measure or character_width
    for name in NAMES_KEPT_TOGETHER:
        text = text.replace(name, name.replace(" ", _KEEP))
    lines: List[str] = []
    for paragraph in text.split("\n"):
        start = len(lines)
        line = ""
        for token in _TOKENS.findall(paragraph):
            if not token.strip(" \t"):
                if line:
                    line += " "
                continue
            if line.strip() and width_of(line + token) > limit:
                lines.append(line.rstrip())
                line = ""
            line += token
        lines.append(line.rstrip())
        if len(lines) - start >= 2 and " " not in lines[-1] and " " in lines[-2]:
            head, _, word = lines[-2].rpartition(" ")
            joined = f"{word} {lines[-1]}"
            if width_of(joined) <= limit:
                lines[-2:] = [head, joined]
    return [line.replace(_KEEP, " ") for line in lines] or [""]
