# 笛语跨品牌服装搭配专家内核 · 文档索引

> 项目编号 DIYU-CBFSK-001｜基线日期 2026-08-13｜产品真源 PRD v1.2（`SIGNED`）｜M0 `PASS`｜M1-EP01 已交付｜M2-EP01 已自检

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
execution_status: M1_M2_PARALLEL_IN_PROGRESS
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
m2_started: true
m2_ep01_status: SELF_CHECKED
m2_evaluation_profile_status: PROVISIONAL_READY
m2_benchmark_assets_status: NOT_CREATED
m2_hidden_assets_status: NOT_CREATED
m2_frozen: false
m1_final_binding: PENDING_M1_CLOSEOUT
knowledge_distillation_started: false
pending_active_baseline_switch: false
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

`01_contracts_and_schemas/m1_object_model/` 下 18 份 Schema ＋ 风格空间 ＋ 注册表 ＋ 覆盖映射表：**12 个输入与 15 个输出对象在 Schema 层全部可寻址**，对象数量与命名逐一对齐 M0 冻结合同（M1 只做 Schema 化，不增删对象）。风格空间落 PRD 5.3 原文点名的 14 维连续坐标，不自行增补未点名维度。输出走「整包」选项，`DecisionTrace` 含 D-28 要求的「被舍弃的合法候选族」必填记录位。交付报告见 [`11_reports_and_receipts/m1_ep01_delivery_report.md`](11_reports_and_receipts/m1_ep01_delivery_report.md)。

M1-EP02（五类品类适配合同）与 M1-EP03（集成与收口）尚未开工。

## M2 评测治理基础（M2-EP01 已自检）

M2 与 M1 并行执行，基线钉死在 M1-EP01 收口 Commit `6499431c66f7bf4a234bd830ee4c810e1ac78694`——签署只授权这一个 Commit，`main` 此后前进不改变本包基线。全项目并行执行包上限 2（`DIYU-CBFSK-FR-GRANULARITY-005`）已由 M1 链 + M2-EP01 占满，**M2-EP02 在 M1 收口合入 `main` 前不得启动**。

`03_m2_evaluation_foundation/` 下四组产物：

| 目录 | 内容 |
|---|---|
| `envelope/` | M1→M2 公共元数据信封与 Profile 组合视图；`m1_source_binding.v0.1.yaml` 是 M1 产物 SHA256 的唯一记录处 |
| `adr/` | 六份最小 ADR，每份声明最小实现／落地里程碑／当前不建设／激活条件 |
| `architecture/` | ADR-001 的落地件：12 输入 + 15 输出对象逐一归到六层 |
| `evaluation_governance/` | 评分者校准、抽样设计、基线修订三件套合同 ＋ 评测资产分类 Profile |
| `identity_isolation/` | 禁止／允许能力两份精确清单（`check_m2_identity_isolation` 的唯一取数处） |

**只包装、不复制、不修改**：M2 一律经 Envelope/Profile 引用 M1 冻结物，`in_place_modification_allowed` 常量 `false`。当前 Profile 全部 `binding_status: PROVISIONAL`——M1 尚未整体收口，最终绑定与重测属 M2-EP02。既有 M1 冻结物字节变了判 `M1_FROZEN_ARTIFACT_DRIFT`（熔断）；只是新增 EP02/EP03 产物则属 `REBIND_AND_RETEST`（正常前进），两者不可混为一谈。

**造型理解与身份识别永久解耦**（ADR-004，红线）：五项禁止能力的激活条件是**永不**，不是「暂缓」。检测走结构化能力面（Schema property 与枚举、能力/组件/服务登记、依赖清单），**不扫散文**——裁决原文里必然写着「不建设人脸身份识别」，全文关键词扫描会把这句话本身判成违规。

本包**一件评测资产都没产**：评分卡、基线锦标赛与隐藏评测资产属 M2-EP02，冻结属 M2-EP03（不可逆包，需 Founder 精确 Prompt 批准）。隐藏边界执行全部委派既有 `check_hidden_benchmark_boundary`，未新建第二套实现。

M2-EP01 交付报告与回执见 [`11_reports_and_receipts/m2_ep01/`](11_reports_and_receipts/m2_ep01/)。

## 治理（governance/）

| 目录 | 内容 |
|---|---|
| `governance/baseline/` | Founder 钉死的基线 Manifest、迁移记录 |
| `governance/founder_rulings/` | Founder 裁决原件（FR-ORG-002、FR-EVAL-003、FR-CALIBRATION-004、FR-GRANULARITY-005、FR-PROCESS-006、FOUNDER-M0-DECISION-001、FOUNDER-M1-GATE-001、FOUNDER-M2-CHARTER-001） |
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
- `ci/checkers/`：UUID、基线哈希、DOCX 规范化哈希、活真源唯一性、角色模型（含红线清单指纹）、工作区佐证、任务分级、条件台账、合规台账、隐藏边界、外部评审声明、M0 十四项、项目状态、工程量口径、投影一致性、裁决覆盖、M0 四字段完备、M0 零接触、M0 清单闭环、M1 对象覆盖、M2 治理落盘、M2 信封合同、M2 身份隔离、M2 评测治理共 24 个确定性 Checker。
- `ci/run_fixtures.py`：判据层 fixture——用字面量 payload 驱动每个 Checker 的 `validate()`；fixture 从不调用 `collect()`，因此被测代码不能自己造出「通过」的证据。
- `ci/run_schema_fixtures.py`：结构层 fixture——用字面量实例驱动 M1 对象 JSON Schema 本身；每份 Schema 正负各一，只证明「对的能过」不算验证过。
- `ci/run_all_checks.py`：一次运行全部 Checker 并逐项打印 PASS/FAIL。
