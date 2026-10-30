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

def write_if_changed(path, text):
    """Write text unless the file already holds exactly that, so an unchanged result keeps its modification time and
    mise does not think the steps that read it are out of date."""
    if os.path.exists(path) and open(path).read() == text: return False
    open(path, 'w').write(text)
    return True

def get(url, binary=False, tries=5, final_codes=(404, 403, 410)):
    """Return (status, bytes|str|None). The final_codes statuses are answers; everything else is retried."""
    global fails  # noqa: PLW0603 (a retry counter shared by the whole run)
    stats['network'] += 1
    codes = []   # what each failed attempt was: an HTTP status, or None for a network error
    for i in range(tries):
        time.sleep(DELAY)
        wait = 20 * 2 ** i
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': UA}), timeout=90) as r:
                d = r.read(); fails = 0
                if d[:2] == b'\x1f\x8b': d = gzip.decompress(d)   # some captures arrive gzipped
                return r.status, (d if binary else d.decode('utf-8', 'replace'))
        except urllib.error.HTTPError as e:
            if e.code in final_codes: fails = 0; return e.code, None
            codes.append(e.code)
            wait = max(wait, int(e.headers.get('Retry-After', 0) or 0))
            print(f'  HTTP {e.code}; retry {i+1}/{tries} in {wait}s', flush=True)
        except Exception as e:
            codes.append(None)
            print(f'  {type(e).__name__}; retry {i+1}/{tries} in {wait}s', flush=True)
        time.sleep(wait)
    if not final_codes and len(codes) == tries and set(codes) <= {404, 410}:
        fails = 0; return codes[-1], None   # gone every time: a dead capture the index still lists, not a failed download
    fails += 1
    if fails >= MAX_CONSEC_FAIL:
        print(f'ABORT: {fails} consecutive failed fetches; wait for the block to clear and re-run.', flush=True)
        sys.exit(2)
    return 0, None

def get_snapshot(url, binary=False):
    """Fetch a capture that the CDX index says exists. A 403/404/410 for such a URL is not an answer, it is a
    refused or flaky request, so it is retried like any other error. Returns (200, data) or, after every
    attempt failed, (0, None); callers must treat that as a failed download, not as 'not archived'.
    A capture that answers 404 or 410 on every attempt is dead (the index lists it but the archive cannot serve it):
    that returns (404, None) or (410, None), which callers treat as 'try another capture', not as a failure."""
    return get(url, binary, tries=3, final_codes=())

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

def candidates(op, caps):
    """Captures to try for an image, best first: the original, then thumbnails widest first; nearest TARGET first within each."""
    near = lambda cs: sorted(cs, key=lambda c: abs(int(c[0]) - int(TARGET)))
    out = [('original', c) for c in near(caps.get(op, []))]
    for w, p in sorted(((width(p), p) for p in caps if p.startswith('/images/thumb/') and orig_path(p) == op), reverse=True):
        out += [(f'thumb-{w}px', c) for c in near(caps[p])]
    return out

def images(inv, files):
    """Fetch the images used by the given page versions. Returns the images whose download failed (not dead captures)."""
    seed_man = json.load(open(f'{SEED}/images.json')) if SEED and os.path.exists(f'{SEED}/images.json') else {}
    caps = {}
    for ts, orig, *_ in inv['images']:
        caps.setdefault(urllib.parse.unquote(urllib.parse.urlparse(orig).path), []).append((ts, orig))
    mpath = f'{RAW}/images.json'
    man = json.load(open(mpath)) if os.path.exists(mpath) else {}
    failed = []   # images the archive has but that could not be downloaded this time
    for op, users in images_used(files).items():
        fname = op.rsplit('/', 1)[1]
        if man.get(fname, {}).get('kind') == 'original' and os.path.exists(f'{RAW}/images/{fname}'):
            continue
        old = man.get(fname, {})
        dead = [list(d) for d in old.get('dead', [])]   # captures the index lists but the archive answered 404/410 for
        cands = [(k, c) for k, c in candidates(op, caps) if list(c) not in dead]
        kind, choice = cands[0] if cands else (None, None)
        if choice and old.get('kind') == kind and old.get('snapshot') == choice[0] and os.path.exists(f'{RAW}/images/{fname}'):
            continue  # already have exactly this capture
        if not choice and fname in man and not man[fname].get('error'):
            continue  # already known to be absent from the archive
        sd = seed_man.get(fname)
        if choice and sd and sd.get('kind') == kind and sd.get('snapshot') == choice[0] and from_seed(f'images/{fname}'):
            man[fname] = {**sd, 'pages': sorted(users)}; json.dump(man, open(mpath, 'w'), indent=1); continue
        rec = {'kind': None, 'pages': sorted(users), 'original_path': op}
        for k, (ts, orig) in cands:
            st, d = get_snapshot(snap(orig, ts, 'im_'), binary=True)
            if st == 200 and d and not d.startswith(b'<'):
                open(f'{RAW}/images/{fname}', 'wb').write(d)
                rec.update(kind=k, snapshot=ts, url=orig, bytes=len(d)); break
            if st in (404, 410):
                dead.append([ts, orig]); continue   # listed in the index but gone: try the next capture
            rec['error'] = f'download failed (status {st})' if not d else 'the archive returned a page, not an image'
            failed.append(fname); break
        if dead: rec['dead'] = dead
        if not rec['kind'] and not rec.get('error') and cands: rec['note'] = 'every capture the index lists for this image is dead (404)'
        man[fname] = rec
        extra = '  <-- DOWNLOAD FAILED: ' + rec['error'] if rec.get('error') else (f'  (skipped {len(dead)} dead capture(s))' if dead else '')
        print(fname, rec['kind'], rec.get('bytes', 0), extra, flush=True)
        json.dump(man, open(mpath, 'w'), indent=1)
    return failed
