"""Per-day moon illumination and age, for the calendar's visual moon-phase
display. Self-contained (duplicates the Meeus new-moon series already used
and validated in verify_astronomy.py), matching this repo's convention of
each script owning its own small astronomy helpers.

Output is deliberately NOT a re-derivation of the Nasi' calendar -- the
moon's actual phase on any given Gregorian day is independent of which
calendar you're reading it through, so this file has nothing to do with
build_calendar.py's logic. It exists purely to paint an accurate picture next
to the date, using the same precision series already checked against NASA's
eclipse catalog earlier in this project.
"""
import json
import math
import sys
from pathlib import Path

# Derived from this file rather than hardcoded: the absolute Windows paths
# these scripts carried meant none of them could run on the VPS.
REPO = Path(__file__).resolve().parent.parent
DAYS = str(REPO / "data" / "nasi_days.json")
OUT_JSON = str(REPO / "data" / "moon_phases.json")
OUT_JS = str(REPO / "docs" / "moon-phases-data.js")

RAD = math.pi / 180.0


def _args(k):
    T = k / 1236.85
    E = 1 - 0.002516 * T - 0.0000074 * T * T
    M = 2.5534 + 29.10535670 * k - 0.0000014 * T**2 - 0.00000011 * T**3
    Mp = (201.5643 + 385.81693528 * k + 0.0107582 * T**2
          + 0.00001238 * T**3 - 0.000000058 * T**4)
    F = (160.7108 + 390.67050284 * k - 0.0016118 * T**2
         - 0.00000227 * T**3 + 0.000000011 * T**4)
    Om = 124.7746 - 1.56375588 * k + 0.0020672 * T**2 + 0.00000215 * T**3
    jde = (2451550.09766 + 29.530588861 * k + 0.00015437 * T**2
           - 0.000000150 * T**3 + 0.00000000073 * T**4)
    return T, E, M * RAD, Mp * RAD, F * RAD, Om * RAD, jde


_A_COEF = [(299.77, 0.107408, 0.000325), (251.88, 0.016321, 0.000165),
           (251.83, 26.651886, 0.000164), (349.42, 36.412478, 0.000126),
           (84.66, 18.206239, 0.000110), (141.74, 53.303771, 0.000062),
           (207.14, 2.453732, 0.000060), (154.84, 7.306860, 0.000056),
           (34.52, 27.261239, 0.000047), (207.19, 0.121824, 0.000042),
           (291.34, 1.844379, 0.000040), (161.72, 24.198154, 0.000037),
           (239.56, 25.513099, 0.000035), (331.55, 3.592518, 0.000023)]


def _planetary(k, T):
    tot = 0.0
    for i, (a, b, c) in enumerate(_A_COEF):
        ang = a + b * k
        if i == 0:
            ang -= 0.009173 * T * T
        tot += c * math.sin(ang * RAD)
    return tot


def new_moon_jde(k):
    T, E, M, Mp, F, Om, jde = _args(k)
    c = (-0.40720 * math.sin(Mp) + 0.17241 * E * math.sin(M)
         + 0.01608 * math.sin(2 * Mp) + 0.01039 * math.sin(2 * F)
         + 0.00739 * E * math.sin(Mp - M) - 0.00514 * E * math.sin(Mp + M)
         + 0.00208 * E * E * math.sin(2 * M)
         - 0.00111 * math.sin(Mp - 2 * F) - 0.00057 * math.sin(Mp + 2 * F)
         + 0.00056 * E * math.sin(2 * Mp + M) - 0.00042 * math.sin(3 * Mp)
         + 0.00042 * E * math.sin(M + 2 * F) + 0.00038 * E * math.sin(M - 2 * F)
         - 0.00024 * E * math.sin(2 * Mp - M) - 0.00017 * math.sin(Om)
         - 0.00007 * math.sin(Mp + 2 * M) + 0.00004 * math.sin(2 * Mp - 2 * F)
         + 0.00004 * math.sin(3 * M) + 0.00003 * math.sin(Mp + M - 2 * F)
         + 0.00003 * math.sin(2 * Mp + 2 * F) - 0.00003 * math.sin(Mp + M + 2 * F)
         + 0.00003 * math.sin(Mp - M + 2 * F) - 0.00002 * math.sin(Mp - M - 2 * F)
         - 0.00002 * math.sin(3 * Mp + M) + 0.00002 * math.sin(4 * Mp))
    return jde + c + _planetary(k, T)


def greg_to_jd(y, m, d):
    if m <= 2:
        y, m = y - 1, m + 12
    a = y // 100
    b = 2 - a + a // 4
    return math.floor(365.25 * (y + 4716)) + math.floor(30.6001 * (m + 1)) + d + b - 1524.5


sys.path.insert(0, str(Path(__file__).resolve().parent))
from moon_position import illuminated_fraction  # noqa: E402


def main():
    days = json.load(open(DAYS, encoding="utf-8"))
    out = []
    k_prev_new = None
    for rec in days:
        y, m, d = int(rec["g"][:4]), int(rec["g"][5:7]), int(rec["g"][8:10])
        jd_noon = greg_to_jd(y, m, d) + 0.5    # local civil noon, plenty for a day-level figure

        k_approx = (jd_noon - 2451550.09766) / 29.530588861
        k0 = math.floor(k_approx)
        # scan a small bracket -- the periodic correction terms can shift the
        # true instant by up to ~0.6 day from the linear estimate
        candidates = sorted(k0 + o for o in (-2, -1, 0, 1, 2))
        times = [(k, new_moon_jde(k)) for k in candidates]
        prev_k, prev_jd = max((t for t in times if t[1] <= jd_noon), key=lambda t: t[1])
        next_k, next_jd = min((t for t in times if t[1] > jd_noon), key=lambda t: t[1])

        age = jd_noon - prev_jd

        # Illumination comes from the Moon's ACTUAL elongation from the Sun,
        # not from how far through the lunation the day sits. The old formula
        #     (1 - cos(2*pi * age / synodic)) / 2
        # assumed uniform motion; the anomalistic month varies the Moon's
        # speed by ~12%, so it ran up to 8.5 points out near the quarters --
        # enough to show the wrong phase icon. See moon_position.py.
        illum = round(100 * illuminated_fraction(jd_noon))
        out.append([illum, round(age, 1)])

    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(out, f, separators=(",", ":"))
    with open(OUT_JS, "w", encoding="utf-8") as f:
        f.write("const MOON_PHASES = " + json.dumps(out, separators=(",", ":")) + ";\n")
    print(f"wrote {len(out)} days -> {OUT_JSON} and {OUT_JS}")

    # spot-check against the well-known full moon this project already used
    idx = next(i for i, r in enumerate(days) if r["g"] == "2026-10-12")
    print(f"2026-10-12 (Ramadan 1 / new moon expected): illum={out[idx][0]}% age={out[idx][1]}d")
    idx2 = next(i for i, r in enumerate(days) if r["g"] == "2026-10-26")
    print(f"2026-10-26 (~14d later, full moon expected): illum={out[idx2][0]}% age={out[idx2][1]}d")


if __name__ == "__main__":
    main()
