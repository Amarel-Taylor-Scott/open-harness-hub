"""src.teleon.context.compressor — content-aware, REVERSIBLE context compression for what Teleon sends to models.

Cut tokens BEFORE an LLM call (the Headroom idea, our way: DETERMINISTIC + LOSSLESS). Content-aware by kind:
  * code  -> drop comments/docstring one-liners/blank lines + dedup (keep the signatures/structure)
  * json  -> keep keys; sample large arrays ("...(+N more)"); truncate huge strings
  * text  -> dedup repeated lines; head+tail if very long
REVERSIBLE (CCR): the RAW is stored locally under a content-hash handle (ccr://<hash>) and ``rehydrate(handle)``
returns it byte-for-byte — nothing is lost (the lossless-distillation law). The compressed form is what's sent; the
raw is recallable for audit/expansion. A candidate realization of OpenCompressionHub /
_repos/shared-backend-components/architecture/context_compression_provider_catalog.json; the prompt-layer sibling is evolution/token_reduction.py.
Pure + deterministic; offline; Teleon-layer — never imports src.baltor; never serves truth.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import hashlib
import json
from pathlib import Path

from src.teleon.evolution.token_reduction import estimate_tokens

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[3])
_CCR = _resource("data") / "ccr"          # reversible raw store (content-addressed; gitignored data/)
_TEXT_HEADTAIL = 4000                   # for very long text: keep this many chars head + tail
_JSON_ARRAY_SAMPLE = 5
_JSON_STR_CAP = 200


def _detect_kind(text: str) -> str:
    s = text.lstrip()
    if s.startswith(("{", "[")):
        return "json"
    if "```python" in text or text.startswith(("def ", "class ")) or "\ndef " in text or "\nclass " in text:
        return "code"
    return "text"


def _dedup_lines(s: str) -> str:
    seen, out = set(), []
    for ln in s.splitlines():
        if ln.strip() and ln in seen:
            continue
        seen.add(ln)
        out.append(ln)
    return "\n".join(out)


def _compress_code(text: str) -> str:
    out = []
    for ln in text.splitlines():
        st = ln.strip()
        if not st or st.startswith("#"):     # drop blank lines + comments (incl. the signature one-liners)
            continue
        out.append(ln)
    return _dedup_lines("\n".join(out))


def _compress_json(text: str) -> str:
    try:
        d = json.loads(text)
    except Exception:
        return text

    def shrink(o):
        if isinstance(o, list):
            head = [shrink(x) for x in o[:_JSON_ARRAY_SAMPLE]]
            return head + ([f"...(+{len(o) - _JSON_ARRAY_SAMPLE} more)"] if len(o) > _JSON_ARRAY_SAMPLE else [])
        if isinstance(o, dict):
            return {k: shrink(v) for k, v in o.items()}
        if isinstance(o, str) and len(o) > _JSON_STR_CAP:
            return o[:_JSON_STR_CAP] + f"...(+{len(o) - _JSON_STR_CAP} chars)"
        return o
    return json.dumps(shrink(d), separators=(",", ":"))


def _compress_text(text: str) -> str:
    s = _dedup_lines(text)
    if len(s) > 2 * _TEXT_HEADTAIL:
        s = s[:_TEXT_HEADTAIL] + f"\n...(+{len(s) - 2 * _TEXT_HEADTAIL} chars elided; recall via ccr handle)...\n" + s[-_TEXT_HEADTAIL:]
    return s


def compress(text: str, *, kind: str = "auto", store: bool = True) -> dict:
    """Compress ``text`` content-aware + reversibly. Returns {compressed, handle, kind, raw_chars, compressed_chars,
    raw_tokens, compressed_tokens, ratio, serves_truth}. The RAW is stored (content-addressed) so rehydrate() can
    return it byte-for-byte (lossless)."""
    text = text or ""
    k = _detect_kind(text) if kind == "auto" else kind
    fn = {"code": _compress_code, "json": _compress_json, "text": _compress_text}.get(k, _compress_text)
    compressed = fn(text)
    if len(compressed) >= len(text):          # never expand — fall back to the original
        compressed = text
    handle = ""
    if store and text and len(compressed) < len(text):
        h = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
        _CCR.mkdir(parents=True, exist_ok=True)
        p = _CCR / f"{h}.txt"
        if not p.exists():                    # content-addressed -> dedup; identical context stored once
            p.write_text(text, encoding="utf-8")
        handle = f"ccr://{h}"
    rt, ct = estimate_tokens(text), estimate_tokens(compressed)
    return {"compressed": compressed, "handle": handle, "kind": k, "raw_chars": len(text),
            "compressed_chars": len(compressed), "raw_tokens": rt, "compressed_tokens": ct,
            "ratio": round(1 - ct / rt, 4) if rt else 0.0, "serves_truth": False}


def rehydrate(handle: str) -> str:
    """Return the RAW context byte-for-byte for a ccr:// handle (the lossless recall). Raises if unknown."""
    if not handle.startswith("ccr://"):
        raise ValueError(f"not a ccr handle: {handle!r}")
    p = _CCR / f"{handle[len('ccr://'):]}.txt"
    if not p.exists():
        raise FileNotFoundError(f"no stored raw for {handle}")
    return p.read_text(encoding="utf-8")
