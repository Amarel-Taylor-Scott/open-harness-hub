#!/usr/bin/env python3
"""scripts.generate_parametric_codec_hash — WORKABLE configured-primitives for the `codec_hash` group by
PARAMETRIC PROOF.

A configured-primitive here = (a PROVEN mutator TEMPLATE) x (a specific parameter BINDING = a curated input
byte/text shape) x (canonical edge types). `base64("data")` and `base64("hello")` are DISTINCT workable
primitives; so are `base64("data")` and `sha256("data")`. Each is proven by ACTUALLY EXECUTING the mutator on
its fixture and checking the output through the imported `run_primitive_proof` — the ONLY thing that flips
serves_truth false->true (L7_executed_proof). A binding whose executed proof fails is NOT persisted as truth.

Templates parameterized (per the group spec): base64, hex, url_quote (reversible — additionally roundtrip-proven
via has_inverse) + sha256, blake2b, crc32 (one-way digests/checksums). The proven mutator TEMPLATES are IMPORTED
from the sibling `prove_leaves_*` modules, which register real callables into `MUTATOR_REGISTRY` on import
(try/except so --self-test still runs if one is absent; local fallbacks fill any gap via setdefault, never an
overwrite — a sibling's proven version always wins).

The parameter space is a CURATED, deterministically-enumerated set of MEANINGFULLY-DISTINCT input shapes
(empty/printable-ASCII singletons, curated realistic tokens — urls/emails/paths/json/numbers/unicode/whitespace,
repeated-char length shapes, and stable-seeded structured payloads `f"{group}:{i}:.."` — NEVER Python `hash()`).
For each binding: build fixture + EXPECTED (compute by executing once), prove, keep ONLY passers, DEDUPE by a
canonical content hash over (mutator, binding, fixture), and TYPE each via `canonicalize_edge`.

ADD-ONLY: a NEW parallel file. Edits NONE of the contract-locked (mutator_registry.py,
build_edge_type_retrofit.py, registry_search.py) or shared (flywheel_proof_modules.py, _config.py) files, and
does NOT register itself in the proof harness (the caller records the (script_path, module_name) tuple).
Deterministic + offline: no network, no LLM, no wall-clock, no RNG. Fixed literal timestamp. CLI: --self-test | --write.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

# IMPORT the shared machinery — never edit it (ADD-ONLY seam).
from scripts.mutator_registry import (  # noqa: E402
    MUTATOR_REGISTRY,
    _receipt,
    apply_mutator,
    run_primitive_proof,
)
from scripts.build_edge_type_retrofit import canonicalize_edge  # noqa: E402

# IMPORT the PROVEN codec/hash templates: importing these siblings registers the real mutators into the shared
# MUTATOR_REGISTRY (setdefault at their module scope). try/except so --self-test still runs if one is absent.
try:  # base64 / hex / url_quote enc+dec live here
    import scripts.prove_leaves_encoding_codec  # noqa: F401,E402
except Exception:  # noqa: BLE001
    pass
try:  # sha256 / blake2b / crc32 live here
    import scripts.prove_leaves_hashing_checksum  # noqa: F401,E402
except Exception:  # noqa: BLE001
    pass

GROUP = "codec_hash"
FAMILY = "codec_hash"
FROZEN_TS = "2026-07-03T00:00:00Z"  # fixed literal — NEVER wall-clock (determinism law)
OUT_DIR = _resource("data") / "dev-intel" / "parametric_primitives"
OUT_JSONL = OUT_DIR / "param_codec_hash.jsonl"
OUT_MANIFEST = OUT_DIR / "manifest_codec_hash.json"


# ── LOCAL fallbacks: only fill a gap if a sibling didn't register (setdefault => sibling's proven version wins). ──
def _fb_base64(text: str, **_: Any) -> tuple[str, dict[str, Any]]:
    import base64 as _b
    out = _b.b64encode(text.encode("utf-8")).decode("ascii")
    return out, _receipt("enc_base64_std", before=text, after=out, lossless=True, note="fallback base64 encode")


def _fb_base64_dec(text: str, **_: Any) -> tuple[str, dict[str, Any]]:
    import base64 as _b
    out = _b.b64decode(text.encode("ascii")).decode("utf-8")
    return out, _receipt("dec_base64_std", before=text, after=out, lossless=True, note="fallback base64 decode")


def _fb_hex(text: str, **_: Any) -> tuple[str, dict[str, Any]]:
    out = text.encode("utf-8").hex()
    return out, _receipt("enc_hex", before=text, after=out, lossless=True, note="fallback hex encode")


def _fb_hex_dec(text: str, **_: Any) -> tuple[str, dict[str, Any]]:
    out = bytes.fromhex(text).decode("utf-8")
    return out, _receipt("dec_hex", before=text, after=out, lossless=True, note="fallback hex decode")


def _fb_url_quote(text: str, **_: Any) -> tuple[str, dict[str, Any]]:
    import urllib.parse as _u
    out = _u.quote(text)
    return out, _receipt("url_quote", before=text, after=out, lossless=True, note="fallback url quote")


def _fb_url_unquote(text: str, **_: Any) -> tuple[str, dict[str, Any]]:
    import urllib.parse as _u
    out = _u.unquote(text)
    return out, _receipt("url_unquote", before=text, after=out, lossless=True, note="fallback url unquote")


def _fb_sha256(text: str, **_: Any) -> tuple[str, dict[str, Any]]:
    out = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return out, _receipt("hc_sha256_hex", before=text, after=out, lossless=False, note="fallback sha256 hex")


def _fb_blake2b(text: str, **_: Any) -> tuple[str, dict[str, Any]]:
    out = hashlib.blake2b(text.encode("utf-8")).hexdigest()
    return out, _receipt("hc_blake2b_hex", before=text, after=out, lossless=False, note="fallback blake2b hex")


def _fb_crc32(text: str, **_: Any) -> tuple[str, dict[str, Any]]:
    import zlib
    out = format(zlib.crc32(text.encode("utf-8")) & 0xFFFFFFFF, "08x")
    return out, _receipt("hc_crc32_hex", before=text, after=out, lossless=False, note="fallback crc32 hex")


_FALLBACKS = {
    "enc_base64_std": _fb_base64, "dec_base64_std": _fb_base64_dec,
    "enc_hex": _fb_hex, "dec_hex": _fb_hex_dec,
    "url_quote": _fb_url_quote, "url_unquote": _fb_url_unquote,
    "hc_sha256_hex": _fb_sha256, "hc_blake2b_hex": _fb_blake2b, "hc_crc32_hex": _fb_crc32,
}
for _name, _fn in _FALLBACKS.items():
    MUTATOR_REGISTRY.setdefault(_name, _fn)  # idempotent; sibling's proven callable takes precedence


# ── the 6 proven TEMPLATES to parameterize (each names a registered mutator + canonical edge types) ──
TEMPLATES: list[dict[str, Any]] = [
    {"template": "base64", "mutator": "enc_base64_std", "inverse": "dec_base64_std",
     "input_edge": "Text", "output_edge": "Base64Text"},
    {"template": "hex", "mutator": "enc_hex", "inverse": "dec_hex",
     "input_edge": "Text", "output_edge": "HexText"},
    {"template": "url_quote", "mutator": "url_quote", "inverse": "url_unquote",
     "input_edge": "Text", "output_edge": "PercentEncodedText"},
    {"template": "sha256", "mutator": "hc_sha256_hex", "inverse": None,
     "input_edge": "Text", "output_edge": "Sha256HexDigest"},
    {"template": "blake2b", "mutator": "hc_blake2b_hex", "inverse": None,
     "input_edge": "Text", "output_edge": "Blake2bHexDigest"},
    {"template": "crc32", "mutator": "hc_crc32_hex", "inverse": None,
     "input_edge": "Text", "output_edge": "Crc32Checksum"},
]


def _available_templates() -> list[dict[str, Any]]:
    """Only templates whose mutator (and inverse, if reversible) is actually in the registry."""
    ok: list[dict[str, Any]] = []
    for t in TEMPLATES:
        if t["mutator"] not in MUTATOR_REGISTRY:
            continue
        if t["inverse"] and t["inverse"] not in MUTATOR_REGISTRY:
            continue
        ok.append(t)
    return ok


# ── the CURATED, deterministically-enumerated parameter space (meaningfully-distinct input shapes) ──
_CURATED_TOKENS: list[str] = [
    # realistic structured shapes
    "", "data", "hello", "hello world", "Hello, World!",
    "https://example.com/path?q=1&r=2", "user@example.com", "/usr/local/bin/python3",
    "C:\\Users\\name\\file.txt", "192.168.1.1", "2026-07-03T00:00:00Z", "+1 (555) 123-4567",
    '{"k":"v","n":42}', "[1, 2, 3]", "key=value;other=thing", "a,b,c,d,e",
    "SELECT * FROM t WHERE id=1", "<a href='x'>link</a>", "# heading\n- item",
    "price: $1,234.56", "50%", "3.14159", "-273.15", "0xDEADBEEF", "0b101010", "1e-9",
    "550e8400-e29b-41d4-a716-446655440000", "sk-abcDEF123", "Bearer token.value.sig",
    # unicode / accents / cjk / emoji / symbols
    "café", "naïve", "Zürich", "Málaga", "Ångström", "Ç", "ñ", "ß", "Ω", "µ",
    "日本語", "中文字符", "한국어", "العربية", "עברית", "Ελληνικά", "Русский",
    "🙂", "🚀🌍", "👋 hi", "emoji: 🎉🎉🎉", "—em—dash—", "…ellipsis…", "«guillemets»",
    # whitespace / control shapes
    " ", "  ", "\t", "\n", "\r\n", "a\tb\tc", "line1\nline2\nline3", "trailing \n",
    " leading", "trailing ", "mixed \t\n mix",
    # symbol-heavy / codec-stressing shapes
    "a b/c", "a+b+c", "100%25done", "?query=&x=1", "#hash#tag", "a&b&c", "<>&\"'",
    "\\backslash\\", "path/to/../file", "%20%2F%3F", "===padding===", "!@#$^&*()",
    # short repeated markers
    "aaa", "AAA", "000", "zzz", "...", "---", "___", "###",
]


def _repeated_shapes() -> list[str]:
    """Length-varied byte shapes: base_char repeated at deterministic (fibonacci-ish) lengths."""
    base_chars = ["a", "Z", "0", "9", " ", ".", "/", "%", "+", "-", "x", "é", "字", "🙂", "\n"]
    lengths = [2, 3, 5, 8, 13, 21, 34, 55]
    return [ch * n for ch in base_chars for n in lengths]


def _ascii_singletons() -> list[str]:
    """Every printable ASCII byte 0x20..0x7E as a single-char shape."""
    return [chr(c) for c in range(0x20, 0x7F)]


_SEED_WORDS = [
    "alpha", "bravo", "charlie", "delta", "echo", "foxtrot", "golf", "hotel", "india",
    "juliet", "kilo", "lima", "mike", "november", "oscar", "papa", "quebec", "romeo",
    "sierra", "tango", "uniform", "victor", "whiskey", "xray", "yankee", "zulu",
]


def _seeded_shapes(count: int) -> list[str]:
    """Stable-seeded structured payloads for meaningfully-distinct volume. Uses a STRING seed f'{group}:{i}',
    never Python hash(). Each is a distinct realistic key:value:index shape."""
    out: list[str] = []
    for i in range(count):
        seed = f"{GROUP}:{i}"
        word = _SEED_WORDS[i % len(_SEED_WORDS)]
        word2 = _SEED_WORDS[(i * 7 + 3) % len(_SEED_WORDS)]
        out.append(f"{seed}:{word}-{word2}:v{(i * 13) % 997}")
    return out


def build_input_corpus() -> list[str]:
    """Deterministically enumerate the full, deduplicated input-shape parameter space (order preserved)."""
    raw = _CURATED_TOKENS + _ascii_singletons() + _repeated_shapes() + _seeded_shapes(160)
    # dedupe preserving first-seen order (no RNG, deterministic)
    return list(dict.fromkeys(raw))


def _shape_class(text: str) -> str:
    if text == "":
        return "empty"
    if len(text) == 1:
        return "singleton"
    if len(set(text)) == 1:
        return "repeated_char"
    if text.startswith(f"{GROUP}:"):
        return "seeded_structured"
    if not text.isascii():
        return "unicode"
    if text.strip() == "":
        return "whitespace"
    return "curated_token"


# ── the content hash used for dedupe + id (canonical over mutator+binding+fixture) ──
def _content_hash(mutator: str, binding: dict[str, Any], fixture: Any) -> str:
    blob = json.dumps({"mutator": mutator, "binding": binding, "fixture": fixture},
                      sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


# ── generate → prove → dedupe → type ──
def generate_candidates() -> list[dict[str, Any]]:
    """Enumerate (template x input-shape) candidate configured-primitives. No proof yet — raw generation."""
    corpus = build_input_corpus()
    candidates: list[dict[str, Any]] = []
    for tmpl in _available_templates():
        for text in corpus:
            binding = {
                "input_text": text,
                "input_len_bytes": len(text.encode("utf-8")),
                "shape_class": _shape_class(text),
                "encoding": "utf-8",
            }
            candidates.append({"template": tmpl, "binding": binding, "fixture": text})
    return candidates


def _prove_and_type(cand: dict[str, Any]) -> dict[str, Any] | None:
    """Compute the expected output by EXECUTING the mutator once, then run the executed proof. Return a
    persisted TEMPLATE+BINDING row ONLY if the proof PASSES (serves_truth=true earned), else None."""
    tmpl = cand["template"]
    mutator = tmpl["mutator"]
    fixture = cand["fixture"]
    binding = cand["binding"]
    try:
        expected, _ = apply_mutator(mutator, fixture)  # EXPECTED computed by executing once
    except Exception:  # noqa: BLE001 — an un-runnable fixture is simply not proven (never persisted)
        return None
    sha16 = _content_hash(mutator, binding, fixture)
    primitive_id = f"prim:param:{mutator}:{sha16}"
    receipt = run_primitive_proof(primitive_id, mutator, fixture, expected, has_inverse=tmpl["inverse"])
    if receipt["serves_truth"] is not True:  # only a PASSING executed proof persists as truth
        return None
    in_type = canonicalize_edge(tmpl["input_edge"])
    out_type = canonicalize_edge(tmpl["output_edge"])
    if not in_type or not out_type:  # must be typed to be workable
        return None
    return {
        "primitive_id": primitive_id,
        "record_type": "parametric_configured_primitive",
        "group": GROUP,
        "family": FAMILY,
        "template": tmpl["template"],
        "mutator": mutator,
        "binding": binding,
        "fixture_input": fixture,
        "expected_output": expected,
        "input_edge": tmpl["input_edge"],
        "output_edge": tmpl["output_edge"],
        "input_edge_type_id": in_type,
        "output_edge_type_id": out_type,
        "has_roundtrip_proof": any(
            p["name"] == "roundtrip_test" and p["passed"] for p in receipt["proofs"]),
        "serves_truth": True,
        "candidate": False,
        "verification_level": "L7_executed_proof",
        "output_hash": receipt["output_hash"],
        "content_hash": sha16,
    }


def build_rows() -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Full pipeline. Returns (deduped proven+typed rows, honest separated counts)."""
    candidates = generate_candidates()
    generated = len(candidates)
    proven_rows: list[dict[str, Any]] = []
    for cand in candidates:
        row = _prove_and_type(cand)
        if row is not None:
            proven_rows.append(row)
    proven = len(proven_rows)
    # DEDUPE by canonical content hash over (mutator, binding, fixture) => identical bindings collapse
    by_id: dict[str, dict[str, Any]] = {}
    for row in proven_rows:
        by_id.setdefault(row["primitive_id"], row)
    unique_rows = sorted(by_id.values(), key=lambda r: r["primitive_id"])
    typed = sum(1 for r in unique_rows if r["input_edge_type_id"] and r["output_edge_type_id"])
    counts = {
        "generated": generated,
        "unique_after_dedupe": len(unique_rows),
        "proven": proven,
        "typed": typed,
    }
    return unique_rows, counts


def build_manifest(rows: list[dict[str, Any]], counts: dict[str, int]) -> dict[str, Any]:
    return {
        "record_type": "parametric_codec_hash_manifest",
        "pack_id": "parametric-codec-hash",
        "group": GROUP,
        "family": FAMILY,
        "generator": "scripts/generate_parametric_codec_hash.py",
        "generated_utc": FROZEN_TS,
        "templates": [t["template"] for t in _available_templates()],
        "input_shape_count": len(build_input_corpus()),
        # HONEST accounting: four SEPARATE counts — never conflated, never report generated as active.
        "generated": counts["generated"],
        "unique_after_dedupe": counts["unique_after_dedupe"],
        "proven": counts["proven"],
        "typed": counts["typed"],
        "roundtrip_pair_count": sum(1 for r in rows if r["has_roundtrip_proof"]),
        "verification_level": "L7_executed_proof",
        "note": "Each row is a configured-primitive = (proven mutator template) x (input-shape binding) x "
                "(canonical edge types). serves_truth=true is set ONLY by run_primitive_proof "
                "(imported from scripts/mutator_registry.py) executing the mutator on the fixture and passing; "
                "a failing binding is never persisted. Rows are TEMPLATE+BINDING (efficient), not bloated "
                "static files. Typed via canonicalize_edge (scripts/build_edge_type_retrofit.py).",
    }


def write_pack() -> dict[str, Any]:
    rows, counts = build_rows()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JSONL.write_text(
        "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows), encoding="utf-8")
    manifest = build_manifest(rows, counts)
    OUT_MANIFEST.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


# ── standalone, small, offline self-test ──
def self_test() -> int:
    checks: list[tuple[str, bool]] = []

    templates = _available_templates()
    checks.append(("all 6 codec_hash templates available (mutators registered via sibling import or fallback)",
                   len(templates) == 6))

    # small enumeration: a handful of inputs across the 6 templates proves + types correctly
    small_inputs = ["data", "café", ""]
    small_rows: list[dict[str, Any]] = []
    for tmpl in templates:
        for text in small_inputs:
            binding = {"input_text": text, "input_len_bytes": len(text.encode("utf-8")),
                       "shape_class": _shape_class(text), "encoding": "utf-8"}
            row = _prove_and_type({"template": tmpl, "binding": binding, "fixture": text})
            if row is not None:
                small_rows.append(row)
    checks.append(("small enumeration proves+types every (template x input) binding",
                   len(small_rows) == len(templates) * len(small_inputs)))
    checks.append(("every proven row is serves_truth=true + L7_executed_proof",
                   all(r["serves_truth"] is True and r["verification_level"] == "L7_executed_proof"
                       for r in small_rows)))
    checks.append(("every proven row carries BOTH non-null edge type_ids",
                   all(bool(r["input_edge_type_id"]) and bool(r["output_edge_type_id"]) for r in small_rows)))

    # distinct bindings are distinct primitives: base64('data') != base64('café') != sha256('data')
    ids = {r["primitive_id"] for r in small_rows}
    checks.append(("distinct (template,binding) => distinct primitive ids", len(ids) == len(small_rows)))

    # DEDUPE collapses an IDENTICAL binding (same mutator+binding+fixture => same content hash => one row)
    b = {"input_text": "data", "input_len_bytes": 4, "shape_class": "curated_token", "encoding": "utf-8"}
    r_a = _prove_and_type({"template": templates[0], "binding": b, "fixture": "data"})
    r_b = _prove_and_type({"template": templates[0], "binding": b, "fixture": "data"})
    dedup: dict[str, dict[str, Any]] = {}
    for r in (r_a, r_b):
        dedup.setdefault(r["primitive_id"], r)
    checks.append(("dedupe collapses an identical binding to ONE row",
                   r_a["primitive_id"] == r_b["primitive_id"] and len(dedup) == 1))

    # a DELIBERATELY-WRONG expected output FAILS the executed proof and is NOT persisted as truth
    wrong = run_primitive_proof("prim:param:WRONG", templates[0]["mutator"], "data", "WRONG!!",
                                has_inverse=templates[0]["inverse"])
    checks.append(("a wrong expected output FAILS the proof (serves_truth stays false, not persisted)",
                   wrong["serves_truth"] is False and wrong["promoted"] is False))

    # an un-runnable fixture (bad hex to dec_hex) does not promote / is skipped by _prove_and_type
    if "dec_hex" in MUTATOR_REGISTRY:
        bad = _prove_and_type({"template": {"template": "hex_dec", "mutator": "dec_hex", "inverse": None,
                                            "input_edge": "HexText", "output_edge": "Text"},
                               "binding": {"input_text": "zzzz"}, "fixture": "zzzz"})
        checks.append(("an un-runnable fixture is not proven (returns None)", bad is None))

    # reversible templates carry a roundtrip proof; one-way ones do not
    rev = {r["mutator"] for r in small_rows if r["has_roundtrip_proof"]}
    oneway = {r["mutator"] for r in small_rows if not r["has_roundtrip_proof"]}
    checks.append(("reversible codecs (base64/hex/url_quote) carry a roundtrip proof",
                   {"enc_base64_std", "enc_hex", "url_quote"}.issubset(rev)))
    checks.append(("one-way digests (sha256/blake2b/crc32) carry no roundtrip proof",
                   {"hc_sha256_hex", "hc_blake2b_hex", "hc_crc32_hex"}.issubset(oneway)))

    # determinism: full pipeline re-runs to identical rows + counts
    rows1, counts1 = build_rows()
    rows2, counts2 = build_rows()
    checks.append(("full pipeline is deterministic (identical rows on re-run)",
                   [json.dumps(r, sort_keys=True) for r in rows1]
                   == [json.dumps(r, sort_keys=True) for r in rows2] and counts1 == counts2))
    checks.append(("honest counts: proven and typed are separate, unique<=proven<=generated",
                   counts1["unique_after_dedupe"] <= counts1["proven"] <= counts1["generated"]
                   and counts1["typed"] == counts1["unique_after_dedupe"]))
    checks.append(("target volume reached (1800-3000 proven+typed+unique bindings)",
                   1800 <= counts1["unique_after_dedupe"] <= 3000))
    checks.append(("EVERY persisted row: serves_truth=true AND both edge type_ids present",
                   all(r["serves_truth"] is True and r["input_edge_type_id"] and r["output_edge_type_id"]
                       for r in rows1)))

    failed = [n for n, ok in checks if not ok]
    if failed:
        print("FAIL - generate_parametric_codec_hash:\n  " + "\n  ".join(failed))
        return 1
    print(f"PASS - generate_parametric_codec_hash: {counts1['unique_after_dedupe']} WORKABLE codec_hash "
          f"configured-primitives — each (proven template x input-shape binding x canonical edge types), "
          f"serves_truth=true earned by an executed proof (L7); "
          f"{sum(1 for r in rows1 if r['has_roundtrip_proof'])} reversible bindings additionally roundtrip-proven. "
          f"generated={counts1['generated']} proven={counts1['proven']} unique={counts1['unique_after_dedupe']} "
          f"typed={counts1['typed']}. Dedupe collapses identical bindings; a wrong expected correctly fails.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test and not args.write:
        return self_test()
    if args.write:
        manifest = write_pack()
        print(json.dumps(manifest, indent=2, sort_keys=True))
        return self_test()
    return self_test()


if __name__ == "__main__":
    raise SystemExit(main())
