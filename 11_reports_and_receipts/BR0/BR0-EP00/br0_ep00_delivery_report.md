# BR0-EP00 交付报告｜启动准备包

> 本报告是模板渲染产物。每一个计数数字都由 `ci/tools/render_report.py` 从机器记录现读，
> 不由人手抄。改数字只能去改台账——改报告本身会被 `check_report_number_traceability` 当场判 render drift。

**候选 Commit**：见 `br0_ep00_delivery_receipt.yaml` 的 `candidate_commit`（落盘时无法自指，由 `git rev-parse HEAD` 复算）
**基线 Commit**：a5564e1a4455b6521ae3c5e0b15385052c86c867
**结论**：PASS

---

## 一、本包做了什么

把仓库从「规划完成但不可安全施工」转成「可以开始 BR0-EP01 真实 Runtime 施工」。
不是产品开发，不是 Runtime 实现，不是治理扩建。判断标准只有一条：**能阻塞 BR0-EP01 的问题处理，不能阻塞的延期。**

两份执行 Prompt（v0.2 与最终收敛版）的要求项已取并集落盘，口径冲突逐条记录在
`01_contracts_and_schemas/branch_baseline.v0.1.yaml` 的 `prompt_merge_record`。
后发 Prompt 未提的要求（反向注入、单一报告树、派发纪律、ADR 分类）一律保留执行——未提不等于取消。

---

## 二、基线与 M2 边界

| 维度 | 值 |
|---|---|
| main 基线 | `a5564e1a4455b6521ae3c5e0b15385052c86c867` |
| candidate/m2 | `64530031c0d0fcbc82ee77e1487e41c8661c0298`，状态 SUSPENDED_REFERENCE |
| 复用方式 | SELECTIVE_BACKPORT（逐个评估后单独迁入，不整支合并） |

candidate/m2 只用 `git show candidate/m2:<path>` 读取，未 merge、未 cherry-pick、未建工作树。

**判据差集共 28 个，逐个归类：**

| 类 | 数量 | 处置 |
|---|---|---|
| A 类 | 3 | 本包迁入并接入 CI |
| B 类 | 7 | BR2 收口时逐个重评 |
| C 类 | 18 | 不迁入（M2 评测基座自身对象） |

**M2 ADR 共 6 份，只分类不搬运：**
已验证通用原则 → 迁移 4 份（ADR-002 / 003 / 004 / 006）；
未来参考 → 保留 2 份（ADR-001 / 005）；
已过时 → 废弃 0 份。

ADR-003 的租户条款单条废弃：它写「多租户隔离实现延后、scope 字段只记录不驱动隔离」，
而 v0.3.2 的 D-TENANT-DAY1 要求每张客户表建表第一天就带 `tenant_id NOT NULL`，
并明文禁止「为既有客户表批量补 tenant_id」的大迁移。两者不可并存，必须在 BR0 判掉。

---

## 三、README 单一真源修正

删除「## 当前项目状态」下整段 yaml 状态块（25 行），替换为一行：

> 当前状态以 `PRD_v1.2_change_map.yaml` 的 `resulting_state` 为准。

**为什么删得掉**：这段状态块没有任何判据读它。`check_project_state` 只把 README 当违禁措辞的扫描面，
它的 flags 全部来自 `PRD_v1.2_change_map.yaml`、`role_operating_model.v0.2.yaml`、
`baseline_reconciliation_receipt.yaml` 三处。它是第四份未受守护的重复副本。

**承重串逐字保留**（删掉即 `check_active_product_truth` 报 DUAL_ACTIVE_PRODUCT_TRUTH）：

```
| `笛语跨品牌服装搭配专家内核_PRD与执行里程碑_v1.2.docx` | 产品合同、范围、里程碑与验收门 | **当前活基线 · `SIGNED`** |
```

未新建任何状态文件。AC-10 的口径是 `readme_no_longer_carries_state`，**不是** `source_of_truth_unique`——
状态真源本有三处，合并它们属扩张，本包不做。

hash pin 已同步到 `governance/baseline/founder_pinned_baseline.v0.1.yaml`
的 `active_baseline_candidates[README.md].post_change_binary_sha256`，并在
`authorized_modification_history` 留 README-MOD-12 一条。

---

## 四、CI 阻塞修复

`secret-and-hidden-boundary` 的「Real brand / customer data boundary」步骤从**中文业务词扫描**
改为**真实泄露模式扫描**。

改造前扫 `真实顾客档案 / 真实库存快照 / REAL_CUSTOMER_RECORD`。已实测复现：
一句正常的业务描述「InventorySnapshot 表示某一时刻的真实库存快照」当场判红。
main 目前没有业务源码，所以这条误阻塞还没发作——BR0-EP01 写下第一行领域代码它就会发作。

继续检测：API Key、Secret、Private Key、Access Token、真实手机号、身份证号、真实客户文件路径、STORE-A 凭证。
不再检测：商品事实、库存快照、品牌规则、商品池、用户画像模型字段。

同一文件的 `Secret pattern scan` 步骤检测内容一字未改，只把模式串提到 job env 供自测复用（单一定义处）。

新增 `Leak detector self-test` 步骤：每次 CI 都在仓外临时目录里种下
9 条已知泄露与
6 条正常业务措辞，双向自证。
检测器换了尺子却抓不住真凭据，等于把 M1「假绿」教训再丢一次。

---

## 五、治理资产迁移

只迁三个，且各自把依赖树补齐——它们在 main 上原本一个都跑不起来。

| 判据 | 补齐的依赖 |
|---|---|
| `check_report_number_traceability` | `ci/tools/render_report.py`（main 无 `ci/tools/` 目录）＋ 报告编号绑定登记册 |
| `check_founder_confirmation_binding` | `_common.clause_resolves` ＋ Founder 确认绑定登记册 |
| `check_collect_derivation_discipline` | 字面量登记册（标准库 `ast`，无其他依赖） |

`_common.py` 只补了 `clause_resolves`。m2 上另有 `extract_ruling_id` 与 `founder_ruling_evidence`，
逐个确认后**没有一个**被 A 类判据使用——迁进来就是死代码（EQ-4），因此不迁。

判据源码逐字未改。三份登记册按 main 实测重建：m2 的登记册登记的是 M2 对象，直接搬过来会全线 MISSING。

**`check_collect_derivation_discipline` 上线当场扫出 8 处硬编码事实源，
全部整改，剩余 0 处。** 没有一处以「尺子」名义登记——判断标准只有一条：
这个值是对世界的测量，还是合同给的期望值。八处全是前者。

整改当场暴露两处从未被发现的既存错误：

1. `check_task_classification` 把 GPT_CHIEF_ADVISOR 写成 `available: True`，
   而签署回执明写「ChatGPT 执行侧持续连接故障」并按记录性豁免处置。
2. 同一判据的处置词表写 `EXPLICITLY_WAIVE_WITH_RISK_ACCEPTANCE`，回执记的是
   `EXPLICITLY_WAIVED_WITH_RISK_ACCEPTANCE`。分支从未被执行过，词表错位一直没人发现。

`check_founder_confirmation_binding` 扫出 56 个 Founder 确认位，
其中 13 个是「声称 Founder 做过某动作且值为真」，逐个绑定到既有裁决文件、
签署回执或基线 Manifest 的具名条款——条款路径现场解析，凭空写的路径解析不出来。
**未新建任何 Founder Decision 格式**，绑定一律指向既有 `governance/founder_rulings/*.yaml` 与回执。

判据总数 21 → 24；
夹具 156 份全部按声明行为，结构层夹具
36 份同样全绿。

---

## 六、复用边界与执行模板

附录 A 由 14 行补至
28 行，覆盖两份 Prompt 点名的全部组：
ProductTruth、Inventory、Tenant、Persona、Platform Profile、Publication Policy、Compliance、
Knowledge State、Non-goals，以及跨品类冲突优先级与三份视觉资产。

**Tenant 组不进本台账**（EP00-FIX R-02）。本仓 M0/M1 没有独立的 Tenant 合同——租户根是
D-TENANT-DAY1 在 BR1 新建的对象。首版曾把 `architecture_and_integration_boundary.v1.0.yaml`
当 Tenant 组登进去，那是归类错误：它是架构与集成边界，不是 Tenant 合同，留在表内会让下游
误读成「有 Tenant 合同可复用」，已删除。Persona 组的另外三份（人设记忆快照 / 人设冲突记录 /
系列连续性状态）保留——C-13 人设五对象的真实成员，BR4-EP01 会消费，漏登成本高于多登。

`01_contracts_and_schemas/pinned_reuse_ledger.v0.1.yaml` 共
28 条，逐条含 `asset` / `source_path` / 四十位 `source_commit` / `file_sha256`。
commit 不是 file hash 的替代：commit 说明当时仓的状态，说明不了这个文件的字节。

`execution/templates/` 两份模板 ＋ `execution/dispatch_discipline.md` 一页派发纪律。
未建执行包数据库、执行管理后台、自动生成系统、Receipt 平台——执行包是文件，不是服务。

`environment_class` 取值域固定为 G / Z / L / S / V / P。首版落盘时六个字母的语义在仓内、
PRD v0.3.2 与执行规划 HTML 均查无定义，模板标的是占位符而**不是编造的含义**。
EP00-FIX 中 Founder 已确认六行定义，落 `execution/README.md` 的枚举定义节，模板同步取真值，
占位符全仓归零。BR0-EP00 自身运行在 **G**（治理/仓库环境）：只动合同与文档，
未起任何服务、未建数据库、未接任何 Provider。

---

## 七、验证

全量 `python3 ci/run_all_checks.py` EXIT=0。

**AC-05 反向注入**（本包唯一「多花力气」的一条）：把本报告里的一个数字改一位，
`check_report_number_traceability` 立刻判 REPORT_RENDER_DRIFT；恢复后 PASS。
理由是 M1 期发生过「女装判据假绿」——判据在，喂它恒假值，CI 全绿。
迁一个判据过来却不验证它在守东西，等于把那次教训再丢一次。

### unreviewed_commits（R-01 补偿动作）

Founder 裁决 R-01：`commit_events` 保持守「旧结论被当作仍然有效」，不改为守「HEAD 尚未被
Guardian 审过」。理由是仓内仅三份 Guardian 审查报告且全部是 M0 时期的，B 版语义会让 CI 长期常红，
而常红的 CI 等于无 CI；Guardian 审查是里程碑级动作，不是每 commit 动作。

作为补偿，这里如实列出自 `c3f6ad3` 起**未被任何 Guardian 审查报告覆盖**的提交：

| Commit | 内容 |
|---|---|
| `947de26e19951f906f5379e9e604264810856905` | PRD v0.3.2：规范化落盘 TBD-16 十例 Founder 内容优越性案例 |
| `11efc1be8dd8e5676fccacfed312e3e2c5eed31e` | 归档支线 v0.3 历史文档：v0.3.1 候选与 v0.3 设计输入入库 |
| `a5564e1a4455b6521ae3c5e0b15385052c86c867` | 修正 v0.3.2 四处交叉一致性漂移 |
| `91173113584978dc80b16975b9f5b5efab368029` | BR0-EP00 启动准备包 |
| `eddbcd15243976c8b846a8f3690f0213d94662c2` | BR0-EP00 候选哈希回填 |

EP00-FIX 自身的提交同样未被覆盖——它就是承载本节的那个提交，落盘时无法自指。

仓内现有 Guardian 报告只有三份，覆盖 `f48fed3` / `9335180f` / `f01e45b`（delta），全部是 M0 时期。

**这一节是信息记录**：不实现为红灯，不实现为判据，不进 `ci/run_all_checks.py`。
它的作用是让「哪些提交没被审过」这件事有地方查，而不是让 CI 常红。
Guardian 审查按里程碑节奏进行——下一次就是本包的 PR。

---

同样做了反向注入验证的还有两处新推导：
把签署回执 `round_1.valid_for_signature_base` 翻真，`GUARDIAN_REVIEW_NOT_REDONE` 当场触发；
往裁决目录塞一份接受纯 Prompt/RAG 直答的裁决，`M6_ANTI_DEGENERATION_VIOLATED` 当场触发。
两处都在验证后恢复原状。

---

## 八、明确延期

延后到 BR1：Error Taxonomy 机器化、Human Review 边界、Mock/Real 详细合同。
延后到 Runtime Skeleton：ECS 部署拓扑、数据库 migration 规范细节。
延后到后续：Stop Conditions 扩展、商业反馈闭环、Pilot 相关内容。

PRD v0.3.2 已有的内容不重复创建。

---

## 九、交接给 BR0-EP01

BR0-EP01 就是 Runtime Skeleton。v0.2 里的「BR0-EP01 合同收敛与复用边界」已整包并入本包，
EP01 这个编号让给 Runtime Skeleton。

强制 DoD 三条（写入 `branch_baseline.v0.1.yaml` 的 `handoff_to_br0_ep01`）：

1. **功能验证能力必须存在**：pytest 骨架 ＋ 针对 `/healthz` 与首个 migration 的真实测试，接入新 workflow。
   理由：本包交付后 main 上的判据全部读 YAML / DOCX / Markdown，对运行时代码结构性失明。
   不加这一条，BR0 之后「CI 全绿」关于功能正确性仍然一个字也没说。
2. **首次 migration 让所有客户表 `tenant_id NOT NULL`**，品牌域表带 `(tenant_id, brand_id)` 复合外键。
   不要求全表 RLS；禁止先建表后批量补。
3. **不得机械扩张 `brand_id`**：Tenant / TenantMembership / Tenant 级 Settings /
   无品牌语义的 Tenant 级审计事件一律不加。

执行合同按本包候选 Commit JIT 编译，不得提前冻结。

---

## 十、条件状态

首版三条条件，Founder 已在 EP00-FIX 中裁掉两条：

| 条件 | 状态 |
|---|---|
| COND-01 commit_events 守护对象 | RESOLVED_BY_FOUNDER_RULING（R-01，保持 A 版 ＋ 本报告 unreviewed_commits 补偿） |
| COND-02 waiver_timestamp 来源 | RESOLVED_BY_FOUNDER_RULING（R-04，标 `derived_from_signed_at`，签署回执未动） |
| COND-03 启动裁决书 | **CLOSED**——Founder 已于 2026-08-15 签署《BR0 启动裁决书 v0.1》 |

三条全部关闭，本回执不再挂任何未决条件。本包结论：**PASS**。

### 裁决落盘方式

`DIYU-CBFSK-FOUNDER-BR0-START-001`，YAML 原文由 Founder 直接给出，执行侧**逐字落盘**，
未新增、未扩张、未解释性改写任何一条。六条 `article_1`…`article_6` ＋ `scope_freeze_rule`。

原文送达前，执行侧曾按 Founder 确认的草案落过一份 A1—A5（措辞由执行侧起草，明标非 Founder 原文）。
**原文一到即整份删除，不保留、不并存**——同一份裁决两份并存，下游就分不清哪份是真的。
两者实质一致，逐条对齐记录在 `branch_baseline.v0.1.yaml` 的 `ruling_alignment`。

### 六条裁决落在哪

| 条 | 落点 | 状态 |
|---|---|---|
| `article_1_baseline` | `baseline_commit` / `runtime_base_branch` | ALIGNED |
| `article_2_candidate_m2` | 仅 3 个判据回迁，其余 25 个（B 类 7 ＋ C 类 18）留 `deferred_items` | ALIGNED |
| `article_3_readme` | EP00-02 已交付：删整段状态块，保留 hash pin 与活基线 marker | ALIGNED |
| `article_4_secret_boundary` | EP00-03B 已交付：业务词扫描 → 真实敏感信息检测 | ALIGNED |
| `article_5_m2_adr` | 暂停维护、分类留档——六份 ADR 一份都没复制到 main | ALIGNED |
| `article_6_br0_ep01` | `decision: AUTHORIZED`，前置「回执 PASS 且 PR 合并入 main」 | 前置未满足 |

`article_2` 说「其余 25 个留 deferred_items」；本仓把它们再分成
B 类（BR2 收口逐个重评）与 C 类（支线不恢复 M2 评测基座）。那是**怎么 defer** 的细化，
不是改动裁决——一个都没迁入。

### 签署关掉了什么、没关掉什么

| | |
|---|---|
| **关掉** | `entry_blocker` 解除；`scope_freeze_rule` 转 `EFFECTIVE`；BR0-EP01 判 `AUTHORIZED` |
| **没关掉** | PR #4 合并 main（`article_6` 前置第二项，当前 NOT_MET）；Guardian 审查；BR0-EP01 开工 |

授权 ≠ 前置已满足 ≠ 可以开工，三件事是三道门。

## 十一、之后的顺序

1. ~~Founder 签《BR0 启动裁决书 v0.1》~~ **已完成** → COND-03 关闭、`scope_freeze_rule` 生效
2. Guardian 审 PR #4 → Founder 批准后合并 main（`article_6` 前置第二项）
3. 基于合并后的 candidate_commit，JIT 编译 BR0-EP01 Runtime Skeleton
   （`br0_ep01_requirements` 强制三条：pytest ≥1 真实测试 / 首次 migration `tenant_id NOT NULL` / JIT 不提前冻结）

本 PR 标题注明「待 Guardian 审查，勿合并」，执行侧不自行合并。

**范围已冻结**（`scope_freeze_rule.effective_from_this_ruling: true`）：此后新发现一律进 `deferred_items`，不回改本包、不新增子任务。
Guardian 审查提出的缺陷修复不受此限——修缺陷不是扩范围。
