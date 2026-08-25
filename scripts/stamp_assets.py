"""Re-stamp the ?v= cache-busting hashes in docs/index.html.

WHY THIS EXISTS. Every local script is loaded as `solar.js?v=013409cd`, where
the suffix is md5(file bytes)[:8]. Browsers cache that exact URL, so if the
file changes and the hash does not, a returning visitor keeps running the OLD
code -- silently, with no error and nothing in the console. The site looks
deployed and behaves as if it never was.

The hashes were hand-maintained, which is exactly the kind of step that gets
forgotten (`nasi-extend.js?v=1` had never been bumped at all). Run this after
touching anything under docs/, before committing:

    python scripts/stamp_assets.py

    --check   report drift and exit 1 without writing, for a pre-commit hook

Only files whose contents actually changed get a new hash, so a no-op run
produces no diff.
"""
import argparse
import hashlib
import io
import re
import sys
from pathlib import Path

DOCS = Path(__file__).resolve().parent.parent / "docs"
HTML = DOCS / "index.html"

# src="name.js?v=hash" / href="name.css?v=hash" -- local paths only, no scheme.
PATTERN = re.compile(r'((?:src|href)=")(?!https?:|//)([^"?]+\.(?:js|css))\?v=([^"]*)(")')


def short_hash(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()[:8]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true",
                    help="report drift and exit 1 without writing")
    args = ap.parse_args()

    html = io.open(HTML, encoding="utf-8").read()
    changed, missing = [], []

    def repl(m):
        prefix, name, old, suffix = m.groups()
        target = DOCS / name
        if not target.exists():
            missing.append(name)
            return m.group(0)
        new = short_hash(target)
        if new != old:
            changed.append((name, old, new))
        return f"{prefix}{name}?v={new}{suffix}"

    stamped = PATTERN.sub(repl, html)

    for name in missing:
        print(f"  MISSING referenced file: {name}", file=sys.stderr)

    if not changed:
        print("all asset hashes current" + (" (referenced files missing!)" if missing else ""))
        return 1 if missing else 0

    for name, old, new in changed:
        print(f"  {name}: {old} -> {new}")

    if args.check:
        print(f"{len(changed)} asset(s) stale -- run scripts/stamp_assets.py", file=sys.stderr)
        return 1

    io.open(HTML, "w", encoding="utf-8", newline="").write(stamped)
    print(f"stamped {len(changed)} asset(s) in {HTML.name}")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
