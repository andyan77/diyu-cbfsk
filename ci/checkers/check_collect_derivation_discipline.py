#!/usr/bin/env python3
"""collect() 里不许有写死的事实源——这条通则由机器执行，不靠人记得。

裁决 DIYU-CBFSK-FOUNDER-M2-PREMERGE-REVIEW-001 第五节 B-04-4（永久生效）：

    凡判据用作事实源的字段，必须由 collect() 现场推导；硬编码常量或自述值充当事实源，一律 FAIL。
    全仓横扫同类，逐处整改或登记

为什么要有本判据，而不是横扫一遍就算完：横扫是一次性的，通则是永久的。
本轮之前，仓里同时躺着十处同类缺陷（`unregistered_main_commits: []`、`dry_run_executed: True`、
`prompt_rag_direct_answer_accepted_for_m6: False`、`role_availability: [...]` 等），
每一处都曾经过审查而无人发现——因为读代码的人看到的是一个字段名和一个值，
看不出这个值是**查出来的**还是**写上去的**。两者在报告里长得一模一样。

判法：AST 解析每个 checker 的 collect()，取它 return 的那个字典。
凡取值是纯字面量的键（含先赋给局部名再返回的），一律登记在案，否则 FAIL。
登记不是豁免——登记项必须写明它为什么不是事实源（尺子 / 契约常量），
且 kind 不允许写成 fact_source：没有「合法的硬编码事实源」这种东西。

反自审绿：本判据自己的 collect() 也在扫描范围内，同样不许写死任何事实。
"""

from __future__ import annotations

import ast

from _common import ROOT, cli, load_yaml

LABEL = "check_collect_derivation_discipline"

CHECKER_DIR = ROOT / "ci" / "checkers"
REGISTRY = "governance/gates/collect_literal_registry.v0.1.yaml"

# 登记项只能是这两类。fact_source 不在其中——那正是本判据要消灭的东西。
ALLOWED_KINDS = ("expectation_constant", "contract_vocabulary")


def _is_literal(node: ast.AST) -> bool:
    try:
        ast.literal_eval(node)
        return True
    except (ValueError, SyntaxError, TypeError):
        return False


def _dead_literal_names(fn: ast.FunctionDef) -> dict[str, ast.AST]:
    """collect() 里「赋了一次字面量，之后再没被碰过」的局部名。

    要把死常量和累加器分开。`hits = []` 后面跟着 `hits.append(...)` 是**派生**——
    字面量只是初值，真正的内容是扫出来的。而 `unregistered_main_commits = []` 之后
    除了塞进返回字典再没出现过，那才是写死的事实源。

    判法：恰好一次 Store，且除返回字典里那一次 Load 外没有别的 Load。
    多一次 Load 就说明它被读过、被 append 过、或被传给别人（可能被改），一律不算死常量。
    """
    stores: dict[str, list] = {}
    loads: dict[str, int] = {}
    for node in ast.walk(fn):
        if isinstance(node, ast.Name):
            if isinstance(node.ctx, ast.Store):
                stores.setdefault(node.id, []).append(node)
            elif isinstance(node.ctx, ast.Load):
                loads[node.id] = loads.get(node.id, 0) + 1
    literal_value: dict[str, ast.AST] = {}
    for stmt in ast.walk(fn):
        if isinstance(stmt, ast.Assign) and _is_literal(stmt.value):
            for target in stmt.targets:
                if isinstance(target, ast.Name):
                    literal_value[target.id] = stmt.value
    return {
        name: value
        for name, value in literal_value.items()
        if len(stores.get(name, [])) == 1 and loads.get(name, 0) <= 1
    }


def collect_literals(source: str) -> list[dict]:
    """一个 checker 源码里，collect() 返回字典中取值为写死常量的键。

    两种写法都算：直接写在 return 里的，以及先赋给局部名再返回的——
    后者是同一个缺陷换了个位置，不该因为多了一行赋值就逃掉。
    """
    tree = ast.parse(source)
    found: list[dict] = []
    for node in tree.body:
        if not (isinstance(node, ast.FunctionDef) and node.name == "collect"):
            continue
        dead = _dead_literal_names(node)
        for inner in ast.walk(node):
            if not (isinstance(inner, ast.Return) and isinstance(inner.value, ast.Dict)):
                continue
            for key, value in zip(inner.value.keys, inner.value.values):
                if not isinstance(key, ast.Constant):
                    continue
                if _is_literal(value):
                    found.append({"field": key.value, "expression": ast.unparse(value)[:80], "via": "inline"})
                elif isinstance(value, ast.Name) and value.id in dead:
                    found.append(
                        {
                            "field": key.value,
                            "expression": ast.unparse(dead[value.id])[:80],
                            "via": f"local name {value.id}",
                        }
                    )
    return found


def validate(payload: dict) -> list[str]:
    errors: list[str] = []

    scanned = payload.get("scanned_checkers") or []
    if not scanned:
        errors.append(
            "COLLECT_SCAN_EMPTY: 一个 checker 也没扫到 —— 判据没读到东西不等于没问题"
        )

    registered = {(e.get("checker"), e.get("field")): e for e in payload.get("registered") or []}
    actual = {(row["checker"], row["field"]): row for row in payload.get("literal_sites") or []}

    for key, row in sorted(actual.items()):
        entry = registered.get(key)
        if entry is None:
            errors.append(
                f"HARDCODED_FACT_SOURCE: {row['checker']}.collect() 把 {row['field']!r} 写成字面量 "
                f"{row['expression']}（{row['via']}）—— 事实源必须现场推导；"
                "确属尺子或契约常量的，须登记并说明理由"
            )
            continue
        if entry.get("kind") not in ALLOWED_KINDS:
            errors.append(
                f"COLLECT_LITERAL_KIND_INVALID: {row['checker']}.{row['field']} 登记为 "
                f"{entry.get('kind')!r} —— 只允许 {list(ALLOWED_KINDS)}；没有「合法的硬编码事实源」"
            )
        if not entry.get("why_not_a_fact_source"):
            errors.append(
                f"COLLECT_LITERAL_KIND_INVALID: {row['checker']}.{row['field']} 未写明 why_not_a_fact_source"
            )

    for key, entry in sorted(registered.items()):
        if key not in actual:
            errors.append(
                f"COLLECT_LITERAL_REGISTRY_STALE: 登记册里有 {key[0]}.{key[1]}，源码里已经没有了 —— "
                "整改完必须销号，否则登记册会慢慢变成一张免罪符"
            )

    declared = payload.get("declared_literal_count")
    if declared != len(actual):
        errors.append(
            f"COLLECT_LITERAL_COUNT_MISSTATED: 登记册声明 {declared!r} 处，实扫 {len(actual)} 处"
        )

    return errors


def collect() -> dict:
    registry = load_yaml(REGISTRY)
    sites = []
    scanned = []
    for path in sorted(CHECKER_DIR.glob("check_*.py")):
        scanned.append(path.name)
        for row in collect_literals(path.read_text(encoding="utf-8")):
            sites.append({"checker": path.stem, **row})
    return {
        "scanned_checkers": scanned,
        "literal_sites": sites,
        "registered": registry.get("entries") or [],
        "declared_literal_count": registry.get("literal_site_count"),
    }


if __name__ == "__main__":
    cli(LABEL, collect, validate)
