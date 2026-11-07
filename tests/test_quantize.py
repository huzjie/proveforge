# -*- coding: utf-8 -*-
"""Quantization + weight generation determinism."""
from __future__ import annotations

import unittest

from proveforge.core.quantize import (gen_model_weights, flatten_rows,
                                      quantize_float_to_int, dequantize_int_to_float)


class TestQuantize(unittest.TestCase):
    def test_deterministic_weights(self):
        a = gen_model_weights(8, 2, 8, "model:A")
        b = gen_model_weights(8, 2, 8, "model:A")
        self.assertEqual(a, b)

    def test_different_seed_different_weights(self):
        a = gen_model_weights(8, 2, 8, "model:A")
        b = gen_model_weights(8, 2, 8, "model:B")
        self.assertNotEqual(a, b)

    def test_shape(self):
        w = gen_model_weights(32, 3, 8, "x")
        self.assertEqual(len(w), 4)  # layers + output head
        self.assertEqual(len(w[0]), 32)
        self.assertEqual(len(w[0][0]), 32)

    def test_values_in_range(self):
        w = gen_model_weights(32, 3, 8, "y")
        for mat in w:
            for row in mat:
                for v in row:
                    self.assertTrue(0 <= v < 256)

    def test_flatten_rows(self):
        w = gen_model_weights(4, 1, 8, "z")
        rows = flatten_rows(w)
        self.assertEqual(len(rows), (1 + 1) * 4)  # 8 rows
        self.assertEqual(len(rows[0]), 4)

    def test_quantize_roundtrip(self):
        q = quantize_float_to_int(0.123, 8, scale=1000.0)
        self.assertTrue(0 <= q < 256)
        back = dequantize_int_to_float(q, 8, scale=1000.0)
        self.assertAlmostEqual(back, round(0.123 * 1000) / 1000.0, places=6)


if __name__ == "__main__":
    unittest.main()
