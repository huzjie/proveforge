# -*- coding: utf-8 -*-
"""proveforge — provable inference for LLMs (Anthropic FlashProve-style).

A zero-dependency reference implementation of the *commit → prove → verify*
pipeline that lets a model provider cryptographically bind a response to a
specific set of (hidden) weights, and lets any CPU-only verifier check that
binding. See README.md and docs/ for the full technical walkthrough.
"""
from __future__ import annotations

from .version import __version__
from .core.prover import commit_weights, prove, CommitmentBundle, Proof
from .core.verifier import verify

__all__ = [
    "__version__",
    "commit_weights",
    "prove",
    "verify",
    "CommitmentBundle",
    "Proof",
]
