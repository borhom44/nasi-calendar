"""Sun times (fajr, sunrise, sunset/maghrib, isha) for any location and date.

Pure computation -- no API, no network. NOAA solar position algorithm, good to
about a minute below ~65 degrees latitude, well inside our display resolution.

Event definitions, as the sun's altitude relative to the horizon:

  fajr     -19.5   true dawn. Convention-dependent -- see ANGLES.
  sunrise   -0.833 upper limb touching the horizon: -0.5667 refraction plus
                   the sun's ~0.2667 semi-diameter. Sunrise is NOT altitude 0.
  sunset    -0.833 the same event descending. Maghrib is the same instant in
                   essentially every convention, so it is not computed twice.
  isha     -17.5   "no daylight left". True astronomical dark is -18.0; Egypt's
                   authority uses -17.5 (under two minutes apart at Cairo).

TIME ZONES: everything is solved in UTC and then converted with `zoneinfo`,
so DST is handled from the real IANA rules. This is not optional pedantry --
Egypt reinstated DST in 2023, so Cairo is UTC+3 in August and UTC+2 in
January. A fixed offset silently shifts half the year by an hour.

HIGH LATITUDE: above roughly 48.5 degrees the sun never reaches -18 in
midsummer, so fajr and isha genuinely DO NOT OCCUR on those dates -- night
never falls. This returns None rather than inventing a time. See
`persistent_twilight_days` to count them before choosing a city.
"""
import math
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

RAD = math.pi / 180.0

# name -> (fajr depression, isha depression); None isha means "maghrib + 90 min"
ANGLES = {
    "egyptian":     (19.5, 17.5),   # Egyptian General Authority of Survey
    "mwl":          (18.0, 17.0),   # Muslim World League
    "isna":         (15.0, 15.0),   # Islamic Society of North America
    "karachi":      (18.0, 18.0),   # Univ. of Islamic Sciences, Karachi
    "umm_alqura":   (18.5, None),   # Umm al-Qura (Saudi Arabia)
    "astronomical": (18.0, 18.0),   # pure astronomical twilight
}
SUN_DISC = -0.833


def _solar_params(jd):
    """(declination degrees, equation of time minutes) for a Julian Day."""
    T = (jd - 2451545.0) / 36525.0
    L0 = (280.46646 + T * (36000.76983 + T * 0.0003032)) % 360.0
    M = 357.52911 + T * (35999.05029 - 0.0001537 * T)
    e = 0.016708634 - T * (0.000042037 + 0.0000001267 * T)
    C = (math.sin(M * RAD) * (1.914602 - T * (0.004817 + 0.000014 * T))
         + math.sin(2 * M * RAD) * (0.019993 - 0.000101 * T)
         + math.sin(3 * M * RAD) * 0.000289)
    omega = 125.04 - 1934.136 * T
    lam = L0 + C - 0.00569 - 0.00478 * math.sin(omega * RAD)
    eps0 = 23.0 + (26.0 + (21.448 - T * (46.815 + T * (0.00059 - T * 0.001813))) / 60.0) / 60.0
    eps = eps0 + 0.00256 * math.cos(omega * RAD)
    decl = math.asin(math.sin(eps * RAD) * math.sin(lam * RAD)) / RAD

    y = math.tan(eps / 2 * RAD) ** 2
    eqtime = 4 * (y * math.sin(2 * L0 * RAD)
                  - 2 * e * math.sin(M * RAD)
                  + 4 * e * y * math.sin(M * RAD) * math.cos(2 * L0 * RAD)
                  - 0.5 * y * y * math.sin(4 * L0 * RAD)
                  - 1.25 * e * e * math.sin(2 * M * RAD)) / RAD
    return decl, eqtime


def _jd(d):
    y, m, dd = d.year, d.month, d.day
    if m <= 2:
        y, m = y - 1, m + 12
    a = y // 100
    b = 2 - a + a // 4
    return math.floor(365.25 * (y + 4716)) + math.floor(30.6001 * (m + 1)) + dd + b - 1524.5


def _hour_angle(lat, decl, altitude):
    """Degrees from solar noon to the given altitude, or None if never reached."""
    cos_h = ((math.sin(altitude * RAD) - math.sin(lat * RAD) * math.sin(decl * RAD))
             / (math.cos(lat * RAD) * math.cos(decl * RAD)))
    if not -1.0 <= cos_h <= 1.0:
        return None
    return math.acos(cos_h) / RAD


def sun_times(d, lat, lon, tzname, convention="egyptian"):
    """All four events for local date `d`, as timezone-aware local datetimes.

    lat/lon degrees, longitude POSITIVE EAST. tzname is an IANA zone
    ("Africa/Cairo"). Any value may be None where the event does not occur.
    """
    fajr_ang, isha_ang = ANGLES[convention]
    tz = ZoneInfo(tzname)
    jd = _jd(d) + 0.5 - lon / 360.0          # centre the solve on local noon
    decl, eqtime = _solar_params(jd)
    noon_utc = 720.0 - 4.0 * lon - eqtime    # minutes past 00:00 UTC

    def at(minutes):
        if minutes is None:
            return None
        base = datetime(d.year, d.month, d.day, tzinfo=timezone.utc)
        return (base + timedelta(minutes=minutes)).astimezone(tz)

    out = {"solar_noon": at(noon_utc)}
    for name, alt, sign in (("fajr", -fajr_ang, -1), ("sunrise", SUN_DISC, -1),
                            ("sunset", SUN_DISC, +1)):
        H = _hour_angle(lat, decl, alt)
        out[name] = at(None if H is None else noon_utc + sign * 4.0 * H)

    if isha_ang is None:                      # Umm al-Qura: fixed 90 min offset
        out["isha"] = out["sunset"] + timedelta(minutes=90) if out["sunset"] else None
    else:
        H = _hour_angle(lat, decl, -isha_ang)
        out["isha"] = at(None if H is None else noon_utc + 4.0 * H)
    return out


def hhmm(dt):
    return "--:--" if dt is None else dt.strftime("%H:%M")


def persistent_twilight_days(lat, lon, tzname, year, convention="egyptian"):
    """Days in `year` with no true night (fajr or isha undefined)."""
    n, d = 0, date(year, 1, 1)
    while d.year == year:
        t = sun_times(d, lat, lon, tzname, convention)
        if t["fajr"] is None or t["isha"] is None:
            n += 1
        d += timedelta(days=1)
    return n
