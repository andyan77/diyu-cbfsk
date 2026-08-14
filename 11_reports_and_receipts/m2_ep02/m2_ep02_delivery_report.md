# M2-EP02 交付报告

> 任务 `DIYU-CBFSK-M2-EP02-001`｜分级 `L2`｜授权 `DIYU-CBFSK-FOUNDER-M2-RESUME-AUTHORIZATION-001`
> 基线 `main = c3f6ad372306cc12f139cf38624e9a5cea2cf329`｜M1 批准提交 `2df11012da46ace0de7b7bce6d199a578d32d341`
> 分支 `candidate/m2`｜工作区 `/home/faye/diyu-cbfsk-m2`

## 1. 每 Phase 一行

| Phase | 结论 |
|---|---|
| P0 受控合并 | `merge` 非 `rebase`，保留 `main` 为祖先；14 处冲突全在允许更新面，冻结路径零冲突；`README-MOD-10` 撞号按规则重编为 `README-MOD-12` |
| P1 两条裁决落盘 | `OI-01` 标 `ADJUDICATED_NOT_IMPLEMENTED`（现役门禁一个未摘、未削弱）；`OI-06` `CLOSED`；`GR-GATE-01` 由新判据强制而非仅承诺 |
| P2 最终绑定 | `PROVISIONAL` 6 件 → `FINAL` 29 件，钉 Founder 批准的 M1 提交；33 条 M1 回执哈希逐件复算，零漂移 |
| P3 三层评分卡 | 三分类合同 + 三张卡 + 稳定率口径；②③类禁唯一 Gold Answer 且保全合法分歧；25 条硬约束双向全覆盖 |
| P4 基线锦标赛 | 四维度并列、不合成总分；dry-run 实跑两次字节相同；零真实模型调用；真实运行登记 `OD-M2-01` |
| **P5 隐藏评测资产** | **STOP: `HIDDEN_STORAGE_NOT_PROVISIONED` 已触发——未生成任何资产，未落主仓，等待 Founder 处置**（详见 §3） |
| P6 两项结转判据 | `RD-M1-02` 改为对 live git 比对 main 实际状态；`NB-M1FIX-01` 守 CI 依赖钉版本，两者各配负例夹具 |
| P7 退役前置清单 | 三层哈希逐层列明守什么、摘除后哪条硬门失去覆盖、有无替代；结论：L1 可替代，L2/L3 无替代 |
| P8 自检 | 31 Checker / 267 判据夹具 / 36 Schema 夹具全绿，退出码 0 |

## 2. Checker 汇总

| 项 | 数量 | 结果 |
|---|---|---|
| 确定性 Checker | 31（合并入 main 的 21 ＋ M2 累计 10） | 全绿 |
| 判据层 fixture | 267 | 267/267 按声明落 |
| M1 Schema 实例 fixture | 36 | 36/36 按声明落 |
| 信封实例 fixture | 13（9 负 4 正） | 13/13 按声明落 |
| 身份扫描用例 | 8（4 负 4 正） | 8/8 按声明落 |

本包新增 6 个 Checker：`check_sequential_registration`、`check_m2_gate_retirement_guard`、`check_m2_scoring_cards`、`check_m2_tournament`、`check_m2_hidden_assets`、`check_m2_main_state_guard`，各配负例夹具（分别 6／9／15／14／15／13 份）。

**证据等级** `runtime_verified`：`python3 ci/run_all_checks.py` 实跑退出码 0。

## 3. P5 隐藏评测资产：停止条件已触发（首要待裁事项）

**判定**：`STORE-A` 未 provision（`hidden_benchmark_storage_contract.allowed_storage[STORE-A].provisioned = false`），`COND-011` 状态 `OPEN`，该条件的 `owner` 与 `verification_role` 均为 Founder。

**执行侧做了什么**：一件隐藏资产都没生成，一个字节都没进主仓，`hidden_benchmark_storage_contract` 的任何字段都没改（它如实记着「未 provision」，改它才是问题）。

**为什么执行侧解不了**：`STORE-A` 的定义是「Planner / Codex / 知识引出工作面不可读」的独立私有仓库。由执行侧去创建它，等于执行侧天然拥有读权限——形式上 provision 了，实质上隔离失效。且「不得就近落在主仓」是明文红线：Git 克隆提供完整对象历史，先放主仓再迁走会留下永久副本，删除撤销不了泄漏。

**替代交付**：生成合同（解除阻塞后可直接执行的规则：抽样设计绑定、同质性控制、合成标记、可验证性原则）＋ 空清单（`count=0`，如实记录而非留白）＋ 停止记录。

**待 Founder 裁决**（记于停止记录 `founder_disposition_required`）：

| 选项 | 后果 |
|---|---|
| OPT-1（执行侧建议） | Founder 侧 provision `STORE-A` → 授权生成 → `COND-011` 关闭 |
| OPT-2 | 改选 `STORE-B`／`STORE-C`，需同步改存储合同与 `COND-011` |
| OPT-3 | 整体延后至 M2 冻结之后，**须同时裁决**「隐藏集须在 M2 冻结前建成」这条 M2 通过标准如何处理——执行侧不得自行放宽 |

**阻塞范围**：M2 冻结的隐藏资产部分、`COND-011` 关闭。**不阻塞**：EP02 其余 Phase 与 EP03 全部 Phase。

## 4. 联动更新项（按 `GR-LINKED-01` 列明）

| 主更新 | 机制强制的联动项 |
|---|---|
| `README.md` | `governance/baseline/founder_pinned_baseline.v0.1.yaml`：`post_change_binary_sha256` ＋ 追加 `README-MOD-12` |
| `governance/bootstrap/role_operating_model.v0.2.yaml` | 12 份投影由 `ci/compile_role_instructions.py --write` 重生成（drift=0） |
| 新增任一 Checker | `ci/run_all_checks.py` 注册表 ＋ `governance/gates/live_gate_roster.v0.1.yaml` |
| `execution_status` 迁移 | `founder_signoff_receipt` `authorized_values` ＋ `value_basis` ＋ `PRD_v1.2_change_map` ＋ README 状态块 |

## 5. EQ-1—EQ-5 自查

| 规则 | 自查结论 |
|---|---|
| EQ-1 | M1 哈希只在绑定表有产出处；`PROVISIONAL` Profile 已**删除**而非与 `FINAL` 并存；隐藏边界、抽样设计、能力清单、品类枚举一律引用不复制 |
| EQ-2 | 判据随合同演进：绑定合法性真值由「M1-EP01 注册表」改为「M1 Delivery Receipt」，因为 M1 已三包收口，旧口径已不成立 |
| EQ-3 | 6 个新 Checker 共 72 份 `expected=FAIL` 夹具；且「判据有没有被行使过」本身是判据（`DRY_RUN_NOT_EXECUTED`、`HARD_GATE_AGGREGATION_UNEXERCISED`、`IDENTITY_SCAN_WITHOUT_NEGATIVE_CASE`） |
| EQ-4 | 常量都有来源：硬约束 ID 取自五份适配器、冲突规则取自优先级表、知识状态取自 M0 状态机、就绪性取自存储合同 |
| EQ-5 | `check_m2_governance_landing` 原把「EP01 收尾态」当成永远的当前态，M1 收口后必然自相矛盾——改为按包区分并保留历史块，而不是在旧结构上加特例 |

## 6. 未决项

| # | 事项 | 处置 |
|---|---|---|
| 1 | **隐藏资产被 `HIDDEN_STORAGE_NOT_PROVISIONED` 阻塞** | 首要待裁，见 §3 |
| 2 | `OD-M2-01` 真实基线运行 | 未执行。成本 15–120 USD、2–8 小时，均为 `inferred` 估算非实测，交 M2 收口裁决 |
| 3 | `OI-01` 三层哈希退役 | `ADJUDICATED_NOT_IMPLEMENTED`。前置清单已出：L1 可由 artifact SHA256 替代，**L2／L3 无现成替代**，建议维持现状或只退 L1 |
| 4 | `COND-011` 未关闭 | 随 §3 一并处置 |
| 5 | `execution_run_id` 未纳入 `check_execution_uuid` | 仍需改既有 checker（不在允许更新面），路由 M2 收口 |
| 6 | `README-MOD-01` 排版错位 | 编号本身不重复不跳号，仅列表顺序有 M0 期遗留错位；未改写 M0 期历史，判据只断言「最新一条在最前」 |

## 7. 停止条件与红线

已触发：`HIDDEN_STORAGE_NOT_PROVISIONED`（见 §3）。
未触发：其余全部停止条件。熔断条款未触发——M1 顶层对象、核心语义、七级事实优先级与品类合同均未改动，本包只扩展引用层。
禁止产出核对：真实模型 API 调用 0、蒸馏调用 0、隐藏内容进主仓 0；`m2_frozen`／`knowledge_distillation_started`／`production_servable` 全部保持 `false`。


---

## 未决项全量披露（M2-EP04 追加，NB-M2-06）

Guardian 非阻塞发现 NB-M2-06：本报告此前只提了回执里的部分未决项。
**回执里有、报告里没有** 的条目，读者无从知道它存在——而读报告的人正是决定要不要往下走的人。
现按披露纪律补齐**全部**条目，不筛选：

| 编号 | 事项 | 当前状态 |
|---|---|---|
| `OD-M2-01` | 真实基线运行未执行 |  |
| `OI-M2-HIDDEN` | 隐藏评测资产被 HIDDEN_STORAGE_NOT_PROVISIONED 阻塞 |  |
| `OI-01` | 三层哈希退役 |  |
| `COND-011` | 隐藏存储 provision 条件未关闭 |  |
| `OI-02` | execution_run_id 未纳入 check_execution_uuid 守卫 |  |

本节由 `ci/checkers/check_disclosure_discipline.py` 的 `OPEN_ITEM_NOT_DISCLOSED` 判据守：
回执里出现的每一个未决项编号，都必须能在对应报告正文里被找到。
