# M0 交付报告 · 独立立项与合同冻结

> 任务 `GKB-CROSS-BRAND-STYLING-EXPERT-KERNEL-M0-CONTRACT-AND-BENCHMARK-FOUNDATION-001`
> 执行申请 `DIYU-CBFSK-EXEC-REQ-M0-003`（Founder 已签署，即时生效）
> 产品真源 PRD v1.2 · `SIGNED` · 签署基准 Commit `9335180f9e1fd3d480f9b39e0a23597ee52079c7`
> 执行角色 `TEMPORARY_EXECUTION_WRITER`（依 §11.3 Founder 指派，Codex 执行面网络中断）
> 状态 **`M0_CANDIDATE_PENDING_FOUNDER_M0_DECISION`** —— 未经 Founder 裁决，本报告不构成 M0 已通过

## 0. 先说清楚这份报告不是什么

它不是 Guardian 审查结论，不是总顾问审查结论，也不是 Founder 批准。它是施工侧的自检报告：说明十四项交付了什么、机器验了什么、哪些地方我没有做也不打算替 Founder 做。M0 是否通过，由 Founder 在读完本报告与 Guardian 报告后裁决。

## 1. 十四项交付物落点

| # | 交付物 | 落点 | 支持任务数 |
|---|---|---|---|
| 1 | `project_charter.v1.0.yaml` | `00_charter/` | 4 |
| 2 | `capability_contract.v1.0.yaml` | `01_contracts_and_schemas/` | 5 |
| 3 | `category_scope_contract.v1.0.yaml` | `01_contracts_and_schemas/` | 5 |
| 4 | `input_output_boundary.v1.0.yaml` | `01_contracts_and_schemas/` | 5 |
| 5 | `role_and_decision_rights.v1.0.yaml` | `01_contracts_and_schemas/` | 5 |
| 6 | `non_goals_and_stop_conditions.v1.0.yaml` | `01_contracts_and_schemas/` | 5 |
| 7 | `knowledge_state_machine.v1.0.yaml` | `01_contracts_and_schemas/` | 5 |
| 8 | `architecture_and_integration_boundary.v1.0.yaml` | `01_contracts_and_schemas/` | 6 |
| 9 | `compliance_review_contract.v1.0.yaml` | `01_contracts_and_schemas/` | 6 |
| 10 | `data_and_fixture_workflow.v1.0.yaml` | `01_contracts_and_schemas/` | 6 |
| 11 | `execution_critical_path_and_decision_gates.v1.0.yaml` | `01_contracts_and_schemas/` | 5 |
| 12 | M1 对象模型 Brief | `01_contracts_and_schemas/m1_object_model_brief.md` | — |
| 13 | M2 评测冻结 Brief | `01_contracts_and_schemas/m2_evaluation_freeze_brief.md` | — |
| 14 | M0 checker / fixtures / report / receipt | `ci/checkers/check_m0_*.py`、`ci/fixtures/`、本报告、`m0_delivery_receipt.yaml` | — |

**合计 57 条支持任务**，每条都带 `required_inputs` / `outputs` / `failure_state` / `owner_role` 四字段。

数量恒为 14：PRD 13 节 M0、14 节、17.1 与执行申请四处名称逐字一致，无第 15 项，也没有 18 项版回潮。

## 2. M0 通过标准的机器化

PRD 13 节 M0 的通过标准原本是两句自然语言。它们在这里各自变成一个确定性 Checker：

| 通过标准原文 | Checker | 结论 |
|---|---|---|
| 所有支持任务都有必需输入、输出、失败状态和负责角色 | `check_m0_contract_completeness` | PASS（57/57 条四字段齐全） |
| 与笛语现有资产零接触验证通过，现有 P7C 状态无漂移 | `check_m0_zero_contact` | PASS（扫描 120 个跟踪文本文件，遗留路径命中 0、写入动作命中 0） |
| 清单闭环（执行申请 Guardian 审查项②） | `check_m0_deliverable_closure` | PASS（14/14 存在，序号无碰撞，名称零漂移） |

三条判据的设计要点：

- **`owner_role` 必须是规范源里真实存在的角色**。角色名的唯一来源是 `role_operating_model.v0.2.yaml`——常规六角色取自 `roles`，`TEMPORARY_EXECUTION_WRITER` 取自角色不可用回退块的 `emergency_role_id`。写一个规范源里没有的名字（如 `DATA_TEAM_LEAD`）等于没有人真正负责，判 `OWNER_ROLE_UNKNOWN`。
- **`failure_state` 必须是具名状态，不能是散文**。"如果库存不对就应该停下来"读起来像个失败状态，但没法被别处引用或断言，判 `FAILURE_STATE_NOT_NAMED`。
- **零接触判的是方向与动作，不是关键词**。合同必须能写出 `P7C`／`DIFY`／`CSO` 才能定义边界，所以"提到名字"是合规内容；判据抓的是指向笛语现有仓的可执行路径、对其状态的写入调用、以及"已建立外部连接"的声明。
- **例外只有两种，且都不藏在代码里**：一是合同 `boundary_documentation_allowlist` 显式列出的 3 个文件（Founder 与 Guardian 可审阅，白名单若只写在代码常量里判 `ALLOWLIST_NOT_IN_CONTRACT`）；二是 `checker` 字段指向本判据的自有 fixture——它描述一次越界，不是越界本身。**别的 checker 的 fixture 不享此例外**（N57）。
- **扫描范围含未提交的新文件**。只扫 tracked 会让新落盘的越界文件在提交前隐身，而门禁的意义正是在提交之前拦下它。

## 3. 新增 fixtures

19 份，每份只行使一条判据：

| 正向 | 负向 |
|---|---|
| P15 支持任务四样俱全 | N42 缺失败状态 · N43 失败状态是散文 · N44 负责角色不在规范源 · N45 Founder 裁决前自称 FROZEN · N46 合同零支持任务 |
| P16 零接触干净态 | N47 遗留资产路径 · N48 向 P7C 回灌 · N49 M0 期声称外部已连接 · N50 凭证接触非 0 · N51 四类遗留资产覆盖不全 · N56 白名单藏在代码里 · N57 别的 checker 的 fixture 不享例外 |
| P17 十四项闭环 | N52 冒出第 15 项 · N53 清单声明了但磁盘没有 · N54 合同序号与清单对不上 · N55 交付物名称漂移 |

fixture 从不调用 `collect()`——payload 是字面量，所以被测代码造不出自己的"通过"证据。

另做了两次变异探针：把一条伪造的遗留仓路径塞进零接触 payload，checker 当场判 `LEGACY_ASSET_PATH`；再把同样的字符串写进一个新建的未跟踪文件，扫描同样抓到——证明它既不是空转，也不会让「尚未提交」成为藏身之处。

## 4. 目录 delta 适配（附录 A 的执行判断）

PRD 附录 A 给的是**推荐**目录树，并明确"具体目录应在 M0 根据现有仓库结构进行 delta 适配，不得未经检查直接覆盖现有命名"。我的适配决定与理由：

- 推荐树的根是 `projects/cross_brand_styling_expert_kernel/`。**本仓就是 D-01 裁决的那个独立项目空间**（不挂靠笛语现有仓），再在仓内嵌一层同名目录是冗余，因此编号目录直接落在仓根。
- `ci/checkers/fixtures/` 一项**复用仓内已有的 `ci/checkers/` 与 `ci/fixtures/`**，不新建第二套 CI 目录——这正是"不得覆盖现有命名"要防的事。
- **只创建本里程碑真正消费的目录**：`00_charter/`、`01_contracts_and_schemas/`、`02_benchmark_manifests/`、`11_reports_and_receipts/`。`03`—`10` 由对应里程碑开工时创建，现在预建就是一堆没人消费的空壳（EQ-4）。
- 完整映射表（含每个推荐目录延后到哪个里程碑）在 `project_charter.v1.0.yaml` 的 `directory_delta_adaptation`。

`02_benchmark_manifests/` 建了目录与一份边界说明，**里面没有任何 manifest**——目录名由 S5/D-27 固定，先把名字和边界钉住，避免 M2 时用错名字。

## 5. 红线自查（M0 十四条任务级禁止事项）

| 禁止事项 | 本轮实际 |
|---|---|
| 大规模知识蒸馏 / 品牌专属 Prompt / 复制品牌专属专家 | 未做。知识单元产出 0，候选产出 0 |
| 接入真实品牌生产与正式库存 / 创建 Serving / 自动内容发布 | 未做。六类外部集成 `m0_connected` 全为 false |
| 触碰、重写、漂移 P7C / Content Kernel / DIFY / CSO | 未做。零接触扫描命中 0 |
| 把候选知识标记为 accepted 或 production_servable | 未做。状态机七级，M0 无任何单元进入任何一级 |
| 生成隐藏品牌或夹具品牌语料 | 未做。`m0_generated_assets` 四项均为 0 |
| 获取、输出或持久化模型 API 明文凭证 | 未做。凭证接触计数 0 |
| 在 M1 Schema 冻结前生成夹具品牌资产 | 未做 |
| 创建或翻转 Serving / RAG / DIFY / 生产发布 / Commercial V1.0 状态 | 未做 |
| 为品牌复制独立内核 / 补写隐藏品牌专属 Prompt / 泄漏隐藏答案 | 未做 |
| 自行更改已冻结产品裁决 | 未做。十四项、五类品类、12+15 对象、七级优先级、22 条停止条件均按 PRD 原文落盘 |
| 接收、处理、保存或测试 Founder 真实品牌资料 | 未做 |
| 运行多模态识别或产生正式 `VisualAttributeExtractionResult` | 未做 |
| 建立人设记忆生产库 / 写入已发布观点 / 运行人设持久化 | 未做。只定义对象与 M1 Schema 要求 |
| 启用自动发布 | 未做。`publication_mode` 保持 `human_review` |

125—185 人月与 15—24 个月基线未改；M0 十四项清单未改；本任务未被表述为"M0 已完成"。

## 6. 我没有做、也不打算替 Founder 做的事

- **没有冻结任何 M2 阈值**。PRD 10.2 里标 `M2_FREEZE_REQUIRED` 的 20 项指标全部留白，由 Founder 在 M2 冻结时裁决（`COND-007`）。执行侧 AI 代冻阈值本身就是越权。
- **没有裁定"限额 POC 证据批次额度"**。PRD 15.6 把它的决策节点定在"M0 冻结时"、裁决人是 Founder，所以它在合规合同里登记为 `PENDING_FOUNDER_M0_DECISION`，等 Founder 在 M0 裁决时一并给值。**这是本次 M0 唯一一个到期未决的 Founder 事项**，需要你在裁决时点名。
- **没有做品牌档案单价校准**。PRD 8.7 要求"M0 以 3—5 个档案的实测工时校准单价后再入预算"，但同一份执行申请禁止 M0 生成任何档案——两条放在一起，M0 无法产生实测工时。我按"不生成"优先，把校准状态如实记为 `NOT_PERFORMED` 并注明随 M1 首批档案执行。**这是一处我按红线优先做的取舍，请你确认口径**。
- **没有自称已冻结**。全部 11 份合同状态都是 `M0_CANDIDATE_PENDING_FOUNDER_M0_DECISION`；checker 有一条 `PREMATURE_FROZEN_CLAIM` 专门抓自称 FROZEN/ACCEPTED 的合同。

## 7. 全量核验结果（本次落盘后重跑，不沿用）

| 项 | 结果 |
|---|---|
| 治理 Checker | 19 个全 PASS（原 16 + M0 新增 3） |
| Fixtures | 74/74 按声明行为（正向 17 / 负向 57） |
| PRD 合同 Checker | `check_prd_v1_2.py --require-archive` 62 项 PASS |
| DOCX 包审计 | 3 份 PASS |
| 指令投影漂移 | 0 |
| 支持任务四字段完备 | 57/57 |
| 零接触扫描 | 120 个跟踪文本文件，命中 0 |

## 8. 交给 Guardian 的十项审查点

执行申请第五节要求 Guardian 逐项返回结论而非只回"同意"。对应证据落点：

| 审查项 | 证据落点 |
|---|---|
| ① 范围一致 | 本报告 §5 红线自查；`m0_generated_assets` 四项为 0 |
| ② 清单闭环 | `check_m0_deliverable_closure`；本报告 §1 |
| ③ 边界安全 | `architecture_and_integration_boundary.v1.0.yaml`；`check_m0_zero_contact` |
| ④ 可验收性 | `check_m0_contract_completeness`；17 份新 fixtures |
| ⑥ 人设与语感闭环 | `capability_contract` C-13/C-14；M1 Brief 第 13—17 项；M2 Brief 第 12—13 项 |
| ⑦ 多模态事实边界 | `input_output_boundary` 七级优先级；`capability_contract.multimodal_visual_mechanism` |
| ⑧ 发布模式 | `compliance_review_contract.publication_governance`；`non_goals` NG-07 的 `misreading_guard` |
| ⑨ 扩展兼容 | `capability_contract.extension_ports`；`non_goals` NG-09；FR-27 |
| ⑩ M0 顶层清单 | `check_m0_deliverable_closure` 的名称逐条对账 |
| ⑤ 最终意见 | 由 Guardian 给出 APPROVE / APPROVE_WITH_CONDITIONS / REJECT |

## 9. 下一步

Guardian 独立审查 → 总顾问远程审查（不可用须 Founder 显式 DEFER/替位/豁免，不得静默跳过）→ Founder 作 **PASS / CONDITIONAL / BLOCK** 裁决。裁决为 PASS 或无阻塞 CONDITIONAL 后方可进入 M1；M1 起适用 `DIYU-CBFSK-FR-GRANULARITY-005` 的里程碑粒度框架。
