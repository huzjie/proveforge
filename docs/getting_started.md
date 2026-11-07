# 快速开始

## 前置条件

- Python 3.9+（无任何第三方依赖）

## 安装

```bash
git clone https://github.com/huzjie/proveforge.git
cd proveforge
```

无需 `pip install`，纯标准库。

## 三步跑通

```bash
# 1. 冒烟自检
python -m proveforge doctor

# 2. 完整基准（四项指标 + 攻击检出 + 声音性曲线）
python -m proveforge bench

# 3. 单元测试
python -m unittest discover -s tests -t .
```

## 最小可运行示例

```python
from proveforge.core.quantize import gen_model_weights
from proveforge.core.model import IntegerLLM
from proveforge.core.prover import commit_weights, prove
from proveforge.core.verifier import verify

V, L, B, CTX = 32, 3, 8, 12
weights = gen_model_weights(V, L, B, seed="model:A")
model = IntegerLLM(weights, V, L, B)

bundle = commit_weights(weights, V, L, B)          # 承诺：只公开根
proof = prove(bundle, [1, 2, 3], model, weights, 1.0, CTX)  # 证明
print(verify(bundle, proof))                        # 校验 → accepted=True
```

## 各命令含义

| 命令 | 作用 |
|---|---|
| `doctor` | 诚实证明者四项指标应全部命中 1.0 |
| `bench` | skill 曲线 + 两类攻击检出 + 声音性扫描 |
| `modes` | 打印模型/承诺/能力清单 |
| `commit` | 输出承诺 JSON |
| `prove` | 为某条 prompt 生成证明 |
| `verify` | 演示篡改攻击被拒 |
| `run` | 诚实证明 + 校验一轮 |
| `train` | 单调 skill 训练（reward 单调上升） |
| `audit` | 攻击检出 + 声音性曲线 |
| `serve` | 起 HTTP 服务（见 api.md） |

## Docker

```bash
docker build -t proveforge .
docker run --rm proveforge python -m proveforge doctor
# 或
docker compose up
```
