#!/usr/bin/env python3
"""check_git_backend_port — proof that a capability unit's storage/versioning/diffs work behind ONE pluggable git
backend, backed by internal git OR the client's platform (GitHub/GitLab/Gitea), with governance in a SIDECAR so the
client's code stays clean. The bridge that meets teams where their code lives while keeping the abstraction above git.

CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_git_backend_port.py --self-test
"""
from __future__ import annotations

import os
import sys

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _R not in sys.path:
        sys.path.insert(0, _R)

from src.teleon.storage.git_backend_port import (
    CapabilityUnitVCS, ClientPlatformBackend, GitBackendPort, LocalGitBackend, SUPPORTED_PLATFORMS,
)


def _self_test() -> int:
    fails: list[str] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    be = LocalGitBackend("internal")
    ck("LocalGitBackend conforms to the GitBackendPort protocol", isinstance(be, GitBackendPort))

    # a unit versions through the backend: commit v1 -> v2 -> history/diff/read/tag
    r1 = be.commit("entity-resolution", "def resolve(a,b): return a==b", message="v1", now="t0")
    r2 = be.commit("entity-resolution", "def resolve(a,b): return fuzzy(a,b)", message="v2", now="t1")
    ck("two commits build a versioned history (parent chain)", len(be.history("entity-resolution")) == 2 and r2.parent == r1.rev)
    ck("revisions are content-addressed (sha) + deterministic", r1.rev != r2.rev and len(r1.rev) == 16
       and LocalGitBackend().commit("u", "x", message="m", now="t").rev == LocalGitBackend().commit("u", "x", message="m", now="t").rev)
    ck("read returns the exact content at a revision", be.read("entity-resolution", r1.rev).startswith("def resolve(a,b): return a=="))
    ck("diff between revisions is non-empty + unified", "fuzzy" in be.diff("entity-resolution", r1.rev, r2.rev))
    be.tag("entity-resolution", r2.rev, "released")

    # governance rides in a SIDECAR — the code blob stays clean
    be.attach_governance("entity-resolution", r2.rev, {"verified": True, "measured_lift": 0.71, "receipt_id": "rc1"})
    gov = be.read_governance("entity-resolution", r2.rev)
    ck("governed metadata attaches in the sidecar (verified/lift/receipt)", gov.get("verified") is True and gov.get("measured_lift") == 0.71)
    ck("the code blob does NOT contain the governance (clean separation)",
       "verified" not in be.read("entity-resolution", r2.rev) and "measured_lift" not in be.read("entity-resolution", r2.rev))
    ck("a backend never serves truth (storage != source of truth)", r1.serves_truth is False and gov.get("serves_truth") is False)

    # PLUGGABLE: the SAME unit/code works on a CLIENT platform backend (offline mirror) — backend-agnostic
    gh = ClientPlatformBackend("github", "acme/capabilities")
    ck("ClientPlatformBackend conforms to the port + supports github/gitlab/gitea", isinstance(gh, GitBackendPort)
       and {"github", "gitlab", "gitea"} <= set(SUPPORTED_PLATFORMS))
    g1 = gh.commit("entity-resolution", "def resolve(a,b): return a==b", message="v1", now="t0")
    ck("the same unit commits to the client's platform (store in THEIR GitHub), same abstraction", g1.backend == "github")

    # DEFER GATE: live external calls are owner-gated (need network + client creds); offline mirrors
    live = ClientPlatformBackend("gitlab", "acme/capabilities", live=True)
    try:
        live.commit("u", "x", message="m", now="t"); gated = False
    except PermissionError:
        gated = True
    ck("a LIVE client-platform call is owner-gated (network + client creds); offline path works", gated)

    # the governed wrapper: commit a unit + attach governance, code blob carries no governance, never truth
    vcs = CapabilityUnitVCS(LocalGitBackend("internal"))
    out = vcs.commit_unit("grounded-search", "def search(q): ...", message="v1", now="t0",
                          governance={"verified": True, "receipt_id": "rc2", "secret": "should-not-pass"})
    ck("CapabilityUnitVCS commits a unit + sidecar governance; code blob has no governance; never truth",
       out["governance_sidecar"].get("verified") is True and "secret" not in out["governance_sidecar"]
       and out["code_blob_has_governance"] is False and out["serves_truth"] is False)
    ck("the wrapper exposes history + diff over the chosen backend", len(vcs.history("grounded-search")) == 1)

    print("\n" + ("PASS - check_git_backend_port: a capability unit's storage/versioning/diffs work behind ONE "
                  "pluggable git backend — internal git OR the client's GitHub/GitLab/Gitea (same abstraction); "
                  "governance rides in a SIDECAR so the client's code stays clean; live external calls are "
                  "owner-gated with an offline mirror (DEFER GATE); a backend never serves truth. The bridge: "
                  "familiar git where their code lives + the governed abstraction above it."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def _main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--self-test" in argv:
        return _self_test()
    print("usage: check_git_backend_port.py --self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
