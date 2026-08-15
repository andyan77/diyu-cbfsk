#!/usr/bin/env python3
"""Founder 确认类字段：不得是执行侧一键可改的裸布尔值。

被守的一方自己就能开门——这是本判据要堵的洞。一个 `founder_merge_approved: false`
改成 `true` 只要一次键盘操作，事后也看不出是谁在哪个版本上批的。因此凡是声称
「Founder 已确认／已批准／已授权／已签署」的布尔字段，值为真时必须挂上四样东西：
具名文件（存在）、该文件里解析得出来的条款路径、完整 40 位签署基线 Commit、签署人与签署时点。

分类是显式的，不靠关键字自动归类：说「需要 Founder 批」的是要求，说「没有被授权」的是否定，
对 git 事实的观测是派生态——这三类不是在声称 Founder 做过什么，因此不要求绑定。
但每一个站点都必须在登记册里具名出现并写明属于哪一类；没登记的站点一律判失败，
新加一个未登记的确认位不会悄悄溜过去。

值也要对齐：登记时是 false 的站点后来被改成 true 而没补绑定，判 CONFIRMATION_VALUE_DRIFT。
「登记过了」不等于「可以随便改」。
"""

from __future__ import annotations

import yaml

from _common import ROOT, cli, clause_resolves, is_full_commit_hash, load_yaml

LABEL = "check_founder_confirmation_binding"

REGISTRY = "governance/gates/founder_confirmation_binding_registry.v0.1.yaml"

CLAIM_KINDS = (
    "founder_act_claim", "requirement", "capability", "negation", "eligibility",
    "derived_state", "discipline_acknowledgement", "inside_founder_ruling",
    "inside_founder_signature_record",
)
BINDING_FIELDS = (
    "authority_kind", "authority_ref", "authority_file", "authority_clause_path",
    "signature_base_commit", "signed_by", "signed_at",
)


def _key_is_site(key: str, stems: set[str]) -> bool:
    return bool(set(str(key).lower().split("_")) & stems)


def _walk(node, stems: set[str], path: str = ""):
    if isinstance(node, dict):
        for key, value in node.items():
            child = f"{path}.{key}" if path else str(key)
            if isinstance(value, bool) and _key_is_site(key, stems):
                yield child, value
            else:
                yield from _walk(value, stems, child)
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from _walk(value, stems, f"{path}[{index}]")


def validate(payload: dict) -> list[str]:
    errors: list[str] = []

    scope = payload.get("declared_scope") or {}
    for prefix in payload.get("actual_excluded_prefixes") or []:
        if prefix not in (scope.get("excluded_prefixes") or []):
            errors.append(f"CONFIRMATION_SCAN_SCOPE_NARROWED: the scan skips {prefix!r}, the registry does not declare it")
    for stem in scope.get("key_stems") or []:
        if stem not in (payload.get("actual_key_stems") or []):
            errors.append(f"CONFIRMATION_SCAN_SCOPE_NARROWED: the registry declares stem {stem!r}, the scan does not use it")

    registered = {(s.get("file"), s.get("key_path")): s for s in payload.get("registered_sites") or []}
    discovered = {(s.get("file"), s.get("key_path")): s for s in payload.get("discovered_sites") or []}

    for key, site in discovered.items():
        if key not in registered:
            errors.append(
                f"CONFIRMATION_FIELD_NOT_REGISTERED: {site['file']} :: {site['key_path']} "
                f"claims a Founder act with no registry entry"
            )
    for key, entry in registered.items():
        if key not in discovered:
            errors.append(
                f"CONFIRMATION_REGISTRY_ENTRY_ORPHANED: the registry lists {entry.get('file')} :: "
                f"{entry.get('key_path')}, the scan finds no such field"
            )
            continue
        if entry.get("claim_kind") not in CLAIM_KINDS:
            errors.append(
                f"CONFIRMATION_CLAIM_KIND_INVALID: {entry.get('file')} :: {entry.get('key_path')} "
                f"is classified {entry.get('claim_kind')!r}"
            )
        actual_value = discovered[key].get("value")
        if entry.get("value_when_registered") != actual_value:
            errors.append(
                f"CONFIRMATION_VALUE_DRIFT: {entry.get('file')} :: {entry.get('key_path')} was registered as "
                f"{entry.get('value_when_registered')!r}, now reads {actual_value!r}"
            )

        if entry.get("claim_kind") != "founder_act_claim" or actual_value is not True:
            continue

        binding = entry.get("binding")
        if not isinstance(binding, dict):
            errors.append(
                f"FOUNDER_CONFIRMATION_UNBOUND: {entry.get('file')} :: {entry.get('key_path')} is true "
                "with no binding at all"
            )
            continue
        for field in BINDING_FIELDS:
            value = binding.get(field)
            if not isinstance(value, str) or not value.strip():
                errors.append(
                    f"FOUNDER_CONFIRMATION_UNBOUND: {entry.get('file')} :: {entry.get('key_path')} binding has no {field}"
                )
        if not is_full_commit_hash(binding.get("signature_base_commit")):
            errors.append(
                f"FOUNDER_CONFIRMATION_UNBOUND: {entry.get('file')} :: {entry.get('key_path')} binds commit "
                f"{binding.get('signature_base_commit')!r}, which is not a full 40-hex hash"
            )
        resolution = (payload.get("binding_resolutions") or {}).get(f"{entry.get('file')}::{entry.get('key_path')}") or {}
        if resolution.get("file_exists") is not True:
            errors.append(
                f"FOUNDER_CONFIRMATION_UNBOUND: {entry.get('file')} :: {entry.get('key_path')} names authority file "
                f"{binding.get('authority_file')!r}, which does not exist"
            )
        elif resolution.get("clause_resolves") is not True:
            errors.append(
                f"FOUNDER_CONFIRMATION_UNBOUND: {entry.get('file')} :: {entry.get('key_path')} names clause "
                f"{binding.get('authority_clause_path')!r}, which does not resolve in {binding.get('authority_file')!r}"
            )

    declared_counts = payload.get("declared_counts") or {}
    actual = {
        "sites": len(discovered),
        "bound": sum(1 for e in registered.values() if e.get("binding")),
        "act_claims_true": sum(
            1
            for k, e in registered.items()
            if e.get("claim_kind") == "founder_act_claim" and discovered.get(k, {}).get("value") is True
        ),
    }
    for field, value in actual.items():
        if declared_counts.get(field) != value:
            errors.append(
                f"CONFIRMATION_SITE_COUNT_MISSTATED: the registry declares {field}={declared_counts.get(field)!r}, "
                f"the scan finds {value}"
            )
    return errors


def collect() -> dict:
    registry = load_yaml(REGISTRY)
    scope = registry["scan_scope"]
    stems = set(scope["key_stems"])
    excluded = tuple(scope["excluded_prefixes"])

    discovered = []
    for path in sorted(ROOT.rglob("*.yaml")):
        rel = str(path.relative_to(ROOT))
        if rel.startswith(excluded) or "/__pycache__/" in rel:
            continue
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        for key_path, value in _walk(doc, stems):
            discovered.append({"file": rel, "key_path": key_path, "value": value})

    resolutions = {}
    for site in registry["sites"]:
        binding = site.get("binding")
        if not isinstance(binding, dict):
            continue
        resolutions[f"{site['file']}::{site['key_path']}"] = clause_resolves(
            binding.get("authority_file"), binding.get("authority_clause_path")
        )

    return {
        "declared_scope": scope,
        "actual_excluded_prefixes": list(excluded),
        "actual_key_stems": sorted(stems),
        "registered_sites": registry["sites"],
        "discovered_sites": discovered,
        "binding_resolutions": resolutions,
        "declared_counts": registry["counts"],
    }


if __name__ == "__main__":
    cli(LABEL, collect, validate)
