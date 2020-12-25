from typing import Iterable, Sequence, Optional, List
from random import choice, randint

from evolver.config import WHITESPACE_CHARS, MAX_COMPILE_MUTLIPLE, DOT_ALL
from evolver.exceptions import InvalidRegexError
from evolver.types import CharSets

char_sets = CharSets.instance()

# Utility functions
def invert_set(
    char_set: Iterable[str], from_set: Optional[str] = "printable"
) -> List[str]:
    """"""
    if not isinstance(char_set, set):
        char_set = set(char_set)
    return list(char_sets[from_set] - char_set)


def expand_set(node):
    char_set = []
    # for n in l:

    if node.name == "range":
        range_boundaries = sorted([ord(c.compile()) for c in node.children])
        for i in range(*range_boundaries):
            char_set.extend([chr(i)])
        char_set.append(chr(range_boundaries[1]))

    elif node.re_type.is_type_name("cset"):
        if "digit" in node.name:
            # char_set.extend([v for v in CHAR_SETS["digit"]])
            char_set += list(char_sets["digit"])

        elif "whitespace" in node.name:
            char_set.extend(WHITESPACE_CHARS)

        elif "word" in node.name:
            # char_set.extend([v for v in CHAR_SETS["alphanum"] + "_"])
            char_set += list(char_sets["alphanum"])
            char_set.append("_")

        if "!" in node.name:
            char_set = invert_set(char_set)
    else:
        char_set.append(node.compile())
    return tuple(set(char_set))


def expand_sets(l):
    values = []
    for node in l:
        values.extend(expand_set(node))
    return tuple(set(values))


# Regex wrapper display functions
def d_set(child_nodes: Sequence["RxNode"], invert: Optional[bool] = False):
    def escape_nonrange_hyphen(displayed):
        if displayed == "-":
            displayed = r"\-"
        return displayed

    display = "".join(
        [escape_nonrange_hyphen(child.display()) for child in child_nodes]
    )
    if invert:
        display = "^" + display
    return f"[{display}]"


def d_nset(child_nodes: Sequence["RxNode"]):
    return d_set(child_nodes, invert=True)


def d_count(child_nodes: Sequence["RxNode"]):
    return "{" + child_nodes[0].display() + "}"


def d_count2(child_nodes: Sequence["RxNode"]):
    values = sorted([child_nodes[0].display(), child_nodes[1].display()])
    return "{" + values[0] + "," + values[1] + "}"


def d_or(child_nodes: Sequence["RxNode"]):
    return "(" + child_nodes[0].display() + "|" + child_nodes[1].display() + ")"


def d_range(child_nodes: Sequence["RxNode"]):
    values = sorted([child_nodes[0].display(), child_nodes[1].display()])
    return f"{values[0]}-{values[1]}"


# Regex wrapper compilation functions


def c_set(l):
    char_set = expand_sets(l)
    if not char_set:
        raise InvalidRegexError(f"Invalid set ({l})")
    return choice(char_set)


def c_nset(l):
    char_set = invert_set(expand_sets(l))
    if not char_set:
        raise InvalidRegexError(f"Invalid set inversion ({l})")
    return choice(char_set)


def c_count(l, compiled):
    return compiled * int(l[0].compile())


def c_count2(l, compiled):
    return compiled * randint(*sorted([int(v.compile()) for v in l]))


def c_or(l):
    return choice([v.compile() for v in l])


def c_range(l):
    return chr(randint(*sorted([ord(v.compile()) for v in l])))


def c_wildcard():
    if not DOT_ALL:
        return choice(invert_set(["\n"]))
    return choice(list(char_sets["printable"]))


def c_zero_plus(compiled):
    return compiled * randint(0, MAX_COMPILE_MUTLIPLE)


def c_zero_one(compiled):
    return compiled * randint(0, 1)


def c_one_plus(compiled):
    return compiled * randint(1, MAX_COMPILE_MUTLIPLE)


def c_not_greedy(compiled, params):
    if params:
        return compiled * min([int(p) for p in params])
    return compiled * randint(1, MAX_COMPILE_MUTLIPLE)


def c_whitespace():
    w = choice(WHITESPACE_CHARS)
    return w


def c_nwhitespace():
    return choice(invert_set(WHITESPACE_CHARS))


def c_empty():
    return ""


def c_digit():
    return choice(char_sets["digit"])


def c_ndigit():
    return choice(invert_set(char_sets["digit"]))


def c_word():
    return choice(char_sets["alphanum"] + "_")


def c_nword():
    return choice(invert_set(char_sets["alphanum"] + "_"))