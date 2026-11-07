# -*- coding: utf-8 -*-
"""Prover + verifier roundtrip and the weight-hiding commitment."""
from __future__ import annotations

import unittest

from proveforge.core.quantize import gen_model_weights
from proveforge.core.model import IntegerLLM
from proveforge.core.prover import commit_weights, prove
from proveforge.core.verifier import verify


def _world(vocab=8, layers=2, bits=8, ctx=8):
    a = gen_model_weights(vocab, layers, bits, "model:A")
    b = gen_model_weights(vocab, layers, bits, "model:B")
    bundle = commit_weights(a, vocab, layers, bits)
    return {
        "bundle": bundle,
        "model_a": IntegerLLM(a, vocab, layers, bits),
        "model_b": IntegerLLM(b, vocab, layers, bits),
        "weights_a": a,
        "weights_b": b,
        "vocab": vocab,
        "ctx": ctx,
    }


class TestProverVerifier(unittest.TestCase):
    def test_commitment_hides_weights(self):
        w = _world()
        b = w["bundle"]
        # root is 32 bytes; cannot reconstruct 4096 weight ints from it
        self.assertEqual(len(b.root), 32)
        self.assertEqual(b.n_entries, (2 + 1) * 8 * 8)

    def test_honest_proof_accepted(self):
        w = _world()
        p = prove(w["bundle"], [1, 2, 3], w["model_a"], w["weights_a"], 1.0, w["ctx"])
        v = verify(w["bundle"], p)
        self.assertTrue(v["accepted"])
        self.assertTrue(v["binding_ok"])
        self.assertTrue(v["integrity_ok"])

    def test_substitution_rejected(self):
        w = _world()
        p = prove(w["bundle"], [1, 2, 3], w["model_b"], w["weights_b"], 1.0, w["ctx"])
        v = verify(w["bundle"], p)
        self.assertFalse(v["accepted"])
        self.assertFalse(v["binding_ok"])

    def test_tamper_rejected(self):
        w = _world()
        base, _ = w["model_a"].decode([1, 2, 3], w["ctx"])
        out = list(base)
        out[3] = (out[3] + 1) % w["vocab"]
        p = prove(w["bundle"], [1, 2, 3], w["model_a"], w["weights_a"], 1.0, w["ctx"],
                  output_tokens=out)
        v = verify(w["bundle"], p)
        self.assertFalse(v["accepted"])
        self.assertFalse(v["integrity_ok"])

    def test_corrupted_trace_rejected(self):
        w = _world()
        _, trace = w["model_a"].decode([1, 2, 3], w["ctx"])
        trace[0]["states"][1][0] = (trace[0]["states"][1][0] + 1) % 256
        p = prove(w["bundle"], [1, 2, 3], w["model_a"], w["weights_a"], 1.0, w["ctx"],
                  trace=trace)
        v = verify(w["bundle"], p)
        self.assertFalse(v["accepted"])
        self.assertFalse(v["integrity_ok"])

    def test_selective_opening_still_accepts_honest(self):
        w = _world()
        p = prove(w["bundle"], [1, 2, 3], w["model_a"], w["weights_a"], 0.5, w["ctx"])
        self.assertTrue(verify(w["bundle"], p)["accepted"])

    def test_commitment_deterministic(self):
        a = commit_weights(_world()["weights_a"], 8, 2, 8)
        b = commit_weights(_world()["weights_a"], 8, 2, 8)
        self.assertEqual(a.root, b.root)


if __name__ == "__main__":
    unittest.main()
