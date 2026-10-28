#!/usr/bin/env python3
"""Fetch the wiki-hosted PDF datasheets that apply to the BigBox (V6 hotend parts, NEMA17 motors, DC fans).

Uses the image CDX inventory (raw/cdx_images.json) to pick each file's newest PDF capture and saves it
to raw/files/ with a manifest. Skips Volcano / silicone heater mat / Super Whopper: not BigBox parts.
Polite: one connection, delay, retries. Run:  python3 -I scripts/fetch_files.py
"""
import gzip, json, os, time, urllib.error, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.environ.get('BIGBOX_RAW', f'{ROOT}/raw')   # archive data lives outside git; override with BIGBOX_RAW
UA = 'bigbox-manual-archiver/2.0 (personal documentation backup; single connection)'
WANT = ['V6-175-ASSM', 'V6-175-BREAK', 'V6-175-SINK', 'V6-300-BREAK', 'V6-300-SINK-D', 'V6-BLOCK-CARTRIDGE',
        'V6-NOZZLE-ALL', 'E-MOTOR-NEMA17-ALL_PUBLIC', 'Motor-Datasheet-All', 'DC_Fans']
os.makedirs(f'{RAW}/files', exist_ok=True)

def fetch(url, tries=4):
    for i in range(tries):
        time.sleep(2.5)
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': UA}), timeout=120) as r:
                d = r.read()
                return gzip.decompress(d) if d[:2] == b'\x1f\x8b' else d
        except urllib.error.HTTPError as e:
            if e.code in (403, 404, 410): return None
        except Exception: pass
        time.sleep(20 * 2 ** i)
    return False

caps = {}
for ts, orig, *_ in json.load(open(f'{RAW}/cdx_images.json')):
    name = urllib.parse.unquote(urllib.parse.urlparse(orig).path).rsplit('/', 1)[-1]
    if name.lower().endswith('.pdf'): caps.setdefault(name[:-4], []).append((ts, orig))

manifest_path = f'{RAW}/files.json'
manifest = json.load(open(manifest_path)) if os.path.exists(manifest_path) else {}
for w in WANT:
    if w in manifest and os.path.exists(f'{RAW}/files/{w}.pdf'): continue
    for ts, orig in sorted(caps.get(w, []), reverse=True):  # newest capture first; fall back if one is bad
        d = fetch(f'https://web.archive.org/web/{ts}id_/{orig}')
        if d and d[:4] == b'%PDF':
            open(f'{RAW}/files/{w}.pdf', 'wb').write(d)
            manifest[w] = {'snapshot': ts, 'url': orig, 'bytes': len(d)}; print(w, ts, len(d), flush=True); break
    else:
        manifest[w] = None; print(w, 'NOT FETCHED', flush=True)
    json.dump(manifest, open(manifest_path, 'w'), indent=1)
