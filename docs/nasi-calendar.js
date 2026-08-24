// Nasi' calendar conversion library.
// Data source: NASI_MONTHS (see nasi-months-data.js), reconstructed from the
// day-by-day 2000-2100 table published as an appendix to "Bara'at al-Nasi'"
// (Wisam al-Din Ishaq). Covers 2000-01-01 through 2100-12-31 only.

const NASI_RANGE = { min: NASI_MONTHS[0].start, max: (function () {
  const last = NASI_MONTHS[NASI_MONTHS.length - 1];
  const d = new Date(last.start + "T00:00:00Z");
  d.setUTCDate(d.getUTCDate() + last.len - 1);
  return d.toISOString().slice(0, 10);
})() };

function toUTCDate(isoDate) {
  return new Date(isoDate + "T00:00:00Z");
}

function fromUTCDate(d) {
  return d.toISOString().slice(0, 10);
}

function addDays(isoDate, n) {
  const d = toUTCDate(isoDate);
  d.setUTCDate(d.getUTCDate() + n);
  return fromUTCDate(d);
}

function daysBetween(a, b) {
  return Math.round((toUTCDate(b) - toUTCDate(a)) / 86400000);
}

// Binary search: the last month whose start <= isoDate.
function monthIndexForDate(isoDate) {
  let lo = 0, hi = NASI_MONTHS.length - 1, ans = -1;
  while (lo <= hi) {
    const mid = (lo + hi) >> 1;
    if (NASI_MONTHS[mid].start <= isoDate) { ans = mid; lo = mid + 1; }
    else hi = mid - 1;
  }
  return ans;
}

// Gregorian ISO date ("YYYY-MM-DD") -> { ny, nm, nd } or null if out of range.
function gregorianToNasi(isoDate) {
  if (isoDate < NASI_RANGE.min || isoDate > NASI_RANGE.max) return null;
  const idx = monthIndexForDate(isoDate);
  const m = NASI_MONTHS[idx];
  const nd = daysBetween(m.start, isoDate) + 1;
  return { ny: m.ny, nm: m.nm, nd };
}

// { ny, nm, nd } -> Gregorian ISO date, or null if that month/day doesn't exist.
function nasiToGregorian(ny, nm, nd) {
  const m = NASI_MONTHS.find((x) => x.ny === ny && x.nm === nm);
  if (!m || nd < 1 || nd > m.len) return null;
  return addDays(m.start, nd - 1);
}

// All months for one Nasi' year, in calendar order.
function monthsForYear(ny) {
  return NASI_MONTHS.filter((m) => m.ny === ny);
}

function monthByIndex(idx) {
  if (idx < 0 || idx >= NASI_MONTHS.length) return null;
  return NASI_MONTHS[idx];
}
