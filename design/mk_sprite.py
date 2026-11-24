#!/usr/bin/env python3
"""Turn a picture into a layout "sprite" widget's bitmap.

    python design/mk_sprite.py logo.png                      # -> hud/sprites/logo.json
    python design/mk_sprite.py logo.png --name brand --tintable
    python design/mk_sprite.py shot.png --box 283,331,329,419   # crop first (x0,y0,x1,y1)
    python design/mk_sprite.py logo.png --max 256 --to C:/tmp/sprites

Then use it in a layout (the editor writes the same thing):

    {"id":"my-logo","type":"sprite","name":"logo","x":880,"y":40,"w":160,"h":40,"z":6}

Format is shared/sprites.js's: {"w","h","tintable","z": base64(zlib(RGBA))}, straight alpha.
`--tintable` makes it white + alpha mask so the widget's `color` tints it (icons); otherwise the
pixels are kept as they are (photos). The bitmap is resampled to the widget's box, so keep the aspect.

After a NEW sprite, pack it into the app the bench serves:

    python kit/tools/build.py cluster_themes

(only editing a layout does not need that; the app reloads layouts by itself).
"""
import argparse
import base64
import io
import json
import os
import zlib

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
DEFAULT_TO = os.path.join(ROOT, 'apps', 'cluster_themes', 'hud', 'sprites')


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('src')
    ap.add_argument('--name', help='sprite name, default: the file name without the extension')
    ap.add_argument('--to', default=DEFAULT_TO, help='output folder (default: cluster_themes/hud/sprites)')
    ap.add_argument('--box', help='crop x0,y0,x1,y1 before baking')
    ap.add_argument('--max', type=int, default=512, help='longest side after resize (default 512)')
    ap.add_argument('--tintable', action='store_true', help='white + alpha mask, tinted by the widget colour')
    ap.add_argument('--bleed', type=float, default=0.0, help='alpha below this (0..1) becomes 0, above becomes 1')
    args = ap.parse_args(argv)

    name = args.name or os.path.splitext(os.path.basename(args.src))[0]
    im = Image.open(args.src).convert('RGBA')
    if args.box:
        im = im.crop(tuple(int(v) for v in args.box.split(',')))

    w, h = im.size
    k = min(1.0, float(args.max) / max(w, h))
    if k < 1.0:
        im = im.resize((max(1, round(w * k)), max(1, round(h * k))), Image.LANCZOS)
    w, h = im.size

    px = im.load()
    if args.tintable:
        for y in range(h):
            for x in range(w):
                r, g, b, a = px[x, y]
                px[x, y] = (255, 255, 255, a)          # keep the alpha, throw the colour away
    if args.bleed:
        t = int(round(args.bleed * 255))
        for y in range(h):
            for x in range(w):
                r, g, b, a = px[x, y]
                px[x, y] = (r, g, b, 255 if a >= t else 0)

    raw = im.tobytes()
    meta = {'w': w, 'h': h, 'tintable': bool(args.tintable),
            'z': base64.b64encode(zlib.compress(raw, 9)).decode('ascii')}

    os.makedirs(args.to, exist_ok=True)
    out = os.path.join(args.to, name + '.json')
    with io.open(out, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(meta, f, separators=(',', ':'))
    print('%s  %dx%d  %s  %.1f KB  tintable=%s' % (
        out, w, h, 'RGBA', os.path.getsize(out) / 1024.0, bool(args.tintable)))


if __name__ == '__main__':
    main()
