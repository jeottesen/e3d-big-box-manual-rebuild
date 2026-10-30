"""Which step of the manual shows each drawing (scripts/sections.py): the rules on small pages, and the result on the real built pages."""
import glob, os, re, unittest
from helpers import ROOT
from sections import embedded_sections, headings, thumb_file
import truth

def h(level, hid, text): return f'<h{level}><span class="mw-headline" id="{hid}">{text}</span></h{level}>'
def img(name, thumb=False): return f'<img src="/images/thumb/a/ab/{name}/300px-{name}">' if thumb else f'<img src="/images/a/ab/{name}">'

class Rules(unittest.TestCase):
    def test_an_image_belongs_to_the_step_it_is_under(self):
        out = embedded_sections({'P': h(2, 'a', '(8) Electronics Cover') + img('E.jpg')})
        self.assertEqual(out['E.jpg'], [('P', 'a', '(8) Electronics Cover')])

    def test_a_thumbnail_and_the_full_image_are_the_same_file(self):
        self.assertEqual(thumb_file('/images/thumb/a/ab/E.jpg/300px-E.jpg'), 'E.jpg')
        self.assertEqual(thumb_file('images/Z%20x.jpg'), 'Z x.jpg')

    def test_a_note_under_a_step_does_not_take_the_image_from_the_step(self):
        body = h(3, 'p', '(20) Printhead') + h(4, 'n', 'A note on nut-traps') + img('N.jpg')
        self.assertEqual(embedded_sections({'P': body})['N.jpg'], [('P', 'p', '(20) Printhead')])

    def test_the_most_specific_numbered_step_wins(self):
        body = h(3, 'p', '(20) Printhead') + h(4, 'q', '(20.2) Assembly of the HotEnds') + img('V.jpg')
        self.assertEqual(embedded_sections({'P': body})['V.jpg'], [('P', 'q', '(20.2) Assembly of the HotEnds')])

    def test_a_later_heading_ends_the_earlier_step(self):
        body = h(3, 'a', '(1) One') + img('A.jpg') + h(3, 'b', '(2) Two') + img('B.jpg')
        out = embedded_sections({'P': body})
        self.assertEqual((out['A.jpg'][0][1], out['B.jpg'][0][1]), ('a', 'b'))

    def test_a_sub_heading_does_not_leak_into_the_next_step(self):
        body = h(3, 'a', '(1) One') + h(4, 'a1', 'Detail') + h(3, 'b', '(2) Two') + img('B.jpg')
        self.assertEqual(embedded_sections({'P': body})['B.jpg'][0][1], 'b')

    def test_an_image_above_the_first_heading_belongs_to_the_page(self):
        self.assertEqual(embedded_sections({'Pro_&_Lite_X-Carriage': img('X.jpg') + h(3, 'a', 'Parts')})['X.jpg'], [('Pro_&_Lite_X-Carriage', None, 'Pro & Lite X-Carriage')])

    def test_a_heading_without_an_id_is_not_a_step(self):   # the page title the build adds
        body = '<h1>Title</h1>' + img('X.jpg')
        self.assertEqual(embedded_sections({'T': body})['X.jpg'], [('T', None, 'T')])

    def test_an_image_in_a_table_still_finds_its_heading(self):
        body = h(3, 'a', '(1) One') + '<table><tr><td>' + img('T.jpg') + '</td></tr></table>'
        self.assertEqual(embedded_sections({'P': body})['T.jpg'][0][1], 'a')

    def test_a_drawing_shown_in_two_steps_lists_both(self):
        out = embedded_sections({'A': h(3, 'a', '(1) One') + img('D.jpg'), 'B': h(3, 'b', '(2) Two') + img('D.jpg')})
        self.assertEqual([(p, i) for p, i, _ in out['D.jpg']], [('A', 'a'), ('B', 'b')])

    def test_pages_that_are_not_build_steps_are_left_out(self):
        out = embedded_sections({'Bill_Of_Materials': h(3, 'a', 'x') + img('D.jpg'), 'BigBox_Build_Manual': h(3, 'a', 'x') + img('D.jpg')})
        self.assertEqual(out, {})

    def test_the_page_slug_is_used_for_the_link(self):
        self.assertEqual(embedded_sections({'A & B': h(3, 'a', '(1) One') + img('D.jpg')}, slug=lambda t: t.replace(' & ', '_'))['D.jpg'][0][0], 'A_B')

    def test_headings_are_listed_in_order_with_ids(self):
        self.assertEqual(headings('<h1>No id</h1>' + h(2, 'a', 'One &amp; two') + h(3, 'b', '<i>Two</i>')), [(2, 'a', 'One & two'), (3, 'b', 'Two')])

def built_pages():
    pages = {}
    for f in sorted(glob.glob(os.path.join(ROOT, 'docs/*.html'))):
        name = os.path.basename(f)[:-5]
        if name not in ('index', 'manual'):
            with open(f, encoding='utf-8') as fh: pages[name] = fh.read()
    return pages

PAGES = built_pages()
DERIVED = embedded_sections(PAGES)

def texts(name): return [t for _, _, t in DERIVED.get(name, [])]

class BuiltPages(unittest.TestCase):
    """The mapping on the real manual. These pin the cases the maintainer confirmed against the manual."""
    def test_the_z_axis_drag_chain_is_step_18(self):   # not the sub-assembly its name suggests
        self.assertEqual(texts('Z-AXIS_DRAG_CHAIN.jpg'), ['(18) Z-Axis Drag Chain Anchors'])

    def test_the_electronics_cover_is_step_8_of_the_sub_assemblies(self):
        self.assertEqual([(p, t) for p, _, t in DERIVED['ELECTRONICS_COVER.jpg']], [('BigBox_Printer_Sub-assemblies', '(8) Electronics Cover')])

    def test_the_v6_hotend_is_in_every_printhead_step_that_shows_it(self):   # a drawing shown in several steps links all of them
        pages = {p for p, _, _ in DERIVED['E3D-V6_HOTEND_ASSEMBLY_BIGBOX.jpg']}
        self.assertEqual(pages, {'Single_Direct-Drive_Printhead_Assembly', 'Dual_Direct-Drive_Printhead_Assembly', 'Printer_main_assemblies_Step_By_Step_Assembly_Process'})

    def test_every_drawing_in_the_reviewed_data_is_shown_somewhere(self):
        shown = [im['file'] for s in truth.load_truth().values() for im in s['images']]
        self.assertEqual([f for f in shown if f not in DERIVED], [])

    def test_every_section_found_exists_in_its_page(self):
        for sections in DERIVED.values():
            for page, hid, _ in sections:
                self.assertIn(page, PAGES)
                if hid: self.assertIn(f'id="{hid}"', PAGES[page], f'{page}#{hid}')

    def test_the_bill_of_materials_links_only_to_steps_that_show_a_drawing(self):
        allowed = {f'{p}.html#{i}' if i else f'{p}.html' for sections in DERIVED.values() for p, i, _ in sections}
        bom = PAGES['Bill_Of_Materials']
        table = bom[bom.index('id="Printed_Parts"'):bom.index('id="Fixings"')]
        links = set(re.findall(r'href="([^"]+\.html(?:#[^"]*)?)"', table))
        self.assertTrue(links)
        self.assertEqual(sorted(l for l in links if l not in allowed), [])

if __name__ == '__main__': unittest.main()
