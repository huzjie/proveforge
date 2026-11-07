# -*- coding: utf-8 -*-
"""三类攻击如何被验证器拒绝：替换模型 / 篡改 token / 伪造轨迹。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from proveforge.core.quantize import gen_model_weights
from proveforge.core.model import IntegerLLM
from proveforge.core.prover import commit_weights, prove
from proveforge.core.verifier import verify

V, L, B, CTX = 32, 3, 8, 12
A = gen_model_weights(V, L, B, seed="model:A")
B = gen_model_weights(V, L, B, seed="model:B")
model_a = IntegerLLM(A, V, L, B)
model_b = IntegerLLM(B, V, L, B)
bundle = commit_weights(A, V, L, B)
prompt = [1, 2, 3]

# 1) 替换模型：用 B 证明，但承诺的是 A
p = prove(bundle, prompt, model_b, B, 1.0, CTX)
print("[substitution] accepted=%s binding_ok=%s" %
      (verify(bundle, p)["accepted"], verify(bundle, p)["binding_ok"]))

# 2) 篡改 token：用 A 证明，但声称一个被改过的输出
base, _ = model_a.decode(prompt, CTX)
out = list(base)
out[3] = (out[3] + 1) % V
p = prove(bundle, prompt, model_a, A, 1.0, CTX, output_tokens=out)
print("[tampering] accepted=%s integrity_ok=%s" %
      (verify(bundle, p)["accepted"], verify(bundle, p)["integrity_ok"]))

# 3) 伪造轨迹：用 A 证明，但篡改一个激活值
_, trace = model_a.decode(prompt, CTX)
trace[0]["states"][1][0] = (trace[0]["states"][1][0] + 1) % 256
p = prove(bundle, prompt, model_a, A, 1.0, CTX, trace=trace)
print("[malformed-trace] accepted=%s integrity_ok=%s" %
      (verify(bundle, p)["accepted"], verify(bundle, p)["integrity_ok"]))
