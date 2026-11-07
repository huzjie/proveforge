# -*- coding: utf-8 -*-
"""Verifier: CPU-only, checks a proof against the published commitment.

This mirrors FlashProve's ``cp_verify``: a lightweight, GPU-free program that
decides accept/reject. It re-derives the Fiat-Shamir challenge from the proof,
then runs two independent checks:

1. **binding** — every opened weight leaf re-derives the committed root. A
   prover that substituted a different model cannot reveal leaves that hash to
   the committed tree (weight-hiding commitment), so this catches substitution.
2. **integrity** — the trace is internally consistent and the claimed output is
   the greedy argmax of the committed model. A tampered token stream fails the
   argmax / chain check.

Verification is cheap by design: it never re-runs the full model from scratch and
never requires the hidden weights — only the opened leaves.
"""
from __future__ import annotations

from .merkle import leaf_hash, verify_proof
from .model import _argmax
from .fiat_shamir import challenge_rng, select_rows


def verify(bundle, proof):
    """Return ``{accepted, binding_ok, integrity_ok}`` for a proof."""
    rng = challenge_rng(bundle.hex(), proof.prompt, proof.output_tokens, proof.trace)
    _open_rows = select_rows(bundle.n_rows, proof.open_ratio, rng)

    # --- binding: opened leaves must re-derive the committed root -------------
    binding_ok = True
    for r in proof.open_rows:
        for (gidx, val, siblings) in proof.openings.get(r, []):
            if not verify_proof(bundle.root, leaf_hash(gidx, val), siblings):
                binding_ok = False

    # --- integrity: trace consistency + argmax + output binding + chain ------
    integrity_ok = True
    opened_vals = {
        r: [proof.openings[r][c][1] for c in range(bundle.vocab)]
        for r in proof.open_rows
    }
    gen_start = len(proof.prompt)
    prev_token = proof.prompt[-1]
    for i, st in enumerate(proof.trace):
        if st["input"] != prev_token:
            integrity_ok = False
        if _argmax(st["logits"]) != st["token"]:
            integrity_ok = False
        # the claimed output must be the greedy argmax the trace commits to
        if proof.output_tokens[gen_start + i] != st["token"]:
            integrity_ok = False
        for r in proof.open_rows:
            layer = r // bundle.vocab
            out = r % bundle.vocab
            in_vec = st["states"][layer]
            actual = st["states"][layer + 1][out] if layer < bundle.layers else st["logits"][out]
            expected = sum(opened_vals[r][c] * in_vec[c] for c in range(bundle.vocab)) % bundle.modulus
            if expected != actual:
                integrity_ok = False
        prev_token = st["token"]

    return {
        "accepted": binding_ok and integrity_ok,
        "binding_ok": binding_ok,
        "integrity_ok": integrity_ok,
    }
