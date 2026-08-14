#!/usr/bin/env python3
"""被当作 STOP 用的错误码，必须先说清谁来抓它。

NB-M2E4-02 抓到的是一条幽灵：MULTIMODAL_SCOPE_CONFLICT_WITH_D10 无实现、无夹具，
却被写成「未触发」。「未触发」是一句实测结论——没有检测器却报未触发，等于没考试就报及格分。

因此三条一起守：

  逐条分类   —— 每个 STOP 声明位上的码都要登记 enforcement：
                machine_checked / human_judgement / future_runtime，缺一即 FAIL。
  分类可核验 —— machine_checked 必须点名检测器，检测器必须在现役门禁册内 LIVE，
                且码字符串必须真出现在那份判据源码里；非机器类一律不得挂检测器。
  未触发受限 —— 「未触发」只有 machine_checked 的码才配说；其余必须显式标注
                enforcement 与判断人，否则判 PHANTOM_STOP_CODE_DECLARED_NOT_TRIGGERED。

报告一侧另守一条：STOP 表格的每一行都要带上该码的 enforcement 类别，
不得把「人工判断为真」与「判据实测为真」混在同一张没有分栏的表里。
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from _common import ROOT, cli, load_yaml

LABEL = "check_stop_code_enforcement"

REGISTRY = "governance/gates/stop_code_enforcement_registry.v0.1.yaml"
ROSTER = "governance/gates/live_gate_roster.v0.1.yaml"
CHECKER_DIR = ROOT / "ci" / "checkers"
REPORT_DIRS = ("11_reports_and_receipts", "governance/reports")

STOP_KEYS = {
    "failure_state", "stop_condition_evaluated", "stop_condition_not_triggered",
    "stop_condition_if_violated", "stop_condition_id", "stop_id", "single_blocker",
    "current_blocker", "stop_condition_ref",
}
NOT_TRIGGERED_KEY = "stop_condition_not_triggered"
CODE_RE = re.compile(r"^[A-Z][A-Z0-9_]{3,}$")
CODE_IN_TEXT_RE = re.compile(r"\b[A-Z][A-Z0-9_]{3,}\b")
NOT_TRIGGERED_MARKERS = ("未触发", "not triggered", "未命中")
VALID_CLASSES = ("machine_checked", "human_judgement", "future_runtime")
SKIP_DIRS = {".git", "__pycache__", "归档_v1.0", "归档_v1.1", "fixtures"}


def validate(payload: dict) -> list[str]:
    errors: list[str] = []

    entries = payload.get("entries") or []
    declared = payload.get("declared_total") or {}
    if declared.get("total_codes") != len(entries):
        errors.append(
            f"STOP_CODE_REGISTRY_COUNT_MISSTATED: registry declares {declared.get('total_codes')!r} codes, "
            f"lists {len(entries)}"
        )
    by_code = {e.get("code"): e for e in entries}
    for name in VALID_CLASSES:
        actual = sum(1 for e in entries if e.get("enforcement") == name)
        if declared.get(name) != actual:
            errors.append(
                f"STOP_CODE_REGISTRY_COUNT_MISSTATED: registry declares {declared.get(name)!r} {name} codes, "
                f"entries give {actual}"
            )

    live = set(payload.get("live_checkers") or [])
    for entry in entries:
        code = entry.get("code", "<no code>")
        enforcement = entry.get("enforcement")
        detectors = entry.get("detectors") or []
        if enforcement not in VALID_CLASSES:
            errors.append(
                f"STOP_CODE_ENFORCEMENT_UNCLASSIFIED: {code} carries enforcement={enforcement!r}, "
                f"must be one of {list(VALID_CLASSES)}"
            )
            continue
        if enforcement == "machine_checked":
            if not detectors:
                errors.append(f"STOP_CODE_DETECTOR_MISSING: {code} is machine_checked but names no detector")
            for detector in detectors:
                if detector not in live:
                    errors.append(
                        f"STOP_CODE_DETECTOR_NOT_LIVE: {code} names detector {detector!r}, which is not a live gate"
                    )
                elif code not in (payload.get("checker_sources") or {}).get(detector, ""):
                    errors.append(
                        f"STOP_CODE_DETECTOR_MISSING: {code} names {detector!r}, whose source never emits that code"
                    )
        else:
            if detectors:
                errors.append(
                    f"NON_MACHINE_CODE_WITH_DETECTOR: {code} is {enforcement} yet claims detectors {detectors}"
                )
            if enforcement == "human_judgement" and not entry.get("judged_by"):
                errors.append(f"STOP_CODE_ENFORCEMENT_UNCLASSIFIED: {code} is human_judgement without naming a judge")
            if enforcement == "future_runtime" and not entry.get("detectable_when"):
                errors.append(
                    f"STOP_CODE_ENFORCEMENT_UNCLASSIFIED: {code} is future_runtime without saying when it becomes checkable"
                )

    retired = {r.get("code") for r in payload.get("retired_codes") or []}
    for site in payload.get("sites") or []:
        code = site.get("code")
        if code in retired:
            errors.append(
                f"RETIRED_STOP_CODE_STILL_DECLARED: {code} is retired but still declared at "
                f"{site.get('file')}#{site.get('key')}"
            )
            continue
        if code not in by_code:
            errors.append(
                f"STOP_CODE_NOT_REGISTERED: {site.get('file')}#{site.get('key')} uses {code}, "
                f"which the enforcement registry does not carry"
            )

    for claim in payload.get("not_triggered_claims") or []:
        code = claim.get("code")
        entry = by_code.get(code) or {}
        if entry.get("enforcement") == "machine_checked":
            continue
        if claim.get("enforcement") in VALID_CLASSES and claim.get("verified_by"):
            continue
        errors.append(
            f"PHANTOM_STOP_CODE_DECLARED_NOT_TRIGGERED: {claim.get('file')} declares {code} not triggered, "
            f"but it is {entry.get('enforcement', 'unregistered')!r} and the site carries no enforcement annotation"
        )

    for mention in payload.get("report_not_triggered_mentions") or []:
        code = mention.get("code")
        entry = by_code.get(code)
        if entry is None:
            errors.append(
                f"PHANTOM_STOP_CODE_DECLARED_NOT_TRIGGERED: {mention.get('file')} reports {code} as not triggered, "
                f"and that code is not registered at all"
            )
        elif entry.get("enforcement") != "machine_checked":
            errors.append(
                f"PHANTOM_STOP_CODE_DECLARED_NOT_TRIGGERED: {mention.get('file')} reports {code} as not triggered, "
                f"but it is {entry.get('enforcement')!r} — 没有检测器就不许说未触发"
            )

    grandfathered = set(payload.get("grandfathered_reports") or [])
    for row in payload.get("report_table_rows") or []:
        code = row.get("code")
        entry = by_code.get(code)
        if entry is None or row.get("file") in grandfathered:
            continue
        if entry.get("enforcement") not in row.get("row_text", ""):
            errors.append(
                f"STOP_TABLE_NOT_PARTITIONED_BY_ENFORCEMENT: {row.get('file')} lists {code} in a table row that "
                f"does not carry its enforcement class"
            )

    return errors


def _walk(node, rel: str, sites: list[dict], claims: list[dict]) -> None:
    if isinstance(node, dict):
        for key, value in node.items():
            if key in STOP_KEYS and isinstance(value, str) and CODE_RE.match(value):
                sites.append({"file": rel, "key": key, "code": value})
                if key == NOT_TRIGGERED_KEY:
                    claims.append(
                        {
                            "file": rel,
                            "code": value,
                            "enforcement": node.get("enforcement"),
                            "verified_by": node.get("verified_by"),
                        }
                    )
            _walk(value, rel, sites, claims)
    elif isinstance(node, list):
        for value in node:
            _walk(value, rel, sites, claims)


def collect() -> dict:
    registry = load_yaml(REGISTRY)
    roster = load_yaml(ROSTER)

    sites: list[dict] = []
    claims: list[dict] = []
    for path in list(ROOT.rglob("*.yaml")) + list(ROOT.rglob("*.yml")):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        try:
            document = yaml.safe_load(path.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001 — 解析不了的文件由各自的 schema 判据负责
            continue
        _walk(document, path.relative_to(ROOT).as_posix(), sites, claims)

    registered = {e["code"] for e in registry["entries"]}
    retired = {r["code"] for r in registry["retired_codes"]}
    mentions: list[dict] = []
    table_rows: list[dict] = []
    for directory in REPORT_DIRS:
        base = ROOT / directory
        if not base.exists():
            continue
        for path in base.rglob("*.md"):
            rel = path.relative_to(ROOT).as_posix()
            for line in path.read_text(encoding="utf-8").splitlines():
                codes = [c for c in CODE_IN_TEXT_RE.findall(line) if c in registered or c in retired]
                if not codes:
                    continue
                if any(marker in line for marker in NOT_TRIGGERED_MARKERS):
                    for code in codes:
                        mentions.append({"file": rel, "code": code, "line": line.strip()})
                if line.lstrip().startswith("|"):
                    for code in codes:
                        table_rows.append({"file": rel, "code": code, "row_text": line})

    return {
        "entries": registry["entries"],
        "declared_total": registry["counts"],
        "retired_codes": registry["retired_codes"],
        "live_checkers": [g["checker"] for g in roster["gates"] if g["status"] == "LIVE"],
        "checker_sources": {
            p.stem: p.read_text(encoding="utf-8") for p in CHECKER_DIR.glob("check_*.py")
        },
        "sites": sites,
        "not_triggered_claims": claims,
        "report_not_triggered_mentions": mentions,
        "report_table_rows": table_rows,
        "grandfathered_reports": registry["report_presentation_rule"]["grandfathered_reports"],
    }


if __name__ == "__main__":
    cli(LABEL, collect, validate)
