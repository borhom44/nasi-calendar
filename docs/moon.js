/* Moon phase lookup + SVG icon rendering.
 *
 * MOON_PHASES[i] = [illumPct, ageDays] for day i, indexed by days since
 * 2000-01-01 (decoupled from nasi_days.json's own array order on purpose --
 * this data is independent astronomy, not part of the Nasi' reconstruction).
 */
const MOON_EPOCH = Date.UTC(2000, 0, 1);
const SYNODIC_MEAN = 29.530589;

function moonPhaseForISO(iso) {
  const t = Date.UTC(+iso.slice(0,4), +iso.slice(5,7)-1, +iso.slice(8,10));
  const idx = Math.round((t - MOON_EPOCH) / 86400000);
  if (idx < 0 || idx >= MOON_PHASES.length) return null;
  const [illum, age] = MOON_PHASES[idx];
  const waxing = age < SYNODIC_MEAN / 2;
  return { illum, age, waxing };
}

/* Thresholds stay here -- generate_ics_full.py copies these exact numbers so
 * the feed and the app cannot disagree about what phase a day is in. Only the
 * WORDS moved to the string table, so the boundaries are still stated once. */
const MOON_PHASE_NAMES = [
  [6,  "moon.phase.new"],
  [44, "moon.phase.crescent"],
  [56, "moon.phase.quarter"],
  [94, "moon.phase.gibbous"],
  [101,"moon.phase.full"],
];
function moonPhaseName(illum, waxing, lang) {
  const l = lang || (typeof LANG === "string" ? LANG : "ar");
  let key;
  for (const [max, k] of MOON_PHASE_NAMES) { if (illum < max) { key = k; break; } }
  const base = t(key, l);
  // New and full have no waxing/waning half to distinguish.
  if (key === "moon.phase.new" || key === "moon.phase.full") return base;
  return base + " " + t(waxing ? "moon.waxing" : "moon.waning", l);
}

/* Illuminated-region path inside a circle of radius r centred at (cx,cy).
 * k = illuminated fraction 0..1. waxing selects which limb is the fixed
 * bright semicircle (a schematic left/right convention for illustration,
 * not a claim about sky orientation, which depends on hemisphere/horizon). */
function moonPath(cx, cy, r, k, waxing) {
  const rx = Math.abs(r * (1 - 2 * k));
  const top = `${cx},${cy - r}`, bot = `${cx},${cy + r}`;
  const outerSweep = waxing ? 1 : 0;
  const innerSweep = k <= 0.5 ? (waxing ? 0 : 1) : (waxing ? 1 : 0);
  return `M${top} A${r},${r} 0 0 ${outerSweep} ${bot} A${rx},${r} 0 0 ${innerSweep} ${top} Z`;
}

function moonIconSVG(illumPct, waxing, size, darkColor, lightColor) {
  const r = size / 2 - 1, cx = size / 2, cy = size / 2;
  const k = illumPct / 100;
  const bright = (illumPct <= 1) ? "" :
    (illumPct >= 99)
      ? `<circle cx="${cx}" cy="${cy}" r="${r}" fill="${lightColor}"/>`
      : `<path d="${moonPath(cx, cy, r, k, waxing)}" fill="${lightColor}"/>`;
  return `<svg width="${size}" height="${size}" viewBox="0 0 ${size} ${size}">` +
    `<circle cx="${cx}" cy="${cy}" r="${r}" fill="${darkColor}" stroke="${darkColor}"/>` +
    bright +
    `<circle cx="${cx}" cy="${cy}" r="${r}" fill="none" stroke="var(--line)" stroke-width="0.75"/>` +
    `</svg>`;
}
