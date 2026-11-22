'use strict';
/**
 * Small line icons, drawn here (no image files): straight RGBA for an image layer, w x h, in one colour.
 * Each icon is a distance function in a 0..1 box; coverage is anti-aliased over one pixel.
 *   gauge (engine), shock (chassis), wheel (steering), cog (gearbox), stack (the gear's shift program
 *   lines), therm (coolant), oilcan (oil), fuel (pump), tyre (a wheel seen from the side: ring, hub, tread notches).
 */
function seg(px, py, ax, ay, bx, by) {
    const pax = px - ax, pay = py - ay, bax = bx - ax, bay = by - ay;
    const h = Math.max(0, Math.min(1, (pax * bax + pay * bay) / (bax * bax + bay * bay)));
    return Math.hypot(pax - bax * h, pay - bay * h);
}
const ring = (px, py, cx, cy, r) => Math.abs(Math.hypot(px - cx, py - cy) - r);
const disc = (px, py, cx, cy, r) => Math.hypot(px - cx, py - cy) - r;
function arc(px, py, cx, cy, r, a0, a1) {          // clockwise from 12 o'clock, radians, a0 < a1
    let a = Math.atan2(px - cx, -(py - cy)); if (a < a0) a += Math.PI * 2;
    if (a <= a1) return Math.abs(Math.hypot(px - cx, py - cy) - r);
    const e = (b) => Math.hypot(px - (cx + r * Math.sin(b)), py - (cy - r * Math.cos(b)));
    return Math.min(e(a0), e(a1));
}

/** Distance (in box units) from (x, y) to the icon's ink; < 0 or < stroke half-width = ink. */
const rbox = (px, py, cx, cy, hw, hh, r) => { const qx = Math.abs(px - cx) - (hw - r), qy = Math.abs(py - cy) - (hh - r);
    return Math.hypot(Math.max(qx, 0), Math.max(qy, 0)) + Math.min(Math.max(qx, qy), 0) - r; };
const ICONS = {
    gauge: (x, y) => Math.min(arc(x, y, 0.5, 0.55, 0.36, -0.75 * Math.PI, 0.75 * Math.PI) - 0.045, seg(x, y, 0.5, 0.55, 0.7, 0.36) - 0.045, disc(x, y, 0.5, 0.55, 0.07)),
    shock: (x, y) => Math.min(seg(x, y, 0.24, 0.78, 0.5, 0.52) - 0.11, seg(x, y, 0.5, 0.52, 0.78, 0.24) - 0.035, seg(x, y, 0.14, 0.88, 0.2, 0.82) - 0.05, seg(x, y, 0.8, 0.22, 0.86, 0.16) - 0.05),
    wheel: (x, y) => Math.min(ring(x, y, 0.5, 0.5, 0.38) - 0.055, disc(x, y, 0.5, 0.55, 0.1), seg(x, y, 0.14, 0.5, 0.42, 0.55) - 0.05, seg(x, y, 0.58, 0.55, 0.86, 0.5) - 0.05, seg(x, y, 0.5, 0.62, 0.5, 0.86) - 0.05),
    cog: (x, y) => {
        let d = Math.min(ring(x, y, 0.5, 0.5, 0.27) - 0.06, ring(x, y, 0.5, 0.5, 0.1) - 0.04);
        for (let i = 0; i < 8; i++) { const a = i * Math.PI / 4; d = Math.min(d, seg(x, y, 0.5 + 0.3 * Math.sin(a), 0.5 - 0.3 * Math.cos(a), 0.5 + 0.42 * Math.sin(a), 0.5 - 0.42 * Math.cos(a)) - 0.06); }
        return d;
    },
    stack: (x, y) => Math.min(seg(x, y, 0.1, 0.22, 0.62, 0.22) - 0.055, seg(x, y, 0.1, 0.5, 0.78, 0.5) - 0.06, seg(x, y, 0.1, 0.8, 0.92, 0.8) - 0.075),
    therm: (x, y) => Math.min(seg(x, y, 0.42, 0.14, 0.42, 0.6) - 0.07, disc(x, y, 0.42, 0.74, 0.14), seg(x, y, 0.6, 0.24, 0.76, 0.24) - 0.035, seg(x, y, 0.6, 0.4, 0.76, 0.4) - 0.035),
    fuel: (x, y) => Math.min(Math.max(Math.abs(x - 0.38) - 0.18, Math.abs(y - 0.55) - 0.33, -Math.max(Math.abs(x - 0.38) - 0.1, Math.abs(y - 0.36) - 0.08)), seg(x, y, 0.12, 0.9, 0.64, 0.9) - 0.04, seg(x, y, 0.56, 0.36, 0.76, 0.48) - 0.04, seg(x, y, 0.76, 0.48, 0.76, 0.78) - 0.04, seg(x, y, 0.76, 0.78, 0.66, 0.84) - 0.04),
    tyre: (x, y) => {
        let d = Math.min(ring(x, y, 0.5, 0.5, 0.4) - 0.075, ring(x, y, 0.5, 0.5, 0.17) - 0.04);
        for (let i = 0; i < 8; i++) { const a = i * Math.PI / 4 + Math.PI / 8; d = Math.min(d, seg(x, y, 0.5 + 0.42 * Math.sin(a), 0.5 - 0.42 * Math.cos(a), 0.5 + 0.49 * Math.sin(a), 0.5 - 0.49 * Math.cos(a)) - 0.04); }
        return d;
    },
    // Body outline auto-sampled from the reference photo, window band cut out.
    car: (x, y) => {
        const pts = [[0.542,-0.44],[0.608,-0.364],[0.588,-0.281],[0.556,-0.199],[0.614,0.048],[0.622,0.13],[0.622,0.212],[0.559,0.294],[0.55,0.377],[0.415,0.459],[0.562,0.535],[0.553,0.617],[0.513,1.029],[0.513,1.111],[0.513,1.193],[0.513,1.276],[0.513,1.358],[0.51,1.44],[0.49,1.358],[0.49,1.276],[0.49,1.193],[0.493,1.111],[0.49,1.029],[0.453,0.617],[0.444,0.535],[0.381,0.459],[0.378,0.377],[0.447,0.294],[0.386,0.212],[0.386,0.13],[0.395,0.048],[0.458,-0.199],[0.441,-0.281],[0.401,-0.364],[0.464,-0.44]];
        let d = 1e9, inside = false;
        for (let i = 0, j = pts.length - 1; i < pts.length; j = i++) {
            const [xi, yi] = pts[i], [xj, yj] = pts[j];
            d = Math.min(d, seg(x, y, xi, yi, xj, yj));
            if ((yi > y) !== (yj > y) && x < (xj - xi) * (y - yi) / (yj - yi) + xi) inside = !inside;
        }
        const band = rbox(x, y, 0.5, 0.500, 0.26, 0.070, 0.020);
        return Math.max(inside ? -d : d, -band);
    },
    tyredot: (x, y) => Math.min(Math.abs(Math.hypot(x - 0.5, y - 0.5) - 0.30) - 0.115,
                                Math.hypot(x - 0.5, y - 0.5) - 0.085),
    oilcan: (x, y) => Math.min(seg(x, y, 0.2, 0.62, 0.6, 0.62) - 0.12, seg(x, y, 0.6, 0.58, 0.9, 0.44) - 0.04, disc(x, y, 0.92, 0.66, 0.05), seg(x, y, 0.3, 0.46, 0.3, 0.34) - 0.035, seg(x, y, 0.22, 0.34, 0.38, 0.34) - 0.04),
};

/* ---------------------------------------------------------------- TPMS (cluster "tpms" theme)
 * BMW's tyre readout, drawn from above: a top view car with its nose up in the middle, the pressure
 * over the temperature at each corner, a circled tyre and the units as the heading, thin rules.
 * The car is three rounded boxes (bonnet, cabin, boot) unioned, so it keeps a car's shoulders rather
 * than a capsule's; it fills the box (0.43 wide, 0.95 tall: about 1 : 2.2), because paintIcon() draws
 * into a min(w, h) square.
 */
const carBody = (x, y) => Math.min(
    rbox(x, y, 0.5, 0.500, 0.260, 0.296, 0.080),      // cabin and doors
    rbox(x, y, 0.5, 0.170, 0.214, 0.150, 0.076),      // bonnet
    rbox(x, y, 0.5, 0.045, 0.188, 0.046, 0.046),      // the nose
    rbox(x, y, 0.5, 0.846, 0.221, 0.140, 0.060),      // boot
    rbox(x, y, 0.5, 0.962, 0.200, 0.032, 0.030));     // the tail
const windscreen = (x, y) => rbox(x, y, 0.5, 0.295, 0.214, 0.036, 0.019);
const rearglass = (x, y) => rbox(x, y, 0.5, 0.655, 0.208, 0.032, 0.017);
const tyreAt = (cx, cy) => (x, y) => rbox(x, y, cx, cy, 0.028, 0.058, 0.015);
const mirrorAt = (cx) => (x, y) => rbox(x, y, cx, 0.330, 0.017, 0.028, 0.013);

Object.assign(ICONS, {
    // the body alone, filled: the light widget under "cartopdark"
    cartop: (x, y) => carBody(x, y),
    // the dark detail over it: the edge, the two glass bands, the four tyres, the mirrors
    cartopdark: (x, y) => Math.min(
        Math.abs(carBody(x, y)) - 0.0055,
        windscreen(x, y), rearglass(x, y),
        tyreAt(0.5 - 0.258, 0.246)(x, y), tyreAt(0.5 + 0.258, 0.246)(x, y),
        tyreAt(0.5 - 0.258, 0.676)(x, y), tyreAt(0.5 + 0.258, 0.676)(x, y),
        mirrorAt(0.5 - 0.271)(x, y), mirrorAt(0.5 + 0.271)(x, y)),
    // a single tyre, filled: the corner dots on the top view car
    tyreblob: (x, y) => rbox(x, y, 0.5, 0.5, 0.30, 0.46, 0.150),

    // the heading glyph: a tyre seen face on (rim, hub, tread notches) inside a ring
    tyrewheel: (x, y) => {
        let d = ring(x, y, 0.5, 0.5, 0.462) - 0.019;
        d = Math.min(d, ring(x, y, 0.5, 0.5, 0.300) - 0.027);
        d = Math.min(d, ring(x, y, 0.5, 0.5, 0.104) - 0.017);
        for (let i = 0; i < 8; i++) {
            const a = i * Math.PI / 4 + Math.PI / 8;
            d = Math.min(d, seg(x, y, 0.5 + 0.318 * Math.sin(a), 0.5 - 0.318 * Math.cos(a),
                0.5 + 0.372 * Math.sin(a), 0.5 - 0.372 * Math.cos(a)) - 0.019);
        }
        return d;
    },
    // the plate the readout sits on, so the numbers stay readable over the map
    plate: (x, y) => rbox(x, y, 0.5, 0.5, 0.464, 0.464, 0.100),
    // the rules: above and below the car, and either side of it between the front and rear pairs
    tpmframe: (x, y) => Math.min(
        seg(x, y, 0.5, 0.260, 0.5, 0.394) - 0.0026,
        seg(x, y, 0.5, 0.829, 0.5, 0.981) - 0.0026,
        seg(x, y, 0.029, 0.606, 0.385, 0.606) - 0.0026,
        seg(x, y, 0.615, 0.606, 0.971, 0.606) - 0.0026),
});

function paintIcon(name, w, h, color) {
    const f = ICONS[name], out = Buffer.alloc(w * h * 4, 0);
    if (!f) return out;
    const s = Math.min(w, h), ox = (w - s) / 2, oy = (h - s) / 2, aa = 1 / s;
    for (let y = 0; y < h; y++) {
        for (let x = 0; x < w; x++) {
            const d = f((x + 0.5 - ox) / s, (y + 0.5 - oy) / s);
            const a = Math.max(0, Math.min(1, 0.5 - d / aa));
            if (a <= 0) continue;
            const o = (y * w + x) * 4;
            out[o] = color[0]; out[o + 1] = color[1]; out[o + 2] = color[2]; out[o + 3] = Math.round(a * (color[3] === undefined ? 255 : color[3]));
        }
    }
    return out;
}

module.exports = { paintIcon, ICONS };
