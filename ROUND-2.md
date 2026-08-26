# Round 2 — collecting

**Status: COLLECTING. Nothing here is implemented.** He has more items coming;
this file is the running list until he says it is complete.

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

## Still to come

He said he has more. Nothing gets built until he says the list is closed.
