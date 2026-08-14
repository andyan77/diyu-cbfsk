#!/usr/bin/env python3
"""执行批次标识：自动发现，不再维护手工清单。

原实现把「哪些批次要被守」写死在 RUNS 里——加一个里程碑就得改一次 checker，忘了改就等于
那个批次脱离守卫，而且没有任何东西会提醒你忘了。A-5 因此改为扫描 governance/** 与
11_reports_and_receipts/**，凡出现 execution_run_id 的地方一律纳入。

守四件事：格式是 UUIDv4；同一个标识不被两个批次占用；声明了父标识的，父标识必须真实存在；
里程碑与执行包回执必须有标识，没有就得显式声明缺口——静默留空不算。
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from _common import ROOT, UUID_V4_RE, cli

LABEL = "check_execution_uuid"

SCAN_DIRS = ("governance", "11_reports_and_receipts")
SCAN_EXTRA_FILES = ("PRD_v1.2_change_map.yaml",)

# 守卫覆盖面下限：判据扫不到东西时必须失败，而不是显绿。
# 当前仓内实际出现点远多于此；下限只用来发现「扫描面整体塌掉」这类故障。
MINIMUM_OCCURRENCES = 8
MINIMUM_DISTINCT_RUNS = 3

_RECEIPT = re.compile(r"^(m\d+)(?:_(ep\d+))?_delivery_receipt\.yaml$")
DECLARED_ABSENCE = "NOT_RECORDED_AT_EXECUTION_TIME"


def _validate_occurrences(payload: dict, errors: list[str]) -> dict[str, set[str]]:
    parents_by_run: dict[str, set[str]] = {}
    for row in payload.get("occurrences") or []:
        where = f"{row.get('file')}:{row.get('path')}"
        run_id = row.get("execution_run_id")
        if not isinstance(run_id, str) or not UUID_V4_RE.match(run_id):
            errors.append(f"INVALID_EXECUTION_RUN_UUID: {where} carries {run_id!r}, not a UUIDv4")
            continue
        parent = row.get("parent_execution_run_id")
        if parent is not None:
            if not UUID_V4_RE.match(str(parent)):
                errors.append(f"INVALID_EXECUTION_RUN_UUID: {where} parent {parent!r} is not a UUIDv4")
            elif parent == run_id:
                errors.append(f"EXECUTION_RUN_ID_REUSE: {where} names itself as its own parent")
            else:
                parents_by_run.setdefault(run_id, set()).add(parent)
    return parents_by_run


def validate(payload: dict) -> list[str]:
    errors: list[str] = []

    occurrences = payload.get("occurrences") or []
    if len(occurrences) < MINIMUM_OCCURRENCES:
        errors.append(
            f"UUID_COVERAGE_BELOW_FLOOR: {len(occurrences)} occurrence(s) discovered, "
            f"at least {MINIMUM_OCCURRENCES} expected — 扫描面塌了比没有守卫更危险"
        )

    parents_by_run = _validate_occurrences(payload, errors)

    known = {
        row["execution_run_id"]
        for row in occurrences
        if isinstance(row.get("execution_run_id"), str) and UUID_V4_RE.match(row["execution_run_id"])
    }
    if len(known) < MINIMUM_DISTINCT_RUNS:
        errors.append(
            f"UUID_COVERAGE_BELOW_FLOOR: {len(known)} distinct run(s) guarded, "
            f"at least {MINIMUM_DISTINCT_RUNS} expected"
        )

    for run_id, parents in sorted(parents_by_run.items()):
        if len(parents) > 1:
            errors.append(
                f"EXECUTION_RUN_ID_INCONSISTENT: {run_id} is recorded with parents {sorted(parents)} — "
                "同一个批次不可能有两个父批次"
            )
        for parent in sorted(parents):
            if parent not in known:
                errors.append(
                    f"PARENT_RUN_ID_UNKNOWN: {run_id} names parent {parent}, which appears nowhere in the repository"
                )

    owners: dict[str, str] = {}
    for row in payload.get("batches") or []:
        run_id = row.get("execution_run_id")
        batch = row.get("batch")
        if run_id is None:
            if row.get("absence_status") != DECLARED_ABSENCE:
                errors.append(
                    f"RUN_ID_ABSENT_WITHOUT_DECLARATION: {batch} has no execution_run_id and declares no gap — "
                    "静默留空读起来像「不适用」，实际是「没记」"
                )
            elif not row.get("absence_note"):
                errors.append(f"RUN_ID_ABSENT_WITHOUT_DECLARATION: {batch} declares a gap without stating why")
            continue
        if run_id in owners and owners[run_id] != batch:
            errors.append(
                f"EXECUTION_RUN_ID_REUSE: {batch} reuses the id already owned by {owners[run_id]}"
            )
        else:
            owners[run_id] = batch

    return errors


def _walk(node, path: str, rel: str, out: list[dict]) -> None:
    if isinstance(node, dict):
        if isinstance(node.get("execution_run_id"), str):
            out.append(
                {
                    "file": rel,
                    "path": path or "<root>",
                    "execution_run_id": node["execution_run_id"],
                    "parent_execution_run_id": node.get("parent_execution_run_id"),
                }
            )
        for key, value in node.items():
            _walk(value, f"{path}.{key}" if path else key, rel, out)
    elif isinstance(node, list):
        for index, value in enumerate(node):
            _walk(value, f"{path}[{index}]", rel, out)


def collect() -> dict:
    paths: list[Path] = []
    for name in SCAN_DIRS:
        paths.extend(sorted((ROOT / name).rglob("*.yaml")))
    for name in SCAN_EXTRA_FILES:
        if (ROOT / name).exists():
            paths.append(ROOT / name)

    occurrences: list[dict] = []
    for path in paths:
        rel = str(path.relative_to(ROOT))
        _walk(yaml.safe_load(path.read_text(encoding="utf-8")), "", rel, occurrences)

    batches = []
    for path in sorted((ROOT / "11_reports_and_receipts").rglob("*_delivery_receipt.yaml")):
        match = _RECEIPT.match(path.name)
        if not match:
            continue
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        batches.append(
            {
                "batch": path.name,
                "execution_run_id": data.get("execution_run_id"),
                "absence_status": data.get("execution_run_id_status"),
                "absence_note": data.get("execution_run_id_note"),
            }
        )

    return {"occurrences": occurrences, "batches": batches}


if __name__ == "__main__":
    cli(LABEL, collect, validate)
