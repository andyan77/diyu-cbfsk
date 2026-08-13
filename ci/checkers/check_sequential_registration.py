#!/usr/bin/env python3
"""顺序登记类编号必须唯一且不跳号，最新一条排在最前。

起因（M2-EP02 受控合并）：README 的授权改写登记用 README-MOD-NN 连续编号，
但 main 与 candidate/m2 两条分支**并行各自分配**，双方都取了 README-MOD-10。
合并时才发现撞号——而在此之前，仓库里没有任何判据在守这套编号。
本 checker 补上这个缺口：撞号、跳号、最新条目没排在最前，三种都判失败。

判据只管编号本身，不管内容：内容是否如实由 check_baseline_hashes 的指纹机制守。

只断言「最新一条排在最前」，不断言整列严格递减：既有 M0 期历史里 README-MOD-01
夹在 05 与 04 之间（纯排版遗留，编号本身既不重复也不跳号）。为这条排版瑕疵去改写
M0 期历史记录，风险大于收益；读者真正依赖的是「第一条是最新的」，那一条已被守住。
"""

from __future__ import annotations

import re

from _common import cli, load_yaml

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

        prefixes = set(registry.get("prefixes") or [])
        if len(prefixes) > 1:
            errors.append(
                f"SEQUENTIAL_REGISTRATION_PREFIX_MIXED: {name} mixes prefixes {sorted(prefixes)} — "
                "同一序列必须同一前缀，否则编号唯一性无从判定"
            )

    return errors


def collect() -> dict:
    manifest = load_yaml(PINNED_BASELINE)

    registries = []
    for candidate in manifest["active_baseline_candidates"]:
        history = candidate.get("authorized_modification_history")
        if not history:
            continue
        numbers, prefixes, malformed = [], [], []
        for entry in history:
            change_id = str(entry.get("change_id", ""))
            match = CHANGE_ID_RE.match(change_id)
            if not match:
                malformed.append(change_id)
                continue
            numbers.append(int(match.group("number")))
            prefixes.append(match.group("prefix"))
        registries.append(
            {
                "registry": f"{PINNED_BASELINE}:{candidate['repository_path']}.authorized_modification_history",
                "numbers": numbers,
                "prefixes": prefixes,
                "malformed_ids": malformed,
            }
        )

    return {"registries": registries}


if __name__ == "__main__":
    cli(LABEL, collect, validate)
