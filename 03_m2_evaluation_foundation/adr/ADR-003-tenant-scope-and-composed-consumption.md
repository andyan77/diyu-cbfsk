---
adr_id: ADR-003
title: Tenant/Scope 与 M1→M2 组合消费
status: ACCEPTED
decision_date: "2026-08-13"
milestone: M2
execution_package: M2-EP01
ruling_anchors:
  - DIYU-CBFSK-FOUNDER-M2-CHARTER-001
minimal_implementation: >-
  Envelope 提供 scope{tenant_id,brand_scope,region_scope,store_scope} 字段合同，
  由 Profile 按对象类型声明是否必填；M2 消费 M1 一律经 Envelope/Profile 引用，
  in_place_modification_allowed 常量 false。本期单租户（SINGLE_TENANT_M2）。
landing_milestone: M2（字段合同与组合消费）；多租户隔离实现随商业形态裁决后的里程碑
not_building_now:
  - 多租户数据隔离实现
  - 租户级权限与配额
  - 跨租户数据共享策略
  - 租户级模型与知识分区
activation_condition: 多租户实现须待商业交付形态由 Founder 裁决后启动；在此之前 scope 字段只记录，不驱动任何隔离逻辑。
---

# ADR-003 · Tenant/Scope 与 M1→M2 组合消费

## 决策

M2 **只能**以组合式引用消费 M1 产物，禁止原位修改 M1 冻结物。作用域信息作为字段合同先行落位，但本期不驱动任何隔离行为。

## 组合消费怎么落

| 机制 | 文件 | 作用 |
|---|---|---|
| Envelope | `envelope/m1_to_m2_envelope.schema.v0.1.json` | 包装单个 M1 产物：从哪个 Commit 的哪个文件来、指纹是什么、按什么方式消费 |
| Profile | `envelope/profile_composition.schema.v0.1.json` | 具名的 Envelope 组合视图，并按对象类型声明条件字段组是否必填 |
| 绑定表 | `envelope/m1_source_binding.v0.1.yaml` | M1 产物 SHA256 的唯一记录处 |

**只包装、不复制**：被包装对象的内容一个字节都不进信封（`additionalProperties: false` 强制）。复制会造出第二份真源，日后两边各改各的，谁也说不清哪个是对的（EQ-1）。

## 为什么是 PROVISIONAL

本包基线是 M1-EP01 收口 Commit `6499431c66f7bf4a234bd830ee4c810e1ac78694`。M1 尚未整体收口，因此当前 Profile 一律 `binding_status: PROVISIONAL` + `final_m1_binding_required: true`。

- 既有 M1 冻结物字节变了 → `M1_FROZEN_ARTIFACT_DRIFT`，熔断，停。
- 只是新增了 M1-EP02/EP03 产物 → `REBIND_AND_RETEST`，由 M2-EP02 重绑并重测。

两者不可混为一谈：前者是有人动了不该动的东西，后者是正常前进。

## 单租户是决定，不是遗漏

本期明确写 `tenant_id: SINGLE_TENANT_M2`。写下来而不是留空，是为了让「现在只有一个租户」成为可被检查的事实，而不是将来某个人看到空字段时自行推断。
