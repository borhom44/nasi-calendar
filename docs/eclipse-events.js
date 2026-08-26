/* Eclipses, and the families they belong to.
 *
 * Lunar eclipses come from the NASA catalogue already shipped in
 * eclipses-data.js. Solar ones are computed here from the geometry, because no
 * solar catalogue ships with the app and the criterion is simple: an eclipse
 * happens somewhere on Earth when the Moon is near a node at new moon.
 *
 * SCOPE, stated plainly. This answers "an eclipse occurs on this date, of this
 * kind, belonging to this Saros family". It does NOT answer "is it total where
 * I am, and at what time" -- local circumstances need Besselian elements and
 * horizon geometry, which is a project rather than a line item. The app says
 * only what it can actually support.
 */

/* --- is there an eclipse at this syzygy? ---------------------------------
 *
 * At new moon the Moon's ecliptic latitude decides it. Sun and Moon are each
 * about 0.26 deg in radius and the Moon's horizontal parallax is about 0.95
 * deg, so somewhere on Earth sees a partial eclipse while |beta| stays under
 * roughly 1.58 deg, and the eclipse is central -- total or annular -- under
 * the calibrated cutoff below. Between them it is partial everywhere.
 */
/* Also calibrated. 1.58 is the textbook geometric bound but it is generous
 * enough to invent an eclipse on 30 May 2022 (beta 1.496), where the
 * catalogue has none. The largest genuine grazing partial in 2017-2028 is
 * 13 Jul 2018 at 1.386, so the boundary sits between them.
 *
 * The trade is deliberate. At 1.44 a century comes out at 2.21 eclipses a
 * year against a true 2.38, so roughly 17 grazing partials per century are
 * missed -- ones visible only as a small bite near a pole. At 1.58 none are
 * missed but eclipses get invented. For a calendar, telling someone an
 * eclipse is happening when it is not is the worse failure. */
const ECLIPSE_PARTIAL_DEG = 1.44;

/* Calibrated, not guessed. Across the 26 solar eclipses of 2017-2028 the
 * catalogue's central ones all have |beta| <= 0.973 deg and its partial ones
 * all have |beta| >= 0.984 -- cleanly separable, with the cutoff falling
 * almost exactly on the Moon's horizontal parallax of ~0.95 deg. That is the
 * physical meaning of the number: beyond it, the shadow axis misses the Earth
 * by more than one Earth radius and nobody stands in the umbra. */
const ECLIPSE_CENTRAL_DEG = 0.978;

/* --- Saros ---------------------------------------------------------------
 *
 * Eclipses are not scattered. Two eclipses 223 lunations apart belong to the
 * same series; two 358 lunations apart (one inex) sit in adjacent series. So
 * from a lunation number k the series follows from
 *
 *     223x + 358y = k - k0      series = s0 + y
 *
 * and since 358 = 135 (mod 223) and 135 inverse is 38 (mod 223),
 *
 *     y = 38 (k - k0)  (mod 223)
 *
 * Calibrated on the total solar eclipse of 21 Aug 2017, Saros 145 (k = 218)
 * and checked against 8 Apr 2024, Saros 139 -- 82 lunations later, and
 * 38 x 82 = 217 = -6 (mod 223), giving 145 - 6 = 139 exactly.
 */
const SAROS_INV = 38;
const SOLAR_SAROS_K0 = 218, SOLAR_SAROS_S0 = 145;
const LUNAR_SAROS_K0 = 229, LUNAR_SAROS_S0 = 129;   // 27 Jul 2018, Saros 129

function _sarosFrom(k, k0, s0) {
  const y = ((SAROS_INV * (k - k0)) % 223 + 223) % 223;
  const s = ((s0 + y) % 223 + 223) % 223;
  return s === 0 ? 223 : s;
}

function solarSaros(k) { return _sarosFrom(k, SOLAR_SAROS_K0, SOLAR_SAROS_S0); }
function lunarSaros(k) { return _sarosFrom(k, LUNAR_SAROS_K0, LUNAR_SAROS_S0); }

/* Lunation number on the k scale moon-events.js uses.
 *
 * Rounding the date is not good enough. Full moons sit roughly half a lunation
 * from the k they belong to, so the nearest integer can land one off -- and one
 * off in k is 38 off in Saros, which is how the lunar series first came out
 * wrong for 16 May 2022 (169 instead of 131). Pick the k whose syzygy is
 * actually closest to the date instead. */
function lunationNumber(jd, isFull) {
  const approx = Math.floor((jd - 2451550.09766) / 29.530588861);
  let best = approx, bestGap = Infinity;
  for (let k = approx - 1; k <= approx + 1; k++) {
    const t = moonPhaseJDE(k, !!isFull) - deltaTExtended(2000 + k / 12.3685) / 86400;
    const gap = Math.abs(t - jd);
    if (gap < bestGap) { bestGap = gap; best = k; }
  }
  return best;
}

/* --- solar eclipses in a date range -------------------------------------- */
function solarEclipsesBetween(fromISO, toISO) {
  const [fy, fm, fd] = fromISO.split("-").map(Number);
  const [ty, tm, td] = toISO.split("-").map(Number);
  const fromJD = _jdUTC(fy, fm, fd), toJD = _jdUTC(ty, tm, td) + 1;

  const out = [];
  for (let k = lunationNumber(fromJD) - 1; k <= lunationNumber(toJD) + 1; k++) {
    const jde = moonPhaseJDE(k, false);                  // new moon, TD
    const jd = jde - deltaTExtended(2000 + k / 12.3685) / 86400;
    if (jd < fromJD || jd > toJD) continue;

    const beta = Math.abs(moonPosition(jd).lat);
    if (beta > ECLIPSE_PARTIAL_DEG) continue;

    // Central eclipses are annular when the Moon is far and total when near;
    // the switch is where its apparent radius matches the Sun's.
    const m = moonPosition(jd);
    const moonRadius = Math.asin(1737.4 / m.distanceKm) / RAD;
    const sunRadius = 959.63 / 3600 / sunDistanceAU(jd);
    // Hybrid: the umbra's tip grazes the surface, so the same eclipse is
    // annular where the Earth curves away and total where it bulges up. That
    // is exactly the case where the two apparent radii are equal. Measured,
    // 20 Apr 2023 -- the catalogue's only hybrid here -- sits at -2.0 arcsec
    // while every other central eclipse is at least 8.5 arcsec clear.
    const radiusGapArcsec = (moonRadius - sunRadius) * 3600;
    const kind = beta > ECLIPSE_CENTRAL_DEG ? "partial"
               : Math.abs(radiusGapArcsec) < 8 ? "hybrid"
               : radiusGapArcsec > 0 ? "total" : "annular";

    out.push({ jd, iso: jdToISO(jd), kind, saros: solarSaros(k), betaDeg: beta, k });
  }
  return out;
}

/* --- eclipse seasons -----------------------------------------------------
 *
 * Eclipses are only possible when the Sun is near one of the Moon's nodes,
 * which happens twice a year for about 34 days. Those windows are 173.3 days
 * apart, not 182.6, because the draconic year is 346.62 days -- shorter than
 * the solar year, since the nodes regress. That is why eclipse seasons creep
 * backwards through the calendar by about 19 days a year.
 */
const DRACONIC_YEAR_DAYS = 346.62;
const ECLIPSE_SEASON_HALF_DAYS = 17;

/* Mean longitude of the Moon's ascending node, degrees. */
function lunarNodeLongitude(jd) {
  const T = (jd - 2451545.0) / 36525.0;
  return ((125.0445479 - 1934.1362891 * T + 0.0020754 * T * T
          + T * T * T / 467441 - T ** 4 / 60616000) % 360 + 360) % 360;
}

/* The eclipse seasons overlapping a year: the Sun passing each node. */
function eclipseSeasons(year) {
  const out = [];
  const start = _jdUTC(year, 1, 1) - 200, end = _jdUTC(year + 1, 1, 1) + 200;
  let prev = null;
  for (let jd = start; jd <= end; jd += 0.5) {
    // Angle from the Sun to the nearer node, wrapped to +-90.
    const node = lunarNodeLongitude(jd);
    let a = (solarLongitude(jd) - node) % 180;
    if (a > 90) a -= 180;
    if (a < -90) a += 180;
    if (prev !== null && prev < 0 && a >= 0) {
      const centre = jd - 0.25;
      const from = centre - ECLIPSE_SEASON_HALF_DAYS;
      const to = centre + ECLIPSE_SEASON_HALF_DAYS;
      if (to >= _jdUTC(year, 1, 1) && from <= _jdUTC(year + 1, 1, 1)) {
        out.push({ centreJD: centre, fromISO: jdToISO(from), toISO: jdToISO(to) });
      }
    }
    prev = a;
  }
  return out;
}

/* --- exeligmos -----------------------------------------------------------
 * Three Saros, 54 years and 33 days: the same series returning to nearly the
 * same longitude on Earth rather than a third of the way round the globe. */
const EXELIGMOS_DAYS = 3 * 223 * 29.530588861;
