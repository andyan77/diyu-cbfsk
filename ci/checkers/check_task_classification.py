#!/usr/bin/env python3
"""L1/L2/L3 definitions, required reviews per class, and role-unavailability handling."""

from __future__ import annotations

from _common import cli, load_yaml

LABEL = "check_task_classification"

L1_FORBIDDEN_SCOPE = {
    "产品范围", "能力", "角色", "状态", "阈值", "风险", "Schema",
    "安全", "合规", "CI", "知识晋级", "发布", "隐藏评测",
}
L3_REQUIRED_REVIEWS = {"独立 Guardian", "ChatGPT 总顾问远程审查", "Founder 具体 Commit 批准"}


def validate(payload: dict) -> list[str]:
    errors: list[str] = []
    tc = payload.get("task_classification") or {}

    for level in ("L1", "L2", "L3"):
        if level not in tc:
            errors.append(f"MISSING_TASK_CLASS: {level}")

    l1 = tc.get("L1") or {}
    missing_forbidden = sorted(L1_FORBIDDEN_SCOPE - set(l1.get("forbidden_scope") or []))
    if missing_forbidden:
        errors.append(f"L1_SCOPE_TOO_WIDE: L1 forbidden_scope is missing {missing_forbidden}")
    overlap = sorted(set(l1.get("allowed_scope") or []) & L1_FORBIDDEN_SCOPE)
    if overlap:
        errors.append(f"L1_SCOPE_CONFLICT: {overlap} appear in both allowed and forbidden scope")

    l3 = tc.get("L3") or {}
    missing_reviews = sorted(L3_REQUIRED_REVIEWS - set(l3.get("must_not_skip_without_explicit_founder_waiver") or []))
    if missing_reviews:
        errors.append(f"L3_REVIEW_SKIPPABLE: {missing_reviews} are not protected for L3")

    task = payload.get("task") or {}
    if task.get("declared_class") != task.get("required_class"):
        errors.append(
            f"TASK_CLASS_MISMATCH: declared {task.get('declared_class')!r}, required {task.get('required_class')!r}"
        )
    if task.get("declared_class") == "L1":
        touched = sorted(set(task.get("touched_scope") or []) & L1_FORBIDDEN_SCOPE)
        if touched:
            errors.append(f"L1_MISCLASSIFIED: task touches {touched}, which L1 must never cover")

    fallback = payload.get("role_unavailability_fallback") or {}
    if fallback.get("default_action") != "DEFER":
        errors.append(f"FALLBACK_DEFAULT: expected DEFER, got {fallback.get('default_action')!r}")
    if fallback.get("silent_bypass_allowed") is not False:
        errors.append("SILENT_BYPASS_ALLOWED: role unavailability must never be silently bypassed")

    for role in payload.get("role_availability") or []:
        if role.get("available") is False:
            decision = role.get("founder_decision")
            if decision not in ("DEFER", "APPOINT_ALTERNATE_ADVISOR", "EXPLICITLY_WAIVE_WITH_RISK_ACCEPTANCE"):
                errors.append(
                    f"SILENT_SKIP: {role.get('role_id')} is unavailable but Founder decision is {decision!r}"
                )
            if role.get("review_completed_claimed") is True:
                errors.append(
                    f"FALSE_REVIEW_CLAIM: {role.get('role_id')} unavailable but review_completed is claimed true"
                )
            if decision == "EXPLICITLY_WAIVE_WITH_RISK_ACCEPTANCE":
                for field in ("waiver_reason", "risk_accepted_by", "waiver_timestamp"):
                    if not role.get(field):
                        errors.append(f"INCOMPLETE_WAIVER: {role.get('role_id')} missing {field}")

    return errors


def collect() -> dict:
    model = load_yaml("governance/bootstrap/role_operating_model.v0.2.yaml")
    return {
        "task_classification": model["task_classification"],
        "role_unavailability_fallback": model["role_unavailability_fallback"],
        "task": {
            "task_id": model["task_id"],
            "declared_class": model["task_classification"]["current_task_class"],
            "required_class": "L3",
            "touched_scope": ["角色", "状态", "合规", "CI", "隐藏评测", "风险"],
        },
        # B-04-4：这张表此前是 collect() 里的 Python 字面量——判据自己造出自己要检查的事实。
        # 现已搬进规范源 role_operating_model.v0.2.yaml role_availability，这里只负责读。
        "role_availability": model["role_availability"]["items"],
    }


if __name__ == "__main__":
    cli(LABEL, collect, validate)
