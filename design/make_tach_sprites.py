"""Bake the two tach dials from the user's reference photo into hud/sprites JSON.

The reference (design/refs/../vis/ref-m3.png) is 2930x1030; the panel is 1920x660, so the dials are scaled by
1920/2930. The right dial in the reference is a mirror of the left one, so it is flipped rather than cropped
again — that also guarantees the two match.
"""
import base64, io, json, os, zlib
from PIL import Image

REF = r'C:/Users/admin/Documents/deepseek-harness/default-workspace/vis/ref-m3.png'
OUT = os.path.join(os.path.dirname(__file__), '..', 'apps', 'cluster_themes', 'hud', 'sprites')
BOX = (780, 85, 1120, 895)          # the left dial only, reference pixels
BOX_R = (1700, 85, 2040, 895)       # the right dial: cropped, not flipped (flipping mirrors the numerals)
S = 1920.0 / 2930.0

def write(name, im):
    # the reference is a photo on black: key the background out so the theme's own backdrop stays visible
    im = im.convert('RGBA')
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, _ = px[x, y]
            m = max(r, g, b)
            if m < 26:
                px[x, y] = (r, g, b, 0)
            elif m < 46:
                px[x, y] = (r, g, b, int(255 * (m - 26) / 20))
    buf = im.tobytes()
    meta = {'name': name, 'w': im.width, 'h': im.height, 'tintable': False,
            'z': base64.b64encode(zlib.compress(buf, 9)).decode('ascii')}
    p = os.path.join(OUT, name + '.json')
    with io.open(p, 'w', encoding='utf-8', newline='') as f:
        json.dump(meta, f, separators=(',', ':'))
    print(name, im.size, len(buf), '->', os.path.getsize(p), 'bytes')

def main():
    ref = Image.open(REF)
    def defuse(im):
        im = im.convert('RGBA')
        # The reference is an idle shot: the red glow near 0 rpm is the needle, not the dial. Neutralise it
        # (keep the grey foot block) so the live marker is the only red down there.
        px = im.load()
        for y in range(int(im.height * 0.60), im.height):
            for x in range(im.width):
                r, g, b, a = px[x, y]
                if a and r > 60 and r - g > 26 and r - b > 26:
                    m = (r + g + b) // 3
                    px[x, y] = (m, m, m, a)
        return im

    BOX_GL = (240, 560, 560, 920)      # the fuel bracket, reference pixels
    BOX_GR = (2400, 560, 2720, 920)     # the oil/temperature bracket
    for box, name in ((BOX, 'tach-m3-l'), (BOX_R, 'tach-m3-r'), (BOX_GL, 'gauge-m3-l'), (BOX_GR, 'gauge-m3-r')):
        im = ref.crop(box)
        w = int(round(im.width * S)); h = int(round(im.height * S))
        im = im.resize((w, h), Image.LANCZOS)
        im = defuse(im)
        write(name, im)
    print('scaled to', (w, h))

if __name__ == '__main__':
    main()
