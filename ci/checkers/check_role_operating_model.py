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


# 一条 Guardian 审查记录「声称自己对当前候选仍然有效」的三个既有字段名。三处记录各用了
# 一个名字（签署回执 / 交接包 / 冻结回执），字段名不同、语义相同；这里只列名字，
# 值一律现读，不在判据里写任何一处的取值。
GUARDIAN_VALIDITY_CLAIM_FIELDS = (
    "valid_for_signature_base",
    "valid_for_current_candidate",
    "prior_decision_valid_for_this_candidate",
)


def _git(*args: str) -> str | None:
    """读不到就返回 None，由调用方处理——不吞，也不假装成空字符串。"""
    try:
        return subprocess.run(
            ["git", *args], cwd=ROOT, capture_output=True, text=True, check=True
        ).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def _validity_claiming_reviews():
    """产出「声称自己仍然有效」的 Guardian 审查记录 (来源, 被审 Commit, 是否已委托复审)。

    本判据守的那条规则是 role_separation_rules.after_new_commit
    previous_guardian_decision_valid = false —— 被违反的形态是**先前结论被当作仍然有效**，
    不是「HEAD 还没被审过」。两者不是一回事：main 上此刻确实存在尚未被 Guardian 审过的
    提交（支线 PRD v0.3.2 是 FOUNDER_REVIEW_CANDIDATE），那是一个真实事实，
    但它由审查流程本身承接，不由本分支承接。本分支只抓「拿旧结论当新结论用」。

    BR0-EP00 之前这里是 []——分支永远拿不到事件，规则真被违反也不会触发。
    现在从三份既有记录现读：任何一条 valid_* 字段为真、而被审 Commit 不等于 HEAD 的记录，
    都是一次「旧结论被当作仍然有效」，除非同时有已委托的复审。
    """
    head = _git("rev-parse", "HEAD")
    if head is None:
        return []
    sources = {
        "governance/receipts/founder_signoff_receipt.yaml": ("guardian_review",),
        "governance/receipts/guardian_handoff_package.yaml": ("prior_guardian_review",),
        "governance/receipts/candidate_freeze_receipt.yaml": ("superseded_candidates",),
    }
    events = []
    for rel, keys in sources.items():
        if not (ROOT / rel).exists():
            continue
        doc = load_yaml(rel)
        for key in keys:
            node = doc.get(key)
            rows = []
            if isinstance(node, dict):
                rows = [(f"{key}.{k}", v) for k, v in node.items() if isinstance(v, dict)]
            elif isinstance(node, list):
                rows = [(f"{key}[{i}]", v) for i, v in enumerate(node) if isinstance(v, dict)]
            for where, row in rows:
                reviewed = row.get("reviewed_commit") or row.get("commit")
                if not reviewed:
                    continue
                claims = [row.get(f) for f in GUARDIAN_VALIDITY_CLAIM_FIELDS if f in row]
                if not any(c is True for c in claims):
                    continue
                events.append(
                    {
                        "source": f"{rel}::{where}",
                        "current_commit": head,
                        "guardian_reviewed_commit": reviewed,
                        "re_review_requested": row.get("re_review_requested") is True,
                    }
                )
    return events


def collect() -> dict:
    model = load_yaml("governance/bootstrap/role_operating_model.v0.2.yaml")
    manifest = load_yaml("governance/baseline/founder_pinned_baseline.v0.1.yaml")
    cont = manifest["continuation_execution"]
    signoff = load_yaml("governance/receipts/founder_signoff_receipt.yaml")
    red_lines = model["red_lines"]

    return {
        "red_line_manifest": signoff.get("red_line_manifest"),
        "red_line_count": len(red_lines),
        "red_line_digest": sha256_text("\n".join(red_lines)),
        "roles": model["roles"],
        "role_separation_rules": model["role_separation_rules"],
        "review_mode": model["review_mode"],
        # BR0-EP00：这两项此前是 Python 字面量。谁是正式 Guardian、谁被 Founder 授权临时写入，
        # 都是仓内可查的事实（规范源 roles.formal_guardian / 基线 Manifest 的 founder_designation），
        # 判据不许自己写一份——那等于判据造出自己要检查的事实。
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
        "commit_events": _validity_claiming_reviews(),
    }


if __name__ == "__main__":
    cli(LABEL, collect, validate)
