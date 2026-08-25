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

Two consequences, already applied to the lists below:

- **Perigee/apogee get no dot.** They occur ~26 times a year, one per
  anomalistic month. Only the supermoon and micromoon are marked (~4/yr); the
  distance is a day-panel row, every day.
- **New and full moon get no dot.** The phase icon already carries them — about
  25 marks a year removed for free.

Without those two, everything dotted lands near **70 marked days a year**, one
day in five: too busy. With them, **~20** — one every eighteen days.

**First to cut if it still reads busy:** cross-quarter days (4/yr, a seasonal
tradition rather than astronomy) and the earthshine window (wants subtle
multi-day shading, not a dot — more design work than the fact is worth).

Every item in Phase 1 is tagged with the layer it belongs to:
**[grid]** = earns a dot | **[panel]** = day detail | **[cycles]** = its own tab.

---

## Already done

- Live on an owned domain, HTTPS enforced, GitHub domain verified
- Tabbed navigation, mobile-adapted, installable to the home screen
- Feeds carry moon-phase icons; four timed sun events a day
- **Range extended 101 → 600 years** (1600–2200) via `nasi-extend.js`:
  the printed table rules 1999-12-09 → 2100-12-31; outside it dates are
  computed from a stated rule and visibly marked
- **Bug fixed:** the table's opening month had lost its day offset — 2000-01-01
  showed as day 1 of ذو القعدة instead of day 24. Cross-check now 36,890/36,890

---

## Phase 1 — Astronomy core

App-only. No feed regeneration, so cheap to iterate.

### 1.1 Replace the sun events — DONE 26 Aug 2026

Drop fajr/isha and every prayer convention (`ANGLES`, `SOLAR_ANGLES`,
`convention=` parameters). Four events, one definition each:

| Event | Angle |
|---|---|
| أول الضوء — first light | −18° rising |
| الشروق — sunrise | −0.833° |
| الغروب — sunset | −0.833° |
| الظلام التام — full darkness | −18° setting |

Solar noon dropped — explicitly not wanted.

Applied across `docs/solar.js`, `scripts/solar_times.py`, `docs/index.html`,
`scripts/generate_ics_full.py` and the FAQ. `SUN_EVENTS` is now the single
source of truth for the keys, order and Arabic labels, carried in both the JS
and the Python side so the app and the feed cannot drift. Verified: equinox day
length 12h07–12h10 rising with latitude (refraction, as expected), first light
and full darkness exactly equidistant from solar midday, white-night counts
unchanged at Berlin 69 / London 59 / Paris 19 / elsewhere 0, feed still CRLF.

### 1.2 White nights

Above **48.56° N** (= 90 − 23.44 − 18) the sun never reaches 18° below the
horizon at midsummer, so there is no astronomical night. Measured: Berlin 69
days/yr, London 59, Paris 19, everywhere else 0.

Show *"لا يحل الظلام التام الليلة"* rather than a blank, and add the
explanation to the FAQ. This is content, not an error state.

### 1.3 The cycle made visible — highest value in the whole plan

Nothing on screen currently explains *why this calendar exists*. Four small
additions do, and every one is pure arithmetic on data already loaded.

- **[cycles + month header] Position in the Metonic cycle** — a 19-segment bar
  in the tab, and a quiet "الدورة ٧ / ١٩" chip on the month header. Makes the 19-year
  rhythm legible instead of buried in code.
- **[cycles] Nasi' drift tracker** — where the Nasi' new year falls against the
  solar year, and the span it moves across over a full cycle. Holding the lunar
  year against the seasons is the entire purpose of the نسيء month; show it
  working.
- **[cycles] Three-calendar comparison** — Nasi' / Hijri / Gregorian. The Hijri
  date slides ~11 days a year and laps the solar year every ~33; the Nasi' date
  does not. One row of a table makes the argument a page of prose cannot.
- **[cycles] Metonic error, stated honestly** — 235 lunations run 2h05m longer
  than 19 tropical years, so the cycle slips a full day every ~219 years. This
  is the reason extrapolated dates are marked, and it belongs on the page.

### 1.4 Sun and Earth

- **[grid] Solstices and equinoxes** — with exact instants, not just dates
- **[grid] Perihelion and aphelion** (~3 Jan / ~4 Jul) — the Earth–Sun
  counterpart to perigee/apogee: 147.1M vs 152.1M km, ~7% difference in sunlight
- **[grid] Longest and shortest day**, per city — shares the solstice dot
- **[grid] Earliest sunset and latest sunrise** — two more dots, and the best
  fact on the page: they sit weeks away from the solstice (Cairo ~2 Dec /
  21 Dec / 10 Jan) because of the equation of time, and the gap *widens* nearer
  the equator. The equation of time appears here as the explanation, never as a
  daily figure.
- **[panel] Day length and its daily change** — "اليوم أطول بـ ٢ د ١٤ ث". Fastest at the
  equinoxes, faster the further from the equator.
- **[panel] Twilight duration** — first light to sunrise. The quantity that
  actually varies with season and latitude, and the one that goes infinite
  above 48.56°N.
- **[grid] Cross-quarter days** — the four midpoints between solstice and
  equinox. First candidate for cutting (see Display rules).

### 1.5 Moon

- **[panel] Moonrise and moonset** per city. The moon rises ~50 min later each
  day, so **some days have no moonrise at all** — an astronomical fact, not an
  error state.
- **[panel] Distance in km every day**; **[grid] a dot only for supermoon and
  micromoon**. ~356,500 vs ~406,700 km: 14% in apparent size, ~30% in
  brightness. The other ~22 perigees and apogees stay in the panel.
- **[cycles] Full moon cycle (411.78 days)** — the beat between the anomalistic
  and synodic months, i.e. when full moon and perigee coincide. This is what a
  "supermoon season" actually is.
- **[panel] Moonrise azimuth**, and **[grid]** its yearly northern/southern
  extremes — the moon's rising point swinging along the horizon.
- **[cycles] Lunar standstills** — the 18.6-year nodal precession. Last major
  2024–25, next ~2043. The longest cycle a person can watch with their own eyes.
- **[panel] Earthshine window** — the days either side of new moon when the dark
  limb is faintly lit by the Earth. Second candidate for cutting: it wants
  multi-day shading rather than a dot.

### 1.6 Eclipses — the Saros family

- **[grid] Solar and lunar eclipses** from the NASA catalogue, with type and
  magnitude
- **[panel] Saros series and member number** (223 lunations = 18y 11⅓d) —
  eclipses are not scattered, they belong to families, and saying which one
  turns a one-off event into a visible cycle
- **[cycles] Eclipse seasons** — the two ~34-day windows a year when eclipses
  are possible, 173.3 days apart (the draconic year is 346.62 days, shorter than
  the solar year, which is why the seasons creep backwards)
- **[cycles] Exeligmos** (3 Saros, 54y 33d) — the repeat that returns to nearly
  the same longitude. One line of flavour, free once Saros is in.

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

## Deployment trap found while doing 1.1 — fixed

Every script in `index.html` loads as `solar.js?v=013409cd`, where the suffix is
`md5(bytes)[:8]`. Browsers cache that exact URL, so **if a file changes and its
hash does not, a returning visitor keeps running the old code** — silently, no
error, nothing in the console. The site looks deployed and behaves as if it
never was.

The hashes were hand-maintained, and two were already stale:

- `nasi-extend.js?v=1` had never been bumped at all
- `nasi-months-data.js` still carried the pre-bug-fix hash, so **the
  1999-12-09 correction never reached anyone who had already loaded the page** —
  they were still being served the version that showed 2000-01-01 as day 1

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

## Phase 2 — Feeds, on the VPS

### 2.1 Prune

Cut the `-1y` and `-100y` spans; keep `-5y`. Import is dead for every span
anyway. **Do this before the link is shared widely** — once strangers subscribe,
those URLs can never be withdrawn.

### 2.2 Move to the personal VPS — DECIDED

Generation moves off GitHub Pages onto the personal box (186.240.155.88).

**The URL does not change.** The `nasi` record switches from a CNAME at GitHub
Pages to an A record at the VPS; `https://nasi.ibrahimabdelrahim.cloud/...`
resolves exactly as before. Nobody re-subscribes, nothing breaks, and the
dangling-CNAME takeover risk disappears with the CNAME.

| | Upload per format change |
|---|---|
| 2 cities (static) | ~5 MB |
| 33 cities (static) | ~76 MB |
| 33 cities (VPS) | 0 |

What it buys: any city or raw coordinates, instant format changes, a tiny repo,
and **access logs** — which is the answer to "how many people are using it",
a question GitHub Pages cannot answer at all.

Cost: the box has to stay up. Google keeps its last copy, so a short outage is
invisible to subscribers.

**Isolation requirements** — this is the first public service on a machine that
holds health and loan records, so the separation is part of the build, not a
follow-up:

- dedicated unix user, own directory, no read access to Personal OS data
- nginx serves that document root only — no proxy to any Personal OS port
- Personal OS stays bound to the tailnet interface (100.126.157.23), unchanged
- firewall opens 443 (and 80 for the ACME redirect) and nothing else; every
  other service stays tailnet-only
- certbot is already installed with the Hostinger DNS hook — reuse it

---

## Phase 3 — Cities (33)

Free in the app (computed client-side, ~2 KB); the cost was entirely in the
static feeds, and 2.2 removes it.

Egypt & Levant · Gulf · North Africa · Europe · Americas · Asia — list agreed.
Group the dropdown by region rather than one flat list of 33.

Each entry needs a correct IANA timezone (self-checking: `zoneinfo` throws on a
bad name). DST comes from real rules — Egypt reinstated it in 2023, so Cairo is
UTC+3 in August and UTC+2 in January.

---

## Phase 4 — English

Largest single job, and orthogonal to everything above — touches nearly every
file but blocks nothing.

Language toggle · full string table · FAQ translated (~13 KB) · month names
transliterated (صفر الأول → *Safar I*, نسيء → *Nasiʾ*) · RTL ↔ LTR switching.

Full translation, not partial — half-translated apps read as broken.

**Extract the string table now, translate later.** Every label added in Phase 1
goes into one table with the Arabic filled and the English column blank. Nothing
looks different today; translation later becomes filling a second column; and
any wording change after translation is one row edited twice, side by side,
instead of two files drifting apart. Changing content *after* translating is
fine — the risk is drift, and the table is what prevents it.

---

## Open decisions

None blocking. Phase 1 starts.

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
- **Feeds are generated on the personal VPS**, at the existing URL. Static
  hosting was rejected on upload cost and on having no access logs.
