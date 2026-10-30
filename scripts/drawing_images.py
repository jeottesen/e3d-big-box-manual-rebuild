#!/usr/bin/env python3
"""Read the parts list off the exploded-drawing sheets that the wiki embedded as images (docs/images/*.jpg).

Some of these sheets are newer than the archived PDF that drawings.py reads (the PDF has 29 sheets, the wiki's images
come from a 36-sheet revision) and some sheets are not in the PDF at all. Images have no text layer, so this script
uses OCR (rapidocr, which bundles its models). It looks for the PARTS LIST table on each drawing-shaped image, rebuilds
the rows from the OCR text positions, and writes notes/parts_images.json.

Like drawings.py it needs third-party packages (requirements.txt), so it runs as its own step, `extract`, only when its inputs change:

    mise run extract        (or: python3 -I scripts/drawing_images.py in the venv from requirements.txt)

The OCR drops the spaces inside names, so names are matched to the exact strings read from the PDF (notes/parts.json)
where possible and re-spaced by rule otherwise. Every sheet is checked (item numbers, quantities, OCR confidence);
anything doubtful is listed under "problems" for a manual look.
"""
import json, os, re, sys
import numpy as np
from PIL import Image
from rapidocr_onnxruntime import RapidOCR

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # sibling modules (python -I does not add the script folder)
import crawl
from targets import OCR_FIXES, SHEET_IMAGES
from ocr_text import MIN_CONF, key, vocabulary, parts_by_description, respace, fix_row
IMAGES = f'{ROOT}/docs/images'
OUT = f'{ROOT}/notes/parts_images.json'
REVIEW = f'{ROOT}/notes/OCR_REVIEW.md'
BY_DESC = None   # set in main()
FIXES = {re.sub(r'[^A-Z0-9]', '', k.upper()): v for k, v in OCR_FIXES.items()}   # hand corrections, found by name without spaces or case

def orig(f):
    """The image as the wiki had it: an enlarged one keeps its original in images/original/."""
    return f'{IMAGES}/original/{f}' if os.path.exists(f'{IMAGES}/original/{f}') else f'{IMAGES}/{f}'

def candidates():
    """Drawing-shaped images: landscape A4 ratio, wide enough to read, and an upper-case file name (the wiki's sheet names)."""
    out = []
    for f in sorted(os.listdir(IMAGES)):
        stem, ext = os.path.splitext(f)
        if f in SHEET_IMAGES or ext.lower() not in ('.jpg', '.jpeg', '.png') or stem != stem.upper() or not re.search(r'[A-Z]', stem): continue   # SHEET_IMAGES are drawn from the PDF already
        w, h = Image.open(orig(f)).size
        if w >= 700 and 1.38 <= w / h <= 1.45: out.append(f)
    return out

def read(ocr, path):
    im = Image.open(path).convert('RGB')
    scale = max(1.0, 2400 / im.width)
    if scale > 1: im = im.resize((round(im.width * scale), round(im.height * scale)), Image.LANCZOS)
    res, _ = ocr(np.array(im))
    words = []
    for box, text, conf in res or []:
        xs = [p[0] for p in box]; ys = [p[1] for p in box]
        words.append({'x': min(xs), 'cy': sum(ys) / 4, 'h': max(ys) - min(ys), 't': text.strip(), 'c': float(conf)})
    return im.size, words

def table(words, vocab):
    head = next((w for w in words if key(w['t']) == 'PARTSLIST'), None)
    if not head: return None, ['no PARTS LIST heading found']
    hdr = [w for w in words if abs(w['cy'] - head['cy'] - 2.2 * head['h']) < 1.6 * head['h'] and key(w['t']) in ('ITEM', 'QTY', 'PARTNUMBER', 'DESCRIPTION', 'ITEMQTY')]
    item = next((w for w in hdr if key(w['t']).startswith('ITEM')), None)
    if not item: return None, ['no ITEM column heading found']
    hh = item['h']
    cells = [w for w in words if w['cy'] > item['cy'] + 0.45 * hh and item['x'] - hh <= w['x'] <= item['x'] + 0.45 * 2400]
    rows, problems = [], []
    cells.sort(key=lambda w: w['cy'])
    groups = []
    for w in cells:
        if groups and abs(w['cy'] - groups[-1][-1]['cy']) < 0.6 * hh: groups[-1].append(w)
        else: groups.append([w])
    last = item['cy']; spacing = None
    for g in groups:
        g.sort(key=lambda w: w['x']); cy = sum(w['cy'] for w in g) / len(g)
        if spacing and cy - last > 2.2 * spacing: break   # a gap this size is the end of the table
        texts = [w['t'] for w in g]
        if texts and texts[0] in ('l', 'I', '|'): texts[0] = '1'
        if len(texts) >= 3 and re.fullmatch(r'\d+(\.\d+)?', texts[0]) and texts[1].isdigit(): num, qty, rest = texts[0], texts[1], texts[2:]
        elif len(texts) >= 3 and texts[0].isdigit() and not texts[1].isdigit(): num, qty, rest = '', texts[0], texts[1:]   # the narrow ITEM column is sometimes not read
        else: num = None
        if num is not None:
            read_part = respace(rest[0], vocab); read_desc = respace(' '.join(rest[1:]), vocab) if len(rest) > 1 else ''   # what the OCR gave, with the spaces put back
            conf = round(min(w['c'] for w in g), 2)
            fixed_part, fixed_desc, by_hand = fix_row(read_part, read_desc, conf, vocab, BY_DESC, FIXES)
            row = {'item': num, 'qty': qty, 'part': fixed_part, 'description': fixed_desc, 'confidence': conf}
            if (fixed_part, fixed_desc) != (read_part, read_desc): row['ocr'] = {'part': read_part, 'description': read_desc}   # what the OCR gave, before the correction
            # a missing item number does not matter; a row is for review when the OCR was unsure and the text is not a string known from the PDF
            known = lambda t: not t or key(t) in vocab
            row['review'] = not by_hand and conf < MIN_CONF and not (known(fixed_part) and known(fixed_desc) and conf >= 0.6)
            rows.append(row)
            if last != item['cy']: spacing = cy - last
            last = cy
        elif rows: continue   # text from the drawing itself, not a row
    return rows, problems

def main():
    global BY_DESC
    sheets_pdf = json.load(open(f'{ROOT}/notes/parts.json'))['sheets'] if os.path.exists(f'{ROOT}/notes/parts.json') else []
    vocab, BY_DESC = vocabulary(sheets_pdf), parts_by_description(sheets_pdf)
    matched = json.load(open(f'{ROOT}/notes/sheet_matches.json'))['matches'] if os.path.exists(f'{ROOT}/notes/sheet_matches.json') else {}
    ocr = RapidOCR()
    sheets, problems = [], []
    for f in candidates():
        (w, h), words = read(ocr, orig(f))
        rows, probs = table(words, vocab)
        n = next((re.fullmatch(r'(\d{1,2})\s*/\s*(\d{1,2})', x['t']) for x in words if x['x'] > 0.7 * w and x['cy'] > 0.88 * h and re.fullmatch(r'(\d{1,2})\s*/\s*(\d{1,2})', x['t'])), None)
        title = os.path.splitext(f)[0].replace('_', ' ')
        entry = {'image': f, 'title': title, 'sheet': int(n.group(1)) if n else None, 'of': int(n.group(2)) if n else None, 'rows': rows or [],
                 'in_pdf': matched.get(f, {}).get('status') == 'confirmed'}   # a sheet the PDF has: the BoM uses the PDF's exact text, not this OCR
        if rows is None: entry['skipped'] = True
        elif not entry['in_pdf']:   # only sheets the PDF lacks are read from the OCR, so only they are worth checking. (A misread item number does not matter.)
            weak = [r for r in rows if r['review']]
            if not rows: problems.append(f'{f}: PARTS LIST found but no rows could be read')
            if weak: problems.append(f'{f}: {len(weak)} of {len(rows)} rows the OCR was unsure of and could not match to a known name: {"; ".join((r["item"] or "no item no.") + " " + r["part"] for r in weak)}')
        sheets.append(entry)
        print(f'{f}: {len(entry["rows"])} rows, sheet {entry["sheet"]}/{entry["of"]}{" (in the PDF)" if entry["in_pdf"] else ""}')
    crawl.write_if_changed(OUT, json.dumps({'source': 'OCR (rapidocr) of the drawing images in docs/images', 'sheets': sheets, 'problems': problems}, indent=1, ensure_ascii=False))
    write_review(sheets)
    used = [x for x in sheets if not x['in_pdf']]
    print(f'\n{len(sheets)} images ({len(sheets) - len(used)} are PDF sheets), {sum(len(x["rows"]) for x in used)} rows used, {len(problems)} to check -> {OUT}, {REVIEW}')
    for p in problems: print('  ', p)

def cell(t): return (str(t) if t not in (None, '') else '-').replace('|', '\\|')

def write_review(sheets):
    """notes/OCR_REVIEW.md: what to check by eye. Only sheets the PDF does not have matter: the rest use the PDF's exact text."""
    used = [x for x in sheets if not x['in_pdf']]
    check = [(x, r) for x in used for r in x['rows'] if r['review']]
    fixed = [(x, r, f) for x in used for r in x['rows'] if 'ocr' in r for f in ('part', 'description') if r['ocr'][f] != r[f]]
    lines = ['# OCR review', '',
             'The drawing sheets that exist only as images on the wiki (not in the exploded drawings PDF) are read by OCR in `scripts/drawing_images.py`. '
             'This page is written by that script and lists what to check by eye. The images that are also PDF sheets are not listed: the Bill of Materials uses the PDF\'s exact text for them. '
             f'{len(used)} image sheets, {sum(len(x["rows"]) for x in used)} rows; {len(check)} to check, {len(fixed)} fields corrected automatically.', '',
             '## Rows to check', '']
    if check:
        lines += ['The OCR was unsure of these and the text is not a name known from the PDF. They are left out of the Bill of Materials until fixed.', '',
                  '| Image | Sheet | Item | Qty | Part (as read) | Description (as read) | Confidence |', '| --- | --- | --- | --- | --- | --- | --- |']
        lines += [f'| {cell(x["image"])} | {cell(str(x["sheet"]) + " / " + str(x["of"]) if x["sheet"] else None)} | {cell(r["item"])} | {cell(r["qty"])} | {cell(r["part"])} | {cell(r["description"])} | {r["confidence"]} |' for x, r in check]
    else: lines.append('None.')
    lines += ['', '## Corrected automatically', '']
    if fixed:
        lines += ['Fixed against the exact names in the PDF; listed so they can be spot-checked.', '', '| Image | Item | Field | OCR read | Now reads |', '| --- | --- | --- | --- | --- |']
        lines += [f'| {cell(x["image"])} | {cell(r["item"])} | {f} | {cell(r["ocr"][f])} | {cell(r[f])} |' for x, r, f in fixed]
    else: lines.append('None.')
    lines += ['', '## No parts list found', '']
    none = [x for x in used if x.get('skipped')]
    lines += [f'- {x["image"]}' for x in none] if none else ['None.']
    crawl.write_if_changed(REVIEW, '\n'.join(lines) + '\n')

if __name__ == '__main__': main()
