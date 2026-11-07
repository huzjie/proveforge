# -*- coding: utf-8 -*-
"""SHA-256 Merkle tree: the cryptographic commitment backbone.

A model provider commits to its weights by publishing a single Merkle root. The
root is *weight-hiding*: it is a one-way hash, so no weight can be recovered from
it. For each proof, the prover selectively opens individual weight leaves with a
Merkle path; the verifier re-derives the root from the opened leaf and checks it
against the published commitment.

Domain separation (``0x00`` for leaves, ``0x01`` for internal nodes) prevents
leaf/node ambiguity. The tree precomputes every level once so that extracting any
number of sibling paths is ``O(log n)`` each (important: a proof opens thousands
of leaves).
"""
from __future__ import annotations

from ..utils.hashing import sha256, int_to_bytes


def leaf_hash(idx: int, value: int) -> bytes:
    """Hash of a single weight leaf: position-indexed so order is committed too."""
    return sha256(b"\x00" + int_to_bytes(idx) + int_to_bytes(value))


def node_hash(left: bytes, right: bytes) -> bytes:
    """Hash of an internal Merkle node."""
    return sha256(b"\x01" + left + right)


def merkle_root(leaves):
    """Compute the Merkle root of a list of leaf digests (duplicate-pad to even)."""
    layer = list(leaves)
    while len(layer) > 1:
        if len(layer) % 2 == 1:
            layer = layer + [layer[-1]]
        layer = [node_hash(layer[i], layer[i + 1]) for i in range(0, len(layer), 2)]
    return layer[0] if layer else sha256(b"")


def verify_proof(root: bytes, leaf: bytes, proof) -> bool:
    """Re-derive the root from a leaf + sibling path and compare to ``root``."""
    h = leaf
    for sibling, is_left in proof:
        h = node_hash(sibling, h) if is_left else node_hash(h, sibling)
    return h == root


class MerkleTree:
    """A Merkle tree with every level precomputed (cheap per-leaf proofs)."""

    def __init__(self, leaves):
        self.leaves = list(leaves)
        if not self.leaves:
            self.root = sha256(b"")
            self.layers = []
            return
        layer = self.leaves
        self.layers = []
        while len(layer) > 1:
            if len(layer) % 2 == 1:
                layer = layer + [layer[-1]]
            self.layers.append(layer)
            layer = [node_hash(layer[i], layer[i + 1]) for i in range(0, len(layer), 2)]
        self.layers.append(layer)  # the root level (single node)
        self.root = layer[0]

    def proof(self, idx: int):
        """Sibling path for leaf ``idx`` as a list of ``(sibling, is_left)``."""
        i = idx
        proof = []
        for layer in self.layers[:-1]:
            if i % 2 == 0:
                sibling, is_left = layer[i + 1], False
            else:
                sibling, is_left = layer[i - 1], True
            proof.append((sibling, is_left))
            i //= 2
        return proof

    def verify(self, idx: int, leaf: bytes, proof) -> bool:
        return verify_proof(self.root, leaf, proof)
