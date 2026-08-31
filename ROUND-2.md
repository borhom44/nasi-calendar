# Round 2 — collecting

**Status: FIRST BATCH BUILT AND LIVE, 26 Aug 2026.** Everything below marked
DONE is deployed. He has more items coming; this file stays the running list.

| Item | State |
|---|---|
| B1 lat/lon block always visible | **DONE** — global `[hidden]` fix |
| B2 "use my location" silent | **DONE** — errors, timeout, timezone |
| A settings modal | **DONE** — gear in header |
| B/C .ics moves to Calendar, dims for custom | **DONE** |
| E font too big | **DONE** — desktop-only override |
| F merge Sky into Cycles | **DONE** |
| G About keeps FAQ only | **DONE** |
| Extra settings rows — all five | **DONE** — he took all of them |
| `gotoMonth` clamped the grid to 2000-2100 | **DONE** — pre-existing, found while testing |
| Settings changes yanked the grid back to the picked month | **DONE** — `applyLanguage` did it too |
| Language toggle beside the gear removed | **DONE** — redundant once language moved into Settings |
| Languages named in their own language | **DONE** — `العربية` / `English` in both interfaces |
| Moon stacked on the day number | **DONE** — `inset-inline-end`, 98px clear in both directions |
| Weekday header never followed the language | **DONE** — pre-existing, found in his screenshot |
| Health check + external monitor | **DONE** — on-box repair, GitHub Actions notices |
| Feeds too busy: 9,266 events | **DONE** — one entry per day, 1,826 |
| English feed was substantially Arabic | **DONE** — found while doing the above |
| Arabic title should drop the article | **PENDING — he asked for it LATER** |
| A private rich feed for him | **PENDING — blocked on one decision** |

---

## Bugs found while checking his points

These are not preferences. They are broken now.

### B1. The latitude/longitude block is always visible

He asked for it to appear only when "Custom location" is chosen. It already
tries to: the markup carries `hidden`, and the change handler sets
`customCity.hidden = !isCustom`. **The attribute has never done anything.**

`[hidden] { display: none }` comes from the browser's own stylesheet, which a
class rule outranks — and `.custom-city { display: flex }` is a class rule.
Verified live: with Cairo selected and `hidden` set, the block still renders
62px tall.

Fix is one line — `.custom-city[hidden] { display: none; }` — but the same
trap applies to every other element toggled by `hidden` that also has a
`display` rule. Audit them all in one pass, don't patch this one.

### B2. "Use my location" fails silently

```js
if (!navigator.geolocation) return;              // silent no-op
navigator.geolocation.getCurrentPosition((pos) => { ... });   // no error callback
```

Three separate ways to look dead:
- permission denied → nothing happens, no message
- request times out → nothing happens, and there is no timeout set, so it can
  hang indefinitely
- no geolocation support → the early `return` says nothing

It probably *is* firing and being denied or hanging. Needs the error callback,
a `timeout`, and a visible message on each failure path.

It also does not set the **timezone** on success. It fills lat/lon and applies,
leaving whatever zone was selected. That defaults to the device's own zone,
which is usually right for "my location" — but is wrong the moment someone has
been looking at another city first, and wrong by whole hours, not minutes.

---

## His items — answered 26 Aug 2026

### A. Settings — **gear icon in the header, opening a modal** (proposed)

He asked what "modal" meant. The three options:

| | What it is | Cost |
|---|---|---|
| **Tab** | a sixth item in the bottom bar | Eats a tab slot; settings is not content you browse |
| **Modal** | gear in the header, opens a centred overlay over a dimmed page, closes on Esc / X / tap-outside | Conventional; costs nothing structurally |
| **Drawer** | slides in from the edge | Same as a modal with different motion |

Recommend the **modal**. Merging Sky and Cycles frees a tab slot, so a tab
*would* fit — but settings is set-and-forget, not something you browse.

**Trade-off to accept:** the language toggle is one tap today, in the header.
Moving it into settings makes it three. If that matters, the gear replaces the
toggle but language stays the first row in the modal.

### B/C. The .ics block moves to the Calendar tab — his decision

- **Calendar tab only.** Not on every tab.
- **No city or language picker there.** It follows the settings city and
  language. Both `#subCity` and `#subLang` are deleted — this is what finally
  satisfies the Phase 3 rule that a city is chosen in one place.
- A **footnote** explains that language and location come from settings.
- **When a custom lat/lon is set, the whole block dims** and shows that same
  note, because arbitrary coordinates have no feed.

### E. The font — identified

It is the **subscribe picker's selects**: `#subscribe select { font-size: 16px }`
sitting beside `.sub-label` at `0.85rem` (13.6px). The selects are ~18% larger
than every label around them, which is what reads as "big".

**Trap, again:** the 16px is the iOS zoom guard. Fix is
`@media (pointer: fine) { #subscribe select { font-size: 0.85rem } }` so desktop
shrinks and touch keeps 16px. Never lower the touch value.

Two other things in his screenshot were **already fixed and cached** — the
picker showing Arabic inside an English page, and only Cairo and Barcelona.
Live now: 33 cities, six regions, correct language. `Cache-Control: no-cache`
went on index.html the same day, so this staleness does not recur.

### F. Merged tab is called **"Cycles"** — his decision

Still lazy: Cycles defers its expensive render until the tab opens. Merged, the
cycles half must stay behind a collapse or an intersection observer or every
Sky open pays for it.

### G. About keeps the FAQ only

---

## Two objections to settle before building

### 1. "Download the calendar button" would break the core promise

He wrote "a simple download the calendar button". A **download** hands over an
`.ics` file, and opening that file **imports** it — which is the exact thing the
README, the FAQ and the on-page steps all tell people not to do. An import
copies thousands of events in once, never updates, and cannot be bulk-deleted.

Same word, opposite outcome. Proposal — one primary button that *subscribes*:

- **Google Calendar:** `https://calendar.google.com/calendar/r?cid=<encoded https URL>`
  adds it as a subscription in one click.
- **Apple Calendar / Outlook:** the same URL with the `webcal://` scheme is
  handled natively as a subscription.
- **Copy link** stays as the fallback that always works.

Wording should say *Add to my calendar*, never *Download*.

### 2. One language, or two?

He wrote "it is the same city and language in the settings" — one language
setting driving both the interface and the feed. That **contradicts** the
separation flagged earlier, which is live and working today: someone reading
the app in Arabic can currently take the English feed.

The real case for two: a shared or work calendar where Latin-script event
titles are wanted, read by someone who prefers the app in Arabic.

Middle option: **one setting**, and the footnote mentions that swapping `-en`
on the URL gives the other language. Keeps the capability, drops the control.
**His call.**

---

## Third and fourth batches — built 26–31 Aug 2026

Everything in the status table above marked DONE is deployed and verified. The
detail lives in the git log; the entries worth remembering are:

- The `[hidden]` attribute never worked anywhere, because `[hidden]{display:none}`
  is a UA-stylesheet rule that any class setting `display` outranks.
- `gotoMonth` clamped the grid to 2000–2100 while everything else advertised
  1600–2200, so no computed date was reachable from the grid at all.
- The English feed carried 1,826 Arabic summaries and 1,826 Arabic descriptions.
- `feed_server.py` documented that editing `strings.json` was enough to pick up
  a change. It was not: `strings.py` fills its table at import time, so a
  deploy could look like it had silently done nothing.

---

## Open now

### 1. Arabic title — drop the definite article (he said do it LATER)

`ui.appTitle` (ar) is **التقويم النسيء**. It should be **تقويم النسيء** —
*taqwīm al-nasīʾ*, not *al-taqwīm al-nasīʾ*. Only the second word takes the
article. `feed.calendarName` (ar) has the same shape: `التقويم النسيء — {city}`.

Both live in `data/strings.json`. The Arabic also sits as fallback text inside
`docs/index.html` in 4 places, and `build_web.py` does NOT rewrite those — miss
them and the markup disagrees with the string table.

### 2. A private rich feed for him — blocked on one decision

He wants to keep the rich version for himself, not linked publicly. That is
what `--everything` already builds. Two things to settle:

**Which sun events it carries.** He asked to drop fajr and isha as duplicating
dawn and dusk — but there is no fajr or isha anywhere in the feed. See the
section below.

**How "private" it needs to be.** `FEED_RE` in `vps/feed_server.py` matches
only `nasi-<city>-full-5y[-<lang>].ics`, so a private feed needs its own route.
An unguessable path is obscurity, not access control: anyone with the URL has
it, exactly like the public feeds. That is probably fine for this — it is a
calendar, not a secret — but it should be a decision rather than an assumption.

### What is actually around sunrise and sunset

Four events, and **no fajr or isha**. `solar_times.py` says the fajr/isha
convention table "was removed deliberately" — those labels existed before the
review pass and were renamed, which is likely why he remembers them.

| event | angle | meaning |
|---|---|---|
| `first_light` | −18.0° | astronomical twilight begins — the sky starts to lighten |
| `sunrise` | −0.833° | upper limb on the horizon (refraction + solar radius) |
| `sunset` | −0.833° | the same, descending |
| `full_dark` | −18.0° | astronomical twilight ends |

Cairo, showing how far the twilights sit from the sun itself:

| date | first light | sunrise | sunset | full dark | gap each side |
|---|---|---|---|---|---|
| 20 Mar 2026 | 04:39 | 05:58 | 18:06 | 19:25 | 80 min |
| 21 Jun 2026 | 04:17 | 05:54 | 19:59 | 21:35 | 97 min |
| 31 Aug 2026 | 05:08 | 06:31 | 19:19 | 20:41 | 83 min |
| 21 Dec 2026 | 05:21 | 06:46 | 16:59 | 18:24 | 86 min |

So nothing is redundant — the pairs are 80–97 minutes apart and describe
genuinely different moments. The real question is whether he wants two events a
day or four.
