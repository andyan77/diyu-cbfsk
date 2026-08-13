#!/usr/bin/env python3
"""用字面量实例驱动 M1 对象 Schema。

与 ci/run_fixtures.py 的分工：那个驱动 checker 的 validate()（判据层），这个驱动 JSON Schema
本身（结构层）。两者都遵守同一条纪律——fixture 的 payload 是字面量，不由被测代码生成，
所以 Schema 写错不可能自己造出「通过」的证据。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_DIR = ROOT / "01_contracts_and_schemas" / "m1_object_model"
FIXTURE_DIR = ROOT / "ci" / "fixtures" / "m1_schema"


def load_store() -> dict:
    store = {}
    for path in sorted(SCHEMA_DIR.glob("*.schema.v0.1.json")):
        schema = json.loads(path.read_text(encoding="utf-8"))
        store[schema["$id"]] = schema
    return store


def run(verbose: bool = True) -> int:
    store = load_store()
    paths = sorted(FIXTURE_DIR.rglob("*.json"))
    if verbose:
        print(f"=== m1 schema fixtures ({len(paths)}) ===")
    failures = 0
    for path in paths:
        fixture = json.loads(path.read_text(encoding="utf-8"))
        schema_id = fixture["schema_id"]
        expected = fixture["expected"]
        if schema_id not in store:
            print(f"FAIL {fixture['fixture_id']}: unknown schema_id {schema_id}")
            failures += 1
            continue
        resolver = jsonschema.RefResolver(base_uri=schema_id, referrer=store[schema_id], store=store)
        validator = jsonschema.Draft7Validator(store[schema_id], resolver=resolver)
        errors = sorted(validator.iter_errors(fixture["instance"]), key=lambda e: list(e.absolute_path))
        actual = "VALID" if not errors else "INVALID"
        if actual == expected:
            detail = "" if actual == "VALID" else f" [{errors[0].message[:90]}]"
            if verbose:
                print(f"PASS {fixture['fixture_id']} ({Path(schema_id).name}) expected={expected}{detail}")
        else:
            failures += 1
            detail = errors[0].message if errors else "<no error raised>"
            print(f"FAIL {fixture['fixture_id']}: expected {expected}, got {actual} — {detail}")
    print(f"RESULT m1 schema fixtures: {len(paths) - failures}/{len(paths)} behaved as declared")
    return failures


if __name__ == "__main__":
    sys.exit(1 if run() else 0)
