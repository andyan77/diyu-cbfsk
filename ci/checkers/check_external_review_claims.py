#!/usr/bin/env python3
"""No AI review may be dressed up as external expert review, nor Founder self-assessment as legal opinion."""

from __future__ import annotations

from _common import ROOT, cli, docx_paragraph_texts, load_yaml

LABEL = "check_external_review_claims"

# 只有「肯定性主张」才算违规。文档里明确禁止/否认这些说法的句子是合规内容，不得误判。
NEGATION_MARKERS = ("不得", "不表示", "不代表", "不是", "不构成", "禁止", "不冒充", "不应", "不自动", "不能")

FORBIDDEN_PHRASES = [
    "外部专家通过率",
    "外部专家共识",
    "外部专家已参与",
    "外部专家审查完成",
    "律师意见",
    "法律意见书",
    "独立法律意见",
    "已获外部法律核验",
    "匹配品类专家通过率",
]

REQUIRED_METRICS = [
    "internal_review_panel_pass_rate",
    "ai_reviewer_disagreement_rate",
    "founder_override_rate",
    "founder_sample_review_rate",
    "high_risk_founder_full_review_rate",
]


def is_affirmative_claim(paragraph: str, phrase: str) -> bool:
    """True when the phrase is asserted, False when the sentence forbids or denies it."""
    index = paragraph.find(phrase)
    if index < 0:
        return True
    return not any(marker in paragraph[:index] for marker in NEGATION_MARKERS)


def validate(payload: dict) -> list[str]:
    errors: list[str] = []

    for hit in payload.get("forbidden_phrase_hits") or []:
        paragraph = hit.get("paragraph", "")
        if is_affirmative_claim(paragraph, hit["phrase"]):
            errors.append(
                f"FALSE_EXTERNAL_REVIEW_CLAIM: {hit['source']} asserts {hit['phrase']!r} in: {paragraph[:80]}"
            )

    for metric in REQUIRED_METRICS:
        if metric not in (payload.get("metrics_present") or []):
            errors.append(f"MISSING_REVIEW_METRIC: {metric}")

    flags = payload.get("flags") or {}
    for key in ("external_human_review", "external_legal_opinion", "independent_external_validation_completed"):
        if flags.get(key) is not False:
            errors.append(f"OVERCLAIMED_FLAG: {key} must be false, got {flags.get(key)!r}")

    if payload.get("domain_review_type") != "founder_self_review_with_ai_adversarial_support":
        errors.append(f"DOMAIN_REVIEW_TYPE: got {payload.get('domain_review_type')!r}")
    if payload.get("legal_review_type") != "founder_compliance_self_assessment":
        errors.append(f"LEGAL_REVIEW_TYPE: got {payload.get('legal_review_type')!r}")

    for claim in payload.get("ai_review_claims") or []:
        if claim.get("reviewer_is_ai") and claim.get("presented_as") == "external_expert":
            errors.append(f"AI_PRESENTED_AS_EXTERNAL_EXPERT: {claim.get('claim_id')}")
        if claim.get("reviewer_is_founder") and claim.get("presented_as") == "legal_opinion":
            errors.append(f"FOUNDER_SELF_ASSESSMENT_PRESENTED_AS_LEGAL_OPINION: {claim.get('claim_id')}")

    return errors


def collect() -> dict:
    model = load_yaml("governance/bootstrap/role_operating_model.v0.2.yaml")
    review = model["review_mode"]

    sources = {
        "PRD_v1.2": ROOT / "笛语跨品牌服装搭配专家内核_PRD与执行里程碑_v1.2.docx",
        "M0_v1.2": ROOT / "笛语跨品牌服装搭配专家内核_M0执行申请_v1.2.docx",
        "RECEIPT_v1.2": ROOT / "PRD_v1.2_核验回执.docx",
    }
    hits = []
    prd_text = ""
    for name, path in sources.items():
        if not path.exists():
            continue
        paragraphs = docx_paragraph_texts(path)
        if name == "PRD_v1.2":
            prd_text = "\n".join(paragraphs)
        for paragraph in paragraphs:
            for phrase in FORBIDDEN_PHRASES:
                if phrase in paragraph:
                    hits.append({"source": name, "phrase": phrase, "paragraph": paragraph})

    metrics_present = [m for m in REQUIRED_METRICS if m in prd_text]

    return {
        "forbidden_phrase_hits": hits,
        "metrics_present": metrics_present,
        "flags": {
            "external_human_review": review["external_human_review"],
            "external_legal_opinion": review["external_legal_opinion"],
            "independent_external_validation_completed": review["independent_external_validation_completed"],
        },
        "domain_review_type": review["domain_review_type"],
        "legal_review_type": review["legal_review_type"],
        "ai_review_claims": [],
    }


if __name__ == "__main__":
    cli(LABEL, collect, validate)
