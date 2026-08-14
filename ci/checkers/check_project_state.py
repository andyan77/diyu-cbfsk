#!/usr/bin/env python3
"""State flags may be true only when a Founder signature authorizes that exact flag.

Before the signature this is indistinguishable from "everything must stay false"; after it,
the guard survives instead of having to be deleted. Two things are still unconditional:
red-line flags can never be authorized at all, and a waived review may never be recorded
as a completed one.
"""

from __future__ import annotations

import re
import sys

from _common import founder_ruling_evidence, ROOT, cli, docx_paragraph_texts, is_full_commit_hash, load_yaml, read_text

sys.path.insert(0, str(ROOT / "ci"))
from derived_state import derived_fields, hand_assigned_derived_fields  # noqa: E402

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


def _ruling_evidence_error(where: str, claim: dict) -> str | None:
    """NB-M2-01：引用的裁决必须真的存在，且具名条款要解析得出来。

    此前只看引用字符串非空——凭空写一个 DIYU-CBFSK-FOUNDER-M9-IMAGINARY-001 照样过关。
    引用里没有裁决编号的（如 prd_signature.founder_prd_decision=PASS）属回执内部字段引用，
    由签署回执自身守，不在此判。
    """
    if not claim.get("ruling_id"):
        return None
    if not claim.get("file_exists"):
        return (
            f"RULING_FILE_NOT_FOUND: {where} cites {claim['ruling_id']}, "
            f"but {claim.get('file')!r} does not exist"
        )

    if claim.get("kind") != "founder_ruling":
        return None
    if claim.get("clause_path") is None:
        return (
            f"RULING_CLAUSE_PATH_MISSING: {where} cites {claim['ruling_id']} without naming a clause path — "
            "指得出文件不等于文件里真有那一条"
        )
    if not claim.get("clause_resolves"):
        return (
            f"RULING_CLAUSE_NOT_FOUND: {where} cites {claim['ruling_id']} clause "
            f"{claim.get('clause_path')!r}, which the ruling file does not contain"
        )
    return None


STATE_BLOCK_RE = re.compile(r"## 当前项目状态\s*\n+```yaml\n(.*?)\n```", re.S)


def _yaml_state_block(text: str):
    """取「## 当前项目状态」下的 yaml 块，解析成 dict；找不到返回 None。

    README 与两份投影用同一个实现（EQ-1）——各写一份的结果是某一处的解析放宽了，
    而放宽的那一处正好是没有生成器守着的那一处。
    """
    match = STATE_BLOCK_RE.search(text)
    if match is None:
        return None
    out = {}
    for line in match.group(1).splitlines():
        if not line.strip() or ":" not in line:
            continue
        key, _, value = line.partition(":")
        value = value.strip()
        if value == "true":
            value = True
        elif value == "false":
            value = False
        out[key.strip()] = value
    return out


def validate(payload: dict) -> list[str]:
    errors: list[str] = []

    for claim in payload.get("ruling_claims") or []:
        error = _ruling_evidence_error(claim.get("where", "<unknown site>"), claim)
        if error:
            errors.append(error)

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

    # --- COND-GUARD-M2-01-3：README 状态块与规范源 project_state 比对 ---
    # 起因：README 状态块缺 m2_status，Guardian 是**读**出来的，不是判据抓到的。
    # 一份没有守卫的状态块，读者却当它是状态真源——那正是最危险的一种。
    if payload.get("readme_state_block_found") is not True:
        errors.append(
            "README_STATE_BLOCK_MISSING: README.md 找不到「## 当前项目状态」下的 yaml 状态块 —— "
            "读不到不等于没问题"
        )
    else:
        readme_state = payload.get("readme_state") or {}
        for key, value in sorted((payload.get("canonical_state") or {}).items()):
            if key not in readme_state:
                errors.append(
                    f"README_STATE_BLOCK_DRIFT: README 状态块缺 {key} —— 规范源写着 {value!r}"
                )
            elif readme_state[key] != value:
                errors.append(
                    f"README_STATE_BLOCK_DRIFT: README 状态块写 {key}={readme_state[key]!r}，"
                    f"规范源写 {value!r}"
                )

    # --- OI-SEAL-01-3：派生字段必须现算，手工赋值即失败 ---
    for name in payload.get("hand_assigned_derived_fields") or []:
        errors.append(
            f"DERIVED_FIELD_HAND_ASSIGNED: project_state 里手工写了派生字段 {name} —— "
            "能手填的派生字段不是派生字段，是又一个可以说谎的状态位"
        )
    for name, value in sorted((payload.get("derived_state") or {}).items()):
        for site, block in sorted((payload.get("projection_states") or {}).items()):
            if name not in block:
                errors.append(f"DERIVED_FIELD_MISCOMPUTED: {site} 状态块缺派生字段 {name}")
            elif block[name] != value:
                errors.append(
                    f"DERIVED_FIELD_MISCOMPUTED: {site} 写 {name}={block[name]!r}，现算值为 {value!r}"
                )

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
    product_truth = model["product_truth"]
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

    canonical_state = model["project_state"]
    derived = derived_fields(canonical_state)
    expected_block = {**canonical_state, **derived}
    readme_block = _yaml_state_block(readme)
    projection_states = {
        site: _yaml_state_block(read_text(site))
        for site in ("CLAUDE.md", "AGENTS.md")
    }
    projection_states = {k: v for k, v in projection_states.items() if v is not None}

    ruling_claims = []
    for name, auth in sorted(authorizations.items()):
        evidence = founder_ruling_evidence(auth.get("basis"), auth.get("ruling_clause_path"))
        evidence["where"] = f"state_flag_authorizations.flags.{name}"
        ruling_claims.append(evidence)
    value_basis = (
        ((signoff.get("state_flag_authorizations") or {}).get("execution_status") or {}).get("value_basis") or {}
    )
    for value, entry in sorted(value_basis.items()):
        evidence = founder_ruling_evidence(entry.get("ruling"), entry.get("ruling_clause_path"))
        evidence["where"] = f"state_flag_authorizations.execution_status.value_basis.{value}"
        ruling_claims.append(evidence)

    flags = {name: state[name] for name in GATED_FLAGS if name in state}
    flags["m0_execution_started"] = receipt["m0_execution_started"]
    flags["knowledge_distillation_started"] = receipt["knowledge_distillation_started"]
    flags["m1_started"] = model["project_state"]["m1_started"]
    flags["m2_started"] = model["project_state"]["m2_started"]

    return {
        "flags": flags,
        "authorizations": authorizations,
        "canonical_state": expected_block,
        "readme_state": readme_block,
        "readme_state_block_found": readme_block is not None,
        "derived_state": derived,
        "projection_states": projection_states,
        "hand_assigned_derived_fields": hand_assigned_derived_fields(canonical_state),
        "ruling_claims": ruling_claims,
        "never_authorizable_declared": (signoff.get("state_flag_authorizations") or {}).get(
            "never_authorizable"
        )
        or [],
        "execution_status": state["execution_status"],
        "execution_status_authorization": (signoff.get("state_flag_authorizations") or {}).get(
            "execution_status"
        )
        or {},
        # B-04-4：此前写死 False——「未签署的候选被当成活真源」这条判据因此永不触发。
        # 现由规范源 product_truth 现算：候选与活基线是同一份时不成立；分成两份而候选仍标生效时成立。
        "candidate_marked_as_effective_truth": (
            product_truth["candidate"] != product_truth["current_active"]
            and product_truth.get("candidate_effective") is True
        ),
        "forbidden_claim_hits": hits,
    }


if __name__ == "__main__":
    cli(LABEL, collect, validate)
