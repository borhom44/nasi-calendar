"""Regenerate everything under docs/ that is derived from data/, then re-stamp.

Run this before committing any change to data/ or docs/:

    python scripts/build_web.py

Three steps, in this order, because the last depends on the first two:

  1. emits docs/cities-data.js  from data/cities.json   (validated by cities.py)
  2. emits docs/strings-data.js from data/strings.json  (validated by strings.py)
  3. runs scripts/stamp_assets.py so index.html's ?v= hashes match the bytes

All three exist because of one failure mode: something derived from a source
file going stale without saying so. A hand-copied city list drifts from the
registry; an untranslated key ships as a blank label; a stale ?v= hash serves
old code to returning visitors with no error anywhere. None of them announce
themselves.

    --check   report drift and exit 1 without writing anything
"""
import argparse
import io
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cities import REGIONS, CITIES, DOCS  # noqa: E402
from strings import STRINGS, SUN_EVENT_KEYS  # noqa: E402


def _js(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(", ", ": "))


def _banner(source, note):
    return (f"/* GENERATED FILE -- do not edit.\n"
            f" *\n"
            f" * Emitted from {source} by scripts/build_web.py. Edit that file and\n"
            f" * re-run the script; anything typed here is overwritten without warning.\n"
            f" *\n"
            f" * {note}\n"
            f" */\n")


def render_cities():
    lines = [_banner("data/cities.json",
                     "`CITIES` is the same global the app has always used, so solar.js\n"
                     " * and moon-events.js keep working unchanged -- it is simply no longer\n"
                     " * hand-written in two places that could disagree about a coordinate."),
             f"const NASI_REGIONS = {_js(REGIONS)};", "", "const CITIES = {"]
    for key, c in CITIES.items():
        entry = {k: c[k] for k in ("region", "ar", "en", "lat", "lon", "tz", "feed")}
        lines.append(f"  {json.dumps(key)}: {_js(entry)},")
    lines += ["};", ""]
    lines += [
        "/* Display name in the active language. Everything user-facing goes",
        " * through this rather than reading .ar or .en directly, so adding a",
        " * third language later is a data change and not a code change. */",
        "function cityLabel(key, lang) {",
        "  const c = CITIES[key];",
        "  return c ? (c[lang] || c.ar) : key;",
        "}",
        "",
        "/* [{region, cities:[key,...]}, ...] -- only cities with a generated feed",
        " * when feedOnly is true, so the subscribe picker never offers a dead link. */",
        "function citiesByRegion(feedOnly) {",
        "  return NASI_REGIONS.map((r) => ({",
        "    region: r,",
        "    cities: Object.keys(CITIES).filter(",
        "      (k) => CITIES[k].region === r.key && (!feedOnly || CITIES[k].feed)",
        "    ),",
        "  })).filter((g) => g.cities.length);",
        "}",
        "",
    ]
    return "\n".join(lines)


def _camel(snake):
    head, *rest = snake.split("_")
    return head + "".join(p.title() for p in rest)


def render_strings():
    lines = [_banner("data/strings.json",
                     "Both languages ship in every build. The table is small enough that\n"
                     " * splitting it per language would cost a request to save a few KB."),
             "const STRINGS = {"]
    for key in STRINGS:
        lines.append(f"  {json.dumps(key)}: {_js(STRINGS[key])},")
    lines += ["};", ""]
    pairs = [[_camel(k), s] for k, s in SUN_EVENT_KEYS]
    lines += [
        "/* Translate. Returns the key itself on a miss and warns rather than",
        " * throwing: a missing string should degrade one label, not blank the page",
        " * mid-render. The Python side raises instead, so the build catches it",
        " * first and this path should not be reachable in a shipped build. */",
        "function t(key, lang) {",
        "  const row = STRINGS[key];",
        "  if (!row) { console.warn('missing string: ' + key); return key; }",
        "  return row[lang] || row.ar;",
        "}",
        "",
        "/* The four sun events in display order, as [sunTimes key, string key].",
        " * Order and wording are decided in data/strings.json alone -- the same",
        " * tuple list the Python generator iterates. */",
        f"const SUN_EVENT_KEYS = {_js(pairs)};",
        "",
        "function sunEvents(lang) {",
        "  return SUN_EVENT_KEYS.map(([k, s]) => [k, t(s, lang)]);",
        "}",
        "",
    ]
    return "\n".join(lines)


TARGETS = [
    (DOCS / "cities-data.js", render_cities),
    (DOCS / "strings-data.js", render_strings),
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true",
                    help="report drift and exit 1 without writing")
    args = ap.parse_args()

    stale = []
    for path, render in TARGETS:
        wanted = render()
        current = path.read_text(encoding="utf-8") if path.exists() else None
        if current == wanted:
            print(f"{path.name} current")
        elif args.check:
            stale.append(path.name)
        else:
            io.open(path, "w", encoding="utf-8", newline="").write(wanted)
            print(f"wrote {path.name}")

    if stale:
        print(f"stale, run scripts/build_web.py: {', '.join(stale)}", file=sys.stderr)
        return 1

    stamp = [sys.executable, str(Path(__file__).with_name("stamp_assets.py"))]
    if args.check:
        stamp.append("--check")
    return subprocess.call(stamp)


if __name__ == "__main__":
    sys.exit(main())
