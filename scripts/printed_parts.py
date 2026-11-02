#!/usr/bin/env python3
"""The STEP files of the printed parts (downloads/printed-parts/), and which Bill of Materials row each one belongs to.

downloads/printed-parts/parts.csv has one row per file (the file is in parts/). Its `name` column is the Bill of Materials
name, so the links on the Bill of Materials page are made from it here and never typed. Four things are not a plain match:

  - a part that comes in two shapes has one file each, told apart by the `variant` column (`dual` / `regular`); the dual one goes by
    the name with DUAL added (X-AXIS CARRIAGE BEARING CLAMP DUAL)
  - `NAME (4 hole)` is the alternate for the newer screw: it is linked on the row of NAME
  - `NAME (R)` with no row of its own is the mirror image of the `NAME (L)` row: it is linked on that row
  - the rest have no row (parts the Bill of Materials does not list yet): they are listed after the table

Run:  python3 -I scripts/printed_parts.py   (lists what matched and what did not)
"""
import csv, os, re, sys, urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR = 'downloads/printed-parts'
CSV = f'{ROOT}/{DIR}/parts.csv'


def load(path=CSV):
    with open(path, newline='') as f: return list(csv.DictReader(f))


def bom_name(row):
    """The name a file goes by in the Bill of Materials."""
    return row['name'] + ' DUAL' if row['variant'] == 'dual' else row['name']


def href(row):
    """The link to a file from a page in docs/ or manual/ (both are one folder below the repository root)."""
    return f'../{DIR}/' + '/'.join(urllib.parse.quote(p) for p in row['file'].split('/'))


def classify(rows, bom_names):
    """(main, alternates, mirrors, extras): main {bom name: row}; alternates {bom name: [row]}; mirrors {bom name: row}; extras [row]."""
    names = set(bom_names)
    main, alternates, mirrors, extras = {}, {}, {}, []
    for r in rows:
        n = bom_name(r)
        if n in names: main[n] = r; continue
        base = n[:-len(' (4 hole)')] if n.endswith(' (4 hole)') else None
        left = re.sub(r'\(R\)$', '(L)', n) if n.endswith('(R)') else None
        if base in names: alternates.setdefault(base, []).append(r)
        elif left in names: mirrors[left] = r
        else: extras.append(r)
    return main, alternates, mirrors, extras


def page_of(row):
    """(manual page, section heading) a row's `manual_url` and `section` columns name, or None."""
    m = re.search(r'/manual/([^#/]+)\.md', row['manual_url'])
    return (m.group(1), row['section']) if m and row['section'] else None


def main():
    md = open(f'{ROOT}/manual/Bill_Of_Materials.md').read()
    table = md[md.index('Printed Parts'):md.index('## Fixings')]
    names = [c.strip() for c in (l.strip('|').split('|')[0] for l in table.splitlines() if l.startswith('| ') and not l.startswith('| Part') and not l.startswith('| ---'))]
    rows = load()
    got, alternates, mirrors, extras = classify(rows, names)
    print(f'{len(rows)} files: {len(got)} on a row, {sum(map(len, alternates.values()))} alternates, {len(mirrors)} mirrors, {len(extras)} with no row')
    for r in extras: print('  no row:', r['name'])
    for n in names:
        if n not in got: print('  no file:', n)
    return 0


if __name__ == '__main__': sys.exit(main())
