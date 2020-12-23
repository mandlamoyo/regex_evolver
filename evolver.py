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

# constants
RAND = -1
MAX_WORDS = 5
MAX_CHILDREN = 5
MAX_COMPILE_MUTLIPLE = 5
P_MODIFIER = 0.1
P_EXTEND = 0.76
SUPPRESS_ROOT_CHARS = True
DISPLAY_MESSAGES = True

CHAR_SETS = {
    "alpha_upper": string.ascii_uppercase,
    "alpha_lower": string.ascii_lowercase,
    "alpha": string.ascii_letters,
    "alphanum": string.digits + string.ascii_letters,
    "num": string.digits,
    "printable": string.printable,
}


# Regex wrapper display functions
def d_set(l, invert=False):
    l = [l[0]] + list(filter(lambda child: child.name != "printable(-)", l[1:]))
    display = "".join([v.display() for v in l])
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
    return l[0].display() + "|" + l[1].display()


def d_range(l):
    values = sorted([l[0].display(), l[1].display()])
    return f"{values[0]}-{values[1]}"


def _d(v):
    return lambda: v


# Regex wrapper compile functions
def invert_compile(values, char_set="printable"):
    if not isinstance(values, list):
        values = list(values)
    return choice(list(set(CHAR_SETS[char_set]) - set(values)))


def c_set(l):
    return choice([v.compile() for v in l])


def c_nset(l):
    return invert_compile([v.compile() for v in l])


def c_count(l, compiled):
    return compiled * int(l[0].compile())


def c_count2(l, compiled):
    return compiled * randint(*sorted([int(v.compile()) for v in l]))


def c_or(l):
    return choice([v.compile() for v in l])


def c_range(l):
    return chr(randint(*sorted([ord(v.compile()) for v in l])))


def c_wildcard():
    return choice(CHAR_SETS["printable"])


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
    return choice([" ", "\t", "\n", "\r", "\f", "\v"])


def c_nwhitespace():
    return invert_compile([" ", "\t", "\n", "\r", "\f", "\v"])


def c_empty():
    return ""


def c_decimal():
    return choice(CHAR_SETS["num"])


def c_ndecimal():
    return invert_compile(CHAR_SETS["num"])


def c_word():
    return choice(CHAR_SETS["alphanum"] + "_")


def c_nword():
    return invert_compile(CHAR_SETS["alphanum"] + "_")


# Classes
class ReTypeCollection:
    def __init__(self):
        self.types = {}

    def get(self, name):
        return self.types[name]

    def add(self, re_type):
        self.types[re_type.name] = re_type

    def add_all(self, re_types):
        for re_type in re_types:
            self.add(re_type)


class ReType:
    c = ReTypeCollection()

    @staticmethod
    def init_types():
        ReType.c.add(ReType("re"))
        ReType.c.add(ReType("mod"))
        ReType.c.add(ReType("num", is_modifiable=False))
        ReType.c.add(ReType("range", is_modifiable=False))
        ReType.c.add(ReType("char", ReType.c.get("re")))
        ReType.c.add(ReType("cset", ReType.c.get("re")))
        ReType.c.add(ReType("cset*", ReType.c.get("re"), is_modifiable=False))
        ReType.c.add(ReType("printable", ReType.c.get("char")))
        ReType.c.add(ReType("alphanum", ReType.c.get("printable")))
        ReType.c.add(ReType("mmod", ReType.c.get("mod"), is_modifiable=False))

    def __init__(self, name, parent_retype=None, is_modifiable=True):
        self.name = name
        self.parent = parent_retype
        self.is_modifiable = is_modifiable

    def __repr__(self):
        parent_name = "-"
        if self.parent:
            parent_name = self.parent.name
        return f"T: {self.name} ({parent_name}, mod:{self.is_modifiable})"

    def is_type(self, re_type):
        return self.name == re_type.name or (
            self.parent and self.parent.is_type(re_type)
        )

    def is_type_name(self, type_name):
        if self.parent:
            return self.name == type_name or self.parent.is_type_name(type_name)
        return self.name == type_name


class ReWrapper:
    wrappers = {}

    @staticmethod
    def add_wrapper(regex_wrapper):
        ReWrapper.wrappers[regex_wrapper.name] = regex_wrapper

    @staticmethod
    def add_wrappers(regex_wrappers):
        for wrapper in regex_wrappers:
            ReWrapper.add_wrapper(wrapper)

    @staticmethod
    def get_wrapper(wrapper_name):
        return ReWrapper.wrappers.get(wrapper_name, None)

    @staticmethod
    def wrapper_is_type(wrapper_name, type_name):
        wrapper = ReWrapper.get_wrapper(wrapper_name)
        if not wrapper:
            raise KeyError(f"wrapper {wrapper_name} not found")
        return wrapper.re_type.is_type_name(type_name)

    @staticmethod
    def init_wrappers():
        ReWrapper.wrappers.clear()

        for s in CHAR_SETS["alphanum"]:
            ReWrapper.add_wrapper(ReWrapper(f"alphanum({s})", _d(s), "alphanum"))

        for s in "'!\"£-~#%&@:;<>/,":
            ReWrapper.add_wrapper(ReWrapper(f"printable({s})", _d(s), "printable"))

        for n in "123456789":
            ReWrapper.add_wrapper(ReWrapper(f"num({n})", _d(n), "num"))

        metachars = r".^$*+?{}[]\|()"
        for m in metachars:
            ReWrapper.add_wrapper(
                ReWrapper(f"char({m})", _d(r"\%s" % m), "char", compile_function=_d(m))
            )

        #  display function, it's type(s), the type(s) it takes (opt), number of inputs
        ReWrapper.add_wrappers(
            [
                ReWrapper(
                    "range",
                    d_range,
                    "range",
                    ["alphanum"],
                    2,
                    compile_function=c_range,
                    strip_child_mods=True,
                ),
                ReWrapper(
                    "set",
                    d_set,
                    "re",
                    ["char", "range", "cset"],
                    RAND,
                    compile_function=c_set,
                ),
                ReWrapper(
                    "!set",
                    d_nset,
                    "re",
                    ["char", "range", "cset"],
                    RAND,
                    compile_function=c_nset,
                    strip_child_mods=True,
                ),
                ReWrapper(
                    "count", d_count, "mod", ["num"], 1, compile_function=c_count
                ),
                ReWrapper(
                    "count2", d_count2, "mod", ["num"], 2, compile_function=c_count2
                ),
                ReWrapper(
                    "or",
                    d_or,
                    "re",
                    ["re"],
                    2,
                    compile_function=c_or,
                    is_modifiable=False,
                ),
                ReWrapper("wildcard", _d("."), "re", compile_function=c_wildcard),
                ReWrapper("0+", _d("*"), "mod", compile_function=c_zero_plus),
                ReWrapper("0/1", _d("?"), "mod", compile_function=c_zero_one),
                ReWrapper("1+", _d("+"), "mod", compile_function=c_one_plus),
                ReWrapper("!greedy", _d("?"), "mmod", compile_function=c_not_greedy),
                ReWrapper(
                    "whitespace", _d(r"\s"), "cset", compile_function=c_whitespace
                ),
                ReWrapper(
                    "!whitespace", _d(r"\S"), "cset", compile_function=c_nwhitespace
                ),
                ReWrapper("emptyterm", _d(r"\b"), "cset*", compile_function=c_empty),
                ReWrapper("emtpy!term", _d(r"\B"), "cset*", compile_function=c_empty),
                ReWrapper("decimal", _d(r"\d"), "cset", compile_function=c_decimal),
                ReWrapper("!decimal", _d(r"\D"), "cset", compile_function=c_ndecimal),
                ReWrapper("word", _d(r"\w"), "cset", compile_function=c_word),
                ReWrapper("!word", _d(r"\W"), "cset", compile_function=c_nword),
                ReWrapper("space", _d(r" "), "printable"),
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
    ):
        self.name = name
        self.display_function = display_function
        self.compile_function = compile_function or display_function
        self.child_count = child_count
        self.child_types = child_types
        self.re_type = ReType.c.get(re_type)
        self.is_modifiable = self.re_type.is_modifiable and is_modifiable
        self.strip_child_mods = strip_child_mods

    def __repr__(self):
        return f"RW: {self.name}({self.child_count}, mod:{self.is_modifiable})"

    def get_child_count(self):
        if self.child_count == RAND:
            return randint(1, MAX_CHILDREN)
        return self.child_count


class ReNode:
    @staticmethod
    def make_node(rw_name=None, children=RAND, modifier=None, rw=None, is_child=False):
        """
        children format: [{'rw_name': regex_wrapper_name, 'children': [<children>]})]
        modifier format: {'rw_name': <modifier_name>, 'children': <children>, 'modifier': <modifier>}
        """
        if not rw:
            if not rw_name:
                raise ValueError("must provide regex wrapper object or name")

            rw = ReWrapper.get_wrapper(rw_name)

        child_nodes = []
        if rw.child_count != 0:
            if children == RAND:
                child_nodes = [
                    ReNode.make_random_node(choice(rw.child_types), is_child=True)
                    for i in range(rw.get_child_count())
                ]
            else:
                for child in children:
                    child_nodes.append(ReNode.make_node(**child, is_child=True))

        node = ReNode(rw, child_nodes, is_child)
        if rw.is_modifiable:
            if modifier == RAND:
                print("- ", node.name)
                print("- ", rw.name)
                print("- ", rw.re_type)
                print("- ", rw.re_type.is_type_name("mod"))
                mod_type = "mmod" if rw.re_type.is_type_name("mod") else "mod"
                print("- ", mod_type)
                omit_types = ["mmod"] if mod_type == "mod" else []
                modifier = ReNode.make_random_node(mod_type, omit_types=omit_types)
                print("-- ", modifier)
            elif modifier:
                modifier = ReNode.make_node(**modifier)
            node.set_modifier(modifier)

        return node

    @staticmethod
    def make_random_node(
        type_name="re",
        is_child=False,
        prob_modifier=P_MODIFIER,
        omit_types=None,
        omit_wrappers=None,
    ):
        omit_types = omit_types or []
        omit_wrappers = omit_wrappers or []
        re_type = ReType.c.get(type_name)
        if not is_child and SUPPRESS_ROOT_CHARS:
            omit_types.append("char")

        # filter ReWrapper.wrappers with items that match re_type
        filtered_wrappers = list(
            filter(lambda rw: rw.re_type.is_type(re_type), ReWrapper.wrappers.values())
        )

        for omit in omit_types:
            omit_type = ReType.c.get(omit)
            filtered_wrappers = list(
                filter(lambda rw: not rw.re_type.is_type(omit_type), filtered_wrappers)
            )

        for omit in omit_wrappers:
            filtered_wrappers = list(
                filter(lambda rw: rw.name != omit, filtered_wrappers)
            )

        rw = choice(filtered_wrappers)
        modifier = None
        if rw.is_modifiable and random() < prob_modifier:
            modifier = RAND

        return ReNode.make_node(rw=rw, modifier=modifier, is_child=is_child)

    def __init__(self, rw, children, is_child):
        self.next = None
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
            return ReNode.make_random_node(
                type_name=self.re_type.name, is_child=self.is_child
            )
        else:
            new_children = []
            for child in self.children:
                new_children.append(child.mutate())

            new_node = deepcopy(self)
            new_node.children = new_children
            return new_node


class ReNodeSet:
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
                if ReWrapper.wrapper_is_type(first_nested(n), "mod"):
                    node["modifier"] = format_node(n)

                else:
                    node["children"] = [format_node(child) for child in n]

            return node

        formatted_node_info = [format_node(n) for n in regex_node_set_info]
        return ReNodeSet([ReNode.make_node(**fn) for fn in formatted_node_info])

    @staticmethod
    def random_node_set(prob_extend=P_EXTEND, omit_types=None, omit_wrappers=None):
        nodes = [
            ReNode.make_random_node(omit_types=omit_types, omit_wrappers=omit_wrappers)
        ]
        while random() < prob_extend:
            nodes.append(
                ReNode.make_random_node(
                    omit_types=omit_types, omit_wrappers=omit_wrappers
                )
            )
        return ReNodeSet(nodes)

    def __init__(self, nodes):
        self.nodes = nodes

    def __repr__(self):
        return ", ".join([str(node) for node in self.nodes])

    def display(self):
        return "".join([node.display() for node in self.nodes])

    def compile(self):
        return "".join([node.compile() for node in self.nodes])

    def mutate(self, prob_change):
        new_nodes = [node.mutate(prob_change) for node in self.nodes]
        if random() < prob_change:
            ix = randint(0, len(new_nodes) - 1)
            if random() < 0.5 and len(new_nodes) > 1:
                new_nodes = new_nodes[:ix] + new_nodes[ix + 1 :]
            else:
                new_nodes = (
                    new_nodes[:ix] + [ReNode.make_random_node()] + new_nodes[ix:]
                )
        return ReNodeSet(new_nodes)

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
        return ReNodeSet([deepcopy(node) for node in new_nodes])


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
        self.population = [ReNodeSet.random_node_set() for _ in range(n)]

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
                    new_pop.append(ReNodeSet.random_node_set())
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


def gen_test_match(regex):
    pc = choice(CHAR_SETS["alpha"])
    if random() < 0.5:
        pc += choice(CHAR_SETS["alpha"])
    pc += choice(CHAR_SETS["num"])
    if random() < 0.5:
        pc += choice(CHAR_SETS["num"])
    pc += (
        " "
        + choice(CHAR_SETS["num"])
        + choice(CHAR_SETS["alpha"])
        + choice(CHAR_SETS["alpha"])
    )
    return pc


def gen_test_no_match(num_words, chars, prob_alphanum=0.5, prob_rightsize=0.5):
    if random() < prob_alphanum:
        chars = "alphanum"
    rightsize = random() < prob_rightsize

    char_set = CHAR_SETS[chars]
    if num_words == RAND:
        num_words = GeneticAlgorithm.select_index(MAX_WORDS) + 1

    res = []
    if rightsize:
        num_words = 2
    for n in range(num_words):
        if rightsize:
            num_chars = [randint(3, 4), 3][n]
        else:
            num_chars = GeneticAlgorithm.select_index(10) + 1
        res.append("".join([choice(char_set) for i in range(num_chars)]))
    return " ".join(res)


def gen_test_datum(
    regex_names, data_format, probabilities=None, char_set="printable", words=RAND
):
    probabilities = probabilities or {"data_format": 0.5, "alphanum": 0.5, "match": 0.5}
    verification_node_set = ReNodeSet.make_node_set(regex_names)

    if random() < probabilities["match"]:
        res = gen_test_match(regex_names)
    else:
        res = gen_test_no_match(words, char_set)

    is_match = GeneticAlgorithm.check_match(verification_node_set.display(), res)
    return (res, is_match)


def gen_test_data(
    regex_names, size=10, data_format=None, probabilities=None, char_sets=RAND
):
    if char_sets == RAND:
        char_sets = list(CHAR_SETS.keys())

    return [
        gen_test_datum(
            regex_names, data_format, probabilities, char_set=choice(char_sets)
        )
        for i in range(size)
    ]


def postcode_test_data_settings(size=10):
    out = {}
    out["size"] = size
    out["data_format"] = {}
    out["data_format"]["num_words"] = 2
    out["data_format"]["char_set"] = "printable"
    out["data_format"]["word_length"] = lambda: [randint(3, 4), 3]
    out["probabilities"]["data_format"] = 0.5
    out["probabilities"]["alphanum"] = 0.5
    out["probabilities"]["match"] = 0.5
    out["regex_names"] = r"[a-zA-Z]{1,2}[0-9Rr][0-9A-Za-z]? [0-9][A-Za-z]{2}"
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
    }


ReType.init_types()
ReWrapper.init_wrappers()


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
    #         ["!decimal", ["count2", ["num(4)", "num(9)"]]],
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
    #     ns = ReNodeSet.make_node_set(e)
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

    for i in range(10):
        r = ReNodeSet.random_node_set(omit_wrappers=["emptyterm", "emtpy!term"])
        rgx = r.display()
        print(r)
        print(rgx)
        s = r.compile()
        print(s)
        res = GeneticAlgorithm.check_match(rgx, s)
        print(res)
        if not res:
            for node in r.nodes:
                print("> ", node.re_type)
                print("> ", node.modifier)
                print("> ", node.children)
                print("> ", [c.compile() for c in node.children])
                for child in node.children:
                    print(">> ", child)
                    print(">> ", child.re_type)
                    print(">> ", child.modifier)
                    print(">> ", child.children)
                    print(">>")
                print(">")
        print()
