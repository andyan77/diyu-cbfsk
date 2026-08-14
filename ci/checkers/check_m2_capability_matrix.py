#!/usr/bin/env python3
"""双轴评测矩阵：七张纵向能力卡、四轴寻址、34 条 PRD 指标归属、11 条硬门承接。

三处地面真值都不取自被检对象：
  * 每个能力维度适用哪些任务类型 —— 读七张卡各自的 evaluation_task_class_applicability，
    矩阵自述的 applicable_task_classes 必须与之逐条相符；寻址格子数由卡片侧重算。
  * 34 条指标 —— 从 PRD v1.2 的 10.2 表格现场解析，不读矩阵里那份清单。
  * 11 条硬门与 8 道发布门 —— 读 execution_critical_path_and_decision_gates 的上游定义。
"""

from __future__ import annotations

from zipfile import ZipFile
from xml.etree import ElementTree

from _common import ROOT, W_NS, cli, load_yaml

LABEL = "check_m2_capability_matrix"

MATRIX = "03_m2_evaluation_foundation/capability_matrix/benchmark_capability_matrix.v0.1.yaml"
GATE_MAP = "03_m2_evaluation_foundation/gates/hard_gate_definitions.v0.1.yaml"
UPSTREAM_GATES = "01_contracts_and_schemas/execution_critical_path_and_decision_gates.v1.0.yaml"
PRD = "笛语跨品牌服装搭配专家内核_PRD与执行里程碑_v1.2.docx"

EXPECTED_CAPABILITY_COUNT = 7
EXPECTED_CATEGORY_COUNT = 5
EXPECTED_RISK_TIER_COUNT = 3
TASK_CLASSES = ("constraint_correctness", "mechanism_correctness", "open_decision")


def _prd_metric_rows() -> list[tuple[str, str]]:
    """PRD 10.2「指标 / 建议阈值 / 说明」表——三列表头完全匹配才认，避免撞上别的表。"""
    root = ElementTree.fromstring(ZipFile(ROOT / PRD).read("word/document.xml"))
    for tbl in root.iter(f"{W_NS}tbl"):
        rows = []
        for tr in tbl.iter(f"{W_NS}tr"):
            rows.append(
                ["".join(n.text or "" for n in tc.iter(f"{W_NS}t")).strip() for tc in tr.iter(f"{W_NS}tc")]
            )
        if rows and rows[0][:3] == ["指标", "建议阈值", "说明"]:
            return [(r[0], r[1]) for r in rows[1:]]
    raise ValueError("PRD 10.2 metric table not found")


def _validate_capabilities(payload: dict, errors: list[str]) -> int:
    slots = 0
    for cap in payload.get("capabilities") or []:
        code = cap.get("code", "<no code>")
        if not cap.get("card_exists"):
            errors.append(f"CAPABILITY_CARD_MISSING: {code} names {cap.get('card')!r}, which does not exist")
            continue
        if cap.get("evaluation_task_class_annotated") is not True:
            errors.append(f"CAPABILITY_ITEM_WITHOUT_TASK_CLASS: {code} is not annotated with evaluation_task_class")

        declared = list(cap.get("declared_task_classes") or [])
        from_card = list(cap.get("card_task_classes") or [])
        for value in declared:
            if value not in TASK_CLASSES:
                errors.append(f"CAPABILITY_ITEM_WITHOUT_TASK_CLASS: {code} declares unknown task class {value!r}")
        if declared != from_card:
            errors.append(
                f"CAPABILITY_TASK_CLASS_DRIFT: {code} matrix says {declared!r}, its card says {from_card!r}"
            )
        if cap.get("per_item_scored"):
            slots += len(from_card)
        elif from_card:
            errors.append(
                f"CAPABILITY_TASK_CLASS_DRIFT: {code} is aggregate_only but its card declares {from_card!r}"
            )
    return slots


def _validate_metrics(payload: dict, errors: list[str]) -> None:
    prd_metrics = [m for m, _ in payload.get("prd_metrics") or []]
    owned = payload.get("metric_owners") or {}
    duplicates = payload.get("duplicate_metric_ids") or []

    for metric in duplicates:
        errors.append(f"METRIC_OWNED_TWICE: {metric!r} appears more than once in metric_ownership")
    for metric in prd_metrics:
        if metric not in owned:
            errors.append(f"METRIC_WITHOUT_OWNER: PRD 10.2 lists {metric!r}, the matrix assigns no owner")
    for metric in owned:
        if metric not in prd_metrics:
            errors.append(f"OWNER_CLAIMS_UNKNOWN_METRIC: {metric!r} is owned but is not in PRD 10.2")

    declared = payload.get("declared_metric_count")
    if declared != len(prd_metrics):
        errors.append(
            f"METRIC_COUNT_DRIFT: matrix declares {declared!r} metrics, PRD 10.2 lists {len(prd_metrics)}"
        )


def _validate_gate_mapping(payload: dict, errors: list[str]) -> None:
    upstream_hard = list(payload.get("upstream_hard_gate_ids") or [])
    upstream_release = set(payload.get("upstream_release_gate_ids") or [])
    mappings = payload.get("gate_mappings") or []

    mapped = [m.get("hard_gate_id") for m in mappings]
    for hg in upstream_hard:
        if hg not in mapped:
            errors.append(f"HARD_GATE_WITHOUT_RELEASE_GATE: {hg} has no row in the mapping table")
    for hg in mapped:
        if hg not in upstream_hard:
            errors.append(f"HARD_GATE_ID_DRIFT: mapping table names {hg!r}, upstream has no such hard gate")

    for row in mappings:
        hg = row.get("hard_gate_id", "<no id>")
        primary = row.get("primary_release_gate")
        if not primary:
            errors.append(f"HARD_GATE_WITHOUT_RELEASE_GATE: {hg} names no primary release gate")
        elif primary not in upstream_release:
            errors.append(f"RELEASE_GATE_ID_UNKNOWN: {hg} points at {primary!r}, which is not one of the eight")
        if isinstance(primary, list):
            errors.append(f"HARD_GATE_MULTIPLE_PRIMARY: {hg} lists more than one primary release gate")
        for secondary in row.get("secondary_release_gates") or []:
            if secondary not in upstream_release:
                errors.append(f"RELEASE_GATE_ID_UNKNOWN: {hg} secondary {secondary!r} is not one of the eight")
            if secondary == primary:
                errors.append(f"HARD_GATE_MULTIPLE_PRIMARY: {hg} repeats {primary!r} as its own secondary")

    if payload.get("declared_hard_gate_count") != len(upstream_hard):
        errors.append(
            f"HARD_GATE_COUNT_DRIFT: mapping table declares {payload.get('declared_hard_gate_count')!r}, "
            f"upstream defines {len(upstream_hard)}"
        )
    if payload.get("declared_release_gate_count") != len(upstream_release):
        errors.append(
            f"RELEASE_GATE_ID_DRIFT: mapping table declares {payload.get('declared_release_gate_count')!r} "
            f"release gates, upstream defines {len(upstream_release)}"
        )

    for cap_code, gates in (payload.get("capability_to_hard_gate") or {}).items():
        for gate in gates:
            if gate not in upstream_hard:
                errors.append(f"HARD_GATE_ID_DRIFT: capability {cap_code} points at unknown hard gate {gate!r}")


def validate(payload: dict) -> list[str]:
    errors: list[str] = []

    if payload.get("axis_count") != 4:
        errors.append(f"AXIS_COUNT_DRIFT: matrix declares {payload.get('axis_count')!r} axes, must be 4")

    capabilities = payload.get("capabilities") or []
    if len(capabilities) != EXPECTED_CAPABILITY_COUNT:
        errors.append(
            f"CAPABILITY_DIMENSION_COUNT_DRIFT: {len(capabilities)} dimensions, must be {EXPECTED_CAPABILITY_COUNT}"
        )
    if payload.get("declared_capability_count") != len(capabilities):
        errors.append(
            f"CAPABILITY_DIMENSION_COUNT_DRIFT: matrix declares {payload.get('declared_capability_count')!r}, "
            f"lists {len(capabilities)}"
        )

    slots = _validate_capabilities(payload, errors)
    expected_cells = slots * EXPECTED_CATEGORY_COUNT * EXPECTED_RISK_TIER_COUNT
    if payload.get("declared_addressable_cells") != expected_cells:
        errors.append(
            f"ADDRESSABLE_CELL_COUNT_DRIFT: matrix declares {payload.get('declared_addressable_cells')!r} cells, "
            f"the seven cards give {expected_cells}"
        )

    _validate_metrics(payload, errors)
    _validate_gate_mapping(payload, errors)
    return errors


def collect() -> dict:
    matrix = load_yaml(MATRIX)
    gate_map = load_yaml(GATE_MAP)
    upstream = load_yaml(UPSTREAM_GATES)

    capabilities = []
    for row in matrix["capability_dimensions"]["items"]:
        card_rel = row["card"]
        card_path = ROOT / card_rel
        card_classes: list[str] = []
        exists = card_path.exists()
        if exists:
            card = load_yaml(card_rel)
            applicability = card.get("evaluation_task_class_applicability") or {}
            card_classes = [c for c in TASK_CLASSES if applicability.get(c) is True]
        capabilities.append(
            {
                "code": row.get("code"),
                "card": card_rel,
                "card_exists": exists,
                "per_item_scored": row.get("per_item_scored"),
                "evaluation_task_class_annotated": row.get("evaluation_task_class_annotated"),
                "declared_task_classes": row.get("applicable_task_classes") or [],
                "card_task_classes": card_classes,
            }
        )

    owner_rows = matrix["metric_ownership"]["items"]
    seen: dict[str, int] = {}
    for row in owner_rows:
        seen[row["metric_id"]] = seen.get(row["metric_id"], 0) + 1

    return {
        "axis_count": matrix["axes"]["count"],
        "declared_capability_count": matrix["capability_dimensions"]["count"],
        "capabilities": capabilities,
        "declared_addressable_cells": matrix["cell_count"]["addressable_cells"],
        "prd_metrics": _prd_metric_rows(),
        "metric_owners": {row["metric_id"]: row["owner"] for row in owner_rows},
        "duplicate_metric_ids": sorted(k for k, v in seen.items() if v > 1),
        "declared_metric_count": matrix["metric_ownership"]["metric_count"],
        "capability_to_hard_gate": matrix["hard_gate_mapping"]["capability_to_hard_gate"],
        "gate_mappings": gate_map["mappings"],
        "declared_hard_gate_count": gate_map["counts"]["hard_gate_count"],
        "declared_release_gate_count": gate_map["counts"]["release_gate_count"],
        "upstream_hard_gate_ids": [i["id"] for i in upstream["hard_gates"]["items"]],
        "upstream_release_gate_ids": [i["id"] for i in upstream["commercial_release_gates"]["items"]],
    }


if __name__ == "__main__":
    cli(LABEL, collect, validate)
