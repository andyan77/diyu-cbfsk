# STORE-A 净化证据 · 收件目录

这是**唯一**的收件位置。判据只读本目录下这两个文件名，不读任何台账自述：

| 文件 | 最低字段 |
|---|---|
| `store_identity.yaml` | `store_id`、`repository_visibility`、`created_from_scratch`、`fork_of_main`、`shares_main_history`、`founder_attestation{signed_by, signed_at}` |
| `access_matrix.yaml` | `access{founder, hidden_steward, main_codex, claude_planner, guardian, chief_advisor, m3_m4_elicitation}` |

两个文件都不在时，STORE-A 证据状态为 `NOT_RECEIVED`，`COND-011` 不具备关闭条件。
这是当前状态——**不是缺文件，是这一步还没发生**。

## 绝对不能写进这两个文件

- 任何 URL（含 `https://`、`git@`、`ssh://`）
- 代码托管仓库定位符（仓库地址、组织名/仓库名路径）
- Token、Deploy Key、SSH 公私钥
- 本机绝对路径（`/home/…`、`/Users/…`、`C:\…`）
- 私有主机名或内网地址
- 任何隐藏评测内容（题目、答案、品牌名、切分方式）
- 随机种子

理由一句话：这两份文件要证明的是「隔离成立」，不是「仓库在哪」。
写上地址，等于为了证明门锁着而把钥匙挂在门上。

判据会扫描这两个文件的**每一个标量值**，命中上述任一类即
`STORE_A_EVIDENCE_LEAKS_LOCATOR`，并且不会因为「只是个示例」而放行。

## 收件之后

顺序是固定的：**先复检，后入库**。
主仓收到后先跑 `ci/checkers/check_hidden_benchmark_boundary.py`，
通过了才谈 `COND-011 → CLOSED` 与 `m2_hidden_assets_status → STORAGE_READY`。
反过来先收进来再检查，一旦命中，Git 历史里已经有副本了。
