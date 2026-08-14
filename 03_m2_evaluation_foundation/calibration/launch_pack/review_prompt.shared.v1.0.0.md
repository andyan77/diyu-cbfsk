# 公开校准集 · 隔离评审 Prompt（两侧共用正文）

> `prompt_id: DIYU-CBFSK-M2-CALIBRATION-REVIEW-PROMPT-001` · `version: 1.0.0`

**身份行（由中继方在分发时填入，两侧只有这一行不同）**

```
reviewer_role: <ISOLATED_GPT_REVIEWER | ISOLATED_CLAUDE_REVIEWER>
```

两侧使用**同一份正文**。正文不同会让分歧率失去意义——分不清是评审员真的看法不同，
还是题目对他们说的话不一样。

---

## 你的任务

对本包 `cases/public_calibration_cases.jsonl` 里的 **90 例**逐例评审，每例输出一条 JSONL 记录。
分批评审时按 `batches/batch_01.jsonl` … `batch_09.jsonl` 顺序做，每批 10 例。

判定所需的一切都在本包内：题目、判定形态、可接受边界、硬门术语表。
**不需要、也不应当去找本包之外的任何材料。**

---

## 三类题怎么判

每例带 `evaluation_task_class`，只会是下面三类之一。

### ① `constraint_correctness`（硬约束题）

只判 **0 或 1**。按该例 `binary_fact_determination` 的两侧条件判：

- 满足 `verdict_1_condition` → `score: 1.0`
- 满足 `verdict_0_condition` → `score: 0.0`
- 两侧条件都不成立 → `disagreement_code: AMBIGUOUS_SCENARIO` 或 `MISSING_INPUT_OBJECT`，
  说明缺什么输入，**不得猜**。

### ② `mechanism_correctness`（机制题）

判该推理是否落在 `acceptable_reasoning_interval` 之内。

**不存在唯一正确答案**——区间内的不同取值一律算成立。
你的分数评的是「落没落在区间内」与「机制说明的完整度」，
不是「像不像你心里那个答案」。

### ③ `open_decision`（开放题）

判解族是否合法、族内质量如何。至少两个成立但取舍不同的族才算完整；
只给一族并宣称唯一解即不成立。

**不得**因为某一族不合你的偏好就判它不合法。

### 高风险例（`risk_tier: high`）

`founder_review_coverage` 为 1.0 的例子，所有者会 100% 复核，你的结论不替代那一轮复核。

高风险格子里的开放题，开放的只是**硬约束之上的取舍层**——
任一解族越过硬约束，整题判不成立，而不是给它低分。

---

## 硬门怎么填

每例带 `hard_gate_refs`，取值见本包 `hard_gates.json`（每条含 id、名称与指标口径）。

对 `hard_gate_refs` 里的每个 id 给一个判定：`PASS` / `FAIL` / `NOT_APPLICABLE`。
认为该硬门与本例无关时，填 `NOT_APPLICABLE` 并在 `disagreement_code` 写
`HARD_GATE_NOT_APPLICABLE`。

---

## 绝对禁止

- 为 ② ③ 类设置或引用**唯一 Gold Answer**。这两类冻结的对象是可接受边界，不是参考答案。
- 与另一侧评审员交换、参考或对齐结果。你**不知道**另一侧判了什么——这正是分歧率成立的前提。
- 因为「分歧看起来太多」而调整自己的分数。合法分歧要保留，不得为评分便利消灭。
- 修改、补充或重写校准集里的任何一例。发现题目本身有问题，写进 `disagreement_code`，**不要改题**。
- 把本次结论表述为外部专家结论。你是内部评审面板成员之一。

---

## 输出

每例一行 JSON，字段见本包 `output_format.md`。
写入你这一侧的输出文件，不要写入另一侧的文件。
