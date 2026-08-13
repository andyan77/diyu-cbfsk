#!/usr/bin/env python3
"""Drive each checker's validate() with literal fixture payloads.

Fixtures never call collect(): their payload is independent literal data, so a bug in the
repository-reading code cannot make a fixture pass, and a bug in validate() cannot hide
behind a payload built by the code under test.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CHECKER_DIR = ROOT / "ci" / "checkers"
FIXTURE_DIR = ROOT / "ci" / "fixtures"
sys.path.insert(0, str(CHECKER_DIR))

_MODULES: dict[str, object] = {}


def load(name: str):
    if name not in _MODULES:
        spec = importlib.util.spec_from_file_location(name, CHECKER_DIR / f"{name}.py")
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        _MODULES[name] = module
    return _MODULES[name]


def run(verbose: bool = True) -> int:
    paths = sorted(FIXTURE_DIR.rglob("*.yaml"))
    if verbose:
        print(f"=== fixtures ({len(paths)}) ===")
    failures = 0
    for path in paths:
        fixture = yaml.safe_load(path.read_text(encoding="utf-8"))
        rel = path.relative_to(ROOT)
        fixture_id = fixture.get("fixture_id", rel.name)
        checker = fixture["checker"]
        expected = fixture["expected"]
        module = load(checker)
        errors = module.validate(fixture["payload"])
        actual = "FAIL" if errors else "PASS"
        if actual != expected:
            failures += 1
            print(f"FAIL fixture {fixture_id} ({checker}): expected {expected}, got {actual}")
            for err in errors:
                print(f"     checker said: {err}")
            if actual == "PASS":
                print("     checker said: <no errors>")
        elif verbose:
            detail = f" [{errors[0]}]" if errors else ""
            print(f"PASS fixture {fixture_id} ({checker}) expected={expected}{detail}")
    if verbose:
        print(f"RESULT fixtures: {len(paths) - failures}/{len(paths)} behaved as declared")
    return failures


if __name__ == "__main__":
    sys.exit(1 if run() else 0)
