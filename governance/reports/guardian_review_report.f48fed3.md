# Guardian 审查报告 · DIYU-CBFSK-GOV-ROLE-OPERATING-MODEL-002

```yaml
reviewed_commit_hash: f48fed3091384cc459b258dace3c267b1d08d1b0
guardian_workspace_id: /home/faye/claude-guardian-diyu-cbfsk-clean
guardian_bootstrap_source: THIS_APPROVED_PROMPT_SECTION_7_5_AND_8
decision: REJECT

scope_alignment: PASS —— 变更面与交接包 changed_files 声明一致；f48fed3 相对 a235b55 实测仅新增 candidate_freeze_receipt.yaml（+75 行，单文件），tree 6e5963ca→bae5ff19、102→103 文件，两段式冻结断言复算成立
founder_ruling_alignment: PASS —— D-17~D-29 共 13 条在 ruling_map 均有 prd_sections 锚点；S1~S8 在 governance_ruling_map 均有 landed 落点；D-28 五锚点、D-29 三条架构符合性抽查齐备
deliverable_closure: PASS —— 15 checker / 30 fixture / 64 项 PRD 合同检查 / 12 份投影全部在隔离工作区实跑复现
checker_validity: CONDITIONAL —— 判别力经变异测试证实有效，但存在一处未被覆盖的残留旁路（见 NB-01）
replayability: FAIL —— 见 BLOCK-01
fact_and_safety_boundaries: PASS —— 工作树与全 Git 历史隐藏内容零命中；无夹具/隐藏品牌资产；无 AI 冒充外部专家或 Founder 自评冒充法律意见
review_timestamp: "2026-08-13T04:52:51-07:00"

workspace_attestation:
  workspace_path: /home/faye/claude-guardian-diyu-cbfsk-clean
  session_started_at: "2026-08-13T04:02:33-07:00"
  session_id_available: true
  founder_manual_attestation_required: true
```

## 九项特别核验逐项结论

| # | 项目 | 结论 | 证据位置 |
|---|---|---|---|
| 1 | 替补写入合法性 | **PASS** | `candidate_freeze_receipt.yaml:7-8` 声明 `TEMPORARY_EXECUTION_WRITER` + §11.3 依据；run ID 链 `29899f92→2fcbfed0` 在 4 份文件交叉一致；全部回执**无一处冒充 Codex 身份** |
| 2 | 红线修复验证 | **PASS** | `1b6f668` 确有 R100 归档三份 v1.1（红线现场证实）；候选中 `归档_v1.1/` 零命中；三份 v1.1 blob 哈希在 `ce13cf3→1b6f668→f48fed3` 三点逐一相同 |
| 3 | 裁决落实矩阵 | **PASS** | `PRD_v1.2_change_map.yaml` ruling_map D-17~D-29 带 prd_sections；D-28 五锚点全部命中；D-29 三条 + `n17_m6_prompt_rag_direct_answer.yaml` 齐备 |
| 4 | 编号顺延 | **PASS** | change_map:137-138/150-151 + `FR-EVAL-003:18-21` 双处映射；PRD v1.2 实测 P-01..P-14、R-01..R-22 **连续无缺无冲突**，旧编号零残留 |
| 5 | 四项自报缺陷独立验证 | **3 PASS / 1 PASS-with-residual** | 见下方 NB-01 |
| 6 | Checker 与 Fixtures 实证 | **PASS** | 15 checker 全 PASS；7 条 negative fixture **绕开 runner 独立复算**均 REAL_FAIL；4 项变异测试证判别力有效；反向探针证 **Founder 见证行无法凌驾机器记录**；64 项逐行核对 |
| 7 | 不变量 | **PASS（附门禁缺口 NB-04）** | `125—185人月`/`15—24个月` 在 v1.1、v1.2 均在；M0 十四项四处清单一致；投影 12 份 drift=0；隐藏内容工作树+全历史零命中 |
| 8 | 台账核验 | **PASS** | 条件台账 7 条全 OPEN、11 必填字段齐全、无提前关闭；合规台账 7 项全 `PENDING_FOUNDER_DECISION`；"律师意见"仅以否定式出现 |
| 9 | 哈希口径 | **FAIL** | 见 BLOCK-01 |

---

## blocking_findings

### BLOCK-01 · Manifest 声明的 canonical/semantic 哈希在候选内不可复现，且被短路结构掩盖

**大白话**：文件本身没问题（字节级我独立验过 17/17 + 4/4 全对）。问题出在"验货单"上——验货单写了三套指纹（原始指纹、去噪指纹、纯文字指纹），并声称三套都核对过。我用仓库自己的代码重算后两套，**三份文件、两套指纹，6 个全对不上**。而负责核对的那道闸，看见第一套对得上就直接放行，**根本不看后两套**，所以这个对不上从来没人发现。

**实测证据**：

| 文件 | binary | canonical | semantic |
|---|---|---|---|
| PRD_v1.1.docx | ✓ `1532f59e…` | ✗ 声明 `752ebe00…` / 实测 `1188f9f1…` | ✗ 声明 `48b69ab1…` / 实测 `eded25ff…` |
| M0执行申请_v1.1.docx | ✓ `bc89e25b…` | ✗ 声明 `6e81d91d…` / 实测 `e9a4b8d1…` | ✗ 声明 `52426029…` / 实测 `b3bbc0a8…` |
| PRD_v1.1_核验回执.docx | ✓ `080008 39…` | ✗ 声明 `a7f8427a…` / 实测 `5c0400dc…` | ✗ 声明 `242762f6…` / 实测 `be1558ea…` |

短路证明（`check_docx_canonical_hashes.py:44-46`）：

```
classify(binary=True,  canonical=False, semantic=False) = BINARY_EQUAL   ← 后两个操作数被忽略
classify(binary=False, canonical=True,  semantic=True ) = PACKAGING_ONLY_DIFFERENCE
```

**根因**（可执行修复的关键）：合同 `hash_contract` 声明 canonical 走 **XML C14N 2.0**，实现却是自写递归序列化器 `_canonical_element`（对属性值用 `repr()`），并且合同要求排除 `w:rsids` **元素**、实现只剥 `rsid*` **属性**。候选中 `grep` 全部 `*.py` **不存在第二套实现**——即这些声明值由 Phase 0（Codex 侧）另一套代码产生，候选里没有任何代码能复现它们。

**为什么判 blocking 而非条件项**：

1. §3.9 是硬性核验项，原文要求"Manifest 声明的 canonical/semantic 哈希必须实测相符"——实测 6/6 不符。
2. `final_delivery_report.md:29-30` **肯定性声称**"三份 v1.1 DOCX 与 README 在 binary / canonical XML / semantic text **三层**与远程完全相等……**无语义差异，无需逐段裁决**"。这句话被用来**免除 Founder 的逐段裁决工作**，而它所依赖的两层指纹在候选内不可验证。
3. 同一份 Manifest 对 `prompt_sha256` **诚实披露**了"不重算、不冒充复核，按继承值原样保留"（L33-35）——证明执行侧懂得该怎么披露继承值；canonical/semantic 却没有任何同等披露，被当作已核验事实呈现。
4. 后果不是理论的：报告 L289 自己说"python-docx 写 ZIP 带时间戳，binary 哈希每次不同，请以 canonical/semantic 层比对"。一旦任何 v1.1 文件被重新打包（报告预期这会发生），闸门会拿实测 canonical 去比一个**永远算不出来的声明值** → 直接落到 `PRODUCT_BASELINE_SEMANTIC_CONFLICT` 硬停，对一个语义从未变过的文件误报。三层哈希合同在真实数据上是**失效**的，`P02-packaging-only-difference` 这条 fixture 用合成字面数据通过，反而制造了覆盖假象。

按 §5「假绿证据 → REJECT」。**这不是内容被篡改的证据**——binary 层我独立验过全对；这是"验证声明超出实际可验证范围"。

**required_delta（三选一，均为小改动）**：
- (a) 用候选内的实现**重算**三份文件的 canonical/semantic 并写回 Manifest，同时把 `hash_contract` 文字改为与实现一致（不再声称 C14N 2.0）；或
- (b) 保留继承值，但**照 `prompt_sha256` 的先例如实披露** `recomputed_by_temporary_execution_writer: false` + `recompute_possible: false`，并把 `final_delivery_report.md:29-30` 的"三层完全相等"降级为"binary 层已核验，canonical/semantic 为 Phase 0 继承值、本轮未重算"；
- (c) 无论选哪条，**都必须**修 `classify()` 的短路：`binary_equal=True` 时仍需比对 canonical/semantic，不一致则显式报 `MANIFEST_DERIVED_HASH_UNREPRODUCIBLE`，并补一条 negative fixture 行使该分支。

---

## non_blocking_findings

| # | 发现 | 证据 | 建议处置 |
|---|---|---|---|
| **NB-01** | `items[:14]` 截断**确已修复**（构造 15 项被当场暴露、13 项也暴露），但替代它的前缀过滤器留了更窄的同类旁路：第 15 项若以 `验收门已通过：` / `工作树、版本、输入清单` / `Founder已形成明确的` 开头会被静默滤掉、计数断言仍绿。三个前缀实测全部可绕。**现存文档未被利用**（三区被滤 3 行均为真验收门行） | `工具/check_prd_v1_2.py:113`、`ci/checkers/check_m0_fourteen_items.py:_checkbox_items` | 改为对三行验收门**精确匹配**而非前缀匹配，或追加断言"被滤掉的行数恰为 3" |
| **NB-02** | `workspace_attestation…yaml:46` 写"base_commit 必须等于**第一候选 Commit**"，与冻结回执 L19、交接包 L30「审查对象是**本分支 HEAD**」口径不一致 | 该文件生成于 a235b55，早于冻结回执 | 判为**旧引用未同步**（非候选身份歧义——f48fed3 相对 a235b55 只多一个回执文件，已实测）。同步该行措辞 |
| **NB-03** | `final_delivery_report.md` 全文不含任何 Commit 哈希，§22.3「文件清单须含 Commit 哈希」在报告内未满足 | 施工侧已自报，我复核属实；哈希实际由 `candidate_freeze_receipt.yaml` 承载 | 采纳施工侧路径①：以冻结回执为哈希唯一权威载体，在报告 §3 加一行指针即可，**不必**为此单开第三个提交 |
| **NB-04** | 「125—185 人月 / 15—24 个月」是 §18 明列红线，却**无任何确定性门禁**：15 个 checker + `工具/` 两个 checker 对该数值全部零命中；`founder_pinned_baseline` 只钉 4 份 v1.1 期文件，不含 v1.2 候选 | `grep 125\|185\|人月 ci/checkers/*.py 工具/*.py` 零命中 | 补一个 checker 断言 PRD v1.2 中该两个区间与 `role_operating_model.v0.2.yaml:effort_baseline` 一致 |
| **NB-05** | 工程量口径新增 `effort_unit=HUMAN_MACHINE_WORK_EQUIVALENT_PERSON_MONTH` 等三字段，在 `change_map` 的 ruling_map / governance_ruling_map / invariants **三处均无锚点** | 锚点实际在 `role_operating_model.v0.2.yaml:118-125`，两份 Founder 裁决亦声明 `effort_baseline_changed: false` | **不构成红线**（数字未变、有规范源锚点、Founder 裁决背书），但建议把 effort_baseline 补进 change_map `invariants` |
| **NB-06** | B1 裁决新增的三处路径关系条件（`D:\` / WSL / 远程唯一真源）尚未落入条件台账 | 台账当前 7 条 | 由执行侧落为 COND-008 |

**已排除的疑点**（查证后确认非缺陷，一并说明避免重复排查）：
- v1.1 的"复用口径降级为条件路线…经 Founder 裁决后重新计算增量工程量"**未被删除**，在 v1.2 拆为独立一行完整保留
- 旧指标名「核心判断重复一致率」在 PRD v1.2 出现 1 处，但**带改名标注**（"原名…阈值≥85%不变"），属 `RENAME_NOTE_MARKERS` 合规引用
- "反退化 / Anti-Degeneration" 字面未入 PRD v1.2，但 D-29 三条实质条款完整且被机器断言覆盖，属术语差异

---

## 给你的一句话总结

**这批东西整体质量很高**——红线修复是真的（三份文件字节级复原）、闸门是真会拦人的（我做了变异测试和对抗构造）、台账没有提前关闭、没有任何隐藏内容进仓、Founder 的见证签名也不能凌驾机器记录。

**卡住它的只有一条**：验货单上有两套指纹声称核对过，但仓库里没有任何代码能算出那两套指纹，而负责核对的闸门看见第一套对上就放行了、从不检查后两套。文件本身没被动过手脚（这点我独立验证了），问题是"声称验过的范围超出了实际能验的范围"——而这句声称被用来免掉你的逐段裁决。按 Prompt §5 的规则，这属于假绿，必须打回。

修起来不大：要么重算写回，要么照 `prompt_sha256` 的先例老实标注"这两套是继承值、本轮没重算"，两条路都必须顺手把那个短路补上。

**下一步**：按 §5，施工侧修复形成新 Commit 后，本结论**自动失效**，须对新 Commit 全量重审，不得沿用。另外提醒——我的 Guardian 记录和你 B4 的见证签名目前**还停在文件里的 `PENDING`/`null` 状态**（`workspace_attestation…yaml:35-48, 61-69`），我无写权限，需由执行侧落盘。

Guardian 工作区 `/home/faye/claude-guardian-diyu-cbfsk-clean` 按 B3 保留作证据，HEAD 仍为 `f48fed3091384cc459b258dace3c267b1d08d1b0`、工作树 dirty=0。

**本结论是工程 Guardian 结论，不是 Founder 批准，也不是外部独立审查。**
