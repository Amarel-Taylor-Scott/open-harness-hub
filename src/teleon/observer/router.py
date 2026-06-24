"""observer.router — the Spotter ROUTER over the intervention TAXONOMY (the memo's central architecture, made real).

"This already exists" is ONE intervention type among several. The key move is treating them as a TAXONOMY where each
type has a different GROUNDING (what stops it hallucinating) and a different FAILURE MODE (what "wrong" means):

  reinvention        grounded in the FEDERATION (search_all)         wrong suggestion -> wasted detour     can ASK
  footgun            grounded in deterministic PATTERN rules         false alarm (protective, tolerated)   can BLOCK
  adversarial        grounded in QUESTION TEMPLATES keyed to intent  not 'wrong' — irrelevant/annoying     NOTICE only
  reinvention_cluster session-level signal SEQUENCE                  premature on partial signal           NOTICE only
  oversized/duplicate observed token WASTE in the stream             mistimed nag                          NOTICE only

The engine is ONE funnel generalized into a router: Tier-0 classify the moment -> wake only the PLAUSIBLE modules ->
each grounds + scores -> Decide applies a per-type floor AND a GLOBAL interruption budget (the make-or-break: six
modules each firing "occasionally" still = a tool that won't shut up) under a graduated MODE
(silent_record -> review_only -> advisory -> active -> enforcing). Live intervention and post-session review are the
SAME engine: review == route_session(mode="review_only") — exhaustive report, zero live interruptions.

Patterns are single-sourced in architecture/behavioral_heuristics.json (no-magic-values); modules read them. Footgun
matches are REDACTED, never echoed (no-store-secrets). Every finding is a governed CANDIDATE a human triages
(serves_truth=false; discovery != trust).
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from ..knowledge import dependency_graph as _depgraph
from ..registry.reinvention_guard import check as _guard_check, detect_intent as _detect_intent

_REPO = Path(__file__).resolve().parents[3]
_HEURISTICS_PATH = _REPO / "architecture" / "behavioral_heuristics.json"

# --- graduated modes + action lattice (the restraint gradient, §10/§12) ----------------------------------------
ACTIONS = ("silent", "notice", "ask", "block")  # ordered weakest -> strongest
MODES = ("silent_record", "review_only", "advisory", "active", "enforcing")
_MODE_CAP = {  # the strongest live action each mode permits (review modes never interrupt -> silent)
    "silent_record": "silent", "review_only": "silent",
    "advisory": "notice", "active": "ask", "enforcing": "block",
}
_LIVE_BUDGET = 3  # GLOBAL cap on non-footgun interruptions surfaced per session in live modes (the attention budget)

# --- waste heuristics (named; no magic values) -----------------------------------------------------------------
_CHARS_PER_TOKEN = 4
_OVERSIZED_TOKENS = 8_000
_DUP_PREFIX_CHARS = 200
_DUP_MIN_TOKENS = 200
_CONF_REINVENTION = 0.8
_CONF_OVERSIZED = 0.55
_CONF_DUPLICATE = 0.7
_CONF_STACK = 0.82  # stack-level reinvention is graph-grounded (transitive coverage) -> high
_PER_TYPE_FLOOR = 0.5  # a finding below its module's confidence floor is dropped before the budget even runs


def _weaker(a: str, b: str) -> str:
    return a if ACTIONS.index(a) <= ACTIONS.index(b) else b


def _approx_tokens(text: str) -> int:
    return len(text) // _CHARS_PER_TOKEN


def _load_heuristics() -> list[dict]:
    return json.loads(_HEURISTICS_PATH.read_text())["heuristics"]


def _iv(type_: str, confidence: float, message: str, evidence: str, suggestion: str, max_action: str,
        source_ref: dict | None = None, dedup_id: str | None = None) -> dict:
    """A governed candidate intervention. `outcome` (accepted|reused|dismissed|ignored) is the accept/reject SIGNAL
    — the moat — filled later by the surface UI; None until a human acts on it."""
    return {
        "type": type_, "confidence": confidence, "message": message, "evidence": evidence,
        "suggestion": suggestion, "max_action": max_action, "source_ref": source_ref or {},
        "dedup_id": dedup_id, "outcome": None, "serves_truth": False, "candidate": True,
    }


# --- the intervention modules (uniform interface: plausible() Tier-0 gate, ground() Tier-1/2) -------------------
class InterventionModule:
    type = "base"

    def plausible(self, text: str, state: dict) -> bool:
        raise NotImplementedError

    def ground(self, text: str, state: dict) -> list[dict]:
        raise NotImplementedError


class ReinventionModule(InterventionModule):
    """Single-message reinvention, GROUNDED in the federation (the reference module — wraps reinvention_guard)."""
    type = "reinvention"

    def plausible(self, text: str, state: dict) -> bool:
        t0 = _detect_intent(text)
        return t0["build_intent"] and bool(t0["candidate_domains"])

    def ground(self, text: str, state: dict) -> list[dict]:
        g = _guard_check(text)
        if not g.get("fire"):
            return []
        return [_iv("reinvention", _CONF_REINVENTION, g["notice"], text[:120].strip(),
                    "reuse the existing component instead of rebuilding (saves the rebuild + its debug trajectory)",
                    max_action="ask", source_ref={"existing": g["existing"], "grounded_in": g.get("grounded_in")})]


class FootgunModule(InterventionModule):
    """Deterministic secret/destructive pattern scan — high-trust, may BLOCK. Evidence is REDACTED (no-store-secrets)."""
    type = "footgun"

    def __init__(self, heuristics: list[dict]):
        self._rules = [(h, re.compile(h["match"]["regex"])) for h in heuristics if h["kind"] == "footgun"]

    def plausible(self, text: str, state: dict) -> bool:
        return True  # a cheap regex scan is always plausible

    def ground(self, text: str, state: dict) -> list[dict]:
        out = []
        for h, rx in self._rules:
            if rx.search(text):
                out.append(_iv("footgun", h["confidence"], h["message"], "<redacted match>",
                               h.get("suggestion", "remove it / use a secret manager; double-check destructive targets"),
                               max_action=h["max_action"], source_ref={"rule": h["id"]}))
        return out


class AdversarialModule(InterventionModule):
    """Challenge an assumption BEFORE wasted work — keyed to question templates. Never blocks; failure = irrelevance."""
    type = "adversarial"

    def __init__(self, heuristics: list[dict]):
        self._templates = [h for h in heuristics if h["kind"] == "adversarial"]

    def plausible(self, text: str, state: dict) -> bool:
        low = text.lower()
        return any(any(k in low for k in h["match"]["keywords"]) for h in self._templates)

    def ground(self, text: str, state: dict) -> list[dict]:
        low = text.lower()
        out = []
        for h in self._templates:
            if any(k in low for k in h["match"]["keywords"]):
                out.append(_iv("adversarial", h["confidence"], h["message"], text[:120].strip(),
                               "answer the question before building; the cheaper rung may already solve it",
                               max_action=h["max_action"], source_ref={"rule": h["id"]}, dedup_id=h["id"]))
        return out


class ReinventionClusterModule(InterventionModule):
    """Session-level: a SEQUENCE of build-signals that together predict rebuilding common infrastructure (§6)."""
    type = "reinvention_cluster"

    def __init__(self, heuristics: list[dict]):
        self._clusters = [h for h in heuristics if h["kind"] == "reinvention_cluster"]

    def plausible(self, text: str, state: dict) -> bool:
        return True  # cheap substring check against accumulated session text

    def ground(self, text: str, state: dict) -> list[dict]:
        seen = state.get("session_text", "").lower()
        out = []
        for h in self._clusters:
            if all(sig in seen for sig in h["match"]["all_of"]):
                out.append(_iv("reinvention_cluster", h["confidence"], h["message"],
                               "signals: " + ", ".join(h["match"]["all_of"]),
                               "adopt a library/framework that covers the whole cluster",
                               max_action=h["max_action"], source_ref={"rule": h["id"]}, dedup_id=h["id"]))
        return out


class StackReinventionModule(InterventionModule):
    """Stack-level reinvention, GROUNDED in the dependency graph (#101): 'this whole dependency stack already provides
    it' via transitive coverage — deeper than the single-keyword federation check. Deterministic (no embedder)."""
    type = "stack_reinvention"

    # generic capability words that appear in ordinary prose ('an api', 'the schema') -> too noisy to fire on alone
    # (found by DOGFOODING the reviewer on a real session: bare 'schema'/'api' over-fired). Distinctive multi-word or
    # domain caps (vector_search, exponential_backoff, oauth, ocr, pdf_text_extraction) stay.
    _AMBIGUOUS = frozenset({"api", "schema", "validation", "routing", "cache", "queue", "search", "encryption",
                            "hashing", "image_processing"})

    def __init__(self):
        self._graph = _depgraph.build_graph()
        # capability vocabulary from what packages PROVIDE; match as word-bounded phrases (underscore or space),
        # excluding the ambiguous generic words.
        self._caps = {c: re.compile(rf"\b{re.escape(c.replace('_', ' '))}\b")
                      for c in self._graph["provides"] if c not in self._AMBIGUOUS}

    def _caps_in(self, text: str) -> list[str]:
        low = text.lower().replace("_", " ")
        return sorted(c for c, rx in self._caps.items() if rx.search(low))

    def plausible(self, text: str, state: dict) -> bool:
        return _detect_intent(text)["build_intent"] and bool(self._caps_in(text))

    def ground(self, text: str, state: dict) -> list[dict]:
        wanted = self._caps_in(text)
        if not wanted:
            return []
        se = _depgraph.stack_exists(wanted, self._graph)
        if not se["stack_exists"]:
            return []
        pkgs = [c["package"] for c in se["covering_packages"]]
        return [_iv("stack_reinvention", _CONF_STACK,
                    "an existing dependency stack already provides this — don't rebuild it",
                    ", ".join(wanted), f"reuse {', '.join(pkgs[:3])} (covers these via its dependency stack)",
                    max_action="notice", source_ref={"covering": se["covering_packages"]},
                    dedup_id="stack:" + ":".join(wanted))]


class OversizedContextModule(InterventionModule):
    type = "oversized_context"

    def plausible(self, text: str, state: dict) -> bool:
        return _approx_tokens(text) > _OVERSIZED_TOKENS

    def ground(self, text: str, state: dict) -> list[dict]:
        return [_iv("oversized_context", _CONF_OVERSIZED, "an oversized context turn (re-billed every turn)",
                    f"~{_approx_tokens(text):,} tokens in one message",
                    "summarize or retrieve the relevant slice before sending", max_action="notice")]


class DuplicateContextModule(InterventionModule):
    type = "duplicate_context"

    def plausible(self, text: str, state: dict) -> bool:
        return _approx_tokens(text) >= _DUP_MIN_TOKENS

    def ground(self, text: str, state: dict) -> list[dict]:
        key = text[:_DUP_PREFIX_CHARS]
        seen = state.setdefault("seen_prefixes", {})
        if key in seen:
            return [_iv("duplicate_context", _CONF_DUPLICATE, "a large blob re-sent (re-upload waste)",
                        f"repeats the blob first sent in message #{seen[key]}",
                        "cache/reference the prior content instead of re-sending it", max_action="notice")]
        seen[key] = state.get("_i", 0)
        return []


def default_modules() -> list[InterventionModule]:
    h = _load_heuristics()
    return [ReinventionModule(), StackReinventionModule(), FootgunModule(h), AdversarialModule(h),
            ReinventionClusterModule(h), OversizedContextModule(), DuplicateContextModule()]


def _message_text(m: dict) -> str:
    c = m.get("content", m.get("text", ""))
    if isinstance(c, list):
        return "\n".join(str(b.get("text", b)) if isinstance(b, dict) else str(b) for b in c)
    return str(c or "")


def _apply_budget(findings: list[dict], mode: str) -> list[dict]:
    """The GLOBAL interruption budget. Footguns (protective) always surface; other types compete for _LIVE_BUDGET
    slots by confidence. Review/silent modes never interrupt (the report carries everything instead)."""
    if _MODE_CAP[mode] == "silent":
        return []
    live = [f for f in findings if f["action"] != "silent"]
    protective = [f for f in live if f["type"] == "footgun"]
    others = sorted((f for f in live if f["type"] != "footgun"), key=lambda f: f["confidence"], reverse=True)
    return protective + others[:_LIVE_BUDGET]


def route_session(events: list[dict], mode: str = "review_only", modules: list[InterventionModule] | None = None) -> dict:
    """Run the router over a session. mode picks the restraint level; review_only = the exhaustive post-session report
    with zero live interruptions. Returns {mode, report (all findings), surfaced (what would interrupt live), summary}."""
    if mode not in MODES:
        raise ValueError(f"unknown mode {mode!r}; one of {MODES}")
    mods = modules if modules is not None else default_modules()
    state: dict = {"seen_prefixes": {}, "session_text": "", "fired": set()}
    findings: list[dict] = []

    for i, ev in enumerate(events):
        text = _message_text(ev)
        if not text.strip():
            continue
        state["_i"] = i
        state["session_text"] += "\n" + text
        for mod in mods:
            if not mod.plausible(text, state):
                continue
            for iv in mod.ground(text, state):
                if iv["confidence"] < _PER_TYPE_FLOOR:
                    continue
                if iv["dedup_id"] is not None:
                    if iv["dedup_id"] in state["fired"]:
                        continue
                    state["fired"].add(iv["dedup_id"])
                iv["message_index"] = i
                iv["action"] = _weaker(iv["max_action"], _MODE_CAP[mode])
                findings.append(iv)

    findings.sort(key=lambda f: f["confidence"], reverse=True)
    surfaced = _apply_budget(findings, mode)
    by_type: dict[str, int] = {}
    for f in findings:
        by_type[f["type"]] = by_type.get(f["type"], 0) + 1
    return {
        "mode": mode,
        "report": findings,
        "surfaced": surfaced,
        "summary": {"messages": len(events), "findings": len(findings), "by_type": by_type,
                    "would_interrupt": len(surfaced)},
        "serves_truth": False,
        "governed": "candidate findings (discovery != trust); a human triages; the accept/reject outcome tunes thresholds",
    }
