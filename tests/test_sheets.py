"""The reviewed per-sheet data (data/sheets/*.json), which the build reads. Fails when a sheet is malformed, unchecked, or contradicts the PDF."""
import os, re, unittest
from helpers import ROOT
import truth
from ocr_text import digits
from targets import OCR_FIXES
from ocr_text import key

SHEETS = truth.load_truth()
BAG = re.compile(r'^Fixings (Kit )?(Bag )?\d+$')   # 'Fixings Bag 8', 'Fixings Kit 11', 'Fixings Kit Bag 13'

def rows():
    for s in SHEETS.values():
        for r in s['rows']: yield s, r

class Shape(unittest.TestCase):
    def test_there_is_data(self):
        self.assertGreater(len(SHEETS), 30)
        self.assertGreater(sum(1 for _ in rows()), 200)

    def test_every_sheet_is_well_formed(self):
        self.assertEqual({sid: truth.problems(s) for sid, s in SHEETS.items() if truth.problems(s)}, {})

    def test_file_names_match_ids(self):
        self.assertEqual([sid for sid, s in SHEETS.items() if s['id'] != sid], [])

    def test_fixings_bags_are_named_consistently(self):
        self.assertEqual([(s['id'], r['description']) for s, r in rows() if r['description'].startswith('Fixings') and not BAG.match(r['description'])], [])

    def test_item_numbers_are_not_repeated_within_a_pdf_sheet(self):
        for s in SHEETS.values():
            if s['source']['kind'] == 'pdf':
                items = [r['item'] for r in s['rows']]
                self.assertEqual(len(items), len(set(items)), f"{s['id']}: {items}")

class Provenance(unittest.TestCase):
    def test_pdf_sheets_were_read_from_the_pdf_in_the_repository(self):
        sha = truth.sha256(truth.PDF)
        wrong = [s['id'] for s in SHEETS.values() if s['source']['kind'] == 'pdf' and s['source']['sha256'] != sha]
        self.assertEqual(wrong, [])

    def test_pdf_sheet_ids_match_their_page(self):
        self.assertEqual([s['id'] for s in SHEETS.values() if s['source']['kind'] == 'pdf' and s['id'] != f"pdf-{s['source']['page']:02d}"], [])

    def test_image_sheets_were_read_from_the_image_recorded(self):
        for s in SHEETS.values():
            if s['source']['kind'] == 'image':
                self.assertEqual(truth.sha256(os.path.join(ROOT, s['source']['file'])), s['source']['sha256'], s['id'])

    def test_every_image_is_in_the_repository(self):
        self.assertEqual([im['file'] for s in SHEETS.values() for im in s['images'] if not os.path.exists(os.path.join(ROOT, 'docs/images', im['file']))], [])

    def test_an_enlarged_or_redrawn_image_keeps_the_wikis_original(self):
        for s in SHEETS.values():
            for im in s['images']:
                if im['role'] in ('enlarged', 'redrawn'): self.assertTrue(os.path.exists(os.path.join(ROOT, 'docs/images/original', im['file'])), im['file'])

    def test_no_image_belongs_to_two_sheets(self):
        owners = {}
        for s in SHEETS.values():
            for im in s['images']: owners.setdefault(im['file'], []).append(s['id'])
        self.assertEqual({f: ids for f, ids in owners.items() if len(ids) > 1}, {})

    def test_heated_bed_corners_is_sheet_9(self):   # regression: its parts were once compared with the wrong sheet
        self.assertIn(('HEATED_BED_CORNERS.jpg', 'wiki'), [(i['file'], i['role']) for i in SHEETS['pdf-09']['images']])

class Review(unittest.TestCase):
    """Nothing read by OCR is used until a person has checked it against the drawing."""
    def test_every_ocr_sheet_is_confirmed(self):
        self.assertEqual([s['id'] for s in SHEETS.values() if s['source']['kind'] == 'image' and s['confirmed'] is None], [])

    def test_no_row_is_marked_unsure_on_a_confirmed_sheet_without_being_fixed(self):
        self.assertEqual([(s['id'], r['part']) for s, r in rows() if r.get('unsure') and r['how'] == 'ocr'], [])

class Corrections(unittest.TestCase):
    """A correction never changes a number unless a person made it (how: hand)."""
    def test_automatic_corrections_keep_digits(self):
        bad = []
        for s, r in rows():
            if r['how'] == 'ocr+fix':
                for f in ('part', 'description'):
                    if digits(r['read_as'][f]) != digits(r[f]): bad.append((s['id'], r['read_as'][f], r[f]))
        self.assertEqual(bad, [])

    def test_a_hand_correction_is_one_in_the_hand_table(self):
        fixes = {key(k) for k in OCR_FIXES}
        self.assertEqual([(s['id'], r['read_as']) for s, r in rows() if r['how'] == 'hand' and not ({key(r['read_as']['part']), key(r['read_as']['description'])} & fixes)], [])

    def test_the_m3_hex_nut_is_m3_everywhere(self):
        self.assertEqual([(s['id'], r['part']) for s, r in rows() if r['part'].startswith('M2') and 'Hex Nut' in r['part']], [])

if __name__ == '__main__': unittest.main()
