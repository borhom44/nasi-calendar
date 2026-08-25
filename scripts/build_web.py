"""Regenerate everything under docs/ that is derived from data/, then re-stamp.

Run this before committing any change to data/ or docs/:

    python scripts/build_web.py

It does two things, in this order, because the second depends on the first:

  1. emits docs/cities-data.js from data/cities.json (validated by cities.py)
  2. runs scripts/stamp_assets.py so index.html's ?v= hashes match the bytes

Both steps exist because of the same failure mode: something derived from a
source file silently going stale. A hand-copied city list drifts from the
registry; a stale ?v= hash serves old code to returning visitors with no error
anywhere. Neither announces itself.

    --check   report drift and exit 1 without writing anything
"""
import argparse
import io
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cities import REGIONS, CITIES, DOCS, CITIES_JSON  # noqa: E402

CITIES_JS = DOCS / "cities-data.js"

HEADER = """/* GENERATED FILE -- do not edit.
 *
 * Emitted from data/cities.json by scripts/build_web.py. Edit the JSON and
 * re-run that script; anything typed here is overwritten without warning.
 *
 * `CITIES` is the same global the app has always used, so solar.js and
 * moon-events.js keep working unchanged -- it is simply no longer hand-written
 * in two places that could disagree about a coordinate.
 */
"""


def render() -> str:
    def js(obj):
        return json.dumps(obj, ensure_ascii=False, separators=(", ", ": "))

    lines = [HEADER, f"const NASI_REGIONS = {js(REGIONS)};", "", "const CITIES = {"]
    for key, c in CITIES.items():
        entry = {k: c[k] for k in ("region", "ar", "en", "lat", "lon", "tz", "feed")}
        lines.append(f"  {json.dumps(key)}: {js(entry)},")
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


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true",
                    help="report drift and exit 1 without writing")
    args = ap.parse_args()

    wanted = render()
    current = CITIES_JS.read_text(encoding="utf-8") if CITIES_JS.exists() else None

    if current == wanted:
        print(f"{CITIES_JS.name} current ({len(CITIES)} cities)")
    elif args.check:
        print(f"{CITIES_JS.name} is stale against {CITIES_JSON.name}"
              f" -- run scripts/build_web.py", file=sys.stderr)
        return 1
    else:
        io.open(CITIES_JS, "w", encoding="utf-8", newline="").write(wanted)
        print(f"wrote {CITIES_JS.name} ({len(CITIES)} cities, {len(REGIONS)} regions)")

    stamp = [sys.executable, str(Path(__file__).with_name("stamp_assets.py"))]
    if args.check:
        stamp.append("--check")
    return subprocess.call(stamp)


if __name__ == "__main__":
    sys.exit(main())
