"""The string table -- loaded and validated from data/strings.json.

Both languages live in one row so they cannot drift: a wording change is one
row edited twice, in view of each other, rather than two files edited weeks
apart. The app and the .ics generator read the same table, so a feed and the
screen cannot disagree about what an event is called.

A row missing either language is rejected at load. That matters more than it
looks: a missing translation would otherwise ship as a blank label on screen,
which reads as a broken app rather than as an untranslated one.
"""
import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
STRINGS_JSON = REPO / "data" / "strings.json"

LANGS = ("ar", "en")
KEY_RE = re.compile(r"^[a-z][a-zA-Z0-9]*(?:\.[a-z][a-zA-Z0-9]*)+$")


def _load():
    raw = json.loads(STRINGS_JSON.read_text(encoding="utf-8"))["strings"]
    for key, row in raw.items():
        if not KEY_RE.match(key):
            raise ValueError(f"strings.json: key {key!r} is not dotted.lowerCamel")
        for lang in LANGS:
            if not row.get(lang, "").strip():
                raise ValueError(f"strings.json: {key!r} has no {lang} text")
        extra = set(row) - set(LANGS)
        if extra:
            raise ValueError(f"strings.json: {key!r} has unknown language(s) {sorted(extra)}")
    return raw


STRINGS = _load()


def t(key, lang="ar"):
    """Translate. Raises on an unknown key rather than returning the key itself:
    a typo should fail the build, not surface as debug text in a live feed."""
    try:
        return STRINGS[key][lang]
    except KeyError:
        raise KeyError(f"no string {key!r} for language {lang!r}") from None


def fmt(key, lang="ar", **vars):
    """Translate and substitute {placeholders}. Missing placeholders raise,
    so a template change that forgets an argument fails the build rather
    than shipping a literal "{city}" into someone's calendar."""
    return t(key, lang).format(**vars)


#: The four sun events in display order, as (solar_times key, string key).
#: The generator and the app both iterate this, so the order and the wording
#: are decided in exactly one place.
SUN_EVENT_KEYS = (
    ("first_light", "sun.firstLight"),
    ("sunrise", "sun.sunrise"),
    ("sunset", "sun.sunset"),
    ("full_dark", "sun.fullDark"),
)


def sun_events(lang="ar"):
    """[(solar_times key, label), ...] for the given language."""
    return [(k, t(s, lang)) for k, s in SUN_EVENT_KEYS]


if __name__ == "__main__":
    import sys
    # Arabic output on a cp1252 Windows console raises otherwise.
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    print(f"{len(STRINGS)} strings, both languages present")
    for key in sorted(STRINGS):
        print(f"  {key:<20} ar={STRINGS[key]['ar']!r:<28} en={STRINGS[key]['en']!r}")
