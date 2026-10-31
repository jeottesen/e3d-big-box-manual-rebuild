"""Comparing the tools' proposals with the reviewed data (scripts/truth.py)."""
import copy, unittest
import helpers  # noqa: F401  (puts scripts/ on the path)
import truth
from ocr_text import key

def sheet(sid='pdf-01', kind='pdf', rows=None, sha='aaa', images=None):
    return {'id': sid, 'title': 'T', 'source': {'kind': kind, 'file': 'f', 'sha256': sha, 'page': 1}, 'images': images if images is not None else [{'file': 'A.jpg', 'role': 'wiki'}],
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

    def test_an_entered_row_needs_a_basis(self):
        s = sheet('img-A', 'image'); s['rows'][0]['how'] = 'entered'
        self.assertTrue(any('basis' in p for p in truth.problems(s)))
        s['rows'][0]['basis'] = 'the title block'
        self.assertEqual(truth.problems(s), [])

    def test_a_sheet_made_only_of_entered_rows_is_not_reported_as_vanished(self):
        t = sheet('img-A', 'image'); t['rows'][0].update(how='entered', basis='x')
        self.assertEqual(truth.diff({'img-A': t}, {}), [])

    def test_confirmed_needs_who_and_when(self):
        s = copy.deepcopy(sheet()); s['confirmed'] = {'by': 'someone'}
        self.assertTrue(truth.problems(s))


class DiffSeesHowARowWasRead(unittest.TestCase):
    """A change to how a row was read is a difference even when quantity, part and description match."""
    def row_diff(self, **changes):
        t, p = sheet('img-A', 'image'), sheet('img-A', 'image')
        p['rows'][0].update(changes)
        return truth.diff({'img-A': t}, {'img-A': p})

    def test_how(self): self.assertTrue(self.row_diff(how='ocr+fix', read_as={'part': 'x', 'description': 'y'}))
    def test_approx(self): self.assertTrue(self.row_diff(approx=True))
    def test_unsure(self): self.assertTrue(self.row_diff(unsure=True))

    def test_what_the_tool_read(self):
        t, p = sheet('img-A', 'image'), sheet('img-A', 'image')
        t['rows'][0].update(how='hand', read_as={'part': 'a', 'description': 'b'})
        p['rows'][0].update(how='hand', read_as={'part': 'c', 'description': 'b'})
        self.assertTrue(truth.diff({'img-A': t}, {'img-A': p}))

class Key(unittest.TestCase):
    def test_the_multiplication_sign_is_an_x_not_nothing(self):
        self.assertEqual(key('M3×10'), key('M3 x 10'))
        self.assertNotEqual(key('M3×10'), key('M3-10'))

    def test_spacing_punctuation_and_case_do_not_matter(self):
        self.assertEqual(key('M3 Hex Nut (Half)'), key('m3hexnut half'))

class HandEditsNeverCrashTheChecks(unittest.TestCase):
    """problems() must return a list of complaints, whatever shape a hand edit left."""
    def bad(self, mutate):
        s = sheet('img-A', 'image'); mutate(s)
        self.assertTrue(truth.problems(s))

    def test_source_is_not_an_object(self): self.bad(lambda s: s.update(source='pdf'))
    def test_rows_are_not_a_list(self): self.bad(lambda s: s.update(rows={}))
    def test_a_row_is_not_an_object(self): self.bad(lambda s: s['rows'].append('x'))
    def test_images_are_not_a_list(self): self.bad(lambda s: s.update(images='A.jpg'))
    def test_a_boolean_is_not_a_quantity(self): self.bad(lambda s: s['rows'][0].update(qty=True))
    def test_a_missing_description(self): self.bad(lambda s: s['rows'][0].pop('description'))
    def test_an_image_sheet_with_no_image_would_crash_the_build(self): self.bad(lambda s: s.update(images=[]))
    def test_an_image_sheet_cannot_have_a_drawn_image(self): self.bad(lambda s: s['images'][0].update(role='lost'))
    def test_the_id_must_match_the_kind(self): self.bad(lambda s: s.update(id='pdf-01'))
    def test_approx_must_be_a_boolean(self): self.bad(lambda s: s['rows'][0].update(approx='yes'))

    def test_a_pdf_sheet_needs_its_page(self):
        s = sheet('pdf-01', 'pdf'); s['source'].pop('page')
        self.assertTrue(truth.problems(s))

    def test_not_even_an_object(self): self.assertTrue(truth.problems([]))

class AllProblems(unittest.TestCase):
    def test_a_sound_set_has_none(self):
        self.assertEqual(truth.all_problems({'pdf-01': sheet(images=[]), 'img-A': sheet('img-A', 'image')}), [])

    def test_a_drawing_claimed_by_two_sheets(self):
        out = truth.all_problems({'img-A': sheet('img-A', 'image'), 'img-B': sheet('img-B', 'image')})   # both list A.jpg
        self.assertTrue(any('more than one sheet' in p for p in out))

    def test_a_file_name_that_differs_from_its_id(self):
        self.assertTrue(any('differ' in p for p in truth.all_problems({'img-Z': sheet('img-A', 'image')})))

if __name__ == '__main__': unittest.main()
