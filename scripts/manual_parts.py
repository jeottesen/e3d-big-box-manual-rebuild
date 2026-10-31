#!/usr/bin/env python3
"""The printed parts the manual itself names in its step lists. Standard library only.

A step's parts list in the manual has items like "2 x Drive Supports (Printed Parts)." or "8 x Printed Feet (Printed Parts Box)." The
exploded drawings do not cover every one of them, so the Bill of Materials adds the rest from here, linked to the step that lists them.
The reviewed list is data/manual_parts.json: each item records which drawing sheet covers it (or null if no drawing does).

    python3 -I scripts/manual_parts.py              compare the manual (docs/*.html) with the reviewed list; exit 1 if they differ
    python3 -I scripts/manual_parts.py --add-new    add what the manual has and the list lacks, with no drawing, for a person to review
"""
import html, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # sibling modules (python -I does not add the script folder)
from sections import HEADING, NOT_BUILD_PAGES, STEP
from ocr_text import key

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = f'{ROOT}/docs'
DATA = f'{ROOT}/data/manual_parts.json'
ITEM = re.compile(r'<li>\s*(\d+) x (.+?) \((Printed [Pp]arts?(?: [Bb]ox| [Bb]ag)?)\)\.?\s*</li>')   # the wiki is not tidy: a stray space after the full stop
CONTAINERS = {'printed part': 'printed', 'printed parts': 'printed', 'printed parts box': 'printed-parts-box', 'printed parts bag': 'printed-parts-bag'}
CONTAINER_LABEL = {'printed': 'printed', 'printed-parts-box': 'from the Printed Parts Box', 'printed-parts-bag': 'from the Printed Parts Bag'}


def scan(pages):
    """[entry] for every "N x NAME (Printed ...)" list item in the pages ({page slug: html}), in the manual's order. Each entry names the step
    (the nearest heading above it that starts with a step number, else the nearest heading) and has drawing=None."""
    out = []
    for slug, body in pages.items():
        if slug in NOT_BUILD_PAGES or slug in ('index', 'manual'): continue
        marks = []
        for m in HEADING.finditer(body):
            found = re.search(r'\bid="([^"]+)"', m.group(2) + m.group(3))
            if found: marks.append((m.start(), 'h', (int(m.group(1)), html.unescape(found.group(1)), ' '.join(html.unescape(re.sub(r'<[^>]+>', '', m.group(3))).split()))))
        marks += [(m.start(), 'i', m) for m in ITEM.finditer(body)]
        stack = []
        for _, kind, v in sorted(marks, key=lambda x: x[0]):
            if kind == 'h':
                while stack and stack[-1][0] >= v[0]: stack.pop()
                stack.append(v)
            else:
                step = next((h for h in reversed(stack) if STEP.match(h[2])), stack[-1] if stack else (0, None, slug.replace('_', ' ')))
                out.append({'page': slug, 'step_id': step[1], 'step': step[2], 'qty': int(v.group(1)), 'part': html.unescape(v.group(2)).strip(),
                            'container': CONTAINERS[v.group(3).lower()], 'drawing': None, 'note': ''})
    return out


def unparsed(pages):
    """List items that mention "(Printed" but that scan() does not take: a layout it does not know yet."""
    out = []
    for slug, body in pages.items():
        if slug in NOT_BUILD_PAGES or slug in ('index', 'manual'): continue
        out += [(slug, ' '.join(html.unescape(re.sub(r'<[^>]+>', '', li)).split())[:120]) for li in re.findall(r'<li>.*?</li>', body, re.S) if re.search(r'\(printed', li, re.I) and not ITEM.fullmatch(li)]
    return out


def read_pages(docs=DOCS):
    pages = {}
    for f in sorted(os.listdir(docs)):
        if f.endswith('.html'):
            with open(f'{docs}/{f}', encoding='utf-8') as fh: pages[f[:-5]] = fh.read()
    return pages


def ident(e): return (e['page'], e['step_id'], key(e['part']))


def load(path=DATA):
    if not os.path.exists(path): return []
    with open(path, encoding='utf-8') as f: return json.load(f)['parts']


def problems(entries, sheet_ids):
    """What is wrong with the reviewed list. sheet_ids: the ids in data/sheets."""
    out, seen = [], set()
    for i, e in enumerate(entries):
        if not isinstance(e, dict): out.append(f'entry {i}: must be an object'); continue
        if not (isinstance(e.get('part'), str) and e['part']): out.append(f'entry {i}: no part')
        if not (isinstance(e.get('qty'), int) and not isinstance(e.get('qty'), bool) and e['qty'] >= 1): out.append(f'entry {i}: qty must be a whole number')
        if e.get('container') not in CONTAINER_LABEL: out.append(f'entry {i}: container must be one of {sorted(CONTAINER_LABEL)}')
        if not (isinstance(e.get('page'), str) and isinstance(e.get('step'), str)): out.append(f'entry {i}: needs page and step')
        if e.get('drawing') is not None and e['drawing'] not in sheet_ids: out.append(f'entry {i} ({e.get("part")}): drawing {e["drawing"]!r} is not a sheet in data/sheets')
        if isinstance(e.get('part'), str) and isinstance(e.get('page'), str):
            k = ident(e) if e.get('step_id') is not None or True else None
            if k in seen: out.append(f'entry {i} ({e["part"]}): listed twice for the same step')
            seen.add(k)
    return out


def diff(found, reviewed):
    """[(kind, message)] between what the manual lists and the reviewed list."""
    f, r = {ident(e): e for e in found}, {ident(e): e for e in reviewed}
    out = [('new', f'in the manual but not in the list: {e["qty"]} x {e["part"]} ({e["step"]}, {e["page"]})') for k, e in f.items() if k not in r]
    out += [('gone', f'in the list but not in the manual: {e["qty"]} x {e["part"]} ({e["step"]}, {e["page"]})') for k, e in r.items() if k not in f]
    out += [('changed', f'quantity differs for {e["part"]} ({e["step"]}): manual {f[k]["qty"]}, list {e["qty"]}') for k, e in r.items() if k in f and f[k]['qty'] != e['qty']]
    return out


def main(argv):
    found, reviewed = scan(read_pages()), load()
    differences = diff(found, reviewed)
    if '--add-new' in argv:
        have = {ident(e) for e in reviewed}
        new = [e for e in found if ident(e) not in have]
        os.makedirs(os.path.dirname(DATA), exist_ok=True)
        with open(DATA, 'w', encoding='utf-8') as fh:
            json.dump({'source': 'the "(Printed Part...)" items in the manual\'s step lists; see scripts/manual_parts.py', 'parts': reviewed + new}, fh, indent=1, ensure_ascii=False); fh.write('\n')
        print(f'added {len(new)} entries with no drawing; set "drawing" to a sheet id where one covers the part')
        return 0
    for kind, msg in differences: print(f'{kind:8}{msg}')
    print(f'\n{len(found)} printed parts in the manual, {len(reviewed)} in the list, {len(differences)} differences.')
    return 1 if differences else 0


if __name__ == '__main__': sys.exit(main(sys.argv[1:]))
