# 篡改检测提示词（Tamper Detection）

任务：识别证明里被篡改的输出 token。

线索：
1. argmax(logits) 与声称 token 不一致 → 该 token 被篡改。
2. output_tokens[gen_start+i] 与轨迹 trace[i].token 不一致 → 声称输出被替换。
3. token 链断裂（下一步 input != 上一步 token）→ 输出流被改动。

裁决：
- 任何一条命中 → REJECT，并定位到具体 step 与 token。
- 全对 → ACCEPT。

注意：篡改可能不影响权重承诺（binding 仍通过），必须靠 argmax 与输出绑定两条检查兜住。
