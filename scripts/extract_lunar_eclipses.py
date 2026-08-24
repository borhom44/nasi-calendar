"""Extract 2000-2100 lunar eclipses from NASA's 5-millennium catalog into a
compact web-ready dataset. Same file, same parsing as verify_astronomy.py's
test 4 -- pulled out here because the app needs it as data, not as a report.

Fields kept: exact UTC instant of greatest eclipse, and type (N=penumbral,
P=partial, U=total/umbral -- "T" in the catalog's own QSE column covers both
total-umbral and total-penumbral prefixes, collapsed here to whether the
umbral phase reached totality: 'T' vs 'P' vs 'N').
"""
import json

CAT = r"C:\Dev\nasi-calendar\data\nasa_5MKLE_catalog.txt"
OUT_JSON = r"C:\Dev\nasi-calendar\data\lunar_eclipses.json"
OUT_JS = r"C:\Dev\nasi-calendar\docs\eclipses-data.js"

MON = {m: i + 1 for i, m in enumerate(
    ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"])}


def main():
    events = []
    with open(CAT, encoding="utf-8", errors="replace") as f:
        for line in f:
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
            # catalogue time is Dynamical Time; convert to UTC via its own DT column
            from datetime import datetime, timedelta
            td_instant = datetime(y, MON[p[2]], dd, hh, mm, ss)
            utc_instant = td_instant - timedelta(seconds=dt_s)
            kind = "T" if etype.startswith("T") else ("P" if etype.startswith("P") else "N")
            events.append({"t": utc_instant.strftime("%Y-%m-%dT%H:%M:%SZ"), "k": kind})

    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(events, f, separators=(",", ":"))
    with open(OUT_JS, "w", encoding="utf-8") as f:
        f.write("const LUNAR_ECLIPSES = " + json.dumps(events, separators=(",", ":")) + ";\n")
    kinds = {}
    for e in events:
        kinds[e["k"]] = kinds.get(e["k"], 0) + 1
    print(f"wrote {len(events)} lunar eclipses (2000-2100) -> {OUT_JSON}")
    print(f"  by type: {kinds}  (N=penumbral, P=partial, T=total)")
    print(f"  first: {events[0]}   last: {events[-1]}")


if __name__ == "__main__":
    main()
