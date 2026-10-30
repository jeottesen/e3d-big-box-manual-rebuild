#!/usr/bin/env python3
"""Match the drawing images on the wiki to the sheets of the exploded drawings PDF.

The wiki embedded most sheets as images (docs/images); the PDF (docs/files/EXPLODED_DRAWINGS.pdf) has the same sheets
as vector drawings. For each image this finds the PDF sheet that looks like it, and checks the match three ways:
the drawing itself (the PDF sheet is drawn small and compared with the image), the sheet title, and the parts list
(the PDF's rows against the rows OCR read from the image). It writes notes/sheet_matches.json, which says for each
image which sheet it is, how sure that is, and whether the image should be redrawn from the PDF (it is low resolution,
and the two have the same parts, so the PDF is the same drawing at a better size).

It uses the original wiki capture of each image (<data folder>/images) when there is one, so that images already
replaced by a redraw do not change the answer. Needs numpy, pillow and pypdfium2 (requirements.txt):  mise run match
"""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # sibling modules (python -I does not add the script folder)
import numpy as np
import pypdfium2 as pdfium
from PIL import Image, ImageFilter
import crawl
from match_logic import decide
from targets import SHEET_IMAGES, MATCH_OVERRIDES

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF = f'{ROOT}/docs/files/EXPLODED_DRAWINGS.pdf'
OUT = f'{ROOT}/notes/sheet_matches.json'
W, H = 420, 297            # size both are compared at (A4 landscape)
LOW_RES = 1200             # images narrower than this are worth redrawing from the PDF

def key(t): return re.sub(r'[^A-Z0-9]', '', t.upper())

def candidates():
    out = {}
    for d in (f'{ROOT}/docs/images', f'{ROOT}/docs/images/original', f'{crawl.RAW}/images'):   # the original wiki capture wins when there is one
        if not os.path.isdir(d): continue
        for f in sorted(os.listdir(d)):
            stem, ext = os.path.splitext(f)
            if f in SHEET_IMAGES or ext.lower() not in ('.jpg', '.jpeg', '.png') or stem != stem.upper() or not re.search(r'[A-Z]', stem): continue   # SHEET_IMAGES are already drawn from the PDF
            w, h = Image.open(f'{d}/{f}').size
            if w >= 700 and 1.38 <= w / h <= 1.45: out[f] = f'{d}/{f}'
    return out

def ink(im):
    """The drawing's lines as a blurred map, with the border and title block (the same on every sheet) blanked."""
    g = im.convert('L').resize((W, H), Image.LANCZOS)
    a = (np.array(g) < 170).astype(np.uint8) * 255
    m = Image.fromarray(a).filter(ImageFilter.GaussianBlur(2.0))
    v = np.array(m, dtype=np.float32)
    v[: int(H * 0.04)] = 0; v[int(H * 0.96):] = 0; v[:, : int(W * 0.03)] = 0; v[:, int(W * 0.97):] = 0
    v[int(H * 0.78):, int(W * 0.38):] = 0
    return v

def ncc(a, b):
    a = a - a.mean(); b = b - b.mean()
    d = np.sqrt((a * a).sum() * (b * b).sum())
    return float((a * b).sum() / d) if d else 0.0

def main():
    pdf = pdfium.PdfDocument(PDF)
    parts = {s['sheet']: s for s in json.load(open(f'{ROOT}/notes/parts.json'))['sheets']}
    sheet_ink = {}
    for n in range(1, len(pdf) + 1):
        page = pdf[n - 1]
        sheet_ink[n] = ink(page.render(scale=1400 / page.get_width()).to_pil())
    ocr = {s['image']: s for s in json.load(open(f'{ROOT}/notes/parts_images.json'))['sheets']}
    result = {}
    for name, path in candidates().items():
        im = Image.open(path); w, h = im.size
        v = ink(im)
        visual = {n: ncc(v, sheet_ink[n]) for n in sheet_ink if np.ptp(sheet_ink[n]) > 0}
        stem = key(os.path.splitext(name)[0])
        by_title = [m for m, sh in parts.items() if key(sh['title']) and (key(sh['title']) == stem or key(sh['title']).startswith(stem) or stem.startswith(key(sh['title'])))]
        img_rows = {(key(r['part']), r['qty']) for r in ocr.get(name, {}).get('rows', [])}
        shared = {t: (len(img_rows & {(key(r['part']), r['qty']) for r in parts[t]['rows']}) / len(img_rows) if img_rows else None) for t in by_title}
        status, n = decide(visual, by_title, shared)
        ranked = sorted(visual.items(), key=lambda kv: kv[1], reverse=True)
        (n_best, best), (n_next, second) = (ranked[0][0], ranked[0][1]), (ranked[1][0], ranked[1][1])
        n = n if n is not None else n_best    # for the record, the sheet it looks most like
        r = {'status': status, 'sheet': n if status != 'no match' else None, 'visual': round(visual[n], 3), 'looks_most_like': n_best, 'best_visual': round(best, 3),
             'next_best': round(second, 3), 'next_sheet': n_next, 'sheets_with_this_title': by_title, 'rows_shared': None if shared.get(n) is None else round(shared[n], 2),
             'image_width': w, 'sheet_title': parts[n]['title'], 'image_sheet_no': ocr.get(name, {}).get('sheet'), 'image_of': ocr.get(name, {}).get('of')}
        if name in MATCH_OVERRIDES:   # decided by eye (targets.MATCH_OVERRIDES): the drawing may be a different view or revision
            r.update({'status': 'confirmed', 'sheet': MATCH_OVERRIDES[name], 'manual': True, 'sheet_title': parts[MATCH_OVERRIDES[name]]['title']})
        elif status == 'confirmed' and w < LOW_RES: r['action'] = 'redraw'
        elif status == 'no match' and w < LOW_RES: r['action'] = 'enlarge'      # no PDF sheet to redraw it from: make it larger, keeping the original       # same drawing, and the PDF has it at a better size
        result[name] = r
    crawl.write_if_changed(OUT, json.dumps({'source': 'scripts/match_sheets.py', 'matches': result}, indent=1))
    for name, r in sorted(result.items(), key=lambda kv: (kv[1]['sheet'] or 99, kv[0])):
        print(f"{name:40} {r['status']:9} sheet {str(r['sheet']):4} visual {r['visual']:.2f} (next {r['next_best']:.2f}) title-sheets {r['sheets_with_this_title']} rows {r['rows_shared']} width {r['image_width']} {r.get('action', '')}")

if __name__ == '__main__': main()
