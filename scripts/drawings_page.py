"""The page that shows every exploded drawing in one place. Standard library only, so the tests can import it.

The exploded drawings PDF does not have them all: the wiki's newer drawings add the hybrid and dual extruders, the Z axis and more.
This page has one entry per sheet in the reviewed data (data/sheets/): the drawing, its parts list, where the manual shows it and its
page in the PDF. The entries follow the manual: the drawings of the parts preparation steps first, then the sub-assemblies, then the
step-by-step assembly, then the drawings that only the other pages show, and last any that the manual does not show at all.
"""
import html, urllib.parse

READING_FIRST = ['BigBox_Parts_Preparation', 'BigBox_Printer_Sub-assemblies', 'Printer_main_assemblies_Step_By_Step_Assembly_Process']
NOT_SHOWN = 'Not shown in the manual'


def _heading_index(heads, page, hid):
    ids = [h[1] for h in heads.get(page, [])]
    return ids.index(hid) if hid in ids else -1   # -1: the page itself, above its first heading


def reading_order(titles, order):
    """Page slugs in the order the manual uses them: the three big step pages first, then the rest as the build lists them."""
    return [p for p in READING_FIRST if p in titles] + [p for p in order if p not in READING_FIRST]


def where_shown(sheet, sections_by_image, rank, heads):
    """(page rank, heading index, page slug) of the earliest step of the manual that shows this sheet's drawing, or None."""
    found = []
    for im in sheet['images']:
        for page, hid, _ in sections_by_image.get(im['file'], []):
            found.append((rank.get(page, len(rank)), _heading_index(heads, page, hid), page))
    return min(found) if found else None


def sheet_entry(sheet, sections_by_image, esc=html.escape):
    files = [im['file'] for im in sheet['images']]
    src = sheet['source']
    facts = []
    if src['kind'] == 'pdf': facts.append(f'<a href="files/EXPLODED_DRAWINGS.pdf#page={src["page"]}">PDF sheet {src["page"]}</a>')
    else:
        n, of = (src.get('image_sheet') or [None, None])
        if n: facts.append(f'sheet {n} of {of} in the wiki&rsquo;s newer drawings')
    shown, seen = [], set()
    for f in files:
        for page, hid, text in sections_by_image.get(f, []):
            if (page, hid) not in seen:
                seen.add((page, hid)); shown.append(f'<a href="{page}.html{"#" + esc(hid) if hid else ""}">{esc(text)}</a>')
    facts.append('shown in ' + '; '.join(shown) if shown else 'the manual does not show this drawing')
    facts += [f'<a href="images/{urllib.parse.quote(f)}">full size</a>' for f in files[:1]]
    out = [f'<h3 id="{esc(sheet["id"])}">{esc(sheet["title"])}</h3>', f'<p class="sheetinfo">{" · ".join(facts)}</p>']
    if files: out.append(f'<img src="images/{urllib.parse.quote(files[0])}" alt="{esc(files[0])}">')
    unchecked = sheet['confirmed'] is None and any(r['how'] in ('ocr', 'ocr+fix') for r in sheet['rows'])
    if unchecked: out.append('<p class="derived"><em>The parts list read from this drawing has not been checked yet.</em></p>')
    elif sheet['rows']:
        body = ''.join(f'<tr><td>{"~" if r.get("approx") else ""}{r["qty"]}</td><td>{esc(r["part"])}</td><td>{esc(r["description"])}</td></tr>' for r in sheet['rows'])
        out.append(f'<table><thead><tr><th>Qty</th><th>Part</th><th>Description</th></tr></thead><tbody>{body}</tbody></table>')
    return ''.join(out)


def drawings_page(sheets, sections_by_image, titles, order, heads):
    """The page body. sheets: the reviewed data {id: sheet}; sections_by_image: {file: [(page slug, heading id, heading text)]};
    titles: {page slug: page title}; order: page slugs in the build's order; heads: {page slug: [(level, id, text)]}."""
    rank = {p: i for i, p in enumerate(reading_order(titles, order))}
    placed = []
    for sh in sheets.values():
        w = where_shown(sh, sections_by_image, rank, heads)
        placed.append(((w[0], w[1]) if w else (len(rank) + 1, 0), w[2] if w else None, sh['id'], sh))
    placed.sort(key=lambda x: (x[0], x[2] or '', x[3]['id']))
    pdf = [s for s in sheets.values() if s['source']['kind'] == 'pdf']
    parts = [f'<p class="derived"><em>Every exploded drawing of the BigBox in one place: {len(sheets)} sheets, each with its parts list. The exploded drawings '
             f'<a href="files/EXPLODED_DRAWINGS.pdf">PDF</a> has {len(pdf)} of them; the rest (the hybrid and dual extruders, the Z axis and a few more) '
             'exist only as images on the wiki. The drawings follow the manual: the parts preparation steps first, then the sub-assemblies, then the step-by-step '
             'assembly. The parts lists were read from the PDF&rsquo;s text and from the wiki&rsquo;s images, see <a href="Bill_Of_Materials.html">the Bill of Materials</a>.</em></p>']
    group = 'unset'
    for _, page, _, sh in placed:
        if page != group:
            group = page
            parts.append(f'<h2><a href="{html.escape(page)}.html">{html.escape(titles[page])}</a></h2>' if page else f'<h2>{NOT_SHOWN}</h2>')
        parts.append(sheet_entry(sh, sections_by_image))
    return ''.join(parts)
