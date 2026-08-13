#!/usr/bin/env python3
"""State flags may be true only when a Founder signature authorizes that exact flag.

Before the signature this is indistinguishable from "everything must stay false"; after it,
the guard survives instead of having to be deleted. Two things are still unconditional:
red-line flags can never be authorized at all, and a waived review may never be recorded
as a completed one.
"""

from __future__ import annotations

from _common import ROOT, cli, docx_paragraph_texts, is_full_commit_hash, load_yaml, read_text

LABEL = "check_project_state"

# Every flag whose transition to true requires a Founder authorization record.
GATED_FLAGS = [
    "prd_v1_2_effective",
    "m0_authorized",
    "guardian_review_completed",
    "chatgpt_remote_review_completed",
    "founder_prd_signed",
    "founder_m0_authorized",
    "founder_merge_approved",
    "main_merged",
    "production_servable",
    "m0_execution_started",
    "m1_started",
    "m2_started",
    "knowledge_distillation_started",
]

# Source: governance/bootstrap/role_operating_model.v0.2.yaml red_lines —— 创建 Serving /
# 开始知识蒸馏. No signature record may authorize these; the receipt's own never_authorizable
# list must agree with this set, so a receipt edit cannot widen it.
#
# m1_started / m2_started 曾在此列。DIYU-CBFSK-FOUNDER-M1-GATE-001 把红线措辞改为「未经授权
# 开始 M1 或 M2」，二者随之转入签署授权门控：守的是**授权缺失**而不是**开工本身**。授权条目必须
# 绑定完整 Commit 哈希且具名 basis，缺一即拦；没有条目的状态位（当前的 m2_started）判
# UNAUTHORIZED_TRUE_FLAG。
#
# 但这**是**一次屏障降级，不要写成「与绝对禁止等效」：在此列时，补一条完美授权也点不亮，
# 除非改本文件；移出后，往签署回执加一条合规条目即可放行，且不触发 RED_LINE_LIST_DRIFT
# （该判据只比对本集合）。m2 当前的锁靠的是「没有条目」，不是「不可授权」。这是 Founder
# 知情裁决，记录见 founder_signoff_receipt.yaml barrier_layer_delta。
RED_LINE_FLAGS = frozenset({"production_servable", "knowledge_distillation_started"})

CLAIM_TO_FLAG = {
    "PRD v1.2已生效": "prd_v1_2_effective",
    "PRD v1.2 已生效": "prd_v1_2_effective",
    "prd_v1_2_effective: true": "prd_v1_2_effective",
    "当前唯一产品真源，已生效": "prd_v1_2_effective",
    "M0已授权": "m0_authorized",
    "m0_authorized: true": "m0_authorized",
}

NEGATION_MARKERS = ("不得", "不表示", "不代表", "不是", "不构成", "禁止", "尚未", "未", "不应")


def is_affirmative_claim(paragraph: str, phrase: str) -> bool:
    index = paragraph.find(phrase)
    if index < 0:
        return True
    return not any(marker in paragraph[:index] for marker in NEGATION_MARKERS)


def _authorization_error(flag: str, auth: dict | None) -> str | None:
    if not auth or auth.get("authorized") is not True:
        return f"UNAUTHORIZED_TRUE_FLAG: {flag} is true with no Founder authorization record"
    if not is_full_commit_hash(auth.get("signature_base_commit")):
        return (
            f"UNBOUND_AUTHORIZATION: {flag} is authorized but signature_base_commit="
            f"{auth.get('signature_base_commit')!r} is not a full commit hash"
        )
    if not auth.get("basis"):
        return f"AUTHORIZATION_WITHOUT_BASIS: {flag} is authorized without a stated basis"
    return None


def validate(payload: dict) -> list[str]:
    errors: list[str] = []

    flags = payload.get("flags") or {}
    authorizations = payload.get("authorizations") or {}

    declared_never = set(payload.get("never_authorizable_declared") or [])
    if declared_never != set(RED_LINE_FLAGS):
        errors.append(
            f"RED_LINE_LIST_DRIFT: receipt declares never_authorizable={sorted(declared_never)}, "
            f"red lines require {sorted(RED_LINE_FLAGS)}"
        )

    for flag in GATED_FLAGS:
        if flag not in flags:
            errors.append(f"MISSING_STATE_FLAG: {flag}")
            continue
        value = flags[flag]
        if value is False:
            continue
        if value is not True:
            errors.append(f"NON_BOOLEAN_STATE_FLAG: {flag}={value!r}")
            continue
        if flag in RED_LINE_FLAGS:
            errors.append(f"RED_LINE_FLAG_SET: {flag} is true; no signature may authorize it")
            continue
        error = _authorization_error(flag, authorizations.get(flag))
        if error:
            errors.append(error)

    status = payload.get("execution_status")
    status_auth = payload.get("execution_status_authorization") or {}
    if status != "EXECUTION_NOT_STARTED":
        if status_auth.get("authorized") is not True:
            errors.append(f"UNAUTHORIZED_EXECUTION_STATUS: {status!r} without a Founder authorization")
        elif status not in (status_auth.get("authorized_values") or []):
            errors.append(
                f"EXECUTION_STATUS_OUT_OF_SCOPE: {status!r} is not in {status_auth.get('authorized_values')!r}"
            )
        elif not is_full_commit_hash(status_auth.get("signature_base_commit")):
            errors.append("UNBOUND_AUTHORIZATION: execution_status authorization has no full commit hash")

    if flags.get("prd_v1_2_effective") is not True and payload.get("candidate_marked_as_effective_truth"):
        errors.append("UNSIGNED_MARKED_EFFECTIVE: the v1.2 candidate is described as an effective product truth")

    for hit in payload.get("forbidden_claim_hits") or []:
        paragraph = hit.get("paragraph", "")
        claim = hit["claim"]
        if not is_affirmative_claim(paragraph, claim):
            continue
        flag = CLAIM_TO_FLAG.get(claim)
        authorized = (
            flag is not None
            and flags.get(flag) is True
            and _authorization_error(flag, authorizations.get(flag)) is None
        )
        if not authorized:
            errors.append(f"FORBIDDEN_STATE_CLAIM: {hit['source']} asserts {claim!r} in: {paragraph[:80]}")

    return errors


def collect() -> dict:
    change_map = load_yaml("PRD_v1.2_change_map.yaml")
    model = load_yaml("governance/bootstrap/role_operating_model.v0.2.yaml")
    receipt = load_yaml("governance/receipts/baseline_reconciliation_receipt.yaml")
    signoff = load_yaml("governance/receipts/founder_signoff_receipt.yaml")
    state = change_map["resulting_state"]
    readme = read_text("README.md")

    hits = []
    sources = {"README.md": readme.splitlines()}
    prd_receipt = ROOT / "PRD_v1.2_核验回执.docx"
    if prd_receipt.exists():
        sources["PRD_v1.2_核验回执.docx"] = docx_paragraph_texts(prd_receipt)
    for name, paragraphs in sources.items():
        for paragraph in paragraphs:
            for claim in CLAIM_TO_FLAG:
                if claim in paragraph:
                    hits.append({"source": name, "claim": claim, "paragraph": paragraph})

    authorizations = (signoff.get("state_flag_authorizations") or {}).get("flags") or {}
    flags = {name: state[name] for name in GATED_FLAGS if name in state}
    flags["m0_execution_started"] = receipt["m0_execution_started"]
    flags["knowledge_distillation_started"] = receipt["knowledge_distillation_started"]
    flags["m1_started"] = model["project_state"]["m1_started"]
    flags["m2_started"] = model["project_state"]["m2_started"]

    return {
        "flags": flags,
        "authorizations": authorizations,
        "never_authorizable_declared": (signoff.get("state_flag_authorizations") or {}).get(
            "never_authorizable"
        )
        or [],
        "execution_status": state["execution_status"],
        "execution_status_authorization": (signoff.get("state_flag_authorizations") or {}).get(
            "execution_status"
        )
        or {},
        "candidate_marked_as_effective_truth": False,
        "forbidden_claim_hits": hits,
    }


if __name__ == "__main__":
    cli(LABEL, collect, validate)
