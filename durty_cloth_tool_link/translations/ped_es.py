# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2026 Schmid Software Solutions (https://schmid-software.de)
"""Spanish (Español): the Custom Ped texts."""

TEXT = {
    # ---- the switch in the DCT tab --------------------------------------------------------------------
    "workspace.prop": "Trabajar en",
    "workspace.prop.desc": (
        "Qué muestra la pestaña DCT: la prenda vinculada en Durty Cloth Tool, el Ajuste de prendas o el Ped "
        "personalizado"
    ),
    "workspace.clothing": "Prenda vinculada",
    "workspace.clothing.desc": (
        "La prenda seleccionada en Durty Cloth Tool: su vista previa en directo en el ped y su modelo"
    ),
    "workspace.garment": "Ajuste de prendas",
    "workspace.garment.desc": (
        "Dejar una prenda de tu programa de ropa lista para el juego y añadirla a tu proyecto como prenda nueva "
        "(experimental)"
    ),
    "workspace.ped": "Ped personalizado",
    "workspace.ped.desc": "Convertir tu propio personaje en un ped personalizado para Durty Cloth Tool",
    # ---- the panel ------------------------------------------------------------------------------------
    "ped.panel": "Ped personalizado",
    "ped.stage-title": "{number}. {title}",
    "ped.section.character": "Personaje",
    "ped.section.markers": "Marcadores",
    "ped.section.rig": "Rig",
    "ped.section.check": "Comprobación",
    "ped.section.send": "Creación",
    "ped.status.none": "Aún ninguno",
    "ped.status.vertices": "{count} vértices",
    "ped.status.rigging": "Haciendo el rig",
    "ped.status.waiting": "Esperándote",
    "ped.status.ready": "Listo",
    "ped.status.review": "Necesita revisión",
    "ped.status.not-rigged": "Sin rig",
    "ped.status.not-checked": "Sin comprobar",
    "ped.status.no-problems": "Sin problemas",
    "ped.status.problems": "{count} hallazgos",
    "ped.status.problems.one": "{count} hallazgo",
    "ped.status.sent": "Creado",
    "ped.status.sending": "Creando",
    "ped.status.not-sent": "Sin crear",
    "ped.status.markers": "{placed} de {total}",
    "ped.privacy": (
        "El rig y la creación del ped se hacen en Durty Cloth Tool en este equipo, a partir de tus propios archivos de "
        "GTA V. Nada de tu personaje va a gta.clothing."
    ),
    # ---- the next step --------------------------------------------------------------------------------
    "ped.next.character": "Selecciona las mallas de tu personaje en la vista 3D y elige Usar selección.",
    "ped.next.fix": "Siguiente: corrige lo que indican las comprobaciones de Personaje.",
    "ped.next.markers": "Siguiente: coloca los marcadores en Marcadores. La guía de clics muestra cada punto.",
    "ped.next.marker-problems": "Siguiente: corrige los marcadores que indica la lista de Marcadores.",
    "ped.next.connect": "Siguiente: conéctate con Durty Cloth Tool (arriba). No hace falta tener un proyecto abierto.",
    "ped.next.template": "Siguiente: elige una plantilla en Rig.",
    "ped.next.rig": "Siguiente: Hacer el rig en Durty Cloth Tool, en Rig.",
    "ped.next.rigging": (
        "Durty Cloth Tool está haciendo el rig de tu personaje. Mientras tanto puedes seguir usando Blender."
    ),
    "ped.next.approve": (
        "Siguiente: comprueba dónde movió Durty Cloth Tool los marcadores (en amarillo) y luego Aplicar rig."
    ),
    "ped.next.check": "Siguiente: mira las poses de prueba y usa Ejecutar comprobaciones en Comprobación.",
    "ped.next.send": "Siguiente: ponle nombre al ped y elige Crear ped personalizado.",
    "ped.next.sending": "Durty Cloth Tool te espera: elige allí dónde crear el proyecto.",
    "ped.next.done": "Hecho: Durty Cloth Tool creó el proyecto {name}. Compílalo allí.",
    "ped.next.done-before": "Hecho: Durty Cloth Tool creó un proyecto a partir de este personaje. Compílalo allí.",
    # ---- 1. Character ---------------------------------------------------------------------------------
    "ped.character.none": (
        "Selecciona todas las mallas de tu personaje (cuerpo, cabeza, pelo, ojos) en la vista 3D y luego elige Usar "
        "selección."
    ),
    "ped.character.facts": (
        "{vertices} vértices · {triangles} triángulos · objetos: {objects} · materiales: {materials}"
    ),
    "ped.prop.character": "Personaje",
    "ped.prop.character.desc": "La colección que contiene las mallas de tu personaje",
    "ped.op.use-selected": "Usar selección",
    "ped.op.use-selected.desc": (
        "Usar las mallas seleccionadas como tu personaje. Si no están en una colección propia, se mueven a una nueva"
    ),
    "ped.done.use-selected": "{name} es tu personaje ({count} mallas).",
    "ped.done.use-selected.one": "{name} es tu personaje ({count} malla).",
    "ped.check.none": "El personaje no tiene mallas.",
    "ped.check.rigged": "El personaje ya tiene rig. Usa Quitar rig en Rig para cambiar su forma o su tamaño.",
    "ped.check.rigged-changed": (
        "Una parte se movió o recibió un modificador después del rig. Deshazlo, o quita el rig y vuelve a hacerlo."
    ),
    "ped.check.transforms": (
        "{count} mallas están movidas, giradas o escaladas. Aplica sus transformaciones para que el personaje conserve "
        "su forma."
    ),
    "ped.check.transforms.one": (
        "{count} malla está movida, girada o escalada. Aplica sus transformaciones para que el personaje conserve su "
        "forma."
    ),
    "ped.check.modifiers": (
        "{count} mallas tienen modificadores ({names}). Aplícalos para que el rig vea lo mismo que tú."
    ),
    "ped.check.modifiers.one": (
        "{count} malla tiene modificadores ({names}). Aplícalos para que el rig vea lo mismo que tú."
    ),
    "ped.check.old-rig": (
        "El personaje usa el rig {name}. Quita el rig antiguo: el personaje conserva su pose, y Desde el rig antiguo "
        "todavía puede colocar los marcadores en sus articulaciones."
    ),
    "ped.check.shape-keys": (
        "{count} mallas tienen formas clave, que no siguen el rig. Quítalas para conservar la forma que ves."
    ),
    "ped.check.shape-keys.one": (
        "{count} malla tiene formas clave, que no siguen el rig. Quítalas para conservar la forma que ves."
    ),
    "ped.check.lying": "El personaje parece estar tumbado (es más largo que alto). ¿Ponerlo de pie?",
    "ped.check.upside-down": "El personaje parece estar cabeza abajo. ¿Darle la vuelta?",
    "ped.check.unit": (
        "El personaje mide {height} unidades, así que probablemente está en {unit}. ¿Escalarlo a {metres} m?"
    ),
    "ped.check.too-tall": "El personaje mide {height} m. Debe caber a menos de 3 m del origen: escálalo.",
    "ped.check.height-unusual": (
        "El personaje mide {height} m. Un ped de GTA V mide unos 1,8 m: los personajes mucho más bajos o más altos "
        "pueden moverse y chocar de forma extraña en el juego."
    ),
    "ped.check.height": "Altura: {height} m",
    "ped.check.origin": "El personaje está a {distance} m del origen. Muévelo al origen.",
    "ped.check.facing": (
        "Tu personaje debe mirar hacia la vista frontal (Numpad 1), con su lado izquierdo a tu derecha. ¿Es así?"
    ),
    "ped.check.facing-other": (
        "Los pies parecen apuntar {direction}. Tu personaje debe mirar hacia la vista frontal (Numpad 1). Gíralo, o "
        "confirma que mira al frente."
    ),
    "ped.check.facing-done": "Mira al frente",
    "ped.check.size-limit": (
        "{vertices} vértices y {triangles} triángulos: un rig admite como máximo {max_vertices} vértices y "
        "{max_triangles} triángulos. Reduce primero una copia del personaje con Diezmar."
    ),
    "ped.check.size-budget": (
        "{vertices} vértices. Un ped debería tener como máximo {budget} en su nivel de detalle más alto, así que Durty "
        "Cloth Tool avisará de ello. Aun así funciona."
    ),
    "ped.check.size": "{vertices} vértices: bien para un ped",
    "ped.unit.cm": "centímetros",
    "ped.unit.mm": "milímetros",
    "ped.unit.in": "pulgadas",
    "ped.direction.back": "hacia atrás",
    "ped.direction.screen-right": "hacia tu derecha",
    "ped.direction.screen-left": "hacia tu izquierda",
    "ped.op.apply-transforms": "Aplicar transformaciones",
    "ped.op.apply-transforms.desc": "Integrar en cada malla su posición, rotación y escala, sin cambiar cómo se ve",
    "ped.done.transforms": "Se aplicaron las transformaciones de {count} mallas.",
    "ped.done.transforms.one": "Se aplicaron las transformaciones de {count} malla.",
    "ped.op.apply-modifiers": "Aplicar modificadores",
    "ped.op.apply-modifiers.desc": (
        "Aplicar todos los modificadores de las mallas del personaje (salvo un modificador Esqueleto)"
    ),
    "ped.confirm.modifiers": (
        "¿Aplicar todos los modificadores de las mallas del personaje? Después sus ajustes desaparecen."
    ),
    "ped.done.modifiers": "Se aplicaron {count} modificadores.",
    "ped.done.modifiers.one": "Se aplicó {count} modificador.",
    "ped.op.remove-old-rig": "Quitar rig antiguo",
    "ped.op.remove-old-rig.desc": (
        "Separar el personaje del esqueleto con el que venía: conserva su pose actual y el esqueleto queda oculto"
    ),
    "ped.confirm.old-rig": (
        "¿Quitar el rig antiguo? El personaje conserva su pose actual y pierde los grupos de vértices del rig antiguo. "
        "El esqueleto antiguo se queda en el archivo, oculto."
    ),
    "ped.done.old-rig": "Se quitó el rig antiguo ({name}). Desde el rig antiguo todavía puede usar sus articulaciones.",
    "ped.op.remove-shape-keys": "Quitar formas clave",
    "ped.op.remove-shape-keys.desc": (
        "Quitar las formas clave de las mallas del personaje, conservando la forma que muestran"
    ),
    "ped.confirm.shape-keys": "¿Quitar todas las formas clave del personaje? Se conserva la forma que ves ahora.",
    "ped.done.shape-keys": "Se quitaron las formas clave de {count} mallas.",
    "ped.done.shape-keys.one": "Se quitaron las formas clave de {count} malla.",
    "ped.op.scale": "Escalar",
    "ped.op.scale.desc": "Escalar el personaje respecto al origen, como lo hace un cambio de unidades",
    "ped.op.scale-by": "Escalar por {factor}",
    "ped.confirm.scale": "¿Escalar el personaje por {factor}?",
    "ped.done.scaled": "Se escaló el personaje por {factor}.",
    "ped.op.turn": "Girar",
    "ped.op.turn.desc": "Girar el personaje en pasos de 90 grados",
    "ped.op.stand-up": "Poner de pie",
    "ped.op.stand-up-other": "Poner de pie hacia el otro lado",
    "ped.op.turn-over": "Dar la vuelta",
    "ped.op.turn-left": "Girar 90° a la izquierda",
    "ped.op.turn-right": "Girar 90° a la derecha",
    "ped.op.turn-around": "Girar 180°",
    "ped.confirm.turn": "¿Girar el personaje? Puedes deshacerlo con Ctrl+Z.",
    "ped.done.turned": "Se giró el personaje.",
    "ped.op.to-origin": "Mover al origen",
    "ped.op.to-origin.desc": "Mover el personaje para que quede de pie sobre el suelo en el origen",
    "ped.done.origin": "El personaje está ahora en el origen.",
    "ped.op.confirm-facing": "Sí, mira al frente",
    "ped.op.confirm-facing.desc": (
        "Confirmar que el personaje mira hacia la vista frontal, con su lado izquierdo a tu derecha"
    ),
    "ped.confirm.facing": "¿El personaje te mira en la vista frontal (Numpad 1), con su mano izquierda a tu derecha?",
    "ped.heading.parts": "Partes ({count})",
    "ped.parts.subtext": (
        "El pelo, los ojos y los dientes se ponderan de otra forma, y el pelo pasa a ser el pelo del ped. Cambia un "
        "rol si la estimación es errónea."
    ),
    "ped.parts.guess": "Estimado: {role}",
    "ped.prop.role": "Rol de la parte",
    "ped.prop.role.desc": "Qué es esta malla: decide cómo se pondera y dónde va en el ped",
    "ped.role.auto": "Automática",
    "ped.role.auto.desc": "Estimar el rol a partir de los nombres de la malla y de sus materiales",
    "ped.role.body": "Cuerpo",
    "ped.role.body.desc": "Piel y ropa que se mueven con el cuerpo",
    "ped.role.head": "Cabeza y cara",
    "ped.role.head.desc": "La cabeza, la cara, las cejas y las pestañas",
    "ped.role.hair": "Pelo",
    "ped.role.hair.desc": "Pelo, barbas hechas con tarjetas (cards) y otro pelo que se mueve con la cabeza",
    "ped.role.eyes": "Ojos",
    "ped.role.eyes.desc": "Los globos oculares, que mueven los huesos de los ojos o la cabeza",
    "ped.role.teeth": "Dientes",
    "ped.role.teeth.desc": "Los dientes y la lengua, que mueve la cabeza",
    "ped.role.accessory": "Accesorio",
    "ped.role.accessory.desc": "Gafas, joyas y otras cosas que lleva el personaje",
    # ---- 2. Markers -----------------------------------------------------------------------------------
    "ped.heading.markers": "Marcadores de articulación",
    "info.ped-markers": (
        "Los marcadores muestran a Durty Cloth Tool dónde están las articulaciones de tu personaje: dentro del cuerpo, "
        "en el centro de cada articulación. Los marcadores izquierdos son azules y los derechos naranjas; el lado "
        "izquierdo del personaje está a tu derecha en la vista frontal."
    ),
    "ped.markers.placed": "{placed} de {total} colocados",
    "ped.op.guide": "Guía de clics",
    "ped.op.guide.desc": (
        "Hacer clic, uno tras otro, en los puntos que muestra una figura en la vista 3D; los demás se colocan a partir "
        "de ellos"
    ),
    "ped.op.auto-markers": "Marcadores automáticos",
    "ped.op.auto-markers.desc": "Colocar todos los marcadores a partir de la forma del personaje. Revísalos después",
    "ped.op.from-rig": "Desde el rig antiguo",
    "ped.op.from-rig.desc": (
        "Colocar los marcadores en las articulaciones del rig antiguo del personaje (Mixamo, Unreal, Rigify, Character "
        "Creator o VRM)"
    ),
    "ped.op.mirror": "Reflejar",
    "ped.op.mirror.desc": "Copiar los marcadores de un lado al otro, reflejados respecto al centro del personaje",
    "ped.op.mirror-left": "Izquierda a derecha",
    "ped.op.mirror-right": "Derecha a izquierda",
    "ped.op.show": "Mostrar",
    "ped.op.show-markers.desc": "Seleccionar estos marcadores en la vista 3D",
    "ped.prop.marker-size": "Tamaño de marcador",
    "ped.prop.marker-size.desc": "El tamaño con que se dibujan las esferas de los marcadores",
    "ped.prop.follow": "Mover codos y rodillas con la extremidad",
    "ped.prop.follow.desc": (
        "Al mover un marcador de muñeca, hombro, tobillo o cadera, el codo o la rodilla que hay entre ellos se mueve "
        "con la extremidad"
    ),
    "ped.done.auto-markers": (
        "Se colocaron los marcadores a partir de la forma del personaje. Revisa cada uno y mueve los que no estén en "
        "su sitio."
    ),
    "ped.done.from-rig": (
        "Se colocaron los marcadores en las articulaciones del rig {rig}. Revisa la barbilla y la parte superior de la "
        "cabeza."
    ),
    "ped.done.mirrored": "Se reflejaron los marcadores.",
    "ped.rig-kind.mixamo": "Mixamo",
    "ped.rig-kind.unreal": "Unreal",
    "ped.rig-kind.rigify": "Rigify",
    "ped.rig-kind.cc": "Character Creator",
    "ped.rig-kind.vrm": "VRM",
    "ped.marker-error.too-small": (
        "El personaje es demasiado pequeño o no está de pie: Marcadores automáticos no encontró ninguna persona."
    ),
    "ped.marker-error.guide-incomplete": "La guía de clics necesita todos sus puntos antes de poder colocar los demás.",
    "ped.marker-error.no-rig": (
        "El personaje no tiene un rig antiguo con nombres de hueso conocidos (Mixamo, Unreal, Rigify, Character "
        "Creator o VRM)."
    ),
    "ped.marker-note.arms": (
        "No se pudieron distinguir los brazos del cuerpo: revisa los hombros, los codos y las muñecas."
    ),
    "ped.marker-note.legs": "No se pudieron distinguir las piernas: revisa las caderas, las rodillas y los tobillos.",
    "ped.marker-note.neck": "Costó encontrar el cuello: revisa el cuello, la barbilla y el pecho.",
    "ped.marker-problem.missing": "Faltan marcadores: {names}.",
    "ped.marker-problem.side": (
        "En el lado equivocado: {names}. El lado izquierdo del personaje debe estar en +X, a tu derecha en la vista "
        "frontal."
    ),
    "ped.marker-problem.order": "No están en orden de la cabeza hacia abajo: {names}.",
    "ped.marker-problem.asymmetric": "Las extremidades izquierdas y derechas difieren en más del 30 %: {names}.",
    "ped.marker-problem.outside": "Fuera del personaje: {names}.",
    "ped.marker.headTop": "Parte superior de la cabeza",
    "ped.marker.chin": "Barbilla",
    "ped.marker.neck": "Cuello",
    "ped.marker.chest": "Pecho",
    "ped.marker.pelvis": "Pelvis",
    "ped.marker.shoulderL": "Hombro izquierdo",
    "ped.marker.shoulderR": "Hombro derecho",
    "ped.marker.elbowL": "Codo izquierdo",
    "ped.marker.elbowR": "Codo derecho",
    "ped.marker.wristL": "Muñeca izquierda",
    "ped.marker.wristR": "Muñeca derecha",
    "ped.marker.hipL": "Cadera izquierda",
    "ped.marker.hipR": "Cadera derecha",
    "ped.marker.kneeL": "Rodilla izquierda",
    "ped.marker.kneeR": "Rodilla derecha",
    "ped.marker.ankleL": "Tobillo izquierdo",
    "ped.marker.ankleR": "Tobillo derecho",
    "ped.marker.toeL": "Dedos del pie izquierdo",
    "ped.marker.toeR": "Dedos del pie derecho",
    "ped.guide.title": "Guía de clics: punto {index} de {total}",
    "ped.guide.keys": (
        "Clic: colocar el punto. Clic derecho: volver un punto atrás. Rueda y botón central del ratón: vista. Esc: "
        "detener."
    ),
    "ped.guide.headTop": "Haz clic en la parte superior de la cabeza.",
    "ped.guide.chin": "Haz clic en la punta de la barbilla.",
    "ped.guide.shoulderL": "Haz clic en la articulación del hombro izquierdo (a tu derecha en la vista frontal).",
    "ped.guide.shoulderR": "Haz clic en la articulación del hombro derecho (a tu izquierda).",
    "ped.guide.wristL": "Haz clic en el centro de la muñeca izquierda.",
    "ped.guide.wristR": "Haz clic en el centro de la muñeca derecha.",
    "ped.guide.hipL": "Haz clic en la articulación de la cadera izquierda, donde la pierna se une al cuerpo.",
    "ped.guide.hipR": "Haz clic en la articulación de la cadera derecha.",
    "ped.guide.ankleL": "Haz clic en el centro del tobillo izquierdo.",
    "ped.guide.ankleR": "Haz clic en el centro del tobillo derecho.",
    "ped.guide.toeL": "Haz clic en el pie izquierdo, donde se doblan los dedos.",
    "ped.guide.toeR": "Haz clic en el pie derecho, donde se doblan los dedos.",
    "ped.guide.finish": "Todos los puntos colocados. Pulsa Intro.",
    "ped.guide.missed": "Ese clic no tocó al personaje. Haz clic sobre él.",
    "ped.guide.done": (
        "Todos los puntos colocados; el cuello, el pecho, la pelvis, los codos y las rodillas se colocaron a partir de "
        "ellos. Revísalos y mueve los que no estén en su sitio."
    ),
    # ---- 3. Rig ---------------------------------------------------------------------------------------
    "ped.heading.template": "Plantilla",
    "info.ped-template": (
        "El ped de GTA V instalado a partir del que se crea tu ped: su esqueleto, su forma de moverse, su voz y las "
        "formas de su cuerpo. Elige uno parecido a tu personaje: del mismo género y de complexión similar."
    ),
    "ped.prop.template": "Plantilla",
    "ped.prop.template.desc": "El ped instalado cuyo esqueleto recibe tu personaje",
    "ped.prop.gender": "Género",
    "ped.gender.any": "Cualquiera",
    "ped.gender.any.desc": "Mostrar plantillas de ambos géneros",
    "ped.gender.male.desc": "Mostrar plantillas masculinas",
    "ped.gender.female.desc": "Mostrar plantillas femeninas",
    "ped.prop.show-all": "Mostrar todas",
    "ped.prop.show-all.desc": (
        "Mostrar también los peds freemode, de jugador, de cinemáticas y de la historia, no solo los ambientales"
    ),
    "ped.template.choose": "Elegir una plantilla",
    "ped.template.recommended": "{model} (recomendada)",
    "ped.template.facts": "{facts}",
    "ped.templates.loading": "Durty Cloth Tool está leyendo tus archivos del juego (varios segundos la primera vez).",
    "ped.templates.refresh": "Elige Actualizar para ver las plantillas instaladas con tu juego.",
    "ped.templates.none": "Ninguna plantilla coincide. Activa Mostrar todas o elige otro género.",
    "ped.templates.truncated": "Durty Cloth Tool muestra los {count} primeros peds que coinciden.",
    "ped.templates.count.any.ambient": "{count} peds ambientales",
    "ped.templates.count.any.ambient.one": "{count} ped ambiental",
    "ped.templates.count.male.ambient": "{count} peds ambientales masculinos",
    "ped.templates.count.male.ambient.one": "{count} ped ambiental masculino",
    "ped.templates.count.female.ambient": "{count} peds ambientales femeninos",
    "ped.templates.count.female.ambient.one": "{count} ped ambiental femenino",
    "ped.templates.count.any.all": "{count} peds",
    "ped.templates.count.any.all.one": "{count} ped",
    "ped.templates.count.male.all": "{count} peds masculinos",
    "ped.templates.count.male.all.one": "{count} ped masculino",
    "ped.templates.count.female.all": "{count} peds femeninos",
    "ped.templates.count.female.all.one": "{count} ped femenino",
    "ped.group.ambient": "ambiental",
    "ped.group.freemode": "freemode",
    "ped.group.player": "jugador",
    "ped.group.cutscene": "cinemática",
    "ped.group.story": "historia",
    "ped.layout.packed": "empaquetado",
    "ped.layout.streamed": "en streaming",
    "ped.op.refresh": "Actualizar",
    "ped.op.refresh.desc": "Volver a pedir a Durty Cloth Tool las plantillas instaladas con tu juego",
    "ped.op.use-template": "Usar plantilla",
    "ped.op.use-template.desc": "Usar este ped instalado como plantilla",
    "ped.op.choose-template": "Buscar plantilla",
    "ped.op.choose-template.desc": "Buscar por nombre los peds instalados y usar uno como plantilla",
    "ped.op.use-template-named": "Usar {template}",
    "ped.rights.title": "Tus derechos sobre este personaje",
    "ped.rights.text": (
        "Convierte solo personajes que hayas creado tú o que tengas permiso para usar en recursos de GTA V (por "
        "ejemplo, con una licencia que permita modificarlos y redistribuirlos). Los personajes sacados de otros "
        "juegos, de películas o de otros creadores normalmente no se pueden convertir ni compartir. Eres responsable "
        "de los personajes que conviertes y publicas."
    ),
    "ped.rights.check": "He creado este personaje o tengo los derechos para convertirlo y usarlo",
    "ped.rights.done": "Confirmaste tus derechos sobre este personaje.",
    "ped.op.rig": "Hacer el rig en Durty Cloth Tool",
    "ped.op.rig.desc": (
        "Durty Cloth Tool ajusta el esqueleto de la plantilla a tus marcadores y calcula los pesos y la pose de reposo "
        "del juego, a partir de tus propios archivos del juego"
    ),
    "ped.op.rig-again": "Volver a hacer el rig",
    "ped.op.cancel-rig.desc": "Detener el rig en Durty Cloth Tool",
    "ped.rig.waiting": "Esperando a que Durty Cloth Tool empiece el rig.",
    "ped.rig.cancelling": "Cancelando el rig.",
    "ped.rig.working": "Haciendo el rig",
    "ped.rig.progress": "{stage} ({percent} %)",
    "ped.stage.template": "Leyendo la plantilla",
    "ped.stage.markers": "Comprobando los marcadores",
    "ped.stage.skeleton": "Ajustando el esqueleto",
    "ped.stage.weights": "Transfiriendo los pesos",
    "ped.stage.rest": "Pasando a la pose de reposo del juego",
    "ped.stage.report": "Escribiendo el informe",
    "ped.prop.refine": "Afinar marcadores",
    "ped.prop.refine.desc": (
        "Durty Cloth Tool mueve los marcadores al centro de las extremidades y del cuerpo, y te muestra dónde"
    ),
    "ped.prop.fingers": "Dedos",
    "ped.fingers.off": "Moverse con la mano",
    "ped.fingers.off.desc": "Los dedos se mueven con la mano, como en una manopla",
    "ped.fingers.auto": "Automática",
    "ped.fingers.auto.desc": "Ponderar los dedos a partir de la mano de la plantilla",
    "ped.prop.face": "Cara",
    "ped.face.off": "Moverse con la cabeza",
    "ped.face.off.desc": "La cara se mueve con la cabeza",
    "ped.face.auto": "Automática",
    "ped.face.auto.desc": "Ponderar la cara a partir de la cara de la plantilla, para las expresiones",
    "ped.prop.roll": "Huesos de torsión",
    "ped.prop.roll.desc": (
        "Ponderar los huesos de torsión de brazos y piernas, que evitan que las muñecas y los muslos se aplasten"
    ),
    "ped.prop.helpers": "Huesos auxiliares",
    "ped.prop.helpers.desc": "Ponderar los huesos auxiliares de la plantilla, como lo está su propio cuerpo",
    "ped.prop.rest": "Forma en reposo",
    "ped.rest.volume": "Conservar volumen",
    "ped.rest.volume.desc": (
        "Llevar el personaje a la pose de reposo de modo que hombros y caderas conserven su volumen"
    ),
    "ped.rest.linear": "Exacta",
    "ped.rest.linear.desc": (
        "Llevar el personaje a la pose de reposo de modo que la deformación por huesos del juego reproduzca "
        "exactamente tu pose"
    ),
    "ped.result.ready": "Listo (confianza {percent} %)",
    "ped.result.review": "Necesita revisión (confianza {percent} %)",
    "ped.result.markers": "({names})",
    "ped.result.moved": "Durty Cloth Tool movió {count} marcadores al centro del cuerpo (en amarillo en la vista 3D):",
    "ped.result.moved.one": (
        "Durty Cloth Tool movió {count} marcador al centro del cuerpo (en amarillo en la vista 3D):"
    ),
    "ped.result.move": "{marker}: {cm} cm",
    "ped.result.subtext": (
        "Aplicar rig crea el esqueleto y da a las mallas sus pesos y la pose de reposo del juego. Tu personaje "
        "conserva su aspecto, y Ctrl+Z lo deshace."
    ),
    "ped.result.proxy": "Los pesos se calcularon sobre una copia simplificada de esta malla grande.",
    "ped.op.apply-rig": "Aplicar rig",
    "ped.op.apply-rig.desc": (
        "Crear el esqueleto a partir del rig y dar a las mallas sus pesos y la pose de reposo del juego; el personaje "
        "conserva su aspecto"
    ),
    "ped.op.use-refined": "Usar estos marcadores",
    "ped.op.use-refined.desc": "Mover tus marcadores a donde los puso Durty Cloth Tool",
    "ped.op.discard-rig": "Descartar",
    "ped.op.discard-rig.desc": "Desechar este rig sin aplicarlo",
    "ped.done.applied": "Se aplicó el rig: el esqueleto {name} tiene {bones} huesos.",
    "ped.done.refined": "Tus marcadores están ahora donde los puso Durty Cloth Tool.",
    "ped.rigged.line": "Rig a partir de {template} ({bones} huesos)",
    "ped.op.previous-rig": "Rig anterior",
    "ped.op.previous-rig.desc": "Intercambiar el rig aplicado por el que se aplicó antes",
    "ped.done.previous": "Se recuperó el rig anterior.",
    "ped.op.remove-rig": "Quitar rig",
    "ped.op.remove-rig.desc": "Quitar el rig: el personaje queda como estaba antes del primer rig",
    "ped.confirm.remove-rig": (
        "¿Quitar el rig? Los esqueletos se eliminan y el personaje queda como estaba antes del primer rig."
    ),
    "ped.done.removed": "Se quitó el rig. El personaje está como antes del rig.",
    "ped.warning.marker_offset": (
        "{count} marcadores estaban a más de 2 cm del centro del cuerpo (hasta {value} mm). Revísalos."
    ),
    "ped.warning.marker_offset.one": (
        "{count} marcador estaba a más de 2 cm del centro del cuerpo ({value} mm). Revísalo."
    ),
    "ped.warning.asymmetric_markers": (
        "Los marcadores izquierdos y derechos difieren en más del 5 %. Revisa ambos lados."
    ),
    "ped.warning.proportion_out_of_range": (
        "Algunas proporciones se alejan mucho de las de la plantilla. Una plantilla de complexión más parecida se "
        "mueve mejor."
    ),
    "ped.warning.ragdoll_mismatch": (
        "La altura de este personaje se aleja mucho de la de su plantilla. En el juego, las balas y las caídas usan "
        "las formas del cuerpo de la plantilla, así que los impactos pueden fallar o dar al lado del modelo. Elige una "
        "plantilla más parecida, o pruébalo en el juego antes de publicarlo."
    ),
    "ped.warning.low_coverage": (
        "Solo una parte del personaje coincidió con el cuerpo de la plantilla. Revisa los pesos en las poses de prueba."
    ),
    "ped.warning.inpainted_large": "Muchos pesos se rellenaron a partir de sus vecinos. Revisa las poses de prueba.",
    "ped.warning.non_deforming_moved": "Algunos pesos se quitaron de huesos que nunca mueven la malla.",
    "ped.warning.empty_rows_refilled": "{count} vértices no tenían pesos y tomaron los de sus vecinos.",
    "ped.warning.empty_rows_refilled.one": "{count} vértice no tenía pesos y tomó los de sus vecinos.",
    "ped.warning.floating_parts": "{count} partes sueltas se unieron al hueso más cercano.",
    "ped.warning.floating_parts.one": "{count} parte suelta se unió al hueso más cercano.",
    "ped.warning.rest_strain": (
        "Algunos triángulos se pliegan en la pose de reposo del juego. Mira los hombros y las caderas en Pose de "
        "reposo del juego."
    ),
    "ped.warning.fingers_fallback": "Los dedos se mueven con la mano.",
    "ped.warning.other": "Durty Cloth Tool informó {code}.",
    "ped.suggest": (
        "{template} se parece más a las proporciones de tu personaje. Úsala y vuelve a hacer el rig para un mejor "
        "ajuste."
    ),
    "ped.refusal.marker_missing": "Faltan marcadores.",
    "ped.refusal.marker_invalid": "Algunos marcadores no se pueden usar. Vuelve a colocarlos sobre el personaje.",
    "ped.refusal.marker_degenerate": "Algunos marcadores están uno encima de otro.",
    "ped.refusal.marker_side": (
        "La izquierda y la derecha están intercambiadas. El lado izquierdo del personaje debe estar en +X: comprueba "
        "que mira al frente."
    ),
    "ped.refusal.not_upright": "El personaje no está de pie, o su cabeza está por debajo del cuello.",
    "ped.refusal.limb_length": (
        "Una extremidad es mucho más corta o más larga que la de la plantilla. Revisa estos marcadores."
    ),
    "ped.refusal.asymmetric": "Las extremidades izquierdas y derechas difieren en más del 30 %.",
    "ped.refusal.pose_unsupported": (
        "Una pierna está demasiado doblada o abierta. Pon el personaje de pie y recto, en A-pose o en T-pose."
    ),
    "ped.refusal.marker_outside_body": "Estos marcadores están fuera del personaje.",
    "ped.refusal.mesh_invalid": (
        "Durty Cloth Tool no pudo leer la malla (vacía, o con casi todos los triángulos planos)."
    ),
    "ped.refusal.mesh_too_large": (
        "El personaje tiene demasiados vértices o triángulos para un rig. Reduce primero una copia con Diezmar."
    ),
    "ped.refusal.options_invalid": "Durty Cloth Tool rechazó las opciones del rig. Actualiza el complemento.",
    "ped.refusal.template_invalid": "Durty Cloth Tool no puede usar esta plantilla. Elige otra.",
    "ped.refusal.template_not_found": "Esta plantilla no está instalada. Actualiza la lista y elige otra.",
    "ped.refusal.game_required": (
        "Durty Cloth Tool necesita tu carpeta de GTA V. Configúrala en los ajustes de Durty Cloth Tool."
    ),
    "ped.refusal.fit_invalid": (
        "El rig salió roto. Comprueba los marcadores sobre el personaje y vuelve a hacer el rig."
    ),
    "ped.refusal.other": "Durty Cloth Tool rechazó el rig ({code}).",
    # ---- 4. Check -------------------------------------------------------------------------------------
    "ped.heading.poses": "Poses de prueba",
    "info.ped-poses": (
        "Flexiones sencillas por nombre de hueso para ver cómo mueven los pesos al personaje. No son animaciones del "
        "juego; es normal que aparezcan pequeños pliegues en los extremos."
    ),
    "ped.pose.yours": "Tu pose",
    "ped.pose.rest": "Pose de reposo del juego",
    "ped.pose.arms_up": "Brazos arriba",
    "ped.pose.arms_forward": "Brazos hacia delante",
    "ped.pose.squat": "Sentadilla",
    "ped.pose.walk": "Paso al caminar",
    "ped.pose.twist": "Torsión",
    "ped.op.pose": "Pose",
    "ped.op.pose.desc": "Mostrar el personaje en esta pose",
    "ped.op.run-checks": "Ejecutar comprobaciones",
    "ped.op.run-checks.desc": "Comprobar los pesos, el esqueleto y las mallas respecto al rig, y las poses de prueba",
    "ped.op.show-finding.desc": "Seleccionar los vértices a los que se refiere este hallazgo",
    "ped.done.checks": (
        "Ejecutar comprobaciones encontró {count} cosas que revisar; nada que Durty Cloth Tool rechazaría."
    ),
    "ped.done.checks.one": (
        "Ejecutar comprobaciones encontró {count} cosa que revisar; nada que Durty Cloth Tool rechazaría."
    ),
    "ped.done.checks-refused": "Ejecutar comprobaciones encontró {count} problemas que Durty Cloth Tool rechazaría.",
    "ped.done.checks-refused.one": "Ejecutar comprobaciones encontró {count} problema que Durty Cloth Tool rechazaría.",
    "ped.local.none": "No se encontraron problemas.",
    "ped.local.unweighted": "{count} vértices no tienen peso. Durty Cloth Tool los rechaza: asígnales pesos.",
    "ped.local.unweighted.one": "{count} vértice no tiene peso. Durty Cloth Tool lo rechaza: asígnale pesos.",
    "ped.local.too-many": "{count} vértices tienen más de cuatro huesos. El juego conserva los cuatro más fuertes.",
    "ped.local.too-many.one": "{count} vértice tiene más de cuatro huesos. El juego conserva los cuatro más fuertes.",
    "ped.local.non-deforming": "{count} vértices tienen pesos de huesos que nunca mueven la malla.",
    "ped.local.non-deforming.one": "{count} vértice tiene pesos de huesos que nunca mueven la malla.",
    "ped.local.unknown-groups": "Los grupos de vértices que no son huesos ({names}) se omiten.",
    "ped.local.armature-changed": (
        "{count} huesos se movieron o giraron después del rig ({names}). Deshazlo o vuelve a hacer el rig: los huesos "
        "conservan la rotación de la plantilla."
    ),
    "ped.local.armature-changed.one": (
        "{count} hueso se movió o giró después del rig ({names}). Deshazlo o vuelve a hacer el rig: los huesos "
        "conservan la rotación de la plantilla."
    ),
    "ped.local.mesh-changed": (
        "Las mallas cambiaron después del rig (se añadieron o quitaron vértices). Vuelve a hacer el rig."
    ),
    "ped.local.strain": "{count} vértices se estiran o se aplastan mucho en {pose}.",
    "ped.local.strain.one": "{count} vértice se estira o se aplasta mucho en {pose}.",
    "ped.local.hint": (
        "Los pliegues pequeños en poses extremas son normales. Para pliegues mayores, mueve un marcador y vuelve a "
        "hacer el rig."
    ),
    # ---- 5. Send --------------------------------------------------------------------------------------
    "ped.prop.name": "Nombre del ped",
    "ped.prop.name.desc": "El nombre que muestra Durty Cloth Tool para el ped",
    "ped.prop.model": "Nombre del modelo",
    "ped.prop.model.desc": (
        "El nombre del nuevo ped en el juego: una letra minúscula y luego de 2 a 31 letras minúsculas, dígitos o "
        "guiones bajos"
    ),
    "ped.prop.ragdoll": "Cuerpo de ragdoll",
    "ped.ragdoll.template": "Como la plantilla",
    "ped.ragdoll.template.desc": "El cuerpo de ragdoll compartido que usa la plantilla",
    "ped.ragdoll.fred": "Hombre estándar",
    "ped.ragdoll.fred.desc": "El cuerpo de ragdoll compartido de la mayoría de los peds masculinos",
    "ped.ragdoll.wilma": "Mujer estándar",
    "ped.ragdoll.wilma.desc": "El cuerpo de ragdoll compartido de la mayoría de los peds femeninos",
    "ped.ragdoll.fred-large": "Hombre grande",
    "ped.ragdoll.fred-large.desc": "El cuerpo de ragdoll compartido de los peds masculinos grandes",
    "ped.ragdoll.wilma-large": "Mujer grande",
    "ped.ragdoll.wilma-large.desc": "El cuerpo de ragdoll compartido de los peds femeninos grandes",
    "ped.ragdoll.subtext": (
        "En el juego, las balas, las caídas y el ragdoll usan las formas de este cuerpo. Elige uno grande para un "
        "personaje mucho más grande."
    ),
    "ped.texture.too-large": "La imagen {name} mide más de 4096 píxeles por un lado. Durty Cloth Tool la rechaza.",
    "ped.texture.not-multiple-of-four": (
        "El ancho o el alto de la imagen {name} no es divisible entre cuatro. Durty Cloth Tool la rechaza."
    ),
    "ped.texture.non-power-of-two": (
        "El tamaño de la imagen {name} no es una potencia de dos (como 1024 o 2048). Funciona, pero esos "
        "tamaños se ven mejor."
    ),
    "ped.op.send": "Crear ped personalizado",
    "ped.op.send.desc": (
        "Exportar el personaje con rig en la pose de reposo del juego y enviarlo a Durty Cloth Tool, que crea un nuevo "
        "proyecto de ped personalizado cuando lo confirmes allí"
    ),
    "ped.op.cancel-send.desc": "Retirar el personaje mientras Durty Cloth Tool siga preguntando",
    "ped.send.subtext": (
        "Durty Cloth Tool muestra el ped con sus revisiones y pregunta dónde crear el proyecto. No se crea nada hasta "
        "que elijas Crear allí."
    ),
    "ped.send.waiting": "Se envió el personaje ({size} MiB). Elige Crear en Durty Cloth Tool.",
    "ped.send.withdrawing": "Retirando el personaje.",
    "ped.send.withdrawn": "Retirado: Durty Cloth Tool no creó nada.",
    "ped.send.created": "Durty Cloth Tool creó el proyecto {name} con el ped {model} a partir de {template}.",
    "ped.send.created-late": (
        "Durty Cloth Tool creó el proyecto {name} con el ped {model} después de todo: se eligió Crear allí "
        "justo cuando se retiró el personaje."
    ),
    "ped.send.findings": "Revisiones de Durty Cloth Tool ({count}):",
    "ped.send.next": (
        "Revisa el comportamiento del ped en Durty Cloth Tool (tipo de ped, movimiento, voz) y luego compila el "
        "proyecto."
    ),
    "ped.finding.rig-mismatch": (
        "El esqueleto no es el de la plantilla ni el del rig: se movió o giró un hueso. Vuelve a aplicar el rig o "
        "vuelve a hacer el rig."
    ),
    "ped.finding.ped-budget": "Más vértices de los que un ped debería tener en su nivel de detalle más alto.",
    "ped.finding.ped-ragdoll-mismatch": (
        "La altura del personaje se aleja mucho del cuerpo de ragdoll de la plantilla: los impactos y las caídas en el "
        "juego usan las formas del cuerpo de la plantilla."
    ),
    "ped.finding.ped-rest-strain": "El rig plegó algunos triángulos en la pose de reposo del juego.",
    # ---- why something cannot run -----------------------------------------------------------------------
    "ped.why.select-meshes": "Selecciona primero las mallas de tu personaje.",
    "ped.why.no-character": "Elige primero tu personaje en Personaje.",
    "ped.why.object-mode": "Cambia primero a Modo Objeto.",
    "ped.why.rigged": "El personaje ya tiene rig. Quita el rig para cambiarlo.",
    "ped.why.no-markers": "Coloca primero los marcadores.",
    "ped.why.guide-running": "La guía de clics está en marcha.",
    "ped.why.view3d": "Inicia la guía de clics desde la barra lateral de la vista 3D.",
    "ped.why.checks": "Corrige primero lo que indican las comprobaciones de Personaje.",
    "ped.why.markers": "Coloca primero todos los marcadores.",
    "ped.why.connect": "Conéctate con Durty Cloth Tool para elegir una plantilla y hacer el rig.",
    "ped.why.template": "Elige primero una plantilla.",
    "ped.why.rights": "Confirma primero tus derechos sobre este personaje.",
    "ped.why.rigging": "Hay un rig en marcha en Durty Cloth Tool.",
    "ped.why.not-rigging": "No hay ningún rig en marcha.",
    "ped.why.no-result": "No hay ningún rig que aplicar. Haz primero el rig del personaje.",
    "ped.why.no-previous": "No hay ningún rig anterior.",
    "ped.why.not-rigged": "Haz primero el rig del personaje.",
    "ped.why.mesh-changed": "Las mallas del personaje cambiaron después de pedir este rig. Vuelve a hacer el rig.",
    "ped.why.vertex-count": "{name} cambia su número de vértices en un modificador. Aplica primero sus modificadores.",
    "ped.why.modifiers-shape-keys": (
        "{name} tiene formas clave, así que sus modificadores no se pueden aplicar. Quítalas primero."
    ),
    "ped.why.export-failed": (
        "El exportador glTF de Blender no escribió el personaje. Su registro Info tiene los detalles."
    ),
    "ped.why.model": (
        "El nombre del modelo es una letra minúscula y luego de 2 a 31 letras minúsculas, dígitos o guiones bajos."
    ),
    "ped.why.model-game": (
        "Los nombres que empiezan por {prefix} pertenecen a los peds propios del juego. Elige otro, como {suggestion}."
    ),
    "ped.why.name": "Da un nombre al ped.",
    "ped.why.transforms-first": "Aplica primero las transformaciones.",
    "ped.why.refused-checks": (
        "Ejecutar comprobaciones encontró problemas que Durty Cloth Tool rechazaría. Corrígelos primero."
    ),
    "ped.why.textures": "Una imagen es demasiado grande o su tamaño no es divisible entre cuatro. Corrígela primero.",
    "ped.why.sending": "Se está enviando un ped personalizado.",
    "ped.why.not-sending": "No se está enviando nada.",
    "ped.invalid": "El complemento no pudo preparar esta solicitud: {detail}",
    # ---- plans and Durty Cloth Tool's answers -----------------------------------------------------------
    "ped.plan.rig": "El rig está incluido en Durty Cloth Tool Ultimate.",
    "ped.plan.add": "Crear un proyecto de ped personalizado necesita Durty Cloth Tool Advanced o Ultimate.",
    "ped.error.rig-busy": (
        "Durty Cloth Tool está haciendo el rig de otro personaje. Vuelve a intentarlo cuando haya terminado."
    ),
    "ped.error.rig-cancelled": "Se canceló el rig.",
    "ped.error.rig-refused": "Durty Cloth Tool no pudo hacer el rig del personaje:",
    "ped.error.dct-too-old": (
        "Este Durty Cloth Tool aún no crea peds personalizados desde Blender. Actualiza Durty Cloth Tool."
    ),
    "ped.error.rig-disconnected": "La conexión con Durty Cloth Tool terminó durante el rig. Vuelve a hacer el rig.",
    "ped.error.rig-timeout": "Durty Cloth Tool no terminó el rig a tiempo. Vuelve a hacer el rig.",
    "ped.error.add-busy": (
        "Durty Cloth Tool está ocupado con otro ped personalizado o una compilación. Vuelve a intentarlo cuando haya "
        "terminado."
    ),
    "ped.error.add-denied": (
        "Se canceló en Durty Cloth Tool. Vuelve a elegir Crear ped personalizado cuando estés listo."
    ),
    "ped.error.model-rejected": (
        "Durty Cloth Tool no pudo crear un ped a partir del personaje. Sus revisiones de abajo explican por qué."
    ),
    "ped.error.save-failed": "Durty Cloth Tool no pudo crear el proyecto. Elige otra carpeta y vuelve a enviarlo.",
    "ped.error.add-disconnected": (
        "La conexión con Durty Cloth Tool terminó antes de que respondiera. Vuelve a elegir Crear ped personalizado."
    ),
    "ped.error.add-timeout": "Durty Cloth Tool no respondió a tiempo. Vuelve a elegir Crear ped personalizado.",
    "ped.error.add-unanswered": "Durty Cloth Tool no confirmó la retirada. Revisa su lista de proyectos.",
    # ---- protocol errors --------------------------------------------------------------------------------
    "error.template-not-found": "Esta plantilla no está instalada. Actualiza la lista y elige otra.",
    "error.mesh-too-large": (
        "El personaje tiene demasiados vértices o triángulos. Reduce primero una copia con Diezmar."
    ),
    "error.rig-refused": "Durty Cloth Tool no pudo hacer el rig del personaje.",
    "error.upload-incomplete": "El personaje no llegó completo a Durty Cloth Tool. Vuelve a enviarlo.",
}
