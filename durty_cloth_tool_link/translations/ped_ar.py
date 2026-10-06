# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2026 Schmid Software Solutions (https://schmid-software.de)
"""Arabic (العربية): the Custom Ped texts. Translated, not mirrored."""

TEXT = {
    "workspace.prop": "العمل على",
    "workspace.prop.desc": "ما تعرضه علامة التبويب DCT: أدوات الملابس أو أدوات الـ ped المخصص",
    "workspace.clothing": "الملابس",
    "workspace.clothing.desc": "قطعة الملابس المرتبطة في Durty Cloth Tool ومعاينتها المباشرة ونموذجها، وملاءمة الملابس",
    "workspace.ped": "ped مخصص",
    "workspace.ped.desc": "تحويل شخصيتك الخاصة إلى ped مخصص لـ Durty Cloth Tool",
    "ped.panel": "ped مخصص (تجريبي)",
    "ped.stage-title": "{number}. {title}",
    "ped.section.character": "الشخصية",
    "ped.section.markers": "العلامات",
    "ped.section.rig": "التجهيز بالعظام",
    "ped.section.check": "الفحص",
    "ped.section.send": "الإرسال",
    "ped.status.none": "لا شيء بعد",
    "ped.status.vertices": "الرؤوس: {count}",
    "ped.status.rigging": "جارٍ التجهيز بالعظام",
    "ped.status.waiting": "بانتظارك",
    "ped.status.ready": "جاهز",
    "ped.status.review": "يحتاج إلى مراجعة",
    "ped.status.not-rigged": "غير مُجهَّز بالعظام",
    "ped.status.not-checked": "لم يُفحص",
    "ped.status.no-problems": "لا مشكلات",
    "ped.status.problems": "الملاحظات: {count}",
    "ped.status.sent": "تم الإنشاء",
    "ped.status.sending": "جارٍ الإرسال",
    "ped.status.not-sent": "لم يُرسل",
    "ped.privacy": (
        "يجري التجهيز بالعظام وإنشاء الـ ped في Durty Cloth Tool على هذا الحاسوب، من ملفات GTA V الخاصة بك. لا يذهب أي "
        "شيء من شخصيتك إلى gta.clothing."
    ),
    "ped.heading.more": "مزيد من الخيارات",
    "ped.next.character": "حدد شبكات شخصيتك في العرض ثلاثي الأبعاد واختر استخدام المحدد.",
    "ped.next.fix": "التالي: أصلح ما تذكره الفحوصات في قسم الشخصية.",
    "ped.next.markers": "التالي: ضع العلامات في قسم العلامات. يُظهر دليل النقر كل نقطة.",
    "ped.next.marker-problems": "التالي: أصلح العلامات التي تذكرها القائمة في قسم العلامات.",
    "ped.next.connect": "التالي: اتصل بـ Durty Cloth Tool (في الأعلى). لا حاجة إلى فتح أي مشروع.",
    "ped.next.template": "التالي: اختر قالبًا في قسم التجهيز بالعظام.",
    "ped.next.rig": "التالي: التجهيز بالعظام في Durty Cloth Tool في قسم التجهيز بالعظام.",
    "ped.next.rigging": "يجهّز Durty Cloth Tool شخصيتك بالعظام. يبقى Blender قابلًا للاستخدام في الأثناء.",
    "ped.next.approve": (
        "التالي: تحقق من المواضع التي نقل إليها Durty Cloth Tool العلامات (بالأصفر)، ثم اختر تطبيق التجهيز العظمي."
    ),
    "ped.next.check": "التالي: جرّب وضعيات الاختبار واختر تشغيل الفحوصات في قسم الفحص.",
    "ped.next.send": "التالي: إنشاء ped مخصص في قسم الإرسال.",
    "ped.next.sending": "بانتظارك في Durty Cloth Tool: اختر هناك مكان إنشاء المشروع.",
    "ped.next.done": "تم: أنشأ Durty Cloth Tool المشروع {name}. ابنِه هناك.",
    "ped.next.done-before": "تم: أنشأ Durty Cloth Tool مشروعًا من هذه الشخصية. ابنِه هناك.",
    "ped.character.none": (
        "حدد كل شبكات شخصيتك (الجسم والرأس والشعر والعينين) في العرض ثلاثي الأبعاد، ثم اختر استخدام المحدد."
    ),
    "ped.character.facts": "الكائنات: {objects}، الرؤوس: {vertices}، المثلثات: {triangles}، المواد: {materials}",
    "ped.prop.character": "الشخصية",
    "ped.prop.character.desc": "المجموعة (Collection) التي تحتوي على شبكات شخصيتك",
    "ped.op.use-selected": "استخدام المحدد",
    "ped.op.use-selected.desc": "استخدام الشبكات المحددة كشخصيتك. إن لم تكن في مجموعة خاصة بها، تُنقل إلى مجموعة جديدة",
    "ped.done.use-selected": "{name} هي شخصيتك (الشبكات: {count}).",
    "ped.check.none": "لا تحتوي الشخصية على أي شبكة.",
    "ped.check.rigged": (
        "الشخصية مُجهَّزة بالعظام. استخدم إزالة التجهيز العظمي في قسم التجهيز بالعظام لتغيير شكلها أو حجمها."
    ),
    "ped.check.rigged-changed": (
        "حُرّك جزء أو أُضيف إليه مُعدِّل بعد التجهيز بالعظام. تراجع عن ذلك، أو أزل التجهيز العظمي وأعد التجهيز بالعظام."
    ),
    "ped.check.transforms": (
        "عدد الشبكات المحرّكة أو المُدارة أو المغيّر حجمها: {count}. طبّق تحويلاتها لتحتفظ الشخصية بشكلها."
    ),
    "ped.check.modifiers": (
        "عدد الشبكات التي تحمل مُعدِّلات ({names}): {count}. طبّقها ليرى التجهيز بالعظام ما تراه أنت."
    ),
    "ped.check.old-rig": (
        "الشخصية مُجهَّزة على {name}. أزل التجهيز العظمي القديم: تحتفظ الشخصية بوضعيتها، ويظل بإمكان من التجهيز القديم "
        "وضع العلامات على مفاصله."
    ),
    "ped.check.shape-keys": (
        "عدد الشبكات التي تحمل مفاتيح شكل (Shape Keys): {count}، وهي لا تتبع التجهيز العظمي. أزلها لتحتفظ بالشكل الذي "
        "تراه."
    ),
    "ped.check.lying": "تبدو الشخصية مستلقية (طولها أفقيًا أكبر من ارتفاعها). هل تريد إيقافها مستقيمة؟",
    "ped.check.upside-down": "تبدو الشخصية واقفة على رأسها. هل تريد قلبها؟",
    "ped.check.unit": (
        "ارتفاع الشخصية {height} وحدة، لذا هي على الأرجح بوحدة {unit}. هل تريد تغيير حجمها إلى {metres} m؟"
    ),
    "ped.check.too-tall": "ارتفاع الشخصية {height} m. يجب أن تقع ضمن 3 m من نقطة الأصل: غيّر حجمها.",
    "ped.check.height-unusual": (
        "ارتفاع الشخصية {height} m. يبلغ ارتفاع الـ ped في GTA V نحو 1.8 m: قد تتحرك الشخصيات الأصغر أو الأطول كثيرًا "
        "وتصطدم بشكل غريب في اللعبة."
    ),
    "ped.check.height": "الارتفاع: {height} m",
    "ped.check.origin": "تقف الشخصية على بعد {distance} m من نقطة الأصل. انقلها إلى نقطة الأصل.",
    "ped.check.facing": "يجب أن تتجه شخصيتك نحو العرض الأمامي (Numpad 1)، وجانبها الأيسر على يمينك. هل هي كذلك؟",
    "ped.check.facing-other": (
        "تبدو القدمان متجهتين {direction}. يجب أن تتجه شخصيتك نحو العرض الأمامي (Numpad 1). أدرها، أو أكّد أنها متجهة "
        "إلى الأمام."
    ),
    "ped.check.facing-done": "متجهة إلى الأمام",
    "ped.check.size-limit": (
        "في الشخصية {vertices} رأس و{triangles} مثلث؛ يقبل التجهيز بالعظام {max_vertices} رأس و{max_triangles} مثلث "
        "على الأكثر. قلّل تفاصيل نسخة من الشخصية أولًا، مثلًا بمعدِّل Decimate."
    ),
    "ped.check.size-budget": (
        "الرؤوس: {vertices}. يجب ألا يحمل الـ ped أكثر من {budget} في مستوى تفاصيله الأعلى، لذا سينبّه Durty Cloth "
        "Tool إلى ذلك. لكنه يعمل مع ذلك."
    ),
    "ped.check.size": "الرؤوس: {vertices}، عدد مناسب لـ ped",
    "ped.unit.cm": "السنتيمتر",
    "ped.unit.mm": "المليمتر",
    "ped.unit.in": "البوصة",
    "ped.direction.back": "إلى الخلف",
    "ped.direction.screen-right": "إلى يمينك",
    "ped.direction.screen-left": "إلى يسارك",
    "ped.op.apply-transforms": "تطبيق التحويلات",
    "ped.op.apply-transforms.desc": "دمج موضع كل شبكة ودورانها وحجمها فيها، مع الحفاظ على مظهرها",
    "ped.done.transforms": "تم تطبيق التحويلات على الشبكات: {count}.",
    "ped.op.apply-modifiers": "تطبيق المُعدِّلات",
    "ped.op.apply-modifiers.desc": "تطبيق كل مُعدِّلات شبكات الشخصية (باستثناء Armature)",
    "ped.confirm.modifiers": "هل تريد تطبيق كل مُعدِّلات شبكات الشخصية؟ تضيع إعداداتها بعد ذلك.",
    "ped.done.modifiers": "تم تطبيق المُعدِّلات: {count}.",
    "ped.op.remove-old-rig": "إزالة التجهيز القديم",
    "ped.op.remove-old-rig.desc": (
        "فصل الشخصية عن الهيكل العظمي (Armature) الذي جاءت معه: تحتفظ بوضعيتها الحالية، ويبقى الهيكل العظمي مخفيًا"
    ),
    "ped.confirm.old-rig": (
        "هل تريد إزالة التجهيز العظمي القديم؟ تحتفظ الشخصية بوضعيتها الحالية وتفقد مجموعات الرؤوس الخاصة بالتجهيز "
        "القديم. يبقى الهيكل العظمي القديم في الملف، مخفيًا."
    ),
    "ped.done.old-rig": "تمت إزالة التجهيز العظمي القديم ({name}). لا يزال بإمكان من التجهيز القديم استخدام مفاصله.",
    "ped.op.remove-shape-keys": "إزالة مفاتيح الشكل",
    "ped.op.remove-shape-keys.desc": "إزالة مفاتيح الشكل من شبكات الشخصية، مع الإبقاء على الشكل الذي تعرضه",
    "ped.confirm.shape-keys": "هل تريد إزالة كل مفاتيح الشكل من الشخصية؟ يبقى الشكل الذي تراه الآن.",
    "ped.done.shape-keys": "تمت إزالة مفاتيح الشكل من الشبكات: {count}.",
    "ped.op.scale": "تغيير الحجم",
    "ped.op.scale.desc": "تغيير حجم الشخصية حول نقطة الأصل، كما يفعل تغيير الوحدات",
    "ped.op.scale-by": "تغيير الحجم بمعامل {factor}",
    "ped.confirm.scale": "هل تريد تغيير حجم الشخصية بمعامل {factor}؟",
    "ped.done.scaled": "تم تغيير حجم الشخصية بمعامل {factor}.",
    "ped.op.turn": "تدوير",
    "ped.op.turn.desc": "تدوير الشخصية بخطوات من 90 درجة",
    "ped.op.stand-up": "إيقاف مستقيمًا",
    "ped.op.stand-up-other": "إيقاف مستقيمًا بالاتجاه الآخر",
    "ped.op.turn-over": "قلب",
    "ped.op.turn-left": "تدوير 90° إلى اليسار",
    "ped.op.turn-right": "تدوير 90° إلى اليمين",
    "ped.op.turn-around": "تدوير 180°",
    "ped.confirm.turn": "هل تريد تدوير الشخصية؟ يمكنك التراجع عن ذلك باستخدام Ctrl+Z.",
    "ped.done.turned": "تم تدوير الشخصية.",
    "ped.op.to-origin": "النقل إلى نقطة الأصل",
    "ped.op.to-origin.desc": "نقل الشخصية لتقف على الأرض عند نقطة الأصل",
    "ped.done.origin": "تقف الشخصية عند نقطة الأصل الآن.",
    "ped.op.confirm-facing": "إنها متجهة إلى الأمام",
    "ped.op.confirm-facing.desc": "تأكيد أن الشخصية تتجه نحو العرض الأمامي، وجانبها الأيسر على يمينك",
    "ped.confirm.facing": "هل تواجهك الشخصية في العرض الأمامي (Numpad 1)، ويدها اليسرى على يمينك؟",
    "ped.heading.parts": "الأجزاء ({count})",
    "ped.parts.subtext": (
        "يُعطى الشعر والعينان والأسنان أوزانًا بطريقة مختلفة، ويصبح الشعر شعر الـ ped. غيّر الدور عندما يكون التخمين "
        "خاطئًا."
    ),
    "ped.parts.guess": "التخمين: {role}",
    "ped.prop.role": "دور الجزء",
    "ped.prop.role.desc": "ما هي هذه الشبكة: يحدد كيف تُعطى أوزانها وأين تذهب في الـ ped",
    "ped.role.auto": "تلقائي",
    "ped.role.auto.desc": "تخمين الدور من اسم الشبكة وأسماء موادها",
    "ped.role.body": "الجسم",
    "ped.role.body.desc": "البشرة والملابس التي تتحرك مع الجسم",
    "ped.role.head": "الرأس والوجه",
    "ped.role.head.desc": "الرأس والوجه والحاجبان والرموش",
    "ped.role.hair": "الشعر",
    "ped.role.hair.desc": "الشعر وبطاقات اللحية وغيرها من الشعر الذي يتحرك مع الرأس",
    "ped.role.eyes": "العينان",
    "ped.role.eyes.desc": "مقلتا العينين، تحركهما عظام العينين أو الرأس",
    "ped.role.teeth": "الأسنان",
    "ped.role.teeth.desc": "الأسنان واللسان، يحركها الرأس",
    "ped.role.accessory": "إكسسوار",
    "ped.role.accessory.desc": "النظارات والمجوهرات وغيرها مما ترتديه الشخصية",
    "ped.heading.markers": "علامات المفاصل",
    "info.ped-markers": (
        "تُري العلامات Durty Cloth Tool أين تقع مفاصل شخصيتك: داخل الجسم، في منتصف كل مفصل. العلامات اليسرى زرقاء "
        "واليمنى برتقالية، ويسار الشخصية على يمينك في العرض الأمامي."
    ),
    "ped.markers.placed": "الموضوعة: {placed} من {total}",
    "ped.op.guide": "دليل النقر",
    "ped.op.guide.desc": (
        "النقر على النقاط التي يعرضها شكل توضيحي في العرض ثلاثي الأبعاد، واحدة تلو الأخرى؛ وتوضع العلامات الأخرى بناءً "
        "عليها"
    ),
    "ped.op.auto-markers": "علامات تلقائية",
    "ped.op.auto-markers.desc": "وضع كل العلامات من شكل الشخصية. تحقق منها بعد ذلك",
    "ped.op.from-rig": "من التجهيز القديم",
    "ped.op.from-rig.desc": (
        "وضع العلامات على مفاصل التجهيز العظمي القديم للشخصية (Mixamo أو Unreal أو Rigify أو Character Creator أو VRM)"
    ),
    "ped.op.mirror": "عكس",
    "ped.op.mirror.desc": "نسخ علامات أحد الجانبين إلى الآخر، معكوسة حول منتصف الشخصية",
    "ped.op.mirror-left": "اليسار إلى اليمين",
    "ped.op.mirror-right": "اليمين إلى اليسار",
    "ped.op.show": "إظهار",
    "ped.op.show-markers.desc": "تحديد هذه العلامات في العرض ثلاثي الأبعاد",
    "ped.prop.marker-size": "حجم العلامات",
    "ped.prop.marker-size.desc": "حجم كرات العلامات المرسومة",
    "ped.prop.follow": "تحريك المرفقين والركبتين معها",
    "ped.prop.follow.desc": "عندما تحرّك علامة رسغ أو كتف أو كاحل أو ورك، يتحرك المرفق أو الركبة بينهما مع الطرف",
    "ped.done.auto-markers": "وُضعت العلامات من شكل الشخصية. تحقق من كل علامة وحرّك أي علامة في غير موضعها.",
    "ped.done.from-rig": "وُضعت العلامات على مفاصل تجهيز {rig} العظمي. تحقق من الذقن وقمة الرأس.",
    "ped.done.mirrored": "تم عكس العلامات.",
    "ped.rig-kind.mixamo": "Mixamo",
    "ped.rig-kind.unreal": "Unreal",
    "ped.rig-kind.rigify": "Rigify",
    "ped.rig-kind.cc": "Character Creator",
    "ped.rig-kind.vrm": "VRM",
    "ped.marker-error.too-small": "الشخصية صغيرة جدًا أو ليست واقفة: لم تعثر علامات تلقائية على أي شخص.",
    "ped.marker-error.guide-incomplete": "يحتاج دليل النقر إلى كل نقاطه قبل أن يتمكن من وضع العلامات الأخرى.",
    "ped.marker-error.no-rig": (
        "لا تملك الشخصية تجهيزًا عظميًا قديمًا بأسماء عظام معروفة (Mixamo أو Unreal أو Rigify أو Character Creator أو "
        "VRM)."
    ),
    "ped.marker-note.arms": "تعذّر تمييز الذراعين عن الجسم: تحقق من الكتفين والمرفقين والرسغين.",
    "ped.marker-note.legs": "تعذّر التمييز بين الساقين: تحقق من الوركين والركبتين والكاحلين.",
    "ped.marker-note.neck": "صعُب العثور على الرقبة: تحقق من الرقبة والذقن والصدر.",
    "ped.marker-problem.missing": "علامات ناقصة: {names}.",
    "ped.marker-problem.side": "في الجانب الخطأ: {names}. يجب أن يكون يسار الشخصية عند +X، على يمينك في العرض الأمامي.",
    "ped.marker-problem.order": "ليست مرتبة من الرأس إلى الأسفل: {names}.",
    "ped.marker-problem.asymmetric": "تختلف الأطراف اليسرى واليمنى بأكثر من 30 %: {names}.",
    "ped.marker-problem.outside": "خارج الشخصية: {names}.",
    "ped.marker.headTop": "قمة الرأس",
    "ped.marker.chin": "الذقن",
    "ped.marker.neck": "الرقبة",
    "ped.marker.chest": "الصدر",
    "ped.marker.pelvis": "الحوض",
    "ped.marker.shoulderL": "الكتف الأيسر",
    "ped.marker.shoulderR": "الكتف الأيمن",
    "ped.marker.elbowL": "المرفق الأيسر",
    "ped.marker.elbowR": "المرفق الأيمن",
    "ped.marker.wristL": "الرسغ الأيسر",
    "ped.marker.wristR": "الرسغ الأيمن",
    "ped.marker.hipL": "الورك الأيسر",
    "ped.marker.hipR": "الورك الأيمن",
    "ped.marker.kneeL": "الركبة اليسرى",
    "ped.marker.kneeR": "الركبة اليمنى",
    "ped.marker.ankleL": "الكاحل الأيسر",
    "ped.marker.ankleR": "الكاحل الأيمن",
    "ped.marker.toeL": "أصابع القدم اليسرى",
    "ped.marker.toeR": "أصابع القدم اليمنى",
    "ped.guide.title": "دليل النقر: النقطة {index} من {total}",
    "ped.guide.keys": "نقرة: وضع النقطة. نقرة يمنى: الرجوع نقطة واحدة. عجلة الفأرة والزر الأوسط: العرض. Esc: الإيقاف.",
    "ped.guide.headTop": "انقر على قمة الرأس.",
    "ped.guide.chin": "انقر على طرف الذقن.",
    "ped.guide.shoulderL": "انقر على مفصل الكتف الأيسر (على يمينك في العرض الأمامي).",
    "ped.guide.shoulderR": "انقر على مفصل الكتف الأيمن (على يسارك).",
    "ped.guide.wristL": "انقر على منتصف الرسغ الأيسر.",
    "ped.guide.wristR": "انقر على منتصف الرسغ الأيمن.",
    "ped.guide.hipL": "انقر على مفصل الورك الأيسر، حيث تلتقي الساق بالجسم.",
    "ped.guide.hipR": "انقر على مفصل الورك الأيمن.",
    "ped.guide.ankleL": "انقر على منتصف الكاحل الأيسر.",
    "ped.guide.ankleR": "انقر على منتصف الكاحل الأيمن.",
    "ped.guide.toeL": "انقر على القدم اليسرى حيث تنثني أصابعها.",
    "ped.guide.toeR": "انقر على القدم اليمنى حيث تنثني أصابعها.",
    "ped.guide.finish": "وُضعت كل النقاط. اضغط Enter.",
    "ped.guide.missed": "لم تُصب تلك النقرة الشخصية. انقر عليها.",
    "ped.guide.done": (
        "وُضعت كل النقاط؛ ووُضعت الرقبة والصدر والحوض والمرفقان والركبتان بناءً عليها. تحقق منها وحرّك أي علامة في غير "
        "موضعها."
    ),
    "ped.heading.template": "القالب",
    "info.ped-template": (
        "الـ ped المثبّت في GTA V الذي يُبنى منه الـ ped الخاص بك: هيكله العظمي وحركته وصوته وأشكال جسمه. اختر واحدًا "
        "يشبه شخصيتك: من الجنس نفسه وببنية مشابهة."
    ),
    "ped.prop.template": "القالب",
    "ped.prop.template.desc": "الـ ped المثبّت الذي تحصل شخصيتك على هيكله العظمي",
    "ped.prop.gender": "الجنس",
    "ped.gender.any": "الكل",
    "ped.gender.any.desc": "عرض قوالب الجنسين كليهما",
    "ped.gender.male.desc": "عرض قوالب الذكور",
    "ped.gender.female.desc": "عرض قوالب الإناث",
    "ped.prop.show-all": "إظهار الكل",
    "ped.prop.show-all.desc": "عرض شخصيات ped من freemode واللاعب والمشاهد السينمائية والقصة أيضًا، لا العابرة فقط",
    "ped.template.choose": "اختيار قالب",
    "ped.template.recommended": "{model} (موصى به)",
    "ped.template.facts": "{facts}",
    "ped.templates.loading": "يقرأ Durty Cloth Tool ملفات لعبتك (بضع ثوانٍ في المرة الأولى).",
    "ped.templates.refresh": "اختر تحديث لعرض القوالب المثبّتة مع لعبتك.",
    "ped.templates.none": "لا يطابق أي قالب. فعّل إظهار الكل أو اختر جنسًا آخر.",
    "ped.templates.truncated": "يعرض Durty Cloth Tool أول {count}. اختر جنسًا لرؤية غيرها.",
    "ped.group.ambient": "عابر",
    "ped.group.freemode": "freemode",
    "ped.group.player": "لاعب",
    "ped.group.cutscene": "مشهد سينمائي",
    "ped.group.story": "قصة",
    "ped.layout.packed": "مدمج",
    "ped.layout.streamed": "متدفق",
    "ped.op.refresh": "تحديث",
    "ped.op.refresh.desc": "طلب القوالب المثبّتة مع لعبتك من Durty Cloth Tool مرة أخرى",
    "ped.op.use-template": "استخدام القالب",
    "ped.op.use-template.desc": "استخدام هذا الـ ped المثبّت كقالب",
    "ped.op.use-template-named": "استخدام {template}",
    "ped.rights.title": "حقوقك في هذه الشخصية",
    "ped.rights.text": (
        "لا تحوّل إلا الشخصيات التي صنعتها بنفسك أو لديك إذن باستخدامها في موارد GTA V (مثل ترخيص يسمح بالتعديل وإعادة "
        "التوزيع). الشخصيات المأخوذة من ألعاب أو أفلام أو صنّاع آخرين لا يجوز عادةً تحويلها أو مشاركتها. أنت مسؤول عن "
        "الشخصيات التي تحوّلها وتنشرها."
    ),
    "ped.rights.check": "صنعت هذه الشخصية أو لديّ حقوق تحويلها واستخدامها",
    "ped.rights.done": "أكدت حقوقك في هذه الشخصية.",
    "ped.op.rig": "التجهيز بالعظام في Durty Cloth Tool",
    "ped.op.rig.desc": (
        "يطابق Durty Cloth Tool الهيكل العظمي للقالب مع علاماتك ويحسب الأوزان ووضعية الراحة في اللعبة، من ملفات لعبتك"
    ),
    "ped.op.rig-again": "إعادة التجهيز بالعظام",
    "ped.op.cancel-rig.desc": "إيقاف التجهيز بالعظام في Durty Cloth Tool",
    "ped.rig.waiting": "بانتظار أن يبدأ Durty Cloth Tool التجهيز بالعظام.",
    "ped.rig.cancelling": "جارٍ إلغاء التجهيز بالعظام.",
    "ped.rig.working": "جارٍ التجهيز بالعظام",
    "ped.rig.progress": "{stage} ({percent} %)",
    "ped.stage.template": "قراءة القالب",
    "ped.stage.markers": "فحص العلامات",
    "ped.stage.skeleton": "مطابقة الهيكل العظمي",
    "ped.stage.weights": "نقل الأوزان",
    "ped.stage.rest": "التحويل إلى وضعية الراحة في اللعبة",
    "ped.stage.report": "كتابة التقرير",
    "ped.prop.refine": "تحسين العلامات",
    "ped.prop.refine.desc": "ينقل Durty Cloth Tool العلامات إلى منتصف الأطراف والجسم، ويُريك إلى أين",
    "ped.prop.fingers": "الأصابع",
    "ped.fingers.off": "تتحرك مع اليد",
    "ped.fingers.off.desc": "تتحرك الأصابع مع اليد، كقفاز بلا أصابع منفصلة",
    "ped.fingers.auto": "تلقائي",
    "ped.fingers.auto.desc": "إعطاء الأصابع أوزانًا من يد القالب",
    "ped.prop.face": "الوجه",
    "ped.face.off": "يتحرك مع الرأس",
    "ped.face.off.desc": "يتحرك الوجه مع الرأس",
    "ped.face.auto": "تلقائي",
    "ped.face.auto.desc": "إعطاء الوجه أوزانًا من وجه القالب، لتعابير الوجه",
    "ped.prop.roll": "عظام الالتواء",
    "ped.prop.roll.desc": "إعطاء أوزان لعظام الالتواء في الذراعين والساقين، التي تمنع انهيار الرسغين والفخذين",
    "ped.prop.helpers": "العظام المساعدة",
    "ped.prop.helpers.desc": "إعطاء أوزان للعظام المساعدة في القالب، كما في جسمه الأصلي",
    "ped.prop.rest": "شكل الراحة",
    "ped.rest.volume": "الحفاظ على الحجم",
    "ped.rest.volume.desc": "نقل الشخصية إلى وضعية الراحة مع حفاظ الكتفين والوركين على حجمها",
    "ped.rest.linear": "دقيق",
    "ped.rest.linear.desc": "نقل الشخصية إلى وضعية الراحة بحيث تعيد اللعبة، عند تحريك الشبكة بالعظام، وضعيتك تمامًا",
    "ped.result.ready": "جاهز (الثقة {percent} %)",
    "ped.result.review": "يحتاج إلى مراجعة (الثقة {percent} %)",
    "ped.result.markers": "({names})",
    "ped.result.moved": "نقل Durty Cloth Tool {count} من العلامات إلى منتصف الجسم (بالأصفر في العرض ثلاثي الأبعاد):",
    "ped.result.move": "{marker}: {cm} سم",
    "ped.result.subtext": (
        "يبني تطبيق التجهيز العظمي الهيكل العظمي (Armature) ويعطي الشبكات أوزانها ووضعية الراحة في اللعبة. تحتفظ "
        "شخصيتك بمظهرها، ويتراجع Ctrl+Z عن ذلك."
    ),
    "ped.result.proxy": "حُسبت الأوزان على نسخة مبسّطة من هذه الشبكة الكبيرة.",
    "ped.op.apply-rig": "تطبيق التجهيز العظمي",
    "ped.op.apply-rig.desc": (
        "بناء الهيكل العظمي (Armature) من التجهيز وإعطاء الشبكات أوزانه ووضعية الراحة في اللعبة؛ تحتفظ الشخصية بمظهرها"
    ),
    "ped.op.use-refined": "استخدام هذه العلامات",
    "ped.op.use-refined.desc": "نقل علاماتك إلى حيث وضعها Durty Cloth Tool",
    "ped.op.discard-rig": "تجاهل",
    "ped.op.discard-rig.desc": "التخلص من هذا التجهيز دون تطبيقه",
    "ped.done.applied": "تم تطبيق التجهيز العظمي: للهيكل العظمي {name} عظام عددها {bones}.",
    "ped.done.refined": "علاماتك الآن حيث وضعها Durty Cloth Tool.",
    "ped.rigged.line": "مُجهَّزة بالعظام من {template} (العظام: {bones})",
    "ped.op.previous-rig": "التجهيز السابق",
    "ped.op.previous-rig.desc": "تبديل التجهيز المطبّق بالتجهيز الذي طُبّق قبله",
    "ped.done.previous": "عاد التجهيز العظمي السابق.",
    "ped.op.remove-rig": "إزالة التجهيز العظمي",
    "ped.op.remove-rig.desc": "إزالة التجهيز العظمي: تعود الشخصية كما كانت قبل أول تجهيز",
    "ped.confirm.remove-rig": (
        "هل تريد إزالة التجهيز العظمي؟ تُحذف الهياكل العظمية وتعود الشخصية كما كانت قبل أول تجهيز."
    ),
    "ped.done.removed": "تمت إزالة التجهيز العظمي. عادت الشخصية كما كانت قبل التجهيز بالعظام.",
    "ped.warning.marker_offset": (
        "كانت {count} من العلامات تبعد أكثر من 2 سم عن منتصف الجسم (حتى {value} مم). تحقق منها."
    ),
    "ped.warning.asymmetric_markers": "تختلف العلامات اليسرى واليمنى بأكثر من 5 %. تحقق من الجانبين.",
    "ped.warning.proportion_out_of_range": "بعض النِّسب بعيدة عن نِسب القالب. القالب ذو البنية الأقرب يتحرك بشكل أفضل.",
    "ped.warning.ragdoll_mismatch": (
        "ارتفاع هذه الشخصية بعيد عن ارتفاع قالبها. في اللعبة، تستخدم الرصاصات والسقطات أشكال جسم القالب، لذا قد تخطئ "
        "الإصابات النموذج أو تقع بجانبه. اختر قالبًا أقرب، أو اختبر في اللعبة قبل النشر."
    ),
    "ped.warning.low_coverage": "طابق جزء فقط من الشخصية جسم القالب. تحقق من الأوزان في وضعيات الاختبار.",
    "ped.warning.inpainted_large": "مُلئت أوزان كثيرة من الرؤوس المجاورة. تحقق من وضعيات الاختبار.",
    "ped.warning.non_deforming_moved": "نُقلت بعض الأوزان عن عظام لا تحرّك الشبكة أبدًا.",
    "ped.warning.empty_rows_refilled": "كانت {count} من الرؤوس بلا أوزان فأخذت أوزان الرؤوس المجاورة.",
    "ped.warning.floating_parts": "رُبطت {count} من الأجزاء السائبة بأقرب عظمة.",
    "ped.warning.rest_strain": (
        "تنطوي بعض المثلثات في وضعية الراحة في اللعبة. انظر إلى الكتفين والوركين باختيار وضعية الراحة في اللعبة."
    ),
    "ped.warning.fingers_fallback": "تتحرك الأصابع مع اليد.",
    "ped.warning.other": "أبلغ Durty Cloth Tool عن {code}.",
    "ped.suggest": "{template} أقرب إلى نِسب شخصيتك. استخدمه وأعد التجهيز بالعظام لملاءمة أفضل.",
    "ped.refusal.marker_missing": "هناك علامات ناقصة.",
    "ped.refusal.marker_invalid": "بعض العلامات غير قابلة للاستخدام. ضعها على الشخصية مرة أخرى.",
    "ped.refusal.marker_degenerate": "بعض العلامات متراكبة فوق بعضها.",
    "ped.refusal.marker_side": (
        "اليسار واليمين متبادلان. يجب أن يكون يسار الشخصية عند +X: تحقق من أنها متجهة إلى الأمام."
    ),
    "ped.refusal.not_upright": "الشخصية لا تقف مستقيمة، أو رأسها أسفل رقبتها.",
    "ped.refusal.limb_length": "أحد الأطراف أقصر أو أطول بكثير من طرف القالب. تحقق من هذه العلامات.",
    "ped.refusal.asymmetric": "تختلف الأطراف اليسرى واليمنى بأكثر من 30 %.",
    "ped.refusal.pose_unsupported": (
        "إحدى الساقين مثنية أو مفتوحة أكثر من اللازم. اجعل الشخصية تقف مستقيمة، بوضعية A أو وضعية T."
    ),
    "ped.refusal.marker_outside_body": "تقع هذه العلامات خارج الشخصية.",
    "ped.refusal.mesh_invalid": "تعذّر على Durty Cloth Tool قراءة الشبكة (فارغة، أو معظم مثلثاتها مسطحة).",
    "ped.refusal.mesh_too_large": (
        "في الشخصية رؤوس أو مثلثات أكثر مما يقبله التجهيز بالعظام. قلّل تفاصيل نسخة منها أولًا، مثلًا بمعدِّل Decimate."
    ),
    "ped.refusal.options_invalid": "رفض Durty Cloth Tool خيارات التجهيز بالعظام. حدّث الإضافة.",
    "ped.refusal.template_invalid": "لا يستطيع Durty Cloth Tool استخدام هذا القالب. اختر قالبًا آخر.",
    "ped.refusal.template_not_found": "هذا القالب غير مثبّت. حدّث القائمة واختر قالبًا آخر.",
    "ped.refusal.game_required": "يحتاج Durty Cloth Tool إلى مجلد GTA V لديك. اضبطه في إعدادات Durty Cloth Tool.",
    "ped.refusal.fit_invalid": "خرج التجهيز العظمي معطوبًا. قارن العلامات بالشخصية وأعد التجهيز بالعظام.",
    "ped.refusal.other": "رفض Durty Cloth Tool التجهيز بالعظام ({code}).",
    "ped.heading.poses": "وضعيات الاختبار",
    "info.ped-poses": (
        "انثناءات بسيطة حسب اسم العظمة لترى كيف تحرّك الأوزان الشخصية. ليست حركات من اللعبة؛ والتجاعيد الصغيرة في "
        "الوضعيات القصوى طبيعية."
    ),
    "ped.pose.yours": "وضعيتك",
    "ped.pose.rest": "وضعية الراحة في اللعبة",
    "ped.pose.arms_up": "الذراعان إلى الأعلى",
    "ped.pose.arms_forward": "الذراعان إلى الأمام",
    "ped.pose.squat": "القرفصاء",
    "ped.pose.walk": "خطوة مشي",
    "ped.pose.twist": "التواء",
    "ped.op.pose": "الوضعية",
    "ped.op.pose.desc": "عرض الشخصية في هذه الوضعية",
    "ped.op.run-checks": "تشغيل الفحوصات",
    "ped.op.run-checks.desc": "فحص الأوزان والهيكل العظمي والشبكات مقارنة بالتجهيز العظمي، وفحص وضعيات الاختبار",
    "ped.op.show-finding.desc": "تحديد الرؤوس التي تخصها هذه الملاحظة",
    "ped.done.checks": "وجد تشغيل الفحوصات أمورًا تستحق النظر: {count}؛ ولا شيء سيرفضه Durty Cloth Tool.",
    "ped.done.checks-refused": "وجد تشغيل الفحوصات مشكلات سيرفضها Durty Cloth Tool: {count}.",
    "ped.local.none": "لم يُعثر على مشكلات.",
    "ped.local.unweighted": "عدد الرؤوس بلا وزن: {count}. يرفضها Durty Cloth Tool: امنحها أوزانًا.",
    "ped.local.too-many": "عدد الرؤوس التي تحركها أكثر من أربع عظام: {count}. تحتفظ اللعبة بالأربع الأقوى.",
    "ped.local.non-deforming": "عدد الرؤوس ذات الأوزان على عظام لا تحرّك الشبكة أبدًا: {count}.",
    "ped.local.unknown-groups": "تُستبعد مجموعات الرؤوس التي ليست عظامًا ({names}).",
    "ped.local.armature-changed": (
        "حُرّكت أو أُديرت عظام بعد التجهيز بالعظام ({names})، عددها {count}. تراجع عن ذلك أو أعد التجهيز بالعظام: "
        "تحتفظ العظام بدوران القالب."
    ),
    "ped.local.mesh-changed": "تغيّرت الشبكات بعد التجهيز بالعظام (أُضيفت رؤوس أو أُزيلت). أعد التجهيز بالعظام.",
    "ped.local.strain": "تتمدد {count} من الرؤوس أو تنضغط كثيرًا في {pose}.",
    "ped.local.hint": "التجاعيد الصغيرة في الوضعيات القصوى طبيعية. للتجاعيد الأكبر، حرّك علامة وأعد التجهيز بالعظام.",
    "ped.prop.name": "اسم الـ ped",
    "ped.prop.name.desc": "الاسم الذي يعرضه Durty Cloth Tool لهذا الـ ped",
    "ped.prop.model": "اسم النموذج",
    "ped.prop.model.desc": (
        "اسم الـ ped الجديد في اللعبة: حرف لاتيني صغير، ثم 2 إلى 31 من الأحرف الصغيرة أو الأرقام أو الشرطات السفلية (_)"
    ),
    "ped.prop.ragdoll": "جسم Ragdoll",
    "ped.ragdoll.template": "كالقالب",
    "ped.ragdoll.template.desc": "جسم Ragdoll المشترك الذي يستخدمه القالب",
    "ped.ragdoll.fred": "ذكر قياسي",
    "ped.ragdoll.fred.desc": "جسم Ragdoll المشترك لمعظم شخصيات ped الذكور",
    "ped.ragdoll.wilma": "أنثى قياسية",
    "ped.ragdoll.wilma.desc": "جسم Ragdoll المشترك لمعظم شخصيات ped الإناث",
    "ped.ragdoll.fred-large": "ذكر ضخم",
    "ped.ragdoll.fred-large.desc": "جسم Ragdoll المشترك لشخصيات ped الذكور الضخمة",
    "ped.ragdoll.wilma-large": "أنثى ضخمة",
    "ped.ragdoll.wilma-large.desc": "جسم Ragdoll المشترك لشخصيات ped الإناث الضخمة",
    "ped.ragdoll.subtext": (
        "تستخدم الرصاصات والسقطات والـ Ragdoll أشكال هذا الجسم في اللعبة. اختر جسمًا ضخمًا لشخصية أكبر بكثير."
    ),
    "ped.texture.too-large": "الصورة {name} أكبر من 4096 بكسل في أحد جانبيها. يرفضها Durty Cloth Tool.",
    "ped.texture.not-multiple-of-four": (
        "عرض الصورة {name} أو ارتفاعها لا يقبل القسمة على أربعة. يرفضها Durty Cloth Tool."
    ),
    "ped.texture.non-power-of-two": (
        "حجم الصورة {name} ليس من قوى العدد اثنين (مثل 1024 أو 2048). تعمل، لكن هذه الأحجام تبدو أفضل."
    ),
    "ped.op.send": "إنشاء ped مخصص",
    "ped.op.send.desc": (
        "تصدير الشخصية المُجهَّزة بالعظام في وضعية الراحة في اللعبة وإرسالها إلى Durty Cloth Tool، الذي ينشئ مشروع ped "
        "مخصص جديدًا بعد أن تؤكد هناك"
    ),
    "ped.op.cancel-send.desc": "سحب الشخصية ما دام Durty Cloth Tool لا يزال يسأل",
    "ped.send.subtext": (
        "يعرض Durty Cloth Tool الـ ped مع فحوصاته ويسأل أين يُنشأ المشروع. لا يُنشأ شيء حتى تختار إنشاء هناك."
    ),
    "ped.send.waiting": "أُرسلت الشخصية ({size} MiB). اختر إنشاء في Durty Cloth Tool.",
    "ped.send.withdrawing": "جارٍ سحب الشخصية.",
    "ped.send.withdrawn": "تم السحب: لم ينشئ Durty Cloth Tool شيئًا.",
    "ped.send.created": "أنشأ Durty Cloth Tool المشروع {name} مع الـ ped {model} من {template}.",
    "ped.send.created-late": (
        "أنشأ Durty Cloth Tool المشروع {name} مع الـ ped {model} في النهاية: اختير الإنشاء هناك في اللحظة "
        "التي سُحبت فيها الشخصية."
    ),
    "ped.send.findings": "فحوصات Durty Cloth Tool ({count}):",
    "ped.send.next": "تحقق من سلوك الـ ped في Durty Cloth Tool (نوع الـ ped، والحركة، والصوت)، ثم ابنِ المشروع.",
    "ped.finding.rig-mismatch": (
        "الهيكل العظمي ليس هيكل القالب ولا هيكل التجهيز: حُرّكت عظمة أو أُديرت. طبّق التجهيز العظمي مرة أخرى، أو أعد "
        "التجهيز بالعظام."
    ),
    "ped.finding.ped-budget": "رؤوس أكثر مما يجب أن يحمله الـ ped في مستوى تفاصيله الأعلى.",
    "ped.finding.ped-ragdoll-mismatch": (
        "ارتفاع الشخصية بعيد عن جسم Ragdoll الخاص بالقالب: تستخدم الإصابات والسقطات في اللعبة أشكال جسم القالب."
    ),
    "ped.finding.ped-rest-strain": "طوى التجهيز العظمي بعض المثلثات في وضعية الراحة في اللعبة.",
    "ped.why.select-meshes": "حدد شبكات شخصيتك أولًا.",
    "ped.why.no-character": "اختر شخصيتك في قسم الشخصية أولًا.",
    "ped.why.object-mode": "انتقل إلى Object Mode أولًا.",
    "ped.why.rigged": "الشخصية مُجهَّزة بالعظام. أزل التجهيز العظمي لتغييرها.",
    "ped.why.no-markers": "ضع العلامات أولًا.",
    "ped.why.guide-running": "دليل النقر قيد التشغيل.",
    "ped.why.view3d": "ابدأ دليل النقر من الشريط الجانبي للعرض ثلاثي الأبعاد.",
    "ped.why.checks": "أصلح ما تذكره الفحوصات في قسم الشخصية أولًا.",
    "ped.why.markers": "ضع كل العلامات أولًا.",
    "ped.why.connect": "اتصل بـ Durty Cloth Tool لاختيار قالب والتجهيز بالعظام.",
    "ped.why.template": "اختر قالبًا أولًا.",
    "ped.why.rights": "أكّد حقوقك في هذه الشخصية أولًا.",
    "ped.why.rigging": "يجري تجهيز بالعظام في Durty Cloth Tool.",
    "ped.why.not-rigging": "لا يجري أي تجهيز بالعظام.",
    "ped.why.no-result": "لا يوجد تجهيز عظمي لتطبيقه. جهّز الشخصية بالعظام أولًا.",
    "ped.why.no-previous": "لا يوجد تجهيز عظمي سابق.",
    "ped.why.not-rigged": "جهّز الشخصية بالعظام أولًا.",
    "ped.why.mesh-changed": "تغيّرت شبكات الشخصية بعد أن طلبت هذا التجهيز. أعد التجهيز بالعظام.",
    "ped.why.vertex-count": "يغيّر {name} عدد رؤوسه في مُعدِّل. طبّق مُعدِّلاته أولًا.",
    "ped.why.modifiers-shape-keys": "يحتوي {name} على مفاتيح شكل، لذا لا يمكن تطبيق مُعدِّلاته. أزلها أولًا.",
    "ped.why.export-failed": "لم يكتب مُصدِّر glTF في Blender الشخصية. التفاصيل في سجل Info الخاص به.",
    "ped.why.model": (
        "يتكون اسم النموذج من حرف لاتيني صغير، ثم 2 إلى 31 من الأحرف الصغيرة أو الأرقام أو الشرطات السفلية (_)."
    ),
    "ped.why.model-game": (
        "الأسماء التي تبدأ بـ {prefix} تخص شخصيات ped الخاصة باللعبة. اختر اسمًا آخر، مثل {suggestion}."
    ),
    "ped.why.name": "امنح الـ ped اسمًا.",
    "ped.why.transforms-first": "طبّق التحويلات أولًا.",
    "ped.why.refused-checks": "وجد تشغيل الفحوصات مشكلات سيرفضها Durty Cloth Tool. أصلحها أولًا.",
    "ped.why.textures": "إحدى الصور كبيرة جدًا أو لا يقبل حجمها القسمة على أربعة. أصلحها أولًا.",
    "ped.why.sending": "يجري إرسال ped مخصص.",
    "ped.why.not-sending": "لا يجري إرسال أي شيء.",
    "ped.invalid": "تعذّر على الإضافة تجهيز هذا الطلب: {detail}",
    "ped.plan.rig": "التجهيز بالعظام مضمّن في Durty Cloth Tool Ultimate.",
    "ped.plan.add": "يتطلب إنشاء مشروع ped مخصص Durty Cloth Tool Advanced أو Ultimate.",
    "ped.error.rig-busy": "يجهّز Durty Cloth Tool شخصية أخرى بالعظام. حاول مرة أخرى عندما ينتهي.",
    "ped.error.rig-cancelled": "أُلغي التجهيز بالعظام.",
    "ped.error.rig-refused": "تعذّر على Durty Cloth Tool تجهيز الشخصية بالعظام:",
    "ped.error.dct-too-old": "لا يصنع Durty Cloth Tool هذا شخصيات ped مخصصة من Blender بعد. حدّث Durty Cloth Tool.",
    "ped.error.rig-disconnected": "انقطع الاتصال بـ Durty Cloth Tool أثناء التجهيز بالعظام. أعد التجهيز بالعظام.",
    "ped.error.rig-timeout": "لم ينهِ Durty Cloth Tool التجهيز بالعظام في الوقت المناسب. أعد التجهيز بالعظام.",
    "ped.error.add-busy": "Durty Cloth Tool مشغول بـ ped مخصص آخر أو بعملية بناء. حاول مرة أخرى عندما ينتهي.",
    "ped.error.add-denied": "أُلغي في Durty Cloth Tool. أرسل الشخصية مرة أخرى عندما تكون جاهزًا.",
    "ped.error.model-rejected": "تعذّر على Durty Cloth Tool صنع ped من الشخصية. توضح فحوصاته أدناه السبب.",
    "ped.error.save-failed": "تعذّر على Durty Cloth Tool إنشاء المشروع. اختر مجلدًا آخر وأرسل مرة أخرى.",
    "ped.error.add-disconnected": "انقطع الاتصال بـ Durty Cloth Tool قبل أن يرد. أرسل الشخصية مرة أخرى.",
    "ped.error.add-timeout": "لم يرد Durty Cloth Tool في الوقت المناسب. أرسل الشخصية مرة أخرى.",
    "ped.error.add-unanswered": "لم يؤكد Durty Cloth Tool السحب. تحقق من قائمة مشاريعه.",
    "error.template-not-found": "هذا القالب غير مثبّت. حدّث القائمة واختر قالبًا آخر.",
    "error.mesh-too-large": (
        "في الشخصية رؤوس أو مثلثات كثيرة جدًا. قلّل تفاصيل نسخة منها أولًا، مثلًا بمعدِّل Decimate."
    ),
    "error.rig-refused": "تعذّر على Durty Cloth Tool تجهيز الشخصية بالعظام.",
    "error.upload-incomplete": "لم تصل الشخصية كاملة إلى Durty Cloth Tool. أرسلها مرة أخرى.",
}
