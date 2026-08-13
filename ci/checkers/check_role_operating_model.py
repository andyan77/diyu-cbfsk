#!/usr/bin/env python3
"""Role permission model integrity: separation of duties, review mode, risk tiers, re-review."""

from __future__ import annotations

from _common import cli, load_yaml

LABEL = "check_role_operating_model"

REQUIRED_ROLES = {
    "FOUNDER_PRODUCT_AUTHORITY",
    "GPT_CHIEF_ADVISOR",
    "CLAUDE_EXECUTION_PLANNER",
    "CODEX_EXECUTION_ENGINEER",
    "CLAUDE_INDEPENDENT_GUARDIAN",
    "CLAUDE_PLANNING_AND_VERIFICATION_SURFACE",
}


def _writes(role: dict) -> bool:
    value = role.get("repo_write_permission", role.get("formal_repository_write_permission", False))
    return value not in (False, None)


def validate(payload: dict) -> list[str]:
    errors: list[str] = []
    roles = {r["role_id"]: r for r in payload.get("roles") or []}

    missing = sorted(REQUIRED_ROLES - set(roles))
    if missing:
        errors.append(f"MISSING_ROLES: {missing}")

    for role_id, role in sorted(roles.items()):
        if _writes(role) and role.get("formal_guardian"):
            errors.append(f"WRITER_IS_GUARDIAN: {role_id} both writes the repository and is a formal guardian")
        if role.get("formal_guardian") and role.get("planning_context_access"):
            errors.append(f"GUARDIAN_READS_PLANNING_CONTEXT: {role_id}")
        if role.get("formal_guardian") and role.get("candidate_edit_permission"):
            errors.append(f"GUARDIAN_EDITS_CANDIDATE: {role_id}")
        if role.get("human") is False and role.get("final_authority"):
            errors.append(f"AI_HAS_FINAL_AUTHORITY: {role_id}")

    writers = sorted(r for r, v in roles.items() if _writes(v))
    if writers and writers != ["CODEX_EXECUTION_ENGINEER"]:
        extra = [w for w in writers if w != "CODEX_EXECUTION_ENGINEER"]
        allowed = set(payload.get("founder_authorized_temporary_writers") or [])
        for writer in extra:
            if writer not in allowed:
                errors.append(f"UNAUTHORIZED_DEFAULT_WRITER: {writer} writes without Founder exception ruling")

    for writer in payload.get("temporary_writers") or []:
        if writer.get("role_id") == payload.get("guardian_role_id"):
            errors.append("TEMPORARY_WRITER_IS_GUARDIAN: emergency writer must not be the task guardian")
        if writer.get("is_task_guardian"):
            errors.append("TEMPORARY_WRITER_IS_GUARDIAN: temporary writer flagged as task guardian")
        if writer.get("founder_exception_recorded") is not True:
            errors.append("TEMPORARY_WRITER_WITHOUT_FOUNDER_EXCEPTION: Founder exception ruling not recorded")
        if writer.get("codex_default_writer_rule_changed") is True:
            errors.append("DEFAULT_WRITER_RULE_CHANGED: temporary writer must not change Codex long-term rule")

    sep = payload.get("role_separation_rules") or {}
    for key in ("session", "workspace", "task_contract"):
        if (sep.get("planner_and_guardian_must_differ") or {}).get(key) is not True:
            errors.append(f"PLANNER_GUARDIAN_SEPARATION: planner_and_guardian_must_differ.{key} must be true")
    after = sep.get("after_new_commit") or {}
    if after.get("previous_guardian_decision_valid") is not False:
        errors.append("STALE_GUARDIAN_DECISION_ALLOWED: previous_guardian_decision_valid must be false after a new commit")
    if after.get("previous_advisor_review_valid") is not False:
        errors.append("STALE_ADVISOR_REVIEW_ALLOWED: previous_advisor_review_valid must be false after a new commit")

    for event in payload.get("commit_events") or []:
        if event.get("guardian_reviewed_commit") and event.get("current_commit") != event.get("guardian_reviewed_commit"):
            if not event.get("re_review_requested"):
                errors.append(
                    "GUARDIAN_REVIEW_NOT_REDONE: commit changed from "
                    f"{event.get('guardian_reviewed_commit')} to {event.get('current_commit')} without re-review"
                )

    review = payload.get("review_mode") or {}
    if review.get("mode") != "FOUNDER_PLUS_ISOLATED_AI":
        errors.append(f"REVIEW_MODE: expected FOUNDER_PLUS_ISOLATED_AI, got {review.get('mode')!r}")
    if review.get("external_human_review") is not False:
        errors.append("EXTERNAL_HUMAN_REVIEW_CLAIMED: external_human_review must be false")
    if review.get("external_legal_opinion") is not False:
        errors.append("EXTERNAL_LEGAL_OPINION_CLAIMED: external_legal_opinion must be false")

    tiers = review.get("risk_tiered_review") or {}
    high = tiers.get("high_risk") or {}
    if high.get("founder_review_coverage") != "100%":
        errors.append(f"HIGH_RISK_COVERAGE: expected 100%, got {high.get('founder_review_coverage')!r}")
    if high.get("sampling_allowed") is not False:
        errors.append("HIGH_RISK_SAMPLING_ALLOWED: high-risk knowledge must not be sampled")

    calib = review.get("reviewer_calibration_contract") or {}
    if calib.get("canonical_name") != "reviewer_calibration_contract":
        errors.append("CALIBRATION_CONTRACT_NAME: canonical name must be reviewer_calibration_contract")

    return errors


def collect() -> dict:
    model = load_yaml("governance/bootstrap/role_operating_model.v0.2.yaml")
    manifest = load_yaml("governance/baseline/founder_pinned_baseline.v0.1.yaml")
    cont = manifest["continuation_execution"]
    return {
        "roles": model["roles"],
        "role_separation_rules": model["role_separation_rules"],
        "review_mode": model["review_mode"],
        "guardian_role_id": "CLAUDE_INDEPENDENT_GUARDIAN",
        "founder_authorized_temporary_writers": ["TEMPORARY_EXECUTION_WRITER"],
        "temporary_writers": [
            {
                "role_id": cont["executor_role_id"],
                "is_task_guardian": cont["executor_is_task_guardian"],
                "founder_exception_recorded": cont["founder_designation"] == "TEMPORARY_EXECUTION_WRITER",
                "codex_default_writer_rule_changed": cont["codex_default_writer_rule_changed"],
            }
        ],
        "commit_events": [],
    }


if __name__ == "__main__":
    cli(LABEL, collect, validate)
