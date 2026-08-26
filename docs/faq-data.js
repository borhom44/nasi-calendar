/* Curated FAQ -- every answer here traces to something actually verified in
 * this project (the source PDF, the NASA eclipse catalog, or a computation
 * checked against both). No answer is speculative; where a limit exists
 * (coverage range, extrapolation, tabular-vs-observational Hijri), it's
 * stated plainly rather than smoothed over.
 *
 * Bilingual: every question and answer carries ar and en side by side, for the
 * same reason the string table does -- a wording change is one entry edited
 * twice, in view of itself, rather than two files drifting apart. faqFor(lang)
 * flattens it to the shape faq.js renders.
 */
const FAQ_CATEGORIES_ALL = [
  { ar: "أساسيات تقويم النسيء", en: "Nasi’ calendar basics" },
  { ar: "كيف بُني هذا التقويم", en: "How this was built" },
  { ar: "التحقق الفلكي", en: "Astronomical verification" },
  { ar: "العلاقة بالتقويم الهجري الرسمي", en: "Against the official Hijri calendar" },
  { ar: "استخدام التطبيق", en: "Using the app" },
];

const FAQ_ALL = [
  { cat: 0,
    q: { ar: "ما هو تقويم النسيء؟",
         en: "What is the Nasi’ calendar?" },
    a: { ar: "تقويم قمري-شمسي كان يُستخدم في الجزيرة العربية قبل الإسلام. يُدرَج فيه شهر ثالث عشر يسمى «النسيء» كل نحو ثلاث سنوات لإعادة مزامنة السنة القمرية (~354 يوماً) مع السنة الشمسية (~365 يوماً)، بحيث تبقى الأشهر ثابتة في فصولها. أبطله الإسلام (سورة التوبة 9:37).",
         en: "A lunisolar calendar used in Arabia before Islam. A thirteenth month called نسيء is inserted roughly every three years to re-synchronise the lunar year (~354 days) with the solar one (~365 days), so that the months stay fixed in their seasons. Islam abolished it (Qur’an 9:37)." } },
  { cat: 0,
    q: { ar: "لماذا لا يوجد شهر «المحرم» في هذا التقويم؟",
         en: "Why is there no month called Muharram here?" },
    a: { ar: "بحسب جدول المصدر (كتاب «براءة النسيء»)، «المحرم» ليس شهراً ثابتاً هنا، بل هو الاسم الذي يأخذه شهر النسيء نفسه عند وقوعه في المرتبة 13 (قبيل بداية السنة الجديدة مباشرة). لذلك حمل الشهر الذي يفتتح السنة اسم «صفر الأول» ثم «صفر الثاني»، لتبدأ السنة القمرية بعد انتهاء شعائر الحج مباشرة.",
         en: "In the source table (the book Barā’at al-Nasī’), Muharram is not a fixed month at all. It is the name the نسيء month takes when it falls in position 13, immediately before the new year. That is why the year opens with Safar I and Safar II instead — so the lunar year begins right after the rites of Hajj end." } },
  { cat: 0,
    q: { ar: "أين يمكن أن يقع شهر النسيء بالضبط؟",
         en: "Where exactly can the نسيء month fall?" },
    a: { ar: "في ثلاثة مواضع ثابتة فقط: المرتبة 13 (بين ذي الحجة وبداية السنة، ويُسمى «المحرم»)، المرتبة 9 (بين شعبان ورمضان، ويُسمى «رجب مضر»)، أو المرتبة 5 (بين ربيع الثاني وجمادى الأولى، ويُسمى «رجب ربيعة»). لكن الجدول نفسه يطبع دائماً التسمية العامة «نسيء» في الحالات الثلاث، وهذا ما يعرضه هذا التطبيق.",
         en: "In exactly three fixed positions: 13th (between Dhu al-Hijja and the new year, called Muharram), 9th (between Shaʿban and Ramadan, called Rajab Mudar), or 5th (between Rabiʿ II and Jumada I, called Rajab Rabiʿa). The table itself always prints the generic name نسيء in all three cases, and that is what this app shows." } },
  { cat: 0,
    q: { ar: "هل صحيح أن رمضان قد يُسبَق مباشرة بشهر النسيء؟",
         en: "Can Ramadan really be preceded directly by the نسيء month?" },
    a: { ar: "نعم، وهذا موثّق في الكتاب نفسه (المرتبة 9، «رجب مضر»)، وليس خطأ. تحقّقنا من هذا بمقارنة مباشرة مع صفحة الجدول المصدر لعام 2026.",
         en: "Yes, and it is documented in the book itself (position 9, Rajab Mudar) rather than being a mistake. It was checked directly against the source table’s page for 2026." } },

  { cat: 1,
    q: { ar: "هل هذا التقويم نسخة من الكتاب أم أُعيد بناؤه؟",
         en: "Is this a copy of the book, or a reconstruction?" },
    a: { ar: "البيانات اليومية مستخرجة برمجياً من جدول 2000-2100 الملحق بالكتاب، عبر قراءة كل رقم بموقعه ولونه في ملف الـPDF، ثم تسمية كل شهر مباشرة من تسميته المطبوعة في الجدول نفسه — 1,250 من أصل 1,251 شهراً مُسمّى من مصدره مباشرة، لا استنتاجاً من نمط متكرر.",
         en: "The daily data is extracted programmatically from the book’s 2000–2100 table, reading every number by its position and colour in the PDF, then naming each month from its own printed label — 1,250 of 1,251 months named directly from the source rather than inferred from a repeating pattern." } },
  { cat: 1,
    q: { ar: "هل حدثت أخطاء أثناء البناء؟ وكيف اكتُشفت؟",
         en: "Were there mistakes along the way, and how were they caught?" },
    a: { ar: "نعم، خطآن رئيسيان جرى تصحيحهما: الأول تسمية أول شهرين بـ«المحرم/صفر» بدل «صفر الأول/صفر الثاني» — اكتُشف بقراءة شرح الكتاب نفسه. الثاني انزياح كل أسماء الأشهر عبر المائة عام بمقدار شهر واحد كامل، لأن نصف تسميات الجدول لم تُقرأ (كانت متلاصقة نصياً) — اكتُشف عندما لاحظ المستخدم أن توقيت النسيء قبل رمضان 2026 يبدو مختلفاً، فقارنّا مباشرة مع صورة من الجدول المصدر ووجدنا أن كل تاريخ يحمل اسم الشهر التالي بدل اسمه الصحيح.",
         en: "Two significant ones, both fixed. First, the opening two months were named Muharram/Safar instead of Safar I/Safar II — caught by reading the book’s own explanation. Second, every month name across the whole century was shifted by exactly one month, because half the table’s labels had not been read at all (they ran together in the text layer). That one surfaced when the user noticed the نسيء placement before Ramadan 2026 looked wrong; comparing against an image of the source page showed every date carrying the following month’s name." } },
  { cat: 1,
    q: { ar: "كيف تم التأكد من عدم تكرار هذا النوع من الأخطاء؟",
         en: "What stops that class of error recurring?" },
    a: { ar: "بعد الإصلاح، أُعيد البناء بحيث يُسمّى كل شهر من تسميته المطبوعة في الجدول مباشرة (لا بالحساب التسلسلي من نقطة انطلاق واحدة)، مع فرض أن يتطابق الناتج مع دورة الأشهر الاثني عشر دون أي تعارض، وأن تقع كل فجوات النسيء في مواضعها الثلاثة المسموحة فقط (5، 9، 13). النتيجة: صفر تعارضات، وكل التواريخ المُتحقَّق منها يدوياً من الجدول تطابقت.",
         en: "After the fix the build was redone so that every month takes its name from its own printed label rather than by counting forward from one starting point, with two constraints enforced: the result must agree with the twelve-month cycle without a single conflict, and every نسيء insertion must land in one of the three permitted slots (5, 9, 13). Result: zero conflicts, and every date checked by hand against the table matched." } },

  { cat: 2,
    q: { ar: "هل تحققتم من مطابقة هذا التقويم لحركة القمر الحقيقية؟",
         en: "Was this checked against the Moon’s actual motion?" },
    a: { ar: "نعم، بمعزل تام عن الكتاب: قورنت بدايات جميع الأشهر الـ1,250 بأوقات المحاق (الاقتران) الفلكية الحقيقية (خوارزمية Meeus). كل شهر يبدأ صفر إلى ثلاثة أيام بعد المحاق الحقيقي (الغالبية يوماً واحداً)، ولا يوجد شهر واحد يبدأ قبل محاقه — وهذا يطابق تماماً تقويماً يعتمد رؤية الهلال.",
         en: "Yes, entirely independently of the book: all 1,250 month starts were compared against real astronomical new moons (Meeus). Every month begins zero to three days after its true conjunction, most of them one day after, and not a single month begins before its own new moon — exactly the signature of a calendar following the crescent." } },
  { cat: 2,
    q: { ar: "هل تحققتم من طول الأشهر مقابل بيانات فلكية حقيقية؟",
         en: "Were the month lengths checked against real astronomical data?" },
    a: { ar: "نعم، عبر كتالوج ناسا الرسمي لخسوفات القمر عبر خمسة آلاف عام (Espenak و Meeus، NASA/TP-2009-214173). الخسوف القمري لا يحدث إلا عند اكتمال القمر: من أصل 230 خسوفاً حقيقياً بين 2000-2100، وقع 99.6% منها في اليوم 14 أو 15 من هذا التقويم، و100% بين اليوم 13 والـ16.",
         en: "Yes, against NASA’s five-millennium catalogue of lunar eclipses (Espenak & Meeus, NASA/TP-2009-214173). A lunar eclipse can only happen at full moon: of 230 real eclipses between 2000 and 2100, 99.6% fell on day 14 or 15 of this calendar, and 100% between day 13 and day 16." } },
  { cat: 2,
    q: { ar: "هل يحافظ هذا التقويم فعلياً على تثبيت السنة مع الفصول؟",
         en: "Does it actually hold the year against the seasons?" },
    a: { ar: "نعم بدرجة كبيرة: بداية كل سنة محصورة ضمن نافذة 28 يوماً فقط عبر المائة عام (16 يناير – 13 فبراير)، مقابل تقويم قمري بحت كان سينجرف نحو 1,100 يوم خلال نفس الفترة — أي يدور عبر كل الفصول عدة مرات.",
         en: "Substantially, yes. Across the whole century the new year stays inside a 28-day window (16 January to 13 February), where a purely lunar calendar would have drifted about 1,100 days over the same span — several full circuits of the seasons." } },
  { cat: 2,
    q: { ar: "ما مدى دقة طول الشهر والسنة المستنتجَين من هذا الجدول؟",
         en: "How accurate are the month and year lengths this table implies?" },
    a: { ar: "متوسط طول الشهر عبر 1,249 شهراً = 29.530024 يوماً، مقابل الشهر القمري الحقيقي البالغ 29.530589 يوماً — خطأ 49 ثانية فقط لكل شهر. متوسط طول السنة = 365.290 يوماً مقابل السنة الشمسية الحقيقية 365.24219 يوماً — أي انجراف نحو 4.8 أيام فقط لكل قرن.",
         en: "The mean month over 1,249 months is 29.530024 days against a true synodic month of 29.530589 — an error of 49 seconds per month. The mean year is 365.290 days against a true tropical year of 365.24219, a drift of about 4.8 days per century." } },
  { cat: 2,
    q: { ar: "هل تثبت هذه الدقة أن التقويم صحيح تاريخياً؟",
         en: "Does that accuracy prove the calendar is historically correct?" },
    a: { ar: "لا. هذه الاختبارات تثبت أن القاعدة الفلكية (شهر قمري حقيقي + نسيء كل نحو ثلاث سنوات لتثبيت السنة الشمسية) سليمة فلكياً بين 2000-2100، لكنها لا تثبت أن هذا هو بالضبط النظام التاريخي المستخدَم قبل الإسلام، ولا صحة ترقيم السنين تاريخياً. الفلك يجيب عن سؤال، والتاريخ يجيب عن سؤال آخر.",
         en: "No. These tests show the astronomical rule — a real lunar month plus a نسيء insertion every three years or so to hold the solar year — is sound between 2000 and 2100. They do not show that this was exactly the system used before Islam, nor that the year numbering is historically right. Astronomy answers one question; history answers a different one." } },

  { cat: 3,
    q: { ar: "ما الفرق بينه وبين التقويم الهجري الرسمي المعروف اليوم؟",
         en: "How does this differ from the official Hijri calendar?" },
    a: { ar: "كلاهما يتبع نفس الأهلة الحقيقية، لكن الهجري الرسمي لا يُدرج أي شهر إضافي أبداً، بينما هذا التقويم يُدرج «النسيء» كل نحو ثلاث سنوات. لذلك ينجرف الهجري الرسمي عبر كل فصول السنة كل 33 سنة تقريباً، بينما يبقى هذا التقويم مرتبطاً بمواسمه.",
         en: "Both follow the same real new moons, but the official Hijri calendar never inserts an extra month while this one inserts نسيء roughly every three years. So the official Hijri date drifts through all four seasons about every 33 years, while this calendar stays tied to its seasons." } },
  { cat: 3,
    q: { ar: "لماذا تختلف أرقام السنين بينهما اليوم؟",
         en: "Why do the year numbers differ today?" },
    a: { ar: "لأن طول السنة يختلف (نحو 354.4 يوماً في الهجري الرسمي مقابل نحو 365.3 يوماً هنا)، يتراكم فارق سنة كاملة كل نحو 27 سنة هجرية تقريباً. بعد نحو 1,400 سنة من الهجرة، بلغ الفارق التراكمي نحو 43 سنة.",
         en: "Because the year lengths differ — about 354.4 days in the official Hijri calendar against about 365.3 here — a whole year accumulates roughly every 27 Hijri years. Some 1,400 years after the Hijra the gap has reached about 43 years." } },
  { cat: 3,
    q: { ar: "متى أُلغي نظام النسيء تاريخياً بحسب هذا التقويم؟",
         en: "When was the نسيء system abolished, on this calendar’s own reckoning?" },
    a: { ar: "بحساب عدد الأشهر التي «أدرجها» هذا التقويم ولم يُدرجها الهجري الرسمي، وقسمة ذلك على معدل إدراج ثابت مضبوط تماماً عبر الجدول كله (7 إدراجات كل 19 سنة)، نحصل على تقدير: نحو السنة 19-25 هـ (حوالي 640-645م). هذا قريب من الرواية التاريخية (الإلغاء عند حجة الوداع، 10هـ/632م)، لكنه استقراء لمعدل ثابت عبر 14 قرناً وليس بيانات فعلية من تلك الحقبة — خطأ سنة واحدة في المعدل يزيح التقدير نحو 2.7 سنة.",
         en: "Counting the months this calendar inserts that the official Hijri one does not, and dividing by an insertion rate that holds exactly across the whole table (7 insertions every 19 years), gives an estimate of roughly 19–25 AH, about 640–645 CE. That is close to the historical account — abolition at the Farewell Pilgrimage, 10 AH / 632 CE — but it extrapolates a constant rate across fourteen centuries rather than resting on data from that era. A one-year error in the rate moves the estimate by about 2.7 years." } },
  { cat: 3,
    q: { ar: "هل يوم 14 أكتوبر يقع دائماً ضمن رمضان في هذا التقويم؟",
         en: "Does 14 October always fall within Ramadan here?" },
    a: { ar: "من أصل 101 رمضان بين 2000-2100، يقع 14 أكتوبر ضمن 100 منها. الاستثناء الوحيد: رمضان 1383 (2004) الذي انتهى في 13 أكتوبر بالضبط. في أي نافذة 50 سنة تستبعد ذلك الاستثناء، يقع 14 أكتوبر ضمن كل رمضان بلا استثناء — نتيجة طبيعية لأن نافذة بداية رمضان (15 سبتمبر إلى 14 أكتوبر) وطوله (29-30 يوماً) شبه متساويين.",
         en: "Of 101 Ramadans between 2000 and 2100, 14 October falls inside 100 of them. The single exception is Ramadan 1383 (2004), which ended on 13 October exactly. In any 50-year window excluding that one, 14 October falls inside every Ramadan — a natural consequence of Ramadan’s start window (15 September to 14 October) and its length (29–30 days) being almost equal." } },

  { cat: 4,
    q: { ar: "ما مدى التغطية الزمنية لهذا التقويم؟",
         en: "What date range does this cover?" },
    a: { ar: "جدول المصدر يغطي 1999-12-09 إلى 2100-12-31، وهو المرجع داخل هذا النطاق. خارجه يمتد التطبيق حسابياً من 1600 إلى 2200 بقاعدة رياضية معلنة، وتُعلَّم تلك التواريخ على الشاشة بأنها محسوبة لا منقولة من الكتاب.",
         en: "The source table runs 1999-12-09 to 2100-12-31 and is authoritative inside that range. Outside it the app extends computationally from 1600 to 2200 using a stated rule, and those dates are marked on screen as computed rather than quoted from the book." } },
  { cat: 4,
    q: { ar: "هل التاريخ الهجري المعروض هو نفسه المعتمد في بلدي؟",
         en: "Is the Hijri date shown the same one my country uses?" },
    a: { ar: "التاريخ الهجري هنا حسابي بالكامل (التقويم الجدولي ذو الدورة الثابتة 30 سنة)، وقد يختلف يوماً أو يومين عن تقويم «أم القرى» أو عن لجان الرؤية المحلية التي تعتمد رؤية الهلال فعلياً. اعتبره مرجعاً حسابياً لا إعلاناً رسمياً لبداية الشهر.",
         en: "The Hijri date here is purely arithmetic — the tabular calendar with its fixed 30-year cycle — and can differ by a day or two from Umm al-Qura or from local sighting committees that rely on actually seeing the crescent. Treat it as a computed reference, not an official announcement of a month’s start." } },
  { cat: 4,
    q: { ar: "لماذا لا يظهر أول الضوء أو الظلام التام في بعض المدن صيفاً؟",
         en: "Why do first light and full darkness disappear in some cities in summer?" },
    a: { ar: "لأن الظلام الفلكي لا يحل هناك أصلاً. فوق خط عرض 48.56° شمالاً (= 90 − 23.44 − 18) لا تهبط الشمس إلى 18° تحت الأفق في ذروة الصيف، فلا يوجد ليل فلكي تام لتُحسب بدايته أو نهايته. هذه حقيقة فلكية لا نقص في البيانات، ولذلك يُكتب «ليل أبيض» بدل وقت وهمي. بالقياس لسنة كاملة: برلين 69 يوماً، لندن 59، باريس 19، وصفر في كل مدينة أخرى في القائمة.",
         en: "Because astronomical darkness never arrives there. Above 48.56° N (= 90 − 23.44 − 18) the sun does not reach 18° below the horizon at midsummer, so there is no astronomical night whose beginning or end could be computed. That is a fact about the sky, not missing data, which is why the app says “white night” instead of inventing a time. Measured over a full year: Berlin 69 days, London 59, Paris 19, and zero for every other city on the list." } },
  { cat: 4,
    q: { ar: "كيف تُحسب أحداث الشمس الأربعة؟",
         en: "How are the four sun events computed?" },
    a: { ar: "فلكياً بالكامل (خوارزمية NOAA) دون أي واجهة خارجية، وبتعريف واحد لكل حدث لا اصطلاح فيه ولا اختيار. أول الضوء والظلام التام عند انخفاض الشمس 18° تحت الأفق (بداية الشفق الفلكي ونهايته)، والشروق والغروب عند ارتفاع -0.833° الذي يراعي الانكسار الجوي ونصف قطر الشمس — فالشروق ليس عند الارتفاع صفر. هذا تقويم فلكي لا تطبيق مواقيت صلاة، ولذلك لا توجد هنا اصطلاحات إقليمية أو فقهية تُختار. المنطقة الزمنية والتوقيت الصيفي مأخوذان من قاعدة بيانات IANA الحقيقية.",
         en: "Entirely astronomically (the NOAA algorithm), with no external service and exactly one definition per event — nothing regional or juristic to choose. First light and full darkness are the sun 18° below the horizon, the beginning and end of astronomical twilight. Sunrise and sunset are −0.833°, which allows for atmospheric refraction and the sun’s own radius: sunrise is not altitude zero. This is an astronomical calendar, not a prayer-times app. Timezones and daylight saving come from the real IANA database." } },
  { cat: 4,
    q: { ar: "هل بيانات القمر (الإضاءة، البدر، الخسوف) جزء من تقويم النسيء؟",
         en: "Is the moon data part of the Nasi’ calendar?" },
    a: { ar: "لا، بشكل مقصود: طور القمر الفعلي في أي يوم ميلادي فلك مستقل تماماً عن أي تقويم يُقرأ من خلاله. حُسب بنفس خوارزمية Meeus المستخدمة في اختبارات التحقق الفلكي، والإضاءة محسوبة من الاستطالة الحقيقية للقمر عن الشمس لا من نسبة تقريبية للدورة.",
         en: "Deliberately not. The Moon’s actual phase on any given Gregorian day is astronomy, entirely independent of whichever calendar you read it through. It uses the same Meeus series as the verification tests, and illumination comes from the Moon’s true elongation from the Sun rather than from an idealised fraction of the lunation." } },
  { cat: 4,
    q: { ar: "لماذا لا تظهر أحداث مثل أرباع القمر؟",
         en: "Why are the quarter moons not shown?" },
    a: { ar: "نعرض حالياً فقط المحاق (بداية الدورة)، والبدر (اكتمالها)، والخسوف القمري الحقيقي من كتالوج ناسا — الأحداث الثلاثة التي تحقّقت دقتها مباشرة. الأرباع الأول والأخير تحتاج معادلة مختلفة لم تُضَف بعد.",
         en: "Only new moon, full moon and real lunar eclipses from the NASA catalogue are marked as events — the three whose accuracy was verified directly. First and last quarter need a different series that has not been added yet. The phase icon on every cell does show the quarters as they happen." } },
  { cat: 4,
    q: { ar: "كيف أضيف هذا التقويم إلى Google Calendar؟",
         en: "How do I add this to Google Calendar?" },
    a: { ar: "من قسم «أضِف التقويم إلى تقويمك»: اختر اللغة والمدينة، انسخ الرابط، ثم في Google Calendar من كمبيوتر اختر «تقويمات أخرى» ← + ← «من عنوان URL». استخدم «من عنوان URL» ولا تستخدم «استيراد»: الاشتراك يُنشئ تقويماً مستقلاً يمكن إلغاؤه بضغطة، ويتحدث تلقائياً، أما الاستيراد فينسخ آلاف الأحداث داخل تقويمك بلا طريقة لحذفها دفعة واحدة.",
         en: "From the “Add this to your calendar” section: pick a language and a city, copy the link, then in Google Calendar on a computer choose Other calendars → + → From URL. Use From URL, not Import. Subscribing creates a separate calendar you can remove in one click and which updates itself; importing copies thousands of events into your own calendar with no way to delete them in bulk." } },
  { cat: 4,
    q: { ar: "هل يمكن اعتماد هذا التقويم مرجعاً دينياً لبداية رمضان أو الأعياد؟",
         en: "Can this be used as a religious reference for Ramadan or the Eids?" },
    a: { ar: "لا. هذا مشروع بحثي وتقني لإعادة بناء نظام تقويمي تاريخي والتحقق منه فلكياً، وليس فتوى أو مرجعاً شرعياً. التقويم الهجري الرسمي، لا هذا التقويم، هو المعتمد دينياً وعملياً اليوم.",
         en: "No. This is a research and engineering project reconstructing a historical calendar system and verifying it astronomically. It is not a religious ruling or authority. The official Hijri calendar, not this one, is what is followed religiously and practically today." } },
];

/* Flattened to the single-language shape faq.js renders. */
function faqCategories(lang) {
  return FAQ_CATEGORIES_ALL.map((c) => c[lang] || c.ar);
}

function faqEntries(lang) {
  return FAQ_ALL.map((e) => ({
    cat: e.cat,
    q: e.q[lang] || e.q.ar,
    a: e.a[lang] || e.a.ar,
  }));
}

/* Back-compat for any caller that still reads the flat globals directly.
 * These are the Arabic view; anything language-aware calls faqEntries(). */
const FAQ_CATEGORIES = faqCategories("ar");
const FAQ_DATA = faqEntries("ar");
