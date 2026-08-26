/* Sun-and-Earth events: solstices, equinoxes, cross-quarter days, perihelion
 * and aphelion, and the per-city extremes of the solar year.
 *
 * Depends on solar.js (_solarParams, _jdUTC, sunTimes, CITIES) and
 * nasi-extend.js (deltaTExtended, jdToISO).
 */

/* --- season instants -----------------------------------------------------
 *
 * Meeus, Astronomical Algorithms ch.27: a mean instant from a quartic in the
 * year, then a periodic correction of 24 terms. Good to well under a minute
 * over this calendar's range.
 *
 * The 24 coefficients are transcribed by hand, and a transcription error would
 * be silent -- the result would simply be a few hours wrong with nothing to
 * flag it. So seasonInstantsChecked() below recomputes the same four instants
 * a completely different way (bisecting the apparent solar longitude of the
 * model solar.js already uses) and requires the two to agree. Two independent
 * routes landing on the same minute is not a proof, but a typo in a periodic
 * term would not survive it.
 */
const SEASON_KEYS = ["marEquinox", "junSolstice", "sepEquinox", "decSolstice"];

/* mean JDE per season, Meeus table 27.B (years 1000-3000) */
const SEASON_MEAN = {
  marEquinox:  [2451623.80984, 365242.37404,  0.05169, -0.00411, -0.00057],
  junSolstice: [2451716.56767, 365241.62603,  0.00325,  0.00888, -0.00030],
  sepEquinox:  [2451810.21715, 365242.01767, -0.11575,  0.00337,  0.00078],
  decSolstice: [2451900.05952, 365242.74049, -0.06223, -0.00823,  0.00032],
};

/* Meeus table 27.C -- [A, B degrees, C degrees] */
const SEASON_TERMS = [
  [485, 324.96,   1934.136], [203, 337.23,  32964.467], [199, 342.08,     20.186],
  [182,  27.85, 445267.112], [156,  73.14,  45036.886], [136, 171.52,  22518.443],
  [ 77, 222.54,  65928.934], [ 74, 296.72,   3034.906], [ 70, 243.58,   9037.513],
  [ 58, 119.81,  33718.147], [ 52, 297.17,    150.678], [ 50,  21.02,   2281.226],
  [ 45, 247.54,  29929.562], [ 44, 325.15,  31555.956], [ 29,  60.93,   4443.417],
  [ 18, 155.12,  67555.328], [ 17, 288.79,   4562.452], [ 16, 198.04,  62894.029],
  [ 14, 199.76,  31436.921], [ 12,  95.39,  14577.848], [ 12, 287.11,  31931.756],
  [ 12, 320.81,  34777.259], [  9, 227.73,   1222.114], [  8,  15.45,  16859.074],
];

/* Terrestrial Dynamical Time -> UT. Without this the instants are ~70 s late
 * today and minutes out at the far ends of the range. */
function _jdeToJDUT(jde, year) {
  return jde - deltaTExtended(year) / 86400;
}

function seasonInstantJD(year, key) {
  const Y = (year - 2000) / 1000;
  const c = SEASON_MEAN[key];
  const jde0 = c[0] + c[1] * Y + c[2] * Y ** 2 + c[3] * Y ** 3 + c[4] * Y ** 4;

  const T = (jde0 - 2451545.0) / 36525;
  const W = (35999.373 * T - 2.47) * RAD;
  const dLam = 1 + 0.0334 * Math.cos(W) + 0.0007 * Math.cos(2 * W);
  let S = 0;
  for (const [A, B, C] of SEASON_TERMS) S += A * Math.cos((B + C * T) * RAD);

  return _jdeToJDUT(jde0 + (0.00001 * S) / dLam, year);
}

/* {marEquinox, junSolstice, sepEquinox, decSolstice} as JD (UT). */
function seasonInstants(year) {
  const out = {};
  for (const k of SEASON_KEYS) out[k] = seasonInstantJD(year, k);
  return out;
}

/* --- the independent check ----------------------------------------------
 *
 * Apparent solar longitude from the same series solar.js uses for sunrise, so
 * this route shares no coefficients with the table above. Solstices and
 * equinoxes are where that longitude passes 0, 90, 180 and 270 degrees --
 * a well-conditioned crossing, unlike the flat maximum of declination.
 */
function solarLongitude(jd) {
  const T = (jd - 2451545.0) / 36525.0;
  const L0 = (280.46646 + T * (36000.76983 + T * 0.0003032)) % 360.0;
  const M = 357.52911 + T * (35999.05029 - 0.0001537 * T);
  const C = Math.sin(M * RAD) * (1.914602 - T * (0.004817 + 0.000014 * T))
          + Math.sin(2 * M * RAD) * (0.019993 - 0.000101 * T)
          + Math.sin(3 * M * RAD) * 0.000289;
  const omega = 125.04 - 1934.136 * T;
  return ((L0 + C - 0.00569 - 0.00478 * Math.sin(omega * RAD)) % 360 + 360) % 360;
}

function _crossingJD(year, targetDeg) {
  // Bracket generously, then bisect on the signed distance to the target,
  // wrapped to +-180 so the 360->0 seam is not a discontinuity.
  const diff = (jd) => {
    let d = solarLongitude(jd) - targetDeg;
    while (d > 180) d -= 360;
    while (d < -180) d += 360;
    return d;
  };
  let lo = _jdUTC(year, 1, 1) - 5, hi = lo + 380;
  // walk forward to the first sign change from negative to positive
  let step = 1, prev = diff(lo);
  for (let jd = lo + step; jd <= hi; jd += step) {
    const cur = diff(jd);
    if (prev < 0 && cur >= 0) { lo = jd - step; hi = jd; break; }
    prev = cur;
  }
  for (let i = 0; i < 60; i++) {
    const mid = (lo + hi) / 2;
    if (diff(mid) < 0) lo = mid; else hi = mid;
  }
  return _jdeToJDUT((lo + hi) / 2, year);
}

/* Returns {instants, maxDisagreementSeconds}. The caller can assert on the
 * second value; the app logs it once in the console rather than displaying it. */
function seasonInstantsChecked(year) {
  const instants = seasonInstants(year);
  const targets = { marEquinox: 0, junSolstice: 90, sepEquinox: 180, decSolstice: 270 };
  let worst = 0;
  for (const k of SEASON_KEYS) {
    const alt = _crossingJD(year, targets[k]);
    worst = Math.max(worst, Math.abs(alt - instants[k]) * 86400);
  }
  return { instants, maxDisagreementSeconds: worst };
}

/* --- cross-quarter days --------------------------------------------------
 * The midpoints in TIME between consecutive season instants. Not the same as
 * midpoints in solar longitude, because the Earth moves faster at perihelion:
 * the two differ by a couple of days, and the traditional dates are the time
 * midpoints. */
function crossQuarterJDs(year) {
  const prevDec = seasonInstantJD(year - 1, "decSolstice");
  const a = seasonInstants(year);
  return {
    feb: (prevDec + a.marEquinox) / 2,
    may: (a.marEquinox + a.junSolstice) / 2,
    aug: (a.junSolstice + a.sepEquinox) / 2,
    nov: (a.sepEquinox + a.decSolstice) / 2,
  };
}

/* --- perihelion and aphelion --------------------------------------------
 *
 * Found numerically from the Sun's radius vector rather than from Meeus's
 * approximate k-formula: it reuses the eccentricity and equation of centre the
 * rest of the app already runs on, so the two cannot disagree, and it is a
 * genuine minimum rather than a mean passage. The extremum is flat, so this
 * scans days first and then refines by ternary search.
 */
function sunDistanceAU(jd) {
  const T = (jd - 2451545.0) / 36525.0;
  const M = (357.52911 + T * (35999.05029 - 0.0001537 * T)) * RAD;
  const e = 0.016708634 - T * (0.000042037 + 0.0000001267 * T);
  const C = Math.sin(M) * (1.914602 - T * (0.004817 + 0.000014 * T))
          + Math.sin(2 * M) * (0.019993 - 0.000101 * T)
          + Math.sin(3 * M) * 0.000289;
  const v = M + C * RAD;
  return (1.000001018 * (1 - e * e)) / (1 + e * Math.cos(v));
}

function _extremumJD(fromJD, toJD, wantMin) {
  let best = fromJD, bestVal = sunDistanceAU(fromJD);
  for (let jd = fromJD; jd <= toJD; jd += 1) {
    const v = sunDistanceAU(jd);
    if (wantMin ? v < bestVal : v > bestVal) { bestVal = v; best = jd; }
  }
  let lo = best - 1, hi = best + 1;
  for (let i = 0; i < 60; i++) {
    const m1 = lo + (hi - lo) / 3, m2 = hi - (hi - lo) / 3;
    const better = wantMin
      ? sunDistanceAU(m1) < sunDistanceAU(m2)
      : sunDistanceAU(m1) > sunDistanceAU(m2);
    if (better) hi = m2; else lo = m1;
  }
  return (lo + hi) / 2;
}

const AU_KM = 149597870.7;

function perihelionAphelion(year) {
  // Perihelion falls in early January, aphelion in early July; search windows
  // wide enough to hold them whatever the year.
  const jan1 = _jdUTC(year, 1, 1);
  const peri = _extremumJD(jan1 - 15, jan1 + 30, true);
  const jul1 = _jdUTC(year, 7, 1);
  const apo = _extremumJD(jul1 - 20, jul1 + 25, false);
  return {
    perihelion: { jd: _jdeToJDUT(peri, year), km: sunDistanceAU(peri) * AU_KM },
    aphelion:   { jd: _jdeToJDUT(apo, year),  km: sunDistanceAU(apo) * AU_KM },
  };
}

/* The Earth's own perihelion and aphelion, not the barycentre's.
 *
 * Scanned at a fine step rather than ternary-searched: adding the lunar wobble
 * puts a 29.5-day ripple on top of an almost flat annual curve, so the
 * function is no longer unimodal and a ternary search would happily converge
 * on whichever local dip it started nearest. A dense scan has no such
 * assumption to violate.
 */
function perihelionAphelionCorrected(year) {
  const extremum = (fromJD, toJD, wantMin) => {
    let best = fromJD, bestVal = earthSunDistanceKm(fromJD);
    for (let jd = fromJD; jd <= toJD; jd += 0.02) {
      const v = earthSunDistanceKm(jd);
      if (wantMin ? v < bestVal : v > bestVal) { bestVal = v; best = jd; }
    }
    return { jd: best, km: bestVal };
  };
  const jan1 = _jdUTC(year, 1, 1), jul1 = _jdUTC(year, 7, 1);
  const p = extremum(jan1 - 15, jan1 + 30, true);
  const a = extremum(jul1 - 20, jul1 + 25, false);
  return {
    perihelion: { jd: _jdeToJDUT(p.jd, year), km: p.km },
    aphelion:   { jd: _jdeToJDUT(a.jd, year), km: a.km },
  };
}

/* --- the solar year as one city sees it ---------------------------------
 *
 * Longest and shortest day, and -- the surprise worth showing -- earliest
 * sunset and latest sunrise, which are NOT the solstice. The equation of time
 * separates them by weeks, and the gap WIDENS towards the equator: at Cairo
 * earliest sunset is around 2 December against a 21 December solstice, while
 * at Berlin the two are barely a week apart.
 *
 * Brute-forced over 365 days because sunTimes() is cheap and a closed form
 * would have to re-derive the equation of time anyway. Cached per city-year.
 */
const _yearExtremeCache = new Map();

function cityYearExtremes(cityKey, year) {
  const cacheKey = `${cityKey}:${year}`;
  if (_yearExtremeCache.has(cacheKey)) return _yearExtremeCache.get(cacheKey);

  const city = CITIES[cityKey];
  let longest = null, shortest = null, earliestSunset = null, latestSunrise = null;

  // One offset for the whole year -- see the note in the loop below.
  const refOffsetMs = _tzOffsetMs(Date.UTC(year, 11, 21), city.tz);

  for (let doy = 0; doy < 366; doy++) {
    const iso = jdToISO(_jdUTC(year, 1, 1) + doy);
    if (!iso.startsWith(String(year))) break;
    const times = sunTimes(iso, cityKey);
    if (!times.sunrise || !times.sunset) continue;

    const len = (times.sunset - times.sunrise) / 1000;
    if (!longest || len > longest.seconds) longest = { iso, seconds: len };
    if (!shortest || len < shortest.seconds) shortest = { iso, seconds: len };

    /* Compared against a FIXED offset, not the zone's actual offset that day.
     *
     * Using the real local clock lets a daylight-saving jump masquerade as the
     * extreme: when clocks go back, sunset lands an hour earlier on the clock
     * overnight. Morocco is the clear case -- it drops an hour for Ramadan --
     * and the earliest sunset of 2026 came out as 15 February instead of
     * 4 December, a ten-month error in a figure the app presents as a fact.
     *
     * Any constant offset gives the same answer, since a constant shifts every
     * day equally; midwinter's is used so sunset sits near the middle of the
     * shifted day and cannot wrap past midnight. Earliest sunset is a claim
     * about the equation of time, which is astronomy -- a civil clock change
     * has no business in it. */
    const setAt = (times.sunset.getTime() + refOffsetMs) % 86400000 / 1000;
    const riseAt = (times.sunrise.getTime() + refOffsetMs) % 86400000 / 1000;
    if (!earliestSunset || setAt < earliestSunset.secondsOfDay)
      earliestSunset = { iso, secondsOfDay: setAt };
    if (!latestSunrise || riseAt > latestSunrise.secondsOfDay)
      latestSunrise = { iso, secondsOfDay: riseAt };
  }

  const out = { longest, shortest, earliestSunset, latestSunrise };
  _yearExtremeCache.set(cacheKey, out);
  return out;
}

/* --- what today looks like ----------------------------------------------
 * Day length, how much it changed since yesterday (fastest at the equinoxes,
 * and faster the further from the equator), and how long twilight lasts. */
function dayLengthInfo(iso, cityKey) {
  const today = sunTimes(iso, cityKey);
  if (!today.sunrise || !today.sunset) return null;
  const seconds = (today.sunset - today.sunrise) / 1000;

  const prev = sunTimes(addDays(iso, -1), cityKey);
  const deltaSeconds = prev.sunrise && prev.sunset
    ? seconds - (prev.sunset - prev.sunrise) / 1000
    : null;

  const twilightSeconds = today.firstLight
    ? (today.sunrise - today.firstLight) / 1000
    : null;

  return { seconds, deltaSeconds, twilightSeconds };
}
