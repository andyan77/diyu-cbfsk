#!/usr/bin/env python3
"""CONDITIONAL is not PASS: every condition must be fully specified and properly closed."""

from __future__ import annotations

from _common import cli, is_full_commit_hash, load_yaml

LABEL = "check_conditional_ledger"

REQUIRED_FIELDS = [
    "condition_id",
    "source_decision_id",
    "source_commit",
    "description",
    "owner",
    "due_milestone",
    "required_evidence",
    "status",
    "verification_role",
    "closure_commit",
    "founder_closure_decision",
]
ALLOWED_STATUS = {"OPEN", "EVIDENCE_SUBMITTED", "VERIFIED", "CLOSED", "WAIVED"}


def validate(payload: dict) -> list[str]:
    errors: list[str] = []

    rules = payload.get("rules") or {}
    if rules.get("conditional_equals_pass") is not False:
        errors.append("CONDITIONAL_TREATED_AS_PASS: rules.conditional_equals_pass must be false")
    if rules.get("verbal_resolution_accepted") is not False:
        errors.append("VERBAL_CLOSURE_ALLOWED: rules.verbal_resolution_accepted must be false")

    for verdict in payload.get("verdicts") or []:
        if verdict.get("verdict") == "CONDITIONAL":
            ids = verdict.get("condition_ids") or []
            if not ids:
                errors.append(
                    f"CONDITIONAL_WITHOUT_LEDGER: verdict {verdict.get('verdict_id')} records no condition_ids"
                )
            known = {c.get("condition_id") for c in payload.get("conditions") or []}
            for cid in ids:
                if cid not in known:
                    errors.append(f"CONDITION_NOT_IN_LEDGER: {cid} referenced by {verdict.get('verdict_id')}")
            if verdict.get("treated_as") == "PASS":
                errors.append(f"CONDITIONAL_TREATED_AS_PASS: {verdict.get('verdict_id')}")

    seen: set[str] = set()
    for cond in payload.get("conditions") or []:
        cid = cond.get("condition_id", "<no id>")
        if cid in seen:
            errors.append(f"DUPLICATE_CONDITION_ID: {cid}")
        seen.add(cid)
        for field in REQUIRED_FIELDS:
            if field not in cond:
                errors.append(f"MISSING_FIELD: {cid}.{field}")
        status = cond.get("status")
        if status not in ALLOWED_STATUS:
            errors.append(f"INVALID_STATUS: {cid} status={status!r}")
        if not cond.get("required_evidence"):
            errors.append(f"MISSING_EVIDENCE_SPEC: {cid} has no required_evidence")
        if status in ("CLOSED", "VERIFIED"):
            if not cond.get("closure_commit"):
                errors.append(f"CLOSURE_WITHOUT_COMMIT: {cid} is {status} but closure_commit is empty")
            if not cond.get("founder_closure_decision"):
                errors.append(f"CLOSURE_WITHOUT_FOUNDER_DECISION: {cid} is {status} without founder_closure_decision")
        if status == "WAIVED" and not cond.get("founder_closure_decision"):
            errors.append(f"WAIVER_WITHOUT_FOUNDER_DECISION: {cid}")
        if "source_commit" in cond:
            source_commit = cond.get("source_commit")
            if not is_full_commit_hash(source_commit):
                errors.append(
                    f"SOURCE_COMMIT_NOT_A_COMMIT_HASH: {cid} source_commit={source_commit!r} "
                    "is not a full 40-hex commit hash"
                )
        if status == "OPEN" and cond.get("closure_commit"):
            errors.append(f"OPEN_WITH_CLOSURE_COMMIT: {cid} is OPEN but already carries a closure_commit")

    if payload.get("merge_requested") and any(
        c.get("status") not in ("CLOSED", "WAIVED") for c in payload.get("conditions") or []
    ):
        if not payload.get("founder_explicit_permission_to_advance"):
            errors.append("ADVANCE_WITH_OPEN_CONDITIONS: merge requested while conditions remain open")

    # A bare boolean is not a permission: it has to name the ruling and bind to one commit.
    if payload.get("founder_explicit_permission_to_advance"):
        if not payload.get("founder_permission_ref"):
            errors.append("PERMISSION_WITHOUT_REF: advance permission names no Founder ruling")
        if not is_full_commit_hash(payload.get("founder_permission_commit")):
            errors.append(
                "UNBOUND_PERMISSION: advance permission is not bound to a full commit hash "
                f"(got {payload.get('founder_permission_commit')!r})"
            )

    return errors


def collect() -> dict:
    ledger = load_yaml("governance/conditions/conditional_decision_ledger.yaml")
    merge_state = ledger.get("merge_state") or {}
    return {
        "rules": ledger["rules"],
        "conditions": ledger["conditions"],
        "verdicts": ledger.get("verdicts") or [],
        "merge_requested": merge_state.get("merge_requested", False),
        "founder_explicit_permission_to_advance": merge_state.get(
            "founder_explicit_permission_to_advance", False
        ),
        "founder_permission_ref": merge_state.get("founder_permission_ref"),
        "founder_permission_commit": merge_state.get("founder_permission_commit"),
    }


if __name__ == "__main__":
    cli(LABEL, collect, validate)
