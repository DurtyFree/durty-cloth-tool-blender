# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2026 Schmid Software Solutions (https://schmid-software.de)
"""Russian (Русский). Neutral wording with polite imperatives, as Durty Cloth Tool uses them."""

TEXT = {
    "path.connected-apps": "Параметры > Подключённые приложения",
    "path.edit-in-app": "Редактировать в подключённом приложении",
    "panel.main": "Durty Cloth Tool",
    "panel.details": "Подключение",
    "panel.setup": "Настройка подключения",
    "panel.linked": "Связанная одежда",
    "panel.live": "Живой предпросмотр",
    "panel.checks": "Проверка текстуры",
    "panel.model": "Модель",
    "panel.settings": "Настройки",
    "chip.connected": "Подключено",
    "chip.live": "Live",
    "chip.connecting": "Подключение",
    "chip.action": "Нужно действие",
    "chip.offline": "Не в сети",
    "chip.problem": "Проблема",
    "state.idle": "Не подключено",
    "state.connecting": "Поиск Durty Cloth Tool",
    "state.waiting": "Durty Cloth Tool не найден. Скоро новая попытка",
    "state.reconnecting": "Повторное подключение к Durty Cloth Tool",
    "state.hello": "Подключение",
    "state.signing-in": "Ожидание входа",
    "state.authenticating": "Вход",
    "state.ready": "Вход выполнен: {name}",
    "state.signed-out": "Выход выполнен",
    "state.dct-signed-out": "Durty Cloth Tool не в аккаунте",
    "state.dct-disconnected": "Отключено в Durty Cloth Tool",
    "details.status": "Состояние: {state}",
    "details.account": "Вход выполнен: {name}",
    "details.not-signed-in": "Вход не выполнен",
    "details.project": "Проект: {name}",
    "details.addon": "Дополнение {version} ({channel})",
    "online.off": (
        "Доступ Blender в интернет выключен, поэтому Durty Cloth Tool нельзя подключить: каждое подключение "
        "подтверждается вашим входом в gta.clothing. Разрешите его в Настройки > Система > Сеть."
    ),
    "dct-signed-out": (
        "В Durty Cloth Tool не выполнен вход. Войдите в Durty Cloth Tool, затем выберите Подключить. Дополнение также "
        "время от времени пытается само."
    ),
    "dct-disconnected": "Это приложение отключено в Durty Cloth Tool. Выберите Подключить, чтобы подключить его снова.",
    "setup.find.title": "Найти Durty Cloth Tool",
    "setup.find.done": "Durty Cloth Tool найден",
    "setup.find.subtext": "Запустите Durty Cloth Tool на этом компьютере. Дополнение найдёт его автоматически.",
    "setup.find.searching": "Поиск Durty Cloth Tool…",
    "setup.find.waiting": "Durty Cloth Tool ещё не запущен. Дополнение продолжает поиск…",
    "setup.sign-in.title": "Войти через gta.clothing",
    "setup.sign-in.done": "Вход выполнен",
    "setup.sign-in.subtext": (
        "Creator Link использует ваш аккаунт gta.clothing (Discord). Вход нужен один раз на этом компьютере."
    ),
    "setup.sign-in.starting": "Начинается вход…",
    "setup.sign-in.finding": "Поиск Durty Cloth Tool для подтверждения входа…",
    "setup.sign-in.how": (
        "Durty Cloth Tool попросит вас подтвердить вход. Если он не запущен, вы получите код для браузера."
    ),
    "setup.sign-in.waiting": "Ожидание подтверждения…",
    "setup.sign-in.asked": "Durty Cloth Tool показывает запрос на вход. Подтвердите его там.",
    "setup.sign-in.approved": "Durty Cloth Tool подтвердил вход. Завершение…",
    "setup.sign-in.declined": "Durty Cloth Tool не подтвердил вход. Войдите в браузере.",
    "setup.sign-in.browser-subtext": "Откройте страницу входа и проверьте, что на ней этот код:",
    "setup.sign-in.signed-out": "Вы вышли. Войдите снова, чтобы пользоваться Creator Link.",
    "linked.project": "Проект: {name}",
    "linked.no-project": "Откройте проект в Durty Cloth Tool.",
    "linked.no-cloth": "Выберите одежду в Durty Cloth Tool, чтобы работать с ней здесь.",
    "linked.variation": "Вариация {letter}",
    "linked.number": "№ {number}",
    "linked.unknown": "Связанная одежда",
    "linked.unknown-subtext": "Выберите её один раз в Durty Cloth Tool, чтобы увидеть здесь её название.",
    "linked.map": "Карта",
    "linked.follows": "Следует за вашим выбором в Durty Cloth Tool",
    "linked.image": "Связано с изображением ниже",
    "linked.open-map": "Открыть карту в Blender",
    "linked.map-missing.diffuse": "У этой одежды нет диффузной карты.",
    "linked.map-missing.normal": "У этой одежды нет карты нормалей.",
    "linked.map-missing.specular": "У этой одежды нет карты бликов.",
    "map.diffuse": "Диффузная (цвет)",
    "map.diffuse-short": "Диффузная",
    "map.diffuse.desc": "Цветовая текстура одежды",
    "map.normal": "Нормали",
    "map.normal.desc": "Карта нормалей одежды",
    "map.specular": "Блики",
    "map.specular.desc": "Карта бликов одежды",
    "gender.male": "Мужской",
    "gender.female": "Женский",
    "open.opened": "Открыто из Durty Cloth Tool: {name}",
    "open.texture-busy": (
        "Durty Cloth Tool отправил {name}, но живой предпросмотр запущен или сохраняется. Остановите его и отправьте "
        "карту снова."
    ),
    "open.texture-failed": "Не удалось открыть {name}: {detail}",
    "open.stop-live-first": "Сначала остановите живой предпросмотр.",
    "open.reading": "Чтение карты из Durty Cloth Tool…",
    "open.map-upsell": "Открытие карт одежды здесь входит в Durty Cloth Tool Ultimate.",
    "open.model-importing": "Импорт {name} с помощью Sollumz…",
    "open.model-needs-sollumz": "Durty Cloth Tool отправил модель {name}. {problem}",
    "open.model-busy": (
        "Durty Cloth Tool отправил модель {name}, но другая модель ещё отправляется или сохраняется. Отправьте её "
        "снова через минуту."
    ),
    "open.model-failed": "Не удалось открыть модель {name}: {detail}",
    "open.import-failed": "Sollumz не смог импортировать модель ({detail}). Подробности в его журнале Info.",
    "open.no-dictionary": "Sollumz не импортировал Drawable Dictionary. Подробности в его журнале Info.",
    "open.import-errors": (
        "Sollumz сообщил об ошибках при импорте, поэтому модель не связана с одеждой. Подробности в его журнале Info."
    ),
    "open.model-warnings": (
        "Открыто из Durty Cloth Tool: {name}. Sollumz сообщил о предупреждениях; подробности в его журнале Info."
    ),
    "live.off": "Запустите живой предпросмотр, чтобы увидеть рисунок на ped.",
    "live.reading": "Чтение изображения…",
    "live.starting": "Запуск живого предпросмотра…",
    "live.on": "Вживую на ped",
    "live.sending": "Отправка изображения…",
    "live.not-worn": "Наденьте эту одежду на ped в Durty Cloth Tool, чтобы её увидеть.",
    "live.paused-dct": "3D-предпросмотр в Durty Cloth Tool приостановлен.",
    "live.paused": "Пауза. Изменения отправятся, когда вы продолжите.",
    "live.saving": "Сохранение…",
    "live.unsaved": "Ещё не сохранено в проекте",
    "live.linked": "Связано с {name} · {map}",
    "live.map": "Карта: {map}",
    "live.save-subtext": (
        "Сохранение записывает эту карту в проект. Его можно отменить в Истории одежды в Durty Cloth Tool."
    ),
    "live.saved": "Сохранено в {name}. Можно отменить в Истории.",
    "live.saved-unnamed": "Сохранено в одежду. Можно отменить в Истории.",
    "live.saved-variation": "Сохранено как новая вариация {name}.",
    "live.saved-variation-unnamed": "Сохранено как новая вариация.",
    "live.discarded": "Изменения в Durty Cloth Tool отброшены.",
    "live.stopped": "Живой предпросмотр остановлен.",
    "live.stopped-unsaved": (
        "Живой предпросмотр остановлен. Изменения не сохранены в проекте; изображение в Blender их сохраняет."
    ),
    "live.failed": "Живой предпросмотр остановлен из-за непредвиденной проблемы: {detail}",
    "live.upsell": "Живой предпросмотр входит в Durty Cloth Tool Ultimate.",
    "live.save-upsell": "Сохранение в одежду входит в Durty Cloth Tool Ultimate.",
    "live.image-changed": "Размер изображения изменился. Запустите живой предпросмотр снова.",
    "live.image-removed": "Изображение удалено.",
    "live.no-memory": "Недостаточно памяти для такого большого изображения.",
    "colour.non-color-diffuse": "Изображение установлено как Non-Color; его значения отправляются как цвет без изменений.",
    "colour.unknown-diffuse": (
        "Цветовое пространство {space} изображения отправляется без преобразования; для точных цветов используйте "
        "sRGB."
    ),
    "colour.unknown-data": (
        "Установите для карты цветовое пространство Non-Color; значения {space} отправляются так, как они есть в "
        "Blender."
    ),
    "image.none": "Сначала выберите изображение.",
    "image.tiled": "Изображения UDIM (тайлы) не поддерживаются. Используйте одно изображение.",
    "image.source": "Можно использовать только файлы изображений и сгенерированные изображения.",
    "image.unreadable": "Не удалось прочитать изображение.",
    "image.not-loaded": "Не удалось загрузить изображение. Проверьте, что его файл существует.",
    "image.channels": "Можно использовать только изображения в оттенках серого, RGB и RGBA.",
    "image.empty": "В изображении нет пикселей. Сначала откройте или создайте его.",
    "image.too-large": "Изображения больше {size} пикселей по стороне использовать нельзя.",
    "image.no-painted": "Раскрашиваемое изображение не найдено. Выберите изображение в списке.",
    "checks.errors": "Ошибки: {count}",
    "checks.warnings": "Предупреждения: {count}",
    "checks.notes": "Примечания: {count}",
    "checks.clean": "Проблем не найдено.",
    "checks.not-checked": "Durty Cloth Tool проверяет текстуру при запуске живого предпросмотра.",
    "checks.checking": "Проверка текстуры…",
    "checks.unavailable": "Проверка текстуры входит в Durty Cloth Tool Ultimate.",
    "severity.error": "Ошибка",
    "severity.warning": "Предупреждение",
    "severity.info": "Примечание",
    "finding.unknown": "Durty Cloth Tool сообщил: {code}.",
    "finding.non-power-of-two": "Размер не является степенью двойки (например, 1024 или 2048).",
    "finding.not-multiple-of-four": "Размер не кратен четырём, а это нужно сжатым текстурам.",
    "finding.too-large": "Текстура больше 2048 пикселей по стороне и занимает много игровой памяти.",
    "finding.too-small": "Текстура меньше 16 пикселей по стороне.",
    "finding.size-changed": "Размер отличается от текстуры, сохранённой в проекте.",
    "finding.palette-alpha": (
        "Эта одежда использует палитру: альфа-канал выбирает цвета палитры, поэтому рисуйте альфу осторожно."
    ),
    "finding.cutout-alpha": "Эта одежда использует альфу как вырез: прозрачные пиксели скрыты на ped.",
    "finding.hair-ramp": "Это волосы: игра окрашивает их в цвет волос, выбранный игроком.",
    "finding.bc1-alpha": "Сохранённая текстура сохраняет только полностью прозрачную или полностью непрозрачную альфу.",
    "finding-fix.non-power-of-two": "Перед сохранением измените размер до степени двойки, например 1024 x 1024.",
    "finding-fix.not-multiple-of-four": "Измените размер так, чтобы обе стороны делились на четыре, например 1024 x 512.",
    "finding-fix.too-large": "Используйте не больше 2048 пикселей по стороне, если одежде не нужна такая детализация.",
    "finding-fix.too-small": "Используйте не меньше 16 пикселей по стороне.",
    "finding-fix.size-changed": (
        "Сохранение заменит текстуру с этим размером. Верните сохранённый размер, если не хотели его менять."
    ),
    "finding-fix.palette-alpha": "Не меняйте значения альфы, если не хотите изменить цвета палитры.",
    "finding-fix.cutout-alpha": "Рисуйте прозрачность только там, где одежда должна быть скрыта.",
    "finding-fix.hair-ramp": "Рисуйте затенение в зелёном канале и пряди в красном канале, а не итоговый цвет.",
    "finding-fix.bc1-alpha": (
        "Используйте полностью прозрачную или полностью непрозрачную альфу; мягкие края при сохранении теряются."
    ),
    "model.subtext": "Отправляет модель снова вскоре после того, как вы перестаёте её редактировать.",
    "model.name": "Модель: {name}",
    "model.sending": "Отправка {name} (текстур: {count})",
    "model.previewing": "Показывается на ped в Durty Cloth Tool. Сохраните или отбросьте её там или здесь.",
    "model.findings": "Durty Cloth Tool сообщил о замечаниях: {count}.",
    "model.warnings-paused": (
        "Sollumz сообщил предупреждения, поэтому автоматическая отправка приостановлена. Посмотрите журнал Info в "
        "Sollumz, затем отправьте снова, чтобы продолжить."
    ),
    "model.warnings": "Sollumz сообщил предупреждения; подробности в его журнале Info.",
    "model.saving": "Сохранение модели в Durty Cloth Tool…",
    "model.saved": "Модель сохранена в одежду. Можно отменить в Истории.",
    "model.discarded": "Модель в Durty Cloth Tool отброшена.",
    "model.save-retry": "Durty Cloth Tool ещё загружает модель. Сохранение через мгновение…",
    "model.save-busy": "Durty Cloth Tool ещё занят моделью. Сохраните снова чуть позже.",
    "model.block.no-model": "Сначала отправьте модель.",
    "model.block.saving": "Уже сохраняется.",
    "model.block.waiting": "Дождитесь ответа Durty Cloth Tool.",
    "model.block.pushing": "Дождитесь, пока последняя отправка появится в Durty Cloth Tool, затем сохраните.",
    "model.block.due": (
        "Ваши последние изменения сейчас будут отправлены. Сохраните, когда они появятся в Durty Cloth Tool."
    ),
    "model.wait.tool": "Автоматическая отправка ждёт, пока работающий инструмент завершится.",
    "model.wait.mode": "Автоматическая отправка ждёт, пока вы выйдете из режима {mode}.",
    "model.gone": "Отправленной модели больше нет в этом файле. Отправьте её снова.",
    "model.linked": "Связано с {name}",
    "model.linked-twice": "{name} связан с той же одеждой. Отвяжите один из них: каждая одежда принимает одну модель.",
    "model.not-linked": "Этот Drawable Dictionary не связан с одеждой.",
    "model.failed": "Автоматическая отправка не удалась: {detail}",
    "model.select": "Выберите модель для отправки: Drawable Dictionary Sollumz или объект внутри него.",
    "model.one-root": "Выберите объекты только одного Drawable Dictionary.",
    "model.needs-dictionary": (
        "Durty Cloth Tool нужен Drawable Dictionary. Сделайте Drawable дочерним для Drawable Dictionary (Sollumz: "
        "Create Drawable Dictionary) и отправьте снова."
    ),
    "model.not-sollumz": "Выберите Drawable Dictionary Sollumz или объект внутри него.",
    "model.unhide": (
        "Покажите Drawable Dictionary (или объект внутри него), сделайте его выбираемым и отправьте снова."
    ),
    "model.not-shown": (
        "Модели нет ни в одной сцене, показанной в окне Blender. Покажите её сцену и отправьте снова."
    ),
    "model.not-in-layer": "Модели нет в текущем view layer. Покажите её и отправьте снова.",
    "model.export-failed": "Sollumz не смог экспортировать модель: {detail}",
    "model.not-exported": "Sollumz не экспортировал модель. Подробности в его журнале Info.",
    "sollumz.ready": "Sollumz {version}",
    "sollumz.ready-unknown": "Sollumz",
    "sollumz.missing": "Установите и включите Sollumz {version} или новее, чтобы открывать и отправлять модели.",
    "sollumz.too-old": (
        "Этот Sollumz слишком старый для экспорта в Durty Cloth Tool. Обновите до Sollumz {version} или новее."
    ),
    "sollumz.tested": "Проверено с Sollumz {version}.",
    "bundle.unreadable": "Не удалось прочитать папку экспорта ({detail}).",
    "bundle.not-dictionary": (
        "Sollumz экспортировал drawable или fragment, а не drawable dictionary. Durty Cloth Tool нужен Drawable "
        "Dictionary: сделайте ваш Drawable дочерним для него (Sollumz: Create Drawable Dictionary) и отправьте снова."
    ),
    "bundle.no-model": "Sollumz не экспортировал модель. Причина в журнале Info Sollumz.",
    "bundle.several": "Sollumz экспортировал несколько drawable dictionary ({count}). Выберите объекты только одного.",
    "bundle.bad-name": (
        "'{name}' нельзя отправить: в именах файлов допустимы только буквы, цифры, '_', '-' и '.', имя не должно "
        "начинаться с '.' или содержать '..' и должно быть не длиннее 128 символов. Переименуйте текстуру или "
        "модель в Blender."
    ),
    "bundle.duplicate": "Две текстуры называются '{name}'. Дайте каждой текстуре своё имя.",
    "bundle.too-many": "Модель использует {count} текстур; отправить можно не больше {limit}.",
    "bundle.empty-file": "'{name}' пустой. Экспортируйте модель снова.",
    "bundle.too-large": "Модель и её текстуры вместе больше {size} MiB, их нельзя отправить.",
    "bundle.invalid": "Экспорт нельзя отправить: {detail}",
    "settings.connection": "Подключение",
    "settings.account": "Аккаунт",
    "settings.updates": "Обновления",
    "settings.privacy": "Конфиденциальность",
    "settings.models": "Модели",
    "settings.connect-subtext": (
        "Нужен Durty Cloth Tool на этом компьютере. Подключение остаётся на этом компьютере; gta.clothing "
        "подтверждает ваш вход для каждого подключения."
    ),
    "settings.signed-in-as": "Вход выполнен: {name}",
    "settings.not-signed-in": "Вход не выполнен",
    "settings.signed-out": "Выход выполнен",
    "settings.sign-out-subtext": "Выход завершает вход gta.clothing этого дополнения на этом компьютере.",
    "settings.device-name-subtext": (
        "Его показывает страница подтверждения gta.clothing, чтобы вы различали свои компьютеры."
    ),
    "settings.licence": "GPL-3.0-or-later, Schmid Software Solutions. Поддерживает DurtyFree (Pleb Masters).",
    "settings.this-version": "Эта версия: {version} ({channel})",
    "settings.diagnostics-copied": (
        "Диагностика скопирована. Вставьте её на сервере Pleb Masters Community Discord, когда просите помощи. В ней "
        "версии и коды состояния, без путей к файлам и без данных входа."
    ),
    "settings.disk-install": (
        "Эта копия установлена из файла, поэтому Blender не может её обновлять. Чтобы получать обновления, "
        "перетащите ссылку установки со страницы плагинов на gta.clothing в Blender."
    ),
    "settings.updates-on": "Blender обновляет это дополнение из репозитория расширений Durty Cloth Tool.",
    "op.plugins-page": "Получить ссылку установки",
    "op.plugins-page.desc": "Открыть страницу плагинов на gta.clothing, откуда ссылка установки перетаскивается в Blender",
    "info.channel": (
        "Experimental получает новые функции и исправления первым и меняется чаще. Release получает их после "
        "проверки. Канал выбирается ссылкой установки, которую вы перетаскиваете в Blender."
    ),
    "settings.code-copied": "Код скопирован.",
    "channel.release": "Release",
    "channel.experimental": "Experimental",
    "info.find": (
        "Creator Link общается только с Durty Cloth Tool на этом компьютере. В интернет не уходит ничего, кроме "
        "вашего входа."
    ),
    "info.sign-in": (
        "Вход показывает Durty Cloth Tool, что это дополнение принадлежит вашему аккаунту. Дополнение никогда не видит "
        "ваш пароль Discord. Durty Cloth Tool показывает это приложение в разделе {apps}, где его можно отключить."
    ),
    "info.map": (
        "Выберите, какую карту одежды изображение заменяет в предпросмотре: Диффузная (цвет), Нормали или Блики. "
        "Диффузные изображения в цвете sRGB; для карт нормалей и бликов установите Non-Color."
    ),
    "info.variation": (
        "Карты нормалей и бликов относятся к модели и общие для всех вариаций, поэтому новой вариацией может стать "
        "только Диффузная (цвет)."
    ),
    "info.live": (
        "Дополнение читает изображение в конце каждого мазка и отправляет то, что изменилось. В проекте ничего не "
        "сохраняется, пока вы не выберете Сохранить в одежду или Сохранить как новую вариацию."
    ),
    "info.model": (
        "Отправить модель экспортирует выбранный Drawable Dictionary Sollumz как CodeWalker XML (YDD) с текстурами и "
        "показывает его на связанной одежде. Модель, присланная из Durty Cloth Tool, импортируется, связывается со "
        "своей одеждой и отправляется снова после каждого изменения. Ничего не сохраняется, пока вы не выберете "
        "Сохранить модель в одежду."
    ),
    "info.open-map": (
        "Открывает эту карту одежды из вашего проекта как изображение в Blender, связанное с одеждой, и запускает её "
        "живой предпросмотр. Durty Cloth Tool тоже может отправить карту: {edit} в меню одежды."
    ),
    "info.model-linked": (
        "Модель, открытая из Durty Cloth Tool, помнит свою одежду, в том числе в сохранённом файле .blend, поэтому "
        "всегда отправляется на эту одежду. Копия, сделанная через Дублировать, тоже несёт связь: отвяжите ту, которая "
        "не должна быть связана."
    ),
    "info.linked": (
        "Изображение, открытое из Durty Cloth Tool, помнит свою одежду и карту, в том числе в сохранённом файле "
        ".blend, поэтому его живой предпросмотр всегда идёт на эту одежду. Отвяжите его в разделе Живой предпросмотр, "
        "чтобы использовать для одежды, выбранной в Durty Cloth Tool."
    ),
    "info.checks": (
        "Durty Cloth Tool проверяет изображение на то, что нужно GTA V и одежде, как его Список ошибок. "
        "Исправьте ошибки до сохранения; предупреждения и примечания это советы."
    ),
    "info.privacy": (
        "Остаётся на этом компьютере: ваши изображения, модели и пиксели живого предпросмотра. Они уходят только в "
        "Durty Cloth Tool. Уходит в gta.clothing: ваш вход (с именем этого компьютера, если вы это не отключили), "
        "подтверждение для каждого подключения, ваш выход, проверки обновлений Blender и, после вашего согласия, форма "
        "одежды, которую вы там подгоняете."
    ),
    "op.connect": "Подключить",
    "op.connect.desc": "Подключиться к Durty Cloth Tool на этом компьютере",
    "op.disconnect": "Отключить",
    "op.disconnect.desc": "Отключиться от Durty Cloth Tool. Запущенный живой предпросмотр остановится",
    "op.sign-in": "Войти",
    "op.sign-in.desc": (
        "Войти с вашим аккаунтом gta.clothing (Discord). Durty Cloth Tool попросит вас подтвердить вход; если он не "
        "запущен, вы получите код для браузера"
    ),
    "op.sign-in-browser": "Войти в браузере",
    "op.sign-in-browser.desc": "Войти с вашим аккаунтом gta.clothing (Discord) на странице gta.clothing в браузере",
    "op.open-sign-in": "Открыть страницу входа",
    "op.open-sign-in.desc": "Открыть страницу gta.clothing, которая подтверждает этот вход",
    "op.copy-code": "Копировать код",
    "op.copy-code.desc": "Скопировать код входа в буфер обмена",
    "op.cancel-sign-in": "Отмена",
    "op.cancel-sign-in.desc": "Больше не ждать входа",
    "op.sign-out": "Выйти",
    "op.sign-out.desc": "Выйти из gta.clothing в этом дополнении и отключиться",
    "op.update-page": "Получить обновление",
    "op.update-page.desc": "Открыть страницу с текущими версиями Durty Cloth Tool и его плагинов",
    "op.open-map": "Открыть карту",
    "op.open-map.desc": (
        "Открыть эту карту одежды из вашего проекта как изображение, связанное с одеждой, и запустить её живой "
        "предпросмотр"
    ),
    "op.unlink": "Отвязать",
    "op.unlink.desc": (
        "Больше не связывать это изображение с его одеждой, чтобы оно следовало за вашим выбором в Durty Cloth Tool"
    ),
    "op.unlink-model.desc": (
        "Больше не связывать этот Drawable Dictionary с его одеждой. Его следующая первая отправка пойдёт на одежду, "
        "выбранную в Durty Cloth Tool"
    ),
    "op.use-paint-image": "Взять раскрашиваемое изображение",
    "op.use-paint-image.desc": "Использовать изображение, на котором вы рисуете, или открытое в Image Editor",
    "op.live-start": "Запустить живой предпросмотр",
    "op.live-start.desc": (
        "Показать это изображение на связанной одежде и обновлять его после каждого мазка. Ничего не сохраняется, "
        "пока вы не сохраните"
    ),
    "op.live-stop": "Остановить живой предпросмотр",
    "op.live-stop.desc": (
        "Перестать отправлять изображение. Изменения остаются на ped, пока вы или Durty Cloth Tool их не отбросите"
    ),
    "op.live-pause": "Пауза",
    "op.live-pause.desc": "Пока не отправлять изменения. Ped продолжает показывать последнее обновление",
    "op.live-resume": "Продолжить",
    "op.live-resume.desc": "Снова отправлять изменения, начиная со всего, что изменилось во время паузы",
    "op.live-send": "Отправить сейчас",
    "op.live-send.desc": "Отправить изображение снова сейчас, для изменений от скриптов, запекания или перезагрузки",
    "op.live-save": "Сохранить в одежду",
    "op.live-save.desc": (
        "Заменить карту связанной одежды этим изображением в проекте. Можно отменить в Истории"
    ),
    "op.live-save-variation": "Сохранить как новую вариацию",
    "op.live-save-variation.desc": (
        "Добавить это изображение к связанной одежде как новую вариацию текстуры (только Диффузная (цвет))"
    ),
    "op.live-discard": "Отбросить изменения",
    "op.live-discard.desc": "Убрать изменения с ped и остановить. Проект сохраняет свою сохранённую текстуру",
    "op.check-again": "Проверить снова",
    "op.check-again.desc": "Попросить Durty Cloth Tool проверить изображение снова",
    "op.model-push": "Отправить модель",
    "op.model-push.desc": (
        "Экспортировать выбранный Drawable Dictionary Sollumz и показать его на связанной одежде. Ничего не "
        "сохраняется, пока вы не сохраните"
    ),
    "op.model-save": "Сохранить модель в одежду",
    "op.model-save.desc": "Сохранить отправленную модель в проекте. Предыдущая модель остаётся в Истории одежды",
    "op.model-discard": "Отбросить",
    "op.model-discard.desc": "Убрать отправленную модель с ped. Проект сохраняет свою сохранённую модель",
    "op.diagnostics": "Копировать диагностику",
    "op.diagnostics.desc": "Скопировать версии и коды состояния для поддержки (без путей к файлам и данных входа)",
    "op.help": "Справка",
    "op.help.desc": "Открыть документацию Durty Cloth Tool",
    "op.community": "Pleb Masters Community Discord",
    "op.community.desc": "Открыть сервер Pleb Masters Community Discord, где можно попросить помощи",
    "op.info": "Подробнее",
    "op.about": "О дополнении",
    "op.about.desc": "Версия и лицензия дополнения, а также что и куда оно отправляет",
    "about.title": "Durty Cloth Tool Link {version} ({channel})",
    "op.join-discord": "Вступить на сервер Discord",
    "op.join-discord.desc": "Открыть приглашение на сервер Pleb Masters Community Discord в браузере",
    "prop.image": "Изображение",
    "prop.image.desc": "Изображение, которое показывается на связанной одежде",
    "prop.map": "Карта",
    "prop.map.desc": "Какую карту связанной одежды изображение заменяет в предпросмотре",
    "prop.auto-push": "Отправлять автоматически",
    "prop.auto-push.desc": "Снова отправлять модель вскоре после окончания правки (после первой отправки)",
    "prop.auto-connect": "Подключаться автоматически",
    "prop.auto-connect.desc": "Искать Durty Cloth Tool на этом компьютере при запуске Blender",
    "prop.device-name": "Показывать имя компьютера при входе",
    "prop.device-name.desc": (
        "Отправлять имя этого компьютера при входе, чтобы страница подтверждения gta.clothing показывала, какой "
        "компьютер спрашивает"
    ),
    "prop.delay": "Задержка автоотправки",
    "prop.delay.desc": (
        "Сколько секунд отправленная модель должна оставаться без изменений, прежде чем Отправлять автоматически "
        "отправит её снова"
    ),
    "notice.signed-in": "Вход выполнен: {name}.",
    "notice.signing-out": "Выход…",
    "notice.signed-out": "Выход выполнен.",
    "notice.signed-out-local": (
        "Выход выполнен на этом компьютере. Разрешите доступ в интернет в настройках Blender, чтобы завершить и "
        "сеанс на gta.clothing."
    ),
    "notice.signed-out-unreached": (
        "Выход выполнен на этом компьютере; gta.clothing недоступен. Сеанс там завершится сам, или завершите его на "
        "странице аккаунта."
    ),
    "notice.browser-opens": "Браузер сейчас откроет страницу входа.",
    "notice.no-sign-in": "Нет ожидающего входа.",
    "notice.not-gta-clothing": "Ссылка для входа не ведёт на gta.clothing.",
    "notice.unexpected": "В дополнении возникла непредвиденная проблема: {detail}",
    "notice.secrets-unreadable": "Не удалось прочитать сохранённый вход ({detail}). Войдите снова.",
    "notice.secret-store": "Не удалось прочитать или записать защищённый вход. Войдите снова.",
    "notice.file-error": "Не удалось прочитать или записать файл: {detail}",
    "notice.not-ready": "Дополнение не готово.",
    "notice.connect-first": "Сначала подключитесь к Durty Cloth Tool.",
    "notice.select-cloth": "Сначала выберите одежду в Durty Cloth Tool.",
    "notice.start-live-first": "Сначала запустите живой предпросмотр.",
    "notice.wait-saving": "Дождитесь окончания сохранения.",
    "notice.diffuse-only": "Новой вариацией может стать только Диффузная (цвет).",
    "notice.pushing": "Отправка уже идёт.",
    "notice.online-off": "Доступ Blender в интернет выключен.",
    "error.generic": "Что-то пошло не так.",
    "error.generic-code": "Что-то пошло не так ({code}).",
    "error.malformed-message": "Durty Cloth Tool и это дополнение не поняли друг друга. Обновите оба и попробуйте снова.",
    "error.invalid-message": "Durty Cloth Tool и это дополнение не поняли друг друга. Обновите оба и попробуйте снова.",
    "error.unknown-message-type": "Durty Cloth Tool не знает этот запрос. Обновите Durty Cloth Tool.",
    "error.unexpected-message": "Durty Cloth Tool сейчас не ожидал этот запрос. Попробуйте снова.",
    "error.message-too-large": "Изображение или модель слишком велики для отправки.",
    "error.unsupported-protocol": "Это дополнение и Durty Cloth Tool используют разные версии связи. Обновите оба.",
    "error.plugin-too-old": "Это дополнение слишком старое для вашего Durty Cloth Tool. Обновите дополнение.",
    "error.dct-too-old": (
        "Этот Durty Cloth Tool старше этого дополнения. Обновите Durty Cloth Tool, затем выберите Подключить."
    ),
    "error.not-authenticated": "Сначала войдите.",
    "error.authentication-failed": "Durty Cloth Tool не принял вход. Новая попытка…",
    "error.untrusted-endpoint": (
        "Ответила программа, которая не является вашим Durty Cloth Tool, поэтому ничего не отправлено. Дополнение "
        "продолжает искать Durty Cloth Tool."
    ),
    "error.account-mismatch": (
        "В Durty Cloth Tool выполнен вход в другой аккаунт. Выйдите здесь и войдите с аккаунтом, который использует "
        "Durty Cloth Tool."
    ),
    "error.dct-signed-out": "В Durty Cloth Tool не выполнен вход. Войдите в Durty Cloth Tool; дополнение подключится само.",
    "error.token-invalid": "Срок входа истёк. Повторный вход…",
    "error.needs-license": "Для этого нужна лицензия Durty Cloth Tool.",
    "error.needs-ultimate": "Это входит в Durty Cloth Tool Ultimate.",
    "error.no-project": "Сначала откройте проект в Durty Cloth Tool.",
    "error.no-focused-item": "Сначала выберите одежду в Durty Cloth Tool.",
    "error.binding-in-use": "Другое приложение уже работает с этой текстурой или моделью.",
    "error.binding-not-found": "Этой одежды или текстуры больше нет в Durty Cloth Tool.",
    "error.lease-not-found": "Durty Cloth Tool завершил этот предпросмотр. Запустите его снова.",
    "error.lease-limit": "Открыто слишком много живых предпросмотров. Сначала остановите один.",
    "error.budget-exceeded": "Память живых предпросмотров в Durty Cloth Tool заполнена. Остановите другой предпросмотр.",
    "error.frame-out-of-bounds": "Обновление изображения не поместилось в текстуру.",
    "error.frame-size-mismatch": "Не удалось отправить изображение.",
    "error.unsupported-format": "Durty Cloth Tool здесь не принимает этот формат. Отправляйте модели как YDD XML Sollumz.",
    "error.stale-revision": "Более новые пиксели ещё были в пути. Сохраните снова.",
    "error.item-refused": "Durty Cloth Tool не может изменить этот элемент (dummy, заблокирован или защищён).",
    "error.game-required": "Для этого Durty Cloth Tool нужна ваша установка GTA V. Настройте её в Durty Cloth Tool.",
    "error.save-failed": "Durty Cloth Tool не смог сохранить. Подробности в его строке состояния.",
    "error.busy": "Durty Cloth Tool занят. Попробуйте снова чуть позже.",
    "error.rate-limited": "Слишком много запросов. Подождите немного и попробуйте снова.",
    "error.connection-limit": "К Durty Cloth Tool подключено слишком много приложений.",
    "error.request-denied": "Durty Cloth Tool отклонил запрос.",
    "error.model-rejected": "Durty Cloth Tool не смог использовать эту модель. Проверьте её в Sollumz и отправьте снова.",
    "error.internal-error": (
        "Что-то пошло не так. Попробуйте снова и перезапустите Blender и Durty Cloth Tool, если это повторится."
    ),
    "error.disconnected": "Связь с Durty Cloth Tool потеряна.",
    "error.timeout": "Durty Cloth Tool не ответил вовремя.",
    "error.superseded": "Этот запрос заменён более новым.",
    "error.cancelled": "Отменено.",
    "error.closed": "Живой предпросмотр закрыт.",
    "error.signed-out": "Вы вышли. Войдите, чтобы снова пользоваться Creator Link.",
    "error.assertion-invalid": "Не удалось подтвердить вход. Новая попытка…",
    "error.pixel-source-failed": "Не удалось прочитать изображение для живого предпросмотра. Новая попытка…",
    "error.callback-failed": "В дополнении что-то пошло не так. Попробуйте снова.",
    "error.offline": (
        "Доступ Blender в интернет выключен. Разрешите его в Настройки > Система > Сеть, чтобы входить и "
        "подключаться."
    ),
    "error.network": "gta.clothing недоступен. Проверьте подключение к интернету.",
    "error.invalid-response": "gta.clothing прислал неожиданный ответ. Попробуйте позже.",
    "error.tls": (
        "Не удалось установить защищённое соединение с gta.clothing. Проверьте сеть, прокси или настройки "
        "антивируса."
    ),
    "error.account_locked": "Ваш аккаунт gta.clothing заблокирован.",
    "error.discord_membership_required": (
        "Для Creator Link ваш аккаунт Discord должен состоять в сервере Pleb Masters Community Discord."
    ),
    "error.discord_unavailable": "Вход через Discord сейчас недоступен. Попробуйте позже.",
    "error.plugin_update_required": "gta.clothing требует более новую версию этого дополнения. Обновите его.",
    "error.expired_token": "Код входа истёк. Войдите снова.",
    "error.access_denied": "Вход отклонён.",
    "error.invalid_grant": "Вход не принят. Войдите снова.",
    "error.session_invalid": "Вход больше не действителен. Войдите снова.",
    "error.session_expired": "Срок входа истёк. Войдите снова.",
    "error.session_revoked": "Вход завершён на gta.clothing. Войдите снова.",
    "error.refresh_in_progress": "Другая программа обновляет ваш вход. Попробуйте снова чуть позже.",
    "close.closed": "Живой предпросмотр остановлен.",
    "close.replaced": "Другое приложение взяло эту текстуру.",
    "close.itemRemoved": "Одежда удалена в Durty Cloth Tool.",
    "close.projectClosed": "Проект закрыт в Durty Cloth Tool.",
    "close.entitlementLost": "Ваш план больше не включает эту функцию.",
    "close.signedOut": "Durty Cloth Tool вышел из аккаунта, поэтому предпросмотр завершён.",
    "close.disconnected": "Связь с Durty Cloth Tool потеряна.",
    "feature.needsLicense": "Для этого нужна лицензия Durty Cloth Tool.",
    "feature.needsUltimate": "Это входит в Durty Cloth Tool Ultimate.",
    "feature.unavailable": "Это не входит в ваш план Durty Cloth Tool.",
}
