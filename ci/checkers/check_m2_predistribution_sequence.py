#!/usr/bin/env python3
"""分发前序列：审阅队列、五步闸、阈值裁决工作表合同。

裁决 EP06-001 把「分发校准包」从一个动作改成一道五步闸：
执行侧出队列并补报哈希 → Founder 确认队列并交回 STORE-A 证据 → 执行侧一次性收口 →
两侧各做一次 Delta → 才可分发。理由是分发那一刻起，包的内容被 180 条评审记录锚定，
之后改一个字，两位评审员已经做的判定全部作废。

本判据守三件事：

  队列是派生物 —— 90 行里只有四列由人写（摘要、依据锚点、依据、把握度），其余现取自校准集与锚点真源。
                  判据重新派生逐字节比对；「需重点确认」子表的成员由判据现算，不由执行侧挑。
                  人挑的清单会不知不觉只剩下自己也觉得有问题的那几行。
  闸不能自己往前走 —— 第 2 步是 Founder 的步，它的完成与否由现场证据决定（锚点真源的绑定字段、
                  STORE-A 收件目录里的文件），不由本仓的一行 status 决定。
                  guardian_review_allowed 在第 3 步产出候选之前必须是 false——
                  解除禁令不等于「现在就可以发起」，被审对象还不存在。
  工作表到期才出 —— 六列里有一列是分歧分布，要从两侧回收的记录里算。记录为 0 条时它只能留空或者编。
                  合同先钉死形状，两侧一旦有记录而工作表还没出，本判据当场追缴。

反自审绿：队列的真值来自校准集与锚点真源，不来自队列自己；记录条数数 JSONL 实际行数，
不读 state 文件的自述；工作表指标全集取自 metric_review_unit_mapping，不取自工作表合同的自述。
"""

from __future__ import annotations

import importlib.util

from _common import PACK_SCAN_EXCLUDED, ROOT, cli, load_yaml, read_text

LABEL = "check_m2_predistribution_sequence"

RULING = "governance/founder_rulings/DIYU-CBFSK-FOUNDER-M2-EP06-001.yaml"
ANNOTATIONS = "03_m2_evaluation_foundation/calibration/founder_review_queue_annotations.v0.1.yaml"
QUEUE = "03_m2_evaluation_foundation/calibration/founder_review_queue.v0.1.md"
CAL = "03_m2_evaluation_foundation/calibration/public_calibration_set.v0.1.yaml"
ANCHOR_TRUTH = "03_m2_evaluation_foundation/calibration/founder_boundary_anchor_truth.v0.1.yaml"
SEQUENCE = "governance/conditions/predistribution_sequence.v0.1.yaml"
WORKSHEET_CONTRACT = "03_m2_evaluation_foundation/calibration/threshold_decision_worksheet_contract.v0.1.yaml"
MAPPING = "03_m2_evaluation_foundation/calibration/metric_review_unit_mapping.v0.1.yaml"
REVIEW_STATE = "03_m2_evaluation_foundation/calibration/calibration_review_state.v0.1.yaml"
TIMING_GATE = "governance/conditions/hidden_generation_timing_gate.v0.1.yaml"
PACK = "03_m2_evaluation_foundation/calibration/launch_pack"
COMMIT_LEDGER = "governance/receipts/m2_package_commit_ledger.yaml"

SUMMARY_MAX = 60
BASIS_MAX = 40
CONFIDENCE_VALUES = ("high", "low")
FORBIDDEN_BASIS_PHRASE = "综合判断"
OPEN_CLASS = "open_decision"
STEP_STATUSES = ("COMPLETE", "NOT_STARTED", "BLOCKED_BY_STEP_2", "BLOCKED_BY_STEP_3", "BLOCKED_BY_STEP_4")
EXPECTED_STEPS = 5
WORKSHEET_FIELDS = 6
WORKSHEET_OPTIONS = 3
# 队列带着锚点判定这一列；它出现在分发包里就是把答案发出去。
QUEUE_LEAK_TOKENS = ("锚点判定", "founder_review_queue")
FULL_HASH_LENGTH = 40

_BUILDER = None


def _builder():
    global _BUILDER
    if _BUILDER is None:
        spec = importlib.util.spec_from_file_location(
            "build_founder_review_queue", ROOT / "ci" / "tools" / "build_founder_review_queue.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        _BUILDER = module
    return _BUILDER


def _validate_queue(payload: dict, errors: list[str]) -> None:
    cases = {c["case_id"]: c for c in payload.get("cases") or []}
    anchors = {a["case_id"]: a for a in payload.get("anchors") or []}
    notes = payload.get("annotations") or []

    for rel in payload.get("queue_derivation_drift") or []:
        errors.append(
            f"REVIEW_QUEUE_DERIVATION_DRIFT: {rel} differs from re-deriving it out of the calibration set, "
            "the anchor truth and the annotations — 队列是派生物，不是第二份标注"
        )

    seen: set[str] = set()
    for note in notes:
        cid = note.get("case_id", "<no id>")
        if cid in seen:
            errors.append(f"REVIEW_QUEUE_COVERAGE_INCOMPLETE: {cid} is annotated more than once")
        seen.add(cid)
        case = cases.get(cid)
        if case is None:
            errors.append(f"REVIEW_QUEUE_COVERAGE_INCOMPLETE: annotation names {cid!r}, not a case in the set")
            continue

        summary = note.get("candidate_summary") or ""
        basis = note.get("judgment_basis") or ""
        if len(summary) > SUMMARY_MAX:
            errors.append(f"REVIEW_QUEUE_FIELD_TOO_LONG: {cid} candidate_summary is {len(summary)} chars > {SUMMARY_MAX}")
        if len(basis) > BASIS_MAX:
            errors.append(f"REVIEW_QUEUE_FIELD_TOO_LONG: {cid} judgment_basis is {len(basis)} chars > {BASIS_MAX}")
        if not summary.strip():
            errors.append(f"REVIEW_QUEUE_FIELD_TOO_LONG: {cid} has an empty candidate_summary")
        if FORBIDDEN_BASIS_PHRASE in basis:
            errors.append(
                f"REVIEW_QUEUE_BASIS_IS_GENERAL_JUDGEMENT: {cid} writes {FORBIDDEN_BASIS_PHRASE!r} as its basis — "
                "依据必须指向被触发或未触发的具体硬门或边界条款"
            )

        anchor_id = note.get("basis_anchor")
        allowed = set(case.get("hard_gate_refs") or [])
        for key in ("constraint_ref", "acceptable_decision_boundary_ref"):
            if case.get(key):
                allowed.add(case[key])
        if anchor_id not in allowed:
            errors.append(
                f"REVIEW_QUEUE_BASIS_ANCHOR_UNRESOLVED: {cid} anchors its basis on {anchor_id!r}, "
                f"which the case does not declare (declares {sorted(allowed)})"
            )
        elif anchor_id not in basis:
            errors.append(
                f"REVIEW_QUEUE_BASIS_NOT_ANCHORED: {cid} names {anchor_id} in its field but not in the basis text"
            )

        confidence = note.get("authoring_confidence")
        if confidence not in CONFIDENCE_VALUES:
            errors.append(f"REVIEW_QUEUE_CONFIDENCE_INVALID: {cid} carries authoring_confidence {confidence!r}")
        elif confidence == "low" and not (note.get("low_confidence_reason") or "").strip():
            errors.append(
                f"REVIEW_QUEUE_LOW_CONFIDENCE_WITHOUT_REASON: {cid} is low confidence with no reason — "
                "「我也拿不准」不写清拿不准什么，Founder 无法重点看"
            )
        if note.get("open_family_boundary_subjective") and case.get("evaluation_task_class") != OPEN_CLASS:
            errors.append(
                f"REVIEW_QUEUE_SUBJECTIVE_FLAG_ON_WRONG_CLASS: {cid} is "
                f"{case.get('evaluation_task_class')}, not {OPEN_CLASS}"
            )

    for cid in cases:
        if cid not in seen:
            errors.append(f"REVIEW_QUEUE_COVERAGE_INCOMPLETE: no annotation for {cid}")

    # 子表成员现算，与队列文本里实际列出的行比对。
    expected_focus: set[str] = set()
    for note in notes:
        cid = note.get("case_id")
        case = cases.get(cid)
        if case is None:
            continue
        if len(case.get("hard_gate_refs") or []) != 1:
            expected_focus.add(cid)
        if note.get("open_family_boundary_subjective"):
            expected_focus.add(cid)
        if note.get("authoring_confidence") == "low":
            expected_focus.add(cid)
    listed = set(payload.get("queue_focus_rows") or [])
    if listed != expected_focus:
        errors.append(
            f"REVIEW_QUEUE_FOCUS_SET_MISSTATED: the queue lists {len(listed)} focus rows, "
            f"the three criteria select {len(expected_focus)}; "
            f"missing {sorted(expected_focus - listed)[:5]}, extra {sorted(listed - expected_focus)[:5]}"
        )

    # 队列里的锚点判定必须与锚点真源同值——队列是唯一会被 Founder 逐行读的地方，读错一行就确认错一行。
    for cid, label in (payload.get("queue_anchor_calls") or {}).items():
        truth = (anchors.get(cid) or {}).get("boundary_position")
        expected = {"inside": "界内", "outside": "越界", "boundary_high_value": "边界高价值位"}.get(truth)
        if label != expected:
            errors.append(
                f"REVIEW_QUEUE_ANCHOR_CALL_DRIFT: {cid} shows {label!r} in the queue, "
                f"the anchor truth records {truth!r}"
            )

    for item in payload.get("shared_question_affects") or []:
        for cid in item["affects"]:
            if cid not in cases:
                errors.append(
                    f"REVIEW_QUEUE_SHARED_QUESTION_UNRESOLVED: {item['id']} names {cid!r}, not a case in the set"
                )

    for hit in payload.get("queue_pack_leaks") or []:
        errors.append(
            f"REVIEW_QUEUE_IN_DISTRIBUTION_PACK: {hit['file']} contains {hit['token']!r} — "
            "队列带着锚点判定这一列，进了包就是把答案发出去"
        )


def _validate_sequence(payload: dict, errors: list[str]) -> None:
    steps = payload.get("steps") or []
    if len(steps) != EXPECTED_STEPS:
        errors.append(f"SEQUENCE_STEP_COUNT_MISSTATED: contract holds {len(steps)} steps, must be {EXPECTED_STEPS}")

    numbers = [s.get("step") for s in steps]
    if numbers != list(range(1, len(steps) + 1)):
        errors.append(f"PREDISTRIBUTION_STEP_OUT_OF_ORDER: steps are numbered {numbers!r}")

    complete_seen_after_incomplete = False
    incomplete = False
    for step in steps:
        status = step.get("status")
        if status not in STEP_STATUSES:
            errors.append(f"PREDISTRIBUTION_STEP_STATUS_INVALID: step {step.get('step')!r} carries {status!r}")
            continue
        if status != "COMPLETE":
            incomplete = True
        elif incomplete:
            complete_seen_after_incomplete = True
    if complete_seen_after_incomplete:
        errors.append(
            "PREDISTRIBUTION_STEP_OUT_OF_ORDER: a later step is COMPLETE while an earlier one is not — "
            "闸的意义就在于顺序"
        )

    # 第 2 步是 Founder 的步。它是否完成，看现场证据，不看本仓写的 status。
    step_two = next((s for s in steps if s.get("step") == 2), {})
    founder_evidence = payload.get("founder_step_evidence") or {}
    evidence_present = bool(founder_evidence.get("anchor_confirmation_bound")) and bool(
        founder_evidence.get("store_a_evidence_file_count")
    )
    if step_two.get("status") == "COMPLETE" and not evidence_present:
        errors.append(
            "EXECUTION_SIDE_PERFORMED_FOUNDER_STEP: step 2 is marked COMPLETE, but the anchor truth carries "
            f"founder_confirmation.confirmed={founder_evidence.get('anchor_confirmation_bound')!r} and the "
            f"STORE-A intake directory holds {founder_evidence.get('store_a_evidence_file_count')!r} files"
        )

    step_three_complete = next((s for s in steps if s.get("step") == 3), {}).get("status") == "COMPLETE"
    gate = payload.get("guardian_gate") or {}
    if gate.get("current_value") is not False and not step_three_complete:
        errors.append(
            "GUARDIAN_UNBLOCK_CLAIMED_BEFORE_PRECONDITION: guardian_review_allowed is "
            f"{gate.get('current_value')!r} while step 3 has not produced the final pre-distribution candidate — "
            "解除禁令不等于现在可以发起，被审对象还不存在"
        )
    if gate.get("lift_precondition") is None:
        errors.append("GUARDIAN_UNBLOCK_CLAIMED_BEFORE_PRECONDITION: the lift records no precondition at all")

    dispatch = payload.get("distribution_gate") or {}
    completed = sum(1 for s in steps if s.get("status") == "COMPLETE")
    if dispatch.get("steps_complete") != completed:
        errors.append(
            f"SEQUENCE_STEP_COUNT_MISSTATED: the gate declares {dispatch.get('steps_complete')!r} completed steps, "
            f"the step list holds {completed}"
        )
    if dispatch.get("current_value") is not False and completed < EXPECTED_STEPS - 1:
        errors.append(
            f"CALIBRATION_PACK_DISPATCHED_BEFORE_SEQUENCE_COMPLETE: distribution is allowed with {completed} "
            f"of {EXPECTED_STEPS} steps complete"
        )
    if payload.get("review_records_present") and completed < EXPECTED_STEPS - 1:
        errors.append(
            f"CALIBRATION_PACK_DISPATCHED_BEFORE_SEQUENCE_COMPLETE: {payload['review_records_present']} review "
            f"records already exist while only {completed} of {EXPECTED_STEPS} steps are complete — "
            "记录存在意味着包已经发出去了"
        )


def _validate_worksheet_contract(payload: dict, errors: list[str]) -> None:
    contract = payload.get("worksheet_contract") or {}
    fields = contract.get("required_per_item_fields") or []
    if len(fields) != WORKSHEET_FIELDS:
        errors.append(
            f"WORKSHEET_ITEM_FIELD_MISSING: the contract requires {len(fields)} per-item fields, "
            f"the ruling names {WORKSHEET_FIELDS}"
        )
    options = next((f for f in fields if f.get("id") == "three_options"), {})
    if options.get("option_count") != WORKSHEET_OPTIONS:
        errors.append(
            f"WORKSHEET_OPTION_COUNT_INVALID: three_options declares {options.get('option_count')!r} options"
        )

    declared_metrics = (contract.get("coverage_rule") or {}).get("metric_count")
    if declared_metrics != payload.get("mapping_metric_count"):
        errors.append(
            f"WORKSHEET_METRIC_MISSING: the contract declares {declared_metrics!r} metrics, "
            f"the metric mapping holds {payload.get('mapping_metric_count')!r}"
        )

    handling = contract.get("empirical_cutpoint_handling") or {}
    if sorted(handling.get("metrics") or []) != sorted(payload.get("empirical_metrics") or []):
        errors.append(
            f"WORKSHEET_EMPIRICAL_DISPOSITION_SELF_CHOSEN: the contract names empirical metrics "
            f"{sorted(handling.get('metrics') or [])}, the mapping types "
            f"{sorted(payload.get('empirical_metrics') or [])} as EMPIRICAL_CUTPOINT"
        )
    if handling.get("count") != len(payload.get("empirical_metrics") or []):
        errors.append(
            f"WORKSHEET_EMPIRICAL_DISPOSITION_SELF_CHOSEN: the contract counts {handling.get('count')!r} "
            f"empirical cutpoints, the mapping holds {len(payload.get('empirical_metrics') or [])}"
        )
    if handling.get("execution_side_must_not_choose") is not True:
        errors.append(
            "WORKSHEET_EMPIRICAL_DISPOSITION_SELF_CHOSEN: the contract does not forbid the execution side "
            "from choosing the disposition — 那两个选项的差别是这条线要不要靠数据定"
        )
    if len(handling.get("disposition_options") or []) != 2:
        errors.append(
            f"WORKSHEET_OPTION_COUNT_INVALID: the ruling gives 2 disposition options, the contract lists "
            f"{len(handling.get('disposition_options') or [])}"
        )

    if payload.get("worksheet_exists") and not payload.get("review_records_present"):
        errors.append(
            "WORKSHEET_DISAGREEMENT_FABRICATED: the worksheet exists while both review sinks hold 0 records — "
            "分歧分布只能从回收的记录里算，没有记录就算不出来"
        )
    if payload.get("review_records_present") and not payload.get("worksheet_exists"):
        errors.append(
            "WORKSHEET_NOT_PRODUCED_AT_AGGREGATION: review records exist but the worksheet is absent — "
            "裁决第四节要求聚合完成时同时产出"
        )


def _validate_worksheet_items(payload: dict, errors: list[str]) -> None:
    """工作表到期才存在。它一存在，就按合同逐项验——不靠人记得回来补一道判据。"""
    items = payload.get("worksheet_items") or []
    if not items:
        return
    required = [f["id"] for f in (payload.get("worksheet_contract") or {}).get("required_per_item_fields") or []]
    empirical = set(payload.get("empirical_metrics") or [])
    seen: dict[str, int] = {}
    for item in items:
        metric = item.get("metric_id")
        seen[metric] = seen.get(metric, 0) + 1
        for field in required:
            value = item.get(field)
            if value is None or (isinstance(value, str) and not value.strip()):
                errors.append(f"WORKSHEET_ITEM_FIELD_MISSING: {metric!r} carries no {field}")
        options = item.get("three_options")
        if isinstance(options, list) and len(options) != WORKSHEET_OPTIONS:
            errors.append(
                f"WORKSHEET_OPTION_COUNT_INVALID: {metric!r} offers {len(options)} option(s), must be {WORKSHEET_OPTIONS}"
            )
        if metric in empirical and item.get("disposition_decided_by") != "FOUNDER_PRODUCT_AUTHORITY":
            errors.append(
                f"WORKSHEET_EMPIRICAL_DISPOSITION_SELF_CHOSEN: {metric!r} records disposition_decided_by="
                f"{item.get('disposition_decided_by')!r} — 延后还是改判为政策阈值，是 Founder 在 TG-04 的裁决"
            )
    for metric, count in sorted(seen.items()):
        if count > 1:
            errors.append(f"WORKSHEET_METRIC_DUPLICATE: {metric!r} appears {count}× in the worksheet")
    expected = payload.get("mapping_metric_count")
    if len(seen) != expected:
        errors.append(
            f"WORKSHEET_METRIC_MISSING: the worksheet covers {len(seen)} metric(s), the mapping holds {expected!r}"
        )


def _validate_ruling_landing(payload: dict, errors: list[str]) -> None:
    declared = payload.get("ruling_fields") or {}
    actual = {
        "sequence_step_count": len(payload.get("steps") or []),
        "worksheet_per_item_field_count": len((payload.get("worksheet_contract") or {}).get("required_per_item_fields") or []),
        "empirical_cutpoint_count": len(payload.get("empirical_metrics") or []),
        "guardian_review_allowed_now": (payload.get("guardian_gate") or {}).get("current_value"),
        "calibration_pack_distribution_allowed": (payload.get("distribution_gate") or {}).get("current_value"),
    }
    for field, value in actual.items():
        if declared.get(field) != value:
            errors.append(
                f"RULING_FIELD_NOT_LANDED: the ruling declares {field}={declared.get(field)!r}, "
                f"the repository holds {value!r}"
            )

    entry = payload.get("backreported_commit") or {}
    commit = entry.get("candidate_commit")
    if not isinstance(commit, str) or len(commit) != FULL_HASH_LENGTH or not all(
        c in "0123456789abcdef" for c in commit
    ):
        errors.append(
            f"PACKAGE_COMMIT_NOT_FULL_HASH: the back-reported commit is {commit!r}, "
            f"a full {FULL_HASH_LENGTH}-hex-digit hash is required"
        )
    if entry.get("is_the_backreported_commit") is not True:
        errors.append(
            "BACKREPORTED_COMMIT_NOT_MARKED: no ledger entry marks itself as the commit EP06 asked to be back-reported"
        )
    for row in payload.get("ledger_entries") or []:
        value = row.get("candidate_commit")
        if row.get("status") == "CURRENT_CANDIDATE":
            continue
        if not isinstance(value, str) or len(value) != FULL_HASH_LENGTH:
            errors.append(
                f"PACKAGE_COMMIT_NOT_FULL_HASH: ledger entry {row.get('execution_package')!r} records {value!r}"
            )


def validate(payload: dict) -> list[str]:
    errors: list[str] = []
    _validate_queue(payload, errors)
    _validate_sequence(payload, errors)
    _validate_worksheet_contract(payload, errors)
    _validate_worksheet_items(payload, errors)
    _validate_ruling_landing(payload, errors)
    return errors


def _queue_focus_rows(text: str) -> tuple[list[str], dict[str, str]]:
    """从落盘队列里取出主表的锚点判定与子表列出的行——读文本，不读生成器的内部状态。"""
    focus: list[str] = []
    calls: dict[str, str] = {}
    section = None
    for line in text.splitlines():
        if line.startswith("## "):
            section = line[3:].strip()
            continue
        if not line.startswith("| CAL-"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if section == "主表" and len(cells) >= 6:
            calls[cells[0]] = cells[5]
        elif section == "需重点确认":
            focus.append(cells[0])
    return focus, calls


def collect() -> dict:
    annotations_doc = load_yaml(ANNOTATIONS)
    sequence = load_yaml(SEQUENCE)
    worksheet = load_yaml(WORKSHEET_CONTRACT)
    mapping = load_yaml(MAPPING)
    ruling = load_yaml(RULING)
    ledger = load_yaml(COMMIT_LEDGER)

    builder = _builder()
    drift = []
    for rel, content in builder.build().items():
        path = ROOT / rel
        if not path.exists() or path.read_text(encoding="utf-8") != content:
            drift.append(rel)

    queue_text = read_text(QUEUE) if (ROOT / QUEUE).exists() else ""
    focus_rows, anchor_calls = _queue_focus_rows(queue_text)

    pack_leaks = []
    pack_root = ROOT / PACK
    if pack_root.exists():
        for path in sorted(pack_root.rglob("*")):
            if not path.is_file() or path.name in PACK_SCAN_EXCLUDED:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            for token in QUEUE_LEAK_TOKENS:
                if token in text:
                    pack_leaks.append({"file": path.relative_to(ROOT).as_posix(), "token": token})

    anchor_truth = load_yaml(ANCHOR_TRUTH)
    confirmation = anchor_truth["founder_confirmation"]
    intake_dir = ROOT / (load_yaml(TIMING_GATE)["store_a_evidence"]["intake_directory"])
    intake_files = [p for p in intake_dir.glob("*.yaml")] if intake_dir.exists() else []

    review_state = load_yaml(REVIEW_STATE)
    records = 0
    for side in review_state["sides"]:
        sink = ROOT / side["sink"]
        if sink.exists():
            records += sum(1 for line in sink.read_text(encoding="utf-8").splitlines() if line.strip())

    empirical = [i["metric_id"] for i in mapping["items"] if i["evidence_kind"] == "EMPIRICAL_CUTPOINT"]
    worksheet_path = ROOT / worksheet["worksheet_path_when_due"]
    backreported = next((e for e in ledger["entries"] if e.get("is_the_backreported_commit")), {})

    return {
        "cases": load_yaml(CAL)["cases"],
        "anchors": anchor_truth["anchors"],
        "annotations": annotations_doc["annotations"],
        "shared_question_affects": annotations_doc["shared_questions"]["items"],
        "queue_derivation_drift": drift,
        "queue_focus_rows": focus_rows,
        "queue_anchor_calls": anchor_calls,
        "queue_pack_leaks": pack_leaks,
        "steps": sequence["steps"],
        "guardian_gate": sequence["guardian_review_allowed"],
        "distribution_gate": sequence["calibration_pack_distribution_allowed"],
        "founder_step_evidence": {
            "anchor_confirmation_bound": bool(confirmation.get("confirmed")),
            "store_a_evidence_file_count": len(intake_files),
        },
        "review_records_present": records,
        "worksheet_contract": worksheet,
        "worksheet_exists": worksheet_path.exists(),
        "worksheet_items": load_yaml(worksheet["worksheet_path_when_due"])["items"] if worksheet_path.exists() else [],
        "mapping_metric_count": len(mapping["items"]),
        "empirical_metrics": empirical,
        "ruling_fields": ruling["machine_checkable_fields"],
        "ledger_entries": ledger["entries"],
        "backreported_commit": backreported,
    }


if __name__ == "__main__":
    cli(LABEL, collect, validate)
