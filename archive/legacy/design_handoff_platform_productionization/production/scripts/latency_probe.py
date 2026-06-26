#!/usr/bin/env python3
"""latency_probe.py — measure p50/p95 per routed service through the gateway and
compare against the budgets declared in services.json (`latency_p95_ms`).

This is S11's proof tool: latency is a budget in the manifest, not a vibe.
  just bench                  # 20 requests per health route, p50/p95 vs budget
  just bench -- --n 100       # more samples
Exit 1 on any budget breach (CI-usable). Appends a bench receipt to
dist/bench-receipts.jsonl so regressions are diffable across passes.
Stdlib only. Honest: measures LOCAL gateway overhead only — it says so in the output.
"""
import json, pathlib, statistics, sys, time, urllib.request

HERE = pathlib.Path(__file__).resolve().parent
PROD = HERE.parent
CFG = json.loads((PROD / "services.json").read_text())
GATEWAY = f"http://localhost:{CFG['gateway']['port']}"
N = int(sys.argv[sys.argv.index("--n") + 1]) if "--n" in sys.argv else 20

def probe(path):
    times = []
    for _ in range(N):
        t0 = time.perf_counter()
        try:
            with urllib.request.urlopen(GATEWAY + path, timeout=10) as r:
                r.read()
            times.append((time.perf_counter() - t0) * 1000)
        except Exception as e:
            return None, str(e)[:80]
    return times, None

def main():
    print(f"latency probe · {N} samples/route · local gateway only (network/provider time excluded)")
    results, breach = {}, False
    for svc in CFG["services"]:
        path = svc.get("health")
        budget = svc.get("latency_p95_ms")
        if not path or not budget:
            continue
        times, err = probe(path)
        if err:
            print(f"  {svc['id']:<10} UNREACHABLE ({err})")
            results[svc["id"]] = {"error": err}
            breach = True
            continue
        p50 = statistics.median(times)
        p95 = sorted(times)[max(0, int(len(times) * 0.95) - 1)]
        ok = p95 <= budget
        breach = breach or not ok
        flag = "ok" if ok else f"BREACH (budget {budget}ms)"
        print(f"  {svc['id']:<10} p50 {p50:6.1f}ms · p95 {p95:6.1f}ms · {flag}")
        results[svc["id"]] = {"p50_ms": round(p50, 1), "p95_ms": round(p95, 1),
                              "budget_ms": budget, "ok": ok}
    out = PROD / "dist" / "bench-receipts.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("a") as f:
        f.write(json.dumps({"at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                            "n": N, "results": results}) + "\n")
    print(f"receipt → {out}")
    sys.exit(1 if breach else 0)

if __name__ == "__main__":
    main()
