# Nasi' Calendar (التقويم النسيء)

> ## Source & attribution
>
> The day-by-day calendar data in this project comes from the 2000–2100 CE table
> published as an appendix to ***براءة النسيء* ("Bara'at al-Nasi'") by وسام الدين إسحق
> (Wisam al-Din Ishaq)**. The original reconstruction work, the method, and the table
> itself are his.
>
> This repository is an **independent software reconstruction** of that table. It is not
> an official version, is not endorsed by or affiliated with the author, and any error
> here is an error in this extraction rather than in the book. Anyone wanting the full
> argument and evidence should go to the book itself.
>
> The **astronomy is independent of the book**: sun times (NOAA), moon phases and
> new/full-moon instants (Meeus, *Astronomical Algorithms* ch.49), and lunar eclipses
> (NASA's Five Millennium Catalog, Espenak & Meeus, NASA/TP-2009-214173). Those are
> used to *verify* the calendar, not to build it — see "Verified against real astronomy".
>
> This is a research and verification project, **not a religious authority**. The
> official Hijri calendar, not this one, is what governs religious observance.


A converter and Google Calendar overlay for the pre-Islamic Arabian lunisolar
calendar — the one that inserted a 13th "Nasi'" month roughly every 2–3 years
to keep the lunar months anchored to the solar seasons, before Islam
abolished the practice (Quran 9:37).

The underlying day-by-day data is not computed from scratch — it's
reconstructed from the 2000–2100 CE table published as an appendix to
*براءة النسيء* ("Bara'at al-Nasi'") by Wisam al-Din Ishaq, who built it by
cross-referencing real astronomical new-moon/eclipse data against a Quranic
argument (9:36–37) for a base "leap month every 3 years" rule, refined into a
19-year/235-lunar-month cycle with insertions at three fixed positions. That
algorithm evolves across the book and isn't fully deterministic from the
text alone, so this project treats the author's own published table as
ground truth rather than re-deriving the rule.

**Coverage: 2000-01-01 through 2100-12-31 only** (whatever the source table covers).

## Live site

**https://nasi.ibrahimabdelrahim.cloud/**

Subscribe-by-URL feeds (Google Calendar → Add calendar → **From URL**, not
Import). Pick one city — sun times differ between them:

The **About** tab has a picker that builds the right link for your city and
language. The pattern, if you would rather write it yourself:

```
https://nasi.ibrahimabdelrahim.cloud/data/nasi-<city>-full-5y.ics      # Arabic
https://nasi.ibrahimabdelrahim.cloud/data/nasi-<city>-full-5y-en.ics   # English
```

All 33 city keys work — `cairo`, `mecca`, `jerusalem`, `istanbul`, `london`,
`new-york`, `sao-paulo`, `kuala-lumpur`, and the rest. A key that is not a city
returns 404 rather than a guess.

One feed per city per language: Arabic keeps the historic unsuffixed name
because people are already subscribed to it, English takes a `-en` suffix.
Each covers 2026–2030 with 9,266 events in about 2.3 MB — 1,826 daily Nasi'
dates, four timed sun events a day, and the new/full moon instants and lunar
eclipses.

The 1-year and 100-year spans were retired. Importing rather than subscribing
is unusable at any span, and at four sun events a day the 100-year file came
to ~55 MB re-fetched daily by every subscriber.

Feeds are generated when your calendar asks for one, not stored — which is why
all 33 cities have links rather than the two that fitted in a static repo, and
why arbitrary coordinates work in the app. A cold city takes about 190 ms to
compute and 3 ms thereafter, and the response is gzipped: 2.5 MB of calendar
text goes over the wire as about 139 KB.

Every feed carries four timed events a day — أول الضوء / الشروق / الغروب / الظلام التام, i.e. astronomical twilight to astronomical twilight —
at their exact instants, so they land in the day grid rather than being buried in
an all-day banner's description. That is 4× the events, which is affordable over
five years and not over a century: the 100-year feed is generated with
`--no-sun-events` deliberately, since with them it would be a ~55 MB file that
every subscriber re-fetches daily. It still carries the daily Nasi' date, the
moon phase icon, the new/full moon instants and the NASA eclipses.

**Importing is no longer viable for any span** — subscribe by URL.

Subscribing has no event-count ceiling and auto-updates; importing copies the
events in once and is capped. When in doubt, subscribe.

### Why a custom domain

The site is addressed at `nasi.ibrahimabdelrahim.cloud` and, since 26 Aug 2026,
served from the VPS (Hostinger DNS, `A nasi -> 186.240.155.88`). It began on
GitHub Pages behind the same name, and that is the whole reason the custom
domain existed from day one: an `.ics` URL, once it is sitting in someone's
calendar subscription, can never be redirected — a static host cannot issue a
301 — and the publisher has no way to find out who subscribed or to contact
them. A URL under a domain we control can be re-pointed at any host forever,
which is exactly what the move to the VPS did, without a single subscriber
having to do anything. A `github.io` path is only as durable as that
repository's name.

Rollback is one DNS record: putting the CNAME back restores the Pages site.
The feeds do not come back with it — the static `.ics` files were deleted on
26 Aug 2026, and they only ever covered Cairo and Barcelona, so as a fallback
they already left 31 of the 33 cities returning 404. The real protection is
that the generator is stdlib-only Python with no dependencies: it runs
anywhere, from this repo, in about 190 ms a city.

The old `borhom44.github.io/nasi-calendar/*` paths still 301 to the new domain,
so nothing published before the move is broken.

### Staying up

Feeds are generated on request, so the site depends on `nasi-feeds.service`
being alive. `nasi-health.timer` checks it every five minutes and tests the
whole chain the way a subscriber does — public DNS, TLS, nginx, the proxy hop
and the generator — because each layer can fail while the one below it still
looks healthy. `Restart=on-failure` only catches the process exiting; a wedged
worker, a dead nginx, or a certificate that quietly failed to renew all leave
the unit `active` and every feed unreachable.

It **repairs before it reports**, and escalates by blame rather than by
desperation. `nasi-feeds` is ours alone, so bouncing it is always safe. nginx
is **shared with Personal OS** on the same box, so it is only touched when it
is actually implicated: the site is served by nginx directly while a feed goes
through the proxy, so a 200 on the site proves nginx is healthy and the fault
is downstream. Reloading it then would disturb someone else's service to fix
something it is not causing.

Measured, with the feed server stopped outright: detected the 502, restarted
`nasi-feeds`, recovered — about 9 seconds, and zero nginx reloads.

`https://nasi.ibrahimabdelrahim.cloud/healthz` returns `ok` in three bytes, for
an external uptime monitor that should not pull 2.5 MB of calendar every few
minutes.

**The external monitor is `.github/workflows/uptime.yml`.** A check running on
the machine it is checking reports nothing when that machine is off, so this
one runs on GitHub's infrastructure instead — roughly every 10 minutes, hitting
`/healthz`, a real feed (a 200 with the wrong body is the failure that would
otherwise go unnoticed), and the certificate. It retries three times before
declaring anything, so a blip on GitHub's side does not cry wolf.

On failure it opens a labelled issue and the job fails, which is two
notifications; the issue closes itself when the site comes back. It needs no
account and no secret — `github.token` is enough.

Two caveats: GitHub's cron is best-effort and can run late under load, so treat
the interval as approximate. And GitHub disables scheduled workflows after 60
days with no repository activity — it emails a warning first, and the Actions
tab re-enables it.

Alerting is opt-in. Create `/etc/nasi-health.conf` (root, mode 600):

```
TELEGRAM_TOKEN=...
TELEGRAM_CHAT_ID=...
```

Without it the check logs to the journal and does nothing else. The token is
passed to curl through `--config` on stdin, never on the command line, because
argv is world-readable via `ps`.


## Month names (deliberate departure from the standard Hijri calendar)

This calendar has **no المحرم**. The twelve regular months run:

> صفر الأول · صفر الثاني · ربيع الأول · ربيع الثاني · جمادى الأولى · جمادى الثانية ·
> رجب · شعبان · رمضان · شوال · ذو القعدة · ذو الحجة

plus **نسيء** when the intercalary month is inserted.

This matches the source table's own key (book p.14), which enumerates exactly
these thirteen symbols — `صفر1 صفر2 ر1 ر2 ج1 ج2 رجب شعبان رمضان شوال ذق ذح النسيء` —
with المحرم absent from the list. The author's stated reason: he treats
"al-Muharram" as a name the *Nasi'* month carries rather than a fixed slot, and
starts the lunar year at صفر الأول so it begins immediately after the Hajj rite.

Two things worth being explicit about:

- **This is not how the standard Islamic calendar names its months**, where
  المحرم is month 1 in its own right. The author is departing from that
  deliberately as part of the book's argument; it is a contested convention,
  not a neutral fact. It's kept here because the day-by-day data comes from
  his table, and mixed labelling would be worse than either choice alone.
- **The intercalary month is only ever displayed as نسيء.** Page 14 also gives
  it position-dependent names (المحرم at position 13, رجب مضر at position 9,
  رجب ربيعة at position 5), but the charts themselves always print the plain
  نسيء label (p.15), and so does this project. Those alternate names are
  never used as labels anywhere in the data or UI.

Switching to standard المحرم/صفر labelling would touch only these two names —
the underlying day arithmetic is identical either way.

## Nasi' insertion positions

The Nasi' month lands at one of three fixed slots in the cycle, and the source
table marks which one applies by printing a green **5**, **9**, or **13** to the
left of each year that carries an insertion (p.14):

| Marker | Inserted between | Alternate name in the book's prose |
|---|---|---|
| 5 | ربيع الثاني → جمادى الأولى | رجب ربيعة |
| 9 | شعبان → رمضان | رجب مضر |
| 13 | ذو الحجة → (year restart) | المحرم |

Position **9** is why the month before Ramadan is sometimes نسيء — that is a
documented, intended placement, not an extraction error.

## What's here

- `data/nasi_days.json` — every day in range, `{g: "YYYY-MM-DD", ny, nm, nd}`.
- `data/nasi_months.json` — the same data compressed to month boundaries
  (~1,250 rows instead of ~36,890) — this is what the web page actually uses.
- `data/cities.json` — the city registry, sole source for all 33 cities. The
  browser copy `docs/cities-data.js` is generated from it.
- `data/strings.json` — every user-visible string with `ar` and `en` side by
  side. `docs/strings-data.js` is generated from it.
- Feeds are not stored anywhere. `vps/feed_server.py` generates each one when
  a calendar asks for it — ~190 ms cold, ~3 ms cached — from `data/*.json` via
  `scripts/generate_ics_full.py`. Nothing on disk can go stale.
- `docs/index.html` — the web app: a month grid
  (each Gregorian day shows its Nasi' date underneath, the convention the source
  table uses), a two-way converter, a sky panel and a cycles view.
- `scripts/extract_spans.py` — PDF → `data/raw_spans.json` (colour-tagged text
  spans; supplies the day digits).
- `scripts/extract_labels.py` — PDF → `data/label_tokens.json` (the 1,250
  printed month labels, split at character resolution — see below).
- `scripts/build_calendar.py` — both of the above → `nasi_days.json`.
- `scripts/generate_ics.py` — plain date-only `.ics` feeds.
- `scripts/generate_ics_full.py` — the enriched feeds: adds per-day sun times
  and moon illumination, plus timed new-moon/full-moon/eclipse events.
- `scripts/solar_times.py` — sun times (NOAA); DST via real IANA rules.
- `scripts/generate_moon_phases.py` / `scripts/extract_lunar_eclipses.py` —
  per-day moon illumination, and the NASA eclipse catalog as web-ready data.
- `scripts/verify_astronomy.py` — tests the result against real lunations, full
  moons, and NASA's eclipse catalog (see "Verified against real astronomy").
- `scripts/divergence.py` — compares this calendar to the official (tabular)
  Hijri calendar and extrapolates back to where they separated. Read its
  caveat: the answer is an extrapolation from a 101-year table, not data.
- `scripts/abolition.py` — runs the intercalation backwards to the year it
  must have stopped. Lands on ~18 AH, matching the book's own stated "no trace
  after year 17". **This recovers the author's assumption, not a historical
  fact** — he chose the year numbering, so this is an internal-consistency
  check on his table (and on our extraction of it), nothing more.
- `data/validation_report.txt` — self-check output from the last build.

## Using the converter page

It's a static page with no build step, but it loads its data via
`<script src>`, which some browsers block under a bare `file://` URL — serve
it locally instead:

```bash
python -m http.server 8902 --directory docs
```

Then open `http://localhost:8902`.

## Getting it into Google Calendar

Google Calendar's manual **Import** screen has an undocumented soft cap around
~1,000 events per file.

**Subscribe, do not import.** Subscribing creates a separate calendar you can
remove in one click and which refreshes itself; importing copies thousands of
events into your own calendar with no way to delete them in bulk.

In Google Calendar on a computer (the phone app cannot add a calendar by URL):
Other calendars → **+** → **From URL** → paste one of the links above.

Each feed carries, per day: the Nasi' date with a moon-phase icon in the title,
the four sun events as timed entries at their real instants, and the moon's
illumination and distance in the description. Plus the exact new and full moon
instants and every real lunar eclipse from NASA's catalogue.

Moon and eclipse times are written in **UTC** (the trailing `Z` form) rather
than with a VTIMEZONE block. Two reasons: a client renders UTC in the viewer's
own zone, so the feed stays correct when you travel; and there's no embedded
DST rule to go stale — which matters here, because Egypt reinstated DST in
2023, part-way through this calendar's range.

Regenerate with a custom range or city:

```bash
python scripts/generate_ics_full.py --city cairo --years-around 1 --out docs/data/custom.ics
python scripts/generate_ics_full.py --city barcelona --start 2000-01-01 --end 2100-12-31 --out docs/data/bcn-full.ics
```

## Rebuilding the data

Only needed if the source PDF changes or you want to re-verify the
extraction. Requires `pymupdf` (`pip install pymupdf`).

```bash
python scripts/extract_spans.py    # PDF -> raw_spans.json  (day digits, colour + position)
python scripts/extract_labels.py   # PDF -> label_tokens.json (month labels, char resolution)
python scripts/build_calendar.py   # both -> nasi_days.json + validation_report.txt
python scripts/generate_ics.py --start 2000-01-01 --end 2100-12-31 --out data/nasi-calendar-full.ics
```

### How names are assigned (and why it's checkable)

Month **boundaries** come from the red digit resets. Month **names** come from
the chart's own printed label for that run — not from walking a cycle out of a
seed. Every one of the 12 months is labelled in the source, but PyMuPDF merges
adjacent labels from different month columns into single spans like
`'صفر1صفر2ر1ر2ج1ج2'`, so `extract_labels.py` reads `rawdict` and splits them
back apart *spatially* (characters of one label sit within ~2pt; separate
labels are a month column apart).

That yields 1,250 labels for 1,251 runs. The build then:

- names each run from its own label, and **asserts** the result follows the
  12-month cycle (`CYCLE CONFLICTS` must be 0);
- checks every Nasi' insertion falls after Dhul-Hijjah, Sha'ban, or Rabi'
  al-Thani — the book's 13-9-5 scheme, p.14;
- takes Hijri **year** numbers from the chart's own per-row year label and
  asserts they advance by exactly 1 (`YEAR-LABEL CONFLICTS` must be 0);
- reports how many runs it had to infer rather than read (should be 1 — the
  table opens part-way through Dhul-Qi'dah, so its first run carries no label).

A clean report reads: 36,890 days, 0 gaps, 1,250 named / 1 inferred, 0 unmatched
labels, 0 conflicts, 37 Nasi' insertions, and only 2 month runs outside 29/30
days (the deliberately truncated first and last).

## Verified against the source

Six dates read off the chart's own day cells by hand. `build_calendar.py`
asserts all six on every run and prints them at the end of the report:

| | Chart | This data |
|---|---|---|
| Ramadan 1404 day 1 | 23 Sep 2025 | 23 Sep 2025 ✓ |
| Ramadan 1405 day 1 | 12 Oct 2026 | 12 Oct 2026 ✓ |
| Nasi' 1405 day 1 | 13 Sep 2026 | 13 Sep 2026 ✓ |
| Ramadan 1409 day 1 | 27 Sep 2030 | 27 Sep 2030 ✓ |
| Dhul-Hijjah 1408 day 1 | 5 Jan 2030 | 5 Jan 2030 ✓ |
| Safar al-Awwal 1409 day 1 | 3 Feb 2030 | 3 Feb 2030 ✓ |

## Verified against real astronomy

`scripts/verify_astronomy.py` tests the finished calendar against the sky
rather than against the book. Moon-phase instants come from Meeus,
*Astronomical Algorithms* 2nd ed. ch.49 (accurate to seconds — many orders
finer than the one-day resolution being tested). Run it with:

```bash
python scripts/verify_astronomy.py
```

| Test | Result |
|---|---|
| 1,250 month starts vs. real new moons | 100% land 0 to +3 days after conjunction; 99.9% within 0–+2; mode +1 day. **Never negative.** |
| 1,249 full moons vs. day of month | 94.6% on day 14–15; **100% on day 13–16** |
| 230 NASA catalogued lunar eclipses | **99.6% on day 14–15**; 100% on day 13–16 |
| Hijri year opening, across 101 years | confined to a 28-day window (16 Jan – 13 Feb) |
| Mean month length (emergent) | 29.530024 d vs. true synodic 29.530589 d — **49 s/month** |
| Mean year length (emergent) | 365.290 d vs. tropical 365.24219 d — +69 min/yr |
| Nasi' insertion rate | 37 in 101 years = 0.3663/yr (Metonic ideal 7/19 = 0.3684) |

**What this establishes.** The months track actual lunations, not an
idealised 29.5-day cycle — the mean month is right to 49 seconds, and no
month ever begins before its own new moon. The one-sided 0/+1/+2 distribution
is the signature of a crescent-visibility (hilāl) calendar: the conjunction is
invisible, the crescent appears roughly a day later. The Nasi' intercalation
genuinely locks the lunar year to the solar one — a pure 12-month lunar year
drifts ~10.9 days/yr (~1,100 days across this table); this one drifts **4.8
days per century**.

**What it does not establish.** Two honest caveats:

- *Test 3 is partly circular.* The book states (p.15) it used this same NASA
  catalog to decide 29- vs 30-day months, so eclipse agreement partly re-checks
  the author's own method. It is not worthless — eclipses occur ~2–3×/year
  against 12 months/year, so most month lengths were never set by one — but
  the new-moon test is the independent result, because it covers all 1,250
  months and could not have been fitted from eclipses.
- *None of this addresses history.* These tests show the calendar is a sound
  lunisolar system for 2000–2100. Whether this is the scheme actually used in
  pre-Islamic Arabia, and whether the year numbering (1379–1479) is correctly
  anchored to a historical epoch, are separate questions that astronomy cannot
  settle.

## Known caveats

**The book's prose contradicts the book's own table (resolved — not our bug).**
Page 105 states: *"Tuesday 5 Jumada al-Ula 1428, corresponding to Tuesday
5 June 2007 — and per the corrected calendar, Tuesday 5 Jumada al-Ula 1386."*
This data says 5 June 2007 = **20** Jumada al-Ula 1386.

The appendix table settles it in our favour: in the June 2007 block, black `5`
sits above red `20`, and the `ج2` band does not begin until 15 June. So the
chart itself reads 20 Jumada al-Ula — the prose is what disagrees with it.

The likely slip: the day-of-month should be near-identical in the standard and
corrected calendars (both track the same moon; the correction re-labels whole
*months*, not days within them). The author gives "the fifth" for both 1428
and 1386, where the standard Hijri date for 5 June 2007 is also around the
20th. The "5" looks like an echo of "5 June" carried into both Hijri dates.

Recorded here because an earlier version of this README cited this mismatch as
an open defect in the extraction. It is not.

**Historical note — the one-position shift.** An earlier version of this
project shifted every month name across all 101 years forward by one position,
dating Ramadan 1409 to 29 Aug 2030 where the chart plainly reads 27 Sep 2030.
Cause: `extract_labels.py` did not exist, so a span-level `text in VOCAB` test
silently dropped every merged label and left only 6 of the 12 months visible
(6 × ~101 years = a misleading "607 labels"). With half the evidence invisible,
the cycle was anchored on a hand-picked constant, and the validation report
explicitly marked the surviving labels *"informational only, not used for
correctness"* — so nothing could contradict it. **That is why names are now
read per-run and asserted.** If you ever extend this code, keep the invariant:
a label that fails to parse must raise the unmatched count, never vanish.

**The "607 labels" figure is not a cross-check.** The validation report line
`regular-month label sightings` is explicitly marked *informational only, not
used for correctness* — no label is currently verified against the derived
name. Don't read it as a passed test.
