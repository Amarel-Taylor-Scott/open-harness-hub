"""src.teleon.storage.git_record_store — a GIT-BACKED record store with a BRANCH-PROMOTION model and a
pgvector MIRROR, behind the same ``RecordStore`` port as ``record_store.py``.

The insight: a record store's storage / versioning / lineage / promotion ARE git primitives, and a
candidate-vs-promoted lifecycle IS a candidate-branch-vs-main-branch flow. So back the store with a REAL
git repo and make the Promotion Boundary (CLAUDE.md) literal:

    raw layer (truth) ── records are CONTENT-ADDRESSED files (``records/<sha256>.json``); git holds
                         everything, forever, via branches. The candidate branch is the full raw layer.
    candidate branch  ── every append lands here first (load-ready, NOT yet operational/published).
    main branch       ── PROMOTION = merging/moving a candidate's file onto main. The operational,
                         publication-ready projection.

Promotion is LOSSLESS (the Lossless-Distillation law): it NEVER deletes the candidate — the winner's
file stays on the candidate branch, the losers stay on the candidate branch, and a ``lineage/<sha>.json``
on main records the winner→losers lineage. Omitted/rejected ≠ deleted; git history is the rollback target.

The pgvector MIRROR is the operational/searchable projection of the PROMOTED records (the operational
tier in ``storage_tier_policy.json``: "millions, indexed, pgvector"). It is HONEST-UNAVAILABLE: when
``psycopg``/``pgvector`` (or a DSN) are absent it falls back to a simple in-memory vector index so the
descent still runs — it NEVER fakes a DB or claims pgvector when it is really running in memory.

Identity is content-addressed (``sha256_hex`` over canonical bytes — single source: experiments.ids), so
a formatting change never forges a new identity and a re-append is an O(1) no-op. Deterministic + offline:
the self-test ``git init``s ONLY throwaway ``tempfile`` dirs, never the real repo. serves_truth=false (a
record is evidence, never a truth claim); Teleon-layer — never imports src.baltor.

    PYTHONPATH=. python3 src/teleon/storage/git_record_store.py --self-test
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

# Single-source helpers — never re-define these (No Magic Values, CLAUDE.md):
from scripts._config import pgvector_type  # noqa: E402  renders the vector(N) DDL — never a literal
from src.teleon.experiments.ids import canonical_bytes, sha256_hex  # noqa: E402  content-addressed identity
from src.teleon.registry.enrich import _EMBED_DIM as EMBED_DIM  # noqa: E402  deterministic-embed dim (single source)
from src.teleon.registry.enrich import embedding  # noqa: E402  deterministic lexical embedder (a learned one drops in)
from src.teleon.storage.record_store import RecordStore  # noqa: E402  the ONE port shape this implements

# -- repo layout + deterministic git identity (named; no magic values) ----------------------------
RECORDS_DIR = "records"                       # content-addressed record files live here
LINEAGE_DIR = "lineage"                       # winner→losers promotion lineage lives here (on main)
DEFAULT_MAIN_BRANCH = "main"                  # the promoted / operational branch
DEFAULT_CANDIDATE_BRANCH = "candidates"       # the raw / candidate branch (full truth layer)
_GIT_NAME = "teleon-record-store"             # deterministic commit identity (offline, reproducible)
_GIT_EMAIL = "record-store@teleon.local"
_DEFAULT_COMMIT_DATE = "2026-06-25T00:00:00 +0000"  # fixed → deterministic commits in the self-test
_PGVECTOR_DSN_ENV = "OH_PGVECTOR_DSN"         # env var holding the operational pgvector DSN (if any)


class GitStoreError(ValueError):
    """Raised on a git failure, an unknown candidate, or a malformed record."""


# =================================================================================================
# pgvector MIRROR — the operational/searchable projection (honest-unavailable → in-memory fallback)
# =================================================================================================
def _cosine(a: list[float], b: list[float]) -> float:
    num = sum(x * y for x, y in zip(a, b))
    da = sum(x * x for x in a) ** 0.5
    db = sum(y * y for y in b) ** 0.5
    return num / (da * db) if da and db else 0.0


def _vec_literal(vector) -> str:
    """pgvector accepts a text literal ``[a,b,c]`` for input — render it without the python adapter."""
    return "[" + ",".join(repr(float(x)) for x in vector) + "]"


def _parse_vec(literal) -> list[float]:
    if isinstance(literal, (list, tuple)):
        return [float(x) for x in literal]
    s = str(literal).strip().lstrip("[").rstrip("]")
    return [float(x) for x in s.split(",")] if s else []


class VectorMirror:
    """The mirror port: upsert a promoted record's embedding, similarity-search it, count, report status.
    serves_truth False — the mirror is a rebuildable projection, never a source of truth."""

    backend = "abstract"
    available = False

    def upsert(self, key: str, record: dict, vector: list[float]) -> None:
        raise NotImplementedError

    def search(self, vector: list[float], k: int = 5) -> list[tuple[str, float, dict]]:
        raise NotImplementedError

    def count(self) -> int:
        raise NotImplementedError

    def status(self) -> dict:
        raise NotImplementedError

    def close(self) -> None:
        pass


class InMemoryVectorMirror(VectorMirror):
    """The HONEST fallback when pgvector is unavailable: a simple in-memory cosine index so the descent
    still runs. It NEVER claims to be a DB — ``status()['faked_db']`` is always False and ``backend`` is
    ``in_memory`` — and it names WHY it fell back (``reason``)."""

    backend = "in_memory"
    available = True

    def __init__(self, *, dim: int = EMBED_DIM, reason: str = "") -> None:
        self.dim = dim
        self.reason = reason
        self._rows: dict[str, tuple[list[float], dict]] = {}

    def upsert(self, key: str, record: dict, vector: list[float]) -> None:
        if len(vector) != self.dim:
            raise GitStoreError(f"embedding dim {len(vector)} != mirror dim {self.dim}")
        self._rows[key] = ([float(x) for x in vector], dict(record))  # idempotent overwrite by key

    def search(self, vector: list[float], k: int = 5) -> list[tuple[str, float, dict]]:
        scored = [(key, _cosine(vector, vec), rec) for key, (vec, rec) in self._rows.items()]
        scored.sort(key=lambda t: (-t[1], t[0]))  # score desc, key asc → deterministic ties
        return scored[:k]

    def count(self) -> int:
        return len(self._rows)

    def status(self) -> dict:
        return {"backend": self.backend, "available": True, "faked_db": False,
                "reason": self.reason, "dim": self.dim, "rows": self.count(), "serves_truth": False}


class PgVectorMirror(VectorMirror):
    """The operational pgvector projection: a ``vector(dim)`` table with cosine/L2 nearest-neighbour
    search. The DB connection is injected (``connect``) so production uses real ``psycopg`` while the
    self-test injects an offline test double — the SQL path is identical and genuinely exercised. The
    DDL dim goes through ``pgvector_type`` so a dimension change can never leave a stale literal."""

    backend = "pgvector"
    available = True

    def __init__(self, dsn: str, *, dim: int = EMBED_DIM, connect, table: str = "teleon_record_mirror") -> None:
        self.dsn = dsn
        self.dim = dim
        self.table = table
        self._conn = connect(dsn)
        self._init_schema()

    def _exec(self, sql: str, params=(), *, fetch: bool = False):
        cur = self._conn.cursor()
        try:
            cur.execute(sql, params)
            return cur.fetchall() if fetch else None
        finally:
            cur.close()

    def _init_schema(self) -> None:
        col = pgvector_type(self.dim)  # e.g. vector(64) — single-sourced, never a literal
        self._exec("CREATE EXTENSION IF NOT EXISTS vector")
        self._exec(f"CREATE TABLE IF NOT EXISTS {self.table} ("
                   f"record_hash text PRIMARY KEY, record jsonb, embedding {col})")
        self._conn.commit()

    def upsert(self, key: str, record: dict, vector: list[float]) -> None:
        if len(vector) != self.dim:
            raise GitStoreError(f"embedding dim {len(vector)} != mirror dim {self.dim}")
        self._exec(
            f"INSERT INTO {self.table} (record_hash, record, embedding) VALUES (%s, %s, %s) "
            f"ON CONFLICT (record_hash) DO UPDATE SET record = EXCLUDED.record, embedding = EXCLUDED.embedding",
            (key, json.dumps(record, sort_keys=True), _vec_literal(vector)))
        self._conn.commit()

    def search(self, vector: list[float], k: int = 5) -> list[tuple[str, float, dict]]:
        rows = self._exec(
            f"SELECT record_hash, embedding, record FROM {self.table} ORDER BY embedding <-> %s LIMIT %s",
            (_vec_literal(vector), int(k)), fetch=True) or []
        out: list[tuple[str, float, dict]] = []
        for key, vec, rec in rows:
            v = _parse_vec(vec)
            r = rec if isinstance(rec, dict) else json.loads(rec)
            out.append((key, _cosine(vector, v), r))
        return out

    def count(self) -> int:
        rows = self._exec(f"SELECT count(*) FROM {self.table}", fetch=True) or [(0,)]
        return int(rows[0][0])

    def status(self) -> dict:
        return {"backend": self.backend, "available": True, "faked_db": False,
                "dsn_present": bool(self.dsn), "dim": self.dim, "table": self.table,
                "rows": self.count(), "serves_truth": False}

    def close(self) -> None:
        try:
            self._conn.close()
        except Exception:
            pass


def pgvector_availability() -> dict:
    """Probe whether the pgvector stack is importable — the HONEST signal that decides the mirror backend.
    Accepts ``psycopg`` (v3) or ``psycopg2`` as the driver; ``pgvector`` must also be importable."""
    driver = None
    for name in ("psycopg", "psycopg2"):
        try:
            __import__(name)
            driver = name
            break
        except Exception:
            continue
    try:
        __import__("pgvector")
        has_pgvector = True
    except Exception:
        has_pgvector = False
    missing = []
    if driver is None:
        missing.append("psycopg (or psycopg2)")
    if not has_pgvector:
        missing.append("pgvector")
    return {"available": not missing, "driver": driver, "pgvector": has_pgvector, "missing": missing}


def _real_connect(dsn: str):  # pragma: no cover - production-only; never called in the offline self-test
    try:
        import psycopg
        return psycopg.connect(dsn)
    except Exception:
        import psycopg2
        return psycopg2.connect(dsn)


def open_vector_mirror(dsn: str | None = None, *, dim: int = EMBED_DIM,
                       available: bool | None = None, connect=None) -> VectorMirror:
    """Open the operational mirror. Returns a real ``PgVectorMirror`` ONLY when a DSN is set AND the
    pgvector stack is available; otherwise an honest ``InMemoryVectorMirror`` that names why it fell back.
    Never fakes a DB. ``available``/``connect`` are injectable seams for the deterministic self-test."""
    probe = pgvector_availability()
    is_avail = probe["available"] if available is None else bool(available)
    if dsn and is_avail:
        try:
            return PgVectorMirror(dsn, dim=dim, connect=connect or _real_connect)
        except Exception as exc:  # honest fallback — a failed connect never silently fakes a DB
            return InMemoryVectorMirror(dim=dim, reason=f"pgvector connect failed: {exc}")
    if not dsn:
        reason = f"no pgvector DSN configured (set {_PGVECTOR_DSN_ENV})"
    else:
        reason = "psycopg/pgvector unavailable: " + (", ".join(probe["missing"]) or "forced-unavailable")
    return InMemoryVectorMirror(dim=dim, reason=reason)


# =================================================================================================
# GIT-BACKED record store with the BRANCH-PROMOTION model (implements the RecordStore port)
# =================================================================================================
class GitRecordStore(RecordStore):
    """Append-only, content-addressed record store backed by a REAL git repo with a candidate→main
    promotion model. ``append`` lands a record on the candidate branch (idempotent by content hash and by
    ``idem_key``); ``promote`` losslessly moves a candidate's file onto main and mirrors it; ``all``
    streams the raw candidate layer, ``promoted`` the operational layer. serves_truth False."""

    backend = "git_branch"

    def __init__(self, repo_path: str | Path, *, main_branch: str = DEFAULT_MAIN_BRANCH,
                 candidate_branch: str = DEFAULT_CANDIDATE_BRANCH, mirror: VectorMirror | None = None,
                 commit_date: str = _DEFAULT_COMMIT_DATE) -> None:
        self.repo = Path(repo_path)
        self.main_branch = main_branch
        self.candidate_branch = candidate_branch
        self.commit_date = commit_date
        self._env = {
            **os.environ,
            "GIT_AUTHOR_NAME": _GIT_NAME, "GIT_COMMITTER_NAME": _GIT_NAME,
            "GIT_AUTHOR_EMAIL": _GIT_EMAIL, "GIT_COMMITTER_EMAIL": _GIT_EMAIL,
            "GIT_AUTHOR_DATE": commit_date, "GIT_COMMITTER_DATE": commit_date,
            "GIT_TERMINAL_PROMPT": "0", "GIT_CONFIG_NOSYSTEM": "1",
        }
        self._ensure_repo()
        self._index_by_hash: dict[str, int] = {}   # record_hash -> seq (candidate layer)
        self._index_by_idem: dict[str, int] = {}    # idem_key   -> seq
        self._next_seq = 0
        self._rebuild_index()
        self.mirror = mirror if mirror is not None else open_vector_mirror(
            dsn=os.environ.get(_PGVECTOR_DSN_ENV), dim=EMBED_DIM)

    # -- git plumbing -----------------------------------------------------------------------------
    def _git(self, *args: str, check: bool = True) -> subprocess.CompletedProcess:
        cp = subprocess.run(["git", *args], cwd=str(self.repo), env=self._env,
                            capture_output=True, text=True)
        if check and cp.returncode != 0:
            raise GitStoreError(f"git {' '.join(args)} failed ({cp.returncode}): {cp.stderr.strip()}")
        return cp

    def _commit(self, message: str) -> None:
        self._git("-c", "commit.gpgsign=false", "commit", "-q", "-m", message)

    def _ensure_repo(self) -> None:
        if (self.repo / ".git").is_dir():
            self._ensure_branch(self.candidate_branch)
            return
        self.repo.mkdir(parents=True, exist_ok=True)
        self._git("-c", f"init.defaultBranch={self.main_branch}", "init", "-q", ".")
        self._git("-c", "commit.gpgsign=false", "commit", "-q", "--allow-empty", "-m", "init record store")
        self._git("branch", "-M", self.main_branch)      # normalize the first branch's name to main
        self._git("branch", self.candidate_branch)        # the raw / candidate branch
        self._git("checkout", "-q", self.candidate_branch)

    def _ensure_branch(self, branch: str) -> None:
        cur = self._git("rev-parse", "--abbrev-ref", "HEAD", check=False).stdout.strip()
        if cur == branch:
            return
        if self._git("checkout", "-q", branch, check=False).returncode != 0:
            self._git("checkout", "-q", "-b", branch, self.main_branch)

    def _current_branch(self) -> str:
        return self._git("rev-parse", "--abbrev-ref", "HEAD").stdout.strip()

    # -- side-effect-free reads (via ls-tree/show against a branch ref) ----------------------------
    def _envelopes_on(self, branch: str) -> list[dict]:
        cp = self._git("ls-tree", "-r", "--name-only", branch, "--", f"{RECORDS_DIR}/", check=False)
        if cp.returncode != 0:
            return []
        envs: list[dict] = []
        for path in cp.stdout.splitlines():
            path = path.strip()
            if not path:
                continue
            blob = self._git("show", f"{branch}:{path}", check=False)
            if blob.returncode != 0 or not blob.stdout:
                continue
            try:
                envs.append(json.loads(blob.stdout))
            except json.JSONDecodeError:
                continue
        envs.sort(key=lambda e: e.get("seq", 0))  # insertion order → deterministic streaming
        return envs

    def _record_for(self, record_hash: str, branch: str | None = None) -> dict:
        branch = branch or self.candidate_branch
        cp = self._git("show", f"{branch}:{RECORDS_DIR}/{record_hash}.json", check=False)
        if cp.returncode != 0:
            raise GitStoreError(f"record {record_hash!r} not on branch {branch!r}")
        return json.loads(cp.stdout)["record"]

    def _rebuild_index(self) -> None:
        for env in self._envelopes_on(self.candidate_branch):
            self._index_by_hash[env["record_hash"]] = env["seq"]
            if env.get("idem_key") is not None:
                self._index_by_idem[env["idem_key"]] = env["seq"]
            self._next_seq = max(self._next_seq, env["seq"] + 1)

    # -- RecordStore port -------------------------------------------------------------------------
    def append(self, record: dict, *, idem_key: str | None = None) -> int:
        """Append a record onto the candidate branch. Idempotent: an identical record (same content hash)
        OR a repeated ``idem_key`` is an O(1) no-op returning the existing seq — never a duplicate commit."""
        if not isinstance(record, dict):
            raise GitStoreError("record must be a dict")
        rec_hash = sha256_hex(record)
        if rec_hash in self._index_by_hash:
            return self._index_by_hash[rec_hash]
        if idem_key is not None and idem_key in self._index_by_idem:
            return self._index_by_idem[idem_key]
        self._ensure_branch(self.candidate_branch)
        seq = self._next_seq
        envelope = {"seq": seq, "record_hash": rec_hash, "idem_key": idem_key,
                    "record": record, "serves_truth": False}
        rel = f"{RECORDS_DIR}/{rec_hash}.json"
        path = self.repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(canonical_bytes(envelope))
        self._git("add", "--", rel)
        self._commit(f"append {rec_hash[:12]} seq={seq}")
        self._index_by_hash[rec_hash] = seq
        if idem_key is not None:
            self._index_by_idem[idem_key] = seq
        self._next_seq = seq + 1
        return seq

    def all(self, predicate=None) -> list[dict]:
        """The raw candidate layer (truth) — every appended record, promoted or not, winners and losers."""
        records = [e["record"] for e in self._envelopes_on(self.candidate_branch)]
        return [r for r in records if predicate(r)] if predicate else records

    def count(self) -> int:
        return len(self._index_by_hash)

    def close(self) -> None:
        self.mirror.close()

    # -- the BRANCH-PROMOTION model ---------------------------------------------------------------
    def promote(self, record_hash: str, *, losers: list[str] | None = None, now: str | None = None) -> dict:
        """PROMOTE a candidate: merge/move its content-addressed file onto the main branch and mirror it.

        Lossless — the candidate branch is NEVER touched: the winner's file stays, the losers' files stay,
        and a ``lineage/<hash>.json`` on main records the winner→losers lineage (a rollback/audit target).
        Idempotent: re-promoting the same record with the same lineage is a no-op (no duplicate commit)."""
        if record_hash not in self._index_by_hash:
            raise GitStoreError(f"cannot promote unknown candidate {record_hash!r}")
        losers = list(losers or [])
        rel = f"{RECORDS_DIR}/{record_hash}.json"
        lrel = f"{LINEAGE_DIR}/{record_hash}.json"
        prev = self._current_branch()
        try:
            self._git("checkout", "-q", self.main_branch)
            # merge/move just THIS candidate's file from the candidate branch onto main (candidate untouched)
            self._git("checkout", self.candidate_branch, "--", rel)
            lineage = {"winner": record_hash, "losers": losers, "promoted_from": self.candidate_branch,
                       "promoted_at": now or self.commit_date, "serves_truth": False}
            lpath = self.repo / lrel
            lpath.parent.mkdir(parents=True, exist_ok=True)
            lpath.write_bytes(canonical_bytes(lineage))
            self._git("add", "--", rel, lrel)
            if self._git("status", "--porcelain").stdout.strip():  # idempotent: skip if nothing changed
                self._commit(f"promote {record_hash[:12]} (losers={len(losers)})")
        finally:
            self._git("checkout", "-q", prev, check=False)
        record = self._record_for(record_hash)
        self.mirror.upsert(record_hash, record, embedding(record))  # mirror the operational projection
        return {"promoted": True, "record_hash": record_hash, "branch": self.main_branch,
                "losers": losers, "mirror_backend": self.mirror.backend, "serves_truth": False}

    def promoted(self, predicate=None) -> list[dict]:
        """The operational (main-branch) projection — only the records that have been promoted."""
        records = [e["record"] for e in self._envelopes_on(self.main_branch)]
        return [r for r in records if predicate(r)] if predicate else records

    def lineage(self, record_hash: str) -> dict:
        """The promotion lineage for a record (winner + the losers it was promoted over). ``{}`` if absent."""
        cp = self._git("show", f"{self.main_branch}:{LINEAGE_DIR}/{record_hash}.json", check=False)
        return json.loads(cp.stdout) if cp.returncode == 0 and cp.stdout else {}

    def record_hashes(self) -> set[str]:
        """The content hashes of every candidate-layer record (the stable, content-addressed identities)."""
        return set(self._index_by_hash)

    def search(self, query: dict | list[float], k: int = 5) -> list[tuple[str, float, dict]]:
        """Similarity-search the operational mirror. ``query`` may be a record (embedded deterministically)
        or a raw embedding vector."""
        vector = query if isinstance(query, list) else embedding(query)
        return self.mirror.search(vector, k=k)


# =================================================================================================
# self-test — deterministic + OFFLINE; git init ONLY in throwaway tempfile dirs, never the real repo
# =================================================================================================
class _FakePgConnection:
    """A minimal DB-API test double used ONLY by ``self_test`` to exercise the real ``PgVectorMirror`` SQL
    path offline. It is explicitly injected by the test — it is NEVER a production fallback (production
    uses real ``psycopg``; the honest fallback is ``InMemoryVectorMirror``)."""

    def __init__(self) -> None:
        self._store: dict[str, tuple[list[float], str]] = {}
        self.executed: list[str] = []

    def cursor(self):
        return _FakePgCursor(self)

    def commit(self) -> None:
        pass

    def close(self) -> None:
        pass


class _FakePgCursor:
    def __init__(self, conn: _FakePgConnection) -> None:
        self.conn = conn
        self._result: list[tuple] = []

    def execute(self, sql: str, params=()):
        self.conn.executed.append(sql)
        head = sql.strip().upper()
        if head.startswith("INSERT"):
            key, rec_json, vec_lit = params
            self.conn._store[key] = (_parse_vec(vec_lit), rec_json)
        elif head.startswith("SELECT COUNT"):
            self._result = [(len(self.conn._store),)]
        elif head.startswith("SELECT"):
            vec_lit, k = params
            query = _parse_vec(vec_lit)
            ranked = sorted(self.conn._store.items(), key=lambda kv: (-_cosine(query, kv[1][0]), kv[0]))
            self._result = [(key, vec, rec_json) for key, (vec, rec_json) in ranked[:int(k)]]
        # CREATE EXTENSION / CREATE TABLE → no-op (DDL string still recorded for assertion)

    def fetchall(self):
        return list(self._result)

    def close(self) -> None:
        pass


def self_test() -> int:
    root = Path(tempfile.mkdtemp(prefix="git_record_store_"))
    repo = root / "store"
    store = GitRecordStore(repo)  # git init in a throwaway temp dir — never the real repo
    assert (repo / ".git").is_dir(), "store must be a REAL git repo"

    # 1) content-addressed append + idempotency (by content hash AND by idem_key) ------------------
    r_alpha = {"name": "alpha extraction", "kind": "ocr"}
    r_beta = {"name": "beta rerank", "kind": "rerank"}
    s_alpha = store.append(r_alpha)
    assert store.append(dict(r_alpha)) == s_alpha, "identical content must be an O(1) idempotent no-op"
    s_beta = store.append(r_beta)
    assert s_beta != s_alpha
    s_key = store.append({"name": "gamma"}, idem_key="K1")
    assert store.append({"name": "gamma-DIFFERENT"}, idem_key="K1") == s_key, "same idem_key must dedupe"
    assert store.count() == 3, f"expected 3 candidates, got {store.count()}"
    assert sorted(r["name"] for r in store.all()) == ["alpha extraction", "beta rerank", "gamma"]
    h_alpha, h_beta = sha256_hex(r_alpha), sha256_hex(r_beta)
    assert h_alpha in store.record_hashes(), "record stored under its content hash"

    # 2) PROMOTION model — lossless branch move + lineage to losers --------------------------------
    promo = store.promote(h_alpha, losers=[h_beta])
    assert promo["promoted"] and promo["branch"] == store.main_branch
    assert [r["name"] for r in store.promoted()] == ["alpha extraction"], "only the winner is on main"
    # lossless: the candidate branch STILL holds the winner AND the loser (nothing deleted)
    assert sorted(r["name"] for r in store.all()) == ["alpha extraction", "beta rerank", "gamma"]
    lin = store.lineage(h_alpha)
    assert lin["winner"] == h_alpha and lin["losers"] == [h_beta], "lineage to losers is preserved"
    store.promote(h_alpha, losers=[h_beta])  # re-promote is an idempotent no-op (no delete, no error)
    assert [r["name"] for r in store.promoted()] == ["alpha extraction"]

    # 3) pgvector MIRROR — honest-unavailable fallback to in-memory --------------------------------
    avail = pgvector_availability()
    mirror = store.mirror  # in-memory here (pgvector absent / no DSN)
    assert mirror.backend == "in_memory" and mirror.available
    assert mirror.status()["faked_db"] is False, "the fallback must NEVER claim to be a DB"
    hits = store.search(r_alpha, k=1)  # the promoted record is searchable in the mirror
    assert hits and hits[0][0] == h_alpha, "promoted record must be mirrored + searchable"
    unavail = open_vector_mirror(dsn="postgresql://example/none", available=False)
    assert unavail.backend == "in_memory" and unavail.status()["faked_db"] is False
    assert "unavailable" in unavail.status()["reason"], "fallback must name what is missing (honest)"

    # 4) pgvector path is REAL — exercise PgVectorMirror via an injected offline test double --------
    fake = _FakePgConnection()
    pg = open_vector_mirror(dsn="postgresql://example/db", available=True, connect=lambda _dsn: fake)
    assert pg.backend == "pgvector" and pg.available
    pg.upsert(h_alpha, r_alpha, embedding(r_alpha))
    pg.upsert(h_beta, r_beta, embedding(r_beta))
    assert pg.count() == 2
    assert any(pgvector_type(EMBED_DIM) in sql for sql in fake.executed), "DDL must use pgvector_type (no literal dim)"
    pg_hits = pg.search(embedding(r_alpha), k=1)
    assert pg_hits and pg_hits[0][0] == h_alpha, "pgvector SQL search path must return the nearest record"
    pg.close()

    # 5) reopening the same repo recovers state (git is the durable store) -------------------------
    store.close()
    reopened = GitRecordStore(repo)
    assert reopened.count() == 3 and reopened.record_hashes() == store.record_hashes()
    assert [r["name"] for r in reopened.promoted()] == ["alpha extraction"]
    reopened.close()

    print("git_record_store self-test: OK — git-backed branch-promotion store · content-addressed · "
          f"lossless promotion+lineage · pgvector mirror honest-unavailable→in_memory "
          f"(pgvector_available={avail['available']}) · serves_truth=false")
    return 0


def main(argv: list[str]) -> int:
    if "--self-test" in argv:
        return self_test()
    print("usage: git_record_store --self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
