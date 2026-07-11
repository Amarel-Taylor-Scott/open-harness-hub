#!/usr/bin/env python3
"""browser_control.llm_extraction_adapter — the LLM-assisted extraction lane (UNTRUSTED, candidate-only).

Turns page text into structured candidates an LLM is good at proposing: a filled schema, candidate primitives,
answers to a question bank, and a grounding CHECK of a prior extraction. This is the discovery/exploration
lane — its output is NON-DETERMINISTIC and is quarantined: every result is stamped ``untrusted=true`` /
``serves_truth=false`` and must be verified before anything downstream trusts it (the repo's candidate/truth
boundary applied to model output).

OFFLINE STUB IS THE DEFAULT. With no provider configured the adapter runs a deterministic, dependency-free
stub (regex/heuristic) so tests and dev never need a model or a key. Live extraction is OPT-IN
(``mode="live"``) and routes to a LOCAL endpoint (Ollama :11434 or an OpenAI-compatible :8000) or the
file-based OpenRouter key lane — presence-only, keys never read into a record. ``verify_extraction`` is a REAL
deterministic verifier (is each extracted value grounded as a substring of the source?), so it is the one
method whose signal is trustworthy even though its inputs came from a model.

Nothing raises: a down provider or a bad schema returns a structured ``{"supported": False|True, "ok": ...}``.

    python3 browser_control/ingestion_self_test.py --self-test   # offline stub, mutation-gated
"""
from __future__ import annotations

import sys
from pathlib import Path

_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install, resource  # noqa: E402

_install()

import json  # noqa: E402
import re  # noqa: E402
import urllib.error  # noqa: E402
import urllib.request  # noqa: E402
from typing import Any, Optional  # noqa: E402

from scripts.primitive_browser_control_harness import BOUNDARY, redact_secrets  # noqa: E402

#: every model-derived result carries this — quarantined until a verifier + promotion pass (never truth)
UNTRUSTED: dict[str, Any] = {"untrusted": True, "candidate": True, "serves_truth": False}
#: local, keyless LLM endpoints tried in "live" mode (up/down + http only — never a model name or a secret)
_LOCAL_ENDPOINTS: dict[str, str] = {"ollama_11434": "http://localhost:11434/api/tags",
                                    "openai_compat_8000": "http://localhost:8000/v1/models"}
_SENTENCE_RE = re.compile(r"[^.!?\n]+[.!?]?")
_STOPWORDS = frozenset(("the", "a", "an", "and", "or", "of", "to", "in", "on", "for", "is", "are", "be",
                        "this", "that", "with", "by", "as", "at", "it", "from"))


def _ping(url: str, timeout: float = 2.0) -> dict[str, Any]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:  # noqa: S310 (loopback only)
            return {"up": resp.getcode() == 200, "http": resp.getcode()}
    except urllib.error.HTTPError as http_err:
        return {"up": False, "http": http_err.code}
    except Exception as exc:  # noqa: BLE001
        return {"up": False, "error": type(exc).__name__}


def _openrouter_file_presence() -> dict[str, Any]:
    """Presence + COUNT of file-based OpenRouter keys (a count is not a secret; values are NEVER read)."""
    try:
        path = resource(".agent/openrouter_keys.txt")
        if path.is_file():
            return {"present": True, "count": sum(1 for ln in path.read_text().splitlines() if ln.strip())}
    except Exception:  # noqa: BLE001
        pass
    return {"present": False, "count": 0}


class LLMExtractionAdapter:
    """LLM-assisted structured extraction. Offline deterministic stub by default; live mode is opt-in and
    routes to a local endpoint / the OpenRouter file lane. All output is UNTRUSTED + candidate-only."""

    name = "llm_extraction"

    def __init__(self, *, mode: str = "offline_stub", provider: str = "auto", timeout: float = 20.0) -> None:
        self._mode = mode                 # "offline_stub" (default) | "live"
        self._provider = provider
        self._timeout = float(timeout)

    # ── capability introspection (presence-only; no secrets) ─────────────────────────────────────────────────
    def capabilities(self) -> dict[str, Any]:
        return {"adapter": self.name, "default_mode": "offline_stub", "current_mode": self._mode,
                "read_only": True, "output_trust": "untrusted",
                "methods": ["extract_schema", "extract_primitives", "ask_questions", "verify_extraction"],
                "providers": {k: _ping(u) for k, u in _LOCAL_ENDPOINTS.items()},
                "openrouter_file": _openrouter_file_presence(), **BOUNDARY}

    # ── extraction (offline stub is deterministic; live is opt-in) ───────────────────────────────────────────
    def extract_schema(self, text: str, schema: dict[str, Any]) -> dict[str, Any]:
        """Fill ``schema`` (field -> hint) from ``text``. Output keys == schema keys EXACTLY. Untrusted."""
        if not isinstance(schema, dict) or not schema:
            return {"supported": False, "adapter": self.name, "reason": "schema must be a non-empty dict of fields",
                    **BOUNDARY}
        if self._mode == "live":
            live = self._live_json(self._schema_prompt(text, schema))
            if live.get("ok"):
                extraction = {k: live["json"].get(k) for k in schema}   # coerce to exactly the requested keys
                return self._extraction_result(extraction, schema, source_text=text, engine="live")
            return {"supported": True, "ok": False, "adapter": self.name, "mode": "live",
                    "reason": live.get("error", "live provider unavailable"), **UNTRUSTED}
        extraction = {field: self._stub_field(text, field, hint) for field, hint in schema.items()}
        return self._extraction_result(extraction, schema, source_text=text, engine="offline_stub")

    def extract_primitives(self, text: str, *, max_primitives: int = 8) -> dict[str, Any]:
        """Propose candidate primitives (name + description + kind guess) from the text. Untrusted candidates."""
        sentences = [s.strip() for s in _SENTENCE_RE.findall(text or "") if len(s.strip()) >= 12][:max_primitives]
        prims: list[dict[str, Any]] = []
        for i, s in enumerate(sentences):
            clean, _ = redact_secrets(s)
            prims.append({"name": self._slug(clean, i), "description": clean[:200],
                          "kind_guess": self._kind_guess(clean), **UNTRUSTED})
        return {"supported": True, "adapter": self.name, "mode": self._mode, "primitives": prims,
                "n": len(prims), **UNTRUSTED}

    def ask_questions(self, text: str, questions: list[str]) -> dict[str, Any]:
        """Answer each question from the text (stub: a grounded snippet or 'unknown'). Untrusted answers."""
        answers: list[dict[str, Any]] = []
        for q in (questions or []):
            snippet = self._grounded_snippet(text or "", q)
            clean, _ = redact_secrets(snippet)
            answers.append({"question": q, "answer": clean or "unknown", "grounded": bool(snippet), **UNTRUSTED})
        return {"supported": True, "adapter": self.name, "mode": self._mode, "answers": answers,
                "n": len(answers), **UNTRUSTED}

    def verify_extraction(self, extraction: dict[str, Any], text: str) -> dict[str, Any]:
        """DETERMINISTIC grounding check: is each extracted string value a substring of the source text?
        This is the trustworthy signal that gates the untrusted extraction — a value that is not grounded is
        flagged (a hallucination guard). Returns per-field checks + ``all_grounded``."""
        src = (text or "").lower()
        checks: list[dict[str, Any]] = []
        for field, value in (extraction or {}).items():
            if value is None or value == "":
                checks.append({"field": field, "value": value, "grounded": None, "note": "empty/None"})
                continue
            grounded = str(value).strip().lower() in src
            checks.append({"field": field, "value": value, "grounded": grounded})
        grounded_flags = [c["grounded"] for c in checks if c["grounded"] is not None]
        n_ungrounded = sum(1 for g in grounded_flags if g is False)
        return {"supported": True, "adapter": self.name, "checks": checks,
                "all_grounded": bool(grounded_flags) and all(grounded_flags), "n_ungrounded": n_ungrounded,
                "n_checked": len(grounded_flags), "candidate": True, "serves_truth": False}

    # ── offline-stub field heuristics (deterministic; no model) ──────────────────────────────────────────────
    def _stub_field(self, text: str, field: str, hint: Any) -> Optional[str]:
        text = text or ""
        f = field.lower()
        if any(t in f for t in ("amount", "price", "total", "cost")):
            m = re.search(r"\$?\d[\d,]*(?:\.\d+)?", text)
            return m.group(0) if m else None
        if "date" in f:
            m = re.search(r"\b\d{4}-\d{2}-\d{2}\b", text)
            return m.group(0) if m else None
        if "email" in f:
            m = re.search(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}", text)
            return m.group(0) if m else None
        if "url" in f or "link" in f:
            m = re.search(r"https?://\S+", text)
            return m.group(0).rstrip(".,)") if m else None
        if "title" in f or "name" in f:
            first = next((s.strip() for s in _SENTENCE_RE.findall(text) if s.strip()), "")
            clean, _ = redact_secrets(first)
            return clean[:120] or None
        clean, _ = redact_secrets(text)
        return clean[:120] or None

    def _extraction_result(self, extraction: dict, schema: dict, *, source_text: str, engine: str) -> dict:
        redacted = {}
        for k, v in extraction.items():
            if isinstance(v, str):
                v, _ = redact_secrets(v)
            redacted[k] = v
        return {"supported": True, "adapter": self.name, "mode": self._mode, "engine": engine,
                "extraction": redacted, "keys": list(schema.keys()),
                "keys_match_schema": set(redacted) == set(schema), **UNTRUSTED}

    # ── tiny heuristics ──────────────────────────────────────────────────────────────────────────────────────
    def _slug(self, s: str, i: int) -> str:
        words = [w for w in re.findall(r"[A-Za-z0-9]+", s.lower()) if w not in _STOPWORDS][:5]
        return "primitive_" + ("_".join(words) if words else f"candidate_{i}")

    def _kind_guess(self, s: str) -> str:
        low = s.lower()
        if any(w in low for w in ("fetch", "download", "request", "get ", "api", "endpoint")):
            return "input"
        if any(w in low for w in ("if ", "when ", "unless", "validate", "check")):
            return "if_statement"
        if any(w in low for w in ("for each", "loop", "iterate", "every")):
            return "loop"
        if any(w in low for w in ("return", "output", "emit", "write", "save")):
            return "output"
        return "action"

    def _grounded_snippet(self, text: str, question: str) -> str:
        q_terms = [w for w in re.findall(r"[a-z0-9]+", question.lower()) if w not in _STOPWORDS and len(w) > 2]
        best, best_score = "", 0
        for sent in _SENTENCE_RE.findall(text):
            s = sent.strip()
            score = sum(1 for t in q_terms if t in s.lower())
            if score > best_score:
                best, best_score = s, score
        return best[:200] if best_score > 0 else ""

    # ── live lane (opt-in; local endpoints; never default) ───────────────────────────────────────────────────
    def _schema_prompt(self, text: str, schema: dict) -> str:
        fields = ", ".join(f"{k} ({v})" if v else k for k, v in schema.items())
        return ("Extract these fields as a JSON object and nothing else. Fields: " + fields
                + "\n\nText:\n" + (text or "")[:6000])

    def _live_json(self, prompt: str) -> dict[str, Any]:
        """Call a local OpenAI-compatible or Ollama endpoint and parse a JSON object from the reply. Opt-in."""
        for name, url in (("openai_compat_8000", "http://localhost:8000/v1/chat/completions"),
                          ("ollama_11434", "http://localhost:11434/api/generate")):
            if not _ping(_LOCAL_ENDPOINTS[name]).get("up"):
                continue
            try:
                if "chat/completions" in url:
                    payload = {"model": "local", "messages": [{"role": "user", "content": prompt}],
                               "temperature": 0}
                else:
                    payload = {"model": "local", "prompt": prompt, "stream": False}
                req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                             headers={"Content-Type": "application/json"}, method="POST")
                with urllib.request.urlopen(req, timeout=self._timeout) as resp:  # noqa: S310 (loopback only)
                    body = json.loads(resp.read().decode("utf-8", "ignore"))
                content = (body.get("choices", [{}])[0].get("message", {}).get("content")
                           or body.get("response") or "")
                m = re.search(r"\{.*\}", content, re.S)
                if m:
                    return {"ok": True, "json": json.loads(m.group(0)), "endpoint": name}
            except Exception as exc:  # noqa: BLE001 — a live failure is structured, never raised
                return {"ok": False, "error": f"{type(exc).__name__}: {exc}"[:200], "endpoint": name}
        return {"ok": False, "error": "no local LLM endpoint reachable"}


__all__ = ["LLMExtractionAdapter", "UNTRUSTED"]
