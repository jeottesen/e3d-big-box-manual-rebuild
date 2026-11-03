"""E3D's own list of the fixings (data/bom.ods, scripts/bom_ods.py) and how the Bill of Materials page merges it with the drawings."""
import glob, html, re, unittest
from helpers import ROOT, load
import bom_ods

OFFICIAL = bom_ods.fixings()
DRAWN = {}
for f in glob.glob(f'{ROOT}/data/sheets/*.json'):
    for r in load(f.replace(ROOT + '/', ''))['rows']:
        if r['description'].upper().startswith('FIXINGS'): DRAWN[r['part']] = int(re.sub(r'\D', '', r['description']) or 0)
PAGE = open(f'{ROOT}/docs/Bill_Of_Materials.html').read()
FIXINGS = PAGE[PAGE.index('id="Fixings"'):]
ROWS = [[html.unescape(re.sub(r'<[^>]+>', '', c)) for c in re.findall(r'<td>(.*?)</td>', r)] for r in re.findall(r'<tr><td>Fixings Bag.*?</tr>', FIXINGS)]

class Sheet(unittest.TestCase):
    def test_the_sheet_lists_the_bags_one_to_seventeen_with_two_quantities_each(self):
        self.assertEqual(sorted({o['bag'] for o in OFFICIAL}), list(range(1, 18)))
        self.assertTrue(all(o['required'] > 0 and o['supplied'] >= o['required'] for o in OFFICIAL))   # a bag has at least as many as the build needs

class OnThePage(unittest.TestCase):
    def test_every_fixing_on_the_sheet_is_a_row_with_its_bag_and_quantities(self):
        page = {(r[0], r[1]): (r[2], r[3]) for r in ROWS}
        for o in OFFICIAL: self.assertEqual(page.get((f'Fixings Bag {o["bag"]}', o['description'])), (str(o['required']), str(o['supplied'])), o['description'])

    def test_a_fixing_only_the_drawings_show_stays_with_no_quantity(self):
        extra = [r for r in ROWS if (r[2], r[3]) == ('–', '–')]
        self.assertEqual([r[1] for r in extra], ['M3 Hex Nut'])   # drawn in bag 3; E3D's list has no plain M3 hex nut, only the half nut in bag 5

    def test_the_rows_are_in_bag_order(self):
        bags = [int(r[0].split()[-1]) for r in ROWS]
        self.assertEqual(bags, sorted(bags))

class WithTheDrawings(unittest.TestCase):
    def test_every_fixing_the_drawings_name_is_on_the_sheet_except_one(self):
        self.assertEqual(sorted(set(DRAWN) - set(bom_ods.match(DRAWN, OFFICIAL))), ['M3 Hex Nut'])

    def test_no_two_drawing_names_are_merged_into_one_sheet_row_by_mistake(self):
        matched = bom_ods.match(DRAWN, OFFICIAL)
        self.assertEqual(len({id(o) for o in matched.values()}), len(matched))

    def test_the_two_bags_the_drawings_disagree_with_the_sheet_on_are_known(self):
        self.assertEqual(sorted(bom_ods.bag_conflicts(DRAWN, OFFICIAL)),
                         [('M3 Microbarb Nut (Brass)', 2, 5), ('Nylon Washer 8 x 16 x 1.6', 13, 16)])   # the manual's own text says nylon washers are in Bag 16, as the sheet does

if __name__ == '__main__': unittest.main()
