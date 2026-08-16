"""口令摘要。标准库 scrypt，不引第三方口令库。

选 scrypt 而不是 sha256+salt：后者算得太快，离线爆破成本几乎为零。
参数取 RFC 7914 的常用生产档（n=2^15）——改小会让摘要形同虚设，所以它们是具名常量，
不是散落在调用处的字面量（EQ-4）。
"""

from __future__ import annotations

import hashlib
import hmac
import os

SCRYPT_N = 2**15
SCRYPT_R = 8
SCRYPT_P = 1
SCRYPT_DKLEN = 32
# OpenSSL 默认只肯给 scrypt 32MiB，而 n=2^15/r=8 恰好要 32MiB 出头，不显式抬高就直接报
# 「memory limit exceeded」。这个上限必须跟着 n/r/p 一起改，所以从它们算出来，不写死数字。
SCRYPT_MAXMEM = 2 * (128 * SCRYPT_R * SCRYPT_N)
SALT_BYTES = 16
HASH_PREFIX = "scrypt"


def hash_password(plaintext: str) -> str:
    """返回 `scrypt$<n>$<r>$<p>$<salt hex>$<dk hex>`。明文不保留。"""
    salt = os.urandom(SALT_BYTES)
    derived = hashlib.scrypt(
        plaintext.encode("utf-8"),
        salt=salt,
        n=SCRYPT_N,
        r=SCRYPT_R,
        p=SCRYPT_P,
        dklen=SCRYPT_DKLEN,
        maxmem=SCRYPT_MAXMEM,
    )
    return f"{HASH_PREFIX}${SCRYPT_N}${SCRYPT_R}${SCRYPT_P}${salt.hex()}${derived.hex()}"


def verify_password(plaintext: str, stored: str) -> bool:
    """常数时间比对。格式不认识一律返回 False，不抛异常——异常会把「这个用户存在」泄露出去。"""
    parts = stored.split("$")
    if len(parts) != 6 or parts[0] != HASH_PREFIX:
        return False
    try:
        n, r, p = int(parts[1]), int(parts[2]), int(parts[3])
        salt = bytes.fromhex(parts[4])
        expected = bytes.fromhex(parts[5])
    except ValueError:
        return False
    derived = hashlib.scrypt(
        plaintext.encode("utf-8"), salt=salt, n=n, r=r, p=p, dklen=len(expected), maxmem=2 * (128 * r * n)
    )
    return hmac.compare_digest(derived, expected)
