# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2026 Schmid Software Solutions (https://schmid-software.de)
"""German (Deutsch): the Custom Ped texts. Informal "du", as Durty Cloth Tool uses it."""

TEXT = {
    "workspace.prop": "Arbeiten an",
    "workspace.prop.desc": "Was der DCT-Tab zeigt: die Kleidungswerkzeuge oder die Werkzeuge für eigene Peds",
    "workspace.clothing": "Kleidung",
    "workspace.clothing.desc": (
        "Die in Durty Cloth Tool verknüpfte Kleidung, ihre Live-Vorschau und ihr Modell sowie Kleidung anpassen"
    ),
    "workspace.ped": "Eigener Ped",
    "workspace.ped.desc": "Mach aus deiner Figur einen eigenen Ped für Durty Cloth Tool",
    "ped.panel": "Eigener Ped (experimentell)",
    "ped.stage-title": "{number}. {title}",
    "ped.section.character": "Figur",
    "ped.section.markers": "Marker",
    "ped.section.rig": "Rig",
    "ped.section.check": "Prüfen",
    "ped.section.send": "Senden",
    "ped.status.none": "Noch keine",
    "ped.status.vertices": "{count} Vertices",
    "ped.status.rigging": "Wird geriggt",
    "ped.status.waiting": "Wartet auf dich",
    "ped.status.ready": "Bereit",
    "ped.status.review": "Bitte prüfen",
    "ped.status.not-rigged": "Nicht geriggt",
    "ped.status.not-checked": "Nicht geprüft",
    "ped.status.no-problems": "Keine Probleme",
    "ped.status.problems": "{count} Befunde",
    "ped.status.sent": "Erstellt",
    "ped.status.sending": "Wird gesendet",
    "ped.status.not-sent": "Nicht gesendet",
    "ped.privacy": (
        "Das Riggen und das Erstellen des Peds passieren in Durty Cloth Tool auf diesem Computer, aus deinen eigenen "
        "GTA V Dateien. Nichts von deiner Figur geht an gta.clothing."
    ),
    "ped.heading.more": "Weitere Optionen",
    "ped.next.character": "Wähle die Meshes deiner Figur in der 3D-Ansicht aus und dann Auswahl nutzen.",
    "ped.next.fix": "Weiter: Behebe, was die Prüfungen unter Figur nennen.",
    "ped.next.markers": "Weiter: Setze die Marker unter Marker. Die Klickhilfe zeigt dir jeden Punkt.",
    "ped.next.marker-problems": "Weiter: Korrigiere die Marker, die die Liste unter Marker nennt.",
    "ped.next.connect": "Weiter: Verbinde dich mit Durty Cloth Tool (oben). Es muss kein Projekt geöffnet sein.",
    "ped.next.template": "Weiter: Wähle unter Rig eine Vorlage.",
    "ped.next.rig": "Weiter: In Durty Cloth Tool riggen unter Rig.",
    "ped.next.rigging": "Durty Cloth Tool riggt deine Figur. Blender bleibt währenddessen nutzbar.",
    "ped.next.approve": "Weiter: Prüfe, wohin Durty Cloth Tool die Marker verschoben hat (gelb), dann Rig anwenden.",
    "ped.next.check": "Weiter: Probiere die Testposen aus und wähle Prüfungen ausführen unter Prüfen.",
    "ped.next.send": "Weiter: Eigenen Ped erstellen unter Senden.",
    "ped.next.sending": "Durty Cloth Tool wartet auf dich: Wähle dort, wo das Projekt erstellt wird.",
    "ped.next.done": "Fertig: Durty Cloth Tool hat das Projekt {name} erstellt. Baue es dort.",
    "ped.next.done-before": "Fertig: Durty Cloth Tool hat aus dieser Figur ein Projekt erstellt. Baue es dort.",
    "ped.character.none": (
        "Wähle jedes Mesh deiner Figur (Körper, Kopf, Haare, Augen) in der 3D-Ansicht aus und dann Auswahl nutzen."
    ),
    "ped.character.facts": "{objects} Objekte, {vertices} Vertices, {triangles} Dreiecke, {materials} Materialien",
    "ped.prop.character": "Figur",
    "ped.prop.character.desc": "Die Sammlung mit den Meshes deiner Figur",
    "ped.op.use-selected": "Auswahl nutzen",
    "ped.op.use-selected.desc": (
        "Die ausgewählten Meshes als deine Figur nutzen. Liegen sie nicht in einer eigenen Sammlung, kommen sie in "
        "eine neue"
    ),
    "ped.done.use-selected": "{name} ist deine Figur ({count} Meshes).",
    "ped.check.none": "Die Figur hat keine Meshes.",
    "ped.check.rigged": "Die Figur ist geriggt. Wähle Rig entfernen unter Rig, um ihre Form oder Größe zu ändern.",
    "ped.check.rigged-changed": (
        "Ein Teil wurde nach dem Riggen verschoben oder hat einen Modifikator bekommen. Mach das rückgängig, oder "
        "entferne das Rig und rigge erneut."
    ),
    "ped.check.transforms": (
        "{count} Meshes sind verschoben, gedreht oder skaliert. Wende ihre Transformationen an, damit die Figur ihre "
        "Form behält."
    ),
    "ped.check.modifiers": (
        "{count} Meshes haben Modifikatoren ({names}). Wende sie an, damit das Rig sieht, was du siehst."
    ),
    "ped.check.old-rig": (
        "Die Figur ist an {name} geriggt. Entferne das alte Rig: Die Figur behält ihre Pose, und Vom alten Rig kann "
        "die Marker trotzdem auf seine Gelenke setzen."
    ),
    "ped.check.shape-keys": (
        "{count} Meshes haben Formschlüssel, die dem Rig nicht folgen. Entferne sie, um die Form zu behalten, die du "
        "siehst."
    ),
    "ped.check.lying": "Die Figur scheint zu liegen (sie ist länger als hoch). Aufstellen?",
    "ped.check.upside-down": "Die Figur scheint auf dem Kopf zu stehen. Umdrehen?",
    "ped.check.unit": (
        "Die Figur ist {height} Einheiten groß, ihre Einheit ist also wahrscheinlich {unit}. Auf {metres} m skalieren?"
    ),
    "ped.check.too-tall": (
        "Die Figur ist {height} m groß. Sie muss innerhalb von 3 m um den Ursprung bleiben: Skaliere sie."
    ),
    "ped.check.height-unusual": (
        "Die Figur ist {height} m groß. Ein Ped in GTA V ist etwa 1,8 m groß: Viel kleinere oder größere Figuren "
        "können sich im Spiel seltsam bewegen und falsch kollidieren."
    ),
    "ped.check.height": "Größe: {height} m",
    "ped.check.origin": "Die Figur steht {distance} m vom Ursprung entfernt. Verschiebe sie auf den Ursprung.",
    "ped.check.facing": (
        "Deine Figur muss zur Vorderansicht (Numpad 1) schauen, ihre linke Seite rechts von dir. Tut sie das?"
    ),
    "ped.check.facing-other": (
        "Die Füße scheinen {direction} zu zeigen. Deine Figur muss zur Vorderansicht (Numpad 1) schauen. Dreh sie, "
        "oder bestätige, dass sie nach vorn schaut."
    ),
    "ped.check.facing-done": "Schaut nach vorn",
    "ped.check.size-limit": (
        "{vertices} Vertices und {triangles} Dreiecke: Ein Rig nimmt höchstens {max_vertices} Vertices und "
        "{max_triangles} Dreiecke. Reduziere zuerst eine Kopie der Figur, zum Beispiel mit einem Decimate-Modifikator."
    ),
    "ped.check.size-budget": (
        "{vertices} Vertices. Ein Ped sollte in seiner detailliertesten Stufe höchstens {budget} haben, darum warnt "
        "Durty Cloth Tool davor. Er funktioniert trotzdem."
    ),
    "ped.check.size": "{vertices} Vertices: passt für einen Ped",
    "ped.unit.cm": "Zentimeter",
    "ped.unit.mm": "Millimeter",
    "ped.unit.in": "Zoll",
    "ped.direction.back": "nach hinten",
    "ped.direction.screen-right": "von dir aus nach rechts",
    "ped.direction.screen-left": "von dir aus nach links",
    "ped.op.apply-transforms": "Transformationen anwenden",
    "ped.op.apply-transforms.desc": (
        "Position, Drehung und Skalierung jedes Meshes in das Mesh übernehmen, ohne sein Aussehen zu ändern"
    ),
    "ped.done.transforms": "Die Transformationen von {count} Meshes wurden angewendet.",
    "ped.op.apply-modifiers": "Modifikatoren anwenden",
    "ped.op.apply-modifiers.desc": "Jeden Modifikator der Meshes der Figur anwenden (außer einem Armature-Modifikator)",
    "ped.confirm.modifiers": "Jeden Modifikator der Meshes der Figur anwenden? Ihre Einstellungen sind danach weg.",
    "ped.done.modifiers": "{count} Modifikatoren angewendet.",
    "ped.op.remove-old-rig": "Altes Rig entfernen",
    "ped.op.remove-old-rig.desc": (
        "Die Figur von der mitgelieferten Armature lösen: Sie behält ihre aktuelle Pose, die Armature bleibt "
        "ausgeblendet"
    ),
    "ped.confirm.old-rig": (
        "Das alte Rig entfernen? Die Figur behält ihre aktuelle Pose und verliert die Vertexgruppen des alten Rigs. "
        "Die alte Armature bleibt ausgeblendet in der Datei."
    ),
    "ped.done.old-rig": "Das alte Rig ({name}) wurde entfernt. Vom alten Rig kann seine Gelenke weiterhin nutzen.",
    "ped.op.remove-shape-keys": "Formschlüssel entfernen",
    "ped.op.remove-shape-keys.desc": (
        "Die Formschlüssel der Meshes der Figur entfernen und die Form behalten, die sie zeigen"
    ),
    "ped.confirm.shape-keys": "Alle Formschlüssel der Figur entfernen? Die Form, die du jetzt siehst, bleibt.",
    "ped.done.shape-keys": "Die Formschlüssel von {count} Meshes wurden entfernt.",
    "ped.op.scale": "Skalieren",
    "ped.op.scale.desc": "Die Figur um den Ursprung skalieren, wie es ein Wechsel der Einheit tut",
    "ped.op.scale-by": "Mit Faktor {factor} skalieren",
    "ped.confirm.scale": "Die Figur mit Faktor {factor} skalieren?",
    "ped.done.scaled": "Die Figur wurde mit Faktor {factor} skaliert.",
    "ped.op.turn": "Drehen",
    "ped.op.turn.desc": "Die Figur in Schritten von 90 Grad drehen",
    "ped.op.stand-up": "Aufstellen",
    "ped.op.stand-up-other": "Andersherum aufstellen",
    "ped.op.turn-over": "Umdrehen",
    "ped.op.turn-left": "90° nach links drehen",
    "ped.op.turn-right": "90° nach rechts drehen",
    "ped.op.turn-around": "180° drehen",
    "ped.confirm.turn": "Die Figur drehen? Du kannst es mit Ctrl+Z rückgängig machen.",
    "ped.done.turned": "Die Figur wurde gedreht.",
    "ped.op.to-origin": "Zum Ursprung verschieben",
    "ped.op.to-origin.desc": "Die Figur so verschieben, dass sie am Ursprung auf dem Boden steht",
    "ped.done.origin": "Die Figur steht jetzt am Ursprung.",
    "ped.op.confirm-facing": "Sie schaut nach vorn",
    "ped.op.confirm-facing.desc": (
        "Bestätigen, dass die Figur zur Vorderansicht schaut, ihre linke Seite rechts von dir"
    ),
    "ped.confirm.facing": "Schaut dich die Figur in der Vorderansicht (Numpad 1) an, ihre linke Hand rechts von dir?",
    "ped.heading.parts": "Teile ({count})",
    "ped.parts.subtext": (
        "Haare, Augen und Zähne werden anders gewichtet, und Haare werden zu den Haaren des Peds. Ändere eine Rolle, "
        "wenn die Vermutung falsch ist."
    ),
    "ped.parts.guess": "Vermutet: {role}",
    "ped.prop.role": "Rolle des Teils",
    "ped.prop.role.desc": "Was dieses Mesh ist: Das entscheidet, wie es gewichtet wird und wohin es im Ped kommt",
    "ped.role.auto": "Automatisch",
    "ped.role.auto.desc": "Die Rolle anhand der Namen des Meshes und seiner Materialien erraten",
    "ped.role.body": "Körper",
    "ped.role.body.desc": "Haut und Kleidung, die sich mit dem Körper bewegen",
    "ped.role.head": "Kopf und Gesicht",
    "ped.role.head.desc": "Kopf, Gesicht, Augenbrauen und Wimpern",
    "ped.role.hair": "Haare",
    "ped.role.hair.desc": "Haare, Bärte aus Hair Cards und andere Haare, die sich mit dem Kopf bewegen",
    "ped.role.eyes": "Augen",
    "ped.role.eyes.desc": "Die Augäpfel, bewegt von den Augenknochen oder vom Kopf",
    "ped.role.teeth": "Zähne",
    "ped.role.teeth.desc": "Zähne und Zunge, bewegt vom Kopf",
    "ped.role.accessory": "Accessoire",
    "ped.role.accessory.desc": "Brillen, Schmuck und andere Dinge, die die Figur trägt",
    "ped.heading.markers": "Gelenkmarker",
    "info.ped-markers": (
        "Marker zeigen Durty Cloth Tool, wo die Gelenke deiner Figur sind: im Körper, in der Mitte jedes Gelenks. "
        "Linke Marker sind blau, rechte orange; die linke Seite der Figur ist in der Vorderansicht rechts von dir."
    ),
    "ped.markers.placed": "{placed} von {total} gesetzt",
    "ped.op.guide": "Klickhilfe",
    "ped.op.guide.desc": (
        "Nacheinander die Punkte anklicken, die eine Skizze in der 3D-Ansicht zeigt; die übrigen werden daraus gesetzt"
    ),
    "ped.op.auto-markers": "Auto-Marker",
    "ped.op.auto-markers.desc": "Jeden Marker anhand der Form der Figur setzen. Prüfe sie danach",
    "ped.op.from-rig": "Vom alten Rig",
    "ped.op.from-rig.desc": (
        "Die Marker auf die Gelenke des alten Rigs der Figur setzen (Mixamo, Unreal, Rigify, Character Creator oder "
        "VRM)"
    ),
    "ped.op.mirror": "Spiegeln",
    "ped.op.mirror.desc": "Die Marker einer Seite an der Mitte der Figur gespiegelt auf die andere Seite kopieren",
    "ped.op.mirror-left": "Links nach rechts",
    "ped.op.mirror-right": "Rechts nach links",
    "ped.op.show": "Zeigen",
    "ped.op.show-markers.desc": "Diese Marker in der 3D-Ansicht auswählen",
    "ped.prop.marker-size": "Markergröße",
    "ped.prop.marker-size.desc": "Wie groß die Markerkugeln gezeichnet werden",
    "ped.prop.follow": "Ellbogen und Knie mitbewegen",
    "ped.prop.follow.desc": (
        "Wenn du einen Handgelenk-, Schulter-, Knöchel- oder Hüftmarker verschiebst, bewegt sich der Ellbogen oder das "
        "Knie dazwischen mit dem Arm oder Bein mit"
    ),
    "ped.done.auto-markers": (
        "Die Marker wurden anhand der Form der Figur gesetzt. Prüfe jeden und verschiebe alle, die danebenliegen."
    ),
    "ped.done.from-rig": "Die Marker wurden auf die Gelenke des {rig}-Rigs gesetzt. Prüfe das Kinn und den Scheitel.",
    "ped.done.mirrored": "Die Marker wurden gespiegelt.",
    "ped.rig-kind.mixamo": "Mixamo",
    "ped.rig-kind.unreal": "Unreal",
    "ped.rig-kind.rigify": "Rigify",
    "ped.rig-kind.cc": "Character Creator",
    "ped.rig-kind.vrm": "VRM",
    "ped.marker-error.too-small": "Die Figur ist zu klein oder steht nicht: Auto-Marker hat keine Person gefunden.",
    "ped.marker-error.guide-incomplete": "Die Klickhilfe braucht alle ihre Punkte, bevor sie die übrigen setzen kann.",
    "ped.marker-error.no-rig": (
        "Die Figur hat kein altes Rig mit bekannten Knochennamen (Mixamo, Unreal, Rigify, Character Creator oder VRM)."
    ),
    "ped.marker-note.arms": (
        "Die Arme ließen sich nicht vom Körper unterscheiden: Prüfe Schultern, Ellbogen und Handgelenke."
    ),
    "ped.marker-note.legs": "Die Beine ließen sich nicht unterscheiden: Prüfe Hüften, Knie und Knöchel.",
    "ped.marker-note.neck": "Der Hals war schwer zu finden: Prüfe Hals, Kinn und Brust.",
    "ped.marker-problem.missing": "Fehlende Marker: {names}.",
    "ped.marker-problem.side": (
        "Auf der falschen Seite: {names}. Die linke Seite der Figur muss bei +X liegen, in der Vorderansicht rechts "
        "von dir."
    ),
    "ped.marker-problem.order": "Nicht in der Reihenfolge vom Kopf abwärts: {names}.",
    "ped.marker-problem.asymmetric": "Linke und rechte Gliedmaßen weichen um mehr als 30 % voneinander ab: {names}.",
    "ped.marker-problem.outside": "Außerhalb der Figur: {names}.",
    "ped.marker.headTop": "Scheitel",
    "ped.marker.chin": "Kinn",
    "ped.marker.neck": "Hals",
    "ped.marker.chest": "Brust",
    "ped.marker.pelvis": "Becken",
    "ped.marker.shoulderL": "Linke Schulter",
    "ped.marker.shoulderR": "Rechte Schulter",
    "ped.marker.elbowL": "Linker Ellbogen",
    "ped.marker.elbowR": "Rechter Ellbogen",
    "ped.marker.wristL": "Linkes Handgelenk",
    "ped.marker.wristR": "Rechtes Handgelenk",
    "ped.marker.hipL": "Linke Hüfte",
    "ped.marker.hipR": "Rechte Hüfte",
    "ped.marker.kneeL": "Linkes Knie",
    "ped.marker.kneeR": "Rechtes Knie",
    "ped.marker.ankleL": "Linker Knöchel",
    "ped.marker.ankleR": "Rechter Knöchel",
    "ped.marker.toeL": "Linke Zehen",
    "ped.marker.toeR": "Rechte Zehen",
    "ped.guide.title": "Klickhilfe: Punkt {index} von {total}",
    "ped.guide.keys": (
        "Klick: Punkt setzen. Rechtsklick: einen Punkt zurück. Mausrad und mittlere Maustaste: Ansicht. Esc: beenden."
    ),
    "ped.guide.headTop": "Klicke oben auf den Kopf.",
    "ped.guide.chin": "Klicke auf die Kinnspitze.",
    "ped.guide.shoulderL": "Klicke auf das linke Schultergelenk (in der Vorderansicht rechts von dir).",
    "ped.guide.shoulderR": "Klicke auf das rechte Schultergelenk (links von dir).",
    "ped.guide.wristL": "Klicke in die Mitte des linken Handgelenks.",
    "ped.guide.wristR": "Klicke in die Mitte des rechten Handgelenks.",
    "ped.guide.hipL": "Klicke auf das linke Hüftgelenk, wo das Bein auf den Körper trifft.",
    "ped.guide.hipR": "Klicke auf das rechte Hüftgelenk.",
    "ped.guide.ankleL": "Klicke in die Mitte des linken Knöchels.",
    "ped.guide.ankleR": "Klicke in die Mitte des rechten Knöchels.",
    "ped.guide.toeL": "Klicke auf den linken Fuß, wo die Zehen abknicken.",
    "ped.guide.toeR": "Klicke auf den rechten Fuß, wo die Zehen abknicken.",
    "ped.guide.finish": "Alle Punkte gesetzt. Drücke Enter.",
    "ped.guide.missed": "Dieser Klick hat die Figur verfehlt. Klicke auf die Figur.",
    "ped.guide.done": (
        "Alle Punkte gesetzt; Hals, Brust, Becken, Ellbogen und Knie wurden daraus gesetzt. Prüfe sie und verschiebe "
        "alle, die danebenliegen."
    ),
    "ped.heading.template": "Vorlage",
    "info.ped-template": (
        "Der installierte GTA V Ped, aus dem dein Ped gebaut wird: sein Skelett, seine Bewegung, seine Stimme und "
        "seine Körperformen. Wähle einen, der deiner Figur ähnelt: dasselbe Geschlecht und ein ähnlicher Körperbau."
    ),
    "ped.prop.template": "Vorlage",
    "ped.prop.template.desc": "Der installierte Ped, dessen Skelett deine Figur bekommt",
    "ped.prop.gender": "Geschlecht",
    "ped.gender.any": "Alle",
    "ped.gender.any.desc": "Vorlagen beider Geschlechter auflisten",
    "ped.gender.male.desc": "Männliche Vorlagen auflisten",
    "ped.gender.female.desc": "Weibliche Vorlagen auflisten",
    "ped.prop.show-all": "Alle zeigen",
    "ped.prop.show-all.desc": (
        "Auch Freemode-, Spieler-, Zwischensequenz- und Story-Peds auflisten, nicht nur Passanten"
    ),
    "ped.template.choose": "Vorlage wählen",
    "ped.template.recommended": "{model} (empfohlen)",
    "ped.template.facts": "{facts}",
    "ped.templates.loading": "Durty Cloth Tool liest deine Spieldateien (beim ersten Mal einige Sekunden).",
    "ped.templates.refresh": "Wähle Aktualisieren, um die Vorlagen aufzulisten, die mit deinem Spiel installiert sind.",
    "ped.templates.none": "Keine Vorlage passt. Schalte Alle zeigen ein oder wähle ein anderes Geschlecht.",
    "ped.templates.truncated": "Durty Cloth Tool listet die ersten {count}. Wähle ein Geschlecht, um weitere zu sehen.",
    "ped.group.ambient": "Passant",
    "ped.group.freemode": "Freemode",
    "ped.group.player": "Spieler",
    "ped.group.cutscene": "Zwischensequenz",
    "ped.group.story": "Story",
    "ped.layout.packed": "gepackt",
    "ped.layout.streamed": "gestreamt",
    "ped.op.refresh": "Aktualisieren",
    "ped.op.refresh.desc": "Durty Cloth Tool erneut nach den Vorlagen fragen, die mit deinem Spiel installiert sind",
    "ped.op.use-template": "Vorlage nutzen",
    "ped.op.use-template.desc": "Diesen installierten Ped als Vorlage nutzen",
    "ped.op.use-template-named": "{template} nutzen",
    "ped.rights.title": "Deine Rechte an dieser Figur",
    "ped.rights.text": (
        "Konvertiere nur Figuren, die du selbst gemacht hast oder in GTA V Ressourcen verwenden darfst (zum Beispiel "
        "mit einer Lizenz, die Änderung und Weitergabe erlaubt). Figuren aus anderen Spielen, aus Filmen oder von "
        "anderen Creatorn dürfen meist nicht konvertiert oder geteilt werden. Du bist für die Figuren verantwortlich, "
        "die du konvertierst und veröffentlichst."
    ),
    "ped.rights.check": "Ich habe diese Figur gemacht oder habe die Rechte, sie zu konvertieren und zu nutzen",
    "ped.rights.done": "Du hast deine Rechte an dieser Figur bestätigt.",
    "ped.op.rig": "In Durty Cloth Tool riggen",
    "ped.op.rig.desc": (
        "Durty Cloth Tool passt das Skelett der Vorlage an deine Marker an und berechnet die Gewichte und die Ruhepose "
        "des Spiels, aus deinen eigenen Spieldateien"
    ),
    "ped.op.rig-again": "Erneut riggen",
    "ped.op.cancel-rig.desc": "Das Riggen in Durty Cloth Tool abbrechen",
    "ped.rig.waiting": "Warte darauf, dass Durty Cloth Tool das Riggen startet.",
    "ped.rig.cancelling": "Das Riggen wird abgebrochen.",
    "ped.rig.working": "Wird geriggt",
    "ped.rig.progress": "{stage} ({percent} %)",
    "ped.stage.template": "Vorlage wird gelesen",
    "ped.stage.markers": "Marker werden geprüft",
    "ped.stage.skeleton": "Skelett wird angepasst",
    "ped.stage.weights": "Gewichte werden übertragen",
    "ped.stage.rest": "Wird in die Ruhepose des Spiels gebracht",
    "ped.stage.report": "Bericht wird geschrieben",
    "ped.prop.refine": "Marker verfeinern",
    "ped.prop.refine.desc": (
        "Durty Cloth Tool verschiebt die Marker in die Mitte der Gliedmaßen und des Körpers und zeigt dir, wohin"
    ),
    "ped.prop.fingers": "Finger",
    "ped.fingers.off": "Mit der Hand bewegen",
    "ped.fingers.off.desc": "Die Finger bewegen sich mit der Hand, wie bei einem Fäustling",
    "ped.fingers.auto": "Automatisch",
    "ped.fingers.auto.desc": "Die Finger anhand der Hand der Vorlage gewichten",
    "ped.prop.face": "Gesicht",
    "ped.face.off": "Mit dem Kopf bewegen",
    "ped.face.off.desc": "Das Gesicht bewegt sich mit dem Kopf",
    "ped.face.auto": "Automatisch",
    "ped.face.auto.desc": "Das Gesicht anhand des Gesichts der Vorlage gewichten, für Mimik",
    "ped.prop.roll": "Roll-Knochen",
    "ped.prop.roll.desc": (
        "Die Drehknochen von Armen und Beinen gewichten, die verhindern, dass Handgelenke und Oberschenkel einfallen"
    ),
    "ped.prop.helpers": "Hilfsknochen",
    "ped.prop.helpers.desc": "Die Hilfsknochen der Vorlage gewichten, so wie bei ihrem eigenen Körper",
    "ped.prop.rest": "Ruheform",
    "ped.rest.volume": "Volumen erhalten",
    "ped.rest.volume.desc": "Die Figur so in die Ruhepose bringen, dass Schultern und Hüften ihr Volumen behalten",
    "ped.rest.linear": "Exakt",
    "ped.rest.linear.desc": (
        "Die Figur so in die Ruhepose bringen, dass das Skinning des Spiels genau deine Pose zurückgibt"
    ),
    "ped.result.ready": "Bereit (Sicherheit {percent} %)",
    "ped.result.review": "Bitte prüfen (Sicherheit {percent} %)",
    "ped.result.markers": "({names})",
    "ped.result.moved": (
        "Durty Cloth Tool hat {count} Marker in die Mitte des Körpers verschoben (gelb in der 3D-Ansicht):"
    ),
    "ped.result.move": "{marker}: {cm} cm",
    "ped.result.subtext": (
        "Rig anwenden baut die Armature und gibt den Meshes ihre Gewichte und die Ruhepose des Spiels. Deine Figur "
        "behält ihr Aussehen, und Ctrl+Z macht es rückgängig."
    ),
    "ped.result.proxy": "Die Gewichte wurden auf einer vereinfachten Kopie dieses großen Meshes berechnet.",
    "ped.op.apply-rig": "Rig anwenden",
    "ped.op.apply-rig.desc": (
        "Die Armature aus dem Rig bauen und den Meshes seine Gewichte und die Ruhepose des Spiels geben; die Figur "
        "behält ihr Aussehen"
    ),
    "ped.op.use-refined": "Diese Marker nutzen",
    "ped.op.use-refined.desc": "Deine Marker dorthin verschieben, wo Durty Cloth Tool sie hingesetzt hat",
    "ped.op.discard-rig": "Verwerfen",
    "ped.op.discard-rig.desc": "Dieses Rig verwerfen, ohne es anzuwenden",
    "ped.done.applied": "Rig angewendet: Die Armature {name} hat {bones} Knochen.",
    "ped.done.refined": "Deine Marker sitzen jetzt dort, wo Durty Cloth Tool sie hingesetzt hat.",
    "ped.rigged.line": "Geriggt mit {template} ({bones} Knochen)",
    "ped.op.previous-rig": "Vorheriges Rig",
    "ped.op.previous-rig.desc": "Das angewendete Rig mit dem davor angewendeten tauschen",
    "ped.done.previous": "Das vorherige Rig ist zurück.",
    "ped.op.remove-rig": "Rig entfernen",
    "ped.op.remove-rig.desc": "Das Rig entfernen: Die Figur ist wieder so wie vor dem ersten Rig",
    "ped.confirm.remove-rig": (
        "Das Rig entfernen? Die Armatures werden entfernt, und die Figur ist wieder so wie vor dem ersten Rig."
    ),
    "ped.done.removed": "Rig entfernt. Die Figur ist wieder so wie vor dem Riggen.",
    "ped.warning.marker_offset": (
        "{count} Marker lagen mehr als 2 cm neben der Mitte des Körpers (bis zu {value} mm). Prüfe sie."
    ),
    "ped.warning.asymmetric_markers": (
        "Die linken und rechten Marker weichen um mehr als 5 % voneinander ab. Prüfe beide Seiten."
    ),
    "ped.warning.proportion_out_of_range": (
        "Einige Proportionen weichen stark von denen der Vorlage ab. Eine Vorlage mit ähnlicherem Körperbau bewegt "
        "sich besser."
    ),
    "ped.warning.ragdoll_mismatch": (
        "Die Größe dieser Figur weicht stark von der ihrer Vorlage ab. Im Spiel nutzen Schüsse und Stürze die "
        "Körperformen der Vorlage, Treffer können also danebengehen oder neben dem Modell landen. Wähle eine "
        "passendere Vorlage oder teste im Spiel, bevor du veröffentlichst."
    ),
    "ped.warning.low_coverage": (
        "Nur ein Teil der Figur passte zum Körper der Vorlage. Prüfe die Gewichte in den Testposen."
    ),
    "ped.warning.inpainted_large": "Viele Gewichte wurden aus ihren Nachbarn aufgefüllt. Prüfe die Testposen.",
    "ped.warning.non_deforming_moved": "Einige Gewichte wurden von Knochen genommen, die das Mesh nie bewegen.",
    "ped.warning.empty_rows_refilled": "{count} Vertices hatten keine Gewichte und haben die ihrer Nachbarn bekommen.",
    "ped.warning.floating_parts": "{count} lose Teile wurden an den nächsten Knochen gebunden.",
    "ped.warning.rest_strain": (
        "Einige Dreiecke klappen in der Ruhepose des Spiels um. Sieh dir in der Testpose Spiel-Ruhepose die Schultern "
        "und Hüften an."
    ),
    "ped.warning.fingers_fallback": "Die Finger bewegen sich mit der Hand.",
    "ped.warning.other": "Durty Cloth Tool meldet {code}.",
    "ped.suggest": (
        "{template} passt besser zu den Proportionen deiner Figur. Nutze diese Vorlage und rigge erneut für eine "
        "bessere Passform."
    ),
    "ped.refusal.marker_missing": "Es fehlen Marker.",
    "ped.refusal.marker_invalid": "Einige Marker sind nicht nutzbar. Setze sie erneut auf die Figur.",
    "ped.refusal.marker_degenerate": "Einige Marker liegen aufeinander.",
    "ped.refusal.marker_side": (
        "Links und rechts sind vertauscht. Die linke Seite der Figur muss bei +X liegen: Prüfe, ob sie nach vorn "
        "schaut."
    ),
    "ped.refusal.not_upright": "Die Figur steht nicht aufrecht, oder ihr Kopf liegt unter ihrem Hals.",
    "ped.refusal.limb_length": "Ein Arm oder Bein ist viel kürzer oder länger als bei der Vorlage. Prüfe diese Marker.",
    "ped.refusal.asymmetric": "Die linken und rechten Gliedmaßen weichen um mehr als 30 % voneinander ab.",
    "ped.refusal.pose_unsupported": (
        "Ein Bein ist zu stark gebeugt oder gespreizt. Stelle die Figur gerade hin, in A-Pose oder T-Pose."
    ),
    "ped.refusal.marker_outside_body": "Diese Marker liegen außerhalb der Figur.",
    "ped.refusal.mesh_invalid": (
        "Durty Cloth Tool konnte das Mesh nicht lesen (leer oder größtenteils flache Dreiecke)."
    ),
    "ped.refusal.mesh_too_large": (
        "Die Figur hat zu viele Vertices oder Dreiecke für ein Rig. Reduziere zuerst eine Kopie."
    ),
    "ped.refusal.options_invalid": "Durty Cloth Tool hat die Optionen des Rigs abgelehnt. Aktualisiere das Add-on.",
    "ped.refusal.template_invalid": "Durty Cloth Tool kann diese Vorlage nicht nutzen. Wähle eine andere.",
    "ped.refusal.template_not_found": (
        "Diese Vorlage ist nicht installiert. Aktualisiere die Liste und wähle eine andere."
    ),
    "ped.refusal.game_required": (
        "Durty Cloth Tool braucht deinen GTA V Ordner. Richte ihn in den Einstellungen von Durty Cloth Tool ein."
    ),
    "ped.refusal.fit_invalid": "Das Rig ist fehlerhaft geworden. Prüfe die Marker an der Figur und rigge erneut.",
    "ped.refusal.other": "Durty Cloth Tool hat das Rig abgelehnt ({code}).",
    "ped.heading.poses": "Testposen",
    "info.ped-poses": (
        "Einfache Beugungen nach Knochennamen, damit du siehst, wie die Gewichte die Figur bewegen. Das sind keine "
        "Spielanimationen; kleine Falten in extremen Stellungen sind normal."
    ),
    "ped.pose.yours": "Deine Pose",
    "ped.pose.rest": "Spiel-Ruhepose",
    "ped.pose.arms_up": "Arme hoch",
    "ped.pose.arms_forward": "Arme nach vorn",
    "ped.pose.squat": "Hocke",
    "ped.pose.walk": "Schritt",
    "ped.pose.twist": "Drehung",
    "ped.op.pose": "Pose",
    "ped.op.pose.desc": "Die Figur in dieser Pose zeigen",
    "ped.op.run-checks": "Prüfungen ausführen",
    "ped.op.run-checks.desc": "Die Gewichte, die Armature und die Meshes am Rig prüfen, dazu die Testposen",
    "ped.op.show-finding.desc": "Die Vertices auswählen, die dieser Befund betrifft",
    "ped.done.checks": (
        "Prüfungen ausführen hat {count} Dinge zum Ansehen gefunden; nichts, was Durty Cloth Tool ablehnen würde."
    ),
    "ped.done.checks-refused": (
        "Prüfungen ausführen hat {count} Probleme gefunden, die Durty Cloth Tool ablehnen würde."
    ),
    "ped.local.none": "Keine Probleme gefunden.",
    "ped.local.unweighted": "{count} Vertices haben kein Gewicht. Durty Cloth Tool lehnt sie ab: Gewichte sie.",
    "ped.local.too-many": "{count} Vertices haben mehr als vier Knochen. Das Spiel behält die vier stärksten.",
    "ped.local.non-deforming": "{count} Vertices sind auf Knochen gewichtet, die das Mesh nie bewegen.",
    "ped.local.unknown-groups": "Vertexgruppen, die keine Knochen sind ({names}), werden weggelassen.",
    "ped.local.armature-changed": (
        "{count} Knochen wurden nach dem Riggen verschoben oder gedreht ({names}). Mach das rückgängig oder rigge "
        "erneut: Knochen behalten die Drehung der Vorlage."
    ),
    "ped.local.mesh-changed": (
        "Die Meshes haben sich nach dem Riggen geändert (Vertices hinzugefügt oder entfernt). Rigge erneut."
    ),
    "ped.local.strain": "{count} Vertices werden in {pose} stark gedehnt oder gestaucht.",
    "ped.local.hint": (
        "Kleine Falten in extremen Posen sind normal. Bei größeren verschiebe einen Marker und rigge erneut."
    ),
    "ped.prop.name": "Ped-Name",
    "ped.prop.name.desc": "Der Name, den Durty Cloth Tool für den Ped zeigt",
    "ped.prop.model": "Modellname",
    "ped.prop.model.desc": (
        "Der Name des neuen Peds im Spiel: ein Kleinbuchstabe, dann 2 bis 31 Kleinbuchstaben, Ziffern oder Unterstriche"
    ),
    "ped.prop.ragdoll": "Ragdoll-Körper",
    "ped.ragdoll.template": "Wie die Vorlage",
    "ped.ragdoll.template.desc": "Der gemeinsame Ragdoll-Körper, den die Vorlage nutzt",
    "ped.ragdoll.fred": "Standard männlich",
    "ped.ragdoll.fred.desc": "Der gemeinsame Ragdoll-Körper der meisten männlichen Peds",
    "ped.ragdoll.wilma": "Standard weiblich",
    "ped.ragdoll.wilma.desc": "Der gemeinsame Ragdoll-Körper der meisten weiblichen Peds",
    "ped.ragdoll.fred-large": "Groß männlich",
    "ped.ragdoll.fred-large.desc": "Der gemeinsame Ragdoll-Körper großer männlicher Peds",
    "ped.ragdoll.wilma-large": "Groß weiblich",
    "ped.ragdoll.wilma-large.desc": "Der gemeinsame Ragdoll-Körper großer weiblicher Peds",
    "ped.ragdoll.subtext": (
        "Schüsse, Stürze und die Ragdoll nutzen im Spiel die Formen dieses Körpers. Wähle einen großen für eine viel "
        "größere Figur."
    ),
    "ped.texture.too-large": "Das Bild {name} ist an einer Seite größer als 4096 Pixel. Durty Cloth Tool lehnt es ab.",
    "ped.texture.not-multiple-of-four": (
        "Breite oder Höhe des Bilds {name} ist nicht durch vier teilbar. Durty Cloth Tool lehnt es ab."
    ),
    "ped.texture.non-power-of-two": (
        "Die Größe des Bilds {name} ist keine Zweierpotenz (etwa 1024 oder 2048). Es geht, aber solche Größen "
        "sehen am besten aus."
    ),
    "ped.op.send": "Eigenen Ped erstellen",
    "ped.op.send.desc": (
        "Die geriggte Figur in der Ruhepose des Spiels exportieren und an Durty Cloth Tool senden, das ein neues "
        "Projekt für einen eigenen Ped erstellt, sobald du dort bestätigst"
    ),
    "ped.op.cancel-send.desc": "Die Figur zurückziehen, solange Durty Cloth Tool noch fragt",
    "ped.send.subtext": (
        "Durty Cloth Tool zeigt den Ped mit seinen Prüfungen und fragt, wo das Projekt erstellt wird. Nichts wird "
        "erstellt, bis du dort Projekt erstellen wählst."
    ),
    "ped.send.waiting": "Die Figur wurde gesendet ({size} MiB). Wähle Projekt erstellen in Durty Cloth Tool.",
    "ped.send.withdrawing": "Die Figur wird zurückgezogen.",
    "ped.send.withdrawn": "Zurückgezogen: Durty Cloth Tool hat nichts erstellt.",
    "ped.send.created": "Durty Cloth Tool hat das Projekt {name} mit dem Ped {model} aus {template} erstellt.",
    "ped.send.created-late": (
        "Durty Cloth Tool hat das Projekt {name} mit dem Ped {model} doch erstellt: Dort wurde Erstellen "
        "gewählt, gerade als die Figur zurückgezogen wurde."
    ),
    "ped.send.findings": "Prüfungen von Durty Cloth Tool ({count}):",
    "ped.send.next": (
        "Prüfe das Verhalten des Peds in Durty Cloth Tool (Ped-Typ, Bewegung, Stimme) und baue dann das Projekt."
    ),
    "ped.finding.rig-mismatch": (
        "Das Skelett ist nicht das der Vorlage oder des Rigs: Ein Knochen wurde verschoben oder gedreht. Wende das Rig "
        "erneut an oder rigge erneut."
    ),
    "ped.finding.ped-budget": "Mehr Vertices, als ein Ped in seiner detailliertesten Stufe haben sollte.",
    "ped.finding.ped-ragdoll-mismatch": (
        "Die Größe der Figur weicht stark vom Ragdoll-Körper der Vorlage ab: Treffer und Stürze nutzen im Spiel die "
        "Körperformen der Vorlage."
    ),
    "ped.finding.ped-rest-strain": "Das Rig hat einige Dreiecke in der Ruhepose des Spiels umgeklappt.",
    "ped.why.select-meshes": "Wähle zuerst die Meshes deiner Figur aus.",
    "ped.why.no-character": "Wähle zuerst unter Figur deine Figur.",
    "ped.why.object-mode": "Wechsle zuerst in den Objektmodus.",
    "ped.why.rigged": "Die Figur ist geriggt. Entferne das Rig, um sie zu ändern.",
    "ped.why.no-markers": "Setze zuerst die Marker.",
    "ped.why.guide-running": "Die Klickhilfe läuft.",
    "ped.why.view3d": "Starte die Klickhilfe aus der Seitenleiste der 3D-Ansicht.",
    "ped.why.checks": "Behebe zuerst, was die Prüfungen unter Figur nennen.",
    "ped.why.markers": "Setze zuerst alle Marker.",
    "ped.why.connect": "Verbinde dich mit Durty Cloth Tool, um eine Vorlage zu wählen und zu riggen.",
    "ped.why.template": "Wähle zuerst eine Vorlage.",
    "ped.why.rights": "Bestätige zuerst deine Rechte an dieser Figur.",
    "ped.why.rigging": "Durty Cloth Tool riggt gerade.",
    "ped.why.not-rigging": "Gerade wird nicht geriggt.",
    "ped.why.no-result": "Es gibt kein Rig zum Anwenden. Rigge die Figur zuerst.",
    "ped.why.no-previous": "Es gibt kein vorheriges Rig.",
    "ped.why.not-rigged": "Rigge die Figur zuerst.",
    "ped.why.mesh-changed": (
        "Die Meshes der Figur haben sich geändert, nachdem du dieses Rig angefordert hast. Rigge erneut."
    ),
    "ped.why.vertex-count": (
        "{name} ändert in einem Modifikator seine Vertexanzahl. Wende zuerst seine Modifikatoren an."
    ),
    "ped.why.modifiers-shape-keys": (
        "{name} hat Formschlüssel, darum lassen sich seine Modifikatoren nicht anwenden. Entferne sie zuerst."
    ),
    "ped.why.export-failed": (
        "Der glTF-Exporter von Blender hat die Figur nicht geschrieben. Sein Info-Log zeigt die Details."
    ),
    "ped.why.model": "Der Modellname ist ein Kleinbuchstabe, dann 2 bis 31 Kleinbuchstaben, Ziffern oder Unterstriche.",
    "ped.why.model-game": (
        "Namen, die mit {prefix} beginnen, gehören zu den eigenen Peds des Spiels. Wähle einen anderen, etwa "
        "{suggestion}."
    ),
    "ped.why.name": "Gib dem Ped einen Namen.",
    "ped.why.transforms-first": "Wende zuerst die Transformationen an.",
    "ped.why.refused-checks": (
        "Prüfungen ausführen hat Probleme gefunden, die Durty Cloth Tool ablehnen würde. Behebe sie zuerst."
    ),
    "ped.why.textures": "Ein Bild ist zu groß, oder seine Größe ist nicht durch vier teilbar. Behebe das zuerst.",
    "ped.why.sending": "Ein eigener Ped wird gesendet.",
    "ped.why.not-sending": "Es wird nichts gesendet.",
    "ped.invalid": "Das Add-on konnte diese Anfrage nicht vorbereiten: {detail}",
    "ped.plan.rig": "Das Riggen ist in Durty Cloth Tool Ultimate enthalten.",
    "ped.plan.add": "Ein Projekt für einen eigenen Ped zu erstellen braucht Durty Cloth Tool Advanced oder Ultimate.",
    "ped.error.rig-busy": "Durty Cloth Tool riggt gerade eine andere Figur. Versuche es erneut, wenn es fertig ist.",
    "ped.error.rig-cancelled": "Das Riggen wurde abgebrochen.",
    "ped.error.rig-refused": "Durty Cloth Tool konnte die Figur nicht riggen:",
    "ped.error.dct-too-old": (
        "Dieses Durty Cloth Tool kann noch keine eigenen Peds aus Blender erstellen. Aktualisiere Durty Cloth Tool."
    ),
    "ped.error.rig-disconnected": (
        "Die Verbindung zu Durty Cloth Tool wurde während des Riggens unterbrochen. Rigge erneut."
    ),
    "ped.error.rig-timeout": "Durty Cloth Tool hat das Riggen nicht rechtzeitig beendet. Rigge erneut.",
    "ped.error.add-busy": (
        "Durty Cloth Tool ist mit einem anderen eigenen Ped oder einem Build beschäftigt. Versuche es erneut, wenn es "
        "fertig ist."
    ),
    "ped.error.add-denied": "In Durty Cloth Tool abgebrochen. Sende die Figur erneut, wenn du bereit bist.",
    "ped.error.model-rejected": (
        "Durty Cloth Tool konnte aus der Figur keinen Ped machen. Seine Prüfungen unten zeigen, warum."
    ),
    "ped.error.save-failed": (
        "Durty Cloth Tool konnte das Projekt nicht erstellen. Wähle einen anderen Ordner und sende erneut."
    ),
    "ped.error.add-disconnected": (
        "Die Verbindung zu Durty Cloth Tool wurde unterbrochen, bevor es geantwortet hat. Sende die Figur erneut."
    ),
    "ped.error.add-timeout": "Durty Cloth Tool hat nicht rechtzeitig geantwortet. Sende die Figur erneut.",
    "ped.error.add-unanswered": "Durty Cloth Tool hat das Zurückziehen nicht bestätigt. Prüfe seine Projektliste.",
    "error.template-not-found": "Diese Vorlage ist nicht installiert. Aktualisiere die Liste und wähle eine andere.",
    "error.mesh-too-large": "Die Figur hat zu viele Vertices oder Dreiecke. Reduziere zuerst eine Kopie.",
    "error.rig-refused": "Durty Cloth Tool konnte die Figur nicht riggen.",
    "error.upload-incomplete": "Die Figur ist nicht vollständig in Durty Cloth Tool angekommen. Sende sie erneut.",
}
