"""The page of every exploded drawing (scripts/drawings_page.py): the rules on small fixtures, and the built page against the reviewed data."""
import os, re, unittest, urllib.parse
from helpers import ROOT
from drawings_page import drawings_page, reading_order, sheet_entry
import truth

def sheet(sid, title='T', kind='pdf', rows=None, files=None, confirmed=None, page=1, image_sheet=None):
    src = {'kind': kind, 'file': 'f', 'sha256': 'a'}
    if kind == 'pdf': src['page'] = page
    if image_sheet: src['image_sheet'] = image_sheet
    default = [{'item': '1', 'qty': 2, 'part': 'M3 Nut', 'description': 'Fixings Bag 5', 'how': 'pdf-text' if kind == 'pdf' else 'ocr'}]
    return {'id': sid, 'title': title, 'source': src, 'images': [{'file': f, 'role': 'wiki'} for f in (files if files is not None else [f'{sid}.jpg'])],
            'rows': rows if rows is not None else default, 'confirmed': confirmed, 'notes': ''}

TITLES = {'BigBox_Parts_Preparation': 'BigBox Parts Preparation', 'BigBox_Printer_Sub-assemblies': 'BigBox Printer Sub-assemblies', 'Print_Cooling_Fan': 'Print Cooling Fan'}
ORDER = ['BigBox_Build_Manual', 'BigBox_Parts_Preparation', 'BigBox_Printer_Sub-assemblies', 'Print_Cooling_Fan']
HEADS = {'BigBox_Parts_Preparation': [(2, 'p1', '(1) One'), (2, 'p2', '(2) Two')], 'BigBox_Printer_Sub-assemblies': [(2, 's1', '(1) Single')], 'Print_Cooling_Fan': []}

def page(sheets, shown):
    return drawings_page({s['id']: s for s in sheets}, shown, TITLES, ORDER, HEADS)

class Order(unittest.TestCase):
    def test_the_big_step_pages_come_first_in_the_manuals_order(self):
        self.assertEqual(reading_order(TITLES, ['Print_Cooling_Fan', 'BigBox_Printer_Sub-assemblies', 'BigBox_Parts_Preparation'])[:2], ['BigBox_Parts_Preparation', 'BigBox_Printer_Sub-assemblies'])

    def test_drawings_follow_the_manual_not_their_ids(self):
        a, b, c, d = sheet('pdf-01'), sheet('pdf-02'), sheet('pdf-03'), sheet('pdf-04')
        shown = {'pdf-01.jpg': [('BigBox_Printer_Sub-assemblies', 's1', '(1) Single')], 'pdf-02.jpg': [('Print_Cooling_Fan', None, 'Print Cooling Fan')],
                 'pdf-03.jpg': [('BigBox_Parts_Preparation', 'p2', '(2) Two')]}
        html = page([a, b, c, d], shown)
        self.assertEqual(re.findall(r'<h3 id="([^"]+)"', html), ['pdf-03', 'pdf-01', 'pdf-02', 'pdf-04'])   # preparation, sub-assembly, another page, not shown

    def test_within_a_page_the_steps_keep_their_order(self):
        a, b = sheet('pdf-01'), sheet('pdf-02')
        shown = {'pdf-01.jpg': [('BigBox_Parts_Preparation', 'p2', '(2) Two')], 'pdf-02.jpg': [('BigBox_Parts_Preparation', 'p1', '(1) One')]}
        self.assertEqual(re.findall(r'<h3 id="([^"]+)"', page([a, b], shown)), ['pdf-02', 'pdf-01'])

    def test_a_drawing_shown_in_two_steps_is_listed_once_by_its_earliest(self):
        a = sheet('pdf-01')
        shown = {'pdf-01.jpg': [('BigBox_Printer_Sub-assemblies', 's1', '(1) Single'), ('BigBox_Parts_Preparation', 'p1', '(1) One')]}
        html = page([a], shown)
        self.assertEqual(html.count('<h3 '), 1)
        self.assertIn('<h2><a href="BigBox_Parts_Preparation.html">', html)
        self.assertIn('(1) Single', html); self.assertIn('(1) One', html)   # but both steps are linked

class Groups(unittest.TestCase):
    def test_one_heading_per_page_and_a_last_group_for_the_unshown(self):
        a, b, c = sheet('pdf-01'), sheet('pdf-02'), sheet('pdf-03')
        shown = {'pdf-01.jpg': [('BigBox_Parts_Preparation', 'p1', '(1) One')], 'pdf-02.jpg': [('BigBox_Parts_Preparation', 'p2', '(2) Two')]}
        html = page([a, b, c], shown)
        self.assertEqual(html.count('<h2>'), 2)
        self.assertTrue(html.rindex('Not shown in the manual') > html.rindex('<h3 id="pdf-02"'))

class Entry(unittest.TestCase):
    def test_a_pdf_sheet_links_its_pdf_page(self):
        self.assertIn('href="files/EXPLODED_DRAWINGS.pdf#page=7"', sheet_entry(sheet('pdf-07', page=7), {}))

    def test_an_image_only_sheet_says_where_in_the_newer_drawings_it_is(self):
        self.assertIn('sheet 18 of 41', sheet_entry(sheet('img-A', kind='image', image_sheet=[18, 41], confirmed={'by': 'J', 'on': 'x'}), {}))

    def test_the_steps_that_show_it_are_linked_and_a_page_level_link_has_no_fragment(self):
        html = sheet_entry(sheet('pdf-01'), {'pdf-01.jpg': [('Print_Cooling_Fan', None, 'Print Cooling Fan'), ('BigBox_Parts_Preparation', 'p1', '(1) One')]})
        self.assertIn('href="Print_Cooling_Fan.html">Print Cooling Fan', html)
        self.assertIn('href="BigBox_Parts_Preparation.html#p1"', html)

    def test_an_approximate_quantity_is_marked(self):
        rows = [{'item': '', 'qty': 150, 'approx': True, 'part': 'NUT TRAP', 'description': 'Printed Part', 'how': 'entered', 'basis': 'x'}]
        self.assertIn('<td>~150</td>', sheet_entry(sheet('img-A', kind='image', rows=rows), {}))

    def test_names_are_escaped(self):
        rows = [{'item': '1', 'qty': 1, 'part': 'Y-AXIS REAR (L&R) <b>', 'description': 'x', 'how': 'pdf-text'}]
        html = sheet_entry(sheet('pdf-01', rows=rows), {})
        self.assertIn('(L&amp;R) &lt;b&gt;', html); self.assertNotIn('<b>', html)

    def test_rows_read_by_ocr_and_not_yet_checked_are_not_shown(self):
        html = sheet_entry(sheet('img-A', kind='image'), {})
        self.assertNotIn('<table>', html); self.assertIn('has not been checked', html)

    def test_rows_a_person_entered_are_shown_without_a_check(self):
        rows = [{'item': '', 'qty': 1, 'part': 'P', 'description': 'Printed Part', 'how': 'entered', 'basis': 'x'}]
        self.assertIn('<table>', sheet_entry(sheet('img-A', kind='image', rows=rows), {}))

    def test_a_sheet_the_manual_never_shows_says_so(self):
        self.assertIn('the manual does not show this drawing', sheet_entry(sheet('pdf-22'), {}))

    def test_the_image_name_is_quoted(self):
        self.assertIn('src="images/A%20B.jpg"', sheet_entry(sheet('pdf-01', files=['A B.jpg']), {}))

# ---- the built page, against the reviewed data
with open(os.path.join(ROOT, 'docs/Exploded_Drawings.html'), encoding='utf-8') as fh: BUILT = fh.read()
SHEETS = truth.load_truth()

def entries():
    parts = re.split(r'(?=<h3 id=")', BUILT)[1:]
    return {re.match(r'<h3 id="([^"]+)"', p).group(1): p for p in parts}

class BuiltPage(unittest.TestCase):
    def test_every_sheet_is_on_the_page_once(self):
        ids = re.findall(r'<h3 id="([^"]+)"', BUILT)
        self.assertEqual(sorted(ids), sorted(SHEETS))
        self.assertEqual(len(ids), len(set(ids)))

    def test_each_entry_has_its_whole_parts_list(self):
        for sid, entry in entries().items():
            confirmed = SHEETS[sid]['confirmed'] is not None or all(r['how'] not in ('ocr', 'ocr+fix') for r in SHEETS[sid]['rows'])
            if confirmed: self.assertEqual(entry.count('<tr><td>'), len(SHEETS[sid]['rows']), sid)

    def test_each_entry_shows_its_drawing_and_the_file_exists(self):
        for sid, entry in entries().items():
            first = SHEETS[sid]['images'][0]['file']
            self.assertIn(f'<img src="images/{urllib.parse.quote(first)}"', entry, sid)
            self.assertTrue(os.path.exists(os.path.join(ROOT, 'docs/images', first)), first)

    def test_every_step_linked_exists(self):
        for href in set(re.findall(r'href="([A-Za-z0-9_.&%-]+\.html(?:#[^"]*)?)"', BUILT)):
            page, _, frag = href.partition('#')
            path = os.path.join(ROOT, 'docs', urllib.parse.unquote(page).replace('&amp;', '&'))
            self.assertTrue(os.path.exists(path), href)
            if frag:
                with open(path, encoding='utf-8') as f: self.assertIn(f'id="{frag}"', f.read(), href)

    def test_the_bill_of_materials_links_to_it(self):
        with open(os.path.join(ROOT, 'docs/Bill_Of_Materials.html'), encoding='utf-8') as f: self.assertIn('href="Exploded_Drawings.html"', f.read())

    def test_the_main_page_links_it_in_an_appendix(self):
        with open(os.path.join(ROOT, 'docs/BigBox_Build_Manual.html'), encoding='utf-8') as f: main = f.read()
        appendix = main[main.index('id="Appendix"'):]
        self.assertIn('href="Exploded_Drawings.html"', appendix)
        self.assertIn('href="Bill_Of_Materials.html"', appendix)
        self.assertIn('href="#Appendix"', main)   # and the page's own contents list has it

    def test_the_manual_does_not_show_exactly_the_sheets_without_a_wiki_image(self):
        heading = re.search(r'<h2[^>]*>Not shown in the manual</h2>', BUILT)   # the contents list also names it, so find the heading itself
        tail = BUILT[heading.end():] if heading else ''
        for sid in re.findall(r'<h3 id="([^"]+)"', tail): self.assertEqual({i['role'] for i in SHEETS[sid]['images']}, {'drawn'})

if __name__ == '__main__': unittest.main()
