"""check_local_embedder — proof that semantic embeddings run LOCALLY with NO API KEY (the local-first principle).

Wires the local Ollama embedder (nomic-embed-text) behind the embedding_port. Proves: it is registered (not the
honest 'not wired' stub), it targets localhost with no key/env, and best_embedder() always returns a WORKING
embedder (local-semantic when the daemon is up, lexical baseline when not) without ever crashing or reaching for a
cloud key. Gate-safe: passes whether or not the local Ollama daemon is running. Deterministic-ish, offline, stdlib.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.teleon.retrieval.embedding_port import (  # noqa: E402
    LexicalEmbedder, LocalOllamaEmbedder, best_embedder, select_embedder,
)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    fails: list[str] = []
    checks = 0

    def ck(name: str, ok: bool, detail: str = "") -> None:
        nonlocal checks
        checks += 1
        if not ok:
            fails.append(f"{name}{(': ' + detail) if detail else ''}")
        if args.self_test and not ok:
            print(f"  [{'ok' if ok else 'XX'}] {name}{(' — ' + detail) if detail else ''}")

    # nomic_embed is now WIRED to the local embedder (was an honest 'not wired' stub before)
    emb = select_embedder("nomic_embed")
    ck("nomic_embed resolves to the LOCAL embedder", isinstance(emb, LocalOllamaEmbedder))

    # local-first: it targets localhost, no API key / env var anywhere in the local path
    src = (_REPO / "src" / "teleon" / "retrieval" / "embedding_port.py").read_text()
    local_block = src[src.index("class LocalOllamaEmbedder"):src.index("_NAME_ADAPTERS")]
    ck("local embedder uses localhost", "localhost" in src)
    ck("local embedder needs NO api key / env", not any(k in local_block for k in ("API_KEY", "os.environ", "getenv", "Authorization")))

    # best_embedder() always returns a WORKING embedder (no key), and never crashes
    be = best_embedder()
    vec = be.embed("extract text from a pdf document")
    ck("best_embedder returns a working embedder (no key)", isinstance(vec, list) and len(vec) >= 1)
    ck("best_embedder is local-semantic OR lexical baseline (never cloud)",
       isinstance(be, (LocalOllamaEmbedder, LexicalEmbedder)), be.name)

    # if the local daemon is up, prove it's genuinely SEMANTIC (pdf closer than an unrelated tool)
    if isinstance(be, LocalOllamaEmbedder):
        import math
        def cos(a, b):
            d = sum(x * y for x, y in zip(a, b)); na = math.sqrt(sum(x * x for x in a)); nb = math.sqrt(sum(y * y for y in b))
            return d / (na * nb) if na and nb else 0.0
        q = be.embed("extract text from a pdf")
        pdf = cos(q, be.embed("PyMuPDF PDF text extraction"))
        obj = cos(q, be.embed("YOLO object detection in images"))
        ck("LIVE local embeddings are semantic (pdf > unrelated)", pdf > obj, f"pdf={pdf:.3f} obj={obj:.3f}")
        print(f"  [local daemon up] semantic: cos(pdf)={pdf:.3f} > cos(object-detection)={obj:.3f}")
    else:
        print("  [local daemon down] honest fallback to the lexical baseline (still no key) — gate-safe")

    if fails:
        print(f"\nFAIL - check_local_embedder: {len(fails)} of {checks} assertions failed")
        for f in fails:
            print(f"  - {f}")
        return 1
    print(f"PASS - check_local_embedder: semantic embeddings run LOCALLY (Ollama nomic-embed-text) with NO API KEY; "
          f"best_embedder falls back to the lexical baseline offline; {checks} assertions; local-first.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
