"""Reconstruct the Nasi' calendar day-by-day from the source PDF.

Layout facts (reverse-engineered from the source PDF):
  - Each page holds 6 Gregorian years, stacked vertically.
  - Each year-block's header row carries: the 4-digit Gregorian year at
    x0~24.7, the Hijri year that BEGINS during it at x0~84.7, and 12
    day-count numbers (28-31) whose x0 mark the 12 Gregorian month columns
    (Jan..Dec, left to right).
  - Below that: a weekday-letter header row, then repeating pairs of rows -- a
    BLACK row of Gregorian day-of-month numbers, and immediately below it a
    row of RED Hijri day-of-month numbers.
  - Where a Hijri month begins, an orange band carries that month's label at
    the right edge of the Gregorian month block, on the same row as its day 1.

Correctness model
-----------------
Month *boundaries* come from the red digit resets (the day count jumping back
to 1). Month *names* come from the chart's own printed label for that run --
all 12 of them, not a walk seeded on a guess.

This matters: a previous version of this script could only see 6 of the 12
labels (see extract_labels.py for why), so it named months by walking a cycle
from a hand-picked anchor constant. The anchor was off by one, every month
name in all 101 years was shifted a position, and nothing in the pipeline
could contradict it -- Ramadan 1409 came out as 29 Aug 2030 where the chart
plainly reads 27 Sep 2030.

So every labelled run is now asserted against the walk rather than merely
"informational", and the run of unlabelled runs is bounded and reported.
"""
import json
import re
import sys
from datetime import date

RAW = r"C:\Dev\nasi-calendar\data\raw_spans.json"
LABELS = r"C:\Dev\nasi-calendar\data\label_tokens.json"
OUT_DAYS = r"C:\Dev\nasi-calendar\data\nasi_days.json"
REPORT = r"C:\Dev\nasi-calendar\data\validation_report.txt"

BLACK = 0x000000
RED = 0xFF0000

# The chart's own key (book p.14). "al-Muharram" is deliberately absent: in
# this convention it is a name the Nasi' month takes at position 13, not a
# fixed slot, and the year opens at Safar al-Awwal so it starts right after
# the Hajj rite. See README "Month names".
HIJRI_CYCLE = [
    "صفر الأول", "صفر الثاني", "ربيع الأول", "ربيع الثاني", "جمادى الأولى", "جمادى الثانية",
    "رجب", "شعبان", "رمضان", "شوال", "ذو القعدة", "ذو الحجة",
]
NASI_LABEL = "نسيء"
NASI_IDX = -1

# Nasi' may only be inserted after these cycle positions (the book's "13-9-5"
# scheme): after Dhul-Hijjah, after Sha'ban, or after Rabi' al-Thani.
LEGAL_NASI_PREDECESSORS = {11, 7, 3}


def greg_days_in_month(y, m):
    if m in (1, 3, 5, 7, 8, 10, 12):
        return 31
    if m == 2:
        return 29 if (y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)) else 28
    return 30


def cluster_rows(tops, gap=1.5):
    tops = sorted(tops)
    clusters = [[tops[0]]]
    for t in tops[1:]:
        if t - clusters[-1][-1] <= gap:
            clusters[-1].append(t)
        else:
            clusters.append([t])
    return [sum(c) / len(c) for c in clusters]


def fill_column_gaps(cells, value_fn):
    """Interpolate a cell missing outright from the source PDF.

    Day numbers step by exactly +-1 per ~7pt column within a week-row. A cell
    can be absent from the PDF (observed once, in the 2012-11 grid); the
    neighbours determine both its value and its x0, which keeps the row's cell
    count aligned for the positional pairing below.
    """
    if len(cells) < 2:
        return cells
    xs = [s["x0"] for s in cells]
    vals = [value_fn(s) for s in cells]
    step = min(b - a for a, b in zip(xs, xs[1:]) if b > a)
    if step <= 0:
        return cells
    filled = [cells[0]]
    for i in range(1, len(cells)):
        gap_cols = round((xs[i] - xs[i - 1]) / step) - 1
        if 0 < gap_cols <= 3:
            val_step = (vals[i] - vals[i - 1]) / (gap_cols + 1)
            if val_step == int(val_step):
                for g in range(1, gap_cols + 1):
                    synth_x0 = xs[i - 1] + step * g
                    synth_val = vals[i - 1] + int(val_step) * g
                    filled.append({"t": str(synth_val), "c": cells[0]["c"],
                                   "x0": synth_x0, "x1": synth_x0 + 2})
        filled.append(cells[i])
    return filled


def month_block_index(x0, header_x0):
    for i in range(len(header_x0) - 1):
        if x0 < header_x0[i] + 15.0:
            return i
    return len(header_x0) - 1


def parse_year_block(spans, page_labels, year_top, year_bottom):
    header_row1 = [s for s in spans if abs(s["top"] - year_top) < 0.6]
    greg_year = int(next(s for s in header_row1
                         if re.fullmatch(r"(19|20|21)\d{2}", s["t"]) and s["x0"] < 40)["t"])
    hijri_year = int(next(s for s in header_row1
                          if re.fullmatch(r"1[34]\d{2}", s["t"]))["t"])

    count_spans = sorted(
        (s for s in header_row1
         if s["c"] == BLACK and re.fullmatch(r"\d{2}", s["t"]) and 28 <= int(s["t"]) <= 31),
        key=lambda s: s["x0"])
    if len(count_spans) != 12:
        raise ValueError(f"year {greg_year}: expected 12 month headers, got {len(count_spans)}")
    month_x0 = [s["x0"] for s in count_spans]

    # A few Hijri digits are highlighted in another colour (blue/teal for the
    # book's eclipse-verified dates), so "not black" is the real test, not
    # "is red".
    header2_top = year_top + 4.6
    digit_spans = [s for s in spans
                   if header2_top + 2.0 < s["top"] < year_bottom and re.fullmatch(r"\d{1,2}", s["t"])]
    for s in digit_spans:
        if s["c"] != BLACK:
            s["c"] = RED

    row_tops = cluster_rows([s["top"] for s in digit_spans])

    digits_by_month = {m: [] for m in range(1, 13)}
    for ri in range(0, len(row_tops) - 1, 2):
        greg_top, hijri_top = row_tops[ri], row_tops[ri + 1]
        greg_cells = [s for s in digit_spans if abs(s["top"] - greg_top) < 1.5 and s["c"] == BLACK]
        hijri_cells = [s for s in digit_spans if abs(s["top"] - hijri_top) < 1.5 and s["c"] == RED]

        gm, hm = {}, {}
        for s in greg_cells:
            gm.setdefault(month_block_index(s["x0"], month_x0) + 1, []).append(s)
        for s in hijri_cells:
            hm.setdefault(month_block_index(s["x0"], month_x0) + 1, []).append(s)

        for mi, gcells in gm.items():
            hcells = hm.get(mi, [])
            if not hcells:
                continue
            gcells = fill_column_gaps(sorted(gcells, key=lambda s: s["x0"]), lambda s: int(s["t"]))
            hcells = fill_column_gaps(sorted(hcells, key=lambda s: s["x0"]), lambda s: int(s["t"]))
            if len(gcells) == len(hcells):
                # equal counts -> pair strictly by left-to-right position. Never
                # by nearest-x0: one genuinely missing cell would make a wrong
                # neighbour "nearest" and two days would claim the same digit.
                pairs = list(zip(gcells, hcells))
            else:
                pool = list(hcells)
                pairs = []
                for gc in gcells:
                    if not pool:
                        break
                    hc = min(pool, key=lambda s: abs(s["x0"] - gc["x0"]))
                    pool.remove(hc)
                    pairs.append((gc, hc))
            for gc, hc in pairs:
                day = int(gc["t"])
                if 1 <= day <= greg_days_in_month(greg_year, mi):
                    digits_by_month[mi].append((day, int(hc["t"]), hijri_top))

    labels = []
    for lb in page_labels:
        if header2_top + 2.0 < lb["top"] < year_bottom:
            labels.append({
                "gm": month_block_index(lb["x0"], month_x0) + 1,
                "top": lb["top"],
                "idx": lb["idx"],
                "t": lb["t"],
            })
    return greg_year, hijri_year, digits_by_month, labels


def main():
    with open(RAW, encoding="utf-8") as f:
        pages = json.load(f)
    with open(LABELS, encoding="utf-8") as f:
        label_pages = json.load(f)

    year_headers = []
    for pno, spans in enumerate(pages):
        ys = sorted({s["top"] for s in spans
                     if s["c"] == BLACK and re.fullmatch(r"(19|20|21)\d{2}", s["t"]) and s["x0"] < 40})
        year_headers += [(pno, yt) for yt in ys]

    digit_map = {}                 # (gy, gm, gd) -> (hijri_digit, row_top)
    hijri_year_of_row = {}         # gy -> Hijri year beginning in that row
    label_sightings = []           # (gy, gm, top, idx, text)

    for i, (pno, ytop) in enumerate(year_headers):
        nxt = year_headers[i + 1] if i + 1 < len(year_headers) else None
        ybottom = nxt[1] if nxt and nxt[0] == pno else 612.0
        gy, hy, digits_by_month, labels = parse_year_block(
            pages[pno], label_pages[pno], ytop, ybottom)
        hijri_year_of_row[gy] = hy
        for m in range(1, 13):
            for day, hdig, row_top in digits_by_month[m]:
                digit_map[(gy, m, day)] = (hdig, row_top)
        for lb in labels:
            label_sightings.append((gy, lb["gm"], lb["top"], lb["idx"], lb["t"]))

    all_dates = sorted(digit_map)
    print(f"days: {len(all_dates)}, labels: {len(label_sightings)}", file=sys.stderr)

    # --- month runs, purely from digit resets -------------------------------
    runs = []  # {start_i, end_i, gy, gm, gd, row_top}
    prev_val = None
    for i, key in enumerate(all_dates):
        hdig, row_top = digit_map[key]
        if prev_val is None or hdig != prev_val + 1:
            runs.append({"start_i": i, "gy": key[0], "gm": key[1], "gd": key[2],
                         "row_top": row_top, "hd0": hdig, "idx": None, "label": None})
        prev_val = hdig
    for r, nxt in zip(runs, runs[1:]):
        r["end_i"] = nxt["start_i"] - 1
    runs[-1]["end_i"] = len(all_dates) - 1

    # --- attach each printed label to the run it names -----------------------
    # Only a genuine month start can carry a label. The table opens part-way
    # through Dhul-Qi'dah, so runs[0] begins on a mid-month digit -- and it
    # shares a week-row with the real month start six days later, so without
    # this guard it steals that row's label and shifts the whole cycle.
    by_start = {}
    for ri, r in enumerate(runs):
        if r["hd0"] == 1:
            by_start.setdefault((r["gy"], r["gm"]), []).append(ri)

    # The label's baseline lands on its month's own red row, or one row above
    # or below it (~5pt either way) -- the placement is not consistent between
    # years. Accept +-7pt, which spans that jitter. Two month starts inside one
    # Gregorian block are always >=29 days apart -- three row-pairs, ~30pt -- so
    # this window can never capture two runs.
    TOP_LO, TOP_HI = -7.0, 7.0

    unmatched_labels = []
    for (gy, gm, top, idx, text) in label_sightings:
        cands = [ri for ri in by_start.get((gy, gm), [])
                 if TOP_LO <= runs[ri]["row_top"] - top <= TOP_HI]
        if not cands:
            unmatched_labels.append((gy, gm, top, text))
            continue
        best = min(cands, key=lambda ri: abs(runs[ri]["row_top"] - top))
        if runs[best]["idx"] is not None and runs[best]["idx"] != idx:
            unmatched_labels.append((gy, gm, top, f"{text} CONFLICTS with {runs[best]['label']}"))
            continue
        runs[best]["idx"] = idx
        runs[best]["label"] = text

    labelled = sum(1 for r in runs if r["idx"] is not None)

    # --- fill unlabelled runs, and assert every labelled one ----------------
    conflicts = []
    for i, r in enumerate(runs):
        if r["idx"] is not None:
            continue
        prev = runs[i - 1] if i else None
        if prev and prev["idx"] is not None and prev["idx"] != NASI_IDX:
            r["idx"] = (prev["idx"] + 1) % 12
        elif i + 1 < len(runs) and runs[i + 1]["idx"] not in (None, NASI_IDX):
            r["idx"] = (runs[i + 1]["idx"] - 1) % 12
        else:
            conflicts.append(f"run {i} @ {r['gy']}-{r['gm']:02d}: cannot infer month")

    for i, (a, b) in enumerate(zip(runs, runs[1:])):
        if b["idx"] == NASI_IDX:
            if a["idx"] not in LEGAL_NASI_PREDECESSORS:
                conflicts.append(f"Nasi' at run {i+1} ({b['gy']}-{b['gm']:02d}) follows "
                                 f"cycle idx {a['idx']}, not one of {sorted(LEGAL_NASI_PREDECESSORS)}")
            continue
        prev_idx = a["idx"] if a["idx"] != NASI_IDX else (runs[i - 1]["idx"] if i else None)
        if prev_idx is not None and b["idx"] != (prev_idx + 1) % 12:
            conflicts.append(f"run {i+1} ({b['gy']}-{b['gm']:02d}) is idx {b['idx']}, "
                             f"expected {(prev_idx + 1) % 12}")

    # --- Hijri years, anchored on the chart's own per-row year label ---------
    year_conflicts = []
    cur_year = None
    for r in runs:
        if r["idx"] == 0:
            stated = hijri_year_of_row.get(r["gy"])
            if stated is None:
                year_conflicts.append(f"no Hijri year label for Gregorian {r['gy']}")
            elif cur_year is not None and stated != cur_year + 1:
                year_conflicts.append(
                    f"year label jumps {cur_year} -> {stated} at {r['gy']}-{r['gm']:02d}")
            cur_year = stated if stated is not None else (cur_year + 1)
        r["ny"] = cur_year
    # runs before the first Safar al-Awwal belong to the preceding year
    first_named = next(r["ny"] for r in runs if r["ny"] is not None)
    for r in runs:
        if r["ny"] is None:
            r["ny"] = first_named - 1

    # --- emit ---------------------------------------------------------------
    results = []
    for r in runs:
        name = NASI_LABEL if r["idx"] == NASI_IDX else HIJRI_CYCLE[r["idx"]]
        for n, i in enumerate(range(r["start_i"], r["end_i"] + 1), start=1):
            gy, gm, gd = all_dates[i]
            results.append({"g": f"{gy:04d}-{gm:02d}-{gd:02d}", "ny": r["ny"], "nm": name, "nd": n})

    # the table opens part-way through a month, so its first run's day numbers
    # must keep the source's printed values rather than restarting at 1
    first_run_len = runs[0]["end_i"] - runs[0]["start_i"] + 1
    for n, i in enumerate(range(runs[0]["start_i"], runs[0]["end_i"] + 1)):
        results[i]["nd"] = digit_map[all_dates[i]][0]

    with open(OUT_DAYS, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False)
    print(f"wrote {len(results)} days to {OUT_DAYS}")

    # --- validation ---------------------------------------------------------
    rep = []
    first, last = date.fromisoformat(results[0]["g"]), date.fromisoformat(results[-1]["g"])
    rep.append(f"range: {results[0]['g']} .. {results[-1]['g']}")
    rep.append(f"records: {len(results)}  expected (no gaps): {(last - first).days + 1}")

    by_date = {r["g"]: r for r in results}
    missing, d = [], first
    while d <= last:
        if d.isoformat() not in by_date:
            missing.append(d.isoformat())
        d = date.fromordinal(d.toordinal() + 1)
    rep.append(f"missing gregorian dates: {len(missing)} {missing[:10]}")

    rep.append("")
    rep.append(f"month runs: {len(runs)}")
    rep.append(f"  named directly by the chart's own label: {labelled}")
    rep.append(f"  inferred from neighbours: {len(runs) - labelled} "
               f"{[f'{r['gy']}-{r['gm']:02d}' for r in runs if r['label'] is None][:10]}")
    rep.append(f"  labels that matched no run: {len(unmatched_labels)} {unmatched_labels[:5]}")
    rep.append(f"CYCLE CONFLICTS: {len(conflicts)}")
    for c in conflicts[:20]:
        rep.append(f"    {c}")
    rep.append(f"YEAR-LABEL CONFLICTS: {len(year_conflicts)}")
    for c in year_conflicts[:20]:
        rep.append(f"    {c}")

    bad = []
    cur_key, cur_len = None, 0
    for r in results:
        k = (r["ny"], r["nm"])
        if k != cur_key:
            if cur_key is not None and cur_len not in (29, 30):
                bad.append((cur_key, cur_len))
            cur_key, cur_len = k, 1
        else:
            cur_len += 1
    if cur_key is not None and cur_len not in (29, 30):
        bad.append((cur_key, cur_len))
    rep.append("")
    rep.append(f"month runs with length not in {{29,30}}: {len(bad)} {bad[:10]}")
    rep.append(f"Nasi' insertions: {sum(1 for r in runs if r['idx'] == NASI_IDX)}")

    rep.append("")
    rep.append("spot-checks read off the source chart by hand:")
    for g, want in [("2025-09-23", "رمضان 1"), ("2026-10-12", "رمضان 1"), ("2026-09-13", "نسيء 1"),
                    ("2030-09-27", "رمضان 1"), ("2030-01-05", "ذو الحجة 1"), ("2030-02-03", "صفر الأول 1")]:
        got = by_date.get(g)
        ok = got and f"{got['nm']} {got['nd']}" == want
        rep.append(f"  {g}  want {want:<14} got {got['nm']} {got['nd']} (ny={got['ny']})  {'OK' if ok else 'MISMATCH'}")

    with open(REPORT, "w", encoding="utf-8") as f:
        f.write("\n".join(rep))
    print("\n".join(rep[:6]))


if __name__ == "__main__":
    main()
