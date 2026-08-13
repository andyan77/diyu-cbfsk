# M2-EP01 交付报告

> 任务 `DIYU-CBFSK-M2-EP01-001`｜分级 `L2`｜计划 `MILESTONE_PLAN_M2 v1.1.0`
> 基线 Commit `6499431c66f7bf4a234bd830ee4c810e1ac78694`（M1-EP01 收口，位于 `main`）
> 分支 `candidate/m2`｜工作区 `/home/faye/diyu-cbfsk-m2`｜`execution_run_id` `41f5cb93-1a3f-4e77-a8e1-142d5ac9de39`

## 1. 每 Phase 一行

| Phase | 结论 |
|---|---|
| P0 基线校验、worktree 与签署落盘 | 三项前置全过（基线哈希＝`main` HEAD 且为 M1-EP01 收口／worktree 路径不存在／`candidate/m2` 不存在），worktree 自基线 Commit 建立；签署声明全文、`m2_started` 授权条目、`M1_M2_PARALLEL_IN_PROGRESS` 枚举与状态切换、FR-CALIBRATION-004 全部落盘 |
| P1 章程与政策落盘 | `FOUNDER-M2-CHARTER-001` 裁决原文一字不改落盘并钉指纹（749 字符，`sha256 7dc5704…`）；商业假设记录与竞品证据政策两份非 ADR 记录落盘；投影经编译器重生成，drift=0 |
| P2 M1→M2 公共元数据信封 | Envelope 与 Profile 两份 Schema、绑定表（6 条 M1-EP01 产物，SHA256 与基线逐条一致）、一份 PROVISIONAL Profile；13 份信封实例夹具（9 负 4 正）全部按声明落 |
| P3 六份最小 ADR | ADR-001—006 齐备，题目与章程 `adr_titles` 逐条一致；四条声明逐份非空；ADR-004 激活条件＝永不；层映射覆盖 12 输入 + 15 输出全 27 个对象 |
| P4 身份识别隔离 | 结构化能力检测 Checker 落地，扫描 235 份结构化文件零命中；8 份扫描用例（4 真实违规必命中 / 4 合规必放行）全部按声明落 |
| P5 评测治理基础 | 评分者校准、抽样设计、基线修订三件套合同 ＋ 评测资产分类 Profile 落盘；隐藏边界执行全部委派既有实现，未建第二套；本包零评测资产 |
| P6 注册、自检与交付 | 4 个新 Checker 全部注册进全量链；全量运行 24 Checker + 161 判据夹具 + 34 Schema 夹具全绿；EQ-1—EQ-5 自查见 §4 |

## 2. 新增文件清单

**治理（`governance/`）**

- `founder_rulings/DIYU-CBFSK-FOUNDER-M2-CHARTER-001.yaml` — M2 章程，裁决原文 + 指纹 + Milestone Plan 信封
- `founder_rulings/DIYU-CBFSK-FR-CALIBRATION-004.yaml` — 校验强度分级定稿，首次形成仓库文件
- `receipts/founder_m2_kickoff_signature_receipt.yaml` — 签署声明全文 + 基线绑定 + 前置校验记录

**M2 评测基础合同（`03_m2_evaluation_foundation/`）**

- `envelope/m1_to_m2_envelope.schema.v0.1.json`、`envelope/profile_composition.schema.v0.1.json`
- `envelope/m1_source_binding.v0.1.yaml`、`envelope/profiles/m2_evaluation_provisional_profile.v0.1.yaml`
- `adr/ADR-001…ADR-006`（六份）
- `architecture/m1_object_layer_map.v0.1.yaml`
- `evaluation_governance/reviewer_calibration_contract.v0.1.yaml`、`evaluation_sampling_design.v0.1.yaml`、`benchmark_revision_protocol.v0.1.yaml`、`evaluation_asset_classification_profile.v0.1.yaml`
- `identity_isolation/identity_capability_isolation_contract.v0.1.yaml`
- `commercial_decision_record.v0.1.yaml`、`competitive_evidence_policy.v0.1.yaml`

**CI（`ci/`）**

- `checkers/check_m2_governance_landing.py`、`check_m2_envelope_contract.py`、`check_m2_identity_isolation.py`、`check_m2_evaluation_governance.py`
- `fixtures/m2/positive/`（4 份）、`fixtures/m2/negative/`（48 份）
- `fixtures/m2/envelope_instances/`（13 份）、`fixtures/m2/identity_capability_cases/`（8 份）

**报告与回执（`11_reports_and_receipts/m2_ep01/`）**

- `m2_ep01_task_manifest.yaml`、`m2_ep01_delivery_report.md`、`m2_ep01_delivery_receipt.yaml`

**有限更新（仅状态同步与注册）**

`governance/bootstrap/role_operating_model.v0.2.yaml`（`project_state` + `parallel_execution`）、`governance/receipts/founder_signoff_receipt.yaml`（`m2_started` 授权条目 + `execution_status` 枚举）、`PRD_v1.2_change_map.yaml`（`resulting_state`）、`README.md`、`ci/run_all_checks.py`（注册表）、以及编译器重生成的 12 份投影。、`governance/baseline/founder_pinned_baseline.v0.1.yaml`（README 指纹登记，见 §6-7）。

## 3. Checker 汇总

| 项 | 数量 | 结果 |
|---|---|---|
| 确定性 Checker | 24（既有 20 ＋ 新增 4） | 全绿 |
| 判据层 fixture | 161（既有 109 ＋ 新增 52） | 161/161 按声明落 |
| M1 Schema 实例 fixture | 34 | 34/34 按声明落 |
| M2 信封实例 fixture | 13（9 负 4 正） | 13/13 按声明落 |
| M2 身份扫描用例 | 8（4 负 4 正） | 8/8 按声明落 |

新增 4 个 Checker 各自的负例夹具数：治理落盘 14、信封合同 11、身份隔离 9、评测治理 14（共 48 份 `expected=FAIL`，另 4 份 `expected=PASS`）。

**证据等级**：以上均为 `runtime_verified` —— `python3 ci/run_all_checks.py` 实跑退出码 0，逐项 PASS 与 fixture 分布见终端输出，非静态推断。

## 4. EQ-1—EQ-5 自查

| 规则 | 自查结论 |
|---|---|
| EQ-1 单一实现 | M1 产物 SHA256 只在 `m1_source_binding.v0.1.yaml` 有产出处，Profile 成员的指纹须能在绑定表里找到（`MEMBER_SHA256_NOT_FROM_BINDING_TABLE`）；禁止/允许能力清单只在隔离合同里，Checker 不重抄；隐藏边界执行委派既有实现，`DUPLICATE_HIDDEN_BOUNDARY_IMPLEMENTATION` 守住不出第二套；投影仍由既有编译器单点生成 |
| EQ-2 合同与实现一致 | 信封字段合同、三态分离、四维度、七类硬门都由 Checker 逐条断言；章程原文钉指纹，改文必改指纹 |
| EQ-3 每 checker 必有负例 | 4 个新 Checker 共 48 份 `expected=FAIL` 夹具；另有 9 份 INVALID 信封实例与 4 份必命中扫描用例。判据「有没有被行使过」本身也是判据：`ENVELOPE_WITHOUT_NEGATIVE_FIXTURE` 与 `IDENTITY_SCAN_WITHOUT_NEGATIVE_CASE` 会在负例缺席时直接 FAIL |
| EQ-4 无死代码无魔法常量 | 常量都有来源与名字：知识状态七级取自 M0 知识状态机、风险分层与校准规范名取自 `role_operating_model`、对象清单取自 M1 覆盖映射表、能力清单取自隔离合同。`in_place_modification_allowed` 留成常量字段而非省略，是为了让「不得原位修改」在每份实例上机器可读 |
| EQ-5 宁重构不打补丁 | 身份检测没有走「全文扫描 + 白名单」那条路——那条路要靠不断加例外维持，例外一多就什么也拦不住；改为限定结构化能力面，从根上消除误报来源。信封实例夹具与扫描用例都走「pure function + 用例目录」而不是在 Checker 里堆特例 |

## 5. 反自审假绿的三处安排

1. **真值独立重算**：知识状态七级枚举不从信封 Schema 自己读，而从 M0 冻结的 `knowledge_state_machine.v1.0.yaml` 取；对象清单不从层映射自己读，而从 M1 覆盖映射表取并**双向**比对；高风险覆盖与校准规范名从 `role_operating_model` 取。拿被检对象当真值，写错了也会一路显绿。
2. **判据必须被行使过**：负例缺席本身就是失败状态，不靠人记得写。
3. **豁免必须窄且可证伪**：身份 Checker 只豁免「`ci/fixtures/` 下 `checker` 字段指向它自己」的夹具——负例 payload 里必然写着能力名，那是在描述违规不是违规本身（沿用既有 `check_hidden_benchmark_boundary` 的同一条规矩）。豁免范围已实测验证：临时在产品目录与**别的 checker 的**夹具里各植入一处违规，两处都被判 FAIL，移除后恢复全绿。
4. **误报同样算失效**：身份扫描的 4 份合规用例里，两份专门放了「禁止人脸识别」这类字样的裁决文本——判据若把它们判成违规，同样 FAIL。

## 6. 未决事项（如实列出，未在本包关闭）

| # | 事项 | 处置 |
|---|---|---|
| 1 | **三层哈希机制退役未落地** | FR-CALIBRATION-004 裁定其退役，但 `check_docx_canonical_hashes` 仍在运行且为绿。退役属降低既有验收严格度，且既有 checker 与 baseline manifest 不在本包 §5 路径权限内。已在裁决文件 `three_layer_hash_mechanism.implementation_gap` 逐条记明理由与前置条件，路由至 Founder／M2 收口。**本包不称其已退役** |
| 2 | `execution_run_id` 未纳入确定性守卫 | `check_execution_uuid` 的 RUNS 只覆盖治理与 M0 两个批次，纳入需改既有 checker（不在允许更新清单）。M1-EP01 批次同样未被覆盖且未生成标识。已在 Manifest `execution_run_id_guard_status` 如实记录，路由至 M2 收口 |
| 3 | Profile 绑定为 PROVISIONAL | M1 尚未整体收口。最终绑定 + 重测属 M2-EP02（`REBIND_AND_RETEST`），本包不预先声明 FINAL |
| 4 | STORE-A 未 provision | 隐藏资产选址已定但未落地（`COND-011`）。M2-EP02 启动隐藏资产建设前须先确认 provision 完成 |
| 5 | 阈值一律未冻结 | 四维度阈值、抽样比例、校准锚点数量全部保持 `M2_FREEZE_REQUIRED`，由 Founder 在 M2 冻结时裁决（`COND-007`）。本包不代为冻结，Checker 对「标着待冻结却已填值」直接 FAIL |
| 7 | **`founder_pinned_baseline.v0.1.yaml` 不在 §5 明文清单内，本包仍改了它** | §5 把 `README.md` 列为 allowed_update，而仓库对 README 的既有机制是「任何授权改写必须同时更新 `post_change_binary_sha256` 并追加一条 `README-MOD-NN`」——不更新指纹，`check_baseline_hashes` 立刻判 `AUTHORIZED_FILE_CHANGED_AFTER_FREEZE`，README 在物理上就无法被更新。按 §5「实际路径与语义对应不一致时按语义对应执行并在报告注明」，把指纹登记视为 README 有限更新的登记动作，仅追加 `README-MOD-10` 并改该一个哈希值，未动任何其他条目、未放宽任何判据。先例：README-MOD-05—09 五次授权改写均如此。**此项提请 Guardian 与 Founder 复核**，若认定越界，撤回方式是回滚这两处改动并同时回滚 README |
| 6 | 「D-09」无仓库锚点 | 启动包称三件套为「D-09」，但仓库内不存在 D-09 这一编号（既有裁决只到 D-29 且无 D-09）。按语义对应落到 M2 冻结 Brief 第 2 节第 8/9/10 项，未凭空创造 D-09 裁决 |

## 7. 熔断与停止条件

本包**未触发**任何停止条件。M1 顶层对象、核心语义、七级事实优先级与品类合同均未改动——只新增引用层，未打开任何 M1 Schema 文件写入。`ep01_forbidden_outputs` 九类禁止产出一件未产。

## 8. 边界纪律

全程未读写原仓库工作目录 `/home/faye/笛语跨品牌服装搭配专家内核`（M1 正在其中执行）；全部取数经 git 对象库从 `signed_baseline_commit` 检出。本包停在 `candidate/m2` 等待指令，未启动 M2-EP02，未发起 Guardian／总顾问单独审查。
