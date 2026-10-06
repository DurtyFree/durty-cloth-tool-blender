# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2026 Schmid Software Solutions (https://schmid-software.de)
"""German (Deutsch): the garment fitting texts. Informal "du", as Durty Cloth Tool uses it."""

TEXT = {
    "garment.panel": "Kleidung anpassen (experimentell)",
    "garment.panel.setup": "Einrichtung",
    "garment.panel.fit": "Anpassen",
    "garment.panel.fix": "Korrigieren",
    "garment.panel.ready": "Spielfertig",
    "garment.next.import": (
        "Importiere ein Kleidungsstück oder wähle deines aus und dann Ausgewähltes Kleidungsstück nutzen."
    ),
    "garment.next.body": "Weiter: Füge unter Einrichtung den Freemode-Körper hinzu.",
    "garment.next.markers": "Weiter: Setze die Marker unter Anpassen mit Auto-Marker und prüfe dann, wo sie sitzen.",
    "garment.next.check": "Weiter: Passform prüfen unter Korrigieren.",
    "garment.next.push": (
        "Weiter: Teile des Kleidungsstücks liegen im Körper. Nutze Aus dem Körper schieben unter Korrigieren."
    ),
    "garment.next.prepare": "Weiter: Kleidungsstück vorbereiten unter Spielfertig.",
    "garment.next.combine": (
        "Weiter: Materialien zusammenfassen unter Spielfertig, damit das Kleidungsstück eine Textur nutzt."
    ),
    "garment.next.lods": "Weiter: LODs erzeugen unter Spielfertig.",
    "garment.next.validate": "Weiter: Validieren unter Spielfertig.",
    "garment.next.sculpting": (
        "Sculpting: Ziehe mit dem Grab-Pinsel und wähle dann unter Korrigieren Übernehmen oder Abbrechen."
    ),
    "garment.gender.male.desc": "Das männliche Freemode-Ped (mp_m_freemode_01)",
    "garment.gender.female.desc": "Das weibliche Freemode-Ped (mp_f_freemode_01)",
    "garment.slot.jbib": "Oberteil (jbib)",
    "garment.slot.jbib.desc": "Jacken und Oberteile",
    "garment.slot.accs": "Unterhemd (accs)",
    "garment.slot.accs.desc": "Unterhemden, die unter einem Oberteil getragen werden",
    "garment.slot.lowr": "Beine (lowr)",
    "garment.slot.lowr.desc": "Hosen, Shorts und Röcke",
    "garment.slot.feet": "Schuhe (feet)",
    "garment.slot.feet.desc": "Schuhe und Stiefel",
    "garment.category.vest": "Ärmellos",
    "garment.category.vest.desc": "Ein Oberteil ohne Ärmel",
    "garment.category.tshirt": "T-Shirt",
    "garment.category.tshirt.desc": "Ein Oberteil mit kurzen Ärmeln",
    "garment.category.long_sleeve": "Langarm",
    "garment.category.long_sleeve.desc": "Ein Oberteil mit Ärmeln bis zu den Handgelenken",
    "garment.category.long_jacket": "Lange Jacke oder Tunika",
    "garment.category.long_jacket.desc": "Ein Oberteil mit langen Ärmeln, das bis unter die Hüften reicht",
    "garment.category.pants": "Lange Hose",
    "garment.category.pants.desc": "Hosen, die bis zu den Knöcheln reichen",
    "garment.category.shorts": "Kurze Hose",
    "garment.category.shorts.desc": "Hosen, die an oder über den Knien enden",
    "garment.category.shoes": "Schuhe",
    "garment.category.shoes.desc": "Schuhe, Stiefel und Sandalen",
    "garment.pose.a_pose": "A-Pose",
    "garment.pose.a_pose.desc": "Die Arme zeigen schräg nach unten, so wie das Ped im Spiel steht",
    "garment.pose.t_pose": "T-Pose",
    "garment.pose.t_pose.desc": "Die Arme zeigen gerade zur Seite",
    "garment.pose.custom": "Eigene",
    "garment.pose.custom.desc": "Eine andere Pose: Prüfe die Marker und verschiebe sie von Hand auf die Gelenke",
    "garment.region.shoulders": "Schultern",
    "garment.region.upper_arms": "Oberarme",
    "garment.region.chest": "Brust",
    "garment.region.back": "Rücken",
    "garment.region.waist": "Taille",
    "garment.region.hips": "Hüften",
    "garment.region.neck": "Hals",
    "garment.region.legs": "Beine",
    "garment.region.desc": "Ein Teil des Kleidungsstücks, anhand der Marker bestimmt",
    "garment.level.high": "Hoch",
    "garment.level.medium": "Mittel",
    "garment.level.low": "Niedrig",
    "garment.prop.garment": "Kleidungsstück",
    "garment.prop.garment.desc": "Das Kleidungsstück, an dem die Werkzeuge arbeiten. Nur dieses Objekt wird geändert",
    "garment.prop.body": "Körper",
    "garment.prop.body.desc": "Der Freemode-Körper, an dem das Kleidungsstück gemessen wird",
    "garment.prop.gender": "Geschlecht",
    "garment.prop.gender.desc": "Für welches Freemode-Ped das Kleidungsstück ist",
    "garment.prop.slot": "Slot",
    "garment.prop.slot.desc": "Der Kleidungsslot, in den das Kleidungsstück in Durty Cloth Tool kommt",
    "garment.prop.category": "Kategorie",
    "garment.prop.category.desc": (
        "Welche Art Kleidungsstück es ist: Das legt fest, wohin die Marker kommen und welche Bereiche die Werkzeuge "
        "anbieten"
    ),
    "garment.prop.pose": "Ausgangspose",
    "garment.prop.pose.desc": "Die Pose des Avatars, auf dem das Kleidungsstück erstellt wurde",
    "garment.prop.marker-size": "Markergröße",
    "garment.prop.marker-size.desc": "Wie groß die Markerkugeln gezeichnet werden",
    "garment.prop.arm-angle": "Armwinkel",
    "garment.prop.arm-angle.desc": (
        "Wie weit unter die Waagerechte T-Pose zu A-Pose die Arme senkt, wenn die Gelenke des Körpers unbekannt sind "
        "(mit ihnen gehen die Arme auf die des Körpers)"
    ),
    "garment.prop.gap": "Abstand (mm)",
    "garment.prop.push-gap.desc": (
        "Wie weit Aus dem Körper schieben das Kleidungsstück aus dem Körper hinaus bewegt, in Millimetern"
    ),
    "garment.prop.snug-gap.desc": "Wie viel Abstand zum Körper An den Körper anlegen dem Bereich lässt, in Millimetern",
    "garment.prop.region": "Bereich",
    "garment.prop.region.desc": (
        "Der Teil des Kleidungsstücks, an dem An den Körper anlegen und Dehnung entspannen arbeiten"
    ),
    "garment.prop.amount": "Anteil",
    "garment.prop.amount.desc": "Welchen Teil des Weges der Bereich zurücklegt: 1 bewegt ihn ganz",
    "garment.prop.radius": "Pinselradius (cm)",
    "garment.prop.radius.desc": "Die Größe des Grab-Pinsels, in Zentimetern",
    "garment.prop.strength": "Stärke",
    "garment.prop.strength.desc": "Wie stark der Grab-Pinsel das Kleidungsstück bewegt",
    "garment.prop.mirror": "X spiegeln",
    "garment.prop.mirror.desc": "Beide Seiten des Kleidungsstücks gleichzeitig bearbeiten",
    "garment.prop.keep-out": "Aus dem Körper halten",
    "garment.prop.keep-out.desc": (
        "Beim Übernehmen das, was du in den Körper geschoben hast, wieder hinaus bewegen, auf den Abstand von Aus dem "
        "Körper schieben"
    ),
    "garment.prop.weld": "Schweißabstand (mm)",
    "garment.prop.weld.desc": (
        "Kanten von Schnittteilen, die näher als dieser Wert (in Millimetern) beieinanderliegen, werden zu einer Naht "
        "verbunden"
    ),
    "garment.prop.colour-1": "Color 1",
    "garment.prop.colour-1.desc": (
        "Die erste Vertexfarbe des Ped-Shaders (Color 1 in Sollumz): das Licht, das das Kleidungsstück empfängt. "
        "#FF8000 passt zu den meisten Kleidungsstücken; #FFBAFF lässt leuchtende Materialien glühen"
    ),
    "garment.prop.colour-2": "Color 2",
    "garment.prop.colour-2.desc": (
        "Die zweite Vertexfarbe des Ped-Shaders (Color 2 in Sollumz): Wind und Schweiß. Schwarz ohne Alpha schaltet "
        "beides ab"
    ),
    "garment.prop.overwrite": "Vorhandene Vertexfarben ersetzen",
    "garment.prop.overwrite.desc": "Color 1 und Color 2 auch ersetzen, wenn das Kleidungsstück sie schon hat",
    "garment.prop.size": "Texturgröße",
    "garment.size.desc": (
        "Die Größe der zusammengefassten Textur in Pixeln. Die Texturprüfung von Durty Cloth Tool rät zu 2048 oder "
        "weniger"
    ),
    "garment.prop.cut": "Lange Streifen schneiden",
    "garment.prop.cut.desc": (
        "Lange, dünne UV-Inseln wie Säume und Bünde in Stücke schneiden, damit der Rest des Kleidungsstücks mehr von "
        "der Textur bekommt"
    ),
    "garment.prop.lod-medium": "Dreiecke (Mittel)",
    "garment.prop.lod-low": "Dreiecke (Niedrig)",
    "garment.prop.lod.desc": (
        "Wie viele Dreiecke diese Detailstufe höchstens behält. 0: ein Anteil von High, höchstens so viel, wie Durty "
        "Cloth Tool empfiehlt (15.000 für Medium, 7.500 für Low)"
    ),
    "garment.prop.ground": "Avatar stand auf dem Boden",
    "garment.prop.ground.desc": (
        "Das Kleidungsstück wurde auf einem Avatar erstellt, der auf Höhe 0 steht, wie in Marvelous Designer: es zum "
        "Ped hinunter verschieben, dessen Sohlen 1 m unter seinem Ursprung liegen"
    ),
    "garment.prop.preset-name": "Name",
    "garment.heading.markers": "Marker",
    "garment.heading.tpose": "Modell in T-Pose",
    "garment.heading.backups": "Sicherungen",
    "garment.heading.push": "Abstand zum Körper",
    "garment.heading.regions": "Bereichswerkzeuge",
    "garment.heading.problems": "Probleme",
    "garment.heading.check": "Passformprüfung",
    "garment.heading.sculpt": "Von Hand korrigieren",
    "garment.heading.tears": "Risse",
    "garment.heading.prepare": "Vorbereiten",
    "garment.heading.combine": "Materialien",
    "garment.heading.lods": "Detailstufen",
    "garment.heading.validate": "Prüfungen",
    "garment.op.use": "Ausgewähltes Kleidungsstück nutzen",
    "garment.op.use.desc": "Am ausgewählten Mesh-Objekt arbeiten",
    "garment.op.import": "Kleidungsstück importieren",
    "garment.op.import.desc": (
        "Ein Kleidungsstück aus einer FBX-, OBJ- oder glTF-Datei importieren (zum Beispiel aus Marvelous Designer), "
        "in Metern und als ein Objekt"
    ),
    "garment.op.add-body": "Freemode-Körper hinzufügen",
    "garment.op.add-body.desc": (
        "Den Freemode-Körper des gewählten Geschlechts für dein Konto von gta.clothing herunterladen (einmal pro "
        "Körperversion) und zur Szene hinzufügen"
    ),
    "garment.op.cancel-body.desc": "Den Download des Körpers abbrechen",
    "garment.op.body-file": "Körperdatei nutzen",
    "garment.op.body-file.desc": (
        "Stattdessen einen Körper aus einer GLB-, glTF-, FBX- oder OBJ-Datei hinzufügen, in Metern und in der Pose "
        "des Spiels"
    ),
    "garment.op.auto-markers": "Auto-Marker",
    "garment.op.auto-markers.desc": (
        "Die Gelenkmarker anhand der Form des Kleidungsstücks setzen (Hals, Brust, Becken, Schultern, Ellbogen, "
        "Handgelenke und Hüften; bei Hosen Hüften, Knie und Knöchel). Verschiebe alle, die danebenliegen"
    ),
    "garment.op.mirror": "Links nach rechts spiegeln",
    "garment.op.mirror.desc": "Die Marker der linken Seite des Peds auf seine rechte Seite kopieren",
    "garment.op.save-preset": "Pose-Voreinstellung speichern",
    "garment.op.save-preset.desc": (
        "Die Marker als Voreinstellung im Ordner des Add-ons speichern, für ähnliche Kleidungsstücke"
    ),
    "garment.op.load-preset": "Pose-Voreinstellung laden",
    "garment.op.load-preset.desc": "Die Marker aus einer gespeicherten Voreinstellung setzen",
    "garment.op.tpose": "T-Pose zu A-Pose",
    "garment.op.tpose.desc": (
        "Die Arme eines in T-Pose erstellten Kleidungsstücks anhand der Marker auf den Armwinkel senken"
    ),
    "garment.op.restore": "Ausgangsform wiederherstellen",
    "garment.op.restore.desc": (
        "Die Form des Kleidungsstücks von vor dem ersten Anpassungsschritt wiederherstellen"
    ),
    "garment.op.push": "Aus dem Körper schieben",
    "garment.op.push.desc": (
        "Jeden Teil des Kleidungsstücks, der im Körper oder näher als der Abstand liegt, auf den Abstand hinaus "
        "bewegen"
    ),
    "garment.op.snug": "An den Körper anlegen",
    "garment.op.snug.desc": "Den gewählten Bereich näher an den Körper bringen, bis auf den Abstand",
    "garment.op.relax": "Dehnung entspannen",
    "garment.op.relax.desc": "Gedehnte Teile des gewählten Bereichs wieder an ihre ursprüngliche Größe annähern",
    "garment.op.problems": "Probleme zeigen",
    "garment.op.problems.desc": (
        "Das Kleidungsstück einfärben: Rot im Körper, Gelb zu nah, Lila gedehnt, Blau eine abstehende Schulter. "
        "Erneut wählen, um die Farben auszublenden"
    ),
    "garment.op.refresh": "Aktualisieren",
    "garment.op.refresh.desc": "Die Probleme nach einer Änderung neu einfärben",
    "garment.op.check": "Passform prüfen",
    "garment.op.check.desc": "Messen, wie weit jeder Bereich des Kleidungsstücks vom Körper absteht",
    "garment.op.sculpt": "Sculpting starten",
    "garment.op.sculpt.desc": (
        "Die Form von Hand mit dem Grab-Pinsel korrigieren. Übernehmen behält das Ergebnis, Abbrechen stellt die Form "
        "wieder her"
    ),
    "garment.op.accept": "Übernehmen",
    "garment.op.accept.desc": "Die bearbeitete Form behalten und die Sitzung beenden",
    "garment.op.cancel-sculpt.desc": "Die Form von vor der Sitzung wiederherstellen und die Sitzung beenden",
    "garment.op.tears": "Risse prüfen",
    "garment.op.tears.desc": (
        "Die Armature des Kleidungsstücks durch einige Testposen bewegen und zeigen, wo Nähte aufgehen"
    ),
    "garment.op.prepare": "Kleidungsstück vorbereiten",
    "garment.op.prepare.desc": (
        "Die Nähte zwischen den Schnittteilen verbinden, lose Teile entfernen, triangulieren, weich schattieren und "
        "die Ped-Vertexfarben hinzufügen"
    ),
    "garment.op.combine": "Materialien zusammenfassen",
    "garment.op.combine.desc": (
        "Alle UV-Inseln in ein Layout packen und jedes Material in eines backen: die Farbe mit ihrer Transparenz und, "
        "wo vorhanden, Normal-, Specular- und Emissions-Maps"
    ),
    "garment.op.lods": "LODs erzeugen",
    "garment.op.lods.desc": (
        "Die Detailstufen Mittel und Niedrig in den LOD-Slots von Sollumz erstellen, mit den Gewichten der Stufe Hoch"
    ),
    "garment.op.validate": "Validieren",
    "garment.op.validate.desc": "Das Kleidungsstück auf Probleme prüfen, die das Spiel zeigen würde",
    "garment.garment.facts": "{count} Vertices · Materialien: {materials}",
    "garment.body.hosted": "Freemode-Körper: {gender}, Version {version}",
    "garment.body.object": "Körper: {name}",
    "garment.body.downloading": "Lade den Freemode-Körper herunter…",
    "garment.body.subtext": (
        "Der Körper kommt von gta.clothing für dein angemeldetes Konto und wird im Ordner des Add-ons aufbewahrt, "
        "darum wird jede Version nur einmal heruntergeladen."
    ),
    "garment.body.cancelled": "Der Download des Körpers wurde abgebrochen.",
    "garment.body.offline": (
        "Der Online-Zugriff von Blender ist aus, und bisher wurde kein Körper heruntergeladen. Erlaube den "
        "Online-Zugriff oder nutze eine Körperdatei."
    ),
    "garment.body.network": (
        "gta.clothing war nicht erreichbar. Prüfe die Internetverbindung oder nutze eine Körperdatei."
    ),
    "garment.body.no-body": (
        "gta.clothing hat für diesen Kanal noch keinen Freemode-Körper. Nutze vorerst eine Körperdatei."
    ),
    "garment.body.signed-out": (
        "Die Anmeldung ist nicht mehr gültig. Melde dich erneut an und füge dann den Körper hinzu."
    ),
    "garment.body.not-entitled": "Dein Konto kann den Freemode-Körper nicht herunterladen.",
    "garment.body.refused": "gta.clothing hat den Download abgelehnt.",
    "garment.body.update": "gta.clothing braucht für den Körper eine neuere Version dieses Add-ons. Aktualisiere es.",
    "garment.body.busy": "Zu viele Downloads gleichzeitig. Warte kurz und versuche es erneut.",
    "garment.body.unavailable": "Der Freemode-Körper ist gerade nicht verfügbar. Versuche es später erneut.",
    "garment.body.invalid": "gta.clothing hat etwas gesendet, das kein Körper ist. Versuche es später erneut.",
    "garment.body.disk": "Der Körper konnte nicht im Ordner des Add-ons gespeichert werden.",
    "garment.markers.count": "Gesetzte Marker: {count} von {total}",
    "garment.presets.none": "Noch keine gespeicherten Voreinstellungen",
    "garment.backups.count": "Aufbewahrte Sicherungen: {count} von {limit}",
    "garment.problem.inside": "Im Körper",
    "garment.problem.close": "Zu nah am Körper",
    "garment.problem.stretched": "Gedehnt",
    "garment.problem.floating": "Abstehende Schulter",
    "garment.check.none": "Wähle Passform prüfen, um zu sehen, wie weit jeder Bereich vom Körper absteht.",
    "garment.check.measured": "Gemessen (mm)",
    "garment.check.value": "{p50} ({p10} bis {p90})",
    "garment.check.inside": "Im Körper: {count} Vertices ({share} %)",
    "garment.advice.shoulders": (
        "Die Schultern stehen vom Körper ab: An den Körper anlegen mit Schultern bringt sie herunter."
    ),
    "garment.sculpt.running": (
        "Ziehe mit dem Grab-Pinsel, um das Kleidungsstück zu bewegen. Der Körper wird als Drahtgittermodell gezeigt."
    ),
    "garment.sculpt.subtext": (
        "Übernehmen behält die Form; Abbrechen stellt die Form von vor der Sitzung wieder her."
    ),
    "garment.pose.arms-up": "Arme hoch",
    "garment.pose.arms-forward": "Arme nach vorn",
    "garment.pose.legs-forward": "Beine nach vorn",
    "garment.pose.twist": "Drehung",
    "garment.tears.pose": "{pose}: {count} Nahtpunkte offen, bis zu {gap} mm",
    "garment.tears.pose-clean": "{pose}: Keine Naht geht auf",
    "garment.validate.clean": "CLEAN: nichts zu beheben.",
    "garment.finding.non-finite": "{count} Punkte haben fehlerhafte Koordinaten.",
    "garment.finding.no-uv": "Das Kleidungsstück hat keine UV-Map, darum kann es keine Textur zeigen.",
    "garment.finding.uv-outside": (
        "{count} UV-Punkte liegen außerhalb des Quadrats von 0 bis 1; dort wiederholt das Spiel die Textur."
    ),
    "garment.finding.uv-area": "Das UV-Layout nutzt nur {area} % der Textur.",
    "garment.finding.no-weights": (
        "Noch nicht geriggt: Weise dem Kleidungsstück Gewichte für die Knochen des Freemode-Skeletts zu."
    ),
    "garment.finding.unweighted": (
        "{count} Vertices haben keine Gewichte; das Spiel lässt sie zurück, wenn sich das Ped bewegt."
    ),
    "garment.finding.influences": (
        "{count} Vertices werden von mehr als {limit} Knochen bewegt; das Spiel nutzt nur {limit}."
    ),
    "garment.finding.colour-missing": "Color 1 fehlt. Kleidungsstück vorbereiten fügt sie hinzu.",
    "garment.finding.colour-format": (
        "Color 1 ist keine Byte-Farbe auf Flächenecken (Face Corner), wie Sollumz sie braucht. Kleidungsstück "
        "vorbereiten ersetzt sie."
    ),
    "garment.finding.inside": "{share} % des Kleidungsstücks liegen im Körper.",
    "garment.finding.materials": (
        "Das Kleidungsstück hat {count} Materialien. Materialien zusammenfassen macht daraus eine Textur."
    ),
    "garment.why.no-garment": "Importiere zuerst ein Kleidungsstück oder wähle eines unter Einrichtung.",
    "garment.why.not-shown": "Das Kleidungsstück ist nicht in der aktuellen View Layer.",
    "garment.why.sculpting": "Beende zuerst die Sculpting-Sitzung mit Übernehmen oder Abbrechen.",
    "garment.why.step-running": "{step} läuft. Warte darauf, oder drücke Esc, um es abzubrechen.",
    "garment.why.object-mode": "Wechsle zuerst in den Objektmodus.",
    "garment.why.shape-keys": "Das Kleidungsstück hat Formschlüssel. Wende sie zuerst an oder entferne sie.",
    "garment.why.empty": "Das Kleidungsstück hat keine Geometrie.",
    "garment.why.no-body": "Füge zuerst unter Einrichtung den Freemode-Körper hinzu.",
    "garment.why.no-markers": "Schuhe brauchen keine Marker.",
    "garment.why.downloading": "Der Körper wird heruntergeladen.",
    "garment.why.sign-in": "Melde dich zuerst mit gta.clothing an (Verbinden) oder nutze eine Körperdatei.",
    "garment.why.select-mesh": "Wähle zuerst ein Mesh-Objekt aus.",
    "garment.why.is-body": "Das ist der Freemode-Körper, kein Kleidungsstück.",
    "garment.why.no-file": "Wähle eine Datei.",
    "garment.why.file-type": "Nur FBX-, OBJ-, GLB- und glTF-Dateien können importiert werden.",
    "garment.why.markers": "Setze zuerst die Marker unter Anpassen.",
    "garment.why.preset-name": "Gib der Voreinstellung einen Namen mit Buchstaben oder Ziffern.",
    "garment.why.preset-unreadable": "Die Voreinstellung konnte nicht gelesen werden: {detail}",
    "garment.why.tops-only": "Nur Oberteile haben Arme, die sich senken lassen.",
    "garment.why.no-backup": (
        "Es gibt noch keine Sicherung. Vor jedem Schritt, der das Kleidungsstück ändert, wird eine angelegt."
    ),
    "garment.why.region-category": "Dieser Bereich gehört nicht zur gewählten Kategorie.",
    "garment.why.region-empty": "Das Kleidungsstück hat nichts im Bereich {region}.",
    "garment.why.no-session": "Es läuft keine Sculpting-Sitzung.",
    "garment.why.no-armature": "Die Rissprüfung braucht eine Armature und Gewichte am Kleidungsstück.",
    "garment.why.no-weights": "Das Kleidungsstück hat keine Gewichte, mit denen es sich posieren lässt.",
    "garment.why.modifiers": (
        "Ein Modifikator ändert die Geometrie des Kleidungsstücks. Risse lassen sich nur ohne ihn prüfen."
    ),
    "garment.why.no-uv": "Das Kleidungsstück hat keine UV-Map.",
    "garment.why.empty-slot": "Jeder Materialsteckplatz des Kleidungsstücks braucht ein Material.",
    "garment.why.uv-full": "Das Kleidungsstück hat so viele UV-Maps, wie Blender erlaubt. Entferne zuerst eine.",
    "garment.why.no-sollumz": "LODs erzeugen braucht Sollumz.",
    "garment.why.show-high": "Zeige in Sollumz zuerst die Detailstufe Hoch.",
    "garment.why.no-download": "Es wird kein Körper heruntergeladen.",
    "garment.error.import": "Die Datei konnte nicht importiert werden: {detail}",
    "garment.error.no-mesh": "Die Datei enthält kein Mesh.",
    "garment.error.mode": "Der Skulpturmodus konnte nicht gestartet werden: {detail}",
    "garment.error.bake": "Das Backen ist fehlgeschlagen: {detail}",
    "garment.marker-error.no-markers": "Diese Kategorie braucht keine Marker.",
    "garment.marker-error.too-small": (
        "Das Kleidungsstück ist zu klein oder zu flach für Marker. Prüfe, ob es in Metern vorliegt."
    ),
    "garment.marker-error.not-a-top": (
        "Das Kleidungsstück sieht nicht wie ein Oberteil aus. Prüfe die Kategorie oder setze die Marker von Hand."
    ),
    "garment.marker-error.no-sleeves": "Keine Ärmel gefunden. Wähle Ärmellos oder setze die Armmarker von Hand.",
    "garment.marker-error.not-legs": (
        "Keine Hosenbeine gefunden. Prüfe die Kategorie oder setze die Marker von Hand."
    ),
    "garment.done.use": "Die Werkzeuge arbeiten jetzt an {name}.",
    "garment.done.import": "{name} importiert ({count} Vertices).",
    "garment.done.body": "Freemode-Körper hinzugefügt ({gender}, Version {version}).",
    "garment.done.body-file": "{name} als Körper hinzugefügt.",
    "garment.done.markers": "{count} Marker gesetzt. Verschiebe alle, die danebenliegen, vor dem Anpassen.",
    "garment.done.mirror": "Die linken Marker wurden nach rechts gespiegelt.",
    "garment.done.preset-saved": "Pose-Voreinstellung {name} gespeichert.",
    "garment.done.preset-loaded": "Pose-Voreinstellung {name} geladen.",
    "garment.done.tpose": "Die Arme wurden um {angle}° gesenkt. Eine Sicherung wurde angelegt.",
    "garment.done.tpose-none": "Die Arme stehen bereits im Armwinkel.",
    "garment.done.restore": "Die Form von vor dem ersten Anpassungsschritt wurde wiederhergestellt.",
    "garment.done.push": "{moved} Vertices verschoben. Im Körper: vorher {before}, jetzt {after}.",
    "garment.done.snug": (
        "{moved} Vertices von {region} näher an den Körper gebracht (durchschnittlich {mean} mm)."
    ),
    "garment.done.relax": "{moved} Vertices von {region} entspannt.",
    "garment.done.relax-smooth": (
        "{moved} Vertices von {region} geglättet (die Form von vor dem Anpassen ist zum Vergleich nicht vorhanden)."
    ),
    "garment.done.problems": (
        "Im Körper: {inside}, zu nah: {close}, gedehnt: {stretched}, abstehend: {floating}."
    ),
    "garment.done.check": "Passformprüfung fertig. Im Körper: {inside} Vertices.",
    "garment.done.sculpt-start": "Sculpting-Sitzung gestartet.",
    "garment.done.accept": (
        "Bearbeitete Form übernommen: {moved} Vertices verschoben. Im Körper: vorher {before}, jetzt {after}."
    ),
    "garment.done.cancel-sculpt": (
        "Sculpting abgebrochen: Das Kleidungsstück hat wieder seine Form von vor der Sitzung."
    ),
    "garment.done.tears": (
        "{count} Naht-Vertices gehen in einer Testpose auf. Sie sind in der Punktgruppe DCT Tears."
    ),
    "garment.done.no-tears": "In den Testposen geht keine Naht auf.",
    "garment.done.tears-welded": (
        "Die Nähte sind verbunden, hier kann also keine aufgehen. Prüfe das Kleidungsstück in Bewegung am Ped in der "
        "3D-Vorschau von Durty Cloth Tool."
    ),
    "garment.done.prepare": (
        "Vorbereitet: {welded} Naht-Vertices verbunden, {removed} lose Vertices entfernt, {triangles} Dreiecke."
    ),
    "garment.done.prepare-lining": (
        "Vorbereitet: {welded} Naht-Vertices verbunden (ein Futter wurde gefunden und getrennt gehalten), {removed} "
        "lose Vertices entfernt, {triangles} Dreiecke."
    ),
    "garment.done.combine": (
        "{count} Materialien zu einer Textur mit {size} Pixeln zusammengefasst, {density} Pixel pro Zentimeter am "
        "Kleidungsstück (das Layout nutzt {used} %, {cut} Streifen geschnitten)."
    ),
    "garment.done.lods": "Detailstufen: Hoch {high}, Mittel {medium}, Niedrig {low} Dreiecke.",
    "garment.done.clean": "Validieren: CLEAN.",
    "garment.done.findings": "Validieren hat Auffälligkeiten gefunden: {count}.",
    "garment.info.pose": (
        "Wähle die Pose des Avatars, auf dem das Kleidungsstück erstellt wurde. Ein in T-Pose erstelltes "
        "Kleidungsstück lässt sich unter Anpassen in die A-Pose des Spiels bringen."
    ),
    "garment.info.garment": (
        "Die Werkzeuge ändern nur dieses Objekt. Kleidungsstück importieren rechnet Zentimeter und Millimeter (wie "
        "Marvelous Designer sie exportiert) in Meter um. Jeder Schritt, der das Kleidungsstück ändert, legt eine "
        "Sicherung an, und Ctrl+Z macht ihn rückgängig."
    ),
    "garment.info.body": (
        "Der Freemode-Körper wird einmal pro Version von gta.clothing heruntergeladen und im Ordner des Add-ons "
        "aufbewahrt. Er wird als eigenes Objekt zur Szene hinzugefügt, und die Werkzeuge ändern ihn nie."
    ),
    "garment.info.markers": (
        "Die Marker stehen für die Gelenke des Peds: Hals, Brust, Becken, Schultern, Ellbogen, Handgelenke und Hüften "
        "(bei Hosen Hüften, Knie und Knöchel). Auto-Marker setzt sie anhand der Form des Kleidungsstücks, und Linien "
        "in der 3D-Ansicht verbinden sie: Orange Linien heißen, dass etwas nicht stimmt. Verschiebe alle Marker, die "
        "danebenliegen; Links nach rechts spiegeln kopiert die linke Seite auf die rechte."
    ),
    "garment.info.tpose": (
        "Dreht die Arme eines Kleidungsstücks aus der T-Pose auf den Armwinkel (oder auf die Arme des Körpers, wenn "
        "seine Gelenke bekannt sind). Jeder Teil des Kleidungsstücks folgt je nachdem, wo er liegt, deshalb bleiben "
        "Nähte geschlossen. An Körper ausrichten macht das auch."
    ),
    "garment.info.backups": (
        "Vor jedem Schritt, der das Kleidungsstück ändert, wird eine Kopie seines Meshes in der .blend-Datei "
        "aufbewahrt (die erste und die neuesten). Einen Schritt zurück setzt die neueste wieder ein, Ausgangsform "
        "wiederherstellen die erste. Sie verschwinden mit dem Kleidungsstück, wenn es gelöscht oder zu Durty Cloth "
        "Tool hinzugefügt wird."
    ),
    "garment.info.push": (
        "Bewegt alles, was im Körper oder näher als der Abstand liegt, auf den Abstand außerhalb des Körpers. Die "
        "umliegenden Vertices folgen, damit kein Knick entsteht, und Lagen darüber (eine Außenhülle über ihrem Futter) "
        "gehen mit. Teile, die mehr als 3 cm innen liegen, Vertices in der Vertexgruppe DCT Pinned und maskierte "
        "Vertices bleiben."
    ),
    "garment.info.regions": (
        "An den Körper anlegen zieht eine lockere Region zum Körper, bis auf den Abstand; frei hängende Mantelschöße, "
        "Röcke und Kapuzen bleiben, wie sie sind. Dehnung entspannen bringt gedehnte Teile wieder näher an ihre "
        "ursprüngliche Größe. Die Ränder der Region gehen weich über."
    ),
    "garment.info.problems": (
        "Färbt das Kleidungsstück, während du arbeitest: Rot im Körper, Gelb zu nah, Lila gedehnt im Vergleich zur "
        "ursprünglichen Form, Blau eine Schulter, die vom Körper absteht."
    ),
    "garment.info.check": (
        "Misst, wie weit jeder Bereich des Kleidungsstücks vom Körper absteht: den mittleren Wert und die Spanne der "
        "meisten seiner Vertices, in Millimetern. Negative Werte liegen im Körper."
    ),
    "garment.info.sculpt": (
        "Skulpturmodus mit dem Grab-Pinsel, der Körper als Drahtgittermodell. Übernehmen behält die Form (und bewegt, "
        "was in den Körper geraten ist, wieder hinaus, wenn Aus dem Körper halten an ist); Abbrechen stellt die "
        "vorherige Form wieder her."
    ),
    "garment.info.tears": (
        "Braucht eine Armature und Gewichte am Kleidungsstück. Das Kleidungsstück wird durch einige Testposen bewegt "
        "(Arme hoch, Arme nach vorn, Beine nach vorn, eine Drehung), und die Nähte, die aufgehen, werden gemeldet."
    ),
    "garment.info.prepare": (
        "Verbindet die Nähte zwischen den Teilen (nie einen Saum mit sich selbst und nie ein Futter mit seiner "
        "Außenhülle: Ein Futter, das nicht erkannt wird, gehört in die Vertexgruppe DCT Lining), entfernt lose Teile, "
        "trianguliert, schattiert weich und gibt dem Kleidungsstück die Vertexfarben Color 1 und Color 2 von Sollumz "
        "mit den Werten unter Optionen."
    ),
    "garment.info.combine": (
        "Packt alle UV-Inseln in ein Quadrat und backt jedes Material in eines: die Farbe mit ihrer Transparenz und "
        "eine Normal-, Specular- und Emissions-Map, wo ein Material eine hat. Das wird das einzige Material des "
        "Kleidungsstücks. Die ursprüngliche UV-Map bleibt als DCT Source UV erhalten."
    ),
    "garment.info.lods": (
        "Reduziert eine Kopie des Kleidungsstücks auf jedes Dreiecksbudget und legt sie in die LOD-Plätze Medium und "
        "Low von Sollumz; offene Kanten und UV-Nähte bleiben so weit wie möglich erhalten. Jede Stufe übernimmt die "
        "Gewichte von High (vier Knochen pro Vertex) und wird aus dem Körper geschoben."
    ),
    "garment.info.validate": (
        "Schnelle lokale Prüfungen: Gewichte, mehr als vier Knochen pro Vertex, kaputte Koordinaten, wo das "
        "Kleidungsstück sitzt, umgedrehte Normalen, das UV-Layout, Vertexfarben, die Dreiecke jeder Detailstufe und "
        "wie viel im Körper liegt."
    ),
    # ---- adding to Durty Cloth Tool ----
    "error.item-limit": (
        "Das Projekt hat so viele Kleidungsstücke, wie die kostenlose Version von Durty Cloth Tool erlaubt."
    ),
    "garment.next.done": (
        "Fertig: Das Kleidungsstück ist in deinem Durty Cloth Tool Projekt. Modell senden und Modell im "
        "Kleidungsstück speichern unter Modell aktualisieren es (in Durty Cloth Tool Ultimate enthalten)."
    ),
    "garment.next.validate-problems": (
        "Weiter: Behebe, was Validieren unter Spielfertig auflistet, und validiere dann erneut."
    ),
    "garment.next.adding": (
        "Wird hinzugefügt: Durty Cloth Tool zeigt das Kleidungsstück. Wähle dort Zum Projekt hinzufügen oder Abbrechen."
    ),
    "garment.next.connect": (
        "Weiter: Verbinde dich mit Durty Cloth Tool (Verbinden), um das Kleidungsstück einem Projekt hinzuzufügen."
    ),
    "garment.next.project": (
        "Weiter: Öffne ein Projekt in Durty Cloth Tool und füge das Kleidungsstück dann unter Spielfertig hinzu."
    ),
    "garment.next.sollumz": "Weiter: Installiere Sollumz, um das Kleidungsstück zu Durty Cloth Tool hinzuzufügen.",
    "garment.next.skeleton": (
        "Weiter: Durty Cloth Tool Skelett nutzen unter Spielfertig oder Zum Durty Cloth Tool Projekt hinzufügen, "
        "das es auch erledigt."
    ),
    "garment.next.add": "Weiter: Zum Durty Cloth Tool Projekt hinzufügen unter Spielfertig.",
    "add.heading": "Zu Durty Cloth Tool hinzufügen",
    "add.heading.variations": "Farbvarianten",
    "add.heading.skeleton": "Freemode-Skelett",
    "add.target": "Es wird als {slot}, {gender} hinzugefügt. Ändere beides unter Einrichtung.",
    "add.variation.none": "Noch keine Farbtextur",
    "add.variations.subtext": "Varianten: {count} von höchstens {limit}.",
    "add.prop.name": "Name des Kleidungsstücks",
    "add.prop.name.desc": (
        "Der Name, den das Kleidungsstück in Durty Cloth Tool bekommt. Leer: sein Name in Blender"
    ),
    "add.prop.skin": "Haut sichtbar",
    "add.prop.skin.desc": (
        "Das Kleidungsstück zeigt etwas von der Haut des Peds, darum färbt das Spiel es im Hautton des Peds "
        "(die Variante _r)"
    ),
    "add.prop.image": "Bild der Variante",
    "add.prop.image.desc": "Die Farbtextur dieser Variante, im Layout der eigenen Textur des Kleidungsstücks",
    "add.prop.variation-name": "Name der Variante",
    "add.prop.variation-name.desc": "Der Name dieser Farbvariante in Durty Cloth Tool. Leer: der Name des Bildes",
    "add.prop.first-name.desc": (
        "Der Name der ersten Farbvariante (der eigenen Textur des Kleidungsstücks) in Durty Cloth Tool. Leer: der "
        "Name des Bildes"
    ),
    "add.op.skeleton": "Durty Cloth Tool Skelett nutzen",
    "add.op.skeleton.desc": (
        "Das Freemode-Skelett des Geschlechts unter Einrichtung aus Durty Cloth Tool holen und das Kleidungsstück "
        "daran binden, bereit für Sollumz"
    ),
    "add.op.add": "Zum Durty Cloth Tool Projekt hinzufügen",
    "add.op.add.desc": (
        "Das Kleidungsstück prüfen, mit Sollumz exportieren und dem in Durty Cloth Tool geöffneten Projekt als "
        "neues Kleidungsstück hinzufügen. Durty Cloth Tool fragt dich vorher"
    ),
    "add.op.cancel.desc": (
        "Das Hinzufügen abbrechen. Solange Durty Cloth Tool noch fragt, wird nichts hinzugefügt"
    ),
    "add.op.add-variation": "Farbvariante hinzufügen",
    "add.op.add-variation.desc": "Ein weiteres Bild als Farbvariante des Kleidungsstücks hinzufügen",
    "add.op.remove-variation": "Entfernen",
    "add.op.remove-variation.desc": "Diese Farbvariante entfernen",
    "add.info": (
        "Fügt das Kleidungsstück dem in Durty Cloth Tool geöffneten Projekt als neues Kleidungsstück hinzu. Durty "
        "Cloth Tool zeigt es zuerst, und nichts wird hinzugefügt, solange du dort nicht Zum Projekt hinzufügen wählst. "
        "Braucht Durty Cloth Tool mit einem geöffneten Projekt und dort eingerichtetem Spiel sowie Sollumz."
    ),
    "add.info.variations": (
        "Die eigene Textur des Kleidungsstücks ist die erste Farbvariante. Füge weitere mit anderen Bildern im "
        "selben Layout hinzu; jedes wird eine Farbvariante des Kleidungsstücks, mit dem Namen, den du ihm gibst."
    ),
    "add.info.skeleton": (
        "Durty Cloth Tool sendet das Freemode-Skelett des Geschlechts unter Einrichtung, erstellt aus deinen "
        "Spieldateien. Sollumz importiert es als Armature, und das Kleidungsstück wird ihm mit einem "
        "Armature-Modifikator untergeordnet; seine Punktgruppen behalten ihre Knochennamen. Hinzufügen erledigt "
        "das für dich, wenn es nötig ist."
    ),
    "add.skeleton.ready": "Am Durty Cloth Tool Skelett ({gender}, {count} Knochen): {name}",
    "add.skeleton.missing": (
        "Das Kleidungsstück ist noch nicht am Durty Cloth Tool Skelett. Wähle Durty Cloth Tool Skelett nutzen oder "
        "Hinzufügen, das es für dich erledigt."
    ),
    "add.skeleton.other-gender": (
        "Das Kleidungsstück ist am Skelett ({gender}). Wähle Durty Cloth Tool Skelett nutzen, um es an das Skelett "
        "des Geschlechts unter Einrichtung umzuhängen."
    ),
    "add.skeleton.modifier": (
        "Der Armature-Modifikator des Kleidungsstücks nutzt nicht sein Durty Cloth Tool Skelett. Wähle erneut "
        "Durty Cloth Tool Skelett nutzen."
    ),
    "add.skeleton.order": (
        "Die Knochen des Skeletts sind nicht in der Reihenfolge des Spiels, darum würden die Gewichte die falschen "
        "Knochen bewegen. Wähle erneut Durty Cloth Tool Skelett nutzen, statt seine Knochen zu ändern."
    ),
    "add.skeleton.bones": (
        "Das Skelett hat {count} Knochen, das Freemode-Skelett aber {expected}. Wähle erneut Durty Cloth Tool "
        "Skelett nutzen, statt seine Knochen zu ändern."
    ),
    "add.skeleton.import": (
        "Sollumz hat das Skelett nicht als eine Armature importiert. Sein Info-Log zeigt die Details."
    ),
    "add.skeleton.invalid": (
        "Durty Cloth Tool hat ein Skelett gesendet, das das Add-on nicht lesen kann. Aktualisiere beide und "
        "versuche es dann erneut."
    ),
    "add.skeleton.game-required": (
        "Durty Cloth Tool braucht für das Freemode-Skelett deine GTA V Installation. "
        "Richte das Spiel in Durty Cloth Tool ein und versuche es dann erneut."
    ),
    "add.skeleton.busy": "Durty Cloth Tool liest noch die Spieldateien. Versuche es gleich noch einmal.",
    "add.dct-too-old": (
        "Dieses Durty Cloth Tool kann noch keine Kleidung aus Blender hinzufügen. Aktualisiere Durty Cloth Tool."
    ),
    "add.done.skeleton": "Das Kleidungsstück ist am Durty Cloth Tool Skelett ({gender}, {count} Knochen): {name}.",
    "add.fetching": "Hole das Freemode-Skelett ({gender}) aus Durty Cloth Tool…",
    "add.progress.skeleton": "Hole das Freemode-Skelett aus Durty Cloth Tool…",
    "add.sent": "{name} mit {count} Farbvarianten gesendet. Wähle Zum Projekt hinzufügen in Durty Cloth Tool.",
    "add.waiting": "Durty Cloth Tool zeigt das Kleidungsstück. Wähle dort Zum Projekt hinzufügen oder Abbrechen.",
    "add.waiting.subtext": (
        "Nichts wird hinzugefügt, bis du in Durty Cloth Tool Zum Projekt hinzufügen wählst. Abbrechen hier zieht das "
        "Hinzufügen zurück."
    ),
    "add.withdrawing": "Breche das Hinzufügen ab…",
    "add.blocked": "Das Hinzufügen ist blockiert: Behebe zuerst {count} Probleme, aufgelistet unter Spielfertig.",
    "add.problems": "Behebe zuerst diese ({count}):",
    "add.findings": "Prüfungen von Durty Cloth Tool: {count}",
    "add.added.subtext": (
        "Das Drawable Dictionary ist mit dem neuen Kleidungsstück verknüpft: Modell senden und Modell im "
        "Kleidungsstück speichern unter Modell aktualisieren es (in Durty Cloth Tool Ultimate enthalten)."
    ),
    "add.invalid": "Das Hinzufügen kann nicht gesendet werden: {detail}",
    "add.why.connect": "Verbinde dich mit Durty Cloth Tool, um das Kleidungsstück einem Projekt hinzuzufügen.",
    "add.why.no-project": "Öffne ein Projekt in Durty Cloth Tool, um das Kleidungsstück dort hinzuzufügen.",
    "add.why.adding": "Ein Hinzufügen wartet auf Durty Cloth Tool.",
    "add.why.fetching": "Warte auf das Freemode-Skelett aus Durty Cloth Tool.",
    "add.why.nothing-running": "Es läuft nichts.",
    "add.why.no-template": "Durty Cloth Tool hat kein Freemode-Skelett gesendet. Versuche es erneut.",
    "add.why.garment-changed": (
        "Inzwischen wurde ein anderes Kleidungsstück gewählt, darum lief der Schritt nicht. Führe ihn erneut aus."
    ),
    "add.why.no-weights": (
        "Das Kleidungsstück hat noch keine Gewichte für das Freemode-Skelett. Weise ihm Gewichte für die Knochen "
        "des Skeletts zu (Punktgruppen, die nach ihnen benannt sind, etwa SKEL_Spine3)."
    ),
    "add.why.unknown-groups": (
        "{count} Punktgruppen sind keine Knochen des Freemode-Skeletts: {names}. Benenne sie um oder entferne sie; "
        "das Spiel würde sie mit dem Root-Knochen bewegen."
    ),
    "add.why.name-empty": "Gib dem Kleidungsstück einen Namen.",
    "add.why.name-invalid": (
        "Der Name des Kleidungsstücks darf höchstens {limit} Zeichen und keine Steuerzeichen enthalten."
    ),
    "add.why.combine": (
        "Das Kleidungsstück hat {count} Materialien. Wähle zuerst Materialien zusammenfassen: Jede Farbvariante ist "
        "eine Textur."
    ),
    "add.why.no-diffuse": (
        "Das Material des Kleidungsstücks hat keine Farbtextur. Materialien zusammenfassen erstellt eine."
    ),
    "add.why.variation-empty": "Farbvariante {number} hat kein Bild. Wähle eines oder entferne die Zeile.",
    "add.why.too-many": "Ein Kleidungsstück hat höchstens {limit} Farbvarianten.",
    "add.why.variation-twice": "Das Bild {name} wird für zwei Farbvarianten genutzt. Jede braucht ein eigenes.",
    "add.why.too-large": (
        "Modell und Bilder sind zusammen größer als {size} MiB und können nicht gesendet werden. Nutze kleinere "
        "Bilder oder weniger Farbvarianten."
    ),
    "add.why.work-folder": (
        "Der Ordner des Add-ons für den Export ist ein Link an einen anderen Ort, darum wird er nicht genutzt."
    ),
    "add.why.convert": "Sollumz konnte aus dem Kleidungsstück kein Drawable Model machen ({detail}).",
    "add.why.material": "Sollumz konnte dem Kleidungsstück nicht den Ped-Shader geben ({detail}).",
    "add.picture.empty": "Das Bild {name} hat keine Pixel.",
    "add.picture.too-large": (
        "Das Bild {name} ist auf einer Seite größer als {size} Pixel; das nimmt Durty Cloth Tool nicht an."
    ),
    "add.picture.not-multiple-of-four": (
        "Das Bild {name} ist {width} x {height}: Durty Cloth Tool braucht Seiten, die durch vier teilbar sind."
    ),
    "add.picture.non-power-of-two": (
        "Das Bild {name} ist {width} x {height}, keine Zweierpotenz (zum Beispiel 1024 oder 2048)."
    ),
    "add.picture.large": (
        "Das Bild {name} ist auf einer Seite größer als {size} Pixel und braucht viel Spielspeicher."
    ),
    "add.picture.small": "Das Bild {name} ist auf einer Seite kleiner als {size} Pixel.",
    "add.picture.unusable": "Das Bild {name} kann nicht gesendet werden: {problem}",
    "add.export.empty": (
        "Sollumz hat das Drawable Dictionary ohne die Geometrie des Kleidungsstücks exportiert. Sein Info-Log zeigt "
        "die Details."
    ),
    "add.export.several": (
        "Sollumz hat {count} Drawables exportiert; Durty Cloth Tool nimmt eines pro Kleidungsstück."
    ),
    "add.export.skeleton": "Der Export enthält noch das Skelett. Aktualisiere Sollumz und versuche es dann erneut.",
    "add.export.errors": (
        "Sollumz hat beim Exportieren Fehler gemeldet, darum fehlt vielleicht ein Teil des Kleidungsstücks. Sein "
        "Info-Log zeigt die Details."
    ),
    "add.export.unreadable": "Der Export konnte nicht gelesen werden ({detail}).",
    "add.export.warnings": "Sollumz hat beim Exportieren Warnungen gemeldet; sein Info-Log zeigt die Details.",
    "add.result.added": "{name} wurde dem Projekt als {slot} hinzugefügt.",
    "add.result.added-unlinked": (
        "{name} wurde dem Projekt hinzugefügt, aber das Modell in Blender konnte nicht damit verknüpft werden "
        "({detail})."
    ),
    "add.result.denied": (
        "Durty Cloth Tool hat das Kleidungsstück nicht hinzugefügt: Dort wurde Abbrechen gewählt. Das Projekt ist "
        "unverändert."
    ),
    "add.result.withdrawn": "Das Hinzufügen wurde abgebrochen. Das Projekt ist unverändert.",
    "add.result.cancel-unanswered": (
        "Das Hinzufügen wurde abgebrochen, aber Durty Cloth Tool hat es nicht bestätigt. Prüfe das Projekt in "
        "Durty Cloth Tool."
    ),
    "add.result.timeout": (
        "Durty Cloth Tool hat auf das Hinzufügen nicht rechtzeitig geantwortet. "
        "Prüfe das Projekt in Durty Cloth Tool."
    ),
    "add.result.disconnected": (
        "Die Verbindung zu Durty Cloth Tool wurde während des Hinzufügens unterbrochen. Prüfe das Projekt in "
        "Durty Cloth Tool, bevor du das Kleidungsstück erneut hinzufügst."
    ),
    "add.result.item-limit": (
        "Durty Cloth Tool hat das Kleidungsstück nicht hinzugefügt: Das Projekt hat schon so viele Kleidungsstücke, "
        "wie dein Plan in Durty Cloth Tool erlaubt, oder das Kleidungsstück hat mehr Farbvarianten, als der Plan für "
        "ein Kleidungsstück erlaubt. Diese Grenzen legt Durty Cloth Tool fest und prüft sie, nicht das Add-on."
    ),
    "add.result.rejected": (
        "Durty Cloth Tool konnte das Modell oder eine Farbvariante nicht verwenden, darum wurde nichts hinzugefügt. "
        "Seine Prüfungen unten zeigen, warum."
    ),
    "add.result.no-project": (
        "Öffne zuerst ein Projekt in Durty Cloth Tool und füge das Kleidungsstück dann erneut hinzu."
    ),
    "add.result.item-refused": (
        "Dieses Projekt nimmt auf diesem Weg keine Freemode-Kleidung an (zum Beispiel ein Projekt für ein "
        "benutzerdefiniertes Ped). Öffne ein Freemode-Projekt in Durty Cloth Tool."
    ),
    "add.result.busy": (
        "Durty Cloth Tool ist beschäftigt (ein Build läuft oder ein anderes Hinzufügen wartet auf eine Antwort). "
        "Versuche es gleich noch einmal."
    ),
    "add.result.rate-limited": (
        "Zu viele Anfragen zum Hinzufügen in kurzer Zeit. Warte ein paar Sekunden und versuche es dann erneut."
    ),
    "add.result.save-failed": (
        "Durty Cloth Tool konnte das Kleidungsstück nicht hinzufügen. Seine Statusleiste zeigt die Details."
    ),
    "add.finding.rig-invalid": (
        "Die Gewichte oder Knochenindizes passen nicht zum Freemode-Skelett: Das Kleidungsstück würde sich im Spiel "
        "falsch bewegen."
    ),
    "add.finding.rig-unchecked": "Durty Cloth Tool konnte die Gewichte nicht lesen, um sie zu prüfen.",
    "add.finding.single-bone-rig": (
        "Ein Knochen trägt fast das ganze Gewicht einer Detailstufe, darum würde sich das Kleidungsstück kaum mit "
        "dem Körper bewegen."
    ),
    "add.finding.hair-tint-unsupported": (
        "Diese Haare können die Haarfarbe, die der Spieler wählt, nicht annehmen."
    ),
    "add.finding.picture.non-power-of-two": (
        "Die Größe einer Farbvariante ist keine Zweierpotenz (zum Beispiel 1024 oder 2048)."
    ),
    "add.finding.picture.not-multiple-of-four": "Die Größe einer Farbvariante ist nicht durch vier teilbar.",
    "add.finding.picture.too-large": (
        "Eine Farbvariante ist größer, als Durty Cloth Tool rät (2048 Pixel pro Seite; es nimmt höchstens 4096 an)."
    ),
    "add.finding.picture.too-small": "Eine Farbvariante ist auf einer Seite kleiner als 16 Pixel.",
    "garment.next.align": (
        "Weiter: An Körper ausrichten unter Anpassen, damit das Kleidungsstück auf dem Freemode-Körper sitzt."
    ),
    "garment.next.weights": (
        "Weiter: Gewichte übertragen unter Spielfertig, oder gewichte das Kleidungsstück selbst auf die Knochen des "
        "Freemode-Skeletts. Erzeuge danach die LODs, die die Gewichte übernehmen."
    ),
    "garment.region.forearms": "Unterarme",
    "garment.region.cuffs": "Bündchen",
    "garment.unit.auto": "Automatisch",
    "garment.unit.m": "Meter",
    "garment.unit.cm": "Zentimeter",
    "garment.unit.mm": "Millimeter",
    "garment.unit.in": "Zoll",
    "garment.unit.desc": "Die Einheit, in der die Datei gespeichert wurde",
    "garment.prop.unit": "Einheit",
    "garment.prop.unit.desc": (
        "Die Einheit, in der die Datei gespeichert wurde. Automatisch wählt die Einheit, mit der das Kleidungsstück "
        "eine glaubhafte Größe hat"
    ),
    "garment.prop.orient": "Aufrichten",
    "garment.prop.orient.desc": (
        "Ein Kleidungsstück, das auf dem Rücken liegt oder nach hinten schaut, so drehen, dass es wie der Ped steht"
    ),
    "garment.prop.keep-size": "Größe behalten",
    "garment.prop.keep-size.desc": (
        "An Körper ausrichten verschiebt und dreht das Kleidungsstück nur, ohne es an den Körper anzupassen"
    ),
    "garment.heading.align": "An Körper ausrichten",
    "garment.heading.options": "Optionen",
    "garment.op.align": "An Körper ausrichten",
    "garment.op.align.desc": (
        "Verschiebt und dreht das Kleidungsstück (und skaliert es, wenn Größe behalten aus ist), sodass seine Marker "
        "auf den Gelenken des Körpers sitzen, und dreht dann seine Arme oder Beine auf die des Körpers"
    ),
    "garment.op.back": "Einen Schritt zurück",
    "garment.op.back.desc": (
        "Die Form des Kleidungsstücks von vor dem letzten Schritt, der es geändert hat, zurückholen"
    ),
    "garment.op.remove-backups": "Sicherungen entfernen",
    "garment.op.remove-backups.desc": "Die Sicherungen des Kleidungsstücks aus der .blend-Datei entfernen",
    "garment.align.source.hosted": "Gelenke: vom Freemode-Körper.",
    "garment.align.source.dct": "Gelenke: aus deinen Spieldateien, über Durty Cloth Tool.",
    "garment.align.source.estimate": (
        "Gelenke: aus der Form des Körpers geschätzt. Mit verbundenem Durty Cloth Tool nutzt An Körper ausrichten die "
        "genauen Gelenke."
    ),
    "garment.align.fetching": "Hole die Gelenke des Freemode-Skeletts aus Durty Cloth Tool…",
    "garment.info.align": (
        "Verschiebt und dreht das Kleidungsstück, sodass seine Marker auf den Gelenken des Freemode-Körpers sitzen, "
        "und dreht dann jeden Arm (oder jedes Bein) auf den des Körpers. Ist Größe behalten aus, skaliert es das "
        "Kleidungsstück auch auf den Körper. Die Werkzeuge unter Korrigieren messen am Körper, darum warten sie auf "
        "diesen Schritt, und erneut, wenn seitdem ein Marker verschoben wurde. Führe zuerst Auto-Marker aus und "
        "verschiebe jeden Marker, der danebenliegt."
    ),
    "garment.done.align": (
        "Am Körper ausgerichtet: um {shift} cm verschoben, um {turn}° gedreht, auf {scale} % skaliert, {limbs} Arme "
        "oder Beine gedreht. Die Marker liegen im Schnitt {residual} mm neben den Gelenken."
    ),
    "garment.why.align-first": "Richte das Kleidungsstück zuerst unter Anpassen am Körper aus.",
    "garment.why.region-snug": (
        "An den Körper anlegen lässt Mantelschöße und Röcke in Ruhe: Sie hängen frei von den Beinen."
    ),
    "garment.why.ped-material": (
        "Das Kleidungsstück hat schon den Ped-Shader, sein Material ist also bereit fürs Spiel. Materialien "
        "zusammenfassen würde es ersetzen."
    ),
    "garment.marker-error.align-markers": (
        "Die Marker passen nicht auf die Gelenke des Körpers, ohne das Kleidungsstück stark zu skalieren oder zu "
        "drehen. Prüfe sie (die Linien zwischen ihnen zeigen, wo sie sitzen) und richte dann erneut aus."
    ),
    "garment.marker-note.arms-estimated": (
        "Es wurden keine Ärmel gefunden, die Arme folgen also der Ausgangspose. Prüfe Ellbogen und Handgelenke."
    ),
    "garment.marker-note.hood": "Eine Kapuze wurde gefunden: Der Halsmarker sitzt darunter.",
    "garment.marker-note.skirt": (
        "Es wurden keine Beine gefunden, die Hüften sind also nach üblichen Proportionen gesetzt (ein Rock?)."
    ),
    "garment.marker-note.legs-estimated": (
        "Die Beine enden früh, Knie und Knöchel sind also nach üblichen Proportionen gesetzt."
    ),
    "garment.marker-problem.order": (
        "Die Marker liegen nicht in der Reihenfolge von oben nach unten. Prüfe Hals, Brust und Becken."
    ),
    "garment.marker-problem.span": (
        "Die Schultern liegen zu nah beieinander oder zu weit auseinander. Prüfe die Schultermarker."
    ),
    "garment.marker-problem.symmetry": (
        "Die linken und rechten Marker spiegeln einander nicht. Links nach rechts spiegeln gleicht sie an."
    ),
    "garment.marker-problem.arms": (
        "Die Marker eines Arms sind zu kurz, zu lang oder zurückgebogen. Prüfe Ellbogen und Handgelenke."
    ),
    "garment.marker-problem.legs": "Die Marker eines Beins sind zu kurz oder zu lang. Prüfe Knie und Knöchel.",
    "garment.done.import-turned": "{name} importiert ({count} Vertices) und so gedreht, dass es wie der Ped steht.",
    "garment.done.import-avatar": "{name} importiert ({count} Vertices), ohne den Avatar, der mitgekommen ist.",
    "garment.done.back": "Die Form von vor dem letzten Schritt ist zurück.",
    "garment.done.remove-backups": "{count} Sicherungen entfernt.",
    "garment.done.push-deep": (
        "{moved} Vertices verschoben. Im Körper: vorher {before}, jetzt {after}. {deep} liegen zu tief, um sie zu "
        "verschieben (ein Ärmel durch den Körper?): korrigiere sie von Hand."
    ),
    "garment.done.prepare-thick": (
        "Dicken Export vorbereitet: {welded} Vertices über Teile hinweg verbunden, {walls} Innenwände entfernt, "
        "{triangles} Dreiecke."
    ),
    "garment.done.cancel-sculpt-lost": (
        "Die Sculpt-Sitzung ist beendet, aber ihre Ausgangsform ging verloren. Strg+Z hat sie noch."
    ),
    "garment.done.sculpt-mirror-off": (
        "Sculpt-Sitzung gestartet. X spiegeln spiegelt um die eigene Mitte des Kleidungsstücks, nicht um die des Peds: "
        "Wende zuerst seine Transformation an, um um den Ped zu spiegeln."
    ),
    "garment.sculpt.broken": (
        "Die Sculpt-Sitzung hat ihre Ausgangsform verloren (das passiert durch Dyntopo oder ein Remesh). Übernehmen "
        "behält die Form und beendet die Sitzung."
    ),
    "garment.tears.pose-skipped": "{pose}: übersprungen, die Armature hat keinen Knochen dafür",
    "garment.error.cycles": (
        "Materialien zusammenfassen backt mit Cycles. Schalte Cycles unter Bearbeiten > Einstellungen > Add-ons ein "
        "und versuche es erneut."
    ),
    "garment.body.compressed": (
        "Dieses Blender kann den komprimierten Freemode-Körper nicht lesen. Nutze Blender 5.2 oder neuer oder eine "
        "Körperdatei, bis gta.clothing den unkomprimierten Körper anbietet."
    ),
    "garment.finding.triangles": (
        "Die Stufe {level} hat {count} Dreiecke, mehr als die {budget}, die Durty Cloth Tool empfiehlt."
    ),
    "garment.finding.placement": (
        "Die Mitte des Kleidungsstücks liegt {distance} cm vom Körper entfernt, es sitzt also nicht am Körper. Prüfe "
        "den Import (Einheit, Avatar auf dem Boden) und An Körper ausrichten."
    ),
    "garment.finding.normals-inward": (
        "{share} % der Fläche nahe am Körper zeigen in ihn hinein: Die Normalen wirken umgedreht. Berechne sie im "
        "Bearbeitungsmodus nach außen neu (Netz > Normalen)."
    ),
    "add.result.added-late": (
        "Durty Cloth Tool hat {name} doch hinzugefügt: Dort wurde Zum Projekt hinzufügen gewählt, bevor der Abbruch "
        "ankam. Es ist jetzt hier verknüpft."
    ),
    "add.warning.normal-not-embedded": (
        "Die Normal-Map {name} ist keine DDS-Datei und wird deshalb nicht mit dem Modell gesendet. Füge sie nach dem "
        "Hinzufügen in Durty Cloth Tool hinzu."
    ),
    "add.warning.specular-not-embedded": (
        "Die Specular-Map {name} ist keine DDS-Datei und wird deshalb nicht mit dem Modell gesendet. Füge sie nach dem "
        "Hinzufügen in Durty Cloth Tool hinzu."
    ),
    "add.why.no-ped-shader": (
        "Sollumz hat keinen Ped-Shader (ped.sps), das Kleidungsstück kann das Kleidungsmaterial also nicht bekommen. "
        "Aktualisiere oder installiere Sollumz neu."
    ),
    "add.progress.prepare": "Setze das Kleidungsstück auf das Skelett und richte sein Material ein…",
    "add.progress.export": "Exportiere das Kleidungsstück mit Sollumz…",
    "add.progress.pictures": "Schreibe die Farbvarianten ({done} von {total})…",
    "add.cancelled-local": (
        "Das Hinzufügen wurde abgebrochen, bevor etwas gesendet wurde. Strg+Z macht rückgängig, was es am "
        "Kleidungsstück geändert hat."
    ),
    "add.failed-undo": "{problem} Strg+Z setzt das Kleidungsstück auf den Stand vor dem Hinzufügen zurück.",
    # ---- garment fitting on gta.clothing ------------------------------------------------------------------
    "garment.heading.service": "Anpassen mit gta.clothing",
    "garment.heading.weights": "Gewichte",
    "garment.op.service-fit": "An Körper anpassen",
    "garment.op.service-fit.desc": (
        "Schickt das Kleidungsstück an gta.clothing, das es in die Spielpose bringt, ihm die Gewichte des "
        "Freemode-Körpers gibt und es aus dem Körper bewegt. Verbraucht eine deiner Anpassungen für heute"
    ),
    "garment.op.service-weights": "Gewichte übertragen",
    "garment.op.service-weights.desc": (
        "Schickt das Kleidungsstück an gta.clothing, das ihm die Gewichte des Freemode-Körpers gibt, ohne es zu "
        "bewegen. Verbraucht eine deiner Anpassungen für heute"
    ),
    "garment.op.service-cancel.desc": (
        "Bricht die Anpassung ab. Eine Anpassung, die gta.clothing noch nicht begonnen hat, zählt nicht für heute; "
        "eine begonnene zählt trotzdem"
    ),
    "garment.info.service": (
        "An Körper anpassen schickt das Kleidungsstück so, wie es nach An Körper ausrichten sitzt, an gta.clothing. Es "
        "kommt in der Spielpose zurück, mit den Gewichten des Freemode-Körpers und dort aus dem Körper bewegt, wo es "
        "darin lag. Das Kleidungsstück behält eine Sicherung, also stellt Einen Schritt zurück es wieder her. Jede "
        "Anpassung verbraucht eine deiner Anpassungen für heute."
    ),
    "garment.info.weights": (
        "Gewichte übertragen gibt dem Kleidungsstück die Gewichte des Freemode-Körpers als Vertexgruppen mit den Namen "
        "der Knochen, ohne es zu bewegen. Nutze es, nachdem sich die Form geändert hat, zum Beispiel nach dem "
        "Sculpting oder Kleidungsstück vorbereiten. Es verbraucht eine deiner Anpassungen für heute; du kannst das "
        "Kleidungsstück auch selbst gewichten."
    ),
    "garment.prop.clearance": "Abstand (mm)",
    "garment.prop.clearance.desc": "Wie weit das Kleidungsstück außerhalb des Körpers bleibt, wo es herausbewegt wird",
    "garment.prop.service-push": "Aus dem Körper bewegen",
    "garment.prop.service-push.desc": (
        "Bewegt jeden Teil des Kleidungsstücks, der im Körper oder zu nah an ihm liegt, auf den Abstand heraus"
    ),
    "garment.prop.max-push": "Tiefste Bewegung (mm)",
    "garment.prop.max-push.desc": "Teile, die tiefer im Körper liegen, bleiben, wo sie sind",
    "garment.prop.seam-gap": "Nahtabstand (mm)",
    "garment.prop.seam-gap.desc": (
        "Schnittkanten, die näher beieinander liegen, zählen als eine Naht, damit beide Seiten dieselben Gewichte "
        "bekommen. 0 schaltet das aus"
    ),
    "garment.prop.proportions": "Proportionen angleichen",
    "garment.prop.proportions.desc": (
        "Streckt auch Arme und Beine des Körpers zu den Markern des Kleidungsstücks, für ein Kleidungsstück, das auf "
        "einem anderen Avatar entstand"
    ),
    "fit.left": "Anpassungen heute übrig: {left} von {total}",
    "fit.stage.uploading": "Kleidungsstück wird gesendet ({percent} %)",
    "fit.stage.busy": "gta.clothing ist beschäftigt. Gleich wird es erneut versucht",
    "fit.stage.queued": "Warten auf gta.clothing",
    "fit.stage.validating": "Kleidungsstück wird geprüft",
    "fit.stage.welding": "Nähte werden verbunden",
    "fit.stage.posing": "Pose wird angeglichen",
    "fit.stage.transferring": "Gewichte des Körpers werden übernommen",
    "fit.stage.unposing": "Es wird in die Spielpose gebracht",
    "fit.stage.pushingout": "Es wird aus dem Körper bewegt",
    "fit.stage.weighting": "Gewichte werden fertiggestellt",
    "fit.stage.running": "Anpassen",
    "fit.stage.cancelling": "Wird abgebrochen",
    "fit.stage.cancelling-counted": "Wird abgebrochen. Die Anpassung hat begonnen und zählt daher trotzdem",
    "fit.consent.title": "Zum Anpassen hochladen",
    "fit.consent.what": (
        "An Körper anpassen und Gewichte übertragen schicken das Kleidungsstück an gta.clothing: seine Form "
        "(Vertex-Positionen und Dreiecke), welche Vertices in DCT Pinned, maskiert oder in DCT Lining sind, seine "
        "Marker, die Anpassungsoptionen sowie Geschlecht, Slot und Kategorie. Keine Texturen, Materialien, Namen oder "
        "Dateien."
    ),
    "fit.consent.kept": (
        "gta.clothing passt es an und schickt es zurück. Das Kleidungsstück wird nicht aufbewahrt: Das Ergebnis wird "
        "spätestens nach zehn Minuten gelöscht. gta.clothing protokolliert zu jeder Anpassung eine Zusammenfassung "
        "ohne die Form des Kleidungsstücks: Zahlen wie Vertices und Dreiecke, das Ergebnis und wie lange es gedauert "
        "hat."
    ),
    "fit.consent.revoke": (
        "Du stimmst einmal zu. Zum Widerrufen schalte Kleidung zum Anpassen hochladen unter Einstellungen > "
        "Datenschutz aus."
    ),
    "fit.consent.confirm": "Hochladen und anpassen",
    "prop.fit-consent": "Kleidung zum Anpassen hochladen",
    "prop.fit-consent.desc": (
        "An Körper anpassen und Gewichte übertragen dürfen die Form des Kleidungsstücks an gta.clothing schicken. "
        "Schalte es aus, um zu widerrufen; das Add-on fragt dann vor dem nächsten Senden erneut"
    ),
    "settings.fit-consent-subtext": (
        "Form, Marker und Anpassungsoptionen des Kleidungsstücks gehen nur an gta.clothing, wenn du An Körper anpassen "
        "oder Gewichte übertragen wählst. Das Kleidungsstück wird dort nicht aufbewahrt; nur eine Zusammenfassung ohne "
        "seine Form wird protokolliert."
    ),
    "fit.why.running": "Eine Anpassung läuft. Warte auf sie oder brich sie ab.",
    "fit.why.hosted-body": (
        "Anpassen braucht den Freemode-Körper von gta.clothing: Freemode-Körper hinzufügen unter Einrichtung."
    ),
    "fit.why.sign-in": "Melde dich zuerst mit gta.clothing an (Verbinden).",
    "fit.why.no-fits": "Heute können keine weiteren Anpassungen gestartet werden. Neue gibt es {wait}.",
    "fit.error.update": (
        "gta.clothing konnte nicht lesen, was das Add-on gesendet hat. Aktualisiere das Add-on und versuche es erneut."
    ),
    "fit.error.plugin-update": (
        "Aktualisiere das Add-on, um Kleidung anzupassen: Bearbeiten > Einstellungen > Erweiterungen holen > Nach "
        "Updates suchen."
    ),
    "fit.error.signed-out": (
        "Deine Anmeldung bei gta.clothing ist abgelaufen. Melde dich unter Verbinden erneut an und versuche es dann "
        "noch einmal."
    ),
    "fit.error.locked": "Dieses gta.clothing-Konto ist gesperrt und kann keine Kleidung anpassen.",
    "fit.error.not-entitled": (
        "Dein gta.clothing-Konto kann keine Kleidung anpassen. Prüfe dein Konto auf gta.clothing."
    ),
    "fit.error.switched-off": (
        "Das Anpassen ist auf gta.clothing gerade abgeschaltet. Die Werkzeuge in Blender funktionieren weiter."
    ),
    "fit.error.unavailable": (
        "Das Anpassen auf gta.clothing ist gerade nicht verfügbar. Versuche es in einer Minute erneut."
    ),
    "fit.error.not-found": (
        "gta.clothing hat diese Anpassung nicht mehr (eine Anpassung wartet zehn Minuten auf das Add-on). Passe erneut "
        "an."
    ),
    "fit.error.body-version": (
        "gta.clothing passt an einen neueren Freemode-Körper an. Wähle Freemode-Körper hinzufügen unter Einrichtung "
        "erneut, richte das Kleidungsstück daran aus und passe erneut an."
    ),
    "fit.error.too-large": (
        "Das Kleidungsstück ist zu detailliert zum Anpassen: höchstens 120.000 Vertices und 240.000 Dreiecke. "
        "Reduziere es, zum Beispiel mit einem Decimate-Modifikator."
    ),
    "fit.error.mesh-invalid": "gta.clothing konnte dieses Kleidungsstück nicht anpassen:",
    "fit.error.quota": "Heute können keine weiteren Anpassungen gestartet werden. Neue gibt es {wait}.",
    "fit.error.busy": "gta.clothing war einige Minuten lang beschäftigt. Versuche es später erneut.",
    "fit.error.rate-limited": (
        "Zu viele Anfragen an gta.clothing in kurzer Zeit. Warte eine Minute und versuche es erneut."
    ),
    "fit.error.server": "Bei gta.clothing ist beim Anpassen etwas schiefgegangen. Versuche es erneut.",
    "fit.error.timeout": (
        "Die Anpassung dauerte länger, als gta.clothing erlaubt. Verringere die Details des Kleidungsstücks und "
        "versuche es erneut."
    ),
    "fit.error.network": "gta.clothing ist nicht erreichbar. Prüfe die Internetverbindung und versuche es erneut.",
    "fit.error.network-uploaded": (
        "Die Verbindung brach ab, nachdem das Kleidungsstück gesendet war. Anpassungen heute übrig zeigt, ob die "
        "Anpassung gezählt hat. Versuche es erneut."
    ),
    "fit.error.upload-timeout": (
        "Das Senden des Kleidungsstücks hat zu lange gedauert, daher hat gta.clothing aufgehört zu warten. Versuche es "
        "mit einer schnelleren oder stabileren Verbindung erneut, oder reduziere die Details des Kleidungsstücks, "
        "damit weniger zu senden ist."
    ),
    "fit.error.cancelled": "Die Anpassung wurde abgebrochen.",
    "fit.error.other": "gta.clothing hat die Anpassung abgelehnt ({code}).",
    "fit.wait.minutes": "in etwa {count} Minuten",
    "fit.wait.hours": "in etwa {count} Stunden",
    "fit.wait.later": "morgen",
    "fit.refunded": "Diese Anpassung zählt nicht für heute.",
    "fit.counted": "Diese Anpassung zählt für heute.",
    "fit.cancelled-counted": "Die Anpassung hatte auf gta.clothing schon begonnen, daher zählt sie für heute.",
    "fit.input.add-on": "Das Add-on hat etwas gesendet, das gta.clothing nicht annimmt. Aktualisiere das Add-on.",
    "fit.input.slot": "Nur Kleidung, die am Körper getragen wird, kann angepasst werden.",
    "fit.input.options": (
        "Eine Anpassungsoption liegt außerhalb ihres Bereichs. Prüfe die Optionen von An Körper anpassen."
    ),
    "fit.input.too-large": (
        "Das Kleidungsstück hat {vertices} Vertices und {triangles} Dreiecke; Anpassen nimmt höchstens 120.000 und "
        "240.000. Reduziere es, zum Beispiel mit einem Decimate-Modifikator."
    ),
    "fit.input.broken": (
        "Einige Vertices des Kleidungsstücks haben kaputte Positionen. Entferne sie oder importiere das Kleidungsstück "
        "erneut."
    ),
    "fit.input.far": (
        "Ein Teil des Kleidungsstücks liegt mehr als 3 m vom Körper entfernt. Entferne verirrte Teile und richte es "
        "dann erneut aus."
    ),
    "fit.input.degenerate": (
        "Das Kleidungsstück hat Flächen ohne Fläche. Nach Abstand zusammenführen im Bearbeitungsmodus entfernt sie."
    ),
    "fit.input.duplicate": (
        "Das Kleidungsstück hat übereinanderliegende doppelte Flächen. Nach Abstand zusammenführen im "
        "Bearbeitungsmodus entfernt die Kopien."
    ),
    "fit.input.seam-dense": (
        "Viele lose Kanten drängen sich an einer Stelle des Kleidungsstücks. Entferne dort lose Teile (im "
        "Bearbeitungsmodus) oder setze Nahtabstand in den Optionen von An Körper anpassen auf 0."
    ),
    "fit.input.seam-crowded": (
        "{count} offene Kanten drängen sich an einer Stelle des Kleidungsstücks, und gta.clothing nimmt dort höchstens "
        "{limit}: meist kleine lose Teile wie Knöpfe oder Ziernähte, die auf dem Stoff liegen. Sie sind ausgewählt: "
        "Drücke Tab, um sie zu sehen, und entferne sie oder führe sie zusammen (Nach Abstand zusammenführen). Oder "
        "setze Nahtabstand in den Optionen von An Körper anpassen auf 0."
    ),
    "fit.input.seam-crowded-prepare": (
        "{count} offene Kanten drängen sich an einer Stelle des Kleidungsstücks, und gta.clothing nimmt dort höchstens "
        "{limit}: meist dort, wo mehrere Schnittteile zusammenkommen und ihre Nähte noch nicht verbunden sind. "
        "Kleidungsstück vorbereiten unter Spielfertig verbindet sie: Führe es aus und passe dann erneut an. Die Stelle "
        "ist ausgewählt: Drücke Tab, um sie zu sehen."
    ),
    "fit.input.marker-far": (
        "Ein Marker sitzt weit vom Gelenk des Körpers entfernt. Prüfe die Marker, richte das Kleidungsstück erneut aus "
        "und passe an."
    ),
    "fit.input.marker-missing": (
        "Es fehlen Marker. Setze sie mit Auto-Marker, richte das Kleidungsstück aus und passe erneut an."
    ),
    "fit.input.marker-side": (
        "Die linken und rechten Marker sind vertauscht. Setze jeden Marker auf seine Seite und passe erneut an."
    ),
    "fit.input.marker-length": (
        "Die Marker von Ellbogen, Handgelenk, Knie oder Knöchel liegen nicht dort, wo die Gelenke eines Arms oder "
        "Beins sein können. Setze sie auf die Gelenke des Kleidungsstücks."
    ),
    "fit.input.gender": (
        "Das Geschlecht des Kleidungsstücks passt nicht zum Körper. Wähle unter Einrichtung das richtige Geschlecht."
    ),
    "fit.input.other": "gta.clothing hat ein Problem mit dem Kleidungsstück gefunden ({code}).",
    "fit.warning.inside-body": (
        "Teile des Kleidungsstücks liegen noch im Körper. Aus dem Körper schieben unter Korrigieren bewegt sie heraus."
    ),
    "fit.warning.low-coverage": (
        "Nur ein Teil des Kleidungsstücks liegt am Körper. Teile weit davon können sich im Spiel seltsam bewegen."
    ),
    "fit.warning.marker-offset": (
        "Einige Marker sitzen neben den Gelenken des Körpers. Prüfe die Marker von Schultern und Ellbogen."
    ),
    "fit.warning.proportion-clamped": (
        "Die Proportionen des Kleidungsstücks weichen stark vom Freemode-Körper ab; einige wurden begrenzt."
    ),
    "fit.warning.shape-strained": (
        "Einige Bereiche wurden beim Posieren gedehnt. Probleme zeigen unter Korrigieren findet sie."
    ),
    "fit.warning.attachment-fallback": (
        "Lose Teile wurden mit dem nächsten Teil des Körpers gewichtet. Prüfe sie im Weight-Paint-Modus."
    ),
    "fit.warning.unweighted": (
        "Einige Vertices haben keine Gewichte bekommen; das Spiel lässt sie zurück, wenn sich die Figur bewegt."
    ),
    "fit.done.fit": "An den Körper angepasst: in der Spielpose, mit Gewichten für {bones} Knochen.",
    "fit.done.review": (
        "An den Körper angepasst, mit Gewichten für {bones} Knochen. Prüfe, was gta.clothing aufgefallen ist:"
    ),
    "fit.done.weights": "Gewichte übertragen: {bones} Knochen.",
    "fit.done.not-on-body": (
        "Das Kleidungsstück liegt nicht am Körper, also hat sich nichts geändert. Richte es zuerst am Körper aus."
    ),
    "fit.done.unweighted": "{count} Vertices haben keine Gewichte bekommen.",
    "fit.changed": (
        "Das Kleidungsstück hat sich während des Anpassens geändert, daher wurde das Ergebnis nicht übernommen. Passe "
        "erneut an."
    ),
    "garment.next.fit": (
        "Weiter: An Körper anpassen unter Anpassen, oder Passform prüfen unter Korrigieren und von Hand anpassen."
    ),
    "garment.check.reference": "Üblich",
    "garment.check.reference-none": "–",
    "garment.check.reference-subtext": (
        "Üblich: wie weit Spielkleidung dieser Art vom Körper absteht, von gta.clothing."
    ),
    "garment.check.reference-offline": (
        "Melde dich an und erlaube den Online-Zugriff, um mit Spielkleidung zu vergleichen."
    ),
    # ---- garment fitting: units, stepped Prepare and Combine -----------------------------------------------------------
    "garment.unit.dm": "Dezimeter",
    "garment.done.import-unit": (
        "{name} importiert ({count} Vertices), Größe in {unit} gelesen, der einzigen Einheit, die ihm die Größe eines "
        "Kleidungsstücks gibt. Wirkt es falsch, importiere es erneut und wähle die Einheit."
    ),
    "garment.done.import-size": (
        "{name} importiert ({count} Vertices), aber mit {size} m hat es nicht die Größe dieser Art Kleidungsstück. "
        "Importiere es erneut und wähle die Einheit, oder prüfe die Kategorie."
    ),
    "garment.done.prepare-open": (
        "Vorbereitet, aber {count} Naht-Vertices fanden keinen Partner am Nachbarteil ({welded} verbunden): Die "
        "Schnittteile treffen sich dort nicht ganz. Sie sind ausgewählt: Drücke Tab, um sie zu sehen. An Körper "
        "anpassen gibt beiden Seiten einer Naht trotzdem dieselben Gewichte; zeigt sich im Spiel eine Lücke, vernähe "
        "diese Nähte in deiner Kleidungs-App und exportiere erneut, oder verbinde sie von Hand."
    ),
    "garment.done.combine-missing": (
        "Zusammengefasst, aber {count} Texturen wurden nicht gefunden und ohne ihre Pixel gebacken: {names}. Lege die "
        "Bilddateien dorthin, wo die Materialien sie erwarten (oder packe sie), und fasse erneut zusammen."
    ),
    "garment.done.step-cancelled": "{step} wurde abgebrochen; das Kleidungsstück ist wie vorher.",
    "garment.step.status": "{step}: {stage} ({done} von {total}). Esc bricht ab.",
    "garment.stage.seams": "Nähte werden gesucht",
    "garment.stage.weld": "Nähte werden verbunden",
    "garment.stage.clean": "Aufräumen und triangulieren",
    "garment.stage.pack-cut": "UV-Layout wird vorbereitet",
    "garment.stage.pack-scale": "UV-Inseln werden angeglichen",
    "garment.stage.pack": "UV-Layout wird gepackt",
    "garment.stage.bake-colour": "Farbe wird gebacken",
    "garment.stage.bake-alpha": "Transparenz wird gebacken",
    "garment.stage.bake-specular": "Specular-Map wird gebacken",
    "garment.stage.bake-normal": "Normal-Map wird gebacken",
    "garment.stage.bake-emission": "Emission-Map wird gebacken",
    "garment.stage.material": "Gemeinsames Material wird erstellt",
}
