# Browser & Web-Ingestion Safety and Compliance

> The read-only-by-default safety rail for every browser/ingestion lane in this repo. It is enforced in code,
> not just documented: `browser_control.safety` (the single policy surface) delegates to the shipped harness
> (`scripts.primitive_browser_control_harness`) so there is ONE robots policy, ONE side-effect ladder, and ONE
> secret redactor. Every adapter obeys it; the self-tests prove the gates bite. Candidate-only layer
> (`serves_truth=false`).

## The core rules (owner spec 2026-07-08)

1. **READ-ONLY by default.** An act command (click/fill/press/submit) is REFUSED unless side effects are
   explicitly enabled for the session. Fetch/parse/crawl/extract are read-only by construction.
2. **Human confirmation for writes.** Even with side effects enabled, any level `>= write` on the ladder emits
   `requires_confirmation` and is NEVER auto-executed.
3. **Never defeat a control.** No solving/bypassing a CAPTCHA, no defeating a paywall/login, no using another
   user's auth/session without explicit consent.
4. **Never submit a form** for real (the fixtures' submit routes are no-ops; probes never submit).
5. **Secrets are redacted** before anything is logged or persisted (single redactor: harness `redact_secrets`).
6. **Env keys are presence-only** — a key's *presence* may be reported (`available_with_credentials`); its
   *value* is never read into a record, printed, or logged.
7. **No raw bodies / no PII.** Store handles, digests, bounded text, and extracted structured units — never the
   raw page body, never real PII.

## The side-effect ladder (single source: `SIDE_EFFECT_LEVELS`)

```
read_only  <  read  <  write_possible  <  write  <  regulated  <  money_movement
└─ auto-allowed when RO ┘   └─ executes if       └────── requires explicit HUMAN confirmation ──────┘
                              side effects on ┘
```

`browser_control.safety.side_effect_confirmation_gate(level, allow_side_effects, confirmed)` returns a DECISION
(`execute` / `requires_confirmation` / `verdict`) and **never executes anything** itself. Verdicts:
`refused_read_only` (default) · `gated_pending_confirmation` (`>= write`, unconfirmed) ·
`gated_confirmed_execute` · `gated_executed` · `invalid_level`.

## robots.txt

- Every fetch/crawl consults `robots.txt` via `safety.robots_gate(url, fetch=…, ua=…)` → the harness
  `browser_respect_robots_policy`. A `Disallow` blocks the URL — it is **never fetched** (recorded as
  `robots_disallow` / `skipped_robots`). Absent/unreadable robots ⇒ allowed (standard crawler convention).
- `FetchAdapter` and `CrawlerAdapter` respect robots by default; the `ingestion_self_test` mutation gate proves
  that flipping robots from `Disallow` to `Allow-all` is what changes whether a page is captured — the gate does
  real work.

## Rate limiting / politeness

- A per-domain throttle (`harness.RateLimiter`, injected clock) enforces a minimum interval between requests to
  the same domain; over-budget requests are **skipped** (`rate_limited_domain` / `skipped_rate_limited`), never
  queued into a hammer.
- Live probes are SINGLE-PAGE only against sanctioned safe targets — **no crawling, no volume** on the public
  internet. Crawls run against the local offline fixture.

## Auth / cookies / sessions

- Never re-use or exfiltrate a user's credentials. Attaching to an open Chrome session (`CdpAdapter` /
  `browser.attach_to_session`) is **consent-gated** and treated as privileged — it acts *as the user*.
- Cookies are **dropped**: `FetchAdapter` surfaces only a whitelist of non-sensitive response headers;
  `Set-Cookie` / `Authorization` echoes never survive into a record. No cookie jar is persisted.

## CAPTCHA / paywalls

- **Detect only, never solve.** `web.detect_captcha` (harness `browser_detect_captcha`) recognizes
  reCAPTCHA/hCaptcha/Turnstile markers so a crawl can *abort and report*. Solving, outsourcing, or bypassing a
  CAPTCHA is PROHIBITED. Paywalls are treated the same — detect, don't defeat.

## PII / data minimization / retention

- Synthetic or public metadata only; no real PII, secrets, confidential data, or proprietary dumps.
- Store **handles + digests + bounded text + extracted structured units**, not raw bodies. Bounded caps
  (`_READABLE_TEXT_CAP`, `max_text_chars`) keep stored surfaces small; the digest carries identity.
- LLM output is UNTRUSTED (`serves_truth=false`) and quarantined until a grounding verifier + promotion pass.

## Allowlist / approval gates

- **Safe live targets (allowlist):** `example.com`, `httpbin.org`, `quotes.toscrape.com` — SINGLE-PAGE GETs
  only, robots-respecting. Anything outside this list on the public internet needs an explicit decision.
- **Approval gates:** binary downloads (`web.download_document` lists by default; fetch needs approval), write+
  actions (`browser.click_ref`/`fill_ref` need human confirmation), agentic plans (`llm.plan_browser_actions`
  — every side-effecting step human-gated), and any keyed remote/managed browser (pages leave your infra).

## PROHIBITED (never build, never run)

- Solving, outsourcing, or bypassing a **CAPTCHA** or anti-bot challenge.
- Defeating a **paywall**, **login wall**, or DRM you do not own.
- Using **another user's authentication / session / cookies** without explicit consent.
- **Submitting forms** or performing **money-movement / regulated / destructive** actions without an approval
  gate and human confirmation.
- Ignoring **`robots.txt`**, rate limits, or a site's Terms; high-volume crawling of a live third party.
- Collecting, storing, or transmitting **real PII, secrets, or credentials**; storing **raw page bodies**.
- Treating any browser/LLM output as **truth** at this layer (it is always `serves_truth=false`).
- Live third-party probing / scraping that would require **written authorization** we do not have.

## Where the gates live (auditable)

`browser_control/safety.py` (policy surface) · `scripts.primitive_browser_control_harness`
(`SIDE_EFFECT_LEVELS`, `browser_respect_robots_policy`, `RateLimiter`, `redact_secrets`, `classify_trust_tier`,
`browser_detect_captcha`/`_login_wall`) · proven by `browser_control/self_test.py` and
`browser_control/ingestion_self_test.py`.

**Playwright is not the whole strategy. It is one adapter in a layered browser/data-ingestion primitive
architecture.**
