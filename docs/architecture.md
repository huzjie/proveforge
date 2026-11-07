# 架构

## 总览

proveforge 把「可验证推理」拆成一条三段式流水线，模块边界严格对应三个角色：

```text
             ┌──────────────┐         ┌──────────────┐         ┌──────────────┐
             │   prover     │         │   verifier   │         │   world      │
  权重 ─────▶│ commit_weights│────────▶│  verify(proof)│◀───────│  oracle(A/B) │
             │   prove(...) │   proof │              │  裁决   │  corpus/attacks│
             └──────────────┘         └──────────────┘         └──────────────┘
```

- **world**：闭式真值——承诺模型 A、替换模型 B、提示词语料、攻击变体。
- **prover**：`commit_weights`（承诺）+ `prove`（证明）。
- **verifier**：`verify`（CPU 校验，输出 `accepted/binding_ok/integrity_ok`）。
- **training**：`VerifierAudit` 用 skill 驱动诚实度，聚合四项指标；`RewardTrainer` 做单调 skill 训练。

## 核心数据结构

### `CommitmentBundle`

承诺包：持有权重行、Merkle 叶子、预计算的树、根哈希、架构元信息。

```text
weights (L+1) × V × V   →   flatten 成 (L+1)·V 行   →   每行 V 个叶子
                                                        ↓
                                    MerkleTree(叶子) → root(32B) + proof(idx)
```

### `Proof`

一次请求的证明，承载验证器需要的一切：

```text
prompt / output_tokens / open_ratio / open_rows /
openings: {row → [(global_idx, value, siblings)]} / trace
```

### 执行轨迹（trace）

每个解码步记录 `states`（L+1 层激活，每层 V 个整数）、`logits`（V 个整数）、`token`（argmax）。轨迹是证明者「承认自己算了什么」的凭证，校验器据此做点积与 argmax 检查。

## 两条校验路径

### 绑定（binding）

对每个被打开的权重叶子 `(idx, value)`：

```text
verify_proof(root, leaf_hash(idx, value), siblings) == True ？
```

偷换模型 B 的证明者只能揭示 B 的值，而 B 的值哈希不到 A 的承诺根 → 绑定失败。

### 完整（integrity）

对每个解码步、每个被打开的行 `r = (layer, out)`：

```text
dot(open_row_r, states[layer]) mod 2^bits == states[layer+1][out] ？
argmax(logits) == 声称的 token ？
output_tokens[gen_start+i] == trace[i].token ？
```

伪造轨迹（改某个 state 值）或篡改 token 都会让其中一条失败。

## 透明 vs 选择性揭示

| | open_ratio=1.0（透明） | open_ratio<1.0（选择性） |
|---|---|---|
| 打开范围 | 全部权重行 | Fiat-Shamir 挑战采样的子集 |
| 声音性 | 1.0（确定） | 概率式（随打开比例上升） |
| 权重隐藏 | 弱（本次请求全揭示） | 强（只揭示被打开的行） |
| 用途 | 基准/精确断言 | 演示 zk 思路与声音性权衡 |

## 可复用的工程决策

1. **确定性优先**：所有随机（权重、挑战、阈值）都由 `md5(key)` 种子驱动，跨机器/进程可复现——这是「可验证奖励」能做出精确断言的前提。
2. **零依赖**：哈希用 `hashlib`，YAML 用自带的 `yamlish.py` 子集解析器，HTTP 用 `http.server`，不引入任何第三方库。
3. **闭式 oracle**：真值由整数模型 A 的贪婪解码唯一确定，奖励由程序化校验产生，不靠人标注、不靠学习型奖励模型。
