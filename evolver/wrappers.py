from __future__ import annotations
from typing import Callable, Optional, Iterable, Dict, List

from evolver.types import RxType, CharSets
from evolver.wrapper_functions import *
from evolver.helpers import _d
from evolver.config import (
    RAND,
    MAX_CHILDREN,
    CHAR_SETS,
    META_CHARS,
    NON_META_SYMBOL_CHARS,
)

char_sets = CharSets.instance()


class RxWrapper:
    """
    The templates that define the various components of which regexes consist.
    """

    wrappers: Dict[str, RxWrapper] = {}

    @staticmethod
    def add_wrapper(regex_wrapper: RxWrapper) -> None:
        RxWrapper.wrappers[regex_wrapper.name] = regex_wrapper

    @staticmethod
    def add_wrappers(regex_wrappers: Iterable[RxWrapper]) -> None:
        for wrapper in regex_wrappers:
            RxWrapper.add_wrapper(wrapper)

    @staticmethod
    def get_wrapper(wrapper_name: str) -> RxWrapper:
        return RxWrapper.wrappers.get(wrapper_name, None)

    @staticmethod
    def wrapper_is_type(wrapper_name: str, type_name: str) -> bool:
        wrapper: RxWrapper = RxWrapper.get_wrapper(wrapper_name)
        if not wrapper:
            raise KeyError(f"wrapper {wrapper_name} not found")
        return wrapper.rxtype.is_type_name(type_name)

    @staticmethod
    def init_wrappers(printable_subset: Optional[Iterable[str]] = None) -> None:
        if not printable_subset:
            printable_subset = CHAR_SETS.keys()
        printable_subset = set(printable_subset)

        # clear containers
        RxWrapper.wrappers.clear()
        char_sets.empty_sets()

        char_sets.init_char_set("digit", RxWrapper, printable_subset)
        char_sets.init_char_set(
            "alpha_upper", RxWrapper, printable_subset, label="alpha"
        )
        char_sets.init_char_set(
            "alpha_lower", RxWrapper, printable_subset, label="alpha"
        )
        char_sets.init_char_set(
            "printable", RxWrapper, printable_subset, char_set=NON_META_SYMBOL_CHARS
        )
        char_sets.init_char_set(
            "printable",
            RxWrapper,
            printable_subset,
            char_set=META_CHARS,
            display_func_generator=lambda m: _d(r"\%s" % m),
            compile_function=_d,
        )

        for n in CHAR_SETS["digit"]:
            RxWrapper.add_wrapper(RxWrapper(f"int({n})", _d(n), "integer"))

        RxWrapper.add_wrappers(
            [
                RxWrapper(
                    "range",
                    d_range,
                    "range",
                    ["digit", "alpha_upper", "alpha_lower"],
                    2,
                    compile_function=c_range,
                    strip_child_mods=True,
                    uniform_child_types=True,
                ),
                RxWrapper(
                    "set",
                    d_set,
                    "re",
                    ["printable", "range", "cset"],
                    RAND,
                    compile_function=c_set,
                    strip_child_mods=True,
                ),
                RxWrapper(
                    "!set",
                    d_nset,
                    "re",
                    ["printable", "range", "cset"],
                    RAND,
                    compile_function=c_nset,
                    strip_child_mods=True,
                ),
                RxWrapper(
                    "count", d_count, "mod", ["integer"], 1, compile_function=c_count
                ),
                RxWrapper(
                    "count2", d_count2, "mod", ["integer"], 2, compile_function=c_count2
                ),
                RxWrapper(
                    "or",
                    d_or,
                    "re",
                    ["re"],
                    2,
                    compile_function=c_or,
                    is_modifiable=False,
                ),
                RxWrapper("wildcard", _d("."), "re", compile_function=c_wildcard),
                RxWrapper("0+", _d("*"), "mod", compile_function=c_zero_plus),
                RxWrapper("0/1", _d("?"), "mod", compile_function=c_zero_one),
                RxWrapper("1+", _d("+"), "mod", compile_function=c_one_plus),
                RxWrapper("!greedy", _d("?"), "mmod", compile_function=c_not_greedy),
                RxWrapper(
                    "whitespace", _d(r"\s"), "cset", compile_function=c_whitespace
                ),
                RxWrapper(
                    "!whitespace", _d(r"\S"), "cset", compile_function=c_nwhitespace
                ),
                RxWrapper("emptyterm", _d(r"\b"), "cset*", compile_function=c_empty),
                RxWrapper("emtpy!term", _d(r"\B"), "cset*", compile_function=c_empty),
                RxWrapper("digit", _d(r"\d"), "cset", compile_function=c_digit),
                RxWrapper("!digit", _d(r"\D"), "cset", compile_function=c_ndigit),
                RxWrapper("word", _d(r"\w"), "cset", compile_function=c_word),
                RxWrapper("!word", _d(r"\W"), "cset", compile_function=c_nword),
                RxWrapper("space", _d(r" "), "printable"),
            ]
        )

    def __init__(
        self,
        name: str,
        display_function: Callable[..., str],
        rxtype_name: str,
        child_types: Optional[List[str]] = None,
        child_count: Optional[int] = 0,
        is_modifiable: Optional[bool] = True,
        compile_function: Optional[Callable[..., str]] = None,
        strip_child_mods: Optional[bool] = False,
        uniform_child_types: Optional[bool] = False,
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
        self.rxtype = RxType.get_type(rxtype_name)
        self.is_modifiable = self.rxtype.is_modifiable and is_modifiable
        self.strip_child_mods = strip_child_mods
        self.uniform_child_types = uniform_child_types

    def __repr__(self) -> str:
        return f"RxWrapper: {self.name}(children:{self.child_count}, mod:{self.is_modifiable})"

    def get_child_count(self) -> int:
        if self.child_count == RAND:
            return randint(1, MAX_CHILDREN)
        return self.child_count