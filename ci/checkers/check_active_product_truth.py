#!/usr/bin/env python3
"""Exactly one active product truth; v1.1 must not be archived before v1.2 is effective."""

from __future__ import annotations

from _common import ROOT, cli, load_yaml, read_text

LABEL = "check_active_product_truth"

FORBIDDEN_README_CLAIMS = [
    "v1.2` | 产品合同、范围、里程碑与验收门 | **当前唯一产品真源",
    "PRD v1.2 是当前唯一产品真源",
    "v1.2 已生效",
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

    if payload.get("active_status") != "PENDING_FOUNDER_SIGNATURE":
        errors.append(
            f"ACTIVE_BASELINE_STATUS: expected PENDING_FOUNDER_SIGNATURE, got {payload.get('active_status')!r}"
        )

    if payload.get("candidate_effective") is not False:
        errors.append("CANDIDATE_MARKED_EFFECTIVE: prd_v1_2_effective must stay false until Founder signature")

    if payload.get("candidate_effective") is False and payload.get("archive_v1_1_exists"):
        errors.append(
            "PREMATURE_ARCHIVE: 归档_v1.1/ exists while prd_v1_2_effective=false (red line: 在 v1.2 生效前归档 v1.1)"
        )

    for name in payload.get("active_baseline_files_expected_at_root") or []:
        if name not in (payload.get("root_files") or []):
            errors.append(f"ACTIVE_BASELINE_MISPLACED: {name} is not at repository root")

    for claim in payload.get("forbidden_claims_found") or []:
        errors.append(f"FORBIDDEN_TRUTH_CLAIM: README contains {claim!r}")

    return errors


def collect() -> dict:
    change_map = load_yaml("PRD_v1.2_change_map.yaml")
    model = load_yaml("governance/bootstrap/role_operating_model.v0.2.yaml")
    readme = read_text("README.md")

    truth = model["product_truth"]
    declared = []
    if "**当前活基线 · `PENDING_FOUNDER_SIGNATURE`**" in readme:
        declared.append(truth["current_active"])

    return {
        "expected_active": truth["current_active"],
        "files_declaring_sole_product_truth": declared,
        "active_status": change_map["resulting_state"]["current_active_baseline_status"],
        "candidate_effective": change_map["resulting_state"]["prd_v1_2_effective"],
        "archive_v1_1_exists": (ROOT / "归档_v1.1").exists(),
        "root_files": sorted(p.name for p in ROOT.iterdir() if p.is_file()),
        "active_baseline_files_expected_at_root": [
            "笛语跨品牌服装搭配专家内核_PRD与执行里程碑_v1.1.docx",
            "笛语跨品牌服装搭配专家内核_M0执行申请_v1.1.docx",
            "PRD_v1.1_核验回执.docx",
        ],
        "forbidden_claims_found": [c for c in FORBIDDEN_README_CLAIMS if c in readme],
    }


if __name__ == "__main__":
    cli(LABEL, collect, validate)
