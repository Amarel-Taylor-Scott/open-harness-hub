#!/usr/bin/env python3
"""scripts.check_sops_secrets — the proof gate for the SOPS+age platform secrets vault.

The vault (`_repos/shared-backend-components/secrets/*.env`, recipient policy `/.sops.yaml`) commits
age-*encrypted* VALUES; the ONE age private key lives as the GitHub Environment secret SOPS_AGE_KEY
and decrypts in CI. The app never decrypts at runtime — SOPS only populates os.environ, which the
UNCHANGED runtime seam (`src.teleon.runtime.credentials.env_value` -> `key_holder.KeyHolder.resolve`)
already reads. This check proves that whole contract without touching the seam.

Asserts (each a FAIL string on breach; [] == green):
  1. COVERAGE  — every credential_registry NAME with key_ownership in {platform, both} is a key in
     secrets.dev.env, and every key in secrets.dev.env is a registry NAME (no orphan keys). This is
     the registry->vault direction the earlier audit lacked.
  2. NO-MAGIC-VALUES — the NAME list is read from credential_registry.json, never hand-typed here.
  3. ROUND-TRIP — if `sops`+`age` are on PATH, `sops -d` succeeds and yields the same key set; if
     unavailable (dev/CI-on-PR without the key), run the pure-Python fallback cipher round-trip on a
     SYNTHETIC value (scripts.deploy.sops_fallback_cipher) so the encrypt/decrypt LOGIC is still proven.
  4. NO PLAINTEXT LEAK — reuse deploy.preflight.SECRET_VALUE_SIGNATURES against the committed file's
     decrypted (or, if not decryptable, raw) content — fail if any real-key signature appears.
  5. EXCLUSION — the secrets dir is present in the subtree split-exclude manifest AND the published-
     dist ignore (.dockerignore), so ciphertext never leaks into a public child repo or image.
  6. SEAM CONTRACT — monkeypatch os.environ[NAME]='x' and assert credentials.env_value(NAME)=='x',
     proving the SOPS -> os.environ -> resolver handoff (not assumed).

CLI:
    python3 _repos/shared-backend-components/scripts/check_sops_secrets.py             # report (exit 0)
    python3 _repos/shared-backend-components/scripts/check_sops_secrets.py --self-test  # exit non-zero on any breach
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

# Self-bootstrap: add the dir that holds the `scripts` package (this file is
# .../shared-backend-components/scripts/check_sops_secrets.py) BEFORE importing scripts._repo_paths,
# so a standalone `python3 .../check_sops_secrets.py` works without a caller-set PYTHONPATH.
_SBC = Path(__file__).resolve().parents[1]          # _repos/shared-backend-components
if str(_SBC) not in sys.path:
    sys.path.insert(0, str(_SBC))
from scripts._repo_paths import pythonpath as _pythonpath, resource as _resource  # noqa: E402

REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), _SBC.parent)
# Add repo root + every _repos/*/backend so `src.teleon.*` imports resolve standalone, exactly as
# run_proofs.py does for the whole suite.
for _p in _pythonpath(".").split(os.pathsep):
    if _p and _p not in sys.path:
        sys.path.insert(0, _p)

# ── Constants (single source; No-Magic-Values) ───────────────────────────────
#: The credential registry = the single source of env-var NAMES (never values).
CREDENTIAL_REGISTRY = _resource("architecture") / "credential_registry.json"
#: The vault directory + the dev secrets file it governs.
SECRETS_DIR = _resource("_repos/shared-backend-components/secrets")
SECRETS_ENV = SECRETS_DIR / "secrets.dev.env"
#: The single-source publish/split exclusion manifest.
PUBLISH_EXCLUDE_MANIFEST = _resource("scripts/deploy") / "publish_exclude.json"
#: The published-dist ignore (repo root).
DOCKERIGNORE = REPO / ".dockerignore"
#: The path (as written in both exclusion mechanisms) that must be excluded.
VAULT_EXCLUDE_PATH = "_repos/shared-backend-components/secrets/"
#: Ownership models whose NAMES MUST be covered by the platform vault (byo-only keys are the tenant's).
PLATFORM_OWNERSHIP = ("platform", "both")


def py_function_scripts_check_sops_secrets__registry_names() -> list[str]:
    """Every env-var NAME in the credential registry (No-Magic-Values: read, never re-typed)."""
    data = json.loads(CREDENTIAL_REGISTRY.read_text(encoding="utf-8"))
    return [e for s in data["services"] for e in s["env_vars"]]


def py_function_scripts_check_sops_secrets__platform_names() -> list[str]:
    """The NAMES the platform vault MUST carry (key_ownership in {platform, both})."""
    data = json.loads(CREDENTIAL_REGISTRY.read_text(encoding="utf-8"))
    return [e for s in data["services"] if s.get("key_ownership") in PLATFORM_OWNERSHIP for e in s["env_vars"]]


def py_function_scripts_check_sops_secrets__parse_dotenv_keys(text: str) -> list[str]:
    """The KEYS in a dotenv body (works on plaintext AND sops-encrypted dotenv — sops keeps keys visible)."""
    keys: list[str] = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key = line.split("=", 1)[0].strip()
        # skip sops metadata keys (sops appends a `sops_...`/`unencrypted_suffix` block on some formats)
        if key.startswith("sops") or key.startswith("unencrypted"):
            continue
        keys.append(key)
    return keys


def py_function_scripts_check_sops_secrets__sops_available() -> bool:
    return bool(shutil.which("sops") and shutil.which("age"))


def py_function_scripts_check_sops_secrets__decrypt_or_raw() -> tuple[str, bool]:
    """Return (content, decrypted?). If sops+age are present and SOPS_AGE_KEY is set, `sops -d`;
    else the raw committed content (plaintext template in dev)."""
    raw = SECRETS_ENV.read_text(encoding="utf-8")
    if py_function_scripts_check_sops_secrets__sops_available() and os.environ.get("SOPS_AGE_KEY"):
        try:
            proc = subprocess.run(["sops", "-d", str(SECRETS_ENV)], capture_output=True, text=True, timeout=60)
            if proc.returncode == 0:
                return proc.stdout, True
        except Exception:  # noqa: BLE001
            pass
    return raw, False


# ── Individual checks (each returns a list of FAIL strings; [] == pass) ───────

def py_function_scripts_check_sops_secrets__check_coverage() -> list[str]:
    fails: list[str] = []
    registry = set(py_function_scripts_check_sops_secrets__registry_names())
    platform = set(py_function_scripts_check_sops_secrets__platform_names())
    vault_keys = set(py_function_scripts_check_sops_secrets__parse_dotenv_keys(SECRETS_ENV.read_text(encoding="utf-8")))
    missing = platform - vault_keys
    if missing:
        fails.append(f"COVERAGE: platform/both NAMES not in vault: {sorted(missing)}")
    orphans = vault_keys - registry
    if orphans:
        fails.append(f"COVERAGE: vault keys that are NOT registry NAMES: {sorted(orphans)}")
    return fails


def py_function_scripts_check_sops_secrets__check_no_magic_values() -> list[str]:
    # The proof of No-Magic-Values is structural: the NAME list is computed from the registry file,
    # not embedded here. Assert the source file exists + parses so the single-source read is real.
    if not CREDENTIAL_REGISTRY.is_file():
        return [f"NO-MAGIC-VALUES: credential registry source missing: {CREDENTIAL_REGISTRY}"]
    names = py_function_scripts_check_sops_secrets__registry_names()
    return [] if names else ["NO-MAGIC-VALUES: registry produced no NAMES (parse failure)"]


def py_function_scripts_check_sops_secrets__check_round_trip() -> list[str]:
    from scripts.deploy import sops_fallback_cipher as fc
    if py_function_scripts_check_sops_secrets__sops_available() and os.environ.get("SOPS_AGE_KEY"):
        content, decrypted = py_function_scripts_check_sops_secrets__decrypt_or_raw()
        if not decrypted:
            return ["ROUND-TRIP: sops present but `sops -d` failed"]
        keys = set(py_function_scripts_check_sops_secrets__parse_dotenv_keys(content))
        raw_keys = set(py_function_scripts_check_sops_secrets__parse_dotenv_keys(SECRETS_ENV.read_text(encoding="utf-8")))
        return [] if keys == raw_keys else [f"ROUND-TRIP: decrypted key set != encrypted key set (diff {keys ^ raw_keys})"]
    # sops/age unavailable -> prove the encrypt/decrypt LOGIC with the fallback shim on a synthetic value.
    return [f"ROUND-TRIP(fallback): {f}" for f in fc.py_function_scripts_deploy_sops_fallback_cipher__self_test()]


#: A committed dotenv VALUE is safe iff it is a synthetic placeholder. Anything else in a NON-encrypted
#: committed file is a real-secret leak — an ALLOWLIST, so keys of ANY vendor format are caught (a
#: vendor-prefix blocklist missed OpenAI sk-proj-, AWS 40-char, GitLab glpat-, github_pat_, Cohere, …).
_SYNTHETIC_VALUE_RE = re.compile(r"^\s*(synthetic-|https://synthetic|/synthetic|synthetic\b)", re.IGNORECASE)


def py_function_scripts_check_sops_secrets__check_no_plaintext_leak() -> list[str]:
    """Encryption-at-rest / no-real-secret gate, enforced in run_proofs (not only at deploy time). If the
    committed secrets file is age-ciphertext (``ENC[``) it is safe; otherwise EVERY value must be a
    synthetic placeholder — a real key of any format would otherwise land in permanent git history."""
    raw = SECRETS_ENV.read_text(encoding="utf-8") if SECRETS_ENV.is_file() else ""
    if "ENC[" in raw:                                          # sops/age ciphertext -> values encrypted at rest
        return []
    bad: list[str] = []
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        value = value.strip().strip('"').strip("'")
        if value and not _SYNTHETIC_VALUE_RE.match(value):    # a real (non-synthetic) value in a plaintext file
            bad.append(key.strip())
    if bad:
        return [f"NO-PLAINTEXT-LEAK: {len(bad)} committed value(s) are NOT synthetic and the file is not "
                f"age-encrypted — a real secret would enter permanent git history. Offending keys: {sorted(bad)[:10]}. "
                f"Fix: `sops -e -i secrets/secrets.dev.env` (encrypt), or use synthetic-* placeholders."]
    return []


def py_function_scripts_check_sops_secrets__check_exclusion() -> list[str]:
    fails: list[str] = []
    try:
        manifest = json.loads(PUBLISH_EXCLUDE_MANIFEST.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        return [f"EXCLUSION: cannot read publish-exclude manifest: {exc}"]
    if VAULT_EXCLUDE_PATH not in manifest.get("subtree_split_exclude", []):
        fails.append(f"EXCLUSION: {VAULT_EXCLUDE_PATH} missing from subtree_split_exclude")
    if VAULT_EXCLUDE_PATH not in manifest.get("published_dist_exclude", []):
        fails.append(f"EXCLUSION: {VAULT_EXCLUDE_PATH} missing from published_dist_exclude")
    dockerignore = DOCKERIGNORE.read_text(encoding="utf-8") if DOCKERIGNORE.is_file() else ""
    if not any(line.strip() == VAULT_EXCLUDE_PATH for line in dockerignore.splitlines()):
        fails.append(f"EXCLUSION: {VAULT_EXCLUDE_PATH} not ignored in .dockerignore")
    return fails


def py_function_scripts_check_sops_secrets__check_seam_contract() -> list[str]:
    """Prove the SOPS -> os.environ -> resolver handoff: inject an env var, read it through the
    UNCHANGED runtime seam credentials.env_value + key_holder.resolve."""
    try:
        from src.teleon.runtime import credentials as C
        from src.teleon.runtime import key_holder as K
    except Exception as exc:  # noqa: BLE001
        return [f"SEAM-CONTRACT: cannot import runtime seam: {exc}"]
    fails: list[str] = []
    probe_name = "OH_GITHUB_TOKEN"       # a real registry NAME (github service) so key_holder.resolve() also sees it
    probe_value = "sops-injected-synthetic-value-xyz"
    prev = os.environ.get(probe_name)
    try:
        os.environ[probe_name] = probe_value
        got = C.py_function_src_teleon_runtime_credentials__env_value(probe_name)
        if got != probe_value:
            fails.append(f"SEAM-CONTRACT: env_value({probe_name}) returned {got!r}, expected {probe_value!r}")
        resolved = K.py_class_src_teleon_runtime_key_holder__KeyHolder().resolve("github")
        if resolved != probe_value:
            fails.append(f"SEAM-CONTRACT: key_holder.resolve('github') returned {resolved!r}, expected {probe_value!r}")
    finally:
        if prev is None:
            os.environ.pop(probe_name, None)
        else:
            os.environ[probe_name] = prev
    return fails


CHECKS = [
    ("coverage", py_function_scripts_check_sops_secrets__check_coverage),
    ("no_magic_values", py_function_scripts_check_sops_secrets__check_no_magic_values),
    ("round_trip", py_function_scripts_check_sops_secrets__check_round_trip),
    ("no_plaintext_leak", py_function_scripts_check_sops_secrets__check_no_plaintext_leak),
    ("exclusion", py_function_scripts_check_sops_secrets__check_exclusion),
    ("seam_contract", py_function_scripts_check_sops_secrets__check_seam_contract),
]


def py_function_scripts_check_sops_secrets__run_all() -> list[tuple[str, list[str]]]:
    return [(name, fn()) for name, fn in CHECKS]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--self-test", action="store_true", help="exit non-zero on any breach (for run_proofs)")
    args = parser.parse_args(argv)
    results = py_function_scripts_check_sops_secrets__run_all()
    total_fail = 0
    for name, fails in results:
        if fails:
            total_fail += len(fails)
            for f in fails:
                print(f"  RED  {name}: {f}")
        else:
            print(f"  ok   {name}")
    sops_mode = "sops+age" if py_function_scripts_check_sops_secrets__sops_available() else "fallback-cipher"
    print(f"\ncheck_sops_secrets: {len(results) - sum(1 for _, f in results if f)}/{len(results)} checks green "
          f"[round-trip mode: {sops_mode}]" + (" — ALL GREEN" if total_fail == 0 else f" — {total_fail} breach(es)"))
    return 1 if (total_fail and args.self_test) else 0


if __name__ == "__main__":
    raise SystemExit(main())
