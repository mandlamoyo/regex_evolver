from evolver.config import CHAR_SETS
from evolver.helpers import first_nested

ESCAPE = "\\"
NAME = 0
MODIFIER = 1
CHILDREN = 2
KIND = 0
LEVEL = 1
VALUE = 2
SKIP = 1

csets = {
    "A": "start",
    "b": "emptyterm",
    "B": "empty!term",
    "d": "digit",
    "D": "!digit",
    "s": "whitespace",
    "S": "!whitespace",
    "w": "word",
    "W": "!word",
    "Z": "",
}
metas = {
    ".": "wildcard",
}
mods = {
    "?": "0/1",
    "*": "0+",
    "+": "1+",
    "{}": "count",
    "{,}": "count2",
}


def get_literal(char):
    if char == " ":
        return "space"
    elif char in CHAR_SETS["digit"]:
        return f"digit({char})"
    elif char in CHAR_SETS["alpha"]:
        return f"alpha({char})"
    else:
        return f"printable({char})"


def extract_symbols(regex_string, level=0):
    is_inverted = False
    is_escaped = False
    is_count = False
    is_mod = False
    is_set = False
    or_groups = []
    symbols = []
    skips = []

    if level == 0:
        regex_string = f"({regex_string})"

    for i in range(len(regex_string)):
        c = regex_string[i]

        if skips:
            skips.pop()
        else:
            if c not in mods and is_mod:
                is_mod = False

            if is_escaped:
                if c in csets:
                    symbols.append(("RE", level, [csets[c], None, []]))
                elif c in CHAR_SETS["digit"]:
                    symbols.append(("RE", level, [f"#match({c})", None, []]))
                elif c in CHAR_SETS["meta"]:
                    symbols.append(("RE", level, [f"printable({c})", None, []]))

                is_escaped = False

            elif c in metas:
                symbols.append(("RE", level, [metas[c], None, []]))

            elif c == "|":
                or_groups.append(("RE", level - 0.5, ["group", None, []]))
                or_groups.extend(symbols)
                symbols = []

            elif c == "(":
                group, offset = extract_symbols(regex_string[i + 1 :], level + 1)
                symbols.extend(group)
                for i in range(offset):
                    skips.append(SKIP)

            elif c == ")":
                if or_groups:
                    or_groups.append(("RE", level - 0.5, ["group", None, []]))
                    or_groups.extend(symbols)
                    return [("RE", level - 1, ["or", None, []])] + or_groups, i + 1
                else:
                    return [("RE", level - 1, ["group", None, []])] + symbols, i + 1

            elif c in set(["[", "{"]):
                if c == "[":
                    if regex_string[i + 1] == "^":
                        symbols.append(("RE", level, ["!set", None, []]))
                        skips.append(SKIP)
                    else:
                        symbols.append(("RE", level, ["set", None, []]))
                    is_set = True

                elif c == "{":
                    symbols.append(("MOD", level, ["count", None, []]))
                    is_count = True
                level += 1

            elif c in set(["]", "}"]):
                if c == "]":
                    is_set = False
                if c == "}":
                    is_count = False
                    is_mod = True
                level -= 1

            elif is_set:
                if c == "-":
                    if (
                        regex_string[i - 1] in CHAR_SETS["alphanum"]
                        and regex_string[i + 1] in CHAR_SETS["alphanum"]
                    ):
                        symbols.pop()
                        symbols.extend(
                            [
                                ("RE", level, ["range", None, []]),
                                (
                                    "RE",
                                    level + 1,
                                    [get_literal(regex_string[i - 1]), None, []],
                                ),
                                (
                                    "RE",
                                    level + 1,
                                    [get_literal(regex_string[i + 1]), None, []],
                                ),
                            ]
                        )
                        skips.append(SKIP)
                    elif regex_string[i + 1] not in CHAR_SETS["alphanum"]:
                        raise ValueError("invalid hyphen literal placement in set")

                else:
                    symbols.append(("RE", level, [get_literal(c), None, []]))

            elif is_count:
                if c == ",":
                    assert symbols[-2][VALUE][NAME] == "count"
                    symbols[-2][VALUE][NAME] = "count2"
                elif c in CHAR_SETS["digit"]:
                    symbols.append(("RE", level, [f"int({c})", None, []]))
                else:
                    raise ValueError(f"invalid value '{c}' in count parameters")

            elif c in mods:
                if is_mod:
                    if c == "?":
                        symbols.append(("MOD", level, ["greedy", None, []]))
                        is_mod = False
                    else:
                        raise ValueError(f"cannot modify a modifier with'{c}'")

                else:
                    symbols.append(("MOD", level, [mods[c], None, []]))
                    is_mod = True

            else:
                is_escaped = False
                if c == "\\":
                    is_escaped = True
                else:
                    symbols.append(("RE", level, [get_literal(c), None, []]))
    return symbols, -1


def construct_rxspec(symbols):
    min_level = 0
    if symbols[0][VALUE][NAME] == "group":
        symbols = symbols[1:]
        min_level += 1

    for i in reversed(range(len(symbols))):
        if symbols[i][KIND] == "MOD":
            j = i - 1
            while j > min_level and symbols[j][LEVEL] != symbols[i][LEVEL]:
                j -= 1

            # Remove empty values from current modifier
            modifier = list(filter(lambda x: x, symbols[i][VALUE]))
            if len(modifier) == 1:
                [modifier] = modifier

            # Set modifier as owner's modifier
            symbols[j][VALUE][MODIFIER] = modifier

        if symbols[i][LEVEL] > min_level:
            j = i - 1
            while j > 0 and symbols[j][LEVEL] >= symbols[i][LEVEL]:
                j -= 1

            # Remove empty values from current child
            child = list(filter(lambda x: x, symbols[i][VALUE]))
            if len(child) == 1:
                [child] = child

            # Add child to parent's list of children
            symbols[j][VALUE][CHILDREN] = [child] + symbols[j][VALUE][CHILDREN]

    symbols = filter(
        lambda node: node[KIND] != "MOD" and node[LEVEL] == min_level, symbols
    )
    symbols = list(map(lambda node: node[VALUE], symbols))

    out = []
    for i in range(len(symbols)):
        node = list(filter(lambda x: x, symbols[i]))
        if len(node) == 1:
            [node] = node
        out.append(node)
    return out


def parse_rxspec(rxspec):
    if not isinstance(rxspec, list):
        rxspec = [rxspec]

    node_spec = {"rw_name": rxspec[0]}
    for spec in rxspec[1:]:
        if first_nested(spec) in mods.values():
            node_spec["modifier"] = parse_rxspec(spec)

        else:
            node_spec["children"] = [parse_rxspec(child) for child in spec]

    return node_spec


def parse_regex(regex_string):
    symbols, _ = extract_symbols(regex_string)
    rxspec = construct_rxspec(symbols)
    return [parse_rxspec(spec) for spec in rxspec]
