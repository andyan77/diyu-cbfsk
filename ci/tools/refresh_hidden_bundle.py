#!/usr/bin/env python3
"""重算隐藏生成输入包的文件哈希、分类计数与内容摘要。

输入包是「隐藏侧照着哪一版公开蓝图出题」的唯一凭据。任何一份输入文件改了字节，
包就必须整体重算——否则隐藏侧按旧版出的题，考的不是现在这套标准，事后还查不出是哪一条变了。

本工具只做重算，不做判断。判断在 ci/checkers/check_m2_hidden_generation_readiness.py：
它现算每份文件的哈希与本包声称的值比对，对不上即 HIDDEN_INPUT_BUNDLE_STALE。

bundle_content_digest 覆盖的是 files 清单（路径与哈希），不覆盖本文件自身——
自己的摘要写进自己，改一次摘要文件就又变了，盖不上章。
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent.parent
BUNDLE = ROOT / "03_m2_evaluation_foundation/steward/hidden_generation_input_bundle.v1.1.0.yaml"


def content_digest(files: list[dict]) -> str:
    """对「路径→哈希」清单取摘要。顺序无关，改一个字节就变。"""
    lines = sorted(f"{row['path']}\t{row['sha256']}" for row in files)
    return hashlib.sha256(("\n".join(lines) + "\n").encode("utf-8")).hexdigest()


def main() -> int:
    doc = yaml.safe_load(BUNDLE.read_text(encoding="utf-8"))
    missing = []
    for row in doc["files"]:
        path = ROOT / row["path"]
        if not path.exists():
            missing.append(row["path"])
            continue
        row["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    if missing:
        print("REQUIRED_INPUT_FILE_MISSING: " + ", ".join(missing), file=sys.stderr)
        return 1

    counts: dict[str, int] = {}
    for row in doc["files"]:
        counts[row["category"]] = counts.get(row["category"], 0) + 1
    order = [c["category"] for c in doc["required_file_categories"]]
    for category in counts:
        if category not in order:
            order.append(category)
    doc["required_file_categories"] = [{"category": c, "file_count": counts[c]} for c in order]
    doc["required_category_count"] = len(order)
    doc["file_count"] = len(doc["files"])
    doc["bundle_content_digest"] = content_digest(doc["files"])
    doc["machine_checkable_fields"]["file_count"]["current_value"] = len(doc["files"])
    doc["machine_checkable_fields"]["required_category_count"]["required_value"] = len(order)

    prompt = doc["steward_prompt"]
    prompt_path = ROOT / prompt["path"]
    prompt["sha256"] = hashlib.sha256(prompt_path.read_bytes()).hexdigest()
    (ROOT / prompt["sha256_sidecar"]).write_text(
        f"{prompt['sha256']}  {Path(prompt['path']).name}\n", encoding="utf-8"
    )

    BUNDLE.write_text(yaml.safe_dump(doc, allow_unicode=True, sort_keys=False, width=120), encoding="utf-8")
    print(f"bundle refreshed: {doc['file_count']} files / {doc['required_category_count']} categories")
    print(f"bundle_content_digest: {doc['bundle_content_digest']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
