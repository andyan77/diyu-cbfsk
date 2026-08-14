#!/usr/bin/env python3
"""GR-CLOSURE-01：每个里程碑收口都要有上位真源生成的覆盖矩阵与已注册的 closure checker。

M2 之前这条规则只是惯例——M0 有 check_m0_deliverable_closure，M1 有 check_m1_object_coverage，
但没有任何东西阻止 M3 直接交一份「我交齐了」的自述清单。本判据把惯例变成门禁：
里程碑级回执一出现，登记册里就必须有对应条目，checker 必须真的在注册表里。
"""

from __future__ import annotations

import re

from _common import ROOT, cli, load_yaml, read_text

LABEL = "check_milestone_closure_coverage"

RULE = "governance/gates/milestone_closure_coverage_rule.v0.1.yaml"
REGISTRY = "ci/run_all_checks.py"
RECEIPT_DIR = "11_reports_and_receipts"

_MILESTONE_FROM_RECEIPT = re.compile(r"^(m\d+)_delivery_receipt\.yaml$")


def validate(payload: dict) -> list[str]:
    errors: list[str] = []

    entries = payload.get("milestones") or []
    if not entries:
        errors.append("MILESTONE_WITHOUT_CLOSURE_CHECKER: the rule registers no milestone at all")

    registered: set[str] = set()
    for entry in entries:
        name = entry.get("milestone", "<unnamed>")
        registered.add(name)

        if not entry.get("upstream_source_exists"):
            errors.append(f"COVERAGE_SOURCE_MISSING: {name} upstream source {entry.get('upstream_source')!r} not found")
        if not entry.get("coverage_map_exists"):
            errors.append(f"COVERAGE_SOURCE_MISSING: {name} coverage map {entry.get('coverage_map')!r} not found")
        if not entry.get("closure_checker_exists"):
            errors.append(
                f"MILESTONE_WITHOUT_CLOSURE_CHECKER: {name} names {entry.get('closure_checker')!r}, which does not exist"
            )
        elif not entry.get("closure_checker_registered"):
            errors.append(
                f"CLOSURE_CHECKER_NOT_REGISTERED: {name}'s {entry.get('closure_checker')!r} is absent from {REGISTRY}"
            )
        if entry.get("milestone_receipt") and not entry.get("milestone_receipt_exists"):
            errors.append(
                f"COVERAGE_SOURCE_MISSING: {name} names receipt {entry.get('milestone_receipt')!r}, which does not exist"
            )

    for milestone in sorted(payload.get("milestones_with_receipts") or []):
        if milestone not in registered:
            errors.append(
                f"MILESTONE_RECEIPT_WITHOUT_COVERAGE_ENTRY: {milestone} has a milestone delivery receipt "
                "but no entry in the closure coverage rule"
            )

    declared = payload.get("declared_milestone_count")
    if declared != len(entries):
        errors.append(
            f"MILESTONE_COUNT_MISSTATED: rule declares {declared!r} milestones, registers {len(entries)}"
        )

    return errors


def collect() -> dict:
    rule = load_yaml(RULE)
    registry_src = read_text(REGISTRY)

    entries = []
    for row in rule["milestones"]:
        checker = row["closure_checker"]
        module = checker.rsplit("/", 1)[-1][: -len(".py")]
        entries.append(
            {
                "milestone": row["milestone"],
                "upstream_source": row["upstream_source"],
                "upstream_source_exists": (ROOT / row["upstream_source"]).exists(),
                "coverage_map": row["coverage_map"],
                "coverage_map_exists": (ROOT / row["coverage_map"]).exists(),
                "closure_checker": checker,
                "closure_checker_exists": (ROOT / checker).exists(),
                "closure_checker_registered": f'"{module}"' in registry_src,
                "milestone_receipt": row.get("milestone_receipt"),
                "milestone_receipt_exists": (ROOT / row["milestone_receipt"]).exists()
                if row.get("milestone_receipt")
                else None,
            }
        )

    # 自动发现：里程碑级回执直接从目录扫，新增里程碑不需要改这里
    found = set()
    for path in (ROOT / RECEIPT_DIR).glob("m*_delivery_receipt.yaml"):
        m = _MILESTONE_FROM_RECEIPT.match(path.name)
        if m:
            found.add(m.group(1).upper())

    return {
        "milestones": entries,
        "milestones_with_receipts": sorted(found),
        "declared_milestone_count": (rule.get("machine_checkable_fields") or {})
        .get("registered_milestone_count", {})
        .get("current_value"),
    }


if __name__ == "__main__":
    cli(LABEL, collect, validate)
