"""The STEP files of the printed parts (downloads/printed-parts/, scripts/printed_parts.py) and their links on the Bill of Materials."""
import hashlib, html, os, re, unittest
from helpers import ROOT
import printed_parts as pp
from targets import STEP_SOURCES, UNRECORDED

D = f'{ROOT}/downloads/printed-parts'
ROWS = pp.load()
BOM = open(f'{ROOT}/docs/Bill_Of_Materials.html').read()
PRINTED = BOM[BOM.index('id="Printed_Parts"'):BOM.index('id="Fixings"')]
TABLE = PRINTED[:PRINTED.index('id="Not_Printed_Parts"')]   # the table of rows; after it come the files that have none
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
        main, _, _, _ = pp.classify(ROWS, BOM_NAMES)
        self.assertTrue({r['name'] for r in ROWS if r['in_bom'] == 'True'} <= {r['name'] for r in main.values()})

    def test_the_alternates_and_the_mirrors_are_on_the_row_of_their_standard_part(self):
        for row in TABLE.split('<tr>')[1:]:
            name = re.sub(r'<[^>]+>', '', row.split('</td>')[0])
            if name in ('Z-AXIS BASE BRACKET LOWER', 'Z-AXIS BASE BRACKET UPPER'): self.assertIn('4-hole.step">STEP (alternate', row, name)
            if name in ('SPOOL-HOLDER OUTER (L)', 'Y-AXIS REAR (L)'): self.assertIn('STEP (R, the mirror image)', row, name)

    def test_the_page_says_the_right_spool_holder_was_made_by_mirroring(self):
        self.assertIn('SPOOL-HOLDER OUTER (R) was made by mirroring the (L) part', PRINTED)

    def test_each_file_with_no_row_of_its_own_is_listed_in_the_table_with_the_step_that_uses_it(self):
        own = [r for r in ROWS if r['in_bom'] != 'True' and not r['name'].endswith(('(4 hole)', '(R)'))]
        self.assertTrue(own)
        for r in own:
            row = next(x for x in TABLE.split('<tr>') if x.startswith(f'<td>{html.escape(pp.bom_name(r))}</td>'))
            self.assertRegex(row, r'<a href="[^"#]+\.html#[^"]+">', r['name'])   # the step the manual puts it in
            self.assertIn(pp.href(r), row)

    def test_the_parts_with_no_file_are_listed_with_the_printed_parts_and_have_no_step_link(self):
        for name in ('IEC Back Cover', 'Non-Titan Direct-Drive Bowden Main Block'):
            row = next(x for x in TABLE.split('<tr>') if x.startswith(f'<td>{name}</td>'))
            self.assertTrue(row.rstrip().endswith('<td></td></tr></tbody></table>') or row.rstrip().endswith('<td></td></tr>'), name)

    def test_what_is_not_printed_is_in_its_own_table_with_no_step_column(self):
        other = PRINTED[PRINTED.index('id="Not_Printed_Parts"'):]
        for name in ('Cork Pads', 'Black Spring', 'Hobgoblin', 'Embedded Bowden Coupler'):
            self.assertIn(f'<td>{name}</td>', other)
            self.assertNotIn(f'<td>{name}</td>', TABLE)
        self.assertNotIn('<th>STEP</th>', other)

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

class Licence(unittest.TestCase):
    def test_every_file_is_marked_cc_by_sa_and_the_folder_and_notice_say_so(self):
        self.assertEqual({r['license'] for r in ROWS}, {'CC BY-SA 3.0'})
        for path in (f'{D}/README.md', f'{ROOT}/NOTICE.md'):
            text = open(path).read()
            self.assertIn('thing:1521722', text, path)
            self.assertIn('CC BY-SA 3.0', text, path)

if __name__ == '__main__': unittest.main()
