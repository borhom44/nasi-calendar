/* The long cycles: everything that changes once a year or once a decade.
 *
 * This is the arithmetic behind the الدورات tab. None of it belongs on a month
 * grid -- a 19-year rhythm rendered as day-cells is invisible -- and all of it
 * is what actually explains why this calendar exists. A lunar year is 11 days
 * short of a solar one; the نسيء month is the correction; the Metonic cycle is
 * the schedule it runs on. Until now none of that appeared anywhere on screen.
 *
 * Depends on nasi-calendar.js (nasiToGregorian, NASI_RANGE), nasi-extend.js
 * (NASI_INTERCALARY, nasiMonthNamesForYear) and hijri.js (hijriToGregorian).
 */

/* --- the Metonic cycle ---------------------------------------------------
 *
 * 235 lunations and 19 tropical years are very nearly the same span, which is
 * what makes a lunisolar calendar possible at all. Very nearly, not exactly:
 *
 *   235 x 29.530589 d = 6939.6884 d
 *    19 x 365.2422  d = 6939.6018 d
 *                       ---------
 *                          0.0866 d  = 2h 04m 45s per cycle
 *
 * so the scheme slips a whole day about every 219 years. That is not a defect
 * to hide; it is the reason dates computed outside the book's printed table
 * are marked as computed, and it belongs on the page where a reader can see it.
 */
const SYNODIC_DAYS = 29.530589;
const TROPICAL_DAYS = 365.2422;
const METONIC_YEARS = 19;
const METONIC_LUNATIONS = 235;

const METONIC_SLIP_DAYS =
  METONIC_LUNATIONS * SYNODIC_DAYS - METONIC_YEARS * TROPICAL_DAYS;
const METONIC_SLIP_SECONDS = METONIC_SLIP_DAYS * 86400;
const METONIC_DAY_EVERY_YEARS = METONIC_YEARS / METONIC_SLIP_DAYS;

/* 1-based position of a Nasi' year within its 19-year cycle. Residue 0 is
 * year 1, so the intercalary residues {2,4,7,10,12,15,18} land on positions
 * 3, 5, 8, 11, 13, 16 and 19. */
function metonicPosition(ny) {
  const residue = ((ny % METONIC_YEARS) + METONIC_YEARS) % METONIC_YEARS;
  return {
    residue,
    position: residue + 1,
    total: METONIC_YEARS,
    intercalary: residue in NASI_INTERCALARY,
    slot: NASI_INTERCALARY[residue] || null,
  };
}

/* Every position in the cycle, flagged -- the 19-segment bar reads off this. */
function metonicCycleMap(ny) {
  const here = metonicPosition(ny).position;
  return Array.from({ length: METONIC_YEARS }, (_, i) => {
    const residue = i;
    return {
      position: i + 1,
      current: i + 1 === here,
      intercalary: residue in NASI_INTERCALARY,
    };
  });
}

/* The next year at or after `ny` that carries a نسيء month, and how far off. */
function nextNasiInsertion(ny) {
  for (let y = ny; y < ny + METONIC_YEARS + 1; y++) {
    if (metonicPosition(y).intercalary) return { ny: y, away: y - ny };
  }
  return null;   // unreachable: seven of every nineteen years are intercalary
}

/* --- where the Nasi' year sits against the solar year --------------------
 *
 * This is the whole point of the نسيء month, and the one thing a reader can
 * check for themselves: the Nasi' new year oscillates inside a fixed window of
 * the solar year, while the official Hijri new year -- which never intercalates
 * -- walks backwards through all four seasons and laps every ~33 years.
 */
function nasiNewYearISO(ny) {
  const first = nasiMonthNamesForYear(ny)[0];
  try {
    return nasiToGregorian(ny, first, 1);
  } catch (e) {
    return null;
  }
}

function hijriNewYearISO(hy) {
  return hijriToGregorian(hy, 1, 1);
}

/* Day-of-year (1-366) for an ISO date, used only to compare positions within
 * the solar year -- the leap-day offset is far below the effect being shown. */
function dayOfYear(iso) {
  const [y, m, d] = iso.split("-").map(Number);
  return Math.round(
    (Date.UTC(y, m - 1, d) - Date.UTC(y, 0, 1)) / 86400000
  ) + 1;
}

/* The window the Nasi' new year moves within, measured over one full cycle
 * starting at `ny`. Returned as the earliest and latest ISO dates found, so
 * the caller can format them however the active language wants. */
function nasiDriftWindow(ny) {
  let earliest = null, latest = null;
  for (let y = ny; y < ny + METONIC_YEARS; y++) {
    const iso = nasiNewYearISO(y);
    if (!iso) continue;
    const doy = dayOfYear(iso);
    if (earliest === null || doy < earliest.doy) earliest = { iso, doy };
    if (latest === null || doy > latest.doy) latest = { iso, doy };
  }
  return earliest && latest ? { earliest, latest, spanDays: latest.doy - earliest.doy } : null;
}

/* Rows comparing the two new years as they advance. Nasi' stays inside its
 * window; Hijri slides ~11 days earlier every year. Five rows twenty years
 * apart makes the divergence obvious without a chart. */
function driftComparison(fromNy, fromHy, step, rows) {
  const out = [];
  for (let i = 0; i < rows; i++) {
    const ny = fromNy + i * step;
    const hy = fromHy + i * step;
    const nasi = nasiNewYearISO(ny);
    if (!nasi) break;
    out.push({ ny, nasiISO: nasi, hy, hijriISO: hijriNewYearISO(hy) });
  }
  return out;
}


/* --- the lunar standstill ------------------------------------------------
 *
 * The Moon's orbit is tilted 5.14 deg to the ecliptic, and that tilt itself
 * rotates: the ascending node regresses through the whole zodiac in 18.6
 * years. When the node reaches 0 deg the two tilts add -- 23.44 + 5.14 =
 * 28.58 deg -- and the Moon's rising point swings its widest along the
 * horizon. That is a major standstill. The last was 2024-25 and the next is
 * around 2043: the longest cycle a person can watch unaided, and the reason
 * some ancient monuments align to moonrise rather than sunrise.
 */
const LUNAR_NODAL_YEARS = 18.613;

/* Next Julian Day at or after `fromJD` when the ascending node passes 0 deg.
 * The node regresses, so the longitude runs downwards through zero. */
function nextMajorStandstillJD(fromJD) {
  let prev = lunarNodeLongitude(fromJD);
  for (let jd = fromJD + 1; jd < fromJD + LUNAR_NODAL_YEARS * 366 + 400; jd += 1) {
    const cur = lunarNodeLongitude(jd);
    if (cur > prev) {          // wrapped past 0 going down
      let lo = jd - 1, hi = jd;
      for (let i = 0; i < 40; i++) {
        const mid = (lo + hi) / 2;
        if (lunarNodeLongitude(mid) > 180) lo = mid; else hi = mid;
      }
      return (lo + hi) / 2;
    }
    prev = cur;
  }
  return null;
}
