#!/usr/bin/env python3
"""The M0 top-level deliverable list must stay at exactly 14 items in every place it appears.

Ground truth is the literal list below, kept independent of the document generator so the
checker cannot re-derive a wrong answer from the artefact it is checking.
"""

from __future__ import annotations

from _common import ROOT, cli, docx_paragraph_texts, docx_table_column

LABEL = "check_m0_fourteen_items"

CANONICAL_M0_ITEMS = [
    "project_charter.v1.0.yaml（项目章程）",
    "capability_contract.v1.0.yaml（能力合同）",
    "category_scope_contract.v1.0.yaml（五类品类范围）",
    "input_output_boundary.v1.0.yaml（输入输出与事实优先级）",
    "role_and_decision_rights.v1.0.yaml（角色与裁决权）",
    "non_goals_and_stop_conditions.v1.0.yaml（非目标与停止条件）",
    "knowledge_state_machine.v1.0.yaml（知识状态机）",
    "architecture_and_integration_boundary.v1.0.yaml（独立解耦与集成边界合同）",
    "compliance_review_contract.v1.0.yaml（合规核验合同：责任人、核验清单、决策时间表）",
    "data_and_fixture_workflow.v1.0.yaml（品牌档案、评测语料与夹具品牌工作流合同）",
    "execution_critical_path_and_decision_gates.v1.0.yaml（关键路径图＋Discovery继续/转向/停止判据）",
    "M1 对象模型 Brief",
    "M2 评测冻结 Brief",
    "M0 checker / fixtures / report / receipt",
]

# 第14节每个里程碑区尾部固定三行验收门。前两行是每个里程碑共用的定值，
# 第一行是「验收门已通过：」＋该里程碑第13节的通过标准原文，故按精确文本剔除，不用前缀匹配。
FIXED_GATE_LINES = (
    "工作树、版本、输入清单、原始输出与报告已可重放。",
    "Founder已形成明确的PASS / CONDITIONAL / BLOCK裁决。",
)
EXPECTED_GATE_LINE_COUNT = 3


def validate(payload: dict) -> list[str]:
    errors: list[str] = []
    default_expected = payload.get("canonical_items") or CANONICAL_M0_ITEMS

    lists = payload.get("lists") or []
    if len(lists) < 4:
        errors.append(f"MISSING_M0_LIST: found {len(lists)} M0 lists, expected at least 4 (PRD 13 / 14 / 17.1 / M0 request)")

    for entry in lists:
        name = entry.get("name", "<unnamed>")
        expected = entry.get("expected") or default_expected
        items = entry.get("items") or []
        if "gate_lines_removed" in entry:
            removed = entry["gate_lines_removed"]
            want = entry.get("expected_gate_lines_removed", 0)
            if removed != want:
                errors.append(
                    f"GATE_LINE_FILTER_DRIFT: {name} removed {removed} gate line(s), expected exactly {want}"
                )
        if len(items) != 14:
            errors.append(f"M0_ITEM_COUNT_CHANGED: {name} has {len(items)} items, expected 14")
        if items != expected:
            missing = [i for i in expected if i not in items]
            extra = [i for i in items if i not in expected]
            if missing:
                errors.append(f"M0_ITEM_MISSING: {name} missing {missing}")
            if extra:
                errors.append(f"M0_ITEM_EXTRA: {name} contains unexpected {extra}")
            if not missing and not extra:
                errors.append(f"M0_ITEM_ORDER_CHANGED: {name} lists the 14 items in a different order")
    return errors


def _region(paragraphs: list[str], start: str, end: str) -> list[str]:
    try:
        i = paragraphs.index(start)
    except ValueError as exc:
        raise ValueError(f"start marker not found: {start!r}") from exc
    for j in range(i + 1, len(paragraphs)):
        if paragraphs[j] == end:
            return paragraphs[i + 1 : j]
    raise ValueError(f"end marker not found after {start!r}: {end!r}")


def _checkbox_items(lines: list[str], *, pass_standard: str | None = None) -> tuple[list[str], int]:
    """Split checkbox lines into (deliverables, gate_lines_removed) by exact text match.

    第14节每个里程碑区尾部固定三行验收门，按精确文本剔除（不用前缀匹配，前缀会误吞交付物）。
    pass_standard=None 表示该区不应有验收门行。剔除数交由 validate() 断言，
    这样 fixture 能真正行使这条判据，而不是只在运行时抛异常。
    """
    gate_lines = set(FIXED_GATE_LINES)
    if pass_standard is not None:
        gate_lines.add(f"验收门已通过：{pass_standard}")
    items = [line[3:].strip() for line in lines if line.startswith("[ ]")]
    kept = [i for i in items if i not in gate_lines]
    return kept, len(items) - len(kept)


def collect() -> dict:
    prd = docx_paragraph_texts(ROOT / "笛语跨品牌服装搭配专家内核_PRD与执行里程碑_v1.2.docx")

    ch13 = _region(prd, "M0｜独立立项与合同冻结", "M1｜语义骨架与品类适配合同")
    pass_standard = ch13[ch13.index("通过标准") + 1]
    ch13_items, ch13_removed = _checkbox_items(ch13)
    ch14_items, ch14_removed = _checkbox_items(
        _region(prd, "M0 独立立项与合同冻结", "M1 语义骨架与品类适配合同"),
        pass_standard=pass_standard,
    )
    s171_items, s171_removed = _checkbox_items(_region(prd, "17.1 首任务必须交付", "17.2 执行纪律"))
    lists = [
        {
            "name": "PRD 13 / M0 交付物",
            "items": ch13_items,
            "gate_lines_removed": ch13_removed,
            "expected_gate_lines_removed": 0,
        },
        {
            "name": "PRD 14 / M0 总清单",
            "items": ch14_items,
            "gate_lines_removed": ch14_removed,
            "expected_gate_lines_removed": EXPECTED_GATE_LINE_COUNT,
        },
        {
            "name": "PRD 17.1 首任务必须交付",
            "items": s171_items,
            "gate_lines_removed": s171_removed,
            "expected_gate_lines_removed": 0,
        },
    ]
    # M0 执行申请把十四项放在「# | 交付物」表里，且不带括注；单独比对短名清单。
    application_items = docx_table_column(
        ROOT / "笛语跨品牌服装搭配专家内核_M0执行申请_v1.2.docx", header=("#", "交付物"), column=1
    )
    short_names = [item.split("（", 1)[0] for item in CANONICAL_M0_ITEMS]
    lists.append({"name": "M0 执行申请 v1.2（表格短名）", "items": application_items, "expected": short_names})
    return {"canonical_items": CANONICAL_M0_ITEMS, "lists": lists}


if __name__ == "__main__":
    cli(LABEL, collect, validate)
