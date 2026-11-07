# -*- coding: utf-8 -*-
"""Bench: skill table, monotonicity, attack detection, soundness sweep."""
from __future__ import annotations

import unittest

from proveforge import bench as benchmod
from proveforge.kit import build_kit
from tests.util import small_cfg


class TestBench(unittest.TestCase):
    def setUp(self):
        self.cfg = small_cfg()
        self.cfg["bench"]["attack_cases"] = 8

    def test_skill_table(self):
        table = benchmod.run_skill_table(self.cfg)
        self.assertEqual(len(table), len(self.cfg["bench"]["skills"]))

    def test_monotone_summary(self):
        table = benchmod.run_skill_table(self.cfg)
        mono = benchmod.check_monotone(table)
        self.assertTrue(all(mono.values()))

    def test_summary_endpoints(self):
        table = benchmod.run_skill_table(self.cfg)
        s = benchmod.summarize(table)
        self.assertAlmostEqual(s["accept"][0], 0.0, places=6)
        self.assertAlmostEqual(s["accept"][1], 1.0, places=6)

    def test_attack_detection_full(self):
        ab = benchmod.run_attack_bench(self.cfg)
        self.assertAlmostEqual(ab["substitution_detection"], 1.0, places=6)
        self.assertAlmostEqual(ab["tamper_detection"], 1.0, places=6)

    def test_soundness_sweep_present(self):
        ab = benchmod.run_attack_bench(self.cfg)
        self.assertEqual(len(ab["sweep"]), len(self.cfg["bench"]["ratios"]))
        # full opening must be at least as good as any selective opening
        self.assertAlmostEqual(ab["sweep"][0]["detection"], 1.0, places=6)


if __name__ == "__main__":
    unittest.main()
