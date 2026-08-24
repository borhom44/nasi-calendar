"""Run the Nasi' system backwards to find when intercalation stopped.

The key constraint is not a rate but an INTEGER. Both calendars ride the same
lunations from the same epoch; the only difference is that ours inserts extra
months. So for any given day:

    K = 12*(official_year - nasi_year) + official_month_idx - nasi_month_idx

is the exact whole number of lunations that this calendar has inserted and the
official one has not. K is a count, with no rounding error in it at all.

If the two calendars were identical until abolition in year A, and ours has
inserted at rate r ever since, then K = r * (Y - A), so:

    A = Y - K/r

The uncertainty therefore lives entirely in r, and is honest and quantifiable
-- unlike the previous rate-only extrapolation, the K term contributes none.
"""
import json
import math

DAYS = r"C:\Dev\nasi-calendar\data\nasi_days.json"
MONTHS = r"C:\Dev\nasi-calendar\data\nasi_months.json"
OUT = r"C:\Dev\nasi-calendar\data\abolition_report.txt"

ISLAMIC_EPOCH_JD = 1948439.5

CYCLE = ["صفر الأول", "صفر الثاني", "ربيع الأول", "ربيع الثاني", "جمادى الأولى",
         "جمادى الثانية", "رجب", "شعبان", "رمضان", "شوال", "ذو القعدة", "ذو الحجة"]


def greg_to_jd(y, m, d):
    if m <= 2:
        y, m = y - 1, m + 12
    a = y // 100
    b = 2 - a + a // 4
    return math.floor(365.25 * (y + 4716)) + math.floor(30.6001 * (m + 1)) + d + b - 1524.5


def jd_to_greg(jd):
    z = math.floor(jd + 0.5)
    f = (jd + 0.5) - z
    alpha = math.floor((z - 1867216.25) / 36524.25)
    a = z if z < 2299161 else z + 1 + alpha - math.floor(alpha / 4)
    b = a + 1524
    c = math.floor((b - 122.1) / 365.25)
    d_ = math.floor(365.25 * c)
    e = math.floor((b - d_) / 30.6001)
    day = b - d_ - math.floor(30.6001 * e) + f
    mo = e - 1 if e < 14 else e - 13
    yr = c - 4716 if mo > 2 else c - 4715
    return int(yr), int(mo), int(day)


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
    months = json.load(open(MONTHS, encoding="utf-8"))
    rep = []

    # lunation index of every month within its own Nasi' year (1-based)
    idx_in_year, seen = {}, {}
    for m in months:
        seen[m["ny"]] = seen.get(m["ny"], 0) + 1
        idx_in_year[m["start"]] = seen[m["ny"]]

    # Establish the intercalation rate empirically rather than assuming it.
    # Every rolling 19-year window in the table holds exactly 7 insertions, so
    # the rule is Metonic and r is the exact rational 7/19 -- not a ratio like
    # 37/100 that merely rounds to it. This matters enormously: A is so
    # sensitive to r that using 37/100 instead shifts the answer by 6 years.
    yrs = sorted({m["ny"] for m in months})
    nasi_years = [m["ny"] for m in months
                  if m["nm"] == "نسيء" and yrs[1] <= m["ny"] <= yrs[-2]]
    windows = [sum(1 for y in nasi_years if s <= y < s + 19)
               for s in range(yrs[1], yrs[-2] - 18)]
    rep.append(f"INTERCALATION RULE: {len(windows)} rolling 19-year windows, "
               f"insertions per window min={min(windows)} max={max(windows)}")
    assert min(windows) == max(windows) == 7, "table is not strictly Metonic"
    rep.append("   -> strictly Metonic; r = 7/19 exactly")
    rep.append("")
    r_measured = 7 / 19

    rep.append("INSERTED-LUNATION COUNT K, measured on many independent dates")
    rep.append("  (K must come out the same shifted story from every sample; A must be constant)")
    rep.append("")
    rep.append("   nasi-date            official Hijri      K     implied A")

    results = []
    for m in months:
        if idx_in_year[m["start"]] != 1 or m["ny"] % 12 != 0:
            continue
        gy, gm, gd = (int(m["start"][:4]), int(m["start"][5:7]), int(m["start"][8:10]))
        oy, om, od = jd_to_islamic(greg_to_jd(gy, gm, gd))
        K = 12 * (oy - m["ny"]) + om - idx_in_year[m["start"]]
        A = m["ny"] - K / r_measured
        results.append((m["start"], m["ny"], oy, om, K, A))

    for row in results[:4] + results[-4:]:
        rep.append(f"   {row[0]}  y{row[1]}   {row[3]:2d}/{row[2]}      {row[4]:4d}   {row[5]:7.1f}")

    As = [r[5] for r in results]
    mean_A = sum(As) / len(As)
    rep.append("")
    rep.append(f"   samples: {len(As)}   A range: {min(As):.1f} .. {max(As):.1f}   "
               f"spread {max(As)-min(As):.1f} yr   mean {mean_A:.1f}")
    rep.append("   The residual spread is the Metonic sawtooth: within a 19-year cycle the")
    rep.append("   running insertion count leads or lags the smooth rate by up to half an")
    rep.append("   insertion, and one insertion is worth 1/r = 2.7 years of A.")

    rep.append("")
    rep.append("ABOLITION YEAR")
    jd = islamic_to_jd(int(round(mean_A)), 1, 1)
    gy, gm, gd = jd_to_greg(jd)
    rep.append(f"   best estimate: Nasi' year {mean_A:.1f} AH  "
               f"(1 Muharram {int(round(mean_A))} AH = approx {gy}-{gm:02d}-{gd:02d} CE)")
    lo, hi = int(math.floor(min(As))), int(math.ceil(max(As)))
    jlo, jhi = islamic_to_jd(lo, 1, 1), islamic_to_jd(hi, 1, 1)
    rep.append(f"   range across samples: {lo}-{hi} AH "
               f"(~{jd_to_greg(jlo)[0]}-{jd_to_greg(jhi)[0]} CE)")
    rep.append("")
    rep.append("   For reference, using 37/100 instead of the true 7/19 -- a 0.4% rate")
    rep.append(f"   error -- would have given {results[-1][1] - results[-1][4]/0.37:.1f} AH. "
               f"That is how sharp the leverage is.")

    rep.append("")
    K0 = results[-1][4]
    rep.append("SENSITIVITY")
    rep.append(f"   dA/dr = K/r^2 = {K0/r_measured**2:.0f} years per unit rate")
    rep.append(f"   -> a 1% error in the intercalation rate moves A by "
               f"{K0/r_measured**2*0.01*r_measured:.1f} years")
    rep.append(f"   an epoch misalignment of +-1 lunation moves A by "
               f"{1/r_measured:.1f} years")

    rep.append("")
    rep.append("ASSUMPTIONS (both load-bearing)")
    rep.append("   1. Year 1 of this calendar and year 1 AH are the same lunation.")
    rep.append("   2. The intercalation rate has been constant since abolition.")
    rep.append("   Neither is verifiable from the 2000-2100 table. The book's own")
    rep.append("   513-2100 charts would test both directly; they are in neither PDF here.")

    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(rep))
    print("\n".join(rep).encode("ascii", "replace").decode("ascii"))


if __name__ == "__main__":
    main()
