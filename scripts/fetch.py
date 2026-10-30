#!/usr/bin/env python3
"""Lean fetch: get only what the manual needs from the Wayback Machine.

1. Start at BigBox_Build_Manual and follow links. For each page, take its newest good capture (stepping back
   to an older capture if the newest is an error page). That is the version the manual uses.
2. For pages the archive never saved (see targets.py), look back through older versions of the page that used
   to contain them, newest first, and stop at the first version that still has the section.
3. Find the removed sections kept in the appendix (targets.py) by bisecting the page's versions.
4. Fetch only the images those page versions use (original if archived, else the widest thumbnail).

Writes versions/<Page>/<timestamp>.html, versions/latest.json, versions/captures.json, pages.json and
cdx_images.json in the data folder. Nothing else is downloaded. Set BIGBOX_SEED to a read-only folder laid out
like the data folder and files are copied from it before any network request.
Run:  python3 -I scripts/fetch.py
"""
import html, json, os, re, sys, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # sibling modules (python -I does not add the script folder)
import crawl, recover
from targets import APPENDIX, TARGETS

RAW = crawl.RAW
VER = f'{RAW}/versions'
START = 'BigBox_Build_Manual'
os.makedirs(VER, exist_ok=True)
tally = {'versions_used': {}, 'seeded_versions': 0, 'network_versions': 0, 'corrupt': []}

# ---------- captures of a page ----------
CAPS_PATH = f'{VER}/captures.json'
caps = json.load(open(CAPS_PATH)) if os.path.exists(CAPS_PATH) else {}
_seed = None

def seed_captures():
    global _seed
    if _seed is None:
        p = f'{crawl.SEED}/versions/captures.json' if crawl.SEED else None
        _seed = json.load(open(p)) if p and os.path.exists(p) else {}
    return _seed

def q(title): return urllib.parse.quote(title, safe="()-_:,")

def captures(title):
    """Newest-first (timestamp, original url) of a page's 200 captures, under both wiki URL forms."""
    if title not in caps:
        if seed_captures().get(title) is not None:
            caps[title] = seed_captures()[title]
        else:
            rows = []
            for form in (f'{crawl.HOST}/wiki/{q(title)}', f'{crawl.HOST}/{q(title)}'):   # 2015-16 form, then 2018+ form
                st, body = crawl.get(f'https://web.archive.org/cdx/search/cdx?url={form}&output=txt'
                                     f'&fl=timestamp,original,digest,statuscode&limit=500')
                if st != 200: sys.exit(f'CDX lookup failed for {title} ({st}); re-run later, progress is kept.')
                rows += [p[:3] for p in (l.split() for l in body.splitlines()) if len(p) == 4 and p[3] == '200']
            caps[title] = rows
        json.dump(caps, open(CAPS_PATH, 'w'), indent=1)
    seen, out = set(), []
    for ts, orig, *_ in sorted(caps[title], reverse=True):
        if ts not in seen: seen.add(ts); out.append((ts, orig))
    return out

# ---------- page versions ----------
def version_path(title, ts): return f'{VER}/{title.replace("/", "_")}/{ts}.html'

def corrupt(path):
    """A saved version that is gzip data decoded as text (an old crawler bug): it starts with the gzip magic byte, then U+FFFD."""
    with open(path, 'rb') as f: return f.read(4) == b'\x1f\xef\xbf\xbd'

def fetch_version(title, orig, ts):
    path = version_path(title, ts)
    rel = f'versions/{title.replace("/", "_")}/{ts}.html'
    if os.path.exists(path) and corrupt(path):
        print(f'  note: {title} {ts} was saved corrupt (undecoded gzip); downloading it again', flush=True)
        os.remove(path); tally['corrupt'].append(f'{title} {ts}')
        use_seed = False
    else: use_seed = True
    if not os.path.exists(path):
        # a seed from an older data folder may keep some versions under versions_removed/
        seeded = use_seed and any(crawl.from_seed(r, rel) for r in (rel, rel.replace('versions/', 'versions_removed/unchanged/'),
                                                                     rel.replace('versions/', 'versions_removed/errors/')))
        if seeded and corrupt(path):   # the seed has the same bug: don't keep its copy
            print(f'  note: the seed copy of {title} {ts} is corrupt (undecoded gzip); downloading it instead', flush=True)
            os.remove(path); tally['corrupt'].append(f'{title} {ts}'); seeded = False
        if seeded: tally['seeded_versions'] += 1
        else:
            st, h = crawl.get_snapshot(crawl.snap(orig, ts, 'id_'))
            if st in (404, 410):   # the archive lists this capture but cannot serve it: forget it, the caller tries an older one
                print(f'  note: {title} {ts} is listed by the archive but returns {st}; skipping that capture', flush=True)
                caps[title] = [r for r in caps.get(title, []) if r[0] != ts]; json.dump(caps, open(CAPS_PATH, 'w'), indent=1)
                return None
            if h is None:   # a real failure: never fall back to an older capture because of it
                sys.exit(f'Could not download {title} {ts} (status {st}). Re-run to retry; what was fetched is kept.')
            os.makedirs(os.path.dirname(path), exist_ok=True); open(path, 'w').write(h)
            tally['network_versions'] += 1
    tally['versions_used'][f'{title} {ts}'] = True
    return open(path).read()

def valid(h):
    """A real article: has a body, no error text, and more than a stub's worth of text."""
    return 'id="mw-content-text"' in h and not recover.ERR.search(h[:6000]) and len(recover.body_text(h)) >= 5

def latest_good(title):
    for ts, orig in captures(title):
        h = fetch_version(title, orig, ts)
        if h and valid(h): return ts, orig, h
    return None

# ---------- 1. discover the pages the manual needs ----------
LINK = re.compile(r'href="(?:https?://wiki\.e3d-online\.com)?/(?:wiki/)?([^"#?/][^"#?]*)"')
NOT_PAGES = ('images/', 'resources/', 'index.php', 'web/', 'skins/', 'load.php', 'extensions/')
# wiki namespaces that are not manual pages; a colon alone does not make a title a namespace page
NAMESPACES = re.compile(r'^(File|Image|Media|Special|Talk|User|Category|Template|Help|MediaWiki|E3D-Online)(_talk)?:', re.I)

def links(h):
    out = []
    for m in LINK.finditer(recover.content(h)):
        t = urllib.parse.unquote(html.unescape(m.group(1))).replace(' ', '_')
        if t.startswith(NOT_PAGES) or NAMESPACES.match(t) or crawl.OTHER.search(t): continue   # File:, Special:, other products
        out.append(t)
    return out

def discover():
    latest, log, absent = {}, {}, []
    todo, seen = [START], set()
    while todo:
        t = todo.pop(0)
        if t.lower() in seen: continue
        seen.add(t.lower())
        got = latest_good(t)
        if got is None:
            log[t] = {'status': 'not-in-archive' if not captures(t) else 'no-valid-capture'}
            absent.append(t); print(f'  {t}: {log[t]["status"]}', flush=True); continue
        ts, orig, h = got
        latest[t] = ts; log[t] = {'status': 200, 'snapshot': ts, 'url': orig}
        print(f'  {t}: {ts}', flush=True)
        todo += links(h)
    return latest, log, absent

# ---------- 2/3. older versions for rebuilt pages and the appendix ----------
def look_back(page, rx, must=None, min_lines=1):
    """Newest-first search of a page's captures for the first version that has the section. (ts) or None."""
    for ts, orig in captures(page):
        h = fetch_version(page, orig, ts)
        if h and valid(h) and recover.find_section(h, rx, must, min_lines): return ts
    return None

def has_section(page, ts, orig, rx, must=None, min_lines=1):
    h = fetch_version(page, orig, ts)
    return bool(h) and valid(h) and bool(recover.find_section(h, rx, must, min_lines))

def last_present(page, rx, must=None):
    """Newest version that has a section which was there from the oldest capture until it was removed.
    Bisects between the oldest capture (checked first) and the newest, so it fetches a handful of versions
    instead of scanning them all. If the section is not in the oldest capture the assumption does not hold
    and it falls back to the newest-first scan. Returns the timestamp or None."""
    vs = captures(page)   # newest first, so a smaller index is newer
    if not vs: return None
    has = lambda i: has_section(page, vs[i][0], vs[i][1], rx, must)
    oldest = len(vs) - 1
    if not has(oldest): return look_back(page, rx, must)
    if has(0): return vs[0][0]
    newer, older = 0, oldest   # newer: section absent, older: section present
    while older - newer > 1:
        mid = (newer + older) // 2
        if has(mid): older = mid
        else: newer = mid
    return vs[older][0]

def older_sources(latest, absent):
    wanted = {t.lower() for t in absent}
    found, extra = {}, {}
    for title, (parents, rx) in TARGETS.items():
        if title in latest or title.lower() not in wanted: continue
        for parent in parents:
            ts = look_back(parent, rx, min_lines=4)
            if ts: found[title] = (parent, ts); extra.setdefault(parent, set()).add(ts); break
        print(f'  rebuild {title}: ' + (f'{found[title][0]} {found[title][1]}' if title in found else 'NOT FOUND'), flush=True)
    for heading, page, rx, must, _ in APPENDIX:
        ts = last_present(page, rx, must)   # these sections date from the first capture, so bisect
        if ts: extra.setdefault(page, set()).add(ts)
        print(f'  appendix {heading}: ' + (f'{page} {ts}' if ts else 'NOT FOUND'), flush=True)
    return extra

# ---------- run ----------
if __name__ == '__main__':
    print('Pages (newest good capture, following links from the index):')
    latest, log, absent = discover()
    print('Older versions for rebuilt pages and the appendix:')
    extra = older_sources(latest, absent)
    json.dump(log, open(f'{RAW}/pages.json', 'w'), indent=1)
    json.dump(latest, open(f'{VER}/latest.json', 'w'), indent=1)
    files = [(t, version_path(t, ts)) for t, ts in latest.items()]
    files += [(p, version_path(p, ts)) for p, tss in extra.items() for ts in tss]
    print(f'Images used by {len(files)} page versions:')
    failed = crawl.images(crawl.inventory(('images',)), files)
    n_extra = sum(len(v) for v in extra.values())
    print(f'\nDone. {len(latest)} pages ({len(absent)} not archived), {n_extra} older versions kept for recovery/appendix, '
          f'{len(tally["versions_used"])} page versions touched in total '
          f'({tally["seeded_versions"]} from seed, {tally["network_versions"]} downloaded, {len(tally["corrupt"])} corrupt copies replaced); '
          f'{crawl.stats["seeded"]} files seeded, {crawl.stats["network"]} network requests.')
    if failed:
        sys.exit(f'\n{len(failed)} image download(s) FAILED, so they are missing from the manual for now: {", ".join(failed)}.\n'
                 'The archive has them. Re-run fetch.py to retry only those.')
