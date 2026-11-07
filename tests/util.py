# -*- coding: utf-8 -*-
"""Shared test helpers."""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def small_cfg(**overrides):
    """A minimal config dict for tests (fast, small vocab)."""
    from proveforge.config import DEFAULTS
    import copy
    cfg = copy.deepcopy(DEFAULTS)
    cfg["world"]["n_prompts"] = 8
    cfg["bench"]["attack_cases"] = 6
    for k, v in overrides.items():
        cfg[k] = v
    return cfg
