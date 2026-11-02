"""The scan for malformed links and thin sections (scripts/suspicious.py), and the link typos it was written for."""
import re, unittest
from helpers import ROOT
import suspicious as s

class MalformedLinks(unittest.TestCase):
    def found(self, md): return [what for _, what in s.malformed_links(md)]

    def test_wiki_piped_link_syntax_in_a_target_is_found(self):
        self.assertTrue(self.found('[x](Page.md#a%7CHybrid)'))

    def test_literal_brackets_around_a_link_are_found(self):
        self.assertTrue(self.found('Please refer to \\[[Instructions](Page.md)\\]'))

    def test_an_empty_link_and_a_stray_double_bracket_are_found(self):
        self.assertTrue(self.found('[](Page.md)'))
        self.assertTrue(self.found('Continue to the \\[\\[\\]\\]'))

    def test_a_link_left_on_the_old_wiki_is_found_but_a_shop_link_is_not(self):
        self.assertTrue(self.found('[x](http://wiki.e3d-online.com/wiki/Titan_Assembly)'))
        self.assertFalse(self.found('[x](http://e3d-online.com/index.php?route=product/product&product_id=356)'))

    def test_code_and_good_links_are_left_alone(self):
        self.assertFalse(self.found('[x](Page.md#a-b) and ![img](../docs/images/a.jpg)\n```\n[[code]]\n```'))

class Thin(unittest.TestCase):
    def test_a_section_that_only_points_elsewhere_is_thin(self):
        md = '## (21) A\n\nPlease refer to [the other page](P.md "P") for how to do this thing here.\n'
        self.assertEqual([t for _, t, _ in s.thin_sections(md)], ['(21) A'])

    def test_a_parent_heading_and_a_full_section_are_not(self):
        md = '## (1) Parent\n\n### (1.1) Child\n\n' + 'Fit the part and tighten the screws firmly. ' * 5 + '\n'
        self.assertEqual(s.thin_sections(md), [])

    def test_a_renumbered_heading_keeps_its_key(self):
        self.assertEqual(s.key('(21.1) Titan Extruder.'), s.key('Titan Extruder'))

class Source(unittest.TestCase):
    def test_the_page_name_loses_markdowns_escapes(self):
        self.assertEqual(s.source_page('Archived 2020 · source: wiki.e3d-online.com/wiki/Printer_main_assemblies:\\_Step_By_Step · [archive link](x)'),
                         'Printer_main_assemblies:_Step_By_Step')

class BuiltManual(unittest.TestCase):
    def test_no_link_to_a_section_carries_the_wiki_pipe_typo(self):
        md = open(f'{ROOT}/manual/Printer_main_assemblies_Step_By_Step_Assembly_Process.md').read()
        self.assertFalse(re.search(r'%7C|\\\[\[', md.split('## (22)')[0].split('## (21)')[1]))

if __name__ == '__main__':
    unittest.main()
