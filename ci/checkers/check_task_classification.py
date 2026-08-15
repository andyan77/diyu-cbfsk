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


# 回执记录的**状态** → 规范源 role_unavailability_fallback 里的**选项**。
# 两张词表本来就是两个东西：options 是「可以怎么裁」（EXPLICITLY_WAIVE…），
# 回执记的是「已经这么裁了」（EXPLICITLY_WAIVED…）。此处只做一次显式对照；
# 选项表本身现读规范源，不在判据里另抄一份。映射不出来即返回 None，
# 由 validate 判 SILENT_SKIP —— 认不出来的处置一律当作没处置（fail closed）。
ADVISOR_STATUS_TO_DECISION = {
    "EXPLICITLY_WAIVED_WITH_RISK_ACCEPTANCE": "EXPLICITLY_WAIVE_WITH_RISK_ACCEPTANCE",
    "WAIVED_BY_FOUNDER": "EXPLICITLY_WAIVE_WITH_RISK_ACCEPTANCE",
    "DEFERRED": "DEFER",
    "ALTERNATE_ADVISOR_APPOINTED": "APPOINT_ALTERNATE_ADVISOR",
}


def _advisor_decision(options, status):
    decision = ADVISOR_STATUS_TO_DECISION.get(status)
    return decision if decision in (options or []) else None


def _role_availability(model: dict, manifest: dict, signoff: dict) -> list[dict]:
    """三个非 Founder 角色的可用性与 Founder 处置——从两份既有记录现推。

    BR0-EP00 之前这里是一张写在 collect() 里的 Python 字面量表：判据自己造出自己要检查的
    事实。它还写错了一处——GPT_CHIEF_ADVISOR 被标成 available=True，而签署回执明写
    「ChatGPT 执行侧持续连接故障」并按记录性豁免处置。现按记录现读：

      CODEX_EXECUTION_ENGINEER —— 基线 Manifest 的 continuation_execution（执行面故障 +
        Founder 指派临时写入角色顶替）。指派了替代角色，即 APPOINT_ALTERNATE_ADVISOR。
      GPT_CHIEF_ADVISOR —— 签署回执 advisor_review。其 advisor_review_status 的取值
        就是 founder_decision 的合法枚举值本身，不做映射。豁免时点取回执 signed_at：
        豁免是随该回执一并落盘的，回执签署时点即该处置的时点。
      CLAUDE_INDEPENDENT_GUARDIAN —— 签署回执 guardian_review 里有带 decision 的轮次，
        即该角色实际可用。
    """
    cont = manifest["continuation_execution"]
    options = ((model["role_unavailability_fallback"] or {}).get("GPT_CHIEF_ADVISOR") or {}).get("options")
    advisor = signoff.get("advisor_review") or {}
    guardian = signoff.get("guardian_review") or {}

    rows = [
        {
            "role_id": "CODEX_EXECUTION_ENGINEER",
            "available": False,
            "founder_decision": (
                "APPOINT_ALTERNATE_ADVISOR" if cont.get("founder_designation") else None
            ),
            "note": f"{cont.get('reason')}；Founder 指派 {cont.get('founder_designation')} 顶替写入工作面",
            "review_completed_claimed": False,
            "waiver_reason": None,
            "risk_accepted_by": None,
            "waiver_timestamp": None,
        },
        {
            "role_id": "GPT_CHIEF_ADVISOR",
            "available": advisor.get("advisor_review_status") not in (
                "EXPLICITLY_WAIVED_WITH_RISK_ACCEPTANCE",
                "UNAVAILABLE",
            ),
            "founder_decision": _advisor_decision(options, advisor.get("advisor_review_status")),
            # 规范源点名的违禁陈述是 advisor_review_completed: true。回执没有这个键即为 False，
            # 不拿 silently_skipped 顶替——那是另一个问题的另一个字段。
            "review_completed_claimed": advisor.get("advisor_review_completed") is True,
            "waiver_reason": advisor.get("waiver_reason"),
            "risk_accepted_by": advisor.get("risk_accepted_by"),
            # 回执的 advisor_review 块本身没有时点字段（规范源要求 waiver_timestamp 必填，
            # 这是一处既存缺口）。豁免是随该回执一并落盘的，故取回执 signed_at；
            # 该缺口记在 BR0-EP00 回执 known_issues，不在此处假装它不存在。
            "waiver_timestamp": signoff.get("signed_at"),
        },
        {
            "role_id": "CLAUDE_INDEPENDENT_GUARDIAN",
            "available": any(
                isinstance(r, dict) and r.get("decision") for r in guardian.values()
            ),
            "review_completed_claimed": False,
        },
    ]
    return rows


def collect() -> dict:
    model = load_yaml("governance/bootstrap/role_operating_model.v0.2.yaml")
    manifest = load_yaml("governance/baseline/founder_pinned_baseline.v0.1.yaml")
    signoff = load_yaml("governance/receipts/founder_signoff_receipt.yaml")
    return {
        "task_classification": model["task_classification"],
        "role_unavailability_fallback": model["role_unavailability_fallback"],
        "task": {
            "task_id": model["task_id"],
            "declared_class": model["task_classification"]["current_task_class"],
            "required_class": "L3",
            "touched_scope": ["角色", "状态", "合规", "CI", "隐藏评测", "风险"],
        },
        "role_availability": _role_availability(model, manifest, signoff),
    }


if __name__ == "__main__":
    cli(LABEL, collect, validate)
