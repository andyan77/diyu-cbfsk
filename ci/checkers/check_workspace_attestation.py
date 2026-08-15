#!/usr/bin/env python3
"""工作面见证：记录必须完整，且不得声称尚未发生的隔离已被见证。

NB-M2-05：原实现只读一个写死的文件名，于是新里程碑的工作面没有落脚处——
要么塞进那份治理任务的文件里（张冠李戴），要么干脆不记（无人发现）。
现在改为自动发现 governance/workspaces/ 下全部见证文件，逐份校验；
新增一个里程碑＝加一份文件，不动 checker。
"""

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


def validate(payload: dict) -> list[str]:
    """payload 形如 {"files": [<每份见证文件>...]}；逐份走同一套判据。"""
    files = payload.get("files")
    if files is None:
        # 兼容单份形态：老夹具直接给一份见证文件的内容。
        files = [payload]
    if not files:
        return ["NO_ATTESTATION_FILES: no workspace attestation file was discovered at all"]

    errors: list[str] = []
    seen_ids: dict[str, str] = {}
    for one in files:
        source = one.get("source_path", "<inline>")
        task_id = one.get("task_id")
        if task_id in seen_ids:
            errors.append(
                f"ATTESTATION_TASK_ID_COLLISION: {source} and {seen_ids[task_id]} both claim task_id {task_id!r}"
            )
        elif task_id:
            seen_ids[task_id] = source
        errors.extend(f"{e} [{source}]" if source != "<inline>" else e for e in _validate_one(one))
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


def collect() -> dict:
    files = []
    for path in sorted((ROOT / "governance" / "workspaces").glob("workspace_attestation.*.yaml")):
        if path.name.endswith(".schema.yaml"):
            continue
        one = load_yaml(str(path.relative_to(ROOT)))
        one["source_path"] = str(path.relative_to(ROOT))
        files.append(one)
    return {"files": files}


if __name__ == "__main__":
    cli(LABEL, collect, validate)
