#!/usr/bin/env python3
"""EQ-3 的机器化：每一条错误码都要有一份 expected=FAIL 的夹具真的把它触发出来。

NB-M2-02 起因：check_compliance_ledger 声明了十一条错误码，却一条负例都没有——
它当时唯一那份夹具还把 minimum_items 从 7 压成 2，用两条项目「通过」了七条项目的判据。
把尺子改短再量自己，这种事只靠人读代码发现不了。

本判据的做法是**实跑**：从注册表里的每个 checker 源码取出它声明的错误码，再把仓库里所有
expected=FAIL 的夹具喂给对应 validate()，收集实际吐出来的码，两边取差集。
「声明了但没人触发」的码进差集，要么补夹具，要么进登记册具名挂账——不允许无声存在。

登记册是棘轮：上限等于册子条目数，只能降不能升。新增 checker 必须自带全覆盖，
存量欠账可以慢慢还，但还掉一条就必须从册子里删掉一条（否则判 STALE_COVERAGE_EXEMPTION）。
"""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

import yaml

from _common import ROOT, cli, load_yaml, read_text

LABEL = "check_error_code_fixture_coverage"

REGISTRY = "ci/run_all_checks.py"
FIXTURE_DIR = "ci/fixtures"
LEDGER = "governance/gates/error_code_fixture_coverage_ledger.v0.1.yaml"

# 错误码写在字符串字面量开头：大写下划线标识符、紧跟冒号与一个空格。注释与文档里的裸词不算。
# 本行刻意不写出那个形状的样例——写出来会被自己扫成一条错误码（首次实跑即被本判据自己抓到）。
_CODE = re.compile(r'["\']([A-Z][A-Z0-9_]{3,}): ')
_REGISTERED = re.compile(r'"(check_[a-z0-9_]+)"')


def validate(payload: dict) -> list[str]:
    errors: list[str] = []

    uncovered = {(row["checker"], row["code"]) for row in payload.get("uncovered") or []}
    registered = {(row["checker"], row["code"]) for row in payload.get("ledger_entries") or []}
    declared = {(row["checker"], row["code"]) for row in payload.get("declared") or []}

    for checker, code in sorted(uncovered - registered):
        errors.append(
            f"ERROR_CODE_WITHOUT_FIXTURE: {checker}.{code} is declared but no expected=FAIL fixture "
            "produces it — 补一份负例，或在登记册里具名挂账"
        )
    for checker, code in sorted(registered - uncovered):
        if (checker, code) not in declared:
            errors.append(
                f"EXEMPTION_FOR_UNKNOWN_CODE: the ledger carries {checker}.{code}, which the checker "
                "no longer declares — 码已删，账也要销"
            )
        else:
            errors.append(
                f"STALE_COVERAGE_EXEMPTION: {checker}.{code} now has a fixture but is still on the ledger — "
                "还掉的账必须从册子里删掉，否则上限降不下来"
            )

    cap = payload.get("declared_cap")
    if cap != len(registered):
        errors.append(
            f"COVERAGE_RATCHET_BROKEN: ledger declares a cap of {cap!r} but carries {len(registered)} entries"
        )
    if len(uncovered) > len(registered):
        errors.append(
            f"COVERAGE_RATCHET_BROKEN: {len(uncovered)} uncovered code(s) against {len(registered)} registered"
        )

    if not payload.get("declared"):
        errors.append("ERROR_CODE_SCAN_EMPTY: no error code was scanned at all — 判据没读到东西不等于没问题")
    if not payload.get("fixture_count"):
        errors.append("ERROR_CODE_SCAN_EMPTY: no expected=FAIL fixture was run at all")

    return errors


def _load_module(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "ci" / "checkers" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def collect() -> dict:
    sys.path.insert(0, str(ROOT / "ci" / "checkers"))
    checkers = _REGISTERED.findall(read_text(REGISTRY))

    declared: list[dict] = []
    declared_by_checker: dict[str, set[str]] = {}
    for name in checkers:
        codes = set(_CODE.findall(read_text(f"ci/checkers/{name}.py")))
        declared_by_checker[name] = codes
        declared.extend({"checker": name, "code": code} for code in sorted(codes))

    produced: dict[str, set[str]] = {name: set() for name in checkers}
    fixture_count = 0
    for path in sorted((ROOT / FIXTURE_DIR).rglob("*.yaml")):
        fixture = yaml.safe_load(path.read_text(encoding="utf-8"))
        if fixture.get("expected") != "FAIL":
            continue
        name = fixture["checker"]
        if name not in produced:
            continue
        fixture_count += 1
        for message in _load_module(name).validate(fixture["payload"]):
            produced[name].add(message.split(":")[0])

    uncovered = [
        {"checker": name, "code": code}
        for name in checkers
        for code in sorted(declared_by_checker[name] - produced[name])
    ]

    ledger = load_yaml(LEDGER)
    return {
        "declared": declared,
        "uncovered": uncovered,
        "fixture_count": fixture_count,
        "ledger_entries": ledger.get("entries") or [],
        "declared_cap": ledger.get("max_uncovered_codes"),
    }


if __name__ == "__main__":
    cli(LABEL, collect, validate)
