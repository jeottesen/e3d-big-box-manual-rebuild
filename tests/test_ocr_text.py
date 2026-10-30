"""The OCR text rules (scripts/ocr_text.py). The rule that matters most: a correction never changes a number."""
import unittest
from helpers import load
from ocr_text import key, vocabulary, parts_by_description, respace, normalise, fix_row, digits
from targets import OCR_FIXES

class Respace(unittest.TestCase):
    def test_puts_spaces_back(self):
        self.assertEqual(respace('M3x10SocketCapScrew', {}), 'M3 x 10 Socket Cap Screw')
        self.assertEqual(respace('FixingsBag8', {}), 'Fixings Bag 8')
        self.assertEqual(respace('M3HexNut(Half)', {}), 'M3 Hex Nut (Half)')

    def test_spacing_varies_between_reads_of_the_same_name(self):
        for read in ('M2HexNut', 'M2Hex Nut', 'M2 HexNut'): self.assertEqual(respace(read, {}), 'M2 Hex Nut', read)

    def test_exact_pdf_string_wins(self):
        self.assertEqual(respace('YAXISREAR(L)', {'YAXISREARL': 'Y-AXIS REAR (L)'}), 'Y-AXIS REAR (L)')

class Normalise(unittest.TestCase):
    def test_fixings_bag_garbles_by_pattern(self):
        for read, want in (('Foings Bog8', 'Fixings Bag 8'), ('Fxinss Bag 12', 'Fixings Bag 12'), ('Fiings Bag17', 'Fixings Bag 17')):
            self.assertEqual(normalise(read, {}, 0.9), want)   # a bag number's own digits must survive: 'Bag17' is 17, not 7

    def test_confident_text_is_left_alone(self):
        vocab = {key('SPOOL-HOLDER INNER'): 'SPOOL-HOLDER INNER'}
        self.assertEqual(normalise('SPOOL-HOLDER CLAMP INNER', vocab, 0.97), 'SPOOL-HOLDER CLAMP INNER')   # a new part, not a misread of an old one

    def test_never_changes_a_number(self):
        vocab = {key('ROD-G.H.SS-8-384'): 'ROD-G.H.SS-8-384'}
        self.assertEqual(normalise('ROD-G.H.SS-8-364', vocab, 0.5), 'ROD-G.H.SS-8-364')

class FixRow(unittest.TestCase):
    vocab = {key('M3 Hex Nut'): 'M3 Hex Nut', key('Fixings Bag 3'): 'Fixings Bag 3'}
    by_desc = {key('Fixings Bag 3'): {key('M3 Hex Nut'): 'M3 Hex Nut'}}

    def test_a_bag_does_not_turn_an_m2_nut_into_an_m3_nut(self):
        part, desc, by_hand = fix_row('M2 Hex Nut', 'Fixings Bag 3', 0.5, self.vocab, self.by_desc, {})
        self.assertEqual((part, desc, by_hand), ('M2 Hex Nut', 'Fixings Bag 3', False))

    def test_hand_fix_wins_and_counts_as_checked(self):
        part, desc, by_hand = fix_row('MAWasher', 'Fixings Bag 13', 0.8, self.vocab, self.by_desc, {key('MAWasher'): 'M4 Washer'})
        self.assertEqual((part, by_hand), ('M4 Washer', True))

class HandFixes(unittest.TestCase):
    def test_the_m3_hex_nut_misread_as_m2_is_a_hand_fix(self):
        # no M2 screws or nuts are listed anywhere in the drawings, and the hybrid drawings print the M3 nut as 'M2' (a typo in
        # the source). The automatic rules must not make this change (they never change a number), so it is recorded by hand.
        self.assertEqual(OCR_FIXES['M2Hex Nut'], 'M3 Hex Nut')

class CommittedData(unittest.TestCase):
    """The same rule, checked on what is committed: only a hand fix (OCR_FIXES) may change the digits of a name."""
    def test_automatic_corrections_keep_digits(self):
        fixes = {key(k) for k in OCR_FIXES}
        bad = []
        for sheet in load('notes/parts_images.json')['sheets']:
            for r in sheet['rows']:
                if 'ocr' not in r: continue
                for f in ('part', 'description'):
                    if r['ocr'][f] != r[f] and key(r['ocr'][f]) not in fixes and digits(r['ocr'][f]) != digits(r[f]):
                        bad.append((sheet['image'], r['item'], r['ocr'][f], r[f]))
        self.assertEqual(bad, [])

    def test_hand_fixes_do_not_collide(self):
        keys = [key(k) for k in OCR_FIXES]
        self.assertEqual(len(keys), len(set(keys)))

    def test_vocabulary_is_built_from_the_pdf(self):
        sheets = load('notes/parts.json')['sheets']
        v = vocabulary(sheets)
        self.assertIn(key('M3 Hex Nut'), v)
        self.assertIn(key('Fixings Bag 3'), parts_by_description(sheets))

if __name__ == '__main__': unittest.main()
