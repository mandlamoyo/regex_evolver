import unittest

from evolver.evolver import RxEvolver, RxDataGen
from evolver.helpers import check_match


class TestRxEvolver(unittest.TestCase):
    pass


class TestRxDataGen(unittest.TestCase):
    def setUp(self):
        self.regex = r"[DXe-p][^c-n]\w\D{4,9}"
        self.rxspec = [
            [
                "set",
                [
                    "alpha(D)",
                    "alpha(X)",
                    ["range", ["alpha(e)", "alpha(p)"]],
                ],
            ],
            ["!set", [["range", ["alpha(c)", "alpha(n)"]]]],
            "word",
            ["!digit", ["count2", ["int(4)", "int(9)"]]],
        ]

    def test_gen_test_match(self):
        data_gen = RxDataGen()
        result = data_gen.gen_test_match(self.rxspec)
        self.assertRegex(result, self.regex)

    def test_gen_test_no_match(self):
        pass
