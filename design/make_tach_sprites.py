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
    for box, name in ((BOX, 'tach-m3-l'), (BOX_R, 'tach-m3-r')):
        im = ref.crop(box)
        w = int(round(im.width * S)); h = int(round(im.height * S))
        write(name, im.resize((w, h), Image.LANCZOS))
    print('scaled to', (w, h))

if __name__ == '__main__':
    main()
