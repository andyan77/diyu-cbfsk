#!/usr/bin/env python3
"""D-28 三层评分卡：分类齐备、②③类禁唯一 Gold Answer、绑定 ID 必须真实存在。

三条纪律各自成判据：

  三分类强制   —— 每道题必须归入且只归入一类；三类齐备，缺一即失败。
  禁唯一答案   —— mechanism_correctness 与 open_decision 一律 gold_answer_allowed=false，
                  且必须保全合法分歧（must_not_score_disagreement_as_error）。
                  违反即 SINGLE_GOLD_ANSWER_ON_OPEN_TASK，触发 SC-20 停止 M2 冻结。
  禁悬空表述   —— 每张卡绑定的 hard_constraint_id / conflict_priority_rule_id / combination_rule_id
                  必须在 M1 品类适配合同与冲突优先级表里真实存在。绑一个不存在的 ID，
                  评分时才会发现判据没有落点。

反自审绿（E12）：合法 ID 集合从 M1 的五份适配器与冲突优先级表**独立重算**，
不从评分卡自己的声明读——拿被检对象当真值，绑错了也会显绿。
constraint_correctness 另做双向覆盖：25 条硬约束一条不漏，多绑一条不存在的也失败。
"""

from __future__ import annotations

import pathlib

from _common import ROOT, cli, load_yaml

LABEL = "check_m2_scoring_cards"

SCORING_DIR = "03_m2_evaluation_foundation/scoring"
TASK_CLASS_CONTRACT = f"{SCORING_DIR}/evaluation_task_class_contract.v0.1.yaml"
STABILITY_METRIC = f"{SCORING_DIR}/decision_logic_stability_rate.v0.1.yaml"
ADAPTER_DIR = ROOT / "01_contracts_and_schemas" / "category_adapter_contracts"
CONFLICT_TABLE = "01_contracts_and_schemas/category_adapter_contracts/cross_category_conflict_priority.v0.1.yaml"

REQUIRED_CLASSES = ("constraint_correctness", "mechanism_correctness", "open_decision")
GOLD_ANSWER_FORBIDDEN_FOR = frozenset({"mechanism_correctness", "open_decision"})

# D-28：②③类的冻结对象是可接受决策边界，不是参考答案。
REQUIRED_FROZEN_OBJECT = "acceptable_decision_boundary"

STABILITY_THRESHOLD = ">= 85%"
FORBIDDEN_LIVE_METRIC_NAME = "核心判断重复一致率"


def validate(payload: dict) -> list[str]:
    errors: list[str] = []

    # --- 三分类合同 ---
    declared = payload.get("contract_classes") or []
    for name in REQUIRED_CLASSES:
        if name not in declared:
            errors.append(f"EVALUATION_TASK_CLASS_MISSING: {name} absent from the task-class contract")
    for extra in sorted(set(declared) - set(REQUIRED_CLASSES)):
        errors.append(f"EVALUATION_TASK_CLASS_UNEXPECTED: {extra} is not one of the three D-28 classes")
    if payload.get("contract_class_count") != len(declared):
        errors.append(
            f"EVALUATION_TASK_CLASS_COUNT_DRIFT: contract declares {payload.get('contract_class_count')!r} "
            f"but lists {len(declared)}"
        )
    if payload.get("single_class_per_item") is not True:
        errors.append("EVALUATION_TASK_CLASS_AMBIGUOUS: single_class_per_item must be true")
    if sorted(payload.get("contract_gold_answer_forbidden_for") or []) != sorted(GOLD_ANSWER_FORBIDDEN_FOR):
        errors.append(
            f"OPEN_TASK_GOLD_ANSWER_RULE_DRIFT: contract forbids gold answers for "
            f"{sorted(payload.get('contract_gold_answer_forbidden_for') or [])}, "
            f"D-28 requires {sorted(GOLD_ANSWER_FORBIDDEN_FOR)}"
        )

    # --- 每类必须有卡，且卡与合同互相对得上 ---
    cards = payload.get("cards") or []
    card_classes = [c.get("evaluation_task_class") for c in cards]
    for name in REQUIRED_CLASSES:
        if name not in card_classes:
            errors.append(f"SCORECARD_MISSING: no scorecard for {name}")
    for name in sorted({c for c in card_classes if card_classes.count(c) > 1}):
        errors.append(f"SCORECARD_DUPLICATE: {name} has more than one scorecard")

    valid_hc = set(payload.get("valid_hard_constraint_ids") or [])
    valid_cp = set(payload.get("valid_conflict_priority_rule_ids") or [])
    valid_combo = set(payload.get("valid_combination_rule_ids") or [])

    for card in cards:
        cid = card.get("evaluation_task_class", "<no class>")

        if cid in GOLD_ANSWER_FORBIDDEN_FOR:
            if card.get("gold_answer_allowed") is not False:
                errors.append(
                    f"SINGLE_GOLD_ANSWER_ON_OPEN_TASK: {cid} allows a gold answer — "
                    "触发 SC-20，停止 M2 冻结"
                )
            if card.get("must_not_score_disagreement_as_error") is not True:
                errors.append(
                    f"LEGITIMATE_DISAGREEMENT_SCORED_AS_ERROR: {cid} does not preserve legitimate disagreement"
                )
            if card.get("frozen_object") != REQUIRED_FROZEN_OBJECT:
                errors.append(
                    f"FROZEN_OBJECT_DRIFT: {cid} freezes {card.get('frozen_object')!r}, "
                    f"D-28 requires {REQUIRED_FROZEN_OBJECT!r}"
                )
            if card.get("gold_answer_field_is_null_const") is not True:
                errors.append(
                    f"SINGLE_GOLD_ANSWER_ON_OPEN_TASK: {cid} has no gold_answer null-constant guard — "
                    "禁位必须是显式常量，不能只写在散文里"
                )

        if cid == "constraint_correctness":
            if card.get("gold_answer_allowed") is not True:
                errors.append("CONSTRAINT_CLASS_GOLD_ANSWER_DENIED: 硬约束题只有违反与不违反两种事实状态")
            if card.get("partial_credit_allowed") is not False:
                errors.append(
                    "CONSTRAINT_PARTIAL_CREDIT_ALLOWED: 给硬约束打半分等于承认「违反了一半安全约束」"
                )

        # --- 悬空绑定 ---
        if not card.get("has_any_binding"):
            errors.append(
                f"SCORECARD_BINDING_EMPTY: {cid} binds no M1 constraint or conflict-priority rule — "
                "禁止悬空表述"
            )
        for hid in card.get("bound_hard_constraint_ids") or []:
            if hid not in valid_hc:
                errors.append(f"SCORECARD_BINDING_UNRESOLVED: {cid} binds hard constraint {hid!r}, which does not exist")
        for rid in card.get("bound_conflict_priority_rule_ids") or []:
            if rid not in valid_cp:
                errors.append(f"SCORECARD_BINDING_UNRESOLVED: {cid} binds conflict rule {rid!r}, which does not exist")
        for rid in card.get("bound_combination_rule_ids") or []:
            if rid not in valid_combo:
                errors.append(f"SCORECARD_BINDING_UNRESOLVED: {cid} binds combination rule {rid!r}, which does not exist")

        if card.get("threshold_status") != "M2_FREEZE_REQUIRED":
            errors.append(
                f"THRESHOLD_FROZEN_OUTSIDE_M2_FREEZE: {cid} threshold_status="
                f"{card.get('threshold_status')!r}, EP02 不得代为冻结阈值"
            )
        if card.get("threshold_value") is not None:
            errors.append(
                f"THRESHOLD_FROZEN_OUTSIDE_M2_FREEZE: {cid} already carries threshold "
                f"{card.get('threshold_value')!r}"
            )

    # --- constraint_correctness 双向覆盖 ---
    covered = set(payload.get("constraint_card_bound_ids") or [])
    for missing in sorted(valid_hc - covered):
        errors.append(
            f"HARD_CONSTRAINT_NOT_SCORED: {missing} exists in M1 but no scorecard binds it — "
            "漏一条硬约束就是漏一条安全判据"
        )

    # --- 稳定率口径 ---
    metric = payload.get("stability_metric") or {}
    if metric.get("canonical_name") != "核心决策逻辑稳定率":
        errors.append(f"STALE_METRIC_NAME: canonical_name={metric.get('canonical_name')!r}")
    if metric.get("threshold") != STABILITY_THRESHOLD:
        errors.append(f"METRIC_THRESHOLD_CHANGED: expected {STABILITY_THRESHOLD}, got {metric.get('threshold')!r}")
    if metric.get("threshold_changed_by_rename") is not False:
        errors.append("METRIC_THRESHOLD_CHANGED: rename must not change the threshold")
    if metric.get("former_name") == metric.get("canonical_name"):
        errors.append(f"STALE_METRIC_NAME: {FORBIDDEN_LIVE_METRIC_NAME} reinstated as the live metric name")
    if metric.get("solution_family_aware") is not True:
        errors.append(
            "SOLUTION_FAMILY_UNAWARE_STABILITY: 落在不同合法解族被算作不稳定，会把合理多解判成缺陷（D-28）"
        )
    if not metric.get("logic_identity_basis"):
        errors.append("STABILITY_BASIS_UNDEFINED: 未说明「逻辑一致」以什么为准，指标无法复算")

    return errors


def collect() -> dict:
    contract = load_yaml(TASK_CLASS_CONTRACT)
    metric = load_yaml(STABILITY_METRIC)
    conflict = load_yaml(CONFLICT_TABLE)

    # 合法 ID 从 M1 真源独立重算，不从评分卡读
    valid_hc, valid_cp, valid_combo = set(), set(), set()
    for path in sorted(ADAPTER_DIR.glob("*.adapter.v0.1.yaml")):
        adapter = load_yaml(str(path.relative_to(ROOT)))
        valid_hc.update(h["id"] for h in adapter["hard_constraints"])
    valid_cp.update(r["id"] for r in conflict["ordered_rules"])
    valid_combo.update(r["id"] for r in conflict["combination_rules"])

    cards, constraint_bound = [], []
    for path in sorted((ROOT / SCORING_DIR).glob("scorecard_*.yaml")):
        card = load_yaml(str(path.relative_to(ROOT)))
        hc = card.get("bound_hard_constraint_ids") or []
        cp = card.get("bound_conflict_priority_rule_ids") or []
        combo = card.get("bound_combination_rule_ids") or []
        gold_field = (card.get("machine_checkable_fields") or {}).get("gold_answer") or {}
        if card.get("evaluation_task_class") == "constraint_correctness":
            constraint_bound = list(hc)
        cards.append(
            {
                "evaluation_task_class": card.get("evaluation_task_class"),
                "gold_answer_allowed": card.get("gold_answer_allowed"),
                "must_not_score_disagreement_as_error": card.get("must_not_score_disagreement_as_error"),
                "frozen_object": card.get("frozen_object"),
                "partial_credit_allowed": card.get("partial_credit_allowed"),
                "bound_hard_constraint_ids": hc,
                "bound_conflict_priority_rule_ids": cp,
                "bound_combination_rule_ids": combo,
                "has_any_binding": bool(hc or cp or combo),
                "gold_answer_field_is_null_const": gold_field.get("type") == "null",
                "threshold_status": card.get("threshold_status"),
                "threshold_value": card.get("threshold_value"),
            }
        )

    return {
        "contract_classes": [c["evaluation_task_class"] for c in contract["classes"]],
        "contract_class_count": contract["class_count"],
        "contract_gold_answer_forbidden_for": contract["gold_answer_forbidden_for"],
        "single_class_per_item": contract["single_class_per_item"],
        "cards": cards,
        "constraint_card_bound_ids": constraint_bound,
        "valid_hard_constraint_ids": sorted(valid_hc),
        "valid_conflict_priority_rule_ids": sorted(valid_cp),
        "valid_combination_rule_ids": sorted(valid_combo),
        "stability_metric": {
            "canonical_name": metric["canonical_name"],
            "former_name": metric["former_name"],
            "threshold": metric["threshold"],
            "threshold_changed_by_rename": metric["threshold_changed_by_rename"],
            "solution_family_aware": metric["computation"]["solution_family_aware"],
            "logic_identity_basis": metric["computation"]["logic_identity_basis"],
        },
    }


if __name__ == "__main__":
    cli(LABEL, collect, validate)
