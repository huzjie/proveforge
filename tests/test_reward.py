# -*- coding: utf-8 -*-
"""Verifiable-reward audit: metrics, monotonicity, extremes."""
from __future__ import annotations

import unittest

from proveforge.kit import build_kit
from proveforge.training.trainer import SkillTrainer, RewardTrainer
from tests.util import small_cfg


class TestReward(unittest.TestCase):
    def setUp(self):
        self.cfg = small_cfg()
        self.kit = build_kit(self.cfg)
        self.audit = self.kit["audit"]

    def test_skill_zero_all_zero(self):
        r = self.audit.audit_skill(0.0)
        self.assertAlmostEqual(r["binding"], 0.0, places=6)
        self.assertAlmostEqual(r["integrity"], 0.0, places=6)
        self.assertAlmostEqual(r["accept"], 0.0, places=6)

    def test_skill_one_all_one(self):
        r = self.audit.audit_skill(1.0)
        self.assertAlmostEqual(r["binding"], 1.0, places=6)
        self.assertAlmostEqual(r["integrity"], 1.0, places=6)
        self.assertAlmostEqual(r["fidelity"], 1.0, places=6)
        self.assertAlmostEqual(r["accept"], 1.0, places=6)

    def test_monotone(self):
        prev = None
        for s in [0.0, 0.25, 0.5, 0.75, 1.0]:
            r = self.audit.audit_skill(s)
            for key in ("binding", "integrity", "fidelity", "accept"):
                if prev is not None:
                    self.assertGreaterEqual(r[key] + 1e-9, prev[key],
                                            "%s not monotone at skill %.2f" % (key, s))
            prev = r

    def test_accept_leq_binding(self):
        for s in [0.25, 0.5, 0.75]:
            r = self.audit.audit_skill(s)
            self.assertLessEqual(r["accept"], r["binding"] + 1e-9)

    def test_skill_trainer_monotone(self):
        t = SkillTrainer(0.0, lr=0.05)
        prev = t.skill
        for _ in range(200):
            step = t.train_step()
            self.assertGreaterEqual(step["delta"], 0)
            self.assertGreaterEqual(t.skill, prev)
            prev = t.skill
        self.assertGreater(t.skill, 0.99)

    def test_reward_trainer_monotone(self):
        tr = RewardTrainer(self.audit, skill=0.0, lr=0.2)
        for _ in range(8):
            tr.step()
        self.assertTrue(tr.is_monotone())


if __name__ == "__main__":
    unittest.main()
