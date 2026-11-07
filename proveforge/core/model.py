# -*- coding: utf-8 -*-
"""The closed-form integer "LLM" whose inference we prove.

This is the model under proof: a small, fully deterministic, integer-valued
decoder. A token is embedded as a one-hot vector, passed through ``layers``
integer linear maps (each ``W_l @ h mod 2^bits``), then mapped to logits by an
output head; greedy decoding picks the argmax. The closed form is what makes the
oracle exact and the proof *verifiable*: given the weights and the input, the
output is unique and reproducible everywhere.
"""
from __future__ import annotations


def _argmax(values):
    best = 0
    for i in range(1, len(values)):
        if values[i] > values[best]:
            best = i
    return best


class IntegerLLM:
    def __init__(self, weights, vocab: int, layers: int, bits: int):
        self.weights = weights  # (layers + 1) matrices, each vocab x vocab
        self.vocab = vocab
        self.layers = layers
        self.bits = bits
        self.modulus = 1 << bits

    def matvec_mod(self, mat, vec):
        """Integer matrix-vector product modulo ``2^bits`` (rows of ``mat``)."""
        modulus = self.modulus
        return [sum(mat[j][i] * vec[i] for i in range(len(vec))) % modulus
                for j in range(len(mat))]

    def step(self, token_id: int):
        """One decode step: return the per-layer states, logits, and greedy next token."""
        states = [[0] * self.vocab for _ in range(self.layers + 1)]
        states[0][token_id] = 1
        for l in range(self.layers):
            states[l + 1] = self.matvec_mod(self.weights[l], states[l])
        logits = self.matvec_mod(self.weights[self.layers], states[self.layers])
        return {
            "input": token_id,
            "states": states,
            "logits": logits,
            "token": _argmax(logits),
        }

    def decode(self, prompt, max_len: int):
        """Autoregressive greedy decode starting from ``prompt``; returns tokens + trace."""
        tokens = list(prompt)
        trace = []
        for _ in range(max_len - len(tokens)):
            st = self.step(tokens[-1])
            tokens.append(st["token"])
            trace.append(st)
        return tokens, trace
