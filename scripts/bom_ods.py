#!/usr/bin/env python3
"""E3D's own Bill of Materials spreadsheet (data/bom.ods, from bom.zip on the BigBox Thingiverse page) and how its Fixings sheet lines up with the
fixings the manual compiled from the exploded drawings.

The Fixings sheet lists every fixing in the kit by bag: description, quantity required and quantity supplied. The Bill of Materials page shows that list,
with the drawings that show each fixing beside it. A drawing's name for a fixing is matched to the sheet's by what it says (size, kind, finish ignored),
and the few that differ in wording more than that are in ALIASES. The sheet is trusted over the drawings: the page shows its bags, quantities and
names, and a fixing only the drawings show (their text was read by OCR for the image-only sheets) is not listed. The General sheet is the list of
everything else in the kit, by product (Lite, Pro, Dual).

Standard library only (an .ods file is a zip of XML).  Run:  python3 -I scripts/bom_ods.py   (lists the matches and the conflicts)
"""
import os, re, sys, zipfile
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ODS = f'{ROOT}/data/bom.ods'
NS = {'table': 'urn:oasis:names:tc:opendocument:xmlns:table:1.0', 'text': 'urn:oasis:names:tc:opendocument:xmlns:text:1.0'}
T, X = '{%s}' % NS['table'], '{%s}' % NS['text']

# Drawing names that do not say the same thing as the sheet's, even with the finish and the plural ignored: drawing name -> sheet description.
ALIASES = {'Nylon Washer 8 x 16 x 1.6': 'Nylon Washer - 8mm ID x 18mm OD x 1.6-1.8mm T',
           'Nylon Spacer 3.2ID 6OD 15L': 'Nylon Spacer - 3-3.2mm ID x 6mm OD x 15 L'}


def sheet(name, path=ODS):
    """The rows of one sheet of the spreadsheet as lists of cell text (empty cells kept up to the last non-empty one)."""
    with zipfile.ZipFile(path) as z: root = ET.fromstring(z.read('content.xml'))
    for tab in root.iter(T + 'table'):
        if tab.get(T + 'name') != name: continue
        rows = []
        for tr in tab.iter(T + 'table-row'):
            cells = []
            for c in tr:
                if c.tag not in (T + 'table-cell', T + 'covered-table-cell'): continue
                text = ' '.join(''.join(p.itertext()) for p in c.iter(X + 'p'))
                cells += [text] * min(int(c.get(T + 'number-columns-repeated', '1')), 30)
            while cells and not cells[-1]: cells.pop()
            if cells: rows += [cells] * min(int(tr.get(T + 'number-rows-repeated', '1')), 1)
        return rows
    raise KeyError(name)


def fixings(path=ODS):
    """[{bag, description, required, supplied}] from the Fixings sheet, in the sheet's order."""
    out = []
    for r in sheet('Fixings', path):
        if len(r) >= 5 and r[1].strip().isdigit():
            out.append({'bag': int(r[1]), 'description': r[2].strip().replace('Knruled', 'Knurled'), 'required': int(r[3]), 'supplied': int(r[4])})   # a typo in the sheet
    return out


def signature(name):
    """What a fixing's name says, without the wording around it: a set of words (size, kind, 'half'...), the finish and the plural left out."""
    s = name.lower().replace('skt', 'socket').replace('csk', 'countersunk')
    s = re.sub(r'platite 30|a2 s/s|\ba2\b|\bbzp\b|\brec\b', ' ', s)
    words = [w[:-1] if w in ('nuts', 'screws', 'washers', 'standoffs') else w for w in re.split(r'[\s()\-,/]+', s) if w]
    return frozenset(w for w in words if w not in ('x', 'a'))


def match(drawn, official):
    """{drawn name: official row} for the drawing names that say the same as a row of the sheet; unmatched names are left out."""
    by = {}
    for o in official: by.setdefault(signature(o['description']), []).append(o)
    out = {}
    for name in drawn:
        rows = by.get(signature(ALIASES.get(name, name)), [])
        if len(rows) == 1: out[name] = rows[0]
    return out


def general(path=ODS):
    """[{category, sub, location, component, lite, pro, dual}] from the General sheet, in the sheet's order (a quantity the sheet leaves empty is '')."""
    out = []
    for r in sheet('General', path)[2:]:   # the first two rows are the headings
        r = r + [''] * (7 - len(r))
        out.append(dict(zip(('category', 'sub', 'location', 'component', 'lite', 'pro', 'dual'), (c.strip() for c in r[:7]), strict=True)))
    return out


def main():
    import glob, json
    drawn = {}
    for f in glob.glob(f'{ROOT}/data/sheets/*.json'):
        for r in json.load(open(f))['rows']:
            if r['description'].upper().startswith('FIXINGS'): drawn[r['part']] = int(re.sub(r'\D', '', r['description']) or 0)
    off = fixings()
    m = match(drawn, off)
    print(f'{len(off)} fixings on the sheet; {len(drawn)} named by the drawings, {len(m)} matched')
    for n in sorted(drawn):
        if n not in m: print('  not on the sheet:', n)
    print('  only on the sheet:', len([o for o in off if o not in m.values()]), '; General sheet rows:', len(general()))
    return 0


if __name__ == '__main__': sys.exit(main())
