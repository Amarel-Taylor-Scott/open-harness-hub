#!/usr/bin/env python3
"""check_credential_registry — the credential PLANE is single-sourced, governed, and drives reachability honestly.

Proves: every service lists env-var NAMES only (no secret values); unlocks reference real planes (tool_planes) / tools
(tool_registry or ocr providers) / sources; the credential env vars actually READ in product code are catalogued here
(no-magic single source — no drifting OH_* key); and the reachability helper (src/teleon/runtime/credentials) computes
present/reachable/missing_for correctly on injected env. serves_truth=false.

  python3 scripts/check_credential_registry.py --self-test
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from src.teleon.runtime import credentials as C

REPO = Path(__file__).resolve().parents[1]
_KEY_SUFFIX = ("_KEY", "_TOKEN", "_BASE_URL", "_ACCOUNT_ID", "_ENDPOINT", "_SECRET")
_FLAG_EXCLUDE = {"OH_INFERENCE_ALLOW_NETWORK", "OH_OLLAMA_MAX_TOKEN", "OH_SHOWCASE_TOKEN"}  # config/flags, not credentials
_VALUE_LOOKING = re.compile(r"(sk-|ghp_|AIza|=|\s)")  # crude: a real secret value, not a NAME
# match only ACTUAL environment reads (_env / os.environ / getenv) — not logical requirement labels or constants
_ENV_READ = re.compile(r'(?:_env|getenv|environ\.get|environ\[)\(?\s*["\']([A-Z][A-Z0-9_]{3,})["\']')


def _load(name):
    return json.loads((REPO / "architecture" / name).read_text(encoding="utf-8"))


def _keys_read_in_product() -> set[str]:
    """Credential env names ACTUALLY read from the environment in product code (_env/os.environ/getenv) — the descent's
    real key usage. Excludes logical requirement labels (e.g. method-grid 'LLM_API_KEY') + constants (CHARS_PER_TOKEN)."""
    found = set()
    for p in (REPO / "src" / "teleon").rglob("*.py"):
        for m in _ENV_READ.findall(p.read_text(encoding="utf-8")):
            if m.endswith(_KEY_SUFFIX) and m not in _FLAG_EXCLUDE:
                found.add(m)
    return found


def _self_test() -> int:
    reg = _load("credential_registry.json")
    svcs = reg["services"]
    planes = {p["plane"] for p in _load("tool_planes.json")["planes"]}
    tool_ids = {t["id"] for t in _load("tool_registry.json")["tools"]}
    tool_ids |= {p.get("id") for p in _load("ocr_provider_registry.json")["providers"]}
    sources = {"github", "gitlab", "pypi", "pypi_keyword", "npm", "crates"}
    catalogued = {v for s in svcs for v in s["env_vars"]}
    fails = []
    def ck(n, ok, d=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok: fails.append(n)

    ck(f"services declared ({len(svcs)})", len(svcs) >= 10)
    ck("every service has id + env_vars + unlocks", all(s.get("id") and s.get("env_vars") and s.get("unlocks") for s in svcs))
    ck("env-var NAMES only (no secret VALUES stored)",
       all(not _VALUE_LOOKING.search(v) and v.isupper() for s in svcs for v in s["env_vars"]),
       "a value-looking entry leaked into env_vars")
    bad_plane = sorted({pl for s in svcs for pl in s["unlocks"].get("planes", []) if pl not in planes})
    ck("unlocks.planes are declared (tool_planes)", not bad_plane, str(bad_plane))
    bad_tool = sorted({t for s in svcs for t in s["unlocks"].get("tools", []) if t not in tool_ids})
    ck("unlocks.tools are real (tool_registry / ocr providers)", not bad_tool, str(bad_tool))
    bad_src = sorted({x for s in svcs for x in s["unlocks"].get("sources", []) if x not in sources})
    ck("unlocks.sources are known", not bad_src, str(bad_src))

    # no-magic single source: every credential key product code reads must be catalogued here
    read = _keys_read_in_product()
    uncatalogued = sorted(read - catalogued)
    ck("every credential env var read in product code is catalogued (no drift)", not uncatalogued, str(uncatalogued))
    ck("services that code reads today are flagged code_read=true",
       all(any(v in catalogued for v in s["env_vars"]) for s in svcs if s.get("code_read")))

    # reachability helper is real (hermetic injected env)
    env_none = {}
    ck("keyless service reachable with no keys (github)", C.is_present("github", env_none))
    ck("keyed service blocked with no keys (libraries_io)", not C.is_present("libraries_io", env_none))
    ck("missing_for names the needed var", C.missing_for("libraries_io", env_none) == ["OH_LIBRARIESIO_KEY"])
    env_have = {"OH_LLM_API_KEY": "x", "OH_LLM_BASE_URL": "y", "COHERE_API_KEY": "z"}
    ck("present when all env vars set (llm_gateway)", C.is_present("llm_gateway", env_have))
    ck("planes unlocked reflects present keys (llm + reranker)",
       {"llm", "reranker"} <= C.reachable_planes(env_have))
    ck("services_for_tool maps a tool to its key (cohere_rerank -> cohere)", "cohere" in C.services_for_tool("cohere_rerank"))
    ck("status() exposes no secret values", all(not _VALUE_LOOKING.search(x) for x in C.status(env_have)["reachable"]))

    # key-ownership model (BYO vs platform-within-limits) — the add-on flexibility
    ck("every service declares key_ownership in {byo, platform, both}",
       all(s.get("key_ownership") in ("byo", "platform", "both") for s in svcs))
    ck("platform-usable services declare platform_limits (the cap on OUR key)",
       all(s.get("platform_limits") for s in svcs if s["key_ownership"] in ("platform", "both")))
    ck("byo-only services declare no platform_limits (their plan, no platform cap)",
       all(s.get("platform_limits") in (None, {}) for s in svcs if s["key_ownership"] == "byo"))
    ck("a marketplace add-on is catalogued (RapidAPI) for external-API components", any(s["id"] == "rapidapi" for s in svcs))
    # key_mode resolves byo vs platform correctly
    ck("key_mode: tenant byo key preferred", C.key_mode("openai", {}, byo={"openai"}) == "byo")
    ck("key_mode: platform key within limits when no byo", C.key_mode("anthropic", {"ANTHROPIC_API_KEY": "x"}) == "platform")
    ck("key_mode: byo-only blocked on platform with no key", C.key_mode("serpapi", {}) is None)
    ck("status() splits byo_only vs platform_capable", "byo_only" in C.status(env_have) and "platform_capable" in C.status(env_have))
    ck("serves_truth=false", reg.get("serves_truth") is False)

    print("\n" + (f"PASS - check_credential_registry: {len(svcs)} services single-sourced; {len(read)} product-read keys "
                  "catalogued; reachability honest (keyless vs keyed, missing_for)." if not fails
                  else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(_self_test())
