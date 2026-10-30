"""Invariants on the committed extraction results (notes/*.json). These fail when a re-run produces something odd."""
import os, re, unittest
from helpers import ROOT, load
from match_logic import STRONG

BAG = re.compile(r'^Fixings (Kit )?(Bag )?\d+$')   # 'Fixings Bag 8', 'Fixings Kit 11', 'Fixings Kit Bag 13'

def all_rows():
    for name, path in (('pdf', 'notes/parts.json'), ('image', 'notes/parts_images.json')):
        for sheet in load(path)['sheets']:
            for r in sheet['rows']: yield name, sheet, r

class Rows(unittest.TestCase):
    def test_there_is_data(self):
        self.assertGreater(sum(1 for _ in all_rows()), 200)

    def test_every_row_has_a_part_and_a_whole_quantity(self):
        bad = [(n, s.get('sheet') or s['image'], r) for n, s, r in all_rows() if not r['part'] or not r['qty'].isdigit() or int(r['qty']) < 1]
        self.assertEqual(bad, [])

    def test_fixings_bags_are_named_consistently(self):
        bad = [(n, r['description']) for n, s, r in all_rows() if r['description'].startswith('Fixings') and not BAG.match(r['description'])]
        self.assertEqual(bad, [])

    def test_item_numbers_are_not_repeated_within_a_pdf_sheet(self):
        for s in load('notes/parts.json')['sheets']:
            items = [r['item'] for r in s['rows']]
            self.assertEqual(len(items), len(set(items)), f"sheet {s['sheet']}: {items}")

class Review(unittest.TestCase):
    """Nothing is left unchecked: a run that finds something it is unsure of fails here until a person has looked."""
    def test_pdf_extraction_has_no_problems(self):
        self.assertEqual(load('notes/parts.json')['problems'], [])

    def test_ocr_has_no_rows_left_to_check(self):
        self.assertEqual(load('notes/parts_images.json')['problems'], [])
        left = [(s['image'], r['item'], r['part']) for s in load('notes/parts_images.json')['sheets'] if not s['in_pdf'] for r in s['rows'] if r['review']]
        self.assertEqual(left, [])

class Matches(unittest.TestCase):
    matches = load('notes/sheet_matches.json')['matches']

    def test_every_matched_image_is_in_the_repository(self):
        missing = [n for n in self.matches if not os.path.exists(os.path.join(ROOT, 'docs/images', n))]
        self.assertEqual(missing, [])

    def test_a_confirmed_image_names_a_real_sheet(self):
        sheets = {s['sheet'] for s in load('notes/parts.json')['sheets']}
        self.assertEqual([n for n, m in self.matches.items() if m['status'] == 'confirmed' and m['sheet'] not in sheets], [])

    def test_no_two_confirmed_images_are_the_same_sheet(self):
        owner = {}
        for n, m in self.matches.items():
            if m['status'] == 'confirmed': owner.setdefault(m['sheet'], []).append(n)
        self.assertEqual({s: ns for s, ns in owner.items() if len(ns) > 1}, {})

    def test_nothing_is_waiting_for_a_manual_check(self):
        self.assertEqual([n for n, m in self.matches.items() if m['status'] == 'check'], [])

    def test_heated_bed_corners_is_sheet_9(self):   # regression: its parts used to be compared with the wrong sheet
        m = self.matches['HEATED_BED_CORNERS.jpg']
        self.assertEqual((m['status'], m['sheet'], m['rows_shared']), ('confirmed', 9, 1.0))

    def test_only_low_resolution_images_are_redrawn_or_enlarged(self):
        for n, m in self.matches.items():
            if m.get('action'): self.assertLess(m['image_width'], 1200, n)

    def test_a_visual_confirmation_really_is_strong(self):
        for n, m in self.matches.items():
            if m['status'] == 'confirmed' and m['rows_shared'] is None: self.assertGreaterEqual(m['visual'], STRONG - 0.05, n)

if __name__ == '__main__': unittest.main()
