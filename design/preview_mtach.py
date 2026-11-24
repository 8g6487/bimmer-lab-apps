"""Render MTACH to a PNG without the bench.

The bench needs build.py + a restart (~30 s); this compiles the same GLSL straight from
apps/shared/shaders.js and screenshots it with headless Chrome (~2 s), which is what makes the
redraw loop workable.

    python design/preview_mtach.py out.png [--w 440] [--h 1040] [--style 1] [--v 0.35] ...

Any --key value is forwarded to the page's query string (see the HTML header for the keys).
"""
import os, re, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
CHROME = os.environ.get('CHROME', r'C:\Program Files\Google\Chrome\Application\chrome.exe')


def main():
    args = sys.argv[1:]
    if not args:
        raise SystemExit('usage: preview_mtach.py out.png [--key value ...]')
    out, rest = args[0], args[1:]
    query = {}
    for i in range(0, len(rest) - 1, 2):
        query[rest[i].lstrip('-')] = rest[i + 1]

    src = open(os.path.join(HERE, '..', 'shared', 'shaders.js'), encoding='utf-8').read()
    m = re.search(r'const MTACH = `([\s\S]*?)`;', src)
    if not m:
        raise SystemExit('MTACH not found in shared/shaders.js')

    html = open(os.path.join(HERE, 'preview_mtach.html'), encoding='utf-8').read()
    inline = '<script>window.MTACH_SRC = ' + repr(m.group(1)).replace("'", '"', 1)[:0] + '`' + m.group(1) + '`;</script>'
    html = html.replace('<canvas id="c"></canvas>', inline + '\n<canvas id="c"></canvas>')

    fd, path = tempfile.mkstemp(suffix='.html', dir=HERE)
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        f.write(html)
    url = 'file:///' + path.replace('\\', '/').lstrip('/')
    if query:
        url += '?' + '&'.join('%s=%s' % kv for kv in query.items())
    w = query.get('w', '440'); h = query.get('h', '1040')
    subprocess.run([CHROME, '--headless=new', '--disable-gpu', '--use-angle=swiftshader',
                    '--enable-unsafe-swiftshader', '--allow-file-access-from-files',
                    '--window-size=%s,%s' % (w, h), '--virtual-time-budget=4000',
                    '--hide-scrollbars', '--screenshot=' + os.path.abspath(out), url],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    os.remove(path)
    print(out)


if __name__ == '__main__':
    main()
