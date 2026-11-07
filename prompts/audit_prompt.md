# 可验证奖励提示词（Audit）

任务：用 skill 驱动的诚实度模拟证明者，聚合四项指标，产出一条单调 0→1 的可验证奖励曲线。

诚实轴（每个 slot 用 skill 与确定性阈值比较）：
- model：skill >= t_model 才用承诺模型 A，否则用独立替换模型 B。
- trace：skill >= t_trace 才报告真实轨迹，否则伪造某个激活值。
- token：skill >= t_token 才报告真实输出，否则篡改一个 token。

四项指标：
- binding = 权重匹配承诺的比例（抓替换）
- integrity = 轨迹自洽 + 输出=argmax 的比例（抓伪造/篡改）
- fidelity = 输出等于真值输出的比例（抓输出偏差）
- accept = 验证器整体接受的比例（严格复合）

铁律：
- 单调性由「阈值阶跃」构造保证，不得用「对+1 错-1」的抖动信号。
- 低 skill 的基线必须「独立抛硬币」，不得「翻转 oracle」（否则起点失真）。
