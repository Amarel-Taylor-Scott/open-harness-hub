#!/usr/bin/env python3
"""semantic_linker_resolve — the RESOLVE step of the semantic linker: capability plan -> verified primitives.

The semantic-linker pipeline (owner vision 2026-07-09):

    human intent -> LLM emits a compact CAPABILITY PLAN (graph IR)
                 -> [THIS MODULE] resolve the plan to VERIFIED implementations (retrieve + BLOCK)
                 -> deterministic assembler wires them -> compiler/tests/policies validate.

This module owns the middle step: given a compact plan (a list of capability intents + a policy), it resolves each
capability to the best-matching VERIFIED primitive by retrieving over the multivector FACET store
(`primitive_facet_enrichment.facet_search` — the 10.28M-vector semantic envelope), then applies HARD BLOCKERS
(policy/effect + type-fit). Per the vision's non-negotiable rule: **retrieval is probabilistic; acceptance is
deterministic** — a blocker is invalidation, never a softened ranking feature. Unmet capabilities become explicit
RESIDUAL specs (the novel code the LLM must author), so a registry miss never silently reverts to unrestricted
generation. Output: a resolved graph + a LOCK (capability -> primitive_id) + residuals + a STRUCTURAL token-savings
projection.

Boundaries (avoids colliding with the concurrent Codex lane):
- The primitive DATA / semantic ABI manifest is `primitive_semantic_abi_registry.py` (Codex) — consumed here, not
  redefined. The LIVE end-to-end token measurement is `semantic_linker_long_session_benchmark.py` (Codex) — this
  module emits a STRUCTURAL projection only (bytes-of-implementation avoided), and points at that benchmark for the
  live number. Retrieval is `primitive_facet_enrichment` (this lane).
- serves_truth=false: a resolved graph is a candidate composition, not promotion. Nothing here executes primitives.

    PYTHONPATH=. python3 scripts/semantic_linker_resolve.py --self-test
    PYTHONPATH=. python3 scripts/semantic_linker_resolve.py --demo        # resolve the create-user plan on the real store
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Callable, Iterable, Optional

_HERE = Path(__file__).resolve()
_REPO = _HERE.parent.parent
for _p in (str(_REPO), str(_REPO / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)


# ================================================================================================================
# Plan IR — the compact capability graph the LLM emits (structured; a tiny text form is also parsed)
# ================================================================================================================
#: A plan is {"name": str, "steps": [Step], "policy": Policy}. A Step names a capability INTENT (natural words the
#: retriever matches) + its inputs (prior step vars / request fields). A Policy declares hard constraints (effects
#: the assembled system may NOT have, fields that must never be logged).
_STEP_RE = re.compile(r"^\s*(?P<var>\w+)\s*=\s*(?P<cap>[\w./-]+)\s*\((?P<args>.*)\)\s*$")


def parse_plan(plan: Any) -> dict[str, Any]:
    """Normalize a plan given as a dict OR the compact text form (``v = cap.name(a, b)`` per line, ``# policy:`` …).
    Returns {name, steps:[{var,capability,inputs}], policy}."""
    if isinstance(plan, dict):
        steps = [{"var": s.get("var") or f"s{i}", "capability": s["capability"],
                  "inputs": list(s.get("inputs") or s.get("in") or []),
                  "expected_out": s.get("out") or s.get("expected_out")}
                 for i, s in enumerate(plan.get("steps", []))]
        return {"name": plan.get("name", "plan"), "steps": steps, "policy": dict(plan.get("policy") or {})}
    steps, policy, name = [], {}, "plan"
    for raw in str(plan).splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            if line.startswith("# policy:"):
                try:
                    policy = json.loads(line.split("# policy:", 1)[1])
                except Exception:  # noqa: BLE001
                    pass
            elif line.startswith("# name:"):
                name = line.split("# name:", 1)[1].strip()
            continue
        m = _STEP_RE.match(line)
        if m:
            args = [a.strip() for a in m.group("args").split(",") if a.strip()]
            steps.append({"var": m.group("var"), "capability": m.group("cap"), "inputs": args})
    return {"name": name, "steps": steps, "policy": policy}


def _capability_words(capability: str) -> str:
    """Turn a capability id (``security.password-hash`` / ``cap://users/create``) into query words."""
    c = re.sub(r"^cap://", "", str(capability))
    c = re.sub(r"[./_:-]+", " ", c)
    return re.sub(r"\s+", " ", c).strip()


#: Query stopwords dropped before the lexical PRECISION check (they carry no capability signal).
_REL_STOPWORDS: frozenset[str] = frozenset({"the", "a", "an", "of", "to", "for", "and", "with", "into", "from",
                                            "by", "on", "in", "as", "is", "be", "or", "at", "that", "this"})


def _significant_tokens(text: str) -> frozenset[str]:
    return frozenset(w for w in re.sub(r"[^a-z0-9]+", " ", str(text).lower()).split()
                     if len(w) > 2 and w not in _REL_STOPWORDS)


def _lexically_relevant(query: str, card: dict[str, Any], *, min_overlap: int = 1) -> bool:
    """PRECISION gate on top of embedding recall: the capability query must share >=min_overlap significant tokens
    with the primitive's NAME/EDGES/blackbox. Static embeddings (model2vec) score even weak matches high, so cosine
    alone can't tell 'insert user' from an auth primitive — the lexical overlap can. This is the research bundle's
    hybrid (dense recall + lexical/type precision), made a hard relevance gate. Empty card -> not relevant."""
    if not card:
        return False
    q = _significant_tokens(query)
    doc = _significant_tokens(f"{card.get('title', '')} {card.get('input_edge', '')} "
                              f"{card.get('output_edge', '')} {card.get('blackbox', '')}")
    return len(q & doc) >= min_overlap


def _output_type_ok(card: dict[str, Any], expected_out: object) -> bool:
    """TYPED-PORT gate: when a plan step declares the OUTPUT TYPE it must produce, the primitive's ``output_edge``
    must share a significant token with it. This is the discriminator lexical/cosine relevance CANNOT provide at
    scale — it rejects the spurious match where 'password-hash' retrieves a TEST primitive (output TestProofReceipt)
    that merely mentions 'password hash' in prose. No declared output type -> cannot disprove (pass)."""
    if not expected_out:
        return True
    want = _significant_tokens(str(expected_out))
    got = _significant_tokens(str(card.get("output_edge") or ""))
    return bool(want & got) if want else True


# ================================================================================================================
# Blockers — HARD invalidation (never a softened ranking feature). Retrieval proposes; blockers dispose.
# ================================================================================================================
#: Effect keywords the policy can forbid. A primitive whose declared effects/blackbox mention a forbidden effect is
#: INVALID under that policy (removed from candidates), not merely down-ranked. Single-source lexicon.
_EFFECT_TOKENS: dict[str, tuple[str, ...]] = {
    "network": ("network", "http", "fetch", "request", "url", "api call", "socket", "outbound"),
    "filesystem": ("filesystem", "file write", "disk", "path write", "os.remove"),
    "subprocess": ("subprocess", "shell", "exec", "spawn", "os.system"),
    "secret": ("secret", "credential", "private key", "api key"),
}


def _card_effect_text(card: dict[str, Any]) -> str:
    """Effect text from DECLARED fields only — the manifest's ``effects`` + ``runtime_targets``. Deliberately NOT
    the blackbox prose: a primitive that DECODES an 'http request body' has no network effect, and inferring
    effects from description text (rather than a declared contract) is the vision's named failure mode (hidden/
    hallucinated effects). Declared effects authorize the block; prose never does."""
    parts: list[str] = []
    eff = card.get("effects")
    if isinstance(eff, list):
        for e in eff:
            parts.append(str(e.get("description") if isinstance(e, dict) else e))
    parts.append(" ".join(str(x) for x in (card.get("runtime_targets") or [])))
    return " ".join(parts).lower()


def policy_blockers(card: dict[str, Any], policy: dict[str, Any]) -> list[str]:
    """Which HARD policy blockers a card violates. ``policy['network']=='none'`` forbids any network-effecting
    primitive; a generic ``policy['forbid_effects']`` list forbids named effects. Returns violated blocker names."""
    violated = []
    text = _card_effect_text(card)
    forbid = set()
    if str(policy.get("network")) == "none":
        forbid.add("network")
    for e in (policy.get("forbid_effects") or []):
        forbid.add(str(e))
    for eff in forbid:
        toks = _EFFECT_TOKENS.get(eff, (eff,))
        if any(t in text for t in toks):
            violated.append(f"forbidden_effect:{eff}")
    return violated


def _norm_edge(edge: object) -> set[str]:
    return {w for w in re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", str(edge or "")).lower().replace("-", " ").split()
            if len(w) > 2}


def type_fits(prev_card: Optional[dict[str, Any]], card: dict[str, Any]) -> bool:
    """Loose TYPE-FIT blocker between consecutive resolved steps: the producer's output_edge shares a significant
    token with this step's input_edge. (A strict typed/refinement check is the assembler's job; this is the cheap
    gate that stops obviously-incompatible chaining — 'similar types' is not 'compatible types'.)"""
    if prev_card is None:
        return True
    out_w, in_w = _norm_edge(prev_card.get("output_edge")), _norm_edge(card.get("input_edge"))
    if not in_w:
        return True  # no declared input edge -> cannot disprove fit
    return bool(out_w & in_w)


# ================================================================================================================
# Resolve — retrieve candidates per capability, apply blockers, pick the survivor (or emit a residual)
# ================================================================================================================
#: Retrieval seam: (query, k) -> [{primitive_id, score, family}]. Default = the facet store; injectable for tests.
Retriever = Callable[[str, int], list[dict[str, Any]]]


def _default_retriever(cards: Optional[list[dict[str, Any]]] = None) -> Retriever:
    from scripts import primitive_facet_enrichment as _facet  # noqa: PLC0415  lazy: heavy numpy path

    def _r(query: str, k: int) -> list[dict[str, Any]]:
        return _facet.facet_search(query, cards, k=k)

    return _r


def _card_index(cards: Optional[list[dict[str, Any]]]) -> dict[str, dict[str, Any]]:
    return {str(c.get("primitive_id")): c for c in (cards or [])}


#: Default RELEVANCE floor — a COSINE floor (facet_search scores are 0-1). A candidate below this is NOT a real
#: match, so binding it would FAKE coverage (an auth primitive for an 'insert user' capability); below the floor the
#: capability becomes an honest RESIDUAL. Tuned to keep strong domain matches (auth ~0.77-0.85) and drop weak ones.
#: The offline keyword retriever returns integer overlap scores (>=1) which trivially exceed this, so self-tests +
#: the controlled sweep are unaffected; the gate only bites on the real cosine retriever. Relevance-gated search is
#: the research bundle's + the reuse fabric's explicit requirement.
DEFAULT_MIN_SCORE = 0.62


def resolve_plan(plan: Any, *, retriever: Optional[Retriever] = None, cards: Optional[list[dict[str, Any]]] = None,
                 k: int = 8, min_score: float = DEFAULT_MIN_SCORE) -> dict[str, Any]:
    """Resolve every capability in the plan to a VERIFIED primitive that survives the blockers, in step order.

    For each step: retrieve top-k candidates for the capability intent, drop any that fail the RELEVANCE floor
    (``min_score`` — a weak semantic match is not a real match, so it must not fake coverage) or a policy/effect
    blocker, and bind the top survivor. If none survive -> a RESIDUAL spec (the typed hole the LLM must fill), never
    a silent skip and never a low-relevance false bind. Returns {resolved, residual, lock, policy, route_ok}.
    """
    p = parse_plan(plan)
    policy = p["policy"]
    retriever = retriever or _default_retriever(cards)
    idx = _card_index(cards)
    resolved: list[dict[str, Any]] = []
    residual: list[dict[str, Any]] = []
    lock: dict[str, str] = {}

    for step in p["steps"]:
        cap = step["capability"]
        query = _capability_words(cap)
        cands = retriever(query, k) or []
        survivor = None
        blocked_by: list[dict[str, Any]] = []
        for cand in cands:
            card = idx.get(str(cand.get("primitive_id"))) or {}
            # RELEVANCE gate (hybrid): a candidate must clear the cosine floor (recall) AND share a capability token
            # with the query (precision). Static-embedding cosines cluster high, so the lexical overlap is the real
            # discriminator that prevents fake coverage (the retriever always returns *something*). A weak match ->
            # honest residual, not a bind. Candidates are score-descending; a below-floor score ends the scan.
            if float(cand.get("score", 0.0)) < min_score:
                blocked_by.append({"primitive_id": cand.get("primitive_id"), "below_min_score": cand.get("score")})
                break
            if not _lexically_relevant(query, card):
                blocked_by.append({"primitive_id": cand.get("primitive_id"), "below_relevance": True})
                continue
            if not _output_type_ok(card, step.get("expected_out")):
                blocked_by.append({"primitive_id": cand.get("primitive_id"), "output_type_mismatch": card.get("output_edge")})
                continue
            # HARD blockers at RESOLVE = policy/effect/security only. TYPE/PORT compatibility is NOT resolved here:
            # an incompatible port is bridged by a typed ADAPTER at ASSEMBLY (semantic_linker_assemble), never a
            # hard reject — so a valid-but-differently-shaped implementation is still reusable via an adapter.
            pol = policy_blockers(card, policy) if card else []
            if pol:
                blocked_by.append({"primitive_id": cand.get("primitive_id"), "policy": pol})
                continue
            survivor = {**cand, "capability": cap, "var": step["var"], "inputs": step["inputs"]}
            break
        if survivor:
            resolved.append({**survivor, "blocked_candidates": blocked_by})
            lock[cap] = survivor["primitive_id"]
        else:
            residual.append({"capability": cap, "var": step["var"], "inputs": step["inputs"],
                             "reason": ("all candidates blocked" if blocked_by else "no candidate retrieved"),
                             "blocked_candidates": blocked_by,
                             "interface": {"in": step["inputs"], "out": step["var"]}})
    route_ok = len(residual) == 0
    return {"plan": p["name"], "n_steps": len(p["steps"]), "resolved": resolved, "residual": residual,
            "lock": lock, "policy": policy, "route_ok": route_ok,
            "coverage": round(len(resolved) / len(p["steps"]), 4) if p["steps"] else 0.0,
            "candidate": True, "serves_truth": False}


# ================================================================================================================
# Token accounting — a STRUCTURAL projection (implementation bytes AVOIDED); the LIVE number is Codex's benchmark
# ================================================================================================================
#: Conservative from-scratch implementation size (output tokens) per capability class, used ONLY for the structural
#: projection. Rationale: the resolved primitive's body never enters model context — the LLM emits ~one plan line
#: instead of ~this many tokens. Deliberately conservative; the LIVE number comes from
#: semantic_linker_long_session_benchmark.py (Codex).
_IMPL_TOKENS_BY_HINT: dict[str, int] = {"validate": 60, "hash": 40, "insert": 70, "decode": 45, "view": 35,
                                        "respond": 25, "default": 55}
_PLAN_TOKENS_PER_STEP = 12  # a compact "v = cap.name(args)" line the LLM DOES emit


def _impl_tokens_for(cap: str) -> int:
    words = _capability_words(cap)
    for hint, n in _IMPL_TOKENS_BY_HINT.items():
        if hint in words:
            return n
    return _IMPL_TOKENS_BY_HINT["default"]


def token_projection(result: dict[str, Any]) -> dict[str, Any]:
    """STRUCTURAL projection of output tokens saved: for each RESOLVED capability the model emits a plan line
    (~{_PLAN_TOKENS_PER_STEP} tok) instead of the from-scratch implementation; RESIDUALS cost both a plan line AND
    their novel implementation (the linker never claims to save novelty). serves_truth=false; this is a projection,
    not a live measurement — see semantic_linker_long_session_benchmark.py for the executed number."""
    resolved, residual = result["resolved"], result["residual"]
    baseline = sum(_impl_tokens_for(r["capability"]) for r in resolved) \
        + sum(_impl_tokens_for(r["capability"]) for r in residual)
    linked = _PLAN_TOKENS_PER_STEP * (len(resolved) + len(residual)) \
        + sum(_impl_tokens_for(r["capability"]) for r in residual)  # residuals still author novel code
    saved = baseline - linked
    return {"method": "structural_projection", "baseline_output_tokens": baseline, "linked_output_tokens": linked,
            "tokens_saved": saved, "savings_fraction": round(saved / baseline, 4) if baseline else 0.0,
            "resolved": len(resolved), "residual": len(residual),
            "note": "PROJECTION: implementation bytes the resolved primitives keep OUT of context (novelty in "
                    "residuals is NOT claimed as saved). Live end-to-end number: semantic_linker_long_session_benchmark.py."}


def link(plan: Any, *, retriever: Optional[Retriever] = None, cards: Optional[list[dict[str, Any]]] = None,
         k: int = 8, min_score: float = DEFAULT_MIN_SCORE) -> dict[str, Any]:
    """Full resolve + token projection (the linker result an agent/MCP would consume)."""
    result = resolve_plan(plan, retriever=retriever, cards=cards, k=k, min_score=min_score)
    result["token_projection"] = token_projection(result)
    return result


# ================================================================================================================
# Self-test — the create-user plan, end-to-end, offline + deterministic
# ================================================================================================================
_CREATE_USER_PLAN = {
    "name": "create-user/v1",
    "steps": [
        {"var": "x", "capability": "http.decode-json", "in": ["req"], "out": "UserCreate"},
        {"var": "u", "capability": "users.validate-create", "in": ["x"], "out": "ValidatedUser"},
        {"var": "d", "capability": "security.password-hash", "in": ["u.password"], "out": "PasswordDigest"},
        {"var": "r", "capability": "users.insert", "in": ["u", "d"], "out": "User"},
        {"var": "v", "capability": "users.public-view", "in": ["r"], "out": "PublicUserView"},
    ],
    "policy": {"network": "none", "no_log": ["u.password"]},
}


def _fixture_cards() -> list[dict[str, Any]]:
    """A tiny primitive set covering the create-user capabilities (+ a network-effecting decoy that policy blocks)."""
    def card(pid, title, black, ie, oe, effects=None):
        return {"primitive_id": pid, "title": title, "blackbox": black, "input_edge": ie, "output_edge": oe,
                "effects": effects or [], "mutations": [], "trust": "candidate",
                "candidate": True, "serves_truth": False}
    return [
        card("prim:t:decode", "Decode JSON Request", "Decodes a JSON http request body into a typed UserCreate.",
             "HttpRequest", "UserCreate"),
        card("prim:t:validate", "Validate Create User", "Validates a UserCreate for unique email and required fields.",
             "UserCreate", "ValidatedUser"),
        card("prim:t:hash", "Password Hash", "Hashes a plaintext password into a salted password digest.",
             "ValidatedUser", "PasswordDigest"),
        card("prim:t:insert", "Insert User", "Inserts a validated user with a password digest and returns the user.",
             "PasswordDigest", "User"),
        card("prim:t:view", "Public User View", "Renders a user into a public view without credential fields.",
             "User", "PublicUserView"),
        # a decoy for 'insert' that phones home over the network -> policy network:none must BLOCK it
        card("prim:t:insert_net", "Insert User Via API", "Inserts a user by making an outbound http network request to a remote api.",
             "PasswordDigest", "User", effects=[{"description": "makes an outbound network http request to a remote service"}]),
    ]


def _keyword_retriever(cards: list[dict[str, Any]]) -> Retriever:
    """Offline retriever for the self-test: token-overlap over title+blackbox+edges (no embedder needed)."""
    def toks(s): return {w for w in re.sub(r"[^a-z0-9]+", " ", str(s).lower()).split() if len(w) > 2}
    docs = [(c, toks(f"{c.get('title')} {c.get('blackbox')} {c.get('input_edge')} {c.get('output_edge')}")) for c in cards]

    def _r(query: str, k: int) -> list[dict[str, Any]]:
        q = toks(query)
        scored = [{"primitive_id": c["primitive_id"], "score": len(q & d), "family": "action"}
                  for c, d in docs if q & d]
        scored.sort(key=lambda r: (-r["score"], r["primitive_id"]))
        return scored[:k]
    return _r


def _self_test() -> int:
    checks: list[tuple[str, bool, str]] = []
    cards = _fixture_cards()
    retr = _keyword_retriever(cards)

    # (1) TEXT PARSE == DICT PARSE: the compact text plan normalizes to the structured plan.
    text = ("# name: create-user/v1\n# policy: {\"network\": \"none\"}\n"
            "x = http.decode-json(req)\nu = users.validate-create(x)\nd = security.password-hash(u.password)\n"
            "r = users.insert(u, d)\nv = users.public-view(r)")
    pt, pd = parse_plan(text), parse_plan(_CREATE_USER_PLAN)
    checks.append(("compact text plan parses to the same steps as the dict form",
                   [s["capability"] for s in pt["steps"]] == [s["capability"] for s in pd["steps"]]
                   and pt["policy"].get("network") == "none", f"{len(pt['steps'])} steps"))

    # (2) FULL RESOLVE: every capability binds to its verified primitive; 0 residual; route_ok.
    res = link(_CREATE_USER_PLAN, retriever=retr, cards=cards)
    checks.append((f"resolve create-user -> {len(res['resolved'])}/5 bound, {len(res['residual'])} residual, route_ok={res['route_ok']}",
                   len(res["resolved"]) == 5 and res["route_ok"] and res["coverage"] == 1.0,
                   json.dumps(res["lock"])))

    # (3a) POSITIVE: in the full plan the clean insert is chosen (the network decoy never out-ranks it).
    insert_step = next(r for r in res["resolved"] if r["capability"] == "users.insert")
    # (3b) BLOCKER PROOF: when the network decoy is the ONLY candidate, network:none INVALIDATES it -> residual
    #      citing the forbidden effect (retrieval offered it; acceptance rejected it — never a silent bind).
    decoy_only: Retriever = lambda q, k: [{"primitive_id": "prim:t:insert_net", "score": 3.0, "family": "action"}]
    res_block = resolve_plan({"name": "b", "steps": [{"var": "r", "capability": "users.insert", "in": ["d"]}],
                              "policy": {"network": "none"}}, retriever=decoy_only, cards=cards)
    blocked_cite = any("forbidden_effect:network" in b["policy"]
                       for r in res_block["residual"] for b in r["blocked_candidates"])
    checks.append(("policy blocker: clean insert chosen in-plan; decoy-alone INVALIDATED -> residual citing effect",
                   insert_step["primitive_id"] == "prim:t:insert" and not res_block["resolved"] and blocked_cite,
                   f"chosen={insert_step['primitive_id']} blocked_cite={blocked_cite}"))

    # (4) RESIDUAL: a capability with NO matching primitive becomes an explicit residual (typed hole), not a fake
    #     bind. Uses a zero-overlap capability so the miss is genuine (no shared token can accidentally match).
    plan_gap = {**_CREATE_USER_PLAN, "steps": _CREATE_USER_PLAN["steps"] + [
        {"var": "z", "capability": "cryptography.elliptic-curve-sign", "in": ["v"]}]}
    res_gap = resolve_plan(plan_gap, retriever=retr, cards=cards)
    checks.append(("registry miss -> explicit residual (not a false bind)",
                   any(r["capability"] == "cryptography.elliptic-curve-sign" for r in res_gap["residual"])
                   and not res_gap["route_ok"], f"{len(res_gap['residual'])} residual"))

    # (4b) RELEVANCE GATE: a weak-score candidate (below the cosine floor) is NOT bound -> residual, preventing the
    #      "retriever always returns something" fake-coverage failure that inflates savings.
    weak: Retriever = lambda q, k: [{"primitive_id": "prim:t:hash", "score": 0.10, "family": "action"}]
    res_weak = resolve_plan({"name": "w", "steps": [{"var": "d", "capability": "security.password-hash", "in": ["x"]}],
                             "policy": {}}, retriever=weak, cards=cards, min_score=0.62)
    checks.append(("relevance gate: a below-floor match is NOT bound (honest residual, no fake coverage)",
                   not res_weak["resolved"] and any("below_min_score" in b
                       for r in res_weak["residual"] for b in r["blocked_candidates"]),
                   f"resolved={len(res_weak['resolved'])}"))

    # (4c) LEXICAL PRECISION gate: a HIGH-score candidate that shares NO capability token with the query is still
    #      rejected (the model2vec-cosine-clusters-high failure the family bench exposed) -> honest residual.
    irrel: Retriever = lambda q, k: [{"primitive_id": "prim:t:hash", "score": 0.99, "family": "action"}]
    res_irrel = resolve_plan({"name": "i", "steps": [{"var": "z", "capability": "quantum.teleport-widget", "in": ["x"]}],
                              "policy": {}}, retriever=irrel, cards=cards, min_score=0.62)
    checks.append(("lexical precision gate: high-score but zero-token-overlap match rejected (no fake bind)",
                   not res_irrel["resolved"] and any(b.get("below_relevance")
                       for r in res_irrel["residual"] for b in r["blocked_candidates"]),
                   f"resolved={len(res_irrel['resolved'])}"))

    # (4d) TYPED-PORT gate: a candidate that shares the query's tokens but produces the WRONG output type is
    #      rejected — the real-store failure where 'password-hash' bound a TEST primitive (output TestProofReceipt)
    #      that merely mentions 'password hash'. A hashing card outputs a digest; the test card does not.
    testish = [{"primitive_id": "p:testhash", "title": "returns false for bots without a password hash",
                "blackbox": "a test that checks password hash presence", "input_edge": "TestFixture",
                "output_edge": "TestProofReceipt", "effects": [], "candidate": True, "serves_truth": False}]
    typed: Retriever = lambda q, k: [{"primitive_id": "p:testhash", "score": 0.94, "family": "action"}]
    res_typed = resolve_plan({"name": "t", "steps": [{"var": "d", "capability": "security.password-hash",
                              "in": ["x"], "out": "PasswordDigest"}], "policy": {}},
                             retriever=typed, cards=testish, min_score=0.62)
    checks.append(("typed-port gate: token-matching but wrong-output-type match rejected (kills spurious coverage)",
                   not res_typed["resolved"] and any(b.get("output_type_mismatch")
                       for r in res_typed["residual"] for b in r["blocked_candidates"]),
                   f"resolved={len(res_typed['resolved'])}"))

    # (5) TOKEN PROJECTION: resolved-heavy plan projects positive savings; label says PROJECTION not measurement.
    tp = res["token_projection"]
    checks.append((f"token projection: {tp['tokens_saved']} saved ({tp['savings_fraction']:.0%}), method={tp['method']}",
                   tp["tokens_saved"] > 0 and tp["method"] == "structural_projection", json.dumps(tp)))

    # (6) DETERMINISM: same plan+cards -> byte-identical result.
    r1 = json.dumps(resolve_plan(_CREATE_USER_PLAN, retriever=retr, cards=cards), sort_keys=True)
    r2 = json.dumps(resolve_plan(_CREATE_USER_PLAN, retriever=retr, cards=cards), sort_keys=True)
    checks.append(("resolve is deterministic (byte-identical twice)", r1 == r2, "hash match"))

    ok = all(c[1] for c in checks)
    print(f"{'PASS' if ok else 'FAIL'} - semantic_linker_resolve: plan-IR -> retrieve -> BLOCK (policy/effect; "
          f"ports adapted at assembly) -> lock + residual + token projection (retrieval probabilistic, acceptance deterministic)")
    for name, passed, detail in checks:
        print(f"  [{'ok' if passed else 'XX'}] {name}" + (f"  ({detail})" if not passed else ""))
    return 0 if ok else 1


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Semantic linker RESOLVE: capability plan -> verified primitives + lock + residual.")
    ap.add_argument("--self-test", action="store_true", help="offline end-to-end gate (create-user plan)")
    ap.add_argument("--demo", action="store_true", help="resolve the create-user plan against the REAL facet store")
    ap.add_argument("--plan", default=None, help="path to a JSON plan file to resolve against the real store")
    ap.add_argument("--k", type=int, default=8, help="retrieval depth per capability")
    args = ap.parse_args(argv)

    if args.self_test:
        return _self_test()

    if args.demo or args.plan:
        from scripts import primitive_facet_enrichment as _facet  # noqa: PLC0415
        cards = _facet.load_cards(sample=0)
        plan = json.loads(Path(args.plan).read_text()) if args.plan else _CREATE_USER_PLAN
        res = link(plan, cards=cards, k=args.k)
        # trim candidate lists for readable output
        for r in res["resolved"]:
            r.pop("blocked_candidates", None)
        print(json.dumps(res, indent=2))
        return 0

    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
