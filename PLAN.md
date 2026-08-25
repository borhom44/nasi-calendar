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

App-only. No feed regeneration, so cheap to iterate. Highest value per unit work.

### 1.1 Replace the sun events

Drop fajr/isha and every prayer convention (`ANGLES`, `SOLAR_ANGLES`,
`convention=` parameters). Four events, one definition each:

| Event | Angle |
|---|---|
| أول الضوء — first light | −18° rising |
| الشروق — sunrise | −0.833° |
| الغروب — sunset | −0.833° |
| الظلام التام — full darkness | −18° setting |

Solar noon dropped — explicitly not wanted.

### 1.2 White nights

Above **48.56° N** (= 90 − 23.44 − 18) the sun never reaches 18° below the
horizon at midsummer, so there is no astronomical night. Measured: Berlin 69
days/yr, London 59, Paris 19, everywhere else 0.

Show *"لا يحل الظلام التام الليلة"* rather than a blank, and add the
explanation to the FAQ. This is content, not an error state.

### 1.3 Seasonal markers

The point of the Nasi' month is holding the lunar year against the solar
seasons — yet nothing on screen currently shows the seasons.

- **Solstices and equinoxes** (4/yr, computed)
- **Metonic cycle start** (every 19 years; the rule is known exactly)
- **Nasi' new year**, and the **نسيء insertions** flagged as events

### 1.4 Moonrise and moonset per city

The only genuinely location-dependent moon data. Note: the moon rises ~50 min
later each day, so **some days have no moonrise at all** — must be handled as a
real astronomical fact, not an error.

### 1.5 Optional later

Perigee/apogee (supermoon), solar eclipses (same NASA catalogue as lunar),
longest/shortest day per city.

---

## Phase 2 — Feeds

Must settle *before* cities, because cities multiply the cost of every change.

### 2.1 Prune

Cut the `-1y` and `-100y` spans; keep `-5y`. Import is dead for every span
anyway. **Do this before the link is shared widely** — once strangers subscribe,
those URLs can never be withdrawn.

### 2.2 Decide: static files or VPS?

The `.ics` files are pre-baked text. Changing how an event *looks* means
rewriting and re-uploading every file.

| | Upload per format change |
|---|---|
| 2 cities (today) | ~5 MB |
| 33 cities (static) | ~76 MB |
| 33 cities (VPS) | 0 |

**Generating on the VPS** removes stored feeds entirely: any city or raw
coordinates, instant format changes, tiny repo. Cost: the VPS must stay up,
though Google keeps its last copy so brief outages are invisible.

**Open decision.** Static is fine for 2 cities and painful for 33.

---

## Phase 3 — Cities (33)

Blocked on 2.2. Free in the app (computed client-side, ~2 KB); the cost is
entirely in the feeds.

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

---

## Open decisions

1. **VPS or static feeds** (2.2) — gates Phase 3
2. Whether English moves earlier

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
