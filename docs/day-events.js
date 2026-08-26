/* What happens on a given day -- the source for the grid's dots and the day
 * panel's rows.
 *
 * The display rule this file exists to enforce: THE GRID NEVER SHOWS MORE THAN
 * ONE DOT PER DAY. Not a dot per event, a single mark meaning "something
 * happens today", with the list itself one tap down. Everything dotted at once
 * would mark roughly 70 days a year, one in five, which reads as noise. Two
 * decisions bring it to about 20:
 *
 *   - perigee and apogee earn no dot. They occur ~26 times a year, one per
 *     anomalistic month; only the supermoon and micromoon are marked, and the
 *     distance is a panel row every day.
 *   - new and full moon earn no dot. The phase icon already carries them.
 *
 * Computed a month at a time rather than a year, because moonrise costs ~150
 * evaluations of a 45-term series per day and a year of it would be visible on
 * first paint. Year-scale facts (solstices, perihelion, the city's earliest
 * sunset) are cheap and cached separately.
 */

const _monthEventCache = new Map();

/* Map of ISO date -> [{key, ...detail}] for one Gregorian month. */
function dayEventsForMonth(year, month0, cityKey) {
  const cacheKey = `${year}-${month0}-${cityKey}`;
  if (_monthEventCache.has(cacheKey)) return _monthEventCache.get(cacheKey);

  const map = new Map();
  const add = (iso, ev) => {
    if (!iso) return;
    if (!map.has(iso)) map.set(iso, []);
    map.get(iso).push(ev);
  };

  const first = `${year}-${String(month0 + 1).padStart(2, "0")}-01`;
  const daysInMonth = new Date(Date.UTC(year, month0 + 1, 0)).getUTCDate();
  const last = `${year}-${String(month0 + 1).padStart(2, "0")}-${String(daysInMonth).padStart(2, "0")}`;

  /* --- Sun and Earth, year-scale ------------------------------------- */
  const seasons = seasonInstants(year);
  add(jdToISO(seasons.marEquinox), { key: "equinoxMar", jd: seasons.marEquinox });
  add(jdToISO(seasons.junSolstice), { key: "solsticeJun", jd: seasons.junSolstice });
  add(jdToISO(seasons.sepEquinox), { key: "equinoxSep", jd: seasons.sepEquinox });
  add(jdToISO(seasons.decSolstice), { key: "solsticeDec", jd: seasons.decSolstice });

  const cq = crossQuarterJDs(year);
  for (const k of ["feb", "may", "aug", "nov"]) add(jdToISO(cq[k]), { key: "crossQuarter" });

  const pa = perihelionAphelionCorrected(year);
  add(jdToISO(pa.perihelion.jd), { key: "perihelion", km: pa.perihelion.km });
  add(jdToISO(pa.aphelion.jd), { key: "aphelion", km: pa.aphelion.km });

  /* --- the solar year as this city sees it ---------------------------- */
  const ex = cityYearExtremes(cityKey, year);
  if (ex.longest) add(ex.longest.iso, { key: "longestDay", seconds: ex.longest.seconds });
  if (ex.shortest) add(ex.shortest.iso, { key: "shortestDay", seconds: ex.shortest.seconds });
  if (ex.earliestSunset) add(ex.earliestSunset.iso, { key: "earliestSunset" });
  if (ex.latestSunrise) add(ex.latestSunrise.iso, { key: "latestSunrise" });

  /* --- Moon: only the extremes of distance earn a mark ---------------- */
  const fromJD = _jdUTC(year, month0 + 1, 1) - 2;
  const toJD = fromJD + daysInMonth + 4;
  for (const e of moonDistanceExtremesInRange(fromJD, toJD)) {
    const illum = moonIlluminatedFraction(e.jd);
    if (e.kind === "perigee" && e.km <= SUPERMOON_KM && illum > 0.97) {
      add(jdToISO(e.jd), { key: "supermoon", km: e.km });
    } else if (e.kind === "apogee" && e.km >= MICROMOON_KM && illum > 0.97) {
      add(jdToISO(e.jd), { key: "micromoon", km: e.km });
    }
  }

  /* --- eclipses -------------------------------------------------------- */
  for (const e of solarEclipsesBetween(first, last)) {
    add(e.iso, { key: "solarEclipse", kind: e.kind, saros: e.saros });
  }
  for (const e of LUNAR_ECLIPSES) {
    const iso = new Intl.DateTimeFormat("en-CA", { timeZone: "UTC" }).format(new Date(e.t));
    if (iso < first || iso > last) continue;
    const [ly, lm, ld] = iso.split("-").map(Number);
    add(iso, {
      key: "lunarEclipse", kind: e.type,
      saros: lunarSaros(lunationNumber(_jdUTC(ly, lm, ld), true)),
    });
  }

  /* --- the Nasi' calendar's own landmarks ----------------------------- */
  for (let d = 1; d <= daysInMonth; d++) {
    const iso = `${year}-${String(month0 + 1).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
    const n = gregorianToNasiExtended(iso);
    if (!n || n.nd !== 1) continue;
    if (n.nm === NASI_MONTH_LABEL) add(iso, { key: "nasiInsertion", ny: n.ny });
    else if (n.nm === nasiMonthNamesForYear(n.ny)[0]) {
      add(iso, { key: "nasiNewYear", ny: n.ny });
      if (metonicPosition(n.ny).position === 1) add(iso, { key: "metonicStart", ny: n.ny });
    }
  }

  // Drop anything that fell outside the month while being computed year-wide.
  for (const iso of [...map.keys()]) if (iso < first || iso > last) map.delete(iso);

  _monthEventCache.set(cacheKey, map);
  return map;
}

/* --- the day panel ------------------------------------------------------- */

/* Everything about one day that is not already a sun time. Returned raw so the
 * caller formats it in the active language. */
function dayDetail(iso, cityKey) {
  const [y, m, d] = iso.split("-").map(Number);
  const jdNoon = _jdUTC(y, m, d) + 0.5;
  const len = dayLengthInfo(iso, cityKey);
  const rs = moonRiseSet(iso, cityKey);
  const pos = moonPosition(jdNoon);
  const illum = moonIlluminatedFraction(jdNoon);

  return {
    dayLengthSeconds: len ? len.seconds : null,
    dayLengthDeltaSeconds: len ? len.deltaSeconds : null,
    twilightSeconds: len ? len.twilightSeconds : null,
    moonrise: rs.rise, moonset: rs.set,
    moonriseAz: rs.riseAz, moonsetAz: rs.setAz,
    moonDistanceKm: pos.distanceKm,
    illuminated: illum,
    // Earthshine: the dark limb is lit by the Earth for a few days either side
    // of new moon. Below ~8% lit is the window where it is easy to see.
    earthshine: illum < 0.08,
    events: dayEventsForMonth(y, m - 1, cityKey).get(iso) || [],
  };
}

/* --- moonrise azimuth extremes ------------------------------------------
 *
 * The Moon's rising point swings along the horizon, and how far it swings is
 * itself on an 18.6-year cycle -- the lunar standstill. Computed on demand for
 * the الدورات tab rather than for the grid: it needs moonRiseSet for all 365
 * days, which is about 50,000 evaluations of the position series and would be
 * plainly visible on first paint.
 */
const _azimuthCache = new Map();

function moonriseAzimuthRange(cityKey, year) {
  const key = `${cityKey}:${year}`;
  if (_azimuthCache.has(key)) return _azimuthCache.get(key);

  let north = null, south = null;
  for (let doy = 0; doy < 366; doy++) {
    const iso = jdToISO(_jdUTC(year, 1, 1) + doy);
    if (!iso.startsWith(String(year))) break;
    const rs = moonRiseSet(iso, cityKey);
    if (rs.riseAz === null) continue;
    // Azimuth runs north(0) through east(90); the smallest value is the most
    // northerly rising point, the largest the most southerly.
    if (north === null || rs.riseAz < north.az) north = { iso, az: rs.riseAz };
    if (south === null || rs.riseAz > south.az) south = { iso, az: rs.riseAz };
  }
  const out = { north, south, swingDeg: north && south ? south.az - north.az : null };
  _azimuthCache.set(key, out);
  return out;
}
