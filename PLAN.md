# Build plan — Nasi' Calendar

Live: https://nasi.ibrahimabdelrahim.cloud
Status as of 26 Aug 2026.

---

## Principle

**This is an astronomical calendar, not a prayer-times app.** Every sun and moon
figure is derived from astronomy alone — no religious convention, no regional
variant, no angle to choose. Where the astronomy produces no answer (white
nights), that fact is *displayed*, not patched over.

---

## Display rules — locked 26 Aug 2026

The answer to "is this too much for one calendar" is **layering, not cutting**.
Three rules govern every addition below. Anything that cannot live inside them
does not ship.

1. **The grid never shows more than one dot per day.** Not a dot per event — a
   single mark meaning *something happens today*. A fully loaded month lands at
   about 5 marked days out of 31.
2. **Detail lives one tap down.** The day panel carries the sun events, day
   length and its delta, moonrise/moonset, moon distance, and the day's events.
   Worst case — the closest full moon of the year — is nine rows. An ordinary
   day is six.
3. **Nothing slow-moving belongs on a month grid.** Metonic position, the drift
   range, standstills, eclipse seasons and Saros families change once a year or
   once a decade. They live in their own **الدورات** tab.

Two consequences, applied throughout:

- **Perigee/apogee get no dot.** ~26 a year, one per anomalistic month. Only
  supermoon and micromoon are marked (~4/yr); distance is a day-panel row.
- **New and full moon get no dot.** The phase icon already carries them.

Without those two, everything dotted lands near **70 marked days a year**, one
day in five. With them, **~20** — one every eighteen days.

Layer tags used below: **[grid]** = earns a dot | **[panel]** = day detail |
**[cycles]** = its own tab.

---

## Decisions — settled 26 Aug 2026

| Question | Answer |
|---|---|
| Publishing | **Push once, at the end.** Build and verify everything, then a single push. Nothing public until then. |
| VPS | **App work now; migration when he is back at the screen.** A DNS or TLS mistake takes the live URL — and every subscriber's feed — down. Not an unattended job. |
| Cities | **33 curated, grouped by country, plus free lat/lon entry.** Computation is client-side, so arbitrary coordinates cost nothing. |
| Feeds | **Per city AND per language.** The subscribe box becomes: pick language, pick city, get the right URL to copy. |
| Translation timing | **Not deferred.** Every string is authored bilingually as it is written. Retrofitting is strictly more work than writing both columns at once. |

### The tension between two of those, and how it is handled

33 cities × 2 languages × the 5-year span is ~150 MB of `.ics`. The site-size
cap is not the issue — **git history is**: those files regenerate whenever any
wording changes, and each pass adds another ~150 MB permanently. A few passes
and the clone is over a gigabyte, which is very hard to undo. That is the same
argument Phase 5 makes for the VPS, and deferring the VPS defers what the feed
decision needs.

**Resolution:** generator and picker are fully parameterised by city and
language now; static generation is limited to Cairo and Barcelona × 2 languages;
the picker offers only cities that actually resolve, so there are never dead
links. The remaining 31 unlock the day hosting moves. **Existing Arabic feed
URLs stay byte-identical** — no current subscriber breaks.

Note: sunrise is a *city* property, not a country one (Alexandria and Aswan
differ by ~20 minutes), so feeds are per city, grouped by country in the picker.

---

## Already done

- Live on an owned domain, HTTPS enforced, GitHub domain verified
- Tabbed navigation, mobile-adapted, installable to the home screen
- Feeds carry moon-phase icons; four timed sun events a day
- **Range extended 101 → 600 years** (1600–2200) via `nasi-extend.js`: the
  printed table rules 1999-12-09 → 2100-12-31; outside it dates are computed
  from a stated rule and visibly marked
- **Bug fixed:** the table's opening month had lost its day offset — 2000-01-01
  showed as day 1 of ذو القعدة instead of day 24. Cross-check now 36,890/36,890
- **Phase 1.1 shipped** (commit `1fe80ff`) — see below

---

## Phase 0 — Foundations — DONE

**Blocks everything else.** Both items exist because the same fact is currently
stored in two places, and every later phase multiplies that cost.

### 0.1 One city registry

`CITIES` is defined **twice** today — `docs/solar.js:17` and
`scripts/generate_ics_full.py:35`. Adding a city means editing two files in two
languages and hoping the coordinates match. At 33 cities that is untenable.

One file, `data/cities.json`, is the sole source: key, names (ar + en), country
(ar + en), lat, lon, IANA timezone. The Python side reads it directly; the
browser side gets a generated `docs/cities-data.js`, emitted by the same script
that stamps asset hashes so it can never go stale.

Self-checking on build: `zoneinfo` throws on a bad IANA name, latitude and
longitude are range-checked, and keys must be unique and URL-safe — they become
feed filenames, which are permanent.

### 0.2 One string table

Every user-visible string moves into `data/strings.json` — one row, two
columns, `ar` and `en`. Nothing looks different the day it lands.

This comes **first**, not last, because from here on every label written in
Phase 1 is written in both languages at once. Retrofitting English onto strings
authored only in Arabic means reading every one back and recovering its context;
writing the pair costs almost nothing at the moment of authorship.

Shared with the generator the same way as the cities, so a feed and the screen
can never disagree about wording.

---

## Phase 1 — Astronomy core — DONE

App-only. No feed regeneration, so cheap to iterate.

### 1.1 Replace the sun events — DONE 26 Aug 2026

| Event | Angle |
|---|---|
| أول الضوء — first light | −18° rising |
| الشروق — sunrise | −0.833° |
| الغروب — sunset | −0.833° |
| الظلام التام — full darkness | −18° setting |

Dropped fajr/isha and every prayer convention (`ANGLES`, `SOLAR_ANGLES`,
`convention=`). Solar noon dropped — explicitly not wanted.

Applied across `docs/solar.js`, `scripts/solar_times.py`, `docs/index.html`,
`scripts/generate_ics_full.py`, the FAQ, the credits and the README.
`SUN_EVENTS` is the single source of truth for keys, order and labels, carried
in both the JS and Python sides. Verified: equinox day length 12h07–12h10
rising with latitude (refraction, as expected), first light and full darkness
exactly equidistant from solar midday, white-night counts unchanged at
Berlin 69 / London 59 / Paris 19 / elsewhere 0, feed still CRLF.

> Moves into `strings.json` in Phase 0 and gains its English column there.

### 1.2 White nights

Above **48.56° N** (= 90 − 23.44 − 18) the sun never reaches 18° below the
horizon at midsummer. Measured: Berlin 69 days/yr, London 59, Paris 19,
everywhere else 0.

Show *"لا يحل الظلام التام الليلة"* rather than a blank, and explain it in the
FAQ. Content, not an error state. The computation is already correct — this is
the display half.

### 1.3 The cycle made visible — highest value in the whole plan

Nothing on screen explains *why this calendar exists*. All four are arithmetic
on data already loaded.

- **[cycles + month header] Position in the Metonic cycle** — a 19-segment bar
  in the tab, and a quiet "الدورة ٧ / ١٩" chip on the month header
- **[cycles] Nasi' drift tracker** — where the Nasi' new year falls against the
  solar year, and the span it moves across over a full cycle. Holding the lunar
  year against the seasons is the entire purpose of the نسيء month; show it
  working
- **[cycles] Three-calendar comparison** — Nasi' / Hijri / Gregorian. The Hijri
  date slides ~11 days a year and laps the solar year every ~33; the Nasi' date
  does not. One table row makes the argument a page of prose cannot
- **[cycles] Metonic error, stated honestly** — 235 lunations run 2h05m longer
  than 19 tropical years, so the cycle slips a full day every ~219 years. This
  is why extrapolated dates are marked, and it belongs on the page

### 1.4 Sun and Earth

- **[grid] Solstices and equinoxes** — with exact instants, not just dates
- **[grid] Perihelion and aphelion** (~3 Jan / ~4 Jul) — the Earth–Sun
  counterpart to perigee/apogee: 147.1M vs 152.1M km, ~7% in sunlight
- **[grid] Longest and shortest day**, per city — shares the solstice dot
- **[grid] Earliest sunset and latest sunrise** — the best fact on the page:
  weeks away from the solstice (Cairo ~2 Dec / 21 Dec / 10 Jan) because of the
  equation of time, and the gap *widens* nearer the equator. The equation of
  time appears here as the explanation, never as a daily figure
- **[panel] Day length and its daily change** — "اليوم أطول بـ ٢ د ١٤ ث".
  Fastest at the equinoxes, faster the further from the equator
- **[panel] Twilight duration** — first light to sunrise; the quantity that
  actually varies with season and latitude, and the one that goes infinite
  above 48.56°N
- **[grid] Cross-quarter days** — the four solstice/equinox midpoints

### 1.5 Moon

- **[panel] Moonrise and moonset** per city. The moon rises ~50 min later each
  day, so **some days have no moonrise at all** — a fact, not an error state
- **[panel] Distance in km every day**; **[grid] a dot only for supermoon and
  micromoon**. ~356,500 vs ~406,700 km: 14% in apparent size, ~30% in brightness
- **[cycles] Full moon cycle (411.78 days)** — the beat between the anomalistic
  and synodic months, i.e. when full moon and perigee coincide. This is what a
  "supermoon season" actually is
- **[panel] Moonrise azimuth**, and **[grid]** its yearly northern/southern
  extremes — the moon's rising point swinging along the horizon
- **[cycles] Lunar standstills** — the 18.6-year nodal precession. Last major
  2024–25, next ~2043. The longest cycle a person can watch unaided
- **[panel] Earthshine window** — the days either side of new moon when the dark
  limb is faintly lit by the Earth

### 1.6 Eclipses — the Saros family

- **[grid] Solar and lunar eclipses** from the NASA catalogue, type + magnitude
- **[panel] Saros series and member number** (223 lunations = 18y 11⅓d) —
  eclipses are not scattered, they belong to families, and naming the family
  turns a one-off event into a visible cycle
- **[cycles] Eclipse seasons** — the two ~34-day windows a year when eclipses
  are possible, 173.3 days apart (the draconic year is 346.62 days, shorter than
  the solar year, which is why the seasons creep backwards)
- **[cycles] Exeligmos** (3 Saros, 54y 33d) — the repeat that returns to nearly
  the same longitude. One line of flavour, free once Saros is in

### 1.7 Nasi'-structural markers

- **[grid] Nasi' new year**, and the **نسيء insertions** flagged as events
- **[cycles] Metonic cycle start** every 19 years, and a countdown to the next
  نسيء insertion

### 1.8 Deliberately out of Phase 1 — and why

| Left out | Reason |
|---|---|
| Per-city eclipse local circumstances (is it total *here*, at what time) | Needs Besselian elements and horizon geometry — a project in itself, not a line item. Phase 1 says *an eclipse occurs, of this type, visible from this region*. |
| Daily libration and declination figures | Correct, computable, and nobody reads them. |
| Callippic (76 yr) and Hipparchic (304 yr) cycles | Refinements of the Metonic that this calendar never uses. FAQ prose, not events. |
| Moon–planet conjunctions | Outside the sun/moon/earth remit — though moon–Venus and moon–Jupiter are the most striking naked-eye sights there are. Candidate for a later toggle. |
| Heliacal rising of Sirius / Sothic cycle | A star and a different calendar, but Egyptian and beautiful. Optional extra later. |

---

## Phase 2 — Feeds: per city, per language — DONE

### 2.1 Prune the spans

Cut `-1y` and `-100y`; keep `-5y`. Import is dead for every span anyway.
**Do this before the link is shared widely** — once strangers subscribe, a URL
can never be withdrawn.

### 2.2 Parameterise the generator

Feed identity becomes `nasi-{city}-{lang}-5y.ics`, driven by the Phase 0 city
registry and string table. No wording lives in the generator any more.

**The existing two Arabic URLs must not change.** They keep their current names
byte-for-byte; the language suffix applies to new feeds only.

### 2.3 The subscribe picker

Pick language, pick city (grouped by country), get the URL to copy. Only cities
with a generated feed appear, so there are never dead links.

Keep the existing "From URL, not Import" warning — it is the single most common
way a subscriber ends up with a frozen copy instead of a live calendar.

### 2.4 What actually gets generated now

Cairo and Barcelona × 2 languages = 4 files. The other 31 cities live in the
registry and drive the app immediately; they enter the picker when hosting moves
— see the tension note above.

---

## Phase 3 — Cities — DONE

Free in the app (client-side, ~2 KB); the cost was entirely in static feeds.

- **33 curated**, grouped by country: Egypt & Levant · Gulf · North Africa ·
  Europe · Americas · Asia
- **Plus free lat/lon entry** — any location on Earth, since the computation is
  client-side. Validated and range-checked; no feed for ad-hoc coordinates

DST comes from real IANA rules, never a fixed offset — Egypt reinstated DST in
2023, so Cairo is UTC+3 in August and UTC+2 in January.

---

## Phase 4 — English — DONE

Much smaller than originally scoped, because Phase 0.2 means the table already
exists and every Phase 1 string was authored bilingually.

What is left: translating the pre-existing Arabic (the FAQ is the bulk, ~13 KB),
the language toggle, RTL ↔ LTR switching, and month-name transliteration
(صفر الأول → *Safar I*, نسيء → *Nasiʾ*).

Arabic stays the default; the choice is remembered, and `?lang=en` deep-links.
Full translation, not partial — half-translated apps read as broken.

---

## Phase 5 — VPS migration (supervised) — READY, waiting on one root paste

Deliberately last, and **not** an unattended job: DNS and TLS mistakes take the
live URL down and every subscriber's feed with it.

The `nasi` record switches from a CNAME at GitHub Pages to an A record at the
personal box (186.240.155.88). **The URL does not change** — nobody
re-subscribes, and the dangling-CNAME takeover vector disappears with the CNAME.

| | Upload per format change |
|---|---|
| 2 cities (static) | ~5 MB |
| 33 cities × 2 languages (static) | ~150 MB, and it compounds in git history |
| 33 cities × 2 languages (VPS) | 0 |

What it buys: all 33 cities × 2 languages with zero stored files, instant format
changes, a small repo, and **access logs** — the only way to answer "how many
people use this". Cost: the box has to stay up, though Google keeps its last
copy so a short outage is invisible to subscribers.

**Isolation is part of the build, not a follow-up.** This is the first public
service on a machine holding health and loan records:

- dedicated unix user, own docroot, no read access to Personal OS data
- nginx serves that docroot only — no proxy to any Personal OS port
- Personal OS stays bound to the tailnet interface (100.126.157.23), unchanged
- firewall opens 443 and 80 (ACME) and nothing else; everything else stays
  tailnet-only
- certbot is installed but has ONLY the standalone and webroot plugins — no
  DNS plugin. `vps/hostinger_dns.py` supplies DNS-01 through the Hostinger
  API instead, which is what allows the certificate to be issued *before*
  the domain points at the box, and therefore a zero-downtime cutover.
  Round-tripped against the live zone: add, verify, remove, zone unchanged.

---

## Phase 5 status

Everything that does not need root is done and tested on the box:
the app is at `/home/personal/nasi-calendar`, the feed generator runs on
`127.0.0.1:8971` with no dependencies beyond the standard library, and it
serves `nasi-cairo-full-5y.ics` byte-identically to the committed static
file with CRLF intact.

What remains is a single paste as root — see `vps/DEPLOY.md`. No standing
privilege is granted and sudo keeps its password.

---

## Deployment trap found while doing 1.1 — fixed

Every script in `index.html` loads as `solar.js?v=md5(bytes)[:8]`. Browsers
cache that exact URL, so **a changed file with a stale hash keeps serving old
code** — silently, no error, nothing in the console. The site looks deployed and
behaves as if it never was.

The hashes were hand-maintained, and two were already stale:

- `nasi-extend.js?v=1` had never been bumped at all
- `nasi-months-data.js` still carried the pre-bug-fix hash, so **the 1999-12-09
  correction never reached anyone who had already loaded the page** — they were
  still served the version that showed 2000-01-01 as day 1

Fixed by `scripts/stamp_assets.py`, which recomputes every referenced hash from
the file's own bytes. Only changed files get a new value, so a no-op run
produces no diff.

**Run it after touching anything under `docs/`, before committing:**

```
python scripts/stamp_assets.py
```

`--check` reports drift and exits 1 without writing — wire it into a pre-commit
hook when convenient.

---

## Settled — do not reopen

- **The book's table cannot be regenerated from a rule.** Three families tested
  against all 1,251 printed month starts: conjunction+offset best 61.5%;
  crescent sighting impossible (36% of months begin *before* their conjunction);
  fixed arithmetic cycle ≈ chance. Hence the marked-extrapolation approach.
- **Intercalation, by contrast, is exact**: `year mod 19` ∈ {2,4,7,10,12,15,18}
  → نسيء at position 5/13/9/5/13/13/9. Holds for all 37 insertions.
- **Sunrise/sunset need no external API.** One astronomical definition, computed
  to under a minute, offline. Verified at the equinox: London/Cairo/New York all
  give ~12h09–13m, the excess being refraction exactly as expected.
- **Feed URLs are permanent.** Existing ones are never renamed or withdrawn.
