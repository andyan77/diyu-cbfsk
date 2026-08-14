#!/usr/bin/env python3
"""A→B 输入包与条件/状态语义分离。

两件事容易出错，这里各守一半：

其一，输入包会过期而没人发现。Steward 在私有仓库里按一份快照出题，公开侧改了一条边界，
两边就不再谈同一套标准了——而且事后无法知道是哪一条变的。因此每个输入文件的哈希都现算比对，
不符即判 STALE，且必须连带把已生成资产标为作废；「只是小改」不是理由。

其二，条件与状态被混着用。COND-011 问的是「存储 provision 了没有」，
m2_hidden_assets_status 问的是「资产到哪一步了」。绑在一起就会出现死锁或谎报：
存储明明好了却因为资产没生成而关不掉条件，或者为了关条件而把资产状态往前写。
这里守的是：状态不得跑在证据前面。
"""

from __future__ import annotations

from _common import ROOT, cli, load_yaml, sha256_file

LABEL = "check_m2_hidden_generation_readiness"

BUNDLE = "03_m2_evaluation_foundation/steward/hidden_generation_input_bundle.v1.0.0.yaml"
SEMANTICS = "governance/conditions/m2_condition_state_semantics.v0.1.yaml"
LEDGER = "governance/conditions/conditional_decision_ledger.yaml"

REQUIRED_CATEGORIES = (
    "交付覆盖映射", "能力矩阵", "未见品牌切分", "未见品类边缘任务", "抽样设计",
    "任务类型合同", "三张横向评分卡", "七类纵向评分合同", "可接受决策边界注册表",
    "隐藏资产生成合同", "硬门定义", "Steward 执行 Prompt",
)
# 状态只能在其前置被核验后推进；STORAGE_READY 的前置是 COND-011 关闭。
STATUS_REQUIRING_COND_011_CLOSED = (
    "STORAGE_READY", "GENERATED", "PRIVATE_REVIEWED", "PRIVATE_FROZEN", "PUBLIC_MANIFEST_IMPORTED",
)


def _validate_bundle(payload: dict, errors: list[str]) -> None:
    files = payload.get("files") or []
    if not files:
        errors.append("REQUIRED_INPUT_FILE_MISSING: the bundle lists no file at all")

    stale = []
    for row in files:
        if not row.get("exists"):
            errors.append(f"REQUIRED_INPUT_FILE_MISSING: {row.get('path')!r} is listed but does not exist")
            continue
        if row.get("declared_sha256") != row.get("actual_sha256"):
            stale.append(row.get("path"))

    if stale:
        for path in stale:
            errors.append(
                f"HIDDEN_INPUT_BUNDLE_STALE: {path} no longer hashes to the value recorded in the bundle"
            )
        if payload.get("input_status") != "STALE":
            errors.append(
                f"HIDDEN_INPUT_BUNDLE_STALE: {len(stale)} file(s) changed but hidden_generation_input_status "
                f"is still {payload.get('input_status')!r} — 「只是小改」不是理由"
            )
        if payload.get("existing_assets_status") not in ("INVALIDATED_REQUIRES_REGENERATION", "NONE_GENERATED"):
            errors.append(
                "STALE_BUNDLE_USED_FOR_GENERATION: inputs changed but existing hidden assets are not marked invalid"
            )

    declared = set(payload.get("declared_categories") or [])
    for category in REQUIRED_CATEGORIES:
        if category not in declared:
            errors.append(f"REQUIRED_CATEGORY_MISSING: the bundle covers no {category!r}")

    prompt = payload.get("steward_prompt") or {}
    if not prompt.get("exists"):
        errors.append(f"REQUIRED_INPUT_FILE_MISSING: steward prompt {prompt.get('path')!r} does not exist")
    elif prompt.get("declared_sha256") != prompt.get("actual_sha256"):
        errors.append("STEWARD_PROMPT_HASH_STALE: the steward prompt no longer matches its recorded hash")
    if prompt.get("summary_does_not_substitute_full_file") is not True:
        errors.append(
            "STEWARD_PROMPT_SUMMARY_SUBSTITUTED: the bundle must state that a summary cannot replace the full prompt"
        )

    if payload.get("declared_file_count") != len(files):
        errors.append(
            f"BUNDLE_FILE_COUNT_MISSTATED: bundle declares {payload.get('declared_file_count')!r} files, lists {len(files)}"
        )


def _validate_semantics(payload: dict, errors: list[str]) -> None:
    status = payload.get("hidden_assets_status")
    allowed = payload.get("hidden_assets_status_allowed") or []
    if status not in allowed:
        errors.append(f"HIDDEN_ASSET_STATUS_UNKNOWN: {status!r} is not one of {allowed}")
    elif status in STATUS_REQUIRING_COND_011_CLOSED and payload.get("cond_011_status") != "CLOSED":
        errors.append(
            f"HIDDEN_ASSET_STATUS_AHEAD_OF_EVIDENCE: status is {status!r} while COND-011 is "
            f"{payload.get('cond_011_status')!r} — 状态不得跑在证据前面"
        )

    if payload.get("cond_007_has_hidden_side") is not False:
        errors.append("THRESHOLD_CLOSED_BY_WRONG_ROLE: COND-007 must declare that it has no hidden side")
    if payload.get("cond_007_workface_b_may_close") is not False:
        errors.append("THRESHOLD_CLOSED_BY_WRONG_ROLE: workface B must not be allowed to close COND-007")
    if payload.get("cond_007_status") == "CLOSED" and not payload.get("threshold_recommendations_present"):
        errors.append("THRESHOLD_CLOSED_BY_WRONG_ROLE: COND-007 is closed without any threshold recommendation")

    if payload.get("blueprint_is_execution_status") is not False:
        errors.append(
            "BLUEPRINT_STATUS_LEAKED_INTO_EXECUTION_STATUS: the new blueprint status must not enter the "
            "execution_status enum without its own authorization"
        )
    if payload.get("blueprint_status_value") in payload.get("execution_status_authorized_values") or []:
        errors.append(
            "BLUEPRINT_STATUS_LEAKED_INTO_EXECUTION_STATUS: the blueprint status appears in execution_status "
            "authorized_values"
        )

    gate = payload.get("final_gate") or {}
    satisfied = sum(1 for item in gate.get("items") or [] if item.get("current") is True)
    if gate.get("satisfied_count") != satisfied:
        errors.append(
            f"FINAL_GATE_COUNT_MISSTATED: gate declares {gate.get('satisfied_count')!r} satisfied, items give {satisfied}"
        )
    if gate.get("gate_open") is True and satisfied != len(gate.get("items") or []):
        errors.append(
            "FINAL_GATE_OPENED_EARLY: the final asset existence gate is open while some criteria are unmet"
        )
    for item in gate.get("items") or []:
        if item.get("current") is False and not item.get("blocked_by"):
            errors.append(f"FINAL_GATE_UNMET_WITHOUT_BLOCKER: {item.get('id')} is unmet but names no blocker")

    for stop in payload.get("current_stops") or []:
        for kind in stop.get("types") or []:
            if kind not in (payload.get("stop_types") or []):
                errors.append(f"STOP_TYPE_UNKNOWN: {stop.get('stop_id')} declares unknown STOP type {kind!r}")
        if not stop.get("types"):
            errors.append(f"STOP_TYPE_UNKNOWN: {stop.get('stop_id')} declares no STOP type at all")


def validate(payload: dict) -> list[str]:
    errors: list[str] = []
    _validate_bundle(payload, errors)
    _validate_semantics(payload, errors)
    return errors


def collect() -> dict:
    bundle = load_yaml(BUNDLE)
    semantics = load_yaml(SEMANTICS)
    ledger = load_yaml(LEDGER)
    signoff = load_yaml("governance/receipts/founder_signoff_receipt.yaml")
    threshold = load_yaml("03_m2_evaluation_foundation/calibration/threshold_freeze_decision.v0.1.yaml")

    conditions = {c["condition_id"]: c for c in ledger["conditions"]}
    prompt = bundle["steward_prompt"]
    prompt_path = prompt["path"]

    files = []
    for row in bundle["files"]:
        path = ROOT / row["path"]
        files.append(
            {
                "path": row["path"],
                "exists": path.exists(),
                "declared_sha256": row["sha256"],
                "actual_sha256": sha256_file(path) if path.exists() else None,
            }
        )

    blueprint = semantics["m2_public_blueprint_status"]
    return {
        "files": files,
        "declared_file_count": bundle["file_count"],
        "declared_categories": [c["category"] for c in bundle["required_file_categories"]],
        "input_status": bundle["current_state"]["hidden_generation_input_status"],
        "existing_assets_status": bundle["current_state"]["existing_hidden_assets_status"],
        "steward_prompt": {
            "path": prompt_path,
            "exists": (ROOT / prompt_path).exists(),
            "declared_sha256": prompt["sha256"],
            "actual_sha256": sha256_file(ROOT / prompt_path) if (ROOT / prompt_path).exists() else None,
            "summary_does_not_substitute_full_file": prompt["summary_does_not_substitute_full_file"],
        },
        "hidden_assets_status": semantics["m2_hidden_assets_status"]["current_value"],
        "hidden_assets_status_allowed": semantics["m2_hidden_assets_status"]["allowed_values"],
        "cond_011_status": conditions["COND-011"]["status"],
        "cond_007_status": conditions["COND-007"]["status"],
        "cond_007_has_hidden_side": semantics["cond_007"]["has_hidden_side"],
        "cond_007_workface_b_may_close": semantics["cond_007"]["workface_b_may_close"],
        "threshold_recommendations_present": any(
            item.get("threshold_recommendation") is not None for item in threshold["items"]
        ),
        "blueprint_status_value": blueprint["value"],
        "blueprint_is_execution_status": not blueprint["is_not_execution_status"],
        "execution_status_authorized_values": (
            (signoff.get("state_flag_authorizations") or {}).get("execution_status") or {}
        ).get("authorized_values")
        or [],
        "final_gate": semantics["final_asset_existence_gate"],
        "current_stops": semantics["stop_taxonomy"]["current_stops"],
        "stop_types": [t["id"] for t in semantics["stop_taxonomy"]["types"]],
    }


if __name__ == "__main__":
    cli(LABEL, collect, validate)
