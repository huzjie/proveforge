# -*- coding: utf-8 -*-
"""World oracle + corpus + attacks."""
from __future__ import annotations

import unittest

from proveforge.world.oracle import ProvableWorld
from proveforge.world.corpus import build_prompts, build_corpus
from proveforge.world.attacks import tamper_token, substitute_model
from tests.util import small_cfg


class TestWorld(unittest.TestCase):
    def setUp(self):
        self.cfg = small_cfg()
        self.world = ProvableWorld(self.cfg)

    def test_models_independent(self):
        self.assertNotEqual(self.world.committed_weights, self.world.substitute_weights)

    def test_true_output_deterministic(self):
        a = self.world.true_output([1, 2, 3])
        b = self.world.true_output([1, 2, 3])
        self.assertEqual(a, b)

    def test_true_output_length(self):
        out = self.world.true_output([1, 2, 3])
        self.assertEqual(len(out), self.cfg["model"]["ctx"])

    def test_corpus_deterministic(self):
        c1 = build_prompts(12, 32)
        c2 = build_prompts(12, 32)
        self.assertEqual(c1, c2)

    def test_corpus_size(self):
        self.assertEqual(len(build_corpus(self.cfg)), self.cfg["world"]["n_prompts"])

    def test_tamper_token_different(self):
        t = tamper_token(0, 0, 5, 32)
        self.assertNotEqual(t, 5)
        self.assertTrue(0 <= t < 32)

    def test_substitute_returns_b(self):
        w, m = substitute_model(self.world)
        self.assertEqual(m, self.world.model_B)


if __name__ == "__main__":
    unittest.main()
