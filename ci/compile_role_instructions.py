#!/usr/bin/env python3
"""Deterministically compile role/instruction projections from the canonical source.

Canonical source: governance/bootstrap/role_operating_model.v0.2.yaml (D-27 / Project CI).

Every file this script emits is a projection. Projections are never product truth and
must never be hand-edited. Run with --check in CI to detect drift, --write to regenerate.
The output is a pure function of the canonical source: no timestamps, no randomness.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CANONICAL = ROOT / "governance" / "bootstrap" / "role_operating_model.v0.2.yaml"

GENERATED_BANNER = (
    "<!-- GENERATED FILE — DO NOT EDIT BY HAND.\n"
    "     canonical source: governance/bootstrap/role_operating_model.v0.2.yaml\n"
    "     regenerate:       python3 ci/compile_role_instructions.py --write\n"
    "     drift check:      python3 ci/compile_role_instructions.py --check\n"
    "     This file is a projection, not product truth. -->"
)

ROLE_FILES = {
    "FOUNDER_PRODUCT_AUTHORITY": "governance/roles/founder_decision_charter.md",
    "GPT_CHIEF_ADVISOR": "governance/roles/chatgpt_chief_advisor.md",
    "CLAUDE_EXECUTION_PLANNER": "governance/roles/claude_execution_planner.md",
    "CODEX_EXECUTION_ENGINEER": "governance/roles/codex_execution_engineer.md",
    "CLAUDE_INDEPENDENT_GUARDIAN": "governance/roles/claude_independent_guardian.md",
}

PROMPT_FILES = {
    "GPT_CHIEF_ADVISOR": "governance/prompts/chatgpt_chief_advisor.prompt.md",
    "CLAUDE_EXECUTION_PLANNER": "governance/prompts/claude_execution_planner.prompt.md",
    "CODEX_EXECUTION_ENGINEER": "governance/prompts/codex_execution_engineer.prompt.md",
    "CLAUDE_INDEPENDENT_GUARDIAN": "governance/prompts/claude_independent_guardian.prompt.md",
}


def load_model() -> dict:
    return yaml.safe_load(CANONICAL.read_text(encoding="utf-8"))


def role_by_id(model: dict, role_id: str) -> dict:
    for role in model["roles"]:
        if role["role_id"] == role_id:
            return role
    raise KeyError(role_id)


def bullets(items) -> str:
    return "\n".join(f"- {item}" for item in items)


def numbered(items) -> str:
    return "\n".join(f"{i}. {item}" for i, item in enumerate(items, start=1))


def yes_no(value) -> str:
    if value is True:
        return "是"
    if value is False:
        return "否"
    return str(value)


def state_block(model: dict) -> str:
    state = model["project_state"]
    lines = [f"{key}: {str(value).lower() if isinstance(value, bool) else value}" for key, value in state.items()]
    return "```yaml\n" + "\n".join(lines) + "\n```"


def permission_table(role: dict) -> str:
    keys = [
        ("human", "人类"),
        ("final_authority", "最终裁决权"),
        ("repo_read_permission", "仓库读"),
        ("repo_write_permission", "仓库写"),
        ("default_repository_writer", "默认唯一写入者"),
        ("merge_permission", "合并权"),
        ("formal_guardian", "正式 Guardian"),
        ("independent_review_vote", "独立评审票"),
        ("planning_context_access", "可读规划上下文"),
        ("candidate_edit_permission", "可编辑候选"),
    ]
    rows = ["| 权限 | 取值 |", "|---|---|"]
    for key, label in keys:
        if key in role:
            rows.append(f"| {label} `{key}` | `{yes_no(role[key])}` |")
    return "\n".join(rows)


def render_role_doc(model: dict, role_id: str) -> str:
    role = role_by_id(model, role_id)
    parts = [
        GENERATED_BANNER,
        "",
        f"# 角色合同 · {role['display_name']}",
        "",
        f"`role_id: {role['role_id']}`｜规范源 `{model['model_id']} {model['model_version']}`"
        f"｜Founder 裁决 `{'`、`'.join(model['founder_ruling_ids'])}`",
        "",
        f"合同生效状态：`effective: {str(model['effective']).lower()}`（生效前置：{model['effective_precondition']}）。",
        "",
        "## 权限",
        "",
        permission_table(role),
        "",
        "## 职责",
        "",
        bullets(role.get("responsibilities", [])),
    ]
    if role.get("forbidden"):
        parts += ["", "## 禁止", "", bullets(role["forbidden"])]
    if role.get("notes"):
        parts += ["", "## 说明", "", bullets(role["notes"])]
    if role.get("downstream_flow"):
        parts += ["", "## 下游流向", "", f"`{role['downstream_flow']}`"]
    if role.get("vote_scope_note"):
        parts += ["", "## 评审票口径", "", role["vote_scope_note"]]

    parts += [
        "",
        "## 角色隔离硬规则",
        "",
        bullets(
            [
                "Planner 与 Guardian 必须是不同会话、不同工作区、不同任务合同。",
                "Guardian 不得读取规划上下文，不得编辑候选。",
                "同一任务的写入者不得担任该任务 Guardian。",
                "任何修复形成新 Commit 后，先前 Guardian 结论与总顾问审查结论一律失效，必须针对新 Commit 重审。",
            ]
        ),
        "",
        "## 权威优先级",
        "",
        numbered(model["authority_hierarchy"]),
        "",
        "下层文件不得扩大上层权限；AI 意见不得升级为 Founder 裁决；文件修改时间不是权威信号；不得用「最新版」代替 Commit 哈希。",
        "",
        "## 当前项目状态",
        "",
        state_block(model),
        "",
    ]
    return "\n".join(parts)


def render_prompt(model: dict, role_id: str) -> str:
    role = role_by_id(model, role_id)
    tc = model["task_classification"]
    parts = [
        GENERATED_BANNER,
        "",
        f"# 角色 Prompt · {role['display_name']}",
        "",
        f"`role_id: {role['role_id']}`",
        "",
        "> 本 Prompt 只约束「你如何工作」。它不是产品真源，不得改变 PRD、里程碑执行申请或 Founder 裁决。",
        "",
        "## 你可以做",
        "",
        bullets(role.get("responsibilities", [])),
        "",
        "## 你不得做",
        "",
        bullets(
            role.get("forbidden", [])
            + [
                "把 AI 评审表述为外部专家意见",
                "把 Founder 自评表述为独立法律意见",
                "静默绕过不可用角色（默认动作是 DEFER）",
                "在未完成基线对账时修改产品真源",
                "把隐藏评测内容带入主仓或其 Git 历史",
            ]
        ),
        "",
        "## 每次输出必须携带",
        "",
        bullets(
            [
                "`task_id` 与 `execution_run_id`（标准 UUIDv4，不复用其他任务 UUID）",
                "所依据的 `baseline_commit` 或 `candidate_commit` 的完整哈希（不得写「最新版」）",
                "结论的证据等级：`runtime_verified` / `static_verified` / `inferred` / `unverified`",
                "未决事项：只列真正需要 Founder 裁决的问题",
            ]
        ),
        "",
        "## 任务分级",
        "",
        f"- **L1 {tc['L1']['name']}**：{'、'.join(tc['L1']['allowed_scope'])}。涉及 "
        f"{'、'.join(tc['L1']['forbidden_scope'])} 一律不得按 L1 处理。",
        f"- **L2 {tc['L2']['name']}**：{'、'.join(tc['L2']['scope'])}。走完整闭环。",
        f"- **L3 {tc['L3']['name']}**：{'、'.join(tc['L3']['scope'])}。未经 Founder 显式豁免不得跳过"
        f"{'、'.join(tc['L3']['must_not_skip_without_explicit_founder_waiver'])}。",
        "",
        "## 标准执行闭环",
        "",
        bullets(model["execution_loop"]),
        "",
        "## 角色不可用",
        "",
        f"默认动作 `{model['role_unavailability_fallback']['default_action']}`；"
        f"静默绕过 = `{str(model['role_unavailability_fallback']['silent_bypass_allowed']).lower()}`。"
        "豁免必须写入 Receipt，且不得写成 `advisor_review_completed: true`。",
        "",
        "## CONDITIONAL 不等于 PASS",
        "",
        f"条件必须进入 `{model['conditional_closure']['ledger_path']}`，字段齐全："
        f"{'、'.join(model['conditional_closure']['required_fields'])}。",
        "",
    ]
    if role_id == "CLAUDE_INDEPENDENT_GUARDIAN":
        parts += [
            "## 自举来源",
            "",
            f"本轮 Guardian 权限来源：`{model['bootstrap']['guardian_bootstrap_source']}`。",
            "",
            bullets(model["bootstrap"]["rules"]),
            "",
        ]
    if role_id == "CODEX_EXECUTION_ENGINEER":
        parts += [
            "## 写入边界",
            "",
            bullets(
                [
                    "只在任务包明确列出的允许路径内写入。",
                    "候选 Commit 冻结后不得再改；需要修复时形成新 Commit 并重新走 Guardian 与总顾问。",
                    "合并 main 必须有 Founder 对具体 Commit 哈希的批准。",
                ]
            ),
            "",
            "## 红线",
            "",
            bullets(model["red_lines"]),
            "",
        ]
    return "\n".join(parts)


def render_agents_md(model: dict) -> str:
    roles_rows = ["| role_id | 写仓 | Guardian | 独立评审票 |", "|---|---|---|---|"]
    for role in model["roles"]:
        roles_rows.append(
            f"| `{role['role_id']}` | `{yes_no(role.get('repo_write_permission', role.get('formal_repository_write_permission', False)))}` "
            f"| `{yes_no(role.get('formal_guardian', False))}` | `{yes_no(role.get('independent_review_vote', False))}` |"
        )
    return "\n".join(
        [
            GENERATED_BANNER,
            "",
            "# AGENTS.md · 笛语跨品牌服装搭配专家内核",
            "",
            f"规范源：`{model['instruction_projection']['canonical_source']}`（{model['model_id']} {model['model_version']}）。",
            "本文件是投影，不是产品真源。改动请改规范源后运行 `python3 ci/compile_role_instructions.py --write`。",
            "",
            "## 当前项目状态",
            "",
            state_block(model),
            "",
            "## 产品真源",
            "",
            f"- 当前活基线：`{model['product_truth']['current_active']}`（`{model['product_truth']['current_active_status']}`）",
            f"- 候选：`{model['product_truth']['candidate']}`，`candidate_effective: "
            f"{str(model['product_truth']['candidate_effective']).lower()}`",
            f"- v1.2 生效前归档 v1.1：`{str(model['product_truth']['archive_v1_1_before_v1_2_effective']).lower()}`",
            "- 任何时刻只允许一个活产品真源；角色 Prompt 与投影文件都不是产品真源。",
            "",
            "## 角色与权限",
            "",
            "\n".join(roles_rows),
            "",
            f"审查模式：`{model['review_mode']['mode']}`；`external_human_review: "
            f"{str(model['review_mode']['external_human_review']).lower()}`；`external_legal_opinion: "
            f"{str(model['review_mode']['external_legal_opinion']).lower()}`。",
            "",
            "禁止表述：",
            "",
            bullets(model["review_mode"]["forbidden_claims"]),
            "",
            "## 权威优先级",
            "",
            numbered(model["authority_hierarchy"]),
            "",
            "## 授权层级",
            "",
            bullets([f"`{k}` → {v}" for k, v in model["authorization_layers"].items()]),
            "",
            "## 标准执行闭环",
            "",
            bullets(model["execution_loop"]),
            "",
            "## 隐藏评测边界",
            "",
            f"主仓存放隐藏内容：`{str(model['hidden_benchmark_isolation']['main_repository_storage_allowed']).lower()}`。"
            f"主仓只允许：{'、'.join(model['hidden_benchmark_isolation']['main_repository_allowed_artifacts'])}。"
            f"公开目录名固定为 `{model['hidden_benchmark_isolation']['directory_rename']['to']}`。",
            "",
            "## 红线",
            "",
            bullets(model["red_lines"]),
            "",
        ]
    )


def render_claude_md(model: dict) -> str:
    tc = model["task_classification"]
    return "\n".join(
        [
            GENERATED_BANNER,
            "",
            "# CLAUDE.md · 笛语跨品牌服装搭配专家内核",
            "",
            f"规范源：`{model['instruction_projection']['canonical_source']}`。本文件是投影，不得手工编辑。",
            "",
            "## 一句话",
            "",
            "本仓是产品合同仓。当前处于 `EXECUTION_NOT_STARTED`；没有任何里程碑被授权开工。",
            "",
            "## 你在本仓可能承担的两个角色（互斥）",
            "",
            "- `CLAUDE_EXECUTION_PLANNER`：只读规划，产出任务包与执行 Prompt。**不写仓、不自审。**",
            "- `CLAUDE_INDEPENDENT_GUARDIAN`：只读审查冻结 Commit。**不规划、不施工、不修复、不读规划上下文。**",
            "",
            "同一会话不得同时充当两者；两者必须不同工作区、不同会话、不同任务合同。",
            "",
            "另有 `CLAUDE_PLANNING_AND_VERIFICATION_SURFACE`（Cowork 工作面）：可出规划建议与核验意见供 Founder 审阅，"
            "但不得直接写正式产品真源、不得担任同一任务 Guardian、不得把核验意见表述为外部独立审查。",
            "",
            "## 产品真源",
            "",
            f"- 活基线 `{model['product_truth']['current_active']}` — `{model['product_truth']['current_active_status']}`",
            f"- 候选 `{model['product_truth']['candidate']}` — 未生效",
            "- v1.2 生效前不得归档 v1.1；不得同时存在两个活产品真源。",
            "",
            "## 当前项目状态",
            "",
            state_block(model),
            "",
            "## 任务分级",
            "",
            f"- L1 {tc['L1']['name']}：只做{'、'.join(tc['L1']['allowed_scope'][:3])}等无语义修复。",
            f"- L2 {tc['L2']['name']}：走 Planner → Founder → Codex → Guardian → PR → 顾问 → Founder → 合并。",
            f"- L3 {tc['L3']['name']}：PRD、角色权限、隐藏评测、安全、合规、发布门等，"
            "未经 Founder 显式豁免不得跳过 Guardian / 总顾问 / Founder 具体 Commit 批准。",
            "",
            "## 硬规则",
            "",
            bullets(
                [
                    "遇事先查再问：可从仓库、配置、命令发现的事实先探索，不先提问。",
                    "结论必须标注证据等级；未实测不得写「已通过 / 已对齐 / 已修复」。",
                    "引用 Commit 必须写完整哈希，禁止「最新版」。",
                    "CONDITIONAL 不等于 PASS；条件必须进台账并绑定证据与 Commit。",
                    "角色不可用默认 DEFER，不得静默绕过。",
                    "不得把 AI 评审说成外部专家，不得把 Founder 自评说成律师意见。",
                ]
            ),
            "",
            "## 红线",
            "",
            bullets(model["red_lines"]),
            "",
            "## 校验",
            "",
            "```bash",
            "python3 ci/run_all_checks.py            # 全量确定性 Checker",
            "python3 ci/compile_role_instructions.py --check   # 投影漂移检测",
            "python3 工具/check_prd_v1_2.py --require-archive  # v1.2 生效后才带该参数",
            "```",
            "",
        ]
    )


def render_copilot(model: dict) -> str:
    return "\n".join(
        [
            GENERATED_BANNER,
            "",
            "# GitHub Copilot / Work CI 指令投影",
            "",
            f"规范源：`{model['instruction_projection']['canonical_source']}`。本文件是投影，不得手工编辑，"
            "也不构成产品真源。",
            "",
            "## 仓库性质",
            "",
            "产品合同仓（PRD、里程碑执行申请、治理合同）。无应用代码，无生产服务。",
            f"当前状态 `{model['project_state']['execution_status']}`，`m0_authorized: "
            f"{str(model['project_state']['m0_authorized']).lower()}`。",
            "",
            "## 允许的建议",
            "",
            bullets(
                [
                    "确定性 Checker、fixtures 与报告脚本。",
                    "文档生成器（从已冻结样式模板可重放生成 DOCX）。",
                    "GitHub Actions 守卫（投影漂移、双活真源、隐藏边界、秘密扫描）。",
                ]
            ),
            "",
            "## 禁止的建议",
            "",
            bullets(
                model["red_lines"]
                + [
                    "在主仓创建隐藏评测题目、答案、保密评分细则或隐藏品牌事实包。",
                    "把真实品牌资料、顾客数据或密钥写入仓库。",
                    "手工编辑任何标记为 GENERATED FILE 的投影文件。",
                ]
            ),
            "",
            "## 写入边界",
            "",
            f"默认唯一常规写入者：`CODEX_EXECUTION_ENGINEER`。合并权：`founder_authorized_only`。",
            "",
        ]
    )


def render_all(model: dict) -> dict[str, str]:
    out: dict[str, str] = {
        "AGENTS.md": render_agents_md(model),
        "CLAUDE.md": render_claude_md(model),
        ".github/copilot-instructions.md": render_copilot(model),
    }
    for role_id, path in ROLE_FILES.items():
        out[path] = render_role_doc(model, role_id)
    for role_id, path in PROMPT_FILES.items():
        out[path] = render_prompt(model, role_id)
    declared = set(model["instruction_projection"]["generated_files"])
    if declared != set(out):
        missing = sorted(declared - set(out))
        extra = sorted(set(out) - declared)
        raise SystemExit(f"projection set mismatch: missing={missing} extra={extra}")
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="write projections to disk")
    parser.add_argument("--check", action="store_true", help="fail on drift")
    args = parser.parse_args()
    if args.write == args.check:
        parser.error("choose exactly one of --write / --check")

    model = load_model()
    rendered = render_all(model)

    if args.write:
        for rel, content in sorted(rendered.items()):
            target = ROOT / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            print(f"WROTE {rel}")
        return 0

    drift: list[str] = []
    for rel, content in sorted(rendered.items()):
        target = ROOT / rel
        if not target.exists():
            drift.append(f"{rel}: missing")
        elif target.read_text(encoding="utf-8") != content:
            drift.append(f"{rel}: content differs from canonical projection")
    for line in drift:
        print(f"FAIL instruction_projection {line}")
    if drift:
        print(f"RESULT FAIL: instruction_projection_drift={len(drift)}")
        return 1
    print(f"PASS instruction_projection: {len(rendered)} files, drift=0")
    return 0


if __name__ == "__main__":
    sys.exit(main())
