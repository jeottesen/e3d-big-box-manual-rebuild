#!/usr/bin/env python3
"""The printed parts the manual itself names in its step lists. Standard library only.

A step's parts list in the manual has items like "2 x Drive Supports (Printed Parts)." or "8 x Printed Feet (Printed Parts Box)." The
exploded drawings do not cover every one of them, so the Bill of Materials adds the rest, linked to the step that lists them. The ones a
drawing does cover are named in MANUAL_PART_NAMES (scripts/targets.py), which says which row of which drawing each one is.

    python3 -I scripts/manual_parts.py     list what the manual names and what each one is in the Bill of Materials
"""
import html, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # sibling modules (python -I does not add the script folder)
from sections import HEADING, NOT_BUILD_PAGES, STEP
from ocr_text import key

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = f'{ROOT}/docs'
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


def group(entries, mapping):
    """(covered, no_drawing). covered: [(entry, sheet id, the drawing's name for the part)] for entries whose manual name is in `mapping`.
    no_drawing: one record per other part, in the manual's order, linking every step that lists it (a part listed in a preparation step and
    again in the step that fits it is one part)."""
    covered, grouped = [], {}
    for e in entries:
        if e['part'] in mapping: covered.append((e, *mapping[e['part']])); continue
        g = grouped.setdefault(key(e['part']), {'part': e['part'], 'qty': e['qty'], 'container': e['container'], 'steps': []})
        g['qty'] = max(g['qty'], e['qty'])
        step = (e['page'], e['step_id'], e['step'])
        if step not in g['steps']: g['steps'].append(step)
    return covered, list(grouped.values())


def main():
    from targets import MANUAL_PART_NAMES
    pages = read_pages()
    found = scan(pages)
    covered, none = group(found, MANUAL_PART_NAMES)
    for e, sheet, name in covered: print(f'{e["qty"]} x {e["part"]:34} -> {sheet} {name}  ({e["step"]})')
    for g in none: print(f'{g["qty"]} x {g["part"]:34} no drawing  [{g["container"]}]  ({"; ".join(st[2] for st in g["steps"])})')
    stale = [n for n in MANUAL_PART_NAMES if n not in {e['part'] for e in found}]
    for n in stale: print(f'STALE: {n!r} is in MANUAL_PART_NAMES but the manual no longer names it')
    for slug, text in unparsed(pages): print(f'UNREAD: {slug}: {text}')
    return 1 if stale or unparsed(pages) else 0


if __name__ == '__main__': sys.exit(main())
