#!/usr/bin/env python3
"""Exactly one active product truth, and the switch to v1.2 only after a Founder signature.

The red line 「v1.2 生效前归档 v1.1」 is unchanged. What the signature adds is a legal path:
once the signature record authorizes it, v1.2 may become the active truth and v1.1 may be
archived. The window between "signed" and "switched" is not silently tolerated —— it must be
declared in the signature receipt, so a half-finished switch cannot masquerade as a finished one.
"""

from __future__ import annotations

from _common import ROOT, cli, is_full_commit_hash, load_yaml, read_text

LABEL = "check_active_product_truth"

ACTIVE_MARKER = "**当前活基线 · `{status}`**"

# Claims that are false —— and therefore forbidden —— until v1.2 is actually effective.
CONDITIONAL_README_CLAIMS = [
    "v1.2` | 产品合同、范围、里程碑与验收门 | **当前唯一产品真源",
    "PRD v1.2 是当前唯一产品真源",
    "v1.2 已生效",
]

V1_1_FILES = [
    "笛语跨品牌服装搭配专家内核_PRD与执行里程碑_v1.1.docx",
    "笛语跨品牌服装搭配专家内核_M0执行申请_v1.1.docx",
    "PRD_v1.1_核验回执.docx",
]
V1_2_FILES = [
    "笛语跨品牌服装搭配专家内核_PRD与执行里程碑_v1.2.docx",
    "笛语跨品牌服装搭配专家内核_M0执行申请_v1.2.docx",
    "PRD_v1.2_核验回执.docx",
]


def validate(payload: dict) -> list[str]:
    errors: list[str] = []

    declared = payload.get("files_declaring_sole_product_truth") or []
    if len(declared) != 1:
        errors.append(
            f"DUAL_ACTIVE_PRODUCT_TRUTH: {len(declared)} file(s) declare sole product truth: {declared}"
        )
    elif declared[0] != payload.get("expected_active"):
        errors.append(
            f"WRONG_ACTIVE_PRODUCT_TRUTH: {declared[0]} declared active, expected {payload.get('expected_active')}"
        )

    signature = payload.get("active_baseline_signature") or {}
    status = payload.get("active_status")
    if status != "PENDING_FOUNDER_SIGNATURE":
        if signature.get("authorized") is not True:
            errors.append(f"UNAUTHORIZED_BASELINE_STATUS: {status!r} without a Founder signature record")
        elif status not in (signature.get("authorized_status_values") or []):
            errors.append(
                f"BASELINE_STATUS_OUT_OF_SCOPE: {status!r} not in {signature.get('authorized_status_values')!r}"
            )
        elif not is_full_commit_hash(signature.get("signature_base_commit")):
            errors.append("UNBOUND_AUTHORIZATION: baseline signature record has no full commit hash")

    effective = payload.get("candidate_effective")
    if effective is True and signature.get("authorized") is not True:
        errors.append("CANDIDATE_MARKED_EFFECTIVE: prd_v1_2_effective is true without a Founder signature")

    if effective is not True and payload.get("archive_v1_1_exists"):
        errors.append(
            "PREMATURE_ARCHIVE: 归档_v1.1/ exists while prd_v1_2_effective=false (red line: 在 v1.2 生效前归档 v1.1)"
        )

    # Signed but not yet switched is a legal, ordered step —— and must be declared as such.
    switched = payload.get("active_baseline_is_candidate")
    if effective is True and not switched and not payload.get("pending_active_baseline_switch"):
        errors.append(
            "SIGNED_BUT_NOT_SWITCHED: v1.2 is effective while v1.1 is still the active truth, "
            "and the signature receipt does not declare pending_active_baseline_switch"
        )
    if switched and payload.get("pending_active_baseline_switch"):
        errors.append(
            "STALE_PENDING_SWITCH: the active truth is already v1.2 but the receipt still declares the switch pending"
        )
    if switched and not payload.get("archive_v1_1_exists"):
        errors.append("SWITCHED_WITHOUT_ARCHIVE: v1.2 is the active truth but 归档_v1.1/ does not exist")

    root_files = payload.get("root_files") or []
    for name in payload.get("active_baseline_files_expected_at_root") or []:
        if name not in root_files:
            errors.append(f"ACTIVE_BASELINE_MISPLACED: {name} is not at repository root")
    for name in payload.get("files_expected_out_of_root") or []:
        if name in root_files:
            errors.append(f"SUPERSEDED_BASELINE_STILL_AT_ROOT: {name} must live under 归档_v1.1/")

    for claim in payload.get("conditional_claims_found") or []:
        if effective is not True:
            errors.append(f"FORBIDDEN_TRUTH_CLAIM: README contains {claim!r} while v1.2 is not effective")

    return errors


def collect() -> dict:
    change_map = load_yaml("PRD_v1.2_change_map.yaml")
    model = load_yaml("governance/bootstrap/role_operating_model.v0.2.yaml")
    signoff = load_yaml("governance/receipts/founder_signoff_receipt.yaml")
    readme = read_text("README.md")

    truth = model["product_truth"]
    state = change_map["resulting_state"]
    status = state["current_active_baseline_status"]
    active_is_candidate = truth["current_active"] == truth["candidate"]

    declared = []
    if ACTIVE_MARKER.format(status=status) in readme:
        declared.append(truth["current_active"])

    return {
        "expected_active": truth["current_active"],
        "files_declaring_sole_product_truth": declared,
        "active_status": status,
        "candidate_effective": state["prd_v1_2_effective"],
        "active_baseline_is_candidate": active_is_candidate,
        "pending_active_baseline_switch": signoff.get("pending_active_baseline_switch", False),
        "active_baseline_signature": (signoff.get("state_flag_authorizations") or {}).get(
            "active_baseline_signature"
        )
        or {},
        "archive_v1_1_exists": (ROOT / "归档_v1.1").exists(),
        "root_files": sorted(p.name for p in ROOT.iterdir() if p.is_file()),
        "active_baseline_files_expected_at_root": V1_2_FILES if active_is_candidate else V1_1_FILES,
        "files_expected_out_of_root": V1_1_FILES if active_is_candidate else [],
        "conditional_claims_found": [c for c in CONDITIONAL_README_CLAIMS if c in readme],
    }


if __name__ == "__main__":
    cli(LABEL, collect, validate)
