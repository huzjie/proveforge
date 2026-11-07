# -*- coding: utf-8 -*-
"""Kit wiring + CLI smoke tests."""
from __future__ import annotations

import unittest

from proveforge.kit import build_kit
from tests.util import small_cfg


class TestKit(unittest.TestCase):
    def test_kit_keys(self):
        kit = build_kit(small_cfg())
        for key in ("cfg", "corpus", "world", "bundle", "audit"):
            self.assertIn(key, kit)

    def test_bundle_consistency(self):
        kit = build_kit(small_cfg())
        b = kit["bundle"]
        self.assertEqual(b.n_rows, (3 + 1) * 32)
        self.assertEqual(b.n_entries, (3 + 1) * 32 * 32)


if __name__ == "__main__":
    unittest.main()
