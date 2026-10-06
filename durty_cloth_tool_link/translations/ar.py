# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2026 Schmid Software Solutions (https://schmid-software.de)
"""Arabic (العربية). Modern Standard Arabic, translated but not mirrored, as Durty Cloth Tool does."""

TEXT = {
    "path.connected-apps": "خيارات > التطبيقات المتصلة",
    "path.edit-in-app": "تعديل في التطبيق المتصل",
    "panel.main": "Durty Cloth Tool",
    "panel.details": "الاتصال",
    "panel.setup": "بدء الاتصال",
    "panel.linked": "الملابس المرتبطة",
    "panel.live": "المعاينة المباشرة",
    "panel.checks": "فحص النسيج",
    "panel.model": "النموذج",
    "panel.settings": "الإعدادات",
    "chip.connected": "متصل",
    "chip.live": "مباشر",
    "chip.connecting": "جارٍ الاتصال",
    "chip.action": "مطلوب إجراء",
    "chip.offline": "غير متصل",
    "chip.problem": "مشكلة",
    "state.idle": "غير متصل",
    "state.connecting": "جارٍ البحث عن Durty Cloth Tool",
    "state.waiting": "لم يُعثر على Durty Cloth Tool. ستتم المحاولة مرة أخرى",
    "state.reconnecting": "جارٍ إعادة الاتصال بـ Durty Cloth Tool",
    "state.hello": "جارٍ الاتصال",
    "state.signing-in": "بانتظار تسجيل الدخول",
    "state.authenticating": "جارٍ تسجيل الدخول",
    "state.ready": "تم تسجيل الدخول باسم {name}",
    "state.signed-out": "تم تسجيل الخروج",
    "state.dct-signed-out": "Durty Cloth Tool غير مسجّل الدخول",
    "state.dct-disconnected": "تم قطع الاتصال في Durty Cloth Tool",
    "details.status": "الحالة: {state}",
    "details.account": "تم تسجيل الدخول باسم {name}",
    "details.not-signed-in": "لم يتم تسجيل الدخول",
    "details.project": "المشروع: {name}",
    "details.addon": "الإضافة {version} ({channel})",
    "online.off": (
        "الوصول إلى الإنترنت في Blender متوقف، لذلك لا يمكن توصيل Durty Cloth Tool: كل اتصال يُؤكَّد بتسجيل دخولك إلى "
        "gta.clothing. اسمح به من التفضيلات > النظام > الشبكة."
    ),
    "dct-signed-out": (
        "Durty Cloth Tool غير مسجّل الدخول. سجّل الدخول في Durty Cloth Tool، ثم اختر اتصال. تعيد الإضافة المحاولة "
        "تلقائيًا من حين لآخر أيضًا."
    ),
    "dct-disconnected": "تم قطع اتصال هذا التطبيق في Durty Cloth Tool. اختر اتصال لتوصيله مرة أخرى.",
    "setup.find.title": "العثور على Durty Cloth Tool",
    "setup.find.done": "تم العثور على Durty Cloth Tool",
    "setup.find.subtext": "شغّل Durty Cloth Tool على هذا الحاسوب. ستعثر عليه الإضافة تلقائيًا.",
    "setup.find.searching": "جارٍ البحث عن Durty Cloth Tool…",
    "setup.find.waiting": "Durty Cloth Tool لا يعمل بعد. تواصل الإضافة البحث…",
    "setup.sign-in.title": "تسجيل الدخول عبر gta.clothing",
    "setup.sign-in.done": "تم تسجيل الدخول",
    "setup.sign-in.subtext": (
        "يستخدم Creator Link حسابك على gta.clothing (Discord). تسجّل الدخول مرة واحدة على هذا الحاسوب."
    ),
    "setup.sign-in.starting": "جارٍ بدء تسجيل الدخول…",
    "setup.sign-in.finding": "جارٍ البحث عن Durty Cloth Tool للموافقة على تسجيل الدخول…",
    "setup.sign-in.how": "يطلب منك Durty Cloth Tool الموافقة. إذا لم يكن قيد التشغيل، تحصل على رمز لمتصفحك.",
    "setup.sign-in.waiting": "بانتظار الموافقة…",
    "setup.sign-in.asked": "يعرض Durty Cloth Tool طلب تسجيل دخول. وافق عليه هناك.",
    "setup.sign-in.approved": "وافق Durty Cloth Tool على تسجيل الدخول. جارٍ الإنهاء…",
    "setup.sign-in.declined": "لم يوافق Durty Cloth Tool على تسجيل الدخول. سجّل الدخول في المتصفح بدلًا من ذلك.",
    "setup.sign-in.browser-subtext": "افتح صفحة تسجيل الدخول وتحقق من أنها تعرض هذا الرمز:",
    "setup.sign-in.signed-out": "لقد سجّلت الخروج. سجّل الدخول مرة أخرى لاستخدام Creator Link.",
    "linked.project": "المشروع: {name}",
    "linked.no-project": "افتح مشروعًا في Durty Cloth Tool.",
    "linked.no-cloth": "حدد قطعة ملابس في Durty Cloth Tool للعمل عليها هنا.",
    "linked.variation": "التنويعة {letter}",
    "linked.number": "رقم {number}",
    "linked.unknown": "الملابس المرتبطة",
    "linked.unknown-subtext": "حددها مرة واحدة في Durty Cloth Tool لترى اسمها هنا.",
    "linked.map": "الخريطة",
    "linked.follows": "يتبع تحديدك في Durty Cloth Tool",
    "linked.image": "مرتبطة بالصورة أدناه",
    "linked.open-map": "فتح خريطة في Blender",
    "linked.map-missing.diffuse": "لا تحتوي قطعة الملابس هذه على خريطة منتشرة.",
    "linked.map-missing.normal": "لا تحتوي قطعة الملابس هذه على خريطة الاتجاهات.",
    "linked.map-missing.specular": "لا تحتوي قطعة الملابس هذه على خريطة اللمعان.",
    "map.diffuse": "منتشرة (لون)",
    "map.diffuse-short": "منتشرة",
    "map.diffuse.desc": "نسيج اللون لقطعة الملابس",
    "map.normal": "الاتجاهات",
    "map.normal.desc": "خريطة الاتجاهات لقطعة الملابس",
    "map.specular": "اللمعان",
    "map.specular.desc": "خريطة اللمعان لقطعة الملابس",
    "gender.male": "ذكر",
    "gender.female": "أنثى",
    "open.opened": "فُتح من Durty Cloth Tool: {name}",
    "open.texture-busy": (
        "أرسل Durty Cloth Tool {name}، لكن معاينة مباشرة قيد التشغيل أو الحفظ. أوقفها، ثم أرسل الخريطة مرة أخرى."
    ),
    "open.texture-failed": "تعذّر فتح {name}: {detail}",
    "open.stop-live-first": "أوقف المعاينة المباشرة أولًا.",
    "open.reading": "جارٍ قراءة الخريطة من Durty Cloth Tool…",
    "open.map-upsell": "فتح خرائط قطعة الملابس هنا مضمّن في Durty Cloth Tool Ultimate.",
    "open.model-importing": "جارٍ استيراد {name} باستخدام Sollumz…",
    "open.model-needs-sollumz": "أرسل Durty Cloth Tool النموذج {name}. {problem}",
    "open.model-busy": (
        "أرسل Durty Cloth Tool النموذج {name}، لكن نموذجًا آخر ما زال قيد الإرسال أو الحفظ. أرسله مرة أخرى بعد لحظة."
    ),
    "open.model-failed": "تعذّر فتح النموذج {name}: {detail}",
    "open.import-failed": "تعذّر على Sollumz استيراد النموذج ({detail}). التفاصيل في سجل Info الخاص به.",
    "open.no-dictionary": "لم يستورد Sollumz أي Drawable Dictionary. التفاصيل في سجل Info الخاص به.",
    "open.import-errors": (
        "أبلغ Sollumz عن أخطاء أثناء الاستيراد، لذا لم يُربط النموذج بقطعة الملابس. التفاصيل في سجل Info الخاص به."
    ),
    "open.model-warnings": "فُتح من Durty Cloth Tool: {name}. أبلغ Sollumz عن تحذيرات؛ التفاصيل في سجل Info الخاص به.",
    "live.off": "ابدأ المعاينة المباشرة لترى رسمك على الـ ped.",
    "live.reading": "جارٍ قراءة الصورة…",
    "live.starting": "جارٍ بدء المعاينة المباشرة…",
    "live.on": "مباشر على الـ ped",
    "live.sending": "جارٍ إرسال الصورة…",
    "live.not-worn": "ألبِس الـ ped قطعة الملابس هذه في Durty Cloth Tool لتراها.",
    "live.paused-dct": "المعاينة ثلاثية الأبعاد متوقفة مؤقتًا في Durty Cloth Tool.",
    "live.paused": "متوقف مؤقتًا. تُرسل تغييراتك عند الاستئناف.",
    "live.saving": "جارٍ الحفظ…",
    "live.unsaved": "لم يُحفظ في المشروع بعد",
    "live.linked": "مرتبطة بـ {name} · {map}",
    "live.map": "الخريطة: {map}",
    "live.save-subtext": (
        "يكتب الحفظ هذه الخريطة في مشروعك. يمكنك التراجع عنه في سجل قطعة الملابس في Durty Cloth Tool."
    ),
    "live.saved": "تم الحفظ في {name}. يمكنك التراجع عنه في السجل.",
    "live.saved-unnamed": "تم الحفظ في قطعة الملابس. يمكنك التراجع عنه في السجل.",
    "live.saved-variation": "تم الحفظ كتنويعة جديدة لـ {name}.",
    "live.saved-variation-unnamed": "تم الحفظ كتنويعة جديدة.",
    "live.discarded": "تم تجاهل التغييرات في Durty Cloth Tool.",
    "live.stopped": "توقفت المعاينة المباشرة.",
    "live.stopped-unsaved": "توقفت المعاينة المباشرة. لم تُحفظ التغييرات في المشروع؛ تحتفظ بها الصورة في Blender.",
    "live.failed": "توقفت المعاينة المباشرة بعد مشكلة غير متوقعة: {detail}",
    "live.upsell": "المعاينة المباشرة مضمّنة في Durty Cloth Tool Ultimate.",
    "live.save-upsell": "الحفظ في قطعة الملابس مضمّن في Durty Cloth Tool Ultimate.",
    "live.image-changed": "تغيّر حجم الصورة. ابدأ المعاينة المباشرة مرة أخرى.",
    "live.image-removed": "تمت إزالة الصورة.",
    "live.no-memory": "لا توجد ذاكرة كافية لصورة بهذا الحجم.",
    "colour.non-color-diffuse": "الصورة مضبوطة على Non-Color؛ تُرسل قيمها كلون دون تغيير.",
    "colour.unknown-diffuse": "تُرسل مساحة الألوان {space} للصورة دون تحويل؛ استخدم sRGB للحصول على ألوان دقيقة.",
    "colour.unknown-data": "اضبط مساحة ألوان الخريطة على Non-Color؛ تُرسل قيم {space} كما هي في Blender.",
    "image.none": "اختر صورة أولًا.",
    "image.tiled": "لا يمكن استخدام صور UDIM (المبلّطة). استخدم صورة واحدة.",
    "image.source": "يمكن استخدام ملفات الصور والصور المولّدة فقط.",
    "image.unreadable": "تعذرت قراءة الصورة.",
    "image.not-loaded": "تعذر تحميل الصورة. تحقق من وجود ملفها.",
    "image.channels": "يمكن استخدام الصور الرمادية وRGB وRGBA فقط.",
    "image.empty": "الصورة بلا بكسلات. افتحها أو أنشئها أولًا.",
    "image.too-large": "لا يمكن استخدام صور يزيد ضلعها على {size} بكسل.",
    "image.no-painted": "لم يُعثر على صورة يتم الرسم عليها. اختر الصورة من القائمة.",
    "checks.errors": "الأخطاء: {count}",
    "checks.warnings": "التحذيرات: {count}",
    "checks.notes": "الملاحظات: {count}",
    "checks.clean": "لم يُعثر على مشكلات.",
    "checks.not-checked": "يفحص Durty Cloth Tool النسيج عند بدء المعاينة المباشرة.",
    "checks.checking": "جارٍ فحص النسيج…",
    "checks.unavailable": "فحص النسيج مضمّن في Durty Cloth Tool Ultimate.",
    "severity.error": "خطأ",
    "severity.warning": "تحذير",
    "severity.info": "ملاحظة",
    "finding.unknown": "أبلغ Durty Cloth Tool عن {code}.",
    "finding.non-power-of-two": "الحجم ليس قوة للعدد اثنين (مثل 1024 أو 2048).",
    "finding.not-multiple-of-four": "الحجم ليس مضاعفًا للعدد أربعة، وهو ما تحتاجه الأنسجة المضغوطة.",
    "finding.too-large": "يزيد ضلع النسيج على 2048 بكسل، مما يستهلك الكثير من ذاكرة اللعبة.",
    "finding.too-small": "يقل ضلع النسيج عن 16 بكسل.",
    "finding.size-changed": "الحجم يختلف عن النسيج المحفوظ في المشروع.",
    "finding.palette-alpha": (
        "تستخدم قطعة الملابس هذه لوحة ألوان: قناة ألفا فيها تختار ألوان اللوحة، لذا ارسم ألفا بحذر."
    ),
    "finding.cutout-alpha": "تستخدم قطعة الملابس هذه ألفا كقص: البكسلات الشفافة مخفية على الـ ped.",
    "finding.hair-ramp": "هذا شعر: تلوّنه اللعبة بلون الشعر الذي يختاره اللاعب.",
    "finding.bc1-alpha": "يحتفظ النسيج المحفوظ فقط بألفا شفافة تمامًا أو معتمة تمامًا.",
    "finding-fix.non-power-of-two": "غيّر الحجم إلى قوة للعدد اثنين، مثل 1024 x 1024، قبل الحفظ.",
    "finding-fix.not-multiple-of-four": "غيّر الحجم بحيث يقبل الضلعان القسمة على أربعة، مثل 1024 x 512.",
    "finding-fix.too-large": "استخدم 2048 بكسل أو أقل للضلع، إلا إذا احتاجت قطعة الملابس إلى التفاصيل الإضافية.",
    "finding-fix.too-small": "استخدم 16 بكسل على الأقل للضلع.",
    "finding-fix.size-changed": (
        "الحفظ يستبدل النسيج بهذا الحجم. أعد الحجم المحفوظ إن لم تكن تقصد تغييره."
    ),
    "finding-fix.palette-alpha": "اترك قيم ألفا كما هي إلا إذا كنت تقصد تغيير ألوان اللوحة.",
    "finding-fix.cutout-alpha": "ارسم الشفافية فقط حيث يجب إخفاء قطعة الملابس.",
    "finding-fix.hair-ramp": "ارسم التظليل في القناة الخضراء والخصلات الفاتحة في القناة الحمراء، لا اللون النهائي.",
    "finding-fix.bc1-alpha": "استخدم ألفا شفافة تمامًا أو معتمة تمامًا؛ تضيع الحواف الناعمة عند الحفظ.",
    "model.subtext": "يرسل النموذج مرة أخرى بعد لحظة من توقفك عن التعديل.",
    "model.name": "النموذج: {name}",
    "model.sending": "جارٍ إرسال {name} (الأنسجة: {count})",
    "model.previewing": "يُعرض على الـ ped في Durty Cloth Tool. احفظه أو تجاهله هناك أو هنا.",
    "model.findings": "أبلغ Durty Cloth Tool عن ملاحظات: {count}.",
    "model.warnings-paused": (
        "أبلغ Sollumz عن تحذيرات، لذلك توقف الإرسال التلقائي مؤقتًا. راجع سجل Info في Sollumz، ثم أرسل مرة أخرى "
        "للاستئناف."
    ),
    "model.warnings": "أبلغ Sollumz عن تحذيرات؛ التفاصيل في سجل Info الخاص به.",
    "model.saving": "جارٍ حفظ النموذج في Durty Cloth Tool…",
    "model.saved": "تم حفظ النموذج في قطعة الملابس. يمكنك التراجع عنه في السجل.",
    "model.discarded": "تم تجاهل النموذج في Durty Cloth Tool.",
    "model.save-retry": "لا يزال Durty Cloth Tool يحمّل النموذج. سيتم الحفظ بعد لحظة…",
    "model.save-busy": "لا يزال Durty Cloth Tool مشغولًا بالنموذج. احفظ مرة أخرى بعد لحظة.",
    "model.block.no-model": "أرسل نموذجًا أولًا.",
    "model.block.saving": "الحفظ جارٍ بالفعل.",
    "model.block.waiting": "انتظر حتى يرد Durty Cloth Tool.",
    "model.block.pushing": "انتظر حتى يظهر آخر إرسال في Durty Cloth Tool، ثم احفظ.",
    "model.block.due": "ستُرسل أحدث تغييراتك قريبًا. احفظ بعد ظهورها في Durty Cloth Tool.",
    "model.wait.tool": "ينتظر الإرسال التلقائي حتى تنتهي الأداة الجارية.",
    "model.wait.mode": "ينتظر الإرسال التلقائي حتى تغادر {mode}.",
    "model.gone": "لم يعد النموذج المرسل في هذا الملف. أرسله مرة أخرى.",
    "model.linked": "مرتبط بـ {name}",
    "model.linked-twice": "{name} مرتبط بقطعة الملابس نفسها. ألغِ ربط أحدهما: كل قطعة ملابس تقبل نموذجًا واحدًا.",
    "model.not-linked": "هذا الـ Drawable Dictionary غير مرتبط بأي قطعة ملابس.",
    "model.failed": "فشل الإرسال التلقائي: {detail}",
    "model.select": "حدد النموذج المراد إرساله: Drawable Dictionary من Sollumz أو كائنًا داخله.",
    "model.one-root": "حدد كائنات من Drawable Dictionary واحد فقط.",
    "model.needs-dictionary": (
        "يحتاج Durty Cloth Tool إلى Drawable Dictionary. اجعل الـ Drawable تابعًا لواحد (Sollumz: Create Drawable "
        "Dictionary) وأرسل مرة أخرى."
    ),
    "model.not-sollumz": "حدد Drawable Dictionary من Sollumz أو كائنًا داخله.",
    "model.unhide": "أظهر الـ Drawable Dictionary (أو كائنًا داخله) واجعله قابلًا للتحديد، ثم أرسل مرة أخرى.",
    "model.not-shown": "النموذج ليس في أي مشهد تعرضه نافذة Blender. اعرض مشهده، ثم أرسل مرة أخرى.",
    "model.not-in-layer": "النموذج ليس في طبقة العرض الحالية. أظهره، ثم أرسل مرة أخرى.",
    "model.export-failed": "تعذر على Sollumz تصدير النموذج: {detail}",
    "model.not-exported": "لم يصدّر Sollumz النموذج. التفاصيل في سجل Info الخاص به.",
    "sollumz.ready": "Sollumz {version}",
    "sollumz.ready-unknown": "Sollumz",
    "sollumz.missing": "ثبّت Sollumz {version} أو أحدث وفعّله لفتح النماذج وإرسالها.",
    "sollumz.too-old": "إصدار Sollumz هذا قديم جدًا للتصدير إلى Durty Cloth Tool. حدّث إلى Sollumz {version} أو أحدث.",
    "sollumz.tested": "تم اختباره مع Sollumz {version}.",
    "bundle.unreadable": "تعذرت قراءة مجلد التصدير ({detail}).",
    "bundle.not-dictionary": (
        "صدّر Sollumz عنصر drawable أو fragment، وليس drawable dictionary. يحتاج Durty Cloth Tool إلى Drawable "
        "Dictionary: اجعل الـ Drawable الخاص بك تابعًا لواحد (Sollumz: Create Drawable Dictionary) وأرسل مرة أخرى."
    ),
    "bundle.no-model": "لم يصدّر Sollumz أي نموذج. السبب في سجل Info الخاص بـ Sollumz.",
    "bundle.several": "صدّر Sollumz عدة drawable dictionary ({count}). حدد كائنات واحد منها فقط.",
    "bundle.bad-name": (
        "لا يمكن إرسال '{name}': يمكن أن تحتوي أسماء الملفات فقط على أحرف وأرقام و'_' و'-' و'.'، ولا يجوز أن تبدأ بـ '.' "
        "أو تحتوي على '..'، وألا تزيد على 128 حرفًا. أعد تسمية النسيج أو النموذج في Blender."
    ),
    "bundle.duplicate": "يوجد نسيجان باسم '{name}'. امنح كل نسيج اسمًا مختلفًا.",
    "bundle.too-many": "يستخدم النموذج {count} نسيجًا؛ يمكن إرسال {limit} على الأكثر.",
    "bundle.empty-file": "'{name}' فارغ. صدّر النموذج مرة أخرى.",
    "bundle.too-large": "حجم النموذج وأنسجته معًا أكبر من {size} MiB ولا يمكن إرسالها.",
    "bundle.invalid": "لا يمكن إرسال التصدير: {detail}",
    "settings.connection": "الاتصال",
    "settings.account": "الحساب",
    "settings.updates": "التحديثات",
    "settings.privacy": "الخصوصية",
    "settings.models": "النماذج",
    "settings.connect-subtext": (
        "يحتاج إلى Durty Cloth Tool على هذا الحاسوب. يبقى الاتصال على هذا الحاسوب؛ يؤكد gta.clothing تسجيل دخولك لكل "
        "اتصال."
    ),
    "settings.signed-in-as": "تم تسجيل الدخول باسم {name}",
    "settings.not-signed-in": "لم يتم تسجيل الدخول",
    "settings.signed-out": "تم تسجيل الخروج",
    "settings.sign-out-subtext": "ينهي تسجيل الخروج تسجيل دخول هذه الإضافة إلى gta.clothing على هذا الحاسوب.",
    "settings.device-name-subtext": "تعرضه صفحة الموافقة في gta.clothing لتميّز بين حواسيبك.",
    "settings.licence": "GPL-3.0-or-later، Schmid Software Solutions. يصونه DurtyFree (Pleb Masters).",
    "settings.this-version": "هذا الإصدار: {version} ({channel})",
    "settings.diagnostics-copied": (
        "تم نسخ التشخيص. الصقه في خادم Pleb Masters Community Discord عند طلب المساعدة. يحتوي على الإصدارات ورموز "
        "الحالة، دون مسارات ملفات ودون بيانات تسجيل الدخول."
    ),
    "settings.disk-install": (
        "ثُبّتت هذه النسخة من ملف، لذلك لا يمكن لـ Blender تحديثها. للحصول على التحديثات، اسحب رابط التثبيت "
        "من صفحة الإضافات على gta.clothing وأفلته على Blender."
    ),
    "settings.updates-on": "يحدّث Blender هذه الإضافة من مستودع إضافات Durty Cloth Tool.",
    "op.plugins-page": "الحصول على رابط التثبيت",
    "op.plugins-page.desc": "فتح صفحة الإضافات على gta.clothing، حيث تسحب رابط التثبيت إلى Blender",
    "info.channel": (
        "تحصل Experimental على الميزات والإصلاحات الجديدة أولًا وتتغير أكثر. تحصل عليها Release بعد اختبارها. "
        "تختار القناة برابط التثبيت الذي تسحبه إلى Blender."
    ),
    "settings.code-copied": "تم نسخ الرمز.",
    "channel.release": "Release",
    "channel.experimental": "Experimental",
    "info.find": "يتواصل Creator Link فقط مع Durty Cloth Tool على هذا الحاسوب. لا يُرسل شيء عبر الإنترنت سوى تسجيل دخولك.",
    "info.sign-in": (
        "يُظهر تسجيل الدخول لـ Durty Cloth Tool أن هذه الإضافة تخص حسابك. لا ترى الإضافة كلمة مرور Discord أبدًا. يعرض "
        "Durty Cloth Tool هذا التطبيق في {apps}، حيث يمكنك قطع اتصاله."
    ),
    "info.map": (
        "اختر أي خريطة لقطعة الملابس تستبدلها الصورة في المعاينة: منتشرة (لون) أو الاتجاهات أو اللمعان. الصور المنتشرة "
        "بلون sRGB؛ اضبط خرائط الاتجاهات واللمعان على Non-Color."
    ),
    "info.variation": (
        "خرائط الاتجاهات واللمعان تخص النموذج وتشترك فيها كل التنويعات، لذا يمكن فقط للمنتشرة (لون) أن تصبح تنويعة جديدة."
    ),
    "info.live": (
        "تقرأ الإضافة الصورة عند انتهاء كل ضربة فرشاة وترسل ما تغيّر. لا يُحفظ شيء في مشروعك حتى تختار الحفظ في قطعة "
        "الملابس أو الحفظ كتنويعة جديدة."
    ),
    "info.model": (
        "يصدّر إرسال النموذج الـ Drawable Dictionary المحدد من Sollumz بصيغة CodeWalker XML (YDD) مع أنسجته ويعرضه على "
        "قطعة الملابس المرتبطة. يُستورد النموذج المرسل من Durty Cloth Tool ويُربط بقطعة ملابسه ويُرسل مجددًا بعد كل "
        "تغيير. لا يُحفظ شيء حتى تختار حفظ النموذج في قطعة الملابس."
    ),
    "info.open-map": (
        "يفتح خريطة قطعة الملابس هذه من مشروعك كصورة في Blender، مرتبطة بقطعة الملابس، ويبدأ معاينتها المباشرة. يمكن "
        "لـ Durty Cloth Tool إرسال خريطة أيضًا: {edit} في قائمة قطعة الملابس."
    ),
    "info.model-linked": (
        "يتذكر النموذج المفتوح من Durty Cloth Tool قطعة ملابسه، حتى في ملف .blend المحفوظ، لذا يُرسل دائمًا إلى تلك "
        "القطعة. النسخة المصنوعة بالتكرار تحمل الربط أيضًا: ألغِ الربط عن النموذج الذي لا يجب أن يكون مرتبطًا."
    ),
    "info.linked": (
        "تتذكر الصورة المفتوحة من Durty Cloth Tool قطعة ملابسها وخريطتها، حتى في ملف .blend المحفوظ، لذا تذهب معاينتها "
        "المباشرة دائمًا إلى تلك القطعة. ألغِ ربطها في المعاينة المباشرة لاستخدامها مع قطعة الملابس المحددة في Durty "
        "Cloth Tool."
    ),
    "info.checks": (
        "يفحص Durty Cloth Tool الصورة وفق ما تحتاجه GTA V وقطعة الملابس، كما تفعل قائمة الأخطاء فيه. أصلح الأخطاء قبل "
        "الحفظ؛ التحذيرات والملاحظات نصائح."
    ),
    "info.privacy": (
        "يبقى على هذا الحاسوب: صورك ونماذجك وبكسلات المعاينة المباشرة. تذهب إلى Durty Cloth Tool فقط. يذهب إلى "
        "gta.clothing: تسجيل دخولك (مع اسم هذا الحاسوب ما لم توقفه)، وتأكيد لكل اتصال، وتسجيل خروجك، وفحوصات التحديث "
        "في Blender، وبعد موافقتك، شكل قطعة الملابس التي تلائمها هناك."
    ),
    "op.connect": "اتصال",
    "op.connect.desc": "الاتصال بـ Durty Cloth Tool على هذا الحاسوب",
    "op.disconnect": "قطع الاتصال",
    "op.disconnect.desc": "قطع الاتصال بـ Durty Cloth Tool. تتوقف المعاينة المباشرة الجارية",
    "op.sign-in": "تسجيل الدخول",
    "op.sign-in.desc": (
        "تسجيل الدخول بحسابك على gta.clothing (Discord). يطلب منك Durty Cloth Tool الموافقة؛ إذا لم يكن قيد التشغيل، "
        "تحصل على رمز لمتصفحك"
    ),
    "op.sign-in-browser": "تسجيل الدخول في المتصفح",
    "op.sign-in-browser.desc": "تسجيل الدخول بحسابك على gta.clothing (Discord) في صفحة gta.clothing في متصفحك",
    "op.open-sign-in": "فتح صفحة تسجيل الدخول",
    "op.open-sign-in.desc": "فتح صفحة gta.clothing التي توافق على تسجيل الدخول هذا",
    "op.copy-code": "نسخ الرمز",
    "op.copy-code.desc": "نسخ رمز تسجيل الدخول إلى الحافظة",
    "op.cancel-sign-in": "إلغاء",
    "op.cancel-sign-in.desc": "التوقف عن انتظار تسجيل الدخول",
    "op.sign-out": "تسجيل الخروج",
    "op.sign-out.desc": "تسجيل الخروج من gta.clothing في هذه الإضافة وقطع الاتصال",
    "op.update-page": "الحصول على التحديث",
    "op.update-page.desc": "فتح صفحة الإصدارات الحالية من Durty Cloth Tool وإضافاته",
    "op.open-map": "فتح الخريطة",
    "op.open-map.desc": "فتح خريطة قطعة الملابس هذه من مشروعك كصورة مرتبطة بقطعة الملابس وبدء معاينتها المباشرة",
    "op.unlink": "إلغاء الربط",
    "op.unlink.desc": "التوقف عن ربط هذه الصورة بقطعة ملابسها، لتتبع تحديدك في Durty Cloth Tool",
    "op.unlink-model.desc": (
        "التوقف عن ربط هذا الـ Drawable Dictionary بقطعة ملابسه. يذهب إرساله الأول التالي إلى قطعة الملابس المحددة في "
        "Durty Cloth Tool"
    ),
    "op.use-paint-image": "استخدام الصورة المرسومة",
    "op.use-paint-image.desc": "استخدام الصورة التي ترسم عليها، أو الصورة في Image Editor",
    "op.live-start": "بدء المعاينة المباشرة",
    "op.live-start.desc": "عرض هذه الصورة على قطعة الملابس المرتبطة وتحديثها بعد كل ضربة فرشاة. لا يُحفظ شيء حتى تحفظ",
    "op.live-stop": "إيقاف المعاينة المباشرة",
    "op.live-stop.desc": "التوقف عن إرسال الصورة. تبقى التغييرات على الـ ped حتى تتجاهلها أنت أو Durty Cloth Tool",
    "op.live-pause": "إيقاف مؤقت",
    "op.live-pause.desc": "عدم إرسال التغييرات الآن. يواصل الـ ped عرض آخر تحديث",
    "op.live-resume": "استئناف",
    "op.live-resume.desc": "إرسال التغييرات مجددًا، بدءًا بكل ما تغيّر أثناء الإيقاف المؤقت",
    "op.live-send": "إرسال الآن",
    "op.live-send.desc": "إرسال الصورة مجددًا الآن، للتغييرات الناتجة عن السكربتات أو الخَبز أو إعادة التحميل",
    "op.live-save": "الحفظ في قطعة الملابس",
    "op.live-save.desc": "استبدال خريطة قطعة الملابس المرتبطة بهذه الصورة في مشروعك. يمكنك التراجع عنه في السجل",
    "op.live-save-variation": "الحفظ كتنويعة جديدة",
    "op.live-save-variation.desc": "إضافة هذه الصورة إلى قطعة الملابس المرتبطة كتنويعة نسيج جديدة (المنتشرة (لون) فقط)",
    "op.live-discard": "تجاهل التغييرات",
    "op.live-discard.desc": "إزالة التغييرات المعروضة على الـ ped والإيقاف. يحتفظ مشروعك بالنسيج المحفوظ",
    "op.check-again": "الفحص مرة أخرى",
    "op.check-again.desc": "طلب أن يفحص Durty Cloth Tool الصورة مرة أخرى",
    "op.model-push": "إرسال النموذج",
    "op.model-push.desc": (
        "تصدير الـ Drawable Dictionary المحدد من Sollumz وعرضه على قطعة الملابس المرتبطة. لا يُحفظ شيء حتى تحفظ"
    ),
    "op.model-save": "حفظ النموذج في قطعة الملابس",
    "op.model-save.desc": "حفظ النموذج المرسل في مشروعك. يبقى النموذج السابق في سجل قطعة الملابس",
    "op.model-discard": "تجاهل",
    "op.model-discard.desc": "إزالة النموذج المرسل من الـ ped. يحتفظ مشروعك بالنموذج المحفوظ",
    "op.diagnostics": "نسخ التشخيص",
    "op.diagnostics.desc": "نسخ الإصدارات ورموز الحالة للدعم (دون مسارات ملفات ودون بيانات تسجيل الدخول)",
    "op.help": "مساعدة",
    "op.help.desc": "فتح وثائق Durty Cloth Tool",
    "op.community": "Pleb Masters Community Discord",
    "op.community.desc": "فتح خادم Pleb Masters Community Discord، حيث يمكنك طلب المساعدة",
    "op.info": "مزيد من المعلومات",
    "op.about": "حول",
    "op.about.desc": "إصدار الإضافة وترخيصها، وما ترسله وإلى أين",
    "about.title": "Durty Cloth Tool Link {version} ({channel})",
    "op.join-discord": "الانضمام إلى خادم Discord",
    "op.join-discord.desc": "فتح دعوة خادم Pleb Masters Community Discord في متصفحك",
    "prop.image": "الصورة",
    "prop.image.desc": "الصورة المعروضة على قطعة الملابس المرتبطة",
    "prop.map": "الخريطة",
    "prop.map.desc": "أي خريطة لقطعة الملابس المرتبطة تستبدلها الصورة في المعاينة",
    "prop.auto-push": "إرسال تلقائي",
    "prop.auto-push.desc": "إرسال النموذج مرة أخرى بعد لحظة من توقفك عن التعديل (بعد الإرسال الأول)",
    "prop.auto-connect": "اتصال تلقائي",
    "prop.auto-connect.desc": "البحث عن Durty Cloth Tool على هذا الحاسوب عند بدء Blender",
    "prop.device-name": "إظهار اسم هذا الحاسوب عند تسجيل الدخول",
    "prop.device-name.desc": "إرسال اسم هذا الحاسوب مع تسجيل الدخول، لتعرض صفحة الموافقة في gta.clothing أي حاسوب يطلب",
    "prop.delay": "مهلة الإرسال التلقائي",
    "prop.delay.desc": "عدد الثواني التي يجب أن يبقى فيها النموذج المرسل دون تغيير قبل أن يرسله الإرسال التلقائي مرة أخرى",
    "notice.signed-in": "تم تسجيل الدخول باسم {name}.",
    "notice.signing-out": "جارٍ تسجيل الخروج…",
    "notice.signed-out": "تم تسجيل الخروج.",
    "notice.signed-out-local": (
        "تم تسجيل الخروج على هذا الحاسوب. اسمح بالوصول إلى الإنترنت في تفضيلات Blender لإنهاء الجلسة على gta.clothing أيضًا."
    ),
    "notice.signed-out-unreached": (
        "تم تسجيل الخروج على هذا الحاسوب؛ تعذر الوصول إلى gta.clothing. تنتهي الجلسة هناك تلقائيًا، أو أنهِها من صفحة "
        "حسابك."
    ),
    "notice.browser-opens": "سيفتح متصفحك صفحة تسجيل الدخول بعد لحظة.",
    "notice.no-sign-in": "لا يوجد تسجيل دخول قيد الانتظار.",
    "notice.not-gta-clothing": "رابط تسجيل الدخول ليس رابطًا من gta.clothing.",
    "notice.unexpected": "واجهت الإضافة مشكلة غير متوقعة: {detail}",
    "notice.secrets-unreadable": "تعذرت قراءة تسجيل الدخول المحفوظ ({detail}). سجّل الدخول مرة أخرى.",
    "notice.secret-store": "تعذرت قراءة أو كتابة تسجيل الدخول المحمي. سجّل الدخول مرة أخرى.",
    "notice.file-error": "تعذرت قراءة ملف أو كتابته: {detail}",
    "notice.not-ready": "الإضافة ليست جاهزة.",
    "notice.connect-first": "اتصل بـ Durty Cloth Tool أولًا.",
    "notice.select-cloth": "حدد قطعة ملابس في Durty Cloth Tool أولًا.",
    "notice.start-live-first": "ابدأ المعاينة المباشرة أولًا.",
    "notice.wait-saving": "انتظر حتى ينتهي الحفظ.",
    "notice.diffuse-only": "يمكن فقط للمنتشرة (لون) أن تصبح تنويعة جديدة.",
    "notice.pushing": "هناك إرسال جارٍ.",
    "notice.online-off": "الوصول إلى الإنترنت في Blender متوقف.",
    "error.generic": "حدث خطأ ما.",
    "error.generic-code": "حدث خطأ ما ({code}).",
    "error.malformed-message": "لم يفهم Durty Cloth Tool وهذه الإضافة بعضهما. حدّث كليهما، ثم حاول مرة أخرى.",
    "error.invalid-message": "لم يفهم Durty Cloth Tool وهذه الإضافة بعضهما. حدّث كليهما، ثم حاول مرة أخرى.",
    "error.unknown-message-type": "لا يعرف Durty Cloth Tool هذا الطلب. حدّث Durty Cloth Tool.",
    "error.unexpected-message": "لم يتوقع Durty Cloth Tool هذا الطلب الآن. حاول مرة أخرى.",
    "error.message-too-large": "الصورة أو النموذج أكبر من أن يُرسل.",
    "error.unsupported-protocol": "تستخدم هذه الإضافة وDurty Cloth Tool إصدارات ربط مختلفة. حدّث كليهما.",
    "error.plugin-too-old": "هذه الإضافة قديمة جدًا بالنسبة إلى Durty Cloth Tool لديك. حدّث الإضافة.",
    "error.dct-too-old": "Durty Cloth Tool هذا أقدم من هذه الإضافة. حدّث Durty Cloth Tool، ثم اختر اتصال.",
    "error.not-authenticated": "سجّل الدخول أولًا.",
    "error.authentication-failed": "لم يقبل Durty Cloth Tool تسجيل الدخول. جارٍ المحاولة مرة أخرى…",
    "error.untrusted-endpoint": (
        "أجاب برنامج ليس Durty Cloth Tool الخاص بك، لذلك لم يُرسل شيء. تواصل الإضافة البحث عن Durty Cloth Tool."
    ),
    "error.account-mismatch": (
        "Durty Cloth Tool مسجّل الدخول بحساب آخر. سجّل الخروج هنا وسجّل الدخول بالحساب الذي يستخدمه Durty Cloth Tool."
    ),
    "error.dct-signed-out": "Durty Cloth Tool غير مسجّل الدخول. سجّل الدخول في Durty Cloth Tool؛ ستتصل الإضافة تلقائيًا.",
    "error.token-invalid": "انتهت صلاحية تسجيل الدخول. جارٍ تسجيل الدخول مجددًا…",
    "error.needs-license": "يتطلب هذا ترخيص Durty Cloth Tool.",
    "error.needs-ultimate": "هذا مضمّن في Durty Cloth Tool Ultimate.",
    "error.no-project": "افتح مشروعًا في Durty Cloth Tool أولًا.",
    "error.no-focused-item": "حدد قطعة ملابس في Durty Cloth Tool أولًا.",
    "error.binding-in-use": "يعمل تطبيق آخر بالفعل على هذا النسيج أو النموذج.",
    "error.binding-not-found": "لم تعد قطعة الملابس أو النسيج موجودة في Durty Cloth Tool.",
    "error.lease-not-found": "أنهى Durty Cloth Tool هذه المعاينة. ابدأها مرة أخرى.",
    "error.lease-limit": "توجد معاينات مباشرة مفتوحة كثيرة جدًا. أوقف واحدة أولًا.",
    "error.budget-exceeded": "امتلأت ذاكرة المعاينة المباشرة في Durty Cloth Tool. أوقف معاينة مباشرة أخرى.",
    "error.frame-out-of-bounds": "لم يتسع تحديث الصورة داخل النسيج.",
    "error.frame-size-mismatch": "تعذر إرسال الصورة.",
    "error.unsupported-format": "لا يقبل Durty Cloth Tool هذه الصيغة هنا. أرسل النماذج بصيغة YDD XML من Sollumz.",
    "error.stale-revision": "كانت بكسلات أحدث لا تزال في الطريق. احفظ مرة أخرى.",
    "error.item-refused": "لا يستطيع Durty Cloth Tool تعديل هذا العنصر (dummy أو مقفل أو محمي).",
    "error.game-required": "يحتاج Durty Cloth Tool إلى تثبيت GTA V لديك لهذا. اضبطه في Durty Cloth Tool.",
    "error.save-failed": "تعذر على Durty Cloth Tool الحفظ. التفاصيل في شريط الحالة لديه.",
    "error.busy": "Durty Cloth Tool مشغول. حاول مرة أخرى بعد لحظة.",
    "error.rate-limited": "طلبات كثيرة جدًا. انتظر لحظة وحاول مرة أخرى.",
    "error.connection-limit": "تطبيقات كثيرة جدًا متصلة بـ Durty Cloth Tool.",
    "error.request-denied": "رفض Durty Cloth Tool الطلب.",
    "error.model-rejected": "تعذر على Durty Cloth Tool استخدام هذا النموذج. افحصه في Sollumz وأرسل مرة أخرى.",
    "error.internal-error": "حدث خطأ ما. حاول مرة أخرى، وأعد تشغيل Blender وDurty Cloth Tool إذا تكرر ذلك.",
    "error.disconnected": "انقطع الاتصال بـ Durty Cloth Tool.",
    "error.timeout": "لم يرد Durty Cloth Tool في الوقت المناسب.",
    "error.superseded": "استبدل طلب أحدث هذا الطلب.",
    "error.cancelled": "تم الإلغاء.",
    "error.closed": "المعاينة المباشرة مغلقة.",
    "error.signed-out": "لقد سجّلت الخروج. سجّل الدخول لاستخدام Creator Link مرة أخرى.",
    "error.assertion-invalid": "تعذر تأكيد تسجيل الدخول. جارٍ المحاولة مرة أخرى…",
    "error.pixel-source-failed": "تعذرت قراءة الصورة للمعاينة المباشرة. جارٍ المحاولة مرة أخرى…",
    "error.callback-failed": "حدث خطأ ما في الإضافة. حاول مرة أخرى.",
    "error.offline": (
        "الوصول إلى الإنترنت في Blender متوقف. اسمح به من التفضيلات > النظام > الشبكة لتسجيل الدخول والاتصال."
    ),
    "error.network": "تعذر الوصول إلى gta.clothing. تحقق من الاتصال بالإنترنت.",
    "error.invalid-response": "أرسل gta.clothing ردًا غير متوقع. حاول مرة أخرى لاحقًا.",
    "error.tls": "فشل الاتصال الآمن بـ gta.clothing. تحقق من الشبكة أو الوكيل أو إعدادات مكافح الفيروسات.",
    "error.account_locked": "حسابك على gta.clothing مقفل.",
    "error.discord_membership_required": "يتطلب Creator Link أن يكون حسابك على Discord عضوًا في خادم Pleb Masters Community Discord.",
    "error.discord_unavailable": "تسجيل الدخول عبر Discord غير متاح الآن. حاول مرة أخرى لاحقًا.",
    "error.plugin_update_required": "يتطلب gta.clothing إصدارًا أحدث من هذه الإضافة. حدّثها.",
    "error.expired_token": "انتهت صلاحية رمز تسجيل الدخول. سجّل الدخول مرة أخرى.",
    "error.access_denied": "تم رفض تسجيل الدخول.",
    "error.invalid_grant": "لم يُقبل تسجيل الدخول. سجّل الدخول مرة أخرى.",
    "error.session_invalid": "لم يعد تسجيل الدخول صالحًا. سجّل الدخول مرة أخرى.",
    "error.session_expired": "انتهت صلاحية تسجيل الدخول. سجّل الدخول مرة أخرى.",
    "error.session_revoked": "تم إنهاء تسجيل الدخول على gta.clothing. سجّل الدخول مرة أخرى.",
    "error.refresh_in_progress": "برنامج آخر يجدد تسجيل دخولك. حاول مرة أخرى بعد لحظة.",
    "close.closed": "توقفت المعاينة المباشرة.",
    "close.replaced": "تولى تطبيق آخر هذا النسيج.",
    "close.itemRemoved": "تمت إزالة قطعة الملابس في Durty Cloth Tool.",
    "close.projectClosed": "تم إغلاق المشروع في Durty Cloth Tool.",
    "close.entitlementLost": "لم تعد خطتك تتضمن هذه الميزة.",
    "close.signedOut": "سجّل Durty Cloth Tool الخروج، لذلك انتهت المعاينة.",
    "close.disconnected": "انقطع الاتصال بـ Durty Cloth Tool.",
    "feature.needsLicense": "يتطلب هذا ترخيص Durty Cloth Tool.",
    "feature.needsUltimate": "هذا مضمّن في Durty Cloth Tool Ultimate.",
    "feature.unavailable": "هذا غير مضمّن في خطة Durty Cloth Tool الخاصة بك.",
}
