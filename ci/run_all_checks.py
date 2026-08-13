#!/usr/bin/env python3
"""Run every deterministic governance checker and print an itemised PASS/FAIL list.

Exit code 0 only when every checker passes and every fixture behaves as declared.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHECKER_DIR = ROOT / "ci" / "checkers"
sys.path.insert(0, str(CHECKER_DIR))

CHECKERS = [
    "check_execution_uuid",
    "check_baseline_hashes",
    "check_docx_canonical_hashes",
    "check_active_product_truth",
    "check_role_operating_model",
    "check_workspace_attestation",
    "check_task_classification",
    "check_conditional_ledger",
    "check_compliance_ledger",
    "check_hidden_benchmark_boundary",
    "check_external_review_claims",
    "check_m0_fourteen_items",
    "check_project_state",
    "check_effort_baseline_consistency",
    "check_instruction_projection",
    "check_ruling_coverage",
    "check_m0_contract_completeness",
    "check_m0_zero_contact",
    "check_m0_deliverable_closure",
]


def load(name: str):
    spec = importlib.util.spec_from_file_location(name, CHECKER_DIR / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    failures = 0
    print("=== governance checkers ===")
    for name in CHECKERS:
        module = load(name)
        try:
            payload = module.collect()
        except Exception as exc:  # noqa: BLE001
            print(f"FAIL {name}: collect() raised {type(exc).__name__}: {exc}")
            failures += 1
            continue
        errors = module.validate(payload)
        if errors:
            failures += 1
            for err in errors:
                print(f"FAIL {name}: {err}")
        else:
            print(f"PASS {name}")

    print()
    fixtures_module = load_fixture_runner()
    fixture_failures = fixtures_module.run(verbose=True)
    return 1 if (failures or fixture_failures) else 0


def load_fixture_runner():
    spec = importlib.util.spec_from_file_location("run_fixtures", ROOT / "ci" / "run_fixtures.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["run_fixtures"] = module
    spec.loader.exec_module(module)
    return module


if __name__ == "__main__":
    sys.exit(main())
