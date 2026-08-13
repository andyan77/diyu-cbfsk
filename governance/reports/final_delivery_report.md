# 最终交付报告 · DIYU-CBFSK-GOV-ROLE-OPERATING-MODEL-002

> 基线迁移、治理角色操作模型与 PRD v1.2 合并落盘
> 执行批次 `2fcbfed0-be7e-4b6f-938e-7f84109ab162`（父批次 `29899f92-c965-4c33-a020-8e7f781fe82d`）
> 生成日期 2026-08-13｜任务分级 **L3**｜状态 **候选已冻结，未生效、未合并**

## 0. 执行主体与授权（必须先读）

Phase 0（基线对账）由 Codex 完成并停在「等待 Founder 确认 Manifest」。Founder 于 2026-08-13
确认 Manifest 为 Phase 1—4 输入基线后，Codex 执行面因网络中断停摆，Founder 依执行 Prompt v2.0
**§11.3** 指派 `TEMPORARY_EXECUTION_WRITER` 接续 Phase 1—5。

| 项 | 取值 |
|---|---|
| 接替执行角色 | `TEMPORARY_EXECUTION_WRITER` |
| 是否兼任本任务 Guardian | **否** |
| 是否兼任本任务 Planner 会话 | **否** |
| 是否改变 Codex 默认唯一写入者长期规则 | **否** |
| Codex 恢复后是否复核本候选 | **未裁决**——按 §11.3 须 Founder 明确，本轮不代为假定（COND-004） |

本报告中所有 `PASS` 均为**候选施工侧自检**，不构成独立 Guardian 结论、不构成 ChatGPT 总顾问审查、
不构成外部独立验证。

## 1. 基线对账（Phase 0 结论 + Founder 确认）

- 远程仓库：`https://github.com/andyan77/diyu-cbfsk`
- 远程 `main` 固定提交：`ce13cf3d6dca3ed6ac918400c8c08c10051832bf`
- 本任务起点提交：`1b6f66864b288b8ebd3ff5894fae839d57ae6655`（分支 `codex/baseline-reconciliation-v2`）
- **binary 层（本候选内实测）**：三份 v1.1 DOCX 与 README 的 binary SHA-256 与 Founder 本轮提供的
  参考值、与 Manifest 记录值逐一相等。
- **canonical / semantic 两层**：「本地＝远程」这一结论由 Phase 0 作出，其哈希实现不在本候选内，
  **本候选无法重新验证该结论**。按 Founder 修复指令 BLOCK-01(a)，这两层已由候选内唯一实现重算并钉入
  Manifest（Phase 0 原值保留在 `phase_0_recorded_*` 供审计），此后用于漂移检测。实测发现 8 份仓内 DOCX
  的 Phase 0 派生值在候选内实现下**均不可复现**，说明此前存在两套哈希实现。
- 未发现产品语义差异，无需逐段逐表提交 Founder 裁决。
- 临时目录 `D:\tmpcodex` 两份文件确认为 `归档_v1.0/` 副本，登记为 `DUPLICATE_CONFIRMED`，
  **未删除**（删除仍需 Founder 批准）。
- Founder 存档区 `治理执行Prompt_分工审计与补强意见书.docx` 登记为仓外历史证据，**未导入**（COND-006）。
- 旧 v1.2 候选 `ace63603f327d61775eff78eef2fbfa9259bb67c` 标记为 `STALE_DERIVED_ARTIFACT`，完整保留未改写。

**Phase 1 迁移动作 MIG-01（红线修复）**：起点提交 `1b6f668` 曾把三份 v1.1 提前归档到 `归档_v1.1/`，
违反 §18「在 v1.2 生效前归档 v1.1」。本轮已将三份文件 **R100 纯改名移回根目录，字节未变**，
`归档_v1.1/` 目录不存在。`工具/check_prd_v1_2.py` 现在默认断言「未归档且 v1.1 在根目录」，
只有 v1.2 正式生效后才允许带 `--require-archive` 反向断言。

## 2. Founder 裁决落实矩阵

### 2.1 产品裁决 D-17—D-29

| 裁决 | 主要锚点 | 状态 |
|---|---|---|
| D-17 M11 双路径 | 1.3 / 4.4 / 6.1 / 7 / 8.7 / 13-14 M11 / 15.6 / 16 / 附录B | PASS |
| D-18 合成封闭未见品牌 | 8.6 / 8.7 / 10.3 / 16.2 / 附录B | PASS |
| D-19 Commercial V1.0 命名与路线 | 12 / 13 / 14 / 15.1 | PASS |
| D-20 搭配师人设连续性 C-13 | 5.5 / 9.5 / 9.6 / 9.9 / FR-23 / FR-24 / M1 Schema / M2 评分卡 / M7 | PASS |
| D-21 自媒体原生语感 C-14 | 9.7 / 9.8 / FR-25 / M2 语感评分卡 / M7 | PASS |
| D-22 VM 扩展端口 | 3.2 / 3.3 / 5.7 / FR-27 / 11.1 / 15.6 / 附录B | PASS |
| D-23 多模态商品理解 C-15 | 3.2 改判 / 5.6 / FR-22 / garment_and_inventory.schema.attribute_provenance / 11.1 | PASS |
| D-24 实时成交辅助端口 | 3.2 / 4.4 S-07 / 5.7 / FR-27 / 15.6 | PASS |
| D-25 Founder 控制发布 | 3.2 改判 / FR-28 / 10 硬门 / 11.1 / FR-17 与 ≥75% 保留 | PASS |
| D-26 五类激活就绪 | 3.1 / FR-29 / 10 / 13-14 / 15.5 | PASS |
| D-27 Project CI 单一规范源 | G-15 / FR-30 / 8.7 / 16.2 / 16.4 / 附录A / governance+ci+.github | PASS |
| **D-28 合理多解原则** | **3.3 P-14 / M2 三分类 / M3 / M4 / M5 / M6 / M10 / 10.2 指标更名 / 16.1 R-22 / 16.2 / 附录B** | PASS |
| **D-29 M6 反退化验收** | **M6 目标 + 交付物 + 通过标准三条 / 11.1 三组件 / 16.2 / negative fixture** | PASS |

**编号裁决说明**：补充 Prompt 文字把 D-28 的原则写作 `P-10`、风险写作 `R-15`；这两个编号已被
D-20—D-26 占用。执行 Prompt v2.0 明令「原有编号一律不重排」，故本版落为 **P-14 / R-22**，
语义与补充 Prompt 完全一致，映射已写入 `PRD_v1.2_change_map.yaml` 的
`principle_id_note` / `risk_id_note` 与 `governance/founder_rulings/DIYU-CBFSK-FR-EVAL-003.yaml`。

### 2.2 治理裁决 S1—S8 与角色模型

| 项 | 落点 | 状态 |
|---|---|---|
| S1 基线锚定 | `governance/baseline/founder_pinned_baseline.v0.1.yaml`（三层哈希 + Founder 确认） | PASS |
| S2 单次 v1.2 签署 | PRD v1.2 全文候选；v1.1 保持 `PENDING_FOUNDER_SIGNATURE` 活基线 | PASS |
| S3 单一 Founder 审查模型 | PRD 10.2 / 15.3 / 15.4 / 16.4 + `review_mode` 合同 + 合规台账 | PASS |
| S4 角色不可用降级 | `role_unavailability_fallback`（默认 DEFER，禁静默绕过）+ PRD 16.4 | PASS |
| S5 隐藏评测物理隔离 | `governance/storage/hidden_benchmark_storage_contract.yaml` + 目录改名 `02_benchmark_manifests/` | PASS |
| S6 工作区证据与自举 | `governance/workspaces/` + `guardian_bootstrap_source` | PASS |
| S7 任务分级 L1/L2/L3 | `task_classification` + PRD 16.4 | PASS |
| S8 Cowork 归位 | `CLAUDE_PLANNING_AND_VERIFICATION_SURFACE` 角色（无写权、无 Guardian、无独立评审票） | PASS |
| 单一 Founder 模式 | `current_human_team` 1 人；8—10 人配置降为 `NON_BINDING_REFERENCE` | PASS |
| 工程量口径 | 125—185 人月 / 15—24 个月**未改变**；`staffing_commitment=false` | PASS |
| ChatGPT 总顾问 | 只读、无写权、无 Guardian、无最终批准；Web 与 Work 合计 1 票 | PASS |
| Claude Planner | 只读、不写仓、不自审 | PASS |
| Codex 默认唯一写入 | `default_repository_writer: true`；合并需 Founder 授权 | PASS |
| Claude Guardian | 只审冻结 Commit；`planning_context_access=false`、`candidate_edit_permission=false` | PASS |
| 不可用替位 | 本轮实际行使：Codex 不可用 → Founder 指派 TEMPORARY_EXECUTION_WRITER，已入 Receipt 与 COND-004 | PASS |
| 隐藏集独立存储 | 三类合法存储登记，均 `provisioned: false`（本任务不选址、不生成资产） | PASS |
| 条件关闭 | `conditional_decision_ledger.yaml` 7 条 OPEN 条件，字段齐全 | PASS |
| 合规逐项决定 | `founder_compliance_decision_ledger.yaml` 七项，全部 `PENDING_FOUNDER_DECISION`（执行侧不代填） | PASS |

## 3. 文件清单与哈希

> **Commit 哈希的唯一权威载体是 `governance/receipts/candidate_freeze_receipt.yaml`。**
> 本节只列文件级 SHA-256；候选 Commit、冻结回执 Commit、candidate_tree 与基线 Commit
> 一律以该回执为准，本报告不再另行复述，避免出现第二处可能漂移的口径。

### 3.1 新建（21 + 角色/Prompt/Checker/Fixture 目录）

| `governance/baseline/baseline_migration_record.yaml` | `9a3f117195137742a4187f7978d7e18529cbc353203859908511b7d8dbabe90b` |
| `governance/bootstrap/role_operating_model.v0.2.yaml` | `effecb2b1340cbf1e9263fa32399c445ffe6487ca6ecc62636989df4e5a534f8` |
| `governance/founder_rulings/DIYU-CBFSK-FR-ORG-002.yaml` | `83638751e9a4f0e95ec74403cd821073dcbe434049ddae1dd3939206d644cf25` |
| `governance/founder_rulings/DIYU-CBFSK-FR-EVAL-003.yaml` | `c4bf1a4052123a84915b7614a9f5a487f6ee1f599a2d037aeed62e52bbb10de2` |
| `governance/conditions/conditional_decision_ledger.yaml` | `47430036acc55ca59cd173afe6e13c4a42d77aa6793e38ebde36f9d210e5e8a7` |
| `governance/compliance/founder_compliance_decision_ledger.yaml` | `709e2135f22d495ceb0585e65b1c15bdbdffe2ea35269ac069138b7894d6c2c6` |
| `governance/storage/hidden_benchmark_storage_contract.yaml` | `4b8233279b43fa85c314b3460efd2d454e6e52153f4c02403d1d7d3e7557dce1` |
| `governance/workspaces/workspace_attestation.schema.yaml` | `7122033f0266153a2aec49533ca01b8e6609e3f532dc2416b47aa067328d805f` |
| `governance/workspaces/workspace_attestation.DIYU-CBFSK-GOV-ROLE-OPERATING-MODEL-002.yaml` | `10b12f21ffe70e4ab2dbaa387c2af34b4e523e300a271edb044d5f19681591b8` |
| `governance/receipts/guardian_handoff_package.yaml` | `1dd784c63a56438451656c1ea4d67474479a027ff3c54eb5e2c1cff3389fb4da` |
| `AGENTS.md` | `141b771d9e971110eb27b8d0e4fb9eb283db2ec5b02ebf0d2b0f9bc8c861f1f0` |
| `CLAUDE.md` | `14a4c6726f38598acefcbac1fd9599c8ad8d39ba34f8303dca00e194dc3c0cc6` |
| `.github/copilot-instructions.md` | `e16f0ae168c80708222efa577003274365119a51ed8c42ddd9d86ec21dc56013` |
| `.github/CODEOWNERS` | `444d1e54ade1a0789242c45e0d70daff597291385a8fe7943d1deae4e30d1100` |
| `.github/pull_request_template.md` | `1d43df34c20ae7d322bc580b99e296fc4f53a6985098e9befa801faf0c898b49` |
| `.github/workflows/role-governance-integrity.yml` | `3d1f2a5cc3bc9c2de86a42ce9617ef70dabe96f56d0a888b076f8ae3c97c0733` |
| `.github/workflows/document-integrity.yml` | `55358cda7791e84b8e052a211c0f0a942e35b49e487a28912424145bf412b39d` |
| `.github/workflows/secret-and-hidden-boundary.yml` | `38c84c611ca123f3aac8dfd22974cb115a8a25862443f414997e0369bc2ecf3a` |
| `ci/compile_role_instructions.py` | `e1db8622841f2dea4aa3c69338c5bbce23249531a992ad092a6c963e3fb0f1d0` |
| `ci/run_all_checks.py` | `d3626f9eb8685fc38d8075bb704e644c5557a326054ac225b3050a8443bd3e7f` |
| `ci/run_fixtures.py` | `a916cc6393791f24db5a45ad9137d1c546718a0c348548c9938919d2343d46b4` |

角色合同（生成投影，5 份）：`governance/roles/chatgpt_chief_advisor.md`, `governance/roles/claude_execution_planner.md`, `governance/roles/claude_independent_guardian.md`, `governance/roles/codex_execution_engineer.md`, `governance/roles/founder_decision_charter.md`

角色 Prompt（生成投影，4 份）：`governance/prompts/chatgpt_chief_advisor.prompt.md`, `governance/prompts/claude_execution_planner.prompt.md`, `governance/prompts/claude_independent_guardian.prompt.md`, `governance/prompts/codex_execution_engineer.prompt.md`

Checker（16 个）：`check_active_product_truth.py`, `check_baseline_hashes.py`, `check_compliance_ledger.py`, `check_conditional_ledger.py`, `check_docx_canonical_hashes.py`, `check_effort_baseline_consistency.py`, `check_execution_uuid.py`, `check_external_review_claims.py`, `check_hidden_benchmark_boundary.py`, `check_instruction_projection.py`, `check_m0_fourteen_items.py`, `check_project_state.py`, `check_role_operating_model.py`, `check_ruling_coverage.py`, `check_task_classification.py`, `check_workspace_attestation.py`

Fixtures（38 份）：positive 11 / negative 27

### 3.2 修改

| `笛语跨品牌服装搭配专家内核_PRD与执行里程碑_v1.2.docx` | `ba34ab9eb02256d4fa638e3851c81fa0256be6562c5e802b6473d64b7123c143` |
| `笛语跨品牌服装搭配专家内核_M0执行申请_v1.2.docx` | `6b492c42b0e0bfc6a1b1710949eea4682c69ce62e98a9ca6bcf35ad9937e0fea` |
| `PRD_v1.2_核验回执.docx` | `e2c29224c7e671531e0d966ff4a6ce2d58109b5255ca82b801074594b78da687` |
| `PRD_v1.2_change_map.yaml` | `0f57dffe1da0fedfea09bcb67ca9748476976133f0c5767907a1073243e582b8` |
| `README.md` | `60942ea4346bd0893583aff202127192710e02cfea9f2cc765d4cdadec138a31` |
| `工具/build_prd_v1_2.py` | `61fad2ab659833059a229ada6b6c24a720ad47796deb8c0d8e63104eb870a303` |
| `工具/check_prd_v1_2.py` | `cb6c4f404de7abb70539733590e2bedb5f664167f607075487ed905c5b010ddb` |
| `governance/baseline/founder_pinned_baseline.v0.1.yaml` | `de8ae154cce44b088e5961733f23898a5b9aa10016c5c62e390c4be6be50d64e` |
| `governance/reports/baseline_reconciliation_report.md` | `1edf3cc5d46fe6ac44b026d8262db365d836b2c9fafe4b00f45e7e328098d566` |
| `governance/receipts/baseline_reconciliation_receipt.yaml` | `af55c612e2f677181cce54c01b949cb11da19c8f97704595caa5245f58d1e7e7` |

### 3.3 迁移（R100 纯改名，字节未变）

| `笛语跨品牌服装搭配专家内核_PRD与执行里程碑_v1.1.docx` | `1532f59eb004bf6a7e47f8429af43969905ba49a51c850b21c728a8711b78f97` |
| `笛语跨品牌服装搭配专家内核_M0执行申请_v1.1.docx` | `bc89e25b437f2cd88e55632451be40213ea6b7733ecfb19b91e5cc7e6463c997` |
| `PRD_v1.1_核验回执.docx` | `080008393c077b2a92d5c79036cfc25f5b1c8027a5630ae42222eb926316b3c9` |

### 3.4 归档候选

- `归档_v1.1/`：**本轮不创建**。只有 PRD v1.2 正式生效后才归档 v1.1。
- `归档_v1.0/`：5 份历史证据保持不变，未重新获得活真源地位。

## 4. Checker 结果（逐项，不写「全绿」）

### 4.1 治理 Checker（16 项）

```
PASS check_execution_uuid
PASS check_baseline_hashes
PASS check_docx_canonical_hashes
PASS check_active_product_truth
PASS check_role_operating_model
PASS check_workspace_attestation
PASS check_task_classification
PASS check_conditional_ledger
PASS check_compliance_ledger
PASS check_hidden_benchmark_boundary
PASS check_external_review_claims
PASS check_m0_fourteen_items
PASS check_project_state
PASS check_effort_baseline_consistency
PASS check_instruction_projection
PASS check_ruling_coverage
```

### 4.2 Fixtures（38 项，positive 必须 PASS、negative 必须 FAIL）

```
PASS fixture N01-invalid-execution-uuid (check_execution_uuid) expected=FAIL [INVALID_EXECUTION_RUN_UUID: execution_run_id='not-a-uuid-2026' is not a valid UUIDv4]
PASS fixture N02-v1.1-semantic-hash-conflict (check_docx_canonical_hashes) expected=FAIL [PRODUCT_BASELINE_SEMANTIC_CONFLICT: 笛语跨品牌服装搭配专家内核_PRD与执行里程碑_v1.1.docx differs semantically; Founder ruling required]
PASS fixture N03-two-active-product-truths (check_active_product_truth) expected=FAIL [DUAL_ACTIVE_PRODUCT_TRUTH: 2 file(s) declare sole product truth: ['笛语跨品牌服装搭配专家内核_PRD与执行里程碑_v1.1.docx', '笛语跨品牌服装搭配专家内核_PRD与执行里程碑_v1.2.docx']]
PASS fixture N04-planner-guardian-same-session (check_workspace_attestation) expected=FAIL [PLANNER_GUARDIAN_SAME_SESSION: planner and guardian share a session id]
PASS fixture N05-commit-changed-without-rereview (check_role_operating_model) expected=FAIL [GUARDIAN_REVIEW_NOT_REDONE: commit changed from aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa to cccccccccccccccccccccccccccccccccccccccc without re-review]
PASS fixture N06-ai-review-as-external-expert (check_external_review_claims) expected=FAIL [FALSE_EXTERNAL_REVIEW_CLAIM: PRD_v1.2 asserts '外部专家共识' in: 未见品牌通过率已获外部专家共识，可作为迁移门证据。]
PASS fixture N07-founder-self-assessment-as-legal-opinion (check_external_review_claims) expected=FAIL [FALSE_EXTERNAL_REVIEW_CLAIM: RECEIPT_v1.2 asserts '独立法律意见' in: 合规部分已形成独立法律意见，六类问题均已结清。]
PASS fixture N08-high-risk-knowledge-sampled (check_role_operating_model) expected=FAIL [HIGH_RISK_COVERAGE: expected 100%, got '20%']
PASS fixture N09-hidden-items-in-main-repo (check_hidden_benchmark_boundary) expected=FAIL [HIDDEN_ASSET_IN_WORKTREE: 02_benchmarks_hidden/items.jsonl]
PASS fixture N10-advisor-silently-skipped (check_task_classification) expected=FAIL [SILENT_SKIP: GPT_CHIEF_ADVISOR is unavailable but Founder decision is None]
PASS fixture N11-temporary-writer-is-guardian (check_role_operating_model) expected=FAIL [TEMPORARY_WRITER_IS_GUARDIAN: temporary writer flagged as task guardian]
PASS fixture N12-conditional-without-ledger (check_conditional_ledger) expected=FAIL [CONDITIONAL_WITHOUT_LEDGER: verdict GUARDIAN-001 records no condition_ids]
PASS fixture N13-rulings-missing-from-v1.2 (check_ruling_coverage) expected=FAIL [RULING_NOT_MERGED: D-27 missing from PRD_v1.2_change_map ruling list]
PASS fixture N14-m0-item-count-changed (check_m0_fourteen_items) expected=FAIL [M0_ITEM_COUNT_CHANGED: PRD 17.1 首任务必须交付 has 15 items, expected 14]
PASS fixture N15-premature-archive-v1.1 (check_active_product_truth) expected=FAIL [PREMATURE_ARCHIVE: 归档_v1.1/ exists while prd_v1_2_effective=false (red line: 在 v1.2 生效前归档 v1.1)]
PASS fixture N16-unsigned-marked-effective (check_project_state) expected=FAIL [PREMATURE_TRUE_FLAG: m0_authorized=True, must stay false]
PASS fixture N17-m6-prompt-rag-direct-answer (check_ruling_coverage) expected=FAIL [M6_ANTI_DEGENERATION_VIOLATED: a pure Prompt/RAG direct-answer implementation was accepted]
PASS fixture N18-instruction-projection-drift (check_instruction_projection) expected=FAIL [PROJECTION_DRIFT: AGENTS.md differs from the canonical render]
PASS fixture N19-stale-metric-name-live (check_ruling_coverage) expected=FAIL [STALE_METRIC_NAME: 核心判断重复一致率 used as a live metric name in: 核心判断重复一致率 ≥ 85% 允许表述变化，不允许关键选择无依据漂移。]
PASS fixture N20-authorized-file-changed-after-freeze (check_baseline_hashes) expected=FAIL [AUTHORIZED_FILE_CHANGED_AFTER_FREEZE: README.md binary sha256 9999999999999999999999999999999999999999999999999999999999999999 != pinned 1111111111111111111111111111111111111111111111111111111111111111]
PASS fixture N21-marker-in-ordinary-file (check_hidden_benchmark_boundary) expected=FAIL [HIDDEN_CONTENT_MARKER: docs/notes.md contains 'HIDDEN_BENCHMARK_ITEM']
PASS fixture N22-marker-outside-allowlist (check_hidden_benchmark_boundary) expected=FAIL [HIDDEN_CONTENT_MARKER: governance/reports/some_other_report.md contains 'HIDDEN_BENCHMARK_ITEM']
PASS fixture N23-manifest-derived-hash-unreproducible (check_docx_canonical_hashes) expected=FAIL [CLASSIFICATION_MISMATCH: 笛语跨品牌服装搭配专家内核_PRD与执行里程碑_v1.1.docx computed MANIFEST_DERIVED_HASH_UNREPRODUCIBLE, expected BINARY_EQUAL]
PASS fixture N24-semantic-layer-unreproducible (check_docx_canonical_hashes) expected=FAIL [CLASSIFICATION_MISMATCH: PRD_v1.1_核验回执.docx computed MANIFEST_DERIVED_HASH_UNREPRODUCIBLE, expected BINARY_EQUAL]
PASS fixture N25-gate-line-filter-drift (check_m0_fourteen_items) expected=FAIL [GATE_LINE_FILTER_DRIFT: PRD 14 / M0 总清单 removed 2 gate line(s), expected exactly 3]
PASS fixture N26-effort-baseline-drift (check_effort_baseline_consistency) expected=FAIL [EFFORT_BASELINE_DRIFT: person_months differs across sources -> {'role_operating_model': '125—185', 'prd': '150—200', 'change_map': '125—185'}]
PASS fixture N27-staffing-commitment-claimed (check_effort_baseline_consistency) expected=FAIL [STAFFING_COMMITMENT_CLAIMED: role_operating_model states staffing_commitment=True]
PASS fixture P01-baseline-local-equals-remote (check_baseline_hashes) expected=PASS
PASS fixture P02-packaging-only-difference (check_docx_canonical_hashes) expected=PASS
PASS fixture P03-planner-guardian-separate-workspaces (check_workspace_attestation) expected=PASS
PASS fixture P04-founder-per-item-compliance (check_compliance_ledger) expected=PASS
PASS fixture P05-l1-task-correctly-simplified (check_task_classification) expected=PASS
PASS fixture P06-prohibition-sentences-are-compliant (check_external_review_claims) expected=PASS
PASS fixture P07-renamed-metric-note-allowed (check_ruling_coverage) expected=PASS
PASS fixture P08-own-fixture-is-not-a-leak (check_hidden_benchmark_boundary) expected=PASS
PASS fixture P09-all-three-layers-reproduce (check_docx_canonical_hashes) expected=PASS
PASS fixture P10-gate-line-filter-exact (check_m0_fourteen_items) expected=PASS
PASS fixture P11-effort-baseline-consistent (check_effort_baseline_consistency) expected=PASS
```

### 4.3 PRD 合同 Checker（`工具/check_prd_v1_2.py`：57 PASS / 0 FAIL）

```
PASS file exists: 笛语跨品牌服装搭配专家内核_PRD与执行里程碑_v1.2.docx
PASS file exists: 笛语跨品牌服装搭配专家内核_M0执行申请_v1.2.docx
PASS file exists: PRD_v1.2_核验回执.docx
PASS file exists: README.md
PASS file exists: PRD_v1.2_change_map.yaml
PASS document status and version
PASS PRD header version is current
PASS forbidden phrase absent: V1.0全生命周期保持人工审核在环
PASS forbidden phrase absent: 所有商业发布门通过后仍不得自动发布
PASS forbidden phrase absent: 图像识别属性提取不属于V1.0
PASS forbidden phrase absent: 商品属性只能来自PIM/ERP，图片不得参与
PASS forbidden phrase absent: 完整陈列能力永久退出
PASS forbidden phrase absent: 实时导购能力永久退出
PASS forbidden phrase absent: 人设仅由账号语气合同承担
PASS forbidden phrase absent: 叙事质量等同于自媒体语感
PASS G IDs are consecutive G-01..G-15
PASS C IDs are consecutive C-01..C-15
PASS FR IDs are consecutive FR-01..FR-30
PASS NFR IDs are consecutive NFR-01..NFR-12
PASS risk IDs are consecutive R-01..R-22
PASS principle IDs are consecutive P-01..P-14
PASS input/configuration object count is 12
PASS output/audit object count is 15
PASS new input/configuration objects
PASS new output/audit objects
PASS formal capabilities C-13..C-15
PASS extension-compatible contracts
PASS Founder-controlled publication contract (D-25 patch)
PASS multimodal evidence grading and hard gates
PASS FR-22 has acceptance/failure/milestone trace
PASS FR-23 has acceptance/failure/milestone trace
PASS FR-24 has acceptance/failure/milestone trace
PASS FR-25 has acceptance/failure/milestone trace
PASS FR-26 has acceptance/failure/milestone trace
PASS FR-27 has acceptance/failure/milestone trace
PASS FR-28 has acceptance/failure/milestone trace
PASS FR-29 has acceptance/failure/milestone trace
PASS M1 schema and object mapping
PASS M2 evaluation additions
PASS M7 deliverables
PASS M11 dual paths and conditional evidence
PASS M12 readiness and governance
PASS risk additions R-15..R-21
PASS new stop conditions
PASS all new terms are in glossary
PASS M0 fourteen items (delegated to ci/checkers)
PASS M0 v1.2 control and Guardian additions
PASS verification receipt identifiers and final state
PASS README current-baseline index
PASS D-28 non-uniqueness anchors
PASS D-29 anti-degeneration anchors
PASS reviewer_calibration_contract appears once per milestone list (13/14), not duplicated
PASS machine-readable change map
PASS v1.1 not archived before PRD v1.2 is effective
PASS active baseline stays at root: 笛语跨品牌服装搭配专家内核_PRD与执行里程碑_v1.1.docx
PASS active baseline stays at root: 笛语跨品牌服装搭配专家内核_M0执行申请_v1.1.docx
PASS active baseline stays at root: PRD_v1.1_核验回执.docx
```

### 4.4 DOCX 包完整性与投影漂移

```
PASS 笛语跨品牌服装搭配专家内核_PRD与执行里程碑_v1.2.docx: ZIP CRC, required parts, XML parse, header version
PASS 笛语跨品牌服装搭配专家内核_M0执行申请_v1.2.docx: ZIP CRC, required parts, XML parse, header version
PASS PRD_v1.2_核验回执.docx: ZIP CRC, required parts, XML parse, header version
PASS instruction_projection: 12 files, drift=0
```

### 4.5 实测补证（本轮亲自运行）

| 项目 | 结果 |
|---|---|
| python-docx 打开三份 DOCX | PRD 790 段 / 44 表；M0 申请 47 段 / 3 表；回执 16 段 / 4 表，全部 OK |
| 生成器重放 | 三份 DOCX **语义哈希稳定**（semantic_text_sha256 一致） |
| 生成器二进制可复现性 | **否**——python-docx 写 ZIP 带时间戳，binary 哈希每次不同；请以 canonical/semantic 层比对，不要以 binary 层判定重放一致性 |
| ID 独立重数（不复用生成器常量） | G 15 / P 14 / S 9 / C 15 / FR 30 / NFR 12 / R 22 / 输入对象 12 / 输出对象 15 |

### 4.6 本轮修掉的三类真实缺陷

| 类型 | 问题 | 处置 |
|---|---|---|
| 语义个案 | M2 交付物出现两条同名 `reviewer_calibration_contract.v0.1.yaml` | 合并为单条兼容扩展（13/14 节各一条），并加 count==2 断言 |
| 协议缺陷 | 3 个 Checker 把「不得表述为外部专家共识」这类**禁止句**误判为违规 | 判据改为「肯定性主张」，否定/禁止语境豁免；新增 P06 / N06 / N07 / P07 / N19 五份 fixture 行使该规则 |
| 协议缺陷 | `工具/check_prd_v1_2.py` 用 `items[:14]` 截断 M0 清单——第 15 项会被静默吞掉 | 去掉截断，改为剔除三行标准验收门后**不截断**比对；ci 侧 `check_m0_fourteen_items` 同样不截断 |
| 协议缺陷 | README 属本任务授权修改文件，但基线 Checker 会把它判成基线冲突 | Manifest 登记 `authorized_modification_in_this_task` + 钉住交付态哈希；新增 N20 fixture |
| 协议缺陷 | 隐藏边界 Checker 把「描述违规的负向 fixture」与「引用 checker 输出的交付报告」当成泄漏（两轮假阳性） | 例外定为两条：① 本 checker 自己的 fixture；② 存储合同里**显式列出**的三条文档白名单（写进 `hidden_benchmark_storage_contract.yaml`，Founder/Guardian 可见，不在代码里隐式放行）。其余一律 FAIL。新增 P08 / N21 / N22 三份 fixture 行使该边界 |

## 4.7 Guardian REJECT 修复批次（f48fed3 → 本候选）

Guardian 对 `f48fed3091384cc459b258dace3c267b1d08d1b0` 判 REJECT。Founder 令一次修完、一次重审。

| 编号 | 问题 | 处置 | 证据 |
|---|---|---|---|
| **BLOCK-01** | Manifest 的 canonical/semantic 值由 Phase 0 一套已不在本仓的实现产出，与候选内实现**并存**；`classify()` 在 `binary_equal=True` 处短路，导致后两层从未被真正比对——**此前的 PASS 是假绿** | ① 哈希实现归一到 `ci/checkers/_common.py`，checker 只消费不再自造；② `classify()` 去短路，`binary_equal=True` 仍比对后两层，不符报 `MANIFEST_DERIVED_HASH_UNREPRODUCIBLE`；③ 用唯一实现重算并写回 Manifest，Phase 0 原值保留在 `phase_0_recorded_*`；④ `hash_contract` 改为如实描述实现（**不再声称 C14N 2.0**） | 修复后当场实测：**8 份仓内 DOCX 的 Phase 0 派生值全部不可复现**，证实两套实现确实存在；新增 N23/N24/P09 三份 fixture 行使该分支 |
| **NB-01** | 验收门用前缀匹配剔除，可能静默吞掉交付物；且 M0 清单提取在 ci 与 工具 各有一套实现 | 改为三行验收门**精确文本匹配**，剔除数写入 payload 由 `validate()` 断言（第13节/17.1 区 0 行、第14节恰 3 行）；`工具/check_prd_v1_2.py` 删除自有实现，委托 ci 唯一实现 | 实测剔除数 0/3/0；新增 N25/P10 fixture |
| **NB-02** | 工作区 Schema 把审查对象写成「冻结候选 Commit」，与两段式冻结不符 | 改为「本分支冻结 HEAD」 | — |
| **NB-03** | 交付报告未指明 Commit 哈希的权威载体 | §3 首行加指针：唯一权威载体是 `candidate_freeze_receipt.yaml` | — |
| **NB-04** | 人月/工期基线散落三处，无机器校验 | 新增 `check_effort_baseline_consistency.py`，逐字段比对 PRD 表格单元、规范源与 change_map | 新增 P11/N26/N27 fixture |
| **NB-05** | `effort_baseline` 未进 change_map 不变量 | `person_months` / `duration_months` / `effort_unit` 三字段落入 `invariants` | — |
| **NB-06** | B1 新增的三处路径关系条件未入台账 | 落为 COND-008：`D:\笛语跨品牌服装搭配专家内核`（仅存档）／WSL 工作区（施工）／远程仓库（唯一正式产品真源），关系固定为「远程唯一真源 ← WSL 推送 ← D:\ 仅存档」，禁止反向 ingest | **更正记录**：执行侧曾按候选内「三处路径」误推断为隐藏标记白名单（证据等级 inferred，已在原条目标注待确认）；收到 Guardian 报告全文后按 B1 原意更正，`correction_note` 留档 |

**Guardian 结论处置**：Guardian 对 `f48fed3091384cc459b258dace3c267b1d08d1b0` 判 **REJECT**（BLOCK-01），
报告全文一字未改落盘于 `governance/reports/guardian_review_report.f48fed3.md`。Founder 选定 BLOCK-01 的
**required_delta (a)+(c)**，已按此执行。按 §14，该 REJECT 结论对本轮新候选 Commit **自动失效**，
必须全量重审、不得沿用（COND-009）。Founder 见证行（B4）已签署并落入
`governance/workspaces/workspace_attestation.…yaml`，Guardian 记录与见证块的 PENDING/null 已清除；
总顾问记录仍为 `PENDING`——那是尚未发生的事件（COND-002），不是待填字段。

**工程质量标准（Founder 裁决，自本批次起长期生效）** 已写入规范源 `engineering_quality_standard`（EQ-1 单一实现原则 / EQ-2 合同与实现严格一致 / EQ-3 每 checker 必有 negative fixture / EQ-4 无死代码无魔法常量 / EQ-5 修复优先重构），并由编译器投影进 `AGENTS.md`、`CLAUDE.md` 与 Codex 角色 Prompt，对后续所有执行包生效。

## 5. 未决事项（只列真正需要 Founder 裁决的问题）

1. **独立 Guardian 对新候选 Commit 的全量重审**（COND-001 / COND-009）——Guardian 已对 `f48fed3` 审过并判
   REJECT；修复形成新 Commit 后该结论按 §14 失效，须在独立工作区重审新 Commit，报告写明
   `guardian_bootstrap_source: THIS_APPROVED_PROMPT_SECTION_7_5_AND_8`。
2. **ChatGPT 总顾问远程审查**（COND-002）——尚未进行。不可用时须 Founder 显式 DEFER / 指派替位 / 豁免并接受风险。
3. **Founder 签署**（COND-003）——PRD v1.2 与 M0 执行申请 v1.2 是**两个独立决定**，可以出现
   「PRD v1.2 PASS 但 M0 仍未授权」。签署须绑定 `prd_file_hash` / `m0_request_file_hash` / `candidate_commit`。
4. **Codex 恢复后是否复核本候选**（COND-004）——§11.3 要求 Founder 在例外裁决中明确，不得自动假定。
5. **Founder 工作区见证行**（COND-005）——已于 2026-08-13 由 Founder 签署，条件转
   `EVIDENCE_SUBMITTED`；`closure_commit` 待绑定最终 Commit 后由 Founder 关闭。
6. **`治理执行Prompt_分工审计与补强意见书.docx` 是否导入主仓**（COND-006）。
7. **七项合规决定**（`founder_compliance_decision_ledger.yaml`）——全部 `PENDING_FOUNDER_DECISION`，
   执行侧不代填 `founder_decision`。
8. **隐藏评测存储选址**——三类合法存储均 `provisioned: false`，须 Founder 在 M2 冻结前裁决。
9. **B1 三处路径关系确认**（COND-008）——`D:\` 存档 / WSL 施工 / 远程唯一真源三者关系，
   须 Founder 或 Guardian 确认与 B1 所指一致（执行侧曾误推断，已更正并留档）。

以下**不是**未决事项，已由已批准 Prompt 或本轮裁决定案，不重新标为建议默认：
D-17—D-29 全部落点、S1—S8、角色权限、任务分级、M0 十四项、125—185 人月基线、
`M2_FREEZE_REQUIRED` 阈值（按合同留待 M2 冻结，非落文缺口）。

## 6. 完成状态

```yaml
baseline_reconciled: true
founder_baseline_confirmed: true

prd_v1_2_candidate_created: true
prd_v1_2_effective: false

role_operating_model_landed: true
role_operating_model_effective: false

guardian_review_completed: false          # 针对本轮新候选 Commit；f48fed3 的 REJECT 按 §14 已失效
prior_guardian_decision_on_f48fed3: REJECT
prior_guardian_decision_valid: false
founder_workspace_attestation_witnessed: true
chatgpt_remote_review_completed: false
founder_prd_signed: false
founder_m0_authorized: false
founder_merge_approved: false
main_merged: false

m0_execution_started: false
m1_started: false
m2_started: false
knowledge_distillation_started: false
production_servable: false
```

## 7. 红线自查

| 红线 | 本轮 |
|---|---|
| 开始 M0 十四项施工 / M1 / M2 / 知识蒸馏 | 未 |
| 生成夹具品牌或隐藏品牌 | 未（只建存储与工作流合同） |
| 隐藏集进入主仓或 Git 历史 | 未（worktree 与全历史双向扫描通过） |
| 接入真实库存 / 真实顾客 / 创建 Serving / 自动发布 | 未 |
| 修改笛语系统底座 | 未 |
| 把 AI 评审冒充外部专家 / Founder 自评冒充法律意见 | 未（并已落 Checker 守卫） |
| 未完成基线对账即修改产品真源 | 未（Founder 确认后才动文档） |
| v1.2 生效前归档 v1.1 | **已撤销**起点提交中的提前归档 |
| Founder 批准前合并 main | 未合并、未推送 |
| 用「最新版」代替 Commit 哈希 | 未（全文均用完整哈希） |
| 静默绕过不可用角色 | 未（Codex 不可用已走 §11.3 显式指派并入台账） |
| 改变 125—185 人月 / 15—24 个月 / M0 十四项 | 未 |
| 把本任务表述为 M0 已开工 | 未 |
