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

import importlib.util
import re
import sys

from _common import ROOT, cli, load_json, load_yaml, read_text

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

BRIEF = "01_contracts_and_schemas/m1_object_model_brief.md"
ADAPTER_DIR = "01_contracts_and_schemas/category_adapter_contracts"
PORT_CONTRACT = "01_contracts_and_schemas/extension_port_contracts.v0.1.yaml"
BUNDLE = f"{MODEL_DIR}/StylingResultBundle.schema.v0.1.json"
BUNDLE_PORT_POINTER = "#/properties/backward_compatible_extension_ports/items/enum"
HANDOFF = "01_contracts_and_schemas/m1_interface_handoff.v0.1.yaml"

# Brief 编号表的行数即 M1 交付清单长度。EP01 漏掉第 3 项（human_visual_profile / C-04）没被任何判据
# 抓到，因为覆盖判据只盯 12 输入 + 15 输出，而它不在这 27 个之内——判据覆盖面缺口，EP03 补上。
BRIEF_DELIVERABLE_COUNT = 21

# PRD 13-M1 通过标准的四条。每一条都必须在某个已注册 checker 里有实现，并且有一份 expected=FAIL
# 的 fixture 真的行使它。守的是「判据被悄悄删掉或从没人跑过」，
# **守不住**「判据还在、但 collect 喂给它的值恒假」——那一类只能靠让 collect 读真源来防
# （EP01 的 WOMENSWEAR_RULE_OVERREACH 正是后者，EP02 已改读五份适配器真实声明）。
M1_ACCEPTANCE_JUDGEMENTS = (
    "OBJECT_NOT_ADDRESSABLE",
    "BRAND_CATEGORY_MIXUP",
    "RUNTIME_FACT_IN_LONG_TERM_TRUTH",
    "WOMENSWEAR_RULE_OVERREACH",
)


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

    brief = payload.get("brief_deliverables") or {}
    if brief.get("source_row_count") != BRIEF_DELIVERABLE_COUNT:
        errors.append(
            f"BRIEF_DELIVERABLE_COUNT_DRIFT: the Brief table has {brief.get('source_row_count')} rows, "
            f"expected {BRIEF_DELIVERABLE_COUNT}"
        )
    if brief.get("declared_count") != brief.get("source_row_count"):
        errors.append(
            f"BRIEF_DELIVERABLE_COUNT_DRIFT: coverage map declares {brief.get('declared_count')} items, "
            f"the Brief table has {brief.get('source_row_count')}"
        )
    for row in brief.get("items") or []:
        if not row.get("landing_exists"):
            errors.append(
                f"BRIEF_DELIVERABLE_NOT_LANDED: Brief item #{row.get('index')} points at "
                f"{row.get('landing')!r} which does not resolve"
            )

    for row in payload.get("capability_objects") or []:
        if not row.get("addressable") or not row.get("landing_exists"):
            errors.append(
                f"CAPABILITY_OBJECT_NOT_ADDRESSABLE: {row.get('object_id')} lands at "
                f"{row.get('landing')!r} which does not resolve"
            )

    for ref in payload.get("cross_package_references") or []:
        if not ref.get("exists"):
            errors.append(
                f"CROSS_PACKAGE_REFERENCE_ORPHAN: {ref.get('source')} references "
                f"{ref.get('target')!r} which does not exist"
            )

    ports = payload.get("extension_ports") or {}
    contract_ports = sorted(ports.get("contract_ports") or [])
    bundle_ports = sorted(ports.get("bundle_enum") or [])
    if contract_ports != bundle_ports:
        errors.append(
            f"EXTENSION_PORT_REGISTRY_DRIFT: port contract lists {contract_ports}, "
            f"the Bundle enum lists {bundle_ports}"
        )
    for port in ports.get("unversioned") or []:
        errors.append(f"EXTENSION_PORT_REGISTRY_DRIFT: {port} has no port_version")

    wiring = {row.get("code"): row for row in payload.get("acceptance_judgements") or []}
    for code in M1_ACCEPTANCE_JUDGEMENTS:
        row = wiring.get(code)
        if row is None or not row.get("implemented_in"):
            errors.append(f"M1_ACCEPTANCE_JUDGEMENT_NOT_WIRED: {code} is implemented by no checker")
            continue
        if not row.get("checker_registered"):
            errors.append(
                f"M1_ACCEPTANCE_JUDGEMENT_NOT_WIRED: {code} lives in {row.get('implemented_in')}, "
                "which is not in the run_all_checks list"
            )
        if not row.get("exercised_by_fixture"):
            errors.append(f"M1_ACCEPTANCE_JUDGEMENT_NOT_WIRED: {code} has no expected=FAIL fixture exercising it")

    for row in payload.get("interface_handoff") or []:
        if row.get("handoff") != row.get("upstream"):
            errors.append(
                f"INTERFACE_HANDOFF_STALE: {row.get('surface')} in the handoff is {row.get('handoff')!r}, "
                f"upstream M1 output says {row.get('upstream')!r}"
            )

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


_CHECKER_CACHE: dict = {}


def _load_checker(name: str):
    """按名加载同目录的 checker 模块；加载不了就返回 None，不吞成静默通过。"""
    if name in _CHECKER_CACHE:
        return _CHECKER_CACHE[name]
    path = ROOT / "ci" / "checkers" / f"{name}.py"
    if not path.exists():
        _CHECKER_CACHE[name] = None
        return None
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault(name, module)
    spec.loader.exec_module(module)
    _CHECKER_CACHE[name] = module
    return module


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

    brief_rows = re.findall(r"^\|\s*(\d+)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*$", read_text(BRIEF), re.M)
    brief_cov = coverage["brief_deliverable_coverage"]
    brief_items = [
        {
            "index": row["index"],
            "landing": row["landing"],
            "landing_exists": (ROOT / row["landing"]).exists(),
            "delivered_in": row.get("delivered_in"),
        }
        for row in brief_cov["items"]
    ]

    capability_objects = [
        {
            "object_id": row["object_id"],
            "landing": row["landing"],
            "landing_exists": (ROOT / row["landing"]).exists(),
            "addressable": bool(row.get("addressable")),
        }
        for row in (coverage.get("capability_level_objects") or {}).get("items") or []
    ]

    # 跨包引用完整性：EP02 适配器与 EP03 端口合同指向的每一个仓内路径都必须真实存在。
    cross_refs = []
    for path in sorted((ROOT / ADAPTER_DIR).glob("*.yaml")):
        rel = str(path.relative_to(ROOT))
        doc = load_yaml(rel)
        targets = [doc.get("conflict_priority_ref"), (doc.get("frozen_source") or {}).get("file")]
        for target in targets:
            if isinstance(target, str) and target:
                cross_refs.append({"source": rel, "target": target, "exists": (ROOT / target).exists()})
    port_doc = load_yaml(PORT_CONTRACT)
    for target in [(port_doc.get("frozen_source") or {}).get("file"), (port_doc.get("obligation_ref") or {}).get("file")]:
        if isinstance(target, str) and target:
            cross_refs.append({"source": PORT_CONTRACT, "target": target, "exists": (ROOT / target).exists()})

    adapter_constraints = {}
    for path in sorted((ROOT / ADAPTER_DIR).glob("*.adapter.v0.1.yaml")):
        doc = load_yaml(str(path.relative_to(ROOT)))
        adapter_constraints[doc["category_id"]] = [c["id"] for c in doc["hard_constraints"]]

    bundle_enum = _pointer(load_json(BUNDLE), BUNDLE_PORT_POINTER) or []
    versions = port_doc.get("versioning", {}).get("current_versions") or {}
    extension_ports = {
        "contract_ports": [p["id"] for p in port_doc["ports"]],
        "bundle_enum": list(bundle_enum),
        "unversioned": [p["id"] for p in port_doc["ports"] if not p.get("port_version") or not versions.get(p["id"])],
    }

    # 判据接线：源码里是否实现、checker 是否进全量清单、有没有一份 expected=FAIL 的 fixture 行使它。
    registered = set(re.findall(r'"(check_[a-z0-9_]+)"', read_text("ci/run_all_checks.py")))
    checker_src = {
        path.stem: path.read_text(encoding="utf-8")
        for path in sorted((ROOT / "ci" / "checkers").glob("check_*.py"))
    }
    # 「被 fixture 行使」的定义就是字面意思：真的把 fixture 喂进那个 checker 的 validate()，
    # 看这条判据码有没有出现在返回的错误里。靠文件名或 expected_judgement 字段猜，
    # 猜错了判据照样显绿——那正是本 checker 要防的东西。
    triggered: set[str] = set()
    for path in sorted((ROOT / "ci" / "fixtures").rglob("*.yaml")):
        doc = load_yaml(str(path.relative_to(ROOT)))
        if doc.get("expected") != "FAIL":
            continue
        module = _load_checker(doc["checker"])
        if module is None:
            continue
        triggered.update(err.split(":")[0] for err in module.validate(doc["payload"]))

    acceptance = [
        {
            "code": code,
            "implemented_in": next((name for name, src in checker_src.items() if code in src), None),
            "checker_registered": next(
                (name in registered for name, src in checker_src.items() if code in src), False
            ),
            "exercised_by_fixture": code in triggered,
        }
        for code in M1_ACCEPTANCE_JUDGEMENTS
    ]

    # 交接面是派生件——每一项都必须与上游 M1 产出逐一对得上，对不上就是它过期了（EQ-2）。
    handoff = load_yaml(HANDOFF)
    handoff_rows = [
        {
            "surface": "schema_ids",
            "handoff": sorted(e["schema_id"] for e in handoff["stable_object_surface"]["schemas"]),
            "upstream": sorted(e["schema_id"] for e in registry["entries"]),
        },
        {
            "surface": "style_dimension_ids",
            "handoff": handoff["style_space_surface"]["dimension_ids"],
            "upstream": [d["id"] for d in style["dimensions"]],
        },
        {
            "surface": "category_ids",
            "handoff": sorted(c["category_id"] for c in handoff["category_constraint_surface"]["categories"]),
            "upstream": sorted(adapter_constraints),
        },
        {
            "surface": "extension_port_ids",
            "handoff": [p["id"] for p in handoff["extension_port_surface"]["ports"]],
            "upstream": extension_ports["contract_ports"],
        },
    ]
    for row in handoff["category_constraint_surface"]["categories"]:
        cid = row["category_id"]
        handoff_rows.append(
            {
                "surface": f"{cid}.hard_constraint_ids",
                "handoff": row["hard_constraint_ids"],
                "upstream": adapter_constraints.get(cid, []),
            }
        )

    return {
        "interface_handoff": handoff_rows,
        "brief_deliverables": {
            "source_row_count": len(brief_rows),
            "declared_count": brief_cov["count"],
            "items": brief_items,
        },
        "capability_objects": capability_objects,
        "cross_package_references": cross_refs,
        "extension_ports": extension_ports,
        "acceptance_judgements": acceptance,
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
