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

Patterns are single-sourced in _repos/shared-backend-components/architecture/behavioral_heuristics.json (no-magic-values); modules read them. Footgun
matches are REDACTED, never echoed (no-store-secrets). Every finding is a governed CANDIDATE a human triages
(serves_truth=false; discovery != trust).
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import json
import re
from pathlib import Path

from ..knowledge import dependency_graph as _depgraph
from ..registry.reinvention_guard import py_function_src_teleon_registry_reinvention_guard__check as _guard_check, py_function_src_teleon_registry_reinvention_guard__detect_intent as _detect_intent
from .settings import ROUTER_SETTINGS, SAVINGS_SETTINGS

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[3])
_HEURISTICS_PATH = _resource("architecture") / "behavioral_heuristics.json"

# --- graduated modes + action lattice (the restraint gradient, §10/§12) ----------------------------------------
ACTIONS = ("silent", "notice", "ask", "block")  # ordered weakest -> strongest
MODES = ("silent_record", "review_only", "advisory", "active", "enforcing")
_MODE_CAP = {  # the strongest live action each mode permits (review modes never interrupt -> silent)
    "silent_record": "silent", "review_only": "silent",
    "advisory": "notice", "active": "ask", "enforcing": "block",
}
_LIVE_BUDGET = ROUTER_SETTINGS.live_budget  # GLOBAL cap on non-footgun interruptions surfaced per session.

# --- waste heuristics (named; no magic values) -----------------------------------------------------------------
_CHARS_PER_TOKEN = ROUTER_SETTINGS.chars_per_token
_OVERSIZED_TOKENS = ROUTER_SETTINGS.oversized_tokens
_DUP_PREFIX_CHARS = ROUTER_SETTINGS.duplicate_prefix_chars
_DUP_MIN_TOKENS = ROUTER_SETTINGS.duplicate_min_tokens
_CONF_REINVENTION = ROUTER_SETTINGS.reinvention_confidence
_CONF_OVERSIZED = ROUTER_SETTINGS.oversized_confidence
_CONF_DUPLICATE = ROUTER_SETTINGS.duplicate_confidence
_CONF_STACK = ROUTER_SETTINGS.stack_confidence
_CONF_ML_COMPETITION_ROUTE = ROUTER_SETTINGS.ml_competition_confidence
_CONF_MANUAL_CONTEXT_WASTE = ROUTER_SETTINGS.manual_context_waste_confidence
_SHORTCUT_REPEAT = ROUTER_SETTINGS.shortcut_repeat
_PER_TYPE_FLOOR = ROUTER_SETTINGS.per_type_floor

_ML_COMPETITION_ROUTES = (
    {
        "id": "tabular_competition_baseline",
        "all": ("competition",),
        "any": ("tabular", "train.csv", "test.csv", "auc", "churn", "submission csv"),
        "template": "template.tabular_competition_baseline",
        "existing": {
            "ml_competition_primitives": [
                {"registry": "teleon_primitive", "name": "dataset.inspect_schema"},
                {"registry": "teleon_primitive", "name": "table.fill_missing_values"},
                {"registry": "teleon_primitive", "name": "table.encode_categoricals"},
                {"registry": "teleon_primitive", "name": "table.train_valid_split_seeded"},
                {"registry": "teleon_primitive", "name": "metric.compute_auc"},
                {"registry": "teleon_primitive", "name": "model.train_lightgbm"},
                {"registry": "teleon_primitive", "name": "submission.write_csv"},
            ]
        },
    },
    {
        "id": "image_classification_competition_baseline",
        "all": ("competition",),
        "any": ("image-classification", "image classification", "confusion matrix", "image folders", "train_cnn"),
        "template": "template.image_classification_competition_baseline",
        "existing": {
            "ml_competition_primitives": [
                {"registry": "teleon_primitive", "name": "image.read_dataset_manifest"},
                {"registry": "teleon_primitive", "name": "image.validate_label_map"},
                {"registry": "teleon_primitive", "name": "image.resize_normalize"},
                {"registry": "teleon_primitive", "name": "vision.augment_train_only"},
                {"registry": "teleon_primitive", "name": "dataset.train_valid_split_seeded"},
                {"registry": "teleon_primitive", "name": "model.train_transfer_classifier"},
                {"registry": "teleon_primitive", "name": "metric.compute_accuracy_confusion_matrix"},
                {"registry": "teleon_primitive", "name": "submission.write_image_predictions"},
            ]
        },
    },
    {
        "id": "text_classification_competition_baseline",
        "all": ("competition",),
        "any": ("text-classification", "text classification", "macro f1", "label descriptions", "vectorize_text"),
        "template": "template.text_classification_competition_baseline",
        "existing": {
            "ml_competition_primitives": [
                {"registry": "teleon_primitive", "name": "text.normalize_for_classification"},
                {"registry": "teleon_primitive", "name": "label.validate_label_set"},
                {"registry": "teleon_primitive", "name": "dataset.train_valid_split_seeded"},
                {"registry": "teleon_primitive", "name": "text.vectorize_tfidf"},
                {"registry": "teleon_primitive", "name": "model.train_linear_text_classifier"},
                {"registry": "teleon_primitive", "name": "metric.compute_macro_f1"},
                {"registry": "teleon_primitive", "name": "submission.write_classification_csv"},
            ]
        },
    },
)

_MANUAL_CONTEXT_WASTE_PATTERNS = (
    {
        "id": "long_data_dictionary_dump",
        "needles": ("data dictionary", "full", "context"),
        "source_ref": {"existing": {"context_primitives": [
            {"registry": "teleon_primitive", "name": "schema.summary"},
            {"registry": "teleon_primitive", "name": "dataset.column_role_inference"},
        ]}},
    },
    {
        "id": "directory_listing_dump",
        "needles": ("directory listing", "pasting"),
        "source_ref": {"existing": {"context_primitives": [
            {"registry": "teleon_primitive", "name": "artifact.image_manifest"},
            {"registry": "teleon_primitive", "name": "image.label_map_summary"},
        ]}},
    },
    {
        "id": "example_rows_dump",
        "needles": ("example rows", "context"),
        "source_ref": {"existing": {"context_primitives": [
            {"registry": "teleon_primitive", "name": "dataset.sample_summary"},
            {"registry": "teleon_primitive", "name": "label.schema_summary"},
        ]}},
    },
)


def _weaker(a: str, b: str) -> str:
    return a if ACTIONS.index(a) <= ACTIONS.index(b) else b


def _approx_tokens(text: str) -> int:
    return len(text) // _CHARS_PER_TOKEN


def _token_savings(tokens_avoided: int, *, basis: str, model_calls_avoided: int = 0) -> dict:
    """Transparent estimated savings payload. This is a heuristic/reporting estimate, not a billing receipt."""
    return {
        "tokens_avoided_estimate": max(0, int(tokens_avoided)),
        "model_calls_avoided_estimate": max(0, int(model_calls_avoided)),
        "basis": basis,
        "serves_truth": False,
    }


def _savings_summary(findings: list[dict]) -> dict:
    tokens = 0
    calls = 0
    by_basis: dict[str, int] = {}
    for finding in findings:
        savings = finding.get("savings") if isinstance(finding.get("savings"), dict) else {}
        tokens += int(savings.get("tokens_avoided_estimate") or 0)
        calls += int(savings.get("model_calls_avoided_estimate") or 0)
        basis = str(savings.get("basis") or "").strip()
        if basis:
            by_basis[basis] = by_basis.get(basis, 0) + 1
    return {
        "tokens_avoided_estimate": tokens,
        "model_calls_avoided_estimate": calls,
        "basis_counts": dict(sorted(by_basis.items())),
        "estimate_method": "observer finding estimates; not a billing receipt",
        "serves_truth": False,
    }


def _load_heuristics() -> list[dict]:
    return json.loads(_HEURISTICS_PATH.read_text())["heuristics"]


def _iv(type_: str, confidence: float, message: str, evidence: str, suggestion: str, max_action: str,
        source_ref: dict | None = None, dedup_id: str | None = None, savings: dict | None = None) -> dict:
    """A governed candidate intervention. `outcome` (accepted|reused|dismissed|ignored) is the accept/reject SIGNAL
    — the moat — filled later by the surface UI; None until a human acts on it."""
    return {
        "type": type_, "confidence": confidence, "message": message, "evidence": evidence,
        "suggestion": suggestion, "max_action": max_action, "source_ref": source_ref or {},
        "dedup_id": dedup_id, "outcome": None, "serves_truth": False, "candidate": True,
        "savings": savings or {},
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
                    "reuse or compare the existing registry component first; this avoids the rebuild and its debug trajectory",
                    max_action="ask", source_ref={"existing": g["existing"], "grounded_in": g.get("grounded_in")},
                    savings=_token_savings(
                        SAVINGS_SETTINGS.reuse_route_tokens_avoided,
                        model_calls_avoided=SAVINGS_SETTINGS.reuse_route_model_calls_avoided,
                        basis="heuristic_registry_reuse_route",
                    ))]


class MLCompetitionReinventionModule(InterventionModule):
    """Narrow AIDevObserver route finder for common Kaggle-style competition baselines.

    This is intentionally separate from the broad reinvention guard. It only wakes on competition/baseline language and
    emits candidate Teleon primitive/template routes, not truth. It exists so data-science examples do not depend on
    generic words like "model" or "classification" over-broadening the solved-domain guard.
    """
    type = "reinvention"

    def plausible(self, text: str, state: dict) -> bool:
        low = text.lower()
        return ("competition" in low or "kaggle" in low) and any(
            trigger in low for trigger in ("baseline", "submission", "train", "classifier", "classification")
        )

    def ground(self, text: str, state: dict) -> list[dict]:
        low = text.lower()
        out = []
        for route in _ML_COMPETITION_ROUTES:
            if not all(token in low for token in route["all"]):
                continue
            if not any(token in low for token in route["any"]):
                continue
            source_ref = {
                **route["existing"],
                "template": route["template"],
                "grounded_in": "AIDevObserver synthetic public-project primitive route map",
            }
            out.append(_iv(
                "reinvention",
                _CONF_ML_COMPETITION_ROUTE,
                "This maps to a known ML competition baseline route in the primitive database.",
                text[:120].strip(),
                "reuse the seeded competition-baseline route instead of rebuilding notebook helpers",
                max_action="ask",
                source_ref=source_ref,
                dedup_id=f"ml_competition:{route['id']}",
                savings=_token_savings(
                    SAVINGS_SETTINGS.ml_baseline_tokens_avoided,
                    model_calls_avoided=SAVINGS_SETTINGS.reuse_route_model_calls_avoided,
                    basis="heuristic_known_ml_baseline_route",
                ),
            ))
        return out


class ManualContextWasteModule(InterventionModule):
    """Detect avoidable context dumps where a compact schema/manifest/sample summary primitive should be used."""
    type = "wasted_context"

    def plausible(self, text: str, state: dict) -> bool:
        low = text.lower()
        return any(word in low for word in ("pasting", "copying", "directory listing", "data dictionary", "example rows"))

    def ground(self, text: str, state: dict) -> list[dict]:
        low = text.lower()
        out = []
        for pattern in _MANUAL_CONTEXT_WASTE_PATTERNS:
            if all(needle in low for needle in pattern["needles"]):
                out.append(_iv(
                    "wasted_context",
                    _CONF_MANUAL_CONTEXT_WASTE,
                    "This context dump can be replaced by a compact summary primitive.",
                    text[:120].strip(),
                    "summarize the schema/manifest/sample first, then plan over the compact record",
                    max_action="notice",
                    source_ref={
                        **pattern["source_ref"],
                        "grounded_in": "AIDevObserver context-minimization primitive map",
                    },
                    dedup_id=f"manual_context:{pattern['id']}",
                    savings=_token_savings(
                        SAVINGS_SETTINGS.manual_context_tokens_avoided,
                        model_calls_avoided=1,
                        basis="heuristic_context_summary_primitive",
                    ),
                ))
        return out


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
        return True  # cheap substring checks against the current turn + the bounded signal set

    def ground(self, text: str, state: dict) -> list[dict]:
        # Keep only the finite cluster signals seen so far. The previous implementation rebuilt and lowercased
        # the entire growing transcript on every event, making long-session review superlinear and causing the
        # product's own 40 MB dogfood session to stall for minutes.
        seen = state.setdefault("reinvention_cluster_signals", set())
        low = text.lower()
        for h in self._clusters:
            seen.update(sig for sig in h["match"]["all_of"] if sig in low)
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
        self._graph = _depgraph.py_function_src_teleon_knowledge_dependency_graph__build_graph()
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
        se = _depgraph.py_function_src_teleon_knowledge_dependency_graph__stack_exists(wanted, self._graph)
        if not se["stack_exists"]:
            return []
        pkgs = [c["package"] for c in se["covering_packages"]]
        return [_iv("stack_reinvention", _CONF_STACK,
                    "an existing dependency stack already provides this — don't rebuild it",
                    ", ".join(wanted), f"reuse {', '.join(pkgs[:3])} (covers these via its dependency stack)",
                    max_action="notice", source_ref={"covering": se["covering_packages"]},
                    dedup_id="stack:" + ":".join(wanted),
                    savings=_token_savings(
                        SAVINGS_SETTINGS.dependency_stack_tokens_avoided,
                        model_calls_avoided=1,
                        basis="heuristic_existing_dependency_stack",
                    ))]


class OversizedContextModule(InterventionModule):
    type = "oversized_context"

    def plausible(self, text: str, state: dict) -> bool:
        return _approx_tokens(text) > _OVERSIZED_TOKENS

    def ground(self, text: str, state: dict) -> list[dict]:
        observed = _approx_tokens(text)
        return [_iv("oversized_context", _CONF_OVERSIZED, "an oversized context turn (re-billed every turn)",
                    f"~{_approx_tokens(text):,} tokens in one message",
                    "summarize or retrieve the relevant slice before sending", max_action="notice",
                    savings=_token_savings(
                        observed - SAVINGS_SETTINGS.compact_context_target_tokens,
                        basis="observed_context_size_minus_compact_target",
                    ))]


class DuplicateContextModule(InterventionModule):
    type = "duplicate_context"

    def plausible(self, text: str, state: dict) -> bool:
        return _approx_tokens(text) >= _DUP_MIN_TOKENS

    def ground(self, text: str, state: dict) -> list[dict]:
        key = text[:_DUP_PREFIX_CHARS]
        seen = state.setdefault("seen_prefixes", {})
        if key in seen:
            observed = _approx_tokens(text)
            return [_iv("duplicate_context", _CONF_DUPLICATE, "a large blob re-sent (re-upload waste)",
                        f"repeats the blob first sent in message #{seen[key]}",
                        "cache/reference the prior content instead of re-sending it", max_action="notice",
                        savings=_token_savings(
                            observed - SAVINGS_SETTINGS.duplicate_context_target_tokens,
                            basis="observed_duplicate_context_minus_reference_target",
                        ))]
        seen[key] = state.get("_i", 0)
        return []


class GuidanceModule(InterventionModule):
    """Best-practice / convention violations (bare except, mutable default, print-debug). Regex rules; NOTICE-only;
    failure = pedantic. Post-action by nature."""
    type = "guidance"

    def __init__(self, heuristics: list[dict]):
        self._rules = [(h, re.compile(h["match"]["regex"])) for h in heuristics if h["kind"] == "guidance"]

    def plausible(self, text: str, state: dict) -> bool:
        return True

    def ground(self, text: str, state: dict) -> list[dict]:
        out = []
        for h, rx in self._rules:
            if rx.search(text):
                out.append(_iv("guidance", h["confidence"], h["message"], text[:120].strip(),
                               h.get("suggestion", "follow the convention"), max_action=h["max_action"],
                               source_ref={"rule": h["id"]}, dedup_id=h["id"]))
        return out


class AlternativeModule(InterventionModule):
    """A simpler/more idiomatic approach exists (os.path->pathlib, manual sum->sum()). Keyword rules; NOTICE-only;
    failure = taste-dependent. Post-action/post-session."""
    type = "alternative"

    def __init__(self, heuristics: list[dict]):
        self._templates = [h for h in heuristics if h["kind"] == "alternative"]

    def plausible(self, text: str, state: dict) -> bool:
        low = text.lower()
        return any(any(k.lower() in low for k in h["match"]["keywords"]) for h in self._templates)

    def ground(self, text: str, state: dict) -> list[dict]:
        low = text.lower()
        out = []
        for h in self._templates:
            if any(k.lower() in low for k in h["match"]["keywords"]):
                out.append(_iv("alternative", h["confidence"], h["message"], text[:120].strip(),
                               h.get("suggestion", "consider the simpler idiom"), max_action=h["max_action"],
                               source_ref={"rule": h["id"]}, dedup_id=h["id"]))
        return out


class ShortcutModule(InterventionModule):
    """Observed repetition: the same tool used >= _SHORTCUT_REPEAT times in a session -> 'batch/script it'. Grounded
    in the captured event stream (state['_event'].tool), not a pattern. Fires once per tool when it crosses."""
    type = "shortcut"

    def plausible(self, text: str, state: dict) -> bool:
        return bool((state.get("_event") or {}).get("tool"))

    def ground(self, text: str, state: dict) -> list[dict]:
        tool = (state.get("_event") or {}).get("tool")
        counts = state.setdefault("tool_counts", {})
        counts[tool] = counts.get(tool, 0) + 1
        if counts[tool] == _SHORTCUT_REPEAT:  # fire exactly once, at the crossing
            return [_iv("shortcut", 0.6, f"you've used {tool} {counts[tool]} times manually in this session",
                        f"{tool} x{counts[tool]}", "replace the repeated manual action with a batch/loop/glob/script",
                        max_action="notice", dedup_id=f"shortcut:{tool}",
                        savings=_token_savings(
                            counts[tool] * SAVINGS_SETTINGS.shortcut_tokens_per_manual_step,
                            basis="heuristic_repeated_manual_tool_steps",
                        ))]
        return []


class ProductReinventionModule(InterventionModule):
    """Product-level reinvention, GROUNDED in latent product space (#102): 'build an AI coding assistant' overlaps
    heavily with Cursor/Continue/Claude Code. Uses the embedder PLANE (best_embedder runtime; inject lexical floor in
    proofs). Embeds the product space once, lazily."""
    type = "product_reinvention"
    _INTENT_NOUNS = ("build", "create", "app", "platform", "system", "assistant", "framework", "database", "tool",
                     "engine", "product")

    def __init__(self, embed_fn=None):
        # default to the deterministic, keyless LEXICAL floor (conservative high_overlap = fewer false alarms,
        # offline gate). Pass best_embedder() explicitly for semantic recall at runtime (the quality fork).
        if embed_fn is None:
            from ..knowledge._vec import py_function_src_teleon_knowledge__vec__lexical_embed_fn
            embed_fn = py_function_src_teleon_knowledge__vec__lexical_embed_fn()
        self._embed_fn = embed_fn
        self._space = None

    def _space_(self):
        if self._space is None:
            from ..knowledge.product_distance import py_function_src_teleon_knowledge_product_distance__build_product_space
            self._space = py_function_src_teleon_knowledge_product_distance__build_product_space(embed_fn=self._embed_fn)
        return self._space

    def plausible(self, text: str, state: dict) -> bool:
        low = text.lower()
        return _detect_intent(text)["build_intent"] and any(w in low for w in self._INTENT_NOUNS)

    def ground(self, text: str, state: dict) -> list[dict]:
        from ..knowledge.product_distance import py_function_src_teleon_knowledge_product_distance__distance_to_products
        r = py_function_src_teleon_knowledge_product_distance__distance_to_products(text, self._space_(), embed_fn=self._embed_fn)
        if not r["high_overlap"]:
            return []
        names = [p["product"] for p in r["nearest_products"][:3]]
        return [_iv("product_reinvention", min(0.9, max(_PER_TYPE_FLOOR, r["reinvention_probability"])),
                    f"overlaps heavily with existing products ({r['nearest_cluster']})", text[:120].strip(),
                    f"compare with {', '.join(names)} before building", max_action="notice",
                    source_ref={"nearest": r["nearest_products"][:3]}, dedup_id=f"product:{r['nearest_cluster']}",
                    savings=_token_savings(
                        SAVINGS_SETTINGS.product_overlap_tokens_avoided,
                        model_calls_avoided=1,
                        basis="heuristic_existing_product_overlap",
                    ))]


def default_modules(embed_fn=None) -> list[InterventionModule]:
    """The full taxonomy. embed_fn is threaded into the embedding-backed module (product_reinvention): None ->
    best_embedder (runtime quality); inject the lexical floor in proofs for a deterministic, offline gate."""
    h = _load_heuristics()
    return [ReinventionModule(), MLCompetitionReinventionModule(), ManualContextWasteModule(),
            StackReinventionModule(), ProductReinventionModule(embed_fn), FootgunModule(h),
            AdversarialModule(h), ReinventionClusterModule(h), GuidanceModule(h), AlternativeModule(h),
            ShortcutModule(), OversizedContextModule(), DuplicateContextModule()]


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
    state: dict = {"seen_prefixes": {}, "reinvention_cluster_signals": set(), "fired": set()}
    findings: list[dict] = []

    for i, ev in enumerate(events):
        text = _message_text(ev)
        if not text.strip():
            continue
        state["_i"] = i
        state["_event"] = ev  # expose event metadata (e.g. tool name) to stateful modules (shortcut)
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
    savings = _savings_summary(findings)
    return {
        "mode": mode,
        "report": findings,
        "surfaced": surfaced,
        "summary": {"messages": len(events), "findings": len(findings), "by_type": by_type,
                    "would_interrupt": len(surfaced),
                    "tokens_avoided_estimate": savings["tokens_avoided_estimate"],
                    "model_calls_avoided_estimate": savings["model_calls_avoided_estimate"]},
        "savings": savings,
        "serves_truth": False,
        "governed": "candidate findings (discovery != trust); a human triages; the accept/reject outcome tunes thresholds",
    }
