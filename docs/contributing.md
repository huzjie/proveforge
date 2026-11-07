# 贡献指南

## 开发环境

- Python 3.9+，零第三方依赖
- 改动后跑：`python -m compileall -q proveforge tests && python -m unittest discover -s tests -t .`

## 代码约定

1. **确定性优先**：一切随机由 `utils/rng.py` 的 `md5(key)` 种子驱动，禁止直接使用全局 `random`。
2. **零依赖**：不引入第三方库；YAML 用 `utils/yamlish.py` 子集解析器，HTTP 用标准库 `http.server`。
3. **闭式真值**：任何新指标都应有对应的确定性 oracle，不接受「学习型奖励模型」或人工标注作为真值。
4. **单调基准铁律**：新增 skill 指标必须满足 `0 → 1` 单调（由阈值阶跃构造保证），并纳入 `check_monotone`。
5. **字符串字面量**：代码中的换行用真实换行，避免在生成器/字符串里写 `\\n`（本项目源码为直接书写的普通 Python）。

## 测试

- 新模块配对应 `tests/test_*.py`。
- 运行：`python -m unittest discover -s tests -t .`。

## 提交规范

- 单一职责提交，提交信息描述动机。
- 涉及基准数字的改动需先跑 `bench` 再用真实测量更新文档表格（禁止手写估算）。

## 安全声明

本仓库是教学/参考实现，代码「经过测试、未经验证」。任何安全等级声明均不成立；生产环境请使用经过形式化验证的 zkSNARK 实现。
