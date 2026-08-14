#!/usr/bin/env python3
"""隔离评审证据与阈值冻结：没有评审就必须说没有，有评审就必须说得清是谁在哪判的。

本判据存在的唯一理由是防一件事：主执行侧自己扮演两个「隔离评审员」，产出两份看起来独立的
结果，再拿它们算分歧率。因此这里守的不是分数好不好，是证据在不在、两侧是不是真的分开：
  * 状态与证据必须互相印证——声称缺证据就必须真的 0 条，有记录就不许还挂着缺证据态。
  * 两侧工作区不得相同；任一侧标记为主执行侧产出即判失败。
  * Prompt 哈希现算——改了 Prompt 不改哈希，评审记录就绑不到它实际读过的那份。
阈值一侧守的是另一件事：执行侧不得代 Founder 冻结任何阈值，也不得给出没有证据来源的建议值。
"""

from __future__ import annotations

import json
from zipfile import ZipFile
from xml.etree import ElementTree

from _common import ROOT, W_NS, cli, is_full_commit_hash, load_yaml, sha256_file

LABEL = "check_m2_calibration_review"

STATE = "03_m2_evaluation_foundation/calibration/calibration_review_state.v0.1.yaml"
THRESHOLD = "03_m2_evaluation_foundation/calibration/threshold_freeze_decision.v0.1.yaml"
AGGREGATION = "03_m2_evaluation_foundation/calibration/calibration_aggregation.v0.1.yaml"
CAL = "03_m2_evaluation_foundation/calibration/public_calibration_set.v0.1.yaml"
PRD = "笛语跨品牌服装搭配专家内核_PRD与执行里程碑_v1.2.docx"

EVIDENCE_MISSING = "CALIBRATION_REVIEW_EVIDENCE_MISSING"
REQUIRED_RECORD_FIELDS = (
    "case_id", "reviewer_role", "model", "model_version", "review_prompt_hash",
    "score", "hard_gate_result", "disagreement_code", "reviewed_at",
)


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


def _validate_sides(payload: dict, errors: list[str]) -> int:
    total = 0
    workspaces: list[str] = []
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

        for record in side.get("records") or []:
            rid = record.get("case_id", "<no case_id>")
            for field in REQUIRED_RECORD_FIELDS:
                if field not in record:
                    errors.append(f"REVIEW_RECORD_SCHEMA_VIOLATION: {sid}/{rid} missing {field}")
            if record.get("reviewer_role") != side.get("reviewer_role"):
                errors.append(
                    f"CALIBRATION_REVIEW_CROSS_CONTAMINATED: {sid}/{rid} carries reviewer_role "
                    f"{record.get('reviewer_role')!r}"
                )
            if record.get("review_prompt_hash") != payload.get("actual_prompt_sha256"):
                errors.append(f"REVIEW_RECORD_SCHEMA_VIOLATION: {sid}/{rid} review_prompt_hash does not match the prompt")
            if record.get("case_id") not in payload.get("known_case_ids", ()):
                errors.append(f"REVIEW_RECORD_SCHEMA_VIOLATION: {sid}/{rid} is not a case in the calibration set")

    if len(workspaces) > 1 and len(set(workspaces)) != len(workspaces):
        errors.append("CALIBRATION_REVIEW_NOT_ISOLATED: two sides record the same produced_by_workspace")
    return total


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

    if payload.get("aggregation_computed") and total == 0:
        errors.append("AGGREGATION_CLAIMED_WITHOUT_RECORDS: aggregation is marked computed with zero records")
    if payload.get("aggregation_execution_side_adjudicated") is not False:
        errors.append("EXECUTION_SIDE_FROZE_THRESHOLD: aggregation claims the execution side adjudicated")

    _validate_thresholds(payload, errors)
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


def collect() -> dict:
    state = load_yaml(STATE)
    threshold = load_yaml(THRESHOLD)
    aggregation = load_yaml(AGGREGATION)
    cases = load_yaml(CAL)["cases"]

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

    prompt_rel = state["prompt"]["path"]
    return {
        "failure_state": state.get("failure_state"),
        "declared_prompt_sha256": state["prompt"]["sha256"],
        "actual_prompt_sha256": sha256_file(ROOT / prompt_rel),
        "sides": sides,
        "known_case_ids": [c["case_id"] for c in cases],
        "aggregation_computed": (aggregation.get("disagreement_statistics") or {}).get("computed"),
        "aggregation_execution_side_adjudicated": aggregation["machine_checkable_fields"][
            "execution_side_adjudicated"
        ]["required_value"],
        "prd_metrics": _prd_metrics(),
        "threshold_items": threshold["items"],
        "declared_metric_count": threshold["metric_count"],
        "hidden_set_tuning_forbidden": threshold["hidden_set_tuning_forbidden"]["forbidden"],
    }


if __name__ == "__main__":
    cli(LABEL, collect, validate)
