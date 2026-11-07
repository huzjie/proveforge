# -*- coding: utf-8 -*-
"""Runtime configuration with layered defaults (code default < recipe yaml < cli)."""
from __future__ import annotations

import copy

from .utils.yamlish import yaml_loads

# Defaults are deliberately small so a reference run stays interactive (<1s on a
# laptop) while still exercising the full commit -> prove -> verify pipeline, the
# verifiable-reward audit, and both attack classes. The real FlashProve system
# proves a 400B MoE model at ~110 tok/s on an H100 with ~19 MB proofs; the
# reference keeps the same protocol shape at a laptop-friendly scale.
DEFAULTS = {
    "model": {
        "skill": 0.5,            # prover honesty: 0.0 dishonest .. 1.0 fully honest
        "vocab": 32,             # token vocabulary size (== embedding dim)
        "layers": 3,             # hidden linear layers (+1 output head)
        "bits": 8,               # integer modulus 2^bits (weight quantization)
        "ctx": 12,               # max decode length
    },
    "world": {
        "n_prompts": 24,         # deterministic prompt corpus size
    },
    "prove": {
        # 1.0 = transparent proof (open all rows, soundness 1.0)
        # <1.0 = Fiat-Shamir selective opening (probabilistic soundness, partial hiding)
        "open_ratio": 1.0,
    },
    "bench": {
        "skills": [0.0, 0.25, 0.5, 0.75, 1.0],
        "attack_cases": 20,
        "ratios": [1.0, 0.5, 0.25, 0.1, 0.02],  # soundness vs open_ratio sweep
    },
    "report": {
        "format": "markdown",    # markdown | json
        "out_dir": "reports",
    },
}


def _merge(base, override):
    out = copy.deepcopy(base)
    for k, v in (override or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _merge(out[k], v)
        else:
            out[k] = v
    return out


def load_config(recipe_path=None):
    """Return the merged config dict. A recipe (yaml subset) overrides defaults."""
    cfg = copy.deepcopy(DEFAULTS)
    if recipe_path:
        with open(recipe_path, "r", encoding="utf-8") as f:
            raw = yaml_loads(f.read())
        cfg = _merge(cfg, raw)
    return cfg
