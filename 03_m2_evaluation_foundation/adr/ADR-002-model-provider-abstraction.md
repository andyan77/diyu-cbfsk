---
adr_id: ADR-002
title: Model Provider Abstraction
status: ACCEPTED
decision_date: "2026-08-13"
milestone: M2
execution_package: M2-EP01
ruling_anchors:
  - DIYU-CBFSK-FOUNDER-M2-CHARTER-001
nfr_anchors:
  - NFR-08
minimal_implementation: >-
  只定义模型无关的接口合同：调用点必须声明 provider、model_id、model_version 与用途，
  并把这三项写入 DecisionTrace 的 model_versions。不写适配器代码、不选型、不接任何供应商。
landing_milestone: M2（接口合同）；实际多供应商适配随 M4 基线锦标赛与 M6 实现落地
not_building_now:
  - 自动路由 / 智能选路
  - 自托管推理
  - 供应商 SDK 适配层
  - 模型能力探测与自动降级
activation_condition: >-
  多供应商适配随 M4 基线锦标赛需要真实横评时启动；自托管与自动路由须 Founder 单独裁决，
  在成本与延迟维度有实测证据之前不启动。
---

# ADR-002 · Model Provider Abstraction

## 决策

承接 NFR-08：系统对模型供应商保持无关。任何调用模型的位置只依赖一份**模型无关合同**，不直接依赖某家供应商的调用形态。

## 最小合同（本期唯一交付）

每个模型调用点必须能回答三个问题，并且答案要落到 `DecisionTrace.model_versions`：

| 字段 | 含义 | 为什么必须有 |
|---|---|---|
| `provider` | 供应商标识 | 换供应商时能定位受影响的调用点 |
| `model_id` | 模型标识 | 「用了大模型」不是可复算的记录 |
| `model_version` | 版本 | 模型版本变化后须重新标定（`reviewer_calibration_contract`） |
| `purpose` | 用途（引出／对抗／评审／生成） | 知识状态链要求区分候选来源与评审来源 |

## 为什么不做自动路由

自动路由要在质量、成本、延迟之间做权衡，而这四个维度的实测数据要到 M4 基线锦标赛才有（ADR-005）。在没有数据时写路由策略，等于把猜测固化成代码。

## 与知识状态链的关系

模型输出一律是候选（PRD-8.1 / P-06）。本抽象**不**改变这一点：无论换哪个供应商，输出仍从 `model_elicited_candidate` 起步，不得因供应商更「权威」而跳级。
