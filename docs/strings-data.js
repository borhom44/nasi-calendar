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

/* The four sun events in display order, as [sunTimes key, string key].
 * Order and wording are decided in data/strings.json alone -- the same
 * tuple list the Python generator iterates. */
const SUN_EVENT_KEYS = [["firstLight", "sun.firstLight"], ["sunrise", "sun.sunrise"], ["sunset", "sun.sunset"], ["fullDark", "sun.fullDark"]];

function sunEvents(lang) {
  return SUN_EVENT_KEYS.map(([k, s]) => [k, t(s, lang)]);
}
