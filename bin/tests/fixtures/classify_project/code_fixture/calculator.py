"""calculator.py -- minimal arithmetic module for the Code classifier fixture.

The fixture exists so the v1.5.3 project-type classifier has a known-Code
target to point at in tests. The intent is "looks like a tiny but real
code project" -- enough non-blank LOC across enough files that the
heuristic lands on Code with high confidence (>= 50 non-blank lines per
SMALL_PROJECT_LOC_THRESHOLD in classify_project.py).
"""

from __future__ import annotations

from typing import Iterable


def add(a: float, b: float) -> float:
    return a + b


def subtract(a: float, b: float) -> float:
    return a - b


def multiply(a: float, b: float) -> float:
    return a * b


def divide(a: float, b: float) -> float:
    if b == 0:
        raise ZeroDivisionError("denominator must be non-zero")
    return a / b


def sum_all(values: Iterable[float]) -> float:
    total = 0.0
    for v in values:
        total = add(total, v)
    return total


def product_all(values: Iterable[float]) -> float:
    total = 1.0
    for v in values:
        total = multiply(total, v)
    return total


def mean(values: Iterable[float]) -> float:
    items = list(values)
    if not items:
        raise ValueError("cannot take mean of empty iterable")
    return divide(sum_all(items), float(len(items)))


def variance(values: Iterable[float]) -> float:
    items = list(values)
    if len(items) < 2:
        raise ValueError("variance requires at least two values")
    mu = mean(items)
    squared_deviations = [multiply(subtract(x, mu), subtract(x, mu)) for x in items]
    return divide(sum_all(squared_deviations), float(len(items) - 1))


class RunningStats:
    def __init__(self) -> None:
        self._n = 0
        self._sum = 0.0
        self._sum_sq = 0.0

    def push(self, value: float) -> None:
        self._n += 1
        self._sum = add(self._sum, value)
        self._sum_sq = add(self._sum_sq, multiply(value, value))

    @property
    def count(self) -> int:
        return self._n

    @property
    def mean(self) -> float:
        if self._n == 0:
            raise ValueError("mean undefined on zero observations")
        return divide(self._sum, float(self._n))

    @property
    def variance(self) -> float:
        if self._n < 2:
            raise ValueError("variance undefined on fewer than two observations")
        n = float(self._n)
        mean_sq = multiply(self.mean, self.mean)
        return divide(subtract(self._sum_sq, multiply(n, mean_sq)), n - 1.0)
