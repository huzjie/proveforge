# -*- coding: utf-8 -*-
"""Minimal pure-Python linear algebra helpers (lists, no numpy)."""
from __future__ import annotations

import math


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def add(a, b):
    return [x + y for x, y in zip(a, b)]


def sub(a, b):
    return [x - y for x, y in zip(a, b)]


def scale(a, c):
    return [x * c for x in a]


def norm(a):
    return math.sqrt(sum(x * x for x in a))


def normalize(a):
    n = norm(a)
    if n == 0.0:
        return [0.0] * len(a)
    return [x / n for x in a]


def cosine(a, b):
    na, nb = norm(a), norm(b)
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot(a, b) / (na * nb)


def softmax(xs):
    m = max(xs)
    e = [math.exp(x - m) for x in xs]
    s = sum(e)
    return [v / s for v in e]


def matvec(W, x):
    """Matrix (rows) times vector -> vector. W is a list of rows."""
    return [dot(row, x) for row in W]


def mean_pool(vectors):
    if not vectors:
        return []
    n = len(vectors[0])
    return [sum(v[i] for v in vectors) / len(vectors) for i in range(n)]
