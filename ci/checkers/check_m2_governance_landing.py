#!/usr/bin/env python3
"""M2 治理落盘完整性：裁决原文、六份 ADR、层映射、结束状态与注册齐备。

覆盖启动包 v1.1 的 Phase 0 / 1 / 3 / 6 落点：

  裁决原文不可静默改写 —— 章程 verbatim 指纹与声明值比对（M2_CHARTER_VERBATIM_DRIFT）。
  ADR 必须是最小 ADR   —— 六份齐、题目与章程一致、四条声明（最小实现／落地里程碑／
                          当前不建设／激活条件）逐份非空；ADR-004 激活条件必须是「永不」。
  分层不得改动 M1      —— 层映射与 M1 覆盖映射表双向比对：多一个是凭空造对象，少一个是漏映射。
  状态位说真话         —— EP01 结束状态块与规范源 project_state 逐项对齐。
  判据必须真的会跑     —— 所有 check_m2_* 必须在 run_all_checks 注册表内。

反自审绿（E12）：ADR 题目的真值取自 Founder 章程的 adr_titles，对象清单的真值取自 M1 覆盖映射表，
状态位真值取自 role_operating_model——都不从被检对象自己读。
"""

from __future__ import annotations

import re

from _common import ROOT, cli, is_full_commit_hash, load_yaml, read_text, sha256_text

import yaml

LABEL = "check_m2_governance_landing"

CHARTER = "governance/founder_rulings/DIYU-CBFSK-FOUNDER-M2-CHARTER-001.yaml"
CALIBRATION_RULING = "governance/founder_rulings/DIYU-CBFSK-FR-CALIBRATION-004.yaml"
SIGNATURE_RECEIPT = "governance/receipts/founder_m2_kickoff_signature_receipt.yaml"
ROLE_MODEL = "governance/bootstrap/role_operating_model.v0.2.yaml"
COVERAGE_MAP = "01_contracts_and_schemas/m1_object_model/object_coverage_map.v0.1.yaml"
LAYER_MAP = "03_m2_evaluation_foundation/architecture/m1_object_layer_map.v0.1.yaml"
COMMERCIAL = "03_m2_evaluation_foundation/commercial_decision_record.v0.1.yaml"
COMPETITIVE = "03_m2_evaluation_foundation/competitive_evidence_policy.v0.1.yaml"
RECEIPT_ROOT = ROOT / "11_reports_and_receipts"
MANIFEST = "11_reports_and_receipts/m2_ep01/m2_ep01_task_manifest.yaml"
ADR_DIR = ROOT / "03_m2_evaluation_foundation" / "adr"
CHECKER_DIR = ROOT / "ci" / "checkers"
REGISTRY = "ci/run_all_checks.py"

SIGNED_BASELINE_COMMIT = "6499431c66f7bf4a234bd830ee4c810e1ac78694"

ADR_IDS = tuple(f"ADR-{n:03d}" for n in range(1, 7))

# 启动包 v1.1 Phase 3：每份 ADR 必须声明的四条。
ADR_REQUIRED_DECLARATIONS = (
    "minimal_implementation",
    "landing_milestone",
    "not_building_now",
    "activation_condition",
)

# 启动包 v1.1 §2 EP01 结束状态块。写死在这里是判据的一部分，不是魔法常量：
# 它就是 Founder 签署时约定的收尾状态，改它必须改本文件并具名裁决。
# 每个执行包收尾时约定的状态块。**只有标记 describes_current_state 的那一份**要与规范源比对；
# 已被后续包取代的历史块保持原样不改写——改写它等于篡改当时的如实记录，
# 只要求它显式标出 superseded_by。这是 EP02 受控合并时的结构性修复：
# 原实现把「EP01 的收尾态」当成「永远的当前态」，M1 收口后必然自相矛盾（EQ-5：先消除结构缺陷再往下走）。
REQUIRED_END_STATE_BY_PACKAGE = {
    "M2-EP01": {
        "execution_status": "M1_M2_PARALLEL_IN_PROGRESS",
        "m2_started": True,
        "m2_ep01_status": "SELF_CHECKED",
        "m2_evaluation_profile_status": "PROVISIONAL_READY",
        "m2_benchmark_assets_status": "NOT_CREATED",
        "m2_hidden_assets_status": "NOT_CREATED",
        "m2_frozen": False,
        "m1_final_binding": "PENDING_M1_CLOSEOUT",
        "knowledge_distillation_started": False,
        "production_servable": False,
        "next_authorized_action": "WAIT_FOR_M1_CLOSEOUT_AND_M2_EP02_PROMPT",
    },
}

# 无论哪个包、无论当前还是历史，这几位都不许为真——它们是红线，不随包的推进而松动。
ALWAYS_FALSE_IN_END_STATE = ("m2_frozen", "knowledge_distillation_started", "production_servable")

# 商业形态裁决前不得建设的三项。
COMMERCIAL_MUST_NOT_BUILD = ("Billing", "开发者门户", "Marketplace")

FRONT_MATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)


def validate(payload: dict) -> list[str]:
    errors: list[str] = []

    # --- 裁决原文 ---
    if payload.get("charter_declared_digest") != payload.get("charter_actual_digest"):
        errors.append(
            f"M2_CHARTER_VERBATIM_DRIFT: charter pins {payload.get('charter_declared_digest')!r}, "
            f"the ruling text hashes to {payload.get('charter_actual_digest')!r}"
        )
    if payload.get("charter_transcription_only") is not True:
        errors.append("M2_CHARTER_VERBATIM_DRIFT: charter does not declare transcription_only")
    for name, commit in sorted((payload.get("baseline_commits") or {}).items()):
        if not is_full_commit_hash(commit):
            errors.append(f"SOURCE_COMMIT_NOT_FULL_HASH: {name}={commit!r}")
        elif commit != SIGNED_BASELINE_COMMIT:
            errors.append(
                f"BASELINE_BINDING_MISMATCH: {name}={commit!r}, signed baseline is {SIGNED_BASELINE_COMMIT!r}"
            )
    for artifact_id, present in sorted((payload.get("rulings_landed") or {}).items()):
        if not present:
            errors.append(f"RULING_NOT_LANDED: {artifact_id}")
    for artifact_id in payload.get("rulings_missing_from_readme_index") or []:
        errors.append(f"RULING_NOT_IN_INDEX: {artifact_id} is absent from the README ruling index")

    # --- FR-CALIBRATION-004 ---
    if payload.get("hard_gate_declared_count") != payload.get("hard_gate_item_count"):
        errors.append(
            f"HARD_GATE_COUNT_DRIFT: ruling declares {payload.get('hard_gate_declared_count')!r} "
            f"but lists {payload.get('hard_gate_item_count')!r}"
        )
    if payload.get("hard_gate_item_count") != 7:
        errors.append(f"HARD_GATE_COUNT_DRIFT: expected 7 hard gates, got {payload.get('hard_gate_item_count')!r}")
    for gate in payload.get("hard_gates_without_statement") or []:
        errors.append(f"HARD_GATE_WITHOUT_STATEMENT: {gate}")

    # --- ADR ---
    found = payload.get("adr_ids") or []
    for adr_id in ADR_IDS:
        if adr_id not in found:
            errors.append(f"ADR_MISSING: {adr_id}")
    for extra in sorted(set(found) - set(ADR_IDS)):
        errors.append(f"ADR_UNEXPECTED: {extra} is not one of the six ADRs the charter names")
    for row in payload.get("adrs") or []:
        adr_id = row.get("adr_id", "<no id>")
        for field in ADR_REQUIRED_DECLARATIONS:
            if not row.get(field):
                errors.append(f"ADR_DECLARATION_MISSING: {adr_id} has no {field}")
        expected_title = (payload.get("charter_adr_titles") or {}).get(adr_id)
        if expected_title and row.get("title") != expected_title:
            errors.append(
                f"ADR_TITLE_DRIFT: {adr_id} is titled {row.get('title')!r}, charter names {expected_title!r}"
            )
    if payload.get("adr_004_activation_is_never") is not True:
        errors.append(
            "IDENTITY_ISOLATION_ACTIVATION_CONDITION_WEAKENED: ADR-004 must declare activation_condition_is_never"
        )

    # --- 非 ADR 记录 ---
    for record, present in sorted((payload.get("non_adr_records_present") or {}).items()):
        if not present:
            errors.append(f"NON_ADR_RECORD_MISSING: {record}")
    for item in payload.get("commercial_capabilities_built") or []:
        errors.append(f"COMMERCIAL_CAPABILITY_BUILT_BEFORE_RULING: {item}")
    missing_commercial = sorted(set(COMMERCIAL_MUST_NOT_BUILD) - set(payload.get("commercial_capabilities_listed") or []))
    if missing_commercial:
        errors.append(f"COMMERCIAL_MUST_NOT_BUILD_LIST_INCOMPLETE: missing {missing_commercial}")

    # --- 层映射双向比对 ---
    truth = set(payload.get("m1_object_ids") or [])
    mapped = set(payload.get("layer_mapped_object_ids") or [])
    for oid in sorted(truth - mapped):
        errors.append(f"LAYER_MAPPING_INCOMPLETE: {oid} has no layer")
    for oid in sorted(mapped - truth):
        errors.append(
            f"NEW_TOP_LEVEL_INPUT_OR_OUTPUT_OBJECT_REQUIRED: layer map introduces {oid}, "
            "which the M1 coverage map does not define"
        )
    for oid in payload.get("layer_refs_unknown") or []:
        errors.append(f"LAYER_ID_UNKNOWN: {oid} maps to a layer id that is not declared")
    if payload.get("layer_count") != 6:
        errors.append(f"LAYER_COUNT_DRIFT: expected 6 layers, got {payload.get('layer_count')!r}")
    if payload.get("fact_priority_changed_by_package") is not False:
        errors.append("FACT_PRIORITY_CHANGE_REQUIRED: the layer map claims to change the fact priority order")

    # --- 结束状态块 ---
    receipts = payload.get("package_receipts") or []
    if not receipts:
        errors.append("PACKAGE_END_STATE_MISSING: no M2 package receipt records an end-state block")

    current = [r for r in receipts if r.get("describes_current_state")]
    if len(current) != 1:
        errors.append(
            f"CURRENT_STATE_RECEIPT_AMBIGUOUS: {len(current)} receipt(s) claim to describe the current state, "
            f"expected exactly 1 (found {[r.get('package_id') for r in current]})"
        )

    for row in receipts:
        pid = row.get("package_id", "<no package>")
        end_state = row.get("end_state") or {}
        if not end_state:
            errors.append(f"PACKAGE_END_STATE_MISSING: {pid} records no end-state block")
            continue

        expected_block = REQUIRED_END_STATE_BY_PACKAGE.get(pid)
        if expected_block:
            for key, expected in sorted(expected_block.items()):
                if key not in end_state:
                    errors.append(f"PACKAGE_END_STATE_MISSING: {pid}.{key}")
                elif end_state[key] != expected:
                    errors.append(
                        f"PACKAGE_END_STATE_DRIFT: {pid}.{key}={end_state[key]!r}, expected {expected!r}"
                    )

        for key in ALWAYS_FALSE_IN_END_STATE:
            if end_state.get(key) not in (False, None):
                errors.append(f"RED_LINE_FLAG_SET: {pid}.{key}={end_state.get(key)!r} must stay false")

        if row.get("describes_current_state"):
            for key, actual in sorted((payload.get("canonical_state") or {}).items()):
                if end_state.get(key) != actual:
                    errors.append(
                        f"CURRENT_END_STATE_CONTRADICTS_CANONICAL_SOURCE: {pid}.{key}="
                        f"{end_state.get(key)!r} in the receipt but {actual!r} in {ROLE_MODEL}"
                    )
        elif not row.get("superseded_by"):
            errors.append(
                f"SUPERSEDED_RECEIPT_UNMARKED: {pid} no longer describes the current state but names no "
                "superseded_by — 历史块必须自报已被取代，否则读者会把旧收尾态当成现状"
            )

        if not row.get("self_reference_limitation_recorded"):
            errors.append(
                f"RECEIPT_SELF_REFERENCE_UNDISCLOSED: {pid} must state that it cannot record the commit hash "
                "of the commit containing itself"
            )

    # --- 注册 ---
    for name in payload.get("unregistered_m2_checkers") or []:
        errors.append(f"CHECKER_NOT_REGISTERED_IN_FULL_SUITE: {name}")
    return errors


def _front_matter(text: str) -> dict:
    match = FRONT_MATTER_RE.match(text)
    if not match:
        return {}
    parsed = yaml.safe_load(match.group(1))
    return parsed if isinstance(parsed, dict) else {}


def collect() -> dict:
    charter = load_yaml(CHARTER)
    calibration = load_yaml(CALIBRATION_RULING)
    signature = load_yaml(SIGNATURE_RECEIPT)
    model = load_yaml(ROLE_MODEL)
    coverage = load_yaml(COVERAGE_MAP)
    layer_map = load_yaml(LAYER_MAP)
    commercial = load_yaml(COMMERCIAL)
    manifest = load_yaml(MANIFEST)
    readme = read_text("README.md")
    registry_source = read_text(REGISTRY)

    package_receipts = []
    for path in sorted(RECEIPT_ROOT.glob("m2_ep*/m2_ep*_delivery_receipt.yaml")):
        doc = load_yaml(str(path.relative_to(ROOT)))
        end_state = next(
            (v for k, v in doc.items() if k.endswith("_end_state") and isinstance(v, dict)), {}
        )
        package_receipts.append(
            {
                "package_id": doc.get("package_id"),
                "path": str(path.relative_to(ROOT)),
                "end_state": end_state,
                "describes_current_state": bool(doc.get("describes_current_state")),
                "superseded_by": doc.get("superseded_by"),
                "self_reference_limitation_recorded": bool(doc.get("self_reference_limitation")),
            }
        )

    adrs = []
    for path in sorted(ADR_DIR.glob("ADR-*.md")):
        fm = _front_matter(path.read_text(encoding="utf-8"))
        adrs.append(
            {
                "adr_id": fm.get("adr_id"),
                "title": fm.get("title"),
                "minimal_implementation": fm.get("minimal_implementation"),
                "landing_milestone": fm.get("landing_milestone"),
                "not_building_now": fm.get("not_building_now"),
                "activation_condition": fm.get("activation_condition"),
                "activation_condition_is_never": fm.get("activation_condition_is_never"),
            }
        )
    adr_by_id = {row["adr_id"]: row for row in adrs}

    charter_titles = {row["id"]: row["title"] for row in charter["milestone_plan_m2"]["adr_titles"]}

    layers = {row["layer_id"] for row in layer_map["layers"]}
    layer_rows = layer_map["mapping"]

    registered = set(re.findall(r'"(check_[a-z0-9_]+)"', registry_source))
    m2_checkers = {path.stem for path in CHECKER_DIR.glob("check_m2_*.py")}

    ruling_files = {
        "DIYU-CBFSK-FOUNDER-M2-CHARTER-001": "governance/founder_rulings/DIYU-CBFSK-FOUNDER-M2-CHARTER-001.yaml",
        "DIYU-CBFSK-FR-CALIBRATION-004": "governance/founder_rulings/DIYU-CBFSK-FR-CALIBRATION-004.yaml",
    }

    gates = calibration["hard_gates"]["items"]

    return {
        "charter_declared_digest": charter["verbatim_integrity"]["verbatim_sha256"],
        "charter_actual_digest": sha256_text(charter["verbatim_ruling"]),
        "charter_transcription_only": charter["verbatim_integrity"]["transcription_only"],
        "baseline_commits": {
            "charter.ruling_base_commit": charter["ruling_base_commit"],
            "calibration.ruling_base_commit": calibration["ruling_base_commit"],
            "signature_receipt.signature_base_commit": signature["signature_base_commit"],
            "manifest.signed_baseline_commit": manifest["control_header"]["signed_baseline_commit"],
        },
        "rulings_landed": {name: (ROOT / rel).exists() for name, rel in ruling_files.items()},
        "rulings_missing_from_readme_index": [name for name in ruling_files if name.split("DIYU-CBFSK-")[-1] not in readme],
        "hard_gate_declared_count": calibration["hard_gates"]["count"],
        "hard_gate_item_count": len(gates),
        "hard_gates_without_statement": [g["id"] for g in gates if not g.get("statement")],
        "adr_ids": [row["adr_id"] for row in adrs],
        "adrs": adrs,
        "charter_adr_titles": charter_titles,
        "adr_004_activation_is_never": adr_by_id.get("ADR-004", {}).get("activation_condition_is_never"),
        "non_adr_records_present": {
            row["id"]: (ROOT / row["landed"]).exists()
            for row in charter["milestone_plan_m2"]["non_adr_records"]["records"]
        },
        "commercial_capabilities_listed": [item["capability"] for item in commercial["must_not_build_before_ruling"]["items"]],
        "commercial_capabilities_built": [
            item["capability"] for item in commercial["must_not_build_before_ruling"]["items"] if item["built"]
        ],
        "m1_object_ids": [row["object_id"] for row in coverage["inputs"]]
        + [row["object_id"] for row in coverage["outputs"]],
        "layer_mapped_object_ids": [row["object_id"] for row in layer_rows],
        "layer_refs_unknown": [row["object_id"] for row in layer_rows if row["layer_id"] not in layers],
        "layer_count": len(layer_map["layers"]),
        "fact_priority_changed_by_package": layer_map["fact_priority_unchanged"]["changed_by_this_package"],
        "package_receipts": package_receipts,
        "canonical_state": {
            "execution_status": model["project_state"]["execution_status"],
            "m2_started": model["project_state"]["m2_started"],
            "knowledge_distillation_started": model["project_state"]["knowledge_distillation_started"],
            "production_servable": model["project_state"]["production_servable"],
        },
        "unregistered_m2_checkers": sorted(m2_checkers - registered),
    }


if __name__ == "__main__":
    cli(LABEL, collect, validate)
