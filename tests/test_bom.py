"""The built Bill of Materials page (docs/Bill_Of_Materials.html): every row must trace to a drawing and a real section."""
import os, re, unittest, urllib.parse
from html.parser import HTMLParser
from helpers import ROOT

class Tables(HTMLParser):
    """The tables that follow the Printed Parts and Fixings headings: {section id: [row, ...]}, a row being [(text, [hrefs])]."""
    def __init__(self):
        super().__init__(); self.section = None; self.tables = {}; self.row = None; self.cell = None
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'span' and a.get('id') in ('Printed_Parts', 'Fixings'): self.section = a['id']
        elif tag == 'h3' and self.section and 'id' not in a: pass
        elif tag == 'tr' and self.section: self.row = []
        elif tag in ('td', 'th') and self.row is not None: self.cell = ['', []]
        elif tag == 'a' and self.cell is not None and a.get('href'): self.cell[1].append(a['href'])
    def handle_data(self, data):
        if self.cell is not None: self.cell[0] += data
    def handle_endtag(self, tag):
        if tag in ('td', 'th') and self.cell is not None: self.row.append((self.cell[0].strip(), self.cell[1])); self.cell = None
        elif tag == 'tr' and self.row is not None:
            if self.row: self.tables.setdefault(self.section, []).append(self.row)
            self.row = None
        elif tag == 'h3': pass

def parse():
    p = Tables()
    with open(os.path.join(ROOT, 'docs/Bill_Of_Materials.html'), encoding='utf-8') as f: p.feed(f.read())
    return {k: [r for r in rows if r[0][0] not in ('Part', 'Fixings bag')] for k, rows in p.tables.items()}   # drop the header rows

TABLES = parse()
PDF_PAGES = 29

class Bom(unittest.TestCase):
    def test_both_tables_are_filled(self):
        self.assertGreater(len(TABLES['Printed_Parts']), 40)
        self.assertGreater(len(TABLES['Fixings']), 20)

    def test_no_row_is_repeated(self):
        for section, rows in TABLES.items():
            seen = [tuple((t, tuple(h)) for t, h in r) for r in rows]
            self.assertEqual(len(seen), len(set(seen)), section)

    def drawing_cell(self, section, row): return row[3] if section == 'Printed_Parts' else row[2]

    def test_every_row_has_a_drawing_that_exists(self):
        for section, rows in TABLES.items():
            for row in rows:
                text, hrefs = self.drawing_cell(section, row)
                self.assertTrue(hrefs, f'{section}: {row[0][0]} has no drawing link')
                for href in hrefs:
                    if href.startswith('images/'): self.assertTrue(os.path.exists(os.path.join(ROOT, 'docs', urllib.parse.unquote(href))), href)
                    else:
                        m = re.fullmatch(r'files/EXPLODED_DRAWINGS\.pdf#page=(\d+)', href)
                        self.assertTrue(m and 1 <= int(m.group(1)) <= PDF_PAGES, href)

    def test_every_build_section_link_lands_on_a_heading(self):
        for row in TABLES['Printed_Parts']:
            for href in row[4][1]:
                page, _, frag = href.partition('#')
                with open(os.path.join(ROOT, 'docs', page), encoding='utf-8') as f: html = f.read()
                self.assertIn(f'id="{frag}"', html, href)

    def test_the_pdf_link_is_at_the_top_of_each_section(self):
        with open(os.path.join(ROOT, 'docs/Bill_Of_Materials.html'), encoding='utf-8') as f: html = f.read()
        self.assertEqual(html.count('<p class="derived">'), 2)
        self.assertEqual(html.count('href="files/EXPLODED_DRAWINGS.pdf"'), 2)

if __name__ == '__main__': unittest.main()
