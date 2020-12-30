from __future__ import annotations
from typing import Any, Callable, Union, Optional, Sequence, List, Tuple
from math import log
from random import random, randint, sample
import csv
import re


def _d(value: str) -> Callable[[Any], str]:
    return lambda node: value


def first_nested(values: Union[Any, List[Any]]):
    if not values:
        raise ValueError("list is empty")

    if isinstance(values, list):
        return first_nested(values[0])
    return values


def select_index(limit: int, pexp: float = 0.7) -> int:
    return min(int(log(random()) / log(pexp)), limit)


def check_match(pattern: str, comparator: str) -> bool:
    m = re.fullmatch(pattern, comparator)
    return m is not None


def callable_get(obj, *args):
    if callable(obj):
        return obj(*args)
    return obj


def safe_sample(collection: Sequence[Any], size: Optional[int] = None) -> Sequence[Any]:
    if size and size <= len(collection):
        return sample(collection, size)
    return collection


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