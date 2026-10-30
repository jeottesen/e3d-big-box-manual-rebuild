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
import difflib, json, os, re, sys
import numpy as np
from PIL import Image
from rapidocr_onnxruntime import RapidOCR

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # sibling modules (python -I does not add the script folder)
from targets import OCR_FIXES, SHEET_IMAGES
IMAGES = f'{ROOT}/docs/images'
OUT = f'{ROOT}/notes/parts_images.json'
REVIEW = f'{ROOT}/notes/OCR_REVIEW.md'
MIN_CONF = 0.85
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

def key(t): return re.sub(r'[^A-Z0-9]', '', t.upper())

def vocabulary():
    """Exact part and description strings from the PDF, keyed without spaces, to put the spaces back."""
    path = f'{ROOT}/notes/parts.json'
    vocab = {}
    if os.path.exists(path):
        for sh in json.load(open(path))['sheets']:
            for r in sh['rows']:
                for t in (r['part'], r['description']):
                    if t: vocab[key(t)] = t
    return vocab

EXTRA_WORDS = 'DOCK CLAMP LEVER GUIDE HYBRID TITAN NON DIRECT BODY TOP CAP BOTTOM BED DUAL CABLE BRACKET CHAIN ANCHOR BASE UPPER LOWER'.split()

def words_of(vocab):
    """Upper-case words from the PDF's names, plus a few the image-only sheets use."""
    return {w for t in vocab.values() for w in re.findall(r'[A-Za-z]{2,}', t.upper())} | set(EXTRA_WORDS)

def segment(run, known):
    """Split a run of capitals with no spaces ('BASEBRACKETLOWER') into known words; unknown stretches stay whole."""
    n = len(run)
    best = [(0, None)] + [(10 ** 9, None)] * n   # (cost, previous index)
    for j in range(1, n + 1):
        for i in range(max(0, j - 14), j):
            w = run[i:j]
            cost = best[i][0] + (1 if w in known else 12 * len(w))
            if cost < best[j][0]: best[j] = (cost, i)
    out, j = [], n
    while j > 0: i = best[j][1]; out.append(run[i:j]); j = i
    return ' '.join(reversed(out))

def parts_by_description():
    """Which part names the PDF lists under each description (mostly each 'Fixings Bag N'), keyed without spaces."""
    path = f'{ROOT}/notes/parts.json'
    out = {}
    if os.path.exists(path):
        for sh in json.load(open(path))['sheets']:
            for r in sh['rows']:
                if r['description']: out.setdefault(key(r['description']), {})[key(r['part'])] = r['part']
    return out

def respace(text, vocab):
    """OCR gives 'M3x10SocketCapScrew' for 'M3 x 10 Socket Cap Screw'. Use the PDF's exact string if there is one."""
    if key(text) in vocab: return vocab[key(text)]
    t = text.strip()
    known = words_of(vocab)
    t = re.sub(r'[A-Z]{7,}', lambda m: segment(m.group(0), known), t)   # OCR runs capitals together: BASEBRACKETLOWER
    t = re.sub(r'\b(M\d+(?:\.\d+)?)(?=[A-Z][a-z])', r'\1 ', t)         # M2Hex Nut -> M2 Hex Nut
    t = re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', t)                         # HexNut -> Hex Nut, CapScrew -> Cap Screw
    if ' ' in t and not re.search(r'[a-z]\d|\dx\d|[A-Za-z0-9]\(', t): return t
    t = re.sub(r'(?<=[a-z])(?=\d)', ' ', t)                            # Bag8 -> Bag 8
    t = re.sub(r'(?<=\d)x(?=\d)', ' x ', t)                           # M3x10 -> M3 x 10
    t = re.sub(r'(?<=[A-Za-z0-9])(?=\()', ' ', t)                      # Nut(Half) -> Nut (Half)
    return t

BAG = re.compile(r'F[A-Za-z]{1,7}\s*B[A-Za-z]{1,3}\s*(\d{1,2})', re.I)   # 'Foings Bog8', 'Fxinss Bag 12': the OCR garbles 'Fixings Bag' more than anything else

def normalise(text, vocab, conf):
    """Put the OCR text right where we can. 'Fixings Bag N' is corrected by pattern. Other names are matched to the closest exact
    string from the PDF only when the OCR itself was unsure, and never if that would change a number: the image-only sheets
    hold parts the PDF does not have, and a near miss (a 364 mm rod for a 384 mm one) is a different part, not a misread."""
    m = BAG.fullmatch(text.strip())
    if m: return f'Fixings Bag {m.group(1)}'
    if not text or key(text) in vocab: return vocab.get(key(text), text)
    if conf >= MIN_CONF: return text
    digits = lambda t: re.sub(r'\D', '', t)
    close = [c for c in difflib.get_close_matches(key(text), list(vocab), n=2, cutoff=0.88) if digits(c) == digits(key(text))]
    return vocab[close[0]] if len(close) == 1 else text

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
            part = respace(rest[0], vocab); desc = respace(' '.join(rest[1:]), vocab) if len(rest) > 1 else ''
            conf = round(min(w['c'] for w in g), 2)
            read_part, read_desc = part, desc   # what the OCR gave
            by_hand = key(part) in FIXES or key(desc) in FIXES   # checked against the drawing by eye (targets.OCR_FIXES)
            part, desc_read = FIXES.get(key(part), part), FIXES.get(key(desc), desc)
            fixed_part, fixed_desc = normalise(part, vocab, conf), normalise(desc_read, vocab, conf)
            if key(fixed_part) not in vocab and fixed_desc.startswith('Fixings Bag') and key(fixed_desc) in BY_DESC:   # only a fixings bag is a short enough list to match inside   # a part in a known bag is one of that bag's parts: M2Hex Nut in Fixings Bag 3 is the M3 Hex Nut
                bag = BY_DESC[key(fixed_desc)]
                close = [c for c in difflib.get_close_matches(key(fixed_part), list(bag), n=2, cutoff=0.8) if re.sub(r'\D', '', c) == re.sub(r'\D', '', key(fixed_part))]   # never change a number
                if len(close) == 1: fixed_part = bag[close[0]]
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
    vocab = vocabulary()
    BY_DESC = parts_by_description()
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
    json.dump({'source': 'OCR (rapidocr) of the drawing images in docs/images', 'sheets': sheets, 'problems': problems}, open(OUT, 'w'), indent=1, ensure_ascii=False)
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
    open(REVIEW, 'w').write('\n'.join(lines) + '\n')

if __name__ == '__main__': main()
