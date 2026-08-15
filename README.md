# 笛语跨品牌服装搭配专家内核 · 文档索引

> 项目编号 DIYU-CBFSK-001｜基线日期 2026-08-13｜产品真源 PRD v1.2（`SIGNED`）｜M0 `PASS`｜M1 `PASS`（`FOUNDER_ACCEPTED`）｜M2 `SUSPENDED_BY_FOUNDER`（Founder 主动挂起，非通过亦非失败；等待三项 Founder 动作，执行侧不得自行推进）

## 当前活基线

| 文档 | 用途 | 状态 |
|---|---|---|
| `笛语跨品牌服装搭配专家内核_PRD与执行里程碑_v1.2.docx` | 产品合同、范围、里程碑与验收门 | **当前活基线 · `SIGNED`** |
| `笛语跨品牌服装搭配专家内核_M0执行申请_v1.2.docx` | M0 执行申请 `DIYU-CBFSK-EXEC-REQ-M0-003` | 已签署，`m0_authorized=true` |
| `PRD_v1.2_核验回执.docx` | 施工侧自检回执 | 自检 PASS，**不代替** Guardian／总顾问／Founder |
| `PRD_v1.2_change_map.yaml` | 机器可读裁决—章节—里程碑—验收映射 | 当前变更映射 |

PRD v1.2 是当前唯一产品真源，由 Founder 于 2026-08-13 签署生效（签署回执 `governance/receipts/founder_signoff_receipt.yaml`，`DIYU-CBFSK-FOUNDER-SIGNOFF-001`，签署基准 Commit `9335180f9e1fd3d480f9b39e0a23597ee52079c7`）。v1.1 三份文档已归入 `归档_v1.1/`，仅作历史证据。

审查链如实记录：独立 Guardian 两轮（`f48fed3` REJECT → `9335180f` APPROVE_WITH_CONDITIONS）；ChatGPT 总顾问远程审查**未进行**，由 Founder 依 §11.2 显式记录性豁免并接受风险，**不是**静默跳过，也**不得**记为已完成。签署子 Commit 自身的 Guardian 确认按 Founder 显式例外延至 M0 收口（`COND-010`），**不视为已确认**。

## 当前项目状态

```yaml
project_status: PROJECT_INITIATED
execution_status: M2_IN_PROGRESS
production_servable: false
m0_authorized: true
current_active_baseline: PRD_v1.2
current_active_baseline_status: SIGNED
prd_v1_2_documentation_status: FOUNDER_SIGNED
prd_v1_2_effective: true
guardian_review_completed: true
chatgpt_remote_review_completed: false
chatgpt_remote_review_status: EXPLICITLY_WAIVED_WITH_RISK_ACCEPTANCE
founder_prd_signed: true
founder_m0_authorized: true
founder_merge_approved: true
main_merged: true
m0_execution_started: true
m0_founder_decision: PASS
m0_founder_decision_original: CONDITIONAL
m0_guardian_delta_review: APPROVE
m1_started: true
m1_status: FOUNDER_ACCEPTED
m2_started: true
m2_status: SUSPENDED_BY_FOUNDER
m2_ep01_status: SELF_CHECKED
m2_ep02_status: SELF_CHECKED
m2_ep03_status: SELF_CHECKED
m2_ep04_status: SELF_CHECKED
m2_ep05_status: SUPERSEDED_BY_CORRECTION
m2_ep05_correction_status: SELF_CHECKED
m2_evaluation_profile_status: FINAL_BOUND
m2_milestone_decision: BLOCK_M2_FREEZE_AND_MERGE
m2_candidate_status: M2_PARTIAL_DELIVERY_BLOCKED
m2_deliverables_ready: 14/18
m2_public_blueprint_status: M2_PUBLIC_BLUEPRINT_READY_FOR_HIDDEN_GENERATION
public_blueprint_stable_for_hidden_generation: false
calibration_pack_distribution_allowed: false
m2_hidden_assets_status: NOT_STARTED
founder_signature_eligible: false
m2_frozen: false
knowledge_distillation_started: false
pending_active_baseline_switch: false
execution_permitted: false
```

状态位不是随手改的：任何一位置 `true`，都必须在 `governance/receipts/founder_signoff_receipt.yaml` 的 `state_flag_authorizations` 里存在一条绑定完整 Commit 哈希的 Founder 授权。`production_servable` 与 `knowledge_distillation_started` 属红线位，**任何签署都不得授权**（分别至 M12 发布、M2 冻结后另行裁决）。`m1_started` 与 `m2_started` 依 [`DIYU-CBFSK-FOUNDER-M1-GATE-001`](governance/founder_rulings/DIYU-CBFSK-FOUNDER-M1-GATE-001.yaml) 转入授权门控。门控要求授权条目绑定完整 Commit 哈希且具名 `basis`，缺一即拦；`m2_started` 已由 Founder 于 [`DIYU-CBFSK-FOUNDER-M2-CHARTER-001`](governance/founder_rulings/DIYU-CBFSK-FOUNDER-M2-CHARTER-001.yaml) 具名签署补上授权条目（绑定 `6499431c66f7bf4a234bd830ee4c810e1ac78694`），随 M2-EP01 实际开工置 `true`——授权存在 ≠ 事件已发生，两者本批同时成立。此前它的锁靠的是「没有条目」而不是「不可授权」（屏障层数对照见回执 `barrier_layer_delta`），本次正是那条路径被 Founder 走了一次，**不是**执行侧自行放宽，也未触碰 `never_authorizable` 两条红线位。

M0 已按里程碑单包模式落盘十四项交付物。Founder 裁决 `CONDITIONAL`（[`DIYU-CBFSK-FOUNDER-M0-DECISION-001`](governance/founder_rulings/DIYU-CBFSK-FOUNDER-M0-DECISION-001.yaml)）→ 四项必修落盘于 `f01e45b4ca4d7416feaec4177f4f8aad2ce35458` → Guardian delta 复核 `APPROVE`、无阻塞发现（[报告](governance/reports/guardian_review_report.f01e45b.delta.md)）→ 依裁决 `upgrade_rule` **自动升级为 M0 `PASS`**。总顾问 delta 复核由 Founder 豁免，**记录在案，不记为已完成**。

`PASS` 只表示 M0 里程碑通过：**不**表示合同已生效，**不**表示可服务生产，**也不**表示 M1 已开工。M1／M2、知识蒸馏、夹具或隐藏品牌生成、多模态识别、人设记忆生产库、Serving、真实库存接入与自动发布均未开始。M1-EP01 已于 main 合并完成后开工（合并 Commit `8eaf5f25987d787a546096b6a60a4e6a6b5a30f4`，快进合并，main HEAD 即 Guardian 审过的哈希）。`m1_started` 依 `DIYU-CBFSK-FOUNDER-M1-GATE-001` 第 4 条如实置 `true`，授权条目绑定该裁决。M2、知识蒸馏、夹具或隐藏品牌生成、多模态识别、人设记忆生产库、Serving、真实库存接入与自动发布仍未开始。

## Founder 裁决 D-17—D-29 摘要

1. **D-17** M11 双路径：Founder 真实品牌注入（可选，优先）＋ Codex 夹具合成回退；注入不是 M11 硬门。
2. **D-18** 未见品牌继续使用合成封闭品牌，与夹具池物理及程序隔离；Founder 注入资料禁入隐藏集。
3. **D-19** `M12｜Commercial V1.0生产加固` 名称、M0—M12 顺序与工程路线不变；仿真／注入／真实市场证据分层表述。
4. **D-20** 搭配师人设连续性升为一级能力（C-13）与评测域，五对象进入 M1 Schema、M7 实现与 M2 评分卡。
5. **D-21** 自媒体原生语感升为独立能力（C-14）、独立 FR 与 M2 评分卡。
6. **D-22** 完整空间陈列不是 V1.0 硬实现，但保留 `VisualMerchandisingExtensionPort`，不是永久退出。
7. **D-23** 多模态商品理解（C-15）正式立项；品牌数据库仍为权威事实源，视觉推断按 `authoritative > human_confirmed > model_inferred` 分层，不得覆盖权威事实，不得推断成分／性能／库存／安全认证。
8. **D-24** 当前只做导购辅助内容投影，保留 `RealtimeSalesAssistExtensionPort`，不是永久排除。
9. **D-25** 默认人工审核在环；自动发布仅经 Founder 按租户／品牌／账号／风险级别显式授权开启，须具备审计、撤回与 Kill Switch；FR-17 与「人工可发布率≥75%」保留不变。
10. **D-26** M11 仍至少三类；正式真实品牌导入前 `five_category_activation_readiness=100%`。
11. **D-27** Project CI：`governance/bootstrap/role_operating_model.v0.2.yaml` 是唯一规范源，AGENTS／CLAUDE／Copilot 指令为生成投影；角色 Prompt 不构成第三套产品真源。
12. **D-28** 合理多解原则（P-14）：评测强制三分类（`constraint_correctness` / `mechanism_correctness` / `open_decision`），②③类禁设唯一 Gold Answer，冻结对象是可接受决策边界；`核心判断重复一致率` 更名 `核心决策逻辑稳定率`（阈值 ≥85% 不变）。
13. **D-29** M6 反退化验收：不得实现为纯 Prompt/RAG 端到端直答；硬约束确定性执行、LLM-off 不变性、DecisionTrace 规则归因三条必须通过。

## M0 执行边界

M0 顶层交付清单仍为 **14 项**，不新增第 15 项，也不恢复 18 项版。D-17—D-29 与 S1—S8 分别落入既有 `capability_contract`、`input_output_boundary`、`role_and_decision_rights`、`non_goals_and_stop_conditions`、`architecture_and_integration_boundary`、`data_and_fixture_workflow`、`execution_critical_path_and_decision_gates`、M1 对象模型 Brief 与 M2 评测冻结 Brief。

## M0 交付（十四项）

| 目录 | 内容 |
|---|---|
| `00_charter/` | 交付物 1：项目章程（含附录 A 目录 delta 适配映射表） |
| `01_contracts_and_schemas/` | 交付物 2—11：十份合同 ＋ 交付物 12—13：M1 对象模型 Brief、M2 评测冻结 Brief |
| `02_benchmark_manifests/` | 公开评测清单目录（名称由 S5／D-27 固定）；M0 只建目录与边界说明，无任何 manifest |
| `11_reports_and_receipts/` | 交付物 14 之报告与回执 |
| `ci/checkers/check_m0_*.py` | 交付物 14 之 Checker：支持任务四字段完备、与笛语现有资产零接触、十四项清单闭环 |

十四项合计 **57 条支持任务**，每条都带必需输入、输出、失败状态与负责角色——这正是 PRD 13 节 M0 通过标准第一条的机器化形式。Founder M0 裁决 PASS 生效后，十四项状态由 `M0_CANDIDATE_PENDING_FOUNDER_M0_DECISION` 转为 `M0_FROZEN`；该转换由 `check_m0_contract_completeness` 双向把关——裁决前写 FROZEN 判 `PREMATURE_FROZEN_CLAIM`，裁决后仍挂 PENDING 判 `STALE_PENDING_STATUS`，两个方向都不许说假话。

## M1 对象模型（M1-EP01 已交付）

`01_contracts_and_schemas/m1_object_model/` 下 19 份 Schema ＋ 风格空间 ＋ 注册表 ＋ 覆盖映射表：**12 个输入与 15 个输出对象在 Schema 层全部可寻址**，对象数量与命名逐一对齐 M0 冻结合同（M1 只做 Schema 化，不增删对象）。风格空间落 PRD 5.3 原文点名的 14 维连续坐标，不自行增补未点名维度。输出走「整包」选项，`DecisionTrace` 含 D-28 要求的「被舍弃的合法候选族」必填记录位。交付报告见 [`11_reports_and_receipts/m1_ep01_delivery_report.md`](11_reports_and_receipts/m1_ep01_delivery_report.md)。

## M1 品类适配合同（M1-EP02 已交付）

`01_contracts_and_schemas/category_adapter_contracts/` 下五份品类适配器 ＋ 一份跨品类冲突优先级表：女装／童装／青少年／亲子／运动各自的硬约束与安全边界，逐字段镜像 M0 冻结的 `category_scope_contract.v1.0.yaml`（品类、硬约束家族、核心受众、专业合同、禁止项、审查要求），适配器改写品类定义会被 `HARD_CONSTRAINT_FAMILY_DRIFT` 当场判失败。冲突优先级 6 条有序规则 ＋ 5 条组合规则**全仓唯一**，五份适配器一律引用不复制，唯一性靠全仓扫 `contract_id` 判定。交付报告见 [`11_reports_and_receipts/m1_ep02_delivery_report.md`](11_reports_and_receipts/m1_ep02_delivery_report.md)。

## M1 集成与收口（M1-EP03 已交付）

补齐 Brief 交付清单第 3 项 `human_visual_profile.schema.v0.1.json`（C-04，EP01 遗漏）与第 21 项 `extension_port_contracts.v0.1.yaml`（D-22 / D-24 / FR-27，两个端口均 `RESERVED_NOT_IMPLEMENTED`）；新增派生件 [`m1_interface_handoff.v0.1.yaml`](01_contracts_and_schemas/m1_interface_handoff.v0.1.yaml) 作为 M1→M2/M3 的接口面，M2 冻结须按 `schema_id` / `hard_constraint_id` / `dimension_id` 绑定；覆盖 checker 扩展出 Brief 21 项交付清单、跨包引用完整性、端口注册表一致、接口面漂移与判据接线五类判据。

M1 交付报告见 [`11_reports_and_receipts/m1_delivery_report.md`](11_reports_and_receipts/m1_delivery_report.md)，回执见 [`11_reports_and_receipts/m1_delivery_receipt.yaml`](11_reports_and_receipts/m1_delivery_receipt.yaml)。

**M1 已通过**：Founder 裁决 [`DIYU-CBFSK-FOUNDER-M1-PASS-001`](governance/founder_rulings/DIYU-CBFSK-FOUNDER-M1-PASS-001.yaml) `decision: PASS`，批准哈希 `2df11012da46ace0de7b7bce6d199a578d32d341`，三项前置齐备（Guardian `APPROVE` 阻断 0 / 总顾问 Delta 复核 `PASS` / Founder 裁决）。已按 FF-ONLY 合并 main，`origin/main` 实测等于该批准哈希，未产生任何合并提交。

`PASS` 只表示 M1 里程碑通过：**不**表示可服务生产，**也不**表示知识蒸馏可开始。M1 收口后 Founder 已下达恢复执行授权（`DIYU-CBFSK-FOUNDER-M2-RESUME-AUTHORIZATION-001`）：M2 解除暂停，`execution_status` 迁移至 `M2_IN_PROGRESS`，EP02 与 EP03 连续执行。M3、知识蒸馏、隐藏资产进入主仓仍须 Founder 另行裁决。

## M2 评测治理基础（M2-EP01 已自检）

M2-EP01 曾与 M1 并行执行，基线钉死在 M1-EP01 收口 Commit `6499431c66f7bf4a234bd830ee4c810e1ac78694`。M1 已于 `c3f6ad372306cc12f139cf38624e9a5cea2cf329` 收口合入 `main`，并行窗口关闭；EP02 已按受控合并（`merge`，非 `rebase`，保留 `main` 为祖先）承接 M1 全部产物。

`03_m2_evaluation_foundation/` 下四组产物：

| 目录 | 内容 |
|---|---|
| `envelope/` | M1→M2 公共元数据信封与 Profile 组合视图；`m1_source_binding.v0.1.yaml` 是 M1 产物 SHA256 的唯一记录处 |
| `adr/` | 六份最小 ADR，每份声明最小实现／落地里程碑／当前不建设／激活条件 |
| `architecture/` | ADR-001 的落地件：12 输入 + 15 输出对象逐一归到六层 |
| `evaluation_governance/` | 评分者校准、抽样设计、基线修订三件套合同 ＋ 评测资产分类 Profile |
| `identity_isolation/` | 禁止／允许能力两份精确清单（`check_m2_identity_isolation` 的唯一取数处） |

**只包装、不复制、不修改**：M2 一律经 Envelope/Profile 引用 M1 冻结物，`in_place_modification_allowed` 常量 `false`。既有 M1 冻结物字节变了判 `M1_FROZEN_ARTIFACT_DRIFT`（熔断）；只是新增产物则属 `REBIND_AND_RETEST`（正常前进），两者不可混为一谈。

**造型理解与身份识别永久解耦**（ADR-004，红线）：五项禁止能力的激活条件是**永不**，不是「暂缓」。检测走结构化能力面（Schema property 与枚举、能力/组件/服务登记、依赖清单），**不扫散文**——裁决原文里必然写着「不建设人脸身份识别」，全文关键词扫描会把这句话本身判成违规。

隐藏边界执行全部委派既有 `check_hidden_benchmark_boundary`，未新建第二套实现。

M2 前三包形成候选后，Founder 收口裁决为 **`BLOCK_M2_FREEZE_AND_MERGE`**（[`DIYU-CBFSK-FOUNDER-M2-CLOSEOUT-001`](governance/founder_rulings/DIYU-CBFSK-FOUNDER-M2-CLOSEOUT-001.yaml)）：Guardian `APPROVE_WITH_CONDITIONS`、阻断 0（东西是真的），总顾问 `BLOCK`（该有的没齐）。两者不冲突，里程碑完整性以上位合同为准。M2-EP04 据此执行收口修复。

**评测体系**：D-28 三分类合同 ＋ 三张评分卡（`constraint_correctness` 0/1 硬判、`mechanism_correctness` 可接受推理区间、`open_decision` 解族判定），②③类**禁设唯一 Gold Answer**、合法分歧必须保全；25 条 M1 品类硬约束双向全覆盖，绑定 ID 一律解析到 M1 真源，禁悬空表述。基线锦标赛四维度（质量／成本／延迟／人工干预）并列记录、**不合成单一总分**——权重就是取舍本身，须待 Founder 冻结。dry-run 骨架零真实模型调用、连跑两次字节相同。

**交付闭环（M2-EP04 新增）**：`03_m2_evaluation_foundation/closure/m2_deliverable_coverage_map.v0.1.yaml` 按 M2 冻结 Brief 第 2 节逐项生成 18 项覆盖矩阵，四态（`ABSENT`／`PARTIAL`／`READY`／`FROZEN`）冻结为合同——**`READY` 不等于「文件存在」**。当前 **14 项 `READY`、4 项 `PARTIAL`**，四项全部卡在同一个条件上：隐藏侧存储未就绪。清单读自 Brief 而非候选自述，判据 `check_m2_deliverable_closure` 直接解析 Brief 表格取数。

**双轴评测矩阵（M2-EP04 新增）**：横轴三张任务类型卡不动，纵轴补齐七类能力卡（专业／叙事／人设连续性／自媒体语感／多模态属性／多模态置信度校准／五品类就绪），四轴（能力 × 任务类型 × 品类 × 风险级别）可寻址 195 格；PRD 10.2 的 **34 条指标逐条归属且唯一**，判据从 DOCX 表格独立提取比对。11 条硬门逐条映射到八道发布门，无硬门无承接。

**公开校准集（M2-EP04 新增）**：90 例，5 品类 × 3 任务类型 × 3 风险等级 = 45 格**无一为空**，每格 2 例。硬约束题带 0/1 两侧条件，机制题带可接受推理区间，开放题带至少两个合法解族与可接受边界——只出题干不合格。两侧隔离评审的 Prompt 已落盘并记哈希，**评审结果为 0 条**，状态如实置 `CALIBRATION_REVIEW_EVIDENCE_MISSING`：主执行侧不得自行扮演「隔离 GPT」与「隔离 Claude」。

**隐藏评测资产未生成**：Founder 已声明 provision `STORE-A` 并设 Steward 角色，但访问矩阵与仓库标识未交到执行侧，`COND-011` 推进至 `EVIDENCE_SUBMITTED` 而非 `CLOSED`。一件资产未产、一个字节未进主仓。A→B 输入包（20 份文件带哈希）与 Steward 执行 Prompt（`DIYU-CBFSK-M2-HIDDEN-STOREA-001` v1.1.0，十二阶段）已就位，任一输入文件哈希变化即判 `STALE` 并连带作废已生成资产。

**M2-EP05 整合与并行启动**：四项定锚裁决落盘（多模态边界／命名／Guardian 报告／指标分组），Guardian 三条发现全闭——编号锚点改由[标识符注册表](governance/identifiers/identifier_registry.v0.1.yaml)承接（任务 ID 不是裁决 ID，两者不得互相改名）；杜撰的停止码 `MULTIMODAL_SCOPE_CONFLICT_WITH_D10` 作废删除，全仓 STOP 声明位逐条标 `enforcement`（`machine_checked` / `human_judgement` / `future_runtime`），**无检测器的码一律不得表述为「未触发」**；报告的计数数字改为模板引用机器记录字段、生成时现读，判据重渲染逐字节比对。[校准评审启动包](03_m2_evaluation_foundation/calibration/launch_pack/)已具备独立分发所需的结构（90 例 / 9 批），但**分发是当前明令禁止的动作**——`calibration_pack_distribution_allowed` 为 `false`，`distribution_status` 为 `NOT_DISTRIBUTED`，且三条已知设计缺口未处置。包已按[封存清单](03_m2_evaluation_foundation/calibration/launch_pack_seal_manifest.v0.1.yaml)逐文件钉哈希；任一文件哈希变化即强制转为需重新确认。两侧评审记录各 0 条。[隐藏生成时序门](governance/conditions/hidden_generation_timing_gate.v0.1.yaml)已装：`public_blueprint_stable_for_hidden_generation` 为 `false` 时，允许 STORE-A provision、私有工具链与 2 个品牌试产批，**禁止 40 品牌正式批**。

`m2_frozen` 仍为 `false`，`founder_signature_eligible` 为 `false`。最终资产存在门 12 条判据当前满足 1 条；条件与状态语义已分离（`COND-011` 管存储、`m2_hidden_assets_status` 管资产、`COND-007` 管阈值且无「隐藏侧」），STOP 分五型，本轮三个 STOP 各自归型见 [`m2_condition_state_semantics.v0.1.yaml`](governance/conditions/m2_condition_state_semantics.v0.1.yaml)。

**M2-EP05-CORRECTION 定向补丁**（裁决 [`DIYU-CBFSK-FOUNDER-M2-EP05-CORRECTION-001`](governance/founder_rulings/DIYU-CBFSK-FOUNDER-M2-EP05-CORRECTION-001.yaml)，`BLOCK_CALIBRATION_DISPATCH`）：校准包此前**没有被评对象**——评审员对着题干打分，判的是空气。本包给 90 个评审单元各挂一份[候选输出](03_m2_evaluation_foundation/calibration/public_calibration_set.v0.1.yaml)（机制题与开放题另带决策轨迹），全部标 `non_candidate_knowledge`：禁止进入知识状态链与任何候选知识池；预期标签只进[边界锚点真源](03_m2_evaluation_foundation/calibration/founder_boundary_anchor_truth.v0.1.yaml)，**不进分发包**。判定语言拆成两个字段——`judgment` 答「算不算」、`score` 答「算的那些做得多好」，②③ 类分数钉到[五档锚点](03_m2_evaluation_foundation/calibration/numeric_scoring_anchors.v0.1.yaml)上，聚合直接比较 `judgment`，严禁用尚未冻结的阈值把分数转成成立与否。阈值[证据分型](03_m2_evaluation_foundation/calibration/metric_review_unit_mapping.v0.1.yaml)：`POLICY_THRESHOLD` 是 Founder 的产品裁决，不得装成统计估计；`EMPIRICAL_CUTPOINT` 必须有 estimator、样本下限与映射到的评审单元，输入不齐时不出建议值。[时序门](governance/conditions/hidden_generation_timing_gate.v0.1.yaml)前置由四项改五项（加「阈值全部冻结且 COND-007 关闭」与「Founder 在指定冻结 Commit 上确认公开蓝图」）。STORE-A 证据改为[文件级 intake](03_m2_evaluation_foundation/hidden_assets/store_a_evidence/)——判据读那两份真实 YAML 并扫描全部标量拒绝定位符，台账只记推导结果，不再充当证据。新增全仓判据 [`check_founder_confirmation_binding`](ci/checkers/check_founder_confirmation_binding.py)：凡声称「Founder 已确认／已批准／已授权／已签署」的布尔位，为真时必须挂具名文件＋可解析条款＋完整 40 位 Commit＋签署人＋签署时点——**被守的一方自己就能开门，这是本轮堵的洞**。

M2 当前现状以 [`11_reports_and_receipts/m2_ep05_correction/`](11_reports_and_receipts/m2_ep05_correction/) 为准；[`m2_delivery_report.md`](11_reports_and_receipts/m2_delivery_report.md) 已标 `SUPERSEDED`，作为 EP03 时点的历史记录保留。各包报告见 [`m2_ep01/`](11_reports_and_receipts/m2_ep01/)、[`m2_ep02/`](11_reports_and_receipts/m2_ep02/)、[`m2_ep04/`](11_reports_and_receipts/m2_ep04/)。

## 治理（governance/）

| 目录 | 内容 |
|---|---|
| `governance/baseline/` | Founder 钉死的基线 Manifest、迁移记录 |
| `governance/founder_rulings/` | Founder 裁决原件（FR-ORG-002、FR-EVAL-003、FR-CALIBRATION-004、FR-GRANULARITY-005、FR-PROCESS-006、FOUNDER-M0-DECISION-001、FOUNDER-M1-GATE-001、FOUNDER-M1-RUNTHROUGH-001、FOUNDER-M1-PASS-001、FOUNDER-RD-M1-01、FOUNDER-M2-CHARTER-001） |
| `governance/bootstrap/` | `role_operating_model.v0.2.yaml`：角色与执行治理的**唯一规范源** |
| `governance/roles/` `governance/prompts/` | 角色合同与角色 Prompt（由规范源生成） |
| `governance/conditions/` | `CONDITIONAL` 条件关闭台账 |
| `governance/compliance/` | Founder 合规逐项裁决台账 |
| `governance/storage/` | 隐藏评测物理隔离合同 |
| `governance/workspaces/` | 工作区隔离佐证 Schema 与实例 |
| `governance/reports/` `governance/receipts/` | 对账报告与 Receipt |

`AGENTS.md`、`CLAUDE.md`、`.github/copilot-instructions.md` 是规范源的**生成投影**，不得手工编辑——改动请改规范源后运行 `python3 ci/compile_role_instructions.py --write`。

## 归档

`归档_v1.0/` 保存 PRD v1.0、v1.1 Delta、v1.0 审查报告与已作废的 M0 申请。`归档_v1.1/` 保存 PRD v1.1、M0 执行申请 v1.1 与 v1.1 核验回执——归档发生在 v1.2 签署生效**之后**，三份均为 R100 纯重命名、字节未变。两个归档目录都只作历史证据，不再是执行依据。

## 工具与 CI

- `工具/build_prd_v1_2.py`：从 v1.1 样式模板可重放生成三份 v1.2 DOCX。
- `工具/check_prd_v1_2.py`：版本、编号、对象数量、FR 追溯、M0 十四项、M11/M12、D-28/D-29 锚点、废弃措辞与 README／归档一致性。
- `工具/audit_docx_package.py`：DOCX ZIP CRC、必需 OOXML 部件、XML 可解析性与页眉版本。
- `ci/compile_role_instructions.py`：从规范源确定性生成三份指令投影，`--check` 用于漂移检测。
- `ci/checkers/`：共 **49 个**确定性 Checker——M0／M1 既有 21 个，M2-EP01～EP03 新增 11 个，M2-EP04 再增 9 个（十八项交付闭环、里程碑闭环通则、能力矩阵、校准集、评审证据、错误码夹具覆盖棘轮、披露纪律、Guardian 报告绑定、隐藏生成就绪度），M2-EP05 再增 4 个（编号解析、STOP 码 enforcement、报告数字溯源、校准启动包），M2-EP05-CORRECTION 再增 1 个（Founder 确认类字段绑定，永久生效），M2-EP06 再增 1 个（分发前序列），M2-SEAL 再增 1 个（挂起封存），M2-PREMERGE-FIX 再增 1 个（`collect()` 硬编码事实源横扫，永久生效）。现役门禁清单以 [`governance/gates/live_gate_roster.v0.1.yaml`](governance/gates/live_gate_roster.v0.1.yaml) 为准，与本行双向比对。
- `ci/tools/`：报告渲染器（模板里的 `{{ref:路径#字段}}` 生成时现读机器记录）与校准启动包生成器（题目由题库派生，不写第二份）。
- `ci/run_fixtures.py`：判据层 fixture——用字面量 payload 驱动每个 Checker 的 `validate()`；fixture 从不调用 `collect()`，因此被测代码不能自己造出「通过」的证据。
- `ci/run_schema_fixtures.py`：结构层 fixture——用字面量实例驱动 M1 对象 JSON Schema 本身；每份 Schema 正负各一，只证明「对的能过」不算验证过。
- `ci/run_all_checks.py`：一次运行全部 Checker 并逐项打印 PASS/FAIL。
