#!/usr/bin/env python3
"""M2 十八项交付闭环：清单读自 Brief，状态读自覆盖矩阵，证据现算。

反自证的关键在 collect()：应交什么由 `m2_evaluation_freeze_brief.md` 第 2 节的表格说了算，
不由覆盖矩阵自述。候选自己声明「我该交这些」再宣布「都交齐了」，是拿考纲和答卷同一支笔写。

四态是合同不是描述词：READY 不等于「文件在」——文件在只排除 ABSENT。因此 READY/FROZEN 的项
一律现算哈希、现查存在性；带 blocker 的项不得声称 READY，反之亦然。
"""

from __future__ import annotations

import re
from pathlib import Path

from _common import ROOT, cli, is_full_commit_hash, load_yaml, read_text, sha256_file

LABEL = "check_m2_deliverable_closure"

BRIEF = "01_contracts_and_schemas/m2_evaluation_freeze_brief.md"
MAP = "03_m2_evaluation_foundation/closure/m2_deliverable_coverage_map.v0.1.yaml"

EXPECTED_COUNT = 18
ALLOWED_STATUS = ("ABSENT", "PARTIAL", "READY", "FROZEN")
SETTLED = ("READY", "FROZEN")

# Brief 第 2 节表格行：| 序号 | 交付物 | 要点 |
_ROW = re.compile(r"^\|\s*(\d+)\s*\|\s*(.+?)\s*\|\s*(.*?)\s*\|\s*$")
_FILENAME = re.compile(r".+\.(yaml|json|md|py)$")


def _brief_deliverables(text: str) -> list[tuple[int, str]]:
    """只取第 2 节那张表；序号必须从 1 连续排到表尾，中断即认为表被改动。"""
    out: list[tuple[int, str]] = []
    for line in text.splitlines():
        m = _ROW.match(line)
        if not m:
            continue
        index = int(m.group(1))
        name = m.group(2).strip().strip("`").strip()
        if index != len(out) + 1:
            continue
        out.append((index, name))
    return out


def _validate_item(item: dict, brief_name: str, errors: list[str]) -> None:
    did = item.get("deliverable_id", "<no id>")
    status = item.get("status")

    if status not in ALLOWED_STATUS:
        errors.append(f"INVALID_DELIVERABLE_STATUS: {did} status={status!r}")
        return

    declared = item.get("canonical_name")
    if declared != brief_name:
        errors.append(
            f"M2_DELIVERABLE_NAME_DRIFT: {did} declares {declared!r}, Brief says {brief_name!r}"
        )

    blockers = item.get("blockers") or []
    if status in SETTLED and blockers:
        errors.append(f"STATUS_CONTRADICTS_BLOCKERS: {did} is {status} but records {len(blockers)} blocker(s)")
    if status not in SETTLED and not blockers:
        errors.append(f"STATUS_CONTRADICTS_BLOCKERS: {did} is {status} but records no blocker")

    artifacts = item.get("equivalent_artifacts") or []
    if not artifacts:
        errors.append(f"READY_WITHOUT_ARTIFACT: {did} names no artifact at all")
    for art in artifacts:
        if not art.get("exists"):
            if status in SETTLED:
                errors.append(f"READY_WITHOUT_ARTIFACT: {did} is {status} but {art['path']} does not exist")
            continue
        if art.get("declared_sha256") != art.get("actual_sha256"):
            errors.append(
                f"EVIDENCE_HASH_STALE: {did} records {art.get('declared_sha256')!r} for {art['path']}, "
                f"file hashes to {art.get('actual_sha256')!r}"
            )

    if item.get("canonical_name_is_filename") and not item.get("canonical_artifact_present"):
        if not item.get("founder_supersession_ruling"):
            errors.append(
                f"SILENT_DELIVERABLE_SUBSTITUTION: {did} ships no artifact named {brief_name!r} "
                "and names no founder_supersession_ruling"
            )

    if status == "FROZEN" and not is_full_commit_hash(item.get("founder_freeze_commit")):
        errors.append(f"FROZEN_WITHOUT_FOUNDER_COMMIT: {did} is FROZEN without a 40-hex founder commit")


def validate(payload: dict) -> list[str]:
    errors: list[str] = []

    brief = payload.get("brief_deliverables") or []
    if len(brief) != EXPECTED_COUNT:
        errors.append(
            f"M2_DELIVERABLE_COUNT_DRIFT: Brief lists {len(brief)} deliverables, must be {EXPECTED_COUNT}"
        )

    items = payload.get("items") or []
    if len(items) != len(brief):
        errors.append(
            f"M2_DELIVERABLE_COUNT_DRIFT: coverage map holds {len(items)} entries, Brief lists {len(brief)}"
        )

    seen: dict[int, str] = {}
    brief_by_index = {i: n for i, n in brief}
    for item in items:
        index = item.get("brief_index")
        did = item.get("deliverable_id", "<no id>")
        if index in seen:
            errors.append(f"M2_DELIVERABLE_INDEX_COLLISION: #{index} claimed by {seen[index]!r} and {did!r}")
        else:
            seen[index] = did
        if index not in brief_by_index:
            errors.append(f"M2_DELIVERABLE_NAME_DRIFT: {did} claims Brief index {index!r}, which the Brief has no row for")
            continue
        _validate_item(item, brief_by_index[index], errors)

    for index, name in brief:
        if index not in seen:
            errors.append(f"M2_DELIVERABLE_COUNT_DRIFT: Brief #{index} {name!r} has no entry in the coverage map")

    settled = [i for i in items if i.get("status") in SETTLED]
    frozen = [i for i in items if i.get("status") == "FROZEN"]

    if payload.get("m2_candidate_formed") and len(settled) != EXPECTED_COUNT:
        errors.append(
            "M2_CANDIDATE_CLAIMED_WITH_INCOMPLETE_DELIVERY: "
            f"m2_candidate_formed is true with only {len(settled)}/{EXPECTED_COUNT} deliverables at READY or better"
        )
    if payload.get("m2_frozen") and len(frozen) != EXPECTED_COUNT:
        errors.append(
            "M2_FROZEN_WITH_UNFROZEN_DELIVERABLE: "
            f"m2_frozen is true with only {len(frozen)}/{EXPECTED_COUNT} deliverables FROZEN"
        )
    if payload.get("founder_signature_eligible") and len(settled) != EXPECTED_COUNT:
        errors.append(
            "M2_CANDIDATE_CLAIMED_WITH_INCOMPLETE_DELIVERY: "
            "founder_signature_eligible is true while deliverables are still incomplete"
        )

    declared = payload.get("declared_counts") or {}
    actual = {
        "ready_count": sum(1 for i in items if i.get("status") == "READY"),
        "partial_count": sum(1 for i in items if i.get("status") == "PARTIAL"),
        "absent_count": sum(1 for i in items if i.get("status") == "ABSENT"),
        "frozen_count": sum(1 for i in items if i.get("status") == "FROZEN"),
    }
    for key, value in actual.items():
        if declared.get(key) != value:
            errors.append(
                f"M2_CLOSURE_COUNT_MISSTATED: map says {key}={declared.get(key)!r}, entries give {value}"
            )
    if declared.get("all_ready") is not (len(settled) == EXPECTED_COUNT):
        errors.append(f"M2_CLOSURE_COUNT_MISSTATED: all_ready={declared.get('all_ready')!r} contradicts the entries")

    return errors


def collect() -> dict:
    brief = _brief_deliverables(read_text(BRIEF))
    data = load_yaml(MAP)

    items = []
    for row in data["items"]:
        artifacts = []
        canonical_present = False
        for rel in row.get("equivalent_artifacts") or []:
            path = ROOT / rel
            exists = path.exists()
            artifacts.append(
                {
                    "path": rel,
                    "exists": exists,
                    "declared_sha256": (row.get("evidence_hashes") or {}).get(rel),
                    "actual_sha256": sha256_file(path) if exists else None,
                }
            )
            if exists and Path(rel).name == row.get("canonical_name"):
                canonical_present = True
        items.append(
            {
                "deliverable_id": row.get("deliverable_id"),
                "brief_index": row.get("brief_index"),
                "canonical_name": row.get("canonical_name"),
                "canonical_name_is_filename": bool(_FILENAME.match(row.get("canonical_name") or "")),
                "canonical_artifact_present": canonical_present,
                "status": row.get("status"),
                "blockers": row.get("blockers") or [],
                "equivalent_artifacts": artifacts,
                "founder_supersession_ruling": row.get("founder_supersession_ruling"),
                "founder_freeze_commit": row.get("founder_freeze_commit"),
            }
        )

    state = data["current_closure_state"]
    project = load_yaml("governance/bootstrap/role_operating_model.v0.2.yaml")["project_state"]
    return {
        "brief_deliverables": brief,
        "items": items,
        "m2_candidate_formed": state.get("m2_candidate_formed"),
        "founder_signature_eligible": state.get("founder_signature_eligible"),
        # m2_frozen 取规范源，不取覆盖矩阵的自述——自述与自述比对永远一致。
        "m2_frozen": project.get("m2_frozen", False),
        "declared_counts": {
            "ready_count": state.get("ready_count"),
            "partial_count": state.get("partial_count"),
            "absent_count": state.get("absent_count"),
            "frozen_count": state.get("frozen_count"),
            "all_ready": state.get("all_ready"),
        },
    }


if __name__ == "__main__":
    cli(LABEL, collect, validate)
