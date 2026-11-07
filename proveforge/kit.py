# -*- coding: utf-8 -*-
"""Wire everything into a ready-to-use kit (corpus + world + commitment + audit)."""
from __future__ import annotations

from .world.corpus import build_corpus
from .world.oracle import ProvableWorld
from .core.prover import commit_weights
from .training.reward import VerifierAudit


def build_kit(cfg):
    corpus = build_corpus(cfg)
    world = ProvableWorld(cfg)
    bundle = commit_weights(world.committed_weights, world.vocab, world.layers, world.bits)
    audit = VerifierAudit(cfg, world, bundle, corpus)
    return {
        "cfg": cfg,
        "corpus": corpus,
        "world": world,
        "bundle": bundle,
        "audit": audit,
    }
