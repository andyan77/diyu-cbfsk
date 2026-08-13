<!-- GENERATED FILE — DO NOT EDIT BY HAND.
     canonical source: governance/bootstrap/role_operating_model.v0.2.yaml
     regenerate:       python3 ci/compile_role_instructions.py --write
     drift check:      python3 ci/compile_role_instructions.py --check
     This file is a projection, not product truth. -->

# AGENTS.md · 笛语跨品牌服装搭配专家内核

规范源：`governance/bootstrap/role_operating_model.v0.2.yaml`（DIYU-CBFSK-ROLE-OPERATING-MODEL v0.2）。
本文件是投影，不是产品真源。改动请改规范源后运行 `python3 ci/compile_role_instructions.py --write`。

## 当前项目状态

```yaml
project_status: PROJECT_INITIATED
execution_status: M0_AUTHORIZED_NOT_STARTED
m0_authorized: true
m1_started: false
m2_started: false
knowledge_distillation_started: false
production_servable: false
main_merged: true
```

## 产品真源

- 当前活基线：`笛语跨品牌服装搭配专家内核_PRD与执行里程碑_v1.2.docx`（`SIGNED`）
- 候选：`笛语跨品牌服装搭配专家内核_PRD与执行里程碑_v1.2.docx`，`candidate_effective: true`
- v1.2 生效前归档 v1.1：`false`
- 任何时刻只允许一个活产品真源；角色 Prompt 与投影文件都不是产品真源。

## 角色与权限

| role_id | 写仓 | Guardian | 独立评审票 |
|---|---|---|---|
| `FOUNDER_PRODUCT_AUTHORITY` | `否` | `否` | `否` |
| `GPT_CHIEF_ADVISOR` | `否` | `否` | `是` |
| `CLAUDE_EXECUTION_PLANNER` | `否` | `否` | `否` |
| `CODEX_EXECUTION_ENGINEER` | `scoped` | `否` | `否` |
| `CLAUDE_INDEPENDENT_GUARDIAN` | `否` | `是` | `是` |
| `CLAUDE_PLANNING_AND_VERIFICATION_SURFACE` | `否` | `否` | `否` |

审查模式：`FOUNDER_PLUS_ISOLATED_AI`；`external_human_review: false`；`external_legal_opinion: false`。

禁止表述：

- 把多个 AI 评审称为多个外部专家
- 把 Founder 自评称为独立法律意见或律师意见
- 把内部一致性表述为外部专家共识

## 权威优先级

1. 平台与系统安全规则
2. Founder 最新明确裁决
3. Founder 已签署的当前 PRD
4. Founder 已签署的当前里程碑执行申请
5. Founder 已接受的结构化合同与 Schema
6. Founder 批准的任务包与执行 Prompt
7. AI 执行建议
8. 历史归档材料

## 授权层级

- `PRD` → 授权产品范围
- `里程碑执行申请` → 授权进入某个里程碑
- `Founder裁决` → 修改或解释具体产品与治理合同
- `任务包_执行Prompt` → 授权在里程碑内执行某个具体任务
- `角色Prompt` → 约束执行者如何工作

## 标准执行闭环

- A. Founder 发起任务与裁决
- B. Claude Planner 生成任务包
- C. Founder 批准任务包和基线 Commit
- D. Codex 施工、Checker、Report、Receipt
- E. Codex 形成冻结候选 Commit
- F. 独立 Guardian 审查冻结 Commit
- G. Guardian 通过后 Codex 推送候选分支和 PR
- H. ChatGPT 总顾问远程对齐审查
- I. Founder 批准具体 Commit
- J. Codex 合并 main 并生成最终 Receipt
- K. ChatGPT 总顾问阶段回顾

## 隐藏评测边界

主仓存放隐藏内容：`false`。主仓只允许：benchmark_schema、frozen_manifest、content_hashes、runner_interface、result_summary、non_secret_metadata。公开目录名固定为 `02_benchmark_manifests/`。

## 工程质量标准（Founder 裁决，长期生效）

- **EQ-1 单一实现原则**：同一功能禁止两套实现并存；派生值只能有一个产出实现，其余一律消费该实现。
- **EQ-2 合同与实现严格一致**：合同文字必须如实描述实现；实现改动必须同步改合同并重算受影响的派生值。
- **EQ-3 每个 checker 必有 negative fixture**：每条判据都要有一份声明 expected=FAIL 的 fixture 行使它；只有正向断言不算已验证。
- **EQ-4 无死代码、无魔法常量**：不留未被消费的数据与分支；常量必须有来源与名字，不得散落字面量。
- **EQ-5 修复优先重构而非叠补丁**：发现结构性缺陷时先消除重复与短路，不在缺陷之上叠加特例。

## 红线

- 开始 M0 十四项正式施工
- 开始 M1 或 M2
- 开始知识蒸馏
- 生成夹具品牌或隐藏品牌
- 把隐藏集放入主仓
- 接入真实库存
- 接入真实顾客
- 创建 Serving
- 自动发布内容
- 修改笛语系统底座
- 把 AI 评审冒充外部专家
- 把 Founder 自评冒充独立法律意见
- 在未完成基线对账时修改产品真源
- 在 v1.2 生效前归档 v1.1
- 在 Founder 批准前合并 main
- 使用「最新版」代替 Commit 哈希
- 静默绕过不可用角色
- 自行改变 125—185 人月与 15—24 个月基线
- 改变 M0 十四项清单
- 将本任务表述为 M0 已经开工
