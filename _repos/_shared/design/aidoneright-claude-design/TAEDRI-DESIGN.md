# TAEDRI-DESIGN.md — the complete design + site specification for Taedri

> Paste-ready for Claude design sessions. Parent authority: this family's `DESIGN-BIBLE.md` (shared kit, tokens,
> laws) — where this brief is silent, the family bible wins; where it conflicts with a Taedri rule below, FLAG it,
> never silently override. Product truth as of 2026-07-10: the LIVE service is the capability gateway (remote MCP
> + agent API + `/console`) at taedri.fly.dev serving 557,392 governed candidate primitives. Sections marked
> **[API: exists]** design against real endpoints; **[API: needs]** are specs for endpoints not built yet — design
> them, and treat the listed contract as the build order. No invented screenshots, no fabricated metrics, ever.

## 1 · Brand core

- **Name:** Taedri — acronym of the first law: **T**his **A**lready **E**xists, **D**on't **R**ebuild **I**t.
  Pronounced **TAY-dree**. Wordmark lowercase `taedri`; capital-T "Taedri" in prose; expansion shown on first use.
- **Tagline lockup:** `Taedri — This already exists. Don't rebuild it.`
- **What it is:** the verified-capability retrieval layer for AI coding agents — search, typed edges
  (input→output), deterministic composition, governance receipts — as a remote MCP server + deterministic API.
- **Pitch:** *Your agent rebuilds solved problems every day. Taedri hands it the verified part instead.*
- **Campaign register (marketing copy, never the brand):** "Don't rebuild." · "Stop burning tokens on solved
  problems." · "Retrieve capabilities, not code." · "Already built. Already verified."
- **Voice:** experienced staff engineer — direct, calm, evidence-first, mildly dry, zero hype. Full words always
  (family law): "primitive search," never "prim srch". Numbers only when measured (honest-ledger law).
- **The badge rule (brand asset, not fine print):** every result shows its governance state — a
  `candidate · serves_truth=false` chip until a primitive is promoted. Honesty is the differentiator.

## 2 · Visual identity

- **Logo:** wordmark `taedri`, geometric mono-adjacent sans. Mark concepts (explore ≤3): hexagonal brick with a
  check (verified building block) · return-arrow into a grid (retrieve, don't regenerate). No wheels/robots/✨.
- **Palette (dark-first, WCAG AA both themes):** bg `#0d1117` · surface `#161b22` · border `#30363d` · text
  `#e6edf3` / muted `#8b949e` · **Taedri green** `#2ea043` (hover `#238636`) for verified/primary actions ·
  accent blue `#1f6feb` (links/info) · amber `#9e6a03` (owner-only/guarded) · danger `#da3633` (sparing).
  Light theme derives the same hues on `#ffffff`/`#f6f8fa`. Both themes REQUIRED.
- **Type:** UI = system-ui stack; ALL ids, edge names, JSON, commands = `ui-monospace`. Edge names are a
  first-class element: `input_edge → output_edge` pills on every primitive card.
- **Icons:** outline 1.5px geometric; a consistent 18-icon set for the domain partitions (database, auth, http,
  files, ML, messaging, cloud, observability, ETL, geo/time, testing, algorithms, frontend, NLP, scraping,
  finance, healthcare, general).
- **Motion:** 120–180ms ease-out; one signature moment — results "retrieve" (8px slide-up + fade). Retrieval
  must FEEL faster than generation.

## 3 · Architecture & template system (the "MVC" of this product)

**Law: the API is the only model.** The web app is a CLIENT of the same public API agents use — it never grows
parallel business logic. Layering:

- **Model** = the gateway API (`/v1/*`, `/mcp`) + identity service. All state, limits, billing, governance live
  here. If a page needs data the API lacks, that's an **[API: needs]** item — never a frontend workaround.
- **View** = server-rendered templates + shared-kit components, progressively enhanced with vanilla JS
  (same-origin `fetch`). No SPA framework requirement; no hardcoded hosts (family seam law).
- **Controller** = thin route handlers on the gateway: parse → call the same service functions the API uses →
  render template. Zero business logic in routes.

**Template inheritance (standardized chrome):**
- `base.html` — head (meta/OG/theme), header, footer, toast region, theme toggle.
- Page templates extending base: `marketing.html` (hero + sections) · `docs.html` (sidebar TOC + prose) ·
  `app.html` (authed shell: sidenav + content) · `auth.html` (centered card) · `error.html`.
- **Header (every page):** wordmark → Product · Pricing · Docs · Status ｜ right side logged-out: `Log in` +
  `Get a key` (primary); logged-in: usage meter mini, account menu (Dashboard, Keys, Billing, Logs, Support,
  Log out). Mobile: collapses to sheet menu. Active-page underline.
- **Footer (every page):** 4 columns — Product (Search, Console, Pricing, Status) · Developers (Docs,
  Quickstart, MCP setup, API reference, Changelog) · Company (About, Mission, Support, Contact) · Legal (Terms,
  Privacy, Acceptable use). Bottom row: © AI Done Right · "Taedri — This Already Exists, Don't Rebuild It." ·
  theme toggle · system-status dot (live from `/healthz`).

## 4 · Complete sitemap

**Marketing (public):**
1. `/` Landing — hero lockup + LIVE corpus counter (computed from the API, never typed) + 3-step strip
   (Sign up → Get key → `claude mcp add`) + terminal block (real command) + how-it-works (search → edges →
   compose → receipts) + honesty section (candidate vs verified) + pricing teaser + FAQ. **[API: exists]**
2. `/about` — the story: the name IS the law; the reuse thesis; the honest-numbers stance; the AI Done Right
   family relationship.
3. `/mission` (may merge into /about) — purpose & mission statements: *Purpose: end the rebuilding of solved
   work by AI systems. Mission: make every verified capability retrievable, composable, and governed — so
   agents reason about the novel and retrieve the solved.* Principles list (candidate/truth boundary, lossless
   history, receipts for everything, non-destructive routing).
4. `/pricing` — plan cards from the real `/v1/pricing` (Free $0 · 200 req/day; Pro $29/mo DRAFT · 20,000/day;
   label "introductory pricing" until Stripe is live) + limits meter visual + upgrade CTA + billing FAQ.
   **[API: exists]**
5. `/docs` — shell + pages: Quickstart (signup curl → key → `claude mcp add --transport http taedri
   https://<host>/mcp --header "Authorization: Bearer KEY"`) · The 7 MCP tools · Agent actions (table computed
   from `actions.list`) · Usage & invoices · Rate limits & plans · Owner admin (add/tombstone/reindex/ledgers) ·
   Private primitives · Errors. **[API: exists]**
6. `/support` — searchable FAQ, troubleshooting (401/429/cold-wake), "email support" (support@taedri…), response
   expectations by plan. **[API: n/a]**
7. `/contact` — form (name/email/topic/message) → **[API: needs]** `POST /v1/contact` (rate-limited, writes a
   ticket receipt; NO silent mailto-only page).
8. `/status` — friendly render of `/healthz` + incident notes placeholder. **[API: exists]**
9. `/legal/terms`, `/legal/privacy`, `/legal/acceptable-use` — static; privacy states the receipts model
   plainly (hashes not raw keys; bounded previews; no raw prompt bodies stored).
10. `/changelog` — dated product notes (manual at first). **[shipped 2026-07-10 as `/news` on the gateway:**
    rendered from the single `TAEDRI_NEWS` constant (newest first, shipped-fact-only entries); the landing
    shows a 3-entry digest from the same constant. The rich-site News page renders the same source.**]**

**App (authenticated, `app.html` shell — sidenav: Dashboard · Search · My primitives · Keys · Logs · Billing ·
Settings):**
11. `/login` — email + account secret (identity `login` **[API: exists]**; session cookie wrapper
    **[API: needs]** — today auth is Bearer-key-only; design the session flow: login → short-lived session →
    dashboard; "lost secret" = support flow, no SSO EVER, family law).
12. `/signup` — the golden 60 seconds: email → key + account secret shown ONCE (copy buttons, "hashes only"
    note) → personalized `claude mcp add` with key inlined → inline "run one search now" box → success = a real
    result within a minute. States: success / existing-account / invalid email. **[API: exists]**
13. `/dashboard` — requests-today meter vs plan · month requests · draft invoice card · quick links (connect
    MCP, view logs, upgrade) · corpus counter · latest changelog entry. **[API: exists** via `/v1/usage`**]**
14. `/search` (workbench = evolved `/console`) — search box + result **PrimitiveCards** (title · mono id · edge
    pills · score · domain chip · candidate badge · "view JSON") + tool tabs (get / reuse-guard / compose /
    corpus status) + agent-action runner. Cold-wake skeleton state: "Waking the corpus (557K primitives)…
    ~30–40s". **[API: exists]**
15. `/my-primitives` — the user-provided/saved/PRIVATE layer: list mine (private chips), add (JSONL dropzone +
    per-row validation preview; truth bits force-stripped notice), edit-as-new-version (lossless), tombstone
    (never delete), save/star public primitives into "Saved". Search toggle: "include my private primitives".
    **[API: needs]** — contract: `POST/GET /v1/my/primitives` (tenant-scoped overlay rows with
    `visibility: private|shared`, same force-stripped governance bits), `POST /v1/my/primitives/remove`
    (tombstone), `POST /v1/my/saved {primitive_id}`, and tenant-overlay search inclusion (per-tenant mini-index
    merged at query time, never into the public index). Promotion path private → shared → verified is displayed
    but gated server-side.
16. `/keys` — identity `api-keys/list` **[API: exists]**: prefix-only rows, created/expires/last-used, mint new
    (secret required), revoke (with "agents using it will 401" warning).
17. `/logs` — user logs & monitoring: the tenant's OWN request receipts — time, kind (mcp:tool / agent:action),
    result count, duration, metered tokens-equivalent; filter by day/kind; CSV/JSON export; anomaly strip
    (spike vs plan). **[API: needs]** `GET /v1/logs?since=&kind=` = tenant-scoped receipts (the data already
    exists in metering receipts keyed by key_id — expose, filtered, paginated).
18. `/billing` — plan card, upgrade/downgrade, draft invoice history, payment method (Stripe element once
    STRIPE_API_KEY is live; until then show draft invoices + "payments not yet enabled" honesty). **[API:
    exists (draft invoices) / needs (Stripe checkout wrapper)]**
19. `/settings` — email display, account secret rotation **[API: needs]**, data export (my primitives + my
    receipts) **[API: needs]**, delete-account policy text (tombstone semantics, lossless law — state it
    honestly).

**Owner/admin (amber-accented, owner chip, `OH_SAAS_OWNER_KEY`):**
20. `/admin` — corpus overlay add (dropzone) · tombstone · reindex (background progress + "serves on next wake"
    honesty) · ledger export · tenant overview (counts only). **[API: exists]**

## 5 · Component library (extend the family kit; never fork)

`PrimitiveCard` · `EdgePill` (mono, input→output) · `DomainChip` (18 partitions) · `CandidateBadge`
(candidate/verified/private states) · `KeyReveal` (show-once + copy + prefix-after) · `SecretReveal` (same for
account secret) · `UsageMeter` (today/limit + month) · `PlanCard` · `TerminalBlock` (copy button; real commands
only) · `ReceiptRow`/`LogTable` (filterable, exportable) · `GuardBanner` (owner-only / billing-gated) ·
`LiveCounter` (computed stats) · `EmptyState` (illustrated, action-forward) · `SkeletonSearch` (cold-wake) ·
`Toast` · `ConfirmModal` (typed-confirm for tombstone/revoke) · `Dropzone` (JSONL validate-preview) ·
`StatusDot` (healthz). Every component: light+dark, keyboard path, visible focus, AA contrast, empty/loading/
error states designed — not implied.

## 6 · Best practices (acceptance criteria, enforced at review)

- **Responsive:** 360 / 768 / 1024 / 1440 breakpoints; app shell collapses sidenav → bottom tabs on mobile;
  tables become cards.
- **Accessibility:** WCAG 2.1 AA both themes; full keyboard coverage; aria-labels on icon buttons; focus-visible
  rings; prefers-reduced-motion honored; error text not color-only.
- **Performance:** system fonts (no webfont blocking), LCP < 2.5s on landing, zero third-party scripts on
  authed pages, JS progressive (pages readable with JS off except the workbench).
- **Security/privacy UX:** keys/secrets shown once then prefix-only; no secrets in URLs or localStorage beyond
  the console's explicit opt-in; CSP same-origin; analytics only with consent banner (family: consent = gate 0).
- **SEO/meta:** unique titles (`Page — Taedri`), meta descriptions, OG card (dark lockup), canonical URLs,
  sitemap.xml, robots.txt; docs pages indexed, app pages noindex.
- **States law:** every screen ships loading / empty / error / 401 / 429 / cold-wake designs. 429 = meter-full
  state + one-click upgrade, never a dead end.
- **Copy law:** computed numbers only (corpus size, limits, counts from the API); no token-savings percentages
  until a measured benchmark ships; "candidate"/"verified" used precisely; first-use expansion of the name.

## 7 · Deliverables checklist for a Claude design session

1. `base.html` chrome: header (both auth states) + footer + theme toggle — desktop & mobile.
2. Landing (dark+light, desktop+mobile). 3. About/Mission. 4. Pricing. 5. Docs shell + Quickstart.
6. Signup golden-60-seconds flow (all states) + Login. 7. Dashboard. 8. Search workbench (PrimitiveCards +
tool tabs + cold-wake state). 9. My-primitives (list/add/validate/tombstone/saved). 10. Keys. 11. Logs.
12. Billing (draft-invoice mode + Stripe-live mode). 13. Admin (amber). 14. Error/429/401/empty/skeleton set.
15. Component spec sheet (§5). 16. Wordmark/logo (≤3 directions).
**Acceptance:** AA both themes · full words · NO SSO · candidate badges on every result · real copyable
commands · computed numbers only · every **[API: needs]** item listed in the handoff as a build ticket with its
contract, never silently mocked as if live.

## 8 · Page-by-page functional requirements (every element, button, and state)

Format per page: **Purpose · Data · Elements (button → action → endpoint → result) · States · Acceptance.**
Endpoint names are the contract; **[needs]** = build ticket, design it but wire to the listed contract only.

### 8.1 `/` Landing
- **Data:** `GET /healthz` (status dot, corpus flag), corpus count via `primitive_corpus_status` (cached 5 min).
- **Elements:** `Get a key` (primary) → `/signup` · `Log in` → `/login` · `Read the docs` → `/docs` ·
  TerminalBlock copy button (copies real `claude mcp add` line; toast "copied") · pricing teaser `See pricing`
  → `/pricing` · FAQ accordions (5–8 items, single-open).
- **States:** status dot green/amber from healthz; corpus counter skeleton until loaded; JS-off = static copy
  with "live numbers unavailable".
- **Acceptance:** zero hardcoded counts; hero readable at 360px; LCP < 2.5s.

### 8.2 `/signup` (golden 60 seconds)
- **Data:** `POST /v1/signup {email}` → `{api_key, account_secret, plan, requests_per_day}`.
- **Elements:** email input (validate on blur, RFC-basic) · `Create my key` (primary; disabled until valid;
  loading spinner ≤10s) · KeyReveal (mono, blurred until `Reveal`, `Copy` per field, "shown once — we store
  only hashes" note) · SecretReveal (same pattern; label "Account secret — needed to log in and mint more
  keys") · `I saved both` checkbox gating `Continue` → `/dashboard` · personalized TerminalBlock (key inlined,
  copy) · inline try-it search box (1 query, renders first PrimitiveCard).
- **States:** success · existing-account (message + `Log in instead`) · invalid email · rate-limited signup
  (friendly wait) · server error (retry).
- **Acceptance:** key/secret never in URL, localStorage optional and opt-in labeled; user reaches a real
  search result in under 60s on broadband.

### 8.3 `/login`
- **Data:** identity `POST login {identifier, secret}` → session **[needs: session-cookie wrapper
  `POST /v1/session` → httpOnly cookie, 60-min TTL, sliding]**.
- **Elements:** email input · secret input (show/hide toggle) · `Log in` (primary) · `Lost your secret?` →
  `/support#lost-secret` (no reset self-serve v1; copy explains why honestly) · NO SSO buttons (family law).
- **States:** wrong-credentials (generic message, no user enumeration) · throttled (identity throttle surfaces
  retry-after) · success → `/dashboard`.

### 8.4 `/dashboard`
- **Data:** `GET /v1/usage` (requests_today, requests_per_day, requests_month, month_statement, draft_invoice,
  plan) · changelog head (static).
- **Elements:** UsageMeter (today/limit; amber ≥80%, danger =100% + `Upgrade` inline) · month card (requests +
  metered USD) · invoice card (`status: draft` chip, total, `View billing` → `/billing`) · quick actions:
  `Connect Claude Code` (opens MCP modal with copyable config) · `Open workbench` → `/search` · `View logs` →
  `/logs` · corpus LiveCounter.
- **States:** fresh-account empty state ("Make your first request — open the workbench"); usage fetch error
  banner with retry.

### 8.5 `/search` (workbench)
- **Data:** `POST /mcp` tools/call per tab; `POST /v1/agent` for action runner.
- **Elements:** search input (`/` focuses; Enter submits) · limit select (5/10/25) · include-mine toggle
  **[needs /v1/my search inclusion]** · result PrimitiveCards: `Copy id` · `View JSON` (drawer) · `Get`
  (tools/call primitive_get, payload toggle "include full payload") · `Save` **[needs /v1/my/saved]** ·
  tabs: Search · Lookup (id input + Get) · Reuse guard (message textarea → find_reuse; QUIET state designed:
  "No existing capability found — genuinely novel") · Compose (request → route view: signature steps + edge
  pills; "route found/not found" states) · Corpus (corpus_status render) · Agent runner (action select from
  `actions.list`, args JSON editor with validation, `Run`).
- **States:** cold-wake skeleton ("Waking the corpus (557K primitives)… ~30–40s" + progress shimmer) · empty
  results (query tips) · 429 meter-full (inline `Upgrade`) · JSON parse error in args editor (inline, precise).
- **Acceptance:** every result carries CandidateBadge + DomainChip + EdgePills; keyboard: tab through cards,
  Enter opens JSON drawer, Esc closes.

### 8.6 `/my-primitives` **[needs: /v1/my/* contract from §4.15]**
- **Data:** `GET /v1/my/primitives` (mine + saved lists) · `POST /v1/my/primitives {cards[]}` ·
  `POST /v1/my/primitives/remove {primitive_id}` · `POST /v1/my/saved {primitive_id}`.
- **Elements:** tabs `Mine` / `Saved` · `Add primitives` (primary) → Dropzone modal: JSONL paste/file →
  per-row validation table (id present? title? edges? → green check / precise error per row; "governance bits
  are force-stripped server-side" note) → `Upload N valid rows` · row actions per primitive: `View` ·
  `New version` (prefilled editor; explains lossless append) · `Tombstone` (ConfirmModal: type the id;
  copy: "tombstoned, never deleted — history is preserved and this cannot be undone from the UI") ·
  visibility chip `private` (v1 fixed; `shared` shown disabled with "promotion coming" tooltip) · Saved tab:
  unsave button.
- **States:** empty Mine ("Your agents can retrieve YOUR solved work too — add your first primitive") · upload
  partial-failure (valid rows accepted, failures listed) · quota banner if a cap exists.

### 8.7 `/keys`
- **Data:** identity `GET api-keys/list` · mint via `login → api-keys/mint` **[needs: gateway wrapper
  `POST /v1/keys {secret, scopes?}`]** · revoke **[needs: `POST /v1/keys/revoke {key_id, secret}`]**.
- **Elements:** key table (prefix mono, created, expires, last-used, scopes) · `Mint new key` (secret re-entry
  modal → KeyReveal once) · per-row `Revoke` (ConfirmModal: "Agents using this key will start receiving 401
  immediately") · MCP config helper per key (copyable with prefix placeholder — never the raw key after
  first reveal).
- **States:** single-key empty-ish state; revoked rows collapse to a muted history section (lossless display).

### 8.8 `/logs`
- **Data:** **[needs `GET /v1/logs?since&kind&page`]** — tenant-scoped receipts: ts, kind (mcp:tool /
  agent:action), result_count, duration_ms, tokens-equivalent.
- **Elements:** LogTable (sortable ts desc default) · filters: date range preset (today/7d/30d), kind
  multi-select, key select · `Export CSV` / `Export JSON` (client-side from fetched pages, labeled row cap) ·
  anomaly strip (today vs 7-day mean; informational only).
- **States:** empty ("No requests yet — connect your agent"), partial (pagination `Load more`), export toast.

### 8.9 `/billing`
- **Data:** `GET /v1/usage` (plan, draft_invoice) · `POST /v1/upgrade {plan}` · Stripe element
  **[needs checkout wrapper once STRIPE_API_KEY live]**.
- **Elements:** current PlanCard (limits, price, `draft pricing` chip until Stripe live) · other-plan card with
  `Upgrade` / `Downgrade` (ConfirmModal shows delta + effective-now note) · invoice history list (month,
  total, `status: draft` chip, `View` drawer with line items) · payment method section: pre-Stripe state =
  GuardBanner "Payments are not enabled yet — plans are recorded, nothing is charged" (honesty law).
- **States:** upgrade success toast + meter refresh; downgrade-below-usage warning.

### 8.10 `/settings`
- **User data shown:** email (display only v1) · account created date · plan · realm.
- **Elements:** `Rotate account secret` **[needs `POST /v1/secret/rotate {old_secret}` → SecretReveal once]** ·
  `Export my data` **[needs `GET /v1/export` → JSON: profile, keys (projections), my primitives, my receipts]**
  · `Delete account` section: v1 = policy text only ("accounts deactivate; records are tombstoned, never
  erased — the lossless law") + `Contact support` link · theme preference (local) · consent toggle for
  analytics (default off).
- **Acceptance:** every destructive/irreversible action uses ConfirmModal with typed confirmation; every
  secret display uses the show-once pattern.

### 8.11 `/admin` (owner)
- **Data/actions [API: exists]:** `POST /v1/admin/primitives` · `POST /v1/admin/primitives/remove` ·
  `POST /v1/admin/reindex` + `GET` status · `GET /v1/admin/ledgers`.
- **Elements:** owner-key field (session-only, never persisted) · corpus Dropzone (same validation table as
  8.6, batch ≤10,000 note) · tombstone input+confirm · `Reindex now` (disabled while running; status poll
  chip: running/done/error + indexed_cards; "serves on next machine wake" honesty banner) · `Export ledgers`
  (JSON download) · tenant overview tiles (counts only, no PII).
- **States:** 403 non-owner (clear, unstyled-data-free) · reindex error state with error string.

### 8.12 Support/Contact/About/Legal/Status/Changelog
- `/support`: FAQ search (client-side), sections (Keys & auth · Limits & plans · MCP setup · Cold starts ·
  Lost secret), each answer deep-linkable; `Still stuck? Contact us` → `/contact`.
- `/contact`: fields name/email/topic(select: support·billing·security·partnership)/message(≤2000 chars) ·
  `Send` → **[needs `POST /v1/contact`]** → success state with ticket id receipt; abuse-rate-limited.
- `/about` + `/mission`: static prose per §4; team section optional later.
- `/legal/*`: static; last-updated stamps; privacy explains receipts/hashing/no-raw-bodies concretely.
- `/status`: healthz render + component list (gateway, identity, corpus, billing seam) with StatusDots.
- `/changelog`: dated entries, newest first, RSS link later.

## 9 · User data model (what the product stores about a tenant — the privacy page mirrors this)

- **Account (identity service):** account_id, email identifier, secret HASH, onboarding state, created_at.
- **Keys (identity service):** key_id, key HASH, prefix (display), scopes, created/expires/last_used/revoked.
- **Tenant meta (gateway):** account_id → plan, created; email digest only.
- **Metering receipts:** ts, key_id, kind, request/response byte counts (token-equivalents), model_class —
  NO raw request bodies, NO raw prompts beyond bounded previews in usage ledgers.
- **My primitives [needs]:** tenant-scoped overlay rows (cards + tombstones + saved ids), governance bits
  forced candidate/serves_truth=false, versions append-only.
- **Never stored:** raw keys, raw secrets, payment card data (Stripe-side only), SSO identities (none exist).

## 10 · Complete user-action inventory (action → endpoint → guard → receipt)

| Action | Endpoint | Guard | Receipt |
|---|---|---|---|
| Sign up | POST /v1/signup | email validity, signup throttle | identity audit + account record |
| Log in | POST /v1/session **[exists 2026-07-10]** | secret hash match, throttle | identity audit |
| Search / MCP tool call | POST /mcp | Bearer key, plan rate limit | invocation receipt |
| Agent action | POST /v1/agent | Bearer + tenant allowlist | invocation receipt |
| View usage | GET /v1/usage | Bearer | — |
| Upgrade/downgrade | POST /v1/upgrade | Bearer | tenant meta + invoice draft |
| Contribute to corpus | POST /v1/contribute **[exists 2026-07-10]** | Bearer or session; batch cap; identity fields stripped; NOT rate-gated (it is the escape hatch at the limit) | anonymized contribution row (candidate-only) + same-day bonus grant |
| Mint key | /v1/keys **[needs]** | account secret re-entry | identity audit |
| Revoke key | /v1/keys/revoke **[needs]** | secret + confirm modal | identity audit |
| Add private primitives | /v1/my/primitives **[exists 2026-07-10]** | Bearer, batch cap, validation | overlay append |
| Tombstone mine | /v1/my/primitives/remove **[exists 2026-07-10]** | typed confirm | tombstone row |
| Save public primitive | /v1/my/saved **[needs]** | Bearer | saved row |
| View logs | GET /v1/logs **[exists 2026-07-10]** | Bearer (own key_ids only) | — |
| Rotate secret | /v1/secret/rotate **[needs]** | old secret | identity audit |
| Export data | GET /v1/export **[needs]** | Bearer + secret | export receipt |
| Contact | POST /v1/contact **[needs]** | rate limit | ticket receipt |
| Owner: add/tombstone/reindex/ledgers | /v1/admin/* | OWNER key | overlay/tombstone/reindex receipts |

**Rule:** any UI element not in this inventory is decoration; any inventory row without a designed screen
state is an incomplete deliverable. Every **[needs]** endpoint above is the build backlog, in priority order:
keys mint/revoke wrappers → secret rotate → export → contact → saved primitives.

### 10.1 · The contributor bonus (share-to-continue) — owner directive 2026-07-10

*"Free or discounted tier if people share their data or primitives into the large corpus … shown as a bonus
after someone has reached their limit (continue using this by submitting anonymized data…)."* Shipped shape:

- **The 429 IS the offer surface:** every rate-limit response carries `continue_free` naming
  `POST /v1/contribute`, the per-card bonus, and the daily cap — the user meets the tier exactly when it
  matters. The landing page pitches the same lane ("Hit your daily limit? Share, and keep going").
- **Amounts live in ONE place** (`capability_saas_gateway.CONTRIBUTOR_BONUS_REQUESTS_PER_ACCEPTED_CARD` /
  `CONTRIBUTOR_BONUS_DAILY_CAP`, DRAFT owner-confirmable, currently +5/card capped +200/day); every surface
  (429, landing, pricing JSON) renders from the constants.
- **Anonymized + candidate-only:** stored rows carry a 16-hex contributor digest (never email/account id;
  identity-shaped fields stripped by exact-name denylist) and `candidate=true, serves_truth=false` in
  `corpus_contributions.jsonl` — owner review promotes; sharing never injects into the serving corpus.
- **A standing discounted TIER (vs the per-day bonus) stays a pricing decision** — draft in
  `billing_plane.PLANS` when the owner confirms terms.

## 11 · The composition layer — groups, frameworks, remixers, integrators, networks (owner-directed 2026-07-10)

Above the flat card corpus sits a composition layer (`scripts/primitive_groups_frameworks_and_remixers.py`
+ `scripts/primitive_networks_and_grid_search.py`), each concept a first-class receipt-backed record family
behind a ZOO table (extend = one row, never a rewrite). All rows `candidate=true, serves_truth=false`; ids
minted only by `canonical_id`. Exposed on the agent API as six read-only actions (in the public trial-key
allowlist), so the `/console` workbench and the Kaggle notebook demo them against the same public API:

| Concept | Agent action | What it is |
|---|---|---|
| **Groups** | `composition.groups` | Computed typed collections (by family / pack / consumed-edge / produced-edge); `by_family` partitions losslessly. |
| **Frameworks** | `composition.frameworks` | Ordered stage scaffolds (governed-scraping 9-stage, entity-resolution 6-stage) instantiated per scope with **honest coverage gaps** — an unfilled stage is listed, never an invented member. |
| **Remixers** | `composition.remix` | Deterministic card→variant transforms (edge-vocabulary-align — the chainability lever — + jurisdiction/cadence swaps); each variant carries lineage `{parent, transform}`. The LLM remix is a declared seam, never run in the 0-token lane. |
| **Integrators** | `composition.integrate` | Compile a composite primitive through an **exact** edge route (reusing the one runtime composer); honest refusal receipt when no route exists. |
| **Networks** | `network.list` | A task as an ordered **edge-type chain** whose steps are **slots of competing primitives**, with computed grid sizes (the product of the slot sizes). |
| **Grid search** | `network.grid_search` | Evaluate every combination (or a deterministic strided sample past the cap) under a scorer zoo (proxy-context-tokens / blackbox-tokens / declared-cost runnable; execution-efficiency a declared harness seam), returning **non-destructive** per-scorer winners + the Pareto front. Different scorers can crown different winners. |

**Design surfaces to build against these [API: exists]:** a **Groups** browser (chips per builder, member
counts, edge signatures); a **Framework** view (stage rail with filled/gap badges per scope); a **Network
grid** visual — the star of this layer — showing the step lattice (columns = steps A/B/C…, rows = competing
primitives per slot) with the winning path highlighted per scorer and the Pareto front marked, every path
wearing its `candidate` badge. The honesty rule holds throughout: rankings are candidate signals, losers are
shown as preserved fallbacks, and an unfillable slot renders as a coverage gap, never a hidden failure.
