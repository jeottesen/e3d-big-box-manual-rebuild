#!/usr/bin/env python3
"""Draw sheets of the exploded drawings PDF as images, for the build to use in place of wiki images, and enlarge the
low-resolution drawing images that have no PDF sheet.

What to draw comes from the reviewed data (data/sheets/): an image with role "lost" (the archive did not keep it) or "redrawn"
(low resolution, and the PDF has the same drawing) or "drawn" (the wiki never showed the sheet as an image) is drawn from the PDF sheet; role "enlarged" (low resolution, no PDF sheet)
is made twice the size, with the original kept. The PDF is vector, so the sheets draw cleanly at any size.
Output: docs/images/<file name>, which is committed, so the build needs no venv. The wiki's own image is kept in docs/images/original/
first. Run it with `mise run render` when the reviewed data changes. Needs pypdfium2 (requirements.txt).
"""
import io, os, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # sibling modules (python -I does not add the script folder)
import crawl
from drawings import get_pdf
import pypdfium2 as pdfium
from PIL import Image, ImageFilter

WIDTH = 1600

def save_if_changed(img, path, quality):
    """Save a JPEG unless the file already holds exactly these bytes, so an unchanged image keeps its modification time."""
    buf = io.BytesIO(); img.save(buf, 'JPEG', quality=quality)
    if os.path.exists(path) and open(path, 'rb').read() == buf.getvalue(): return False
    open(path, 'wb').write(buf.getvalue()); return True

def main():
    import truth
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    images, originals = f'{root}/docs/images', f'{root}/docs/images/original'
    os.makedirs(originals, exist_ok=True)
    pdf = pdfium.PdfDocument(get_pdf())
    for sheet in truth.load_truth().values():
        for im in sheet['images']:
            name = im['file']
            if im['role'] in ('redrawn', 'enlarged') and not os.path.exists(f'{originals}/{name}'):   # keep the wiki's own image before it is replaced
                if os.path.exists(f'{crawl.RAW}/images/{name}'): shutil.copy(f'{crawl.RAW}/images/{name}', f'{originals}/{name}')
                else: sys.exit(f'{name}: the wiki original is not in {originals} and not in the data folder; run `mise run fetch` first')
            if im['role'] in ('lost', 'redrawn', 'drawn'):
                page = pdf[sheet['source']['page'] - 1]
                img = page.render(scale=WIDTH / page.get_width()).to_pil().convert('RGB')
                changed = save_if_changed(img, f'{images}/{name}', 88)
                print(f'{name}: sheet {sheet["source"]["page"]} -> {img.size[0]}x{img.size[1]}{"" if changed else " (unchanged)"}')
            elif im['role'] == 'enlarged':
                orig = Image.open(f'{originals}/{name}').convert('RGB')
                big = orig.resize((orig.width * 2, orig.height * 2), Image.LANCZOS).filter(ImageFilter.UnsharpMask(radius=1.4, percent=70, threshold=2))
                changed = save_if_changed(big, f'{images}/{name}', 92)
                print(f'{name}: enlarged {orig.width}x{orig.height} -> {big.width}x{big.height}{"" if changed else " (unchanged)"}')

if __name__ == '__main__': main()
