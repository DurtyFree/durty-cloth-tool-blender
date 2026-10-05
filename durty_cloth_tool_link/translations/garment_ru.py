# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2026 Schmid Software Solutions (https://schmid-software.de)
"""Russian (Русский): the garment fitting texts."""

TEXT = {
    "garment.panel": "Подгонка одежды (экспериментально)",
    "garment.panel.setup": "Настройка",
    "garment.panel.fit": "Подгонка",
    "garment.panel.fix": "Исправление",
    "garment.panel.ready": "Готово к игре",
    "garment.next.import": "Импортируйте одежду или выделите свою и выберите Использовать выделенную одежду.",
    "garment.next.body": "Далее: добавьте тело freemode в разделе Настройка.",
    "garment.next.markers": (
        "Далее: расставьте маркеры кнопкой Автомаркеры в разделе Подгонка, затем проверьте, где они стоят."
    ),
    "garment.next.tpose": "Далее: переведите T-позу в A-позу в разделе Подгонка.",
    "garment.next.check": "Далее: запустите проверку посадки в разделе Исправление.",
    "garment.next.push": (
        "Далее: части одежды находятся внутри тела. Используйте Вытолкнуть из тела в разделе Исправление."
    ),
    "garment.next.prepare": "Далее: выберите Подготовить одежду в разделе Готово к игре.",
    "garment.next.combine": (
        "Далее: выберите Объединить материалы в разделе Готово к игре, чтобы у одежды была одна текстура."
    ),
    "garment.next.lods": "Далее: выберите Создать LOD в разделе Готово к игре.",
    "garment.next.validate": "Далее: выберите Проверить в разделе Готово к игре.",
    "garment.next.sculpting": (
        "Скульптинг: тяните кистью Grab, затем выберите Принять или Отмена в разделе Исправление."
    ),
    "garment.gender.male.desc": "Мужской ped freemode (mp_m_freemode_01)",
    "garment.gender.female.desc": "Женский ped freemode (mp_f_freemode_01)",
    "garment.slot.jbib": "Верх (jbib)",
    "garment.slot.jbib.desc": "Куртки, рубашки и кофты",
    "garment.slot.accs": "Нижняя рубашка (accs)",
    "garment.slot.accs.desc": "Нижние рубашки, которые носят под верхом",
    "garment.slot.lowr": "Ноги (lowr)",
    "garment.slot.lowr.desc": "Брюки, шорты и юбки",
    "garment.slot.feet": "Обувь (feet)",
    "garment.slot.feet.desc": "Туфли и ботинки",
    "garment.category.vest": "Майка",
    "garment.category.vest.desc": "Верх без рукавов",
    "garment.category.tshirt": "Футболка",
    "garment.category.tshirt.desc": "Верх с короткими рукавами",
    "garment.category.long_sleeve": "Длинный рукав",
    "garment.category.long_sleeve.desc": "Верх с рукавами до запястий",
    "garment.category.long_jacket": "Длинная куртка или туника",
    "garment.category.long_jacket.desc": "Верх с длинными рукавами, доходящий ниже бёдер",
    "garment.category.pants": "Брюки",
    "garment.category.pants.desc": "Брюки длиной до щиколоток",
    "garment.category.shorts": "Шорты",
    "garment.category.shorts.desc": "Штаны, которые заканчиваются на коленях или выше",
    "garment.category.shoes": "Обувь",
    "garment.category.shoes.desc": "Туфли, ботинки и сандалии",
    "garment.pose.a_pose": "A-поза",
    "garment.pose.a_pose.desc": "Руки опущены под углом, как стоит ped в игре",
    "garment.pose.t_pose": "T-поза",
    "garment.pose.t_pose.desc": "Руки вытянуты прямо в стороны",
    "garment.pose.custom": "Другая",
    "garment.pose.custom.desc": "Другая поза: проверьте маркеры и передвиньте их к суставам вручную",
    "garment.region.shoulders": "Плечи",
    "garment.region.upper_arms": "Верх рук",
    "garment.region.chest": "Грудь",
    "garment.region.back": "Спина",
    "garment.region.waist": "Талия",
    "garment.region.hips": "Бёдра",
    "garment.region.neck": "Шея",
    "garment.region.legs": "Ноги",
    "garment.region.desc": "Часть одежды, найденная по маркерам",
    "garment.level.high": "Высокий",
    "garment.level.medium": "Средний",
    "garment.level.low": "Низкий",
    "garment.prop.garment": "Одежда",
    "garment.prop.garment.desc": "Одежда, с которой работают инструменты. Меняется только этот объект",
    "garment.prop.body": "Тело",
    "garment.prop.body.desc": "Тело freemode, по которому измеряется одежда",
    "garment.prop.gender": "Пол",
    "garment.prop.gender.desc": "Для какого ped freemode эта одежда",
    "garment.prop.slot": "Слот",
    "garment.prop.slot.desc": "Слот одежды, в который она попадёт в Durty Cloth Tool",
    "garment.prop.category": "Категория",
    "garment.prop.category.desc": (
        "Вид одежды: от него зависит, куда ставятся маркеры и какие области предлагают инструменты"
    ),
    "garment.prop.pose": "Исходная поза",
    "garment.prop.pose.desc": "Поза аватара, на котором сделана одежда",
    "garment.prop.marker-size": "Размер маркеров",
    "garment.prop.marker-size.desc": "Насколько крупными рисуются сферы маркеров",
    "garment.prop.arm-angle": "Угол рук",
    "garment.prop.arm-angle.desc": "Насколько ниже горизонтали кнопка T-поза в A-позу опускает руки",
    "garment.prop.gap": "Зазор (мм)",
    "garment.prop.push-gap.desc": (
        "Как далеко за пределы тела кнопка Вытолкнуть из тела перемещает одежду, в миллиметрах"
    ),
    "garment.prop.snug-gap.desc": "На каком расстоянии от тела кнопка Прижать к телу оставляет область, в миллиметрах",
    "garment.prop.region": "Область",
    "garment.prop.region.desc": "Часть одежды, с которой работают Прижать к телу и Ослабить растяжение",
    "garment.prop.amount": "Степень",
    "garment.prop.amount.desc": "Какую часть пути проходит область: 1 перемещает её до конца",
    "garment.prop.radius": "Радиус (см)",
    "garment.prop.radius.desc": "Размер кисти Grab, в сантиметрах",
    "garment.prop.strength": "Сила",
    "garment.prop.strength.desc": "Насколько сильно кисть Grab двигает одежду",
    "garment.prop.mirror": "Зеркально по X",
    "garment.prop.mirror.desc": "Скульптить обе стороны одежды одновременно",
    "garment.prop.keep-out": "Держать вне тела",
    "garment.prop.keep-out.desc": (
        "Когда вы выбираете Принять, вернуть вдавленное в тело обратно наружу, на зазор кнопки Вытолкнуть из тела"
    ),
    "garment.prop.weld": "Расстояние сшивания (мм)",
    "garment.prop.weld.desc": "Края деталей кроя ближе этого расстояния, в миллиметрах, соединяются в один шов",
    "garment.prop.colour-1": "Color 1",
    "garment.prop.colour-1.desc": (
        "Первый цвет вершин шейдера ped (Color 1 в Sollumz): свет, который получает одежда. #FF8000 подходит "
        "большей части одежды; #FFBAFF заставляет светиться эмиссионные материалы"
    ),
    "garment.prop.colour-2": "Color 2",
    "garment.prop.colour-2.desc": (
        "Второй цвет вершин шейдера ped (Color 2 в Sollumz): ветер и пот. Чёрный без альфы отключает и то, и другое"
    ),
    "garment.prop.overwrite": "Заменять существующие цвета вершин",
    "garment.prop.overwrite.desc": "Заменять Color 1 и Color 2, даже если они уже есть у одежды",
    "garment.prop.size": "Размер текстуры",
    "garment.size.desc": (
        "Размер объединённой текстуры в пикселях. Проверка текстуры Durty Cloth Tool советует 2048 или меньше"
    ),
    "garment.prop.cut": "Разрезать длинные полосы",
    "garment.prop.cut.desc": (
        "Разрезать длинные тонкие UV-острова, например подолы и пояса, на куски, чтобы остальной одежде досталось "
        "больше текстуры"
    ),
    "garment.prop.lod-medium": "Треугольники (средний)",
    "garment.prop.lod-low": "Треугольники (низкий)",
    "garment.prop.lod.desc": "Наибольшее число треугольников, которое сохраняет этот уровень детализации",
    "garment.prop.ground": "Аватар стоял на земле",
    "garment.prop.ground.desc": (
        "Одежда сделана на аватаре, стоящем на высоте 0, как в Marvelous Designer: опустить её к ped, подошвы "
        "которого на 1 м ниже его начала координат"
    ),
    "garment.prop.preset-name": "Название",
    "garment.heading.markers": "Маркеры",
    "garment.heading.tpose": "Модель в T-позе",
    "garment.heading.backups": "Резервные копии",
    "garment.heading.push": "Отступ от тела",
    "garment.heading.regions": "Инструменты для областей",
    "garment.heading.problems": "Проблемы",
    "garment.heading.check": "Проверка посадки",
    "garment.heading.sculpt": "Ручная правка",
    "garment.heading.tears": "Разрывы",
    "garment.heading.prepare": "Подготовка",
    "garment.heading.combine": "Материалы",
    "garment.heading.lods": "Уровни детализации",
    "garment.heading.validate": "Проверки",
    "garment.op.use": "Использовать выделенную одежду",
    "garment.op.use.desc": "Работать с выделенным меш-объектом",
    "garment.op.import": "Импортировать одежду",
    "garment.op.import.desc": (
        "Импортировать одежду из файла FBX, OBJ или glTF (например, из Marvelous Designer) в метрах и одним "
        "объектом"
    ),
    "garment.op.add-body": "Добавить тело freemode",
    "garment.op.add-body.desc": (
        "Скачать тело freemode выбранного пола с gta.clothing для вашего аккаунта (один раз для каждой версии тела) "
        "и добавить его в сцену"
    ),
    "garment.op.cancel-body.desc": "Остановить скачивание тела",
    "garment.op.body-file": "Использовать файл тела",
    "garment.op.body-file.desc": "Вместо этого добавить тело из файла GLB, glTF, FBX или OBJ, в метрах и в позе игры",
    "garment.op.auto-markers": "Автомаркеры",
    "garment.op.auto-markers.desc": (
        "Расставить маркеры суставов (шея, грудь, таз, плечи, локти, запястья, бёдра) по форме одежды. Передвиньте "
        "маркеры, которые стоят не на месте"
    ),
    "garment.op.mirror": "Отразить слева направо",
    "garment.op.mirror.desc": "Скопировать маркеры левой стороны ped на его правую сторону",
    "garment.op.save-preset": "Сохранить пресет позы",
    "garment.op.save-preset.desc": "Сохранить маркеры как пресет в папке дополнения, для похожей одежды",
    "garment.op.load-preset": "Загрузить пресет позы",
    "garment.op.load-preset.desc": "Расставить маркеры из сохранённого пресета",
    "garment.op.tpose": "T-поза в A-позу",
    "garment.op.tpose.desc": "Опустить руки одежды, сделанной в T-позе, до угла рук с помощью маркеров",
    "garment.op.restore": "Вернуть до подгонки",
    "garment.op.restore.desc": "Вернуть форму одежды, какой она была до первого шага подгонки",
    "garment.op.push": "Вытолкнуть из тела",
    "garment.op.push.desc": (
        "Переместить наружу на зазор каждую часть одежды, которая находится внутри тела или ближе зазора"
    ),
    "garment.op.snug": "Прижать к телу",
    "garment.op.snug.desc": "Приблизить выбранную область к телу, вплоть до зазора",
    "garment.op.relax": "Ослабить растяжение",
    "garment.op.relax.desc": "Вернуть растянутые части выбранной области ближе к их исходному размеру",
    "garment.op.problems": "Показать проблемы",
    "garment.op.problems.desc": (
        "Раскрасить одежду: красным то, что внутри тела, жёлтым слишком близкое, фиолетовым растянутое, синим "
        "отстающее плечо. Выберите снова, чтобы скрыть цвета"
    ),
    "garment.op.refresh": "Обновить",
    "garment.op.refresh.desc": "Снова раскрасить проблемы после изменения",
    "garment.op.check": "Запустить проверку посадки",
    "garment.op.check.desc": "Измерить, насколько каждая область одежды отстоит от тела",
    "garment.op.sculpt": "Начать скульптинг",
    "garment.op.sculpt.desc": (
        "Исправить форму вручную кистью Grab. Принять сохраняет результат, Отмена возвращает прежнюю форму"
    ),
    "garment.op.accept": "Принять",
    "garment.op.accept.desc": "Оставить форму после скульптинга и завершить сеанс",
    "garment.op.cancel-sculpt.desc": "Вернуть форму, какой она была до сеанса, и завершить его",
    "garment.op.tears": "Проверить разрывы",
    "garment.op.tears.desc": "Провести арматуру одежды через несколько тестовых поз и показать, где расходятся швы",
    "garment.op.prepare": "Подготовить одежду",
    "garment.op.prepare.desc": (
        "Сшить швы между деталями кроя, удалить свободные части, триангулировать, включить гладкое затенение и "
        "добавить цвета вершин ped"
    ),
    "garment.op.combine": "Объединить материалы",
    "garment.op.combine.desc": (
        "Упаковать все UV-острова в одну раскладку и запечь цвет каждого материала в одну текстуру"
    ),
    "garment.op.lods": "Создать LOD",
    "garment.op.lods.desc": (
        "Создать средний и низкий уровни детализации в слотах LOD Sollumz с весами высокого уровня"
    ),
    "garment.op.validate": "Проверить",
    "garment.op.validate.desc": "Проверить одежду на проблемы, которые проявятся в игре",
    "garment.garment.facts": "Вершин: {count} · материалов: {materials}",
    "garment.body.hosted": "Тело freemode: {gender}, версия {version}",
    "garment.body.object": "Тело: {name}",
    "garment.body.downloading": "Скачивание тела freemode…",
    "garment.body.subtext": (
        "Тело скачивается с gta.clothing для аккаунта, в который выполнен вход, и хранится в папке дополнения, "
        "поэтому каждая версия скачивается один раз."
    ),
    "garment.body.cancelled": "Скачивание тела отменено.",
    "garment.body.offline": (
        "Доступ Blender в интернет выключен, а тело раньше не скачивалось. Разрешите доступ в интернет или "
        "используйте файл тела."
    ),
    "garment.body.network": "gta.clothing недоступен. Проверьте подключение к интернету или используйте файл тела.",
    "garment.body.no-body": "На gta.clothing пока нет тела freemode для этого канала. Пока используйте файл тела.",
    "garment.body.signed-out": "Вход больше не действителен. Войдите снова, затем добавьте тело.",
    "garment.body.not-entitled": "Ваш аккаунт не может скачать тело freemode.",
    "garment.body.refused": "gta.clothing отклонил скачивание.",
    "garment.body.update": "Для тела gta.clothing требует более новую версию этого дополнения. Обновите его.",
    "garment.body.busy": "Слишком много скачиваний одновременно. Подождите немного и попробуйте снова.",
    "garment.body.unavailable": "Тело freemode сейчас недоступно. Попробуйте позже.",
    "garment.body.invalid": "gta.clothing прислал не тело. Попробуйте позже.",
    "garment.body.disk": "Не удалось сохранить тело в папке дополнения.",
    "garment.markers.count": "Маркеров расставлено: {count} из {total}",
    "garment.presets.none": "Сохранённых пресетов пока нет",
    "garment.backups.count": "Резервных копий: {count} из {limit}",
    "garment.problem.inside": "Внутри тела",
    "garment.problem.close": "Слишком близко к телу",
    "garment.problem.stretched": "Растянуто",
    "garment.problem.floating": "Отстающее плечо",
    "garment.check.none": "Запустите проверку посадки, чтобы увидеть, насколько каждая область отстоит от тела.",
    "garment.check.measured": "Измерено (мм)",
    "garment.check.value": "{p50} (от {p10} до {p90})",
    "garment.check.inside": "Внутри тела: вершин {count} ({share} %)",
    "garment.advice.shoulders": "Плечи отстоят от тела. Выберите Прижать к телу с областью Плечи, чтобы опустить их.",
    "garment.sculpt.running": "Тяните кистью Grab, чтобы двигать одежду. Тело показано каркасом.",
    "garment.sculpt.subtext": "Принять сохраняет форму; Отмена возвращает форму, какой она была до сеанса.",
    "garment.pose.arms-up": "Руки вверх",
    "garment.pose.arms-forward": "Руки вперёд",
    "garment.pose.legs-forward": "Ноги вперёд",
    "garment.pose.twist": "Скручивание",
    "garment.tears.pose": "{pose}: точек шва расходится: {count}, до {gap} мм",
    "garment.tears.pose-clean": "{pose}: швы не расходятся",
    "garment.validate.clean": "CLEAN: исправлять нечего.",
    "garment.finding.non-finite": "Точек с испорченными координатами: {count}.",
    "garment.finding.no-uv": "У одежды нет UV-развёртки, поэтому на ней не может быть текстуры.",
    "garment.finding.uv-outside": "UV-точек вне квадрата от 0 до 1: {count}; там игра повторяет текстуру.",
    "garment.finding.uv-area": "UV-раскладка использует только {area} % текстуры.",
    "garment.finding.no-weights": "Риг ещё не сделан: назначьте одежде веса костей скелета freemode.",
    "garment.finding.unweighted": "Вершин без весов: {count}; когда ped двигается, игра оставляет их на месте.",
    "garment.finding.influences": (
        "Вершин, на которые влияет больше {limit} костей: {count}; игра использует только {limit}."
    ),
    "garment.finding.colour-missing": "Нет Color 1. Его добавляет кнопка Подготовить одежду.",
    "garment.finding.colour-format": (
        "Color 1 не байтовый цвет углов граней, как нужно Sollumz. Кнопка Подготовить одежду заменяет его."
    ),
    "garment.finding.vertices": "Уровень {level}: игровых вершин {count}, больше, чем советует дополнение ({budget}).",
    "garment.finding.inside": "Внутри тела: {share} % одежды.",
    "garment.finding.materials": (
        "У одежды материалов: {count}. Кнопка Объединить материалы делает из них одну текстуру."
    ),
    "garment.why.no-garment": "Сначала импортируйте одежду или выберите её в разделе Настройка.",
    "garment.why.not-shown": "Одежды нет в текущем view layer.",
    "garment.why.sculpting": "Сначала примите или отмените сеанс скульптинга.",
    "garment.why.object-mode": "Сначала перейдите в Объектный режим.",
    "garment.why.shape-keys": "У одежды есть ключи формы. Сначала примените или удалите их.",
    "garment.why.empty": "У одежды нет геометрии.",
    "garment.why.no-body": "Сначала добавьте тело freemode в разделе Настройка.",
    "garment.why.no-markers": "Обуви маркеры не нужны.",
    "garment.why.downloading": "Тело скачивается.",
    "garment.why.sign-in": "Сначала войдите через gta.clothing (Настройка подключения) или используйте файл тела.",
    "garment.why.select-mesh": "Сначала выделите меш-объект.",
    "garment.why.is-body": "Это тело freemode, а не одежда.",
    "garment.why.no-file": "Выберите файл.",
    "garment.why.file-type": "Импортировать можно только файлы FBX, OBJ, GLB и glTF.",
    "garment.why.markers": "Сначала расставьте маркеры в разделе Подгонка.",
    "garment.why.preset-name": "Дайте пресету название из букв или цифр.",
    "garment.why.preset-unreadable": "Не удалось прочитать пресет: {detail}",
    "garment.why.tops-only": "Опустить руки можно только у верха.",
    "garment.why.no-backup": (
        "Резервной копии пока нет. Она сохраняется перед каждым шагом, который меняет одежду."
    ),
    "garment.why.region-category": "Эта область не входит в выбранную категорию.",
    "garment.why.region-empty": "У одежды ничего нет в области {region}.",
    "garment.why.no-session": "Сеанс скульптинга не запущен.",
    "garment.why.no-armature": "Для проверки разрывов одежде нужны арматура и веса.",
    "garment.why.no-weights": "У одежды нет весов, чтобы ставить её в позы.",
    "garment.why.modifiers": "Модификатор меняет геометрию одежды. Разрывы можно проверить только без него.",
    "garment.why.no-uv": "У одежды нет UV-развёртки.",
    "garment.why.empty-slot": "В каждом слоте материала одежды должен быть материал.",
    "garment.why.uv-full": "У одежды столько UV-развёрток, сколько позволяет Blender. Сначала удалите одну.",
    "garment.why.no-sollumz": "Для создания LOD нужен Sollumz.",
    "garment.why.show-high": "Сначала покажите в Sollumz высокий уровень детализации (High).",
    "garment.why.no-download": "Тело сейчас не скачивается.",
    "garment.error.import": "Не удалось импортировать файл: {detail}",
    "garment.error.no-mesh": "В файле нет меша.",
    "garment.error.mode": "Не удалось запустить Режим скульптинга: {detail}",
    "garment.error.bake": "Запекание не удалось: {detail}",
    "garment.marker-error.no-markers": "Этой категории маркеры не нужны.",
    "garment.marker-error.too-small": (
        "Одежда слишком маленькая или плоская для маркеров. Проверьте, что она в метрах."
    ),
    "garment.marker-error.not-a-top": (
        "Одежда не похожа на верх. Проверьте категорию или расставьте маркеры вручную."
    ),
    "garment.marker-error.no-sleeves": (
        "Рукава не найдены. Выберите категорию Майка или расставьте маркеры рук вручную."
    ),
    "garment.marker-error.not-legs": (
        "Штанины не найдены. Проверьте категорию или расставьте маркеры вручную."
    ),
    "garment.done.use": "Выбрано для работы: {name}.",
    "garment.done.import": "Импортировано: {name} (вершин: {count}).",
    "garment.done.body": "Тело freemode добавлено ({gender}, версия {version}).",
    "garment.done.body-file": "Добавлено как тело: {name}.",
    "garment.done.markers": "Маркеров расставлено: {count}. До подгонки передвиньте те, что стоят не на месте.",
    "garment.done.mirror": "Левые маркеры отражены на правую сторону.",
    "garment.done.preset-saved": "Пресет позы сохранён: {name}.",
    "garment.done.preset-loaded": "Пресет позы загружен: {name}.",
    "garment.done.tpose": "Руки опущены на {angle}°. Резервная копия сохранена.",
    "garment.done.tpose-none": "Руки уже опущены под заданным углом.",
    "garment.done.restore": "Форма возвращена к состоянию до первого шага подгонки.",
    "garment.done.push": "Перемещено вершин: {moved}. Внутри тела: было {before}, сейчас {after}.",
    "garment.done.snug": "Придвинуто к телу вершин области {region}: {moved} (в среднем {mean} мм).",
    "garment.done.relax": "Ослаблено вершин области {region}: {moved}.",
    "garment.done.relax-smooth": (
        "Сглажено вершин области {region}: {moved} (формы до подгонки нет, сравнивать не с чем)."
    ),
    "garment.done.problems": (
        "Внутри: {inside}, слишком близко: {close}, растянуто: {stretched}, отстаёт: {floating}."
    ),
    "garment.done.check": "Проверка посадки выполнена. Внутри тела вершин: {inside}.",
    "garment.done.sculpt-start": "Сеанс скульптинга начат.",
    "garment.done.accept": (
        "Форма после скульптинга сохранена, перемещено вершин: {moved}. Внутри тела: было {before}, сейчас {after}."
    ),
    "garment.done.cancel-sculpt": "Скульптинг отменён: одежда вернулась к форме, которая была до сеанса.",
    "garment.done.tears": (
        "Вершин шва, расходящихся в тестовой позе: {count}. Они собраны в группе вершин DCT Tears."
    ),
    "garment.done.no-tears": "В тестовых позах швы не расходятся.",
    "garment.done.tears-welded": "У одежды нет открытых швов, которые могли бы разойтись.",
    "garment.done.prepare": (
        "Подготовлено: сшито вершин швов: {welded}, удалено свободных вершин: {removed}, треугольников: "
        "{triangles}."
    ),
    "garment.done.prepare-lining": (
        "Подготовлено: сшито вершин швов: {welded} (найдена подкладка, она оставлена отдельно), удалено свободных "
        "вершин: {removed}, треугольников: {triangles}."
    ),
    "garment.done.combine": (
        "Материалов объединено в одну текстуру {size} пикселей: {count}; раскладка занимает {used} % её площади "
        "(разрезано полос: {cut})."
    ),
    "garment.done.lods": "Уровни детализации, треугольников: высокий {high}, средний {medium}, низкий {low}.",
    "garment.done.clean": "Проверка: CLEAN.",
    "garment.done.findings": "Проверка: замечаний, на которые стоит посмотреть: {count}.",
    "garment.info.pose": (
        "Выберите позу аватара, на котором сделана одежда. Одежду, сделанную в T-позе, можно перевести в A-позу "
        "игры в разделе Подгонка."
    ),
    "garment.info.garment": (
        "Инструменты меняют только этот объект. Кнопка Импортировать одежду переводит сантиметры и миллиметры (в "
        "них экспортирует Marvelous Designer) в метры. Каждый шаг, который меняет одежду, сохраняет резервную "
        "копию, а Ctrl+Z отменяет его."
    ),
    "garment.info.body": (
        "Тело freemode скачивается с gta.clothing один раз для каждой версии и хранится в папке дополнения. Оно "
        "добавляется в сцену отдельным объектом, и инструменты никогда его не меняют."
    ),
    "garment.info.markers": (
        "Маркеры обозначают суставы ped: шею, грудь, таз, плечи, локти, запястья и бёдра. Кнопка Автомаркеры "
        "расставляет их по форме одежды; передвиньте те, что стоят не на месте. Кнопка Отразить слева направо "
        "копирует левую сторону на правую."
    ),
    "garment.info.tpose": (
        "Для одежды, сделанной в T-позе: временная арматура, построенная по маркерам, опускает руки до угла рук и "
        "затем удаляется. Маркеры следуют за руками."
    ),
    "garment.info.backups": (
        "Перед каждым шагом, который меняет одежду, копия её меша сохраняется в файле .blend (первая и самые "
        "новые). Кнопка Вернуть до подгонки возвращает первую."
    ),
    "garment.info.push": (
        "Перемещает всё, что находится внутри тела или ближе зазора, наружу на расстояние зазора. Соседние вершины "
        "следуют за ними, поэтому складок не образуется."
    ),
    "garment.info.regions": (
        "Кнопка Прижать к телу подтягивает свободно сидящую область к телу, вплоть до зазора. Кнопка Ослабить "
        "растяжение возвращает растянутые части ближе к исходному размеру. Края области плавно переходят в "
        "остальную одежду."
    ),
    "garment.info.problems": (
        "Раскрашивает одежду во время работы: красным то, что внутри тела, жёлтым слишком близкое, фиолетовым "
        "растянутое по сравнению с исходной формой, синим плечо, которое отстаёт от тела."
    ),
    "garment.info.check": (
        "Измеряет, насколько каждая область одежды отстоит от тела: медиану и диапазон большинства её вершин, в "
        "миллиметрах. Отрицательные значения означают, что вершины внутри тела."
    ),
    "garment.info.sculpt": (
        "Режим скульптинга с кистью Grab, тело показано каркасом. Принять сохраняет форму (и возвращает наружу то, "
        "что попало в тело, если включено Держать вне тела); Отмена возвращает прежнюю форму."
    ),
    "garment.info.tears": (
        "Нужны арматура и веса на одежде. Одежда проводится через несколько тестовых поз (руки вверх, руки вперёд, "
        "ноги вперёд, скручивание), и показываются швы, которые расходятся."
    ),
    "garment.info.prepare": (
        "Сшивает швы между деталями кроя (подкладку никогда не пришивает к верху), удаляет свободные части, "
        "триангулирует, включает гладкое затенение и задаёт одежде цвета вершин Sollumz Color 1 и Color 2 со "
        "значениями выше."
    ),
    "garment.info.combine": (
        "Упаковывает все UV-острова в один квадрат и запекает цвет каждого материала в одну текстуру, которая "
        "становится единственным материалом одежды. Исходная UV-развёртка сохраняется как DCT Source UV. "
        "Прозрачность не запекается."
    ),
    "garment.info.lods": (
        "Упрощает копию одежды до каждого бюджета треугольников и помещает её в слоты LOD Sollumz для среднего и "
        "низкого уровней; их веса берутся с высокого уровня."
    ),
    "garment.info.validate": (
        "Быстрые локальные проверки: веса, больше четырёх костей на вершину, испорченные координаты, UV-раскладка, "
        "цвета вершин, вершины каждого уровня детализации и сколько одежды внутри тела."
    ),
    # ---- adding to Durty Cloth Tool ----
    "error.item-limit": "В проекте уже столько одежды, сколько позволяет бесплатная версия Durty Cloth Tool.",
    "garment.next.done": (
        "Готово: одежда в вашем проекте Durty Cloth Tool. Кнопки Отправить модель и Сохранить модель в одежду в "
        "разделе Модель обновляют её (входят в Durty Cloth Tool Ultimate)."
    ),
    "garment.next.validate-problems": (
        "Далее: исправьте то, что перечисляет Проверить в разделе Готово к игре, затем проверьте снова."
    ),
    "garment.next.adding": "Добавление: Durty Cloth Tool показывает одежду. Выберите там Добавить в проект или Отмена.",
    "garment.next.connect": (
        "Далее: подключитесь к Durty Cloth Tool (Настройка подключения), чтобы добавить одежду в проект."
    ),
    "garment.next.project": (
        "Далее: откройте проект в Durty Cloth Tool, затем добавьте одежду в разделе Готово к игре."
    ),
    "garment.next.sollumz": "Далее: установите Sollumz, чтобы добавить одежду в Durty Cloth Tool.",
    "garment.next.skeleton": (
        "Далее: выберите Использовать скелет Durty Cloth Tool в разделе Готово к игре или Добавить в проект Durty "
        "Cloth Tool (эта кнопка тоже это делает)."
    ),
    "garment.next.add": "Далее: выберите Добавить в проект Durty Cloth Tool в разделе Готово к игре.",
    "add.heading": "Добавить в Durty Cloth Tool",
    "add.heading.variations": "Цветовые вариации",
    "add.heading.skeleton": "Скелет freemode",
    "add.target": "Одежда добавится как {slot}, {gender}. Изменить оба можно в разделе Настройка.",
    "add.variation.none": "Цветовой текстуры пока нет",
    "add.variations.subtext": "Вариаций: {count} из максимум {limit}.",
    "add.prop.name": "Название одежды",
    "add.prop.name.desc": (
        "Название, которое одежда получит в Durty Cloth Tool. Если пусто, используется имя одежды в Blender"
    ),
    "add.prop.skin": "Видна кожа",
    "add.prop.skin.desc": (
        "Одежда открывает часть кожи ped, поэтому игра окрашивает её в тон кожи ped (вариант _r)"
    ),
    "add.prop.image": "Изображение вариации",
    "add.prop.image.desc": "Цветовая текстура этой вариации, в раскладке собственной текстуры одежды",
    "add.prop.variation-name": "Название вариации",
    "add.prop.variation-name.desc": (
        "Название этой цветовой вариации в Durty Cloth Tool. Если пусто, используется имя изображения"
    ),
    "add.prop.first-name.desc": (
        "Название первой цветовой вариации (собственной текстуры одежды) в Durty Cloth Tool. Если пусто, "
        "используется имя изображения"
    ),
    "add.op.skeleton": "Использовать скелет Durty Cloth Tool",
    "add.op.skeleton.desc": (
        "Получить из Durty Cloth Tool скелет freemode пола, выбранного в разделе Настройка, и надеть на него "
        "одежду, готовую для Sollumz"
    ),
    "add.op.add": "Добавить в проект Durty Cloth Tool",
    "add.op.add.desc": (
        "Проверить одежду, экспортировать её с помощью Sollumz и добавить как новую в проект, открытый в Durty "
        "Cloth Tool. Durty Cloth Tool сначала спросит вас"
    ),
    "add.op.cancel.desc": "Прервать добавление. Пока Durty Cloth Tool ещё спрашивает, ничего не добавляется",
    "add.op.add-variation": "Добавить цветовую вариацию",
    "add.op.add-variation.desc": "Добавить ещё одно изображение как цветовую вариацию одежды",
    "add.op.remove-variation": "Удалить",
    "add.op.remove-variation.desc": "Удалить эту цветовую вариацию",
    "add.info": (
        "Добавляет одежду в проект, открытый в Durty Cloth Tool, как новую. Durty Cloth Tool сначала показывает её, и "
        "ничего не добавляется, пока вы не выберете там Добавить в проект. Нужны Durty Cloth Tool с открытым проектом "
        "и настроенной в нём игрой, а также Sollumz."
    ),
    "add.info.variations": (
        "Собственная текстура одежды становится первой цветовой вариацией. Добавьте ещё изображения в той же "
        "раскладке: каждое станет цветовой вариацией одежды с названием, которое вы ему дадите."
    ),
    "add.info.skeleton": (
        "Durty Cloth Tool отправляет скелет freemode пола, выбранного в разделе Настройка, собранный из файлов "
        "вашей игры. Sollumz импортирует его как арматуру, а одежда становится его дочерним объектом с "
        "модификатором Арматура; её группы вершин сохраняют имена костей. Кнопка Добавить делает это за вас, "
        "когда нужно."
    ),
    "add.skeleton.ready": "На скелете Durty Cloth Tool ({gender}, костей: {count}): {name}",
    "add.skeleton.missing": (
        "Одежда ещё не на скелете Durty Cloth Tool. Выберите Использовать скелет Durty Cloth Tool или Добавить "
        "(эта кнопка сделает это за вас)."
    ),
    "add.skeleton.other-gender": (
        "Одежда на скелете другого пола ({gender}). Выберите Использовать скелет Durty Cloth Tool, чтобы "
        "перенести её на скелет пола, выбранного в разделе Настройка."
    ),
    "add.skeleton.modifier": (
        "Модификатор Арматура у одежды не использует её скелет Durty Cloth Tool. Снова выберите Использовать "
        "скелет Durty Cloth Tool."
    ),
    "add.skeleton.order": (
        "Кости скелета идут не в игровом порядке, поэтому веса двигали бы не те кости. Снова выберите "
        "Использовать скелет Durty Cloth Tool, а не меняйте его кости."
    ),
    "add.skeleton.bones": (
        "В скелете костей: {count}, а в скелете freemode: {expected}. Снова выберите Использовать скелет Durty "
        "Cloth Tool, а не меняйте его кости."
    ),
    "add.skeleton.import": "Sollumz не импортировал скелет как одну арматуру. Подробности в его журнале Info.",
    "add.skeleton.invalid": (
        "Durty Cloth Tool прислал скелет, который дополнение не может прочитать. Обновите оба и попробуйте снова."
    ),
    "add.skeleton.game-required": (
        "Для скелета freemode Durty Cloth Tool нужна ваша установка GTA V. Настройте игру в Durty Cloth Tool и "
        "попробуйте снова."
    ),
    "add.skeleton.busy": "Durty Cloth Tool ещё читает файлы игры. Попробуйте снова чуть позже.",
    "add.dct-too-old": "Этот Durty Cloth Tool ещё не умеет добавлять одежду из Blender. Обновите Durty Cloth Tool.",
    "add.done.skeleton": "Одежда на скелете Durty Cloth Tool ({gender}, костей: {count}): {name}.",
    "add.fetching": "Получение скелета freemode ({gender}) из Durty Cloth Tool…",
    "add.progress.skeleton": "Получение скелета freemode из Durty Cloth Tool…",
    "add.sent": "Отправлено: {name}, цветовых вариаций: {count}. Выберите Добавить в проект в Durty Cloth Tool.",
    "add.waiting": "Durty Cloth Tool показывает одежду. Выберите там Добавить в проект или Отмена.",
    "add.waiting.subtext": (
        "Ничего не добавляется, пока вы не выберете Добавить в проект в Durty Cloth Tool. Отмена здесь отзывает "
        "добавление."
    ),
    "add.withdrawing": "Отмена добавления…",
    "add.blocked": (
        "Добавление заблокировано: сначала исправьте проблемы ({count}), они перечислены в разделе Готово к игре."
    ),
    "add.problems": "Сначала исправьте это ({count}):",
    "add.findings": "Проверки Durty Cloth Tool: {count}",
    "add.added.subtext": (
        "Drawable Dictionary связан с новой одеждой: кнопки Отправить модель и Сохранить модель в одежду в "
        "разделе Модель обновляют её (входят в Durty Cloth Tool Ultimate)."
    ),
    "add.invalid": "Добавление нельзя отправить: {detail}",
    "add.why.connect": "Подключитесь к Durty Cloth Tool, чтобы добавить одежду в проект.",
    "add.why.no-project": "Откройте проект в Durty Cloth Tool, чтобы добавить в него одежду.",
    "add.why.adding": "Добавление ожидает ответа Durty Cloth Tool.",
    "add.why.fetching": "Ожидание скелета freemode от Durty Cloth Tool.",
    "add.why.nothing-running": "Ничего не выполняется.",
    "add.why.no-template": "Durty Cloth Tool не прислал скелет freemode. Попробуйте снова.",
    "add.why.garment-changed": (
        "Тем временем была выбрана другая одежда, поэтому шаг не выполнен. Запустите его снова."
    ),
    "add.why.no-weights": (
        "У одежды ещё нет весов для скелета freemode. Назначьте ей веса костей скелета (группы вершин с их "
        "именами, например SKEL_Spine3)."
    ),
    "add.why.unknown-groups": (
        "Группы вершин, которых нет среди костей скелета freemode ({count}): {names}. Переименуйте или удалите "
        "их, иначе игра будет двигать их вместе с корневой костью."
    ),
    "add.why.name-empty": "Дайте одежде название.",
    "add.why.name-invalid": (
        "Название одежды может содержать не больше {limit} символов и не может содержать управляющие символы."
    ),
    "add.why.combine": (
        "У одежды материалов: {count}. Сначала выберите Объединить материалы: каждая цветовая вариация состоит "
        "из одной текстуры."
    ),
    "add.why.no-diffuse": "У материала одежды нет цветовой текстуры. Кнопка Объединить материалы создаёт её.",
    "add.why.variation-empty": "У цветовой вариации {number} нет изображения. Выберите его или удалите строку.",
    "add.why.too-many": "У одежды может быть не больше {limit} цветовых вариаций.",
    "add.why.variation-twice": (
        "Изображение {name} используется для двух цветовых вариаций. Каждой нужно своё."
    ),
    "add.why.too-large": (
        "Модель и её изображения вместе больше {size} MiB, их нельзя отправить. Используйте изображения поменьше "
        "или меньше цветовых вариаций."
    ),
    "add.why.work-folder": (
        "Папка дополнения для экспорта является ссылкой на другое место, поэтому она не используется."
    ),
    "add.why.convert": "Sollumz не смог превратить одежду в Drawable Model ({detail}).",
    "add.why.material": "Sollumz не смог назначить одежде шейдер ped ({detail}).",
    "add.picture.empty": "В изображении {name} нет пикселей.",
    "add.picture.too-large": (
        "Изображение {name} больше {size} пикселей по стороне, а такое Durty Cloth Tool не принимает."
    ),
    "add.picture.not-multiple-of-four": (
        "Изображение {name} имеет размер {width} x {height}: Durty Cloth Tool нужно, чтобы обе стороны делились "
        "на четыре."
    ),
    "add.picture.non-power-of-two": (
        "Изображение {name} имеет размер {width} x {height}, это не степень двойки (например, 1024 или 2048)."
    ),
    "add.picture.large": (
        "Изображение {name} больше {size} пикселей по стороне и занимает много игровой памяти."
    ),
    "add.picture.small": "Изображение {name} меньше {size} пикселей по стороне.",
    "add.picture.unusable": "Изображение {name} нельзя отправить: {problem}",
    "add.export.empty": (
        "Sollumz экспортировал Drawable Dictionary без геометрии одежды. Подробности в его журнале Info."
    ),
    "add.export.several": (
        "Sollumz экспортировал несколько drawable ({count}); Durty Cloth Tool принимает один на одежду."
    ),
    "add.export.skeleton": "В экспорте всё ещё есть скелет. Обновите Sollumz и попробуйте снова.",
    "add.export.errors": (
        "Sollumz сообщил об ошибках при экспорте, поэтому части одежды может не хватать. Подробности в его "
        "журнале Info."
    ),
    "add.export.unreadable": "Не удалось прочитать экспорт ({detail}).",
    "add.export.warnings": "Sollumz сообщил о предупреждениях при экспорте; подробности в его журнале Info.",
    "add.result.added": "Добавлено в проект как {slot}: {name}.",
    "add.result.added-unlinked": (
        "Добавлено в проект: {name}, но модель в Blender не удалось связать с этой одеждой ({detail})."
    ),
    "add.result.denied": "Durty Cloth Tool не добавил одежду: там выбрали Отмена. Проект не изменён.",
    "add.result.withdrawn": "Добавление отменено. Проект не изменён.",
    "add.result.cancel-unanswered": (
        "Добавление отменено, но Durty Cloth Tool этого не подтвердил. Проверьте проект в Durty Cloth Tool."
    ),
    "add.result.timeout": (
        "Durty Cloth Tool не ответил на добавление вовремя. Проверьте проект в Durty Cloth Tool."
    ),
    "add.result.disconnected": (
        "Связь с Durty Cloth Tool потеряна во время добавления. Проверьте проект в Durty Cloth Tool, прежде чем "
        "добавлять одежду снова."
    ),
    "add.result.item-limit": (
        "Durty Cloth Tool не добавил одежду: в проекте уже столько одежды, сколько позволяет бесплатная версия "
        "Durty Cloth Tool. Этот лимит задаёт и проверяет Durty Cloth Tool, а не дополнение; сколько можно "
        "добавить, решает ваш план в Durty Cloth Tool."
    ),
    "add.result.rejected": (
        "Durty Cloth Tool не смог использовать модель или цветовую вариацию, поэтому ничего не добавлено. Его "
        "проверки ниже объясняют почему."
    ),
    "add.result.no-project": "Сначала откройте проект в Durty Cloth Tool, затем добавьте одежду снова.",
    "add.result.item-refused": (
        "Этот проект не принимает одежду freemode таким способом (например, проект пользовательского ped). "
        "Откройте проект freemode в Durty Cloth Tool."
    ),
    "add.result.busy": (
        "Durty Cloth Tool занят (идёт сборка или другое добавление ждёт ответа). Попробуйте снова чуть позже."
    ),
    "add.result.rate-limited": (
        "Слишком много добавлений за короткое время. Подождите несколько секунд и попробуйте снова."
    ),
    "add.result.save-failed": "Durty Cloth Tool не смог добавить одежду. Подробности в его строке состояния.",
    "add.finding.rig-invalid": (
        "Веса или индексы костей не подходят к скелету freemode: в игре одежда двигалась бы неправильно."
    ),
    "add.finding.rig-unchecked": "Durty Cloth Tool не смог прочитать веса, чтобы проверить их.",
    "add.finding.single-bone-rig": (
        "Почти весь вес уровня детализации приходится на одну кость, поэтому одежда почти не двигалась бы вместе "
        "с телом."
    ),
    "add.finding.hair-tint-unsupported": "Эти волосы не могут принимать цвет волос, выбранный игроком.",
    "add.finding.picture.non-power-of-two": (
        "Размер цветовой вариации не является степенью двойки (например, 1024 или 2048)."
    ),
    "add.finding.picture.not-multiple-of-four": "Размер цветовой вариации не делится на четыре.",
    "add.finding.picture.too-large": (
        "Цветовая вариация больше, чем советует Durty Cloth Tool (2048 пикселей по стороне; он принимает не больше "
        "4096)."
    ),
    "add.finding.picture.too-small": "Цветовая вариация меньше 16 пикселей по стороне.",
}
