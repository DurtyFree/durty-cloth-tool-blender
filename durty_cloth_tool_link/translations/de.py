# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2026 Schmid Software Solutions (https://schmid-software.de)
"""German (Deutsch). Informal "du", as Durty Cloth Tool uses it."""

TEXT = {
    "path.connected-apps": "Optionen > Verbundene Apps",
    "path.edit-in-app": "In verbundener App bearbeiten",
    "panel.main": "Durty Cloth Tool",
    "panel.details": "Verbindung",
    "panel.setup": "Verbinden",
    "panel.linked": "Verknüpfte Kleidung",
    "panel.live": "Live-Vorschau",
    "panel.checks": "Texturprüfung",
    "panel.model": "Modell",
    "panel.settings": "Einstellungen",
    "chip.connected": "Verbunden",
    "chip.live": "Live",
    "chip.connecting": "Verbinde",
    "chip.action": "Aktion nötig",
    "chip.offline": "Offline",
    "chip.problem": "Problem",
    "state.idle": "Nicht verbunden",
    "state.connecting": "Suche Durty Cloth Tool",
    "state.waiting": "Durty Cloth Tool nicht gefunden. Neuer Versuch folgt",
    "state.reconnecting": "Verbinde erneut mit Durty Cloth Tool",
    "state.hello": "Verbinde",
    "state.signing-in": "Warte auf die Anmeldung",
    "state.authenticating": "Melde an",
    "state.ready": "Angemeldet als {name}",
    "state.signed-out": "Abgemeldet",
    "state.dct-signed-out": "Durty Cloth Tool ist abgemeldet",
    "state.dct-disconnected": "In Durty Cloth Tool getrennt",
    "details.status": "Status: {state}",
    "details.account": "Angemeldet als {name}",
    "details.not-signed-in": "Nicht angemeldet",
    "details.project": "Projekt: {name}",
    "details.addon": "Add-on {version} ({channel})",
    "online.off": (
        "Der Online-Zugriff von Blender ist aus, darum kann Durty Cloth Tool nicht verbunden werden: Jede Verbindung "
        "wird mit deiner gta.clothing-Anmeldung bestätigt. Erlaube ihn unter Einstellungen > System > Netzwerk."
    ),
    "dct-signed-out": (
        "Durty Cloth Tool ist abgemeldet. Melde dich in Durty Cloth Tool an und wähle dann Verbinden. Das Add-on "
        "versucht es auch von selbst immer wieder."
    ),
    "dct-disconnected": "Diese App wurde in Durty Cloth Tool getrennt. Wähle Verbinden, um sie wieder zu verbinden.",
    "setup.find.title": "Durty Cloth Tool finden",
    "setup.find.done": "Durty Cloth Tool gefunden",
    "setup.find.subtext": "Starte Durty Cloth Tool auf diesem Computer. Das Add-on findet es automatisch.",
    "setup.find.searching": "Suche Durty Cloth Tool…",
    "setup.find.waiting": "Durty Cloth Tool läuft noch nicht. Das Add-on sucht weiter…",
    "setup.sign-in.title": "Mit gta.clothing anmelden",
    "setup.sign-in.done": "Angemeldet",
    "setup.sign-in.subtext": (
        "Creator Link nutzt dein gta.clothing-Konto (Discord). Du meldest dich auf diesem Computer einmal an."
    ),
    "setup.sign-in.starting": "Starte die Anmeldung…",
    "setup.sign-in.finding": "Suche Durty Cloth Tool, um die Anmeldung zu bestätigen…",
    "setup.sign-in.how": (
        "Durty Cloth Tool bittet dich, sie zu bestätigen. Läuft es nicht, bekommst du einen Code für deinen Browser."
    ),
    "setup.sign-in.waiting": "Warte auf die Bestätigung…",
    "setup.sign-in.asked": "Durty Cloth Tool zeigt eine Anmeldeanfrage. Bestätige sie dort.",
    "setup.sign-in.approved": "Durty Cloth Tool hat die Anmeldung bestätigt. Schließe ab…",
    "setup.sign-in.declined": "Durty Cloth Tool hat die Anmeldung nicht bestätigt. Melde dich stattdessen im Browser an.",
    "setup.sign-in.browser-subtext": "Öffne die Anmeldeseite und prüfe, dass sie diesen Code zeigt:",
    "setup.sign-in.signed-out": "Du hast dich abgemeldet. Melde dich wieder an, um Creator Link zu nutzen.",
    "linked.project": "Projekt: {name}",
    "linked.no-project": "Öffne ein Projekt in Durty Cloth Tool.",
    "linked.no-cloth": "Wähle ein Kleidungsstück in Durty Cloth Tool, um hier daran zu arbeiten.",
    "linked.variation": "Variante {letter}",
    "linked.number": "#{number}",
    "linked.unknown": "Verknüpfte Kleidung",
    "linked.unknown-subtext": "Wähle sie einmal in Durty Cloth Tool aus, um hier ihren Namen zu sehen.",
    "linked.map": "Map",
    "linked.follows": "Folgt deiner Auswahl in Durty Cloth Tool",
    "linked.image": "Mit dem Bild unten verknüpft",
    "linked.open-map": "Map in Blender öffnen",
    "linked.map-missing.diffuse": "Dieses Kleidungsstück hat keine Diffuse-Map.",
    "linked.map-missing.normal": "Dieses Kleidungsstück hat keine Normal-Map.",
    "linked.map-missing.specular": "Dieses Kleidungsstück hat keine Specular-Map.",
    "map.diffuse": "Diffuse (Farbe)",
    "map.diffuse-short": "Diffuse",
    "map.diffuse.desc": "Die Farbtextur des Kleidungsstücks",
    "map.normal": "Normal",
    "map.normal.desc": "Die Normal-Map des Kleidungsstücks",
    "map.specular": "Specular",
    "map.specular.desc": "Die Specular-Map des Kleidungsstücks",
    "gender.male": "Männlich",
    "gender.female": "Weiblich",
    "open.opened": "Aus Durty Cloth Tool geöffnet: {name}",
    "open.texture-busy": (
        "Durty Cloth Tool hat {name} gesendet, aber eine Live-Vorschau läuft oder speichert. Beende sie und sende die "
        "Map dann erneut."
    ),
    "open.texture-failed": "{name} konnte nicht geöffnet werden: {detail}",
    "open.stop-live-first": "Beende zuerst die Live-Vorschau.",
    "open.reading": "Lese die Map aus Durty Cloth Tool…",
    "open.map-upsell": "Die Maps eines Kleidungsstücks hier zu öffnen ist in Durty Cloth Tool Ultimate enthalten.",
    "open.model-importing": "Importiere {name} mit Sollumz…",
    "open.model-needs-sollumz": "Durty Cloth Tool hat das Modell {name} gesendet. {problem}",
    "open.model-busy": (
        "Durty Cloth Tool hat das Modell {name} gesendet, aber ein anderes Modell wird noch gesendet oder gespeichert. "
        "Sende es gleich noch einmal."
    ),
    "open.model-failed": "Das Modell {name} konnte nicht geöffnet werden: {detail}",
    "open.import-failed": "Sollumz konnte das Modell nicht importieren ({detail}). Sein Info-Log zeigt die Details.",
    "open.no-dictionary": "Sollumz hat kein Drawable Dictionary importiert. Sein Info-Log zeigt die Details.",
    "open.import-errors": (
        "Sollumz hat beim Importieren Fehler gemeldet, darum wurde das Modell nicht mit dem Kleidungsstück verknüpft. "
        "Sein Info-Log zeigt die Details."
    ),
    "open.model-warnings": (
        "Aus Durty Cloth Tool geöffnet: {name}. Sollumz hat Warnungen gemeldet; sein Info-Log zeigt die Details."
    ),
    "live.off": "Starte die Live-Vorschau, um deine Farbe auf dem Ped zu sehen.",
    "live.reading": "Lese das Bild…",
    "live.starting": "Starte die Live-Vorschau…",
    "live.on": "Live auf dem Ped",
    "live.sending": "Sende das Bild…",
    "live.not-worn": "Zieh dem Ped dieses Kleidungsstück in Durty Cloth Tool an, um es zu sehen.",
    "live.paused-dct": "Die 3D-Vorschau ist in Durty Cloth Tool pausiert.",
    "live.paused": "Pausiert. Deine Änderungen werden gesendet, wenn du fortsetzt.",
    "live.saving": "Speichere…",
    "live.unsaved": "Noch nicht im Projekt gespeichert",
    "live.linked": "Verknüpft mit {name} · {map}",
    "live.map": "Map: {map}",
    "live.save-subtext": (
        "Speichern schreibt diese Map in dein Projekt. Du kannst es im Verlauf des Kleidungsstücks in Durty Cloth "
        "Tool rückgängig machen."
    ),
    "live.saved": "In {name} gespeichert. Du kannst es im Verlauf rückgängig machen.",
    "live.saved-unnamed": "Im Kleidungsstück gespeichert. Du kannst es im Verlauf rückgängig machen.",
    "live.saved-variation": "Als neue Variante von {name} gespeichert.",
    "live.saved-variation-unnamed": "Als neue Variante gespeichert.",
    "live.discarded": "Die Änderungen in Durty Cloth Tool wurden verworfen.",
    "live.stopped": "Live-Vorschau beendet.",
    "live.stopped-unsaved": (
        "Live-Vorschau beendet. Die Änderungen wurden nicht im Projekt gespeichert; das Bild in Blender behält sie."
    ),
    "live.failed": "Die Live-Vorschau wurde nach einem unerwarteten Problem beendet: {detail}",
    "live.upsell": "Die Live-Vorschau ist in Durty Cloth Tool Ultimate enthalten.",
    "live.save-upsell": "Das Speichern im Kleidungsstück ist in Durty Cloth Tool Ultimate enthalten.",
    "live.image-changed": "Die Bildgröße hat sich geändert. Starte die Live-Vorschau erneut.",
    "live.image-removed": "Das Bild wurde entfernt.",
    "live.no-memory": "Nicht genug Speicher für ein so großes Bild.",
    "colour.non-color-diffuse": "Das Bild ist auf Non-Color gestellt; seine Werte werden unverändert als Farbe gesendet.",
    "colour.unknown-diffuse": (
        "Der Farbraum {space} des Bildes wird nicht umgerechnet gesendet; nutze sRGB für genaue Farben."
    ),
    "colour.unknown-data": (
        "Stelle den Farbraum der Map auf Non-Color; {space}-Werte werden so gesendet, wie sie in Blender sind."
    ),
    "image.none": "Wähle zuerst ein Bild.",
    "image.tiled": "UDIM-Bilder (Kacheln) können nicht verwendet werden. Nutze ein einzelnes Bild.",
    "image.source": "Nur Bilddateien und generierte Bilder können verwendet werden.",
    "image.unreadable": "Das Bild konnte nicht gelesen werden.",
    "image.not-loaded": "Das Bild konnte nicht geladen werden. Prüfe, ob seine Datei existiert.",
    "image.channels": "Nur Graustufen-, RGB- und RGBA-Bilder können verwendet werden.",
    "image.empty": "Das Bild hat keine Pixel. Öffne oder erstelle es zuerst.",
    "image.too-large": "Bilder mit mehr als {size} Pixeln Kantenlänge können nicht verwendet werden.",
    "image.no-painted": "Kein bemaltes Bild gefunden. Wähle das Bild in der Liste.",
    "checks.errors": "Fehler: {count}",
    "checks.warnings": "Warnungen: {count}",
    "checks.notes": "Hinweise: {count}",
    "checks.clean": "Keine Probleme gefunden.",
    "checks.not-checked": "Durty Cloth Tool prüft die Textur, wenn die Live-Vorschau startet.",
    "checks.checking": "Prüfe die Textur…",
    "checks.unavailable": "Die Texturprüfung ist in Durty Cloth Tool Ultimate enthalten.",
    "severity.error": "Fehler",
    "severity.warning": "Warnung",
    "severity.info": "Hinweis",
    "finding.unknown": "Durty Cloth Tool meldet {code}.",
    "finding.non-power-of-two": "Die Größe ist keine Zweierpotenz (zum Beispiel 1024 oder 2048).",
    "finding.not-multiple-of-four": "Die Größe ist kein Vielfaches von vier, das komprimierte Texturen brauchen.",
    "finding.too-large": "Die Textur ist größer als 2048 Pixel pro Seite und braucht viel Spielspeicher.",
    "finding.too-small": "Die Textur ist kleiner als 16 Pixel pro Seite.",
    "finding.size-changed": "Die Größe weicht von der im Projekt gespeicherten Textur ab.",
    "finding.palette-alpha": (
        "Dieses Kleidungsstück nutzt eine Farbpalette: Sein Alphakanal wählt Palettenfarben, male Alpha also mit "
        "Bedacht."
    ),
    "finding.cutout-alpha": (
        "Dieses Kleidungsstück nutzt Alpha zum Ausschneiden: Transparente Pixel sind auf dem Ped unsichtbar."
    ),
    "finding.hair-ramp": "Das sind Haare: Das Spiel färbt sie mit der Haarfarbe, die der Spieler wählt.",
    "finding.bc1-alpha": "Die gespeicherte Textur behält nur ganz transparentes oder ganz deckendes Alpha.",
    "finding-fix.non-power-of-two": "Skaliere vor dem Speichern auf eine Zweierpotenz, zum Beispiel 1024 x 1024.",
    "finding-fix.not-multiple-of-four": "Skaliere so, dass beide Seiten durch vier teilbar sind, zum Beispiel 1024 x 512.",
    "finding-fix.too-large": "Nutze höchstens 2048 Pixel pro Seite, außer das Kleidungsstück braucht die Details.",
    "finding-fix.too-small": "Nutze mindestens 16 Pixel pro Seite.",
    "finding-fix.size-changed": (
        "Speichern ersetzt die Textur in dieser Größe. Skaliere auf die gespeicherte Größe, wenn du sie nicht ändern "
        "wolltest."
    ),
    "finding-fix.palette-alpha": "Lass die Alphawerte, wie sie sind, außer du willst die Palettenfarben ändern.",
    "finding-fix.cutout-alpha": "Male Transparenz nur dort, wo das Kleidungsstück verborgen sein soll.",
    "finding-fix.hair-ramp": (
        "Male die Schattierung in den Grünkanal und die Strähnchen in den Rotkanal, nicht die fertige Farbe."
    ),
    "finding-fix.bc1-alpha": "Nutze ganz transparentes oder ganz deckendes Alpha; weiche Kanten gehen beim Speichern verloren.",
    "model.subtext": "Sendet das Modell erneut, kurz nachdem du aufhörst zu bearbeiten.",
    "model.name": "Modell: {name}",
    "model.sending": "Sende {name} (Texturen: {count})",
    "model.previewing": "Wird in Durty Cloth Tool auf dem Ped gezeigt. Speichere oder verwirf es dort oder hier.",
    "model.findings": "Durty Cloth Tool meldet Befunde: {count}.",
    "model.warnings-paused": (
        "Sollumz hat Warnungen gemeldet, darum ist das automatische Senden pausiert. Prüfe das Info-Log von Sollumz "
        "und sende dann erneut, um fortzufahren."
    ),
    "model.warnings": "Sollumz hat Warnungen gemeldet; sein Info-Log zeigt die Details.",
    "model.saving": "Speichere das Modell in Durty Cloth Tool…",
    "model.saved": "Modell im Kleidungsstück gespeichert. Du kannst es im Verlauf rückgängig machen.",
    "model.discarded": "Das Modell in Durty Cloth Tool wurde verworfen.",
    "model.save-retry": "Durty Cloth Tool lädt das Modell noch. Speichere gleich…",
    "model.save-busy": "Durty Cloth Tool ist noch mit dem Modell beschäftigt. Speichere gleich noch einmal.",
    "model.block.no-model": "Sende zuerst ein Modell.",
    "model.block.saving": "Wird bereits gespeichert.",
    "model.block.waiting": "Warte, bis Durty Cloth Tool geantwortet hat.",
    "model.block.pushing": "Warte, bis das neueste Senden in Durty Cloth Tool zu sehen ist, und speichere dann.",
    "model.block.due": (
        "Deine neuesten Änderungen werden gleich gesendet. Speichere, sobald sie in Durty Cloth Tool zu sehen sind."
    ),
    "model.wait.tool": "Das automatische Senden wartet, bis das laufende Werkzeug fertig ist.",
    "model.wait.mode": "Das automatische Senden wartet, bis du {mode} verlässt.",
    "model.gone": "Das gesendete Modell ist nicht mehr in dieser Datei. Sende es erneut.",
    "model.linked": "Verknüpft mit {name}",
    "model.linked-twice": (
        "{name} ist mit demselben Kleidungsstück verknüpft. Hebe eine der Verknüpfungen auf: Jedes Kleidungsstück "
        "nimmt ein Modell."
    ),
    "model.not-linked": "Dieses Drawable Dictionary ist mit keinem Kleidungsstück verknüpft.",
    "model.failed": "Das automatische Senden ist fehlgeschlagen: {detail}",
    "model.select": "Wähle das Modell zum Senden: ein Sollumz Drawable Dictionary oder ein Objekt darin.",
    "model.one-root": "Wähle nur Objekte eines Drawable Dictionary.",
    "model.needs-dictionary": (
        "Durty Cloth Tool braucht ein Drawable Dictionary. Ordne das Drawable einem unter (Sollumz: Create Drawable "
        "Dictionary) und sende erneut."
    ),
    "model.not-sollumz": "Wähle ein Sollumz Drawable Dictionary oder ein Objekt darin.",
    "model.unhide": (
        "Blende das Drawable Dictionary (oder ein Objekt darin) ein, mach es auswählbar und sende dann erneut."
    ),
    "model.not-shown": (
        "Das Modell ist in keiner Szene, die ein Blender-Fenster zeigt. Zeig seine Szene an und sende dann erneut."
    ),
    "model.not-in-layer": "Das Modell ist nicht in der aktuellen View Layer. Zeig es an und sende dann erneut.",
    "model.export-failed": "Sollumz konnte das Modell nicht exportieren: {detail}",
    "model.not-exported": "Sollumz hat das Modell nicht exportiert. Sein Info-Log zeigt die Details.",
    "sollumz.ready": "Sollumz {version}",
    "sollumz.ready-unknown": "Sollumz",
    "sollumz.missing": "Installiere und aktiviere Sollumz {version} oder neuer, um Modelle zu öffnen und zu senden.",
    "sollumz.too-old": (
        "Dieses Sollumz ist zu alt, um für Durty Cloth Tool zu exportieren. Aktualisiere auf Sollumz {version} oder "
        "neuer."
    ),
    "sollumz.tested": "Getestet mit Sollumz {version}.",
    "bundle.unreadable": "Der Exportordner konnte nicht gelesen werden ({detail}).",
    "bundle.not-dictionary": (
        "Sollumz hat ein Drawable oder Fragment exportiert, kein Drawable Dictionary. Durty Cloth Tool braucht ein "
        "Drawable Dictionary: Ordne dein Drawable einem unter (Sollumz: Create Drawable Dictionary) und sende erneut."
    ),
    "bundle.no-model": "Sollumz hat kein Modell exportiert. Das Info-Log von Sollumz zeigt den Grund.",
    "bundle.several": "Sollumz hat mehrere Drawable Dictionaries exportiert ({count}). Wähle Objekte von nur einem.",
    "bundle.bad-name": (
        "'{name}' kann nicht gesendet werden: Dateinamen dürfen nur Buchstaben, Ziffern, '_', '-' und '.' enthalten, "
        "nicht mit '.' beginnen, kein '..' enthalten und höchstens 128 Zeichen lang sein. Benenne die Textur oder "
        "das Modell in Blender um."
    ),
    "bundle.duplicate": "Zwei Texturen heißen '{name}'. Gib jeder Textur einen eigenen Namen.",
    "bundle.too-many": "Das Modell nutzt {count} Texturen; höchstens {limit} können gesendet werden.",
    "bundle.empty-file": "'{name}' ist leer. Exportiere das Modell erneut.",
    "bundle.too-large": "Modell und Texturen sind zusammen größer als {size} MiB und können nicht gesendet werden.",
    "bundle.invalid": "Der Export kann nicht gesendet werden: {detail}",
    "settings.connection": "Verbindung",
    "settings.account": "Konto",
    "settings.updates": "Updates",
    "settings.privacy": "Datenschutz",
    "settings.models": "Modelle",
    "settings.connect-subtext": (
        "Braucht Durty Cloth Tool auf diesem Computer. Die Verbindung bleibt auf diesem Computer; gta.clothing "
        "bestätigt deine Anmeldung für jede Verbindung."
    ),
    "settings.signed-in-as": "Angemeldet als {name}",
    "settings.not-signed-in": "Nicht angemeldet",
    "settings.signed-out": "Abgemeldet",
    "settings.sign-out-subtext": "Abmelden beendet die gta.clothing-Anmeldung dieses Add-ons auf diesem Computer.",
    "settings.device-name-subtext": (
        "Die Bestätigungsseite von gta.clothing zeigt ihn, damit du deine Computer unterscheiden kannst."
    ),
    "settings.licence": "GPL-3.0-or-later, Schmid Software Solutions. Gepflegt von DurtyFree (Pleb Masters).",
    "settings.this-version": "Diese Version: {version} ({channel})",
    "settings.diagnostics-copied": (
        "Diagnose kopiert. Füge sie im Pleb Masters Community Discord Server ein, wenn du um Hilfe bittest. Sie "
        "enthält Versionen und Statuscodes, keine Dateipfade und keine Anmeldedaten."
    ),
    "settings.disk-install": (
        "Diese Kopie wurde aus einer Datei installiert, darum kann Blender sie nicht aktualisieren. Für "
        "Updates zieh den Installationslink von der Plugin-Seite auf gta.clothing auf Blender."
    ),
    "settings.updates-on": "Blender aktualisiert dieses Add-on aus dem Erweiterungs-Repository von Durty Cloth Tool.",
    "op.plugins-page": "Installationslink holen",
    "op.plugins-page.desc": "Die Plugin-Seite auf gta.clothing öffnen, wo du den Installationslink auf Blender ziehst",
    "info.channel": (
        "Experimental bekommt neue Funktionen und Korrekturen zuerst und ändert sich öfter. Release bekommt "
        "sie, sobald sie getestet sind. Den Kanal wählst du mit dem Installationslink, den du auf Blender "
        "ziehst."
    ),
    "settings.code-copied": "Code kopiert.",
    "channel.release": "Release",
    "channel.experimental": "Experimental",
    "info.find": (
        "Creator Link spricht nur mit Durty Cloth Tool auf diesem Computer. Außer deiner Anmeldung geht nichts ins "
        "Internet."
    ),
    "info.sign-in": (
        "Die Anmeldung zeigt Durty Cloth Tool, dass dieses Add-on zu deinem Konto gehört. Das Add-on sieht dein "
        "Discord-Passwort nie. Durty Cloth Tool zeigt diese App unter {apps}, wo du sie trennen kannst."
    ),
    "info.map": (
        "Wähle, welche Map des Kleidungsstücks das Bild in der Vorschau ersetzt: Diffuse (Farbe), Normal oder "
        "Specular. Diffuse-Bilder sind sRGB-Farbe; stelle Normal- und Specular-Maps auf Non-Color."
    ),
    "info.variation": (
        "Normal- und Specular-Maps gehören zum Modell und werden von jeder Variante geteilt, darum kann nur Diffuse "
        "(Farbe) eine neue Variante werden."
    ),
    "info.live": (
        "Das Add-on liest das Bild, wenn ein Pinselstrich endet, und sendet, was sich geändert hat. In deinem Projekt "
        "wird nichts gespeichert, bis du In Kleidungsstück speichern oder Als neue Variante speichern wählst."
    ),
    "info.model": (
        "Modell senden exportiert das ausgewählte Sollumz Drawable Dictionary als CodeWalker XML (YDD) mit seinen "
        "Texturen und zeigt es auf dem verknüpften Kleidungsstück. Ein aus Durty Cloth Tool gesendetes Modell wird "
        "importiert, mit seinem Kleidungsstück verknüpft und nach jeder Änderung erneut gesendet. Gespeichert wird "
        "erst mit Modell im Kleidungsstück speichern."
    ),
    "info.open-map": (
        "Öffnet diese Map des Kleidungsstücks aus deinem Projekt als Bild in Blender, verknüpft mit dem "
        "Kleidungsstück, und startet ihre Live-Vorschau. Durty Cloth Tool kann eine Map auch senden: {edit} im Menü "
        "des Kleidungsstücks."
    ),
    "info.model-linked": (
        "Ein aus Durty Cloth Tool geöffnetes Modell merkt sich sein Kleidungsstück, auch in der gespeicherten "
        ".blend-Datei, damit es immer an dieses Kleidungsstück gesendet wird. Eine mit Duplizieren gemachte Kopie "
        "trägt die Verknüpfung mit: Hebe sie bei dem Modell auf, das nicht verknüpft sein soll."
    ),
    "info.linked": (
        "Ein aus Durty Cloth Tool geöffnetes Bild merkt sich sein Kleidungsstück und seine Map, auch in der "
        "gespeicherten .blend-Datei, damit seine Live-Vorschau immer zu diesem Kleidungsstück geht. Hebe die "
        "Verknüpfung unter Live-Vorschau auf, um es für das in Durty Cloth Tool ausgewählte Kleidungsstück zu nutzen."
    ),
    "info.checks": (
        "Durty Cloth Tool prüft das Bild darauf, was GTA V und das Kleidungsstück brauchen, wie seine Fehlerliste. "
        "Behebe Fehler vor dem Speichern; Warnungen und Hinweise sind Ratschläge."
    ),
    "info.privacy": (
        "Bleibt auf diesem Computer: deine Bilder, Modelle und die Pixel der Live-Vorschau. Sie gehen nur an Durty "
        "Cloth Tool. Geht an gta.clothing: deine Anmeldung (mit dem Namen dieses Computers, außer du schaltest das "
        "aus), eine Bestätigung pro Verbindung, deine Abmeldung, die Update-Prüfungen von Blender und, nachdem du "
        "zugestimmt hast, die Form eines Kleidungsstücks, das du dort anpasst."
    ),
    "op.connect": "Verbinden",
    "op.connect.desc": "Mit Durty Cloth Tool auf diesem Computer verbinden",
    "op.disconnect": "Trennen",
    "op.disconnect.desc": "Von Durty Cloth Tool trennen. Eine laufende Live-Vorschau endet",
    "op.sign-in": "Anmelden",
    "op.sign-in.desc": (
        "Mit deinem gta.clothing-Konto (Discord) anmelden. Durty Cloth Tool bittet dich, es zu bestätigen; läuft es "
        "nicht, bekommst du einen Code für deinen Browser"
    ),
    "op.sign-in-browser": "Im Browser anmelden",
    "op.sign-in-browser.desc": (
        "Mit deinem gta.clothing-Konto (Discord) auf der Seite von gta.clothing in deinem Browser anmelden"
    ),
    "op.open-sign-in": "Anmeldeseite öffnen",
    "op.open-sign-in.desc": "Die gta.clothing-Seite öffnen, die diese Anmeldung bestätigt",
    "op.copy-code": "Code kopieren",
    "op.copy-code.desc": "Den Anmeldecode in die Zwischenablage kopieren",
    "op.cancel-sign-in": "Abbrechen",
    "op.cancel-sign-in.desc": "Nicht mehr auf die Anmeldung warten",
    "op.sign-out": "Abmelden",
    "op.sign-out.desc": "Dieses Add-on von gta.clothing abmelden und trennen",
    "op.update-page": "Update holen",
    "op.update-page.desc": "Die Seite mit den aktuellen Versionen von Durty Cloth Tool und seinen Plugins öffnen",
    "op.open-map": "Map öffnen",
    "op.open-map.desc": (
        "Diese Map des Kleidungsstücks aus deinem Projekt als verknüpftes Bild öffnen und ihre Live-Vorschau starten"
    ),
    "op.unlink": "Verknüpfung aufheben",
    "op.unlink.desc": (
        "Dieses Bild nicht mehr mit seinem Kleidungsstück verknüpfen, damit es deiner Auswahl in Durty Cloth Tool folgt"
    ),
    "op.unlink-model.desc": (
        "Dieses Drawable Dictionary nicht mehr mit seinem Kleidungsstück verknüpfen. Sein nächstes erstes Senden geht "
        "an das in Durty Cloth Tool ausgewählte Kleidungsstück"
    ),
    "op.use-paint-image": "Bemaltes Bild nutzen",
    "op.use-paint-image.desc": "Das Bild nutzen, auf dem du malst, oder das im Image Editor",
    "op.live-start": "Live-Vorschau starten",
    "op.live-start.desc": (
        "Dieses Bild auf dem verknüpften Kleidungsstück zeigen und nach jedem Pinselstrich aktualisieren. Gespeichert "
        "wird erst, wenn du speicherst"
    ),
    "op.live-stop": "Live-Vorschau beenden",
    "op.live-stop.desc": (
        "Das Bild nicht mehr senden. Die Änderungen bleiben auf dem Ped, bis du sie verwirfst oder Durty Cloth Tool "
        "sie verwirft"
    ),
    "op.live-pause": "Pausieren",
    "op.live-pause.desc": "Vorerst keine Änderungen senden. Das Ped zeigt weiter das letzte Update",
    "op.live-resume": "Fortsetzen",
    "op.live-resume.desc": "Wieder Änderungen senden, zuerst alles, was sich während der Pause geändert hat",
    "op.live-send": "Jetzt senden",
    "op.live-send.desc": "Das Bild jetzt erneut senden, für Änderungen durch Skripte, Baking oder Neuladen",
    "op.live-save": "In Kleidungsstück speichern",
    "op.live-save.desc": (
        "Die Map des verknüpften Kleidungsstücks in deinem Projekt durch dieses Bild ersetzen. Du kannst es im "
        "Verlauf rückgängig machen"
    ),
    "op.live-save-variation": "Als neue Variante speichern",
    "op.live-save-variation.desc": (
        "Dieses Bild dem verknüpften Kleidungsstück als neue Texturvariante hinzufügen (nur Diffuse (Farbe))"
    ),
    "op.live-discard": "Änderungen verwerfen",
    "op.live-discard.desc": (
        "Die Änderungen auf dem Ped verwerfen und beenden. Dein Projekt behält seine gespeicherte Textur"
    ),
    "op.check-again": "Erneut prüfen",
    "op.check-again.desc": "Durty Cloth Tool bitten, das Bild erneut zu prüfen",
    "op.model-push": "Modell senden",
    "op.model-push.desc": (
        "Das ausgewählte Sollumz Drawable Dictionary exportieren und auf dem verknüpften Kleidungsstück zeigen. "
        "Gespeichert wird erst, wenn du speicherst"
    ),
    "op.model-save": "Modell im Kleidungsstück speichern",
    "op.model-save.desc": (
        "Das gesendete Modell in deinem Projekt speichern. Das vorherige Modell bleibt im Verlauf des "
        "Kleidungsstücks"
    ),
    "op.model-discard": "Verwerfen",
    "op.model-discard.desc": "Das gesendete Modell vom Ped nehmen. Dein Projekt behält sein gespeichertes Modell",
    "op.diagnostics": "Diagnose kopieren",
    "op.diagnostics.desc": "Versionen und Statuscodes für den Support kopieren (keine Dateipfade und keine Anmeldedaten)",
    "op.help": "Hilfe",
    "op.help.desc": "Die Dokumentation von Durty Cloth Tool öffnen",
    "op.community": "Pleb Masters Community Discord",
    "op.community.desc": "Den Pleb Masters Community Discord Server öffnen, wo du um Hilfe bitten kannst",
    "op.info": "Mehr Informationen",
    "op.about": "Über",
    "op.about.desc": "Version und Lizenz des Add-ons, und was es wohin sendet",
    "about.title": "Durty Cloth Tool Link {version} ({channel})",
    "op.join-discord": "Discord-Server beitreten",
    "op.join-discord.desc": "Die Einladung zum Pleb Masters Community Discord Server im Browser öffnen",
    "prop.image": "Bild",
    "prop.image.desc": "Das Bild, das auf dem verknüpften Kleidungsstück gezeigt wird",
    "prop.map": "Map",
    "prop.map.desc": "Welche Map des verknüpften Kleidungsstücks das Bild in der Vorschau ersetzt",
    "prop.auto-push": "Automatisch senden",
    "prop.auto-push.desc": "Das Modell kurz nach dem Bearbeiten erneut senden (nach dem ersten Senden)",
    "prop.auto-connect": "Automatisch verbinden",
    "prop.auto-connect.desc": "Beim Start von Blender nach Durty Cloth Tool auf diesem Computer suchen",
    "prop.device-name": "Namen dieses Computers bei der Anmeldung zeigen",
    "prop.device-name.desc": (
        "Den Namen dieses Computers mit einer Anmeldung senden, damit die Bestätigungsseite von gta.clothing zeigt, "
        "welcher Computer fragt"
    ),
    "prop.delay": "Verzögerung für automatisches Senden",
    "prop.delay.desc": "Sekunden, die ein gesendetes Modell unverändert bleiben muss, bevor Automatisch senden es erneut sendet",
    "notice.signed-in": "Angemeldet als {name}.",
    "notice.signing-out": "Melde ab…",
    "notice.signed-out": "Abgemeldet.",
    "notice.signed-out-local": (
        "Auf diesem Computer abgemeldet. Erlaube den Online-Zugriff in den Einstellungen von Blender, um auch die "
        "Sitzung auf gta.clothing zu beenden."
    ),
    "notice.signed-out-unreached": (
        "Auf diesem Computer abgemeldet; gta.clothing war nicht erreichbar. Die Sitzung dort endet von selbst, oder "
        "beende sie auf deiner Kontoseite."
    ),
    "notice.browser-opens": "Dein Browser öffnet gleich die Anmeldeseite.",
    "notice.no-sign-in": "Es wartet keine Anmeldung.",
    "notice.not-gta-clothing": "Der Anmeldelink ist kein gta.clothing-Link.",
    "notice.unexpected": "Das Add-on hatte ein unerwartetes Problem: {detail}",
    "notice.secrets-unreadable": (
        "Die gespeicherte Anmeldung konnte nicht gelesen werden ({detail}). Melde dich erneut an."
    ),
    "notice.secret-store": (
        "Die geschützte Anmeldung konnte nicht gelesen oder geschrieben werden. Melde dich erneut an."
    ),
    "notice.file-error": "Eine Datei konnte nicht gelesen oder geschrieben werden: {detail}",
    "notice.not-ready": "Das Add-on ist nicht bereit.",
    "notice.connect-first": "Verbinde dich zuerst mit Durty Cloth Tool.",
    "notice.select-cloth": "Wähle zuerst ein Kleidungsstück in Durty Cloth Tool.",
    "notice.start-live-first": "Starte zuerst die Live-Vorschau.",
    "notice.wait-saving": "Warte, bis das Speichern fertig ist.",
    "notice.diffuse-only": "Nur Diffuse (Farbe) kann eine neue Variante werden.",
    "notice.pushing": "Ein Senden ist unterwegs.",
    "notice.online-off": "Der Online-Zugriff von Blender ist aus.",
    "error.generic": "Etwas ist schiefgelaufen.",
    "error.generic-code": "Etwas ist schiefgelaufen ({code}).",
    "error.malformed-message": (
        "Durty Cloth Tool und dieses Add-on haben sich nicht verstanden. Aktualisiere beide und versuche es erneut."
    ),
    "error.invalid-message": (
        "Durty Cloth Tool und dieses Add-on haben sich nicht verstanden. Aktualisiere beide und versuche es erneut."
    ),
    "error.unknown-message-type": "Durty Cloth Tool kennt diese Anfrage nicht. Aktualisiere Durty Cloth Tool.",
    "error.unexpected-message": "Durty Cloth Tool hat diese Anfrage gerade nicht erwartet. Versuche es erneut.",
    "error.message-too-large": "Das Bild oder Modell war zu groß zum Senden.",
    "error.unsupported-protocol": "Dieses Add-on und Durty Cloth Tool nutzen verschiedene Link-Versionen. Aktualisiere beide.",
    "error.plugin-too-old": "Dieses Add-on ist zu alt für dein Durty Cloth Tool. Aktualisiere das Add-on.",
    "error.dct-too-old": (
        "Dieses Durty Cloth Tool ist älter als dieses Add-on. Aktualisiere Durty Cloth Tool und wähle dann Verbinden."
    ),
    "error.not-authenticated": "Melde dich zuerst an.",
    "error.authentication-failed": "Durty Cloth Tool hat die Anmeldung nicht akzeptiert. Neuer Versuch…",
    "error.untrusted-endpoint": (
        "Ein Programm, das nicht dein Durty Cloth Tool ist, hat geantwortet, daher wurde nichts gesendet. Das Add-on "
        "sucht weiter nach Durty Cloth Tool."
    ),
    "error.account-mismatch": (
        "Durty Cloth Tool ist mit einem anderen Konto angemeldet. Melde dich hier ab und mit dem Konto an, das Durty "
        "Cloth Tool nutzt."
    ),
    "error.dct-signed-out": (
        "Durty Cloth Tool ist abgemeldet. Melde dich in Durty Cloth Tool an; das Add-on verbindet sich von selbst."
    ),
    "error.token-invalid": "Die Anmeldung ist abgelaufen. Melde erneut an…",
    "error.needs-license": "Dafür brauchst du eine Durty Cloth Tool Lizenz.",
    "error.needs-ultimate": "Das ist in Durty Cloth Tool Ultimate enthalten.",
    "error.no-project": "Öffne zuerst ein Projekt in Durty Cloth Tool.",
    "error.no-focused-item": "Wähle zuerst ein Kleidungsstück in Durty Cloth Tool.",
    "error.binding-in-use": "Eine andere App arbeitet bereits an dieser Textur oder diesem Modell.",
    "error.binding-not-found": "Das Kleidungsstück oder die Textur gibt es in Durty Cloth Tool nicht mehr.",
    "error.lease-not-found": "Durty Cloth Tool hat diese Vorschau beendet. Starte sie erneut.",
    "error.lease-limit": "Zu viele Live-Vorschauen sind offen. Beende zuerst eine.",
    "error.budget-exceeded": "Der Speicher für Live-Vorschauen in Durty Cloth Tool ist voll. Beende eine andere Live-Vorschau.",
    "error.frame-out-of-bounds": "Die Bildaktualisierung passte nicht in die Textur.",
    "error.frame-size-mismatch": "Das Bild konnte nicht gesendet werden.",
    "error.unsupported-format": (
        "Durty Cloth Tool nimmt dieses Format hier nicht an. Sende Modelle als Sollumz YDD XML."
    ),
    "error.stale-revision": "Neuere Pixel waren noch unterwegs. Speichere erneut.",
    "error.item-refused": "Durty Cloth Tool kann dieses Element nicht bearbeiten (Dummy, gesperrt oder geschützt).",
    "error.game-required": (
        "Durty Cloth Tool braucht dafür deine GTA V Installation. Richte sie in Durty Cloth Tool ein."
    ),
    "error.save-failed": "Durty Cloth Tool konnte nicht speichern. Seine Statusleiste zeigt die Details.",
    "error.busy": "Durty Cloth Tool ist beschäftigt. Versuche es gleich noch einmal.",
    "error.rate-limited": "Zu viele Anfragen. Warte kurz und versuche es erneut.",
    "error.connection-limit": "Zu viele Apps sind mit Durty Cloth Tool verbunden.",
    "error.request-denied": "Durty Cloth Tool hat die Anfrage abgelehnt.",
    "error.model-rejected": "Durty Cloth Tool konnte dieses Modell nicht verwenden. Prüfe es in Sollumz und sende erneut.",
    "error.internal-error": (
        "Etwas ist schiefgelaufen. Versuche es erneut und starte Blender und Durty Cloth Tool neu, wenn es wieder "
        "passiert."
    ),
    "error.disconnected": "Die Verbindung zu Durty Cloth Tool wurde unterbrochen.",
    "error.timeout": "Durty Cloth Tool hat nicht rechtzeitig geantwortet.",
    "error.superseded": "Eine neuere Anfrage hat diese ersetzt.",
    "error.cancelled": "Abgebrochen.",
    "error.closed": "Die Live-Vorschau ist geschlossen.",
    "error.signed-out": "Du hast dich abgemeldet. Melde dich an, um Creator Link wieder zu nutzen.",
    "error.assertion-invalid": "Die Anmeldung konnte nicht bestätigt werden. Neuer Versuch…",
    "error.pixel-source-failed": "Das Bild konnte für die Live-Vorschau nicht gelesen werden. Neuer Versuch…",
    "error.callback-failed": "Im Add-on ist etwas schiefgelaufen. Versuche es erneut.",
    "error.offline": (
        "Der Online-Zugriff von Blender ist aus. Erlaube ihn unter Einstellungen > System > Netzwerk, um dich "
        "anzumelden und zu verbinden."
    ),
    "error.network": "gta.clothing war nicht erreichbar. Prüfe die Internetverbindung.",
    "error.invalid-response": "gta.clothing hat unerwartet geantwortet. Versuche es später erneut.",
    "error.tls": (
        "Die sichere Verbindung zu gta.clothing ist fehlgeschlagen. Prüfe dein Netzwerk, deinen Proxy oder deine "
        "Antivirus-Einstellungen."
    ),
    "error.account_locked": "Dein gta.clothing-Konto ist gesperrt.",
    "error.discord_membership_required": (
        "Für Creator Link muss dein Discord-Konto Mitglied des Pleb Masters Community Discord Servers sein."
    ),
    "error.discord_unavailable": "Die Discord-Anmeldung ist gerade nicht verfügbar. Versuche es später erneut.",
    "error.plugin_update_required": "gta.clothing braucht eine neuere Version dieses Add-ons. Aktualisiere es.",
    "error.expired_token": "Der Anmeldecode ist abgelaufen. Melde dich erneut an.",
    "error.access_denied": "Die Anmeldung wurde abgelehnt.",
    "error.invalid_grant": "Die Anmeldung wurde nicht akzeptiert. Melde dich erneut an.",
    "error.session_invalid": "Die Anmeldung ist nicht mehr gültig. Melde dich erneut an.",
    "error.session_expired": "Die Anmeldung ist abgelaufen. Melde dich erneut an.",
    "error.session_revoked": "Die Anmeldung wurde auf gta.clothing beendet. Melde dich erneut an.",
    "error.refresh_in_progress": "Ein anderes Programm erneuert gerade deine Anmeldung. Versuche es gleich noch einmal.",
    "close.closed": "Live-Vorschau beendet.",
    "close.replaced": "Eine andere App hat diese Textur übernommen.",
    "close.itemRemoved": "Das Kleidungsstück wurde in Durty Cloth Tool entfernt.",
    "close.projectClosed": "Das Projekt wurde in Durty Cloth Tool geschlossen.",
    "close.entitlementLost": "Dein Plan enthält diese Funktion nicht mehr.",
    "close.signedOut": "Durty Cloth Tool wurde abgemeldet, darum endete die Vorschau.",
    "close.disconnected": "Die Verbindung zu Durty Cloth Tool wurde unterbrochen.",
    "feature.needsLicense": "Dafür brauchst du eine Durty Cloth Tool Lizenz.",
    "feature.needsUltimate": "Das ist in Durty Cloth Tool Ultimate enthalten.",
    "feature.unavailable": "Das ist in deinem Durty Cloth Tool Plan nicht enthalten.",
}
