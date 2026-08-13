#!/usr/bin/env python3
"""M1→M2 信封与 Profile 合同：只包装、不复制、不修改，三态严格分离。

M2 消费 M1 的唯一合法方式是 Envelope/Profile 引用（DIYU-CBFSK-FOUNDER-M2-CHARTER-001）。
这里把那句话拆成可执行判据，分四层：

  1. 冻结物指纹    —— 重算每份被绑定 M1 产物的字节 SHA256，与绑定表比对；对不上即熔断。
  2. 绑定范围      —— 绑定只能落在 M1-EP01 注册表内的产物，不得指向尚不存在的 EP02/EP03 产物。
  3. 三态严格分离  —— 七级知识状态只属知识单元，运行时有效性只属运行时事实对象。
  4. 判据自身有效  —— 用字面量实例夹具驱动 Envelope Schema，正负都得按声明的结果落。

反自审绿（E12）：knowledge_state 的七级枚举**不从信封 Schema 自己读**，而是从 M0 冻结的
knowledge_state_machine.v1.0.yaml 独立重算。信封写错枚举时，拿信封自己当真值会一路显绿。
"""

from __future__ import annotations

import json

import jsonschema

from _common import ROOT, cli, is_full_commit_hash, load_json, load_yaml, sha256_file

LABEL = "check_m2_envelope_contract"

M2_DIR = "03_m2_evaluation_foundation"
ENVELOPE_SCHEMA = f"{M2_DIR}/envelope/m1_to_m2_envelope.schema.v0.1.json"
PROFILE_SCHEMA = f"{M2_DIR}/envelope/profile_composition.schema.v0.1.json"
BINDING = f"{M2_DIR}/envelope/m1_source_binding.v0.1.yaml"
PROFILE_DIR = f"{M2_DIR}/envelope/profiles"
KNOWLEDGE_STATE_MACHINE = "01_contracts_and_schemas/knowledge_state_machine.v1.0.yaml"
M1_REGISTRY = "01_contracts_and_schemas/m1_object_model/schema_registry.v0.1.yaml"
INSTANCE_FIXTURE_DIR = ROOT / "ci" / "fixtures" / "m2" / "envelope_instances"

ENVELOPE_SCHEMA_ID = "https://diyu-cbfsk.local/m2/m1_to_m2_envelope.schema.v0.1.json"

# 启动包 v1.1 Phase 2 字段合同：所有对象一律必填的十一项。
REQUIRED_ENVELOPE_FIELDS = frozenset(
    {
        "artifact_id",
        "object_ref",
        "object_kind",
        "schema_id",
        "schema_version",
        "source_milestone",
        "source_commit",
        "source_artifact_sha256",
        "data_classification",
        "consumption_mode",
        "in_place_modification_allowed",
        "artifact_lifecycle_state",
    }
)

# 条件必填字段 -> 唯一允许携带它的 object_kind。
STATE_FIELD_OWNER = {
    "knowledge_state": "knowledge_unit",
    "runtime_validity_state": "runtime_fact_object",
}

ARTIFACT_LIFECYCLE_STATES = frozenset({"draft", "validated", "frozen", "superseded"})
RUNTIME_VALIDITY_STATES = frozenset({"current", "stale", "expired", "revoked"})
CONDITIONAL_GROUPS = ("scope", "correlation", "temporal")
M1_EP01 = "M1-EP01"


def validate(payload: dict) -> list[str]:
    errors: list[str] = []

    # --- 1. 冻结物指纹 ---
    for row in payload.get("bindings") or []:
        bid = row.get("binding_id", "<no id>")
        if not row.get("artifact_exists"):
            errors.append(f"BINDING_ARTIFACT_MISSING: {bid} points at {row.get('artifact_path')!r} which does not exist")
            continue
        if row.get("declared_sha256") != row.get("actual_sha256"):
            errors.append(
                f"M1_FROZEN_ARTIFACT_DRIFT: {bid} {row.get('artifact_path')} pins "
                f"{row.get('declared_sha256')!r} but the file hashes to {row.get('actual_sha256')!r}"
            )
        if not row.get("in_m1_ep01_registry"):
            errors.append(
                f"BINDING_OUTSIDE_M1_EP01: {bid} binds {row.get('artifact_path')!r}, "
                "which is absent from the M1-EP01 schema registry"
            )

    if payload.get("binding_source_execution_package") != M1_EP01:
        errors.append(
            f"BINDING_OUTSIDE_M1_EP01: binding table declares source package "
            f"{payload.get('binding_source_execution_package')!r}, expected {M1_EP01!r}"
        )
    if payload.get("registry_execution_package") != M1_EP01:
        errors.append(
            f"BINDING_OUTSIDE_M1_EP01: M1 registry declares execution_package "
            f"{payload.get('registry_execution_package')!r}, expected {M1_EP01!r}"
        )
    if not is_full_commit_hash(payload.get("binding_source_commit")):
        errors.append(
            f"SOURCE_COMMIT_NOT_FULL_HASH: binding table source_commit="
            f"{payload.get('binding_source_commit')!r}"
        )

    # --- 2. 信封字段合同 ---
    declared_required = set(payload.get("envelope_required_fields") or [])
    missing = sorted(REQUIRED_ENVELOPE_FIELDS - declared_required)
    if missing:
        errors.append(f"ENVELOPE_REQUIRED_FIELD_MISSING: {missing}")
    if payload.get("envelope_forbids_extra_properties") is not True:
        errors.append(
            "ENVELOPE_ACCEPTS_UNDECLARED_CONTENT: additionalProperties must be false — "
            "an envelope that accepts arbitrary keys can carry the wrapped object's content"
        )
    if payload.get("envelope_in_place_modification_const") is not False:
        errors.append(
            "IN_PLACE_MODIFICATION_ALLOWED: in_place_modification_allowed must be pinned to the constant false"
        )

    # --- 3. 三态严格分离（枚举来自 M0 冻结合同，不取自被测 Schema） ---
    canonical_states = payload.get("canonical_knowledge_states") or []
    envelope_states = payload.get("envelope_knowledge_states") or []
    if list(canonical_states) != list(envelope_states):
        errors.append(
            f"KNOWLEDGE_STATE_ENUM_DRIFT: envelope declares {envelope_states!r}, "
            f"knowledge_state_machine defines {canonical_states!r}"
        )
    if set(payload.get("envelope_lifecycle_states") or []) != ARTIFACT_LIFECYCLE_STATES:
        errors.append(
            f"ARTIFACT_LIFECYCLE_ENUM_DRIFT: {sorted(payload.get('envelope_lifecycle_states') or [])} "
            f"!= {sorted(ARTIFACT_LIFECYCLE_STATES)}"
        )
    if set(payload.get("envelope_runtime_validity_states") or []) != RUNTIME_VALIDITY_STATES:
        errors.append(
            f"RUNTIME_VALIDITY_ENUM_DRIFT: {sorted(payload.get('envelope_runtime_validity_states') or [])} "
            f"!= {sorted(RUNTIME_VALIDITY_STATES)}"
        )
    for owner_field, owner_kind in sorted(STATE_FIELD_OWNER.items()):
        if payload.get("state_field_owner", {}).get(owner_field) != owner_kind:
            errors.append(
                f"STATE_FIELD_OWNER_DRIFT: envelope must restrict {owner_field} to object_kind={owner_kind}"
            )

    # --- 4. Profile ---
    profiles = payload.get("profiles") or []
    if not profiles:
        errors.append("PROFILE_MISSING: no Profile instance found")
    for prof in profiles:
        pid = prof.get("profile_id", "<no id>")
        for err in prof.get("schema_errors") or []:
            errors.append(f"PROFILE_SCHEMA_VIOLATION: {pid}: {err}")
        if prof.get("envelope_schema_id") != ENVELOPE_SCHEMA_ID:
            errors.append(
                f"MULTIPLE_ENVELOPE_SCHEMAS: {pid} composes {prof.get('envelope_schema_id')!r}, "
                f"the single envelope contract is {ENVELOPE_SCHEMA_ID!r}"
            )
        if prof.get("binding_status") == "FINAL" and payload.get("m1_closeout_merged") is not True:
            errors.append(
                f"PREMATURE_FINAL_BINDING: {pid} claims FINAL before M1 closeout is merged into main"
            )
        if prof.get("binding_status") == "PROVISIONAL" and prof.get("final_m1_binding_required") is not True:
            errors.append(f"PROVISIONAL_WITHOUT_REBIND_OBLIGATION: {pid}")
        if not prof.get("final_binding_at"):
            errors.append(f"PROVISIONAL_WITHOUT_REBIND_OBLIGATION: {pid} names no final_binding_at")
        if not is_full_commit_hash(prof.get("source_commit")):
            errors.append(f"SOURCE_COMMIT_NOT_FULL_HASH: {pid} source_commit={prof.get('source_commit')!r}")

        for member in prof.get("members") or []:
            mid = f"{pid}/{member.get('member_id', '<no id>')}"
            kind = member.get("object_kind")
            for field, owner_kind in sorted(STATE_FIELD_OWNER.items()):
                if member.get(field) is not None and kind != owner_kind:
                    code = (
                        "KNOWLEDGE_STATE_APPLIED_TO_RUNTIME_OBJECT"
                        if field == "knowledge_state"
                        else "RUNTIME_VALIDITY_APPLIED_TO_NON_RUNTIME_OBJECT"
                    )
                    errors.append(f"{code}: {mid} is object_kind={kind!r} but carries {field}")
            if member.get("in_place_modification_allowed") is not False:
                errors.append(f"IN_PLACE_MODIFICATION_ALLOWED: {mid}")
            if member.get("sha256_known_binding") is False:
                errors.append(
                    f"MEMBER_SHA256_NOT_FROM_BINDING_TABLE: {mid} carries a digest absent from "
                    f"{BINDING} — digests have exactly one home"
                )
            for group in CONDITIONAL_GROUPS:
                if member.get(f"{group}_required") and not member.get(f"{group}_present"):
                    errors.append(
                        f"PROFILE_MEMBER_CONDITIONAL_REQUIREMENT_UNMET: {mid} requires {group} but omits it"
                    )

    # --- 5. 判据自身被实例夹具行使 ---
    fixtures = payload.get("instance_fixtures") or []
    if not any(f.get("expected") == "INVALID" for f in fixtures):
        errors.append("ENVELOPE_WITHOUT_NEGATIVE_FIXTURE: no expected=INVALID instance exercises the envelope")
    if not any(f.get("expected") == "VALID" for f in fixtures):
        errors.append("ENVELOPE_WITHOUT_POSITIVE_FIXTURE: no expected=VALID instance exercises the envelope")
    for fixture in fixtures:
        if fixture.get("expected") != fixture.get("actual"):
            errors.append(
                f"ENVELOPE_FIXTURE_BEHAVIOUR_MISMATCH: {fixture.get('fixture_id')} expected "
                f"{fixture.get('expected')}, got {fixture.get('actual')} — {fixture.get('detail')}"
            )

    return errors


def _enum_at(schema: dict, prop: str) -> list:
    return list(((schema.get("properties") or {}).get(prop) or {}).get("enum") or [])


def _state_field_owner(schema: dict, field: str) -> str | None:
    """从 allOf 条件里读出「只有哪个 object_kind 允许携带该字段」。

    读的是 Schema 真正会执行的那条约束，不是描述文字——描述可以写得很好听而约束是空的。
    """
    for clause in schema.get("allOf") or []:
        then = clause.get("then") or {}
        forbids = (then.get("not") or {}).get("required") or []
        if field not in forbids:
            continue
        cond = ((clause.get("if") or {}).get("properties") or {}).get("object_kind") or {}
        const = (cond.get("not") or {}).get("const")
        if const:
            return const
    return None


def collect() -> dict:
    envelope = load_json(ENVELOPE_SCHEMA)
    profile_schema = load_json(PROFILE_SCHEMA)
    binding = load_yaml(BINDING)
    registry = load_yaml(M1_REGISTRY)
    ksm = load_yaml(KNOWLEDGE_STATE_MACHINE)

    registry_files = {entry["file"] for entry in registry["entries"]}

    bindings = []
    digest_home = {}
    for entry in binding["entries"]:
        rel = entry["artifact_path"]
        path = ROOT / rel
        exists = path.exists()
        actual = sha256_file(path) if exists else None
        digest_home[entry["sha256"]] = rel
        bindings.append(
            {
                "binding_id": entry["binding_id"],
                "artifact_path": rel,
                "artifact_exists": exists,
                "declared_sha256": entry["sha256"],
                "actual_sha256": actual,
                "in_m1_ep01_registry": rel in registry_files,
            }
        )

    store = {envelope["$id"]: envelope, profile_schema["$id"]: profile_schema}

    def _validator(schema_id: str) -> jsonschema.Draft7Validator:
        resolver = jsonschema.RefResolver(base_uri=schema_id, referrer=store[schema_id], store=store)
        return jsonschema.Draft7Validator(store[schema_id], resolver=resolver)

    profile_validator = _validator(profile_schema["$id"])
    profiles = []
    for path in sorted((ROOT / PROFILE_DIR).glob("*.yaml")):
        doc = load_yaml(str(path.relative_to(ROOT)))
        schema_errors = [
            f"{list(e.absolute_path)}: {e.message}"
            for e in sorted(profile_validator.iter_errors(doc), key=lambda e: list(e.absolute_path))
        ]
        requirements = doc.get("conditional_requirements") or {}
        members = []
        for member in doc.get("members") or []:
            env = member.get("envelope") or {}
            kind = env.get("object_kind")
            row = {
                "member_id": member.get("member_id"),
                "object_kind": kind,
                "knowledge_state": env.get("knowledge_state"),
                "runtime_validity_state": env.get("runtime_validity_state"),
                "in_place_modification_allowed": env.get("in_place_modification_allowed"),
                "sha256_known_binding": env.get("source_artifact_sha256") in digest_home,
            }
            required = requirements.get(kind) or {}
            for group in CONDITIONAL_GROUPS:
                row[f"{group}_required"] = bool(required.get(group))
                row[f"{group}_present"] = env.get(group) is not None
            members.append(row)
        profiles.append(
            {
                "profile_id": doc.get("profile_id"),
                "envelope_schema_id": doc.get("envelope_schema_id"),
                "binding_status": doc.get("binding_status"),
                "final_m1_binding_required": doc.get("final_m1_binding_required"),
                "final_binding_at": doc.get("final_binding_at"),
                "source_commit": doc.get("source_commit"),
                "schema_errors": schema_errors,
                "members": members,
            }
        )

    envelope_validator = _validator(envelope["$id"])
    instance_fixtures = []
    for path in sorted(INSTANCE_FIXTURE_DIR.rglob("*.json")):
        fixture = json.loads(path.read_text(encoding="utf-8"))
        errs = sorted(
            envelope_validator.iter_errors(fixture["instance"]), key=lambda e: list(e.absolute_path)
        )
        instance_fixtures.append(
            {
                "fixture_id": fixture["fixture_id"],
                "expected": fixture["expected"],
                "actual": "VALID" if not errs else "INVALID",
                "detail": errs[0].message[:120] if errs else "<no error raised>",
            }
        )

    return {
        "bindings": bindings,
        "binding_source_commit": binding["source_commit"],
        "binding_source_execution_package": binding["source_execution_package"],
        "registry_execution_package": registry["execution_package"],
        "envelope_required_fields": envelope.get("required") or [],
        "envelope_forbids_extra_properties": envelope.get("additionalProperties") is False,
        "envelope_in_place_modification_const": (
            (envelope.get("properties") or {}).get("in_place_modification_allowed") or {}
        ).get("const"),
        "canonical_knowledge_states": [item["state"] for item in ksm["states"]["items"]],
        "envelope_knowledge_states": _enum_at(envelope, "knowledge_state"),
        "envelope_lifecycle_states": _enum_at(envelope, "artifact_lifecycle_state"),
        "envelope_runtime_validity_states": _enum_at(envelope, "runtime_validity_state"),
        "state_field_owner": {field: _state_field_owner(envelope, field) for field in STATE_FIELD_OWNER},
        "profiles": profiles,
        "instance_fixtures": instance_fixtures,
        # M1 收口是否已合入 main 由 M2-EP02 重新核实；EP01 基线上尚未发生，因此为 false。
        "m1_closeout_merged": False,
    }


if __name__ == "__main__":
    cli(LABEL, collect, validate)
