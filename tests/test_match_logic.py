"""Which PDF sheet an image is (scripts/match_logic.py)."""
import unittest
import helpers  # noqa: F401  (puts scripts/ on the path)
from match_logic import decide

class Decide(unittest.TestCase):
    def test_a_drawing_that_looks_the_same_and_unlike_any_other_is_confirmed(self):
        self.assertEqual(decide({1: 0.96, 2: 0.46, 3: 0.3}, [], {}), ('confirmed', 1))

    def test_title_and_parts_confirm_a_sheet_that_looks_different(self):
        # HEATED_BED_CORNERS: another view of sheet 9, so it looks more like sheet 10, but its parts are all on sheet 9
        self.assertEqual(decide({9: 0.57, 10: 0.66, 4: 0.62}, [9], {9: 1.0}), ('confirmed', 9))

    def test_parts_are_compared_with_the_sheet_the_title_names_not_the_one_it_looks_like(self):
        # the regression: comparing with sheet 10 (the best look) gave 0.25 and the image was wrongly sent for a manual check
        shared = {9: 1.0}
        self.assertEqual(decide({9: 0.57, 10: 0.66}, [9], shared)[0], 'confirmed')

    def test_a_title_whose_parts_disagree_is_flagged(self):
        self.assertEqual(decide({9: 0.5, 10: 0.66}, [9], {9: 0.25}), ('check', 9))

    def test_no_rows_to_compare_needs_title_and_look_to_agree(self):
        self.assertEqual(decide({7: 0.7, 2: 0.5}, [7], {7: None}), ('confirmed', 7))
        self.assertEqual(decide({7: 0.5, 2: 0.7}, [7], {7: None}), ('check', 7))

    def test_a_sheet_nothing_resembles_has_no_match(self):
        self.assertEqual(decide({1: 0.6, 2: 0.58}, [], {}), ('no match', None))

    def test_the_title_sheet_with_the_most_shared_rows_wins(self):
        self.assertEqual(decide({16: 0.5, 18: 0.45, 2: 0.4}, [16, 18], {16: 0.5, 18: 1.0}), ('confirmed', 18))

if __name__ == '__main__': unittest.main()
