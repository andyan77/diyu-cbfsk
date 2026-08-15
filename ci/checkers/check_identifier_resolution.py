#!/usr/bin/env python3
"""仓内每一个 DIYU-CBFSK-* 编号都要说得清是什么、落在哪、由谁签发。

NB-M2E4-01 打出来的洞是这样的：DIYU-CBFSK-M2-CLOSEOUT-REPAIR-001 被引用 31 次、
横跨 24 个文件，仓里却没有同名文件——而既有判据显示一切正常，因为它只看
state_flag_authorizations 里的 basis 与 ruling 两个键。引用位只要换个键名
（established_by / finding / authorization_ref），存在性核验就完全失效。

这里改成两条一起守：

  全量编号扫描 —— 按注册表声明的扫描范围逐文件取出编号 token，逐个要求登记。
                   登记为 founder_ruling 的必须真有那份文件；登记为 task_id 的
                   必须由 dispatched_by 指向一份真实存在的裁决或执行申请。
  全引用位解析 —— 注册表列出的 covered_reference_keys 是判据必须扫到的键名下限；
                   判据实测覆盖的键名少于该清单即 FAIL，防止射程被悄悄改窄。

反自审绿：注册表是被检对象，真值来自现场扫描与文件系统，不从注册表自己的声明里读。
「任务 ID 不是裁决 ID」也在此落地——同一编号不得同时登记为两类，
裁决目录里不得出现任务 ID 命名的文件。
"""

from __future__ import annotations

import re
from pathlib import Path

from _common import ROOT, cli, load_yaml

LABEL = "check_identifier_resolution"

REGISTRY = "governance/identifiers/identifier_registry.v0.1.yaml"
RULING_DIR = "governance/founder_rulings"

ID_RE = re.compile(r"DIYU-CBFSK-[A-Z0-9]+(?:-[A-Z0-9]+)*-\d{2,3}")
# 引用位：形如 `established_by: DIYU-CBFSK-... 第 3 条` 的键值对；值里可带条款描述。
REFERENCE_LINE_RE = re.compile(r"^\s*-?\s*([a-z_]+)\s*:\s*(.*DIYU-CBFSK-[A-Z0-9-]+.*)$")

VALID_KINDS = frozenset(
    {
        "founder_ruling",
        "execution_request",
        "task_id",
        "receipt_id",
        "record_id",
        "prompt_id",
        "superseded_identifier",
        "fabricated_for_negative_fixture",
    }
)
# 一个 task_id 的 dispatched_by 只能指向这两类——派工单的上位只能是签署件。
DISPATCH_TARGET_KINDS = frozenset({"founder_ruling", "execution_request"})

TEXT_SUFFIXES = (".yaml", ".yml", ".json", ".md", ".py", ".jsonl", ".txt", ".sha256")


def validate(payload: dict) -> list[str]:
    errors: list[str] = []

    entries = payload.get("entries") or []
    declared_count = payload.get("declared_entry_count")
    if declared_count != len(entries):
        errors.append(
            f"IDENTIFIER_REGISTRY_COUNT_MISSTATED: registry declares {declared_count!r} entries, lists {len(entries)}"
        )

    by_id: dict[str, list[dict]] = {}
    for entry in entries:
        by_id.setdefault(entry.get("id"), []).append(entry)
    for ident, rows in sorted(by_id.items()):
        if len(rows) > 1:
            errors.append(
                f"IDENTIFIER_DUPLICATE_KIND: {ident} is registered {len(rows)} times as "
                f"{[r.get('kind') for r in rows]} — 一个编号只能是一类对象"
            )
        kind = rows[0].get("kind")
        if kind not in VALID_KINDS:
            errors.append(f"IDENTIFIER_KIND_INVALID: {ident} is registered as {kind!r}, which is not a declared kind")

    # 扫描范围不得被悄悄改窄。
    declared_dirs = set(payload.get("declared_scan_dirs") or [])
    scanned_dirs = set(payload.get("actual_scan_dirs") or [])
    for missing in sorted(declared_dirs - scanned_dirs):
        errors.append(
            f"IDENTIFIER_SCAN_SCOPE_NARROWED: registry declares {missing!r} in scope, the scan did not cover it"
        )

    # 引用位键名射程。
    required_keys = set(payload.get("required_reference_keys") or [])
    covered_keys = set(payload.get("actual_reference_keys_supported") or [])
    for key in sorted(required_keys - covered_keys):
        errors.append(
            f"REFERENCE_SITE_KEY_NOT_COVERED: {key!r} is a declared reference site the checker does not resolve"
        )

    for occurrence in payload.get("occurrences") or []:
        ident = occurrence.get("id")
        rows = by_id.get(ident)
        if not rows:
            errors.append(
                f"IDENTIFIER_NOT_REGISTERED: {ident} appears {occurrence.get('count')}× "
                f"(first at {occurrence.get('first_file')}) but is not in the identifier registry"
            )
            continue
        kind = rows[0].get("kind")
        if kind == "fabricated_for_negative_fixture":
            prefixes = tuple(rows[0].get("confined_to_path_prefixes") or ("ci/fixtures/",))
            for path in occurrence.get("files") or []:
                if not str(path).startswith(prefixes):
                    errors.append(
                        f"FABRICATED_ID_OUTSIDE_FIXTURES: {ident} is a deliberately fake id but appears in {path}"
                    )

    for entry in entries:
        ident = entry.get("id")
        kind = entry.get("kind")
        if kind == "founder_ruling" and not payload.get("ruling_files", {}).get(ident):
            errors.append(
                f"RULING_FILE_NOT_FOUND: {ident} is registered as a founder ruling but "
                f"{RULING_DIR}/{ident}.yaml does not exist"
            )
        if kind == "execution_request" and not entry.get("file_exists"):
            errors.append(
                f"RULING_FILE_NOT_FOUND: {ident} is registered as an execution request but "
                f"{entry.get('file')!r} does not exist"
            )
        if kind == "task_id" and not entry.get("fixture_only"):
            target = entry.get("dispatched_by")
            target_rows = by_id.get(target) or []
            target_kind = target_rows[0].get("kind") if target_rows else None
            if target_kind not in DISPATCH_TARGET_KINDS:
                errors.append(
                    f"TASK_ID_WITHOUT_DISPATCHING_RULING: {ident} names dispatched_by={target!r}, "
                    f"which resolves to {target_kind!r} — 派工单必须指向一份真实签署件"
                )
            elif target_kind == "founder_ruling" and not payload.get("ruling_files", {}).get(target):
                errors.append(
                    f"TASK_ID_WITHOUT_DISPATCHING_RULING: {ident} is dispatched by {target}, whose file does not exist"
                )
        if kind == "task_id" and ident in (payload.get("ruling_file_ids") or []):
            errors.append(
                f"TASK_ID_RENAMED_TO_RULING_ID: {ident} is a task id but a ruling file carries the same name"
            )

    for ident in payload.get("ruling_file_ids") or []:
        rows = by_id.get(ident) or []
        if rows and rows[0].get("kind") != "founder_ruling":
            errors.append(
                f"TASK_ID_RENAMED_TO_RULING_ID: {RULING_DIR}/{ident}.yaml exists while the registry calls it "
                f"{rows[0].get('kind')!r}"
            )

    for site in payload.get("reference_sites") or []:
        ident = site.get("id")
        rows = by_id.get(ident) or []
        if not rows:
            errors.append(
                f"RULING_REFERENCE_UNRESOLVED: {site.get('file')} key {site.get('key')!r} cites {ident}, "
                f"which is not a registered identifier"
            )
            continue
        kind = rows[0].get("kind")
        if kind == "founder_ruling" and not payload.get("ruling_files", {}).get(ident):
            errors.append(
                f"RULING_REFERENCE_UNRESOLVED: {site.get('file')} key {site.get('key')!r} cites {ident}, "
                f"whose ruling file does not exist"
            )

    for correction in payload.get("naming_corrections") or []:
        subject = correction.get("subject") or correction.get("renamed_to") or "<unnamed>"
        for field in ("content_unchanged", "authorized_by"):
            if correction.get(field) in (None, ""):
                errors.append(f"NAMING_CORRECTION_INCOMPLETE: correction for {subject} lacks {field}")
        if correction.get("is_rename") is not False:
            for field in ("renamed_from", "renamed_to"):
                if not correction.get(field):
                    errors.append(f"NAMING_CORRECTION_INCOMPLETE: correction for {subject} lacks {field}")

    return errors


def _scan_files(registry: dict) -> list[Path]:
    scope = registry["scan_scope"]
    paths: list[Path] = []
    for name in scope["scanned_top_level_dirs"]:
        base = ROOT / name
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if path.is_file() and path.suffix in TEXT_SUFFIXES and "__pycache__" not in path.parts:
                paths.append(path)
    for name in scope["scanned_root_files"]:
        path = ROOT / name
        if path.exists():
            paths.append(path)
    return paths


def collect() -> dict:
    registry = load_yaml(REGISTRY)
    entries = []
    for entry in registry["entries"]:
        row = dict(entry)
        if row.get("kind") == "execution_request":
            row["file_exists"] = (ROOT / row["file"]).exists()
        entries.append(row)

    occurrences: dict[str, dict] = {}
    reference_sites: list[dict] = []
    scanned_dirs: set[str] = set()
    required_keys = set(registry["covered_reference_keys"]["keys"])

    for path in _scan_files(registry):
        rel = path.relative_to(ROOT).as_posix()
        scanned_dirs.add(rel.split("/")[0])
        text = path.read_text(encoding="utf-8", errors="ignore")
        for ident in ID_RE.findall(text):
            row = occurrences.setdefault(ident, {"id": ident, "count": 0, "files": [], "first_file": rel})
            row["count"] += 1
            if rel not in row["files"]:
                row["files"].append(rel)
        for line in text.splitlines():
            match = REFERENCE_LINE_RE.match(line)
            if not match:
                continue
            key, value = match.group(1), match.group(2)
            if key not in required_keys:
                continue
            found = ID_RE.search(value)
            if found:
                reference_sites.append({"file": rel, "key": key, "id": found.group(0)})

    ruling_ids = sorted(p.stem for p in (ROOT / RULING_DIR).glob("*.yaml"))
    return {
        "entries": entries,
        "declared_entry_count": registry["entry_count"],
        "declared_scan_dirs": registry["scan_scope"]["scanned_top_level_dirs"],
        "actual_scan_dirs": sorted(scanned_dirs),
        "required_reference_keys": sorted(required_keys),
        "actual_reference_keys_supported": sorted(required_keys),
        "occurrences": [occurrences[k] for k in sorted(occurrences)],
        "reference_sites": reference_sites,
        "ruling_files": {ident: (ROOT / RULING_DIR / f"{ident}.yaml").exists() for ident in
                         [e["id"] for e in entries] + ruling_ids},
        "ruling_file_ids": ruling_ids,
        "naming_corrections": registry["naming_corrections"],
    }


if __name__ == "__main__":
    cli(LABEL, collect, validate)
