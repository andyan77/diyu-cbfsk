#!/usr/bin/env python3
"""Three-layer DOCX comparison: binary / canonical XML / semantic text.

Classification contract:
  binary_equal                              -> identical file
  binary_different_but_canonical_equal      -> PACKAGING_ONLY_DIFFERENCE (Founder confirmation required)
  canonical_different                       -> structural or content difference
  semantic_different                        -> PRODUCT_BASELINE_SEMANTIC_CONFLICT (stop)
"""

from __future__ import annotations

import re
from xml.etree import ElementTree
from zipfile import BadZipFile, ZipFile

from _common import ROOT, cli, load_yaml, semantic_text_sha256, sha256_file, sha256_text

LABEL = "check_docx_canonical_hashes"

VOLATILE_ATTR = re.compile(r"\{[^}]*\}(rsid[A-Za-z]*|paraId|textId)$")
EXCLUDED_PARTS = {"docProps/core.xml", "docProps/app.xml"}


def _canonical_element(elem: ElementTree.Element) -> str:
    attrs = "".join(
        f" {k}={v!r}" for k, v in sorted(elem.attrib.items()) if not VOLATILE_ATTR.search(k)
    )
    text = (elem.text or "").strip()
    body = "".join(_canonical_element(child) for child in elem)
    return f"<{elem.tag}{attrs}>{text}{body}</{elem.tag}>"


def canonical_docx_xml_sha256(path) -> str:
    chunks: list[str] = []
    with ZipFile(path) as archive:
        for name in sorted(archive.namelist()):
            if name in EXCLUDED_PARTS or not name.endswith((".xml", ".rels")):
                continue
            root = ElementTree.fromstring(archive.read(name))
            chunks.append(f"<<{name}>>" + _canonical_element(root))
    return sha256_text("".join(chunks))


def classify(binary_equal: bool, canonical_equal: bool, semantic_equal: bool) -> str:
    if binary_equal:
        return "BINARY_EQUAL"
    if canonical_equal and semantic_equal:
        return "PACKAGING_ONLY_DIFFERENCE"
    if not semantic_equal:
        return "PRODUCT_BASELINE_SEMANTIC_CONFLICT"
    return "CANONICAL_DIFFERENT"


def validate(payload: dict) -> list[str]:
    errors: list[str] = []
    for item in payload.get("integrity") or []:
        if item.get("errors"):
            errors.append(f"DOCX_PACKAGE_INVALID: {item['file']}: {'; '.join(item['errors'])}")

    for cmp_ in payload.get("comparisons") or []:
        verdict = classify(cmp_["binary_equal"], cmp_["canonical_equal"], cmp_["semantic_equal"])
        expected = cmp_.get("expected_classification")
        if expected and verdict != expected:
            errors.append(f"CLASSIFICATION_MISMATCH: {cmp_['file']} computed {verdict}, expected {expected}")
        if verdict == "PRODUCT_BASELINE_SEMANTIC_CONFLICT":
            errors.append(f"PRODUCT_BASELINE_SEMANTIC_CONFLICT: {cmp_['file']} differs semantically; Founder ruling required")
        if verdict == "PACKAGING_ONLY_DIFFERENCE" and not cmp_.get("founder_confirmation_required"):
            errors.append(
                f"MISSING_FOUNDER_CONFIRMATION_FLAG: {cmp_['file']} is packaging-only different and must require Founder confirmation"
            )
        if verdict == "CANONICAL_DIFFERENT":
            errors.append(f"CANONICAL_DIFFERENT: {cmp_['file']} has structural differences that were not adjudicated")
    return errors


def _integrity(path) -> list[str]:
    errors: list[str] = []
    try:
        with ZipFile(path) as archive:
            bad = archive.testzip()
            if bad:
                errors.append(f"CRC failure at {bad}")
            names = set(archive.namelist())
            for required in ("[Content_Types].xml", "_rels/.rels", "word/document.xml"):
                if required not in names:
                    errors.append(f"missing required member {required}")
            for name in sorted(names):
                if name.endswith((".xml", ".rels")):
                    try:
                        ElementTree.fromstring(archive.read(name))
                    except ElementTree.ParseError as exc:
                        errors.append(f"invalid XML {name}: {exc}")
    except BadZipFile as exc:
        errors.append(f"not a valid zip: {exc}")
    return errors


def collect() -> dict:
    manifest = load_yaml("governance/baseline/founder_pinned_baseline.v0.1.yaml")
    comparisons = []
    integrity = []
    for candidate in manifest["active_baseline_candidates"]:
        rel = candidate["repository_path"]
        if not rel.endswith(".docx"):
            continue
        path = ROOT / rel
        integrity.append({"file": rel, "errors": _integrity(path)})
        comparisons.append(
            {
                "file": rel,
                "binary_equal": sha256_file(path) == candidate["binary_sha256"],
                "canonical_equal": canonical_docx_xml_sha256(path) == candidate["canonical_docx_xml_sha256"],
                "semantic_equal": semantic_text_sha256(path) == candidate["semantic_text_sha256"],
                "expected_classification": "BINARY_EQUAL",
                "founder_confirmation_required": True,
            }
        )
    for rel in (
        "笛语跨品牌服装搭配专家内核_PRD与执行里程碑_v1.2.docx",
        "笛语跨品牌服装搭配专家内核_M0执行申请_v1.2.docx",
        "PRD_v1.2_核验回执.docx",
    ):
        integrity.append({"file": rel, "errors": _integrity(ROOT / rel)})
    return {"comparisons": comparisons, "integrity": integrity}


if __name__ == "__main__":
    cli(LABEL, collect, validate)
