#!/usr/bin/env python3
"""报告里的计数数字必须追得到某个机器记录字段。

NB-M2E4-03：EP04 报告写 500/350/149，台账实测 523/376/147，而且 500−350≠149。
裁决定的修法不是再抄一遍正确数字，是把连线接上——报告改模板，数字生成时现读台账。

本判据守三件事：

  重渲染一致 —— 模板重渲染的结果必须与落盘报告逐字节相同。
                 台账改了而报告没重渲染，这里当场失败。
  计数必有源 —— 渲染结果里每一个「数字＋计量单位」的出现位置，
                 必须落在某个引用渲染出来的字符区间内。
  例外要列名 —— 确实不是测量值的数字（版本号、条款序号、历史引述里的原始数字）
                 必须逐条登记在白名单里并写明理由；白名单是公开可数的，
                 不是「判据看不见就算过」。

反自审绿：引用的值由渲染器现场读源文件，不读报告自己写了什么。
"""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path

from _common import ROOT, cli, load_yaml

LABEL = "check_report_number_traceability"

REGISTRY = "governance/gates/report_number_binding_registry.v0.1.yaml"

# 计量单位：出现「数字＋这些单位」即视为计数类数字，必须来自引用。
COUNT_UNITS = "项|条|例|份|道|张|格|个|类|批|轮|次|品牌|商品|图像|阶段|处"
COUNT_RE = re.compile(rf"(\d+)\s*(?:{COUNT_UNITS})")

_RENDER = None


def _renderer():
    global _RENDER
    if _RENDER is None:
        spec = importlib.util.spec_from_file_location(
            "render_report", ROOT / "ci" / "tools" / "render_report.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        _RENDER = module
    return _RENDER


def validate(payload: dict) -> list[str]:
    errors: list[str] = []

    reports = payload.get("reports") or []
    if payload.get("declared_report_count") != len(reports):
        errors.append(
            f"REPORT_BINDING_COUNT_MISSTATED: registry declares {payload.get('declared_report_count')!r} reports, "
            f"lists {len(reports)}"
        )

    for report in reports:
        name = report.get("report", "<unnamed>")
        status = report.get("status")
        if status == "legacy_untemplated":
            if not report.get("reason"):
                errors.append(f"LEGACY_REPORT_WITHOUT_REASON: {name} is left untemplated without a stated reason")
            continue
        if status != "templated":
            errors.append(f"REPORT_BINDING_STATUS_INVALID: {name} carries status {status!r}")
            continue

        if not report.get("template_exists"):
            errors.append(f"REPORT_TEMPLATE_MISSING: {name} declares template {report.get('template')!r}, absent")
            continue
        for failure in report.get("ref_errors") or []:
            errors.append(f"REPORT_REF_UNRESOLVED: {name}: {failure}")
        if report.get("ref_errors"):
            continue
        if not report.get("report_exists"):
            errors.append(f"REPORT_TEMPLATE_MISSING: {name} has a template but no rendered report on disk")
            continue
        if report.get("rendered") != report.get("on_disk"):
            errors.append(
                f"REPORT_RENDER_DRIFT: {name} on disk differs from re-rendering its template — "
                "台账变了而报告没重渲染"
            )
            continue
        for hit in report.get("untraced_counts") or []:
            errors.append(
                f"UNTRACED_COUNT_IN_REPORT: {name} states {hit['number']!r} in {hit['context']!r} without a "
                f"machine-record reference"
            )

    for name in payload.get("unregistered_reports") or []:
        errors.append(
            f"REPORT_NOT_REGISTERED: {name} is a delivery report that the number-binding registry does not carry"
        )

    return errors


def _untraced(text: str, spans, allowlist) -> list[dict]:
    covered = [(start, end) for start, end, _ in spans]
    hits = []
    for match in COUNT_RE.finditer(text):
        position = match.start(1)
        if any(start <= position < end for start, end in covered):
            continue
        line_start = text.rfind("\n", 0, match.start()) + 1
        line_end = text.find("\n", match.end())
        line = text[line_start: line_end if line_end != -1 else len(text)]
        allowed = any(
            str(entry.get("number")) == match.group(1) and (entry.get("context_substring") or "") in line
            for entry in allowlist
        )
        if not allowed:
            hits.append({"number": match.group(0), "context": line.strip()[:70]})
    return hits


def collect() -> dict:
    registry = load_yaml(REGISTRY)
    renderer = _renderer()

    reports = []
    for row in registry["reports"]:
        entry = {"report": row["report"], "status": row["status"], "reason": row.get("reason")}
        if row["status"] != "templated":
            reports.append(entry)
            continue
        template_rel = row["template"]
        template_path = ROOT / template_rel
        report_path = ROOT / row["report"]
        entry.update(
            {
                "template": template_rel,
                "template_exists": template_path.exists(),
                "report_exists": report_path.exists(),
                "ref_errors": [],
            }
        )
        if entry["template_exists"]:
            try:
                rendered, spans = renderer.render(template_path.read_text(encoding="utf-8"))
            except renderer.RefError as exc:
                entry["ref_errors"] = [str(exc)]
                reports.append(entry)
                continue
            entry["rendered"] = rendered
            entry["on_disk"] = report_path.read_text(encoding="utf-8") if entry["report_exists"] else None
            entry["untraced_counts"] = _untraced(rendered, spans, row.get("literal_allowlist") or [])
        reports.append(entry)

    registered = {row["report"] for row in registry["reports"]}
    discovered = set()
    for pattern in registry["discovery"]["globs"]:
        for path in ROOT.glob(pattern):
            discovered.add(path.relative_to(ROOT).as_posix())

    return {
        "reports": reports,
        "declared_report_count": registry["report_count"],
        "unregistered_reports": sorted(discovered - registered),
    }


if __name__ == "__main__":
    cli(LABEL, collect, validate)
