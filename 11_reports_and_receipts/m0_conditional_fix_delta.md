# M0 CONDITIONAL 修复 · Delta 清单（供 Guardian delta 复核）

> 裁决依据：`DIYU-CBFSK-FOUNDER-M0-DECISION-001`（M0 = CONDITIONAL）
> 被修复的候选：`2780e65dc32b20576635b887bd7634663afe531b`
> 复核范围：**仅限下列四项修复 ＋ 两项到期裁决的落盘**
> 升级规则：本 delta 复核通过即 M0 自动升级为 PASS，无需 Founder 再出场

## 一、四项必修（逐条对应裁决第一条）

### M0-FIX-01 规范源状态矛盾修正

| | |
|---|---|
| 文件 | `governance/bootstrap/role_operating_model.v0.2.yaml` |
| 改动 A | `effective: false` → `true`，并新增 `effective_precondition_satisfied_by`（PRD 签署 PASS、合并批准、签署基准 `9335180f`、已合并 `1153fc7`）与 `effective_correction_note` |
| 改动 B | 红线 `开始 M0 十四项正式施工` → `未经授权开始 M0 施工` |
| 为什么 | v1.2 已签署生效、main 已合并、`project_state.m0_authorized=true`，而 `effective` 仍为 false，同一文件内部自相矛盾。红线原文在 M0 获授权后变成自我违反——把已授权的正当施工也列为越界；改后守的是**授权缺失**而非**施工本身** |
| 连带 | 红线是投影内容，`AGENTS.md` / `CLAUDE.md` / `.github/copilot-instructions.md` / 5 份角色合同 / 1 份角色 Prompt 由编译器重新生成，`--check` drift=0 |

### M0-FIX-02 变更映射活真源更新

| | |
|---|---|
| 文件 | `PRD_v1.2_change_map.yaml` |
| 改动 | `files.current_active_product_truth` 由 v1.1 → v1.2；新增 `current_active_product_truth_status: SIGNED`、`superseded_product_truth`（指向 `归档_v1.1/`）与更正说明 |
| 为什么 | 活基线已在 `1153fc7` 切换到 v1.2 并归档 v1.1，此字段仍指向 v1.1 |

### M0-FIX-03 M0 独立执行标识

| | |
|---|---|
| 文件 | `11_reports_and_receipts/m0_delivery_receipt.yaml`、`m0_delivery_report.md`（页眉） |
| 改动 | `execution_run_id` = `ec8d723a-4515-45ef-8889-71f6ddafbd0e`（新生成 UUIDv4）；`parent_execution_run_id` = `2fcbfed0-be7e-4b6f-938e-7f84109ab162`（治理任务标识下沉） |
| 为什么 | M0 是独立里程碑批次，此前误用治理任务 `DIYU-CBFSK-GOV-ROLE-OPERATING-MODEL-002` 的 run 标识 |
| **主动披露** | 该新标识**尚未纳入 `check_execution_uuid` 守卫**。守卫扩展属 checker 增强，按同一裁决「不入本批」，与 NB-M0-01 / NB-M0-02 一并随 M1-EP01 落地。此处如实标注，不假装已有守卫 |

### M0-FIX-04 COND-010 范围改写并关闭

| | |
|---|---|
| 文件 | `governance/conditions/conditional_decision_ledger.yaml` |
| 改动 | 新增 `actual_scope_of_deferred_commit`（`dcd6484`，45 文件，9 类改动逐条列出）；`status` OPEN → CLOSED；`closure_commit` = `2780e65d`；`founder_closure_decision` 绑定本裁决 |
| 为什么 | 原描述把 `dcd6484` 概括为「签署回执、状态位更新、三项 required_delta 修复」，窄于实际改动面——遗漏了门禁改造、15 份新 fixture、FR-GRANULARITY-005、台账推进与合规七项转录 |
| 关闭依据 | Guardian 对 `2780e65d`（其祖先含 `dcd6484`）作 M0 收口审查，结论 APPROVE_WITH_CONDITIONS |
| 连带 | `merge_state.open_conditions_at_permission` 是签署许可当时的快照，不改写；新增 `open_conditions_note` 说明当前状态以各条 `status` 为准 |

## 二、两项到期裁决落盘（裁决第二条）

| 项 | 落点 | 内容 |
|---|---|---|
| M0-OPEN-01 限额 POC 证据批次额度 | `compliance_review_contract.v1.0.yaml` `deferred_decision_nodes` | 场景实例 ≤500 · 候选回答 ≤2,000 · 专家抽评 ≥100 件 · 限额 6 人月；四项均为**上限或下限约束**，非目标值；超出任一项须 Founder 另行裁决 |
| M0-OPEN-02 品牌档案单价校准 | `data_and_fixture_workflow.v1.0.yaml` `reference_brand_archives.cost_calibration` | 确认延至 M1；M0 如实记 `NOT_PERFORMED`；Founder 确认「不生成」红线优先读法正确 |

回执中 `open_items_for_founder` 相应替换为 `founder_decisions_of_record`，两项状态 `DECIDED`。

## 三、状态口径

| 字段 | 值 | 说明 |
|---|---|---|
| 回执 `status` | `M0_CONDITIONAL_PENDING_GUARDIAN_DELTA_REVIEW` | **未**改为 PASS |
| `execution_status` | `M0_IN_PROGRESS` | 未动 |
| 十一份合同 `status` | `M0_CANDIDATE_PENDING_FOUNDER_M0_DECISION` | 未动 |

**执行侧没有自行把 M0 翻成 PASS。** 裁决把升级判定权委托给 Guardian 的 delta 复核，PASS 生效与 README／状态位更新是复核通过之后的动作，不在本 Commit 内。

## 四、不在本 delta 内

| 项 | 去向 |
|---|---|
| NB-M0-01 零接触扫描加 `scanned_file_count` 断言 | M1-EP01 顺手项 |
| NB-M0-02 `PREMATURE` 判据改白名单 | M1-EP01 顺手项 |
| M0-FIX-03 新执行标识的 checker 守卫 | 同上批次 |
| MILESTONE_PLAN_M1 三包结构与 M1-EP01 执行 Prompt | 已作为**裁决自身内容**记入 `DIYU-CBFSK-FOUNDER-M0-DECISION-001.m1_pre_approval`；M1 实际施工不在本 Commit |

## 五、核验（本修复后重跑，未沿用）

| 项 | 结果 |
|---|---|
| 治理 Checker | 19 PASS / 0 FAIL |
| Fixtures | 74/74 按声明行为 |
| PRD 合同 Checker | `--require-archive` 62 PASS / 0 FAIL |
| 指令投影漂移 | 0（12 份投影，红线改动已重新生成） |
| 支持任务四字段完备 | 57 / 57 |
| 零接触扫描 | 命中 0 |
| 回执 `artifact_sha256` | 18 份已按修复后内容重算 |
