#!/usr/bin/env python3
"""Fetch the E3D BigBox wiki from the Wayback Machine using its CDX API.

1. inventory: two bulk CDX queries list every captured wiki page and image (cached in raw/cdx_*.json).
2. pages: crawl from BigBox_Build_Manual, fetching the capture nearest TARGET by exact timestamp.
3. images: for each image used, prefer the full-res original path, else the widest archived thumbnail.

Polite by design: one connection, fixed delay, Retry-After honoured, exponential backoff,
aborts after repeated failures. Everything is cached so re-runs only fetch what is missing.
Run:  python3 -I scripts/crawl.py [inventory|pages|images|all]
"""
import gzip, json, os, re, shutil, sys, time, html, urllib.request, urllib.parse, urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.environ.get('BIGBOX_RAW', f'{ROOT}/raw')   # archive data lives outside git; override with BIGBOX_RAW
TARGET = '20161018063904'
HOST = 'wiki.e3d-online.com'
UA = 'bigbox-manual-archiver/2.0 (personal documentation backup; single connection)'
DELAY = 2.0
MAX_CONSEC_FAIL = 4
os.makedirs(f'{RAW}/images', exist_ok=True)
SEED = os.environ.get('BIGBOX_SEED')   # optional read-only folder laid out like the data folder; used before any network fetch
stats = {'seeded': 0, 'network': 0}

def from_seed(rel, dest=None):
    """Copy rel from the seed folder into the data folder (at dest, default rel). True if the seed had it."""
    src = f'{SEED}/{rel}' if SEED else None
    if not src or not os.path.exists(src): return False
    os.makedirs(os.path.dirname(f'{RAW}/{dest or rel}'), exist_ok=True)
    shutil.copy(src, f'{RAW}/{dest or rel}'); stats['seeded'] += 1
    return True

fails = 0

def get(url, binary=False, tries=5):
    """Return (status, bytes|str|None). 404/403/410 are final answers; everything else is retried."""
    global fails
    stats['network'] += 1
    for i in range(tries):
        time.sleep(DELAY)
        wait = 20 * 2 ** i
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': UA}), timeout=90) as r:
                d = r.read(); fails = 0
                if d[:2] == b'\x1f\x8b': d = gzip.decompress(d)   # some captures arrive gzipped
                return r.status, (d if binary else d.decode('utf-8', 'replace'))
        except urllib.error.HTTPError as e:
            if e.code in (404, 403, 410): fails = 0; return e.code, None
            wait = max(wait, int(e.headers.get('Retry-After', 0) or 0))
            print(f'  HTTP {e.code}; retry {i+1}/{tries} in {wait}s', flush=True)
        except Exception as e:
            print(f'  {type(e).__name__}; retry {i+1}/{tries} in {wait}s', flush=True)
        time.sleep(wait)
    fails += 1
    if fails >= MAX_CONSEC_FAIL:
        print(f'ABORT: {fails} consecutive failed fetches; wait for the block to clear and re-run.', flush=True)
        sys.exit(2)
    return 0, None

def snap(url, ts, flavor):  # exact-timestamp raw capture; id_ = original bytes, im_ = image
    return f'https://web.archive.org/web/{ts}{flavor}/{url}'

# ---------- 1. inventory ----------
def cdx(prefix, extra=''):
    q = (f'https://web.archive.org/cdx/search/cdx?url={urllib.parse.quote(prefix)}&matchType=prefix'
         f'&output=json&fl=timestamp,original,mimetype,statuscode&filter=statuscode:200&limit=100000{extra}')
    st, body = get(q)
    if st != 200: sys.exit(f'CDX query failed ({st}): {prefix}')
    rows = json.loads(body) if body.strip() else []
    return rows[1:] if rows else []

def inventory(names=('wiki', 'index', 'images')):
    out = {}
    for name, prefix, extra in [x for x in (('wiki', f'{HOST}/wiki/', ''),   # no mimetype filter: duplicate captures are stored as warc/revisit
                                ('index', f'{HOST}/index.php?title=', ''),
                                ('images', f'{HOST}/images/', '')) if x[0] in names]:
        path = f'{RAW}/cdx_{name}.json'
        if not os.path.exists(path) and not from_seed(f'cdx_{name}.json'):
            rows = cdx(prefix, extra)
            json.dump(rows, open(path, 'w'))
            print(f'CDX {name}: {len(rows)} captures', flush=True)
        out[name] = json.load(open(path))
    return out

def index(rows, keyf):
    idx = {}
    for ts, orig, *_ in rows:
        idx.setdefault(keyf(orig), []).append((ts, orig))
    return idx

def nearest(caps, target=TARGET):
    return min(caps, key=lambda c: abs(int(c[0]) - int(target)))

# ---------- 2. pages ----------
OTHER = re.compile(r'^(Main_Page|FAQs|CAD|E3D|Cyclops|Kraken|Ultimaker|Acceptable_Guide|Frame_Fixings)|v6|Lite6|PT100', re.I)

def slug(t): return urllib.parse.unquote(t).replace('/', '_')
def title_of(orig):
    u = urllib.parse.urlparse(orig)
    if '/wiki/' in u.path:
        return urllib.parse.unquote(u.path.split('/wiki/', 1)[1]).replace(' ', '_')
    q = urllib.parse.parse_qs(u.query)  # plain index.php?title=X only (no action=, oldid=, ...)
    return q['title'][0].replace(' ', '_') if list(q) == ['title'] else None

def page_links(h):
    m = re.search(r'id="mw-content-text".*?<div class="printfooter"', h, re.S) or re.search(r'id="mw-content-text".*', h, re.S)
    out = set()
    for href in re.findall(r'href="(?:https?://wiki\.e3d-online\.com)?(/wiki/[^"#?]+)"', m.group(0) if m else h):
        t = urllib.parse.unquote(html.unescape(href)[6:])
        if ':' in t.split('/')[0] or t.endswith('.jpg'): continue  # Special:, Talk:, File:, ...
        out.add(t)
    return out

def pages(inv):
    os.makedirs(f'{RAW}/pages', exist_ok=True)
    rows = [r for r in inv['wiki'] + inv['index'] if title_of(r[1])]
    idx = index(rows, lambda o: title_of(o).lower())
    log_path = f'{RAW}/pages.json'
    log = json.load(open(log_path)) if os.path.exists(log_path) else {}
    todo, seen, skipped = ['BigBox_Build_Manual'], set(), set()
    while todo:
        t = todo.pop()
        if t.lower() in seen: continue
        seen.add(t.lower())
        cache = f'{RAW}/pages/{slug(t)}.html'
        if os.path.exists(cache):
            h = open(cache).read()
        else:
            caps = idx.get(t.lower())
            if not caps:
                log[t] = {'status': 'not-in-archive'}; print(t, 'NOT IN ARCHIVE', flush=True); continue
            ts, orig = nearest(caps)
            st, h = get(snap(orig, ts, 'id_'))
            log[t] = {'status': st, 'snapshot': ts, 'url': orig}
            print(t, st, ts, flush=True)
            if h:
                open(cache, 'w').write(h)
                json.dump(log, open(log_path, 'w'), indent=1)
        if not h: continue
        for l in page_links(h):
            (skipped if OTHER.search(l) else set()).add(l)
            if not OTHER.search(l): todo.append(l)
    json.dump(log, open(log_path, 'w'), indent=1)
    json.dump(sorted(skipped), open(f'{RAW}/skipped_other_products.json', 'w'), indent=1)

# ---------- 3. images ----------
def orig_path(path):
    """/images/thumb/d/d5/X.png/550px-X.png -> /images/d/d5/X.png"""
    m = re.match(r'(/images)/thumb/(.+?)/[^/]+$', path)
    return f'{m.group(1)}/{m.group(2)}' if m else path

def all_saved_pages():
    """(name, path) of every saved page and version in the data folder."""
    pdir = f'{RAW}/pages'
    files = [(f[:-5], f'{pdir}/{f}') for f in sorted(os.listdir(pdir))] if os.path.isdir(pdir) else []
    vdir = f'{RAW}/versions'   # every archived version too: older versions hold images later removed
    if os.path.isdir(vdir):
        for t in sorted(os.listdir(vdir)):
            if os.path.isdir(f'{vdir}/{t}'):
                files += [(t, f'{vdir}/{t}/{v}') for v in sorted(os.listdir(f'{vdir}/{t}')) if v.endswith('.html')]
    return files

def images_used(files=None):
    """Image file -> pages using it, over the given (name, path) list or every saved page and version."""
    used = {}
    for name, path in (all_saved_pages() if files is None else files):
        h = open(path).read()
        m = re.search(r'id="mw-content-text".*?<div class="printfooter"', h, re.S)
        for tag in re.findall(r'<img[^>]*>', m.group(0) if m else h):
            s = re.search(r'\ssrc="([^"]+)"', tag)
            if not s: continue
            p = urllib.parse.unquote(urllib.parse.urlparse(html.unescape(s.group(1))).path)
            if not p.startswith('/images/'): continue
            used.setdefault(orig_path(p), set()).add(name)
    return used

def width(p):
    m = re.search(r'/(\d+)px-[^/]+$', p); return int(m.group(1)) if m else 0

def images(inv, files=None):
    seed_man = json.load(open(f'{SEED}/images.json')) if SEED and os.path.exists(f'{SEED}/images.json') else {}
    caps = {}
    for ts, orig, *_ in inv['images']:
        caps.setdefault(urllib.parse.unquote(urllib.parse.urlparse(orig).path), []).append((ts, orig))
    mpath = f'{RAW}/images.json'
    man = json.load(open(mpath)) if os.path.exists(mpath) else {}
    for op, users in images_used(files).items():
        fname = op.rsplit('/', 1)[1]
        if man.get(fname, {}).get('kind') == 'original' and os.path.exists(f'{RAW}/images/{fname}'):
            continue
        choice, kind = None, None
        if op in caps:
            choice, kind = nearest(caps[op]), 'original'
        else:  # widest thumbnail archived for this file
            th = [(width(p), p) for p in caps if p.startswith('/images/thumb/') and orig_path(p) == op]
            if th:
                w, p = max(th); choice, kind = nearest(caps[p]), f'thumb-{w}px'
        old = man.get(fname, {})
        if choice and old.get('kind') == kind and old.get('snapshot') == choice[0] and os.path.exists(f'{RAW}/images/{fname}'):
            continue  # already have exactly this capture
        if not choice and fname in man and not man[fname].get('kind'):
            continue  # already known to be absent from the archive
        sd = seed_man.get(fname)
        if choice and sd and sd.get('kind') == kind and sd.get('snapshot') == choice[0] and from_seed(f'images/{fname}'):
            man[fname] = {**sd, 'pages': sorted(users)}; json.dump(man, open(mpath, 'w'), indent=1); continue
        rec = {'kind': None, 'pages': sorted(users), 'original_path': op}
        if choice:
            ts, orig = choice
            st, d = get(snap(orig, ts, 'im_'), binary=True)
            if st == 200 and d and not d.startswith(b'<'):
                open(f'{RAW}/images/{fname}', 'wb').write(d)
                rec.update(kind=kind, snapshot=ts, url=orig, bytes=len(d))
        man[fname] = rec
        print(fname, rec['kind'], rec.get('bytes', 0), flush=True)
        json.dump(man, open(mpath, 'w'), indent=1)

if __name__ == '__main__':
    step = sys.argv[1] if len(sys.argv) > 1 else 'all'
    inv = inventory()
    if step in ('pages', 'all'): pages(inv)
    if step in ('images', 'all'): images(inv)
