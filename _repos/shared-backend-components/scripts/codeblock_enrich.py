#!/usr/bin/env python3
"""scripts.codeblock_enrich — give CODE records a templated, customizable CODEBLOCK (token-efficient reuse).

The owner's insight: reuse should be FILLING a template, not regenerating code. For code-shaped records
(tool/component/function/method/class/skill/...), this attaches a CODEBLOCK = a parameterized template with declared
{{variables}}, inputs, and outputs, plus a DETERMINISTIC customize(params) that fills the slots from a small dict.
Reuse = a few tokens of params (deterministic) instead of a full LLM regeneration; only genuinely-novel slots are
flagged for a bounded LLM edit. Generalized: when no specific template fits, emit a simple generic function/class
skeleton. Lossless: writes data/dev-intel/record_codeblocks.jsonl. serves_truth=false (a template, not a truth claim).

  --self-test | --run [--limit N]
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource
RECORDS = _resource("data") / "dev-intel" / "registry_records.jsonl"
OUT = _resource("data") / "dev-intel" / "record_codeblocks.jsonl"
STATE = _resource("data") / "dev-intel" / "codeblock_cursor.json"
CODE_TYPES = {"tool", "component", "function", "method", "class", "skill", "plugin", "deterministic_tool", "connector"}

#: template kind -> (template, variables, inputs, outputs). {{var}} slots are filled by customize().
TEMPLATES = {
    "function": ("def {{name}}({{inputs}}):\n    \"\"\"{{doc}}\"\"\"\n    {{body}}\n    return {{output}}",
                 ["name", "inputs", "doc", "body", "output"], ["inputs"], ["output"]),
    "class": ("class {{name}}:\n    \"\"\"{{doc}}\"\"\"\n    def __init__(self, {{inputs}}):\n        {{init}}\n"
              "    def run(self):\n        {{body}}\n        return {{output}}",
              ["name", "doc", "inputs", "init", "body", "output"], ["inputs"], ["output"]),
    "tool": ("def {{name}}_tool(params: dict) -> dict:\n    \"\"\"{{doc}} (wraps {{ref}}).\"\"\"\n    {{body}}\n"
             "    return {{output}}", ["name", "doc", "ref", "body", "output"], ["params"], ["output"]),
}


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9_]+", "_", (s or "comp").lower()).strip("_")[:40] or "comp"


def template_for(rec: dict) -> dict:
    ot = rec.get("object_type", "")
    kind = "function" if ot in ("function", "method") else ("class" if ot == "class" else "tool")
    tmpl, variables, inputs, outputs = TEMPLATES[kind]
    name = _slug(rec.get("name", ""))
    prefill = {
        "name": name,
        "doc": f"{rec.get('name', '')} — generalized reusable {ot or 'component'}",
        "ref": rec.get("source", {}).get("url", ""),
        "inputs": "params" if kind == "tool" else "*args, **kwargs",
        "init": "pass", "params": "params",
        "body": "# customize(params) fills this; only novel logic needs a bounded LLM edit",
        "output": "{}",
    }
    return {"language": "python", "kind": kind, "template": tmpl, "variables": variables,
            "inputs": inputs, "outputs": outputs, "prefill": {k: prefill[k] for k in variables if k in prefill}}


def customize(cb: dict, params: dict | None = None) -> tuple[str, list[str]]:
    """Deterministic fill: substitute {{var}} from prefill∪params. Returns (code, missing_vars_needing_llm)."""
    vals = {**cb.get("prefill", {}), **(params or {})}
    code = cb["template"]
    missing = []
    for v in cb["variables"]:
        if v in vals:
            code = code.replace("{{" + v + "}}", str(vals[v]))
        else:
            missing.append(v)
    return code, missing


def _load_state() -> dict:
    if STATE.exists():
        try:
            return json.loads(STATE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {"cursor": 0, "codeblocks": 0}


def _save_state(s: dict) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(s, indent=2), encoding="utf-8")


def run(limit: int = 0) -> dict:
    if not RECORDS.exists():
        return {"new": 0}
    recs = [json.loads(ln) for ln in RECORDS.read_text(encoding="utf-8").splitlines() if ln.strip()]
    s = _load_state()
    new = recs[s["cursor"]:]
    if limit:
        new = new[:limit]
    n = 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("a", encoding="utf-8") as fh:
        for rec in new:
            if rec.get("object_type") not in CODE_TYPES or rec.get("kind") != "record" or not rec.get("name"):
                continue
            cb = template_for(rec)
            rendered, missing = customize(cb, {})
            fh.write(json.dumps({"record_id": rec.get("record_id"), "codeblock": cb, "rendered_example": rendered,
                                 "needs_llm_fill": missing, "serves_truth": False,
                                 "at": time.strftime("%Y-%m-%dT%H:%M:%S")}) + "\n")
            n += 1
    s.update(cursor=s["cursor"] + len(new), codeblocks=s["codeblocks"] + n)
    _save_state(s)
    return {"new": len(new), "codeblocks_added": n, "total": s["codeblocks"]}


def self_test() -> int:
    cb = template_for({"object_type": "function", "name": "Resize Image Util", "source": {"url": "u"}})
    assert set(cb["variables"]) >= {"name", "inputs", "output"} and cb["inputs"] and cb["outputs"], "declared vars/io"
    code, missing = customize(cb, {"body": "img = open(path); return img.resize(size)", "output": "img"})
    assert "def resize_image_util" in code and "img.resize" in code, f"deterministic fill: {code}"
    assert "{{" not in code or missing, "either fully filled or missing flagged"
    # token efficiency: a tiny params dict customizes vs regenerating — only novel slots need the LLM
    cb2 = template_for({"object_type": "tool", "name": "github search", "source": {"url": "g"}})
    code2, miss2 = customize(cb2, {})   # prefill alone yields a runnable skeleton
    assert "def github_search_tool(params: dict)" in code2 and "{{" not in code2, f"tool skeleton: {code2}"
    print("codeblock_enrich self-test: OK (templated codeblock, declared vars/inputs/outputs, deterministic customize)")
    return 0


def main(argv: list[str]) -> int:
    if "--self-test" in argv:
        return self_test()
    if "--run" in argv:
        lim = int(argv[argv.index("--limit") + 1]) if "--limit" in argv else 0
        print(json.dumps(run(lim), indent=2)); return 0
    print("usage: codeblock_enrich.py --self-test | --run [--limit N]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
