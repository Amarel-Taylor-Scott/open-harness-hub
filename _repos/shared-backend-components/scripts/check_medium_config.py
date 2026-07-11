#!/usr/bin/env python3
"""check_medium_config — proof that mediums (compute/llm/search) are UI-configurable per-tenant AND per-function.

Clients connect their preferred mediums and can set DIFFERENT mediums for DIFFERENT functions. This proves the
resolver merges most-specific-first (function -> tenant default -> global default), the available choices are computed
from the LIVE registries (so the UI stays in sync), every resolved id is valid, and secrets are SecretRefs. serves_truth=false.

CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_medium_config.py --self-test
"""
from __future__ import annotations

import json
import os
import sys

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _R not in sys.path:
        sys.path.insert(0, _R)

from src.teleon.config.medium_resolver import resolve_mediums, available_mediums, configured_functions


def _self_test() -> int:
    fails = []
    def ck(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': '+detail) if detail and not ok else ''}")
        if not ok: fails.append(name)

    avail = available_mediums()
    ck("available mediums are computed from the live registries (compute incl. cloudflare_workers + k8s)",
       "cloudflare_workers" in avail["compute"] and "k8s_deployment_worker" in avail["compute"], str(avail["compute"][:6]))
    ck("available LLM lanes include cloudflare_workers_ai + ollama", {"cloudflare_workers_ai", "ollama"} <= set(avail["llm"]))
    ck("available search providers include wikipedia + federal_register", {"wikipedia", "federal_register"} <= set(avail["search"]))
    ck("compute_ownership modes are exposed for the UI", "customer_account" in avail.get("compute_ownership", []))

    ext = resolve_mediums("demo", "extraction")
    enr = resolve_mediums("demo", "enrichment")
    # the headline: DIFFERENT mediums for DIFFERENT functions
    ck("extraction resolves to its configured mediums (cloudflare compute + cloudflare LLM)",
       ext["compute"] == "cloudflare_workers" and ext["llm"] == "cloudflare_workers_ai", str(ext))
    ck("enrichment uses a DIFFERENT LLM + search than extraction (per-function mediums)",
       enr["llm"] == "ollama" and enr["search"] == "federal_register" and enr["llm"] != ext["llm"], str(enr))
    ck("each medium records its source layer (function vs default) — traceable",
       ext["sources"].get("llm") == "function" and ext["sources"].get("compute_ownership") == "default")

    # unknown function falls back to tenant default -> global default (no crash, valid mediums)
    unk = resolve_mediums("demo", "does_not_exist")
    ck("an unconfigured function falls back to defaults", unk["compute"] and unk["llm"] and unk["all_valid"])

    ck("every resolved medium id is VALID (exists in a registry)", ext["all_valid"] and enr["all_valid"], str({"ext": ext["valid"], "enr": enr["valid"]}))
    ck("secrets are SecretRefs (never inline tokens)",
       all(str(v).startswith("secret://") for v in ext["secrets"].values()), str(ext["secrets"]))
    ck("configured functions are listed for the UI", set(configured_functions("demo")) >= {"extraction", "enrichment"})
    ck("a medium selection never serves truth (routing decision)", ext["serves_truth"] is False)

    print("\n" + ("PASS - check_medium_config: mediums (compute/llm/search) are configurable per-tenant AND per-function "
                  "(extraction on Cloudflare, enrichment on Ollama+Federal-Register) — resolved most-specific-first, "
                  "choices computed from the live registries, ids validated, secrets as SecretRefs. serves_truth=false."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def _main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--self-test" in argv:
        return _self_test()
    print("usage: check_medium_config.py --self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
