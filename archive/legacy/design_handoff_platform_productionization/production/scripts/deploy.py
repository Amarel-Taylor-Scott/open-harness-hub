#!/usr/bin/env python3
"""deploy.py — the self-orienting one-click deploy.

`just deploy` (or `python3 scripts/deploy.py`) does, in order:
  1. ORIENT     read services.json (what should exist) + .deploy-state.json (what last
                shipped) + fingerprint every service's inputs (content hashes).
  2. PLAN       diff → exactly which services changed and what action each needs
                (build+restart container / reload routes / restart-hint for host services).
  3. ACT        only the changed parts: regenerate Caddyfile if routes changed, compose
                build+up changed containers, reload caddy. Never touches the unchanged.
  4. VERIFY     health-check every routed service through the gateway, with retries.
                Fail loud; nothing is reported deployed that didn't answer.
  5. RECEIPT    append a deploy receipt (what changed, hashes before/after, health
                results) to dist/deploy-receipts.jsonl. HMAC-signed when
                CORE_SIGNING_SECRET is set; explicitly marked unsigned otherwise.

Flags: --dry-run (plan only) · --status (orient only) · --force <id> (redeploy one)
Stdlib only — no dependencies. Honest: host-kind services (the identity service) are
restarted by YOU; this prints the exact command instead of pretending to own them.
"""
import hashlib, hmac, json, os, pathlib, subprocess, sys, time, urllib.request

HERE = pathlib.Path(__file__).resolve().parent
PROD = HERE.parent
CFG = json.loads((PROD / "services.json").read_text())
STATE_FILE = PROD / ".deploy-state.json"
RECEIPTS = PROD / "dist" / "deploy-receipts.jsonl"
GATEWAY = f"http://localhost:{CFG['gateway']['port']}"

def sh(cmd, **kw):
    print(f"  $ {cmd}")
    return subprocess.run(cmd, shell=True, check=True, **kw)

def fingerprint(svc):
    """Content hash of a service's inputs (file sizes+mtimes+names — fast, good enough
    to detect change; switch to full sha256 when repos get checked-in artifacts)."""
    h = hashlib.sha256()
    if svc["kind"] == "container":
        root = PROD / svc["build"]
    elif svc["kind"] == "static":
        root = pathlib.Path(os.environ.get("SITE_ROOT", PROD.parent / "uploads" / "Designs"))
    else:  # host service — fingerprint its start command + port (we don't own its code)
        h.update(json.dumps(svc, sort_keys=True).encode())
        return h.hexdigest()[:16]
    if not root.exists():
        return "missing"
    for p in sorted(root.rglob("*")):
        if p.is_file() and "node_modules" not in p.parts and not p.name.startswith("."):
            st = p.stat()
            h.update(f"{p.relative_to(root)}:{st.st_size}:{int(st.st_mtime)}".encode())
    h.update(json.dumps(svc, sort_keys=True).encode())  # config change = change
    return h.hexdigest()[:16]

def orient():
    state = json.loads(STATE_FILE.read_text()) if STATE_FILE.exists() else {}
    plan = []
    for svc in CFG["services"]:
        now = fingerprint(svc)
        before = state.get(svc["id"], {}).get("hash")
        if now != before:
            plan.append({"id": svc["id"], "kind": svc["kind"], "before": before, "after": now})
    routes_now = hashlib.sha256(json.dumps(CFG, sort_keys=True).encode()).hexdigest()[:16]
    routes_changed = routes_now != state.get("_routes", {}).get("hash")
    return state, plan, routes_now, routes_changed

def health(svc, timeout=30):
    path = svc.get("health")
    if not path:
        return "no-health-route"
    url = GATEWAY + path
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=5) as r:
                if r.status == 200:
                    return "ok"
                last = f"http {r.status}"
        except Exception as e:
            last = str(e)[:60]
        time.sleep(2)
    return f"UNHEALTHY ({last})"

def receipt(body):
    rec = {"at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), **body}
    secret = os.environ.get("CORE_SIGNING_SECRET")
    if secret:
        rec["sig"] = "hmac-sha256:" + hmac.new(secret.encode(),
            json.dumps(body, sort_keys=True).encode(), hashlib.sha256).hexdigest()[:32]
    else:
        rec["sig"] = "UNSIGNED (set CORE_SIGNING_SECRET)"
    RECEIPTS.parent.mkdir(parents=True, exist_ok=True)
    with RECEIPTS.open("a") as f:
        f.write(json.dumps(rec) + "\n")
    return rec

def main():
    args = sys.argv[1:]
    state, plan, routes_now, routes_changed = orient()
    if "--force" in args:
        forced = args[args.index("--force") + 1]
        if not any(p["id"] == forced for p in plan):
            plan.append({"id": forced, "kind": next(s["kind"] for s in CFG["services"] if s["id"] == forced),
                         "before": "forced", "after": fingerprint(next(s for s in CFG["services"] if s["id"] == forced))})

    print(f"ORIENT  {len(CFG['services'])} services · {len(plan)} changed · routes {'changed' if routes_changed else 'current'}")
    for p in plan:
        print(f"  ~ {p['id']} ({p['kind']})  {p['before']} → {p['after']}")
    if "--status" in args or "--dry-run" in args:
        return
    if not plan and not routes_changed:
        print("Nothing to do — everything current.")
        return

    print("ACT")
    if routes_changed:
        sh(f"python3 {HERE / 'gen_caddy.py'}")
    for p in plan:
        svc = next(s for s in CFG["services"] if s["id"] == p["id"])
        if svc["kind"] == "container":
            sh(f"docker compose -f {PROD / 'docker-compose.yaml'} build {svc['id']}")
            sh(f"docker compose -f {PROD / 'docker-compose.yaml'} up -d {svc['id']}")
        elif svc["kind"] == "static":
            print(f"  · {svc['id']}: static — served live, nothing to build")
        else:
            print(f"  ! {svc['id']}: host service — restart it yourself:\n      {svc.get('start', '(no start command declared)')}")
    if routes_changed or any(p["kind"] == "static" for p in plan):
        sh(f"docker compose -f {PROD / 'docker-compose.yaml'} up -d sites")
        sh(f"docker compose -f {PROD / 'docker-compose.yaml'} exec -T sites caddy reload --config /etc/caddy/Caddyfile || true")

    print("VERIFY")
    results = {}
    for svc in CFG["services"]:
        if svc.get("health"):
            results[svc["id"]] = health(svc)
            print(f"  {svc['id']}: {results[svc['id']]}")
    failed = [k for k, v in results.items() if v.startswith("UNHEALTHY")]

    for p in plan:
        state[p["id"]] = {"hash": p["after"], "at": time.time()}
    state["_routes"] = {"hash": routes_now}
    STATE_FILE.write_text(json.dumps(state, indent=1))

    rec = receipt({"kind": "deploy", "changed": [p["id"] for p in plan],
                   "routes_changed": routes_changed, "health": results})
    print(f"RECEIPT {rec['sig'][:40]}…  → {RECEIPTS}")
    if failed:
        print(f"DEPLOY FAILED VERIFY: {failed}")
        sys.exit(1)
    print("DONE — only what changed was touched.")

if __name__ == "__main__":
    main()
