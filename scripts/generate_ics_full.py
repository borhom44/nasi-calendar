"""Generate the .ics feed: one all-day entry per day, and by default nothing else.

  ONE ALL-DAY event per day -- the title is the Nasi' date with the moon's
  phase as an icon, and the description carries that day's four sun events for
  the chosen city plus the moon's illumination.

Three other kinds of entry can be switched on (--sun-events, --moon-events,
--eclipses) and are OFF everywhere that ships. They used to be on: four timed
sun events a day, plus moon instants and eclipses, came to 9,266 events over
five years, which leaves a subscriber's calendar permanently full and buries
the date itself -- the one thing the feed exists to deliver. Removing them
loses no information: the sun times are in the daily entry's description,
which is what a reader sees on the single tap they were going to make anyway.

All times are written as UTC (the trailing Z form). This is deliberate: a
calendar client renders UTC in the viewer's own timezone, so the feed stays
correct if you travel, and there is no VTIMEZONE block to get stale when a
country changes its DST rules -- which Egypt did in 2023, mid-way through
this calendar's range.

Usage:
    python generate_ics_full.py --city cairo --years-around 1 --out out.ics
    python generate_ics_full.py --city barcelona --start 2000-01-01 --end 2100-12-31 --out full.ics
"""
import argparse
import json
import math
import sys
from datetime import date, datetime, timedelta, timezone

# Paths derive from this file, not from an absolute Windows path. The old
# hardcoded C:\Dev\... meant the generator could not run on the VPS at all,
# which is where feeds are ultimately built.
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from solar_times import sun_times, hhmm  # noqa: E402
from strings import sun_events, t as tr, fmt  # noqa: E402
from cities import CITIES, DATA, label as city_label  # noqa: E402
from generate_moon_phases import new_moon_jde, greg_to_jd, _args, _planetary, RAD  # noqa: E402

DAYS_JSON = str(DATA / "nasi_days.json")
MOON_JSON = str(DATA / "moon_phases.json")
ECLIPSE_JSON = str(DATA / "lunar_eclipses.json")

# Unicode has all eight phases, which is the closest an .ics can get to the
# app's SVG moon. The thresholds are copied from docs/moon.js MOON_PHASE_NAMES
# deliberately -- if they ever drift apart, the calendar and the app would
# disagree about what phase the same day is in.
SYNODIC_MEAN = 29.530589


def nasi_month_label(arabic_name, lang):
    """The same mapping the app's nasiMonthLabel() does. nasi_days.json stores
    month names in Arabic only, so any other language has to find the name's
    index in the Arabic list and take the same position from its own."""
    if lang == "ar":
        return arabic_name
    names_ar = tr("month.nasi", "ar").split(",")
    try:
        i = names_ar.index(arabic_name)
    except ValueError:
        return arabic_name          # unknown month: show it rather than lose it
    return tr("month.nasi", lang).split(",")[i]


def moon_emoji(illum, age):
    waxing = age < SYNODIC_MEAN / 2
    if illum < 6:
        return "🌑"                                    # محاق / new
    if illum < 44:
        return "🌒" if waxing else "🌘"        # هلال
    if illum < 56:
        return "🌓" if waxing else "🌗"        # تربيع
    if illum < 94:
        return "🌔" if waxing else "🌖"        # أحدب
    return "🌕"                                        # بدر / full


ECLIPSE_AR = {"T": "خسوف كلي", "P": "خسوف جزئي", "N": "خسوف شبه ظلي"}


def moon_phase_jde(k, full=False):
    """Same series as generate_moon_phases.new_moon_jde, plus the full-moon
    coefficient set (Meeus ch.49). Kept here rather than imported because
    that module only ever needed the new-moon branch."""
    if not full:
        return new_moon_jde(k)
    T, E, M, Mp, F, Om, jde = _args(k + 0.5)
    c = (-0.40614 * math.sin(Mp) + 0.17302 * E * math.sin(M)
         + 0.01614 * math.sin(2 * Mp) + 0.01043 * math.sin(2 * F)
         + 0.00734 * E * math.sin(Mp - M) - 0.00515 * E * math.sin(Mp + M)
         + 0.00209 * E * E * math.sin(2 * M)
         - 0.00111 * math.sin(Mp - 2 * F) - 0.00057 * math.sin(Mp + 2 * F)
         + 0.00056 * E * math.sin(2 * Mp + M) - 0.00042 * math.sin(3 * Mp)
         + 0.00042 * E * math.sin(M + 2 * F) + 0.00038 * E * math.sin(M - 2 * F)
         - 0.00024 * E * math.sin(2 * Mp - M) - 0.00017 * math.sin(Om)
         - 0.00007 * math.sin(Mp + 2 * M) + 0.00004 * math.sin(2 * Mp - 2 * F)
         + 0.00004 * math.sin(3 * M) + 0.00003 * math.sin(Mp + M - 2 * F)
         + 0.00003 * math.sin(2 * Mp + 2 * F) - 0.00003 * math.sin(Mp + M + 2 * F)
         + 0.00003 * math.sin(Mp - M + 2 * F) - 0.00002 * math.sin(Mp - M - 2 * F)
         - 0.00002 * math.sin(3 * Mp + M) + 0.00002 * math.sin(4 * Mp))
    return jde + c + _planetary(k + 0.5, T)


def delta_t_seconds(y):
    if y < 2050:
        t = y - 2000
        return 62.92 + 0.32217 * t + 0.005589 * t * t
    return -20 + 32 * ((y - 1820) / 100.0) ** 2 - 0.5628 * (2150 - y)


def jde_to_utc(jde, approx_year):
    jd_ut = jde - delta_t_seconds(approx_year) / 86400.0
    unix_s = (jd_ut - 2440587.5) * 86400.0
    return datetime.fromtimestamp(unix_s, tz=timezone.utc)


def escape_ics(text):
    return (text.replace("\\", "\\\\").replace(",", "\\,")
                .replace(";", "\\;").replace("\n", "\\n"))


def fold(line):
    """RFC 5545 caps a content line at 75 OCTETS. Arabic is 2 bytes/char in
    UTF-8, so a visually short line can still overflow -- fold on encoded
    length, never on character count, and never split a multi-byte char."""
    raw = line.encode("utf-8")
    if len(raw) <= 75:
        return line
    out, cur = [], b""
    for ch in line:
        b = ch.encode("utf-8")
        limit = 75 if not out else 74          # continuation lines carry a leading space
        if len(cur) + len(b) > limit:
            out.append(cur.decode("utf-8"))
            cur = b
        else:
            cur += b
    out.append(cur.decode("utf-8"))
    return "\r\n ".join(out)


def build(days, moon, eclipses, city_key, start, end, lang="ar",
          with_sun_events=False, with_moon_events=False, with_eclipses=False):
    # lang selects the display language for every label in the feed. It is a
    # parameter rather than a constant because Phase 2 generates one feed per
    # city per language from this same code path -- no wording is hardcoded.
    #
    # ONE ENTRY PER DAY is the default, and the default is what the live feeds
    # use. Four timed sun events a day plus moon and eclipse entries came to
    # 9,266 events over five years and made the subscriber's calendar unusable:
    # every day permanently full. The sun times were never lost by removing
    # them -- they have always also been in this entry's DESCRIPTION, which is
    # what the reader sees on the single tap they were going to make anyway.
    #
    # The other three are kept behind flags rather than deleted: the code is
    # correct and someone may want a research feed. Nothing generates them now.
    city = CITIES[city_key]
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        f"PRODID:-//nasi-calendar//Nasi'//{lang.upper()}",
        "CALSCALE:GREGORIAN",
        # Google ignores both of these and refetches on its own schedule (8-24h,
        # sometimes longer, with no way for a publisher to trigger it). Apple
        # Calendar and Outlook do honour them, so they are worth stating even
        # though the largest audience will not act on them.
        "REFRESH-INTERVAL;VALUE=DURATION:PT12H",
        "X-PUBLISHED-TTL:PT12H",
        fold("X-WR-CALNAME:" + escape_ics(fmt("feed.calendarName", lang, city=city_label(city, lang)))),
        # was hardcoded Arabic, so every English subscriber got an Arabic
        # calendar description in a feed whose labels were otherwise English
        fold("X-WR-CALDESC:" + escape_ics(tr("feed.calendarDesc", lang))),
    ]

    n_day = n_moon = n_ecl = n_sun = 0
    epoch = date(2000, 1, 1)

    # --- 1. all-day Nasi' date entries, with sun times + moon illumination ---
    for d in days:
        g = d["g"]
        if not (start <= g <= end):
            continue
        gdate = date.fromisoformat(g)
        t = sun_times(gdate, city["lat"], city["lon"], city["tz"])
        idx = (gdate - epoch).days
        illum = moon[idx][0] if 0 <= idx < len(moon) else None
        age = moon[idx][1] if 0 <= idx < len(moon) else None

        # Built from SUN_EVENTS so the description, the timed entries below and
        # the app's own panel can never disagree about wording or order.
        desc_parts = [
            " · ".join(f"{label} {hhmm(t[key])}" for key, label in sun_events(lang))
            + f"  ({city_label(city, lang)})",
        ]
        if illum is not None:
            desc_parts.append(fmt("feed.moonIllum", lang, pct=illum))

        # The headline carries only the date and the moon's phase. The four sun
        # events are emitted below as TIMED entries so they land in the day grid
        # at the hour they actually happen -- reading "الغروب" in the 19:00 row
        # beats parsing a time out of an all-day banner. Full times stay in this
        # description too, so one tap still shows all four together.
        # The month name in nasi_days.json is Arabic, so an English feed has
        # to translate it -- and the era marker was "هـ" (AH), which belongs to
        # the official Hijri calendar the app deliberately keeps as a SEPARATE
        # row. Labelling a Nasi' date with it conflated the two calendars this
        # whole project exists to distinguish.
        icon = moon_emoji(illum, age) + " " if illum is not None else ""
        summary = (f"{icon}{d['nd']} {nasi_month_label(d['nm'], lang)} "
                   f"{d['ny']} {tr('era.nasi', lang)}")

        lines += [
            "BEGIN:VEVENT",
            f"UID:nasi-{g}-{city_key}@nasi-calendar",
            f"DTSTAMP:{stamp}",
            f"DTSTART;VALUE=DATE:{gdate.strftime('%Y%m%d')}",
            f"DTEND;VALUE=DATE:{(gdate + timedelta(days=1)).strftime('%Y%m%d')}",
            fold(f"SUMMARY:{escape_ics(summary)}"),
            fold(f"DESCRIPTION:{escape_ics('\n'.join(desc_parts))}"),
            "TRANSP:TRANSPARENT",
            "END:VEVENT",
        ]
        n_day += 1

        # --- the four sun events, as timed entries at their real instants ---
        # Written in UTC like the moon events: sunrise in Cairo is an instant,
        # so a client renders it in whatever zone the reader is in, and there is
        # no VTIMEZONE block to go stale when a country changes its DST rules
        # (Egypt did, in 2023, mid-way through this calendar's range).
        # TRANSP:TRANSPARENT matters more here than anywhere else -- four opaque
        # events a day would make the reader permanently "busy" to anyone
        # checking their free/busy.
        if with_sun_events:
            for key, label in sun_events(lang):
                when = t.get(key)
                if when is None:          # undefined at high latitude; skip it
                    continue
                z = when.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
                lines += [
                    "BEGIN:VEVENT",
                    f"UID:sun-{key}-{g}-{city_key}@nasi-calendar",
                    f"DTSTAMP:{stamp}",
                    f"DTSTART:{z}",
                    f"DTEND:{z}",
                    fold(f"SUMMARY:{escape_ics(label)}"),
                    fold("DESCRIPTION:" + escape_ics(fmt("feed.eventInCity", lang, event=label, city=city_label(city, lang)))),
                    "TRANSP:TRANSPARENT",
                    "END:VEVENT",
                ]
                n_sun += 1

    # --- 2. exact new-moon and full-moon instants (off by default) ---
    start_jd = greg_to_jd(*[int(x) for x in start.split("-")])
    end_jd = greg_to_jd(*[int(x) for x in end.split("-")])
    k_lo = int(math.floor((start_jd - 2451550.09766) / 29.530588861)) - 1
    k_hi = int(math.ceil((end_jd - 2451550.09766) / 29.530588861)) + 1

    for k in (range(k_lo, k_hi + 1) if with_moon_events else ()):
        for is_full, label in ((False, "🌑 بداية دورة قمرية جديدة (محاق)"),
                               (True, "🌕 اكتمال القمر (بدر)")):
            approx_y = 2000 + int(k / 12.3685)
            dt = jde_to_utc(moon_phase_jde(k, is_full), approx_y)
            if not (start <= dt.date().isoformat() <= end):
                continue
            stampfmt = dt.strftime("%Y%m%dT%H%M%SZ")
            lines += [
                "BEGIN:VEVENT",
                f"UID:moon-{'full' if is_full else 'new'}-{k}@nasi-calendar",
                f"DTSTAMP:{stamp}",
                f"DTSTART:{stampfmt}",
                f"DTEND:{stampfmt}",
                fold(f"SUMMARY:{escape_ics(label)}"),
                "TRANSP:TRANSPARENT",
                "END:VEVENT",
            ]
            n_moon += 1

    # --- 3. real lunar eclipses from NASA's catalog (off by default) ---
    for ev in (eclipses if with_eclipses else ()):
        dt = datetime.strptime(ev["t"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        if not (start <= dt.date().isoformat() <= end):
            continue
        stampfmt = dt.strftime("%Y%m%dT%H%M%SZ")
        lines += [
            "BEGIN:VEVENT",
            f"UID:eclipse-{ev['t']}@nasi-calendar",
            f"DTSTAMP:{stamp}",
            f"DTSTART:{stampfmt}",
            f"DTEND:{stampfmt}",
            fold(f"SUMMARY:{escape_ics(ECLIPSE_AR[ev['k']] + ' 🌘')}"),
            fold(f"DESCRIPTION:{escape_ics('من كتالوج ناسا لخسوفات القمر (Espenak & Meeus). التوقيت بالتوقيت العالمي UTC، وسيعرضه تقويمك بتوقيتك المحلي.')}"),
            "TRANSP:TRANSPARENT",
            "END:VEVENT",
        ]
        n_ecl += 1

    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n", n_day, n_moon, n_ecl, n_sun


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--city", default="cairo", choices=sorted(CITIES))
    ap.add_argument("--start")
    ap.add_argument("--end")
    ap.add_argument("--years-around", type=int, default=1)
    ap.add_argument("--out", required=True)
    # Four extra events a day is ~4x the file. Worth it over five years; over a
    # century it would be a ~55MB feed that every subscriber re-fetches daily,
    # so the 100-year file deliberately ships without them.
    # These were on by default and are now opt-in. A feed with four timed sun
    # events a day leaves the reader permanently booked; the times are in the
    # daily entry's description either way, which is where they are actually
    # read. Kept as flags because the code is correct and a research feed may
    # want them -- nothing that ships turns them on.
    ap.add_argument("--sun-events", action="store_true",
                    help="also emit the four daily sun events as timed entries")
    ap.add_argument("--moon-events", action="store_true",
                    help="also emit exact new-moon and full-moon instants")
    ap.add_argument("--eclipses", action="store_true",
                    help="also emit lunar eclipses from NASA's catalogue")
    ap.add_argument("--everything", action="store_true",
                    help="shorthand for --sun-events --moon-events --eclipses")
    # build() has always taken lang; the CLI never exposed it, so the only way
    # to produce an English feed was through build_feeds.py or the server.
    ap.add_argument("--lang", default="ar", choices=("ar", "en"),
                    help="feed language (default: ar)")
    a = ap.parse_args()

    today = date.today()
    start = a.start or today.replace(year=today.year - a.years_around).isoformat()
    end = a.end or today.replace(year=today.year + a.years_around).isoformat()
    start, end = max(start, "2000-01-01"), min(end, "2100-12-31")

    days = json.load(open(DAYS_JSON, encoding="utf-8"))
    moon = json.load(open(MOON_JSON, encoding="utf-8"))
    eclipses = json.load(open(ECLIPSE_JSON, encoding="utf-8"))

    ics, nd, nm, ne, ns = build(
        days, moon, eclipses, a.city, start, end,
        with_sun_events=a.sun_events or a.everything,
        with_moon_events=a.moon_events or a.everything,
        with_eclipses=a.eclipses or a.everything,
        lang=a.lang)
    with open(a.out, "w", encoding="utf-8", newline="") as f:
        f.write(ics)
    total = nd + nm + ne + ns
    print(f"wrote {total} events to {a.out}")
    print(f"  {nd} daily Nasi' dates (with {a.city} sun times + moon illumination)")
    print(f"  {nm} moon phase instants (new/full)")
    print(f"  {ne} lunar eclipses (NASA catalog)")
    print(f"  {ns} timed sun events (first light/sunrise/sunset/full dark)")
    print(f"  range {start} .. {end}")
    if total > 1000:
        print(f"  NOTE: {total} events exceeds Google's ~1000-event manual-import cap;")
        print(f"        this file needs the subscribe-by-URL path instead.")


if __name__ == "__main__":
    main()
