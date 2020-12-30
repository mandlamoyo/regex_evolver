import unittest

from evolver.parser import parse_regex


class TestRxParser(unittest.TestCase):
    def setUp(self):
        self.regex = r"nv\d:[a-z4-7Z][A-E]*,\[(020|4+)..?\]\d\W.+[Ad0-9_]_x{3,5}?"
        self.or_bounded_regex = r"af(e|z(m|b)z|g)*"
        self.or_regex = r"afe|z(m|b)z*|g"

    def test_parse_regex(self):
        result = parse_regex(self.regex)
        for r in result:
            print(r)
        print()

        result = parse_regex(self.or_regex)
        for r in result:
            print(r)
        self.assertTrue(False)
