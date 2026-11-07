# -*- coding: utf-8 -*-
"""Utility helpers: deterministic rng, hashing, minimal yaml subset, linear algebra."""
from __future__ import annotations

from .rng import stable_rand, stable_float, stable_int, stable_vector, stable_choice, stable_matrix, stable_shuffle
from .hashing import sha256, int_to_bytes, hex_of
from .linalg import dot, add, sub, scale, norm, normalize, cosine, softmax, matvec, mean_pool
from .yamlish import yaml_loads, yaml_dump

__all__ = [
    "stable_rand", "stable_float", "stable_int", "stable_vector", "stable_choice",
    "stable_matrix", "stable_shuffle",
    "sha256", "int_to_bytes", "hex_of",
    "dot", "add", "sub", "scale", "norm", "normalize", "cosine", "softmax", "matvec", "mean_pool",
    "yaml_loads", "yaml_dump",
]
