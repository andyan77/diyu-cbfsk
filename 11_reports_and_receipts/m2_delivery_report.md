# M2 里程碑交付报告（EP01 ＋ EP02 ＋ EP03）

> 里程碑 M2｜计划 `MILESTONE_PLAN_M2 v1.1.0`｜分支 `candidate/m2`
> 授权链：`DIYU-CBFSK-FOUNDER-M2-CHARTER-001` → `DIYU-CBFSK-FOUNDER-M2-RESUME-AUTHORIZATION-001`（含 EP03 精确 Prompt 批准）
> M1 批准提交 `2df11012da46ace0de7b7bce6d199a578d32d341`｜合并基线 `main = c3f6ad372306cc12f139cf38624e9a5cea2cf329`

## 1. 结论

M2 三个执行包全部完成并形成冻结候选。**`m2_frozen` 仍为 `false`**——冻结自 Founder 收口签署起生效。

全量确定性核验：**32 Checker / 276 判据夹具 / 36 Schema 夹具全绿，退出码 0**（`runtime_verified`）。

**有一项未完成，且不是执行侧能解决的**：隐藏评测资产因 `STORE-A` 未 provision 被 `STOP: HIDDEN_STORAGE_NOT_PROVISIONED` 阻断，一件未产。详见 §4。

## 2. 三包交付

| 包 | 交付 |
|---|---|
| EP01 | M1→M2 Envelope/Profile（PROVISIONAL）、六份最小 ADR、身份识别永久隔离、评测治理基础三件套 |
| EP02 | 受控合并 main、两条裁决落盘、绑定升 FINAL（29 件）、D-28 三层评分卡、锦标赛四维度＋dry-run 骨架、两项结转判据 |
| EP03 | 跨包一致性核验、M2→M3/M4 接口交接面、冻结候选、全量回归、Report ＋ Receipt |

## 3. M2 冻结候选内容

**已形成候选**：Envelope/Profile 合同与 FINAL 绑定（29 件，钉 Founder 批准的 M1 提交）；六份 ADR 与六层架构映射；身份识别隔离能力清单（激活条件＝永不，红线）；评测治理三件套（M2 冻结 Brief 第 2 节第 8/9/10 项）；D-28 三分类合同与三张评分卡；核心决策逻辑稳定率口径；锦标赛四维度合同与 dry-run 骨架；隐藏资产生成合同与可验证性原则。

**明确未冻结**：全部评测阈值（`M2_FREEZE_REQUIRED`，`COND-007`）；隐藏资产本体（未生成）；真实基线运行结果（`OD-M2-01` 未执行）；锦标赛排序权重（不合成单一总分）。

## 4. 首要待裁：隐藏评测资产被阻断

`STORE-A` 未 provision（`hidden_benchmark_storage_contract.allowed_storage[STORE-A].provisioned = false`），`COND-011` 状态 `OPEN`，owner 与 verification_role 均为 Founder。

执行侧**一件资产未产、一个字节未进主仓、存储合同一字未改**。执行侧不能自行解决：`STORE-A` 按定义是「Planner／Codex／知识引出工作面不可读」的独立私有仓库，由执行侧创建它就等于天然拥有读权限——形式上 provision 了，实质上隔离失效。而「不得就近落在主仓」是明文红线：Git 克隆提供完整对象历史，先放主仓再迁走会留下永久副本，删除撤销不了泄漏。

**这一项直接影响 M2 能否冻结**：M2 冻结 Brief 第 6 节要求「30—50 个合成封闭未见品牌须在 M2 冻结前建成」，该条**尚未满足**。执行侧不得自行放宽。

| 选项 | 后果 |
|---|---|
| **OPT-1（建议）** | Founder 侧 provision `STORE-A` → 授权生成 → `COND-011` 关闭 → M2 可完整冻结 |
| OPT-2 | 改选 `STORE-B`／`STORE-C` 并 provision，需同步改存储合同与 `COND-011` |
| OPT-3 | 隐藏资产整体延后至 M2 冻结之后，**须同时裁决**上述 M2 通过标准条款如何处理 |

## 5. 全部未决项与建议处置

| # | 事项 | 状态 | 建议处置 |
|---|---|---|---|
| 1 | 隐藏评测资产阻断 | `STOP` 已触发 | OPT-1：Founder 侧 provision `STORE-A` |
| 2 | `OD-M2-01` 真实基线运行 | 未执行 | 收口时裁决是否执行。估算 15–120 USD、2–8 小时，`evidence_level: inferred`（**非实测**），不得当预算承诺 |
| 3 | `OI-01` 三层哈希退役 | `ADJUDICATED_NOT_IMPLEMENTED` | 前置清单结论：L1 可由 artifact SHA256 替代，**L2／L3 无现成替代**。建议维持现状，或只退 L1、保留 L2/L3 |
| 4 | `COND-011` | `OPEN` | 随 #1 一并处置 |
| 5 | 全部评测阈值 | `M2_FREEZE_REQUIRED` | 收口时由 Founder 裁决（`COND-007`） |
| 6 | `execution_run_id` 未纳入 `check_execution_uuid` | 未覆盖 | 需改既有 checker（不在允许更新面）。建议作为独立治理动作单独授权 |
| 7 | `README-MOD-01` 排版错位 | 已知 | 编号不重复不跳号，仅 M0 期列表顺序遗留。建议不动 M0 期历史 |

## 6. 判据体系（M2 新增 11 个）

`check_sequential_registration`（顺序登记撞号）、`check_m2_gate_retirement_guard`（门禁静默摘除）、`check_m2_governance_landing`、`check_m2_envelope_contract`、`check_m2_identity_isolation`、`check_m2_evaluation_governance`、`check_m2_scoring_cards`、`check_m2_tournament`、`check_m2_hidden_assets`、`check_m2_main_state_guard`（main 实际状态）、`check_m2_cross_package_consistency`。

三个判据补的是**此前无人守的缺口**：
- 顺序登记编号撞号——EP02 合并时才发现两分支都取了 `README-MOD-10`，此前没有任何判据在守
- 现役门禁静默摘除——此前摘掉一个 checker 只需从注册表删一行
- `main` 实际状态——此前只有声明式 `merge_state`，而声明字段永远与自己一致，因此永远为绿

## 7. 红线与禁止产出核对

真实模型 API 调用 **0**；蒸馏调用 **0**；隐藏内容进主仓 **0**；`m2_frozen`／`knowledge_distillation_started`／`production_servable` 全部 `false`；Billing／开发者门户／Marketplace **0**；人脸识别类能力 **0**（结构化扫描 419 份文件零命中）；对 M1 冻结物的原位修改 **0**（33 条 M1 回执哈希逐件复算，零漂移）。

熔断条款未触发：M1 顶层对象、核心语义、七级事实优先级与品类合同均未改动。

## 8. 审查状态（如实）

Guardian **未审查**；总顾问 **未审查**；Founder **未裁决**。按授权，两包完成后统一进行一次 Guardian → 一次总顾问 → 一次 Founder 裁决。本报告的全绿结论**只是执行侧自检**，不代替任何一方审查。

合并 `main` 三项前置尚未齐备，本包**未合并、未自行合并**。


---

## 未决项全量披露（M2-EP04 追加，NB-M2-06）

Guardian 非阻塞发现 NB-M2-06：本报告此前只提了回执里的部分未决项。
**回执里有、报告里没有** 的条目，读者无从知道它存在——而读报告的人正是决定要不要往下走的人。
现按披露纪律补齐**全部**条目，不筛选：

| 编号 | 事项 | 当前状态 |
|---|---|---|
| `OI-M2-HIDDEN` | 隐藏评测资产被 HIDDEN_STORAGE_NOT_PROVISIONED 阻断 |  |
| `OD-M2-01` | 真实基线运行未执行 |  |
| `OI-01` | 三层哈希退役 |  |
| `COND-011` | 隐藏存储 provision 条件未关闭 |  |
| `COND-007` | 全部评测阈值仍为 M2_FREEZE_REQUIRED |  |
| `OI-02` | execution_run_id 未纳入 check_execution_uuid 守卫 |  |
| `OI-03` | README-MOD-01 列表排版错位 |  |

本节由 `ci/checkers/check_disclosure_discipline.py` 的 `OPEN_ITEM_NOT_DISCLOSED` 判据守：
回执里出现的每一个未决项编号，都必须能在对应报告正文里被找到。
