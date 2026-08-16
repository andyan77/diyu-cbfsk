"""口令摘要。"""

from __future__ import annotations

from runtime.domain.security import hash_password, verify_password


def test_hash_is_salted_and_verifiable() -> None:
    first = hash_password("correct.horse")
    second = hash_password("correct.horse")
    assert first != second, "同一口令两次摘要相同 —— 说明没有加盐"
    assert verify_password("correct.horse", first)
    assert not verify_password("wrong.horse", first)


def test_malformed_stored_hash_is_rejected_without_raising() -> None:
    """格式不认识就抛异常，会把「这个用户存在」通过 500 与 401 的差异泄露出去。"""
    for stored in ("", "not-a-hash", "scrypt$x$8$1$aa$bb", "bcrypt$1$2$3$4$5"):
        assert verify_password("anything", stored) is False
