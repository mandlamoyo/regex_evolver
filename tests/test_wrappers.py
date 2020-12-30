from __future__ import annotations
from typing import Optional, Callable, List
import unittest
import random

from evolver.config import CHAR_SETS, WHITESPACE_CHARS
from evolver.helpers import _d
from evolver.types import RxType, RxTypeSet, CharSets
from evolver.wrappers import RxWrapper, RxWrapperSet
from evolver.wrapper_functions import *


class MockNode:
    def __init__(
        self,
        display_function: Optional[Callable] = None,
        compile_function: Optional[Callable] = None,
        name: Optional[str] = None,
        rxtype: Optional[RxType] = None,
        children: List[MockNode] = None,
        char_sets: Optional[CharSets] = None,
    ):
        self.name = name
        self.rxtype = rxtype
        self.char_sets = char_sets
        self.children = children or []
        self.display_function = display_function
        self.compile_function = compile_function

    def display(self):
        return self.display_function(self)

    def compile(self):
        return self.compile_function(self)


class TestRxWrapper(unittest.TestCase):
    def test_init_not_null_defaults(self):
        rxtype = RxType("water")
        river_wrapper = RxWrapper("River", lambda node: "River", rxtype)

        self.assertEqual(river_wrapper.child_count, 0)
        self.assertTrue(river_wrapper.is_modifiable)
        self.assertFalse(river_wrapper.strip_child_mods)
        self.assertFalse(river_wrapper.uniform_child_types)
        self.assertEqual(river_wrapper.display_function, river_wrapper.compile_function)

        sea_wrapper = RxWrapper(
            "Sea",
            lambda node: "Sea",
            rxtype,
            child_types=None,
            child_count=None,
            is_modifiable=None,
            compile_function=None,
            strip_child_mods=None,
            uniform_child_types=None,
        )

        self.assertEqual(sea_wrapper.child_count, 0)
        self.assertTrue(sea_wrapper.is_modifiable)
        self.assertFalse(sea_wrapper.strip_child_mods)
        self.assertFalse(sea_wrapper.uniform_child_types)
        self.assertEqual(sea_wrapper.display_function, sea_wrapper.compile_function)


class TestRxWrapperSet(unittest.TestCase):
    def setUp(self):
        self.water_type = RxType("water")
        self.fire_type = RxType("fire")
        self.rxtypes = RxTypeSet()
        self.char_sets = CharSets(self.rxtypes)
        self.river_wrapper = RxWrapper("river", lambda node: "river", self.water_type)
        self.candle_wrapper = RxWrapper("candle", lambda node: "candle", self.fire_type)

    def test_getitem(self):
        wrappers = RxWrapperSet(self.char_sets, init_wrappers=False)
        wrappers._wrappers[self.river_wrapper.name] = self.river_wrapper
        self.assertEqual(wrappers[self.river_wrapper.name], self.river_wrapper)

    def test_all(self):
        wrappers = RxWrapperSet(self.char_sets, init_wrappers=False)
        wrappers._wrappers[self.river_wrapper.name] = self.river_wrapper
        wrappers._wrappers[self.candle_wrapper.name] = self.candle_wrapper
        result = wrappers.all()

        self.assertEqual(len(result), 2)
        self.assertSetEqual(set(result), set([self.river_wrapper, self.candle_wrapper]))

    def test_add(self):
        wrappers = RxWrapperSet(self.char_sets, init_wrappers=False)
        wrappers.add(self.river_wrapper)
        self.assertEqual(wrappers[self.river_wrapper.name], self.river_wrapper)

    def test_wrapper_is_type(self):
        wrappers = RxWrapperSet(self.char_sets, init_wrappers=False)
        wrappers._wrappers[self.river_wrapper.name] = self.river_wrapper
        result = wrappers.wrapper_is_type("river", "water")
        self.assertTrue(result)

    def test_get_wrapper_func_name(self):
        data = {
            "0+": "zero_plus",
            "0/1": "zero_one",
            "1+": "one_plus",
            "!set": "nset",
        }

        wrappers = RxWrapperSet(self.char_sets, init_wrappers=False)
        for name in data.keys():
            result = wrappers.get_wrapper_func_name(name)
            self.assertEqual(result, data[name])

    def test_create_wrapper_full(self):
        data = {
            "name": "test",
            "rxtype_name": "re",
            "child_types": ["alpha_lower", "digit"],
            "child_count": 3,
            "is_modifiable": False,
            "strip_child_mods": True,
            "uniform_child_types": True,
            "display_function_name": "or",
            "compile_function_name": "or",
        }
        wrappers = RxWrapperSet(self.char_sets, init_wrappers=False)
        wrapper = wrappers.create_wrapper(**data)
        mock_node = MockNode(
            children=[
                MockNode(_d("f"), _d("f")),
                MockNode(_d("j"), _d("j")),
            ]
        )

        self.assertEqual(wrapper.name, data["name"])
        self.assertEqual(wrapper.rxtype.name, data["rxtype_name"])
        self.assertEqual(wrapper.child_types, data["child_types"])
        self.assertEqual(wrapper.child_count, data["child_count"])
        self.assertFalse(wrapper.is_modifiable)
        self.assertTrue(wrapper.strip_child_mods)
        self.assertTrue(wrapper.uniform_child_types)
        self.assertEqual(wrapper.display_function(mock_node), d_or(mock_node))
        self.assertIn(wrapper.compile_function(mock_node), ["f", "j"])

    def test_create_wrapper_defaults_invalid_function(self):
        wrappers = RxWrapperSet(self.char_sets, init_wrappers=False)
        with self.assertRaises(TypeError):
            wrappers.create_wrapper("test", "re")

    def test_create_wrapper_defaults_invalid_char_set(self):
        wrappers = RxWrapperSet(self.char_sets, init_wrappers=False)
        with self.assertRaises(TypeError):
            wrappers.create_wrapper("test", "re", display_value="X", is_char_set=True)

    def test_create_wrapper_defaults_func_name(self):
        wrappers = RxWrapperSet(self.char_sets, init_wrappers=False)
        set_wrapper = wrappers.create_wrapper("set", "re")
        mock_node = MockNode(
            children=[
                MockNode(_d("a"), _d("a"), rxtype=RxType("test")),
            ],
        )

        self.assertEqual(set_wrapper.display_function(mock_node), d_set(mock_node))
        self.assertEqual(set_wrapper.compile_function(mock_node), c_set(mock_node))

    def test_create_wrapper_defaults(self):
        wrappers = RxWrapperSet(self.char_sets, init_wrappers=False)
        wrapper = wrappers.create_wrapper("test", "re", display_value="X")

        self.assertEqual(wrapper.child_types, None)
        self.assertEqual(wrapper.child_count, 0)
        self.assertTrue(wrapper.is_modifiable)
        self.assertFalse(wrapper.strip_child_mods)
        self.assertFalse(wrapper.uniform_child_types)

    def test_create_wrapper_display_function_from_display_value_only(self):
        wrappers = RxWrapperSet(self.char_sets, init_wrappers=False)
        data = {
            "name": "test",
            "display_value": "X",
            "rxtype_name": "re",
        }

        wrapper = wrappers.create_wrapper(**data)
        self.assertEqual(wrapper.display_function(None), data["display_value"])

    def test_create_wrapper_compile_function_from_display_value_only(self):
        wrappers = RxWrapperSet(self.char_sets, init_wrappers=False)
        data = {
            "name": "test",
            "display_value": "X",
            "rxtype_name": "re",
        }

        wrapper = wrappers.create_wrapper(**data)
        self.assertEqual(wrapper.compile_function(None), data["display_value"])

    def test_create_wrapper_explicit_compile_function_name(self):
        wrappers = RxWrapperSet(self.char_sets, init_wrappers=False)
        data = {
            "name": "empty!term",
            "display_value": r"\B",
            "rxtype_name": "cset*",
            "compile_function_name": "empty",
        }

        wrapper = wrappers.create_wrapper(**data)
        c_func = rxwrapper_functions["compile"][data["compile_function_name"]]
        self.assertEqual(wrapper.compile_function(None), c_func(None))

    def test_create_wrapper_format_char_set_display_with_value(self):
        wrappers = RxWrapperSet(self.char_sets, init_wrappers=False)
        data = {
            "name": "digit",
            "rxtype_name": "digit",
            "is_char_set": True,
            "char_value": "5",
        }
        wrapper = wrappers.create_wrapper(**data)
        self.assertEqual(wrapper.display_function(None), "5")

    def test_create_wrapper_format_char_set_name_with_value(self):
        wrappers = RxWrapperSet(self.char_sets, init_wrappers=False)
        data = {
            "name": "digit",
            "rxtype_name": "digit",
            "is_char_set": True,
            "char_value": "5",
        }
        wrapper = wrappers.create_wrapper(**data)
        self.assertEqual(wrapper.name, "digit(5)")

    def test_init_wrappers(self):
        wrappers = RxWrapperSet(self.char_sets, init_wrappers=False)
        wrappers.init_wrappers()
        # print(wrappers._char_sets._char_sets)
        # print(wrappers._wrappers)
        self.assertTrue(False)

    def test_init_wrappers_printable_subset(self):
        wrappers = RxWrapperSet(self.char_sets, init_wrappers=False)
        wrappers.init_wrappers(printable_subset=["alpha_upper", "digit"])
        # print(wrappers._char_sets._char_sets)
        # print(wrappers._wrappers)
        self.assertTrue(False)


class TestRxWrapperFunctions(unittest.TestCase):
    def setUp(self):
        self.rxtypes = RxTypeSet()
        self.char_sets = CharSets(self.rxtypes)
        self.rxwrappers = RxWrapperSet(self.char_sets)

    def test_set_choice(self):
        value = 5
        s = set([value])
        result = set_choice(s)
        self.assertEqual(result, value)

    def test_invert_set(self):
        mock_node = MockNode(char_sets=self.char_sets)
        for char_set_name in CHAR_SETS.keys():
            char_set = list(self.char_sets[char_set_name])  #  CHAR_SETS[char_set_name]
            subset = set([random.choice(char_set) for i in range(5)])
            result = invert_set(mock_node, subset, char_set_name)

            self.assertEqual(len(result) + len(subset), len(char_set))
            self.assertSetEqual(result | subset, set(char_set))

    def test_expand_set_range(self):
        mock_node = MockNode(
            name="range",
            char_sets=self.char_sets,
            children=[
                MockNode(_d("f"), _d("f")),
                MockNode(_d("j"), _d("j")),
            ],
        )

        result = expand_set(mock_node)
        self.assertSetEqual(result, set(["f", "g", "h", "i", "j"]))

    def test_expand_set_digit(self):
        mock_node = MockNode(
            name="digit", rxtype=RxType("cset"), char_sets=self.char_sets
        )
        result = expand_set(mock_node)
        self.assertSetEqual(result, set(CHAR_SETS["digit"]))

    def test_expand_set_whitespace(self):
        mock_node = MockNode(
            name="whitespace", rxtype=RxType("cset"), char_sets=self.char_sets
        )
        result = expand_set(mock_node)
        self.assertSetEqual(result, set(WHITESPACE_CHARS))
