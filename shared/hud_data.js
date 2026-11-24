'use strict';
/**
 * The app's data folder hud/ (fonts, built-in layouts). The kit's build packs it into
 * hud.pack next to this file; kit/pack.js reads the pack, or the plain folder when there
 * is none (running from apps/ on the Mac). json(rel) returns {} for a missing file.
 */
const path = require('path');

// In the built app kit/pack.js sits next to this file (dist/shared/kit/pack.js); running from apps/ on a
// desktop there is no pack, and the kit lives at ../kit, so try both before giving up. Tools (the bench, the
// preview scripts) require this module straight from the repo, which is the second case.
function loadPack() {
    var tries = ['./kit/pack', '../kit/runtime/pack'];
    for (var i = 0; i < tries.length; i++) {
        try { return require(tries[i]); } catch (e) { if (e.code !== 'MODULE_NOT_FOUND') throw e; }
    }
    throw new Error('hud_data: kit/pack.js not found next to shared/ or in ../kit');
}
module.exports = loadPack().open(path.join(__dirname, 'hud'));
