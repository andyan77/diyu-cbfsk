#!/usr/bin/env python3
"""M2 挂起封存：以机器状态封存，不以意图封存；事实一律现场推导，不读自述。

守六件事：

  包没被动过 —— 校准包逐文件哈希与封存快照现算比对。任一文件变了、或文件集有增删，
                distribution_status 必须是 REQUIRES_RECONFIRMATION，不得仍写 NOT_DISTRIBUTED。
  缺口没被绕过 —— 三条已知设计缺口的处置只能由 Founder 做，且处置记录必须点名：
                哪条缺口、选了哪一支、哪个提交生效。指得出一份裁决不等于那份裁决说的是这件事。
  封存项没自己往前走 —— 被封各项与封存快照逐项比对；越过封存值必须有具名解封裁决，
                且该裁决条款正文必须点名该封存项与新值。
  审查对象只有一个 —— 一轮审查的对象四处全等：报告内声明、审查请求、package ledger、Git。
                占位串一律拒收——写一个看起来像值的字符串，读者与判据都会把它当成已解析。
  审查结论不可自填 —— 记录必须带七个字段，报告文件现场读、sha256 现算，
                并核对报告正文确实点名了该角色、该提交、该结论。Guardian 还要有隔离工作区见证；
                见证缺失即标 unverified，不计入通过证据。
  合并没抢跑 —— 三门未齐备不得合并；标签不得在合并核验通过前打；
                总顾问 BLOCK 未逐条具名回应即置门为真，当场拦下。

反自审绿（本轮 B-04 的教训）：包的真值现算文件字节；被封各项取自各自真源；四问取自裁决原文；
**合并是否发生、标签是否已打、主线上有没有未登记提交，一律由 git 现算**。
上一版这里写着 unregistered_main_commits: []——一个写死的空列表，于是「主线上有没有未登记提交」
这条判据永远回答「没有」，而它当时被当作合规证据引用了。声明式字段永远与自己一致，因此永远为绿。
"""

from __future__ import annotations

import hashlib
import subprocess

import yaml

from _common import ROOT, cli, clause_resolves, founder_ruling_evidence, is_full_commit_hash, load_yaml, read_text

LABEL = "check_m2_suspension_seal"

RULING = "governance/founder_rulings/DIYU-CBFSK-FOUNDER-M2-SUSPENSION-001.yaml"
FIX_RULING = "governance/founder_rulings/DIYU-CBFSK-FOUNDER-M2-PREMERGE-REVIEW-001.yaml"
SEAL_LEDGER = "governance/conditions/m2_seal_ledger.v0.1.yaml"
PACK_SEAL = "03_m2_evaluation_foundation/calibration/launch_pack_seal_manifest.v0.1.yaml"
GAPS = "03_m2_evaluation_foundation/calibration/known_design_gaps.v0.1.yaml"
REVIEW_REQUEST = "governance/reports/m2_premerge_review_request.v0.1.yaml"
REVIEW_TRANSMITTAL = "governance/reports/m2_premerge_review_request.md"
MERGE_PROTOCOL = "governance/conditions/mainline_freeze_and_merge_protocol.v0.1.yaml"
PACKAGE_LEDGER = "governance/receipts/m2_package_commit_ledger.yaml"
ROLE_MODEL = "governance/bootstrap/role_operating_model.v0.2.yaml"
CAL = "03_m2_evaluation_foundation/calibration/public_calibration_set.v0.1.yaml"
COVERAGE_MAP = "03_m2_evaluation_foundation/closure/m2_deliverable_coverage_map.v0.1.yaml"
HIDDEN_MANIFEST = "03_m2_evaluation_foundation/hidden_assets/hidden_asset_manifest.v0.1.yaml"
THRESHOLDS = "03_m2_evaluation_foundation/calibration/threshold_freeze_decision.v0.1.yaml"
TIMING_GATE = "governance/conditions/hidden_generation_timing_gate.v0.1.yaml"
ANCHOR_TRUTH = "03_m2_evaluation_foundation/calibration/founder_boundary_anchor_truth.v0.1.yaml"
REVIEW_STATE = "03_m2_evaluation_foundation/calibration/calibration_review_state.v0.1.yaml"
CONDITION_LEDGER = "governance/conditions/conditional_decision_ledger.yaml"
ARTIFACT_CHANGE = "governance/gates/artifact_change_since_delivery_freeze.v0.1.yaml"
WORKSPACE_DIR = "governance/workspaces"

SUSPENDED = "SUSPENDED_BY_FOUNDER"
PACK_STATUSES = ("NOT_DISTRIBUTED", "REQUIRES_RECONFIRMATION", "DISTRIBUTED")
EXPECTED_GAPS = 3
EXPECTED_QUESTIONS = 4
EXPECTED_OUT_OF_SCOPE = 4
EXPECTED_RESTORE_STEPS = 9
EXPECTED_MUST_NOT_ASSUME = 2
FOUNDER_ROLE = "FOUNDER_PRODUCT_AUTHORITY"
GUARDIAN_ROLE = "CLAUDE_INDEPENDENT_GUARDIAN"

# B-02-1：占位串一律拒收。它们读起来像值，实际上什么也没指。
FORBIDDEN_COMMIT_PLACEHOLDERS = (
    "RESOLVED_AT_REPORT_TIME",
    "PENDING",
    "PENDING_RECOMPUTE",
    "TBD",
    "最新版",
)


def _placeholder_hit(value) -> str | None:
    if not isinstance(value, str):
        return None
    return next((p for p in FORBIDDEN_COMMIT_PLACEHOLDERS if p in value), None)


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


def _validate_authorization_record(
    kind: str, item_id: str, record: dict, required: list[str], errors: list[str]
) -> None:
    """B-03-2 通则：引用裁决作为授权依据者，须证明该条款点名了本次动作。

    分三层：字段齐 → 条款解析得出来 → 条款正文真的点了这一项、这一支、这个提交。
    前两层此前就有，第三层是本轮补的——少了它，随便指一份真实裁决里的任意一条都能开门。
    """
    prefix = "DISPOSITION" if kind == "disposition" else "UNSEAL"

    missing = [f for f in required if record.get(f) in (None, "", [], {})]
    if missing:
        errors.append(
            f"{prefix}_RECORD_FIELD_MISSING: {item_id} 的处置记录缺 {missing} —— "
            "字段不齐就不成其为授权记录"
        )
        return

    if not is_full_commit_hash(record.get("signature_base_commit")):
        errors.append(
            f"{prefix}_RECORD_FIELD_MISSING: {item_id} 的 signature_base_commit="
            f"{record.get('signature_base_commit')!r} 不是完整 40 位哈希"
        )

    if not record.get("clause_resolves"):
        errors.append(
            f"{'UNSEAL_WITHOUT_FOUNDER_RULING' if kind == 'unseal' else 'DISPOSITION_RULING_DOES_NOT_NAME_ITEM'}: "
            f"{item_id} 引用 {record.get('ruling_ref')!r} 条款 {record.get('clause_path')!r}，该条款解析不出来"
        )
        return

    clause_text = record.get("clause_text") or ""
    if str(record.get("affected_item")) not in clause_text:
        errors.append(
            f"{prefix}_RULING_DOES_NOT_NAME_ITEM: {item_id} 的授权条款正文里找不到 "
            f"{record.get('affected_item')!r} —— 有一份裁决不等于那份裁决说的是这件事"
        )
    if kind == "disposition":
        if str(record.get("chosen_branch_id")) not in clause_text:
            errors.append(
                f"DISPOSITION_RULING_DOES_NOT_NAME_BRANCH: {item_id} 的授权条款没点名所选分支 "
                f"{record.get('chosen_branch_id')!r}"
            )
        if str(record.get("signature_base_commit")) not in clause_text:
            errors.append(
                f"DISPOSITION_RULING_DOES_NOT_NAME_COMMIT: {item_id} 的授权条款没点名生效 Commit "
                f"{record.get('signature_base_commit')!r}"
            )
    elif str(record.get("authorized_new_value")) not in clause_text:
        errors.append(
            f"UNSEAL_RULING_DOES_NOT_NAME_ITEM: {item_id} 的解封条款没点名被授权的新值 "
            f"{record.get('authorized_new_value')!r}"
        )


def _validate_design_gaps(payload: dict, errors: list[str]) -> None:
    gaps = payload.get("design_gaps") or []
    required = payload.get("disposition_required_fields") or []

    if payload.get("declared_gap_count") != len(gaps) or len(gaps) != EXPECTED_GAPS:
        errors.append(
            f"DESIGN_GAP_COUNT_MISSTATED: the registry declares {payload.get('declared_gap_count')!r} gaps, "
            f"holds {len(gaps)}, the ruling names {EXPECTED_GAPS}"
        )

    case_ids = set(payload.get("case_ids") or [])
    disposed = 0
    for gap in gaps:
        gap_id = gap.get("id")
        for cid in gap.get("affects") or []:
            if cid not in case_ids:
                errors.append(f"DESIGN_GAP_AFFECTS_UNRESOLVED: {gap_id} names {cid!r}, not a case in the set")
        if gap.get("disposition_status") != "NOT_STARTED":
            disposed += 1
            if gap.get("disposed_by") != FOUNDER_ROLE:
                errors.append(
                    f"DESIGN_GAP_DISPOSED_BY_EXECUTION_SIDE: {gap_id} is disposed by "
                    f"{gap.get('disposed_by')!r} — 每个分支都改变题目考什么，执行侧替 Founder 选一支就是自己改自己出的题"
                )
            elif not is_full_commit_hash(gap.get("disposed_at_commit")):
                errors.append(
                    f"DESIGN_GAP_DISPOSED_BY_EXECUTION_SIDE: {gap_id} records no full 40-hex disposal commit"
                )
            record = gap.get("disposition_record")
            if not isinstance(record, dict):
                errors.append(
                    f"DISPOSITION_RECORD_FIELD_MISSING: {gap_id} 已处置但没有 disposition_record —— "
                    "处置人是自述的，依据必须是可核的"
                )
            else:
                _validate_authorization_record("disposition", gap_id, record, required, errors)
        elif gap.get("disposition_record") is not None:
            errors.append(
                f"DISPOSITION_RECORD_FIELD_MISSING: {gap_id} 未处置却带着 disposition_record —— "
                "没处置就没有授权记录"
            )
        intent = gap.get("execution_side_authoring_intent")
        if isinstance(intent, dict):
            if intent.get("evidence_level") != "execution_side_self_report":
                errors.append(
                    f"DESIGN_GAP_INTENT_CLAIMED_AS_FOUNDER_TRUTH: {gap_id} records an authoring intent at "
                    f"evidence_level {intent.get('evidence_level')!r}"
                )
            if intent.get("must_be_confirmed_before_use") is not True:
                errors.append(
                    f"DESIGN_GAP_INTENT_CLAIMED_AS_FOUNDER_TRUTH: {gap_id} does not require Founder "
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
    required = payload.get("unseal_required_fields") or []

    for key, sealed_value in sorted(sealed.items()):
        live_value = live.get(key)
        if live_value == sealed_value:
            continue
        record = unseal.get(key)
        if not isinstance(record, dict):
            errors.append(
                f"SEALED_ITEM_ADVANCED_WITHOUT_UNSEAL: {key} is {live_value!r} in its source, "
                f"the seal records {sealed_value!r}, and no unseal ruling names it"
            )
            continue
        _validate_authorization_record("unseal", key, record, required, errors)


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


def _validate_review_rounds(payload: dict, errors: list[str]) -> None:
    """B-02 ＋ B-03：审查对象只能有一个值，审查结论不能自填。"""
    rounds = payload.get("review_rounds") or []
    required = payload.get("review_record_required_fields") or []
    live_head = payload.get("live_head")
    ledger_by_commit = payload.get("ledger_commits") or {}
    attestations = payload.get("guardian_workspace_attestations") or []

    if not rounds:
        errors.append("REVIEW_TARGET_MISMATCH: the request records no review round at all")

    for rnd in rounds:
        rid = rnd.get("round_id", "<no id>")
        target = rnd.get("target_commit")
        concluded = rnd.get("status") == "CONCLUDED"

        hit = _placeholder_hit(target)
        if hit:
            errors.append(
                f"REVIEW_TARGET_PLACEHOLDER_USED: {rid} 的 target_commit 写着占位串 {hit!r} —— "
                "禁用 RESOLVED_AT_REPORT_TIME 之类占位；写不进自己就留空并声明推导方式"
            )
            continue

        if concluded:
            if not is_full_commit_hash(target):
                errors.append(
                    f"REVIEW_TARGET_HASH_NOT_FULL_40: {rid} 已结束，其审查对象 {target!r} 不是完整 40 位哈希"
                )
                continue
            if not rnd.get("target_is_ancestor_of_head"):
                errors.append(
                    f"REVIEW_TARGET_MISMATCH: {rid} 审过的 {target} 不在本分支现有历史上"
                    f"（HEAD={live_head}）—— 审过的东西必须还在线上"
                )
            if target not in ledger_by_commit:
                errors.append(
                    f"REVIEW_TARGET_MISMATCH: {rid} 的对象 {target} 在 package ledger 里没有对应条目"
                )
        else:
            if target is not None:
                errors.append(
                    f"REVIEW_TARGET_MISMATCH: {rid} 尚未结束却存了 target_commit={target!r} —— "
                    "待审那一轮的对象由 git 现算，存下来的那一刻就开始过期"
                )
            if rnd.get("target_commit_binding") != "derived_from_git_head":
                errors.append(
                    f"REVIEW_TARGET_MISMATCH: {rid} 未声明 target_commit_binding=derived_from_git_head"
                )

        records = rnd.get("records") or []
        if rnd.get("declared_conclusions_received") != len(records):
            errors.append(
                f"REVIEW_CONCLUSION_SELF_FILLED: {rid} 声称收到 "
                f"{rnd.get('declared_conclusions_received')!r} 份结论，实际登记 {len(records)} 份"
            )

        for record in records:
            role = record.get("reviewer_role", "<no role>")
            label = f"{rid}/{role}"

            missing = [f for f in required if record.get(f) in (None, "", [], {})]
            if missing:
                errors.append(f"REVIEW_RECORD_FIELD_MISSING: {label} 缺字段 {missing}")
                continue

            hit = _placeholder_hit(record.get("report_sha256"))
            if hit:
                errors.append(
                    f"REVIEW_REPORT_HASH_STALE: {label} 的 report_sha256 写着占位串 {hit!r} —— "
                    "哈希要么算出来，要么承认没有报告"
                )
            elif not record.get("report_exists"):
                errors.append(
                    f"REVIEW_REPORT_HASH_STALE: {label} 指向 {record.get('report_path')!r}，该文件不存在"
                )
            elif record.get("report_sha256") != record.get("report_actual_sha256"):
                errors.append(
                    f"REVIEW_REPORT_HASH_STALE: {label} 记录 {str(record.get('report_sha256'))[:12]}…，"
                    f"文件现算 {str(record.get('report_actual_sha256'))[:12]}…"
                )

            if record.get("reviewed_commit") != target and concluded:
                errors.append(
                    f"REVIEW_TARGET_MISMATCH: {label} 的 reviewed_commit={record.get('reviewed_commit')!r} "
                    f"与本轮对象 {target!r} 不等"
                )

            if record.get("report_exists"):
                if not record.get("claim_names_role"):
                    errors.append(
                        f"REVIEW_REPORT_DOES_NOT_NAME_ITS_CLAIM: {label} 的证据载体没点名该角色"
                    )
                if not record.get("claim_names_conclusion"):
                    errors.append(
                        f"REVIEW_REPORT_DOES_NOT_NAME_ITS_CLAIM: {label} 的证据载体没点名结论 "
                        f"{record.get('conclusion')!r}"
                    )
                if not record.get("report_names_commit"):
                    errors.append(
                        f"REVIEW_REPORT_DOES_NOT_NAME_ITS_CLAIM: {label} 的证据载体没点名被审提交 "
                        f"{record.get('reviewed_commit')!r}"
                    )

            if record.get("evidence_kind") == "founder_ruling_transcription":
                if record.get("reviewer_authored_fulltext_landed") is not False:
                    errors.append(
                        f"REVIEW_CONCLUSION_SELF_FILLED: {label} 是裁决转录，却声称评审方原文已落盘"
                    )
                if record.get("counts_as_independent_verification") is not False:
                    errors.append(
                        f"REVIEW_CONCLUSION_SELF_FILLED: {label} 是裁决转录，不得计入独立核验证据"
                    )

            if role == GUARDIAN_ROLE:
                attested = any(
                    a.get("role") == GUARDIAN_ROLE and a.get("base_commit") == record.get("reviewed_commit")
                    for a in attestations
                )
                if record.get("workspace_attested") is not attested:
                    errors.append(
                        f"GUARDIAN_WORKSPACE_UNATTESTED: {label} 记录 workspace_attested="
                        f"{record.get('workspace_attested')!r}，而 {WORKSPACE_DIR} 下"
                        f"{'有' if attested else '没有'}对应见证 —— 自述与实测不符"
                    )
                elif not attested and record.get("counts_as_independent_verification") is not False:
                    errors.append(
                        f"GUARDIAN_WORKSPACE_UNATTESTED: {label} 无隔离工作区见证，"
                        "却被计入通过证据 —— 确认不了的标 unverified"
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

    for commit in payload.get("unregistered_main_commits") or []:
        errors.append(
            f"FUNCTIONAL_COMMIT_ON_FROZEN_MAINLINE: {commit['commit']} sits on main after the freeze and touches "
            f"{commit['forbidden_paths']} — 冻结后只收治理登记与裁决落盘"
        )

    # RR-3（永久生效）：BLOCK 未被逐条具名回应就置门为真，当场拦下。
    override = payload.get("advisor_block_override") or {}
    blocking = override.get("outstanding_blocking_findings") or []
    if blocking and override.get("gate_2_satisfied") is True:
        responses = override.get("itemised_response") or []
        answered = {r.get("finding_id") for r in responses if isinstance(r, dict)}
        unanswered = sorted(set(blocking) - answered)
        if unanswered:
            errors.append(
                f"ADVISOR_BLOCK_OVERRIDDEN_WITHOUT_ITEMISED_RESPONSE: GATE-2 置真，但阻断发现 "
                f"{unanswered} 没有逐条具名回应 —— 不得以「已收到顾问意见，故三门齐备」带过"
            )


def _validate_artifact_change(payload: dict, errors: list[str]) -> None:
    """B-01：「自 a4be75e 起零字节改动」被撤销后，取而代之的必须是可复算的清单与分类。

    绝对表述（零、全部、任何、从未）只要有一个反例就整句失效。所以这里不再问「改了没有」，
    只问三件事：改了哪些（清单与 git 现算全等）、其中哪些是交付物（按前缀分类）、
    那几处是不是真的没动语义（逐条写明，不许留空）。
    """
    change = payload.get("artifact_change") or {}

    declared = sorted(change.get("declared_changed") or [])
    actual = sorted(change.get("actual_changed") or [])
    if declared != actual:
        missing = sorted(set(actual) - set(declared))
        extra = sorted(set(declared) - set(actual))
        errors.append(
            f"CHANGED_FILE_LIST_MISSTATED: 台账清单与 git 现算不符 —— 漏记 {missing}，多记 {extra}"
        )
    if change.get("declared_changed_count") != len(actual):
        errors.append(
            f"CHANGED_FILE_LIST_MISSTATED: 台账声明 {change.get('declared_changed_count')!r} 处既有文件被改，"
            f"git 现算 {len(actual)} 处"
        )

    declared_delivery = {row.get("path"): row for row in change.get("declared_delivery_artifacts") or []}
    actual_delivery = sorted(change.get("actual_delivery_artifacts") or [])
    if change.get("declared_delivery_count") != len(actual_delivery):
        errors.append(
            f"DELIVERY_ARTIFACT_SEMANTICS_CHANGED: 台账声明 {change.get('declared_delivery_count')!r} 份交付物被改，"
            f"git 现算 {len(actual_delivery)} 份"
        )
    for path in actual_delivery:
        row = declared_delivery.get(path)
        if row is None:
            errors.append(
                f"DELIVERY_ARTIFACT_SEMANTICS_CHANGED: 交付物 {path} 的字节变了，台账里没有它的逐条说明 —— "
                "交付物被改必须写明改的是什么以及为什么不是语义变更"
            )
            continue
        if row.get("semantics_changed") is not False:
            errors.append(
                f"DELIVERY_ARTIFACT_SEMANTICS_CHANGED: {path} 记录 semantics_changed="
                f"{row.get('semantics_changed')!r} —— 交付语义变了就不是记账更新"
            )
        if not row.get("why_not_semantics"):
            errors.append(
                f"DELIVERY_ARTIFACT_SEMANTICS_CHANGED: {path} 未写明 why_not_semantics"
            )
    for path in sorted(set(declared_delivery) - set(actual_delivery)):
        errors.append(
            f"CHANGED_FILE_LIST_MISSTATED: 台账里 {path} 记为被改的交付物，git 现算它没变"
        )

    for hit in change.get("absolute_claim_hits") or []:
        errors.append(
            f"ABSOLUTE_UNCHANGED_CLAIM_PRESENT: {hit['file']} 仍写着 {hit['phrase']!r} —— "
            "该类绝对表述已由裁决 B-01-1 全部撤销"
        )


def validate(payload: dict) -> list[str]:
    errors: list[str] = []
    _validate_artifact_change(payload, errors)
    _validate_pack_seal(payload, errors)
    _validate_design_gaps(payload, errors)
    _validate_sealed_items(payload, errors)
    _validate_suspension_record(payload, errors)
    _validate_review_relay(payload, errors)
    _validate_review_rounds(payload, errors)
    _validate_merge_protocol(payload, errors)
    return errors


def _sha256(path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git(*args: str):
    """git 现场推导。读不到就返回 None——不吞成 0，也不假装成空。"""
    try:
        done = subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True)
    except FileNotFoundError:
        return None
    return done.stdout.strip() if done.returncode == 0 else None


def _is_ancestor(a: str, b: str) -> bool:
    if not (a and b):
        return False
    done = subprocess.run(
        ["git", "-C", str(ROOT), "merge-base", "--is-ancestor", a, b], capture_output=True, text=True
    )
    return done.returncode == 0


def _authorization_record(record: dict | None) -> dict | None:
    """把一条授权记录连同它引用条款的**正文**一起取出来，交给 validate 判。

    正文是关键：只解析出「条款存在」不足以证明它说的是眼前这件事。
    """
    if not isinstance(record, dict):
        return record
    out = dict(record)
    evidence = clause_resolves(record.get("ruling_file"), record.get("clause_path"))
    out["clause_resolves"] = bool(evidence.get("file_exists") and evidence.get("clause_resolves"))
    clause_text = ""
    if out["clause_resolves"]:
        node = yaml.safe_load((ROOT / record["ruling_file"]).read_text(encoding="utf-8"))
        for key in str(record["clause_path"]).split("."):
            node = node[key]
        clause_text = yaml.safe_dump(node, allow_unicode=True, sort_keys=False)
    out["clause_text"] = clause_text
    return out


def _review_record(record: dict, ruling_text_cache: dict) -> dict:
    out = dict(record)
    path = record.get("report_path")
    full = ROOT / path if path else None
    exists = bool(full and full.exists())
    out["report_exists"] = exists
    out["report_actual_sha256"] = _sha256(full) if exists else None

    report_text = ""
    if exists:
        report_text = ruling_text_cache.setdefault(path, full.read_text(encoding="utf-8"))

    # 证据载体里「这一条」的正文：给了条款路径就取那一节，没给就取全文。
    claim_text = report_text
    clause_path = record.get("evidence_clause_path")
    if exists and clause_path and path.endswith((".yaml", ".yml")):
        node = yaml.safe_load(report_text)
        try:
            for key in str(clause_path).split("."):
                node = node[key]
            claim_text = yaml.safe_dump(node, allow_unicode=True, sort_keys=False)
        except (KeyError, TypeError):
            claim_text = ""

    out["claim_names_role"] = str(record.get("reviewer_role")) in claim_text
    out["claim_names_conclusion"] = str(record.get("conclusion")) in claim_text
    out["report_names_commit"] = str(record.get("reviewed_commit")) in report_text
    return out


def _frozen_mainline_commits(protocol: dict, candidate_head: str, origin_main: str) -> list[dict]:
    """冻结点之后 main 上的功能性提交——现场从 git 列出来并按路径分类。

    B-04：此前这里是写死的 []。合并尚未发生时，冻结尚未开始，列表为空是**推导出来的**结论
    （rev-list 跑了，范围为空），不是常量。
    """
    if not (candidate_head and origin_main):
        return []
    if not _is_ancestor(candidate_head, origin_main):
        return []  # 未合并 → 冻结未开始 → 本分类不适用
    allowed = tuple((protocol.get("frozen_mainline_classification") or {}).get("allowed_paths") or [])
    listed = _git("rev-list", f"{candidate_head}..{origin_main}") or ""
    out = []
    for commit in [c for c in listed.splitlines() if c.strip()]:
        files = (_git("show", "--pretty=format:", "--name-only", commit) or "").splitlines()
        forbidden = sorted({f for f in files if f.strip() and not f.startswith(allowed)})
        if forbidden:
            out.append({"commit": commit, "forbidden_paths": forbidden})
    return out


def _artifact_change_payload() -> dict:
    """自交付态冻结点以来「既有文件被改」的清单——git 现算，不读台账自述。

    比的是**工作树**而不是 HEAD：判据要在两个时点都跑得对——提交前的断言门（工作树是候选内容）
    与提交后的 CI（工作树等于 HEAD）。拿 HEAD 比会在提交那一刻突然换一套答案。
    """
    ledger = load_yaml(ARTIFACT_CHANGE)
    freeze = ledger["freeze_point"]["commit"]
    prefixes = tuple(ledger["classification_rule"]["delivery_artifact_prefixes"])

    listed = _git("diff", "--name-status", freeze) or ""
    actual = []
    for line in listed.splitlines():
        parts = line.split("\t")
        if len(parts) >= 2 and parts[0].startswith(("M", "D")):
            actual.append(parts[-1])

    scan = ledger["absolute_claim_scan"]
    phrases = scan["phrases"]
    exclusions = set(scan["exclusions"])
    directory_exclusions = tuple(scan.get("directory_exclusions") or ())
    extensions = tuple(scan["scan_extensions"])
    hits = []
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or path.suffix not in extensions or ".git" in path.parts:
            continue
        rel = path.relative_to(ROOT).as_posix()
        if rel in exclusions or rel.startswith(directory_exclusions):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for phrase in phrases:
            if phrase in text:
                hits.append({"file": rel, "phrase": phrase})

    return {
        "declared_changed": [row["path"] for row in ledger["changed_existing_m2_files"]["items"] or []],
        "declared_changed_count": ledger["changed_existing_m2_files"]["count"],
        "actual_changed": sorted(actual),
        "declared_delivery_artifacts": ledger["changed_delivery_artifacts"]["items"] or [],
        "declared_delivery_count": ledger["changed_delivery_artifacts"]["count"],
        "actual_delivery_artifacts": sorted(p for p in actual if p.startswith(prefixes)),
        "absolute_claim_hits": hits,
    }


def collect() -> dict:
    ruling = load_yaml(RULING)
    ledger = load_yaml(SEAL_LEDGER)
    seal = load_yaml(PACK_SEAL)
    gaps_doc = load_yaml(GAPS)
    request = load_yaml(REVIEW_REQUEST)
    protocol = load_yaml(MERGE_PROTOCOL)
    model = load_yaml(ROLE_MODEL)
    package_ledger = load_yaml(PACKAGE_LEDGER)

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

    # ---- B-04：合并、标签、主线提交一律 git 现算 ----
    live_head = _git("rev-parse", "HEAD")
    live_main = _git("rev-parse", "refs/remotes/origin/main")
    tag_pattern = (protocol.get("tag") or {}).get("tag_name_pattern") or "m2-suspension-point"
    tags = (_git("tag", "--list", f"{tag_pattern}*") or "").split()
    pr_merged = _is_ancestor(live_head, live_main) if (live_head and live_main) else False

    # ---- B-02 / B-03：审查轮次 ----
    ledger_commits = {
        e["candidate_commit"]: e for e in package_ledger["entries"] if e.get("candidate_commit")
    }
    text_cache: dict = {}
    rounds = []
    for rnd in (request.get("review_rounds") or {}).get("items") or []:
        target = rnd.get("target_commit")
        rounds.append(
            {
                "round_id": rnd.get("round_id"),
                "status": rnd.get("status"),
                "target_commit": target,
                "target_commit_binding": rnd.get("target_commit_binding"),
                "target_is_ancestor_of_head": _is_ancestor(target, live_head) if target else False,
                "declared_conclusions_received": rnd.get("conclusions_received"),
                "records": [_review_record(r, text_cache) for r in rnd.get("records") or []],
            }
        )

    attestations = []
    for path in sorted((ROOT / WORKSPACE_DIR).glob("workspace_attestation.*.yaml")):
        if path.name.endswith("schema.yaml"):
            continue
        doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        for record in doc.get("records") or []:
            attestations.append({"role": record.get("role"), "base_commit": record.get("base_commit")})

    advisor_block = []
    for rnd in (request.get("review_rounds") or {}).get("items") or []:
        for record in rnd.get("records") or []:
            if record.get("conclusion") == "BLOCK":
                advisor_block = list(record.get("blocking_findings") or [])
    gates = protocol["three_gates"]["items"]
    gate_2 = next((g for g in gates if g.get("id") == "GATE-2"), {})

    return {
        "artifact_change": _artifact_change_payload(),
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
        "live_head": live_head,
        "restore_steps": ledger["restore"]["ordered_sequence"],
        "declared_restore_step_count": ledger["restore"]["step_count"],
        "must_not_assume_count": ledger["restore"]["must_not_assume_true_on_restore"]["count"],
        "unseal_records": {
            k: _authorization_record(v) for k, v in ((ledger["unseal"].get("records") or {}) or {}).items()
        },
        "unseal_required_fields": ledger["unseal"]["record_contract"]["required_fields"],
        "ledger_sealed_values": ledger_sealed_values,
        "live_sealed_values": live_sealed_values,
        "sealed_pack_files": sealed_files,
        "live_pack_files": live_files,
        "pack_distribution_status": seal["distribution_status"],
        "declared_pack_digest": seal["pack_content_digest"],
        "recomputed_sealed_digest": hashlib.sha256(digest_input.encode("utf-8")).hexdigest(),
        "declared_pack_file_count": seal["file_count"],
        "review_sink_counts": sinks,
        "design_gaps": [
            {**g, "disposition_record": _authorization_record(g.get("disposition_record"))}
            for g in gaps_doc["gaps"]
        ],
        "disposition_required_fields": gaps_doc["disposition_record_contract"]["required_fields"],
        "declared_gap_count": gaps_doc["gap_count"],
        "declared_gaps_disposed": gaps_doc["machine_checkable_fields"]["gaps_disposed"],
        "case_ids": [c["case_id"] for c in load_yaml(CAL)["cases"]],
        "ruling_questions": ruling["article_3_premerge_review"]["review_questions"],
        "ruling_out_of_scope": ruling["article_3_premerge_review"]["out_of_scope"]["items"],
        "request_questions": request["questions"],
        "request_out_of_scope": request["out_of_scope"]["items"],
        "declared_question_count": request["question_count"],
        "review_rounds": rounds,
        "review_record_required_fields": request["review_record_contract"]["required_fields"],
        "ledger_commits": ledger_commits,
        "guardian_workspace_attestations": attestations,
        "transmittal_text": read_text(REVIEW_TRANSMITTAL),
        "merge_gates": gates,
        "declared_gates_satisfied": protocol["three_gates"]["satisfied_count"],
        "merge_authorized_now": protocol["what_this_file_is"]["merge_authorized_now"],
        "ff_only": protocol["merge_method"]["ff_only"],
        "command_line_only": protocol["merge_method"]["command_line_only"],
        "tag_applied": bool(tags),
        "pr_merged": pr_merged,
        "frozen_observation_entered": pr_merged,
        "unregistered_main_commits": _frozen_mainline_commits(protocol, live_head, live_main),
        "advisor_block_override": {
            "outstanding_blocking_findings": advisor_block,
            "gate_2_satisfied": gate_2.get("satisfied"),
            "itemised_response": (protocol.get("advisor_block_override") or {}).get("itemised_response"),
        },
    }


if __name__ == "__main__":
    cli(LABEL, collect, validate)
