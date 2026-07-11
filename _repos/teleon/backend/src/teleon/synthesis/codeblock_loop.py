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

  PYTHONPATH=. python3 _repos/teleon/backend/src/teleon/synthesis/codeblock_loop.py --self-test
"""
from __future__ import annotations

import ast
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

py_const_src_teleon_synthesis_codeblock_loop__REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[3])
if str(py_const_src_teleon_synthesis_codeblock_loop__REPO) not in sys.path:
    sys.path.insert(0, str(py_const_src_teleon_synthesis_codeblock_loop__REPO))

from src.teleon.llm_port import CallableLLM, as_callable, select_llm  # noqa: E402

py_const_src_teleon_synthesis_codeblock_loop__DEFAULT_MAX_ATTEMPTS = 3                                   # bounded retry: render->validate->feedback at most this many times
#: codeblock slot syntax is mustache-style `{{name}}` so a template body may freely contain Python's single braces
#: (f-strings, dict/set literals) without colliding with the fill machinery.
py_var_src_teleon_synthesis_codeblock_loop___SLOT = re.compile(r"\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}\}")


# ── the codeblock (a reusable code template + its declared contract) ──────────────────────────────────────────────
@dataclass
class py_class_src_teleon_synthesis_codeblock_loop__Codeblock:
    block_id: str
    template: str
    variables: list = field(default_factory=list)         # declared fill slots (auto-derived from the body when empty)
    inputs: list = field(default_factory=list)             # identifiers the rendered code must REFERENCE (the contract)
    outputs: list = field(default_factory=list)            # identifiers the rendered code must DEFINE  (the contract)
    defaults: dict = field(default_factory=dict)           # safe deterministic fallbacks per variable (the repair source)
    language: str = "python"

    def declared_variables(self) -> list:
        return list(self.variables) if self.variables else py_function_src_teleon_synthesis_codeblock_loop__template_variables(self.template)


def py_function_src_teleon_synthesis_codeblock_loop__codeblock_from_dict(py_arg_src_teleon_synthesis_codeblock_loop__codeblock_from_dict__d: dict) -> py_class_src_teleon_synthesis_codeblock_loop__Codeblock:
    """Build a Codeblock from a plain dict (so a composer can hand JSON). Tolerant of id/body aliases."""
    return py_class_src_teleon_synthesis_codeblock_loop__Codeblock(
        block_id=py_arg_src_teleon_synthesis_codeblock_loop__codeblock_from_dict__d.get("block_id") or py_arg_src_teleon_synthesis_codeblock_loop__codeblock_from_dict__d.get("id") or "codeblock",
        template=py_arg_src_teleon_synthesis_codeblock_loop__codeblock_from_dict__d.get("template") or py_arg_src_teleon_synthesis_codeblock_loop__codeblock_from_dict__d.get("body") or "",
        variables=list(py_arg_src_teleon_synthesis_codeblock_loop__codeblock_from_dict__d.get("variables", [])), inputs=list(py_arg_src_teleon_synthesis_codeblock_loop__codeblock_from_dict__d.get("inputs", [])),
        outputs=list(py_arg_src_teleon_synthesis_codeblock_loop__codeblock_from_dict__d.get("outputs", [])), defaults=dict(py_arg_src_teleon_synthesis_codeblock_loop__codeblock_from_dict__d.get("defaults", {})),
        language=py_arg_src_teleon_synthesis_codeblock_loop__codeblock_from_dict__d.get("language", "python"),
    )


def py_function_src_teleon_synthesis_codeblock_loop__template_variables(py_arg_src_teleon_synthesis_codeblock_loop__template_variables__template: str) -> list:
    """The ordered, de-duplicated `{{slot}}` names in a template body."""
    py_local_src_teleon_synthesis_codeblock_loop__template_variables__seen, py_local_src_teleon_synthesis_codeblock_loop__template_variables__out = set(), []
    for py_local_src_teleon_synthesis_codeblock_loop__template_variables__m in py_var_src_teleon_synthesis_codeblock_loop___SLOT.finditer(py_arg_src_teleon_synthesis_codeblock_loop__template_variables__template or ""):
        py_local_src_teleon_synthesis_codeblock_loop__template_variables__v = py_local_src_teleon_synthesis_codeblock_loop__template_variables__m.group(1)
        if py_local_src_teleon_synthesis_codeblock_loop__template_variables__v not in py_local_src_teleon_synthesis_codeblock_loop__template_variables__seen:
            py_local_src_teleon_synthesis_codeblock_loop__template_variables__seen.add(py_local_src_teleon_synthesis_codeblock_loop__template_variables__v)
            py_local_src_teleon_synthesis_codeblock_loop__template_variables__out.append(py_local_src_teleon_synthesis_codeblock_loop__template_variables__v)
    return py_local_src_teleon_synthesis_codeblock_loop__template_variables__out


def py_function_src_teleon_synthesis_codeblock_loop__render(py_arg_src_teleon_synthesis_codeblock_loop__render__template: str, py_arg_src_teleon_synthesis_codeblock_loop__render__fills: dict) -> str:
    """Substitute each `{{slot}}` with str(fills[slot]); an absent/None fill leaves the slot intact so validation
    flags it honestly (rather than silently emitting a hole)."""
    def _sub(py_arg_src_teleon_synthesis_codeblock_loop__render__sub__m: "re.Match") -> str:
        py_local_src_teleon_synthesis_codeblock_loop__render__sub__val = py_arg_src_teleon_synthesis_codeblock_loop__render__fills.get(py_arg_src_teleon_synthesis_codeblock_loop__render__sub__m.group(1))
        return py_arg_src_teleon_synthesis_codeblock_loop__render__sub__m.group(0) if py_local_src_teleon_synthesis_codeblock_loop__render__sub__val is None else str(py_local_src_teleon_synthesis_codeblock_loop__render__sub__val)
    return py_var_src_teleon_synthesis_codeblock_loop___SLOT.sub(_sub, py_arg_src_teleon_synthesis_codeblock_loop__render__template)


# ── validation (the declared contract: nothing unfilled · it parses · outputs defined · inputs referenced) ────────
def py_function_src_teleon_synthesis_codeblock_loop___names(py_arg_src_teleon_synthesis_codeblock_loop__names__tree: ast.AST) -> tuple:
    """(defined, referenced) identifier names in an AST: defined = def/class names + assignment (Store) targets;
    referenced = names used in a Load context (incl. inside f-strings)."""
    py_local_src_teleon_synthesis_codeblock_loop__names__defined, py_local_src_teleon_synthesis_codeblock_loop__names__referenced = set(), set()
    for py_local_src_teleon_synthesis_codeblock_loop__names__node in ast.walk(py_arg_src_teleon_synthesis_codeblock_loop__names__tree):
        if isinstance(py_local_src_teleon_synthesis_codeblock_loop__names__node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            py_local_src_teleon_synthesis_codeblock_loop__names__defined.add(py_local_src_teleon_synthesis_codeblock_loop__names__node.name)
        elif isinstance(py_local_src_teleon_synthesis_codeblock_loop__names__node, ast.Name):
            (py_local_src_teleon_synthesis_codeblock_loop__names__defined if isinstance(py_local_src_teleon_synthesis_codeblock_loop__names__node.ctx, ast.Store) else py_local_src_teleon_synthesis_codeblock_loop__names__referenced).add(py_local_src_teleon_synthesis_codeblock_loop__names__node.id)
    return py_local_src_teleon_synthesis_codeblock_loop__names__defined, py_local_src_teleon_synthesis_codeblock_loop__names__referenced


def py_function_src_teleon_synthesis_codeblock_loop__validate(py_arg_src_teleon_synthesis_codeblock_loop__validate__text: str, py_arg_src_teleon_synthesis_codeblock_loop__validate__block: py_class_src_teleon_synthesis_codeblock_loop__Codeblock) -> dict:
    """Verdict for a filled block: unfilled slots, python-syntax, and the declared input/output contract.
    For a non-python language only the unfilled-slot check is enforced (the contract isn't statically checkable here)."""
    py_local_src_teleon_synthesis_codeblock_loop__validate__unfilled = py_function_src_teleon_synthesis_codeblock_loop__template_variables(py_arg_src_teleon_synthesis_codeblock_loop__validate__text)                   # any `{{slot}}` still present == not filled
    py_local_src_teleon_synthesis_codeblock_loop__validate__syntax_ok, py_local_src_teleon_synthesis_codeblock_loop__validate__syntax_err, py_local_src_teleon_synthesis_codeblock_loop__validate__missing_out, py_local_src_teleon_synthesis_codeblock_loop__validate__missing_in = True, None, [], []
    if py_arg_src_teleon_synthesis_codeblock_loop__validate__block.language == "python":
        try:
            py_local_src_teleon_synthesis_codeblock_loop__validate__defined, py_local_src_teleon_synthesis_codeblock_loop__validate__referenced = py_function_src_teleon_synthesis_codeblock_loop___names(ast.parse(py_arg_src_teleon_synthesis_codeblock_loop__validate__text))
        except SyntaxError as py_local_src_teleon_synthesis_codeblock_loop__validate__e:                           # syntax dominates; don't double-report the contract on garbage
            py_local_src_teleon_synthesis_codeblock_loop__validate__syntax_ok, py_local_src_teleon_synthesis_codeblock_loop__validate__syntax_err = False, f"{py_local_src_teleon_synthesis_codeblock_loop__validate__e.msg} (line {py_local_src_teleon_synthesis_codeblock_loop__validate__e.lineno})"
        else:
            py_local_src_teleon_synthesis_codeblock_loop__validate__missing_out = [o for o in py_arg_src_teleon_synthesis_codeblock_loop__validate__block.outputs if o not in py_local_src_teleon_synthesis_codeblock_loop__validate__defined]
            py_local_src_teleon_synthesis_codeblock_loop__validate__missing_in = [i for i in py_arg_src_teleon_synthesis_codeblock_loop__validate__block.inputs if i not in py_local_src_teleon_synthesis_codeblock_loop__validate__referenced]
    py_local_src_teleon_synthesis_codeblock_loop__validate__errors = []
    if py_local_src_teleon_synthesis_codeblock_loop__validate__unfilled:
        py_local_src_teleon_synthesis_codeblock_loop__validate__errors.append(f"unfilled variables: {py_local_src_teleon_synthesis_codeblock_loop__validate__unfilled}")
    if not py_local_src_teleon_synthesis_codeblock_loop__validate__syntax_ok:
        py_local_src_teleon_synthesis_codeblock_loop__validate__errors.append(f"syntax error: {py_local_src_teleon_synthesis_codeblock_loop__validate__syntax_err}")
    if py_local_src_teleon_synthesis_codeblock_loop__validate__missing_out:
        py_local_src_teleon_synthesis_codeblock_loop__validate__errors.append(f"declared outputs not defined: {py_local_src_teleon_synthesis_codeblock_loop__validate__missing_out}")
    if py_local_src_teleon_synthesis_codeblock_loop__validate__missing_in:
        py_local_src_teleon_synthesis_codeblock_loop__validate__errors.append(f"declared inputs not referenced: {py_local_src_teleon_synthesis_codeblock_loop__validate__missing_in}")
    py_local_src_teleon_synthesis_codeblock_loop__validate__ok = not py_local_src_teleon_synthesis_codeblock_loop__validate__unfilled and py_local_src_teleon_synthesis_codeblock_loop__validate__syntax_ok and not py_local_src_teleon_synthesis_codeblock_loop__validate__missing_out and not py_local_src_teleon_synthesis_codeblock_loop__validate__missing_in
    return {"ok": py_local_src_teleon_synthesis_codeblock_loop__validate__ok, "unfilled": py_local_src_teleon_synthesis_codeblock_loop__validate__unfilled, "syntax_ok": py_local_src_teleon_synthesis_codeblock_loop__validate__syntax_ok, "syntax_error": py_local_src_teleon_synthesis_codeblock_loop__validate__syntax_err,
            "missing_outputs": py_local_src_teleon_synthesis_codeblock_loop__validate__missing_out, "missing_inputs": py_local_src_teleon_synthesis_codeblock_loop__validate__missing_in, "errors": py_local_src_teleon_synthesis_codeblock_loop__validate__errors, "serves_truth": False}


# ── the fill sources (deterministic from provided values · LLM proposal; both honest) ─────────────────────────────
def py_function_src_teleon_synthesis_codeblock_loop___deterministic_fill(py_arg_src_teleon_synthesis_codeblock_loop__deterministic_fill__block: py_class_src_teleon_synthesis_codeblock_loop__Codeblock, py_arg_src_teleon_synthesis_codeblock_loop__deterministic_fill__values: dict, py_arg_src_teleon_synthesis_codeblock_loop__deterministic_fill__feedback: dict) -> dict:
    """Fill from the caller's provided values. Repair: for any variable the validator flagged UNFILLED, supply the
    block's declared default (so the caller's values are preferred and a default is only a post-failure fallback)."""
    py_local_src_teleon_synthesis_codeblock_loop__deterministic_fill__fills = dict(py_arg_src_teleon_synthesis_codeblock_loop__deterministic_fill__values)
    for py_local_src_teleon_synthesis_codeblock_loop__deterministic_fill__var in py_arg_src_teleon_synthesis_codeblock_loop__deterministic_fill__feedback.get("unfilled", []):
        if py_local_src_teleon_synthesis_codeblock_loop__deterministic_fill__var not in py_local_src_teleon_synthesis_codeblock_loop__deterministic_fill__fills and py_local_src_teleon_synthesis_codeblock_loop__deterministic_fill__var in py_arg_src_teleon_synthesis_codeblock_loop__deterministic_fill__block.defaults:
            py_local_src_teleon_synthesis_codeblock_loop__deterministic_fill__fills[py_local_src_teleon_synthesis_codeblock_loop__deterministic_fill__var] = py_arg_src_teleon_synthesis_codeblock_loop__deterministic_fill__block.defaults[py_local_src_teleon_synthesis_codeblock_loop__deterministic_fill__var]
    return py_local_src_teleon_synthesis_codeblock_loop__deterministic_fill__fills


def py_function_src_teleon_synthesis_codeblock_loop___fill_prompt(py_arg_src_teleon_synthesis_codeblock_loop__fill_prompt__task: str, py_arg_src_teleon_synthesis_codeblock_loop__fill_prompt__block: py_class_src_teleon_synthesis_codeblock_loop__Codeblock, py_arg_src_teleon_synthesis_codeblock_loop__fill_prompt__need: list, py_arg_src_teleon_synthesis_codeblock_loop__fill_prompt__feedback: dict) -> str:
    py_local_src_teleon_synthesis_codeblock_loop__fill_prompt__lines = [f"Task: {py_arg_src_teleon_synthesis_codeblock_loop__fill_prompt__task}",
             f"Fill these variables for a {py_arg_src_teleon_synthesis_codeblock_loop__fill_prompt__block.language} code template: {py_arg_src_teleon_synthesis_codeblock_loop__fill_prompt__need}.",
             f"Template:\n{py_arg_src_teleon_synthesis_codeblock_loop__fill_prompt__block.template}",
             "Return one `name = value` per line; the values must make the rendered code parse and satisfy "
             f"outputs={py_arg_src_teleon_synthesis_codeblock_loop__fill_prompt__block.outputs} inputs={py_arg_src_teleon_synthesis_codeblock_loop__fill_prompt__block.inputs}."]
    if py_arg_src_teleon_synthesis_codeblock_loop__fill_prompt__feedback.get("text"):
        py_local_src_teleon_synthesis_codeblock_loop__fill_prompt__lines.append(f"RETRY: the previous attempt FAILED — fix it. Feedback: {py_arg_src_teleon_synthesis_codeblock_loop__fill_prompt__feedback['text']}")
    return "\n".join(py_local_src_teleon_synthesis_codeblock_loop__fill_prompt__lines)


def py_function_src_teleon_synthesis_codeblock_loop___parse_fills(py_arg_src_teleon_synthesis_codeblock_loop__parse_fills__text: str, py_arg_src_teleon_synthesis_codeblock_loop__parse_fills__variables: list) -> dict:
    """Parse `name = value` / `name: value` lines (tolerating code-fence backticks) into a fills dict for known vars."""
    py_local_src_teleon_synthesis_codeblock_loop__parse_fills__out: dict = {}
    for py_local_src_teleon_synthesis_codeblock_loop__parse_fills__raw in (py_arg_src_teleon_synthesis_codeblock_loop__parse_fills__text or "").splitlines():
        py_local_src_teleon_synthesis_codeblock_loop__parse_fills__line = py_local_src_teleon_synthesis_codeblock_loop__parse_fills__raw.strip().strip("`").strip()
        py_local_src_teleon_synthesis_codeblock_loop__parse_fills__m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*[:=]\s*(.*)$", py_local_src_teleon_synthesis_codeblock_loop__parse_fills__line)
        if py_local_src_teleon_synthesis_codeblock_loop__parse_fills__m and py_local_src_teleon_synthesis_codeblock_loop__parse_fills__m.group(1) in py_arg_src_teleon_synthesis_codeblock_loop__parse_fills__variables:
            py_local_src_teleon_synthesis_codeblock_loop__parse_fills__out[py_local_src_teleon_synthesis_codeblock_loop__parse_fills__m.group(1)] = py_local_src_teleon_synthesis_codeblock_loop__parse_fills__m.group(2).strip()
    return py_local_src_teleon_synthesis_codeblock_loop__parse_fills__out


def py_function_src_teleon_synthesis_codeblock_loop___llm_fill(py_arg_src_teleon_synthesis_codeblock_loop__llm_fill__call, py_arg_src_teleon_synthesis_codeblock_loop__llm_fill__task: str, py_arg_src_teleon_synthesis_codeblock_loop__llm_fill__block: py_class_src_teleon_synthesis_codeblock_loop__Codeblock, py_arg_src_teleon_synthesis_codeblock_loop__llm_fill__values: dict, py_arg_src_teleon_synthesis_codeblock_loop__llm_fill__feedback: dict) -> dict:
    """The LLM proposes fills for the gap variables; provided values stay authoritative; declared defaults backstop
    anything STILL unfilled (so the loop degrades, never fabricates)."""
    py_local_src_teleon_synthesis_codeblock_loop__llm_fill__variables = py_arg_src_teleon_synthesis_codeblock_loop__llm_fill__block.declared_variables()
    py_local_src_teleon_synthesis_codeblock_loop__llm_fill__need = [py_local_src_teleon_synthesis_codeblock_loop__llm_fill__v for py_local_src_teleon_synthesis_codeblock_loop__llm_fill__v in py_local_src_teleon_synthesis_codeblock_loop__llm_fill__variables if py_local_src_teleon_synthesis_codeblock_loop__llm_fill__v not in py_arg_src_teleon_synthesis_codeblock_loop__llm_fill__values]
    try:
        py_local_src_teleon_synthesis_codeblock_loop__llm_fill__text = py_arg_src_teleon_synthesis_codeblock_loop__llm_fill__call(py_function_src_teleon_synthesis_codeblock_loop___fill_prompt(py_arg_src_teleon_synthesis_codeblock_loop__llm_fill__task, py_arg_src_teleon_synthesis_codeblock_loop__llm_fill__block, py_local_src_teleon_synthesis_codeblock_loop__llm_fill__need, py_arg_src_teleon_synthesis_codeblock_loop__llm_fill__feedback)) or ""
    except Exception:  # noqa: BLE001
        py_local_src_teleon_synthesis_codeblock_loop__llm_fill__text = ""
    py_local_src_teleon_synthesis_codeblock_loop__llm_fill__fills = {**py_function_src_teleon_synthesis_codeblock_loop___parse_fills(py_local_src_teleon_synthesis_codeblock_loop__llm_fill__text, py_local_src_teleon_synthesis_codeblock_loop__llm_fill__variables), **py_arg_src_teleon_synthesis_codeblock_loop__llm_fill__values}
    for py_local_src_teleon_synthesis_codeblock_loop__llm_fill__v in py_local_src_teleon_synthesis_codeblock_loop__llm_fill__variables:
        if py_local_src_teleon_synthesis_codeblock_loop__llm_fill__v not in py_local_src_teleon_synthesis_codeblock_loop__llm_fill__fills and py_local_src_teleon_synthesis_codeblock_loop__llm_fill__v in py_arg_src_teleon_synthesis_codeblock_loop__llm_fill__block.defaults:
            py_local_src_teleon_synthesis_codeblock_loop__llm_fill__fills[py_local_src_teleon_synthesis_codeblock_loop__llm_fill__v] = py_arg_src_teleon_synthesis_codeblock_loop__llm_fill__block.defaults[py_local_src_teleon_synthesis_codeblock_loop__llm_fill__v]
    return py_local_src_teleon_synthesis_codeblock_loop__llm_fill__fills


def py_function_src_teleon_synthesis_codeblock_loop___resolve_llm(py_arg_src_teleon_synthesis_codeblock_loop__resolve_llm__llm):
    """Resolve the fill LLM to a (prompt)->str callable, or None (honest-unavailable -> deterministic fill).
    Accepts an LLMPort / a (prompt)->str callable / a model-or-lane name / 'auto' / None."""
    if py_arg_src_teleon_synthesis_codeblock_loop__resolve_llm__llm is None or py_arg_src_teleon_synthesis_codeblock_loop__resolve_llm__llm == "auto":
        return as_callable(select_llm("auto"))
    return as_callable(py_arg_src_teleon_synthesis_codeblock_loop__resolve_llm__llm)


# ── the loop ──────────────────────────────────────────────────────────────────────────────────────────────────────
@dataclass
class py_class_src_teleon_synthesis_codeblock_loop__FillAttempt:
    attempt: int
    source: str
    fills: dict
    block_text: str
    verdict: dict
    feedback: str = ""

    def to_dict(self) -> dict:
        return {"attempt": self.attempt, "source": self.source, "fills": self.fills, "block_text": self.block_text,
                "ok": self.verdict["ok"], "errors": self.verdict["errors"], "feedback": self.feedback}


def py_function_src_teleon_synthesis_codeblock_loop___feedback(py_arg_src_teleon_synthesis_codeblock_loop__feedback__verdict: dict) -> str:
    return "" if py_arg_src_teleon_synthesis_codeblock_loop__feedback__verdict["ok"] else ("; ".join(py_arg_src_teleon_synthesis_codeblock_loop__feedback__verdict["errors"]) or "invalid fill")


def py_function_src_teleon_synthesis_codeblock_loop__fill_codeblock(py_arg_src_teleon_synthesis_codeblock_loop__fill_codeblock__task: str, py_arg_src_teleon_synthesis_codeblock_loop__fill_codeblock__block: py_class_src_teleon_synthesis_codeblock_loop__Codeblock, values: dict | None = None, *, llm="auto",
                   max_attempts: int = py_const_src_teleon_synthesis_codeblock_loop__DEFAULT_MAX_ATTEMPTS) -> dict:
    """Fill -> validate -> (on failure) feedback -> retry, BOUNDED by max_attempts (1 initial + retries). Returns the
    verdict + the runnable block (only when valid — honest) + the LOSSLESS history of every attempt. Never raises."""
    values = dict(values or {})
    py_local_src_teleon_synthesis_codeblock_loop__fill_codeblock__call = py_function_src_teleon_synthesis_codeblock_loop___resolve_llm(llm)
    py_local_src_teleon_synthesis_codeblock_loop__fill_codeblock__llm_used = py_local_src_teleon_synthesis_codeblock_loop__fill_codeblock__call is not None
    py_local_src_teleon_synthesis_codeblock_loop__fill_codeblock__source = "llm" if py_local_src_teleon_synthesis_codeblock_loop__fill_codeblock__llm_used else "deterministic"
    py_local_src_teleon_synthesis_codeblock_loop__fill_codeblock__history: list[py_class_src_teleon_synthesis_codeblock_loop__FillAttempt] = []
    py_local_src_teleon_synthesis_codeblock_loop__fill_codeblock__feedback: dict = {}
    for py_local_src_teleon_synthesis_codeblock_loop__fill_codeblock__i in range(1, max(1, max_attempts) + 1):
        py_local_src_teleon_synthesis_codeblock_loop__fill_codeblock__fills = py_function_src_teleon_synthesis_codeblock_loop___llm_fill(py_local_src_teleon_synthesis_codeblock_loop__fill_codeblock__call, py_arg_src_teleon_synthesis_codeblock_loop__fill_codeblock__task, py_arg_src_teleon_synthesis_codeblock_loop__fill_codeblock__block, values, py_local_src_teleon_synthesis_codeblock_loop__fill_codeblock__feedback) if py_local_src_teleon_synthesis_codeblock_loop__fill_codeblock__llm_used else py_function_src_teleon_synthesis_codeblock_loop___deterministic_fill(py_arg_src_teleon_synthesis_codeblock_loop__fill_codeblock__block, values, py_local_src_teleon_synthesis_codeblock_loop__fill_codeblock__feedback)
        py_local_src_teleon_synthesis_codeblock_loop__fill_codeblock__text = py_function_src_teleon_synthesis_codeblock_loop__render(py_arg_src_teleon_synthesis_codeblock_loop__fill_codeblock__block.template, py_local_src_teleon_synthesis_codeblock_loop__fill_codeblock__fills)
        py_local_src_teleon_synthesis_codeblock_loop__fill_codeblock__verdict = py_function_src_teleon_synthesis_codeblock_loop__validate(py_local_src_teleon_synthesis_codeblock_loop__fill_codeblock__text, py_arg_src_teleon_synthesis_codeblock_loop__fill_codeblock__block)
        py_local_src_teleon_synthesis_codeblock_loop__fill_codeblock__history.append(py_class_src_teleon_synthesis_codeblock_loop__FillAttempt(py_local_src_teleon_synthesis_codeblock_loop__fill_codeblock__i, py_local_src_teleon_synthesis_codeblock_loop__fill_codeblock__source, dict(py_local_src_teleon_synthesis_codeblock_loop__fill_codeblock__fills), py_local_src_teleon_synthesis_codeblock_loop__fill_codeblock__text, py_local_src_teleon_synthesis_codeblock_loop__fill_codeblock__verdict, py_function_src_teleon_synthesis_codeblock_loop___feedback(py_local_src_teleon_synthesis_codeblock_loop__fill_codeblock__verdict)))
        if py_local_src_teleon_synthesis_codeblock_loop__fill_codeblock__verdict["ok"]:
            return py_function_src_teleon_synthesis_codeblock_loop___result(py_arg_src_teleon_synthesis_codeblock_loop__fill_codeblock__task, py_arg_src_teleon_synthesis_codeblock_loop__fill_codeblock__block, py_local_src_teleon_synthesis_codeblock_loop__fill_codeblock__history, True, py_local_src_teleon_synthesis_codeblock_loop__fill_codeblock__llm_used)
        py_local_src_teleon_synthesis_codeblock_loop__fill_codeblock__feedback = {"unfilled": py_local_src_teleon_synthesis_codeblock_loop__fill_codeblock__verdict["unfilled"], "errors": py_local_src_teleon_synthesis_codeblock_loop__fill_codeblock__verdict["errors"], "text": py_function_src_teleon_synthesis_codeblock_loop___feedback(py_local_src_teleon_synthesis_codeblock_loop__fill_codeblock__verdict)}
    return py_function_src_teleon_synthesis_codeblock_loop___result(py_arg_src_teleon_synthesis_codeblock_loop__fill_codeblock__task, py_arg_src_teleon_synthesis_codeblock_loop__fill_codeblock__block, py_local_src_teleon_synthesis_codeblock_loop__fill_codeblock__history, False, py_local_src_teleon_synthesis_codeblock_loop__fill_codeblock__llm_used)


def py_function_src_teleon_synthesis_codeblock_loop___result(py_arg_src_teleon_synthesis_codeblock_loop__result__task: str, py_arg_src_teleon_synthesis_codeblock_loop__result__block: py_class_src_teleon_synthesis_codeblock_loop__Codeblock, py_arg_src_teleon_synthesis_codeblock_loop__result__history: list, py_arg_src_teleon_synthesis_codeblock_loop__result__ok: bool, py_arg_src_teleon_synthesis_codeblock_loop__result__llm_used: bool) -> dict:
    py_local_src_teleon_synthesis_codeblock_loop__result__last = py_arg_src_teleon_synthesis_codeblock_loop__result__history[-1]
    return {
        "task": py_arg_src_teleon_synthesis_codeblock_loop__result__task, "block_id": py_arg_src_teleon_synthesis_codeblock_loop__result__block.block_id, "language": py_arg_src_teleon_synthesis_codeblock_loop__result__block.language,
        "filled": py_arg_src_teleon_synthesis_codeblock_loop__result__ok,
        "block": py_local_src_teleon_synthesis_codeblock_loop__result__last.block_text if py_arg_src_teleon_synthesis_codeblock_loop__result__ok else None,         # the runnable code, only when valid (honest)
        "final_text": py_local_src_teleon_synthesis_codeblock_loop__result__last.block_text,                    # always present (incl. the last rejected) for inspection
        "attempts": len(py_arg_src_teleon_synthesis_codeblock_loop__result__history), "llm_used": py_arg_src_teleon_synthesis_codeblock_loop__result__llm_used,
        "verdict": py_local_src_teleon_synthesis_codeblock_loop__result__last.verdict,
        "template": py_arg_src_teleon_synthesis_codeblock_loop__result__block.template,                       # LOSSLESS: the template is preserved unmutated
        "inputs": list(py_arg_src_teleon_synthesis_codeblock_loop__result__block.inputs), "outputs": list(py_arg_src_teleon_synthesis_codeblock_loop__result__block.outputs),
        "history": [a.to_dict() for a in py_arg_src_teleon_synthesis_codeblock_loop__result__history],        # LOSSLESS: every attempt incl. rejected, with its feedback
        "rejected": [a.to_dict() for a in py_arg_src_teleon_synthesis_codeblock_loop__result__history if not a.verdict["ok"]],
        "reason": None if py_arg_src_teleon_synthesis_codeblock_loop__result__ok else f"no valid fill within {len(py_arg_src_teleon_synthesis_codeblock_loop__result__history)} attempt(s)",
        "serves_truth": False,
    }


def py_function_src_teleon_synthesis_codeblock_loop__persist_history(py_arg_src_teleon_synthesis_codeblock_loop__persist_history__result: dict, py_arg_src_teleon_synthesis_codeblock_loop__persist_history__path) -> str:
    """LOSSLESS sink: the template + every attempt (incl. rejected) as JSONL (the caller owns the path; temp/local).
    Mirrors synthesis_trace's plain-JSONL persistence. serves_truth=false."""
    p = Path(py_arg_src_teleon_synthesis_codeblock_loop__persist_history__path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as py_local_src_teleon_synthesis_codeblock_loop__persist_history__f:
        py_local_src_teleon_synthesis_codeblock_loop__persist_history__f.write(json.dumps({"record": "template", "block_id": py_arg_src_teleon_synthesis_codeblock_loop__persist_history__result["block_id"], "template": py_arg_src_teleon_synthesis_codeblock_loop__persist_history__result["template"]}) + "\n")
        for py_local_src_teleon_synthesis_codeblock_loop__persist_history__a in py_arg_src_teleon_synthesis_codeblock_loop__persist_history__result["history"]:
            py_local_src_teleon_synthesis_codeblock_loop__persist_history__f.write(json.dumps({"record": "attempt", "block_id": py_arg_src_teleon_synthesis_codeblock_loop__persist_history__result["block_id"], **py_local_src_teleon_synthesis_codeblock_loop__persist_history__a}) + "\n")
    return str(p)


# ── compose wiring (the compose-facing entry point; registry.compose can import + call this, no edit to compose.py) ─
def py_function_src_teleon_synthesis_codeblock_loop__compose_codeblock(py_arg_src_teleon_synthesis_codeblock_loop__compose_codeblock__intent: str, py_arg_src_teleon_synthesis_codeblock_loop__compose_codeblock__block_spec, values: dict | None = None, *, llm="auto",
                      py_arg_src_teleon_synthesis_codeblock_loop__compose_codeblock__max_attempts: int = py_const_src_teleon_synthesis_codeblock_loop__DEFAULT_MAX_ATTEMPTS) -> dict:
    """Compose a codeblock as a runnable stage: hand an intent + a codeblock spec (a Codeblock or a plain dict) +
    provided values; this fills+validates into a CANDIDATE block (shaped like registry.compose's candidate outputs).
    The verification + governance gates still run before anything executes — candidate, not promoted. serves_truth=false."""
    py_local_src_teleon_synthesis_codeblock_loop__compose_codeblock__block = py_arg_src_teleon_synthesis_codeblock_loop__compose_codeblock__block_spec if isinstance(py_arg_src_teleon_synthesis_codeblock_loop__compose_codeblock__block_spec, py_class_src_teleon_synthesis_codeblock_loop__Codeblock) else py_function_src_teleon_synthesis_codeblock_loop__codeblock_from_dict(py_arg_src_teleon_synthesis_codeblock_loop__compose_codeblock__block_spec)
    py_local_src_teleon_synthesis_codeblock_loop__compose_codeblock__res = py_function_src_teleon_synthesis_codeblock_loop__fill_codeblock(py_arg_src_teleon_synthesis_codeblock_loop__compose_codeblock__intent, py_local_src_teleon_synthesis_codeblock_loop__compose_codeblock__block, values, llm=llm, max_attempts=py_arg_src_teleon_synthesis_codeblock_loop__compose_codeblock__max_attempts)
    return {"intent": py_arg_src_teleon_synthesis_codeblock_loop__compose_codeblock__intent, "block_id": py_local_src_teleon_synthesis_codeblock_loop__compose_codeblock__block.block_id, "candidate_codeblock": True,
            "filled": py_local_src_teleon_synthesis_codeblock_loop__compose_codeblock__res["filled"], "block": py_local_src_teleon_synthesis_codeblock_loop__compose_codeblock__res["block"], "attempts": py_local_src_teleon_synthesis_codeblock_loop__compose_codeblock__res["attempts"],
            "result": py_local_src_teleon_synthesis_codeblock_loop__compose_codeblock__res, "serves_truth": False}


__all__ = ["py_class_src_teleon_synthesis_codeblock_loop__Codeblock", "py_function_src_teleon_synthesis_codeblock_loop__codeblock_from_dict", "py_function_src_teleon_synthesis_codeblock_loop__template_variables", "py_function_src_teleon_synthesis_codeblock_loop__render", "py_function_src_teleon_synthesis_codeblock_loop__validate",
           "py_function_src_teleon_synthesis_codeblock_loop__fill_codeblock", "py_function_src_teleon_synthesis_codeblock_loop__persist_history", "py_function_src_teleon_synthesis_codeblock_loop__compose_codeblock", "py_const_src_teleon_synthesis_codeblock_loop__DEFAULT_MAX_ATTEMPTS"]


# ── self-test (deterministic · offline · temp paths only) ─────────────────────────────────────────────────────────
def py_function_src_teleon_synthesis_codeblock_loop__self_test() -> int:
    import tempfile

    # A codeblock = a reusable code template with declared variables / inputs / outputs (+ a safe default for `expr`).
    block = py_class_src_teleon_synthesis_codeblock_loop__Codeblock(
        block_id="greet_fn",
        template='def {{fn}}(payload):\n    result = {{expr}}\n    return result',
        variables=["fn", "expr"],
        inputs=["payload"],          # the rendered body must REFERENCE payload
        outputs=["result"],          # the rendered code must DEFINE result
        defaults={"expr": "payload"},  # deterministic repair when `expr` isn't provided
    )
    py_local_src_teleon_synthesis_codeblock_loop__self_test__det = select_llm("deterministic")  # available()==False -> the loop takes the deterministic fill path (offline)

    # (1) fills from PROVIDED VALUES, validates first try (deterministic path; no LLM).
    py_local_src_teleon_synthesis_codeblock_loop__self_test__r1 = py_function_src_teleon_synthesis_codeblock_loop__fill_codeblock("greet a user", block,
                        values={"fn": "greet", "expr": 'f"hi {payload}"'}, llm=py_local_src_teleon_synthesis_codeblock_loop__self_test__det)
    assert py_local_src_teleon_synthesis_codeblock_loop__self_test__r1["filled"] is True, py_local_src_teleon_synthesis_codeblock_loop__self_test__r1["verdict"]
    assert py_local_src_teleon_synthesis_codeblock_loop__self_test__r1["attempts"] == 1 and py_local_src_teleon_synthesis_codeblock_loop__self_test__r1["llm_used"] is False, py_local_src_teleon_synthesis_codeblock_loop__self_test__r1
    assert py_local_src_teleon_synthesis_codeblock_loop__self_test__r1["verdict"]["syntax_ok"] and not py_local_src_teleon_synthesis_codeblock_loop__self_test__r1["verdict"]["missing_outputs"] and not py_local_src_teleon_synthesis_codeblock_loop__self_test__r1["verdict"]["missing_inputs"]
    assert py_local_src_teleon_synthesis_codeblock_loop__self_test__r1["block"] and "{{" not in py_local_src_teleon_synthesis_codeblock_loop__self_test__r1["block"] and "greet" in py_local_src_teleon_synthesis_codeblock_loop__self_test__r1["block"]
    compile(py_local_src_teleon_synthesis_codeblock_loop__self_test__r1["block"], "<greet>", "exec")            # the emitted block is real, runnable python

    # (2a) BOUNDED RETRY on a bad fill RECOVERS — deterministic path: incomplete values -> default repair on retry.
    py_local_src_teleon_synthesis_codeblock_loop__self_test__r2 = py_function_src_teleon_synthesis_codeblock_loop__fill_codeblock("greet (incomplete values)", block, values={"fn": "greet"}, llm=py_local_src_teleon_synthesis_codeblock_loop__self_test__det)
    assert py_local_src_teleon_synthesis_codeblock_loop__self_test__r2["filled"] is True and py_local_src_teleon_synthesis_codeblock_loop__self_test__r2["attempts"] == 2, py_local_src_teleon_synthesis_codeblock_loop__self_test__r2
    assert py_local_src_teleon_synthesis_codeblock_loop__self_test__r2["history"][0]["ok"] is False and "expr" in str(py_local_src_teleon_synthesis_codeblock_loop__self_test__r2["history"][0]["errors"]), "first attempt rejected on `expr`"
    assert py_local_src_teleon_synthesis_codeblock_loop__self_test__r2["history"][1]["fills"].get("expr") == "payload", "the declared default repaired the retry"
    compile(py_local_src_teleon_synthesis_codeblock_loop__self_test__r2["block"], "<greet2>", "exec")

    # (2b) BOUNDED RETRY on a bad fill RECOVERS — LLM path: a bad fill, then the LLM fixes once it SEES the feedback.
    py_local_src_teleon_synthesis_codeblock_loop__self_test__calls = {"n": 0}
    def _double(py_arg_src_teleon_synthesis_codeblock_loop__self_test__double__prompt: str) -> str:
        py_local_src_teleon_synthesis_codeblock_loop__self_test__calls["n"] += 1
        if "FAILED" in py_arg_src_teleon_synthesis_codeblock_loop__self_test__double__prompt:                          # the feedback reached the filler -> emit a valid fill
            return 'fn = greet\nexpr = f"hi {payload}"'
        return "fn = greet\nexpr = return payload"      # first try: `return payload` as an expr -> syntax error
    py_local_src_teleon_synthesis_codeblock_loop__self_test__r3 = py_function_src_teleon_synthesis_codeblock_loop__fill_codeblock("greet via llm", block, values={}, llm=CallableLLM(_double, name="double"), max_attempts=3)
    assert py_local_src_teleon_synthesis_codeblock_loop__self_test__r3["llm_used"] is True and py_local_src_teleon_synthesis_codeblock_loop__self_test__r3["filled"] is True and py_local_src_teleon_synthesis_codeblock_loop__self_test__r3["attempts"] == 2, (py_local_src_teleon_synthesis_codeblock_loop__self_test__r3["attempts"], py_local_src_teleon_synthesis_codeblock_loop__self_test__r3["verdict"])
    assert py_local_src_teleon_synthesis_codeblock_loop__self_test__calls["n"] == 2, "the loop must RE-CALL the LLM with feedback after the bad fill"
    assert py_local_src_teleon_synthesis_codeblock_loop__self_test__r3["history"][0]["ok"] is False and py_local_src_teleon_synthesis_codeblock_loop__self_test__r3["history"][0]["feedback"], "the rejected first fill + its feedback are kept"
    compile(py_local_src_teleon_synthesis_codeblock_loop__self_test__r3["block"], "<greet3>", "exec")

    # (3) BOUNDED failure is honest (never exceeds max_attempts; no fabricated block).
    py_local_src_teleon_synthesis_codeblock_loop__self_test__r4 = py_function_src_teleon_synthesis_codeblock_loop__fill_codeblock("never valid", block, values={},
                        llm=CallableLLM(lambda py_arg_src_teleon_synthesis_codeblock_loop__self_test___p: "fn = greet\nexpr = def"), max_attempts=2)
    assert py_local_src_teleon_synthesis_codeblock_loop__self_test__r4["filled"] is False and py_local_src_teleon_synthesis_codeblock_loop__self_test__r4["attempts"] == 2, py_local_src_teleon_synthesis_codeblock_loop__self_test__r4
    assert py_local_src_teleon_synthesis_codeblock_loop__self_test__r4["block"] is None and py_local_src_teleon_synthesis_codeblock_loop__self_test__r4["reason"] and len(py_local_src_teleon_synthesis_codeblock_loop__self_test__r4["rejected"]) == 2, py_local_src_teleon_synthesis_codeblock_loop__self_test__r4

    # (4) LOSSLESS — the template is preserved unmutated and every attempt (incl. rejected) survives, durably (temp JSONL).
    assert py_local_src_teleon_synthesis_codeblock_loop__self_test__r2["template"] == block.template, "the template must be preserved unmutated (lossless)"
    with tempfile.TemporaryDirectory() as py_local_src_teleon_synthesis_codeblock_loop__self_test__td:
        py_local_src_teleon_synthesis_codeblock_loop__self_test__path = py_function_src_teleon_synthesis_codeblock_loop__persist_history(py_local_src_teleon_synthesis_codeblock_loop__self_test__r2, Path(py_local_src_teleon_synthesis_codeblock_loop__self_test__td) / "codeblock_history.jsonl")
        py_local_src_teleon_synthesis_codeblock_loop__self_test__rows = [json.loads(line) for line in Path(py_local_src_teleon_synthesis_codeblock_loop__self_test__path).read_text(encoding="utf-8").splitlines()]
        assert py_local_src_teleon_synthesis_codeblock_loop__self_test__rows[0]["record"] == "template" and py_local_src_teleon_synthesis_codeblock_loop__self_test__rows[0]["template"] == block.template
        py_local_src_teleon_synthesis_codeblock_loop__self_test__attempts = [r for r in py_local_src_teleon_synthesis_codeblock_loop__self_test__rows if r["record"] == "attempt"]
        assert len(py_local_src_teleon_synthesis_codeblock_loop__self_test__attempts) == py_local_src_teleon_synthesis_codeblock_loop__self_test__r2["attempts"] == 2 and any(a["ok"] is False for a in py_local_src_teleon_synthesis_codeblock_loop__self_test__attempts), "rejected attempt persisted"

    # (5) compose wiring — a plain dict spec composes into a CANDIDATE runnable block.
    py_local_src_teleon_synthesis_codeblock_loop__self_test__spec = {"block_id": "sum_fn", "template": "def {{fn}}(a, b):\n    total = a + b\n    return total",
            "variables": ["fn"], "inputs": ["a"], "outputs": ["total"]}
    py_local_src_teleon_synthesis_codeblock_loop__self_test__comp = py_function_src_teleon_synthesis_codeblock_loop__compose_codeblock("add two numbers", py_local_src_teleon_synthesis_codeblock_loop__self_test__spec, values={"fn": "add"}, llm=py_local_src_teleon_synthesis_codeblock_loop__self_test__det)
    assert py_local_src_teleon_synthesis_codeblock_loop__self_test__comp["candidate_codeblock"] is True and py_local_src_teleon_synthesis_codeblock_loop__self_test__comp["filled"] is True and py_local_src_teleon_synthesis_codeblock_loop__self_test__comp["serves_truth"] is False
    compile(py_local_src_teleon_synthesis_codeblock_loop__self_test__comp["block"], "<sum>", "exec")

    # Governance: every surfaced result serves_truth=false (an LLM/fill is never a source of truth).
    assert all(r["serves_truth"] is False for r in (py_local_src_teleon_synthesis_codeblock_loop__self_test__r1, py_local_src_teleon_synthesis_codeblock_loop__self_test__r2, py_local_src_teleon_synthesis_codeblock_loop__self_test__r3, py_local_src_teleon_synthesis_codeblock_loop__self_test__r4, py_local_src_teleon_synthesis_codeblock_loop__self_test__comp))

    print(f"codeblock_loop self-test: OK (provided-values fill+validate [1 attempt] · bounded retry recovers "
          f"[deterministic {py_local_src_teleon_synthesis_codeblock_loop__self_test__r2['attempts']} / llm {py_local_src_teleon_synthesis_codeblock_loop__self_test__r3['attempts']} attempts] · bounded failure honest "
          f"[{py_local_src_teleon_synthesis_codeblock_loop__self_test__r4['attempts']} attempts, no block] · lossless template+history persisted · "
          f"compose_codeblock candidate · serves_truth=false)")
    return 0


def main(py_arg_src_teleon_synthesis_codeblock_loop__main__argv: list) -> int:
    if "--self-test" in py_arg_src_teleon_synthesis_codeblock_loop__main__argv:
        return py_function_src_teleon_synthesis_codeblock_loop__self_test()
    print("usage: codeblock_loop --self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
