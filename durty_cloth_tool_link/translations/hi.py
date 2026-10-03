# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2026 Schmid Software Solutions (https://schmid-software.de)
"""Hindi (हिन्दी). Polite "आप", with the modding loanwords Durty Cloth Tool uses (टेक्सचर, प्रीव्यू, प्रोजेक्ट)."""

TEXT = {
    "path.connected-apps": "विकल्प > कनेक्टेड ऐप्स",
    "panel.main": "Durty Cloth Tool",
    "panel.details": "कनेक्शन",
    "panel.setup": "कनेक्ट करें",
    "panel.linked": "लिंक किया गया कपड़ा",
    "panel.live": "लाइव प्रीव्यू",
    "panel.checks": "टेक्सचर जाँच",
    "panel.model": "मॉडल",
    "panel.settings": "सेटिंग्स",
    "chip.connected": "कनेक्टेड",
    "chip.live": "लाइव",
    "chip.connecting": "कनेक्ट हो रहा है",
    "chip.action": "कार्रवाई ज़रूरी",
    "chip.offline": "ऑफ़लाइन",
    "chip.problem": "समस्या",
    "state.idle": "कनेक्ट नहीं है",
    "state.connecting": "Durty Cloth Tool खोजा जा रहा है",
    "state.waiting": "Durty Cloth Tool नहीं मिला। फिर से कोशिश होगी",
    "state.reconnecting": "Durty Cloth Tool से फिर से कनेक्ट हो रहा है",
    "state.hello": "कनेक्ट हो रहा है",
    "state.signing-in": "साइन इन का इंतज़ार",
    "state.authenticating": "साइन इन हो रहा है",
    "state.ready": "{name} के रूप में साइन इन",
    "state.signed-out": "साइन आउट",
    "state.dct-signed-out": "Durty Cloth Tool साइन आउट है",
    "state.dct-disconnected": "Durty Cloth Tool में डिस्कनेक्ट किया गया",
    "details.status": "स्थिति: {state}",
    "details.account": "{name} के रूप में साइन इन",
    "details.not-signed-in": "साइन इन नहीं है",
    "details.project": "प्रोजेक्ट: {name}",
    "details.addon": "ऐड-ऑन {version} ({channel})",
    "online.off": (
        "Blender का ऑनलाइन एक्सेस बंद है, इसलिए Durty Cloth Tool कनेक्ट नहीं हो सकता: हर कनेक्शन आपके gta.clothing "
        "साइन इन से पुष्ट होता है। इसे Preferences > System > Network में चालू करें।"
    ),
    "dct-signed-out": (
        "Durty Cloth Tool साइन आउट है। Durty Cloth Tool में साइन इन करें, फिर कनेक्ट करें चुनें। ऐड-ऑन समय-समय पर अपने "
        "आप भी कोशिश करता है।"
    ),
    "dct-disconnected": (
        "इस ऐप को Durty Cloth Tool में डिस्कनेक्ट किया गया। इसे फिर से कनेक्ट करने के लिए कनेक्ट करें चुनें।"
    ),
    "setup.find.title": "Durty Cloth Tool खोजें",
    "setup.find.done": "Durty Cloth Tool मिल गया",
    "setup.find.subtext": "इस कंप्यूटर पर Durty Cloth Tool शुरू करें। ऐड-ऑन उसे अपने आप खोज लेता है।",
    "setup.find.searching": "Durty Cloth Tool खोजा जा रहा है…",
    "setup.find.waiting": "Durty Cloth Tool अभी चल नहीं रहा है। ऐड-ऑन खोजता रहेगा…",
    "setup.sign-in.title": "gta.clothing से साइन इन करें",
    "setup.sign-in.done": "साइन इन हो गया",
    "setup.sign-in.subtext": (
        "Creator Link आपके gta.clothing अकाउंट (Discord) का उपयोग करता है। इस कंप्यूटर पर आप एक बार साइन इन करते हैं।"
    ),
    "setup.sign-in.starting": "साइन इन शुरू हो रहा है…",
    "setup.sign-in.waiting": "मंज़ूरी का इंतज़ार…",
    "setup.sign-in.asked": "Durty Cloth Tool साइन इन अनुरोध दिखा रहा है। उसे वहीं मंज़ूर करें।",
    "setup.sign-in.approved": "Durty Cloth Tool ने साइन इन मंज़ूर कर दिया। पूरा हो रहा है…",
    "setup.sign-in.declined": "Durty Cloth Tool ने साइन इन मंज़ूर नहीं किया। इसके बजाय ब्राउज़र में साइन इन करें।",
    "setup.sign-in.browser-subtext": "साइन इन पेज खोलें और जाँचें कि वह यह कोड दिखा रहा है:",
    "setup.sign-in.signed-out": "आपने साइन आउट किया है। Creator Link इस्तेमाल करने के लिए फिर से साइन इन करें।",
    "linked.project": "प्रोजेक्ट: {name}",
    "linked.no-project": "Durty Cloth Tool में एक प्रोजेक्ट खोलें।",
    "linked.no-cloth": "यहाँ काम करने के लिए Durty Cloth Tool में एक कपड़ा चुनें।",
    "linked.cloth": "{name} · वैरिएशन {letter}",
    "linked.cloth-no-variation": "{name}",
    "linked.texture": "{name} ({width} x {height})",
    "linked.map": "मैप",
    "linked.follows": "Durty Cloth Tool में आपके चयन के साथ चलता है",
    "linked.map-locked": "दूसरा मैप चुनने के लिए लाइव प्रीव्यू रोकें।",
    "linked.map-missing.diffuse": "इस कपड़े में डिफ्यूज़ मैप नहीं है।",
    "linked.map-missing.normal": "इस कपड़े में नॉर्मल मैप नहीं है।",
    "linked.map-missing.specular": "इस कपड़े में स्पेक्युलर मैप नहीं है।",
    "map.diffuse": "डिफ्यूज़ (रंग)",
    "map.diffuse.desc": "कपड़े का रंग वाला टेक्सचर",
    "map.normal": "नॉर्मल",
    "map.normal.desc": "कपड़े का नॉर्मल मैप",
    "map.specular": "स्पेक्युलर",
    "map.specular.desc": "कपड़े का स्पेक्युलर मैप",
    "live.off": "ped पर अपनी पेंटिंग देखने के लिए लाइव प्रीव्यू शुरू करें।",
    "live.reading": "इमेज पढ़ी जा रही है…",
    "live.starting": "लाइव प्रीव्यू शुरू हो रहा है…",
    "live.on": "ped पर लाइव",
    "live.sending": "इमेज भेजी जा रही है…",
    "live.not-worn": "इसे देखने के लिए Durty Cloth Tool में यह कपड़ा ped को पहनाएँ।",
    "live.paused-dct": "Durty Cloth Tool में 3D प्रीव्यू रुका हुआ है।",
    "live.paused": "रुका हुआ। फिर से शुरू करने पर आपके बदलाव भेजे जाएँगे।",
    "live.saving": "सेव हो रहा है…",
    "live.unsaved": "अभी प्रोजेक्ट में सेव नहीं हुआ",
    "live.save-subtext": (
        "सेव करने से यह मैप आपके प्रोजेक्ट में लिखा जाता है। आप इसे Durty Cloth Tool में कपड़े के इतिहास में पूर्ववत कर "
        "सकते हैं।"
    ),
    "live.saved": "{name} में सेव किया गया। आप इसे इतिहास में पूर्ववत कर सकते हैं।",
    "live.saved-unnamed": "कपड़े में सेव किया गया। आप इसे इतिहास में पूर्ववत कर सकते हैं।",
    "live.saved-variation": "{name} के नए वैरिएशन के रूप में सेव किया गया।",
    "live.saved-variation-unnamed": "नए वैरिएशन के रूप में सेव किया गया।",
    "live.discarded": "Durty Cloth Tool में बदलाव छोड़ दिए गए।",
    "live.stopped": "लाइव प्रीव्यू रुक गया।",
    "live.stopped-unsaved": (
        "लाइव प्रीव्यू रुक गया। बदलाव प्रोजेक्ट में सेव नहीं हुए; Blender की इमेज में वे बने रहते हैं।"
    ),
    "live.failed": "एक अनपेक्षित समस्या के बाद लाइव प्रीव्यू रुक गया: {detail}",
    "live.upsell": "लाइव प्रीव्यू Durty Cloth Tool Ultimate में शामिल है।",
    "live.save-upsell": "कपड़े में सेव करना Durty Cloth Tool Ultimate में शामिल है।",
    "live.image-changed": "इमेज का आकार बदल गया है। लाइव प्रीव्यू फिर से शुरू करें।",
    "live.image-removed": "इमेज हटा दी गई।",
    "live.no-memory": "इतनी बड़ी इमेज के लिए पर्याप्त मेमोरी नहीं है।",
    "colour.non-color-diffuse": "इमेज Non-Color पर सेट है; इसके मान बिना बदले रंग के रूप में भेजे जाते हैं।",
    "colour.unknown-diffuse": (
        "इमेज का कलर स्पेस {space} बिना बदले भेजा जाता है; सटीक रंगों के लिए sRGB इस्तेमाल करें।"
    ),
    "colour.unknown-data": (
        "मैप का कलर स्पेस Non-Color पर सेट करें; {space} मान वैसे ही भेजे जाते हैं जैसे वे Blender में हैं।"
    ),
    "image.none": "पहले एक इमेज चुनें।",
    "image.tiled": "UDIM (टाइल वाली) इमेज इस्तेमाल नहीं हो सकतीं। एक अकेली इमेज इस्तेमाल करें।",
    "image.source": "केवल इमेज फ़ाइलें और बनाई गई इमेज ही इस्तेमाल हो सकती हैं।",
    "image.unreadable": "इमेज पढ़ी नहीं जा सकी।",
    "image.not-loaded": "इमेज लोड नहीं हो सकी। जाँचें कि उसकी फ़ाइल मौजूद है।",
    "image.channels": "केवल ग्रे, RGB और RGBA इमेज ही इस्तेमाल हो सकती हैं।",
    "image.empty": "इमेज में कोई पिक्सेल नहीं है। पहले उसे खोलें या बनाएँ।",
    "image.too-large": "जिन इमेज की किसी भुजा पर {size} पिक्सेल से ज़्यादा हैं, वे इस्तेमाल नहीं हो सकतीं।",
    "image.no-painted": "पेंट की जा रही कोई इमेज नहीं मिली। सूची में इमेज चुनें।",
    "checks.errors": "त्रुटियाँ: {count}",
    "checks.warnings": "चेतावनियाँ: {count}",
    "checks.notes": "नोट: {count}",
    "checks.clean": "कोई समस्या नहीं मिली।",
    "checks.not-checked": "लाइव प्रीव्यू शुरू होने पर Durty Cloth Tool टेक्सचर जाँचता है।",
    "checks.checking": "टेक्सचर जाँचा जा रहा है…",
    "checks.unavailable": "टेक्सचर जाँच Durty Cloth Tool Ultimate में शामिल है।",
    "severity.error": "त्रुटि",
    "severity.warning": "चेतावनी",
    "severity.info": "नोट",
    "finding.unknown": "Durty Cloth Tool ने {code} बताया।",
    "finding.non-power-of-two": "आकार दो की घात नहीं है (जैसे 1024 या 2048)।",
    "finding.not-multiple-of-four": "आकार चार का गुणज नहीं है, जो कंप्रेस्ड टेक्सचर के लिए ज़रूरी है।",
    "finding.too-large": "टेक्सचर हर भुजा पर 2048 पिक्सेल से बड़ा है, जिससे गेम की बहुत मेमोरी लगती है।",
    "finding.too-small": "टेक्सचर हर भुजा पर 16 पिक्सेल से छोटा है।",
    "finding.size-changed": "आकार प्रोजेक्ट में सेव टेक्सचर से अलग है।",
    "finding.palette-alpha": (
        "यह कपड़ा कलर पैलेट इस्तेमाल करता है: इसका अल्फ़ा चैनल पैलेट के रंग चुनता है, इसलिए अल्फ़ा सावधानी से पेंट करें।"
    ),
    "finding.cutout-alpha": "यह कपड़ा अल्फ़ा को कटआउट की तरह इस्तेमाल करता है: पारदर्शी पिक्सेल ped पर छिपे रहते हैं।",
    "finding.hair-ramp": "ये बाल हैं: लाल और हरे चैनल बालों के रंग चुनते हैं।",
    "finding.bc1-alpha": "सेव किया गया टेक्सचर केवल पूरी तरह पारदर्शी या पूरी तरह अपारदर्शी अल्फ़ा रखता है।",
    "finding-fix.non-power-of-two": "सेव करने से पहले आकार को दो की घात पर करें, जैसे 1024 x 1024।",
    "finding-fix.not-multiple-of-four": "आकार ऐसा करें कि दोनों भुजाएँ चार से विभाज्य हों, जैसे 1024 x 512।",
    "finding-fix.too-large": "हर भुजा पर 2048 पिक्सेल या कम इस्तेमाल करें, जब तक कपड़े को उतनी डिटेल न चाहिए।",
    "finding-fix.too-small": "हर भुजा पर कम से कम 16 पिक्सेल इस्तेमाल करें।",
    "finding-fix.size-changed": (
        "सेव करने से टेक्सचर इस आकार में बदल जाता है। अगर आप आकार नहीं बदलना चाहते थे तो सेव किए गए आकार पर लौटें।"
    ),
    "finding-fix.palette-alpha": "जब तक आप पैलेट के रंग बदलना न चाहें, अल्फ़ा मानों को वैसा ही रहने दें।",
    "finding-fix.cutout-alpha": "पारदर्शिता केवल वहीं पेंट करें जहाँ कपड़ा छिपना चाहिए।",
    "finding-fix.hair-ramp": "लाल और हरे चैनल को बालों के रंग के मास्क की तरह पेंट करें, दिखने वाले रंग की तरह नहीं।",
    "finding-fix.bc1-alpha": "पूरी तरह पारदर्शी या पूरी तरह अपारदर्शी अल्फ़ा इस्तेमाल करें; सेव करते समय नरम किनारे खो जाते हैं।",
    "model.subtext": "आपके एडिट करना बंद करने के कुछ ही देर बाद मॉडल फिर से भेजता है।",
    "model.name": "मॉडल: {name}",
    "model.sending": "{name} भेजा जा रहा है (टेक्सचर: {count})",
    "model.previewing": "Durty Cloth Tool में ped पर दिख रहा है। इसे वहीं या यहीं सेव करें या छोड़ दें।",
    "model.findings": "Durty Cloth Tool ने समस्याएँ बताईं: {count}।",
    "model.warnings-paused": (
        "Sollumz ने चेतावनियाँ दीं, इसलिए अपने आप भेजना रुका है। Sollumz का Info लॉग देखें, फिर दोबारा शुरू करने के लिए "
        "फिर से भेजें।"
    ),
    "model.warnings": "Sollumz ने चेतावनियाँ दीं; उसके Info लॉग में विवरण है।",
    "model.saving": "Durty Cloth Tool में मॉडल सेव हो रहा है…",
    "model.saved": "मॉडल कपड़े में सेव हो गया। आप इसे इतिहास में पूर्ववत कर सकते हैं।",
    "model.discarded": "Durty Cloth Tool में मॉडल छोड़ दिया गया।",
    "model.save-retry": "Durty Cloth Tool अभी मॉडल लोड कर रहा है। कुछ ही पल में सेव होगा…",
    "model.save-busy": "Durty Cloth Tool अभी मॉडल में व्यस्त है। थोड़ी देर में फिर से सेव करें।",
    "model.block.no-model": "पहले एक मॉडल भेजें।",
    "model.block.saving": "पहले से सेव हो रहा है।",
    "model.block.waiting": "Durty Cloth Tool के जवाब का इंतज़ार करें।",
    "model.block.pushing": "सबसे नया भेजा गया मॉडल Durty Cloth Tool में दिखने तक रुकें, फिर सेव करें।",
    "model.block.due": "आपके नए बदलाव भेजे जाने वाले हैं। जब वे Durty Cloth Tool में दिखें, तब सेव करें।",
    "model.wait.tool": "अपने आप भेजना चल रहे टूल के खत्म होने का इंतज़ार करता है।",
    "model.wait.mode": "अपने आप भेजना आपके {mode} छोड़ने का इंतज़ार करता है।",
    "model.gone": "भेजा गया मॉडल अब इस फ़ाइल में नहीं है। उसे फिर से भेजें।",
    "model.failed": "अपने आप भेजना विफल रहा: {detail}",
    "model.select": "भेजने के लिए मॉडल चुनें: एक Sollumz Drawable Dictionary या उसके अंदर का कोई ऑब्जेक्ट।",
    "model.one-root": "केवल एक Drawable Dictionary के ऑब्जेक्ट चुनें।",
    "model.needs-dictionary": (
        "Durty Cloth Tool को Drawable Dictionary चाहिए। Drawable को एक Drawable Dictionary का चाइल्ड बनाएँ (Sollumz: "
        "Create Drawable Dictionary) और फिर से भेजें।"
    ),
    "model.not-sollumz": "एक Sollumz Drawable Dictionary या उसके अंदर का कोई ऑब्जेक्ट चुनें।",
    "model.unhide": "Drawable Dictionary (या उसके अंदर का कोई ऑब्जेक्ट) दिखाएँ, उसे चुनने योग्य बनाएँ, फिर से भेजें।",
    "model.not-shown": "मॉडल किसी ऐसे सीन में नहीं है जो Blender विंडो में दिख रहा हो। उसका सीन दिखाएँ, फिर से भेजें।",
    "model.not-in-layer": "मॉडल मौजूदा view layer में नहीं है। उसे दिखाएँ, फिर से भेजें।",
    "model.export-failed": "Sollumz मॉडल एक्सपोर्ट नहीं कर सका: {detail}",
    "model.not-exported": "Sollumz ने मॉडल एक्सपोर्ट नहीं किया। उसके Info लॉग में विवरण है।",
    "sollumz.ready": "Sollumz {version}",
    "sollumz.ready-unknown": "Sollumz",
    "sollumz.missing": "मॉडल भेजने के लिए Sollumz {version} या नया इंस्टॉल और चालू करें।",
    "sollumz.too-old": (
        "यह Sollumz Durty Cloth Tool के लिए एक्सपोर्ट करने को बहुत पुराना है। Sollumz {version} या नए पर अपडेट करें।"
    ),
    "sollumz.tested": "Sollumz {version} के साथ जाँचा गया।",
    "bundle.unreadable": "एक्सपोर्ट फ़ोल्डर पढ़ा नहीं जा सका ({detail})।",
    "bundle.not-dictionary": (
        "Sollumz ने drawable या fragment एक्सपोर्ट किया, drawable dictionary नहीं। Durty Cloth Tool को Drawable "
        "Dictionary चाहिए: अपने Drawable को एक का चाइल्ड बनाएँ (Sollumz: Create Drawable Dictionary) और फिर से भेजें।"
    ),
    "bundle.no-model": "Sollumz ने कोई मॉडल एक्सपोर्ट नहीं किया। कारण Sollumz के Info लॉग में है।",
    "bundle.several": "Sollumz ने कई drawable dictionary एक्सपोर्ट किए ({count})। केवल एक के ऑब्जेक्ट चुनें।",
    "bundle.bad-name": (
        "'{name}' भेजा नहीं जा सकता: फ़ाइल नामों में केवल अक्षर, अंक, '_', '-' और '.' हो सकते हैं, वे '.' से शुरू नहीं हो "
        "सकते या '..' नहीं रख सकते, और अधिकतम 128 अक्षर के हो सकते हैं। Blender में टेक्सचर या मॉडल का नाम बदलें।"
    ),
    "bundle.duplicate": "दो टेक्सचर का नाम '{name}' है। हर टेक्सचर को अलग नाम दें।",
    "bundle.too-many": "मॉडल {count} टेक्सचर इस्तेमाल करता है; अधिकतम {limit} भेजे जा सकते हैं।",
    "bundle.empty-file": "'{name}' खाली है। मॉडल फिर से एक्सपोर्ट करें।",
    "bundle.too-large": "मॉडल और उसके टेक्सचर मिलकर {size} MiB से बड़े हैं और भेजे नहीं जा सकते।",
    "bundle.invalid": "एक्सपोर्ट भेजा नहीं जा सकता: {detail}",
    "settings.connection": "कनेक्शन",
    "settings.account": "अकाउंट",
    "settings.updates": "अपडेट",
    "settings.privacy": "गोपनीयता",
    "settings.about": "जानकारी",
    "settings.models": "मॉडल",
    "settings.connect-subtext": (
        "इस कंप्यूटर पर Durty Cloth Tool ज़रूरी है। कनेक्शन इसी कंप्यूटर पर रहता है; gta.clothing हर कनेक्शन के लिए "
        "आपका साइन इन पुष्ट करता है।"
    ),
    "settings.signed-in-as": "{name} के रूप में साइन इन",
    "settings.not-signed-in": "साइन इन नहीं है",
    "settings.signed-out": "साइन आउट",
    "settings.sign-out-subtext": "साइन आउट करने से इस कंप्यूटर पर इस ऐड-ऑन का gta.clothing साइन इन खत्म हो जाता है।",
    "settings.device-name-subtext": "gta.clothing का मंज़ूरी पेज इसे दिखाता है, ताकि आप अपने कंप्यूटर पहचान सकें।",
    "settings.licence": "GPL-3.0-or-later, Schmid Software Solutions. DurtyFree (Pleb Masters) द्वारा देखरेख।",
    "settings.this-version": "यह संस्करण: {version} ({channel})",
    "settings.diagnostics-copied": (
        "डायग्नोस्टिक्स कॉपी हो गए। मदद माँगते समय इन्हें Pleb Masters Community Discord सर्वर में पेस्ट करें। इनमें संस्करण "
        "और स्थिति कोड हैं, कोई फ़ाइल पाथ और कोई साइन इन डेटा नहीं।"
    ),
    "settings.disk-install": (
        "यह कॉपी एक फ़ाइल से इंस्टॉल हुई है, इसलिए Blender इसे अपडेट नहीं कर सकता। अपडेट पाने के लिए "
        "gta.clothing के प्लगइन पेज से इंस्टॉल लिंक को Blender पर खींचें।"
    ),
    "settings.updates-on": "Blender इस ऐड-ऑन को Durty Cloth Tool एक्सटेंशन रिपॉज़िटरी से अपडेट करता है।",
    "op.plugins-page": "इंस्टॉल लिंक पाएँ",
    "op.plugins-page.desc": "gta.clothing पर प्लगइन पेज खोलें, जहाँ से आप इंस्टॉल लिंक को Blender पर खींचते हैं",
    "info.channel": (
        "Experimental को नई सुविधाएँ और सुधार पहले मिलते हैं और यह ज़्यादा बार बदलता है। Release को वे जाँच "
        "के बाद मिलते हैं। चैनल उस इंस्टॉल लिंक से तय होता है जिसे आप Blender पर खींचते हैं।"
    ),
    "settings.code-copied": "कोड कॉपी हो गया।",
    "channel.release": "Release",
    "channel.experimental": "Experimental",
    "info.find": (
        "Creator Link केवल इस कंप्यूटर पर Durty Cloth Tool से बात करता है। आपके साइन इन के अलावा इंटरनेट पर कुछ नहीं भेजा जाता।"
    ),
    "info.sign-in": (
        "साइन इन Durty Cloth Tool को बताता है कि यह ऐड-ऑन आपके अकाउंट का है। ऐड-ऑन कभी आपका Discord पासवर्ड नहीं "
        "देखता। Durty Cloth Tool इस ऐप को {apps} में दिखाता है, जहाँ आप इसे डिस्कनेक्ट कर सकते हैं।"
    ),
    "info.map": (
        "चुनें कि इमेज प्रीव्यू में कपड़े का कौन सा मैप बदलती है: डिफ्यूज़ (रंग), नॉर्मल या स्पेक्युलर। डिफ्यूज़ इमेज sRGB "
        "रंग होती हैं; नॉर्मल और स्पेक्युलर मैप को Non-Color पर सेट करें।"
    ),
    "info.variation": (
        "नॉर्मल और स्पेक्युलर मैप मॉडल के होते हैं और हर वैरिएशन में साझा होते हैं, इसलिए केवल डिफ्यूज़ (रंग) नया वैरिएशन "
        "बन सकता है।"
    ),
    "info.live": (
        "हर ब्रश स्ट्रोक खत्म होने पर ऐड-ऑन इमेज पढ़ता है और जो बदला वह भेजता है। जब तक आप कपड़े में सेव करें या नए "
        "वैरिएशन के रूप में सेव करें न चुनें, आपके प्रोजेक्ट में कुछ सेव नहीं होता।"
    ),
    "info.model": (
        "मॉडल भेजें चुना गया Sollumz Drawable Dictionary उसके टेक्सचर के साथ CodeWalker XML (YDD) के रूप में एक्सपोर्ट "
        "करता है और लिंक किए गए कपड़े पर दिखाता है। जब तक आप मॉडल को कपड़े में सेव करें न चुनें, कुछ सेव नहीं होता।"
    ),
    "info.checks": (
        "Durty Cloth Tool अपनी त्रुटि सूची की तरह इमेज को GTA V और कपड़े की ज़रूरतों के अनुसार जाँचता है। सेव करने से पहले "
        "त्रुटियाँ ठीक करें; चेतावनियाँ और नोट सलाह हैं।"
    ),
    "info.privacy": (
        "इस कंप्यूटर पर रहता है: आपकी इमेज, मॉडल और लाइव प्रीव्यू के पिक्सेल। ये केवल Durty Cloth Tool को जाते हैं। "
        "gta.clothing को जाता है: आपका साइन इन (इस कंप्यूटर के नाम के साथ, जब तक आप इसे बंद न करें), हर कनेक्शन की "
        "पुष्टि, आपका साइन आउट और Blender की अपडेट जाँच।"
    ),
    "op.connect": "कनेक्ट करें",
    "op.connect.desc": "इस कंप्यूटर पर Durty Cloth Tool से कनेक्ट करें",
    "op.disconnect": "डिस्कनेक्ट करें",
    "op.disconnect.desc": "Durty Cloth Tool से डिस्कनेक्ट करें। चल रहा लाइव प्रीव्यू रुक जाएगा",
    "op.sign-in-dct": "Durty Cloth Tool में मंज़ूर करें",
    "op.sign-in-dct.desc": "Durty Cloth Tool से उसके अकाउंट के साथ साइन इन मंज़ूर करने को कहें",
    "op.sign-in": "ब्राउज़र में साइन इन करें",
    "op.sign-in.desc": "अपने gta.clothing अकाउंट (Discord) से ब्राउज़र में साइन इन करें",
    "op.open-sign-in": "साइन इन पेज खोलें",
    "op.open-sign-in.desc": "वह gta.clothing पेज खोलें जो यह साइन इन मंज़ूर करता है",
    "op.copy-code": "कोड कॉपी करें",
    "op.copy-code.desc": "साइन इन कोड क्लिपबोर्ड पर कॉपी करें",
    "op.cancel-sign-in": "रद्द करें",
    "op.cancel-sign-in.desc": "साइन इन का इंतज़ार बंद करें",
    "op.sign-out": "साइन आउट करें",
    "op.sign-out.desc": "इस ऐड-ऑन में gta.clothing से साइन आउट करें और डिस्कनेक्ट करें",
    "op.update-page": "अपडेट पाएँ",
    "op.update-page.desc": "Durty Cloth Tool और उसके प्लगइन के मौजूदा संस्करणों वाला पेज खोलें",
    "op.use-paint-image": "पेंट की जा रही इमेज इस्तेमाल करें",
    "op.use-paint-image.desc": "वह इमेज इस्तेमाल करें जिस पर आप पेंट कर रहे हैं, या Image Editor वाली",
    "op.live-start": "लाइव प्रीव्यू शुरू करें",
    "op.live-start.desc": (
        "यह इमेज लिंक किए गए कपड़े पर दिखाएँ और हर ब्रश स्ट्रोक के बाद अपडेट करें। आपके सेव करने तक कुछ सेव नहीं होता"
    ),
    "op.live-stop": "लाइव प्रीव्यू रोकें",
    "op.live-stop.desc": (
        "इमेज भेजना बंद करें। बदलाव ped पर तब तक रहते हैं जब तक आप या Durty Cloth Tool उन्हें छोड़ न दें"
    ),
    "op.live-pause": "रोकें",
    "op.live-pause.desc": "अभी के लिए बदलाव न भेजें। ped आखिरी अपडेट दिखाता रहता है",
    "op.live-resume": "फिर से शुरू करें",
    "op.live-resume.desc": "फिर से बदलाव भेजें, रुकने के दौरान बदली हर चीज़ से शुरू करते हुए",
    "op.live-send": "अभी भेजें",
    "op.live-send.desc": "स्क्रिप्ट, बेकिंग या रीलोड से हुए बदलावों के लिए इमेज अभी फिर से भेजें",
    "op.live-save": "कपड़े में सेव करें",
    "op.live-save.desc": "अपने प्रोजेक्ट में लिंक किए गए कपड़े का मैप इस इमेज से बदलें। आप इसे इतिहास में पूर्ववत कर सकते हैं",
    "op.live-save-variation": "नए वैरिएशन के रूप में सेव करें",
    "op.live-save-variation.desc": "यह इमेज लिंक किए गए कपड़े में नए टेक्सचर वैरिएशन के रूप में जोड़ें (केवल डिफ्यूज़ (रंग))",
    "op.live-discard": "बदलाव छोड़ें",
    "op.live-discard.desc": "ped पर दिख रहे बदलाव हटाएँ और रोकें। आपका प्रोजेक्ट अपना सेव टेक्सचर रखता है",
    "op.check-again": "फिर से जाँचें",
    "op.check-again.desc": "Durty Cloth Tool से इमेज फिर से जाँचने को कहें",
    "op.model-push": "मॉडल भेजें",
    "op.model-push.desc": (
        "चुना गया Sollumz Drawable Dictionary एक्सपोर्ट करें और लिंक किए गए कपड़े पर दिखाएँ। आपके सेव करने तक कुछ सेव नहीं होता"
    ),
    "op.model-save": "मॉडल को कपड़े में सेव करें",
    "op.model-save.desc": "भेजा गया मॉडल अपने प्रोजेक्ट में सेव करें। पिछला मॉडल कपड़े के इतिहास में रहता है",
    "op.model-discard": "छोड़ें",
    "op.model-discard.desc": "भेजा गया मॉडल ped से हटाएँ। आपका प्रोजेक्ट अपना सेव मॉडल रखता है",
    "op.diagnostics": "डायग्नोस्टिक्स कॉपी करें",
    "op.diagnostics.desc": "सहायता के लिए संस्करण और स्थिति कोड कॉपी करें (कोई फ़ाइल पाथ और कोई साइन इन डेटा नहीं)",
    "op.help": "मदद",
    "op.help.desc": "Durty Cloth Tool का दस्तावेज़ खोलें",
    "op.community": "Pleb Masters Community Discord",
    "op.community.desc": "Pleb Masters Community Discord सर्वर खोलें, जहाँ आप मदद माँग सकते हैं",
    "op.info": "अधिक जानकारी",
    "op.join-discord": "Discord सर्वर से जुड़ें",
    "op.join-discord.desc": "ब्राउज़र में Pleb Masters Community Discord सर्वर का आमंत्रण खोलें",
    "prop.image": "इमेज",
    "prop.image.desc": "लिंक किए गए कपड़े पर दिखने वाली इमेज",
    "prop.map": "मैप",
    "prop.map.desc": "इमेज प्रीव्यू में लिंक किए गए कपड़े का कौन सा मैप बदलती है",
    "prop.auto-push": "अपने आप भेजें",
    "prop.auto-push.desc": "एडिट करना बंद करने के कुछ देर बाद मॉडल फिर से भेजें (पहली बार भेजने के बाद)",
    "prop.auto-connect": "अपने आप कनेक्ट करें",
    "prop.auto-connect.desc": "Blender शुरू होने पर इस कंप्यूटर पर Durty Cloth Tool खोजें",
    "prop.device-name": "साइन इन करते समय इस कंप्यूटर का नाम दिखाएँ",
    "prop.device-name.desc": (
        "साइन इन के साथ इस कंप्यूटर का नाम भेजें, ताकि gta.clothing का मंज़ूरी पेज दिखा सके कि कौन सा कंप्यूटर पूछ रहा है"
    ),
    "prop.delay": "अपने आप भेजने की देरी",
    "prop.delay.desc": "भेजा गया मॉडल कितने सेकंड बिना बदले रहना चाहिए, इससे पहले कि अपने आप भेजें उसे फिर से भेजे",
    "notice.signed-in": "{name} के रूप में साइन इन।",
    "notice.signing-out": "साइन आउट हो रहा है…",
    "notice.signed-out": "साइन आउट हो गया।",
    "notice.signed-out-local": (
        "इस कंप्यूटर पर साइन आउट हो गया। gta.clothing पर सेशन भी खत्म करने के लिए Blender की प्राथमिकताओं में ऑनलाइन एक्सेस "
        "चालू करें।"
    ),
    "notice.signed-out-unreached": (
        "इस कंप्यूटर पर साइन आउट हो गया; gta.clothing तक नहीं पहुँचा जा सका। वहाँ का सेशन अपने आप खत्म होगा, या अपने "
        "अकाउंट पेज पर उसे खत्म करें।"
    ),
    "notice.browser-opens": "आपका ब्राउज़र जल्द ही साइन इन पेज खोलेगा।",
    "notice.no-sign-in": "कोई साइन इन इंतज़ार में नहीं है।",
    "notice.not-gta-clothing": "साइन इन लिंक gta.clothing का लिंक नहीं है।",
    "notice.unexpected": "ऐड-ऑन में एक अनपेक्षित समस्या आई: {detail}",
    "notice.secrets-unreadable": "सेव किया गया साइन इन पढ़ा नहीं जा सका ({detail})। फिर से साइन इन करें।",
    "notice.secret-store": "सुरक्षित साइन इन पढ़ा या लिखा नहीं जा सका। फिर से साइन इन करें।",
    "notice.file-error": "एक फ़ाइल पढ़ी या लिखी नहीं जा सकी: {detail}",
    "notice.not-ready": "ऐड-ऑन तैयार नहीं है।",
    "notice.connect-first": "पहले Durty Cloth Tool से कनेक्ट करें।",
    "notice.select-cloth": "पहले Durty Cloth Tool में एक कपड़ा चुनें।",
    "notice.start-live-first": "पहले लाइव प्रीव्यू शुरू करें।",
    "notice.wait-saving": "सेव पूरा होने तक रुकें।",
    "notice.diffuse-only": "केवल डिफ्यूज़ (रंग) नया वैरिएशन बन सकता है।",
    "notice.pushing": "एक भेजना चल रहा है।",
    "notice.online-off": "Blender का ऑनलाइन एक्सेस बंद है।",
    "error.generic": "कुछ गलत हो गया।",
    "error.generic-code": "कुछ गलत हो गया ({code})।",
    "error.malformed-message": "Durty Cloth Tool और यह ऐड-ऑन एक-दूसरे को समझ नहीं पाए। दोनों अपडेट करें, फिर कोशिश करें।",
    "error.invalid-message": "Durty Cloth Tool और यह ऐड-ऑन एक-दूसरे को समझ नहीं पाए। दोनों अपडेट करें, फिर कोशिश करें।",
    "error.unknown-message-type": "Durty Cloth Tool यह अनुरोध नहीं जानता। Durty Cloth Tool अपडेट करें।",
    "error.unexpected-message": "Durty Cloth Tool को अभी यह अनुरोध अपेक्षित नहीं था। फिर कोशिश करें।",
    "error.message-too-large": "इमेज या मॉडल भेजने के लिए बहुत बड़ा था।",
    "error.unsupported-protocol": "यह ऐड-ऑन और Durty Cloth Tool अलग लिंक संस्करण इस्तेमाल करते हैं। दोनों अपडेट करें।",
    "error.plugin-too-old": "यह ऐड-ऑन आपके Durty Cloth Tool के लिए बहुत पुराना है। ऐड-ऑन अपडेट करें।",
    "error.dct-too-old": "आपका Durty Cloth Tool इस ऐड-ऑन के लिए बहुत पुराना है। Durty Cloth Tool अपडेट करें।",
    "error.not-authenticated": "पहले साइन इन करें।",
    "error.authentication-failed": "Durty Cloth Tool ने साइन इन स्वीकार नहीं किया। फिर कोशिश हो रही है…",
    "error.untrusted-endpoint": (
        "एक ऐसे प्रोग्राम ने जवाब दिया जो आपका Durty Cloth Tool नहीं है, इसलिए कुछ नहीं भेजा गया। ऐड-ऑन Durty Cloth "
        "Tool को खोजता रहेगा।"
    ),
    "error.account-mismatch": (
        "Durty Cloth Tool किसी दूसरे अकाउंट से साइन इन है। यहाँ साइन आउट करें और उस अकाउंट से साइन इन करें जो Durty Cloth "
        "Tool इस्तेमाल करता है।"
    ),
    "error.dct-signed-out": "Durty Cloth Tool साइन आउट है। Durty Cloth Tool में साइन इन करें; ऐड-ऑन अपने आप कनेक्ट हो जाएगा।",
    "error.token-invalid": "साइन इन की अवधि खत्म हो गई। फिर से साइन इन हो रहा है…",
    "error.needs-license": "इसके लिए Durty Cloth Tool लाइसेंस चाहिए।",
    "error.needs-ultimate": "यह Durty Cloth Tool Ultimate में शामिल है।",
    "error.no-project": "पहले Durty Cloth Tool में एक प्रोजेक्ट खोलें।",
    "error.no-focused-item": "पहले Durty Cloth Tool में एक कपड़ा चुनें।",
    "error.binding-in-use": "कोई दूसरा ऐप पहले से इस टेक्सचर या मॉडल पर काम कर रहा है।",
    "error.binding-not-found": "यह कपड़ा या टेक्सचर अब Durty Cloth Tool में मौजूद नहीं है।",
    "error.lease-not-found": "Durty Cloth Tool ने यह प्रीव्यू खत्म कर दिया। इसे फिर से शुरू करें।",
    "error.lease-limit": "बहुत ज़्यादा लाइव प्रीव्यू खुले हैं। पहले एक रोकें।",
    "error.budget-exceeded": "Durty Cloth Tool की लाइव प्रीव्यू मेमोरी भर गई है। कोई दूसरा लाइव प्रीव्यू रोकें।",
    "error.frame-out-of-bounds": "इमेज अपडेट टेक्सचर में फ़िट नहीं हुआ।",
    "error.frame-size-mismatch": "इमेज भेजी नहीं जा सकी।",
    "error.unsupported-format": "Durty Cloth Tool यहाँ यह फ़ॉर्मैट स्वीकार नहीं करता। मॉडल Sollumz YDD XML के रूप में भेजें।",
    "error.stale-revision": "नए पिक्सेल अभी रास्ते में थे। फिर से सेव करें।",
    "error.item-refused": "Durty Cloth Tool इस आइटम को एडिट नहीं कर सकता (dummy, लॉक या सुरक्षित)।",
    "error.game-required": "इसके लिए Durty Cloth Tool को आपका GTA V इंस्टॉलेशन चाहिए। इसे Durty Cloth Tool में सेट करें।",
    "error.save-failed": "Durty Cloth Tool सेव नहीं कर सका। उसके स्टेटस बार में विवरण है।",
    "error.busy": "Durty Cloth Tool व्यस्त है। थोड़ी देर में फिर कोशिश करें।",
    "error.rate-limited": "बहुत ज़्यादा अनुरोध। थोड़ा रुकें और फिर कोशिश करें।",
    "error.connection-limit": "Durty Cloth Tool से बहुत ज़्यादा ऐप कनेक्टेड हैं।",
    "error.request-denied": "Durty Cloth Tool ने अनुरोध अस्वीकार कर दिया।",
    "error.model-rejected": "Durty Cloth Tool यह मॉडल इस्तेमाल नहीं कर सका। इसे Sollumz में जाँचें और फिर से भेजें।",
    "error.internal-error": (
        "कुछ गलत हो गया। फिर कोशिश करें, और अगर ऐसा होता रहे तो Blender और Durty Cloth Tool दोबारा शुरू करें।"
    ),
    "error.disconnected": "Durty Cloth Tool से कनेक्शन टूट गया।",
    "error.timeout": "Durty Cloth Tool ने समय पर जवाब नहीं दिया।",
    "error.superseded": "एक नए अनुरोध ने इसकी जगह ले ली।",
    "error.cancelled": "रद्द किया गया।",
    "error.closed": "लाइव प्रीव्यू बंद है।",
    "error.signed-out": "आपने साइन आउट किया है। Creator Link फिर से इस्तेमाल करने के लिए साइन इन करें।",
    "error.assertion-invalid": "साइन इन पुष्ट नहीं हो सका। फिर कोशिश हो रही है…",
    "error.pixel-source-failed": "लाइव प्रीव्यू के लिए इमेज पढ़ी नहीं जा सकी। फिर कोशिश हो रही है…",
    "error.callback-failed": "ऐड-ऑन में कुछ गलत हो गया। फिर कोशिश करें।",
    "error.offline": (
        "Blender का ऑनलाइन एक्सेस बंद है। साइन इन और कनेक्ट करने के लिए इसे Preferences > System > Network में चालू करें।"
    ),
    "error.network": "gta.clothing तक नहीं पहुँचा जा सका। इंटरनेट कनेक्शन जाँचें।",
    "error.invalid-response": "gta.clothing ने अनपेक्षित जवाब भेजा। बाद में फिर कोशिश करें।",
    "error.tls": "gta.clothing से सुरक्षित कनेक्शन विफल रहा। अपना नेटवर्क, प्रॉक्सी या एंटीवायरस सेटिंग्स जाँचें।",
    "error.account_locked": "आपका gta.clothing अकाउंट लॉक है।",
    "error.discord_membership_required": (
        "Creator Link के लिए आपका Discord अकाउंट Pleb Masters Community Discord सर्वर का सदस्य होना चाहिए।"
    ),
    "error.discord_unavailable": "Discord साइन इन अभी उपलब्ध नहीं है। बाद में फिर कोशिश करें।",
    "error.plugin_update_required": "gta.clothing को इस ऐड-ऑन का नया संस्करण चाहिए। इसे अपडेट करें।",
    "error.expired_token": "साइन इन कोड की अवधि खत्म हो गई। फिर से साइन इन करें।",
    "error.access_denied": "साइन इन अस्वीकार कर दिया गया।",
    "error.invalid_grant": "साइन इन स्वीकार नहीं हुआ। फिर से साइन इन करें।",
    "error.session_invalid": "साइन इन अब मान्य नहीं है। फिर से साइन इन करें।",
    "error.session_expired": "साइन इन की अवधि खत्म हो गई। फिर से साइन इन करें।",
    "error.session_revoked": "साइन इन gta.clothing पर खत्म कर दिया गया। फिर से साइन इन करें।",
    "error.refresh_in_progress": "कोई दूसरा प्रोग्राम आपका साइन इन नवीनीकृत कर रहा है। थोड़ी देर में फिर कोशिश करें।",
    "close.closed": "लाइव प्रीव्यू रुक गया।",
    "close.replaced": "किसी दूसरे ऐप ने यह टेक्सचर ले लिया।",
    "close.itemRemoved": "कपड़ा Durty Cloth Tool में हटा दिया गया।",
    "close.projectClosed": "प्रोजेक्ट Durty Cloth Tool में बंद कर दिया गया।",
    "close.entitlementLost": "आपके प्लान में अब यह सुविधा शामिल नहीं है।",
    "close.signedOut": "Durty Cloth Tool साइन आउट हो गया, इसलिए प्रीव्यू खत्म हो गया।",
    "close.disconnected": "Durty Cloth Tool से कनेक्शन टूट गया।",
    "feature.needsLicense": "इसके लिए Durty Cloth Tool लाइसेंस चाहिए।",
    "feature.needsUltimate": "यह Durty Cloth Tool Ultimate में शामिल है।",
    "feature.unavailable": "यह आपके Durty Cloth Tool प्लान में शामिल नहीं है।",
}
