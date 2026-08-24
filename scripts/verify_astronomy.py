"""Check the reconstructed calendar against real astronomy.

Nothing here reads the book. The question is not "did we copy the table
correctly" (build_calendar.py answers that) but "does the table describe the
actual sky". Three independent tests:

  1. LUNATION   -- does every month start at a real astronomical new moon?
  2. FULL MOON  -- does the full moon land on day 14/15, as the book claims
                   it must (p.15) for 29-day/30-day months respectively?
  3. SOLAR LOCK -- does the Nasi' intercalation actually hold the lunar year
                   against the solar year, or does it drift like a pure
                   lunar calendar (~11 days/yr)?

Moon phase instants come from Meeus, *Astronomical Algorithms* 2nd ed., ch.49
(the standard truncated ELP series), including the 14 planetary-argument
corrections. Quoted accuracy vs. full theory is a few seconds of time -- many
orders of magnitude finer than the one-day resolution we are testing at, so
the algorithm is not the limiting factor in anything below.
"""
import json
import math
from datetime import date, timedelta

DAYS = r"C:\Dev\nasi-calendar\data\nasi_days.json"
MONTHS = r"C:\Dev\nasi-calendar\data\nasi_months.json"
NASA = r"C:\Dev\nasi-calendar\data\nasa_5MKLE_catalog.txt"
OUT = r"C:\Dev\nasi-calendar\data\astronomy_report.txt"

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


def moon_phase_jde(k, full=False):
    """JDE (Dynamical Time) of the new moon (full=False) or full moon."""
    if full:
        k += 0.5
    T, E, M, Mp, F, Om, jde = _args(k)
    if not full:
        c = (-0.40720 * math.sin(Mp) + 0.17241 * E * math.sin(M)
             + 0.01608 * math.sin(2 * Mp) + 0.01039 * math.sin(2 * F)
             + 0.00739 * E * math.sin(Mp - M) - 0.00514 * E * math.sin(Mp + M)
             + 0.00208 * E * E * math.sin(2 * M))
    else:
        c = (-0.40614 * math.sin(Mp) + 0.17302 * E * math.sin(M)
             + 0.01614 * math.sin(2 * Mp) + 0.01043 * math.sin(2 * F)
             + 0.00734 * E * math.sin(Mp - M) - 0.00515 * E * math.sin(Mp + M)
             + 0.00209 * E * E * math.sin(2 * M))
    c += (-0.00111 * math.sin(Mp - 2 * F) - 0.00057 * math.sin(Mp + 2 * F)
          + 0.00056 * E * math.sin(2 * Mp + M) - 0.00042 * math.sin(3 * Mp)
          + 0.00042 * E * math.sin(M + 2 * F) + 0.00038 * E * math.sin(M - 2 * F)
          - 0.00024 * E * math.sin(2 * Mp - M) - 0.00017 * math.sin(Om)
          - 0.00007 * math.sin(Mp + 2 * M) + 0.00004 * math.sin(2 * Mp - 2 * F)
          + 0.00004 * math.sin(3 * M) + 0.00003 * math.sin(Mp + M - 2 * F)
          + 0.00003 * math.sin(2 * Mp + 2 * F) - 0.00003 * math.sin(Mp + M + 2 * F)
          + 0.00003 * math.sin(Mp - M + 2 * F) - 0.00002 * math.sin(Mp - M - 2 * F)
          - 0.00002 * math.sin(3 * Mp + M) + 0.00002 * math.sin(4 * Mp))
    return jde + c + _planetary(k, T)


def delta_t_seconds(y):
    """NASA/Espenak-Meeus polynomial for 2005-2150 (this range only)."""
    if y < 2050:
        t = y - 2000
        return 62.92 + 0.32217 * t + 0.005589 * t * t
    if y < 2150:
        return -20 + 32 * ((y - 1820) / 100.0) ** 2 - 0.5628 * (2150 - y)
    return 0.0


def jd_to_date(jd):
    z = math.floor(jd + 0.5)
    f = (jd + 0.5) - z
    if z < 2299161:
        a = z
    else:
        alpha = math.floor((z - 1867216.25) / 36524.25)
        a = z + 1 + alpha - math.floor(alpha / 4)
    b = a + 1524
    c = math.floor((b - 122.1) / 365.25)
    d = math.floor(365.25 * c)
    e = math.floor((b - d) / 30.6001)
    day = b - d - math.floor(30.6001 * e) + f
    month = e - 1 if e < 14 else e - 13
    year = c - 4716 if month > 2 else c - 4715
    return int(year), int(month), day


def phase_dates(full=False):
    """Every phase instant 1999-2101, as (UTC civil date, fractional day)."""
    out = []
    for k in range(-20, 1270):
        jde = moon_phase_jde(k, full=full)
        y, m, d = jd_to_date(jde)
        if not (1999 <= y <= 2101):
            continue
        jd_ut = jde - delta_t_seconds(y) / 86400.0
        y, m, d = jd_to_date(jd_ut)
        out.append((date(y, m, int(d)), d - int(d)))
    return out


def main():
    months = json.load(open(MONTHS, encoding="utf-8"))
    days = json.load(open(DAYS, encoding="utf-8"))
    by_date = {d["g"]: d for d in days}
    rep = []

    # ---- 1. every month start vs. the real new moon ----------------------
    newmoons = phase_dates(full=False)
    nm_dates = [d for d, _ in newmoons]
    offsets = {}
    worst = []
    for mo in months[1:]:                      # skip the truncated opening run
        start = date.fromisoformat(mo["start"])
        nearest = min(nm_dates, key=lambda d: abs((start - d).days))
        off = (start - nearest).days
        offsets[off] = offsets.get(off, 0) + 1
        if abs(off) > 2:
            worst.append((mo["start"], mo["nm"], off))
    rep.append("1. MONTH START vs. ASTRONOMICAL NEW MOON")
    rep.append(f"   month starts tested: {sum(offsets.values())}")
    for off in sorted(offsets):
        n = offsets[off]
        rep.append(f"     start = new moon {off:+d} day(s): {n:5d}  ({100*n/sum(offsets.values()):5.1f}%)")
    rep.append(f"   |offset| > 2 days: {len(worst)} {worst[:5]}")

    # ---- 2. full moon vs. day 14/15 --------------------------------------
    fulls = phase_dates(full=True)
    hist, missing = {}, 0
    for d, _ in fulls:
        rec = by_date.get(d.isoformat())
        if rec is None:
            missing += 1
            continue
        hist[rec["nd"]] = hist.get(rec["nd"], 0) + 1
    tot = sum(hist.values())
    rep.append("")
    rep.append("2. FULL MOON vs. DAY OF MONTH  (book p.15 predicts 14 or 15)")
    rep.append(f"   full moons tested: {tot}")
    for dnum in sorted(hist):
        n = hist[dnum]
        bar = "#" * int(60 * n / max(hist.values()))
        rep.append(f"     day {dnum:2d}: {n:5d} ({100*n/tot:5.1f}%) {bar}")
    in_window = sum(n for d, n in hist.items() if d in (14, 15))
    rep.append(f"   on day 14 or 15: {in_window}/{tot} = {100*in_window/tot:.1f}%")
    rep.append(f"   on day 13-16   : {sum(n for d,n in hist.items() if 13<=d<=16)}/{tot}"
               f" = {100*sum(n for d,n in hist.items() if 13<=d<=16)/tot:.1f}%")

    # ---- 3. does the intercalation hold the solar year? ------------------
    rep.append("")
    rep.append("3. SOLAR LOCK -- Gregorian date on which each Hijri year opens")
    firsts = [m for m in months if m["nm"] == "صفر الأول"]
    doy = []
    for m in firsts:
        d = date.fromisoformat(m["start"])
        doy.append((m["ny"], d, d.timetuple().tm_yday))
    rep.append(f"   years tested: {len(doy)}")
    rep.append(f"   earliest opening: {min(doy, key=lambda t: t[2])[1]}  "
               f"latest opening: {max(doy, key=lambda t: t[2])[1]}")
    span = max(t[2] for t in doy) - min(t[2] for t in doy)
    rep.append(f"   spread in day-of-year: {span} days")
    rep.append(f"   (a pure lunar calendar drifts ~11 days/yr = ~1100 days over this range,")
    rep.append(f"    i.e. it would wander through every season several times over)")
    rep.append("   sample openings:")
    for ny, d, n in doy[:3] + doy[len(doy)//2:len(doy)//2+2] + doy[-3:]:
        rep.append(f"     {ny}: {d}  (day {n} of the Gregorian year)")

    # ---- 4. NASA's own lunar eclipse catalog -----------------------------
    # The book cites this exact file (p.15) as what it used to fix month
    # lengths, so it is the author's own stated standard. A lunar eclipse can
    # only occur at full moon, so every entry must land mid-month.
    rep.append("")
    rep.append("4. NASA 5-MILLENNIUM LUNAR ECLIPSE CATALOG (Espenak & Meeus, NASA/TP-2009-214173)")
    try:
        with open(NASA, encoding="utf-8", errors="replace") as f:
            cat = f.read().splitlines()
    except FileNotFoundError:
        rep.append("   catalog not present -- skipped")
        cat = []

    MON = {m: i + 1 for i, m in enumerate(
        ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])}
    ehist, ehist_vis, n_tot, n_vis = {}, {}, 0, 0
    for line in cat:
        p = line.split()
        if len(p) < 10 or p[2] not in MON:
            continue
        try:
            y, dd = int(p[1]), int(p[3])
            hh, mm, ss = (int(v) for v in p[4].split(":"))
            dt_s, etype = int(p[5]), p[8]
        except (ValueError, IndexError):
            continue
        if not (2000 <= y <= 2100):
            continue
        # catalogue time is TD; convert to UT before taking the civil date
        inst = date(y, MON[p[2]], dd)
        frac = (hh * 3600 + mm * 60 + ss - dt_s) / 86400.0
        while frac < 0:
            inst, frac = inst - timedelta(days=1), frac + 1
        while frac >= 1:
            inst, frac = inst + timedelta(days=1), frac - 1
        rec = by_date.get(inst.isoformat())
        if rec is None:
            continue
        n_tot += 1
        ehist[rec["nd"]] = ehist.get(rec["nd"], 0) + 1
        if etype.startswith(("P", "T")):        # umbral: visible to the eye
            n_vis += 1
            ehist_vis[rec["nd"]] = ehist_vis.get(rec["nd"], 0) + 1

    if n_tot:
        rep.append(f"   eclipses in range: {n_tot}  (of which umbral/visible: {n_vis})")
        rep.append("   ALL eclipses, by day of our month:")
        for dnum in sorted(ehist):
            rep.append(f"     day {dnum:2d}: {ehist[dnum]:4d} ({100*ehist[dnum]/n_tot:5.1f}%)")
        rep.append("   UMBRAL only (penumbral ones are invisible to the naked eye):")
        for dnum in sorted(ehist_vis):
            rep.append(f"     day {dnum:2d}: {ehist_vis[dnum]:4d} ({100*ehist_vis[dnum]/n_vis:5.1f}%)")
        w = sum(n for d, n in ehist.items() if d in (14, 15))
        rep.append(f"   on day 14 or 15: {w}/{n_tot} = {100*w/n_tot:.1f}%")
        w4 = sum(n for d, n in ehist.items() if 13 <= d <= 16)
        rep.append(f"   on day 13-16   : {w4}/{n_tot} = {100*w4/n_tot:.1f}%")

    # ---- 5. constants implied by the calendar itself ---------------------
    # If the table were invented, its emergent constants would be arbitrary.
    # If it tracks the sky, they must reproduce the synodic month and the
    # tropical year without ever having been told either number.
    rep.append("")
    rep.append("5. CONSTANTS THE TABLE IMPLIES (nothing here is fitted -- these fall out)")
    inner = months[1:-1]                       # drop both truncated edge runs
    span_days = sum(m["len"] for m in inner)
    mean_syn = span_days / len(inner)
    rep.append(f"   mean month length over {len(inner)} months : {mean_syn:.6f} days")
    rep.append(f"   true mean synodic month (Meeus)           : 29.530589 days")
    rep.append(f"   error                                     : {abs(mean_syn-29.530589)*86400:+.1f} seconds/month")

    yr_lens = []
    for a, b in zip(firsts, firsts[1:]):
        if b["ny"] == a["ny"] + 1:
            yr_lens.append((date.fromisoformat(b["start"]) - date.fromisoformat(a["start"])).days)
    mean_yr = sum(yr_lens) / len(yr_lens)
    rep.append(f"   mean year length over {len(yr_lens)} years      : {mean_yr:.6f} days")
    rep.append(f"   mean tropical year (Meeus, J2000)         : 365.242190 days")
    rep.append(f"   error                                     : {(mean_yr-365.242190)*24*60:+.1f} minutes/year")
    rep.append(f"   -> drift over the full 101-year table     : {(mean_yr-365.242190)*len(yr_lens):+.2f} days")
    rep.append(f"   for contrast, a pure 12-month lunar year  : {12*29.530589:.3f} days"
               f"  ({12*29.530589-365.242190:+.1f} days/yr, ~{abs(12*29.530589-365.242190)*101:.0f} days over the table)")
    rep.append(f"   Nasi' months inserted: {sum(1 for m in months if m['nm']=='نسيء')} in {len(yr_lens)+1} years"
               f"  = {sum(1 for m in months if m['nm']=='نسيء')/(len(yr_lens)+1):.4f}/yr"
               f"  (Metonic ideal 7/19 = {7/19:.4f})")

    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(rep))
    # Windows consoles are cp1252 here; the report contains Arabic month names,
    # so echo it transliteration-safe and leave the real text in the file.
    print("\n".join(rep).encode("ascii", "replace").decode("ascii"))
    print(f"\nfull report: {OUT}")


if __name__ == "__main__":
    main()
