from random import random, randint, choice, sample
from copy import deepcopy
from math import log
import string
import re


# constants
RAND = -1
MAX_WORDS = 5
MAX_CHILDREN = 5
CHANCE_MODIFIER = 0.1
CHANCE_EXTEND = 0.76
SUPPRESS_ROOT_CHARS = True
DISPLAY_MESSAGES = True

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

CHAR_SETS = {
    "alpha_upper": string.ascii_uppercase,
    "alpha_lower": string.ascii_lowercase,
    "alpha": string.ascii_letters,
    "alphanum": string.digits + string.ascii_letters,
    "num": string.digits,
    "printable": string.printable,
}


class ReType:
    def __init__(self, name, parent_retype=None, is_modifiable=True):
        self.name = name
        self.parent = parent_retype
        self.is_modifiable = is_modifiable

    def __repr__(self):
        parent_name = "-"
        if self.parent:
            parent_name = self.parent.name
        return f"T: {self.name} ({parent_name}, {self.is_modifiable})"

    def is_type(self, re_type):
        return self.name == re_type.name or (
            self.parent and self.parent.is_type(re_type)
        )

    def is_type_name(self, type_name):
        return self.name == type_name or (
            self.parent and self.parent.is_type_name(type_name)
        )


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


class ReWrapper:
    t = ReTypeCollection()

    def __init__(self, name, display_function, re_type, child_types=None, childcount=0):
        self.name = name
        self.display_function = display_function
        self.childcount = childcount
        self.child_types = child_types
        self.re_type = ReWrapper.t.get(re_type)

    def __repr__(self):
        return f"RW: {self.name} - {self.childcount} {self.get_childcount()}"

    def get_childcount(self):
        if self.childcount == RAND:
            return randint(1, MAX_CHILDREN)
        return self.childcount


class ReNode:
    @staticmethod
    def make_random_node(
        type_name="re", mpr=CHANCE_MODIFIER, omit=None, is_child=False
    ):
        re_type = ReWrapper.t.get(type_name)
        if not is_child and SUPPRESS_ROOT_CHARS:
            omit = "char"

        # filter rw_list with items that match re_type
        filtered_rw_list = list(filter(lambda rw: rw.re_type.is_type(re_type), rw_list))
        if omit:
            omit_type = ReWrapper.t.get(omit)
            filtered_rw_list = list(
                filter(lambda rw: not rw.re_type.is_type(omit_type), filtered_rw_list)
            )
        rw = choice(filtered_rw_list)

        # create node of correct type
        children = [
            ReNode.make_random_node(choice(rw.child_types), is_child=True)
            for i in range(rw.get_childcount())
        ]
        node = ReNode(rw, children, is_child)

        if rw.re_type.is_modifiable and random() < mpr:
            mod_type = "mmod" if type_name == "mod" else "mod"
            modifier = ReNode.make_random_node(mod_type)
            node.set_modifier(modifier)

        return node

    def __init__(self, rw, children, is_child):
        self.next = None
        self.name = rw.name
        self.modifier = None
        self.assertion = None
        self.children = children
        self.re_type = rw.re_type
        self.display_function = rw.display_function
        self.is_child = is_child

    def __repr__(self):
        if self.children:
            return f"{self.name}{str(self.children)}"
        return f"{self.name}"  # :: {self.display_function()}'

    def set_assertion(self, assertion):
        self.assertion = assertion

    def set_modifier(self, modifier):
        self.modifier = modifier

    def set_next(self, node):
        self.next = node

    def display(self, strip_mod=False):
        out = ""

        if self.assertion and not strip_mod:
            out += self.assertion.display()

        if self.children:
            out += self.display_function(self.children)
            if self.trailing_non_modifiable(self.children[-1]):
                strip_mod = True
        else:
            out += self.display_function()
        # print('- ', self.name, self.re_type)

        if self.modifier and not strip_mod:
            out += self.modifier.display()

        if self.next:
            out += self.next.display()

        return out

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

    def trailing_non_modifiable(self, child):
        if child.modifier:
            return True
        if child.re_type.is_type_name("mod"):
            return True
        if not child.re_type.is_modifiable:
            return True
        if child.children and self.trailing_non_modifiable(child.children[-1]):
            return True
        return False


class ReNodeSet:
    @staticmethod
    def random_node_set(epr=CHANCE_EXTEND, omit=None):
        nodes = [ReNode.make_random_node(omit=omit)]
        while random() < epr:
            nodes.append(ReNode.make_random_node(omit=omit))
        return ReNodeSet(nodes)

    def __init__(self, nodes):
        self.nodes = nodes

    def __repr__(self):
        return ", ".join([str(node) for node in self.nodes])

    def display(self):
        return "".join([node.display() for node in self.nodes])

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
        self.dataset = None
        self.load_data(dataset)

    def load_data(self, dataset):
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

            self.population = new_pop
            pnew -= pnew_dec
        print(scores[0][1].display())
        return scores[0][1]


rw_list = []
ReWrapper.t.add(ReType("re"))
ReWrapper.t.add(ReType("mod"))
ReWrapper.t.add(ReType("num", is_modifiable=False))
ReWrapper.t.add(ReType("range", is_modifiable=False))
ReWrapper.t.add(ReType("char", ReWrapper.t.get("re")))
ReWrapper.t.add(ReType("cset", ReWrapper.t.get("re")))
ReWrapper.t.add(ReType("cset_nonmod", ReWrapper.t.get("re"), is_modifiable=False))
ReWrapper.t.add(ReType("printable", ReWrapper.t.get("char")))
ReWrapper.t.add(ReType("alphanum", ReWrapper.t.get("printable")))
ReWrapper.t.add(ReType("mmod", ReWrapper.t.get("mod"), is_modifiable=False))


def d_set(l, invert=False):
    l = [l[0]] + list(filter(lambda child: child.name != "printable(-)", l[1:]))
    display = "".join([v.display(strip_mod=True) for v in l])
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
    values = sorted([l[0].display(strip_mod=True), l[1].display(strip_mod=True)])
    return f"{values[0]}-{values[1]}"


def _d(v):
    return lambda: v


for s in string.printable[:62]:
    rw_list.append(ReWrapper(f"alphanum({s})", _d(s), "alphanum"))

for s in "'!\"£-~#%&@:;<>/,":
    rw_list.append(ReWrapper(f"printable({s})", _d(s), "printable"))

for n in "123456789":
    rw_list.append(ReWrapper(f"num({n})", _d(n), "num"))

metachars = r".^$*+?{}[]\|()"
for m in metachars:
    rw_list.append(ReWrapper(f"char({m})", _d(r"\%s" % m), "char"))

#  display function, it's type(s), the type(s) it takes (opt), number of inputs
rangew = ReWrapper("range", d_range, "range", ["alphanum"], 2)
setw = ReWrapper("set", d_set, "re", ["char", "range", "cset"], RAND)
nsetw = ReWrapper("!set", d_nset, "re", ["char", "range", "cset"], RAND)
countw = ReWrapper("count", d_count, "mod", ["num"], 1)
count2w = ReWrapper("count2", d_count2, "mod", ["num"], 2)
orw = ReWrapper("or", d_or, "re", ["re"], 2)
wildw = ReWrapper("wildcard", _d("."), "re")
zeroplusw = ReWrapper("0+", _d("*"), "mod")
zeroonew = ReWrapper("0/1", _d("?"), "mod")
oneplusw = ReWrapper("1+", _d("+"), "mod")
ngreedw = ReWrapper("!greedy", _d("?"), "mmod")
wspw = ReWrapper("whitespace", _d(r"\s"), "cset")
nwspw = ReWrapper("!whitespace", _d(r"\S"), "cset")
empstw = ReWrapper("emptyterm", _d(r"\b"), "cset_nonmod")
empnstw = ReWrapper("emtpy!term", _d(r"\B"), "cset_nonmod")
decw = ReWrapper("decimal", _d(r"\d"), "cset")
ndecw = ReWrapper("!decimal", _d(r"\D"), "cset")
wordw = ReWrapper("word", _d(r"\w"), "cset")
nwordw = ReWrapper("!word", _d(r"\W"), "cset")

rw_list.extend(
    [
        rangew,
        setw,
        nsetw,
        countw,
        count2w,
        orw,
        wildw,
        zeroplusw,
        zeroonew,
        oneplusw,
        ngreedw,
        wspw,
        nwspw,
        empstw,
        empnstw,
        decw,
        ndecw,
        wordw,
        nwordw,
    ]
)


def gen_postcode_test_match():
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


def gen_postcode_test_no_match(num_words, chars, prob_alphanum=0.5, prob_rightsize=0.5):
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


def gen_postcode_test_datum(prob_match, chars="printable", words=RAND):
    if random() < prob_match:
        res = gen_postcode_test_match()
    else:
        res = gen_postcode_test_no_match(words, chars)

    postcode_re = r"[a-zA-Z]{1,2}[0-9Rr][0-9A-Za-z]? [0-9][A-Za-z]{2}"
    is_postcode = GeneticAlgorithm.check_match(postcode_re, res)
    return (res, is_postcode)


def gen_postcode_test_data(n=1, prob_match=0.5, char_set=RAND):
    if char_set == RAND:
        char_set = list(CHAR_SETS.keys())
    else:
        char_set = [char_set]
    return [
        gen_postcode_test_datum(prob_match, chars=choice(char_set)) for i in range(n)
    ]


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


if __name__ == "__main__":
    test_data_set = gen_postcode_test_data(SIZE_DATASET)
    ga = GeneticAlgorithm(test_data_set)
    print("pct data correct: ", get_pct_data_correct(test_data_set))
    ga.evolve()