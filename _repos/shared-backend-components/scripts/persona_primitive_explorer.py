#!/usr/bin/env python3
"""scripts.persona_primitive_explorer — take on the persona of EVERY worker and ideate the primitives their
work needs. Enumerate role × industry × personality × company-type × country × era = millions of personas;
for each, derive WHAT they do and WHY, the PRIMARY software primitive involved, ALTERNATIVE primitives (the
multi-path law made data — every task has a portfolio of options), the INFRASTRUCTURE they run on, and the
LIBRARIES/tools they reach for. Then optionally EXPLORE THE WORLD: an LLM arm (our lanes) that ideates NOVEL
primitives, systems, and CHAINS of primitives beyond the deterministic seed.

The persona is context: a risk-averse auditor at a government agency in the mainframe era needs different
primitives (and different alternatives) than an exploratory ML engineer at an AI-native startup. Reuses the
computed operation/tool/infra vocabularies from ``primitive_grid_remixer`` (single source, DRY). All counts
are computed; the walk is a deterministic COPRIME full-period stride to ``--target``; ids are minted only by
``canonical_id``; every card is ``candidate=true / serves_truth=false`` (generation is never promotion); the
staged file is a NEW file next to — never equal to — the verified corpus. Quality is a NON-DESTRUCTIVE routing
signal (owner law: nothing discarded).

    python3 scripts/persona_primitive_explorer.py --self-test
    python3 scripts/persona_primitive_explorer.py --mint --target 200000
    python3 scripts/persona_primitive_explorer.py --explore --sample 20 --provider ollama --model glm-5.2
"""
from __future__ import annotations

import sys
from pathlib import Path

# ── substrate-root bootstrap (sentinel; mirrors scripts/primitive_grid_remixer.py) ───────────────────────────
_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots, resource  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import json  # noqa: E402
import re  # noqa: E402
from typing import Any, Callable, Iterator, Optional  # noqa: E402

try:
    from src.teleon.experiments.ids import canonical_id  # noqa: E402
except Exception as exc:  # noqa: BLE001
    raise SystemExit(f"persona_primitive_explorer requires canonical_id; import failed: {exc}")

# REUSE the computed primitive/infra/tool vocabularies (single source — no re-declaration).
import scripts.primitive_grid_remixer as _grid  # noqa: E402

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}

PERSONA_ID_PREFIX = "prim-persona"
PERSONA_RECORD_TYPE = "persona_primitive_candidate"
STAGED_FILENAME = "persona_primitive_candidates.jsonl"
_VERIFIED_CORPUS_FILENAMES = frozenset({"verified_factory_primitive_cards.jsonl", "primitive_edge_cards.jsonl"})
_PROMOTION_BLOCKERS = ("source_evidence", "correctness_proof", "usefulness_or_enrichment", "license_review")
_CAMEL_EDGE_RE = re.compile(r"^[A-Z][A-Za-z0-9]*$")
_COPRIME_STRIDE = 2147483647  # 2**31-1, coprime to the persona-grid size

# ── the PERSONA axes (single source; extensible; counts computed). ───────────────────────────────────────────
# role → (title, the verb-family of ops they do)
_ROLES: tuple[tuple[str, str], ...] = (
    ("data engineer", "ingest"), ("ml engineer", "embed"), ("sre", "monitor"), ("security analyst", "audit"),
    ("backend engineer", "route"), ("frontend engineer", "transform"), ("data scientist", "score"),
    ("data analyst", "aggregate"), ("devops engineer", "schedule"), ("platform engineer", "replicate"),
    ("qa engineer", "validate"), ("product manager", "rank"), ("financial analyst", "reconcile"),
    ("actuary", "forecast"), ("bioinformatician", "classify"), ("journalist", "extract"),
    ("legal analyst", "redact"), ("teacher", "annotate"), ("logistics coordinator", "route"),
    ("game developer", "stream"), ("embedded engineer", "compress"), ("research scientist", "sample"),
    ("compliance officer", "verify"), ("support engineer", "search"), ("growth marketer", "cluster"),
    ("database administrator", "index"), ("network engineer", "throttle"), ("hardware engineer", "checkpoint"),
    ("robotics engineer", "filter"), ("quantitative trader", "rank"),
)
# industry → the entity/domain they work on
_INDUSTRIES: tuple[tuple[str, str], ...] = (
    ("finance", "transactions"), ("healthcare admin", "patient records"), ("logistics", "shipments"),
    ("ecommerce", "orders"), ("telecom", "call records"), ("education", "student records"),
    ("energy", "grid telemetry"), ("agriculture", "yield data"), ("manufacturing", "sensor streams"),
    ("media", "content assets"), ("government", "public records"), ("gaming", "player events"),
    ("biotech", "sequence data"), ("insurance-adjacent", "claims-shape records"), ("real estate", "parcel records"),
    ("transportation", "transit schedules"), ("cybersecurity", "threat feeds"), ("aerospace", "flight telemetry"),
    ("retail", "inventory records"), ("advertising", "impression logs"), ("scientific computing", "simulation grids"),
    ("civic tech", "open datasets"),
)
# personality archetype → the motivation phrase (WHY they do it)
_PERSONALITIES: tuple[tuple[str, str], ...] = (
    ("the optimizer", "to cut cost and latency to the bone"),
    ("the auditor", "to guarantee correctness, provenance, and compliance"),
    ("the builder", "to ship a working end-to-end path fast"),
    ("the firefighter", "to keep it running under load and recover from failure"),
    ("the explorer", "to discover what is possible and prototype it"),
    ("the standardizer", "to make everything conform, typed, and reusable"),
    ("the scaler", "to make it survive 100x growth"),
    ("the minimalist", "to remove every unnecessary moving part"),
    ("the integrator", "to wire disparate systems into one flow"),
    ("the skeptic", "to verify every claim before trusting it"),
)
# company type → the constraint it imposes
_COMPANY_TYPES: tuple[tuple[str, str], ...] = (
    ("early startup", "with no budget and one machine"), ("scale-up", "under fast growth"),
    ("enterprise", "under governance and legacy constraints"), ("agency", "across many client stacks"),
    ("non-profit", "on donated/cheap infrastructure"), ("government agency", "under strict regulation"),
    ("research lab", "for reproducibility over speed"), ("SMB", "with a small generalist team"),
    ("solo/freelance", "doing everything alone"), ("big tech", "at planet scale"),
)
# country/region → the operating context (regulatory/scale/infra)
_COUNTRIES: tuple[str, ...] = (
    "the US", "the EU", "the UK", "India", "China", "Brazil", "Nigeria", "Japan", "Germany", "Canada",
    "Australia", "Singapore", "Kenya", "Indonesia", "Mexico", "South Korea", "the UAE", "Ghana",
)
# era → the technology regime available (what primitives even exist)
_ERAS: tuple[tuple[str, str], ...] = (
    ("the mainframe era", "batch jobs on shared iron"), ("the client-server era", "fat clients on a LAN"),
    ("the web 2.0 era", "LAMP stacks and AJAX"), ("the cloud-native era", "containers and managed services"),
    ("the mobile-first era", "offline-first apps and sync"), ("the big-data era", "distributed batch + streams"),
    ("the AI-native era", "models, embeddings, and agents"), ("the edge era", "compute pushed to devices"),
)

_STOP = frozenset("a an the for of to in on with and or via using into from as is are be that this it one".split())

_FRAMES: tuple[str, ...] = (
    "As {role} in {industry} at {company} in {country} during {era} ({era_desc}), you {op} {entity} "
    "{motivation}. The core primitive: {primary}; alternatives: {alts}. You run it on {infra} with {libs}.",
    "Persona: {personality} {role}, {industry}, {country}, {era}. What you do: {op} {entity} {motivation} "
    "{company}. Primary primitive {primary} (or {alts}); infra {infra}; tools {libs}.",
    "In {era} ({era_desc}), {role} at {company} in {industry} ({country}) must {op} {entity} {motivation}. "
    "Reach for {primary}; if that fails, {alts}. Substrate: {infra}; libraries: {libs}.",
    "{role} · {industry} · {country} · {era}: the job is to {op} {entity} {motivation}. The reusable "
    "primitive is {primary} (alternatives {alts}), running on {infra} using {libs}.",
)


def axis_sizes() -> dict[str, int]:
    return {"roles": len(_ROLES), "industries": len(_INDUSTRIES), "personalities": len(_PERSONALITIES),
            "company_types": len(_COMPANY_TYPES), "countries": len(_COUNTRIES), "eras": len(_ERAS)}


def persona_grid_size() -> int:
    s = axis_sizes()
    return s["roles"] * s["industries"] * s["personalities"] * s["company_types"] * s["countries"] * s["eras"]


_AXIS_ORDER = ("roles", "industries", "personalities", "company_types", "countries", "eras")


def _camel(*words: str) -> str:
    parts = re.split(r"[^A-Za-z0-9]+", " ".join(words))
    return ("".join(p[:1].upper() + p[1:] for p in parts if p) or "X")[:60]


def _primitive_portfolio(role_verb: str, idx_seed: int) -> tuple[str, list[str], str, str]:
    """A primary primitive + alternatives + infra + libs for a role's verb-family. Draws from the grid's
    COMPUTED vocab (reuse). The primary is an op in the role's verb-family; alternatives are sibling ops."""
    ops = _grid._OPERATIONS  # noqa: SLF001 — the single computed operations vocab
    family = [op for op in ops if op.split()[0] == role_verb] or ops
    primary = family[idx_seed % len(family)]
    # alternatives: other ops on the same object (the multi-path portfolio for the same target)
    obj = primary.split()[-1]
    alts = [op for op in ops if op.split()[-1] == obj and op != primary]
    alt_pick = [alts[(idx_seed + j) % len(alts)] for j in range(1, 3)] if alts else []
    infra = _grid._INFRA_TOOLS[idx_seed % len(_grid._INFRA_TOOLS)]  # noqa: SLF001
    libs = _grid._SOFTWARE_TOOLS[(idx_seed // 2) % len(_grid._SOFTWARE_TOOLS)]  # noqa: SLF001
    return primary, alt_pick, infra, libs


def _persona_card(idx: tuple[int, int, int, int, int, int]) -> dict[str, Any]:
    ri, ii, pi, ci, coi, ei = idx
    role, role_verb = _ROLES[ri]
    industry, entity = _INDUSTRIES[ii]
    personality, motivation = _PERSONALITIES[pi]
    company, company_desc = _COMPANY_TYPES[ci]
    country = _COUNTRIES[coi]
    era, era_desc = _ERAS[ei]
    seed = ri * 7 + ii * 5 + pi * 3 + ci + coi + ei
    primary, alts, infra, libs = _primitive_portfolio(role_verb, seed)
    alts_str = ", ".join(alts) if alts else "none catalogued yet"

    title = f"{role} in {industry} ({country}, {era}): {primary} for {entity}"
    frame = _FRAMES[seed % len(_FRAMES)]
    blackbox = frame.format(role=role, personality=personality, industry=industry, company=company_desc,
                            country=country, era=era, era_desc=era_desc, op=role_verb, entity=entity,
                            motivation=motivation, primary=primary, alts=alts_str, infra=infra, libs=libs)
    tokens = []
    for t in (role_verb, entity, primary.split()[-1], infra.replace("_", " ")):
        for w in str(t).split():
            wl = w.lower()
            if wl not in _STOP and wl not in tokens:
                tokens.append(wl)
    input_edge = _camel(entity.split()[-1], role_verb, "input")
    output_edge = _camel(primary.split()[0], infra, "result")
    pid = canonical_id(PERSONA_ID_PREFIX, title, blackbox)
    return {
        "record_type": PERSONA_RECORD_TYPE, "schema_version": 1, "kind": "route.primitive",
        "primitive_id": pid, "title": title[:180], "blackbox": blackbox[:1400],
        "input_edge": input_edge, "output_edge": output_edge, "blocking_keys": tokens,
        "persona": {"role": role, "industry": industry, "personality": personality, "company_type": company,
                    "country": country, "era": era},
        "primary_primitive": primary, "alternative_primitives": alts, "infrastructure": infra, "libraries": libs,
        "capability_tags": [f"role:{role.replace(' ', '_')}", f"industry:{industry.replace(' ', '_')}",
                            f"personality:{personality.replace(' ', '_')}", f"era:{era.replace(' ', '_')}",
                            f"op:{primary.replace(' ', '_')}", f"infra:{infra}"],
        "contract": {"input": f"{entity} for a {role} in {industry} ({country})",
                     "output": f"a typed result of {primary} via {infra}"},
        "provenance": {"minter": "scripts.persona_primitive_explorer", "persona_grid_size": persona_grid_size()},
        "promotion_blockers": list(_PROMOTION_BLOCKERS), "readiness": "persona_candidate_unproven", **BOUNDARY,
    }


def _strided_indices(target: int) -> Iterator[tuple[int, int, int, int, int, int]]:
    total = persona_grid_size()
    sizes = [axis_sizes()[k] for k in _AXIS_ORDER]
    for i in range(min(target, total)):
        flat = (i * _COPRIME_STRIDE) % total
        idx = []
        rem = flat
        for sz in reversed(sizes):
            idx.append(rem % sz)
            rem //= sz
        yield tuple(reversed(idx))  # type: ignore[misc]


def mint_personas(target: int) -> list[dict[str, Any]]:
    if target < 1:
        raise ValueError("target must be >= 1")
    cards: list[dict[str, Any]] = []
    seen: set = set()
    for idx in _strided_indices(target):
        card = _persona_card(idx)
        if card["primitive_id"] in seen:
            raise ValueError(f"duplicate persona mint for {card['title']!r}")
        seen.add(card["primitive_id"])
        cards.append(card)
    return cards


def validate_persona_card(card: dict[str, Any]) -> list[str]:
    problems: list[str] = []
    if card.get("primitive_id") != canonical_id(PERSONA_ID_PREFIX, card.get("title", ""), card.get("blackbox", "")):
        problems.append("primitive_id does not recompute")
    for ef in ("input_edge", "output_edge"):
        if not _CAMEL_EDGE_RE.match(str(card.get(ef) or "")):
            problems.append(f"{ef} not CamelCase")
    if card.get("serves_truth") is not False or card.get("candidate") is not True:
        problems.append("candidate boundary not stamped")
    if not card.get("primary_primitive"):
        problems.append("no primary primitive")
    text = f"{card.get('title','')} {card.get('blackbox','')}".lower()
    if not all(t in text for t in card.get("blocking_keys", [])[:2]):
        problems.append("blackbox does not carry its leading tokens")
    return problems


def staged_path() -> Path:
    return resource("data") / "dev-intel" / "aidevobserver_edge_foundry" / STAGED_FILENAME


def write_staged(cards: list[dict[str, Any]], target_path: Optional[Path] = None) -> dict[str, Any]:
    from scripts._jsonl import read_jsonl_tolerant  # noqa: PLC0415
    p = target_path or staged_path()
    if p.name != STAGED_FILENAME:
        raise ValueError(f"refusing to write to {p.name!r} — only {STAGED_FILENAME!r} allowed")
    if p.is_symlink():
        raise ValueError(f"refusing to write through a symlink at {p}")
    if p.exists() and (p.resolve().name in _VERIFIED_CORPUS_FILENAMES or p.resolve().name != STAGED_FILENAME):
        raise ValueError(f"resolved target {p.resolve()} is not the staged file — refused")
    for c in cards:
        probs = validate_persona_card(c)
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


def quality_report(cards: list[dict[str, Any]]) -> dict[str, Any]:
    from scripts.primitive_usefulness_gate import measure_pool  # noqa: PLC0415
    m = measure_pool(cards, "persona_primitive_mint")
    return {k: m[k] for k in ("n_cards_scored", "placeholder_rate", "weak_rate", "verdict_counts",
                              "stamped_clusters")}


# ── EXPLORE THE WORLD: an LLM arm that ideates NOVEL primitives / systems / CHAINS per persona ────────────────

_EXPLORE_SYSTEM = ("You take on a worker's persona and ideate the reusable software PRIMITIVES their real work "
                   "needs — including NOVEL ones and CHAINS of primitives. Reply ONLY as JSON.")


def _explore_prompt(persona: dict[str, str]) -> str:
    return (f"You are {persona['personality']}, a {persona['role']} in {persona['industry']} at a "
            f"{persona['company_type']} in {persona['country']} during {persona['era']}.\n"
            "Ideate the reusable software primitives your real work needs. Reply ONLY as JSON:\n"
            '{"tasks":[{"what":"...","why":"...","primary_primitive":"...",'
            '"alternative_primitives":["...","..."],"infrastructure":"...","libraries":["..."],'
            '"novel_primitive":"a primitive not commonly catalogued","primitive_chain":["step1","step2","step3"]}]}')


def explore(personas: list[dict[str, str]], transport: Callable[[str, str], dict[str, Any]]) -> dict[str, Any]:
    """For a sample of personas, ask an LLM lane to ideate novel primitives + chains. Failures recorded, never
    faked. Returns discovered cards (candidate) + a ledger."""
    from scripts._jsonl import read_jsonl_tolerant  # noqa: PLC0415,F401
    discovered: list[dict[str, Any]] = []
    ledger: list[dict[str, Any]] = []
    for persona in personas:
        resp = transport(_EXPLORE_SYSTEM, _explore_prompt(persona))
        if not resp.get("ok"):
            ledger.append({"persona": persona.get("role"), "outcome": "failed", "detail": resp.get("error")})
            continue
        parsed = _extract_json(resp.get("text") or "")
        tasks = parsed.get("tasks") if isinstance(parsed, dict) else None
        if not isinstance(tasks, list) or not tasks:
            ledger.append({"persona": persona.get("role"), "outcome": "unparseable"})
            continue
        for t in tasks:
            title = f"{persona['role']} ({persona['industry']}): {str(t.get('what') or '')[:80]}"
            blackbox = (f"[explored] {t.get('what')} — {t.get('why')}. Primary: {t.get('primary_primitive')}; "
                        f"alternatives: {', '.join(t.get('alternative_primitives') or [])}; novel: "
                        f"{t.get('novel_primitive')}; chain: {' -> '.join(t.get('primitive_chain') or [])}. "
                        f"Infra: {t.get('infrastructure')}; libs: {', '.join(t.get('libraries') or [])}.")
            if not (t.get("what") and t.get("primary_primitive")):
                continue
            pid = canonical_id(PERSONA_ID_PREFIX, title, blackbox)
            discovered.append({"record_type": "explored_persona_primitive_candidate", "primitive_id": pid,
                               "title": title[:180], "blackbox": blackbox[:1400],
                               "input_edge": _camel(persona["role"], "input"),
                               "output_edge": _camel(str(t.get("primary_primitive") or "result"), "result"),
                               "persona": persona, "primitive_chain": t.get("primitive_chain") or [],
                               "novel_primitive": t.get("novel_primitive"),
                               "provenance": {"minter": "scripts.persona_primitive_explorer.explore",
                                              "provider": resp.get("provider")}, **BOUNDARY})
        ledger.append({"persona": persona.get("role"), "outcome": "explored", "n_tasks": len(tasks)})
    return {"discovered": discovered, "ledger": ledger, "n_personas": len(personas),
            "n_discovered": len(discovered), **BOUNDARY}


def _extract_json(text: str) -> Optional[Any]:
    start = text.find("{")
    if start == -1:
        return None
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start:i + 1])
                except json.JSONDecodeError:
                    return None
    return None


def _self_test() -> int:
    checks: list[tuple[str, bool]] = []
    checks.append(("persona grid is COMPUTED and in the millions",
                   persona_grid_size() == len(_ROLES) * len(_INDUSTRIES) * len(_PERSONALITIES)
                   * len(_COMPANY_TYPES) * len(_COUNTRIES) * len(_ERAS) and persona_grid_size() > 1_000_000))
    cards = mint_personas(600)
    checks.append(("mints deterministically + byte-identical remint",
                   len(cards) == 600 and json.dumps(cards, sort_keys=True) == json.dumps(mint_personas(600), sort_keys=True)))
    checks.append(("every card validates (id recompute, edges, boundary, primary primitive)",
                   all(not validate_persona_card(c) for c in cards)))
    checks.append(("every card carries a primitive PORTFOLIO (primary + alternatives + infra + libs)",
                   all(c["primary_primitive"] and "infrastructure" in c and "libraries" in c for c in cards)
                   and any(c["alternative_primitives"] for c in cards)))
    checks.append(("cards carry the full persona (role/industry/personality/company/country/era)",
                   all(set(c["persona"]) == {"role", "industry", "personality", "company_type", "country", "era"}
                       for c in cards)))

    def _distinct(axis: str) -> int:
        return len({c["persona"][axis] for c in cards})
    checks.append(("the stride spreads across persona axes",
                   _distinct("role") >= 15 and _distinct("industry") >= 10 and _distinct("country") >= 8
                   and _distinct("era") >= 6 and _distinct("personality") >= 6))
    import tempfile  # noqa: PLC0415
    refused = False
    try:
        write_staged(cards[:1], target_path=Path(tempfile.gettempdir()) / "verified_factory_primitive_cards.jsonl")
    except ValueError:
        refused = True
    checks.append(("write_staged REFUSES a verified corpus filename", refused))
    with tempfile.TemporaryDirectory() as td:
        tp = Path(td) / STAGED_FILENAME
        a = write_staged(cards[:40], target_path=tp)
        b = write_staged(cards[:40], target_path=tp)
        checks.append(("append-dedupe", a["appended"] == 40 and b["appended"] == 0))
    qr = quality_report(cards)
    checks.append(("usefulness gate scores the mint (routing signal)",
                   set(qr["verdict_counts"]) == {"pass", "weak", "placeholder"}))

    # explore arm with a stub transport: discovers novel primitives + chains; failures recorded
    def _stub(system: str, user: str) -> dict[str, Any]:
        return {"ok": True, "provider": "stub",
                "text": json.dumps({"tasks": [{"what": "reconcile ledgers nightly", "why": "audit compliance",
                                               "primary_primitive": "reconcile transactions",
                                               "alternative_primitives": ["diff transactions", "hash transactions"],
                                               "infrastructure": "postgres", "libraries": ["pandas"],
                                               "novel_primitive": "drift-aware ledger reconciler",
                                               "primitive_chain": ["extract", "normalize", "reconcile", "sign"]}]})}
    ex = explore([cards[0]["persona"]], _stub)
    checks.append(("explore discovers novel primitives + chains from a persona",
                   ex["n_discovered"] >= 1 and ex["discovered"][0]["primitive_chain"]
                   and ex["discovered"][0]["novel_primitive"]))
    fail = explore([cards[0]["persona"]], lambda s, u: {"ok": False, "error": "rate_limited"})
    checks.append(("explore records a lane failure, never fabricates", fail["n_discovered"] == 0 and fail["ledger"]))

    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print(f"\nPASS - persona_primitive_explorer: {persona_grid_size():,}-persona grid (role x industry x "
          f"personality x company x country x era); each card carries what/why + a PRIMITIVE PORTFOLIO "
          f"(primary + alternatives + infra + libraries); deterministic strided mint; the EXPLORE arm ideates "
          f"novel primitives + chains via our lanes (failures recorded); usefulness gate = NON-DESTRUCTIVE "
          f"routing. serves_truth=false.")
    return 0


def _mint(target: int) -> int:
    cards = mint_personas(target)
    qr = quality_report(cards)
    wrote = write_staged(cards)
    rec = {"record_type": "persona_primitive_mint_receipt", "target": target, "minted": len(cards),
           "appended": wrote["appended"], "on_file": wrote["on_file"], "persona_grid_size": persona_grid_size(),
           "axis_sizes": axis_sizes(),
           "distinct_axis_values": {ax: len({c["persona"][ax] for c in cards})
                                    for ax in ("role", "industry", "personality", "company_type", "country", "era")},
           "quality_gate": qr, "routing": "placeholder/weak route to enrichment; NONE discarded", **BOUNDARY}
    out = resource("data") / "dev-intel" / "session_emulation" / "persona_primitive_mint_receipt.json"
    out.write_text(json.dumps(rec, indent=2, sort_keys=True))
    print(json.dumps({k: rec[k] for k in ("target", "minted", "appended", "persona_grid_size",
                                          "quality_gate")}, indent=2, sort_keys=True))
    print(f"\nstaged: {wrote['path']}\nreceipt: {out}")
    return 0


def _explore_run(sample: int, provider: str, model: str) -> int:
    from scripts import _llm_client  # noqa: PLC0415
    prov = _llm_client.resolve_provider(provider)

    def _t(system: str, user: str) -> dict[str, Any]:
        try:
            r = _llm_client.chat(model, system, user, prov)  # inherit the high-ceiling default; never truncate generation
            if r.get("error"):
                return {"ok": False, "error": str(r["error"])[:120]}
            return {"ok": True, "text": r.get("text") or "", "provider": provider}
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "error": str(exc)[:120]}
    personas = [c["persona"] for c in mint_personas(sample)]
    result = explore(personas, _t)
    if result["discovered"]:
        wrote = write_staged([_reshape_explored(c) for c in result["discovered"]])
        result["staged"] = wrote["appended"]
    out = resource("data") / "dev-intel" / "session_emulation" / "persona_explore_receipt.json"
    out.write_text(json.dumps({k: result[k] for k in ("n_personas", "n_discovered", "ledger")}
                              | ({"staged": result.get("staged", 0)}) | BOUNDARY, indent=2, sort_keys=True))
    print(json.dumps({"n_personas": result["n_personas"], "n_discovered": result["n_discovered"],
                      "staged": result.get("staged", 0)}, indent=2))
    print(f"\nreceipt: {out}")
    return 0


def _reshape_explored(c: dict[str, Any]) -> dict[str, Any]:
    """Give an explored card the fields write_staged validates (primary_primitive, blocking_keys)."""
    toks = [w.lower() for w in re.findall(r"[a-z]+", c.get("title", "").lower())][:4] or ["explored"]
    return {**c, "primary_primitive": c.get("novel_primitive") or "explored", "blocking_keys": toks,
            "record_type": PERSONA_RECORD_TYPE}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--mint", action="store_true")
    ap.add_argument("--target", type=int, default=200_000)
    ap.add_argument("--explore", action="store_true", help="LLM arm: ideate novel primitives + chains per persona")
    ap.add_argument("--sample", type=int, default=20)
    ap.add_argument("--provider", default="ollama")
    ap.add_argument("--model", default="glm-5.2")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.explore:
        return _explore_run(args.sample, args.provider, args.model)
    if args.mint:
        return _mint(args.target)
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
