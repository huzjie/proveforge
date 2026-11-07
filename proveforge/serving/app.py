# -*- coding: utf-8 -*-
"""Zero-dependency HTTP API over the prove/verify pipeline (http.server based).

Endpoints:
  GET  /health          -> liveness
  GET  /v1/info         -> model + commitment metadata
  POST /v1/commit       -> the weight-hiding commitment
  POST /v1/prove        -> a proof for {prompt, open_ratio}
  POST /v1/verify       -> verify a {prompt, tampered} proof (detection demo)
"""
from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer

from ..kit import build_kit
from ..core.prover import prove
from ..core.verifier import verify


def _find_prompt(corpus, pid):
    for p in corpus:
        if p["id"] == pid:
            return p
    return corpus[0]


def build_app(cfg):
    kit = build_kit(cfg)

    class Handler(BaseHTTPRequestHandler):
        def _send(self, code, obj):
            body = json.dumps(obj).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.path == "/health":
                return self._send(200, {"status": "ok", "service": "proveforge"})
            if self.path == "/v1/info":
                b = kit["bundle"]
                return self._send(200, {
                    "vocab": b.vocab, "layers": b.layers, "bits": b.bits,
                    "commitment": b.hex(), "rows": b.n_rows, "entries": b.n_entries,
                })
            return self._send(404, {"error": "not found"})

        def do_POST(self):
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length) if length else b"{}"
            try:
                data = json.loads(raw.decode("utf-8"))
            except Exception:
                return self._send(400, {"error": "bad json"})

            if self.path == "/v1/commit":
                b = kit["bundle"]
                return self._send(200, {"commitment": b.hex(), "entries": b.n_entries})
            if self.path == "/v1/prove":
                p = _find_prompt(kit["corpus"], data.get("prompt", "p00"))
                ratio = float(data.get("open_ratio", cfg["prove"]["open_ratio"]))
                proof = prove(kit["bundle"], p["tokens"], kit["world"].model_A,
                              kit["world"].committed_weights, ratio, kit["world"].ctx)
                return self._send(200, {
                    "prompt": p["tokens"], "output": proof.output_tokens,
                    "open_rows": len(proof.open_rows),
                })
            if self.path == "/v1/verify":
                p = _find_prompt(kit["corpus"], data.get("prompt", "p00"))
                from ..bench import _tamper_proof
                tp = _tamper_proof(kit["world"], kit["bundle"], p, cfg["prove"]["open_ratio"])
                v = verify(kit["bundle"], tp)
                return self._send(200, {
                    "tampered": True, "accepted": v["accepted"],
                    "binding_ok": v["binding_ok"], "integrity_ok": v["integrity_ok"],
                })
            return self._send(404, {"error": "not found"})

        def log_message(self, *args):
            pass

    return Handler


def serve(host="127.0.0.1", port=8431, cfg=None):
    if cfg is None:
        from ..config import load_config
        cfg = load_config()
    handler = build_app(cfg)
    server = HTTPServer((host, port), handler)
    print("[serve] proveforge API listening on http://%s:%d" % (host, port))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()
