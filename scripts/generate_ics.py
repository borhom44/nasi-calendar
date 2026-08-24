"""
Generate an .ics calendar feed of daily Nasi'-calendar date overlays.

Each day in the requested range gets one all-day VEVENT whose title is the
Nasi' date ("7 Jumada al-Ula 1447 AH"), the same way Google Calendar's
built-in Hebrew/Chinese calendar overlays work.

Usage:
    python generate_ics.py --start 2000-01-01 --end 2100-12-31 --out full.ics
    python generate_ics.py --years-around 5 --out nearby.ics   # default

Google Calendar's manual "Import" screen silently caps out around ~1000
events; a full 100-year feed (~36,890 events) will exceed that. Two ways
around it:
  - Import a smaller window directly (this script's default: +-5 years).
  - Host the full .ics file somewhere with a stable URL (e.g. a personal
    VPS) and use Google Calendar's "From URL" subscribe option instead of
    Import -- that path does not have the same event-count ceiling.
"""
import argparse
import json
from datetime import date, datetime, timedelta, timezone

DAYS_JSON = r"C:\Dev\nasi-calendar\data\nasi_days.json"


def load_days():
    with open(DAYS_JSON, encoding="utf-8") as f:
        return json.load(f)


def escape_ics(text):
    return text.replace("\\", "\\\\").replace(",", "\\,").replace(";", "\\;")


def build_ics(days, start, end):
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//nasi-calendar//Bara'at al-Nasi' overlay//AR",
        "CALSCALE:GREGORIAN",
        "X-WR-CALNAME:التقويم النسيء (Nasi' Calendar)",
        "X-WR-CALDESC:Daily Nasi'-calendar date overlay, reconstructed from the "
        "2000-2100 table in Bara'at al-Nasi' (Wisam al-Din Ishaq).",
    ]
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    count = 0
    for d in days:
        g = d["g"]
        if not (start <= g <= end):
            continue
        gdate = date.fromisoformat(g)
        nextday = gdate + timedelta(days=1)
        summary = f"{d['nd']} {d['nm']} {d['ny']} هـ"
        uid = f"nasi-{g}@nasi-calendar.local"
        lines += [
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTAMP:{stamp}",
            f"DTSTART;VALUE=DATE:{gdate.strftime('%Y%m%d')}",
            f"DTEND;VALUE=DATE:{nextday.strftime('%Y%m%d')}",
            f"SUMMARY:{escape_ics(summary)}",
            "TRANSP:TRANSPARENT",
            "END:VEVENT",
        ]
        count += 1
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n", count


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default=None, help="YYYY-MM-DD, default = today - years-around")
    ap.add_argument("--end", default=None, help="YYYY-MM-DD, default = today + years-around")
    ap.add_argument("--years-around", type=int, default=5)
    ap.add_argument("--out", default=r"C:\Dev\nasi-calendar\data\nasi-calendar.ics")
    args = ap.parse_args()

    today = date.today()
    start = args.start or (today.replace(year=today.year - args.years_around)).isoformat()
    end = args.end or (today.replace(year=today.year + args.years_around)).isoformat()
    start = max(start, "2000-01-01")
    end = min(end, "2100-12-31")

    days = load_days()
    ics, count = build_ics(days, start, end)
    with open(args.out, "w", encoding="utf-8", newline="") as f:
        f.write(ics)
    print(f"wrote {count} events ({start}..{end}) to {args.out}")


if __name__ == "__main__":
    main()
