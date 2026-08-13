#!/usr/bin/env python3
"""现役门禁不得被静默摘除或降级（GR-GATE-01）。

在此判据之前，摘掉一个 checker 只需从 ci/run_all_checks.py 的注册表删一行——
没有任何东西会发现。「不得静默降级门禁」当时只是一句承诺。

本判据把承诺变成事实：governance/gates/live_gate_roster.v0.1.yaml 登记当前所有现役门禁，
与注册表**双向**比对。册子写 LIVE 却不在注册表 → 有门禁被摘了；
在注册表却没进册子 → 有门禁没登记。两个方向都判失败，只测一向会漏掉一半。

摘除是独立治理动作：必须先有 Founder 单独授权、册子改 RETIRED 并绑定完整 Commit 哈希，
才允许从注册表移除。授权不得夹带在其他任务里（DIYU-CBFSK-M2-RESUME-AUTHORIZATION-001 OI-01）。
"""

from __future__ import annotations

import re

from _common import ROOT, cli, is_full_commit_hash, load_yaml, read_text

LABEL = "check_m2_gate_retirement_guard"

ROSTER = "governance/gates/live_gate_roster.v0.1.yaml"
REGISTRY = "ci/run_all_checks.py"
CHECKER_DIR = ROOT / "ci" / "checkers"
ALLOWED_STATUSES = frozenset({"LIVE", "RETIRED"})


def validate(payload: dict) -> list[str]:
    errors: list[str] = []

    roster = payload.get("gates") or []
    if not roster:
        errors.append("GATE_ROSTER_EMPTY: the roster records no gate — 空册子守不住任何东西")

    declared_count = payload.get("live_gate_count")
    live = [g for g in roster if g.get("status") == "LIVE"]
    if declared_count != len(live):
        errors.append(
            f"GATE_ROSTER_COUNT_DRIFT: roster declares live_gate_count={declared_count!r} but lists {len(live)}"
        )

    registered = set(payload.get("registered_checkers") or [])
    if not registered:
        errors.append("GATE_REGISTRY_UNREADABLE: no checker was read from the full-suite registry")

    for gate in roster:
        name = gate.get("checker", "<unnamed>")
        status = gate.get("status")
        if status not in ALLOWED_STATUSES:
            errors.append(f"GATE_STATUS_INVALID: {name} has status {status!r}")
            continue
        if status == "LIVE":
            if name not in registered:
                errors.append(
                    f"LIVE_GATE_REMOVED_FROM_SUITE: {name} is rostered LIVE but absent from {REGISTRY} — "
                    "门禁被摘除却没有 Founder 单独授权"
                )
            if not gate.get("implementation_exists", True):
                errors.append(f"LIVE_GATE_IMPLEMENTATION_MISSING: {name} is rostered LIVE but has no module")
        else:
            auth = gate.get("retirement_authorization") or {}
            if not auth:
                errors.append(
                    f"GATE_RETIRED_WITHOUT_AUTHORIZATION: {name} is marked RETIRED with no authorization record"
                )
                continue
            if not auth.get("ruling"):
                errors.append(f"GATE_RETIRED_WITHOUT_AUTHORIZATION: {name} names no Founder ruling")
            if not is_full_commit_hash(auth.get("signature_base_commit")):
                errors.append(
                    f"GATE_RETIREMENT_UNBOUND: {name} retirement_authorization.signature_base_commit="
                    f"{auth.get('signature_base_commit')!r} is not a full commit hash"
                )
            if name in registered:
                errors.append(
                    f"GATE_RETIRED_BUT_STILL_REGISTERED: {name} is marked RETIRED yet still runs in {REGISTRY}"
                )

    rostered = {g.get("checker") for g in roster}
    for name in sorted(registered - rostered):
        errors.append(
            f"GATE_NOT_ROSTERED: {name} runs in the full suite but is absent from {ROSTER} — "
            "没进册子的门禁，日后被摘掉也不会被发现"
        )

    return errors


def collect() -> dict:
    roster = load_yaml(ROSTER)
    registry_source = read_text(REGISTRY)
    block = registry_source.split("CHECKERS = [", 1)[1].split("]", 1)[0]
    registered = re.findall(r'"([a-z0-9_]+)"', block)

    gates = []
    for gate in roster["gates"]:
        gates.append(
            {
                "checker": gate.get("checker"),
                "status": gate.get("status"),
                "retirement_authorization": gate.get("retirement_authorization"),
                "implementation_exists": (CHECKER_DIR / f"{gate.get('checker')}.py").exists(),
            }
        )

    return {
        "gates": gates,
        "live_gate_count": roster["live_gate_count"],
        "registered_checkers": registered,
    }


if __name__ == "__main__":
    cli(LABEL, collect, validate)
