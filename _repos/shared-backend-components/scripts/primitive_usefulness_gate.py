#!/usr/bin/env python3
"""scripts.primitive_usefulness_gate — the anti-placeholder gate: deterministic, model-free PURE-FUNCTION
criteria that measure whether a primitive card is USEFUL (concrete mechanism, real tool signals, actionable
steps, typed edges) or a stamped PLACEHOLDER (scaffold prose, restated title, generic edges, template
clusters). Criteria are ROWS in a registry (multi-path law): the placeholder-audit fleet's measured rubric
merges in as new rows, never a rewrite. Produces a placeholder-rate receipt over stratified samples of every
card namespace plus an ENRICHED-vs-PLAIN grading of the enrichment engine's output (the same cards scored
with and without their enrichment — the queue's "grade enriched vs plain" verification).

Grades are CANDIDATE signals for the funnel (review routing / enrichment targeting) — never promotion, never
truth. A "pass" here does not make a card serveable; a "placeholder" verdict does not delete it (the funnel
decides; nothing is destroyed).

    PYTHONPATH=. python3 scripts/primitive_usefulness_gate.py --self-test
    PYTHONPATH=. python3 scripts/primitive_usefulness_gate.py --run [--cap 20000]
"""
from __future__ import annotations

import sys
from pathlib import Path

# ── substrate-root bootstrap (sentinel; mirrors scripts/enrich_minted_primitives.py) ─────────────────────────
_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots, resource  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import re  # noqa: E402
import zlib  # noqa: E402
from typing import Any, Callable, Optional  # noqa: E402

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}

# chars: the shortest genuine one-clause mechanism sentence observed in the verified corpus is ~45 chars;
# below this a blackbox cannot name a mechanism AND a subject.
_MIN_BLACKBOX_CHARS = 40
# a blackbox must add at least this many content tokens beyond its own title to be more than a restatement.
_MIN_NOVEL_CONTENT_TOKENS = 3
# template stamping: a skeleton cluster is "stamped" when it has at least this many members. Absolute, not
# pool-fraction — a fraction threshold lets variant families hide in large pools (measured: the minted pool's
# phrasing variants each stayed under 0.5% of a 20K sample and scored 0.0 despite being template-generated
# by construction). Short skeletons collapse too easily after wildcarding, so they never stamp.
_STAMP_MIN_CLUSTER = 5
_STAMP_MIN_SKELETON_TOKENS = 6
# steps are vague when at least this fraction of them fail the actionability rule.
_VAGUE_STEP_FRACTION = 0.5
# --run stride-sampling cap per namespace (pure functions are cheap; the cap bounds worst-case runtime).
_DEFAULT_SAMPLE_CAP = int(os.environ.get("OH_USEFULNESS_SAMPLE_CAP", "20000"))

_STOPWORDS = frozenset(
    "a an the and or of for to in on with via by from into over under as is are be been this that it its "
    "their our your his her they we you i at any all each per não only very more most other another some "
    "such no not but if then else when where which who whom whose what how why can could may might shall "
    "should will would must do does did done have has had having".split())

# real tool / protocol / format signals (lowercased membership test on blackbox tokens). A curated seed —
# the CamelCase / acronym / digit / file-extension patterns below carry the long tail, and the fleet rubric
# extends this as data. Presence of ANY signal = the card names something concrete.
_CONCRETE_TOOL_TOKENS = frozenset("""
postgres postgresql redis kafka rabbitmq sqlite mysql mariadb mongodb elasticsearch opensearch clickhouse
bigquery pgvector faiss hnswlib numpy pandas sklearn scikit pytorch tensorflow onnx ffmpeg opencv tesseract
saml oauth oauth2 oidc jwt tls ssl https http2 grpc websocket webhook graphql smtp imap pop3 dns cdn docker
kubernetes k8s terraform ansible nginx caddy github gitlab bitbucket stripe twilio sendgrid mailgun
playwright selenium puppeteer beautifulsoup scrapy airflow dagster dbt spark flink parquet avro protobuf
jsonl csv yaml toml regex sha256 crc32 hmac aes rsa argon2 bcrypt scrypt ldap sso mfa totp webauthn fido2
openai anthropic ollama huggingface minhash simhash bm25 tfidf embedding embeddings rerank levenshtein
jaccard websockets fastapi flask django celery gunicorn uvicorn pydantic sqlalchemy alembic prometheus
grafana opentelemetry jaeger s3 gcs r2 lambda cloudflare vercel fly render supabase firebase
""".split())

_VAGUE_STEP_VERBS = frozenset(
    "process handle manage integrate leverage utilize ensure support address consider optimize streamline "
    "facilitate coordinate oversee enhance improve".split())

# edge names that carry no type information once normalized (alpha-only, lowercased). "SsoRequest" survives
# (normalizes to "ssorequest", not in the set); a bare "Request" does not.
_GENERIC_EDGE_NAMES = frozenset(
    "in out input output data result results payload request response item items record records info object "
    "message event value values content thing stuff generic any none".split())

# stamped-scaffold prose: each pattern is a known generator fingerprint observed in the staged pools.
_SCAFFOLD_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"vendorable .{0,40}component for the [a-z_ ]+ plane", re.IGNORECASE),
    re.compile(r"is under-covered", re.IGNORECASE),
    re.compile(r"could seed a (ladder|plane)", re.IGNORECASE),
    # a single pure hedge clause ("Provides X for a Y.") with nothing after it
    re.compile(r"^(provides|supports|enables|handles|offers|implements) [a-z ,\-]+ for (a|an|the|your)?"
               r" ?[a-z \-]+\.?$", re.IGNORECASE),
)

# high-precision GENERATOR-TEMPLATE fingerprints harvested + grounded on real pools (gate wave 2): the
# `Calls X with Y and returns Z.` signature echo fires on 39% of edge cards and 0% of verified (a literal
# mechanism-free template); the capability-slot frames fire on 100% of minted_gap and 0% of verified (they
# name a capability + tokens but no MECHANISM — the exact gap the LLM audit fleet flagged 100% placeholder).
_CALLS_SIGNATURE_RE = re.compile(r"Calls\s+\S+\s+with\s+.+\s+and\s+returns\s+.+\.\s*$", re.IGNORECASE)
_MINT_CAPABILITY_SLOT_RE = re.compile(
    r"a working .+ capability:|[-\s]in module that adds |the .+ gap in .+ by shipping", re.IGNORECASE)
_CAMELCASE_RE = re.compile(r"\b[A-Z][a-z0-9]+(?:[A-Z][a-z0-9]+)+\b")
_ACRONYM_RE = re.compile(r"\b[A-Z]{2,6}\b")
_DIGIT_RE = re.compile(r"\d")
_FILEEXT_RE = re.compile(r"\b\w+\.(?:py|js|ts|json|jsonl|csv|xml|yaml|yml|toml|sql|proto|md|html)\b")
_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _content_tokens(text: str) -> set[str]:
    return {t for t in _TOKEN_RE.findall((text or "").lower()) if t not in _STOPWORDS and len(t) > 2}


def _edge_name(value: Any) -> str:
    if isinstance(value, dict):
        value = value.get("name") or value.get("edge") or value.get("type") or ""
    return str(value or "")


def _edge_is_generic(value: Any) -> bool:
    normalized = re.sub(r"[^a-z]", "", _edge_name(value).lower())
    return bool(normalized) and normalized in _GENERIC_EDGE_NAMES


def _card_text_fields(card: dict[str, Any]) -> tuple[str, str, Optional[list[str]]]:
    """(blackbox, title, steps-or-None). Steps come from the card or its enrichment; None = not applicable."""
    raw_blackbox = card.get("blackbox")
    if isinstance(raw_blackbox, dict):  # edge cards carry structured blackboxes — grade their text values
        blackbox = " ".join(str(v) for v in raw_blackbox.values() if isinstance(v, (str, int, float)))
    else:
        blackbox = str(raw_blackbox or "")
    title = str(card.get("title") or "")
    steps = card.get("steps")
    if steps is None and isinstance(card.get("enriched"), dict):
        steps = card["enriched"].get("steps")
    if not isinstance(steps, list) or not steps:
        steps = None
    return blackbox, title, steps


# ── the criteria registry: each row is (name, kind, applies(card)->bool, flag(card)->bool, rationale). ──────
# Adding a fleet-rubric criterion = appending a row here; the receipt picks it up computed, never re-typed.

def _crit_blackbox_missing_or_stub(card: dict[str, Any]) -> bool:
    blackbox, _, _ = _card_text_fields(card)
    return len(blackbox.strip()) < _MIN_BLACKBOX_CHARS


def _crit_blackbox_generic_scaffold(card: dict[str, Any]) -> bool:
    blackbox, _, _ = _card_text_fields(card)
    return any(p.search(blackbox) for p in _SCAFFOLD_PATTERNS)


def _crit_title_restatement(card: dict[str, Any]) -> bool:
    blackbox, title, _ = _card_text_fields(card)
    if not blackbox or not title:
        return False
    novel = _content_tokens(blackbox) - _content_tokens(title)
    return len(novel) < _MIN_NOVEL_CONTENT_TOKENS


def _crit_generic_edge_names(card: dict[str, Any]) -> bool:
    return _edge_is_generic(card.get("input_edge")) or _edge_is_generic(card.get("output_edge"))


def _crit_no_concrete_token(card: dict[str, Any]) -> bool:
    blackbox, _, _ = _card_text_fields(card)
    if not blackbox:
        return True
    if _content_tokens(blackbox) & _CONCRETE_TOOL_TOKENS:
        return False
    return not (_CAMELCASE_RE.search(blackbox) or _ACRONYM_RE.search(blackbox)
                or _DIGIT_RE.search(blackbox) or _FILEEXT_RE.search(blackbox))


def _steps_applicable(card: dict[str, Any]) -> bool:
    return _card_text_fields(card)[2] is not None


def _crit_calls_signature_echo(card: dict[str, Any]) -> bool:
    """The `Calls X with Y and returns Z.` template — a mechanism-free signature echo (39% of edge cards,
    0% of verified). A literal generator fingerprint: HARD."""
    blackbox, _, _ = _card_text_fields(card)
    return bool(_CALLS_SIGNATURE_RE.search(blackbox.strip()))


def _crit_mint_capability_slot(card: dict[str, Any]) -> bool:
    """The mint capability-slot frames ("a working X capability:", "-in module that adds", "the X gap in Y by
    shipping") — they name a capability + tokens but NO mechanism (100% of minted_gap, 0% of verified). SOFT:
    pairs with no_concrete_token to route the card to enrichment, never a standalone discard."""
    blackbox, _, _ = _card_text_fields(card)
    return bool(_MINT_CAPABILITY_SLOT_RE.search(blackbox))


def _crit_vague_steps(card: dict[str, Any]) -> bool:
    _, _, steps = _card_text_fields(card)
    if steps is None:  # honesty: absence of steps is a tier fact (consumability audit), not vagueness
        return False
    def vague(step: Any) -> bool:
        words = str(step).strip().split()
        first = re.sub(r"[^a-z]", "", words[0].lower()) if words else ""
        return first in _VAGUE_STEP_VERBS or len(_content_tokens(str(step))) < 3
    return sum(1 for s in steps if vague(s)) >= max(1, int(len(steps) * _VAGUE_STEP_FRACTION))


CRITERIA: list[dict[str, Any]] = [
    {"name": "blackbox_missing_or_stub", "kind": "length", "severity": "hard",
     "applies": lambda c: True, "flag": _crit_blackbox_missing_or_stub,
     "rationale": f"a blackbox under {_MIN_BLACKBOX_CHARS} chars cannot name a mechanism and a subject"},
    {"name": "blackbox_generic_scaffold", "kind": "regex", "severity": "hard",
     "applies": lambda c: True, "flag": _crit_blackbox_generic_scaffold,
     "rationale": "known generator scaffold fingerprints (hedge clauses, plane/ladder seeding prose)"},
    {"name": "calls_signature_echo", "kind": "regex", "severity": "hard",
     "applies": lambda c: True, "flag": _crit_calls_signature_echo,
     "rationale": "the mechanism-free `Calls X with Y and returns Z.` template (39% of edge cards, 0% verified)"},
    {"name": "mint_capability_slot", "kind": "regex", "severity": "soft",
     "applies": lambda c: True, "flag": _crit_mint_capability_slot,
     "rationale": "capability-slot frame naming a capability but no mechanism (100% of minted_gap, 0% verified)"},
    {"name": "title_restatement", "kind": "token", "severity": "soft",
     "applies": lambda c: True, "flag": _crit_title_restatement,
     "rationale": f"blackbox adds <{_MIN_NOVEL_CONTENT_TOKENS} content tokens beyond the title"},
    {"name": "generic_edge_names", "kind": "token", "severity": "soft",
     "applies": lambda c: True, "flag": _crit_generic_edge_names,
     "rationale": "an edge named In/Out/Data/Result carries no type information for composition"},
    {"name": "no_concrete_token", "kind": "token", "severity": "soft",
     "applies": lambda c: True, "flag": _crit_no_concrete_token,
     "rationale": "no real-tool token, CamelCase type, acronym, digit, or file extension anywhere"},
    {"name": "vague_steps", "kind": "token", "severity": "soft",
     "applies": _steps_applicable, "flag": _crit_vague_steps,
     "rationale": "steps dominated by process/handle/manage verbs or <3 content tokens each"},
]

# template_stamped is pool-level (needs cluster context) — reported alongside the per-card criteria.
_TEMPLATE_STAMPED = "template_stamped"
_HARD_CRITERIA = frozenset(c["name"] for c in CRITERIA if c["severity"] == "hard") | {_TEMPLATE_STAMPED}
_SOFT_CRITERIA = frozenset(c["name"] for c in CRITERIA if c["severity"] == "soft")
# verdict: any hard flag => placeholder; >=2 soft flags => placeholder; exactly 1 soft flag => weak.
_SOFT_FLAGS_FOR_PLACEHOLDER = 2


def _skeleton(card: dict[str, Any]) -> str:
    """Scaffold fingerprint: blackbox with digits + card-specific tokens (title/capability/artifact words)
    wildcarded — identical skeletons across many cards = one generator stamp."""
    blackbox, title, _ = _card_text_fields(card)
    specific = _content_tokens(title) | _content_tokens(str(card.get("capability") or "")) \
        | _content_tokens(str(card.get("artifact") or "")) \
        | _content_tokens(" ".join(str(t) for t in (card.get("capability_tags") or [])))
    tokens = [("*" if t in specific else re.sub(r"\d+", "#", t))
              for t in (blackbox or "").lower().split()]
    return " ".join(tokens)


def _skeleton_key(card: dict[str, Any]) -> str:
    return f"{zlib.crc32(_skeleton(card).encode('utf-8')):08x}"


def stamped_keys(cards: list[dict[str, Any]]) -> dict[str, int]:
    """Skeleton keys whose cluster is big enough to be a generator stamp within THIS pool (on a sample the
    cluster sizes are lower bounds — the receipt labels the sample size)."""
    counts: dict[str, int] = {}
    long_enough: set[str] = set()
    for card in cards:
        blackbox = _card_text_fields(card)[0]
        if blackbox.strip():
            key = _skeleton_key(card)
            counts[key] = counts.get(key, 0) + 1
            if len(_skeleton(card).split()) >= _STAMP_MIN_SKELETON_TOKENS:
                long_enough.add(key)
    return {k: v for k, v in counts.items() if v >= _STAMP_MIN_CLUSTER and k in long_enough}


def evaluate_card(card: dict[str, Any], *, stamped: Optional[dict[str, int]] = None) -> dict[str, Any]:
    """Pure per-card evaluation. `stamped` (from stamped_keys over the pool) adds the pool-level criterion."""
    flags = [c["name"] for c in CRITERIA if c["applies"](card) and c["flag"](card)]
    na = [c["name"] for c in CRITERIA if not c["applies"](card)]
    if stamped and _card_text_fields(card)[0].strip() and _skeleton_key(card) in stamped:
        flags.append(_TEMPLATE_STAMPED)
    soft_hits = sum(1 for f in flags if f in _SOFT_CRITERIA)
    if any(f in _HARD_CRITERIA for f in flags) or soft_hits >= _SOFT_FLAGS_FOR_PLACEHOLDER:
        verdict = "placeholder"
    elif soft_hits == 1:
        verdict = "weak"
    else:
        verdict = "pass"
    return {"primitive_id": str(card.get("primitive_id") or card.get("id") or ""),
            "flags": flags, "not_applicable": na, "verdict": verdict}


def _card_like(row: dict[str, Any]) -> bool:
    return bool((row.get("primitive_id") or row.get("id"))
                and (row.get("title") or row.get("blackbox")))


def measure_pool(cards: list[dict[str, Any]], pool_name: str) -> dict[str, Any]:
    """Placeholder-rate measurement over one pool (or stratified sample). All numbers computed."""
    card_rows = [c for c in cards if isinstance(c, dict) and _card_like(c)]
    stamped = stamped_keys(card_rows)
    results = [evaluate_card(c, stamped=stamped) for c in card_rows]
    n = len(results)
    flag_counts: dict[str, int] = {}
    applicable: dict[str, int] = {}
    for c in CRITERIA:
        applicable[c["name"]] = sum(1 for card in card_rows if c["applies"](card))
    applicable[_TEMPLATE_STAMPED] = n
    for r in results:
        for f in r["flags"]:
            flag_counts[f] = flag_counts.get(f, 0) + 1
    verdicts = {v: sum(1 for r in results if r["verdict"] == v) for v in ("pass", "weak", "placeholder")}
    top_stamps = sorted(stamped.items(), key=lambda kv: -kv[1])[:5]
    stamp_examples = []
    for key, count in top_stamps:
        example = next((c for c in card_rows if _skeleton_key(c) == key), None)
        if example is not None:
            stamp_examples.append({"cluster_size": count,
                                   "skeleton_excerpt": _skeleton(example)[:140]})
    return {
        "pool": pool_name, "n_rows_seen": len(cards), "n_cards_scored": n,
        "non_card_rows": len(cards) - n,
        "criterion_rates": {name: round(flag_counts.get(name, 0) / max(1, applicable.get(name, 0)), 4)
                            for name in sorted(applicable)},
        "criterion_applicable": {k: applicable[k] for k in sorted(applicable)},
        "verdict_counts": verdicts,
        "placeholder_rate": round(verdicts["placeholder"] / max(1, n), 4),
        "weak_rate": round(verdicts["weak"] / max(1, n), 4),
        "stamped_clusters": len(stamped),
        "stamped_examples": stamp_examples,
        **BOUNDARY,
    }


def enriched_vs_plain(enriched_rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Grade the SAME cards with and without their enrichment (in-memory views; nothing rewritten). The
    enrichment engine wins iff the enriched view's placeholder rate is strictly lower."""
    plain_views: list[dict[str, Any]] = []
    enriched_views: list[dict[str, Any]] = []
    for row in enriched_rows:
        e = row.get("enriched")
        if not isinstance(e, dict) or not e.get("blackbox"):
            continue
        plain = {k: v for k, v in row.items() if k != "enriched"}
        plain_views.append(plain)
        enriched_views.append({**plain, "blackbox": str(e.get("blackbox") or ""),
                               "steps": list(e.get("steps") or [])})
    plain_m = measure_pool(plain_views, "enriched_pool_PLAIN_view")
    enriched_m = measure_pool(enriched_views, "enriched_pool_ENRICHED_view")
    return {"n_pairs": len(plain_views), "plain": plain_m, "enriched": enriched_m,
            "placeholder_rate_delta": round(plain_m["placeholder_rate"] - enriched_m["placeholder_rate"], 4),
            "enrichment_wins": enriched_m["placeholder_rate"] < plain_m["placeholder_rate"],
            **BOUNDARY}


def _stride_sample(rows: list[dict[str, Any]], cap: int) -> list[dict[str, Any]]:
    if len(rows) <= cap:
        return rows
    step = max(1, len(rows) // cap)
    return rows[::step][:cap]


def _namespaces() -> list[tuple[str, Path]]:
    foundry = resource("data") / "dev-intel" / "aidevobserver_edge_foundry"
    return [
        ("verified_factory", foundry / "verified_factory_primitive_cards.jsonl"),
        ("edge_cards", foundry / "primitive_edge_cards.jsonl"),
        ("minted_gap", foundry / "minted_gap_primitive_candidates.jsonl"),
        ("enriched_staged", foundry / "enriched_primitive_candidates.jsonl"),
    ]


def run_gate(cap: int = _DEFAULT_SAMPLE_CAP) -> dict[str, Any]:
    from scripts._jsonl import read_jsonl_tolerant  # noqa: PLC0415
    pools: dict[str, Any] = {}
    enriched_rows: list[dict[str, Any]] = []
    for name, path in _namespaces():
        if not path.exists():
            pools[name] = {"pool": name, "missing_file": str(path), **BOUNDARY}
            continue
        rows = read_jsonl_tolerant(path)
        sample = _stride_sample(rows, cap)
        pools[name] = measure_pool(sample, name)
        pools[name]["n_pool_total"] = len(rows)
        pools[name]["sampled"] = len(sample) < len(rows)
        if name == "enriched_staged":
            enriched_rows = rows
    receipt = {"record_type": "primitive_usefulness_gate_receipt", "schema_version": 1,
               "sample_cap": cap, "pools": pools,
               "enriched_vs_plain": (enriched_vs_plain(enriched_rows) if enriched_rows
                                     else {"n_pairs": 0, "note": "no enriched staged rows found"}),
               "criteria": [{k: c[k] for k in ("name", "kind", "severity", "rationale")} for c in CRITERIA]
               + [{"name": _TEMPLATE_STAMPED, "kind": "cluster", "severity": "hard",
                   "rationale": f"skeleton cluster >= {_STAMP_MIN_CLUSTER} members (skeletons under "
                                f"{_STAMP_MIN_SKELETON_TOKENS} tokens never stamp)"}],
               **BOUNDARY}
    return receipt


def _receipt_path() -> Path:
    return resource("data") / "dev-intel" / "session_emulation" / "usefulness_gate_receipt.json"


# ── self-test: every criterion must be individually trippable (mutation gate) and the good card must pass ───

def _good_card() -> dict[str, Any]:
    return {"primitive_id": "ug:good", "title": "Single sign on middleware for SaaS web app",
            "blackbox": "Validates SAML assertions via python3-saml against a cached IdP metadata store, "
                        "mints a JWT session with a 15 minute TTL, and falls back to OIDC via authlib.",
            "input_edge": "SamlAssertionBatch", "output_edge": "MintedSessionToken",
            "steps": ["parse the IdP metadata XML with lxml", "validate the assertion signature",
                      "mint the JWT session token with a 15m TTL"], **BOUNDARY}


def _self_test() -> int:
    checks: list[tuple[str, bool]] = []
    good = _good_card()
    good_eval = evaluate_card(good)
    checks.append(("a realistic concrete card passes with zero flags",
                   good_eval["verdict"] == "pass" and good_eval["flags"] == []))

    trip_fixtures: dict[str, dict[str, Any]] = {
        "blackbox_missing_or_stub": {**good, "blackbox": "Does SSO."},
        "blackbox_generic_scaffold": {**good, "blackbox": "vendorable MIT component for the "
                                      "workflow_orchestration plane; workflow_orchestration is under-covered"},
        "title_restatement": {**good, "blackbox": "Middleware providing single sign on for a SaaS web app."},
        "generic_edge_names": {**good, "input_edge": "Data"},
        "no_concrete_token": {**good, "blackbox": "Seamlessly connects identity between the platform and "
                              "the workspace so people gain entrance without friction across the estate."},
        "vague_steps": {**good, "steps": ["process the data", "handle errors", "manage the flow"]},
        "calls_signature_echo": {**good, "blackbox": "Calls SsoMiddleware with SsoRequest and returns SsoResult."},
        "mint_capability_slot": {**good, "blackbox": "Gives a SaaS web app a working single sign on capability: "
                                 "sso, saml, oidc handled in one governed typed path."},
    }
    for name, fixture in trip_fixtures.items():
        flags = evaluate_card(fixture)["flags"]
        checks.append((f"mutation gate: '{name}' is individually trippable", name in flags))
    checks.append(("the good card trips none of the trip-fixtures' criteria",
                   not set(trip_fixtures) & set(good_eval["flags"])))

    stamped_pool = [{**good, "primitive_id": f"ug:s{i}",
                     "title": f"Widget {i} orchestrator",
                     "blackbox": f"vendorable component for the widget{i} plane; stamped filler prose here"}
                    for i in range(6)]
    organic_pool = [good, {**good, "primitive_id": "ug:o2", "title": "OCR intake for scanned invoices",
                           "blackbox": "Runs tesseract 5 with a preprocessing pass in opencv, emits "
                                       "hOCR plus a confidence histogram per page."}]
    m = measure_pool(stamped_pool + organic_pool, "fixture")
    stamped_flagged = sum(1 for c in stamped_pool
                          if _TEMPLATE_STAMPED in evaluate_card(c, stamped=stamped_keys(stamped_pool
                                                                                        + organic_pool))["flags"])
    checks.append(("template stamping: the 6 clones are cluster-flagged, the 2 organic cards are not",
                   stamped_flagged == 6 and m["stamped_clusters"] >= 1
                   and _TEMPLATE_STAMPED not in evaluate_card(good, stamped=stamped_keys(stamped_pool
                                                                                         + organic_pool))["flags"]))
    checks.append(("verdicts split hard: stamped pool placeholder-rated, organic passes",
                   m["verdict_counts"]["placeholder"] >= 6 and m["verdict_counts"]["pass"] >= 2))

    no_steps = {k: v for k, v in good.items() if k != "steps"}
    ev = evaluate_card(no_steps)
    checks.append(("honesty: a card without steps is NOT flagged vague_steps (criterion not-applicable)",
                   "vague_steps" not in ev["flags"] and "vague_steps" in ev["not_applicable"]))

    distinct_mechanisms = [
        ("Token-bucket limiter on redis INCR inside a lua script, returns 429 with Retry-After.",
         ["create the redis lua token bucket script", "wire the middleware to return 429"]),
        ("nginx limit_req zone with burst and nodelay, keyed on the API key header.",
         ["define the limit_req_zone in nginx.conf", "key the zone on the X-Api-Key header"]),
        ("Envoy global rate limit service over gRPC with descriptors per route.",
         ["deploy the envoy ratelimit service", "declare descriptors per route in the filter"]),
        ("Sliding-window counter in postgres with an advisory lock per tenant row.",
         ["create the window table with a tenant index", "take the advisory lock before increment"]),
        ("Leaky-bucket drain worker over a rabbitmq queue with per-user credits.",
         ["declare the credits exchange in rabbitmq", "run the drain worker on a 100ms tick"]),
        ("GCRA implementation with redis TTL math, no lua, single EVAL-free roundtrip.",
         ["compute the theoretical arrival time", "store it under a redis key with TTL"]),
    ]
    enriched_fixture = [{"primitive_id": f"ug:e{i}", "title": f"Rate limiting engine variant {i}",
                         "blackbox": f"vendorable component for the rate{i} plane; filler",
                         "input_edge": "Data", "output_edge": "Result",
                         "enriched": {"blackbox": mech, "steps": steps}}
                        for i, (mech, steps) in enumerate(distinct_mechanisms)]
    cmp_rec = enriched_vs_plain(enriched_fixture)
    checks.append(("enriched-vs-plain: enrichment strictly lowers the placeholder rate on the fixture",
                   cmp_rec["enrichment_wins"] and cmp_rec["placeholder_rate_delta"] > 0
                   and cmp_rec["n_pairs"] == 6))
    checks.append(("grading is a VIEW: originals untouched (no card mutated)",
                   "enriched" in enriched_fixture[0] and enriched_fixture[0]["blackbox"].startswith("vendorable")))

    twice = [json.dumps(measure_pool(stamped_pool + organic_pool, "fixture"), sort_keys=True)
             for _ in range(2)]
    checks.append(("determinism: identical pool -> byte-identical measurement", twice[0] == twice[1]))
    checks.append(("receipts carry the candidate boundary",
                   m["candidate"] is True and m["serves_truth"] is False))

    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print("\nPASS - primitive_usefulness_gate: deterministic anti-placeholder criteria (stub/scaffold/"
          "restatement/generic-edge/no-concrete-token/vague-steps + pool-level template stamping), each "
          "individually mutation-trippable; enriched-vs-plain grading as in-memory views; verdicts are "
          "candidate signals for the funnel, never promotion. serves_truth=false.")
    return 0


def _run(cap: int) -> int:
    receipt = run_gate(cap)
    out = _receipt_path()
    out.write_text(json.dumps(receipt, indent=2, sort_keys=True))
    summary = {name: {"placeholder_rate": p.get("placeholder_rate"), "n": p.get("n_cards_scored")}
               for name, p in receipt["pools"].items() if "placeholder_rate" in p}
    evp = receipt["enriched_vs_plain"]
    print(json.dumps({"pools": summary,
                      "enriched_vs_plain": {k: evp.get(k) for k in
                                            ("n_pairs", "placeholder_rate_delta", "enrichment_wins")}},
                     indent=2))
    print(f"\nreceipt: {out}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--run", action="store_true", help="measure every namespace + enriched-vs-plain grading")
    ap.add_argument("--cap", type=int, default=_DEFAULT_SAMPLE_CAP,
                    help="stride-sample cap per namespace (pure functions; cap bounds runtime)")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.run:
        return _run(args.cap)
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
