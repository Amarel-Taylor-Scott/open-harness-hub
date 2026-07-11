#!/usr/bin/env python3
"""scripts.code_factory_lane — the Compiled-AI paper's CODE FACTORY as a SIDE-BY-SIDE lane over OUR gap specs.

The Compiled-AI paradigm (XY.AI Labs et al., 2026) pairs the compile-once route cache
(``scripts/compiled_route_cache.py``) with a Code Factory: when compilation finds a genuinely MISSING
narrow function, the factory renders it into a VALIDATED TEMPLATE and runs a four-stage
generation-and-validation pipeline. Our system already flags exactly that hole —
``primitive_runtime.compose_solution`` emits a ``model_step_flag`` gap spec (a ``needed_output_type``
nobody produces, remix stage 6) — but nothing turned the flag into a reviewable candidate component.
This lane adds exactly that, reusing the existing engines:

  stage 1  RENDER           deterministic template fill from the gap spec (the ``_render_*`` string-fill
                            pattern of scripts/observer_local_service.py; identifiers follow
                            architecture/teleon_codegen_contracts.json). The body is a typed
                            identity/transform STUB the caller must review — needs_review=true,
                            NOT executable-as-truth.
  stage 2  COMPILE-CHECK    ``compile()`` the rendered source; a SyntaxError is a hard reject.
  stage 3  SELF-TEST        exec in a namespace, call the function on a synthetic input matching the
                            input edge, assert the output envelope shape. (Safety note: the stage-4
                            deny-list screen is COMPUTED before any exec — an unscreened body is never
                            executed — while receipts keep the paper's stage numbering.)
  stage 4  SECURITY SCREEN  deny-list scan (exec/eval/os.system/subprocess/__import__ substrings + an
                            AST open-for-write check), named constants only.

Output: one candidate CARD per gap — primitive_id minted via sha256 of content through the canonical_id
authority (``src.teleon.experiments.ids``), input_edge/output_edge from the gap spec, a blackbox
describing the generated function, generation_stage_receipts for all four stages, and always
``candidate=true, serves_truth=false, needs_review=true``. Generation is NEVER promotion. Deterministic:
no RNG, no wall-clock in any id/key — byte-identical twice. Side-by-side: this module edits nothing; it
only imports existing engines.

    PYTHONPATH=. python3 scripts/code_factory_lane.py --self-test     # also runs BARE (sentinel bootstrap)
    PYTHONPATH=. python3 scripts/code_factory_lane.py --intent "from X to Y"
"""
from __future__ import annotations

import sys
from pathlib import Path

_here = Path(__file__).resolve()
_sbc = next((p for p in _here.parents if (p / "scripts" / "_repo_paths.py").exists()), _here.parents[1])
if str(_sbc) not in sys.path:
    sys.path.insert(0, str(_sbc))
from scripts._repo_paths import install as _install_code_roots  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import ast  # noqa: E402
import json  # noqa: E402
import re  # noqa: E402
from typing import Any, Iterator, Optional  # noqa: E402

from scripts._repo_paths import resource  # noqa: E402  the universal repo-relative resource resolver
from src.teleon.experiments.ids import canonical_id, sha256_hex  # noqa: E402  the DATA-plane id authority

# ── the governed-candidate boundary (mirrors scripts/compiled_route_cache.py; the law is
#    standards/CANDIDATE-TRUTH-BOUNDARY.md — every generated row is born candidate, never truth) ──────────
BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}

# ── record types (one definition each; consumers match on these, never on retyped literals) ──────────────
CARD_RECORD_TYPE = "code_factory_candidate_card"          # the manufactured candidate component card
RECEIPT_RECORD_TYPE = "generation_stage_receipt"          # one per pipeline stage, kept on the card
LANE_RECORD_TYPE = "code_factory_lane_result"             # the intent-level wrapper around the cards
GAP_RECORD_TYPE = "model_step_flag"                       # emitted by primitive_runtime.remix_gap — the input we consume

# ── card identity + metadata ──────────────────────────────────────────────────────────────────────────────
CARD_ID_PREFIX = "codefactory"      # DATA-plane prefix; canonical_id makes the id f"{prefix}-{sha256[:16]}" of content
CARD_SCHEMA_VERSION = 1             # version lives in METADATA, never in a name or id (naming law)
CARD_KIND_ACTION = "action"         # a generated processor is an Action per the product vocabulary
NEEDS_REVIEW_ALWAYS = True          # the template body is a typed stub — a human must review before ANY promotion

# ── the four pipeline stages, in the paper's order (receipts are always emitted in this order) ───────────
STAGE_RENDER = "stage1_render"
STAGE_COMPILE_CHECK = "stage2_compile_check"
STAGE_SELF_TEST = "stage3_self_test"
STAGE_SECURITY_SCREEN = "stage4_security_screen"
STAGE_ORDER: tuple[str, ...] = (STAGE_RENDER, STAGE_COMPILE_CHECK, STAGE_SELF_TEST, STAGE_SECURITY_SCREEN)

# ── stage-receipt path labels (produced by the stages AND asserted by the self-test — single source) ─────
PATH_RENDERED_FROM_GAP_SPEC = "rendered_from_gap_spec_template"
PATH_OVERRIDE_INJECTED = "override_injected_for_testing"            # the self-test's defect-injection hook
PATH_COMPILE_OK = "compile_ok"
PATH_SYNTAX_ERROR = "syntax_error_rejected"
PATH_SCREEN_CLEAN = "denylist_screen_clean"
PATH_SCREEN_VIOLATIONS = "denylist_screen_rejected"
PATH_SELFTEST_OK = "synthetic_shape_asserted"
PATH_SELFTEST_SHAPE_FAILED = "synthetic_shape_failed"
PATH_SELFTEST_EXEC_ERROR = "exec_or_call_error"
PATH_SELFTEST_FN_MISSING = "generated_function_not_defined"
PATH_SELFTEST_SKIPPED_COMPILE = "skipped_compile_failed_source_never_executed"
PATH_SELFTEST_SKIPPED_SCREEN = "skipped_unscreened_source_never_executed"

# ── stage 1 RENDER constants ──────────────────────────────────────────────────────────────────────────────
TEMPLATE_ID = "typed_identity_transform_stub"   # the one deterministic template this lane renders today
GENERATED_VIRTUAL_FILE_TAG = "code_factory_generated"       # the <file> part of every generated identifier
GENERATED_VIRTUAL_FILENAME = "<code_factory_generated>"     # compile()/traceback filename for generated source
GENERATED_VIRTUAL_MODULE_NAME = "code_factory_generated_candidate"  # __name__ inside the stage-3 exec namespace
GENERATED_FUNCTION_NAME_PREFIX = f"py_function__{GENERATED_VIRTUAL_FILE_TAG}__"  # codegen naming-contract prefix
RENDER_UNTYPED_EDGE_FALLBACK = "UntypedEdge"    # a gap spec may carry a None edge; the stub renders typed as this sentinel
EDGE_SLUG_FALLBACK = "untyped"                  # identifier slug when an edge name has no [0-9a-z] characters at all
CODEGEN_CONTRACTS_RELPATH = "architecture/teleon_codegen_contracts.json"  # the generated-code naming/typing law
_EDGE_SLUG_DISALLOWED = re.compile(r"[^0-9a-z]+")  # anything outside [0-9a-z] collapses to "_" in an identifier slug

# ── stage 2 COMPILE-CHECK constants ───────────────────────────────────────────────────────────────────────
COMPILE_MODE_EXEC = "exec"  # compile() mode for a module body (the generated source is a mini-module)

# ── stage 3 SELF-TEST constants ───────────────────────────────────────────────────────────────────────────
STAGE3_SYNTHETIC_VALUE = "code-factory-synthetic-input-0001"  # fixed synthetic payload value — deterministic, no RNG

# ── stage 4 SECURITY SCREEN constants (deny-list; reject-on-suspicion is the correct side of the screen) ──
SECURITY_DENYLIST_SUBSTRINGS: tuple[str, ...] = (
    "exec(",        # dynamic execution — generated code must never self-execute strings
    "eval(",        # dynamic evaluation (also matches literal_eval — over-rejection is acceptable here)
    "os.system",    # shell escape
    "subprocess",   # process spawn in any form (import or call)
    "__import__",   # dynamic import bypasses this static screen
)
OPEN_BUILTIN_NAME = "open"          # the callable the AST portion of the screen inspects
OPEN_MODE_KEYWORD = "mode"          # open(..., mode=...) keyword name
OPEN_MODE_POSITIONAL_INDEX = 1      # open(file, mode, ...) — mode is the second positional argument
OPEN_DEFAULT_MODE = "r"             # CPython's default open() mode when none is passed — read-only, allowed
OPEN_WRITE_MODE_CHARS = "wax+"      # any of these in a mode string can write/create/truncate — denied


# ══════════════════════════════════════════════════════════════════════════════════════════════════════════
# Gap-spec intake — the lane consumes compose_solution's remix.model_steps flags.
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════
def extract_model_step_gaps(solution: dict[str, Any]) -> list[dict[str, Any]]:
    """Pull the ``model_step_flag`` gap specs out of one ``compose_solution`` result, stamped with the
    intent that flagged them (lineage — the raw flag is preserved verbatim inside each returned dict)."""
    gaps: list[dict[str, Any]] = []
    for step in (solution.get("remix") or {}).get("model_steps") or []:
        if step.get("record_type") != GAP_RECORD_TYPE:
            continue
        gaps.append({**step, "flagged_by_intent": solution.get("intent")})
    return gaps


# ══════════════════════════════════════════════════════════════════════════════════════════════════════════
# Stage 1 — RENDER: deterministic template fill (the observer_local_service _render_* string-fill pattern).
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════
_CONTRACT_STAMP_CACHE: Optional[dict[str, Any]] = None


def codegen_contract_stamp() -> dict[str, Any]:
    """Read architecture/teleon_codegen_contracts.json once (via the universal ``resource()`` resolver) and
    return the provenance stamp the render receipt carries: which contract shaped the generated identifiers.
    Honest when absent — ``present=false`` with the path still named, never a fabricated law."""
    global _CONTRACT_STAMP_CACHE
    if _CONTRACT_STAMP_CACHE is None:
        contract_path = resource(CODEGEN_CONTRACTS_RELPATH)
        if contract_path.exists():
            contract = json.loads(contract_path.read_text(encoding="utf-8"))
            _CONTRACT_STAMP_CACHE = {
                "present": True,
                "contract_path": CODEGEN_CONTRACTS_RELPATH,
                "naming_law": contract.get("naming_law") or "",
                "rule_ids": [rule.get("id") for rule in (contract.get("rules") or [])],
            }
        else:
            _CONTRACT_STAMP_CACHE = {"present": False, "contract_path": CODEGEN_CONTRACTS_RELPATH,
                                     "naming_law": "", "rule_ids": []}
    return _CONTRACT_STAMP_CACHE


def _edge_slug(edge_type_name: str) -> str:
    """A deterministic identifier slug for an edge type name (lowercase, [0-9a-z_] only)."""
    slug = _EDGE_SLUG_DISALLOWED.sub("_", str(edge_type_name).lower()).strip("_")
    return slug or EDGE_SLUG_FALLBACK


def render_gap_function_source(gap_spec: dict[str, Any]) -> tuple[str, str]:
    """Stage 1: fill the typed identity/transform stub template from the gap spec — pure string assembly,
    no model call, no clock, no RNG. Returns ``(source, function_name)``.

    Generated identifiers follow the codegen contract (py_<kind>__<file>__<scope>__<name>; long names are
    context for AI readers). Edge values are embedded via ``json.dumps`` (quote-safe); a hostile edge name
    that still breaks the template fails CLOSED at stage 2 (compile) or stage 4 (screen) — never open."""
    input_edge = str(gap_spec.get("needed_input_type") or RENDER_UNTYPED_EDGE_FALLBACK)
    output_edge = str(gap_spec.get("needed_output_type") or RENDER_UNTYPED_EDGE_FALLBACK)
    input_slug, output_slug = _edge_slug(input_edge), _edge_slug(output_edge)
    scope = f"transform_{input_slug}_to_{output_slug}"
    function_name = f"{GENERATED_FUNCTION_NAME_PREFIX}module__{scope}"
    input_const = f"py_const__{GENERATED_VIRTUAL_FILE_TAG}__module__input_edge_type_{input_slug}"
    output_const = f"py_const__{GENERATED_VIRTUAL_FILE_TAG}__module__output_edge_type_{output_slug}"
    arg_name = f"py_arg__{GENERATED_VIRTUAL_FILE_TAG}__{scope}__payload"
    local_name = f"py_local__{GENERATED_VIRTUAL_FILE_TAG}__{scope}__value"
    lines = [
        f'"""Generated candidate transform: {input_edge} -> {output_edge}.',
        "",
        "purpose: close a flagged model_step gap with a NARROW reviewed function (Compiled-AI Code Factory lane).",
        'input shape: a dict envelope {"type": <input edge>, "value": <scalar_or_sequence>}; a bare value is lifted.',
        'output shape: a dict envelope {"type": <output edge>, "value": <scalar_or_sequence>} + candidate boundary flags.',
        "dependencies: none (pure function, no imports).",
        "proof-to-run: scripts/code_factory_lane.py --self-test (stage 3 synthetic-input shape assertion).",
        "",
        "NEEDS_REVIEW: the body is a typed identity/transform STUB — it forwards the input value unchanged",
        "under the output edge type. A human must confirm or replace the transform; NEVER executable-as-truth.",
        '"""',
        "",
        f"{input_const} = {json.dumps(input_edge)}",
        f"{output_const} = {json.dumps(output_edge)}",
        "",
        "",
        f"def {function_name}({arg_name}):",
        f'    """{input_edge} -> {output_edge}: typed identity/transform stub (contract in the module docstring)."""',
        f"    {local_name} = (",
        f'        {arg_name}.get("value")',
        f"        if isinstance({arg_name}, dict)",
        f"        else {arg_name}",
        "    )",
        "    return {",
        f'        "type": {output_const},',
        f'        "value": {local_name},',
        '        "candidate": True,',
        '        "serves_truth": False,',
        '        "needs_review": True,',
        "    }",
        "",
    ]
    return "\n".join(lines), function_name


# ══════════════════════════════════════════════════════════════════════════════════════════════════════════
# The stage receipt shape + stages 2–4.
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════
def _stage_receipt(stage: str, *, passed: bool, path: str, detail: str, **extras: Any) -> dict[str, Any]:
    return {"record_type": RECEIPT_RECORD_TYPE, "stage": stage, "passed": bool(passed),
            "path": path, "detail": detail, **extras, **BOUNDARY}


def compile_check_stage(source: str) -> dict[str, Any]:
    """Stage 2: ``compile()`` the rendered source; a SyntaxError is a hard reject (nothing is executed)."""
    try:
        compile(source, GENERATED_VIRTUAL_FILENAME, COMPILE_MODE_EXEC)
    except SyntaxError as syntax_error:
        return _stage_receipt(STAGE_COMPILE_CHECK, passed=False, path=PATH_SYNTAX_ERROR,
                              detail=f"SyntaxError rejected at compile(): {syntax_error.msg} "
                                     f"(line {syntax_error.lineno})")
    return _stage_receipt(STAGE_COMPILE_CHECK, passed=True, path=PATH_COMPILE_OK,
                          detail="compile(source, mode='exec') succeeded — syntactically valid Python")


def _open_call_mode(call_node: ast.Call) -> tuple[str, bool]:
    """The mode string of one ``open(...)`` AST call: ``(mode, known)``. Unknowable statically (non-constant
    mode, **kwargs, starred args) returns ``known=False`` — the screen then rejects on suspicion."""
    if any(isinstance(arg, ast.Starred) for arg in call_node.args[:OPEN_MODE_POSITIONAL_INDEX + 1]):
        return "", False
    mode_node: Optional[ast.expr] = None
    if len(call_node.args) > OPEN_MODE_POSITIONAL_INDEX:
        mode_node = call_node.args[OPEN_MODE_POSITIONAL_INDEX]
    else:
        for keyword in call_node.keywords:
            if keyword.arg == OPEN_MODE_KEYWORD:
                mode_node = keyword.value
            elif keyword.arg is None:  # **kwargs may smuggle a mode
                return "", False
    if mode_node is None:
        return OPEN_DEFAULT_MODE, True
    if isinstance(mode_node, ast.Constant) and isinstance(mode_node.value, str):
        return mode_node.value, True
    return "", False


def security_screen_stage(source: str) -> dict[str, Any]:
    """Stage 4: the deny-list screen — dangerous-construct substrings + an AST scan for open-for-write.
    Pure static analysis: this stage never executes the source. On a source that does not parse, the
    substring scan still runs and the receipt records ``ast_scanned=false`` honestly."""
    violations: list[str] = []
    for denied_construct in SECURITY_DENYLIST_SUBSTRINGS:
        if denied_construct in source:
            violations.append(f"denied construct present: {denied_construct!r}")
    ast_scanned = False
    try:
        parsed = ast.parse(source)
        ast_scanned = True
    except SyntaxError:
        parsed = None  # stage 2 already rejects this source; the substring verdict above still stands
    if parsed is not None:
        for node in ast.walk(parsed):
            if not isinstance(node, ast.Call):
                continue
            callee = node.func
            callee_name = (callee.id if isinstance(callee, ast.Name)
                           else callee.attr if isinstance(callee, ast.Attribute) else None)
            if callee_name != OPEN_BUILTIN_NAME:
                continue
            mode_value, mode_is_known = _open_call_mode(node)
            if not mode_is_known:
                violations.append("open() call with a statically-unknowable mode cannot be proven read-only")
            elif any(char in OPEN_WRITE_MODE_CHARS for char in mode_value):
                violations.append(f"open() call with write-capable mode {mode_value!r}")
    passed = not violations
    return _stage_receipt(STAGE_SECURITY_SCREEN, passed=passed,
                          path=PATH_SCREEN_CLEAN if passed else PATH_SCREEN_VIOLATIONS,
                          detail="deny-list substring scan + AST open-for-write scan (static only — no execution)",
                          violations=violations, ast_scanned=ast_scanned)


#: several structurally-varied probes (not one fixed string) — a body that transforms must move the VALUE
#: on at least one; identical-in==out on ALL of them is a semantic no-op (the audit's high-sev finding).
STAGE3_PROBES: tuple[Any, ...] = (
    STAGE3_SYNTHETIC_VALUE,
    {"id": "code-factory-probe-2", "amount": 42, "items": ["a", "b"], "nested": {"k": "v"}},
    ["code-factory", "probe", 3],
    "  Mixed CASE and spaces 4  ",
)


def _skeleton(source: str) -> str:
    """AST skeleton (names->N, literals->K) so 'this body is byte-for-byte the free identity template' is
    detectable regardless of the hardcoded output-type string — the 'no lift over the free stub' signal."""
    import ast  # noqa: PLC0415

    class _Norm(ast.NodeTransformer):
        def visit_Name(self, node):  # noqa: N802
            return ast.copy_location(ast.Name(id="N", ctx=node.ctx), node)

        def visit_Constant(self, node):  # noqa: N802
            return ast.copy_location(ast.Constant(value="K"), node)

    try:
        return ast.dump(_Norm().visit(ast.parse(source)), annotate_fields=False)
    except SyntaxError:
        return "<unparseable>"


def synthetic_self_test_stage(source: str, function_name: str, input_edge: str, output_edge: str, *,
                              compile_passed: bool, screen_passed: bool,
                              require_lift: bool = False, gap_spec: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    """Stage 3: exec the (compiled AND screened) source, call the function on SEVERAL varied input-edge
    envelopes, and assert the output envelope shape on each. A body that failed compile or screen is NEVER
    executed. ``require_lift`` (model fills) additionally FAILS a semantic no-op — a body whose output value
    equals its input value on every probe, OR whose AST skeleton equals the free identity template — because
    a model that returns the free stub added nothing (the audit's 29%-hollow finding). Template mints keep
    ``require_lift=False``: identity IS the honest stub they render."""
    if not compile_passed:
        return _stage_receipt(STAGE_SELF_TEST, passed=False, path=PATH_SELFTEST_SKIPPED_COMPILE,
                              detail="source failed the compile check — never executed")
    if not screen_passed:
        return _stage_receipt(STAGE_SELF_TEST, passed=False, path=PATH_SELFTEST_SKIPPED_SCREEN,
                              detail="source failed the security deny-list screen — an unscreened body is "
                                     "NEVER executed (the screen keeps the paper's stage-4 number but is "
                                     "computed before any exec)")
    namespace: dict[str, Any] = {"__name__": GENERATED_VIRTUAL_MODULE_NAME}
    try:
        exec(compile(source, GENERATED_VIRTUAL_FILENAME, COMPILE_MODE_EXEC), namespace)  # noqa: S102  screened source only
    except Exception as execution_error:  # noqa: BLE001  any runtime failure is a stage-3 reject, not a crash
        return _stage_receipt(STAGE_SELF_TEST, passed=False, path=PATH_SELFTEST_EXEC_ERROR,
                              detail=f"module exec raised {type(execution_error).__name__}: {execution_error}")
    generated_function = namespace.get(function_name)
    if not callable(generated_function):
        return _stage_receipt(STAGE_SELF_TEST, passed=False, path=PATH_SELFTEST_FN_MISSING,
                              detail=f"expected function {function_name!r} was not defined by the source")
    shape_failures: list[str] = []
    value_moved = False
    first_output_repr = ""
    for probe_index, probe_value in enumerate(STAGE3_PROBES):
        synthetic_input = {"type": input_edge, "value": probe_value}
        try:
            output_envelope = generated_function(synthetic_input)
        except Exception as call_error:  # noqa: BLE001
            return _stage_receipt(STAGE_SELF_TEST, passed=False, path=PATH_SELFTEST_EXEC_ERROR,
                                  detail=f"generated function call raised {type(call_error).__name__}: {call_error}"
                                         f" on probe {probe_index}")
        if probe_index == 0:
            first_output_repr = repr(output_envelope)
        if not isinstance(output_envelope, dict):
            shape_failures.append(f"probe {probe_index}: output is {type(output_envelope).__name__}, not a dict")
            continue
        if output_envelope.get("type") != output_edge:
            shape_failures.append(f"probe {probe_index}: output 'type' {output_envelope.get('type')!r} != {output_edge!r}")
        for flag, want in (("value", ...), ("candidate", True), ("serves_truth", False), ("needs_review", True)):
            if flag == "value":
                if "value" not in output_envelope:
                    shape_failures.append(f"probe {probe_index}: envelope missing 'value'")
            elif output_envelope.get(flag) is not want:
                shape_failures.append(f"probe {probe_index}: envelope '{flag}' must be {want}")
        if output_envelope.get("value") != probe_value:
            value_moved = True
    is_free_template = _skeleton(source) == _skeleton(render_gap_function_source(gap_spec or {})[0])
    lift_failures: list[str] = []
    if require_lift and input_edge != output_edge:
        if not value_moved:
            lift_failures.append("semantic no-op: output value equals input value on every probe while "
                                 f"input_edge {input_edge!r} != output_edge {output_edge!r}")
        if is_free_template:
            lift_failures.append("no lift: body AST is identical to the free identity template")
    passed = not shape_failures and not lift_failures
    return _stage_receipt(STAGE_SELF_TEST, passed=passed,
                          path=PATH_SELFTEST_OK if passed else PATH_SELFTEST_SHAPE_FAILED,
                          detail=f"executed on {len(STAGE3_PROBES)} varied input envelopes; shape asserted; "
                                 f"value_moved={value_moved}; free_template={is_free_template}; "
                                 f"lift_required={require_lift}",
                          output_repr=first_output_repr, shape_failures=shape_failures,
                          lift_failures=lift_failures, value_moved=value_moved, is_free_template=is_free_template)


# ══════════════════════════════════════════════════════════════════════════════════════════════════════════
# Model-backed fills: the prompt is DERIVED from the stage-3 contract (prompt and validator cannot drift).
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════
_FILL_MAX_TOKENS = 3000          # generous: reasoning models emit thinking before the function (a 700-token
                                 # cap silently truncated the first live fill — receipts 2026-07-06)


def build_fill_prompt(gap_spec: dict[str, Any]) -> tuple[str, str, str]:
    """The model prompt for a gap fill, rendered FROM the same template + stage-3 contract the validator
    enforces — hand-written prompts drifted from the contract on the first live runs (receipts: two
    rejections), so the contract terms here are the LITERAL values stage 3 asserts. Returns
    ``(prompt, template_source, function_name)``."""
    template_source, function_name = render_gap_function_source(gap_spec)
    input_edge = str(gap_spec.get("needed_input_type") or RENDER_UNTYPED_EDGE_FALLBACK)
    output_edge = str(gap_spec.get("needed_output_type") or RENDER_UNTYPED_EDGE_FALLBACK)
    contract_lines = [
        f"1. Keep the EXACT function name and signature: {function_name}(payload). Do not rename anything.",
        f"2. The input is a dict envelope {{'type': {input_edge!r}, 'value': ...}}; a bare value may also arrive.",
        f"3. Return a dict envelope with EXACTLY these keys present: 'type' == {output_edge!r}, 'value' (the",
        "   transformed payload), 'candidate': True, 'serves_truth': False, 'needs_review': True.",
        "4. Pure stdlib, NO imports, no I/O, no eval/exec/os/subprocess, deterministic.",
        "5. Implement a REASONABLE minimal transform for these edge types (never just raise).",
        "6. Return ONLY the complete function definition. No markdown fences, no prose.",
    ]
    prompt = ("Rewrite the BODY of this Python function. Contract (validated mechanically — violations are "
              "rejected):\n" + "\n".join(contract_lines) + "\n\nTemplate to fill:\n\n" + template_source)
    return prompt, template_source, function_name


def _strip_markdown_fences(text: str) -> str:
    lines = [l for l in text.strip().splitlines() if not l.strip().startswith("```")]
    return "\n".join(lines).strip()


def model_fill_gap(gap_spec: dict[str, Any], chat_fn: Any, model: str = "unknown_model") -> dict[str, Any]:
    """One model-backed fill through the FULL four-stage pipeline. ``chat_fn(prompt) -> str`` is the model
    seam (hermetic in the self-test; the CLI binds it to the OpenAI-compat endpoint). Provenance is recorded
    HONESTLY (fill_model, prompt hash) and stage 3 requires SEMANTIC LIFT (a no-op fill fails — a model that
    returns the free stub added nothing). The card is ALWAYS candidate/serves_truth=false/needs_review."""
    prompt, _template, _function_name = build_fill_prompt(gap_spec)
    generated = _strip_markdown_fences(str(chat_fn(prompt)))
    card = manufacture_candidate_card(gap_spec, source_override=generated,
                                      provenance={"fill_model": model, "require_lift": True,
                                                  "prompt_sha256": sha256_hex(prompt)})
    card["fill_mode"] = "model_backed"
    return card


# ══════════════════════════════════════════════════════════════════════════════════════════════════════════
# The card factory: gap spec -> four-stage pipeline -> one governed candidate card.
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════
def _card_blocking_keys(input_edge: str, output_edge: str) -> list[str]:
    """Lowercased edge tokens, the retrieval shape compose_solution's demo cards use — so a manufactured
    card can be fed straight back into the composer as a candidate card."""
    keys = [input_edge.lower(), output_edge.lower()]
    return keys if keys[0] != keys[1] else keys[:1]


def _card_blackbox(function_name: str, input_edge: str, output_edge: str) -> str:
    return (f"Generated narrow function {function_name}: consumes a {input_edge} envelope and emits a "
            f"{output_edge} envelope. The body is a typed identity/transform STUB rendered deterministically "
            f"from a model_step gap flag by the Compiled-AI Code Factory lane (template {TEMPLATE_ID}); its "
            "render/compile/self-test/security-screen results are recorded in generation_stage_receipts. It "
            "remains a reviewable CANDIDATE — needs_review=true, serves_truth=false; generation is never "
            "promotion.")


def manufacture_candidate_card(gap_spec: dict[str, Any], *, source_override: Optional[str] = None,
                               function_name_override: Optional[str] = None,
                               provenance: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    """Run the four-stage generation-and-validation pipeline for one gap spec and return the candidate CARD.

    ``source_override`` supplies a body from ELSEWHERE (a model fill, or the self-test's defect injection);
    ``provenance`` records WHERE it came from honestly (fill_mode/model/require_lift) so the render receipt
    never lies about origin (the audit's provenance-fabrication finding). When provenance says the body was
    model-generated (``require_lift=True``), stage 3 additionally rejects a semantic no-op. The card is
    emitted even when a stage fails — the failing receipts ARE the record (lossless) — and it is ALWAYS
    candidate=true / serves_truth=false / needs_review=true. ``body_status`` labels it for the index."""
    input_edge = str(gap_spec.get("needed_input_type") or RENDER_UNTYPED_EDGE_FALLBACK)
    output_edge = str(gap_spec.get("needed_output_type") or RENDER_UNTYPED_EDGE_FALLBACK)
    rendered_source, rendered_function_name = render_gap_function_source(gap_spec)
    source = rendered_source if source_override is None else source_override
    function_name = function_name_override or rendered_function_name
    prov = provenance or {}
    is_model = bool(prov.get("fill_model"))
    is_defect_injection = source_override is not None and not is_model and not prov.get("origin")
    require_lift = bool(prov.get("require_lift", is_model))  # model fills must lift; template mints need not

    if source_override is None:
        render_path, render_detail = PATH_RENDERED_FROM_GAP_SPEC, \
            "deterministic template fill from the gap spec — no model call; the body is a reviewable stub"
    elif is_model:
        render_path, render_detail = "model_fill", \
            f"body generated by model {prov.get('fill_model')!r}; a reviewable candidate, NOT a template stub"
    elif prov.get("origin"):
        render_path, render_detail = str(prov["origin"]), f"body supplied by {prov['origin']!r}"
    else:
        render_path, render_detail = PATH_OVERRIDE_INJECTED, "defect-injected body (self-test mutation gate)"
    render_receipt = _stage_receipt(
        STAGE_RENDER, passed=True, path=render_path, detail=render_detail,
        template_id=None if is_model else TEMPLATE_ID, source_sha256=sha256_hex(source),
        fill_model=prov.get("fill_model"), prompt_sha256=prov.get("prompt_sha256"),
        codegen_contract=codegen_contract_stamp(), input_edge=input_edge, output_edge=output_edge)
    compile_receipt = compile_check_stage(source)
    screen_receipt = security_screen_stage(source)  # computed BEFORE any exec — stage 3 refuses unscreened source
    self_test_receipt = synthetic_self_test_stage(source, function_name, input_edge, output_edge,
                                                  compile_passed=compile_receipt["passed"],
                                                  screen_passed=screen_receipt["passed"],
                                                  require_lift=require_lift, gap_spec=gap_spec)
    _ = is_defect_injection
    receipts = [render_receipt, compile_receipt, self_test_receipt, screen_receipt]  # the paper's stage order
    all_stages_passed = all(receipt["passed"] for receipt in receipts)
    # body_status labels the card for the index/compose lanes so a stub is never mistaken for a real producer
    # (the integration audit's core ask). identity_stub = the free template (honest, needs_review); model_fill
    # = a lifted model body that passed the semantic-lift gate; failed = a rejected candidate.
    if not all_stages_passed:
        body_status = "failed_validation"
    elif self_test_receipt.get("is_free_template") or not self_test_receipt.get("value_moved"):
        body_status = "identity_stub"
    elif is_model:
        body_status = "model_fill_lifted"
    else:
        body_status = "supplied_lifted"
    return {
        "record_type": CARD_RECORD_TYPE,
        "schema_version": CARD_SCHEMA_VERSION,
        "primitive_id": canonical_id(CARD_ID_PREFIX, source),  # sha256 of content via the one id authority
        "kind": CARD_KIND_ACTION,
        "title": (f"[STUB needs_review] {input_edge} -> {output_edge}" if body_status == "identity_stub"
                  else f"generated candidate transform: {input_edge} -> {output_edge}"),
        "input_edge": input_edge,
        "output_edge": output_edge,
        "blocking_keys": _card_blocking_keys(input_edge, output_edge),
        "blackbox": _card_blackbox(function_name, input_edge, output_edge),
        "generated_function_name": function_name,
        "generated_source": source,
        "source_sha256": sha256_hex(source),
        "generation_stage_receipts": receipts,
        "all_stages_passed": all_stages_passed,
        "body_status": body_status,          # identity_stub | model_fill_lifted | supplied_lifted | failed_validation
        "fill_model": prov.get("fill_model"),
        "gap_spec": dict(gap_spec),  # lineage: the flag that caused this card, preserved verbatim
        "needs_review": NEEDS_REVIEW_ALWAYS,
        **BOUNDARY,
    }


def card_boundary_violations(card: dict[str, Any]) -> list[str]:
    """The tamper/consistency guard: a WRONG artifact yields violations (the self-test's mutation gate).
    Checks the candidate/truth boundary flags, the content-minted primitive_id, the source hash, and the
    stage-receipt order/consistency."""
    violations: list[str] = []
    if card.get("candidate") is not True:
        violations.append("candidate must be True — generation is never promotion")
    if card.get("serves_truth") is not False:
        violations.append("serves_truth must be False on every generated card")
    if card.get("needs_review") is not True:
        violations.append("needs_review must be True — the stub body is never executable-as-truth")
    if card.get("record_type") != CARD_RECORD_TYPE:
        violations.append(f"record_type must be {CARD_RECORD_TYPE!r}")
    source = card.get("generated_source") or ""
    if card.get("primitive_id") != canonical_id(CARD_ID_PREFIX, source):
        violations.append("primitive_id does not match the content hash of generated_source")
    if card.get("source_sha256") != sha256_hex(source):
        violations.append("source_sha256 does not match generated_source")
    receipts = card.get("generation_stage_receipts") or []
    if [receipt.get("stage") for receipt in receipts] != list(STAGE_ORDER):
        violations.append("generation_stage_receipts must carry all four stages in order")
    if card.get("all_stages_passed") != all(receipt.get("passed") is True for receipt in receipts):
        violations.append("all_stages_passed is inconsistent with the stage receipts")
    return violations


# ══════════════════════════════════════════════════════════════════════════════════════════════════════════
# The lane: intent -> compose_solution (existing engine) -> gap specs -> candidate cards.
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════
def run_code_factory_lane(intent: str, *, candidate_cards: Optional[list[dict[str, Any]]] = None,
                          index: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    """Run compose_solution for ``intent`` and manufacture one candidate card per flagged model_step gap."""
    from scripts.primitive_runtime import compose_solution  # noqa: PLC0415  lazy: heavy sibling engine, loaded only when the lane runs
    kwargs: dict[str, Any] = {}
    if candidate_cards is not None:
        kwargs["candidate_cards"] = candidate_cards
    if index is not None:
        kwargs["index"] = index
    solution = compose_solution(intent, **kwargs)
    gaps = extract_model_step_gaps(solution)
    cards = [manufacture_candidate_card(gap) for gap in gaps]
    return {
        "record_type": LANE_RECORD_TYPE,
        "intent": intent,
        "route_found": bool((solution.get("route") or {}).get("route_found")),
        "model_step_gap_count": len(gaps),
        "cards": cards,
        "compose_step_log": solution.get("step_log") or [],  # lineage back into the composer run
        **BOUNDARY,
    }


def _iter_record_rows(obj: Any) -> Iterator[dict[str, Any]]:
    """Every nested dict carrying a record_type — the boundary sweep the self-test runs over a lane result."""
    if isinstance(obj, dict):
        if obj.get("record_type"):
            yield obj
        for value in obj.values():
            yield from _iter_record_rows(value)
    elif isinstance(obj, list):
        for value in obj:
            yield from _iter_record_rows(value)


# ══════════════════════════════════════════════════════════════════════════════════════════════════════════
# Self-test — hermetic; includes MUTATION gates (injected defects fail their own stage; a tampered card is
# detected) and a determinism gate (byte-identical twice). Fixture mirrors primitive_runtime's own gap test.
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════
SELF_TEST_GAP_INTENT = "from AlphaUniqueType to OmegaUniqueType"
SELF_TEST_GAP_INPUT_EDGE = "AlphaUniqueType"
SELF_TEST_GAP_MID_EDGE = "MidUniqueType"
SELF_TEST_GAP_OUTPUT_EDGE = "OmegaUniqueType"
SELF_TEST_GAP_CARDS: tuple[dict[str, Any], ...] = ({
    "primitive_id": "prim:code-factory-self-test-alpha-to-mid",
    "title": f"self-test producer: {SELF_TEST_GAP_INPUT_EDGE} to {SELF_TEST_GAP_MID_EDGE}",
    "input_edge": SELF_TEST_GAP_INPUT_EDGE,
    "output_edge": SELF_TEST_GAP_MID_EDGE,
    "blocking_keys": [SELF_TEST_GAP_INPUT_EDGE.lower(), SELF_TEST_GAP_MID_EDGE.lower()],
    **BOUNDARY,
},)

# injected-defect bodies — each one targets EXACTLY one stage (never executed unless it passes the screen):
DANGEROUS_BODY_FUNCTION_NAME = f"py_function__{GENERATED_VIRTUAL_FILE_TAG}__module__dangerous_body_for_self_test"
DANGEROUS_BODY_FOR_SELF_TEST = (
    "import os\n"
    f"def {DANGEROUS_BODY_FUNCTION_NAME}(payload):\n"
    "    os.system('echo this-line-must-never-run')\n"
    "    return payload\n"
)
SYNTAX_BROKEN_BODY_FOR_SELF_TEST = (
    f"def py_function__{GENERATED_VIRTUAL_FILE_TAG}__module__broken_body_for_self_test(:\n"
    "    return None\n"
)
WRONG_SHAPE_FUNCTION_NAME = f"py_function__{GENERATED_VIRTUAL_FILE_TAG}__module__wrong_shape_body_for_self_test"
WRONG_SHAPE_BODY_FOR_SELF_TEST = (
    f"def {WRONG_SHAPE_FUNCTION_NAME}(payload):\n"
    "    return {'type': 'DeliberatelyWrongOutputType', 'value': None}\n"
)
OPEN_WRITE_FUNCTION_NAME = f"py_function__{GENERATED_VIRTUAL_FILE_TAG}__module__open_write_body_for_self_test"
OPEN_WRITE_BODY_FOR_SELF_TEST = (
    f"def {OPEN_WRITE_FUNCTION_NAME}(payload):\n"
    "    open('never-created.txt', 'w')\n"
    "    return payload\n"
)
OPEN_READ_BODY_FOR_SELF_TEST = (  # read-mode open() must NOT trip the open-for-write rule
    f"def py_function__{GENERATED_VIRTUAL_FILE_TAG}__module__open_read_body_for_self_test(payload):\n"
    "    if payload is None:\n"
    "        open('never-opened.txt')\n"
    "    return payload\n"
)
TAMPER_SUFFIX_FOR_SELF_TEST = "\n# tampered-after-minting"  # content change WITHOUT re-minting the id


def _self_test() -> int:
    checks: list[tuple[str, bool]] = []

    # ── the lane sits over the REAL gap flagger: intent -> model_step flag -> manufactured card ──
    lane = run_code_factory_lane(SELF_TEST_GAP_INTENT, candidate_cards=list(SELF_TEST_GAP_CARDS))
    checks.append(("compose_solution flags the missing edge and the lane extracts exactly one gap spec",
                   lane["model_step_gap_count"] == 1 and len(lane["cards"]) == 1
                   and lane["cards"][0]["gap_spec"]["needed_output_type"] == SELF_TEST_GAP_OUTPUT_EDGE))
    card = lane["cards"][0]
    checks.append(("the manufactured card passes ALL four generation stages, receipts in stage order",
                   card["all_stages_passed"] is True
                   and [receipt["stage"] for receipt in card["generation_stage_receipts"]] == list(STAGE_ORDER)
                   and all(receipt["passed"] for receipt in card["generation_stage_receipts"])))
    checks.append(("the card is a governed candidate: candidate=true serves_truth=false needs_review=true",
                   card["candidate"] is True and card["serves_truth"] is False and card["needs_review"] is True))
    checks.append(("primitive_id is minted from content (sha256 via the canonical_id authority)",
                   card["primitive_id"] == canonical_id(CARD_ID_PREFIX, card["generated_source"])
                   and card["primitive_id"].startswith(f"{CARD_ID_PREFIX}-")))
    checks.append(("the generated function follows the codegen naming contract (py_function__… scheme)",
                   card["generated_function_name"].startswith(GENERATED_FUNCTION_NAME_PREFIX)))
    render_receipt = card["generation_stage_receipts"][0]
    checks.append(("the render receipt stamps the codegen contract provenance honestly",
                   render_receipt["codegen_contract"]["contract_path"] == CODEGEN_CONTRACTS_RELPATH
                   and (not render_receipt["codegen_contract"]["present"]
                        or bool(render_receipt["codegen_contract"]["naming_law"]))))

    # ── functional closure: feeding the manufactured card back CLOSES the flagged gap ──
    from scripts.primitive_runtime import compose_solution  # noqa: PLC0415
    reclosed = compose_solution(SELF_TEST_GAP_INTENT, candidate_cards=list(SELF_TEST_GAP_CARDS) + [card])
    checks.append(("feeding the manufactured card back closes the gap (route_found flips False -> True)",
                   lane["route_found"] is False and reclosed["route"]["route_found"] is True))

    # ── MUTATION gates: each injected defect fails its OWN stage ──
    gap = card["gap_spec"]
    dangerous = manufacture_candidate_card(gap, source_override=DANGEROUS_BODY_FOR_SELF_TEST,
                                           function_name_override=DANGEROUS_BODY_FUNCTION_NAME)
    dangerous_receipts = {receipt["stage"]: receipt for receipt in dangerous["generation_stage_receipts"]}
    checks.append(("MUTATION: an injected dangerous body FAILS stage 4 (security screen) and is NEVER executed",
                   dangerous["all_stages_passed"] is False
                   and dangerous_receipts[STAGE_SECURITY_SCREEN]["passed"] is False
                   and dangerous_receipts[STAGE_SELF_TEST]["path"] == PATH_SELFTEST_SKIPPED_SCREEN))
    broken = manufacture_candidate_card(gap, source_override=SYNTAX_BROKEN_BODY_FOR_SELF_TEST)
    broken_receipts = {receipt["stage"]: receipt for receipt in broken["generation_stage_receipts"]}
    checks.append(("MUTATION: a syntax-broken body FAILS stage 2 (compile check) and is never executed",
                   broken["all_stages_passed"] is False
                   and broken_receipts[STAGE_COMPILE_CHECK]["passed"] is False
                   and broken_receipts[STAGE_SELF_TEST]["path"] == PATH_SELFTEST_SKIPPED_COMPILE))
    wrong = manufacture_candidate_card(gap, source_override=WRONG_SHAPE_BODY_FOR_SELF_TEST,
                                       function_name_override=WRONG_SHAPE_FUNCTION_NAME)
    wrong_receipts = {receipt["stage"]: receipt for receipt in wrong["generation_stage_receipts"]}
    checks.append(("MUTATION: a clean-compiling body with the WRONG output shape FAILS stage 3 (self-test)",
                   wrong["all_stages_passed"] is False
                   and wrong_receipts[STAGE_SELF_TEST]["passed"] is False
                   and wrong_receipts[STAGE_SELF_TEST]["path"] == PATH_SELFTEST_SHAPE_FAILED
                   and wrong_receipts[STAGE_COMPILE_CHECK]["passed"] is True
                   and wrong_receipts[STAGE_SECURITY_SCREEN]["passed"] is True))
    open_write = manufacture_candidate_card(gap, source_override=OPEN_WRITE_BODY_FOR_SELF_TEST,
                                            function_name_override=OPEN_WRITE_FUNCTION_NAME)
    open_write_receipts = {receipt["stage"]: receipt for receipt in open_write["generation_stage_receipts"]}
    checks.append(("MUTATION: open-for-write trips the AST screen while read-mode open() does not",
                   open_write_receipts[STAGE_SECURITY_SCREEN]["passed"] is False
                   and open_write_receipts[STAGE_SELF_TEST]["path"] == PATH_SELFTEST_SKIPPED_SCREEN
                   and security_screen_stage(OPEN_READ_BODY_FOR_SELF_TEST)["passed"] is True))
    # MUTATION: the SEMANTIC-LIFT gate — a compiling, screened, correctly-SHAPED body that returns the input
    # unchanged (a no-op) FAILS under require_lift; the same body with a real transform PASSES and lifts.
    lift_gap = {"needed_input_type": "AlphaType", "needed_output_type": "OmegaType"}
    _lift_tmpl, lift_fn = render_gap_function_source(lift_gap)
    noop_body = (f"def {lift_fn}(payload):\n"
                 "    value = payload.get('value') if isinstance(payload, dict) else payload\n"
                 "    return {'type': 'OmegaType', 'value': value, 'candidate': True, "
                 "'serves_truth': False, 'needs_review': True}\n")
    noop_card = manufacture_candidate_card(lift_gap, source_override=noop_body,
                                           provenance={"fill_model": "test-model", "require_lift": True})
    noop_s3 = {r["stage"]: r for r in noop_card["generation_stage_receipts"]}[STAGE_SELF_TEST]
    checks.append(("MUTATION: a semantic NO-OP model fill FAILS the lift gate (audit's 29%-hollow fix)",
                   noop_card["all_stages_passed"] is False and noop_s3["passed"] is False
                   and bool(noop_s3.get("lift_failures")) and noop_card["body_status"] == "failed_validation"))
    real_body = (f"def {lift_fn}(payload):\n"
                 "    value = payload.get('value') if isinstance(payload, dict) else payload\n"
                 "    out = {'wrapped': value} if not isinstance(value, dict) else {**value, 'omega': True}\n"
                 "    return {'type': 'OmegaType', 'value': out, 'candidate': True, "
                 "'serves_truth': False, 'needs_review': True}\n")
    real_card = manufacture_candidate_card(lift_gap, source_override=real_body,
                                           provenance={"fill_model": "test-model", "require_lift": True})
    checks.append(("a REAL model transform lifts and passes all four stages (body_status=model_fill_lifted)",
                   real_card["all_stages_passed"] is True and real_card["body_status"] == "model_fill_lifted"))
    # HONEST PROVENANCE: a model fill records the model + non-template origin, never the fake "no model call"
    real_render = {r["stage"]: r for r in real_card["generation_stage_receipts"]}[STAGE_RENDER]
    checks.append(("model-fill provenance is HONEST (audit's fabrication fix)",
                   real_render["path"] == "model_fill" and real_render.get("fill_model") == "test-model"
                   and real_render.get("template_id") is None and real_card.get("fill_model") == "test-model"))
    # the template stub is honestly an identity_stub (require_lift=False — identity IS the honest stub)
    stub_card = manufacture_candidate_card(lift_gap)
    checks.append(("a template mint is labeled identity_stub and still passes (needs_review honest stub)",
                   stub_card["all_stages_passed"] is True and stub_card["body_status"] == "identity_stub"
                   and stub_card["title"].startswith("[STUB needs_review]")))

    # ── MUTATION gate on the artifact itself: a wrong card makes the guard go red ──
    checks.append(("a genuine passing card carries zero boundary violations",
                   card_boundary_violations(card) == []))
    tampered_promotion = {**card, "serves_truth": True}
    tampered_content = {**card, "generated_source": card["generated_source"] + TAMPER_SUFFIX_FOR_SELF_TEST}
    checks.append(("MUTATION: flipping serves_truth or tampering content WITHOUT re-minting is detected",
                   any("serves_truth" in violation for violation in card_boundary_violations(tampered_promotion))
                   and any("primitive_id" in violation for violation in card_boundary_violations(tampered_content))))

    # ── determinism gate: byte-identical twice (no RNG, no wall-clock in any id/key) ──
    lane_again = run_code_factory_lane(SELF_TEST_GAP_INTENT, candidate_cards=list(SELF_TEST_GAP_CARDS))
    card_again = manufacture_candidate_card(gap)
    checks.append(("deterministic: the same gap yields a byte-identical card and lane result twice",
                   json.dumps(lane, sort_keys=True).encode("utf-8")
                   == json.dumps(lane_again, sort_keys=True).encode("utf-8")
                   and json.dumps(card_again, sort_keys=True) == json.dumps(card, sort_keys=True)))

    # ── boundary sweep: every emitted record row is candidate=true / serves_truth=false ──
    emitted_rows = list(_iter_record_rows(lane))
    checks.append(("boundary held: every emitted row is candidate=true / serves_truth=false",
                   bool(emitted_rows) and all(row.get("candidate") is True and row.get("serves_truth") is False
                                              for row in emitted_rows)))

    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(("PASS" if ok else "FAIL") + f" — {name}")
    verdict = "PASS" if not failed else "FAIL"
    print(f"code_factory_lane --self-test: {verdict} ({len(checks) - len(failed)}/{len(checks)} checks)")
    return 0 if not failed else 1


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Compiled-AI Code Factory lane: render+validate a candidate function for every "
                    "model_step gap compose_solution flags (candidate-only; generation is never promotion).")
    parser.add_argument("--self-test", action="store_true",
                        help="run the hermetic self-test (mutation + determinism gates)")
    parser.add_argument("--intent", default=None,
                        help="run the lane over one intent against the persisted search index (demo)")
    parser.add_argument("--race-staged", type=int, default=0, metavar="N",
                        help="model-fill the first N staged unmet-edge gaps, racing every --models entry")
    parser.add_argument("--models", default="kimi-k2.7-code,glm-5.2,qwen3-coder:480b",
                        help="comma-separated Ollama Cloud model ids to race (multi-path: rows, receipts)")
    parser.add_argument("--gaps-file", default=None,
                        help="JSONL of gap specs ({needed_input_type, needed_output_type}) to fill instead of "
                             "the staged producer cards — the supply seam for demand-ranked unmet edges")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.intent:
        print(json.dumps(run_code_factory_lane(args.intent), indent=2, sort_keys=True))
        return 0
    if args.race_staged:
        return _race_staged(args.race_staged, [m.strip() for m in args.models.split(",") if m.strip()],
                            gaps_file=args.gaps_file)
    parser.print_help()
    return 0


def _race_staged(n: int, models: list[str], gaps_file: str | None = None) -> int:
    """RACE models over the staged unmet-edge gaps through the full pipeline — per-model pass-rate receipts
    (the multi-path law applied to generation), validated cards appended, losers kept as labelled rows."""
    import concurrent.futures
    import os
    import urllib.request
    from scripts._repo_paths import resource

    staged = (Path(gaps_file) if gaps_file
              else resource("data") / "dev-intel" / "domain_token_savings" / "staged_producer_candidates.jsonl")
    gaps: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for line in staged.read_text().splitlines():
        try:
            card = json.loads(line)
        except json.JSONDecodeError:
            continue
        needed_in = card.get("needed_input_type") or card.get("input_edge")
        needed_out = card.get("needed_output_type") or card.get("output_edge")
        key = (str(needed_in), str(needed_out))
        if key in seen or not needed_out:
            continue
        seen.add(key)
        gaps.append({"needed_input_type": needed_in, "needed_output_type": needed_out})
    gaps = gaps[:n]

    from scripts.runtime.secret_resolve import resolve, resolve_required  # noqa: PLC0415  THE secret chokepoint

    api_key = resolve_required("OLLAMA_API_KEY")  # via the chokepoint — never a direct env read
    base_url = str(resolve("OH_LLM_BASE_URL", default="https://ollama.com/v1"))

    def _chat(model: str, prompt: str) -> str:
        req = urllib.request.Request(
            base_url.rstrip("/") + "/chat/completions",
            data=json.dumps({"model": model, "messages": [{"role": "user", "content": prompt}],
                             "max_tokens": _FILL_MAX_TOKENS, "temperature": 0}).encode(),
            headers={"Authorization": "Bearer " + api_key,
                     "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=240) as resp:
            return json.load(resp)["choices"][0]["message"]["content"]

    def _one(model: str, gap: dict[str, Any]) -> dict[str, Any]:
        try:
            card = model_fill_gap(gap, lambda prompt: _chat(model, prompt), model=model)
            return card
        except Exception as fill_error:  # noqa: BLE001 — a lane/network fault is a receipt row, not a crash
            return {"fill_model": model, "gap_spec": gap, "error": f"{type(fill_error).__name__}: {fill_error}",
                    "generation_stage_receipts": [], "candidate": True, "serves_truth": False}

    out = staged.parent / "model_backed_factory_cards.jsonl"
    per_model: dict[str, dict[str, int]] = {m: {"all4_pass": 0, "stage3_fail": 0, "other_fail": 0, "error": 0}
                                            for m in models}
    seen_ids: set[str] = set()
    if out.exists():
        for line in out.read_text().splitlines():
            try:
                seen_ids.add(json.loads(line).get("primitive_id"))
            except json.JSONDecodeError:
                continue
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool, out.open("a", encoding="utf-8") as fh:
        futures = [pool.submit(_one, m, g) for m in models for g in gaps]
        for fut in concurrent.futures.as_completed(futures):
            card = fut.result()
            pid = card.get("primitive_id")
            if pid and pid in seen_ids:  # dedup: never write the same content-hashed body twice
                continue
            if pid:
                seen_ids.add(pid)
            fh.write(json.dumps(card, sort_keys=True, default=str) + "\n")
            model = card["fill_model"]
            receipts = {r["stage"]: r["passed"] for r in card.get("generation_stage_receipts", [])}
            if card.get("error"):
                per_model[model]["error"] += 1
            elif receipts and all(receipts.values()):
                per_model[model]["all4_pass"] += 1
            elif receipts.get("stage3_self_test") is False:
                per_model[model]["stage3_fail"] += 1
            else:
                per_model[model]["other_fail"] += 1
    summary = {"record_type": "model_fill_race_receipt", "gaps_raced": len(gaps), "models": models,
               "per_model": per_model, "cards_appended_to": str(out), "candidate": True, "serves_truth": False}
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
