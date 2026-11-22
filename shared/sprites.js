'use strict';
/**
 * Bitmaps the layouts draw, baked into hud/sprites/ as JSON (the kit's build packs hud/ as JSON only):
 *
 *   {"name","w","h","tintable", "z": base64 of zlib-compressed RGBA, straight alpha}
 *
 * A layout widget asks for one by name:
 *
 *   {"type":"sprite", "name":"car-top", "x":..,"y":..,"w":..,"h":..}          as it is
 *   {"type":"sprite", "name":"wheel", "color":"fg", "grade":"tyre", "corner":"FL"}   tinted
 *
 * The car comes from the user's reference photo (tpms1.jpg), the wheel from wheel.jpg; design/make_sprites.py
 * rebuilds both. The sprites are drawn over the top view car the cluster themes share, so one app can hand
 * its car to another by copying hud/sprites/ and listing this file in app.json "shared".
 *
 *   paint(name, w, h, colour) -> RGBA Buffer (w*h*4), or null when the name is not there
 *
 * The bitmap is resampled to the widget's box, so a layout may ask for any size; keep the aspect or it
 * stretches. A "tintable" sprite is white with an alpha mask: it takes the widget's colour (the wheel),
 * a plain one keeps its own pixels (the car).
 */
const data = require('./hud_data');
const zlib = require('zlib');

const cache = new Map();
const warned = new Set();

function load(name) {
    if (cache.has(name)) return cache.get(name);
    let meta = null;
    try { meta = data.json('sprites/' + name + '.json'); } catch (e) { meta = null; }
    if (!meta || !meta.z || !meta.w || !meta.h) {
        if (!warned.has(name)) { warned.add(name); console.warn('[sprites] no sprite "' + name + '" in hud/sprites'); }
        cache.set(name, null);
        return null;
    }
    const buf = zlib.inflateSync(Buffer.from(meta.z, 'base64'));
    if (buf.length !== meta.w * meta.h * 4) throw new Error('sprite "' + name + '": size does not match ' + meta.w + 'x' + meta.h);
    const s = { w: meta.w, h: meta.h, buf, tintable: !!meta.tintable };
    cache.set(name, s);
    return s;
}

/** The sprite as a widget-sized RGBA buffer; colour (an RGBA array) tints a "tintable" sprite. */
function paint(name, w, h, colour) {
    const s = load(name);
    if (!s || w <= 0 || h <= 0) return null;
    const out = Buffer.alloc(w * h * 4, 0);
    const tint = s.tintable && colour ? colour : null;
    for (let y = 0; y < h; y++) {
        const sy = Math.min(s.h - 1, Math.floor((y + 0.5) * s.h / h));
        for (let x = 0; x < w; x++) {
            const sx = Math.min(s.w - 1, Math.floor((x + 0.5) * s.w / w));
            const si = (sy * s.w + sx) * 4;
            const di = (y * w + x) * 4;
            const a = s.buf[si + 3];
            if (!a) continue;
            out[di + 3] = a;
            if (tint) {
                out[di] = tint[0]; out[di + 1] = tint[1]; out[di + 2] = tint[2];
            } else {
                out[di] = s.buf[si]; out[di + 1] = s.buf[si + 1]; out[di + 2] = s.buf[si + 2];
            }
        }
    }
    return out;
}

function has(name) { return !!load(name); }

module.exports = { paint, has, load };
