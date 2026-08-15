#!/usr/bin/env python3
"""D-17—D-29 and S1—S8 must all be landed on real anchors; D-28/D-29 anchors are checked verbatim."""

from __future__ import annotations

import yaml

from _common import ROOT, cli, docx_all_text, docx_paragraph_texts, load_yaml

LABEL = "check_ruling_coverage"

REQUIRED_RULINGS = [f"D-{n}" for n in range(17, 30)]
REQUIRED_GOVERNANCE_RULINGS = [f"S{n}" for n in range(1, 9)]

# D-28 / D-29 的锚点文本必须在 PRD 候选正文中真实出现（逐条 verbatim 片段，不是关键词模糊匹配）。
D28_ANCHORS = {
    "P-14 原则行": "Non-Uniqueness by Design（合理多解原则）",
    "三分类合同": "evaluation_task_class_contract.v0.1.yaml",
    "可接受决策边界登记": "acceptable_decision_boundary_registry.v0.1.yaml",
    "EvaluationCard 三分类": "必须标注evaluation_task_class",
    "M3 开放题模板": "open_decision_question_template_contract.v0.1.yaml",
    "M4 分歧账本": "保留合法分歧，不得为评分便利消灭",
    "M5 合法多解族": "disagreement_classification_and_solution_family_ledger.v0.1.yaml",
    "M6 舍弃候选族": "acceptable_solution_family_trace",
    "M10 合法决策空间": "legal_decision_space_conformance_report",
    "10.2 指标更名": "核心决策逻辑稳定率",
    "R-22 唯一答案偏误": "唯一答案偏误",
    "停止条件-唯一Gold Answer": "被设置唯一Gold Answer：停止M2冻结",
    "术语-可接受决策边界": "Acceptable Decision Boundary（可接受决策边界）",
    "术语-合法多解族": "Legitimate Solution Family（合法多解族）",
    "术语-决策逻辑稳定率": "Decision Logic Stability Rate（核心决策逻辑稳定率）",
}

D29_ANCHORS = {
    "M6 禁单层直答": "不得实现为“把已接受知识注入Prompt/RAG后由LLM端到端直接作答”的单层结构",
    "架构符合性报告": "architecture_conformance_check_report",
    "LLM-off 重放夹具": "llm_off_invariance_replay_fixtures",
    "通过标准三条": "架构符合性检查三条全部通过",
    "StylingRanker 非唯一argmax": "不是唯一argmax（D-28）",
    "DecisionTrace 规则归因": "每个排除项须标注触发它的确定性规则",
    "停止条件-纯PromptRAG": "M6以纯Prompt/RAG端到端直答实现",
    "术语-LLM-off不变性": "LLM-off Invariance（LLM-off不变性）",
}

FORBIDDEN_METRIC_RESIDUE = "核心判断重复一致率"
# 旧指标名只允许作为「原名」注记出现在术语表；作为活指标名出现即判 FAIL。
RENAME_NOTE_MARKERS = ("原名", "更名", "renamed")


def validate(payload: dict) -> list[str]:
    errors: list[str] = []

    mapped = payload.get("rulings_in_change_map") or []
    for ruling in REQUIRED_RULINGS:
        if ruling not in mapped:
            errors.append(f"RULING_NOT_MERGED: {ruling} missing from PRD_v1.2_change_map ruling list")
    detailed = payload.get("rulings_with_anchors") or []
    for ruling in REQUIRED_RULINGS:
        if ruling not in detailed:
            errors.append(f"RULING_WITHOUT_ANCHORS: {ruling} has no ruling_map entry")

    gov = payload.get("governance_rulings") or []
    for s in REQUIRED_GOVERNANCE_RULINGS:
        if s not in gov:
            errors.append(f"GOVERNANCE_RULING_NOT_LANDED: {s}")

    for name, present in sorted((payload.get("d28_anchors") or {}).items()):
        if not present:
            errors.append(f"D28_ANCHOR_MISSING: {name}")
    for name, present in sorted((payload.get("d29_anchors") or {}).items()):
        if not present:
            errors.append(f"D29_ANCHOR_MISSING: {name}")

    for paragraph in payload.get("old_metric_name_paragraphs") or []:
        if not any(marker in paragraph for marker in RENAME_NOTE_MARKERS):
            errors.append(
                f"STALE_METRIC_NAME: {FORBIDDEN_METRIC_RESIDUE} used as a live metric name in: {paragraph[:80]}"
            )
    if payload.get("metric_threshold") != "≥ 85%":
        errors.append(f"METRIC_THRESHOLD_CHANGED: expected ≥ 85%, got {payload.get('metric_threshold')!r}")

    for ruling in ("D-28", "D-29"):
        if ruling not in (payload.get("rulings_in_receipt_matrix") or []):
            errors.append(f"RECEIPT_MATRIX_MISSING: {ruling} absent from the verification receipt matrix")

    if payload.get("prompt_rag_direct_answer_accepted_for_m6") is True:
        errors.append("M6_ANTI_DEGENERATION_VIOLATED: a pure Prompt/RAG direct-answer implementation was accepted")

    return errors


# D-29 明文禁止的实现形态。判据要回答的是「有没有哪份 Founder 裁决**接受**了它」，
# 不是「有没有人提过它」——D-29 自己就整段在提它。
M6_PROMPT_RAG_FORMS = (
    "将已接受知识注入 Prompt/RAG 后由 LLM 端到端直接作答",
    "纯 Prompt/RAG 直答",
    "Prompt/RAG 端到端直答",
    "PROMPT_RAG_DIRECT_ANSWER",
)
# 同一段文字里出现任一否定/失败措辞，即判为「不是接受」。放在整段而不是短语之前判：
# 「新增 negative fixture——纯 Prompt/RAG 直答实现通过 M6 必须 FAIL」这句里，
# 否定词在短语之后，按「短语之前有没有否定」判会误判成接受。
M6_REFUSAL_MARKERS = ("不得", "禁止", "不允许", "不可", "FAIL", "negative fixture", "反退化", "不是")


def _m6_prompt_rag_accepted() -> bool:
    """有没有哪份 Founder 裁决肯定性地接受了 M6 纯 Prompt/RAG 端到端直答。

    BR0-EP00 之前这里写死 False——恒假分支，D-29 真被推翻也不会触发
    （与 M2 期 STORE-A locator_present 硬编码 False 同源）。现改为现场扫裁决目录。

    已知边界：本实现按「结构化字段 + 整段否定词」判定。一份用全新措辞肯定接受该形态、
    且整段不含任何否定词的裁决，本实现看不见——这条限制记在
    11_reports_and_receipts/BR0/BR0-EP00 的 known_issues 里，不假装已覆盖全部表达方式。
    """
    for path in sorted((ROOT / "governance" / "founder_rulings").glob("*.yaml")):
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        for node in _walk_scalars(doc):
            if node[0] == "accepted_implementation_form" and str(node[1]) in M6_PROMPT_RAG_FORMS:
                return True
            text = str(node[1])
            if any(form in text for form in M6_PROMPT_RAG_FORMS) and not any(
                marker in text for marker in M6_REFUSAL_MARKERS
            ):
                return True
    return False


def _walk_scalars(node, key=None):
    """产出 (键名, 标量值) 二元组；键名用于识别结构化声明字段。"""
    if isinstance(node, dict):
        for k, v in node.items():
            yield from _walk_scalars(v, k)
    elif isinstance(node, list):
        for v in node:
            yield from _walk_scalars(v, key)
    elif node is not None:
        yield (key, node)


def collect() -> dict:
    change_map = load_yaml("PRD_v1.2_change_map.yaml")
    prd_text = docx_all_text(ROOT / "笛语跨品牌服装搭配专家内核_PRD与执行里程碑_v1.2.docx")
    receipt_text = docx_all_text(ROOT / "PRD_v1.2_核验回执.docx")

    # 阈值存放在 10.2 表格单元里；docx 抽取按段落输出，直接检索该阈值串。
    threshold = "≥ 85%" if "≥ 85%" in prd_text else None

    return {
        "rulings_in_change_map": change_map["change_set"]["rulings"],
        "rulings_with_anchors": sorted(change_map["ruling_map"].keys()),
        "governance_rulings": sorted(change_map["governance_ruling_map"].keys()),
        "d28_anchors": {name: (text in prd_text) for name, text in D28_ANCHORS.items()},
        "d29_anchors": {name: (text in prd_text) for name, text in D29_ANCHORS.items()},
        "old_metric_name_paragraphs": [
            p for p in docx_paragraph_texts(ROOT / "笛语跨品牌服装搭配专家内核_PRD与执行里程碑_v1.2.docx")
            if FORBIDDEN_METRIC_RESIDUE in p
        ],
        "metric_threshold": threshold,
        "rulings_in_receipt_matrix": [r for r in REQUIRED_RULINGS if r in receipt_text],
        "prompt_rag_direct_answer_accepted_for_m6": _m6_prompt_rag_accepted(),
    }


if __name__ == "__main__":
    cli(LABEL, collect, validate)
