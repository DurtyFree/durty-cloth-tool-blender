# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2026 Schmid Software Solutions (https://schmid-software.de)
"""French (Français). "vous", as Durty Cloth Tool uses it."""

TEXT = {
    "path.connected-apps": "Options > Applications connectées",
    "path.edit-in-app": "Modifier dans l'application connectée",
    "panel.main": "Durty Cloth Tool",
    "panel.details": "Connexion",
    "panel.setup": "Se connecter",
    "panel.linked": "Vêtement lié",
    "panel.live": "Aperçu en direct",
    "panel.checks": "Vérification de la texture",
    "panel.model": "Modèle",
    "panel.settings": "Réglages",
    "chip.connected": "Connecté",
    "chip.live": "En direct",
    "chip.connecting": "Connexion",
    "chip.action": "Action requise",
    "chip.offline": "Hors ligne",
    "chip.problem": "Problème",
    "state.idle": "Non connecté",
    "state.connecting": "Recherche de Durty Cloth Tool",
    "state.waiting": "Durty Cloth Tool introuvable. Nouvel essai bientôt",
    "state.reconnecting": "Reconnexion à Durty Cloth Tool",
    "state.hello": "Connexion",
    "state.signing-in": "En attente de la connexion au compte",
    "state.authenticating": "Connexion au compte",
    "state.ready": "Connecté en tant que {name}",
    "state.signed-out": "Déconnecté",
    "state.dct-signed-out": "Durty Cloth Tool est déconnecté",
    "state.dct-disconnected": "Déconnecté dans Durty Cloth Tool",
    "details.status": "État : {state}",
    "details.account": "Connecté en tant que {name}",
    "details.not-signed-in": "Non connecté au compte",
    "details.project": "Projet : {name}",
    "details.addon": "Module {version} ({channel})",
    "online.off": (
        "L'accès en ligne de Blender est désactivé, donc Durty Cloth Tool ne peut pas être connecté : chaque "
        "connexion est confirmée par votre compte gta.clothing. Autorisez-le dans Préférences > Système > Réseau."
    ),
    "dct-signed-out": (
        "Durty Cloth Tool est déconnecté. Connectez-vous dans Durty Cloth Tool, puis choisissez Connecter. Le module "
        "réessaie aussi de lui-même de temps en temps."
    ),
    "dct-disconnected": (
        "Cette application a été déconnectée dans Durty Cloth Tool. Choisissez Connecter pour la reconnecter."
    ),
    "setup.find.title": "Trouver Durty Cloth Tool",
    "setup.find.done": "Durty Cloth Tool trouvé",
    "setup.find.subtext": "Lancez Durty Cloth Tool sur cet ordinateur. Le module le trouve automatiquement.",
    "setup.find.searching": "Recherche de Durty Cloth Tool…",
    "setup.find.waiting": "Durty Cloth Tool n'est pas encore lancé. Le module continue de chercher…",
    "setup.sign-in.title": "Se connecter avec gta.clothing",
    "setup.sign-in.done": "Connecté au compte",
    "setup.sign-in.subtext": (
        "Creator Link utilise votre compte gta.clothing (Discord). Vous vous connectez une fois sur cet ordinateur."
    ),
    "setup.sign-in.starting": "Démarrage de la connexion…",
    "setup.sign-in.finding": "Recherche de Durty Cloth Tool pour approuver la connexion…",
    "setup.sign-in.how": (
        "Durty Cloth Tool vous demande de l'approuver. S'il n'est pas lancé, vous recevez un code pour votre "
        "navigateur."
    ),
    "setup.sign-in.waiting": "En attente de l'approbation…",
    "setup.sign-in.asked": "Durty Cloth Tool affiche une demande de connexion. Approuvez-la là-bas.",
    "setup.sign-in.approved": "Durty Cloth Tool a approuvé la connexion. Finalisation…",
    "setup.sign-in.declined": (
        "Durty Cloth Tool n'a pas approuvé la connexion. Connectez-vous plutôt dans le navigateur."
    ),
    "setup.sign-in.browser-subtext": "Ouvrez la page de connexion et vérifiez qu'elle affiche ce code :",
    "setup.sign-in.signed-out": "Vous êtes déconnecté. Reconnectez-vous pour utiliser Creator Link.",
    "linked.project": "Projet : {name}",
    "linked.no-project": "Ouvrez un projet dans Durty Cloth Tool.",
    "linked.no-cloth": "Sélectionnez un vêtement dans Durty Cloth Tool pour y travailler ici.",
    "linked.variation": "Variante {letter}",
    "linked.number": "n° {number}",
    "linked.unknown": "Vêtement lié",
    "linked.unknown-subtext": "Sélectionnez-le une fois dans Durty Cloth Tool pour voir son nom ici.",
    "linked.map": "Map",
    "linked.follows": "Suit votre sélection dans Durty Cloth Tool",
    "linked.image": "Lié à l'image ci-dessous",
    "linked.open-map": "Ouvrir une map dans Blender",
    "linked.map-missing.diffuse": "Ce vêtement n'a pas de map diffuse.",
    "linked.map-missing.normal": "Ce vêtement n'a pas de normal map.",
    "linked.map-missing.specular": "Ce vêtement n'a pas de map spéculaire.",
    "map.diffuse": "Diffuse (couleur)",
    "map.diffuse-short": "Diffuse",
    "map.diffuse.desc": "La texture de couleur du vêtement",
    "map.normal": "Normal",
    "map.normal.desc": "La normal map du vêtement",
    "map.specular": "Spéculaire",
    "map.specular.desc": "La map spéculaire du vêtement",
    "gender.male": "Homme",
    "gender.female": "Femme",
    "open.opened": "Ouvert depuis Durty Cloth Tool : {name}",
    "open.texture-busy": (
        "Durty Cloth Tool a envoyé {name}, mais un aperçu en direct est en cours ou enregistre. Arrêtez-le, puis "
        "renvoyez la map."
    ),
    "open.texture-failed": "Impossible d'ouvrir {name} : {detail}",
    "open.stop-live-first": "Arrêtez d'abord l'aperçu en direct.",
    "open.reading": "Lecture de la map depuis Durty Cloth Tool…",
    "open.map-upsell": "Ouvrir ici les maps d'un vêtement est inclus dans Durty Cloth Tool Ultimate.",
    "open.model-importing": "Importation de {name} avec Sollumz…",
    "open.model-needs-sollumz": "Durty Cloth Tool a envoyé le modèle {name}. {problem}",
    "open.model-busy": (
        "Durty Cloth Tool a envoyé le modèle {name}, mais un autre modèle est encore en cours d'envoi ou "
        "d'enregistrement. Renvoyez-le dans un instant."
    ),
    "open.model-failed": "Impossible d'ouvrir le modèle {name} : {detail}",
    "open.import-failed": "Sollumz n'a pas pu importer le modèle ({detail}). Son journal Info contient les détails.",
    "open.no-dictionary": "Sollumz n'a pas importé de Drawable Dictionary. Son journal Info contient les détails.",
    "live.off": "Lancez l'aperçu en direct pour voir votre peinture sur le ped.",
    "live.reading": "Lecture de l'image…",
    "live.starting": "Démarrage de l'aperçu en direct…",
    "live.on": "En direct sur le ped",
    "live.sending": "Envoi de l'image…",
    "live.not-worn": "Mettez ce vêtement sur le ped dans Durty Cloth Tool pour le voir.",
    "live.paused-dct": "L'aperçu 3D est en pause dans Durty Cloth Tool.",
    "live.paused": "En pause. Vos modifications sont envoyées quand vous reprenez.",
    "live.saving": "Enregistrement…",
    "live.unsaved": "Pas encore enregistré dans le projet",
    "live.linked": "Lié à {name} · {map}",
    "live.map": "Map : {map}",
    "live.save-subtext": (
        "L'enregistrement écrit cette map dans votre projet. Vous pouvez l'annuler dans l'Historique du vêtement "
        "dans Durty Cloth Tool."
    ),
    "live.saved": "Enregistré dans {name}. Vous pouvez l'annuler dans l'Historique.",
    "live.saved-unnamed": "Enregistré dans le vêtement. Vous pouvez l'annuler dans l'Historique.",
    "live.saved-variation": "Enregistré comme nouvelle variante de {name}.",
    "live.saved-variation-unnamed": "Enregistré comme nouvelle variante.",
    "live.discarded": "Les modifications ont été abandonnées dans Durty Cloth Tool.",
    "live.stopped": "Aperçu en direct arrêté.",
    "live.stopped-unsaved": (
        "Aperçu en direct arrêté. Les modifications n'ont pas été enregistrées dans le projet ; l'image dans Blender "
        "les conserve."
    ),
    "live.failed": "L'aperçu en direct s'est arrêté après un problème inattendu : {detail}",
    "live.upsell": "L'aperçu en direct est inclus dans Durty Cloth Tool Ultimate.",
    "live.save-upsell": "L'enregistrement dans le vêtement est inclus dans Durty Cloth Tool Ultimate.",
    "live.image-changed": "La taille de l'image a changé. Relancez l'aperçu en direct.",
    "live.image-removed": "L'image a été supprimée.",
    "live.no-memory": "Pas assez de mémoire pour une image aussi grande.",
    "colour.non-color-diffuse": (
        "L'image est réglée sur Non-Color ; ses valeurs sont envoyées telles quelles comme couleur."
    ),
    "colour.unknown-diffuse": (
        "L'espace colorimétrique {space} de l'image est envoyé sans conversion ; utilisez sRGB pour des couleurs "
        "exactes."
    ),
    "colour.unknown-data": (
        "Réglez l'espace colorimétrique de la map sur Non-Color ; les valeurs {space} sont envoyées telles qu'elles "
        "sont dans Blender."
    ),
    "image.none": "Choisissez d'abord une image.",
    "image.tiled": "Les images UDIM (tuiles) ne sont pas prises en charge. Utilisez une image unique.",
    "image.source": "Seuls les fichiers image et les images générées peuvent être utilisés.",
    "image.unreadable": "L'image n'a pas pu être lue.",
    "image.not-loaded": "L'image n'a pas pu être chargée. Vérifiez que son fichier existe.",
    "image.channels": "Seules les images en niveaux de gris, RGB et RGBA peuvent être utilisées.",
    "image.empty": "L'image n'a pas de pixels. Ouvrez-la ou créez-la d'abord.",
    "image.too-large": "Les images de plus de {size} pixels de côté ne peuvent pas être utilisées.",
    "image.no-painted": "Aucune image peinte trouvée. Choisissez l'image dans la liste.",
    "checks.errors": "Erreurs : {count}",
    "checks.warnings": "Avertissements : {count}",
    "checks.notes": "Remarques : {count}",
    "checks.clean": "Aucun problème trouvé.",
    "checks.not-checked": "Durty Cloth Tool vérifie la texture au démarrage de l'aperçu en direct.",
    "checks.checking": "Vérification de la texture…",
    "checks.unavailable": "La vérification de la texture est incluse dans Durty Cloth Tool Ultimate.",
    "severity.error": "Erreur",
    "severity.warning": "Avertissement",
    "severity.info": "Remarque",
    "finding.unknown": "Durty Cloth Tool a signalé {code}.",
    "finding.non-power-of-two": "La taille n'est pas une puissance de deux (par exemple 1024 ou 2048).",
    "finding.not-multiple-of-four": "La taille n'est pas un multiple de quatre, nécessaire aux textures compressées.",
    "finding.too-large": "La texture dépasse 2048 pixels de côté, ce qui utilise beaucoup de mémoire en jeu.",
    "finding.too-small": "La texture fait moins de 16 pixels de côté.",
    "finding.size-changed": "La taille diffère de celle de la texture enregistrée dans le projet.",
    "finding.palette-alpha": (
        "Ce vêtement utilise une palette de couleurs : son canal alpha choisit les couleurs de la palette, peignez "
        "donc l'alpha avec soin."
    ),
    "finding.cutout-alpha": (
        "Ce vêtement utilise l'alpha comme découpe : les pixels transparents sont masqués sur le ped."
    ),
    "finding.hair-ramp": "Ce sont des cheveux : le jeu les colore avec la couleur de cheveux choisie par le joueur.",
    "finding.bc1-alpha": "La texture enregistrée ne garde qu'un alpha entièrement transparent ou entièrement opaque.",
    "finding-fix.non-power-of-two": (
        "Redimensionnez à une puissance de deux, par exemple 1024 x 1024, avant d'enregistrer."
    ),
    "finding-fix.not-multiple-of-four": (
        "Redimensionnez pour que les deux côtés soient divisibles par quatre, par exemple 1024 x 512."
    ),
    "finding-fix.too-large": (
        "Utilisez au plus 2048 pixels de côté, sauf si le vêtement a besoin de ces détails."
    ),
    "finding-fix.too-small": "Utilisez au moins 16 pixels de côté.",
    "finding-fix.size-changed": (
        "L'enregistrement remplace la texture à cette taille. Redimensionnez à la taille enregistrée si vous ne "
        "vouliez pas la changer."
    ),
    "finding-fix.palette-alpha": (
        "Gardez les valeurs alpha telles quelles, sauf si vous voulez changer les couleurs de la palette."
    ),
    "finding-fix.cutout-alpha": "Peignez la transparence seulement là où le vêtement doit être masqué.",
    "finding-fix.hair-ramp": (
        "Peignez l'ombrage dans le canal vert et les mèches dans le canal rouge, pas la couleur finale."
    ),
    "finding-fix.bc1-alpha": (
        "Utilisez un alpha entièrement transparent ou entièrement opaque ; les bords doux sont perdus à "
        "l'enregistrement."
    ),
    "model.subtext": "Renvoie le modèle peu après que vous arrêtez de le modifier.",
    "model.name": "Modèle : {name}",
    "model.sending": "Envoi de {name} (textures : {count})",
    "model.previewing": (
        "Affiché sur le ped dans Durty Cloth Tool. Enregistrez-le ou abandonnez-le là-bas ou ici."
    ),
    "model.findings": "Durty Cloth Tool a signalé des problèmes : {count}.",
    "model.warnings-paused": (
        "Sollumz a signalé des avertissements, l'envoi automatique est donc en pause. Consultez le journal Info de "
        "Sollumz, puis envoyez de nouveau pour reprendre."
    ),
    "model.warnings": "Sollumz a signalé des avertissements ; son journal Info contient les détails.",
    "model.saving": "Enregistrement du modèle dans Durty Cloth Tool…",
    "model.saved": "Modèle enregistré dans le vêtement. Vous pouvez l'annuler dans l'Historique.",
    "model.discarded": "Le modèle a été abandonné dans Durty Cloth Tool.",
    "model.save-retry": "Durty Cloth Tool charge encore le modèle. Enregistrement dans un instant…",
    "model.save-busy": "Durty Cloth Tool est encore occupé avec le modèle. Enregistrez de nouveau dans un instant.",
    "model.block.no-model": "Envoyez d'abord un modèle.",
    "model.block.saving": "Enregistrement déjà en cours.",
    "model.block.waiting": "Attendez la réponse de Durty Cloth Tool.",
    "model.block.pushing": "Attendez que le dernier envoi s'affiche dans Durty Cloth Tool, puis enregistrez.",
    "model.block.due": (
        "Vos dernières modifications vont être envoyées. Enregistrez quand elles s'affichent dans Durty Cloth Tool."
    ),
    "model.wait.tool": "L'envoi automatique attend la fin de l'outil en cours.",
    "model.wait.mode": "L'envoi automatique attend que vous quittiez {mode}.",
    "model.gone": "Le modèle envoyé n'est plus dans ce fichier. Envoyez-le de nouveau.",
    "model.failed": "L'envoi automatique a échoué : {detail}",
    "model.select": "Sélectionnez le modèle à envoyer : un Drawable Dictionary Sollumz ou un objet qu'il contient.",
    "model.one-root": "Sélectionnez des objets d'un seul Drawable Dictionary.",
    "model.needs-dictionary": (
        "Durty Cloth Tool a besoin d'un Drawable Dictionary. Rattachez le Drawable à un Drawable Dictionary "
        "(Sollumz : Create Drawable Dictionary) et envoyez de nouveau."
    ),
    "model.not-sollumz": "Sélectionnez un Drawable Dictionary Sollumz ou un objet qu'il contient.",
    "model.unhide": (
        "Affichez le Drawable Dictionary (ou un objet qu'il contient), rendez-le sélectionnable, puis envoyez de "
        "nouveau."
    ),
    "model.not-shown": (
        "Le modèle n'est dans aucune scène affichée dans une fenêtre Blender. Affichez sa scène, puis envoyez de "
        "nouveau."
    ),
    "model.not-in-layer": "Le modèle n'est pas dans le view layer actuel. Affichez-le, puis envoyez de nouveau.",
    "model.export-failed": "Sollumz n'a pas pu exporter le modèle : {detail}",
    "model.not-exported": "Sollumz n'a pas exporté le modèle. Son journal Info contient les détails.",
    "sollumz.ready": "Sollumz {version}",
    "sollumz.ready-unknown": "Sollumz",
    "sollumz.missing": "Installez et activez Sollumz {version} ou plus récent pour ouvrir et envoyer des modèles.",
    "sollumz.too-old": (
        "Ce Sollumz est trop ancien pour exporter pour Durty Cloth Tool. Passez à Sollumz {version} ou plus récent."
    ),
    "sollumz.tested": "Testé avec Sollumz {version}.",
    "bundle.unreadable": "Le dossier d'export n'a pas pu être lu ({detail}).",
    "bundle.not-dictionary": (
        "Sollumz a exporté un drawable ou un fragment, pas un drawable dictionary. Durty Cloth Tool a besoin d'un "
        "Drawable Dictionary : rattachez votre Drawable à un Drawable Dictionary (Sollumz : Create Drawable "
        "Dictionary) et envoyez de nouveau."
    ),
    "bundle.no-model": "Sollumz n'a pas exporté de modèle. Le journal Info de Sollumz indique pourquoi.",
    "bundle.several": (
        "Sollumz a exporté plusieurs drawable dictionaries ({count}). Sélectionnez les objets d'un seul."
    ),
    "bundle.bad-name": (
        "'{name}' ne peut pas être envoyé : les noms de fichier ne peuvent contenir que des lettres, des chiffres, "
        "'_', '-' et '.', ne doivent pas commencer par '.' ni contenir '..', et font au plus 128 caractères. "
        "Renommez la texture ou le modèle dans Blender."
    ),
    "bundle.duplicate": "Deux textures s'appellent '{name}'. Donnez un nom différent à chaque texture.",
    "bundle.too-many": "Le modèle utilise {count} textures ; au plus {limit} peuvent être envoyées.",
    "bundle.empty-file": "'{name}' est vide. Exportez de nouveau le modèle.",
    "bundle.too-large": (
        "Le modèle et ses textures dépassent ensemble {size} MiB et ne peuvent pas être envoyés."
    ),
    "bundle.invalid": "L'export ne peut pas être envoyé : {detail}",
    "settings.connection": "Connexion",
    "settings.account": "Compte",
    "settings.updates": "Mises à jour",
    "settings.privacy": "Confidentialité",
    "settings.models": "Modèles",
    "settings.connect-subtext": (
        "Nécessite Durty Cloth Tool sur cet ordinateur. La connexion reste sur cet ordinateur ; gta.clothing "
        "confirme votre compte pour chaque connexion."
    ),
    "settings.signed-in-as": "Connecté en tant que {name}",
    "settings.not-signed-in": "Non connecté au compte",
    "settings.signed-out": "Déconnecté",
    "settings.sign-out-subtext": (
        "La déconnexion met fin à la connexion gta.clothing de ce module sur cet ordinateur."
    ),
    "settings.device-name-subtext": (
        "La page d'approbation de gta.clothing l'affiche, pour que vous distinguiez vos ordinateurs."
    ),
    "settings.licence": "GPL-3.0-or-later, Schmid Software Solutions. Maintenu par DurtyFree (Pleb Masters).",
    "settings.this-version": "Cette version : {version} ({channel})",
    "settings.diagnostics-copied": (
        "Diagnostic copié. Collez-le sur le serveur Pleb Masters Community Discord quand vous demandez de l'aide. Il "
        "contient des versions et des codes d'état, aucun chemin de fichier ni aucune donnée de connexion."
    ),
    "settings.disk-install": (
        "Cette copie a été installée depuis un fichier, Blender ne peut donc pas la mettre à jour. Pour "
        "recevoir les mises à jour, glissez le lien d'installation de la page des plugins de gta.clothing sur "
        "Blender."
    ),
    "settings.updates-on": "Blender met à jour ce module depuis le dépôt d'extensions de Durty Cloth Tool.",
    "op.plugins-page": "Obtenir le lien d'installation",
    "op.plugins-page.desc": "Ouvrir la page des plugins sur gta.clothing, d'où vous glissez le lien d'installation sur Blender",
    "info.channel": (
        "Experimental reçoit les nouvelles fonctions et corrections en premier et change plus souvent. "
        "Release les reçoit une fois testées. Vous choisissez le canal avec le lien d'installation que vous "
        "glissez sur Blender."
    ),
    "settings.code-copied": "Code copié.",
    "channel.release": "Release",
    "channel.experimental": "Experimental",
    "info.find": (
        "Creator Link ne communique qu'avec Durty Cloth Tool sur cet ordinateur. Rien n'est envoyé sur Internet, "
        "sauf votre connexion au compte."
    ),
    "info.sign-in": (
        "La connexion montre à Durty Cloth Tool que ce module appartient à votre compte. Le module ne voit jamais "
        "votre mot de passe Discord. Durty Cloth Tool affiche cette application dans {apps}, où vous pouvez la "
        "déconnecter."
    ),
    "info.map": (
        "Choisissez quelle map du vêtement l'image remplace dans l'aperçu : Diffuse (couleur), Normal ou "
        "Spéculaire. Les images diffuses sont en couleur sRGB ; réglez les maps normal et spéculaire sur Non-Color."
    ),
    "info.variation": (
        "Les maps normal et spéculaire appartiennent au modèle et sont partagées par toutes les variantes, donc "
        "seule la Diffuse (couleur) peut devenir une nouvelle variante."
    ),
    "info.live": (
        "Le module lit l'image à la fin de chaque coup de pinceau et envoie ce qui a changé. Rien n'est enregistré "
        "dans votre projet tant que vous ne choisissez pas Enregistrer dans le vêtement ou Enregistrer comme "
        "nouvelle variante."
    ),
    "info.model": (
        "Envoyer le modèle exporte le Drawable Dictionary Sollumz sélectionné en CodeWalker XML (YDD) avec ses "
        "textures et l'affiche sur le vêtement lié. Un modèle envoyé par Durty Cloth Tool est importé, lié à son "
        "vêtement et renvoyé après chaque modification. Rien n'est enregistré tant que vous ne choisissez pas "
        "Enregistrer le modèle dans le vêtement."
    ),
    "info.open-map": (
        "Ouvre cette map du vêtement depuis votre projet comme image dans Blender, liée au vêtement, et lance son "
        "aperçu en direct. Durty Cloth Tool peut aussi envoyer une map : {edit} dans le menu du vêtement."
    ),
    "info.linked": (
        "Une image ouverte depuis Durty Cloth Tool retient son vêtement et sa map, aussi dans le fichier .blend "
        "enregistré, pour que son aperçu en direct aille toujours à ce vêtement. Supprimez le lien sous Aperçu en "
        "direct pour l'utiliser avec le vêtement sélectionné dans Durty Cloth Tool."
    ),
    "info.checks": (
        "Durty Cloth Tool vérifie l'image selon les besoins de GTA V et du vêtement, comme sa liste d'erreurs. "
        "Corrigez les erreurs avant d'enregistrer ; les avertissements et remarques sont des conseils."
    ),
    "info.privacy": (
        "Reste sur cet ordinateur : vos images, vos modèles et les pixels de l'aperçu en direct. Ils ne vont qu'à "
        "Durty Cloth Tool. Va à gta.clothing : votre connexion au compte (avec le nom de cet ordinateur, sauf si "
        "vous le désactivez), une confirmation par connexion, votre déconnexion et les vérifications de mise à jour "
        "de Blender."
    ),
    "op.connect": "Connecter",
    "op.connect.desc": "Se connecter à Durty Cloth Tool sur cet ordinateur",
    "op.disconnect": "Déconnecter",
    "op.disconnect.desc": "Se déconnecter de Durty Cloth Tool. Un aperçu en direct en cours s'arrête",
    "op.sign-in": "Se connecter",
    "op.sign-in.desc": (
        "Se connecter avec votre compte gta.clothing (Discord). Durty Cloth Tool vous demande de l'approuver ; s'il "
        "n'est pas lancé, vous recevez un code pour votre navigateur"
    ),
    "op.sign-in-browser": "Se connecter dans le navigateur",
    "op.sign-in-browser.desc": (
        "Se connecter avec votre compte gta.clothing (Discord) sur la page gta.clothing dans votre navigateur"
    ),
    "op.open-sign-in": "Ouvrir la page de connexion",
    "op.open-sign-in.desc": "Ouvrir la page gta.clothing qui approuve cette connexion",
    "op.copy-code": "Copier le code",
    "op.copy-code.desc": "Copier le code de connexion dans le presse-papiers",
    "op.cancel-sign-in": "Annuler",
    "op.cancel-sign-in.desc": "Ne plus attendre la connexion",
    "op.sign-out": "Se déconnecter",
    "op.sign-out.desc": "Déconnecter ce module de gta.clothing et couper la connexion",
    "op.update-page": "Obtenir la mise à jour",
    "op.update-page.desc": "Ouvrir la page des versions actuelles de Durty Cloth Tool et de ses plugins",
    "op.open-map": "Ouvrir la map",
    "op.open-map.desc": (
        "Ouvrir cette map du vêtement depuis votre projet comme image liée au vêtement et lancer son aperçu en direct"
    ),
    "op.unlink": "Supprimer le lien",
    "op.unlink.desc": (
        "Ne plus lier cette image à son vêtement, pour qu'elle suive votre sélection dans Durty Cloth Tool"
    ),
    "op.use-paint-image": "Utiliser l'image peinte",
    "op.use-paint-image.desc": "Utiliser l'image sur laquelle vous peignez, ou celle de l'Image Editor",
    "op.live-start": "Lancer l'aperçu en direct",
    "op.live-start.desc": (
        "Afficher cette image sur le vêtement lié et la mettre à jour après chaque coup de pinceau. Rien n'est "
        "enregistré tant que vous n'enregistrez pas"
    ),
    "op.live-stop": "Arrêter l'aperçu en direct",
    "op.live-stop.desc": (
        "Arrêter d'envoyer l'image. Les modifications restent sur le ped jusqu'à ce que vous les abandonniez ou que "
        "Durty Cloth Tool les abandonne"
    ),
    "op.live-pause": "Pause",
    "op.live-pause.desc": "Ne plus envoyer de modifications pour l'instant. Le ped garde la dernière mise à jour",
    "op.live-resume": "Reprendre",
    "op.live-resume.desc": "Envoyer de nouveau les modifications, à commencer par tout ce qui a changé pendant la pause",
    "op.live-send": "Envoyer maintenant",
    "op.live-send.desc": (
        "Renvoyer l'image maintenant, pour les modifications faites par des scripts, un baking ou un rechargement"
    ),
    "op.live-save": "Enregistrer dans le vêtement",
    "op.live-save.desc": (
        "Remplacer la map du vêtement lié par cette image dans votre projet. Vous pouvez l'annuler dans "
        "l'Historique"
    ),
    "op.live-save-variation": "Enregistrer comme nouvelle variante",
    "op.live-save-variation.desc": (
        "Ajouter cette image au vêtement lié comme nouvelle variante de texture (Diffuse (couleur) seulement)"
    ),
    "op.live-discard": "Abandonner les modifications",
    "op.live-discard.desc": (
        "Retirer les modifications affichées sur le ped et arrêter. Votre projet garde sa texture enregistrée"
    ),
    "op.check-again": "Vérifier de nouveau",
    "op.check-again.desc": "Demander à Durty Cloth Tool de vérifier de nouveau l'image",
    "op.model-push": "Envoyer le modèle",
    "op.model-push.desc": (
        "Exporter le Drawable Dictionary Sollumz sélectionné et l'afficher sur le vêtement lié. Rien n'est "
        "enregistré tant que vous n'enregistrez pas"
    ),
    "op.model-save": "Enregistrer le modèle dans le vêtement",
    "op.model-save.desc": (
        "Enregistrer le modèle envoyé dans votre projet. Le modèle précédent reste dans l'Historique du vêtement"
    ),
    "op.model-discard": "Abandonner",
    "op.model-discard.desc": "Retirer le modèle envoyé du ped. Votre projet garde son modèle enregistré",
    "op.diagnostics": "Copier le diagnostic",
    "op.diagnostics.desc": (
        "Copier les versions et codes d'état pour l'assistance (aucun chemin de fichier ni donnée de connexion)"
    ),
    "op.help": "Aide",
    "op.help.desc": "Ouvrir la documentation de Durty Cloth Tool",
    "op.community": "Pleb Masters Community Discord",
    "op.community.desc": "Ouvrir le serveur Pleb Masters Community Discord, où vous pouvez demander de l'aide",
    "op.info": "Plus d'informations",
    "op.about": "À propos",
    "op.about.desc": "La version du module, sa licence et ce qu'il envoie, et où",
    "about.title": "Durty Cloth Tool Link {version} ({channel})",
    "op.join-discord": "Rejoindre le serveur Discord",
    "op.join-discord.desc": "Ouvrir l'invitation au serveur Pleb Masters Community Discord dans votre navigateur",
    "prop.image": "Image",
    "prop.image.desc": "L'image à afficher sur le vêtement lié",
    "prop.map": "Map",
    "prop.map.desc": "Quelle map du vêtement lié l'image remplace dans l'aperçu",
    "prop.auto-push": "Envoyer automatiquement",
    "prop.auto-push.desc": (
        "Renvoyer le modèle peu après que vous arrêtez de le modifier (après le premier envoi)"
    ),
    "prop.auto-connect": "Connecter automatiquement",
    "prop.auto-connect.desc": "Chercher Durty Cloth Tool sur cet ordinateur au démarrage de Blender",
    "prop.device-name": "Afficher le nom de cet ordinateur à la connexion",
    "prop.device-name.desc": (
        "Envoyer le nom de cet ordinateur avec une connexion, pour que la page d'approbation de gta.clothing montre "
        "quel ordinateur la demande"
    ),
    "prop.delay": "Délai d'envoi automatique",
    "prop.delay.desc": (
        "Secondes pendant lesquelles un modèle envoyé doit rester inchangé avant qu'Envoyer automatiquement le "
        "renvoie"
    ),
    "notice.signed-in": "Connecté en tant que {name}.",
    "notice.signing-out": "Déconnexion…",
    "notice.signed-out": "Déconnecté.",
    "notice.signed-out-local": (
        "Déconnecté sur cet ordinateur. Autorisez l'accès en ligne dans les préférences de Blender pour mettre aussi "
        "fin à la session sur gta.clothing."
    ),
    "notice.signed-out-unreached": (
        "Déconnecté sur cet ordinateur ; gta.clothing n'a pas pu être joint. La session y prend fin d'elle-même, ou "
        "terminez-la sur la page de votre compte."
    ),
    "notice.browser-opens": "Votre navigateur ouvre la page de connexion dans un instant.",
    "notice.no-sign-in": "Aucune connexion n'est en attente.",
    "notice.not-gta-clothing": "Le lien de connexion n'est pas un lien gta.clothing.",
    "notice.unexpected": "Le module a rencontré un problème inattendu : {detail}",
    "notice.secrets-unreadable": "La connexion enregistrée n'a pas pu être lue ({detail}). Connectez-vous à nouveau.",
    "notice.secret-store": "La connexion protégée n'a pas pu être lue ou écrite. Connectez-vous à nouveau.",
    "notice.file-error": "Un fichier n'a pas pu être lu ou écrit : {detail}",
    "notice.not-ready": "Le module n'est pas prêt.",
    "notice.connect-first": "Connectez-vous d'abord à Durty Cloth Tool.",
    "notice.select-cloth": "Sélectionnez d'abord un vêtement dans Durty Cloth Tool.",
    "notice.start-live-first": "Lancez d'abord l'aperçu en direct.",
    "notice.wait-saving": "Attendez la fin de l'enregistrement.",
    "notice.diffuse-only": "Seule la Diffuse (couleur) peut devenir une nouvelle variante.",
    "notice.pushing": "Un envoi est en cours.",
    "notice.online-off": "L'accès en ligne de Blender est désactivé.",
    "error.generic": "Une erreur s'est produite.",
    "error.generic-code": "Une erreur s'est produite ({code}).",
    "error.malformed-message": (
        "Durty Cloth Tool et ce module ne se sont pas compris. Mettez les deux à jour, puis réessayez."
    ),
    "error.invalid-message": (
        "Durty Cloth Tool et ce module ne se sont pas compris. Mettez les deux à jour, puis réessayez."
    ),
    "error.unknown-message-type": "Durty Cloth Tool ne connaît pas cette demande. Mettez à jour Durty Cloth Tool.",
    "error.unexpected-message": "Durty Cloth Tool n'attendait pas cette demande maintenant. Réessayez.",
    "error.message-too-large": "L'image ou le modèle était trop grand pour être envoyé.",
    "error.unsupported-protocol": (
        "Ce module et Durty Cloth Tool utilisent des versions de lien différentes. Mettez les deux à jour."
    ),
    "error.plugin-too-old": "Ce module est trop ancien pour votre Durty Cloth Tool. Mettez le module à jour.",
    "error.dct-too-old": (
        "Ce Durty Cloth Tool est plus ancien que ce module. Mettez Durty Cloth Tool à jour, puis choisissez Connecter."
    ),
    "error.not-authenticated": "Connectez-vous d'abord.",
    "error.authentication-failed": "Durty Cloth Tool n'a pas accepté la connexion. Nouvel essai…",
    "error.untrusted-endpoint": (
        "Un programme qui n'est pas votre Durty Cloth Tool a répondu, donc rien n'a été envoyé. Le module continue de "
        "chercher Durty Cloth Tool."
    ),
    "error.account-mismatch": (
        "Durty Cloth Tool est connecté avec un autre compte. Déconnectez-vous ici et connectez-vous avec le compte "
        "qu'utilise Durty Cloth Tool."
    ),
    "error.dct-signed-out": (
        "Durty Cloth Tool est déconnecté. Connectez-vous dans Durty Cloth Tool ; le module se connecte tout seul."
    ),
    "error.token-invalid": "La connexion a expiré. Nouvelle connexion…",
    "error.needs-license": "Cela nécessite une licence Durty Cloth Tool.",
    "error.needs-ultimate": "Ceci est inclus dans Durty Cloth Tool Ultimate.",
    "error.no-project": "Ouvrez d'abord un projet dans Durty Cloth Tool.",
    "error.no-focused-item": "Sélectionnez d'abord un vêtement dans Durty Cloth Tool.",
    "error.binding-in-use": "Une autre application travaille déjà sur cette texture ou ce modèle.",
    "error.binding-not-found": "Le vêtement ou la texture n'existe plus dans Durty Cloth Tool.",
    "error.lease-not-found": "Durty Cloth Tool a mis fin à cet aperçu. Relancez-le.",
    "error.lease-limit": "Trop d'aperçus en direct sont ouverts. Arrêtez-en d'abord un.",
    "error.budget-exceeded": (
        "La mémoire des aperçus en direct de Durty Cloth Tool est pleine. Arrêtez un autre aperçu en direct."
    ),
    "error.frame-out-of-bounds": "La mise à jour de l'image ne tenait pas dans la texture.",
    "error.frame-size-mismatch": "L'image n'a pas pu être envoyée.",
    "error.unsupported-format": (
        "Durty Cloth Tool n'accepte pas ce format ici. Envoyez les modèles en YDD XML de Sollumz."
    ),
    "error.stale-revision": "Des pixels plus récents étaient encore en route. Enregistrez de nouveau.",
    "error.item-refused": "Durty Cloth Tool ne peut pas modifier cet élément (dummy, verrouillé ou protégé).",
    "error.game-required": (
        "Durty Cloth Tool a besoin de votre installation de GTA V pour cela. Configurez-la dans Durty Cloth Tool."
    ),
    "error.save-failed": "Durty Cloth Tool n'a pas pu enregistrer. Sa barre d'état contient les détails.",
    "error.busy": "Durty Cloth Tool est occupé. Réessayez dans un instant.",
    "error.rate-limited": "Trop de demandes. Patientez un instant et réessayez.",
    "error.connection-limit": "Trop d'applications sont connectées à Durty Cloth Tool.",
    "error.request-denied": "Durty Cloth Tool a refusé la demande.",
    "error.model-rejected": (
        "Durty Cloth Tool n'a pas pu utiliser ce modèle. Vérifiez-le dans Sollumz et envoyez de nouveau."
    ),
    "error.internal-error": (
        "Une erreur s'est produite. Réessayez, et redémarrez Blender et Durty Cloth Tool si cela se reproduit."
    ),
    "error.disconnected": "La connexion à Durty Cloth Tool a été perdue.",
    "error.timeout": "Durty Cloth Tool n'a pas répondu à temps.",
    "error.superseded": "Une demande plus récente a remplacé celle-ci.",
    "error.cancelled": "Annulé.",
    "error.closed": "L'aperçu en direct est fermé.",
    "error.signed-out": "Vous êtes déconnecté. Connectez-vous pour utiliser de nouveau Creator Link.",
    "error.assertion-invalid": "La connexion n'a pas pu être confirmée. Nouvel essai…",
    "error.pixel-source-failed": "L'image n'a pas pu être lue pour l'aperçu en direct. Nouvel essai…",
    "error.callback-failed": "Une erreur s'est produite dans le module. Réessayez.",
    "error.offline": (
        "L'accès en ligne de Blender est désactivé. Autorisez-le dans Préférences > Système > Réseau pour vous "
        "connecter."
    ),
    "error.network": "gta.clothing n'a pas pu être joint. Vérifiez la connexion Internet.",
    "error.invalid-response": "gta.clothing a envoyé une réponse inattendue. Réessayez plus tard.",
    "error.tls": (
        "La connexion sécurisée à gta.clothing a échoué. Vérifiez votre réseau, votre proxy ou votre antivirus."
    ),
    "error.account_locked": "Votre compte gta.clothing est verrouillé.",
    "error.discord_membership_required": (
        "Creator Link exige que votre compte Discord soit membre du serveur Pleb Masters Community Discord."
    ),
    "error.discord_unavailable": "La connexion Discord est indisponible pour le moment. Réessayez plus tard.",
    "error.plugin_update_required": (
        "gta.clothing exige une version plus récente de ce module. Mettez-le à jour."
    ),
    "error.expired_token": "Le code de connexion a expiré. Connectez-vous de nouveau.",
    "error.access_denied": "La connexion a été refusée.",
    "error.invalid_grant": "La connexion n'a pas été acceptée. Connectez-vous de nouveau.",
    "error.session_invalid": "La connexion n'est plus valide. Connectez-vous de nouveau.",
    "error.session_expired": "La connexion a expiré. Connectez-vous de nouveau.",
    "error.session_revoked": "La connexion a été terminée sur gta.clothing. Connectez-vous de nouveau.",
    "error.refresh_in_progress": (
        "Un autre programme renouvelle votre connexion. Réessayez dans un instant."
    ),
    "close.closed": "Aperçu en direct arrêté.",
    "close.replaced": "Une autre application a repris cette texture.",
    "close.itemRemoved": "Le vêtement a été supprimé dans Durty Cloth Tool.",
    "close.projectClosed": "Le projet a été fermé dans Durty Cloth Tool.",
    "close.entitlementLost": "Votre offre n'inclut plus cette fonction.",
    "close.signedOut": "Durty Cloth Tool s'est déconnecté, l'aperçu a donc pris fin.",
    "close.disconnected": "La connexion à Durty Cloth Tool a été perdue.",
    "feature.needsLicense": "Cela nécessite une licence Durty Cloth Tool.",
    "feature.needsUltimate": "Ceci est inclus dans Durty Cloth Tool Ultimate.",
    "feature.unavailable": "Ceci n'est pas inclus dans votre offre Durty Cloth Tool.",
}
