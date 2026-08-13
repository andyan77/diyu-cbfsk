# M1-EP01 开工记录 · 核心语义与对象注册表

> 里程碑 M1｜执行包 `M1-EP01`｜task_class `L2`｜基线 `8eaf5f25987d787a546096b6a60a4e6a6b5a30f4`（M0 PASS 生效后的 main HEAD）

## 开工依据链

| 环节 | 对象 | 结论 |
|---|---|---|
| M1 计划预批准 | `DIYU-CBFSK-FOUNDER-M0-DECISION-001` `m1_pre_approval` | MILESTONE_PLAN_M1，EP01→EP02→EP03 串行 |
| 红线放行 | `DIYU-CBFSK-FOUNDER-M1-GATE-001` 第 1、4 条 | 红线改为「未经授权开始 M1 或 M2」；`m1_started` 授权条目绑定该裁决 |
| Guardian | delta 复核 `76a1394e`（APPROVE_WITH_CONDITIONS→RD-01）→ 复看 `8eaf5f25`（APPROVE，无遗留条件） | 合并前置成立 |
| 合并 | `1153fc7` → `8eaf5f2` 快进合并 | main HEAD 即 Guardian 审过的哈希，无未经审查的合并提交 |

**Milestone Plan 不另建文件**：MILESTONE_PLAN_M1 的全文已在 `DIYU-CBFSK-FOUNDER-M0-DECISION-001` 的 `m1_pre_approval` 内。另起一份计划文件会形成同一计划的第二处记录（违反 EQ-1），也与 FR-GRANULARITY-005 修正③「禁止先行建设执行框架本身」相悖。本记录只做指针。

## 目录落位

M1 对象模型落 `01_contracts_and_schemas/m1_object_model/`。理由：PRD 附录 A 推荐目录树中 M1 没有独立编号目录，`01_contracts_and_schemas/` 正是「合同与 Schema」的落点；建子目录而非平铺，是为了让 M0 已冻结的十一份合同与 M1 新增 Schema 在目录层就分得开。

**未修改 M0 已冻结文件**：`00_charter/project_charter.v1.0.yaml` 的 `directory_delta_adaptation` 是 M0 交付物且状态 `M0_FROZEN`，其哈希被 `m0_delivery_receipt.yaml` 钉死。本次目录决定记在本文件，不回头改冻结件。

## 两处口径不一致（如实记录，按更严的冻结口径执行）

| # | 处 | 裁决措辞 | M0 冻结真源 | 本包取值 |
|---|---|---|---|---|
| 1 | 输出对象数 | `DIYU-CBFSK-FOUNDER-M0-DECISION-001` `acceptance_gate` 写「11 个输出对象在 schema 层全部可寻址」 | `input_output_boundary.v1.0.yaml` `output_and_internal_audit_objects.count: 15`（`count_is_frozen: true`）；M1 Brief 第 3 节同为 15 | **15** |
| 2 | 事实优先级层数 | EP01 执行 Prompt 写「六层事实优先级可表达」 | `fact_and_rule_priority.ordered_levels` 共 **7** 级 | **七级** |

两处均按冻结真源执行：15 ⊃ 11、七级 ⊃ 六层，满足更严口径即同时满足两种读法，不需要产品裁决，因此不停工上报。若 Founder 认为裁决措辞才是准，须走产品裁决变更（M1 Brief 第 4 节：对象数量与命名属 M0 冻结项，M1 不得自行调整）。

## 本包交付范围

**做**：连续风格坐标空间；IN-03—IN-12 十份输入对象 Schema；D-20 五对象；D-21 平台语感；OUT-01—OUT-15 输出整包（逐对象可寻址）；Schema 注册表与输入输出覆盖映射表；覆盖率 checker 与正负 fixture。

**不做**（EP02／EP03 或后续里程碑）：五类品类适配合同（EP02）；扩展端口合同（EP03）；知识内容语料夹具；隐藏评测；任何夹具品牌资产。

## M1 阶段红线自检（M1 Brief 第 6 节）

本包不生成夹具品牌资产、不生成隐藏品牌或隐藏题、不接收 Founder 真实品牌资料、不运行多模态识别、不建人设记忆生产库、不启用自动发布、不把任何知识单元标记为 `founder_accepted` 或 `production_servable`。
