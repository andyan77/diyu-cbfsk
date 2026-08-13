# M1 对象模型 Brief

> M0 交付物 #12 · `DIYU-CBFSK-EXEC-REQ-M0-003` · 状态 `M0_CANDIDATE_PENDING_FOUNDER_M0_DECISION`
> 产品真源：PRD v1.2（签署基准 Commit `9335180f9e1fd3d480f9b39e0a23597ee52079c7`）
> PRD 锚点：13 节 M1、6.1、6.2、5.3、5.5、5.6、5.7

本 Brief 是 M1 的**开工输入**，不是 M1 的交付物本身。它只做三件事：钉住 M1 必须产出什么、钉住 M1 的通过标准、钉住 M0 已冻结而 M1 不得改动的东西。

## 1. 前置条件（DEP-01）

产品边界未冻结不得建立最终对象模型。M1 启动的硬前置＝Founder 对 M0 作出 `PASS` 或无阻塞的 `CONDITIONAL` 裁决。M0 若被判 `BLOCK`，M1 不得启动。

## 2. M1 必须交付（PRD 13 节 M1 原清单）

| # | 交付物 | 承接对象 |
|---|---|---|
| 1 | `brand_style_space.v0.1.yaml` | 连续风格坐标（PRD 5.3，≥14 维） |
| 2 | `audience_profile.schema.v0.1.json` | IN-05 |
| 3 | `human_visual_profile.schema.v0.1.json` | C-04 |
| 4 | `garment_and_inventory.schema.v0.1.json` | IN-04；**新增 `attribute_provenance`：authoritative / human_confirmed / model_inferred** |
| 5 | `styling_task_context.schema.v0.1.json` | IN-07 |
| 6 | `styling_decision_trace.schema.v0.1.json` | OUT-11 |
| 7 | `category_adapter_contracts/*.v0.1.yaml`（五类） | 女装／童装／青少年／亲子／运动 |
| 8 | semantic coverage checker / report | 覆盖率机器验证 |
| 9 | `brand_truth_pack.schema.v0.1.json` | IN-03 |
| 10 | `individual_profile.schema.v0.1.json` | IN-06，**含双模式标记位与授权状态字段** |
| 11 | 6.2 的 15 个输出与内部审计对象逐个 Schema，**或**一个明确包含全部对象的 `StylingResultBundle.schema.v0.1.json` 整包（二选一） | OUT-01—OUT-15 |
| 12 | 输入对象覆盖映射表 | 12 个输入对象 ↔ Schema/合同文件一一对应 |
| 13 | `stylist_persona_profile.schema.v0.1.json` | IN-09 / D-20 |
| 14 | `persona_memory_snapshot.schema.v0.1.json` | IN-10 / D-20 |
| 15 | `published_viewpoint_ledger.schema.v0.1.json` | D-20 |
| 16 | `series_continuity_state.schema.v0.1.json` | D-20 |
| 17 | `platform_voice_profile.schema.v0.1.json` | D-21 |
| 18 | `product_image_asset_bundle.schema.v0.1.json` | IN-08 / D-23 |
| 19 | `visual_attribute_extraction_result.schema.v0.1.json` | OUT-12 / D-23 |
| 20 | `publication_policy.schema.v0.1.json` | IN-12 / D-25 |
| 21 | `extension_port_contracts`（VM ／实时成交辅助／结果 Bundle 兼容） | D-22 / D-24 / FR-27 |

**映射表的一条特例**：`UniversalExpertKernel` 与 `CategoryAdapter` 是合同文件而非数据 Schema，在映射表中注明即可，不必也不应为其造 JSON Schema。

**D-20 五对象**必须齐全：`StylistPersonaProfile`、`PersonaMemorySnapshot`、`PublishedViewpointLedger`、`SeriesContinuityState`、`PersonaConflictRecord`。前四项在上表第 13—16 行；`PersonaConflictRecord` 随人设快照或独立 Schema 落地，M1 收口时须逐一可寻址。

## 3. M1 通过标准（PRD 13 节 M1 原文）

不存在未定义对象、品牌与品类混用、运行时事实混入长期真源，或女装规则默认覆盖其他品类；6.2 的 15 个输出与内部审计对象在 Schema 层**全部可寻址，无一遗漏**。

对应四条机器可验证判据：

| 判据 | 失败状态 |
|---|---|
| 12 输入 + 15 输出对象在映射表中一一有落点 | `OBJECT_NOT_ADDRESSABLE` |
| 品牌事实与品类规则不得互相混写 | `BRAND_CATEGORY_MIXUP` |
| 运行时事实不得写入长期真源 | `RUNTIME_FACT_IN_LONG_TERM_TRUTH` |
| 女装规则不得默认覆盖其他四类 | `WOMENSWEAR_RULE_OVERREACH` |

## 4. M0 已冻结、M1 不得改动

- 12 项输入与 15 项输出对象的**数量与命名**（M1 只做 Schema 化，不增删对象）
- 七级事实优先级（`input_output_boundary.v1.0.yaml`）
- 五类首发品类与各自硬约束家族
- 15 项能力、14 条设计原则、22 条强制停止条件
- 125—185 人月 / 15—24 个月基线，以及 M0 十四项清单本身

M1 若发现上述任一项需要改动，属产品裁决变更 → **停下报 Founder**，不得自行调整。

## 5. 与 M2 的并行边界

M1 对象模型与 M2 评测设计可并行，但 **M2 最终冻结必须引用稳定对象**。M1 未稳定的对象不得被 M2 冻结进评分卡。

## 6. M1 阶段仍然禁止

- 生成任何夹具品牌资产（须待 M1 Schema 冻结**之后**）
- 生成隐藏品牌或隐藏题
- 接收、处理、保存或测试 Founder 真实品牌资料
- 运行多模态商品识别并产生正式 `VisualAttributeExtractionResult`
- 建立搭配师人设记忆**生产库**（M1 只交付 Schema）
- 启用自动发布（`publication_mode` 保持 `human_review`）
- 把任何知识单元标记为 `founder_accepted` 或 `production_servable`

## 7. 执行粒度

自 M1 起适用 `DIYU-CBFSK-FR-GRANULARITY-005`：1 份 Milestone Plan + 2—4 个执行包（含收口包）+ 1 次统一收口；执行 Prompt 按仓库当时状态即时编译；同时执行的包不超过 2 个；Founder 触点为 Plan/Envelope 批准与收口裁决两次。**禁止先行建设执行框架本身**——模板先作文档约定，自动化按需生长。
