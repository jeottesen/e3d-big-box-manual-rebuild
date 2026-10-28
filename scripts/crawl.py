#!/usr/bin/env python3
"""Wayback Machine helpers used by fetch.py and fetch_files.py: polite fetching, the CDX image inventory,
the BIGBOX_SEED layer, and choosing and downloading images.

Polite by design: one connection, fixed delay, Retry-After honoured, exponential backoff, abort after repeated
failures. Image choice: the full-size original if the archive has it, else the widest archived thumbnail.
Not run directly; see scripts/README.md.
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

def nearest(caps, target=TARGET):
    return min(caps, key=lambda c: abs(int(c[0]) - int(target)))

# pages the manual does not follow (other E3D products)
OTHER = re.compile(r'^(Main_Page|FAQs|CAD|E3D|Cyclops|Kraken|Ultimaker|Acceptable_Guide|Frame_Fixings)|v6|Lite6|PT100', re.I)

# ---------- 3. images ----------
def orig_path(path):
    """/images/thumb/d/d5/X.png/550px-X.png -> /images/d/d5/X.png"""
    m = re.match(r'(/images)/thumb/(.+?)/[^/]+$', path)
    return f'{m.group(1)}/{m.group(2)}' if m else path

def images_used(files):
    """Image file -> pages using it, over the given (name, path) list of saved page versions."""
    used = {}
    for name, path in files:
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

def images(inv, files):
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
