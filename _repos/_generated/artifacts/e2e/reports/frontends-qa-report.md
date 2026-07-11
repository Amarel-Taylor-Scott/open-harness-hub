# Multi-front-end QA — 2026-06-10T13:05:35.446Z

## Real signups into other products' realms (realm-parameterized auth)
| realm | result | detail |
|---|---|---|
| baltor | PASS | real account registered + signed in to the baltor realm (isolated) |
| teleon | PASS | real account registered + signed in to the teleon realm (isolated) |
| opencontexthub | PASS | real account registered + signed in to the opencontexthub realm (isolated) |

## Front-end render sweep
| surface | result | detail |
|---|---|---|
| parent-AI-Done-Right | ok | "AI Done Right — Infrastructure for gover" http=200 overflow=false consoleErr=0 pageErr=0 |
| baltor-app | ok | "Baltor — verified context control for AI" http=200 overflow=false consoleErr=1 pageErr=0 |
| teleon | ok | "Teleon.dev — the purpose-driven runtime" http=200 overflow=false consoleErr=1 pageErr=0 |
| control-tower | ok | "Demo Control Tower — AI Done Right portf" http=200 overflow=false consoleErr=1 pageErr=0 |
| hub-opencontexthub | ok | "OpenContextHub.io — the open context reg" http=200 overflow=false consoleErr=0 pageErr=0 |
| hub-openreviewhub | ok | "OpenReviewHub.io — does it do what it cl" http=200 overflow=false consoleErr=0 pageErr=0 |
| hub-openroutinghub | ok | "OpenRoutingHub.io — model-routing policy" http=200 overflow=false consoleErr=0 pageErr=0 |

## Findings (0)
- none

Video: `artifacts/e2e/videos/frontends-qa.mp4`