# -*- coding: utf-8 -*-
"""Config: layered defaults + yaml recipe merging."""
from __future__ import annotations

import unittest

from proveforge.config import load_config, DEFAULTS


class TestConfig(unittest.TestCase):
    def test_defaults_present(self):
        cfg = load_config()
        self.assertIn("model", cfg)
        self.assertIn("prove", cfg)
        self.assertIn("bench", cfg)

    def test_default_values(self):
        cfg = load_config()
        self.assertEqual(cfg["model"]["vocab"], 32)
        self.assertEqual(cfg["model"]["layers"], 3)
        self.assertAlmostEqual(cfg["prove"]["open_ratio"], 1.0)

    def test_recipe_merge(self):
        import tempfile, os
        with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as f:
            f.write("model:\n  vocab: 16\n")
            path = f.name
        try:
            cfg = load_config(path)
            self.assertEqual(cfg["model"]["vocab"], 16)
            # non-overridden keys preserved
            self.assertEqual(cfg["model"]["layers"], 3)
        finally:
            os.unlink(path)

    def test_deepcopy_isolation(self):
        a = load_config()
        b = load_config()
        a["model"]["vocab"] = 99
        self.assertEqual(b["model"]["vocab"], 32)


if __name__ == "__main__":
    unittest.main()
