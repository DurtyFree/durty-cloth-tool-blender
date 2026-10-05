# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2026 Schmid Software Solutions (https://schmid-software.de)
"""Brazilian Portuguese (Português do Brasil). "você", as Durty Cloth Tool uses it; also used for Portugal."""

TEXT = {
    "path.connected-apps": "Opções > Apps conectados",
    "path.edit-in-app": "Editar no app conectado",
    "panel.main": "Durty Cloth Tool",
    "panel.details": "Conexão",
    "panel.setup": "Conectar",
    "panel.linked": "Roupa vinculada",
    "panel.live": "Pré-visualização ao vivo",
    "panel.checks": "Verificação da textura",
    "panel.model": "Modelo",
    "panel.settings": "Configurações",
    "chip.connected": "Conectado",
    "chip.live": "Ao vivo",
    "chip.connecting": "Conectando",
    "chip.action": "Ação necessária",
    "chip.offline": "Offline",
    "chip.problem": "Problema",
    "state.idle": "Não conectado",
    "state.connecting": "Procurando o Durty Cloth Tool",
    "state.waiting": "Durty Cloth Tool não encontrado. Tentando de novo em breve",
    "state.reconnecting": "Reconectando ao Durty Cloth Tool",
    "state.hello": "Conectando",
    "state.signing-in": "Aguardando o login",
    "state.authenticating": "Entrando",
    "state.ready": "Conectado como {name}",
    "state.signed-out": "Desconectado da conta",
    "state.dct-signed-out": "O Durty Cloth Tool está sem login",
    "state.dct-disconnected": "Desconectado no Durty Cloth Tool",
    "details.status": "Status: {state}",
    "details.account": "Conectado como {name}",
    "details.not-signed-in": "Sem login",
    "details.project": "Projeto: {name}",
    "details.addon": "Add-on {version} ({channel})",
    "online.off": (
        "O acesso online do Blender está desligado, então o Durty Cloth Tool não pode ser conectado: cada conexão é "
        "confirmada com o seu login do gta.clothing. Permita em Preferências > Sistema > Rede."
    ),
    "dct-signed-out": (
        "O Durty Cloth Tool está sem login. Entre no Durty Cloth Tool e depois escolha Conectar. O add-on também tenta "
        "de novo sozinho de tempos em tempos."
    ),
    "dct-disconnected": "Este app foi desconectado no Durty Cloth Tool. Escolha Conectar para conectá-lo de novo.",
    "setup.find.title": "Encontrar o Durty Cloth Tool",
    "setup.find.done": "Durty Cloth Tool encontrado",
    "setup.find.subtext": "Abra o Durty Cloth Tool neste computador. O add-on o encontra automaticamente.",
    "setup.find.searching": "Procurando o Durty Cloth Tool…",
    "setup.find.waiting": "O Durty Cloth Tool ainda não está aberto. O add-on continua procurando…",
    "setup.sign-in.title": "Entrar com o gta.clothing",
    "setup.sign-in.done": "Login feito",
    "setup.sign-in.subtext": (
        "O Creator Link usa a sua conta do gta.clothing (Discord). Você entra uma vez neste computador."
    ),
    "setup.sign-in.starting": "Iniciando o login…",
    "setup.sign-in.finding": "Procurando o Durty Cloth Tool para aprovar o login…",
    "setup.sign-in.how": (
        "O Durty Cloth Tool pede que você aprove. Se ele não estiver aberto, você recebe um código para o navegador."
    ),
    "setup.sign-in.waiting": "Aguardando a aprovação…",
    "setup.sign-in.asked": "O Durty Cloth Tool mostra um pedido de login. Aprove lá.",
    "setup.sign-in.approved": "O Durty Cloth Tool aprovou o login. Finalizando…",
    "setup.sign-in.declined": "O Durty Cloth Tool não aprovou o login. Entre pelo navegador.",
    "setup.sign-in.browser-subtext": "Abra a página de login e confira se ela mostra este código:",
    "setup.sign-in.signed-out": "Você saiu. Entre de novo para usar o Creator Link.",
    "linked.project": "Projeto: {name}",
    "linked.no-project": "Abra um projeto no Durty Cloth Tool.",
    "linked.no-cloth": "Selecione uma roupa no Durty Cloth Tool para trabalhar nela aqui.",
    "linked.variation": "Variação {letter}",
    "linked.number": "#{number}",
    "linked.unknown": "Roupa vinculada",
    "linked.unknown-subtext": "Selecione-a uma vez no Durty Cloth Tool para ver o nome dela aqui.",
    "linked.map": "Mapa",
    "linked.follows": "Segue a sua seleção no Durty Cloth Tool",
    "linked.image": "Vinculada à imagem abaixo",
    "linked.open-map": "Abrir um mapa no Blender",
    "linked.map-missing.diffuse": "Esta roupa não tem mapa difuso.",
    "linked.map-missing.normal": "Esta roupa não tem mapa normal.",
    "linked.map-missing.specular": "Esta roupa não tem mapa especular.",
    "map.diffuse": "Difusa (cor)",
    "map.diffuse-short": "Difusa",
    "map.diffuse.desc": "A textura de cor da roupa",
    "map.normal": "Normal",
    "map.normal.desc": "O mapa normal da roupa",
    "map.specular": "Especular",
    "map.specular.desc": "O mapa especular da roupa",
    "gender.male": "Masculino",
    "gender.female": "Feminino",
    "open.opened": "Aberto pelo Durty Cloth Tool: {name}",
    "open.texture-busy": (
        "O Durty Cloth Tool enviou {name}, mas uma pré-visualização ao vivo está rodando ou salvando. Pare-a e envie o "
        "mapa de novo."
    ),
    "open.texture-failed": "Não foi possível abrir {name}: {detail}",
    "open.stop-live-first": "Pare a pré-visualização ao vivo primeiro.",
    "open.reading": "Lendo o mapa do Durty Cloth Tool…",
    "open.map-upsell": "Abrir aqui os mapas de uma roupa está incluído no Durty Cloth Tool Ultimate.",
    "open.model-importing": "Importando {name} com o Sollumz…",
    "open.model-needs-sollumz": "O Durty Cloth Tool enviou o modelo {name}. {problem}",
    "open.model-busy": (
        "O Durty Cloth Tool enviou o modelo {name}, mas outro modelo ainda está sendo enviado ou salvo. Envie de novo "
        "daqui a pouco."
    ),
    "open.model-failed": "Não foi possível abrir o modelo {name}: {detail}",
    "open.import-failed": "O Sollumz não conseguiu importar o modelo ({detail}). O log Info dele tem os detalhes.",
    "open.no-dictionary": "O Sollumz não importou um Drawable Dictionary. O log Info dele tem os detalhes.",
    "live.off": "Inicie a pré-visualização ao vivo para ver a sua pintura no ped.",
    "live.reading": "Lendo a imagem…",
    "live.starting": "Iniciando a pré-visualização ao vivo…",
    "live.on": "Ao vivo no ped",
    "live.sending": "Enviando a imagem…",
    "live.not-worn": "Vista esta roupa no ped no Durty Cloth Tool para vê-la.",
    "live.paused-dct": "A pré-visualização 3D está pausada no Durty Cloth Tool.",
    "live.paused": "Pausado. Suas alterações são enviadas quando você retomar.",
    "live.saving": "Salvando…",
    "live.unsaved": "Ainda não salvo no projeto",
    "live.linked": "Vinculada a {name} · {map}",
    "live.map": "Mapa: {map}",
    "live.save-subtext": (
        "Salvar grava este mapa no seu projeto. Você pode desfazer no Histórico da roupa no Durty Cloth Tool."
    ),
    "live.saved": "Salvo em {name}. Você pode desfazer no Histórico.",
    "live.saved-unnamed": "Salvo na roupa. Você pode desfazer no Histórico.",
    "live.saved-variation": "Salvo como nova variação de {name}.",
    "live.saved-variation-unnamed": "Salvo como nova variação.",
    "live.discarded": "As alterações foram descartadas no Durty Cloth Tool.",
    "live.stopped": "Pré-visualização ao vivo parada.",
    "live.stopped-unsaved": (
        "Pré-visualização ao vivo parada. As alterações não foram salvas no projeto; a imagem no Blender as mantém."
    ),
    "live.failed": "A pré-visualização ao vivo parou após um problema inesperado: {detail}",
    "live.upsell": "A pré-visualização ao vivo está incluída no Durty Cloth Tool Ultimate.",
    "live.save-upsell": "Salvar na roupa está incluído no Durty Cloth Tool Ultimate.",
    "live.image-changed": "O tamanho da imagem mudou. Inicie a pré-visualização ao vivo de novo.",
    "live.image-removed": "A imagem foi removida.",
    "live.no-memory": "Não há memória suficiente para uma imagem tão grande.",
    "colour.non-color-diffuse": "A imagem está em Non-Color; os valores são enviados como cor sem alteração.",
    "colour.unknown-diffuse": (
        "O espaço de cor {space} da imagem é enviado sem conversão; use sRGB para cores exatas."
    ),
    "colour.unknown-data": (
        "Defina o espaço de cor do mapa como Non-Color; os valores {space} são enviados como estão no Blender."
    ),
    "image.none": "Escolha uma imagem primeiro.",
    "image.tiled": "Imagens UDIM (em blocos) não podem ser usadas. Use uma única imagem.",
    "image.source": "Só arquivos de imagem e imagens geradas podem ser usados.",
    "image.unreadable": "Não foi possível ler a imagem.",
    "image.not-loaded": "Não foi possível carregar a imagem. Confira se o arquivo existe.",
    "image.channels": "Só imagens em tons de cinza, RGB e RGBA podem ser usadas.",
    "image.empty": "A imagem não tem pixels. Abra ou crie a imagem primeiro.",
    "image.too-large": "Imagens com mais de {size} pixels de lado não podem ser usadas.",
    "image.no-painted": "Nenhuma imagem pintada encontrada. Escolha a imagem na lista.",
    "checks.errors": "Erros: {count}",
    "checks.warnings": "Avisos: {count}",
    "checks.notes": "Observações: {count}",
    "checks.clean": "Nenhum problema encontrado.",
    "checks.not-checked": "O Durty Cloth Tool verifica a textura quando a pré-visualização ao vivo começa.",
    "checks.checking": "Verificando a textura…",
    "checks.unavailable": "A verificação da textura está incluída no Durty Cloth Tool Ultimate.",
    "severity.error": "Erro",
    "severity.warning": "Aviso",
    "severity.info": "Observação",
    "finding.unknown": "O Durty Cloth Tool informou {code}.",
    "finding.non-power-of-two": "O tamanho não é uma potência de dois (por exemplo 1024 ou 2048).",
    "finding.not-multiple-of-four": "O tamanho não é múltiplo de quatro, o que texturas comprimidas precisam.",
    "finding.too-large": "A textura passa de 2048 pixels de lado, o que usa muita memória do jogo.",
    "finding.too-small": "A textura tem menos de 16 pixels de lado.",
    "finding.size-changed": "O tamanho é diferente da textura salva no projeto.",
    "finding.palette-alpha": (
        "Esta roupa usa uma paleta de cores: o canal alfa escolhe as cores da paleta, então pinte o alfa com cuidado."
    ),
    "finding.cutout-alpha": "Esta roupa usa o alfa como recorte: pixels transparentes ficam ocultos no ped.",
    "finding.hair-ramp": "Isto é cabelo: o jogo o colore com a cor de cabelo que o jogador escolhe.",
    "finding.bc1-alpha": "A textura salva mantém só alfa totalmente transparente ou totalmente opaco.",
    "finding-fix.non-power-of-two": "Redimensione para uma potência de dois, por exemplo 1024 x 1024, antes de salvar.",
    "finding-fix.not-multiple-of-four": (
        "Redimensione para que os dois lados sejam divisíveis por quatro, por exemplo 1024 x 512."
    ),
    "finding-fix.too-large": "Use 2048 pixels ou menos de lado, a não ser que a roupa precise desse detalhe.",
    "finding-fix.too-small": "Use pelo menos 16 pixels de lado.",
    "finding-fix.size-changed": (
        "Salvar substitui a textura neste tamanho. Volte ao tamanho salvo se não queria mudá-lo."
    ),
    "finding-fix.palette-alpha": "Mantenha os valores alfa como estão, a não ser que queira mudar as cores da paleta.",
    "finding-fix.cutout-alpha": "Pinte transparência só onde a roupa deve ficar oculta.",
    "finding-fix.hair-ramp": "Pinte o sombreamento no canal verde e as mechas no canal vermelho, não a cor final.",
    "finding-fix.bc1-alpha": (
        "Use alfa totalmente transparente ou totalmente opaco; bordas suaves se perdem ao salvar."
    ),
    "model.subtext": "Envia o modelo de novo pouco depois que você para de editar.",
    "model.name": "Modelo: {name}",
    "model.sending": "Enviando {name} (texturas: {count})",
    "model.previewing": "Exibido no ped no Durty Cloth Tool. Salve ou descarte lá ou aqui.",
    "model.findings": "O Durty Cloth Tool informou ocorrências: {count}.",
    "model.warnings-paused": (
        "O Sollumz informou avisos, então o envio automático está pausado. Confira o log Info do Sollumz e envie de "
        "novo para retomar."
    ),
    "model.warnings": "O Sollumz informou avisos; o log Info dele tem os detalhes.",
    "model.saving": "Salvando o modelo no Durty Cloth Tool…",
    "model.saved": "Modelo salvo na roupa. Você pode desfazer no Histórico.",
    "model.discarded": "O modelo foi descartado no Durty Cloth Tool.",
    "model.save-retry": "O Durty Cloth Tool ainda está carregando o modelo. Salvando em instantes…",
    "model.save-busy": "O Durty Cloth Tool ainda está ocupado com o modelo. Salve de novo em instantes.",
    "model.block.no-model": "Envie um modelo primeiro.",
    "model.block.saving": "Já está salvando.",
    "model.block.waiting": "Aguarde a resposta do Durty Cloth Tool.",
    "model.block.pushing": "Aguarde o último envio aparecer no Durty Cloth Tool e então salve.",
    "model.block.due": (
        "Suas últimas alterações estão prestes a ser enviadas. Salve quando aparecerem no Durty Cloth Tool."
    ),
    "model.wait.tool": "O envio automático aguarda a ferramenta em uso terminar.",
    "model.wait.mode": "O envio automático aguarda você sair de {mode}.",
    "model.gone": "O modelo enviado não está mais neste arquivo. Envie de novo.",
    "model.failed": "O envio automático falhou: {detail}",
    "model.select": "Selecione o modelo a enviar: um Drawable Dictionary do Sollumz ou um objeto dentro dele.",
    "model.one-root": "Selecione objetos de um único Drawable Dictionary.",
    "model.needs-dictionary": (
        "O Durty Cloth Tool precisa de um Drawable Dictionary. Faça do Drawable um filho de um (Sollumz: Create "
        "Drawable Dictionary) e envie de novo."
    ),
    "model.not-sollumz": "Selecione um Drawable Dictionary do Sollumz ou um objeto dentro dele.",
    "model.unhide": (
        "Mostre o Drawable Dictionary (ou um objeto dentro dele), torne-o selecionável e envie de novo."
    ),
    "model.not-shown": (
        "O modelo não está em nenhuma cena exibida numa janela do Blender. Mostre a cena dele e envie de novo."
    ),
    "model.not-in-layer": "O modelo não está na view layer atual. Mostre-o e envie de novo.",
    "model.export-failed": "O Sollumz não conseguiu exportar o modelo: {detail}",
    "model.not-exported": "O Sollumz não exportou o modelo. O log Info dele tem os detalhes.",
    "sollumz.ready": "Sollumz {version}",
    "sollumz.ready-unknown": "Sollumz",
    "sollumz.missing": "Instale e ative o Sollumz {version} ou mais novo para abrir e enviar modelos.",
    "sollumz.too-old": (
        "Este Sollumz é antigo demais para exportar para o Durty Cloth Tool. Atualize para o Sollumz {version} ou "
        "mais novo."
    ),
    "sollumz.tested": "Testado com o Sollumz {version}.",
    "bundle.unreadable": "Não foi possível ler a pasta de exportação ({detail}).",
    "bundle.not-dictionary": (
        "O Sollumz exportou um drawable ou fragment, não um drawable dictionary. O Durty Cloth Tool precisa de um "
        "Drawable Dictionary: faça do seu Drawable um filho de um (Sollumz: Create Drawable Dictionary) e envie de "
        "novo."
    ),
    "bundle.no-model": "O Sollumz não exportou um modelo. O log Info do Sollumz mostra o motivo.",
    "bundle.several": "O Sollumz exportou vários drawable dictionaries ({count}). Selecione objetos de apenas um.",
    "bundle.bad-name": (
        "'{name}' não pode ser enviado: nomes de arquivo só podem usar letras, dígitos, '_', '-' e '.', não podem "
        "começar com '.' nem conter '..', e têm no máximo 128 caracteres. Renomeie a textura ou o modelo no Blender."
    ),
    "bundle.duplicate": "Duas texturas se chamam '{name}'. Dê um nome diferente a cada textura.",
    "bundle.too-many": "O modelo usa {count} texturas; no máximo {limit} podem ser enviadas.",
    "bundle.empty-file": "'{name}' está vazio. Exporte o modelo de novo.",
    "bundle.too-large": "O modelo e as texturas juntos passam de {size} MiB e não podem ser enviados.",
    "bundle.invalid": "A exportação não pode ser enviada: {detail}",
    "settings.connection": "Conexão",
    "settings.account": "Conta",
    "settings.updates": "Atualizações",
    "settings.privacy": "Privacidade",
    "settings.models": "Modelos",
    "settings.connect-subtext": (
        "Precisa do Durty Cloth Tool neste computador. A conexão fica neste computador; o gta.clothing confirma o "
        "seu login a cada conexão."
    ),
    "settings.signed-in-as": "Conectado como {name}",
    "settings.not-signed-in": "Sem login",
    "settings.signed-out": "Desconectado da conta",
    "settings.sign-out-subtext": "Sair encerra o login do gta.clothing deste add-on neste computador.",
    "settings.device-name-subtext": (
        "A página de aprovação do gta.clothing mostra o nome, para você diferenciar seus computadores."
    ),
    "settings.licence": "GPL-3.0-or-later, Schmid Software Solutions. Mantido por DurtyFree (Pleb Masters).",
    "settings.this-version": "Esta versão: {version} ({channel})",
    "settings.diagnostics-copied": (
        "Diagnóstico copiado. Cole no servidor Pleb Masters Community Discord quando pedir ajuda. Ele contém versões "
        "e códigos de status, sem caminhos de arquivo e sem dados de login."
    ),
    "settings.disk-install": (
        "Esta cópia foi instalada a partir de um arquivo, então o Blender não pode atualizá-la. Para receber "
        "atualizações, arraste para o Blender o link de instalação da página de plugins do gta.clothing."
    ),
    "settings.updates-on": "O Blender atualiza este add-on pelo repositório de extensões do Durty Cloth Tool.",
    "op.plugins-page": "Obter o link de instalação",
    "op.plugins-page.desc": "Abrir a página de plugins do gta.clothing, de onde você arrasta o link de instalação para o Blender",
    "info.channel": (
        "O Experimental recebe recursos e correções novos primeiro e muda com mais frequência. O Release os "
        "recebe depois de testados. Você escolhe o canal pelo link de instalação que arrasta para o Blender."
    ),
    "settings.code-copied": "Código copiado.",
    "channel.release": "Release",
    "channel.experimental": "Experimental",
    "info.find": (
        "O Creator Link só conversa com o Durty Cloth Tool neste computador. Nada vai para a internet além do seu "
        "login."
    ),
    "info.sign-in": (
        "O login mostra ao Durty Cloth Tool que este add-on pertence à sua conta. O add-on nunca vê a sua senha do "
        "Discord. O Durty Cloth Tool mostra este app em {apps}, onde você pode desconectá-lo."
    ),
    "info.map": (
        "Escolha qual mapa da roupa a imagem substitui na pré-visualização: Difusa (cor), Normal ou Especular. "
        "Imagens difusas são cor sRGB; defina os mapas normal e especular como Non-Color."
    ),
    "info.variation": (
        "Os mapas normal e especular pertencem ao modelo e são compartilhados por todas as variações, então só a "
        "Difusa (cor) pode virar uma nova variação."
    ),
    "info.live": (
        "O add-on lê a imagem ao fim de cada pincelada e envia o que mudou. Nada é salvo no seu projeto até você "
        "escolher Salvar na roupa ou Salvar como nova variação."
    ),
    "info.model": (
        "Enviar modelo exporta o Drawable Dictionary do Sollumz selecionado como CodeWalker XML (YDD) com as texturas "
        "e o mostra na roupa vinculada. Um modelo enviado pelo Durty Cloth Tool é importado, vinculado à roupa dele e "
        "enviado de novo após cada alteração. Nada é salvo até você escolher Salvar modelo na roupa."
    ),
    "info.open-map": (
        "Abre este mapa da roupa do seu projeto como imagem no Blender, vinculada à roupa, e inicia a pré-visualização "
        "ao vivo dela. O Durty Cloth Tool também pode enviar um mapa: {edit} no menu da roupa."
    ),
    "info.linked": (
        "Uma imagem aberta pelo Durty Cloth Tool lembra a roupa e o mapa dela, também no arquivo .blend salvo, para "
        "que a pré-visualização ao vivo sempre vá para essa roupa. Desvincule-a em Pré-visualização ao vivo para "
        "usá-la na roupa selecionada no Durty Cloth Tool."
    ),
    "info.checks": (
        "O Durty Cloth Tool verifica a imagem conforme o que o GTA V e a roupa precisam, como a sua Lista de erros. "
        "Corrija os erros antes de salvar; avisos e observações são conselhos."
    ),
    "info.privacy": (
        "Fica neste computador: suas imagens, modelos e os pixels da pré-visualização ao vivo. Eles vão só para o "
        "Durty Cloth Tool. Vai para o gta.clothing: o seu login (com o nome deste computador, a menos que você "
        "desligue isso), uma confirmação por conexão, a sua saída e as verificações de atualização do Blender."
    ),
    "op.connect": "Conectar",
    "op.connect.desc": "Conectar ao Durty Cloth Tool neste computador",
    "op.disconnect": "Desconectar",
    "op.disconnect.desc": "Desconectar do Durty Cloth Tool. Uma pré-visualização ao vivo em andamento para",
    "op.sign-in": "Entrar",
    "op.sign-in.desc": (
        "Entrar com a sua conta do gta.clothing (Discord). O Durty Cloth Tool pede que você aprove; se ele não estiver "
        "aberto, você recebe um código para o navegador"
    ),
    "op.sign-in-browser": "Entrar pelo navegador",
    "op.sign-in-browser.desc": (
        "Entrar com a sua conta do gta.clothing (Discord) na página do gta.clothing no navegador"
    ),
    "op.open-sign-in": "Abrir página de login",
    "op.open-sign-in.desc": "Abrir a página do gta.clothing que aprova este login",
    "op.copy-code": "Copiar código",
    "op.copy-code.desc": "Copiar o código de login para a área de transferência",
    "op.cancel-sign-in": "Cancelar",
    "op.cancel-sign-in.desc": "Parar de aguardar o login",
    "op.sign-out": "Sair",
    "op.sign-out.desc": "Sair do gta.clothing neste add-on e desconectar",
    "op.update-page": "Obter a atualização",
    "op.update-page.desc": "Abrir a página com as versões atuais do Durty Cloth Tool e dos plugins",
    "op.open-map": "Abrir mapa",
    "op.open-map.desc": (
        "Abrir este mapa da roupa do seu projeto como imagem vinculada à roupa e iniciar a pré-visualização ao vivo "
        "dela"
    ),
    "op.unlink": "Desvincular",
    "op.unlink.desc": (
        "Deixar de vincular esta imagem à roupa dela, para que ela siga a sua seleção no Durty Cloth Tool"
    ),
    "op.use-paint-image": "Usar imagem pintada",
    "op.use-paint-image.desc": "Usar a imagem em que você está pintando, ou a do Image Editor",
    "op.live-start": "Iniciar pré-visualização ao vivo",
    "op.live-start.desc": (
        "Mostrar esta imagem na roupa vinculada e atualizá-la após cada pincelada. Nada é salvo até você salvar"
    ),
    "op.live-stop": "Parar pré-visualização ao vivo",
    "op.live-stop.desc": (
        "Parar de enviar a imagem. As alterações ficam no ped até você ou o Durty Cloth Tool descartá-las"
    ),
    "op.live-pause": "Pausar",
    "op.live-pause.desc": "Não enviar alterações por enquanto. O ped continua mostrando a última atualização",
    "op.live-resume": "Retomar",
    "op.live-resume.desc": "Enviar alterações de novo, começando por tudo o que mudou durante a pausa",
    "op.live-send": "Enviar agora",
    "op.live-send.desc": "Enviar a imagem de novo agora, para alterações feitas por scripts, bake ou recarga",
    "op.live-save": "Salvar na roupa",
    "op.live-save.desc": (
        "Substituir o mapa da roupa vinculada por esta imagem no seu projeto. Você pode desfazer no Histórico"
    ),
    "op.live-save-variation": "Salvar como nova variação",
    "op.live-save-variation.desc": (
        "Adicionar esta imagem à roupa vinculada como nova variação de textura (só Difusa (cor))"
    ),
    "op.live-discard": "Descartar alterações",
    "op.live-discard.desc": "Tirar as alterações do ped e parar. Seu projeto mantém a textura salva",
    "op.check-again": "Verificar de novo",
    "op.check-again.desc": "Pedir ao Durty Cloth Tool que verifique a imagem de novo",
    "op.model-push": "Enviar modelo",
    "op.model-push.desc": (
        "Exportar o Drawable Dictionary do Sollumz selecionado e mostrá-lo na roupa vinculada. Nada é salvo até você "
        "salvar"
    ),
    "op.model-save": "Salvar modelo na roupa",
    "op.model-save.desc": "Salvar o modelo enviado no seu projeto. O modelo anterior fica no Histórico da roupa",
    "op.model-discard": "Descartar",
    "op.model-discard.desc": "Tirar o modelo enviado do ped. Seu projeto mantém o modelo salvo",
    "op.diagnostics": "Copiar diagnóstico",
    "op.diagnostics.desc": "Copiar versões e códigos de status para o suporte (sem caminhos de arquivo e sem dados de login)",
    "op.help": "Ajuda",
    "op.help.desc": "Abrir a documentação do Durty Cloth Tool",
    "op.community": "Pleb Masters Community Discord",
    "op.community.desc": "Abrir o servidor Pleb Masters Community Discord, onde você pode pedir ajuda",
    "op.info": "Mais informações",
    "op.about": "Sobre",
    "op.about.desc": "A versão e a licença do add-on, e o que ele envia e para onde",
    "about.title": "Durty Cloth Tool Link {version} ({channel})",
    "op.join-discord": "Entrar no servidor do Discord",
    "op.join-discord.desc": "Abrir o convite para o servidor Pleb Masters Community Discord no navegador",
    "prop.image": "Imagem",
    "prop.image.desc": "A imagem mostrada na roupa vinculada",
    "prop.map": "Mapa",
    "prop.map.desc": "Qual mapa da roupa vinculada a imagem substitui na pré-visualização",
    "prop.auto-push": "Enviar automaticamente",
    "prop.auto-push.desc": "Enviar o modelo de novo pouco depois de você parar de editar (após o primeiro envio)",
    "prop.auto-connect": "Conectar automaticamente",
    "prop.auto-connect.desc": "Procurar o Durty Cloth Tool neste computador quando o Blender iniciar",
    "prop.device-name": "Mostrar o nome deste computador no login",
    "prop.device-name.desc": (
        "Enviar o nome deste computador com um login, para a página de aprovação do gta.clothing mostrar qual "
        "computador pede"
    ),
    "prop.delay": "Atraso do envio automático",
    "prop.delay.desc": (
        "Segundos que um modelo enviado precisa ficar sem alteração antes que Enviar automaticamente o envie de novo"
    ),
    "notice.signed-in": "Conectado como {name}.",
    "notice.signing-out": "Saindo…",
    "notice.signed-out": "Você saiu.",
    "notice.signed-out-local": (
        "Saída feita neste computador. Permita o acesso online nas preferências do Blender para encerrar também a "
        "sessão no gta.clothing."
    ),
    "notice.signed-out-unreached": (
        "Saída feita neste computador; não foi possível alcançar o gta.clothing. A sessão lá termina sozinha, ou "
        "encerre na página da sua conta."
    ),
    "notice.browser-opens": "O seu navegador abre a página de login em instantes.",
    "notice.no-sign-in": "Nenhum login está aguardando.",
    "notice.not-gta-clothing": "O link de login não é um link do gta.clothing.",
    "notice.unexpected": "O add-on teve um problema inesperado: {detail}",
    "notice.secrets-unreadable": "Não foi possível ler o login salvo ({detail}). Entre de novo.",
    "notice.secret-store": "Não foi possível ler ou gravar o login protegido. Entre de novo.",
    "notice.file-error": "Não foi possível ler ou gravar um arquivo: {detail}",
    "notice.not-ready": "O add-on não está pronto.",
    "notice.connect-first": "Conecte ao Durty Cloth Tool primeiro.",
    "notice.select-cloth": "Selecione uma roupa no Durty Cloth Tool primeiro.",
    "notice.start-live-first": "Inicie a pré-visualização ao vivo primeiro.",
    "notice.wait-saving": "Aguarde o salvamento terminar.",
    "notice.diffuse-only": "Só a Difusa (cor) pode virar uma nova variação.",
    "notice.pushing": "Um envio está em andamento.",
    "notice.online-off": "O acesso online do Blender está desligado.",
    "error.generic": "Algo deu errado.",
    "error.generic-code": "Algo deu errado ({code}).",
    "error.malformed-message": (
        "O Durty Cloth Tool e este add-on não se entenderam. Atualize os dois e tente de novo."
    ),
    "error.invalid-message": (
        "O Durty Cloth Tool e este add-on não se entenderam. Atualize os dois e tente de novo."
    ),
    "error.unknown-message-type": "O Durty Cloth Tool não conhece este pedido. Atualize o Durty Cloth Tool.",
    "error.unexpected-message": "O Durty Cloth Tool não esperava este pedido agora. Tente de novo.",
    "error.message-too-large": "A imagem ou o modelo era grande demais para enviar.",
    "error.unsupported-protocol": "Este add-on e o Durty Cloth Tool usam versões de link diferentes. Atualize os dois.",
    "error.plugin-too-old": "Este add-on é antigo demais para o seu Durty Cloth Tool. Atualize o add-on.",
    "error.dct-too-old": (
        "Este Durty Cloth Tool é mais antigo que este add-on. Atualize o Durty Cloth Tool e depois escolha Conectar."
    ),
    "error.not-authenticated": "Entre primeiro.",
    "error.authentication-failed": "O Durty Cloth Tool não aceitou o login. Tentando de novo…",
    "error.untrusted-endpoint": (
        "Um programa que não é o seu Durty Cloth Tool respondeu, então nada foi enviado. O add-on continua procurando "
        "o Durty Cloth Tool."
    ),
    "error.account-mismatch": (
        "O Durty Cloth Tool está conectado com outra conta. Saia aqui e entre com a conta que o Durty Cloth Tool usa."
    ),
    "error.dct-signed-out": "O Durty Cloth Tool está sem login. Entre no Durty Cloth Tool; o add-on se conecta sozinho.",
    "error.token-invalid": "O login expirou. Entrando de novo…",
    "error.needs-license": "Isto precisa de uma licença do Durty Cloth Tool.",
    "error.needs-ultimate": "Isto está incluído no Durty Cloth Tool Ultimate.",
    "error.no-project": "Abra um projeto no Durty Cloth Tool primeiro.",
    "error.no-focused-item": "Selecione uma roupa no Durty Cloth Tool primeiro.",
    "error.binding-in-use": "Outro app já está trabalhando nesta textura ou modelo.",
    "error.binding-not-found": "A roupa ou textura não existe mais no Durty Cloth Tool.",
    "error.lease-not-found": "O Durty Cloth Tool encerrou esta pré-visualização. Inicie de novo.",
    "error.lease-limit": "Há pré-visualizações ao vivo demais abertas. Pare uma primeiro.",
    "error.budget-exceeded": (
        "A memória de pré-visualizações ao vivo do Durty Cloth Tool está cheia. Pare outra pré-visualização ao vivo."
    ),
    "error.frame-out-of-bounds": "A atualização da imagem não coube na textura.",
    "error.frame-size-mismatch": "Não foi possível enviar a imagem.",
    "error.unsupported-format": "O Durty Cloth Tool não aceita este formato aqui. Envie modelos como YDD XML do Sollumz.",
    "error.stale-revision": "Pixels mais novos ainda estavam a caminho. Salve de novo.",
    "error.item-refused": "O Durty Cloth Tool não pode editar este item (dummy, bloqueado ou protegido).",
    "error.game-required": "O Durty Cloth Tool precisa da sua instalação do GTA V para isso. Configure no Durty Cloth Tool.",
    "error.save-failed": "O Durty Cloth Tool não conseguiu salvar. A barra de status dele tem os detalhes.",
    "error.busy": "O Durty Cloth Tool está ocupado. Tente de novo em instantes.",
    "error.rate-limited": "Pedidos demais. Aguarde um momento e tente de novo.",
    "error.connection-limit": "Há apps demais conectados ao Durty Cloth Tool.",
    "error.request-denied": "O Durty Cloth Tool recusou o pedido.",
    "error.model-rejected": "O Durty Cloth Tool não conseguiu usar este modelo. Confira no Sollumz e envie de novo.",
    "error.internal-error": (
        "Algo deu errado. Tente de novo e reinicie o Blender e o Durty Cloth Tool se continuar acontecendo."
    ),
    "error.disconnected": "A conexão com o Durty Cloth Tool foi perdida.",
    "error.timeout": "O Durty Cloth Tool não respondeu a tempo.",
    "error.superseded": "Um pedido mais novo substituiu este.",
    "error.cancelled": "Cancelado.",
    "error.closed": "A pré-visualização ao vivo está fechada.",
    "error.signed-out": "Você saiu. Entre para usar o Creator Link de novo.",
    "error.assertion-invalid": "Não foi possível confirmar o login. Tentando de novo…",
    "error.pixel-source-failed": "Não foi possível ler a imagem para a pré-visualização ao vivo. Tentando de novo…",
    "error.callback-failed": "Algo deu errado no add-on. Tente de novo.",
    "error.offline": (
        "O acesso online do Blender está desligado. Permita em Preferências > Sistema > Rede para entrar e conectar."
    ),
    "error.network": "Não foi possível alcançar o gta.clothing. Confira a conexão com a internet.",
    "error.invalid-response": "O gta.clothing enviou uma resposta inesperada. Tente de novo mais tarde.",
    "error.tls": (
        "A conexão segura com o gta.clothing falhou. Confira a sua rede, proxy ou as configurações do antivírus."
    ),
    "error.account_locked": "A sua conta do gta.clothing está bloqueada.",
    "error.discord_membership_required": (
        "O Creator Link precisa que a sua conta do Discord seja membro do servidor Pleb Masters Community Discord."
    ),
    "error.discord_unavailable": "O login pelo Discord está indisponível agora. Tente de novo mais tarde.",
    "error.plugin_update_required": "O gta.clothing precisa de uma versão mais nova deste add-on. Atualize-o.",
    "error.expired_token": "O código de login expirou. Entre de novo.",
    "error.access_denied": "O login foi negado.",
    "error.invalid_grant": "O login não foi aceito. Entre de novo.",
    "error.session_invalid": "O login não é mais válido. Entre de novo.",
    "error.session_expired": "O login expirou. Entre de novo.",
    "error.session_revoked": "O login foi encerrado no gta.clothing. Entre de novo.",
    "error.refresh_in_progress": "Outro programa está renovando o seu login. Tente de novo em instantes.",
    "close.closed": "Pré-visualização ao vivo parada.",
    "close.replaced": "Outro app assumiu esta textura.",
    "close.itemRemoved": "A roupa foi removida no Durty Cloth Tool.",
    "close.projectClosed": "O projeto foi fechado no Durty Cloth Tool.",
    "close.entitlementLost": "O seu plano não inclui mais este recurso.",
    "close.signedOut": "O Durty Cloth Tool saiu da conta, então a pré-visualização terminou.",
    "close.disconnected": "A conexão com o Durty Cloth Tool foi perdida.",
    "feature.needsLicense": "Isto precisa de uma licença do Durty Cloth Tool.",
    "feature.needsUltimate": "Isto está incluído no Durty Cloth Tool Ultimate.",
    "feature.unavailable": "Isto não está incluído no seu plano do Durty Cloth Tool.",
}
