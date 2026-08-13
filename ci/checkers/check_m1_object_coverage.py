#!/usr/bin/env python3
"""M1 通过标准的机器形式：不存在未定义对象，12 输入与 15 输出全部可寻址。

PRD 13 节 M1 的通过标准是一句自然语言——「不存在未定义对象、品牌与品类混用、运行时事实
混入长期真源，或女装规则默认覆盖其他品类；6.2 的 15 个输出与内部审计对象在 Schema 层全部
可寻址，无一遗漏」。这里把它拆成可执行判据。

注册表与覆盖映射表都是**派生件**：它们的字段必须与 Schema 文件本身对得上，对不上就是漂移，
而不是「以注册表为准」——那样等于让派生件反过来定义真源（EQ-1）。

M1 通过标准的第四条「女装规则不得默认覆盖其他品类」不在本文件，在 check_m1_category_adapters：
品类规则的真源是五份适配器合同，判据必须读那里。EP01 期间它写在这里，读的是 object_coverage_map
里一个全仓不存在的键，恒为假、永不触发——判据有检出力但 collect 喂它恒假值，属假绿，EP02 迁走并改读真源。
"""

from __future__ import annotations

from _common import ROOT, cli, load_json, load_yaml

LABEL = "check_m1_object_coverage"

CONTRACT = "01_contracts_and_schemas/input_output_boundary.v1.0.yaml"
MODEL_DIR = "01_contracts_and_schemas/m1_object_model"
REGISTRY = f"{MODEL_DIR}/schema_registry.v0.1.yaml"
COVERAGE = f"{MODEL_DIR}/object_coverage_map.v0.1.yaml"
STYLE_SPACE = f"{MODEL_DIR}/brand_style_space.v0.1.yaml"

# PRD 5.3 原文点名的维度数即下限；少于它就是把连续坐标退回成粗标签。
STYLE_DIMENSION_MINIMUM = 14

# 品牌真源里不得出现品类规则（BRAND_CATEGORY_MIXUP）。这些属性名一旦承载真实内容就是混写；
# 允许它们以「显式禁位」形式存在（type: null），因为禁位本身是让违规可被判定。
CATEGORY_RULE_PROPERTY_HINTS = ("category_rule", "category_hard_constraint", "category_adapter")

BRAND_SCOPED_OBJECTS = ("IN-03",)


def validate(payload: dict) -> list[str]:
    errors: list[str] = []

    frozen = payload.get("frozen_counts") or {}
    declared = payload.get("declared_counts") or {}
    for side in ("inputs", "outputs"):
        if frozen.get(side) != declared.get(side):
            errors.append(
                f"OBJECT_COUNT_DRIFT: {side} declared {declared.get(side)}, frozen contract says {frozen.get(side)}"
            )

    seen_landings: dict[str, str] = {}
    for row in payload.get("objects") or []:
        oid = row.get("object_id", "<no id>")
        if not row.get("addressable"):
            errors.append(f"OBJECT_NOT_ADDRESSABLE: {oid} has no schema or contract landing")
            continue
        landing = row.get("landing")
        if not row.get("landing_exists"):
            errors.append(f"LANDING_FILE_MISSING: {oid} points at {landing!r} which does not resolve")
        if landing in seen_landings:
            errors.append(f"DUPLICATE_OBJECT_LANDING: {oid} and {seen_landings[landing]} share landing {landing!r}")
        else:
            seen_landings[landing] = oid
        if row.get("persistence_class_conflict"):
            errors.append(
                f"RUNTIME_FACT_IN_LONG_TERM_TRUTH: {oid} registry says "
                f"{row.get('registry_persistence_class')!r} but the schema declares {row.get('schema_persistence_class')!r}"
            )
        if row.get("object_id") in BRAND_SCOPED_OBJECTS and row.get("category_rule_properties"):
            errors.append(
                f"BRAND_CATEGORY_MIXUP: {oid} carries category-rule properties {row['category_rule_properties']}"
            )

    for entry in payload.get("registry") or []:
        name = entry.get("file", "<no file>")
        if not entry.get("file_exists"):
            errors.append(f"REGISTRY_ENTRY_STALE: {name} is registered but absent from the repository")
            continue
        if entry.get("declared_schema_id") != entry.get("actual_schema_id"):
            errors.append(
                f"REGISTRY_ENTRY_STALE: {name} registers $id {entry.get('declared_schema_id')!r} "
                f"but the file declares {entry.get('actual_schema_id')!r}"
            )
        if not entry.get("schema_version"):
            errors.append(f"SCHEMA_NOT_VERSIONABLE: {name} has no schema_version")
        if entry.get("instance_bearing"):
            if not entry.get("has_positive_fixture"):
                errors.append(f"SCHEMA_WITHOUT_FIXTURE: {name} has no VALID instance fixture")
            if not entry.get("has_negative_fixture"):
                errors.append(f"SCHEMA_WITHOUT_FIXTURE: {name} has no INVALID instance fixture")

    for orphan in payload.get("unregistered_schema_files") or []:
        errors.append(f"SCHEMA_NOT_REGISTERED: {orphan} exists but is absent from the registry")

    style = payload.get("style_space") or {}
    dims = style.get("dimension_ids") or []
    if len(dims) < STYLE_DIMENSION_MINIMUM:
        errors.append(f"STYLE_SPACE_DIMENSION_DRIFT: {len(dims)} dimensions, PRD 5.3 names {STYLE_DIMENSION_MINIMUM}")
    if len(set(dims)) != len(dims):
        errors.append("STYLE_SPACE_DIMENSION_DRIFT: duplicate dimension ids")
    if style.get("declared_count") != len(dims):
        errors.append(
            f"STYLE_SPACE_DIMENSION_DRIFT: declares {style.get('declared_count')} but lists {len(dims)}"
        )

    return errors


def _pointer(doc: dict, pointer: str):
    node = doc
    for part in pointer.lstrip("#/").split("/"):
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    return node


def collect() -> dict:
    contract = load_yaml(CONTRACT)
    registry = load_yaml(REGISTRY)
    coverage = load_yaml(COVERAGE)
    style = load_yaml(STYLE_SPACE)

    schema_files = sorted((ROOT / MODEL_DIR).glob("*.schema.v0.1.json"))
    actual_by_rel = {}
    for path in schema_files:
        rel = f"{MODEL_DIR}/{path.name}"
        actual_by_rel[rel] = load_json(rel)

    fixture_root = ROOT / "ci" / "fixtures" / "m1_schema"
    positives, negatives = set(), set()
    for path in fixture_root.rglob("*.json"):
        fixture = load_json(str(path.relative_to(ROOT)))
        (positives if fixture.get("expected") == "VALID" else negatives).add(fixture.get("schema_id"))

    registry_rows = []
    registered_files = set()
    for entry in registry["entries"]:
        rel = entry["file"]
        registered_files.add(rel)
        actual = actual_by_rel.get(rel)
        registry_rows.append(
            {
                "file": rel,
                "file_exists": actual is not None,
                "declared_schema_id": entry.get("schema_id"),
                "actual_schema_id": (actual or {}).get("$id"),
                "schema_version": (actual or {}).get("schema_version"),
                "instance_bearing": entry.get("instance_bearing", True),
                "has_positive_fixture": entry.get("schema_id") in positives,
                "has_negative_fixture": entry.get("schema_id") in negatives,
            }
        )

    registry_by_id = {e["schema_id"]: e for e in registry["entries"]}

    objects = []
    for side in ("inputs", "outputs"):
        for row in coverage[side]:
            landing = row.get("landing")
            exists = False
            schema_pc = None
            category_props = []
            if landing:
                if "#" in landing:
                    rel, pointer = landing.split("#", 1)
                    doc = actual_by_rel.get(rel)
                    exists = doc is not None and _pointer(doc, pointer) is not None
                else:
                    doc = actual_by_rel.get(landing)
                    exists = doc is not None or (ROOT / landing).exists()
                    if doc:
                        schema_pc = doc.get("persistence_class")
                        for prop in (doc.get("properties") or {}):
                            spec = doc["properties"][prop]
                            if any(h in prop for h in CATEGORY_RULE_PROPERTY_HINTS) and spec.get("type") != "null":
                                category_props.append(prop)
            reg = registry_by_id.get(row.get("schema_id")) if row.get("schema_id") else None
            reg_pc = (reg or {}).get("persistence_class")
            objects.append(
                {
                    "object_id": row.get("object_id"),
                    "landing": landing,
                    "landing_exists": exists,
                    "addressable": bool(row.get("addressable")),
                    "registry_persistence_class": reg_pc,
                    "schema_persistence_class": schema_pc,
                    "persistence_class_conflict": bool(reg_pc and schema_pc and reg_pc != schema_pc),
                    "category_rule_properties": category_props,
                }
            )

    return {
        "frozen_counts": {
            "inputs": contract["input_and_configuration_objects"]["count"],
            "outputs": contract["output_and_internal_audit_objects"]["count"],
        },
        "declared_counts": {
            "inputs": len(coverage["inputs"]),
            "outputs": len(coverage["outputs"]),
        },
        "objects": objects,
        "registry": registry_rows,
        "unregistered_schema_files": sorted(set(actual_by_rel) - registered_files),
        "style_space": {
            "declared_count": style["dimension_count"],
            "dimension_ids": [d["id"] for d in style["dimensions"]],
        },
    }


if __name__ == "__main__":
    cli(LABEL, collect, validate)
