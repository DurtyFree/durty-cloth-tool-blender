# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2026 Schmid Software Solutions (https://schmid-software.de)
"""Custom Ped's English texts (merged into :data:`strings.EN`; the translations are the ``ped_<language>`` modules of ``translations``).

The same rules as every add-on text: keys, never displayed text, in logic; ``str.format`` fields; labels and buttons
in Title Case, descriptions and messages as sentences. Nothing here imports Blender.
"""

from __future__ import annotations

from typing import Dict

EN: Dict[str, str] = {
    # ---- the switch in the DCT tab --------------------------------------------------------------------
    "workspace.prop": "Work On",
    "workspace.prop.desc": (
        "What the DCT tab shows: the cloth linked in Durty Cloth Tool, Garment Fitting or Custom Ped"
    ),
    "workspace.clothing": "Linked Cloth",
    "workspace.clothing.desc": "The cloth selected in Durty Cloth Tool: its live preview on the ped and its model",
    "workspace.garment": "Garment Fitting",
    "workspace.garment.desc": (
        "Make a garment from your clothing app game-ready and add it to your project as a new cloth (experimental)"
    ),
    "workspace.ped": "Custom Ped",
    "workspace.ped.desc": "Turn your own character into a custom ped for Durty Cloth Tool",
    # ---- the panel ------------------------------------------------------------------------------------
    "ped.panel": "Custom Ped",
    "ped.stage-title": "{number}. {title}",
    "ped.section.character": "Character",
    "ped.section.markers": "Markers",
    "ped.section.rig": "Rig",
    "ped.section.check": "Check",
    "ped.section.send": "Create",
    "ped.status.none": "None yet",
    "ped.status.vertices": "{count} vertices",
    "ped.status.rigging": "Rigging",
    "ped.status.waiting": "Waiting for you",
    "ped.status.ready": "Ready",
    "ped.status.review": "Needs review",
    "ped.status.not-rigged": "Not rigged",
    "ped.status.not-checked": "Not checked",
    "ped.status.no-problems": "No problems",
    "ped.status.problems": "{count} findings",
    "ped.status.problems.one": "{count} finding",
    "ped.status.sent": "Created",
    "ped.status.sending": "Creating",
    "ped.status.not-sent": "Not created",
    "ped.status.markers": "{placed} of {total}",
    "ped.privacy": (
        "Rigging and creating the ped happen in Durty Cloth Tool on this computer, from your own GTA V files. Nothing "
        "of your character goes to gta.clothing."
    ),
    # ---- the next step --------------------------------------------------------------------------------
    "ped.next.character": "Select your character's meshes in the 3D view and choose Use Selected.",
    "ped.next.fix": "Next: fix what the checks under Character name.",
    "ped.next.markers": "Next: place the markers under Markers. The click guide shows each point.",
    "ped.next.marker-problems": "Next: fix the markers the list under Markers names.",
    "ped.next.connect": "Next: connect to Durty Cloth Tool (above). No project needs to be open.",
    "ped.next.template": "Next: choose a template under Rig.",
    "ped.next.rig": "Next: Rig in Durty Cloth Tool under Rig.",
    "ped.next.rigging": "Durty Cloth Tool is rigging your character. Blender stays usable meanwhile.",
    "ped.next.approve": "Next: check where Durty Cloth Tool moved the markers (yellow), then Apply Rig.",
    "ped.next.check": "Next: try the test poses and Run Checks under Check.",
    "ped.next.send": "Next: name the ped and choose Create Custom Ped.",
    "ped.next.sending": "Waiting for you in Durty Cloth Tool: choose where to create the project there.",
    "ped.next.done": "Done: Durty Cloth Tool created the project {name}. Build it there.",
    "ped.next.done-before": "Done: Durty Cloth Tool created a project from this character. Build it there.",
    # ---- 1. Character ---------------------------------------------------------------------------------
    "ped.character.none": (
        "Select every mesh of your character (body, head, hair, eyes) in the 3D view, then choose Use Selected."
    ),
    "ped.character.facts": "{vertices} vertices · {triangles} triangles · objects: {objects} · materials: {materials}",
    "ped.prop.character": "Character",
    "ped.prop.character.desc": "The collection that holds your character's meshes",
    "ped.op.use-selected": "Use Selected",
    "ped.op.use-selected.desc": (
        "Use the selected meshes as your character. When they are not in a collection of their own, they move into a "
        "new one"
    ),
    "ped.done.use-selected": "{name} is your character ({count} meshes).",
    "ped.done.use-selected.one": "{name} is your character ({count} mesh).",
    "ped.check.none": "The character has no meshes.",
    "ped.check.rigged": "The character is rigged. Remove Rig under Rig to change its shape or size.",
    "ped.check.rigged-changed": (
        "A part was moved or got a modifier after the rig. Undo that, or remove the rig and rig again."
    ),
    "ped.check.transforms": (
        "{count} meshes are moved, turned or scaled. Apply their transforms so the character keeps its shape."
    ),
    "ped.check.transforms.one": (
        "{count} mesh is moved, turned or scaled. Apply its transforms so the character keeps its shape."
    ),
    "ped.check.modifiers": "{count} meshes have modifiers ({names}). Apply them so the rig sees what you see.",
    "ped.check.modifiers.one": "{count} mesh has modifiers ({names}). Apply them so the rig sees what you see.",
    "ped.check.old-rig": (
        "The character is rigged to {name}. Remove the old rig: the character keeps its pose, and From Old Rig can "
        "still place the markers on its joints."
    ),
    "ped.check.shape-keys": (
        "{count} meshes have shape keys, which do not follow the rig. Remove them to keep the shape you see."
    ),
    "ped.check.shape-keys.one": (
        "{count} mesh has shape keys, which do not follow the rig. Remove them to keep the shape you see."
    ),
    "ped.check.lying": "The character seems to lie down (it is longer than it is tall). Stand it up?",
    "ped.check.upside-down": "The character seems to stand on its head. Turn it over?",
    "ped.check.unit": "The character is {height} units tall, so it is probably in {unit}. Scale it to {metres} m?",
    "ped.check.too-tall": "The character is {height} m tall. It must fit within 3 m of the origin: scale it.",
    "ped.check.height-unusual": (
        "The character is {height} m tall. A GTA V ped is about 1.8 m tall: much smaller or taller characters can "
        "move and collide oddly in the game."
    ),
    "ped.check.height": "Height: {height} m",
    "ped.check.origin": "The character stands {distance} m from the origin. Move it to the origin.",
    "ped.check.facing": (
        "Your character must face the front view (Numpad 1), its left side on your right. Does it?"
    ),
    "ped.check.facing-other": (
        "The feet seem to point {direction}. Your character must face the front view (Numpad 1). Turn it, or confirm "
        "that it faces the front."
    ),
    "ped.check.facing-done": "Faces the front",
    "ped.check.size-limit": (
        "{vertices} vertices and {triangles} triangles: a rig takes at most {max_vertices} vertices and "
        "{max_triangles} triangles. Decimate a copy of the character first."
    ),
    "ped.check.size-budget": (
        "{vertices} vertices. A ped should carry at most {budget} in its most detailed level, so Durty Cloth Tool "
        "will warn about it. It still works."
    ),
    "ped.check.size": "{vertices} vertices: fine for a ped",
    "ped.unit.cm": "centimetres",
    "ped.unit.mm": "millimetres",
    "ped.unit.in": "inches",
    "ped.direction.back": "to the back",
    "ped.direction.screen-right": "to your right",
    "ped.direction.screen-left": "to your left",
    "ped.op.apply-transforms": "Apply Transforms",
    "ped.op.apply-transforms.desc": "Bake each mesh's position, rotation and scale into it, keeping how it looks",
    "ped.done.transforms": "Applied the transforms of {count} meshes.",
    "ped.done.transforms.one": "Applied the transforms of {count} mesh.",
    "ped.op.apply-modifiers": "Apply Modifiers",
    "ped.op.apply-modifiers.desc": "Apply every modifier of the character's meshes (an Armature excepted)",
    "ped.confirm.modifiers": "Apply every modifier of the character's meshes? Their settings are gone afterwards.",
    "ped.done.modifiers": "Applied {count} modifiers.",
    "ped.done.modifiers.one": "Applied {count} modifier.",
    "ped.op.remove-old-rig": "Remove Old Rig",
    "ped.op.remove-old-rig.desc": (
        "Take the character off the armature it came with: it keeps its current pose, the armature stays hidden"
    ),
    "ped.confirm.old-rig": (
        "Remove the old rig? The character keeps its current pose and loses the old rig's vertex groups. The old "
        "armature stays in the file, hidden."
    ),
    "ped.done.old-rig": "Removed the old rig ({name}). From Old Rig can still use its joints.",
    "ped.op.remove-shape-keys": "Remove Shape Keys",
    "ped.op.remove-shape-keys.desc": "Remove the shape keys of the character's meshes, keeping the shape they show",
    "ped.confirm.shape-keys": "Remove all shape keys of the character? The shape you see now stays.",
    "ped.done.shape-keys": "Removed the shape keys of {count} meshes.",
    "ped.done.shape-keys.one": "Removed the shape keys of {count} mesh.",
    "ped.op.scale": "Scale",
    "ped.op.scale.desc": "Scale the character about the origin, as a change of units does",
    "ped.op.scale-by": "Scale by {factor}",
    "ped.confirm.scale": "Scale the character by {factor}?",
    "ped.done.scaled": "Scaled the character by {factor}.",
    "ped.op.turn": "Turn",
    "ped.op.turn.desc": "Turn the character in 90 degree steps",
    "ped.op.stand-up": "Stand Up",
    "ped.op.stand-up-other": "Stand Up the Other Way",
    "ped.op.turn-over": "Turn Over",
    "ped.op.turn-left": "Turn 90° Left",
    "ped.op.turn-right": "Turn 90° Right",
    "ped.op.turn-around": "Turn 180°",
    "ped.confirm.turn": "Turn the character? You can undo it with Ctrl+Z.",
    "ped.done.turned": "Turned the character.",
    "ped.op.to-origin": "Move to Origin",
    "ped.op.to-origin.desc": "Move the character so it stands on the ground at the origin",
    "ped.done.origin": "The character stands at the origin now.",
    "ped.op.confirm-facing": "It Faces the Front",
    "ped.op.confirm-facing.desc": "Confirm that the character faces the front view, its left side on your right",
    "ped.confirm.facing": "Does the character face you in the front view (Numpad 1), its left hand on your right?",
    "ped.heading.parts": "Parts ({count})",
    "ped.parts.subtext": (
        "Hair, eyes and teeth are weighted differently, and hair becomes the ped's hair. Change a role when the guess "
        "is wrong."
    ),
    "ped.parts.guess": "Guessed: {role}",
    "ped.prop.role": "Part Role",
    "ped.prop.role.desc": "What this mesh is: it decides how it is weighted and where it goes in the ped",
    "ped.role.auto": "Automatic",
    "ped.role.auto.desc": "Guess the role from the names of the mesh and its materials",
    "ped.role.body": "Body",
    "ped.role.body.desc": "Skin and clothing that move with the body",
    "ped.role.head": "Head and Face",
    "ped.role.head.desc": "The head, face, eyebrows and lashes",
    "ped.role.hair": "Hair",
    "ped.role.hair.desc": "Hair, beard cards and other hair that moves with the head",
    "ped.role.eyes": "Eyes",
    "ped.role.eyes.desc": "The eyeballs, moved by the eye bones or the head",
    "ped.role.teeth": "Teeth",
    "ped.role.teeth.desc": "Teeth and tongue, moved by the head",
    "ped.role.accessory": "Accessory",
    "ped.role.accessory.desc": "Glasses, jewellery and other things the character wears",
    # ---- 2. Markers -----------------------------------------------------------------------------------
    "ped.heading.markers": "Joint Markers",
    "info.ped-markers": (
        "Markers show Durty Cloth Tool where your character's joints are: inside the body, in the middle of each "
        "joint. Left markers are blue, right ones orange, the character's left being on your right in the front view."
    ),
    "ped.markers.placed": "{placed} of {total} placed",
    "ped.op.guide": "Click Guide",
    "ped.op.guide.desc": (
        "Click the points a figure in the 3D view shows, one after the other; the others are placed from them"
    ),
    "ped.op.auto-markers": "Auto Markers",
    "ped.op.auto-markers.desc": "Place every marker from the character's shape. Check them afterwards",
    "ped.op.from-rig": "From Old Rig",
    "ped.op.from-rig.desc": (
        "Place the markers on the joints of the character's old rig (Mixamo, Unreal, Rigify, Character Creator or VRM)"
    ),
    "ped.op.mirror": "Mirror",
    "ped.op.mirror.desc": "Copy the markers of one side onto the other, mirrored across the character's middle",
    "ped.op.mirror-left": "Left to Right",
    "ped.op.mirror-right": "Right to Left",
    "ped.op.show": "Show",
    "ped.op.show-markers.desc": "Select these markers in the 3D view",
    "ped.prop.marker-size": "Marker Size",
    "ped.prop.marker-size.desc": "How large the marker spheres are drawn",
    "ped.prop.follow": "Move Elbows and Knees Along",
    "ped.prop.follow.desc": (
        "When you move a wrist, shoulder, ankle or hip marker, the elbow or knee between them moves with the limb"
    ),
    "ped.done.auto-markers": "Placed the markers from the character's shape. Check each one and move any that are off.",
    "ped.done.from-rig": "Placed the markers on the joints of the {rig} rig. Check the chin and the top of the head.",
    "ped.done.mirrored": "Mirrored the markers.",
    "ped.rig-kind.mixamo": "Mixamo",
    "ped.rig-kind.unreal": "Unreal",
    "ped.rig-kind.rigify": "Rigify",
    "ped.rig-kind.cc": "Character Creator",
    "ped.rig-kind.vrm": "VRM",
    "ped.marker-error.too-small": "The character is too small or not standing: Auto Markers found no person.",
    "ped.marker-error.guide-incomplete": "The click guide needs all its points before it can place the others.",
    "ped.marker-error.no-rig": (
        "The character has no old rig with known bone names (Mixamo, Unreal, Rigify, Character Creator or VRM)."
    ),
    "ped.marker-note.arms": "The arms could not be told apart from the body: check the shoulders, elbows and wrists.",
    "ped.marker-note.legs": "The legs could not be told apart: check the hips, knees and ankles.",
    "ped.marker-note.neck": "The neck was hard to find: check the neck, chin and chest.",
    "ped.marker-problem.missing": "Missing markers: {names}.",
    "ped.marker-problem.side": (
        "On the wrong side: {names}. The character's left must be at +X, on your right in the front view."
    ),
    "ped.marker-problem.order": "Not in order from the head down: {names}.",
    "ped.marker-problem.asymmetric": "Left and right limbs differ by more than 30 %: {names}.",
    "ped.marker-problem.outside": "Outside the character: {names}.",
    "ped.marker.headTop": "Top of Head",
    "ped.marker.chin": "Chin",
    "ped.marker.neck": "Neck",
    "ped.marker.chest": "Chest",
    "ped.marker.pelvis": "Pelvis",
    "ped.marker.shoulderL": "Left Shoulder",
    "ped.marker.shoulderR": "Right Shoulder",
    "ped.marker.elbowL": "Left Elbow",
    "ped.marker.elbowR": "Right Elbow",
    "ped.marker.wristL": "Left Wrist",
    "ped.marker.wristR": "Right Wrist",
    "ped.marker.hipL": "Left Hip",
    "ped.marker.hipR": "Right Hip",
    "ped.marker.kneeL": "Left Knee",
    "ped.marker.kneeR": "Right Knee",
    "ped.marker.ankleL": "Left Ankle",
    "ped.marker.ankleR": "Right Ankle",
    "ped.marker.toeL": "Left Toes",
    "ped.marker.toeR": "Right Toes",
    "ped.guide.title": "Click Guide: point {index} of {total}",
    "ped.guide.keys": "Click: place the point. Right click: back one point. Mouse wheel and middle mouse: view. Esc: stop.",
    "ped.guide.headTop": "Click the top of the head.",
    "ped.guide.chin": "Click the tip of the chin.",
    "ped.guide.shoulderL": "Click the left shoulder joint (on your right in the front view).",
    "ped.guide.shoulderR": "Click the right shoulder joint (on your left).",
    "ped.guide.wristL": "Click the middle of the left wrist.",
    "ped.guide.wristR": "Click the middle of the right wrist.",
    "ped.guide.hipL": "Click the left hip joint, where the leg meets the body.",
    "ped.guide.hipR": "Click the right hip joint.",
    "ped.guide.ankleL": "Click the middle of the left ankle.",
    "ped.guide.ankleR": "Click the middle of the right ankle.",
    "ped.guide.toeL": "Click the left foot where the toes bend.",
    "ped.guide.toeR": "Click the right foot where the toes bend.",
    "ped.guide.finish": "All points placed. Press Enter.",
    "ped.guide.missed": "That click missed the character. Click on it.",
    "ped.guide.done": (
        "All points placed; the neck, chest, pelvis, elbows and knees were placed from them. Check them and move any "
        "that are off."
    ),
    # ---- 3. Rig ---------------------------------------------------------------------------------------
    "ped.heading.template": "Template",
    "info.ped-template": (
        "The installed GTA V ped your ped is built from: its skeleton, movement, voice and body shapes. Choose one "
        "like your character: the same gender and a similar build."
    ),
    "ped.prop.template": "Template",
    "ped.prop.template.desc": "The installed ped whose skeleton your character gets",
    "ped.prop.gender": "Gender",
    "ped.gender.any": "Any",
    "ped.gender.any.desc": "List templates of both genders",
    "ped.gender.male.desc": "List male templates",
    "ped.gender.female.desc": "List female templates",
    "ped.prop.show-all": "Show All",
    "ped.prop.show-all.desc": "Also list freemode, player, cutscene and story peds, not only ambient ones",
    "ped.template.choose": "Choose a Template",
    "ped.template.recommended": "{model} (Recommended)",
    "ped.template.facts": "{facts}",
    "ped.templates.loading": "Durty Cloth Tool is reading your game files (several seconds the first time).",
    "ped.templates.refresh": "Choose Refresh to list the templates installed with your game.",
    "ped.templates.none": "No template matches. Turn on Show All or choose another gender.",
    "ped.templates.truncated": "Durty Cloth Tool lists the first {count}. Choose a gender to see others.",
    "ped.group.ambient": "ambient",
    "ped.group.freemode": "freemode",
    "ped.group.player": "player",
    "ped.group.cutscene": "cutscene",
    "ped.group.story": "story",
    "ped.layout.packed": "packed",
    "ped.layout.streamed": "streamed",
    "ped.op.refresh": "Refresh",
    "ped.op.refresh.desc": "Ask Durty Cloth Tool again for the templates installed with your game",
    "ped.op.use-template": "Use Template",
    "ped.op.use-template.desc": "Use this installed ped as the template",
    "ped.op.use-template-named": "Use {template}",
    "ped.rights.title": "Your Rights to This Character",
    "ped.rights.text": (
        "Only convert characters you made yourself or have permission to use in GTA V resources (for example a "
        "licence that allows modification and redistribution). Characters taken from other games, films or creators "
        "usually may not be converted or shared. You are responsible for the characters you convert and publish."
    ),
    "ped.rights.check": "I made this character or have the rights to convert and use it",
    "ped.rights.done": "You confirmed your rights to this character.",
    "ped.op.rig": "Rig in Durty Cloth Tool",
    "ped.op.rig.desc": (
        "Durty Cloth Tool fits the template's skeleton to your markers and computes the weights and the game's rest "
        "pose, from your own game files"
    ),
    "ped.op.rig-again": "Rig Again",
    "ped.op.cancel-rig.desc": "Stop the rig in Durty Cloth Tool",
    "ped.rig.waiting": "Waiting for Durty Cloth Tool to start the rig.",
    "ped.rig.cancelling": "Cancelling the rig.",
    "ped.rig.working": "Rigging",
    "ped.rig.progress": "{stage} ({percent} %)",
    "ped.stage.template": "Reading the template",
    "ped.stage.markers": "Checking the markers",
    "ped.stage.skeleton": "Fitting the skeleton",
    "ped.stage.weights": "Transferring weights",
    "ped.stage.rest": "Converting to the game's rest pose",
    "ped.stage.report": "Writing the report",
    "ped.prop.refine": "Refine Markers",
    "ped.prop.refine.desc": (
        "Durty Cloth Tool moves the markers onto the middle of the limbs and the body, and shows you where"
    ),
    "ped.prop.fingers": "Fingers",
    "ped.fingers.off": "Move with the Hand",
    "ped.fingers.off.desc": "The fingers move with the hand, like a mitten",
    "ped.fingers.auto": "Automatic",
    "ped.fingers.auto.desc": "Weight the fingers from the template's hand",
    "ped.prop.face": "Face",
    "ped.face.off": "Move with the Head",
    "ped.face.off.desc": "The face moves with the head",
    "ped.face.auto": "Automatic",
    "ped.face.auto.desc": "Weight the face from the template's face, for expressions",
    "ped.prop.roll": "Roll Bones",
    "ped.prop.roll.desc": "Weight the twist bones of the arms and legs, which keep wrists and thighs from collapsing",
    "ped.prop.helpers": "Helper Bones",
    "ped.prop.helpers.desc": "Weight the template's helper bones, as its own body is",
    "ped.prop.rest": "Rest Shape",
    "ped.rest.volume": "Keep Volume",
    "ped.rest.volume.desc": "Bring the character to the rest pose so shoulders and hips keep their volume",
    "ped.rest.linear": "Exact",
    "ped.rest.linear.desc": "Bring the character to the rest pose so the game's skinning gives back your pose exactly",
    "ped.result.ready": "Ready (confidence {percent} %)",
    "ped.result.review": "Needs review (confidence {percent} %)",
    "ped.result.markers": "({names})",
    "ped.result.moved": "Durty Cloth Tool moved {count} markers onto the middle of the body (yellow in the 3D view):",
    "ped.result.moved.one": (
        "Durty Cloth Tool moved {count} marker onto the middle of the body (yellow in the 3D view):"
    ),
    "ped.result.move": "{marker}: {cm} cm",
    "ped.result.subtext": (
        "Apply Rig builds the armature and gives the meshes their weights and the game's rest pose. Your character "
        "keeps its look, and Ctrl+Z takes it back."
    ),
    "ped.result.proxy": "The weights were computed on a simplified copy of this large mesh.",
    "ped.op.apply-rig": "Apply Rig",
    "ped.op.apply-rig.desc": (
        "Build the armature from the rig and give the meshes its weights and the game's rest pose; the character keeps "
        "its look"
    ),
    "ped.op.use-refined": "Use These Markers",
    "ped.op.use-refined.desc": "Move your markers to where Durty Cloth Tool put them",
    "ped.op.discard-rig": "Discard",
    "ped.op.discard-rig.desc": "Throw this rig away without applying it",
    "ped.done.applied": "Applied the rig: the armature {name} has {bones} bones.",
    "ped.done.refined": "Your markers are where Durty Cloth Tool put them now.",
    "ped.rigged.line": "Rigged from {template} ({bones} bones)",
    "ped.op.previous-rig": "Previous Rig",
    "ped.op.previous-rig.desc": "Swap the applied rig with the one applied before it",
    "ped.done.previous": "The previous rig is back.",
    "ped.op.remove-rig": "Remove Rig",
    "ped.op.remove-rig.desc": "Take the rig off: the character is as it was before the first rig",
    "ped.confirm.remove-rig": "Remove the rig? The armatures go and the character is as it was before the first rig.",
    "ped.done.removed": "Removed the rig. The character is as it was before rigging.",
    "ped.warning.marker_offset": (
        "{count} markers sat more than 2 cm off the middle of the body (up to {value} mm). Check them."
    ),
    "ped.warning.marker_offset.one": (
        "{count} marker sat more than 2 cm off the middle of the body ({value} mm). Check it."
    ),
    "ped.warning.asymmetric_markers": "The left and right markers differ by more than 5 %. Check both sides.",
    "ped.warning.proportion_out_of_range": (
        "Some proportions are far from the template's. A template of a closer build moves better."
    ),
    "ped.warning.ragdoll_mismatch": (
        "This character's height is far from its template's. In the game, bullets and falls use the template's body "
        "shapes, so hits can miss or land beside the model. Choose a closer template, or test in the game before you "
        "publish."
    ),
    "ped.warning.low_coverage": (
        "Only part of the character matched the template's body. Check the weights in the test poses."
    ),
    "ped.warning.inpainted_large": "Many weights were filled in from their neighbours. Check the test poses.",
    "ped.warning.non_deforming_moved": "Some weights were moved off bones that never move the mesh.",
    "ped.warning.empty_rows_refilled": "{count} vertices had no weights and took their neighbours'.",
    "ped.warning.empty_rows_refilled.one": "{count} vertex had no weights and took its neighbours'.",
    "ped.warning.floating_parts": "{count} loose parts were bound to the nearest bone.",
    "ped.warning.floating_parts.one": "{count} loose part was bound to the nearest bone.",
    "ped.warning.rest_strain": (
        "Some triangles fold in the game's rest pose. Look at the shoulders and hips in the Game Rest Pose."
    ),
    "ped.warning.fingers_fallback": "The fingers move with the hand.",
    "ped.warning.other": "Durty Cloth Tool reported {code}.",
    "ped.suggest": "{template} is closer to your character's proportions. Use it and rig again for a better fit.",
    "ped.refusal.marker_missing": "Markers are missing.",
    "ped.refusal.marker_invalid": "Some markers are not usable. Place them on the character again.",
    "ped.refusal.marker_degenerate": "Some markers sit on top of each other.",
    "ped.refusal.marker_side": (
        "Left and right are swapped. The character's left must be at +X: check that it faces the front."
    ),
    "ped.refusal.not_upright": "The character does not stand upright, or its head is below its neck.",
    "ped.refusal.limb_length": "A limb is much shorter or longer than the template's. Check these markers.",
    "ped.refusal.asymmetric": "The left and right limbs differ by more than 30 %.",
    "ped.refusal.pose_unsupported": (
        "A leg is bent or spread too far. Pose the character standing straight, in an A-pose or a T-pose."
    ),
    "ped.refusal.marker_outside_body": "These markers lie outside the character.",
    "ped.refusal.mesh_invalid": "Durty Cloth Tool could not read the mesh (empty, or mostly flat triangles).",
    "ped.refusal.mesh_too_large": "The character has too many vertices or triangles for a rig. Decimate a copy first.",
    "ped.refusal.options_invalid": "Durty Cloth Tool refused the rig's options. Update the add-on.",
    "ped.refusal.template_invalid": "Durty Cloth Tool cannot use this template. Choose another one.",
    "ped.refusal.template_not_found": "This template is not installed. Refresh the list and choose another one.",
    "ped.refusal.game_required": "Durty Cloth Tool needs your GTA V folder. Set it in Durty Cloth Tool's settings.",
    "ped.refusal.fit_invalid": "The rig came out broken. Check the markers against the character and rig again.",
    "ped.refusal.other": "Durty Cloth Tool refused the rig ({code}).",
    # ---- 4. Check -------------------------------------------------------------------------------------
    "ped.heading.poses": "Test Poses",
    "info.ped-poses": (
        "Simple bends by bone name to see how the weights move the character. They are not game animations; small "
        "creases at the extremes are normal."
    ),
    "ped.pose.yours": "Your Pose",
    "ped.pose.rest": "Game Rest Pose",
    "ped.pose.arms_up": "Arms Up",
    "ped.pose.arms_forward": "Arms Forward",
    "ped.pose.squat": "Squat",
    "ped.pose.walk": "Walk Step",
    "ped.pose.twist": "Twist",
    "ped.op.pose": "Pose",
    "ped.op.pose.desc": "Show the character in this pose",
    "ped.op.run-checks": "Run Checks",
    "ped.op.run-checks.desc": "Check the weights, the armature and the meshes against the rig, and the test poses",
    "ped.op.show-finding.desc": "Select the vertices this finding concerns",
    "ped.done.checks": "Run Checks found {count} things to look at; nothing Durty Cloth Tool would refuse.",
    "ped.done.checks.one": "Run Checks found {count} thing to look at; nothing Durty Cloth Tool would refuse.",
    "ped.done.checks-refused": "Run Checks found {count} problems Durty Cloth Tool would refuse.",
    "ped.done.checks-refused.one": "Run Checks found {count} problem Durty Cloth Tool would refuse.",
    "ped.local.none": "No problems found.",
    "ped.local.unweighted": "{count} vertices have no weight. Durty Cloth Tool refuses them: weight them.",
    "ped.local.unweighted.one": "{count} vertex has no weight. Durty Cloth Tool refuses it: weight it.",
    "ped.local.too-many": "{count} vertices have more than four bones. The game keeps the four strongest.",
    "ped.local.too-many.one": "{count} vertex has more than four bones. The game keeps the four strongest.",
    "ped.local.non-deforming": "{count} vertices are weighted to bones that never move the mesh.",
    "ped.local.non-deforming.one": "{count} vertex is weighted to bones that never move the mesh.",
    "ped.local.unknown-groups": "Vertex groups that are not bones ({names}) are left out.",
    "ped.local.armature-changed": (
        "{count} bones were moved or turned after the rig ({names}). Undo that or rig again: bones keep the "
        "template's rotation."
    ),
    "ped.local.armature-changed.one": (
        "{count} bone was moved or turned after the rig ({names}). Undo that or rig again: bones keep the template's "
        "rotation."
    ),
    "ped.local.mesh-changed": "The meshes changed after the rig (vertices added or removed). Rig again.",
    "ped.local.strain": "{count} vertices stretch or squash a lot in {pose}.",
    "ped.local.strain.one": "{count} vertex stretches or squashes a lot in {pose}.",
    "ped.local.hint": "Small creases in extreme poses are normal. For bigger ones, move a marker and rig again.",
    # ---- 5. Send --------------------------------------------------------------------------------------
    "ped.prop.name": "Ped Name",
    "ped.prop.name.desc": "The name Durty Cloth Tool shows for the ped",
    "ped.prop.model": "Model Name",
    "ped.prop.model.desc": (
        "The game's name of the new ped: a lowercase letter, then 2 to 31 lowercase letters, digits or underscores"
    ),
    "ped.prop.ragdoll": "Ragdoll Body",
    "ped.ragdoll.template": "As the Template",
    "ped.ragdoll.template.desc": "The shared ragdoll body the template uses",
    "ped.ragdoll.fred": "Standard Male",
    "ped.ragdoll.fred.desc": "The shared ragdoll body of most male peds",
    "ped.ragdoll.wilma": "Standard Female",
    "ped.ragdoll.wilma.desc": "The shared ragdoll body of most female peds",
    "ped.ragdoll.fred-large": "Large Male",
    "ped.ragdoll.fred-large.desc": "The shared ragdoll body of large male peds",
    "ped.ragdoll.wilma-large": "Large Female",
    "ped.ragdoll.wilma-large.desc": "The shared ragdoll body of large female peds",
    "ped.ragdoll.subtext": (
        "Bullets, falls and the ragdoll use this body's shapes in the game. Choose a large one for a much bigger "
        "character."
    ),
    "ped.texture.too-large": "The image {name} is larger than 4096 pixels on a side. Durty Cloth Tool refuses it.",
    "ped.texture.not-multiple-of-four": (
        "The width or height of the image {name} does not divide by four. Durty Cloth Tool refuses it."
    ),
    "ped.texture.non-power-of-two": (
        "The image {name} is not a power of two in size (such as 1024 or 2048). It works, but such sizes look best."
    ),
    "ped.op.send": "Create Custom Ped",
    "ped.op.send.desc": (
        "Export the rigged character in the game's rest pose and send it to Durty Cloth Tool, which creates a new "
        "custom ped project once you confirm there"
    ),
    "ped.op.cancel-send.desc": "Withdraw the character while Durty Cloth Tool still asks",
    "ped.send.subtext": (
        "Durty Cloth Tool shows the ped with its checks and asks where to create the project. Nothing is created "
        "until you choose Create there."
    ),
    "ped.send.waiting": "Sent the character ({size} MiB). Choose Create in Durty Cloth Tool.",
    "ped.send.withdrawing": "Withdrawing the character.",
    "ped.send.withdrawn": "Withdrawn: Durty Cloth Tool created nothing.",
    "ped.send.created": "Durty Cloth Tool created the project {name} with the ped {model} from {template}.",
    "ped.send.created-late": (
        "Durty Cloth Tool created the project {name} with the ped {model} after all: Create was chosen there just as "
        "the character was withdrawn."
    ),
    "ped.send.findings": "Durty Cloth Tool's checks ({count}):",
    "ped.send.next": (
        "Check the ped's behaviour in Durty Cloth Tool (ped type, movement, voice), then build the project."
    ),
    "ped.finding.rig-mismatch": (
        "The skeleton is not the template's or the rig's: a bone was moved or turned. Apply the rig again, or rig "
        "again."
    ),
    "ped.finding.ped-budget": "More vertices than a ped should carry in its most detailed level.",
    "ped.finding.ped-ragdoll-mismatch": (
        "The character's height is far from the template's ragdoll body: hits and falls in the game use the "
        "template's body shapes."
    ),
    "ped.finding.ped-rest-strain": "The rig folded some triangles in the game's rest pose.",
    # ---- why something cannot run -----------------------------------------------------------------------
    "ped.why.select-meshes": "Select the meshes of your character first.",
    "ped.why.no-character": "Choose your character under Character first.",
    "ped.why.object-mode": "Switch to Object Mode first.",
    "ped.why.rigged": "The character is rigged. Remove the rig to change it.",
    "ped.why.no-markers": "Place the markers first.",
    "ped.why.guide-running": "The click guide is running.",
    "ped.why.view3d": "Start the click guide from the 3D view's sidebar.",
    "ped.why.checks": "Fix what the checks under Character name first.",
    "ped.why.markers": "Place all markers first.",
    "ped.why.connect": "Connect to Durty Cloth Tool to choose a template and rig.",
    "ped.why.template": "Choose a template first.",
    "ped.why.rights": "Confirm your rights to this character first.",
    "ped.why.rigging": "A rig is running in Durty Cloth Tool.",
    "ped.why.not-rigging": "No rig is running.",
    "ped.why.no-result": "There is no rig to apply. Rig the character first.",
    "ped.why.no-previous": "There is no previous rig.",
    "ped.why.not-rigged": "Rig the character first.",
    "ped.why.mesh-changed": "The character's meshes changed after you asked for this rig. Rig again.",
    "ped.why.vertex-count": "{name} changes its vertex count in a modifier. Apply its modifiers first.",
    "ped.why.modifiers-shape-keys": "{name} has shape keys, so its modifiers cannot be applied. Remove them first.",
    "ped.why.export-failed": "Blender's glTF exporter did not write the character. Its Info log has the details.",
    "ped.why.model": "The model name is a lowercase letter, then 2 to 31 lowercase letters, digits or underscores.",
    "ped.why.model-game": "Names starting with {prefix} belong to the game's own peds. Choose another, such as {suggestion}.",
    "ped.why.name": "Give the ped a name.",
    "ped.why.transforms-first": "Apply the transforms first.",
    "ped.why.refused-checks": "Run Checks found problems Durty Cloth Tool would refuse. Fix them first.",
    "ped.why.textures": "An image is too large or its size does not divide by four. Fix it first.",
    "ped.why.sending": "A custom ped is being sent.",
    "ped.why.not-sending": "Nothing is being sent.",
    "ped.invalid": "The add-on could not prepare this request: {detail}",
    # ---- plans and Durty Cloth Tool's answers -----------------------------------------------------------
    "ped.plan.rig": "Rigging is included in Durty Cloth Tool Ultimate.",
    "ped.plan.add": "Creating a custom ped project needs Durty Cloth Tool Advanced or Ultimate.",
    "ped.error.rig-busy": "Durty Cloth Tool is rigging another character. Try again when it has finished.",
    "ped.error.rig-cancelled": "The rig was cancelled.",
    "ped.error.rig-refused": "Durty Cloth Tool could not rig the character:",
    "ped.error.dct-too-old": "This Durty Cloth Tool does not make custom peds from Blender yet. Update Durty Cloth Tool.",
    "ped.error.rig-disconnected": "The connection to Durty Cloth Tool ended during the rig. Rig again.",
    "ped.error.rig-timeout": "Durty Cloth Tool did not finish the rig in time. Rig again.",
    "ped.error.add-busy": "Durty Cloth Tool is busy with another custom ped or a build. Try again when it has finished.",
    "ped.error.add-denied": "Cancelled in Durty Cloth Tool. Choose Create Custom Ped again when you are ready.",
    "ped.error.model-rejected": "Durty Cloth Tool could not make a ped from the character. Its checks below say why.",
    "ped.error.save-failed": "Durty Cloth Tool could not create the project. Choose another folder and send again.",
    "ped.error.add-disconnected": (
        "The connection to Durty Cloth Tool ended before it answered. Choose Create Custom Ped again."
    ),
    "ped.error.add-timeout": "Durty Cloth Tool did not answer in time. Choose Create Custom Ped again.",
    "ped.error.add-unanswered": "Durty Cloth Tool did not confirm the withdrawal. Check its project list.",
    # ---- protocol errors --------------------------------------------------------------------------------
    "error.template-not-found": "This template is not installed. Refresh the list and choose another one.",
    "error.mesh-too-large": "The character has too many vertices or triangles. Decimate a copy first.",
    "error.rig-refused": "Durty Cloth Tool could not rig the character.",
    "error.upload-incomplete": "The character did not arrive complete in Durty Cloth Tool. Send it again.",
}
