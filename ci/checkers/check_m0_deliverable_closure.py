#!/usr/bin/env python3
"""M0 清单闭环：十四项交付物逐项存在、可追溯，且数量恒为 14。

「不以文档数量替代结果」——所以这里不数文件，而是核对三件事：章程声明的清单与 PRD/执行申请
是同一组 14 项；每一项在磁盘上真实存在；每份合同的 deliverable_index 与清单序号一一对应，
没有两份合同抢同一个位次，也没有哪一位次空缺。
"""

from __future__ import annotations

from _common import ROOT, cli, load_yaml

LABEL = "check_m0_deliverable_closure"

EXPECTED_COUNT = 14

# 序号与名称的唯一权威是 PRD 13/14/17.1 与 DIYU-CBFSK-EXEC-REQ-M0-003；此处复述用于对账，
# 与章程声明不一致即判漂移（两个来源互不派生，才构成真正的交叉核对）。
EXPECTED_NAMES = (
    "project_charter.v1.0.yaml",
    "capability_contract.v1.0.yaml",
    "category_scope_contract.v1.0.yaml",
    "input_output_boundary.v1.0.yaml",
    "role_and_decision_rights.v1.0.yaml",
    "non_goals_and_stop_conditions.v1.0.yaml",
    "knowledge_state_machine.v1.0.yaml",
    "architecture_and_integration_boundary.v1.0.yaml",
    "compliance_review_contract.v1.0.yaml",
    "data_and_fixture_workflow.v1.0.yaml",
    "execution_critical_path_and_decision_gates.v1.0.yaml",
    "M1 对象模型 Brief",
    "M2 评测冻结 Brief",
    "M0 checker / fixtures / report / receipt",
)


def validate(payload: dict) -> list[str]:
    errors: list[str] = []

    items = payload.get("declared_items") or []
    if len(items) != EXPECTED_COUNT:
        errors.append(f"M0_DELIVERABLE_COUNT_DRIFT: charter declares {len(items)} items, must be {EXPECTED_COUNT}")

    declared_names = [item.get("name") for item in items]
    if declared_names != list(EXPECTED_NAMES):
        for index, (declared, expected) in enumerate(zip(declared_names, EXPECTED_NAMES), start=1):
            if declared != expected:
                errors.append(f"M0_DELIVERABLE_NAME_DRIFT: #{index} declares {declared!r}, expected {expected!r}")
        extra = declared_names[len(EXPECTED_NAMES):]
        for name in extra:
            errors.append(f"M0_FIFTEENTH_ITEM: {name!r} is not part of the frozen fourteen")

    seen_index: dict[int, str] = {}
    for item in items:
        index = item.get("index")
        name = item.get("name")
        if index in seen_index:
            errors.append(f"M0_DELIVERABLE_INDEX_COLLISION: #{index} claimed by both {seen_index[index]!r} and {name!r}")
        else:
            seen_index[index] = name
        if not item.get("present"):
            errors.append(f"M0_DELIVERABLE_MISSING: #{index} {name!r} at {item.get('path')!r} does not exist")

    for contract in payload.get("contract_indices") or []:
        declared = contract.get("declared_index")
        expected = contract.get("expected_index")
        if declared != expected:
            errors.append(
                f"DELIVERABLE_INDEX_MISMATCH: {contract.get('path')} says deliverable_index={declared!r}, "
                f"charter places it at #{expected!r}"
            )

    if payload.get("count_is_frozen") is not True:
        errors.append("M0_COUNT_NOT_DECLARED_FROZEN: charter must declare the fourteen-item count frozen")
    if payload.get("no_fifteenth_item") is not True:
        errors.append("M0_FIFTEENTH_ITEM_NOT_FORBIDDEN: charter must forbid a fifteenth item")

    return errors


def collect() -> dict:
    charter = load_yaml("00_charter/project_charter.v1.0.yaml")
    block = charter["m0_deliverables"]

    items = []
    contract_indices = []
    for item in block["items"]:
        rel = item["path"]
        path = ROOT / rel
        items.append({"index": item["index"], "name": item["name"], "path": rel, "present": path.exists()})
        if path.exists() and rel.endswith(".yaml"):
            data = load_yaml(rel)
            if "deliverable_index" in data:
                contract_indices.append(
                    {"path": rel, "declared_index": data["deliverable_index"], "expected_index": item["index"]}
                )

    return {
        "declared_items": items,
        "contract_indices": contract_indices,
        "count_is_frozen": block.get("count_is_frozen"),
        "no_fifteenth_item": block.get("no_fifteenth_item"),
    }


if __name__ == "__main__":
    cli(LABEL, collect, validate)
