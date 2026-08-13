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
import re
import sys
import unicodedata
from pathlib import Path
from xml.etree import ElementTree
from zipfile import ZipFile

import yaml

ROOT = Path(__file__).resolve().parent.parent.parent

W_NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

UUID_V4_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


def load_yaml(rel: str) -> dict:
    return yaml.safe_load((ROOT / rel).read_text(encoding="utf-8"))


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
