from __future__ import annotations
from typing import Any, Callable, Union, Optional, Sequence, List, Tuple
from math import log
from random import random, sample
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