#!/usr/bin/env python3
"""scripts.build_scenario_corpus — TENS OF THOUSANDS of build-anything scenarios: everything someone could
want to build with an LLM (SaaS apps, mobile apps, pages, dashboards, design systems, toolkits, SDKs, CLIs,
APIs, pipelines, extensions, chatbots, internal tools, report generators, slack bots, terraform modules,
api gateways …) × real industries × capabilities × stacks × phrasings — generated DETERMINISTICALLY (a
strided walk of the cartesian axes; no RNG), each row carrying expected CONCEPT tokens so coverage is
VERIFIED, never "returned something". Capability rows span the original SaaS + UI/UX families plus
AI/agents, data engineering, devops, mobile, games, security, collaboration, commerce, content, and
ops/compliance; phrasings include bug-, migration-, and comparison-flavored asks. Axis sizes are computed
(the PASS line), never typed into prose.

The corpus is DATA (`build_scenario_corpus.jsonl`) — the at-scale sibling of the SaaS gold seed: benchmark
rows, gap-mining leads (every miss names what the primitive corpus lacks), and the sampling pool for the
REAL-generation harness. Axes are module-level rows: a new domain/artifact/capability/stack/phrasing is one
row and the corpus regenerates.

Expected tokens are DF-AUDITED against the real corpus (`--token-audit`): a token generic at corpus scale
(document frequency >= _GENERIC_TOKEN_DF_BAR) fails the audit, so a verified hit means a genuinely relevant
card — never "any card that says 'harness'".

serves_truth=false — scenarios and coverage numbers are candidates/measurements, never truth.

    PYTHONPATH=. python3 scripts/build_scenario_corpus.py --self-test
    PYTHONPATH=. python3 scripts/build_scenario_corpus.py --write [--count 30000]
    PYTHONPATH=. python3 scripts/build_scenario_corpus.py --coverage [--sample 2000]   # verified, full corpus
    PYTHONPATH=. python3 scripts/build_scenario_corpus.py --token-audit                # df-audit token contracts
"""
from __future__ import annotations

import sys
from pathlib import Path

# ── substrate-root bootstrap (sentinel; mirrors scripts/capability_retrieval_mcp_server.py) ──────────────────
_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots, resource  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import itertools  # noqa: E402
import json  # noqa: E402
import math  # noqa: E402
from typing import Any, Optional  # noqa: E402

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}

_DEFAULT_COUNT = 30000
_CORPUS_FILENAME = "build_scenario_corpus.jsonl"
#: max document frequency (fraction of corpus cards) an expected CONCEPT token may carry. Above this bar a
#: token is GENERIC at corpus scale: the one-token OR hit gate (_verified_hit over the top-k cards) would
#: grant vacuous hits (review 2026-07-07: "harness" sat in 49% of the 112K cards, making "model eval
#: harness" literally unmissable). Enforced by token_df_audit() / `--token-audit` — recomputed, never
#: hand-typed into prose.
_GENERIC_TOKEN_DF_BAR = 0.01

#: the AXES — every entry is a row; the corpus is a deterministic strided walk of their product.
_DOMAINS: tuple[str, ...] = (
    "logistics", "healthcare admin", "legal services", "real estate", "education", "hospitality",
    "agriculture", "manufacturing", "renewable energy", "construction", "recruiting", "event planning",
    "fitness studios", "veterinary clinics", "restaurants", "e-commerce", "media publishing", "game studios",
    "travel agencies", "non-profits", "municipal services", "research labs", "museums", "sports clubs",
    "salons", "auto repair", "field services", "property management", "warehousing", "print shops",
    "photography", "catering", "childcare", "elder care", "pet services", "marine charters",
    # scale-out rows (2026-07-06, ADD-only): more real industries — one entry = one new axis row
    "dental practices", "pharmacies", "public libraries", "food trucks", "breweries", "wineries",
    "florists", "moving companies", "storage facilities", "cleaning services", "landscaping",
    "tutoring centers", "dance studios", "music schools", "coworking spaces", "bike shops")
_ARTIFACTS: tuple[str, ...] = (
    "SaaS web app", "mobile app", "landing page", "marketing site", "admin dashboard", "design system",
    "UI toolkit", "client SDK", "command line tool", "REST API service", "data pipeline",
    "browser extension", "customer chatbot", "internal tool", "report generator", "booking portal",
    # scale-out rows (2026-07-06, ADD-only): developer/ops deliverables people ask an LLM to build
    "slack bot", "vscode extension", "jupyter workflow", "terraform module", "figma plugin",
    "email template pack", "api gateway", "cron service")
#: capability -> the expected CONCEPT tokens a genuinely relevant primitive would carry — specific,
#: boundary-matched, and DF-AUDITED: every token's document frequency over the real corpus must stay under
#: _GENERIC_TOKEN_DF_BAR (review 2026-07-07 replaced the generic tokens — e.g. "harness" df 49%, "receipt"
#: df 20%, "version" df 12% — with corpus-verified low-df concept tokens; `--token-audit` recomputes the
#: sweep with the hit gate's own tokenizer and fails on any regression). Rows are kept, never deleted:
#: correcting a defective token contract preserves the ADD-only zoo law.
_CAPABILITIES: dict[str, tuple[str, ...]] = {
    "user login and accounts": ("login", "oauth", "session"),
    "accept card payments": ("payment", "stripe", "billing", "checkout"),
    "subscription plans": ("subscription", "billing", "invoice"),
    "full text search": ("fulltext", "bm25", "inverted", "stemming"),
    "email notifications": ("email", "notification", "smtp"),
    "file uploads": ("upload", "storage"),
    "usage dashboard with charts": ("dashboard", "chart", "metric"),
    "export data to csv": ("export", "csv", "download"),
    "appointment scheduling": ("schedule", "calendar", "booking"),
    "background jobs": ("queue", "worker"),
    "realtime chat": ("websocket", "message"),
    "map with locations": ("geocode", "location"),
    "reviews and ratings": ("rating", "feedback"),
    "inventory tracking": ("inventory", "stock", "sku"),
    "customer onboarding flow": ("onboarding", "signup", "wizard"),
    "roles and permissions": ("role", "permission", "rbac", "access"),
    "webhook integrations": ("webhook", "integration", "callback"),
    "product analytics events": ("analytics", "event", "tracking"),
    "multi language support": ("translation", "locale", "i18n"),
    "generate pdf documents": ("pdf", "document", "render"),
    "scan and extract documents": ("ocr", "scan"),
    "deduplicate records": ("duplicate", "dedupe", "merge"),
    "sync data between systems": ("sync", "replication", "etl"),
    "automated backups": ("backup", "restore", "snapshot"),
    "forms with validation": ("form", "validator", "fieldset"),
    "response caching": ("cache", "redis", "ttl"),
    "rate limiting": ("rate", "limit", "throttle"),
    "audit trail of changes": ("trail", "log", "history"),
    "single sign on": ("sso", "saml", "oidc"),
    "feature flags": ("feature", "flag", "rollout"),
    # UI/UX capability rows (owner directive: "more UI/UX") — same verified-token contract
    "responsive page layout": ("responsive", "layout", "grid", "breakpoint"),
    "dark mode theming": ("theme", "dark", "css", "token"),
    "accessible components": ("accessibility", "aria", "wcag", "contrast"),
    "design token system": ("design", "token", "palette", "typography"),
    "reusable component library": ("library", "storybook", "props"),
    "data table with sorting": ("table", "sort", "column"),
    "drag and drop editor": ("drag", "drop", "editor", "canvas"),
    "empty states and loading skeletons": ("skeleton", "loading", "empty", "placeholder"),
    "guided product tour": ("tour", "tooltip", "walkthrough", "highlight"),
    "form ux with inline errors": ("form", "inline", "error"),
    # scale-out capability rows (2026-07-06, ADD-only zoo extension) — same verified-token contract:
    # 3-4 SPECIFIC lowercase concept tokens a genuinely relevant primitive card would carry.
    # AI / agents
    "llm prompt pipeline": ("fewshot", "chain"),
    "rag document retrieval": ("rag", "chunk", "grounding"),
    "embeddings similarity search": ("embedding", "vector", "similarity", "cosine"),
    "agent tool calling": ("agent", "tool", "calling", "orchestration"),
    "model eval harness": ("eval", "rubric", "grader", "grading"),
    "llm output guardrails": ("guardrail", "moderation", "safety"),
    "model routing and fallback": ("routing", "fallback", "latency"),
    "fine tuning data preparation": ("training", "annotation", "curation"),
    "semantic reranking": ("rerank", "relevance", "scoring"),
    "prompt injection defense": ("injection", "sanitize", "jailbreak"),
    "token usage metering": ("token", "usage", "metering", "quota"),
    "vector database indexing": ("vector", "pgvector", "hnsw"),
    # data engineering
    "change data capture stream": ("cdc", "capture", "changelog", "replication"),
    "schema migrations": ("migration", "versioning", "rollback", "alembic"),
    "parquet data lake": ("parquet", "lake", "columnar", "partition"),
    "streaming event ingestion": ("stream", "kafka", "ingestion", "topic"),
    "sql transform models": ("transform", "dbt", "sql", "lineage"),
    "data quality checks": ("quality", "anomaly", "assertion", "profiling"),
    "entity resolution matching": ("entity", "resolution", "matching", "fuzzy"),
    "batch orchestration dags": ("orchestration", "dag", "airflow", "scheduler"),
    "reverse etl to crm": ("etl", "warehouse", "crm", "activation"),
    # devops
    "infrastructure as code": ("terraform", "infrastructure", "provisioning", "iac"),
    "blue green deployments": ("deployment", "cutover", "rollout", "switchover"),
    "cluster autoscaling": ("autoscaling", "kubernetes", "replicas", "hpa"),
    "incident response runbooks": ("incident", "runbook", "oncall", "escalation"),
    "chaos testing": ("chaos", "fault", "injection", "resilience"),
    "cloud cost monitoring": ("cost", "spend", "budget", "anomaly"),
    "observability tracing": ("tracing", "span", "telemetry", "opentelemetry"),
    "secrets management": ("secret", "vault", "rotation", "kms"),
    "container image builds": ("container", "docker", "buildkit"),
    "release pipeline automation": ("release", "cicd", "changelog"),
    # mobile
    "push notifications": ("push", "notification", "fcm", "apns"),
    "offline data sync": ("offline", "sync", "conflict", "replica"),
    "deep link routing": ("deeplink", "universal", "applink"),
    "in app purchases": ("purchase", "iap", "storekit", "paywall"),
    "biometric authentication": ("biometric", "fingerprint", "faceid", "keychain"),
    "mobile crash reporting": ("crash", "stacktrace", "breadcrumb", "symbolication"),
    # games
    "player leaderboards": ("leaderboard", "ranking", "season"),
    "matchmaking queues": ("matchmaking", "lobby", "elo", "queue"),
    "game save system": ("save", "checkpoint", "serialization"),
    "achievements and badges": ("achievement", "badge", "unlock", "progression"),
    # security
    "encryption at rest": ("encryption", "aes", "cipher", "keystore"),
    "key rotation policy": ("rotation", "rekey", "expiry"),
    "penetration test checklist": ("pentest", "vulnerability", "exploit", "checklist"),
    "web application firewall rules": ("waf", "firewall", "owasp", "blocklist"),
    "dependency vulnerability scanning": ("dependency", "vulnerability", "cve", "scanning"),
    "content security policy headers": ("csp", "xss", "nonce", "header"),
    # collaboration
    "inline comment threads": ("comment", "thread", "annotation", "reply"),
    "mentions and tagging": ("mention", "tag", "notify", "autocomplete"),
    "presence indicators": ("presence", "online", "heartbeat", "cursor"),
    "document version history": ("revision", "history", "diff", "restore"),
    "approval workflows": ("approval", "reviewer", "signoff"),
    "realtime collaborative editing": ("collaborative", "crdt", "conflict", "merge"),
    # commerce
    "shopping cart": ("cart", "checkout", "basket", "quantity"),
    "discount codes": ("discount", "coupon", "promo", "voucher"),
    "sales tax calculation": ("tax", "vat", "jurisdiction", "nexus"),
    "shipping rates and labels": ("shipping", "carrier", "label", "tracking"),
    "returns and refunds": ("refund", "rma", "restock"),
    "gift cards and store credit": ("gift", "credit", "balance", "redemption"),
    "abandoned cart recovery": ("abandoned", "cart", "remarketing"),
    "loyalty points program": ("loyalty", "points", "reward", "tier"),
    # content
    "headless cms": ("cms", "headless", "publishing", "editorial"),
    "markdown rendering": ("render", "sanitize", "frontmatter"),
    "image processing pipeline": ("image", "resize", "thumbnail", "webp"),
    "video transcoding": ("video", "transcode", "ffmpeg", "codec"),
    "media asset library": ("asset", "media", "gallery"),
    "seo meta and sitemaps": ("seo", "sitemap", "opengraph"),
    # ops / compliance / growth
    "timesheet tracking": ("timesheet", "clock", "shift", "payroll"),
    "gdpr data deletion": ("gdpr", "deletion", "consent", "retention"),
    "status page and uptime": ("uptime", "monitor", "sla"),
    "split testing experiments": ("experiment", "variant", "allocation", "significance"),
    "sms text alerts": ("sms", "twilio", "shortcode", "optout"),
}
_STACKS: tuple[str, ...] = ("", "in python", "on node", "in go", "with react", "with nextjs",
                            "on postgres", "on aws", "on kubernetes")
#: phrasing templates — {cap} capability, {dom} domain, {art} artifact, {stack} optional stack tail
#: KNOWN LATENT PROPERTY (documented 2026-07-06, row preserved per the ADD-only zoo law): the
#: "requirement: …" template is the one template without {dom}, so two walk positions differing ONLY in
#: domain render the SAME query string. generate() neutralizes this STRUCTURALLY (hardened 2026-07-07):
#: every emitted query is checked against a seen-set and a colliding render is skipped deterministically
#: (the walk just advances to the next stride hit — the axis product is orders of magnitude larger than
#: any requested count, so the count is still reached), which makes query uniqueness hold at EVERY
#: --count — asserted in the self-test at the anchor counts AND at a previously-colliding count, never
#: promised for blessed counts only. A NEW template should still carry all four placeholders so skips
#: stay rare.
_PHRASINGS: tuple[str, ...] = (
    "{cap} for a {dom} {art}{stack}",
    "build me a {dom} {art} that has {cap}{stack}",
    "how do i add {cap} to my {dom} {art}{stack}",
    "need {cap} in the {art} we are building for {dom} customers{stack}",
    "requirement: the {art} must support {cap}{stack}",
    "hey, working on a {art} for {dom} — please wire up {cap}{stack}",
    # scale-out rows (2026-07-06, ADD-only): bug-, migration-, comparison-, best-practice-flavored asks —
    # every template carries all four placeholders so rows stay distinct across every axis
    "the {cap} in our {dom} {art} keeps breaking, help me fix and harden it{stack}",
    "we are migrating our legacy {dom} {art} and need to reimplement {cap}{stack}",
    "what is the best way to add {cap} to a {dom} {art}{stack}",
    "compare approaches for {cap} in a {dom} {art} and implement the winner{stack}",
)


def generate(count: int = _DEFAULT_COUNT) -> list[dict[str, Any]]:
    """A deterministic strided walk of the axis product: same rows every run (no RNG anywhere), the stride
    kept coprime with the inner stack x phrasing period so no inner axis is ever starved, and a seen-set
    skip that guarantees globally-unique queries at every requested count. Rows carry the capability's
    expected tokens (and their phrasing_template index) for verified coverage."""
    caps = sorted(_CAPABILITIES)
    total = len(_DOMAINS) * len(_ARTIFACTS) * len(caps) * len(_STACKS) * len(_PHRASINGS)
    stride = max(1, total // max(1, count))
    # inner-axis starvation guard: a stride sharing a factor with the stack x phrasing period samples only
    # a subset of those axes (e.g. a stride divisible by len(_PHRASINGS) pins ONE template forever), so
    # decrement to the nearest stride coprime with the period — computed from the axes, never a literal.
    inner_period = len(_STACKS) * len(_PHRASINGS)
    while stride > 1 and math.gcd(stride, inner_period) != 1:
        stride -= 1
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    product = itertools.product(range(len(_DOMAINS)), range(len(_ARTIFACTS)), range(len(caps)),
                                range(len(_STACKS)), range(len(_PHRASINGS)))
    for i, (d, a, c, s, p) in enumerate(product):
        if i % stride:
            continue
        cap = caps[c]
        stack = f" {_STACKS[s]}" if _STACKS[s] else ""
        query = _PHRASINGS[p].format(cap=cap, dom=_DOMAINS[d], art=_ARTIFACTS[a], stack=stack)
        if query in seen:  # the {dom}-less template can re-render an emitted ask — skip, walk on
            continue
        seen.add(query)
        rows.append({"record_type": "build_scenario", "domain": _DOMAINS[d], "artifact": _ARTIFACTS[a],
                     "capability": cap, "stack": _STACKS[s] or "any", "phrasing_template": p,
                     "query": query, "expected_tokens": list(_CAPABILITIES[cap]), **BOUNDARY})
        if len(rows) >= count:
            break
    return rows


def corpus_path() -> Path:
    return resource("data") / "dev-intel" / "session_emulation" / _CORPUS_FILENAME


def coverage(cards: list[dict[str, Any]], scenarios: list[dict[str, Any]], *, k: int = 5) -> dict[str, Any]:
    """VERIFIED coverage of the scenarios over ``cards`` via the fast lanes (lexical + stored-dense + their
    fusion — the registers lane is measured separately at suite scale; at 10^4 queries the fast lanes carry
    the sweep). Reuses saas_requirements_bench's verified-hit gate — token-boundary, never substring."""
    from scripts import capability_embedding as _emb  # noqa: PLC0415
    from scripts import rank_fusion_zoo as _f  # noqa: PLC0415
    from scripts.build_primitive_search_index import build_index, search_with_stats  # noqa: PLC0415
    from scripts.saas_requirements_bench import _verified_hit  # noqa: PLC0415  REUSE: the one hit gate
    index = build_index(cards)
    by_id = {c.get("primitive_id"): c for c in cards}
    path = _emb.real_text_path()

    def _lex(q: str, kk: int) -> list[str]:
        hits, _stats = search_with_stats(q, kk, index)
        return [h["primitive_id"] for h in hits]

    def _dense(q: str, kk: int) -> list[str]:
        return [h.get("primitive_id") for h in _emb.intent_query(q, cards, k=kk, path=path)]

    hits_n = 0
    by_artifact: dict[str, list[int]] = {}
    by_capability: dict[str, list[int]] = {}
    misses_sample: list[dict[str, str]] = []
    for sc in scenarios:
        fused = [r["primitive_id"] for r in _f.rrf({"lexical": _lex(sc["query"], k * 4),
                                                    "dense": _dense(sc["query"], k * 4)})][:k]
        hit = _verified_hit([by_id[i] for i in fused if i in by_id], sc["expected_tokens"])
        hits_n += hit
        by_artifact.setdefault(sc["artifact"], []).append(int(hit))
        by_capability.setdefault(sc["capability"], []).append(int(hit))
        if not hit and len(misses_sample) < 40:
            misses_sample.append({"capability": sc["capability"], "artifact": sc["artifact"],
                                  "query": sc["query"]})
    n = len(scenarios) or 1
    return {"record_type": "build_scenario_coverage", "scenarios": len(scenarios), "corpus_cards": len(cards),
            "k": k, "verified_hit_rate": round(hits_n / n, 4),
            "by_artifact": {a: round(sum(v) / len(v), 4) for a, v in sorted(by_artifact.items())},
            "weakest_capabilities": dict(sorted(((c, round(sum(v) / len(v), 4))
                                                 for c, v in by_capability.items()),
                                                key=lambda kv: kv[1])[:10]),
            "misses_sample": misses_sample,
            "note": "verified hits over lexical+dense fusion (fast lanes); misses are corpus-gap acquisition "
                    "leads at scenario scale. Scenario phrasing/axes are synthetic-combinatorial — coverage "
                    "here measures REACH into the real corpus, gold relevance judgments remain roadmap #2.",
            **BOUNDARY}


def token_df_audit(cards: list[dict[str, Any]], *, df_bar: float = _GENERIC_TOKEN_DF_BAR) -> dict[str, Any]:
    """Document-frequency audit of EVERY expected CONCEPT token in _CAPABILITIES over ``cards``, using the
    SAME tokenizer + membership rule as the verified-hit gate (multi-word tokens count when every word is
    present). A token at/above ``df_bar`` is an OFFENDER — generic enough that the one-token OR gate would
    grant vacuous hits at corpus scale. All numbers are computed from the cards, never hand-typed."""
    import re  # noqa: PLC0415
    from scripts.saas_requirements_bench import _card_tokens  # noqa: PLC0415  REUSE: the gate's tokenizer
    watch = sorted({t for toks in _CAPABILITIES.values() for t in toks})
    words_of = {t: [w for w in re.split(r"[^a-z0-9]+", t.lower()) if w] for t in watch}
    n = len(cards) or 1
    df = dict.fromkeys(watch, 0)
    for card in cards:
        toks = _card_tokens(card)
        for t in watch:
            if words_of[t] and all(w in toks for w in words_of[t]):
                df[t] += 1
    by_token = {t: round(df[t] / n, 6) for t in watch}
    offenders = {t: by_token[t] for t in watch if by_token[t] >= df_bar}
    return {"record_type": "expected_token_df_audit", "corpus_cards": len(cards), "tokens": len(watch),
            "df_bar": df_bar, "max_df": max(by_token.values(), default=0.0),
            "offenders": offenders, "by_token": by_token, **BOUNDARY}


def _self_test() -> int:
    checks: list[tuple[str, bool]] = []
    rows = generate(2000)
    checks.append(("generation is deterministic and hits the requested count",
                   len(rows) == 2000 and rows == generate(2000)))
    checks.append(("no duplicate queries (every scenario is a distinct ask)",
                   len({r["query"] for r in rows}) == len(rows)))
    checks.append(("every axis is exercised at 2K rows (domains, artifacts, capabilities, stacks, phrasings)",
                   {r["domain"] for r in rows} == set(_DOMAINS)
                   and {r["artifact"] for r in rows} == set(_ARTIFACTS)
                   and {r["capability"] for r in rows} == set(_CAPABILITIES)
                   and {r["stack"] for r in rows} == {s or "any" for s in _STACKS}
                   and {r["phrasing_template"] for r in rows} == set(range(len(_PHRASINGS)))))
    checks.append(("every row carries specific expected tokens (verified coverage is possible)",
                   all(r["expected_tokens"] and all(len(t) >= 3 for t in r["expected_tokens"]) for r in rows)))
    big = generate(30000)
    checks.append(("the generator scales to tens of thousands deterministically",
                   len(big) == 30000 and big[0] == rows[0]))
    checks.append(("no duplicate queries at the default count",
                   len({r["query"] for r in big}) == len(big)))
    # a count whose naive stride used to BOTH collide (896 duplicate queries) and starve inner axes
    # (5/9 stacks, 5/10 phrasings) before the coprime-stride guard + seen-set skip landed
    rows_adv = generate(12250)
    checks.append(("globally-unique queries and full count at a previously-colliding count",
                   len({r["query"] for r in rows_adv}) == len(rows_adv) == 12250))
    cap_token_sets = {c: frozenset(t) for c, t in _CAPABILITIES.items()}
    checks.append(("capability token contracts are differentiated (pairwise overlap <= 1 token)",
                   all(len(cap_token_sets[a] & cap_token_sets[b]) <= 1
                       for a, b in itertools.combinations(sorted(cap_token_sets), 2))))
    # hermetic coverage: a capability the tiny corpus covers hits; one it cannot cover misses honestly
    cards = [{"primitive_id": "s:auth", "title": "OAuth login handler",
              "blackbox": "Handle oauth login and issue a session token.", "input_edge": "In",
              "output_edge": "Out", **BOUNDARY}]
    sample = [r for r in rows if r["capability"] == "user login and accounts"][:3] + \
             [r for r in rows if r["capability"] == "map with locations"][:3]
    cov = coverage(cards, sample, k=1)
    checks.append(("verified coverage: covered capability hits, uncovered capability is an honest miss",
                   cov["verified_hit_rate"] == 0.5 and len(cov["misses_sample"]) == 3))
    checks.append(("coverage receipt is deterministic (byte-identical twice)",
                   json.dumps(coverage(cards, sample, k=1), sort_keys=True)
                   == json.dumps(coverage(cards, sample, k=1), sort_keys=True)))
    # hermetic df-audit mutation gate: a token carried by 3/4 tiny cards is flagged generic at a 0.5 bar,
    # a token carried by 1/4 is cleared — the audit can go RED, it is not a rubber stamp
    audit_cards = [{"primitive_id": f"s:aud{i}", "title": "OAuth connector",
                    "blackbox": "Wire oauth for the app.", "input_edge": "In", "output_edge": "Out",
                    **BOUNDARY} for i in range(3)]
    audit_cards.append({"primitive_id": "s:aud3", "title": "Geocode lookup",
                        "blackbox": "Geocode an address.", "input_edge": "In", "output_edge": "Out",
                        **BOUNDARY})
    aud = token_df_audit(audit_cards, df_bar=0.5)
    checks.append(("token df audit flags a generic token and clears a rare one (hermetic)",
                   "oauth" in aud["offenders"] and "geocode" not in aud["offenders"]
                   and aud["by_token"]["geocode"] == 0.25 and aud["corpus_cards"] == 4))
    checks.append(("rows + receipts are candidate/serves_truth=false",
                   rows[0]["serves_truth"] is False and cov["serves_truth"] is False
                   and aud["serves_truth"] is False))

    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print(f"\nPASS - build_scenario_corpus: a deterministic strided walk of {len(_DOMAINS)} domains x "
          f"{len(_ARTIFACTS)} artifacts x {len(_CAPABILITIES)} capabilities x {len(_STACKS)} stacks x "
          f"{len(_PHRASINGS)} phrasings — tens of thousands of distinct build-anything scenarios with "
          f"specific expected tokens, verified-coverage machinery reused, byte-stable. serves_truth=false.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--write", action="store_true", help="generate + write the scenario corpus JSONL")
    ap.add_argument("--coverage", action="store_true", help="verified coverage sweep over the real corpus")
    ap.add_argument("--token-audit", action="store_true",
                    help="df-audit every expected token over the real corpus; fails on generic tokens")
    ap.add_argument("--count", type=int, default=_DEFAULT_COUNT)
    ap.add_argument("--sample", type=int, default=None, help="cap the coverage sweep (default: ALL scenarios)")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.write:
        rows = generate(args.count)
        with corpus_path().open("w", encoding="utf-8") as fh:
            for r in rows:
                fh.write(json.dumps(r, sort_keys=True) + "\n")
        print(f"written {len(rows)} scenarios to {corpus_path()}")
        return 0
    if args.token_audit:
        from scripts import path_graph_bench as _bench  # noqa: PLC0415
        cards = _bench._load_scale_corpus(None)  # noqa: SLF001
        rec = token_df_audit(cards)
        print(json.dumps({kk: rec[kk] for kk in ("corpus_cards", "tokens", "df_bar", "max_df", "offenders")},
                         indent=2, sort_keys=True))
        ok = not rec["offenders"]
        print("PASS - every expected concept token stays under the generic-df bar" if ok
              else f"FAIL - {len(rec['offenders'])} generic token(s) at/above the df bar")
        return 0 if ok else 1
    if args.coverage:
        from scripts import path_graph_bench as _bench  # noqa: PLC0415
        from scripts._jsonl import read_jsonl_tolerant  # noqa: PLC0415
        scenarios = read_jsonl_tolerant(corpus_path())
        if args.sample:
            step = max(1, len(scenarios) // args.sample)
            scenarios = scenarios[::step][:args.sample]
        cards = _bench._load_scale_corpus(None)  # noqa: SLF001
        print(f"verified coverage: {len(scenarios)} scenarios over {len(cards)} cards ...")
        rec = coverage(cards, scenarios)
        out = resource("data") / "dev-intel" / "session_emulation" / "build_scenario_coverage_receipt.json"
        out.write_text(json.dumps(rec, indent=2, sort_keys=True))
        print(json.dumps({kk: rec[kk] for kk in ("scenarios", "verified_hit_rate", "by_artifact",
                                                 "weakest_capabilities")}, indent=2, sort_keys=True))
        print(f"\nwritten: {out}")
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
