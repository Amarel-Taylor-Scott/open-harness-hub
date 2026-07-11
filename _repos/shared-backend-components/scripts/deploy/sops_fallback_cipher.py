#!/usr/bin/env python3
"""scripts.deploy.sops_fallback_cipher — a dependency-free round-trip cipher used ONLY as the
CI/dev fallback when the real `sops` + `age` binaries are unavailable in the runner.

WHY this exists: the platform secrets vault (see ../../secrets/README.md) is decrypted in
production by `sops -d` with the age private key from the GitHub Environment secret SOPS_AGE_KEY.
`sops`/`age` are NOT installed in every local/CI sandbox, so this module provides a *logic-level*
symmetric round-trip (passphrase -> keystream -> XOR -> base64 armor) whose ONLY job is to prove
that the encrypt/decrypt CONTRACT round-trips a value byte-for-byte. It is:

  - NOT a security boundary. It never replaces age. When `sops`/`age` are present the check uses
    them and this shim is skipped (age's X25519 + ChaCha20-Poly1305 is the real thing).
  - deterministic and self-contained (stdlib only) so `check_sops_secrets.py --self-test` can prove
    round-trip integrity in any sandbox.

The keystream is PBKDF2-HMAC-SHA256 over a passphrase+salt; XOR is its own inverse, so
decrypt(encrypt(x)) == x for any bytes x. This file is under scripts/ (not src/**), so the direct
`import hashlib` is not a canonical-id drift signal (that gate guards src/** only).
"""
from __future__ import annotations

import base64
import hashlib

#: PBKDF2 rounds for the fallback keystream. Named constant (No-Magic-Values); a cost knob only —
#: the shim is a logic proof, not a security boundary, so the value is documented, not tuned for KDF hardness.
FALLBACK_KDF_ROUNDS = 100_000
#: Fixed salt label for the deterministic fallback keystream (round-trip logic, not secrecy).
FALLBACK_KDF_SALT = b"aidoneright-sops-fallback-v1"
#: Armor prefix marking a blob produced by THIS fallback (so a reader can tell it apart from real age ciphertext).
FALLBACK_ARMOR_PREFIX = "AIDR-FALLBACK-1:"


def py_function_scripts_deploy_sops_fallback_cipher__keystream(passphrase: str, length: int) -> bytes:
    """Deterministic keystream of `length` bytes derived from `passphrase` (PBKDF2-HMAC-SHA256).
    Expanded by counter-blocks so it covers payloads longer than one hash digest."""
    out = bytearray()
    counter = 0
    while len(out) < length:
        block = hashlib.pbkdf2_hmac(
            "sha256",
            passphrase.encode("utf-8"),
            FALLBACK_KDF_SALT + counter.to_bytes(4, "big"),
            FALLBACK_KDF_ROUNDS,
            dklen=32,
        )
        out.extend(block)
        counter += 1
    return bytes(out[:length])


def py_function_scripts_deploy_sops_fallback_cipher__encrypt(plaintext: str, passphrase: str) -> str:
    """Encrypt a UTF-8 string with the fallback cipher -> armored base64 string. Logic proof only."""
    raw = plaintext.encode("utf-8")
    ks = py_function_scripts_deploy_sops_fallback_cipher__keystream(passphrase, len(raw))
    xored = bytes(b ^ k for b, k in zip(raw, ks))
    return FALLBACK_ARMOR_PREFIX + base64.b64encode(xored).decode("ascii")


def py_function_scripts_deploy_sops_fallback_cipher__decrypt(armored: str, passphrase: str) -> str:
    """Inverse of encrypt(): armored base64 string -> original UTF-8 plaintext."""
    if not armored.startswith(FALLBACK_ARMOR_PREFIX):
        raise ValueError("not a fallback-armored blob")
    xored = base64.b64decode(armored[len(FALLBACK_ARMOR_PREFIX):])
    ks = py_function_scripts_deploy_sops_fallback_cipher__keystream(passphrase, len(xored))
    return bytes(b ^ k for b, k in zip(xored, ks)).decode("utf-8")


def py_function_scripts_deploy_sops_fallback_cipher__self_test() -> list[str]:
    """Return a list of failure strings ([] == pass). Proves round-trip on a SYNTHETIC value."""
    failures: list[str] = []
    synthetic = "synthetic-anthropic-api-key-dev-000"
    passphrase = "AGE-SECRET-KEY-SYNTHETIC-FALLBACK-PASSPHRASE"
    blob = py_function_scripts_deploy_sops_fallback_cipher__encrypt(synthetic, passphrase)
    if synthetic in blob:
        failures.append("ciphertext leaks the plaintext value")
    back = py_function_scripts_deploy_sops_fallback_cipher__decrypt(blob, passphrase)
    if back != synthetic:
        failures.append(f"round-trip mismatch: {back!r} != {synthetic!r}")
    # wrong passphrase must NOT reproduce the value (garbage bytes may not even be valid UTF-8 — that is a pass)
    try:
        wrong = py_function_scripts_deploy_sops_fallback_cipher__decrypt(blob, passphrase + "x")
    except UnicodeDecodeError:
        wrong = "<undecodable>"
    if wrong == synthetic:
        failures.append("wrong passphrase reproduced the value (keystream not passphrase-bound)")
    return failures


if __name__ == "__main__":
    import sys
    fails = py_function_scripts_deploy_sops_fallback_cipher__self_test()
    if fails:
        for f in fails:
            print("FAIL:", f)
        sys.exit(1)
    print("sops_fallback_cipher --self-test: round-trip OK (synthetic value)")
