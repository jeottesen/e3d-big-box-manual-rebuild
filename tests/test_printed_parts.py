"""The STEP files of the printed parts (downloads/printed-parts/, scripts/printed_parts.py) and their links on the Bill of Materials."""
import hashlib, html, os, re, unittest
from helpers import ROOT
import printed_parts as pp
from targets import STEP_SOURCES, UNRECORDED

D = f'{ROOT}/downloads/printed-parts'
ROWS = pp.load()
BOM = open(f'{ROOT}/docs/Bill_Of_Materials.html').read()
PRINTED = BOM[BOM.index('id="Printed_Parts"'):BOM.index('id="Fixings"')]
TABLE = PRINTED[:PRINTED.index('id="Printed_Parts_With_No_Row"')]   # the table of rows; after it come the files that have none
BOM_NAMES = [html.unescape(re.sub(r'<[^>]+>', '', c)) for c in re.findall(r'<tr><td>(.*?)</td><td>', TABLE)]
HREFS = re.findall(r'href="\.\./downloads/printed-parts/(parts/[^"]+)"', PRINTED)

class Files(unittest.TestCase):
    def test_every_row_has_its_file_and_every_file_has_its_row(self):
        self.assertEqual(sorted(f'parts/{f}' for f in os.listdir(f'{D}/parts')), sorted(r['file'] for r in ROWS))

    def test_every_file_matches_its_checksum(self):
        sums = dict(reversed(l.split('  ', 1)) for l in open(f'{D}/SHA256SUMS').read().splitlines() if l)
        for r in ROWS:
            with open(f'{D}/{r["file"]}', 'rb') as f: digest = hashlib.sha256(f.read()).hexdigest()
            self.assertEqual((digest, sums.get(r['file'])), (r['sha256'], r['sha256']), r['file'])

    def test_a_dual_and_a_regular_file_are_told_apart_by_name(self):
        self.assertEqual(sorted(pp.bom_name(r) for r in ROWS if r['name'] == 'X-AXIS CARRIAGE BEARING CLAMP'),
                         ['X-AXIS CARRIAGE BEARING CLAMP', 'X-AXIS CARRIAGE BEARING CLAMP DUAL'])

class OnTheBillOfMaterials(unittest.TestCase):
    def test_every_file_is_linked_exactly_once_and_no_other_file_is(self):
        self.assertEqual(sorted(HREFS), sorted(pp.href(r).split('printed-parts/', 1)[1] for r in ROWS))

    def test_every_file_the_package_says_is_on_a_row_is_on_that_row(self):
        main, _, _, extras = pp.classify(ROWS, BOM_NAMES)
        self.assertEqual(sorted(r['name'] for r in main.values()), sorted(r['name'] for r in ROWS if r['in_bom'] == 'True'))
        self.assertTrue(all(r['in_bom'] != 'True' for r in extras))

    def test_the_alternates_and_the_mirrors_are_on_the_row_of_their_standard_part(self):
        for row in TABLE.split('<tr>')[1:]:
            name = re.sub(r'<[^>]+>', '', row.split('</td>')[0])
            if name in ('Z-AXIS BASE BRACKET LOWER', 'Z-AXIS BASE BRACKET UPPER'): self.assertIn('4-hole.step">STEP (alternate', row, name)
            if name in ('SPOOL-HOLDER OUTER (L)', 'Y-AXIS REAR (L)'): self.assertIn('STEP (R, the mirror image)', row, name)

    def test_the_page_says_the_right_spool_holder_was_made_by_mirroring(self):
        self.assertIn('SPOOL-HOLDER OUTER (R) was made by mirroring the (L) part', PRINTED)

    def test_each_part_with_no_row_says_which_step_uses_it(self):
        extras = PRINTED[PRINTED.index('id="Printed_Parts_With_No_Row"'):]
        for row in extras.split('<tr>')[2:]:
            self.assertRegex(row, r'<a href="[^"#]+\.html#[^"]+">', row[:80])

class Sources(unittest.TestCase):
    def test_every_original_file_is_listed_with_how_many_parts_came_from_it(self):
        counts = {}
        for r in ROWS: counts[r['source_file']] = counts.get(r['source_file'], 0) + 1
        self.assertEqual(sorted(counts), sorted(n for n, *_ in STEP_SOURCES))
        for name, _url, note, _licence in STEP_SOURCES: self.assertIn(f'{counts[name]} ', note, name)

    def test_the_source_and_licence_of_every_original_file_are_recorded(self):
        for name, url, _note, licence in STEP_SOURCES:
            self.assertTrue(url, f'{name}: no source address')
            self.assertNotEqual(licence, UNRECORDED, name)

if __name__ == '__main__': unittest.main()
