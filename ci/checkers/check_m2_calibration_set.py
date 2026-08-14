#!/usr/bin/env python3
"""90 例公开校准集：45 个格子无一为空，每一例都带该类要求的判定形态。

「只出题干不合格」是这份判据的全部动机。因此每一例都要按它自己的任务类型交出对应的东西：
① 类交 0/1 两侧条件，② 类交可接受推理区间，③ 类交至少两个合法解族与可接受边界。
②③ 类携带唯一 Gold Answer 直接触发 SC-20。

能力维度是否适用某个任务类型，读七张纵向卡自己的声明；边界族是否存在，读注册表；
品类枚举读 M1 交接面。校准集自述的任何计数都不作为判定依据。

第二件事（EP05-CORRECTION C-1）：每一例还必须挂一个候选输出。只有题干没有被评对象，
评审员判的是空气，测出来的一致率没有指涉。候选被构造时落在边界哪一侧，记在
founder_boundary_anchor_truth.v0.1.yaml——本判据现算格子覆盖与分配规则，
并核对那份标签一个字也没有留在校准集里。
"""

from __future__ import annotations

from _common import ROOT, cli, load_yaml

LABEL = "check_m2_calibration_set"

CAL = "03_m2_evaluation_foundation/calibration/public_calibration_set.v0.1.yaml"
ANCHOR_TRUTH = "03_m2_evaluation_foundation/calibration/founder_boundary_anchor_truth.v0.1.yaml"
REGISTRY = "03_m2_evaluation_foundation/scoring/acceptable_decision_boundary_registry.v0.1.yaml"
MATRIX = "03_m2_evaluation_foundation/capability_matrix/benchmark_capability_matrix.v0.1.yaml"
HANDOFF = "01_contracts_and_schemas/m1_interface_handoff.v0.1.yaml"
UPSTREAM_GATES = "01_contracts_and_schemas/execution_critical_path_and_decision_gates.v1.0.yaml"

EXPECTED_TOTAL = 90
EXPECTED_CELLS = 45
EXPECTED_PER_CELL = 2
TASK_CLASSES = ("constraint_correctness", "mechanism_correctness", "open_decision")
RISK_TIERS = ("high", "medium", "low")
TRACE_REQUIRED_CLASSES = ("mechanism_correctness", "open_decision")
BOUNDARY_POSITIONS = ("inside", "outside", "boundary_high_value")
CONSTRUCTED_JUDGMENTS = ("ACCEPT", "REJECT")
# 标签只许住在锚点真源里。它出现在校准集，就会跟着派生进分发包。
ANCHOR_LABEL_KEYS = ("boundary_position", "constructed_judgment", "expected_judgment")


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


def _validate_candidates(cases: list[dict], errors: list[str]) -> None:
    """每个评审单元都要有被评对象；机制题与开放题还要有决策轨迹。"""
    for case in cases:
        cid = case.get("case_id", "<no id>")
        cand = case.get("candidate")
        if not isinstance(cand, dict):
            errors.append(f"CANDIDATE_MISSING: {cid} carries no candidate block")
            continue
        if cand.get("candidate_id") != f"CAND-{cid}":
            errors.append(
                f"CANDIDATE_MISSING: {cid} carries candidate_id {cand.get('candidate_id')!r}, expected CAND-{cid}"
            )
        if not (cand.get("candidate_output") or "").strip():
            errors.append(f"CANDIDATE_MISSING: {cid} has an empty candidate_output")
        if cand.get("non_candidate_knowledge") is not True:
            errors.append(f"CANDIDATE_NOT_MARKED_NON_KNOWLEDGE: {cid} does not mark its candidate as non-knowledge")
        if case.get("evaluation_task_class") in TRACE_REQUIRED_CLASSES:
            if not (cand.get("candidate_decision_trace") or "").strip():
                errors.append(f"CANDIDATE_DECISION_TRACE_MISSING: {cid} is {case.get('evaluation_task_class')} with no trace")
        for key in ANCHOR_LABEL_KEYS:
            if key in cand or key in case:
                errors.append(f"EXPECTED_LABEL_IN_CASE_FILE: {cid} carries {key!r}, which belongs only in the anchor truth")


def _validate_anchors(cases: list[dict], payload: dict, errors: list[str]) -> None:
    """锚点真源：覆盖、格内两侧、分配规则、自述计数，四项都现算。"""
    anchors = payload.get("anchors") or []
    by_case = {a.get("case_id"): a for a in anchors}
    case_ids = [c.get("case_id") for c in cases]

    for cid in case_ids:
        if cid not in by_case:
            errors.append(f"ANCHOR_COVERAGE_INCOMPLETE: no anchor for {cid}")
    for cid in by_case:
        if cid not in case_ids:
            errors.append(f"ANCHOR_COVERAGE_INCOMPLETE: anchor names {cid!r}, which is not a case in the set")
    if len(anchors) != len(by_case):
        errors.append(f"ANCHOR_COVERAGE_INCOMPLETE: {len(anchors)} anchors collapse to {len(by_case)} case ids")

    for a in anchors:
        cid = a.get("case_id", "<no id>")
        if a.get("boundary_position") not in BOUNDARY_POSITIONS:
            errors.append(f"ANCHOR_JUDGMENT_INVALID: {cid} has boundary_position {a.get('boundary_position')!r}")
        if a.get("constructed_judgment") not in CONSTRUCTED_JUDGMENTS:
            errors.append(f"ANCHOR_JUDGMENT_INVALID: {cid} has constructed_judgment {a.get('constructed_judgment')!r}")
        if a.get("candidate_id") != f"CAND-{cid}":
            errors.append(f"ANCHOR_JUDGMENT_INVALID: {cid} anchors candidate {a.get('candidate_id')!r}")
        if a.get("boundary_position") == "inside" and a.get("constructed_judgment") != "ACCEPT":
            errors.append(f"ANCHOR_JUDGMENT_INVALID: {cid} is inside the boundary but constructed as REJECT")
        if a.get("boundary_position") == "outside" and a.get("constructed_judgment") != "REJECT":
            errors.append(f"ANCHOR_JUDGMENT_INVALID: {cid} is outside the boundary but constructed as ACCEPT")

    # 格子按首次出现排序；偶数格第一例为 inside，奇数格第二例为 inside。
    order: list[tuple] = []
    cells: dict[tuple, list[str]] = {}
    for case in cases:
        key = (case.get("category_id"), case.get("evaluation_task_class"), case.get("risk_tier"))
        if key not in cells:
            cells[key] = []
            order.append(key)
        cells[key].append(case.get("case_id"))

    for index, key in enumerate(order):
        ids = cells[key]
        judgments = [(by_case.get(i) or {}).get("constructed_judgment") for i in ids]
        if sorted(j for j in judgments if j) != ["ACCEPT", "REJECT"]:
            errors.append(
                f"ANCHOR_CELL_COVERAGE_BROKEN: cell {key} holds constructed judgments {judgments!r}, "
                "each cell needs exactly one ACCEPT and one REJECT"
            )
            continue
        if len(ids) != EXPECTED_PER_CELL:
            continue
        expected_accept = ids[0] if index % 2 == 0 else ids[1]
        actual_accept = [i for i in ids if (by_case.get(i) or {}).get("constructed_judgment") == "ACCEPT"]
        if actual_accept != [expected_accept]:
            errors.append(
                f"ANCHOR_ASSIGNMENT_RULE_VIOLATED: cell index {index} puts ACCEPT on {actual_accept!r}, "
                f"the declared rule puts it on {expected_accept!r}"
            )

    declared = payload.get("declared_anchor_counts") or {}
    actual = {
        "anchors": len(anchors),
        "inside": sum(1 for a in anchors if a.get("boundary_position") == "inside"),
        "outside": sum(1 for a in anchors if a.get("boundary_position") == "outside"),
        "boundary_high_value": sum(1 for a in anchors if a.get("boundary_position") == "boundary_high_value"),
        "constructed_accept": sum(1 for a in anchors if a.get("constructed_judgment") == "ACCEPT"),
        "constructed_reject": sum(1 for a in anchors if a.get("constructed_judgment") == "REJECT"),
    }
    for field, value in actual.items():
        if declared.get(field) != value:
            errors.append(
                f"ANCHOR_COUNT_MISSTATED: anchor truth declares {field}={declared.get(field)!r}, holds {value}"
            )
    if payload.get("anchor_distributed_to_reviewers") is not False:
        errors.append("ANCHOR_COUNT_MISSTATED: the anchor truth does not declare itself undistributed")


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

    _validate_candidates(cases, errors)
    _validate_anchors(cases, payload, errors)

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
    anchor_truth = load_yaml(ANCHOR_TRUTH)

    return {
        "cases": data["cases"],
        "anchors": anchor_truth["anchors"],
        "declared_anchor_counts": anchor_truth["counts"],
        "anchor_distributed_to_reviewers": anchor_truth["distribution"]["distributed_to_reviewers"],
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
