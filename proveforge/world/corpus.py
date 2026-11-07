# -*- coding: utf-8 -*-
"""Deterministic prompt corpus.

Every prompt is a short token sequence generated from a string seed, so the
benchmark is reproducible across machines and processes — the same reason the
commitment and proofs can make exact, repeatable claims.
"""
from __future__ import annotations

from ..utils.rng import stable_rand


def build_prompts(n, vocab, seed="corpus"):
    prompts = []
    rnd = stable_rand(seed)
    for i in range(n):
        length = 3 + (i % 3)  # 3..5 token prompts
        prompts.append({
            "id": "p%02d" % i,
            "tokens": [rnd.randrange(vocab) for _ in range(length)],
        })
    return prompts


def build_corpus(cfg):
    vocab = cfg["model"]["vocab"]
    return build_prompts(cfg["world"].get("n_prompts", 24), vocab)
