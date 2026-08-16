# execution/｜执行合同区

本目录只放三样东西：执行包模板、回执模板、派发纪律。**不是**执行管理平台，没有数据库、没有后台、没有自动生成系统。执行包是文件，不是服务。

| 路径 | 用途 |
|---|---|
| [`templates/execution_package_template.yaml`](templates/execution_package_template.yaml) | 执行包合同模板；复制改名后落在 `execution/packages/` |
| [`templates/receipt_template.yaml`](templates/receipt_template.yaml) | 执行回执模板；复制改名后落在 `11_reports_and_receipts/<BRn>/<BRn-EPmm>/` |
| [`dispatch_discipline.md`](dispatch_discipline.md) | 派发纪律一页：worktree 归属、单窗口规则、断言门命令链 |

回执落 `11_reports_and_receipts/` 这一棵**唯一**的报告与回执树，不得另起第二棵。

---

## environment_class 枚举定义

取值域固定为 **G / Z / L / S / V / P**，六个取值由 Founder 确认，语义如下。**取值域只可由 Founder 变更**；执行包实例的 `environment_class` 必须取其中之一，不得自造第七个。

| 代号 | 名称 | 构成 |
|---|---|---|
| **G** | 治理/仓库环境 | 已批准基线 Commit、独占 branch/worktree、合同与文档；单一集成者 |
| **Z** | 零代码发现环境 | 聊天窗口、选定 Provider、真实商品与品牌事实；无代码/数据库/Runner |
| **L** | 本地开发环境 | Docker Compose：React + FastAPI + Worker + PostgreSQL + 本地对象存储 + Mock Provider |
| **S** | Staging ECS | 单台 ECS、Nginx、Web/API/Worker、RDS、OSS 私有桶、SLS/CloudMonitor、真实 Provider |
| **V** | 条件视觉环境 | S/P 环境 ＋ Image Adapter ＋ 媒体模型/VLM ＋ 真实源素材 |
| **P** | Pilot Production | ECS/VPC/RAM/TLS/RDS/OSS/备份，真实 Tenant、Brand、Reviewer、真实任务 |

**读法**：G 不跑代码，Z 不写代码，L 不接真实 Provider，S 接真实 Provider 但不接真实客户，V 是 S/P 之上的视觉附加层，P 才有真实租户与真实任务。往下一级走一步，就多一类不可逆后果。

BR0-EP00 自身运行在 **G**：只动合同与文档，未起任何服务、未建数据库、未接任何 Provider。

---

## 技术栈偏离登记规则（所有执行包继承）

凡实施与 PRD 技术栈章节／附录 D 不一致者，一律在回执 `deviation` 段登记，包含
`prd_requires` / `implemented` / `reason` / `status` / `remediation_owner_package` 五个字段。

不一致的三种形态**都要登记，不得只登记第三种**：

| 形态 | 说明 | 例 |
|---|---|---|
| ① 工具替换 | 以 A 工具替代 PRD 指定的 B 工具 | PRD 点名的类型检查器被换成另一个 |
| ② 跨大版本 | major 不同 | PRD 写 v6，实施锁 v5 |
| ③ lockfile 内小版本漂移 | major/minor 相符、具体版本号不同 | 合同写 7.1.14，registry 上没有，锁 7.3.6 |

**为什么三种都要登记**：只登记第三种，是各执行包最容易滑到的地方——小版本漂移一眼就看得见，
所以顺手记了；而工具替换和跨大版本恰恰是影响更大的两种，却因为「反正能跑通」而被当成实现细节
略过。BR0-EP01 首版就同时漏掉了①（PRD 点名的类型检查器被换掉，且 PRD 原文里另一个工具零命中）
与②（PRD 侧要求的 UI 库大版本），只登记了③。判据看不见的偏离等于没有偏离——这条规则就是把
它们逼到台面上。

`status` 取值：

- `FOUNDER_INFORMED_DEVIATION` —— 已登记、Founder 知情、暂不整改；必须同时写
  `remediation_owner_package` 与 `remediation_trigger`
- `RESOLVED_IN_<包号>` —— 该偏离已在某个包内消除，登记条目保留作为痕迹，不删除

**登记不是豁免**。写进 `deviation` 段只意味着这件事被摆到了台面上并且有主，不意味着它被批准为长期状态。
