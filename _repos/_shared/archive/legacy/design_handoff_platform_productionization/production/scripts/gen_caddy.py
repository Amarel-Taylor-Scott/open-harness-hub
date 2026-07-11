#!/usr/bin/env python3
"""gen_caddy.py — generate the gateway Caddyfile from services.json.

Short, intelligent routes: one path namespace (/api/<plane>/*, /llm/*) that works
identically on localhost, through the trycloudflare tunnel, and in prod — service code
never hardcodes a port. host-kind services are reached via host.docker.internal;
container-kind via their compose service name; static roots via file_server.

Run:  python3 scripts/gen_caddy.py            (writes ../Caddyfile)
      python3 scripts/gen_caddy.py --check    (exit 1 if Caddyfile is stale — CI drift gate)
"""
import json, sys, pathlib

HERE = pathlib.Path(__file__).resolve().parent
PROD = HERE.parent
CFG = json.loads((PROD / "services.json").read_text())

def upstream(svc):
    if svc["kind"] == "host":
        return f"host.docker.internal:{svc['port']}"
    return f"{svc['id']}:{svc['port']}"

def block(svc):
    lines = []
    for route in svc.get("routes", []):
        if svc["kind"] == "static":
            continue  # static is the catch-all, rendered last
        path = route
        lines.append(f"\thandle {path} {{")
        strip = (svc.get("strip_prefix") or {})
        # apply the longest matching declared prefix rewrite, if any
        for pref, repl in sorted(strip.items(), key=lambda kv: -len(kv[0])):
            if path.startswith(pref):
                lines.append(f"\t\turi strip_prefix {pref}")
                if repl:
                    lines.append(f"\t\trewrite * {repl}{{uri}}")
                break
        lines.append(f"\t\treverse_proxy {upstream(svc)}")
        lines.append("\t}")
    return lines

def render():
    port = CFG["gateway"]["port"]
    out = [
        "# Caddyfile — GENERATED from services.json by scripts/gen_caddy.py. Do not hand-edit.",
        "# Route truth lives in services.json; `just routes` regenerates; CI checks drift.",
        ":80 {",
        "\tencode gzip",
    ]
    dynamic = [s for s in CFG["services"] if s["kind"] != "static"]
    dynamic.sort(key=lambda s: s.get("priority", 50))
    for svc in dynamic:
        out += block(svc)
    out += [
        "\thandle {",
        "\t\troot * /srv/sites",
        "\t\tfile_server browse",
        "\t}",
        "}",
        "",
    ]
    return "\n".join(out)

if __name__ == "__main__":
    target = PROD / "Caddyfile"
    content = render()
    if "--check" in sys.argv:
        ok = target.exists() and target.read_text() == content
        print("Caddyfile is " + ("current" if ok else "STALE — run: just routes"))
        sys.exit(0 if ok else 1)
    target.write_text(content)
    print(f"wrote {target} ({len(content.splitlines())} lines) from services.json")
