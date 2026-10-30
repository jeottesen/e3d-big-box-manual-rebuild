#!/usr/bin/env python3
"""Draw sheets of the exploded drawings PDF as images, to stand in for drawing images the archive did not keep.

targets.SHEET_IMAGES says which sheet replaces which missing image. The PDF is vector, so the sheets draw cleanly at
the same size the wiki used (1200 px wide). Output: <data folder>/rendered/<file name>, which build.py uses.
Needs pypdfium2 (requirements.txt); run it with `mise run render`.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # sibling modules (python -I does not add the script folder)
import crawl
from drawings import get_pdf
from targets import SHEET_IMAGES
import pypdfium2 as pdfium

WIDTH = 1200

def main():
    pdf = pdfium.PdfDocument(get_pdf())
    out = f'{crawl.RAW}/rendered'
    os.makedirs(out, exist_ok=True)
    for name, sheet in SHEET_IMAGES.items():
        page = pdf[sheet - 1]
        im = page.render(scale=WIDTH / page.get_width()).to_pil().convert('RGB')
        im.save(f'{out}/{name}', quality=88)
        print(f'{name}: sheet {sheet} -> {im.size[0]}x{im.size[1]}')

if __name__ == '__main__': main()
