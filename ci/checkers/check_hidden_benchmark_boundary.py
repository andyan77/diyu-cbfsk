#!/usr/bin/env python3
"""No hidden benchmark content anywhere in the main repository — working tree or git history."""

from __future__ import annotations

import subprocess

from _common import ROOT, cli, load_yaml

LABEL = "check_hidden_benchmark_boundary"

FORBIDDEN_PATH_FRAGMENTS = [
    "02_benchmarks_hidden/",
    "hidden_benchmark_items",
    "hidden_brand_fact_pack",
    "answer_key",
    "answer_keys",
]
FORBIDDEN_CONTENT_MARKERS = [
    "HIDDEN_BENCHMARK_ITEM",
    "HIDDEN_BRAND_FACT_PACK",
    "ANSWER_KEY:",
    "GOLD_ANSWER_SECRET",
]
TEXT_SUFFIXES = {".md", ".yaml", ".yml", ".json", ".jsonl", ".py", ".txt", ".toml", ".cfg", ".ini"}


def validate(payload: dict) -> list[str]:
    errors: list[str] = []

    if payload.get("main_repository_storage_allowed") is not False:
        errors.append("HIDDEN_STORAGE_IN_MAIN_REPO_ALLOWED: contract must forbid main-repo storage")

    for path in payload.get("forbidden_paths_in_worktree") or []:
        errors.append(f"HIDDEN_ASSET_IN_WORKTREE: {path}")
    for path in payload.get("forbidden_paths_in_git_history") or []:
        errors.append(f"HIDDEN_ASSET_IN_GIT_HISTORY: {path}")
    for hit in payload.get("forbidden_content_hits") or []:
        # 例外只有一种：本 checker 自己的 fixture（ci/fixtures 下且 checker 字段指向本 checker）——
        # 它「描述」违规，不是违规本身。其它任何文件（含别的 checker 的 fixture）命中标记一律 FAIL。
        if hit.get("declared_fixture_for_this_checker") or hit.get("documentation_allowlisted"):
            continue
        errors.append(f"HIDDEN_CONTENT_MARKER: {hit['file']} contains {hit['marker']!r}")

    rename = payload.get("directory_rename") or {}
    if rename.get("to") != "02_benchmark_manifests/":
        errors.append(f"PUBLIC_DIRECTORY_NAME: expected 02_benchmark_manifests/, got {rename.get('to')!r}")
    if payload.get("prd_mentions_old_directory"):
        errors.append("STALE_DIRECTORY_NAME: 02_benchmarks_hidden/ still referenced in the PRD candidate")

    allowed = set(payload.get("main_repository_allowed_artifacts") or [])
    required = {"benchmark_schema", "frozen_manifest", "content_hashes", "runner_interface", "result_summary", "non_secret_metadata"}
    missing = sorted(required - allowed)
    if missing:
        errors.append(f"ALLOWED_ARTIFACT_LIST_INCOMPLETE: missing {missing}")

    if payload.get("any_hidden_asset_touched_by_this_task") is not False:
        errors.append("HIDDEN_ASSET_TOUCHED: this task must not touch hidden assets")

    return errors


def _is_own_fixture(rel: str, text: str) -> bool:
    """True only for a fixture under ci/fixtures whose `checker` field targets this very checker."""
    if not rel.startswith("ci/fixtures/"):
        return False
    try:
        import yaml

        data = yaml.safe_load(text)
    except Exception:  # noqa: BLE001 - malformed fixture is never exempt
        return False
    return isinstance(data, dict) and data.get("checker") == LABEL


def _git(*args: str) -> str:
    try:
        return subprocess.run(
            ["git", *args], cwd=ROOT, capture_output=True, text=True, check=True
        ).stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""


def collect() -> dict:
    contract = load_yaml("governance/storage/hidden_benchmark_storage_contract.yaml")

    tracked = [line for line in _git("ls-files").splitlines() if line]
    history = [line for line in _git("log", "--all", "--pretty=format:", "--name-only").splitlines() if line]

    def hits(paths):
        out = []
        for path in paths:
            lowered = path.lower()
            if any(fragment in lowered for fragment in FORBIDDEN_PATH_FRAGMENTS):
                out.append(path)
        return sorted(set(out))

    allowlist = set(
        contract["ci_enforcement"]["marker_documentation_allowlist"]["paths"]
    )
    content_hits = []
    for rel in tracked:
        path = ROOT / rel
        if path.suffix.lower() not in TEXT_SUFFIXES or not path.exists():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        declared = _is_own_fixture(rel, text)
        for marker in FORBIDDEN_CONTENT_MARKERS:
            if marker in text:
                content_hits.append(
                    {
                        "file": rel,
                        "marker": marker,
                        "declared_fixture_for_this_checker": declared,
                        "documentation_allowlisted": rel in allowlist,
                    }
                )

    from _common import docx_all_text  # local import keeps the module import cost low

    prd = ROOT / "笛语跨品牌服装搭配专家内核_PRD与执行里程碑_v1.2.docx"
    prd_text = docx_all_text(prd) if prd.exists() else ""

    return {
        "main_repository_storage_allowed": contract["main_repository"]["hidden_content_storage_allowed"],
        "main_repository_allowed_artifacts": contract["main_repository"]["allowed_artifacts"],
        "directory_rename": {
            "from": contract["main_repository"]["renamed_from"],
            "to": contract["main_repository"]["public_directory_name"],
        },
        "forbidden_paths_in_worktree": hits(tracked),
        "forbidden_paths_in_git_history": hits(history),
        "forbidden_content_hits": content_hits,
        "prd_mentions_old_directory": "02_benchmarks_hidden" in prd_text,
        "any_hidden_asset_touched_by_this_task": contract["current_state"]["any_hidden_asset_touched_by_this_task"],
    }


if __name__ == "__main__":
    cli(LABEL, collect, validate)
