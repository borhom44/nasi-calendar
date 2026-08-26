/* GENERATED FILE -- do not edit.
 *
 * Emitted from data/strings.json by scripts/build_web.py. Edit that file and
 * re-run the script; anything typed here is overwritten without warning.
 *
 * Both languages ship in every build. The table is small enough that
 * splitting it per language would cost a request to save a few KB.
 */

const STRINGS = {
  "sun.firstLight": {"ar": "أول الضوء", "en": "First light"},
  "sun.sunrise": {"ar": "الشروق", "en": "Sunrise"},
  "sun.sunset": {"ar": "الغروب", "en": "Sunset"},
  "sun.fullDark": {"ar": "الظلام التام", "en": "Full darkness"},
  "sun.noNight": {"ar": "لا يحل الظلام التام الليلة", "en": "No astronomical night tonight"},
  "sun.noNightShort": {"ar": "ليل أبيض", "en": "White night"},
  "sun.dayLength": {"ar": "طول النهار", "en": "Day length"},
  "sun.twilight": {"ar": "مدة الشفق", "en": "Twilight"},
  "sun.longerBy": {"ar": "أطول بـ", "en": "longer by"},
  "sun.shorterBy": {"ar": "أقصر بـ", "en": "shorter by"},
  "unit.hour": {"ar": "س", "en": "h"},
  "unit.minute": {"ar": "د", "en": "m"},
  "unit.second": {"ar": "ث", "en": "s"},
  "unit.km": {"ar": "كم", "en": "km"},
  "city.label": {"ar": "المدينة:", "en": "City:"},
  "app.name": {"ar": "التقويم النسيء", "en": "Nasi’ Calendar"},
  "feed.calendarName": {"ar": "التقويم النسيء — {city}", "en": "Nasi’ Calendar — {city}"},
  "feed.eventInCity": {"ar": "{event} في {city}", "en": "{event} in {city}"},
  "tab.cycles": {"ar": "الدورات", "en": "Cycles"},
  "cycles.metonic": {"ar": "الدورة الميتونية", "en": "The Metonic cycle"},
  "cycles.yearOf": {"ar": "السنة {n} من {total}", "en": "Year {n} of {total}"},
  "cycles.metonicWhat": {"ar": "٢٣٥ شهراً قمرياً تساوي تقريباً ١٩ سنة شمسية. هذا التقارب هو ما يجعل التقويم الشمسي-القمري ممكناً أصلاً، والنسيء هو ما يصحّح الفارق الباقي.", "en": "235 lunar months come to very nearly 19 solar years. That near-coincidence is what makes a lunisolar calendar possible at all, and the نسيء month is what corrects the remainder."},
  "cycles.nextNasi": {"ar": "النسيء القادم", "en": "Next نسيء month"},
  "cycles.thisYear": {"ar": "هذه السنة", "en": "this year"},
  "cycles.inYears": {"ar": "بعد {n} سنة", "en": "in {n} years"},
  "cycles.yearNo": {"ar": "سنة {ny}", "en": "year {ny}"},
  "cycles.intercalary": {"ar": "سنة نسيء", "en": "intercalary year"},
  "cycles.driftTitle": {"ar": "رأس السنة أمام السنة الشمسية", "en": "The new year against the solar year"},
  "cycles.driftWhat": {"ar": "رأس السنة النسيئية يتأرجح داخل نافذة ثابتة من السنة الشمسية لأن النسيء يعيده إليها. أما رأس السنة الهجرية فلا يُدرج شهراً أبداً، فينزلق نحو ١١ يوماً كل سنة ويدور على الفصول الأربعة كاملةً كل ٣٣ سنة تقريباً.", "en": "The Nasi’ new year oscillates inside a fixed window of the solar year, because the نسيء month pulls it back. The Hijri new year never intercalates, so it slides about 11 days earlier every year and laps all four seasons roughly every 33."},
  "cycles.nasiNewYear": {"ar": "رأس السنة النسيئية", "en": "Nasi’ new year"},
  "cycles.hijriNewYear": {"ar": "رأس السنة الهجرية", "en": "Hijri new year"},
  "cycles.window": {"ar": "النافذة", "en": "Window"},
  "cycles.windowValue": {"ar": "بين {from} و {to} — {days} يوماً", "en": "{from} to {to} — {days} days"},
  "cycles.slipTitle": {"ar": "انزياح الدورة", "en": "Cycle slip"},
  "cycles.slipValue": {"ar": "يوم كامل كل {years} سنة", "en": "a whole day every {years} years"},
  "cycles.slipWhat": {"ar": "الدورة الميتونية ليست مضبوطة تماماً: ٢٣٥ شهراً قمرياً أطول من ١٩ سنة شمسية بنحو ساعتين وخمس دقائق، فتنزاح يوماً كاملاً كل ٢١٩ سنة. لهذا تُعلَّم التواريخ المحسوبة خارج جدول الكتاب على أنها محسوبة لا منقولة.", "en": "The Metonic cycle is not exact: 235 lunar months run about 2h 05m longer than 19 solar years, so the scheme slips a whole day every 219 years. That is why dates computed outside the book’s printed table are marked as computed rather than quoted."},
};

/* Translate. Returns the key itself on a miss and warns rather than
 * throwing: a missing string should degrade one label, not blank the page
 * mid-render. The Python side raises instead, so the build catches it
 * first and this path should not be reachable in a shipped build. */
function t(key, lang) {
  const row = STRINGS[key];
  if (!row) { console.warn('missing string: ' + key); return key; }
  return row[lang] || row.ar;
}

/* Translate and substitute {placeholders}. Unmatched placeholders are
 * left as-is rather than throwing -- the Python fmt() raises, so the
 * build already catches a template that lost an argument. */
function fmt(key, lang, vars) {
  return t(key, lang).replace(/\{(\w+)\}/g, (m, name) =>
    Object.prototype.hasOwnProperty.call(vars || {}, name) ? vars[name] : m);
}

/* The four sun events in display order, as [sunTimes key, string key].
 * Order and wording are decided in data/strings.json alone -- the same
 * tuple list the Python generator iterates. */
const SUN_EVENT_KEYS = [["firstLight", "sun.firstLight"], ["sunrise", "sun.sunrise"], ["sunset", "sun.sunset"], ["fullDark", "sun.fullDark"]];

function sunEvents(lang) {
  return SUN_EVENT_KEYS.map(([k, s]) => [k, t(s, lang)]);
}
