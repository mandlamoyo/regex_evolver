from typing import Iterable, Sequence, Hashable, Optional, List, Set, Tuple
from random import choice, randint

from evolver.config import WHITESPACE_CHARS, MAX_COMPILE_MUTLIPLE, DOT_ALL
from evolver.exceptions import InvalidRegexError
from evolver.types import CharSets

char_sets = CharSets.instance()

# Utility functions
def set_choice(values: set) -> Hashable:
    return choice(tuple(set))


def invert_set(char_set: Set[str], from_set: Optional[str] = "printable") -> Set[str]:
    """
    Given a character set and the name of a character group, returns the characters
    in the group that do not appear in the provided set.
    """
    if not isinstance(char_set, set):
        char_set = set(char_set)
    return list(char_sets[from_set] - char_set)


def expand_set(node: "RxNode") -> Set(str):
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
    elif node.re_type.is_type_name("cset"):
        if "digit" in node.name:
            char_set |= char_sets["digit"]

        elif "whitespace" in node.name:
            char_set |= set(WHITESPACE_CHARS)

        elif "word" in node.name:
            char_set |= char_sets["alphanum"]
            char_set.add("_")

        if "!" in node.name:
            char_set = invert_set(char_set)

    # If the node is not a range or a character set, it can simply be compiled
    else:
        char_set.append(node.compile())

    return set(char_set)


def expand_sets(child_nodes: Sequence["RxNode"]) -> Set[str]:
    """
    Expands the set of characters that are matched by a series of regex nodes.
    """
    values: Set["RxNode"] = Set()
    for node in child_nodes:
        values |= expand_set(node)
    return values


def escape_nonrange_hyphen(displayed: str) -> str:
    """
    Function for escaping hyphens in sets that do not define a range.
    """
    if displayed == "-":
        displayed = r"\-"
    return displayed


# Regex wrapper display functions
def d_set(child_nodes: Sequence["RxNode"], invert: Optional[bool] = False) -> str:
    display = "".join(
        [escape_nonrange_hyphen(child.display()) for child in child_nodes]
    )
    if invert:
        display = "^" + display
    return f"[{display}]"


def d_nset(child_nodes: Sequence["RxNode"]) -> str:
    return d_set(child_nodes, invert=True)


def d_count(child_nodes: Sequence["RxNode"]) -> str:
    return "{" + child_nodes[0].display() + "}"


def d_count2(child_nodes: Sequence["RxNode"]) -> str:
    values = sorted([child_nodes[0].display(), child_nodes[1].display()])
    return "{" + values[0] + "," + values[1] + "}"


def d_or(child_nodes: Sequence["RxNode"]) -> str:
    return "(" + child_nodes[0].display() + "|" + child_nodes[1].display() + ")"


def d_range(child_nodes: Sequence["RxNode"]) -> str:
    values = sorted([child_nodes[0].display(), child_nodes[1].display()])
    return f"{values[0]}-{values[1]}"


# Regex wrapper compilation functions


def c_set(child_nodes: Sequence["RxNode"]) -> str:
    char_set = expand_sets(child_nodes)
    if not char_set:
        raise InvalidRegexError(f"Invalid set ({child_nodes})")
    return set_choice(char_set)


def c_nset(child_nodes: Sequence["RxNode"]) -> str:
    char_set = invert_set(expand_sets(child_nodes))
    if not char_set:
        raise InvalidRegexError(f"Invalid set inversion ({child_nodes})")
    return set_choice(char_set)


def c_or(child_nodes: Sequence["RxNode"]) -> str:
    return choice([child.compile() for child in child_nodes])


def c_range(child_nodes: Sequence["RxNode"]) -> str:
    return chr(randint(*sorted([ord(child.compile()) for child in child_nodes])))


def c_wildcard() -> str:
    if not DOT_ALL:
        return set_choice(invert_set(["\n"]))
    return set_choice(char_sets["printable"])


## Modifiers
def c_count(child_nodes: Sequence["RxNode"], compiled: str) -> str:
    return compiled * int(child_nodes[0].compile())


def c_count2(child_nodes: Sequence["RxNode"], compiled: str) -> str:
    return compiled * randint(*sorted([int(child.compile()) for child in child_nodes]))


def c_zero_plus(compiled: str) -> str:
    return compiled * randint(0, MAX_COMPILE_MUTLIPLE)


def c_zero_one(compiled: str) -> str:
    return compiled * randint(0, 1)


def c_one_plus(compiled: str) -> str:
    return compiled * randint(1, MAX_COMPILE_MUTLIPLE)


def c_not_greedy(compiled: str, params: Iterable) -> str:
    if params:
        return compiled * min([int(p) for p in params])
    return compiled * randint(1, MAX_COMPILE_MUTLIPLE)


## Character Sets
def c_whitespace() -> str:
    w = choice(WHITESPACE_CHARS)
    return w


def c_nwhitespace() -> str:
    return set_choice(invert_set(WHITESPACE_CHARS))


def c_empty() -> str:
    return ""


def c_digit() -> str:
    return set_choice(char_sets["digit"])


def c_ndigit() -> str:
    return set_choice(invert_set(char_sets["digit"]))


def c_word() -> str:
    return set_choice(char_sets["alphanum"] + "_")


def c_nword() -> str:
    return set_choice(invert_set(char_sets["alphanum"] + "_"))