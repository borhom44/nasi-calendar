/* Sun times -- JS port of scripts/solar_times.py. Same NOAA algorithm, same
 * event definitions; see that file's docstring for why each angle is what it is.
 *
 * Four events, one astronomical definition each. There are no conventions to
 * choose: this is not a prayer-times app, so nothing here is regional,
 * juristic, or configurable.
 *
 * Time zones: solved in UTC, then rendered via Intl.DateTimeFormat with an
 * explicit IANA zone, which uses the browser's own tz database -- so DST
 * (e.g. Cairo's reinstated EEST) is handled from real rules, not a fixed
 * offset, exactly like the Python side's zoneinfo.
 */
const RAD = Math.PI / 180;
const SUN_DISC = -0.833;      // upper limb on the horizon
const TWILIGHT = -18.0;       // astronomical twilight, both ends

/* CITIES now comes from the generated cities-data.js, which is emitted from
 * data/cities.json -- the single registry. It used to be declared here AND in
 * generate_ics_full.py, so a coordinate could differ between the app and the
 * feed with nothing to catch it. cities-data.js must load before this file. */

function _solarParams(jd) {
  const T = (jd - 2451545.0) / 36525.0;
  const L0 = (280.46646 + T * (36000.76983 + T * 0.0003032)) % 360.0;
  const M = 357.52911 + T * (35999.05029 - 0.0001537 * T);
  const e = 0.016708634 - T * (0.000042037 + 0.0000001267 * T);
  const C = Math.sin(M*RAD) * (1.914602 - T*(0.004817 + 0.000014*T))
          + Math.sin(2*M*RAD) * (0.019993 - 0.000101*T)
          + Math.sin(3*M*RAD) * 0.000289;
  const omega = 125.04 - 1934.136 * T;
  const lam = L0 + C - 0.00569 - 0.00478 * Math.sin(omega*RAD);
  const eps0 = 23.0 + (26.0 + (21.448 - T*(46.815 + T*(0.00059 - T*0.001813)))/60)/60;
  const eps = eps0 + 0.00256 * Math.cos(omega*RAD);
  const decl = Math.asin(Math.sin(eps*RAD) * Math.sin(lam*RAD)) / RAD;
  const y = Math.tan(eps/2*RAD) ** 2;
  const eqtime = 4 * (y*Math.sin(2*L0*RAD) - 2*e*Math.sin(M*RAD)
               + 4*e*y*Math.sin(M*RAD)*Math.cos(2*L0*RAD)
               - 0.5*y*y*Math.sin(4*L0*RAD) - 1.25*e*e*Math.sin(2*M*RAD)) / RAD;
  return { decl, eqtime };
}

function _jdUTC(y, m, d) {
  if (m <= 2) { y -= 1; m += 12; }
  const a = Math.floor(y / 100), b = 2 - a + Math.floor(a / 4);
  return Math.floor(365.25*(y+4716)) + Math.floor(30.6001*(m+1)) + d + b - 1524.5;
}

function _hourAngle(lat, decl, altitude) {
  const cosH = (Math.sin(altitude*RAD) - Math.sin(lat*RAD)*Math.sin(decl*RAD))
             / (Math.cos(lat*RAD)*Math.cos(decl*RAD));
  if (cosH < -1 || cosH > 1) return null;
  return Math.acos(cosH) / RAD;
}

/* iso: "YYYY-MM-DD" LOCAL civil date at the given location. Returns
 * {firstLight,sunrise,sunset,fullDark}: JS Date objects (UTC instants).
 *
 * firstLight/fullDark are null above ~48.56 deg N at midsummer, where the sun
 * never reaches -18 -- the night genuinely never falls. That is a fact to
 * display, not an error to paper over; see the white-nights note in PLAN.md. */
function sunTimes(iso, cityKey) {
  const city = CITIES[cityKey];
  const y = +iso.slice(0,4), m = +iso.slice(5,7), d = +iso.slice(8,10);
  const jd = _jdUTC(y, m, d) + 0.5 - city.lon / 360.0;
  const { decl, eqtime } = _solarParams(jd);
  const noonUTC = 720.0 - 4.0 * city.lon - eqtime;   // minutes past 00:00 UTC on `iso`

  const at = (minutes) => minutes === null ? null
    : new Date(Date.UTC(y, m - 1, d) + minutes * 60000);

  const hDark = _hourAngle(city.lat, decl, TWILIGHT);
  const hRise = _hourAngle(city.lat, decl, SUN_DISC);

  return {
    firstLight: at(hDark === null ? null : noonUTC - 4*hDark),
    sunrise:    at(hRise === null ? null : noonUTC - 4*hRise),
    sunset:     at(hRise === null ? null : noonUTC + 4*hRise),
    fullDark:   at(hDark === null ? null : noonUTC + 4*hDark),
  };
}

/* Labels live in data/strings.json, not here. Call sunEvents(lang) from the
 * generated strings-data.js for [key, label] pairs in display order -- this
 * file computes instants and knows nothing about how they are worded. */

/* Why an event is missing, which is NOT always the same reason.
 *
 * Any null used to be reported as a white night. That is right for first light
 * and full darkness above 48.56 deg, but at a polar latitude a missing SUNRISE
 * means the sun never came up at all -- the exact opposite. Svalbard on 21
 * December was being told it had no darkness while sitting in permanent night.
 *
 * Both follow from the sun's altitude at the two culminations:
 *   upper (local noon)     90 - |lat - dec|
 *   lower (local midnight) |lat + dec| - 90
 */
function sunSituation(iso, cityKey) {
  const city = CITIES[cityKey];
  const y = +iso.slice(0, 4), m = +iso.slice(5, 7), d = +iso.slice(8, 10);
  const jd = _jdUTC(y, m, d) + 0.5 - city.lon / 360.0;
  const { decl } = _solarParams(jd);
  const noonAlt = 90 - Math.abs(city.lat - decl);
  const midnightAlt = Math.abs(city.lat + decl) - 90;
  return {
    polarNight: noonAlt < SUN_DISC,        // the sun never clears the horizon
    polarDay: midnightAlt > SUN_DISC,      // the sun never drops below it
    whiteNight: midnightAlt > TWILIGHT && midnightAlt <= SUN_DISC,
  };
}

function fmtLocal(date, tz) {
  if (!date) return "--:--";
  // NASI_CLOCK12 and nasiMeridiem are set by the app; this file loads first, so
  // both are read defensively and 24-hour is the behaviour without them.
  const h12 = typeof NASI_CLOCK12 !== "undefined" && NASI_CLOCK12;
  if (!h12) {
    return new Intl.DateTimeFormat("en-GB", { timeZone: tz, hour: "2-digit", minute: "2-digit", hour12: false }).format(date);
  }
  // The am/pm marker is translated rather than taken from the locale: en-GB
  // keeps the Western digits the whole app uses, but would print "am" on an
  // Arabic screen where the reader expects ص.
  const parts = new Intl.DateTimeFormat("en-GB", {
    timeZone: tz, hour: "numeric", minute: "2-digit", hour12: true,
  }).formatToParts(date);
  const get = (k) => (parts.find((x) => x.type === k) || {}).value || "";
  const mark = typeof nasiMeridiem === "function" ? nasiMeridiem(get("dayPeriod")) : get("dayPeriod");
  return `${get("hour")}:${get("minute")} ${mark}`.trim();
}
