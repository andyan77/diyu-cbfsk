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
