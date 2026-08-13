---
adr_id: ADR-006
title: Canonical Connector 边界
status: ACCEPTED
decision_date: "2026-08-13"
milestone: M2
execution_package: M2-EP01
ruling_anchors:
  - DIYU-CBFSK-FOUNDER-M2-CHARTER-001
minimal_implementation: >-
  只定义 Adapter 合同的形状——对外连接必须经具名 Adapter，声明方向、作用域、
  事实优先级归属与失败状态；不写任何连接器实现，不接任何外部系统。
landing_milestone: M2（Adapter 合同形状）；实际连接器在 M11 真实品牌注入与 M12 生产加固
not_building_now:
  - 任何品牌库连接器
  - 任何渠道／平台发布连接器
  - Billing
  - 开发者门户
  - Marketplace
activation_condition: >-
  品牌库与渠道连接器随 M11 真实品牌注入启动（需 Founder 精确 Prompt 批准，属不可逆包）；
  Billing／开发者门户／Marketplace 的激活条件＝商业交付形态由 Founder 裁决
  （M10 通过后、M11 设计冻结前），在此之前一律不得建设。
---

# ADR-006 · Canonical Connector 边界

## 决策

所有对外连接（品牌库、渠道、平台）只经 **Adapter 合同**。内核不认识任何具体外部系统。

## Adapter 合同的形状（本期唯一交付）

每个 Adapter 必须声明四件事：

| 声明 | 含义 |
|---|---|
| `direction` | `inbound`（外部事实进来）／`outbound`（内容出去）。双向 Adapter 不允许——方向混在一起就说不清是谁污染了谁 |
| `scope` | 租户／品牌／区域／门店作用域（承接 ADR-003） |
| `fact_priority_binding` | 进来的事实落在七级优先级的哪一级。外部数据不因「来自官方接口」自动升为权威事实 |
| `failure_state` | 连接失败时的 fail-closed 状态，取自 M1 `common_defs` 的 `failClosedState` |

**inbound 的硬约束**：外部事实一律先落候选，不得直写知识真源（与 `KSM-INV-03` 同源）。

**outbound 的硬约束**：发布必须经 `PublicationPolicy` 与 `PublicationDecision`，默认人工审核在环；自动发布只在 Founder 按租户／品牌／账号／风险级别显式授权后开启（D-25），硬门 `unauthorized_auto_publish_rate=0`。

## 商业化设施为什么在这里

Billing、开发者门户、Marketplace 都是**对外交付形态**，属本 ADR 的边界内。它们的激活条件不是技术条件而是商业裁决——把它们写进本 ADR 的「当前不建设」，就让「还没裁决就不许建」成为可被检查的架构约束，而不是一句口头承诺。当前状态见 `commercial_decision_record.v0.1.yaml`。

## 本期真实状态

连接器数量 **0**。合同定义了形状，仓库里没有任何实现，也没有任何外部依赖。
