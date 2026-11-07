# -*- coding: utf-8 -*-
"""四项指标随 skill 的单调曲线（可验证奖励）。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from proveforge.config import load_config
from proveforge.kit import build_kit

kit = build_kit(load_config())
audit = kit["audit"]

print("%-6s %-9s %-10s %-9s %-8s" % ("skill", "binding", "integrity", "fidelity", "accept"))
for s in [0.0, 0.25, 0.5, 0.75, 1.0]:
    r = audit.audit_skill(s)
    print("%-6.2f %-9.4f %-10.4f %-9.4f %-8.4f"
          % (s, r["binding"], r["integrity"], r["fidelity"], r["accept"]))
