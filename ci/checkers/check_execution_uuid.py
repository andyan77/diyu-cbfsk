#!/usr/bin/env python3
"""每个执行批次都要有自己的 v4 运行标识，不复用、不与父标识相同、各处出现值一致。

原实现只守治理任务那一个批次。M0 生成独立标识（ec8d723a）后，那个标识在守卫之外——
Guardian 在 f01e45b 的 delta 复核里点名了这件事，执行侧当时如实披露「尚未纳入守卫」。
这里把它改成**多批次**结构：新增一个批次就是往 RUNS 里加一条，而不是再写一个 checker（EQ-1）。

同时补覆盖面下限（NB-M0-05）：判据有检出力不代表它真的在守东西。payload 被清空时
原实现会显绿；现在守卫批次数少于下限、或某批次一处出现点都没有，一律判失败。
"""

from __future__ import annotations

from _common import UUID_V4_RE, cli, load_yaml

LABEL = "check_execution_uuid"

# 当前必须被守住的批次：治理任务批次与 M0 里程碑批次。少一个就说明有批次脱离守卫。
MINIMUM_GUARDED_RUNS = 2


def _check_run(run: dict, errors: list[str]) -> str | None:
    name = run.get("name", "<unnamed run>")
    run_id = run.get("execution_run_id")
    if not isinstance(run_id, str) or not UUID_V4_RE.match(run_id):
        errors.append(f"INVALID_EXECUTION_RUN_UUID: {name}.execution_run_id={run_id!r} is not a valid UUIDv4")
        return None

    parent = run.get("parent_execution_run_id")
    if parent is not None:
        if not UUID_V4_RE.match(str(parent)):
            errors.append(
                f"INVALID_EXECUTION_RUN_UUID: {name}.parent_execution_run_id={parent!r} is not a valid UUIDv4"
            )
        if parent == run_id:
            errors.append(f"EXECUTION_RUN_ID_REUSE: {name} parent_execution_run_id equals execution_run_id")

    if run_id in set(run.get("forbidden_reuse_ids") or []):
        errors.append(f"EXECUTION_RUN_ID_REUSE: {run_id} is listed as a previously used id")

    occurrences = run.get("run_id_occurrences") or {}
    if not occurrences:
        errors.append(f"UUID_COVERAGE_BELOW_FLOOR: {name} has no recorded occurrence to cross-check")
    for where, value in sorted(occurrences.items()):
        if value != run_id:
            errors.append(f"EXECUTION_RUN_ID_INCONSISTENT: {where} carries {value!r}, expected {run_id!r}")

    if run.get("continuation") and parent is None:
        errors.append(f"MISSING_PARENT_EXECUTION_RUN_ID: {name} is a continuation batch but links no parent")
    return run_id


def validate(payload: dict) -> list[str]:
    errors: list[str] = []
    runs = payload.get("runs") or []

    if len(runs) < MINIMUM_GUARDED_RUNS:
        errors.append(
            f"UUID_COVERAGE_BELOW_FLOOR: {len(runs)} run(s) guarded, at least {MINIMUM_GUARDED_RUNS} required"
        )

    seen: dict[str, str] = {}
    for run in runs:
        run_id = _check_run(run, errors)
        if run_id is None:
            continue
        if run_id in seen:
            errors.append(f"EXECUTION_RUN_ID_REUSE: {run['name']} reuses the id already used by {seen[run_id]}")
        else:
            seen[run_id] = run.get("name", "<unnamed run>")

    return errors


def collect() -> dict:
    manifest = load_yaml("governance/baseline/founder_pinned_baseline.v0.1.yaml")
    migration = load_yaml("governance/baseline/baseline_migration_record.yaml")
    change_map = load_yaml("PRD_v1.2_change_map.yaml")
    m0_receipt = load_yaml("11_reports_and_receipts/m0_delivery_receipt.yaml")
    cont = manifest["continuation_execution"]

    # 按 id 取，不按下标取：裁决文件里插一条修复项就会让下标失准，而 id 是稳定的。
    ruling = load_yaml("governance/founder_rulings/DIYU-CBFSK-FOUNDER-M0-DECISION-001.yaml")
    m0_fix_03 = next(f for f in ruling["m0_decision"]["required_fixes"] if f["id"] == "M0-FIX-03")

    return {
        "runs": [
            {
                "name": "governance_task_continuation",
                "execution_run_id": cont["execution_run_id"],
                "parent_execution_run_id": cont["parent_execution_run_id"],
                "continuation": True,
                "forbidden_reuse_ids": [manifest["execution_run_id"]],
                "run_id_occurrences": {
                    "governance/baseline/baseline_migration_record.yaml": migration["execution_run_id"],
                    "PRD_v1.2_change_map.yaml": change_map["change_set"]["execution_run_id"],
                },
            },
            {
                "name": "m0_milestone_batch",
                "execution_run_id": m0_receipt["execution_run_id"],
                "parent_execution_run_id": m0_receipt["parent_execution_run_id"],
                "continuation": True,
                "forbidden_reuse_ids": [manifest["execution_run_id"], cont["execution_run_id"]],
                "run_id_occurrences": {
                    "governance/founder_rulings/DIYU-CBFSK-FOUNDER-M0-DECISION-001.yaml":
                        m0_fix_03["m0_execution_run_id"],
                },
            },
        ]
    }


if __name__ == "__main__":
    cli(LABEL, collect, validate)
