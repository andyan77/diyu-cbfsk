#!/usr/bin/env python3
"""校准评审启动包：可独立分发、由题库派生、不夹带治理上下文。

启动包要交到两个互相隔离的评审工作面手里，因此守三件事：

  单一真源 —— 包里的题由生成器从公开校准集现场重新派生，与落盘文件逐字节比对。
              手改包里的题会被当场比出来；写两份题就会有两套口径，改一处漏一处。
  分批不重不漏 —— 九批合起来必须正好覆盖 90 例，每例恰好一次。
              少一例是漏评，多一例是同一题被两次计入分歧统计。
  不夹带上下文 —— 里程碑状态、裁决编号、既往结论、另一侧结果一律不得出现在包内。
              评审员知道得越多，分歧率测出来的就越不是他们各自的判断。

反自审绿：题目真值来自公开校准集，不来自包自己的清单；哈希现算，不读 Manifest 的自述。
"""

from __future__ import annotations

import hashlib
import importlib.util
import json

from _common import ROOT, cli, load_yaml

LABEL = "check_calibration_launch_pack"

PACK = "03_m2_evaluation_foundation/calibration/launch_pack"
MANIFEST = f"{PACK}/pack_manifest.yaml"
SOURCE_SET = "03_m2_evaluation_foundation/calibration/public_calibration_set.v0.1.yaml"
REVIEW_STATE = "03_m2_evaluation_foundation/calibration/calibration_review_state.v0.1.yaml"
# Manifest 自身写着黑名单本身，扫它等于扫规则条文；分发内容之外不入扫描面。
SCAN_EXCLUDED = ("pack_manifest.yaml",)

_BUILDER = None


def _builder():
    global _BUILDER
    if _BUILDER is None:
        spec = importlib.util.spec_from_file_location(
            "build_calibration_pack", ROOT / "ci" / "tools" / "build_calibration_pack.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        _BUILDER = module
    return _BUILDER


def validate(payload: dict) -> list[str]:
    errors: list[str] = []

    for rel in payload.get("missing_files") or []:
        errors.append(f"PACK_FILE_MISSING: {rel} is listed in the manifest but absent from the pack")

    for rel in payload.get("derivation_drift") or []:
        errors.append(
            f"PACK_DERIVATION_DRIFT: {rel} differs from re-deriving it out of the calibration set — "
            "启动包是派生物，不是第二份题库"
        )

    for row in payload.get("hash_drift") or []:
        errors.append(
            f"PACK_MANIFEST_HASH_STALE: {row['path']} hashes to {row['actual'][:12]}…, "
            f"the manifest records {row['declared'][:12]}…"
        )

    declared_cases = payload.get("declared_case_count")
    source_ids = payload.get("source_case_ids") or []
    pack_ids = payload.get("pack_case_ids") or []
    if pack_ids != source_ids:
        errors.append(
            f"PACK_CASE_SET_DRIFT: the pack carries {len(pack_ids)} case ids, the calibration set defines "
            f"{len(source_ids)}; first divergence at index "
            f"{next((i for i, (a, b) in enumerate(zip(pack_ids, source_ids)) if a != b), min(len(pack_ids), len(source_ids)))}"
        )
    if declared_cases != len(source_ids):
        errors.append(
            f"PACK_CASE_SET_DRIFT: manifest declares {declared_cases!r} cases, the calibration set defines "
            f"{len(source_ids)}"
        )

    batch_ids = payload.get("batch_case_ids") or []
    flattened = [case_id for batch in batch_ids for case_id in batch]
    if sorted(flattened) != sorted(source_ids):
        errors.append(
            f"PACK_BATCH_PARTITION_BROKEN: batches cover {len(flattened)} case slots for "
            f"{len(source_ids)} cases — 每例必须恰好一次"
        )
    duplicates = sorted({c for c in flattened if flattened.count(c) > 1})
    if duplicates:
        errors.append(f"PACK_BATCH_PARTITION_BROKEN: {duplicates[:5]} appear in more than one batch")
    if payload.get("declared_batch_count") != len(batch_ids):
        errors.append(
            f"PACK_BATCH_PARTITION_BROKEN: manifest declares {payload.get('declared_batch_count')!r} batches, "
            f"the pack holds {len(batch_ids)}"
        )
    size = payload.get("declared_batch_size")
    for index, batch in enumerate(batch_ids, start=1):
        if len(batch) > (size or 0):
            errors.append(
                f"PACK_BATCH_PARTITION_BROKEN: batch {index} holds {len(batch)} cases, the declared size is {size}"
            )

    for hit in payload.get("forbidden_hits") or []:
        errors.append(
            f"PACK_CONTAINS_GOVERNANCE_CONTEXT: {hit['file']} contains {hit['token']!r} — "
            "启动包不得夹带治理上下文、既往结论或另一侧结果"
        )

    if payload.get("manifest_prompt_sha256") != payload.get("state_prompt_sha256"):
        errors.append(
            "PACK_PROMPT_HASH_MISMATCH: the pack manifest and the review-state record disagree on the prompt hash — "
            "评审记录会绑到一份没人读过的正文上"
        )

    return errors


def collect() -> dict:
    manifest = load_yaml(MANIFEST)
    builder = _builder()
    generated = builder.build()

    pack_root = ROOT / PACK
    missing: list[str] = []
    drift: list[str] = []
    for rel, content in generated.items():
        path = pack_root / rel
        if not path.exists():
            missing.append(rel)
            continue
        if path.read_text(encoding="utf-8") != content:
            drift.append(rel)

    hash_drift = []
    for row in manifest["files"]:
        path = pack_root / row["path"]
        if not path.exists():
            missing.append(row["path"])
            continue
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != row["sha256"]:
            hash_drift.append({"path": row["path"], "declared": row["sha256"], "actual": actual})

    cases_path = pack_root / "cases/public_calibration_cases.jsonl"
    pack_ids = [
        json.loads(line)["case_id"]
        for line in cases_path.read_text(encoding="utf-8").splitlines() if line.strip()
    ] if cases_path.exists() else []

    batch_ids = []
    batch_dir = pack_root / "batches"
    if batch_dir.exists():
        for path in sorted(batch_dir.glob("batch_*.jsonl")):
            batch_ids.append(
                [json.loads(line)["case_id"] for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
            )

    tokens = manifest["must_not_contain"]["tokens"]
    forbidden_hits = []
    for path in sorted(pack_root.rglob("*")):
        if not path.is_file() or path.name in SCAN_EXCLUDED:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for token in tokens:
            if token in text:
                forbidden_hits.append({"file": path.relative_to(ROOT).as_posix(), "token": token})

    return {
        "missing_files": sorted(set(missing)),
        "derivation_drift": sorted(drift),
        "hash_drift": hash_drift,
        "declared_case_count": manifest["case_count"],
        "declared_batch_count": manifest["batch_count"],
        "declared_batch_size": manifest["batch_size"],
        "source_case_ids": [c["case_id"] for c in load_yaml(SOURCE_SET)["cases"]],
        "pack_case_ids": pack_ids,
        "batch_case_ids": batch_ids,
        "forbidden_hits": forbidden_hits,
        "manifest_prompt_sha256": manifest["review_prompt"]["sha256"],
        "state_prompt_sha256": load_yaml(REVIEW_STATE)["prompt"]["sha256"],
    }


if __name__ == "__main__":
    cli(LABEL, collect, validate)
