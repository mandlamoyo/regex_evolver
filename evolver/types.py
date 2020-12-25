from __future__ import annotations
from typing import Callable, Iterable, Optional, Dict, Set, List
from evolver.helpers import _d, Singleton
from evolver.config import CHAR_SETS


class RxType:
    """
    RxTypes model the different types of components that can be used to
    define regular expressions, the characteristics that pertain to them,
    and the hierarchical relationships between them.
    """

    _types = {}

    @staticmethod
    def get_type(name: str) -> RxType:
        return RxType._types[name]

    @staticmethod
    def add_type(re_type: RxType) -> None:
        RxType._types[re_type.name] = re_type

    @staticmethod
    def add_types(re_types: Iterable[RxType]) -> None:
        for re_type in re_types:
            RxType.add_type(re_type)

    @staticmethod
    def init_types() -> None:
        """
        Creates necessary RxTypes and adds them to the RxTypeCollector to activate them.
        """
        RxType._types.clear()
        RxType.add_type(RxType("re"))
        RxType.add_type(RxType("mod"))
        RxType.add_type(RxType("integer", is_modifiable=False))
        RxType.add_type(RxType("range", is_modifiable=False))
        RxType.add_type(RxType("cset", RxType.get_type("re")))
        RxType.add_type(RxType("cset*", RxType.get_type("re"), is_modifiable=False))
        RxType.add_type(RxType("printable", RxType.get_type("re")))
        RxType.add_type(RxType("alphanum", RxType.get_type("printable")))
        RxType.add_type(RxType("digit", RxType.get_type("alphanum")))
        RxType.add_type(RxType("alpha", RxType.get_type("alphanum")))
        RxType.add_type(RxType("alpha_upper", RxType.get_type("alpha")))
        RxType.add_type(RxType("alpha_lower", RxType.get_type("alpha")))
        RxType.add_type(RxType("mmod", RxType.get_type("mod"), is_modifiable=False))

    @staticmethod
    def is_of(instance_name: str, of_name: str) -> bool:
        """
        Determines whether the RxType referenced by `instance_name` is
        equivalent to or inherited from the RxType referenced by `of_name`.
        """
        return RxType.get_type(instance_name).is_type_name(of_name)

    @staticmethod
    def is_one_of(instance_name: str, of_names: Iterable[str]) -> bool:
        """
        Determines whether the RxType referenced by `instance_name` is
        equivalent to or inherited from any of the RxTypes referenced by
        the names in `of_names`.
        """
        for name in of_names:
            if RxType.is_of(instance_name, name):
                return True
        return False

    @staticmethod
    def get_full_type_names(type_name: str) -> List[str]:
        """
        Returns `type_name` along with all the names of the RxTypes that it inherits from.
        """
        rxtype = RxType.get_type(type_name)
        type_list = [type_name]
        while rxtype.parent:
            rxtype = rxtype.parent
            type_list.append(rxtype.name)
        return type_list

    def __init__(
        self,
        name: str,
        parent_rxtype: Optional[RxType] = None,
        is_modifiable: Optional[bool] = True,
    ) -> None:
        self.name = name
        self.parent = parent_rxtype
        self.is_modifiable = is_modifiable

    def __repr__(self) -> str:
        parent_name = "-"
        if self.parent:
            parent_name = self.parent.name
        return f"T: {self.name} ({parent_name}, mod:{self.is_modifiable})"

    def is_type(self, re_type: RxType, strict: Optional[bool] = False) -> bool:
        """
        Determines equivalence to or inheritance from `re_type`.

        The `strict` parameter ignores inheritence and only matches explicitly equivalent types.
        """
        return self.name == re_type.name or (
            not strict and self.parent and self.parent.is_type(re_type)
        )

    def is_type_name(self, type_name: str, strict: Optional[bool] = False) -> bool:
        """
        Determines equivalence to or inheritance from the RxType referenced by `type_name`.

        The `strict` parameter ignores inheritence and only matches explicitly equivalent types.
        """
        if not strict and self.parent:
            return self.name == type_name or self.parent.is_type_name(type_name)
        return self.name == type_name


@Singleton
class CharSets:
    """
    Contains the active characters that are usable for regexes to generate.
    """

    @staticmethod
    def instance():
        raise AttributeError(
            "FOR RESOLVING PYLINT DECORATOR ISSUE, SHOULD NOT BE REACHED"
        )

    def __init__(self) -> None:
        self._char_sets: Dict[str, Set[str]] = {c: set() for c in CHAR_SETS.keys()}

    def __getitem__(self, key: str) -> Set[str]:
        return self._char_sets[key]

    def __contains__(self, key: str) -> bool:
        return key in self._char_sets

    def empty_sets(self) -> None:
        for key in self._char_sets.keys():
            self._char_sets[key].clear()

    def init_char_set(
        self,
        type_name: str,
        wrapper_class: "RxWrapper",
        printable_subset: Optional[Set[str]] = None,
        label: Optional[str] = None,
        display_func_generator: Optional[Callable] = _d,
        compile_function: Optional[Callable] = None,
        char_set: Optional[Iterable[str]] = None,
    ) -> None:
        """
        Activates a set of characters, including functions for their display and compilation.

        Parameters
        ----------
        `type_name`:
            The name of the character set to activate (as outlined in the `CHAR_SETS` constant in `config.py`)

        `wrapper_class`:
            The RxWrapper class.

        `printable_subset`:
            Specifies which subgroup of characters the character set `type_name` should be restricted to.
            Available subgroups are outlined in the `CHAR_SETS` constant in `config.py`,
            and the relationships between them are outlined in `RxType.init_types()`.

            e.g. if `type_name` is `alphanum` and `printable_subset` is `{'num', 'alpha_upper'}`,
            lower case letters will be excluded.

        `label`:
            The label this character set should be referenced as.

        `display_function_generator`:
            Used to produce the display function for each character.
            The default `_d` function produces a function that returns the given character.
            If characters require pre-rendering, this function can be replaced.

        `compile_function`:
            The function used to generate a given character in the set when the regex node in which
            it is contained is compiled. If none is provided, the display function will be used.

        `char_set`:
            The custom characters to activate. Useful when different display or compilation functions are
            required for subsets of a specific character set.
        """
        label = label or type_name
        char_set = char_set or CHAR_SETS[type_name]
        type_names = set(RxType.get_full_type_names(type_name))

        if type_names & printable_subset:
            for s in char_set:
                wrapper_class.add_wrapper(
                    wrapper_class(
                        f"{label}({s})",
                        display_func_generator(s),
                        type_name,
                        compile_function=compile_function,
                    )
                )

                for name in type_names:
                    if name in self._char_sets:
                        self._char_sets[name].add(s)