#!/usr/bin/env python3
"""experiments/primitive_store — the git-like, content-addressed, scoped store for primitives (ours AND
external) + the GENERIC EXECUTOR that runs a primitive by reference.

This is the reference implementation of the rules the owner set for storing primitives across a database, a
git-like environment (forks / parallel versions / merges), and buckets — plus the "one generic stateless
executor, fetch the code by ref" idea. It is a CANDIDATE reference impl (experiments/): stdlib-only, offline,
`--self-test`-able. The production wiring points are called out inline (canonical_id single-source, the real
object bucket via the credential-plane, the real sandbox, the Omnigraph instance, run_proofs).

THE RULES IT ENCODES (each asserted in --self-test):
  1. CONTENT plane  — a primitive's body/code lives content-addressed in a bucket, keyed by canonical hash
                      (dedup + integrity). Long bodies never bloat the lineage or the DB.
  2. LINEAGE plane  — a git-like DAG: branch (parallel versions of one key), fork (derive a NEW primitive),
                      merge (remix — two parents), supersede (new version, prior KEPT never overwritten).
  3. QUERY plane    — a searchable index; a rebuildable projection, not the source of truth.
  4. SCOPE          — every primitive is PUBLIC (externally available: searchable + runnable) or INTERNAL
                      (OUR code: stored/versioned/forked EXACTLY like a primitive, but SECRET — never returned
                      by a public search and never run for a public caller). Mirrors LineageBundle.scope's
                      "tenant_private never enters a global_public bundle" law.
  5. SYSTEM         — a named group of primitives = one of our GitHub repos ("every project is a group of
                      primitives + systems").
  6. CANDIDATE/TRUTH— every write is born candidate; promotion is a POINTER MOVE with a REQUIRED rollback
                      target (reuses the PromotionRecord discipline).
  7. MULTI-PATH     — one PrimitiveStorePort with a reference Local backend AND an Omnigraph adapter, chosen
                      by a selector and comparable in a bake-off (never hardwire one storage engine).
  8. GENERIC EXECUTOR — a stateless runner that, given (code_ref, inputs), fetches the code from the store,
                      checks scope + promotion state, runs it via a pluggable sandbox runner, validates I/O
                      against the primitive's contracts, and returns outputs + a receipt. One generic image;
                      the primitive (code) is fetched per-launch — the hosting plan's "place workloads, don't
                      rewrite them", taken to its endpoint.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Callable


# ---------------------------------------------------------------------------- enums + hashing
class Scope(str, Enum):
    PUBLIC = "public"        # externally available: appears in public search, runnable by any caller
    INTERNAL = "internal"    # OUR code: stored/versioned like a primitive, but secret — excluded from public search/use


class State(str, Enum):
    CANDIDATE = "candidate"      # born here; not served truth
    PROMOTED = "promoted"        # the active, served version (only these run in prod mode)
    SUPERSEDED = "superseded"    # a prior version; KEPT, never deleted
    REJECTED = "rejected"        # a losing variation; KEPT with lineage to the winner


def canonical_hash(body: bytes) -> str:
    """Content address. PRODUCTION: replace with src.teleon.experiments.ids.canonical_id (the single-source
    authority) — the '{prefix}-{sha256[:16]}' scheme. Kept local here so the reference impl runs standalone."""
    return "sha256:" + hashlib.sha256(body).hexdigest()[:16]


# ---------------------------------------------------------------------------- content plane (the bucket)
class ContentBucket:
    """Content-addressed blob store for primitive bodies/code. In-memory here; PRODUCTION is S3/R2/MinIO
    behind the credential-plane (env-name indirection), or Omnigraph's Lance object store."""
    def __init__(self) -> None:
        self._blobs: dict[str, bytes] = {}

    def put(self, body: bytes) -> str:
        ref = canonical_hash(body)
        self._blobs.setdefault(ref, body)     # same bytes -> same ref -> stored once (dedup)
        return ref

    def get(self, ref: str) -> bytes:
        if ref not in self._blobs:
            raise KeyError(f"content {ref} not in bucket")
        return self._blobs[ref]

    def __len__(self) -> int:
        return len(self._blobs)


# ---------------------------------------------------------------------------- lineage plane (the git-like DAG)
@dataclass
class PrimitiveVersion:
    version_id: str
    key: str                      # logical id; parallel versions of ONE primitive share a key
    system: str                   # the group/repo this primitive belongs to
    scope: Scope
    branch: str
    content_ref: str              # -> ContentBucket (the body/code); the hash join across all three planes
    name: str
    parents: list[str] = field(default_factory=list)   # derivation edges: fork/branch source(s)
    transform: str = ""           # how it was made ("edit", "merge", "fork", ...) — remix provenance
    prior_version_id: str | None = None                # supersede edge (KEPT, never overwritten)
    state: State = State.CANDIDATE
    owner: str = ""               # accountable owner (ties to AccountabilityBinding)
    input_contract: dict = field(default_factory=dict)
    output_contract: dict = field(default_factory=dict)
    runtime: str = "python"       # which generic runner materializes it

    def to_json(self) -> dict:
        d = asdict(self)
        d["scope"] = self.scope.value
        d["state"] = self.state.value
        return d


class LineageGraph:
    """The git-like DAG over primitive versions: branch, fork, merge, supersede + active-pointer per key."""
    def __init__(self) -> None:
        self.versions: dict[str, PrimitiveVersion] = {}
        self.heads: dict[tuple[str, str], str] = {}       # (system, branch) -> head version_id
        self.active: dict[str, str] = {}                  # key -> the promoted (served) version_id
        self._n = 0

    def _mint(self, key: str, branch: str) -> str:
        self._n += 1
        return f"v_{key}_{branch}_{self._n}"               # PRODUCTION: canonical_id over canonical bytes

    def commit(self, key, system, scope, branch, content_ref, name, *, parents=None, transform="edit",
               prior=None, owner="", input_contract=None, output_contract=None, runtime="python") -> PrimitiveVersion:
        vid = self._mint(key, branch)
        pv = PrimitiveVersion(vid, key, system, scope, branch, content_ref, name,
                              parents=list(parents or []), transform=transform, prior_version_id=prior,
                              owner=owner, input_contract=input_contract or {}, output_contract=output_contract or {},
                              runtime=runtime)
        self.versions[vid] = pv
        self.heads[(system, branch)] = vid
        return pv

    def head(self, system: str, branch: str) -> PrimitiveVersion | None:
        vid = self.heads.get((system, branch))
        return self.versions.get(vid) if vid else None

    def walk(self, version_id: str) -> list[str]:
        """All ancestors (the lineage) — every parent + prior version, transitively."""
        seen, stack = [], [version_id]
        while stack:
            vid = stack.pop()
            pv = self.versions.get(vid)
            if not pv:
                continue
            for p in pv.parents + ([pv.prior_version_id] if pv.prior_version_id else []):
                if p not in seen:
                    seen.append(p); stack.append(p)
        return seen


# ---------------------------------------------------------------------------- query plane (the index)
class Index:
    """A scope-tagged search projection. THE load-bearing rule lives in search(): a query only ever sees the
    scopes it is allowed, so a PUBLIC search can never surface an INTERNAL (secret) primitive."""
    def __init__(self) -> None:
        self._docs: dict[str, tuple[Scope, str]] = {}     # version_id -> (scope, searchable text)

    def add(self, version_id: str, scope: Scope, text: str) -> None:
        self._docs[version_id] = (scope, text.lower())

    def search(self, query: str, allowed_scopes: set[Scope]) -> list[str]:
        q = query.lower().split()
        hits = []
        for vid, (scope, text) in self._docs.items():
            if scope not in allowed_scopes:
                continue                                   # SECRET code is invisible to a public search
            if all(tok in text for tok in q):
                hits.append(vid)
        return sorted(hits)


# ---------------------------------------------------------------------------- the port (multi-path seam)
class PrimitiveStorePort:
    """The seam. A backend is contract-substitutable (Local reference, Omnigraph, ...); callers never bind to
    a storage engine. Add a backend = a new class + a selector entry, never a rewrite."""
    def put(self, *, key, system, scope, name, body, branch="main", owner="", input_contract=None,
            output_contract=None, runtime="python") -> PrimitiveVersion: raise NotImplementedError
    def get_body(self, version_id: str) -> bytes: raise NotImplementedError
    def fork(self, version_id: str, *, new_key: str, owner: str) -> PrimitiveVersion: raise NotImplementedError
    def branch(self, version_id: str, *, branch: str) -> PrimitiveVersion: raise NotImplementedError
    def supersede(self, version_id: str, *, body: bytes, name=None) -> PrimitiveVersion: raise NotImplementedError
    def merge(self, a_id: str, b_id: str, *, body: bytes, branch: str) -> PrimitiveVersion: raise NotImplementedError
    def promote(self, version_id: str, *, rollback_target: str) -> PrimitiveVersion: raise NotImplementedError
    def search(self, query: str, *, viewer_scope: Scope) -> list[PrimitiveVersion]: raise NotImplementedError
    def list_system(self, system: str) -> list[PrimitiveVersion]: raise NotImplementedError


def _visible_scopes(viewer: Scope) -> set[Scope]:
    """A PUBLIC caller sees only PUBLIC; an INTERNAL (authorized) caller sees both. The secret-code guarantee."""
    return {Scope.PUBLIC} if viewer == Scope.PUBLIC else {Scope.PUBLIC, Scope.INTERNAL}


class LocalPrimitiveStore(PrimitiveStorePort):
    """Reference backend = our rules, composed from the three planes. This is the bake-off baseline that the
    Omnigraph adapter must beat on measured receipts before we would adopt it for the moat layer."""
    def __init__(self) -> None:
        self.bucket = ContentBucket()
        self.lineage = LineageGraph()
        self.index = Index()

    def _index(self, pv: PrimitiveVersion) -> None:
        self.index.add(pv.version_id, pv.scope, f"{pv.name} {pv.key} {pv.system}")

    def put(self, *, key, system, scope, name, body, branch="main", owner="", input_contract=None,
            output_contract=None, runtime="python") -> PrimitiveVersion:
        ref = self.bucket.put(body)                        # content plane
        pv = self.lineage.commit(key, system, Scope(scope), branch, ref, name, transform="create",
                                 owner=owner, input_contract=input_contract, output_contract=output_contract,
                                 runtime=runtime)           # lineage plane — born CANDIDATE
        self._index(pv)                                    # query plane
        return pv

    def get_body(self, version_id: str) -> bytes:
        return self.bucket.get(self.lineage.versions[version_id].content_ref)

    def fork(self, version_id: str, *, new_key: str, owner: str) -> PrimitiveVersion:
        src = self.lineage.versions[version_id]            # a fork derives a NEW primitive (new key), lineage kept
        pv = self.lineage.commit(new_key, src.system, src.scope, "main", src.content_ref, f"{src.name} (fork)",
                                 parents=[version_id], transform="fork", owner=owner,
                                 input_contract=src.input_contract, output_contract=src.output_contract,
                                 runtime=src.runtime)
        self._index(pv); return pv

    def branch(self, version_id: str, *, branch: str) -> PrimitiveVersion:
        src = self.lineage.versions[version_id]            # a branch = a parallel version of the SAME key
        pv = self.lineage.commit(src.key, src.system, src.scope, branch, src.content_ref, src.name,
                                 parents=[version_id], transform="branch", owner=src.owner,
                                 input_contract=src.input_contract, output_contract=src.output_contract,
                                 runtime=src.runtime)
        self._index(pv); return pv

    def supersede(self, version_id: str, *, body: bytes, name=None) -> PrimitiveVersion:
        src = self.lineage.versions[version_id]
        ref = self.bucket.put(body)
        pv = self.lineage.commit(src.key, src.system, src.scope, src.branch, ref, name or src.name,
                                 parents=[version_id], transform="edit", prior=version_id, owner=src.owner,
                                 input_contract=src.input_contract, output_contract=src.output_contract,
                                 runtime=src.runtime)       # old version KEPT, not overwritten
        self._index(pv); return pv

    def merge(self, a_id: str, b_id: str, *, body: bytes, branch: str) -> PrimitiveVersion:
        a = self.lineage.versions[a_id]
        ref = self.bucket.put(body)
        pv = self.lineage.commit(a.key, a.system, a.scope, branch, ref, a.name, parents=[a_id, b_id],
                                 transform="merge", owner=a.owner, input_contract=a.input_contract,
                                 output_contract=a.output_contract, runtime=a.runtime)  # remix = two parents
        self._index(pv); return pv

    def promote(self, version_id: str, *, rollback_target: str) -> PrimitiveVersion:
        if not rollback_target:                            # PromotionRecord law: no rollback target => invalid
            raise ValueError("promotion requires a rollback_target (a promotion without one is not lossless)")
        pv = self.lineage.versions[version_id]
        prior = self.lineage.active.get(pv.key)
        if prior and prior in self.lineage.versions:
            self.lineage.versions[prior].state = State.SUPERSEDED   # prior KEPT, just no longer active
        pv.state = State.PROMOTED
        self.lineage.active[pv.key] = version_id
        return pv

    def search(self, query: str, *, viewer_scope: Scope) -> list[PrimitiveVersion]:
        return [self.lineage.versions[v] for v in self.index.search(query, _visible_scopes(viewer_scope))]

    def list_system(self, system: str) -> list[PrimitiveVersion]:
        return [pv for pv in self.lineage.versions.values() if pv.system == system]


class OmnigraphPrimitiveStore(PrimitiveStorePort):
    """CANDIDATE adapter: same port, backed by an Omnigraph instance (Lance/object-store git-branching graph).
    Maps put->upsert node, branch->`omnigraph branch create`, merge->`omnigraph branch merge`, search->vector
    ANN. Requires a running instance; without one every op raises with the exact call it WOULD make, so the
    bake-off harness can skip it cleanly instead of silently passing."""
    def __init__(self, base_url: str, token: str | None = None, client: Callable | None = None) -> None:
        self.base_url = base_url.rstrip("/"); self.token = token; self._client = client

    def _call(self, method: str, path: str, body: dict | None = None):
        if self._client is None:
            raise RuntimeError(f"Omnigraph instance required: would {method} {self.base_url}{path}")
        return self._client(method, f"{self.base_url}{path}", body)

    def put(self, **kw): return self._call("POST", "/v1/nodes", kw)
    def branch(self, version_id, *, branch): return self._call("POST", "/v1/branches", {"from": version_id, "name": branch})
    def merge(self, a_id, b_id, **kw): return self._call("POST", "/v1/branches/merge", {"a": a_id, "b": b_id, **kw})
    def search(self, query, *, viewer_scope):
        return self._call("POST", "/v1/search", {"q": query, "scopes": list(_visible_scopes(viewer_scope))})


# ---------------------------------------------------------------------------- the generic executor
@dataclass
class ExecReceipt:
    code_ref: str
    version_id: str
    scope: str
    state: str
    ok: bool
    detail: str = ""


class GenericExecutor:
    """One stateless runner for ALL primitives. Given (version_id, inputs) it: resolves the primitive, ENFORCES
    scope (a public caller cannot run internal/secret code) and promotion state (prod mode runs only PROMOTED),
    fetches the code from the bucket BY CONTENT REF (cacheable by hash), runs it via a pluggable sandbox runner,
    and returns outputs + a receipt. The runner is itself a port: the demo runner execs constrained Python for
    the self-test; PRODUCTION plugs in the real sandbox (gVisor/Firecracker + Cedar policy + credential-plane).
    This is the 'generic stateless function that captures I/O + where to download the code' made concrete."""
    def __init__(self, store: LocalPrimitiveStore, runner: Callable[[bytes, dict], dict] | None = None) -> None:
        self.store = store
        self.runner = runner or self._demo_runner
        self._code_cache: dict[str, bytes] = {}            # by content_ref — the generic-image cold-start mitigation

    @staticmethod
    def _demo_runner(code: bytes, inputs: dict) -> dict:
        """DEMO ONLY — a constrained exec so the reference impl is runnable. NOT for production; prod delegates
        to the shared sandbox. The primitive body defines `def run(inputs): -> outputs`."""
        ns: dict = {}
        exec(compile(code.decode(), "<primitive>", "exec"), {"__builtins__": {"len": len, "sum": sum, "range": range}}, ns)
        return ns["run"](inputs)

    def _fetch(self, pv: PrimitiveVersion) -> bytes:
        if pv.content_ref not in self._code_cache:         # fetch-by-ref, cached by content hash
            self._code_cache[pv.content_ref] = self.store.get_body(pv.version_id)
        return self._code_cache[pv.content_ref]

    def execute(self, version_id: str, inputs: dict, *, caller_scope: Scope, mode: str = "prod") -> tuple[dict | None, ExecReceipt]:
        pv = self.store.lineage.versions.get(version_id)
        if pv is None:
            return None, ExecReceipt("", version_id, "", "", False, "unknown primitive")
        if pv.scope not in _visible_scopes(caller_scope):  # SECRET code never runs for a public caller
            return None, ExecReceipt(pv.content_ref, version_id, pv.scope.value, pv.state.value, False,
                                     "scope denied: internal primitive not runnable by a public caller")
        if mode == "prod" and pv.state != State.PROMOTED:  # candidate/truth boundary: prod runs only promoted
            return None, ExecReceipt(pv.content_ref, version_id, pv.scope.value, pv.state.value, False,
                                     "not promoted: candidate primitives run only in dry-run mode")
        missing = [k for k in pv.input_contract if k not in inputs]   # typed input contract
        if missing:
            return None, ExecReceipt(pv.content_ref, version_id, pv.scope.value, pv.state.value, False,
                                     f"input contract unmet: missing {missing}")
        outputs = self.runner(self._fetch(pv), inputs)     # fetch code by ref -> run in the sandbox runner
        missing_out = [k for k in pv.output_contract if k not in (outputs or {})]
        ok = not missing_out
        return (outputs if ok else None), ExecReceipt(pv.content_ref, version_id, pv.scope.value, pv.state.value,
                                                      ok, "" if ok else f"output contract unmet: missing {missing_out}")


# ---------------------------------------------------------------------------- selector (multi-path resolver)
def select_primitive_store(backend: str = "local", **kw) -> PrimitiveStorePort:
    if backend == "local":
        return LocalPrimitiveStore()
    if backend == "omnigraph":
        return OmnigraphPrimitiveStore(kw.get("base_url", "http://localhost:8080"), kw.get("token"), kw.get("client"))
    raise ValueError(f"unknown primitive-store backend: {backend}")


# ---------------------------------------------------------------------------- proof
def self_test() -> int:
    checks: list[tuple[str, bool]] = []
    s = LocalPrimitiveStore()

    # a PUBLIC primitive: an adder, with typed I/O
    adder_src = b"def run(inputs):\n    return {'sum': inputs['a'] + inputs['b']}\n"
    p = s.put(key="adder", system="aidoneright-openhubforai", scope="public", name="two-number adder",
              body=adder_src, input_contract={"a": "int", "b": "int"}, output_contract={"sum": "int"})
    checks.append(("write is born candidate", p.state == State.CANDIDATE))
    checks.append(("body is content-addressed", p.content_ref.startswith("sha256:")))

    # content-addressing dedups identical bytes
    before = len(s.bucket)
    s.put(key="adder2", system="aidoneright-openhubforai", scope="public", name="dup", body=adder_src)
    checks.append(("identical bytes dedup in the bucket", len(s.bucket) == before))

    # branch = a parallel version of the SAME key
    b = s.branch(p.version_id, branch="experiment")
    checks.append(("branch is a parallel version of the same key", b.key == "adder" and b.branch == "experiment" and p.version_id in b.parents))

    # fork = a NEW primitive derived from a source (lineage kept)
    f = s.fork(p.version_id, new_key="adder-with-log", owner="team-core")
    checks.append(("fork derives a new key with parent lineage", f.key == "adder-with-log" and p.version_id in f.parents))

    # supersede = new version, prior KEPT (never overwritten)
    v2 = s.supersede(p.version_id, body=b"def run(inputs):\n    return {'sum': sum([inputs['a'], inputs['b']])}\n")
    checks.append(("supersede keeps the prior version", v2.prior_version_id == p.version_id and p.version_id in s.lineage.versions))

    # merge = remix (two parents)
    m = s.merge(b.version_id, f.version_id, body=adder_src, branch="main")
    checks.append(("merge records two parents (remix)", set(m.parents) == {b.version_id, f.version_id}))

    # promotion needs a rollback target; then it's the active served version
    try:
        s.promote(v2.version_id, rollback_target="")
        checks.append(("promotion without rollback target is rejected", False))
    except ValueError:
        checks.append(("promotion without rollback target is rejected", True))
    s.promote(v2.version_id, rollback_target=p.version_id)
    checks.append(("promoted version becomes the active pointer", s.lineage.active["adder"] == v2.version_id))

    # SCOPE: an INTERNAL (secret) primitive = our own code
    secret = s.put(key="deploy-key-rotator", system="aidoneright-infra", scope="internal",
                   name="internal deploy secret rotator", body=b"def run(i):\n    return {'ok': True}\n",
                   output_contract={"ok": "bool"})
    pub_hits = s.search("rotator", viewer_scope=Scope.PUBLIC)
    int_hits = s.search("rotator", viewer_scope=Scope.INTERNAL)
    checks.append(("internal code is INVISIBLE to a public search", secret.version_id not in [x.version_id for x in pub_hits]))
    checks.append(("internal code IS visible to an authorized internal search", secret.version_id in [x.version_id for x in int_hits]))

    # SYSTEM grouping = a repo's primitives
    checks.append(("a system lists its own primitives", any(x.key == "deploy-key-rotator" for x in s.list_system("aidoneright-infra"))))

    # GENERIC EXECUTOR: fetch code by ref + run + receipt
    ex = GenericExecutor(s)
    out, rc = ex.execute(v2.version_id, {"a": 2, "b": 3}, caller_scope=Scope.PUBLIC, mode="prod")
    checks.append(("executor runs a promoted primitive by ref and returns outputs", out == {"sum": 5} and rc.ok))
    # a candidate primitive does not run in prod mode
    _, rc2 = ex.execute(b.version_id, {"a": 1, "b": 1}, caller_scope=Scope.PUBLIC, mode="prod")
    checks.append(("executor refuses a non-promoted primitive in prod mode", not rc2.ok and "not promoted" in rc2.detail))
    # a public caller cannot run internal/secret code
    s.promote(secret.version_id, rollback_target=secret.version_id)
    _, rc3 = ex.execute(secret.version_id, {}, caller_scope=Scope.PUBLIC, mode="prod")
    checks.append(("executor denies internal/secret code to a public caller", not rc3.ok and "scope denied" in rc3.detail))
    # input contract enforced
    _, rc4 = ex.execute(v2.version_id, {"a": 1}, caller_scope=Scope.PUBLIC, mode="prod")
    checks.append(("executor enforces the input contract", not rc4.ok and "input contract" in rc4.detail))

    # multi-path: the selector yields both backends; omnigraph without an instance fails loudly (never silent)
    checks.append(("selector returns the local backend", isinstance(select_primitive_store("local"), LocalPrimitiveStore)))
    og = select_primitive_store("omnigraph", base_url="http://x")
    try:
        og.branch("v1", branch="b"); checks.append(("omnigraph without an instance raises, not silently passes", False))
    except RuntimeError as e:
        checks.append(("omnigraph without an instance raises, not silently passes", "instance required" in str(e)))

    failed = [n for n, ok in checks if not ok]
    if failed:
        print("FAIL - primitive_store:\n  " + "\n  ".join(failed)); return 1
    print(f"PASS - primitive_store: {len(checks)} checks — content-addressed bucket + git-like "
          "fork/branch/merge/supersede lineage + scope-gated search (secret code invisible to public) + "
          "candidate/promotion + the generic fetch-by-ref executor + the multi-path Omnigraph seam.")
    return 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="The primitive store: git-like, content-addressed, scoped + a generic executor.")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args(argv)
    if args.self_test:
        return self_test()
    print("usage: primitive_store.py --self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
