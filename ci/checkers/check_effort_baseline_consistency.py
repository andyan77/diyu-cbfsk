#!/usr/bin/env python3
"""The effort baseline must read identically in the PRD, the canonical role model and the change map.

「自行改变 125—185 人月与 15—24 个月基线」是红线。三处若有任何一处漂移，必须当场暴露，
而不是靠人读三份文件对眼。
"""

from __future__ import annotations

import re

from _common import ROOT, cli, docx_paragraph_texts, load_yaml

LABEL = "check_effort_baseline_consistency"

COMPARED_FIELDS = ("person_months", "duration_months", "effort_unit")
PRD_ANCHOR = "工程量与工期口径（单一Founder模式）"


def validate(payload: dict) -> list[str]:
    errors: list[str] = []
    sources = payload.get("sources") or {}

    missing = [name for name in ("role_operating_model", "prd", "change_map") if name not in sources]
    if missing:
        errors.append(f"MISSING_EFFORT_BASELINE_SOURCE: {missing}")
        return errors

    for field in COMPARED_FIELDS:
        values = {name: (src or {}).get(field) for name, src in sources.items()}
        if any(v in (None, "") for v in values.values()):
            errors.append(f"EFFORT_BASELINE_FIELD_MISSING: {field} -> {values}")
            continue
        if len(set(values.values())) != 1:
            errors.append(f"EFFORT_BASELINE_DRIFT: {field} differs across sources -> {values}")

    for name, src in sources.items():
        if (src or {}).get("staffing_commitment") not in (False, None):
            errors.append(f"STAFFING_COMMITMENT_CLAIMED: {name} states staffing_commitment={src['staffing_commitment']!r}")

    if payload.get("changed_by_this_task") is not False:
        errors.append("EFFORT_BASELINE_CHANGED: this task must not change the 125—185 / 15—24 baseline")

    return errors


def _prd_effort_cell() -> dict:
    for paragraph in docx_paragraph_texts(ROOT / "笛语跨品牌服装搭配专家内核_PRD与执行里程碑_v1.2.docx"):
        if not paragraph.startswith(PRD_ANCHOR):
            continue
        person = re.search(r"(\d+—\d+)人月", paragraph)
        duration = re.search(r"(\d+—\d+)个月", paragraph)
        unit = re.search(r"effort_unit=([A-Z_]+)", paragraph)
        commitment = re.search(r"staffing_commitment=(true|false)", paragraph)
        return {
            "person_months": person.group(1) if person else None,
            "duration_months": duration.group(1) if duration else None,
            "effort_unit": unit.group(1) if unit else None,
            "staffing_commitment": (commitment.group(1) == "true") if commitment else None,
        }
    raise ValueError(f"PRD effort baseline cell not found (anchor: {PRD_ANCHOR})")


def collect() -> dict:
    model = load_yaml("governance/bootstrap/role_operating_model.v0.2.yaml")["current_team"]["effort_baseline"]
    invariants = load_yaml("PRD_v1.2_change_map.yaml")["invariants"]["effort_baseline"]
    return {
        "sources": {
            "role_operating_model": {
                "person_months": model["person_months"],
                "duration_months": model["duration_months"],
                "effort_unit": model["effort_unit"],
                "staffing_commitment": model["staffing_commitment"],
            },
            "prd": _prd_effort_cell(),
            "change_map": {
                "person_months": invariants["person_months"],
                "duration_months": invariants["duration_months"],
                "effort_unit": invariants["effort_unit"],
            },
        },
        "changed_by_this_task": model["changed_by_this_task"],
    }


if __name__ == "__main__":
    cli(LABEL, collect, validate)
