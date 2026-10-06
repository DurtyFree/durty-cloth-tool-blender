# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2026 Schmid Software Solutions (https://schmid-software.de)
"""French (Français): the Custom Ped texts."""

TEXT = {
    # ---- the switch in the DCT tab --------------------------------------------------------------------
    "workspace.prop": "Travailler sur",
    "workspace.prop.desc": (
        "Ce qu'affiche l'onglet DCT : le vêtement lié dans Durty Cloth Tool, l'Ajustement de vêtements ou le Ped "
        "personnalisé"
    ),
    "workspace.clothing": "Vêtement lié",
    "workspace.clothing.desc": (
        "Le vêtement sélectionné dans Durty Cloth Tool : son aperçu en direct sur le ped et son modèle"
    ),
    "workspace.garment": "Ajustement de vêtements",
    "workspace.garment.desc": (
        "Rendre un vêtement de votre logiciel de vêtements prêt pour le jeu et l'ajouter à votre projet comme "
        "nouveau vêtement (expérimental)"
    ),
    "workspace.ped": "Ped personnalisé",
    "workspace.ped.desc": "Transformer votre propre personnage en ped personnalisé pour Durty Cloth Tool",
    # ---- the panel ------------------------------------------------------------------------------------
    "ped.panel": "Ped personnalisé",
    "ped.stage-title": "{number}. {title}",
    "ped.section.character": "Personnage",
    "ped.section.markers": "Marqueurs",
    "ped.section.rig": "Rig",
    "ped.section.check": "Vérification",
    "ped.section.send": "Création",
    "ped.status.none": "Aucun pour l'instant",
    "ped.status.vertices": "{count} sommets",
    "ped.status.rigging": "Rigging en cours",
    "ped.status.waiting": "Attend votre choix",
    "ped.status.ready": "Prêt",
    "ped.status.review": "À vérifier",
    "ped.status.not-rigged": "Non riggé",
    "ped.status.not-checked": "Non vérifié",
    "ped.status.no-problems": "Aucun problème",
    "ped.status.problems": "{count} points à examiner",
    "ped.status.problems.one": "{count} point à examiner",
    "ped.status.sent": "Créé",
    "ped.status.sending": "Création en cours",
    "ped.status.not-sent": "Non créé",
    "ped.status.markers": "{placed} sur {total}",
    "ped.privacy": (
        "Le rigging et la création du ped se font dans Durty Cloth Tool sur cet ordinateur, à partir de vos propres "
        "fichiers GTA V. Rien de votre personnage ne va à gta.clothing."
    ),
    # ---- the next step --------------------------------------------------------------------------------
    "ped.next.character": (
        "Sélectionnez les maillages de votre personnage dans la vue 3D et choisissez Utiliser la sélection."
    ),
    "ped.next.fix": "Ensuite : corrigez ce que signalent les vérifications sous Personnage.",
    "ped.next.markers": "Ensuite : placez les marqueurs sous Marqueurs. Le guide de clics montre chaque point.",
    "ped.next.marker-problems": "Ensuite : corrigez les marqueurs que nomme la liste sous Marqueurs.",
    "ped.next.connect": (
        "Ensuite : connectez-vous à Durty Cloth Tool (ci-dessus). Aucun projet n'a besoin d'être ouvert."
    ),
    "ped.next.template": "Ensuite : choisissez un modèle sous Rig.",
    "ped.next.rig": "Ensuite : Rigger dans Durty Cloth Tool sous Rig.",
    "ped.next.rigging": "Durty Cloth Tool rigge votre personnage. Blender reste utilisable pendant ce temps.",
    "ped.next.approve": (
        "Ensuite : vérifiez où Durty Cloth Tool a déplacé les marqueurs (en jaune), puis Appliquer le rig."
    ),
    "ped.next.check": "Ensuite : essayez les poses de test et Lancer les vérifications sous Vérification.",
    "ped.next.send": "Ensuite : nommez le ped et choisissez Créer le ped personnalisé.",
    "ped.next.sending": "Durty Cloth Tool attend votre choix : choisissez là-bas où créer le projet.",
    "ped.next.done": "Terminé : Durty Cloth Tool a créé le projet {name}. Lancez son build là-bas.",
    "ped.next.done-before": (
        "Terminé : Durty Cloth Tool a créé un projet à partir de ce personnage. Lancez son build là-bas."
    ),
    # ---- 1. Character ---------------------------------------------------------------------------------
    "ped.character.none": (
        "Sélectionnez tous les maillages de votre personnage (corps, tête, cheveux, yeux) dans la vue 3D, puis "
        "choisissez Utiliser la sélection."
    ),
    "ped.character.facts": "{vertices} sommets · {triangles} triangles · objets : {objects} · matériaux : {materials}",
    "ped.prop.character": "Personnage",
    "ped.prop.character.desc": "La collection qui contient les maillages de votre personnage",
    "ped.op.use-selected": "Utiliser la sélection",
    "ped.op.use-selected.desc": (
        "Utiliser les maillages sélectionnés comme personnage. S'ils ne sont pas dans une collection à eux, ils sont "
        "déplacés dans une nouvelle collection"
    ),
    "ped.done.use-selected": "{name} est votre personnage ({count} maillages).",
    "ped.done.use-selected.one": "{name} est votre personnage ({count} maillage).",
    "ped.check.none": "Le personnage n'a aucun maillage.",
    "ped.check.rigged": (
        "Le personnage est riggé. Utilisez Supprimer le rig sous Rig pour changer sa forme ou sa taille."
    ),
    "ped.check.rigged-changed": (
        "Une partie a été déplacée ou a reçu un modificateur après le rig. Annulez cela, ou supprimez le rig et riggez "
        "de nouveau."
    ),
    "ped.check.transforms": (
        "{count} maillages sont déplacés, tournés ou mis à l'échelle. Appliquez leurs transformations pour que le "
        "personnage garde sa forme."
    ),
    "ped.check.transforms.one": (
        "{count} maillage est déplacé, tourné ou mis à l'échelle. Appliquez ses transformations pour que le personnage "
        "garde sa forme."
    ),
    "ped.check.modifiers": (
        "{count} maillages ont des modificateurs ({names}). Appliquez-les pour que le rig voie ce que vous voyez."
    ),
    "ped.check.modifiers.one": (
        "{count} maillage a des modificateurs ({names}). Appliquez-les pour que le rig voie ce que vous voyez."
    ),
    "ped.check.old-rig": (
        "Le personnage est riggé sur {name}. Supprimez l'ancien rig : le personnage garde sa pose, et Depuis l'ancien "
        "rig peut encore placer les marqueurs sur ses articulations."
    ),
    "ped.check.shape-keys": (
        "{count} maillages ont des clés de forme, qui ne suivent pas le rig. Supprimez-les pour garder la forme que "
        "vous voyez."
    ),
    "ped.check.shape-keys.one": (
        "{count} maillage a des clés de forme, qui ne suivent pas le rig. Supprimez-les pour garder la forme que vous "
        "voyez."
    ),
    "ped.check.lying": "Le personnage semble couché (il est plus long que haut). Le redresser ?",
    "ped.check.upside-down": "Le personnage semble se tenir sur la tête. Le retourner ?",
    "ped.check.unit": (
        "Le personnage mesure {height} unités, il est donc probablement en {unit}. Le mettre à l'échelle pour qu'il "
        "mesure {metres} m ?"
    ),
    "ped.check.too-tall": (
        "Le personnage mesure {height} m. Il doit tenir dans un rayon de 3 m autour de l'origine : mettez-le à "
        "l'échelle."
    ),
    "ped.check.height-unusual": (
        "Le personnage mesure {height} m. Un ped de GTA V mesure environ 1,8 m : un personnage beaucoup plus petit ou "
        "plus grand peut bouger et entrer en collision de façon étrange dans le jeu."
    ),
    "ped.check.height": "Taille : {height} m",
    "ped.check.origin": "Le personnage se tient à {distance} m de l'origine. Déplacez-le à l'origine.",
    "ped.check.facing": (
        "Votre personnage doit être tourné vers vous dans la vue de face (Numpad 1), son côté gauche à votre droite. "
        "Est-ce le cas ?"
    ),
    "ped.check.facing-other": (
        "Les pieds semblent pointer {direction}. Votre personnage doit être tourné vers vous dans la vue de face "
        "(Numpad 1). Tournez-le, ou confirmez qu'il est tourné vers l'avant."
    ),
    "ped.check.facing-done": "Tourné vers l'avant",
    "ped.check.size-limit": (
        "{vertices} sommets et {triangles} triangles : un rig accepte au plus {max_vertices} sommets et "
        "{max_triangles} triangles. Décimez d'abord une copie du personnage."
    ),
    "ped.check.size-budget": (
        "{vertices} sommets. Un ped devrait en avoir au plus {budget} dans son niveau le plus détaillé, Durty Cloth "
        "Tool vous en avertira donc. Cela fonctionne quand même."
    ),
    "ped.check.size": "{vertices} sommets : convient pour un ped",
    "ped.unit.cm": "centimètres",
    "ped.unit.mm": "millimètres",
    "ped.unit.in": "pouces",
    "ped.direction.back": "vers l'arrière",
    "ped.direction.screen-right": "vers votre droite",
    "ped.direction.screen-left": "vers votre gauche",
    "ped.op.apply-transforms": "Appliquer les transformations",
    "ped.op.apply-transforms.desc": (
        "Intégrer à chaque maillage sa position, sa rotation et son échelle, sans changer son apparence"
    ),
    "ped.done.transforms": "Transformations de {count} maillages appliquées.",
    "ped.done.transforms.one": "Transformations de {count} maillage appliquées.",
    "ped.op.apply-modifiers": "Appliquer les modificateurs",
    "ped.op.apply-modifiers.desc": (
        "Appliquer chaque modificateur des maillages du personnage (sauf un modificateur Armature)"
    ),
    "ped.confirm.modifiers": (
        "Appliquer chaque modificateur des maillages du personnage ? Leurs réglages sont perdus ensuite."
    ),
    "ped.done.modifiers": "{count} modificateurs appliqués.",
    "ped.done.modifiers.one": "{count} modificateur appliqué.",
    "ped.op.remove-old-rig": "Supprimer l'ancien rig",
    "ped.op.remove-old-rig.desc": (
        "Détacher le personnage de l'armature avec laquelle il est venu : il garde sa pose actuelle, l'armature reste "
        "masquée"
    ),
    "ped.confirm.old-rig": (
        "Supprimer l'ancien rig ? Le personnage garde sa pose actuelle et perd les groupes de sommets de l'ancien rig. "
        "L'ancienne armature reste dans le fichier, masquée."
    ),
    "ped.done.old-rig": "Ancien rig supprimé ({name}). Depuis l'ancien rig peut encore utiliser ses articulations.",
    "ped.op.remove-shape-keys": "Supprimer les clés de forme",
    "ped.op.remove-shape-keys.desc": (
        "Supprimer les clés de forme des maillages du personnage, en gardant la forme qu'ils affichent"
    ),
    "ped.confirm.shape-keys": (
        "Supprimer toutes les clés de forme du personnage ? La forme que vous voyez maintenant reste."
    ),
    "ped.done.shape-keys": "Clés de forme de {count} maillages supprimées.",
    "ped.done.shape-keys.one": "Clés de forme de {count} maillage supprimées.",
    "ped.op.scale": "Mettre à l'échelle",
    "ped.op.scale.desc": "Mettre le personnage à l'échelle autour de l'origine, comme le fait un changement d'unité",
    "ped.op.scale-by": "Mettre à l'échelle × {factor}",
    "ped.confirm.scale": "Mettre le personnage à l'échelle × {factor} ?",
    "ped.done.scaled": "Personnage mis à l'échelle × {factor}.",
    "ped.op.turn": "Tourner",
    "ped.op.turn.desc": "Tourner le personnage par pas de 90 degrés",
    "ped.op.stand-up": "Redresser",
    "ped.op.stand-up-other": "Redresser dans l'autre sens",
    "ped.op.turn-over": "Retourner",
    "ped.op.turn-left": "Tourner de 90° à gauche",
    "ped.op.turn-right": "Tourner de 90° à droite",
    "ped.op.turn-around": "Tourner de 180°",
    "ped.confirm.turn": "Tourner le personnage ? Vous pouvez l'annuler avec Ctrl+Z.",
    "ped.done.turned": "Personnage tourné.",
    "ped.op.to-origin": "Déplacer à l'origine",
    "ped.op.to-origin.desc": "Déplacer le personnage pour qu'il se tienne au sol à l'origine",
    "ped.done.origin": "Le personnage se tient maintenant à l'origine.",
    "ped.op.confirm-facing": "Il est tourné vers l'avant",
    "ped.op.confirm-facing.desc": (
        "Confirmer que le personnage est tourné vers vous dans la vue de face, son côté gauche à votre droite"
    ),
    "ped.confirm.facing": (
        "Le personnage est-il tourné vers vous dans la vue de face (Numpad 1), sa main gauche à votre droite ?"
    ),
    "ped.heading.parts": "Parties ({count})",
    "ped.parts.subtext": (
        "Les cheveux, les yeux et les dents sont pondérés différemment, et les cheveux deviennent les cheveux du ped. "
        "Changez un rôle quand l'estimation est fausse."
    ),
    "ped.parts.guess": "Estimé : {role}",
    "ped.prop.role": "Rôle de la partie",
    "ped.prop.role.desc": "Ce qu'est ce maillage : cela décide comment il est pondéré et où il va dans le ped",
    "ped.role.auto": "Automatique",
    "ped.role.auto.desc": "Deviner le rôle d'après les noms du maillage et de ses matériaux",
    "ped.role.body": "Corps",
    "ped.role.body.desc": "La peau et les vêtements qui bougent avec le corps",
    "ped.role.head": "Tête et visage",
    "ped.role.head.desc": "La tête, le visage, les sourcils et les cils",
    "ped.role.hair": "Cheveux",
    "ped.role.hair.desc": "Les cheveux, les cartes de barbe et les autres poils qui bougent avec la tête",
    "ped.role.eyes": "Yeux",
    "ped.role.eyes.desc": "Les globes oculaires, déplacés par les os des yeux ou par la tête",
    "ped.role.teeth": "Dents",
    "ped.role.teeth.desc": "Les dents et la langue, déplacées par la tête",
    "ped.role.accessory": "Accessoire",
    "ped.role.accessory.desc": "Lunettes, bijoux et autres objets que porte le personnage",
    # ---- 2. Markers -----------------------------------------------------------------------------------
    "ped.heading.markers": "Marqueurs d'articulation",
    "info.ped-markers": (
        "Les marqueurs montrent à Durty Cloth Tool où se trouvent les articulations de votre personnage : à "
        "l'intérieur du corps, au milieu de chaque articulation. Les marqueurs gauches sont bleus, les droits orange, "
        "la gauche du personnage étant à votre droite dans la vue de face."
    ),
    "ped.markers.placed": "{placed} sur {total} placés",
    "ped.op.guide": "Guide de clics",
    "ped.op.guide.desc": (
        "Cliquer sur les points qu'une figure montre dans la vue 3D, l'un après l'autre ; les autres sont placés à "
        "partir d'eux"
    ),
    "ped.op.auto-markers": "Marqueurs automatiques",
    "ped.op.auto-markers.desc": "Placer chaque marqueur d'après la forme du personnage. Vérifiez-les ensuite",
    "ped.op.from-rig": "Depuis l'ancien rig",
    "ped.op.from-rig.desc": (
        "Placer les marqueurs sur les articulations de l'ancien rig du personnage (Mixamo, Unreal, Rigify, Character "
        "Creator ou VRM)"
    ),
    "ped.op.mirror": "Miroir",
    "ped.op.mirror.desc": "Copier les marqueurs d'un côté sur l'autre, en miroir par rapport au milieu du personnage",
    "ped.op.mirror-left": "Gauche vers droite",
    "ped.op.mirror-right": "Droite vers gauche",
    "ped.op.show": "Afficher",
    "ped.op.show-markers.desc": "Sélectionner ces marqueurs dans la vue 3D",
    "ped.prop.marker-size": "Taille des marqueurs",
    "ped.prop.marker-size.desc": "La taille à laquelle les sphères des marqueurs sont affichées",
    "ped.prop.follow": "Entraîner coudes et genoux",
    "ped.prop.follow.desc": (
        "Quand vous déplacez un marqueur de poignet, d'épaule, de cheville ou de hanche, le coude ou le genou entre "
        "les deux suit le membre"
    ),
    "ped.done.auto-markers": (
        "Marqueurs placés d'après la forme du personnage. Vérifiez chacun et déplacez ceux qui sont mal placés."
    ),
    "ped.done.from-rig": (
        "Marqueurs placés sur les articulations du rig {rig}. Vérifiez le menton et le sommet de la tête."
    ),
    "ped.done.mirrored": "Marqueurs reproduits en miroir.",
    "ped.rig-kind.mixamo": "Mixamo",
    "ped.rig-kind.unreal": "Unreal",
    "ped.rig-kind.rigify": "Rigify",
    "ped.rig-kind.cc": "Character Creator",
    "ped.rig-kind.vrm": "VRM",
    "ped.marker-error.too-small": (
        "Le personnage est trop petit ou n'est pas debout : Marqueurs automatiques n'a trouvé aucune personne."
    ),
    "ped.marker-error.guide-incomplete": (
        "Le guide de clics a besoin de tous ses points avant de pouvoir placer les autres."
    ),
    "ped.marker-error.no-rig": (
        "Le personnage n'a pas d'ancien rig aux noms d'os connus (Mixamo, Unreal, Rigify, Character Creator ou VRM)."
    ),
    "ped.marker-note.arms": (
        "Les bras n'ont pas pu être distingués du corps : vérifiez les épaules, les coudes et les poignets."
    ),
    "ped.marker-note.legs": (
        "Les jambes n'ont pas pu être distinguées : vérifiez les hanches, les genoux et les chevilles."
    ),
    "ped.marker-note.neck": "Le cou était difficile à trouver : vérifiez le cou, le menton et la poitrine.",
    "ped.marker-problem.missing": "Marqueurs manquants : {names}.",
    "ped.marker-problem.side": (
        "Du mauvais côté : {names}. La gauche du personnage doit être en +X, à votre droite dans la vue de face."
    ),
    "ped.marker-problem.order": "Pas dans l'ordre de haut en bas : {names}.",
    "ped.marker-problem.asymmetric": "Les membres gauches et droits diffèrent de plus de 30 % : {names}.",
    "ped.marker-problem.outside": "Hors du personnage : {names}.",
    "ped.marker.headTop": "Sommet de la tête",
    "ped.marker.chin": "Menton",
    "ped.marker.neck": "Cou",
    "ped.marker.chest": "Poitrine",
    "ped.marker.pelvis": "Bassin",
    "ped.marker.shoulderL": "Épaule gauche",
    "ped.marker.shoulderR": "Épaule droite",
    "ped.marker.elbowL": "Coude gauche",
    "ped.marker.elbowR": "Coude droit",
    "ped.marker.wristL": "Poignet gauche",
    "ped.marker.wristR": "Poignet droit",
    "ped.marker.hipL": "Hanche gauche",
    "ped.marker.hipR": "Hanche droite",
    "ped.marker.kneeL": "Genou gauche",
    "ped.marker.kneeR": "Genou droit",
    "ped.marker.ankleL": "Cheville gauche",
    "ped.marker.ankleR": "Cheville droite",
    "ped.marker.toeL": "Orteils gauches",
    "ped.marker.toeR": "Orteils droits",
    "ped.guide.title": "Guide de clics : point {index} sur {total}",
    "ped.guide.keys": (
        "Clic : placer le point. Clic droit : revenir d'un point. Molette et bouton du milieu : vue. Échap : arrêter."
    ),
    "ped.guide.headTop": "Cliquez sur le sommet de la tête.",
    "ped.guide.chin": "Cliquez sur la pointe du menton.",
    "ped.guide.shoulderL": "Cliquez sur l'articulation de l'épaule gauche (à votre droite dans la vue de face).",
    "ped.guide.shoulderR": "Cliquez sur l'articulation de l'épaule droite (à votre gauche).",
    "ped.guide.wristL": "Cliquez sur le milieu du poignet gauche.",
    "ped.guide.wristR": "Cliquez sur le milieu du poignet droit.",
    "ped.guide.hipL": "Cliquez sur l'articulation de la hanche gauche, là où la jambe rejoint le corps.",
    "ped.guide.hipR": "Cliquez sur l'articulation de la hanche droite.",
    "ped.guide.ankleL": "Cliquez sur le milieu de la cheville gauche.",
    "ped.guide.ankleR": "Cliquez sur le milieu de la cheville droite.",
    "ped.guide.toeL": "Cliquez sur le pied gauche, là où les orteils se plient.",
    "ped.guide.toeR": "Cliquez sur le pied droit, là où les orteils se plient.",
    "ped.guide.finish": "Tous les points sont placés. Appuyez sur Entrée.",
    "ped.guide.missed": "Ce clic a manqué le personnage. Cliquez dessus.",
    "ped.guide.done": (
        "Tous les points sont placés ; le cou, la poitrine, le bassin, les coudes et les genoux ont été placés à "
        "partir d'eux. Vérifiez-les et déplacez ceux qui sont mal placés."
    ),
    # ---- 3. Rig ---------------------------------------------------------------------------------------
    "ped.heading.template": "Modèle",
    "info.ped-template": (
        "Le ped GTA V installé à partir duquel votre ped est construit : son squelette, sa démarche, sa voix et les "
        "formes de son corps. Choisissez-en un qui ressemble à votre personnage : du même genre et d'une carrure "
        "proche."
    ),
    "ped.prop.template": "Modèle",
    "ped.prop.template.desc": "Le ped installé dont votre personnage reçoit le squelette",
    "ped.prop.gender": "Genre",
    "ped.gender.any": "Tous",
    "ped.gender.any.desc": "Lister les modèles des deux genres",
    "ped.gender.male.desc": "Lister les modèles masculins",
    "ped.gender.female.desc": "Lister les modèles féminins",
    "ped.prop.show-all": "Tout afficher",
    "ped.prop.show-all.desc": (
        "Lister aussi les peds freemode, joueur, cinématique et histoire, pas seulement les peds ambiants"
    ),
    "ped.template.choose": "Choisir un modèle",
    "ped.template.recommended": "{model} (recommandé)",
    "ped.template.facts": "{facts}",
    "ped.templates.loading": "Durty Cloth Tool lit vos fichiers du jeu (plusieurs secondes la première fois).",
    "ped.templates.refresh": "Choisissez Actualiser pour lister les modèles installés avec votre jeu.",
    "ped.templates.none": "Aucun modèle ne correspond. Activez Tout afficher ou choisissez un autre genre.",
    "ped.templates.truncated": "Durty Cloth Tool liste les {count} premiers peds correspondants.",
    "ped.templates.count.any.ambient": "{count} peds ambiants",
    "ped.templates.count.any.ambient.one": "{count} ped ambiant",
    "ped.templates.count.male.ambient": "{count} peds ambiants masculins",
    "ped.templates.count.male.ambient.one": "{count} ped ambiant masculin",
    "ped.templates.count.female.ambient": "{count} peds ambiants féminins",
    "ped.templates.count.female.ambient.one": "{count} ped ambiant féminin",
    "ped.templates.count.any.all": "{count} peds",
    "ped.templates.count.any.all.one": "{count} ped",
    "ped.templates.count.male.all": "{count} peds masculins",
    "ped.templates.count.male.all.one": "{count} ped masculin",
    "ped.templates.count.female.all": "{count} peds féminins",
    "ped.templates.count.female.all.one": "{count} ped féminin",
    "ped.group.ambient": "ambiant",
    "ped.group.freemode": "freemode",
    "ped.group.player": "joueur",
    "ped.group.cutscene": "cinématique",
    "ped.group.story": "histoire",
    "ped.layout.packed": "empaqueté",
    "ped.layout.streamed": "streamé",
    "ped.op.refresh": "Actualiser",
    "ped.op.refresh.desc": "Redemander à Durty Cloth Tool les modèles installés avec votre jeu",
    "ped.op.use-template": "Utiliser le modèle",
    "ped.op.use-template.desc": "Utiliser ce ped installé comme modèle",
    "ped.op.choose-template": "Rechercher un modèle",
    "ped.op.choose-template.desc": "Rechercher les peds installés par leur nom et en utiliser un comme modèle",
    "ped.op.use-template-named": "Utiliser {template}",
    "ped.rights.title": "Vos droits sur ce personnage",
    "ped.rights.text": (
        "Ne convertissez que des personnages que vous avez créés vous-même ou que vous avez le droit d'utiliser dans "
        "des ressources GTA V (par exemple avec une licence qui autorise la modification et la redistribution). Les "
        "personnages tirés d'autres jeux, de films ou d'autres créateurs ne peuvent généralement pas être convertis ni "
        "partagés. Vous êtes responsable des personnages que vous convertissez et publiez."
    ),
    "ped.rights.check": "J'ai créé ce personnage ou j'ai le droit de le convertir et de l'utiliser",
    "ped.rights.done": "Vous avez confirmé vos droits sur ce personnage.",
    "ped.op.rig": "Rigger dans Durty Cloth Tool",
    "ped.op.rig.desc": (
        "Durty Cloth Tool ajuste le squelette du modèle à vos marqueurs et calcule les poids et la pose de repos du "
        "jeu, à partir de vos propres fichiers du jeu"
    ),
    "ped.op.rig-again": "Rigger de nouveau",
    "ped.op.cancel-rig.desc": "Arrêter le rig dans Durty Cloth Tool",
    "ped.rig.waiting": "En attente du démarrage du rig par Durty Cloth Tool.",
    "ped.rig.cancelling": "Annulation du rig.",
    "ped.rig.working": "Rigging en cours",
    "ped.rig.progress": "{stage} ({percent} %)",
    "ped.stage.template": "Lecture du modèle",
    "ped.stage.markers": "Vérification des marqueurs",
    "ped.stage.skeleton": "Ajustement du squelette",
    "ped.stage.weights": "Transfert des poids",
    "ped.stage.rest": "Conversion vers la pose de repos du jeu",
    "ped.stage.report": "Rédaction du rapport",
    "ped.prop.refine": "Affiner les marqueurs",
    "ped.prop.refine.desc": (
        "Durty Cloth Tool déplace les marqueurs au milieu des membres et du corps, et vous montre où"
    ),
    "ped.prop.fingers": "Doigts",
    "ped.fingers.off": "Suivre la main",
    "ped.fingers.off.desc": "Les doigts bougent avec la main, comme une moufle",
    "ped.fingers.auto": "Automatique",
    "ped.fingers.auto.desc": "Pondérer les doigts d'après la main du modèle",
    "ped.prop.face": "Visage",
    "ped.face.off": "Suivre la tête",
    "ped.face.off.desc": "Le visage bouge avec la tête",
    "ped.face.auto": "Automatique",
    "ped.face.auto.desc": "Pondérer le visage d'après le visage du modèle, pour les expressions",
    "ped.prop.roll": "Os de torsion",
    "ped.prop.roll.desc": (
        "Pondérer les os de torsion des bras et des jambes, qui empêchent les poignets et les cuisses de s'écraser"
    ),
    "ped.prop.helpers": "Os d'assistance",
    "ped.prop.helpers.desc": "Pondérer les os d'assistance du modèle, comme l'est son propre corps",
    "ped.prop.rest": "Forme de repos",
    "ped.rest.volume": "Garder le volume",
    "ped.rest.volume.desc": (
        "Amener le personnage dans la pose de repos en gardant le volume des épaules et des hanches"
    ),
    "ped.rest.linear": "Exacte",
    "ped.rest.linear.desc": (
        "Amener le personnage dans la pose de repos pour que le skinning du jeu redonne exactement votre pose"
    ),
    "ped.result.ready": "Prêt (confiance {percent} %)",
    "ped.result.review": "À vérifier (confiance {percent} %)",
    "ped.result.markers": "({names})",
    "ped.result.moved": "Durty Cloth Tool a déplacé {count} marqueurs au milieu du corps (en jaune dans la vue 3D) :",
    "ped.result.moved.one": (
        "Durty Cloth Tool a déplacé {count} marqueur au milieu du corps (en jaune dans la vue 3D) :"
    ),
    "ped.result.move": "{marker} : {cm} cm",
    "ped.result.subtext": (
        "Appliquer le rig construit l'armature et donne aux maillages leurs poids et la pose de repos du jeu. Votre "
        "personnage garde son apparence, et Ctrl+Z l'annule."
    ),
    "ped.result.proxy": "Les poids ont été calculés sur une copie simplifiée de ce grand maillage.",
    "ped.op.apply-rig": "Appliquer le rig",
    "ped.op.apply-rig.desc": (
        "Construire l'armature à partir du rig et donner aux maillages ses poids et la pose de repos du jeu ; le "
        "personnage garde son apparence"
    ),
    "ped.op.use-refined": "Utiliser ces marqueurs",
    "ped.op.use-refined.desc": "Déplacer vos marqueurs là où Durty Cloth Tool les a mis",
    "ped.op.discard-rig": "Abandonner",
    "ped.op.discard-rig.desc": "Jeter ce rig sans l'appliquer",
    "ped.done.applied": "Rig appliqué : l'armature {name} a {bones} os.",
    "ped.done.refined": "Vos marqueurs sont maintenant là où Durty Cloth Tool les a mis.",
    "ped.rigged.line": "Riggé à partir de {template} ({bones} os)",
    "ped.op.previous-rig": "Rig précédent",
    "ped.op.previous-rig.desc": "Échanger le rig appliqué contre celui appliqué avant lui",
    "ped.done.previous": "Le rig précédent est de retour.",
    "ped.op.remove-rig": "Supprimer le rig",
    "ped.op.remove-rig.desc": "Retirer le rig : le personnage redevient comme avant le premier rig",
    "ped.confirm.remove-rig": (
        "Supprimer le rig ? Les armatures disparaissent et le personnage redevient comme avant le premier rig."
    ),
    "ped.done.removed": "Rig supprimé. Le personnage est comme avant le rigging.",
    "ped.warning.marker_offset": (
        "{count} marqueurs étaient à plus de 2 cm du milieu du corps (jusqu'à {value} mm). Vérifiez-les."
    ),
    "ped.warning.marker_offset.one": (
        "{count} marqueur était à plus de 2 cm du milieu du corps ({value} mm). Vérifiez-le."
    ),
    "ped.warning.asymmetric_markers": (
        "Les marqueurs gauches et droits diffèrent de plus de 5 %. Vérifiez les deux côtés."
    ),
    "ped.warning.proportion_out_of_range": (
        "Certaines proportions sont loin de celles du modèle. Un modèle à la carrure plus proche bouge mieux."
    ),
    "ped.warning.ragdoll_mismatch": (
        "La taille de ce personnage est loin de celle de son modèle. Dans le jeu, les balles et les chutes utilisent "
        "les formes du corps du modèle, les tirs peuvent donc manquer le personnage ou toucher à côté. Choisissez un "
        "modèle plus proche, ou testez dans le jeu avant de publier."
    ),
    "ped.warning.low_coverage": (
        "Seule une partie du personnage correspondait au corps du modèle. Vérifiez les poids dans les poses de test."
    ),
    "ped.warning.inpainted_large": (
        "Beaucoup de poids ont été complétés à partir de leurs voisins. Vérifiez les poses de test."
    ),
    "ped.warning.non_deforming_moved": "Certains poids ont été retirés d'os qui ne déplacent jamais le maillage.",
    "ped.warning.empty_rows_refilled": "{count} sommets n'avaient pas de poids et ont pris ceux de leurs voisins.",
    "ped.warning.empty_rows_refilled.one": "{count} sommet n'avait pas de poids et a pris ceux de ses voisins.",
    "ped.warning.floating_parts": "{count} parties isolées ont été rattachées à l'os le plus proche.",
    "ped.warning.floating_parts.one": "{count} partie isolée a été rattachée à l'os le plus proche.",
    "ped.warning.rest_strain": (
        "Certains triangles se replient dans la pose de repos du jeu. Regardez les épaules et les hanches dans Pose de "
        "repos du jeu."
    ),
    "ped.warning.fingers_fallback": "Les doigts bougent avec la main.",
    "ped.warning.other": "Durty Cloth Tool a signalé {code}.",
    "ped.suggest": (
        "{template} est plus proche des proportions de votre personnage. Utilisez-le et riggez de nouveau pour un "
        "meilleur ajustement."
    ),
    "ped.refusal.marker_missing": "Des marqueurs manquent.",
    "ped.refusal.marker_invalid": "Certains marqueurs sont inutilisables. Placez-les de nouveau sur le personnage.",
    "ped.refusal.marker_degenerate": "Certains marqueurs sont superposés.",
    "ped.refusal.marker_side": (
        "La gauche et la droite sont inversées. La gauche du personnage doit être en +X : vérifiez qu'il est tourné "
        "vers l'avant."
    ),
    "ped.refusal.not_upright": "Le personnage n'est pas debout, ou sa tête est sous son cou.",
    "ped.refusal.limb_length": (
        "Un membre est beaucoup plus court ou plus long que celui du modèle. Vérifiez ces marqueurs."
    ),
    "ped.refusal.asymmetric": "Les membres gauches et droits diffèrent de plus de 30 %.",
    "ped.refusal.pose_unsupported": (
        "Une jambe est trop pliée ou trop écartée. Mettez le personnage debout bien droit, en A-pose ou en T-pose."
    ),
    "ped.refusal.marker_outside_body": "Ces marqueurs se trouvent hors du personnage.",
    "ped.refusal.mesh_invalid": (
        "Durty Cloth Tool n'a pas pu lire le maillage (vide, ou fait surtout de triangles plats)."
    ),
    "ped.refusal.mesh_too_large": (
        "Le personnage a trop de sommets ou de triangles pour un rig. Décimez d'abord une copie."
    ),
    "ped.refusal.options_invalid": "Durty Cloth Tool a refusé les options du rig. Mettez le module à jour.",
    "ped.refusal.template_invalid": "Durty Cloth Tool ne peut pas utiliser ce modèle. Choisissez-en un autre.",
    "ped.refusal.template_not_found": "Ce modèle n'est pas installé. Actualisez la liste et choisissez-en un autre.",
    "ped.refusal.game_required": (
        "Durty Cloth Tool a besoin de votre dossier GTA V. Définissez-le dans les options de Durty Cloth Tool."
    ),
    "ped.refusal.fit_invalid": (
        "Le rig obtenu est cassé. Vérifiez les marqueurs par rapport au personnage et riggez de nouveau."
    ),
    "ped.refusal.other": "Durty Cloth Tool a refusé le rig ({code}).",
    # ---- 4. Check -------------------------------------------------------------------------------------
    "ped.heading.poses": "Poses de test",
    "info.ped-poses": (
        "De simples flexions par nom d'os, pour voir comment les poids déplacent le personnage. Ce ne sont pas des "
        "animations du jeu ; de petits plis aux extrêmes sont normaux."
    ),
    "ped.pose.yours": "Votre pose",
    "ped.pose.rest": "Pose de repos du jeu",
    "ped.pose.arms_up": "Bras levés",
    "ped.pose.arms_forward": "Bras en avant",
    "ped.pose.squat": "Accroupi",
    "ped.pose.walk": "Pas de marche",
    "ped.pose.twist": "Torsion",
    "ped.op.pose": "Pose",
    "ped.op.pose.desc": "Afficher le personnage dans cette pose",
    "ped.op.run-checks": "Lancer les vérifications",
    "ped.op.run-checks.desc": (
        "Vérifier les poids, l'armature et les maillages par rapport au rig, ainsi que les poses de test"
    ),
    "ped.op.show-finding.desc": "Sélectionner les sommets que concerne ce point",
    "ped.done.checks": (
        "Lancer les vérifications a relevé {count} points à examiner ; rien que Durty Cloth Tool refuserait."
    ),
    "ped.done.checks.one": (
        "Lancer les vérifications a relevé {count} point à examiner ; rien que Durty Cloth Tool refuserait."
    ),
    "ped.done.checks-refused": "Lancer les vérifications a relevé {count} problèmes que Durty Cloth Tool refuserait.",
    "ped.done.checks-refused.one": (
        "Lancer les vérifications a relevé {count} problème que Durty Cloth Tool refuserait."
    ),
    "ped.local.none": "Aucun problème trouvé.",
    "ped.local.unweighted": "{count} sommets n'ont pas de poids. Durty Cloth Tool les refuse : pondérez-les.",
    "ped.local.unweighted.one": "{count} sommet n'a pas de poids. Durty Cloth Tool le refuse : pondérez-le.",
    "ped.local.too-many": "{count} sommets ont plus de quatre os. Le jeu garde les quatre plus forts.",
    "ped.local.too-many.one": "{count} sommet a plus de quatre os. Le jeu garde les quatre plus forts.",
    "ped.local.non-deforming": "{count} sommets sont pondérés sur des os qui ne déplacent jamais le maillage.",
    "ped.local.non-deforming.one": "{count} sommet est pondéré sur des os qui ne déplacent jamais le maillage.",
    "ped.local.unknown-groups": "Les groupes de sommets qui ne sont pas des os ({names}) sont laissés de côté.",
    "ped.local.armature-changed": (
        "{count} os ont été déplacés ou tournés après le rig ({names}). Annulez cela ou riggez de nouveau : les os "
        "gardent la rotation du modèle."
    ),
    "ped.local.armature-changed.one": (
        "{count} os a été déplacé ou tourné après le rig ({names}). Annulez cela ou riggez de nouveau : les os gardent "
        "la rotation du modèle."
    ),
    "ped.local.mesh-changed": (
        "Les maillages ont changé après le rig (sommets ajoutés ou supprimés). Riggez de nouveau."
    ),
    "ped.local.strain": "{count} sommets s'étirent ou s'écrasent beaucoup dans {pose}.",
    "ped.local.strain.one": "{count} sommet s'étire ou s'écrase beaucoup dans {pose}.",
    "ped.local.hint": (
        "De petits plis dans les poses extrêmes sont normaux. Pour des plis plus grands, déplacez un marqueur et "
        "riggez de nouveau."
    ),
    # ---- 5. Send --------------------------------------------------------------------------------------
    "ped.prop.name": "Nom du ped",
    "ped.prop.name.desc": "Le nom que Durty Cloth Tool affiche pour le ped",
    "ped.prop.model": "Nom du modèle",
    "ped.prop.model.desc": (
        "Le nom du nouveau ped dans le jeu : une lettre minuscule, puis 2 à 31 lettres minuscules, chiffres ou tirets "
        "bas"
    ),
    "ped.prop.ragdoll": "Corps ragdoll",
    "ped.ragdoll.template": "Comme le modèle",
    "ped.ragdoll.template.desc": "Le corps ragdoll partagé qu'utilise le modèle",
    "ped.ragdoll.fred": "Homme standard",
    "ped.ragdoll.fred.desc": "Le corps ragdoll partagé de la plupart des peds masculins",
    "ped.ragdoll.wilma": "Femme standard",
    "ped.ragdoll.wilma.desc": "Le corps ragdoll partagé de la plupart des peds féminins",
    "ped.ragdoll.fred-large": "Homme corpulent",
    "ped.ragdoll.fred-large.desc": "Le corps ragdoll partagé des peds masculins corpulents",
    "ped.ragdoll.wilma-large": "Femme corpulente",
    "ped.ragdoll.wilma-large.desc": "Le corps ragdoll partagé des peds féminins corpulents",
    "ped.ragdoll.subtext": (
        "Les balles, les chutes et le ragdoll utilisent les formes de ce corps dans le jeu. Choisissez-en un corpulent "
        "pour un personnage beaucoup plus grand."
    ),
    "ped.texture.too-large": "L'image {name} dépasse 4096 pixels de côté. Durty Cloth Tool la refuse.",
    "ped.texture.not-multiple-of-four": (
        "La largeur ou la hauteur de l'image {name} n'est pas divisible par quatre. Durty Cloth Tool la "
        "refuse."
    ),
    "ped.texture.non-power-of-two": (
        "La taille de l'image {name} n'est pas une puissance de deux (comme 1024 ou 2048). Elle fonctionne, "
        "mais ces tailles rendent le mieux."
    ),
    "ped.op.send": "Créer le ped personnalisé",
    "ped.op.send.desc": (
        "Exporter le personnage riggé dans la pose de repos du jeu et l'envoyer à Durty Cloth Tool, qui crée un "
        "nouveau projet de ped personnalisé une fois que vous confirmez là-bas"
    ),
    "ped.op.cancel-send.desc": "Retirer le personnage tant que Durty Cloth Tool pose encore la question",
    "ped.send.subtext": (
        "Durty Cloth Tool affiche le ped avec ses vérifications et demande où créer le projet. Rien n'est créé tant "
        "que vous n'y choisissez pas Créer le projet."
    ),
    "ped.send.waiting": "Personnage envoyé ({size} MiB). Choisissez Créer le projet dans Durty Cloth Tool.",
    "ped.send.withdrawing": "Retrait du personnage.",
    "ped.send.withdrawn": "Retiré : Durty Cloth Tool n'a rien créé.",
    "ped.send.created": "Durty Cloth Tool a créé le projet {name} avec le ped {model} à partir de {template}.",
    "ped.send.created-late": (
        "Durty Cloth Tool a finalement créé le projet {name} avec le ped {model} : Créer y a été choisi juste "
        "au moment où le personnage a été retiré."
    ),
    "ped.send.findings": "Vérifications de Durty Cloth Tool ({count}) :",
    "ped.send.next": (
        "Vérifiez le comportement du ped dans Durty Cloth Tool (type de ped, démarche, voix), puis lancez le build du "
        "projet."
    ),
    "ped.finding.rig-mismatch": (
        "Le squelette n'est ni celui du modèle ni celui du rig : un os a été déplacé ou tourné. Appliquez de nouveau "
        "le rig, ou riggez de nouveau."
    ),
    "ped.finding.ped-budget": "Plus de sommets qu'un ped ne devrait en avoir dans son niveau le plus détaillé.",
    "ped.finding.ped-ragdoll-mismatch": (
        "La taille du personnage est loin de celle du corps ragdoll du modèle : les tirs et les chutes dans le jeu "
        "utilisent les formes du corps du modèle."
    ),
    "ped.finding.ped-rest-strain": "Le rig a replié certains triangles dans la pose de repos du jeu.",
    # ---- why something cannot run -----------------------------------------------------------------------
    "ped.why.select-meshes": "Sélectionnez d'abord les maillages de votre personnage.",
    "ped.why.no-character": "Choisissez d'abord votre personnage sous Personnage.",
    "ped.why.object-mode": "Passez d'abord en Mode Objet.",
    "ped.why.rigged": "Le personnage est riggé. Supprimez le rig pour le modifier.",
    "ped.why.no-markers": "Placez d'abord les marqueurs.",
    "ped.why.guide-running": "Le guide de clics est en cours.",
    "ped.why.view3d": "Lancez le guide de clics depuis la barre latérale de la vue 3D.",
    "ped.why.checks": "Corrigez d'abord ce que signalent les vérifications sous Personnage.",
    "ped.why.markers": "Placez d'abord tous les marqueurs.",
    "ped.why.connect": "Connectez-vous à Durty Cloth Tool pour choisir un modèle et rigger.",
    "ped.why.template": "Choisissez d'abord un modèle.",
    "ped.why.rights": "Confirmez d'abord vos droits sur ce personnage.",
    "ped.why.rigging": "Un rig est en cours dans Durty Cloth Tool.",
    "ped.why.not-rigging": "Aucun rig n'est en cours.",
    "ped.why.no-result": "Il n'y a aucun rig à appliquer. Riggez d'abord le personnage.",
    "ped.why.no-previous": "Il n'y a pas de rig précédent.",
    "ped.why.not-rigged": "Riggez d'abord le personnage.",
    "ped.why.mesh-changed": (
        "Les maillages du personnage ont changé depuis que vous avez demandé ce rig. Riggez de nouveau."
    ),
    "ped.why.vertex-count": (
        "{name} change son nombre de sommets dans un modificateur. Appliquez d'abord ses modificateurs."
    ),
    "ped.why.modifiers-shape-keys": (
        "{name} a des clés de forme, ses modificateurs ne peuvent donc pas être appliqués. Supprimez-les d'abord."
    ),
    "ped.why.export-failed": (
        "L'exportateur glTF de Blender n'a pas écrit le personnage. Son journal Info contient les détails."
    ),
    "ped.why.model": (
        "Le nom du modèle est une lettre minuscule, puis 2 à 31 lettres minuscules, chiffres ou tirets bas."
    ),
    "ped.why.model-game": (
        "Les noms qui commencent par {prefix} appartiennent aux peds du jeu. Choisissez-en un autre, par exemple "
        "{suggestion}."
    ),
    "ped.why.name": "Donnez un nom au ped.",
    "ped.why.transforms-first": "Applique d'abord les transformations.",
    "ped.why.refused-checks": (
        "Lancer les vérifications a relevé des problèmes que Durty Cloth Tool refuserait. Corrigez-les d'abord."
    ),
    "ped.why.textures": "Une image est trop grande ou sa taille n'est pas divisible par quatre. Corrigez-la d'abord.",
    "ped.why.sending": "Un ped personnalisé est en cours d'envoi.",
    "ped.why.not-sending": "Rien n'est en cours d'envoi.",
    "ped.invalid": "Le module n'a pas pu préparer cette demande : {detail}",
    # ---- plans and Durty Cloth Tool's answers -----------------------------------------------------------
    "ped.plan.rig": "Le rigging est inclus dans Durty Cloth Tool Ultimate.",
    "ped.plan.add": "Créer un projet de ped personnalisé nécessite Durty Cloth Tool Advanced ou Ultimate.",
    "ped.error.rig-busy": "Durty Cloth Tool rigge un autre personnage. Réessayez quand il aura terminé.",
    "ped.error.rig-cancelled": "Le rig a été annulé.",
    "ped.error.rig-refused": "Durty Cloth Tool n'a pas pu rigger le personnage :",
    "ped.error.dct-too-old": (
        "Ce Durty Cloth Tool ne crée pas encore de peds personnalisés depuis Blender. Mettez Durty Cloth Tool à jour."
    ),
    "ped.error.rig-disconnected": "La connexion à Durty Cloth Tool a pris fin pendant le rig. Riggez de nouveau.",
    "ped.error.rig-timeout": "Durty Cloth Tool n'a pas terminé le rig à temps. Riggez de nouveau.",
    "ped.error.add-busy": (
        "Durty Cloth Tool est occupé avec un autre ped personnalisé ou un build. Réessayez quand il aura terminé."
    ),
    "ped.error.add-denied": (
        "Annulé dans Durty Cloth Tool. Choisissez à nouveau Créer le ped personnalisé quand vous êtes prêt."
    ),
    "ped.error.model-rejected": (
        "Durty Cloth Tool n'a pas pu faire un ped à partir du personnage. Ses vérifications ci-dessous indiquent "
        "pourquoi."
    ),
    "ped.error.save-failed": (
        "Durty Cloth Tool n'a pas pu créer le projet. Choisissez un autre dossier et renvoyez le personnage."
    ),
    "ped.error.add-disconnected": (
        "La connexion à Durty Cloth Tool a pris fin avant sa réponse. Choisissez à nouveau Créer le ped personnalisé."
    ),
    "ped.error.add-timeout": (
        "Durty Cloth Tool n'a pas répondu à temps. Choisissez à nouveau Créer le ped personnalisé."
    ),
    "ped.error.add-unanswered": "Durty Cloth Tool n'a pas confirmé le retrait. Vérifiez sa liste de projets.",
    # ---- protocol errors --------------------------------------------------------------------------------
    "error.template-not-found": "Ce modèle n'est pas installé. Actualisez la liste et choisissez-en un autre.",
    "error.mesh-too-large": "Le personnage a trop de sommets ou de triangles. Décimez d'abord une copie.",
    "error.rig-refused": "Durty Cloth Tool n'a pas pu rigger le personnage.",
    "error.upload-incomplete": "Le personnage n'est pas arrivé complet dans Durty Cloth Tool. Renvoyez-le.",
}
