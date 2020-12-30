from __future__ import annotations
from typing import Callable, Optional, Iterable, Dict, List

from evolver.types import RxType, RxTypeSet, CharSets
from evolver.wrapper_functions import *
from evolver.helpers import _d
from evolver.config import (
    RAND,
    MAX_CHILDREN,
    CHAR_SETS,
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
        child_count: Optional[int] = None,
        is_modifiable: Optional[bool] = None,
        compile_function: Optional[Callable[..., str]] = None,
        strip_child_mods: Optional[bool] = None,
        uniform_child_types: Optional[bool] = None,
    ) -> None:
        """
        Instantiates a wrapper that defines a particular regex component.

        Parameters
        ----------
        `name`: The name of the regex component.
        `display_function`: The function used to display the given regex component wrapper.
        `rxtype`: The regex component wrapper's type.
        `child_types`: The types that are allowable for the component's children.
        `child_count`: The number of children the regex component requires.
        `is_modifiable`: Whether the component can have frequency modifiers (`?`, `+`, `*`, `{}`) attached to it.
        `compile_function`: The function used when the regex component is compiled into a concrete instance.
        `strip_child_mods`: Whether the component cannot have children with modifiers (eg range `[value]-[value]`)
        `uniform_child_types`: Whether the component's children must all be of the same type (eg modifier ranged count `{X, Y}`)
        """
        # Truthify bools to defaults
        is_modifiable = is_modifiable if is_modifiable is not None else True
        strip_child_mods = strip_child_mods if strip_child_mods is not None else False
        uniform_child_types = (
            uniform_child_types if uniform_child_types is not None else False
        )

        self.name: str = name
        self.display_function: Callable = display_function
        self.compile_function: Callable = compile_function or display_function
        self.child_count: int = child_count or 0
        self.child_types: Optional[Sequence[str]] = child_types
        self.rxtype: RxType = rxtype
        self.is_modifiable: bool = self.rxtype.is_modifiable and is_modifiable
        self.strip_child_mods: bool = strip_child_mods
        self.uniform_child_types: bool = uniform_child_types

    def __repr__(self) -> str:
        return f"RxWrapper: {self.name}(children:{self.child_count}, mod:{self.is_modifiable})"

    def get_child_count(self) -> int:
        if self.child_count == RAND:
            return randint(1, MAX_CHILDREN)
        return self.child_count


class RxWrapperSet:
    def __init__(
        self,
        char_sets: CharSets,
        printable_subset: Optional[Iterable[str]] = None,
        init_wrappers: bool = True,
    ) -> None:
        self._wrappers: Dict[str, RxWrapper] = {}
        self._char_sets: CharSets = char_sets
        self._rxtypes: RxTypeSet = char_sets.rxtypes()
        if init_wrappers:
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

    def get_wrapper_func_name(self, name):
        return "".join([RXWRAPPER_SYMBOL_KEY.get(c, c) for c in name])

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
        is_char_set: Optional[bool] = None,
        display_value: Optional[str] = None,
        char_value: Optional[str] = None,
        char_set: Optional[Iterable[str]] = None,
    ) -> RxWrapper:
        func_name = self.get_wrapper_func_name(name)

        display_value = display_value or char_value
        if display_value:
            display_value = display_value.format(char_value)

        else:
            if (
                display_function_name not in rxwrapper_functions["display"]
                and func_name not in rxwrapper_functions["display"]
            ):
                raise TypeError("valid display function name or display value required")

            if (
                compile_function_name not in rxwrapper_functions["compile"]
                and func_name not in rxwrapper_functions["compile"]
            ):
                raise TypeError("valid compile function name or display value required")

        rxtype = self._rxtypes[rxtype_name]

        display_function = rxwrapper_functions["display"].get(
            display_function_name or func_name, _d(display_value)
        )
        compile_function = rxwrapper_functions["compile"].get(
            compile_function_name or func_name, _d(display_value)
        )

        if is_char_set:
            if not char_value:
                raise TypeError("char set wrappers require a char value")
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
            settings["rxtype_name"] = settings.get("rxtype_name", settings["name"])

            if settings.get("is_char_set"):
                type_name = settings.get("rxtype_name", settings["name"])
                char_set = settings.get("char_set") or CHAR_SETS[type_name]

                self._char_sets.init_char_set(type_name, printable_subset, char_set)

                for char in char_set:
                    settings["char_value"] = char
                    self.add(self.create_wrapper(**settings))

            else:
                self.add(self.create_wrapper(**settings))
