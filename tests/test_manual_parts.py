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

class Group(unittest.TestCase):
    def entry(self, part, qty=1, step_id='s', page='P', container='printed'):
        return {'page': page, 'step_id': step_id, 'step': '(1) S', 'qty': qty, 'part': part, 'container': container, 'drawing': None, 'note': ''}

    def test_a_mapped_name_is_covered_by_its_drawing_row(self):
        covered, none = mp.group([self.entry('Dock')], {'Dock': ('img-DOCK', 'DOCK-BRACKET')})
        self.assertEqual([(e['part'], sid, name) for e, sid, name in covered], [('Dock', 'img-DOCK', 'DOCK-BRACKET')])
        self.assertEqual(none, [])

    def test_an_unmapped_name_has_no_drawing(self):
        self.assertEqual([g['part'] for g in mp.group([self.entry('Drive Supports', 2)], {})[1]], ['Drive Supports'])

    def test_a_part_listed_in_two_steps_is_one_part_linking_both(self):
        none = mp.group([self.entry('Clamp', step_id='a', page='Prep'), self.entry('Clamp', step_id='b', page='Fit')], {})[1]
        self.assertEqual(len(none), 1)
        self.assertEqual([(pg, sid) for pg, sid, _ in none[0]['steps']], [('Prep', 'a'), ('Fit', 'b')])

    def test_the_same_step_twice_is_listed_once(self):
        self.assertEqual(len(mp.group([self.entry('Clamp'), self.entry('Clamp')], {})[1][0]['steps']), 1)

    def test_names_that_differ_only_in_spacing_and_case_are_one_part(self):
        self.assertEqual(len(mp.group([self.entry('Drive Supports'), self.entry('drive  supports')], {})[1]), 1)

    def test_the_largest_quantity_is_kept(self):
        self.assertEqual(mp.group([self.entry('C', 1), self.entry('C', 2)], {})[1][0]['qty'], 2)

# ---- the table in targets.py and the manual
from targets import MANUAL_PART_NAMES
PAGES = mp.read_pages()
FOUND = mp.scan(PAGES)
SHEETS = truth.load_truth()

class TheTable(unittest.TestCase):
    def test_the_manual_has_no_printed_part_item_this_tool_cannot_read(self):
        self.assertEqual(mp.unparsed(PAGES), [])

    def test_every_name_in_the_table_is_still_in_the_manual(self):
        self.assertEqual([n for n in MANUAL_PART_NAMES if n not in {e['part'] for e in FOUND}], [])

    def test_every_name_in_the_table_is_a_row_of_the_sheet_it_says(self):
        for name, (sid, part) in MANUAL_PART_NAMES.items():
            self.assertIn(truth.key(part), [truth.key(r['part']) for r in SHEETS[sid]['rows']], name)

    def test_a_mapped_part_is_a_printed_part_on_its_drawing(self):
        for name, (sid, part) in MANUAL_PART_NAMES.items():
            row = next(r for r in SHEETS[sid]['rows'] if truth.key(r['part']) == truth.key(part))
            self.assertEqual(row['description'], 'Printed Part', name)

    def test_the_parts_the_user_found_have_no_drawing(self):
        none = {g['part']: g for g in mp.group(FOUND, MANUAL_PART_NAMES)[1]}
        self.assertEqual((none['Drive Supports']['qty'], [st[2] for st in none['Drive Supports']['steps']]), (2, ['(10) Z-Axis Bed Assembly']))

def bom_rows():
    with open(os.path.join(ROOT, 'docs/Bill_Of_Materials.html'), encoding='utf-8') as f: bom = f.read()
    table = bom[bom.index('id="Printed_Parts"'):bom.index('id="Fixings"')]
    return bom, table

class InTheBom(unittest.TestCase):
    def test_every_part_without_a_drawing_is_a_row_linked_to_its_step(self):
        _, table = bom_rows()
        for g in mp.group(FOUND, MANUAL_PART_NAMES)[1]:
            row = re.search(rf'<tr><td>{re.escape(g["part"].replace("&", "&amp;"))}</td>.*?</tr>', table)
            self.assertTrue(row, g['part'])
            self.assertIn('<td>no drawing</td>', row.group(0))
            for page, _, _ in g['steps']: self.assertIn(f'{page}.html', row.group(0))

    def test_a_part_a_drawing_covers_shows_the_quantity_the_manual_uses_and_one_name(self):
        _, table = bom_rows()
        for e, _sid, part in mp.group(FOUND, MANUAL_PART_NAMES)[0]:
            row = re.search(rf'<tr><td>{re.escape(part)}</td><td>(\d+)</td>.*?</tr>', table)
            self.assertTrue(row, part)
            self.assertEqual(int(row.group(1)), e['qty'], part)                       # the manual's quantity (4 corners of the Z bed), not the drawing's 1
            if e['part'] != part: self.assertNotIn(f'<td>{e["part"]}</td>', table, e['part'])   # one name: the drawing's, not also the manual's

    def test_the_heading_says_the_table_holds_box_and_bag_items(self):
        bom, _ = bom_rows()
        self.assertIn('id="Printed_Parts">Printed Parts, Printed Parts Box and Printed Parts Bag<', bom)
        self.assertIn('Printed Parts, Printed Parts Box and Printed Parts Bag</a>', bom)   # and so does the page's contents list

    def test_box_and_bag_items_are_labelled_with_where_they_come_from(self):
        _, table = bom_rows()
        for g in mp.group(FOUND, MANUAL_PART_NAMES)[1]:
            row = re.search(rf'<tr><td>{re.escape(g["part"])}</td>.*?</tr>', table).group(0)
            self.assertIn(f'<td>{mp.CONTAINER_LABEL[g["container"]]}</td>', row)

if __name__ == '__main__': unittest.main()
