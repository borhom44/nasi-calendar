/* Sun times (fajr, sunrise, sunset/maghrib, isha) -- JS port of
 * scripts/solar_times.py. Same NOAA algorithm, same event definitions; see
 * that file's docstring for why each angle is what it is.
 *
 * Time zones: solved in UTC, then rendered via Intl.DateTimeFormat with an
 * explicit IANA zone, which uses the browser's own tz database -- so DST
 * (e.g. Cairo's reinstated EEST) is handled from real rules, not a fixed
 * offset, exactly like the Python side's zoneinfo.
 */
const RAD = Math.PI / 180;
const SUN_DISC = -0.833;
const SOLAR_ANGLES = { egyptian: [19.5, 17.5], mwl: [18.0, 17.0], isna: [15.0, 15.0] };

const CITIES = {
  cairo:     { label: "القاهرة",   lat: 30.0444, lon: 31.2357, tz: "Africa/Cairo" },
  barcelona: { label: "برشلونة",   lat: 41.3874, lon: 2.1686,  tz: "Europe/Madrid" },
};

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
 * {fajr,sunrise,sunset,isha,solarNoon}: JS Date objects (UTC instants), or
 * null where the event does not occur (high-latitude persistent twilight). */
function sunTimes(iso, cityKey, convention) {
  convention = convention || "egyptian";
  const city = CITIES[cityKey];
  const [fajrAng, ishaAng] = SOLAR_ANGLES[convention];
  const y = +iso.slice(0,4), m = +iso.slice(5,7), d = +iso.slice(8,10);
  const jd = _jdUTC(y, m, d) + 0.5 - city.lon / 360.0;
  const { decl, eqtime } = _solarParams(jd);
  const noonUTC = 720.0 - 4.0 * city.lon - eqtime;   // minutes past 00:00 UTC on `iso`

  const at = (minutes) => minutes === null ? null
    : new Date(Date.UTC(y, m - 1, d) + minutes * 60000);

  const hFajr = _hourAngle(city.lat, decl, -fajrAng);
  const hRise = _hourAngle(city.lat, decl, SUN_DISC);
  const hIsha = _hourAngle(city.lat, decl, -ishaAng);

  return {
    solarNoon: at(noonUTC),
    fajr:    at(hFajr === null ? null : noonUTC - 4*hFajr),
    sunrise: at(hRise === null ? null : noonUTC - 4*hRise),
    sunset:  at(hRise === null ? null : noonUTC + 4*hRise),
    isha:    at(hIsha === null ? null : noonUTC + 4*hIsha),
  };
}

function fmtLocal(date, tz) {
  if (!date) return "--:--";
  return new Intl.DateTimeFormat("en-GB", { timeZone: tz, hour: "2-digit", minute: "2-digit", hour12: false }).format(date);
}
