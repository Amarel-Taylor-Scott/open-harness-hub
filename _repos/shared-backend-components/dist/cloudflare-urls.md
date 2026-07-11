# Cloudflare URL Handoff

Generated: 2026-06-06T00:00:00Z

## Status

- Overall status: **RED**
- cloudflared: available
- Active Cloudflare URLs: 0
- Failed URLs: 2
- Missing/candidate surfaces: 9

## Start Here
| Surface | Local URL | Cloudflare URL | Status | Review |
|---|---|---|---|---|
| Demo Control Tower (START HERE) | http://127.0.0.1:9000/ | — | failed | 1 |

## Portfolio websites
| Surface | Local URL | Cloudflare URL | Status | Review |
|---|---|---|---|---|
| AI Done Right | http://127.0.0.1:9101/ | — | ok | 2 |
| Teleon | http://127.0.0.1:9102/ | — | ok | 3 |
| Baltor | http://127.0.0.1:9103/ | — | ok | 4 |
| OpenContextHub | http://127.0.0.1:9105/ | — | ok | 5 |
| OpenSkillsHub | http://127.0.0.1:9106/ | — | ok | 6 |
| OpenToolsHub | http://127.0.0.1:9107/ | — | ok | 7 |
| OpenHubForAI | http://127.0.0.1:9104/ | — | ok | 8 |
| Portfolio Hub | http://127.0.0.1:9100/ | — | failed | 9 |

## Product demos
| Surface | Local URL | Cloudflare URL | Status | Review |
|---|---|---|---|---|
| Baltor CFPB guided demo (/admin-demo/ live console) | http://127.0.0.1:9301/admin-demo/ | — | ok | 10 |
| Baltor CFPB e2e (offline, PROVEN) | — | — | missing | - |
| Governed Examples Gallery (real deterministic pipeline output) | — | — | missing | - |

## Baltor dashboards
| Surface | Local URL | Cloudflare URL | Status | Review |
|---|---|---|---|---|
| Baltor admin dashboard (monitor) | http://127.0.0.1:9301/admin-dashboard/monitor | — | ok | 11 |
| Baltor ops/monitoring | http://127.0.0.1:9301/admin-demo/monitoring | — | ok | 12 |

## Missing or candidate
| Surface | Reason | Next action |
|---|---|---|
| Teleon PurposeTask demo | candidate | start the backing server / build the web surface |
| OpenContextHub registry API | candidate | start the backing server / build the web surface |
| OpenSkillsHub registry API | candidate | start the backing server / build the web surface |
| OpenToolsHub registry API | candidate | start the backing server / build the web surface |
| OpenHubForAI registry API | candidate | start the backing server / build the web surface |
| Shared Inference Gateway / OIPS (internal) | internal_only | start the backing server / build the web surface |
| Shared Template Registry (internal) | internal_only | start the backing server / build the web surface |

## Caveats

- TryCloudflare URLs are random/session URLs — they change if a tunnel restarts.
- These are demo/local preview links, not production hosting.
- Some URLs may include demo tokens; treat them as demo-only.
- Do not treat local demo links as a production security posture.
- No paid cloud is required. cloudflared quick tunnels only.

