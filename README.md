# Regex Evolver

A project for evolving regular expressions.

Additional functionality for generating test sets for evolving a UK postcode regex.

The dataset generator uses the UK postcode regex `[a-zA-Z]{1,2}[0-9Rr][0-9A-Za-z]? [0-9][A-Za-z]{2}` to generate a split of matching and non-matching strings (50-50 by default) for testing.

## Options

### Settings:
- `MAX_GEN`: *Max generations* - The number of generations to run unless a perfect scoring candidate is found
- `POP_SIZE`: *Population size* - Number of instances in each generation
- `SIZE_DATASET`: *Size of dataset* - The number of entries to generate in the dataset

### Parameters:
- `MUTATION_RATE`: *Mutation rate* - Probability of a node in the regex being mutated
- `CROSSOVER_RATE`: *Crossover rate* - Probability of two regexes being spliced together
- `P_NEW_UPPER`: Upper % of new regexes in population
- `P_NEW_LOWER`:Lower % of new regexes in population
- `P_EXP`: (0-1) - Used to calculate random number skewing to low numbers. Higher value - more lower numbers

`P_NEW_UPPER` and `P_NEW_LOWER` determine what percentage of the next generation of regexes should be generated at random, at the beginning and and of the cycle respectively, with a linear descent from upper to lower across the cycle's generations.

## Usage

### To run:

Running file as main will automatically set up and run evolution with default settings and params

### To import and run:

```python
from evolver import *
test_data_set = gen_postcode_test_data(n=100)
ga = GeneticAlgorithm(test_data_set)

# run with default params
ga.evolve()

# alternatively, generate new params
params = gen_random_params()
ga.evolve(**params)

# the best produced candidate is returned by the evolution function
node_set = ga.evolve()
print(node_set.display())
```

Evolution terminates if a perfect score is reached by a candidate.

### To test:

```python
from evolver import *
test_data_set = gen_postcode_test_data(n=100)
ga = GeneticAlgorithm(test_data_set)

# create and test random regex against dataset
node_set = ReNodeSet.random_node_set()
ga.score_func(node_set=node_set, sample_size=10, verbose=True)

# create and test random population of regexes against dataset
ga.generate_population(n=10)
ge.rank_population(verbose=True)

# to test arbitrary regex string against dataset
rs = r''
ga.score_func(sample_size=10, verbose=True, regex_string=rs)
```

## Evolution sample:

```
# Settings: 
    MAX_GEN=500
    POP_SIZE=500
    SIZE_DATASET=300

# Parameters:
    MUTATION_RATE = 0.2
    CROSSOVER_RATE = 0.4
    P_NEW_UPPER = 0.9
    P_NEW_LOWER = 0.6
    P_EXP = 0.7

# Output:
generation, top score (% incorrect), top scoring regex, % new in next generation
0 0.3033 \D\d\d.\S* 0.9
1 0.3033 \D\d\d.\S* 0.8994
2 0.1167 \D\w+\d[^H-V]\S\w??[\W\w%Y-aH]\S 0.8988
3 0.1167 \D\w+\d[^H-V]\S\w??[\W\w%Y-aH]\S 0.8982
4 0.0733 \w+\d[^H-V]\S\w??[\W\w%Y-aH]\S 0.8976
5 0.0433 \w+\d[^H-V]\S\w??\w\D 0.897
6 0.0033 \w+\d[^H-M]\d\w??\w\D 0.8964
7 0.0033 \w+\d[^H-M]\d\w??\w\D 0.8958
8 0.0033 \w+\d[^H-M]\d\w??\w\D 0.8952
9 0.0033 \w+\d[^H-M]\d\w??\w\D 0.8946
10 0.0 \w+\d[^R-h]\d\w??\D\D 0.894

# Evolved Solution: '\w+\d[^R-h]\d\w??\D\D'
```

## Tasks Remaining

[ ]: consolidate tests
[ ]: implement formatted regex (eg for test data generation) generation from node(set)
[X]: separate code into separate files
[ ]: improve comments and documentation
[ ]: implement hyperparameter tuning (10k cross validation)
[ ]: audit missing regex functionalities
[ ]: implement regex assertions (?...)
[ ]: fix greedy modifier
[ ]: nice to have - frontend


## Useful Links

(Regex Golf)[https://alf.nu/RegexGolf]: A handy site for testing and playing with the evolver

(Programming Collective Intelligence)[https://www.amazon.co.uk/Programming-Collective-Intelligence-Building-Applications/dp/0596529325/ref=sr_1_1]: A great book which goes through genetic programming among other interesting algorithms