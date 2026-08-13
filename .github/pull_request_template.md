<!-- L2/L3 任务必须逐项填写。留空、写「见上文」或写「最新版」的 PR 不予合并。 -->

## 1. 任务标识

- `task_id`：
- `execution_run_id`（标准 UUIDv4）：
- `parent_execution_run_id`（如为续跑批次）：
- `founder_ruling_id`：
- 任务分级：`L1` / `L2` / `L3`

## 2. 提交对象

- `baseline_commit`（完整哈希，禁止「最新版」）：
- `candidate_commit`（完整哈希）：
- 变更文件清单：

## 3. 角色与隔离

- 写入工作面 role_id：
- Planner 工作面 / 会话：
- Guardian 工作面 / 会话：
- [ ] Planner 与 Guardian 不同会话、不同工作区、不同任务合同
- [ ] 写入者未担任本任务 Guardian
- [ ] 工作区佐证已写入 `governance/workspaces/`
- [ ] 已知：工作区记录只是程序性佐证，不是密码学独立性证明

## 4. 审查状态（L3 不得跳过，除非 Founder 显式豁免）

- 独立 Guardian：`PASS` / `CONDITIONAL` / `BLOCK` / `NOT_RUN`
  - `guardian_bootstrap_source`：
- ChatGPT 总顾问远程审查：`COMPLETED` / `WAIVED_BY_FOUNDER` / `DEFER` / `NOT_RUN`
  - 若豁免：理由 / 风险接受人 / 时间戳：
- Founder 对具体 Commit 的批准：

> 若审查后又产生新 Commit：先前 Guardian 与顾问结论一律失效，必须重审。

## 5. CONDITIONAL 条件

- [ ] 本 PR 无 CONDITIONAL 条件
- [ ] 有条件，已全部进入 `governance/conditions/conditional_decision_ledger.yaml`，字段齐全（含 `closure_commit` 与 `founder_closure_decision`）

## 6. Checker 结果（逐项，不接受「全绿」一句话）

```
python3 ci/run_all_checks.py
python3 ci/compile_role_instructions.py --check
python3 工具/check_prd_v1_2.py
python3 工具/audit_docx_package.py
```

粘贴逐项 PASS/FAIL：

## 7. 红线自查

- [ ] 未开始 M0 / M1 / M2 / 知识蒸馏
- [ ] 未生成夹具品牌或隐藏品牌
- [ ] 隐藏评测内容未进入主仓或 Git 历史
- [ ] 未接入真实库存、真实顾客，未创建 Serving，未自动发布
- [ ] 未把 AI 评审表述为外部专家，未把 Founder 自评表述为法律意见
- [ ] v1.2 生效前未归档 v1.1
- [ ] 未在 Founder 批准前合并 main
- [ ] 未改变 M0 十四项与 125—185 人月 / 15—24 个月基线

## 8. 未决事项

只列真正需要 Founder 裁决的问题；已由已批准 Prompt 裁决的事项不得重新标为建议默认。
