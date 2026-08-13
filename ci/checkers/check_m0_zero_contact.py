#!/usr/bin/env python3
"""M0 通过标准第二条：与笛语现有资产零接触，现有 P7C 状态无漂移。

「零接触」不是「不提这些名字」——合同必须能写出 P7C / DIFY / CSO 才能定义边界。判据是接触
的**方向与动作**：本仓不得出现指向笛语现有仓的文件系统路径、不得出现对其状态的写入或调用，
也不得声明已建立外部连接。提及名字并声明禁止，是合规内容；把它写成一条可执行的读写路径，
才是越界。
"""

from __future__ import annotations

import re
import subprocess

import yaml

from _common import ROOT, cli, load_yaml

LABEL = "check_m0_zero_contact"

LEGACY_ASSETS = ("P7C", "Content Kernel", "DIFY", "CSO")

# 指向笛语现有仓/运行时的具体路径或端点形态。命中即为可执行接触，不是叙述。
LEGACY_PATH_PATTERNS = (
    r"~/diyu/[^\s\"']+",
    r"/home/[a-z]+/diyu/[^\s\"']+",
    r"D:\\\\diyu[^\s\"']*",
    r"projects/p7c[^\s\"']*",
    r"content_kernel/[^\s\"']+",
    r"dify_[a-z_]*\.(?:yaml|yml|json)",
)

# 对现有资产的写入/调用动作。
LEGACY_WRITE_ACTION_PATTERNS = (
    r"(?:写入|回灌|覆盖|重写|迁移)\s*(?:到)?\s*(?:P7C|DIFY|CSO|Content Kernel)",
    r"(?:P7C|DIFY|CSO)\s*(?:\.|::)\s*(?:write|update|upsert|delete)",
)

TEXT_SUFFIXES = {".md", ".yaml", ".yml", ".json", ".jsonl", ".py", ".txt", ".toml", ".cfg", ".ini"}

FIXTURE_DIR_PREFIX = "ci/fixtures/"


def validate(payload: dict) -> list[str]:
    errors: list[str] = []

    contract = payload.get("boundary_contract") or {}
    if contract.get("declared") is not True:
        errors.append("ZERO_CONTACT_CONTRACT_MISSING: architecture contract does not declare the decoupling ruling")
    declared_targets = set(contract.get("zero_contact_targets") or [])
    missing = sorted(set(LEGACY_ASSETS) - declared_targets)
    if missing:
        errors.append(f"ZERO_CONTACT_TARGET_MISSING: contract does not cover {missing}")
    if contract.get("allowlist_declared_in_contract") is not True:
        errors.append(
            "ALLOWLIST_NOT_IN_CONTRACT: the boundary-documentation allowlist must live in the contract, not in code"
        )
    if contract.get("declared_contact_count") != 0:
        errors.append(
            f"CONTACT_COUNT_NOT_ZERO: contract declares {contract.get('declared_contact_count')!r} contacts, must be 0"
        )

    for hit in payload.get("legacy_path_hits") or []:
        errors.append(f"LEGACY_ASSET_PATH: {hit['file']} references legacy path {hit['match']!r}")
    for hit in payload.get("legacy_write_hits") or []:
        errors.append(f"LEGACY_ASSET_WRITE_ACTION: {hit['file']} declares a write/call into legacy assets: {hit['match']!r}")

    for integration in payload.get("external_integrations") or []:
        if integration.get("m0_connected") is not False:
            errors.append(
                f"PREMATURE_EXTERNAL_CONNECTION: {integration.get('name')} is marked connected during M0"
            )

    if payload.get("credentials_touched") != 0:
        errors.append(f"CREDENTIAL_EXPOSURE: {payload.get('credentials_touched')!r} credential touches recorded, must be 0")

    return errors


def _is_own_fixture(rel: str, path) -> bool:
    """本 checker 自己的 fixture 描述一次越界，不是越界本身。别的 checker 的 fixture 不享此例外。"""
    if not rel.startswith(FIXTURE_DIR_PREFIX) or path.suffix.lower() not in {".yaml", ".yml"}:
        return False
    try:
        return (yaml.safe_load(path.read_text(encoding="utf-8")) or {}).get("checker") == LABEL
    except yaml.YAMLError:
        return False


def _iter_text_files(allowlist: frozenset[str]):
    # 必须同时含未提交的新文件：只扫 tracked 会让新落盘的越界文件在提交前隐身，
    # 而门禁的意义正是在提交之前拦下它。
    listed = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.splitlines()
    for rel in listed:
        path = ROOT / rel
        if path.suffix.lower() not in TEXT_SUFFIXES or not path.is_file():
            continue
        if rel in allowlist or _is_own_fixture(rel, path):
            continue
        yield rel, path


def collect() -> dict:
    boundary = load_yaml("01_contracts_and_schemas/architecture_and_integration_boundary.v1.0.yaml")
    ruling = boundary.get("decoupling_ruling") or {}
    allowlist = frozenset((ruling.get("boundary_documentation_allowlist") or {}).get("paths") or ())

    path_res = [re.compile(p) for p in LEGACY_PATH_PATTERNS]
    write_res = [re.compile(p) for p in LEGACY_WRITE_ACTION_PATTERNS]

    path_hits, write_hits = [], []
    for rel, path in _iter_text_files(allowlist):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for regex in path_res:
            for match in regex.findall(text):
                path_hits.append({"file": rel, "match": match})
        for regex in write_res:
            for match in regex.findall(text):
                write_hits.append({"file": rel, "match": match})

    return {
        "boundary_contract": {
            "declared": bool(ruling),
            "allowlist_declared_in_contract": bool(allowlist),
            "zero_contact_targets": ruling.get("zero_contact_targets"),
            "declared_contact_count": ruling.get("m0_actual_contact_count"),
        },
        "legacy_path_hits": path_hits,
        "legacy_write_hits": write_hits,
        "external_integrations": boundary.get("external_integrations", {}).get("items"),
        "credentials_touched": (boundary.get("credential_boundary") or {}).get("m0_credentials_touched"),
    }


if __name__ == "__main__":
    cli(LABEL, collect, validate)
