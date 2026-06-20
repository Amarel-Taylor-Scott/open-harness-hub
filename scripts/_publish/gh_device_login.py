#!/usr/bin/env python3
"""GitHub Device Authorization Flow — get a user-scoped OAuth token
without installing the gh CLI or pasting a PAT.

Uses the gh CLI's public OAuth client_id (178c6fc778ccc68e1d6a) so we
inherit its registered redirect URI. The token is saved with chmod 600
to a path printed at the end.

Usage:
  python scripts/_publish/gh_device_login.py [--scope "repo workflow"]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.parse
import urllib.request

GH_CLI_CLIENT_ID = "178c6fc778ccc68e1d6a"

DEVICE_URL = "https://github.com/login/device/code"
TOKEN_URL  = "https://github.com/login/oauth/access_token"


def post(url: str, data: dict) -> dict:
    body = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(url, data=body, method="POST", headers={
        "Accept":       "application/json",
        "User-Agent":   "open-harness-hub-publish/0.1",
        "Content-Type": "application/x-www-form-urlencoded",
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scope", default="repo workflow")
    ap.add_argument("--client-id", default=GH_CLI_CLIENT_ID)
    ap.add_argument("--out", default="/tmp/.oh_gh_token")
    args = ap.parse_args()

    print("Requesting device code …", flush=True)
    d = post(DEVICE_URL, {"client_id": args.client_id, "scope": args.scope})

    user_code        = d["user_code"]
    device_code      = d["device_code"]
    verification_uri = d.get("verification_uri", "https://github.com/login/device")
    interval         = max(5, int(d.get("interval", 5)))
    expires_in       = int(d.get("expires_in", 900))

    sep = "═" * 64
    print()
    print(sep)
    print("  GitHub authorization needed")
    print(sep)
    print(f"  1. Open this URL in your browser:")
    print(f"        {verification_uri}")
    print(f"  2. Enter this one-time code:")
    print(f"        {user_code}")
    print(f"  3. Approve the requested scopes ({args.scope}).")
    print(f"  Code expires in {expires_in // 60} min.")
    print(sep)
    print(flush=True)

    deadline = time.time() + expires_in
    while time.time() < deadline:
        time.sleep(interval)
        try:
            t = post(TOKEN_URL, {
                "client_id":  args.client_id,
                "device_code": device_code,
                "grant_type": "urn:ietf:params:oauth:grant_type:device_code",
            })
        except Exception as e:
            print(f"  (poll error: {e!r}; retrying)", flush=True)
            continue

        if "access_token" in t:
            token = t["access_token"]
            scope = t.get("scope", args.scope)
            out_path = args.out
            with open(out_path, "w") as f:
                f.write(token)
            os.chmod(out_path, 0o600)
            print(f"\n✅  Authorized. Token saved to {out_path} (chmod 600).")
            print(f"    Scopes granted: {scope}")
            return 0

        err = t.get("error")
        if err == "authorization_pending":
            print("  waiting for you to approve …", flush=True)
            continue
        if err == "slow_down":
            interval += 5
            continue
        if err in ("expired_token", "access_denied"):
            print(f"\n✗  {err}: please re-run the script.", flush=True)
            return 2

        print(f"  unexpected response: {t!r}", flush=True)

    print("\n✗  device code expired before authorization.", flush=True)
    return 1


if __name__ == "__main__":
    sys.exit(main())
