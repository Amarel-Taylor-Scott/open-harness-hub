"""src.teleon.synthesis.codeblock_loop — the CODEBLOCK fill loop: fill a reusable code template's variables, VALIDATE
the filled block (syntax + the declared input/output contract), and on failure RETRY with feedback (bounded).

A *codeblock* = a reusable code template with declared variables / inputs / outputs (the code-text sibling of the DAG
SLOT templates in `templates.py`: those fill a DAG slot with a component; this fills a code template's `{{variable}}`
slots into a runnable block). The loop mirrors the cheapest-first descent + the intent_to_dag discipline (the LLM
PROPOSES the fills; the validator + the declared contract DISPOSE — LLM proposes, scaffold/tests govern):

  1. fill      LLM when a lane is available (llm_port.ProviderLLM via select_llm/as_callable); honest-unavailable
               with no lane -> DETERMINISTIC fill from the caller's provided values (never fabricated). Provided
               values are authoritative; the LLM/defaults only fill the gaps.
  2. validate  the filled text: no unfilled `{{slot}}` remains, it PARSES (python syntax), and the declared OUTPUTS
               are defined + declared INPUTS are referenced.
  3. retry     on failure, build feedback from the verdict and re-fill — BOUNDED by max_attempts. Recovery for the
               deterministic path comes from the codeblock's declared `defaults`; for the LLM path, the feedback is
               fed back into the next prompt.

LOSSLESS: the template is preserved unmutated and EVERY attempt (incl. the rejected ones, with their feedback) is kept
in `history` (and `persist_history` sinks it to JSONL). serves_truth=false (an LLM is never a source of truth; this
emits a CANDIDATE runnable block — verify_buildable_dag + the governance gates still run before anything executes).

  block = Codeblock("greet_fn", "def {{fn}}(payload):\\n    result = {{expr}}\\n    return result",
                    variables=["fn", "expr"], inputs=["payload"], outputs=["result"], defaults={"expr": "payload"})
  res   = fill_codeblock("greet a user", block, values={"fn": "greet", "expr": "f\\"hi {payload}\\""})
  res["filled"], res["block"], res["history"]        # verdict, runnable code, every attempt (lossless)

  compose_codeblock(intent, block_spec, values)      # the compose-facing entry point (registry.compose can call this)

  PYTHONPATH=. python3 src/teleon/synthesis/codeblock_loop.py --self-test
"""
from __future__ import annotations

import ast
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.teleon.llm_port import CallableLLM, as_callable, select_llm  # noqa: E402

DEFAULT_MAX_ATTEMPTS = 3                                   # bounded retry: render->validate->feedback at most this many times
#: codeblock slot syntax is mustache-style `{{name}}` so a template body may freely contain Python's single braces
#: (f-strings, dict/set literals) without colliding with the fill machinery.
_SLOT = re.compile(r"\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}\}")


# ── the codeblock (a reusable code template + its declared contract) ──────────────────────────────────────────────
@dataclass
class Codeblock:
    block_id: str
    template: str
    variables: list = field(default_factory=list)         # declared fill slots (auto-derived from the body when empty)
    inputs: list = field(default_factory=list)             # identifiers the rendered code must REFERENCE (the contract)
    outputs: list = field(default_factory=list)            # identifiers the rendered code must DEFINE  (the contract)
    defaults: dict = field(default_factory=dict)           # safe deterministic fallbacks per variable (the repair source)
    language: str = "python"

    def declared_variables(self) -> list:
        return list(self.variables) if self.variables else template_variables(self.template)


def codeblock_from_dict(d: dict) -> Codeblock:
    """Build a Codeblock from a plain dict (so a composer can hand JSON). Tolerant of id/body aliases."""
    return Codeblock(
        block_id=d.get("block_id") or d.get("id") or "codeblock",
        template=d.get("template") or d.get("body") or "",
        variables=list(d.get("variables", [])), inputs=list(d.get("inputs", [])),
        outputs=list(d.get("outputs", [])), defaults=dict(d.get("defaults", {})),
        language=d.get("language", "python"),
    )


def template_variables(template: str) -> list:
    """The ordered, de-duplicated `{{slot}}` names in a template body."""
    seen, out = set(), []
    for m in _SLOT.finditer(template or ""):
        v = m.group(1)
        if v not in seen:
            seen.add(v)
            out.append(v)
    return out


def render(template: str, fills: dict) -> str:
    """Substitute each `{{slot}}` with str(fills[slot]); an absent/None fill leaves the slot intact so validation
    flags it honestly (rather than silently emitting a hole)."""
    def _sub(m: "re.Match") -> str:
        val = fills.get(m.group(1))
        return m.group(0) if val is None else str(val)
    return _SLOT.sub(_sub, template)


# ── validation (the declared contract: nothing unfilled · it parses · outputs defined · inputs referenced) ────────
def _names(tree: ast.AST) -> tuple:
    """(defined, referenced) identifier names in an AST: defined = def/class names + assignment (Store) targets;
    referenced = names used in a Load context (incl. inside f-strings)."""
    defined, referenced = set(), set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            defined.add(node.name)
        elif isinstance(node, ast.Name):
            (defined if isinstance(node.ctx, ast.Store) else referenced).add(node.id)
    return defined, referenced


def validate(text: str, block: Codeblock) -> dict:
    """Verdict for a filled block: unfilled slots, python-syntax, and the declared input/output contract.
    For a non-python language only the unfilled-slot check is enforced (the contract isn't statically checkable here)."""
    unfilled = template_variables(text)                   # any `{{slot}}` still present == not filled
    syntax_ok, syntax_err, missing_out, missing_in = True, None, [], []
    if block.language == "python":
        try:
            defined, referenced = _names(ast.parse(text))
        except SyntaxError as e:                           # syntax dominates; don't double-report the contract on garbage
            syntax_ok, syntax_err = False, f"{e.msg} (line {e.lineno})"
        else:
            missing_out = [o for o in block.outputs if o not in defined]
            missing_in = [i for i in block.inputs if i not in referenced]
    errors = []
    if unfilled:
        errors.append(f"unfilled variables: {unfilled}")
    if not syntax_ok:
        errors.append(f"syntax error: {syntax_err}")
    if missing_out:
        errors.append(f"declared outputs not defined: {missing_out}")
    if missing_in:
        errors.append(f"declared inputs not referenced: {missing_in}")
    ok = not unfilled and syntax_ok and not missing_out and not missing_in
    return {"ok": ok, "unfilled": unfilled, "syntax_ok": syntax_ok, "syntax_error": syntax_err,
            "missing_outputs": missing_out, "missing_inputs": missing_in, "errors": errors, "serves_truth": False}


# ── the fill sources (deterministic from provided values · LLM proposal; both honest) ─────────────────────────────
def _deterministic_fill(block: Codeblock, values: dict, feedback: dict) -> dict:
    """Fill from the caller's provided values. Repair: for any variable the validator flagged UNFILLED, supply the
    block's declared default (so the caller's values are preferred and a default is only a post-failure fallback)."""
    fills = dict(values)
    for var in feedback.get("unfilled", []):
        if var not in fills and var in block.defaults:
            fills[var] = block.defaults[var]
    return fills


def _fill_prompt(task: str, block: Codeblock, need: list, feedback: dict) -> str:
    lines = [f"Task: {task}",
             f"Fill these variables for a {block.language} code template: {need}.",
             f"Template:\n{block.template}",
             "Return one `name = value` per line; the values must make the rendered code parse and satisfy "
             f"outputs={block.outputs} inputs={block.inputs}."]
    if feedback.get("text"):
        lines.append(f"RETRY: the previous attempt FAILED — fix it. Feedback: {feedback['text']}")
    return "\n".join(lines)


def _parse_fills(text: str, variables: list) -> dict:
    """Parse `name = value` / `name: value` lines (tolerating code-fence backticks) into a fills dict for known vars."""
    out: dict = {}
    for raw in (text or "").splitlines():
        line = raw.strip().strip("`").strip()
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*[:=]\s*(.*)$", line)
        if m and m.group(1) in variables:
            out[m.group(1)] = m.group(2).strip()
    return out


def _llm_fill(call, task: str, block: Codeblock, values: dict, feedback: dict) -> dict:
    """The LLM proposes fills for the gap variables; provided values stay authoritative; declared defaults backstop
    anything STILL unfilled (so the loop degrades, never fabricates)."""
    variables = block.declared_variables()
    need = [v for v in variables if v not in values]
    try:
        text = call(_fill_prompt(task, block, need, feedback)) or ""
    except Exception:  # noqa: BLE001
        text = ""
    fills = {**_parse_fills(text, variables), **values}
    for v in variables:
        if v not in fills and v in block.defaults:
            fills[v] = block.defaults[v]
    return fills


def _resolve_llm(llm):
    """Resolve the fill LLM to a (prompt)->str callable, or None (honest-unavailable -> deterministic fill).
    Accepts an LLMPort / a (prompt)->str callable / a model-or-lane name / 'auto' / None."""
    if llm is None or llm == "auto":
        return as_callable(select_llm("auto"))
    return as_callable(llm)


# ── the loop ──────────────────────────────────────────────────────────────────────────────────────────────────────
@dataclass
class FillAttempt:
    attempt: int
    source: str
    fills: dict
    block_text: str
    verdict: dict
    feedback: str = ""

    def to_dict(self) -> dict:
        return {"attempt": self.attempt, "source": self.source, "fills": self.fills, "block_text": self.block_text,
                "ok": self.verdict["ok"], "errors": self.verdict["errors"], "feedback": self.feedback}


def _feedback(verdict: dict) -> str:
    return "" if verdict["ok"] else ("; ".join(verdict["errors"]) or "invalid fill")


def fill_codeblock(task: str, block: Codeblock, values: dict | None = None, *, llm="auto",
                   max_attempts: int = DEFAULT_MAX_ATTEMPTS) -> dict:
    """Fill -> validate -> (on failure) feedback -> retry, BOUNDED by max_attempts (1 initial + retries). Returns the
    verdict + the runnable block (only when valid — honest) + the LOSSLESS history of every attempt. Never raises."""
    values = dict(values or {})
    call = _resolve_llm(llm)
    llm_used = call is not None
    source = "llm" if llm_used else "deterministic"
    history: list[FillAttempt] = []
    feedback: dict = {}
    for i in range(1, max(1, max_attempts) + 1):
        fills = _llm_fill(call, task, block, values, feedback) if llm_used else _deterministic_fill(block, values, feedback)
        text = render(block.template, fills)
        verdict = validate(text, block)
        history.append(FillAttempt(i, source, dict(fills), text, verdict, _feedback(verdict)))
        if verdict["ok"]:
            return _result(task, block, history, True, llm_used)
        feedback = {"unfilled": verdict["unfilled"], "errors": verdict["errors"], "text": _feedback(verdict)}
    return _result(task, block, history, False, llm_used)


def _result(task: str, block: Codeblock, history: list, ok: bool, llm_used: bool) -> dict:
    last = history[-1]
    return {
        "task": task, "block_id": block.block_id, "language": block.language,
        "filled": ok,
        "block": last.block_text if ok else None,         # the runnable code, only when valid (honest)
        "final_text": last.block_text,                    # always present (incl. the last rejected) for inspection
        "attempts": len(history), "llm_used": llm_used,
        "verdict": last.verdict,
        "template": block.template,                       # LOSSLESS: the template is preserved unmutated
        "inputs": list(block.inputs), "outputs": list(block.outputs),
        "history": [a.to_dict() for a in history],        # LOSSLESS: every attempt incl. rejected, with its feedback
        "rejected": [a.to_dict() for a in history if not a.verdict["ok"]],
        "reason": None if ok else f"no valid fill within {len(history)} attempt(s)",
        "serves_truth": False,
    }


def persist_history(result: dict, path) -> str:
    """LOSSLESS sink: the template + every attempt (incl. rejected) as JSONL (the caller owns the path; temp/local).
    Mirrors synthesis_trace's plain-JSONL persistence. serves_truth=false."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        f.write(json.dumps({"record": "template", "block_id": result["block_id"], "template": result["template"]}) + "\n")
        for a in result["history"]:
            f.write(json.dumps({"record": "attempt", "block_id": result["block_id"], **a}) + "\n")
    return str(p)


# ── compose wiring (the compose-facing entry point; registry.compose can import + call this, no edit to compose.py) ─
def compose_codeblock(intent: str, block_spec, values: dict | None = None, *, llm="auto",
                      max_attempts: int = DEFAULT_MAX_ATTEMPTS) -> dict:
    """Compose a codeblock as a runnable stage: hand an intent + a codeblock spec (a Codeblock or a plain dict) +
    provided values; this fills+validates into a CANDIDATE block (shaped like registry.compose's candidate outputs).
    The verification + governance gates still run before anything executes — candidate, not promoted. serves_truth=false."""
    block = block_spec if isinstance(block_spec, Codeblock) else codeblock_from_dict(block_spec)
    res = fill_codeblock(intent, block, values, llm=llm, max_attempts=max_attempts)
    return {"intent": intent, "block_id": block.block_id, "candidate_codeblock": True,
            "filled": res["filled"], "block": res["block"], "attempts": res["attempts"],
            "result": res, "serves_truth": False}


__all__ = ["Codeblock", "codeblock_from_dict", "template_variables", "render", "validate",
           "fill_codeblock", "persist_history", "compose_codeblock", "DEFAULT_MAX_ATTEMPTS"]


# ── self-test (deterministic · offline · temp paths only) ─────────────────────────────────────────────────────────
def self_test() -> int:
    import tempfile

    # A codeblock = a reusable code template with declared variables / inputs / outputs (+ a safe default for `expr`).
    block = Codeblock(
        block_id="greet_fn",
        template='def {{fn}}(payload):\n    result = {{expr}}\n    return result',
        variables=["fn", "expr"],
        inputs=["payload"],          # the rendered body must REFERENCE payload
        outputs=["result"],          # the rendered code must DEFINE result
        defaults={"expr": "payload"},  # deterministic repair when `expr` isn't provided
    )
    det = select_llm("deterministic")  # available()==False -> the loop takes the deterministic fill path (offline)

    # (1) fills from PROVIDED VALUES, validates first try (deterministic path; no LLM).
    r1 = fill_codeblock("greet a user", block,
                        values={"fn": "greet", "expr": 'f"hi {payload}"'}, llm=det)
    assert r1["filled"] is True, r1["verdict"]
    assert r1["attempts"] == 1 and r1["llm_used"] is False, r1
    assert r1["verdict"]["syntax_ok"] and not r1["verdict"]["missing_outputs"] and not r1["verdict"]["missing_inputs"]
    assert r1["block"] and "{{" not in r1["block"] and "greet" in r1["block"]
    compile(r1["block"], "<greet>", "exec")            # the emitted block is real, runnable python

    # (2a) BOUNDED RETRY on a bad fill RECOVERS — deterministic path: incomplete values -> default repair on retry.
    r2 = fill_codeblock("greet (incomplete values)", block, values={"fn": "greet"}, llm=det)
    assert r2["filled"] is True and r2["attempts"] == 2, r2
    assert r2["history"][0]["ok"] is False and "expr" in str(r2["history"][0]["errors"]), "first attempt rejected on `expr`"
    assert r2["history"][1]["fills"].get("expr") == "payload", "the declared default repaired the retry"
    compile(r2["block"], "<greet2>", "exec")

    # (2b) BOUNDED RETRY on a bad fill RECOVERS — LLM path: a bad fill, then the LLM fixes once it SEES the feedback.
    calls = {"n": 0}
    def _double(prompt: str) -> str:
        calls["n"] += 1
        if "FAILED" in prompt:                          # the feedback reached the filler -> emit a valid fill
            return 'fn = greet\nexpr = f"hi {payload}"'
        return "fn = greet\nexpr = return payload"      # first try: `return payload` as an expr -> syntax error
    r3 = fill_codeblock("greet via llm", block, values={}, llm=CallableLLM(_double, name="double"), max_attempts=3)
    assert r3["llm_used"] is True and r3["filled"] is True and r3["attempts"] == 2, (r3["attempts"], r3["verdict"])
    assert calls["n"] == 2, "the loop must RE-CALL the LLM with feedback after the bad fill"
    assert r3["history"][0]["ok"] is False and r3["history"][0]["feedback"], "the rejected first fill + its feedback are kept"
    compile(r3["block"], "<greet3>", "exec")

    # (3) BOUNDED failure is honest (never exceeds max_attempts; no fabricated block).
    r4 = fill_codeblock("never valid", block, values={},
                        llm=CallableLLM(lambda _p: "fn = greet\nexpr = def"), max_attempts=2)
    assert r4["filled"] is False and r4["attempts"] == 2, r4
    assert r4["block"] is None and r4["reason"] and len(r4["rejected"]) == 2, r4

    # (4) LOSSLESS — the template is preserved unmutated and every attempt (incl. rejected) survives, durably (temp JSONL).
    assert r2["template"] == block.template, "the template must be preserved unmutated (lossless)"
    with tempfile.TemporaryDirectory() as td:
        path = persist_history(r2, Path(td) / "codeblock_history.jsonl")
        rows = [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines()]
        assert rows[0]["record"] == "template" and rows[0]["template"] == block.template
        attempts = [r for r in rows if r["record"] == "attempt"]
        assert len(attempts) == r2["attempts"] == 2 and any(a["ok"] is False for a in attempts), "rejected attempt persisted"

    # (5) compose wiring — a plain dict spec composes into a CANDIDATE runnable block.
    spec = {"block_id": "sum_fn", "template": "def {{fn}}(a, b):\n    total = a + b\n    return total",
            "variables": ["fn"], "inputs": ["a"], "outputs": ["total"]}
    comp = compose_codeblock("add two numbers", spec, values={"fn": "add"}, llm=det)
    assert comp["candidate_codeblock"] is True and comp["filled"] is True and comp["serves_truth"] is False
    compile(comp["block"], "<sum>", "exec")

    # Governance: every surfaced result serves_truth=false (an LLM/fill is never a source of truth).
    assert all(r["serves_truth"] is False for r in (r1, r2, r3, r4, comp))

    print(f"codeblock_loop self-test: OK (provided-values fill+validate [1 attempt] · bounded retry recovers "
          f"[deterministic {r2['attempts']} / llm {r3['attempts']} attempts] · bounded failure honest "
          f"[{r4['attempts']} attempts, no block] · lossless template+history persisted · "
          f"compose_codeblock candidate · serves_truth=false)")
    return 0


def main(argv: list) -> int:
    if "--self-test" in argv:
        return self_test()
    print("usage: codeblock_loop --self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
