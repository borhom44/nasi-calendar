"""When did the Nasi' calendar and the official Hijri calendar separate?

Both calendars are lunar and ride the same lunations. The only structural
difference is that this one inserts a 13th month roughly every third year while
the official Hijri calendar never does. So the official calendar's year number
gains on ours at a fixed rate, and the separation point is simply where that
gap goes to zero.

The gap rate is MEASURED from the 2000-2100 table rather than assumed, then
extrapolated back. That extrapolation is the whole load-bearing assumption --
see the caveat printed at the end.

Official Hijri here is the tabular/civil Islamic calendar (the standard
arithmetic scheme). Observational and Umm al-Qura variants differ by a day or
two on month starts, which is far below the resolution of a question about
which *year* things separated in.
"""
import json
import math

DAYS = r"C:\Dev\nasi-calendar\data\nasi_days.json"
MONTHS = r"C:\Dev\nasi-calendar\data\nasi_months.json"
OUT = r"C:\Dev\nasi-calendar\data\divergence_report.txt"

ISLAMIC_EPOCH_JD = 1948439.5      # 1 Muharram 1 AH = Fri 16 July 622 CE (Julian)


def greg_to_jd(y, m, d):
    if m <= 2:
        y, m = y - 1, m + 12
    a = y // 100
    b = 2 - a + a // 4
    return math.floor(365.25 * (y + 4716)) + math.floor(30.6001 * (m + 1)) + d + b - 1524.5


def islamic_to_jd(y, m, d):
    return (d + math.ceil(29.5 * (m - 1)) + (y - 1) * 354
            + math.floor((3 + 11 * y) / 30.0) + ISLAMIC_EPOCH_JD - 1)


def jd_to_islamic(jd):
    jd = math.floor(jd) + 0.5
    y = int(math.floor((30 * (jd - ISLAMIC_EPOCH_JD) + 10646) / 10631.0))
    m = max(1, int(min(12, math.ceil((jd - islamic_to_jd(y, 1, 1) + 1) / 29.5))))
    d = int(jd - islamic_to_jd(y, m, 1)) + 1
    # The 29.5-day average over-estimates the month on the LAST day of a
    # 30-day month, yielding day 0 of the next month (~6 days a year).
    # Walk back until the day is valid rather than trusting the estimate.
    while d < 1:
        m -= 1
        if m < 1:
            y -= 1
            m = 12
        d = int(jd - islamic_to_jd(y, m, 1)) + 1
    return y, m, d


def main():
    days = json.load(open(DAYS, encoding="utf-8"))
    months = json.load(open(MONTHS, encoding="utf-8"))
    rep = []

    # --- sanity: does the tabular Hijri implementation look right? --------
    rep.append("SANITY CHECK -- tabular Hijri for a few known dates")
    for g in ["2000-01-01", "2026-08-20", "2026-10-12", "2100-12-31"]:
        y, m, d = (int(g[:4]), int(g[5:7]), int(g[8:10]))
        hy, hm, hd = jd_to_islamic(greg_to_jd(y, m, d))
        ours = next(r for r in days if r["g"] == g)
        rep.append(f"   {g}: official Hijri {hd:2d}/{hm:02d}/{hy}   |   Nasi' calendar "
                   f"{ours['nd']:2d} {ours['nm']} {ours['ny']}")

    # --- measure how fast the year-number gap grows -----------------------
    rep.append("")
    rep.append("1. YEAR-NUMBER GAP (official Hijri year minus Nasi' year), measured")
    samples = []
    for r in days:
        if r["g"].endswith("-07-01"):                    # one sample per year
            y, m, d = int(r["g"][:4]), 7, 1
            hy, _, _ = jd_to_islamic(greg_to_jd(y, m, d))
            samples.append((y, hy, r["ny"], hy - r["ny"]))
    for s in samples[:3] + samples[len(samples)//2:len(samples)//2+2] + samples[-3:]:
        rep.append(f"   {s[0]} CE: official {s[1]}  ours {s[2]}  gap {s[3]}")

    first, last = samples[0], samples[-1]
    span_our_years = last[2] - first[2]
    gap_growth = last[3] - first[3]
    rate = gap_growth / span_our_years
    rep.append(f"   gap grew {first[3]} -> {last[3]} (= {gap_growth}) across {span_our_years} Nasi' years")
    rep.append(f"   measured rate: {rate:.6f} extra official-years per Nasi' year")

    # theoretical rate from the intercalation density
    n_nasi = sum(1 for m in months if m["nm"] == "نسيء")
    n_years = len({m["ny"] for m in months}) - 1
    theo = (n_nasi / n_years) / 12.0
    rep.append(f"   theoretical rate from {n_nasi} insertions / {n_years} yrs: {theo:.6f}")

    # --- extrapolate the gap back to zero ---------------------------------
    rep.append("")
    rep.append("2. EXTRAPOLATING THE GAP BACK TO ZERO")
    ny_now, gap_now = last[2], last[3]
    for label, r in (("measured rate", rate), ("theoretical rate", theo)):
        back = gap_now / r
        y0 = ny_now - back
        # Gregorian year of that Nasi' year: our years are ~solar
        greg0 = last[0] - back
        rep.append(f"   using {label} ({r:.6f}):")
        rep.append(f"     {back:.1f} Nasi' years before {last[0]} CE")
        rep.append(f"     -> separation at Nasi' year {y0:+.1f}, i.e. about {greg0:.0f} CE")

    rep.append("")
    rep.append("3. WHAT THAT MEANS")
    rep.append("   Both calendars are anchored to the same epoch (year 1 = 622 CE):")
    rep.append(f"     official Hijri year 1 -> 622 CE (lunar years, ~354.37 d)")
    y1 = last[0] - (last[2] - 1) * 365.29 / 365.2425
    rep.append(f"     Nasi' year 1          -> {y1:.0f} CE (solar-locked years, ~365.29 d)")
    rep.append("   They share an epoch but count differently, so the year NUMBERS")
    rep.append("   separate essentially at the epoch itself -- not centuries later.")

    rep.append("")
    rep.append("CAVEAT -- this is extrapolation, not data.")
    rep.append("   The source table covers 2000-2100 CE only. Everything above assumes the")
    rep.append("   intercalation rate held steady for ~1400 years. The book states it built")
    rep.append("   the calendar from 513 CE, and describes longer correction cycles, so the")
    rep.append("   real historical rate is very unlikely to be exactly constant.")
    rep.append("   The book's own 513-2000 charts would answer this from data; they are in")
    rep.append("   neither PDF supplied here.")

    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(rep))
    print("\n".join(rep).encode("ascii", "replace").decode("ascii"))


if __name__ == "__main__":
    main()
