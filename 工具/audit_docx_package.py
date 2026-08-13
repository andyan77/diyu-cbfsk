#!/usr/bin/env python3
"""Audit DOCX ZIP/OOXML integrity and version-bearing parts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from xml.etree import ElementTree
from zipfile import BadZipFile, ZipFile


def audit(path: Path, required_version: str | None) -> list[str]:
    errors: list[str] = []
    try:
        with ZipFile(path) as archive:
            bad_member = archive.testzip()
            if bad_member:
                errors.append(f"CRC failure: {bad_member}")
            names = set(archive.namelist())
            for required in ("[Content_Types].xml", "_rels/.rels", "word/document.xml"):
                if required not in names:
                    errors.append(f"missing required member: {required}")
            for name in sorted(names):
                if name.endswith((".xml", ".rels")):
                    try:
                        ElementTree.fromstring(archive.read(name))
                    except ElementTree.ParseError as exc:
                        errors.append(f"invalid XML {name}: {exc}")
            if required_version:
                header_names = sorted(name for name in names if name.startswith("word/header") and name.endswith(".xml"))
                if not header_names:
                    errors.append("no header XML part")
                else:
                    for name in header_names:
                        text = archive.read(name).decode("utf-8", errors="replace")
                        if required_version not in text:
                            errors.append(f"{name} does not contain {required_version}")
                        for stale in ("PRD v1.0", "PRD v1.1"):
                            if stale in text:
                                errors.append(f"{name} contains stale version {stale}")
    except (BadZipFile, OSError) as exc:
        errors.append(str(exc))
    return errors


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("docx", nargs="+", type=Path)
    parser.add_argument("--required-version", default="v1.2")
    args = parser.parse_args()

    failed = False
    for path in args.docx:
        errors = audit(path, args.required_version)
        if errors:
            failed = True
            print(f"FAIL {path}")
            for error in errors:
                print(f"  - {error}")
        else:
            print(f"PASS {path}: ZIP CRC, required parts, XML parse, header version")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
