# Full user journey (E2E) — 2026-06-10T12:56:27.407Z

**Arc:** landing → register → sign up → configure → integrate → ingestion → consumption
**Surfaces:** OpenHubForAI (http://127.0.0.1:8000) + Baltor (http://127.0.0.1:8001) · real account, real session, real key

| # | stage | detail |
|---|---|---|
| 1 | landing | OpenHubForAI landing — the value proposition |
| 2 | register-account | registered demo+1781096120098@aidoneright.dev (real account, identity service) |
| 3 | sign-up-onboard | onboarded + signed in — real realm session sess_60759fc… |
| 4 | configure | configuring the governed pipeline from the task |
| 5 | integrate | integration API key minted (server-verified=true; blurred + redacted in artifacts) |
| 6 | ingestion-flow | the governed pipeline — source → reconcile → harden → … (ingestion) |
| 7 | ingestion-run | pipeline run — stages execute over the ingested context |
| 8 | consumption-govern | governed output — cited, reconciled, with held-out conflicts (consumption) |
| 9 | baltor-engine | Baltor — the context engine (verified context control for agents) |
| 10 | baltor-stages | the six-stage governed pipeline — ingestion through optimization |
| 11 | baltor-consume | consumption — the served verified answer with its receipt + source handles |
| 12 | back-of-house-receipts | verification email rendered + first draft invoice $99.00 (standardized email + billing ports) |

Video: `artifacts/e2e/videos/full-journey.mp4` · Stills: `artifacts/e2e/screenshots/journey-*.png`

_API key blurred every frame + redacted before stills; passphrase never recorded._