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
