#!/usr/bin/env python3
"""Build an offline copy of the BigBox manual from ../raw into ../site.

Produces one HTML file per wiki page, an index.html, and manual.html (every page in one file).
Images missing from the archive are shown as a labelled placeholder with the original file name.
Run:  python3 -I scripts/build.py
"""
import filecmp, html, json, os, re, shutil, sys, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # sibling modules (python -I does not add the script folder)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.environ.get('BIGBOX_RAW', f'{ROOT}/raw')   # archive data lives outside git; override with BIGBOX_RAW
SITE = os.environ.get('BIGBOX_SITE', f'{ROOT}/docs')
os.makedirs(f'{SITE}/images', exist_ok=True)

def copy(src, dst):
    """Copy a file unless the destination already holds the same bytes, so an unchanged image keeps its modification time
    (mise decides whether the drawing extraction is out of date from the images' times)."""
    if os.path.exists(dst) and filecmp.cmp(src, dst, shallow=False): return
    shutil.copy(src, dst)

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
LINKS_PATH = os.environ.get('BIGBOX_LINKS', f'{ROOT}/notes/link-status.json')   # written by scripts/check_links.py, plus links the maintainer reported dead
link_status = json.load(open(LINKS_PATH)) if os.path.exists(LINKS_PATH) else {}

STYLE = '''body{font:16px/1.55 system-ui,sans-serif;max-width:60rem;margin:2rem auto;padding:0 1rem;color:#222}
img{max-width:100%;height:auto}.missing{display:inline-block;border:1px dashed #999;padding:.4rem .7rem;color:#777;font-size:.85em;margin:.2rem 0}
nav a{margin-right:1rem}table{border-collapse:collapse}td,th{border:1px solid #ccc;padding:.3rem .5rem}
.src{color:#777;font-size:.8em}h1,h2,h3{line-height:1.2}
.toc{display:inline-block;border:1px solid #ccc;background:#f8f8f8;padding:.4rem 1.2rem;margin:.6rem 0}.toc ul{margin:.1rem 0;padding-left:1.3rem}.sections ul{margin:.1rem 0 .9rem}.derived{color:#555}'''

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

from sections import HEADING, embedded_sections, thumb_file
from drawings_page import drawings_page
import truth
SHEETS = truth.load_truth()   # the reviewed per-sheet data (data/sheets/*.json): the build reads this and nothing the tools propose
_bad = truth.all_problems(SHEETS)
if _bad: sys.exit('data/sheets is malformed, so the Bill of Materials cannot be built:\n  ' + '\n  '.join(_bad))   # a hand edit that left a file the wrong shape
# images drawn from the exploded drawings PDF by scripts/render_sheets.py: name -> (sheet, 'lost', 'redrawn' or 'enlarged')
REDRAW = {im['file']: (sh['source'].get('page'), im['role']) for sh in SHEETS.values() for im in sh['images'] if im['role'] != 'wiki'}
REDRAW_NOTE = {'drawn': "the wiki never showed this sheet as an image",
               'lost': "the wiki's own copy of this image was not archived",
               'redrawn': "the wiki's image of this drawing was low resolution and the PDF has it larger"}

def fix_images(body, stats):
    def repl(m):
        tag = m.group(0)
        s = re.search(r'\ssrc="([^"]+)"', tag)
        if not s: return tag
        if '/resources/' in s.group(1): return ''
        fn = thumb_file(s.group(1))
        if fn in REDRAW and os.path.exists(f'{ROOT}/docs/images/{fn}'):   # drawn from the PDF or enlarged (scripts/render_sheets.py): the committed image replaces the wiki's
            sheet, kind = REDRAW[fn]
            copy(f'{ROOT}/docs/images/{fn}', f'{SITE}/images/{fn}')
            stats['rendered'] = stats.get('rendered', 0) + 1
            kept = ''
            if kind != 'lost' and os.path.exists(f'{ROOT}/docs/images/original/{fn}'):   # the wiki's own image stays, and the note links to it
                os.makedirs(f'{SITE}/images/original', exist_ok=True)
                copy(f'{ROOT}/docs/images/original/{fn}', f'{SITE}/images/original/{fn}')
                kept = f' <a href="images/original/{urllib.parse.quote(fn)}">The wiki\'s original</a> is kept.'
            if kind == 'enlarged': note = f'Enlarged to twice the size from the wiki\'s low-resolution image.{kept}'
            else: note = f'Drawn from sheet {sheet} of the exploded drawings PDF; {REDRAW_NOTE[kind]}.{kept}'
            return f'<img src="images/{urllib.parse.quote(fn)}" alt="{html.escape(fn)}"><p class="derived"><em>{note}</em></p>'
        rec = imgs.get(fn)
        if rec and rec.get('kind') and os.path.exists(f'{RAW}/images/{fn}'):
            copy(f'{RAW}/images/{fn}', f'{SITE}/images/{fn}')
            stats[rec['kind'].split('-')[0]] = stats.get(rec['kind'].split('-')[0], 0) + 1
            return f'<img src="images/{urllib.parse.quote(fn)}" alt="{html.escape(fn)}">'
        stats['missing'] = stats.get('missing', 0) + 1
        return f'<span class="missing">[image not archived: {html.escape(fn)}]</span>'
    def never_uploaded(m):   # the wiki's red link for a file that was never uploaded; it points at Special:Upload, which is no use here
        stats['missing'] = stats.get('missing', 0) + 1
        return f'<span class="missing">[image not archived: {html.escape(urllib.parse.unquote(html.unescape(m.group(1))))}]</span>'
    body = re.sub(r'<a [^>]*href="[^"]*Special:Upload[^"]*?wpDestFile=([^"&]+)[^"]*"[^>]*>.*?</a>', never_uploaded, body, flags=re.S)
    body = re.sub(r'<a [^>]*class="image"[^>]*>\s*(<img[^>]*>)\s*</a>', r'\1', body)  # drop links to File: pages
    return re.sub(r'<img[^>]*>', repl, body)

captures = json.load(open(f'{RAW}/versions/captures.json')) if os.path.exists(f'{RAW}/versions/captures.json') else {}
recovered = json.load(open(rec_path)) if os.path.exists(rec_path) else {}
def wayback_link(title, snap, label='archive link'):
    """A link to the capture the page was taken from, using the URL form that capture was saved under."""
    url = next((u for ts, u, *_ in captures.get(title, []) if ts == snap), None) or f'https://wiki.e3d-online.com/wiki/{title}'
    return f'<a href="https://web.archive.org/web/{snap}/{html.escape(url, quote=True)}">{label}</a>'

def with_heading_ids(body):
    """Give every h1-h6 an id (the wiki puts it on an inner span; rebuilt sections have none).
    Returns the body and [(level, id, text)] for the contents list."""
    heads, used = [], set()
    def repl(m):
        level, attrs, inner = int(m.group(1)), m.group(2), m.group(3)
        text = ' '.join(html.unescape(re.sub(r'<[^>]+>', '', inner)).split())
        found = re.search(r'\bid="([^"]+)"', attrs + inner)
        if found:
            heads.append((level, html.unescape(found.group(1)), text)); return m.group(0)
        hid = re.sub(r'[^\w-]+', '_', text).strip('_') or 'section'
        base, n = hid, 2
        while hid in used: hid, n = f'{base}_{n}', n + 1
        used.add(hid); heads.append((level, hid, text))
        return f'<h{level}{attrs} id="{html.escape(hid)}">{inner}</h{level}>'
    return HEADING.sub(repl, body), heads

def toc_html(heads):
    """A nested contents list, like the wiki's, for pages with four or more headings."""
    if len(heads) < 4: return ''
    out, stack = ['<div class="toc"><p class="toctitle"><strong>Contents</strong></p>'], []
    for level, hid, text in heads:
        while stack and stack[-1] > level: out.append('</li></ul>'); stack.pop()
        if stack and stack[-1] == level: out.append('</li>')
        elif not stack or stack[-1] < level: out.append('<ul>'); stack.append(level)
        out.append(f'<li><a href="#{html.escape(hid)}">{html.escape(text)}</a>')
    out.append('</li></ul>' * len(stack) + '</div>')
    return ''.join(out)

def add_section_lists(body, self_slug, heads_by_slug):
    """On the Build Manual page: under each heading that links to another page, list that page's top-level sections."""
    def repl(m):
        link = re.search(r'<a href="([^"#]+)\.html"', m.group(0))
        heads = heads_by_slug.get(link.group(1)) if link and link.group(1) != self_slug else None
        if not heads or len(heads) < 2: return m.group(0)
        top = min(level for level, _, _ in heads)
        items = ''.join(f'<li><a href="{link.group(1)}.html#{html.escape(hid)}">{html.escape(text)}</a></li>' for level, hid, text in heads if level == top)
        return m.group(0) + f'<div class="sections"><ul>{items}</ul></div>'
    body = HEADING.sub(repl, body)
    # The wiki also left each linked page's section names behind as plain text; the lists above replace them.
    # Under Versions Overview that text is a label followed by version names, so the names move under the matching link.
    # Software has an intro line, which stays.
    def tidy(m):
        div, rest = m.group(1), m.group(2)
        blocks = re.findall(r'<dl>.*?</dl>|<p>.*?</p>', rest, re.S)
        if 'BigBox_Version_Overview.html' in div:
            label = None
            for block in blocks:
                if block.startswith('<p>'): label = re.sub(r'<[^>]+>|\s+', ' ', block).strip()
                elif label:
                    names = ''.join(f'<li>{n.strip()}</li>' for n in re.findall(r'<dd>(.*?)</dd>', block, re.S))
                    div = re.sub(rf'(>{re.escape(html.escape(label))}</a>)(</li>)', rf'\1<ul>{names}</ul>\2', div, count=1)
            return div
        keep = [bl for bl in blocks if 'BigBox_Software.html' in div and bl.startswith('<p>The BigBox')]
        return div + ''.join(keep)
    return re.sub(r'(<div class="sections">.*?</div>)((?:\s*(?:<dl>(?:(?!<h\d).)*?</dl>|<p>(?:(?!<h\d).)*?</p>))*)', tidy, body, flags=re.S)

PRINTED_PART = truth.key('Printed Part')
PRINTED = {PRINTED_PART, truth.key('Printed Parts Box')}
PDF_LINK = 'files/EXPLODED_DRAWINGS.pdf'   # the copy kept in the repository (the archive's capture of 2016-01-09)

def add_drawing_parts(body, sheets, sections_by_image):
    """On the Bill of Materials page: fill the empty Printed Parts section and add a fixings table under Fixings, from the
    reviewed sheets (data/sheets). Both are marked as coming from the drawings, not from the wiki page.
    PDF sheets are exact text. Sheets that are only images on the wiki were read by OCR; their rows are used once a person has confirmed the sheet."""
    esc = html.escape
    def sections_for(names):   # every step of the manual that shows one of these images
        links, seen = [], set()
        for name in names:
            for page, hid, text in sections_by_image.get(name, []):
                if (page, hid) not in seen:
                    seen.add((page, hid)); links.append(f'<a href="{page}.html{"#" + html.escape(hid) if hid else ""}">{esc(text)}</a>')
        return '; '.join(links)
    rows, left_out = [], 0   # (drawing link, build section link, row)
    for sh in sorted(sheets.values(), key=lambda x: (x['source']['kind'] != 'pdf', x['id'])):   # the PDF's sheets first, then the image-only ones
        files = [im['file'] for im in sh['images']]
        if sh['source']['kind'] == 'pdf':
            n = sh['source']['page']
            drawing = (f'<a href="images/{urllib.parse.quote(files[0])}">{esc(os.path.splitext(files[0])[0].replace("_", " ").lower())}</a> (sheet {n})' if files
                       else f'<a href="{PDF_LINK}#page={n}">sheet {n} of the PDF</a>')
        else:
            if sh['confirmed'] is None and any(r['how'] in ('ocr', 'ocr+fix') for r in sh['rows']): left_out += len(sh['rows']); continue   # read by OCR and not yet checked by a person
            drawing = f'<a href="images/{urllib.parse.quote(files[0])}">{esc(sh["title"].lower())} (image)</a>'
        for r in sh['rows']: rows.append((drawing, sections_for(files), r))
    last_pdf_page = max((sh['source']['page'] for sh in sheets.values() if sh['source']['kind'] == 'pdf'), default=0)
    ocr = ' Sheets marked (image) exist only as pictures on the wiki; they were read by OCR and checked by a person, or entered by hand from the drawing and the manual where the drawing has no parts list.' if any('(image)' in d for d, _, _ in rows) else ''
    cut = f' {left_out} rows read by OCR are left out until they are checked.' if left_out else ''
    note = ('<p class="derived"><em>This list is not from the wiki page, which left it empty. It is compiled from the parts lists in the '
            f'<a href="{PDF_LINK}">exploded drawings PDF</a> (EXPLODED_DRAWINGS.pdf, sheets 1 to {last_pdf_page}) and the drawing images on the wiki. Each row links to the drawing, with its sheet number in the PDF. <a href="Exploded_Drawings.html">All the drawings are on one page.</a>{ocr}{cut}</em></p>')
    printed = [(d, sec, r) for d, sec, r in rows if truth.key(r['description']) in PRINTED]   # compared the way drift compares names: spacing and case do not matter
    tr = ''.join(f'<tr><td>{esc(r["part"])}</td><td>{"~" if r.get("approx") else ""}{r["qty"]}</td><td>{"printed" if truth.key(r["description"]) == PRINTED_PART else "from the Printed Parts Box"}</td>'
                 f'<td>{d}</td><td>{sec or "–"}</td></tr>' for d, sec, r in printed)
    printed_html = note + f'<table><thead><tr><th>Part</th><th>Qty</th><th>Source</th><th>Drawing</th><th>Build section</th></tr></thead><tbody>{tr}</tbody></table>'
    fixings = {}
    for d, _sec, r in rows:
        if truth.key(r['description']).startswith('FIXINGS'): fixings.setdefault((r['description'], r['part']), []).append(d)
    def bag_no(d): return int(''.join(c for c in d if c.isdigit()) or 0)
    tr = ''.join(f'<tr><td>{esc(bag)}</td><td>{esc(part)}</td><td>{", ".join(ds)}</td></tr>'
                 for (bag, part), ds in sorted(fixings.items(), key=lambda kv: (bag_no(kv[0][0]), kv[0][1])))
    fixings_html = note + f'<table><thead><tr><th>Fixings bag</th><th>Fixing</th><th>Drawings</th></tr></thead><tbody>{tr}</tbody></table>'
    body = re.sub(r'(<h3><span class="mw-headline" id="Printed_Parts">Printed Parts</span></h3>)', lambda m: m.group(1) + printed_html, body, count=1)
    return re.sub(r'(<h3><span class="mw-headline" id="Fixings">Fixings</span></h3>)', lambda m: m.group(1) + fixings_html, body, count=1)

def mark_dead(body):
    """A link the status file says is dead keeps its text and is labelled; if the archive has a copy, that is linked too."""
    def repl(m):
        url, inner = html.unescape(m.group(2)), m.group(4)
        info = link_status.get(url)
        if not info or info.get('status') != 'dead': return m.group(0)
        if re.match(r'\s*https?://', re.sub(r'<[^>]+>', '', inner)): inner = f'<code>{inner}</code>'   # a bare URL as text, not a link
        archived = f'; <a href="{html.escape(info["archived"])}">archived copy</a>' if info.get('archived') else ''
        return f'{inner} <em>(dead link{archived})</em>'
    return re.sub(r'<a\b([^>]*?)\bhref="(https?://[^"]+)"([^>]*)>(.*?)</a>', repl, body, flags=re.S)

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
    return mark_dead(re.sub(r'<a\b[^>]*href="#unarchived-page"[^>]*>(.*?)</a>', r'\1', body, flags=re.S))   # plain text, not a link

os.makedirs(f'{SITE}/files', exist_ok=True)   # wiki-hosted PDF datasheets (see fetch_files.py / appendix.py)
if os.path.isdir(f'{RAW}/files'):
    for f in os.listdir(f'{RAW}/files'): copy(f'{RAW}/files/{f}', f'{SITE}/files/{f}')

TARGET = '20161018063904'
# index first, then the archived pages alphabetically, then rebuilt pages, appendix and datasheets in the order recover/appendix wrote them
rebuilt = [t for t, info in (json.load(open(rec_path)).items() if os.path.exists(rec_path) else []) if info and t in pages and t not in latest_titles]
extras = {t for t, info in (json.load(open(rec_path)).items() if os.path.exists(rec_path) else []) if info and info.get('heading') in ('appendix', 'datasheets', 'downloads')}
order = ['BigBox_Build_Manual'] + sorted(t for t in pages if t != 'BigBox_Build_Manual' and t not in rebuilt) + rebuilt
stats, sections = {}, []
prepared = {t: with_heading_ids(extract(pages[t])) for t in order}   # (body, headings) per page
heads_by_slug = {slug(t): heads for t, (_, heads) in prepared.items()}
DRAWINGS_PAGE = 'Exploded_Drawings'   # every exploded drawing on one page, generated from the reviewed data
shown_in = embedded_sections({t: body for t, (body, _) in prepared.items()}, slug)   # before the new page exists, so it does not count as a step
if SHEETS and 'Bill_Of_Materials' in prepared:
    prepared['Bill_Of_Materials'] = (add_drawing_parts(prepared['Bill_Of_Materials'][0], SHEETS, shown_in), prepared['Bill_Of_Materials'][1])
if SHEETS:
    order.insert(order.index('Bill_Of_Materials') + 1 if 'Bill_Of_Materials' in order else len(order), DRAWINGS_PAGE)
    prepared[DRAWINGS_PAGE] = with_heading_ids(drawings_page(SHEETS, shown_in, {slug(t): t.replace('_', ' ') for t in order if t != DRAWINGS_PAGE},
                                                             [slug(t) for t in order if t != DRAWINGS_PAGE], heads_by_slug))
    heads_by_slug[slug(DRAWINGS_PAGE)] = prepared[DRAWINGS_PAGE][1]
    extras.add(DRAWINGS_PAGE)   # not a wiki page: no source line
if 'BigBox_Build_Manual' in prepared:   # the main page links the pages that are generated from the reviewed data, in an Appendix at the end
    entries = [(DRAWINGS_PAGE, 'Exploded Drawings', 'every assembly drawing in one place, each with its parts list and the steps of the manual that show it')] if SHEETS else []
    entries += [('Bill_Of_Materials', 'Bill of Materials', 'the parts, with the printed parts and fixings compiled from the exploded drawings')] if 'Bill_Of_Materials' in prepared else []
    if entries:
        appendix = '<h3><span class="mw-headline" id="Appendix">Appendix</span></h3><ul>' + ''.join(f'<li><a href="{slug(t)}.html">{label}</a> &ndash; {note}</li>' for t, label, note in entries) + '</ul>'
        body, heads = prepared['BigBox_Build_Manual']
        extra_body, extra_heads = with_heading_ids(appendix)
        prepared['BigBox_Build_Manual'] = (body + extra_body, heads + extra_heads)
        heads_by_slug[slug('BigBox_Build_Manual')] = prepared['BigBox_Build_Manual'][1]
for t in order:
    body0, heads = prepared[t]
    b = fix_links(fix_images(body0, stats), False)
    if t == 'BigBox_Build_Manual': b = add_section_lists(b, slug(t), heads_by_slug)
    snap = meta.get(t, {}).get('snapshot', '?')
    if t in latest_titles: src = f'Archived {snap} · source: wiki.e3d-online.com/wiki/{html.escape(t)} · {wayback_link(t, snap)}'
    elif t in extras: src = ''   # the appendix and datasheets pages are not wiki pages
    else:   # rebuilt pages: the note under the title says where from; link the parent page's capture the text was cut from
        parent = recovered.get(t) or {}
        link = f' · {wayback_link(parent["parent"], parent["version"], "archive link (parent page)")}' if parent.get('parent') else ''
        src = f'Rebuilt page · source: wiki.e3d-online.com/wiki/{html.escape(t)}{link}'
    head = f'<h1>{html.escape(t.replace("_", " "))}</h1>' + (f'<p class="src">{src}</p>' if src else '')
    nav = '<nav><a href="index.html">All pages</a></nav>'
    open(f'{SITE}/{slug(t)}.html', 'w').write(f'<!doctype html><meta charset="utf-8"><title>{html.escape(t)}</title><style>{STYLE}</style>{nav}{head}{toc_html(heads)}{b}')
    sections.append((t, fix_links(fix_images(body0, {}), True), head))

toc = ''.join(f'<li><a href="{slug(t)}.html">{html.escape(t.replace("_"," "))}</a></li>' for t in order)
open(f'{SITE}/index.html', 'w').write(f'<!doctype html><meta charset="utf-8"><title>BigBox Manual</title><style>{STYLE}</style><h1>BigBox 3D Printer Manual</h1><p>Offline copy compiled from the Wayback Machine capture of wiki.e3d-online.com.</p><ul>{toc}</ul><p><a href="manual.html">Everything on one page</a></p><p class="src">The original wiki showed a notice on its pages from 2019 onward saying it was no longer maintained and pointing to e3d-online.dozuki.com. That notice is left out here. The Dozuki site could not be reached when this copy was compiled, and the archived copy that was checked contained no BigBox guides.</p>')
allp = ''.join(f'<section id="{slug(t)}">{h}{b}</section><hr>' for t, b, h in sections)
open(f'{SITE}/manual.html', 'w').write(f'<!doctype html><meta charset="utf-8"><title>BigBox Manual</title><style>{STYLE}</style><h1>BigBox Manual (complete)</h1><ol>{"".join(f"<li><a href=#{slug(t)}>{html.escape(t.replace(chr(95), chr(32)))}</a></li>" for t in order)}</ol><hr>{allp}')
print(len(order), 'pages built;', 'images:', stats)
