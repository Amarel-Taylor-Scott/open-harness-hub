#!/usr/bin/env python3
"""check_experiments_ids — functional proof of the canonical-id MINTER (``src.teleon.experiments.ids``).

``ids.py`` is THE single authority that mints every generated data id (``canonical_id``) — the code-readiness
benchmark flagged it as the top high-fan-in **UNVERIFIED** module (29 dependents, no self-test). This closes
that gap by proving the properties every caller relies on:
  * DETERMINISM — same input → same id, in-process AND cross-process under a DIFFERENT ``PYTHONHASHSEED`` (so
    the minter cannot secretly depend on ``hash()``/set ordering — the classic non-reproducibility bug);
  * COLLISION-RESISTANCE — thousands of distinct inputs → thousands of distinct ids;
  * CONTENT-SENSITIVITY — a changed part changes the id (source changes are detectable);
  * FORMATTING-STABILITY — ``canonical_bytes`` normalizes dict key order, so re-formatting never mints a false
    version (the ID-discipline law), while content changes still register;
  * SHAPE ``<prefix>-<16 hex>`` and NO version-in-the-id (``.vN``/``@N`` — the naming law: version is metadata).

  PYTHONPATH=. python3 scripts/check_experiments_ids.py --self-test
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

_here = Path(__file__).resolve()
_SBC = next((p for p in _here.parents if (p / "scripts" / "_repo_paths.py").exists()), _here.parents[1])
if str(_SBC) not in sys.path:
    sys.path.insert(0, str(_SBC))
from scripts._repo_paths import install as _install_code_roots  # noqa: E402

_install_code_roots()


def _checks() -> list[tuple[str, bool, str]]:
    from src.teleon.experiments.ids import canonical_bytes, canonical_id, sha256_hex  # noqa: PLC0415

    results: list[tuple[str, bool, str]] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        results.append((name, ok, detail))

    # A. determinism (in-process)
    a1 = canonical_id("prim", "ocr", "v1contract")
    a2 = canonical_id("prim", "ocr", "v1contract")
    ck("canonical_id deterministic in-process (same parts -> same id)", a1 == a2, a1)

    # B. shape: <prefix>-<16 hex>
    ck("shape is <prefix>-<16 lowercase hex>", bool(re.match(r"^prim-[0-9a-f]{16}$", a1)), a1)

    # C. content sensitivity + prefix participation
    ck("a changed part changes the id (content detectable)", a1 != canonical_id("prim", "ocr", "v2contract"))
    cap = canonical_id("cap", "ocr", "v1contract")
    ck("prefix participates in identity", a1 != cap and cap.startswith("cap-"), cap)

    # D. collision resistance across a large batch
    batch = {canonical_id("x", str(i), f"body-{i}") for i in range(5000)}
    ck("5000 distinct inputs -> 5000 distinct ids (no collisions)", len(batch) == 5000, f"{len(batch)} unique")

    # E. canonical_bytes: formatting-stable (key order) but content-sensitive
    ck("canonical_bytes normalizes dict key order (formatting != a new version)",
       canonical_bytes({"a": 1, "b": 2}) == canonical_bytes({"b": 2, "a": 1}))
    ck("canonical_bytes IS sensitive to a content change",
       canonical_bytes({"a": 1, "b": 2}) != canonical_bytes({"a": 1, "b": 3}))

    # F. sha256_hex determinism + shape
    h1, h2 = sha256_hex({"a": 1}), sha256_hex({"a": 1})
    ck("sha256_hex deterministic + 64 hex chars", h1 == h2 and bool(re.match(r"^[0-9a-f]{64}$", h1)))

    # G. no version-in-the-id (the naming law)
    ck("id carries NO version suffix (version lives in metadata, not the id)", ".v" not in a1 and "@" not in a1)

    # H. CROSS-PROCESS determinism under a different PYTHONHASHSEED — the strongest reproducibility proof: if
    #    the minter used hash()/unordered sets, a different seed would change the id. It must NOT.
    probe = ("import scripts._repo_paths as r; r.install(); "
             "from src.teleon.experiments.ids import canonical_id; "
             "print(canonical_id('prim','ocr','v1contract'))")
    seeds = []
    for seed in ("12345", "99999"):
        env = {**os.environ, "PYTHONHASHSEED": seed}
        out = subprocess.run([sys.executable, "-c", probe], capture_output=True, text=True,
                             cwd=str(_SBC), env=env, timeout=60)
        seeds.append(out.stdout.strip())
    ck("cross-process determinism under two PYTHONHASHSEEDs (id identical to in-process)",
       seeds[0] == seeds[1] == a1, f"{seeds} vs {a1}")

    return results


def main() -> int:
    results = _checks()
    failures = [n for n, ok, _ in results if not ok]
    for name, ok, detail in results:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
    if failures:
        print(f"\n{len(failures)} FAILURES: {failures}")
        return 1
    print("\nPASS - check_experiments_ids: the canonical-id minter is deterministic (in- AND cross-process under "
          "differing PYTHONHASHSEED), collision-resistant (5000/5000 unique), content-sensitive, formatting-stable "
          "(key order), shaped <prefix>-<16 hex>, and version-free. The top high-fan-in module is now verified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
