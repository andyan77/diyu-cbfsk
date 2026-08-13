# M1-EP02 交付报告 · 五类品类适配合同

> 包 `M1-EP02` · 任务分级 L2 · 基线 `6499431`（M1-EP01 收口后的 main HEAD）
> 封套 `MILESTONE_PLAN_M1`（`DIYU-CBFSK-FOUNDER-M0-DECISION-001` 预批准，范围未变）
> 连跑授权：Founder「M1 连跑」——EP02 自检＋CI 全绿后直接进入 EP03，不中途上报

## 1. 交付了什么

| # | 文件 | 内容 |
|---|---|---|
| 1 | `category_adapter_contracts/womenswear.adapter.v0.1.yaml` | CAT-WOMENSWEAR · 4 条硬约束 · FC-04 |
| 2 | `category_adapter_contracts/kidswear.adapter.v0.1.yaml` | CAT-KIDSWEAR · 5 条（全 safety_critical）· FC-05 / SC-06 |
| 3 | `category_adapter_contracts/teen_trend.adapter.v0.1.yaml` | CAT-TEEN-TREND · 6 条 · FC-05 / SC-06 |
| 4 | `category_adapter_contracts/family_trend.adapter.v0.1.yaml` | CAT-FAMILY-TREND · 4 条 · FC-05 / SC-06 · 与童装/青少年/女装 `stricter_of` 组合 |
| 5 | `category_adapter_contracts/sport_trend.adapter.v0.1.yaml` | CAT-SPORT-TREND · 6 条 · FC-06 / SC-06 · 三类承诺全禁 |
| 6 | `category_adapter_contracts/cross_category_conflict_priority.v0.1.yaml` | 跨品类冲突优先级：6 条有序规则 + 5 条组合规则 + 不可解冲突处置 |
| 7 | `ci/checkers/check_m1_category_adapters.py` | 第 21 个 checker · 15 条判据 |
| 8 | `ci/fixtures/{positive,negative}/…` | P22 + N76（迁入）+ N89—N102，共 16 份 |

## 2. 适配器不是新裁决，是冻结裁决的落地

五份适配器的 `category_id`、`hard_constraint_family`、`core_audience`、
`unique_professional_contract`、`forbidden`、`founder_full_review_required`
全部逐字段取自 `category_scope_contract.v1.0.yaml`（`M0_FROZEN`），并由
`HARD_CONSTRAINT_FAMILY_DRIFT` 逐字段比对——**适配器改写品类定义会当场判失败**。
硬约束条目本身是把已冻结的禁止事项（PRD 9.4 / 6.4 / 16.2）编号化，不新增产品裁决。

冲突优先级同理：6 条规则各自标注派生自哪一句冻结原文，改顺序属产品裁决变更，须停下报 Founder。

## 3. 修掉一个 EP01 的假绿

EP01 把 M1 通过标准第四条「女装规则不得默认覆盖其他品类」写成了
`check_m1_object_coverage` 的 `WOMENSWEAR_RULE_OVERREACH`，读
`object_coverage_map.category_defaults.womenswear_rules_apply_to_other_categories_by_default`。

**这个键全仓不存在。** 读出来恒为 `None` → `False`，判据在真实仓库上永远不会响。
N76 能触发它，只是因为 fixture 手写了 `true`——判据有检出力，`collect()` 却喂它一个恒假值。

这比 NB-M0-05 深一层：NB-M0-05 守的是「payload 空了不许显绿」，这个是「payload 非空，
但关键那一位恒假」。同一类病——**判据看起来在守，实际什么都没守**。

修法按「协议缺陷改工具」：判据迁到 `check_m1_category_adapters`（品类规则的真源是五份适配器合同），
`collect()` 读真实声明；`check_m1_object_coverage` 里那条与那个死键一并删除（EQ-1 只留一份实现、EQ-4 无死数据）。
N76 随判据迁到新 checker，不留指向已删判据的空壳；另 12 份 fixture 里的死键一并清除。

## 4. 十五条判据与各自的反向 fixture

| 判据 | 反向 fixture | 守什么 |
|---|---|---|
| `CATEGORY_ADAPTER_COVERAGE_BELOW_FLOOR` | N89 | 冻结源读不到五类＝根本没扫到，不许显绿 |
| `CATEGORY_ADAPTER_MISSING` | N90 | 冻结品类缺适配器 |
| `CATEGORY_ID_DRIFT` | N91 | 冒出 V1.0 之外的品类（男装等 `NOT_IN_V1_0`）|
| `CATEGORY_ADAPTER_DUPLICATE` | N92 | 同一品类两套实现（EQ-1）|
| `HARD_CONSTRAINT_FAMILY_DRIFT` | N93 | 适配器改写 M0 冻结的品类定义 |
| `WOMENSWEAR_RULE_OVERREACH` | N76 | 女装被声明为其他品类默认 |
| `CATEGORY_RULE_OVERREACH` | N94 | 非女装品类的同类越界 |
| `CATEGORY_SAFETY_RULE_MISSING` | N95 | 高风险品类没有 safety_critical 硬约束 |
| `FAIL_CLOSED_BINDING_MISSING` | N96 | 童装/青少年缺 FC-05、运动缺 FC-06 |
| `STOP_CONDITION_BINDING_MISSING` | N97 | 三类高风险品类缺 SC-06 |
| `CONFLICT_PRIORITY_TABLE_NOT_UNIQUE` | N98 | 冲突优先级出现第二份实现（全仓扫 `contract_id`）|
| `CONFLICT_PRIORITY_NOT_REFERENCED` | N99 | 适配器指向自己的本地优先级表 |
| `MIXED_AGE_RESOLUTION_NOT_STRICTER` | N100 | 混龄组合被解析为折中而非取更严 |
| `SPORT_PERFORMANCE_CLAIM_ALLOWED` | N101 | 运动三类承诺有遗漏 |
| `FOUNDER_REVIEW_COVERAGE_DRIFT` | N102 | 高风险知识允许抽样审查 |

**每份反向 fixture 只触发自己那一条判据**，由提交断言逐份核对（`errors` 的判据码集合必须恰好等于
`expected_judgement`）。这是 N81 的教训：fixture 因错的理由通过，等于没测。

N91 起初改现有品类的 `category_id`，会连带触发 `CATEGORY_ADAPTER_MISSING`——两条判据混在一份
fixture 里就分不出是谁在响，改成「五类齐全之外多出一份男装适配器」后只行使 `CATEGORY_ID_DRIFT`。

## 5. 三个建模判断

**① 亲子的「取更严」不只是搭配规则，也是审查强度。** 冻结合同点名的高风险知识是童装安全、
青少年身体与年龄适当性、运动功能安全三项，亲子不在其中；但亲子按 CP-02 与童装/青少年
`stricter_of` 组合，若它自己可以抽样审查，「取更严」在审查这一维上就是空话。所以
`_required_full_review()` 把要求 100% 不抽样的集合算成「三类高风险 ∪ 以 stricter_of 与其组合的品类」——
亲子的 100% 是**推导出来的**，不是手写常量（EQ-4）。

**② 女装的「不是默认」写成显式字段而不是省略。** `is_default_for_other_categories: false`
看似废话，但省略它，判据就只能靠「没声明＝没越界」，而那正是 EP01 那条假绿的形状。
显式禁位让违规可被判定。

**③ 冲突优先级表全仓唯一靠扫描，不靠自觉。** `collect()` 遍历全仓 YAML 找
`contract_id: cross_category_conflict_priority.v0.1`，出现第二份即失败——而不是靠
「我只写了一份」这种自我保证。

## 6. 红线自查

- 未生成任何品类知识内容、语料、夹具品牌资产、隐藏品牌或隐藏题：**未触碰**
- 未接收/处理/保存/测试 Founder 真实品牌资料：**未触碰**
- 未运行多模态识别、未建人设记忆生产库、未启用自动发布：**未触碰**
- 未把任何知识单元标记为 `founder_accepted` / `production_servable`：**未触碰**
- 未改动 M0 冻结的十四项交付物任何一份（`check_m0_deliverable_closure` PASS 为证）
- 未改动五类品类、其硬约束家族、12/15 对象数量与命名、七级事实优先级

## 7. 核验（实测，本包提交时）

```
21 checkers PASS / 0 FAIL
124 判据 fixture 全部按声明行为
34 实例 fixture 全部按声明行为（17 VALID / 17 INVALID）
16 份品类适配 fixture 各自只触发本条判据
```

## 8. 路由到 EP03 的事项

- **EP01 遗漏项**：`m1_object_model_brief.md` 交付清单第 3 项
  `human_visual_profile.schema.v0.1.json`（C-04 人体视觉档案）EP01 未交付，也未登记在
  `not_delivered_in_ep01`。它不属 12 输入对象，因此不触发 `OBJECT_NOT_ADDRESSABLE`——
  这说明覆盖判据只盯 12+15 对象、不盯 Brief 的 21 项交付清单，属**判据覆盖面缺口**。
  EP03 补齐 Schema，并按「协议缺陷改工具」给覆盖 checker 加 Brief 交付清单判据，杜绝同类遗漏。
- 扩展端口合同（D-22 / D-24 / FR-27）：EP01 已在 Bundle 留 `backward_compatible_extension_ports` 位，EP03 落合同。
- `m2_evaluation_freeze_brief.md` 属 M0 冻结交付物；EP03 按 M1 真实产出更新它时须走
  `post_m0_authorized_modifications` 登记，不得改写 `artifact_sha256`。

---

*EP02 未踩七类硬门，未出现改变封套范围的 open_item，按连跑授权直接进入 EP03。*
