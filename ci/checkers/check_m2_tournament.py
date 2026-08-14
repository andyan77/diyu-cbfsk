#!/usr/bin/env python3
"""基线锦标赛：四维度齐备、不合成总分、dry-run 确定性可重放、零真实模型调用。

四条纪律各自成判据：

  四维度并列   —— 质量／成本／延迟／人工干预缺一，比较结果就不成立。
                  人工干预最容易被省，省了会把「模型很好」和「有人在后面一直补」混为一谈。
  不合成总分   —— 权重就是取舍本身。Founder 冻结权重之前合成总分，
                  等于执行侧替 Founder 做了「质量换成本」的决定。
  确定性可重放 —— 连跑两次必须字节相同。聚合口径带抖动就没法比较两个方案，
                  因为分不清差异来自方案还是来自抖动。这里**实跑两次**比对，不看声明。
  零真实调用   —— 扫 runner 源码的 import，出现网络或模型供应商 SDK 即失败。

反自审绿：确定性不是读合同里的 replayable: true，是真的把 runner 跑两遍比字节；
硬门聚合口径也不是读合同，是从实跑结果里核「有一条 fail 的臂是否真的被判失败」。
"""

from __future__ import annotations

import importlib.util
import json
import re

from _common import ROOT, cli, load_yaml, sha256_text

LABEL = "check_m2_tournament"

CONTRACT = "03_m2_evaluation_foundation/tournament/baseline_tournament_contract.v0.1.yaml"
RUNNER = "03_m2_evaluation_foundation/tournament/run_tournament_dryrun.py"
FIXTURE_DIR = "ci/fixtures/m2/tournament"

REQUIRED_DIMENSIONS = ("quality", "cost", "latency", "human_intervention")

# 真实模型调用与网络访问的结构化痕迹。命中即说明本包越过了「禁止真实模型 API 调用」。
FORBIDDEN_RUNTIME_IMPORTS = (
    "requests", "httpx", "urllib.request", "urllib3", "socket", "http.client",
    "openai", "anthropic", "google.generativeai", "boto3", "aiohttp",
)
IMPORT_RE = re.compile(r"^\s*(?:import|from)\s+([A-Za-z0-9_.]+)", re.MULTILINE)


def validate(payload: dict) -> list[str]:
    errors: list[str] = []

    declared = payload.get("contract_dimensions") or []
    for dim in REQUIRED_DIMENSIONS:
        if dim not in declared:
            errors.append(
                f"TOURNAMENT_DIMENSION_MISSING: {dim} — 四维度缺一，比较结果不成立"
            )
    if payload.get("contract_dimension_count") != len(declared):
        errors.append(
            f"TOURNAMENT_DIMENSION_DRIFT: contract declares {payload.get('contract_dimension_count')!r} "
            f"but lists {len(declared)}"
        )
    if payload.get("all_required") is not True:
        errors.append("TOURNAMENT_DIMENSION_OPTIONAL: all_required must be true")

    for dim in payload.get("dimensions_without_aggregation") or []:
        errors.append(f"TOURNAMENT_AGGREGATION_UNDEFINED: {dim} defines no aggregation")
    for dim in payload.get("dimensions_without_fields") or []:
        errors.append(f"TOURNAMENT_FIELDS_UNDEFINED: {dim} defines no field")
    for dim in payload.get("dimensions_with_frozen_threshold") or []:
        errors.append(
            f"THRESHOLD_FROZEN_OUTSIDE_M2_FREEZE: {dim} threshold is no longer M2_FREEZE_REQUIRED"
        )

    # --- 不合成总分 ---
    if payload.get("no_single_composite_score_enforced") is not True:
        errors.append("COMPOSITE_SCORE_WITHOUT_FROZEN_WEIGHTS: contract does not forbid a composite score")
    for arm in payload.get("arms_with_composite_score") or []:
        errors.append(
            f"COMPOSITE_SCORE_WITHOUT_FROZEN_WEIGHTS: {arm} emits a composite score before "
            "Founder freezes the weights"
        )

    # --- 零真实调用 ---
    for hit in payload.get("forbidden_runtime_imports") or []:
        errors.append(
            f"REAL_MODEL_API_CALL_RISK: {RUNNER} imports {hit!r} — 本包禁止真实模型调用与网络访问"
        )
    if payload.get("declared_model_api_calls") != 0:
        errors.append(
            f"REAL_MODEL_API_CALL_PERFORMED: run reports {payload.get('declared_model_api_calls')!r} model calls"
        )
    if payload.get("declared_network_access") is not False:
        errors.append("REAL_MODEL_API_CALL_RISK: the run reports network access")

    # --- 确定性（实跑两次比对，不读声明） ---
    if not payload.get("dry_run_executed"):
        errors.append("DRY_RUN_NOT_EXECUTED: the skeleton was never run — 合同里写能跑不等于真的能跑")
    elif payload.get("dry_run_digest_first") != payload.get("dry_run_digest_second"):
        errors.append(
            f"DRY_RUN_NOT_DETERMINISTIC: two runs hashed to {payload.get('dry_run_digest_first')!r} "
            f"and {payload.get('dry_run_digest_second')!r} — 带抖动的聚合口径无法用于比较"
        )
    if payload.get("dry_run_arm_count", 0) < 2:
        errors.append(
            f"DRY_RUN_INSUFFICIENT_ARMS: {payload.get('dry_run_arm_count')} arm(s) — "
            "锦标赛至少要有两个臂才谈得上比较"
        )

    # --- 硬门聚合口径（从实跑结果核，不读合同） ---
    for arm in payload.get("arms_with_failed_gate_not_marked_failed") or []:
        errors.append(
            f"HARD_GATE_ABSORBED_BY_AVERAGE: {arm} has a failing hard gate but is not marked failed — "
            "硬门混进平均分等于允许高分抵消安全违规"
        )
    if payload.get("dry_run_exercised_failing_gate") is not True:
        errors.append(
            "HARD_GATE_AGGREGATION_UNEXERCISED: no dry-run arm exercises a failing hard gate — "
            "没被行使过的聚合口径不算验证过（EQ-3）"
        )
    for dim in payload.get("arms_missing_dimensions") or []:
        errors.append(f"TOURNAMENT_DIMENSION_MISSING: dry-run output omits {dim}")

    # --- OD-M2-01 ---
    od = payload.get("open_decision") or {}
    if od.get("open_decision_id") != "OD-M2-01":
        errors.append(f"OPEN_DECISION_NOT_REGISTERED: expected OD-M2-01, got {od.get('open_decision_id')!r}")
    if od.get("status") != "NOT_EXECUTED":
        errors.append(f"REAL_BASELINE_RUN_PERFORMED: OD-M2-01 status={od.get('status')!r}")
    if not od.get("cost_range_usd"):
        errors.append("OPEN_DECISION_WITHOUT_COST_ESTIMATE: OD-M2-01 carries no cost range")
    if not od.get("time_estimate_range"):
        errors.append("OPEN_DECISION_WITHOUT_TIME_ESTIMATE: OD-M2-01 carries no wall-clock estimate")
    if od.get("evidence_level") != "inferred":
        errors.append(
            f"COST_ESTIMATE_OVERSTATED: OD-M2-01 evidence_level={od.get('evidence_level')!r} — "
            "未实测的估算不得标成实测"
        )

    return errors


def _load_runner():
    spec = importlib.util.spec_from_file_location("run_tournament_dryrun", ROOT / RUNNER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def collect() -> dict:
    contract = load_yaml(CONTRACT)
    source = (ROOT / RUNNER).read_text(encoding="utf-8")

    imported = set(IMPORT_RE.findall(source))
    forbidden = sorted(
        name for name in imported
        if any(name == bad or name.startswith(bad + ".") for bad in FORBIDDEN_RUNTIME_IMPORTS)
    )

    dims = contract["dimensions"]["items"]
    dim_ids = [d["dimension_id"] for d in dims]

    module = _load_runner()
    first = module.run(ROOT / FIXTURE_DIR)
    second = module.run(ROOT / FIXTURE_DIR)
    dump = lambda o: json.dumps(o, ensure_ascii=False, indent=2, sort_keys=True)

    arms = first.get("arms") or []
    failed_gate_not_marked, missing_dims, composite = [], [], []
    exercised_failing_gate = False
    for arm in arms:
        has_fail = any(v == "fail" for v in (arm.get("hard_gate_results") or {}).values())
        if has_fail:
            exercised_failing_gate = True
            if not arm.get("arm_failed_by_hard_gate"):
                failed_gate_not_marked.append(arm.get("arm"))
        for dim in REQUIRED_DIMENSIONS:
            if dim not in (arm.get("dimensions") or {}):
                missing_dims.append(f"{arm.get('arm')}.{dim}")
        if arm.get("composite_score") is not None:
            composite.append(arm.get("arm"))

    real = contract["real_baseline_run"]

    return {
        "contract_dimensions": dim_ids,
        "contract_dimension_count": contract["dimensions"]["count"],
        "all_required": contract["dimensions"]["all_required"],
        "dimensions_without_aggregation": [d["dimension_id"] for d in dims if not d.get("aggregation")],
        "dimensions_without_fields": [d["dimension_id"] for d in dims if not d.get("fields")],
        "dimensions_with_frozen_threshold": [
            d["dimension_id"] for d in dims if d.get("threshold_status") != "M2_FREEZE_REQUIRED"
        ],
        "no_single_composite_score_enforced": contract["no_single_composite_score"]["enforced"],
        "arms_with_composite_score": composite,
        "forbidden_runtime_imports": forbidden,
        "declared_model_api_calls": first.get("model_api_calls"),
        "declared_network_access": first.get("network_access"),
        # B-04-4：此前写死 True——骨架一个臂也没跑出来，这一位照样说「跑过了」。
        # 现在由两次实跑各自是否产出结果对象推导。
        "dry_run_executed": isinstance(first, dict) and isinstance(second, dict) and bool(first) and bool(second),
        "dry_run_digest_first": sha256_text(dump(first)),
        "dry_run_digest_second": sha256_text(dump(second)),
        "dry_run_arm_count": len(arms),
        "dry_run_exercised_failing_gate": exercised_failing_gate,
        "arms_with_failed_gate_not_marked_failed": failed_gate_not_marked,
        "arms_missing_dimensions": missing_dims,
        "open_decision": {
            "open_decision_id": real["open_decision_id"],
            "status": real["status"],
            "cost_range_usd": real["cost_estimate"]["cost_range_usd"],
            "time_estimate_range": real["time_estimate"]["wall_clock_hours_range"],
            "evidence_level": real["cost_estimate"]["evidence_level"],
        },
    }


if __name__ == "__main__":
    cli(LABEL, collect, validate)
