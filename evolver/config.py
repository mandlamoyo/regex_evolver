import string
from typing import Mapping, Union, Sequence, Dict, List, Tuple


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


##### Types #####

# User-centric succinct template for specifying regex components
RxSpec = List[Union[str, "RxSpec", List["RxSpec"]]]

# Intermediate verbose template used for generating nodes
NodeSpec = Mapping[str, Union[str, "NodeSpec", List["NodeSpec"]]]

# Dataset type definitions
DatasetRow = Tuple[str, bool]
Dataset = List[DatasetRow]

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

# RxWrapper settings
SettingInstance = Dict[str, Union[int, str, bool, List[str]]]

RXWRAPPER_SYMBOL_KEY: Dict[str, str] = {
    "!": "n",
    "+": "_plus",
    "0": "zero",
    "1": "one",
    "/": "_",
}

RXTYPE_SETTINGS: List[dict] = [
    {"name": "re"},
    {"name": "mod"},
    {"name": "integer", "is_modifiable": False},
    {"name": "range", "is_modifiable": False},
    {"name": "cset", "parent_name": "re"},
    {"name": "cset*", "parent_name": "re"},
    {"name": "printable", "parent_name": "re"},
    {"name": "alphanum", "parent_name": "printable"},
    {"name": "digit", "parent_name": "alphanum"},
    {"name": "alpha", "parent_name": "alphanum"},
    {"name": "alpha_upper", "parent_name": "alpha"},
    {"name": "alpha_lower", "parent_name": "alpha"},
    {"name": "mmod", "parent_name": "mod", "is_modifiable": False},
]

RXWRAPPER_SETTINGS: List[dict] = [
    # DEFAULT VALUES
    # {
    #     "name": N/A
    #     "display_function_name": "d_{display_value}()" or "d_{name}()" or "d_()"
    #     "display_value": None
    #     "rxtype_name": "{name}"
    #     "child_types": None
    #     "child_count": 0
    #     "is_modifiable": True
    #     "compile_function_name": "c_{compile_function}()" or "c_{name}()"
    #     "strip_child_mods": False
    #     "uniform_child_types": False
    # },
    {
        "name": "digit",
        "is_char_set": True,
    },
    {
        "name": "alpha",
        "rxtype_name": "alpha_upper",
        "is_char_set": True,
    },
    {
        "name": "alpha",
        "rxtype_name": "alpha_lower",
        "is_char_set": True,
    },
    {
        "name": "printable",
        "is_char_set": True,
        "char_set": NON_META_SYMBOL_CHARS,
    },
    {
        "name": "printable",
        "display_value": r"\{}",
        "is_char_set": True,
        "char_set": META_CHARS,
    },
    {
        "name": "int",
        "rxtype_name": "integer",
        "is_char_set": True,
        "char_set": CHAR_SETS["digit"],
    },
    {
        "name": "range",
        "child_types": ["digit", "alpha_upper", "alpha_lower"],
        "child_count": 2,
        "is_modifiable": False,
        "strip_child_mods": True,
        "uniform_child_types": True,
    },
    {
        "name": "set",
        "rxtype_name": "re",
        "child_types": ["printable", "range", "cset"],
        "child_count": RAND,
        "strip_child_mods": True,
    },
    {
        "name": "!set",
        "rxtype_name": "re",
        "child_types": ["printable", "range", "cset"],
        "child_count": RAND,
        "strip_child_mods": True,
    },
    {
        "name": "count",
        "rxtype_name": "mod",
        "child_types": ["integer"],
        "child_count": 1,
    },
    {
        "name": "count2",
        "rxtype_name": "mod",
        "child_types": ["integer"],
        "child_count": 2,
    },
    {
        "name": "or",
        "rxtype_name": "re",
        "child_types": ["re"],
        "child_count": 2,
        "is_modifiable": False,
    },
    {
        "name": "wildcard",
        "display_value": ".",
        "rxtype_name": "re",
    },
    {
        "name": "0+",
        "display_value": "*",
        "rxtype_name": "mod",
    },
    {
        "name": "0/1",
        "display_value": "?",
        "rxtype_name": "mod",
    },
    {
        "name": "1+",
        "display_value": "+",
        "rxtype_name": "mod",
    },
    {
        "name": "!greedy",
        "display_value": "?",
        "rxtype_name": "mmod",
        "is_modifiable": False,
    },
    {
        "name": "whitespace",
        "display_value": r"\s",
        "rxtype_name": "cset",
    },
    {
        "name": "!whitespace",
        "display_value": r"\S",
        "rxtype_name": "cset",
    },
    {
        "name": "emptyterm",
        "display_value": r"\b",
        "rxtype_name": "cset*",
    },
    {
        "name": "empty!term",
        "display_value": r"\B",
        "rxtype_name": "cset*",
        "compile_function_name": "emptyterm",
    },
    {
        "name": "digit",
        "display_value": r"\d",
        "rxtype_name": "cset",
    },
    {
        "name": "!digit",
        "display_value": r"\D",
        "rxtype_name": "cset",
    },
    {
        "name": "word",
        "display_value": r"\w",
        "rxtype_name": "cset",
    },
    {
        "name": "!word",
        "display_value": r"\W",
        "rxtype_name": "cset",
    },
    {
        "name": "space",
        "display_value": " ",
        "rxtype_name": "printable",
    },
]
