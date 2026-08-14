#!/usr/bin/env python3
"""造型理解与身份识别永久解耦：结构化能力检测，不做全文关键词扫描。

Founder 裁决（DIYU-CBFSK-FOUNDER-M2-CHARTER-001）：不建设人脸身份识别、验证、模板存储或
跨会话面部关联能力，激活条件＝永不。

为什么不扫散文：本判据要拦的是「系统真的会去做的事」，不是「有人在文档里讨论这件事」。
ADR-004、隔离合同与裁决原文里必然出现「人脸识别」，它们出现在**禁止**的语境里。
全文扫描会把这些判成违规，于是被迫加白名单，白名单一大就什么也拦不住。因此扫描面限定为：
Schema 的 property 名与枚举值、能力/组件/服务登记、依赖清单——这三处出现禁止能力，
才意味着系统声明了这项能力。

禁止与允许两份清单来自 identity_capability_isolation_contract.v0.1.yaml，不在本文件重抄
（EQ-1 / EQ-4：常量必须有来源与名字）。
"""

from __future__ import annotations

from _common import ROOT, cli, is_full_commit_hash, load_yaml

LABEL = "check_m2_identity_isolation"

CONTRACT = "03_m2_evaluation_foundation/identity_isolation/identity_capability_isolation_contract.v0.1.yaml"

# 本 checker 自己的扫描用例目录。用例里**必须**能写出违规声明，否则判据无法被行使（EQ-3）；
# 因此仓库扫描排除它，而它的内容另由 scan_cases 逐条断言命中数——不是「跳过不看」，
# 是「换一条更严的路看」。例外只此一处，且限定到目录，不接受任何其他豁免。
IDENTITY_CASE_DIR = "ci/fixtures/m2/identity_capability_cases"

# 本 checker 自己的判据层夹具同样必须能写出违规声明（负例 payload 里就带着能力名），
# 它「描述」违规而不是违规本身。豁免与 check_hidden_benchmark_boundary 的
# 「自己的 fixture 不算泄漏」同一条规矩：只认 ci/fixtures/ 下 checker 字段指向本 checker 的文件，
# **别的 checker 的 fixture 与任何产品文件一律不豁免**。
FIXTURE_ROOT = "ci/fixtures/"

# 结构化能力声明的落点：只有这些键下面的值才被当作「系统声明的能力」。
CAPABILITY_DECLARATION_KEYS = frozenset(
    {
        "capabilities",
        "capability",
        "capability_id",
        "components",
        "component",
        "services",
        "service",
        "dependencies",
        "dependency",
        "requirements",
        "provides",
        "features",
        "enabled_capabilities",
    }
)

# Schema 结构面：property 名与枚举值。
SCHEMA_STRUCTURAL_KEYS = frozenset({"properties", "definitions", "patternProperties"})

SCANNED_SUFFIXES = (".json", ".yaml", ".yml")

# 只有把某项能力标成「要建 / 已建 / 启用」才算声明。合同里把它列进 forbidden 清单不算。
DECLARATION_CONTEXT_NEGATIVE_KEYS = frozenset(
    {
        "forbidden_capabilities",
        "not_building_now",
        "forbidden",
        "prohibited",
        "never_build",
        "must_not_build",
    }
)


def validate(payload: dict) -> list[str]:
    errors: list[str] = []

    contract = payload.get("contract") or {}
    if contract.get("activation_condition_is_never") is not True:
        errors.append(
            "IDENTITY_ISOLATION_ACTIVATION_CONDITION_WEAKENED: activation_condition_is_never must be true — "
            "「永不」不是「暂缓」，不得改成任何带条件的激活路径"
        )

    forbidden = payload.get("forbidden_capabilities") or []
    if not forbidden:
        errors.append("FORBIDDEN_CAPABILITY_LIST_EMPTY: the contract declares no forbidden capability")
    declared_count = payload.get("forbidden_capabilities_declared_count")
    if declared_count != len(forbidden):
        errors.append(
            f"FORBIDDEN_CAPABILITY_LIST_DRIFT: contract declares count={declared_count!r} "
            f"but lists {len(forbidden)}"
        )

    overlap = sorted(set(forbidden) & set(payload.get("allowed_capabilities") or []))
    if overlap:
        errors.append(
            f"CAPABILITY_LIST_CONTRADICTION: {overlap} appear in both the forbidden and allowed lists"
        )

    for hit in payload.get("forbidden_capability_declarations") or []:
        errors.append(
            f"FORBIDDEN_IDENTITY_CAPABILITY_DECLARED: {hit['file']} declares {hit['capability']!r} "
            f"at {hit['location']}"
        )

    cases = payload.get("scan_cases") or []
    if not any(case.get("expected_hits", 0) > 0 for case in cases):
        errors.append(
            "IDENTITY_SCAN_WITHOUT_NEGATIVE_CASE: no case declares a real violation — "
            "a scanner that was never shown a violation is not known to detect one"
        )
    if not any(case.get("expected_hits", 0) == 0 for case in cases):
        errors.append(
            "IDENTITY_SCAN_WITHOUT_POSITIVE_CASE: no case declares a compliant document — "
            "误报同样是失效，禁止清单出现在裁决文本里必须仍然放行"
        )
    for case in cases:
        if case.get("expected_hits") != case.get("actual_hits"):
            errors.append(
                f"IDENTITY_SCAN_BEHAVIOUR_MISMATCH: {case.get('case_id')} expected "
                f"{case.get('expected_hits')} hit(s), got {case.get('actual_hits')} — {case.get('detail')}"
            )

    for rel in payload.get("own_fixture_exemptions") or []:
        if not rel.startswith("ci/fixtures/"):
            errors.append(
                f"IDENTITY_SCAN_EXEMPTION_TOO_BROAD: {rel} is exempted but is not a fixture — "
                "豁免只限本 checker 自己的夹具，不得扩展到产品文件"
            )

    if payload.get("scanned_file_count", 0) <= 0:
        errors.append(
            "IDENTITY_SCAN_SCANNED_NOTHING: the scan covered no file — a checker that reads nothing "
            "is green for the wrong reason"
        )

    _validate_scan_coverage(payload, errors)

    state = payload.get("current_state") or {}
    for key in ("any_forbidden_capability_declared", "any_face_recognition_dependency", "any_biometric_template_store"):
        if state.get(key) is not False:
            errors.append(f"IDENTITY_ISOLATION_STATE_CLAIM: {key} must be false, got {state.get(key)!r}")
    if state.get("any_forbidden_capability_declared") is False and payload.get("forbidden_capability_declarations"):
        errors.append(
            "IDENTITY_ISOLATION_STATE_CLAIM: contract states no forbidden capability is declared, "
            "but the scan found one — the contract text and the scan disagree"
        )

    return errors


def _walk(node, forbidden: set[str], rel: str, hits: list, path: str = "", in_forbidden_ctx: bool = False) -> None:
    """只在结构化能力面上认能力声明；进入 forbidden/not_building 上下文后一律不认。"""
    if isinstance(node, dict):
        for key, value in node.items():
            child_ctx = in_forbidden_ctx or key in DECLARATION_CONTEXT_NEGATIVE_KEYS
            here = f"{path}.{key}" if path else str(key)
            if key in SCHEMA_STRUCTURAL_KEYS and isinstance(value, dict):
                for prop in value:
                    if not child_ctx and prop in forbidden:
                        hits.append({"file": rel, "capability": prop, "location": f"{here}/{prop}"})
            if not child_ctx and key in CAPABILITY_DECLARATION_KEYS:
                for cap in _scalars(value):
                    if cap in forbidden:
                        hits.append({"file": rel, "capability": cap, "location": here})
            if not child_ctx and key == "enum" and isinstance(value, list):
                for item in value:
                    if isinstance(item, str) and item in forbidden:
                        hits.append({"file": rel, "capability": item, "location": f"{here}[]"})
            _walk(value, forbidden, rel, hits, here, child_ctx)
    elif isinstance(node, list):
        for index, item in enumerate(node):
            _walk(item, forbidden, rel, hits, f"{path}[{index}]", in_forbidden_ctx)


def _scalars(value):
    """能力声明可能写成字符串、字符串数组，或带 capability_id 的对象数组。"""
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            if isinstance(item, str):
                yield item
            elif isinstance(item, dict):
                for key in ("capability_id", "id", "name"):
                    if isinstance(item.get(key), str):
                        yield item[key]
    elif isinstance(value, dict):
        for key in ("capability_id", "id"):
            if isinstance(value.get(key), str):
                yield value[key]


def _is_own_fixture(rel: str, doc) -> bool:
    """只有 ci/fixtures/ 下、checker 字段指向本 checker 的文件，才算「自己的测试数据」。"""
    return rel.startswith(FIXTURE_ROOT) and isinstance(doc, dict) and doc.get("checker") == LABEL


def scan(documents: dict, forbidden: set[str]) -> list[dict]:
    """纯函数形式的扫描：输入已解析文档，输出命中列表。夹具可以直接驱动它。"""
    hits: list[dict] = []
    for rel, doc in sorted(documents.items()):
        _walk(doc, forbidden, rel, hits)
    return hits


def _validate_scan_coverage(payload: dict, errors: list[str]) -> None:
    """NB-M2-03：覆盖面数字必须是记录值，且当前值现算比对。

    「扫了多少份」写错不改变零命中这个结论，但会让审查者对覆盖面形成错误印象——
    而覆盖面正是判断「零命中值不值钱」的唯一依据。
    """
    record = payload.get("scan_coverage_record")
    if record is None:
        errors.append("SCAN_COVERAGE_RECORD_MISSING: the contract records no scan coverage at all")
        return
    declared = record.get("declared_current_count")
    actual = record.get("actual_current_count")
    if declared != actual:
        errors.append(
            f"SCAN_COVERAGE_COUNT_MISSTATED: contract records {declared!r} scanned files, "
            f"the scan actually walked {actual!r}"
        )
    for row in record.get("history") or []:
        if not is_full_commit_hash(row.get("measured_at_commit")):
            errors.append(
                f"SCAN_COVERAGE_HISTORY_UNBOUND: history entry for {row.get('package')!r} "
                f"records {row.get('measured_at_commit')!r}, which is not a full commit hash"
            )
        if row.get("evidence_level") != "runtime_verified":
            errors.append(
                f"SCAN_COVERAGE_HISTORY_UNMEASURED: history entry for {row.get('package')!r} "
                f"claims evidence_level={row.get('evidence_level')!r}, coverage counts must be measured"
            )


def _scan_coverage_payload(contract: dict, actual: int) -> dict | None:
    record = contract.get("scan_coverage_record")
    if record is None:
        return None
    return {
        "declared_current_count": (record.get("current") or {}).get("scanned_file_count"),
        "actual_current_count": actual,
        "history": record.get("history") or [],
    }


def collect() -> dict:
    import json

    import yaml

    contract = load_yaml(CONTRACT)
    forbidden = [item["capability_id"] for item in contract["forbidden_capabilities"]["items"]]
    allowed = [item["capability_id"] for item in contract["allowed_capabilities"]["items"]]

    documents: dict[str, dict] = {}
    own_fixture_exemptions: list[str] = []
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in SCANNED_SUFFIXES:
            continue
        if ".git" in path.parts:
            continue
        rel = str(path.relative_to(ROOT))
        if rel.startswith(IDENTITY_CASE_DIR + "/"):
            continue  # 见 IDENTITY_CASE_DIR：改由 scan_cases 逐条断言
        try:
            text = path.read_text(encoding="utf-8")
            doc = json.loads(text) if path.suffix.lower() == ".json" else yaml.safe_load(text)
        except (UnicodeDecodeError, OSError, ValueError, yaml.YAMLError):
            continue
        if not isinstance(doc, (dict, list)):
            continue
        if _is_own_fixture(rel, doc):
            own_fixture_exemptions.append(rel)
            continue
        documents[rel] = doc

    scan_cases = []
    for path in sorted((ROOT / IDENTITY_CASE_DIR).glob("*.json")):
        case = json.loads(path.read_text(encoding="utf-8"))
        hits = scan(case["documents"], set(forbidden))
        scan_cases.append(
            {
                "case_id": case["case_id"],
                "expected_hits": case["expected_hits"],
                "actual_hits": len(hits),
                "detail": ", ".join(f"{h['capability']}@{h['location']}" for h in hits) or "<no hit>",
            }
        )

    return {
        "own_fixture_exemptions": sorted(own_fixture_exemptions),
        "scan_cases": scan_cases,
        "contract": {
            "activation_condition_is_never": contract["contract"]["activation_condition_is_never"],
        },
        "forbidden_capabilities": forbidden,
        "forbidden_capabilities_declared_count": contract["forbidden_capabilities"]["count"],
        "allowed_capabilities": allowed,
        "scan_coverage_record": _scan_coverage_payload(contract, len(documents)),
        "scanned_file_count": len(documents),
        "forbidden_capability_declarations": scan(documents, set(forbidden)),
        "current_state": contract["current_state"],
    }


if __name__ == "__main__":
    cli(LABEL, collect, validate)
