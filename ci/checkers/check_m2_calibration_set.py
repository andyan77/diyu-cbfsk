#!/usr/bin/env python3
"""90 例公开校准集：45 个格子无一为空，每一例都带该类要求的判定形态。

「只出题干不合格」是这份判据的全部动机。因此每一例都要按它自己的任务类型交出对应的东西：
① 类交 0/1 两侧条件，② 类交可接受推理区间，③ 类交至少两个合法解族与可接受边界。
②③ 类携带唯一 Gold Answer 直接触发 SC-20。

能力维度是否适用某个任务类型，读七张纵向卡自己的声明；边界族是否存在，读注册表；
品类枚举读 M1 交接面。校准集自述的任何计数都不作为判定依据。
"""

from __future__ import annotations

from _common import ROOT, cli, load_yaml

LABEL = "check_m2_calibration_set"

CAL = "03_m2_evaluation_foundation/calibration/public_calibration_set.v0.1.yaml"
REGISTRY = "03_m2_evaluation_foundation/scoring/acceptable_decision_boundary_registry.v0.1.yaml"
MATRIX = "03_m2_evaluation_foundation/capability_matrix/benchmark_capability_matrix.v0.1.yaml"
HANDOFF = "01_contracts_and_schemas/m1_interface_handoff.v0.1.yaml"
UPSTREAM_GATES = "01_contracts_and_schemas/execution_critical_path_and_decision_gates.v1.0.yaml"

EXPECTED_TOTAL = 90
EXPECTED_CELLS = 45
EXPECTED_PER_CELL = 2
TASK_CLASSES = ("constraint_correctness", "mechanism_correctness", "open_decision")
RISK_TIERS = ("high", "medium", "low")


def _validate_case(case: dict, ctx: dict, errors: list[str]) -> None:
    cid = case.get("case_id", "<no id>")
    cls = case.get("evaluation_task_class")

    if cls not in TASK_CLASSES:
        errors.append(f"CASE_WITHOUT_EVALUATION_FORM: {cid} has unknown evaluation_task_class {cls!r}")
        return
    if case.get("risk_tier") not in RISK_TIERS:
        errors.append(f"CASE_WITHOUT_EVALUATION_FORM: {cid} has unknown risk_tier {case.get('risk_tier')!r}")
    if case.get("category_id") not in ctx["categories"]:
        errors.append(f"CASE_CATEGORY_UNKNOWN: {cid} names category {case.get('category_id')!r}")
    if not (case.get("scenario") or "").strip():
        errors.append(f"CASE_WITHOUT_EVALUATION_FORM: {cid} has an empty scenario")
    if not case.get("input_object_refs"):
        errors.append(f"CASE_WITHOUT_EVALUATION_FORM: {cid} lists no input_object_refs")

    for cap in case.get("capability_dimensions") or []:
        applicable = ctx["capability_classes"].get(cap)
        if applicable is None:
            errors.append(f"CAPABILITY_NOT_APPLICABLE_TO_TASK_CLASS: {cid} names unknown capability {cap!r}")
        elif cls not in applicable:
            errors.append(
                f"CAPABILITY_NOT_APPLICABLE_TO_TASK_CLASS: {cid} scores {cap!r} on a {cls} task, "
                "which that card does not declare applicable"
            )

    for gate in case.get("hard_gate_refs") or []:
        if gate not in ctx["hard_gates"]:
            errors.append(f"CASE_HARD_GATE_UNKNOWN: {cid} references {gate!r}")

    if cls == "constraint_correctness":
        if case.get("gold_answer_allowed") is not True:
            errors.append(f"CASE_WITHOUT_EVALUATION_FORM: {cid} is ① class but does not allow a gold answer")
        det = case.get("binary_fact_determination") or {}
        for field in ("question", "verdict_1_condition", "verdict_0_condition"):
            if not (det.get(field) or "").strip():
                errors.append(f"BINARY_DETERMINATION_INCOMPLETE: {cid} has no {field}")
        ref = case.get("constraint_ref")
        if ref not in ctx["constraint_ids"]:
            errors.append(f"CASE_CONSTRAINT_REF_UNRESOLVED: {cid} references {ref!r}")
        return

    if case.get("gold_answer_allowed") is not False or case.get("single_gold_answer_present") is not False:
        errors.append(f"SINGLE_GOLD_ANSWER_ON_OPEN_TASK: {cid} is {cls} but carries a gold answer flag")

    ref = case.get("acceptable_decision_boundary_ref")
    family = ctx["families"].get(ref)
    if family is None:
        errors.append(f"BOUNDARY_REF_MISSING: {cid} references boundary {ref!r}, which the registry does not define")
    elif family != cls:
        errors.append(
            f"BOUNDARY_CONTRADICTS_FAMILY: {cid} is {cls} but {ref} is registered for {family}"
        )

    if cls == "mechanism_correctness":
        if not (case.get("acceptable_reasoning_interval") or "").strip():
            errors.append(f"REASONING_INTERVAL_MISSING: {cid} has no acceptable_reasoning_interval")
    else:
        families = case.get("legal_solution_families") or []
        if len(families) < 2:
            errors.append(f"SOLUTION_FAMILY_INSUFFICIENT: {cid} lists {len(families)} legal solution family/families")
        if not (case.get("acceptance_boundary") or "").strip():
            errors.append(f"SOLUTION_FAMILY_INSUFFICIENT: {cid} has no acceptance_boundary")


def validate(payload: dict) -> list[str]:
    errors: list[str] = []
    cases = payload.get("cases") or []
    ctx = {
        "categories": set(payload.get("categories") or []),
        "capability_classes": payload.get("capability_classes") or {},
        "families": payload.get("boundary_families") or {},
        "hard_gates": set(payload.get("hard_gate_ids") or []),
        "constraint_ids": set(payload.get("constraint_ids") or []),
    }

    if len(cases) != EXPECTED_TOTAL:
        errors.append(f"CALIBRATION_CASE_COUNT_DRIFT: {len(cases)} cases, must be {EXPECTED_TOTAL}")

    seen: set[str] = set()
    grid: dict[tuple, int] = {}
    for case in cases:
        cid = case.get("case_id")
        if cid in seen:
            errors.append(f"CASE_ID_COLLISION: {cid} appears more than once")
        seen.add(cid)
        key = (case.get("category_id"), case.get("evaluation_task_class"), case.get("risk_tier"))
        grid[key] = grid.get(key, 0) + 1
        _validate_case(case, ctx, errors)
        if case.get("risk_tier") == "high":
            if case.get("founder_review_coverage") != 1.0 or case.get("sampling_allowed") is not False:
                errors.append(f"HIGH_RISK_SAMPLED: {cid} is high risk without 100% founder coverage")

    for category in sorted(ctx["categories"]):
        for cls in TASK_CLASSES:
            for tier in RISK_TIERS:
                count = grid.get((category, cls, tier), 0)
                if count == 0:
                    errors.append(f"STRATUM_EMPTY: no case for ({category}, {cls}, {tier})")
                elif count != EXPECTED_PER_CELL:
                    errors.append(
                        f"STRATUM_SIZE_DRIFT: ({category}, {cls}, {tier}) holds {count} cases, must be {EXPECTED_PER_CELL}"
                    )

    if len(grid) != EXPECTED_CELLS:
        errors.append(f"STRATUM_COUNT_DRIFT: {len(grid)} populated cells, must be {EXPECTED_CELLS}")

    declared = payload.get("declared_grid") or {}
    if declared.get("total_cases") != len(cases):
        errors.append(f"CALIBRATION_CASE_COUNT_DRIFT: header declares {declared.get('total_cases')!r} cases")
    if declared.get("empty_cells") != 0:
        errors.append(f"STRATUM_EMPTY: header declares {declared.get('empty_cells')!r} empty cells, must be 0")

    anchor = payload.get("declared_anchor_item_count")
    if anchor != len(cases):
        errors.append(f"ANCHOR_ITEM_COUNT_DRIFT: set declares {anchor!r} anchor items, holds {len(cases)} cases")
    if payload.get("consumer_anchor_item_count") != len(cases):
        errors.append(
            f"ANCHOR_ITEM_COUNT_DRIFT: reviewer_calibration_contract records "
            f"{payload.get('consumer_anchor_item_count')!r} anchor items"
        )

    registry = payload.get("registry_counts") or {}
    if registry.get("declared_total") != registry.get("actual_total"):
        errors.append(
            f"BOUNDARY_FAMILY_COUNT_DRIFT: registry declares {registry.get('declared_total')!r} families, "
            f"lists {registry.get('actual_total')!r}"
        )
    for missing in payload.get("families_without_out_of_boundary") or []:
        errors.append(f"BOUNDARY_FAMILY_INCOMPLETE: {missing} has no out_of_boundary")

    return errors


def collect() -> dict:
    data = load_yaml(CAL)
    registry = load_yaml(REGISTRY)
    matrix = load_yaml(MATRIX)
    handoff = load_yaml(HANDOFF)
    upstream = load_yaml(UPSTREAM_GATES)

    capability_classes: dict[str, list[str]] = {}
    for row in matrix["capability_dimensions"]["items"]:
        card_rel = row["card"]
        if not (ROOT / card_rel).exists():
            continue
        card = load_yaml(card_rel)
        applicability = card.get("evaluation_task_class_applicability") or {}
        capability_classes[card["capability_dimension"]] = [
            c for c in TASK_CLASSES if applicability.get(c) is True
        ]

    surface = handoff["category_constraint_surface"]
    constraint_ids: set[str] = set(surface.get("conflict_priority_rule_ids") or [])
    constraint_ids |= set(surface.get("combination_rule_ids") or [])
    for cat in surface["categories"]:
        constraint_ids |= set(cat.get("hard_constraint_ids") or [])
    hard_gate_ids = [i["id"] for i in upstream["hard_gates"]["items"]]
    constraint_ids |= set(hard_gate_ids)

    families = {f["boundary_id"]: f["task_class"] for f in registry["families"]}
    no_oob = [
        f["boundary_id"]
        for f in registry["families"]
        if not (f.get("out_of_boundary") or f.get("acceptance_boundary"))
    ]

    consumer = load_yaml("03_m2_evaluation_foundation/evaluation_governance/reviewer_calibration_contract.v0.1.yaml")

    return {
        "cases": data["cases"],
        "declared_grid": data["grid"],
        "declared_anchor_item_count": data["anchor_item_binding"]["anchor_item_count"],
        "consumer_anchor_item_count": consumer["machine_checkable_fields"]["anchor_item_count"]["current_value"],
        "categories": [c["category_id"] for c in surface["categories"]],
        "capability_classes": capability_classes,
        "boundary_families": families,
        "families_without_out_of_boundary": no_oob,
        "registry_counts": {
            "declared_total": registry["boundary_family_count"],
            "actual_total": len(registry["families"]),
        },
        "hard_gate_ids": hard_gate_ids,
        "constraint_ids": sorted(constraint_ids),
    }


if __name__ == "__main__":
    cli(LABEL, collect, validate)
