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
from targets import SHEET_IMAGES

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF = f'{ROOT}/docs/files/EXPLODED_DRAWINGS.pdf'
OUT = f'{ROOT}/notes/sheet_matches.json'
W, H = 420, 297            # size both are compared at (A4 landscape)
LOW_RES = 1200             # images narrower than this are worth redrawing from the PDF
MIN_ROWS = 0.8             # share of the image's rows that must also be on the PDF sheet to say they have the same parts

def key(t): return re.sub(r'[^A-Z0-9]', '', t.upper())

def candidates():
    out = {}
    for d in (f'{ROOT}/docs/images', f'{crawl.RAW}/images'):   # the raw capture wins when there is one
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
        scores = sorted(((ncc(v, sheet_ink[n]), n) for n in sheet_ink if np.ptp(sheet_ink[n]) > 0), reverse=True)
        (best, n), (second, n2) = scores[0], scores[1]
        stem = key(os.path.splitext(name)[0])
        by_title = [m for m, sh in parts.items() if key(sh['title']) and (key(sh['title']) == stem or key(sh['title']).startswith(stem) or stem.startswith(key(sh['title'])))]
        pdf_rows = {(key(r['part']), r['qty']) for r in parts[n]['rows']}
        img_rows = {(key(r['part']), r['qty']) for r in ocr.get(name, {}).get('rows', [])}
        shared = len(pdf_rows & img_rows) / len(img_rows) if img_rows else None
        strong = best >= 0.85 and best - second >= 0.2                      # the drawings look the same, and no other sheet does
        text_ok = n in by_title and (shared is None or shared >= 0.8 or (shared >= 0.6 and best - second >= 0.15))   # same title and (mostly) the same parts
        if strong or text_ok: status = 'confirmed'
        elif by_title and n not in by_title: status = 'check'               # the title says one sheet, the drawing looks like another
        else: status = 'no match'                                           # nothing in the PDF looks like it: a sheet from a newer revision
        r = {'status': status, 'sheet': n if status != 'no match' else None, 'visual': round(best, 3), 'next_best': round(second, 3), 'next_sheet': n2,
             'sheets_with_this_title': by_title, 'rows_shared': None if shared is None else round(shared, 2), 'image_width': w,
             'sheet_title': parts[n]['title'], 'image_sheet_no': ocr.get(name, {}).get('sheet'), 'image_of': ocr.get(name, {}).get('of')}
        if status == 'confirmed' and w < LOW_RES: r['action'] = 'redraw'       # same drawing, and the PDF has it at a better size
        result[name] = r
    json.dump({'source': 'scripts/match_sheets.py', 'matches': result}, open(OUT, 'w'), indent=1)
    for name, r in sorted(result.items(), key=lambda kv: (kv[1]['sheet'] or 99, kv[0])):
        print(f"{name:40} {r['status']:9} sheet {str(r['sheet']):4} visual {r['visual']:.2f} (next {r['next_best']:.2f}) title-sheets {r['sheets_with_this_title']} rows {r['rows_shared']} width {r['image_width']} {r.get('action', '')}")

if __name__ == '__main__': main()
