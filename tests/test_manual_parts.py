"""The printed parts the manual's own step lists name (scripts/manual_parts.py), and the reviewed list in data/manual_parts.json."""
import os, re, unittest
from helpers import ROOT
import manual_parts as mp
import truth

def h(level, hid, text): return f'<h{level}><span class="mw-headline" id="{hid}">{text}</span></h{level}>'
def li(text): return f'<ul><li>{text}</li></ul>'

class Scan(unittest.TestCase):
    def one(self, body, slug='P'): return mp.scan({slug: body})

    def test_an_item_is_read_with_its_quantity_name_and_step(self):
        e = self.one(h(2, 's', '(10) Z-Axis Bed Assembly') + li('2 x Drive Supports (Printed Parts).'))[0]
        self.assertEqual((e['qty'], e['part'], e['container'], e['step'], e['step_id'], e['page'], e['drawing']), (2, 'Drive Supports', 'printed', '(10) Z-Axis Bed Assembly', 's', 'P', None))

    def test_the_boxes_and_bags_are_told_apart(self):
        body = h(2, 's', '(1) S') + li('8 x Feet (Printed Parts Box).') + li('1 x Spring (Printed Parts Bag).') + li('1 x Dock (Printed part).') + li('1 x Thing (Printed parts Box).')
        self.assertEqual([e['container'] for e in self.one(body)], ['printed-parts-box', 'printed-parts-bag', 'printed', 'printed-parts-box'])

    def test_the_wikis_stray_spaces_do_not_hide_an_item(self):
        self.assertEqual(len(self.one(h(2, 's', '(1) S') + '<ul><li>1 x Clamp (Printed Parts). </li></ul>')), 1)

    def test_an_item_belongs_to_the_nearest_numbered_step_not_a_note(self):
        body = h(3, 'a', '(8) Hybrid X-Carriage') + h(4, 'n', 'A note') + li('1 x Clamp (Printed Parts).')
        self.assertEqual(self.one(body)[0]['step_id'], 'a')

    def test_an_item_above_any_heading_belongs_to_the_page(self):
        e = self.one(li('1 x Bracket (Printed Part).'), slug='Dual_Direct-Drive_Extruders')[0]
        self.assertEqual((e['step_id'], e['step']), (None, 'Dual Direct-Drive Extruders'))

    def test_the_generated_pages_are_not_read(self):
        self.assertEqual(mp.scan({'Bill_Of_Materials': h(2, 's', '(1) S') + li('1 x X (Printed Part).'), 'Exploded_Drawings': li('1 x X (Printed Part).')}), [])

    def test_other_list_items_are_ignored(self):
        self.assertEqual(self.one(h(2, 's', '(1) S') + li('4 x M3 x 10 Socket Cap Screw.') + li('1 x Hobgoblin (Extruder Box).')), [])

    def test_html_entities_in_names_are_read_as_text(self):
        self.assertEqual(self.one(h(2, 's', '(1) S') + li('1 x Fan &amp; Duct (Printed Part).'))[0]['part'], 'Fan & Duct')

    def test_an_item_the_pattern_does_not_take_is_reported(self):
        self.assertEqual(mp.unparsed({'P': li('Some printed thing (Printed Part)') + li('1 x Fine (Printed Part).')}), [('P', 'Some printed thing (Printed Part)')])

class Compare(unittest.TestCase):
    def entry(self, part='A', qty=1, step_id='s', page='P', drawing=None):
        return {'page': page, 'step_id': step_id, 'step': '(1) S', 'qty': qty, 'part': part, 'container': 'printed', 'drawing': drawing, 'note': ''}

    def test_no_difference(self): self.assertEqual(mp.diff([self.entry()], [self.entry(drawing='pdf-01')]), [])
    def test_a_new_part_in_the_manual(self): self.assertEqual([k for k, _ in mp.diff([self.entry('A'), self.entry('B')], [self.entry('A')])], ['new'])
    def test_a_part_no_longer_in_the_manual(self): self.assertEqual([k for k, _ in mp.diff([self.entry('A')], [self.entry('A'), self.entry('B')])], ['gone'])
    def test_a_changed_quantity(self): self.assertEqual([k for k, _ in mp.diff([self.entry(qty=2)], [self.entry(qty=1)])], ['changed'])
    def test_spacing_and_case_in_a_name_do_not_matter(self): self.assertEqual(mp.diff([self.entry('Drive Supports')], [self.entry('drive  supports')]), [])

class Shape(unittest.TestCase):
    ok = {'page': 'P', 'step_id': 's', 'step': '(1) S', 'qty': 2, 'part': 'A', 'container': 'printed', 'drawing': None, 'note': ''}

    def bad(self, **changes):
        e = dict(self.ok); e.update(changes)
        self.assertTrue(mp.problems([e], {'pdf-01'}))

    def test_a_good_entry(self): self.assertEqual(mp.problems([self.ok, dict(self.ok, drawing='pdf-01', part='B')], {'pdf-01'}), [])
    def test_a_drawing_that_is_not_a_sheet(self): self.bad(drawing='pdf-99')
    def test_a_boolean_quantity(self): self.bad(qty=True)
    def test_an_unknown_container(self): self.bad(container='shelf')
    def test_no_part(self): self.bad(part='')
    def test_not_an_object(self): self.assertTrue(mp.problems(['x'], set()))
    def test_the_same_part_twice_for_one_step(self): self.assertTrue(mp.problems([self.ok, dict(self.ok)], set()))

# ---- the committed list against the manual
PAGES = mp.read_pages()
FOUND = mp.scan(PAGES)
REVIEWED = mp.load()

class CommittedList(unittest.TestCase):
    def test_nothing_in_the_manual_is_missing_from_the_list_and_nothing_is_stale(self):
        self.assertEqual(mp.diff(FOUND, REVIEWED), [])

    def test_the_manual_has_no_printed_part_item_this_tool_cannot_read(self):
        self.assertEqual(mp.unparsed(PAGES), [])

    def test_the_list_is_sound(self):
        self.assertEqual(mp.problems(REVIEWED, set(truth.load_truth())), [])

    def test_every_step_named_exists_in_its_page(self):
        for e in REVIEWED:
            self.assertIn(e['page'], PAGES, e)
            if e['step_id']: self.assertIn(f'id="{e["step_id"]}"', PAGES[e['page']], e['part'])

    def test_the_parts_the_user_found_are_on_the_list_with_no_drawing(self):
        drive = [e for e in REVIEWED if e['part'] == 'Drive Supports']
        self.assertEqual([(e['qty'], e['drawing'], e['step']) for e in drive], [(2, None, '(10) Z-Axis Bed Assembly')])

    def test_a_part_a_drawing_covers_names_a_part_on_that_sheet(self):
        # not the same words (the manual says Belt Tensioner, the drawing X-AXIS BELT-TENSIONER), so check the drawing has printed parts at all
        sheets = truth.load_truth()
        for e in REVIEWED:
            if e['drawing']: self.assertTrue(any(r['description'] == 'Printed Part' for r in sheets[e['drawing']]['rows']), e['part'])

class InTheBom(unittest.TestCase):
    def test_every_part_without_a_drawing_is_a_row_linked_to_its_step(self):
        with open(os.path.join(ROOT, 'docs/Bill_Of_Materials.html'), encoding='utf-8') as f: bom = f.read()
        table = bom[bom.index('id="Printed_Parts"'):bom.index('id="Fixings"')]
        for group in {truth.key(e['part']): e for e in REVIEWED if not e['drawing']}.values():
            row = re.search(rf'<tr><td>{re.escape(group["part"].replace("&", "&amp;"))}</td>.*?</tr>', table)
            self.assertTrue(row, group['part'])
            self.assertIn('<td>no drawing</td>', row.group(0))
            self.assertIn(f'{group["page"]}.html', row.group(0))

if __name__ == '__main__': unittest.main()
