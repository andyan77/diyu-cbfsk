#!/usr/bin/env python3
"""五类品类适配合同：各自硬约束齐备、冲突优先级唯一、女装规则不得默认覆盖其他品类。

判据来源是 M0 已冻结的 category_scope_contract.v1.0（五类、硬约束家族、审查覆盖率）与
input_output_boundary.v1.0（失败关闭）、non_goals_and_stop_conditions.v1.0（停止条件）。
适配器只是把这些冻结裁决落成可判定的合同，不新增产品裁决——所以这里逐字段比对冻结源，
对不上就是漂移，而不是「以适配器为准」。

WOMENSWEAR_RULE_OVERREACH 从 check_m1_object_coverage 迁到这里（EQ-1 只留一份实现）。
迁移原因不是归类美学：原实现读的是 object_coverage_map 里一个**全仓不存在**的键
（category_defaults.womenswear_rules_apply_to_other_categories_by_default），恒为 None，
判据在真实仓库上永远不响——fixture 能触发它，collect 却喂它恒假值，属假绿。
现在它读的是五份适配器的真实声明。
"""

from __future__ import annotations

from _common import ROOT, cli, load_yaml

LABEL = "check_m1_category_adapters"

FROZEN_CONTRACT = "01_contracts_and_schemas/category_scope_contract.v1.0.yaml"
ADAPTER_DIR = "01_contracts_and_schemas/category_adapter_contracts"
CONFLICT_PRIORITY_FILE = f"{ADAPTER_DIR}/cross_category_conflict_priority.v0.1.yaml"
CONFLICT_PRIORITY_CONTRACT_ID = "cross_category_conflict_priority.v0.1"

# 冻结合同 launch_categories.count = 5。collect 读不到五类就是根本没扫到东西（覆盖面下限）。
MINIMUM_FROZEN_CATEGORIES = 5

WOMENSWEAR = "CAT-WOMENSWEAR"

# category_safety_by_design 原文点名的三类：必须具有独立的安全、功能、年龄适当性和表达边界。
SAFETY_CRITICAL = ("CAT-KIDSWEAR", "CAT-TEEN-TREND", "CAT-SPORT-TREND")

# PRD 6.4 缺失输入失败关闭：FC-05 童装/青少年年龄与场景，FC-06 运动功能信息。
REQUIRED_FAIL_CLOSED = {
    "CAT-KIDSWEAR": "FC-05",
    "CAT-TEEN-TREND": "FC-05",
    "CAT-SPORT-TREND": "FC-06",
}
# PRD 16.2 SC-06：童装、青少年或运动安全硬门失败 → 对应品类立即关闭 Serving。
REQUIRED_STOP_CONDITION = "SC-06"

# PRD 9.4 category_rules 原文：运动品类不得把视觉建议包装为专业性能、伤病预防或医疗效果。
SPORT_FORBIDDEN_CLAIMS = ("专业性能", "伤病预防", "医疗效果")

# category_safety_by_design.founder_review_coverage：高风险知识 100%，不得抽样。
REQUIRED_REVIEW_COVERAGE = "100%"

STRICTER_OF = "stricter_of"

# 逐字段比对冻结源的字段名 → 漂移即失败。core_audience 等文字字段一并比，
# 因为「适配器悄悄改写了品类定义」和「改了硬约束家族」是同一类问题。
FROZEN_MIRROR_FIELDS = (
    "hard_constraint_family",
    "founder_full_review_required",
    "core_audience",
    "unique_professional_contract",
    "forbidden",
)


def _required_full_review(adapters: list[dict]) -> set[str]:
    """必须 100% 不抽样的品类 = 三类高风险 ∪ 以 stricter_of 与其组合的品类。

    亲子本身不在冻结合同点名的高风险清单里，但它按 CP-02 取更严地与童装/青少年组合，
    因此审查强度不能低于被组合的一侧——否则「取更严」在审查这一维上就是空话。
    """
    required = set(SAFETY_CRITICAL)
    for adapter in adapters:
        if adapter.get("composition_resolution") != STRICTER_OF:
            continue
        if any(c in SAFETY_CRITICAL for c in adapter.get("composes_with") or []):
            required.add(adapter.get("category_id"))
    return required


def validate(payload: dict) -> list[str]:
    errors: list[str] = []

    frozen = payload.get("frozen_categories") or []
    adapters = payload.get("adapters") or []
    priority = payload.get("conflict_priority") or {}

    if len(frozen) < MINIMUM_FROZEN_CATEGORIES:
        errors.append(
            f"CATEGORY_ADAPTER_COVERAGE_BELOW_FLOOR: {len(frozen)} frozen categories read, "
            f"the frozen contract declares {MINIMUM_FROZEN_CATEGORIES}"
        )

    frozen_by_id = {c.get("id"): c for c in frozen}

    by_category: dict[str, list[str]] = {}
    for adapter in adapters:
        by_category.setdefault(adapter.get("category_id"), []).append(adapter.get("file", "<no file>"))
    for cid, files in sorted(by_category.items()):
        if len(files) > 1:
            errors.append(f"CATEGORY_ADAPTER_DUPLICATE: {cid} is defined by {len(files)} adapters: {sorted(files)}")

    for cid in sorted(frozen_by_id):
        if cid not in by_category:
            errors.append(f"CATEGORY_ADAPTER_MISSING: frozen category {cid} has no adapter contract")

    required_full_review = _required_full_review(adapters)

    for adapter in adapters:
        cid = adapter.get("category_id")
        where = adapter.get("file", "<no file>")
        source = frozen_by_id.get(cid)
        if source is None:
            errors.append(f"CATEGORY_ID_DRIFT: {where} declares {cid!r}, absent from the frozen five categories")
            continue

        for field in FROZEN_MIRROR_FIELDS:
            if adapter.get(field) != source.get(field):
                errors.append(
                    f"HARD_CONSTRAINT_FAMILY_DRIFT: {cid}.{field} is {adapter.get(field)!r} "
                    f"but the frozen contract says {source.get(field)!r}"
                )

        overreach = []
        if adapter.get("is_default_for_other_categories"):
            overreach.append("is_default_for_other_categories=true")
        foreign = [c for c in adapter.get("applies_to_categories") or [] if c != cid]
        if foreign:
            overreach.append(f"applies_to_categories includes {foreign}")
        inherited = adapter.get("inherits_category_rules_from")
        if overreach:
            code = "WOMENSWEAR_RULE_OVERREACH" if cid == WOMENSWEAR else "CATEGORY_RULE_OVERREACH"
            errors.append(f"{code}: {cid} claims reach beyond itself — {'; '.join(overreach)}")
        if inherited:
            code = "WOMENSWEAR_RULE_OVERREACH" if inherited == WOMENSWEAR else "CATEGORY_RULE_OVERREACH"
            errors.append(f"{code}: {cid} inherits category rules from {inherited}")

        if cid in SAFETY_CRITICAL and not adapter.get("safety_critical_constraint_ids"):
            errors.append(f"CATEGORY_SAFETY_RULE_MISSING: {cid} declares no safety-critical hard constraint")

        needed_fc = REQUIRED_FAIL_CLOSED.get(cid)
        if needed_fc and needed_fc not in (adapter.get("fail_closed_bindings") or []):
            errors.append(f"FAIL_CLOSED_BINDING_MISSING: {cid} does not bind {needed_fc}")

        if cid in SAFETY_CRITICAL and REQUIRED_STOP_CONDITION not in (adapter.get("stop_condition_bindings") or []):
            errors.append(f"STOP_CONDITION_BINDING_MISSING: {cid} does not bind {REQUIRED_STOP_CONDITION}")

        if cid == "CAT-SPORT-TREND":
            declared = adapter.get("forbidden_claims") or []
            missing = [c for c in SPORT_FORBIDDEN_CLAIMS if c not in declared]
            if missing:
                errors.append(f"SPORT_PERFORMANCE_CLAIM_ALLOWED: {cid} leaves {missing} unforbidden")

        if adapter.get("conflict_priority_ref") != priority.get("canonical_file"):
            errors.append(
                f"CONFLICT_PRIORITY_NOT_REFERENCED: {cid} points at "
                f"{adapter.get('conflict_priority_ref')!r}, not the canonical table"
            )

        if cid in required_full_review:
            if adapter.get("founder_review_coverage") != REQUIRED_REVIEW_COVERAGE:
                errors.append(
                    f"FOUNDER_REVIEW_COVERAGE_DRIFT: {cid} declares coverage "
                    f"{adapter.get('founder_review_coverage')!r}, required {REQUIRED_REVIEW_COVERAGE}"
                )
            if adapter.get("founder_review_sampling_allowed"):
                errors.append(f"FOUNDER_REVIEW_COVERAGE_DRIFT: {cid} allows sampling on high-risk knowledge")

    declaring = priority.get("declaring_files") or []
    if len(declaring) != 1:
        errors.append(
            f"CONFLICT_PRIORITY_TABLE_NOT_UNIQUE: {len(declaring)} file(s) declare "
            f"{CONFLICT_PRIORITY_CONTRACT_ID}: {sorted(declaring)}"
        )

    for rule in priority.get("combination_rules") or []:
        if rule.get("resolution") != STRICTER_OF:
            errors.append(
                f"MIXED_AGE_RESOLUTION_NOT_STRICTER: {rule.get('id')} resolves "
                f"{rule.get('combination')} by {rule.get('resolution')!r}, not {STRICTER_OF!r}"
            )

    return errors


def collect() -> dict:
    contract = load_yaml(FROZEN_CONTRACT)
    frozen = [
        {
            "id": item["id"],
            "hard_constraint_family": item.get("hard_constraint_family"),
            "founder_full_review_required": bool(item.get("founder_full_review_required", False)),
            "core_audience": item.get("core_audience"),
            "unique_professional_contract": item.get("unique_professional_contract"),
            "forbidden": item.get("forbidden") or [],
        }
        for item in contract["launch_categories"]["items"]
    ]

    adapters = []
    for path in sorted((ROOT / ADAPTER_DIR).glob("*.adapter.v0.1.yaml")):
        rel = f"{ADAPTER_DIR}/{path.name}"
        doc = load_yaml(rel)
        scope = doc.get("scope") or {}
        review = doc.get("founder_review") or {}
        constraints = doc.get("hard_constraints") or []
        adapters.append(
            {
                "file": rel,
                "category_id": doc.get("category_id"),
                "hard_constraint_family": doc.get("hard_constraint_family"),
                "founder_full_review_required": bool(doc.get("founder_full_review_required", False)),
                "core_audience": doc.get("core_audience"),
                "unique_professional_contract": doc.get("unique_professional_contract"),
                "forbidden": doc.get("forbidden") or [],
                "applies_to_categories": scope.get("applies_to_categories") or [],
                "is_default_for_other_categories": bool(scope.get("is_default_for_other_categories")),
                "inherits_category_rules_from": scope.get("inherits_category_rules_from"),
                "composes_with": scope.get("composes_with") or [],
                "composition_resolution": scope.get("composition_resolution"),
                "hard_constraint_ids": [c["id"] for c in constraints],
                "safety_critical_constraint_ids": [
                    c["id"] for c in constraints if c.get("severity") == "safety_critical"
                ],
                "fail_closed_bindings": doc.get("fail_closed_bindings") or [],
                "stop_condition_bindings": doc.get("stop_condition_bindings") or [],
                "forbidden_claims": doc.get("forbidden_claims") or [],
                "conflict_priority_ref": doc.get("conflict_priority_ref"),
                "founder_review_coverage": review.get("coverage"),
                "founder_review_sampling_allowed": bool(review.get("sampling_allowed")),
            }
        )

    # 唯一性靠全仓扫 contract_id，而不是靠「我只写了一份」的自我保证。
    declaring = []
    for path in sorted(ROOT.rglob("*.yaml")):
        if ".git" in path.parts or "ci/fixtures" in str(path.relative_to(ROOT)):
            continue
        try:
            doc = load_yaml(str(path.relative_to(ROOT)))
        except Exception:  # noqa: BLE001 - 非 YAML 或坏文件不参与唯一性判定
            continue
        if isinstance(doc, dict) and doc.get("contract_id") == CONFLICT_PRIORITY_CONTRACT_ID:
            declaring.append(str(path.relative_to(ROOT)))

    table = load_yaml(CONFLICT_PRIORITY_FILE)
    return {
        "frozen_categories": frozen,
        "adapters": adapters,
        "conflict_priority": {
            "canonical_file": CONFLICT_PRIORITY_FILE,
            "declaring_files": declaring,
            "combination_rules": [
                {"id": r["id"], "combination": r["combination"], "resolution": r["resolution"]}
                for r in table["combination_rules"]
            ],
        },
    }


if __name__ == "__main__":
    cli(LABEL, collect, validate)
