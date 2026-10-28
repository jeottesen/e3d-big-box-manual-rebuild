#!/usr/bin/env python3
"""Collect every distinct archived version of each wiki page and diff consecutive versions.

For each page in raw/pages.json this looks up captures under BOTH URL forms
(/wiki/Title from ~2016, /Title from ~2018-2020) via exact-URL CDX queries, keeps one file per
distinct content digest in raw/versions/<Title>/<timestamp>.html, and writes
raw/versions/<Title>/CHANGES.diff (text diff of the article body between consecutive versions).
raw/versions/SUMMARY.md lists what changed per page.

Polite: one connection, fixed delay, backoff on errors/archive error pages, abort after repeated failure.
Resumable: captures list and fetched files are cached.
Run:  python3 -I scripts/versions.py [list|fetch|diff|all]
"""
import difflib, gzip, html, json, os, re, sys, time, urllib.parse, urllib.request, urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.environ.get('BIGBOX_RAW', f'{ROOT}/raw')   # archive data lives outside git; override with BIGBOX_RAW
VER = f'{RAW}/versions'
HOST = 'wiki.e3d-online.com'
UA = 'bigbox-manual-archiver/2.0 (personal documentation backup; single connection)'
DELAY, MAX_FAIL = 3.0, 4
EXTERNAL = {'Secure_Shell', 'Marlin', 'Mains_electricity_by_country'}  # links to other wikis, logged by an early crawler bug
os.makedirs(VER, exist_ok=True)
fails = 0

def get(url, tries=4):
    global fails
    for i in range(tries):
        time.sleep(DELAY)
        wait = 30 * 2 ** i
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': UA}), timeout=120) as r:
                d = r.read()
                if d[:2] == b'\x1f\x8b': d = gzip.decompress(d)   # some captures arrive gzipped
                d = d.decode('utf-8', 'replace')
                if 'Temporarily Offline' in d[:3000] or d.lstrip().startswith('<html><head><title>50'):
                    raise RuntimeError('archive error page')
                fails = 0; return d
        except urllib.error.HTTPError as e:
            if e.code in (404, 403, 410): fails = 0; return None
            wait = max(wait, int(e.headers.get('Retry-After', 0) or 0))
        except Exception:
            pass
        print(f'  retry {i+1}/{tries} in {wait}s', flush=True); time.sleep(wait)
    fails += 1
    if fails >= MAX_FAIL: sys.exit('ABORT: repeated failures; re-run later (progress is cached).')
    return False  # False = inconclusive (not cached); None = definitively absent; '' = answered, empty

def q(t): return urllib.parse.quote(t, safe="()-_:,")

def list_captures():
    path = f'{VER}/captures.json'
    caps = json.load(open(path)) if os.path.exists(path) else {}
    for t in json.load(open(f'{RAW}/pages.json')):
        if t in EXTERNAL: continue
        if t in caps and caps[t] is not None: continue
        rows = []
        for form in (f'{HOST}/wiki/{q(t)}', f'{HOST}/{q(t)}'):
            d = get(f'https://web.archive.org/cdx/search/cdx?url={form}&output=txt&fl=timestamp,original,digest,statuscode&limit=200')
            if d is False: rows = None; break         # request failed: inconclusive, retry on next run
            for line in (d or '').splitlines():
                p = line.split()
                if len(p) == 4 and p[3] == '200': rows.append(p[:3])
        caps[t] = rows
        print(t, 'inconclusive' if rows is None else f'{len(rows)} captures', flush=True)
        json.dump(caps, open(path, 'w'), indent=1)
    return caps

def distinct(rows):
    seen, out = set(), []
    for ts, orig, dg in sorted(rows):
        if dg not in seen: seen.add(dg); out.append((ts, orig))
    return out

def fetch(caps):
    for t, rows in caps.items():
        for ts, orig in distinct(rows or []):
            f = f'{VER}/{t.replace("/", "_")}/{ts}.html'
            if os.path.exists(f) or any(os.path.exists(f'{RAW}/versions_removed/{r}/{t.replace("/", "_")}/{ts}.html') for r in ('errors', 'unchanged')): continue  # have it, or already judged by clean.py
            os.makedirs(os.path.dirname(f), exist_ok=True)
            d = get(f'https://web.archive.org/web/{ts}id_/{orig}')
            print(t, ts, 'ok' if d else ('absent' if d is None else 'inconclusive'), flush=True)
            if d: open(f, 'w').write(d)

def body_text(h):
    m = re.search(r'id="mw-content-text"[^>]*>(.*?)(?:<div class="printfooter"|<!-- NewPP)', h, re.S) or re.search(r'id="mw-content-text"[^>]*>(.*)', h, re.S)
    b = m.group(1) if m else h
    b = re.sub(r'<(script|style).*?</\1>|<!--.*?-->', '', b, flags=re.S)
    b = re.sub(r'<img[^>]*?(?:alt="([^"]*)")?[^>]*?src="[^"]*?/([^/"]+)"[^>]*>',  # keep image file names in the diff
               lambda m: f'\n[img {urllib.parse.unquote(m.group(2))}]\n', b)
    b = re.sub(r'</(p|li|h\d|tr|div|dd|dt|pre)>|<br\s*/?>', '\n', b)
    b = html.unescape(re.sub(r'<[^>]+>', '', b))
    return [l.strip() for l in b.splitlines() if l.strip() and not l.strip().startswith('[edit')]

def diffs():
    summary = ['# Version changes per page\n']
    for t in sorted(os.listdir(VER)):
        d = f'{VER}/{t}'
        if not os.path.isdir(d): continue
        files = sorted(f for f in os.listdir(d) if f.endswith('.html'))
        summary.append(f'## {t}\n- versions: {", ".join(f[:-5] for f in files)}')
        out = []
        for a, b in zip(files, files[1:]):
            la, lb = body_text(open(f'{d}/{a}').read()), body_text(open(f'{d}/{b}').read())
            ud = list(difflib.unified_diff(la, lb, a[:-5], b[:-5], lineterm='', n=1))
            add = sum(1 for l in ud if l.startswith('+') and not l.startswith('+++'))
            rem = sum(1 for l in ud if l.startswith('-') and not l.startswith('---'))
            summary.append(f'- {a[:-5]} -> {b[:-5]}: +{add} / -{rem} lines' if ud else f'- {a[:-5]} -> {b[:-5]}: text identical (layout/markup only)')
            out += ud + ['']
        open(f'{d}/CHANGES.diff', 'w').write('\n'.join(out))
        summary.append('')
    open(f'{VER}/SUMMARY.md', 'w').write('\n'.join(summary))
    print(f'wrote {VER}/SUMMARY.md')

if __name__ == '__main__':
    step = sys.argv[1] if len(sys.argv) > 1 else 'all'
    if step in ('list', 'fetch', 'all'):
        caps = list_captures()
        if step in ('fetch', 'all'): fetch(caps)
    if step in ('diff', 'all'): diffs()
