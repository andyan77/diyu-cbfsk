# BR0-EP01 交付报告 · 运行时骨架与 Tenant 安全根

> 本文件是模板 `br0_ep01_delivery_report.md.tmpl` 的渲染结果。
> 所有计数从 `11_reports_and_receipts/BR0/BR0-EP01/br0_ep01_delivery_receipt.yaml` 现读；改数字只能改回执，改不动本报告。

| | |
|---|---|
| 包号 | BR0-EP01 |
| 基线 Commit | `8f327c354afb5dc6ec085e48dc6eaf28f4272a13` |
| 候选 Commit | `ad375df6b0587ed3db5aadfe1bac373b1d41ccfa` |
| 分支 | `br0/ep01-runtime-skeleton` |
| 结论 | **PASS** |

---

## 一、这一包到底立住了什么

一句话：**在建第一张客户数据表的同一个提交里，把租户安全根立住了。**

PRD v0.3.2 §10.5 把这件事写成硬要求，理由不是洁癖。`tenant_id` 如果不是第一天就 NOT NULL，
后面补的时候要回填全部历史行——而那时候已经没有任何字段能告诉你某一行当初属于哪个客户。
这类事实一旦当场不记，事后无法恢复。

本包实际落下的四道关卡：

| 关卡 | 内容 | 在哪一层 |
|---|---|---|
| 列约束 | 4 张客户表 `tenant_id NOT NULL` | 数据库结构 |
| 复合外键 | `draft_tasks (tenant_id, brand_id)` → `brands (tenant_id, id)` | 数据库结构 |
| 上下文来源 | 租户只从服务端会话取，请求面上的租户字段声明恰好 1 处 | 应用 |
| 角色分离 | `cbfsk_migrator` 可改结构、`cbfsk_app` 只有 DML 且 NOBYPASSRLS，DDL 授权 0 项 | 数据库权限 |

第二道关卡值得单独说：只写单列外键 `brand_id → brands.id` 是**不够**的。
那种模型下「A 租户的任务引用 B 租户的品牌」在数据库层面完全合法，
全靠应用层每次记得加 `WHERE tenant_id`，漏一次就串租户。
所以 `tests/test_cross_tenant_rejection.py` 故意绕开全部应用代码，直接用 SQL 插这么一行——
实测被数据库拒绝。

---

## 二、交付面

| 面 | 内容 | 计数 |
|---|---|---|
| 后端 | `runtime/` 的 api / domain / worker / adapters | 20 个 Python 模块、12 个路由处理器 |
| 迁移 | `alembic/versions/0001_tenant_root.py` | 1 份手写迁移、6 张表 |
| 前端 | `web/`：Vite + React + Ant Design 工作台 | 自写 3 个源文件 |
| 测试 | `tests/` + `e2e/` | 23 个 pytest 用例、2 个 Playwright 用例 |
| 编排 | 本地 `docker-compose.yml` 与 Staging 编排 | 各 4 个服务 |
| 部署 | `deploy/` provision / deploy / rollback | 3 个脚本 |
| CI | `.github/workflows/runtime-ci.yml` | 5 个作业、5 项边界扫描 |

相对 `main` 共改动 57 个文件。

---

## 三、技术栈（PRD 附录 D 对照）

| 项 | 附录 D 参考结论 | 实测取值 |
|---|---|---|
| Python | 生产基线 3.13，CI 验证 3.14 | 生产 3.13.9，CI 双腿矩阵 2 条 |
| FastAPI | 0.129+ 与 Pydantic v2 | 0.141.1 / Pydantic 2.13.4 |
| SQLAlchemy | 2.0 风格 API | 2.0.52 |
| PostgreSQL | 18 | 18.4 |
| Node.js | 24 LTS | 24.13.0 |
| Vite / React | 不使用 RSC，锁定已修复版本 | Vite 7.3.6 / React 19.2.4，RSC 未启用 |
| Ant Design | 企业级中后台 UI | 5.29.3 |
| Playwright | 关键 E2E 工具 | 1.62.1 |

附录 D 原文：技术版本在 BR0 以 lockfile、SBOM 和安全扫描结果为准。
本包提交三份 lockfile（`uv.lock`、`web/package-lock.json`、`e2e/package-lock.json`），
以上取值全部可复算。

两处版本落点与执行合同的写法不同，均为 registry 上不存在该版本号：
Vite 取 7.3.6、Ant Design 取 5.29.3，
都是各自主版本线上现有的最高版。详见回执 `stack_actual.version_pin_deviations`。

---

## 四、前端：参考而非拷贝

自参考实现**迁入文件数 = 0**，
`pinned_reuse_ledger.v0.1.yaml` 新增条目数 = 0。

参考的是两个**模式**，不是文件：构建配置里 `base` 由后端挂载路径决定（两处不一致时页面能打开但刷新 404，
dev server 下看不出来），以及单一 root 容器的挂载写法。

明确不迁的：样式目录（与 Ant Design 冲突）、组件目录（全部基于 antd 重建）、
以及 `src/services/` 与 `src/app/`——后两者是另一套后端的合同，属禁止迁入面。
CI 的 boundaries 作业直接断言这两个目录不存在。

---

## 五、Worker：只交付骨架

已注册处理器 0 个，队列框架命中 0 处。

这不是漏了。队列选型要由真实的任务形态决定——重试语义、可见性超时、有序性、死信处理，
这些在 BR1-EP03 出现第一个真实异步任务之前全是猜。先引一个框架，等于让骨架期的猜测锁死后面的真实需求。

已经落下的是接口位与一条硬约束：入队信封**必须**带租户，否则 `enqueue()` 直接抛错。
异步任务是最容易丢租户的地方——请求上下文在入队那一刻就没了。

---

## 六、ECS Staging

触发状态：**TRIGGERED**（本地闭环全部通过，满足合同的唯一触发条件）。

| 资源 | 支线取值 |
|---|---|
| 库 | `diyu_cbfsk` |
| 桶 | `diyu-cbfsk-materials` |
| 配置目录 | `/etc/diyu-cbfsk` |
| 应用目录 | `/opt/diyu-cbfsk` |
| 备份目录 | `/var/backups/diyu-cbfsk` |
| 容器前缀 | `diyu-cbfsk-` |
| 应用端口 | `18001` |

端口是**算出来的**：合同规定从 18000 起顺延、占用则 +1，而共享主机上 18000 已被另一进程占用，
provision 脚本现算得 `18001`。写死会当场抢端口。

**邻居应用不受影响**——部署前探 3 项、
部署后再探 3 项，六次全部 200；
共享基础设施容器状态未变，18000 端口的占用进程 pid 未变。
`BLOCKED_ON_SHARED_HOST` 项：无。

支线只监听回环，**未**新增 Nginx server 块、**未**改动主机上任何既有 server 块。
合同允许新增独立 server 块但不要求；对外暴露是独立决定，不作为本包副作用。

初始账号口令由 provision 现场随机生成，bootstrap 跑完即删除，未落仓、未回显。

### 一处自查与收口

第一版部署脚本给共享基础设施容器名与邻居健康探针地址写了默认值。
那是部署环境的事实，不是支线仓的内容，且直接违反 EP01-08「无邻居应用的端点/容器名」。
自查发现后改为必填环境变量（`${VAR:?}`），重建镜像重部署一次。
现仓内站点相关标识 0 项。

---

## 七、遗留项：R6 与 R7

**R6（历史 Guardian 报告豁免）**——`branch_baseline.v0.1.yaml` 的 `gates` 段落：
`guardian_reports_landing.status = EXPLICITLY_WAIVED_WITH_RISK_ACCEPTANCE`，
`m1_03_status = WAIVED_BY_FOUNDER`（**不**记为 MET）。
豁免只覆盖 BR0-EP00 期间那三轮历史报告；本包及此后每个执行包自己的交付报告仍必须落盘并登记，
否则 `check_report_number_traceability` 被架空。

**R7（合并覆盖标记更正）**——`merged_commit_guardian_coverage.status` 由 `NOT_COVERED` 转
`COVERED_BY_POST_MERGE_REVIEW`，同时明写 `timing: POST_MERGE`。时序不抹去：
合并当时 Guardian 结论只覆盖 `9ad5f94`，`95dbc5d` 与 `8f327c3` 是事后补审覆盖的。

两处均**取代**原字段，不与旧口径并存（EQ-1 单一定义处）。

---

## 八、验收

12 条全部 blocking，实测结果：

| ID | 判据 | 方法 | 结果 |
|---|---|---|---|
| EP01-01 | compose 起得来，浏览器可登录并创建 Tenant / Brand / Draft Task | E2E_DEMO | **PASS** |
| EP01-02 | 客户表 `tenant_id NOT NULL`、租户上下文服务端固化、app 角色 NOBYPASSRLS | DETERMINISTIC_CHECK | **PASS** |
| EP01-03 | pytest 与 Playwright 真实用例均接入 CI 且实跑通过 | INTEGRATION_TEST | **PASS** |
| EP01-04 | upgrade → downgrade → upgrade 实跑 | OPERATIONAL_DRILL | **PASS** |
| EP01-05 | 收费面为零 | DETERMINISTIC_GREP | **PASS** |
| EP01-06 | 版本与附录 D 一致、lockfile 已提交、CI 有 3.14 矩阵 | DETERMINISTIC_CHECK | **PASS** |
| EP01-07 | 前端迁入为零、services / app 零迁入 | DETERMINISTIC_CHECK | **PASS** |
| EP01-08 | 历史资产路径与标识为零、无邻居应用标识、零接触判据通过 | CI_FULL_RUN | **PASS** |
| EP01-09 | 全仓无任何密钥值 | CI_FULL_RUN | **PASS** |
| EP01-10 | ECS 命名空间落位、部署前后邻居三项健康检查均 200 | OPERATIONAL_DRILL | **PASS** |
| EP01-11 | 既有闸与 runtime-ci 全绿、工作区干净 | CI_FULL_RUN | **PASS** |
| EP01-12 | R6 豁免与 R7 更正已落盘 | DETERMINISTIC_GREP | **PASS** |

---

## 九、验证

| 命令 | 结果 |
|---|---|
| `python3 ci/run_all_checks.py` | EXIT=0，25 判据 + 161 判据层夹具 + 36 结构层夹具 |
| `python3 ci/compile_role_instructions.py --check` | drift=0 |
| `python3 工具/check_prd_v1_2.py --require-archive` | RESULT PASS，63 项 |
| `git status --porcelain` | 空 |
| GitHub Actions | 四个 workflow 全 success（含 runtime-ci 的 5 个作业） |

---

## 十、未决事项

回执登记已知问题若干条，均已写明「在什么条件下咬人」：
RLS 策略尚未启用（NOBYPASSRLS 目前是空守卫）、lockfile 落点与合同目录树字面不同、
边界扫描保持字面严格因而三处注释改用同义表述、mypy 在 3.14 腿上仍按 3.13 语义检查、
Staging 未装定时备份 timer。详见
`11_reports_and_receipts/BR0/BR0-EP01/br0_ep01_delivery_receipt.yaml` 的 `known_issues`。

**下一步**：Founder 指派 Guardian 在隔离工作区审查本 PR。
Guardian 必须实跑三个既有 workflow 与 `runtime-ci.yml`，不得只跑 `ci/run_all_checks.py`——
BR0-EP00 期间已发生过因只跑本地判据而漏掉红闸的覆盖缺口。执行侧不自行合并。
