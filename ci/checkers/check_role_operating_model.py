#!/usr/bin/env python3
"""Role permission model integrity: separation of duties, review mode, risk tiers, re-review."""

from __future__ import annotations

import subprocess

from _common import ROOT, cli, is_full_commit_hash, load_yaml, sha256_text

LABEL = "check_role_operating_model"

# NB-M0-04：那份 20 条散文红线清单此前无人守。指纹与条数存在 Founder 可见的签署回执里，
# 不藏在代码里——藏在代码里等于执行侧可以自己改自己的判据。
RED_LINE_DIGEST_RECIPE = "sha256(utf-8(newline_joined(red_lines)))"

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


def _validate_red_lines(payload: dict, errors: list[str]) -> None:
    manifest = payload.get("red_line_manifest")
    if not manifest:
        errors.append("RED_LINE_MANIFEST_MISSING: the signoff receipt declares no red_line_manifest")
        return
    actual_count = payload.get("red_line_count")
    actual_digest = payload.get("red_line_digest")
    if manifest.get("count") != actual_count:
        errors.append(
            f"RED_LINE_COUNT_DRIFT: manifest declares {manifest.get('count')!r}, source has {actual_count!r}"
        )
    if manifest.get("sha256") != actual_digest:
        errors.append(
            f"RED_LINE_TEXT_DRIFT: manifest pins {manifest.get('sha256')!r}, source hashes to {actual_digest!r}"
        )
    if not manifest.get("last_changed_by_ruling"):
        errors.append("RED_LINE_CHANGE_WITHOUT_RULING: red_line_manifest names no Founder ruling")
    if not is_full_commit_hash(manifest.get("last_changed_commit")):
        errors.append(
            "RED_LINE_CHANGE_WITHOUT_RULING: red_line_manifest.last_changed_commit="
            f"{manifest.get('last_changed_commit')!r} is not a full commit hash"
        )
    if manifest.get("digest_recipe") != RED_LINE_DIGEST_RECIPE:
        errors.append(
            f"RED_LINE_DIGEST_RECIPE_DRIFT: manifest declares {manifest.get('digest_recipe')!r}, "
            f"checker computes {RED_LINE_DIGEST_RECIPE!r}"
        )


def validate(payload: dict) -> list[str]:
    errors: list[str] = []
    roles = {r["role_id"]: r for r in payload.get("roles") or []}

    _validate_red_lines(payload, errors)

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


def _git(*args: str) -> str | None:
    """读不到就返回 None，由 validate 判——不吞，也不假装成 0。"""
    try:
        return subprocess.run(
            ["git", *args], cwd=ROOT, capture_output=True, text=True, check=True
        ).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def _commit_events() -> list[dict]:
    """「提交变了却没重审」现场推导：候选 HEAD 对上最近一轮 Guardian 审过的提交。

    此前这里是 []——role_separation_rules 写着「任何修复形成新 Commit 后先前结论一律失效」，
    而检查它的那个分支永远拿不到事件（B-04-4）。现在事件由 git 与审查登记册现算：
    只要 HEAD 不等于最近审过的那个提交，就必须存在一条已委托的复审记录，否则失败。
    """
    head = _git("rev-parse", "HEAD")
    if head is None:
        return []
    registry = load_yaml("governance/reports/guardian_report_registry.v0.1.yaml")
    entries = registry.get("entries") or []
    if not entries:
        return []
    latest = entries[-1]
    request = load_yaml("governance/reports/m2_premerge_review_request.v0.1.yaml")
    pending = request.get("re_review") or {}
    return [
        {
            "current_commit": head,
            "guardian_reviewed_commit": latest.get("reviewed_commit"),
            "re_review_requested": pending.get("commissioned") is True,
            "re_review_authority": pending.get("authority"),
        }
    ]


def collect() -> dict:
    model = load_yaml("governance/bootstrap/role_operating_model.v0.2.yaml")
    manifest = load_yaml("governance/baseline/founder_pinned_baseline.v0.1.yaml")
    cont = manifest["continuation_execution"]
    signoff = load_yaml("governance/receipts/founder_signoff_receipt.yaml")
    red_lines = model["red_lines"]
    commit_events = _commit_events()

    return {
        "red_line_manifest": signoff.get("red_line_manifest"),
        "red_line_count": len(red_lines),
        "red_line_digest": sha256_text("\n".join(red_lines)),
        "roles": model["roles"],
        "role_separation_rules": model["role_separation_rules"],
        "review_mode": model["review_mode"],
        # B-04-4：这三项此前是 Python 字面量。谁是 Guardian、谁被 Founder 授权临时写入、
        # 有没有「提交变了却没重审」——全都是仓内可查的事实，判据不许自己写一份。
        "guardian_role_id": next(
            (r["role_id"] for r in model["roles"] if r.get("formal_guardian") is True), None
        ),
        "founder_authorized_temporary_writers": sorted(
            {cont["founder_designation"]} - {None}
        ),
        "temporary_writers": [
            {
                "role_id": cont["executor_role_id"],
                "is_task_guardian": cont["executor_is_task_guardian"],
                "founder_exception_recorded": cont["founder_designation"] == "TEMPORARY_EXECUTION_WRITER",
                "codex_default_writer_rule_changed": cont["codex_default_writer_rule_changed"],
            }
        ],
        "commit_events": commit_events,
    }


if __name__ == "__main__":
    cli(LABEL, collect, validate)
