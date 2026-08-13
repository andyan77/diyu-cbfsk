#!/usr/bin/env python3
"""Pinned baseline manifest must still describe the files that are actually in the repo."""

from __future__ import annotations

from _common import ROOT, cli, load_yaml, sha256_file

LABEL = "check_baseline_hashes"


def validate(payload: dict) -> list[str]:
    errors: list[str] = []

    if payload.get("founder_confirmation_status") != "CONFIRMED":
        errors.append("BASELINE_NOT_CONFIRMED: founder_confirmation.status must be CONFIRMED before editing documents")
    if payload.get("baseline_effective") is not True:
        errors.append("BASELINE_NOT_EFFECTIVE: baseline_effective must be true after Founder confirmation")
    if payload.get("document_editing_authorized") is not True:
        errors.append("EDITING_NOT_AUTHORIZED: document_editing_authorized must be true after Founder confirmation")

    entries = payload.get("entries") or []
    if not entries:
        errors.append("EMPTY_MANIFEST: no active baseline candidates recorded")
    for entry in entries:
        name = entry["repository_path"]
        if not entry.get("present"):
            errors.append(f"MISSING_BASELINE_FILE: {name} recorded in manifest but absent from the repository")
            continue
        if entry.get("authorized_modification_in_this_task"):
            if not entry.get("authorization_ref"):
                errors.append(f"UNAUTHORIZED_BASELINE_EDIT: {name} is modified without an authorization_ref")
            expected = entry.get("post_change_binary_sha256")
            if expected in (None, "", "PENDING_FREEZE"):
                errors.append(f"UNPINNED_DELIVERED_STATE: {name} post_change_binary_sha256 is not pinned yet")
            elif entry.get("actual_binary_sha256") != expected:
                errors.append(
                    f"AUTHORIZED_FILE_CHANGED_AFTER_FREEZE: {name} binary sha256 "
                    f"{entry.get('actual_binary_sha256')} != pinned {expected}"
                )
        elif entry.get("actual_binary_sha256") != entry.get("recorded_binary_sha256"):
            errors.append(
                "PRODUCT_BASELINE_SEMANTIC_CONFLICT: "
                f"{name} binary sha256 {entry.get('actual_binary_sha256')} != manifest {entry.get('recorded_binary_sha256')}"
            )
        for flag in ("local_remote_binary_equal", "local_remote_semantic_equal"):
            if flag in entry and entry[flag] is not True:
                errors.append(f"UNRESOLVED_BASELINE_DIFFERENCE: {name}.{flag} is not true")

    for entry in payload.get("reference_hashes") or []:
        if not entry.get("located"):
            errors.append(
                f"FOUNDER_REFERENCE_FILE_UNLOCATABLE: {entry['file']} is not recorded at any manifest path"
            )
        elif entry["actual"] != entry["founder_reference"]:
            errors.append(
                f"FOUNDER_REFERENCE_HASH_MISMATCH: {entry['file']} at {entry.get('resolved_path')} "
                f"actual {entry['actual']} != founder {entry['founder_reference']}"
            )
    return errors


# Founder 在本轮 dispatch 中直接给出的 binary 参考哈希。**值**必须独立于 Manifest——交叉核对
# 的意义就在于两个来源互不派生；但**路径**只能有一处记录，由 Manifest 的 repository_path 提供，
# 否则文件一归档就要改两个地方（EQ-1）。
FOUNDER_REFERENCE_BINARY_HASHES = {
    "笛语跨品牌服装搭配专家内核_PRD与执行里程碑_v1.1.docx":
        "1532f59eb004bf6a7e47f8429af43969905ba49a51c850b21c728a8711b78f97",
    "笛语跨品牌服装搭配专家内核_M0执行申请_v1.1.docx":
        "bc89e25b437f2cd88e55632451be40213ea6b7733ecfb19b91e5cc7e6463c997",
    "PRD_v1.1_核验回执.docx":
        "080008393c077b2a92d5c79036cfc25f5b1c8027a5630ae42222eb926316b3c9",
}


def collect() -> dict:
    manifest = load_yaml("governance/baseline/founder_pinned_baseline.v0.1.yaml")
    entries = []
    for candidate in manifest["active_baseline_candidates"]:
        rel = candidate["repository_path"]
        path = ROOT / rel
        entry = {
            "repository_path": rel,
            "present": path.exists(),
            "recorded_binary_sha256": candidate["binary_sha256"],
            "local_remote_binary_equal": candidate.get("local_remote_binary_equal"),
            "local_remote_semantic_equal": candidate.get("local_remote_semantic_equal"),
            "authorized_modification_in_this_task": candidate.get("authorized_modification_in_this_task", False),
            "authorization_ref": candidate.get("authorization_ref"),
            "post_change_binary_sha256": candidate.get("post_change_binary_sha256"),
        }
        if path.exists():
            entry["actual_binary_sha256"] = sha256_file(path)
        entries.append(entry)

    by_original_name = {}
    for candidate in manifest["active_baseline_candidates"]:
        rel = candidate["repository_path"]
        by_original_name[candidate.get("repository_path_before_archive") or rel] = rel

    references = []
    for name, expected in sorted(FOUNDER_REFERENCE_BINARY_HASHES.items()):
        rel = by_original_name.get(name)
        path = (ROOT / rel) if rel else None
        references.append(
            {
                "file": name,
                "resolved_path": rel,
                "located": bool(rel and path.exists()),
                "founder_reference": expected,
                "actual": sha256_file(path) if (path and path.exists()) else "<missing>",
            }
        )

    return {
        "founder_confirmation_status": manifest["founder_confirmation"]["status"],
        "baseline_effective": manifest["baseline_effective"],
        "document_editing_authorized": manifest["document_editing_authorized"],
        "entries": entries,
        "reference_hashes": references,
    }


if __name__ == "__main__":
    cli(LABEL, collect, validate)
