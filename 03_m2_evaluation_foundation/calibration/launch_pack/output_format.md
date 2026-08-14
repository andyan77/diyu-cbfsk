# 输出格式说明

每评审一个单元，输出**一行** JSON。十二个字段缺一不可。

| 字段 | 类型 | 说明 |
|---|---|---|
| `case_id` | string | 必须是 `CAL-001`—`CAL-090` 之一，且每个至多一条 |
| `candidate_id` | string | 该单元候选输出的 id，形如 `CAND-CAL-001`，从题目里原样抄 |
| `reviewer_role` | string | 你的身份行给的值：`ISOLATED_GPT_REVIEWER` 或 `ISOLATED_CLAUDE_REVIEWER` |
| `model` | string | 你的模型名。同一侧的 90 条必须全部相同 |
| `model_version` | string | 你的模型版本标识。同一侧的 90 条必须全部相同 |
| `review_prompt_hash` | string | 评审 Prompt 的 sha256（由中继方填入，**不要自己编**） |
| `judgment` | string | `ACCEPT` / `REJECT` / `AMBIGUOUS`——这份候选输出算不算落在接受边界内 |
| `score` | number | 落在里面的做得多完整。① 类只允许 0.0／1.0；②③ 类只取 `scoring_anchors.json` 的五档 |
| `hard_gate_result` | object | `{"<HG-id>": "PASS"｜"FAIL"｜"NOT_APPLICABLE"}`，键必须与该单元 `hard_gate_refs` **完全一致** |
| `disagreement_code` | string \| null | 见下表；无异议填 `null` |
| `review_note` | string \| null | 三种情形下必须非空，见下方说明 |
| `reviewed_at` | string | ISO-8601 时间戳 |

## `judgment` 与 `score` 不是一件事

`judgment` 回答「算不算」，`score` 回答「算的那些做得多好」。
**不要**用分数高低表达成立与否——那需要一条及格线，而及格线正是本轮要收集证据去定的东西。

① 类两者必须一致：`ACCEPT`↔`1.0`，`REJECT`↔`0.0`，`AMBIGUOUS`↔`0.0`。
②③ 类不作强制换算：判 `ACCEPT` 也可能只给 0.5（落在区间内但说明不完整）。

## `review_note` 什么时候必须非空

1. `disagreement_code` 非空
2. `judgment` 为 `AMBIGUOUS`
3. `hard_gate_result` 里出现 `FAIL` 或 `NOT_APPLICABLE`

其余情形可填 `null`。

## `disagreement_code` 取值

| 值 | 含义 |
|---|---|
| `AMBIGUOUS_SCENARIO` | 题干信息不足以判定 |
| `BOUNDARY_TOO_WIDE` | 可接受边界宽到无法区分成立与不成立 |
| `BOUNDARY_TOO_NARROW` | 边界窄到把合法解排除在外 |
| `CLASS_MISASSIGNED` | 该单元被归错任务类型 |
| `HARD_GATE_NOT_APPLICABLE` | 所引硬门与本单元无关 |
| `MISSING_INPUT_OBJECT` | 判定所需的输入对象未在 `input_object_refs` 中列出 |

## 一行示例

```json
{"case_id":"CAL-001","candidate_id":"CAND-CAL-001","reviewer_role":"ISOLATED_GPT_REVIEWER","model":"<模型名>","model_version":"<版本>","review_prompt_hash":"<由中继方填入>","judgment":"ACCEPT","score":1.0,"hard_gate_result":{"HG-04":"PASS"},"disagreement_code":null,"review_note":null,"reviewed_at":"2026-08-14T10:00:00Z"}
```

## 交付

- 全部 90 行写入一个文件；分批做的话，把各批结果按 `case_id` 顺序合并成一个文件。
- 每个 `case_id` 只能出现一次，`CAL-001`—`CAL-090` 一个不能少。
- 不要输出 JSON 以外的解释文字。需要说明的，写进 `review_note`。
