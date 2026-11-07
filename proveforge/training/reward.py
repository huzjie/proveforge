# -*- coding: utf-8 -*-
"""Verifiable reward: the skill-driven audit that produces provable-inference metrics.

There is no learned reward model and no human labelling. For every (prompt,
skill) pair we simulate a prover with *three* independent honesty axes, each a
deterministic threshold function of ``skill``:

* **model honesty** — use the committed model A, or a substitute model B;
* **trace honesty** — report the true execution trace, or corrupt a state value;
* **token honesty** — claim the greedy output, or tamper with a token.

For each prompt we produce a real proof, run the real verifier, and aggregate
four metrics. Each is a monotone 0 -> 1 function of ``skill`` by construction:

* **binding**   — revealed weights match the commitment (catches substitution);
* **integrity** — trace is consistent and output is the greedy argmax (catches
  trace corruption + token tampering);
* **fidelity**  — claimed output equals the committed model's true output
  (catches substitution + tampering in output space);
* **accept**    — the verifier accepts (the strict three-way composite).
"""
from __future__ import annotations

from ..utils.rng import stable_float, stable_int
from ..core.prover import prove
from ..core.verifier import verify
from ..world.attacks import tamper_token


class VerifierAudit:
    def __init__(self, cfg, world, bundle, corpus):
        self.cfg = cfg
        self.world = world
        self.bundle = bundle
        self.corpus = corpus
        self.open_ratio = cfg["prove"]["open_ratio"]

    # -- deterministic per-slot honesty thresholds ---------------------------
    def _t(self, pi, axis):
        return stable_float("%s:%d" % (axis, pi), 1e-6, 0.9999)

    def _audit_one(self, pi, prompt, skill):
        ptoks = prompt["tokens"]
        gen_start = len(ptoks)
        true_out = self.world.true_output(ptoks)

        honest_model = skill >= self._t(pi, "model")
        honest_trace = skill >= self._t(pi, "trace")
        honest_token = skill >= self._t(pi, "token")

        if honest_model:
            weights, model = self.world.committed_weights, self.world.model_A
        else:
            weights, model = self.world.substitute_weights, self.world.model_B

        base_out, trace = model.decode(ptoks, self.world.ctx)

        # tamper the first generated token
        out = list(base_out)
        if not honest_token:
            i = gen_start
            out[i] = tamper_token(pi, 0, out[i], self.world.vocab)

        # corrupt a single state value in the first decode step (layer 1, index k)
        if not honest_trace and trace:
            k = stable_int("corrupt:%d" % pi, 0, self.world.vocab - 1)
            v = trace[0]["states"][1][k]
            trace[0]["states"][1][k] = (v + 1) % (1 << self.world.bits)

        proof = prove(self.bundle, ptoks, model, weights, self.open_ratio,
                      self.world.ctx, output_tokens=out, trace=trace)
        verdict = verify(self.bundle, proof)

        fidelity = 1.0 if out == true_out else 0.0
        return verdict, fidelity

    def audit_skill(self, skill):
        binding = integrity = fidelity = accept = 0
        n = len(self.corpus)
        for pi, prompt in enumerate(self.corpus):
            verdict, fid = self._audit_one(pi, prompt, skill)
            binding += verdict["binding_ok"]
            integrity += verdict["integrity_ok"]
            fidelity += fid
            accept += verdict["accepted"]
        return {
            "skill": skill,
            "binding": binding / n,
            "integrity": integrity / n,
            "fidelity": fidelity / n,
            "accept": accept / n,
        }

    def mean_reward(self, skill):
        return self.audit_skill(skill)["accept"]
