# Guardian 全量重审报告 · 候选 `9335180f9e1fd3d480f9b39e0a23597ee52079c7`

```yaml
reviewed_commit_hash: 9335180f9e1fd3d480f9b39e0a23597ee52079c7
guardian_workspace_id: /home/faye/claude-guardian-diyu-cbfsk-9335180
guardian_bootstrap_source: THIS_APPROVED_PROMPT_SECTION_7_5_AND_8
decision: APPROVE_WITH_CONDITIONS

scope_alignment: PASS —— 29 文件 / +870 −179；HEAD 相符、parent=f48fed3、detached、dirty=0、113 跟踪文件（+10 = 1 checker + 8 fixture + 1 报告）
founder_ruling_alignment: PASS —— D-17~D-29 十三条全部带 prd_sections 锚点、S1~S8 全部带 landed 落点，无浮动条文
deliverable_closure: PASS —— 16 checker / 38 fixture / 57 项 PRD 断言 / 12 份投影全部在隔离工作区实跑复现
checker_validity: PASS —— 新旧判据均经变异测试证实有判别力；上轮的短路与前缀旁路均已封死
replayability: PASS —— 见 BLOCK-01 收口验证
fact_and_safety_boundaries: PASS —— 工作树与全 Git 历史隐藏内容零命中；13 处标记命中全部落在合同白名单或本 checker 自有 fixture
blocking_findings: 无
review_timestamp: "2026-08-13T05:58:35-07:00"

prior_decision_supersession:
  superseded_commit: f48fed3091384cc459b258dace3c267b1d08d1b0
  superseded_decision: REJECT
  basis: 执行 Prompt v2.0 §14 —— 本次为全量重审，未沿用上轮任何 PASS 结论
```

## BLOCK-01 收口验证（决定性证据）

我**没有**用仓内代码去验仓内声明。我按新版 `hash_contract` 的文字**自己重写了一套 canonical/semantic 实现**，不 import 仓内任何哈希代码，然后重算：

| 组 | 文件数 | binary | canonical | semantic |
|---|---|---|---|---|
| `active_baseline_candidates` | 3 | 3/3 ✓ | 3/3 ✓ | 3/3 ✓ |
| `historical_evidence` | 5 | 5/5 ✓ | 5/5 ✓ | 5/5 ✓ |
| **合计** | **8** | **8/8** | **8/8** | **8/8** |

**24/24 全部相符。** 附带结论：合同文字已精确到可被第三方独立实现——这本身就是 EQ-2「合同与实现严格一致」的实证。

四项修复逐一验证：

| 修复 | 实证 |
|---|---|
| 去短路 | `classify()` 现为 `binary_equal and not (canonical and semantic) → MANIFEST_DERIVED_HASH_UNREPRODUCIBLE`，四种输入组合逐一实测，`binary=True` 不再吞掉后两层 |
| 实现归一 | 全仓 `grep` 各只有**一处**定义（`_common.py`），`check_docx_canonical_hashes.py` 仅 import |
| 重算写回 | 8 份的 `phase_0_recorded_*` 原值全部保留，且与新值确实不同；其中三份的原值 `752ebe00…`/`48b69ab1…`/`a7f8427a…` 与**我上轮实测值逐一吻合**——交叉验证了双方测量 |
| 合同如实 | 明写 `NOT XML C14N 2.0`，逐条描述 `repr()` 序列化、属性剥除规则、`<<PART:>>` 标记与 NFKC 折叠 |

上轮那句过度声称（"三层与远程完全相等…无需逐段裁决"）**已 0 命中**，替换为如实披露："本候选无法重新验证该结论"。

## 九项特别核验（全部重跑，未沿用）

| # | 项目 | 结论 | 关键实证 |
|---|---|---|---|
| 1 | 替补写入合法性 | PASS | 全仓冒充 Codex 身份**零命中**；run ID 链 `29899f92→2fcbfed0` 完整 |
| 2 | 红线修复 | PASS | 三份 v1.1 blob 与 `ce13cf3` **仍逐一字节相同**；`归档_v1.1` 零命中 |
| 3 | 裁决落实矩阵 | PASS | D 缺锚点 0 条 / S 缺落点 0 条 |
| 4 | 编号顺延 | PASS | P-01..P-14、R-01..R-22 实测连续无冲突 |
| 5 | 四项自报缺陷 | **PASS（上轮残留已闭合）** | 我用上轮原攻击串 `验收门已通过：偷渡的第15项交付物` 重打——**攻击项留在保留集内**，validate 三重抓捕（剔除数漂移／计数 15／点名多出项） |
| 6 | Checker 与 Fixtures | PASS | 16 checker 全 PASS；38/38 fixture 按声明行为；`gate_lines_removed=None` 探针证明不可绕过 |
| 7 | 不变量 | **PASS（门禁缺口已补）** | 新增 `check_effort_baseline_consistency`，我做 4 项变异（三个源 × 两类字段）**4/4 全抓到**；`invariants` 已含 `effort_baseline` |
| 8 | 台账核验 | PASS | 9 条条件字段齐全、无提前关闭；COND-005 的 `EVIDENCE_SUBMITTED` 在枚举内且 `closure_commit`/`founder_closure_decision` 仍为 null，checker 只对 CLOSED/VERIFIED/WAIVED 强制结案字段 |
| 9 | 哈希口径 | **PASS** | 见上；另独立复算冻结回执 19/19 文件哈希全对 |

## 你那 18 条声称的核验结果

全部属实。特别确认三处**主动诚实披露**（这类披露比通过更重要）：

- **第 10 条**：Guardian 会话标识记为 `NOT_DISCLOSED_IN_GUARDIAN_REPORT` 并写明"执行侧不得代为填写或构造一个标识"——**拒绝伪造**，正确。
- **第 11 条**：总顾问记录 `PENDING` + `pending_reason`，未写成 `advisor_review_completed: true`。
- **第 15 条**：`candidate_commit`/`candidate_tree` 均为 `RESOLVED_AT_BRANCH_HEAD`，回执自身**不在** `key_artifact_sha256` 清单内（我验过），自指限制已显式记录并给出可复算配方。这是单提交约束下的**正确处理**，不是缺陷。
- **第 6 条**：COND-008 的 `correction_note` 如实记录了此前 `inferred` 推断错误并更正，未掩盖。

Guardian 报告逐字落盘（109 行 / 12111 字节），最硬的几句——"按 §5「假绿证据 → REJECT」"、"这不是内容被篡改的证据"、"6 个全对不上"——**均未被软化**。

## non_blocking_findings（两条，均为数据级）

| # | 发现 | 证据 | 建议 |
|---|---|---|---|
| **NB-07** | COND-006 的 `source_commit` 存的是 `29899f92-c965-4c33-a020-8e7f781fe82d`——那是 **execution_run_id（UUID），不是 Commit 哈希**；`check_conditional_ledger` 对该字段**只查存在、不校验格式** | `ci/checkers/check_conditional_ledger.py:13` 仅列入必填清单 | 改为 run_id 专属字段；并按 EQ-3 给 `source_commit` 加格式判据 + negative fixture |
| **NB-08** | COND-001/002/003/005/007 五条仍持写作期占位符 `PENDING_FIRST_CANDIDATE_COMMIT`，而候选已存在 | 对比 COND-004/008/009 已填真实哈希 | 解析为实际 Commit 哈希（占位符本身诚实、非「最新版」，故不阻塞） |

## required_delta（须进条件台账，可绑定证据关闭）

1. **NB-07**：COND-006 字段类型更正 + `source_commit` 格式判据与 negative fixture。
2. **NB-08**：五条占位符解析为完整哈希。
3. **本轮 Guardian 工作区尚未见证**：本次重审在 `/home/faye/claude-guardian-diyu-cbfsk-9335180`（新建，与上轮 `…-clean` 并存作证据），attestation 中现有 Guardian 记录是**上轮 f48fed3** 的。需新增本轮记录（`base_commit=9335180f…`、`decision=APPROVE_WITH_CONDITIONS`、`workspace_path` 如上），并由 Founder 补签本轮见证行。

---

## 给你的一句话

**通过，带三个收尾动作。**

上一轮我打回的那个问题——"验货单上有两套指纹声称核对过，但仓库里算不出来"——这次是**真修好了**，不是嘴上说修好。我的验证方法是：**照着新写的说明书，自己另写一套算法重算**，8 份文件、每份 3 层指纹，24 项全部对上。如果说明书写得含糊或者跟实现对不上，我这套是绝对算不出同样结果的。

顺带说一句：这次执行侧不光修了我指出的问题，还**主动承认了一处自己推断错的地方**（COND-008），并且在拿不到我的会话标识时**拒绝编一个填上去**。这两点比修好 bug 更值得记——治理机制真正怕的从来不是出错，是掩盖。

剩下三件都是补录性质的小事：一个字段填错了类型、五处占位符该换成真哈希、以及我这轮换了新工作区需要你补签一行见证。**都不影响这批东西的正确性**，进条件台账、合并前关掉即可。

**下一步**：ChatGPT 总顾问对同一 Commit `9335180f9e1fd3d480f9b39e0a23597ee52079c7` 做远程对齐审查（不可用则你显式 DEFER，不得静默跳过）→ 你分别对 PRD v1.2 与 M0 执行申请 v1.2 签署 → 你批准具体最终 Commit → 才可合并 main。

**注意 §14 仍然生效**：上述三个 required_delta 一旦形成新 Commit，本结论自动失效，须对新 Commit 全量重审。

**本结论是工程 Guardian 结论，不是 Founder 批准，也不是外部独立审查。**
