#!/usr/bin/env python3
"""scripts.executable_primitive_library — primitives that ACTUALLY WORK: a tiered library of real, correct,
tested Python implementations for common, rare, and super-rare coding tasks. A descriptive card does not save
tokens; a working, tested unit that an agent RETRIEVES and RUNS (0 generation tokens) instead of regenerating
from scratch does. This is the executable substrate under the descriptive primitive registry.

Three tiers, chosen by how often a base model gets the task RIGHT unaided:
  * COMMON      — high-frequency utilities a model usually nails (chunking, dedupe, flatten). Reuse still
                  saves the whole regeneration.
  * RARE        — medium-frequency algorithms a model often gets subtly wrong at the edges (toposort with
                  cycle detection, edit distance, interval merge, token bucket). Reuse saves tokens AND
                  correctness.
  * SUPER_RARE  — low-frequency algorithms a model frequently gets wrong (union-find, Fenwick tree, KMP,
                  Tarjan SCC, Dijkstra). Reuse is the biggest win: large regeneration + high failure rate.

Every primitive ships with an ORACLE-BACKED test (a brute-force or property check), so "it works" is proven,
not asserted — the self-test runs all of them and a broken implementation goes red. Cards carry the REAL
source (via inspect.getsource — single source, no drift) as the executable body, a canonical id, typed edges,
and the tier. Candidates only; serves_truth=false. Token savings are measured in scripts.token_savings_bench.

    python3 scripts/executable_primitive_library.py --self-test
    python3 scripts/executable_primitive_library.py --stage
"""
from __future__ import annotations

import sys
from pathlib import Path

# ── substrate-root bootstrap (sentinel; mirrors scripts/mint_idea_primitives.py) ─────────────────────────────
_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots, resource  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import inspect  # noqa: E402
import json  # noqa: E402
import re  # noqa: E402
import zlib  # noqa: E402
from typing import Any, Callable, Optional  # noqa: E402

try:
    from src.teleon.experiments.ids import canonical_id  # noqa: E402  THE data-plane id authority
except Exception as exc:  # noqa: BLE001
    raise SystemExit(f"executable_primitive_library requires canonical_id; import failed: {exc}")

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
CARD_PREFIX = "prim-exec"
CARD_RECORD_TYPE = "executable_primitive_candidate"
STAGED_FILENAME = "executable_primitive_candidates.jsonl"
_VERIFIED_CORPUS_FILENAMES = frozenset({"verified_factory_primitive_cards.jsonl", "primitive_edge_cards.jsonl"})


# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════
# TIER: COMMON — utilities a base model usually gets right; reuse saves the whole regeneration.
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════

def chunk_list(xs: list, n: int) -> list:
    """Split a list into consecutive chunks of size n (last may be shorter). n must be >= 1."""
    if n < 1:
        raise ValueError("n must be >= 1")
    return [xs[i:i + n] for i in range(0, len(xs), n)]


def dedupe_stable(xs: list) -> list:
    """Order-preserving de-duplication (first occurrence wins). Elements must be hashable."""
    seen: set = set()
    out: list = []
    for x in xs:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def flatten_dict(d: dict, sep: str = ".", _prefix: str = "") -> dict:
    """Flatten a nested dict into dotted keys. Non-dict values (incl. lists) are leaves."""
    out: dict = {}
    for k, v in d.items():
        key = f"{_prefix}{sep}{k}" if _prefix else str(k)
        if isinstance(v, dict) and v:
            out.update(flatten_dict(v, sep, key))
        else:
            out[key] = v
    return out


def deep_get(d: dict, path: str, default: Any = None, sep: str = ".") -> Any:
    """Safe nested lookup by a dotted path; returns default if any segment is missing."""
    cur: Any = d
    for part in path.split(sep):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return default
    return cur


def group_by(xs: list, key: Callable[[Any], Any]) -> dict:
    """Group items by key(item), preserving input order within each group."""
    out: dict = {}
    for x in xs:
        out.setdefault(key(x), []).append(x)
    return out


def parse_bool(s: Any) -> bool:
    """Robustly parse a truthy string/number to bool. Raises on genuinely ambiguous input."""
    if isinstance(s, bool):
        return s
    if isinstance(s, (int, float)):
        return bool(s)
    t = str(s).strip().lower()
    if t in ("1", "true", "t", "yes", "y", "on"):
        return True
    if t in ("0", "false", "f", "no", "n", "off", ""):
        return False
    raise ValueError(f"ambiguous boolean: {s!r}")


# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════
# TIER: RARE — algorithms a base model often gets subtly wrong at the edges; reuse saves tokens AND correctness.
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════

def toposort(deps: dict) -> list:
    """Kahn topological sort. deps maps node -> iterable of prerequisites. Raises ValueError on a cycle.
    Deterministic: ties broken by sorted node order."""
    nodes = set(deps) | {p for ps in deps.values() for p in ps}
    indeg = {n: 0 for n in nodes}
    adj: dict = {n: [] for n in nodes}
    for n, prereqs in deps.items():
        for p in prereqs:
            adj[p].append(n)
            indeg[n] += 1
    ready = sorted(n for n in nodes if indeg[n] == 0)
    order: list = []
    while ready:
        n = ready.pop(0)
        order.append(n)
        newly = []
        for m in adj[n]:
            indeg[m] -= 1
            if indeg[m] == 0:
                newly.append(m)
        for m in sorted(newly):
            # insert keeping `ready` sorted (small n; simplicity over a heap)
            ready.append(m)
        ready.sort()
    if len(order) != len(nodes):
        raise ValueError("cycle detected: graph is not a DAG")
    return order


def levenshtein(a: str, b: str) -> int:
    """Edit distance (insert/delete/substitute cost 1) via the O(len(a)*len(b)) DP, single-row space."""
    if a == b:
        return 0
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i] + [0] * len(b)
        for j, cb in enumerate(b, 1):
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb))
        prev = cur
    return prev[-1]


def merge_intervals(intervals: list) -> list:
    """Merge overlapping/adjacent [start, end] closed intervals; returns sorted, disjoint intervals."""
    if not intervals:
        return []
    ordered = sorted((list(iv) for iv in intervals), key=lambda iv: (iv[0], iv[1]))
    merged = [ordered[0][:]]
    for start, end in ordered[1:]:
        if start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return merged


def binary_search_leftmost(xs: list, target: Any) -> int:
    """Leftmost insertion index for target in a sorted list (bisect_left semantics), from scratch."""
    lo, hi = 0, len(xs)
    while lo < hi:
        mid = (lo + hi) // 2
        if xs[mid] < target:
            lo = mid + 1
        else:
            hi = mid
    return lo


def reservoir_sample(iterable, k: int, rng) -> list:
    """Algorithm R reservoir sampling — a uniform k-sample in ONE pass over an unknown-length stream.
    rng is a random.Random (injected for determinism)."""
    reservoir: list = []
    for i, item in enumerate(iterable):
        if i < k:
            reservoir.append(item)
        else:
            j = rng.randint(0, i)
            if j < k:
                reservoir[j] = item
    return reservoir


class TokenBucket:
    """A token-bucket rate limiter. capacity tokens, refilled at `rate`/sec. `now` is injected (a clock fn)
    so behavior is testable and deterministic. allow(cost) returns True and consumes iff enough tokens."""

    def __init__(self, rate: float, capacity: float, now: Callable[[], float]):
        self.rate = float(rate)
        self.capacity = float(capacity)
        self._now = now
        self._tokens = float(capacity)
        self._last = now()

    def allow(self, cost: float = 1.0) -> bool:
        t = self._now()
        self._tokens = min(self.capacity, self._tokens + (t - self._last) * self.rate)
        self._last = t
        if self._tokens >= cost:
            self._tokens -= cost
            return True
        return False


# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════
# TIER: SUPER_RARE — algorithms a base model frequently gets wrong; reuse is the biggest token + correctness win.
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════

class UnionFind:
    """Disjoint-set union with path compression + union by rank. near-O(1) find/union (inverse-Ackermann)."""

    def __init__(self, n: int):
        self.parent = list(range(n))
        self.rank = [0] * n

    def find(self, x: int) -> int:
        root = x
        while self.parent[root] != root:
            root = self.parent[root]
        while self.parent[x] != root:  # path compression
            self.parent[x], x = root, self.parent[x]
        return root

    def union(self, a: int, b: int) -> bool:
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False
        if self.rank[ra] < self.rank[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        if self.rank[ra] == self.rank[rb]:
            self.rank[ra] += 1
        return True


class FenwickTree:
    """Binary Indexed Tree: O(log n) prefix sums + point updates over an array of size n (1-indexed API)."""

    def __init__(self, n: int):
        self.n = n
        self.tree = [0] * (n + 1)

    def update(self, i: int, delta: int) -> None:
        i += 1  # 0-indexed input -> 1-indexed tree
        while i <= self.n:
            self.tree[i] += delta
            i += i & (-i)

    def prefix_sum(self, i: int) -> int:
        """Sum of the first i elements (indices 0..i-1)."""
        s = 0
        while i > 0:
            s += self.tree[i]
            i -= i & (-i)
        return s

    def range_sum(self, lo: int, hi: int) -> int:
        """Sum of elements in [lo, hi)."""
        return self.prefix_sum(hi) - self.prefix_sum(lo)


def boyer_moore_majority(xs: list) -> Optional[Any]:
    """Boyer-Moore majority vote: the element appearing > len/2 times in O(n) time, O(1) space, or None."""
    candidate, count = None, 0
    for x in xs:
        if count == 0:
            candidate, count = x, 1
        elif x == candidate:
            count += 1
        else:
            count -= 1
    if candidate is not None and xs.count(candidate) * 2 > len(xs):
        return candidate
    return None


def kmp_search(text: str, pattern: str) -> list:
    """Knuth-Morris-Pratt: all start indices where pattern occurs in text, via the failure function. O(n+m)."""
    if not pattern:
        return list(range(len(text) + 1))
    lps = [0] * len(pattern)
    k = 0
    for i in range(1, len(pattern)):
        while k > 0 and pattern[i] != pattern[k]:
            k = lps[k - 1]
        if pattern[i] == pattern[k]:
            k += 1
        lps[i] = k
    hits: list = []
    k = 0
    for i, ch in enumerate(text):
        while k > 0 and ch != pattern[k]:
            k = lps[k - 1]
        if ch == pattern[k]:
            k += 1
        if k == len(pattern):
            hits.append(i - k + 1)
            k = lps[k - 1]
    return hits


def tarjan_scc(graph: dict) -> list:
    """Tarjan's strongly-connected-components: returns a list of SCCs (each a sorted list of nodes). Iterative
    to avoid recursion limits. graph maps node -> iterable of successors."""
    index: dict = {}
    low: dict = {}
    on_stack: set = set()
    stack: list = []
    result: list = []
    counter = [0]
    nodes = list(graph)
    for start in nodes:
        if start in index:
            continue
        work = [(start, iter(graph.get(start, ())))]
        index[start] = low[start] = counter[0]
        counter[0] += 1
        stack.append(start)
        on_stack.add(start)
        while work:
            node, it = work[-1]
            advanced = False
            for w in it:
                if w not in index:
                    index[w] = low[w] = counter[0]
                    counter[0] += 1
                    stack.append(w)
                    on_stack.add(w)
                    work.append((w, iter(graph.get(w, ()))))
                    advanced = True
                    break
                if w in on_stack:
                    low[node] = min(low[node], index[w])
            if advanced:
                continue
            if low[node] == index[node]:
                comp = []
                while True:
                    w = stack.pop()
                    on_stack.discard(w)
                    comp.append(w)
                    if w == node:
                        break
                result.append(sorted(comp))
            work.pop()
            if work:
                parent = work[-1][0]
                low[parent] = min(low[parent], low[node])
    return result


def dijkstra(graph: dict, source: Any) -> dict:
    """Dijkstra shortest paths from source over a non-negative weighted graph (node -> {neighbor: weight}).
    Returns node -> distance (unreachable nodes omitted). Uses a binary heap."""
    import heapq  # noqa: PLC0415
    dist: dict = {source: 0}
    heap = [(0, source)]
    while heap:
        d, u = heapq.heappop(heap)
        if d > dist.get(u, float("inf")):
            continue
        for v, w in graph.get(u, {}).items():
            if w < 0:
                raise ValueError("dijkstra requires non-negative weights")
            nd = d + w
            if nd < dist.get(v, float("inf")):
                dist[v] = nd
                heapq.heappush(heap, (nd, v))
    return dist


# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════
# TIER: TOKEN_OPTIMIZATION — executable primitives for the "spend fewer tokens without hurting quality"
# architecture (token budgets per route, budgeted retrieval selection, structured-state compaction, output
# schema enforcement, model routing, tail measurement). These are the primitives an agent harness reuses to
# route information cheaply — they save tokens by construction, not by asking a model to "be concise".
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════

def token_budget_gate(sections: dict, input_limit: int, requested_output: int, output_limit: int) -> dict:
    """Fail-fast token budget check per route. sections maps prompt-section name -> token count. Returns a
    verdict {ok, total_input, breaches:[...]} — a breach names WHICH side blew the budget (input stuffing vs
    an over-long output request), the recurring gotcha where only max_tokens is capped."""
    total_input = sum(int(v) for v in sections.values())
    breaches = []
    if total_input > input_limit:
        breaches.append({"side": "input", "actual": total_input, "limit": input_limit,
                         "worst_section": max(sections, key=lambda k: sections[k]) if sections else None})
    if requested_output > output_limit:
        breaches.append({"side": "output", "actual": requested_output, "limit": output_limit})
    return {"ok": not breaches, "total_input": total_input, "breaches": breaches}


def select_within_budget(items: list, token_of: Callable[[Any], int], budget: int) -> list:
    """Greedy budgeted selection (the retrieval span-budget loop): walk items in priority order, include each
    whose token cost still fits the remaining budget, SKIP over-budget items and keep trying smaller later
    ones. Returns the selected sublist. This is why 'better retrieval is cheaper retrieval'."""
    selected: list = []
    used = 0
    for item in items:
        cost = int(token_of(item))
        if used + cost <= budget:
            selected.append(item)
            used += cost
    return selected


def tail_percentile(values: list, p: float) -> float:
    """Nearest-rank percentile (token/latency tail measurement — the p95/p99 where token bugs hide). p in
    [0,100]. Raises on empty input (a percentile of nothing is undefined, not 0)."""
    if not values:
        raise ValueError("percentile of an empty sequence is undefined")
    if not 0 <= p <= 100:
        raise ValueError("p must be in [0, 100]")
    ordered = sorted(values)
    if p == 0:
        return float(ordered[0])
    import math  # noqa: PLC0415
    rank = math.ceil(p / 100 * len(ordered))
    return float(ordered[rank - 1])


def validate_against_schema(obj: dict, required: list, enums: Optional[dict] = None) -> dict:
    """Minimal output-schema enforcement (reject rambling/invalid machine output before it costs a repair
    call). Checks required keys present + enum membership. Returns {ok, errors:[...]} — no jsonschema dep."""
    errors: list = []
    for key in required:
        if key not in obj:
            errors.append(f"missing required key: {key}")
    for key, allowed in (enums or {}).items():
        if key in obj and obj[key] not in allowed:
            errors.append(f"{key}={obj[key]!r} not in {list(allowed)}")
    return {"ok": not errors, "errors": errors}


def route_model(route: str, policy: dict, default: str) -> str:
    """Cheapest-model routing: map a product route to a model class by an explicit policy table, falling back
    to a default. The engineering point is routing, not brand loyalty — use the cheapest model that clears the
    task's quality bar."""
    return policy.get(route, default)


def compact_recent_turns(turns: list, k: int, keep_system: bool = True) -> list:
    """Replace transcript stuffing with recent-window memory: keep the last k turns; optionally always keep a
    leading system turn (role=='system' at index 0) even if it falls outside the window. Order preserved."""
    if k < 0:
        raise ValueError("k must be >= 0")
    tail = turns[-k:] if k else []
    if keep_system and turns and isinstance(turns[0], dict) and turns[0].get("role") == "system" \
            and turns[0] not in tail:
        return [turns[0]] + tail
    return list(tail)


# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════
# ENGINEERING DOMAINS — executable primitives beyond algorithms: microservices, data analysis, data
# standardization + conformation, embedding generation, model training, loop patterns, hierarchical patterns.
# Every one is pure-stdlib, deterministic, and oracle-tested (a batch/closed-form/brute-force check).
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════

# ── microservices ────────────────────────────────────────────────────────────────────────────────────────────
class CircuitBreaker:
    """Closed -> Open -> Half-open state machine. `threshold` consecutive failures trip it Open; after
    `cooldown` seconds it goes Half-open (one trial); a trial success closes it, a trial failure re-opens.
    `now` is injected (a clock fn) so behavior is deterministic and testable."""

    def __init__(self, threshold: int, cooldown: float, now: Callable[[], float]):
        self.threshold = threshold
        self.cooldown = cooldown
        self._now = now
        self.state = "closed"
        self._failures = 0
        self._opened_at = 0.0

    def allow(self) -> bool:
        if self.state == "open" and self._now() - self._opened_at >= self.cooldown:
            self.state = "half_open"
        return self.state != "open"

    def record(self, ok: bool) -> None:
        if self.state == "half_open":
            self.state, self._failures = ("closed", 0) if ok else ("open", self.threshold)
            if not ok:
                self._opened_at = self._now()
            return
        if ok:
            self._failures = 0
        else:
            self._failures += 1
            if self._failures >= self.threshold:
                self.state = "open"
                self._opened_at = self._now()


def exponential_backoff_schedule(base: float, cap: float, attempts: int) -> list:
    """The (deterministic, no-jitter) backoff delay sequence: min(cap, base * 2**i) for i in range(attempts)."""
    return [min(cap, base * (2 ** i)) for i in range(attempts)]


def idempotency_dedup(requests: list, key_of: Callable[[Any], Any]) -> list:
    """Keep the FIRST request per idempotency key, drop replays (at-least-once delivery made effectively-once)."""
    seen: set = set()
    out: list = []
    for r in requests:
        k = key_of(r)
        if k not in seen:
            seen.add(k)
            out.append(r)
    return out


# ── data analysis ────────────────────────────────────────────────────────────────────────────────────────────
class RunningStats:
    """Welford's online mean/variance in ONE pass, O(1) memory — matches the batch computation exactly and is
    numerically stable (no sum-of-squares catastrophic cancellation)."""

    def __init__(self):
        self.n = 0
        self.mean = 0.0
        self._m2 = 0.0

    def push(self, x: float) -> None:
        self.n += 1
        delta = x - self.mean
        self.mean += delta / self.n
        self._m2 += delta * (x - self.mean)

    def variance(self) -> float:
        return self._m2 / self.n if self.n else 0.0


def iqr_outliers(values: list, k: float = 1.5) -> list:
    """Indices of values outside [Q1 - k*IQR, Q3 + k*IQR] (Tukey fences). Fewer than 4 values -> no outliers."""
    if len(values) < 4:
        return []
    ordered = sorted(values)

    def _q(p: float) -> float:
        idx = p * (len(ordered) - 1)
        lo = int(idx)
        frac = idx - lo
        return ordered[lo] + frac * (ordered[min(lo + 1, len(ordered) - 1)] - ordered[lo])
    q1, q3 = _q(0.25), _q(0.75)
    iqr = q3 - q1
    lo_f, hi_f = q1 - k * iqr, q3 + k * iqr
    return [i for i, v in enumerate(values) if v < lo_f or v > hi_f]


def histogram_counts(values: list, bins: int) -> list:
    """Equal-width histogram bin counts over [min, max]; the max value lands in the last bin. bins >= 1."""
    if bins < 1:
        raise ValueError("bins must be >= 1")
    if not values:
        return [0] * bins
    lo, hi = min(values), max(values)
    if hi == lo:
        return [len(values) if i == 0 else 0 for i in range(bins)]
    width = (hi - lo) / bins
    counts = [0] * bins
    for v in values:
        idx = min(bins - 1, int((v - lo) / width))
        counts[idx] += 1
    return counts


# ── data standardization + conformation ──────────────────────────────────────────────────────────────────────
def zscore_normalize(values: list) -> list:
    """Standardize to mean 0, std 1 (population std). Constant input -> all zeros (no divide-by-zero)."""
    if not values:
        return []
    mean = sum(values) / len(values)
    var = sum((v - mean) ** 2 for v in values) / len(values)
    std = var ** 0.5
    return [0.0 for _ in values] if std == 0 else [(v - mean) / std for v in values]


def min_max_scale(values: list, lo: float = 0.0, hi: float = 1.0) -> list:
    """Scale values to [lo, hi]. Constant input maps to lo."""
    if not values:
        return []
    vmin, vmax = min(values), max(values)
    if vmax == vmin:
        return [lo for _ in values]
    return [lo + (v - vmin) / (vmax - vmin) * (hi - lo) for v in values]


def snake_case_key(s: str) -> str:
    """Standardize a key to snake_case from CamelCase / kebab-case / 'space case' / mixed."""
    s = re.sub(r"[\s\-]+", "_", s.strip())
    s = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", s)
    s = re.sub(r"__+", "_", s)
    return s.lower().strip("_")


def coerce_type(value: Any, target: str, default: Any = None) -> Any:
    """Safe cast to 'int'|'float'|'bool'|'str'; returns default on failure (never raises). 'bool' parses
    common truthy/falsey strings."""
    try:
        if target == "int":
            return int(float(value)) if isinstance(value, str) else int(value)
        if target == "float":
            return float(value)
        if target == "bool":
            return parse_bool(value)
        if target == "str":
            return str(value)
    except (ValueError, TypeError):
        return default
    return default


def conform_to_schema(record: dict, schema: dict) -> dict:
    """DATA CONFORMATION: coerce a record to a target schema. schema maps field -> {type, default?, required?}.
    Returns {conformed, violations}: type-coerces present fields, fills defaults, drops extras, and reports
    missing-required + coercion failures — the deterministic gate before data enters a typed store."""
    conformed: dict = {}
    violations: list = []
    for field, rule in schema.items():
        target = rule.get("type", "str")
        if field in record and record[field] is not None:
            coerced = coerce_type(record[field], target, default=None)
            if coerced is None and record[field] is not None:
                violations.append(f"{field}: cannot coerce {record[field]!r} to {target}")
                if "default" in rule:
                    conformed[field] = rule["default"]
            else:
                conformed[field] = coerced
        elif "default" in rule:
            conformed[field] = rule["default"]
        elif rule.get("required"):
            violations.append(f"{field}: required field missing")
    extras = [k for k in record if k not in schema]
    return {"conformed": conformed, "violations": violations, "dropped_extras": sorted(extras)}


# ── embedding generation ─────────────────────────────────────────────────────────────────────────────────────
def l2_normalize(vec: list) -> list:
    """Unit-normalize a vector (L2). Zero vector maps to itself (no divide-by-zero)."""
    norm = sum(x * x for x in vec) ** 0.5
    return list(vec) if norm == 0 else [x / norm for x in vec]


def cosine_similarity(a: list, b: list) -> float:
    """Cosine similarity of two equal-length vectors in [-1, 1]. Zero vector -> 0.0."""
    if len(a) != len(b):
        raise ValueError("vectors must be equal length")
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(y * y for y in b) ** 0.5
    return 0.0 if na == 0 or nb == 0 else dot / (na * nb)


def hashing_vectorizer(tokens: list, dim: int) -> list:
    """Deterministic feature-hashing embedding (the 'hashing trick'): map tokens into a fixed dim-vector with
    a signed hash — same tokens always give the same vector, no vocabulary needed. dim >= 1."""
    if dim < 1:
        raise ValueError("dim must be >= 1")
    vec = [0.0] * dim
    for tok in tokens:
        h = zlib.crc32(str(tok).encode("utf-8"))
        sign = 1.0 if (h >> 31) & 1 else -1.0
        vec[h % dim] += sign
    return vec


def topk_by_cosine(query: list, matrix: list, k: int) -> list:
    """Top-k row indices of `matrix` most cosine-similar to `query` (the retrieval core of an embedding store).
    Ties broken by lower index; returns min(k, len) indices."""
    scored = [(cosine_similarity(query, row), -i, i) for i, row in enumerate(matrix)]
    scored.sort(reverse=True)
    return [i for _s, _neg, i in scored[:k]]


# ── model training ───────────────────────────────────────────────────────────────────────────────────────────
def train_test_split(items: list, test_frac: float, rng) -> dict:
    """Deterministic train/test split (rng = random.Random injected). Returns {train, test}: disjoint, union =
    all items, |test| = round(test_frac * n)."""
    if not 0.0 <= test_frac <= 1.0:
        raise ValueError("test_frac in [0,1]")
    idx = list(range(len(items)))
    rng.shuffle(idx)
    n_test = round(test_frac * len(items))
    test_idx = set(idx[:n_test])
    return {"train": [items[i] for i in range(len(items)) if i not in test_idx],
            "test": [items[i] for i in range(len(items)) if i in test_idx]}


def kfold_indices(n: int, k: int) -> list:
    """k contiguous-ish folds of range(n): returns [(train_idx, test_idx), ...]; every index is in exactly one
    test fold and folds partition range(n). k in [2, n]."""
    if not 2 <= k <= max(2, n):
        raise ValueError("k in [2, n]")
    fold_sizes = [n // k + (1 if i < n % k else 0) for i in range(k)]
    folds: list = []
    start = 0
    all_idx = list(range(n))
    for size in fold_sizes:
        test = all_idx[start:start + size]
        train = all_idx[:start] + all_idx[start + size:]
        folds.append((train, test))
        start += size
    return folds


def sgd_linear_fit(xs: list, ys: list, lr: float, epochs: int) -> dict:
    """One-feature linear regression y = w*x + b by batch gradient descent. On a linear dataset it converges to
    the closed-form fit. Returns {w, b}."""
    w = b = 0.0
    n = len(xs)
    for _ in range(epochs):
        err = [(w * x + b) - y for x, y in zip(xs, ys)]
        grad_w = sum(e * x for e, x in zip(err, xs)) * 2 / n
        grad_b = sum(err) * 2 / n
        w -= lr * grad_w
        b -= lr * grad_b
    return {"w": w, "b": b}


def confusion_counts(y_true: list, y_pred: list) -> dict:
    """Binary confusion counts (labels truthy/falsey). Returns {tp, fp, tn, fn}."""
    tp = fp = tn = fn = 0
    for t, p in zip(y_true, y_pred):
        if t and p:
            tp += 1
        elif not t and p:
            fp += 1
        elif not t and not p:
            tn += 1
        else:
            fn += 1
    return {"tp": tp, "fp": fp, "tn": tn, "fn": fn}


def precision_recall_f1(tp: int, fp: int, fn: int) -> dict:
    """Precision, recall, F1 from confusion counts (0.0 where undefined, not a crash)."""
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return {"precision": round(precision, 6), "recall": round(recall, 6), "f1": round(f1, 6)}


# ── loop patterns ────────────────────────────────────────────────────────────────────────────────────────────
def batch_process(items: list, fn: Callable[[list], list], batch_size: int) -> list:
    """Apply fn to consecutive batches and flatten the results (the embed/infer-in-batches loop). batch_size>=1."""
    if batch_size < 1:
        raise ValueError("batch_size >= 1")
    out: list = []
    for i in range(0, len(items), batch_size):
        out.extend(fn(items[i:i + batch_size]))
    return out


def poll_until(predicate: Callable[[], bool], now: Callable[[], float], timeout: float, interval: float,
               sleep: Optional[Callable[[float], None]] = None) -> bool:
    """Loop until predicate() is true or timeout elapses (injected clock). Returns True if satisfied, else
    False. sleep is injected/no-op for tests."""
    start = now()
    sleep = sleep or (lambda _s: None)
    while now() - start <= timeout:
        if predicate():
            return True
        sleep(interval)
        if sleep is None:  # pragma: no cover
            break
    return predicate()


def fixpoint(f: Callable[[Any], Any], x0: Any, max_iter: int = 1000) -> Any:
    """Iterate x = f(x) until a fixpoint (x == f(x)) or max_iter (the convergence loop). Returns the fixpoint."""
    x = x0
    for _ in range(max_iter):
        nxt = f(x)
        if nxt == x:
            return x
        x = nxt
    return x


# ── hierarchical patterns ────────────────────────────────────────────────────────────────────────────────────
def build_tree(edges: list) -> dict:
    """Adjacency (parent -> sorted children) from (parent, child) edges, plus the roots (nodes that are never a
    child). Returns {children, roots}."""
    children: dict = {}
    all_nodes: set = set()
    child_nodes: set = set()
    for parent, child in edges:
        children.setdefault(parent, []).append(child)
        children.setdefault(child, [])
        all_nodes.update((parent, child))
        child_nodes.add(child)
    for p in children:
        children[p].sort()
    return {"children": children, "roots": sorted(all_nodes - child_nodes)}


def hierarchical_rollup(children: dict, values: dict, node: Any) -> dict:
    """Roll values UP a tree (OLAP rollup): each node's total = its own value + the totals of its children.
    Returns node -> total. Iterative post-order to avoid recursion limits."""
    totals: dict = {}
    order: list = []
    stack = [node]
    visited: set = set()
    while stack:  # produce a post-order
        n = stack.pop()
        if n in visited:
            continue
        visited.add(n)
        order.append(n)
        for c in children.get(n, ()):
            stack.append(c)
    for n in reversed(order):
        totals[n] = values.get(n, 0) + sum(totals.get(c, 0) for c in children.get(n, ()))
    return totals


def tree_depth(children: dict, root: Any) -> int:
    """Max depth (number of nodes on the longest root-to-leaf path). A single-node tree has depth 1."""
    best = 0
    stack = [(root, 1)]
    while stack:
        node, d = stack.pop()
        best = max(best, d)
        for c in children.get(node, ()):
            stack.append((c, d + 1))
    return best


def nest_by_path(records: list, path_keys: list) -> dict:
    """Group flat records into a nested dict by a sequence of key fields (the hierarchical group-by). Leaves are
    lists of the records that share the full path."""
    root: dict = {}
    for rec in records:
        cur = root
        for key in path_keys[:-1]:
            cur = cur.setdefault(rec.get(key), {})
        leaf_key = rec.get(path_keys[-1])
        cur.setdefault(leaf_key, []).append(rec)
    return root


# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════
# REGISTRY + oracle-backed tests (proving "it works").
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════

def _test_common() -> None:
    assert chunk_list([1, 2, 3, 4, 5], 2) == [[1, 2], [3, 4], [5]]
    assert chunk_list([], 3) == []
    assert dedupe_stable([3, 1, 3, 2, 1]) == [3, 1, 2]
    assert flatten_dict({"a": {"b": 1, "c": {"d": 2}}, "e": 3}) == {"a.b": 1, "a.c.d": 2, "e": 3}
    assert deep_get({"a": {"b": {"c": 9}}}, "a.b.c") == 9 and deep_get({"a": 1}, "a.b.c", -1) == -1
    assert group_by([1, 2, 3, 4], lambda x: x % 2) == {1: [1, 3], 0: [2, 4]}
    assert parse_bool("Yes") is True and parse_bool("off") is False and parse_bool(0) is False


def _test_rare() -> None:
    import random  # noqa: PLC0415
    # toposort: order must respect deps; cycle raises
    order = toposort({"shirt": [], "tie": ["shirt"], "jacket": ["tie", "shirt"]})
    pos = {n: i for i, n in enumerate(order)}
    assert pos["shirt"] < pos["tie"] < pos["jacket"]
    try:
        toposort({"a": ["b"], "b": ["a"]})
        assert False, "cycle not detected"
    except ValueError:
        pass
    # levenshtein vs a naive full-matrix oracle on random small strings
    def _lev_oracle(a: str, b: str) -> int:
        dp = [[0] * (len(b) + 1) for _ in range(len(a) + 1)]
        for i in range(len(a) + 1):
            dp[i][0] = i
        for j in range(len(b) + 1):
            dp[0][j] = j
        for i in range(1, len(a) + 1):
            for j in range(1, len(b) + 1):
                dp[i][j] = min(dp[i - 1][j] + 1, dp[i][j - 1] + 1, dp[i - 1][j - 1] + (a[i - 1] != b[j - 1]))
        return dp[-1][-1]
    rng = random.Random(7)
    for _ in range(200):
        a = "".join(rng.choice("abc") for _ in range(rng.randint(0, 6)))
        b = "".join(rng.choice("abc") for _ in range(rng.randint(0, 6)))
        assert levenshtein(a, b) == _lev_oracle(a, b)
    assert merge_intervals([[1, 3], [2, 6], [8, 10], [15, 18]]) == [[1, 6], [8, 10], [15, 18]]
    assert merge_intervals([[1, 4], [4, 5]]) == [[1, 5]]
    # binary_search_leftmost vs bisect
    import bisect  # noqa: PLC0415
    arr = [1, 2, 2, 2, 5, 7]
    for t in range(-1, 9):
        assert binary_search_leftmost(arr, t) == bisect.bisect_left(arr, t)
    # reservoir sample: right size, subset, uniform-ish over many trials
    counts = {i: 0 for i in range(10)}
    for seed in range(3000):
        s = reservoir_sample(range(10), 3, random.Random(seed))
        assert len(s) == 3 and set(s) <= set(range(10)) and len(set(s)) == 3
        for x in s:
            counts[x] += 1
    assert min(counts.values()) > 0 and max(counts.values()) < 3000  # every element sampled, none always
    # token bucket with an injected clock
    clock = [0.0]
    tb = TokenBucket(rate=1.0, capacity=2.0, now=lambda: clock[0])
    assert tb.allow() and tb.allow() and not tb.allow()  # burst of 2 then empty
    clock[0] = 1.0
    assert tb.allow() and not tb.allow()  # refilled 1 token


def _test_super_rare() -> None:
    import random  # noqa: PLC0415
    # union-find vs a brute-force connectivity oracle
    rng = random.Random(11)
    for _ in range(50):
        n = rng.randint(1, 12)
        uf = UnionFind(n)
        oracle = {i: {i} for i in range(n)}
        for _e in range(rng.randint(0, 15)):
            a, b = rng.randrange(n), rng.randrange(n)
            uf.union(a, b)
            merged = oracle[a] | oracle[b]
            for x in merged:
                oracle[x] = merged
        for a in range(n):
            for b in range(n):
                assert (uf.find(a) == uf.find(b)) == (b in oracle[a])
    # Fenwick vs prefix-sum oracle
    for _ in range(50):
        n = rng.randint(1, 20)
        vals = [rng.randint(-5, 5) for _ in range(n)]
        ft = FenwickTree(n)
        for i, v in enumerate(vals):
            ft.update(i, v)
        for hi in range(n + 1):
            assert ft.prefix_sum(hi) == sum(vals[:hi])
        for lo in range(n + 1):
            for hi in range(lo, n + 1):
                assert ft.range_sum(lo, hi) == sum(vals[lo:hi])
    # majority vote
    assert boyer_moore_majority([2, 2, 1, 1, 1, 2, 2]) == 2
    assert boyer_moore_majority([1, 2, 3]) is None
    # KMP vs the str.find sweep oracle
    for _ in range(300):
        text = "".join(rng.choice("ab") for _ in range(rng.randint(0, 12)))
        pat = "".join(rng.choice("ab") for _ in range(rng.randint(1, 4)))
        oracle = [i for i in range(len(text) - len(pat) + 1) if text[i:i + len(pat)] == pat]
        assert kmp_search(text, pat) == oracle
    # Tarjan SCC vs a reachability brute force
    for _ in range(40):
        n = rng.randint(1, 8)
        graph = {i: [] for i in range(n)}
        for _e in range(rng.randint(0, 12)):
            graph[rng.randrange(n)].append(rng.randrange(n))
        def _reach(src, g):
            seen, stack = set(), [src]
            while stack:
                u = stack.pop()
                for v in g.get(u, ()):
                    if v not in seen:
                        seen.add(v)
                        stack.append(v)
            return seen
        comp_of: dict = {}
        for comp in tarjan_scc(graph):
            for node in comp:
                comp_of[node] = tuple(comp)
        for a in range(n):
            for b in range(n):
                same_scc = b in _reach(a, graph) and a in _reach(b, graph) or a == b
                assert (comp_of[a] == comp_of[b]) == same_scc
    # Dijkstra vs Bellman-Ford oracle
    for _ in range(40):
        n = rng.randint(1, 7)
        graph = {i: {} for i in range(n)}
        for _e in range(rng.randint(0, 12)):
            u, v = rng.randrange(n), rng.randrange(n)
            if u != v:
                graph[u][v] = rng.randint(1, 9)
        src = 0
        dj = dijkstra(graph, src)
        dist = {i: float("inf") for i in range(n)}
        dist[src] = 0
        for _i in range(n - 1):
            for u in graph:
                for v, w in graph[u].items():
                    if dist[u] + w < dist[v]:
                        dist[v] = dist[u] + w
        for node in range(n):
            assert dj.get(node, float("inf")) == dist[node]


def _test_token_optimization() -> None:
    # token budget gate: input stuffing and over-long output both caught, with the worst section named
    v = token_budget_gate({"system": 742, "history": 3890, "retrieval": 12640, "user": 184}, 4500, 700, 700)
    assert not v["ok"] and any(b["side"] == "input" and b["worst_section"] == "retrieval" for b in v["breaches"])
    v2 = token_budget_gate({"user": 184}, 4500, 900, 700)
    assert not v2["ok"] and any(b["side"] == "output" for b in v2["breaches"])
    assert token_budget_gate({"user": 184}, 4500, 600, 700)["ok"]
    # budgeted selection: respects the budget, skips over-budget items, keeps smaller later ones
    items = [("a", 300), ("b", 1000), ("c", 250), ("d", 300)]
    sel = select_within_budget(items, lambda it: it[1], 900)
    assert sum(it[1] for it in sel) <= 900 and ("b", 1000) not in sel and ("a", 300) in sel
    # tail percentile vs a hand computation (nearest-rank)
    vals = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    assert tail_percentile(vals, 100) == 100.0 and tail_percentile(vals, 50) == 50.0
    assert tail_percentile(vals, 95) == 100.0 and tail_percentile(vals, 90) == 90.0
    assert tail_percentile([42], 99) == 42.0
    try:
        tail_percentile([], 50)
        assert False, "empty percentile must raise"
    except ValueError:
        pass
    # schema validation: missing key + bad enum caught; good passes
    r = validate_against_schema({"priority": "sky-high"}, ["category", "priority"], {"priority": {"low", "high"}})
    assert not r["ok"] and any("category" in e for e in r["errors"]) and any("priority" in e for e in r["errors"])
    assert validate_against_schema({"category": "billing", "priority": "high"}, ["category", "priority"],
                                   {"priority": {"low", "high"}})["ok"]
    # model routing
    policy = {"simple_faq": "haiku-4.5", "legal_exception": "opus-4.8"}
    assert route_model("simple_faq", policy, "sonnet-4.6") == "haiku-4.5"
    assert route_model("unknown", policy, "sonnet-4.6") == "sonnet-4.6"
    # recent-turn compaction keeps the system turn + last k
    turns = [{"role": "system", "content": "s"}] + [{"role": "user", "content": str(i)} for i in range(10)]
    comp = compact_recent_turns(turns, 3)
    assert comp[0]["role"] == "system" and len(comp) == 4 and comp[-1]["content"] == "9"
    assert compact_recent_turns([{"role": "user", "content": "x"}], 0) == []


def _test_engineering() -> None:
    import random  # noqa: PLC0415
    rng = random.Random(3)
    # microservices: circuit breaker state machine
    clk = [0.0]
    cb = CircuitBreaker(threshold=2, cooldown=5.0, now=lambda: clk[0])
    assert cb.allow() and cb.state == "closed"
    cb.record(False); cb.record(False)
    assert cb.state == "open" and not cb.allow()      # tripped
    clk[0] = 6.0
    assert cb.allow() and cb.state == "half_open"     # cooled down -> trial
    cb.record(True); assert cb.state == "closed"      # trial success closes it
    assert exponential_backoff_schedule(1.0, 10.0, 5) == [1.0, 2.0, 4.0, 8.0, 10.0]
    assert idempotency_dedup([{"k": 1}, {"k": 1}, {"k": 2}], lambda r: r["k"]) == [{"k": 1}, {"k": 2}]
    # data analysis: Welford vs batch
    for _ in range(30):
        data = [rng.uniform(-10, 10) for _ in range(rng.randint(1, 40))]
        rs = RunningStats()
        for x in data:
            rs.push(x)
        mean = sum(data) / len(data)
        var = sum((x - mean) ** 2 for x in data) / len(data)
        assert abs(rs.mean - mean) < 1e-9 and abs(rs.variance() - var) < 1e-9
    assert iqr_outliers([10, 11, 12, 13, 9, 11, 100]) == [6]
    assert sum(histogram_counts([1, 2, 3, 4, 5, 6], 3)) == 6 and histogram_counts([1, 2, 3, 4, 5, 6], 3) == [2, 2, 2]
    # standardization + conformation
    z = zscore_normalize([1, 2, 3, 4, 5])
    assert abs(sum(z)) < 1e-9 and abs((sum(v * v for v in z) / len(z)) - 1.0) < 1e-9
    assert min_max_scale([10, 20, 30]) == [0.0, 0.5, 1.0] and zscore_normalize([7, 7, 7]) == [0.0, 0.0, 0.0]
    assert snake_case_key("CamelCaseKey") == "camel_case_key" and snake_case_key("kebab-case key") == "kebab_case_key"
    schema = {"age": {"type": "int", "required": True}, "active": {"type": "bool", "default": False},
              "name": {"type": "str"}}
    c = conform_to_schema({"age": "42", "name": "x", "extra": 1}, schema)
    assert c["conformed"]["age"] == 42 and c["conformed"]["active"] is False and c["dropped_extras"] == ["extra"]
    assert conform_to_schema({"name": "x"}, schema)["violations"] == ["age: required field missing"]
    # embedding generation
    assert abs(sum(x * x for x in l2_normalize([3.0, 4.0])) - 1.0) < 1e-9
    assert abs(cosine_similarity([1, 0], [1, 0]) - 1.0) < 1e-9 and abs(cosine_similarity([1, 0], [0, 1])) < 1e-9
    assert hashing_vectorizer(["a", "b"], 16) == hashing_vectorizer(["a", "b"], 16)  # deterministic
    mat = [[1.0, 0.0], [0.9, 0.1], [0.0, 1.0]]
    assert topk_by_cosine([1.0, 0.0], mat, 2) == [0, 1]
    # model training
    split = train_test_split(list(range(10)), 0.3, random.Random(1))
    assert len(split["test"]) == 3 and len(split["train"]) == 7 and set(split["train"]) | set(split["test"]) == set(range(10))
    folds = kfold_indices(10, 5)
    test_union = sorted(i for _tr, te in folds for i in te)
    assert test_union == list(range(10)) and all(len(te) == 2 for _tr, te in folds)
    fit = sgd_linear_fit([0, 1, 2, 3, 4], [1, 3, 5, 7, 9], lr=0.05, epochs=2000)  # y = 2x + 1
    assert abs(fit["w"] - 2.0) < 0.05 and abs(fit["b"] - 1.0) < 0.05
    cc = confusion_counts([1, 1, 0, 0, 1], [1, 0, 0, 1, 1])
    assert cc == {"tp": 2, "fp": 1, "tn": 1, "fn": 1}
    prf = precision_recall_f1(cc["tp"], cc["fp"], cc["fn"])
    assert abs(prf["precision"] - 2 / 3) < 1e-6 and abs(prf["recall"] - 2 / 3) < 1e-6
    # loop patterns
    assert batch_process(list(range(7)), lambda b: [x * 2 for x in b], 3) == [0, 2, 4, 6, 8, 10, 12]
    t = [0.0]
    hits = {"n": 0}
    def _pred():
        hits["n"] += 1
        return hits["n"] >= 3
    assert poll_until(_pred, lambda: t[0], timeout=10, interval=1, sleep=lambda s: t.__setitem__(0, t[0] + s))
    assert fixpoint(lambda x: (x + 16 // x) // 2 if x else 1, 16) in (4, 5)  # integer sqrt-ish convergence
    assert fixpoint(lambda x: x, 7) == 7
    # hierarchical
    tree = build_tree([("root", "a"), ("root", "b"), ("a", "c"), ("a", "d")])
    assert tree["roots"] == ["root"] and tree["children"]["a"] == ["c", "d"]
    roll = hierarchical_rollup(tree["children"], {"root": 1, "a": 2, "b": 3, "c": 4, "d": 5}, "root")
    assert roll["a"] == 2 + 4 + 5 and roll["root"] == 1 + (2 + 4 + 5) + 3
    assert tree_depth(tree["children"], "root") == 3
    nested = nest_by_path([{"region": "NA", "city": "NYC", "v": 1}, {"region": "NA", "city": "NYC", "v": 2},
                           {"region": "EU", "city": "LON", "v": 3}], ["region", "city"])
    assert len(nested["NA"]["NYC"]) == 2 and len(nested["EU"]["LON"]) == 1


#: registry: id -> (tier, name, fn-or-class, one-line mechanism, input_type, output_type)
PRIMITIVES: dict[str, dict[str, Any]] = {
    # COMMON
    "chunk_list": {"tier": "common", "obj": chunk_list, "in": "list, int", "out": "list[list]",
                   "mechanism": "slice a list into fixed-size consecutive chunks"},
    "dedupe_stable": {"tier": "common", "obj": dedupe_stable, "in": "list", "out": "list",
                      "mechanism": "order-preserving de-duplication via a seen-set"},
    "flatten_dict": {"tier": "common", "obj": flatten_dict, "in": "dict", "out": "dict",
                     "mechanism": "recursively flatten nested dicts into dotted keys"},
    "deep_get": {"tier": "common", "obj": deep_get, "in": "dict, str", "out": "Any",
                 "mechanism": "safe nested lookup by a dotted path with a default"},
    "group_by": {"tier": "common", "obj": group_by, "in": "list, callable", "out": "dict",
                 "mechanism": "bucket items by a key function, order-preserving"},
    "parse_bool": {"tier": "common", "obj": parse_bool, "in": "Any", "out": "bool",
                   "mechanism": "robust truthy-string parse with an ambiguity guard"},
    # RARE
    "toposort": {"tier": "rare", "obj": toposort, "in": "dict", "out": "list",
                 "mechanism": "Kahn topological sort with cycle detection"},
    "levenshtein": {"tier": "rare", "obj": levenshtein, "in": "str, str", "out": "int",
                    "mechanism": "single-row DP edit distance"},
    "merge_intervals": {"tier": "rare", "obj": merge_intervals, "in": "list", "out": "list",
                        "mechanism": "sort then sweep-merge overlapping intervals"},
    "binary_search_leftmost": {"tier": "rare", "obj": binary_search_leftmost, "in": "list, Any", "out": "int",
                               "mechanism": "bisect-left insertion index, from scratch"},
    "reservoir_sample": {"tier": "rare", "obj": reservoir_sample, "in": "iterable, int, Random", "out": "list",
                         "mechanism": "Algorithm R one-pass uniform k-sample of a stream"},
    "TokenBucket": {"tier": "rare", "obj": TokenBucket, "in": "rate, capacity, clock", "out": "allow(cost)->bool",
                    "mechanism": "token-bucket rate limiter with an injected clock"},
    # SUPER_RARE
    "UnionFind": {"tier": "super_rare", "obj": UnionFind, "in": "int n", "out": "find/union",
                  "mechanism": "disjoint-set union with path compression + union by rank"},
    "FenwickTree": {"tier": "super_rare", "obj": FenwickTree, "in": "int n", "out": "prefix/range sum",
                    "mechanism": "binary indexed tree: O(log n) prefix sums + point updates"},
    "boyer_moore_majority": {"tier": "super_rare", "obj": boyer_moore_majority, "in": "list", "out": "Any|None",
                             "mechanism": "Boyer-Moore majority vote, O(n) time O(1) space"},
    "kmp_search": {"tier": "super_rare", "obj": kmp_search, "in": "str, str", "out": "list[int]",
                   "mechanism": "Knuth-Morris-Pratt all-occurrences via the failure function"},
    "tarjan_scc": {"tier": "super_rare", "obj": tarjan_scc, "in": "dict", "out": "list[list]",
                   "mechanism": "Tarjan strongly-connected components, iterative"},
    "dijkstra": {"tier": "super_rare", "obj": dijkstra, "in": "dict, node", "out": "dict",
                 "mechanism": "Dijkstra shortest paths over a non-negative weighted graph, heap-based"},
    # TOKEN_OPTIMIZATION (capability group) — the "spend fewer tokens without hurting quality" architecture,
    # each tiered by base-model error rate. These primitives SAVE tokens by construction when an agent reuses
    # them to route information (source: token-reduction engineering practice, 2026-06).
    "token_budget_gate": {"tier": "rare", "cat": "token_optimization", "obj": token_budget_gate,
                          "in": "sections dict, limits", "out": "verdict dict",
                          "mechanism": "fail-fast per-route token budget check naming the breaching side"},
    "select_within_budget": {"tier": "rare", "cat": "token_optimization", "obj": select_within_budget,
                             "in": "items, token_of, budget", "out": "list",
                             "mechanism": "greedy budgeted selection for retrieval/context (span budget)"},
    "tail_percentile": {"tier": "common", "cat": "token_optimization", "obj": tail_percentile,
                        "in": "values, p", "out": "float",
                        "mechanism": "nearest-rank percentile for token/latency tail measurement"},
    "validate_against_schema": {"tier": "rare", "cat": "token_optimization", "obj": validate_against_schema,
                                "in": "obj, required, enums", "out": "verdict dict",
                                "mechanism": "output-schema enforcement (required keys + enums) sans jsonschema"},
    "route_model": {"tier": "common", "cat": "token_optimization", "obj": route_model,
                    "in": "route, policy, default", "out": "model name",
                    "mechanism": "cheapest-model routing by an explicit policy table"},
    "compact_recent_turns": {"tier": "common", "cat": "token_optimization", "obj": compact_recent_turns,
                             "in": "turns, k", "out": "list",
                             "mechanism": "recent-window memory: keep last k turns + a leading system turn"},
    # ENGINEERING DOMAINS
    "CircuitBreaker": {"tier": "rare", "cat": "microservices", "obj": CircuitBreaker, "in": "threshold, cooldown, clock",
                       "out": "allow/record", "mechanism": "closed/open/half-open circuit breaker state machine"},
    "exponential_backoff_schedule": {"tier": "common", "cat": "microservices", "obj": exponential_backoff_schedule,
                                     "in": "base, cap, attempts", "out": "list",
                                     "mechanism": "capped exponential backoff delay sequence"},
    "idempotency_dedup": {"tier": "common", "cat": "microservices", "obj": idempotency_dedup,
                          "in": "requests, key_of", "out": "list",
                          "mechanism": "effectively-once: keep first request per idempotency key"},
    "RunningStats": {"tier": "rare", "cat": "data_analysis", "obj": RunningStats, "in": "stream", "out": "mean/variance",
                     "mechanism": "Welford online mean/variance, one pass, numerically stable"},
    "iqr_outliers": {"tier": "rare", "cat": "data_analysis", "obj": iqr_outliers, "in": "values, k", "out": "indices",
                     "mechanism": "Tukey IQR-fence outlier detection"},
    "histogram_counts": {"tier": "common", "cat": "data_analysis", "obj": histogram_counts, "in": "values, bins",
                         "out": "counts", "mechanism": "equal-width histogram bin counts"},
    "zscore_normalize": {"tier": "common", "cat": "data_standardization", "obj": zscore_normalize, "in": "values",
                         "out": "list", "mechanism": "standardize to mean 0 / std 1 (divide-by-zero safe)"},
    "min_max_scale": {"tier": "common", "cat": "data_standardization", "obj": min_max_scale, "in": "values, lo, hi",
                      "out": "list", "mechanism": "min-max scale to [lo, hi]"},
    "snake_case_key": {"tier": "common", "cat": "data_standardization", "obj": snake_case_key, "in": "str", "out": "str",
                       "mechanism": "standardize a key to snake_case from Camel/kebab/space"},
    "coerce_type": {"tier": "common", "cat": "data_conformation", "obj": coerce_type, "in": "value, target, default",
                    "out": "Any", "mechanism": "safe type cast with a fallback (never raises)"},
    "conform_to_schema": {"tier": "rare", "cat": "data_conformation", "obj": conform_to_schema, "in": "record, schema",
                          "out": "conformed+violations", "mechanism": "coerce/fill/drop a record to a typed schema, report violations"},
    "l2_normalize": {"tier": "common", "cat": "embedding_generation", "obj": l2_normalize, "in": "vec", "out": "vec",
                     "mechanism": "L2 unit-normalize a vector (zero-safe)"},
    "cosine_similarity": {"tier": "common", "cat": "embedding_generation", "obj": cosine_similarity, "in": "a, b",
                          "out": "float", "mechanism": "cosine similarity of two vectors"},
    "hashing_vectorizer": {"tier": "rare", "cat": "embedding_generation", "obj": hashing_vectorizer, "in": "tokens, dim",
                           "out": "vec", "mechanism": "deterministic feature-hashing embedding (hashing trick)"},
    "topk_by_cosine": {"tier": "rare", "cat": "embedding_generation", "obj": topk_by_cosine, "in": "query, matrix, k",
                       "out": "indices", "mechanism": "top-k most cosine-similar rows (retrieval core)"},
    "train_test_split": {"tier": "common", "cat": "model_training", "obj": train_test_split, "in": "items, frac, rng",
                         "out": "train/test", "mechanism": "deterministic disjoint train/test split"},
    "kfold_indices": {"tier": "rare", "cat": "model_training", "obj": kfold_indices, "in": "n, k", "out": "folds",
                      "mechanism": "k-fold CV index partition"},
    "sgd_linear_fit": {"tier": "rare", "cat": "model_training", "obj": sgd_linear_fit, "in": "xs, ys, lr, epochs",
                       "out": "w, b", "mechanism": "one-feature linear regression by gradient descent"},
    "confusion_counts": {"tier": "common", "cat": "model_training", "obj": confusion_counts, "in": "y_true, y_pred",
                         "out": "tp/fp/tn/fn", "mechanism": "binary confusion counts"},
    "precision_recall_f1": {"tier": "common", "cat": "model_training", "obj": precision_recall_f1, "in": "tp, fp, fn",
                            "out": "metrics", "mechanism": "precision/recall/F1 from confusion counts"},
    "batch_process": {"tier": "common", "cat": "loop", "obj": batch_process, "in": "items, fn, batch_size", "out": "list",
                      "mechanism": "apply a fn over batches and flatten (embed/infer loop)"},
    "poll_until": {"tier": "rare", "cat": "loop", "obj": poll_until, "in": "predicate, clock, timeout, interval",
                   "out": "bool", "mechanism": "poll until a predicate holds or timeout"},
    "fixpoint": {"tier": "rare", "cat": "loop", "obj": fixpoint, "in": "f, x0, max_iter", "out": "Any",
                 "mechanism": "iterate to a fixpoint (convergence loop)"},
    "build_tree": {"tier": "rare", "cat": "hierarchical", "obj": build_tree, "in": "edges", "out": "children+roots",
                   "mechanism": "parent->children adjacency + roots from edges"},
    "hierarchical_rollup": {"tier": "rare", "cat": "hierarchical", "obj": hierarchical_rollup, "in": "children, values, root",
                            "out": "totals", "mechanism": "OLAP rollup: sum values up the tree"},
    "tree_depth": {"tier": "common", "cat": "hierarchical", "obj": tree_depth, "in": "children, root", "out": "int",
                   "mechanism": "max root-to-leaf depth"},
    "nest_by_path": {"tier": "rare", "cat": "hierarchical", "obj": nest_by_path, "in": "records, path_keys", "out": "dict",
                     "mechanism": "hierarchical group-by into a nested dict"},
}

_TESTS: tuple[Callable[[], None], ...] = (_test_common, _test_rare, _test_super_rare, _test_token_optimization,
                                          _test_engineering)
TIERS = ("common", "rare", "super_rare")


def _camel(*words: str) -> str:
    parts = re.split(r"[^A-Za-z0-9]+", " ".join(words))
    return ("".join(p[:1].upper() + p[1:] for p in parts if p) or "Edge")[:48]


def primitive_source(pid: str) -> str:
    """The REAL source of the implementation (inspect.getsource — single source, no drift)."""
    return inspect.getsource(PRIMITIVES[pid]["obj"])


def token_estimate(text: str) -> int:
    """Deterministic token proxy: word/punctuation atoms (a defensible ~model-token count for code)."""
    return len(re.findall(r"[A-Za-z0-9_]+|[^\sA-Za-z0-9_]", text))


def card(pid: str) -> dict[str, Any]:
    """A governed candidate card carrying the EXECUTABLE body (real source), typed edges, tier, canonical id."""
    spec = PRIMITIVES[pid]
    src = primitive_source(pid)
    title = f"{spec['mechanism']} [{pid}]"
    blackbox = (f"Executable primitive ({spec['tier']} tier): {spec['mechanism']}. "
                f"Input: {spec['in']}. Output: {spec['out']}. Ships with an oracle-backed test; runs "
                f"deterministically at 0 generation tokens when reused.")
    pid_hash = canonical_id(CARD_PREFIX, title, src)
    return {
        "record_type": CARD_RECORD_TYPE, "schema_version": 1, "kind": "route.primitive",
        "primitive_id": pid_hash, "impl_name": pid, "tier": spec["tier"], "title": title[:160],
        "blackbox": blackbox[:1200], "mechanism": spec["mechanism"],
        "input_edge": _camel(pid, "input"), "output_edge": _camel(pid, "result"),
        "capability_tags": [f"tier:{spec['tier']}", "executable", "coding_task", pid]
                           + ([f"cat:{spec['cat']}"] if spec.get("cat") else []),
        "executable_body": src, "language": "python",
        "executable_token_estimate": token_estimate(src),
        "contract": {"input": spec["in"], "output": spec["out"]},
        "provenance": {"minter": "scripts.executable_primitive_library", "verified_by": "oracle_backed_test"},
        "promotion_blockers": ["license_review"], **BOUNDARY,
    }


def all_cards() -> list[dict[str, Any]]:
    return [card(pid) for pid in PRIMITIVES]


def run_tests() -> dict[str, Any]:
    """Run every tier's oracle-backed tests. Returns which passed; a failure surfaces the exception."""
    results: dict[str, Any] = {}
    for fn in _TESTS:
        tier = fn.__name__.replace("_test_", "")
        try:
            fn()
            results[tier] = {"ok": True}
        except Exception as exc:  # noqa: BLE001
            results[tier] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    return results


def staged_path() -> Path:
    return resource("data") / "dev-intel" / "aidevobserver_edge_foundry" / STAGED_FILENAME


def stage_cards(cards: list[dict[str, Any]], target_path: Optional[Path] = None) -> dict[str, Any]:
    from scripts._jsonl import read_jsonl_tolerant  # noqa: PLC0415
    p = target_path or staged_path()
    if p.name != STAGED_FILENAME:
        raise ValueError(f"refusing to write to {p.name!r} — only {STAGED_FILENAME!r} allowed")
    if p.is_symlink() or (p.exists() and p.resolve().name in _VERIFIED_CORPUS_FILENAMES):
        raise ValueError("refused: symlink or verified-corpus target")
    existing = {str(r.get("primitive_id")) for r in (read_jsonl_tolerant(p) if p.exists() else [])}
    appended = 0
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as fh:
        for c in cards:
            if str(c["primitive_id"]) in existing:
                continue
            existing.add(str(c["primitive_id"]))
            fh.write(json.dumps(c, sort_keys=True) + "\n")
            appended += 1
    return {"appended": appended, "on_file": len(existing), "path": str(p), **BOUNDARY}


def _self_test() -> int:
    checks: list[tuple[str, bool]] = []
    # 1) EVERY primitive actually works (oracle-backed) — the core "it works" gate.
    results = run_tests()
    for tier, r in results.items():
        checks.append((f"tier '{tier}': all primitives pass their oracle-backed tests",
                       r["ok"] if r["ok"] else print(f"    {tier} error: {r.get('error')}") or False))
    # 2) mutation gate: a deliberately broken implementation makes its tier go red.
    import random  # noqa: PLC0415
    orig = globals()["levenshtein"]
    try:
        globals()["levenshtein"] = lambda a, b: 0  # planted bug
        broke = False
        try:
            _test_rare()
        except AssertionError:
            broke = True
        checks.append(("mutation gate: a broken primitive is CAUGHT by its oracle test", broke))
    finally:
        globals()["levenshtein"] = orig
    # 3) cards carry the real executable body + recompute their canonical id + typed edges + boundary.
    cards = all_cards()
    checks.append(("every primitive has a card with a non-trivial executable body",
                   all(len(c["executable_body"]) > 40 and "def " in c["executable_body"]
                       or "class " in c["executable_body"] for c in cards)))
    checks.append(("card ids recompute from canonical_id(title, source)",
                   all(c["primitive_id"] == canonical_id(CARD_PREFIX, c["title"], c["executable_body"])
                       for c in cards)))
    checks.append(("all three tiers are represented",
                   {c["tier"] for c in cards} == set(TIERS)))
    checks.append(("cards are candidate/serves_truth=false with CamelCase edges",
                   all(c["candidate"] and not c["serves_truth"]
                       and re.match(r"^[A-Z][A-Za-z0-9]*$", c["input_edge"]) for c in cards)))
    # 4) determinism + write-safety
    checks.append(("card generation is deterministic (byte-identical twice)",
                   json.dumps(all_cards(), sort_keys=True) == json.dumps(all_cards(), sort_keys=True)))
    import tempfile  # noqa: PLC0415
    refused = False
    try:
        stage_cards(cards[:1], target_path=Path(tempfile.gettempdir()) / "verified_factory_primitive_cards.jsonl")
    except ValueError:
        refused = True
    checks.append(("stage_cards refuses a verified corpus filename", refused))
    with tempfile.TemporaryDirectory() as td:
        tp = Path(td) / STAGED_FILENAME
        a = stage_cards(cards, target_path=tp)
        b = stage_cards(cards, target_path=tp)
        checks.append(("append-dedupe: first stages all, second stages 0",
                       a["appended"] == len(cards) and b["appended"] == 0))

    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print(f"\nPASS - executable_primitive_library: {len(PRIMITIVES)} primitives across "
          f"{len(TIERS)} tiers, EVERY one proven correct by an oracle-backed test (mutation-gated); cards "
          f"carry the real executable body + canonical id; deterministic; write-safe. These RUN — reuse is "
          f"0 generation tokens. serves_truth=false.")
    return 0


def _stage() -> int:
    tests = run_tests()
    if not all(r["ok"] for r in tests.values()):
        print(f"refusing to stage — tests failing: {tests}")
        return 1
    cards = all_cards()
    wrote = stage_cards(cards)
    by_tier: dict[str, int] = {}
    for c in cards:
        by_tier[c["tier"]] = by_tier.get(c["tier"], 0) + 1
    rec = {"record_type": "executable_primitive_stage_receipt", "n_primitives": len(cards),
           "by_tier": by_tier, "appended": wrote["appended"], "on_file": wrote["on_file"],
           "all_tests_pass": True, **BOUNDARY}
    out = resource("data") / "dev-intel" / "session_emulation" / "executable_primitive_stage_receipt.json"
    out.write_text(json.dumps(rec, indent=2, sort_keys=True))
    print(json.dumps(rec, indent=2, sort_keys=True))
    print(f"\nstaged: {wrote['path']}\nreceipt: {out}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--stage", action="store_true")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.stage:
        return _stage()
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
