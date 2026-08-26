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

## His items

### A. A settings page or icon

Location and language move into it. Question of what else — proposals below.

### C. Should the .ics link dim for a custom location?

Yes, but there is a bigger question underneath it — see "the structural
question" below. Custom coordinates genuinely have no feed: the filename is a
city key, and a feed for arbitrary coordinates could not be regenerated from
its own URL. The Sky-tab note already says so in words.

### E. The font in "this part" is a bit big

Needs pinning down — which part. Current sizes:

| | desktop | mobile |
|---|---|---|
| sun tile time (`05:05`) | 1.05rem | 0.95rem |
| sun tile label | 0.78rem | 0.7rem |
| custom-city labels/buttons | 0.85rem | 0.85rem |
| custom-city inputs/selects | **16px** | **16px** |

**Trap:** the 16px on inputs and selects is load-bearing. Below 16px, iOS
zooms the whole page when the field takes focus — that bug was found and fixed
on 25 Aug. If the inputs are what feels big, the fix is a `@media (pointer: fine)`
override so desktop can shrink while touch keeps 16px.

### F. Merge Sky and Cycles into one tab

**Trap:** Cycles defers its most expensive work until the tab is opened —
`showTab` calls `renderCycles` in a `setTimeout` precisely because it is slow.
Merging puts that cost on every Sky open unless the cycles half stays lazy
behind a collapse or an intersection observer.

### G. "About" holds both the .ics block and the FAQ

His read: those are two unrelated things. The .ics is *the product in another
format*, so it belongs near the calendar — possibly collapsed behind a
disclosure. The FAQ is reference material and can stay in About.

---

## The structural question underneath C, A and G

**There are two city selectors.** `#citySel` on the Sky tab drives the
displayed sun and moon times; `#subCity` in the About tab drives the feed URL.
They are independent — you can view Jakarta and copy Cairo's link.

That contradicts what he asked for in Phase 3: cities "should be done in one
place and shows up the result in all other places."

If city selection becomes one global setting, then C answers itself: pick a
custom location and the subscribe link has nothing to point at, so it dims with
an explanation. And G gets easier, because the .ics block stops needing its own
picker and becomes a link plus a copy button.

**One thing to keep:** UI language and feed language are deliberately separate
and that is worth preserving. Someone reading in Arabic may want the English
feed. Verified working today. A single "language" setting must not collapse them.

---

## What else could go in settings — proposals

Grounded in what the app actually does today, not a wish list.

| Setting | Today | Note |
|---|---|---|
| **Location** | Sky tab | His. Becomes the single source — see above |
| **UI language** | header toggle | His |
| **Feed language** | About tab | Keep separate from UI language |
| **Theme** | auto only, via `prefers-color-scheme` | No manual override exists. Light / Dark / System is cheap and commonly wanted |
| **Time format** | 24h, hardcoded | 12h option. Touches the feed too, or deliberately does not |
| **Week starts on** | Sunday, via `getUTCDay()` | Saturday is normal in much of the Arab world, Monday in Europe. Touches the grid and the weekday header |
| **Numerals** | Western, deliberately | ٠١٢٣ vs 0123. **Trap:** this was a deliberate decision — `Intl` with an `ar-*` locale gives Arabic-Indic and the two would then disagree on the same screen. All-or-nothing, every formatter |
| **Converter rows** | all three always | Gregorian / official Hijri / Nasi' — let someone hide a row they never use |
| **Show computed dates** | always shown, marked | The 1600–2200 extension outside the book's table. A toggle to hide them entirely, for someone who only trusts the table |
| **Default tab** | Calendar | Minor |

My own suggestion, not from the list above: **the settings icon should show
the current city** next to it, or the location becomes invisible state that
people forget is set.

---

## Open questions

1. **Settings as a page, a panel, or a modal?** A modal keeps the tab bar at
   five items; a page makes it six.
2. **Which font felt big** — the sun tiles, the custom-location controls, or
   the whole Sky panel?
3. **Merged tab name** if Sky and Cycles combine. "Sky" covering the long
   cycles is a stretch.
4. **Does the .ics disclosure sit under the calendar on every tab, or only the
   Calendar tab?**
5. **Does one global city replace both selectors** — confirming the Phase 3
   intent — or do they stay independent on purpose?

---

## Still to come

He said he has more. Nothing gets built until he says the list is closed.
