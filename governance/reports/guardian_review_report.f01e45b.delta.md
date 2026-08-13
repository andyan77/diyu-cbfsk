# Guardian M0 修复 Delta 复核报告 · `f01e45b4ca4d7416feaec4177f4f8aad2ce35458`

> 本文件是 Guardian 结论原文转录，由执行侧落盘存档。执行侧未改写结论内容。
> 结论性质：工程 Guardian 结论，**不是** Founder 批准，**不是** 外部独立审查。

```yaml
reviewed_commit_hash: f01e45b4ca4d7416feaec4177f4f8aad2ce35458
parent_commit: 2780e65dc32b20576635b887bd7634663afe531b
branch: m0/contract-and-benchmark-foundation-001
guardian_workspace_id: /home/faye/claude-guardian-m0fix-f01e45b
guardian_bootstrap_source: THIS_APPROVED_PROMPT_SECTION_7_5_AND_8
review_scope: DELTA_ONLY（限 M0-FIX-01~04 + 越界排查）
decision: APPROVE
blocking_findings: 无
m0_status_effect: M0 CONDITIONAL → PASS 生效（依 FOUNDER-M0-DECISION-001 第三条，本复核通过即生效）
review_timestamp: "2026-08-13T09:28:21-07:00"
```

## Delta 范围纪律 —— 无夹带

18 文件 / +339 −46。**断言门控里那条硬约束我独立复算过**：

```
ci/checkers 改动数: 0        ci/fixtures 改动数: 0
```

checker 增强确实没混进来污染 delta 范围。这条自我约束做得对——它让「四项修复」可被单独判定，而不是混在一堆改动里让我无法归因。

## 四项修复逐项结论

| 项 | 结论 | 实测证据 |
|---|---|---|
| **M0-FIX-01** | **PASS** | 规范源 diff **恰好只有两处**：`effective: false→true`（附 `effective_precondition_satisfied_by` 绑定 `SIGNOFF-001` / `9335180f` / `1153fc7`）＋红线一条换写。红线清单 **20→20、一换一、其余 19 条逐字不动**。12 份投影重生成 drift=0 |
| **M0-FIX-02** | **PASS** | `current_active_product_truth` v1.1→v1.2，另加 `status: SIGNED` 与更正说明 |
| **M0-FIX-03** | **PASS** | `ec8d723a-4515-45ef-8889-71f6ddafbd0e` 实测 **version=4**、与治理标识不同；治理 UUID 下沉为 `parent_execution_run_id` |
| **M0-FIX-04** | **PASS** | COND-010 已按实际范围改写为 **9 类 / 45 文件**，`status: CLOSED`、`closure_commit: 2780e65d`、`founder_closure_decision` 具名。这正是我上轮要求的处置 |

### 红线改写的专项判断 —— Guardian 认为它是**收紧**，不是放松

原文「开始 M0 十四项正式施工」改为「未经授权开始 M0 施工」。对新措辞做了对抗测试，看它是不是只剩一句好听的话：

| 攻击 | 结果 |
|---|---|
| 删掉 `m0_execution_started` 的授权条目 | `UNAUTHORIZED_TRUE_FLAG` ✓ |
| 授权条目去掉 `signature_base_commit` | `UNBOUND_AUTHORIZATION` ✓ |
| 把 `authorized` 改 false | `UNAUTHORIZED_TRUE_FLAG` ✓ |

**三重锚点都实在。** 关键在于：**原来那条红线从来没有任何 checker 检查过**——它只是规范源里的一句散文。改写后它挂上了「授权必须绑定完整 Commit 哈希」的机器判据。执行侧给出的理由（自我违反的红线守不住任何东西）成立，且改完的版本可执行性反而更强。

## 两项到期裁决

- **POC 限额**：落成 `quota_is_a_ceiling: true` 的上下限约束，并明写「超出任一项须 Founder 另行裁决」。「差一点就够」自行放宽这条路被堵死 ✓
- **单价校准**：`m0_calibration_status: NOT_PERFORMED` 原样保留，理由具名 ✓

## 执行侧两点主动披露 —— 核验结果：**都属实**

1. **`ec8d723a` 未纳入 `check_execution_uuid` 守卫**：实测确认该守卫只覆盖治理任务标识（`2fcbfed0` + parent + 禁用复用 + 2 处出现点），新标识确在其外。**执行侧没假装它有守卫**。附带说明：该 checker 本身不是空转——塞非法 UUID 它抓得住。
2. **未自行把 M0 翻成 PASS**：回执 `M0_CONDITIONAL_PENDING_GUARDIAN_DELTA_REVIEW`、十一份合同全部仍是 `M0_CANDIDATE_PENDING_FOUNDER_M0_DECISION`、红线四位全 false。**升级判定权确实留给了这次复核**。

## 新增非阻塞发现（随 M1-EP01 顺手修，不构成 M0 条件）

| # | 发现 | 证据 | 建议 |
|---|---|---|---|
| **NB-M0-04** | **规范源那份 20 条散文红线清单，本身没有漂移守卫。** `RED_LINE_LIST_DRIFT` 守的是签署回执里的 `never_authorizable` **状态位**清单（N31 即测删 `m2_started`），`check_project_state` 的 payload 里根本没有 `red_lines` 字段。改散文清单不触发任何 checker——投影 drift=0 只保证投影与源一致，源改了再重生成照样 0 | 对 payload 逐键确认；20 条中仅 4 条（M1/M2/知识蒸馏/生产可服务）有 `RED_LINE_FLAGS` 机器锚点 | 给 `red_lines` 加清单指纹或条数断言 + negative fixture。**这是既存缺口、非本次引入**，但 FIX-01 是该清单首次被编辑，所以现在才显形 |
| **NB-M0-05** | **多个 checker 的 payload 清空后仍判绿**——实测 `check_m0_zero_contact` 与 `check_execution_uuid` 皆如此。这是 NB-M0-01 的一般化：判据有检出力，但**没有对自身覆盖面的断言** | 空 payload 探针 | 与 NB-M0-01 合并处理：各 checker 加覆盖面下限断言 |

## 本轮**未**核验的项（按口径外，如实标注而非默认通过）

- **回执 18 份哈希重算**：执行侧声称已重算，Guardian **没有验**。按 FR-CALIBRATION-004「禁止字节级核对」的口径，哈希重算属字节级，不在本次 delta 范围内。如需覆盖，请单独指定。

## 结论

**通过。M0 正式 PASS 生效。**

§14 仍然生效：M0-FIX 之外若再形成新 Commit，须另行复核。

**本结论是工程 Guardian 结论，不是 Founder 批准，也不是外部独立审查。**
