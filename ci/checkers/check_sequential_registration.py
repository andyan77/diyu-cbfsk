#!/usr/bin/env python3
"""顺序登记类编号必须唯一且不跳号，最新一条排在最前。

起因（M2-EP02 受控合并）：README 的授权改写登记用 README-MOD-NN 连续编号，
但 main 与 candidate/m2 两条分支**并行各自分配**，双方都取了 README-MOD-10。
合并时才发现撞号——而在此之前，仓库里没有任何判据在守这套编号。
本 checker 补上这个缺口：撞号、跳号、最新条目没排在最前，三种都判失败。

判据只管编号本身与它指向哪个提交，不管内容改得对不对：内容是否如实由 check_baseline_hashes 守。

NB-M2-04 补入 landed_in_commit：原先 12 条写的是 M1_EP03_CLOSEOUT_COMMIT 这类符号名，
解析不到任何一个对象——「最新版」被禁的理由对它同样成立。现在要求逐条给完整 40 位哈希，
并现场取出该提交的 README 与登记的 binary_sha256 比对；只有最新一条允许自指，
因为它落地的那个提交在写它的时候还不存在，但必须显式声明 self_reference_limitation。

只断言「最新一条排在最前」，不断言整列严格递减：既有 M0 期历史里 README-MOD-01
夹在 05 与 04 之间（纯排版遗留，编号本身既不重复也不跳号）。为这条排版瑕疵去改写
M0 期历史记录，风险大于收益；读者真正依赖的是「第一条是最新的」，那一条已被守住。
"""

from __future__ import annotations

import re

import subprocess

from _common import ROOT, cli, is_full_commit_hash, load_yaml, sha256_text

LABEL = "check_sequential_registration"

PINNED_BASELINE = "governance/baseline/founder_pinned_baseline.v0.1.yaml"
CHANGE_ID_RE = re.compile(r"^(?P<prefix>[A-Z0-9-]+?)-(?P<number>\d+)$")


def validate(payload: dict) -> list[str]:
    errors: list[str] = []

    registries = payload.get("registries") or []
    if not registries:
        errors.append(
            "SEQUENTIAL_REGISTRY_NOT_FOUND: no sequential registry was read — "
            "判据没读到东西不等于没问题"
        )

    for registry in registries:
        name = registry.get("registry", "<unnamed>")
        numbers = registry.get("numbers") or []
        if not numbers:
            errors.append(f"SEQUENTIAL_REGISTRY_EMPTY: {name} has no numbered entry")
            continue

        seen: dict[int, int] = {}
        for number in numbers:
            seen[number] = seen.get(number, 0) + 1
        duplicates = sorted(n for n, count in seen.items() if count > 1)
        if duplicates:
            errors.append(
                f"SEQUENTIAL_REGISTRATION_DUPLICATE: {name} assigns {duplicates} more than once — "
                "两条分支并行分配同一个号即属此类，合并时必须重编为下一个空号"
            )

        expected = set(range(1, max(numbers) + 1))
        missing = sorted(expected - set(numbers))
        if missing:
            errors.append(
                f"SEQUENTIAL_REGISTRATION_GAP: {name} skips {missing} — 跳号会让读者以为有条目被删掉了"
            )

        if numbers[0] != max(numbers):
            errors.append(
                f"SEQUENTIAL_REGISTRATION_NEWEST_NOT_FIRST: {name} starts with {numbers[0]}, "
                f"newest is {max(numbers)} — 读者默认第一条是最新的，排错位会读出过期状态"
            )

        malformed = registry.get("malformed_ids") or []
        for bad in malformed:
            errors.append(f"SEQUENTIAL_REGISTRATION_MALFORMED_ID: {name} entry {bad!r} has no numeric suffix")

        for entry in registry.get("entries") or []:
            cid = entry.get("change_id", "<no id>")
            if entry.get("is_newest") and entry.get("self_referential"):
                if not entry.get("self_reference_limitation"):
                    errors.append(
                        f"SELF_REFERENCE_UNDECLARED: {name} entry {cid} lands in the commit that creates it "
                        "but declares no self_reference_limitation"
                    )
                continue
            if not entry.get("landed_commit_is_full_hash"):
                errors.append(
                    f"LANDED_COMMIT_NOT_RESOLVED: {name} entry {cid} records "
                    f"{entry.get('landed_in_commit')!r}, which is not a 40-hex commit — "
                    "符号名和「最新版」一样解析不到唯一对象"
                )
                continue
            if entry.get("landed_commit_blob_sha256") != entry.get("binary_sha256"):
                errors.append(
                    f"LANDED_COMMIT_BLOB_MISMATCH: {name} entry {cid} points at "
                    f"{entry.get('landed_in_commit')}, whose {entry.get('tracked_path')} hashes to "
                    f"{entry.get('landed_commit_blob_sha256')!r}, not the registered "
                    f"{entry.get('binary_sha256')!r}"
                )

        prefixes = set(registry.get("prefixes") or [])
        if len(prefixes) > 1:
            errors.append(
                f"SEQUENTIAL_REGISTRATION_PREFIX_MIXED: {name} mixes prefixes {sorted(prefixes)} — "
                "同一序列必须同一前缀，否则编号唯一性无从判定"
            )

    return errors


def _blob_sha256(commit: str, rel: str) -> str | None:
    """取出该提交下的文件内容现算哈希；取不到就返回 None，由 validate 判失败（fail-closed）。"""
    try:
        data = subprocess.run(
            ["git", "show", f"{commit}:{rel}"],
            cwd=ROOT, capture_output=True, check=True,
        ).stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    return sha256_text(data.decode("utf-8"))


def collect() -> dict:
    manifest = load_yaml(PINNED_BASELINE)

    registries = []
    for candidate in manifest["active_baseline_candidates"]:
        history = candidate.get("authorized_modification_history")
        if not history:
            continue
        tracked = candidate["repository_path"]
        numbers, prefixes, malformed, entries = [], [], [], []
        for position, entry in enumerate(history):
            change_id = str(entry.get("change_id", ""))
            match = CHANGE_ID_RE.match(change_id)
            if not match:
                malformed.append(change_id)
                continue
            numbers.append(int(match.group("number")))
            prefixes.append(match.group("prefix"))

            landed = entry.get("landed_in_commit")
            full = is_full_commit_hash(landed)
            entries.append(
                {
                    "change_id": change_id,
                    "is_newest": position == 0,
                    "self_referential": bool(entry.get("self_referential")),
                    "self_reference_limitation": entry.get("self_reference_limitation"),
                    "landed_in_commit": landed,
                    "landed_commit_is_full_hash": full,
                    "tracked_path": tracked,
                    "binary_sha256": entry.get("binary_sha256"),
                    "landed_commit_blob_sha256": _blob_sha256(landed, tracked) if full else None,
                }
            )
        registries.append(
            {
                "registry": f"{PINNED_BASELINE}:{tracked}.authorized_modification_history",
                "numbers": numbers,
                "prefixes": prefixes,
                "malformed_ids": malformed,
                "entries": entries,
            }
        )

    return {"registries": registries}


if __name__ == "__main__":
    cli(LABEL, collect, validate)
