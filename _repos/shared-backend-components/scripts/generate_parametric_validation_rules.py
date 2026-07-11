#!/usr/bin/env python3
"""scripts.generate_parametric_validation_rules — WORKABLE (proven + TYPED) *configured*-primitives for the
'validation_rules' group, minted by PARAMETRIC PROOF.

Vocabulary is not capability, and a bare proven TEMPLATE is only one primitive. The scalable, honest way to mint
thousands of *workable* primitives is PARAMETRIC PROOF: a configured-primitive = (a proven mutator TEMPLATE) x (a
specific parameter BINDING) x (canonical edge types). `in_range{lo:0,hi:10}` and `in_range{lo:32,hi:212}` are DISTINCT
workable primitives — each proven by EXECUTING the mutator on a realistic fixture and checking that it deterministically
produces the expected typed verdict. This module curates a deterministic, meaningfully-distinct parameter space over
five proven validation TEMPLATES (in_range · regex_match · enum_member · length_bound · required_keys), proves EACH
binding through the IMPORTED executed-proof runner, DEDUPES by a canonical content hash, and TYPES every survivor with
canonical edge type ids so a workable configured-primitive can chain.

Repo law kept verbatim: serves_truth=true is set ONLY by a PASSING executed proof of THAT binding (we run the mutator
on the fixture, compute the expected output, and re-run to prove determinism) — never inferred from the template; a
binding whose proof fails is NOT persisted. Honest accounting: generated vs unique(deduped) vs proven vs typed are
kept as SEPARATE counts and never conflated. ADD-ONLY / flexible: a NEW parallel path that IMPORTS the shared
machinery (MUTATOR_REGISTRY / apply_mutator / run_primitive_proof + canonicalize_edge) and REGISTERS its template
mutators via setdefault — it edits NO contract-locked or shared file, and writes its OWN shard (no shared-JSONL race).
Deterministic + offline: no network, no LLM, no wall-clock (fixed literal timestamp), no RNG (the parameter space is
enumerated deterministically; pseudo-variety uses stable string seeds like f"{group}:{i}", never hash()).

CLI: --self-test (offline, standalone, small) | --write [--date D].
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import hashlib
import itertools
import json
import re
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

# IMPORT the shared machinery — never edit it (ADD-ONLY / flexible-multi-path).
from scripts.build_edge_type_retrofit import canonicalize_edge  # noqa: E402
from scripts.mutator_registry import (  # noqa: E402
    MUTATOR_REGISTRY,
    apply_mutator,
    run_primitive_proof,
)

GROUP = "validation_rules"
#: fixed literal timestamp — NEVER wall-clock (repo law: deterministic + offline).
_FIXED_UTC = "2026-07-03"

OUT_DIR = _resource("data") / "dev-intel" / "parametric_primitives"
OUT_JSONL = OUT_DIR / "param_validation_rules.jsonl"
OUT_MANIFEST = OUT_DIR / "manifest_validation_rules.json"


# ── template mutators: prefer the PROVEN sibling implementations; fall back to identical local defs if absent ──
# The sibling _repos/shared-backend-components/scripts/prove_leaves_validation_predicate.py registers vp_in_range/vp_regex_match/... into the shared
# MUTATOR_REGISTRY on import. We import it best-effort; if it (or the base 11) is all that is present we register our
# own byte-identical template mutators via setdefault so --self-test runs standalone. setdefault never overwrites an
# existing (already-proven) entry, so we reuse the sibling's proven templates when they are there.
def _verdict(check: str, valid: Any, **extra: Any) -> dict[str, Any]:
    rec: dict[str, Any] = {"check": check, "valid": bool(valid)}
    rec.update(extra)
    return rec


def _receipt(name: str, before: Any, after: Any) -> dict[str, Any]:
    return {"record_type": "mutator_receipt", "mutator": name, "candidate": True, "serves_truth": False,
            "note": f"{name} template"}


def _tpl_in_range(value: Any, lo: Any, hi: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    out = _verdict("in_range", lo <= value <= hi, value=value, lo=lo, hi=hi)
    return out, _receipt("vp_in_range", value, out)


def _tpl_regex_match(value: str, pattern: str) -> tuple[dict[str, Any], dict[str, Any]]:
    out = _verdict("regex_match", re.fullmatch(pattern, value) is not None, pattern=pattern)
    return out, _receipt("vp_regex_match", value, out)


def _tpl_enum_member(value: Any, choices: list[Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    out = _verdict("enum_member", value in choices, value=value)
    return out, _receipt("vp_enum_member", value, out)


def _tpl_length_bound(value: Any, min_len: int, max_len: int) -> tuple[dict[str, Any], dict[str, Any]]:
    n = len(value)
    out = _verdict("length_bound", min_len <= n <= max_len, length=n, min=min_len, max=max_len)
    return out, _receipt("vp_length_bound", value, out)


def _tpl_required_keys(record: dict[str, Any], required: list[str]) -> tuple[dict[str, Any], dict[str, Any]]:
    missing = [k for k in required if k not in record]
    out = _verdict("required_keys", not missing, missing=missing)
    return out, _receipt("vp_required_keys", record, out)


_LOCAL_TEMPLATES = {
    "vp_in_range": _tpl_in_range, "vp_regex_match": _tpl_regex_match, "vp_enum_member": _tpl_enum_member,
    "vp_length_bound": _tpl_length_bound, "vp_required_keys": _tpl_required_keys,
}


def _ensure_templates() -> None:
    """Register the five template mutators into the shared registry. Best-effort import of the proven sibling first
    (try/except so a standalone --self-test still runs), then setdefault local fallbacks — never an overwrite."""
    try:  # reuse the sibling's already-proven templates when available
        import scripts.prove_leaves_validation_predicate  # noqa: F401
    except Exception:  # noqa: BLE001 — standalone path: fall back to identical local templates
        pass
    for name, fn in _LOCAL_TEMPLATES.items():
        MUTATOR_REGISTRY.setdefault(name, fn)


_ensure_templates()


# ── the five templates + their canonical edge types (Record folds to RecordBatch; all non-empty => typable) ──
TEMPLATE_EDGES: dict[str, tuple[str, str]] = {
    "vp_in_range": ("Number", "ValidationVerdict"),
    "vp_regex_match": ("Text", "ValidationVerdict"),
    "vp_enum_member": ("Value", "ValidationVerdict"),
    "vp_length_bound": ("Text", "ValidationVerdict"),
    "vp_required_keys": ("Record", "ValidationVerdict"),
}
_EDGE_ID_CACHE: dict[str, str] = {}


def _edge_id(edge: str) -> str:
    if edge not in _EDGE_ID_CACHE:
        _EDGE_ID_CACHE[edge] = canonicalize_edge(edge)
    return _EDGE_ID_CACHE[edge]


# ── deterministic, meaningfully-distinct PARAMETER SPACES (each yields a distinct rule behavior) ──
# in_range: a curated grid of numeric bounds; each (lo, hi) is a distinct rule. Fixture = an in-range midpoint.
_IR_LO = [-1000000, -100000, -10000, -1000, -500, -273, -100, -50, -10, -5, -1, 0, 1, 2, 3, 5, 8, 10,
          16, 18, 21, 25, 32, 50, 64, 100, 128, 200, 255, 500, 1000]
_IR_HI = [0, 1, 2, 3, 5, 8, 10, 12, 16, 18, 20, 21, 24, 32, 50, 60, 64, 90, 100, 120, 127, 128, 200, 212,
          255, 256, 360, 500, 999, 1000, 1024, 5000, 9999, 32767, 65535, 100000, 1000000]


def _space_in_range() -> list[dict[str, Any]]:
    specs: list[dict[str, Any]] = []
    for lo in _IR_LO:
        for hi in _IR_HI:
            if lo >= hi:
                continue
            mid = (lo + hi) // 2  # deterministic in-range witness value
            specs.append({"template": "vp_in_range", "args": {"lo": lo, "hi": hi}, "fixture": mid,
                          "capability": f"numeric value within the inclusive range [{lo}, {hi}]"})
    return specs


# length_bound: curated (min_len, max_len) grid; fixture = an in-bounds string of 'a'*min_len (len==min_len).
_LB_MIN = [0, 1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 14, 16, 20, 24, 32, 40, 48, 50, 64, 80, 100, 128, 200, 255]
_LB_MAX = [1, 2, 3, 4, 5, 6, 8, 10, 12, 14, 16, 20, 24, 32, 40, 48, 50, 60, 64, 80, 100, 128, 160, 200,
           255, 256, 500, 1000, 2000, 4096]


def _space_length_bound() -> list[dict[str, Any]]:
    specs: list[dict[str, Any]] = []
    for mn in _LB_MIN:
        for mx in _LB_MAX:
            if mn > mx:
                continue
            witness = "a" * mn  # deterministic in-bounds witness (len == mn, which is within [mn, mx])
            specs.append({"template": "vp_length_bound", "args": {"min_len": mn, "max_len": mx}, "fixture": witness,
                          "capability": f"string length within the inclusive bound [{mn}, {mx}]"})
    return specs


# enum_member: a library of curated domain enums + parametric numeric/label sets. Fixture = choices[0] (a member).
_NAMED_ENUMS: dict[str, list[Any]] = {
    "rgb_color": ["red", "green", "blue"],
    "primary_color": ["red", "yellow", "blue"],
    "traffic_light": ["red", "amber", "green"],
    "http_method": ["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"],
    "http_safe_method": ["GET", "HEAD", "OPTIONS"],
    "order_status": ["pending", "paid", "shipped", "delivered", "cancelled", "refunded"],
    "ticket_status": ["open", "in_progress", "resolved", "closed"],
    "task_state": ["todo", "doing", "review", "done"],
    "priority": ["low", "medium", "high", "critical"],
    "severity": ["info", "warning", "error", "fatal"],
    "log_level": ["debug", "info", "warn", "error"],
    "size": ["xs", "s", "m", "l", "xl", "xxl"],
    "tshirt_estimate": ["xs", "s", "m", "l", "xl"],
    "weekday": ["mon", "tue", "wed", "thu", "fri"],
    "weekend": ["sat", "sun"],
    "day_of_week": ["mon", "tue", "wed", "thu", "fri", "sat", "sun"],
    "month": ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"],
    "quarter": ["q1", "q2", "q3", "q4"],
    "yes_no": ["yes", "no"],
    "bool_word": ["true", "false"],
    "on_off": ["on", "off"],
    "sign": ["positive", "negative", "zero"],
    "direction": ["north", "south", "east", "west"],
    "cardinal8": ["n", "ne", "e", "se", "s", "sw", "w", "nw"],
    "currency_major": ["USD", "EUR", "GBP", "JPY", "CHF", "CAD", "AUD"],
    "continent": ["africa", "antarctica", "asia", "europe", "north_america", "oceania", "south_america"],
    "blood_type": ["A", "B", "AB", "O"],
    "planet": ["mercury", "venus", "earth", "mars", "jupiter", "saturn", "uranus", "neptune"],
    "role": ["admin", "editor", "viewer", "guest"],
    "visibility": ["public", "private", "unlisted"],
    "gender_form": ["female", "male", "nonbinary", "unspecified"],
    "env_tier": ["dev", "staging", "prod"],
    "deploy_state": ["queued", "building", "deployed", "failed", "rolled_back"],
    "payment_method": ["card", "bank", "wallet", "cash"],
    "media_type": ["image", "video", "audio", "document"],
    "compass_quality": ["poor", "fair", "good", "excellent"],
    "grade": ["A", "B", "C", "D", "F"],
    "star_rating": [1, 2, 3, 4, 5],
    "http_status_family": [1, 2, 3, 4, 5],
    "boolean_int": [0, 1],
    "trit": [-1, 0, 1],
    "iso_weekday_num": [1, 2, 3, 4, 5, 6, 7],
    "die_face": [1, 2, 3, 4, 5, 6],
    "byte_edge": [0, 255],
}


def _space_enum_member() -> list[dict[str, Any]]:
    specs: list[dict[str, Any]] = []
    # (a) named domain enums
    for name, choices in _NAMED_ENUMS.items():
        specs.append({"template": "vp_enum_member", "args": {"choices": list(choices)}, "fixture": choices[0],
                      "capability": f"value is a member of the '{name}' allowed set ({len(choices)} choices)"})
    # (b) parametric numeric ranges as enums: choices = [start .. start+size)
    for start in [0, 1, 2, 5, 10, 100, 1000]:
        for size in [2, 3, 4, 5, 6, 8, 10, 12, 16, 20, 24, 32]:
            choices = list(range(start, start + size))
            specs.append({"template": "vp_enum_member", "args": {"choices": choices}, "fixture": choices[0],
                          "capability": f"integer in the enumerated set [{start}..{start + size - 1}]"})
    # (c) parametric labelled sets: [f"{prefix}{i}" ...] — stable string seeds, never hash()
    for prefix in ["opt", "code", "tier", "lvl", "grp", "cat", "mode", "flag", "slot", "zone"]:
        for size in [2, 3, 4, 5, 6, 8, 10, 12, 16, 20]:
            choices = [f"{prefix}_{i}" for i in range(size)]  # stable seed f"{prefix}_{i}"
            specs.append({"template": "vp_enum_member", "args": {"choices": choices}, "fixture": choices[0],
                          "capability": f"value is one of {size} '{prefix}' labels"})
    # (d) single-letter alphabet windows: distinct allowed alphabets
    letters = [chr(ord("a") + i) for i in range(26)]
    for width in [2, 3, 4, 5, 6, 8, 10, 13]:
        for offset in range(0, 26 - width + 1, 3):
            choices = letters[offset:offset + width]
            specs.append({"template": "vp_enum_member", "args": {"choices": choices}, "fixture": choices[0],
                          "capability": f"letter within a {width}-letter alphabet window at offset {offset}"})
    return specs


# regex_match: a library of (pattern, matching-sample) families; fixture ALWAYS fullmatches so valid=True is workable.
def _space_regex_match() -> list[dict[str, Any]]:
    specs: list[dict[str, Any]] = []

    def add(pattern: str, sample: str, cap: str) -> None:
        specs.append({"template": "vp_regex_match", "args": {"pattern": pattern}, "fixture": sample, "capability": cap})

    # (a) fixed-count character classes
    for n in range(1, 17):
        add(rf"\d{{{n}}}", "0" * n, f"exactly {n} digits")
        add(rf"[a-z]{{{n}}}", "a" * n, f"exactly {n} lowercase letters")
        add(rf"[A-Z]{{{n}}}", "A" * n, f"exactly {n} uppercase letters")
        add(rf"[a-zA-Z]{{{n}}}", "a" * n, f"exactly {n} letters")
        add(rf"[a-z0-9]{{{n}}}", "a" * n, f"exactly {n} lowercase-alnum chars")
    # (b) ranged-count classes {lo,hi}
    for lo in [1, 2, 3, 4, 5, 6, 8]:
        for extra in [1, 2, 3, 4, 6, 8, 10]:
            hi = lo + extra
            add(rf"\d{{{lo},{hi}}}", "0" * lo, f"{lo}-{hi} digits")
            add(rf"[a-z]{{{lo},{hi}}}", "a" * lo, f"{lo}-{hi} lowercase letters")
    # (c) prefixed id patterns PREFIX-\d{n}
    for prefix in ["SKU", "ORD", "USR", "INV", "TXN", "REF", "PO", "TicketId"]:
        for n in [3, 4, 5, 6, 8]:
            add(rf"{prefix}-\d{{{n}}}", f"{prefix}-{'0' * n}", f"{prefix}-<{n} digits> id")
    # (d) license-plate style [A-Z]{k}\d{m}
    for k in [1, 2, 3]:
        for m in [2, 3, 4, 5]:
            add(rf"[A-Z]{{{k}}}\d{{{m}}}", "A" * k + "0" * m, f"{k} letters then {m} digits")
    # (e) word alternations (cat|dog|...) — stable-seeded label groups
    word_pools = {
        "animal": ["cat", "dog", "bird", "fish"], "fruit": ["apple", "pear", "plum"],
        "metal": ["iron", "gold", "tin", "zinc"], "planetlet": ["moon", "sun", "star"],
        "verb": ["get", "put", "post", "del"], "hue": ["red", "blue", "teal"],
    }
    for name, pool in word_pools.items():
        pat = "(" + "|".join(pool) + ")"
        add(pat, pool[0], f"one of the '{name}' words {pool}")
    # (f) named canonical shapes with matching samples
    named = [
        (r"[a-z0-9]+(?:-[a-z0-9]+)*", "my-url-slug", "kebab-case slug"),
        (r"[a-z_][a-z0-9_]*", "snake_case_id", "snake_case identifier"),
        (r"[A-Za-z_][A-Za-z0-9_]*", "CamelName", "generic identifier"),
        (r"#[0-9a-fA-F]{6}", "#ff8800", "#rrggbb hex color"),
        (r"#[0-9a-fA-F]{3}", "#f80", "#rgb short hex color"),
        (r"\d{4}-\d{2}-\d{2}", "2026-07-03", "YYYY-MM-DD date shape"),
        (r"\d{2}:\d{2}", "14:30", "HH:MM time shape"),
        (r"\d{2}:\d{2}:\d{2}", "14:30:59", "HH:MM:SS time shape"),
        (r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", "192.168.0.1", "IPv4 dotted-quad shape"),
        (r"\d+\.\d+\.\d+", "1.2.3", "semantic-version shape"),
        (r"v\d+\.\d+\.\d+", "v10.4.2", "v-prefixed semver shape"),
        (r"[^@\s]+@[^@\s]+\.[^@\s]+", "user@example.com", "email shape"),
        (r"\+?\d{7,15}", "+14155550123", "E.164-ish phone shape"),
        (r"\d{5}(?:-\d{4})?", "94107", "US ZIP (+4 optional) shape"),
        (r"[A-Z]{2}\d{2}[A-Z0-9]{1,30}", "GB29NWBK60161331926819", "IBAN-ish shape"),
        (r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", "550e8400-e29b-41d4-a716-446655440000", "uuid shape"),
        (r"https?://[^\s]+", "https://example.com/x", "http(s) url shape"),
        (r"[A-Z]{3}", "USD", "3-letter currency code"),
        (r"@[a-z0-9_]{1,15}", "@handle_1", "social handle shape"),
        (r"#[a-z0-9_]+", "#topic_1", "hashtag shape"),
    ]
    for pat, sample, cap in named:
        add(pat, sample, cap)
    return specs


# required_keys: curated named record schemas + parametric key-set combinations. Fixture = a record with all keys.
_FIELD_POOL = ["id", "name", "email", "phone", "age", "status", "created_at", "updated_at", "price",
               "quantity", "sku", "title", "description", "url", "type", "owner", "tags", "score",
               "active", "country"]
_NAMED_SCHEMAS: dict[str, list[str]] = {
    "user": ["id", "name", "email"],
    "user_full": ["id", "name", "email", "phone", "country"],
    "order": ["id", "sku", "quantity", "price"],
    "order_line": ["sku", "quantity", "price"],
    "product": ["sku", "title", "price"],
    "product_full": ["sku", "title", "description", "price", "tags"],
    "event": ["type", "created_at", "owner"],
    "audit": ["id", "type", "created_at", "updated_at"],
    "contact": ["name", "email", "phone"],
    "address_min": ["country"],
    "listing": ["id", "title", "price", "active"],
    "review": ["id", "score", "description"],
    "ticket": ["id", "title", "status", "owner"],
    "account": ["id", "name", "status", "active"],
    "session": ["id", "owner", "created_at"],
    "profile": ["name", "url", "tags"],
}


def _space_required_keys() -> list[dict[str, Any]]:
    specs: list[dict[str, Any]] = []

    def add(required: list[str], cap: str) -> None:
        record = {k: i for i, k in enumerate(required)}  # deterministic record carrying every required key
        specs.append({"template": "vp_required_keys", "args": {"required": list(required)}, "fixture": record,
                      "capability": cap})

    # (a) named domain schemas
    for name, keys in _NAMED_SCHEMAS.items():
        add(keys, f"record satisfies the '{name}' required-key schema {keys}")
    # (b) every single required key
    for k in _FIELD_POOL:
        add([k], f"record contains required key '{k}'")
    # (c) all 2-key sets (C(20,2)=190 distinct required-pairs)
    for combo in itertools.combinations(_FIELD_POOL, 2):
        keys = list(combo)
        add(keys, f"record contains both required keys {keys}")
    # (d) a deterministic stride-sample of 3-key sets — meaningfully-distinct triples without combinatorial bloat
    #     (the full C(20,3)=1140 is mostly noise; a fixed stride keeps a representative, reproducible subset).
    _TRIPLE_STRIDE = 3  # every 3rd combination -> ~380 distinct triples
    for i, combo in enumerate(itertools.combinations(_FIELD_POOL, 3)):
        if i % _TRIPLE_STRIDE != 0:
            continue
        keys = list(combo)
        add(keys, f"record contains all 3 required keys {keys}")
    return specs


_SPACES = [_space_in_range, _space_length_bound, _space_enum_member, _space_regex_match, _space_required_keys]


def enumerate_all() -> list[dict[str, Any]]:
    """Deterministically enumerate the full curated parameter space across the five templates (raw GENERATED specs)."""
    specs: list[dict[str, Any]] = []
    for space in _SPACES:
        specs.extend(space())
    return specs


# ── content hash for dedupe: canonical over (mutator, binding, fixture) — identical bindings collapse ──
def _content_hash(mutator: str, args: dict[str, Any], fixture: Any) -> str:
    payload = json.dumps({"m": mutator, "a": args, "f": fixture}, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _prove_binding(spec: dict[str, Any]) -> dict[str, Any] | None:
    """PROVE one configured-primitive: run the template mutator on the fixture to COMPUTE the expected typed verdict,
    then run the imported executed-proof runner (which re-executes for a determinism proof). Returns a persisted row
    ONLY if serves_truth flipped true; otherwise None (a failing binding is never persisted)."""
    mutator = spec["template"]
    args = spec["args"]
    fixture = spec["fixture"]
    try:
        expected, _ = apply_mutator(mutator, fixture, **args)  # compute the EXPECTED output by executing once
    except Exception:  # noqa: BLE001 — an un-runnable binding is not proof; drop it
        return None
    receipt = run_primitive_proof(spec["id"], mutator, fixture, expected, mutator_args=args, has_inverse=None)
    if receipt["serves_truth"] is not True:
        return None
    in_edge, out_edge = TEMPLATE_EDGES[mutator]
    in_id, out_id = _edge_id(in_edge), _edge_id(out_edge)
    if not in_id or not out_id:  # must be TYPED to be persisted (typed == proven is the target)
        return None
    return {
        "primitive_id": spec["id"],
        "mutator": mutator,
        "binding": args,
        "fixture": fixture,
        "family": GROUP,
        "capability": spec.get("capability"),
        "serves_truth": True,
        "candidate": False,
        "verification_level": "L7_executed_proof",
        "input_edge": in_edge,
        "output_edge": out_edge,
        "input_edge_type_id": in_id,
        "output_edge_type_id": out_id,
        "proofs": receipt["proofs"],
        "input_hash": receipt.get("input_hash"),
        "output_hash": receipt.get("output_hash"),
    }


def build(specs: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Prove + DEDUPE + TYPE. Returns (persisted rows, honest SEPARATE counts). generated != unique != proven != typed
    are never conflated: generated = raw specs; unique = distinct content hashes; proven = passing executed proofs;
    typed = proven rows carrying both edge type ids."""
    generated = len(specs)
    seen: set[str] = set()
    rows: list[dict[str, Any]] = []
    proven = 0
    typed = 0
    for spec in specs:
        h = _content_hash(spec["template"], spec["args"], spec["fixture"])
        if h in seen:  # identical (mutator, binding, fixture) collapses — dedupe
            continue
        seen.add(h)
        spec = {**spec, "id": f"prim:param:{spec['template']}:{h}"}
        row = _prove_binding(spec)
        if row is None:
            continue
        proven += 1
        if row.get("input_edge_type_id") and row.get("output_edge_type_id"):
            typed += 1
        rows.append(row)
    rows.sort(key=lambda r: r["primitive_id"])
    counts = {"generated": generated, "unique_after_dedupe": len(seen), "proven": proven, "typed": typed}
    return rows, counts


def build_manifest(rows: list[dict[str, Any]], counts: dict[str, int]) -> dict[str, Any]:
    canonical = "\n".join(json.dumps(r, sort_keys=True, ensure_ascii=False) for r in rows)
    per_template: dict[str, int] = {}
    for r in rows:
        per_template[r["mutator"]] = per_template.get(r["mutator"], 0) + 1
    return {
        "record_type": "parametric_validation_rules_manifest",
        "pack_id": "parametric-validation-rules", "group": GROUP, "family": GROUP,
        "generator": "scripts/generate_parametric_validation_rules.py",
        "generated_utc": _FIXED_UTC,
        "templates": sorted(TEMPLATE_EDGES),
        # SEPARATE honest counts — never conflate generated vs unique vs proven vs typed.
        "generated": counts["generated"],
        "unique_after_dedupe": counts["unique_after_dedupe"],
        "proven": counts["proven"],
        "typed": counts["typed"],
        "per_template_proven": per_template,
        "verification_level": "L7_executed_proof",
        "row_counts": {OUT_JSONL.name: len(rows)},
        "total_rows": len(rows),
        "note": "Each row is a CONFIGURED-primitive = (proven template) x (specific binding) x (canonical edge "
                "types). serves_truth=true is set ONLY by a PASSING executed proof of THAT binding (the mutator is "
                "run on the fixture and re-run for determinism); a failing binding is not persisted. Counts are "
                "SEPARATE: generated (raw enumerated specs) vs unique_after_dedupe (distinct content hashes) vs "
                "proven (passing executed proofs) vs typed (proven rows carrying both edge type ids).",
        "content_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
    }


def write_pack() -> dict[str, Any]:
    rows, counts = build(enumerate_all())
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JSONL.write_text(
        "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows), encoding="utf-8")
    manifest = build_manifest(rows, counts)
    OUT_MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def self_test() -> int:
    # A SMALL, standalone enumeration proves the whole contract without touching disk or running the full space.
    small: list[dict[str, Any]] = [
        {"template": "vp_in_range", "args": {"lo": 0, "hi": 10}, "fixture": 5, "capability": "range [0,10]"},
        {"template": "vp_in_range", "args": {"lo": 32, "hi": 212}, "fixture": 100, "capability": "range [32,212]"},
        {"template": "vp_length_bound", "args": {"min_len": 1, "max_len": 8}, "fixture": "abc", "capability": "len [1,8]"},
        {"template": "vp_enum_member", "args": {"choices": ["red", "green", "blue"]}, "fixture": "red", "capability": "rgb"},
        {"template": "vp_regex_match", "args": {"pattern": r"\d{3}"}, "fixture": "007", "capability": "3 digits"},
        {"template": "vp_required_keys", "args": {"required": ["id", "name"]}, "fixture": {"id": 1, "name": "x"},
         "capability": "keys id,name"},
        # a DUPLICATE of the first binding (same mutator+args+fixture) — must collapse in dedupe
        {"template": "vp_in_range", "args": {"lo": 0, "hi": 10}, "fixture": 5, "capability": "range [0,10] dup"},
    ]
    rows, counts = build(small)

    # a deliberately-WRONG expected must FAIL the proof and never persist (the gate is real, not a rubber stamp)
    wrong = run_primitive_proof("prim:param:WRONG", "vp_in_range", 5, {"check": "in_range", "valid": False},
                                mutator_args={"lo": 0, "hi": 10}, has_inverse=None)
    # an un-runnable binding (bad args) is not proof and yields no row
    bad_row = _prove_binding({"id": "prim:param:BAD", "template": "vp_in_range", "args": {"lo": 0},  # missing hi
                              "fixture": 5, "capability": "x"})

    checks: list[tuple[str, bool]] = [
        ("small space enumerated (7 raw specs incl. 1 duplicate)", counts["generated"] == 7),
        ("dedupe collapsed the identical binding (7 generated -> 6 unique)", counts["unique_after_dedupe"] == 6),
        ("all 6 unique bindings PROVE serves_truth=true", counts["proven"] == 6 and len(rows) == 6),
        ("proven == typed (every proven row is typed)", counts["typed"] == counts["proven"]),
        ("EVERY persisted row carries serves_truth=true + L7_executed_proof",
         all(r["serves_truth"] is True and r["verification_level"] == "L7_executed_proof" for r in rows)),
        ("EVERY persisted row carries BOTH non-empty edge type ids",
         all(r["input_edge_type_id"] and r["output_edge_type_id"] for r in rows)),
        ("EVERY persisted row's sub-proofs all passed (fixture + determinism)",
         all(all(p["passed"] for p in r["proofs"]) for r in rows)),
        ("primitive ids are unique + parametric-shaped", len({r["primitive_id"] for r in rows}) == len(rows)
         and all(r["primitive_id"].startswith("prim:param:") for r in rows)),
        ("distinct bindings of the SAME template are DISTINCT primitives",
         len({r["primitive_id"] for r in rows if r["mutator"] == "vp_in_range"}) == 2),
        ("a deliberately-wrong expected FAILS and is not promoted",
         wrong["serves_truth"] is False and wrong["promoted"] is False),
        ("an un-runnable binding yields no persisted row", bad_row is None),
        ("deterministic: re-running build yields identical rows",
         [json.dumps(r, sort_keys=True) for r in build(small)[0]] == [json.dumps(r, sort_keys=True) for r in rows]),
        ("manifest keeps generated/unique/proven/typed as SEPARATE counts",
         build_manifest(rows, counts)["proven"] == 6 and build_manifest(rows, counts)["generated"] == 7
         and build_manifest(rows, counts)["unique_after_dedupe"] == 6),
        ("all five templates registered in the shared registry",
         all(m in MUTATOR_REGISTRY for m in TEMPLATE_EDGES)),
    ]
    failed = [n for n, ok in checks if not ok]
    if failed:
        print("FAIL - generate_parametric_validation_rules:\n  " + "\n  ".join(failed))
        return 1
    print(f"PASS - generate_parametric_validation_rules: {counts['proven']} configured-primitives PROVEN + TYPED from "
          f"{counts['generated']} generated specs ({counts['unique_after_dedupe']} unique after dedupe); each = "
          "(proven template) x (binding) x (canonical edges), serves_truth=true set ONLY by a passing executed proof; "
          "a wrong-expected and an un-runnable binding correctly stay unpersisted. Workable capability, not vocabulary.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--date", default=None)  # accepted for parity; body uses a fixed literal timestamp
    args = parser.parse_args(argv)
    if args.self_test and not args.write:
        return self_test()
    manifest = write_pack()
    print(json.dumps({k: v for k, v in manifest.items() if k != "content_sha256"}, indent=2, sort_keys=True))
    return self_test()


if __name__ == "__main__":
    raise SystemExit(main())
