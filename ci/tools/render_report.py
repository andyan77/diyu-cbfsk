#!/usr/bin/env python3
"""报告渲染器：报告里的计数数字由生成时从机器记录现读，不由人手抄。

NB-M2E4-03 的形态是这样的：EP04 报告写「500 条声明码，350 条有夹具，149 条挂账」，
台账实测是 523/376/147——而且 500−350≠149，三个数字彼此都对不上。
根因不是手抄错了一次，是报告里的数字与台账之间根本没有连线。

因此报告改为模板 + 引用：

    {{ref:governance/gates/error_code_fixture_coverage_ledger.v0.1.yaml#measurement.declared_codes_total}}

渲染时现读该字段。判据再把模板重新渲染一遍与落盘报告逐字节比对——
台账变了而报告没重渲染，比对当场失败；想改数字只能去改台账，改不动报告本身。

render() 同时返回每个引用在渲染结果里的字符区间，
判据据此判断「报告里的每一个计数数字是不是都从引用来的」。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent.parent
REF_OPEN = "{{ref:"
REF_CLOSE = "}}"
# 转义：模板要展示引用语法本身时写 {{!ref:...}}，渲染成字面量且不参与计数溯源。
REF_ESCAPED = "{{!ref:"


class RefError(RuntimeError):
    """引用解析失败：路径不存在、键路径解不出、或值不是标量。"""


def resolve(ref: str):
    """解析 `<相对路径>#<点分键路径>`，返回该字段的值。"""
    if "#" not in ref:
        raise RefError(f"{ref!r} lacks the '#' between path and field")
    rel, dotted = ref.split("#", 1)
    path = ROOT / rel
    if not path.exists():
        raise RefError(f"{rel!r} does not exist")
    node = yaml.safe_load(path.read_text(encoding="utf-8"))
    for key in dotted.split("."):
        if isinstance(node, list):
            try:
                node = node[int(key)]
                continue
            except (ValueError, IndexError) as exc:
                raise RefError(f"{ref!r}: list index {key!r} does not resolve") from exc
        if not isinstance(node, dict) or key not in node:
            raise RefError(f"{ref!r}: {key!r} does not resolve")
        node = node[key]
    if isinstance(node, (dict, list)):
        raise RefError(f"{ref!r} resolves to a {type(node).__name__}, not a scalar")
    return node


def render(template: str) -> tuple[str, list[tuple[int, int, str]]]:
    """把模板里的引用换成实读值；返回 (渲染文本, [(起, 止, 引用)])。"""
    out: list[str] = []
    spans: list[tuple[int, int, str]] = []
    cursor = 0
    length = 0
    while True:
        plain = template.find(REF_OPEN, cursor)
        escaped = template.find(REF_ESCAPED, cursor)
        start = min(x for x in (plain, escaped) if x != -1) if (plain != -1 or escaped != -1) else -1
        if start == -1:
            out.append(template[cursor:])
            break
        out.append(template[cursor:start])
        length += start - cursor
        end = template.find(REF_CLOSE, start)
        if end == -1:
            raise RefError(f"unterminated reference starting at offset {start}")
        if start == escaped:
            literal = REF_OPEN + template[start + len(REF_ESCAPED):end] + REF_CLOSE
            out.append(literal)
            length += len(literal)
            cursor = end + len(REF_CLOSE)
            continue
        ref = template[start + len(REF_OPEN):end]
        value = str(resolve(ref))
        out.append(value)
        spans.append((length, length + len(value), ref))
        length += len(value)
        cursor = end + len(REF_CLOSE)
    return "".join(out), spans


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("template", help="模板路径（相对仓根或绝对路径）")
    parser.add_argument("-o", "--output", help="输出路径；缺省为去掉 .tmpl 后缀")
    args = parser.parse_args()

    template_path = Path(args.template)
    if not template_path.is_absolute():
        template_path = ROOT / template_path
    text, _ = render(template_path.read_text(encoding="utf-8"))
    output = Path(args.output) if args.output else Path(str(template_path)[: -len(".tmpl")])
    if not output.is_absolute():
        output = ROOT / output
    output.write_text(text, encoding="utf-8")
    print(f"rendered {template_path.relative_to(ROOT)} -> {output.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
