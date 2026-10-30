#!/usr/bin/env python3
"""Draw sheets of the exploded drawings PDF as images, for the build to use in place of wiki images.

Two kinds: drawing images the archive did not keep (targets.SHEET_IMAGES says which sheet replaces which), and wiki
images that are low resolution but the same drawing as a PDF sheet (notes/sheet_matches.json, action "redraw", written
by match_sheets.py). The PDF is vector, so the sheets draw cleanly at any size. Output: <data folder>/rendered/<file name>.
Needs pypdfium2 (requirements.txt); run it with `mise run render`.
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # sibling modules (python -I does not add the script folder)
import crawl
from drawings import get_pdf
from targets import SHEET_IMAGES
import pypdfium2 as pdfium

WIDTH = 1600

def main():
    pdf = pdfium.PdfDocument(get_pdf())
    out = f'{crawl.RAW}/rendered'
    os.makedirs(out, exist_ok=True)
    wanted = dict(SHEET_IMAGES)
    matches = f'{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/notes/sheet_matches.json'
    if os.path.exists(matches):
        wanted.update({n: m['sheet'] for n, m in json.load(open(matches))['matches'].items() if m.get('action') == 'redraw'})
    for name, sheet in wanted.items():
        page = pdf[sheet - 1]
        im = page.render(scale=WIDTH / page.get_width()).to_pil().convert('RGB')
        im.save(f'{out}/{name}', quality=88)
        print(f'{name}: sheet {sheet} -> {im.size[0]}x{im.size[1]}')

if __name__ == '__main__': main()
