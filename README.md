# 笛语跨品牌服装搭配专家内核 · 文档索引

> 项目编号 DIYU-CBFSK-001｜基线日期 2026-08-13｜任务 DIYU-CBFSK-GOV-ROLE-OPERATING-MODEL-002

## 当前活基线（尚未签署）

| 文档 | 用途 | 状态 |
|---|---|---|
| `笛语跨品牌服装搭配专家内核_PRD与执行里程碑_v1.1.docx` | 已核验、未签署的产品真源基线 | **当前活基线 · `PENDING_FOUNDER_SIGNATURE`** |
| `笛语跨品牌服装搭配专家内核_M0执行申请_v1.1.docx` | M0 执行授权（v1.1 版） | 未签署，未授权 |
| `PRD_v1.1_核验回执.docx` | v1.1 核验记录 | 历史核验证据 |

按 Founder 裁决，**v1.1 不单独签署**；它保持活基线身份直到 PRD v1.2 正式生效。**v1.2 生效前不得归档 v1.1。**

## PRD v1.2 候选（未生效）

| 文档 | 用途 | 状态 |
|---|---|---|
| `笛语跨品牌服装搭配专家内核_PRD与执行里程碑_v1.2.docx` | 合并 D-17—D-29、S1—S8 与治理操作模型的全文候选 | `READY_FOR_GUARDIAN` · 未生效 |
| `笛语跨品牌服装搭配专家内核_M0执行申请_v1.2.docx` | M0 执行申请 `DIYU-CBFSK-EXEC-REQ-M0-003` | 候选，未签署，`m0_authorized=false` |
| `PRD_v1.2_核验回执.docx` | 候选施工侧自检回执 | 自检 PASS，**不代替** Guardian／总顾问／Founder |
| `PRD_v1.2_change_map.yaml` | 机器可读裁决—章节—里程碑—验收映射 | 当前变更映射 |

PRD v1.2 是可独立阅读的全文版，不需要对照 v1.1 或 Delta。它必须依次通过独立 Guardian → ChatGPT 总顾问远程审查 → Founder 一次性签署，才会取代 v1.1 成为唯一产品真源。

## 当前项目状态

```yaml
project_status: PROJECT_INITIATED
execution_status: EXECUTION_NOT_STARTED
production_servable: false
m0_authorized: false
current_active_baseline: PRD_v1.1
current_active_baseline_status: PENDING_FOUNDER_SIGNATURE
prd_v1_2_documentation_status: READY_FOR_GUARDIAN
prd_v1_2_effective: false
guardian_review_completed: false
chatgpt_remote_review_completed: false
founder_prd_signed: false
founder_merge_approved: false
main_merged: false
```

本轮没有开始 M0 施工、M1／M2、知识蒸馏、夹具或隐藏品牌生成、多模态识别、人设记忆生产库、Serving、真实库存接入或自动发布。

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

## 治理（governance/）

| 目录 | 内容 |
|---|---|
| `governance/baseline/` | Founder 钉死的基线 Manifest、迁移记录 |
| `governance/founder_rulings/` | Founder 裁决原件（FR-ORG-002、FR-EVAL-003） |
| `governance/bootstrap/` | `role_operating_model.v0.2.yaml`：角色与执行治理的**唯一规范源** |
| `governance/roles/` `governance/prompts/` | 角色合同与角色 Prompt（由规范源生成） |
| `governance/conditions/` | `CONDITIONAL` 条件关闭台账 |
| `governance/compliance/` | Founder 合规逐项裁决台账 |
| `governance/storage/` | 隐藏评测物理隔离合同 |
| `governance/workspaces/` | 工作区隔离佐证 Schema 与实例 |
| `governance/reports/` `governance/receipts/` | 对账报告与 Receipt |

`AGENTS.md`、`CLAUDE.md`、`.github/copilot-instructions.md` 是规范源的**生成投影**，不得手工编辑——改动请改规范源后运行 `python3 ci/compile_role_instructions.py --write`。

## 归档

`归档_v1.0/` 保存 PRD v1.0、v1.1 Delta、v1.0 审查报告与已作废的 M0 申请，仅作历史证据，不再是执行依据。**目前没有 `归档_v1.1/`**：v1.1 仍是活基线，只有在 PRD v1.2 正式生效后才归档。

## 工具与 CI

- `工具/build_prd_v1_2.py`：从 v1.1 样式模板可重放生成三份 v1.2 DOCX。
- `工具/check_prd_v1_2.py`：版本、编号、对象数量、FR 追溯、M0 十四项、M11/M12、D-28/D-29 锚点、废弃措辞与 README／归档一致性。
- `工具/audit_docx_package.py`：DOCX ZIP CRC、必需 OOXML 部件、XML 可解析性与页眉版本。
- `ci/compile_role_instructions.py`：从规范源确定性生成三份指令投影，`--check` 用于漂移检测。
- `ci/checkers/`：UUID、基线哈希、DOCX 规范化哈希、活真源唯一性、角色模型、工作区佐证、任务分级、条件台账、隐藏边界、外部评审声明、M0 十四项、项目状态、投影一致性共 13 个确定性 Checker。
- `ci/run_all_checks.py`：一次运行全部 Checker 并逐项打印 PASS/FAIL。
