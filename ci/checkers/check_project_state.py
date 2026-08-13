#!/usr/bin/env python3
"""Project state flags must all stay false until the corresponding Founder decision exists."""

from __future__ import annotations

from _common import ROOT, cli, docx_paragraph_texts, load_yaml, read_text

LABEL = "check_project_state"

MUST_BE_FALSE = [
    "prd_v1_2_effective",
    "m0_authorized",
    "guardian_review_completed",
    "chatgpt_remote_review_completed",
    "founder_prd_signed",
    "founder_m0_authorized",
    "founder_merge_approved",
    "main_merged",
    "production_servable",
]

FORBIDDEN_EFFECTIVE_CLAIMS = [
    "PRD v1.2已生效",
    "PRD v1.2 已生效",
    "prd_v1_2_effective: true",
    "当前唯一产品真源，已生效",
    "M0已授权",
    "m0_authorized: true",
]


NEGATION_MARKERS = ("不得", "不表示", "不代表", "不是", "不构成", "禁止", "尚未", "未", "不应")


def is_affirmative_claim(paragraph: str, phrase: str) -> bool:
    index = paragraph.find(phrase)
    if index < 0:
        return True
    return not any(marker in paragraph[:index] for marker in NEGATION_MARKERS)


def validate(payload: dict) -> list[str]:
    errors: list[str] = []

    flags = payload.get("flags") or {}
    for key in MUST_BE_FALSE:
        if key not in flags:
            errors.append(f"MISSING_STATE_FLAG: {key}")
        elif flags[key] is not False:
            errors.append(f"PREMATURE_TRUE_FLAG: {key}={flags[key]!r}, must stay false")

    if flags.get("prd_v1_2_effective") is False and payload.get("candidate_marked_as_effective_truth"):
        errors.append("UNSIGNED_MARKED_EFFECTIVE: the v1.2 candidate is described as an effective product truth")

    for hit in payload.get("forbidden_claim_hits") or []:
        paragraph = hit.get("paragraph", "")
        if is_affirmative_claim(paragraph, hit["claim"]):
            errors.append(f"FORBIDDEN_STATE_CLAIM: {hit['source']} asserts {hit['claim']!r} in: {paragraph[:80]}")

    if payload.get("execution_status") != "EXECUTION_NOT_STARTED":
        errors.append(f"EXECUTION_STATUS: expected EXECUTION_NOT_STARTED, got {payload.get('execution_status')!r}")

    for started in ("m0_execution_started", "m1_started", "m2_started", "knowledge_distillation_started"):
        if payload.get(started) is not False:
            errors.append(f"MILESTONE_STARTED: {started} must be false")

    return errors


def collect() -> dict:
    change_map = load_yaml("PRD_v1.2_change_map.yaml")
    model = load_yaml("governance/bootstrap/role_operating_model.v0.2.yaml")
    receipt = load_yaml("governance/receipts/baseline_reconciliation_receipt.yaml")
    state = change_map["resulting_state"]
    readme = read_text("README.md")

    hits = []
    sources = {"README.md": readme.splitlines()}
    prd_receipt = ROOT / "PRD_v1.2_核验回执.docx"
    if prd_receipt.exists():
        sources["PRD_v1.2_核验回执.docx"] = docx_paragraph_texts(prd_receipt)
    for name, paragraphs in sources.items():
        for paragraph in paragraphs:
            for claim in FORBIDDEN_EFFECTIVE_CLAIMS:
                if claim in paragraph:
                    hits.append({"source": name, "claim": claim, "paragraph": paragraph})

    return {
        "flags": {
            "prd_v1_2_effective": state["prd_v1_2_effective"],
            "m0_authorized": state["m0_authorized"],
            "guardian_review_completed": state["guardian_review_completed"],
            "chatgpt_remote_review_completed": state["chatgpt_remote_review_completed"],
            "founder_prd_signed": state["founder_prd_signed"],
            "founder_m0_authorized": state["founder_m0_authorized"],
            "founder_merge_approved": state["founder_merge_approved"],
            "main_merged": state["main_merged"],
            "production_servable": state["production_servable"],
        },
        "execution_status": state["execution_status"],
        "m0_execution_started": receipt["m0_execution_started"],
        "m1_started": model["project_state"]["m1_started"],
        "m2_started": model["project_state"]["m2_started"],
        "knowledge_distillation_started": receipt["knowledge_distillation_started"],
        "candidate_marked_as_effective_truth": False,
        "forbidden_claim_hits": hits,
    }


if __name__ == "__main__":
    cli(LABEL, collect, validate)
