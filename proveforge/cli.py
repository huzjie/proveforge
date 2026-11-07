# -*- coding: utf-8 -*-
"""Command-line interface: doctor / bench / modes / run / train / audit / commit / prove / verify / serve."""
from __future__ import annotations

import argparse
import json

from .config import load_config
from .kit import build_kit
from . import bench as benchmod
from .core.prover import prove
from .core.verifier import verify
from .training.trainer import RewardTrainer
from .tasks import list_tasks


def _find_prompt(corpus, pid):
    for p in corpus:
        if p["id"] == pid:
            return p
    return corpus[0]


def _proof_size(proof):
    n_open = len(proof.open_rows)
    n_entries = sum(len(v) for v in proof.openings.values())
    # value (8B) + siblings (~7 x 32B) per entry + states/logits
    approx = n_entries * (8 + 7 * 32) + sum(len(s["states"]) * 8 for s in proof.trace)
    return n_open, n_entries, approx


def cmd_doctor(cfg):
    kit = build_kit(cfg)
    b = kit["bundle"]
    r = kit["audit"].audit_skill(1.0)
    print("[doctor] vocab=%d layers=%d bits=%d ctx=%d prompts=%d"
          % (b.vocab, b.layers, b.bits, cfg["model"]["ctx"], len(kit["corpus"])))
    print("[doctor] commitment root=%s (rows=%d entries=%d)"
          % (b.hex(), b.n_rows, b.n_entries))
    print("[doctor] binding=%.4f integrity=%.4f fidelity=%.4f accept=%.4f"
          % (r["binding"], r["integrity"], r["fidelity"], r["accept"]))
    ok = (r["binding"] >= 0.9999 and r["integrity"] >= 0.9999
          and r["fidelity"] >= 0.9999 and r["accept"] >= 0.9999)
    if not ok:
        raise SystemExit("[doctor] FAIL: metrics not at 1.0 at skill=1.0")
    print("[doctor] OK (fully honest prover reproduced across all four metrics)")


def cmd_bench(cfg):
    table = benchmod.run_skill_table(cfg)
    print("[bench] skill  binding  integrity  fidelity  accept")
    for r in table:
        print("[bench] %.2f   %.4f    %.4f      %.4f     %.4f"
              % (r["skill"], r["binding"], r["integrity"], r["fidelity"], r["accept"]))
    s = benchmod.summarize(table)
    print("[bench] binding %.4f->%.4f | integrity %.4f->%.4f | fidelity %.4f->%.4f | accept %.4f->%.4f"
          % (s["binding"][0], s["binding"][1], s["integrity"][0], s["integrity"][1],
             s["fidelity"][0], s["fidelity"][1], s["accept"][0], s["accept"][1]))
    mono = benchmod.check_monotone(table)
    print("[bench] monotone: %s" % ", ".join("%s=%s" % (k, v) for k, v in mono.items()))
    ab = benchmod.run_attack_bench(cfg)
    print("[bench] substitution_detection=%.4f tamper_detection=%.4f"
          % (ab["substitution_detection"], ab["tamper_detection"]))
    print("[bench] soundness sweep (partial substitution):")
    for row in ab["sweep"]:
        print("[bench]   open_ratio=%.2f detection=%.4f" % (row["open_ratio"], row["detection"]))


def cmd_modes(cfg):
    kit = build_kit(cfg)
    b = kit["bundle"]
    print("[modes] vocab=%d layers=%d bits=%d ctx=%d" % (b.vocab, b.layers, b.bits, cfg["model"]["ctx"]))
    print("[modes] weights rows=%d entries=%d commitment=%s..." % (b.n_rows, b.n_entries, b.hex()[:12]))
    print("[modes] prompts=%d ratios=%s" % (len(kit["corpus"]), cfg["bench"]["ratios"]))
    print("[modes] capabilities=%s" % ", ".join(t["id"] for t in list_tasks()))


def cmd_run(cfg, args):
    kit = build_kit(cfg)
    p = _find_prompt(kit["corpus"], args.prompt)
    proof = prove(kit["bundle"], p["tokens"], kit["world"].model_A,
                  kit["world"].committed_weights, cfg["prove"]["open_ratio"], kit["world"].ctx)
    verdict = verify(kit["bundle"], proof)
    n_open, n_entries, size = _proof_size(proof)
    print("[run] prompt=%s input=%s" % (p["id"], p["tokens"]))
    print("[run] output=%s" % proof.output_tokens)
    print("[run] proof open_rows=%d entries=%d ~%d bytes" % (n_open, n_entries, size))
    print("[run] verify: accepted=%s binding=%s integrity=%s"
          % (verdict["accepted"], verdict["binding_ok"], verdict["integrity_ok"]))


def cmd_train(cfg, args):
    kit = build_kit(cfg)
    trainer = RewardTrainer(kit["audit"], skill=args.start, lr=args.lr)
    for _ in range(args.steps):
        rec = trainer.step()
        print("[train] step %02d skill=%.4f reward=%.4f delta=%.4f"
              % (rec["step"], rec["skill"], rec["reward"], rec["delta"]))
    print("[train] reward monotone=%s" % trainer.is_monotone())


def cmd_audit(cfg):
    ab = benchmod.run_attack_bench(cfg)
    print("[audit] substitution_detection=%.4f tamper_detection=%.4f"
          % (ab["substitution_detection"], ab["tamper_detection"]))
    for row in ab["sweep"]:
        print("[audit] open_ratio=%.2f detection=%.4f" % (row["open_ratio"], row["detection"]))


def cmd_commit(cfg):
    kit = build_kit(cfg)
    b = kit["bundle"]
    print(json.dumps({"root": b.hex(), "rows": b.n_rows, "entries": b.n_entries,
                      "vocab": b.vocab, "layers": b.layers, "bits": b.bits}, indent=2))


def cmd_prove(cfg, args):
    kit = build_kit(cfg)
    p = _find_prompt(kit["corpus"], args.prompt)
    proof = prove(kit["bundle"], p["tokens"], kit["world"].model_A,
                  kit["world"].committed_weights, args.ratio, kit["world"].ctx)
    n_open, n_entries, size = _proof_size(proof)
    print(json.dumps({"prompt": p["tokens"], "output": proof.output_tokens,
                      "open_rows": n_open, "open_entries": n_entries,
                      "approx_bytes": size}, indent=2))


def cmd_verify(cfg, args):
    kit = build_kit(cfg)
    p = _find_prompt(kit["corpus"], args.prompt)
    # demonstrate a tamper attack being caught
    from .bench import _tamper_proof
    tp = _tamper_proof(kit["world"], kit["bundle"], p, cfg["prove"]["open_ratio"])
    v = verify(kit["bundle"], tp)
    print(json.dumps({"tampered": True, "accepted": v["accepted"],
                      "binding_ok": v["binding_ok"], "integrity_ok": v["integrity_ok"]}, indent=2))


def cmd_serve(cfg, args):
    from .serving.app import serve
    serve(host=args.host, port=args.port, cfg=cfg)


def build_parser():
    ap = argparse.ArgumentParser(
        prog="proveforge",
        description="Provable inference for LLMs (commit/prove/verify) reference implementation")
    ap.add_argument("--recipe", default=None, help="yaml recipe to merge over defaults")
    sub = ap.add_subparsers(dest="cmd")

    sub.add_parser("doctor")
    sub.add_parser("bench")
    sub.add_parser("modes")
    sub.add_parser("commit")
    sub.add_parser("audit")

    p = sub.add_parser("run")
    p.add_argument("--prompt", default="p00")

    p = sub.add_parser("prove")
    p.add_argument("--prompt", default="p00")
    p.add_argument("--ratio", type=float, default=None)

    p = sub.add_parser("verify")
    p.add_argument("--prompt", default="p00")

    p = sub.add_parser("train")
    p.add_argument("--steps", type=int, default=10)
    p.add_argument("--lr", type=float, default=0.05)
    p.add_argument("--start", type=float, default=0.0)

    p = sub.add_parser("serve")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8431)
    return ap


def main(argv=None):
    ap = build_parser()
    args = ap.parse_args(argv)
    cfg = load_config(args.recipe)
    if args.cmd is None:
        ap.print_help()
        return

    dispatch = {
        "doctor": lambda: cmd_doctor(cfg),
        "bench": lambda: cmd_bench(cfg),
        "modes": lambda: cmd_modes(cfg),
        "commit": lambda: cmd_commit(cfg),
        "audit": lambda: cmd_audit(cfg),
        "run": lambda: cmd_run(cfg, args),
        "prove": lambda: cmd_prove(cfg, args),
        "verify": lambda: cmd_verify(cfg, args),
        "train": lambda: cmd_train(cfg, args),
        "serve": lambda: cmd_serve(cfg, args),
    }
    dispatch[args.cmd]()


if __name__ == "__main__":
    main()
