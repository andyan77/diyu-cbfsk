#!/usr/bin/env python3
"""RD-M1-02：守 main 的实际状态，不是台账里的声明。

merge_state 是一组声明字段——它说「Founder 许可了合并」，却没有任何东西核对 main 上
**实际**多了哪些提交、那些提交是否被审过。声明式字段永远与自己一致，因此永远为绿。

本判据改用 live git：列出 main 上未被最近一次 Guardian PASS 覆盖的提交
（`git rev-list <guardian_commit>..main`），逐个要求 governance/gates/main_state_coverage.v0.1.yaml
里存在具名追认条目。没有追认即 FAIL。

fail-closed：读不到 git 就判失败，不跳过。「没读到」不等于「没问题」——
跳过会让判据在最需要它的环境里静默失效（E2：退出码不等于业务通过）。

同时守 NB-M1FIX-01：requirements-ci.txt 除 jsonschema 外不得钉 == 版本。
钉版本曾把 CI 全带崩（PyYAML==5.4.1 在 Python 3.11 构建失败），当时靠提交时的人工断言拦住，
仓内没有持久判据——本判据补上这个缺口。
"""

from __future__ import annotations

import re
import subprocess

from _common import ROOT, cli, is_full_commit_hash, load_yaml, read_text

LABEL = "check_m2_main_state_guard"

COVERAGE = "governance/gates/main_state_coverage.v0.1.yaml"
REQUIREMENTS = "requirements-ci.txt"

# NB-M1FIX-01：只有 jsonschema 允许钉版本——它必须停在 3.2.0（只实现到 draft-07，
# 而 M1 的 Schema 正是按 draft-07 写的）。其余一律不钉。
PINNING_ALLOWED_FOR = frozenset({"jsonschema"})
PIN_RE = re.compile(r"^\s*([A-Za-z0-9_.\-]+)\s*==", re.MULTILINE)
REQUIREMENT_LINE_RE = re.compile(r"^\s*([A-Za-z0-9_.\-]+)", re.MULTILINE)


def validate(payload: dict) -> list[str]:
    errors: list[str] = []

    # --- RD-M1-02 ---
    if not payload.get("git_available"):
        errors.append(
            "MAIN_STATE_UNVERIFIABLE: git could not resolve main — fail-closed，"
            "读不到 main 的实际状态时判失败而不是跳过"
        )
    else:
        reviewed = payload.get("last_guardian_reviewed_commit")
        if not is_full_commit_hash(reviewed):
            errors.append(f"GUARDIAN_COVERAGE_UNBOUND: last_guardian_pass.reviewed_commit={reviewed!r}")
        if payload.get("last_guardian_decision") != "PASS":
            errors.append(f"GUARDIAN_COVERAGE_NOT_PASS: decision={payload.get('last_guardian_decision')!r}")
        if not payload.get("reviewed_commit_exists"):
            errors.append(
                f"GUARDIAN_COVERAGE_UNRESOLVABLE: {reviewed!r} does not resolve to an object in this repository"
            )

        ratified = set(payload.get("ratified_commits") or [])
        for commit in payload.get("uncovered_main_commits") or []:
            if commit not in ratified:
                errors.append(
                    f"MAIN_COMMIT_WITHOUT_COVERAGE: {commit} is on main but neither covered by the last "
                    "Guardian PASS nor named in a ratification entry"
                )

        for entry in payload.get("ratification_entries") or []:
            cid = entry.get("commit")
            if not is_full_commit_hash(cid):
                errors.append(f"RATIFICATION_UNBOUND: ratified commit {cid!r} is not a full 40-hex hash")
            if not entry.get("ruling"):
                errors.append(f"RATIFICATION_WITHOUT_RULING: {cid} names no Founder ruling")
            if not entry.get("reason"):
                errors.append(f"RATIFICATION_WITHOUT_REASON: {cid} states no reason")
            if entry.get("sets_precedent") is True:
                errors.append(
                    f"RATIFICATION_SETS_PRECEDENT: {cid} is marked as setting a precedent — "
                    "追认是有界例外，不是常态通道"
                )

        stale = sorted(set(payload.get("ratified_commits") or []) - set(payload.get("known_commits") or []))
        for commit in stale:
            errors.append(f"RATIFICATION_UNRESOLVABLE: {commit} is ratified but does not exist in this repository")

    if payload.get("fail_closed_on_missing_git") is not True:
        errors.append("MAIN_STATE_GUARD_WEAKENED: fail_closed_on_missing_git must stay true")

    # --- NB-M1FIX-01 ---
    if not payload.get("requirements_present"):
        errors.append(f"CI_REQUIREMENTS_MISSING: {REQUIREMENTS} does not exist")
    else:
        for package in payload.get("pinned_packages") or []:
            if package not in PINNING_ALLOWED_FOR:
                errors.append(
                    f"CI_DEPENDENCY_PINNED: {package} is pinned with == in {REQUIREMENTS}; "
                    f"only {sorted(PINNING_ALLOWED_FOR)} may be pinned — "
                    "钉版本曾把 CI 全带崩（PyYAML==5.4.1 在 Python 3.11 构建失败）"
                )
        if "jsonschema" not in (payload.get("pinned_packages") or []):
            errors.append(
                "JSONSCHEMA_NOT_PINNED: jsonschema must stay pinned — 它只实现到 draft-07，"
                "而 M1 的 Schema 正是按 draft-07 写的，装更高版本会让 CI 与本地验的不是同一件事"
            )
        if not payload.get("declared_packages"):
            errors.append(f"CI_REQUIREMENTS_EMPTY: {REQUIREMENTS} declares no package")

    return errors


def _git(*args: str) -> tuple[bool, str]:
    try:
        out = subprocess.run(
            ["git", *args], cwd=ROOT, capture_output=True, text=True, check=True
        ).stdout
        return True, out
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False, ""


def collect() -> dict:
    coverage = load_yaml(COVERAGE)
    guardian = coverage["last_guardian_pass"]
    reviewed = guardian["reviewed_commit"]

    # main 优先取 origin/main；本地无远程引用时回落到本地 main。
    main_ref = None
    for candidate in ("origin/main", "main"):
        ok, out = _git("rev-parse", "--verify", candidate)
        if ok and out.strip():
            main_ref = candidate
            break

    git_available = main_ref is not None
    reviewed_exists = False
    uncovered: list[str] = []
    known: list[str] = []
    if git_available:
        ok, _ = _git("cat-file", "-e", f"{reviewed}^{{commit}}")
        reviewed_exists = ok
        if reviewed_exists:
            ok, out = _git("rev-list", f"{reviewed}..{main_ref}")
            uncovered = [line.strip() for line in out.splitlines() if line.strip()]
        ok, out = _git("rev-list", main_ref)
        known = [line.strip() for line in out.splitlines() if line.strip()]

    entries = [
        {
            "commit": item.get("commit"),
            "ruling": item.get("ruling"),
            "reason": item.get("reason_verbatim"),
            "sets_precedent": item.get("sets_precedent"),
        }
        for item in coverage["ratified_commits"]["items"]
    ]

    requirements_path = ROOT / REQUIREMENTS
    requirements_present = requirements_path.exists()
    pinned: list[str] = []
    declared: list[str] = []
    if requirements_present:
        text = read_text(REQUIREMENTS)
        body = "\n".join(
            line for line in text.splitlines() if line.strip() and not line.strip().startswith("#")
        )
        pinned = PIN_RE.findall(body)
        declared = REQUIREMENT_LINE_RE.findall(body)

    return {
        "git_available": git_available,
        "main_ref": main_ref,
        "last_guardian_reviewed_commit": reviewed,
        "last_guardian_decision": guardian["decision"],
        "reviewed_commit_exists": reviewed_exists,
        "uncovered_main_commits": uncovered,
        "known_commits": known,
        "ratified_commits": [e["commit"] for e in entries],
        "ratification_entries": entries,
        "fail_closed_on_missing_git": coverage["contract"]["fail_closed_on_missing_git"],
        "requirements_present": requirements_present,
        "pinned_packages": pinned,
        "declared_packages": declared,
    }


if __name__ == "__main__":
    cli(LABEL, collect, validate)
