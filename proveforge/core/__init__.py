# -*- coding: utf-8 -*-
"""Core provable-inference primitives: quantize, merkle, model, fiat-shamir, prover, verifier."""
from __future__ import annotations

from .quantize import gen_model_weights, flatten_rows, quantize_float_to_int, dequantize_int_to_float
from .merkle import merkle_root, MerkleTree, verify_proof, leaf_hash, node_hash
from .model import IntegerLLM, _argmax
from .prover import commit_weights, prove, CommitmentBundle, Proof
from .verifier import verify

__all__ = [
    "gen_model_weights", "flatten_rows", "quantize_float_to_int", "dequantize_int_to_float",
    "merkle_root", "MerkleTree", "verify_proof", "leaf_hash", "node_hash",
    "IntegerLLM", "_argmax",
    "commit_weights", "prove", "verify", "CommitmentBundle", "Proof",
]
