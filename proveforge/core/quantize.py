# -*- coding: utf-8 -*-
"""Weight generation and quantization helpers.

FlashProve proves an *integer* version of the model under greedy decoding
(4-bit quantized weights, integer arithmetic in prefill). The reference mirrors
this: weights are native integers in ``[0, 2^bits)``, generated deterministically
from a string seed. This module also ships float<->int quantizers to document the
quantization step a real pipeline performs before committing.
"""
from __future__ import annotations

from ..utils.rng import stable_rand


def gen_model_weights(vocab: int, layers: int, bits: int, seed: str):
    """Deterministic integer weights: ``(layers + 1)`` matrices of ``vocab x vocab``.

    Layers 0..layers-1 are the hidden linear maps; the final matrix is the output
    head (logits). Every entry is an integer in ``[0, 2^bits)``.
    """
    modulus = 1 << bits
    rnd = stable_rand(seed)
    weights = []
    for _ in range(layers + 1):
        mat = [[rnd.randrange(modulus) for _ in range(vocab)] for _ in range(vocab)]
        weights.append(mat)
    return weights


def flatten_rows(weights):
    """Flatten ``(layers+1) x vocab x vocab`` into a list of ``vocab``-int rows."""
    rows = []
    for mat in weights:
        for row in mat:
            rows.append(list(row))
    return rows


def quantize_float_to_int(value: float, bits: int, scale: float = 1.0) -> int:
    """Quantize a float weight to a ``bits``-bit integer (the pre-commit step)."""
    modulus = 1 << bits
    q = int(round(value * scale))
    return q % modulus


def dequantize_int_to_float(q: int, bits: int, scale: float = 1.0) -> float:
    """Inverse of :func:`quantize_float_to_int` (approximate, for inspection)."""
    return (q / scale) if scale else float(q)
