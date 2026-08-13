# M1 收口修复交付报告

> 授权 `DIYU-CBFSK-FOUNDER-RD-M1-01` D 节 · 唯一一个最小修复 Commit · 分支 `m1/candidate-freeze`
> 本报告只报结论。**不是 Founder 批准，也不是外部独立审查。**

## 1. 修复内容清单（严格限于 D 节五项）

| D 项 | 做了什么 | 文件 |
|---|---|---|
| D.1 | 新增 CI 依赖单一真源，三个 workflow 统一从该文件安装 | `requirements-ci.txt`、`.github/workflows/*.yml`（3 份） |
| D.2 | `semantic_candidate_commit` 与 `review_package_head` 分离；supersession 基准改为最终 review target | `m1_delivery_receipt.yaml`、`guardian_handoff_m1.md`、PR #2 正文 |
| D.3 | 裁决 A/B/C（连同 D/E）全文落盘；`FR-PROCESS-006-R1` 澄清行；6 项 Open Item 逐项状态 | `DIYU-CBFSK-FOUNDER-RD-M1-01.yaml`、`DIYU-CBFSK-FR-PROCESS-006.yaml`、`m1_delivery_receipt.yaml#open_items` |
| D.4 | 禁止项自查，逐条由提交门控断言 | 见 §4 |
| D.5 | 三个 Actions 全量重跑 | 见 §3 |

## 2. D.1 实测根因与一处口径更正

**根因（实测，非推断）**：`role-governance-integrity` → `Full checker suite and fixtures` → `ci/run_all_checks.py`
加载 `ci/run_schema_fixtures.py` → `import jsonschema` → `ModuleNotFoundError: No module named 'jsonschema'`。
workflow 只装了 `pyyaml python-docx`。日志见 GitHub Actions run id 31733862619（run id，非 Commit 哈希）。

**与「缺 jsonschema」的假设一致**，故按裁决原方案修复。

**但有一处口径要更正**：裁决表述为「远程三个 Actions 全量重跑」，隐含三个都在失败；
实测**只有 `role-governance-integrity` 一个失败**——`document-integrity` 与 `secret-and-hidden-boundary`
在 `97b73f63fff65d9eb259b2f23dd51b0498ffbed6` 上都是 success。
按 D.1 的「按实测做最小修复并在报告说明」如实报出。三个 workflow 仍统一改为从
`requirements-ci.txt` 安装——裁决明文要求，且把三处手写包清单收敛成一处，同类漏装不会再发生。

`jsonschema` 钉 `==3.2.0`：与 M1 本地验证环境一致。3.2.0 只实现到 draft-07，M1 的 19 份 Schema
正是按 draft-07 写的；装更高版本会让 CI 与本地验的不是同一件事。

### 2.1 修复过程中自己制造并修掉的一次失败（如实记录）

第一版 `requirements-ci.txt` 把 `PyYAML` 也钉成本地的 `5.4.1`，理由是「与本地环境一致」。
推送后**三个 workflow 全部变红**——比修复前更糟：`PyYAML 5.4.1` 在 CI 的 Python 3.11 +
新 setuptools 下构建失败（`AttributeError: 'build_ext' object has no attribute 'cython_sources'`），
连原本通过的 `document-integrity` 与 `secret-and-hidden-boundary` 也被带崩。

更正：只钉 `jsonschema`（裁决 D.1 明文要求的那一个），`PyYAML` 与 `python-docx` 不钉版本——
与本次修复前 CI 一直在用的写法一致。更正前在干净 venv 实测：安装解析到 `PyYAML 6.0.3`，
全量核验 21 checkers / 131 判据 fixture / 36 实例 fixture 全绿，且仓内无裸 `yaml.load` 调用
（PyYAML 6 唯一的破坏性变更点）。**这次是先实测再推送，不是再赌一次。**

按 Founder「唯一一个最小修复 Commit」的要求，更正以 `git commit --amend` 合入同一个修复 Commit，
而不是追加第二个提交；候选分支强制推送前该提交尚未被任何角色审查。原始失败 run id
31739617841 / 31739617792 / 31739617773 仍留在 Actions 记录里，不因 amend 而消失。

## 3. 三个工作流全绿证据

见 §5 表格（本报告随修复 Commit 落盘，运行结果在推送后由 Actions 产生，run id 与结论补记于 PR #2 正文）。
判定标准：三个 workflow 均为 `success`，且均为**完整重跑**（非只重跑失败步骤）。

## 4. D.4 禁止项自查

| 禁止项 | 状态 | 证据 |
|---|---|---|
| 不改 M1 对象语义 | 未改 | 回执 33 份交付物哈希逐份复算一致 |
| 不改五品类合同 | 未改 | 同上（5 份适配器 + 冲突优先级表在清单内） |
| 不改事实优先级 | 未改 | `input_output_boundary.v1.0` 属 M0 冻结件，字节未变 |
| 不新增 M2 资产 | 未新增 | 本包新增文件仅 3 份：`requirements-ci.txt`、`RD-M1-01.yaml`、本报告 |
| 不开始桥接 Schema | 未开始 | `01_contracts_and_schemas/` 下无新增 Schema |
| 不在本分支触碰 `m2` 状态位 | 未触碰 | 本分支 `m2_started: false` 且签署回执无 `m2_started` 授权条目 |
| 不改知识状态 | 未改 | `knowledge_distillation_started: false` 未动 |
| 不生成隐藏题或夹具品牌 | 未生成 | `02_benchmark_manifests/` 仅 `README.md` |

## 5. 最终 PR Head

`review_package_head` ＝ 本分支最终 HEAD ＝ PR #2 最终 Head。
**完整 40 位哈希在推送后补记于 PR #2 正文与本节**——它就是包含本文件的那个 Commit，写进文件内会自指。

## 6. 下一步（按裁决 E.3）

CI 全绿 → Guardian 对**最终 Head** 做 Delta 复审 → 总顾问 Delta 复核 →
Founder 单次 PASS ＋ FF-ONLY 合并授权 → main ＝ 最终 M1 SHA → 派发 M2-EP02。

`RD-M1-02`（守 main 实际状态的判据）按 A.4 归入 M2-EP02，**不在本次修复范围**。
M2 启动包 v1.1 继续有效，M2-EP01 在 `candidate/m2` 跑至内置停点后等待指令，不自行开始 EP02。
