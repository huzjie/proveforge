# -*- coding: utf-8 -*-
"""Benchmarks: skill-driven metric table + monotonicity + attack detection + soundness sweep."""
from __future__ import annotations

from .kit import build_kit
from .core.prover import prove
from .core.verifier import verify


def run_skill_table(cfg):
    """Aggregate the four provable-inference metrics vs prover skill."""
    kit = build_kit(cfg)
    audit = kit["audit"]
    return [audit.audit_skill(s) for s in cfg["bench"]["skills"]]


def summarize(table):
    a, b = table[0], table[-1]
    return {
        "binding": (a["binding"], b["binding"]),
        "integrity": (a["integrity"], b["integrity"]),
        "fidelity": (a["fidelity"], b["fidelity"]),
        "accept": (a["accept"], b["accept"]),
    }


def check_monotone(table):
    """Verify all four metrics are non-decreasing across the skill axis."""
    def inc(get):
        return all(get(table[i]) <= get(table[i + 1]) + 1e-9
                   for i in range(len(table) - 1))

    return {
        "binding_inc": inc(lambda r: r["binding"]),
        "integrity_inc": inc(lambda r: r["integrity"]),
        "fidelity_inc": inc(lambda r: r["fidelity"]),
        "accept_inc": inc(lambda r: r["accept"]),
    }


# --- attack constructions ---------------------------------------------------

def _substitution_proof(world, bundle, prompt, open_ratio):
    ptoks = prompt["tokens"]
    return prove(bundle, ptoks, world.model_B, world.substitute_weights,
                 open_ratio, world.ctx)


def _tamper_proof(world, bundle, prompt, open_ratio):
    ptoks = prompt["tokens"]
    model = world.model_A
    base_out, _ = model.decode(ptoks, world.ctx)
    out = list(base_out)
    i = len(ptoks)
    out[i] = (out[i] + 1) % world.vocab  # flip the first generated token
    return prove(bundle, ptoks, model, world.committed_weights,
                 open_ratio, world.ctx, output_tokens=out)


def _partial_substitution_proof(world, bundle, prompt, open_ratio, poison_rows):
    """Substitute only a few weight rows (a 'sneaky' swap), keeping A's trace."""
    ptoks = prompt["tokens"]
    b_rows = [row for mat in world.substitute_weights for row in mat]
    mixed = [list(m) for m in world.committed_weights]
    for r in poison_rows:
        layer = r // world.vocab
        col = r % world.vocab
        mixed[layer][col] = list(b_rows[r])
    return prove(bundle, ptoks, world.model_A, mixed, open_ratio, world.ctx)


def run_attack_bench(cfg):
    """Detection rates for full substitution + tamper, and a soundness sweep.

    The sweep uses *partial* substitution (only a handful of poisoned rows) so
    that selective opening has a real detection gradient: opening more rows
    raises the probability of catching a poisoned row. This is the Fiat-Shamir
    soundness / proof-complexity tradeoff made measurable.
    """
    kit = build_kit(cfg)
    world, bundle = kit["world"], kit["bundle"]
    prompts = kit["corpus"]
    n = cfg["bench"]["attack_cases"]

    sub_det = tam_det = 0
    for i in range(n):
        p = prompts[i % len(prompts)]
        if not verify(bundle, _substitution_proof(world, bundle, p, 1.0))["accepted"]:
            sub_det += 1
        if not verify(bundle, _tamper_proof(world, bundle, p, 1.0))["accepted"]:
            tam_det += 1

    poison_rows = [0, 1, 2, 3]  # first four weight rows (layer 0)
    sweep = []
    for ratio in cfg["bench"]["ratios"]:
        det = 0
        for i in range(n):
            p = prompts[i % len(prompts)]
            proof = _partial_substitution_proof(world, bundle, p, ratio, poison_rows)
            if not verify(bundle, proof)["accepted"]:
                det += 1
        sweep.append({"open_ratio": ratio, "detection": det / n})

    return {
        "substitution_detection": sub_det / n,
        "tamper_detection": tam_det / n,
        "sweep": sweep,
    }
