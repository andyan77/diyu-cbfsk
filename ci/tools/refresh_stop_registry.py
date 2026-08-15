#!/usr/bin/env python3
"""按实扫结果重建 STOP 码执行力登记册。

册子记的是「每一条被当作 STOP 使用的错误码，是机器会抓、人得判，还是要等运行时才有得抓」。
sites 一栏必须来自实扫——自报路径没人核对，等于册子说它守着哪些位置就守着哪些位置。
NB-M2E5-01 要的就是这条对账。

分类沿用册子已有的判断（human_judgement / future_runtime 是人做的归类，工具不擅自改）；
新出现的码按「现役判据源码里有没有这个字符串」自动定为 machine_checked，找不到的留空待人分类。
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent.parent
REGISTRY = ROOT / "governance/gates/stop_code_enforcement_registry.v0.1.yaml"
CHECKER_DIR = ROOT / "ci" / "checkers"
ROSTER = ROOT / "governance/gates/live_gate_roster.v0.1.yaml"


def load_checker_module():
    sys.path.insert(0, str(CHECKER_DIR))
    spec = importlib.util.spec_from_file_location(
        "check_stop_code_enforcement", CHECKER_DIR / "check_stop_code_enforcement.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["check_stop_code_enforcement"] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    module = load_checker_module()
    payload = module.collect()
    registry = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))

    scanned: dict[str, set[str]] = {}
    for site in payload["sites"]:
        scanned.setdefault(site["code"], set()).add(f"{site['file']}#{site['key']}")

    retired = {r["code"] for r in registry["retired_codes"]}
    known = {e["code"]: e for e in registry["entries"]}
    live = {g["checker"] for g in yaml.safe_load(ROSTER.read_text(encoding="utf-8"))["gates"] if g["status"] == "LIVE"}
    sources = {name: (CHECKER_DIR / f"{name}.py").read_text(encoding="utf-8") for name in live
               if (CHECKER_DIR / f"{name}.py").exists()}

    entries = []
    unclassified = []
    for code in sorted(set(scanned) - retired):
        entry = dict(known.get(code) or {"code": code})
        entry["code"] = code
        entry["sites"] = sorted(scanned[code])
        # 未归类的条目每次都重算一遍：上一轮留空是因为当时没有检测器，
        # 这一轮检测器补上了就该自动升为 machine_checked，不该因为「已经在册」而一直留空。
        if code not in known or known[code].get("enforcement") is None:
            detectors = sorted(name for name, text in sources.items() if code in text)
            if detectors:
                entry["enforcement"] = "machine_checked"
                entry["detectors"] = detectors
            else:
                entry["enforcement"] = None
                entry["detectors"] = []
                unclassified.append(code)
        entries.append({k: entry[k] for k in ("code", "sites", "enforcement", "detectors", "judged_by",
                                              "detectable_when") if k in entry})

    counts = {"total_codes": len(entries)}
    for cls in ("machine_checked", "human_judgement", "future_runtime"):
        counts[cls] = sum(1 for e in entries if e.get("enforcement") == cls)
    registry["entries"] = entries
    registry["counts"] = counts
    REGISTRY.write_text(yaml.safe_dump(registry, allow_unicode=True, sort_keys=False, width=140), encoding="utf-8")

    print(f"stop registry refreshed: {counts}")
    if unclassified:
        print("UNCLASSIFIED (需人工归类): " + ", ".join(unclassified), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
