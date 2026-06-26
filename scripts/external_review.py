#!/usr/bin/env python3
"""external_review — call EXTERNAL models (GLM-5.2 + Kimi-2.7) to review our codebase + PMF.

A different model disagreeing with us is the value: this assembles a BOUNDED, secrets-excluded context pack of the
code + product, sends it to GLM-5.2 and Kimi-2.7, and lands each review as a GOVERNED CANDIDATE (serves_truth=false
— an external model's opinion is a proposal, never trusted truth).

PROVIDER-AGNOSTIC (OpenAI-compatible /v1/chat/completions): defaults to the **Ollama Cloud** lane configured in
.env (OH_LLM_BASE_URL / OH_LLM_API_KEY) since OpenRouter is out of credits; --provider openrouter is also wired.
Both reach GLM + Kimi; the call path is identical (OpenAI-compatible), the model ids differ per provider.

GOVERNANCE (mirrors architecture/lowcost_llm_endpoint_registry.json): external lanes, allowed_data_classes=
[public, internal_non_sensitive]. The pack is built from PUBLIC/non-sensitive repo files ONLY and EXCLUDES .env,
secrets, _reference/. Each call writes a receipt (model, data-class, serves_truth=false). The API key is read from
.env and never logged.

  --self-test           offline: prove the pack excludes secrets, is bounded, lands as a candidate
  --live                actually call the models (network egress) -> docs/reviews/external-review/
  --provider ollama|openrouter   pick the lane (default: ollama)
  --models a,b          override model ids
CLI: python3 scripts/external_review.py --live
"""
from __future__ import annotations

import json
import os
import sys
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

# FULL context in, MAXIMUM tokens out (env-overridable — Kimi-2.7 / GLM-5.2 / qwen3-coder + Claude all carry huge
# windows, so default big and let the owner push to a 1M-context lane). These are the single source for both lanes.
PACK_CHAR_CAP = int(os.environ.get("OH_REVIEW_PACK_CHARS", str(900_000)))   # ~225k tokens of whole-repo map+API+graph+knowledge
# Output is UNCAPPED by default (None -> max_tokens omitted from the request -> the model runs to its OWN maximum).
# Kimi-2.7 / GLM-5.2 / qwen3-coder + Claude all carry huge windows; set OH_REVIEW_MAX_TOKENS to a positive int only
# if you deliberately want to cap. This is the single source for the per-call output budget across both lanes.
_mt_env = os.environ.get("OH_REVIEW_MAX_TOKENS", "").strip()
REVIEW_MAX_TOKENS = int(_mt_env) if _mt_env.isdigit() and int(_mt_env) > 0 else None
OUT_DIR = REPO / "docs" / "reviews"

# Provider lanes (all OpenAI-compatible). base_url ends in /v1; the call hits {base_url}/chat/completions.
PROVIDERS = {
    "ollama": {"base_url_var": "OH_LLM_BASE_URL", "key_var": "OH_LLM_API_KEY",
               "models": ["glm-5.2", "kimi-k2.7-code"], "headers": {}},
    "openrouter": {"base_url": "https://openrouter.ai/api/v1", "key_var": "OPENROUTER_API_KEY",
                   "models": ["z-ai/glm-5.2", "moonshotai/kimi-k2.7-code"],
                   "headers": {"HTTP-Referer": "https://aidoneright.dev", "X-Title": "OpenHarnessHub external review"}},
}
DEFAULT_PROVIDER = "ollama"

# Curated, PUBLIC/non-sensitive high-signal sources for the pack (head N chars each, total-capped).
PACK_SOURCES = [
    ("CLAUDE.md", 9000),
    ("docs/strategy/teleon-baltor-openharnesshub-portfolio.md", 4000),
    ("docs/strategy/teleon-naming-and-domain.md", 2500),
    ("docs/concepts/capability-valleys.md", 3500),
    ("docs/concepts/component-taxonomy-and-stages.md", 2500),
    ("architecture/storage_tier_policy.json", 3500),
    ("src/teleon/evolution/descent_axes.py", 4500),
    ("src/teleon/evolution/descent_attempt_store.py", 2500),
    ("src/teleon/evolution/substrate_selector.py", 2500),
    ("src/teleon/storage/record_store.py", 2500),
    ("src/teleon/objectives/objective.py", 2500),
    ("src/teleon/inference/model_index.py", 2000),
]


def _env(var: str) -> str:
    for ln in (REPO / ".env").read_text(encoding="utf-8").splitlines():
        if ln.startswith(f"{var}="):
            return ln.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def resolve_provider(name: str) -> dict:
    if name not in PROVIDERS:
        raise SystemExit(f"unknown provider {name!r}; have: {list(PROVIDERS)}")
    p = dict(PROVIDERS[name])
    p["base_url"] = p.get("base_url") or _env(p["base_url_var"])
    p["key"] = _env(p["key_var"])
    p["name"] = name
    return p


def _repo_shape() -> str:
    import subprocess
    def n(cmd):
        try:
            return subprocess.run(cmd, cwd=REPO, capture_output=True, text=True, shell=True).stdout.strip()
        except Exception:
            return "?"
    return (f"Repo shape (computed): {n('find src scripts -name *.py | wc -l')} python modules under src/+scripts/, "
            f"{n('ls architecture/*.json | wc -l')} architecture/*.json registries/configs, "
            f"{n('ls scripts/check_*.py | wc -l')} scripts/check_*.py proof gates (the repo's --self-test idiom).")


def build_context_pack() -> tuple[str, list[dict]]:
    """The NON-FRAGILE, layered (global/regional/local) pack — generated from live code via context_pack_builder, so
    a reviewer sees the full API surface (no truncated-heads false-negatives) and never a stale doc. Falls back to the
    curated-heads pack only if the generator is unavailable."""
    try:
        from scripts.context_pack_builder import build_pack
        return build_pack(full=True)   # the big-context Ollama lane gets the FULL repo map + entire src/ API
    except Exception:  # noqa: BLE001 — degrade to the legacy heads pack rather than fail a review
        parts = ["# Context pack — OpenHubForAI (Teleon + Baltor)\n", _repo_shape() + "\n"]
        manifest, total = [], 0
        for rel, cap in PACK_SOURCES:
            p = REPO / rel
            if not p.exists():
                manifest.append({"path": rel, "status": "missing"}); continue
            text = p.read_text(encoding="utf-8", errors="replace")[:cap]
            chunk = f"\n\n## FILE: {rel}\n```\n{text}\n```\n"
            parts.append(chunk); total += len(chunk)
            manifest.append({"path": rel, "status": "included", "chars": len(text)})
            if total >= PACK_CHAR_CAP:
                break
        return "".join(parts), manifest


_SECRET_VAR_MARKERS = ("KEY", "SECRET", "TOKEN", "PASSWORD", "CREDENTIAL", "PRIVATE")
_SECRET_MIN_LEN = 24   # real keys/tokens are long+high-entropy; short config values (ollama/false/a url) are not secrets


def assert_pack_safe(pack: str, manifest: list[dict]) -> list[str]:
    """Return governance violations (empty = safe). A leak = a SECRET-class .env value in the pack; short
    non-sensitive config values (e.g. OH_LLM_BACKEND=auto) may legitimately appear and are NOT leaks."""
    bad = []
    if len(pack) > PACK_CHAR_CAP + 2000:
        bad.append(f"pack exceeds cap: {len(pack)}")
    for ln in (REPO / ".env").read_text(encoding="utf-8", errors="replace").splitlines():
        if "=" not in ln or ln.lstrip().startswith("#"):
            continue
        name, _, val = ln.partition("=")
        val = val.strip().strip('"').strip("'")
        if (any(m in name.upper() for m in _SECRET_VAR_MARKERS) or len(val) >= _SECRET_MIN_LEN) and val and val in pack:
            bad.append(f"a SECRET .env value leaked into the pack: {name.strip()}")
    if not any(m["status"] == "included" for m in manifest):
        bad.append("pack is empty (no sources included)")
    return bad


REVIEW_SYSTEM = (
    "You are a skeptical principal engineer + a YC partner doing diligence on another team's codebase and product. "
    "Be specific and critical; cite file names from the pack. No flattery, no hedging.")

REVIEW_USER_TMPL = (
    "Below is a bounded digest of a two-product AI platform: Baltor (a context engine: ingest -> reconcile -> harden "
    "-> enrich -> compress -> serve) and Teleon (a runtime that takes a plain non-deterministic capability and "
    "DESCENDS it to cheaper/faster/more-deterministic/more-bounded against user preferences, using registries of "
    "models/context/harnesses/skills as the selection substrate). OpenHubForAI is the open ecosystem.\n\n"
    "Review it and answer each with concrete, file-cited points:\n"
    "1. ARCHITECTURE: biggest strengths and the 3 most serious risks/weaknesses.\n"
    "2. PRODUCT-MARKET FIT: is the wedge real and defensible? who buys this, why now, what would kill it?\n"
    "3. WHAT'S MISSING: the highest-leverage thing they are NOT doing.\n"
    "4. NEXT STEPS: 5 concrete, prioritized next steps (most impactful first).\n"
    "5. ONE BRUTAL TRUTH: the thing the team is probably in denial about.\n\n"
    "=== CONTEXT PACK ===\n{pack}\n=== END PACK ===")


def chat(model: str, system: str, user: str, provider: dict, *, max_tokens: int = REVIEW_MAX_TOKENS, timeout: int = 600) -> dict:
    """One OpenAI-compatible chat call against any provider lane. Captures reasoning-model output (kimi puts its
    text in `reasoning`/`reasoning_content`, content empty). Returns {model,text,usage,finish_reason,error}."""
    url = provider["base_url"].rstrip("/") + "/chat/completions"
    payload = {
        "model": model,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "temperature": 0.3, "stream": False,
    }
    if max_tokens:                 # None / 0 -> omit -> UNCAPPED (the model emits to its own maximum)
        payload["max_tokens"] = max_tokens
    body = json.dumps(payload).encode()
    headers = {"Authorization": f"Bearer {provider['key']}", "Content-Type": "application/json", **provider["headers"]}
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data=body, headers=headers), timeout=timeout) as r:
            d = json.loads(r.read().decode())
        choice = d["choices"][0]
        msg = choice.get("message", {})
        text = msg.get("content") or msg.get("reasoning") or msg.get("reasoning_content") or ""
        return {"model": model, "text": text, "usage": d.get("usage", {}),
                "finish_reason": choice.get("finish_reason"), "error": None}
    except Exception as e:  # noqa: BLE001 — surface any provider/network error in the receipt
        detail = ""
        if hasattr(e, "read"):
            try: detail = e.read().decode()[:500]
            except Exception: pass
        return {"model": model, "text": "", "usage": {}, "error": f"{type(e).__name__}: {e} {detail}"}


def call_model(model: str, pack: str, provider: dict, *, timeout: int = 300) -> dict:
    return chat(model, REVIEW_SYSTEM, REVIEW_USER_TMPL.format(pack=pack), provider, timeout=timeout)


def _receipt(result: dict, manifest: list[dict], provider: str) -> dict:
    return {"model": result["model"], "provider": provider, "serves_truth": False,
            "data_class": "public/internal_non_sensitive", "usage": result["usage"], "error": result["error"],
            "pack_sources": [m["path"] for m in manifest if m["status"] == "included"], "status": "candidate",
            "note": "external model opinion; a PROPOSAL, never trusted truth"}


def run_live(provider_name: str, models: list[str]) -> int:
    pack, manifest = build_context_pack()
    bad = assert_pack_safe(pack, manifest)
    if bad:
        print("REFUSED — pack failed governance:", bad); return 1
    provider = resolve_provider(provider_name)
    if not provider["key"]:
        print(f"REFUSED — no key for provider {provider_name!r} ({provider['key_var']} empty in .env)"); return 1
    if not provider["base_url"]:
        print(f"REFUSED — no base_url for provider {provider_name!r}"); return 1
    out = OUT_DIR / "external-review"; out.mkdir(parents=True, exist_ok=True)
    print(f"provider={provider_name} base_url={provider['base_url']} · pack {len(pack)} chars, "
          f"{sum(1 for m in manifest if m['status']=='included')} files")
    results = []
    for m in models:
        print(f"calling {m} ...", flush=True)
        res = call_model(m, pack, provider); results.append(res)
        slug = m.replace("/", "_")
        if res["error"]:
            print(f"  ERROR: {res['error'][:200]}")
        else:
            print(f"  ok: {len(res['text'])} chars, usage={res['usage']}")
            header = (f"# External review — {m} (via {provider_name})\n\n> CANDIDATE · serves_truth=false · external "
                      f"model opinion (a proposal, never trusted truth).\n\n")
            (out / f"{slug}.md").write_text(header + res["text"], encoding="utf-8")
        (out / f"{slug}.receipt.json").write_text(json.dumps(_receipt(res, manifest, provider_name), indent=2), encoding="utf-8")
    (out / "manifest.json").write_text(json.dumps({"provider": provider_name, "models": models, "pack_manifest": manifest}, indent=2), encoding="utf-8")
    ok = [r for r in results if not r["error"]]
    print(f"\n{'PASS' if ok else 'FAIL'} - external_review: {len(ok)}/{len(models)} models returned a review -> {out}/")
    return 0 if ok else 1


def _self_test() -> int:
    fails = []
    def ck(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': '+detail) if detail and not ok else ''}")
        if not ok: fails.append(name)
    pack, manifest = build_context_pack()
    ck("the context pack is non-empty and bounded", 0 < len(pack) <= PACK_CHAR_CAP + 2000, str(len(pack)))
    ck("the pack includes curated public sources", any(m["status"] == "included" for m in manifest))
    ck("the pack passes the secrets-governance check (no SECRET .env value leaks)", not assert_pack_safe(pack, manifest), str(assert_pack_safe(pack, manifest)))
    p = resolve_provider(DEFAULT_PROVIDER)
    ck("the default provider is the Ollama Cloud lane from .env", p["base_url"].startswith("https://ollama.com") and bool(p["key"]), p["base_url"])
    ck("the default models are GLM-5.2 + Kimi-2.7", p["models"] == ["glm-5.2", "kimi-k2.7-code"])
    ck("the pack does NOT contain the provider key value", p["key"] and p["key"] not in pack)
    ck("receipts mark candidate + serves_truth=false", _receipt({"model": "x", "usage": {}, "error": None}, manifest, "ollama")["serves_truth"] is False)
    print("\n" + ("PASS - external_review --self-test: bounded secrets-excluded pack, governance-gated, candidate output; "
                  "default lane = Ollama Cloud (GLM-5.2 + Kimi-2.7). Run --live to call them."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def _main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    provider = DEFAULT_PROVIDER
    models = None
    for i, a in enumerate(argv):
        if a == "--provider" and i + 1 < len(argv): provider = argv[i + 1]
        if a == "--models" and i + 1 < len(argv): models = [m.strip() for m in argv[i + 1].split(",") if m.strip()]
    models = models or PROVIDERS.get(provider, {}).get("models", [])
    if "--self-test" in argv: return _self_test()
    if "--live" in argv: return run_live(provider, models)
    print("usage: external_review.py --self-test | --live [--provider ollama|openrouter] [--models a,b]")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
