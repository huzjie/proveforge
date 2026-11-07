# proveforge · 可验证推理（Provable Inference）

> 把「这份回复到底是谁算出来的」变成一道可以用密码学验证的题。
> 零依赖、纯 Python、可运行的 **commit → prove → verify** 参考实现，对标 Anthropic 开源的 **FlashProve**。

---

## 一句话说清这件事

今天的大模型调用里藏着一个**没人能查的信任缺口**：你问一个模型，但没法确认返回的 token 到底是「你付费的那个模型」算出来的，还是被路由服务悄悄换成了一个便宜的模型，或者被中间人在传输里改了一个 token。

FlashProve 的思路是：**让模型提供方先对权重做一个密码学承诺，然后每次回复都附一张「数学收据」，任何人都能在普通 CPU 上校验这张收据，却看不到权重本身。** 本仓库就是这条思路的零依赖参考实现——它不追求 zkSNARK 的完整零知识，而是把「承诺 + 挑战 + 选择性揭示」这条最核心、最可复用的工程骨架原样落地，让你能跑、能改、能照着写。

> ⚠️ 定位说明：本仓库是**教学/参考实现**，代码「经过测试但未经过形式化验证」，与 FlashProve 官方口径一致——它证明的是「协议思路」，不声称任何安全等级。生产级仍需要真正的 zkSNARK 与形式化证明。

---

## 目录

- [它怎么工作（技术拆解）](#它怎么工作技术拆解)
- [快速开始](#快速开始)
- [四个指标与攻击检测](#四个指标与攻击检测)
- [干货块：可复用思路与工程技巧](#干货块可复用思路与工程技巧)
- [CLI 与 HTTP API](#cli-与-http-api)
- [项目结构](#项目结构)
- [运行测试](#运行测试)

---

## 它怎么工作（技术拆解）

### 1. 承诺（Commit）：权重只公开一个根哈希

模型权重被压平成一串整数叶子，每个叶子 `leaf_hash(idx, value) = sha256(0x00 || idx || value)`，再按 Merkle 树层层哈希到**一个 32 字节的根**。这个根就是承诺：

- **隐藏权重**：根是单向哈希，从根反推不出任何权重；
- **绑定权重**：换任何一行、任何一个值，根都会变。

架构（词表、层数、位宽）是公开的，隐藏的是权重的具体数值——这正是 FlashProve 文档里写的「承诺隐藏权重、不隐藏架构」。

```python
from proveforge.core.prover import commit_weights
bundle = commit_weights(weights, vocab=32, layers=3, bits=8)
print(bundle.hex())          # 只有这一个根哈希需要公开
```

### 2. 证明（Prove）：跑一遍解码，把轨迹和「被打开的行」一起交出去

提供方正常跑贪婪解码，记录每一步的**执行轨迹**（每一层的激活值、logits、argmax 出的 token），然后用 **Fiat-Shamir** 决定「打开哪些权重行」：

```text
challenge = sha256( 承诺 || prompt || 输出 token || 轨迹摘要 )
open_rows = 由 challenge 种子的伪随机采样决定
```

证明者无法事先知道会被打开哪些行，因此想偷换模型（substitution）或篡改输出（tampering）的人，无法只伪造「不会被查到的部分」。这是把「交互式挑战」变成「非交互式」的经典手法。

### 3. 校验（Verify）：CPU 上做两件便宜的事

验证器（无 GPU、无权重）拿到证明后，重导出同一个 challenge，然后只做两类检查：

1. **绑定检查**：被打开的权重叶子的 Merkle 路径能否重新导出承诺根（抓「偷换模型」）；
2. **完整性检查**：轨迹是否自洽（`dot(打开的行, 上一层激活) == 下一层激活`）、`argmax(logits)` 是否等于声称的输出 token、token 链是否连续（抓「篡改 token」「伪造轨迹」）。

**证明贵、校验便宜**——这是整套设计能被当审计工具用的关键。

### 关键参数（本参考实现的默认值）

| 参数 | 值 | 说明 |
|---|---|---|
| vocab | 32 | 词表大小（= 嵌入维度，one-hot） |
| layers | 3 | 隐藏线性层（另有 1 层输出头） |
| bits | 8 | 整数模 `2^8 = 256`（权重量化位宽） |
| ctx | 12 | 最大解码长度 |
| open_ratio | 1.0 | `1.0`=透明证明（全开、soundness=1.0）；`<1.0`=Fiat-Shamir 选择性揭示 |
| 承诺规模 | 4096 叶子 / 128 行 | 根 32 字节 |
| 证明规模 | ~1 MB | 打开全部 4096 个权重叶子 |

---

## 快速开始

```bash
# 零依赖，Python 3.9+ 即可
git clone https://github.com/huzjie/proveforge.git
cd proveforge

# 冒烟自检：诚实证明者在 skill=1.0 时四项指标应全部命中 1.0
python -m proveforge doctor

# 完整基准：四项指标的 skill 曲线 + 两类攻击检出率 + 声音性曲线
python -m proveforge bench

# 跑单测
python -m unittest discover -s tests -t .
```

`doctor` 的输出应形如：

```text
[doctor] vocab=32 layers=3 bits=8 ctx=12 prompts=24
[doctor] commitment root=30338d0d... (rows=128 entries=4096)
[doctor] binding=1.0000 integrity=1.0000 fidelity=1.0000 accept=1.0000
[doctor] OK (fully honest prover reproduced across all four metrics)
```

---

## 四个指标与攻击检测

用 `skill`（0.0=不诚实的基线证明者，1.0=完全诚实）驱动证明者的三个**独立诚实轴**：是否偷换模型、是否伪造轨迹、是否篡改 token。四条指标都是 `0 → 1` 的单调曲线：

| skill | binding（模型绑定） | integrity（轨迹完整） | fidelity（输出保真） | accept（审计通过） |
|---|---|---|---|---|
| 0.00 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 0.25 | 0.2083 | 0.0417 | 0.0000 | 0.0000 |
| 0.50 | 0.5000 | 0.3750 | 0.2500 | 0.2083 |
| 0.75 | 0.7917 | 0.6250 | 0.5833 | 0.5000 |
| 1.00 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |

（以上为 `python -m proveforge bench` 的实测输出，非手写估算。）

- **binding** 抓「偷换便宜模型」——权重对不上承诺；
- **integrity** 抓「伪造轨迹 / 篡改 token」——点积对不上、argmax 对不上；
- **fidelity** 抓「输出不是承诺模型该有的输出」——替换 + 篡改都会拉低它；
- **accept** 是三者全过的严格复合，所以曲线最低。

**攻击检出**（透明模式下 soundness=1.0）：

```text
substitution_detection = 1.0000   # 偷换模型 100% 被拒
tamper_detection      = 1.0000    # 篡改 token 100% 被拒
```

**声音性曲线**（Fiat-Shamir 选择性揭示的代价，攻击=只投毒 4 行权重）：

| open_ratio | 1.0 | 0.5 | 0.25 | 0.1 | 0.02 |
|---|---|---|---|---|---|
| detection | 1.00 | 0.90 | 0.60 | 0.40 | 0.05 |

打开的行越多、越接近全开，抓到投毒行的概率越高——这就是「证明复杂度 ↔ 声音性」的可量化权衡。

---

## 干货块：可复用思路与工程技巧

### 干货块 1 · 把「证明某事」翻译成「承诺 + 挑战 + 选择性揭示」

这是整件事最值钱的三段式骨架，能迁移到任何「我需要证明我算对了、但不想把算的过程全公开」的场景：

1. **承诺**：把私有数据（权重/状态/输入）哈希成一棵 Merkle 树的根，只公开根。
2. **挑战**：用 `H(公开信息 + 输出)` 生成不可预测的随机挑战，决定揭示哪些位置。
3. **选择性揭示**：只打开被挑战命中的位置 + 它们的 Merkle 兄弟路径，校验方重导出根 + 重算局部关系。

校验方**永远拿不到全部私有数据**，但能确信「没造假」。证明贵、校验便宜，是非对称成本设计的关键。

### 干货块 2 · 可直接复用的提示词模板（给做「可验证/可审计 AI」的人）

把「可验证奖励」这件事喂给模型时，这套提示词模板能直接拿去改：

```markdown
你是「可验证推理审计器」。给定：
- COMMITMENT：模型权重的 Merkle 根哈希（权重不可见）
- PROOF：证明者声称的输出 token + 打开的行 + 兄弟路径 + 执行轨迹

请逐条校验，只输出通过/不通过与原因：
1. [绑定] 每个被打开权重叶子的 Merkle 路径是否重新导出 COMMITMENT？
2. [完整] 每个打开行的 dot(行, 输入激活) mod 2^bits 是否等于下一层激活？
3. [输出] argmax(logits) 是否等于声称的 token？token 链是否连续？
4. [裁决] 三条全过才 ACCEPT，任何一条失败即 REJECT 并指出攻击类型：
   substitution（权重不符）/ tampering（token 不符）/ malformed-trace（轨迹不符）。

铁律：只能依据 COMMITMENT 与 PROOF 内可见信息判断，禁止假设「证明者可信」。
```

### 干货块 3 · 踩过的坑与解法

| 坑 | 现象 | 解法 |
|---|---|---|
| Merkle 树把「单节点层」也做了奇偶补齐 | `while True` 里 `len(layer)==1` 的 break 永远不触发，无限循环 | 循环条件改为 `while len(layer) > 1`，根层在循环外追加 |
| 验证器漏了「声明输出 vs 轨迹 token」的绑定 | 篡改 token 后 integrity 仍恒为 1.0，tamper_detection=0 | 显式加 `output_tokens[gen_start+i] == trace[i].token` 检查 |
| 每个叶子单独 `merkle_proof` 都重建整棵树 | 4096 叶子 × O(n) = O(n²)，单次证明数分钟 | 预计算每层一次（`MerkleTree` 类），单叶子证明 O(log n) |
| 基线用「翻转 oracle」而非「独立抛硬币」 | skill=0 起点不是干净的 ~0 | 替换模型 B 用独立种子生成、篡改 token 用独立随机值 |

### 干货块 4 · 可复用配置片段（`recipes/` 直接改）

`recipes/selective.yaml` 演示如何打开「选择性揭示」模式：

```yaml
prove:
  open_ratio: 0.5      # 只打开 50% 的权重行：部分隐藏权重，声音性降为概率式
```

`python -m proveforge bench --recipe recipes/selective.yaml` 即可看到 soundness 曲线下移。

---

## CLI 与 HTTP API

```bash
python -m proveforge doctor          # 冒烟自检
python -m proveforge bench           # 完整基准
python -m proveforge modes           # 打印模型/承诺/能力清单
python -m proveforge commit          # 输出承诺 JSON
python -m proveforge run --prompt p00          # 诚实证明 + 校验一轮
python -m proveforge prove --prompt p00 --ratio 0.5
python -m proveforge verify --prompt p00        # 演示篡改攻击被拒
python -m proveforge train --steps 10           # 单调 skill 训练
python -m proveforge audit                       # 攻击检出 + 声音性曲线
python -m proveforge serve --port 8431           # 起 HTTP 服务
```

HTTP API（零依赖，`http.server`）：

```bash
curl http://127.0.0.1:8431/health        # {"status":"ok","service":"proveforge"}
curl http://127.0.0.1:8431/v1/info       # 模型 + 承诺元信息
curl -X POST http://127.0.0.1:8431/v1/prove -d '{"prompt":"p00","open_ratio":1.0}'
curl -X POST http://127.0.0.1:8431/v1/verify -d '{"prompt":"p00"}'
```

---

## 项目结构

```text
proveforge/
├── core/          # quantize(量化) / merkle(承诺) / model(整数LLM)
│                  # fiat_shamir(挑战) / prover(承诺+证明) / verifier(校验)
├── world/         # oracle(承诺模型A + 替换模型B) / corpus(提示词) / attacks(攻击)
├── training/      # reward(可验证奖励审计) / trainer(单调 skill)
├── serving/       # 零依赖 HTTP API
├── tasks/         # 五项能力清单
├── utils/         # rng(确定性随机) / hashing / linalg / yamlish(极简YAML)
├── cli.py bench.py kit.py config.py
├── docs/          # 架构 / 起步 / API / 基准 / 攻击 / 可验证推理
├── prompts/       # 可复用提示词
├── recipes/       # yaml 配方（full/transparent/selective/...）
├── examples/      # 可运行的示例脚本
├── tests/         # 63 个单元测试
├── Dockerfile  docker-compose.yml  deploy/  .github/workflows/ci.yml
```

---

## 运行测试

```bash
python -m compileall -q proveforge tests    # 编译零错
python -m unittest discover -s tests -t .   # 63 测试全绿
```

覆盖：Merkle 树的根/证明/篡改检测、整数模型解码确定性、prove/verify 往返、三类攻击被拒、四指标单调性、攻击检出率、声音性曲线。

---

## 许可

MIT。代码「经过测试、未经验证」——协议思路可复用，安全等级不作任何声明。

**相关阅读**：Anthropic *「Progress on provable inference for large language models」*（2026-11-02）、`anthropics/FlashProve`（Apache-2.0）。
