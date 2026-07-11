#!/usr/bin/env python3
"""scripts.domain_med_more_operations — WORKABLE (proven + TYPED) deterministic SHAPE leaves for general
media/content OPERATIONS (compression headers, line diff/patch/merge, MIME detect, tokenize, mustache-lite
template render, URL parse/build/normalize, query-string codec, checksum verify, ETag compute).

ADD-ONLY parallel path (its OWN shard file). It IMPORTS the shared machinery, never edits it:
  * `run_primitive_proof` / `MUTATOR_REGISTRY` / `_receipt` from `scripts.mutator_registry` — the proof-runner
    EXECUTES each pure mutator against a synthetic fixture and flips serves_truth false->true ONLY on a PASSING
    executed proof (fixture-behavior + optional roundtrip + determinism), never a shape check;
  * `canonicalize_edge` from `scripts.build_edge_type_retrofit` — folds each leaf's logical edge labels to canonical
    type_ids so every proven leaf is also TYPED (input_edge_type_id + output_edge_type_id) and can chain.

All mutators are PURE deterministic string/byte-SHAPE transforms on SYNTHETIC fixtures. NO network, NO LLM, NO
wall-clock, NO RNG. hashlib/zlib checksums are content-deterministic (stable string seeds only).

DOMAIN LAWS honored: NO insurance primitives (any domain); NO healthcare-clinical / no insurance shapes; synthetic
/public content only (no real PII/PAN/SSN/secrets — validators operate on SHAPE with fabricated fixtures). Any
NETWORK/EFFECTFUL capability (fetch-with-ETag over HTTP, upload compressed object, write patched file to disk,
push merge result to a remote) is NEVER run through the proof runner and NEVER serves_truth — it is declared as a
GATED EFFECT candidate (candidate=true, serves_truth=false, effect, proof_obligation) in a SEPARATE section of the
shard, with SEPARATE honest counts.

CLI: --self-test | --write.

Register tuple for the shared proof suite (REPORT ONLY — this module does NOT self-register):
    ("_repos/shared-backend-components/scripts/domain_med_more_operations.py", "domain_med_more_operations")
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import difflib
import hashlib
import json
import re
import sys
import zlib
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

# IMPORT the shared machinery — never edit it (ADD-ONLY / flexible-multi-path).
from scripts.mutator_registry import (  # noqa: E402
    MUTATOR_REGISTRY,
    _receipt,
    run_primitive_proof,
)
from scripts.build_edge_type_retrofit import canonicalize_edge  # noqa: E402

DOMAIN = "med_more_operations"
_FIXED_UTC = "2026-07-03"  # fixed literal timestamp — NO wall-clock (repo law: deterministic + offline)

OUT_DIR = _resource("data") / "dev-intel" / "domain_primitives"
OUT_JSONL = OUT_DIR / "domain_med_more_operations.jsonl"
OUT_MANIFEST = OUT_DIR / "manifest_med_more_operations.json"


# ── PURE deterministic mutators, contract (payload, **kwargs) -> (output, receipt). Domain-prefixed (`mmo_`) so they
#    never collide with existing registry entries; registered via setdefault (idempotent, never overwrites). ──

# ---- gzip / zlib header SHAPE (input = lowercase hex string of the leading header bytes; fabricated) ----
def mmo_gzip_header_parse(hex_header: str, **_kw: Any) -> tuple[dict[str, int], dict[str, Any]]:
    b = bytes.fromhex(hex_header)
    if len(b) < 10:
        raise ValueError("gzip header needs >=10 bytes")
    out = {"id1": b[0], "id2": b[1], "method": b[2], "flags": b[3],
           "mtime": int.from_bytes(b[4:8], "little"), "xfl": b[8], "os": b[9]}
    return out, _receipt("mmo_gzip_header_parse", before=hex_header, after=out, lossless=False,
                         note="gzip 10-byte header hex -> {id1,id2,method,flags,mtime,xfl,os}")


def mmo_gzip_magic_validate(hex_header: str, **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    b = bytes.fromhex(hex_header)
    valid = len(b) >= 2 and b[0] == 0x1F and b[1] == 0x8B
    out = {"valid": bool(valid)}
    return out, _receipt("mmo_gzip_magic_validate", before=hex_header, after=out, lossless=False,
                         note="validate gzip magic bytes 1f 8b")


def mmo_zlib_header_parse(hex_header: str, **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    b = bytes.fromhex(hex_header)
    if len(b) < 2:
        raise ValueError("zlib header needs >=2 bytes")
    cmf, flg = b[0], b[1]
    cm, cinfo = cmf & 0x0F, cmf >> 4
    out = {"cm": cm, "cinfo": cinfo, "window_size": 1 << (cinfo + 8),
           "fcheck_ok": ((cmf << 8) | flg) % 31 == 0, "fdict": bool((flg >> 5) & 1)}
    return out, _receipt("mmo_zlib_header_parse", before=hex_header, after=out, lossless=False,
                         note="zlib 2-byte header hex -> {cm,cinfo,window_size,fcheck_ok,fdict}")


def mmo_zlib_compression_method(hex_header: str, **_kw: Any) -> tuple[int, dict[str, Any]]:
    out = bytes.fromhex(hex_header)[0] & 0x0F
    return out, _receipt("mmo_zlib_compression_method", before=hex_header, after=out, lossless=False,
                         note="zlib compression method CM = CMF & 0x0f (8 == deflate)")


def mmo_zlib_header_validate(hex_header: str, **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    b = bytes.fromhex(hex_header)
    cmf, flg = b[0], b[1]
    out = {"valid": (cmf & 0x0F) == 8 and ((cmf << 8) | flg) % 31 == 0}
    return out, _receipt("mmo_zlib_header_validate", before=hex_header, after=out, lossless=False,
                         note="validate zlib header: CM==8 (deflate) AND (CMF<<8|FLG) %% 31 == 0")


# ---- line diff / patch-apply / diff-stat / 3-way merge (synthetic text) ----
def mmo_line_diff(payload: dict[str, str], **_kw: Any) -> tuple[list[dict[str, str]], dict[str, Any]]:
    a_lines, b_lines = payload["a"].splitlines(), payload["b"].splitlines()
    sm = difflib.SequenceMatcher(None, a_lines, b_lines)
    patch: list[dict[str, str]] = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            patch += [{"tag": " ", "line": ln} for ln in a_lines[i1:i2]]
        elif tag == "delete":
            patch += [{"tag": "-", "line": ln} for ln in a_lines[i1:i2]]
        elif tag == "insert":
            patch += [{"tag": "+", "line": ln} for ln in b_lines[j1:j2]]
        elif tag == "replace":
            patch += [{"tag": "-", "line": ln} for ln in a_lines[i1:i2]]
            patch += [{"tag": "+", "line": ln} for ln in b_lines[j1:j2]]
    return patch, _receipt("mmo_line_diff", before=payload, after=patch, lossless=True,
                           note="{a,b} -> full-context line patch [{tag:' '|'+'|'-',line}]; mmo_patch_apply rebuilds b")


def mmo_patch_apply(patch: list[dict[str, str]], **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = "\n".join(p["line"] for p in patch if p["tag"] in (" ", "+"))
    return out, _receipt("mmo_patch_apply", before=patch, after=out, lossless=False,
                         note="apply full-context patch -> b text (keep context ' ' + additions '+')")


def mmo_patch_recover_a(patch: list[dict[str, str]], **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = "\n".join(p["line"] for p in patch if p["tag"] in (" ", "-"))
    return out, _receipt("mmo_patch_recover_a", before=patch, after=out, lossless=False,
                         note="recover original a text from patch (keep context ' ' + deletions '-')")


def mmo_diff_stat(patch: list[dict[str, str]], **_kw: Any) -> tuple[dict[str, int], dict[str, Any]]:
    out = {"additions": sum(1 for p in patch if p["tag"] == "+"),
           "deletions": sum(1 for p in patch if p["tag"] == "-"),
           "context": sum(1 for p in patch if p["tag"] == " ")}
    return out, _receipt("mmo_diff_stat", before=patch, after=out, lossless=False,
                         note="count patch additions/deletions/context lines")


def mmo_three_way_merge(payload: dict[str, str], **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    base, a, b = payload["base"], payload["a"], payload["b"]
    if a == base:
        merged, conflict = b, False
    elif b == base:
        merged, conflict = a, False
    elif a == b:
        merged, conflict = a, False
    else:
        merged, conflict = f"<<<<<<< a\n{a}\n=======\n{b}\n>>>>>>> b", True
    out = {"merged": merged, "conflict": conflict}
    return out, _receipt("mmo_three_way_merge", before=payload, after=out, lossless=False,
                         note="{base,a,b} -> deterministic whole-text 3-way merge; conflict markers when both diverge")


# ---- MIME type detect-from-ext  (+ inverse ext-from-mime on a bijective synthetic table) ----
_EXT_TO_MIME = {
    ".json": "application/json", ".csv": "text/csv", ".html": "text/html", ".txt": "text/plain",
    ".xml": "application/xml", ".pdf": "application/pdf", ".png": "image/png", ".jpg": "image/jpeg",
    ".gif": "image/gif", ".gz": "application/gzip", ".zip": "application/zip", ".yaml": "application/yaml",
    ".md": "text/markdown", ".js": "text/javascript", ".svg": "image/svg+xml",
}
_MIME_TO_EXT = {v: k for k, v in _EXT_TO_MIME.items()}


def mmo_mime_from_ext(ext: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    key = ext if ext.startswith(".") else "." + ext
    out = _EXT_TO_MIME.get(key.lower(), "application/octet-stream")
    return out, _receipt("mmo_mime_from_ext", before=ext, after=out, lossless=False,
                         note="file extension -> MIME type (fallback application/octet-stream)")


def mmo_ext_from_mime(mime: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = _MIME_TO_EXT.get(mime, "")
    return out, _receipt("mmo_ext_from_mime", before=mime, after=out, lossless=False,
                         note="MIME type -> canonical file extension (inverse of mmo_mime_from_ext on known table)")


def mmo_mime_is_text(mime: str, **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    out = {"is_text": mime.startswith("text/") or mime in {
        "application/json", "application/xml", "application/yaml", "image/svg+xml"}}
    return out, _receipt("mmo_mime_is_text", before=mime, after=out, lossless=False,
                         note="classify MIME as text-like (text/* + known textual application/* types)")


# ---- content tokenize (+ whitespace tokenize/detokenize roundtrip pair) ----
def mmo_content_tokenize(text: str, **_kw: Any) -> tuple[list[str], dict[str, Any]]:
    out = [t for t in re.split(r"[^A-Za-z0-9]+", text.lower()) if t]
    return out, _receipt("mmo_content_tokenize", before=text, after=out, lossless=False,
                         note="lowercase + split on non-alphanumeric -> token list")


def mmo_token_count(text: str, **_kw: Any) -> tuple[int, dict[str, Any]]:
    out = len([t for t in re.split(r"[^A-Za-z0-9]+", text.lower()) if t])
    return out, _receipt("mmo_token_count", before=text, after=out, lossless=False,
                         note="count content tokens")


def mmo_token_frequency(text: str, **_kw: Any) -> tuple[dict[str, int], dict[str, Any]]:
    freq: dict[str, int] = {}
    for t in [t for t in re.split(r"[^A-Za-z0-9]+", text.lower()) if t]:
        freq[t] = freq.get(t, 0) + 1
    out = {k: freq[k] for k in sorted(freq)}  # sorted keys -> deterministic
    return out, _receipt("mmo_token_frequency", before=text, after=out, lossless=False,
                         note="token -> count map (keys sorted for determinism)")


def mmo_whitespace_tokenize(text: str, **_kw: Any) -> tuple[list[str], dict[str, Any]]:
    out = text.split(" ")
    return out, _receipt("mmo_whitespace_tokenize", before=text, after=out, lossless=True,
                         note="single-space split -> tokens; mmo_whitespace_detokenize restores")


def mmo_whitespace_detokenize(tokens: list[str], **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = " ".join(tokens)
    return out, _receipt("mmo_whitespace_detokenize", before=tokens, after=out, lossless=True,
                         note="join tokens with single space -> text")


# ---- mustache-lite template render + variable extraction ----
_VAR_RE = re.compile(r"\{\{\s*([A-Za-z0-9_]+)\s*\}\}")


def mmo_template_render(payload: dict[str, Any], **_kw: Any) -> tuple[str, dict[str, Any]]:
    ctx = payload.get("context", {})
    out = _VAR_RE.sub(lambda m: str(ctx.get(m.group(1), "")), payload["template"])
    return out, _receipt("mmo_template_render", before=payload, after=out, lossless=False,
                         note="{template,context} -> rendered; {{var}} substituted (missing -> empty)")


def mmo_template_extract_vars(template: str, **_kw: Any) -> tuple[list[str], dict[str, Any]]:
    seen: list[str] = []
    for m in _VAR_RE.finditer(template):
        if m.group(1) not in seen:
            seen.append(m.group(1))
    return seen, _receipt("mmo_template_extract_vars", before=template, after=seen, lossless=False,
                          note="extract ordered unique {{var}} names from a mustache-lite template")


# ---- URL parse / build (roundtrip) / normalize / component extract ----
def mmo_url_parse(url: str, **_kw: Any) -> tuple[dict[str, str], dict[str, Any]]:
    sp = urlsplit(url)
    out = {"scheme": sp.scheme, "netloc": sp.netloc, "path": sp.path, "query": sp.query, "fragment": sp.fragment}
    return out, _receipt("mmo_url_parse", before=url, after=out, lossless=True,
                         note="url -> {scheme,netloc,path,query,fragment}; mmo_url_build restores")


def mmo_url_build(parts: dict[str, str], **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = urlunsplit((parts["scheme"], parts["netloc"], parts["path"], parts["query"], parts["fragment"]))
    return out, _receipt("mmo_url_build", before=parts, after=out, lossless=True,
                         note="{scheme,netloc,path,query,fragment} -> url string")


def mmo_url_host(url: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = urlsplit(url).hostname or ""
    return out, _receipt("mmo_url_host", before=url, after=out, lossless=False, note="extract URL host")


def mmo_url_scheme(url: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = urlsplit(url).scheme
    return out, _receipt("mmo_url_scheme", before=url, after=out, lossless=False, note="extract URL scheme")


def mmo_url_path(url: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = urlsplit(url).path
    return out, _receipt("mmo_url_path", before=url, after=out, lossless=False, note="extract URL path")


_DEFAULT_PORTS = {"http": "80", "https": "443", "ws": "80", "wss": "443"}


def mmo_url_normalize(url: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    sp = urlsplit(url)
    scheme = sp.scheme.lower()
    host = (sp.hostname or "").lower()
    netloc = host
    if sp.port is not None and str(sp.port) != _DEFAULT_PORTS.get(scheme):
        netloc = f"{host}:{sp.port}"
    path = sp.path or "/"
    out = urlunsplit((scheme, netloc, path, sp.query, ""))  # drop fragment; lowercase scheme+host; drop default port
    return out, _receipt("mmo_url_normalize", before=url, after=out, lossless=False,
                         note="normalize URL: lowercase scheme+host, drop default port, empty path->'/', drop fragment")


# ---- query-string encode (sorted) / decode (roundtrip) / get ----
def mmo_query_encode(params: dict[str, str], **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = urlencode(sorted(params.items()))
    return out, _receipt("mmo_query_encode", before=params, after=out, lossless=True,
                         note="dict -> sorted percent-encoded query string; mmo_query_decode restores")


def mmo_query_decode(qs: str, **_kw: Any) -> tuple[dict[str, str], dict[str, Any]]:
    out = dict(parse_qsl(qs))
    return out, _receipt("mmo_query_decode", before=qs, after=out, lossless=True,
                         note="query string -> {key:value} dict")


def mmo_query_get(payload: dict[str, str], **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = dict(parse_qsl(payload["qs"])).get(payload["key"], "")
    return out, _receipt("mmo_query_get", before=payload, after=out, lossless=False,
                         note="{qs,key} -> value of key in query string (missing -> empty)")


# ---- checksum compute / verify + ETag ----
def mmo_sha256_hex(content: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = hashlib.sha256(content.encode("utf-8")).hexdigest()
    return out, _receipt("mmo_sha256_hex", before=content, after=out, lossless=False,
                         note="sha256 hex digest of UTF-8 content (deterministic)")


def mmo_md5_hex(content: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = hashlib.md5(content.encode("utf-8")).hexdigest()
    return out, _receipt("mmo_md5_hex", before=content, after=out, lossless=False,
                         note="md5 hex digest of UTF-8 content (non-security checksum shape)")


def mmo_crc32(content: str, **_kw: Any) -> tuple[int, dict[str, Any]]:
    out = zlib.crc32(content.encode("utf-8")) & 0xFFFFFFFF
    return out, _receipt("mmo_crc32", before=content, after=out, lossless=False,
                         note="crc32 checksum (unsigned) of UTF-8 content")


def mmo_checksum_verify(payload: dict[str, str], **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    actual = hashlib.sha256(payload["content"].encode("utf-8")).hexdigest()
    out = {"valid": actual == payload["expected_sha256"], "actual_sha256": actual}
    return out, _receipt("mmo_checksum_verify", before=payload, after=out, lossless=False,
                         note="{content,expected_sha256} -> {valid, actual_sha256}")


def mmo_etag_compute(content: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = '"' + hashlib.md5(content.encode("utf-8")).hexdigest() + '"'
    return out, _receipt("mmo_etag_compute", before=content, after=out, lossless=False,
                         note='strong ETag = quoted md5 hex of content')


def mmo_etag_weak_compute(content: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = 'W/"' + hashlib.md5(content.encode("utf-8")).hexdigest() + '"'
    return out, _receipt("mmo_etag_weak_compute", before=content, after=out, lossless=False,
                         note='weak ETag = W/ quoted md5 hex of content')


def mmo_etag_match(payload: dict[str, str], **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    def _strip(e: str) -> str:
        return e[2:] if e.startswith("W/") else e
    out = {"match": _strip(payload["etag"]) == _strip(payload["candidate"])}
    return out, _receipt("mmo_etag_match", before=payload, after=out, lossless=False,
                         note="ETag comparison (weak: ignore W/ prefix) -> {match}")


#: new pure mutators to plug into the shared registry (idempotent setdefault — never overwrites an existing entry)
_NEW_MUTATORS = {
    "mmo_gzip_header_parse": mmo_gzip_header_parse, "mmo_gzip_magic_validate": mmo_gzip_magic_validate,
    "mmo_zlib_header_parse": mmo_zlib_header_parse, "mmo_zlib_compression_method": mmo_zlib_compression_method,
    "mmo_zlib_header_validate": mmo_zlib_header_validate,
    "mmo_line_diff": mmo_line_diff, "mmo_patch_apply": mmo_patch_apply, "mmo_patch_recover_a": mmo_patch_recover_a,
    "mmo_diff_stat": mmo_diff_stat, "mmo_three_way_merge": mmo_three_way_merge,
    "mmo_mime_from_ext": mmo_mime_from_ext, "mmo_ext_from_mime": mmo_ext_from_mime, "mmo_mime_is_text": mmo_mime_is_text,
    "mmo_content_tokenize": mmo_content_tokenize, "mmo_token_count": mmo_token_count,
    "mmo_token_frequency": mmo_token_frequency, "mmo_whitespace_tokenize": mmo_whitespace_tokenize,
    "mmo_whitespace_detokenize": mmo_whitespace_detokenize,
    "mmo_template_render": mmo_template_render, "mmo_template_extract_vars": mmo_template_extract_vars,
    "mmo_url_parse": mmo_url_parse, "mmo_url_build": mmo_url_build, "mmo_url_host": mmo_url_host,
    "mmo_url_scheme": mmo_url_scheme, "mmo_url_path": mmo_url_path, "mmo_url_normalize": mmo_url_normalize,
    "mmo_query_encode": mmo_query_encode, "mmo_query_decode": mmo_query_decode, "mmo_query_get": mmo_query_get,
    "mmo_sha256_hex": mmo_sha256_hex, "mmo_md5_hex": mmo_md5_hex, "mmo_crc32": mmo_crc32,
    "mmo_checksum_verify": mmo_checksum_verify, "mmo_etag_compute": mmo_etag_compute,
    "mmo_etag_weak_compute": mmo_etag_weak_compute, "mmo_etag_match": mmo_etag_match,
}


def register_new_mutators() -> None:
    """Plug the domain's pure mutators into the shared MUTATOR_REGISTRY (registration, not a rewrite). Idempotent."""
    for name, fn in _NEW_MUTATORS.items():
        MUTATOR_REGISTRY.setdefault(name, fn)


register_new_mutators()


# ── proven-deterministic leaves: each a REAL SHAPE capability with a synthetic fixture + expected (+ inverse where a
#    roundtrip holds). spec fields: id, mutator, fixture, expected, args?, inverse?, format, input_edge, output_edge ──
_SHA_HW = "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"  # sha256("hello world")
_MD5_HW = "5eb63bbbe01eeed093cb22bb8f5acdc3"                                    # md5("hello world")
_MD5_CB = "33e6191d5894d58f4ed1a8e7f1a4607a"                                    # md5("content-body")
_SHA_CB = "9fa439ea15dcd3275374c1c6f69489582f6e629f5948e6cd57f9f9968883fac5"  # sha256("content-body")

_DIFF_PATCH = [{"tag": " ", "line": "line1"}, {"tag": "-", "line": "line2"},
               {"tag": "+", "line": "line2x"}, {"tag": " ", "line": "line3"}]

LEAF_SPECS: list[dict[str, Any]] = [
    # gzip / zlib header shape
    {"id": "prim:leaf:mmo_gzip_header_parse", "mutator": "mmo_gzip_header_parse", "format": "compression_header",
     "fixture": "1f8b0800000000000003",
     "expected": {"id1": 31, "id2": 139, "method": 8, "flags": 0, "mtime": 0, "xfl": 0, "os": 3},
     "input_edge": "GzipHeaderHex", "output_edge": "GzipHeader"},
    {"id": "prim:leaf:mmo_gzip_magic_validate", "mutator": "mmo_gzip_magic_validate", "format": "compression_header",
     "fixture": "1f8b08", "expected": {"valid": True}, "input_edge": "GzipHeaderHex", "output_edge": "ValidationResult"},
    {"id": "prim:leaf:mmo_zlib_header_parse", "mutator": "mmo_zlib_header_parse", "format": "compression_header",
     "fixture": "789c", "expected": {"cm": 8, "cinfo": 7, "window_size": 32768, "fcheck_ok": True, "fdict": False},
     "input_edge": "ZlibHeaderHex", "output_edge": "ZlibHeader"},
    {"id": "prim:leaf:mmo_zlib_compression_method", "mutator": "mmo_zlib_compression_method", "format": "compression_header",
     "fixture": "789c", "expected": 8, "input_edge": "ZlibHeaderHex", "output_edge": "CompressionMethod"},
    {"id": "prim:leaf:mmo_zlib_header_validate", "mutator": "mmo_zlib_header_validate", "format": "compression_header",
     "fixture": "789c", "expected": {"valid": True}, "input_edge": "ZlibHeaderHex", "output_edge": "ValidationResult"},

    # line diff / patch / merge
    {"id": "prim:leaf:mmo_line_diff", "mutator": "mmo_line_diff", "format": "line_diff",
     "fixture": {"a": "line1\nline2\nline3", "b": "line1\nline2x\nline3"}, "expected": _DIFF_PATCH,
     "input_edge": "TextPair", "output_edge": "LinePatch"},
    {"id": "prim:leaf:mmo_patch_apply", "mutator": "mmo_patch_apply", "format": "line_diff",
     "fixture": _DIFF_PATCH, "expected": "line1\nline2x\nline3",
     "input_edge": "LinePatch", "output_edge": "PatchedText"},
    {"id": "prim:leaf:mmo_patch_recover_a", "mutator": "mmo_patch_recover_a", "format": "line_diff",
     "fixture": _DIFF_PATCH, "expected": "line1\nline2\nline3",
     "input_edge": "LinePatch", "output_edge": "OriginalText"},
    {"id": "prim:leaf:mmo_diff_stat", "mutator": "mmo_diff_stat", "format": "line_diff",
     "fixture": _DIFF_PATCH, "expected": {"additions": 1, "deletions": 1, "context": 2},
     "input_edge": "LinePatch", "output_edge": "DiffStat"},
    {"id": "prim:leaf:mmo_three_way_merge", "mutator": "mmo_three_way_merge", "format": "line_diff",
     "fixture": {"base": "x", "a": "x", "b": "y"}, "expected": {"merged": "y", "conflict": False},
     "input_edge": "ThreeWayInput", "output_edge": "MergeResult"},

    # MIME
    {"id": "prim:leaf:mmo_mime_from_ext", "mutator": "mmo_mime_from_ext", "format": "mime_type",
     "fixture": ".json", "expected": "application/json", "inverse": "mmo_ext_from_mime",
     "input_edge": "FileExtension", "output_edge": "MimeType"},
    {"id": "prim:leaf:mmo_ext_from_mime", "mutator": "mmo_ext_from_mime", "format": "mime_type",
     "fixture": "text/csv", "expected": ".csv", "inverse": "mmo_mime_from_ext",
     "input_edge": "MimeType", "output_edge": "FileExtension"},
    {"id": "prim:leaf:mmo_mime_is_text", "mutator": "mmo_mime_is_text", "format": "mime_type",
     "fixture": "application/json", "expected": {"is_text": True},
     "input_edge": "MimeType", "output_edge": "ValidationResult"},

    # tokenize
    {"id": "prim:leaf:mmo_content_tokenize", "mutator": "mmo_content_tokenize", "format": "text_tokens",
     "fixture": "Hello, World! 42", "expected": ["hello", "world", "42"],
     "input_edge": "Text", "output_edge": "TokenList"},
    {"id": "prim:leaf:mmo_token_count", "mutator": "mmo_token_count", "format": "text_tokens",
     "fixture": "the cat sat", "expected": 3, "input_edge": "Text", "output_edge": "Count"},
    {"id": "prim:leaf:mmo_token_frequency", "mutator": "mmo_token_frequency", "format": "text_tokens",
     "fixture": "a b a c b a", "expected": {"a": 3, "b": 2, "c": 1},
     "input_edge": "Text", "output_edge": "TokenFrequency"},
    {"id": "prim:leaf:mmo_whitespace_tokenize", "mutator": "mmo_whitespace_tokenize", "format": "text_tokens",
     "fixture": "one two three", "expected": ["one", "two", "three"], "inverse": "mmo_whitespace_detokenize",
     "input_edge": "Text", "output_edge": "TokenList"},
    {"id": "prim:leaf:mmo_whitespace_detokenize", "mutator": "mmo_whitespace_detokenize", "format": "text_tokens",
     "fixture": ["alpha", "beta"], "expected": "alpha beta", "inverse": "mmo_whitespace_tokenize",
     "input_edge": "TokenList", "output_edge": "Text"},

    # mustache-lite template
    {"id": "prim:leaf:mmo_template_render", "mutator": "mmo_template_render", "format": "template",
     "fixture": {"template": "Hi {{name}}, you have {{n}} msgs", "context": {"name": "Sam", "n": 3}},
     "expected": "Hi Sam, you have 3 msgs", "input_edge": "TemplateInput", "output_edge": "RenderedText"},
    {"id": "prim:leaf:mmo_template_extract_vars", "mutator": "mmo_template_extract_vars", "format": "template",
     "fixture": "{{a}} and {{ b }} and {{a}}", "expected": ["a", "b"],
     "input_edge": "TemplateText", "output_edge": "TemplateVars"},

    # URL
    {"id": "prim:leaf:mmo_url_parse", "mutator": "mmo_url_parse", "format": "url",
     "fixture": "https://example.com/a/b?x=1#frag",
     "expected": {"scheme": "https", "netloc": "example.com", "path": "/a/b", "query": "x=1", "fragment": "frag"},
     "inverse": "mmo_url_build", "input_edge": "Url", "output_edge": "UrlParts"},
    {"id": "prim:leaf:mmo_url_build", "mutator": "mmo_url_build", "format": "url",
     "fixture": {"scheme": "http", "netloc": "host.test:8080", "path": "/p", "query": "q=2", "fragment": ""},
     "expected": "http://host.test:8080/p?q=2", "inverse": "mmo_url_parse",
     "input_edge": "UrlParts", "output_edge": "Url"},
    {"id": "prim:leaf:mmo_url_host", "mutator": "mmo_url_host", "format": "url",
     "fixture": "https://api.example.com:443/v1/x", "expected": "api.example.com",
     "input_edge": "Url", "output_edge": "UrlHost"},
    {"id": "prim:leaf:mmo_url_scheme", "mutator": "mmo_url_scheme", "format": "url",
     "fixture": "ftp://files.test/x", "expected": "ftp", "input_edge": "Url", "output_edge": "UrlScheme"},
    {"id": "prim:leaf:mmo_url_path", "mutator": "mmo_url_path", "format": "url",
     "fixture": "https://x.test/a/b/c?z=1", "expected": "/a/b/c", "input_edge": "Url", "output_edge": "UrlPath"},
    {"id": "prim:leaf:mmo_url_normalize", "mutator": "mmo_url_normalize", "format": "url",
     "fixture": "HTTPS://Example.COM:443?a=1#top", "expected": "https://example.com/?a=1",
     "input_edge": "Url", "output_edge": "NormalizedUrl"},

    # query string
    {"id": "prim:leaf:mmo_query_encode", "mutator": "mmo_query_encode", "format": "query_string",
     "fixture": {"b": "2", "a": "1"}, "expected": "a=1&b=2", "inverse": "mmo_query_decode",
     "input_edge": "QueryParams", "output_edge": "QueryString"},
    {"id": "prim:leaf:mmo_query_decode", "mutator": "mmo_query_decode", "format": "query_string",
     "fixture": "a=1&b=2", "expected": {"a": "1", "b": "2"}, "inverse": "mmo_query_encode",
     "input_edge": "QueryString", "output_edge": "QueryParams"},
    {"id": "prim:leaf:mmo_query_get", "mutator": "mmo_query_get", "format": "query_string",
     "fixture": {"qs": "user=u1&page=2", "key": "page"}, "expected": "2",
     "input_edge": "QueryGetInput", "output_edge": "QueryValue"},

    # checksum + ETag
    {"id": "prim:leaf:mmo_sha256_hex", "mutator": "mmo_sha256_hex", "format": "checksum",
     "fixture": "hello world", "expected": _SHA_HW, "input_edge": "Content", "output_edge": "Sha256Hex"},
    {"id": "prim:leaf:mmo_md5_hex", "mutator": "mmo_md5_hex", "format": "checksum",
     "fixture": "hello world", "expected": _MD5_HW, "input_edge": "Content", "output_edge": "Md5Hex"},
    {"id": "prim:leaf:mmo_crc32", "mutator": "mmo_crc32", "format": "checksum",
     "fixture": "hello world", "expected": 222957957, "input_edge": "Content", "output_edge": "Crc32"},
    {"id": "prim:leaf:mmo_checksum_verify", "mutator": "mmo_checksum_verify", "format": "checksum",
     "fixture": {"content": "content-body", "expected_sha256": _SHA_CB},
     "expected": {"valid": True, "actual_sha256": _SHA_CB},
     "input_edge": "ChecksumVerifyInput", "output_edge": "ValidationResult"},
    {"id": "prim:leaf:mmo_etag_compute", "mutator": "mmo_etag_compute", "format": "etag",
     "fixture": "content-body", "expected": '"' + _MD5_CB + '"', "input_edge": "Content", "output_edge": "ETag"},
    {"id": "prim:leaf:mmo_etag_weak_compute", "mutator": "mmo_etag_weak_compute", "format": "etag",
     "fixture": "content-body", "expected": 'W/"' + _MD5_CB + '"', "input_edge": "Content", "output_edge": "WeakETag"},
    {"id": "prim:leaf:mmo_etag_match", "mutator": "mmo_etag_match", "format": "etag",
     "fixture": {"etag": 'W/"' + _MD5_CB + '"', "candidate": '"' + _MD5_CB + '"'}, "expected": {"match": True},
     "input_edge": "ETagMatchInput", "output_edge": "ValidationResult"},
]

#: deliberately-wrong leaf — the proof gate MUST leave it candidate (never persisted as proven-deterministic)
NEGATIVE_SPEC: dict[str, Any] = {
    "id": "prim:leaf:mmo_WRONG_expected", "mutator": "mmo_url_scheme", "format": "url",
    "fixture": "https://x.test/", "expected": "WRONG", "input_edge": "Url", "output_edge": "UrlScheme"}


# ── GATED-EFFECT candidates: NETWORK / EFFECTFUL capabilities. NEVER run through the proof runner, NEVER
#    serve_truth. Each declares effect + proof_obligation (a live integration test with a credential) + typed edges. ──
GATED_EFFECT_SPECS: list[dict[str, Any]] = [
    {"id": "prim:gated:mmo_http_get_with_etag", "capability": "HTTP GET with If-None-Match — conditional fetch of a remote resource by ETag",
     "effect": "network_read", "proof_obligation": "live integration test against a sandbox HTTP origin that returns 200/304 by ETag",
     "input_edge": "Url", "output_edge": "HttpResponse", "format": "url"},
    {"id": "prim:gated:mmo_http_head_fetch_etag", "capability": "HTTP HEAD — fetch a remote resource's ETag header",
     "effect": "network_read", "proof_obligation": "live integration test against a sandbox HTTP origin serving an ETag header",
     "input_edge": "Url", "output_edge": "ETag", "format": "etag"},
    {"id": "prim:gated:mmo_upload_gzip_object", "capability": "Upload a gzip-compressed object body to a remote object store",
     "effect": "network_write", "proof_obligation": "live integration test uploading to a sandbox object-store bucket with a credential",
     "input_edge": "GzipHeader", "output_edge": "UploadResult", "format": "compression_header"},
    {"id": "prim:gated:mmo_write_patched_file", "capability": "Write a patched text file to local disk",
     "effect": "file_write", "proof_obligation": "live integration test writing to a sandbox temp path and reading it back",
     "input_edge": "PatchedText", "output_edge": "FileWriteResult", "format": "line_diff"},
    {"id": "prim:gated:mmo_push_merge_result", "capability": "Push a 3-way merge result to a remote VCS branch",
     "effect": "network_write", "proof_obligation": "live integration test against a sandbox git remote with credentials",
     "input_edge": "MergeResult", "output_edge": "PushResult", "format": "line_diff"},
    {"id": "prim:gated:mmo_fetch_url_body", "capability": "HTTP GET — download a URL's response body",
     "effect": "network_read", "proof_obligation": "live integration test against a sandbox HTTP origin",
     "input_edge": "Url", "output_edge": "HttpBody", "format": "url"},
]


def _prove_one(spec: dict[str, Any]) -> dict[str, Any]:
    return run_primitive_proof(
        spec["id"], spec["mutator"], spec["fixture"], spec["expected"],
        mutator_args=spec.get("args") or {}, has_inverse=spec.get("inverse"),
    )


def prove_all() -> list[tuple[dict[str, Any], dict[str, Any]]]:
    """Run every declared deterministic leaf through the imported executed-proof runner. Returns [(spec, receipt), ...]."""
    return [(s, _prove_one(s)) for s in LEAF_SPECS]


def build_proven_rows() -> list[dict[str, Any]]:
    """Persist-ready rows for leaves whose executed proof PASSED — TYPED via canonicalize_edge (workable == typed)."""
    rows: list[dict[str, Any]] = []
    for spec, receipt in prove_all():
        if receipt["serves_truth"] is not True:
            continue  # a failing / wrong-expected leaf stays candidate and is NOT persisted (the gate is the point)
        rows.append({
            "primitive_id": receipt["primitive_id"],
            "mutator": receipt["mutator"],
            "domain": DOMAIN,
            "format": spec["format"],
            "row_section": "proven_deterministic",
            "candidate": False,
            "serves_truth": True,
            "verification_level": "L7_executed_proof",
            "input_edge": spec["input_edge"],
            "output_edge": spec["output_edge"],
            "input_edge_type_id": canonicalize_edge(spec["input_edge"]),
            "output_edge_type_id": canonicalize_edge(spec["output_edge"]),
            "has_inverse": spec.get("inverse"),
            "proofs": [p["name"] for p in receipt["proofs"] if p["passed"]],
        })
    return rows


def build_gated_rows() -> list[dict[str, Any]]:
    """Gated-effect candidate rows — NEVER proven, NEVER serves_truth; typed so they still declare their edges."""
    rows: list[dict[str, Any]] = []
    for spec in GATED_EFFECT_SPECS:
        rows.append({
            "primitive_id": spec["id"],
            "domain": DOMAIN,
            "format": spec["format"],
            "row_section": "gated_effect_candidate",
            "capability": spec["capability"],
            "candidate": True,
            "serves_truth": False,
            "effect": spec["effect"],
            "proof_obligation": spec["proof_obligation"],
            "input_edge": spec["input_edge"],
            "output_edge": spec["output_edge"],
            "input_edge_type_id": canonicalize_edge(spec["input_edge"]),
            "output_edge_type_id": canonicalize_edge(spec["output_edge"]),
        })
    return rows


def build_manifest(proven: list[dict[str, Any]], gated: list[dict[str, Any]]) -> dict[str, Any]:
    typed = [r for r in proven if r["input_edge_type_id"] and r["output_edge_type_id"]]
    return {
        "record_type": "domain_primitive_shard_manifest",
        "domain": DOMAIN,
        "generator": "scripts/domain_med_more_operations.py",
        "generated_utc": _FIXED_UTC,
        "formats_covered": sorted({s["format"] for s in LEAF_SPECS}),
        # SEPARATE, honest counts (proven-deterministic vs gated-effect candidate).
        "defined_deterministic_count": len(LEAF_SPECS),
        "proven_deterministic": len(proven),
        "typed": len(typed),
        "gated_effect_candidates": len(gated),
        "gated_effect_by_effect": {e: sum(1 for r in gated if r["effect"] == e)
                                   for e in sorted({r["effect"] for r in gated})},
        "verification_level": "L7_executed_proof",
        "proven_primitive_ids": sorted(r["primitive_id"] for r in proven),
        "gated_effect_primitive_ids": sorted(r["primitive_id"] for r in gated),
        "note": "proven_deterministic rows: serves_truth=true set ONLY by an executed passing proof (run_primitive_proof, "
                "imported from scripts/mutator_registry.py); every row TYPED via canonicalize_edge (imported from "
                "scripts/build_edge_type_retrofit.py). gated_effect_candidate rows: network/effectful capabilities are "
                "NEVER proven and stay candidate/serves_truth=false with an effect + proof_obligation. Synthetic/public "
                "content only; NO insurance; NO healthcare-clinical; NO real PII/secrets. Counts are separate and honest.",
    }


def write_shard() -> dict[str, Any]:
    proven = build_proven_rows()
    gated = build_gated_rows()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    # Both sections written to the SAME shard, each row self-labels via row_section.
    all_rows = proven + gated
    OUT_JSONL.write_text(
        "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in all_rows), encoding="utf-8")
    manifest = build_manifest(proven, gated)
    OUT_MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def self_test() -> int:
    proven = prove_all()
    rows = build_proven_rows()
    gated = build_gated_rows()
    ids = [r["primitive_id"] for r in rows]
    typed = [r for r in rows if r["input_edge_type_id"] and r["output_edge_type_id"]]
    roundtrip_specs = [s for s in LEAF_SPECS if s.get("inverse")]
    proven_by_id = {r["primitive_id"]: r for (s, r) in proven}

    # deliberately-wrong leaf must stay candidate (proof gate is real) — and never enter the proven section
    wrong = _prove_one(NEGATIVE_SPEC)
    # a second wrong path: an un-runnable fixture -> execution error -> not promoted
    err = run_primitive_proof("prim:leaf:mmo_EXEC_ERROR", "mmo_gzip_header_parse", object(), "irrelevant")

    manifest = build_manifest(rows, gated)
    valid_effects = {"network_read", "network_write", "model_call", "file_write"}
    target_formats = {"compression_header", "line_diff", "mime_type", "text_tokens",
                      "template", "url", "query_string", "checksum", "etag"}

    checks: list[tuple[str, bool]] = [
        (">=25 deterministic leaves declared", len(LEAF_SPECS) >= 25),
        ("unique proven primitive ids", len(set(ids)) == len(ids)),
        (">=25 leaves PROVE serves_truth=true via an executed proof", len(rows) >= 25),
        ("every proven receipt is L7_executed_proof with all sub-proofs passing",
         all(r["verification_level"] == "L7_executed_proof" and all(p["passed"] for p in r["proofs"])
             for (_s, r) in proven if r["serves_truth"] is True)),
        ("EVERY proven row carries non-null input+output edge type ids", len(typed) == len(rows)),
        ("manifest typed == proven_deterministic", manifest["typed"] == manifest["proven_deterministic"]),
        ("all 9 target formats are covered", set(manifest["formats_covered"]) == target_formats),
        ("roundtrip-inverse pairs actually ran + PASSED a roundtrip proof", all(
            any(p["name"] == "roundtrip_test" and p["passed"] for p in proven_by_id[s["id"]]["proofs"])
            for s in roundtrip_specs)),
        ("domain stamped on every proven row", all(r["domain"] == DOMAIN for r in rows)),
        ("deterministic: re-running yields identical proven rows",
         [json.dumps(r, sort_keys=True) for r in build_proven_rows()] == [json.dumps(r, sort_keys=True) for r in rows]),
        # gated-effect law: EVERY gated row is candidate / serves_truth=false with a valid effect + proof_obligation
        (">=1 gated-effect candidate declared", len(gated) >= 1),
        ("EVERY gated-effect row is candidate + serves_truth=false",
         all(r["candidate"] is True and r["serves_truth"] is False for r in gated)),
        ("EVERY gated-effect row has a valid effect + non-empty proof_obligation",
         all(r["effect"] in valid_effects and isinstance(r["proof_obligation"], str) and r["proof_obligation"]
             for r in gated)),
        ("EVERY gated-effect row is TYPED (input+output edge type ids)",
         all(r["input_edge_type_id"] and r["output_edge_type_id"] for r in gated)),
        ("no gated-effect id leaked into the proven section", not (set(r["primitive_id"] for r in gated) & set(ids))),
        # the proof gate is real
        ("a deliberately-wrong leaf stays CANDIDATE (never promoted)",
         wrong["serves_truth"] is False and wrong["promoted"] is False),
        ("the wrong leaf is NOT persisted as proven", NEGATIVE_SPEC["id"] not in set(ids)),
        ("an un-runnable fixture fails the proof, does not promote",
         err["serves_truth"] is False and err["promoted"] is False),
        ("new mutators registered into the shared registry (add-only seam)",
         all(m in MUTATOR_REGISTRY for m in _NEW_MUTATORS)),
    ]
    failed = [n for n, ok in checks if not ok]
    if failed:
        print("FAIL - domain_med_more_operations:\n  " + "\n  ".join(failed))
        return 1
    print(f"PASS - domain_med_more_operations: {len(rows)} WORKABLE (proven + TYPED) deterministic SHAPE leaves for "
          f"'{DOMAIN}' (serves_truth=true, L7_executed_proof; typed=={len(rows)}) across {len(target_formats)} operation "
          f"formats; {len(roundtrip_specs)} inverse pairs proven reversible via roundtrip; {len(gated)} "
          "network/effectful capabilities declared as GATED-EFFECT candidates (serves_truth=false, effect + "
          "proof_obligation). A deliberately-wrong leaf and an un-runnable fixture correctly stay candidate. "
          "Synthetic content; no PII/secrets; no insurance; no healthcare-clinical.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    if args.write:
        manifest = write_shard()
        print(json.dumps(manifest, indent=2, sort_keys=True))
        return self_test()
    return self_test()


if __name__ == "__main__":
    raise SystemExit(main())
