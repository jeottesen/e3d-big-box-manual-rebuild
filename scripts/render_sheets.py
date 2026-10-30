#!/usr/bin/env python3
"""Draw sheets of the exploded drawings PDF as images, for the build to use in place of wiki images, and enlarge the
low-resolution drawing images that have no PDF sheet.

Three kinds: drawing images the archive did not keep (targets.SHEET_IMAGES says which sheet replaces which), and wiki
images that are low resolution but the same drawing as a PDF sheet (notes/sheet_matches.json, action "redraw", written
by match_sheets.py). The PDF is vector, so the sheets draw cleanly at any size. Wiki drawing images that are low resolution
and not in the PDF (action "enlarge") are made twice the size; the original is kept and linked from the page. Output:
<data folder>/rendered/<file name>.
Needs pypdfium2 (requirements.txt); run it with `mise run render`.
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # sibling modules (python -I does not add the script folder)
import crawl
from drawings import get_pdf
from targets import SHEET_IMAGES
import pypdfium2 as pdfium
from PIL import Image, ImageFilter

WIDTH = 1600

def main():
    pdf = pdfium.PdfDocument(get_pdf())
    out = f'{crawl.RAW}/rendered'
    os.makedirs(out, exist_ok=True)
    wanted = dict(SHEET_IMAGES)
    matches = f'{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/notes/sheet_matches.json'
    if os.path.exists(matches):
        wanted.update({n: m['sheet'] for n, m in json.load(open(matches))['matches'].items() if m.get('action') == 'redraw'})
    enlarge = [n for n, m in json.load(open(matches))['matches'].items() if m.get('action') == 'enlarge'] if os.path.exists(matches) else []
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for name in enlarge:   # the wiki's own capture, or the original kept in docs/images/original/ from an earlier build
        src = next((p for p in (f'{crawl.RAW}/images/{name}', f'{root}/docs/images/original/{name}') if os.path.exists(p)), None)
        if not src: print(f'{name}: no original to enlarge'); continue
        im = Image.open(src).convert('RGB')
        big = im.resize((im.width * 2, im.height * 2), Image.LANCZOS).filter(ImageFilter.UnsharpMask(radius=1.4, percent=70, threshold=2))
        big.save(f'{out}/{name}', quality=92)
        print(f'{name}: enlarged {im.width}x{im.height} -> {big.width}x{big.height}')
    for name, sheet in wanted.items():
        page = pdf[sheet - 1]
        im = page.render(scale=WIDTH / page.get_width()).to_pil().convert('RGB')
        im.save(f'{out}/{name}', quality=88)
        print(f'{name}: sheet {sheet} -> {im.size[0]}x{im.size[1]}')

if __name__ == '__main__': main()
