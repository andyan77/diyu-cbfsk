#!/usr/bin/env python3
"""M2 评测治理基础：三件套合同齐备、资产分类只有一套隔离实现、本包零资产。

启动包 v1.1 Phase 5 的三条纪律，逐条变成判据：

  合同先行     —— 评分者校准、抽样设计、基线修订三份合同必须带最小机器可检字段；
                  阈值一律保持 M2_FREEZE_REQUIRED，本包不得代为冻结。
  复用优先     —— 隐藏边界执行必须委派给既有 check_hidden_benchmark_boundary；
                  任何 check_m2_* 自建一套路径/内容扫描即 DUPLICATE_HIDDEN_BOUNDARY_IMPLEMENTATION。
  资产不在本包 —— 评测资产本体属 M2-EP02，本包分类合同落地、资产计数必须全零。

反自审绿（E12）：高风险全审覆盖、风险分层取值与校准合同规范名都不从本包的合同文件读，
而是从 role_operating_model 与 Envelope Schema 独立重算——拿自己写的合同当真值，写错了也会显绿。
"""

from __future__ import annotations

from _common import ROOT, cli, load_json, load_yaml, read_text

LABEL = "check_m2_evaluation_governance"

GOV_DIR = "03_m2_evaluation_foundation/evaluation_governance"
CALIBRATION = f"{GOV_DIR}/reviewer_calibration_contract.v0.1.yaml"
SAMPLING = f"{GOV_DIR}/evaluation_sampling_design.v0.1.yaml"
REVISION = f"{GOV_DIR}/benchmark_revision_protocol.v0.1.yaml"
CLASSIFICATION = f"{GOV_DIR}/evaluation_asset_classification_profile.v0.1.yaml"
ENVELOPE_SCHEMA = "03_m2_evaluation_foundation/envelope/m1_to_m2_envelope.schema.v0.1.json"
ROLE_MODEL = "governance/bootstrap/role_operating_model.v0.2.yaml"
HIDDEN_CHECKER = "ci/checkers/check_hidden_benchmark_boundary.py"
CHECKER_DIR = ROOT / "ci" / "checkers"

# 三件套＝M2 冻结 Brief 第 2 节第 8/9/10 项。判据按 Brief 项号绑定，不按 Delta 编号——
# D-09 是 PRD v1.1 Delta 的真实编号（第二部分「D-09 M2 评测治理三件套」），
# 但那套编号不在 v1.2 活合同的编号空间里，活判据引用它会指向一份已归档的文档。
REQUIRED_CONTRACTS = {
    "reviewer_calibration_contract.v0.1": CALIBRATION,
    "evaluation_sampling_design.v0.1": SAMPLING,
    "benchmark_revision_protocol.v0.1": REVISION,
}

TOURNAMENT_DIMENSIONS = ("quality", "cost", "latency", "human_intervention")

# 既有隐藏边界实现的判据常量名。任何 M2 checker 里出现同名常量，就是在造第二套。
HIDDEN_IMPLEMENTATION_MARKERS = ("FORBIDDEN_PATH_FRAGMENTS", "FORBIDDEN_CONTENT_MARKERS")

# D-28：②③类禁设唯一 Gold Answer。
GOLD_ANSWER_FORBIDDEN_FOR = ("mechanism_correctness", "open_decision")


def validate(payload: dict) -> list[str]:
    errors: list[str] = []

    for artifact_id, present in sorted((payload.get("contracts_present") or {}).items()):
        if not present:
            errors.append(f"EVALUATION_CONTRACT_MISSING: {artifact_id}")

    # --- 阈值不得被本包冻结 ---
    for item in payload.get("prematurely_frozen_thresholds") or []:
        errors.append(
            f"THRESHOLD_FROZEN_OUTSIDE_M2_FREEZE: {item['field']} in {item['artifact']} carries a value "
            "while still marked M2_FREEZE_REQUIRED — M2-EP01 不得代为冻结阈值"
        )

    # --- 高风险口径必须与规范源一致（真值独立取自 role_operating_model） ---
    if payload.get("canonical_high_risk_coverage") != "100%":
        errors.append(
            f"HIGH_RISK_COVERAGE: canonical source declares {payload.get('canonical_high_risk_coverage')!r}"
        )
    if payload.get("canonical_high_risk_sampling_allowed") is not False:
        errors.append("HIGH_RISK_SAMPLING_ALLOWED: canonical source permits sampling of high-risk items")
    if payload.get("sampling_high_risk_coverage") != 1.0:
        errors.append(
            f"HIGH_RISK_COVERAGE_DRIFT: sampling design declares {payload.get('sampling_high_risk_coverage')!r}, "
            "canonical source requires full 100% Founder review"
        )
    if payload.get("sampling_high_risk_sampling_allowed") is not False:
        errors.append("HIGH_RISK_SAMPLED: sampling design allows sampling of high-risk items")
    if payload.get("sampling_high_risk_adjustable") is not False:
        errors.append(
            "HIGH_RISK_COVERAGE_MARKED_ADJUSTABLE: 高风险全审覆盖率不是可调阈值"
        )

    canonical_tiers = payload.get("canonical_risk_tiers") or []
    declared_tiers = payload.get("sampling_risk_tiers") or []
    if canonical_tiers and sorted(declared_tiers) != sorted(canonical_tiers):
        errors.append(
            f"RISK_TIER_DRIFT: sampling design lists {sorted(declared_tiers)}, "
            f"canonical source implies {sorted(canonical_tiers)}"
        )
    if payload.get("sampling_dimension_count") != 3:
        errors.append(
            f"STRATIFICATION_DIMENSION_DRIFT: expected 3 (品类 × 任务类型 × 风险等级), "
            f"got {payload.get('sampling_dimension_count')!r}"
        )

    # --- 校准合同规范名（真值取自 role_operating_model） ---
    if payload.get("calibration_canonical_name") != payload.get("canonical_calibration_name"):
        errors.append(
            f"CALIBRATION_CONTRACT_NAME: contract declares {payload.get('calibration_canonical_name')!r}, "
            f"canonical source requires {payload.get('canonical_calibration_name')!r}"
        )
    for element in payload.get("missing_calibration_elements") or []:
        errors.append(f"CALIBRATION_ELEMENT_MISSING: {element}")

    # --- 锦标赛四维度 ---
    dims = payload.get("tournament_dimensions") or []
    if sorted(dims) != sorted(TOURNAMENT_DIMENSIONS):
        errors.append(
            f"TOURNAMENT_DIMENSION_DRIFT: {sorted(dims)} != {sorted(TOURNAMENT_DIMENSIONS)} — "
            "四维度缺一，比较结果不成立"
        )
    if payload.get("tournament_declared_count") != len(dims):
        errors.append(
            f"TOURNAMENT_DIMENSION_DRIFT: protocol declares count="
            f"{payload.get('tournament_declared_count')!r} but lists {len(dims)}"
        )
    if payload.get("threshold_lowered_after_failure") is not False:
        errors.append("THRESHOLD_LOWERED_AFTER_FAILURE: 因失败而降标永久禁止")
    if payload.get("revision_requires_founder_ruling") is not True:
        errors.append("REVISION_WITHOUT_FOUNDER_RULING: 冻结后修订必须绑定 Founder 裁决")
    if sorted(payload.get("gold_answer_forbidden_for") or []) != sorted(GOLD_ANSWER_FORBIDDEN_FOR):
        errors.append(
            f"OPEN_TASK_GOLD_ANSWER_RULE_DRIFT: {sorted(payload.get('gold_answer_forbidden_for') or [])} "
            f"!= {sorted(GOLD_ANSWER_FORBIDDEN_FOR)} (D-28)"
        )

    # --- 隐藏边界单一实现 ---
    if payload.get("enforcement_delegated_to") != HIDDEN_CHECKER:
        errors.append(
            f"HIDDEN_BOUNDARY_NOT_DELEGATED: classification profile delegates to "
            f"{payload.get('enforcement_delegated_to')!r}, expected {HIDDEN_CHECKER!r}"
        )
    if not payload.get("delegated_checker_exists"):
        errors.append(f"HIDDEN_BOUNDARY_NOT_DELEGATED: {HIDDEN_CHECKER} does not exist")
    if not payload.get("delegated_checker_registered"):
        errors.append(
            f"HIDDEN_BOUNDARY_NOT_DELEGATED: {HIDDEN_CHECKER} is not registered in the full suite — "
            "委派给一个不会被跑的 checker 等于没有委派"
        )
    if payload.get("second_implementation_declared") is not False:
        errors.append("DUPLICATE_HIDDEN_BOUNDARY_IMPLEMENTATION: the profile itself declares a second implementation")
    for hit in payload.get("m2_checkers_reimplementing_hidden_boundary") or []:
        errors.append(
            f"DUPLICATE_HIDDEN_BOUNDARY_IMPLEMENTATION: {hit['file']} defines {hit['marker']} — "
            "隐藏边界只能有一套实现（EQ-1）"
        )

    # --- 分类枚举与信封对齐 ---
    if sorted(payload.get("profile_classification_values") or []) != sorted(
        payload.get("envelope_classification_values") or []
    ):
        errors.append(
            f"CLASSIFICATION_ENUM_DRIFT: profile {sorted(payload.get('profile_classification_values') or [])} "
            f"!= envelope {sorted(payload.get('envelope_classification_values') or [])}"
        )
    for value in payload.get("hidden_values_marked_main_repo_storable") or []:
        errors.append(
            f"HIDDEN_CONTENT_WRITTEN_TO_MAIN_REPOSITORY: classification {value!r} is marked storable in the main repository"
        )

    # --- 本包零资产 ---
    for field, count in sorted((payload.get("asset_counts") or {}).items()):
        if count != 0:
            errors.append(
                f"EP01_FORBIDDEN_OUTPUT_PRODUCED: {field}={count}, M2-EP01 must produce no evaluation asset"
            )
    if payload.get("any_hidden_content_written_to_main_repository") is not False:
        errors.append("HIDDEN_CONTENT_WRITTEN_TO_MAIN_REPOSITORY: the profile itself reports hidden content in the main repo")

    return errors


def _threshold_scan(artifact: str, doc: dict) -> list[dict]:
    """标着 M2_FREEZE_REQUIRED 却已经填了值的字段——那就是提前冻结。"""
    out = []
    for field, spec in (doc.get("machine_checkable_fields") or {}).items():
        if not isinstance(spec, dict):
            continue
        if spec.get("threshold_status") == "M2_FREEZE_REQUIRED" and spec.get("current_value") is not None:
            out.append({"artifact": artifact, "field": field})
    return out


def collect() -> dict:
    calibration = load_yaml(CALIBRATION)
    sampling = load_yaml(SAMPLING)
    revision = load_yaml(REVISION)
    classification = load_yaml(CLASSIFICATION)
    envelope = load_json(ENVELOPE_SCHEMA)
    model = load_yaml(ROLE_MODEL)

    tiers = model["review_mode"]["risk_tiered_review"]
    canonical_calibration = model["review_mode"]["reviewer_calibration_contract"]

    contracts_present = {
        artifact_id: (ROOT / rel).exists() for artifact_id, rel in REQUIRED_CONTRACTS.items()
    }

    prematurely_frozen = []
    for artifact, doc in (("reviewer_calibration_contract.v0.1", calibration),
                          ("evaluation_sampling_design.v0.1", sampling),
                          ("benchmark_revision_protocol.v0.1", revision)):
        prematurely_frozen.extend(_threshold_scan(artifact, doc))

    sampling_rules = {rule["id"]: rule for rule in sampling["sampling_rules"]}
    sr1 = sampling_rules.get("SR-1", {})
    sampling_fields = sampling["machine_checkable_fields"]

    declared_elements = {item["machine_field"] for item in calibration["required_elements"]["items"]}
    calibration_fields = set(calibration["machine_checkable_fields"])
    missing_elements = sorted(declared_elements - calibration_fields)

    risk_dim = next(d for d in sampling["stratification_dimensions"]["items"] if d["dimension"] == "risk_tier")

    registry_source = read_text("ci/run_all_checks.py")

    duplicate_hits = []
    for path in sorted(CHECKER_DIR.glob("check_m2_*.py")):
        source = path.read_text(encoding="utf-8")
        for marker in HIDDEN_IMPLEMENTATION_MARKERS:
            # 只认「定义了同名常量」，不认「提到这个名字」——本 checker 自己就要提到它。
            if f"\n{marker} = " in source or f"\n{marker}=" in source:
                duplicate_hits.append({"file": str(path.relative_to(ROOT)), "marker": marker})

    classification_values = [row["value"] for row in classification["classification_field_contract"]["values"]]
    hidden_storable = [
        row["value"]
        for row in classification["classification_field_contract"]["values"]
        if row["value"] in ("hidden_evaluation", "restricted_founder_only")
        and row.get("main_repository_storage_allowed") is not False
    ]

    asset_state = classification["m2_ep01_asset_state"]

    return {
        "contracts_present": contracts_present,
        "prematurely_frozen_thresholds": prematurely_frozen,
        "canonical_high_risk_coverage": tiers["high_risk"]["founder_review_coverage"],
        "canonical_high_risk_sampling_allowed": tiers["high_risk"]["sampling_allowed"],
        "canonical_risk_tiers": tiers["tiers"],
        "canonical_calibration_name": canonical_calibration["canonical_name"],
        "sampling_high_risk_coverage": sr1.get("founder_review_coverage"),
        "sampling_high_risk_sampling_allowed": sr1.get("sampling_allowed"),
        "sampling_high_risk_adjustable": sampling_fields["high_risk_founder_full_review_rate"].get("adjustable"),
        "sampling_risk_tiers": risk_dim["values"],
        "sampling_dimension_count": sampling["stratification_dimensions"]["count"],
        "calibration_canonical_name": calibration["canonical_name"],
        "missing_calibration_elements": missing_elements,
        "tournament_dimensions": [d["dimension_id"] for d in revision["tournament_dimensions"]["items"]],
        "tournament_declared_count": revision["tournament_dimensions"]["count"],
        "threshold_lowered_after_failure": revision["machine_checkable_fields"][
            "threshold_lowered_after_failure"
        ]["required_value"],
        "revision_requires_founder_ruling": revision["revision_requirements"]["founder_ruling_required"],
        "gold_answer_forbidden_for": revision["open_decision_scoring"]["gold_answer_forbidden_for"],
        "enforcement_delegated_to": classification["single_implementation"]["enforcement_delegated_to"],
        "delegated_checker_exists": (ROOT / HIDDEN_CHECKER).exists(),
        "delegated_checker_registered": '"check_hidden_benchmark_boundary"' in registry_source,
        "second_implementation_declared": classification["single_implementation"]["second_implementation_created"],
        "m2_checkers_reimplementing_hidden_boundary": duplicate_hits,
        "profile_classification_values": classification_values,
        "envelope_classification_values": (
            (envelope["properties"]["data_classification"]).get("enum") or []
        ),
        "hidden_values_marked_main_repo_storable": hidden_storable,
        "asset_counts": {
            key: value for key, value in asset_state.items() if isinstance(value, int)
        },
        "any_hidden_content_written_to_main_repository": asset_state[
            "any_hidden_content_written_to_main_repository"
        ],
    }


if __name__ == "__main__":
    cli(LABEL, collect, validate)
