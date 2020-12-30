from __future__ import annotations
from typing import Callable, Iterable, Optional, Dict, Set, List
from evolver.helpers import _d
from evolver.config import CHAR_SETS, RXTYPE_SETTINGS


class RxType:
    """
    RxTypes model the different types of components that can be used to
    define regular expressions, the characteristics that pertain to them,
    and the hierarchical relationships between them.
    """

    def __init__(
        self,
        name: str,
        parent_rxtype: Optional[RxType] = None,
        is_modifiable: bool = True,
    ) -> None:
        self.name = name
        self.parent = parent_rxtype
        self.is_modifiable = is_modifiable

    def __repr__(self) -> str:
        parent_name = "-"
        if self.parent:
            parent_name = self.parent.name
        return f"T: {self.name} ({parent_name}, mod:{self.is_modifiable})"

    def is_type(self, rxtype: RxType, strict: bool = False) -> bool:
        """
        Determines equivalence to or inheritance from `re_type`.

        The `strict` parameter ignores inheritence and only matches explicitly equivalent types.
        """
        return self.name == rxtype.name or (
            not strict and self.parent is not None and self.parent.is_type(rxtype)
        )

    def is_type_name(self, type_name: str, strict: bool = False) -> bool:
        """
        Determines equivalence to or inheritance from the RxType referenced by `type_name`.

        The `strict` parameter ignores inheritence and only matches explicitly equivalent types.
        """
        if not strict and self.parent:
            return self.name == type_name or self.parent.is_type_name(type_name)
        return self.name == type_name


class RxTypeSet:
    def __init__(self, init_types: bool = True):
        self._types: Dict[str, RxType] = {}
        if init_types:
            self.init_types()

    def __getitem__(self, key: str) -> RxType:
        return self._types[key]

    def add(self, rxtype: RxType) -> None:
        self._types[rxtype.name] = rxtype

    def is_of(self, instance_name: str, of_name: str) -> bool:
        """
        Determines whether the RxType referenced by `instance_name` is
        equivalent to or inherited from the RxType referenced by `of_name`.
        """
        return self._types[instance_name].is_type_name(of_name)

    def is_one_of(self, instance_name: str, of_names: Iterable[str]) -> bool:
        """
        Determines whether the RxType referenced by `instance_name` is
        equivalent to or inherited from any of the RxTypes referenced by
        the names in `of_names`.
        """
        for name in of_names:
            if self.is_of(instance_name, name):
                return True
        return False

    def get_full_type_names(self, type_name: str) -> List[str]:
        """
        Returns `type_name` along with all the names of the RxTypes that it inherits from.
        """
        rxtype: RxType = self._types[type_name]
        type_list: List[str] = [type_name]
        while rxtype.parent:
            rxtype = rxtype.parent
            type_list.append(rxtype.name)
        return type_list

    def init_types(self) -> None:
        """
        Creates necessary RxTypes and adds them to the RxTypeCollector to activate them.
        """
        self._types.clear()
        for settings in RXTYPE_SETTINGS:
            self.add(
                RxType(
                    name=settings["name"],
                    parent_rxtype=self._types.get(settings.get("parent_name")),
                    is_modifiable=settings.get("is_modifiable", True),
                )
            )


class CharSets:
    """
    Contains the active characters that are usable for regexes to generate.
    """

    def __init__(self, rxtypes: RxTypeSet) -> None:
        self._char_sets: Dict[str, Set[str]] = {c: set() for c in CHAR_SETS.keys()}
        self._rxtypes: RxTypeSet = rxtypes

    def __getitem__(self, key: str) -> Set[str]:
        return self._char_sets[key]

    def __contains__(self, key: str) -> bool:
        return key in self._char_sets

    def rxtypes(self) -> RxTypeSet:
        return self._rxtypes

    def empty_sets(self) -> None:
        for key in self._char_sets.keys():
            self._char_sets[key].clear()

    def init_char_set(
        self,
        type_name: str,
        printable_subset: Set[str],
        char_set: str,
    ) -> None:
        """
        Activates a set of characters, including functions for their display and compilation.

        Parameters
        ----------
        `type_name`:
            The name of the character set being activated (as outlined in the `CHAR_SETS` constant in `config.py`)

        `printable_subset`:
            Specifies which subgroup of characters the character set `type_name` should be restricted to.
            Available subgroups are outlined in the `CHAR_SETS` constant in `config.py`,
            and the relationships between them are outlined in `RxType.init_types()`.

            e.g. if `type_name` is `alphanum` and `printable_subset` is `{'digit', 'alpha_upper'}`,
            lower case letters will be excluded.

        `char_set`:
            The custom characters to activate. Useful when different display or compilation functions are
            required for subsets of a specific character set.
        """
        type_names = set(self._rxtypes.get_full_type_names(type_name))

        # if type name is in printable subset, add characters from char set
        # into the relevant character containers.
        if type_names & printable_subset:
            for char in char_set:
                for name in type_names:
                    if name in self._char_sets:
                        self._char_sets[name].add(char)