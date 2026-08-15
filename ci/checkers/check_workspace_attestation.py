#!/usr/bin/env python3
"""Workspace attestation records must be complete and must not claim un-witnessed isolation."""

from __future__ import annotations

from _common import ROOT, cli, load_yaml

LABEL = "check_workspace_attestation"

REQUIRED_FIELDS = [
    "workspace_id",
    "workspace_path",
    "conversation_or_session_id",
    "session_started_at",
    "base_commit",
    "role",
]


def _documents(payload: dict) -> list[dict]:
    """两种载荷都吃：扁平单文档，与 collect() 扫目录后的多文档。

    R-03 之前 collect() 写死一个文件名——目录里再放一份佐证，判据看都不看。
    改成扫目录后载荷可能带多份，因此这里统一成 [{file, document}]。
    既有夹具喂的是扁平单文档，照旧工作；断言逻辑与错误码一条没动。
    """
    docs = payload.get("documents")
    if docs is None:
        return [{"file": payload.get("source_file"), "document": payload}]
    return docs


def validate(payload: dict) -> list[str]:
    errors: list[str] = []
    docs = _documents(payload)
    if not docs:
        errors.append("NO_ATTESTATION_DOCUMENT: 一份工作区佐证都没扫到 —— 扫不到不等于没问题")
    for entry in docs:
        for err in _validate_one(entry.get("document") or {}):
            errors.append(f"{err} (in {entry['file']})" if len(docs) > 1 and entry.get("file") else err)
    return errors


def _validate_one(payload: dict) -> list[str]:
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


ATTESTATION_DIR = "governance/workspaces"
SCHEMA_FILE = "workspace_attestation.schema.yaml"


def collect() -> dict:
    """扫 governance/workspaces/ 下每一份 workspace_attestation.*.yaml（Schema 本身除外）。

    R-03：此前写死单一文件名，于是新任务放进来的佐证根本不会被读——判据在，
    但它守的是一个固定文件，不是这个目录。
    """
    documents = []
    for path in sorted((ROOT / ATTESTATION_DIR).glob("workspace_attestation.*.yaml")):
        if path.name == SCHEMA_FILE:
            continue
        rel = f"{ATTESTATION_DIR}/{path.name}"
        documents.append({"file": rel, "document": load_yaml(rel)})
    return {"documents": documents}


if __name__ == "__main__":
    cli(LABEL, collect, validate)
