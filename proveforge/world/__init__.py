# -*- coding: utf-8 -*-
"""World: the closed-form committed model (oracle) + deterministic prompt corpus + attacks."""
from __future__ import annotations

from .oracle import ProvableWorld
from .corpus import build_corpus, build_prompts
from .attacks import tamper_token, substitute_model

__all__ = ["ProvableWorld", "build_corpus", "build_prompts", "tamper_token", "substitute_model"]
