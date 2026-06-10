> **EDITOR'S NOTE (captured 2026-06-06 from the owner).** Canonical spec for the GitHub Signal Flywheel / Repo
> Intelligence Agent (governed weekly repo-trend reviewer feeding the hubs). Executed INCREMENTALLY. **DONE +
> proven (flywheel 341):** contracts `schemas/repo_intel/{RepoSnapshot,RepoTrendSignal,RepoIntakeDecision}.v1`
> (registered); 10-repo fixture `fixtures/repo_intel/weekly_github_trend_watch_sample.json`
> (owner_provided_unverified); policies `architecture/repo_{hub_mapping,intake}_policy.json`; engine
> `scripts/repo_intel/engine.py` (snapshot store w/ delta-from-STORED-snapshots · classifier→hub · trend/fit/
> risk scorers · intake-decision engine that NEVER auto-activates · weekly report); proof
> `scripts/check_github_signal_flywheel.py`; weekly report `docs/research/weekly-github-signal-watch.md` +
> `dist/reports/*`. Reuses `scripts/acquisition/github_repo_harvester.py` (live source adapter). Placed in
> `scripts/repo_intel/` (neutral research/intake scope). **QUEUED:** live GitHub adapter wiring; Teleon
> PurposeTasks (purpose.github_signal_watch/snapshot/classifier/...); open-hub candidate outputs (Skill/Tool/
> Harness/Template/Context candidate records); /api/repo-intel + /repo-intel UI; the redteam suite; rubrics;
> fit_scorer depth; similarity/duplicate detection vs the hub registries.

# /workflows /github-signal-flywheel-repo-intelligence-agent
Governed weekly repo-trend reviewer. **Discovery is not trust · stars are not proof · trend ≠ fit ≠ activation.**
Feeds OpenSkillsHub/OpenToolsHub/OpenHarnessHub/OpenContextHub/Shared-Templates/Teleon/Baltor as CANDIDATES only.

## GITHUB SIGNAL FLYWHEEL CLAUSE (carry forward)
Every flywheel checks whether repo-intelligence work is due; light cycles update snapshots + queued
classifications, weekly cycles publish a verified GitHub Signal Watch. Trending repos are discovery inputs only.
A repo cannot become an active skill/tool/harness/template/context/Teleon/Baltor integration without provenance,
classification, duplicate detection, risk/license review, local eval/sandbox where applicable, redteam, and a
promotion decision. Star growth must come from STORED snapshots or be labelled low-confidence/owner-provided.

*(Full PART 0–21 detail is in the owner's message + the proven core above; build the QUEUED items next.)*
