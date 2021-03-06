from random import random, randint, choice, sample
from copy import deepcopy
from math import log
import string
import csv
import re

# settings
MAX_GEN = 500
POP_SIZE = 500
SIZE_DATASET = 300

# parameters
MUTATION_RATE = 0.2
CROSSOVER_RATE = 0.4
P_NEW_UPPER = 0.9
P_NEW_LOWER = 0.6
P_EXP = 0.7

P_MODIFIER = 0.1
P_EXTEND = 0.76

# constants
RAND = -1
MAX_WORDS = 5
MAX_CHILDREN = 5
MAX_COMPILE_MUTLIPLE = 5

DOT_ALL = False  # wildcard matches newlines
SUPPRESS_ROOT_CHARS = True  # character constants can only be generated as node children
DISPLAY_MESSAGES = True
WHITESPACE_CHARS = string.whitespace  # [" ", "\t", "\n", "\r", "\f", "\v"]
NON_META_SYMBOL_CHARS = "'!\"£-~#%&@:;<>/,"
META_CHARS = r".^$*+?{}[]\|()\\"
CHAR_SETS = {
    "alpha_upper": string.ascii_uppercase,
    "alpha_lower": string.ascii_lowercase,
    "alpha": string.ascii_letters,
    "alphanum": string.digits + string.ascii_letters,
    "digit": string.digits,
    "printable": string.printable,
}


class InvalidRegexError(Exception):
    """Raised when an invalid regex has been specified"""

    pass


class NotFoundError(Exception):
    """Raised when no valid regex match can be compiled"""

    pass


# Regex wrapper display functions
def d_set(l, invert=False):
    def escape_nonrange_hyphen(displayed):
        if displayed == "-":
            displayed = r"\-"
        return displayed

    display = "".join([escape_nonrange_hyphen(v.display()) for v in l])
    if invert:
        display = "^" + display
    return f"[{display}]"


def d_nset(l):
    return d_set(l, invert=True)


def d_count(l):
    return "{" + l[0].display() + "}"


def d_count2(l):
    values = sorted([l[0].display(), l[1].display()])
    return "{" + values[0] + "," + values[1] + "}"


def d_or(l):
    return "(" + l[0].display() + "|" + l[1].display() + ")"


def d_range(l):
    values = sorted([l[0].display(), l[1].display()])
    return f"{values[0]}-{values[1]}"


def _d(v):
    return lambda: v


# Regex wrapper compile functions


def invert_set(values, char_set="printable"):
    if not isinstance(values, set):
        values = set(values)
    return list(RxWrapper.char_sets[char_set] - values)


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
            char_set += list(RxWrapper.char_sets["digit"])

        elif "whitespace" in node.name:
            char_set.extend(WHITESPACE_CHARS)

        elif "word" in node.name:
            # char_set.extend([v for v in CHAR_SETS["alphanum"] + "_"])
            char_set += list(RxWrapper.char_sets["alphanum"])
            char_set.append("_")

        if "!" in node.name:
            char_set = invert_set(char_set)
    else:
        char_set.append(node.compile())
    return list(set(char_set))


def expand_sets(l):
    values = []
    for node in l:
        values.extend(expand_set(node))
    return list(set(values))


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
    return choice(list(RxWrapper.char_sets["printable"]))


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
    return choice(RxWrapper.char_sets["digit"])


def c_ndigit():
    return choice(invert_set(RxWrapper.char_sets["digit"]))


def c_word():
    return choice(RxWrapper.char_sets["alphanum"] + "_")


def c_nword():
    return choice(invert_set(RxWrapper.char_sets["alphanum"] + "_"))


# Classes
class RxTypeCollection:
    def __init__(self):
        self.types = {}

    def get(self, name):
        return self.types[name]

    def add(self, re_type):
        self.types[re_type.name] = re_type

    def add_all(self, re_types):
        for re_type in re_types:
            self.add(re_type)


class RxType:
    c = RxTypeCollection()

    @staticmethod
    def init_types():
        RxType.c.add(RxType("re"))
        RxType.c.add(RxType("mod"))
        RxType.c.add(RxType("integer", is_modifiable=False))
        RxType.c.add(RxType("range", is_modifiable=False))
        RxType.c.add(RxType("cset", RxType.c.get("re")))
        RxType.c.add(RxType("cset*", RxType.c.get("re"), is_modifiable=False))
        RxType.c.add(RxType("printable", RxType.c.get("re")))
        RxType.c.add(RxType("alphanum", RxType.c.get("printable")))
        RxType.c.add(RxType("digit", RxType.c.get("alphanum")))
        RxType.c.add(RxType("alpha", RxType.c.get("alphanum")))
        RxType.c.add(RxType("alpha_upper", RxType.c.get("alpha")))
        RxType.c.add(RxType("alpha_lower", RxType.c.get("alpha")))
        RxType.c.add(RxType("mmod", RxType.c.get("mod"), is_modifiable=False))

    @staticmethod
    def is_of(instance_name, of_name):
        return RxType.c.get(instance_name).is_type_name(of_name)

    @staticmethod
    def is_one_of(instance_name, of_names):
        for name in of_names:
            if RxType.is_of(instance_name, name):
                return True
        return False

    @staticmethod
    def get_full_type_names(type_name):
        rxtype = RxType.c.get(type_name)
        type_list = [type_name]
        while rxtype.parent:
            rxtype = rxtype.parent
            type_list.append(rxtype.name)
        return type_list

    def __init__(self, name, parent_rxtype=None, is_modifiable=True):
        self.name = name
        self.parent = parent_rxtype
        self.is_modifiable = is_modifiable

    def __repr__(self):
        parent_name = "-"
        if self.parent:
            parent_name = self.parent.name
        return f"T: {self.name} ({parent_name}, mod:{self.is_modifiable})"

    def is_type(self, re_type, strict=False):
        return self.name == re_type.name or (
            not strict and self.parent and self.parent.is_type(re_type)
        )

    def is_type_name(self, type_name, strict=False):
        if not strict and self.parent:
            return self.name == type_name or self.parent.is_type_name(type_name)
        return self.name == type_name


class RxWrapper:
    wrappers = {}
    char_sets = {c: set() for c in CHAR_SETS.keys()}

    @staticmethod
    def add_wrapper(regex_wrapper):
        RxWrapper.wrappers[regex_wrapper.name] = regex_wrapper

    @staticmethod
    def add_wrappers(regex_wrappers):
        for wrapper in regex_wrappers:
            RxWrapper.add_wrapper(wrapper)

    @staticmethod
    def get_wrapper(wrapper_name):
        return RxWrapper.wrappers.get(wrapper_name, None)

    @staticmethod
    def wrapper_is_type(wrapper_name, type_name):
        wrapper = RxWrapper.get_wrapper(wrapper_name)
        if not wrapper:
            raise KeyError(f"wrapper {wrapper_name} not found")
        return wrapper.re_type.is_type_name(type_name)

    @staticmethod
    def init_char_set(
        type_name,
        printable_subset=None,
        label=None,
        display_func_generator=_d,
        compile_function=None,
        char_set=None,
    ):
        label = label or type_name
        char_set = char_set or CHAR_SETS[type_name]
        type_names = set(RxType.get_full_type_names(type_name))

        if type_names & printable_subset:
            for s in char_set:
                RxWrapper.add_wrapper(
                    RxWrapper(
                        f"{label}({s})",
                        display_func_generator(s),
                        type_name,
                        compile_function=compile_function,
                    )
                )

                for name in type_names:
                    if name in RxWrapper.char_sets:
                        RxWrapper.char_sets[name].add(s)

    @staticmethod
    def init_wrappers(printable_subset=None):
        if not printable_subset:
            printable_subset = CHAR_SETS.keys()
        printable_subset = set(printable_subset)

        # clear containers
        RxWrapper.wrappers.clear()
        for key in RxWrapper.char_sets.keys():
            RxWrapper.char_sets[key].clear()

        RxWrapper.init_char_set("digit", printable_subset)
        RxWrapper.init_char_set("alpha_upper", printable_subset, label="alpha")
        RxWrapper.init_char_set("alpha_lower", printable_subset, label="alpha")
        RxWrapper.init_char_set(
            "printable", printable_subset, char_set=NON_META_SYMBOL_CHARS
        )
        RxWrapper.init_char_set(
            "printable",
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
        name,
        display_function,
        re_type,
        child_types=None,
        child_count=0,
        is_modifiable=True,
        compile_function=None,
        strip_child_mods=False,
        uniform_child_types=False,
    ):
        self.name = name
        self.display_function = display_function
        self.compile_function = compile_function or display_function
        self.child_count = child_count
        self.child_types = child_types
        self.re_type = RxType.c.get(re_type)
        self.is_modifiable = self.re_type.is_modifiable and is_modifiable
        self.strip_child_mods = strip_child_mods
        self.uniform_child_types = uniform_child_types

    def __repr__(self):
        return f"RxWrapper: {self.name}(children:{self.child_count}, mod:{self.is_modifiable})"

    def get_child_count(self):
        if self.child_count == RAND:
            return randint(1, MAX_CHILDREN)
        return self.child_count


class RxNode:
    @staticmethod
    def make_node(
        rw_name=None,
        children=RAND,
        modifier=None,
        rw=None,
        is_child=False,
        omit_types=None,
        omit_wrappers=None,
        strict_type_match=False,
    ):
        """
        children format: [{'rw_name': regex_wrapper_name, 'children': [<children>]})]
        modifier format: {'rw_name': <modifier_name>, 'children': <children>, 'modifier': <modifier>}
        """
        omit_types = omit_types or []
        omit_wrappers = omit_wrappers or []

        if not rw:
            if not rw_name:
                raise ValueError("must provide regex wrapper object or name")

            rw = RxWrapper.get_wrapper(rw_name)

        child_nodes = []
        if rw.child_count != 0:
            if children == RAND:
                child_types = list(
                    filter(
                        lambda type_name: not RxType.is_one_of(type_name, omit_types),
                        rw.child_types,
                    )
                )

                # print("> ", rw)
                # print(">> ", omit_types)
                # print(">>> ", child_types)

                if rw.uniform_child_types:
                    child_types = sample(rw.child_types, 1)
                child_nodes = [
                    RxNode.make_random_node(
                        choice(child_types),
                        is_child=True,
                        omit_types=omit_types,
                        omit_wrappers=omit_wrappers,
                    )
                    for i in range(rw.get_child_count())
                ]
            else:
                for child in children:
                    child_nodes.append(
                        RxNode.make_node(
                            **child,
                            is_child=True,
                            omit_types=omit_types,
                            omit_wrappers=omit_wrappers,
                        )
                    )

        node = RxNode(rw, child_nodes, is_child)
        if rw.is_modifiable:
            if modifier == RAND:
                # print("- ", node.name)
                # print("- ", rw.name)
                # print("- ", rw.re_type)
                # print("- ", rw.re_type.is_type_name("mod"))

                # if wrapper is not a modifier, build a modifier. Otherwise, build mod-modifier.
                mod_type = "mmod" if rw.re_type.is_type_name("mod") else "mod"
                # print("- ", mod_type)
                # if mod_type (to make) is mod, then don't build an mmod
                # omit_types += ["mmod"] if mod_type == "mod" else []
                # print(">> ", omit_types)
                if mod_type not in omit_types:
                    modifier = RxNode.make_random_node(
                        mod_type,
                        omit_types=omit_types,
                        omit_wrappers=omit_wrappers,
                        strict_type_match=True,
                    )
                    node.set_modifier(modifier)
                # print("-- ", modifier)
            elif modifier:
                modifier = RxNode.make_node(**modifier)
                node.set_modifier(modifier)

        return node

    @staticmethod
    def make_random_node(
        type_name="re",
        is_child=False,
        prob_modifier=P_MODIFIER,
        omit_types=None,
        omit_wrappers=None,
        strict_type_match=False,
    ):
        omit_types = omit_types or []
        omit_wrappers = omit_wrappers or []
        re_type = RxType.c.get(type_name)

        # filter RxWrapper.wrappers with items that match re_type
        filtered_wrappers = list(
            filter(
                lambda rw: rw.re_type.is_type(re_type, strict=strict_type_match),
                RxWrapper.wrappers.values(),
            )
        )

        # filter out types specified for omission in node generation
        for omit in omit_types:
            omit_type = RxType.c.get(omit)
            filtered_wrappers = list(
                filter(lambda rw: not rw.re_type.is_type(omit_type), filtered_wrappers)
            )

        # filter out characters if is root node and suppression parameter specified
        if not is_child and SUPPRESS_ROOT_CHARS:
            filtered_wrappers = list(
                filter(
                    lambda rw: not rw.re_type.is_type(RxType.c.get("printable")),
                    filtered_wrappers,
                )
            )

        # filter out wrappers specified for omission in node generation
        for omit in omit_wrappers:
            filtered_wrappers = list(
                filter(lambda rw: rw.name != omit, filtered_wrappers)
            )

        rw = choice(filtered_wrappers)
        modifier = None
        if rw.is_modifiable and random() < prob_modifier:
            modifier = RAND

        return RxNode.make_node(
            rw=rw,
            modifier=modifier,
            is_child=is_child,
            omit_types=omit_types,
            omit_wrappers=omit_wrappers,
        )

    def __init__(self, rw, children, is_child):
        self.next = None  # TODO: remove?
        self.name = rw.name
        self.modifier = None
        self.assertion = None
        self.children = children
        self.re_type = rw.re_type
        self.display_function = rw.display_function
        self.compile_function = rw.compile_function
        self.is_child = is_child
        self.strip_child_mods = rw.strip_child_mods
        self.strip_mod = False

        for child in self.children:
            if self.strip_child_mods:
                child.strip_mod = True

    def __repr__(self):
        out = f"{self.name}"
        if self.modifier:
            out += f":<{self.modifier}>"
        if self.children:
            out += f"{str(self.children)}"
        return out

    def set_assertion(self, assertion):
        self.assertion = assertion

    def set_modifier(self, modifier):
        self.modifier = modifier

    def set_next(self, node):
        self.next = node

    def display(self):
        out = ""

        if self.assertion and not self.strip_mod:
            out += self.assertion.display()

        if self.children:
            out += self.display_function(self.children)

        else:
            out += self.display_function()
        # print('- ', self.name, self.re_type)

        if self.modifier and not self.strip_mod:
            out += self.modifier.display()

        if self.next:
            out += self.next.display()

        return out

    def compile(self, compiled_node=None, compiled_children=None):
        args = []

        if self.children:
            args.append(self.children)

        if self.re_type.is_type_name("mod"):
            args.append(compiled_node)

        if self.re_type.is_type_name("mmod"):
            args.append(compiled_children)

        res = self.compile_function(*args)

        if self.modifier and not self.strip_mod:
            res = self.modifier.compile(
                res, [child.compile() for child in self.children]
            )
        return res

    def mutate(self, prob_change=0.1):
        if random() < prob_change:
            return RxNode.make_random_node(
                type_name=self.re_type.name, is_child=self.is_child
            )
        else:
            new_children = []
            for child in self.children:
                new_children.append(child.mutate())

            new_node = deepcopy(self)
            new_node.children = new_children
            return new_node


class RxNodeSet:
    @staticmethod
    def make_node_set(regex_node_set_info):
        """
        format: [
            'name_1',
            ['<name_2>', <modifier>]
            ['<name_3>', [<child_1>]],
            ['<name_4>', [<child_1>, <child_2>]],
            ['<name_5>', [<child_1>], <modifier>],
            ['<name_6>', <modifier>, [<child_1>]],
            ['<name_7>', [<modifier>, [<child_1>]], [<child_1>]],
            ['<name_8>', [[<child_1>, [<sub_child_1>, <sub_child_2>]], <child_2>]]
        ]
        """

        def first_nested(li):
            if not li:
                raise ValueError("list is empty")

            if isinstance(li, list):
                return first_nested(li[0])
            return li

        def format_node(node_info):
            if not isinstance(node_info, list):
                node_info = [node_info]

            node = {"rw_name": node_info[0]}
            for n in node_info[1:]:
                if RxWrapper.wrapper_is_type(first_nested(n), "mod"):
                    node["modifier"] = format_node(n)

                else:
                    node["children"] = [format_node(child) for child in n]

            return node

        formatted_node_info = [format_node(n) for n in regex_node_set_info]
        return RxNodeSet([RxNode.make_node(**fn) for fn in formatted_node_info])

    @staticmethod
    def random_node_set(prob_extend=P_EXTEND, omit_types=None, omit_wrappers=None):
        nodes = [
            RxNode.make_random_node(omit_types=omit_types, omit_wrappers=omit_wrappers)
        ]
        while random() < prob_extend:
            nodes.append(
                RxNode.make_random_node(
                    omit_types=omit_types, omit_wrappers=omit_wrappers
                )
            )
        return RxNodeSet(nodes)

    def __init__(self, nodes):
        self.nodes = nodes

    def __repr__(self):
        return ", ".join([str(node) for node in self.nodes])

    def display(self):
        return "".join([node.display() for node in self.nodes])

    def compile(self):
        try:
            return "".join([node.compile() for node in self.nodes])
        except InvalidRegexError as e:
            print(f"{self.display()} is an invalid regex")
            print(e)
            return None
        except:
            raise

    def mutate(self, prob_change):
        new_nodes = [node.mutate(prob_change) for node in self.nodes]
        if random() < prob_change:
            ix = randint(0, len(new_nodes) - 1)
            if random() < 0.5 and len(new_nodes) > 1:
                new_nodes = new_nodes[:ix] + new_nodes[ix + 1 :]
            else:
                new_nodes = (
                    new_nodes[:ix] + [RxNode.make_random_node()] + new_nodes[ix:]
                )
        return RxNodeSet(new_nodes)

    def crossover(self, node_set, probswap):
        new_nodes = self.nodes
        if random() < probswap:
            max_len = max([len(self.nodes), len(node_set.nodes)])
            cuts = sorted([randint(0, max_len), randint(0, max_len)])
            new_nodes = (
                self.nodes[: cuts[0]]
                + node_set.nodes[cuts[0] : cuts[1]]
                + self.nodes[cuts[1] :]
            )
        return RxNodeSet([deepcopy(node) for node in new_nodes])


class GeneticAlgorithm:
    @staticmethod
    def select_index(limit, pexp=0.7):
        return min(int(log(random()) / log(pexp)), limit)

    @staticmethod
    def check_match(pattern, string):
        m = re.fullmatch(pattern, string)
        return m is not None

    @staticmethod
    def safe_sample(collection, size=None):
        if size and size <= len(collection):
            return sample(collection, size)
        return collection

    def __init__(self, dataset=None):
        self.population = []
        self.dataset = dataset

    def load_data(self, dataset=None, filepath=None, delimiter=",", quotechar="|"):
        if not dataset:
            if not filepath:
                raise ValueError("must provide dataset or filepath")

            dataset = []
            with open(filepath, newline="") as f:
                csvreader = csv.reader(f, delimiter=delimiter, quotechar=quotechar)
                for row in csvreader:
                    dataset.append((row[0], row[1].strip().lower() in ["true", "t"]))

        self.dataset = dataset

    def generate_population(self, n=10):
        self.population = [RxNodeSet.random_node_set() for _ in range(n)]

    def sample_dataset(self, size=None):
        return GeneticAlgorithm.safe_sample(self.dataset, size)

    def sample_population(self, size=None):
        return GeneticAlgorithm.safe_sample(self.population, size)

    def score_func(
        self, node_set=None, sample_size=None, verbose=False, regex_string=None
    ):
        correct = 0
        if not regex_string:
            if not node_set:
                return 1
            regex_string = node_set.display()

        if verbose:
            print("> [regex] [test_string] [expected] [actual]")
        dataset = self.sample_dataset(sample_size)
        for row in dataset:
            res = GeneticAlgorithm.check_match(regex_string, row[0])
            if res == row[1]:
                correct += 1
            if verbose:
                print("> ", regex_string, row[0], row[1], res)
        if verbose:
            print("\n>> [num_correct] [len_dataset] [% correct] [% incorrect]")
            print(
                ">> ",
                correct,
                len(dataset),
                correct / len(dataset),
                1 - correct / len(dataset),
            )
            print()
        return 1 - correct / len(dataset)

    def rank_population(self, sample_size=None, verbose=False):
        population_sample = self.sample_population(sample_size)
        scores = [
            (self.score_func(node_set, verbose), node_set)
            for node_set in population_sample
        ]
        return sorted(scores, key=lambda s: s[0])

    def print_population(self, lim=10):
        for i in range(len(self.population[:lim])):
            print(i, self.population[i], f":: {self.population[i].display()}")
        print()

    def evolve(
        self,
        pop_size=POP_SIZE,
        max_gen=MAX_GEN,
        mutation_rate=MUTATION_RATE,
        crossover_rate=CROSSOVER_RATE,
        pexp=P_EXP,
        pnew_upper=P_NEW_UPPER,
        pnew_lower=P_NEW_LOWER,
        verbose=DISPLAY_MESSAGES,
    ):
        self.generate_population(pop_size)
        pnew_dec = (pnew_upper - pnew_lower) / max_gen
        pnew = pnew_upper

        for i in range(max_gen):
            scores = self.rank_population()
            if verbose:
                print(i, round(scores[0][0], 4), scores[0][1].display(), round(pnew, 4))
            if scores[0][0] == 0:
                break

            new_pop = [scores[0][1], scores[1][1]]

            while len(new_pop) < pop_size:
                if random() < pnew:
                    new_pop.append(RxNodeSet.random_node_set())
                else:
                    ixs = [
                        GeneticAlgorithm.select_index(len(self.population) - 1)
                        for i in range(2)
                    ]
                    crossed = scores[ixs[0]][1].crossover(
                        scores[ixs[1]][1], crossover_rate
                    )
                    mutated = crossed.mutate(mutation_rate)
                    new_pop.append(mutated)

            if verbose:
                new_scores = self.rank_population()
                for i in range(10):
                    print(
                        "> ", i, round(new_scores[i][0], 4), new_scores[i][1].display()
                    )
                if pop_size > 10:
                    print("...")
                    for i in sorted(
                        list(set([randint(11, pop_size - 1) for _ in range(10)]))
                    ):
                        print(
                            "> ",
                            i,
                            round(new_scores[i][0], 4),
                            new_scores[i][1].display(),
                        )
                print()
            self.population = new_pop
            pnew -= pnew_dec
        print(scores[0][1].display())
        return scores[0][1]


def gen_test_match(regex, char_sets=None, max_tries=10):
    match_found = False
    count = 0
    while not match_found:

        node_set = RxNodeSet.make_node_set(regex)
        formatted = node_set.display()
        res = node_set.compile()
        if res and GeneticAlgorithm.check_match(formatted, res):
            match_found = True
        if count > max_tries:
            raise NotFoundError(f"Could not compile match for regex '{formatted}'")
        count += 1

    return res


def callable_get(obj, *args):
    if callable(obj):
        return obj(*args)
    return obj


def gen_test_no_match(
    prob_alphanum=None, prob_data_format=None, data_format=None, char_sets=None
):

    prob_alphanum = prob_alphanum or 0.5
    prob_data_format = prob_data_format or 0.5

    if not data_format:
        prob_data_format = 0

    if char_sets == RAND:
        char_sets = list(CHAR_SETS.keys())

    use_data_format = random() < prob_data_format
    num_words = GeneticAlgorithm.select_index(MAX_WORDS) + 1
    if random() < prob_alphanum:
        char_set_name = "alphanum"
    else:
        char_set_name = choice(char_sets)

    if use_data_format:
        num_words = callable_get(data_format.get("num_words", None)) or num_words
        char_set_name = callable_get(data_format.get("char_set", None)) or char_set_name

    char_set = CHAR_SETS[char_set_name]
    res = []

    for i in range(num_words):
        num_chars = GeneticAlgorithm.select_index(10) + 1
        if use_data_format:
            num_chars = (
                callable_get(data_format.get("word_length", None), i) or num_chars
            )
        res.append("".join([choice(char_set) for i in range(num_chars)]))

    return " ".join(res)


def gen_test_datum(regex, data_format=None, probabilities=None, char_sets=RAND):

    verification_node_set = RxNodeSet.make_node_set(regex)

    if random() < probabilities.get("match", 0.5):
        res = gen_test_match(regex)
    else:
        res = gen_test_no_match(
            probabilities.get("alphanum"),
            probabilities.get("data_format"),
            data_format,
            char_sets,
        )

    is_match = GeneticAlgorithm.check_match(verification_node_set.display(), res)
    return (res, is_match)


def gen_test_data(regex, rows=10, data_format=None, probabilities=None, char_sets=RAND):
    return [
        gen_test_datum(regex, data_format, probabilities, char_sets=char_sets)
        for i in range(rows)
    ]


rg1_test_data_settings = {
    "data_format": {"num_words": 1, "char_set": "alpha"},
    "rows": 100,
    "probabilities": {"data_format": 1},
    "regex": [
        ["wildcard", "0+"],
        "alpha(f)",
        "alpha(o)",
        "alpha(o)",
        ["wildcard", "0+"],
    ],
}


def postcode_test_data_settings(rows=10):
    out = {}
    out["rows"] = rows
    out["data_format"] = {}
    out["data_format"]["num_words"] = 2
    out["data_format"]["char_set"] = "printable"
    out["data_format"]["word_length"] = lambda i: [randint(3, 4), 3][i]
    out["probabilities"] = {}
    out["probabilities"]["data_format"] = 0.5
    out["probabilities"]["alphanum"] = 0.5
    out["probabilities"]["match"] = 0.5
    out["regex"] = [  # r"[a-zA-Z]{1,2}[0-9Rr][0-9A-Za-z]? [0-9][A-Za-z]{2}"
        [
            "set",
            ["count2", ["int(1)", "int(2)"]],
            [
                ["range", ["alpha(a)", "alpha(z)"]],
                ["range", ["alpha(A)", "alpha(Z)"]],
            ],
        ],
        [
            "set",
            [
                ["range", ["digit(0)", "digit(9)"]],
                "alpha(R)",
                "alpha(r)",
            ],
        ],
        [
            "set",
            "0/1",
            [
                ["range", ["digit(0)", "digit(9)"]],
                ["range", ["alpha(a)", "alpha(z)"]],
                ["range", ["alpha(A)", "alpha(Z)"]],
            ],
        ],
        "space",
        ["set", [["range", ["digit(0)", "digit(9)"]]]],
        [
            "set",
            ["count", ["int(2)"]],
            [
                ["range", ["alpha(a)", "alpha(z)"]],
                ["range", ["alpha(A)", "alpha(Z)"]],
            ],
        ],
    ]
    return out


def get_pct_data_correct(dataset):
    return sum([1 for row in dataset if row[1]]) / len(dataset)


def gen_random_params():
    return {
        "mutation_rate": random(),
        "crossover_rate": random(),
        "pexp": random(),
        "pnew_upper": random(),
        "pnew_lower": random(),
        # "pmodifier": random(),
        # "pextend": random(),
    }


RxType.init_types()
RxWrapper.init_wrappers()


if __name__ == "__main__":
    # node_set_examples = [
    #     [  # r"a|b*"
    #         ["or", ["alphanum(a)", ["alphanum(b)", "0+"]]],
    #     ],
    #     [  # r"[DXQ-p][^c-n]\w\D{4,9}"
    #         [
    #             "set",
    #             [
    #                 "alphanum(D)",
    #                 "alphanum(X)",
    #                 ["range", ["alphanum(Q)", "alphanum(p)"]],
    #             ],
    #         ],
    #         ["!set", [["range", ["alphanum(c)", "alphanum(n)"]]]],
    #         "word",
    #         ["!digit", ["count2", ["num(4)", "num(9)"]]],
    #     ],
    #     [  # r"[a-zA-Z]{1,2}[0-9Rr][0-9A-Za-z]? [0-9][A-Za-z]{2}"
    #         [
    #             "set",
    #             ["count2", ["num(1)", "num(2)"]],
    #             [
    #                 ["range", ["alphanum(a)", "alphanum(z)"]],
    #                 ["range", ["alphanum(A)", "alphanum(Z)"]],
    #             ],
    #         ],
    #         [
    #             "set",
    #             [
    #                 ["range", ["alphanum(0)", "alphanum(9)"]],
    #                 "alphanum(R)",
    #                 "alphanum(r)",
    #             ],
    #         ],
    #         [
    #             "set",
    #             "0/1",
    #             [
    #                 ["range", ["alphanum(0)", "alphanum(9)"]],
    #                 ["range", ["alphanum(a)", "alphanum(z)"]],
    #                 ["range", ["alphanum(A)", "alphanum(Z)"]],
    #             ],
    #         ],
    #         "space",
    #         ["set", [["range", ["alphanum(0)", "alphanum(9)"]]]],
    #         [
    #             "set",
    #             ["count", ["num(2)"]],
    #             [
    #                 ["range", ["alphanum(a)", "alphanum(z)"]],
    #                 ["range", ["alphanum(A)", "alphanum(Z)"]],
    #             ],
    #         ],
    #     ],
    # ]

    # for e in node_set_examples:
    #     ns = RxNodeSet.make_node_set(e)
    #     rgx = ns.display()
    #     s = ns.compile()
    #     print(ns)
    #     print(rgx)
    #     print(s)
    #     print(GeneticAlgorithm.check_match(rgx, s))
    #     print()

    # test_data_set = gen_postcode_test_data(SIZE_DATASET)
    # ga = GeneticAlgorithm(test_data_set)
    # print("pct data correct: ", get_pct_data_correct(test_data_set))
    # ga.evolve()
    total = 0
    correct = 0
    for i in range(100):
        out = []
        res = None
        try:
            r = RxNodeSet.random_node_set(
                omit_types=["mmod"], omit_wrappers=["emptyterm", "emtpy!term"]
            )
            rgx = r.display()
            out.append(r)
            out.append(rgx)
            s = r.compile()
            if s:
                total += 1
                out.append(f"'{s}'")
                res = GeneticAlgorithm.check_match(rgx, s)
        except:
            for debug in out:
                print(debug)
            raise

        out.append(res)
        if res:
            correct += 1
        else:
            for debug in out:
                print(debug)
            print()

        # if not res:
        #     for node in r.nodes:
        #         print("> ", node.re_type)
        #         print("> ", node.modifier)
        #         print("> ", node.children)
        #         print("> ", [c.compile() for c in node.children])
        #         for child in node.children:
        #             print(">> ", child)
        #             print(">> ", child.re_type)
        #             print(">> ", child.modifier)
        #             print(">> ", child.children)
        #             print(">>")
        #         print(">")
        # print()

    print()
    print(correct, total, correct / total)
