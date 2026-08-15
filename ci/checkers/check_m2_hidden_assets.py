#!/usr/bin/env python3
"""隐藏评测资产：存储未就绪时必须为零，且不得就近落在主仓。

Phase 5 的第一件事是判存储就绪性，不是生成资产。STORE-A 按定义是执行侧不可读的
独立私有仓库——未 provision 就生成，只剩两条路：放主仓（永久留在 Git 历史里，
克隆提供完整对象历史，删除撤销不了泄漏），或者放一个执行侧可读的地方
（那就不满足隔离定义，形式上完成、实质上失效）。两条都不可接受，因此判据要求：
存储未就绪 → 资产计数必须为零，且必须有一份具名停止记录。

边界执行一概委派 check_hidden_benchmark_boundary，本判据不重写任何路径或内容扫描
（DUPLICATE_HIDDEN_BOUNDARY_IMPLEMENTATION）。这里只管三件事：
就绪性与资产计数是否自洽、停止是否被如实记录、可验证性原则是否落盘。

反自审绿（E12）：就绪性真值取自 governance/storage/ 的存储合同与条件台账，
不取自 M2 侧清单的自述——拿被检对象当真值，写错了也会显绿。
"""

from __future__ import annotations

from _common import ROOT, cli, load_yaml

LABEL = "check_m2_hidden_assets"

STORAGE_CONTRACT = "governance/storage/hidden_benchmark_storage_contract.yaml"
CONDITION_LEDGER = "governance/conditions/conditional_decision_ledger.yaml"
HIDDEN_DIR = "03_m2_evaluation_foundation/hidden_assets"
MANIFEST = f"{HIDDEN_DIR}/hidden_asset_manifest.v0.1.yaml"
STOP_RECORD = f"{HIDDEN_DIR}/hidden_asset_stop_record.v0.1.yaml"
GENERATION_CONTRACT = f"{HIDDEN_DIR}/hidden_asset_generation_contract.v0.1.yaml"
HIDDEN_BOUNDARY_CHECKER = "ci/checkers/check_hidden_benchmark_boundary.py"

ASSET_COUNT_FIELDS = (
    "asset_count", "hidden_benchmark_items", "hidden_brands", "fixture_brands", "answer_assets",
)

# 审查者可以看的与绝对不能要求看的——可验证性原则的机器形式。
REVIEWER_MAY_NOT_REQUEST = (
    "隐藏题正文", "参考答案", "隐藏品牌完整事实包", "逐题原始输出", "生成参数",
)


def validate(payload: dict) -> list[str]:
    errors: list[str] = []

    provisioned = payload.get("storage_provisioned")
    counts = payload.get("asset_counts") or {}

    # --- 就绪性与资产计数必须自洽 ---
    if provisioned is not True:
        for field, count in sorted(counts.items()):
            if count != 0:
                errors.append(
                    f"HIDDEN_ASSET_GENERATED_WITHOUT_STORAGE: {field}={count} while the Founder-selected "
                    "store is not provisioned — 未就绪就生成，只能落主仓或落可读处，两条都不可接受"
                )
        if not payload.get("stop_record_present"):
            errors.append(
                f"HIDDEN_STORAGE_NOT_PROVISIONED: storage is not provisioned but {STOP_RECORD} is absent — "
                "阻塞必须留下具名记录，不能只是没做"
            )
        elif payload.get("stop_condition_id") != "HIDDEN_STORAGE_NOT_PROVISIONED":
            errors.append(
                f"STOP_RECORD_MISTYPED: stop record declares {payload.get('stop_condition_id')!r}"
            )
        elif payload.get("stop_record_triggered") is not True:
            errors.append("STOP_RECORD_NOT_TRIGGERED: the stop record exists but does not declare it triggered")
        if payload.get("manifest_claims_delivered"):
            errors.append(
                "EMPTY_MANIFEST_PRESENTED_AS_DELIVERED: 空清单不得冒充已交付"
            )

    # --- 声明与计数一致 ---
    if payload.get("declared_asset_count") != counts.get("asset_count"):
        errors.append(
            f"MANIFEST_COUNT_DRIFT: manifest declares {payload.get('declared_asset_count')!r} "
            f"but the count field says {counts.get('asset_count')!r}"
        )
    hashes = payload.get("content_hash_count")
    if hashes != counts.get("asset_count"):
        errors.append(
            f"MANIFEST_HASH_COUNT_DRIFT: {hashes} content hash(es) for {counts.get('asset_count')} asset(s)"
        )
    if payload.get("manifest_frozen") and provisioned is not True:
        errors.append("PREMATURE_HIDDEN_FREEZE: manifest claims frozen while no asset exists")

    # --- 主仓边界：只委派，不重写 ---
    if payload.get("enforcement_delegated_to") != HIDDEN_BOUNDARY_CHECKER:
        errors.append(
            f"HIDDEN_BOUNDARY_NOT_DELEGATED: manifest delegates to "
            f"{payload.get('enforcement_delegated_to')!r}, expected {HIDDEN_BOUNDARY_CHECKER!r}"
        )
    if payload.get("second_implementation_created") is not False:
        errors.append("DUPLICATE_HIDDEN_BOUNDARY_IMPLEMENTATION: a second boundary implementation is declared")
    if payload.get("hidden_content_in_main_repository") is not False:
        errors.append("HIDDEN_CONTENT_WRITTEN_TO_MAIN_REPOSITORY: the manifest itself reports hidden content in the main repo")

    # --- 生成合同的三组条款必须在位 ---
    if not payload.get("sampling_design_bound"):
        errors.append("GENERATION_CONTRACT_INCOMPLETE: no sampling-design binding")
    if not payload.get("homogeneity_control_present"):
        errors.append("GENERATION_CONTRACT_INCOMPLETE: no homogeneity-control clause")
    if payload.get("synthetic_marking_required") is not True:
        errors.append(
            "SYNTHETIC_ASSET_UNMARKED: synthetic marking is not required — "
            "「看起来像真的」正是合成资产的设计目标，标记不能靠人记得"
        )
    if payload.get("founder_package_may_enter_hidden_pool"):
        errors.append("FOUNDER_PACKAGE_IN_HIDDEN_SET: Founder-provided real brand material must never enter the hidden pool (D-18)")
    for field in payload.get("sampling_restated_fields") or []:
        errors.append(f"SAMPLING_DESIGN_RESTATED: {field} is copied instead of referenced (EQ-1)")

    # --- 可验证性原则 ---
    vp = payload.get("verifiability_principle") or {}
    if not vp:
        errors.append("VERIFIABILITY_PRINCIPLE_MISSING: 收口核验方式未落合同")
    else:
        missing = sorted(set(REVIEWER_MAY_NOT_REQUEST) - set(vp.get("may_not_request") or []))
        if missing:
            errors.append(f"VERIFIABILITY_PRINCIPLE_INCOMPLETE: reviewers are not barred from requesting {missing}")
        if not vp.get("may_verify_with"):
            errors.append("VERIFIABILITY_PRINCIPLE_INCOMPLETE: no permitted verification surface is listed")
        if vp.get("on_such_request") != "一律拒绝并报告":
            errors.append(
                f"VERIFIABILITY_PRINCIPLE_WEAKENED: on_such_request={vp.get('on_such_request')!r} — "
                "要求读取隐藏内容才能核验，等于为了证明隔离而破坏隔离"
            )
        if vp.get("founder_exempt") is not True:
            errors.append("VERIFIABILITY_PRINCIPLE_OVERREACH: the Founder owns the hidden set and is not bound by this clause")

    return errors


def collect() -> dict:
    storage = load_yaml(STORAGE_CONTRACT)
    manifest = load_yaml(MANIFEST)
    generation = load_yaml(GENERATION_CONTRACT)
    stop_path = ROOT / STOP_RECORD
    stop = load_yaml(STOP_RECORD) if stop_path.exists() else {}

    # 就绪性真值：存储合同里那份 provisioned，不是 M2 清单的自述
    selected = storage["current_state"]["selected_storage_id"]
    provisioned = None
    for store in storage["allowed_storage"]:
        if store["id"] == selected:
            provisioned = store["provisioned"]

    ledger = load_yaml(CONDITION_LEDGER)
    conditions = ledger.get("conditions") if isinstance(ledger, dict) else ledger
    cond_status = None
    for cond in conditions or []:
        if cond.get("condition_id") == "COND-011":
            cond_status = cond.get("status")

    state = manifest["manifest_state"]
    vp = generation["verifiability_principle"]
    hom = generation.get("homogeneity_control") or {}
    sampling = generation.get("sampling_design_binding") or {}

    return {
        "storage_provisioned": provisioned,
        "selected_storage_id": selected,
        "cond_011_status": cond_status,
        "asset_counts": {f: state.get(f) for f in ASSET_COUNT_FIELDS},
        "declared_asset_count": state.get("asset_count"),
        "content_hash_count": len(state.get("content_hashes") or []),
        "manifest_frozen": state.get("frozen"),
        "manifest_claims_delivered": manifest.get("why_empty", {}).get("honest_state") is not True,
        "stop_record_present": bool(stop),
        "stop_condition_id": (stop.get("stop_condition") or {}).get("id"),
        "stop_record_triggered": (stop.get("stop_condition") or {}).get("triggered"),
        "enforcement_delegated_to": manifest["main_repository_compliance"]["enforcement_delegated_to"],
        "second_implementation_created": generation["single_implementation"]["second_implementation_created"],
        "hidden_content_in_main_repository": manifest["main_repository_compliance"]["hidden_content_in_main_repository"],
        "sampling_design_bound": bool(sampling.get("source")),
        "sampling_restated_fields": ["sampling_design_binding"] if sampling.get("restated_here") else [],
        "homogeneity_control_present": bool(hom.get("separated_on")),
        "synthetic_marking_required": generation["synthetic_marking"]["required"],
        "founder_package_may_enter_hidden_pool": not hom.get("founder_package_must_not_enter_hidden_pool", False),
        "verifiability_principle": {
            "may_verify_with": vp.get("reviewer_may_verify_with"),
            "may_not_request": vp.get("reviewer_may_not_request"),
            "on_such_request": vp.get("on_such_request"),
            "founder_exempt": vp.get("founder_exempt"),
        },
    }


if __name__ == "__main__":
    cli(LABEL, collect, validate)
