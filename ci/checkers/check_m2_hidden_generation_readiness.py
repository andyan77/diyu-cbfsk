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

import hashlib
import re

from _common import ROOT, cli, founder_ruling_evidence, is_full_commit_hash, load_yaml, sha256_file

LABEL = "check_m2_hidden_generation_readiness"

BUNDLE = "03_m2_evaluation_foundation/steward/hidden_generation_input_bundle.v1.1.0.yaml"
TIMING_GATE = "governance/conditions/hidden_generation_timing_gate.v0.1.yaml"
AGGREGATION = "03_m2_evaluation_foundation/calibration/calibration_aggregation.v0.1.yaml"
REVIEW_STATE = "03_m2_evaluation_foundation/calibration/calibration_review_state.v0.1.yaml"
SEMANTICS = "governance/conditions/m2_condition_state_semantics.v0.1.yaml"
LEDGER = "governance/conditions/conditional_decision_ledger.yaml"

REQUIRED_CATEGORIES = (
    "交付覆盖映射", "能力矩阵", "未见品牌切分", "未见品类边缘任务", "抽样设计",
    "任务类型合同", "三张横向评分卡", "七类纵向评分合同", "可接受决策边界注册表",
    "隐藏资产生成合同", "硬门定义", "Steward 执行 Prompt", "时序门合同",
)
# 状态只能在其前置被核验后推进；STORAGE_READY 的前置是 COND-011 关闭。
STATUS_REQUIRING_COND_011_CLOSED = (
    "STORAGE_READY", "GENERATED", "PRIVATE_REVIEWED", "PRIVATE_FROZEN", "PUBLIC_MANIFEST_IMPORTED",
)


def _content_digest(files: list[dict]) -> str:
    """摘要覆盖的是「路径→哈希」清单，不覆盖输入包自身——单一实现在 ci/tools/refresh_hidden_bundle.py，
    这里现算一遍作比对，比对的是同一个定义。"""
    lines = sorted(f"{row['path']}\t{row['sha256']}" for row in files)
    return hashlib.sha256(("\n".join(lines) + "\n").encode("utf-8")).hexdigest()


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

    if payload.get("declared_content_digest") != payload.get("actual_content_digest"):
        errors.append(
            f"BUNDLE_CONTENT_DIGEST_STALE: the bundle records digest {payload.get('declared_content_digest')!r}, "
            f"recomputing over its file list gives {payload.get('actual_content_digest')!r}"
        )

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


def _validate_founder_confirmation(gate: dict, errors: list[str]) -> None:
    """C-5／BLOCK-M2E5-01：确认不得是裸布尔值。

    一个 false 改成 true 只要一次键盘操作，事后看不出是谁在哪个版本上确认的。
    因此置 true 时必须同时给出签署人、时点、完整 40 位基线 Commit，
    以及一份存在且条款路径解析得出来的具名裁决——四项缺一即不算确认。
    """
    fc = gate.get("founder_confirmation") or {}
    if gate.get("state") is True and fc.get("confirmed") is not True:
        errors.append(
            "EXECUTION_SIDE_FLIPPED_TIMING_GATE: the gate is open without a recorded Founder confirmation"
        )
    if fc.get("confirmed") is not True:
        return
    for field in ("confirmed_by", "confirmed_at", "ruling_ref", "ruling_clause_path"):
        if not (fc.get(field) or "").strip():
            errors.append(f"FOUNDER_CONFIRMATION_UNBOUND: confirmation carries no {field}")
    if fc.get("commit_is_full_hash") is not True:
        errors.append(
            f"FOUNDER_CONFIRMATION_UNBOUND: confirmed_at_commit {fc.get('confirmed_at_commit')!r} "
            "is not a full 40-hex commit"
        )
    if fc.get("ruling_file_exists") is not True:
        errors.append(f"FOUNDER_CONFIRMATION_UNBOUND: ruling {fc.get('ruling_ref')!r} has no file on disk")
    elif fc.get("ruling_clause_resolves") is not True:
        errors.append(
            f"FOUNDER_CONFIRMATION_UNBOUND: clause {fc.get('ruling_clause_path')!r} does not resolve "
            f"inside {fc.get('ruling_ref')!r}"
        )


def _validate_store_a(payload: dict, gate: dict, errors: list[str]) -> None:
    """C-6：证据是那两份文件，不是台账对那两份文件的转述。"""
    ev = gate.get("store_a_evidence") or {}

    if ev.get("declared_status") != ev.get("derived_status"):
        errors.append(
            f"STORE_A_LEDGER_SELF_REPORT: the ledger records status {ev.get('declared_status')!r}, "
            f"reading the evidence files derives {ev.get('derived_status')!r}"
        )
    for leak in ev.get("leaks") or []:
        errors.append(f"STORE_A_EVIDENCE_LEAKS_LOCATOR: {leak}")

    if ev.get("derived_status") == "RECEIVED":
        for missing in sorted(set(ev.get("required_fields") or []) - set(ev.get("received_fields") or [])):
            errors.append(f"STORE_A_EVIDENCE_INCOMPLETE: STORE-A evidence lacks {missing!r}")
        actual_values = ev.get("actual_values") or {}
        for field, expected in (ev.get("required_values") or {}).items():
            if actual_values.get(field) != expected:
                errors.append(
                    f"STORE_A_EVIDENCE_INCOMPLETE: {field} is {actual_values.get(field)!r}, must be {expected!r}"
                )
        actual_access = ev.get("actual_access") or {}
        for role, expected in (ev.get("required_access") or {}).items():
            if actual_access.get(role) != expected:
                errors.append(
                    f"STORE_A_EVIDENCE_INCOMPLETE: access[{role}] is {actual_access.get(role)!r}, "
                    f"must be {expected!r}"
                )

    if payload.get("cond_011_status") == "CLOSED" and ev.get("cond_011_may_close") is not True:
        errors.append(
            "STORE_A_EVIDENCE_INCOMPLETE: COND-011 is closed while the evidence files do not support closing it"
        )


def _validate_timing_gate(payload: dict, errors: list[str]) -> None:
    """EP05 第七节 ＋ CORRECTION C-5／C-6：正式批必须等阈值冻结，试产批不得混进正式数。"""
    gate = payload.get("timing_gate") or {}

    for item in gate.get("preconditions") or []:
        recomputed = item.get("recomputed")
        if recomputed is not None and item.get("declared") != recomputed:
            errors.append(
                f"TIMING_GATE_PRECONDITION_MISSTATED: {item.get('id')} declares {item.get('declared')!r}, "
                f"its evidence source gives {recomputed!r}"
            )

    declared_count = len(gate.get("preconditions") or [])
    expected_count = gate.get("declared_precondition_count")
    if expected_count is not None and declared_count != expected_count:
        errors.append(
            f"TIMING_GATE_PRECONDITION_MISSTATED: the gate declares {expected_count!r} preconditions, "
            f"lists {declared_count}"
        )

    satisfied = all(item.get("declared") is True for item in gate.get("preconditions") or [])
    if gate.get("state") is True and not satisfied:
        errors.append(
            "TIMING_GATE_OPEN_WITHOUT_PRECONDITIONS: the gate is open while some precondition is unmet"
        )
    _validate_founder_confirmation(gate, errors)

    if gate.get("formal_batch_started") is True and gate.get("state") is not True:
        errors.append(
            "FORMAL_BATCH_BEFORE_TIMING_GATE: the 40-brand formal batch started while the gate is closed"
        )
    limit = gate.get("pilot_brand_limit")
    if isinstance(limit, int) and (gate.get("pilot_brand_count") or 0) > limit:
        errors.append(
            f"PILOT_BATCH_EXCEEDS_LIMIT: {gate.get('pilot_brand_count')} pilot brands exceed the limit of {limit}"
        )
    if gate.get("pilot_counted_in_brand_count") is True:
        errors.append("PILOT_COUNTED_IN_BRAND_COUNT: pilot brands must not be counted in brand_count")
    if (gate.get("pilot_brand_count") or 0) > 0 and (gate.get("counted_brand_count") or 0) > 0 \
            and gate.get("state") is not True:
        errors.append(
            "PILOT_COUNTED_IN_BRAND_COUNT: brands are counted while only a pilot batch is authorised"
        )

    _validate_store_a(payload, gate, errors)
    if payload.get("hidden_assets_status") in STATUS_REQUIRING_COND_011_CLOSED \
            and gate.get("boundary_recheck_performed") is not True:
        errors.append(
            "BOUNDARY_RECHECK_SKIPPED_ON_INTAKE: hidden asset status advanced without the boundary recheck"
        )


def validate(payload: dict) -> list[str]:
    errors: list[str] = []
    _validate_bundle(payload, errors)
    _validate_semantics(payload, errors)
    _validate_timing_gate(payload, errors)
    return errors


# 定位符扫描：这两份文件要证明隔离成立，不是让人找得到仓库。
LOCATOR_PATTERNS = (
    ("URL scheme", re.compile(r"[a-zA-Z][a-zA-Z0-9+.-]*://")),
    ("scp 式 git 地址", re.compile(r"\b[\w.-]+@[\w.-]+:")),
    ("代码托管仓库定位符", re.compile(r"github\.com|gitlab|bitbucket|gitee|codeberg|\.git\b", re.I)),
    ("Token", re.compile(r"ghp_|github_pat_|gho_|glpat-|AKIA[0-9A-Z]{8}|xox[baprs]-")),
    ("Deploy Key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----|ssh-(rsa|ed25519|dss)")),
    ("本机绝对路径", re.compile(r"(^|\s)(/home/|/Users/|/root/|/mnt/|[A-Za-z]:\\\\)")),
    ("私有主机名或内网地址", re.compile(r"\b(?:10|127|192\.168)\.\d|\.local\b|\.internal\b|\blocalhost\b", re.I)),
    ("随机种子", re.compile(r"\bseed\b", re.I)),
)


def _scalars(node, path="") -> list[tuple[str, str]]:
    if isinstance(node, dict):
        return [pair for k, v in node.items() for pair in _scalars(v, f"{path}.{k}" if path else str(k))]
    if isinstance(node, list):
        return [pair for i, v in enumerate(node) for pair in _scalars(v, f"{path}[{i}]")]
    return [(path, str(node))] if node is not None else []


def _read_store_a_evidence(spec: dict, required_fields: list[str]) -> dict:
    """从固定目录读两份真实 YAML。文件不在就是没收到——不读台账怎么说。"""
    directory = spec["intake_directory"]
    files, present, received_fields, leaks = [], [], set(), []
    values: dict = {}
    access: dict = {}
    for entry in spec["files"]:
        rel = f"{directory}{entry['name']}"
        path = ROOT / rel
        exists = path.exists()
        doc = load_yaml(rel) if exists else {}
        files.append({"name": entry["name"], "exists": exists, "sha256": sha256_file(path) if exists else None})
        present.append(exists)
        if not exists:
            continue
        received_fields |= {k for k in doc if k in required_fields}
        if "founder_attestation" in doc:
            received_fields.add("founder_attestation")
        values.update({k: v for k, v in doc.items() if not isinstance(v, (dict, list))})
        if isinstance(doc.get("access"), dict):
            access = doc["access"]
            received_fields.add("access")
        for key, text in _scalars(doc):
            for label, pattern in LOCATOR_PATTERNS:
                if pattern.search(text):
                    leaks.append(f"{entry['name']}:{key} looks like a {label}")

    derived = "RECEIVED" if all(present) and present else "NOT_RECEIVED"
    complete = (
        derived == "RECEIVED"
        and not leaks
        and not (set(required_fields) - received_fields)
        and all(values.get(f) == v for f, v in spec["required_values"].items())
        and all(access.get(r) == v for r, v in spec["required_access_matrix"].items())
    )
    return {
        "declared_status": spec["status"],
        "derived_status": derived,
        "files": files,
        "required_fields": required_fields,
        "received_fields": sorted(received_fields),
        "required_values": spec["required_values"],
        "actual_values": values,
        "required_access": spec["required_access_matrix"],
        "actual_access": access,
        "leaks": leaks,
        "cond_011_may_close": complete,
    }


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

    gate = load_yaml(TIMING_GATE)
    aggregation_doc = load_yaml(AGGREGATION)
    review_state = load_yaml(REVIEW_STATE)

    # 前四项前置由判据现算，不读门自己的声明——门是被检对象。
    sides_collected = all(
        (side.get("record_count") or 0) >= (side.get("expected_record_count") or 0) > 0
        for side in review_state["sides"]
    )
    thresholds_frozen = bool(threshold["items"]) and all(
        item.get("founder_decision") is not None and is_full_commit_hash(item.get("founder_decision_commit"))
        for item in threshold["items"]
    )
    recomputed = {
        "TG-01": sides_collected,
        "TG-02": bool((aggregation_doc.get("disagreement_statistics") or {}).get("computed")),
        "TG-03": threshold["counts"]["recommendation_absent"] == 0,
        "TG-04": thresholds_frozen and conditions["COND-007"]["status"] == "CLOSED",
        "TG-05": None,
    }
    preconditions = [
        {
            "id": item["id"],
            "declared": item["current"],
            "recomputed": recomputed.get(item["id"]),
        }
        for item in gate["preconditions"]["items"]
    ]
    evidence = gate["store_a_evidence"]
    required_fields = sorted(
        {field for spec in evidence["files"] for field in spec["minimum_fields"]}
    )
    store_a = _read_store_a_evidence(evidence, required_fields)

    confirmation = gate["founder_confirmation"]
    ruling_evidence = founder_ruling_evidence(
        confirmation.get("ruling_ref"), confirmation.get("ruling_clause_path")
    )

    blueprint = semantics["m2_public_blueprint_status"]
    return {
        "timing_gate": {
            "state": gate["state"]["current_value"],
            "preconditions": preconditions,
            "founder_confirmed": gate["founder_confirmation"]["confirmed"],
            "formal_batch_started": gate["current_generation_state"]["formal_batch_started"],
            "pilot_brand_count": gate["current_generation_state"]["pilot_brand_count"],
            "counted_brand_count": gate["current_generation_state"]["counted_brand_count"],
            "pilot_brand_limit": next(
                a["constraints"]["pilot_brand_limit"]
                for a in gate["while_false"]["allowed"] if a["id"] == "AL-03"
            ),
            "pilot_counted_in_brand_count": next(
                a["constraints"]["counted_in_brand_count"]
                for a in gate["while_false"]["allowed"] if a["id"] == "AL-03"
            ),
            "boundary_recheck_performed": gate["on_main_repo_acceptance"]["boundary_recheck_performed"],
            "declared_precondition_count": gate["preconditions"]["count"],
            "founder_confirmation": {
                "confirmed": confirmation["confirmed"],
                "confirmed_by": confirmation["confirmed_by"],
                "confirmed_at": confirmation["confirmed_at"],
                "confirmed_at_commit": confirmation["confirmed_at_commit"],
                "commit_is_full_hash": is_full_commit_hash(confirmation["confirmed_at_commit"]),
                "ruling_ref": confirmation["ruling_ref"],
                "ruling_clause_path": confirmation["ruling_clause_path"],
                "ruling_file_exists": ruling_evidence["file_exists"],
                "ruling_clause_resolves": ruling_evidence["clause_resolves"],
            },
            "store_a_evidence": store_a,
        },
        "files": files,
        "declared_content_digest": bundle["bundle_content_digest"],
        "actual_content_digest": _content_digest(bundle["files"]),
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
