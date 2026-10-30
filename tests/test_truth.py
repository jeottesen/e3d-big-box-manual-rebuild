"""Comparing the tools' proposals with the reviewed data (scripts/truth.py)."""
import copy, unittest
import helpers  # noqa: F401  (puts scripts/ on the path)
import truth

def sheet(sid='pdf-01', kind='pdf', rows=None, sha='aaa'):
    return {'id': sid, 'title': 'T', 'source': {'kind': kind, 'sha256': sha, 'page': 1}, 'images': [{'file': 'A.jpg', 'role': 'wiki'}],
            'rows': rows if rows is not None else [{'item': '1', 'qty': 2, 'part': 'M3 Nut', 'description': 'Fixings Bag 5', 'how': 'pdf-text' if kind == 'pdf' else 'ocr'}],
            'confirmed': None, 'notes': ''}

class Diff(unittest.TestCase):
    def test_no_difference(self):
        self.assertEqual(truth.diff({'pdf-01': sheet()}, {'pdf-01': sheet()}), [])

    def test_item_numbers_and_spacing_are_not_differences(self):
        p = sheet(); p['rows'][0]['item'] = '7'; p['rows'][0]['part'] = 'M3Nut'
        self.assertEqual(truth.diff({'pdf-01': sheet()}, {'pdf-01': p}), [])

    def test_a_change_to_exact_pdf_text_is_an_error(self):
        p = sheet(); p['rows'][0]['qty'] = 3
        self.assertEqual({sev for sev, _, _ in truth.diff({'pdf-01': sheet()}, {'pdf-01': p})}, {'error'})

    def test_a_change_to_ocr_text_is_only_information(self):
        t, p = sheet('img-A', 'image'), sheet('img-A', 'image')
        p['rows'][0]['part'] = 'M4 Nut'
        self.assertEqual({sev for sev, _, _ in truth.diff({'img-A': t}, {'img-A': p})}, {'info'})

    def test_a_changed_pdf_is_an_error(self):
        self.assertEqual([sev for sev, _, _ in truth.diff({'pdf-01': sheet(sha='aaa')}, {'pdf-01': sheet(sha='bbb')})], ['error'])

    def test_new_and_vanished_sheets_are_information(self):
        out = truth.diff({'pdf-01': sheet()}, {'pdf-02': sheet('pdf-02')})
        self.assertEqual(sorted((sev, sid) for sev, sid, _ in out), [('info', 'pdf-01'), ('info', 'pdf-02')])

class Shape(unittest.TestCase):
    def test_a_good_sheet_has_no_problems(self):
        self.assertEqual(truth.problems(sheet()), [])

    def test_quantity_must_be_a_whole_number(self):
        s = sheet(); s['rows'][0]['qty'] = '2'
        self.assertTrue(truth.problems(s))

    def test_a_corrected_row_must_keep_what_the_tool_read(self):
        s = sheet('img-A', 'image'); s['rows'][0]['how'] = 'ocr+fix'
        self.assertTrue(any('read_as' in p for p in truth.problems(s)))

    def test_confirmed_needs_who_and_when(self):
        s = copy.deepcopy(sheet()); s['confirmed'] = {'by': 'someone'}
        self.assertTrue(truth.problems(s))

if __name__ == '__main__': unittest.main()
