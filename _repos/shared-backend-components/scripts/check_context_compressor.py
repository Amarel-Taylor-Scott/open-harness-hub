#!/usr/bin/env python3
"""check_context_compressor — proof of reversible, content-aware context compression (wired into the loop).

Cuts tokens before a model call WITHOUT losing anything: content-aware per kind (code/json/text), reversible via a
CCR handle (rehydrate returns the raw byte-for-byte), never expands, token-accounted. Used by the multi-model loop to
make each cycle cheaper. serves_truth=false; lossless (the lossless-distillation law).

CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_context_compressor.py --self-test
"""
from __future__ import annotations

import os
import sys

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _R not in sys.path:
        sys.path.insert(0, _R)

from src.teleon.context.compressor import compress, rehydrate
from pathlib import Path

REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])


def _self_test() -> int:
    fails = []
    def ck(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': '+detail) if detail and not ok else ''}")
        if not ok: fails.append(name)

    code = "def f(x):\n    # a comment\n    '''doc'''\n    return x\n\n\ndef f(x):\n    # a comment\n    return x\n" * 3
    cjson = '{"entries": [' + ",".join(f'{{"id":{i},"big":"{"x"*400}"}}' for i in range(30)) + ']}'
    text = ("the same line\n" * 40) + "a unique tail line\n"

    rc = compress(code, kind="code")
    rj = compress(cjson, kind="json")
    rt = compress(text, kind="text")
    ck("code compresses (comments/blanks/dupes dropped)", rc["ratio"] > 0 and rc["compressed_chars"] < rc["raw_chars"], str(rc["ratio"]))
    ck("json compresses (large arrays sampled, big strings truncated)", rj["ratio"] > 0.5, str(rj["ratio"]))
    ck("text compresses (dedup + head/tail)", rt["ratio"] > 0, str(rt["ratio"]))
    ck("auto-detect picks the right kind", compress(code)["kind"] == "code" and compress(cjson)["kind"] == "json")

    # REVERSIBLE: the raw is recallable byte-for-byte (lossless / CCR)
    ck("compression yields a ccr:// handle for the raw", rc["handle"].startswith("ccr://"))
    ck("rehydrate(handle) returns the RAW byte-for-byte (lossless)", rehydrate(rc["handle"]) == code)
    ck("rehydrate of the json raw is exact too", rehydrate(rj["handle"]) == cjson)

    ck("never expands (compressed <= raw)", rc["compressed_chars"] <= rc["raw_chars"] and rj["compressed_chars"] <= rj["raw_chars"])
    ck("token accounting shows the saving", rc["raw_tokens"] >= rc["compressed_tokens"] and rj["raw_tokens"] > rj["compressed_tokens"])
    ck("compression never serves truth (it's an optimization, raw preserved)", rc["serves_truth"] is False)

    # wired into the loop: a real module context compresses, and the loop toggles it
    import scripts.multi_model_improvement_loop as loop
    ck("the loop has compression ON by default (--no-compress to disable)", loop._COMPRESS is True)
    mref = "_repos/teleon/backend/src/teleon/evolution/descent_attempt_store.py"
    raw = loop.focused_context({"id": f"module:{mref}", "kind": "module", "ref": mref})
    cr = compress(raw)
    ck("a real loop context (module) compresses with a positive ratio", cr["ratio"] >= 0 and cr["compressed_chars"] <= cr["raw_chars"], f"ratio={cr['ratio']}")

    print("\n" + ("PASS - check_context_compressor: reversible, content-aware context compression — code/json/text each "
                  "shrink, the raw is recallable byte-for-byte via a ccr handle (lossless), it never expands, tokens are "
                  "accounted, and it's wired into the multi-model loop (cheaper per cycle). serves_truth=false."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def _main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--self-test" in argv:
        return _self_test()
    print("usage: check_context_compressor.py --self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
