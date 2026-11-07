# -*- coding: utf-8 -*-
"""Training: a monotone, gradient-free fit of the skill axis.

"Training" here means raising the prover's ``skill`` from an initial value toward
1.0 (fully honest). The update is non-negative and shrinks as the gap closes, so
the reward trace is monotone by construction — mirroring how verifiable-reward
RL monotonically closes the gap between a learned policy and the ground truth.
"""
from __future__ import annotations


class SkillTrainer:
    """Monotone skill axis (0.0 dishonest baseline .. 1.0 fully honest)."""

    def __init__(self, skill: float = 0.0, lr: float = 0.05):
        self.skill = float(skill)
        self.lr = float(lr)

    def train_step(self):
        before = self.skill
        gap = 1.0 - self.skill
        delta = self.lr * gap + 1e-3
        self.skill = min(1.0, self.skill + delta)
        return {"skill": self.skill, "delta": self.skill - before}


class RewardTrainer:
    """Drive skill upward and report the (monotone) verifiable reward."""

    def __init__(self, audit, skill: float = 0.0, lr: float = 0.05):
        self.audit = audit
        self.skill_trainer = SkillTrainer(skill, lr)
        self.history = []

    def step(self):
        step = self.skill_trainer.train_step()
        reward = self.audit.mean_reward(self.skill_trainer.skill)
        rec = {"step": len(self.history) + 1, "skill": step["skill"],
               "delta": step["delta"], "reward": reward}
        self.history.append(rec)
        return rec

    def is_monotone(self):
        rs = [h["reward"] for h in self.history]
        return all(rs[i] <= rs[i + 1] + 1e-9 for i in range(len(rs) - 1))
