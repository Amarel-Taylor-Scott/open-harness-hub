# repo_reference/ — external repos cloned for offline study

These are third-party repositories cloned **for reference/study only**. The working-tree clones are
**git-ignored and NEVER republished** — several carry copyleft (AGPL/GPL) or unstated licenses, and
vendoring them would violate both their licenses and our own clean-room discipline (we *learn from*
them; we do not ship their code).

- **What's here + how to govern each:** `architecture/repo_reference_manifest.json` (tracked) — the
  canonical record: slug, exact cloned commit SHA, license, our disposition, and the governed seed(s)
  we distilled from each.
- **Re-clone (after a fresh checkout):**
  `git clone --depth 1 https://github.com/<slug> repo_reference/<name> && git -C repo_reference/<name> checkout <cloned_sha>`
- **What we learned → built:** each repo's lesson is implemented clean-room as a governed capability
  seed in `src/teleon/seeds/` (drop-in only for clean-permissive licenses; technique-only otherwise),
  gated by `scripts/check_capability_seeds.py`. The DueCare repo (`gemma4_comp`) is the **template** we
  generalize across professions in `src/teleon/seeds/profession_capability_seeder.py`.

Only this README is tracked inside `repo_reference/`; everything else stays local.
