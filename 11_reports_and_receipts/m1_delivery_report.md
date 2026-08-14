# M1 交付报告 · 语义骨架与品类适配合同

> 里程碑 `M1` · 封套 `MILESTONE_PLAN_M1`（`DIYU-CBFSK-FOUNDER-M0-DECISION-001` 预批准）
> 连跑授权 `DIYU-CBFSK-FOUNDER-M1-RUNTHROUGH-001` · 三包串行 EP01 → EP02 → EP03
> **本报告是执行侧结论，不是 Founder 批准，也不是外部独立审查。** M1 是否通过由 Founder 裁决。

## 1. 包完成矩阵

| 包 | 名称 | Commit | 交付物 | 自检 |
|---|---|---|---|---|
| M1-EP01 | 核心语义与对象注册表 | `38d13b7dc451ee2372aee8ca3ca2d49c23866c33` 开工 / `c714732ff9a303719dde7a5a70bfa9c2fc36d042` 对象模型 / `6499431c66f7bf4a234bd830ee4c810e1ac78694` 收口 | 18 Schema + 风格空间 + 注册表 + 覆盖映射表 + 第 20 个 checker | 20 checker / 109 判据 fixture / 34 实例 fixture |
| M1-EP02 | 五类品类适配合同 | `8ce837a4569565299be3f8dacf65121bb0908a44` | 5 适配器 + 冲突优先级表 + 第 21 个 checker（15 判据） | 21 checker / 124 判据 fixture / 34 实例 fixture |
| M1-EP03 | 集成与收口 | 本包 | C-04 Schema + 端口合同 + 接口交接面 + 覆盖 checker 全量扩展（7 判据）+ 报告与 Receipt | 21 checker / 131 判据 fixture / 36 实例 fixture |

三包串行，`max_concurrent_packages: 2` 未用满（实际并发 1），与 `MILESTONE_PLAN_M1` 声明一致。

## 2. M1 通过标准逐条对照（PRD 13 节原文）

| 通过标准 | 机器判据 | 实现在 | 反向 fixture | 实测 |
|---|---|---|---|---|
| 不存在未定义对象 | `OBJECT_NOT_ADDRESSABLE` | `check_m1_object_coverage` | N66 | PASS |
| 品牌与品类不混用 | `BRAND_CATEGORY_MIXUP` | `check_m1_object_coverage` | N70 | PASS |
| 运行时事实不混入长期真源 | `RUNTIME_FACT_IN_LONG_TERM_TRUTH` | `check_m1_object_coverage` | N69 | PASS |
| 女装规则不得默认覆盖其他品类 | `WOMENSWEAR_RULE_OVERREACH` | `check_m1_category_adapters` | N76 | PASS |
| 15 输出对象 Schema 层全部可寻址 | `OBJECT_COUNT_DRIFT` + `LANDING_FILE_MISSING` | `check_m1_object_coverage` | N65 / N67 | PASS |

四条通过标准判据另有一层元判据 `M1_ACCEPTANCE_JUDGEMENT_NOT_WIRED`（反向 fixture N108）：
每条都必须在已注册 checker 里有实现、且真的被某份 `expected=FAIL` 的 fixture 触发。
「被行使」的判定不是看文件名或声明字段，而是**真的把 fixture 喂进 validate() 看这条码有没有出现**。

**这条元判据守不住什么，得说清楚**：它守「判据被删掉或从没人跑过」，**守不住**「判据还在、
fixture 也在，但 `collect()` 喂给它的值恒假」。EP01 的女装判据正是后者（见 §4）。那一类只能靠
让 `collect()` 读真源来防，没有通用元判据能替代。

## 3. 交付物清单对照（M1 对象模型 Brief 21 项）

21 项全部有落点，由 `BRIEF_DELIVERABLE_COUNT_DRIFT` / `BRIEF_DELIVERABLE_NOT_LANDED` 逐项判定
（条数与名称的真源是 Brief 编号表本身，M0 冻结，未改写）。

- EP01 交付 17 项 · EP02 交付 1 项（第 7 项五类适配器）· EP03 交付 3 项（第 3、21 项 + 第 8 项扩展）
- 第 11 项按「整包」选项交付（`StylingResultBundle`），`DecisionTrace` / `VisualAttributeExtractionResult`
  另出独立 Schema——两者是 Brief 单独点名的交付物，写进整包再写一遍就是两套定义（EQ-1）。

## 4. M1 期间发现并修复的两处自身缺陷

**① EP01 的女装判据是假绿（EP02 修）。** `WOMENSWEAR_RULE_OVERREACH` 读
`object_coverage_map.category_defaults.womenswear_rules_apply_to_other_categories_by_default`——
**这个键全仓不存在**，恒为 `None` → `False`。判据有检出力（N76 能触发），但 `collect()` 喂它恒假值，
在真实仓库上永不触发。修法按「协议缺陷改工具」：判据迁到 `check_m1_category_adapters`，
改读五份适配器的真实声明；死键与旧实现一并删除。

**② EP01 漏交 Brief 第 3 项（EP03 补）。** `human_visual_profile.schema.v0.1.json`（C-04 人体视觉档案）
未交付，也未登记在 `not_delivered_in_ep01`。没被抓到的原因是覆盖判据只盯 12 输入 + 15 输出，
而 C-04 不在这 27 个之内。EP03 补齐 Schema，并给覆盖 checker 加 Brief 21 项交付清单判据——
补数据的同时补判据，杜绝同类复发。

两处都不是「跑一遍发现的」，而是读代码时发现判据读的键在仓里不存在、以及逐项核对 Brief 清单时发现缺项。
**CI 全绿不等于判据在守东西**——这是 M1 最值得记下的一条。

## 5. 红线自查（M1 全程）

| 红线 | 状态 | 证据 |
|---|---|---|
| M1 五条禁止焊成 `const false` | 已焊 | 多模态正式结果 / 真实库存 / 真实顾客 / 人设记忆生产库 / Founder 真实品牌接收，写 `true` 即 Schema 非法，反向 fixture 当场行使 |
| 不生成知识内容、语料、夹具品牌资产 | 未触碰 | 全部交付物为 Schema 与合同，无任何品类知识内容 |
| 不生成隐藏品牌 / 隐藏题、不碰隐藏评测 | 未触碰 | `check_hidden_benchmark_boundary` PASS |
| 不接收/处理/保存/测试 Founder 真实品牌资料 | 未触碰 | IN-11 只有 Schema 与隔离合同 |
| 不启用自动发布 | 未触碰 | `publication_mode` 默认 `human_review`，`auto_publish` 须 Founder 授权条件 |
| 不标记 `founder_accepted` / `production_servable` | 未触碰 | `check_project_state` PASS |
| 不改 M0 冻结的对象数量、品类、事实优先级、十四项清单 | 未改 | `check_m0_deliverable_closure` / `check_m0_fourteen_items` PASS |
| 引用 Commit 写完整哈希 | 遵守 | 本报告与裁决归档中的 Commit 均为 40 位完整哈希 |

**M0 冻结交付物只动了一份**：`m2_evaluation_freeze_brief.md` 追加第 10 节 M1 接口交接，
按 `DIYU-CBFSK-FOUNDER-M1-RUNTHROUGH-001` 授权，已在回执 `post_m0_authorized_modifications` 登记
（`artifact_sha256` 保持 M0 交付当时的值不动）。其余 17 份字节未变。

## 6. 核验（实测）

```
21 个确定性 checker            PASS / 0 FAIL
131 份判据层 fixture           全部按声明行为（22 正 / 109 反）
36 份结构层实例 fixture        全部按声明行为（18 VALID / 18 INVALID）
check_prd_v1_2 --require-archive   62 PASS
compile_role_instructions --check  12 files, drift=0
```

每条新增判据都有一份反向 fixture，且**每份反向 fixture 只触发它自己那一条判据**——
由提交门控逐份核对。N81 的教训：fixture 因错的理由通过，等于没测。

## 7. Open Items（只登记，不自行裁决）

| ID | 事项 | 执行侧处理 | 建议路由 |
|---|---|---|---|
| OI-M1-01 | `DIYU-CBFSK-FOUNDER-M0-DECISION-001` 的 `acceptance_gate` 写「11 个输出对象」，冻结合同 `input_output_boundary.v1.0` 写 15（`count_is_frozen: true`） | 按 15 执行（15 ⊃ 11，满足更严即同时满足两种读法） | 若以裁决措辞为准，属产品裁决变更，须 Founder 裁决 |
| OI-M1-02 | M1-EP01 Prompt 写「六层事实优先级」，冻结合同为七级 | 按七级执行 | 同上，建议以冻结合同为准并更正 Prompt 模板 |
| OI-M1-03 | 仓内不存在 M3 问题系统 Brief，EP03 Prompt 要求「更新」无对象 | 未新建 M3 Brief（新建＝在未授权下先行规划 M3）；改为把 M1→M3 接口面落在 `m1_interface_handoff.v0.1.yaml`，标 `INTERFACE_ONLY` | Founder 决定 M3 Brief 何时立、由谁立 |
| OI-M1-04 | 两个扩展端口的 8 个预留对象未建 Schema | 只登记名称与归属端口，不建 Schema（未立 Brief 前建 Schema 等于先定型扩展数据结构） | 按 D-22 / D-24，Founder 另立 Brief 时决定 |
| OI-M1-05 | 「运行时事实与长期真源分离」目前判定的是注册表与 Schema 的 `persistence_class` 一致性 | M1 无持久化实现，行为层不可测 | M6/M8 有实现后补行为层判据 |
| OI-M1-06 | 女装适配器 4 条硬约束均未标 `safety_critical` | 冻结合同的高风险清单只含童装安全、青少年身体与年龄适当性、运动功能安全，女装不在其中 | 如需提升女装约束等级，属产品裁决变更 |

已闭合项（记录在案，不再路由）：EP01 女装判据假绿（EP02 修）、EP01 漏交 Brief 第 3 项（EP03 补）、
Guardian `NB-M0-01/02/04/05`（EP01 全关）。

## 8. 下一步

M1 候选冻结 → Guardian 里程碑收口审查 →（总顾问，可豁免）→ Founder 收口裁决。
**M2 未开工**：`m2_started` 无授权条目，置 `true` 即判 `UNAUTHORIZED_TRUE_FLAG`。
知识蒸馏、夹具或隐藏品牌生成、多模态识别、人设记忆生产库、Serving、真实库存接入与自动发布均未开始。


---

## 未决项全量披露（M2-EP04 追加，NB-M2-06）

Guardian 非阻塞发现 NB-M2-06：本报告此前只提了回执里的部分未决项。
**回执里有、报告里没有** 的条目，读者无从知道它存在——而读报告的人正是决定要不要往下走的人。
现按披露纪律补齐**全部**条目，不筛选：

| 编号 | 事项 | 当前状态 |
|---|---|---|
| `OI-M1-01` | 裁决 acceptance_gate 写 11 输出对象 vs 冻结合同 15 | CLOSED_BY_HIGHER_AUTHORITY |
| `OI-M1-02` | EP01 Prompt 写六层事实优先级 vs 合同七级 | CLOSED_BY_HIGHER_AUTHORITY |
| `OI-M1-03` | M3 问题系统 Brief 不存在，未新建，接口面标 INTERFACE_ONLY | ROUTED_TO_M3 |
| `OI-M1-04` | 两个扩展端口的 8 个预留对象未建 Schema | ACCEPTED_AS_IS |
| `OI-M1-05` | 运行时事实分离目前只判 persistence_class 一致性，行为层不可测 | ROUTED_TO_M6_M8_M9 |
| `OI-M1-06` | 女装 4 条硬约束均未标 safety_critical | ACCEPTED_AS_IS |

本节由 `ci/checkers/check_disclosure_discipline.py` 的 `OPEN_ITEM_NOT_DISCLOSED` 判据守：
回执里出现的每一个未决项编号，都必须能在对应报告正文里被找到。
