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

lines = ['# What the Wayback Machine does not have\n',
         '## Pages with no archived copy of their own',
         'Their text was rebuilt from older versions of the pages that used to contain them (or, where noted, found under a later URL).\n']
pages = json.load(open(f'{RAW}/pages.json'))
for title, info in recovered.items():
    if title in ('Appendix_Older_Version_Content', 'Datasheets'): continue
    real = pages.get(title, {})
    if real.get('status') == 200:  # the build uses this real capture, whatever recover.py also extracted
        lines.append(f'- {title}: found as a real page under a later URL form (capture {real["snapshot"]})')
    elif info is None: lines.append(f'- {title}: not recoverable')
    else: lines.append(f'- {title}: rebuilt from {info["parent"]} {info["version"]} ({info["lines"]} lines)')

no_caps = [t for t, rows in captures.items() if rows == []]
lines += ['', '## Pages with no captures under either wiki URL form', *(f'- {t}' for t in no_caps)] if no_caps else []

miss = sorted(k for k, v in images.items() if not v.get('kind'))
lines += ['', f'## Images with no archived copy ({len(miss)} files)',
          'The manual shows a placeholder with the original file name for each.\n']
for k in miss:
    pages = sorted(set(images[k]['pages']))
    lines.append(f'- {k} (seen in: {", ".join(pages[:3])}{"…" if len(pages) > 3 else ""})')

kinds = {}
for v in images.values():
    kinds[(v.get('kind') or 'missing').split('-')[0]] = kinds.get((v.get('kind') or 'missing').split('-')[0], 0) + 1
lines += ['', '## Image totals', f'- {len(images)} distinct images: ' + ', '.join(f'{n} {k}' for k, n in sorted(kinds.items()))]
open(f'{RAW}/MISSING.md', 'w').write('\n'.join(lines) + '\n')
print(f'wrote {RAW}/MISSING.md: {len(miss)} images missing')
