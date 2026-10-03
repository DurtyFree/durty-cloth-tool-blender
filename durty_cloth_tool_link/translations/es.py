# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2026 Schmid Software Solutions (https://schmid-software.de)
"""Spanish (Español). Direct "tú" imperatives, as Durty Cloth Tool uses them."""

TEXT = {
    "path.connected-apps": "Opciones > Apps conectadas",
    "panel.main": "Durty Cloth Tool",
    "panel.details": "Conexión",
    "panel.setup": "Conectar",
    "panel.linked": "Prenda vinculada",
    "panel.live": "Vista previa en directo",
    "panel.checks": "Revisión de textura",
    "panel.model": "Modelo",
    "panel.settings": "Ajustes",
    "chip.connected": "Conectado",
    "chip.live": "En directo",
    "chip.connecting": "Conectando",
    "chip.action": "Acción necesaria",
    "chip.offline": "Sin conexión",
    "chip.problem": "Problema",
    "state.idle": "No conectado",
    "state.connecting": "Buscando Durty Cloth Tool",
    "state.waiting": "No se encontró Durty Cloth Tool. Se volverá a intentar",
    "state.reconnecting": "Reconectando con Durty Cloth Tool",
    "state.hello": "Conectando",
    "state.signing-in": "Esperando el inicio de sesión",
    "state.authenticating": "Iniciando sesión",
    "state.ready": "Sesión iniciada como {name}",
    "state.signed-out": "Sesión cerrada",
    "state.dct-signed-out": "Durty Cloth Tool tiene la sesión cerrada",
    "state.dct-disconnected": "Desconectado en Durty Cloth Tool",
    "details.status": "Estado: {state}",
    "details.account": "Sesión iniciada como {name}",
    "details.not-signed-in": "Sin sesión iniciada",
    "details.project": "Proyecto: {name}",
    "details.addon": "Complemento {version} ({channel})",
    "online.off": (
        "El acceso en línea de Blender está desactivado, así que Durty Cloth Tool no se puede conectar: cada conexión "
        "se confirma con tu sesión de gta.clothing. Permítelo en Preferencias > Sistema > Red."
    ),
    "dct-signed-out": (
        "Durty Cloth Tool tiene la sesión cerrada. Inicia sesión en Durty Cloth Tool y luego elige Conectar. El "
        "complemento también lo reintenta solo de vez en cuando."
    ),
    "dct-disconnected": "Esta app se desconectó en Durty Cloth Tool. Elige Conectar para volver a conectarla.",
    "setup.find.title": "Encontrar Durty Cloth Tool",
    "setup.find.done": "Durty Cloth Tool encontrado",
    "setup.find.subtext": "Abre Durty Cloth Tool en este equipo. El complemento lo encuentra automáticamente.",
    "setup.find.searching": "Buscando Durty Cloth Tool…",
    "setup.find.waiting": "Durty Cloth Tool aún no está abierto. El complemento sigue buscando…",
    "setup.sign-in.title": "Iniciar sesión con gta.clothing",
    "setup.sign-in.done": "Sesión iniciada",
    "setup.sign-in.subtext": (
        "Creator Link usa tu cuenta de gta.clothing (Discord). Inicias sesión una vez en este equipo."
    ),
    "setup.sign-in.starting": "Iniciando el inicio de sesión…",
    "setup.sign-in.waiting": "Esperando la aprobación…",
    "setup.sign-in.asked": "Durty Cloth Tool muestra una solicitud de inicio de sesión. Apruébala allí.",
    "setup.sign-in.approved": "Durty Cloth Tool aprobó el inicio de sesión. Terminando…",
    "setup.sign-in.declined": (
        "Durty Cloth Tool no aprobó el inicio de sesión. Inicia sesión en el navegador en su lugar."
    ),
    "setup.sign-in.browser-subtext": "Abre la página de inicio de sesión y comprueba que muestra este código:",
    "setup.sign-in.signed-out": "Cerraste la sesión. Vuelve a iniciar sesión para usar Creator Link.",
    "linked.project": "Proyecto: {name}",
    "linked.no-project": "Abre un proyecto en Durty Cloth Tool.",
    "linked.no-cloth": "Selecciona una prenda en Durty Cloth Tool para trabajar en ella aquí.",
    "linked.cloth": "{name} · Variante {letter}",
    "linked.cloth-no-variation": "{name}",
    "linked.texture": "{name} ({width} x {height})",
    "linked.map": "Mapa",
    "linked.follows": "Sigue tu selección en Durty Cloth Tool",
    "linked.map-locked": "Detén la vista previa en directo para elegir otro mapa.",
    "linked.map-missing.diffuse": "Esta prenda no tiene mapa difuso.",
    "linked.map-missing.normal": "Esta prenda no tiene mapa normal.",
    "linked.map-missing.specular": "Esta prenda no tiene mapa especular.",
    "map.diffuse": "Difusa (color)",
    "map.diffuse.desc": "La textura de color de la prenda",
    "map.normal": "Normal",
    "map.normal.desc": "El mapa normal de la prenda",
    "map.specular": "Especular",
    "map.specular.desc": "El mapa especular de la prenda",
    "live.off": "Inicia la vista previa en directo para ver tu pintura en el ped.",
    "live.reading": "Leyendo la imagen…",
    "live.starting": "Iniciando la vista previa en directo…",
    "live.on": "En directo en el ped",
    "live.sending": "Enviando la imagen…",
    "live.not-worn": "Ponle esta prenda al ped en Durty Cloth Tool para verla.",
    "live.paused-dct": "La vista previa 3D está en pausa en Durty Cloth Tool.",
    "live.paused": "En pausa. Tus cambios se envían cuando reanudes.",
    "live.saving": "Guardando…",
    "live.unsaved": "Aún no guardado en el proyecto",
    "live.save-subtext": (
        "Guardar escribe este mapa en tu proyecto. Puedes deshacerlo en el Historial de la prenda en Durty Cloth "
        "Tool."
    ),
    "live.saved": "Guardado en {name}. Puedes deshacerlo en el Historial.",
    "live.saved-unnamed": "Guardado en la prenda. Puedes deshacerlo en el Historial.",
    "live.saved-variation": "Guardado como nueva variante de {name}.",
    "live.saved-variation-unnamed": "Guardado como nueva variante.",
    "live.discarded": "Se descartaron los cambios en Durty Cloth Tool.",
    "live.stopped": "Vista previa en directo detenida.",
    "live.stopped-unsaved": (
        "Vista previa en directo detenida. Los cambios no se guardaron en el proyecto; la imagen en Blender los "
        "conserva."
    ),
    "live.failed": "La vista previa en directo se detuvo tras un problema inesperado: {detail}",
    "live.upsell": "La vista previa en directo está incluida en Durty Cloth Tool Ultimate.",
    "live.save-upsell": "Guardar en la prenda está incluido en Durty Cloth Tool Ultimate.",
    "live.image-changed": "El tamaño de la imagen cambió. Vuelve a iniciar la vista previa en directo.",
    "live.image-removed": "Se eliminó la imagen.",
    "live.no-memory": "No hay memoria suficiente para una imagen tan grande.",
    "colour.non-color-diffuse": (
        "La imagen está en Non-Color; sus valores se envían como color sin cambios."
    ),
    "colour.unknown-diffuse": (
        "El espacio de color {space} de la imagen se envía sin convertir; usa sRGB para colores exactos."
    ),
    "colour.unknown-data": (
        "Pon el espacio de color del mapa en Non-Color; los valores {space} se envían tal como están en Blender."
    ),
    "image.none": "Elige primero una imagen.",
    "image.tiled": "Las imágenes UDIM (en mosaico) no se pueden usar. Usa una sola imagen.",
    "image.source": "Solo se pueden usar archivos de imagen e imágenes generadas.",
    "image.unreadable": "No se pudo leer la imagen.",
    "image.not-loaded": "No se pudo cargar la imagen. Comprueba que su archivo existe.",
    "image.channels": "Solo se pueden usar imágenes en escala de grises, RGB y RGBA.",
    "image.empty": "La imagen no tiene píxeles. Ábrela o créala primero.",
    "image.too-large": "No se pueden usar imágenes de más de {size} píxeles por lado.",
    "image.no-painted": "No se encontró ninguna imagen pintada. Elige la imagen en la lista.",
    "checks.errors": "Errores: {count}",
    "checks.warnings": "Advertencias: {count}",
    "checks.notes": "Notas: {count}",
    "checks.clean": "No se encontraron problemas.",
    "checks.not-checked": "Durty Cloth Tool revisa la textura al iniciar la vista previa en directo.",
    "checks.checking": "Revisando la textura…",
    "checks.unavailable": "La revisión de textura está incluida en Durty Cloth Tool Ultimate.",
    "severity.error": "Error",
    "severity.warning": "Advertencia",
    "severity.info": "Nota",
    "finding.unknown": "Durty Cloth Tool informó {code}.",
    "finding.non-power-of-two": "El tamaño no es potencia de dos (por ejemplo 1024 o 2048).",
    "finding.not-multiple-of-four": "El tamaño no es múltiplo de cuatro, algo que necesitan las texturas comprimidas.",
    "finding.too-large": "La textura supera los 2048 píxeles por lado, lo que usa mucha memoria del juego.",
    "finding.too-small": "La textura tiene menos de 16 píxeles por lado.",
    "finding.size-changed": "El tamaño es distinto del de la textura guardada en el proyecto.",
    "finding.palette-alpha": (
        "Esta prenda usa una paleta de colores: su canal alfa elige colores de la paleta, así que pinta el alfa con "
        "cuidado."
    ),
    "finding.cutout-alpha": "Esta prenda usa el alfa como recorte: los píxeles transparentes se ocultan en el ped.",
    "finding.hair-ramp": "Esto es pelo: el juego lo colorea con el color de pelo que elige el jugador.",
    "finding.bc1-alpha": "La textura guardada solo conserva alfa totalmente transparente o totalmente opaco.",
    "finding-fix.non-power-of-two": "Redimensiona a una potencia de dos, por ejemplo 1024 x 1024, antes de guardar.",
    "finding-fix.not-multiple-of-four": (
        "Redimensiona para que ambos lados sean divisibles entre cuatro, por ejemplo 1024 x 512."
    ),
    "finding-fix.too-large": "Usa 2048 píxeles o menos por lado salvo que la prenda necesite ese detalle.",
    "finding-fix.too-small": "Usa al menos 16 píxeles por lado.",
    "finding-fix.size-changed": (
        "Guardar reemplaza la textura con este tamaño. Vuelve al tamaño guardado si no querías cambiarlo."
    ),
    "finding-fix.palette-alpha": "Deja los valores alfa como están salvo que quieras cambiar los colores de la paleta.",
    "finding-fix.cutout-alpha": "Pinta transparencia solo donde la prenda deba ocultarse.",
    "finding-fix.hair-ramp": "Pinta el sombreado en el canal verde y los reflejos en el canal rojo, no el color final.",
    "finding-fix.bc1-alpha": (
        "Usa alfa totalmente transparente o totalmente opaco; los bordes suaves se pierden al guardar."
    ),
    "model.subtext": "Vuelve a enviar el modelo poco después de que dejes de editar.",
    "model.name": "Modelo: {name}",
    "model.sending": "Enviando {name} (texturas: {count})",
    "model.previewing": "Se muestra en el ped en Durty Cloth Tool. Guárdalo o descártalo allí o aquí.",
    "model.findings": "Durty Cloth Tool informó hallazgos: {count}.",
    "model.warnings-paused": (
        "Sollumz informó advertencias, así que el envío automático está en pausa. Revisa el registro Info de "
        "Sollumz y vuelve a enviar para reanudar."
    ),
    "model.warnings": "Sollumz informó advertencias; su registro Info tiene los detalles.",
    "model.saving": "Guardando el modelo en Durty Cloth Tool…",
    "model.saved": "Modelo guardado en la prenda. Puedes deshacerlo en el Historial.",
    "model.discarded": "Se descartó el modelo en Durty Cloth Tool.",
    "model.save-retry": "Durty Cloth Tool aún está cargando el modelo. Guardando en un momento…",
    "model.save-busy": "Durty Cloth Tool sigue ocupado con el modelo. Vuelve a guardar en un momento.",
    "model.block.no-model": "Envía primero un modelo.",
    "model.block.saving": "Ya se está guardando.",
    "model.block.waiting": "Espera a que Durty Cloth Tool responda.",
    "model.block.pushing": "Espera a que el último envío se vea en Durty Cloth Tool y luego guarda.",
    "model.block.due": (
        "Tus últimos cambios se van a enviar. Guarda cuando se vean en Durty Cloth Tool."
    ),
    "model.wait.tool": "El envío automático espera a que termine la herramienta en curso.",
    "model.wait.mode": "El envío automático espera a que salgas de {mode}.",
    "model.gone": "El modelo enviado ya no está en este archivo. Envíalo de nuevo.",
    "model.failed": "El envío automático falló: {detail}",
    "model.select": "Selecciona el modelo que enviar: un Drawable Dictionary de Sollumz o un objeto dentro de uno.",
    "model.one-root": "Selecciona objetos de un solo Drawable Dictionary.",
    "model.needs-dictionary": (
        "Durty Cloth Tool necesita un Drawable Dictionary. Emparenta el Drawable con uno (Sollumz: Create Drawable "
        "Dictionary) y vuelve a enviar."
    ),
    "model.not-sollumz": "Selecciona un Drawable Dictionary de Sollumz o un objeto dentro de uno.",
    "model.unhide": (
        "Muestra el Drawable Dictionary (o un objeto dentro de él), hazlo seleccionable y vuelve a enviar."
    ),
    "model.not-shown": (
        "El modelo no está en ninguna escena que muestre una ventana de Blender. Muestra su escena y vuelve a enviar."
    ),
    "model.not-in-layer": "El modelo no está en el view layer actual. Muéstralo y vuelve a enviar.",
    "model.export-failed": "Sollumz no pudo exportar el modelo: {detail}",
    "model.not-exported": "Sollumz no exportó el modelo. Su registro Info tiene los detalles.",
    "sollumz.ready": "Sollumz {version}",
    "sollumz.ready-unknown": "Sollumz",
    "sollumz.missing": "Instala y activa Sollumz {version} o posterior para enviar modelos.",
    "sollumz.too-old": (
        "Este Sollumz es demasiado antiguo para exportar a Durty Cloth Tool. Actualiza a Sollumz {version} o "
        "posterior."
    ),
    "sollumz.tested": "Probado con Sollumz {version}.",
    "bundle.unreadable": "No se pudo leer la carpeta de exportación ({detail}).",
    "bundle.not-dictionary": (
        "Sollumz exportó un drawable o fragment, no un drawable dictionary. Durty Cloth Tool necesita un Drawable "
        "Dictionary: emparenta tu Drawable con uno (Sollumz: Create Drawable Dictionary) y vuelve a enviar."
    ),
    "bundle.no-model": "Sollumz no exportó ningún modelo. El registro Info de Sollumz indica el motivo.",
    "bundle.several": "Sollumz exportó varios drawable dictionaries ({count}). Selecciona objetos de uno solo.",
    "bundle.bad-name": (
        "'{name}' no se puede enviar: los nombres de archivo solo pueden usar letras, dígitos, '_', '-' y '.', no "
        "pueden empezar por '.' ni contener '..', y tienen como máximo 128 caracteres. Cambia el nombre de la "
        "textura o del modelo en Blender."
    ),
    "bundle.duplicate": "Dos texturas se llaman '{name}'. Da a cada textura un nombre distinto.",
    "bundle.too-many": "El modelo usa {count} texturas; se pueden enviar como máximo {limit}.",
    "bundle.empty-file": "'{name}' está vacío. Exporta el modelo de nuevo.",
    "bundle.too-large": "El modelo y sus texturas superan juntos {size} MiB y no se pueden enviar.",
    "bundle.invalid": "La exportación no se puede enviar: {detail}",
    "settings.connection": "Conexión",
    "settings.account": "Cuenta",
    "settings.updates": "Actualizaciones",
    "settings.privacy": "Privacidad",
    "settings.about": "Acerca de",
    "settings.models": "Modelos",
    "settings.connect-subtext": (
        "Necesita Durty Cloth Tool en este equipo. La conexión se queda en este equipo; gta.clothing confirma tu "
        "sesión en cada conexión."
    ),
    "settings.signed-in-as": "Sesión iniciada como {name}",
    "settings.not-signed-in": "Sin sesión iniciada",
    "settings.signed-out": "Sesión cerrada",
    "settings.sign-out-subtext": "Cerrar sesión termina la sesión de gta.clothing de este complemento en este equipo.",
    "settings.device-name-subtext": (
        "La página de aprobación de gta.clothing lo muestra, para que distingas tus equipos."
    ),
    "settings.licence": "GPL-3.0-or-later, Schmid Software Solutions. Mantenido por DurtyFree (Pleb Masters).",
    "settings.this-version": "Esta versión: {version} ({channel})",
    "settings.diagnostics-copied": (
        "Diagnóstico copiado. Pégalo en el servidor Pleb Masters Community Discord cuando pidas ayuda. Contiene "
        "versiones y códigos de estado, sin rutas de archivo ni datos de inicio de sesión."
    ),
    "settings.disk-install": (
        "Esta copia se instaló desde un archivo, así que Blender no puede actualizarla. Para recibir "
        "actualizaciones, arrastra a Blender el enlace de instalación de la página de plugins de "
        "gta.clothing."
    ),
    "settings.updates-on": "Blender actualiza este complemento desde el repositorio de extensiones de Durty Cloth Tool.",
    "op.plugins-page": "Obtener el enlace de instalación",
    "op.plugins-page.desc": "Abrir la página de plugins de gta.clothing, desde donde arrastras el enlace de instalación a Blender",
    "info.channel": (
        "Experimental recibe primero las funciones y correcciones nuevas y cambia más a menudo. Release las "
        "recibe cuando están probadas. Eliges el canal con el enlace de instalación que arrastras a Blender."
    ),
    "settings.code-copied": "Código copiado.",
    "channel.release": "Release",
    "channel.experimental": "Experimental",
    "info.find": (
        "Creator Link solo habla con Durty Cloth Tool en este equipo. No se envía nada por internet salvo tu inicio "
        "de sesión."
    ),
    "info.sign-in": (
        "Iniciar sesión muestra a Durty Cloth Tool que este complemento pertenece a tu cuenta. El complemento nunca ve "
        "tu contraseña de Discord. Durty Cloth Tool muestra esta app en {apps}, donde puedes desconectarla."
    ),
    "info.map": (
        "Elige qué mapa de la prenda reemplaza la imagen en la vista previa: Difusa (color), Normal o Especular. Las "
        "imágenes difusas son color sRGB; pon los mapas normal y especular en Non-Color."
    ),
    "info.variation": (
        "Los mapas normal y especular pertenecen al modelo y los comparten todas las variantes, así que solo la "
        "Difusa (color) puede convertirse en una nueva variante."
    ),
    "info.live": (
        "El complemento lee la imagen al terminar cada trazo y envía lo que cambió. No se guarda nada en tu proyecto "
        "hasta que elijas Guardar en la prenda o Guardar como nueva variante."
    ),
    "info.model": (
        "Enviar modelo exporta el Drawable Dictionary de Sollumz seleccionado como CodeWalker XML (YDD) con sus "
        "texturas y lo muestra en la prenda vinculada. No se guarda nada hasta que elijas Guardar modelo en la prenda."
    ),
    "info.checks": (
        "Durty Cloth Tool revisa la imagen según lo que necesitan GTA V y la prenda, como su lista de errores. "
        "Corrige los errores antes de guardar; las advertencias y notas son consejos."
    ),
    "info.privacy": (
        "Se queda en este equipo: tus imágenes, modelos y los píxeles de la vista previa en directo. Solo van a "
        "Durty Cloth Tool. Va a gta.clothing: tu inicio de sesión (con el nombre de este equipo salvo que lo "
        "desactives), una confirmación por conexión, tu cierre de sesión y las comprobaciones de actualizaciones de "
        "Blender."
    ),
    "op.connect": "Conectar",
    "op.connect.desc": "Conectar con Durty Cloth Tool en este equipo",
    "op.disconnect": "Desconectar",
    "op.disconnect.desc": "Desconectar de Durty Cloth Tool. La vista previa en directo en curso se detiene",
    "op.sign-in-dct": "Aprobar en Durty Cloth Tool",
    "op.sign-in-dct.desc": "Pedir a Durty Cloth Tool que apruebe el inicio de sesión con la cuenta que usa",
    "op.sign-in": "Iniciar sesión en el navegador",
    "op.sign-in.desc": "Iniciar sesión con tu cuenta de gta.clothing (Discord) en el navegador",
    "op.open-sign-in": "Abrir página de inicio de sesión",
    "op.open-sign-in.desc": "Abrir la página de gta.clothing que aprueba este inicio de sesión",
    "op.copy-code": "Copiar código",
    "op.copy-code.desc": "Copiar el código de inicio de sesión al portapapeles",
    "op.cancel-sign-in": "Cancelar",
    "op.cancel-sign-in.desc": "Dejar de esperar el inicio de sesión",
    "op.sign-out": "Cerrar sesión",
    "op.sign-out.desc": "Cerrar la sesión de gta.clothing en este complemento y desconectar",
    "op.update-page": "Obtener la actualización",
    "op.update-page.desc": "Abrir la página con las versiones actuales de Durty Cloth Tool y sus plugins",
    "op.use-paint-image": "Usar imagen pintada",
    "op.use-paint-image.desc": "Usar la imagen en la que pintas, o la del Image Editor",
    "op.live-start": "Iniciar vista previa en directo",
    "op.live-start.desc": (
        "Mostrar esta imagen en la prenda vinculada y actualizarla tras cada trazo. No se guarda nada hasta que "
        "guardes"
    ),
    "op.live-stop": "Detener vista previa en directo",
    "op.live-stop.desc": (
        "Dejar de enviar la imagen. Los cambios siguen en el ped hasta que los descartes o Durty Cloth Tool los "
        "descarte"
    ),
    "op.live-pause": "Pausar",
    "op.live-pause.desc": "No enviar cambios por ahora. El ped sigue mostrando la última actualización",
    "op.live-resume": "Reanudar",
    "op.live-resume.desc": "Volver a enviar cambios, empezando por todo lo que cambió durante la pausa",
    "op.live-send": "Enviar ahora",
    "op.live-send.desc": "Volver a enviar la imagen ahora, para cambios hechos por scripts, bakes o recargas",
    "op.live-save": "Guardar en la prenda",
    "op.live-save.desc": (
        "Reemplazar el mapa de la prenda vinculada con esta imagen en tu proyecto. Puedes deshacerlo en el Historial"
    ),
    "op.live-save-variation": "Guardar como nueva variante",
    "op.live-save-variation.desc": (
        "Añadir esta imagen a la prenda vinculada como nueva variante de textura (solo Difusa (color))"
    ),
    "op.live-discard": "Descartar cambios",
    "op.live-discard.desc": "Quitar los cambios del ped y detener. Tu proyecto conserva su textura guardada",
    "op.check-again": "Revisar de nuevo",
    "op.check-again.desc": "Pedir a Durty Cloth Tool que revise la imagen de nuevo",
    "op.model-push": "Enviar modelo",
    "op.model-push.desc": (
        "Exportar el Drawable Dictionary de Sollumz seleccionado y mostrarlo en la prenda vinculada. No se guarda "
        "nada hasta que guardes"
    ),
    "op.model-save": "Guardar modelo en la prenda",
    "op.model-save.desc": "Guardar el modelo enviado en tu proyecto. El modelo anterior queda en el Historial de la prenda",
    "op.model-discard": "Descartar",
    "op.model-discard.desc": "Quitar el modelo enviado del ped. Tu proyecto conserva su modelo guardado",
    "op.diagnostics": "Copiar diagnóstico",
    "op.diagnostics.desc": "Copiar versiones y códigos de estado para soporte (sin rutas de archivo ni datos de sesión)",
    "op.help": "Ayuda",
    "op.help.desc": "Abrir la documentación de Durty Cloth Tool",
    "op.community": "Pleb Masters Community Discord",
    "op.community.desc": "Abrir el servidor Pleb Masters Community Discord, donde puedes pedir ayuda",
    "op.info": "Más información",
    "op.join-discord": "Unirse al servidor de Discord",
    "op.join-discord.desc": "Abrir la invitación al servidor Pleb Masters Community Discord en el navegador",
    "prop.image": "Imagen",
    "prop.image.desc": "La imagen que se muestra en la prenda vinculada",
    "prop.map": "Mapa",
    "prop.map.desc": "Qué mapa de la prenda vinculada reemplaza la imagen en la vista previa",
    "prop.auto-push": "Enviar automáticamente",
    "prop.auto-push.desc": "Volver a enviar el modelo poco después de dejar de editar (tras el primer envío)",
    "prop.auto-connect": "Conectar automáticamente",
    "prop.auto-connect.desc": "Buscar Durty Cloth Tool en este equipo al iniciar Blender",
    "prop.device-name": "Mostrar el nombre de este equipo al iniciar sesión",
    "prop.device-name.desc": (
        "Enviar el nombre de este equipo con un inicio de sesión, para que la página de aprobación de gta.clothing "
        "muestre qué equipo lo pide"
    ),
    "prop.delay": "Retraso del envío automático",
    "prop.delay.desc": (
        "Segundos que un modelo enviado debe seguir sin cambios antes de que Enviar automáticamente lo vuelva a "
        "enviar"
    ),
    "notice.signed-in": "Sesión iniciada como {name}.",
    "notice.signing-out": "Cerrando sesión…",
    "notice.signed-out": "Sesión cerrada.",
    "notice.signed-out-local": (
        "Sesión cerrada en este equipo. Permite el acceso en línea en las preferencias de Blender para terminar "
        "también la sesión en gta.clothing."
    ),
    "notice.signed-out-unreached": (
        "Sesión cerrada en este equipo; no se pudo contactar con gta.clothing. Allí la sesión termina sola, o "
        "termínala en la página de tu cuenta."
    ),
    "notice.browser-opens": "Tu navegador abrirá la página de inicio de sesión en un momento.",
    "notice.no-sign-in": "No hay ningún inicio de sesión pendiente.",
    "notice.not-gta-clothing": "El enlace de inicio de sesión no es un enlace de gta.clothing.",
    "notice.unexpected": "El complemento tuvo un problema inesperado: {detail}",
    "notice.secrets-unreadable": "No se pudo leer la sesión guardada ({detail}). Vuelve a iniciar sesión.",
    "notice.secret-store": "No se pudo leer ni escribir la sesión protegida. Vuelve a iniciar sesión.",
    "notice.file-error": "No se pudo leer ni escribir un archivo: {detail}",
    "notice.not-ready": "El complemento no está listo.",
    "notice.connect-first": "Conecta primero con Durty Cloth Tool.",
    "notice.select-cloth": "Selecciona primero una prenda en Durty Cloth Tool.",
    "notice.start-live-first": "Inicia primero la vista previa en directo.",
    "notice.wait-saving": "Espera a que termine de guardarse.",
    "notice.diffuse-only": "Solo la Difusa (color) puede convertirse en una nueva variante.",
    "notice.pushing": "Hay un envío en curso.",
    "notice.online-off": "El acceso en línea de Blender está desactivado.",
    "error.generic": "Algo salió mal.",
    "error.generic-code": "Algo salió mal ({code}).",
    "error.malformed-message": (
        "Durty Cloth Tool y este complemento no se entendieron. Actualiza ambos y vuelve a intentarlo."
    ),
    "error.invalid-message": (
        "Durty Cloth Tool y este complemento no se entendieron. Actualiza ambos y vuelve a intentarlo."
    ),
    "error.unknown-message-type": "Durty Cloth Tool no conoce esta solicitud. Actualiza Durty Cloth Tool.",
    "error.unexpected-message": "Durty Cloth Tool no esperaba esta solicitud ahora. Vuelve a intentarlo.",
    "error.message-too-large": "La imagen o el modelo era demasiado grande para enviarlo.",
    "error.unsupported-protocol": (
        "Este complemento y Durty Cloth Tool usan versiones de enlace distintas. Actualiza ambos."
    ),
    "error.plugin-too-old": "Este complemento es demasiado antiguo para tu Durty Cloth Tool. Actualiza el complemento.",
    "error.dct-too-old": "Tu Durty Cloth Tool es demasiado antiguo para este complemento. Actualiza Durty Cloth Tool.",
    "error.not-authenticated": "Inicia sesión primero.",
    "error.authentication-failed": "Durty Cloth Tool no aceptó el inicio de sesión. Reintentando…",
    "error.untrusted-endpoint": (
        "Respondió un programa que no es tu Durty Cloth Tool, así que no se envió nada. El complemento sigue buscando "
        "Durty Cloth Tool."
    ),
    "error.account-mismatch": (
        "Durty Cloth Tool tiene la sesión iniciada con otra cuenta. Cierra sesión aquí e inicia sesión con la "
        "cuenta que usa Durty Cloth Tool."
    ),
    "error.dct-signed-out": (
        "Durty Cloth Tool tiene la sesión cerrada. Inicia sesión en Durty Cloth Tool; el complemento se conecta solo."
    ),
    "error.token-invalid": "La sesión caducó. Iniciando sesión de nuevo…",
    "error.needs-license": "Esto necesita una licencia de Durty Cloth Tool.",
    "error.needs-ultimate": "Esto está incluido en Durty Cloth Tool Ultimate.",
    "error.no-project": "Abre primero un proyecto en Durty Cloth Tool.",
    "error.no-focused-item": "Selecciona primero una prenda en Durty Cloth Tool.",
    "error.binding-in-use": "Otra app ya está trabajando en esta textura o modelo.",
    "error.binding-not-found": "La prenda o textura ya no existe en Durty Cloth Tool.",
    "error.lease-not-found": "Durty Cloth Tool terminó esta vista previa. Vuelve a iniciarla.",
    "error.lease-limit": "Hay demasiadas vistas previas en directo abiertas. Detén una primero.",
    "error.budget-exceeded": (
        "La memoria de vistas previas en directo de Durty Cloth Tool está llena. Detén otra vista previa en directo."
    ),
    "error.frame-out-of-bounds": "La actualización de la imagen no cabía en la textura.",
    "error.frame-size-mismatch": "No se pudo enviar la imagen.",
    "error.unsupported-format": (
        "Durty Cloth Tool no acepta este formato aquí. Envía los modelos como YDD XML de Sollumz."
    ),
    "error.stale-revision": "Aún había píxeles más nuevos en camino. Vuelve a guardar.",
    "error.item-refused": "Durty Cloth Tool no puede editar este elemento (dummy, bloqueado o protegido).",
    "error.game-required": (
        "Durty Cloth Tool necesita tu instalación de GTA V para esto. Configúrala en Durty Cloth Tool."
    ),
    "error.save-failed": "Durty Cloth Tool no pudo guardar. Su barra de estado tiene los detalles.",
    "error.busy": "Durty Cloth Tool está ocupado. Vuelve a intentarlo en un momento.",
    "error.rate-limited": "Demasiadas solicitudes. Espera un momento y vuelve a intentarlo.",
    "error.connection-limit": "Hay demasiadas apps conectadas a Durty Cloth Tool.",
    "error.request-denied": "Durty Cloth Tool rechazó la solicitud.",
    "error.model-rejected": (
        "Durty Cloth Tool no pudo usar este modelo. Revísalo en Sollumz y vuelve a enviarlo."
    ),
    "error.internal-error": (
        "Algo salió mal. Vuelve a intentarlo y reinicia Blender y Durty Cloth Tool si sigue pasando."
    ),
    "error.disconnected": "Se perdió la conexión con Durty Cloth Tool.",
    "error.timeout": "Durty Cloth Tool no respondió a tiempo.",
    "error.superseded": "Una solicitud más reciente reemplazó a esta.",
    "error.cancelled": "Cancelado.",
    "error.closed": "La vista previa en directo está cerrada.",
    "error.signed-out": "Cerraste la sesión. Inicia sesión para volver a usar Creator Link.",
    "error.assertion-invalid": "No se pudo confirmar el inicio de sesión. Reintentando…",
    "error.pixel-source-failed": "No se pudo leer la imagen para la vista previa en directo. Reintentando…",
    "error.callback-failed": "Algo salió mal en el complemento. Vuelve a intentarlo.",
    "error.offline": (
        "El acceso en línea de Blender está desactivado. Permítelo en Preferencias > Sistema > Red para iniciar "
        "sesión y conectar."
    ),
    "error.network": "No se pudo contactar con gta.clothing. Comprueba la conexión a internet.",
    "error.invalid-response": "gta.clothing envió una respuesta inesperada. Vuelve a intentarlo más tarde.",
    "error.tls": (
        "Falló la conexión segura con gta.clothing. Revisa tu red, tu proxy o la configuración del antivirus."
    ),
    "error.account_locked": "Tu cuenta de gta.clothing está bloqueada.",
    "error.discord_membership_required": (
        "Creator Link necesita que tu cuenta de Discord sea miembro del servidor Pleb Masters Community Discord."
    ),
    "error.discord_unavailable": "El inicio de sesión con Discord no está disponible ahora. Vuelve a intentarlo más tarde.",
    "error.plugin_update_required": "gta.clothing necesita una versión más nueva de este complemento. Actualízalo.",
    "error.expired_token": "El código de inicio de sesión caducó. Vuelve a iniciar sesión.",
    "error.access_denied": "Se denegó el inicio de sesión.",
    "error.invalid_grant": "No se aceptó el inicio de sesión. Vuelve a iniciar sesión.",
    "error.session_invalid": "La sesión ya no es válida. Vuelve a iniciar sesión.",
    "error.session_expired": "La sesión caducó. Vuelve a iniciar sesión.",
    "error.session_revoked": "La sesión se terminó en gta.clothing. Vuelve a iniciar sesión.",
    "error.refresh_in_progress": "Otro programa está renovando tu sesión. Vuelve a intentarlo en un momento.",
    "close.closed": "Vista previa en directo detenida.",
    "close.replaced": "Otra app tomó esta textura.",
    "close.itemRemoved": "La prenda se eliminó en Durty Cloth Tool.",
    "close.projectClosed": "El proyecto se cerró en Durty Cloth Tool.",
    "close.entitlementLost": "Tu plan ya no incluye esta función.",
    "close.signedOut": "Durty Cloth Tool cerró la sesión, así que la vista previa terminó.",
    "close.disconnected": "Se perdió la conexión con Durty Cloth Tool.",
    "feature.needsLicense": "Esto necesita una licencia de Durty Cloth Tool.",
    "feature.needsUltimate": "Esto está incluido en Durty Cloth Tool Ultimate.",
    "feature.unavailable": "Esto no está incluido en tu plan de Durty Cloth Tool.",
}
