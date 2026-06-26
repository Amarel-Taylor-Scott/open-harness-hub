#!/usr/bin/env python3
"""scripts.registry_api_server — a documented, self-describing REST API over the RECONCILED registry SPINE
(`src.teleon.registry.index`). Owner 2026-06-25.

ONE read surface for the same set browse / search / agent already read: every registry carries its metadata +
catalog status + record count, and every record projects to the universal `RegistryObject` shape (id, name, type).
The API is read-only and CORS-open so the browse UI can call it from a tunnel. serves_truth=false.

  GET /                                  -> JSON API index (route list + reconciliation summary) — self-documenting
  GET /registries                        -> reconciled_index()  (?source=&kind=&status=&has_catalog= filters)
  GET /registries/{id}                   -> one registry's metadata (404 JSON if unknown)
  GET /registries/{id}/records?limit=N   -> the registry's RegistryObject records
  GET /search?q=QUERY                    -> {query, hits:[{registry,name}, ...]}  (federated search)
  GET /reconciliation                    -> the ontology∪catalog reconciliation summary

  python3 scripts/registry_api_server.py [--port 8140]    then tunnel it
  --self-test
"""
from __future__ import annotations

import http.server
import json
import sys
import urllib.parse
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.teleon.registry.index import get, reconciled_index, records  # noqa: E402
from src.teleon.registry.search import search_all  # noqa: E402

DEFAULT_PORT = 8140
DEFAULT_RECORD_LIMIT = 200

# the registry-row fields that the ?key=value filters select on (each compared as a string for query-param parity)
_FILTERS = ("source", "kind", "status", "has_catalog")
_TRUE = {"1", "true", "yes", "on"}


def _api_index() -> dict:
    """The self-documenting JSON root: the route list + the live reconciliation summary."""
    idx = reconciled_index()
    return {
        "service": "registry_api_server",
        "description": "Read-only REST API over the reconciled registry spine (src.teleon.registry.index).",
        "serves_truth": False,
        "count": idx["count"],
        "reconciliation": idx["reconciliation"],
        "routes": {
            "GET /": "this API index (route list + reconciliation summary)",
            "GET /registries": "the reconciled index; filters: ?source=&kind=&status=&has_catalog=",
            "GET /registries/{id}": "one registry's metadata (404 if unknown)",
            "GET /registries/{id}/records?limit=N": "the registry's records, each as RegistryObject (id,name,type)",
            "GET /search?q=QUERY": "federated search across all queryable registries",
            "GET /reconciliation": "the ontology∪catalog reconciliation summary",
        },
    }


def _filtered_registries(params: dict) -> dict:
    """reconciled_index() narrowed by the optional ?source=&kind=&status=&has_catalog= params (count recomputed)."""
    idx = reconciled_index()
    regs = idx["registries"]
    for key in _FILTERS:
        if key not in params:
            continue
        want = params[key]
        if key == "has_catalog":
            flag = want.lower() in _TRUE
            regs = [r for r in regs if bool(r.get("has_catalog")) == flag]
        else:
            regs = [r for r in regs if str(r.get(key)) == want]
    return {**idx, "registries": regs, "count": len(regs)}


def route(path: str, query: str = "") -> tuple[int, dict]:
    """Pure router: (method-agnostic GET) path + raw query string -> (status_code, json_payload).

    Factored out of the HTTP handler so the self-test can exercise every endpoint without binding a socket.
    """
    path = path.rstrip("/") or "/"
    params = {k: v[-1] for k, v in urllib.parse.parse_qs(query).items()}

    if path == "/":
        return 200, _api_index()
    if path == "/reconciliation":
        return 200, reconciled_index()["reconciliation"]
    if path == "/search":
        q = params.get("q", "")
        return 200, {"query": q, "hits": search_all(q) if q else [], "serves_truth": False}
    if path == "/registries":
        return 200, _filtered_registries(params)

    parts = [urllib.parse.unquote(p) for p in path.split("/") if p]
    if parts and parts[0] == "registries":
        if len(parts) == 2:
            reg = get(parts[1])
            if reg is None:
                return 404, {"error": "unknown registry", "id": parts[1], "serves_truth": False}
            return 200, reg
        if len(parts) == 3 and parts[2] == "records":
            rid = parts[1]
            if get(rid) is None:
                return 404, {"error": "unknown registry", "id": rid, "serves_truth": False}
            try:
                limit = int(params.get("limit", DEFAULT_RECORD_LIMIT))
            except ValueError:
                limit = DEFAULT_RECORD_LIMIT
            return 200, {"registry": rid, "limit": limit,
                         "records": records(rid, limit=limit), "serves_truth": False}

    return 404, {"error": "not found", "path": path, "serves_truth": False}


class _H(http.server.BaseHTTPRequestHandler):
    def _send(self, code, payload, ctype="application/json"):
        b = payload if isinstance(payload, (bytes, bytearray)) else json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(b)))
        self.send_header("Access-Control-Allow-Origin", "*")  # CORS: the browse UI calls this from a tunnel
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        split = urllib.parse.urlsplit(self.path)
        try:
            code, payload = route(split.path, split.query)
        except Exception as e:  # noqa: BLE001 — never leak a stack trace; honest JSON error
            code, payload = 500, {"error": str(e), "serves_truth": False}
        self._send(code, payload)

    def do_OPTIONS(self):  # CORS preflight
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()

    def log_message(self, *a):
        pass


def self_test() -> int:
    # / is self-documenting: the route list + the reconciliation summary
    code, idx = route("/")
    assert code == 200 and "routes" in idx and "reconciliation" in idx, "/ is self-documenting"

    # /registries returns the reconciled set (>=155) with the reconciliation block
    code, body = route("/registries")
    assert code == 200 and body["count"] >= 155, f"/registries count = {body.get('count')}"
    assert body["reconciliation"]["ontology_types"] and "overlap" in body["reconciliation"], "reconciliation block present"

    # the ?source= filter narrows + recomputes the count (subset of the whole)
    _, only = route("/registries", "source=catalog")
    assert 0 < only["count"] <= body["count"] and all(r["source"] == "catalog" for r in only["registries"]), "filter works"

    # /registries/{id}/records -> RegistryObject items (each id/name/type)
    code, recs = route("/registries/component/records", "limit=5")
    assert code == 200, recs
    items = recs["records"]
    assert items and all({"id", "name", "type"} <= set(o) for o in items), "records conform to RegistryObject"
    assert all(o["type"] == "component" for o in items), "type = the registry id"

    # /registries/{id} -> one real registry
    code, one = route("/registries/component")
    assert code == 200 and one["id"] == "component", one

    # a 404 (JSON) for an unknown id — both the metadata and the records routes
    miss_code, miss = route("/registries/__nope__")
    assert miss_code == 404 and "error" in miss, "unknown id -> 404 JSON"
    assert route("/registries/__nope__/records")[0] == 404, "unknown id records -> 404 JSON"

    # /search?q=cost -> federated hits
    code, sr = route("/search", "q=cost")
    assert code == 200 and sr["query"] == "cost" and sr["hits"], f"/search hits = {len(sr.get('hits', []))}"
    assert all({"registry", "name"} <= set(h) for h in sr["hits"]), "search hits are registry-tagged"

    # /reconciliation -> the summary block alone
    code, rc = route("/reconciliation")
    assert code == 200 and rc["ontology_types"] == body["reconciliation"]["ontology_types"], rc

    print(f"registry_api_server self-test: OK ({body['count']} registries [ontology "
          f"{rc['ontology_types']} ∪ catalogs {rc['live_catalogs']}, overlap {rc['overlap']}]; "
          f"{len(items)} RegistryObject records for 'component'; {len(sr['hits'])} search hits for 'cost'; "
          "serves_truth=false)")
    return 0


def main(argv: list[str]) -> int:
    if "--self-test" in argv:
        return self_test()
    port = int(argv[argv.index("--port") + 1]) if "--port" in argv else DEFAULT_PORT
    print(f"registry API on http://127.0.0.1:{port}  (GET / for the route index)")
    http.server.HTTPServer(("127.0.0.1", port), _H).serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
