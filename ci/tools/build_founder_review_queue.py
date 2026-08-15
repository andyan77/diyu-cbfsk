#!/usr/bin/env python3
"""从校准集、锚点真源与执行侧标注派生 Founder 审阅队列。

队列要解决的问题只有一个：90 份候选输出要在合理时间内被 Founder 过一遍。
逐份读候选正文需要几个钟头；读一张每行一句话的表，加上一张「这几行请重点看」的短表，
可以压到十几分钟。压缩本身有代价——摘要写偏了，Founder 就在错的描述上确认——
因此摘要与判定依据由人写，其余各列一律现场取自真源，判据重新派生逐字节比对。

四列由人写（founder_review_queue_annotations.v0.1.yaml）：
    候选摘要 / 判定依据锚点 / 判定依据 / 执行侧自评把握度
其余各列现取：
    品类       ← 品类适配合同 category_name
    任务类型   ← evaluation_task_class_contract 的 index
    风险等级   ← 校准集 risk_tier（口径见角色运行模型 review_mode.risk_tiered_review）
    锚点判定   ← founder_boundary_anchor_truth 的 boundary_position

「需重点确认」子表的三条判据由本工具现算，不由人挑：人挑的清单会不知不觉只剩下自己也觉得有问题的那几行。
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent.parent
CAL = ROOT / "03_m2_evaluation_foundation/calibration/public_calibration_set.v0.1.yaml"
ANCHOR = ROOT / "03_m2_evaluation_foundation/calibration/founder_boundary_anchor_truth.v0.1.yaml"
ANNOTATIONS = ROOT / "03_m2_evaluation_foundation/calibration/founder_review_queue_annotations.v0.1.yaml"
TASK_CLASSES = ROOT / "03_m2_evaluation_foundation/scoring/evaluation_task_class_contract.v0.1.yaml"
ROLE_MODEL = ROOT / "governance/bootstrap/role_operating_model.v0.2.yaml"
ADAPTER_DIR = ROOT / "01_contracts_and_schemas/category_adapter_contracts"
OUT = "03_m2_evaluation_foundation/calibration/founder_review_queue.v0.1.md"

# 锚点判定两个取值的中文写法由裁决给定：article_2 明文写「锚点判定（界内｜越界）」。
POSITION_LABELS = {"inside": "界内", "outside": "越界", "boundary_high_value": "边界高价值位"}
CIRCLED = "①②③④⑤⑥⑦⑧⑨"
CRITERION_A = "判定依据不是单一硬门"
CRITERION_B = "开放题解族边界依赖主观判断"
CRITERION_C = "执行侧自评把握度较低"


def load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def category_names() -> dict[str, str]:
    names = {}
    for path in sorted(ADAPTER_DIR.glob("*.adapter.v0.1.yaml")):
        doc = load(path)
        names[doc["category_id"]] = doc["category_name"]
    return names


def class_labels() -> tuple[dict[str, str], list[str]]:
    """①②③ 只是列宽考虑；圈号与含义的对照写在表头图例里，取自三分类合同自己的字段。"""
    doc = load(TASK_CLASSES)
    marks, legend = {}, []
    for row in doc["classes"]:
        mark = CIRCLED[row["index"] - 1]
        marks[row["evaluation_task_class"]] = mark
        legend.append(f"{mark} {row['evaluation_task_class']}——{row['scores_what']}")
    return marks, legend


def risk_legend() -> list[str]:
    tiers = load(ROLE_MODEL)["review_mode"]["risk_tiered_review"]
    high = tiers["high_risk"]
    rest = tiers["medium_and_low_risk"]
    return [
        f"high——Founder 覆盖 {high['founder_review_coverage']}，sampling_allowed={str(high['sampling_allowed']).lower()}",
        f"medium / low——Founder {rest['founder_review']}，AI {rest['ai_review']}",
    ]


def rows() -> list[dict]:
    cases = {c["case_id"]: c for c in load(CAL)["cases"]}
    anchors = {a["case_id"]: a for a in load(ANCHOR)["anchors"]}
    annotations = load(ANNOTATIONS)["annotations"]
    names = category_names()
    marks, _ = class_labels()

    out = []
    for note in annotations:
        cid = note["case_id"]
        case = cases[cid]
        gates = case.get("hard_gate_refs") or []
        anchor_id = note["basis_anchor"]
        flags = []
        reasons = []
        if len(gates) != 1:
            flags.append(CRITERION_A)
            reasons.append(
                f"本例无硬门，判定完全落在边界条款 {anchor_id} 上"
                if not gates
                else f"本例同时命中 {'、'.join(gates)} 两个硬门"
            )
        if note.get("open_family_boundary_subjective"):
            flags.append(CRITERION_B)
        if note["authoring_confidence"] == "low":
            flags.append(CRITERION_C)
            reasons.append(note["low_confidence_reason"])
        out.append(
            {
                "case_id": cid,
                "category": names[case["category_id"]],
                "task_class": case["evaluation_task_class"],
                "task_mark": marks[case["evaluation_task_class"]],
                "risk_tier": case["risk_tier"],
                "candidate_summary": note["candidate_summary"],
                "position": anchors[cid]["boundary_position"],
                "position_label": POSITION_LABELS[anchors[cid]["boundary_position"]],
                "basis_anchor": anchor_id,
                "basis_anchor_kind": "hard_gate" if anchor_id.startswith("HG-") else "boundary_clause",
                "judgment_basis": note["judgment_basis"],
                "authoring_confidence": note["authoring_confidence"],
                "hard_gate_count": len(gates),
                "flags": flags,
                "flag_reasons": reasons,
            }
        )
    return out


def counts(table: list[dict]) -> dict:
    flagged = [r for r in table if r["flags"]]
    strict_only = [
        r for r in table if r["basis_anchor_kind"] == "boundary_clause" and not r["flags"]
    ]
    return {
        "review_units": len(table),
        "inside": sum(1 for r in table if r["position"] == "inside"),
        "outside": sum(1 for r in table if r["position"] == "outside"),
        "flagged": len(flagged),
        "flagged_by_a": sum(1 for r in table if CRITERION_A in r["flags"]),
        "flagged_by_b": sum(1 for r in table if CRITERION_B in r["flags"]),
        "flagged_by_c": sum(1 for r in table if CRITERION_C in r["flags"]),
        "basis_on_hard_gate": sum(1 for r in table if r["basis_anchor_kind"] == "hard_gate"),
        "basis_on_boundary_clause": sum(1 for r in table if r["basis_anchor_kind"] == "boundary_clause"),
        "strict_reading_additional": len(strict_only),
    }


def render() -> str:
    table = rows()
    total = counts(table)
    _, legend = class_labels()
    annotations = load(ANNOTATIONS)
    shared = annotations["shared_questions"]

    lines: list[str] = []
    lines.append("# Founder 审阅队列 · 90 个评审单元")
    lines.append("")
    lines.append("> 本文件由 `ci/tools/build_founder_review_queue.py` 派生，勿手改。")
    lines.append("> 手改会在 `check_m2_predistribution_sequence` 重新派生比对时被逐字节比出来。")
    lines.append("")
    lines.append("## 这份表是干什么的")
    lines.append("")
    lines.append(
        "90 份候选输出要 Founder 过一遍才能分发校准包。逐份读正文要几个钟头；"
        "读这张表加下面那张短表，十几分钟能过完。"
    )
    lines.append("")
    lines.append(
        "**代价说清楚**：摘要是压缩过的。摘要写偏了，确认就落在错的描述上。"
        "凡下面「需重点确认」里出现的行，请回原文核对——原文在 "
        "`03_m2_evaluation_foundation/calibration/public_calibration_set.v0.1.yaml` 各例的 `candidate.candidate_output`。"
    )
    lines.append("")
    lines.append("## 这份表不能做什么")
    lines.append("")
    lines.append(
        "**不得进入分发包。** 它带着「锚点判定」这一列——候选被构造时落在边界哪一侧的答案。"
        "随包发出去，测的就是评审员抄标签的能力。"
    )
    lines.append("")
    lines.append("## 怎么读")
    lines.append("")
    lines.append("- 任务类型：" + "；".join(legend))
    lines.append("- 风险等级：" + "；".join(risk_legend()))
    lines.append(
        "- 锚点判定：**界内**＝照着落在该例接受边界之内构造；**越界**＝照着明确越过该例接受边界构造。"
        "这是构造事实，不是「评审员应当给出的正确答案」。"
    )
    lines.append("- 判定依据：指向被触发或未触发的具体硬门（HG-\\*）或边界条款（ADB-\\*、品类硬约束、CP-\\*）。")
    lines.append("")
    lines.append("## 主表")
    lines.append("")
    lines.append("| case_id | 品类 | 任务类型 | 风险等级 | 候选摘要 | 锚点判定 | 判定依据 |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- |")
    for r in table:
        lines.append(
            f"| {r['case_id']} | {r['category']} | {r['task_mark']} | {r['risk_tier']} | "
            f"{r['candidate_summary']} | {r['position_label']} | {r['judgment_basis']} |"
        )
    lines.append("")
    lines.append("## 需重点确认")
    lines.append("")
    lines.append("凡满足以下任一条即列入，由工具现算，不由执行侧挑选：")
    lines.append("")
    lines.append(f"- **A**：{CRITERION_A}——该例声明的硬门不是恰好一个（无硬门，或同时命中两个）。")
    lines.append(f"- **B**：{CRITERION_B}——开放题，合法解族的边界要靠判断而非题内条款划出。")
    lines.append(f"- **C**：{CRITERION_C}——撰写时执行侧认为称职的评审员可以合理地判到相反的一侧。")
    lines.append("")
    lines.append("| case_id | 锚点判定 | 命中判据 | 为什么要重点看 |")
    lines.append("| --- | --- | --- | --- |")
    for r in table:
        if not r["flags"]:
            continue
        marks = "／".join(_flag_marks(r["flags"]))
        reason = "；".join(r["flag_reasons"]) if r["flag_reasons"] else _shared_reason(r["case_id"], shared)
        lines.append(f"| {r['case_id']} | {r['position_label']} | {marks} | {reason} |")
    lines.append("")
    lines.append("## 共同问题")
    lines.append("")
    lines.append(shared["purpose"])
    lines.append("")
    for item in shared["items"]:
        lines.append(f"### {item['id']}｜{item['question']}")
        lines.append("")
        lines.append(f"- 涉及：{'、'.join(item['affects'])}")
        lines.append(f"- 为什么要紧：{item['why_it_matters'].strip()}")
        lines.append("")
    lines.append("## 计数与口径")
    lines.append("")
    lines.append(f"- 评审单元：{total['review_units']}（界内 {total['inside']}／越界 {total['outside']}）")
    lines.append(
        f"- 需重点确认：{total['flagged']}（A {total['flagged_by_a']}／B {total['flagged_by_b']}／C {total['flagged_by_c']}，同一行可命中多条）"
    )
    lines.append(
        f"- 判定依据落在硬门上 {total['basis_on_hard_gate']} 行，落在边界条款上 {total['basis_on_boundary_clause']} 行。"
    )
    lines.append("")
    lines.append(
        f"**一处读法差异请裁**：判据 A 现在读作「该例声明的硬门不是恰好一个」。"
        f"若「判定依据不是单一硬门」应当读作更严的一版——依据必须落在硬门上，落在边界条款上就算命中——"
        f"则另有 {total['strict_reading_additional']} 行进入子表，合计 "
        f"{total['flagged'] + total['strict_reading_additional']} 行。"
        f"两种读法都已算好，改哪一版由 Founder 定。"
    )
    lines.append("")
    return "\n".join(lines) + "\n"


def _flag_marks(flags: list[str]) -> list[str]:
    order = {CRITERION_A: "A", CRITERION_B: "B", CRITERION_C: "C"}
    return [order[f] for f in flags]


def _shared_reason(case_id: str, shared: dict) -> str:
    for item in shared["items"]:
        if case_id in item["affects"]:
            return f"见 {item['id']}"
    return ""


def build() -> dict[str, str]:
    """返回 {仓内相对路径: 文件内容}。"""
    return {OUT: render()}


def main() -> int:
    for rel, content in build().items():
        (ROOT / rel).write_text(content, encoding="utf-8")
        print(f"generated {rel}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
