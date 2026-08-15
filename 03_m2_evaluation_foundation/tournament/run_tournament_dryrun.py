#!/usr/bin/env python3
"""基线锦标赛 dry-run 骨架：四维度并列聚合，确定性可重放。

本骨架**不调用任何模型、不访问网络**。它的作用只有一个：证明 baseline_tournament_contract
里写的四维度记录与聚合口径真的能跑通，而不是只写在合同里没人验证过。

输入是夹具数据（合成，非真实模型输出）；同一输入必须产出字节相同的结果——
不确定的聚合口径没法用来比较两个方案，因为分不清差异来自方案还是来自抖动。

真实基线运行需要 API Key 与实际成本，登记为 OD-M2-01，交 M2 收口时由 Founder 裁决。
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

CONTRACT_DIMENSIONS = ("quality", "cost", "latency", "human_intervention")
SEVERITY_ORDER = ("none", "minor_edit", "rework", "reject")


def _percentile(values: list[int], pct: float) -> int:
    """最近秩百分位。不插值——插值会引入浮点尾差，破坏字节级可重放。"""
    if not values:
        return 0
    ordered = sorted(values)
    rank = max(1, -(-len(ordered) * pct // 100))  # ceil，整数运算
    return ordered[int(rank) - 1]


def aggregate(arm: dict) -> dict:
    items = arm["items"]
    n = len(items)
    if n == 0:
        raise ValueError(f"arm {arm['arm']!r} has no item")

    scores = [i["per_item_score"] for i in items]
    costs = [i["per_item_cost"] for i in items]
    latencies = [i["per_item_latency_ms"] for i in items]

    # 硬门不进平均：一条失败即该臂失败。混进平均分等于允许高分抵消安全违规。
    gate_results: dict[str, str] = {}
    for it in items:
        for gate, verdict in it["hard_gate_results"].items():
            if gate_results.get(gate) != "fail":
                gate_results[gate] = verdict
    any_gate_failed = any(v == "fail" for v in gate_results.values())

    severity_histogram = {s: 0 for s in SEVERITY_ORDER}
    for it in items:
        severity_histogram[it["intervention_severity"]] += 1
    interventions = sum(1 for i in items if i["intervention_required"])

    return {
        "arm": arm["arm"],
        "item_count": n,
        "deterministic_seed": arm["deterministic_seed"],
        "dimensions": {
            "quality": {
                "mean_score": round(sum(scores) / n, 6),
                "min_score": min(scores),
                "max_score": max(scores),
            },
            "cost": {
                "total_cost": round(sum(costs), 6),
                "mean_cost": round(sum(costs) / n, 6),
                "unit": "USD",
            },
            "latency": {
                "mean_ms": round(sum(latencies) / n, 6),
                "p50_ms": _percentile(latencies, 50),
                "p95_ms": _percentile(latencies, 95),
            },
            "human_intervention": {
                "intervention_count": interventions,
                "intervention_rate": round(interventions / n, 6),
                "severity_histogram": severity_histogram,
            },
        },
        "hard_gate_results": dict(sorted(gate_results.items())),
        "arm_failed_by_hard_gate": any_gate_failed,
        # 不合成单一总分：权重就是取舍本身，须待 M2 冻结时 Founder 裁决。
        "composite_score": None,
        "composite_score_note": "四维度并列，不合成总分——权重未经 Founder 冻结前不得排序。",
    }


def run(fixture_dir: pathlib.Path) -> dict:
    arms = []
    for path in sorted(fixture_dir.glob("*.json")):
        arms.append(aggregate(json.loads(path.read_text(encoding="utf-8"))))
    return {
        "run_id": "DRY-RUN-DETERMINISTIC",
        "run_kind": "dry_run",
        "model_api_calls": 0,
        "network_access": False,
        "dimensions_recorded": list(CONTRACT_DIMENSIONS),
        "arms": arms,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixtures", default="ci/fixtures/m2/tournament")
    parser.add_argument("--out", default="-")
    args = parser.parse_args()

    root = pathlib.Path(__file__).resolve().parent.parent.parent
    result = run(root / args.fixtures)
    payload = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.out == "-":
        sys.stdout.write(payload)
    else:
        pathlib.Path(args.out).write_text(payload, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
