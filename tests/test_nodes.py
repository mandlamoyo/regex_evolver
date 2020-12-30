import unittest

from evolver.nodes import RxNode, RxNodeFactory


class TestRxNode(unittest.TestCase):
    def test_display(self):
        pass

    def test_display_with_children(self):
        pass

    def test_display_with_children_strip_child_mods(self):
        pass

    def test_display_with_modifier(self):
        pass

    def test_display_with_modifier_strip_mod(self):
        pass

    def test_display_with_modifier_and_children(self):
        pass

    def test_compile(self):
        pass

    def test_compile_with_children(self):
        pass

    def test_compile_with_children_strip_child_mods(self):
        pass

    def test_compile_with_modifier(self):
        pass

    def test_compile_with_modifier_strip_mod(self):
        pass

    def test_display_with_modifier_and_children(self):
        pass

    def test_mutate(self):
        pass

    def test_mutate_with_children(self):
        pass


class TestRxNodeFactory(unittest.TestCase):
    def setUp(self):
        self.rxspecs = [  # r"[DXe-p][^c-n]\w\D{4,9}"
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

        self.node_specs = [
            {
                "rw_name": "set",
                "children": [
                    {"rw_name": "alpha(D)"},
                    {"rw_name": "alpha(X)"},
                    {
                        "rw_name": "range",
                        "children": [
                            {"rw_name": "alpha(e)"},
                            {"rw_name": "alpha(p)"},
                        ],
                    },
                ],
            },
            {
                "rw_name": "!set",
                "children": [
                    {
                        "rw_name": "range",
                        "children": [
                            {"rw_name": "alpha(c)"},
                            {"rw_name": "alpha(n)"},
                        ],
                    },
                ],
            },
            {"rw_name": "word"},
            {
                "rw_name": "!digit",
                "modifier": {
                    "rw_name": "count2",
                    "children": [
                        {"rw_name": "int(4)"},
                        {"rw_name": "int(9)"},
                    ],
                },
            },
        ]

    def test_parse_rxspec(self):

        """
        children format: [{'rw_name': regex_wrapper_name, 'children': [<children>]})]
        modifier format: {'rw_name': <modifier_name>, 'children': <children>, 'modifier': <modifier>}
        """

        node_factory = RxNodeFactory()
        results = [node_factory.parse_rxspec(rxspec) for rxspec in self.rxspecs]
        self.assertEqual(len(results), len(self.node_specs))
        for i in range(len(results)):
            self.assertEqual(results[i], self.node_specs[i])

    def test_make_node(self):
        pass

    def test_make_random_node(self):
        pass

    def test_make_random_node_omit_types(self):
        pass

    def test_make_random_node_omit_wrappers(self):
        pass


class TestRxNodeSet(unittest.TestCase):
    def test_display(self):
        pass

    def test_compile(self):
        pass

    def test_mutate(self):
        pass

    def test_crossover(self):
        pass


class TestRxNodeSetFactory(unittest.TestCase):
    def test_make_node_set(self):
        pass

    def test_random_node_set(self):
        pass

    def test_random_node_set_omit_types(self):
        pass

    def test_random_node_set_omit_wrappers(self):
        pass
