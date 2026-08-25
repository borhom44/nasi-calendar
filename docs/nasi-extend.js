/* Computed extension of the Nasi' calendar beyond the printed table.
 *
 * The table in "Bara'at al-Nasi'" covers 2000-2100 and is the authority inside
 * that range. Outside it, months are COMPUTED from a stated rule. The two do
 * not agree perfectly -- the best rule found reproduces only 61.5% of the
 * printed month starts, the rest differing by a single day -- so computed dates
 * are marked as such in the UI and must never be presented as the book's.
 *
 * The rule, stated plainly:
 *   1. A month begins on the civil day (UTC) that contains the astronomical
 *      new moon, plus one day.
 *   2. A year has 13 months when (year mod 19) is one of {2,4,7,10,12,15,18},
 *      with نسيء inserted at position 5, 13, 9, 5, 13, 13, 9 respectively.
 *      This rule was DERIVED from the table, where it holds for all 37
 *      insertions across five Metonic cycles, so it is the book's own rule.
 *
 * Only rule 1 is an approximation. Rule 2 is exact.
 */

const NASI_CYCLE_12 = [
  "صفر الأول", "صفر الثاني", "ربيع الأول", "ربيع الثاني",
  "جمادى الأولى", "جمادى الثانية", "رجب", "شعبان",
  "رمضان", "شوال", "ذو القعدة", "ذو الحجة",
];
const NASI_MONTH_LABEL = "نسيء";

/* residue mod 19 -> 1-based position نسيء occupies in that year */
const NASI_INTERCALARY = { 2: 5, 4: 13, 7: 9, 10: 5, 12: 13, 15: 13, 18: 9 };

function nasiMonthNamesForYear(ny) {
  const pos = NASI_INTERCALARY[((ny % 19) + 19) % 19];
  const names = NASI_CYCLE_12.slice();
  if (pos) names.splice(pos - 1, 0, NASI_MONTH_LABEL);
  return names;
}

/* Espenak & Meeus polynomials (NASA/TP-2009-214173). moon-events.js carries a
 * short version valid only 2005-2150, which is all the printed range needed;
 * extending centuries needs the full set, or the conjunction instants drift by
 * enough to move a month boundary. Year 1500: the short version gives ~1300 s,
 * the true value is ~198 s. */
function deltaTExtended(y) {
  let u, t;
  if (y < -500)  { u = (y - 1820) / 100; return -20 + 32 * u * u; }
  if (y < 500)   { u = y / 100; return 10583.6 - 1014.41 * u + 33.78311 * u ** 2
                     - 5.952053 * u ** 3 - 0.1798452 * u ** 4 + 0.022174192 * u ** 5
                     + 0.0090316521 * u ** 6; }
  if (y < 1600)  { u = (y - 1000) / 100; return 1574.2 - 556.01 * u + 71.23472 * u ** 2
                     + 0.319781 * u ** 3 - 0.8503463 * u ** 4 - 0.005050998 * u ** 5
                     + 0.0083572073 * u ** 6; }
  if (y < 1700)  { t = y - 1600; return 120 - 0.9808 * t - 0.01532 * t ** 2 + t ** 3 / 7129; }
  if (y < 1800)  { t = y - 1700; return 8.83 + 0.1603 * t - 0.0059285 * t ** 2
                     + 0.00013336 * t ** 3 - t ** 4 / 1174000; }
  if (y < 1860)  { t = y - 1800; return 13.72 - 0.332447 * t + 0.0068612 * t ** 2
                     + 0.0041116 * t ** 3 - 0.00037436 * t ** 4 + 0.0000121272 * t ** 5
                     - 0.0000001699 * t ** 6 + 0.000000000875 * t ** 7; }
  if (y < 1900)  { t = y - 1860; return 7.62 + 0.5737 * t - 0.251754 * t ** 2
                     + 0.01680668 * t ** 3 - 0.0004473624 * t ** 4 + t ** 5 / 233174; }
  if (y < 1920)  { t = y - 1900; return -2.79 + 1.494119 * t - 0.0598939 * t ** 2
                     + 0.0061966 * t ** 3 - 0.000197 * t ** 4; }
  if (y < 1941)  { t = y - 1920; return 21.20 + 0.84493 * t - 0.076100 * t ** 2 + 0.0020936 * t ** 3; }
  if (y < 1961)  { t = y - 1950; return 29.07 + 0.407 * t - t ** 2 / 233 + t ** 3 / 2547; }
  if (y < 1986)  { t = y - 1975; return 45.45 + 1.067 * t - t ** 2 / 260 - t ** 3 / 718; }
  if (y < 2005)  { t = y - 2000; return 63.86 + 0.3345 * t - 0.060374 * t ** 2
                     + 0.0017275 * t ** 3 + 0.000651814 * t ** 4 + 0.00002373599 * t ** 5; }
  if (y < 2050)  { t = y - 2000; return 62.92 + 0.32217 * t + 0.005589 * t * t; }
  if (y < 2150)  { return -20 + 32 * ((y - 1820) / 100) ** 2 - 0.5628 * (2150 - y); }
  u = (y - 1820) / 100;
  return -20 + 32 * u * u;
}

/* Julian Day (…​.5 = midnight UTC) -> "YYYY-MM-DD" */
function jdToISO(jd) {
  const z = Math.floor(jd + 0.5);
  const alpha = Math.floor((z - 1867216.25) / 36524.25);
  const a = z < 2299161 ? z : z + 1 + alpha - Math.floor(alpha / 4);
  const b = a + 1524;
  const c = Math.floor((b - 122.1) / 365.25);
  const d = Math.floor(365.25 * c);
  const e = Math.floor((b - d) / 30.6001);
  const day = b - d - Math.floor(30.6001 * e);
  const mo = e < 14 ? e - 1 : e - 13;
  const yr = mo > 2 ? c - 4716 : c - 4715;
  return `${String(yr).padStart(4, "0")}-${String(mo).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
}

/* THE RULE: civil day (UTC) containing conjunction k, plus one day. */
function computedMonthStartJD(k) {
  const approxYear = 2000 + Math.floor(k / 12.3685);
  const jdUT = moonPhaseJDE(k, false) - deltaTExtended(approxYear) / 86400;
  return Math.floor(jdUT + 0.5) - 0.5 + 1;
}

/* ---- joining computed months to the printed table ----------------------- */

/* The conjunction index k is stored on every computed month rather than being
 * re-derived from its start date. Table months follow a different (unknown)
 * rule, so round-tripping a date back to a k would drift at the seam; seeding
 * k once from the table edge and then walking by ±1 keeps the lunation count
 * exact however far out we go. */
function kSeedFromISO(iso) {
  const [y, m, d] = iso.split("-").map(Number);
  return Math.round((greg2JD(y, m, d) - 2451550.09766) / 29.530588861);
}

function positionInYear(ny, nm) {
  return nasiMonthNamesForYear(ny).indexOf(nm) + 1;   // 1-based; 0 = not found
}

let _extended = null;

function extendedMonths() {
  if (_extended) return _extended;
  _extended = NASI_MONTHS.map((m) => ({ ...m, computed: false }));
  return _extended;
}

function nextComputedMonth(prev, prevK) {
  const names = nasiMonthNamesForYear(prev.ny);
  const pos = names.indexOf(prev.nm) + 1;
  let ny = prev.ny, nm;
  if (pos > 0 && pos < names.length) nm = names[pos];
  else { ny = prev.ny + 1; nm = nasiMonthNamesForYear(ny)[0]; }
  const k = prevK + 1;
  const startJD = computedMonthStartJD(k);
  return { start: jdToISO(startJD), len: Math.round(computedMonthStartJD(k + 1) - startJD),
           ny, nm, computed: true, _k: k };
}

function prevComputedMonth(next, nextK) {
  const namesNext = nasiMonthNamesForYear(next.ny);
  const pos = namesNext.indexOf(next.nm) + 1;
  let ny = next.ny, nm;
  if (pos > 1) nm = namesNext[pos - 2];
  else { ny = next.ny - 1; const n = nasiMonthNamesForYear(ny); nm = n[n.length - 1]; }
  const k = nextK - 1;
  const startJD = computedMonthStartJD(k);
  return { start: jdToISO(startJD), len: Math.round(computedMonthStartJD(k + 1) - startJD),
           ny, nm, computed: true, _k: k };
}

/* Grow the cached list until it covers `iso`. Lazy on purpose: each step costs
 * a full Meeus series, so covering centuries eagerly would stall first paint. */
function ensureCovers(iso) {
  const arr = extendedMonths();
  let guard = 0;
  while (guard++ < 40000) {
    const last = arr[arr.length - 1];
    const end = addDays(last.start, last.len - 1);
    if (end >= iso) break;
    arr.push(nextComputedMonth(last, last._k !== undefined ? last._k : kSeedFromISO(last.start)));
  }
  guard = 0;
  while (guard++ < 40000) {
    const first = arr[0];
    if (first.start <= iso) break;
    const k = first._k !== undefined ? first._k : kSeedFromISO(first.start);
    arr.unshift(prevComputedMonth(first, k));
  }
  return arr;
}

/* Same contract as gregorianToNasi, but never returns null for an in-support
 * date: outside the table it computes, and flags the result. */
function gregorianToNasiExtended(isoDate) {
  const inTable = isoDate >= NASI_RANGE.min && isoDate <= NASI_RANGE.max;
  if (inTable) return { ...gregorianToNasi(isoDate), computed: false };
  const arr = ensureCovers(isoDate);
  let lo = 0, hi = arr.length - 1, ans = -1;
  while (lo <= hi) {
    const mid = (lo + hi) >> 1;
    if (arr[mid].start <= isoDate) { ans = mid; lo = mid + 1; }
    else hi = mid - 1;
  }
  if (ans < 0) return null;
  const m = arr[ans];
  if (isoDate > addDays(m.start, m.len - 1)) return null;
  return { ny: m.ny, nm: m.nm, nd: daysBetween(m.start, isoDate) + 1, computed: !!m.computed };
}
