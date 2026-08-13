# M1-EP01 交付报告 · 核心语义与对象注册表

> 里程碑 M1｜执行包 `M1-EP01`｜`task_class: L2`｜基线 `8eaf5f25987d787a546096b6a60a4e6a6b5a30f4`
> 计划来源 `DIYU-CBFSK-FOUNDER-M0-DECISION-001` `m1_pre_approval`｜开工授权 `DIYU-CBFSK-FOUNDER-M1-GATE-001` 第 4 条

## 一句话

PRD v1.2 的对象世界变成了机器 schema：**12 个输入 + 15 个输出对象在 Schema 层全部可寻址**，对象数量与命名逐一对齐 M0 冻结合同，M1 只做 Schema 化、未增删任何对象。

## 交付清单

| # | 交付物 | 落点 |
|---|---|---|
| 1 | 连续风格坐标空间（14 维） | `01_contracts_and_schemas/m1_object_model/brand_style_space.v0.1.yaml` |
| 2 | 公共定义（七级事实优先级、属性来源分层、持久化类别、版本引用） | `common_defs.schema.v0.1.json` |
| 3 | 输入对象 Schema ×10（IN-03—IN-12） | 同目录 `*.schema.v0.1.json` |
| 4 | D-20 五对象 | 人设画像／记忆快照／已公开观点台账／系列连续性／**人设冲突记录（独立件）** |
| 5 | D-21 平台语感 | `platform_voice_profile.schema.v0.1.json` |
| 6 | 输出整包（OUT-01—OUT-15） | `StylingResultBundle.schema.v0.1.json` ＋ OUT-11／OUT-12 两份独立件由整包 `$ref` |
| 7 | Schema 注册表 | `schema_registry.v0.1.yaml`（派生件） |
| 8 | 输入输出覆盖映射表 | `object_coverage_map.v0.1.yaml` |
| 9 | 覆盖率 checker | `ci/checkers/check_m1_object_coverage.py`（第 20 个确定性 checker） |
| 10 | 结构层 fixture runner | `ci/run_schema_fixtures.py` |

## 验收判据逐条对照

| 验收要求 | 实测 |
|---|---|
| 不存在未定义对象；12 输入 + 15 输出全部可寻址 | 27 个对象逐一有落点，落点全部可解析（含 JSON Pointer 解引用）；`check_m1_object_coverage` PASS |
| 六层（合同为**七级**）事实优先级可表达 | `factProvenance` 的 `level` 与 `rank` 一一绑定；第 5、7 级强制 `is_model_inference` 与显式标记 |
| 运行时事实与长期真源分离 | 每份 Schema 声明 `persistence_class`；注册表与 Schema 交叉核对，不一致判 `RUNTIME_FACT_IN_LONG_TERM_TRUTH` |
| 可版本化 | `objectVersion` 公共定义 + 每份 Schema 的 `schema_version`；缺失判 `SCHEMA_NOT_VERSIONABLE` |
| 每个 schema 有正负 fixture | 17 份 instance-bearing Schema × 正负各一 = **34 份实例 fixture**，全部按声明行为；缺任一判 `SCHEMA_WITHOUT_FIXTURE` |
| coverage checker 通过 | 12 条判据各配 negative fixture，全部按声明行为 |

`common_defs` 是唯一豁免实例 fixture 的 Schema：它只提供 `$defs`、本身没有实例，判据由引用它的 Schema 的 fixture 间接行使。豁免理由写在注册表里，不是默默跳过。

## 两处口径不一致（按更严的冻结真源执行）

| 处 | 裁决措辞 | M0 冻结真源 | 本包取值 |
|---|---|---|---|
| 输出对象数 | `M0-DECISION-001` 验收门写「11 个输出对象」 | 冻结合同与 M1 Brief 均为 **15**（`count_is_frozen: true`） | **15** |
| 事实优先级层数 | EP01 Prompt 写「六层」 | 合同 `ordered_levels` 为 **7** 级 | **七级** |

15 ⊃ 11、七级 ⊃ 六层，满足更严口径即同时满足两种读法，因此未停工上报。若 Founder 认为裁决措辞才是准，须走产品裁决变更——对象数量与命名属 M0 冻结项，执行侧不得自行调整。

## 设计上的三个取舍

1. **风格空间只落 PRD 点名的 14 维，不自行增补。** PRD 5.3 原文点名了 14 个维度且写「至少覆盖」。凭空加轴无法从真源核验，属发明产品事实；扩轴走 `dimension_extension_rule`，须给 PRD 锚点或裁决编号并升版本。
2. **输出走「整包」而非 15 份独立文件，但 OUT-11／OUT-12 例外。** M1 Brief 第 11 项允许二选一。整包内 13 个 `$defs` + 两份独立件由整包 `$ref` 引用——两份独立件是 Brief 第 6、19 项单独点名的交付物，若在整包内再写一遍就是两套定义（EQ-1）。
3. **Schema 采用 draft-07 而非 2020-12。** 本机 `jsonschema` 为 3.2.0，只实现到 draft-07。写成 2020-12 会得到一份**无法被实测行使**的 Schema——看起来更新，实际上 34 份 fixture 一份也验不了，属 EQ-3 意义上的假绿。理由记入注册表 `json_schema_draft_reason`。

## M1 红线焊进结构

五处 M1 期禁止项在 Schema 里写成 `const false`，写 `true` 即结构性非法、被 fixture 当场行使：

| 红线 | 落点 |
|---|---|
| 不得运行多模态商品识别 | `product_image_asset_bundle.multimodal_recognition_executed` |
| 不得接入真实库存 | `garment_and_inventory.is_real_inventory_connection` |
| 不得接入真实顾客 | `individual_profile.is_real_customer_connection` |
| 不得建人设记忆生产库 | `stylist_persona_profile.is_production_memory_store` |
| 不得接收 Founder 真实品牌资料 | `founder_provided_real_brand_package.received_by_execution_side` |

本包另未生成任何夹具品牌资产、隐藏品牌或隐藏题，未启用自动发布（`publication_mode` 默认 `human_review`），未把任何知识单元标记为 `founder_accepted` 或 `production_servable`。

## 顺手项：Guardian 四项非阻塞发现全部关闭

| # | 发现 | 处置 |
|---|---|---|
| **NB-M0-01** | 零接触扫描无覆盖面断言 | `check_m0_zero_contact` 新增 `scanned_file_count` 与下限 80（当前实测 239）；扫 0 份判 `SCAN_COVERAGE_BELOW_FLOOR` |
| **NB-M0-02** | `PREMATURE` 判据应改白名单 | `PREMATURE_EXTERNAL_CONNECTION` 改为授权白名单：任何连接须在签署回执有绑定完整 Commit 哈希的 Founder 授权，否则判 `UNAUTHORIZED_EXTERNAL_CONNECTION` / `UNBOUND_INTEGRATION_AUTHORIZATION`。守的是**授权缺失**而不是硬编的里程碑名——M0 已 PASS，硬编里程碑会随时间失真 |
| **NB-M0-04** | 20 条散文红线清单无漂移守卫 | 签署回执新增 `red_line_manifest`（条数＋全文 sha256＋具名裁决＋绑定 Commit）；`check_role_operating_model` 重算比对，判 `RED_LINE_COUNT_DRIFT` / `RED_LINE_TEXT_DRIFT` / `RED_LINE_CHANGE_WITHOUT_RULING` / `RED_LINE_MANIFEST_MISSING`。指纹放在 Founder 可见的回执里，不藏在代码常量中 |
| **NB-M0-05** | 多个 checker 空 payload 仍判绿 | `check_execution_uuid` 与 `check_m0_zero_contact` 各加覆盖面下限断言 |
| 附带 | M0 交付物交付后被改动无守卫 | `check_m0_deliverable_closure` 新增字节完整性三判据 + 回执 `post_m0_authorized_modifications` 登记块（详见下节） |
| 附带 | `ec8d723a` 未纳入 `check_execution_uuid` 守卫 | 该 checker 重构为**多批次**结构（治理任务批次 + M0 里程碑批次），新增批次只需加一条，不再写第二个 checker（EQ-1）；下限 2 个批次，另加跨批次标识复用判据 |

### 顺手修过程中暴露并补上的一处结构缺口

改 `check_m0_zero_contact.py` 时撞上一件事：它本身是 M0 交付物，字节被 `m0_delivery_receipt.artifact_sha256` 钉死。Founder 已把 NB-M0-01/02 路由到 M1 顺手修，所以**改是被授权的**——但直接重写那份哈希等于抹掉「M0 交付的到底是哪一版」这个记录。

处置：`artifact_sha256` 保持 M0 交付当时的字节状态不动，新增 `post_m0_authorized_modifications` 逐条登记交付后的授权改动（谁授权、改了什么、新哈希）；`check_m0_deliverable_closure` 新增三条判据（`M0_ARTIFACT_MODIFIED_WITHOUT_RECORD` / `M0_MODIFICATION_RECORD_STALE` / `M0_MODIFICATION_WITHOUT_RULING`），按「要么与交付哈希一致，要么已登记且对得上」判定。**改动不是禁止的，不留痕才是。**

这条判据落地后**第一个抓到的就是引入它的那次改动**——`check_m0_deliverable_closure.py` 自己也在十四项清单里。这不是巧合：交付物清单包含 checker 自身，它就必须能查自己。

五项 checker 增强共补 **12 份 negative fixture + 1 份 positive**（N77—N88、P21）。既有受影响 fixture 同步补齐新字段，使它们仍**只因各自那条判据失败**——其中 N81 初版因「父子标识相同」而非「跨批次复用」判失败，已修正；fixture 因错的理由通过等于没测。

## 不在本包（按计划路由）

| 项 | 去向 |
|---|---|
| 五类品类适配合同 | M1-EP02 |
| 扩展端口合同（VM／实时成交辅助／Bundle 兼容） | M1-EP03；整包已留 `backward_compatible_extension_ports` 位 |
| 知识内容语料夹具、隐藏评测 | 非 M1 目标 |

## 核验

```
20 checker PASS / 0 FAIL
109 判据 fixture 按声明行为
34 实例 fixture 按声明行为（17 正 / 17 反）
check_prd_v1_2.py --require-archive: 62 PASS
投影 drift = 0
零接触扫描 239 份文本文件，遗留资产命中 0
M0 十一份合同与章程零改动；M0 回执 18 份哈希中 2 份因授权顺手修而变化，已逐条登记
```

按 `M0-DECISION-001` `package_level_guardian: false`：本包自检 + CI 绿即提交推进，不做包级 Guardian，里程碑收口统一审。本包未踩七类硬门，无中断上报事项。
