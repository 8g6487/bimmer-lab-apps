#!/usr/bin/env python3
"""Bake the HUD's bitmap font atlases from the TTFs in tools/fonts-src/ (Barlow, Michroma, Orbitron, DSEG7, Outfit).

    UV_CACHE_DIR=... uv run --no-project --with pillow python tools/bake_fonts.py [app_id ...]

Runs on the Mac only (needs Pillow). The car never rasterizes fonts: it blits
these pre-drawn glyphs (shared/hud_text.js). Each app has its own set (FONTS below); output per
font, in apps/<app_id>/hud/fonts/<name>.json: the metrics plus the atlas as
one alpha byte per pixel (coverage), base64 in "alpha". JSON because the kit's
build packs the app's data folders into hud.pack, which holds JSON only, and
because then the car needs no PNG decoder. Barlow is SIL OFL 1.1; the licence
ships in each app's NOTICE.

Metrics: every glyph cell is the same height, from the highest ink to the lowest
ink across the font's glyph set, so a widget's y is the top of its tallest
character. `ox` shifts a cell from the pen position (ink overhang), `advance`
moves the pen. Digits get one shared advance (tabular), so a changing number
doesn't shift sideways.
"""
import base64, json, os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'fonts-src')
APPS = os.path.join(HERE, '..', 'apps')

UPPER = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
DIGITS = '0123456789'
LOWER = 'abcdefghijklmnopqrstuvwxyz'
# HUD Widgets, fitted to the part of the 800x480 HUD the driver can see (485x278 from the Nov 5 2026 grid
# photo; 560x280 since Nov 9, the sizes stayed): hero 140 -> 96, big 42 -> 34, mid 30 -> 24; label and small stay, BMW's own "mph" is that size.
# Preview faces: the bench's font picker (bench/server.js) lists everything baked for cluster_themes, so these are
# baked at a ladder of sizes — a text widget blits glyphs 1:1, so "size" really means "which baked size".
# Eurostile LT Std Demi and the four Microgramma Bold Extended cuts live in tools/fonts-src/ (eurostile*.ttf,
# microgramma-*.ttf) and are picked up automatically at the sizes below; the free stand-ins are gone.
PREVIEW_SIZES = (44, 56, 70, 88)
PREVIEW_FAMILIES = []
PREVIEW_CHARS = DIGITS + UPPER + LOWER + '.:-+°/% '

HUD_FONTS = [
    # name, file, px size, characters
    ('hero', 'BarlowSemiCondensed-SemiBold.ttf', 96, DIGITS + 'PRND-'),
    ('big', 'BarlowSemiCondensed-Medium.ttf', 34, DIGITS + ':.-° PRNDSM'),
    ('mid', 'BarlowSemiCondensed-Medium.ttf', 24, DIGITS + ':.-° ' + UPPER),
    ('label', 'Barlow-Medium.ttf', 15, UPPER + DIGITS + '/.:-°%>· '),
    ('small', 'Barlow-Medium.ttf', 13, UPPER + DIGITS + '/.:-°%>· '),
    # Retro: seven-segment digits (DSEG7 Classic, SIL OFL; the unlit 8s behind are the same font in "track")
    ('d7_hero', 'DSEG7Classic-Bold.ttf', 76, DIGITS + 'PRN-', 0, None, {'R': 'r', 'N': 'n'}),   # r and n: seven segments can't draw R or N
    ('d7_mid', 'DSEG7Classic-Bold.ttf', 26, DIGITS + '-.:'),
    # Vector: now playing (any printable ASCII: a song's text is folded to it, hud.js mediaText)
    ('np_title', 'BarlowSemiCondensed-SemiBold.ttf', 22, ''.join(chr(i) for i in range(32, 127))),
    ('np_small', 'Barlow-Medium.ttf', 16, ''.join(chr(i) for i in range(32, 127))),
]
# Cluster Themes, 1920x720 LCD. GT3: the race-dash look, Barlow Condensed.
CLUSTER_FONTS = [
    ('m_pt', 'eurostile.ttf', 24, DIGITS + '.:- '),
    ('m_pu', 'microgramma-d.ttf', 28, LOWER + UPPER + DIGITS + '°/-. '),
    ('gear', 'BarlowCondensed-Bold.ttf', 330, DIGITS + 'PRND-'),
    ('big', 'BarlowCondensed-Bold.ttf', 124, DIGITS + '.:-'),   # 124: "20.3 PSI" fits a 280 px box beside the hood; ':' for a clock in a readout slot
    ('value', 'BarlowCondensed-Bold.ttf', 92, DIGITS + '.:- PRND°', 0, None, None, '°'),   # °: a readout slot showing a temperature (tucked: the cell keeps its height)
    ('small', 'BarlowCondensed-Bold.ttf', 50, DIGITS + '.:-° '),
    ('unit', 'BarlowCondensed-SemiBold.ttf', 34, UPPER + DIGITS + '/°%>·.: -'),
    ('head', 'BarlowCondensed-SemiBold.ttf', 24, UPPER + DIGITS + '/°%>·.: -'),
    ('scale', 'BarlowCondensed-SemiBold.ttf', 30, DIGITS),
    ('badge', 'BarlowCondensed-SemiBold.ttf', 30, UPPER + LOWER + DIGITS + ' -'),   # the model badge (shared/badges.js)
    # M: the wide squared numbers (Michroma, SIL OFL) and Barlow for the small print
    ('m_num', 'Orbitron[wght].ttf', 36, DIGITS, 0, 'Black', {'0': 'O'}),
    ('m_gear', 'Orbitron[wght].ttf', 125, 'PRNDSM-' + DIGITS, 3, 'Black', {'0': 'O'}),
    ('m_speed', 'Orbitron[wght].ttf', 78, DIGITS + '-', 3, 'Black', {'0': 'O'}),
    ('m_gl', 'Orbitron[wght].ttf', 25, DIGITS + '/.-', 0, 'Black', {'0': 'O'}),
    ('m_val', 'Barlow-Medium.ttf', 54, DIGITS + ':+-.'),
    ('m_mid', 'Orbitron[wght].ttf', 34, DIGITS + ':+-.', 0, 'Bold', {'0': 'O'}),
    ('m_tyre', 'Orbitron[wght].ttf', 25, DIGITS + '.-:', 0, 'Bold', {'0': 'O'}),   # ':' for M's map-view clock (fit)
    ('m_unit', 'Barlow-Medium.ttf', 30, LOWER + UPPER + '°/-.'),
    ('m_label', 'Orbitron[wght].ttf', 20, UPPER + DIGITS + ' -/%°', 0, 'Bold'),   # digits, / % °: the M readout slots' names and units
    ('m_tiny', 'Barlow-Medium.ttf', 26, LOWER + DIGITS + 'CF./ -°'),
    ('m_badge', 'Barlow-Medium.ttf', 26, UPPER + LOWER + DIGITS + ' -'),
    # Sport: BMW Live Cockpit style, the wide numbers in Michroma like BMW's own
    ('s_scale', 'Michroma-Regular.ttf', 27, DIGITS, 1),
    ('s_speed', 'Michroma-Regular.ttf', 74, DIGITS + '-', 3),
    ('s_hero', 'Michroma-Regular.ttf', 132, DIGITS + '-', 3),   # the big speed in the middle while no map shows (Nov 13 2026)
    ('s_gear', 'Michroma-Regular.ttf', 70, DIGITS + 'PRNDSM-', 3),
    ('s_val', 'Michroma-Regular.ttf', 26, DIGITS + ':+-.', 1),
    ('s_unit', 'Barlow-Medium.ttf', 24, LOWER + UPPER + DIGITS + '°/-. '),
    ('s_label', 'BarlowSemiCondensed-SemiBold.ttf', 30, UPPER + DIGITS + ' .'),
    ('s_gl', 'Michroma-Regular.ttf', 21, DIGITS + '/', 1),
    # Vector: the music panel's song title and artist (any printable ASCII: a song's text is folded to it, hud.js
    # mediaText), the ring gauges' numbers and labels, the track time
    ('v_title', 'BarlowSemiCondensed-SemiBold.ttf', 38, ''.join(chr(i) for i in range(32, 127))),
    ('v_artist', 'Barlow-Medium.ttf', 26, ''.join(chr(i) for i in range(32, 127))),
    ('v_val', 'Michroma-Regular.ttf', 22, DIGITS + '.-+', 1),
    ('v_label', 'BarlowSemiCondensed-SemiBold.ttf', 19, UPPER + LOWER + DIGITS + ' °%/.-'),
    ('v_time', 'Michroma-Regular.ttf', 16, DIGITS + ':-', 1),
    # Minimal: one huge speed, the gear, small print
    ('n_speed', 'BarlowSemiCondensed-Medium.ttf', 260, DIGITS + '-'),
    ('n_gear', 'BarlowSemiCondensed-SemiBold.ttf', 110, DIGITS + 'PRNDSM-'),
    ('n_unit', 'Barlow-Medium.ttf', 34, LOWER + UPPER + '/'),
    # Cruise and Minimal labels (r_label: the Roadster theme's, kept when Roadster was removed in 0.17.8)
    ('r_label', 'BarlowSemiCondensed-SemiBold.ttf', 24, UPPER + LOWER + DIGITS + '/°%.: -'),
    # Drag: the 0-60 clock
    ('timer', 'BarlowCondensed-Bold.ttf', 220, DIGITS + '.-'),
    # Rally: the huge gear and the readouts in the arc
    ('y_gear', 'BarlowCondensed-Bold.ttf', 300, DIGITS + 'PRNDSM-'),
    ('y_val', 'BarlowCondensed-Bold.ttf', 76, DIGITS + '.:-+°', 0, None, None, '°'),
    # TPMS: BMW's own tyre readout is set in a Helvetica-like grotesque; Barlow Medium with a little stroke
    # round it is that weight, tabular digits and all (stroke is why the digits stay in step as they change)
    ('t_val', 'eurostile.ttf', 70, DIGITS + '.:- '),
    ('t_unit', 'microgramma-d.ttf', 44, LOWER + UPPER + DIGITS + '°/-. ' + 'barpsi', 0, None, None, '', 4,
              {'°': 0.52}),
    # Retro 80s: seven-segment digits (DSEG7 Classic, SIL OFL; the unlit 8s behind are the same font in "track")
    ('d7_big', 'DSEG7Classic-Bold.ttf', 170, DIGITS + '-'),
    ('d7_val', 'DSEG7Classic-Bold.ttf', 60, DIGITS + '-.:'),
    ('d7_sm', 'DSEG7Classic-Bold.ttf', 42, DIGITS + '-.:'),
    ('d7_gear', 'DSEG7Classic-Bold.ttf', 190, DIGITS + 'PRN-', 0, None, {'R': 'r', 'N': 'n'}),   # r and n: seven segments can't draw R or N
    # Cruise: calm, light numbers
    ('c_speed', 'BarlowSemiCondensed-Medium.ttf', 150, DIGITS + '-'),
    ('c_val', 'BarlowSemiCondensed-Medium.ttf', 62, DIGITS + '.:-+°'),
    # Ribbon: Outfit (SIL OFL), thin and calm: the huge speed, the side readouts, small spaced labels
    ('b_speed', 'Outfit[wght].ttf', 250, DIGITS + '-', 0, 'ExtraLight'),
    ('b_val', 'Outfit[wght].ttf', 44, DIGITS + '.:-+°% ' + LOWER + UPPER, 0, 'Light'),
    ('b_label', 'Outfit[wght].ttf', 20, UPPER + DIGITS + "' .-", 0, 'SemiBold'),
    ('b_unit', 'Outfit[wght].ttf', 26, UPPER + LOWER + '/', 0, 'Medium'),
    ('b_gear', 'Outfit[wght].ttf', 32, DIGITS + 'PRNDSM-', 0, 'SemiBold'),
    ('b_scale', 'Outfit[wght].ttf', 20, DIGITS, 0, 'Medium'),
]
def preview_fonts():
    """A size ladder for every face the bench may switch to: the families above, plus anything else dropped into
    tools/fonts-src/ (a commercial Eurostile or Microgramma lands here the same way)."""
    have = {f for (_n, f, _px, *_rest) in CLUSTER_FONTS}
    fams = list(PREVIEW_FAMILIES)
    seen = {f for (_k, f, _w) in fams}
    for f in sorted(os.listdir(SRC)):
        if not f.lower().endswith(('.ttf', '.otf')) or f in seen or f in have:
            continue
        key = ''.join(ch for ch in os.path.splitext(f)[0].lower() if ch.isalnum())[:16]
        fams.append((key, f, None))
    out = []
    for key, f, weight in fams:
        for px in PREVIEW_SIZES:
            out.append((key + '_' + str(px), f, px, PREVIEW_CHARS, 0, weight))
    return out


FONTS = {'idrive_hud_widgets': HUD_FONTS, 'cluster_themes': CLUSTER_FONTS + preview_fonts()}
PAD = 2
ATLAS_W = 1024


def bake(out, name, file, size, chars, stroke=0, weight=None, subs=None, tuck='', track=0, shrink=None):
    """stroke: px of extra weight round every glyph (Michroma has one weight). weight: a named instance of a
    variable font (Orbitron: Regular .. Black), for the M theme's squared BMW-style gear, speed and numbers.
    subs: {char: glyph drawn for it} (Orbitron's zero is slashed; the M8's is plain, so its O stands in).
    tuck: characters added to a font after layouts were built on its cell height (° on value / y_val, Nov 7 2026):
    they don't count towards the cell, and one that rises above it is drawn lower so its top meets the cell's."""
    font = ImageFont.truetype(os.path.join(SRC, file), size)
    if weight: font.set_variation_by_name(weight)
    subs = subs or {}
    glyph = lambda c: subs.get(c, c)
    ink = [c for c in chars if c != ' ']
    boxes = {c: font.getbbox(glyph(c), anchor='ls', stroke_width=stroke) for c in ink}
    top = min(b[1] for c, b in boxes.items() if c not in tuck)
    bottom = max(b[3] for c, b in boxes.items() if c not in tuck)
    drop = {c: max(0, top - boxes[c][1]) for c in tuck if c in boxes}
    height = bottom - top + 2 * PAD
    tab = (max(font.getlength(glyph(d)) for d in DIGITS if d in chars) + 2 * stroke) if any(d in chars for d in DIGITS) else 0

    cells = []
    for c in chars:
        adv = font.getlength(glyph(c)) + (2 * stroke if c != ' ' else 0) + (track if c != ' ' else 0)
        if c == ' ':
            cells.append((c, None, 0, round(adv if adv else size * 0.25)))
            continue
        l, _, r, _ = boxes[c]
        w = r - l + 2 * PAD
        img = Image.new('L', (w, height), 0)
        ImageDraw.Draw(img).text((PAD - l, PAD - top + drop.get(c, 0)), glyph(c), font=font, fill=255, anchor='ls', stroke_width=stroke, stroke_fill=255)
        if shrink and c in shrink:                     # a superscript °: smaller ink, top of the cell, narrower advance
            f_ = shrink[c]
            img = img.resize((max(1, round(img.width * f_)), max(1, round(img.height * f_))), Image.LANCZOS)
            canvas = Image.new('L', (w, height), 0)
            canvas.paste(img, (0, 0))
            img = canvas
            adv = round(adv * f_) + 2
        shift = (tab - adv) / 2 if c in DIGITS else 0
        cells.append((c, img, round(l - PAD + shift), round(tab if c in DIGITS else adv)))

    # simple row packing
    x = y = 0
    placed = {}
    for c, img, ox, adv in cells:
        if img is None:
            continue
        if x + img.width > ATLAS_W:
            x, y = 0, y + height
        placed[c] = (x, y)
        x += img.width
    atlas_h = y + height
    atlas = Image.new('L', (ATLAS_W, atlas_h), 0)
    glyphs = {}
    for c, img, ox, adv in cells:
        if img is None:
            glyphs[c] = {'x': 0, 'y': 0, 'w': 0, 'h': 0, 'ox': 0, 'advance': adv}
            continue
        gx, gy = placed[c]
        atlas.paste(img, (gx, gy))
        glyphs[c] = {'x': gx, 'y': gy, 'w': img.width, 'h': img.height, 'ox': ox, 'advance': adv}
    meta = {'source': file, 'size': size, 'cellHeight': height, 'baseline': PAD - top, 'glyphs': glyphs,
            'width': ATLAS_W, 'height': atlas_h, 'alpha': base64.b64encode(atlas.tobytes()).decode('ascii')}
    with open(os.path.join(out, name + '.json'), 'w', encoding='utf-8') as f:
        json.dump(meta, f, separators=(',', ':'), ensure_ascii=False)
    print('%-6s %3dpx  cell height %3d  atlas %dx%d  %d glyphs' % (name, size, height, ATLAS_W, atlas_h, len(glyphs)))


if __name__ == '__main__':
    import sys
    args = sys.argv[1:]
    face = None
    if '--face' in args:                               # --face eurostile_64: one atlas, any size the bench asks for
        i = args.index('--face'); face = args[i + 1]; del args[i:i + 2]
    for app in args or sorted(FONTS):
        out = os.path.join(APPS, app, 'hud', 'fonts')
        os.makedirs(out, exist_ok=True)
        print(app)
        if face:
            key, px = face.rsplit('_', 1)
            stem = lambda f: ''.join(ch for ch in os.path.splitext(os.path.basename(f))[0].lower()
                                     if ch.isalnum())[:16]
            faces = {}
            for sp in FONTS[app]:
                pair = (sp[1], sp[5] if len(sp) > 5 else None)
                faces.setdefault(stem(sp[1]), pair)          # `eurostile` for tools/fonts-src/eurostile.ttf
                faces.setdefault(sp[0].rsplit('_', 1)[0], pair)
            if key not in faces:
                sys.exit('no family ' + key + ' in ' + app)
            file, weight = faces[key]
            bake(out, key + '_' + px, file, int(px), PREVIEW_CHARS, 0, weight)
            continue
        for spec in FONTS[app]:
            bake(out, *spec)
