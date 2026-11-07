# -*- coding: utf-8 -*-
"""Attack variants: the dishonest prover behaviours the verifier must catch.

Two canonical attacks on provable inference:

* **substitute_model** — the prover runs a different (cheaper) model but keeps
  claiming the committed model's identity. Caught by the binding check: its
  revealed weights can't hash to the committed root.
* **tamper_token** — the prover (or a man-in-the-middle) flips an output token in
  transit. Caught by the integrity check: the claimed token is no longer the
  greedy argmax of the revealed logits.

Both are what the verifier's job is — and the benchmark measures how reliably it
rejects them.
"""
from __future__ import annotations

from ..utils.rng import stable_int


def tamper_token(prompt_idx: int, token_idx: int, true_token: int, vocab: int) -> int:
    """An independent, guaranteed-different token (models a tampered token stream)."""
    t = stable_int("tamper:p%d:t%d" % (prompt_idx, token_idx), 0, vocab - 1)
    if t == true_token:
        t = (true_token + 1) % vocab
    return t


def substitute_model(world):
    """Return the independent substitute weights + model (model B)."""
    return world.substitute_weights, world.model_B
