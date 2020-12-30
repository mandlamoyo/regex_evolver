import unittest

from evolver.types import RxType, RxTypeSet, CharSets
from evolver.config import CHAR_SETS, RXTYPE_SETTINGS, RXWRAPPER_SETTINGS


class TestRxType(unittest.TestCase):
    def test_is_type_true(self):
        t_liquid = RxType("liquid")
        t_water = RxType("water", t_liquid)
        t_lake = RxType("lake", t_water)
        self.assertTrue(t_water.is_type(t_liquid))
        self.assertTrue(t_lake.is_type(t_water))
        self.assertTrue(t_lake.is_type(t_liquid))

    def test_is_type_false_unrelated(self):
        t_solid = RxType("solid")
        t_liquid = RxType("liquid")
        t_water = RxType("water", t_liquid)
        t_lake = RxType("lake", t_water)

        self.assertFalse(t_liquid.is_type(t_solid))
        self.assertFalse(t_water.is_type(t_solid))
        self.assertFalse(t_lake.is_type(t_solid))

        self.assertFalse(t_solid.is_type(t_liquid))
        self.assertFalse(t_solid.is_type(t_water))
        self.assertFalse(t_solid.is_type(t_lake))

    def test_is_type_false_hierarchy(self):
        t_liquid = RxType("liquid")
        t_water = RxType("water", t_liquid)
        t_lake = RxType("lake", t_water)
        self.assertFalse(t_liquid.is_type(t_water))
        self.assertFalse(t_liquid.is_type(t_lake))
        self.assertFalse(t_water.is_type(t_lake))

    def test_is_type_strict_true(self):
        t_liquid = RxType("liquid")
        t_water = RxType("water", t_liquid)
        t_lake_actual = RxType("lake", t_water)
        t_lake_painting = RxType("lake")
        self.assertTrue(t_lake_actual.is_type(t_lake_painting, strict=True))
        self.assertTrue(t_lake_painting.is_type(t_lake_actual, strict=True))

    def test_is_type_strict_false(self):

        t_liquid = RxType("liquid")
        t_solid = RxType("solid")
        t_water = RxType("water", t_liquid)
        t_lake = RxType("lake", t_water)

        self.assertFalse(t_liquid.is_type(t_water, strict=True))
        self.assertFalse(t_water.is_type(t_liquid, strict=True))

        self.assertFalse(t_water.is_type(t_lake, strict=True))
        self.assertFalse(t_lake.is_type(t_water, strict=True))

        self.assertFalse(t_liquid.is_type(t_lake, strict=True))
        self.assertFalse(t_lake.is_type(t_liquid, strict=True))

        self.assertFalse(t_liquid.is_type(t_solid, strict=True))
        self.assertFalse(t_solid.is_type(t_liquid, strict=True))

        self.assertFalse(t_solid.is_type(t_lake, strict=True))
        self.assertFalse(t_lake.is_type(t_solid, strict=True))

    def test_is_type_name_true(self):
        t_liquid = RxType("liquid")
        t_water = RxType("water", t_liquid)
        t_lake = RxType("lake", t_water)
        self.assertTrue(t_water.is_type_name("liquid"))
        self.assertTrue(t_lake.is_type_name("water"))
        self.assertTrue(t_lake.is_type_name("liquid"))

    def test_is_type_name_false_unrelated(self):
        t_solid = RxType("solid")
        t_liquid = RxType("liquid")
        t_water = RxType("water", t_liquid)
        t_lake = RxType("lake", t_water)

        self.assertFalse(t_liquid.is_type_name("solid"))
        self.assertFalse(t_water.is_type_name("solid"))
        self.assertFalse(t_lake.is_type_name("solid"))

        self.assertFalse(t_solid.is_type_name("liquid"))
        self.assertFalse(t_solid.is_type_name("water"))
        self.assertFalse(t_solid.is_type_name("lake"))

    def test_is_type_name_false_hierarchy(self):
        t_liquid = RxType("liquid")
        t_water = RxType("water", t_liquid)
        t_lake = RxType("lake", t_water)
        self.assertFalse(t_liquid.is_type_name("water"))
        self.assertFalse(t_liquid.is_type_name("lake"))
        self.assertFalse(t_water.is_type_name("lake"))

    def test_is_type_name_strict_true(self):
        t_liquid = RxType("liquid")
        t_water = RxType("water", t_liquid)
        t_lake_actual = RxType("lake", t_water)
        t_lake_painting = RxType("lake")
        self.assertTrue(t_lake_actual.is_type_name("lake", strict=True))
        self.assertTrue(t_lake_painting.is_type_name("lake", strict=True))

    def test_is_type_name_strict_false(self):

        t_liquid = RxType("liquid")
        t_solid = RxType("solid")
        t_water = RxType("water", t_liquid)
        t_lake = RxType("lake", t_water)

        self.assertFalse(t_liquid.is_type_name("water", strict=True))
        self.assertFalse(t_water.is_type_name("liquid", strict=True))

        self.assertFalse(t_water.is_type_name("lake", strict=True))
        self.assertFalse(t_lake.is_type_name("water", strict=True))

        self.assertFalse(t_liquid.is_type_name("lake", strict=True))
        self.assertFalse(t_lake.is_type_name("liquid", strict=True))

        self.assertFalse(t_liquid.is_type_name("solid", strict=True))
        self.assertFalse(t_solid.is_type_name("liquid", strict=True))

        self.assertFalse(t_solid.is_type_name("lake", strict=True))
        self.assertFalse(t_lake.is_type_name("solid", strict=True))


class TestRxTypeSet(unittest.TestCase):
    def test_add(self):

        rxtype = RxType("liquid")
        type_set = RxTypeSet(init_types=False)
        type_set.add(rxtype)
        self.assertEqual(len(type_set._types), 1)
        self.assertEqual(type_set._types["liquid"], rxtype)

    def test_getitem(self):

        rxtype = RxType("liquid")
        type_set = RxTypeSet()
        type_set._types = {"liquid": rxtype}
        self.assertEqual(type_set["liquid"], rxtype)

    def test_is_of_true(self):

        t_liquid = RxType("liquid")
        t_water = RxType("water", t_liquid)
        t_lake = RxType("lake", t_water)
        type_set = RxTypeSet()
        type_set._types = {"water": t_water, "lake": t_lake}
        self.assertTrue(type_set.is_of("water", "liquid"))
        self.assertTrue(type_set.is_of("lake", "water"))

    def test_is_of_excluded(self):
        t_liquid = RxType("liquid")
        t_water = RxType("water", t_liquid)
        type_set = RxTypeSet()
        type_set._types = {"liquid": t_liquid}

        with self.assertRaises(KeyError):
            type_set.is_of("water", "liquid")

    def test_is_of_false_unrelated(self):
        t_liquid = RxType("liquid")
        t_solid = RxType("solid")
        type_set = RxTypeSet()
        type_set._types = {"liquid": t_liquid, "solid": t_solid}
        self.assertFalse(type_set.is_of("solid", "liquid"))
        self.assertFalse(type_set.is_of("liquid", "solid"))

    def test_is_of_false_hierarchy(self):
        t_liquid = RxType("liquid")
        t_water = RxType("water", t_liquid)
        t_lake = RxType("lake", t_water)
        type_set = RxTypeSet()
        type_set._types = {"liquid": t_liquid, "water": t_water}
        self.assertFalse(type_set.is_of("liquid", "water"))
        self.assertFalse(type_set.is_of("water", "lake"))

    def test_is_one_of_true(self):
        t_liquid = RxType("liquid")
        t_solid = RxType("solid")
        t_gas = RxType("gas")
        t_water = RxType("water", t_liquid)
        type_set = RxTypeSet()
        type_set._types = {"water": t_water}
        self.assertTrue(type_set.is_one_of("water", ["liquid", "solid", "gas"]))

    def test_is_one_of_false_unrelated(self):
        t_liquid = RxType("liquid")
        t_solid = RxType("solid")
        t_gas = RxType("gas")
        t_plasma = RxType("plasma")
        type_set = RxTypeSet()
        type_set._types = {"plasma": t_plasma}
        self.assertFalse(type_set.is_one_of("plasma", ["liquid", "solid", "gas"]))

    def test_is_one_of_false_hierarchy(self):
        t_liquid = RxType("liquid")
        t_water = RxType("water", t_liquid)
        t_lake = RxType("lake", t_water)
        type_set = RxTypeSet()
        type_set._types = {"liquid": t_liquid}
        self.assertFalse(type_set.is_one_of("liquid", ["water", "lake"]))

    def test_get_full_type_names(self):
        t_liquid = RxType("liquid")
        t_water = RxType("water", t_liquid)
        t_lake = RxType("lake", t_water)
        type_set = RxTypeSet()
        type_set._types = {"liquid": t_liquid, "water": t_water, "lake": t_lake}

        self.assertEqual(type_set.get_full_type_names("liquid"), ["liquid"])
        self.assertEqual(type_set.get_full_type_names("water"), ["water", "liquid"])
        self.assertEqual(
            type_set.get_full_type_names("lake"), ["lake", "water", "liquid"]
        )

    def test_init_types(self):

        type_set = RxTypeSet(init_types=False)
        type_set.init_types()

        for settings in RXTYPE_SETTINGS:
            self.assertIn(settings["name"], type_set._types)
            rxtype = type_set._types[settings["name"]]
            self.assertIsInstance(rxtype, RxType)
            self.assertEqual(rxtype.name, settings["name"])


class TestCharSet(unittest.TestCase):
    def test_init(self):
        type_set = RxTypeSet()
        char_sets = CharSets(type_set)

        self.assertEqual(len(char_sets._char_sets), len(CHAR_SETS.keys()))

        for key in CHAR_SETS.keys():
            self.assertIn(key, char_sets._char_sets)
            self.assertIsInstance(char_sets._char_sets[key], set)
            self.assertEqual(len(char_sets._char_sets[key]), 0)

        self.assertEqual(type_set, char_sets._rxtypes)

    def test_getitem(self):
        type_set = RxTypeSet()
        char_sets = CharSets(type_set)
        for key in CHAR_SETS.keys():
            self.assertIsInstance(char_sets[key], set)

    def test_contains_true(self):
        type_set = RxTypeSet()
        char_sets = CharSets(type_set)
        for key in CHAR_SETS.keys():
            self.assertTrue(key in char_sets)
            self.assertIn(key, char_sets)

    def test_contains_false(self):
        type_set = RxTypeSet()
        char_sets = CharSets(type_set)
        self.assertFalse("INVALID_KEY" in char_sets)
        self.assertNotIn("INVALID_KEY", char_sets)

    def test_rxtypes(self):
        type_set = RxTypeSet()
        char_sets = CharSets(type_set)
        result = char_sets.rxtypes()
        self.assertEqual(result, type_set)

    def test_empty_sets(self):
        type_set = RxTypeSet()
        char_sets = CharSets(type_set)

        for key in char_sets._char_sets.keys():
            char_sets._char_sets[key].add("a")
            char_sets._char_sets[key].add("b")
            char_sets._char_sets[key].add("c")
            self.assertEqual(len(char_sets._char_sets[key]), 3)

        char_sets.empty_sets()

        self.assertEqual(len(char_sets._char_sets), len(CHAR_SETS.keys()))
        for key in char_sets._char_sets.keys():
            self.assertEqual(len(char_sets._char_sets[key]), 0)

    def test_init_char_set_full_subset(self):
        type_set = RxTypeSet()
        type_set.init_types()
        char_sets = CharSets(type_set)

        type_name = "alphanum"
        full_type_names = set(type_set.get_full_type_names(type_name))
        printable_subset = set(CHAR_SETS.keys())
        char_set = CHAR_SETS[type_name]

        char_sets.init_char_set(type_name, printable_subset, char_set)

        # all related type names should contain all characters in alphanum char set
        for char in char_set:
            for name in full_type_names:

                # only evaluate those type names that represent actual printable character sets
                if name in char_sets._char_sets:
                    self.assertIn(char, char_sets._char_sets[name])

    def test_init_char_set_partial_subset(self):
        type_set = RxTypeSet()
        type_set.init_types()
        char_sets = CharSets(type_set)
        type_names = ["digit", "alpha_lower", "alpha_upper"]
        printable_subset = set(["digit", "alpha_upper"])

        # Initialise character sets
        for type_name in type_names:
            char_set = CHAR_SETS[type_name]
            char_sets.init_char_set(type_name, printable_subset, char_set)

        # Search through all specified type names
        for type_name in type_names:

            # Confirm that type name is present in charsets
            self.assertIn(type_name, char_sets._char_sets)

            # Get the full list of character set type names that the current type name inherits from (inluding itself)
            full_type_names = list(
                filter(
                    lambda name: name in char_sets._char_sets,
                    type_set.get_full_type_names(type_name),
                )
            )

            # For all characters in the character set corresponding to the current type name
            for char in CHAR_SETS[type_name]:

                # For all the character set types it inherits from (including itself)
                for name in full_type_names:

                    # If the current type name is in the printable subset, it should be activated within the charset
                    if type_name in printable_subset:
                        self.assertIn(char, char_sets._char_sets[name])

                    # If the current type name is not in the printable subset, it should be excluded from the charset
                    else:
                        self.assertNotIn(char, char_sets._char_sets[name])

    def test_init_char_set_empty_subset(self):
        type_set = RxTypeSet()
        type_set.init_types()
        char_sets = CharSets(type_set)

        type_name = "alphanum"
        full_type_names = set(type_set.get_full_type_names(type_name))
        printable_subset = set()
        char_set = CHAR_SETS[type_name]

        char_sets.init_char_set(type_name, printable_subset, char_set)

        # no characters should be activated from type name character set
        for char in char_set:
            for name in full_type_names:
                if name in char_sets._char_sets:
                    self.assertNotIn(char, char_sets._char_sets[name])

    def test_init_char_set(self):
        type_set = RxTypeSet()
        type_set.init_types()
        char_sets = CharSets(type_set)
        printable_subset = set(CHAR_SETS.keys())

        for settings in RXWRAPPER_SETTINGS:
            if settings.get("is_char_set"):
                type_name = settings.get("rxtype_name", settings["name"])
                char_set = settings.get("char_set") or CHAR_SETS[type_name]
                char_sets.init_char_set(type_name, printable_subset, char_set)

        for type_name in CHAR_SETS.keys():
            self.assertIn(type_name, char_sets._char_sets)

            for char in CHAR_SETS[type_name]:
                self.assertIn(char, char_sets._char_sets[type_name])
