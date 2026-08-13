#!/usr/bin/env python3
"""Execution run UUID must be a valid v4, unique per batch, and parent-linked on continuation."""

from __future__ import annotations

from _common import UUID_V4_RE, cli, load_yaml

LABEL = "check_execution_uuid"


def validate(payload: dict) -> list[str]:
    errors: list[str] = []
    run_id = payload.get("execution_run_id")
    if not isinstance(run_id, str) or not UUID_V4_RE.match(run_id):
        errors.append(f"INVALID_EXECUTION_RUN_UUID: execution_run_id={run_id!r} is not a valid UUIDv4")
        return errors

    parent = payload.get("parent_execution_run_id")
    if parent is not None:
        if not UUID_V4_RE.match(str(parent)):
            errors.append(f"INVALID_EXECUTION_RUN_UUID: parent_execution_run_id={parent!r} is not a valid UUIDv4")
        if parent == run_id:
            errors.append("EXECUTION_RUN_ID_REUSE: parent_execution_run_id equals execution_run_id")

    forbidden = set(payload.get("forbidden_reuse_ids") or [])
    if run_id in forbidden:
        errors.append(f"EXECUTION_RUN_ID_REUSE: {run_id} is listed as a previously used id")

    for name, value in sorted((payload.get("run_id_occurrences") or {}).items()):
        if value != run_id:
            errors.append(f"EXECUTION_RUN_ID_INCONSISTENT: {name} carries {value!r}, expected {run_id!r}")

    if payload.get("continuation") and parent is None:
        errors.append("MISSING_PARENT_EXECUTION_RUN_ID: a continuation batch must link its parent")
    return errors


def collect() -> dict:
    manifest = load_yaml("governance/baseline/founder_pinned_baseline.v0.1.yaml")
    migration = load_yaml("governance/baseline/baseline_migration_record.yaml")
    change_map = load_yaml("PRD_v1.2_change_map.yaml")
    cont = manifest["continuation_execution"]
    return {
        "execution_run_id": cont["execution_run_id"],
        "parent_execution_run_id": cont["parent_execution_run_id"],
        "continuation": True,
        "forbidden_reuse_ids": [manifest["execution_run_id"]],
        "run_id_occurrences": {
            "governance/baseline/baseline_migration_record.yaml": migration["execution_run_id"],
            "PRD_v1.2_change_map.yaml": change_map["change_set"]["execution_run_id"],
        },
    }


if __name__ == "__main__":
    cli(LABEL, collect, validate)
