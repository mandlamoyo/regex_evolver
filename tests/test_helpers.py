import unittest

from evolver.helpers import (
    _d,
    first_nested,
    select_index,
    check_match,
    callable_get,
    safe_sample,
)


class TestHelpers(unittest.TestCase):
    def test__d(self):
        data = "a"
        result = _d(data)(None)
        self.assertEqual(result, data)

    def test__d_meta(self):
        data = r"\d"
        result = _d(data)(None)
        self.assertEqual(result, data)

    def test_nested_first_value(self):
        data = "first"
        result = first_nested(data)
        self.assertEqual(result, "first")

    def test_nested_first_flat_list(self):
        data = ["first", "second", "third"]
        result = first_nested(data)
        self.assertEqual(result, "first")

    def test_nested_first_nested_list(self):
        data = [[["first", "second"], [["third"], "fourth", "fifth"], "sixth"]]
        result = first_nested(data)
        self.assertEqual(result, "first")

    # def test_select_index(self):
    #     self.assertTrue(False)

    def test_check_match_true(self):
        regex = r"[0-9][0-9][a-z][A-Z] \d\w[a-z]*_[1-3]+[A-Z]{3}"
        data = "36dI 4Nlafiew_132FJE"
        result = check_match(regex, data)
        self.assertTrue(result)

    def test_check_match_false(self):
        regex = r"first"
        data = "second"
        result = check_match(regex, data)
        self.assertFalse(result)

    def test_check_match_partial_false(self):
        regex = r"foo"
        data = "afoot"
        result = check_match(regex, data)
        self.assertFalse(result)

    def test_callable_get_non_callable(self):
        data = 5
        result = callable_get(data)
        self.assertEqual(result, 5)

    def test_callable_get_callable(self):
        data = lambda: 5
        result = callable_get(data)
        self.assertEqual(result, 5)

    def test_callable_get_callable_args(self):
        data = lambda x: x * x
        result = callable_get(data, 5)
        self.assertEqual(result, 25)

    def test_safe_sample_safe(self):
        data = [1, 2, 3, 4, 5]
        result = safe_sample(data, 3)
        self.assertEqual(len(result), 3)

    def test_safe_sample_unsafe(self):
        data = [1, 2, 3, 4, 5]
        result = safe_sample(data, 10)
        self.assertEqual(len(result), len(data))