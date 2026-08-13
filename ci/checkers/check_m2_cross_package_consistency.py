#!/usr/bin/env python3
"""EP01 与 EP02 产物必须完全自洽：对象引用、约束 ID、状态字段、命名逐项对得上。

M2 的产物分两批落盘（EP01 桥接、EP02 评测），中间还隔着一次 M1 收口与受控合并。
跨包不一致最典型的三种：EP01 写的路径在 EP02 被改名、EP02 的评分卡绑到 EP01 已删掉的
Profile、两批产物对同一状态给出不同说法。这些都不会被单包判据发现——单包判据只看自己那批。

四类交叉引用逐项解析，解析不到即失败：

  对象引用 —— consumes_via_profile / adr_ref / delegated_to / landed_in 指向的东西必须真实存在
  约束 ID  —— 评分卡与信封绑的 hard_constraint_id / conflict rule id 必须在 M1 真源里
  状态字段 —— 同一状态位在各产物里的说法必须一致
  命名     —— artifact_id 必须与文件名对得上，避免「文件改了名、引用还指着旧名」

反自审绿（E12）：合法 ID 与合法路径都从被引用方独立重算，不从引用方的声明读。
"""

from __future__ import annotations

import pathlib

from _common import ROOT, cli, load_yaml

LABEL = "check_m2_cross_package_consistency"

M2_DIR = ROOT / "03_m2_evaluation_foundation"
ADAPTER_DIR = ROOT / "01_contracts_and_schemas" / "category_adapter_contracts"
CONFLICT_TABLE = "01_contracts_and_schemas/category_adapter_contracts/cross_category_conflict_priority.v0.1.yaml"
PROFILE_DIR = M2_DIR / "envelope" / "profiles"
ADR_DIR = M2_DIR / "adr"
ROLE_MODEL = "governance/bootstrap/role_operating_model.v0.2.yaml"

# 这些键的值是仓库相对路径，必须解析得到真实文件。
PATH_BEARING_KEYS = (
    "enforcement_delegated_to", "existing_checker", "delegated_to", "scorecard",
    "runner", "record", "blocked_record", "prerequisites_list",
)
# 这些键的值是 Profile 名。
PROFILE_BEARING_KEYS = ("consumes_via_profile",)
# 这些键的值是 ADR 编号。
ADR_BEARING_KEYS = ("adr_ref",)


def validate(payload: dict) -> list[str]:
    errors: list[str] = []

    for ref in payload.get("unresolved_paths") or []:
        errors.append(
            f"CROSS_PACKAGE_PATH_UNRESOLVED: {ref['file']} field {ref['key']!r} points at "
            f"{ref['value']!r}, which does not exist"
        )
    for ref in payload.get("unresolved_profiles") or []:
        errors.append(
            f"CROSS_PACKAGE_PROFILE_UNRESOLVED: {ref['file']} consumes profile {ref['value']!r}, "
            f"which no Profile declares (available: {ref['available']})"
        )
    for ref in payload.get("unresolved_adrs") or []:
        errors.append(
            f"CROSS_PACKAGE_ADR_UNRESOLVED: {ref['file']} references {ref['value']!r}, "
            "which is not among the six ADRs"
        )
    for ref in payload.get("unresolved_constraint_ids") or []:
        errors.append(
            f"CROSS_PACKAGE_CONSTRAINT_UNRESOLVED: {ref['file']} binds {ref['value']!r}, "
            "which does not exist in the M1 category contracts"
        )
    for ref in payload.get("artifact_id_mismatches") or []:
        errors.append(
            f"CROSS_PACKAGE_NAMING_MISMATCH: {ref['file']} declares artifact_id {ref['declared']!r} "
            f"but the filename implies {ref['implied']!r}"
        )
    for ref in payload.get("state_field_conflicts") or []:
        errors.append(
            f"CROSS_PACKAGE_STATE_CONFLICT: {ref['field']} is {ref['a_value']!r} in {ref['a']} "
            f"but {ref['b_value']!r} in {ref['b']}"
        )

    if payload.get("profile_count") != 1:
        errors.append(
            f"MULTIPLE_ACTIVE_PROFILES: {payload.get('profile_count')} Profile(s) present — "
            "并存会让「当前绑定是哪一份」变成需要推断的问题（EQ-1）"
        )
    if payload.get("scanned_file_count", 0) <= 0:
        errors.append("CROSS_PACKAGE_SCAN_SCANNED_NOTHING: no M2 artifact was read")

    return errors


def _walk(node, fn, path=""):
    if isinstance(node, dict):
        for k, v in node.items():
            fn(k, v)
            _walk(v, fn, f"{path}.{k}")
    elif isinstance(node, list):
        for i, item in enumerate(node):
            _walk(item, fn, f"{path}[{i}]")


def collect() -> dict:
    valid_hc, valid_rule = set(), set()
    for path in sorted(ADAPTER_DIR.glob("*.adapter.v0.1.yaml")):
        adapter = load_yaml(str(path.relative_to(ROOT)))
        valid_hc.update(h["id"] for h in adapter["hard_constraints"])
    conflict = load_yaml(CONFLICT_TABLE)
    valid_rule.update(r["id"] for r in conflict["ordered_rules"])
    valid_rule.update(r["id"] for r in conflict["combination_rules"])

    profiles = {}
    for path in sorted(PROFILE_DIR.glob("*.yaml")):
        doc = load_yaml(str(path.relative_to(ROOT)))
        profiles[doc["profile_id"]] = str(path.relative_to(ROOT))

    adr_ids = set()
    for path in sorted(ADR_DIR.glob("ADR-*.md")):
        adr_ids.add(path.name.split("-")[0] + "-" + path.name.split("-")[1])

    unresolved_paths, unresolved_profiles, unresolved_adrs = [], [], []
    unresolved_constraints, naming = [], []
    docs = {}

    for path in sorted(M2_DIR.rglob("*.yaml")):
        rel = str(path.relative_to(ROOT))
        doc = load_yaml(rel)
        if not isinstance(doc, dict):
            continue
        docs[rel] = doc

        declared = doc.get("artifact_id")
        if declared:
            implied = path.name.rsplit(".yaml", 1)[0]
            if declared != implied:
                naming.append({"file": rel, "declared": declared, "implied": implied})

        def check(key, value, rel=rel):
            if not isinstance(value, str):
                return
            if key in PATH_BEARING_KEYS and "/" in value and not (ROOT / value).exists():
                unresolved_paths.append({"file": rel, "key": key, "value": value})
            if key in PROFILE_BEARING_KEYS and value not in profiles:
                unresolved_profiles.append({"file": rel, "value": value, "available": sorted(profiles)})
            if key in ADR_BEARING_KEYS and value not in adr_ids:
                unresolved_adrs.append({"file": rel, "value": value})

        _walk(doc, check)

        for key in ("bound_hard_constraint_ids", "bound_conflict_priority_rule_ids", "bound_combination_rule_ids"):
            for value in doc.get(key) or []:
                pool = valid_hc if key == "bound_hard_constraint_ids" else valid_rule
                if value not in pool:
                    unresolved_constraints.append({"file": rel, "value": value})

    # 状态字段跨产物一致性
    model = load_yaml(ROLE_MODEL)["project_state"]
    receipts = {}
    for path in sorted((ROOT / "11_reports_and_receipts").glob("m2_ep*/m2_ep*_delivery_receipt.yaml")):
        doc = load_yaml(str(path.relative_to(ROOT)))
        if doc.get("describes_current_state"):
            end = next((v for k, v in doc.items() if k.endswith("_end_state") and isinstance(v, dict)), {})
            receipts[str(path.relative_to(ROOT))] = end

    conflicts = []
    for rel, end in receipts.items():
        for field in ("execution_status", "m2_started", "knowledge_distillation_started", "production_servable"):
            if field in end and end[field] != model.get(field):
                conflicts.append({"field": field, "a": ROLE_MODEL, "a_value": model.get(field),
                                  "b": rel, "b_value": end[field]})

    return {
        "unresolved_paths": unresolved_paths,
        "unresolved_profiles": unresolved_profiles,
        "unresolved_adrs": unresolved_adrs,
        "unresolved_constraint_ids": unresolved_constraints,
        "artifact_id_mismatches": naming,
        "state_field_conflicts": conflicts,
        "profile_count": len(profiles),
        "scanned_file_count": len(docs),
    }


if __name__ == "__main__":
    cli(LABEL, collect, validate)
