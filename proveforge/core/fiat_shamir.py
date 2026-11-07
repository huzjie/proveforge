# -*- coding: utf-8 -*-
"""Fiat-Shamir: turn the interactive challenge into a deterministic non-interactive one.

The prover cannot choose which weight rows to open — the verifier would catch a
lazy or lying prover if it knew them in advance. So the openings are selected by
a challenge derived from a hash of everything the prover already committed to:
the commitment, the prompt, the claimed output, and the execution trace. This is
the Fiat-Shamir transform: the prover "asks itself" the question the verifier
would have asked, and the hash makes the answer unpredictable *before* the proof
is finalised.
"""
from __future__ import annotations

import random

from ..utils.hashing import sha256


def trace_digest(trace) -> bytes:
    """Deterministic digest of an execution trace (logits only; states are opened)."""
    parts = []
    for st in trace:
        parts.append(b"%d:%s" % (
            st["input"],
            b",".join(b"%d" % x for x in st["logits"]),
        ))
    return b"|".join(parts)


def transcript_seed(commitment_hex: str, prompt, output_tokens, trace) -> bytes:
    """Hash the full transcript into a challenge seed."""
    payload = b"\x02".join([
        commitment_hex.encode("ascii"),
        bytes(prompt),
        bytes(output_tokens),
        trace_digest(trace),
    ])
    return sha256(payload)


def challenge_rng(commitment_hex: str, prompt, output_tokens, trace) -> "random.Random":
    """Deterministic RNG seeded by the transcript (same for prover and verifier)."""
    seed = transcript_seed(commitment_hex, prompt, output_tokens, trace)
    return random.Random(int.from_bytes(seed[:8], "big"))


def select_rows(n_rows: int, open_ratio: float, rng: "random.Random"):
    """Select which weight rows to open.

    ``open_ratio = 1.0`` opens every row (transparent proof, soundness 1.0);
    ``open_ratio < 1.0`` opens a challenge-driven subset (probabilistic soundness,
    partial weight hiding — the Fiat-Shamir regime).
    """
    if open_ratio >= 1.0:
        return list(range(n_rows))
    k = max(1, int(round(n_rows * open_ratio)))
    return sorted(rng.sample(range(n_rows), k))
