#!/usr/bin/env python3
"""Foundry model_route — the production seam for the model/agent stages.

Offline, the foundry's gap-probe / measurement / authoring run on deterministic
defaults (zero cost, fully tested). This module is the **one place** a live model is
wired in: set an API key and the same pipeline confirms gaps live and measures real
`pipeline_score − bare_model_score` deltas — so the open/free/commercial tagging then
applies to genuinely model-built, measured components.

  - ``ModelRoute`` wraps a single ``complete(prompt, system) -> str`` callable.
  - ``from_env()`` builds one from ``ANTHROPIC_API_KEY`` or an OpenAI-compatible
    ``OPENAI_API_KEY`` (+ optional ``OPENAI_BASE_URL`` / ``OH_CHAT_MODEL``); returns
    ``None`` when no key is set, so callers fall back to the offline defaults.
  - Adapters implement the stage protocols: ``RouteBareModel`` (Stage 0 prober +
    Stage 5 bare), ``RouteJudge`` (Stage 5 LLM-judge), ``RoutePipelineRunner``
    (Stage 5 grounded run — the model answering *with* the component's content).
  - ``wire(foundry, route)`` swaps the live measurement + gap-probe into a `Foundry`.

The HTTP lives in ``from_env``'s closure and only fires when a key is present; the
self-test injects a scripted route, so this module is verified offline with no
network. stdlib-only.

Run ``python -m scripts.foundry.model_route`` for the offline self-test.
"""
from __future__ import annotations

import json
import os
import re
import urllib.request
from typing import Any, Callable

from scripts.foundry.contracts import Candidate, FoundryContext
from scripts.foundry.measure import MeasurementStage

_SCORE_RE = re.compile(r"\d+(?:\.\d+)?|\.\d+")   # first number; clamped to [0,1]
_DEFAULT_CHAT_MODEL = "claude-opus-4-8"   # overridable via OH_CHAT_MODEL
_DEFAULT_OLLAMA_EMBED_MODEL = "nomic-embed-text"   # an Ollama embedding tag (see scripts/_config)


class ModelRoute:
    """A thin wrapper over a completion callable so adapters stay transport-agnostic."""

    def __init__(self, complete_fn: Callable[[str, str | None], str], *,
                 embed_fn: Callable[[str], list[float]] | None = None, name: str = "route") -> None:
        self._complete = complete_fn
        self._embed = embed_fn
        self.name = name

    def complete(self, prompt: str, system: str | None = None) -> str:
        return self._complete(prompt, system)

    @property
    def has_embeddings(self) -> bool:
        return self._embed is not None

    def embed(self, text: str) -> list[float]:
        if self._embed is None:
            raise RuntimeError("this route has no embeddings endpoint (pair with Ollama/OpenAI)")
        return self._embed(text)


def _openai_compatible(base: str, key: str, model: str, embed_model: str):
    """Build (complete_fn, embed_fn) for any OpenAI-compatible endpoint (OpenAI, Ollama Cloud, vLLM…)."""
    base = base.rstrip("/")

    def _complete(prompt: str, system: str | None = None) -> str:
        msgs = ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": prompt}]
        req = urllib.request.Request(
            f"{base}/chat/completions",
            data=json.dumps({"model": model, "messages": msgs}).encode(),
            headers={"authorization": f"Bearer {key}", "content-type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=60) as r:  # pragma: no cover - network
            data = json.loads(r.read())
        return data["choices"][0]["message"]["content"]

    def _embed(text: str) -> list[float]:
        req = urllib.request.Request(
            f"{base}/embeddings",
            data=json.dumps({"model": embed_model, "input": text}).encode(),
            headers={"authorization": f"Bearer {key}", "content-type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=60) as r:  # pragma: no cover - network
            data = json.loads(r.read())
        return data["data"][0]["embedding"]

    return _complete, _embed


def from_env() -> ModelRoute | None:
    """Build a ModelRoute from env, or None (→ offline defaults). No network unless called.

    Priority: ``OLLAMA_API_KEY`` (Ollama Cloud — chat **and** embeddings) → ``MISTRAL_API_KEY``
    → ``OPENROUTER_API_KEY`` → ``ANTHROPIC_API_KEY`` → ``OPENAI_API_KEY`` (+ ``OPENAI_BASE_URL``).
    Mistral and OpenRouter are OpenAI-compatible, so they ride ``_openai_compatible`` with their
    own base URLs. Pick models with ``OH_CHAT_MODEL`` / ``OH_EMBED_MODEL``.
    """
    model = os.environ.get("OH_CHAT_MODEL", _DEFAULT_CHAT_MODEL)

    # Ollama Cloud — OpenAI-compatible at <host>/v1; the only single key that gives BOTH
    # chat (measurement/authoring) AND embeddings (the real-embedder / vector-ready gate).
    if os.environ.get("OLLAMA_API_KEY"):
        host = os.environ.get("OLLAMA_HOST", "https://ollama.com").rstrip("/")
        key = os.environ["OLLAMA_API_KEY"]
        embed_model = os.environ.get("OH_EMBED_MODEL", _DEFAULT_OLLAMA_EMBED_MODEL)
        comp, _ = _openai_compatible(f"{host}/v1", key, model, embed_model)  # chat via OpenAI-compatible /v1

        def _ollama_embed(text: str) -> list[float]:
            # Ollama embeddings use the NATIVE /api/embed endpoint (not /v1/embeddings).
            req = urllib.request.Request(
                f"{host}/api/embed",
                data=json.dumps({"model": embed_model, "input": text}).encode(),
                headers={"authorization": f"Bearer {key}", "content-type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=60) as r:  # pragma: no cover - network
                d = json.loads(r.read())
            vecs = d.get("embeddings") or ([d["embedding"]] if "embedding" in d else [])
            return vecs[0]

        return ModelRoute(comp, embed_fn=_ollama_embed, name=f"ollama:{model}")

    # Mistral — OpenAI-compatible (the owner's existing keys); chat + mistral-embed embeddings.
    if os.environ.get("MISTRAL_API_KEY"):
        base = os.environ.get("MISTRAL_BASE_URL", "https://api.mistral.ai/v1")
        mdl = os.environ.get("OH_CHAT_MODEL") or "mistral-small-latest"
        embed_model = os.environ.get("OH_EMBED_MODEL", "mistral-embed")
        comp, emb = _openai_compatible(base, os.environ["MISTRAL_API_KEY"], mdl, embed_model)
        return ModelRoute(comp, embed_fn=emb, name=f"mistral:{mdl}")

    # OpenRouter — OpenAI-compatible gateway to many models (incl. ':free' variants).
    if os.environ.get("OPENROUTER_API_KEY"):
        base = os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
        embed_model = os.environ.get("OH_EMBED_MODEL", "text-embedding-3-small")
        comp, emb = _openai_compatible(base, os.environ["OPENROUTER_API_KEY"], model, embed_model)
        return ModelRoute(comp, embed_fn=emb, name=f"openrouter:{model}")

    if os.environ.get("ANTHROPIC_API_KEY"):
        key = os.environ["ANTHROPIC_API_KEY"]

        def _complete(prompt: str, system: str | None = None) -> str:
            body = {"model": model, "max_tokens": 1024, "messages": [{"role": "user", "content": prompt}]}
            if system:
                body["system"] = system
            req = urllib.request.Request(
                "https://api.anthropic.com/v1/messages",
                data=json.dumps(body).encode(),
                headers={"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=60) as r:  # pragma: no cover - network
                data = json.loads(r.read())
            return "".join(b.get("text", "") for b in data.get("content", []))

        # Anthropic has no embeddings endpoint — pair with Ollama/OpenAI for the embedder.
        return ModelRoute(_complete, name=f"anthropic:{model}")

    if os.environ.get("OPENAI_API_KEY"):
        base = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
        embed_model = os.environ.get("OH_EMBED_MODEL", "text-embedding-3-small")
        comp, emb = _openai_compatible(base, os.environ["OPENAI_API_KEY"], model, embed_model)
        return ModelRoute(comp, embed_fn=emb, name=f"openai:{model}")

    return None


def _parse_score(text: str) -> float | None:
    m = _SCORE_RE.search(text or "")
    if not m:
        return None
    try:
        return max(0.0, min(1.0, float(m.group(0))))
    except ValueError:
        return None


def _grounding_text(candidate: Candidate) -> str:
    """The component's content, injected so the 'pipeline' answer is grounded."""
    body = candidate.body or {}
    parts = [body.get("description", "")]
    for e in (body.get("_entries") or [])[:50]:
        parts.append(json.dumps(e) if isinstance(e, dict) else str(e))
    for r in (body.get("rules") or [])[:50]:
        parts.append(json.dumps(r) if isinstance(r, dict) else str(r))
    return "\n".join(p for p in parts if p)[:6000]


class RouteBareModel:
    """Bare model — answers the task with no pipeline (Stage 0 probe + Stage 5 baseline)."""

    def __init__(self, route: ModelRoute) -> None:
        self.route = route

    def probe(self, task: dict) -> str:
        return self.answer(task)

    def answer(self, task: dict) -> str:
        return self.route.complete(task.get("prompt") or task.get("task") or "")


class RouteJudge:
    """LLM-judge — scores an answer 0..1 against the task (+ reference if present)."""

    name = "model-judge"

    def __init__(self, route: ModelRoute) -> None:
        self.route = route

    def score(self, task: dict, answer: str | None) -> float | None:
        if answer is None:
            return None
        gold = task.get("correct_answer")
        system = "You are a strict grader. Reply with ONLY a number from 0 to 1."
        prompt = (f"TASK: {task.get('prompt', '')}\n"
                  + (f"REFERENCE ANSWER: {gold}\n" if gold else "")
                  + f"CANDIDATE ANSWER: {answer}\n"
                  "Score 0..1 how correct and complete the candidate answer is.")
        return _parse_score(self.route.complete(prompt, system))


class RoutePipelineRunner:
    """The 'pipeline' answer — the model answering WITH the component's content injected."""

    def __init__(self, route: ModelRoute) -> None:
        self.route = route

    def run(self, task: dict, candidate: Candidate) -> str:
        system = "Answer using the provided grounding when relevant; prefer it over guessing."
        return self.route.complete(
            f"GROUNDING:\n{_grounding_text(candidate)}\n\nTASK: {task.get('prompt', '')}", system)


class RouteEmbedder:
    """Real embeddings via the route (Stage 7) — flips object_embedding to vector-search-ready.

    Satisfies `stage_load.Embedder` (model · dim · is_real · embed). Set ``OH_EMBED_MODEL``
    to match the route's embedding model so the declared dimension matches the vectors."""

    is_real = True

    def __init__(self, route: ModelRoute, *, model: str | None = None, dim: int | None = None) -> None:
        from scripts._config import DEFAULT_EMBEDDING_DIMENSIONS, DEFAULT_EMBEDDING_MODEL, EMBEDDING_MODELS

        self.route = route
        self.model = model or os.environ.get("OH_EMBED_MODEL") or DEFAULT_EMBEDDING_MODEL
        self.dim = dim or EMBEDDING_MODELS.get(self.model, DEFAULT_EMBEDDING_DIMENSIONS)

    def embed(self, text: str) -> list[float]:
        return self.route.embed(text)


def measurement_stage(route: ModelRoute) -> MeasurementStage:
    from scripts.foundry.benchmark_synth import RouteSynth
    return MeasurementStage(judge=RouteJudge(route), bare_model=RouteBareModel(route),
                            pipeline_runner=RoutePipelineRunner(route), synthesizer=RouteSynth(route))


def wire(foundry: Any, route: ModelRoute) -> Any:
    """Swap the live measurement + gap-probe into a Foundry (in place); returns it."""
    foundry.measure = measurement_stage(route)
    foundry.gaps.prober = RouteBareModel(route)
    foundry.gaps.judge = RouteJudge(route)
    # keep self.stages pointing at the new measure stage
    foundry.stages = [(fs, foundry.measure if fs == "lift_measured" else st) for fs, st in foundry.stages]
    # real embeddings → vector-search-ready (clears gate #6) — but ONLY if the embed
    # endpoint is actually entitled. Probe once; otherwise keep the placeholder embedder
    # (staging-only), so a route without embeddings never breaks Stage 7.
    if route.has_embeddings:
        try:
            route.embed("probe")
            foundry.stage_load.embedder = RouteEmbedder(route)
        except Exception:
            pass
    return foundry


# --------------------------------------------------------------------------- #
# self-test (offline; a SCRIPTED route — no network, no key)
# --------------------------------------------------------------------------- #
class _FakeRoute(ModelRoute):
    """Bare answers are vague; grounded answers carry a sentinel the judge rewards."""

    def __init__(self) -> None:
        super().__init__(self._c, embed_fn=self._e, name="fake")

    def _c(self, prompt: str, system: str | None = None) -> str:
        if system and "grader" in system.lower():
            return "0.95" if "GROUNDED" in prompt else "0.15"
        if "GROUNDING:" in prompt:
            return "GROUNDED: the answer per the provided source."
        return "an unsure guess"

    def _e(self, text: str) -> list[float]:
        return [0.1] * 8


def _self_test() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    # score parsing
    check("parse '0.9'", _parse_score("0.9") == 0.9)
    check("parse 'Score: 1'", _parse_score("Score: 1") == 1.0)
    check("clamp >1", _parse_score("7") == 1.0)
    check("none on garbage", _parse_score("no number here") is None)

    # from_env returns None offline (no keys) — so the foundry stays on offline defaults
    saved = {k: os.environ.pop(k, None) for k in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY")}
    try:
        check("from_env() is None without keys", from_env() is None)
    finally:
        for k, v in saved.items():
            if v is not None:
                os.environ[k] = v

    # adapters route correctly
    route = _FakeRoute()
    check("RouteBareModel.answer calls route", "guess" in RouteBareModel(route).answer({"prompt": "q"}))
    check("RouteJudge parses a score", RouteJudge(route).score({"prompt": "q", "correct_answer": "x"}, "GROUNDED") == 0.95)
    cand = Candidate(target_type="knowledge-pack", body={"description": "facts", "_entries": [{"a": 1}]})
    check("RoutePipelineRunner injects grounding", "GROUNDED" in RoutePipelineRunner(route).run({"prompt": "q"}, cand))

    # END-TO-END: a model-backed measurement yields a positive delta from generated answers
    c = Candidate(target_type="knowledge-pack", component_id="knowledge-pack/x",
                  body={"description": "csddd", "_entries": [{"art": "8"}]},
                  gap={"id": "g", "eval_tasks": [{"prompt": "cite art 8", "correct_answer": "Article 8"},
                                                 {"prompt": "cite art 29", "correct_answer": "Article 29"}]},
                  source={"source_url": "https://eur-lex.europa.eu/x", "author": "EU", "license": "CC-BY-4.0"})
    ctx = FoundryContext()
    measurement_stage(route).run([c], ctx)
    check("model-backed measurement produced a lift", bool(c.lift) and c.lift["delta"] > 0.5, str(c.lift))
    check("not flagged offline (live route)", c.lift and c.lift["measured_offline"] is False)
    check("model calls spent (bare+pipeline per task)", ctx.model_calls >= 4, f"calls={ctx.model_calls}")

    # wire() swaps the live stage into a Foundry without breaking the pipeline
    from scripts.foundry.pipeline import Foundry
    f = wire(Foundry(), route)
    check("wire() set a model-backed measure stage", isinstance(f.measure.judge, RouteJudge))
    check("wire() kept measure in the stage list", any(st is f.measure for _fs, st in f.stages))

    # embeddings: the route serves vectors → a REAL embedder (clears the vector-ready gate)
    check("route exposes embeddings", route.has_embeddings)
    re_emb = RouteEmbedder(route, model="all-minilm", dim=8)
    check("RouteEmbedder returns a real vector", len(re_emb.embed("x")) == 8 and re_emb.is_real)
    check("wire() upgraded stage_load to a real embedder", getattr(f.stage_load.embedder, "is_real", False) is True)

    print(f"\n{'all model_route self-tests passed.' if not failures else f'{len(failures)} FAILURES: {failures}'}")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(_self_test())
