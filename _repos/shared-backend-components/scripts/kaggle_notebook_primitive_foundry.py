#!/usr/bin/env python3
"""scripts.kaggle_notebook_primitive_foundry — a STANDALONE (no Claude-Code-harness) foundry that turns real
Kaggle notebooks into governed primitive candidates for our database.

Pipeline:  Kaggle API (list + pull)  ->  governed source snapshot (handle + digest, NO raw body in cards)
           ->  LLM DECOMPOSITION (a series of questions/prompts to Ollama / OpenWebUI-Gemma-4 / OpenRouter)
           ->  seven-primitive candidate cards  ->  LLM REMIX (variations across domains)
           ->  stage to the candidate DB (canonical_id; candidate=true / serves_truth=false; append-dedupe).

Runnable directly:  no harness, no MCP, just python3. Resumable (a page cursor), rate-limited, bounded per
run, and idempotent (canonical content-hash ids + append-dedupe). Raw notebook bodies live ONLY in a
gitignored cache; primitive rows carry the source HANDLE + DIGEST, never the body (lossless governance law).
LLM lanes and Kaggle access are OPT-IN flags; the default `--self-test` is fully offline (fixture notebook +
stub model) so the whole pipeline is verifiable without credentials or network.

    # verify the whole pipeline offline (no creds, no network):
    python3 scripts/kaggle_notebook_primitive_foundry.py --self-test

    # live: needs Kaggle creds (~/.kaggle/kaggle.json or KAGGLE_USERNAME/KAGGLE_KEY) + a reachable model lane
    python3 scripts/kaggle_notebook_primitive_foundry.py --run --kaggle --use-llm \
        --provider openwebui --model gemma-4-coding --max-notebooks 50 --page-size 100 \
        --search "feature engineering" --rate-limit-seconds 2.0

    # resume from where the last run stopped (the cursor persists the next page):
    python3 scripts/kaggle_notebook_primitive_foundry.py --run --kaggle --use-llm --provider ollama \
        --model gemma-4-coding --resume --max-notebooks 200
"""
from __future__ import annotations

import sys
from pathlib import Path

# ── substrate-root bootstrap (sentinel; mirrors scripts/enrich_minted_primitives.py) ─────────────────────────
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
import subprocess  # noqa: E402
import time  # noqa: E402
from typing import Any, Callable, Optional  # noqa: E402

try:
    from src.teleon.experiments.ids import canonical_id  # noqa: E402  THE data-plane id authority
except Exception as exc:  # noqa: BLE001
    raise SystemExit("kaggle_notebook_primitive_foundry requires src.teleon.experiments.ids.canonical_id "
                     f"(the ONE id authority); import failed: {exc}")

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}

CARD_PREFIX = "prim-kaggle"
CARD_RECORD_TYPE = "kaggle_derived_primitive_candidate"
CARD_SCHEMA_VERSION = 1
STAGED_FILENAME = "kaggle_primitive_candidates.jsonl"
_VERIFIED_CORPUS_FILENAMES = frozenset({"verified_factory_primitive_cards.jsonl", "primitive_edge_cards.jsonl"})
_PROMOTION_BLOCKERS = ("source_license_review", "correctness_proof", "usefulness_or_enrichment")
_CAMEL_EDGE_RE = re.compile(r"^[A-Z][A-Za-z0-9]*$")
#: keep notebook text a MODEL can actually read but bound cost — decode-safe upper bound per notebook.
_MAX_NOTEBOOK_CHARS = 20_000
#: politeness default between Kaggle API calls (seconds); overridable, never below the floor.
_RATE_LIMIT_FLOOR_SECONDS = 1.0


# ── caches / staging paths (raw bodies stay OUT of git and out of the cards) ──────────────────────────────────

def _base_dir() -> Path:
    return resource("data") / "dev-intel" / "kaggle_primitive_foundry"


def _cache_dir() -> Path:
    d = _base_dir() / "notebook_cache"  # gitignored; raw bodies only here
    d.mkdir(parents=True, exist_ok=True)
    return d


def _cursor_path() -> Path:
    return _base_dir() / "cursor.json"


def staged_path() -> Path:
    return resource("data") / "dev-intel" / "aidevobserver_edge_foundry" / STAGED_FILENAME


# ── LLM lane (reuse scripts/_llm_client) — injectable for the offline self-test ───────────────────────────────

def make_llm_transport(provider_name: str, model: str) -> Callable[[str, str], str]:
    """Return a call(system, user)->reply_text bound to a real provider via scripts/_llm_client.chat."""
    from scripts import _llm_client  # noqa: PLC0415
    provider = _llm_client.resolve_provider(provider_name)

    def _call(system: str, user: str) -> str:
        resp = _llm_client.chat(model, system, user, provider)  # inherit the high-ceiling default; never truncate generation
        if resp.get("error"):
            raise RuntimeError(str(resp["error"])[:200])
        return str(resp.get("text") or "")
    return _call


def _extract_json(text: str) -> Optional[Any]:
    """Tolerant JSON object/array extraction from a model reply (first balanced {...} or [...]). None on fail."""
    for opener, closer in (("{", "}"), ("[", "]")):
        start = text.find(opener)
        if start == -1:
            continue
        depth = 0
        for i in range(start, len(text)):
            if text[i] == opener:
                depth += 1
            elif text[i] == closer:
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[start:i + 1])
                    except json.JSONDecodeError:
                        break
    return None


# ── Kaggle acquisition adapter (subprocess to the `kaggle` CLI) — injectable for the self-test ────────────────

def _kaggle_env_ready() -> bool:
    return bool(os.environ.get("KAGGLE_USERNAME") and os.environ.get("KAGGLE_KEY")) \
        or (Path.home() / ".kaggle" / "kaggle.json").exists()


def kaggle_list_kernels(page: int, page_size: int, *, search: str = "",
                        runner: Optional[Callable[[list[str]], str]] = None) -> list[dict[str, Any]]:
    """List kernels (notebooks) via `kaggle kernels list -v` (CSV). Returns [{ref, title, author, ...}]."""
    run = runner or _default_cli_runner
    cmd = ["kaggle", "kernels", "list", "-p", str(page), "--page-size", str(page_size), "-v"]
    if search:
        cmd += ["-s", search]
    out = run(cmd)
    return _parse_kaggle_csv(out)


def kaggle_pull_kernel(ref: str, dest: Path, *,
                       runner: Optional[Callable[[list[str]], str]] = None) -> Optional[str]:
    """Pull a kernel's source into `dest` and return the extracted TEXT (code + markdown, outputs stripped),
    bounded to _MAX_NOTEBOOK_CHARS. None if nothing usable was pulled."""
    run = runner or _default_cli_runner
    dest.mkdir(parents=True, exist_ok=True)
    run(["kaggle", "kernels", "pull", ref, "-p", str(dest), "-m"])
    return read_notebook_text(dest)


def _default_cli_runner(cmd: list[str]) -> str:
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120, check=False)  # noqa: S603
    if proc.returncode != 0:
        raise RuntimeError(f"{' '.join(cmd[:3])} failed rc={proc.returncode}: {proc.stderr[:200]}")
    return proc.stdout


def _parse_kaggle_csv(csv_text: str) -> list[dict[str, Any]]:
    import csv  # noqa: PLC0415
    import io  # noqa: PLC0415
    rows: list[dict[str, Any]] = []
    reader = csv.DictReader(io.StringIO(csv_text.strip()))
    for r in reader:
        ref = (r.get("ref") or "").strip()
        if ref:
            rows.append({"ref": ref, "title": (r.get("title") or "").strip(),
                         "author": (r.get("author") or "").strip(),
                         "lastRunTime": (r.get("lastRunTime") or "").strip()})
    return rows


def read_notebook_text(folder: Path) -> Optional[str]:
    """Extract code + markdown from a pulled kernel (.ipynb or .py/.r), stripping outputs. Bounded."""
    parts: list[str] = []
    for p in sorted(folder.glob("*")):
        if p.suffix == ".ipynb":
            try:
                nb = json.loads(p.read_text(encoding="utf-8", errors="replace"))
            except Exception:  # noqa: BLE001
                continue
            for cell in nb.get("cells", []):
                src = cell.get("source") or []
                text = "".join(src) if isinstance(src, list) else str(src)
                if cell.get("cell_type") in ("code", "markdown") and text.strip():
                    parts.append(text)
        elif p.suffix in (".py", ".r", ".R"):
            parts.append(p.read_text(encoding="utf-8", errors="replace"))
    joined = "\n\n".join(parts).strip()
    return joined[:_MAX_NOTEBOOK_CHARS] if joined else None


def source_snapshot(kernel: dict[str, Any], notebook_text: str) -> dict[str, Any]:
    """A GOVERNED source row: handle + digest, NO raw body (the raw body stays only in the gitignored cache)."""
    digest = hashlib.sha256(notebook_text.encode("utf-8")).hexdigest()[:16]
    return {"source_kind": "kaggle_notebook", "ref": kernel.get("ref"), "title": kernel.get("title"),
            "author": kernel.get("author"), "handle": f"kaggle://kernels/{kernel.get('ref')}",
            "content_digest": digest, "chars": len(notebook_text), **BOUNDARY}


# ── LLM decomposition (the series of questions) + remix ───────────────────────────────────────────────────────

_DECOMPOSE_SYSTEM = (
    "You extract REUSABLE software primitives from a data-science notebook. A primitive is one reusable unit "
    "of computational work with a concrete mechanism (named tools/libraries), a typed input, and a typed "
    "output. Ignore notebook-specific glue. Reply ONLY with JSON.")


def _decompose_prompt(snapshot: dict[str, Any], notebook_text: str) -> str:
    return (
        f"Notebook: {snapshot.get('title')!r} (ref {snapshot.get('ref')}).\n\n"
        f"SOURCE (code+markdown, truncated):\n{notebook_text[:_MAX_NOTEBOOK_CHARS]}\n\n"
        "Questions:\n"
        "1. What are the reusable computational components here (data intake, cleaning, feature engineering, "
        "model, evaluation, submission, etc.)?\n"
        "2. For EACH, give: name (short), mechanism (one sentence naming the concrete tools/libraries), "
        "input (a typed noun), output (a typed noun), 2-3 imperative steps, and 2-4 capability tags.\n"
        'Reply ONLY as JSON: {"primitives":[{"name":..,"mechanism":..,"input":..,"output":..,'
        '"steps":[..],"tags":[..]}]}')


def _remix_prompt(primitives: list[dict[str, Any]]) -> str:
    compact = [{"name": p.get("name"), "mechanism": p.get("mechanism"),
                "input": p.get("input"), "output": p.get("output")} for p in primitives]
    return (
        "Here are extracted primitives:\n" + json.dumps(compact, indent=1) + "\n\n"
        "Remix them into NEW reusable primitives that would serve DIFFERENT domains or compose two of these "
        "into a stronger unit. For each: name, mechanism (concrete tools), input, output, steps, tags, and "
        '"remix_of" (the source names). Reply ONLY as JSON: {"remixes":[{...}]}')


def _to_card(item: dict[str, Any], snapshot: dict[str, Any], *, origin: str,
             remix_of: Optional[list[str]] = None) -> Optional[dict[str, Any]]:
    """One extracted/remixed primitive -> a governed candidate card (canonical id, typed edges, provenance)."""
    name = str(item.get("name") or "").strip()
    mechanism = str(item.get("mechanism") or "").strip()
    if not name or not mechanism:
        return None
    title = name if len(name) > 12 else f"{name} ({snapshot.get('title') or 'kaggle'})"
    steps = [str(s)[:200] for s in (item.get("steps") or [])][:5]
    tags = [str(t)[:40] for t in (item.get("tags") or [])][:6]
    blackbox = mechanism if len(mechanism) >= 40 else (
        f"{mechanism} Input: {item.get('input')}. Output: {item.get('output')}.")
    input_edge = _camel(str(item.get("input") or "input"), "input")
    output_edge = _camel(str(item.get("output") or "result"), "result")
    pid = canonical_id(CARD_PREFIX, title, blackbox, snapshot.get("content_digest") or "")
    card = {
        "record_type": CARD_RECORD_TYPE, "schema_version": CARD_SCHEMA_VERSION, "kind": "route.primitive",
        "primitive_id": pid, "title": title[:160], "blackbox": blackbox[:1200],
        "steps": steps, "capability_tags": tags,
        "input_edge": input_edge, "output_edge": output_edge,
        "contract": {"input": str(item.get("input") or "")[:200], "output": str(item.get("output") or "")[:200]},
        "provenance": {"origin": origin, "minter": "scripts.kaggle_notebook_primitive_foundry",
                       "source_kind": "kaggle_notebook", "source_ref": snapshot.get("ref"),
                       "source_handle": snapshot.get("handle"), "source_digest": snapshot.get("content_digest")},
        "promotion_blockers": list(_PROMOTION_BLOCKERS),
        **({"remix_of": remix_of} if remix_of else {}),
        **BOUNDARY,
    }
    return card


def _camel(*words: str) -> str:
    parts = re.split(r"[^A-Za-z0-9]+", " ".join(words))
    out = "".join(p[:1].upper() + p[1:] for p in parts if p) or "Edge"
    return out[:48]


def process_notebook(kernel: dict[str, Any], notebook_text: str, llm: Callable[[str, str], str], *,
                     do_remix: bool = True) -> dict[str, Any]:
    """Decompose one notebook into primitive cards + remix cards. LLM failures are recorded, never faked."""
    snap = source_snapshot(kernel, notebook_text)
    cards: list[dict[str, Any]] = []
    errors: list[str] = []
    try:
        reply = llm(_DECOMPOSE_SYSTEM, _decompose_prompt(snap, notebook_text))
        parsed = _extract_json(reply)
        prims = parsed.get("primitives") if isinstance(parsed, dict) else None
        prim_items = prims if isinstance(prims, list) else []
        if not prim_items:  # a present-but-unparseable/empty reply is a RECORDED miss, never a silent success
            errors.append("decompose: unparseable_or_no_primitives")
    except Exception as exc:  # noqa: BLE001
        errors.append(f"decompose: {str(exc)[:120]}")
        prim_items = []
    base_cards = [c for c in (_to_card(it, snap, origin="decompose") for it in prim_items) if c]
    cards.extend(base_cards)
    if do_remix and base_cards:
        try:
            reply = llm(_DECOMPOSE_SYSTEM, _remix_prompt(prim_items))
            parsed = _extract_json(reply) or {}
            remixes = parsed.get("remixes") if isinstance(parsed, dict) else None
            for it in (remixes if isinstance(remixes, list) else []):
                c = _to_card(it, snap, origin="remix", remix_of=it.get("remix_of") or [])
                if c:
                    cards.append(c)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"remix: {str(exc)[:120]}")
    return {"snapshot": snap, "cards": cards, "errors": errors, "n_decomposed": len(base_cards),
            "n_total": len(cards), **BOUNDARY}


# ── staging (canonical id + append-dedupe; refuses any verified corpus target) ────────────────────────────────

def _validate_card(card: dict[str, Any]) -> list[str]:
    problems: list[str] = []
    if card.get("primitive_id") != canonical_id(CARD_PREFIX, card.get("title", ""), card.get("blackbox", ""),
                                                card.get("provenance", {}).get("source_digest") or ""):
        problems.append("primitive_id does not recompute")
    for ef in ("input_edge", "output_edge"):
        if not _CAMEL_EDGE_RE.match(str(card.get(ef) or "")):
            problems.append(f"{ef} not CamelCase")
    if card.get("serves_truth") is not False or card.get("candidate") is not True:
        problems.append("candidate boundary not stamped")
    return problems


def stage_cards(cards: list[dict[str, Any]], target_path: Optional[Path] = None) -> dict[str, Any]:
    """APPEND-dedupe cards to the Kaggle staged file. HARD GATE: the target must carry STAGED_FILENAME, not be
    a symlink, and never resolve to a verified corpus file."""
    from scripts._jsonl import read_jsonl_tolerant  # noqa: PLC0415
    p = target_path or staged_path()
    if p.name != STAGED_FILENAME:
        raise ValueError(f"refusing to write to {p.name!r} — only {STAGED_FILENAME!r} allowed")
    if p.is_symlink():
        raise ValueError(f"refusing to write through a symlink at {p}")
    if p.exists() and (p.resolve().name in _VERIFIED_CORPUS_FILENAMES or p.resolve().name != STAGED_FILENAME):
        raise ValueError(f"resolved target {p.resolve()} is not the staged file — refused")
    for c in cards:
        probs = _validate_card(c)
        if probs:
            raise ValueError(f"card {c.get('primitive_id')} failed validation: {probs}")
    existing = {str(r.get("primitive_id")) for r in (read_jsonl_tolerant(p) if p.exists() else [])}
    appended = 0
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as fh:
        for c in cards:
            pid = str(c["primitive_id"])
            if pid in existing:
                continue
            existing.add(pid)
            fh.write(json.dumps(c, sort_keys=True) + "\n")
            appended += 1
    return {"appended": appended, "on_file": len(existing), "path": str(p), **BOUNDARY}


# ── the run loop (resumable, rate-limited, bounded) ──────────────────────────────────────────────────────────

def _load_cursor() -> dict[str, Any]:
    p = _cursor_path()
    if p.exists():
        try:
            return json.loads(p.read_text())
        except Exception:  # noqa: BLE001
            pass
    return {"next_page": 1, "seen_refs": []}


def _save_cursor(cursor: dict[str, Any]) -> None:
    _cursor_path().parent.mkdir(parents=True, exist_ok=True)
    _cursor_path().write_text(json.dumps(cursor, sort_keys=True))


def run_foundry(*, llm: Callable[[str, str], str], lister: Callable[..., list[dict[str, Any]]],
                puller: Callable[..., Optional[str]], max_notebooks: int, page_size: int, search: str,
                rate_limit_seconds: float, resume: bool, do_remix: bool,
                sleep: Callable[[float], None] = time.sleep) -> dict[str, Any]:
    """Acquire -> decompose -> remix -> stage, until max_notebooks processed or pages exhausted. Resumable."""
    cursor = _load_cursor() if resume else {"next_page": 1, "seen_refs": []}
    seen = set(cursor.get("seen_refs") or [])
    rate = max(_RATE_LIMIT_FLOOR_SECONDS, float(rate_limit_seconds))
    processed = staged = failed = 0
    page = int(cursor.get("next_page") or 1)
    all_cards: list[dict[str, Any]] = []
    while processed < max_notebooks:
        kernels = lister(page, page_size, search=search)
        if not kernels:
            break
        for k in kernels:
            if processed >= max_notebooks:
                break
            ref = k.get("ref")
            if not ref or ref in seen:
                continue
            seen.add(ref)
            sleep(rate)  # politeness between pulls
            try:
                text = puller(ref, _cache_dir() / re.sub(r"[^A-Za-z0-9_.-]", "_", ref))
            except Exception:  # noqa: BLE001
                failed += 1
                continue
            if not text:
                failed += 1
                continue
            result = process_notebook(k, text, llm, do_remix=do_remix)
            processed += 1
            if result["cards"]:
                all_cards.extend(result["cards"])
        page += 1
        sleep(rate)
    wrote = stage_cards(all_cards) if all_cards else {"appended": 0, "on_file": 0}
    staged = wrote["appended"]
    _save_cursor({"next_page": page, "seen_refs": sorted(seen)[-5000:]})
    return {"processed_notebooks": processed, "cards_extracted": len(all_cards), "staged_appended": staged,
            "failed_pulls": failed, "next_page": page, "staged_path": wrote.get("path"), **BOUNDARY}


# ── self-test (fully offline: fixture notebook + stub LLM + stub Kaggle) ──────────────────────────────────────

_FIXTURE_NOTEBOOK = (
    "# Titanic feature engineering\n"
    "import pandas as pd\n"
    "df = pd.read_csv('train.csv')\n"
    "df['FamilySize'] = df['SibSp'] + df['Parch'] + 1\n"
    "from sklearn.ensemble import GradientBoostingClassifier\n"
    "model = GradientBoostingClassifier().fit(X, y)\n"
    "df[['PassengerId','Survived']].to_csv('submission.csv', index=False)\n")


def _stub_llm(system: str, user: str) -> str:
    if "Remix" in user or "remix" in user:
        return ('noise {"remixes":[{"name":"cross-domain family-size feature","mechanism":"pandas column '
                'arithmetic generalized to any count columns","input":"a dataframe","output":"an engineered '
                'feature column","steps":["sum the count columns","add one"],"tags":["feature_engineering"],'
                '"remix_of":["family size feature"]}]} tail')
    return ('here is the json {"primitives":[{"name":"family size feature","mechanism":"pandas column '
            'arithmetic over SibSp/Parch to derive FamilySize","input":"a passenger dataframe","output":"a '
            'FamilySize column","steps":["add SibSp and Parch","add one"],"tags":["feature_engineering",'
            '"pandas"]},{"name":"gradient boosting classifier","mechanism":"sklearn '
            'GradientBoostingClassifier fit on engineered features","input":"a feature matrix","output":"a '
            'fitted classifier","steps":["instantiate GBC","fit on X,y"],"tags":["model","sklearn"]}]}')


def _self_test() -> int:
    import tempfile  # noqa: PLC0415
    checks: list[tuple[str, bool]] = []

    kernel = {"ref": "user/titanic-fe", "title": "Titanic FE", "author": "user"}
    result = process_notebook(kernel, _FIXTURE_NOTEBOOK, _stub_llm, do_remix=True)
    checks.append(("decompose extracts >=2 primitive cards from the fixture notebook",
                   result["n_decomposed"] >= 2))
    checks.append(("remix adds at least one remix card (origin=remix, remix_of set)",
                   any(c["provenance"]["origin"] == "remix" and c.get("remix_of") for c in result["cards"])))
    checks.append(("cards carry the source HANDLE + DIGEST but NOT the raw body",
                   all(c["provenance"]["source_handle"].startswith("kaggle://") for c in result["cards"])
                   and all("read_csv" not in json.dumps(c) for c in result["cards"])))
    checks.append(("every card id recomputes from canonical_id (title+blackbox+digest)",
                   all(not _validate_card(c) for c in result["cards"])))
    checks.append(("edges are CamelCase typed names",
                   all(_CAMEL_EDGE_RE.match(c["input_edge"]) and _CAMEL_EDGE_RE.match(c["output_edge"])
                       for c in result["cards"])))
    checks.append(("every card is candidate/serves_truth=false",
                   all(c["candidate"] is True and c["serves_truth"] is False for c in result["cards"])))

    # unparseable model reply is a RECORDED error, never a fabricated card
    bad = process_notebook(kernel, _FIXTURE_NOTEBOOK, lambda s, u: "no json here", do_remix=True)
    checks.append(("an unparseable model reply yields 0 cards + a recorded error, never fabrication",
                   bad["n_total"] == 0 and bad["errors"]))

    # CSV parse of a kaggle-list style output
    csv_out = "ref,title,author,lastRunTime\nu/a,A Notebook,u,2026\nu/b,B Notebook,u,2026\n"
    kernels = _parse_kaggle_csv(csv_out)
    checks.append(("kaggle CSV listing parses to refs", [k["ref"] for k in kernels] == ["u/a", "u/b"]))

    # notebook text extraction strips outputs, keeps code+markdown, bounded
    with tempfile.TemporaryDirectory() as td:
        nb = {"cells": [{"cell_type": "code", "source": ["import pandas as pd\n"], "outputs": [{"x": 1}]},
                        {"cell_type": "markdown", "source": ["# Title"]},
                        {"cell_type": "code", "source": ["print(1)"], "execution_count": 3}]}
        (Path(td) / "k.ipynb").write_text(json.dumps(nb))
        text = read_notebook_text(Path(td))
        checks.append(("notebook extraction keeps code+markdown, drops outputs",
                       text is not None and "import pandas" in text and "# Title" in text
                       and "execution_count" not in text and "outputs" not in text))

    # end-to-end run loop with STUB kaggle + stub llm (no network) -> staged file in a tmp path
    def _stub_lister(page: int, size: int, *, search: str = "") -> list[dict[str, Any]]:
        return [{"ref": f"u/nb{page}", "title": f"NB {page}", "author": "u"}] if page <= 2 else []

    def _stub_puller(ref: str, dest: Path) -> Optional[str]:
        return _FIXTURE_NOTEBOOK

    with tempfile.TemporaryDirectory() as td:
        staged = Path(td) / STAGED_FILENAME
        orig = staged_path
        try:
            globals()["staged_path"] = lambda: staged  # noqa: B010
            summary = run_foundry(llm=_stub_llm, lister=_stub_lister, puller=_stub_puller, max_notebooks=2,
                                  page_size=5, search="", rate_limit_seconds=0.0, resume=False, do_remix=True,
                                  sleep=lambda _s: None)
        finally:
            globals()["staged_path"] = orig
        checks.append(("end-to-end run processes notebooks and STAGES cards to the candidate file",
                       summary["processed_notebooks"] == 2 and summary["staged_appended"] >= 2
                       and Path(summary["staged_path"]).name == STAGED_FILENAME))
        # append-dedupe: staging the same cards again writes nothing new
        again = stage_cards(process_notebook(kernel, _FIXTURE_NOTEBOOK, _stub_llm)["cards"], target_path=staged)
        checks.append(("append-dedupe: identical cards re-stage to 0", again["appended"] == 0))

    # write-safety: refuse a verified corpus filename
    refused = False
    try:
        stage_cards(result["cards"][:1],
                    target_path=Path(tempfile.gettempdir()) / "verified_factory_primitive_cards.jsonl")
    except ValueError:
        refused = True
    checks.append(("stage_cards REFUSES a verified corpus filename", refused))

    failed_names = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
    if failed_names:
        print(f"\n{len(failed_names)} FAILURES: {failed_names}")
        return 1
    print("\nPASS - kaggle_notebook_primitive_foundry: offline pipeline proven end-to-end (fixture notebook + "
          "stub model + stub Kaggle) — decompose -> remix -> canonical-id staging with source handle+digest "
          "(no raw body in cards), unparseable replies recorded not fabricated, append-dedupe, and write-safety "
          "refusing verified corpus files. Live Kaggle/LLM lanes are opt-in. serves_truth=false.")
    return 0


def _run(args: argparse.Namespace) -> int:
    if not args.self_test:
        if args.kaggle and not _kaggle_env_ready():
            print("Kaggle creds not found. Set KAGGLE_USERNAME + KAGGLE_KEY or place ~/.kaggle/kaggle.json, "
                  "then re-run. (Get the key from kaggle.com -> Account -> Create New API Token.)")
            return 2
        if args.use_llm:
            llm = make_llm_transport(args.provider, args.model)
        else:
            print("no --use-llm: nothing to decompose. Add --use-llm --provider <ollama|openwebui|openrouter> "
                  "--model <gemma-4-coding|...>.")
            return 2
        lister = kaggle_list_kernels if args.kaggle else (lambda *a, **k: [])
        puller = kaggle_pull_kernel if args.kaggle else (lambda *a, **k: None)
        summary = run_foundry(llm=llm, lister=lister, puller=puller, max_notebooks=args.max_notebooks,
                              page_size=args.page_size, search=args.search,
                              rate_limit_seconds=args.rate_limit_seconds, resume=args.resume,
                              do_remix=not args.no_remix)
        out = _base_dir() / "run_receipt.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(summary, indent=2, sort_keys=True))
        print(json.dumps(summary, indent=2, sort_keys=True))
        print(f"\nreceipt: {out}")
        return 0
    return _self_test()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true", help="offline end-to-end verification (no creds/network)")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--kaggle", action="store_true", help="use the real Kaggle API (needs creds)")
    ap.add_argument("--use-llm", action="store_true", help="decompose via a real model lane")
    ap.add_argument("--provider", default="ollama", help="ollama | openwebui | openrouter")
    ap.add_argument("--model", default="gemma-4-coding")
    ap.add_argument("--max-notebooks", type=int, default=50)
    ap.add_argument("--page-size", type=int, default=100)
    ap.add_argument("--search", default="")
    ap.add_argument("--rate-limit-seconds", type=float, default=2.0)
    ap.add_argument("--resume", action="store_true", help="continue from the persisted page cursor")
    ap.add_argument("--no-remix", action="store_true")
    args = ap.parse_args(argv)
    if args.self_test or args.run:
        return _run(args)
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
