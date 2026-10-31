"""Accepting a proposal (scripts/drift.py): it merges into the reviewed data and must not throw away what a person added."""
import contextlib, copy, io, tempfile, unittest
from unittest import mock
import helpers  # noqa: F401  (puts scripts/ on the path)
import drift, truth

def row(part='M3 Nut', qty=2, how='ocr', **extra):
    r = {'item': '1', 'qty': qty, 'part': part, 'description': 'Fixings Bag 5', 'how': how}
    r.update(extra)
    return r

def sheet(sid='img-A', kind='image', rows=None, confirmed=None, sha='a', images=None, title='T', notes=''):
    return {'id': sid, 'title': title, 'source': {'kind': kind, 'file': 'f', 'sha256': sha, 'page': 1},
            'images': images if images is not None else [{'file': f'{sid}.jpg', 'role': 'wiki'}],
            'rows': rows if rows is not None else [row()], 'confirmed': confirmed, 'notes': notes}

CHECKED = {'by': 'J', 'on': '2026-10-30'}

class Merge(unittest.TestCase):
    def test_a_reviewed_correction_survives_when_the_tool_reads_the_same_row(self):
        reviewed = row('M3 Nut', how='hand', read_as={'part': 'M3Nut', 'description': 'Fixings Bag 5'}, approx=True)
        old = sheet(rows=[reviewed], confirmed=CHECKED, notes='n')
        new = sheet(rows=[row('M3Nut', how='ocr')])
        got = drift.merge(old, new)
        self.assertEqual(got['rows'], [reviewed])      # how, read_as and approx are not lost
        self.assertEqual(got['confirmed'], CHECKED)    # nothing a person checked has changed
        self.assertEqual(got['notes'], 'n')

    def test_a_changed_quantity_takes_the_proposal_and_asks_for_a_new_check(self):
        old = sheet(rows=[row(qty=2)], confirmed=CHECKED)
        got = drift.merge(old, sheet(rows=[row(qty=3)]))
        self.assertEqual([r['qty'] for r in got['rows']], [3])
        self.assertIsNone(got['confirmed'])

    def test_a_row_the_tools_no_longer_read_is_dropped(self):
        old = sheet(rows=[row('A'), row('B')], confirmed=CHECKED)
        self.assertEqual([r['part'] for r in drift.merge(old, sheet(rows=[row('A')]))['rows']], ['A'])

    def test_a_row_a_person_entered_is_never_dropped(self):
        entered = row('Nut trap', how='entered', basis='the manual', approx=True)
        got = drift.merge(sheet(rows=[row('A'), entered], confirmed=CHECKED), sheet(rows=[row('A')]))
        self.assertIn(entered, got['rows'])

    def test_a_new_image_or_title_alone_does_not_cancel_a_check(self):
        old = sheet(confirmed=CHECKED)
        new = sheet(images=[{'file': 'B.jpg', 'role': 'enlarged'}], title='Other')
        got = drift.merge(old, new)
        self.assertEqual((got['confirmed'], got['title'], got['images'][0]['role']), (CHECKED, 'Other', 'enlarged'))

    def test_a_changed_pdf_cancels_a_check(self):
        self.assertIsNone(drift.merge(sheet('pdf-01', 'pdf', confirmed=CHECKED, sha='a'), sheet('pdf-01', 'pdf', sha='b'))['confirmed'])

    def test_a_proposal_with_nothing_reviewed_is_taken_as_it_is(self):
        new = sheet()
        self.assertEqual(drift.merge(None, new), new)

    def test_the_inputs_are_not_changed(self):
        old, new = sheet(confirmed=CHECKED), sheet(rows=[row(qty=9)])
        before = copy.deepcopy((old, new))
        drift.merge(old, new)
        self.assertEqual((old, new), before)

class WithData(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        patch = mock.patch.object(truth, 'DATA', self.tmp)
        patch.start(); self.addCleanup(patch.stop)

    def run_main(self, argv, proposed):
        out = io.StringIO()
        with mock.patch.object(truth, 'proposals', return_value=proposed), contextlib.redirect_stdout(out):
            code = drift.main(argv)
        return code, out.getvalue()

class Accept(WithData):
    def test_a_bad_sheet_leaves_nothing_half_written(self):
        good, bad = sheet('img-A'), sheet('img-B'); bad['rows'][0]['qty'] = 'x'
        with self.assertRaises(SystemExit): drift.accept(['img-A', 'img-B'], {'img-A': good, 'img-B': bad}, {}, None)
        self.assertEqual(truth.load_truth(), {})

    def test_it_writes_and_can_confirm(self):
        with contextlib.redirect_stdout(io.StringIO()): drift.accept(['img-A'], {'img-A': sheet()}, {}, 'J')
        self.assertEqual(truth.load_truth()['img-A']['confirmed']['by'], 'J')

class AcceptAll(WithData):
    def test_it_does_not_accept_a_changed_pdf_or_changed_exact_text(self):
        truth.write_sheet(sheet('pdf-01', 'pdf', sha='a', images=[]))
        truth.write_sheet(sheet('img-A', rows=[row(qty=2)], confirmed=CHECKED))
        proposed = {'pdf-01': sheet('pdf-01', 'pdf', sha='b', images=[]), 'img-A': sheet('img-A', rows=[row(qty=3)])}
        code, out = self.run_main(['--accept-all'], proposed)
        self.assertEqual(code, 0)
        self.assertIn('skipped pdf-01', out)
        self.assertEqual(truth.load_truth()['pdf-01']['source']['sha256'], 'a')                # untouched
        self.assertEqual(truth.load_truth()['img-A']['rows'][0]['qty'], 3)                      # the OCR sheet was accepted

    def test_it_cannot_stamp_sheets_as_checked(self):
        with self.assertRaises(SystemExit): drift.parse(['--accept-all', '--confirm', 'J'])

class Report(WithData):
    def test_malformed_data_is_reported_not_a_traceback(self):
        s = sheet(); s.pop('source')
        truth.write_sheet(s)
        with mock.patch.object(truth, 'proposals', side_effect=AssertionError('must not be reached')), contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(drift.main([]), 1)
        self.assertIn('missing "source"', out.getvalue())

    def test_a_change_to_exact_pdf_text_fails_the_report(self):
        truth.write_sheet(sheet('pdf-01', 'pdf', images=[]))
        code, _ = self.run_main([], {'pdf-01': sheet('pdf-01', 'pdf', rows=[row(qty=9)], images=[])})
        self.assertEqual(code, 1)

    def test_strict_fails_on_any_difference(self):
        truth.write_sheet(sheet(confirmed=CHECKED))
        proposed = {'img-A': sheet(rows=[row(qty=3)])}
        self.assertEqual(self.run_main([], proposed)[0], 0)
        self.assertEqual(self.run_main(['--strict'], proposed)[0], 1)

class Arguments(unittest.TestCase):
    def test_what_is_accepted(self):
        self.assertEqual(drift.parse(['--accept', 'a', 'b', '--confirm', 'J']), {'--accept': ['a', 'b'], '--confirm': ['J']})
        self.assertEqual(drift.parse([]), {})

    def test_what_is_refused(self):
        for argv in (['--bogus'], ['--confirm'], ['--accept'], ['--accept', '--confirm', 'J'], ['--confirm', '--strict']):
            with self.assertRaises(SystemExit, msg=argv): drift.parse(argv)

if __name__ == '__main__': unittest.main()
