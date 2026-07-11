#!/usr/bin/env bash
# scripts/split_repos_for_github.sh — split each _repos/<repo> into its OWN standalone branch (files at the
# branch root, with history) so it can be pushed to a fresh GitHub repo — the "one repo per surface" migration.
#
# This is the CLEAN way to leave the monorepo (proven: a working monorepo can't have an empty root because
# ~267 proofs enforce the root layout; the split repos get the empty-root goal for free — each component's code
# sits at ITS repo root, where paths resolve without the compat symlinks). Idempotent: re-run to refresh a branch.
#
#   scripts/split_repos_for_github.sh                 # split every repo into split/<repo>
#   scripts/split_repos_for_github.sh aidevobserver   # split one
#   # then, per repo, push to the new account:
#   #   git push git@github.com:<new-org>/<repo>.git split/<repo>:main
set -euo pipefail
cd "$(dirname "$0")/.."

# every _repos/<owner> that owns tracked files becomes a repo; _shared is a dependency others vendor, not a surface
REPOS=("aidevobserver" "aidoneright" "baltor" "openhubforai" "teleon" "dev-rules-context" "shared-backend-components")
[ $# -gt 0 ] && REPOS=("$@")

echo "Splitting ${#REPOS[@]} repo(s) — each becomes split/<repo> (files at root, own history):"
for repo in "${REPOS[@]}"; do
  prefix="_repos/${repo}"
  if [ ! -d "$prefix" ]; then echo "  SKIP ${repo}: ${prefix} missing"; continue; fi
  n=$(git ls-files "$prefix" | wc -l | tr -d ' ')
  # -q on subtree isn't supported everywhere; route the progress spew to /dev/null, keep the result.
  GIT_LFS_SKIP_SMUDGE=1 git -c core.hooksPath=/dev/null subtree split -P "$prefix" -b "split/${repo}" >/dev/null 2>&1 || {
    git branch -D "split/${repo}" >/dev/null 2>&1 || true
    GIT_LFS_SKIP_SMUDGE=1 git -c core.hooksPath=/dev/null subtree split -P "$prefix" -b "split/${repo}" >/dev/null 2>&1
  }
  root_top=$(git ls-tree --name-only "split/${repo}" | tr '\n' ' ')
  echo "  ✓ split/${repo}  (${n} files; root: ${root_top})"
  echo "      push:  git push <new-remote-for-${repo}> split/${repo}:main"
done
echo
echo "Cross-repo dependencies (each repo's interface.json + EDGES.md declare them) are resolved on the new"
echo "account by: (a) shared-backend-components published as a package the others depend on, or (b) vendoring"
echo "_repos/_shared into each. See _repos/MIGRATION-STATUS.md."
