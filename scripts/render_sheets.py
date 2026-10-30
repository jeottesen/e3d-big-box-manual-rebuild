#!/usr/bin/env python3
"""Draw sheets of the exploded drawings PDF as images, for the build to use in place of wiki images, and enlarge the
low-resolution drawing images that have no PDF sheet.

What to draw comes from the reviewed data (data/sheets/): an image with role "lost" (the archive did not keep it) or "redrawn"
(low resolution, and the PDF has the same drawing) is drawn from the PDF sheet; role "enlarged" (low resolution, no PDF sheet)
is made twice the size, with the original kept. The PDF is vector, so the sheets draw cleanly at any size.
Output: <data folder>/rendered/<file name>. Needs pypdfium2 (requirements.txt); run it with `mise run render`.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # sibling modules (python -I does not add the script folder)
import crawl
from drawings import get_pdf
import pypdfium2 as pdfium
from PIL import Image, ImageFilter

WIDTH = 1600

def main():
    import truth
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pdf = pdfium.PdfDocument(get_pdf())
    out = f'{crawl.RAW}/rendered'
    os.makedirs(out, exist_ok=True)
    for sheet in truth.load_truth().values():
        for im in sheet['images']:
            name = im['file']
            if im['role'] in ('lost', 'redrawn'):
                page = pdf[sheet['source']['page'] - 1]
                img = page.render(scale=WIDTH / page.get_width()).to_pil().convert('RGB')
                img.save(f'{out}/{name}', quality=88)
                print(f'{name}: sheet {sheet["source"]["page"]} -> {img.size[0]}x{img.size[1]}')
            elif im['role'] == 'enlarged':   # the wiki's own capture, or the original kept in docs/images/original/ from an earlier build
                src = next((p for p in (f'{crawl.RAW}/images/{name}', f'{root}/docs/images/original/{name}') if os.path.exists(p)), None)
                if not src: print(f'{name}: no original to enlarge'); continue
                orig = Image.open(src).convert('RGB')
                big = orig.resize((orig.width * 2, orig.height * 2), Image.LANCZOS).filter(ImageFilter.UnsharpMask(radius=1.4, percent=70, threshold=2))
                big.save(f'{out}/{name}', quality=92)
                print(f'{name}: enlarged {orig.width}x{orig.height} -> {big.width}x{big.height}')

if __name__ == '__main__': main()
