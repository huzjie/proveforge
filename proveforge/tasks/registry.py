# -*- coding: utf-8 -*-
"""Declarative task catalogue: the five provable-inference capabilities."""
from __future__ import annotations

TASKS = [
    {
        "id": "commit",
        "name": "承诺权重",
        "desc": "对量化后的模型权重计算 Merkle 承诺，仅发布根哈希（隐藏权重）。",
    },
    {
        "id": "prove",
        "name": "生成证明",
        "desc": "运行贪婪解码、记录执行轨迹，按 Fiat-Shamir 挑战选择性打开权重行。",
    },
    {
        "id": "verify",
        "name": "校验证明",
        "desc": "CPU-only 校验：重导出挑战，核对绑定(权重承诺)与完整性(轨迹/argmax)。",
    },
    {
        "id": "audit",
        "name": "可验证奖励",
        "desc": "以 skill 驱动的诚实度模拟证明者，聚合 binding/integrity/fidelity/accept 四项指标。",
    },
    {
        "id": "detect",
        "name": "攻击检出",
        "desc": "衡量验证器对替换模型、token 篡改、局部投毒的检出率与声音性曲线。",
    },
]


def list_tasks():
    return TASKS


def get_task(task_id):
    for t in TASKS:
        if t["id"] == task_id:
            return t
    return None
