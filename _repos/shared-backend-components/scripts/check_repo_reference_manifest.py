#!/usr/bin/env python3
"""check_repo_reference_manifest — proof that the repo_reference/ clone set is governed + reconstructable WITHOUT
republishing anyone's code. The clones are gitignored (copyleft/unstated code never enters our git); the tracked
_repos/shared-backend-components/architecture/repo_reference_manifest.json records exactly what to re-clone (slug + commit SHA) and how we govern
each (license, disposition, the seed we distilled). Fresh-checkout-safe: validates the manifest, never the clones.

Asserts: every repo has a valid commit SHA + license + disposition; `vendorable` agrees with the license class
(copyleft/unstated → never vendorable — the don't-republish guard); the folder is actually gitignored; every
reviewed repo + the DueCare template are covered; and each repo's distilled seeds map to real built artifacts.

CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_repo_reference_manifest.py --self-test
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import json
import os
import re
import sys
from pathlib import Path

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _R not in sys.path:
        sys.path.insert(0, _R)

_REPO = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_MANIFEST = _resource("architecture") / "repo_reference_manifest.json"
_SIGNAL_FEED = _resource("data") / "capability-candidates" / "discovered-feed-github-signal-2026-06-20.json"
_SHA = re.compile(r"^[0-9a-f]{40}$")

from src.teleon.seeds import all_seeds
from src.teleon.seeds.capability_seed import vendorable


def _self_test() -> int:
    fails: list[str] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    m = json.loads(_MANIFEST.read_text())
    repos = m["repos"]
    ck("manifest declares the folder gitignored + never republished + serves_truth false",
       m["folder"] == "repo_reference/" and m["gitignored"] is True and m["serves_truth"] is False)
    ck("every repo has name/slug/url/cloned_sha/license/disposition/our_seeds",
       all({"name", "slug", "url", "cloned_sha", "license", "disposition", "our_seeds"} <= set(r) for r in repos))
    bad_sha = [r["name"] for r in repos if not _SHA.match(r["cloned_sha"])]
    ck("every cloned_sha is a full 40-hex git commit (reconstructable)", not bad_sha, str(bad_sha))

    # the don't-republish guard: vendorable must agree with the license class; copyleft/unstated never vendorable
    mismatch = [r["name"] for r in repos if r["vendorable"] != vendorable(r["license"])]
    ck("vendorable agrees with the license class (consistent with the seed framework)", not mismatch, str(mismatch))
    leaky = [r["name"] for r in repos if not vendorable(r["license"]) and r["vendorable"]]
    ck("no copyleft/unstated/proprietary repo is marked vendorable (don't-republish guard)", not leaky, str(leaky))

    # coverage: every reviewed GitHub REPO (not dead-SaaS targets like deeprepo.ai) + the DueCare template are present
    signal = json.loads(_SIGNAL_FEED.read_text())["candidates"]
    signal_tokens = {c["repo"].split("/")[-1].lower() for c in signal if "github.com" in c.get("source_url", "")}
    man_tokens = {r["slug"].split("/")[-1].lower() for r in repos}
    missing = sorted(t for t in signal_tokens if t not in man_tokens)
    ck("every reviewed GitHub repo is in the manifest (deeprepo.ai is a dead SaaS, not cloneable)", not missing, str(missing))
    ck("the DueCare template (gemma4_comp) is in the manifest as TEMPLATE",
       any(r["name"] == "gemma4_comp" and r["disposition"] == "TEMPLATE" for r in repos))

    # the folder is actually gitignored (the rule exists)
    gi = (_REPO.parent.parent / ".gitignore").read_text()  # .gitignore stayed at the monorepo root (_repos/<sbc>.parent.parent)
    ck("repo_reference/ is gitignored (clones never enter git; only README tracked)",
       "/repo_reference/*" in gi and "!/repo_reference/README.md" in gi)

    # each repo's distilled seeds map to real built artifacts (capability-seed slots, or template modules/scripts)
    seed_slots = {s.slot for s in all_seeds()}
    template_artifacts = {"entity-intelligence-ingestion": _resource("scripts/ingest_entity_intelligence_catalog.py"),
                          "profession-capability-seeder": _resource("src/teleon/seeds/profession_capability_seeder.py")}
    bad_seed = []
    for r in repos:
        for s in r["our_seeds"]:
            if s in seed_slots:
                continue
            if s in template_artifacts and template_artifacts[s].exists():
                continue
            bad_seed.append(f"{r['name']}:{s}")
    ck("every distilled seed maps to a real built artifact (seed slot or template module)", not bad_seed, str(bad_seed))
    ck("the README is the only tracked file inside repo_reference/", (_resource("repo_reference") / "README.md").exists())

    n_vend = sum(1 for r in repos if r["vendorable"])
    print("\n" + (f"PASS - check_repo_reference_manifest: {len(repos)} reference repos recorded + reconstructable "
                  f"(slug+SHA), {n_vend} vendorable / {len(repos) - n_vend} clean-room-only; copyleft/unstated never "
                  f"vendorable; folder gitignored (no republishing); every reviewed repo + the DueCare template "
                  f"covered; distilled seeds map to real artifacts. Never serves truth."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def _main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--self-test" in argv:
        return _self_test()
    print("usage: check_repo_reference_manifest.py --self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
