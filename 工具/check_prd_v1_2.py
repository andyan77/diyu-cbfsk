#!/usr/bin/env python3
"""Contract checker for the PRD v1.2 documentation baseline."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from docx import Document


ROOT = Path(__file__).resolve().parent.parent
PRD = ROOT / "笛语跨品牌服装搭配专家内核_PRD与执行里程碑_v1.2.docx"
M0 = ROOT / "笛语跨品牌服装搭配专家内核_M0执行申请_v1.2.docx"
RECEIPT = ROOT / "PRD_v1.2_核验回执.docx"
README = ROOT / "README.md"
CHANGE_MAP = ROOT / "PRD_v1.2_change_map.yaml"


FORBIDDEN = [
    "V1.0全生命周期保持人工审核在环",
    "所有商业发布门通过后仍不得自动发布",
    "图像识别属性提取不属于V1.0",
    "商品属性只能来自PIM/ERP，图片不得参与",
    "完整陈列能力永久退出",
    "实时导购能力永久退出",
    "人设仅由账号语气合同承担",
    "叙事质量等同于自媒体语感",
]

M0_ITEMS = [
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


class Checker:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.passes: list[str] = []

    def check(self, condition: bool, label: str, detail: str = "") -> None:
        if condition:
            self.passes.append(label)
        else:
            self.errors.append(label + (f": {detail}" if detail else ""))

    def contains_all(self, text: str, tokens: list[str], label: str) -> None:
        missing = [token for token in tokens if token not in text]
        self.check(not missing, label, f"missing={missing}")


def document_text(doc: Document) -> str:
    chunks = [paragraph.text for paragraph in doc.paragraphs]
    for table in doc.tables:
        for row in table.rows:
            chunks.extend(cell.text for cell in row.cells)
    for section in doc.sections:
        chunks.extend(paragraph.text for paragraph in section.header.paragraphs)
        chunks.extend(paragraph.text for paragraph in section.footer.paragraphs)
    return "\n".join(chunks)


def table_by_second_row(doc: Document, value: str):
    return next(table for table in doc.tables if len(table.rows) > 1 and table.cell(1, 0).text.strip() == value)


def ids_from_table(doc: Document, first_id: str, prefix: str) -> list[int]:
    table = table_by_second_row(doc, first_id)
    result: list[int] = []
    for row in table.rows[1:]:
        match = re.fullmatch(rf"{re.escape(prefix)}-(\d+)", row.cells[0].text.strip())
        if match:
            result.append(int(match.group(1)))
    return result


def heading_region(doc: Document, start: str, end: str) -> list[str]:
    paragraphs = doc.paragraphs
    start_index = next(i for i, paragraph in enumerate(paragraphs) if paragraph.text.strip() == start)
    end_index = next(i for i, paragraph in enumerate(paragraphs) if paragraph.text.strip() == end and i > start_index)
    return [paragraph.text.strip() for paragraph in paragraphs[start_index + 1 : end_index]]


def check_m0_lists(checker: Checker, prd: Document, m0: Document) -> None:
    regions = [
        heading_region(prd, "M0｜独立立项与合同冻结", "M1｜语义骨架与品类适配合同"),
        heading_region(prd, "M0 独立立项与合同冻结", "M1 语义骨架与品类适配合同"),
        heading_region(prd, "17.1 首任务必须交付", "17.2 执行纪律"),
    ]
    lists: list[list[str]] = []
    for region in regions:
        items = [line[4:] for line in region if line.startswith("[ ] ")]
        lists.append(items[:14])
    expected = M0_ITEMS
    for index, items in enumerate(lists, start=1):
        checker.check(len(items) == 14, f"PRD M0 list {index} has 14 items", repr(items))
        checker.check(items == expected, f"PRD M0 list {index} matches canonical list", repr(items))

    app_items = [row.cells[1].text.strip() for row in m0.tables[1].rows[1:]]
    checker.check(len(app_items) == 14, "M0 application has 14 items", repr(app_items))
    expected_application = [item.split("（", 1)[0] for item in expected]
    checker.check(app_items == expected_application, "M0 application matches canonical list", repr(app_items))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-archive", action="store_true")
    args = parser.parse_args()
    checker = Checker()

    for path in (PRD, M0, RECEIPT, README, CHANGE_MAP):
        checker.check(path.exists(), f"file exists: {path.name}")
    if checker.errors:
        for error in checker.errors:
            print("FAIL", error)
        sys.exit(1)

    prd = Document(PRD)
    m0 = Document(M0)
    receipt = Document(RECEIPT)
    prd_text = document_text(prd)
    m0_text = document_text(m0)
    receipt_text = document_text(receipt)
    readme_text = README.read_text(encoding="utf-8")
    map_text = CHANGE_MAP.read_text(encoding="utf-8")

    checker.contains_all(
        prd_text,
        [
            "PRD v1.2 · 人设连续性、多模态商品理解与扩展兼容基线",
            "PROJECT_INITIATED / EXECUTION_NOT_STARTED / M0_AUTHORIZED_FALSE",
            "production_servable",
            "待Founder签署生效",
        ],
        "document status and version",
    )
    headers = "\n".join(paragraph.text for section in prd.sections for paragraph in section.header.paragraphs)
    checker.check("PRD v1.2" in headers and "PRD v1.0" not in headers and "PRD v1.1" not in headers, "PRD header version is current", headers)
    for phrase in FORBIDDEN:
        checker.check(phrase not in prd_text, f"forbidden phrase absent: {phrase}")

    checker.check(ids_from_table(prd, "G-01", "G") == list(range(1, 15)), "G IDs are consecutive G-01..G-14")
    checker.check(ids_from_table(prd, "C-01", "C") == list(range(1, 16)), "C IDs are consecutive C-01..C-15")
    checker.check(ids_from_table(prd, "FR-01", "FR") == list(range(1, 30)), "FR IDs are consecutive FR-01..FR-29")
    checker.check(ids_from_table(prd, "NFR-01", "NFR") == list(range(1, 13)), "NFR IDs are consecutive NFR-01..NFR-12")
    checker.check(ids_from_table(prd, "R-01", "R") == list(range(1, 22)), "risk IDs are consecutive R-01..R-21")

    inputs = table_by_second_row(prd, "UniversalExpertKernel")
    outputs = table_by_second_row(prd, "BrandAudienceInterpretation")
    checker.check(len(inputs.rows) - 1 == 12, "input/configuration object count is 12", str(len(inputs.rows) - 1))
    checker.check(len(outputs.rows) - 1 == 15, "output/audit object count is 15", str(len(outputs.rows) - 1))
    checker.contains_all(prd_text, ["ProductImageAssetBundle", "StylistPersonaProfile", "PersonaMemorySnapshot", "FounderProvidedRealBrandPackage", "PublicationPolicy"], "new input/configuration objects")
    checker.contains_all(prd_text, ["VisualAttributeExtractionResult", "PersonaContinuityUpdate", "SocialMediaVoicePlan", "PublicationDecision"], "new output/audit objects")

    checker.contains_all(prd_text, ["C-13", "Stylist Persona Continuity Intelligence", "C-14", "Social-Media Native Voice Intelligence", "C-15", "Multimodal Garment Understanding"], "formal capabilities C-13..C-15")
    checker.contains_all(prd_text, ["VisualMerchandisingExtensionPort", "StoreSpaceContext", "PlanogramContext", "RealtimeSalesAssistExtensionPort", "SalesAssociateSessionContext", "RealtimeRecommendationResult"], "extension-compatible contracts")
    checker.contains_all(prd_text, ["publication_mode=human_review", "publication_mode=founder_authorized_auto_publish", "PublicationPolicyController", "AutoPublishKillSwitch", "unauthorized_auto_publish_rate = 0"], "Founder-controlled publication contract")
    checker.contains_all(prd_text, ["authoritative_structured_fact", "human_verified_visual_attribute", "multimodal_inferred_visual_attribute", "authoritative_fact_override_rate = 0", "unverifiable_function_claim_rate = 0"], "multimodal evidence grading and hard gates")

    fr_table = table_by_second_row(prd, "FR-01")
    for number in range(22, 30):
        row = next(row for row in fr_table.rows if row.cells[0].text.strip() == f"FR-{number}")
        acceptance = row.cells[3].text
        checker.check(all(token in acceptance for token in ("验收：", "失败状态：", "里程碑：")), f"FR-{number} has acceptance/failure/milestone trace", acceptance)

    checker.contains_all(prd_text, ["stylist_persona_profile.schema.v0.1.json", "product_image_asset_bundle.schema.v0.1.json", "publication_policy.schema.v0.1.json", "extension_port_contracts", "12个输入与配置对象", "15个输出与内部审计对象"], "M1 schema and object mapping")
    checker.contains_all(prd_text, ["persona_continuity_scoring_rubric", "social_media_native_voice_scoring_rubric", "multimodal_attribute_benchmark", "multimodal_confidence_calibration_contract", "five_category_readiness_definition", "M2_FREEZE_REQUIRED"], "M2 evaluation additions")
    checker.contains_all(prd_text, ["persona_consistency_checker", "social_media_native_voice_checker", "anti_template_checker", "persona_and_voice_qualification_report"], "M7 deliverables")
    checker.contains_all(prd_text, ["FounderProvidedRealBrandPackage", "FounderInjectedRealBrandProductionTest", "founder_provided_real_brand_package_manifest", "founder_real_brand_test_production_report", "multimodal_product_understanding_report", "founder_capability_assessment_receipt", "founder_real_brand_package_provided=false", "fallback_source=codex_synthetic_fixture"], "M11 dual paths and conditional evidence")
    checker.contains_all(prd_text, ["five_category_activation_readiness=100%", "five_category_activation_readiness_report", "persona_state_versioning_and_rollback", "auto_publish_kill_switch_contract", "extension_port_registry"], "M12 readiness and governance")

    checker.contains_all(prd_text, ["R-15", "R-16", "R-17", "R-18", "R-19", "R-20", "R-21"], "risk additions R-15..R-21")
    checker.contains_all(prd_text, ["多模态推断覆盖权威", "未经Founder授权启用自动发布", "人设虚构履历", "Founder注入数据进入隐藏集", "扩展模块破坏现有输出Schema"], "new stop conditions")

    required_terms = ["Stylist Persona Continuity", "Social-Media Native Voice", "Persona Memory Snapshot", "Published Viewpoint Ledger", "Multimodal Garment Understanding", "Visual Attribute Provenance", "FounderProvidedRealBrandPackage", "FounderInjectedRealBrandProductionTest", "Publication Policy", "Visual Merchandising Extension Port", "Realtime Sales Assist Extension Port", "Five-category Activation Readiness"]
    term_table = next(table for table in prd.tables if table.cell(0, 0).text.strip() == "术语")
    term_text = "\n".join(cell.text for row in term_table.rows for cell in row.cells)
    checker.contains_all(term_text, required_terms, "all new terms are in glossary")

    check_m0_lists(checker, prd, m0)
    checker.contains_all(m0_text, ["DIYU-CBFSK-EXEC-REQ-M0-003", "PRD v1.2", "M0不得实际接收", "M0不得运行多模态", "M0不得建立搭配师人设记忆生产库", "M0不得启用自动发布", "人设与语感闭环", "多模态事实边界", "扩展兼容"], "M0 v1.2 control and Guardian additions")
    checker.contains_all(receipt_text, ["DIYU-CBFSK-PRD-V1.2-VERIFY-RECEIPT-001", "D-17", "D-26", "READY_FOR_FOUNDER_REVIEW", "m0_authorized: false", "production_servable: false"], "verification receipt identifiers and final state")

    checker.contains_all(readme_text, ["当前唯一产品真源", "PRD v1.2", "DIYU-CBFSK-EXEC-REQ-M0-003", "待 Founder 签署", "归档_v1.1/", "Founder真实品牌注入", "Codex夹具合成回退", "多模态商品图片理解", "人设连续性", "自媒体原生语感", "VisualMerchandisingExtensionPort", "RealtimeSalesAssistExtensionPort", "five_category_activation_readiness=100%"], "README current-baseline index")
    checker.contains_all(map_text, ["D-17:", "D-26:", "m0_top_level_deliverable_count: 14", "input_and_configuration_objects: 12", "output_and_internal_audit_objects: 15", "documentation_status: READY_FOR_FOUNDER_REVIEW"], "machine-readable change map")

    if args.require_archive:
        archive = ROOT / "归档_v1.1"
        checker.check(archive.is_dir(), "v1.1 archive directory exists")
        for name in ["笛语跨品牌服装搭配专家内核_PRD与执行里程碑_v1.1.docx", "笛语跨品牌服装搭配专家内核_M0执行申请_v1.1.docx", "PRD_v1.1_核验回执.docx"]:
            checker.check((archive / name).is_file(), f"archived: {name}")
            checker.check(not (ROOT / name).exists(), f"v1.1 removed from root: {name}")

    for label in checker.passes:
        print("PASS", label)
    if checker.errors:
        for error in checker.errors:
            print("FAIL", error)
        print(f"RESULT FAIL: {len(checker.errors)} error(s), {len(checker.passes)} pass(es)")
        sys.exit(1)
    print(f"RESULT PASS: {len(checker.passes)} checks")


if __name__ == "__main__":
    main()
