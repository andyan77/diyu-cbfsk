---
adr_id: ADR-005
title: 评测锦标赛与最小可观测性
status: ACCEPTED
decision_date: "2026-08-13"
milestone: M2
execution_package: M2-EP01
ruling_anchors:
  - DIYU-CBFSK-FOUNDER-M2-CHARTER-001
minimal_implementation: >-
  只定义四维度指标与每次运行必须记录的字段（run_id / arm / 四维度度量 / 硬门结果），
  落在 evaluation_governance/benchmark_revision_protocol.v0.1.yaml 的 tournament_dimensions。
  不建评测执行框架、不建观测平台、不产任何评测资产。
landing_milestone: M2（指标与记录字段定义）；实际锦标赛运行在 M4，资产在 M2-EP02
not_building_now:
  - 观测平台（指标采集、看板、告警）
  - 评测执行框架与调度器
  - 自动回归流水线
  - 成本与延迟的实时采集埋点
activation_condition: 评测执行随 M4 基线锦标赛正式批次启动；观测平台须在有真实运行流量、且 Founder 认可投入产出后另行裁决。
---

# ADR-005 · 评测锦标赛与最小可观测性

## 决策

基线锦标赛**同时**衡量四个维度。任何一个维度缺席，比较结果都不成立。

| 维度 | 度量什么 | 为什么不能省 |
|---|---|---|
| 质量 | 评分卡得分、硬门通过与否 | 省了就不知道好不好 |
| 成本 | 每次运行的调用成本 | 省了会选出「好但用不起」的方案 |
| 延迟 | 端到端耗时 | 省了会选出「好但等不起」的方案 |
| 人工干预 | 需要人改多少、改哪里 | **最容易被省**——省了会把「模型很好」和「有人在后面一直补」混为一谈 |

人工干预维度直接对应 PRD 的「人工可发布率 ≥75%」：一个需要大量返工才能发布的方案，其质量分再高也不是好方案。

## 最小可观测性（本期唯一交付）

每次锦标赛运行必须记录：`run_id`、`arm`（对比臂）、四维度各自的度量值、硬门逐条 pass/fail。仅此而已——不建采集管道，先用运行时产出的结构化记录。

## 与 D-28 的关系

②③类任务（`mechanism_correctness` / `open_decision`）**禁止唯一 Gold Answer**，冻结对象是可接受决策边界。因此质量维度不是「与标准答案的匹配率」，而是「是否落在可接受决策边界内、多解族质量如何」。把开放题按唯一答案打分会触发 `SC-20`，停止 M2 冻结。

## 阈值不在本期冻结

四维度的具体阈值属 `M2_FREEZE_REQUIRED`，由 Founder 在 M2 冻结时裁决（`COND-007`）。本 ADR 只定义**测什么**，不定义**过线是多少**。M0 不得代为冻结阈值，M2-EP01 同样不得。
