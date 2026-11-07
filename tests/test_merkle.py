# -*- coding: utf-8 -*-
"""Merkle tree: root, proofs, verification, tamper detection."""
from __future__ import annotations

import unittest

from proveforge.core.merkle import (MerkleTree, leaf_hash, merkle_root, verify_proof,
                                    node_hash)
from proveforge.utils.hashing import sha256


class TestMerkle(unittest.TestCase):
    def _leaves(self, n):
        return [leaf_hash(i, i * 7 % 256) for i in range(n)]

    def test_root_deterministic(self):
        a = merkle_root(self._leaves(8))
        b = merkle_root(self._leaves(8))
        self.assertEqual(a, b)

    def test_proof_verifies_all_indices(self):
        for n in [1, 2, 3, 5, 8, 32]:
            leaves = self._leaves(n)
            tree = MerkleTree(leaves)
            for idx in range(n):
                self.assertTrue(verify_proof(tree.root, leaves[idx], tree.proof(idx)),
                                "n=%d idx=%d" % (n, idx))

    def test_odd_leaf_count_padding(self):
        tree = MerkleTree(self._leaves(5))
        self.assertTrue(verify_proof(tree.root, self._leaves(5)[4], tree.proof(4)))

    def test_tampered_leaf_fails(self):
        leaves = self._leaves(8)
        tree = MerkleTree(leaves)
        bad = leaf_hash(3, 123)  # wrong value
        self.assertFalse(verify_proof(tree.root, bad, tree.proof(3)))

    def test_wrong_index_leaf_fails(self):
        leaves = self._leaves(8)
        tree = MerkleTree(leaves)
        # leaf for idx 0 presented at idx 3
        self.assertFalse(verify_proof(tree.root, leaves[0], tree.proof(3)))

    def test_empty_tree(self):
        tree = MerkleTree([])
        self.assertEqual(tree.root, sha256(b""))

    def test_leaf_hash_position_sensitive(self):
        self.assertNotEqual(leaf_hash(0, 5), leaf_hash(1, 5))

    def test_node_hash_domain_separated(self):
        self.assertNotEqual(node_hash(b"a", b"b"), sha256(b"\x00" + b"a" + b"b"))


if __name__ == "__main__":
    unittest.main()
