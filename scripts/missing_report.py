#!/usr/bin/env python3
"""Write MISSING.md: what the Wayback Machine did not have, from the saved manifests.

Reads images.json, recovered/index.json and versions/captures.json from the data folder and writes
MISSING.md next to them (copy it into notes/ to commit it).
Run:  python3 -I scripts/missing_report.py
"""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.environ.get('BIGBOX_RAW', f'{ROOT}/raw')   # archive data lives outside git; override with BIGBOX_RAW

images = json.load(open(f'{RAW}/images.json'))
recovered = json.load(open(f'{RAW}/recovered/index.json'))
captures = json.load(open(f'{RAW}/versions/captures.json'))

pages = json.load(open(f'{RAW}/pages.json'))
blocks = []   # (heading, intro, bullet list); written with blank lines around every heading and list

def block(heading, intro, items):
    blocks.append(f'## {heading}\n\n' + (intro + '\n\n' if intro else '') + ''.join(f'- {i}\n' for i in items))

rebuilt = []
for title, info in recovered.items():
    if title in ('Appendix_Older_Version_Content', 'Datasheets'): continue
    real = pages.get(title, {})
    if real.get('status') == 200:  # the build uses this real capture, whatever recover.py also extracted
        rebuilt.append(f'{title}: found as a real page under a later URL form (capture {real["snapshot"]})')
    elif info is None: rebuilt.append(f'{title}: not recoverable')
    else: rebuilt.append(f'{title}: rebuilt from {info["parent"]} {info["version"]} ({info["lines"]} lines)')
block('Pages with no archived copy of their own',
      'Their text was rebuilt from older versions of the pages that used to contain them (or, where noted, found under a later URL).', rebuilt)

no_caps = [t for t, rows in captures.items() if rows == []]
if no_caps: block('Pages with no captures under either wiki URL form', '', no_caps)
skipped = [t for t, v in pages.items() if v.get('status') == 'no-valid-capture']
if skipped: block('Pages left out because no capture is a real article', 'Stub pages such as "Coming Soon!".', skipped)

def seen_in(k):
    ps = sorted(set(images[k]['pages']))
    return f'{k} (seen in: {", ".join(ps[:3])}{"…" if len(ps) > 3 else ""})'

absent = sorted(k for k, v in images.items() if not v.get('kind') and not v.get('error') and not v.get('note'))
dead = sorted(k for k, v in images.items() if v.get('note'))
failed = sorted(k for k, v in images.items() if v.get('error'))
block(f'Images with no archived copy ({len(absent)} files)', 'The manual shows a placeholder with the original file name for each.', [seen_in(k) for k in absent])
if dead: block(f'Images the archive lists but cannot serve ({len(dead)} files)', 'Every capture in the archive index for these answers 404.', [seen_in(k) for k in dead])
if failed: block(f'Images that failed to download ({len(failed)} files)', 'The archive has these. Re-run `scripts/fetch.py` to retry them.', [seen_in(k) for k in failed])

kinds = {}
for v in images.values():
    k = (v.get('kind') or 'missing').split('-')[0]; kinds[k] = kinds.get(k, 0) + 1
block('Image totals', '', [f'{len(images)} distinct images: ' + ', '.join(f'{n} {k}' for k, n in sorted(kinds.items()))])
open(f'{RAW}/MISSING.md', 'w').write('# What the Wayback Machine does not have\n\n' + '\n'.join(blocks))
print(f'wrote {RAW}/MISSING.md: {len(absent)} images missing, {len(dead)} dead, {len(failed)} failed')
