"""Generate .ics feeds on demand, for nginx to proxy to.

    python3 vps/feed_server.py [--port 8971] [--host 127.0.0.1]

Bound to loopback by design: nginx terminates TLS and proxies to it, so this
process is never directly reachable from the internet.

WHY THIS EXISTS. Pre-baked feeds meant 33 cities x 2 languages of .ics
regenerated and committed on every wording change. Generated per request there
are no stored feeds at all: a label changes in data/strings.json and every feed
reflects it on the next fetch, with nothing to rebuild and nothing to forget.

URL SHAPE -- the existing paths must keep working exactly:

    /data/nasi-{city}-full-5y.ics        Arabic  (already in people's calendars)
    /data/nasi-{city}-full-5y-en.ics     English

An .ics URL can never be redirected or recalled once someone subscribes, so
these two forms are frozen. Anything else 404s rather than guessing.

CACHING. A feed takes a few seconds to build and subscribers refetch daily, so
each (city, lang) is cached in memory and rebuilt only when a source file
changes -- checked by mtime.

Invalidating the cache is NOT by itself enough to pick up a data change.
strings.py fills its table in a module global at IMPORT time, so a rebuild
would use the wording the process started with and the deploy would look like
it silently did nothing. The reload below is what makes "edit strings.json and
it takes effect" actually true.

Editing a .py file still requires `systemctl restart nasi-feeds`: the module
object is already in memory and nothing here re-imports code. Hot-reloading
code is not worth the failure modes; the restart is a second.
"""
import argparse
import re
import sys
import threading
import time
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

import json  # noqa: E402
from cities import CITIES  # noqa: E402
import strings  # noqa: E402
from strings import LANGS  # noqa: E402
import generate_ics_full as gen  # noqa: E402

SPAN_YEARS = 5

# Arabic is the unsuffixed historic name; every other language takes a suffix.
FEED_RE = re.compile(r"^/data/nasi-([a-z0-9-]+)-full-5y(?:-([a-z]{2}))?\.ics$")

# Any of these changing means every cached feed is stale.
SOURCES = [REPO / "data" / "strings.json", REPO / "data" / "cities.json",
           REPO / "data" / "nasi_days.json", REPO / "data" / "moon_phases.json",
           REPO / "data" / "lunar_eclipses.json",
           REPO / "scripts" / "generate_ics_full.py",
           REPO / "scripts" / "solar_times.py"]


def sources_stamp():
    return tuple(p.stat().st_mtime_ns if p.exists() else 0 for p in SOURCES)


class FeedCache:
    def __init__(self):
        self._lock = threading.Lock()
        self._stamp = None
        self._feeds = {}
        self._data = None

    def _load_inputs(self):
        self._data = (
            json.loads(Path(gen.DAYS_JSON).read_text(encoding="utf-8")),
            json.loads(Path(gen.MOON_JSON).read_text(encoding="utf-8")),
            json.loads(Path(gen.ECLIPSE_JSON).read_text(encoding="utf-8")),
        )

    def get(self, city_key, lang):
        with self._lock:
            stamp = sources_stamp()
            if stamp != self._stamp:
                # A source changed: drop everything rather than guessing which
                # feeds it touched. Rebuilding is seconds; serving a stale feed
                # is invisible and could persist for months.
                self._feeds.clear()
                self._data = None
                self._stamp = stamp
                # _load_inputs() below re-reads the JSON day/moon/eclipse
                # files, but the string table is a module global filled at
                # import. Without this, a wording change rebuilds into the
                # identical old bytes.
                strings.STRINGS = strings._load()
            key = (city_key, lang)
            if key not in self._feeds:
                if self._data is None:
                    self._load_inputs()
                start = f"{date.today().year}-01-01"
                end = f"{date.today().year + SPAN_YEARS - 1}-12-31"
                ics, *_ = gen.build(*self._data, city_key, start, end, lang=lang)
                self._feeds[key] = ics.encode("utf-8")
            return self._feeds[key]


CACHE = FeedCache()


class Handler(BaseHTTPRequestHandler):
    server_version = "nasi-feeds"

    def _send(self, status, body=b"", ctype="text/plain; charset=utf-8", extra=None):
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        if self.path == "/healthz":
            return self._send(200, b"ok\n")

        m = FEED_RE.match(self.path)
        if not m:
            return self._send(404, b"not found\n")
        city_key, lang = m.group(1), m.group(2) or "ar"
        if city_key not in CITIES or lang not in LANGS:
            return self._send(404, b"not found\n")

        try:
            body = CACHE.get(city_key, lang)
        except Exception as exc:                      # noqa: BLE001
            self.log_error("build failed for %s/%s: %s", city_key, lang, exc)
            return self._send(500, b"generation failed\n")

        self._send(200, body, "text/calendar; charset=utf-8", {
            # Subscribers poll daily; an hour of caching costs nothing and
            # protects the box if a feed is ever linked somewhere busy.
            "Cache-Control": "public, max-age=3600",
            "Content-Disposition":
                f'inline; filename="{Path(self.path).name}"',
        })

    def log_message(self, fmt, *args):
        sys.stderr.write("%s %s\n" % (self.log_date_time_string(), fmt % args))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8971)
    a = ap.parse_args()
    srv = ThreadingHTTPServer((a.host, a.port), Handler)
    print(f"nasi feed server on {a.host}:{a.port}, "
          f"{len(CITIES)} cities x {len(LANGS)} languages", flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()
