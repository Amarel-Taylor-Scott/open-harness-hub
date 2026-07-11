# Register → onboard → login → API keys → logout → login (E2E) — 2026-06-09T19:05:39.334Z

App: http://127.0.0.1:8000 · Realm: openharnesshub · Identity service: real (localhost:9410) · Result: **PASS**

| # | step | ok | detail |
|---|---|---|---|
| 1 | signup-page | ok |  |
| 2 | register | ok | registered demo+1781031935762@aidoneright.dev |
| 3 | onboarding | ok |  |
| 4 | activate-and-login | ok | REAL session sess_0268dd4… (realm-scoped, opaque) |
| 5 | keys-console | ok |  |
| 6 | mint-key-blurred | ok | key minted; server-side verify=valid; field redacted+blurred in artifacts |
| 7 | revoke-key | ok |  |
| 8 | logout | ok | logged_out=true |
| 9 | sign-back-in | ok |  |
| 10 | session-restored | ok | realm session validates after re-login |

Video: `artifacts/e2e/videos/portal-register-login-keys.mp4` (continuous frames) · Stills: `artifacts/e2e/screenshots/portal-*.png`

_Raw key blurred+redacted in all artifacts; passphrase never recorded._