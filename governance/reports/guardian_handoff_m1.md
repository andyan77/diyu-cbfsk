# Guardian 交接包 · M1 里程碑收口审查

> 候选 Commit `37f636c73dac1be7457dfc951984b43532056804`（分支 `m1/candidate-freeze`）
> 里程碑 M1 · 封套 `MILESTONE_PLAN_M1` · 连跑授权 `DIYU-CBFSK-FOUNDER-M1-RUNTHROUGH-001`
> 本包由执行侧生成，**不是审查结论**。Guardian 独立复核后自行出结论。

## 1. 你要审的是什么

M1 的三个执行包全部落在 `m1/candidate-freeze` 分支上，相对 `origin/main`（`6499431c66f7bf4a234bd830ee4c810e1ac78694`，你上轮审过并已合并的状态）有两个新 Commit：

| Commit | 包 | 内容 |
|---|---|---|
| `8ce837a4569565299be3f8dacf65121bb0908a44` | M1-EP02 | 五类品类适配合同 + 跨品类冲突优先级 + 第 21 个 checker |
| `37f636c73dac1be7457dfc951984b43532056804` | M1-EP03 | 补齐 Brief 未交付两项 + 终检判据扩展 + 接口交接 + 报告与 Receipt + 候选冻结 |

M1-EP01 的三个 Commit（`38d13b7dc451ee2372aee8ca3ca2d49c23866c33`、`c714732ff9a303719dde7a5a70bfa9c2fc36d042`、`6499431c66f7bf4a234bd830ee4c810e1ac78694`）已在 main 上，本轮不重复提交，但它们的产出在本轮的审查范围内（M1 是一个里程碑，不是三次独立交付）。

## 2. 执行侧自检数值（请独立复算，不要采信本表）

```
21 个确定性 checker            PASS / 0 FAIL      python3 ci/run_all_checks.py
131 份判据层 fixture           全部按声明行为      （22 正 / 109 反）
36 份结构层实例 fixture        全部按声明行为      （18 VALID / 18 INVALID）
check_prd_v1_2 --require-archive   62 PASS
compile_role_instructions --check  12 files, drift=0
提交门控                       158 条断言（EP03）/ 256 条断言（EP02）
```

## 3. 执行侧主动披露（这几处最值得你盯）

**① M1 期间发现两处自身缺陷，都不是 CI 报出来的。**

- **EP01 的 `WOMENSWEAR_RULE_OVERREACH` 是假绿**：`collect()` 读 `object_coverage_map.category_defaults.womenswear_rules_apply_to_other_categories_by_default`，**该键全仓不存在**，恒为 `False`，判据在真实仓库上永不触发。N76 能触发它，只因 fixture 手写了 `true`。EP02 把判据迁到 `check_m1_category_adapters` 改读五份适配器真实声明。
  **请复核**：迁移后是否真的读到了真源；旧实现与死键是否彻底删除；N76 是否只触发这一条判据。
- **EP01 漏交 Brief 第 3 项**（`human_visual_profile.schema` / C-04），也未登记在 `not_delivered_in_ep01`。EP03 补 Schema + 补 `BRIEF_DELIVERABLE_*` 判据。
  **请复核**：Brief 21 项是否真的逐项落地；判据的条数真源是否取自 Brief 本身而不是覆盖映射表自己声明的数字。

**② 新增元判据 `M1_ACCEPTANCE_JUDGEMENT_NOT_WIRED` 有明确的能力边界，我们没有夸大它。**
它守「判据被删或从没人跑过」，**守不住**「判据还在、fixture 也在，但 `collect()` 喂给它的值恒假」——即上面①那一类。报告 §2 与回执 `self_disclosure` 均写明这条边界。**请复核我们是否在别处把它说成了更强的保证。**

**③ 动了一份 M0 冻结交付物。** `m2_evaluation_freeze_brief.md` 追加第 10 节（M1 接口交接），授权来自 `DIYU-CBFSK-FOUNDER-M1-RUNTHROUGH-001`，已在 M0 回执 `post_m0_authorized_modifications` 登记，`artifact_sha256` 保持 M0 交付当时的值未改写。
**请复核**：新节是否只新增、未放宽 M2 的 18 项清单 / 10.2 阈值 / D-28 口径 / 高风险全审 100% 不可抽样中的任何一条。

**④ EP03 Prompt 要求「M3 问题系统 Brief 按 M1 真实产出更新」，但仓内不存在该文件。** 我们没有新建（新建等于在未授权下先行规划 M3），改为把 M1→M3 接口面标 `INTERFACE_ONLY` 落在交接件里，并登记为 `OI-M1-03` 交 Founder。
**请复核**：这算不算「静默绕过指令」。执行侧认为不算——因为已显式登记并路由，而不是当作已完成。这一判断本身请你独立评估。

**⑤ 连跑授权裁决 `DIYU-CBFSK-FOUNDER-M1-RUNTHROUGH-001` 是执行侧转录归档，不是 Founder 亲自落盘的文件。** 文件头 `transcription_note` 已如实标注。它之所以必须存在，是因为改 M0 冻结件需要绑定具名授权。**请复核转录是否忠实于 Founder 原话，有无自我扩权。**

**⑥ 一次自我更正**：起草连跑裁决时写入了一个**编造的** 40 位基线哈希（非仓内真实 Commit），当场发现并更正为 `8ce837a4569565299be3f8dacf65121bb0908a44`，门控加断言核对。已在此披露，不因「最终结果正确」而略过。

## 4. 建议的对抗性探针

1. 把 `object_coverage_map` 的 `brief_deliverable_coverage.count` 改成 20 → 应报 `BRIEF_DELIVERABLE_COUNT_DRIFT`。
2. 删掉某份适配器的 `conflict_priority_ref` → 应报 `CONFLICT_PRIORITY_NOT_REFERENCED`。
3. 复制一份冲突优先级表到别处（保留 `contract_id`）→ 应报 `CONFLICT_PRIORITY_TABLE_NOT_UNIQUE`。
4. 把童装适配器的 `hard_constraint_family` 改成女装的 → 应报 `HARD_CONSTRAINT_FAMILY_DRIFT`。
5. 给女装适配器加 `is_default_for_other_categories: true` → 应报 `WOMENSWEAR_RULE_OVERREACH`。
6. 删掉 N76 → 应报 `M1_ACCEPTANCE_JUDGEMENT_NOT_WIRED`。
7. 改交接件里任一 `schema_id` → 应报 `INTERFACE_HANDOFF_STALE`。
8. 改 `m2_evaluation_freeze_brief.md` 任意一字而不更新登记 → 应报 `M0_MODIFICATION_RECORD_STALE`。
9. 把 `m2_started` 置 `true` → 应报 `UNAUTHORIZED_TRUE_FLAG`（当前无授权条目）。
10. 把 M1 回执 `status` 改成含 `FROZEN` / `ACCEPTED` 的值 → 应被 M0 合同完备性判据拦下。

## 5. 未决事项（执行侧只登记，未裁决）

`OI-M1-01` 裁决写 11 输出对象 vs 冻结合同 15（按 15 执行）· `OI-M1-02` Prompt 写六层事实优先级 vs 合同七级（按七级执行）· `OI-M1-03` M3 Brief 不存在 · `OI-M1-04` 8 个端口预留对象未建 Schema · `OI-M1-05` 运行时事实分离目前只判 `persistence_class` 一致性，行为层不可测 · `OI-M1-06` 女装 4 条硬约束均未标 `safety_critical`。

## 6. 边界

- 执行侧不得自审：本包不含任何「已通过 / 已对齐」的结论。
- Guardian 结论是工程结论，不是 Founder 批准，也不是外部独立审查。
- §14 supersession：`37f636c73dac1be7457dfc951984b43532056804` 之后的任何新 Commit 都使针对它的复核结论失效。
