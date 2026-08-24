/* Official (tabular/civil) Islamic calendar <-> Gregorian.
 *
 * This is the standard arithmetic scheme: a fixed 30-year cycle with 11 leap
 * years, epoch 1 Muharram 1 AH = Friday 16 July 622 CE (Julian). It is what
 * almost every "Hijri date" widget uses.
 *
 * It is NOT the observational calendar. Saudi Umm al-Qura and local
 * moon-sighting committees can differ from this by a day, occasionally two,
 * because they depend on actual crescent visibility. Treat the Hijri row here
 * as the arithmetic reference, not as an announcement of when a month starts.
 */
const HIJRI_MONTHS = [
  "المحرم", "صفر", "ربيع الأول", "ربيع الآخر", "جمادى الأولى", "جمادى الآخرة",
  "رجب", "شعبان", "رمضان", "شوال", "ذو القعدة", "ذو الحجة",
];
const ISLAMIC_EPOCH_JD = 1948439.5;

function gregToJD(y, m, d) {
  if (m <= 2) { y -= 1; m += 12; }
  const a = Math.floor(y / 100);
  const b = 2 - a + Math.floor(a / 4);
  return Math.floor(365.25 * (y + 4716)) + Math.floor(30.6001 * (m + 1)) + d + b - 1524.5;
}

function jdToGreg(jd) {
  const z = Math.floor(jd + 0.5);
  const alpha = Math.floor((z - 1867216.25) / 36524.25);
  const a = z < 2299161 ? z : z + 1 + alpha - Math.floor(alpha / 4);
  const b = a + 1524;
  const c = Math.floor((b - 122.1) / 365.25);
  const dd = Math.floor(365.25 * c);
  const e = Math.floor((b - dd) / 30.6001);
  const day = b - dd - Math.floor(30.6001 * e);
  const month = e < 14 ? e - 1 : e - 13;
  const year = month > 2 ? c - 4716 : c - 4715;
  return { y: year, m: month, d: day };
}

function islamicToJD(y, m, d) {
  return d + Math.ceil(29.5 * (m - 1)) + (y - 1) * 354
       + Math.floor((3 + 11 * y) / 30) + ISLAMIC_EPOCH_JD - 1;
}

function jdToIslamic(jd) {
  jd = Math.floor(jd) + 0.5;
  let y = Math.floor((30 * (jd - ISLAMIC_EPOCH_JD) + 10646) / 10631);
  let m = Math.max(1, Math.min(12, Math.ceil((jd - islamicToJD(y, 1, 1) + 1) / 29.5)));
  let d = Math.floor(jd - islamicToJD(y, m, 1)) + 1;
  // The 29.5-day average over-estimates the month on the LAST day of a
  // 30-day month, producing day 0 of the next month (~6 days a year).
  // Walk back until the day is valid rather than trusting the estimate.
  while (d < 1) {
    m -= 1;
    if (m < 1) { y -= 1; m = 12; }
    d = Math.floor(jd - islamicToJD(y, m, 1)) + 1;
  }
  return { y: y, m: m, d: d };
}

/* ISO "YYYY-MM-DD" -> {y,m,d} official Hijri */
function gregorianToHijri(iso) {
  const y = +iso.slice(0, 4), m = +iso.slice(5, 7), d = +iso.slice(8, 10);
  return jdToIslamic(gregToJD(y, m, d));
}

/* official Hijri -> ISO "YYYY-MM-DD" */
function hijriToGregorian(y, m, d) {
  const g = jdToGreg(islamicToJD(y, m, d));
  return `${String(g.y).padStart(4, "0")}-${String(g.m).padStart(2, "0")}-${String(g.d).padStart(2, "0")}`;
}
