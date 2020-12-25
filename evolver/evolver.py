from random import random, randint, sample
from math import log
import string
import csv
import re

from evolver.node import RxNodeSetFactory

from evolver.config import (
    POP_SIZE,
    MAX_GEN,
    MUTATION_RATE,
    CROSSOVER_RATE,
    P_EXP,
    P_NEW_UPPER,
    P_NEW_LOWER,
    DISPLAY_MESSAGES,
)


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
        self.node_set_factory = RxNodeSetFactory.instance()

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
        self.population = [self.node_set_factory.random_node_set() for _ in range(n)]

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
                    new_pop.append(self.node_set_factory.random_node_set())
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