'use strict';
/**
 * What colour a tyre is in, the way BMW colours the tyre display: green while the pressure is in the
 * band it should be, amber when it is low, red when it is nearly flat, amber again when it is running
 * hot. The car sends bar and °C (the tokens convert for display), so the bands are in bar.
 *
 * Layout widgets ask for it instead of a fixed colour:
 *   {"type": "icon", "icon": "tyreblob", "grade": "tyre", "corner": "FL", ...}
 *   {"type": "text", "colorBy": "tyre", "corner": "RL", ...}
 * (hud.js paints the first and recolours it when the band changes, and colours the second each update.)
 *
 * The bands are one car's guess: BMW's own thresholds depend on the tyre spec the car is coded for,
 * which an app cannot read. Low at 2.0 bar is the pressure at which a run-flat starts looking
 * unhappy; 1.5 bar is BMW's own "stop now" line for most 18" to 20" fitments.
 */

const LOW = 2.0;        // bar: at or below this, a tyre is worth a look
const FLAT = 1.5;       // bar: at or below this, it is a warning
const HOT = 65;         // °C: at or above this, the tyre is running hot
const COLD = 5;         // °C: at or below this, the tyre is cold (not a fault, just not up to pressure yet)

const OK = [62, 186, 44, 255];      // green, as BMW draws a healthy tyre
const WARN = [232, 168, 48, 255];    // amber
const BAD = [226, 36, 44, 255];      // the shift red, for "stop"
const COLD_C = [104, 170, 236, 255]; // blue, for a tyre below its cold band
const NONE = [122, 132, 142, 255];   // grey, when the car sends no pressure for that corner

/** 'ok' | 'cold' | 'low' | 'flat' | 'hot' from a pressure in bar and a temperature in °C. */
function grade(p, t) {
    if (!isNum(p)) return 'unknown';
    if (p <= FLAT) return 'flat';
    if (p <= LOW) return 'low';
    if (isNum(t) && t >= HOT) return 'hot';
    if (isNum(t) && t <= COLD) return 'cold';
    return 'ok';
}

/** The colour for that grade: an RGBA array, which the theme's colour() passes through unchanged. */
function rgba(g) {
    if (g === 'unknown') return NONE;   // no reading: grey, so no corner claims to be fine
    if (g === 'flat') return BAD;
    if (g === 'low' || g === 'hot') return WARN;
    if (g === 'cold') return COLD_C;
    return OK;
}

function isNum(v) { return typeof v === 'number' && isFinite(v); }

/** grade for one corner of a car-like object with _tyre(kind, corner) (hud.js passes itself). */
function of(hud, corner) {
    return grade(hud._tyre('p', corner), hud._tyre('t', corner));
}

/** A short key for "did the band change", used to skip repaints. */
function key(hud, corner) { return of(hud, corner); }

module.exports = { LOW, FLAT, HOT, COLD, OK, WARN, BAD, COLD_C, NONE, grade, rgba, of, key };
