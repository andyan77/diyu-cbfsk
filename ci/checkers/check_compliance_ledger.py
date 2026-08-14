#!/usr/bin/env python3
"""Compliance items must be adjudicated one by one; no blanket self-assessment, no fake legal opinion."""

from __future__ import annotations

from _common import cli, load_yaml

LABEL = "check_compliance_ledger"

# 清单下限来自合规审查合同（PRD 10.4 第八道门 Safety & Compliance 的七项必答）。
# NB-M2-02：原先这个下限由 payload 传入，于是正例只要把它写成 2 就能用两条项目「通过」——
# 夹具把尺子改短了再量自己。下限从此只有这一个定义处，夹具改不动。
MINIMUM_ITEMS = 7
MINIMUM_ITEMS_SOURCE = "01_contracts_and_schemas/compliance_review_contract.v1.0.yaml"

REQUIRED_FIELDS = [
    "compliance_item_id",
    "issue",
    "applicable_stage",
    "founder_decision",
    "rationale",
    "evidence",
    "required_controls",
    "next_review_milestone",
    "decision_date",
    "external_legal_opinion_obtained",
]
ALLOWED_DECISIONS = {"ACCEPT", "MITIGATE", "DEFER", "BLOCK", "PENDING_FOUNDER_DECISION"}
DECIDED = {"ACCEPT", "MITIGATE", "DEFER", "BLOCK"}


def validate(payload: dict) -> list[str]:
    errors: list[str] = []

    if payload.get("blanket_self_assessment_allowed") is not False:
        errors.append("BLANKET_SELF_ASSESSMENT: per-item Founder decisions are mandatory")
    if payload.get("external_legal_opinion") is not False:
        errors.append("EXTERNAL_LEGAL_OPINION_CLAIMED: external_legal_opinion must be false")
    if payload.get("legal_review_type") != "founder_compliance_self_assessment":
        errors.append(f"LEGAL_REVIEW_TYPE: got {payload.get('legal_review_type')!r}")

    items = payload.get("items") or []
    if len(items) < MINIMUM_ITEMS:
        errors.append(
            f"INCOMPLETE_CHECKLIST: {len(items)} items, expected at least {MINIMUM_ITEMS} "
            f"（下限定义于 {MINIMUM_ITEMS_SOURCE}，不由 payload 传入）"
        )

    seen: set[str] = set()
    for item in items:
        iid = item.get("compliance_item_id", "<no id>")
        if iid in seen:
            errors.append(f"DUPLICATE_ITEM_ID: {iid}")
        seen.add(iid)
        for field in REQUIRED_FIELDS:
            if field not in item:
                errors.append(f"MISSING_FIELD: {iid}.{field}")
        decision = item.get("founder_decision")
        if decision not in ALLOWED_DECISIONS:
            errors.append(f"INVALID_DECISION: {iid} founder_decision={decision!r}")
        if decision in DECIDED:
            if not item.get("rationale"):
                errors.append(f"DECISION_WITHOUT_RATIONALE: {iid}")
            if not item.get("decision_date"):
                errors.append(f"DECISION_WITHOUT_DATE: {iid}")
        if item.get("external_legal_opinion_obtained") is True and not item.get("legal_opinion_reference"):
            errors.append(f"UNSUPPORTED_LEGAL_OPINION_CLAIM: {iid} claims a legal opinion without a reference")
        if not item.get("required_controls"):
            errors.append(f"MISSING_CONTROLS: {iid}")

    return errors


def collect() -> dict:
    ledger = load_yaml("governance/compliance/founder_compliance_decision_ledger.yaml")
    return {
        "blanket_self_assessment_allowed": ledger["blanket_self_assessment_allowed"],
        "external_legal_opinion": ledger["external_legal_opinion"],
        "legal_review_type": ledger["legal_review_type"],
        "items": ledger["items"],
    }


if __name__ == "__main__":
    cli(LABEL, collect, validate)
