#!/usr/bin/env python3
"""Shift a group of widgets in one layout file.

    python design/move_block.py tp- --dx 12 --dy 10
    python design/move_block.py tp- --dx -92 --dy -34 --layout mtpms --dry-run

`prefix` matches `id.startswith(...)`, so `tp-` moves the whole TPMS block and
`tp-unit` would move only the unit labels (handy for fine nudges). Coordinates
are panel px; positive dx is right, positive dy is down.
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
APP = os.path.join(HERE, '..', 'apps', 'cluster_themes')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('prefix', help="id prefix, e.g. tp-")
    ap.add_argument('--dx', type=float, default=0)
    ap.add_argument('--dy', type=float, default=0)
    ap.add_argument('--layout', default='mtpms')
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()

    path = os.path.join(APP, 'hud', 'layouts', a.layout + '.json')
    d = json.load(open(path, encoding='utf-8'))
    hit = [w for w in d['widgets'] if str(w.get('id', '')).startswith(a.prefix)]
    if not hit:
        sys.exit('no widget id starts with %r in %s' % (a.prefix, a.layout))

    for w in hit:
        w['x'] = int(round(w['x'] + a.dx))
        w['y'] = int(round(w['y'] + a.dy))

    xs = [w['x'] for w in hit]
    ys = [w['y'] for w in hit]
    x1 = max(w['x'] + w['w'] for w in hit)
    y1 = max(w['y'] + w['h'] for w in hit)
    print('%s: %d widgets → x %d..%d, y %d..%d' % (a.layout, len(hit), min(xs), x1, min(ys), y1))

    if a.dry_run:
        return
    json.dump(d, open(path, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print('wrote', os.path.relpath(path, APP))


if __name__ == '__main__':
    main()
