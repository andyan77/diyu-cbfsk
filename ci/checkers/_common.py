#!/usr/bin/env python3
"""Shared helpers for deterministic governance checkers.

Design rule (anti self-green): every checker splits into
  collect() -> payload   # reads the real repository
  validate(payload) -> list[str]   # pure predicate over the payload
so fixtures can drive validate() with independent literal data that never
reuses the code under test to build its own ground truth.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path
from xml.etree import ElementTree
from zipfile import ZipFile

import yaml

ROOT = Path(__file__).resolve().parent.parent.parent

W_NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

# canonical 层：排除 Word 封装元数据与易变编辑标识；其余 XML/RELS 部件按名称排序后递归序列化。
CANONICAL_EXCLUDED_PARTS = ("docProps/core.xml", "docProps/app.xml")
CANONICAL_VOLATILE_ATTR = re.compile(r"\{[^}]*\}(rsid[A-Za-z]*|paraId|textId)$")

UUID_V4_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


def load_yaml(rel: str) -> dict:
    return yaml.safe_load((ROOT / rel).read_text(encoding="utf-8"))


def load_json(rel: str) -> dict:
    """JSON 与 YAML 走同一条读法：路径相对仓根，读失败就让它抛，不吞异常。"""
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def read_text(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def docx_paragraph_texts(path: Path) -> list[str]:
    """Extract paragraph and table-cell texts from word/document.xml without python-docx."""
    with ZipFile(path) as archive:
        xml = archive.read("word/document.xml")
    root = ElementTree.fromstring(xml)
    out: list[str] = []
    for para in root.iter(f"{W_NS}p"):
        text = "".join(node.text or "" for node in para.iter(f"{W_NS}t"))
        text = text.strip()
        if text:
            out.append(text)
    return out


def docx_table_column(path: Path, header: tuple[str, ...], column: int) -> list[str]:
    """Return one column of the first table whose header row matches `header` exactly."""
    with ZipFile(path) as archive:
        root = ElementTree.fromstring(archive.read("word/document.xml"))
    for tbl in root.iter(f"{W_NS}tbl"):
        rows = []
        for tr in tbl.iter(f"{W_NS}tr"):
            cells = []
            for tc in tr.iter(f"{W_NS}tc"):
                text = "".join(node.text or "" for node in tc.iter(f"{W_NS}t")).strip()
                cells.append(text)
            rows.append(cells)
        if rows and tuple(rows[0][: len(header)]) == header:
            return [r[column].strip() for r in rows[1:] if len(r) > column]
    raise ValueError(f"no table headed {header} in {path.name}")


def docx_all_text(path: Path) -> str:
    return "\n".join(docx_paragraph_texts(path))


def _canonical_element(elem: ElementTree.Element) -> str:
    attrs = "".join(
        f" {k}={v!r}"
        for k, v in sorted(elem.attrib.items())
        if not CANONICAL_VOLATILE_ATTR.search(k)
    )
    text = (elem.text or "").strip()
    body = "".join(_canonical_element(child) for child in elem)
    return f"<{elem.tag}{attrs}>{text}{body}</{elem.tag}>"


def canonical_docx_xml_sha256(path: Path) -> str:
    """Structural hash over the DOCX XML parts. See hash_contract in the pinned baseline manifest.

    This is the single implementation of the canonical layer; nothing may re-derive it elsewhere.
    """
    chunks: list[str] = []
    with ZipFile(path) as archive:
        for name in sorted(archive.namelist()):
            if name in CANONICAL_EXCLUDED_PARTS or not name.endswith((".xml", ".rels")):
                continue
            root = ElementTree.fromstring(archive.read(name))
            chunks.append(f"<<{name}>>" + _canonical_element(root))
    return sha256_text("".join(chunks))


def semantic_text_sha256(path: Path) -> str:
    """NFKC-normalised, whitespace-collapsed text hash over body then headers/footers."""
    parts: list[str] = []
    with ZipFile(path) as archive:
        names = archive.namelist()
        ordered = ["word/document.xml"]
        ordered += sorted(n for n in names if re.fullmatch(r"word/(header|footer)\d+\.xml", n))
        for name in ordered:
            if name not in names:
                continue
            root = ElementTree.fromstring(archive.read(name))
            parts.append(f"<<PART:{name}>>")
            for para in root.iter(f"{W_NS}p"):
                text = "".join(node.text or "" for node in para.iter(f"{W_NS}t"))
                text = unicodedata.normalize("NFKC", text)
                text = re.sub(r"\s+", " ", text).strip()
                if text:
                    parts.append(text)
    return sha256_text("\n".join(parts))


def report(label: str, errors: list[str]) -> int:
    if errors:
        for err in errors:
            print(f"FAIL {label}: {err}")
        print(f"RESULT FAIL {label}: {len(errors)} error(s)")
        return 1
    print(f"PASS {label}")
    return 0


def run_checker(label: str, collect, validate) -> int:
    try:
        payload = collect()
    except Exception as exc:  # noqa: BLE001 - surfaced as a checker failure, never swallowed
        print(f"FAIL {label}: collect() raised {type(exc).__name__}: {exc}")
        print(f"RESULT FAIL {label}: 1 error(s)")
        return 1
    return report(label, validate(payload))


def cli(label: str, collect, validate) -> None:
    sys.exit(run_checker(label, collect, validate))


COMMIT_HASH_RE = re.compile(r"[0-9a-f]{40}")


def is_full_commit_hash(value) -> bool:
    """A commit reference must resolve to exactly one object.

    Abbreviations and run UUIDs are rejected for the same reason 「最新版」 is rejected:
    a reference that cannot be resolved to one exact object is not a reference.
    This is the single implementation — checkers import it, none re-derive it.
    """
    return isinstance(value, str) and COMMIT_HASH_RE.fullmatch(value) is not None
