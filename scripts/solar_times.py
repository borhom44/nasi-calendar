"""Sun times for any location and date.

Pure computation -- no API, no network. NOAA solar position algorithm, good to
about a minute below ~65 degrees latitude, well inside our display resolution.

Four events, as the sun's altitude relative to the horizon:

  first_light  -18.0   the sky begins to lighten (astronomical twilight begins)
  sunrise       -0.833 upper limb touching the horizon: -0.5667 refraction plus
                       the sun's ~0.2667 semi-diameter. Sunrise is NOT altitude 0.
  sunset        -0.833 the same event descending.
  full_dark    -18.0   the last daylight is gone (astronomical twilight ends)

There is exactly ONE definition per event. This is an astronomical calendar,
not a prayer-times app: nothing here is regional, juristic, or configurable,
and the old ANGLES table of fajr/isha conventions was removed deliberately.
Solar noon is not computed -- it is used internally to solve the hour angles
and is not an event anyone asked to see.

TIME ZONES: everything is solved in UTC and then converted with `zoneinfo`,
so DST is handled from the real IANA rules. This is not optional pedantry --
Egypt reinstated DST in 2023, so Cairo is UTC+3 in August and UTC+2 in
January. A fixed offset silently shifts half the year by an hour.

HIGH LATITUDE: above 48.56 degrees (= 90 - 23.44 - 18) the sun never reaches
-18 at midsummer, so first_light and full_dark genuinely DO NOT OCCUR on those
dates -- night never falls. This returns None rather than inventing a time.
See `white_night_days` to count them for a city.
"""
import math
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

RAD = math.pi / 180.0

SUN_DISC = -0.833       # upper limb on the horizon
TWILIGHT = -18.0        # astronomical twilight, both ends

# Latitude above which midsummer has no astronomical night at all.
WHITE_NIGHT_LAT = 90.0 - 23.44 - 18.0     # 48.56

# Labels live in data/strings.json; import sun_events(lang) from strings.py.
# This module computes instants and knows nothing about how they are worded,
# which is what lets one code path emit a feed in any language.


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


def sun_times(d, lat, lon, tzname):
    """All four events for local date `d`, as timezone-aware local datetimes.

    lat/lon degrees, longitude POSITIVE EAST. tzname is an IANA zone
    ("Africa/Cairo"). first_light and full_dark may be None at high latitude
    in summer; sunrise and sunset may be None inside the polar circles.
    """
    tz = ZoneInfo(tzname)
    jd = _jd(d) + 0.5 - lon / 360.0          # centre the solve on local noon
    decl, eqtime = _solar_params(jd)
    noon_utc = 720.0 - 4.0 * lon - eqtime    # minutes past 00:00 UTC

    def at(minutes):
        if minutes is None:
            return None
        base = datetime(d.year, d.month, d.day, tzinfo=timezone.utc)
        return (base + timedelta(minutes=minutes)).astimezone(tz)

    out = {}
    for name, alt, sign in (("first_light", TWILIGHT, -1),
                            ("sunrise", SUN_DISC, -1),
                            ("sunset", SUN_DISC, +1),
                            ("full_dark", TWILIGHT, +1)):
        H = _hour_angle(lat, decl, alt)
        out[name] = at(None if H is None else noon_utc + sign * 4.0 * H)
    return out


def hhmm(dt):
    return "--:--" if dt is None else dt.strftime("%H:%M")


def day_length(t):
    """Seconds of daylight from a sun_times() dict, or None inside a polar day."""
    if t["sunrise"] is None or t["sunset"] is None:
        return None
    return (t["sunset"] - t["sunrise"]).total_seconds()


def white_night_days(lat, lon, tzname, year):
    """Days in `year` with no astronomical night (first_light or full_dark absent).

    Zero below WHITE_NIGHT_LAT. Measured: Berlin 69, London 59, Paris 19.
    """
    n, d = 0, date(year, 1, 1)
    while d.year == year:
        t = sun_times(d, lat, lon, tzname)
        if t["first_light"] is None or t["full_dark"] is None:
            n += 1
        d += timedelta(days=1)
    return n
