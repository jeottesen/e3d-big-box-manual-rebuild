#!/usr/bin/env python3
"""Fetch the wiki-hosted PDF datasheets that apply to the BigBox (V6 hotend parts, NEMA17 motors, DC fans).

Uses the image CDX inventory (raw/cdx_images.json) to pick each file's newest PDF capture and saves it
to raw/files/ with a manifest. Skips Volcano / silicone heater mat / Super Whopper: not BigBox parts.
Polite: one connection, delay, retries. Run:  python3 -I scripts/fetch_files.py
"""
import json, os, urllib.parse
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # sibling modules (python -I does not add the script folder)
import crawl
from targets import WANT_FILES as WANT

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.environ.get('BIGBOX_RAW', f'{ROOT}/raw')   # archive data lives outside git; override with BIGBOX_RAW
os.makedirs(f'{RAW}/files', exist_ok=True)

caps = {}
for ts, orig, *_ in json.load(open(f'{RAW}/cdx_images.json')):
    name = urllib.parse.unquote(urllib.parse.urlparse(orig).path).rsplit('/', 1)[-1]
    if name.lower().endswith('.pdf'): caps.setdefault(name[:-4], []).append((ts, orig))

manifest_path = f'{RAW}/files.json'
manifest = json.load(open(manifest_path)) if os.path.exists(manifest_path) else {}
failed = []
for w in WANT:
    if w in manifest and os.path.exists(f'{RAW}/files/{w}.pdf'): continue
    seeded = json.load(open(f'{crawl.SEED}/files.json')).get(w) if crawl.SEED and os.path.exists(f'{crawl.SEED}/files.json') else None
    if seeded and crawl.from_seed(f'files/{w}.pdf'):
        manifest[w] = seeded; json.dump(manifest, open(manifest_path, 'w'), indent=1); print(w, 'from seed'); continue
    status = 'none'   # none: the archive has no usable PDF; failed: a download failed; ok
    for ts, orig in sorted(caps.get(w, []), reverse=True):  # newest capture first
        st, d = crawl.get_snapshot(f'https://web.archive.org/web/{ts}id_/{orig}', binary=True)
        if d is None: status = 'failed'; break   # do not fall back to an older datasheet because a download failed
        if d[:4] == b'%PDF':                      # a capture that downloaded but is not a PDF: try the next one
            open(f'{RAW}/files/{w}.pdf', 'wb').write(d)
            manifest[w] = {'snapshot': ts, 'url': orig, 'bytes': len(d)}; print(w, ts, len(d), flush=True); status = 'ok'; break
    if status != 'ok':
        manifest[w] = None
        print(w, 'DOWNLOAD FAILED' if status == 'failed' else 'NOT ARCHIVED', flush=True)
        if status == 'failed': failed.append(w)
    json.dump(manifest, open(manifest_path, 'w'), indent=1)
if failed: sys.exit(f'\n{len(failed)} datasheet download(s) FAILED: {", ".join(failed)}. The archive has them; re-run to retry only those.')
