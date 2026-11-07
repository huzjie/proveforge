# -*- coding: utf-8 -*-
"""Prover: commit to weights and produce a proof for a specific request.

The two public operations mirror FlashProve's ``cp_commit`` / ``cp_prove``:

* ``commit_weights`` publishes a Merkle root over the (quantized) weights — the
  commitment. Only the root (and the architecture: vocab/layers/bits) is public;
  the weights stay secret.
* ``prove`` runs the model, records the execution trace, uses Fiat-Shamir to pick
  which weight rows to open, and returns a Proof carrying the opened rows + the
  trace. The proof binds a claimed output to the committed weights.
"""
from __future__ import annotations

from .merkle import MerkleTree, leaf_hash
from .fiat_shamir import challenge_rng, select_rows


class CommitmentBundle:
    """Everything the verifier needs about a committed model (root + architecture)."""

    def __init__(self, weights, vocab: int, layers: int, bits: int):
        self.weights = weights
        self.vocab = vocab
        self.layers = layers
        self.bits = bits
        self.modulus = 1 << bits
        self.rows = []
        for mat in weights:
            for row in mat:
                self.rows.append(list(row))
        self.n_rows = len(self.rows)
        self.leaves = []
        for r, row in enumerate(self.rows):
            for c, val in enumerate(row):
                self.leaves.append(leaf_hash(r * vocab + c, val))
        self.tree = MerkleTree(self.leaves)
        self.root = self.tree.root
        self.n_entries = len(self.leaves)

    def hex(self) -> str:
        return self.root.hex()


class Proof:
    def __init__(self, commitment, prompt, output_tokens, open_ratio, open_rows,
                 openings, trace):
        self.commitment = commitment
        self.prompt = list(prompt)
        self.output_tokens = list(output_tokens)
        self.open_ratio = open_ratio
        self.open_rows = open_rows
        self.openings = openings  # row_idx -> list of (global_idx, value, siblings)
        self.trace = trace


def commit_weights(weights, vocab: int, layers: int, bits: int) -> CommitmentBundle:
    """Build the weight-hiding commitment to a set of weights."""
    return CommitmentBundle(weights, vocab, layers, bits)


def prove(bundle, prompt, model, used_weights, open_ratio: float, max_len: int,
          output_tokens=None, trace=None):
    """Produce a proof that ``used_weights`` produced ``output_tokens`` for ``prompt``.

    ``bundle`` is the *published* commitment; ``used_weights`` is the model the
    prover actually ran (equal to the committed weights for an honest prover,
    different for a substitute-model attack). ``output_tokens`` defaults to the
    model's own greedy output but can be overridden to model token tampering;
    ``trace`` can be overridden to model a corrupted execution trace.
    """
    base_out, base_trace = model.decode(prompt, max_len)
    if output_tokens is None:
        output_tokens = base_out
    if trace is None:
        trace = base_trace
    rng = challenge_rng(bundle.hex(), prompt, output_tokens, trace)
    open_rows = select_rows(bundle.n_rows, open_ratio, rng)

    used_rows = []
    for mat in used_weights:
        for row in mat:
            used_rows.append(list(row))

    openings = {}
    for r in open_rows:
        row_open = []
        for c in range(bundle.vocab):
            gidx = r * bundle.vocab + c
            val = used_rows[r][c]                    # the value the prover reveals
            siblings = bundle.tree.proof(gidx)       # path in the committed tree
            row_open.append((gidx, val, siblings))
        openings[r] = row_open

    return Proof(bundle, prompt, output_tokens, open_ratio, open_rows, openings, trace)
