#!/usr/bin/env python3
"""Read the parts list off each sheet of the BigBox exploded drawings (EXPLODED_DRAWINGS.pdf).

The PDF is vector, so its text can be read exactly; no OCR is involved. Each sheet has a PARTS LIST table
(ITEM, QTY, PART NUMBER, DESCRIPTION) and a title block with the sheet title and "n / N" sheet number.
The pdf text comes out one glyph at a time with its position, so rows and columns are rebuilt from positions.

It needs a third-party package (pypdf, in requirements.txt), so it runs as its own step, `extract`, only when its
inputs change, and writes notes/parts.json, which the build reads:

    mise run extract        (or: python3 -I scripts/drawings.py [--pdf FILE] in the venv from requirements.txt)

Output: notes/parts.json, one entry per sheet: title, sheet number, and the parts list rows. Rows that do not
look right (item numbers that do not run 1..n, an empty field) are listed under "problems" for a manual look.
"""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # sibling modules (python -I does not add the script folder)
import crawl
from pypdf import PdfReader

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = f'{ROOT}/notes/parts.json'
PDF_URL = 'http://files.e3d-online.com/BigBox/EXPLODED_DRAWINGS.pdf'
PDF_TS = '20160109071827'
PDF_PATH = f'{crawl.RAW}/drawings/EXPLODED_DRAWINGS.pdf'   # not under files/, which the build publishes

def get_pdf():
    if len(sys.argv) > 2 and sys.argv[1] == '--pdf': return sys.argv[2]
    if not os.path.exists(PDF_PATH) and not crawl.from_seed('drawings/EXPLODED_DRAWINGS.pdf'):
        st, data = crawl.get_snapshot(crawl.snap(PDF_URL, PDF_TS, 'id_'), binary=True)
        if not data: sys.exit(f'Could not download the exploded drawings (status {st}).')
        os.makedirs(os.path.dirname(PDF_PATH), exist_ok=True); open(PDF_PATH, 'wb').write(data)
    return PDF_PATH

def glyphs(page):
    out = []
    def visit(text, cm, tm, font_dict, size):
        if text: out.append((tm[4], tm[5], text, size or 10))
    page.extract_text(visitor_text=visit)
    return out

def words(gl, ytol=2.0, gap=10.0, split_x=None):
    """Join glyphs into text runs per line; a gap wider than `gap` points starts a new run (the next table cell)."""
    lines = []
    for x, y, t, s in sorted(gl, key=lambda g: (-g[1], g[0])):
        for ln in lines:
            if abs(ln['y'] - y) <= ytol: ln['g'].append((x, t, s)); break
        else: lines.append({'y': y, 'g': [(x, t, s)]})
    out = []
    for ln in lines:
        cur, start, last, last_x = '', None, None, None
        for x, t, s in sorted(ln['g']):
            forced = split_x is not None and last is not None and last_x < split_x <= x   # a long part name can run right into the next cell
            if last is not None and (x - last > gap or forced) and cur.strip():
                out.append((start, ln['y'], cur.strip())); cur, start = '', None
            if start is None: start = x
            cur += t; last = x + s * 0.55 * len(t); last_x = x
        if cur.strip(): out.append((start, ln['y'], cur.strip()))
    return out

def table_rows(ws):
    """Rows of the PARTS LIST table from text runs (x, y, text). Returns [] when the sheet has no table in its text."""
    head = next((w for w in ws if w[2].upper() == 'PARTS LIST'), None)
    if not head: return []
    # The table's position and column widths differ from sheet to sheet, but its shape does not: every row is
    # item, qty, part number, description, left to right. The table's left edge is where the ITEM heading starts.
    hy = head[1] - 16
    left = min((x for x, y, t in ws if abs(y - hy) < 6 and t.upper().startswith('ITEM')), default=None)
    if left is None: return []
    by = {}
    for x, y, t in ws:
        if left - 6 <= x <= left + 330 and y < hy - 6: by.setdefault(round(y / 3), []).append((x, t))
    rows, last_y = [], hy
    for k in sorted(by, reverse=True):
        y = k * 3
        if last_y - y > 22: break   # a gap this size is the end of the table (rows are about 12 points apart)
        cells = [(x, t) for x, t in sorted(by[k])]
        if len(cells) >= 3 and re.fullmatch(r'\d+(\.\d+)?', cells[0][1]) and cells[1][1].isdigit():   # assembly sheets leave DESCRIPTION empty
            rows.append({'item': cells[0][1], 'qty': cells[1][1], 'part': cells[2][1], 'description': ' '.join(t for x, t in cells[3:]), '_x': cells[3][0] if len(cells) > 3 else None}); last_y = y
    return rows

def sheet(page):
    gl = glyphs(page)
    ws = words(gl)
    rows = table_rows(ws)
    xs = [r['_x'] for r in rows if r['_x'] is not None]
    if xs:   # the description column starts at the same x on every row of a sheet; re-read with a split there in case a part name ran into it
        dx = max(set(round(x) for x in xs), key=[round(x) for x in xs].count)
        again = table_rows(words(gl, split_x=dx - 1))
        described = lambda rs: sum(1 for r in rs if r['description'])
        if len(again) >= len(rows) and described(again) > described(rows): rows = again   # a glued row has no description of its own
    for r in rows:
        r.pop('_x')
        glued = re.fullmatch(r'(.*?[a-z)\d])(Fixings (?:Kit )?Bag \d+)', r['part'])   # a sheet with no other description cells gives no column to split at
        if glued and not r['description']: r['part'], r['description'] = glued.group(1), glued.group(2)
    full = ' '.join(w[2] for w in ws)
    n = re.search(r'(?<![\d/])(\d{1,2})\s*/\s*(\d{1,2})(?![\d/])', full)
    return {'sheet': int(n.group(1)) if n else None, 'of': int(n.group(2)) if n else None, 'rows': rows, '_words': ws}

def title(ws):
    """The sheet title is the large line in the title block, above 'E3D BigBox Part Explosions' (bottom right of the sheet)."""
    return ' '.join(t for x, y, t in sorted(ws, key=lambda w: w[0]) if 55 < y < 80 and x > 500).strip()

def main():
    reader = PdfReader(get_pdf())
    sheets, problems, notes = [], [], []
    for i, page in enumerate(reader.pages, 1):
        s = sheet(page)
        s['title'] = title(s.pop('_words'))
        s['page'] = i
        items = [int(r['item']) for r in s['rows'] if '.' not in r['item']]   # sub-items (11.1, 11.2) belong to their parent
        lines = (page.extract_text() or '').splitlines()
        if not s['rows'] and 'PARTS LIST' not in lines:
            s['blank'] = True   # nothing but the title block: a blank sheet in the PDF, nothing to read
            notes.append(f'sheet {i}: blank in the PDF (no parts list, no title)'); sheets.append(s); continue
        if not s['rows']: problems.append(f'sheet {i}: a parts list is in the text but no rows could be read')
        elif len(set(items)) != len(items) or 1 not in items: problems.append(f'sheet {i}: item numbers {items} repeat or have no item 1; check against the drawing')
        elif items != list(range(1, len(items) + 1)): notes.append(f'sheet {i}: item numbers are not 1..n in order (as on the drawing): {items}')
        if not s['title']: problems.append(f'sheet {i}: no title found')
        # cross-check: the plain text extraction lists the table as one line per row, between the header and the title block
        if 'PARTS LIST' in lines:
            start = lines.index('PARTS LIST') + 2
            end = next((n for n, l in enumerate(lines) if l.startswith('E3D BigBox Part Explosions')), len(lines))
            if end - start != len(s['rows']): problems.append(f'sheet {i}: read {len(s["rows"])} rows but the text has {end - start} table lines')
        sheets.append(s)
    json.dump({'source': f'{PDF_URL} (archived {PDF_TS})', 'sheets': sheets, 'problems': problems, 'notes': notes}, open(OUT, 'w'), indent=1, ensure_ascii=False)
    print(f'{len(sheets)} sheets, {sum(len(s["rows"]) for s in sheets)} parts rows, {len(problems)} problems, {len(notes)} notes -> {OUT}')
    for p in problems + notes: print('  ', p)

if __name__ == '__main__': main()
