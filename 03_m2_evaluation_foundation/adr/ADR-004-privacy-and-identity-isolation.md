---
adr_id: ADR-004
title: 隐私与身份隔离
status: ACCEPTED
decision_date: "2026-08-13"
milestone: M2
execution_package: M2-EP01
ruling_anchors:
  - DIYU-CBFSK-FOUNDER-M2-CHARTER-001
is_red_line: true
minimal_implementation: >-
  确定性 Checker ci/checkers/check_m2_identity_isolation.py 对 Schema property、
  能力登记与依赖清单做结构化能力检测，命中五项禁止能力之一即 FAIL；
  禁止/允许能力清单落在 identity_isolation/identity_capability_isolation_contract.v0.1.yaml，
  是清单的唯一定义处。Outcome 数据只入候选台账，不直写真值源。
landing_milestone: M2（隔离 Checker 与能力清单）；此后每个里程碑持续生效，永不退役
not_building_now:
  - face_identification_1_to_n（1:N 人脸身份识别）
  - face_verification_1_to_1（1:1 人脸验证）
  - persistent_face_embedding（持久化人脸特征向量）
  - biometric_template_storage（生物识别模板存储）
  - cross_session_face_linking（跨会话面部关联）
activation_condition: 永不（NEVER）
activation_condition_is_never: true
---

# ADR-004 · 隐私与身份隔离

## 决策（红线，明文）

**项目永久坚持造型理解与身份识别解耦。** 上述五项能力的激活条件是**永不**——不是「暂缓」，不是「待裁决」，不设条件、不设审批路径。

这是 Founder 裁决原文（`DIYU-CBFSK-FOUNDER-M2-CHARTER-001`）：「项目永久坚持造型理解与身份识别解耦，不建设人脸身份识别、验证、模板存储或跨会话面部关联能力。」

## 解耦的技术含义

造型理解需要知道的是**这一次这张图里有什么视觉属性**，不需要知道**这是谁**，也不需要在下一次认出同一个人。

| 允许 | 为什么允许 |
|---|---|
| `face_region_localization_for_color_analysis` | 定位面部区域做肤色/色彩分析——只在本次任务内使用，不产生可跨会话比对的标识 |
| `task_scoped_non_identifying_visual_attributes` | 任务内的非身份性视觉属性（如肩线、比例） |
| `ephemeral_image_processing` | 处理完即丢弃，不留存 |
| `user_authorized_account_identity` | 普通账号登录与 API 鉴权——用户主动提供的账号身份，与生物识别无关 |

**关键区分**：定位一张脸在图上的位置 ≠ 认出这是谁。前者是几何，后者是身份。分界点在于是否产生**可跨会话比对的持久标识**——产生了就是禁止能力，无论叫什么名字。

## 为什么用结构化能力检测而不是全文关键词扫描

本 ADR 与 Founder 裁决原文里必然出现「人脸识别」「身份验证」这些词——它们出现在**禁止**的语境里。全文关键词扫描会把「我们禁止人脸识别」这句话本身判成违规，于是要么误报，要么被迫加一堆例外白名单，最后白名单大到什么也拦不住。

因此检测对象限定为：JSON/YAML Schema 的 property 名与枚举值、能力登记与服务组件声明、依赖清单中的生物识别实现。**不扫描散文与裁决文本。**

## Outcome 数据

内容表现、用户反馈与门店修改只进候选台账，不直接改写知识真源（`KSM-INV-03` / FR-20）。这条与身份隔离同源：不因为「数据来自真实用户」就给它超出候选的地位。
