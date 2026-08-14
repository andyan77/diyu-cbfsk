#!/usr/bin/env python3
"""披露纪律：交付报告必须列出对应回执里的**全部**未决项，不得挑着写。

NB-M2-06 起因：回执里记了七条未决项，报告只提了其中几条。少写的那几条不是被解决了，
是被省略了——而读报告的人（Guardian、总顾问、Founder）正是靠报告决定要不要往下走。
回执里有、报告里没有，等于让决策者在不知道有这条的情况下签字。

判据只做一件事：把回执的 open_items 逐个 id 拿去报告正文里找。找不到就判失败。
不判「写得够不够详细」——那是人的判断；只判「有没有提到」——那是机器能守住的事实。
"""

from __future__ import annotations

import re
from pathlib import Path

from _common import ROOT, cli, load_yaml, read_text

LABEL = "check_disclosure_discipline"

RECEIPT_DIR = "11_reports_and_receipts"
_ID_KEYS = ("id", "item_id", "open_item_id", "condition_id")


def validate(payload: dict) -> list[str]:
    errors: list[str] = []

    pairs = payload.get("pairs") or []
    if not pairs:
        errors.append("DISCLOSURE_SCAN_EMPTY: no receipt/report pair was discovered — 读到空不等于没问题")

    for pair in pairs:
        receipt = pair.get("receipt", "<unknown receipt>")
        report = pair.get("report")
        if not report:
            errors.append(f"REPORT_MISSING_FOR_RECEIPT: {receipt} has open items but no delivery report beside it")
            continue
        for item in pair.get("open_items") or []:
            oid = item.get("id")
            if not oid:
                errors.append(f"OPEN_ITEM_WITHOUT_ID: {receipt} carries an open item with no identifier")
                continue
            if not item.get("disclosed_in_report"):
                errors.append(
                    f"OPEN_ITEM_NOT_DISCLOSED: {receipt} records {oid} but {report} never mentions it — "
                    "回执里有、报告里没有，等于让决策者在不知情的前提下签字"
                )
        declared = pair.get("declared_open_item_count")
        actual = len(pair.get("open_items") or [])
        if declared is not None and declared != actual:
            errors.append(
                f"OPEN_ITEM_COUNT_MISSTATED: {report} says {declared!r} open item(s), {receipt} holds {actual}"
            )

    return errors


def _open_item_id(item) -> str | None:
    if not isinstance(item, dict):
        return None
    for key in _ID_KEYS:
        if item.get(key):
            return str(item[key])
    return None


def _declared_count(text: str) -> int | None:
    """报告若自报未决项条数，就必须对得上。没自报则不判这一条。"""
    match = re.search(r"未决项\D{0,6}(\d+)\s*(?:条|项)", text)
    return int(match.group(1)) if match else None


def collect() -> dict:
    pairs = []
    for receipt_path in sorted((ROOT / RECEIPT_DIR).rglob("*delivery_receipt.yaml")):
        rel = str(receipt_path.relative_to(ROOT))
        data = load_yaml(rel)
        raw = data.get("open_items")
        if isinstance(raw, dict):
            # 有的回执把逐条清单包在 items 里，外层放裁定人与时间；取里层，别把元数据当条目。
            raw = raw.get("items") or [v for v in raw.values() if isinstance(v, dict)]
        if not raw:
            continue

        report_path = receipt_path.with_name(receipt_path.name.replace("_receipt.yaml", "_report.md"))
        report_rel = str(report_path.relative_to(ROOT)) if report_path.exists() else None
        text = read_text(report_rel) if report_rel else ""

        items = []
        for entry in raw:
            oid = _open_item_id(entry)
            items.append({"id": oid, "disclosed_in_report": bool(oid) and oid in text})
        pairs.append(
            {
                "receipt": rel,
                "report": report_rel,
                "open_items": items,
                "declared_open_item_count": _declared_count(text) if text else None,
            }
        )
    return {"pairs": pairs}


if __name__ == "__main__":
    cli(LABEL, collect, validate)
