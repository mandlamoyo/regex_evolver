from __future__ import annotations
from typing import (
    TYPE_CHECKING,
    Callable,
    Iterable,
    Sequence,
    Hashable,
    Optional,
    Dict,
    List,
    Set,
    Tuple,
)
from random import choice, randint

from evolver.config import WHITESPACE_CHARS, MAX_COMPILE_MUTLIPLE, DOT_ALL
from evolver.exceptions import InvalidRegexError
from evolver.types import CharSets

if TYPE_CHECKING:
    from evolver.nodes import RxNode


# Utility functions
def set_choice(values: Set[str]) -> str:
    return choice(tuple(values))


def invert_set(
    node, char_set: Set[str], from_set: Optional[str] = "printable"
) -> Set[str]:
    """
    Given a character set and the name of a character group, returns the characters
    in the group that do not appear in the provided set.
    """
    if not isinstance(char_set, set):
        char_set = set(char_set)
    return node.char_sets[from_set] - char_set


def expand_set(node: "RxNode") -> Set[str]:
    """
    Returns a set of all the characters that are matched by a given regex node.
    """
    char_set = Set()

    # If the node is a range, add all the values between
    # the children specifying the boundary characters
    if node.name == "range":
        range_boundaries = sorted([ord(c.compile()) for c in node.children])
        for i in range(*range_boundaries):
            char_set.add(chr(i))
        char_set.add(chr(range_boundaries[1]))

    # If the node is a character set, add all corresponding characters
    elif node.rxtype.is_type_name("cset"):
        if "digit" in node.name:
            char_set |= node.char_sets["digit"]

        elif "whitespace" in node.name:
            char_set |= set(WHITESPACE_CHARS)

        elif "word" in node.name:
            char_set |= node.char_sets["alphanum"]
            char_set.add("_")

        if "!" in node.name:
            char_set = invert_set(node, char_set)

    # If the node is not a range or a character set, it can simply be compiled
    else:
        char_set.add(node.compile())

    return set(char_set)


def expand_sets(child_nodes: Sequence["RxNode"]) -> Set[str]:
    """
    Expands the set of characters that are matched by a series of regex nodes.
    """
    values: Set[str] = Set()
    for child in child_nodes:
        values |= expand_set(child)
    return values


def escape_nonrange_hyphen(displayed: str) -> str:
    """
    Function for escaping hyphens in sets that do not define a range.
    """
    if displayed == "-":
        displayed = r"\-"
    return displayed


# Regex wrapper display functions
def d_set(
    node: "RxNode",
    child_nodes: Sequence["RxNode"],
    invert: Optional[bool] = False,
) -> str:
    display = "".join(
        [escape_nonrange_hyphen(child.display()) for child in child_nodes]
    )
    if invert:
        display = "^" + display
    return f"[{display}]"


def d_nset(node: "RxNode", child_nodes: Sequence["RxNode"]) -> str:
    return d_set(node, child_nodes, invert=True)


def d_count(node: "RxNode", child_nodes: Sequence["RxNode"]) -> str:
    return "{" + child_nodes[0].display() + "}"


def d_count2(node: "RxNode", child_nodes: Sequence["RxNode"]) -> str:
    values = sorted([child_nodes[0].display(), child_nodes[1].display()])
    return "{" + values[0] + "," + values[1] + "}"


def d_or(node: "RxNode", child_nodes: Sequence["RxNode"]) -> str:
    return "(" + child_nodes[0].display() + "|" + child_nodes[1].display() + ")"


def d_range(node: "RxNode", child_nodes: Sequence["RxNode"]) -> str:
    values = sorted([child_nodes[0].display(), child_nodes[1].display()])
    return f"{values[0]}-{values[1]}"


# Regex wrapper compilation functions


def c_set(node: "RxNode", child_nodes: Sequence["RxNode"]) -> str:
    char_set = expand_sets(child_nodes)
    if not char_set:
        raise InvalidRegexError(f"Invalid set ({child_nodes})")
    return set_choice(char_set)


def c_nset(node: "RxNode", child_nodes: Sequence["RxNode"]) -> str:
    char_set = invert_set(node, expand_sets(child_nodes))
    if not char_set:
        raise InvalidRegexError(f"Invalid set inversion ({child_nodes})")
    return set_choice(char_set)


def c_or(node: "RxNode", child_nodes: Sequence["RxNode"]) -> str:
    return choice([child.compile() for child in child_nodes])


def c_range(node: "RxNode", child_nodes: Sequence["RxNode"]) -> str:
    return chr(randint(*sorted([ord(child.compile()) for child in child_nodes])))


def c_wildcard(node: "RxNode") -> str:
    if not DOT_ALL:
        return set_choice(invert_set(node, {"\n"}))
    return set_choice(node.char_sets["printable"])


## Modifiers
def c_count(node: "RxNode", child_nodes: Sequence["RxNode"], compiled: str) -> str:
    return compiled * int(child_nodes[0].compile())


def c_count2(node: "RxNode", child_nodes: Sequence["RxNode"], compiled: str) -> str:
    return compiled * randint(*sorted([int(child.compile()) for child in child_nodes]))


def c_zero_plus(node: "RxNode", compiled: str) -> str:
    return compiled * randint(0, MAX_COMPILE_MUTLIPLE)


def c_zero_one(node: "RxNode", compiled: str) -> str:
    return compiled * randint(0, 1)


def c_one_plus(node: "RxNode", compiled: str) -> str:
    return compiled * randint(1, MAX_COMPILE_MUTLIPLE)


def c_ngreedy(node: "RxNode", compiled: str, params: Iterable) -> str:
    if params:
        return compiled * min([int(p) for p in params])
    return compiled * randint(1, MAX_COMPILE_MUTLIPLE)


## Character Sets
def c_whitespace(node: "RxNode") -> str:
    w = choice(WHITESPACE_CHARS)
    return w


def c_nwhitespace(node: "RxNode") -> str:
    return set_choice(invert_set(node, set(WHITESPACE_CHARS)))


def c_empty(node: "RxNode") -> str:
    return ""


def c_digit(node: "RxNode") -> str:
    return set_choice(node.char_sets["digit"])


def c_ndigit(node: "RxNode") -> str:
    return set_choice(invert_set(node, node.char_sets["digit"]))


def c_word(node: "RxNode") -> str:
    return set_choice(node.char_sets["alphanum"] | {"_"})


def c_nword(node: "RxNode") -> str:
    return set_choice(invert_set(node, node.char_sets["alphanum"] | {"_"}))


rxwrapper_functions: Dict[str, Dict[str, Callable]] = {
    "display": {
        "set": d_set,
        "nset": d_nset,
        "count": d_count,
        "count2": d_count2,
        "range": d_range,
        "or": d_or,
    },
    "compile": {
        "set": c_set,
        "nset": c_nset,
        "count": c_count,
        "count2": c_count2,
        "range": c_range,
        "or": c_or,
        "wildcard": c_wildcard,
        "zero_one": c_zero_one,
        "zero_plus": c_zero_plus,
        "one_plus": c_one_plus,
        "ngreedy": c_ngreedy,
        "whitespace": c_whitespace,
        "nwhitespace": c_nwhitespace,
        "empty": c_empty,
        "digit": c_digit,
        "ndigit": c_ndigit,
        "word": c_word,
        "nword": c_nword,
    },
}
