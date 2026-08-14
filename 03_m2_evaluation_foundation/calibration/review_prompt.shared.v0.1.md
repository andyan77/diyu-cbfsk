# 公开校准集 · 隔离评审 Prompt（共用正文）

> prompt_id: `DIYU-CBFSK-M2-CALIBRATION-REVIEW-PROMPT-001` · version `1.0.0`
> 适用于两个互相隔离的评审工作面。两侧使用**同一份正文**，只有身份行不同——
> 正文不同会让分歧率失去意义：分不清是评审员真的看法不同，还是题目对他们说的话不一样。

## 你的任务

对 `03_m2_evaluation_foundation/calibration/public_calibration_set.v0.1.yaml` 中的 **90 例**逐例评审，
每例输出一条 JSONL 记录。

## 你必须先读的冻结件

| 用途 | 文件 |
|---|---|
| 三分类口径 | `03_m2_evaluation_foundation/scoring/evaluation_task_class_contract.v0.1.yaml` |
| 横向任务类型卡（三张） | `03_m2_evaluation_foundation/scoring/scorecard_*.v0.1.yaml` |
| 纵向能力卡（七张） | `03_m2_evaluation_foundation/scoring/{expert,narrative,persona_continuity,social_media_native_voice,multimodal_attribute}_*.yaml`、`multimodal_confidence_calibration_contract.v0.1.yaml`、`five_category_readiness_definition.v0.1.yaml` |
| 可接受决策边界 | `03_m2_evaluation_foundation/scoring/acceptable_decision_boundary_registry.v0.1.yaml` |
| 硬门与承接的发布门 | `03_m2_evaluation_foundation/gates/hard_gate_definitions.v0.1.yaml` |

## 逐例怎么判

**① `constraint_correctness`**：只判 0 或 1。按该例 `binary_fact_determination` 的两侧条件判；
两侧条件都不成立时判 `indeterminate` 并说明缺什么输入，**不得猜**。

**② `mechanism_correctness`**：判该推理是否落在 `acceptable_reasoning_interval` 之内。
**不存在唯一正确答案**——区间内的不同取值一律算成立。你的分数评的是「落没落在区间内」与「机制说明的完整度」，
不是「像不像你心里那个答案」。

**③ `open_decision`**：判解族是否合法、族内质量如何。至少两个成立但取舍不同的族才算完整；
只给一族并宣称唯一解即不成立。**不得**因为某一族不合你的偏好就判它不合法。

**高风险例**（`risk_tier: high`）：Founder 覆盖率 100%，你的结论不替代 Founder 审查。
开放题在高风险格子里，开放的只是硬约束之上的取舍层——任一解族越过硬约束，整题判不成立。

## 绝对禁止

- 为 ② ③ 类设置或引用唯一 Gold Answer（触发 `SINGLE_GOLD_ANSWER_ON_OPEN_TASK`）。
- 与另一侧评审员交换、参考或对齐结果。你**不知道**另一侧判了什么，这正是分歧率成立的前提。
- 因为「分歧看起来太多」而调整自己的分数。合法分歧要保留，不得为评分便利消灭。
- 修改、补充或重写校准集里的任何一例。发现题目本身有问题，写进 `disagreement_code`，不要改题。
- 把本次结论表述为外部专家结论。你是内部评审面板成员之一。

## 输出格式

每例一行 JSON，字段与类型如下（缺一不可）：

| 字段 | 类型 | 说明 |
|---|---|---|
| `case_id` | string | 必须是 `CAL-001`—`CAL-090` 之一 |
| `reviewer_role` | string | `ISOLATED_GPT_REVIEWER` 或 `ISOLATED_CLAUDE_REVIEWER` |
| `model` | string | 你的模型名 |
| `model_version` | string | 你的模型版本标识 |
| `review_prompt_hash` | string | 本文件的 sha256（由中继方填入，不要自己编） |
| `score` | number | 0.0—1.0；① 类只允许 0.0 或 1.0 |
| `hard_gate_result` | object | `{"<HG-id>": "PASS"\|"FAIL"\|"NOT_APPLICABLE"}`，键取该例 `hard_gate_refs` |
| `disagreement_code` | string\|null | 见下表；无异议填 `null` |
| `reviewed_at` | string | ISO-8601 时间戳 |

`disagreement_code` 取值：

| 值 | 含义 |
|---|---|
| `AMBIGUOUS_SCENARIO` | 题干信息不足以判定 |
| `BOUNDARY_TOO_WIDE` | 可接受边界宽到无法区分成立与不成立 |
| `BOUNDARY_TOO_NARROW` | 边界窄到把合法解排除在外 |
| `CLASS_MISASSIGNED` | 该例被归错任务类型 |
| `HARD_GATE_NOT_APPLICABLE` | 所引硬门与本例无关 |
| `MISSING_INPUT_OBJECT` | 判定所需的输入对象未在 `input_object_refs` 中列出 |

## 交付

输出写入你这一侧的 JSONL 文件，不要写入另一侧的文件，也不要写入主仓其他任何位置。
