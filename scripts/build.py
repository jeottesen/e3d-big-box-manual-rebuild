#!/usr/bin/env python3
"""Build an offline copy of the BigBox manual from ../raw into ../site.

Produces one HTML file per wiki page, an index.html, and manual.html (every page in one file).
Images missing from the archive are shown as a labelled placeholder with the original file name.
Run:  python3 -I scripts/build.py
"""
import html, json, os, re, shutil, urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.environ.get('BIGBOX_RAW', f'{ROOT}/raw')   # archive data lives outside git; override with BIGBOX_RAW
SITE = os.environ.get('BIGBOX_SITE', f'{ROOT}/docs')
os.makedirs(f'{SITE}/images', exist_ok=True)

pages = {f[:-5]: open(f'{RAW}/pages/{f}').read() for f in sorted(os.listdir(f'{RAW}/pages'))} if os.path.isdir(f'{RAW}/pages') else {}
meta = json.load(open(f'{RAW}/pages.json'))
imgs = json.load(open(f'{RAW}/images.json'))
rec_path = f'{RAW}/recovered/index.json'   # pages rebuilt from older versions of parent pages (see recover.py)
for t, info in (json.load(open(rec_path)).items() if os.path.exists(rec_path) else []):
    if info and t not in pages:
        pages[t] = open(f'{RAW}/recovered/{t}.html').read()
        meta[t] = {'snapshot': f'recovered from {info["parent"]} {info["version"]}'}
latest_titles = set()
lat_path = f'{RAW}/versions/latest.json'   # latest good (non-error) version per page, written by fetch.py
for t, v in (json.load(open(lat_path)).items() if os.path.exists(lat_path) else []):
    if v:
        latest_titles.add(t)
        pages[t] = open(f'{RAW}/versions/{t}/{v}.html').read()
        meta[t] = {'snapshot': v}
local = {t.lower(): t for t in pages}

STYLE = '''body{font:16px/1.55 system-ui,sans-serif;max-width:60rem;margin:2rem auto;padding:0 1rem;color:#222}
img{max-width:100%;height:auto}.missing{display:inline-block;border:1px dashed #999;padding:.4rem .7rem;color:#777;font-size:.85em;margin:.2rem 0}
nav a{margin-right:1rem}table{border-collapse:collapse}td,th{border:1px solid #ccc;padding:.3rem .5rem}
.src{color:#777;font-size:.8em}h1,h2,h3{line-height:1.2}'''

def slug(t): return re.sub(r'[<>:"|?*\\]', '_', re.sub(r':_', '_', urllib.parse.unquote(t).replace('/', '_')))   # safe file name on every OS: no colons

def strip_div(body, open_rx):
    """Remove every <div> matching open_rx together with its matching </div>, counting nested divs."""
    m = re.search(open_rx, body)
    while m:
        depth, end = 0, m.end()
        for t in re.finditer(r'<div\b|</div>', body[m.start():]):
            depth += 1 if t.group().startswith('<div') else -1
            if depth == 0: end = m.start() + t.end(); break
        body = body[:m.start()] + body[end:]
        m = re.search(open_rx, body)
    return body

def extract(h):
    m = re.search(r'id="mw-content-text"[^>]*>(.*?)<div class="printfooter"', h, re.S) or re.search(r'id="mw-content-text"[^>]*>(.*)', h, re.S)
    body = m.group(1)
    body = re.sub(r'<span class="mw-editsection">.*?</span></span>', '', body, flags=re.S)
    body = strip_div(body, r'<div class="warning">(?=\s*This Wiki is not looked after)')   # 2019-21 closure banner added by the wiki; noted once on the index page instead
    body = strip_div(body, r'<div id="toc"[^>]*>')   # table of contents: remove the whole balanced <div>, nothing after it
    body = re.sub(r'<!--.*?-->', '', body, flags=re.S)
    body = re.sub(r'<a [^>]*href="[^"]*?/(?:wiki/)?(?:File|Special|Media):[^"]*"[^>]*>(.*?)</a>', r'\1', body, flags=re.S)  # image-info links: keep contents only
    return body

def fix_images(body, stats):
    def thumb_file(src):
        p = urllib.parse.unquote(urllib.parse.urlparse(html.unescape(src)).path)
        m = re.match(r'/images/thumb/[^/]+/[^/]+/([^/]+)/', p)
        return m.group(1) if m else p.rsplit('/', 1)[-1]
    def repl(m):
        tag = m.group(0)
        s = re.search(r'\ssrc="([^"]+)"', tag)
        if not s: return tag
        if '/resources/' in s.group(1): return ''
        fn = thumb_file(s.group(1))
        rec = imgs.get(fn)
        if rec and rec.get('kind') and os.path.exists(f'{RAW}/images/{fn}'):
            shutil.copy(f'{RAW}/images/{fn}', f'{SITE}/images/{fn}')
            stats[rec['kind'].split('-')[0]] = stats.get(rec['kind'].split('-')[0], 0) + 1
            return f'<img src="images/{urllib.parse.quote(fn)}" alt="{html.escape(fn)}">'
        stats['missing'] = stats.get('missing', 0) + 1
        return f'<span class="missing">[image not archived: {html.escape(fn)}]</span>'
    body = re.sub(r'<a [^>]*class="image"[^>]*>\s*(<img[^>]*>)\s*</a>', r'\1', body)  # drop links to File: pages
    return re.sub(r'<img[^>]*>', repl, body)

def fix_links(body, to_anchor):
    def repl(m):
        href = html.unescape(m.group(1)); frag = ''
        if '#' in href: href, frag = href.split('#', 1); frag = '#' + frag
        m2 = re.match(r'(?:https?://wiki\.e3d-online\.com)?/(?:wiki/)?(?!images/|resources/|index\.php|web/)([^?#]+)$', href)   # /wiki/Title (2016) and /Title (2019+)
        if m2:
            t = urllib.parse.unquote(m2.group(1)).replace(' ', '_')
            if t.lower() in local:
                t = local[t.lower()]
                return f'href="{"#" + slug(t) if to_anchor else slug(t) + ".html"}{frag}"'
            return 'href="#unarchived-page"'   # the archive does not have this page: its link is removed below
        if href.startswith('/web/'): return f'href="https://web.archive.org{html.escape(href)}{frag}"'
        return m.group(0)
    body = re.sub(r'href="([^"]+)"', repl, body)
    return re.sub(r'<a\b[^>]*href="#unarchived-page"[^>]*>(.*?)</a>', r'\1', body, flags=re.S)   # plain text, not a link

os.makedirs(f'{SITE}/files', exist_ok=True)   # wiki-hosted PDF datasheets (see fetch_files.py / appendix.py)
if os.path.isdir(f'{RAW}/files'):
    for f in os.listdir(f'{RAW}/files'): shutil.copy(f'{RAW}/files/{f}', f'{SITE}/files/{f}')

TARGET = '20161018063904'
# index first, then the archived pages alphabetically, then rebuilt pages, appendix and datasheets in the order recover/appendix wrote them
rebuilt = [t for t, info in (json.load(open(rec_path)).items() if os.path.exists(rec_path) else []) if info and t in pages and t not in latest_titles]
extras = {t for t, info in (json.load(open(rec_path)).items() if os.path.exists(rec_path) else []) if info and info.get('heading') in ('appendix', 'datasheets')}
order = ['BigBox_Build_Manual'] + sorted(t for t in pages if t != 'BigBox_Build_Manual' and t not in rebuilt) + rebuilt
stats, sections = {}, []
for t in order:
    b = fix_links(fix_images(extract(pages[t]), stats), False)
    snap = meta.get(t, {}).get('snapshot', '?')
    if t in latest_titles: src = f'Archived {snap} · source: wiki.e3d-online.com/wiki/{html.escape(t)}'
    elif t in extras: src = ''   # the appendix and datasheets pages are not wiki pages
    else: src = f'Rebuilt page · source: wiki.e3d-online.com/wiki/{html.escape(t)}'   # the note under the title says where from
    head = f'<h1>{html.escape(t.replace("_", " "))}</h1>' + (f'<p class="src">{src}</p>' if src else '')
    nav = '<nav><a href="index.html">Contents</a></nav>'
    open(f'{SITE}/{slug(t)}.html', 'w').write(f'<!doctype html><meta charset="utf-8"><title>{html.escape(t)}</title><style>{STYLE}</style>{nav}{head}{b}')
    sections.append((t, fix_links(fix_images(extract(pages[t]), {}), True), head))

toc = ''.join(f'<li><a href="{slug(t)}.html">{html.escape(t.replace("_"," "))}</a></li>' for t in order)
open(f'{SITE}/index.html', 'w').write(f'<!doctype html><meta charset="utf-8"><title>BigBox Manual</title><style>{STYLE}</style><h1>BigBox 3D Printer Manual</h1><p>Offline copy compiled from the Wayback Machine capture of wiki.e3d-online.com.</p><ul>{toc}</ul><p><a href="manual.html">Everything on one page</a></p><p class="src">The original wiki showed a notice on its pages from 2019 onward saying it was no longer maintained and pointing to e3d-online.dozuki.com. That notice is left out here. The Dozuki site could not be reached when this copy was compiled, and the archived copy that was checked contained no BigBox guides.</p>')
allp = ''.join(f'<section id="{slug(t)}">{h}{b}</section><hr>' for t, b, h in sections)
open(f'{SITE}/manual.html', 'w').write(f'<!doctype html><meta charset="utf-8"><title>BigBox Manual</title><style>{STYLE}</style><h1>BigBox Manual (complete)</h1><ol>{"".join(f"<li><a href=#{slug(t)}>{html.escape(t.replace(chr(95), chr(32)))}</a></li>" for t in order)}</ol><hr>{allp}')
print(len(order), 'pages built;', 'images:', stats)
