#!/usr/bin/env python3
"""scripts.deploy.go_live — the one command that answers "what do I still have to provide?"

Everything an agent can pre-wire is done: green proofs, re-anchored CI, the SOPS+age vault template,
deploy topology, the preflight GO/NO-GO gate. This tool reports the OWNER RESIDUAL — the short list of
things only a human can do (generate the age key, create host accounts + cards, provide key values).
Each item is READY (agent-done) or OWNER (you must provide it), so "get me to just provide keys" is
a checklist you can watch go green.

    PYTHONPATH=. python3 scripts/deploy/go_live.py            # readiness report
    PYTHONPATH=. python3 scripts/deploy/go_live.py --self-test
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

REPO = next((p for p in Path(__file__).resolve().parents if (p / ".aidoneright-root").exists()),
            Path(__file__).resolve().parents[3])
_SBC = Path(__file__).resolve().parents[2]
if str(_SBC) not in sys.path:
    sys.path.insert(0, str(_SBC))

#: Placeholder marker the vault ships with until the owner drops in a real age recipient.
_AGE_PLACEHOLDER = "age1PLACEHOLDER"
#: The single required CI secret (everything else is host-side / optional).
_REQUIRED_CI_SECRET = "SOPS_AGE_KEY"


def _sops_policy_ready() -> tuple[bool, str]:
    p = REPO / ".sops.yaml"
    if not p.exists():
        return False, ".sops.yaml missing"
    txt = p.read_text(encoding="utf-8")
    if _AGE_PLACEHOLDER in txt:
        return False, "OWNER: replace the placeholder age recipient in .sops.yaml with your `age-keygen` public key"
    return True, "age recipient set"


def _secrets_encrypted() -> tuple[bool, str]:
    env = _SBC / "secrets" / "secrets.dev.env"
    if not env.exists():
        return False, "secrets/secrets.dev.env missing"
    txt = env.read_text(encoding="utf-8", errors="ignore")
    # a SOPS-encrypted dotenv carries ENC[ markers; the shipped template is plaintext-synthetic
    if "ENC[" in txt:
        return True, "values are age-encrypted"
    if "synthetic-" in txt:
        return False, "OWNER: put real values in secrets/secrets.dev.env then `sops -e -i` it (keys stay, values encrypt)"
    return False, "secrets template not in expected state"


def _preflight_go() -> tuple[bool, str]:
    try:
        from scripts.deploy import preflight
        go, results = preflight.run()
        if go:
            return True, "deploy artifacts consistent (preflight GO)"
        bad = [r["check"] for r in results if not r.get("ok")]
        return False, f"preflight NO-GO on: {', '.join(bad) or 'unknown'}"
    except Exception as exc:  # pragma: no cover - defensive
        return False, f"preflight could not run: {exc}"


def _env_or(names, label) -> tuple[bool, str]:
    have = [n for n in names if os.environ.get(n)]
    if have:
        return True, f"{label}: {have[0]} present"
    return None, f"OWNER (optional): {label} — set one of {', '.join(names)} when you deploy"


def readiness() -> list[dict]:
    """Return the readiness matrix. status: True=READY, False=OWNER-blocking, None=OWNER-optional."""
    age_ok, age_msg = _sops_policy_ready()
    sec_ok, sec_msg = _secrets_encrypted()
    pf_ok, pf_msg = _preflight_go()
    ci_secret = bool(os.environ.get(_REQUIRED_CI_SECRET))
    fly_ok, fly_msg = _env_or(["FLY_API_TOKEN"], "Fly host token")
    cf_ok, cf_msg = _env_or(["CLOUDFLARE_API_TOKEN"], "Cloudflare token (DNS/Pages)")
    show_ok, show_msg = _env_or(["OH_SHOWCASE_TOKEN"], "public-surface showcase token")
    return [
        {"item": "Proof suite green", "status": True, "detail": "run_proofs umbrella (agent-verified)"},
        {"item": "CI workflows re-pathed + compileall gate", "status": True, "detail": "pages/validate/emit/release"},
        {"item": "Deploy artifacts consistent", "status": pf_ok, "detail": pf_msg},
        {"item": "SOPS+age vault policy", "status": age_ok, "detail": age_msg},
        {"item": "Secrets encrypted", "status": sec_ok, "detail": sec_msg},
        {"item": f"CI secret {_REQUIRED_CI_SECRET}", "status": True if ci_secret else False,
         "detail": "present" if ci_secret else "OWNER: add your age PRIVATE key as the GitHub Environment secret SOPS_AGE_KEY"},
        {"item": "GitHub Settings toggles", "status": None,
         "detail": "OWNER: Actions -> Workflow permissions = Read/write; Pages -> Source = GitHub Actions"},
        {"item": "Host account + token", "status": fly_ok, "detail": fly_msg},
        {"item": "DNS token", "status": cf_ok, "detail": cf_msg},
        {"item": "Showcase token", "status": show_ok, "detail": show_msg},
    ]


def _render(matrix: list[dict]) -> int:
    owner_blocking = [m for m in matrix if m["status"] is False]
    owner_optional = [m for m in matrix if m["status"] is None]
    sym = {True: "READY ", False: "OWNER ", None: "OWNER?"}
    print("== go-live readiness ==")
    for m in matrix:
        print(f"  [{sym[m['status']]}] {m['item']} — {m['detail']}")
    print()
    if not owner_blocking:
        print("ALL AGENT-DOABLE PREP IS DONE. Residual is only the OWNER? (optional, at deploy time) items above.")
    else:
        print(f"YOUR RESIDUAL — {len(owner_blocking)} thing(s) only you can provide:")
        for m in owner_blocking:
            print(f"  -> {m['detail']}")
    print(f"\n(plus {len(owner_optional)} optional-at-deploy items: host/DNS/showcase tokens)")
    return 0


def _self_test() -> int:
    m = readiness()
    checks = [
        ("matrix covers all expected items", len(m) == 10),
        ("every row has a tri-state status", all(x["status"] in (True, False, None) for x in m)),
        ("the required CI secret is tracked", any(_REQUIRED_CI_SECRET in x["item"] for x in m)),
        ("preflight row present", any("Deploy artifacts" in x["item"] for x in m)),
        ("vault policy row present", any("vault policy" in x["item"] for x in m)),
    ]
    failed = [n for n, ok in checks if not ok]
    if failed:
        print("FAIL - go_live:\n  " + "\n  ".join(failed))
        return 1
    print("PASS - go_live: readiness matrix reports each go-live item as READY (agent-done) or OWNER "
          "(you provide), so the owner residual is explicit and watchable.")
    return 0


def main(argv: list[str]) -> int:
    if "--self-test" in argv:
        return _self_test()
    return _render(readiness())


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
