"""Build every published .ics feed, one per city per language.

    python scripts/build_feeds.py            # write them
    python scripts/build_feeds.py --check    # report drift, write nothing

WHICH FEEDS EXIST. Only cities with feed:true in data/cities.json, times every
language. The subscribe picker in the app reads the same flag, so it can never
offer a link that 404s.

    nasi-{city}-full-5y.ics        Arabic   <- the existing, already-subscribed URL
    nasi-{city}-full-5y-en.ics     English

THE ARABIC NAMES ARE FROZEN. Those two URLs are in people's calendars and an
.ics URL can never be redirected or recalled -- a subscriber cannot be found,
warned, or migrated. English gets a suffix precisely so the unsuffixed name
keeps meaning what it has always meant.

WHY ONLY TWO CITIES. All 33 are in the registry and drive the app immediately,
but 33 cities x 2 languages is ~150 MB of pre-baked text that has to be
regenerated and committed on every wording change. That work disappears the
moment feeds are generated per request on the VPS (Phase 5), so baking it now
would be building something to throw away. Flip feed:true when hosting moves.

WHY 5 YEARS AND NOTHING ELSE. The 1-year and 100-year spans were retired: at
four sun events a day the 100-year feed is ~55 MB re-fetched daily by every
subscriber, and importing rather than subscribing is unusable at any span.
"""
import argparse
import io
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cities import FEED_CITIES, REPO  # noqa: E402
from strings import LANGS  # noqa: E402
import generate_ics_full as gen  # noqa: E402

OUT_DIR = REPO / "docs" / "data"
SPAN_YEARS = 5


def feed_name(city_key, lang):
    """Arabic keeps the historic name; other languages take a suffix."""
    base = f"nasi-{city_key}-full-{SPAN_YEARS}y"
    return f"{base}.ics" if lang == "ar" else f"{base}-{lang}.ics"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true",
                    help="report what would change and write nothing")
    ap.add_argument("--start", help="ISO date; defaults to 1 January of this year")
    args = ap.parse_args()

    start = args.start or f"{date.today().year}-01-01"
    end = f"{int(start[:4]) + SPAN_YEARS - 1}-12-31"

    import json
    days = json.load(io.open(gen.DAYS_JSON, encoding="utf-8"))
    moon = json.load(io.open(gen.MOON_JSON, encoding="utf-8"))
    eclipses = json.load(io.open(gen.ECLIPSE_JSON, encoding="utf-8"))

    total_bytes = 0
    changed = []
    for city_key in sorted(FEED_CITIES):
        for lang in LANGS:
            path = OUT_DIR / feed_name(city_key, lang)
            ics, n_day, n_moon, n_ecl, n_sun = gen.build(
                days, moon, eclipses, city_key, start, end, lang=lang)
            total_bytes += len(ics.encode("utf-8"))

            current = io.open(path, encoding="utf-8", newline="").read() if path.exists() else None
            # DTSTAMP carries today's date, so a byte comparison always differs.
            # Compare with those lines stripped to see real change.
            strip = lambda s: "\n".join(
                l for l in s.splitlines() if not l.startswith("DTSTAMP"))
            if current is not None and strip(current) == strip(ics):
                print(f"  {path.name:<34} unchanged  ({n_day + n_moon + n_ecl + n_sun} events)")
                continue

            changed.append(path.name)
            if args.check:
                print(f"  {path.name:<34} WOULD CHANGE")
                continue

            # RFC 5545 requires CRLF and generate_ics_full already emits it;
            # newline="" keeps it byte-for-byte. .gitattributes has *.ics -text
            # so git does not normalise it away on commit. Never remove either.
            io.open(path, "w", encoding="utf-8", newline="").write(ics)
            print(f"  {path.name:<34} written    "
                  f"({n_day + n_moon + n_ecl + n_sun} events, "
                  f"{len(ics.encode('utf-8')) / 1048576:.2f} MB)")

    print(f"{len(FEED_CITIES)} cities x {len(LANGS)} languages, "
          f"{start} .. {end}, {total_bytes / 1048576:.1f} MB total")
    if args.check and changed:
        print(f"stale: {', '.join(changed)}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
