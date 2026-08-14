# M2-EP04 交付报告 · M2 收口修复

> 任务 `DIYU-CBFSK-M2-CLOSEOUT-REPAIR-001` · 分级 `L3_CRITICAL_EVALUATION_CLOSEOUT`
> 起点 `3008f56b2c200324b2f2cd1babafdef1950b5bc6` · 分支 `candidate/m2` · 基线 `main = c3f6ad37…`
> 里程碑裁决 **`BLOCK_M2_FREEZE_AND_MERGE`**（`DIYU-CBFSK-FOUNDER-M2-CLOSEOUT-001`）

---

## 一句话

**18 项强制交付里 14 项到 `READY`，4 项 `PARTIAL`——四项卡在同一个条件上：隐藏侧存储未就绪。**
这不是四个独立缺口，是一个缺口的四处露头。

## 一、18 项交付状态表

清单读自 `01_contracts_and_schemas/m2_evaluation_freeze_brief.md` 第 2 节，
**不由候选自述**：`check_m2_deliverable_closure` 直接解析 Brief 表格取序号与名称。

| # | 交付物 | 状态 |
|---|---|---|
| 1 | `benchmark_capability_matrix.v0.1.yaml` | `READY` |
| 2 | `unseen_brand_split.v0.1.yaml` | **`PARTIAL`** |
| 3 | `unseen_category_edge_cases.v0.1.yaml` | **`PARTIAL`** |
| 4 | `expert_scoring_rubric.v0.1.yaml` | `READY` |
| 5 | `narrative_scoring_rubric.v0.1.yaml` | `READY` |
| 6 | `hard_gate_definitions.v0.1.yaml` | `READY` |
| 7 | 泄漏检查器 / 冻结清单 / 回执 | **`PARTIAL`** |
| 8 | `reviewer_calibration_contract.v0.1.yaml` | `READY` |
| 9 | `evaluation_sampling_design.v0.1.yaml` | `READY` |
| 10 | `benchmark_revision_protocol.v0.1.yaml` | `READY` |
| 11 | 泄漏 ＋ 同质性双检查报告 | **`PARTIAL`** |
| 12 | `persona_continuity_scoring_rubric.v0.1.yaml` | `READY` |
| 13 | `social_media_native_voice_scoring_rubric.v0.1.yaml` | `READY` |
| 14 | `multimodal_attribute_benchmark.v0.1.yaml` | `READY`（边界待 Founder 批准） |
| 15 | `multimodal_confidence_calibration_contract.v0.1.yaml` | `READY`（同上） |
| 16 | `five_category_readiness_definition.v0.1.yaml` | `READY` |
| 17 | `evaluation_task_class_contract.v0.1.yaml` | `READY` |
| 18 | `acceptable_decision_boundary_registry.v0.1.yaml` | `READY` |

**四态是合同不是形容词**：`READY` ＝ 文件与实际内容均存在 ＋ 满足最低数量 ＋ Schema 校验通过
＋ 正负例通过 ＋ 引用可解析 ＋ 证据哈希完整，且**尚未** Founder 冻结。
`FROZEN` 另需 Founder 签署具体 Commit 与资产版本。**当前 `FROZEN` 数为 0。**

判据不因「现实是 `PARTIAL`」而失败——它只在**有人声称候选已形成或 M2 已冻结**时才拦。
`m2_candidate_formed` 与 `founder_signature_eligible` 均为 `false`，因此判据绿而事实不绿，两者并存且各自如实。

## 二、校准执行证据

| 项 | 值 | 证据等级 |
|---|---|---|
| 公开校准集 | **90 例**，5 品类 × 3 任务类型 × 3 风险等级 = **45 格无一为空**，每格 2 例 | `runtime_verified` |
| 场景文本重复 | **0**（90 条各不相同） | `runtime_verified` |
| ②③ 类携带唯一 Gold Answer | **0** | `runtime_verified` |
| 高风险例 | 30 例，Founder 覆盖 100%、不可抽样 | `runtime_verified` |
| 可接受决策边界族 | 15 个（机制 8 / 开放 7），每族均有 `out_of_boundary` | `runtime_verified` |
| 评审 Prompt | 已落盘，sha256 由判据现算比对 | `runtime_verified` |
| **GPT 侧评审记录** | **0 条** | — |
| **Claude 侧评审记录** | **0 条** | — |

**两侧评审都没有执行。** 状态如实置 `CALIBRATION_REVIEW_EVIDENCE_MISSING`，
未用任何模拟分数填充。理由写在状态文件里：分歧率的全部意义在于两位评审互不知道对方判了什么；
同一个执行侧写两份，两份之间的差异是这个执行侧编出来的，测出来的不是分歧，是想象力。

因此 25 条 `M2_FREEZE_REQUIRED` 指标**没有建议值**——不是漏写，是没有校准数据时给出的建议值就是编的。
另 9 条有建议值的，全部来自 PRD 已给的值，`evidence_source` 逐条写明。

## 三、Guardian 六条非阻塞发现

| 编号 | 处置 | 关键证据 |
|---|---|---|
| `NB-M2-01` | 受控位授权与 main 追认引用的裁决，现场解析文件与具名条款路径 | 捏造裁决 ID 的 6 条负例已落盘；执行时当场发现 `EXEC-REQ-M0-003` 是执行申请非裁决，按来源类型分流而非开豁免 |
| `NB-M2-02` | 合规台账下限由 payload 改为模块常量（夹具再也压不低），补 11 条负例；全仓横扫 | 实跑：**523 条声明错误码，376 条有夹具行使，147 条挂账**，装棘轮：上限只降不升，新增 checker 零欠账 |
| `NB-M2-03` | 覆盖面数字改实测值 | EP01 报告 **235 → 270**，里程碑报告 **255 → 419**；在各自提交上建临时 worktree 跑该提交自带的 checker 实测 |
| `NB-M2-04` | 12 条符号名回填真实完整哈希 | 用各条已登记的 `binary_sha256` 反查 README 历史 blob，12 条全部命中且互不冲突；末条自指按 `self_reference_limitation` 处理 |
| `NB-M2-05` | 工作面见证改自动发现 | 目录扫描替代硬编码单一文件；新增 `M2-EP04` 分册，其中**不伪造** Guardian 记录 |
| `NB-M2-06` | 披露纪律判据 | 判据当场查出 **4 份报告共 12 条未决项未披露**，已逐份补齐全量披露节 |

## 四、新增文件清单

**评测内容（`03_m2_evaluation_foundation/`）**

- `closure/m2_deliverable_coverage_map.v0.1.yaml`
- `capability_matrix/benchmark_capability_matrix.v0.1.yaml`
- `gates/hard_gate_definitions.v0.1.yaml`
- `splits/unseen_brand_split.v0.1.yaml`、`splits/unseen_category_edge_cases.v0.1.yaml`
- `scoring/` 七类纵向能力卡 ＋ `acceptable_decision_boundary_registry.v0.1.yaml`
- `calibration/public_calibration_set.v0.1.yaml`（90 例）、`review_prompt.shared.v0.1.md`、
  `calibration_review_state.v0.1.yaml`、`calibration_aggregation.v0.1.yaml`、
  `threshold_freeze_decision.v0.1.yaml`、`reviews/*.jsonl`（0 条，如实为空）
- `steward/hidden_asset_steward_prompt.v1.0.0.md`、`steward/hidden_generation_input_bundle.v1.0.0.yaml`

**公开清单（`02_benchmark_manifests/`）**：`benchmark_freeze_receipt.v0.1.yaml`、
`leakage_and_homogeneity_double_check_report.v0.1.md`

**治理（`governance/`）**：`founder_rulings/DIYU-CBFSK-FOUNDER-M2-CLOSEOUT-001.yaml`、
`gates/milestone_closure_coverage_rule.v0.1.yaml`、`gates/error_code_fixture_coverage_ledger.v0.1.yaml`、
`conditions/m2_condition_state_semantics.v0.1.yaml`、`reports/guardian_report_registry.v0.1.yaml`、
`reports/guardian_review_report.3008f56b.PENDING.md`、`workspaces/workspace_attestation.M2-EP04.yaml`

**判据（`ci/checkers/`，9 个）**：`check_m2_deliverable_closure`、`check_milestone_closure_coverage`、
`check_m2_capability_matrix`、`check_m2_calibration_set`、`check_m2_calibration_review`、
`check_error_code_fixture_coverage`、`check_disclosure_discipline`、`check_guardian_report_binding`、
`check_m2_hidden_generation_readiness`

## 五、联动更新项（OI-06 口径，逐条列明）

| 主动作 | 机制强制的联动登记 |
|---|---|
| 改 `README.md` | `founder_pinned_baseline` 新增 `README-MOD-14` ＋ 更新 `post_change_binary_sha256` |
| 新增 9 个 checker | `ci/run_all_checks.py` 注册表 ＋ `live_gate_roster` 由 32 增至 **41** |
| 新增判据错误码 | `error_code_fixture_coverage_ledger` 重算（实跑，不手改数字） |
| EP04 描述当前态 | 里程碑回执改 `describes_current_state: false` ＋ `superseded_by: M2-EP04`，**其记录值一字未改** |
| 重命名 `RESUME-AUTHORIZATION` | 全仓 20 处引用同步更新 ＋ 在该裁决内留 `naming_correction` |

## 六、执行侧当场发现并如实上报的三件事

1. **`D-10` 编号对不上。** 任务 Prompt 引 `D-10`「商品属性来源于品牌专属数据库、不做图像识别提取」；
   核对真源后：`D-10` 的标题是「运行时模型合同」，所引实质内容逐字对应 **`D-12`「商品属性来源」**，
   而 `D-12` 已被 `D-23` 在 PRD v1.2 中部分改判为「分层引入视觉推断」。
   执行侧**未放宽也未改写任何裁决**，按 `D-12` 与 `D-23` 的**交集**定义多模态评测范围，
   编号更正与边界定义均待 Founder 确认。

   > **EP05 更正（追加，不改写原判断）**：本段原有一句，把停止码
   > `MULTIMODAL_SCOPE_CONFLICT_WITH_D10` 当成实测结论写了出来。
   > EP05 裁决第二节认定该停止码系派发件杜撰——无实现、无夹具，且码名内嵌错误编号，予以作废删除。
   > 按同节通则「无检测器的码一律不得表述为未触发」，该表述在此撤回；
   > 它原本想守的边界改由三条现场解析 PRD 正文的机器判据承接，
   > 见 `03_m2_evaluation_foundation/scoring/multimodal_attribute_benchmark.v0.1.yaml` `scope_boundary`。

2. **`D-09` 不是假锚点。** 任务 A-6 称其为「假锚点」；核对后 `D-09` 是 PRD v1.1 Delta 第二部分的真实编号
   「M2 评测治理三件套」。执行侧仍按裁决把活合同与机器引用改指 Brief 项号与三个合同 ID——
   **理由不是「它是假的」，而是那套编号属已归档文档的编号空间**。历史记录只追加更正说明，未改写。

3. **`RESUME-AUTHORIZATION-001` 命名违规是执行侧自己造成的。** 收口裁决第二节第 2 条正指此事，
   已重命名为带 `FOUNDER-` 前缀版本，正文一字未动。`FR-*` 五份为 Founder 早期签发，
   执行侧不擅自重命名，列 `OI-M2-NAMING` 待裁。

## 七、未决项全量披露（不筛选）

见本报告末尾自动生成的披露节；判据 `check_disclosure_discipline` 保证回执里每一个编号都能在此被找到。

**首要待裁**：`OI-M2-HIDDEN`（需 STORE-A 标识与访问矩阵）与 `OI-M2-CALIBRATION`（需启动两侧隔离评审）。
这两项不解，最终资产存在门 12 条里只有 1 条满足。

## 八、边界声明

- 本包**未**发生任何真实模型 API 调用、任何蒸馏调用。
- **零**隐藏内容进入主仓；一件隐藏资产未生成。
- `m2_frozen`、`knowledge_distillation_started`、`production_servable`、`m3_started`、`m4_started` 全部 `false`。
- 未合并 PR，未发起任何审查轮次。
- 全量自检绿**只是执行侧自检**，不代替 Guardian、总顾问或 Founder 的任何一方审查。


---

## 未决项全量披露（不筛选）

| 编号 | 事项 | 当前状态 |
|---|---|---|
| `OI-M2-HIDDEN` | 隐藏评测资产未生成；COND-011 三项关闭要件只齐一项 | AWAITING_FOUNDER |
| `OI-M2-CALIBRATION` | 两侧隔离评审未执行，阈值建议因此无证据来源 | AWAITING_FOUNDER |
| `OI-M2-GUARDIAN-REPORT` | 3008f56b 与 2df1101 两轮 Guardian 报告全文未落盘 | AWAITING_FOUNDER |
| `OI-M2-ANCHOR` | D-10 编号更正与多模态评测边界待 Founder 确认 | AWAITING_FOUNDER |
| `OI-M2-METRIC-GROUPING` | Brief 第 5 节「人设四项／语感六项／多模态六项」与 PRD 10.2 逐行条数不符 | REGISTERED |
| `OI-M2-NAMING` | FR-* 五份 Founder 裁决文件不带 FOUNDER- 前缀 | AWAITING_FOUNDER |
| `OI-M2-FIXTURE-DEBT` | 147 条已声明错误码尚无 expected=FAIL 夹具行使 | REGISTERED_WITH_RATCHET |
| `COND-007` | 阈值冻结 | OPEN |
| `COND-011` | 隐藏存储 provision | EVIDENCE_SUBMITTED |
| `OD-M2-01` | 真实基线锦标赛运行 | DEFERRED_BY_FOUNDER |

本节由 `ci/checkers/check_disclosure_discipline.py` 的 `OPEN_ITEM_NOT_DISCLOSED` 判据守：
回执里出现的每一个未决项编号，都必须能在本报告正文里被找到。
