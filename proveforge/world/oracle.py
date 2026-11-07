# -*- coding: utf-8 -*-
"""World: the closed-form committed model (oracle)."""
from __future__ import annotations

from ..core.quantize import gen_model_weights
from ..core.model import IntegerLLM


class ProvableWorld:
    """Ground truth: the committed model A and an independent substitute model B.

    Model A is what the provider commits to (and what honest provers run). Model B
    is an *independent* draw — the stand-in for a cheap model a routing service
    might silently substitute. Everything is deterministic from string seeds.
    """

    def __init__(self, cfg):
        m = cfg["model"]
        self.vocab = m["vocab"]
        self.layers = m["layers"]
        self.bits = m["bits"]
        self.ctx = m["ctx"]
        self.committed_weights = gen_model_weights(
            self.vocab, self.layers, self.bits, seed="model:A")
        self.substitute_weights = gen_model_weights(
            self.vocab, self.layers, self.bits, seed="model:B")
        self.model_A = IntegerLLM(self.committed_weights, self.vocab, self.layers, self.bits)
        self.model_B = IntegerLLM(self.substitute_weights, self.vocab, self.layers, self.bits)

    def true_output(self, prompt_tokens):
        """The committed model's greedy output for a prompt (ground truth)."""
        return self.model_A.decode(prompt_tokens, self.ctx)[0]
