# 校验提示词（Verify）

任务：在无权重、无 GPU 的前提下校验一份证明。

逐条检查（每条输出通过/不通过 + 原因）：
1. [绑定] 每个被打开权重叶子的 Merkle 路径能否重新导出 COMMITMENT？
2. [完整] 每个打开行的 dot(行, 输入激活) mod 2^bits 是否等于下一层激活？
3. [输出] argmax(logits) 是否等于声称的 token？token 链是否连续？
4. [裁决] 三条全过才 ACCEPT；任何一条失败即 REJECT，并指出攻击类型：
   - substitution（权重不符）→ 偷换模型
   - tampering（token 不符）→ 篡改输出
   - malformed-trace（轨迹不符）→ 伪造轨迹

铁律：只能依据 COMMITMENT 与 PROOF 内可见信息判断，禁止假设「证明者可信」。
