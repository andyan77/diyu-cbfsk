# 笛语跨品牌服装搭配专家内核 · 文档索引

> 项目编号 DIYU-CBFSK-001｜基线日期 2026-08-12

## 当前唯一产品真源

| 文档 | 用途 | 状态 |
|---|---|---|
| `笛语跨品牌服装搭配专家内核_PRD与执行里程碑_v1.2.docx` | 产品合同、范围、里程碑与验收门 | **当前唯一产品真源，待 Founder 签署生效** |
| `笛语跨品牌服装搭配专家内核_M0执行申请_v1.2.docx` | M0下一步执行授权 | 申请ID `DIYU-CBFSK-EXEC-REQ-M0-003`，待 Founder 签署 |
| `PRD_v1.2_核验回执.docx` | D-17—D-26落文、一致性与可打开性核验 | 文档核验PASS；不代替Founder签署 |
| `PRD_v1.2_change_map.yaml` | 机器可读裁决—章节—里程碑—验收映射 | 当前变更映射 |

PRD v1.2是完整合并后的全文版，不需要对照v1.1或单独Delta阅读。

## 当前项目状态

```yaml
project_status: PROJECT_INITIATED
execution_status: EXECUTION_NOT_STARTED
production_servable: false
m0_authorized: false
prd_v1_2_documentation_status: READY_FOR_FOUNDER_REVIEW
prd_v1_2_effective: false
```

PRD v1.2与M0执行申请v1.2均获Founder明确签署后，才能另行开始M0。本轮没有开始M0施工、知识蒸馏、多模态识别、人设记忆生产库、Serving、真实库存接入或自动发布。

## Founder 新增裁决 D-17—D-26 摘要

1. M11仍为多品牌、多门店、多品类仿真试点，并支持双路径：
   - 路径A：Founder真实品牌注入，用于可选测试生产和Founder能力评判；
   - 路径B：Founder未提供时，使用Codex夹具合成回退。
2. 未见品牌继续使用合成封闭品牌。夹具池与隐藏池的配方、参数、随机种子、工作区和上下文物理隔离；Founder注入资料不得进入隐藏集。
3. `M12｜Commercial V1.0生产加固`名称、M0—M12顺序与工程路线不变；仿真、Founder注入与真实市场证据分层表述。
4. 搭配师人设连续性和自媒体原生语感已升级为正式一级能力、对象、组件与评测域。
5. 多模态商品图片理解进入正式范围；权威结构化事实 > 人工确认视觉属性 > 多模态视觉推断 > 一般模型推断。
6. 发布默认为`human_review`；Founder可按品牌、租户、账号、内容类型和风险等级授权自动发布，但自动发布不是Commercial V1.0必须实现。
7. `VisualMerchandisingExtensionPort`和`RealtimeSalesAssistExtensionPort`保持前后向兼容；完整VM和实时成交辅助不是当前V1.0或M12强制交付门。
8. M11仍至少选择三类；正式真实品牌导入前，五类首发品类必须全部处于可开启就绪状态，`five_category_activation_readiness=100%`。

## M0 执行边界

M0顶层交付清单仍为14项，不新增第15项，也不恢复18项版。D-17—D-26分别落入既有`capability_contract`、`input_output_boundary`、`non_goals_and_stop_conditions`、`architecture_and_integration_boundary`、`data_and_fixture_workflow`、`execution_critical_path_and_decision_gates`、M1对象模型Brief与M2评测冻结Brief。

## 归档

`归档_v1.1/`保存PRD v1.1、M0执行申请v1.1和v1.1核验回执，仅作历史证据。`归档_v1.0/`继续保存更早基线与审查记录。历史文件不再是执行依据。

## 工具

- `工具/build_prd_v1_2.py`：从v1.1样式模板可重放生成三份v1.2 DOCX。
- `工具/check_prd_v1_2.py`：检查版本、编号、对象数量、FR追溯、M0十四项、M11/M12、废弃措辞与README/归档一致性。
- `工具/audit_docx_package.py`：检查DOCX ZIP CRC、必需OOXML部件、所有XML/RELS可解析性与页眉版本。
- `工具/.tmp_render_docx.py`及现有样式/标题/分节审计脚本：用于PDF渲染与版式抽检。
