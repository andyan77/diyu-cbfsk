#!/usr/bin/env python3
"""Workspace attestation records must be complete and must not claim un-witnessed isolation."""

from __future__ import annotations

from _common import cli, load_yaml

LABEL = "check_workspace_attestation"

REQUIRED_FIELDS = [
    "workspace_id",
    "workspace_path",
    "conversation_or_session_id",
    "session_started_at",
    "base_commit",
    "role",
]


def validate(payload: dict) -> list[str]:
    errors: list[str] = []

    if payload.get("is_cryptographic_independence_proof") is not False:
        errors.append("OVERCLAIMED_EVIDENCE: attestation must not claim cryptographic independence")

    records = payload.get("records") or []
    if not records:
        errors.append("NO_ATTESTATION_RECORDS")

    for record in records:
        role = record.get("role") or "<unknown role>"
        for field in REQUIRED_FIELDS:
            if field not in record:
                errors.append(f"MISSING_FIELD: {role}.{field}")
        if record.get("conversation_or_session_id") in (None, ""):
            if record.get("session_id_available") is not False:
                errors.append(f"SESSION_ID_FLAG: {role} has no session id but session_id_available is not false")
            if record.get("founder_manual_attestation_required") is not True:
                errors.append(f"MISSING_FOUNDER_ATTESTATION_FLAG: {role} needs founder_manual_attestation_required=true")

    active = [r for r in records if r.get("status") in ("ACTIVE", "COMPLETED")]
    for a in active:
        for b in active:
            if a is b:
                continue
            pair = {a.get("role"), b.get("role")}
            planner_like = {"CLAUDE_EXECUTION_PLANNER", "CLAUDE_PLANNING_AND_VERIFICATION_SURFACE"}
            if pair & planner_like and "CLAUDE_INDEPENDENT_GUARDIAN" in pair:
                if a.get("conversation_or_session_id") and a.get("conversation_or_session_id") == b.get(
                    "conversation_or_session_id"
                ):
                    errors.append("PLANNER_GUARDIAN_SAME_SESSION: planner and guardian share a session id")
                if a.get("workspace_path") and a.get("workspace_path") == b.get("workspace_path"):
                    errors.append("PLANNER_GUARDIAN_SAME_WORKSPACE: planner and guardian share a workspace path")

    for record in records:
        if record.get("role") in ("CODEX_EXECUTION_ENGINEER", "TEMPORARY_EXECUTION_WRITER"):
            if record.get("is_task_guardian") is True:
                errors.append(f"WRITER_IS_GUARDIAN: {record.get('role')} is flagged as the task guardian")

    witness = payload.get("founder_workspace_attestation") or {}
    guardian_ran = any(
        r.get("role") == "CLAUDE_INDEPENDENT_GUARDIAN" and r.get("status") in ("ACTIVE", "COMPLETED")
        for r in records
    )
    if not guardian_ran:
        for key in ("planner_and_guardian_are_different_sessions", "planner_and_guardian_are_different_workspaces"):
            if witness.get(key) is True:
                errors.append(f"UNWITNESSED_CLAIM: {key} is true but the guardian has not run yet")
        if witness.get("attested_by"):
            errors.append("UNWITNESSED_CLAIM: attested_by is filled but the guardian has not run yet")
    else:
        for key in ("planner_and_guardian_are_different_sessions", "planner_and_guardian_are_different_workspaces"):
            if witness.get(key) is not True:
                errors.append(f"MISSING_FOUNDER_WITNESS: {key} must be witnessed once the guardian has run")
        if not witness.get("attested_by") or not witness.get("attested_at"):
            errors.append("MISSING_FOUNDER_WITNESS: attested_by / attested_at required once the guardian has run")

    return errors


def collect() -> dict:
    return load_yaml(
        "governance/workspaces/workspace_attestation.DIYU-CBFSK-GOV-ROLE-OPERATING-MODEL-002.yaml"
    )


if __name__ == "__main__":
    cli(LABEL, collect, validate)
