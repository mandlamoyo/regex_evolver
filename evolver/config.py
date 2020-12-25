import string
from typing import Dict


##### Parameters #####

# default probability of node mutation
MUTATION_RATE: float = 0.2

# default probability of crossover of two nodesets
CROSSOVER_RATE: float = 0.4

# initial % of regexes in population that should be randomly generated after scoring
P_NEW_UPPER: float = 0.9

# final % of regexes in population that should be randomly generated after scoring
P_NEW_LOWER: float = 0.6

# used to calculate random number skewing to low numbers. Higher value - more lower numbers
P_EXP: float = 0.7

# default probability of a modifier being generated during random regex creation
P_MODIFIER: float = 0.1

# default probability of a additional node being added during random node set creation
P_EXTEND: float = 0.76


##### Settings #####

# default number of generations to run evolution unless perfect candidate found
MAX_GEN: int = 500

# default population size
POP_SIZE: int = 500

# default number of rows to generate in dataset
SIZE_DATASET: int = 300

# maximum number of words that can be generated in a testing data item
MAX_WORDS: int = 5

# maximum number of children to be generated in a regex node (eg set)
MAX_CHILDREN: int = 5

# maximum times regex modifiers (*, ?, +, {}) can multiply characters on compilation
MAX_COMPILE_MUTLIPLE: int = 5

# wildcard matches newlines
DOT_ALL: bool = False

# prevents character constants from being generated as node children
SUPPRESS_ROOT_CHARS: bool = True

# enables message output during evolution
DISPLAY_MESSAGES: bool = True


##### Constants #####
RAND: int = -1

# character sets
WHITESPACE_CHARS: str = string.whitespace  # [" ", "\t", "\n", "\r", "\f", "\v"]
NON_META_SYMBOL_CHARS: str = "'!\"£-~#%&@:;<>/,"
META_CHARS: str = r".^$*+?{}[]\|()\\"
CHAR_SETS: Dict[str, str] = {
    "alpha_upper": string.ascii_uppercase,
    "alpha_lower": string.ascii_lowercase,
    "alpha": string.ascii_letters,
    "alphanum": string.digits + string.ascii_letters,
    "digit": string.digits,
    "printable": string.printable,
}
