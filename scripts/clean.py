#!/usr/bin/env python3
"""Classify saved page versions, then (with --apply) move the unwanted ones aside.

  error       archive/MediaWiki error page, no article body, or almost no text
  truncated   far shorter than both neighbours (probably a partial or broken capture)
  unchanged   article text identical to the previous kept version (only markup differs)

Moved files go to raw/versions_removed/<reason>/<Title>/ (reversible), never deleted.
The first version of each unchanged run and the last version of every page are always kept.
Writes CLEAN_REPORT.md and raw/versions/latest.json (latest good version per page).
Run:  python3 -I scripts/clean.py [--apply]
"""
import json, os, re, shutil, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.environ.get('BIGBOX_RAW', f'{ROOT}/raw')   # archive data lives outside git; override with BIGBOX_RAW
VER, REM = f'{RAW}/versions', f'{RAW}/versions_removed'
ns = {'__file__': f'{ROOT}/scripts/versions.py'}
exec(compile(open(f'{ROOT}/scripts/versions.py').read().split('if __name__')[0], 'versions', 'exec'), ns)
body_text = ns['body_text']

ERR = re.compile(r'Temporarily Offline|Internal Server Error|Service Unavailable|Gateway Time-?out|Bad Gateway|'
                 r'database error|MediaWiki internal error|Wayback Machine doesn.t have|Error 50\d|'
                 r'There is currently no text in this page|Hrm\. ', re.I)

def classify(t):
    d = f'{VER}/{t}'; vs = sorted(f[:-5] for f in os.listdir(d) if f.endswith('.html')); info = {}
    for v in vs:
        h = open(f'{d}/{v}.html').read(); L = body_text(h)
        why = None
        title = (re.search(r'<title>(.*?)</title>', h, re.S) or [0, ''])[1]
        if 'id="mw-content-text"' not in h: why = 'no article body'
        elif ERR.search(title) or ERR.search(h[:6000]): why = 'error text: ' + (ERR.search(title) or ERR.search(h[:6000])).group(0)
        elif len(L) < 5: why = f'only {len(L)} text lines'
        info[v] = {'lines': len(L), 'text': L, 'error': why}
    good = [v for v in vs if not info[v]['error']]
    for i, v in enumerate(good):  # truncated: < 50% of both neighbours' size
        if not 0 < i < len(good) - 1: continue  # first/last versions can't be a dip (early drafts are short)
        nb = [info[good[i - 1]]['lines'], info[good[i + 1]]['lines']]
        if info[v]['lines'] < 0.5 * min(nb):
            info[v]['truncated'] = f'{info[v]["lines"]} lines vs neighbours {nb}'
    return vs, info

def main(apply):
    report, latest = ['# Version clean-up report\n'], {}
    for t in sorted(os.listdir(VER)):
        if not os.path.isdir(f'{VER}/{t}') or not any(f.endswith('.html') for f in os.listdir(f'{VER}/{t}')): continue
        vs, info = classify(t)
        bad = {v: info[v]['error'] or ('truncated: ' + info[v]['truncated']) for v in vs if info[v]['error'] or info[v].get('truncated')}
        keep = [v for v in vs if v not in bad]
        unchanged, prev = [], None
        for v in keep:
            if prev is not None and info[v]['text'] == info[prev]['text'] and v != keep[-1]: unchanged.append(v); continue
            prev = v
        # last good version is "latest real version"; if it only duplicates text it still stays as the latest
        latest[t] = keep[-1] if keep else None
        report.append(f'## {t}\n- {len(vs)} versions: {len(bad)} error/truncated, {len(unchanged)} unchanged, {len(vs)-len(bad)-len(unchanged)} kept; latest good: {latest[t]}')
        report += [f'  - removed ({why}): {v}' for v, why in bad.items()] + [f'  - unchanged duplicate: {v}' for v in unchanged]
        if apply:
            for reason, group in (('errors', list(bad)), ('unchanged', unchanged)):
                for v in group:
                    os.makedirs(f'{REM}/{reason}/{t}', exist_ok=True)
                    shutil.move(f'{VER}/{t}/{v}.html', f'{REM}/{reason}/{t}/{v}.html')
    open(f'{RAW}/CLEAN_REPORT.md', 'w').write('\n'.join(report) + '\n')
    json.dump(latest, open(f'{VER}/latest.json', 'w'), indent=1)
    print('\n'.join(report))

if __name__ == '__main__': main('--apply' in sys.argv)
