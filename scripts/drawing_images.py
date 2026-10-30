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
IMAGES = f'{ROOT}/docs/images'
OUT = f'{ROOT}/notes/parts_images.json'
MIN_CONF = 0.85

def candidates():
    """Drawing-shaped images: landscape A4 ratio, wide enough to read, and an upper-case file name (the wiki's sheet names)."""
    out = []
    for f in sorted(os.listdir(IMAGES)):
        stem, ext = os.path.splitext(f)
        if ext.lower() not in ('.jpg', '.jpeg', '.png') or stem != stem.upper() or not re.search(r'[A-Z]', stem): continue
        w, h = Image.open(f'{IMAGES}/{f}').size
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

def respace(text, vocab):
    """OCR gives 'M3x10SocketCapScrew' for 'M3 x 10 Socket Cap Screw'. Use the PDF's exact string if there is one."""
    if key(text) in vocab: return vocab[key(text)]
    t = text.strip()
    known = words_of(vocab)
    t = re.sub(r'[A-Z]{7,}', lambda m: segment(m.group(0), known), t)   # OCR runs capitals together: BASEBRACKETLOWER
    if ' ' in t: return t
    t = re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', t)          # CapScrew -> Cap Screw
    t = re.sub(r'(?<=[a-z])(?=\d)', ' ', t)             # Bag8 -> Bag 8
    t = re.sub(r'(?<=\d)x(?=\d)', ' x ', t)             # M3x10 -> M3 x 10
    t = re.sub(r'(?<=[A-Za-z0-9])(?=\()', ' ', t)       # Nut(Half) -> Nut (Half)
    return t

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
            rows.append({'item': num, 'qty': qty, 'part': respace(rest[0], vocab), 'description': respace(' '.join(rest[1:]), vocab) if len(rest) > 1 else '',
                         'confidence': round(min(w['c'] for w in g), 2)})
            if last != item['cy']: spacing = cy - last
            last = cy
        elif rows: continue   # text from the drawing itself, not a row
    return rows, problems

def main():
    vocab = vocabulary()
    ocr = RapidOCR()
    sheets, problems = [], []
    for f in candidates():
        (w, h), words = read(ocr, f'{IMAGES}/{f}')
        rows, probs = table(words, vocab)
        n = next((re.fullmatch(r'(\d{1,2})\s*/\s*(\d{1,2})', x['t']) for x in words if x['x'] > 0.7 * w and x['cy'] > 0.88 * h and re.fullmatch(r'(\d{1,2})\s*/\s*(\d{1,2})', x['t'])), None)
        title = os.path.splitext(f)[0].replace('_', ' ')
        entry = {'image': f, 'title': title, 'sheet': int(n.group(1)) if n else None, 'of': int(n.group(2)) if n else None, 'rows': rows or []}
        if rows is None: problems.append(f'{f}: {probs[0]}'); entry['skipped'] = True
        else:
            items = [r['item'] for r in rows if r['item'] and '.' not in r['item']]
            if not rows: problems.append(f'{f}: PARTS LIST found but no rows could be read')
            elif len(set(items)) != len(items): problems.append(f'{f}: item numbers {items} repeat; one was probably misread')
            weak = [r for r in rows if r['confidence'] < MIN_CONF]
            if weak: problems.append(f'{f}: low OCR confidence on {len(weak)} of {len(rows)} rows ({", ".join(r["item"] for r in weak)}); check against the image')
        sheets.append(entry)
        print(f'{f}: {len(entry["rows"])} rows, sheet {entry["sheet"]}/{entry["of"]}')
    json.dump({'source': 'OCR (rapidocr) of the drawing images in docs/images', 'sheets': sheets, 'problems': problems}, open(OUT, 'w'), indent=1, ensure_ascii=False)
    print(f'\n{len(sheets)} images, {sum(len(s["rows"]) for s in sheets)} rows, {len(problems)} problems -> {OUT}')
    for p in problems: print('  ', p)

if __name__ == '__main__': main()
