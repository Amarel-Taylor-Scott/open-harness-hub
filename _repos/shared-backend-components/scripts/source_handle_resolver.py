#!/usr/bin/env python3
"""scripts.source_handle_resolver — the Source-Handle Resolution Service (foundational).

Everything in Baltor references context by `ctx://` source handle, so this is the service the
rest of the system calls: parse / validate / resolve / expand a handle, and check whether what it
points at is still fresh (hash CDC), permitted (ACL), and in-TTL. It is a thin ORCHESTRATION layer
that composes the proven modules — `document_decompose` (resolve/expand a doc fragment handle to
its node), `context_rot` (TTL + content-hash + ACL + supersession verdict), `scrapers.content_hash`
(the CDC identity) — and adds no new scoring.

Handle grammar (the ctx:// scheme used across Baltor):
    ctx://<source>/<kind>/<id>[#k=v&k=v...]
e.g. ctx://acme/doc/policy#page=0487&block=03 · ctx://ofac/sdn · ctx://acme/github/repo/billing

Deterministic + offline (the live "what changed upstream" observation is HANDED in, as in
context_rot; the self-test resolves against an in-memory decomposed tree). Stdlib only.

CLI:
    python3 _repos/shared-backend-components/scripts/source_handle_resolver.py --self-test
"""
from __future__ import annotations

import argparse
from typing import Any

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    import os
    import sys

    _REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _REPO_ROOT not in sys.path:
        sys.path.insert(0, _REPO_ROOT)

from scripts.foundry.scrapers import content_hash
from scripts.ingest import context_rot
from scripts.ingest.document_decompose import DocumentTree, expand as _decompose_expand, resolve as _decompose_resolve

HANDLE_SCHEME = "ctx://"


def validate(handle: str) -> bool:
    """A well-formed source handle starts with ctx:// and names a non-empty path."""
    if not isinstance(handle, str) or not handle.startswith(HANDLE_SCHEME):
        return False
    rest = handle[len(HANDLE_SCHEME):].split("#", 1)[0]
    return bool(rest.strip("/"))


def parse(handle: str) -> dict[str, Any]:
    """Parse a handle into {source, path, fragment{...}}. Raises ValueError if malformed."""
    if not validate(handle):
        raise ValueError(f"malformed source handle (must start with {HANDLE_SCHEME!r} + a path): {handle!r}")
    body = handle[len(HANDLE_SCHEME):]
    path_part, _, frag_part = body.partition("#")
    segs = [s for s in path_part.split("/") if s]
    fragment: dict[str, str] = {}
    for kv in frag_part.split("&") if frag_part else []:
        if "=" in kv:
            k, v = kv.split("=", 1)
            fragment[k] = v
    return {"source": segs[0] if segs else None, "path": segs, "fragment": fragment, "raw": handle}


def resolve(handle: str, *, tree: DocumentTree | None = None) -> dict[str, Any]:
    """Resolve a handle to its target.

    For a document fragment handle (`ctx://…/doc/…#page=…`) and a provided decomposed ``tree``,
    returns the matching node (via document_decompose). Otherwise returns the parsed handle (the
    live fetch of an external source is the connector's job — a SEAM, not faked here).
    Raises KeyError (``source_handle_unresolvable``) if a doc handle does not match the tree.
    """
    parsed = parse(handle)
    if tree is not None and parsed["fragment"]:
        node = _decompose_resolve(tree, handle)
        if node is None:
            raise KeyError(f"{context_rot.STATE_HANDLE_UNRESOLVABLE}: {handle}")
        return {"resolved": True, "kind": node.kind, "node": node.as_dict(), "parsed": parsed}
    return {"resolved": tree is None, "parsed": parsed,
            "note": "external/non-fragment handle — resolution against the live source is the connector seam"}


def expand(handle: str, tree: DocumentTree, *, with_parent: bool = False, with_children: bool = False) -> dict[str, Any]:
    """Expand a doc fragment handle to exactly its node (+ optional parent/children). Delegates to
    document_decompose.expand — the minimal-node expansion that keeps packs small."""
    return _decompose_expand(tree, handle, with_parent=with_parent, with_children=with_children)


def freshness(
    handle: str,
    *,
    cached_at_s: int,
    now_s: int,
    ttl_class: str,
    cached_content_hash: str = "",
    current_content_hash: str | None = None,
    cached_acl_hash: str | None = None,
    current_acl_hash: str | None = None,
    resolvable: bool = True,
    superseded: bool = False,
) -> dict[str, Any]:
    """Is what this handle points at still safe to serve? Composes context_rot.assess (TTL + CDC +
    ACL + supersession). Returns the rot assessment as a dict."""
    item = context_rot.CachedItem(handle=handle, ttl_class=ttl_class, cached_at_s=cached_at_s,
                                  content_hash=cached_content_hash, acl_hash=cached_acl_hash)
    return context_rot.assess(item, now_s=now_s, current_content_hash=current_content_hash,
                              current_acl_hash=current_acl_hash, resolvable=resolvable,
                              superseded=superseded).as_dict()


def _self_test() -> int:
    from scripts.ingest.document_decompose import CannedParser, decompose
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    # ── validate / parse ──
    check("validate accepts a ctx:// handle", validate("ctx://acme/doc/policy#page=0001&block=02"))
    check("validate rejects http://", not validate("http://example.com"))
    check("validate rejects scheme-only", not validate("ctx://"))
    p = parse("ctx://acme/doc/policy#page=0487&block=03")
    check("parse splits source/path/fragment", p["source"] == "acme" and p["fragment"] == {"page": "0487", "block": "03"}, str(p))
    raised = False
    try:
        parse("not-a-handle")
    except ValueError:
        raised = True
    check("parse raises on malformed", raised)

    # ── resolve / expand against a decomposed tree ──
    parsed_doc = {"pages": [{"page_no": 1, "blocks": [
        {"kind": "heading", "ordinal": 0, "text": "Policy"},
        {"kind": "paragraph", "ordinal": 1, "text": "Screen all counterparties."}]}]}
    tree = decompose("acme", "policy", CannedParser(parsed_doc).parse(None))
    h = "ctx://acme/doc/policy#page=0001&block=02"
    r = resolve(h, tree=tree)
    check("resolve a doc fragment handle → its node", r["resolved"] and "Screen all counterparties." in r["node"]["text"], str(r.get("kind")))
    ex = expand(h, tree, with_parent=True)
    check("expand returns exactly the node + parent page", ex["node"]["source_handle"] == h and ex["parent"]["kind"] == "page")
    bad_raised = False
    try:
        resolve("ctx://acme/doc/policy#page=0099&block=99", tree=tree)
    except KeyError:
        bad_raised = True
    check("unresolvable doc handle raises", bad_raised)

    # ── freshness (composes context_rot) ──
    now = 1_000_000_000
    chash = content_hash("ofac list v1")
    fresh = freshness("ctx://ofac/sdn", cached_at_s=now - context_rot.SECONDS_PER_HOUR, now_s=now,
                      ttl_class="raw_snapshot", cached_content_hash=chash, current_content_hash=chash)
    check("in-TTL, unchanged → fresh/serve", fresh["state"] == context_rot.STATE_FRESH and fresh["servable"])
    changed = freshness("ctx://ofac/sdn", cached_at_s=now - context_rot.SECONDS_PER_HOUR, now_s=now,
                        ttl_class="raw_snapshot", cached_content_hash=chash,
                        current_content_hash=content_hash("ofac list v2"))
    check("upstream hash changed → refresh", changed["state"] == context_rot.STATE_SOURCE_HASH_CHANGED)
    expired = freshness("ctx://ofac/sdn", cached_at_s=now - 3 * context_rot.SECONDS_PER_DAY, now_s=now,
                        ttl_class="raw_snapshot", cached_content_hash=chash, current_content_hash=chash)
    check("past TTL → expired (not servable)", expired["state"] == context_rot.STATE_EXPIRED and not expired["servable"])
    acl = freshness("ctx://acme/doc/policy", cached_at_s=now, now_s=now, ttl_class="generated_artifact",
                    cached_content_hash=chash, current_content_hash=chash, cached_acl_hash="v1", current_acl_hash="v2")
    check("ACL changed → block (not servable)", acl["state"] == context_rot.STATE_PERMISSION_CHANGED and not acl["servable"])

    # ── determinism ──
    check("freshness is deterministic", freshness("ctx://ofac/sdn", cached_at_s=now, now_s=now, ttl_class="pack",
          cached_content_hash=chash, current_content_hash=chash) == freshness("ctx://ofac/sdn", cached_at_s=now,
          now_s=now, ttl_class="pack", cached_content_hash=chash, current_content_hash=chash))

    print(f"\n{'all source_handle_resolver self-tests passed.' if not failures else f'{len(failures)} FAILURES: {failures}'}")
    return 0 if not failures else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Source-Handle Resolution Service (parse/validate/resolve/expand/freshness over ctx:// handles).")
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args(argv)
    if args.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
