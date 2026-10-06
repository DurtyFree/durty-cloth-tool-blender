# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2026 Schmid Software Solutions (https://schmid-software.de)
"""French (Français): the garment fitting texts."""

TEXT = {
    "garment.panel": "Ajustement de vêtements",
    "garment.panel.setup": "Configuration",
    "garment.panel.fit": "Ajustement",
    "garment.panel.fix": "Correction",
    "garment.panel.ready": "Prêt pour le jeu",
    "garment.panel.add": "Ajouter au projet",
    "experimental.note": "Expérimental : vérifiez chaque résultat avant de l'utiliser.",
    "garment.status.no-garment": "Aucun vêtement",
    "garment.status.no-body": "Pas encore de corps",
    "garment.status.setup": "{type} · {gender}",
    "garment.status.markers": "{count} marqueurs sur {total}",
    "garment.status.aligned": "Aligné",
    "garment.status.fitted": "Ajusté",
    "garment.status.snapped": "Posé",
    "garment.status.not-snapped": "Non posé",
    "garment.status.inside": "{count} dans le corps",
    "garment.status.blocking": "Problèmes à corriger",
    "garment.status.validated": "Validé",
    "garment.status.not-validated": "Non validé",
    "garment.status.added": "Ajouté",
    "garment.status.adding": "Ajout en cours",
    "garment.status.not-added": "Non ajouté",
    "garment.next.import": "Importez un vêtement, ou sélectionnez le vôtre et choisissez Utiliser la sélection.",
    "garment.next.body": "Ensuite : ajoutez le corps freemode sous Configuration.",
    "garment.next.markers": (
        "Ensuite : placez les marqueurs avec Marqueurs automatiques sous Ajustement, puis vérifiez leur position."
    ),
    "garment.next.check": "Ensuite : lancez le contrôle de l'ajustement sous Correction.",
    "garment.next.push": (
        "Ensuite : des parties du vêtement sont dans le corps. Utilisez Pousser hors du corps sous Correction."
    ),
    "garment.next.prepare": "Ensuite : Préparer le vêtement sous Prêt pour le jeu.",
    "garment.next.combine": (
        "Ensuite : Combiner les matériaux sous Prêt pour le jeu, pour que le vêtement utilise une seule texture."
    ),
    "garment.next.lods": "Ensuite : Générer les LOD sous Prêt pour le jeu.",
    "garment.next.validate": "Ensuite : Valider sous Prêt pour le jeu.",
    "garment.next.sculpting": (
        "Sculpture : faites glisser avec la brosse Grab, puis choisissez Accepter ou Annuler sous Correction."
    ),
    "garment.gender.male.desc": "Le ped freemode masculin (mp_m_freemode_01)",
    "garment.gender.female.desc": "Le ped freemode féminin (mp_f_freemode_01)",
    "garment.slot.jbib": "Haut (jbib)",
    "garment.slot.jbib.desc": "Vestes et hauts",
    "garment.slot.accs": "Maillot (accs)",
    "garment.slot.accs.desc": "Maillots, portés sous un haut",
    "garment.slot.lowr": "Jambes (lowr)",
    "garment.slot.lowr.desc": "Pantalons, shorts et jupes",
    "garment.slot.feet": "Chaussures (feet)",
    "garment.slot.feet.desc": "Chaussures, bottes et sandales",
    "garment.category.vest": "Débardeur",
    "garment.category.vest.desc": "Un haut sans manches",
    "garment.category.tshirt": "T-shirt",
    "garment.category.tshirt.desc": "Un haut à manches courtes",
    "garment.category.long_sleeve": "Manches longues",
    "garment.category.long_sleeve.desc": "Un haut avec des manches jusqu'aux poignets",
    "garment.category.long_jacket": "Veste longue ou tunique",
    "garment.category.long_jacket.desc": "Un haut à manches longues qui descend sous les hanches",
    "garment.category.pants": "Pantalon",
    "garment.category.pants.desc": "Un pantalon qui descend jusqu'aux chevilles",
    "garment.category.shorts": "Short",
    "garment.category.shorts.desc": "Un pantalon qui s'arrête aux genoux ou au-dessus",
    "garment.category.shoes": "Chaussures",
    "garment.category.shoes.desc": "Chaussures et bottes",
    "garment.pose.a_pose": "A-pose",
    "garment.pose.a_pose.desc": "Les bras pointent vers le bas en biais, comme le ped se tient dans le jeu",
    "garment.pose.t_pose": "T-pose",
    "garment.pose.t_pose.desc": "Les bras pointent droit sur les côtés",
    "garment.pose.custom": "Personnalisée",
    "garment.pose.custom.desc": (
        "Une autre pose : vérifiez les marqueurs et déplacez-les à la main sur les articulations"
    ),
    "garment.region.shoulders": "Épaules",
    "garment.region.upper_arms": "Haut des bras",
    "garment.region.chest": "Poitrine",
    "garment.region.back": "Dos",
    "garment.region.waist": "Taille",
    "garment.region.hips": "Hanches",
    "garment.region.neck": "Cou",
    "garment.region.legs": "Jambes",
    "garment.region.desc": "Une partie du vêtement, trouvée à partir des marqueurs",
    "garment.level.high": "Haut",
    "garment.level.medium": "Moyen",
    "garment.level.low": "Bas",
    "garment.prop.garment": "Vêtement",
    "garment.prop.garment.desc": "Le vêtement sur lequel travaillent les outils. Seul cet objet est modifié",
    "garment.prop.body": "Corps",
    "garment.prop.body.desc": "Le corps freemode par rapport auquel le vêtement est mesuré",
    "garment.prop.gender": "Genre",
    "garment.prop.gender.desc": "Le ped freemode auquel le vêtement est destiné",
    "garment.prop.slot": "Emplacement",
    "garment.prop.slot.desc": "L'emplacement de vêtement qu'occupe le vêtement dans Durty Cloth Tool",
    "garment.prop.category": "Type de vêtement",
    "garment.prop.category.desc": (
        "Le genre de vêtement : il fixe l'emplacement, la façon de trouver les marqueurs, les zones proposées par les "
        "outils et ce qui est vérifié"
    ),
    "garment.prop.pose": "Pose d'origine",
    "garment.prop.pose.desc": "La pose de l'avatar sur lequel le vêtement a été créé",
    "garment.prop.marker-size": "Taille des marqueurs",
    "garment.prop.marker-size.desc": "La taille à laquelle les sphères des marqueurs sont affichées",
    "garment.prop.arm-angle": "Angle des bras",
    "garment.prop.arm-angle.desc": (
        "De combien T-pose vers A-pose baisse les bras sous l'horizontale quand les articulations du corps sont "
        "inconnues (avec elles, les bras vont sur ceux du corps)"
    ),
    "garment.prop.gap": "Écart (mm)",
    "garment.prop.push-gap.desc": (
        "La distance hors du corps à laquelle Pousser hors du corps place le vêtement, en millimètres"
    ),
    "garment.prop.snug-gap.desc": "La distance au corps à laquelle Plaquer au corps laisse la zone, en millimètres",
    "garment.prop.region": "Zone",
    "garment.prop.region.desc": (
        "La partie du vêtement sur laquelle travaillent Plaquer au corps et Détendre les parties étirées"
    ),
    "garment.prop.amount": "Intensité",
    "garment.prop.amount.desc": "La part du trajet que parcourt la zone : 1 la déplace jusqu'au bout",
    "garment.prop.radius": "Rayon (cm)",
    "garment.prop.radius.desc": "La taille de la brosse Grab, en centimètres",
    "garment.prop.strength": "Force",
    "garment.prop.strength.desc": "La force avec laquelle la brosse Grab déplace le vêtement",
    "garment.prop.mirror": "Miroir X",
    "garment.prop.mirror.desc": "Sculpter les deux côtés du vêtement à la fois",
    "garment.prop.keep-out": "Garder hors du corps",
    "garment.prop.keep-out.desc": (
        "Quand vous acceptez, ressortir ce que vous avez poussé dans le corps, jusqu'à l'écart de Pousser hors du "
        "corps"
    ),
    "garment.prop.weld": "Distance de soudure (mm)",
    "garment.prop.weld.desc": (
        "Les bords de panneaux plus proches que cette distance, en millimètres, sont joints en une seule couture"
    ),
    "garment.prop.colour-1": "Color 1",
    "garment.prop.colour-1.desc": (
        "La première couleur de sommet du shader de ped (Color 1 de Sollumz) : la lumière que reçoit le vêtement. "
        "#FF8000 convient à la plupart des vêtements ; #FFBAFF fait briller les matériaux émissifs"
    ),
    "garment.prop.colour-2": "Color 2",
    "garment.prop.colour-2.desc": (
        "La deuxième couleur de sommet du shader de ped (Color 2 de Sollumz) : le vent et la sueur. Le noir sans "
        "alpha désactive les deux"
    ),
    "garment.prop.overwrite": "Remplacer les couleurs de sommets existantes",
    "garment.prop.overwrite.desc": "Remplacer aussi Color 1 et Color 2 quand le vêtement les a déjà",
    "garment.prop.size": "Taille de la texture",
    "garment.size.desc": (
        "La taille de la texture combinée en pixels. Les vérifications de texture de Durty Cloth Tool conseillent "
        "2048 ou moins"
    ),
    "garment.prop.cut": "Couper les longues bandes",
    "garment.prop.cut.desc": (
        "Couper en morceaux les îlots UV longs et fins, comme les ourlets et les ceintures, pour que le reste du "
        "vêtement reçoive une plus grande part de la texture"
    ),
    "garment.prop.lod-medium": "Triangles (Moyen)",
    "garment.prop.lod-low": "Triangles (Bas)",
    "garment.prop.lod.desc": (
        "Le nombre maximal de triangles que garde ce niveau de détail. 0 : une part de High, au plus ce que conseille "
        "Durty Cloth Tool (15 000 pour Medium, 7 500 pour Low)"
    ),
    "garment.prop.ground": "Avatar debout au sol",
    "garment.prop.ground.desc": (
        "Le vêtement a été créé sur un avatar debout à la hauteur 0, comme dans Marvelous Designer : le descendre "
        "jusqu'au ped, dont les semelles sont 1 m sous son origine"
    ),
    "garment.prop.preset-name": "Nom",
    "garment.heading.markers": "Marqueurs",
    "garment.heading.tpose": "Modèle en T-pose",
    "garment.heading.backups": "Sauvegardes",
    "garment.heading.regions": "Outils de zone",
    "garment.heading.problems": "Problèmes",
    "garment.heading.sculpt": "Correction à la main",
    "garment.heading.tears": "Déchirures",
    "garment.op.use": "Utiliser la sélection",
    "garment.op.use.desc": "Travailler sur l'objet maillage sélectionné",
    "garment.op.import": "Importer un vêtement",
    "garment.op.import.desc": (
        "Importer un vêtement depuis un fichier FBX, OBJ ou glTF (par exemple de Marvelous Designer), en mètres et "
        "en un seul objet"
    ),
    "garment.op.add-body": "Ajouter le corps freemode",
    "garment.op.add-body.desc": (
        "Télécharger le corps freemode du genre choisi depuis gta.clothing pour votre compte (une fois par version "
        "du corps) et l'ajouter à la scène"
    ),
    "garment.op.cancel-body.desc": "Arrêter le téléchargement du corps",
    "garment.op.body-file": "Utiliser un fichier de corps",
    "garment.op.body-file.desc": (
        "Ajouter plutôt un corps depuis un fichier GLB, glTF, FBX ou OBJ, en mètres et dans la pose du jeu"
    ),
    "garment.op.auto-markers": "Marqueurs automatiques",
    "garment.op.auto-markers.desc": (
        "Placer les marqueurs d'articulation : sur les articulations de l'avatar choisi dans Configuration, d'après la "
        "forme du vêtement (hauts et pantalons), ou sur les articulations du corps pour commencer. Déplacez ceux qui "
        "sont mal placés"
    ),
    "garment.op.mirror": "Miroir G vers D",
    "garment.op.mirror.desc": "Copier les marqueurs du côté gauche du ped sur son côté droit",
    "garment.op.save-preset": "Enregistrer le préréglage de pose",
    "garment.op.save-preset.desc": (
        "Enregistrer les marqueurs comme préréglage dans le dossier du module, pour des vêtements similaires"
    ),
    "garment.op.load-preset": "Charger un préréglage de pose",
    "garment.op.load-preset.desc": "Placer les marqueurs d'après un préréglage enregistré",
    "garment.op.tpose": "T-pose vers A-pose",
    "garment.op.tpose.desc": (
        "Abaisser les bras d'un vêtement créé en T-pose jusqu'à l'angle des bras, à l'aide des marqueurs"
    ),
    "garment.op.restore": "Restaurer avant ajustement",
    "garment.op.restore.desc": "Rétablir la forme du vêtement d'avant la première étape d'ajustement",
    "garment.op.push": "Pousser hors du corps",
    "garment.op.push.desc": (
        "Déplacer jusqu'à l'écart chaque partie du vêtement qui est dans le corps, ou plus proche que l'écart"
    ),
    "garment.op.snug": "Plaquer au corps",
    "garment.op.snug.desc": "Rapprocher la zone choisie du corps, jusqu'à l'écart",
    "garment.op.relax": "Détendre les parties étirées",
    "garment.op.relax.desc": "Ramener les parties étirées de la zone choisie vers leur taille d'origine",
    "garment.op.problems": "Afficher les problèmes",
    "garment.op.problems.desc": (
        "Colorer le vêtement : rouge dans le corps, jaune trop près, violet étiré, bleu une épaule décollée. "
        "Sélectionnez de nouveau pour masquer les couleurs"
    ),
    "garment.op.refresh": "Actualiser",
    "garment.op.refresh.desc": "Colorer de nouveau les problèmes après une modification",
    "garment.op.check": "Lancer le contrôle de l'ajustement",
    "garment.op.check.desc": "Mesurer à quelle distance du corps se tient chaque zone du vêtement",
    "garment.op.sculpt": "Commencer la sculpture",
    "garment.op.sculpt.desc": (
        "Corriger la forme à la main avec la brosse Grab. Accepter garde le résultat, Annuler rétablit la forme"
    ),
    "garment.op.accept": "Accepter",
    "garment.op.accept.desc": "Garder la forme sculptée et terminer la session",
    "garment.op.cancel-sculpt.desc": "Rétablir la forme d'avant la session et terminer celle-ci",
    "garment.op.tears": "Vérifier les déchirures",
    "garment.op.tears.desc": (
        "Faire passer l'armature du vêtement par quelques poses de test et montrer où les coutures s'ouvrent"
    ),
    "garment.op.prepare": "Préparer le vêtement",
    "garment.op.prepare.desc": (
        "Joindre les coutures des panneaux, supprimer les parties isolées, trianguler, lisser l'ombrage et ajouter "
        "les couleurs de sommets du ped"
    ),
    "garment.op.combine": "Combiner les matériaux",
    "garment.op.combine.desc": (
        "Regrouper tous les îlots UV dans une disposition et cuire chaque matériau en un seul : la couleur avec sa "
        "transparence, et des normal, specular et emission maps quand il y en a"
    ),
    "garment.combine.nothing": "Rien à combiner : le vêtement n'a qu'un seul matériau.",
    "garment.op.lods": "Générer les LOD",
    "garment.op.lods.desc": (
        "Créer les niveaux de détail Moyen et Bas dans les emplacements LOD de Sollumz, avec les poids du niveau "
        "Haut"
    ),
    "garment.op.validate": "Valider",
    "garment.op.validate.desc": "Rechercher dans le vêtement les problèmes que le jeu afficherait",
    "garment.garment.facts": "{count} sommets · matériaux : {materials}",
    "garment.body.hosted": "Corps freemode : {gender}, version {version}",
    "garment.body.object": "Corps : {name}",
    "garment.body.downloading": "Téléchargement du corps freemode…",
    "garment.body.cancelled": "Le téléchargement du corps a été annulé.",
    "garment.body.offline": (
        "L'accès en ligne de Blender est désactivé et aucun corps n'a été téléchargé auparavant. Autorisez l'accès "
        "en ligne, ou utilisez un fichier de corps."
    ),
    "garment.body.network": (
        "gta.clothing n'a pas pu être joint. Vérifiez la connexion Internet, ou utilisez un fichier de corps."
    ),
    "garment.body.no-body": (
        "gta.clothing n'a pas encore de corps freemode pour ce canal. Utilisez un fichier de corps pour l'instant."
    ),
    "garment.body.signed-out": "La connexion n'est plus valide. Connectez-vous de nouveau, puis ajoutez le corps.",
    "garment.body.not-entitled": "Votre compte ne peut pas télécharger le corps freemode.",
    "garment.body.refused": "gta.clothing a refusé le téléchargement.",
    "garment.body.update": "gta.clothing exige une version plus récente de ce module pour le corps. Mettez-le à jour.",
    "garment.body.busy": "Trop de téléchargements en même temps. Patientez un instant et réessayez.",
    "garment.body.unavailable": "Le corps freemode est indisponible pour le moment. Réessayez plus tard.",
    "garment.body.invalid": "gta.clothing a envoyé autre chose qu'un corps. Réessayez plus tard.",
    "garment.body.disk": "Le corps n'a pas pu être enregistré dans le dossier du module.",
    "garment.markers.count": "Marqueurs placés : {count} sur {total}",
    "garment.presets.none": "Aucun préréglage enregistré pour l'instant",
    "garment.backups.count": "Sauvegardes conservées : {count} sur {limit}",
    "garment.problem.inside": "Dans le corps",
    "garment.problem.close": "Trop près du corps",
    "garment.problem.stretched": "Étiré",
    "garment.problem.floating": "Épaule décollée",
    "garment.check.none": (
        "Lancez le contrôle de l'ajustement pour voir à quelle distance du corps se tient chaque zone."
    ),
    "garment.check.measured": "Mesuré (mm)",
    "garment.check.value": "{p50} ({p10} à {p90})",
    "garment.check.usual-line": "Habituel : {range}",
    "garment.check.inside": "Dans le corps : {count} sommets ({share} %)",
    "garment.check.inside.one": "Dans le corps : {count} sommet ({share} %)",
    "garment.advice.shoulders": (
        "Les épaules sont décollées du corps : Plaquer au corps (Outils de zone) avec Épaules les rabaisse."
    ),
    "garment.sculpt.running": (
        "Faites glisser avec la brosse Grab pour déplacer le vêtement. Le corps s'affiche en fil de fer."
    ),
    "garment.sculpt.subtext": "Accepter garde la forme ; Annuler rétablit la forme d'avant la session.",
    "garment.pose.arms-up": "Bras levés",
    "garment.pose.arms-forward": "Bras en avant",
    "garment.pose.legs-forward": "Jambes en avant",
    "garment.pose.twist": "Torsion",
    "garment.tears.pose": "{pose} : {count} points de couture ouverts, jusqu'à {gap} mm",
    "garment.tears.pose.one": "{pose} : {count} point de couture ouvert, jusqu'à {gap} mm",
    "garment.tears.pose-clean": "{pose} : aucune couture ne s'ouvre",
    "garment.validate.clean": "CLEAN : rien à corriger.",
    "garment.finding.non-finite": "{count} points ont des coordonnées invalides.",
    "garment.finding.non-finite.one": "{count} point a des coordonnées invalides.",
    "garment.finding.no-uv": "Le vêtement n'a pas de carte UV, il ne peut donc pas afficher de texture.",
    "garment.finding.uv-outside": (
        "{count} points UV se trouvent hors du carré 0 à 1 ; le jeu y répète la texture."
    ),
    "garment.finding.uv-outside.one": "{count} point UV se trouve hors du carré 0 à 1 ; le jeu y répète la texture.",
    "garment.finding.uv-area": "La disposition UV n'utilise que {area} % de la texture.",
    "garment.finding.no-weights": (
        "Pas encore riggé : attribuez au vêtement des poids sur les os du squelette freemode."
    ),
    "garment.finding.unweighted": (
        "{count} sommets n'ont pas de poids ; le jeu les laisse sur place quand le ped bouge."
    ),
    "garment.finding.unweighted.one": (
        "{count} sommet n'a pas de poids ; le jeu le laisse sur place quand le ped bouge."
    ),
    "garment.finding.influences": (
        "{count} sommets sont déplacés par plus de {limit} os ; le jeu n'en utilise que {limit}."
    ),
    "garment.finding.influences.one": (
        "{count} sommet est déplacé par plus de {limit} os ; le jeu n'en utilise que {limit}."
    ),
    "garment.finding.colour-missing": "Color 1 est absent. Préparer le vêtement l'ajoute.",
    "garment.finding.colour-format": (
        "Color 1 n'est pas une couleur en octets sur les coins de face, comme l'exige Sollumz. Préparer le vêtement "
        "le remplace."
    ),
    "garment.finding.inside": "{share} % du vêtement est dans le corps.",
    "garment.finding.materials": (
        "Le vêtement a {count} matériaux. Combiner les matériaux en fait une seule texture."
    ),
    "garment.why.no-garment": "Importez d'abord un vêtement ou choisissez-en un sous Configuration.",
    "garment.why.not-shown": "Le vêtement n'est pas dans le view layer actuel.",
    "garment.why.sculpting": "Acceptez ou annulez d'abord la session de sculpture.",
    "garment.why.step-running": "{step} est en cours. Attendez la fin, ou appuyez sur Échap pour l'arrêter.",
    "garment.why.object-mode": "Passez d'abord en Mode Objet.",
    "garment.why.shape-keys": "Le vêtement a des clés de forme. Appliquez-les ou supprimez-les d'abord.",
    "garment.why.empty": "Le vêtement n'a pas de géométrie.",
    "garment.why.no-body": "Ajoutez d'abord le corps freemode sous Configuration.",
    "garment.why.no-markers": "Ce type de vêtement n'a pas besoin de marqueurs.",
    "garment.why.downloading": "Le corps est en cours de téléchargement.",
    "garment.why.sign-in": (
        "Connectez-vous d'abord avec gta.clothing (Se connecter), ou utilisez un fichier de corps."
    ),
    "garment.why.select-mesh": "Sélectionnez d'abord un objet maillage.",
    "garment.why.is-body": "Ceci est le corps freemode, pas un vêtement.",
    "garment.why.no-file": "Choisissez un fichier.",
    "garment.why.file-type": "Seuls les fichiers FBX, OBJ, GLB et glTF peuvent être importés.",
    "garment.why.markers": "Placez d'abord les marqueurs sous Ajustement.",
    "garment.why.preset-name": "Donnez au préréglage un nom avec des lettres ou des chiffres.",
    "garment.why.preset-unreadable": "Le préréglage n'a pas pu être lu : {detail}",
    "garment.why.tops-only": "Seuls les hauts ont des bras à abaisser.",
    "garment.why.no-backup": (
        "Il n'y a pas encore de sauvegarde. Une sauvegarde est conservée avant chaque étape qui modifie le "
        "vêtement."
    ),
    "garment.why.region-category": "Cette zone ne fait pas partie du type de vêtement choisi.",
    "garment.why.region-empty": "Le vêtement n'a rien dans la zone {region}.",
    "garment.why.no-session": "Aucune session de sculpture n'est en cours.",
    "garment.why.no-armature": "Vérifier les déchirures nécessite une armature et des poids sur le vêtement.",
    "garment.why.no-weights": "Le vêtement n'a pas de poids avec lesquels le poser.",
    "garment.why.modifiers": (
        "Un modificateur change la géométrie du vêtement. Les déchirures ne peuvent être vérifiées que sans lui."
    ),
    "garment.why.no-uv": "Le vêtement n'a pas de carte UV.",
    "garment.why.empty-slot": "Chaque emplacement de matériau du vêtement a besoin d'un matériau.",
    "garment.why.uv-full": "Le vêtement a autant de cartes UV que Blender le permet. Supprimez-en d'abord une.",
    "garment.why.no-sollumz": "Générer les LOD nécessite Sollumz.",
    "garment.why.show-high": "Affichez d'abord le niveau de détail Haut dans Sollumz.",
    "garment.why.no-download": "Aucun corps n'est en cours de téléchargement.",
    "garment.error.import": "Le fichier n'a pas pu être importé : {detail}",
    "garment.error.no-mesh": "Le fichier ne contient aucun maillage.",
    "garment.error.mode": "Le Mode Sculpture n'a pas pu être lancé : {detail}",
    "garment.error.bake": "Le baking a échoué : {detail}",
    "garment.marker-error.no-markers": "Ce type de vêtement n'a pas besoin de marqueurs.",
    "garment.marker-error.too-small": (
        "Le vêtement est trop petit ou trop plat pour des marqueurs. Vérifiez qu'il est en mètres."
    ),
    "garment.marker-error.not-a-top": (
        "Le vêtement ne ressemble pas à un haut. Vérifiez le type de vêtement, ou placez les marqueurs à la main."
    ),
    "garment.marker-error.no-sleeves": (
        "Aucune manche n'a été trouvée. Choisissez Débardeur, ou placez les marqueurs des bras à la main."
    ),
    "garment.marker-error.not-legs": (
        "Aucune jambe de pantalon n'a été trouvée. Vérifiez le type de vêtement, ou placez les marqueurs à la main."
    ),
    "garment.done.use": "Vous travaillez maintenant sur {name}.",
    "garment.done.import": "{name} importé ({count} sommets).",
    "garment.done.body": "Corps freemode ajouté ({gender}, version {version}).",
    "garment.done.body-file": "{name} ajouté comme corps.",
    "garment.done.markers": "{count} marqueurs placés. Déplacez ceux qui sont mal placés avant l'ajustement.",
    "garment.done.markers.one": "{count} marqueur placé. Déplacez-le avant l'ajustement s'il est mal placé.",
    "garment.done.mirror": "Marqueurs de gauche reproduits en miroir à droite.",
    "garment.done.preset-saved": "Préréglage de pose {name} enregistré.",
    "garment.done.preset-loaded": "Préréglage de pose {name} chargé.",
    "garment.done.tpose": "Bras abaissés de {angle}°. Une sauvegarde a été conservée.",
    "garment.done.tpose-none": "Les bras sont déjà à l'angle des bras.",
    "garment.done.restore": "Forme d'avant la première étape d'ajustement rétablie.",
    "garment.done.push": "{moved} sommets déplacés. Dans le corps : {before} avant, {after} maintenant.",
    "garment.done.snug": (
        "{moved} sommets de la zone {region} rapprochés du corps ({mean} mm en moyenne)."
    ),
    "garment.done.relax": "{moved} sommets de la zone {region} détendus.",
    "garment.done.relax-smooth": (
        "{moved} sommets de la zone {region} lissés (la forme d'avant l'ajustement n'est pas disponible pour la "
        "comparaison)."
    ),
    "garment.done.problems": (
        "Dans le corps : {inside}, trop près : {close}, étirés : {stretched}, décollés : {floating}."
    ),
    "garment.done.check": "Contrôle de l'ajustement terminé. Dans le corps : {count} sommets.",
    "garment.done.check.one": "Contrôle de l'ajustement terminé. Dans le corps : {count} sommet.",
    "garment.done.sculpt-start": "Session de sculpture lancée.",
    "garment.done.accept": (
        "Forme sculptée conservée : {moved} sommets déplacés. Dans le corps : {before} avant, {after} maintenant."
    ),
    "garment.done.cancel-sculpt": "Sculpture annulée : le vêtement a retrouvé sa forme d'avant la session.",
    "garment.done.tears": (
        "{count} sommets de couture s'ouvrent dans une pose de test. Ils sont dans le groupe de sommets DCT Tears."
    ),
    "garment.done.tears.one": (
        "{count} sommet de couture s'ouvre dans une pose de test. Il est dans le groupe de sommets DCT Tears."
    ),
    "garment.done.no-tears": "Aucune couture ne s'ouvre dans les poses de test.",
    "garment.done.tears-welded": (
        "Les coutures sont jointes, aucune ne peut donc s'ouvrir ici. Vérifiez le vêtement en mouvement sur le ped "
        "dans l'aperçu 3D de Durty Cloth Tool."
    ),
    "garment.done.prepare": (
        "Préparé : {welded} sommets de couture joints, {removed} sommets isolés supprimés, {triangles} triangles."
    ),
    "garment.done.prepare-lining": (
        "Préparé : {welded} sommets de couture joints (une doublure a été trouvée et gardée à part), {removed} "
        "sommets isolés supprimés, {triangles} triangles."
    ),
    "garment.done.combine": (
        "{count} matériaux combinés en une texture de {size} pixels, {density} pixels par centimètre sur le vêtement "
        "(la disposition en utilise {used} %, {cut} bandes coupées)."
    ),
    "garment.done.lods": "Niveaux de détail : Haut {high}, Moyen {medium}, Bas {low} triangles.",
    "garment.done.clean": "Valider : CLEAN.",
    "garment.done.findings": "Valider a relevé des points à examiner : {count}.",
    "garment.info.pose": (
        "Choisissez la pose de l'avatar sur lequel le vêtement a été créé. Un vêtement créé en T-pose peut être "
        "amené dans l'A-pose du jeu sous Ajustement."
    ),
    "garment.info.garment": (
        "Les outils ne modifient que cet objet. Importer un vêtement convertit les centimètres et les millimètres "
        "(tels que Marvelous Designer les exporte) en mètres. Chaque étape qui modifie le vêtement conserve une "
        "sauvegarde, et Ctrl+Z l'annule."
    ),
    "garment.info.body": (
        "Le corps freemode est téléchargé depuis gta.clothing une fois par version et conservé dans le dossier du "
        "module. Il est ajouté à la scène comme objet à part, et les outils ne le modifient jamais."
    ),
    "garment.info.markers": (
        "Les marqueurs représentent les articulations du ped : cou, poitrine, bassin, épaules, coudes, poignets et "
        "hanches (pour un pantalon les hanches, genoux et chevilles, pour un masque la tête). Marqueurs automatiques "
        "les place sur les articulations de l'avatar choisi dans Configuration, sinon les lit d'après la forme du "
        "vêtement (hauts et pantalons) ou les place d'abord sur les articulations du corps. Des lignes les relient "
        "dans la vue 3D : des lignes orange signalent un problème. Déplacez les marqueurs mal placés ; Miroir G vers D "
        "copie le côté gauche sur le côté droit."
    ),
    "garment.info.tpose": (
        "Tourne les bras d'un vêtement fait en T-pose jusqu'à l'angle des bras (ou sur les bras du corps quand ses "
        "articulations sont connues). Chaque partie du vêtement suit selon sa position, donc les coutures restent "
        "fermées. Aligner sur le corps le fait aussi."
    ),
    "garment.info.backups": (
        "Avant chaque étape qui modifie le vêtement, une copie de son maillage est conservée dans le fichier .blend "
        "(la première et les plus récentes). Revenir d'une étape rétablit la plus récente, Restaurer avant ajustement "
        "la première. Elles partent avec le vêtement quand il est supprimé ou ajouté à Durty Cloth Tool."
    ),
    "garment.info.push": (
        "Déplace tout ce qui est dans le corps, ou plus proche que l'écart, jusqu'à l'écart à l'extérieur. Les sommets "
        "autour suivent, pour qu'aucun pli ne se forme, et les couches au-dessus (un tissu extérieur sur sa doublure) "
        "suivent aussi. Les parties à plus de 3 cm à l'intérieur, les sommets du groupe DCT Pinned et les sommets "
        "masqués restent en place."
    ),
    "garment.info.regions": (
        "Plaquer au corps rapproche une région lâche du corps, jusqu'à l'écart ; les pans de manteau, jupes et "
        "capuches qui pendent librement restent tels quels. Détendre les parties étirées ramène les parties étirées "
        "vers leur taille d'origine. Les bords de la région se fondent."
    ),
    "garment.info.problems": (
        "Colore le vêtement pendant que vous travaillez : rouge dans le corps, jaune trop près, violet étiré par "
        "rapport à sa forme d'origine, bleu une épaule décollée du corps."
    ),
    "garment.info.check": (
        "Mesure à quelle distance du corps se tient chaque zone du vêtement : la valeur médiane et la plage de la "
        "plupart de ses sommets, en millimètres. Les valeurs négatives sont dans le corps."
    ),
    "garment.info.sculpt": (
        "Le Mode Sculpture avec la brosse Grab, le corps en fil de fer. Accepter garde la forme (et ressort ce qui "
        "est entré dans le corps quand Garder hors du corps est activé) ; Annuler rétablit la forme d'avant."
    ),
    "garment.info.tears": (
        "Nécessite une armature et des poids sur le vêtement. Le vêtement passe par quelques poses de test (bras "
        "levés, bras en avant, jambes en avant, une torsion), et les coutures qui s'ouvrent sont signalées."
    ),
    "garment.info.prepare": (
        "Joint les coutures entre les pièces (jamais un ourlet sur lui-même, et jamais une doublure sur son tissu "
        "extérieur : mettez une doublure non trouvée dans le groupe de sommets DCT Lining), supprime les parties "
        "libres, triangule, lisse l'ombrage et donne au vêtement les couleurs de sommet Color 1 et Color 2 de Sollumz "
        "avec les valeurs sous Options."
    ),
    "garment.info.combine": (
        "Regroupe tous les îlots UV dans un carré et cuit chaque matériau en un seul : la couleur avec sa "
        "transparence, et une normal, specular et emission map quand un matériau en a une. Cela devient le seul "
        "matériau du vêtement. La carte UV d'origine est conservée sous le nom DCT Source UV."
    ),
    "garment.info.lods": (
        "Réduit une copie du vêtement à chaque budget de triangles et la place dans les emplacements LOD Medium et Low "
        "de Sollumz, en gardant autant que possible les bords ouverts et les coutures UV. Chaque niveau reprend les "
        "poids de High (quatre os par sommet) et est poussé hors du corps."
    ),
    "garment.info.validate": (
        "Contrôles locaux rapides : poids, plus de quatre os par sommet, coordonnées cassées, position du vêtement, "
        "normales inversées, disposition UV, couleurs de sommet, triangles de chaque niveau de détail et quantité dans "
        "le corps."
    ),
    # ---- adding to Durty Cloth Tool ----
    "error.item-limit": (
        "Le projet contient autant de vêtements que la version gratuite de Durty Cloth Tool le permet."
    ),
    "garment.next.done": (
        "Terminé : le vêtement est dans votre projet Durty Cloth Tool. Envoyer le modèle et Enregistrer le modèle "
        "dans le vêtement, sous Vêtement lié, le mettent à jour (inclus dans Durty Cloth Tool Ultimate)."
    ),
    "garment.next.validate-problems": (
        "Ensuite : corrigez ce que Valider signale sous Prêt pour le jeu, puis validez de nouveau."
    ),
    "garment.next.adding": (
        "Ajout en cours : Durty Cloth Tool affiche le vêtement. Choisissez Ajouter au projet ou Annuler là-bas."
    ),
    "garment.next.connect": "Ensuite : connectez-vous à Durty Cloth Tool pour ajouter le vêtement à un projet.",
    "garment.next.project": "Ensuite : ouvrez un projet dans Durty Cloth Tool, puis choisissez Ajouter au projet.",
    "garment.next.sollumz": "Ensuite : installez Sollumz pour ajouter le vêtement à Durty Cloth Tool.",
    "garment.next.skeleton": (
        "Ensuite : Utiliser le squelette Durty Cloth Tool sous Prêt pour le jeu, ou Ajouter au projet, qui le fait "
        "aussi."
    ),
    "garment.next.add-skeleton": (
        "Ensuite : Ajouter au projet place le vêtement sur le squelette Durty Cloth Tool et dans votre projet."
    ),
    "garment.next.add": "Ensuite : Ajouter au projet place le vêtement dans votre projet Durty Cloth Tool.",
    "add.heading.variations": "Variantes de couleur",
    "add.target": "Il sera ajouté comme {slot}, {gender}. Modifiez les deux sous Configuration.",
    "add.variation.none": "Pas encore de texture de couleur",
    "add.variations.subtext": "Variantes : {count} sur {limit} au maximum.",
    "add.prop.name": "Nom du vêtement",
    "add.prop.name.desc": "Le nom que reçoit le vêtement dans Durty Cloth Tool. Vide : son nom dans Blender",
    "add.prop.skin": "Peau visible",
    "add.prop.skin.desc": (
        "Le vêtement laisse voir une partie de la peau du ped, le jeu le colore donc avec le teint de peau du ped "
        "(la variante _r)"
    ),
    "add.prop.image": "Image de la variante",
    "add.prop.image.desc": (
        "La texture de couleur de cette variante, dans la disposition de la propre texture du vêtement"
    ),
    "add.prop.variation-name": "Nom de la variante",
    "add.prop.variation-name.desc": (
        "Le nom de cette variante de couleur dans Durty Cloth Tool. Vide : le nom de l'image"
    ),
    "add.prop.first-name.desc": (
        "Le nom de la première variante de couleur (la propre texture du vêtement) dans Durty Cloth Tool. Vide : le "
        "nom de l'image"
    ),
    "add.op.skeleton": "Utiliser le squelette Durty Cloth Tool",
    "add.op.skeleton.desc": (
        "Récupérer depuis Durty Cloth Tool le squelette freemode du genre choisi sous Configuration et y placer le "
        "vêtement, prêt pour Sollumz"
    ),
    "add.op.add": "Ajouter au projet",
    "add.op.add.desc": (
        "Vérifier le vêtement, l'exporter avec Sollumz et l'ajouter comme nouveau vêtement au projet ouvert dans "
        "Durty Cloth Tool. Durty Cloth Tool vous le demande d'abord"
    ),
    "add.op.cancel.desc": (
        "Arrêter l'ajout. Tant que Durty Cloth Tool pose encore la question, rien n'est ajouté"
    ),
    "add.op.add-variation": "Ajouter une variante de couleur",
    "add.op.add-variation.desc": "Ajouter une autre image comme variante de couleur du vêtement",
    "add.op.remove-variation": "Supprimer",
    "add.op.remove-variation.desc": "Supprimer cette variante de couleur",
    "add.info": (
        "Ajoute le vêtement comme nouveau vêtement au projet ouvert dans Durty Cloth Tool. Durty Cloth Tool l'affiche "
        "d'abord, et rien n'est ajouté tant que vous n'y choisissez pas Ajouter au projet. Nécessite Durty Cloth Tool "
        "avec un projet ouvert et le jeu configuré, ainsi que Sollumz."
    ),
    "add.info.variations": (
        "La propre texture du vêtement est la première variante de couleur. Ajoutez-en d'autres avec d'autres "
        "images dans la même disposition ; chacune devient une variante de couleur du vêtement, avec le nom que "
        "vous lui donnez."
    ),
    "add.info.skeleton": (
        "Durty Cloth Tool envoie le squelette freemode du genre choisi sous Configuration, créé à partir de vos "
        "fichiers de jeu. Sollumz l'importe comme armature, et le vêtement y est rattaché par un modificateur "
        "Armature ; ses groupes de sommets gardent leurs noms d'os. Ajouter le fait pour vous quand c'est "
        "nécessaire."
    ),
    "add.skeleton.ready": "Sur le squelette Durty Cloth Tool ({gender}, {count} os) : {name}",
    "add.skeleton.missing": (
        "Le vêtement n'est pas encore sur le squelette Durty Cloth Tool. "
        "Choisissez Utiliser le squelette Durty Cloth Tool, ou Ajouter, qui le fait pour vous."
    ),
    "add.skeleton.other-gender": (
        "Le vêtement est sur le squelette ({gender}). Choisissez Utiliser le squelette Durty Cloth Tool pour le "
        "déplacer sur le squelette du genre choisi sous Configuration."
    ),
    "add.skeleton.modifier": (
        "Le modificateur Armature du vêtement n'utilise pas son squelette Durty Cloth Tool. Choisissez de nouveau "
        "Utiliser le squelette Durty Cloth Tool."
    ),
    "add.skeleton.order": (
        "Les os du squelette ne sont pas dans l'ordre du jeu, les poids déplaceraient donc les mauvais os. "
        "Choisissez de nouveau Utiliser le squelette Durty Cloth Tool au lieu de modifier ses os."
    ),
    "add.skeleton.bones": (
        "Le squelette a {count} os, mais le squelette freemode en a {expected}. Choisissez de nouveau Utiliser le "
        "squelette Durty Cloth Tool au lieu de modifier ses os."
    ),
    "add.skeleton.import": (
        "Sollumz n'a pas importé le squelette comme une seule armature. Son journal Info contient les détails."
    ),
    "add.skeleton.invalid": (
        "Durty Cloth Tool a envoyé un squelette que le module ne peut pas lire. Mettez les deux à jour, puis "
        "réessayez."
    ),
    "add.skeleton.game-required": (
        "Durty Cloth Tool a besoin de votre installation de GTA V pour le squelette freemode. Configurez le jeu "
        "dans Durty Cloth Tool, puis réessayez."
    ),
    "add.skeleton.busy": "Durty Cloth Tool lit encore les fichiers du jeu. Réessayez dans un instant.",
    "add.dct-too-old": (
        "Ce Durty Cloth Tool ne peut pas encore ajouter de vêtements depuis Blender. Mettez Durty Cloth Tool à jour."
    ),
    "add.done.skeleton": "Le vêtement est sur le squelette Durty Cloth Tool ({gender}, {count} os) : {name}.",
    "add.fetching": "Récupération du squelette freemode ({gender}) depuis Durty Cloth Tool…",
    "add.progress.skeleton": "Récupération du squelette freemode depuis Durty Cloth Tool…",
    "add.sent": "{name} envoyé avec {count} variantes de couleur. Choisissez Ajouter au projet dans Durty Cloth Tool.",
    "add.sent.one": (
        "{name} envoyé avec {count} variante de couleur. Choisissez Ajouter au projet dans Durty Cloth Tool."
    ),
    "add.waiting": "Durty Cloth Tool affiche le vêtement. Choisissez Ajouter au projet ou Annuler là-bas.",
    "add.waiting.subtext": (
        "Rien n'est ajouté tant que vous ne choisissez pas Ajouter au projet dans Durty Cloth Tool. Annuler ici retire "
        "l'ajout."
    ),
    "add.withdrawing": "Annulation de l'ajout…",
    "add.blocked": "L'ajout est bloqué : {count} problèmes à corriger d'abord, listés sous Ajouter au projet.",
    "add.blocked.one": "L'ajout est bloqué : {count} problème à corriger d'abord, listé sous Ajouter au projet.",
    "add.problems": "Corrigez d'abord ceux-ci ({count}) :",
    "add.findings": "Vérifications de Durty Cloth Tool : {count}",
    "add.added.subtext": (
        "Le Drawable Dictionary est lié au nouveau vêtement : Envoyer le modèle et Enregistrer le modèle dans le "
        "vêtement, sous Vêtement lié, le mettent à jour (inclus dans Durty Cloth Tool Ultimate)."
    ),
    "add.invalid": "L'ajout ne peut pas être envoyé : {detail}",
    "add.why.connect": "Connectez-vous à Durty Cloth Tool pour ajouter le vêtement à un projet.",
    "add.why.no-project": "Ouvrez un projet dans Durty Cloth Tool pour y ajouter le vêtement.",
    "add.why.adding": "Un ajout attend la réponse de Durty Cloth Tool.",
    "add.why.fetching": "En attente du squelette freemode de Durty Cloth Tool.",
    "add.why.nothing-running": "Rien n'est en cours.",
    "add.why.no-template": "Durty Cloth Tool n'a envoyé aucun squelette freemode. Réessayez.",
    "add.why.garment-changed": (
        "Un autre vêtement a été choisi entre-temps, l'étape ne s'est donc pas exécutée. Relancez-la."
    ),
    "add.why.no-weights": (
        "Le vêtement n'a pas encore de poids pour le squelette freemode. Attribuez-lui des poids sur les os du "
        "squelette (des groupes de sommets nommés d'après eux, comme SKEL_Spine3)."
    ),
    "add.why.unknown-groups": (
        "{count} groupes de sommets ne sont pas des os du squelette freemode : {names}. Renommez-les ou "
        "supprimez-les ; le jeu les déplacerait avec l'os racine."
    ),
    "add.why.unknown-groups.one": (
        "{count} groupe de sommets n'est pas un os du squelette freemode : {names}. Renommez-le ou supprimez-le ; le "
        "jeu le déplacerait avec l'os racine."
    ),
    "add.why.name-empty": "Donnez un nom au vêtement.",
    "add.why.name-invalid": (
        "Le nom du vêtement peut contenir au plus {limit} caractères, sans caractères de contrôle."
    ),
    "add.why.combine": (
        "Le vêtement a {count} matériaux. Utilisez d'abord Combiner les matériaux : chaque variante de couleur est "
        "une seule texture."
    ),
    "add.why.no-diffuse": (
        "Le matériau du vêtement n'a pas de texture de couleur. Combiner les matériaux en crée une."
    ),
    "add.why.variation-empty": (
        "La variante de couleur {number} n'a pas d'image. Choisissez-en une, ou supprimez la ligne."
    ),
    "add.why.too-many": "Un vêtement a au plus {limit} variantes de couleur.",
    "add.why.variation-twice": (
        "L'image {name} est utilisée pour deux variantes de couleur. Chacune a besoin de la sienne."
    ),
    "add.why.too-large": (
        "Le modèle et ses images dépassent ensemble {size} MiB et ne peuvent pas être envoyés. Utilisez des images "
        "plus petites ou moins de variantes de couleur."
    ),
    "add.why.convert": "Sollumz n'a pas pu faire du vêtement un Drawable Model ({detail}).",
    "add.why.material": "Sollumz n'a pas pu donner au vêtement le shader de ped ({detail}).",
    "add.picture.empty": "L'image {name} n'a pas de pixels.",
    "add.picture.too-large": (
        "L'image {name} dépasse {size} pixels sur un côté, ce que Durty Cloth Tool n'accepte pas."
    ),
    "add.picture.not-multiple-of-four": (
        "L'image {name} fait {width} x {height} : Durty Cloth Tool a besoin de côtés divisibles par quatre."
    ),
    "add.picture.non-power-of-two": (
        "L'image {name} fait {width} x {height}, ce qui n'est pas une puissance de deux (par exemple 1024 ou 2048)."
    ),
    "add.picture.large": (
        "L'image {name} dépasse {size} pixels sur un côté, ce qui utilise beaucoup de mémoire en jeu."
    ),
    "add.picture.small": "L'image {name} fait moins de {size} pixels sur un côté.",
    "add.picture.unusable": "L'image {name} ne peut pas être envoyée : {problem}",
    "add.export.empty": (
        "Sollumz a exporté le Drawable Dictionary sans la géométrie du vêtement. Son journal Info contient les "
        "détails."
    ),
    "add.export.several": "Sollumz a exporté {count} drawables ; Durty Cloth Tool en prend un par vêtement.",
    "add.export.skeleton": "L'export contient encore le squelette. Mettez Sollumz à jour, puis réessayez.",
    "add.export.errors": (
        "Sollumz a signalé des erreurs pendant l'export, une partie du vêtement manque donc peut-être. Son journal "
        "Info contient les détails."
    ),
    "add.export.unreadable": "L'export n'a pas pu être lu ({detail}).",
    "add.export.warnings": (
        "Sollumz a signalé des avertissements pendant l'export ; son journal Info contient les détails."
    ),
    "add.result.added": "{name} a été ajouté au projet comme {slot}.",
    "add.result.added-unlinked": (
        "{name} a été ajouté au projet, mais le modèle dans Blender n'a pas pu y être lié ({detail})."
    ),
    "add.result.denied": (
        "Durty Cloth Tool n'a pas ajouté le vêtement : Annuler a été choisi là-bas. Le projet est inchangé."
    ),
    "add.result.withdrawn": "L'ajout a été annulé. Le projet est inchangé.",
    "add.result.cancel-unanswered": (
        "L'ajout a été annulé, mais Durty Cloth Tool ne l'a pas confirmé. Vérifiez le projet dans Durty Cloth Tool."
    ),
    "add.result.timeout": (
        "Durty Cloth Tool n'a pas répondu à temps à l'ajout. Vérifiez le projet dans Durty Cloth Tool."
    ),
    "add.result.disconnected": (
        "La connexion à Durty Cloth Tool a été perdue pendant l'ajout. Vérifiez le projet dans Durty Cloth Tool "
        "avant d'ajouter de nouveau le vêtement."
    ),
    "add.result.item-limit": (
        "Durty Cloth Tool n'a pas ajouté le vêtement : le projet contient déjà autant de vêtements que votre offre "
        "dans Durty Cloth Tool le permet, ou le vêtement a plus de variantes de couleur que l'offre n'en permet pour "
        "un vêtement. C'est Durty Cloth Tool qui fixe et vérifie ces limites, pas le module."
    ),
    "add.result.rejected": (
        "Durty Cloth Tool n'a pas pu utiliser le modèle ou une variante de couleur, rien n'a donc été ajouté. Ses "
        "vérifications ci-dessous indiquent pourquoi."
    ),
    "add.result.no-project": (
        "Ouvrez d'abord un projet dans Durty Cloth Tool, puis ajoutez de nouveau le vêtement."
    ),
    "add.result.item-refused": (
        "Ce projet n'accepte pas de vêtements freemode de cette façon (par exemple un projet de ped personnalisé). "
        "Ouvrez un projet freemode dans Durty Cloth Tool."
    ),
    "add.result.busy": (
        "Durty Cloth Tool est occupé (un build est en cours, ou un autre ajout attend une réponse). Réessayez dans "
        "un instant."
    ),
    "add.result.rate-limited": "Trop d'ajouts en peu de temps. Patientez quelques secondes, puis réessayez.",
    "add.result.save-failed": (
        "Durty Cloth Tool n'a pas pu ajouter le vêtement. Sa barre d'état contient les détails."
    ),
    "add.finding.rig-invalid": (
        "Les poids ou les indices d'os ne correspondent pas au squelette freemode : le vêtement bougerait mal dans "
        "le jeu."
    ),
    "add.finding.rig-unchecked": "Durty Cloth Tool n'a pas pu lire les poids pour les vérifier.",
    "add.finding.single-bone-rig": (
        "Un seul os porte presque tout le poids d'un niveau de détail, le vêtement suivrait donc à peine les "
        "mouvements du corps."
    ),
    "add.finding.hair-tint-unsupported": (
        "Ces cheveux ne peuvent pas prendre la couleur de cheveux choisie par le joueur."
    ),
    "add.finding.picture.non-power-of-two": (
        "La taille d'une variante de couleur n'est pas une puissance de deux (par exemple 1024 ou 2048)."
    ),
    "add.finding.picture.not-multiple-of-four": (
        "La taille d'une variante de couleur n'est pas divisible par quatre."
    ),
    "add.finding.picture.too-large": (
        "Une variante de couleur est plus grande que ce que conseille Durty Cloth Tool (2048 pixels de côté ; il "
        "accepte au plus 4096)."
    ),
    "add.finding.picture.too-small": "Une variante de couleur fait moins de 16 pixels sur un côté.",
    "garment.next.align": (
        "Ensuite : Aligner sur le corps sous Ajustement, pour que le vêtement soit posé sur le corps freemode."
    ),
    "garment.next.weights": (
        "Ensuite : Transférer les poids sous Prêt pour le jeu, ou pondérez vous-même le vêtement sur les os du "
        "squelette freemode. Générez ensuite les LOD, qui reprennent les poids."
    ),
    "garment.region.forearms": "Avant-bras",
    "garment.region.cuffs": "Poignets de manche",
    "garment.unit.auto": "Automatique",
    "garment.unit.m": "Mètres",
    "garment.unit.cm": "Centimètres",
    "garment.unit.mm": "Millimètres",
    "garment.unit.in": "Pouces",
    "garment.unit.desc": "L'unité dans laquelle le fichier a été enregistré",
    "garment.prop.unit": "Unité",
    "garment.prop.unit.desc": (
        "L'unité dans laquelle le fichier a été enregistré. Automatique choisit l'unité qui donne au vêtement une "
        "taille crédible"
    ),
    "garment.prop.orient": "Redresser",
    "garment.prop.orient.desc": (
        "Tourner un vêtement couché sur le dos ou tourné vers l'arrière pour qu'il se tienne comme le ped"
    ),
    "garment.prop.keep-size": "Garder la taille",
    "garment.prop.keep-size.desc": (
        "Aligner sur le corps se contente de déplacer et de tourner le vêtement, sans l'adapter à la taille du corps"
    ),
    "garment.heading.options": "Options",
    "garment.op.align": "Aligner sur le corps",
    "garment.op.align.desc": (
        "Déplace et tourne le vêtement (et le met à l'échelle, Garder la taille désactivé) pour que ses marqueurs se "
        "trouvent sur les articulations du corps, puis tourne ses bras ou ses jambes sur ceux du corps"
    ),
    "garment.op.back": "Revenir d'une étape",
    "garment.op.back.desc": "Rétablir la forme du vêtement d'avant la dernière étape qui l'a modifié",
    "garment.op.remove-backups": "Supprimer les sauvegardes",
    "garment.op.remove-backups.desc": "Supprimer les sauvegardes du vêtement du fichier .blend",
    "garment.align.source.hosted": "Articulations : du corps freemode.",
    "garment.align.source.dct": "Articulations : de vos fichiers du jeu, via Durty Cloth Tool.",
    "garment.align.source.estimate": (
        "Articulations : estimées d'après la forme du corps. Avec Durty Cloth Tool connecté, Aligner sur le corps "
        "utilise les articulations exactes."
    ),
    "garment.align.fetching": "Récupération des articulations du squelette freemode dans Durty Cloth Tool…",
    "garment.info.align": (
        "Déplace et tourne le vêtement pour que ses marqueurs se trouvent sur les articulations du corps freemode, "
        "puis tourne chaque bras (ou jambe) sur celui du corps. Avec Garder la taille désactivé, il met aussi le "
        "vêtement à l'échelle du corps. Les outils sous Correction mesurent par rapport au corps, ils attendent donc "
        "cette étape, et à nouveau quand un marqueur a été déplacé depuis. Lancez d'abord Marqueurs automatiques et "
        "déplacez tout marqueur mal placé."
    ),
    "garment.done.align": (
        "Aligné sur le corps : déplacé de {shift} cm, tourné de {turn}°, mis à {scale} %, {limbs} bras ou jambes "
        "tournés. Les marqueurs sont en moyenne à {residual} mm des articulations."
    ),
    "garment.why.align-first": "Alignez d'abord le vêtement sur le corps sous Ajustement.",
    "garment.why.region-snug": (
        "Plaquer au corps laisse les pans de manteau et les jupes tranquilles : ils pendent librement des jambes."
    ),
    "garment.why.ped-material": (
        "Le vêtement a déjà le shader ped, son matériau est donc prêt pour le jeu. Combiner les matériaux le "
        "remplacerait."
    ),
    "garment.marker-error.align-markers": (
        "Les marqueurs ne correspondent pas aux articulations du corps sans beaucoup mettre à l'échelle ou tourner le "
        "vêtement. Vérifiez-les (les lignes entre eux montrent où ils sont), puis alignez de nouveau."
    ),
    "garment.marker-note.arms-estimated": (
        "Aucune manche trouvée, les bras suivent donc la pose d'origine. Vérifiez les coudes et les poignets."
    ),
    "garment.marker-note.hood": "Une capuche a été trouvée : le marqueur du cou est placé dessous.",
    "garment.marker-note.skirt": (
        "Aucune jambe trouvée, les hanches sont donc placées selon des proportions courantes (une jupe ?)."
    ),
    "garment.marker-note.legs-estimated": (
        "Les jambes s'arrêtent tôt, les genoux et les chevilles sont donc placés selon des proportions courantes."
    ),
    "garment.marker-problem.order": (
        "Les marqueurs ne sont pas dans l'ordre de haut en bas. Vérifiez le cou, la poitrine et le bassin."
    ),
    "garment.marker-problem.span": (
        "Les épaules sont trop proches ou trop éloignées. Vérifiez les marqueurs des épaules."
    ),
    "garment.marker-problem.symmetry": (
        "Les marqueurs gauches et droits ne sont pas symétriques. Miroir G vers D les fait correspondre."
    ),
    "garment.marker-problem.arms": (
        "Les marqueurs d'un bras sont trop courts, trop longs ou repliés. Vérifiez les coudes et les poignets."
    ),
    "garment.marker-problem.legs": (
        "Les marqueurs d'une jambe sont trop courts ou trop longs. Vérifiez les genoux et les chevilles."
    ),
    "garment.done.import-turned": "{name} importé ({count} sommets) et tourné pour se tenir comme le ped.",
    "garment.done.import-avatar": "{name} importé ({count} sommets), sans l'avatar qui l'accompagnait.",
    "garment.done.back": "La forme d'avant la dernière étape est rétablie.",
    "garment.done.remove-backups": "{count} sauvegardes supprimées.",
    "garment.done.remove-backups.one": "{count} sauvegarde supprimée.",
    "garment.done.push-deep": (
        "{moved} sommets déplacés. Dans le corps : {before} avant, {after} maintenant. {deep} sont trop profonds pour "
        "être déplacés (une manche à travers le corps ?) : corrigez-les à la main."
    ),
    "garment.done.prepare-thick": (
        "Export épais préparé : {welded} sommets joints entre les pièces, {walls} parois intérieures supprimées, "
        "{triangles} triangles."
    ),
    "garment.done.cancel-sculpt-lost": (
        "La session de sculpture est terminée, mais sa forme de départ a été perdue. Ctrl+Z l'a encore."
    ),
    "garment.done.sculpt-mirror-off": (
        "Session de sculpture commencée. Miroir X travaille autour du centre propre du vêtement, qui n'est pas celui "
        "du ped : appliquez d'abord la transformation du vêtement pour travailler en miroir autour du ped."
    ),
    "garment.sculpt.broken": (
        "La session de sculpture a perdu sa forme de départ (Dyntopo ou un remaillage font cela). Accepter garde la "
        "forme et termine la session."
    ),
    "garment.tears.pose-skipped": "{pose} : ignorée, l'armature n'a pas d'os pour elle",
    "garment.error.cycles": (
        "Combiner les matériaux cuit avec Cycles. Activez Cycles sous Édition > Préférences > Add-ons, puis réessayez."
    ),
    "garment.body.compressed": (
        "Ce Blender ne peut pas lire le corps freemode compressé. Utilisez Blender 5.2 ou plus récent, ou un fichier "
        "de corps, jusqu'à ce que gta.clothing propose le corps non compressé."
    ),
    "garment.finding.triangles": (
        "Le niveau {level} a {count} triangles, plus que les {budget} que conseille Durty Cloth Tool."
    ),
    "garment.finding.placement": (
        "Le milieu du vêtement est à {distance} cm du corps, il n'est donc pas sur le corps. Vérifiez l'importation "
        "(unité, avatar au sol) et Aligner sur le corps."
    ),
    "garment.finding.normals-inward": (
        "{share} % de la surface proche du corps est tournée vers l'intérieur : les normales semblent inversées. "
        "Recalculez-les vers l'extérieur en Mode Édition (Maillage > Normales)."
    ),
    "add.result.added-late": (
        "Durty Cloth Tool a finalement ajouté {name} : Ajouter au projet y a été choisi avant l'arrivée de "
        "l'annulation. Il est maintenant lié ici."
    ),
    "add.warning.normal-not-embedded": (
        "La normal map {name} n'est pas un fichier DDS, elle n'est donc pas envoyée avec le modèle. Ajoutez-la dans "
        "Durty Cloth Tool après l'ajout."
    ),
    "add.warning.specular-not-embedded": (
        "La specular map {name} n'est pas un fichier DDS, elle n'est donc pas envoyée avec le modèle. Ajoutez-la dans "
        "Durty Cloth Tool après l'ajout."
    ),
    "add.why.no-ped-shader": (
        "Sollumz n'a pas de shader ped (ped.sps), le vêtement ne peut donc pas recevoir le matériau des vêtements. "
        "Mettez à jour ou réinstallez Sollumz."
    ),
    "add.progress.prepare": "Mise du vêtement sur le squelette et préparation de son matériau…",
    "add.progress.export": "Exportation du vêtement avec Sollumz…",
    "add.progress.pictures": "Écriture des variantes de couleur ({done} sur {total})…",
    "add.cancelled-local": "L'ajout a été annulé avant tout envoi. Ctrl+Z annule ce qu'il a modifié sur le vêtement.",
    "add.failed-undo": "{problem} Ctrl+Z rétablit le vêtement tel qu'il était avant l'ajout.",
    # ---- garment fitting on gta.clothing ------------------------------------------------------------------
    "garment.op.service-fit": "Ajuster sur gta.clothing",
    "garment.op.service-fit.desc": (
        "Envoie le vêtement à gta.clothing, qui le met dans la pose du jeu, lui donne les poids du corps freemode et "
        "le sort du corps. Utilise un de vos ajustements du jour"
    ),
    "garment.op.service-weights": "Transférer les poids",
    "garment.op.service-weights.desc": (
        "Envoie le vêtement à gta.clothing, qui lui donne les poids du corps freemode sans le déplacer. Utilise un de "
        "vos ajustements du jour"
    ),
    "garment.op.service-cancel.desc": (
        "Arrête l'ajustement. Un ajustement que gta.clothing n'a pas encore commencé ne compte pas pour aujourd'hui ; "
        "un ajustement commencé compte quand même"
    ),
    "garment.info.service": (
        "Ajuster sur gta.clothing ajuste le vêtement tel qu'il est après Aligner sur le corps. Il revient dans la pose "
        "du jeu, avec les poids du corps freemode, et sorti du corps là où il était dedans. Le vêtement garde une "
        "sauvegarde, donc Revenir d'une étape le remet comme avant. Chaque ajustement utilise un de vos ajustements du "
        "jour."
    ),
    "garment.info.weights": (
        "Transférer les poids donne au vêtement les poids du corps freemode, sous forme de groupes de sommets au nom "
        "des os, sans le déplacer. Utilisez-le après un changement de forme, par exemple après la sculpture ou "
        "Préparer le vêtement. Il utilise un de vos ajustements du jour ; vous pouvez aussi pondérer le vêtement "
        "vous-même."
    ),
    "garment.prop.clearance": "Écart (mm)",
    "garment.prop.clearance.desc": "La distance à laquelle le vêtement reste hors du corps là où il est sorti",
    "garment.prop.service-push": "Sortir du corps",
    "garment.prop.service-push.desc": (
        "Sort jusqu'à l'écart chaque partie du vêtement qui est dans le corps ou trop près de lui"
    ),
    "garment.prop.max-push": "Déplacement maximal (mm)",
    "garment.prop.max-push.desc": "Les parties plus profondes dans le corps restent où elles sont",
    "garment.prop.seam-gap": "Écart de couture (mm)",
    "garment.prop.seam-gap.desc": (
        "Les bords de pièces plus proches que cela forment une seule couture, pour que les deux côtés reçoivent les "
        "mêmes poids. 0 le désactive"
    ),
    "garment.prop.proportions": "Adapter les proportions",
    "garment.prop.proportions.desc": (
        "Étire aussi les bras et les jambes du corps jusqu'aux marqueurs du vêtement, pour un vêtement fait sur un "
        "autre avatar"
    ),
    "fit.left": "Ajustements restants aujourd'hui : {left} sur {total}",
    "fit.stage.uploading": "Envoi du vêtement ({percent} %)",
    "fit.stage.busy": "gta.clothing est occupé. Nouvel essai dans un instant",
    "fit.stage.queued": "En attente de gta.clothing",
    "fit.stage.validating": "Vérification du vêtement",
    "fit.stage.running": "Ajustement",
    "fit.stage.cancelling": "Annulation",
    "fit.stage.cancelling-counted": "Annulation. L'ajustement a commencé, il compte donc quand même",
    "fit.consent.title": "Envoyer pour l'ajustement",
    "fit.consent.what": "Ajuster sur gta.clothing et Transférer les poids envoient le vêtement.",
    "fit.consent.kept": (
        "Seuls la forme et les marqueurs du vêtement sont envoyés, avec les options d'ajustement, et rien n'en est "
        "conservé plus de dix minutes après l'ajustement."
    ),
    "fit.consent.revoke": (
        "Vous acceptez une seule fois. Pour revenir dessus, désactivez Envoyer les vêtements pour l'ajustement sous "
        "Réglages > Confidentialité."
    ),
    "fit.consent.confirm": "Envoyer et ajuster",
    "prop.fit-consent": "Envoyer les vêtements pour l'ajustement",
    "prop.fit-consent.desc": (
        "Autorise Ajuster sur gta.clothing et Transférer les poids à envoyer le vêtement. Désactivez-le pour revenir "
        "dessus ; l'add-on redemande alors avant tout envoi"
    ),
    "settings.fit-consent-subtext": (
        "Seuls la forme et les marqueurs du vêtement sont envoyés, avec les options d'ajustement, et rien n'en est "
        "conservé plus de dix minutes après l'ajustement."
    ),
    "fit.why.running": "Un ajustement est en cours. Attendez-le ou annulez-le.",
    "fit.why.hosted-body": (
        "L'ajustement a besoin du corps freemode de gta.clothing : Ajouter le corps freemode sous Configuration."
    ),
    "fit.why.sign-in": "Connectez-vous d'abord avec gta.clothing (Se connecter).",
    "fit.why.no-fits": "Plus aucun ajustement ne peut être lancé aujourd'hui. D'autres seront disponibles {wait}.",
    "fit.error.update": "gta.clothing n'a pas pu lire ce que l'add-on a envoyé. Mettez l'add-on à jour et réessayez.",
    "fit.error.plugin-update": (
        "Mettez l'add-on à jour pour ajuster des vêtements : Édition > Préférences > Obtenir des extensions > "
        "Rechercher des mises à jour."
    ),
    "fit.error.signed-out": (
        "Votre connexion à gta.clothing a pris fin. Reconnectez-vous sous Se connecter, puis réessayez."
    ),
    "fit.error.locked": "Ce compte gta.clothing est verrouillé et ne peut pas ajuster de vêtements.",
    "fit.error.not-entitled": (
        "Votre compte gta.clothing ne peut pas ajuster de vêtements. Vérifiez votre compte sur gta.clothing."
    ),
    "fit.error.switched-off": (
        "L'ajustement est désactivé sur gta.clothing pour le moment. Les outils dans Blender fonctionnent toujours."
    ),
    "fit.error.unavailable": (
        "L'ajustement sur gta.clothing n'est pas disponible pour l'instant. Réessayez dans une minute."
    ),
    "fit.error.not-found": "gta.clothing n'a plus cet ajustement. Ajustez à nouveau.",
    "fit.error.body-version": (
        "gta.clothing ajuste sur un corps freemode plus récent. Refaites Ajouter le corps freemode sous Configuration, "
        "alignez le vêtement dessus et ajustez à nouveau."
    ),
    "fit.error.too-large": (
        "Le vêtement est trop détaillé pour être ajusté : au plus 120 000 sommets et 240 000 triangles. Réduisez-le, "
        "par exemple avec un modificateur Décimer."
    ),
    "fit.error.mesh-invalid": "gta.clothing n'a pas pu ajuster ce vêtement :",
    "fit.error.quota": "Plus aucun ajustement ne peut être lancé aujourd'hui. D'autres seront disponibles {wait}.",
    "fit.error.busy": "gta.clothing est resté occupé pendant quelques minutes. Réessayez plus tard.",
    "fit.error.rate-limited": "Trop de requêtes vers gta.clothing en peu de temps. Attendez une minute et réessayez.",
    "fit.error.server": "Un problème est survenu sur gta.clothing pendant l'ajustement. Réessayez.",
    "fit.error.timeout": (
        "L'ajustement a duré plus longtemps que gta.clothing ne le permet. Réduisez les détails du vêtement et "
        "réessayez."
    ),
    "fit.error.network": "gta.clothing est injoignable. Vérifiez la connexion Internet et réessayez.",
    "fit.error.network-uploaded": (
        "La connexion a été coupée après l'envoi du vêtement. Ajustements restants aujourd'hui indique si l'ajustement "
        "a compté. Réessayez."
    ),
    "fit.error.upload-timeout": (
        "L'envoi du vêtement a pris trop de temps, gta.clothing a donc cessé de l'attendre. Réessayez avec une "
        "connexion plus rapide ou plus stable, ou réduisez le détail du vêtement pour avoir moins à envoyer."
    ),
    "fit.error.cancelled": "L'ajustement a été annulé.",
    "fit.error.other": "gta.clothing a refusé l'ajustement ({code}).",
    "fit.wait.minutes": "dans environ {count} minutes",
    "fit.wait.minutes.one": "dans environ {count} minute",
    "fit.wait.hours": "dans environ {count} heures",
    "fit.wait.hours.one": "dans environ {count} heure",
    "fit.wait.later": "demain",
    "fit.refunded": "Cet ajustement ne compte pas pour aujourd'hui.",
    "fit.counted": "Cet ajustement compte pour aujourd'hui.",
    "fit.cancelled-counted": "L'ajustement avait déjà commencé sur gta.clothing, il compte donc pour aujourd'hui.",
    "fit.input.add-on": "L'add-on a envoyé quelque chose que gta.clothing n'accepte pas. Mettez l'add-on à jour.",
    "fit.input.slot": "Seuls les vêtements portés sur le corps peuvent être ajustés.",
    "fit.input.options": (
        "Une option d'ajustement est hors de sa plage. Vérifiez les options de Ajuster sur gta.clothing."
    ),
    "fit.input.too-large": (
        "Le vêtement a {vertices} sommets et {triangles} triangles ; l'ajustement en accepte au plus 120 000 et 240 "
        "000. Réduisez-le, par exemple avec un modificateur Décimer."
    ),
    "fit.input.broken": (
        "Certains sommets du vêtement ont des positions cassées. Supprimez-les ou importez à nouveau le vêtement."
    ),
    "fit.input.far": (
        "Une partie du vêtement se trouve à plus de 3 m du corps. Supprimez les parties égarées, puis alignez-le à "
        "nouveau."
    ),
    "fit.input.degenerate": (
        "Le vêtement a des faces sans surface. Fusionner par distance en Mode Édition les supprime."
    ),
    "fit.input.duplicate": (
        "Le vêtement a des faces empilées les unes sur les autres. Fusionner par distance en Mode Édition supprime les "
        "copies."
    ),
    "fit.input.seam-dense": (
        "De nombreuses arêtes libres se pressent en un point du vêtement. Supprimez-y les parties isolées (en Mode "
        "Édition), ou réglez Écart de couture sur 0 dans les options de Ajuster sur gta.clothing."
    ),
    "fit.input.seam-crowded": (
        "{count} arêtes ouvertes se pressent en un point du vêtement, et gta.clothing en accepte au plus {limit} à cet "
        "endroit : en général de petites parties isolées comme des boutons, ou des surpiqûres posées sur le tissu. "
        "Elles sont sélectionnées : appuyez sur Tab pour les voir, puis supprimez-les ou fusionnez-les (Fusionner par "
        "distance). Ou réglez Écart de couture sur 0 dans les options de Ajuster sur gta.clothing."
    ),
    "fit.input.seam-crowded-prepare": (
        "{count} arêtes ouvertes se pressent en un point du vêtement, et gta.clothing en accepte au plus {limit} à cet "
        "endroit : en général là où plusieurs pièces se rejoignent sans que leurs coutures soient encore réunies. "
        "Préparer le vêtement dans Prêt pour le jeu les réunit : lancez-le, puis ajustez à nouveau. L'endroit est "
        "sélectionné : appuyez sur Tab pour le voir."
    ),
    "fit.input.marker-far": (
        "Un marqueur est loin de l'articulation du corps. Vérifiez les marqueurs, alignez à nouveau le vêtement et "
        "ajustez."
    ),
    "fit.input.marker-missing": (
        "Des marqueurs manquent. Placez-les avec Marqueurs automatiques, alignez le vêtement et ajustez à nouveau."
    ),
    "fit.input.marker-side": (
        "Les marqueurs gauche et droite sont inversés. Placez chaque marqueur de son côté et ajustez à nouveau."
    ),
    "fit.input.marker-length": (
        "Les marqueurs du coude, du poignet, du genou ou de la cheville ne sont pas là où peuvent se trouver les "
        "articulations d'un bras ou d'une jambe. Placez-les sur les articulations du vêtement."
    ),
    "fit.input.gender": "Le genre du vêtement ne correspond pas au corps. Choisissez le bon genre sous Configuration.",
    "fit.input.other": "gta.clothing a trouvé un problème dans le vêtement ({code}).",
    "fit.warning.inside-body": (
        "Des parties du vêtement sont encore dans le corps. Pousser hors du corps sous Correction les sort."
    ),
    "fit.warning.low-coverage": (
        "Seule une partie du vêtement repose sur le corps. Les parties éloignées peuvent bouger bizarrement en jeu."
    ),
    "fit.warning.marker-offset": (
        "Certains marqueurs sont éloignés des articulations du corps. Vérifiez les marqueurs des épaules et des "
        "coudes."
    ),
    "fit.warning.proportion-clamped": (
        "Les proportions du vêtement sont très éloignées de celles du corps freemode ; certaines ont été limitées."
    ),
    "fit.warning.shape-strained": (
        "Certaines zones se sont étirées pendant la mise en pose. Afficher les problèmes (sous Correction, dans "
        "Problèmes) les trouve."
    ),
    "fit.warning.attachment-fallback": (
        "Des parties isolées ont été pondérées sur la partie du corps la plus proche. Vérifiez-les en mode Peinture de "
        "poids."
    ),
    "fit.warning.unweighted": (
        "Certains sommets n'ont reçu aucun poids ; le jeu les laisse derrière quand le personnage bouge."
    ),
    "fit.done.fit": "Ajusté au corps : dans la pose du jeu, avec des poids pour {bones} os.",
    "fit.done.review": "Ajusté au corps, avec des poids pour {bones} os. Vérifiez ce que gta.clothing a remarqué :",
    "fit.done.weights": "Poids transférés : {bones} os.",
    "fit.done.not-on-body": (
        "Le vêtement ne repose pas sur le corps, donc rien n'a changé. Alignez-le d'abord sur le corps."
    ),
    "fit.done.unweighted": "{count} sommets n'ont reçu aucun poids.",
    "fit.done.unweighted.one": "{count} sommet n'a reçu aucun poids.",
    "fit.changed": (
        "Le vêtement a changé pendant l'ajustement, donc le résultat n'a pas été appliqué. Ajustez à nouveau."
    ),
    "garment.next.fit": (
        "Ensuite : Ajuster sur gta.clothing sous Ajustement, ou lancez le contrôle de l'ajustement sous Correction et "
        "ajustez le vêtement à la main."
    ),
    "garment.check.reference": "Habituel",
    "garment.check.reference-none": "–",
    "garment.check.reference-subtext": (
        "Habituel : la distance à laquelle les vêtements du jeu de ce type se tiennent du corps, d'après gta.clothing."
    ),
    "garment.check.reference-offline": (
        "Connectez-vous et autorisez l'accès en ligne pour comparer avec les vêtements du jeu."
    ),
    # ---- garment fitting: units, stepped Prepare and Combine -----------------------------------------------------------
    "garment.unit.dm": "Décimètres",
    "garment.done.import-unit": (
        "{name} importé ({count} sommets), sa taille lue en {unit}, la seule unité qui lui donne la taille d'un "
        "vêtement. Si elle semble fausse, importez-le à nouveau et choisissez l'unité."
    ),
    "garment.done.import-size": (
        "{name} importé ({count} sommets), mais avec {size} m il n'a pas la taille de ce genre de vêtement. "
        "Importez-le à nouveau et choisissez l'unité, ou vérifiez le type de vêtement."
    ),
    "garment.done.prepare-open": (
        "Préparé, mais {count} sommets de couture n'ont trouvé aucun partenaire sur la pièce voisine ({welded} réunis) "
        ": les pièces ne se rejoignent pas tout à fait à cet endroit. Ils sont sélectionnés : appuyez sur Tab pour les "
        "voir. Ajuster sur gta.clothing donne quand même les mêmes poids aux deux côtés d'une couture ; si un trou "
        "apparaît dans le jeu, cousez ces coutures dans votre application de vêtements et exportez à nouveau, ou "
        "réunissez-les à la main."
    ),
    "garment.done.prepare-open.one": (
        "Préparé, mais {count} sommet de couture n'a trouvé aucun partenaire sur la pièce voisine ({welded} réunis) : "
        "les pièces ne se rejoignent pas tout à fait à cet endroit. Il est sélectionné : appuyez sur Tab pour le voir. "
        "Ajuster sur gta.clothing donne quand même les mêmes poids aux deux côtés d'une couture ; si un trou apparaît "
        "dans le jeu, cousez cette couture dans votre application de vêtements et exportez à nouveau, ou réunissez-la "
        "à la main."
    ),
    "garment.done.combine-missing": (
        "Combiné, mais {count} textures sont introuvables et ont été cuites sans leurs pixels : {names}. Placez les "
        "fichiers d'image là où les matériaux les attendent (ou empaquetez-les), puis combinez à nouveau."
    ),
    "garment.done.combine-missing.one": (
        "Combiné, mais {count} texture est introuvable et a été cuite sans ses pixels : {names}. Placez le fichier "
        "d'image là où le matériau l'attend (ou empaquetez-le), puis combinez à nouveau."
    ),
    "garment.done.step-cancelled": "{step} a été annulé ; le vêtement est comme avant.",
    "garment.step.status": "{step} : {stage} ({done} sur {total}). Échap annule à la fin de cette étape.",
    "garment.stage.seams": "Recherche des coutures",
    "garment.stage.weld": "Réunion des coutures",
    "garment.stage.clean": "Nettoyage et triangulation",
    "garment.stage.pack-cut": "Préparation de la disposition UV",
    "garment.stage.pack-scale": "Harmonisation des îlots UV",
    "garment.stage.pack": "Empaquetage de la disposition UV",
    "garment.stage.bake-colour": "Cuisson de la couleur",
    "garment.stage.bake-alpha": "Cuisson de la transparence",
    "garment.stage.bake-specular": "Cuisson de la carte spéculaire",
    "garment.stage.bake-normal": "Cuisson de la carte de normales",
    "garment.stage.bake-emission": "Cuisson de la carte d'émission",
    "garment.stage.material": "Création du matériau combiné",
    "garment.slot.berd": "Masque (berd)",
    "garment.slot.berd.desc": "Masques et couvre-visages",
    "garment.slot.hand": "Sac (hand)",
    "garment.slot.hand.desc": "Sacs, sacs à dos et parachutes",
    "garment.slot.task": "Armure (task)",
    "garment.slot.task.desc": "Gilets pare-balles et autres équipements portés sur le haut",
    "garment.slot.p_head": "Accessoire de tête (p_head)",
    "garment.slot.p_head.desc": "Un accessoire sur la tête : chapeaux, casquettes et casques",
    "garment.slot.p_eyes": "Accessoire des yeux (p_eyes)",
    "garment.slot.p_eyes.desc": "Un accessoire sur les yeux : lunettes",
    "garment.slot.p_ears": "Accessoire des oreilles (p_ears)",
    "garment.slot.p_ears.desc": "Un accessoire aux oreilles : boucles d'oreilles et oreillettes",
    "garment.slot.p_lwrist": "Accessoire du poignet gauche (p_lwrist)",
    "garment.slot.p_lwrist.desc": "Un accessoire au poignet gauche : montres et bracelets",
    "garment.slot.p_rwrist": "Accessoire du poignet droit (p_rwrist)",
    "garment.slot.p_rwrist.desc": "Un accessoire au poignet droit : montres et bracelets",
    "garment.category.hoodie": "Sweat à capuche",
    "garment.category.hoodie.desc": "Un haut à manches longues avec une capuche",
    "garment.category.open_jacket": "Veste ouverte",
    "garment.category.open_jacket.desc": "Une veste portée ouverte : ses deux devants ne sont jamais joints",
    "garment.category.long_coat": "Manteau long",
    "garment.category.long_coat.desc": (
        "Un manteau qui descend aux genoux ou plus bas, ses pans suivant les deux jambes"
    ),
    "garment.category.dress": "Robe",
    "garment.category.dress.desc": (
        "Un haut et une jupe d'un seul tenant : un vêtement dans l'emplacement Haut, ou séparé en Haut et Jambes"
    ),
    "garment.category.skirt": "Jupe",
    "garment.category.skirt.desc": "Une jupe dans l'emplacement Jambes qui suit les deux jambes",
    "garment.category.sandals": "Sandales",
    "garment.category.sandals.desc": "Des chaussures ouvertes qui laissent les pieds nus",
    "garment.category.mask": "Masque",
    "garment.category.mask.desc": "Un masque ou un couvre-visage",
    "garment.category.armour": "Gilet pare-balles",
    "garment.category.armour.desc": "Porté sur le haut, comme un gilet pare-balles ou un porte-plaques",
    "garment.category.bag": "Sac ou parachute",
    "garment.category.bag.desc": "Un sac à dos, un sac ou un parachute porté sur le dos",
    "garment.category.hat": "Chapeau",
    "garment.category.hat.desc": "Un chapeau, une casquette ou un casque : un accessoire sur la tête",
    "garment.category.glasses": "Lunettes",
    "garment.category.glasses.desc": "Des lunettes de vue ou de soleil : un accessoire sur les yeux",
    "garment.category.ears": "Accessoire d'oreille",
    "garment.category.ears.desc": "Des boucles d'oreilles ou une oreillette : un accessoire aux oreilles",
    "garment.category.watch": "Montre",
    "garment.category.watch.desc": "Une montre : un accessoire au poignet",
    "garment.category.bracelet": "Bracelet",
    "garment.category.bracelet.desc": "Un bracelet : un accessoire au poignet",
    "garment.region.head": "Tête",
    "garment.info.type": (
        "Le type fixe l'emplacement du vêtement, la façon de trouver ses marqueurs, les zones proposées par les outils "
        "et ce qui est vérifié. Les accessoires (chapeaux, lunettes, accessoires d'oreille, montres et bracelets) sont "
        "posés sur leur ancrage au lieu d'être ajustés au corps."
    ),
    "garment.hint.hood": (
        "Marqueurs automatiques trouve le cou sous la capuche, et Plaquer au corps laisse la capuche telle quelle."
    ),
    "garment.hint.open-front": (
        "Préparer le vêtement ne joint jamais les deux devants, aussi proches soient-ils (Devant ouvert dans Options)."
    ),
    "garment.hint.coat": (
        "Les pans pendent librement : Plaquer au corps les laisse tels quels, et après chaque ajustement leurs poids "
        "des cuisses sont reliés d'une jambe à l'autre, pour que le manteau ne se sépare pas entre elles."
    ),
    "garment.hint.dress": (
        "D'un seul tenant : la robe va dans l'emplacement Haut comme un seul vêtement, les poids de la jupe reliés "
        "d'une jambe à l'autre ; les joueurs portent des jambes nues dans l'emplacement Jambes avec elle. En deux "
        "pièces : Couper à la taille dans Ajustement la sépare en un haut et une jupe pour l'emplacement Jambes, "
        "ajoutés l'un après l'autre, pour que chacun se porte avec d'autres vêtements."
    ),
    "garment.hint.bare-legs": (
        "L'emplacement Jambes remplace les jambes du ped : les jambes nues sous l'ourlet doivent donc faire partie du "
        "vêtement. L'extension ajoute le vêtement ; les jambes nues viennent des outils de Durty Cloth Tool, selon ce "
        "que permet votre offre Durty Cloth Tool. Peau visible est activé."
    ),
    "garment.hint.bare-feet": (
        "L'emplacement Chaussures remplace les pieds du ped : les pieds nus doivent donc faire partie du vêtement. "
        "L'extension ajoute les sandales ; les pieds nus viennent des outils de Durty Cloth Tool, selon ce que permet "
        "votre offre Durty Cloth Tool. Peau visible est activé."
    ),
    "garment.hint.avatar": (
        "Ses marqueurs ne se lisent pas d'après sa forme : choisissez l'avatar sur lequel il a été drapé, ou Marqueurs "
        "automatiques les place d'abord sur les articulations du corps pour que vous les déplaciez."
    ),
    "garment.hint.prop": (
        "Un accessoire pend à un seul os et garde sa forme : il n'est pas ajusté au corps et n'a pas besoin de poids. "
        "Poser sur l'ancrage dans Ajustement le met en place ; déplacez-le ensuite à la main."
    ),
    "garment.prop.open-front": "Devant ouvert",
    "garment.prop.open-front.desc": (
        "Le vêtement se porte ouvert : Préparer le vêtement ne joint jamais ses deux devants"
    ),
    "garment.prop.avatar": "Avatar",
    "garment.prop.avatar.desc": (
        "L'avatar sur lequel le vêtement a été drapé, s'il est connu : ses articulations deviennent les marqueurs"
    ),
    "garment.avatar.detect": "Inconnu",
    "garment.avatar.detect.desc": "Marqueurs automatiques lit les marqueurs d'après la forme du vêtement",
    "garment.avatar.file": "Importé avec le vêtement",
    "garment.avatar.file.desc": (
        "L'avatar riggé exporté avec le vêtement : l'importation a gardé l'emplacement de ses articulations"
    ),
    "garment.avatar.manne": "Manne (homme, A-pose)",
    "garment.avatar.manne.desc": (
        "MaleTemplate_Manne_01, le modèle masculin de Marvelous Designer et de CLO, dans son A-pose"
    ),
    "garment.info.avatar": (
        "Si l'avatar sur lequel le vêtement a été drapé est connu, Marqueurs automatiques place les marqueurs sur ses "
        "articulations, dans la pose du drapé. Importer un vêtement les garde depuis un FBX exporté avec l'avatar "
        "riggé ; sinon choisissez l'avatar standard sur lequel vous avez drapé. Les marqueurs d'un avatar standard "
        "correspondent à sa taille et à sa pose par défaut : vérifiez les marqueurs si vous l'avez redimensionné ou "
        "changé de pose dans Marvelous Designer."
    ),
    "garment.marker-note.avatar": "Placés sur les articulations de l'avatar sur lequel le vêtement a été drapé.",
    "garment.marker-note.from-body": (
        "Placés sur les articulations du corps : déplacez chacun sur le point correspondant du vêtement."
    ),
    "garment.why.no-avatar-file": (
        "Cet avatar n'est pas connu pour ce vêtement : il n'a pas été importé avec son avatar riggé. Choisissez un "
        "autre avatar, ou Inconnu."
    ),
    "garment.why.avatar-markers": (
        "Il manque à l'avatar un marqueur dont ce type a besoin. Choisissez Inconnu, ou placez-le à la main."
    ),
    "garment.why.avatar-moved": (
        "Le vêtement a bougé depuis son import, les marqueurs de l'avatar ne lui correspondent donc plus. Choisissez "
        "Inconnu, ou déplacez les marqueurs à la main."
    ),
    "garment.done.import-rig": (
        "{name} importé ({count} sommets), avec les articulations de l'avatar exporté avec lui gardées pour les "
        "marqueurs."
    ),
    "garment.op.snap": "Poser sur l'ancrage",
    "garment.op.snap.desc": (
        "Poser l'accessoire sur son ancrage sur le corps : un chapeau sur la tête, des lunettes devant les yeux, un "
        "accessoire d'oreille aux oreilles, une montre ou un bracelet autour du poignet"
    ),
    "garment.info.snap": (
        "Dans le jeu, un accessoire pend à un seul os : la tête pour les chapeaux, lunettes et accessoires d'oreille, "
        "l'avant-bras au poignet pour les montres et bracelets. Poser sur l'ancrage le met là où il se trouve "
        "d'habitude sur le corps freemode ; déplacez-le, tournez-le ou redimensionnez-le ensuite à la main. Une fois "
        "ajouté, il garde sa position par rapport à son ancrage."
    ),
    "garment.snap.subtext": (
        "Ancrage : {anchor}. Après l'avoir posé, déplacez l'accessoire à la main, puis continuez dans Prêt pour le jeu."
    ),
    "garment.done.snap": "Accessoire posé sur son ancrage ({anchor}) : {distance} cm, tourné de {turn}°.",
    "garment.next.snap": (
        "Suite : Poser sur l'ancrage dans Ajustement, puis déplacez l'accessoire à la main à sa place."
    ),
    "garment.why.not-prop": "Seuls les accessoires sont posés sur un ancrage.",
    "garment.why.prop-fix": "Les accessoires gardent leur forme : placez-les avec Poser sur l'ancrage et à la main.",
    "fit.why.prop": (
        "Les accessoires ne sont pas ajustés au corps et n'ont pas besoin de poids : ils bougent avec leur ancrage."
    ),
    "garment.marker-error.no-head": "Le corps n'a pas de tête sur laquelle poser l'accessoire.",
    "garment.marker-error.no-arm": "Le corps n'a pas de bras sur lequel poser l'accessoire.",
    "garment.finding.anchor-far": (
        "Le milieu de l'accessoire est à {distance} cm de son ancrage : posez-le ou rapprochez-le."
    ),
    "add.info.anchor": (
        "Une fois ajouté, l'accessoire pend à son os d'ancrage, placé d'après le squelette freemode de Durty Cloth "
        "Tool (issu de vos fichiers du jeu), et garde sa position par rapport à lui. Il n'a pas besoin de poids."
    ),
    "add.anchor.ready": "Pend à son ancrage ({anchor}) dans {name}.",
    "add.anchor.missing": "Ancrage : {anchor}. Ajouter au projet y suspend l'accessoire.",
    "add.why.no-anchor": "Le squelette de Durty Cloth Tool n'a pas d'os {bone} auquel suspendre l'accessoire.",
    "add.prop.missing": "L'accessoire ne pend pas encore à son ancrage. Ajouter au projet s'en charge.",
    "add.why.prop-skeleton": "Les accessoires ne vont pas sur le squelette : ils pendent à leur ancrage.",
    "garment.op.split": "Couper à la taille",
    "garment.op.split.desc": (
        "Couper la robe à la taille en un haut et une jupe : la jupe devient un vêtement à part pour l'emplacement "
        "Jambes"
    ),
    "garment.info.split": (
        "Une robe va dans le jeu comme un seul vêtement dans l'emplacement Haut, ou comme un haut et une jupe. Couper "
        "à la taille la coupe là où elle est la plus étroite au-dessus du bassin : la robe garde le haut, et un "
        "nouveau vêtement à son nom reçoit la jupe, préparé pour l'emplacement Jambes. Coupez après Ajuster sur "
        "gta.clothing, pour que les deux pièces gardent l'ajustement et ses poids, puis choisissez chaque pièce dans "
        "Configuration pour la terminer et l'ajouter."
    ),
    "garment.done.split": (
        "{name} coupée à la taille : {skirt} est la jupe, pour l'emplacement Jambes. Choisissez-la dans Configuration."
    ),
    "garment.why.not-dress": "Seule une robe se coupe à la taille.",
    "garment.why.split-nothing": "Rien ne se trouve d'un côté de la taille : vérifiez les marqueurs.",
    "garment.op.bridge": "Relier les poids des cuisses",
    "garment.op.bridge.desc": (
        "Répartir les poids de la jupe ou des pans du manteau entre les deux cuisses par-dessus le milieu, pour que le "
        "tissu entre les jambes ne se sépare pas"
    ),
    "garment.done.bridge": "Poids des cuisses de {count} sommets reliés d'une jambe à l'autre.",
    "garment.done.bridge.one": "Poids des cuisses de {count} sommet reliés d'une jambe à l'autre.",
    "garment.why.no-bridge": "Seuls les jupes, robes et manteaux longs sont reliés d'une jambe à l'autre.",
    "garment.why.no-leg-weights": (
        "Le vêtement n'a pas encore de poids des cuisses à relier. Ajustez-le sur gta.clothing ou transférez d'abord "
        "les poids."
    ),
    "garment.done.combine-walls": (
        "{count} matériaux combinés en une texture de {size} pixels, {density} pixels par centimètre sur le vêtement "
        "(la disposition utilise {used} %). {walls} faces n'avaient pas de place dans la carte UV (comme les flancs "
        "d'un export épais) : elles prennent la couleur du bord de pièce voisin."
    ),
    "garment.done.combine-sparse": (
        "La disposition combinée n'utilise que {used} % de la texture, le vêtement paraîtrait donc flou. Sa carte UV a "
        "des îlots sans place ou très éloignés : vérifiez-la, ou redépliez le vêtement, puis combinez à nouveau."
    ),
    "garment.why.uv-degenerate": "La carte UV du vêtement n'a de surface nulle part. Dépliez d'abord le vêtement.",
}
