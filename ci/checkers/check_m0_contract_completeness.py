#!/usr/bin/env python3
"""M0 通过标准第一条：所有支持任务都有必需输入、输出、失败状态和负责角色。

PRD 13 节 M0 的通过标准是一句自然语言。它在这里变成一条可执行判据：每份 M0 合同里的每条
obligation 都必须四样俱全 —— required_inputs / outputs / failure_state / owner_role ——
并且 owner_role 必须是规范源里真实存在的角色，failure_state 必须是可被引用的具名状态，
而不是一句散文。四样缺一，M0 范围与角色门就不算过。
"""

from __future__ import annotations

import re

from _common import ROOT, cli, is_full_commit_hash, load_yaml

LABEL = "check_m0_contract_completeness"

REQUIRED_OBLIGATION_FIELDS = ("statement", "required_inputs", "outputs", "failure_state", "owner_role")

FAILURE_STATE_RE = re.compile(r"[A-Z][A-Z0-9_]{4,}")

M0_CONTRACT_PATHS = (
    "00_charter/project_charter.v1.0.yaml",
    "01_contracts_and_schemas/capability_contract.v1.0.yaml",
    "01_contracts_and_schemas/category_scope_contract.v1.0.yaml",
    "01_contracts_and_schemas/input_output_boundary.v1.0.yaml",
    "01_contracts_and_schemas/role_and_decision_rights.v1.0.yaml",
    "01_contracts_and_schemas/non_goals_and_stop_conditions.v1.0.yaml",
    "01_contracts_and_schemas/knowledge_state_machine.v1.0.yaml",
    "01_contracts_and_schemas/architecture_and_integration_boundary.v1.0.yaml",
    "01_contracts_and_schemas/compliance_review_contract.v1.0.yaml",
    "01_contracts_and_schemas/data_and_fixture_workflow.v1.0.yaml",
    "01_contracts_and_schemas/execution_critical_path_and_decision_gates.v1.0.yaml",
)

# 章程原文：「冻结时点＝Founder M0 裁决」。所以「已冻结/已接受」不是永远禁止，而是**裁决前**禁止；
# 裁决为 PASS 之后，继续挂 PENDING 反而是过期的假话。两个方向都要判，判据才不是单向的。
PENDING_DECISION_STATUS = "M0_CANDIDATE_PENDING_FOUNDER_M0_DECISION"
FORBIDDEN_BEFORE_M0_DECISION = ("FROZEN", "ACCEPTED", "FOUNDER_ACCEPTED")
# 这两条与 M0 裁决无关：M0 通过不等于合同生效，更不等于可服务生产。任何时候都不得自称。
FORBIDDEN_ALWAYS = ("PRODUCTION_SERVABLE", "EFFECTIVE")


def _declares(status: str, word: str) -> bool:
    return status == word or status.endswith(f"_{word}")


def validate(payload: dict) -> list[str]:
    errors: list[str] = []

    known_roles = set(payload.get("known_roles") or [])
    if not known_roles:
        errors.append("NO_KNOWN_ROLES: the canonical role source produced no role list")

    # 冻结授权只认一个来源：Founder M0 裁决，且该裁决升级为 PASS 的依据必须绑定 Guardian
    # delta 复核的完整 Commit 哈希。没绑哈希的 PASS 一律当作「尚未裁决」处理。
    decision = payload.get("founder_m0_decision") or {}
    m0_passed = decision.get("value") == "PASS"
    if m0_passed and not is_full_commit_hash(decision.get("guardian_delta_review_commit")):
        errors.append(
            "UNBOUND_M0_DECISION: founder_m0_decision=PASS but guardian_delta_review_commit="
            f"{decision.get('guardian_delta_review_commit')!r} is not a full commit hash"
        )
        m0_passed = False

    contracts = payload.get("contracts") or []
    expected = payload.get("expected_contract_count")
    if expected is not None and len(contracts) != expected:
        errors.append(f"CONTRACT_SET_INCOMPLETE: {len(contracts)} contracts loaded, expected {expected}")

    seen_ids: set[str] = set()
    for contract in contracts:
        path = contract.get("path", "<no path>")
        if not contract.get("present"):
            errors.append(f"MISSING_M0_CONTRACT: {path}")
            continue

        contract_id = contract.get("contract_id")
        if not contract_id:
            errors.append(f"CONTRACT_WITHOUT_ID: {path}")
        elif contract_id in seen_ids:
            errors.append(f"DUPLICATE_CONTRACT_ID: {contract_id}")
        else:
            seen_ids.add(contract_id)

        if not contract.get("prd_anchors"):
            errors.append(f"CONTRACT_WITHOUT_PRD_ANCHOR: {path}")

        status = contract.get("status") or ""
        for forbidden in FORBIDDEN_ALWAYS:
            if _declares(status, forbidden):
                errors.append(f"OVERREACHING_STATUS_CLAIM: {path} declares status={status!r}")
        if m0_passed:
            if status == PENDING_DECISION_STATUS:
                errors.append(
                    f"STALE_PENDING_STATUS: {path} still declares status={status!r} after the Founder "
                    "M0 decision took effect as PASS"
                )
        else:
            for forbidden in FORBIDDEN_BEFORE_M0_DECISION:
                if _declares(status, forbidden):
                    errors.append(
                        f"PREMATURE_FROZEN_CLAIM: {path} declares status={status!r} before the Founder M0 decision"
                    )

        obligations = contract.get("obligations") or []
        if not obligations:
            errors.append(f"CONTRACT_WITHOUT_OBLIGATIONS: {path} defines no supporting task")
            continue

        for obligation in obligations:
            oid = obligation.get("id") or "<no id>"
            where = f"{path}:{oid}"
            for field in REQUIRED_OBLIGATION_FIELDS:
                value = obligation.get(field)
                if value in (None, "", [], {}):
                    errors.append(f"OBLIGATION_FIELD_MISSING: {where}.{field}")
            for list_field in ("required_inputs", "outputs"):
                value = obligation.get(list_field)
                if value is not None and not isinstance(value, list):
                    errors.append(f"OBLIGATION_FIELD_NOT_A_LIST: {where}.{list_field}")

            failure_state = obligation.get("failure_state")
            if isinstance(failure_state, str) and not FAILURE_STATE_RE.fullmatch(failure_state):
                errors.append(
                    f"FAILURE_STATE_NOT_NAMED: {where}.failure_state={failure_state!r} is prose, not a named state"
                )

            owner = obligation.get("owner_role")
            if isinstance(owner, str) and owner not in known_roles:
                errors.append(f"OWNER_ROLE_UNKNOWN: {where}.owner_role={owner!r} is not a role in the canonical source")

    return errors


def collect() -> dict:
    model = load_yaml("governance/bootstrap/role_operating_model.v0.2.yaml")
    # 角色名只有一个来源：规范源。常规角色在 roles 里，应急写入者只登记在角色不可用回退块里，
    # 两处都要取，否则 §11.3 指派的临时写入者会被误判为「不存在的角色」。
    known_roles = {role["role_id"] for role in model["roles"]}
    fallback = model.get("role_unavailability_fallback") or {}
    for entry in fallback.values():
        if isinstance(entry, dict) and entry.get("emergency_role_id"):
            known_roles.add(entry["emergency_role_id"])

    contracts = []
    for rel in M0_CONTRACT_PATHS:
        path = ROOT / rel
        entry: dict = {"path": rel, "present": path.exists()}
        if path.exists():
            data = load_yaml(rel)
            entry.update(
                {
                    "contract_id": data.get("contract_id"),
                    "prd_anchors": data.get("prd_anchors"),
                    "status": data.get("status"),
                    "obligations": data.get("obligations"),
                }
            )
        contracts.append(entry)

    receipt = load_yaml("11_reports_and_receipts/m0_delivery_receipt.yaml")

    return {
        "known_roles": sorted(known_roles),
        "contracts": contracts,
        "expected_contract_count": len(M0_CONTRACT_PATHS),
        "founder_m0_decision": receipt.get("founder_m0_decision_effective") or {},
    }


if __name__ == "__main__":
    cli(LABEL, collect, validate)
