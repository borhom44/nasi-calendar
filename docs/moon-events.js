/* Exact new-moon / full-moon instants -- JS port of the same Meeus series
 * already used and NASA-cross-checked in scripts/verify_astronomy.py and
 * scripts/generate_moon_phases.py. Not a table lookup: this is the same
 * closed-form calculation computed live, matching how hijri.js/solar.js work.
 *
 * "full=false" -> new moon (start of a lunar cycle); "full=true" -> full moon.
 * Accuracy: a few seconds against full lunar theory (Meeus, ch.49) -- far
 * finer than anything displayed here.
 */
const MRAD = Math.PI / 180;

function moonArgs(k) {
  const T = k / 1236.85;
  const E = 1 - 0.002516*T - 0.0000074*T*T;
  const M  = (2.5534 + 29.10535670*k - 0.0000014*T**2 - 0.00000011*T**3) * MRAD;
  const Mp = (201.5643 + 385.81693528*k + 0.0107582*T**2 + 0.00001238*T**3 - 0.000000058*T**4) * MRAD;
  const F  = (160.7108 + 390.67050284*k - 0.0016118*T**2 - 0.00000227*T**3 + 0.000000011*T**4) * MRAD;
  const Om = (124.7746 - 1.56375588*k + 0.0020672*T**2 + 0.00000215*T**3) * MRAD;
  const jde = 2451550.09766 + 29.530588861*k + 0.00015437*T**2 - 0.000000150*T**3 + 0.00000000073*T**4;
  return { T, E, M, Mp, F, Om, jde };
}

const PLANETARY_A = [
  [299.77,0.107408,0.000325],[251.88,0.016321,0.000165],[251.83,26.651886,0.000164],
  [349.42,36.412478,0.000126],[84.66,18.206239,0.000110],[141.74,53.303771,0.000062],
  [207.14,2.453732,0.000060],[154.84,7.306860,0.000056],[34.52,27.261239,0.000047],
  [207.19,0.121824,0.000042],[291.34,1.844379,0.000040],[161.72,24.198154,0.000037],
  [239.56,25.513099,0.000035],[331.55,3.592518,0.000023],
];
function planetary(k, T) {
  let tot = 0;
  PLANETARY_A.forEach(([a,b,c], i) => {
    let ang = a + b*k;
    if (i === 0) ang -= 0.009173*T*T;
    tot += c * Math.sin(ang*MRAD);
  });
  return tot;
}

function moonPhaseJDE(k, full) {
  if (full) k += 0.5;
  const { T, E, M, Mp, F, Om, jde } = moonArgs(k);
  const co = full
    ? [-0.40614,0.17302,0.01614,0.01043,0.00734,-0.00515,0.00209]
    : [-0.40720,0.17241,0.01608,0.01039,0.00739,-0.00514,0.00208];
  let c = co[0]*Math.sin(Mp) + co[1]*E*Math.sin(M) + co[2]*Math.sin(2*Mp) + co[3]*Math.sin(2*F)
        + co[4]*E*Math.sin(Mp-M) + co[5]*E*Math.sin(Mp+M) + co[6]*E*E*Math.sin(2*M);
  c += -0.00111*Math.sin(Mp-2*F) - 0.00057*Math.sin(Mp+2*F) + 0.00056*E*Math.sin(2*Mp+M)
     - 0.00042*Math.sin(3*Mp) + 0.00042*E*Math.sin(M+2*F) + 0.00038*E*Math.sin(M-2*F)
     - 0.00024*E*Math.sin(2*Mp-M) - 0.00017*Math.sin(Om) - 0.00007*Math.sin(Mp+2*M)
     + 0.00004*Math.sin(2*Mp-2*F) + 0.00004*Math.sin(3*M) + 0.00003*Math.sin(Mp+M-2*F)
     + 0.00003*Math.sin(2*Mp+2*F) - 0.00003*Math.sin(Mp+M+2*F) + 0.00003*Math.sin(Mp-M+2*F)
     - 0.00002*Math.sin(Mp-M-2*F) - 0.00002*Math.sin(3*Mp+M) + 0.00002*Math.sin(4*Mp);
  return jde + c + planetary(k, T);
}

/* NASA/Espenak-Meeus Delta T polynomial, valid 2005-2150 (our 2000-2100 range). */
function deltaTSeconds(y) {
  if (y < 2050) { const t = y - 2000; return 62.92 + 0.32217*t + 0.005589*t*t; }
  if (y < 2150) return -20 + 32*((y-1820)/100)**2 - 0.5628*(2150-y);
  return 0;
}

function jdeToDate(jde, y) {
  const jdUT = jde - deltaTSeconds(y) / 86400;
  return new Date((jdUT - 2440587.5) * 86400000);   // JD -> Unix epoch ms
}

function greg2JD(y, m, d) {
  if (m <= 2) { y -= 1; m += 12; }
  const a = Math.floor(y/100), b = 2 - a + Math.floor(a/4);
  return Math.floor(365.25*(y+4716)) + Math.floor(30.6001*(m+1)) + d + b - 1524.5;
}

/* For a local civil date `iso`, return the exact instants (as JS Date, i.e.
 * UTC) bracketing its lunar cycle, plus the full moon within it. */
function moonEventsForDate(iso) {
  const y = +iso.slice(0,4), m = +iso.slice(5,7), d = +iso.slice(8,10);
  const jdNoon = greg2JD(y, m, d) + 0.5;
  const kApprox = (jdNoon - 2451550.09766) / 29.530588861;
  const k0 = Math.floor(kApprox);
  const cands = [-2,-1,0,1,2].map(o => k0 + o);
  const newTimes = cands.map(k => [k, moonPhaseJDE(k, false)]);
  const prev = newTimes.filter(t => t[1] <= jdNoon).reduce((a,b) => b[1] > a[1] ? b : a);
  const next = newTimes.filter(t => t[1] >  jdNoon).reduce((a,b) => b[1] < a[1] ? b : a);
  const fullJDE = moonPhaseJDE(prev[0], true);   // full moon of the SAME lunation as prev's new moon
  return {
    cycleStart: jdeToDate(prev[1], y),
    cycleEnd:   jdeToDate(next[1], y),
    fullMoon:   jdeToDate(fullJDE, y),
  };
}

function fmtLocalDateTime(date, tz) {
  if (!date) return "--";
  // en-GB, not ar-EG: an Arabic locale renders Arabic-Indic numerals and the
  // grid, the sun panel and the cycles tab all use Western digits. Two numeral
  // systems on one screen reads as a bug.
  const parts = new Intl.DateTimeFormat("en-GB", {
    timeZone: tz, day: "2-digit", month: "2-digit", year: "numeric",
    hour: "2-digit", minute: "2-digit", hour12: false,
  }).formatToParts(date);
  const g = (t) => parts.find(p => p.type === t).value;
  return `${g("day")}/${g("month")}/${g("year")} – ${g("hour")}:${g("minute")}`;
}

/* All new-moon, full-moon, and NASA-catalogued eclipse instants whose LOCAL
 * civil date (in `cityKey`'s timezone) falls within Gregorian month `y`-`m0`
 * (m0 is 0-11). Used to badge the grid -- see index.html's renderGrid(). */
function computeMonthMoonEvents(y, m0, cityKey) {
  const tz = CITIES[cityKey].tz;
  const localDateKey = (d) => new Intl.DateTimeFormat("en-CA", { timeZone: tz }).format(d); // YYYY-MM-DD

  const firstJD = greg2JD(y, m0 + 1, 1);
  const daysInMonth = new Date(Date.UTC(y, m0 + 1, 0)).getUTCDate();
  const lastJD = greg2JD(y, m0 + 1, daysInMonth);
  const kLo = Math.floor((firstJD - 2451550.09766) / 29.530588861) - 1;
  const kHi = Math.ceil((lastJD - 2451550.09766) / 29.530588861) + 1;

  const byDate = {};
  const add = (dateKey, entry) => { (byDate[dateKey] = byDate[dateKey] || []).push(entry); };

  for (let k = kLo; k <= kHi; k++) {
    const newD = jdeToDate(moonPhaseJDE(k, false), y);
    add(localDateKey(newD), { type: "new", time: newD });
    const fullD = jdeToDate(moonPhaseJDE(k, true), y);
    add(localDateKey(fullD), { type: "full", time: fullD });
  }
  for (const ev of LUNAR_ECLIPSES) {
    const d = new Date(ev.t);
    if (d.getUTCFullYear() < y - 1 || d.getUTCFullYear() > y + 1) continue;   // cheap pre-filter
    const key = localDateKey(d);
    if (key.slice(0, 4) == y && +key.slice(5, 7) == m0 + 1) {
      add(key, { type: "eclipse", time: d, kind: ev.k });
    }
  }
  return byDate;
}
