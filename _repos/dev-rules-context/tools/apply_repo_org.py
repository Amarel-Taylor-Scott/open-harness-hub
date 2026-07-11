#!/usr/bin/env python3
"""tools/apply_repo_org — ORGANIZATION AS CODE for the AI Done Right GitHub org.

GitHub is flat (no folders/subgroups). This makes the flat org navigable + REPRODUCIBLE from ONE manifest
(contracts/repo_org_manifest.json): typed custom properties (layer / domain / visibility-plan), nested teams,
and the template repo. Edit the manifest, run --write. Nothing here is hand-clicked in the GitHub UI, so the
org's shape is version-controlled and drift-checkable — the same single-source + drift-gate law the code runs on.

  --check      report drift: repos in the org but not the manifest (and vice-versa)
  --write      apply property schemas + per-repo values + nested teams + team repo grants + is_template
  --self-test  offline mutation gate on the planning logic (no network)

Token: env AIDONERIGHT_GITHUB_PAT or GH_TOKEN (needs admin:org). --self-test needs no token/network.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
MANIFEST = HERE.parent / "contracts" / "repo_org_manifest.json"


def load_manifest(p: Path = MANIFEST) -> dict:
    return json.loads(Path(p).read_text())


# ---------- pure planning (offline-testable) ----------
def plan_property_values(m: dict) -> dict:
    """repo -> {axis: value} for every axis declared, straight from the manifest."""
    axes = list(m["property_axes"])
    return {repo: {ax: attrs[ax] for ax in axes if ax in attrs} for repo, attrs in m["repos"].items()}


def plan_team_repos(m: dict) -> dict:
    """team -> [repos] for teams that select repos by layer (a repo joins every team whose layers include it)."""
    out: dict[str, list[str]] = {}
    for team, spec in m["teams"].items():
        layers = set(spec.get("layers", []))
        if layers:
            out[team] = sorted(r for r, a in m["repos"].items() if a.get("layer") in layers)
    return out


def diff_repos(manifest_repos: list[str], org_repos: list[str]) -> dict:
    mset, oset = set(manifest_repos), set(org_repos)
    return {"in_org_not_manifest": sorted(oset - mset), "in_manifest_not_org": sorted(mset - oset)}


# ---------- GitHub API (only used for --write / --check) ----------
def _token() -> str | None:
    t = os.environ.get("AIDONERIGHT_GITHUB_PAT") or os.environ.get("GH_TOKEN")
    if t:
        return t
    for env in (HERE.parents[2] / ".env", HERE.parent / ".env"):     # repo-root .env fallback
        if env.exists():
            for line in env.read_text().splitlines():
                if line.startswith("AIDONERIGHT_GITHUB_PAT="):
                    return line.split("=", 1)[1].strip()
    return None


def _api(method: str, path: str, token: str, body: dict | None = None) -> tuple:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(f"https://api.github.com{path}", data=data, method=method,
                                 headers={"Authorization": f"token {token}", "Accept": "application/vnd.github+json",
                                          "X-GitHub-Api-Version": "2022-11-28"})
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read().decode()
            return resp.status, (json.loads(raw) if raw else {})
    except urllib.error.HTTPError as e:
        return e.code, {"error": e.read().decode()[:160]}


def org_repos(org: str, token: str) -> list[str]:
    names, page = [], 1
    while True:
        st, data = _api("GET", f"/orgs/{org}/repos?per_page=100&page={page}", token)
        if st != 200 or not isinstance(data, list) or not data:
            break
        names += [r["name"] for r in data]
        if len(data) < 100:
            break
        page += 1
    return names


def apply(m: dict, token: str) -> list[str]:
    org = m["org"]
    log = []
    for name, spec in m["property_axes"].items():                    # 1) typed property definitions
        st, _ = _api("PUT", f"/orgs/{org}/properties/schema/{name}", token,
                     {"value_type": "single_select", "required": False,
                      "allowed_values": spec["values"], "description": spec.get("description", "")})
        log.append(f"property def {name}: {st}")
    for repo, vals in plan_property_values(m).items():               # 2) per-repo property values
        props = [{"property_name": k, "value": v} for k, v in vals.items()]
        st, _ = _api("PATCH", f"/orgs/{org}/properties/values", token,
                     {"repository_names": [repo], "properties": props})
        log.append(f"values {repo}: {st}")
    team_ids: dict[str, int] = {}                                    # 3) nested teams (parents first)
    for team, spec in sorted(m["teams"].items(), key=lambda kv: kv[1].get("parent") is not None):
        body = {"name": team, "description": spec.get("description", ""), "privacy": "closed"}
        if spec.get("parent") and team_ids.get(spec["parent"]):
            body["parent_team_id"] = team_ids[spec["parent"]]
        st, data = _api("POST", f"/orgs/{org}/teams", token, body)
        if st == 201:
            team_ids[team] = data["id"]
        else:                                                        # already exists -> fetch its id
            s2, d2 = _api("GET", f"/orgs/{org}/teams/{team}", token)
            if s2 == 200:
                team_ids[team] = d2["id"]
        log.append(f"team {team}: {st}")
    for team, repos in plan_team_repos(m).items():                   # 4) grant each team its layer's repos
        perm = m["teams"][team].get("permission", "push")
        ok = sum(_api("PUT", f"/orgs/{org}/teams/{team}/repos/{org}/{r}", token, {"permission": perm})[0] in (204, 201)
                 for r in repos)
        log.append(f"team {team} <- {ok}/{len(repos)} repos ({perm})")
    if m.get("template_repo"):                                       # 5) make the devkit a 'Use this template' repo
        st, _ = _api("PATCH", f"/repos/{org}/{m['template_repo']}", token, {"is_template": True})
        log.append(f"is_template {m['template_repo']}: {st}")
    return log


# ---------- modes ----------
def self_test() -> int:
    m = {"org": "X",
         "property_axes": {"layer": {"values": ["a", "b"]}, "domain": {"values": ["d"]}},
         "teams": {"eng": {"parent": None}, "prod": {"parent": "eng", "layers": ["a"]}},
         "repos": {"r1": {"layer": "a", "domain": "d"}, "r2": {"layer": "b", "domain": "d"}}}
    checks = []
    pv = plan_property_values(m)
    checks.append(("values planned per repo across axes", pv["r1"] == {"layer": "a", "domain": "d"}))
    tr = plan_team_repos(m)
    checks.append(("team selects repos by layer", tr["prod"] == ["r1"]))
    checks.append(("parentless team selects nothing by layer", "eng" not in tr))
    df = diff_repos(list(m["repos"]), ["r1", "r3"])
    checks.append(("diff finds org-only + manifest-only", df["in_org_not_manifest"] == ["r3"] and df["in_manifest_not_org"] == ["r2"]))
    # mutation: move r2 into layer a -> it must join the prod team
    m2 = {**m, "repos": {**m["repos"], "r2": {"layer": "a", "domain": "d"}}}
    checks.append(("mutation: r2->layer a joins prod team", plan_team_repos(m2)["prod"] == ["r1", "r2"]))
    failed = [n for n, ok in checks if not ok]
    if failed:
        print("FAIL - apply_repo_org:\n  " + "\n  ".join(failed)); return 1
    print("PASS - apply_repo_org: manifest -> property values + layer-selected nested teams + org/manifest drift.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Apply the org structure manifest to the GitHub org.")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--manifest", type=Path, default=MANIFEST)
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    m = load_manifest(args.manifest)
    if args.check or args.write:
        token = _token()
        if not token:
            print("no token (set AIDONERIGHT_GITHUB_PAT or GH_TOKEN)"); return 2
        if args.check:
            d = diff_repos(list(m["repos"]), org_repos(m["org"], token))
            extra = d["in_org_not_manifest"]; missing = d["in_manifest_not_org"]
            for r in extra:
                print(f"  [org, not in manifest] {r}")
            for r in missing:
                print(f"  [manifest, not in org] {r}")
            print(f"org drift: {len(extra)} undocumented + {len(missing)} missing")
            return 1 if (extra or missing) else 0
        for line in apply(m, token):
            print("  " + line)
        print("applied org manifest")
        return 0
    print("usage: apply_repo_org.py --self-test | --check | --write")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
