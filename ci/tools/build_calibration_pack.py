#!/usr/bin/env python3
"""从公开校准集派生「可独立分发」的评审启动包。

启动包要交到两个互相隔离的评审工作面手里，因此有两条硬性质：

  单一真源 —— 题目只有一处定义（public_calibration_set.v0.1.yaml）。
              启动包是派生物，由本工具生成、由判据重新派生比对；
              手改启动包会被当场比出来。写两份题会出现两套口径，改一处漏一处。
  无治理上下文 —— 包里不得出现里程碑状态、裁决编号、Commit 哈希、既往结论或另一侧评审结果。
              评审员知道得越多，「分歧率」测出来的就越不是他们各自的判断。

生成物：cases/ 全量 JSONL、batches/ 分批清单（每批 10 个单元）、hard_gates.json 术语表、
scoring_anchors.json 数值评分锚点、pack_manifest.yaml。
评审 Prompt 与输出格式说明是手写文件，本工具只负责把它们的哈希登进 Manifest。

评审单元由题干与候选输出组成。候选输出随包带出，**被构造时落在边界哪一侧的标签不带出**——
那份对照表在 founder_boundary_anchor_truth.v0.1.yaml，发出去就等于把答案发出去。
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent.parent
CAL = ROOT / "03_m2_evaluation_foundation/calibration/public_calibration_set.v0.1.yaml"
ANCHORS = ROOT / "03_m2_evaluation_foundation/calibration/numeric_scoring_anchors.v0.1.yaml"
GATES = ROOT / "03_m2_evaluation_foundation/gates/hard_gate_definitions.v0.1.yaml"
PACK = ROOT / "03_m2_evaluation_foundation/calibration/launch_pack"
BATCH_SIZE = 10

# 评审员需要看到的字段；治理字段（authority / execution_package / 状态）一律不带出来。
CASE_FIELDS = (
    "case_id", "category_id", "evaluation_task_class", "risk_tier", "capability_dimensions",
    "input_object_refs", "scenario", "hard_gate_refs", "expected_evaluation_form",
    "binary_fact_determination", "acceptable_reasoning_interval", "acceptable_decision_boundary_ref",
    "legal_solution_families", "acceptance_boundary", "gold_answer_allowed",
    "founder_review_coverage", "sampling_allowed", "candidate",
)
# 候选块只带出这三个键。non_candidate_knowledge 是仓内治理标记，评审员不需要，也不该看见。
CANDIDATE_FIELDS = ("candidate_id", "candidate_output", "candidate_decision_trace")
ANCHORED_CLASSES = ("mechanism_correctness", "open_decision")


def build_cases() -> list[dict]:
    cases = yaml.safe_load(CAL.read_text(encoding="utf-8"))["cases"]
    out = []
    for case in cases:
        row = {k: case[k] for k in CASE_FIELDS if k in case}
        cand = row.get("candidate")
        if cand is not None:
            row["candidate"] = {k: cand[k] for k in CANDIDATE_FIELDS if k in cand}
        out.append(row)
    return out


def build_scoring_anchors() -> dict:
    """②③ 类的五档锚点：单一定义在 numeric_scoring_anchors.v0.1.yaml，这里只投影。"""
    src = yaml.safe_load(ANCHORS.read_text(encoding="utf-8"))
    doc = {
        "judgment_values": ["ACCEPT", "REJECT", "AMBIGUOUS"],
        "judgment_is_not_score": src["judgment_vs_score"]["why"],
        "constraint_correctness": {
            "score_values_allowed": src["constraint_correctness"]["score_values_allowed"],
            "judgment_score_binding": src["constraint_correctness"]["judgment_score_binding"],
        },
    }
    for cls in ANCHORED_CLASSES:
        doc[cls] = {
            "anchors": src[cls]["anchors"],
            "intermediate_values_allowed": src[cls]["intermediate_values_allowed"],
        }
    return doc


def build_hard_gates() -> list[dict]:
    mappings = yaml.safe_load(GATES.read_text(encoding="utf-8"))["mappings"]
    return [
        {"hard_gate_id": m["hard_gate_id"], "name": m["hard_gate_name"], "metric": m["metric"]}
        for m in mappings
    ]


def jsonl(rows: list[dict]) -> str:
    return "".join(json.dumps(r, ensure_ascii=False, sort_keys=False) + "\n" for r in rows)


def build() -> dict[str, str]:
    """返回 {相对包内路径: 文件内容}。"""
    cases = build_cases()
    out = {"cases/public_calibration_cases.jsonl": jsonl(cases)}
    for index in range(0, len(cases), BATCH_SIZE):
        number = index // BATCH_SIZE + 1
        out[f"batches/batch_{number:02d}.jsonl"] = jsonl(cases[index:index + BATCH_SIZE])
    out["hard_gates.json"] = json.dumps(build_hard_gates(), ensure_ascii=False, indent=2) + "\n"
    out["scoring_anchors.json"] = json.dumps(build_scoring_anchors(), ensure_ascii=False, indent=2) + "\n"
    return out


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


HANDWRITTEN = (
    "README_分发说明.md",
    "review_prompt.shared.v1.1.0.md",
    "output_format.md",
    "identity_lines.yaml",
)
# 治理上下文黑名单：这些串一旦出现在包里，评审员就不再是「只看题判题」。
FORBIDDEN_TOKENS = (
    "m2_frozen", "execution_status", "milestone", "里程碑", "候选 Commit", "Guardian", "总顾问",
    "裁决", "DIYU-CBFSK-FOUNDER", "COND-0", "BLOCK_M2", "PR #", "M2-EP", "隐藏集", "STORE-A",
    "founder_signature_eligible", "APPROVE_WITH_CONDITIONS",
)
# 锚点标签黑名单：候选输出被构造时落在哪一侧，是本包唯一不能带出去的东西。
FORBIDDEN_ANCHOR_KEYS = ("boundary_position", "constructed_judgment", "expected_judgment")


def build_manifest(generated: dict[str, str]) -> str:
    files = []
    for rel in sorted(list(generated) + list(HANDWRITTEN)):
        content = generated.get(rel)
        if content is None:
            content = (PACK / rel).read_text(encoding="utf-8")
        files.append({"path": rel, "sha256": sha256(content)})
    cases = build_cases()
    doc = {
        "schema_version": "0.1",
        "pack_id": "DIYU-CBFSK-M2-CALIBRATION-LAUNCH-PACK",
        "pack_version": "1.1.0",
        "generated_by": "ci/tools/build_calibration_pack.py",
        "derived_from": "03_m2_evaluation_foundation/calibration/public_calibration_set.v0.1.yaml",
        "single_source_rule": "题目只有一处定义；本包是派生物，手改会被判据重新派生比对时抓到。",
        "independently_distributable": True,
        "case_count": len(cases),
        "batch_size": BATCH_SIZE,
        "batch_count": (len(cases) + BATCH_SIZE - 1) // BATCH_SIZE,
        "review_unit_count": len(cases),
        "candidate_count": sum(1 for c in cases if c.get("candidate")),
        "review_prompt": {
            "path": "review_prompt.shared.v1.1.0.md",
            "sha256": sha256((PACK / "review_prompt.shared.v1.1.0.md").read_text(encoding="utf-8")),
            "shared_by_both_sides": True,
            "only_identity_line_differs": True,
        },
        "must_not_contain": {
            "kinds": ["项目治理上下文", "既往结论", "其他评审结果", "候选输出的边界侧标签"],
            "tokens": list(FORBIDDEN_TOKENS),
            "anchor_keys": list(FORBIDDEN_ANCHOR_KEYS),
            "why": (
                "分歧率要测的是两位评审员各自的判断。评审员一旦知道项目卡在哪、"
                "或上一轮别人怎么判的，他会往那个方向靠——测出来的一致是靠过去的，不是各自看出来的。"
            ),
        },
        "file_count": len(files),
        "files": files,
        "failure_states": [
            "PACK_DERIVATION_DRIFT", "PACK_MANIFEST_HASH_STALE", "PACK_CASE_SET_DRIFT",
            "PACK_BATCH_PARTITION_BROKEN", "PACK_CONTAINS_GOVERNANCE_CONTEXT",
            "PACK_PROMPT_HASH_MISMATCH", "PACK_FILE_MISSING", "PACK_CONTAINS_ANCHOR_LABEL",
            "PACK_CANDIDATE_MISSING",
        ],
    }
    return yaml.safe_dump(doc, allow_unicode=True, sort_keys=False, width=120)


def main() -> int:
    generated = build()
    for rel, content in generated.items():
        path = PACK / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    (PACK / "pack_manifest.yaml").write_text(build_manifest(generated), encoding="utf-8")
    print(f"generated {len(generated) + 1} files under {PACK.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
