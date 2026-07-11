# Migration plan — monorepo → managed multi-repo

22 repos. Every repo installs the shared **`aidoneright-devkit`** (standards + contracts + gates) instead of copying them. Splitting is history-preserving (`git subtree split`) so the working monorepo never breaks — do it repo-by-repo, in order.

## Order + commands

### aidoneright-dev-rules-context  (dev-rules-context · rules_and_context)
- code: `_repos/dev-rules-context`  ·  depends on: aidoneright-devkit
```bash
git subtree split --prefix=_repos/dev-rules-context -b split/aidoneright-dev-rules-context      # history-preserving extract of _repos/dev-rules-context
# create empty GitHub repo aidoneright-dev-rules-context on the new org account, then:
git push git@github.com:<org>/aidoneright-dev-rules-context.git split/aidoneright-dev-rules-context:main
```

### aidoneright-svc-platform  (shared-backend-components · microservice)
- code: `services/platform`  ·  depends on: aidoneright-devkit
```bash
git subtree split --prefix=services/platform -b split/aidoneright-svc-platform      # history-preserving extract of services/platform
# create empty GitHub repo aidoneright-svc-platform on the new org account, then:
git push git@github.com:<org>/aidoneright-svc-platform.git split/aidoneright-svc-platform:main
```

### aidoneright-svc-scheduler  (shared-backend-components · microservice)
- code: `services/scheduler`  ·  depends on: aidoneright-devkit
```bash
git subtree split --prefix=services/scheduler -b split/aidoneright-svc-scheduler      # history-preserving extract of services/scheduler
# create empty GitHub repo aidoneright-svc-scheduler on the new org account, then:
git push git@github.com:<org>/aidoneright-svc-scheduler.git split/aidoneright-svc-scheduler:main
```

### aidoneright-svc-worker  (shared-backend-components · microservice)
- code: `services/worker`  ·  depends on: aidoneright-devkit
```bash
git subtree split --prefix=services/worker -b split/aidoneright-svc-worker      # history-preserving extract of services/worker
# create empty GitHub repo aidoneright-svc-worker on the new org account, then:
git push git@github.com:<org>/aidoneright-svc-worker.git split/aidoneright-svc-worker:main
```

### aidoneright-aidevobserver-backend  (aidevobserver · backend)
- code: `scripts/observer (TBD extract)`  ·  depends on: aidoneright-devkit
```bash
# aidevobserver-backend: code_path 'scripts/observer (TBD extract)' not yet a clean subdir — extract/create it first
```

### aidoneright-api-endpoint-wrappers  (api-endpoint-wrappers · dev_tool)
- code: `_repos/api-endpoint-wrappers`  ·  depends on: aidoneright-devkit
```bash
git subtree split --prefix=_repos/api-endpoint-wrappers -b split/aidoneright-api-endpoint-wrappers      # history-preserving extract of _repos/api-endpoint-wrappers
# create empty GitHub repo aidoneright-api-endpoint-wrappers on the new org account, then:
git push git@github.com:<org>/aidoneright-api-endpoint-wrappers.git split/aidoneright-api-endpoint-wrappers:main
```

### aidoneright-baltor-backend  (baltor · backend)
- code: `src/baltor`  ·  depends on: aidoneright-devkit
```bash
git subtree split --prefix=src/baltor -b split/aidoneright-baltor-backend      # history-preserving extract of src/baltor
# create empty GitHub repo aidoneright-baltor-backend on the new org account, then:
git push git@github.com:<org>/aidoneright-baltor-backend.git split/aidoneright-baltor-backend:main
```

### aidoneright-business-context  (business-context · context)
- code: `_repos/business-context`  ·  depends on: aidoneright-devkit
```bash
git subtree split --prefix=_repos/business-context -b split/aidoneright-business-context      # history-preserving extract of _repos/business-context
# create empty GitHub repo aidoneright-business-context on the new org account, then:
git push git@github.com:<org>/aidoneright-business-context.git split/aidoneright-business-context:main
```

### aidoneright-context-injection  (context-injection · dev_tool)
- code: `_repos/context-injection`  ·  depends on: aidoneright-devkit
```bash
git subtree split --prefix=_repos/context-injection -b split/aidoneright-context-injection      # history-preserving extract of _repos/context-injection
# create empty GitHub repo aidoneright-context-injection on the new org account, then:
git push git@github.com:<org>/aidoneright-context-injection.git split/aidoneright-context-injection:main
```

### aidoneright-edge-graph-generator  (edge-graph-generator · meta_tool)
- code: `_repos/edge-graph-generator`  ·  depends on: aidoneright-devkit
```bash
git subtree split --prefix=_repos/edge-graph-generator -b split/aidoneright-edge-graph-generator      # history-preserving extract of _repos/edge-graph-generator
# create empty GitHub repo aidoneright-edge-graph-generator on the new org account, then:
git push git@github.com:<org>/aidoneright-edge-graph-generator.git split/aidoneright-edge-graph-generator:main
```

### aidoneright-fundraising  (fundraising · context)
- code: `_repos/fundraising`  ·  depends on: aidoneright-devkit
```bash
git subtree split --prefix=_repos/fundraising -b split/aidoneright-fundraising      # history-preserving extract of _repos/fundraising
# create empty GitHub repo aidoneright-fundraising on the new org account, then:
git push git@github.com:<org>/aidoneright-fundraising.git split/aidoneright-fundraising:main
```

### aidoneright-openhubforai-backend  (openhubforai · backend)
- code: `src/openhubforai`  ·  depends on: aidoneright-devkit
```bash
git subtree split --prefix=src/openhubforai -b split/aidoneright-openhubforai-backend      # history-preserving extract of src/openhubforai
# create empty GitHub repo aidoneright-openhubforai-backend on the new org account, then:
git push git@github.com:<org>/aidoneright-openhubforai-backend.git split/aidoneright-openhubforai-backend:main
```

### aidoneright-pitch-decks  (pitch-decks · context)
- code: `_repos/pitch-decks`  ·  depends on: aidoneright-devkit
```bash
git subtree split --prefix=_repos/pitch-decks -b split/aidoneright-pitch-decks      # history-preserving extract of _repos/pitch-decks
# create empty GitHub repo aidoneright-pitch-decks on the new org account, then:
git push git@github.com:<org>/aidoneright-pitch-decks.git split/aidoneright-pitch-decks:main
```

### aidoneright-scraping  (scraping · dev_tool)
- code: `_repos/scraping`  ·  depends on: aidoneright-devkit
```bash
git subtree split --prefix=_repos/scraping -b split/aidoneright-scraping      # history-preserving extract of _repos/scraping
# create empty GitHub repo aidoneright-scraping on the new org account, then:
git push git@github.com:<org>/aidoneright-scraping.git split/aidoneright-scraping:main
```

### aidoneright-teleon-backend  (teleon · backend)
- code: `src/teleon`  ·  depends on: aidoneright-devkit
```bash
git subtree split --prefix=src/teleon -b split/aidoneright-teleon-backend      # history-preserving extract of src/teleon
# create empty GitHub repo aidoneright-teleon-backend on the new org account, then:
git push git@github.com:<org>/aidoneright-teleon-backend.git split/aidoneright-teleon-backend:main
```

### aidoneright-yc-applications  (yc-applications · context)
- code: `_repos/yc-applications`  ·  depends on: aidoneright-devkit
```bash
git subtree split --prefix=_repos/yc-applications -b split/aidoneright-yc-applications      # history-preserving extract of _repos/yc-applications
# create empty GitHub repo aidoneright-yc-applications on the new org account, then:
git push git@github.com:<org>/aidoneright-yc-applications.git split/aidoneright-yc-applications:main
```

### aidoneright-aidevobserver-extension  (aidevobserver · client)
- code: `TBD`  ·  depends on: aidoneright-devkit, aidevobserver-backend
```bash
# aidevobserver-extension: code_path 'TBD' not yet a clean subdir — extract/create it first
```

### aidoneright-aidevobserver-frontend  (aidevobserver · frontend)
- code: `web/aidevobserver`  ·  depends on: aidoneright-devkit, aidevobserver-backend
```bash
git subtree split --prefix=web/aidevobserver -b split/aidoneright-aidevobserver-frontend      # history-preserving extract of web/aidevobserver
# create empty GitHub repo aidoneright-aidevobserver-frontend on the new org account, then:
git push git@github.com:<org>/aidoneright-aidevobserver-frontend.git split/aidoneright-aidevobserver-frontend:main
```

### aidoneright-parent-frontend  (aidoneright · frontend)
- code: `web/context-is-everything`  ·  depends on: aidoneright-devkit
```bash
git subtree split --prefix=web/context-is-everything -b split/aidoneright-parent-frontend      # history-preserving extract of web/context-is-everything
# create empty GitHub repo aidoneright-parent-frontend on the new org account, then:
git push git@github.com:<org>/aidoneright-parent-frontend.git split/aidoneright-parent-frontend:main
```

### aidoneright-baltor-frontend  (baltor · frontend)
- code: `web/baltor`  ·  depends on: aidoneright-devkit, baltor-backend
```bash
git subtree split --prefix=web/baltor -b split/aidoneright-baltor-frontend      # history-preserving extract of web/baltor
# create empty GitHub repo aidoneright-baltor-frontend on the new org account, then:
git push git@github.com:<org>/aidoneright-baltor-frontend.git split/aidoneright-baltor-frontend:main
```

### aidoneright-openhubforai-frontend  (openhubforai · frontend)
- code: `web/openhubforai`  ·  depends on: aidoneright-devkit, openhubforai-backend
```bash
git subtree split --prefix=web/openhubforai -b split/aidoneright-openhubforai-frontend      # history-preserving extract of web/openhubforai
# create empty GitHub repo aidoneright-openhubforai-frontend on the new org account, then:
git push git@github.com:<org>/aidoneright-openhubforai-frontend.git split/aidoneright-openhubforai-frontend:main
```

### aidoneright-teleon-frontend  (teleon · frontend)
- code: `web/teleon`  ·  depends on: aidoneright-devkit, teleon-backend
```bash
git subtree split --prefix=web/teleon -b split/aidoneright-teleon-frontend      # history-preserving extract of web/teleon
# create empty GitHub repo aidoneright-teleon-frontend on the new org account, then:
git push git@github.com:<org>/aidoneright-teleon-frontend.git split/aidoneright-teleon-frontend:main
```

## After each extract
1. In the new repo, `pip install -e` (or workspace-link) the shared `aidoneright-devkit`.
2. Run the inherited gates (`run_proofs`) — green before you push.
3. Rewrite any `src.<x>` imports to the package name; leave a compat shim during transition.

