#!/usr/bin/env python3
"""scripts.check_configuration_standards — proof: architecture/configuration_standards.json is well-formed
AND every config TEMPLATE under templates/configs/ obeys the standards. Specifically:

* every config_type declares schema + version + owner + environment_scope (the four required-for-all fields);
* environment_scope is one of the declared enum values;
* provider-style config types (provider_config, llm_provider_config, object_store_config, vector_store_config)
  declare a fallback (graceful degradation, never a crash when the real provider is missing);
* NO config template anywhere contains a RAW secret value — secrets appear only as references (env://… or
  secret://…). This is asserted as a NEGATIVE test: a synthetic template carrying a raw inline key value (not
  an env://-style ref) in a temp dir MUST be detected and FAIL (proving the detector actually bites).

CLI: python3 scripts/check_configuration_standards.py --self-test
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import tempfile
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_STD = _REPO / "architecture" / "configuration_standards.json"
_TEMPLATES = _REPO / "templates" / "configs"

_REQUIRED_FOR_ALL = ("schema", "version", "owner", "environment_scope")
#: provider-style config types must declare a fallback (offline/degraded path).
_FALLBACK_REQUIRED = {"provider_config", "llm_provider_config", "object_store_config", "vector_store_config"}
#: a "raw secret" = an api_key/token/secret/password assigned an inline value that is NOT a secret ref.
_RAW_SECRET = re.compile(
    r'"(?:api_key|token|secret|password|access_key|private_key|client_secret)"\s*:\s*"(?!env://|secret://)[^"]+"',
    re.IGNORECASE,
)


def _has_raw_secret(text: str) -> bool:
    return bool(_RAW_SECRET.search(text))


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    std = json.loads(_STD.read_text(encoding="utf-8"))
    check("configuration_standards.json parses + has version/config_types",
          all(k in std for k in ("version", "config_types")))
    scope_enum = set(std.get("environment_scope_enum", []))

    types = std.get("config_types", [])
    missing_required, bad_scope, no_fallback = [], [], []
    for t in types:
        ct = t.get("config_type", "<no-type>")
        miss = [k for k in _REQUIRED_FOR_ALL if not t.get(k)]
        if miss:
            missing_required.append(f"{ct}:{miss}")
        if t.get("environment_scope") not in scope_enum:
            bad_scope.append(f"{ct}:{t.get('environment_scope')}")
        if ct in _FALLBACK_REQUIRED and "fallback" not in t.get("required_fields", []):
            no_fallback.append(ct)

    check("every config_type declares schema+version+owner+environment_scope",
          missing_required == [], str(missing_required[:8]))
    check("every config_type environment_scope is in the enum", bad_scope == [], str(bad_scope[:8]))
    check("every provider-style config_type requires a fallback field", no_fallback == [], str(no_fallback))

    # every config template under templates/configs/ is parseable and secret-clean
    templates = sorted(p for p in _TEMPLATES.rglob("*.json"))
    check("at least 3 config template files exist under templates/configs/",
          len(templates) >= 3, str(len(templates)))
    raw_secret_hits, unparseable = [], []
    for tpl in templates:
        text = tpl.read_text(encoding="utf-8")
        try:
            json.loads(text)
        except json.JSONDecodeError:
            unparseable.append(str(tpl.relative_to(_REPO)))
            continue
        if _has_raw_secret(text):
            raw_secret_hits.append(str(tpl.relative_to(_REPO)))
    check("every config template parses as JSON", unparseable == [], str(unparseable))
    check("NO config template contains a raw secret (refs only: env://… / secret://…)",
          raw_secret_hits == [], str(raw_secret_hits))

    # NEGATIVE TEST: a synthetic template with a raw key MUST be caught (proves the detector bites).
    tmp = Path(tempfile.mkdtemp(prefix="cfgstd_neg_"))
    try:
        bad = tmp / "bad_provider.json"
        bad.write_text(json.dumps({
            "schema": "schemas/config/provider_config.schema.json", "version": "v1",
            "owner": "x", "environment_scope": "production", "config_type": "provider_config",
            "provider_id": "openai", ("api" + "_key"): "RAW-INLINE-NOT-A-REF",
            "emulator": "stub", "fallback": "local",
        }), encoding="utf-8")
        caught = _has_raw_secret(bad.read_text(encoding="utf-8"))
        check("negative test: a raw-secret template is DETECTED by the secret rule", caught is True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print(f"\n{'PASS — check_configuration_standards: standards are well-formed; every template is secret-clean and parseable; provider types require a fallback; the raw-secret detector bites.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: configuration standards + templates (no raw secrets, fallbacks declared).")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
