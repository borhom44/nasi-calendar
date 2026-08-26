"""Geocentric position of the Moon -- Python twin of docs/moon-position.js.

Meeus ch.47, abridged to the terms that matter at this resolution. The two
implementations carry the SAME coefficient tables, and tests/check_moon.py
compares them numerically; if they ever diverge, one of them has been edited
without the other.

This exists because the shipped moon-phase table was wrong in a way that was
easy to miss. generate_moon_phases.py computed illumination as

    (1 - cos(2*pi * fraction_of_lunation)) / 2

which assumes the Moon moves uniformly through its cycle. It does not: the
anomalistic month makes its angular speed vary by about 12 percent, so that
formula is up to 8.5 percentage points out near first and last quarter --
enough to show the wrong phase icon for a day. Real illumination needs the
real elongation, which needs the real longitude, which is this file.
"""
import math

RAD = math.pi / 180.0

# [D, M, M', F, l coefficient (1e-6 deg), r coefficient (1e-3 km)]
MOON_LR = [
    (0, 0, 1, 0, 6288774, -20905355), (2, 0, -1, 0, 1274027, -3699111),
    (2, 0, 0, 0, 658314, -2955968),   (0, 0, 2, 0, 213618, -569925),
    (0, 1, 0, 0, -185116, 48888),     (0, 0, 0, 2, -114332, -3149),
    (2, 0, -2, 0, 58793, 246158),     (2, -1, -1, 0, 57066, -152138),
    (2, 0, 1, 0, 53322, -170733),     (2, -1, 0, 0, 45758, -204586),
    (0, 1, -1, 0, -40923, -129620),   (1, 0, 0, 0, -34720, 108743),
    (0, 1, 1, 0, -30383, 104755),     (2, 0, 0, -2, 15327, 10321),
    (0, 0, 1, 2, -12528, 0),          (0, 0, 1, -2, 10980, 79661),
    (4, 0, -1, 0, 10675, -34782),     (0, 0, 3, 0, 10034, -23210),
    (4, 0, -2, 0, 8548, -21636),      (2, 1, -1, 0, -7888, 24208),
    (2, 1, 0, 0, -6766, 30824),       (1, 0, -1, 0, -5163, -8379),
    (1, 1, 0, 0, 4987, -16675),       (2, -1, 1, 0, 4036, -12831),
    (2, 0, 2, 0, 3994, -10445),       (4, 0, 0, 0, 3861, -11650),
    (2, 0, -3, 0, 3665, 14403),       (0, 1, -2, 0, -2689, -7003),
    (2, 0, -1, 2, -2602, 0),          (2, -1, -2, 0, 2390, 10056),
    (1, 0, 1, 0, -2348, 6322),        (2, -2, 0, 0, 2236, -9884),
    (0, 1, 2, 0, -2120, 5751),        (0, 2, 0, 0, -2069, 0),
    (2, -2, -1, 0, 2048, -4950),      (2, 0, 1, -2, -1773, 4130),
    (2, 0, 0, 2, -1595, 0),           (4, -1, -1, 0, 1215, -3958),
    (0, 0, 2, 2, -1110, 0),           (3, 0, -1, 0, -892, 3258),
    (2, 1, 1, 0, -810, 2616),         (4, -1, -2, 0, 759, -1897),
    (0, 2, -1, 0, -713, -2117),       (2, 2, -1, 0, -700, 2354),
    (2, 0, -1, -2, 0, 8752),
]

# [D, M, M', F, b coefficient (1e-6 deg)]
MOON_B = [
    (0, 0, 0, 1, 5128122), (0, 0, 1, 1, 280602), (0, 0, 1, -1, 277693),
    (2, 0, 0, -1, 173237), (2, 0, -1, 1, 55413), (2, 0, -1, -1, 46271),
    (2, 0, 0, 1, 32573),   (0, 0, 2, -1, 17198), (2, 0, 1, -1, 9266),
    (0, 0, 2, 1, 8822),    (2, -1, 0, -1, 8216), (2, 0, -2, -1, 4324),
    (2, 0, 1, 1, 4200),    (2, 1, 0, -1, -3359), (2, -1, -1, 1, 2463),
    (2, -1, 0, 1, 2211),   (2, -1, -1, -1, 2065), (0, 1, -1, -1, -1870),
    (4, 0, -1, -1, 1828),  (0, 1, 0, 1, -1794),  (0, 0, 0, 3, -1749),
    (0, 1, -1, 1, -1565),  (1, 0, 0, 1, -1491),  (0, 1, 1, 1, -1475),
    (0, 1, 1, -1, -1410),  (0, 1, 0, -1, -1344), (1, 0, 0, -1, -1335),
    (0, 0, 3, 1, 1107),    (4, 0, 0, -1, 1021),  (4, 0, -1, 1, 833),
]


def moon_position(jd):
    """Apparent geocentric (longitude deg, latitude deg, distance km)."""
    T = (jd - 2451545.0) / 36525.0

    Lp = (218.3164477 + 481267.88123421 * T - 0.0015786 * T ** 2
          + T ** 3 / 538841 - T ** 4 / 65194000)
    D = (297.8501921 + 445267.1114034 * T - 0.0018819 * T ** 2
         + T ** 3 / 545868 - T ** 4 / 113065000)
    M = 357.5291092 + 35999.0502909 * T - 0.0001536 * T ** 2 + T ** 3 / 24490000
    Mp = (134.9633964 + 477198.8675055 * T + 0.0087414 * T ** 2
          + T ** 3 / 69699 - T ** 4 / 14712000)
    F = (93.2720950 + 483202.0175233 * T - 0.0036539 * T ** 2
         - T ** 3 / 3526000 + T ** 4 / 863310000)

    E = 1 - 0.002516 * T - 0.0000074 * T * T

    def ecc(m):
        return 1.0 if m == 0 else (E if abs(m) == 1 else E * E)

    sum_l = sum_r = sum_b = 0.0
    for d, m, mp, f, cl, cr in MOON_LR:
        arg = (d * D + m * M + mp * Mp + f * F) * RAD
        sum_l += cl * ecc(m) * math.sin(arg)
        sum_r += cr * ecc(m) * math.cos(arg)
    for d, m, mp, f, cb in MOON_B:
        arg = (d * D + m * M + mp * Mp + f * F) * RAD
        sum_b += cb * ecc(m) * math.sin(arg)

    A1 = 119.75 + 131.849 * T
    A2 = 53.09 + 479264.290 * T
    A3 = 313.45 + 481266.484 * T
    sum_l += (3958 * math.sin(A1 * RAD) + 1962 * math.sin((Lp - F) * RAD)
              + 318 * math.sin(A2 * RAD))
    sum_b += (-2235 * math.sin(Lp * RAD) + 382 * math.sin(A3 * RAD)
              + 175 * math.sin((A1 - F) * RAD) + 175 * math.sin((A1 + F) * RAD)
              + 127 * math.sin((Lp - Mp) * RAD) - 115 * math.sin((Lp + Mp) * RAD))

    return ((Lp + sum_l / 1e6) % 360.0, sum_b / 1e6, 385000.56 + sum_r / 1000.0)


def solar_longitude(jd):
    """Apparent longitude of the Sun, degrees. Same series as solar_times.py."""
    T = (jd - 2451545.0) / 36525.0
    L0 = (280.46646 + T * (36000.76983 + T * 0.0003032)) % 360.0
    M = 357.52911 + T * (35999.05029 - 0.0001537 * T)
    C = (math.sin(M * RAD) * (1.914602 - T * (0.004817 + 0.000014 * T))
         + math.sin(2 * M * RAD) * (0.019993 - 0.000101 * T)
         + math.sin(3 * M * RAD) * 0.000289)
    omega = 125.04 - 1934.136 * T
    return (L0 + C - 0.00569 - 0.00478 * math.sin(omega * RAD)) % 360.0


def sun_distance_km(jd):
    """Earth-Moon barycentre to Sun, kilometres."""
    T = (jd - 2451545.0) / 36525.0
    M = (357.52911 + T * (35999.05029 - 0.0001537 * T)) * RAD
    e = 0.016708634 - T * (0.000042037 + 0.0000001267 * T)
    C = (math.sin(M) * (1.914602 - T * (0.004817 + 0.000014 * T))
         + math.sin(2 * M) * (0.019993 - 0.000101 * T)
         + math.sin(3 * M) * 0.000289)
    v = M + C * RAD
    return (1.000001018 * (1 - e * e)) / (1 + e * math.cos(v)) * 149597870.7


def illuminated_fraction(jd):
    """True illuminated fraction of the Moon's disc, 0-1.

    NOT (1 - cos(2*pi*phase))/2. That idealisation assumes uniform motion
    through the lunation and is up to 8.5 points out near the quarters.
    """
    lon, lat, dist = moon_position(jd)
    sun_lon = solar_longitude(jd)
    elong = math.acos(
        max(-1.0, min(1.0, math.cos(lat * RAD) * math.cos((lon - sun_lon) * RAD)))
    )
    sun_km = sun_distance_km(jd)
    i = math.atan2(sun_km * math.sin(elong), dist - sun_km * math.cos(elong))
    return (1 + math.cos(i)) / 2
