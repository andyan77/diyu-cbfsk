# M2 评测冻结 Brief

> M0 交付物 #13 · `DIYU-CBFSK-EXEC-REQ-M0-003` · 状态 `M0_FROZEN`（Founder M0 裁决 CONDITIONAL → Guardian delta 复核 APPROVE 后升 PASS，冻结时点即此裁决）
> 产品真源：PRD v1.2（签署基准 Commit `9335180f9e1fd3d480f9b39e0a23597ee52079c7`）
> PRD 锚点：13 节 M2、10.1、10.2、10.3、10.4、8.7、D-28

M2 的目标一句话：**在大规模知识生成前把考试冻结，阻止模型用自己生成的答案证明自己。**

## 1. 前置与阻断

- 前置（DEP-02）：M1 对象稳定后才可冻结引用它们的评分卡。
- 阻断（SC-01）：M2 隐藏评测未冻结 → **停止大规模知识蒸馏**。M4 不得在 M2 冻结前启动正式批次。

## 2. M2 必须交付（PRD 13 节 M2 原清单，18 项）

| # | 交付物 | 要点 |
|---|---|---|
| 1 | `benchmark_capability_matrix.v0.1.yaml` | **每条能力项须标注 `evaluation_task_class`** |
| 2 | `unseen_brand_split.v0.1.yaml` | 未见品牌切分 |
| 3 | `unseen_category_edge_cases.v0.1.yaml` | 品类边缘任务 |
| 4 | `expert_scoring_rubric.v0.1.yaml` | 专业解释评分卡 |
| 5 | `narrative_scoring_rubric.v0.1.yaml` | 叙事质量评分卡 |
| 6 | `hard_gate_definitions.v0.1.yaml` | **须扩展为「硬门 → 八道门」显式映射表** |
| 7 | benchmark leakage checker / frozen manifest / receipt | 泄漏检查与冻结清单 |
| 8 | `reviewer_calibration_contract.v0.1.yaml` | 兼容旧名 `rater_calibration_contract`；**内部一致性不得表述为外部专家共识** |
| 9 | `evaluation_sampling_design.v0.1.yaml` | 分层维度＝品类 × 任务类型 × 风险等级 |
| 10 | `benchmark_revision_protocol.v0.1.yaml` | 冻结后唯一合法修订通道；**因失败而降标永久禁止** |
| 11 | 泄漏 ＋ 同质性双检查报告 | 夹具池与隐藏池配方分离核验（8.7） |
| 12 | `persona_continuity_scoring_rubric.v0.1.yaml` | D-20 |
| 13 | `social_media_native_voice_scoring_rubric.v0.1.yaml` | D-21 |
| 14 | `multimodal_attribute_benchmark.v0.1.yaml` | D-23 |
| 15 | `multimodal_confidence_calibration_contract.v0.1.yaml` | D-23 |
| 16 | `five_category_readiness_definition.v0.1.yaml` | 阈值 `M2_FREEZE_REQUIRED` |
| 17 | `evaluation_task_class_contract.v0.1.yaml` | **D-28 强制三分类** |
| 18 | `acceptable_decision_boundary_registry.v0.1.yaml` | **②③类冻结对象＝可接受决策边界** |

## 3. D-28 合理多解原则：M2 的核心口径

强制三分类，**每一道题必须归入且只归入一类**：

| 类 | `evaluation_task_class` | 评什么 | Gold Answer |
|---|---|---|---|
| ① | `constraint_correctness` | 硬约束题 | 唯一 0/1，**允许** |
| ② | `mechanism_correctness` | 可接受推理区间 | **禁止唯一 Gold Answer** |
| ③ | `open_decision` | 可接受解空间与多解族质量 | **禁止唯一 Gold Answer** |

②③类的**冻结对象是 Acceptable Decision Boundary（可接受决策边界），不是参考答案**。

停止条件 SC-20：`mechanism_correctness` 或 `open_decision` 类任务被设置唯一 Gold Answer → **停止 M2 冻结**，改回可接受决策边界后重跑。风险 R-22（唯一答案偏误）严重度对标 R-09（评测泄漏）。

配套口径：`核心判断重复一致率` 已更名 `核心决策逻辑稳定率`（阈值 ≥85% 不变）。反例＝同条件下先「弱化肩部」后「强化肩部」；**非**反例＝同条件下一次裤装方案、一次裙装方案且均成立。

## 4. 11 条硬门必须逐条映射到八道发布门

`hard_gate_definitions.v0.1.yaml` 的强制结构要求：10.1 的每一条硬门都能追溯到承接它的发布门，不得有硬门无承接（`HARD_GATE_WITHOUT_RELEASE_GATE`）。硬门与发布门清单见 `execution_critical_path_and_decision_gates.v1.0.yaml`。

## 5. 阈值冻结范围

M0 **不得代为冻结任何阈值**。以下指标在 PRD 10.2 中标记为 `M2_FREEZE_REQUIRED`，由 Founder 在 M2 冻结时裁决（`COND-007` 跟踪）：人设四项、语感六项、多模态六项、五类就绪度、发布授权率、AI 评审分歧率、Founder 推翻率与抽检率。

已在 PRD 中给出建议阈值、M2 冻结前可调整、**冻结后不得因失败降标**的：内部评审面板通过率（未见品牌 ≥80%、未见品类 ≥75%）、严重风格错位率 <5%、核心决策逻辑稳定率 ≥85%、专业解释平均分 ≥4.0/5、叙事质量平均分 ≥4.0/5、账号差异化通过率 ≥85%、人工可发布率 ≥75%。

**高风险 Founder 全审覆盖率＝100%，不可抽样，不是可调阈值。**

## 6. 隐藏集与同质性

- 30—50 个合成封闭未见品牌须在 **M2 冻结前**建成。
- 夹具池与隐藏池必须**不同配方、不同参数空间、不同随机种子、不同工作区**，隐藏池另有专属风格坐标覆盖。
- Guardian 出同质性报告；M2 执行**泄漏 ＋ 同质性双检查**。
- 隐藏内容物理隔离于主仓，存 STORE-A（独立私有仓库，受限访问），M2 前 provision（`COND-011`）。主仓 `02_benchmark_manifests/` 只放 schema、frozen manifest、hashes、runner 接口与结果摘要。
- 13 条必设隐藏测试的设计要求见 `data_and_fixture_workflow.v1.0.yaml`。

## 7. M2 通过标准（PRD 原文）

隐藏集、评分卡、硬门和阈值冻结；后续失败不得降标；泄漏与同质性双检查通过；`EvaluationCard` 与 `benchmark_capability_matrix` 三分类齐备，②③类未设置唯一 Gold Answer，冻结对象为可接受决策边界。

## 8. 评审表述纪律

内部评审面板由隔离 GPT、隔离 Claude、规则 Checker 与 Founder 组成，其结论**不是外部专家证明**，不得写成「外部专家通过率」。`external_human_review=false`、`external_legal_opinion=false` 须如实保留。

## 9. M2 是不可逆包

按 `DIYU-CBFSK-FR-GRANULARITY-005`，M2 冻结属五个需要 **Founder 精确 Prompt 批准**的不可逆包之一，且里程碑收口须走 Guardian →（总顾问，可豁免）→ Founder。
