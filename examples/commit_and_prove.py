# -*- coding: utf-8 -*-
"""完整往返：承诺 → 证明 → 校验（可验证推理的最小可运行闭环）。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from proveforge.core.quantize import gen_model_weights
from proveforge.core.model import IntegerLLM
from proveforge.core.prover import commit_weights, prove
from proveforge.core.verifier import verify

V, L, B, CTX = 32, 3, 8, 12

weights = gen_model_weights(V, L, B, seed="model:A")
model = IntegerLLM(weights, V, L, B)

# 1) 承诺：只公开根哈希，权重保持隐藏
bundle = commit_weights(weights, V, L, B)
print("[commit] root=%s (entries=%d)" % (bundle.hex(), bundle.n_entries))

# 2) 证明：为 prompt [1,2,3] 生成证明
prompt = [1, 2, 3]
proof = prove(bundle, prompt, model, weights, open_ratio=1.0, max_len=CTX)
print("[prove] output=%s open_rows=%d" % (proof.output_tokens, len(proof.open_rows)))

# 3) 校验：CPU 上重导出挑战并检查
verdict = verify(bundle, proof)
print("[verify] accepted=%s binding=%s integrity=%s"
      % (verdict["accepted"], verdict["binding_ok"], verdict["integrity_ok"]))
