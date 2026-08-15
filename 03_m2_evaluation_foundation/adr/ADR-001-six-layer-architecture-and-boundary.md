---
adr_id: ADR-001
title: 六层架构与边界
status: ACCEPTED
decision_date: "2026-08-13"
milestone: M2
execution_package: M2-EP01
ruling_anchors:
  - DIYU-CBFSK-FOUNDER-M2-CHARTER-001
minimal_implementation: >-
  只落六层定义与 M1 对象→层映射文档（03_m2_evaluation_foundation/architecture/m1_object_layer_map.v0.1.yaml），
  由 check_m2_governance_landing 断言 12 输入 + 15 输出全部有归属层。不写任何运行代码。
landing_milestone: M2（层定义与映射）；运行层与 API 层的实现分别落在 M6 与商业形态裁决之后
not_building_now:
  - 运行层（服务进程、调度、编排）
  - API 层（对外接口、鉴权、配额）
  - 层间通信框架
  - 任何跨层运行时依赖注入机制
activation_condition: >-
  运行层随 M6 反退化实现启动；API 层须待商业交付形态由 Founder 裁决
  （M10 通过后、M11 设计冻结前）后才可启动。
---

# ADR-001 · 六层架构与边界

## 决策

项目采用**包含叙事平面与人设平面**的六层架构。分层的意义只有一个：让「哪一层可以覆盖哪一层的结论」成为结构问题，而不是每次实现时临时商量。

| 层 | layer_id | 承载 | 不承载 |
|---|---|---|---|
| L1 知识层 | `knowledge_layer` | 13 类知识单元与七级状态链 | 具体品牌事实、运行时库存 |
| L2 领域内核层 | `domain_core` | 通用专家内核、品类适配器、确定性约束与排序 | 表达风格、平台语感 |
| L3 人设平面 | `persona_plane` | 搭配师人设、记忆快照、观点账本、栏目续接、人设冲突 | 品牌硬事实（不得覆盖 L2/品牌真源） |
| L4 叙事平面 | `narrative_plane` | 叙事包、平台语感、自媒体表达模式 | 专业判断本身 |
| L5 交付面 | `delivery_surface` | 内容投影、发布决策与发布策略、扩展端口 | 知识晋级、评分裁决 |
| L6 评测与治理层 | `evaluation_and_governance` | 评测资产、硬门、状态位、确定性 Checker | 产品功能 |

## Domain Core 与 Delivery Surface 的分界

分界线落在 **L4 与 L5 之间**：

- **L1—L4 属 Domain Core**：判断「什么是对的搭配、由谁以什么口吻说」。这一段的正确性由知识状态链与硬约束决定，不因交付渠道改变。
- **L5 属 Delivery Surface**：决定「以什么形态送出去」。换渠道、换平台、换成 API，Domain Core 一行不改。

这条线是「内容先行、API 第二步」在架构上的含义：内容与 API 都只是 L5 的两种交付形态，**不是两套系统**。因此第二步做 API 时不需要重建内核——如果需要重建，说明有 Domain Core 的东西漏到了 L5。

## 事实优先级不因分层而改变

七级事实优先级由 M1 冻结的 `common_defs.schema.v0.1.json#/definitions/factPriorityLevel` 单独定义。分层**不引入第二套优先级**：L3 人设与 L4 叙事都不得覆盖 L2 的品牌真源与品类硬约束。若某次实现需要改变优先级，属 Charter 熔断条款 `FACT_PRIORITY_CHANGE_REQUIRED`，停止并提交 Founder 裁决。

## 本期为什么不建运行层

FR-GRANULARITY-005 修正③：不得先建执行框架再干活。当前没有任何运行时消费者——先建层间框架，等于给一个还没有用户的结构写调度代码。
