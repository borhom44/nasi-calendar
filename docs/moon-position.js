/* Geocentric position of the Moon -- longitude, latitude and distance.
 *
 * Meeus, Astronomical Algorithms ch.47, abridged to the terms that matter at
 * this display resolution: about 30 periodic terms for longitude and distance
 * and 15 for latitude, giving roughly 30" in longitude and 200 km in distance.
 * Moonrise is wanted to the minute and perigee to the day, so that is ample;
 * the full 60-term tables would buy precision nothing on screen can show.
 *
 * Everything downstream needs this: moonrise and moonset, perigee and apogee,
 * the Moon's rising azimuth -- and, less obviously, perihelion. The Earth sits
 * up to 4,671 km from the Earth-Moon barycentre, and since the Earth-Sun
 * distance extremum is very flat, that wobble moves perihelion by up to a day.
 *
 * The coefficients are transcribed by hand, so two independent checks run
 * against them (see the probe): the Moon's elongation from the Sun must be
 * ~0 deg at each new moon and ~180 deg at each full moon computed by the
 * already-verified moon-events.js, and computed illumination must match the
 * precomputed moon-phases-data.js table.
 */

/* [D, M, M', F, l coefficient (1e-6 deg), r coefficient (1e-3 km)] */
const MOON_LR = [
  [0, 0, 1, 0, 6288774, -20905355], [2, 0, -1, 0, 1274027, -3699111],
  [2, 0, 0, 0, 658314, -2955968],   [0, 0, 2, 0, 213618, -569925],
  [0, 1, 0, 0, -185116, 48888],     [0, 0, 0, 2, -114332, -3149],
  [2, 0, -2, 0, 58793, 246158],     [2, -1, -1, 0, 57066, -152138],
  [2, 0, 1, 0, 53322, -170733],     [2, -1, 0, 0, 45758, -204586],
  [0, 1, -1, 0, -40923, -129620],   [1, 0, 0, 0, -34720, 108743],
  [0, 1, 1, 0, -30383, 104755],     [2, 0, 0, -2, 15327, 10321],
  [0, 0, 1, 2, -12528, 0],          [0, 0, 1, -2, 10980, 79661],
  [4, 0, -1, 0, 10675, -34782],     [0, 0, 3, 0, 10034, -23210],
  [4, 0, -2, 0, 8548, -21636],      [2, 1, -1, 0, -7888, 24208],
  [2, 1, 0, 0, -6766, 30824],       [1, 0, -1, 0, -5163, -8379],
  [1, 1, 0, 0, 4987, -16675],       [2, -1, 1, 0, 4036, -12831],
  [2, 0, 2, 0, 3994, -10445],       [4, 0, 0, 0, 3861, -11650],
  [2, 0, -3, 0, 3665, 14403],       [0, 1, -2, 0, -2689, -7003],
  [2, 0, -1, 2, -2602, 0],          [2, -1, -2, 0, 2390, 10056],
  [1, 0, 1, 0, -2348, 6322],        [2, -2, 0, 0, 2236, -9884],
  [0, 1, 2, 0, -2120, 5751],        [0, 2, 0, 0, -2069, 0],
  [2, -2, -1, 0, 2048, -4950],      [2, 0, 1, -2, -1773, 4130],
  [2, 0, 0, 2, -1595, 0],           [4, -1, -1, 0, 1215, -3958],
  [0, 0, 2, 2, -1110, 0],           [3, 0, -1, 0, -892, 3258],
  [2, 1, 1, 0, -810, 2616],         [4, -1, -2, 0, 759, -1897],
  [0, 2, -1, 0, -713, -2117],       [2, 2, -1, 0, -700, 2354],
  [2, 0, -1, -2, 0, 8752],
];

/* [D, M, M', F, b coefficient (1e-6 deg)] */
const MOON_B = [
  [0, 0, 0, 1, 5128122], [0, 0, 1, 1, 280602], [0, 0, 1, -1, 277693],
  [2, 0, 0, -1, 173237], [2, 0, -1, 1, 55413], [2, 0, -1, -1, 46271],
  [2, 0, 0, 1, 32573],   [0, 0, 2, -1, 17198], [2, 0, 1, -1, 9266],
  [0, 0, 2, 1, 8822],    [2, -1, 0, -1, 8216], [2, 0, -2, -1, 4324],
  [2, 0, 1, 1, 4200],    [2, 1, 0, -1, -3359], [2, -1, -1, 1, 2463],
  [2, -1, 0, 1, 2211],   [2, -1, -1, -1, 2065], [0, 1, -1, -1, -1870],
  [4, 0, -1, -1, 1828],  [0, 1, 0, 1, -1794],  [0, 0, 0, 3, -1749],
  [0, 1, -1, 1, -1565],  [1, 0, 0, 1, -1491],  [0, 1, 1, 1, -1475],
  [0, 1, 1, -1, -1410],  [0, 1, 0, -1, -1344], [1, 0, 0, -1, -1335],
  [0, 0, 3, 1, 1107],    [4, 0, 0, -1, 1021],  [4, 0, -1, 1, 833],
];

/* {lon, lat, distanceKm} -- apparent geocentric, degrees and kilometres. */
function moonPosition(jd) {
  const T = (jd - 2451545.0) / 36525.0;

  const Lp = 218.3164477 + 481267.88123421 * T - 0.0015786 * T ** 2
           + T ** 3 / 538841 - T ** 4 / 65194000;
  const D = 297.8501921 + 445267.1114034 * T - 0.0018819 * T ** 2
          + T ** 3 / 545868 - T ** 4 / 113065000;
  const M = 357.5291092 + 35999.0502909 * T - 0.0001536 * T ** 2 + T ** 3 / 24490000;
  const Mp = 134.9633964 + 477198.8675055 * T + 0.0087414 * T ** 2
           + T ** 3 / 69699 - T ** 4 / 14712000;
  const F = 93.2720950 + 483202.0175233 * T - 0.0036539 * T ** 2
          - T ** 3 / 3526000 + T ** 4 / 863310000;

  // Terms in M are scaled by E because the Sun's eccentricity changes slowly.
  const E = 1 - 0.002516 * T - 0.0000074 * T * T;
  const ecc = (m) => (m === 0 ? 1 : Math.abs(m) === 1 ? E : E * E);

  let sumL = 0, sumR = 0, sumB = 0;
  for (const [d, m, mp, f, cl, cr] of MOON_LR) {
    const arg = (d * D + m * M + mp * Mp + f * F) * RAD;
    sumL += cl * ecc(m) * Math.sin(arg);
    sumR += cr * ecc(m) * Math.cos(arg);
  }
  for (const [d, m, mp, f, cb] of MOON_B) {
    const arg = (d * D + m * M + mp * Mp + f * F) * RAD;
    sumB += cb * ecc(m) * Math.sin(arg);
  }

  // Additive terms for Venus, Jupiter and the flattening of the Earth.
  const A1 = 119.75 + 131.849 * T;
  const A2 = 53.09 + 479264.290 * T;
  const A3 = 313.45 + 481266.484 * T;
  sumL += 3958 * Math.sin(A1 * RAD) + 1962 * Math.sin((Lp - F) * RAD)
        + 318 * Math.sin(A2 * RAD);
  sumB += -2235 * Math.sin(Lp * RAD) + 382 * Math.sin(A3 * RAD)
        + 175 * Math.sin((A1 - F) * RAD) + 175 * Math.sin((A1 + F) * RAD)
        + 127 * Math.sin((Lp - Mp) * RAD) - 115 * Math.sin((Lp + Mp) * RAD);

  return {
    lon: ((Lp + sumL / 1e6) % 360 + 360) % 360,
    lat: sumB / 1e6,
    distanceKm: 385000.56 + sumR / 1000,
  };
}

/* Illuminated fraction, 0-1. Used as a cross-check against the precomputed
 * moon-phases-data.js table, which was verified against Meeus independently. */
function moonIlluminatedFraction(jd) {
  const m = moonPosition(jd);
  const sunLon = solarLongitude(jd);
  const elong = Math.acos(
    Math.cos(m.lat * RAD) * Math.cos((m.lon - sunLon) * RAD)
  ) / RAD;
  // Phase angle of the Sun-Moon-Earth triangle, with the Sun at ~1 AU.
  const sunKm = sunDistanceAU(jd) * 149597870.7;
  const i = Math.atan2(
    sunKm * Math.sin(elong * RAD),
    m.distanceKm - sunKm * Math.cos(elong * RAD)
  ) / RAD;
  return (1 + Math.cos(i * RAD)) / 2;
}

/* --- what the Moon does to the Earth's distance from the Sun -------------
 *
 * The Earth orbits the Earth-Moon barycentre as well as the Sun, sitting
 * 4,671 km from it on the far side from the Moon. Projected onto the
 * Earth-Sun line that is +/- 4,671 km of extra distance depending on phase.
 * Trivial against 147 million km -- but the perihelion extremum is flat
 * enough that it moves the instant by up to a day and a half, which is the
 * difference between marking the right day on a calendar and the wrong one.
 */
const EARTH_EMB_RATIO = 0.0121505;   // Moon mass / (Earth + Moon) mass

function earthSunDistanceKm(jd) {
  const embKm = sunDistanceAU(jd) * 149597870.7;
  const m = moonPosition(jd);
  const sunLon = solarLongitude(jd);
  // Earth is displaced away from the Moon, so distance grows when the Moon
  // lies sunward (new moon) and shrinks when it is opposite (full moon).
  return embKm + EARTH_EMB_RATIO * m.distanceKm
       * Math.cos((m.lon - sunLon) * RAD) * Math.cos(m.lat * RAD);
}
