#!/usr/bin/env python3
"""Bake the two bitmaps the TPMS theme draws from the pictures the user supplied.

    python design/make_sprites.py

Writes, into apps/cluster_themes/hud/sprites/ (and the HUD app's copy):

  car-top.json   the top view car, taken from the user's reference photo tpms1.jpg (its own green tyre
                 lights painted out, the body turned a neutral grey, upscaled), so the theme shows the
                 car BMW drew rather than an approximation of it
  wheel.json     the 5-spoke wheel from wheel.jpg as a mask (dark = opaque), tinted with the widget colour

Format (shared/sprites.js reads it): {"w", "h", "tintable", "z": base64 of zlib-compressed RGBA}.
The kit's build packs hud/ folders as JSON only, so the bitmap rides along as JSON, like the fonts do.
"""
import base64
import json
import os
import zlib

import math
import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
SRC_CAR = os.path.join(ROOT, '..', 'tpms1.jpg')      # the user's reference photo (563x545)
SRC_WHEEL = os.path.join(ROOT, '..', 'wheel.jpg')    # the user's wheel icon (1000x1000)
SRC_REAL = os.path.join(ROOT, '..', 'cluster-tyres-1.png')   # a photo of the readout on a real car
CAR_PHOTO_BOX = (283, 331, 329, 419)                 # the car inside it, 46x89
OUT = [os.path.join(ROOT, 'apps', 'cluster_themes', 'hud', 'sprites'),
       os.path.join(ROOT, 'apps', 'idrive_hud_widgets', 'hud', 'sprites')]

# the car in tpms1.jpg, measured from its green tyre lights (x 218..232, y 296..314) plus the body
CAR_BOX = (212, 289, 240, 321)
CAR_W = 96                    # the sprite's size: the theme draws it at this size, so it is baked once


def write(name, rgba, tintable, tyres=None):
    rgba = rgba.convert('RGBA')
    w, h = rgba.size
    raw = rgba.tobytes()
    blob = base64.b64encode(zlib.compress(raw, 9)).decode('ascii')
    meta = {'name': name, 'w': w, 'h': h, 'tintable': tintable, 'z': blob}
    if tyres:
        meta['tyres'] = tyres
    for out in OUT:
        os.makedirs(out, exist_ok=True)
        with open(os.path.join(out, name + '.json'), 'w') as f:
            json.dump(meta, f, separators=(',', ':'))
    print('%-10s %3dx%-3d %6d px  %5.1f KB' % (name, w, h, w * h, len(blob) / 1024))


def car():
    """The top view car from the reference photo (tpms1.jpg), rebuilt at the size the theme draws it.

    Measured off the photo's car (23x28 px, cropped and scaled up 14x to read it) and redrawn at 10x: the
    bonnet, the roof and the boot are the bright panels, a band of dark glass runs round the roof, and the
    doors are the wide flanks between the two glass bands. Front and rear are deliberately not alike:

      * the nose tapers to a rounded point and the bonnet carries two creases,
      * the tail is square and wider, with a spoiler line across it,
      * the doors are wide, with a shut line at each end of them,
      * the tyres are big capsules that stick out past the body, as they do on the photo.
    """
    DW, DH = 78, 104              # drawn at the width the measurements below were taken at ...
    W, H = 54, 104                # ... then squeezed to about 1:1.9, like the reference
    S = 10
    img = Image.new('RGBA', (DW * S, DH * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    def box(x0, y0, x1, y1, r, fill):
        d.rounded_rectangle([x0 * S, y0 * S, x1 * S, y1 * S], radius=r * S, fill=fill)

    def poly(points, fill):
        d.polygon([(x * S, y * S) for x, y in points], fill=fill)

    BODY = (150, 156, 150, 255)
    HI = (188, 194, 188, 255)          # bonnet and boot
    CABIN = (203, 209, 203, 255)       # the cabin is the brightest panel, as in the photo
    GLASS = (30, 35, 33, 255)
    LINE = (92, 100, 95, 255)          # shut lines and bonnet creases
    WELL = (26, 31, 29, 255)           # where a tyre sits: the lit capsule is a separate widget on top

    # body: rounded nose, a waist at the doors, a tail that narrows again
    poly([(22, 0), (56, 0), (62, 7), (69, 16), (67, 30), (64, 40), (64, 62), (67, 72), (69, 88), (63, 99),
          (55, 103), (23, 103), (15, 99), (9, 88), (11, 72), (14, 62), (14, 40), (11, 30), (9, 16), (16, 7)],
         BODY)
    box(19, 0, 59, 8, 4, BODY)          # nose
    box(12, 94, 66, 104, 3, BODY)       # tail

    # panels: bonnet, the wide bright cabin, boot
    box(16, 3, 62, 18, 3, HI)           # bonnet, shorter than the cabin as in the photo
    box(16, 24, 62, 58, 4, CABIN)       # cabin, inset so the body shows either side of it
    box(16, 62, 62, 99, 3, HI)          # boot

    # two thin screens only: under the bonnet, and above the boot
    box(16, 18, 62, 24, 2, GLASS)       # windscreen, inset from the body's edges
    box(16, 58, 62, 64, 2, GLASS)       # rear screen

    # bonnet creases (front), and the shut line across the doors
    for x in (32, 46):
        d.line([(x * S, 5 * S), (x * S, 19 * S)], fill=LINE, width=max(1, S // 3))
    d.line([(13 * S, 44 * S), (17 * S, 44 * S)], fill=LINE, width=max(1, S // 3))
    d.line([(61 * S, 44 * S), (65 * S, 44 * S)], fill=LINE, width=max(1, S // 3))

    # no dark tyre wells: the lit capsules are the tyres, and a well would show as a gap round them

    img = img.resize((W, H), Image.LANCZOS)      # 78 -> 52 is the photo's own proportion
    # a soft fall-off towards the edges, the way the reference's render catches the light in the middle
    a = np.asarray(img).astype(np.float32)
    yy, xx = np.mgrid[0:H, 0:W]
    rad = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
    shade = np.clip(1.10 - 0.20 * rad ** 2, 0.88, 1.10)[:, :, None]
    a[:, :, :3] = np.clip(a[:, :, :3] * shade, 0, 255)
    img = Image.fromarray(a.round().astype(np.uint8), 'RGBA').filter(ImageFilter.GaussianBlur(0.7))
    write('car-top', img, False)



def car_from_vector():
    """Top view as separate blocks with air between them, the way the real cluster draws it.

    The two colour photos the user added (`design/refs/cluster-tyres-1.webp`, `-2.webp`) show the car at
    cluster scale: a narrow blue-grey body cut into a bonnet block, a lit roof, a boot block and two flank
    strips, with the background showing through the windscreen and the rear window, and four bright tyres
    standing outside the body.  Every part is its own shape on transparent ground, so nothing merges.
    """
    W, H = 60, 126
    S = 12
    w, h = W * S, H * S

    EDGE = (104, 110, 120)
    BONNET = (80, 86, 96)
    FLANK = (66, 72, 82)
    ROOF = (120, 126, 136)
    BOOT = (52, 58, 68)

    img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    def rr(x0, y0, x1, y1, r, fill):
        d.rounded_rectangle((x0 * S, y0 * S, x1 * S, y1 * S), radius=r * S, fill=fill)
        d.rounded_rectangle((x0 * S, y0 * S, x1 * S, y1 * S), radius=r * S, outline=EDGE + (255,), width=max(1, int(0.7 * S)))

    # bonnet: full width, its back edge stops where the windscreen gap starts
    rr(W * 0.030, H * 0.000, W * 0.970, H * 0.300, 9, BONNET + (255,))
    # flanks: two strips that run past the screens and frame the roof, with air outside them
    rr(W * 0.000, H * 0.140, W * 0.120, H * 0.880, 6, FLANK + (255,))
    rr(W * 0.880, H * 0.140, W * 1.000, H * 0.880, 6, FLANK + (255,))
    # roof: the lit block between the two screens
    rr(W * 0.205, H * 0.360, W * 0.795, H * 0.780, 6, ROOF + (255,))
    # boot: full width, shorter and darker than the bonnet
    rr(W * 0.030, H * 0.850, W * 0.970, H * 1.000, 8, BOOT + (255,))

    img = img.resize((W, H), Image.LANCZOS)
    img = img.filter(ImageFilter.GaussianBlur(0.25))
    # tyres stand outside the body: only about a fifth of each one overlaps the flank
    boxes = {'FL': [-0.045, 0.150, 0.190, 0.300], 'FR': [0.855, 0.150, 0.190, 0.300],
             'RL': [-0.045, 0.560, 0.190, 0.300], 'RR': [0.855, 0.560, 0.190, 0.300]}
    write('car-top', img, False, tyres=boxes)


def tyre():
    """One tyre, a tall capsule the theme tints green / amber / red. A sprite, not an icon: paintIcon draws
    into a square, and a tyre is not square."""
    W, H = 22, 44          # slimmer and taller than before: the reference's tyres are 9 x 21 px on a 46 x 89 car
    S = 8
    img = Image.new('RGBA', (W * S, H * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, W * S - 1, H * S - 1], radius=10 * S, fill=(255, 255, 255, 255))
    img = img.resize((W, H), Image.LANCZOS).filter(ImageFilter.GaussianBlur(0.6))
    write('tyre', img, True)


def car_from_photo():
    """The car exactly as the car itself draws it: the photo's own pixels, with the lit tyres taken out.

    `cluster-tyres-1.png` is a photo of the readout on a real car, so its car is the thing to copy, not to
    approximate. The crop is 46x89 px at native size; it is upscaled 3x with LANCZOS and stored, and the four
    tyres are repainted in a neutral dark (their colour is the app's business: green / amber / red by band).
    Their measured boxes travel in the sprite JSON so the layout puts the lit capsules back exactly on top.
    """
    src = Image.open(SRC_REAL).convert('RGB')
    box = CAR_PHOTO_BOX
    im = src.crop(box)
    W, H = im.size
    a = np.asarray(im).astype(np.float32)
    r, g, b = a[:, :, 0], a[:, :, 1], a[:, :, 2]
    luma = 0.299 * r + 0.587 * g + 0.114 * b
    green = (g > 60) & (g > r + 24) & (g > b + 24)
    # grow the mask by a pixel so the tyre's glow goes with it and no green halo survives
    gm = Image.fromarray((green * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(7))
    green = np.asarray(gm) > 0
    alpha = np.clip((luma - 12.0) / 24.0, 0, 1)
    a[:, :, :3] = np.where(green[:, :, None], np.array([44, 50, 58], np.float32), a[:, :, :3])
    a = np.dstack([a[:, :, :3], alpha * 255.0])
    out = Image.fromarray(a.round().astype(np.uint8), 'RGBA')

    ys, xs = np.nonzero(green)
    mid = (xs.min() + xs.max()) / 2
    left = xs <= mid
    rows = np.nonzero(green.any(1))[0]
    empty = [y for y in range(rows.min(), rows.max() + 1) if not green[y].any()]
    cut = empty[len(empty) // 2] if empty else (rows.min() + rows.max()) // 2
    fy0, fy1 = np.nonzero(green[:cut].any(1))[0][[0, -1]]
    ry0, ry1 = np.nonzero(green[cut:].any(1))[0][[0, -1]] + cut
    fx = lambda v: round(v / W, 4)
    fy = lambda v: round(v / H, 4)
    left_x0, left_x1 = fx(xs[left].min()), fx(xs[left].max() + 1)
    right_x0, right_x1 = fx(xs[~left].min()), fx(xs[~left].max() + 1)
    boxes = {
        'FL': [left_x0, fy(fy0), round(left_x1 - left_x0, 4), fy(fy1 + 1) - fy(fy0)],
        'FR': [right_x0, fy(fy0), round(right_x1 - right_x0, 4), fy(fy1 + 1) - fy(fy0)],
        'RL': [left_x0, fy(ry0), round(left_x1 - left_x0, 4), fy(ry1 + 1) - fy(ry0)],
        'RR': [right_x0, fy(ry0), round(right_x1 - right_x0, 4), fy(ry1 + 1) - fy(ry0)],
    }
    out = out.resize((W * 3, H * 3), Image.LANCZOS)
    # the crop is 46x89 px, so a 3x upscale is soft by construction: sharpen the colour, and make the
    # silhouette a hard edge instead of a 2 px ramp (the dash behind is black, so a soft edge reads blurry)
    rgb = out.convert('RGB').filter(ImageFilter.UnsharpMask(radius=2.0, percent=180, threshold=1))
    rgb = Image.fromarray(np.clip((np.asarray(rgb).astype(np.float32) - 128) * 1.06 + 128, 0, 255).astype(np.uint8), 'RGB')
    al = np.asarray(out.getchannel('A')).astype(np.float32) / 255.0
    al = np.clip((al - 0.18) / 0.64, 0, 1) ** 0.85
    out = rgb.convert('RGBA')
    out.putalpha(Image.fromarray((al * 255).round().astype(np.uint8)))
    write('car-photo', out, False, tyres=boxes)


def wheel():
    im = Image.open(SRC_WHEEL).convert('L')
    a = np.asarray(im).astype(np.float32) / 255
    # the icon is black on white; the stock watermark is mid grey, so only real ink becomes opaque
    alpha = np.clip((0.45 - a) / 0.30, 0, 1)
    ys, xs = np.nonzero(alpha > 0.35)
    box = (xs.min(), ys.min(), xs.max() + 1, ys.max() + 1)
    alpha = alpha[box[1]:box[3], box[0]:box[2]]
    # one sprite, white pixels, the widget colour multiplies them (tintable)
    rgb = np.ones(alpha.shape + (3,), dtype=np.float32)
    out = np.concatenate([rgb, alpha[:, :, None]], axis=2)
    img = Image.fromarray((out * 255).round().astype(np.uint8), 'RGBA')
    side = 96
    s = side / max(img.size)
    img = img.resize((max(1, round(img.width * s)), max(1, round(img.height * s))), Image.LANCZOS)
    square = Image.new('RGBA', (side, side), (255, 255, 255, 0))
    square.paste(img, ((side - img.width) // 2, (side - img.height) // 2))
    write('wheel', square, True)


if __name__ == '__main__':
    car_from_vector()
    car_from_photo()
    tyre()
    wheel()
