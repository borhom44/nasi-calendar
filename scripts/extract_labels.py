"""Extract the Hijri month-name labels from the source calendar PDF, at
character resolution.

Why this exists separately from extract_spans.py
------------------------------------------------
Every one of the 12 months (plus Nasi') is labelled in the source chart, in
the orange band at the right edge of the Gregorian month block in which that
Hijri month begins. Six of them render as standalone text spans:

    رجب  شعبان  رمضان  شوال  ذق  ذح

The other six render as short tokens -- صفر1 صفر2 ر1 ر2 ج1 ج2 -- and PyMuPDF
very often merges SEVERAL of them, from different month blocks 60+pt apart,
into a single text span whose `.text` is the concatenation:

    'صفر1صفر2ر1ر2ج1ج2'

A span-level `text in VOCAB` test therefore drops all of them silently. That
is exactly the bug that let build_calendar.py run for 101 years on a guessed
cycle anchor with nothing able to contradict it.

The fix: read `rawdict` (per-character bboxes), then split each span back
into labels *spatially* rather than by string surgery -- characters of one
label sit within ~2pt of each other, while separate labels are a whole month
column apart. Cluster on the x-gap and each cluster is one label, with a
trustworthy x0 of its own.
"""
import json
import sys

import fitz

SRC = r"C:\Users\Owner\OneDrive\Desktop\calendar 2000-2100-010 2021.pdf"
OUT = r"C:\Dev\nasi-calendar\data\label_tokens.json"

# Gap (pt) between consecutive characters that means "different label".
# Intra-label character gaps are ~0-2pt; adjacent month columns are ~61.5pt.
CLUSTER_GAP = 6.0

# The chart's own key, book p.14. Note رحب: the PDF's glyph for رجب extracts
# as ر-ح-ب, so both spellings are accepted.
VOCAB = {
    "صفر1": 0, "صفر2": 1,
    "ر1": 2, "ر2": 3,
    "ج1": 4, "ج2": 5,
    "رجب": 6, "رحب": 6,
    "شعبان": 7, "رمضان": 8, "شوال": 9,
    "ذق": 10, "ذح": 11,
}
NASI = "نسيء"


def cluster_chars(chars):
    """chars: [{'c': str, 'x0': float, 'x1': float}] in original span order.

    Group into spatially-contiguous runs. Order within a cluster is kept as
    the PDF emitted it (which already matches the vocabulary spellings), so
    no bidi/shaping reordering is attempted here.
    """
    if not chars:
        return []
    order = sorted(range(len(chars)), key=lambda i: chars[i]["x0"])
    groups, cur = [], [order[0]]
    for prev, idx in zip(order, order[1:]):
        if chars[idx]["x0"] - chars[prev]["x1"] > CLUSTER_GAP:
            groups.append(cur)
            cur = [idx]
        else:
            cur.append(idx)
    groups.append(cur)

    out = []
    for g in groups:
        g_sorted = sorted(g)  # back to original emission order
        text = "".join(chars[i]["c"] for i in g_sorted)
        out.append({
            "t": text,
            "x0": round(min(chars[i]["x0"] for i in g), 2),
            "x1": round(max(chars[i]["x1"] for i in g), 2),
        })
    return out


def main():
    doc = fitz.open(SRC)
    pages_out = []
    kept = dropped = 0
    unknown = {}
    for pno in range(doc.page_count):
        d = doc[pno].get_text("rawdict")
        labels = []
        for block in d["blocks"]:
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    chars = [{"c": c["c"], "x0": c["bbox"][0], "x1": c["bbox"][2]}
                             for c in span.get("chars", []) if c["c"].strip()]
                    if not chars:
                        continue
                    for tok in cluster_chars(chars):
                        t = tok["t"]
                        if t in VOCAB or t == NASI:
                            labels.append({
                                "t": t,
                                "idx": VOCAB.get(t, -1),   # -1 == Nasi'
                                "x0": tok["x0"],
                                "x1": tok["x1"],
                                "top": round(span["bbox"][1], 2),
                                "c": span["color"],
                            })
                            kept += 1
                        else:
                            dropped += 1
                            if not t.isdigit():
                                unknown[t] = unknown.get(t, 0) + 1
        pages_out.append(labels)
        print(f"page {pno}: {len(labels)} labels", file=sys.stderr)

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(pages_out, f, ensure_ascii=False)
    print(f"wrote {OUT}: {kept} labels kept, {dropped} non-label clusters skipped")

    # Anything month-name-shaped that failed to match is a silent-drop risk --
    # the whole point of this module -- so surface the top offenders.
    interesting = {k: v for k, v in unknown.items()
                   if any("\u0600" <= ch <= "\u06ff" for ch in k) and len(k) > 1}
    for t, n in sorted(interesting.items(), key=lambda kv: -kv[1])[:15]:
        print(f"  unmatched arabic cluster {t!r} x{n}", file=sys.stderr)


if __name__ == "__main__":
    main()
