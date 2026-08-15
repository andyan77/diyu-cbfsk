#!/usr/bin/env python3
"""隔离评审证据、记录合法性与阈值冻结：没有评审就必须说没有，有评审就必须说得清是谁在哪判的。

本判据守三件事：

  证据在不在、两侧是不是真分开
      主执行侧自己扮演两个「隔离评审员」，产出两份看起来独立的结果再算分歧率——
      这是本任务的绝对禁止项。状态与证据必须互相印证；两侧工作区不得相同；
      Prompt 哈希现算，改了 Prompt 不改哈希，记录就绑不到它实际读过的那一份。

  记录本身是不是合法（EP05-CORRECTION C-3）
      此前只查九个字段在不在，于是重复 case_id、越界分数、多给一个硬门键、
      异议不写理由，全都能过。这里逐条现算：每侧恰好 90 个唯一 case、CAL-001—090 全覆盖、
      score 数值且在区间内、约束题只许 0/1 且与 judgment 绑定、
      hard_gate_result 的键与该例 hard_gate_refs 精确相等、三种情形下 review_note 必须非空。

  阈值一侧
      执行侧不得代 Founder 冻结任何阈值，也不得给出没有证据来源的建议值。
      并且（C-4）每条指标必须声明证据类型：POLICY_THRESHOLD 是产品裁决，不得装成统计估计；
      EMPIRICAL_CUTPOINT 必须有 estimator、样本下限与映射到的评审单元，且输入不齐时不许出建议值。
"""

from __future__ import annotations

import json
from numbers import Real
from zipfile import ZipFile
from xml.etree import ElementTree

from _common import ROOT, W_NS, cli, is_full_commit_hash, load_yaml, sha256_file

LABEL = "check_m2_calibration_review"

STATE = "03_m2_evaluation_foundation/calibration/calibration_review_state.v0.1.yaml"
THRESHOLD = "03_m2_evaluation_foundation/calibration/threshold_freeze_decision.v0.1.yaml"
AGGREGATION = "03_m2_evaluation_foundation/calibration/calibration_aggregation.v0.1.yaml"
CAL = "03_m2_evaluation_foundation/calibration/public_calibration_set.v0.1.yaml"
MAPPING = "03_m2_evaluation_foundation/calibration/metric_review_unit_mapping.v0.1.yaml"
PRD = "笛语跨品牌服装搭配专家内核_PRD与执行里程碑_v1.2.docx"

EVIDENCE_MISSING = "CALIBRATION_REVIEW_EVIDENCE_MISSING"
CONSTRAINT_CLASS = "constraint_correctness"
EVIDENCE_KINDS = ("POLICY_THRESHOLD", "EMPIRICAL_CUTPOINT")


def _prd_metrics() -> dict[str, str]:
    root = ElementTree.fromstring(ZipFile(ROOT / PRD).read("word/document.xml"))
    for tbl in root.iter(f"{W_NS}tbl"):
        rows = []
        for tr in tbl.iter(f"{W_NS}tr"):
            rows.append(
                ["".join(n.text or "" for n in tc.iter(f"{W_NS}t")).strip() for tc in tr.iter(f"{W_NS}tc")]
            )
        if rows and rows[0][:3] == ["指标", "建议阈值", "说明"]:
            return {r[0]: r[1] for r in rows[1:]}
    raise ValueError("PRD 10.2 metric table not found")


def _validate_record(record: dict, sid: str, ctx: dict, errors: list[str]) -> None:
    rid = record.get("case_id", "<no case_id>")
    for field in ctx["required_fields"]:
        if field not in record:
            errors.append(f"REVIEW_RECORD_SCHEMA_VIOLATION: {sid}/{rid} missing {field}")
    if record.get("reviewer_role") != ctx["reviewer_role"]:
        errors.append(
            f"CALIBRATION_REVIEW_CROSS_CONTAMINATED: {sid}/{rid} carries reviewer_role "
            f"{record.get('reviewer_role')!r}"
        )
    if record.get("review_prompt_hash") != ctx["prompt_sha256"]:
        errors.append(f"REVIEW_RECORD_SCHEMA_VIOLATION: {sid}/{rid} review_prompt_hash does not match the prompt")

    case = ctx["cases"].get(record.get("case_id"))
    if case is None:
        errors.append(f"REVIEW_RECORD_SCHEMA_VIOLATION: {sid}/{rid} is not a case in the calibration set")
        return
    if not case.get("has_candidate_output"):
        errors.append(f"REVIEW_UNIT_WITHOUT_CANDIDATE: {sid}/{rid} reviews a unit that carries no candidate_output")
    if record.get("candidate_id") != case.get("candidate_id"):
        errors.append(
            f"REVIEW_RECORD_SCHEMA_VIOLATION: {sid}/{rid} carries candidate_id {record.get('candidate_id')!r}, "
            f"the unit holds {case.get('candidate_id')!r}"
        )

    judgment = record.get("judgment")
    if judgment not in ctx["judgments"]:
        errors.append(f"REVIEW_RECORD_JUDGMENT_INVALID: {sid}/{rid} carries judgment {judgment!r}")

    score = record.get("score")
    if not isinstance(score, Real) or isinstance(score, bool):
        errors.append(f"REVIEW_RECORD_SCORE_OUT_OF_RANGE: {sid}/{rid} carries a non-numeric score {score!r}")
    elif not 0.0 <= float(score) <= 1.0:
        errors.append(f"REVIEW_RECORD_SCORE_OUT_OF_RANGE: {sid}/{rid} scores {score!r}, must be within 0.0—1.0")
    elif case.get("evaluation_task_class") == CONSTRAINT_CLASS:
        if float(score) not in (0.0, 1.0):
            errors.append(
                f"REVIEW_RECORD_CONSTRAINT_SCORE_INVALID: {sid}/{rid} is a hard-constraint unit scored {score!r}"
            )
        expected = ctx["constraint_binding"].get(judgment)
        if expected is not None and float(score) != float(expected):
            errors.append(
                f"JUDGMENT_SCORE_INCONSISTENT: {sid}/{rid} judges {judgment} but scores {score!r}, "
                f"the binding requires {expected!r}"
            )

    gates = record.get("hard_gate_result")
    if not isinstance(gates, dict):
        errors.append(f"REVIEW_RECORD_HARD_GATE_KEYS_MISMATCH: {sid}/{rid} carries hard_gate_result {gates!r}")
        gates = {}
    else:
        expected_keys = set(case.get("hard_gate_refs") or ())
        if set(gates) != expected_keys:
            errors.append(
                f"REVIEW_RECORD_HARD_GATE_KEYS_MISMATCH: {sid}/{rid} judges {sorted(gates)!r}, "
                f"the unit references {sorted(expected_keys)!r}"
            )
        for key, value in gates.items():
            if value not in ctx["gate_values"]:
                errors.append(f"REVIEW_RECORD_HARD_GATE_VALUE_INVALID: {sid}/{rid} gives {key}={value!r}")

    code = record.get("disagreement_code")
    if code is not None and code not in ctx["codes"]:
        errors.append(f"REVIEW_RECORD_DISAGREEMENT_CODE_INVALID: {sid}/{rid} carries {code!r}")

    note_required = (
        code is not None
        or judgment == "AMBIGUOUS"
        or any(v in ("FAIL", "NOT_APPLICABLE") for v in gates.values())
    )
    if note_required and not (record.get("review_note") or "").strip():
        errors.append(
            f"REVIEW_NOTE_REQUIRED_BUT_EMPTY: {sid}/{rid} needs a review_note "
            "(disagreement code, AMBIGUOUS judgment, or a FAIL/NOT_APPLICABLE hard gate)"
        )


def _validate_sides(payload: dict, errors: list[str]) -> int:
    total = 0
    workspaces: list[str] = []
    cases = {c["case_id"]: c for c in payload.get("cases") or []}
    expected_per_side = payload.get("expected_records_per_side")

    for side in payload.get("sides") or []:
        sid = side.get("side_id", "<no id>")
        declared = side.get("declared_record_count")
        actual = side.get("actual_record_count")
        if declared != actual:
            errors.append(
                f"CALIBRATION_REVIEW_STATE_CONTRADICTS_EVIDENCE: {sid} declares {declared!r} records, "
                f"its sink holds {actual!r}"
            )
        if side.get("executed") is not (actual > 0):
            errors.append(
                f"CALIBRATION_REVIEW_STATE_CONTRADICTS_EVIDENCE: {sid} executed={side.get('executed')!r} "
                f"with {actual} record(s)"
            )
        if side.get("produced_by_main_execution_side") is True:
            errors.append(f"CALIBRATION_REVIEW_SELF_PLAYED: {sid} is flagged as produced by the main execution side")
        if side.get("produced_by_workspace"):
            workspaces.append(side["produced_by_workspace"])
        total += actual

        records = side.get("records") or []
        if records and not (side.get("produced_by_workspace") or "").strip():
            errors.append(f"REVIEW_SIDE_WORKSPACE_MISSING: {sid} holds {len(records)} record(s) with no workspace")

        if records:
            if len(records) != expected_per_side:
                errors.append(
                    f"REVIEW_RECORD_CASE_COVERAGE_BROKEN: {sid} holds {len(records)} record(s), "
                    f"the contract expects exactly {expected_per_side!r}"
                )
            seen: set[str] = set()
            for record in records:
                cid = record.get("case_id")
                if cid in seen:
                    errors.append(f"REVIEW_RECORD_DUPLICATE_CASE: {sid} judges {cid} more than once")
                seen.add(cid)
            for cid in sorted(cases):
                if cid not in seen:
                    errors.append(f"REVIEW_RECORD_CASE_COVERAGE_BROKEN: {sid} never judges {cid}")
            for field in ("model", "model_version"):
                values = {record.get(field) for record in records}
                if len(values) > 1:
                    errors.append(
                        f"REVIEW_SIDE_MODEL_INCONSISTENT: {sid} mixes {field} values {sorted(map(repr, values))}"
                    )

        ctx = {
            "cases": cases,
            "reviewer_role": side.get("reviewer_role"),
            "prompt_sha256": payload.get("actual_prompt_sha256"),
            "required_fields": payload.get("required_record_fields") or (),
            "judgments": set(payload.get("allowed_judgments") or ()),
            "gate_values": set(payload.get("allowed_hard_gate_values") or ()),
            "codes": set(payload.get("allowed_disagreement_codes") or ()),
            "constraint_binding": payload.get("constraint_judgment_score_binding") or {},
        }
        for record in records:
            _validate_record(record, sid, ctx, errors)

    if len(workspaces) > 1 and len(set(workspaces)) != len(workspaces):
        errors.append("CALIBRATION_REVIEW_NOT_ISOLATED: two sides record the same produced_by_workspace")
    return total


def _validate_aggregation(payload: dict, total: int, errors: list[str]) -> None:
    if payload.get("aggregation_computed") and total == 0:
        errors.append("AGGREGATION_CLAIMED_WITHOUT_RECORDS: aggregation is marked computed with zero records")
    if payload.get("aggregation_execution_side_adjudicated") is not False:
        errors.append("EXECUTION_SIDE_FROZE_THRESHOLD: aggregation claims the execution side adjudicated")
    computed_from = payload.get("aggregation_conflict_computed_from")
    if computed_from != "judgment":
        errors.append(
            f"SCORE_USED_AS_JUDGMENT: the aggregation contract computes conflicts from {computed_from!r}; "
            "成立与否只能直接比较 judgment，不经任何分数换算"
        )
    if payload.get("aggregation_unfrozen_threshold_used") is not False:
        errors.append(
            "UNFROZEN_THRESHOLD_USED_IN_AGGREGATION: aggregation admits converting score into a verdict "
            "with a threshold this round has not frozen"
        )

    declared = payload.get("aggregation_declared_statistics") or {}
    recomputed = payload.get("aggregation_recomputed_statistics") or {}
    for field in sorted(set(declared) | set(recomputed)):
        if declared.get(field) != recomputed.get(field):
            errors.append(
                f"AGGREGATION_NOT_RECOMPUTED_FROM_RECORDS: {field} is declared {declared.get(field)!r}, "
                f"recomputing from the raw records gives {recomputed.get(field)!r}"
            )


def _validate_evidence_typing(payload: dict, errors: list[str]) -> None:
    mapping = payload.get("metric_mapping") or []
    declared_ids = [i.get("metric") for i in payload.get("threshold_items") or []]
    mapped_ids = [m.get("metric_id") for m in mapping]

    for metric in declared_ids:
        if metric not in mapped_ids:
            errors.append(f"METRIC_MAPPING_MISSING: {metric!r} has no evidence-kind mapping")
    for metric in mapped_ids:
        if metric not in declared_ids:
            errors.append(f"METRIC_MAPPING_UNKNOWN: mapping lists {metric!r}, the decision file has no such metric")
        if mapped_ids.count(metric) > 1:
            errors.append(f"METRIC_MAPPING_DUPLICATE: {metric!r} is mapped more than once")

    recommendations = {i.get("metric"): i.get("threshold_recommendation") for i in payload.get("threshold_items") or []}
    for entry in mapping:
        metric = entry.get("metric_id", "<no metric>")
        kind = entry.get("evidence_kind")
        if kind not in EVIDENCE_KINDS:
            errors.append(f"EVIDENCE_KIND_INVALID: {metric} declares evidence_kind {kind!r}")
            continue
        if kind == "EMPIRICAL_CUTPOINT":
            if not (entry.get("estimator") or "").strip():
                errors.append(f"EMPIRICAL_CUTPOINT_WITHOUT_ESTIMATOR: {metric} names no estimator")
            if not isinstance(entry.get("minimum_sample_count"), int):
                errors.append(f"EMPIRICAL_CUTPOINT_WITHOUT_SAMPLE_FLOOR: {metric} names no minimum_sample_count")
            if entry.get("recomputed_by_checker_from_raw_records") is not True:
                errors.append(f"EMPIRICAL_CUTPOINT_WITHOUT_ESTIMATOR: {metric} is not recomputed from raw records")
            if entry.get("estimator_inputs_available") is not True:
                if not entry.get("blocked_by"):
                    errors.append(
                        f"EMPIRICAL_CUTPOINT_WITHOUT_REVIEW_UNITS: {metric} has no inputs and names no blocker"
                    )
                if recommendations.get(metric) is not None:
                    errors.append(
                        f"RECOMMENDATION_WITHOUT_AVAILABLE_INPUTS: {metric} gives a recommendation while its "
                        "estimator inputs do not exist"
                    )
            for field in ("false_acceptance_policy", "false_rejection_policy"):
                if not (entry.get(field) or "").strip():
                    errors.append(f"EMPIRICAL_CUTPOINT_WITHOUT_ESTIMATOR: {metric} has no {field}")
        else:
            if entry.get("estimator") is not None:
                errors.append(
                    f"POLICY_THRESHOLD_DISGUISED_AS_ESTIMATE: {metric} is a product ruling yet names an estimator"
                )
            if entry.get("recomputed_by_checker_from_raw_records") is not False:
                errors.append(
                    f"POLICY_THRESHOLD_DISGUISED_AS_ESTIMATE: {metric} claims to be recomputed from raw records"
                )

    declared_counts = payload.get("mapping_counts") or {}
    actual_counts = {
        "metrics": len(mapping),
        "policy_threshold": sum(1 for m in mapping if m.get("evidence_kind") == "POLICY_THRESHOLD"),
        "empirical_cutpoint": sum(1 for m in mapping if m.get("evidence_kind") == "EMPIRICAL_CUTPOINT"),
        "empirical_with_inputs_available": sum(
            1
            for m in mapping
            if m.get("evidence_kind") == "EMPIRICAL_CUTPOINT" and m.get("estimator_inputs_available") is True
        ),
    }
    for field, value in actual_counts.items():
        if declared_counts.get(field) != value:
            errors.append(
                f"MAPPING_COUNT_MISSTATED: mapping declares {field}={declared_counts.get(field)!r}, holds {value}"
            )


def _validate_thresholds(payload: dict, errors: list[str]) -> None:
    prd = payload.get("prd_metrics") or {}
    items = payload.get("threshold_items") or []

    declared_ids = [i.get("metric") for i in items]
    for metric in prd:
        if metric not in declared_ids:
            errors.append(f"THRESHOLD_METRIC_MISSING: PRD 10.2 lists {metric!r}, the decision file omits it")
    for metric in declared_ids:
        if metric not in prd:
            errors.append(f"THRESHOLD_METRIC_UNKNOWN: decision file lists {metric!r}, PRD 10.2 has no such metric")

    for item in items:
        metric = item.get("metric", "<no metric>")
        decision = item.get("founder_decision")
        if decision is not None and not is_full_commit_hash(item.get("founder_decision_commit")):
            errors.append(
                f"EXECUTION_SIDE_FROZE_THRESHOLD: {metric} carries a founder_decision without a 40-hex founder commit"
            )
        if item.get("threshold_recommendation") is not None and not item.get("evidence_source"):
            errors.append(f"RECOMMENDATION_WITHOUT_EVIDENCE: {metric} gives a recommendation with no evidence_source")
        if item.get("threshold_recommendation") is None and item.get("blocked_by") is None:
            errors.append(f"RECOMMENDATION_WITHOUT_EVIDENCE: {metric} has no recommendation and names no blocker")
        if metric == "high_risk_founder_full_review_rate":
            if item.get("threshold_recommendation") != prd.get(metric):
                errors.append(
                    f"HIGH_RISK_THRESHOLD_LOWERED: {metric} recommends {item.get('threshold_recommendation')!r}, "
                    f"PRD fixes it at {prd.get(metric)!r}"
                )
            if item.get("threshold_kind") != "NOT_ADJUSTABLE":
                errors.append(f"HIGH_RISK_THRESHOLD_LOWERED: {metric} is marked {item.get('threshold_kind')!r}")

    if payload.get("declared_metric_count") != len(items):
        errors.append(
            f"THRESHOLD_METRIC_MISSING: decision file declares {payload.get('declared_metric_count')!r} metrics, "
            f"lists {len(items)}"
        )
    if payload.get("hidden_set_tuning_forbidden") is not True:
        errors.append("HIDDEN_SET_USED_FOR_TUNING: the decision file does not forbid tuning on the hidden set")


def validate(payload: dict) -> list[str]:
    errors: list[str] = []

    if payload.get("declared_prompt_sha256") != payload.get("actual_prompt_sha256"):
        errors.append(
            f"PROMPT_HASH_STALE: state records {payload.get('declared_prompt_sha256')!r}, "
            f"the prompt hashes to {payload.get('actual_prompt_sha256')!r}"
        )

    total = _validate_sides(payload, errors)
    failure_state = payload.get("failure_state")

    if failure_state == EVIDENCE_MISSING and total != 0:
        errors.append(
            f"CALIBRATION_REVIEW_STATE_CONTRADICTS_EVIDENCE: state is {EVIDENCE_MISSING} with {total} record(s)"
        )
    if failure_state is None and total == 0:
        errors.append(
            f"CALIBRATION_REVIEW_STATE_CONTRADICTS_EVIDENCE: failure state cleared with zero review records"
        )

    _validate_aggregation(payload, total, errors)
    _validate_thresholds(payload, errors)
    _validate_evidence_typing(payload, errors)
    return errors


def _read_jsonl(rel: str) -> list[dict]:
    path = ROOT / rel
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            out.append(json.loads(line))
    return out


def _recompute_statistics(sides: list[dict]) -> dict:
    """由两侧原始记录现算分歧统计。台账自述值只用来比对，不参与计算。"""
    by_case: dict[str, dict[str, dict]] = {}
    for side in sides:
        for record in side["records"]:
            by_case.setdefault(record.get("case_id"), {})[side["side_id"]] = record
    both = {cid: rec for cid, rec in by_case.items() if len(rec) == 2}
    if not both:
        return {
            "total_cases_both_sided": 0,
            "verdict_conflict_count": None,
            "verdict_conflict_rate": None,
            "legitimate_disagreement_count": None,
            "hard_gate_conflict_count": None,
        }
    conflicts = 0
    legitimate = 0
    gate_conflicts = 0
    for rec in both.values():
        left, right = rec.values()
        judgments = {left.get("judgment"), right.get("judgment")}
        if judgments == {"ACCEPT", "REJECT"}:
            conflicts += 1
        elif judgments == {"ACCEPT"} and left.get("score") != right.get("score"):
            legitimate += 1
        lg, rg = left.get("hard_gate_result") or {}, right.get("hard_gate_result") or {}
        if any(lg.get(k) != rg.get(k) for k in set(lg) | set(rg)):
            gate_conflicts += 1
    return {
        "total_cases_both_sided": len(both),
        "verdict_conflict_count": conflicts,
        "verdict_conflict_rate": round(conflicts / len(both), 4),
        "legitimate_disagreement_count": legitimate,
        "hard_gate_conflict_count": gate_conflicts,
    }


def collect() -> dict:
    state = load_yaml(STATE)
    threshold = load_yaml(THRESHOLD)
    aggregation = load_yaml(AGGREGATION)
    cal = load_yaml(CAL)
    mapping = load_yaml(MAPPING)

    sides = []
    for side in state["sides"]:
        records = _read_jsonl(side["sink"])
        sides.append(
            {
                "side_id": side.get("side_id"),
                "reviewer_role": side.get("reviewer_role"),
                "declared_record_count": side.get("record_count"),
                "actual_record_count": len(records),
                "executed": side.get("executed"),
                "produced_by_workspace": side.get("produced_by_workspace"),
                "produced_by_main_execution_side": side.get("produced_by_main_execution_side"),
                "records": records,
            }
        )

    schema = state["record_schema"]
    fields = aggregation["disagreement_statistics"]["fields_when_computed"]
    declared_statistics = {
        name: spec.get("current_value")
        for name, spec in fields.items()
        if name in (
            "total_cases_both_sided",
            "verdict_conflict_count",
            "verdict_conflict_rate",
            "legitimate_disagreement_count",
            "hard_gate_conflict_count",
        )
    }

    cases = [
        {
            "case_id": c["case_id"],
            "evaluation_task_class": c["evaluation_task_class"],
            "hard_gate_refs": c.get("hard_gate_refs") or [],
            "candidate_id": (c.get("candidate") or {}).get("candidate_id"),
            "has_candidate_output": bool(((c.get("candidate") or {}).get("candidate_output") or "").strip()),
        }
        for c in cal["cases"]
    ]

    prompt_rel = state["prompt"]["path"]
    return {
        "failure_state": state.get("failure_state"),
        "declared_prompt_sha256": state["prompt"]["sha256"],
        "actual_prompt_sha256": sha256_file(ROOT / prompt_rel),
        "sides": sides,
        "cases": cases,
        "expected_records_per_side": state["machine_checkable_fields"]["expected_records_per_side"]["required_value"],
        "required_record_fields": schema["required_fields"],
        "allowed_judgments": schema["allowed_judgments"],
        "allowed_hard_gate_values": schema["allowed_hard_gate_values"],
        "allowed_disagreement_codes": schema["allowed_disagreement_codes"],
        "constraint_judgment_score_binding": schema["constraint_judgment_score_binding"],
        "aggregation_computed": (aggregation.get("disagreement_statistics") or {}).get("computed"),
        "aggregation_execution_side_adjudicated": aggregation["machine_checkable_fields"][
            "execution_side_adjudicated"
        ]["required_value"],
        "aggregation_unfrozen_threshold_used": aggregation["machine_checkable_fields"][
            "unfrozen_threshold_used"
        ]["required_value"],
        "aggregation_conflict_computed_from": aggregation["disagreement_statistics"]["conflict_definition"][
            "computed_from"
        ],
        "aggregation_declared_statistics": declared_statistics,
        "aggregation_recomputed_statistics": _recompute_statistics(sides),
        "prd_metrics": _prd_metrics(),
        "threshold_items": threshold["items"],
        "declared_metric_count": threshold["metric_count"],
        "hidden_set_tuning_forbidden": threshold["hidden_set_tuning_forbidden"]["forbidden"],
        "metric_mapping": mapping["items"],
        "mapping_counts": mapping["counts"],
    }


if __name__ == "__main__":
    cli(LABEL, collect, validate)
