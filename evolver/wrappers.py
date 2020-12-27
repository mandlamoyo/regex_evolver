from __future__ import annotations
from typing import Callable, Optional, Iterable, Dict, List

from evolver.types import RxType, RxTypeSet, CharSets
from evolver.wrapper_functions import *
from evolver.helpers import _d
from evolver.config import (
    RAND,
    MAX_CHILDREN,
    CHAR_SETS,
    META_CHARS,
    NON_META_SYMBOL_CHARS,
    RXWRAPPER_SETTINGS,
    RXWRAPPER_SYMBOL_KEY,
)


class RxWrapper:
    """
    The templates that define the various components of which regexes consist.
    """

    def __init__(
        self,
        name: str,
        display_function: Callable[..., str],
        rxtype: RxType,
        child_types: Optional[Sequence[str]] = None,
        child_count: int = 0,
        is_modifiable: Optional[bool] = True,
        compile_function: Optional[Callable[..., str]] = None,
        strip_child_mods: bool = False,
        uniform_child_types: bool = False,
    ) -> None:
        """
        Instantiates a wrapper that defines a particular regex component.

        Parameters
        ----------
        `name`: The name of the regex component.
        `display_function`: The function used to display the given regex component wrapper.
        `rxtype_name`: The name of the regex component wrapper's type (RxType).
        `child_types`: The types that are allowable for the component's children.
        `child_count`: The number of children the regex component requires.
        `is_modifiable`: Whether the component can have frequency modifiers (`?`, `+`, `*`, `{}`) attached to it.
        `compile_function`: The function used when the regex component is compiled into a concrete instance.
        `strip_child_mods`: Whether the component cannot have children with modifiers (eg range `[value]-[value]`)
        `uniform_child_types`: Whether the component's children must all be of the same type (eg modifier ranged count `{X, Y}`)
        """
        self.name = name
        self.display_function = display_function
        self.compile_function = compile_function or display_function
        self.child_count = child_count
        self.child_types = child_types
        self.rxtype = rxtype
        self.is_modifiable = self.rxtype.is_modifiable and is_modifiable
        self.strip_child_mods = strip_child_mods
        self.uniform_child_types = uniform_child_types

    def __repr__(self) -> str:
        return f"RxWrapper: {self.name}(children:{self.child_count}, mod:{self.is_modifiable})"

    def get_child_count(self) -> int:
        if self.child_count == RAND:
            return randint(1, MAX_CHILDREN)
        return self.child_count


class RxWrapperSet:
    def __init__(
        self, char_sets: CharSets, printable_subset: Optional[Iterable[str]] = None
    ) -> None:
        self._wrappers: Dict[str, RxWrapper] = {}
        self._char_sets: CharSets = char_sets
        self._rxtypes: RxTypeSet = char_sets.rxtypes()
        self.init_wrappers(printable_subset)

    def __getitem__(self, key: str) -> RxWrapper:
        return self._wrappers[key]

    def all(self) -> Tuple[RxWrapper]:
        return tuple(self._wrappers.values())

    def add(self, rxwrapper: RxWrapper) -> None:
        self._wrappers[rxwrapper.name] = rxwrapper

    def wrapper_is_type(self, rxwrapper_name: str, rxtype_name: str) -> bool:
        wrapper: RxWrapper = self._wrappers[rxwrapper_name]
        return wrapper.rxtype.is_type_name(rxtype_name)

    def create_wrapper(
        self,
        name: str,
        rxtype_name: str,
        child_types: Optional[Sequence[str]] = None,
        child_count: Optional[int] = None,
        is_modifiable: Optional[bool] = None,
        strip_child_mods: Optional[bool] = None,
        uniform_child_types: Optional[bool] = None,
        compile_function_name: Optional[str] = None,
        display_function_name: Optional[str] = None,
        is_char_set: bool = False,
        display_value: Optional[str] = None,
        char_value: Optional[str] = None,
        char_set: Optional[Iterable[str]] = None,
    ) -> RxWrapper:
        func_name = "".join([RXWRAPPER_SYMBOL_KEY.get(c, c) for c in name])

        display_value = display_value or char_value
        if display_value:
            display_value = display_value.format(char_value)

        rxtype = self._rxtypes[rxtype_name]

        display_function = rxwrapper_functions["display"].get(
            display_function_name or func_name, _d(display_value)
        )
        compile_function = rxwrapper_functions["compile"].get(
            compile_function_name or func_name, _d(display_value)
        )

        if is_char_set:
            name = f"{name}({char_value})"

        return RxWrapper(
            name,
            display_function,
            rxtype,
            child_types,
            child_count,
            is_modifiable,
            compile_function,
            strip_child_mods,
            uniform_child_types,
        )

    def init_wrappers(self, printable_subset: Optional[Iterable[str]] = None) -> None:
        if not printable_subset:
            printable_subset = CHAR_SETS.keys()
        printable_subset = set(printable_subset)

        # clear containers
        self._wrappers.clear()
        self._char_sets.empty_sets()

        for settings in RXWRAPPER_SETTINGS:
            if settings["is_char_set"]:
                char_set = settings.get("char_set", CHAR_SETS[settings["name"]])
                self._char_sets.init_char_set(
                    settings["name"], printable_subset, char_set
                )
                for char in char_set:
                    settings["char_value"] = char
                    self.add(self.create_wrapper(**settings))

            else:
                self.add(self.create_wrapper(**settings))
