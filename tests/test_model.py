# -*- coding: utf-8 -*-
"""Integer LLM: determinism, trace shape, greedy decode."""
from __future__ import annotations

import unittest

from proveforge.core.quantize import gen_model_weights
from proveforge.core.model import IntegerLLM, _argmax


class TestModel(unittest.TestCase):
    def setUp(self):
        self.vocab, self.layers, self.bits = 16, 2, 8
        self.w = gen_model_weights(self.vocab, self.layers, self.bits, "m")
        self.m = IntegerLLM(self.w, self.vocab, self.layers, self.bits)

    def test_decode_deterministic(self):
        a = self.m.decode([1, 2, 3], 8)
        b = self.m.decode([1, 2, 3], 8)
        self.assertEqual(a, b)

    def test_decode_length(self):
        tokens, trace = self.m.decode([1, 2, 3], 8)
        self.assertEqual(len(tokens), 8)
        self.assertEqual(len(trace), 8 - 3)

    def test_trace_shape(self):
        _, trace = self.m.decode([1], 5)
        st = trace[0]
        self.assertEqual(st["input"], 1)
        self.assertEqual(len(st["states"]), self.layers + 1)
        self.assertEqual(len(st["logits"]), self.vocab)
        self.assertTrue(0 <= st["token"] < self.vocab)

    def test_states_integer_range(self):
        _, trace = self.m.decode([1], 6)
        for st in trace:
            for s in st["states"]:
                for v in s:
                    self.assertTrue(0 <= v < 256)

    def test_argmax_is_greedy(self):
        logits = trace = self.m.decode([1], 3)[1][0]["logits"]
        self.assertEqual(_argmax(logits), max(range(len(logits)), key=lambda i: logits[i]))

    def test_argmax_tie_breaks_lowest(self):
        self.assertEqual(_argmax([1, 3, 3, 2]), 1)


if __name__ == "__main__":
    unittest.main()
