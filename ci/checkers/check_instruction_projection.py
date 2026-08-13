#!/usr/bin/env python3
"""Instruction projections must be byte-identical to what the canonical source compiles to."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from _common import ROOT, cli, load_yaml

LABEL = "check_instruction_projection"

GENERATED_MARKER = "GENERATED FILE — DO NOT EDIT BY HAND."


def validate(payload: dict) -> list[str]:
    errors: list[str] = []

    if payload.get("canonical_source") != "governance/bootstrap/role_operating_model.v0.2.yaml":
        errors.append(f"WRONG_CANONICAL_SOURCE: {payload.get('canonical_source')!r}")
    if payload.get("manual_edit_allowed") is not False:
        errors.append("MANUAL_EDIT_ALLOWED: projections must not be hand-editable by contract")
    if payload.get("drift_tolerance") != 0:
        errors.append(f"DRIFT_TOLERANCE: expected 0, got {payload.get('drift_tolerance')!r}")

    for entry in payload.get("files") or []:
        rel = entry.get("path")
        if not entry.get("exists"):
            errors.append(f"MISSING_PROJECTION: {rel}")
            continue
        if not entry.get("matches_render"):
            errors.append(f"PROJECTION_DRIFT: {rel} differs from the canonical render")
        if not entry.get("has_generated_marker"):
            errors.append(f"MISSING_GENERATED_MARKER: {rel}")

    declared = set(payload.get("declared_files") or [])
    rendered = {e.get("path") for e in payload.get("files") or []}
    if declared != rendered:
        errors.append(
            f"PROJECTION_SET_MISMATCH: declared-only={sorted(declared - rendered)} rendered-only={sorted(rendered - declared)}"
        )
    return errors


def _load_compiler():
    path = ROOT / "ci" / "compile_role_instructions.py"
    spec = importlib.util.spec_from_file_location("compile_role_instructions", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["compile_role_instructions"] = module
    spec.loader.exec_module(module)
    return module


def collect() -> dict:
    model = load_yaml("governance/bootstrap/role_operating_model.v0.2.yaml")
    projection = model["instruction_projection"]
    compiler = _load_compiler()
    rendered = compiler.render_all(compiler.load_model())

    files = []
    for rel, content in sorted(rendered.items()):
        target: Path = ROOT / rel
        exists = target.exists()
        on_disk = target.read_text(encoding="utf-8") if exists else ""
        files.append(
            {
                "path": rel,
                "exists": exists,
                "matches_render": exists and on_disk == content,
                "has_generated_marker": GENERATED_MARKER in on_disk,
            }
        )

    return {
        "canonical_source": projection["canonical_source"],
        "manual_edit_allowed": projection["manual_edit_allowed"],
        "drift_tolerance": projection["drift_tolerance"],
        "declared_files": projection["generated_files"],
        "files": files,
    }


if __name__ == "__main__":
    cli(LABEL, collect, validate)
