# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2026 Schmid Software Solutions (https://schmid-software.de)
"""Brazilian Portuguese (Português do Brasil): the Custom Ped texts."""

TEXT = {
    # ---- the switch in the DCT tab --------------------------------------------------------------------
    "workspace.prop": "Trabalhar em",
    "workspace.prop.desc": "O que a aba DCT mostra: as ferramentas de roupa ou as ferramentas de ped personalizado",
    "workspace.clothing": "Roupas",
    "workspace.clothing.desc": (
        "A roupa vinculada no Durty Cloth Tool, a pré-visualização ao vivo e o modelo dela, e o Ajuste de roupas"
    ),
    "workspace.ped": "Ped personalizado",
    "workspace.ped.desc": "Transformar o seu próprio personagem em um ped personalizado para o Durty Cloth Tool",
    # ---- the panel ------------------------------------------------------------------------------------
    "ped.panel": "Ped personalizado (experimental)",
    "ped.stage-title": "{number}. {title}",
    "ped.section.character": "Personagem",
    "ped.section.markers": "Marcadores",
    "ped.section.rig": "Rig",
    "ped.section.check": "Verificação",
    "ped.section.send": "Envio",
    "ped.status.none": "Ainda nenhum",
    "ped.status.vertices": "{count} vértices",
    "ped.status.rigging": "Fazendo o rig",
    "ped.status.waiting": "Aguardando você",
    "ped.status.ready": "Pronto",
    "ped.status.review": "Precisa de revisão",
    "ped.status.not-rigged": "Sem rig",
    "ped.status.not-checked": "Não verificado",
    "ped.status.no-problems": "Sem problemas",
    "ped.status.problems": "Ocorrências: {count}",
    "ped.status.sent": "Criado",
    "ped.status.sending": "Enviando",
    "ped.status.not-sent": "Não enviado",
    "ped.privacy": (
        "O rig e a criação do ped acontecem no Durty Cloth Tool neste computador, a partir dos seus próprios arquivos "
        "do GTA V. Nada do seu personagem vai para o gta.clothing."
    ),
    "ped.heading.more": "Mais opções",
    # ---- the next step --------------------------------------------------------------------------------
    "ped.next.character": "Selecione as malhas do seu personagem na vista 3D e escolha Usar seleção.",
    "ped.next.fix": "A seguir: corrija o que as verificações em Personagem apontam.",
    "ped.next.markers": "A seguir: posicione os marcadores em Marcadores. O guia de cliques mostra cada ponto.",
    "ped.next.marker-problems": "A seguir: corrija os marcadores que a lista em Marcadores aponta.",
    "ped.next.connect": "A seguir: conecte-se ao Durty Cloth Tool (acima). Nenhum projeto precisa estar aberto.",
    "ped.next.template": "A seguir: escolha um modelo base em Rig.",
    "ped.next.rig": "A seguir: Fazer o rig no Durty Cloth Tool em Rig.",
    "ped.next.rigging": (
        "O Durty Cloth Tool está fazendo o rig do seu personagem. Enquanto isso, você pode continuar usando o Blender."
    ),
    "ped.next.approve": (
        "A seguir: confira para onde o Durty Cloth Tool moveu os marcadores (amarelos) e depois use Aplicar rig."
    ),
    "ped.next.check": "A seguir: experimente as poses de teste e use Executar verificações em Verificação.",
    "ped.next.send": "A seguir: Criar ped personalizado em Envio.",
    "ped.next.sending": "Aguardando você no Durty Cloth Tool: escolha lá onde criar o projeto.",
    "ped.next.done": "Concluído: o Durty Cloth Tool criou o projeto {name}. Compile-o lá.",
    "ped.next.done-before": "Concluído: o Durty Cloth Tool criou um projeto a partir deste personagem. Compile-o lá.",
    # ---- 1. Character ---------------------------------------------------------------------------------
    "ped.character.none": (
        "Selecione todas as malhas do seu personagem (corpo, cabeça, cabelo, olhos) na vista 3D e depois escolha Usar "
        "seleção."
    ),
    "ped.character.facts": "{objects} objetos, {vertices} vértices, {triangles} triângulos, {materials} materiais",
    "ped.prop.character": "Personagem",
    "ped.prop.character.desc": "A coleção que contém as malhas do seu personagem",
    "ped.op.use-selected": "Usar seleção",
    "ped.op.use-selected.desc": (
        "Usar as malhas selecionadas como o seu personagem. Quando elas não estão numa coleção própria, são movidas "
        "para uma nova"
    ),
    "ped.done.use-selected": "{name} é o seu personagem ({count} malhas).",
    "ped.check.none": "O personagem não tem malhas.",
    "ped.check.rigged": "O personagem já tem rig. Use Remover rig em Rig para mudar a forma ou o tamanho dele.",
    "ped.check.rigged-changed": (
        "Uma parte foi movida ou recebeu um modificador depois do rig. Desfaça isso, ou remova o rig e faça o rig de "
        "novo."
    ),
    "ped.check.transforms": (
        "{count} malhas estão movidas, giradas ou escaladas. Aplique as transformações delas para o personagem manter "
        "a forma."
    ),
    "ped.check.modifiers": "{count} malhas têm modificadores ({names}). Aplique-os para que o rig veja o que você vê.",
    "ped.check.old-rig": (
        "O personagem usa o rig {name}. Remova o rig antigo: o personagem mantém a pose, e Do rig antigo ainda pode "
        "posicionar os marcadores nas articulações dele."
    ),
    "ped.check.shape-keys": (
        "{count} malhas têm shape keys, que não acompanham o rig. Remova-as para manter a forma que você vê."
    ),
    "ped.check.lying": "O personagem parece estar deitado (é mais comprido do que alto). Colocá-lo em pé?",
    "ped.check.upside-down": "O personagem parece estar de cabeça para baixo. Desvirá-lo?",
    "ped.check.unit": (
        "O personagem tem {height} unidades de altura, então provavelmente está em {unit}. Escalá-lo para {metres} m?"
    ),
    "ped.check.too-tall": (
        "O personagem tem {height} m de altura. Ele precisa ficar a no máximo 3 m da origem: reduza a escala dele."
    ),
    "ped.check.height-unusual": (
        "O personagem tem {height} m de altura. Um ped do GTA V tem cerca de 1,8 m: personagens muito menores ou "
        "maiores podem se mover e colidir de um jeito estranho no jogo."
    ),
    "ped.check.height": "Altura: {height} m",
    "ped.check.origin": "O personagem está a {distance} m da origem. Mova-o para a origem.",
    "ped.check.facing": (
        "O seu personagem precisa estar de frente para você na vista frontal (Numpad 1), com o lado esquerdo dele à "
        "sua direita. Está?"
    ),
    "ped.check.facing-other": (
        "Os pés parecem apontar {direction}. O seu personagem precisa estar de frente para você na vista frontal "
        "(Numpad 1). Gire-o, ou confirme que ele está de frente."
    ),
    "ped.check.facing-done": "Está de frente",
    "ped.check.size-limit": (
        "{vertices} vértices e {triangles} triângulos: um rig aceita no máximo {max_vertices} vértices e "
        "{max_triangles} triângulos. Reduza primeiro uma cópia do personagem, por exemplo com um modificador Decimate."
    ),
    "ped.check.size-budget": (
        "{vertices} vértices. Um ped deveria ter no máximo {budget} no nível de detalhe mais alto, então o Durty Cloth "
        "Tool vai avisar sobre isso. Mesmo assim, funciona."
    ),
    "ped.check.size": "{vertices} vértices: bom para um ped",
    "ped.unit.cm": "centímetros",
    "ped.unit.mm": "milímetros",
    "ped.unit.in": "polegadas",
    "ped.direction.back": "para trás",
    "ped.direction.screen-right": "para a sua direita",
    "ped.direction.screen-left": "para a sua esquerda",
    "ped.op.apply-transforms": "Aplicar transformações",
    "ped.op.apply-transforms.desc": (
        "Incorporar em cada malha a posição, a rotação e a escala dela, sem mudar a aparência"
    ),
    "ped.done.transforms": "Transformações de {count} malhas aplicadas.",
    "ped.op.apply-modifiers": "Aplicar modificadores",
    "ped.op.apply-modifiers.desc": (
        "Aplicar todos os modificadores das malhas do personagem (exceto o modificador Armature)"
    ),
    "ped.confirm.modifiers": (
        "Aplicar todos os modificadores das malhas do personagem? As configurações deles se perdem depois."
    ),
    "ped.done.modifiers": "{count} modificadores aplicados.",
    "ped.op.remove-old-rig": "Remover rig antigo",
    "ped.op.remove-old-rig.desc": (
        "Tirar o personagem da armature com que ele veio: ele mantém a pose atual, e a armature fica oculta"
    ),
    "ped.confirm.old-rig": (
        "Remover o rig antigo? O personagem mantém a pose atual e perde os grupos de vértices do rig antigo. A "
        "armature antiga fica no arquivo, oculta."
    ),
    "ped.done.old-rig": "O rig antigo ({name}) foi removido. Do rig antigo ainda pode usar as articulações dele.",
    "ped.op.remove-shape-keys": "Remover shape keys",
    "ped.op.remove-shape-keys.desc": (
        "Remover as shape keys das malhas do personagem, mantendo a forma que elas mostram"
    ),
    "ped.confirm.shape-keys": "Remover todas as shape keys do personagem? A forma que você vê agora continua.",
    "ped.done.shape-keys": "Shape keys de {count} malhas removidas.",
    "ped.op.scale": "Escalar",
    "ped.op.scale.desc": "Escalar o personagem em torno da origem, como faz uma mudança de unidades",
    "ped.op.scale-by": "Escalar por {factor}",
    "ped.confirm.scale": "Escalar o personagem por {factor}?",
    "ped.done.scaled": "Personagem escalado por {factor}.",
    "ped.op.turn": "Girar",
    "ped.op.turn.desc": "Girar o personagem em passos de 90 graus",
    "ped.op.stand-up": "Colocar em pé",
    "ped.op.stand-up-other": "Colocar em pé do outro jeito",
    "ped.op.turn-over": "Desvirar",
    "ped.op.turn-left": "Girar 90° à esquerda",
    "ped.op.turn-right": "Girar 90° à direita",
    "ped.op.turn-around": "Girar 180°",
    "ped.confirm.turn": "Girar o personagem? Você pode desfazer com Ctrl+Z.",
    "ped.done.turned": "Personagem girado.",
    "ped.op.to-origin": "Mover para a origem",
    "ped.op.to-origin.desc": "Mover o personagem para que ele fique em pé no chão, na origem",
    "ped.done.origin": "O personagem agora está na origem.",
    "ped.op.confirm-facing": "Ele está de frente",
    "ped.op.confirm-facing.desc": (
        "Confirmar que o personagem está de frente na vista frontal, com o lado esquerdo dele à sua direita"
    ),
    "ped.confirm.facing": (
        "O personagem está de frente para você na vista frontal (Numpad 1), com a mão esquerda dele à sua direita?"
    ),
    "ped.heading.parts": "Partes ({count})",
    "ped.parts.subtext": (
        "Cabelo, olhos e dentes recebem pesos de outro jeito, e o cabelo vira o cabelo do ped. Mude a função quando o "
        "palpite estiver errado."
    ),
    "ped.parts.guess": "Palpite: {role}",
    "ped.prop.role": "Função da parte",
    "ped.prop.role.desc": "O que esta malha é: define como ela recebe pesos e onde ela entra no ped",
    "ped.role.auto": "Automática",
    "ped.role.auto.desc": "Adivinhar a função pelos nomes da malha e dos materiais dela",
    "ped.role.body": "Corpo",
    "ped.role.body.desc": "Pele e roupas que se movem com o corpo",
    "ped.role.head": "Cabeça e rosto",
    "ped.role.head.desc": "A cabeça, o rosto, as sobrancelhas e os cílios",
    "ped.role.hair": "Cabelo",
    "ped.role.hair.desc": "Cabelo, cards de barba e outros pelos que se movem com a cabeça",
    "ped.role.eyes": "Olhos",
    "ped.role.eyes.desc": "Os globos oculares, movidos pelos ossos dos olhos ou pela cabeça",
    "ped.role.teeth": "Dentes",
    "ped.role.teeth.desc": "Dentes e língua, movidos pela cabeça",
    "ped.role.accessory": "Acessório",
    "ped.role.accessory.desc": "Óculos, joias e outras coisas que o personagem usa",
    # ---- 2. Markers -----------------------------------------------------------------------------------
    "ped.heading.markers": "Marcadores de articulação",
    "info.ped-markers": (
        "Os marcadores mostram ao Durty Cloth Tool onde ficam as articulações do seu personagem: dentro do corpo, no "
        "meio de cada articulação. Os marcadores da esquerda são azuis e os da direita, laranja; a esquerda do "
        "personagem fica à sua direita na vista frontal."
    ),
    "ped.markers.placed": "{placed} de {total} posicionados",
    "ped.op.guide": "Guia de cliques",
    "ped.op.guide.desc": (
        "Clicar, um após o outro, nos pontos que uma figura mostra na vista 3D; os demais são posicionados a partir "
        "deles"
    ),
    "ped.op.auto-markers": "Marcadores automáticos",
    "ped.op.auto-markers.desc": "Posicionar todos os marcadores a partir da forma do personagem. Confira-os depois",
    "ped.op.from-rig": "Do rig antigo",
    "ped.op.from-rig.desc": (
        "Posicionar os marcadores nas articulações do rig antigo do personagem (Mixamo, Unreal, Rigify, Character "
        "Creator ou VRM)"
    ),
    "ped.op.mirror": "Espelhar",
    "ped.op.mirror.desc": "Copiar os marcadores de um lado para o outro, espelhados em relação ao meio do personagem",
    "ped.op.mirror-left": "Esquerda para direita",
    "ped.op.mirror-right": "Direita para esquerda",
    "ped.op.show": "Mostrar",
    "ped.op.show-markers.desc": "Selecionar estes marcadores na vista 3D",
    "ped.prop.marker-size": "Tamanho dos marcadores",
    "ped.prop.marker-size.desc": "O tamanho com que as esferas dos marcadores são desenhadas",
    "ped.prop.follow": "Mover cotovelos e joelhos junto",
    "ped.prop.follow.desc": (
        "Quando você move um marcador de pulso, ombro, tornozelo ou quadril, o cotovelo ou o joelho entre eles "
        "acompanha o membro"
    ),
    "ped.done.auto-markers": (
        "Marcadores posicionados a partir da forma do personagem. Confira cada um e mova os que estiverem fora do "
        "lugar."
    ),
    "ped.done.from-rig": "Marcadores posicionados nas articulações do rig {rig}. Confira o queixo e o topo da cabeça.",
    "ped.done.mirrored": "Marcadores espelhados.",
    "ped.rig-kind.mixamo": "Mixamo",
    "ped.rig-kind.unreal": "Unreal",
    "ped.rig-kind.rigify": "Rigify",
    "ped.rig-kind.cc": "Character Creator",
    "ped.rig-kind.vrm": "VRM",
    "ped.marker-error.too-small": (
        "O personagem é pequeno demais ou não está em pé: Marcadores automáticos não encontrou nenhuma pessoa."
    ),
    "ped.marker-error.guide-incomplete": (
        "O guia de cliques precisa de todos os pontos dele antes de posicionar os outros."
    ),
    "ped.marker-error.no-rig": (
        "O personagem não tem rig antigo com nomes de ossos conhecidos (Mixamo, Unreal, Rigify, Character Creator ou "
        "VRM)."
    ),
    "ped.marker-note.arms": "Não foi possível separar os braços do corpo: confira os ombros, os cotovelos e os pulsos.",
    "ped.marker-note.legs": "Não foi possível separar as pernas: confira os quadris, os joelhos e os tornozelos.",
    "ped.marker-note.neck": "Foi difícil encontrar o pescoço: confira o pescoço, o queixo e o peito.",
    "ped.marker-problem.missing": "Marcadores faltando: {names}.",
    "ped.marker-problem.side": (
        "No lado errado: {names}. A esquerda do personagem precisa ficar em +X, à sua direita na vista frontal."
    ),
    "ped.marker-problem.order": "Fora da ordem da cabeça para baixo: {names}.",
    "ped.marker-problem.asymmetric": "Os membros da esquerda e da direita diferem mais de 30 %: {names}.",
    "ped.marker-problem.outside": "Fora do personagem: {names}.",
    "ped.marker.headTop": "Topo da cabeça",
    "ped.marker.chin": "Queixo",
    "ped.marker.neck": "Pescoço",
    "ped.marker.chest": "Peito",
    "ped.marker.pelvis": "Pélvis",
    "ped.marker.shoulderL": "Ombro esquerdo",
    "ped.marker.shoulderR": "Ombro direito",
    "ped.marker.elbowL": "Cotovelo esquerdo",
    "ped.marker.elbowR": "Cotovelo direito",
    "ped.marker.wristL": "Pulso esquerdo",
    "ped.marker.wristR": "Pulso direito",
    "ped.marker.hipL": "Quadril esquerdo",
    "ped.marker.hipR": "Quadril direito",
    "ped.marker.kneeL": "Joelho esquerdo",
    "ped.marker.kneeR": "Joelho direito",
    "ped.marker.ankleL": "Tornozelo esquerdo",
    "ped.marker.ankleR": "Tornozelo direito",
    "ped.marker.toeL": "Dedos do pé esquerdo",
    "ped.marker.toeR": "Dedos do pé direito",
    "ped.guide.title": "Guia de cliques: ponto {index} de {total}",
    "ped.guide.keys": (
        "Clique: posicionar o ponto. Clique direito: voltar um ponto. Roda e botão do meio do mouse: vista. Esc: parar."
    ),
    "ped.guide.headTop": "Clique no topo da cabeça.",
    "ped.guide.chin": "Clique na ponta do queixo.",
    "ped.guide.shoulderL": "Clique na articulação do ombro esquerdo (à sua direita na vista frontal).",
    "ped.guide.shoulderR": "Clique na articulação do ombro direito (à sua esquerda).",
    "ped.guide.wristL": "Clique no meio do pulso esquerdo.",
    "ped.guide.wristR": "Clique no meio do pulso direito.",
    "ped.guide.hipL": "Clique na articulação do quadril esquerdo, onde a perna encontra o corpo.",
    "ped.guide.hipR": "Clique na articulação do quadril direito.",
    "ped.guide.ankleL": "Clique no meio do tornozelo esquerdo.",
    "ped.guide.ankleR": "Clique no meio do tornozelo direito.",
    "ped.guide.toeL": "Clique no pé esquerdo, onde os dedos dobram.",
    "ped.guide.toeR": "Clique no pé direito, onde os dedos dobram.",
    "ped.guide.finish": "Todos os pontos posicionados. Aperte Enter.",
    "ped.guide.missed": "Esse clique não acertou o personagem. Clique nele.",
    "ped.guide.done": (
        "Todos os pontos posicionados; o pescoço, o peito, a pélvis, os cotovelos e os joelhos foram posicionados a "
        "partir deles. Confira-os e mova os que estiverem fora do lugar."
    ),
    # ---- 3. Rig ---------------------------------------------------------------------------------------
    "ped.heading.template": "Modelo base",
    "info.ped-template": (
        "O ped instalado do GTA V a partir do qual o seu ped é montado: o esqueleto, o jeito de andar, a voz e as "
        "formas do corpo dele. Escolha um parecido com o seu personagem: o mesmo gênero e um porte parecido."
    ),
    "ped.prop.template": "Modelo base",
    "ped.prop.template.desc": "O ped instalado cujo esqueleto o seu personagem recebe",
    "ped.prop.gender": "Gênero",
    "ped.gender.any": "Qualquer",
    "ped.gender.any.desc": "Listar modelos base dos dois gêneros",
    "ped.gender.male.desc": "Listar modelos base masculinos",
    "ped.gender.female.desc": "Listar modelos base femininos",
    "ped.prop.show-all": "Mostrar todos",
    "ped.prop.show-all.desc": (
        "Listar também peds freemode, de jogador, de cutscene e da história, não só os de ambiente"
    ),
    "ped.template.choose": "Escolher um modelo base",
    "ped.template.recommended": "{model} (recomendado)",
    "ped.template.facts": "{facts}",
    "ped.templates.loading": (
        "O Durty Cloth Tool está lendo os seus arquivos do jogo (alguns segundos na primeira vez)."
    ),
    "ped.templates.refresh": "Escolha Atualizar para listar os modelos base instalados com o seu jogo.",
    "ped.templates.none": "Nenhum modelo base corresponde. Ligue Mostrar todos ou escolha outro gênero.",
    "ped.templates.truncated": "O Durty Cloth Tool lista os primeiros {count}. Escolha um gênero para ver os outros.",
    "ped.group.ambient": "ambiente",
    "ped.group.freemode": "freemode",
    "ped.group.player": "jogador",
    "ped.group.cutscene": "cutscene",
    "ped.group.story": "história",
    "ped.layout.packed": "empacotado",
    "ped.layout.streamed": "em streaming",
    "ped.op.refresh": "Atualizar",
    "ped.op.refresh.desc": "Pedir de novo ao Durty Cloth Tool os modelos base instalados com o seu jogo",
    "ped.op.use-template": "Usar modelo base",
    "ped.op.use-template.desc": "Usar este ped instalado como modelo base",
    "ped.op.use-template-named": "Usar {template}",
    "ped.rights.title": "Seus direitos sobre este personagem",
    "ped.rights.text": (
        "Converta só personagens que você mesmo fez ou que tem permissão para usar em recursos do GTA V (por exemplo, "
        "uma licença que permita modificação e redistribuição). Personagens tirados de outros jogos, filmes ou "
        "criadores geralmente não podem ser convertidos nem compartilhados. Você é responsável pelos personagens que "
        "converte e publica."
    ),
    "ped.rights.check": "Eu fiz este personagem ou tenho os direitos para convertê-lo e usá-lo",
    "ped.rights.done": "Você confirmou os seus direitos sobre este personagem.",
    "ped.op.rig": "Fazer o rig no Durty Cloth Tool",
    "ped.op.rig.desc": (
        "O Durty Cloth Tool ajusta o esqueleto do modelo base aos seus marcadores e calcula os pesos e a pose de "
        "repouso do jogo, a partir dos seus próprios arquivos do jogo"
    ),
    "ped.op.rig-again": "Fazer o rig de novo",
    "ped.op.cancel-rig.desc": "Parar o rig no Durty Cloth Tool",
    "ped.rig.waiting": "Aguardando o Durty Cloth Tool iniciar o rig.",
    "ped.rig.cancelling": "Cancelando o rig.",
    "ped.rig.working": "Fazendo o rig",
    "ped.rig.progress": "{stage} ({percent} %)",
    "ped.stage.template": "Lendo o modelo base",
    "ped.stage.markers": "Verificando os marcadores",
    "ped.stage.skeleton": "Ajustando o esqueleto",
    "ped.stage.weights": "Transferindo os pesos",
    "ped.stage.rest": "Convertendo para a pose de repouso do jogo",
    "ped.stage.report": "Escrevendo o relatório",
    "ped.prop.refine": "Refinar marcadores",
    "ped.prop.refine.desc": (
        "O Durty Cloth Tool move os marcadores para o meio dos membros e do corpo e mostra para onde"
    ),
    "ped.prop.fingers": "Dedos",
    "ped.fingers.off": "Mover com a mão",
    "ped.fingers.off.desc": "Os dedos se movem junto com a mão, como numa luva sem divisão para os dedos",
    "ped.fingers.auto": "Automática",
    "ped.fingers.auto.desc": "Dar pesos aos dedos a partir da mão do modelo base",
    "ped.prop.face": "Rosto",
    "ped.face.off": "Mover com a cabeça",
    "ped.face.off.desc": "O rosto se move com a cabeça",
    "ped.face.auto": "Automática",
    "ped.face.auto.desc": "Dar pesos ao rosto a partir do rosto do modelo base, para expressões",
    "ped.prop.roll": "Ossos de torção",
    "ped.prop.roll.desc": (
        "Dar pesos aos ossos de torção dos braços e das pernas, que evitam que pulsos e coxas colapsem"
    ),
    "ped.prop.helpers": "Ossos auxiliares",
    "ped.prop.helpers.desc": "Dar pesos aos ossos auxiliares do modelo base, como no corpo dele",
    "ped.prop.rest": "Forma de repouso",
    "ped.rest.volume": "Manter volume",
    "ped.rest.volume.desc": "Levar o personagem à pose de repouso de forma que ombros e quadris mantenham o volume",
    "ped.rest.linear": "Exata",
    "ped.rest.linear.desc": (
        "Levar o personagem à pose de repouso de forma que o skinning do jogo devolva exatamente a sua pose"
    ),
    "ped.result.ready": "Pronto (confiança {percent} %)",
    "ped.result.review": "Precisa de revisão (confiança {percent} %)",
    "ped.result.markers": "({names})",
    "ped.result.moved": "O Durty Cloth Tool moveu {count} marcadores para o meio do corpo (amarelos na vista 3D):",
    "ped.result.move": "{marker}: {cm} cm",
    "ped.result.subtext": (
        "Aplicar rig cria a armature e dá às malhas os pesos e a pose de repouso do jogo. O seu personagem mantém a "
        "aparência, e Ctrl+Z desfaz isso."
    ),
    "ped.result.proxy": "Os pesos foram calculados numa cópia simplificada desta malha grande.",
    "ped.op.apply-rig": "Aplicar rig",
    "ped.op.apply-rig.desc": (
        "Criar a armature a partir do rig e dar às malhas os pesos dele e a pose de repouso do jogo; o personagem "
        "mantém a aparência"
    ),
    "ped.op.use-refined": "Usar estes marcadores",
    "ped.op.use-refined.desc": "Mover os seus marcadores para onde o Durty Cloth Tool os colocou",
    "ped.op.discard-rig": "Descartar",
    "ped.op.discard-rig.desc": "Jogar este rig fora sem aplicá-lo",
    "ped.done.applied": "Rig aplicado: a armature {name} tem {bones} ossos.",
    "ped.done.refined": "Os seus marcadores agora estão onde o Durty Cloth Tool os colocou.",
    "ped.rigged.line": "Rig a partir de {template} ({bones} ossos)",
    "ped.op.previous-rig": "Rig anterior",
    "ped.op.previous-rig.desc": "Trocar o rig aplicado pelo que foi aplicado antes dele",
    "ped.done.previous": "O rig anterior voltou.",
    "ped.op.remove-rig": "Remover rig",
    "ped.op.remove-rig.desc": "Tirar o rig: o personagem fica como era antes do primeiro rig",
    "ped.confirm.remove-rig": (
        "Remover o rig? As armatures são removidas e o personagem fica como era antes do primeiro rig."
    ),
    "ped.done.removed": "Rig removido. O personagem está como era antes do rig.",
    "ped.warning.marker_offset": (
        "{count} marcadores estavam a mais de 2 cm do meio do corpo (até {value} mm). Confira-os."
    ),
    "ped.warning.asymmetric_markers": (
        "Os marcadores da esquerda e da direita diferem mais de 5 %. Confira os dois lados."
    ),
    "ped.warning.proportion_out_of_range": (
        "Algumas proporções estão longe das do modelo base. Um modelo base de porte mais parecido se move melhor."
    ),
    "ped.warning.ragdoll_mismatch": (
        "A altura deste personagem está longe da do modelo base dele. No jogo, tiros e quedas usam as formas do corpo "
        "do modelo base, então acertos podem errar ou cair ao lado do modelo. Escolha um modelo base mais próximo ou "
        "teste no jogo antes de publicar."
    ),
    "ped.warning.low_coverage": (
        "Só uma parte do personagem combinou com o corpo do modelo base. Confira os pesos nas poses de teste."
    ),
    "ped.warning.inpainted_large": "Muitos pesos foram preenchidos a partir dos vizinhos. Confira as poses de teste.",
    "ped.warning.non_deforming_moved": "Alguns pesos foram tirados de ossos que nunca movem a malha.",
    "ped.warning.empty_rows_refilled": "{count} vértices não tinham pesos e receberam os dos vizinhos.",
    "ped.warning.floating_parts": "{count} partes soltas foram presas ao osso mais próximo.",
    "ped.warning.rest_strain": (
        "Alguns triângulos se dobram na pose de repouso do jogo. Olhe os ombros e os quadris em Pose de repouso do "
        "jogo."
    ),
    "ped.warning.fingers_fallback": "Os dedos se movem com a mão.",
    "ped.warning.other": "O Durty Cloth Tool informou {code}.",
    "ped.suggest": (
        "{template} está mais perto das proporções do seu personagem. Use-o e faça o rig de novo para um ajuste melhor."
    ),
    "ped.refusal.marker_missing": "Faltam marcadores.",
    "ped.refusal.marker_invalid": "Alguns marcadores não podem ser usados. Posicione-os no personagem de novo.",
    "ped.refusal.marker_degenerate": "Alguns marcadores estão uns em cima dos outros.",
    "ped.refusal.marker_side": (
        "Esquerda e direita estão trocadas. A esquerda do personagem precisa ficar em +X: confira se ele está de "
        "frente."
    ),
    "ped.refusal.not_upright": "O personagem não está em pé, ou a cabeça dele está abaixo do pescoço.",
    "ped.refusal.limb_length": (
        "Um membro é muito mais curto ou mais longo que o do modelo base. Confira estes marcadores."
    ),
    "ped.refusal.asymmetric": "Os membros da esquerda e da direita diferem mais de 30 %.",
    "ped.refusal.pose_unsupported": (
        "Uma perna está dobrada ou aberta demais. Coloque o personagem em pé e reto, em A-pose ou T-pose."
    ),
    "ped.refusal.marker_outside_body": "Estes marcadores ficam fora do personagem.",
    "ped.refusal.mesh_invalid": (
        "O Durty Cloth Tool não conseguiu ler a malha (vazia, ou com triângulos quase todos achatados)."
    ),
    "ped.refusal.mesh_too_large": (
        "O personagem tem vértices ou triângulos demais para um rig. Reduza primeiro uma cópia."
    ),
    "ped.refusal.options_invalid": "O Durty Cloth Tool recusou as opções do rig. Atualize o add-on.",
    "ped.refusal.template_invalid": "O Durty Cloth Tool não pode usar este modelo base. Escolha outro.",
    "ped.refusal.template_not_found": "Este modelo base não está instalado. Atualize a lista e escolha outro.",
    "ped.refusal.game_required": (
        "O Durty Cloth Tool precisa da sua pasta do GTA V. Defina-a nas configurações do Durty Cloth Tool."
    ),
    "ped.refusal.fit_invalid": (
        "O rig saiu quebrado. Confira os marcadores em relação ao personagem e faça o rig de novo."
    ),
    "ped.refusal.other": "O Durty Cloth Tool recusou o rig ({code}).",
    # ---- 4. Check -------------------------------------------------------------------------------------
    "ped.heading.poses": "Poses de teste",
    "info.ped-poses": (
        "Dobras simples pelo nome dos ossos, para ver como os pesos movem o personagem. Não são animações do jogo; "
        "pequenos vincos nos extremos são normais."
    ),
    "ped.pose.yours": "Sua pose",
    "ped.pose.rest": "Pose de repouso do jogo",
    "ped.pose.arms_up": "Braços para cima",
    "ped.pose.arms_forward": "Braços para a frente",
    "ped.pose.squat": "Agachamento",
    "ped.pose.walk": "Passo de caminhada",
    "ped.pose.twist": "Torção",
    "ped.op.pose": "Pose",
    "ped.op.pose.desc": "Mostrar o personagem nesta pose",
    "ped.op.run-checks": "Executar verificações",
    "ped.op.run-checks.desc": "Verificar os pesos, a armature e as malhas em relação ao rig, e as poses de teste",
    "ped.op.show-finding.desc": "Selecionar os vértices a que esta ocorrência se refere",
    "ped.done.checks": (
        "Executar verificações encontrou {count} pontos para conferir; nada que o Durty Cloth Tool recusaria."
    ),
    "ped.done.checks-refused": "Executar verificações encontrou {count} problemas que o Durty Cloth Tool recusaria.",
    "ped.local.none": "Nenhum problema encontrado.",
    "ped.local.unweighted": "{count} vértices não têm peso. O Durty Cloth Tool os recusa: dê pesos a eles.",
    "ped.local.too-many": "{count} vértices têm mais de quatro ossos. O jogo mantém os quatro mais fortes.",
    "ped.local.non-deforming": "{count} vértices têm pesos em ossos que nunca movem a malha.",
    "ped.local.unknown-groups": "Grupos de vértices que não são ossos ({names}) ficam de fora.",
    "ped.local.armature-changed": (
        "{count} ossos foram movidos ou girados depois do rig ({names}). Desfaça isso ou faça o rig de novo: os ossos "
        "mantêm a rotação do modelo base."
    ),
    "ped.local.mesh-changed": (
        "As malhas mudaram depois do rig (vértices adicionados ou removidos). Faça o rig de novo."
    ),
    "ped.local.strain": "{count} vértices esticam ou se comprimem muito em {pose}.",
    "ped.local.hint": (
        "Pequenos vincos em poses extremas são normais. Para vincos maiores, mova um marcador e faça o rig de novo."
    ),
    # ---- 5. Send --------------------------------------------------------------------------------------
    "ped.prop.name": "Nome do ped",
    "ped.prop.name.desc": "O nome que o Durty Cloth Tool mostra para o ped",
    "ped.prop.model": "Nome do modelo",
    "ped.prop.model.desc": (
        "O nome do novo ped no jogo: uma letra minúscula e depois de 2 a 31 letras minúsculas, dígitos ou sublinhados"
    ),
    "ped.prop.ragdoll": "Corpo de ragdoll",
    "ped.ragdoll.template": "Como o modelo base",
    "ped.ragdoll.template.desc": "O corpo de ragdoll compartilhado que o modelo base usa",
    "ped.ragdoll.fred": "Masculino padrão",
    "ped.ragdoll.fred.desc": "O corpo de ragdoll compartilhado da maioria dos peds masculinos",
    "ped.ragdoll.wilma": "Feminino padrão",
    "ped.ragdoll.wilma.desc": "O corpo de ragdoll compartilhado da maioria dos peds femininos",
    "ped.ragdoll.fred-large": "Masculino grande",
    "ped.ragdoll.fred-large.desc": "O corpo de ragdoll compartilhado dos peds masculinos grandes",
    "ped.ragdoll.wilma-large": "Feminino grande",
    "ped.ragdoll.wilma-large.desc": "O corpo de ragdoll compartilhado dos peds femininos grandes",
    "ped.ragdoll.subtext": (
        "Tiros, quedas e o ragdoll usam as formas deste corpo no jogo. Escolha um grande para um personagem bem maior."
    ),
    "ped.texture": "Imagem {name}: {problem}",
    "ped.op.send": "Criar ped personalizado",
    "ped.op.send.desc": (
        "Exportar o personagem com rig na pose de repouso do jogo e enviá-lo ao Durty Cloth Tool, que cria um novo "
        "projeto de ped personalizado assim que você confirmar lá"
    ),
    "ped.op.cancel-send.desc": "Retirar o personagem enquanto o Durty Cloth Tool ainda está perguntando",
    "ped.send.subtext": (
        "O Durty Cloth Tool mostra o ped com as verificações dele e pergunta onde criar o projeto. Nada é criado até "
        "você escolher Criar projeto lá."
    ),
    "ped.send.waiting": "Personagem enviado ({size} MiB). Escolha Criar projeto no Durty Cloth Tool.",
    "ped.send.withdrawing": "Retirando o personagem.",
    "ped.send.withdrawn": "Retirado: o Durty Cloth Tool não criou nada.",
    "ped.send.created": "O Durty Cloth Tool criou o projeto {name} com o ped {model} a partir de {template}.",
    "ped.send.findings": "Verificações do Durty Cloth Tool ({count}):",
    "ped.send.next": (
        "Confira o comportamento do ped no Durty Cloth Tool (tipo de ped, jeito de andar, voz) e depois compile o "
        "projeto."
    ),
    "ped.finding.rig-mismatch": (
        "O esqueleto não é o do modelo base nem o do rig: um osso foi movido ou girado. Aplique o rig de novo, ou faça "
        "o rig de novo."
    ),
    "ped.finding.ped-budget": "Mais vértices do que um ped deveria ter no nível de detalhe mais alto.",
    "ped.finding.ped-ragdoll-mismatch": (
        "A altura do personagem está longe da do corpo de ragdoll do modelo base: acertos e quedas no jogo usam as "
        "formas do corpo do modelo base."
    ),
    "ped.finding.ped-rest-strain": "O rig dobrou alguns triângulos na pose de repouso do jogo.",
    # ---- why something cannot run -----------------------------------------------------------------------
    "ped.why.select-meshes": "Selecione as malhas do seu personagem primeiro.",
    "ped.why.no-character": "Escolha o seu personagem em Personagem primeiro.",
    "ped.why.object-mode": "Mude para o Object Mode primeiro.",
    "ped.why.rigged": "O personagem já tem rig. Remova o rig para alterá-lo.",
    "ped.why.no-markers": "Posicione os marcadores primeiro.",
    "ped.why.guide-running": "O guia de cliques está em andamento.",
    "ped.why.view3d": "Inicie o guia de cliques pela barra lateral da vista 3D.",
    "ped.why.checks": "Corrija primeiro o que as verificações em Personagem apontam.",
    "ped.why.markers": "Posicione todos os marcadores primeiro.",
    "ped.why.connect": "Conecte-se ao Durty Cloth Tool para escolher um modelo base e fazer o rig.",
    "ped.why.template": "Escolha um modelo base primeiro.",
    "ped.why.rights": "Confirme primeiro os seus direitos sobre este personagem.",
    "ped.why.rigging": "Um rig está em andamento no Durty Cloth Tool.",
    "ped.why.not-rigging": "Nenhum rig está em andamento.",
    "ped.why.no-result": "Não há rig para aplicar. Faça o rig do personagem primeiro.",
    "ped.why.no-previous": "Não há rig anterior.",
    "ped.why.not-rigged": "Faça o rig do personagem primeiro.",
    "ped.why.mesh-changed": "As malhas do personagem mudaram depois que você pediu este rig. Faça o rig de novo.",
    "ped.why.vertex-count": (
        "{name} muda a contagem de vértices num modificador. Aplique os modificadores dele primeiro."
    ),
    "ped.why.modifiers-shape-keys": (
        "{name} tem shape keys, então os modificadores dele não podem ser aplicados. Remova-as primeiro."
    ),
    "ped.why.export-failed": "O exportador glTF do Blender não gravou o personagem. O log Info dele tem os detalhes.",
    "ped.why.model": (
        "O nome do modelo é uma letra minúscula e depois de 2 a 31 letras minúsculas, dígitos ou sublinhados."
    ),
    "ped.why.model-game": (
        "Nomes que começam com {prefix} pertencem aos peds do próprio jogo. Escolha outro, como {suggestion}."
    ),
    "ped.why.name": "Dê um nome ao ped.",
    "ped.why.refused-checks": (
        "Executar verificações encontrou problemas que o Durty Cloth Tool recusaria. Corrija-os primeiro."
    ),
    "ped.why.textures": "Uma imagem é grande demais ou o tamanho dela não é divisível por quatro. Corrija-a primeiro.",
    "ped.why.sending": "Um ped personalizado está sendo enviado.",
    "ped.why.not-sending": "Nada está sendo enviado.",
    "ped.invalid": "O add-on não conseguiu preparar este pedido: {detail}",
    # ---- plans and Durty Cloth Tool's answers -----------------------------------------------------------
    "ped.plan.rig": "O rigging está incluído no Durty Cloth Tool Ultimate.",
    "ped.plan.add": "Criar um projeto de ped personalizado precisa do Durty Cloth Tool Advanced ou Ultimate.",
    "ped.error.rig-busy": (
        "O Durty Cloth Tool está fazendo o rig de outro personagem. Tente de novo quando ele terminar."
    ),
    "ped.error.rig-cancelled": "O rig foi cancelado.",
    "ped.error.rig-refused": "O Durty Cloth Tool não conseguiu fazer o rig do personagem:",
    "ped.error.dct-too-old": (
        "Este Durty Cloth Tool ainda não cria peds personalizados a partir do Blender. Atualize o Durty Cloth Tool."
    ),
    "ped.error.rig-disconnected": "A conexão com o Durty Cloth Tool terminou durante o rig. Faça o rig de novo.",
    "ped.error.rig-timeout": "O Durty Cloth Tool não terminou o rig a tempo. Faça o rig de novo.",
    "ped.error.add-busy": (
        "O Durty Cloth Tool está ocupado com outro ped personalizado ou uma compilação. Tente de novo quando ele "
        "terminar."
    ),
    "ped.error.add-denied": "Cancelado no Durty Cloth Tool. Envie o personagem de novo quando estiver pronto.",
    "ped.error.model-rejected": (
        "O Durty Cloth Tool não conseguiu criar um ped a partir do personagem. As verificações dele abaixo dizem o "
        "motivo."
    ),
    "ped.error.save-failed": "O Durty Cloth Tool não conseguiu criar o projeto. Escolha outra pasta e envie de novo.",
    "ped.error.add-disconnected": (
        "A conexão com o Durty Cloth Tool terminou antes da resposta. Envie o personagem de novo."
    ),
    "ped.error.add-timeout": "O Durty Cloth Tool não respondeu a tempo. Envie o personagem de novo.",
    "ped.error.add-unanswered": "O Durty Cloth Tool não confirmou a retirada. Confira a lista de projetos dele.",
    # ---- protocol errors --------------------------------------------------------------------------------
    "error.template-not-found": "Este modelo base não está instalado. Atualize a lista e escolha outro.",
    "error.mesh-too-large": "O personagem tem vértices ou triângulos demais. Reduza primeiro uma cópia.",
    "error.rig-refused": "O Durty Cloth Tool não conseguiu fazer o rig do personagem.",
    "error.upload-incomplete": "O personagem não chegou completo ao Durty Cloth Tool. Envie-o de novo.",
}
