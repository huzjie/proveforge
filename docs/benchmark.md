# 基准与指标

## 四个指标

`python -m proveforge bench` 的实测输出（skill 0→1）：

```text
[bench] skill  binding  integrity  fidelity  accept
[bench] 0.00   0.0000    0.0000      0.0000     0.0000
[bench] 0.25   0.2083    0.0417      0.0000     0.0000
[bench] 0.50   0.5000    0.3750      0.2500     0.2083
[bench] 0.75   0.7917    0.6250      0.5833     0.5000
[bench] 1.00   1.0000    1.0000      1.0000     1.0000
```

- **binding**：被打开权重匹配承诺的比例（抓替换模型）。
- **integrity**：轨迹自洽 + 输出=argmax 的比例（抓伪造轨迹 / 篡改）。
- **fidelity**：输出等于承诺模型真值输出的比例（替换 + 篡改都会拉低）。
- **accept**：验证器整体接受的比例（严格复合，最低）。

四条曲线都严格单调（`monotone: ...=True`）。

## 攻击检出

透明模式（open_ratio=1.0）下：

```text
substitution_detection = 1.0000
tamper_detection      = 1.0000
```

## 声音性曲线

攻击 = 只投毒 4 行权重（局部替换），验证器打开的行越多越可能命中投毒行：

```text
open_ratio=1.00 detection=1.0000
open_ratio=0.50 detection=0.9000
open_ratio=0.25 detection=0.6000
open_ratio=0.10 detection=0.4000
open_ratio=0.02 detection=0.0500
```

## 方法论

- **单调性由构造保证**：每个诚实轴都是 `skill >= 阈值` 的阶跃函数，聚合（均值/合取）保持非递减。
- **干净基线**：替换模型 B 由独立种子生成、篡改 token 用独立随机值，避免「翻转 oracle」导致 skill=0 起点失真。
- **闭式真值**：真值输出由整数模型 A 唯一确定，奖励由程序化校验产生，无学习型奖励模型、无人标注。
