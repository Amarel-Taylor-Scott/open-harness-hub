#!/usr/bin/env python3
"""check_variation_store — capability variations are stored in git (GitHub/GitLab) + the durable version log.

Proves: variations persist to the version_history stream (idempotent by version_hash, lossless winners+losers); committing
to INTERNAL git puts the winner on main + each loser on a PR branch (offline, always works); GitHub/GitLab are SUPPORTED
but token-gated (honest plan-only without a git_token, never a fake push); the new git/hosting credential KINDS exist.
serves_truth=false.

  python3 scripts/check_variation_store.py --self-test
"""
from __future__ import annotations

from src.teleon.runtime import credentials as C
from src.teleon.storage.git_backend_port import SUPPORTED_PLATFORMS
from src.teleon.synthesis import variation_store as V


def _self_test() -> int:
    fails = []
    def ck(n, ok, d=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok: fails.append(n)

    cap = "test_capability_xyz"
    variations = [
        {"decision_path": "A=a2/B=b2", "status": "working", "strategy": "base"},
        {"decision_path": "A=a1", "status": "dead_end", "strategy": "base"},
        {"decision_path": "A=a2/B=b1", "status": "abandoned", "strategy": "sprout"},
    ]
    r1 = V.record_variations(cap, variations)
    ck("variations persist to version_history (winners + losers, lossless)", r1["total"] == 3)
    r2 = V.record_variations(cap, variations)
    ck("re-record is idempotent (version_hash dedupe — no dup rows)", r2["stored"] == 0)
    got = {v["status"] for v in V.list_variations(cap)}
    ck("list_variations returns all kept variations (incl. losers)", {"working", "dead_end", "abandoned"} <= got, str(got))

    # internal git: winner -> main, losers -> PR branches (offline, always works)
    g = V.commit_to_git(cap, variations, platform="internal", now="2026-06-22T00:00:00Z")
    ck("internal git push succeeds offline", g.get("pushed") is True and g.get("main") is True)
    ck("each loser becomes a PR branch (lossless review trail)", len(g.get("branches", [])) == 2)

    # GitHub/GitLab supported but token-gated (honest, no fake push)
    ck("github + gitlab are supported platforms", {"github", "gitlab"} <= set(SUPPORTED_PLATFORMS))
    gh = V.commit_to_git(cap, variations, platform="github", now="2026-06-22T00:00:00Z", token_present=False)
    ck("github push without a git_token -> honest plan (not a fake push)", gh.get("pushed") is False and "needs a git_token" in gh.get("reason", ""))
    gh2 = V.commit_to_git(cap, variations, platform="github", now="2026-06-22T00:00:00Z", token_present=True)
    ck("github with a token -> pushes (winner main + loser branches)", gh2.get("pushed") is True)
    ck("unsupported platform -> honest error", "error" in V.commit_to_git(cap, variations, platform="dropbox", now="x"))

    # the other/hosting credential KINDS
    ck("credential kinds modeled (git_token + deploy_token beyond api_key)",
       C.credential_kind("github") == "git_token" and C.credential_kind("fly") == "deploy_token")
    ck("gitlab git_token + fly/cloudflare deploy (hosting) keys registered",
       "gitlab" in C.services_by_kind("git_token") and {"fly", "cloudflare_ai"} <= set(C.services_by_kind("deploy_token")))
    ck("default kind is api_key", C.credential_kind("tavily") == "api_key")

    print("\n" + ("PASS - check_variation_store: variations stored in git (winner->main, losers->PR branches) + the version "
                  "log; GitHub/GitLab token-gated; git/deploy key kinds modeled." if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(_self_test())
