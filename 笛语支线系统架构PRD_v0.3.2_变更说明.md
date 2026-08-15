# 笛语支线系统架构 PRD v0.3.2 · 变更说明

> 状态 `FOUNDER_REVIEW_CANDIDATE`｜完整替代 v0.3.1｜基准日期 2026-08-15
> v0.3.1 保留为历史候选，不原位覆盖。未经 Founder 签署，本文件与 v0.3.2 均不构成生效产品真源。

## 〇、支线文档入口

本文件同时充当支线 PRD 的版本入口。仓库根 `README.md` 未改动——它被 `governance/baseline/founder_pinned_baseline.v0.1.yaml` 钉了哈希，加入口需要重钉哈希并追加 `README-MOD` 记录，属独立治理动作，Founder 已裁定本轮不做。README 入口待单独授权后补。

| 文档 | 用途 | 状态 |
|---|---|---|
| `笛语支线系统架构PRD_v0.3.2.docx` | 支线运行时的产品与工程合同（当前候选） | `FOUNDER_REVIEW_CANDIDATE`，**未签署、未生效** |
| `笛语支线_v0.3.2_阶段里程碑与执行包规划_Rev2.html` | 阶段、里程碑与执行包规划（单文件、无外部依赖、可打印） | 规划窗口输出，本轮原样收录，仅按 Founder 指示对齐 PRD 裁决口径 |
| `归档_支线v0.3/笛语支线系统架构PRD_v0.3.1.docx` | 上一版候选 | 历史候选，保留不覆盖；已归档并纳入 Git 跟踪（v0.3.2 的构建来源，保留才可复现） |
| `归档_支线v0.3/笛语支线系统架构PRD_v0.3_Draft.docx` | 历史 v0.3 设计输入 | `SUPERSEDED_HISTORICAL_DESIGN_INPUT`；`authoritative=false`、`runtime_dependency=false`；已归档并纳入 Git 跟踪 |
| `归档_支线v0.3/README.md` | 支线归档说明 | 说明该目录不属于主线 `归档_v1.x/` 的治理链路，不改变任何主线状态位 |

支线 PRD **不是产品真源**，也不改变主线状态位——PRD v1.2 仍是唯一活基线，M0/M1 冻结资产与 M2 状态本轮零改动。

---

## 一、为什么修订

v0.3.1 已经把内容从「Decision Truth 的附庸」提升为主产品，但同时又堆出一套内部评分体系——三张评分卡、四个参赛臂、内容硬门、Rubric、Content Battle Score、Calibrated Prediction 启用门——内容主产品被内部评分重新绑架。同时暴露另外两个结构问题：多品牌 Pilot 缺少正式、轻量、正确的多租户数据边界；测试矩阵有再次异化为项目完成度量表的趋势。

本轮**只**解决这三个结构问题，不新增运行时代码、不做数据库迁移、不扩建测试资产、不开新一轮治理工程。

---

## 二、三项 Founder 决定

### 决定 A｜商业结果主导，评测退回约束和路线实验

用户购买的是「专业搭配决策 ＋ 平台原生内容制作交付包」。内部评测只负责防止系统制造重大错误、支持路线选择和定位退化，**不承担证明产品有商业价值的主职责**。产品是否成立，最终由客户接受、实际发布、编辑负担、复购付费和真实内容表现证明。

### 决定 B｜首版实现最薄多租户数据面，永久不做 Billing

```yaml
tenant_mode: POOLED_MULTI_TENANT_DATA_PLANE
customer_self_service_enabled: false
billing_enabled: false
subscription_enabled: false
payment_enabled: false
public_platform_enabled: false
same_tenant_cross_brand_enabled: true
cross_tenant_task_enabled: false
```

多租户是**数据隔离和授权边界**，不是 Billing，也不意味着首版建设 SaaS 平台。

### 决定 C｜测试矩阵改为风险场景登记册

「测试矩阵」「内容测试矩阵」「场景覆盖矩阵」统一收敛为 **Risk Scenario Registry｜风险场景登记册**。测试数量、矩阵单元数量、矩阵覆盖率、代码覆盖率、Fixture 数量、Checker 数量和场景目录完整率，均不得独立构成里程碑 PASS 条件，也不得作为项目成功 KPI。

---

## 三、主要替换关系

| v0.3.1 结构 | v0.3.2 结构 | 落点 |
|---|---|---|
| Professional Capability Scorecard、Operational / Business Scorecard、Content Production Capability Scorecard、内容硬门、Rubric | **一门**：Delivery Safety Gate（只判 `PASS` / `BLOCK`，DSG-01～DSG-13） | 16.1、16.2、8.14 FR-1401/1402 |
| 三张评分卡中的商业与运营指标 | **一表**：Commercial Outcome Ledger（接受、发布、编辑负担、复购、付费证据 + 平台深度指标） | 16.1、16.3、8.14 FR-1403/1404 |
| 四个参赛臂「每次运行」 | **一次实验**：Capability Route Experiment（P-only / C-lite / D-full / H，四类触发条件之一成立才运行，否则 `NOT_RUN`） | 16.1、16.4、8.14 FR-1405～1409 |
| Content Battle Score（正式总分 / 发布门 / 商业预测） | **Preflight Content Signals**（仅候选相对排序与弱点提示，无总分、无阈值、非发布门） | 16.7、8.14 FR-1411、AOE-10 |
| Calibrated Prediction 启用门（V1 里程碑） | **移出 V1 → FUTURE ADR**；不保留训练里程碑、Feature Store、MLflow、在线训练、自动调参、实时预测 API 或独立发布门 | 16.8、8.14 FR-1412、13.4、20.2 |
| 「首版仍是单组织，不建设 SaaS Tenant 管理」；`brand_id` 承担隔离 | **`tenant_id` 为安全根**：Tenant / TenantMembership / TenantContext / tenant-scoped RBAC / 三层隔离（Repository → 复合外键 → RLS） | 4.4、4.5、10.5、10.6、8.1 FR-107～114、8.2 FR-213/220/221 |
| 「至少三个品牌 Pilot」 | **2 Tenant / 3 Brand 拓扑**：Tenant A 含 Brand A1/A2 且允许同租户跨品牌；Tenant B 含 Brand B1，与 A 完全隔离 | 5.6、5.9、5.10、18.2 BR7、3.3 |
| 17.4 P0 高压端到端与内容测试矩阵 | **17.4 风险场景登记册**：`RiskScenario` 字段化 + RS-* 具名 P0 场景 + 发布阻断规则 | 17.4、17.3 G8、AOE-03/AOE-14 |

---

## 四、保留的能力（未回退、未删除）

`ContentProductionPackage`、「3+1」内容制作交付包、`NarrativeTypeRegistry`、`ContentStyleProfile`、`PlatformGrammarProfile`、`HookPatternLibrary`；小红书 / 抖音 / 视频号 / 公众号的差异化内容语法；三个开场钩子或标题候选；文案、脚本、镜头、字幕、配图逻辑与商品引用；脚本—镜头—SKU 对账；平台原生而非同稿换词；人设连续性；商品事实与库存变化向内容资产传播；评论互动问题、预期质疑与官方回复模板；人工审核；结构化导出；发布指标回传；反馈不得直接改写真源。

专业决策真源（Decision Bundle / DecisionTrace）作为内容的必要前提**未被反向删除**；上传归一化、库存快照、ECS 冷部署与恢复、视觉投影等能力原样保留。

---

## 五、删除或降级的内容

- **删除**：三张评分卡结构、内容评测协议（`content_evaluation_protocol`）、Content Battle Score 的两阶段实现与其发布门、Calibrated Prediction 的 V1 启用门与样本门、「轻量战力模型」的 P1 训练路径（scikit-learn / calibration）。
- **降级**：Content Battle Score → Preflight Content Signals（辅助信号）；四参赛臂 → 一次性实验定义；`ContentBattleMode` 枚举 → `PreflightSignalMode`（唯一值 `RELATIVE_RANKING_ONLY`）。
- **改判**：D-4、D-6 两条建议默认；新增 NEW-03（薄多租户）、NEW-04（风险场景登记册）、NEW-05（信号降级与预测移出）。
- **不新增**：运行时代码、数据库 migration、RLS SQL、Tenant API 实现、Checker、Fixture、测试框架、评测平台、YAML 真源、状态机、审批链、角色体系、Billing / Quota / Subscription / Payment、Tenant Console、Evaluation Console、Feature Store、ML 平台、多租户微服务、Kubernetes、通用工作流引擎。

---

## 六、追加轮：历史 v0.3 有界吸收、界面分期、内容血缘与发布核对收敛

### 6.1 历史 v0.3 的地位

历史《笛语支线系统架构与产品需求文档 v0.3》（仓库内 `笛语支线系统架构PRD_v0.3_Draft.docx`）在 §0.2 来源优先级中登记为第 6 优先级：

```yaml
status: SUPERSEDED_HISTORICAL_DESIGN_INPUT
authoritative: false
runtime_dependency: false
```

**已吸收**：草图 B/C/A/D 的交互语义（事实缺口前置、Unknown 不给猜测入口、候选并列不放大成唯一答案、Trace 抽屉不暴露密钥、编辑即时显示事实边界、REWORK 必选范围与原因）；§8.7 通用交互规则（状态不只依赖颜色、长任务、危险动作、错误、版本、WCAG 2.2 AA）→ 落在 12.2；附录 A 场景种子 → 落在 17.4；附录 E 一页核对思想 → 落在附录 H。

**明确未吸收**：旧技术栈、R0–R6 里程碑体系、三套记分卡、评测臂常驻运行方式、旧角色体系、旧多租户口径与 `workspace_id` 安全根、旧 Measurement 章节、旧 Billing/平台化/公开 API 表述、草图 E 盲评（只属能力路线实验，不进核心导航）。全文不出现「详细设计见历史 v0.3」——被采纳的语义一律在 v0.3.2 中重新表达。

### 6.2 六张核心界面草图与分期（§12.3）

阶段字段一律使用本 PRD 唯一路标 BR0–BR8，且 `first_required_at` 等于该能力在 §18.2 中真实首次可用的节点（Founder 裁定：钉到能力真实首次可用的 BR 节点，不引入第二套路标；BR 形态在第三轮被重新定义后，本表已随之回改）：

> 下表为**第三轮重切后的最终阶段**（第二轮的旧值与取代理由见 §8.4）。

| screen_id | first_required_at | 说明 |
|---|---|---|
| UI-01 创建任务向导 | BR1（EP01） | BR2 补同租户多品牌的 TaskBrandBinding 选择 |
| UI-02 候选比较与 DecisionTrace | BR1（EP03） | BR3 补齐替代方案、无解解释与完整取舍链 |
| UI-03 平台原生内容工作台 | BR1（EP04） | `minimum_platform_scope_at_BR1` = 视频号单平台完整垂直切片；`additional_platforms: DEFERRED 至 BR4` |
| UI-04 生产工作台与任务列表 | BR2（完整形态） | BR1 起必须有极简任务索引，但不建仪表盘 |
| UI-05 审核与定向返工工作台 | BR4（独立完整形态） | BR1-EP04 起在内容工作台内提供最小人工审核；BR6 补 Evidence 关联 |
| UI-06 发布表现与商业结果表 | BR7 / PILOT | 真实数据出现前不建空仪表盘；`surface_mode: READ_ONLY` |

每张均带 `screen_id / first_required_at / minimum_scope_at_stage / deferred_elements / non_goals`，配一张低保真布局（4 张沿用既有草图，UI-03/UI-06 用等宽 ASCII 布局）、一段最小交互合同与关键停止/恢复行为。不交付 Figma、高保真视觉稿、设计系统、组件库或动效原型。

### 6.3 商业结果只读边界（§16.3、FR-1113、NFR-BIZ-02、AOE-16）

`commercial_outcome_surface` 九个开关全部为 `false`/`READ_ONLY`。四类禁止回流被逐条点名（完播率低→阻止发布、点击率低→降候选、互动率高→改平台语法、商品点击高→提权重）。唯一允许的未来链路是「Evidence → 人工分析 → 提案 → Founder 批准 → 新版本 → 风险场景验证 → 后续版本启用」，且不得为它提前建反馈服务、训练平台或自动权重系统。

### 6.4 内容资产血缘（§10.7，BR1 P0 数据合同）

`ArtifactLineage` 14 字段落入数据字典；内容制作资产六个必填字段（`artifact_id`、`artifact_revision_id`、`source_decision_revision_id`、`source_product_refs`、`platform_grammar_version`、`generation_manifest_id`）随内容同事务写入。节点级 `ContentNodeRef` 覆盖标题/Hook/正文段/脚本段/镜头/字幕/CTA。实现方式固定为「关系型顶层外键 + 版本化 JSONB 节点引用」；不建图数据库、Lineage Service、DAG、Event Sourcing 或依赖图 UI。落点覆盖数据字典、FR-821～823、9.3 返工路由、8.12 导出 Manifest、18.2 BR4、17.2 DoD 与 17.4 风险场景 RS-LINEAGE-01。

> 阶段口径取代记录：第二轮我按 Founder 裁定「钉到能力真实首次可用的 BR 节点」把血缘落在 **BR4**，前提是当时的 BR1 里没有内容生成。第三轮追加指令把 BR1 重新定义为完整垂直切片（`BR1-EP03` 含三候选与 DecisionTrace，`BR1-EP04` 含首平台内容编译、审核与导出），该前提不再成立。按「冲突以最新 Prompt 为准」，血缘回到 **BR1 P0（BR1-EP04）**，界面草图阶段同步回改（见 §八）。这是前提变更导致的正当取代，不是静默翻转；实质要求（生成当场写入、不靠事后反推、不是界面增强、不是 Pilot 分析功能）自始未变。

### 6.5 风险场景迁移与一页核对（§17.4、附录 H）

历史 AC-01/02/03/05/06/07/08/11/12/13 以语义迁移进 Risk Scenario Registry，保留 `historical_source_ref: v0.3/AC-xx` 供追溯；当前场景 ID、前置条件与预期不变式一律以 v0.3.2 为准。AC-15 盲评只属能力路线实验，AC-14 STORE-A 只保留隔离边界断言。新增附录 H《Pilot / Release Readiness One-Pager》：`maximum_top_level_rows: 12`、`row_change_authority: FOUNDER_ONLY`，每行只有 `check / status / evidence_ref / owner / checked_at`；新风险默认进登记册，不得自动增第 13 行，也不得用子表、脚注或证据森林把 12 行伪装扩张。

### 6.6 信息架构

核心导航固定为「任务 / 商品与品牌 / 内容制作 / 审核与交付 / 设置」，PILOT 后增加只读的「商业结果」。Capability Route Experiment 不进入客户核心导航，未激活时不建设页面。

---

## 七、当前状态

```yaml
document: 笛语支线系统架构PRD_v0.3.2.docx
status: FOUNDER_REVIEW_CANDIDATE
supersedes: 笛语支线系统架构PRD_v0.3.1.docx   # 保留为历史候选，未原位覆盖
signed: false
merged_to_main: false
release_tagged: false
main_baseline: c3f6ad372306cc12f139cf38624e9a5cea2cf329   # 未改动
```

v0.3.2 只有在 Founder 明确签署版本、日期、D-1～D-6 与 NEW-01～NEW-05、以及 TBD-01～TBD-14 的处理结果后，才成为支线产品与工程实施基线。未经签署，所有 `[PRD]` 条款均为建议。本轮不修改主线 M0/M1 冻结资产、M2 候选、STORE-A、隐藏评测资产或任何主线状态位。

---

## 八、第三轮追加：BR1 零代码穿刺、Day-1 租户边界、并行纪律与渐进式结果记录

### 8.1 BR1-EP00 Founder 零代码内容穿刺（新增 §18.6）

在 BR0 之后、任何 BR1 运行时代码施工之前，先由 Founder 在现有聊天窗口里人工产出一份真实内容制作交付包。它是 BR1 的 Entry Package，不是里程碑，不产生代码 Commit。

```yaml
execution_package_id: BR1-EP00
duration: 1-2 working days
code_changes: prohibited
database_changes: prohibited
formal_benchmark: prohibited
max_manual_iterations: 2
```

执行顺序固定为 `BR0 → BR1-EP00 → Founder Verdict → BR1-EP01 → EP02 → EP03 → EP04`。Founder 判断只有 `YES / CONDITIONAL / NO`，可附不超过五条差距说明，不得形成评分体系。EP00 不是客户付款证明、不是市场验证、不是能力评测，也不冻结 Schema——**在没有看过 EP00 实际输出之前，不得把完整 `ContentProductionPackage` Schema 视为已冻结**（AOE-17）。

### 8.2 Day-1 租户安全根（§10.5、AOE-18 相邻条款）

正式合同：所有客户所有权数据表，从第一次创建起必须含 `tenant_id NOT NULL`；禁止先建无租户表、再在 BR2 或 Pilot 跨几十张表补列。列名下限 22 项（Brand … Job），新增客户表一律适用。品牌域必须从首次建表起保证 `FOREIGN KEY (tenant_id, brand_id) REFERENCES brands (tenant_id, brand_id)` 或同等复合键。**不得机械扩张**：Tenant、TenantMembership、Tenant-level Settings 与无品牌语义的租户级审计事件不带 `brand_id`。

- **BR1 最小边界**：服务端产生的 TenantContext、BR1 所用查询的租户作用域、`tenant_id NOT NULL`、品牌复合外键、对象存储租户前缀。BR1 不要求全表 RLS。
- **BR2 职责**：统一 Tenant-scoped Repository、RLS、Audit/Queue/Cache/Export/签名 URL 完整作用域、2 Tenant 3 Brand、同租户跨品牌、跨租户阻断、多品牌规则冲突语义。**BR2 不重新设计 Tenant 根，也不执行批量补 `tenant_id` 的大迁移**。

### 8.3 并行纪律与日历非承诺（§18.2、§18.3）

`dependency_parallelizable ≠ same_worktree_concurrent_execution`。默认 `execution_mode: SERIAL`，`same_worktree_concurrent_write: prohibited`。真并行需同时满足独立分支、独立 worktree、路径不重叠或显式冻结、公共合同已冻结、单一集成/迁移/锁文件 Owner、单一集成窗口、公共合同变更后基线刷新。数据库 migrations、领域 contracts、公共 Schema、Task/Run 状态机、公共枚举、依赖 lockfile、全局配置与部署入口默认禁止并发编辑。不建设 Worktree 调度平台、Agent 协作平台、分支编排服务或自动冲突仲裁系统。

20–24 周标注 `binding: false`、`capacity_assumption: backend 2 / frontend 1 / product_design_qa 1`，明确是四人容量参考情景，不是 Founder ＋ AI 形态下的交付承诺。

### 8.4 里程碑重切与界面/血缘阶段回改

§18.2 重切为九个里程碑，BR1 成为首条商业垂直切片（EP00 ＋ EP01～EP04）。据此，第二轮钉出的界面与血缘阶段同步回改：

| 对象 | 第二轮（旧 BR 形态） | 本轮（新 BR 形态） |
|---|---|---|
| UI-01 创建任务向导 | BR2 | **BR1**（EP01 起即为施工要求；BR2 补多品牌绑定） |
| UI-02 候选比较与 DecisionTrace | BR3 | **BR1**（EP03 最小形态）；BR3 补齐替代与无解 |
| UI-03 平台原生内容工作台 | BR4 | **BR1**（EP04 单平台切片）；BR4 扩多平台 |
| UI-04 生产工作台与任务列表 | BR4 完整 | **BR2 完整**；BR1 起极简任务索引 |
| UI-05 审核与定向返工 | BR6 独立 | **BR4 独立**；BR1-EP04 起最小审核 |
| UI-06 商业结果面 | BR7 / PILOT | 不变 |
| ArtifactLineage | BR4 P0 | **BR1 P0（EP04）** |

### 8.5 创意方向结构门（FR-824～826）

新增 `CreativeDirectionSignature`（narrative_type / audience_scene / primary_selling_point / emotional_curve / tradeoff）。三个方向不得只是标题、措辞、Emoji、语气或句序变化；每个方向必须有可命名的核心差异；整组至少在叙事类型、受众场景、卖点排序、情绪曲线、商品角色中的两个维度上形成差异；每个方向必须回答「选择这个方向，意味着放弃或弱化什么」。**这是可人工阅读的结构门，不是新评分卡**——不加多样性综合分、向量距离门槛、聚类服务或覆盖率 KPI。

### 8.6 Provider 调用成本 Day-1 落盘（FR-611～613、§11.3）

自 `BR1-EP03` 第一次真实 Provider 调用起，每次 `ModelCall` 记录 provider / model / operation / input_tokens / output_tokens / total_tokens / cached_tokens / latency_ms / estimated_cost / currency / pricing_version / usage_source / task_id / run_id / step_id。未返回字段写 `null`，不伪造 token 与成本；`estimated_cost` 绑定 `pricing_version`；Run 层聚合、ModelCall 层明细、重试独立成行；**不记录 API Key 与私有 Prompt 全文**。BR1 只落盘与基础查询，不建成本仪表盘。明确不是 Billing / Metering / Subscription / Quota / 客户计费 / FinOps Pipeline / 自动模型路由 / 成本优化平台。

### 8.7 商业结果 v0.1 渐进定型（FR-1111～1113、§16.3）

`BR6-EP01` 只实现 `CommercialOutcomeV01` 九字段最小集，`customer_action` 首版仅七个取值。结果面仍 `READ_ONLY`，不自动回流、不影响排序、不影响安全硬门、不影响发布权限、不自动改 Profile/Rule/Skill/Prompt，缺数据写 `null / UNKNOWN`。累计 5 条有效真实记录后做一次 Founder 字段评审——**五条记录仅用于字段发现，不是统计样本量、商业成功阈值、里程碑通过门或自动 Schema 升级条件**。

### 8.8 两项 Founder 补充裁决

- **TBD-08 已裁决**：`BR1-EP04` 的首个垂直切片平台为**视频号**；小红书笔记、抖音短视频与公众号长文在 BR4 扩展启用。UI-03 的 `minimum_platform_scope_at_BR1` 随之确定。
- **TBD-15 已裁决**：附录 H 的 12 个顶层项自 v0.3.2 签署起冻结，增删拆换均为 Founder-only；新风险进风险场景登记册，不上一页纸；BR7 Pilot 结束后 Founder 复核一次，之后不再改。

### 8.9 新增红线与风险场景

AOE-17（未见真实成品不冻结内容合同）、AOE-18（逻辑并行 ≠ 同 worktree 并发写入）、AOE-19（低成本事实当场记录，但不建平台）；风险场景新增 RS-TENANT-04、RS-COST-01、RS-CREATIVE-01、RS-OUTCOME-02。

执行包数量同步为 **25 个通用执行包（含 BR1-EP00）＋ 2 个 BR5 视觉条件执行包**；执行包数量不得作为进度 KPI。

---

## 九、第四轮追加：SUCCESS-FV-01 与 Deliverable Superiority Test

### 9.1 SUCCESS-FV-01（§1.4，最高成功定义）

> 笛语支线在功能价值上成功的唯一标准，是其最终生成的 `ContentProductionPackage`，在同题、同事实、同等级基础模型、同输出合同的公平条件下，能够稳定、显著地优于事实已经完整提供给普通 LLM 的直接生成结果。

它衡量最终交付物，不是模块数量、Schema 字段数量、DecisionTrace 长度、执行包数量、页数、Checker/Fixture 数量、输出篇幅或排版精美程度。**输出更长不等于输出更强**。三个判断互不替代：

| 判断 | 成立条件 | 判定位置 |
|---|---|---|
| 功能价值成功 | 相对公平基线达到 `CLEARLY_SUPERIOR` | §16.9 |
| 生产交付前提 | `Delivery Safety Gate = PASS` | §16.2 |
| 商业成功 | 真实接受、发布、付费、复购、平台表现 | §16.3 |

### 9.2 公平条件：删除含糊的「同样 Prompt」（§16.9.1）

正式合同统一表述为**同题 ＋ 同事实 ＋ 同一基础模型或同等级、明确版本的基础模型 ＋ 同输出合同**。输出合同两边一致（3 候选、1 推荐、依据与取舍、3 个标题/钩子、正文或口播、脚本结构、镜头计划、商品引用、失效条件与不确定性）。禁止「笛语完整 3+1 交付包 vs 普通 LLM 一段自由文本」这类不公平比较。普通 LLM 不得被故意剥夺笛语已有的事实；模型等级差异不得包装成系统优势。

### 9.3 四个对照组（§16.9.2）

| 组 | 地位 | 说明 |
|---|---|---|
| **B0** 裸问 | `eligible_as_success_evidence: false` | 只能证明「有资料的比没资料的强」；可作演示，不入成功结论 |
| **B1** 事实喂齐一次生成 | `PRIMARY_BASELINE`，必做 | 笛语最现实的直接竞争对手 |
| **B2** 认真使用普通 LLM（2–3 轮） | `SAMPLED_REALISTIC_BASELINE` | BR4 只抽样 3 例 |
| **B3** 系统编译 Prompt | `ARCHITECTURE_DIAGNOSTIC` | 若「笛语 > B1 且 笛语 ≈ B3」，必须如实说明价值可能来自事实接地与 Prompt 编译，而非已证明的独立专家推理代差 |

### 9.4 呈现、主判断与结果口径（§16.9.3～16.9.5）

中性模板 ＋ 人工随机 A/B ＋ 运行前固定案例。唯一主判断问题：**「在不知道来源的情况下，哪一份你愿意直接交给内容团队进入拍摄、编辑或发布准备，而不需要实质性重写？」** 允许 `DIYU / BASELINE / BOTH_USABLE / BOTH_UNUSABLE / UNABLE_TO_JUDGE`；只有 `DIYU` 计胜出，`BOTH_USABLE` 计平局。

- `CLEARLY_SUPERIOR`：10 例中明确胜出 9–10，高难案例至少 2/3，安全门 PASS → 方可写「内容主产品在功能价值上完成定型」
- `ADVANTAGE_BUT_NOT_DECISIVE`：7–8 例 → 有优势但无代差，继续修订，不得用页面完成度、平台数量、Schema 完整或风险场景通过替代结论
- `NO_MATERIAL_ADVANTAGE`：≤6 例、大量 `BOTH_UNUSABLE` 或关键高难案例持续失败 → 返回产品定义/Prompt/架构收敛，或停止投资

这是 Founder 产品路线门，不是统计显著性结论；不加置信区间、Power Analysis、多重比较修正或加权模型。

### 9.5 L1—L5 只用于失败定位（§16.9.6）

保留五层作为诊断视图，不重建为五张评分卡或加权总分。**若优势只在 L2 事实正确与 L5 可追溯，而 L1/L3/L4 与普通 LLM 基本持平，不得宣称内容制作交付包远超普通 LLM**——那只说明可靠性与生产结构更强。要宣称内容主产品成立，Founder 必须明确确认 L1/L3/L4 中至少两层存在稳定、可见优势。

### 9.6 三个执行时点（§16.9.8）

`BR1-EP00` 加 1 例 B1 公平对照（0.5–1 天、零代码、零数据库、不新增执行包编号，不形成正式功能成功结论）；`BR4` 做 10 例（B1 全量、B2/B3 各抽 3 例）内容主产品定型门；`BR7` 同类中性 A/B，**判断人改为真实试点品牌使用者**，并记录实际采用、是否需实质性重写、编辑时间、是否进入制作/发布/复购/付费与客户理由。不得强迫客户选择笛语，也不得把 Founder 判断冒充客户判断。

### 9.7 旧评测机制降级（§16.9.9）

三张评分卡不再作为常规产品成功体系，只保留为临时诊断词汇与风险定位维度，不再形成三个常规总分；Content Battle Score 继续降级为 Preflight Content Signals，不作功能成功判据、不作发布硬门、不出 CTR/完播/爆款概率预测；四臂 Capability Route Experiment 不进常规 Release，仅在 B3 显示 Runtime 可能无增量、核心模型或架构重大更换、Founder 怀疑 Skill ＋ Constraint 已足够或 `material_delta=true` 时才可能运行，否则 `NOT_RUN`。Deliverable Superiority Test 不得被重新扩张成四臂长期实验。

### 9.8 最小数据与文件边界（§16.9.10、附录 I）

首版不新增任何数据库实体（无 EvaluationRun / ComparisonCase / BlindReview / Scorecard / BaselineRegistry 表，无测试结果 API）。执行只需一份运行前案例清单、两组中性输出文件、一页人工选择结果与 Founder 或品牌方结论。附录 I 给出人工记录模板（`case_id … safety_gate`）——**只是记录格式，不是数据库 Schema，不触发运行时开发**。新增 TBD-16：BR4 的 10 例案例清单与 3 个高难案例命题待 Founder 在 BR3 结束前固定。

### 9.9 HTML 的来源与对齐

第四轮指令原文是「不要修改执行规划 HTML」，规划窗口已单独输出 `笛语支线_v0.3.2_阶段里程碑与执行包规划_Rev2.html`（含 SUCCESS-FV-01、B1/B2/B3、CLEARLY_SUPERIOR、BR1-EP00、25＋2、Day-1 Tenant、串行纪律、非承诺日历）。上一轮的 Rev1 已按 Founder 指示删除；Rev2 是 Rev1 的严格超集（同 12 节 ＋ 新增「功能价值唯一标准」节）。

Founder 随后追加指令「将 HTML 对齐 PRD」，据此对 Rev2 做了**七处最小对齐编辑**，只改与 PRD 冲突或缺失的裁决口径，不动结构、样式与其余文字：

| # | 位置 | 改动 |
|---|---|---|
| 1 | 裁决清单「BR1 首个平台」 | 「建议小红书或抖音二选一」→ **已裁决：视频号**（PRD TBD-08 已解除阻断） |
| 2 | 里程碑表 BR1「允许变化」列 | 移除「首个平台」这一变量 |
| 3 | BR1-EP04 执行包卡片 | 标题与说明改为视频号首发 |
| 4 | 里程碑表 BR1 交付列 | 「一个平台内容包」→「视频号单平台内容包」 |
| 5 | BR1-EP00 卡片输入 | 「1 个目标平台」→「目标平台＝视频号」 |
| 6 | UI-03 界面卡片 | 「BR1 做一个平台垂直切片」→「BR1 做视频号单平台垂直切片」 |
| 7 | 裁决清单新增一条 | **Readiness One-Pager 12 行 · 已裁决**（PRD TBD-15：签署起冻结、Founder-only、新风险进登记册、BR7 后复核一次不再改）；并把既有「BR4 10 例案例清单」标注为 PRD TBD-16 |

对齐后核验：标签闭合平衡，`0` 外部依赖、`0` script 标签，单文件可浏览可打印；视频号口径 8 处一致，旧口径「小红书或抖音二选一」`0` 残留。

---

## 十、第五轮追加：TBD-16 十例 Founder Case Slate 落盘（附录 I）

### 10.1 附录定位纠错（必须留痕）

第五轮 Prompt 原文要求把十例写进**附录 H**。执行侧核对后发现这会破坏既有 Founder 裁决：附录 H 是《Pilot / Release Readiness One-Pager》，其 12 行已由 **TBD-15** 冻结（签署起生效、增删拆换 Founder-only）。承载 Deliverable Superiority Test 的是**附录 I**。因此十例落进附录 I，附录 H 一字未动。Founder 随后发出紧急纠错指令，确认这一定位；本节保留过程记录，以免后续审查误读。

**两个附录的合同已彻底分离**：

| 附录 | 承载什么 | 由谁冻结 | 本批是否改动 |
|---|---|---|---|
| 附录 H｜Pilot / Release Readiness One-Pager | 12 行发布准备核对（check / status / evidence_ref / owner / checked_at） | TBD-15（签署起冻结、Founder-only、BR7 后复核一次） | **否**——顶层仍 12 行，无 DS-01～DS-10、无 B0/B1/B2/B3、无 CLEARLY_SUPERIOR、无 TBD-16 |
| 附录 I｜Deliverable Superiority Test | 内容制作交付包优越性对比与 TBD-16 十例 | TBD-16（BR3 结束前 Founder 冻结） | **是**——新增 I.1～I.20 |

未新增附录 J，未产生第二份评测协议。

### 10.2 附录 I 结构（I.1～I.20）

正文 §16.9 仍是 Deliverable Superiority Test 的**规范条款**；附录 I 不复制第二份协议，而是 I.1～I.6 逐项指明规范出处与本轮十例的适用口径，I.7 之后放只存在于此处的内容：

```
附录 I｜Deliverable Superiority Test：内容制作交付包优越性对比
├── I.1  功能价值标准（指向 1.4 SUCCESS-FV-01）
├── I.2  公平对照条件（指向 16.9.1）＋ 模型条件记录字段
├── I.3  B0/B1/B2/B3 在本轮十例中的范围
├── I.4  中性呈现、主判断问题与信息面分离
├── I.5  结果口径（高难门按 4 例适配）
├── I.6  Delivery Safety Gate 独立边界
├── I.7  TBD-16 状态与冻结规则
├── I.8  十例汇总表
├── I.9—I.18  DS-01～DS-10 完整案例卡
├── I.19 人工记录模板
└── I.20 市场理由来源规则与不建设清单
```

### 10.3 TBD-16 状态

```yaml
decision_id: TBD-16
project_location: APPENDIX_I
case_slate_version: v0.1
case_count: 10
hard_case_count: 4
business_case_selection_status: FOUNDER_SELECTED
execution_protocol_status: PROVISIONAL
founder_freeze_completed: false
freeze_authority: FOUNDER_ONLY
freeze_deadline: BR3_EXIT
blocks: BR4_ENTRY
execution_side_may_change_business_meaning: false
execution_side_may_normalize_format: true
```

Founder 已选定十类真实业务命题，执行侧只做格式规范化、不改商业含义、不补造缺失事实。BR3 结束前由 Founder 冻结协议、案例清单、四个高难案例、共同事实包、模型条件与中性输出合同，状态方可转 `FROZEN_FOR_BR4`；未冻结则 **BR4_NOT_AUTHORIZED**。依赖链固定为 `BR3 → Founder Freeze Appendix I / TBD-16 → BR4`，附录 H 不参与此门。

### 10.4 十例与对照范围

| Case | 核心命题 | 平台 | 高难 | 主价值轴 | B2 | B3 |
|---|---|---|:-:|---|:-:|:-:|
| DS-01 | 库存激活与品牌调性 | 抖音 | 是 | L1/L3/L4 | 是 | 否 |
| DS-02 | 极端跨风格与合理取舍 | 小红书 | 是 | L1/L3 | 否 | 是 |
| DS-03 | 版型事实与尺码内容 | 小红书＋视频号 | 是 | L1/L2/L3/L4 | 否 | 否 |
| DS-04 | 同租户跨品牌协同 | 视频号 | 否 | L1/L3/L4 | 否 | 是 |
| DS-05 | 反模板化长文 | 公众号 | 否 | L3/L4 | 是 | 否 |
| DS-06 | 低预算制作可行性 | 视频号 | 否 | L3/L4 | 是 | 否 |
| DS-07 | 证据不足与正确拒绝 | 小红书 | 是 | L2/L4 | 否 | 否 |
| DS-08 | 最小差异重规划 | 小红书＋抖音 | 否 | L1/L3/L4/L5 | 否 | 是 |
| DS-09 | 官方互动身份边界 | 小红书 | 否 | L2/L3/L4 | 否 | 否 |
| DS-10 | 有限商品池与诚实缺口 | 视频号 | 否 | L1/L3/L4 | 否 | 否 |

**B1 覆盖全部十例**（主对照）；B0 不运行、不得作为成功证据。

### 10.5 信息面分离（防答案泄漏）

每张案例卡强制拆成两面：**双方共同输入**＝`business_scenario / authoritative_input_facts / requested_claims / hard_constraints / soft_objectives / target_platform / required_output_contract`；**Judge-only**＝`market_rationale / test_intent / primary_value_axis / secondary_value_axis / allowed_outcome_families / forbidden_outcomes / safety_focus / diagnostic_notes`。参考创意、参考标题、参考搭配、允许答案族、禁止结果与 Judge 预期一律不得进入任何一侧的生成 Prompt——否则测到的是「复述参考答案」。十例均为开放任务，**无唯一 Gold Answer**。

### 10.6 BR4 结果门按 4 个高难案例适配

高难案例由 3 例改为 **4 例**（DS-01/02/03/07），`CLEARLY_SUPERIOR` 条件同步为：

```yaml
overall_diyu_clear_wins: 9-10 of 10
hard_case_total: 4
hard_case_clear_wins_min: 3
delivery_safety_gate: PASS
```

§3.3 核心成功指标、§16.9.5、§18.2 BR4 退出条件与 HTML 已同步。

### 10.7 外部有效性与边界

明确写入：在这十个已知案例上胜出，只证明系统在已公开产品命题上的交付能力，**不能单独证明对全部服装场景的泛化能力**；外部有效性仍由 BR7 的真实品牌、真实新任务和品牌方盲化采用行为验证。十例是公开产品验收题，不得复制进 STORE-A、不得据此生成隐藏答案、不得把生产过程中的修改反向写入 STORE-A。案例未改变品类授权——**男装未被纳入首版授权范围**。

### 10.8 顺带修正的文档缺陷

本轮发现并修复：§16.9.1～16.9.10 此前被错误套用 Heading1 模板（与「17. 章」同级、混入目录顶层），已改为 Heading3，与文档既有惯例（UI-01…、I.1… 均为 H3 且不进 `\o "1-2"` 目录）一致。目录条目由 139 降为 129，是该修正的正确结果，不是内容丢失。

### 10.9 HTML 同步边界

HTML 只同步 TBD-16 摘要（位于附录 I、10 例 4 高难、B1 全量与 B2/B3 抽样、BR3 前冻结、未冻结则 BR4 不启动），**不复制十个案例全文**——HTML 是施工地图，不是考试卷。HTML 中「附录 H」只出现在 TBD-15 的 One-Pager 冻结条目里，未被写成承载对比协议或案例。

---

## 十一、交叉一致性修正（Founder 复核发现的四处口径漂移）

Founder 复核 HTML 与 PRD 时指出四处口径不一致，全部核实存在并已修正。

| # | 漏洞 | 正确口径 | 修正位置 |
|---|---|---|---|
| 1 | HTML 4 处仍写 BR4「至少胜 2/3 难例」 | 4 个高难案例（DS-01/02/03/07）中至少 3 个胜出 | HTML 优越性节、里程碑表、门槛卡、裁决清单；PRD §3.3／§16.9.5／I.5／§18.2 早已是 3/4 |
| 2 | HTML 把三创意方向弱化为「至少一个可命名主维度成对不同」 | 每方向携带 `CreativeDirectionSignature` 且有可命名核心差异；**整组至少两个维度**形成差异；每方向必须写明取舍 | HTML BR4-EP02 包卡；PRD FR-824～826 原本即为正确口径 |
| 3 | BR6 退出条件要求「能可靠记下 5 条真实记录」，同时 BR7 才产生首 5 条真实记录——自相矛盾 | **BR6 验记录能力**（人工表单与 CSV 导入可靠落盘、缺值 null/UNKNOWN、只读无写回，内部样例或演练数据即可）；**BR7 产真实数据并做字段评审** | PRD §18.2 BR6 退出条件（本轮改）＋ HTML BR6 里程碑行与 BR6-EP01 包卡 |
| 4 | 27 张执行包卡中仅 13 张有包级退出条件，0 张有独立环境（分支/worktree/文件范围）与证据落点 | 本表只能作为**归并后的执行总表**；正式施工前仍须按真实 Commit 哈希 JIT 编译任务包 | HTML 执行包节新增红线框，明确本页不是施工合同 |

第 3 项是 PRD 自身的缺陷（由本会话第三轮里程碑重切时引入），不只是 HTML 漂移；第 1、2 项是 HTML 落后于 PRD；第 4 项是范围声明缺失，按反过度工程化纪律用一条边界声明解决，**不为 27 张卡补 3×27 个字段**。

修正后复验：PRD 129 标题／129 目录条目，真实渲染 PDF 129 页逐条核页码 0 不符、0 孤立标题，113 张多行表全部保留表头重复；HTML 标签闭合平衡、0 外部依赖、0 script，「至少 2/3」0 残留。四项已写入提交前断言门，后续任何一处回退都会当场拦下提交。
