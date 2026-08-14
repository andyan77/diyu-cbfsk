#!/usr/bin/env python3
"""M2 挂起封存：以机器状态封存，不以意图封存。

「以意图封存」是写一句「我们暂停推进」；「以机器状态封存」是把每一项的当前值钉成可复算的字段，
并让判据在有人推进时当场拦下。前者靠人记得，后者不靠。上一版封口台账自述
「本台账没有机器守卫……封存靠人遵守，不靠判据拦阻」——本判据就是那句话的替代品。

守五件事：

  包没被动过 —— 校准包逐文件哈希与封存快照现算比对。任一文件变了、或文件集有增删，
                distribution_status 必须是 REQUIRES_RECONFIRMATION，不得仍写 NOT_DISTRIBUTED。
                哈希变了而状态还写着「没动过」，恢复的人会照着那句话直接发出去，发出去的却是另一份包。
  缺口没被绕过 —— 三条已知设计缺口的处置只能由 Founder 做。执行侧填了处置人即 FAIL；
                缺口未处置而包已分发即 FAIL。带着缺口分发，分歧统计里会混进「题出得有问题」，
                而统计分不出这一层，最后记在评审员头上。
  封存项没自己往前走 —— 隐藏资产计数、阈值冻结数、时序门满足数、18 项矩阵四态，
                逐项与封存快照比对；越过封存值必须有具名解封裁决。
  转达没被润色 —— 裁决第三节的四问与四项不在范围内，逐字比对裁决原文与转达件正文。
                改一个字就不再是「原样转达」。
  合并没抢跑 —— 三门未齐备不得合并；标签不得在合并核验通过前打。

反自审绿：包的真值现算文件字节，不读封存清单的自述；被封各项的真值取自各自真源文件，
不取自封口台账的复述；四问的真值取自裁决文件，不取自转达件自己。
"""

from __future__ import annotations

import hashlib
import subprocess

from _common import ROOT, cli, founder_ruling_evidence, is_full_commit_hash, load_yaml, read_text

LABEL = "check_m2_suspension_seal"

RULING = "governance/founder_rulings/DIYU-CBFSK-FOUNDER-M2-SUSPENSION-001.yaml"
SEAL_LEDGER = "governance/conditions/m2_seal_ledger.v0.1.yaml"
PACK_SEAL = "03_m2_evaluation_foundation/calibration/launch_pack_seal_manifest.v0.1.yaml"
GAPS = "03_m2_evaluation_foundation/calibration/known_design_gaps.v0.1.yaml"
REVIEW_REQUEST = "governance/reports/m2_premerge_review_request.v0.1.yaml"
REVIEW_TRANSMITTAL = "governance/reports/m2_premerge_review_request.md"
MERGE_PROTOCOL = "governance/conditions/mainline_freeze_and_merge_protocol.v0.1.yaml"
ROLE_MODEL = "governance/bootstrap/role_operating_model.v0.2.yaml"
CAL = "03_m2_evaluation_foundation/calibration/public_calibration_set.v0.1.yaml"
COVERAGE_MAP = "03_m2_evaluation_foundation/closure/m2_deliverable_coverage_map.v0.1.yaml"
HIDDEN_MANIFEST = "03_m2_evaluation_foundation/hidden_assets/hidden_asset_manifest.v0.1.yaml"
THRESHOLDS = "03_m2_evaluation_foundation/calibration/threshold_freeze_decision.v0.1.yaml"
TIMING_GATE = "governance/conditions/hidden_generation_timing_gate.v0.1.yaml"
ANCHOR_TRUTH = "03_m2_evaluation_foundation/calibration/founder_boundary_anchor_truth.v0.1.yaml"
REVIEW_STATE = "03_m2_evaluation_foundation/calibration/calibration_review_state.v0.1.yaml"
CONDITION_LEDGER = "governance/conditions/conditional_decision_ledger.yaml"

SUSPENDED = "SUSPENDED_BY_FOUNDER"
PACK_STATUSES = ("NOT_DISTRIBUTED", "REQUIRES_RECONFIRMATION", "DISTRIBUTED")
EXPECTED_GAPS = 3
EXPECTED_QUESTIONS = 4
EXPECTED_OUT_OF_SCOPE = 4
EXPECTED_RESTORE_STEPS = 9
EXPECTED_MUST_NOT_ASSUME = 2
FOUNDER_ROLE = "FOUNDER_PRODUCT_AUTHORITY"


def _validate_pack_seal(payload: dict, errors: list[str]) -> None:
    sealed = payload.get("sealed_pack_files") or {}
    live = payload.get("live_pack_files") or {}
    status = payload.get("pack_distribution_status")

    if status not in PACK_STATUSES:
        errors.append(f"SEALED_PACK_STATUS_INVALID: distribution_status is {status!r}, not one of {PACK_STATUSES}")

    missing = sorted(set(sealed) - set(live))
    added = sorted(set(live) - set(sealed))
    changed = sorted(p for p in set(sealed) & set(live) if sealed[p] != live[p])

    for path in missing:
        errors.append(f"SEALED_PACK_FILE_SET_CHANGED: {path} was sealed but is absent from the pack")
    for path in added:
        errors.append(f"SEALED_PACK_FILE_SET_CHANGED: {path} sits in the pack but was never sealed")
    for path in changed:
        errors.append(
            f"SEALED_PACK_FILE_CHANGED: {path} hashes to {live[path][:12]}…, "
            f"the seal records {sealed[path][:12]}…"
        )

    drifted = bool(missing or added or changed)
    if drifted and status == "NOT_DISTRIBUTED":
        errors.append(
            "SEALED_PACK_STATUS_INVALID: the pack drifted from its seal while distribution_status still reads "
            "NOT_DISTRIBUTED — 裁决要求一律判为需重新确认（REQUIRES_RECONFIRMATION），不得直接分发"
        )
    if not drifted and status == "REQUIRES_RECONFIRMATION":
        errors.append(
            "SEALED_PACK_STATUS_INVALID: distribution_status claims the pack needs reconfirmation, "
            "but every sealed hash still matches"
        )
    if status == "DISTRIBUTED" and payload.get("m2_status") == SUSPENDED:
        errors.append(
            "SEALED_PACK_DISTRIBUTED_WHILE_SUSPENDED: the pack is marked DISTRIBUTED while M2 is suspended"
        )

    if payload.get("declared_pack_digest") != payload.get("recomputed_sealed_digest"):
        errors.append(
            f"SEALED_PACK_DIGEST_MISSTATED: the seal declares {str(payload.get('declared_pack_digest'))[:12]}…, "
            f"its own file list hashes to {str(payload.get('recomputed_sealed_digest'))[:12]}…"
        )
    if payload.get("declared_pack_file_count") != len(sealed):
        errors.append(
            f"SEALED_PACK_DIGEST_MISSTATED: the seal declares {payload.get('declared_pack_file_count')!r} files, "
            f"lists {len(sealed)}"
        )

    for row in payload.get("review_sink_counts") or []:
        if row["live"] != row["sealed"]:
            errors.append(
                f"SEALED_REVIEW_RECORDS_APPEARED: {row['side_id']} holds {row['live']} record(s), "
                f"the seal records {row['sealed']} — 记录出现意味着包已经发出去了"
            )


def _validate_design_gaps(payload: dict, errors: list[str]) -> None:
    gaps = payload.get("design_gaps") or []
    if payload.get("declared_gap_count") != len(gaps) or len(gaps) != EXPECTED_GAPS:
        errors.append(
            f"DESIGN_GAP_COUNT_MISSTATED: the registry declares {payload.get('declared_gap_count')!r} gaps, "
            f"holds {len(gaps)}, the ruling names {EXPECTED_GAPS}"
        )

    case_ids = set(payload.get("case_ids") or [])
    disposed = 0
    for gap in gaps:
        for cid in gap.get("affects") or []:
            if cid not in case_ids:
                errors.append(f"DESIGN_GAP_AFFECTS_UNRESOLVED: {gap.get('id')} names {cid!r}, not a case in the set")
        if gap.get("disposition_status") != "NOT_STARTED":
            disposed += 1
            if gap.get("disposed_by") != FOUNDER_ROLE:
                errors.append(
                    f"DESIGN_GAP_DISPOSED_BY_EXECUTION_SIDE: {gap.get('id')} is disposed by "
                    f"{gap.get('disposed_by')!r} — 每个分支都改变题目考什么，执行侧替 Founder 选一支就是自己改自己出的题"
                )
            elif not is_full_commit_hash(gap.get("disposed_at_commit")):
                errors.append(
                    f"DESIGN_GAP_DISPOSED_BY_EXECUTION_SIDE: {gap.get('id')} records no full 40-hex disposal commit"
                )
        intent = gap.get("execution_side_authoring_intent")
        if isinstance(intent, dict):
            if intent.get("evidence_level") != "execution_side_self_report":
                errors.append(
                    f"DESIGN_GAP_INTENT_CLAIMED_AS_FOUNDER_TRUTH: {gap.get('id')} records an authoring intent at "
                    f"evidence_level {intent.get('evidence_level')!r}"
                )
            if intent.get("must_be_confirmed_before_use") is not True:
                errors.append(
                    f"DESIGN_GAP_INTENT_CLAIMED_AS_FOUNDER_TRUTH: {gap.get('id')} does not require Founder "
                    "confirmation before its authoring intent is used to route the disposition"
                )

    if payload.get("declared_gaps_disposed") != disposed:
        errors.append(
            f"DESIGN_GAP_COUNT_MISSTATED: the registry declares {payload.get('declared_gaps_disposed')!r} disposed, "
            f"holds {disposed}"
        )
    if disposed < len(gaps) and payload.get("pack_distribution_status") == "DISTRIBUTED":
        errors.append(
            f"DESIGN_GAP_UNDISPOSED_AT_DISTRIBUTION: {len(gaps) - disposed} gap(s) are undisposed while the pack "
            "is marked DISTRIBUTED — 恢复前必须先处置，不得直接分发"
        )


def _validate_sealed_items(payload: dict, errors: list[str]) -> None:
    """被封各项的真值取自各自真源；越过封存值必须有具名解封裁决。"""
    live = payload.get("live_sealed_values") or {}
    sealed = payload.get("ledger_sealed_values") or {}
    unseal = payload.get("unseal_records") or {}

    for key, sealed_value in sorted(sealed.items()):
        live_value = live.get(key)
        if live_value == sealed_value:
            continue
        record = unseal.get(key)
        if record is None:
            errors.append(
                f"SEALED_ITEM_ADVANCED_WITHOUT_UNSEAL: {key} is {live_value!r} in its source, "
                f"the seal records {sealed_value!r}, and no unseal ruling names it"
            )
            continue
        evidence = founder_ruling_evidence(record.get("ruling_ref"), record.get("clause_path"))
        if not (evidence.get("file_exists") and evidence.get("clause_resolves")):
            errors.append(
                f"UNSEAL_WITHOUT_FOUNDER_RULING: {key} claims an unseal via {record.get('ruling_ref')!r} "
                f"clause {record.get('clause_path')!r}, which does not resolve "
                f"(file_exists={evidence.get('file_exists')}, clause_resolves={evidence.get('clause_resolves')})"
            )


def _validate_suspension_record(payload: dict, errors: list[str]) -> None:
    if payload.get("m2_status") != SUSPENDED:
        errors.append(
            f"SUSPENSION_STATUS_UNBOUND: project_state.m2_status is {payload.get('m2_status')!r}, expected {SUSPENDED!r}"
        )
    if payload.get("ledger_status") != SUSPENDED:
        errors.append(f"SEAL_LEDGER_STALE: the seal ledger carries status {payload.get('ledger_status')!r}")
    evidence = founder_ruling_evidence(
        payload.get("suspension_ruling_ref"), payload.get("suspension_clause_path")
    )
    if not (evidence.get("file_exists") and evidence.get("clause_resolves")):
        errors.append(
            f"SUSPENSION_STATUS_UNBOUND: the suspension cites {payload.get('suspension_ruling_ref')!r} "
            f"clause {payload.get('suspension_clause_path')!r}, which does not resolve "
            f"(file_exists={evidence.get('file_exists')}, clause_resolves={evidence.get('clause_resolves')})"
        )

    for name, value in sorted((payload.get("ledger_hashes") or {}).items()):
        if not is_full_commit_hash(value):
            errors.append(f"SEAL_HASH_NOT_FULL_40: the seal records {name}={value!r}")

    if payload.get("recorded_main_head") != payload.get("live_main_head"):
        errors.append(
            f"SEAL_LEDGER_STALE: the seal records main at {payload.get('recorded_main_head')!r}, "
            f"the repository resolves origin/main to {payload.get('live_main_head')!r}"
        )

    steps = payload.get("restore_steps") or []
    if len(steps) != EXPECTED_RESTORE_STEPS or payload.get("declared_restore_step_count") != len(steps):
        errors.append(
            f"SEAL_RESTORE_SEQUENCE_MISSTATED: the seal declares "
            f"{payload.get('declared_restore_step_count')!r} restore steps, holds {len(steps)}, "
            f"the ruling names {EXPECTED_RESTORE_STEPS}"
        )
    if [s.get("step") for s in steps] != list(range(1, len(steps) + 1)):
        errors.append(f"SEAL_RESTORE_SEQUENCE_MISSTATED: restore steps are numbered {[s.get('step') for s in steps]!r}")
    if payload.get("must_not_assume_count") != EXPECTED_MUST_NOT_ASSUME:
        errors.append(
            f"SEAL_RESTORE_SEQUENCE_MISSTATED: the seal lists "
            f"{payload.get('must_not_assume_count')!r} must-not-assume items, the ruling names {EXPECTED_MUST_NOT_ASSUME}"
        )


def _validate_review_relay(payload: dict, errors: list[str]) -> None:
    ruling_questions = payload.get("ruling_questions") or []
    request_questions = payload.get("request_questions") or []
    transmittal = payload.get("transmittal_text") or ""

    if len(request_questions) != EXPECTED_QUESTIONS or payload.get("declared_question_count") != EXPECTED_QUESTIONS:
        errors.append(
            f"REVIEW_QUESTION_COUNT_MISSTATED: the request declares "
            f"{payload.get('declared_question_count')!r} questions and holds {len(request_questions)}, "
            f"the ruling names {EXPECTED_QUESTIONS}"
        )
    if len(payload.get("request_out_of_scope") or []) != EXPECTED_OUT_OF_SCOPE:
        errors.append(
            f"REVIEW_QUESTION_COUNT_MISSTATED: the request lists "
            f"{len(payload.get('request_out_of_scope') or [])} out-of-scope items, the ruling names {EXPECTED_OUT_OF_SCOPE}"
        )

    by_id = {q.get("id"): q for q in request_questions}
    for question in ruling_questions:
        relayed = by_id.get(question.get("id"))
        if relayed is None:
            errors.append(f"REVIEW_QUESTION_NOT_VERBATIM: the request drops {question.get('id')}")
            continue
        if relayed.get("text") != question.get("text"):
            errors.append(
                f"REVIEW_QUESTION_NOT_VERBATIM: {question.get('id')} was relayed as {relayed.get('text')!r}, "
                f"the ruling writes {question.get('text')!r} — 原样转达不许润色"
            )
        elif question.get("text") not in transmittal:
            errors.append(
                f"REVIEW_QUESTION_NOT_VERBATIM: {question.get('id')} does not appear verbatim in the transmittal document"
            )
    for item in payload.get("ruling_out_of_scope") or []:
        if item not in transmittal:
            errors.append(f"REVIEW_QUESTION_NOT_VERBATIM: out-of-scope item {item!r} is absent from the transmittal")

    received = 0
    for reviewer in payload.get("reviewers") or []:
        if reviewer.get("conclusion_received") or reviewer.get("conclusion") is not None:
            received += 1
            report = reviewer.get("report")
            has_report = isinstance(report, str) and report.strip() != ""
            if not has_report:
                errors.append(
                    f"REVIEW_CONCLUSION_SELF_FILLED: {reviewer.get('role')} carries a conclusion with no report file — "
                    "结论必须由该侧自己给出并落成可读原文"
                )
    if payload.get("declared_conclusions_received") != received:
        errors.append(
            f"REVIEW_CONCLUSION_SELF_FILLED: the request declares "
            f"{payload.get('declared_conclusions_received')!r} conclusions received, holds {received}"
        )
    if not is_full_commit_hash(payload.get("delivery_state_frozen_at")):
        errors.append(
            f"REVIEW_TARGET_HASH_NOT_FULL_40: the request records the frozen delivery state as "
            f"{payload.get('delivery_state_frozen_at')!r}"
        )


def _validate_merge_protocol(payload: dict, errors: list[str]) -> None:
    gates = payload.get("merge_gates") or []
    satisfied = [g for g in gates if g.get("satisfied") is True]
    if payload.get("declared_gates_satisfied") != len(satisfied):
        errors.append(
            f"MERGE_BEFORE_THREE_GATES: the protocol declares {payload.get('declared_gates_satisfied')!r} "
            f"satisfied gates, holds {len(satisfied)}"
        )
    if payload.get("merge_authorized_now") is True and len(satisfied) != len(gates):
        errors.append(
            f"MERGE_BEFORE_THREE_GATES: merge is marked authorized with {len(satisfied)} of {len(gates)} gates satisfied"
        )
    if payload.get("pr_merged") is True and len(satisfied) != len(gates):
        errors.append(f"MERGE_BEFORE_THREE_GATES: PR #3 is recorded merged with {len(satisfied)} of {len(gates)} gates")
    if payload.get("ff_only") is not True or payload.get("command_line_only") is not True:
        errors.append(
            f"MERGE_METHOD_VIOLATED: the protocol records ff_only={payload.get('ff_only')!r}, "
            f"command_line_only={payload.get('command_line_only')!r}"
        )
    if payload.get("tag_applied") is True and payload.get("pr_merged") is not True:
        errors.append("TAG_APPLIED_BEFORE_MERGE_VERIFIED: the M2 suspension tag is applied before the merge landed")
    if payload.get("frozen_observation_entered") is True:
        for commit in payload.get("unregistered_main_commits") or []:
            errors.append(
                f"FUNCTIONAL_COMMIT_ON_FROZEN_MAINLINE: {commit} sits on main after the freeze without a "
                "governance-registration entry"
            )


def validate(payload: dict) -> list[str]:
    errors: list[str] = []
    _validate_pack_seal(payload, errors)
    _validate_design_gaps(payload, errors)
    _validate_sealed_items(payload, errors)
    _validate_suspension_record(payload, errors)
    _validate_review_relay(payload, errors)
    _validate_merge_protocol(payload, errors)
    return errors


def _sha256(path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def collect() -> dict:
    ruling = load_yaml(RULING)
    ledger = load_yaml(SEAL_LEDGER)
    seal = load_yaml(PACK_SEAL)
    gaps_doc = load_yaml(GAPS)
    request = load_yaml(REVIEW_REQUEST)
    protocol = load_yaml(MERGE_PROTOCOL)
    model = load_yaml(ROLE_MODEL)

    pack_root = ROOT / seal["pack_root"]
    live_files = {
        p.relative_to(pack_root).as_posix(): _sha256(p)
        for p in sorted(pack_root.rglob("*"))
        if p.is_file()
    }
    sealed_files = {row["path"]: row["sha256"] for row in seal["files"]}
    digest_input = "".join(f"{row['path']}:{row['sha256']}\n" for row in seal["files"])

    sinks = []
    for side in load_yaml(REVIEW_STATE)["sides"]:
        path = ROOT / side["sink"]
        live = sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip()) if path.exists() else 0
        sinks.append(
            {
                "side_id": side["side_id"],
                "live": live,
                "sealed": seal["review_sinks"]["sealed_record_count_per_side"],
            }
        )

    coverage = load_yaml(COVERAGE_MAP)
    closure = coverage["current_closure_state"]
    thresholds = load_yaml(THRESHOLDS)
    gate = load_yaml(TIMING_GATE)
    hidden = load_yaml(HIDDEN_MANIFEST)
    conditions = {c["condition_id"]: c for c in load_yaml(CONDITION_LEDGER)["conditions"]}
    anchor_conf = load_yaml(ANCHOR_TRUTH)["founder_confirmation"]

    live_sealed_values = {
        "hidden_asset_count": hidden["manifest_state"]["asset_count"],
        "hidden_manifest_status": hidden["status"],
        "cond_011": conditions["COND-011"]["status"],
        "cond_007": conditions["COND-007"]["status"],
        "threshold_metric_count": len(thresholds["items"]),
        "threshold_frozen_count": sum(1 for i in thresholds["items"] if i.get("founder_decision") is not None),
        "timing_gate_precondition_count": gate["preconditions"]["count"],
        "timing_gate_satisfied_count": sum(1 for i in gate["preconditions"]["items"] if i.get("current") is True),
        "founder_confirmation_fields_filled": sum(
            1
            for f in ("confirmed_by", "confirmed_at", "confirmed_at_commit", "ruling_ref", "clause_path")
            if anchor_conf.get(f) is not None
        ),
        "deliverables_ready": closure["ready_count"],
        "deliverables_partial": closure["partial_count"],
        "deliverables_frozen": closure["frozen_count"],
    }
    sealed_block = ledger["sealed_state"]
    ledger_sealed_values = {
        "hidden_asset_count": sealed_block["seal_3_hidden_assets"]["asset_count"],
        "hidden_manifest_status": sealed_block["seal_3_hidden_assets"]["manifest_status"],
        "cond_011": sealed_block["seal_3_hidden_assets"]["cond_011"],
        "cond_007": sealed_block["seal_4_thresholds"]["cond_007"],
        "threshold_metric_count": sealed_block["seal_4_thresholds"]["metric_count"],
        "threshold_frozen_count": sealed_block["seal_4_thresholds"]["frozen_count"],
        "timing_gate_precondition_count": sealed_block["seal_5_timing_gate"]["precondition_count"],
        "timing_gate_satisfied_count": sealed_block["seal_5_timing_gate"]["satisfied_count"],
        "founder_confirmation_fields_filled": sealed_block["seal_5_timing_gate"][
            "founder_confirmation_bound_fields_filled"
        ],
        "deliverables_ready": sealed_block["seal_6_deliverable_matrix"]["ready"],
        "deliverables_partial": sealed_block["seal_6_deliverable_matrix"]["partial"],
        "deliverables_frozen": sealed_block["seal_6_deliverable_matrix"]["frozen"],
    }

    live_main = subprocess.run(
        ["git", "-C", str(ROOT), "rev-parse", "refs/remotes/origin/main"],
        capture_output=True, text=True,
    ).stdout.strip()

    return {
        "m2_status": model["project_state"]["m2_status"],
        "suspension_ruling_ref": model["m2_suspension"]["authority"].split()[0],
        "suspension_clause_path": model["m2_suspension"]["authority"].split()[1],
        "ledger_status": ledger["status"],
        "ledger_hashes": {
            "main": ledger["frozen_hashes"]["main"]["head"],
            "delivery_state": ledger["frozen_hashes"]["candidate"]["delivery_state_frozen_at"],
        },
        "recorded_main_head": ledger["frozen_hashes"]["main"]["head"],
        "live_main_head": live_main,
        "restore_steps": ledger["restore"]["ordered_sequence"],
        "declared_restore_step_count": ledger["restore"]["step_count"],
        "must_not_assume_count": ledger["restore"]["must_not_assume_true_on_restore"]["count"],
        "unseal_records": ledger.get("unseal_records") or {},
        "ledger_sealed_values": ledger_sealed_values,
        "live_sealed_values": live_sealed_values,
        "sealed_pack_files": sealed_files,
        "live_pack_files": live_files,
        "pack_distribution_status": seal["distribution_status"],
        "declared_pack_digest": seal["pack_content_digest"],
        "recomputed_sealed_digest": hashlib.sha256(digest_input.encode("utf-8")).hexdigest(),
        "declared_pack_file_count": seal["file_count"],
        "review_sink_counts": sinks,
        "design_gaps": gaps_doc["gaps"],
        "declared_gap_count": gaps_doc["gap_count"],
        "declared_gaps_disposed": gaps_doc["machine_checkable_fields"]["gaps_disposed"],
        "case_ids": [c["case_id"] for c in load_yaml(CAL)["cases"]],
        "ruling_questions": ruling["article_3_premerge_review"]["review_questions"],
        "ruling_out_of_scope": ruling["article_3_premerge_review"]["out_of_scope"]["items"],
        "request_questions": request["questions"],
        "request_out_of_scope": request["out_of_scope"]["items"],
        "declared_question_count": request["question_count"],
        "declared_conclusions_received": request["machine_checkable_fields"]["conclusions_received"],
        "reviewers": request["reviewers"]["items"],
        "delivery_state_frozen_at": request["review_target"]["delivery_state_frozen_at"],
        "transmittal_text": read_text(REVIEW_TRANSMITTAL),
        "merge_gates": protocol["three_gates"]["items"],
        "declared_gates_satisfied": protocol["three_gates"]["satisfied_count"],
        "merge_authorized_now": protocol["what_this_file_is"]["merge_authorized_now"],
        "ff_only": protocol["merge_method"]["ff_only"],
        "command_line_only": protocol["merge_method"]["command_line_only"],
        "tag_applied": protocol["tag"]["tag_applied"],
        "frozen_observation_entered": protocol["mainline_state_after_merge"]["entered"],
        "unregistered_main_commits": [],
        "pr_merged": ledger["state_flags_at_seal"]["pr_3_merged"],
    }


if __name__ == "__main__":
    cli(LABEL, collect, validate)
