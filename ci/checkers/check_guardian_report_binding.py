#!/usr/bin/env python3
"""Guardian 结论必须绑哈希，不得靠转述。

A-7 起因：M2 冻结候选的 Guardian 结论（APPROVE_WITH_CONDITIONS、阻断 0）是 Founder 在任务
Prompt 里转述给执行侧的，报告全文从未落盘。转述与原文的差别不在诚信，在**边界**——
一轮审查真正的覆盖范围写在它自己的「本轮未验」段里，而转述通常只带结论。

本判据守三件事：登记为已落盘的，文件必须在且哈希现算相符；没落盘的，必须具名挂账写明原因；
占位文件不得被当成报告本身——它的哈希只能证明占位记录没被改过。
"""

from __future__ import annotations

from _common import ROOT, cli, is_full_commit_hash, load_yaml, sha256_file

LABEL = "check_guardian_report_binding"

REGISTRY = "governance/reports/guardian_report_registry.v0.1.yaml"
LANDED = "LANDED"


def validate(payload: dict) -> list[str]:
    errors: list[str] = []

    entries = payload.get("entries") or []
    if not entries:
        errors.append("GUARDIAN_REGISTRY_EMPTY: the registry lists no Guardian review at all")

    seen: set[str] = set()
    for entry in entries:
        commit = entry.get("reviewed_commit")
        label = commit or "<no commit>"
        if not is_full_commit_hash(commit):
            errors.append(f"GUARDIAN_REVIEW_COMMIT_UNBOUND: {label!r} is not a full 40-hex commit hash")
        elif commit in seen:
            errors.append(f"GUARDIAN_REVIEW_DUPLICATE: {commit} is registered more than once")
        else:
            seen.add(commit)

        if entry.get("status") == LANDED:
            if not entry.get("report_exists"):
                errors.append(
                    f"GUARDIAN_REPORT_MISSING: {label} is registered as LANDED but "
                    f"{entry.get('report')!r} does not exist"
                )
            elif entry.get("declared_sha256") != entry.get("actual_sha256"):
                errors.append(
                    f"GUARDIAN_REPORT_HASH_STALE: {label} records {entry.get('declared_sha256')!r}, "
                    f"the report hashes to {entry.get('actual_sha256')!r}"
                )
            if entry.get("placeholder"):
                errors.append(
                    f"PLACEHOLDER_TREATED_AS_REPORT: {label} is LANDED yet still names a placeholder file"
                )
        else:
            if not entry.get("reason") or not entry.get("blocker_id"):
                errors.append(
                    f"GUARDIAN_REPORT_GAP_UNDECLARED: {label} is not landed and states no reason or blocker id"
                )
            if entry.get("declared_sha256"):
                errors.append(
                    f"PLACEHOLDER_TREATED_AS_REPORT: {label} is not landed but carries a report sha256 — "
                    "没有报告就没有报告哈希"
                )
            if entry.get("placeholder") and not entry.get("placeholder_exists"):
                errors.append(
                    f"GUARDIAN_REPORT_MISSING: {label} names placeholder {entry.get('placeholder')!r}, "
                    "which does not exist"
                )

    declared = payload.get("declared_counts") or {}
    actual_landed = sum(1 for e in entries if e.get("status") == LANDED)
    if declared.get("landed") != actual_landed:
        errors.append(
            f"GUARDIAN_REGISTRY_COUNT_MISSTATED: registry says {declared.get('landed')!r} landed, "
            f"entries give {actual_landed}"
        )
    if declared.get("total") != len(entries):
        errors.append(
            f"GUARDIAN_REGISTRY_COUNT_MISSTATED: registry says {declared.get('total')!r} entries, "
            f"holds {len(entries)}"
        )

    return errors


def collect() -> dict:
    registry = load_yaml(REGISTRY)
    entries = []
    for row in registry["entries"]:
        report = row.get("report")
        placeholder = row.get("placeholder")
        entries.append(
            {
                "reviewed_commit": row.get("reviewed_commit"),
                "status": row.get("status"),
                "report": report,
                "report_exists": bool(report) and (ROOT / report).exists(),
                "declared_sha256": row.get("sha256"),
                "actual_sha256": sha256_file(ROOT / report) if report and (ROOT / report).exists() else None,
                "placeholder": placeholder,
                "placeholder_exists": bool(placeholder) and (ROOT / placeholder).exists(),
                "reason": row.get("reason"),
                "blocker_id": row.get("blocker_id"),
            }
        )
    return {"entries": entries, "declared_counts": registry.get("counts") or {}}


if __name__ == "__main__":
    cli(LABEL, collect, validate)
