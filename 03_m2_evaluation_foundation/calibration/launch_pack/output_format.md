# 输出格式说明

每评审一例，输出**一行** JSON。九个字段缺一不可。

| 字段 | 类型 | 说明 |
|---|---|---|
| `case_id` | string | 必须是 `CAL-001`—`CAL-090` 之一，且每例至多一条 |
| `reviewer_role` | string | 你的身份行给的值：`ISOLATED_GPT_REVIEWER` 或 `ISOLATED_CLAUDE_REVIEWER` |
| `model` | string | 你的模型名 |
| `model_version` | string | 你的模型版本标识 |
| `review_prompt_hash` | string | 评审 Prompt 的 sha256（由中继方填入，**不要自己编**） |
| `score` | number | 0.0—1.0；① 类只允许 0.0 或 1.0 |
| `hard_gate_result` | object | `{"<HG-id>": "PASS"｜"FAIL"｜"NOT_APPLICABLE"}`，键取该例 `hard_gate_refs` |
| `disagreement_code` | string \| null | 见下表；无异议填 `null` |
| `reviewed_at` | string | ISO-8601 时间戳 |

## `disagreement_code` 取值

| 值 | 含义 |
|---|---|
| `AMBIGUOUS_SCENARIO` | 题干信息不足以判定 |
| `BOUNDARY_TOO_WIDE` | 可接受边界宽到无法区分成立与不成立 |
| `BOUNDARY_TOO_NARROW` | 边界窄到把合法解排除在外 |
| `CLASS_MISASSIGNED` | 该例被归错任务类型 |
| `HARD_GATE_NOT_APPLICABLE` | 所引硬门与本例无关 |
| `MISSING_INPUT_OBJECT` | 判定所需的输入对象未在 `input_object_refs` 中列出 |

## 一行示例

```json
{"case_id":"CAL-001","reviewer_role":"ISOLATED_GPT_REVIEWER","model":"<模型名>","model_version":"<版本>","review_prompt_hash":"<由中继方填入>","score":1.0,"hard_gate_result":{"HG-04":"PASS"},"disagreement_code":null,"reviewed_at":"2026-08-14T10:00:00Z"}
```

## 交付

- 全部 90 行写入一个文件；分批做的话，把各批结果按 `case_id` 顺序合并成一个文件。
- 不要输出 JSON 以外的解释文字。需要说明的，用 `disagreement_code` 表达。
