from random import random, randint, sample, choice
from typing import Any, Sequence, Optional, List, Tuple
from math import log
import string
import csv
import re

from evolver.nodes import RxNodeSetFactory
from evolver.exceptions import NotFoundError

from evolver.helpers import (
    safe_sample,
    select_index,
    check_match,
    callable_get,
)

from evolver.config import (
    POP_SIZE,
    MAX_GEN,
    MUTATION_RATE,
    CROSSOVER_RATE,
    P_EXP,
    P_NEW_UPPER,
    P_NEW_LOWER,
    DISPLAY_MESSAGES,
    CHAR_SETS,
    RAND,
    MAX_WORDS,
)

Dataset_Row = Tuple[str, bool]
Dataset = Sequence[Dataset_Row]


class RxEvolver:
    def __init__(self, dataset: Optional[Dataset] = None) -> None:
        self._population: Sequence["RxNodeSet"] = []
        self._dataset: Dataset = dataset
        self._rxnode_set_factory: RxNodeSetFactory = RxNodeSetFactory()

    def generate_population(self, size: Optional[int] = 10) -> None:
        self._population = [
            self._rxnode_set_factory.random_node_set() for _ in range(size)
        ]

    def sample_dataset(self, size: int = None) -> List[Tuple[str, bool]]:
        return safe_sample(self._dataset, size)

    def sample_population(self, size: int = None) -> List["RxNodeSet"]:
        return safe_sample(self._population, size)

    def score_func(
        self,
        node_set: Optional["RxNodeSet"] = None,
        sample_size: Optional[int] = None,
        verbose: Optional[bool] = False,
        regex_string: Optional[str] = None,
    ) -> float:
        correct = 0
        if not regex_string:
            if not node_set:
                return 1
            regex_string = node_set.display()

        if verbose:
            print("> [regex] [test_string] [expected] [actual]")
        dataset = self.sample_dataset(sample_size)
        for row in dataset:
            res = check_match(regex_string, row[0])
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

    def rank_population(
        self, sample_size: Optional[int] = None, verbose: Optional[bool] = False
    ) -> Sequence[Tuple[float, "RxNodeSet"]]:
        population_sample = self.sample_population(sample_size)
        scores = [
            (self.score_func(node_set, verbose), node_set)
            for node_set in population_sample
        ]
        return sorted(scores, key=lambda s: s[0])

    def print_population(self, lim: Optional[int] = 10) -> None:
        for i in range(len(self._population[:lim])):
            print(i, self._population[i], f":: {self._population[i].display()}")
        print()

    def evolve(
        self,
        pop_size: Optional[int] = POP_SIZE,
        max_gen: Optional[int] = MAX_GEN,
        mutation_rate: Optional[float] = MUTATION_RATE,
        crossover_rate: Optional[float] = CROSSOVER_RATE,
        pexp: Optional[float] = P_EXP,
        pnew_upper: Optional[float] = P_NEW_UPPER,
        pnew_lower: Optional[float] = P_NEW_LOWER,
        verbose: Optional[bool] = DISPLAY_MESSAGES,
    ) -> "RxNodeSet":
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
                    new_pop.append(self._rxnode_set_factory.random_node_set())
                else:
                    ixs = [select_index(len(self._population) - 1) for i in range(2)]
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
            self._population = new_pop
            pnew -= pnew_dec
        print(scores[0][1].display())
        return scores[0][1]


class RxDataGen:
    def __init__(self, settings=None):
        self._rxnode_set_factory: RxNodeSetFactory = RxNodeSetFactory()
        self._data_settings = settings
        self._dataset = []

    def export(self):
        return self._dataset

    def reset(self):
        self._dataset = []

    def apply_settings(self, settings):
        self._data_settings = settings

    def load_data(
        self,
        dataset: Optional[Sequence[Tuple[str, bool]]] = None,
        filepath: Optional[str] = None,
        delimiter: Optional[str] = ",",
        quotechar: Optional[str] = "|",
    ) -> None:
        if not dataset:
            if not filepath:
                raise ValueError("must provide dataset or filepath")

            dataset = []
            with open(filepath, newline="") as f:
                csvreader = csv.reader(f, delimiter=delimiter, quotechar=quotechar)
                for row in csvreader:
                    dataset.append((row[0], row[1].strip().lower() in ["true", "t"]))

        self._dataset.extend(dataset)

    def gen_test_match(self, regex, char_sets=None, max_tries=10):
        match_found = False
        count = 0
        while not match_found:

            node_set = self._rxnode_set_factory.make_node_set(regex)
            formatted = node_set.display()
            res = node_set.compile()
            if res and check_match(formatted, res):
                match_found = True
            if count > max_tries:
                raise NotFoundError(f"Could not compile match for regex '{formatted}'")
            count += 1

        return res

    def gen_test_no_match(
        self,
        prob_alphanum=None,
        prob_data_format=None,
        data_format=None,
        char_sets=None,
    ):

        prob_alphanum = prob_alphanum or 0.5
        prob_data_format = prob_data_format or 0.5

        if not data_format:
            prob_data_format = 0

        if char_sets == RAND:
            char_sets = list(CHAR_SETS.keys())

        use_data_format = random() < prob_data_format
        num_words = select_index(MAX_WORDS) + 1
        if random() < prob_alphanum:
            char_set_name = "alphanum"
        else:
            char_set_name = choice(char_sets)

        if use_data_format:
            num_words = callable_get(data_format.get("num_words", None)) or num_words
            char_set_name = (
                callable_get(data_format.get("char_set", None)) or char_set_name
            )

        char_set = CHAR_SETS[char_set_name]
        res = []

        for i in range(num_words):
            num_chars = select_index(10) + 1
            if use_data_format:
                num_chars = (
                    callable_get(data_format.get("word_length", None), i) or num_chars
                )
            res.append("".join([choice(char_set) for i in range(num_chars)]))

        return " ".join(res)

    def gen_test_datum(
        self, regex, data_format=None, probabilities=None, char_sets=RAND
    ):

        verification_node_set = self._rxnode_set_factory.make_node_set(regex)

        if random() < probabilities.get("match", 0.5):
            res = self.gen_test_match(regex)
        else:
            res = self.gen_test_no_match(
                probabilities.get("alphanum"),
                probabilities.get("data_format"),
                data_format,
                char_sets,
            )

        is_match = check_match(verification_node_set.display(), res)
        return (res, is_match)

    def gen_test_data(
        self, regex, rows=10, data_format=None, probabilities=None, char_sets=RAND
    ):
        return [
            self.gen_test_datum(regex, data_format, probabilities, char_sets=char_sets)
            for i in range(rows)
        ]

    def get_pct_data_correct(self):
        return sum([1 for row in self._dataset if row[1]]) / len(self._dataset)
