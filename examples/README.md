# Examples

每个脚本都可直接运行（`python examples/<name>.py`）。脚本头部已做 `sys.path` 引导，无需安装即可导入包。

| 脚本 | 演示内容 |
|---|---|
| `commit_and_prove.py` | 承诺权重 → 生成证明 → CPU 校验的完整往返 |
| `detect_attacks.py` | 三类攻击（替换/篡改/伪造轨迹）如何被拒 |
| `skill_curve.py` | 四项指标随 skill 的单调曲线 |
| `http_api.py` | 用 `urllib` 调用 HTTP API 的客户端示例 |

从项目根运行：

```bash
python examples/commit_and_prove.py
python examples/detect_attacks.py
python examples/skill_curve.py

# HTTP 示例（另开终端先起服务）：
python -m proveforge serve --port 8431
python examples/http_api.py
```
