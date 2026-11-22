#!/usr/bin/env python3
"""Generate the cluster "TPMS car" theme layout (apps/cluster_themes/hud/layouts/tpms.json).

BMW's own tyre readout, drawn from above: the top view car (a bitmap baked from the reference photo by
design/make_sprites.py) nose up in the middle, the pressure over the temperature at each corner, the wheel
and the units as the heading, thin rules between the front and rear pairs and above and below the car, and
the four tyres lit by their pressure band (shared/tyre_grade.js).

    python design/gen_tpms.py            # writes tpms.json
    python design/gen_tpms.py --font t_val --size 70 --heading t_unit

Everything is derived from the number font's cell height, so switching the font or the size rescales the
whole block the way BMW's own readout scales.
"""
import argparse
import json
import os

APP = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'apps', 'cluster_themes')
OUT = os.path.join(APP, 'hud', 'layouts')
FONT_DIR = os.path.join(APP, 'hud', 'fonts')

W, H = 1920, 720
CONTENT_H = 660                 # y 660..720 is BMW's own bottom strip
CX = 960
AXIS = None   # filled in once car_w is known; the cross hangs off the car's own centre

TOP = [236, 240, 244, 255]      # the numbers
HEAD = [150, 158, 170, 255]     # the heading: wheel, psi, °C — deliberately a step dimmer than the numbers
LINE = [108, 116, 128, 255]     # the thin rules
BG = [6, 8, 11, 255]            # the panel behind everything

# the car sprite (hud/sprites/car-photo.json): the photo's own pixels, with the tyres' boxes in the meta
with open(os.path.join(APP, 'hud', 'sprites', 'car-photo.json'), encoding='utf-8') as _f:
    _meta = json.load(_f)
SPRITE_W, SPRITE_H = _meta['w'], _meta['h']
TYRE_BOX = _meta.get('tyres') or {}          # the corners the car's own tyres were painted out of
# fractions of the sprite's box: the wells are drawn at x 2..18 and 60..76, y 17..37 and 54..74 of 78 x 104
TYRE_X = (13 / 78, 65 / 78)                     # the tyres' centres across, half on the body's edge
TYRE_Y = (27 / 104, 68 / 104)                   # front, rear
TYRE_W, TYRE_H = 21 / 78, 21 / 104              # the lit capsule, a little larger than its well


def ink(font, text):
    """Where the text's ink sits inside its cell, in px: (top, bottom). drawText puts the cell's top at the
    widget's y, so a heading whose letters sit low in the cell needs its box moved up to line up."""
    with open(os.path.join(FONT_DIR, font + '.json'), encoding='utf-8') as f:
        d = json.load(f)
    g = d['glyphs']
    ch = d['cellHeight']
    # a big atlas stacks its glyph rows, so g[c].y is an offset in the atlas, not in the cell: take the row off
    # first, else a heading measured from a second-row glyph places itself above the panel (y < 0, unusable layout)
    tops = [g[c]['y'] - (g[c]['y'] // ch) * ch for c in text if c in g and g[c]['h']]
    bots = [g[c]['y'] + g[c]['h'] - (g[c]['y'] // ch) * ch for c in text if c in g and g[c]['h']]
    return (min(tops) if tops else 0), (max(bots) if bots else ch)


def advance(font, text):
    """Width of the text in px at this face's baked advance."""
    with open(os.path.join(FONT_DIR, font + '.json'), encoding='utf-8') as f:
        g = json.load(f)['glyphs']
    return sum(g[c]['advance'] for c in text if c in g)


def metrics(font):
    with open(os.path.join(FONT_DIR, font + '.json'), encoding='utf-8') as f:
        d = json.load(f)
    g = d['glyphs']
    adv = max(g[c]['advance'] for c in '0123456789')
    return d.get('cellHeight') or d.get('height'), adv


def build(font, height, heading_font, pitch_ratio=1.45, gap_ratio=0.34):
    cell, adv = metrics(font)
    d = height or cell
    pitch = round(d * pitch_ratio)
    col_w = 2 * adv + round(d * 0.40)   # air either side of the digits
    gap = round(d * gap_ratio)

    # Proportions read off the reference (design/refs/cluster-tyres-1.webp, 585x616): row pitch p, rows at
    # 0, 1p then 2.52p, 3.52p (a bigger gap between the two groups), car 1.25p long and 0.5 of that wide,
    # its centre at 2.04p, and 0.60p of white between a column and the car's edge.
    car_len = round(1.25 * pitch)
    car_w = round(car_len * SPRITE_W / SPRITE_H)
    car_x = round(CX - car_w / 2)
    AXIS = car_x + (car_w - 1) // 2   # left edge of the 2 px stroke, so its centre lands on the car's centre

    rows = [0, pitch, round(2.52 * pitch), round(3.52 * pitch)]
    gap = round(0.52 * pitch)                  # white between the numbers and the car
    hcell, _ = metrics(heading_font)

    # the heading: the wheel, then psi over °C on two lines, as BMW stacks them. Both boxes are placed by
    # where their ink is in the cell (ink()), so the two lines sit the same distance apart whatever the font.
    psi = ink(heading_font, 'psi')
    deg = ink(heading_font, 'C')
    head_h = round((psi[1] - psi[0]) + 6 + (deg[1] - deg[0]))
    head_gap = round(0.45 * pitch)   # °C to the first row, as in the photo
    block_h = head_h + head_gap + rows[3] + d
    top = round((CONTENT_H - block_h) / 2)
    head_top = top
    r1 = top + head_h + head_gap
    block_bottom = r1 + rows[3] + d
    head_bottom = head_top + head_h

    # the rule sits on the rows' midpoint (the photo: (377.5-253)/71 = 1.75), and the car rides on the rule
    rule_y = round(r1 + (rows[1] + rows[2]) / 2 + hcell / 2)   # the ink centres of the two middle rows
    car_top = rule_y - round(car_len / 2)
    car_bottom = car_top + car_len

    left_edge = round(CX - car_w / 2 - gap)    # right edge of the left column
    right_edge = round(CX + car_w / 2 + gap)
    inner_l = left_edge - col_w
    inner_r = right_edge
    ink_l = left_edge - 2 * adv            # where the left column's ink starts
    ink_r = right_edge + 2 * adv           # where the right column's ink ends

    glyph = round(hcell * 0.95)                 # about one cap height, as the photo's tyre glyph
    head_pair = glyph + 18 + advance(heading_font, 'psi')
    glyph_x = round(CX - head_pair / 2)
    unit_x = glyph_x + glyph + 18
    glyph_y = round(head_top + (psi[0] + psi[1]) / 2 - glyph / 2)   # on the psi line, not across both

    box_w, box_h = 0.261, 0.239            # the photo's tyre well, mirrored to the four corners
    dot_w = round(box_w * car_w * 0.62)
    dot_h = round(box_h * car_len * 0.78)
    out = max(0.0, (dot_w - box_w * car_w) / 2)   # how far a capsule reaches outside the body
    clear = round(0.30 * pitch)                   # the photo's ~0.38 pitch, trimmed 5 px on your note
    stop_l = round(car_x - out - clear)           # stop outside the tyres, and with the photo's gap
    stop_r = round(car_x + car_w + out + clear)

    v_top = r1 + round(0.04 * d)   # first row's ink top                       # the first row's ink top
    v_bottom = r1 + rows[3] + round(0.95 * d)   # last row's ink bottom          # the last row's ink bottom, a touch short

    widgets = [
        # BMW's cluster is behind a dark panel here: the theme draws over its gauges, not on top of them
        {'id': 'bg', 'type': 'fill', 'z': 0, 'x': 0, 'y': 0, 'w': W, 'h': CONTENT_H, 'color': BG},

        # the rules stop outside the tyres: a hole over the body still left the line ends cutting the capsules
        {'id': 'rules-h-left', 'type': 'fill', 'z': 1,
         'x': ink_l, 'y': rule_y - 1, 'w': stop_l - ink_l, 'h': 2, 'color': LINE},
        {'id': 'rules-h-right', 'type': 'fill', 'z': 1,
         'x': stop_r, 'y': rule_y - 1, 'w': ink_r - stop_r, 'h': 2, 'color': LINE},
        # two segments, not one line with a hole: the car sprite is semi-transparent, so a line drawn behind it
        # ghosts through the bonnet and the boot
        # the top segment starts with the first row's reading, not up at the heading
        {'id': 'rules-v-top', 'type': 'fill', 'z': 1, 'x': AXIS, 'y': v_top,
         'w': 2, 'h': car_top - v_top - clear, 'color': LINE},
        {'id': 'rules-v-bottom', 'type': 'fill', 'z': 1, 'x': AXIS, 'y': car_bottom + clear,
         'w': 2, 'h': v_bottom - car_bottom - clear, 'color': LINE},

        # the car, as the reference photo draws it
        {'id': 'car', 'type': 'sprite', 'name': 'car-photo', 'z': 2,
         'x': car_x, 'y': car_top, 'w': car_w, 'h': car_len},

        # the heading: the 5-spoke wheel from wheel.jpg, then psi over °C
        {'id': 'head', 'type': 'sprite', 'name': 'wheel', 'z': 4, 'color': HEAD,
         'x': glyph_x, 'y': glyph_y, 'w': glyph, 'h': glyph},
        {'id': 'unit-pressure', 'type': 'text', 'z': 4, 'x': unit_x, 'y': head_top - psi[0],
         'w': 140, 'h': hcell, 'text': '{{u:pressure}}', 'font': heading_font, 'align': 'left', 'color': HEAD},
        {'id': 'unit-temp', 'type': 'text', 'z': 4, 'x': unit_x, 'y': head_top + (psi[1] - psi[0]) + 7 - deg[0],
         'w': 140, 'h': hcell, 'text': '{{u:temp}}', 'font': heading_font, 'align': 'left', 'color': HEAD},
    ]
    # the four tyres, exactly where the car's own tyres were painted out of the sprite (a hair larger, so the
    # capsule covers the dark patch underneath), lit by their pressure band
    box_x, box_y = 0.0, 0.182
    for corner in ('FL', 'FR', 'RL', 'RR'):
        left = corner in ('FL', 'RL')
        front = corner in ('FL', 'FR')
        cx = car_x + (box_x + box_w / 2 if left else 1 - box_x - box_w / 2) * car_w
        cy = car_top + ((box_y if front else 0.682) + box_h / 2) * car_len
        widgets.append({
            'id': 'tyre-' + corner.lower(), 'type': 'sprite', 'name': 'tyre', 'z': 3,
            'x': round(cx - dot_w / 2), 'y': round(cy - dot_h / 2),
            'w': dot_w, 'h': dot_h, 'grade': 'tyre', 'corner': corner,
        })

    order = [('pfl', 'tyreP:FL', 'left', 0, 'FL'), ('tfl', 'tyreT:FL', 'left', 1, 'FL'),
             ('prl', 'tyreP:RL', 'left', 2, 'RL'), ('trl', 'tyreT:RL', 'left', 3, 'RL'),
             ('pfr', 'tyreP:FR', 'right', 0, 'FR'), ('tfr', 'tyreT:FR', 'right', 1, 'FR'),
             ('prr', 'tyreP:RR', 'right', 2, 'RR'), ('trr', 'tyreT:RR', 'right', 3, 'RR')]
    for wid, tok, side, row, corner in order:
        w = {
            'id': wid, 'type': 'text', 'z': 4,
            'x': inner_l if side == 'left' else inner_r,
            'y': r1 + rows[row], 'w': col_w, 'h': d,
            'text': '{{%s}}' % tok, 'font': font,
            'align': 'right' if side == 'left' else 'left',
            'fit': ['t_val', 'd7_val', 'm_val'],
            'color': TOP,
        }
        if wid.startswith('p'):                 # the pressure that is out of band turns amber / red
            w['colorBy'] = 'tyre'
            w['corner'] = corner
        widgets.append(w)

    return {
        'schemaVersion': 2,
        'name': 'TPMS car',
        'theme': 'mdash',
        '_about': ("Tyre pressures and temperatures the way BMW's own tyre readout draws them: a top view "
                   "car (the bitmap from the reference photo, hud/sprites/car-top.json) nose up in the "
                   "middle, the fronts above the rears either side of it, the pressure over the temperature "
                   "at each corner, the wheel and the units as the heading, thin rules between the pairs and "
                   "above and below the car, and the four tyres lit by their pressure band (green / amber / "
                   "red). The values come from the car's tyre sensors ({{tyreP:FL}} .. {{tyreT:RR}}); the "
                   "heading follows the units setting."),
        'widgets': widgets,
    }


# BMW's own readout is set in a Helvetica-like grotesque: Barlow Medium, stroked to bold, baked as t_val
# (digits) and t_unit (the heading's lowercase and °), see tools/bake_fonts.py.
FONT, SIZE, HEADING = 't_val', None, 't_unit'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--font', default=FONT, help='number font (hud/fonts/<name>.json)')
    ap.add_argument('--size', type=int, default=SIZE, help="digit height in px (default: the font's own)")
    ap.add_argument('--heading', default=HEADING, help='font for psi / bar and °C')
    a = ap.parse_args()
    data = build(a.font, a.size, a.heading)
    with open(os.path.join(OUT, 'tpms.json'), 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
        f.write('\n')
    print('wrote tpms.json: %d widgets, %s %s' % (len(data['widgets']), a.font, a.size or 'auto'))


if __name__ == '__main__':
    main()
