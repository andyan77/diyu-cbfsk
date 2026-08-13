# 基线对账报告

项目：DIYU-CBFSK-001  
任务：DIYU-CBFSK-GOV-ROLE-OPERATING-MODEL-002  
执行批次：`29899f92-c965-4c33-a020-8e7f781fe82d`  
生成时间：2026-08-13T00:47:18-07:00

## 结论

Phase 0 已完成，未发现产品基线语义冲突。Founder 正本目录中的三份 v1.1 DOCX 和 `README.md` 与远程 `main` 提交 `ce13cf3d6dca3ed6ac918400c8c08c10051832bf` 在二进制层完全相同；因此规范化 XML 与语义文本也完全相同。

当前状态仍为：

```yaml
baseline_effective: false
document_editing_authorized: false
founder_confirmation: PENDING
```

本报告只完成对账，不确认基线、不修改产品文档，也不开始 M0。

## 远程与本地定位

- 远程仓库：`https://github.com/andyan77/diyu-cbfsk`
- 远程默认分支：`main`
- 远程 HEAD：`ce13cf3d6dca3ed6ac918400c8c08c10051832bf`
- Founder 正本候选目录：`D:\笛语跨品牌服装搭配专家内核`
- 临时目录：`D:\tmpcodex`
- 当前 Phase 0 分支：`codex/baseline-reconciliation-v2`，从远程 `main` 建立

## 活基线候选三层哈希

| 文件 | binary SHA-256 | canonical DOCX XML SHA-256 | semantic text SHA-256 | 结论 |
|---|---|---|---|---|
| PRD v1.1 | `1532f59eb004bf6a7e47f8429af43969905ba49a51c850b21c728a8711b78f97` | `752ebe00e09133ca4934ce0bcada01b71f666e1f8720b8f1f97a9169f32782a6` | `48b69ab1261b9dbfd6a2b167a9054a02f3a6a7bd661f31ba8409f998e221da37` | 本地＝远程 |
| M0 执行申请 v1.1 | `bc89e25b437f2cd88e55632451be40213ea6b7733ecfb19b91e5cc7e6463c997` | `6e81d91d588400f11d9c4ef851931daa6fee2928e43ece690b42da14bd020e1e` | `52426029579c4073de0aa3d6d43b2ad56369ad276728e04e4b0b94533416f32d` | 本地＝远程 |
| PRD v1.1 核验回执 | `080008393c077b2a92d5c79036cfc25f5b1c8027a5630ae42222eb926316b3c9` | `a7f8427a8898d6b58e8525bddb110d32b2c06d8645e6316d7b9d307079bb1fee` | `242762f68f9ffd6ffaf7b68a24d26e3ced782a39190623e0106b6bcc69573c31` | 本地＝远程 |
| README.md | `e5a4d75c7fd4e4e2eb9236b0cb3a7afff5d371eeb295d3ca5523a3783544007b` | 不适用 | `0a3293228d1577a6558c3fa8e648926e9ebbb37b2aa24c7ad6272e445dfb9d8a` | 本地＝远程 |

以上四个 binary 哈希均与 Founder 本轮提供值一致。`治理执行Prompt_分工审计与补强意见书.docx` 的 binary 哈希也与提供值 `ecf2fc4079fd94aab3e3e12e295d1dc1a2e8b5b6b1f25fe4a46f21c7a04cf3b7` 一致。

## 规范化规则与差异结果

- canonical DOCX XML：对按名称排序的有效 XML/RELS 部件执行 C14N 2.0；排除 Word 封装元数据和易变编辑标识。
- semantic text：读取正文、表格、页眉与页脚，做 NFKC 和空白规范化，再计算 SHA-256。
- 差异结果：三份 DOCX 在 binary、canonical 和 semantic 三层均为相等；不存在需要逐段或逐表提交 Founder 裁决的语义差异。

## 历史证据

远程 `归档_v1.0/` 中五份历史文件与 Founder 存档区对应文件逐一 binary 相同。它们只保留历史证据身份，不重新获得活真源地位。Founder 存档区另有一份 `治理执行Prompt_分工审计与补强意见书.docx`，本阶段记录为仓外历史证据，不自动导入。

## 临时目录处置建议

`D:\tmpcodex` 共有两份文件：

| 文件 | 与仓库文件的关系 | 建议处置 |
|---|---|---|
| `prd.docx` | 与归档 PRD v1.0 binary 完全相同 | `DUPLICATE_CONFIRMED` |
| `report.docx` | 与 v1.0 完整性审查报告 binary 完全相同 | `DUPLICATE_CONFIRMED` |

没有删除任何文件。仓库外文件不算正式交付物；若以后清理，仍需 Founder 明确批准。

## 既有 v1.2 候选的边界

工作区进入本任务前存在 `docs/prd-v1.2-founder-rulings` 分支，提交为 `ace63603f327d61775eff78eef2fbfa9259bb67c`。该分支只覆盖此前 D-17—D-26 候选，早于本 Prompt 的 D-27、S1—S8、角色治理和本轮三项补丁，故标记为 `STALE_DERIVED_ARTIFACT_REQUIRES_REGENERATION`。它已完整保留，未被删除或改写，也未被当作本轮基线。

## 本轮三项补丁的处理状态

三项补丁已钉入 Manifest 的 `pending_founder_patch_set`，但依附件第 4.1 与 Phase 0 门禁尚未修改 PRD：

1. D-23 对 D-12 部分改判：3.2 新非目标文案；`garment_and_inventory.schema` 增加 `attribute_provenance` 分层字段。
2. D-25 对 D-13 改判：3.2 新非目标文案；FR-17 与“人工可发布率≥75%”门保持不变。
3. §5.2 末尾增加 D-17—D-27 不得浮动规则，并要求回执重跑“目标→FR→门→里程碑”追溯检查。

## 唯一待 Founder 确认事项

请确认：以上四份活基线候选、远程 `main` 的固定提交、临时目录重复件处置，以及旧 v1.2 候选的派生材料身份，是否共同构成本任务 Phase 1—4 的输入基线。

确认前不执行产品文档修改；确认后才会把 D-17—D-27、S1—S8、治理角色模型与三项补丁一次性合并到完整 PRD v1.2 候选。



---

## 续跑说明（Founder 确认后）

Founder 已于 2026-08-13 确认本 Manifest 为 Phase 1—4 输入基线，原文：
「确认该 Manifest 为本任务 Phase 1—4 输入基线。」

Phase 0 之后 Codex 执行面因网络中断停摆。Founder 依执行 Prompt v2.0 §11.3 指派
`TEMPORARY_EXECUTION_WRITER` 接续 Phase 1—5，新执行批次
`2fcbfed0-be7e-4b6f-938e-7f84109ab162`，父批次
`29899f92-c965-4c33-a020-8e7f781fe82d`。Codex 作为默认唯一常规写入者的长期规则未变；
Codex 恢复后是否复核本候选，按 §11.3 由 Founder 明确裁决，本轮不代为假定
（见 `governance/conditions/conditional_decision_ledger.yaml` COND-004）。

补充裁决 `DIYU-CBFSK-GOV-ROLE-OPERATING-MODEL-002-SUPP-01`（D-28 / D-29）在第一候选
Commit 冻结前并入 Phase 2 合并范围，裁决区间由 D-17—D-27 扩展为 **D-17—D-29**。

本报告的 Phase 0 对账结论、哈希与临时目录处置建议均未修改。
