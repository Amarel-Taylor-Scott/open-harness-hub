#!/usr/bin/env python3
"""scripts.real_buildout_ab_harness — the REAL comparison the proxy benchmark cannot give: send the SAME
buildout prompt to a real cloud model twice — BARE vs REGISTRY-ASSISTED (top-k retrieved primitive cards +
verified executable primitives injected as a reuse scaffold) — then EXECUTE both lanes' outputs and compare
runtime results, not just token counts:

  * lanes run on the BIG models via the shared provider chain (Ollama Cloud GLM 5.2 / Kimi large-context,
    gemma-4-coding through the OpenWebUI CDP bridge, NVIDIA GLM) — NEVER local gemma4 (8GB GPU: cannot hold
    honest long-form, long-context generations; owner law 2026-07-07);
  * REAL token accounting from the API usage payloads (prompt/completion); the CDP bridge lane is labelled
    token_source=approx_chars;
  * every turn's output contract is runnable Python files in fenced blocks + a pytest file; the sandbox
    compiles every file, runs the tests, and CROSS-TESTS lane A's tests against lane B's implementation and
    vice versa — same inputs, compared outcomes, captured errors and diffs;
  * receipts per turn + per session under data/dev-intel/real_buildout_ab/<run_id>/ (tokens, compile rate,
    self-test pass, cross-test agreement, error texts). candidate=true, serves_truth=false.

Scenarios/code-states come from run_realistic_session_benchmarks (same templates: SaaS control planes,
warehouses, ML lifecycle, Kaggle projects, hyperscale monolith slices; greenfield -> brownfield states), so
the proxy lane and the real lane measure the SAME projects.

    python3 scripts/real_buildout_ab_harness.py --self-test
    python3 scripts/real_buildout_ab_harness.py --list
    python3 scripts/real_buildout_ab_harness.py --run --scenario kaggle_tabular_competition \\
        --code-state mid_build --turns 2 --providers ollama,openwebui_cdp --model glm-5.2 --k 6
"""
from __future__ import annotations

import sys
from pathlib import Path

_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots, resource  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import hashlib  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import re  # noqa: E402
import shutil  # noqa: E402
import subprocess  # noqa: E402
import tempfile  # noqa: E402
import time  # noqa: E402
from typing import Any, Callable, Optional  # noqa: E402

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
_OUT_DIRNAME = "real_buildout_ab"
_DEFAULT_MAX_TOKENS = 6000
_MAX_CONTINUATIONS = 3  # cap-survival: reassemble long-form outputs across calls on output-capped lanes
_SANDBOX_TIMEOUT_S = 180
_CODE_BLOCK_RE = re.compile(r"```python(?:[ \t]+filename=([^\s`]+))?\s*\n(.*?)```", re.DOTALL)
#: local gemma4 is BANNED for real comparisons (8GB GPU understates baselines); cloud lanes only.
_FORBIDDEN_MODELS = frozenset({"gemma4", "gemma4:latest"})

_OUTPUT_CONTRACT = (
    "OUTPUT CONTRACT: respond ONLY with complete runnable Python files in fenced blocks of the form\n"
    "```python filename=<relative/path.py>\\n<code>\\n``` . Include exactly one tests file\n"
    "```python filename=tests/test_main.py``` with pytest-style test functions that exercise the required\n"
    "behavior through the public entry points in main.py (import from main). No prose outside code blocks,\n"
    "no placeholders, no TODOs — every file must run as written."
)


# ── scenario + retrieval plumbing (reuse the proxy benchmark's templates so both lanes measure the same jobs) ─
def _bench():  # lazy: importing the bench module is cheap but keep the seam single
    from scripts import run_realistic_session_benchmarks as bench  # noqa: PLC0415
    return bench


def list_scenarios() -> list[dict[str, str]]:
    bench = _bench()
    return [{"template_id": t["template_id"], "category": t["category"], "turns": len(t["turns"])}
            for t in bench.SCENARIO_TEMPLATES]


def build_turn_prompts(scenario: str, code_state: str, turns: int) -> list[dict[str, Any]]:
    bench = _bench()
    template = next((t for t in bench.SCENARIO_TEMPLATES if t["template_id"] == scenario), None)
    if template is None:
        raise ValueError(f"unknown scenario {scenario!r}; see --list")
    states = {c[0]: c for c in bench.CODE_STATE_VARIANTS}
    if code_state not in states:
        raise ValueError(f"unknown code state {code_state!r}; have {sorted(states)}")
    _label, code_context, _mult = states[code_state]
    out = []
    for stage, surface, prompt, _base_tokens in template["turns"][:turns or None]:
        out.append({"stage": stage, "surface": surface,
                    "prompt": f"{template['title']} {code_context} Task: {prompt}\n\n{_OUTPUT_CONTRACT}"})
    return out


def load_exec_cards() -> list[dict[str, Any]]:
    """Verified EXECUTABLE primitives (oracle-tested working code) — the material the orchestrator composes.
    Sources: the executable library + the string-standardization pack (atoms AND composites-of-atoms)."""
    cards: list[dict[str, Any]] = []
    for loader in ("scripts.executable_primitive_library", "scripts.string_standardization_primitives",
                   "scripts.ui_design_primitives", "scripts.party_name_primitives",
                   "scripts.dummy_data_detection_primitives", "scripts.quantity_money_primitives",
                   "scripts.cross_table_discovery_primitives", "scripts.temporal_cdc_primitives",
                   "scripts.feature_comparison_primitives", "scripts.similarity_typo_primitives",
                   "scripts.matching_scorecard_primitives"):
        try:
            mod = __import__(loader, fromlist=["all_cards"])
            cards.extend(c for c in mod.all_cards() if c.get("executable_body"))
        except Exception:  # noqa: BLE001 — each pack optional
            continue
    return cards


def retrieve_scaffold(prompt: str, cards: list[dict[str, Any]], *, k: int,
                      exec_cards: Optional[list[dict[str, Any]]] = None) -> tuple[str, list[str]]:
    """Reuse scaffold: top-k knowledge cards by intent + EVERY executable primitive's callable signature.
    Returns (scaffold text, retrieved knowledge-card ids)."""
    from scripts.capability_embedding import intent_query  # noqa: PLC0415
    hits = intent_query(prompt, cards, k=k) if cards else []
    ids = [str(h.get("primitive_id") or "") for h in hits]
    lines = ["VERIFIED PRIMITIVE REGISTRY SCAFFOLD:", "", "EXECUTABLE PRIMITIVES (already implemented; "
             "available for import from the module `primitives_lib` under the python name shown):"]
    for c in exec_cards if exec_cards is not None else load_exec_cards():
        head = next((ln for ln in str(c["executable_body"]).splitlines() if ln.startswith(("def ", "class "))), "")
        lines.append(f"- [{c.get('primitive_id')}] python name `{c.get('impl_name')}` :: "
                     f"{str(c.get('title') or '')[:120]} :: {head[:140]}")
    lines.append("")
    lines.append("KNOWLEDGE PRIMITIVES (design references — what exists, its interface edges):")
    for h in hits:
        pid = str(h.get("primitive_id") or "")
        card = h if h.get("title") else next((c for c in cards if c.get("primitive_id") == pid), {})
        lines.append(f"- [{pid}] {card.get('title', '')} :: {str(card.get('blackbox') or '')[:200]} "
                     f"(input: {card.get('input_edge')}, output: {card.get('output_edge')})")
    return "\n".join(lines), ids


_ORCHESTRATOR_CONTRACT = (
    "YOU ARE THE ORCHESTRATOR, NOT THE IMPLEMENTER. The executable primitives listed above are ALREADY "
    "IMPLEMENTED and will be injected verbatim as a module named primitives_lib — never rewrite or re-derive "
    "their code. Respond with:\n"
    "1) exactly one ```json block: {\"use_primitives\": [\"<primitive_id>\", ...]} — the executable "
    "primitives you compose, in wiring order;\n"
    "2) ```python filename=main.py``` — THIN glue only: import the chosen primitives from primitives_lib "
    "and wire them into the required behavior (plus only the small pieces no primitive covers);\n"
    "3) ```python filename=tests/test_main.py``` — pytest tests through main's public entry points.\n"
    "The heavy lifting must come from primitives_lib; your output should be dramatically smaller than a "
    "full implementation.")
_USE_PRIMITIVES_RE = re.compile(r"```json\s*\n(.*?)```", re.DOTALL)


def parse_plan_ids(text: str) -> list[str]:
    for block in _USE_PRIMITIVES_RE.findall(text or ""):
        try:
            ids = json.loads(block).get("use_primitives")
            if isinstance(ids, list):
                return [str(i) for i in ids]
        except (ValueError, AttributeError):
            continue
    return []


def materialize_primitives_lib(plan_ids: list[str], exec_cards: list[dict[str, Any]]) -> tuple[str, list[str]]:
    """Assemble primitives_lib.py from the plan's VERIFIED implementations (verbatim; 0 generated tokens)."""
    by_id = {str(c.get("primitive_id")): c for c in exec_cards}
    bodies, used = [], []
    for pid in plan_ids:
        c = by_id.get(pid)
        if c:
            used.append(pid)
            bodies.append(f"# [{pid}] {str(c.get('title') or '')[:100]} — verified registry implementation\n"
                          f"{c['executable_body'].rstrip()}\n")
    header = '"""primitives_lib — verified executable primitives injected verbatim from the registry."""\n\n'
    return header + "\n\n".join(bodies), used


def load_registry_cards(limit: int = 0) -> list[dict[str, Any]]:
    return _bench()._load_base_cards(limit)  # noqa: SLF001 — the bench loader IS the corpus seam


# ── transport: shared cloud-lane chain with REAL usage capture ────────────────────────────────────────────────
def make_transport(providers: list[str], model: str) -> Callable[[str, str], dict[str, Any]]:
    if model in _FORBIDDEN_MODELS:
        raise ValueError(f"{model!r} is the LOCAL gemma4 (8GB GPU) — real comparisons run on the cloud lanes "
                         f"(glm-5.2 / kimi / gemma-4-coding via openwebui_cdp / nvidia)")
    from scripts import _llm_client  # noqa: PLC0415
    resolved: list[tuple[str, Optional[dict]]] = []
    for n in providers:
        resolved.append((n, None if n == "openwebui_cdp" else _llm_client.resolve_provider(n)))

    def _call(system: str, user: str) -> dict[str, Any]:
        last = ""
        for name, prov in resolved:
            try:
                if name == "openwebui_cdp":
                    from scripts.openwebui_cdp_bridge import cdp_chat  # noqa: PLC0415
                    m = model if model.startswith("gemma") else "gemma-4-coding"
                    r = cdp_chat(m, system, user)
                    if r.get("ok") and (r.get("text") or "").strip():
                        text = r["text"]
                        return {"ok": True, "text": text, "provider": name, "model": m,
                                "prompt_tokens": (len(system) + len(user)) // 4,
                                "completion_tokens": len(text) // 4, "token_source": "approx_chars"}
                    last = str(r.get("error") or "empty")[:160]
                    continue
                r = _llm_client.chat(model, system, user, prov, max_tokens=_DEFAULT_MAX_TOKENS)
                if not r.get("error") and (r.get("text") or "").strip():
                    # CONTINUATION PROTOCOL: provider output caps (NVIDIA et al.) must not silently truncate
                    # long-form baselines — on finish_reason=length, continue up to _MAX_CONTINUATIONS times.
                    text, n_cont = r["text"], 0
                    pt = int((r.get("usage") or {}).get("prompt_tokens") or 0)
                    ct = int((r.get("usage") or {}).get("completion_tokens") or 0)
                    while r.get("finish_reason") == "length" and n_cont < _MAX_CONTINUATIONS:
                        cont_user = (f"{user}\n\n[YOUR PARTIAL OUTPUT SO FAR — do not repeat it]\n{text}\n\n"
                                     f"Continue EXACTLY from where the output stopped, mid-file if necessary.")
                        r = _llm_client.chat(model, system, cont_user, prov, max_tokens=_DEFAULT_MAX_TOKENS)
                        if r.get("error") or not (r.get("text") or "").strip():
                            break
                        text += r["text"]
                        pt += int((r.get("usage") or {}).get("prompt_tokens") or 0)
                        ct += int((r.get("usage") or {}).get("completion_tokens") or 0)
                        n_cont += 1
                    return {"ok": True, "text": text, "provider": name, "model": model,
                            "prompt_tokens": pt, "completion_tokens": ct,
                            "finish_reason": r.get("finish_reason"), "n_continuations": n_cont,
                            "token_source": "api_usage" if pt or ct else "missing"}
                last = str(r.get("error") or "empty")[:160]
            except Exception as exc:  # noqa: BLE001
                last = f"{type(exc).__name__}: {exc}"[:160]
        return {"ok": False, "error": last}
    return _call


# ── artifact extraction + sandboxed execution (compile -> pytest -> cross-test) ──────────────────────────────
def extract_files(text: str) -> dict[str, str]:
    """```python filename=path``` blocks -> {path: code}; unnamed blocks become main.py / tests in order."""
    files: dict[str, str] = {}
    unnamed = 0
    for name, code in _CODE_BLOCK_RE.findall(text or ""):
        code = code.strip() + "\n"
        if not name:
            name = "main.py" if unnamed == 0 else f"module_{unnamed}.py"
            unnamed += 1
        name = name.strip()
        if ".." in name or name.startswith(("/", "~")):
            continue  # no path escape from the sandbox dir (check BEFORE any stripping)
        while name.startswith("./"):
            name = name[2:]
        files[name] = code
    return files


def _run_sandboxed(cmd: list[str], cwd: Path, timeout: int = _SANDBOX_TIMEOUT_S) -> tuple[int, str]:
    env = {"PATH": os.environ.get("PATH", ""), "PYTHONDONTWRITEBYTECODE": "1", "HOME": str(cwd),
           "NO_PROXY": "*", "PYTHONHASHSEED": "0"}
    try:
        p = subprocess.run(cmd, cwd=str(cwd), env=env, capture_output=True, text=True, timeout=timeout)
        return p.returncode, (p.stdout + p.stderr)[-4000:]
    except subprocess.TimeoutExpired:
        return 124, "sandbox timeout"


def execute_lane(files: dict[str, str], workdir: Path) -> dict[str, Any]:
    """Write files, compile everything, run its own pytest file. Returns the runtime verdict for one lane."""
    workdir.mkdir(parents=True, exist_ok=True)
    for rel, code in files.items():
        p = workdir / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(code)
    compile_fail = []
    for rel in files:
        if rel.endswith(".py"):
            rc, out = _run_sandboxed([sys.executable, "-m", "py_compile", rel], workdir, timeout=30)
            if rc != 0:
                compile_fail.append({"file": rel, "error": out[-400:]})
    tests_rc, tests_out = (None, "no tests file emitted")
    if any(r.startswith("tests/") for r in files):
        tests_rc, tests_out = _run_sandboxed(
            [sys.executable, "-m", "pytest", "-q", "--no-header", "-x", "tests"], workdir)
    return {"n_files": len(files), "compile_failures": compile_fail,
            "compile_ok": not compile_fail and bool(files),
            "self_tests_rc": tests_rc, "self_tests_passed": tests_rc == 0,
            "self_tests_tail": tests_out[-1200:]}


def cross_test(impl_files: dict[str, str], test_files: dict[str, str], workdir: Path) -> dict[str, Any]:
    """Run lane X's TESTS against lane Y's IMPLEMENTATION — the same-input/same-expected-output differential."""
    if not impl_files or not any(r.startswith("tests/") for r in test_files):
        return {"ran": False, "reason": "missing impl or tests"}
    workdir.mkdir(parents=True, exist_ok=True)
    merged = {r: c for r, c in impl_files.items() if not r.startswith("tests/")}
    merged.update({r: c for r, c in test_files.items() if r.startswith("tests/")})
    for rel, code in merged.items():
        p = workdir / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(code)
    rc, out = _run_sandboxed([sys.executable, "-m", "pytest", "-q", "--no-header", "tests"], workdir)
    return {"ran": True, "passed": rc == 0, "rc": rc, "tail": out[-1200:]}


# ── the A/B session ───────────────────────────────────────────────────────────────────────────────────────────
# ── the PLANNED lane: few-token plan -> DETERMINISTIC builder/remixer -> LLM micro-repair as last resort ─────
_PLAN_CONTRACT = (
    "YOU ARE THE PLANNER. The build/wiring is done by a DETERMINISTIC builder, not you. Output ONLY:\n"
    "1) one line 'PLAN: <name> -> <name> -> <name>' using the python names of the executable primitives "
    "above; a loop step is loop(<name>, until=<name>); a branch step is if(<cond_name>)?<then_name>:"
    "<else_name>; a step may carry SETTINGS inline as <name>(knob=value, ...) when a primitive documents "
    "knobs. Data flows left to right through run(payload).\n"
    "2) one ```python filename=tests/test_main.py``` pytest file exercising run(payload) from main.\n"
    "Nothing else — no implementation code.")
_ARROW_PLAN_RE = re.compile(r"^\s*PLAN:\s*(.+)$", re.MULTILINE)
_LOOP_STEP_RE = re.compile(r"^loop\((\w+),\s*until=(\w+)\)$")
_BRANCH_STEP_RE = re.compile(r"^if\((\w+)\)\?(\w+):(\w+)$")
#: settings-in-plan (owner breakthrough 2026-07-07): 'b(size=200, overlap=20)' — the LLM tunes knobs inline
#: in the SAME few-token plan; the deterministic builder passes them as kwargs. Baked variants (b__tight)
#: are the 0-settings-token alternative for hot combos (primitive_settings_control_plane.bake_variant).
_CALL_SETTINGS_RE = re.compile(r"^(\w+)\(([^)]*)\)$")
_SETTING_KV_RE = re.compile(r"^\s*(\w+)\s*=\s*(.+?)\s*$")


def _parse_setting_value(raw: str) -> Any:
    try:
        return json.loads(raw)
    except ValueError:
        return raw.strip("'\"")
_MAX_REMIX_ATTEMPTS = 6
_REPAIR_RADIUS_LINES = 6  # the LLM sees ONLY this many lines around the failing line


def parse_arrow_plan(text: str) -> list[dict[str, str]]:
    """'PLAN: a -> loop(b, until=c) -> if(d)?e:f -> g' -> ordered step dicts (a plan-dialect zoo row;
    the json use_primitives dialect is the other row)."""
    m = _ARROW_PLAN_RE.search(text or "")
    if not m:
        return []
    steps: list[dict[str, str]] = []
    for raw in (p.strip() for p in m.group(1).split("->")):
        lm, bm = _LOOP_STEP_RE.match(raw), _BRANCH_STEP_RE.match(raw)
        cm = _CALL_SETTINGS_RE.match(raw) if not (lm or bm) else None
        if lm:
            steps.append({"kind": "loop", "name": lm.group(1), "until": lm.group(2)})
        elif bm:
            steps.append({"kind": "branch", "cond": bm.group(1), "then": bm.group(2), "else": bm.group(3)})
        elif cm:  # settings-in-plan: name(k=v, ...) — knobs ride inside the plan line
            settings = {}
            for part in cm.group(2).split(","):
                kv = _SETTING_KV_RE.match(part)
                if kv:
                    settings[kv.group(1)] = _parse_setting_value(kv.group(2))
            steps.append({"kind": "call", "name": cm.group(1), "settings": settings})
        elif re.fullmatch(r"\w+", raw):
            steps.append({"kind": "call", "name": raw})
    return steps


def _plan_names(steps: list[dict[str, str]]) -> list[str]:
    out: list[str] = []
    for s in steps:
        out += [s[k] for k in ("name", "until", "cond", "then", "else") if s.get(k)]
    return out


def deterministic_build(steps: list[dict[str, str]], exec_by_name: dict[str, dict[str, Any]]) -> dict[str, str]:
    """The DETERMINISTIC builder (python_chain_v1 of the builders zoo): plan -> runnable wiring, ZERO LLM
    tokens. Unknown names are skipped (recorded by the caller via the name diff)."""
    known = [s for s in steps if all(exec_by_name.get(n) for n in _plan_names([s]))]
    names = sorted({n for s in known for n in _plan_names([s])})
    body = ["def run(payload):", "    x = payload"]
    for s in known:
        if s["kind"] == "call":
            kwargs = "".join(f", {k}={v!r}" for k, v in sorted((s.get("settings") or {}).items()))
            body.append(f"    x = {s['name']}(x{kwargs})")
        elif s["kind"] == "loop":
            body += [f"    while not {s['until']}(x):", f"        x = {s['name']}(x)"]
        elif s["kind"] == "branch":
            body.append(f"    x = {s['then']}(x) if {s['cond']}(x) else {s['else']}(x)")
    body.append("    return x")
    lib = "\n\n".join(f"# [{exec_by_name[n].get('primitive_id')}] verified registry implementation\n"
                      f"{exec_by_name[n]['executable_body'].rstrip()}" for n in names)
    main = (f"from primitives_lib import {', '.join(names)}\n\n\n" if names else "") + "\n".join(body) + "\n"
    return {"main.py": main,
            "primitives_lib.py": '"""primitives_lib — verified executable primitives (deterministic build)."""\n\n' + lib + "\n"}


def _remix_variants(steps: list[dict[str, str]]) -> list[list[dict[str, str]]]:
    """Deterministic remixer v1: adjacent swaps, then single-step drops (bounded)."""
    out = []
    for i in range(len(steps) - 1):
        v = list(steps); v[i], v[i + 1] = v[i + 1], v[i]; out.append(v)
    for i in range(len(steps)):
        if len(steps) > 1:
            out.append(steps[:i] + steps[i + 1:])
    return out[:_MAX_REMIX_ATTEMPTS]


#: both python-traceback ('File "x.py", line N') and pytest-short ('x.py:N:') location styles
_TRACE_LOC_RES = (re.compile(r'File "([^"]+\.py)", line (\d+)'), re.compile(r"^([^\s:]+\.py):(\d+):", re.MULTILINE))


def _locate_failure(failure_tail: str, files: dict[str, str]) -> Optional[tuple[str, int]]:
    by_base = {Path(rel).name: rel for rel in files}
    hits: list[tuple[str, int]] = []
    for rx in _TRACE_LOC_RES:
        for f, ln in rx.findall(failure_tail or ""):
            rel = f.replace("\\", "/")
            while rel.startswith("./"):
                rel = rel[2:]
            rel = rel if rel in files else by_base.get(Path(rel).name, "")
            if rel:
                hits.append((rel, int(ln)))
    impl_hits = [h for h in hits if not h[0].startswith("tests/")]  # prefer the implementation frame
    return (impl_hits or hits)[-1] if hits else None


def micro_repair(files: dict[str, str], failure_tail: str, transport: Callable[[str, str], dict],
                 workdir: Path) -> dict[str, Any]:
    """LAST RESORT: the LLM sees ONLY the failing traceback +/-_REPAIR_RADIUS_LINES around the failing line
    — never the whole program — returns a corrected snippet, we splice + retest. Tiny token cost."""
    loc = _locate_failure(failure_tail, files)
    if not loc:
        return {"attempted": False, "reason": "no in-artifact location in traceback"}
    rel, line_no = loc
    lines = files[rel].splitlines()
    lo, hi = max(0, line_no - 1 - _REPAIR_RADIUS_LINES), min(len(lines), line_no - 1 + _REPAIR_RADIUS_LINES)
    snippet = "\n".join(lines[lo:hi])
    r = transport("You repair one small code snippet. Return ONLY the corrected snippet in one "
                  "```python block — same number of concerns, no commentary.",
                  f"This snippet from {rel} (around line {line_no}) fails with:\n{failure_tail[-600:]}\n\n"
                  f"```python\n{snippet}\n```")
    if not r.get("ok"):
        return {"attempted": True, "fixed": False, "error": r.get("error")}
    blocks = _CODE_BLOCK_RE.findall(r["text"])
    if not blocks:
        return {"attempted": True, "fixed": False, "error": "no snippet returned"}
    fixed = dict(files)
    fixed[rel] = "\n".join(lines[:lo] + blocks[0][1].strip("\n").splitlines() + lines[hi:]) + "\n"
    verdict = execute_lane(fixed, workdir)
    return {"attempted": True, "fixed": verdict["self_tests_passed"], "file": rel, "line": line_no,
            "repair_tokens": int(r.get("completion_tokens") or 0), "verdict": verdict, "files": fixed}


def save_composition_candidate(steps: list[dict[str, str]], files: dict[str, str], *, scenario: str,
                               fixed_by: str, out_dir: Optional[Path] = None) -> str:
    """Every repaired/remixed WORKING composition becomes a NEW candidate primitive (the flywheel)."""
    body = files.get("main.py", "")
    cid = f"prim-composed-{hashlib.blake2b(body.encode(), digest_size=8).hexdigest()}"
    row = {"primitive_id": cid, "record_type": "composed_primitive_candidate", "kind": "primitive_group",
           "title": f"Composed: {' -> '.join(_plan_names(steps))[:120]}", "executable_body": body,
           "plan_steps": steps, "scenario": scenario, "fixed_by": fixed_by, "language": "python", **BOUNDARY}
    out = (out_dir or resource("data") / "dev-intel" / _OUT_DIRNAME) / "composed_primitive_candidates.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("a") as f:
        f.write(json.dumps(row, sort_keys=True) + "\n")
    return cid


def run_planned_lane(turn_prompt: str, scaffold: str, transport: Callable[[str, str], dict],
                     exec_cards: list[dict[str, Any]], workdir: Path, *, scenario: str,
                     save_dir: Optional[Path] = None) -> dict[str, Any]:
    """plan (few LLM tokens) -> deterministic build -> test -> deterministic remix -> micro-repair -> save."""
    r = transport("You are a precise planner.", f"{scaffold}\n\n{turn_prompt}\n\n{_PLAN_CONTRACT}")
    if not r.get("ok"):
        return {"ok": False, "error": r.get("error")}
    exec_by_name = {str(c.get("impl_name")): c for c in exec_cards if c.get("impl_name")}
    steps = parse_arrow_plan(r["text"])
    if not steps:  # dialect zoo fallback: the json use_primitives form (ids or python names)
        by_id = {str(c.get("primitive_id")): str(c.get("impl_name")) for c in exec_cards}
        names = [by_id.get(x, x) for x in parse_plan_ids(r["text"])]
        steps = [{"kind": "call", "name": n} for n in names if re.fullmatch(r"\w+", n or "")]
    tests = {rel: code for rel, code in extract_files(r["text"]).items() if rel.startswith("tests/")}
    unknown = sorted({n for n in _plan_names(steps) if n not in exec_by_name})
    result: dict[str, Any] = {"ok": True, "provider": r.get("provider"), "model": r.get("model"),
                              "prompt_tokens": r.get("prompt_tokens"), "completion_tokens": r.get("completion_tokens"),
                              "token_source": r.get("token_source"), "plan": " -> ".join(_plan_names(steps)),
                              "plan_steps": len(steps), "unknown_plan_names": unknown,
                              "builder": "python_chain_v1", "remix_attempts": 0,
                              "repaired_by_llm": False, "repair_tokens": 0, "saved_candidate": None}
    if not steps or not tests:
        return {**result, "compile_ok": False, "self_tests_passed": False, "n_files": 0,
                "self_tests_tail": "planner emitted no parsable plan or no tests", "compile_failures": [],
                "n_primitives_reused": 0, "reused_code_chars": 0, "_files": {}}
    files = {**deterministic_build(steps, exec_by_name), **tests}
    verdict = execute_lane(files, workdir / "attempt0")
    if not verdict["self_tests_passed"]:
        for ai, variant in enumerate(_remix_variants(steps), start=1):  # deterministic remix first
            result["remix_attempts"] = ai
            vfiles = {**deterministic_build(variant, exec_by_name), **tests}
            vv = execute_lane(vfiles, workdir / f"remix{ai}")
            if vv["self_tests_passed"]:
                steps, files, verdict = variant, vfiles, vv
                result["saved_candidate"] = save_composition_candidate(steps, files, scenario=scenario,
                                                                       fixed_by="deterministic_remix",
                                                                       out_dir=save_dir)
                break
    if not verdict["self_tests_passed"]:  # LLM last resort, tiny radius
        rep = micro_repair(files, verdict["self_tests_tail"], transport, workdir / "repair")
        result["repaired_by_llm"] = bool(rep.get("fixed"))
        result["repair_tokens"] = int(rep.get("repair_tokens") or 0)
        result["completion_tokens"] = int(result["completion_tokens"] or 0) + result["repair_tokens"]
        if rep.get("fixed"):
            files, verdict = rep["files"], rep["verdict"]
            result["saved_candidate"] = save_composition_candidate(steps, files, scenario=scenario,
                                                                   fixed_by="llm_micro_repair",
                                                                   out_dir=save_dir)
    reused = [n for n in sorted({x for s in steps for x in _plan_names([s])}) if n in exec_by_name]
    return {**result, **{k: v for k, v in verdict.items()}, "files": sorted(files),
            "n_primitives_reused": len(reused),
            "reused_code_chars": len(files.get("primitives_lib.py", "")), "_files": files}


def run_ab_session(*, scenario: str, code_state: str, turns: int, transport: Callable[[str, str], dict],
                   cards: Optional[list[dict[str, Any]]] = None, k: int = 6,
                   lanes_spec: tuple[str, ...] = ("bare", "orchestrated"),
                   exec_cards: Optional[list[dict[str, Any]]] = None,
                   workroot: Optional[Path] = None, run_id: Optional[str] = None) -> dict[str, Any]:
    cards = cards if cards is not None else load_registry_cards()
    exec_cards = exec_cards if exec_cards is not None else load_exec_cards()
    run_id = run_id or f"ab-{scenario}-{code_state}-{hashlib.blake2b(str(turns).encode(), digest_size=4).hexdigest()}"
    workroot = workroot or Path(tempfile.mkdtemp(prefix="real_ab_"))
    system = ("You are a senior engineer producing production-quality, runnable code. Follow the output "
              "contract exactly.")
    turn_rows: list[dict[str, Any]] = []
    for i, turn in enumerate(build_turn_prompts(scenario, code_state, turns)):
        scaffold, used_ids = retrieve_scaffold(turn["prompt"], cards, k=k, exec_cards=exec_cards)
        prompts = {
            "bare": turn["prompt"],  # the LLM writes ALL the code
            "assisted": f"{scaffold}\n\n{turn['prompt']}",  # LLM still writes all code, with references
            # the compiler thesis: the LLM is ONLY the designer/orchestrator — primitive A -> B -> C + glue
            "orchestrated": f"{scaffold}\n\n{turn['prompt']}\n\n{_ORCHESTRATOR_CONTRACT}",
        }
        lanes: dict[str, dict[str, Any]] = {}
        for lane in lanes_spec:
            if lane == "planned":  # few-token plan -> deterministic builder/remixer -> micro-repair
                t0 = time.time()
                res = run_planned_lane(turn["prompt"], scaffold, transport, exec_cards,
                                       workroot / f"t{i}" / lane, scenario=scenario)
                res["wall_seconds"] = round(time.time() - t0, 1)
                lanes[lane] = res
                continue
            t0 = time.time()
            r = transport(system, prompts[lane])
            wall = round(time.time() - t0, 1)
            if not r.get("ok"):
                lanes[lane] = {"ok": False, "error": r.get("error"), "wall_seconds": wall}
                continue
            files = extract_files(r["text"])
            reused_ids: list[str] = []
            reused_chars = 0
            if lane == "orchestrated":
                lib_src, reused_ids = materialize_primitives_lib(parse_plan_ids(r["text"]), exec_cards)
                reused_chars = len(lib_src)
                files["primitives_lib.py"] = lib_src  # verified code injected verbatim: 0 generated tokens
            verdict = execute_lane(files, workroot / f"t{i}" / lane)
            lanes[lane] = {"ok": True, "provider": r.get("provider"), "model": r.get("model"),
                           "prompt_tokens": r.get("prompt_tokens"), "completion_tokens": r.get("completion_tokens"),
                           "n_continuations": r.get("n_continuations", 0), "finish_reason": r.get("finish_reason"),
                           "token_source": r.get("token_source"), "wall_seconds": wall,
                           "n_primitives_reused": len(reused_ids), "reused_primitive_ids": reused_ids,
                           "reused_code_chars": reused_chars,
                           "files": sorted(files), **verdict, "_files": files}
        a, b = lanes_spec[0], lanes_spec[-1]
        cross: dict[str, Any] = {}
        if lanes.get(a, {}).get("_files") and lanes.get(b, {}).get("_files"):
            cross = {f"{a}_tests_on_{b}_impl": cross_test(lanes[b]["_files"], lanes[a]["_files"],
                                                          workroot / f"t{i}" / "cross_ab"),
                     f"{b}_tests_on_{a}_impl": cross_test(lanes[a]["_files"], lanes[b]["_files"],
                                                          workroot / f"t{i}" / "cross_ba")}
        for lane in lanes.values():
            lane.pop("_files", None)
        turn_rows.append({"turn_index": i + 1, "stage": turn["stage"], "surface": turn["surface"],
                          "scaffold_primitive_ids": used_ids, "lanes": lanes, "cross_test": cross, **BOUNDARY})
    ok_turns = [t for t in turn_rows if all(t["lanes"].get(x, {}).get("ok") for x in lanes_spec)]
    def _sum(lane: str, key: str) -> int:
        return sum(int(t["lanes"][lane].get(key) or 0) for t in ok_turns)
    def _rate(lane: str, key: str) -> Optional[float]:
        return round(sum(bool(t["lanes"][lane].get(key)) for t in ok_turns) / len(ok_turns), 3) if ok_turns else None
    lane_summaries = {lane: {"prompt_tokens": _sum(lane, "prompt_tokens"),
                             "completion_tokens": _sum(lane, "completion_tokens"),
                             "compile_ok_rate": _rate(lane, "compile_ok"),
                             "self_test_pass_rate": _rate(lane, "self_tests_passed"),
                             "n_primitives_reused": _sum(lane, "n_primitives_reused"),
                             "reused_code_chars": _sum(lane, "reused_code_chars")}
                      for lane in lanes_spec}
    summary = {
        "run_id": run_id, "scenario": scenario, "code_state": code_state, "turns_requested": turns,
        "turns_compared": len(ok_turns), "lanes": lane_summaries,
        "generation_avoided_completion_tokens": (
            lane_summaries[a]["completion_tokens"] - lane_summaries[b]["completion_tokens"]) if ok_turns else None,
        "cross_test_agreement_rate": round(sum(
            1 for t in ok_turns if all(v.get("passed") for v in t["cross_test"].values())) / len(ok_turns), 3)
            if ok_turns else None,
        "note": ("completion-token deltas alone do NOT equal savings — weigh them against "
                 "self_test_pass_rate and cross-test outcomes lane-vs-lane; 'orchestrated' = the compiler "
                 "thesis (LLM plans primitive A->B->C + thin glue; verified code injected at 0 generated "
                 "tokens)"),
        **BOUNDARY}
    out_dir = resource("data") / "dev-intel" / _OUT_DIRNAME / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "turns.jsonl").write_text("".join(json.dumps(t, sort_keys=True) + "\n" for t in turn_rows))
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True))
    summary["receipt_dir"] = str(out_dir)
    return summary


# ── self-test (offline: stub transport; REAL sandbox subprocesses) ───────────────────────────────────────────
_STUB_GOOD = '''```python filename=main.py
def add_invoice_totals(rows):
    """Sum invoice line totals per invoice id."""
    out = {}
    for r in rows:
        out[r["invoice_id"]] = out.get(r["invoice_id"], 0) + r["amount"]
    return out
```
```python filename=tests/test_main.py
from main import add_invoice_totals

def test_add_invoice_totals():
    rows = [{"invoice_id": "a", "amount": 2}, {"invoice_id": "a", "amount": 3}]
    assert add_invoice_totals(rows) == {"a": 5}
```
'''
_STUB_BUGGY = _STUB_GOOD.replace('out.get(r["invoice_id"], 0) + r["amount"]', 'r["amount"]')


def _self_test() -> int:
    checks: list[tuple[str, bool]] = []
    files = extract_files(_STUB_GOOD)
    checks.append(("extracts named python files incl. the tests file",
                   set(files) == {"main.py", "tests/test_main.py"}))
    checks.append(("path escape is refused", extract_files("```python filename=../evil.py\nx=1\n```") == {}))
    with tempfile.TemporaryDirectory() as td:
        good = execute_lane(extract_files(_STUB_GOOD), Path(td) / "good")
        buggy = execute_lane(extract_files(_STUB_BUGGY), Path(td) / "buggy")
        checks.append(("REAL sandbox: correct lane compiles + passes its own pytest",
                       good["compile_ok"] and good["self_tests_passed"]))
        checks.append(("MUTATION GATE: the buggy lane compiles but FAILS its tests (verifier can go red)",
                       buggy["compile_ok"] and not buggy["self_tests_passed"]))
        ct = cross_test(extract_files(_STUB_BUGGY), extract_files(_STUB_GOOD), Path(td) / "cross")
        checks.append(("cross-test: good lane's tests FAIL on the buggy lane's implementation",
                       ct["ran"] and not ct["passed"]))
        broken = execute_lane({"main.py": "def broken(:\n"}, Path(td) / "syntax")
        checks.append(("syntax-broken artifact fails compile", not broken["compile_ok"]))
    calls = {"n": 0}
    _STUB_PLAN = ('```json\n{"use_primitives": ["prim-exec:selftest:agg"]}\n```\n'
                  '```python filename=main.py\nfrom primitives_lib import add_invoice_totals\n\n'
                  'def run(rows):\n    return add_invoice_totals(rows)\n```\n'
                  '```python filename=tests/test_main.py\nfrom main import run\n\n'
                  'def test_run():\n    rows = [{"invoice_id": "a", "amount": 2}, {"invoice_id": "a", "amount": 3}]\n'
                  '    assert run(rows) == {"a": 5}\n```\n')
    def stub_transport(system: str, user: str) -> dict[str, Any]:
        calls["n"] += 1
        if "ORCHESTRATOR" in user:  # the plan-only lane: tiny completion, imports the verified primitive
            return {"ok": True, "text": _STUB_PLAN, "provider": "stub", "model": "stub",
                    "prompt_tokens": len(user) // 4, "completion_tokens": 120, "token_source": "api_usage"}
        return {"ok": True, "text": _STUB_BUGGY, "provider": "stub", "model": "stub",
                "prompt_tokens": len(user) // 4, "completion_tokens": 700, "token_source": "api_usage"}
    fake_cards = [{"primitive_id": "prim:test:aggregate", "title": "Aggregate invoice line totals per invoice",
                   "blackbox": "Consumes invoice line rows and emits per-invoice totals. Input: rows. Output: totals map.",
                   "input_edge": "InvoiceLineRows", "output_edge": "InvoiceTotalsMap"}]
    fake_exec = [{"primitive_id": "prim-exec:selftest:agg", "impl_name": "add_invoice_totals",
                  "title": "Aggregate invoice line totals per invoice",
                  "executable_body": ('def add_invoice_totals(rows):\n    out = {}\n    for r in rows:\n'
                                      '        out[r["invoice_id"]] = out.get(r["invoice_id"], 0) + r["amount"]\n'
                                      '    return out\n')}]
    with tempfile.TemporaryDirectory() as td:
        summary = run_ab_session(scenario="kaggle_tabular_competition", code_state="mid_build", turns=1,
                                 transport=stub_transport, cards=fake_cards, k=1, exec_cards=fake_exec,
                                 lanes_spec=("bare", "orchestrated"),
                                 workroot=Path(td) / "w", run_id="ab-selftest")
        lanes = summary["lanes"]
        checks.append(("A/B session: two lane calls per turn, real-usage token accounting summed",
                       calls["n"] == 2 and lanes["bare"]["completion_tokens"] == 700
                       and lanes["orchestrated"]["completion_tokens"] == 120))
        checks.append(("COMPILER THESIS measured: orchestrated lane = plan+glue only; verified primitive "
                       "injected at 0 generated tokens; generation avoided = 580",
                       lanes["orchestrated"]["n_primitives_reused"] == 1
                       and lanes["orchestrated"]["reused_code_chars"] > 100
                       and summary["generation_avoided_completion_tokens"] == 580))
        checks.append(("runtime differential caught: orchestrated (registry code) PASSES its tests, "
                       "bare (buggy full generation) FAILS",
                       lanes["orchestrated"]["self_test_pass_rate"] == 1.0
                       and lanes["bare"]["self_test_pass_rate"] == 0.0))
        checks.append(("cross-testing ran between the lanes", summary["turns_compared"] == 1
                       and summary["cross_test_agreement_rate"] is not None))
        rec_dir = Path(summary["receipt_dir"])
        checks.append(("receipts written (turns.jsonl + summary.json) with the boundary",
                       (rec_dir / "turns.jsonl").exists()
                       and json.loads((rec_dir / "summary.json").read_text()).get("serves_truth") is False))
        shutil.rmtree(rec_dir, ignore_errors=True)  # self-test receipts don't pollute real runs
    # ── the PLANNED lane: deterministic builder + remixer + micro-repair (owner descent directive) ──────────
    steps = parse_arrow_plan("junk\nPLAN: parse_rows -> loop(clean_row, until=is_clean) -> if(has_id)?keep:drop\nmore")
    checks.append(("plan dialect parses chains, loops, and branches from few tokens",
                   [s["kind"] for s in steps] == ["call", "loop", "branch"]
                   and steps[1]["until"] == "is_clean" and steps[2]["else"] == "drop"))
    s_steps = parse_arrow_plan("PLAN: parse_rows -> scale_amounts(factor=2, label='x') -> sum_by_invoice")
    checks.append(("SETTINGS-IN-PLAN (owner breakthrough): 'b(factor=2)' parses knobs inline",
                   s_steps[1]["settings"] == {"factor": 2, "label": "x"}))
    exec_fix2 = [{"primitive_id": "p:parse", "impl_name": "parse_rows",
                  "executable_body": ("def parse_rows(text):\n"
                                      "    return [{'invoice_id': p.split(':')[0], 'amount': int(p.split(':')[1])}\n"
                                      "            for p in text.split(',') if p]\n")},
                 {"primitive_id": "p:scale", "impl_name": "scale_amounts",
                  "executable_body": ("def scale_amounts(rows, factor=1, label=''):\n"
                                      "    return [{**r, 'amount': r['amount'] * factor} for r in rows]\n")},
                 {"primitive_id": "p:agg", "impl_name": "sum_by_invoice",
                  "executable_body": ("def sum_by_invoice(rows):\n    out = {}\n    for r in rows:\n"
                                      "        out[r['invoice_id']] = out.get(r['invoice_id'], 0) + r['amount']\n"
                                      "    return out\n")}]
    with tempfile.TemporaryDirectory() as td2:
        built = deterministic_build(s_steps, {c["impl_name"]: c for c in exec_fix2})
        tests2 = extract_files('```python filename=tests/test_main.py\nfrom main import run\n\n'
                               'def test_run():\n    assert run("a:2,a:3,b:1") == {"a": 10, "b": 2}\n```\n')
        v2 = execute_lane({**built, **tests2}, Path(td2) / "s")
        checks.append(("deterministic builder passes plan settings as kwargs; doubled amounts verified "
                       "at runtime", "factor=2" in built["main.py"] and v2["self_tests_passed"]))
    exec_fixture = [
        {"primitive_id": "prim-exec:st:parse", "impl_name": "parse_rows",
         "executable_body": ("def parse_rows(text):\n"
                             "    return [{'invoice_id': p.split(':')[0], 'amount': int(p.split(':')[1])}\n"
                             "            for p in text.split(',') if p]\n")},
        {"primitive_id": "prim-exec:st:agg", "impl_name": "sum_by_invoice",
         "executable_body": ("def sum_by_invoice(rows):\n    out = {}\n    for r in rows:\n"
                             "        out[r['invoice_id']] = out.get(r['invoice_id'], 0) + r['amount']\n"
                             "    return out\n")}]
    plan_tests = ('```python filename=tests/test_main.py\nfrom main import run\n\n'
                  'def test_run():\n    assert run("a:2,a:3,b:1") == {"a": 5, "b": 1}\n```\n')
    def planner_stub_wrong_order(system: str, user: str) -> dict[str, Any]:
        return {"ok": True, "text": f"PLAN: sum_by_invoice -> parse_rows\n{plan_tests}", "provider": "stub",
                "model": "stub", "prompt_tokens": 100, "completion_tokens": 60, "token_source": "api_usage"}
    with tempfile.TemporaryDirectory() as td:
        good = deterministic_build(parse_arrow_plan("PLAN: parse_rows -> sum_by_invoice"),
                                   {c["impl_name"]: c for c in exec_fixture})
        v = execute_lane({**good, **extract_files(plan_tests)}, Path(td) / "det")
        checks.append(("DETERMINISTIC builder wires a correct plan into a passing program at 0 LLM tokens",
                       v["compile_ok"] and v["self_tests_passed"]))
        res = run_planned_lane("aggregate invoices", "scaffold", planner_stub_wrong_order, exec_fixture,
                               Path(td) / "lane", scenario="selftest", save_dir=Path(td) / "cands")
        checks.append(("DETERMINISTIC remixer repairs a wrong-order plan (no LLM repair needed) and the fix "
                       "is SAVED as a new composed-primitive candidate",
                       res["self_tests_passed"] and res["remix_attempts"] >= 1
                       and not res["repaired_by_llm"] and res["saved_candidate"]
                       and (Path(td) / "cands" / "composed_primitive_candidates.jsonl").exists()))
        checks.append(("planned lane's LLM bill is the PLAN ONLY (few tokens)",
                       res["completion_tokens"] == 60))
        broken_files = {"main.py": "def run(payload):\n    return payload + 1\n",
                        **extract_files(plan_tests)}
        broken_v = execute_lane(broken_files, Path(td) / "br")
        def repair_stub(system: str, user: str) -> dict[str, Any]:
            assert "def run" in user and len(user) < 4000  # small radius, never the whole program
            return {"ok": True, "text": ('```python\ndef run(payload):\n'
                                         '    return {"a": 5, "b": 1} if payload == "a:2,a:3,b:1" else {}\n```'),
                    "provider": "stub", "model": "stub", "completion_tokens": 30, "token_source": "api_usage"}
        rep = micro_repair(broken_files, broken_v["self_tests_tail"], repair_stub, Path(td) / "rep")
        checks.append(("LLM MICRO-REPAIR (last resort) fixes from the local error radius only",
                       rep.get("attempted") and rep.get("fixed") and rep.get("repair_tokens") == 30))
    try:
        make_transport(["ollama"], "gemma4")
        checks.append(("local gemma4 is REFUSED for real comparisons (owner law)", False))
    except ValueError:
        checks.append(("local gemma4 is REFUSED for real comparisons (owner law)", True))
    failed = [n for n, ok in checks if not ok]
    for n, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print("\nPASS - real_buildout_ab_harness: same prompt -> bare vs registry-assisted on the CLOUD lanes, "
          "real usage tokens, sandbox compile+pytest, cross-tested implementations. Local gemma4 refused. "
          "serves_truth=false.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--scenario", default="kaggle_tabular_competition")
    ap.add_argument("--code-state", default="mid_build")
    ap.add_argument("--turns", type=int, default=2)
    ap.add_argument("--providers", default="ollama,nvidia,openwebui_cdp")
    ap.add_argument("--model", default="glm-5.2")
    ap.add_argument("--lanes", default="bare,orchestrated",
                    help="comma list of bare|assisted|orchestrated (orchestrated = LLM plans A->B->C + glue)")
    ap.add_argument("--k", type=int, default=6)
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.list:
        for s in list_scenarios():
            print(f"  {s['template_id']:44s} {s['category']:28s} {s['turns']} turns")
        return 0
    if args.run:
        transport = make_transport([p.strip() for p in args.providers.split(",")], args.model)
        summary = run_ab_session(scenario=args.scenario, code_state=args.code_state, turns=args.turns,
                                 transport=transport, k=args.k,
                                 lanes_spec=tuple(x.strip() for x in args.lanes.split(",")))
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
