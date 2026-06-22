"""src.teleon.repo_strategy — decompose GitHub repos + strategize how they (or variations, or our code) could integrate.

The owner's ask: "send over lots of github pages/repos; various tools process, decompose, and strategize how these
repos or variations of them or our own code could be improved and integrated." This is the PURE logic (offline-testable;
the operator CLI scripts/repo_intake_strategize.py does the live GitHub fetch + writes the governed candidate feed):

  normalize_repo_urls(messy text)  → clean (owner, repo, url) list (strips fbclid/tracking, splits concatenated URLs)
  classify_license(str)            → (license_class, vendorable)   permissive / copyleft / unstated
  decompose(meta, readme)          → structured {what, language, topics, license, deps signal, readme_excerpt}
  map_to_hub(decompose)            → which Open*Hub it fits (keyword map over name/topics/what)
  strategize(decompose, hub)       → {disposition, integration_idea, axes, rationale}  (how to integrate / improve)
  build_record(...)                → ONE governed candidate record (serves_truth=false; adoptable cross-checked)

Governance (matches scripts/ingest_github_signal_intake convention): discovery≠trust; a repo is a CANDIDATE, never
promoted; COPYLEFT/UNSTATED licenses can NEVER be adoptable (technique-only, behind a port). Teleon may import OHH.
"""
from __future__ import annotations

import re

#: disposition vocabulary (single source; mirrors the GitHub-signal intake).
DISPOSITIONS = ("ADOPT-CANDIDATE", "CONSIDER", "WATCH", "AVOID")
#: license → class. permissive ⇒ vendorable; copyleft/unstated ⇒ technique-only (never vendored).
_PERMISSIVE = ("MIT", "APACHE", "BSD", "ISC", "UNLICENSE", "0BSD", "ZLIB", "PYTHON-2")
_COPYLEFT = ("GPL", "AGPL", "LGPL", "MPL", "EPL", "CDDL", "OSL", "EUPL", "CC-BY-SA")
#: name/topic keyword → the Open*Hub a repo most naturally feeds (single source; extend freely).
_HUB_KEYWORDS = [
    ("mcp", "OpenMCPHub"), ("model-context-protocol", "OpenMCPHub"),
    ("harness", "OpenHarnessHub"), ("eval", "OpenBenchmarkHub"), ("benchmark", "OpenBenchmarkHub"),
    ("agent", "OpenAgentHub"), ("skill", "OpenSkillsHub"),
    ("compress", "OpenCompressionHub"), ("token", "OpenCompressionHub"),
    ("graph", "OpenContextHub"), ("rag", "OpenContextHub"), ("retrieval", "OpenContextHub"),
    ("context", "OpenContextHub"), ("knowledge", "OpenContextHub"), ("deep-learning", "OpenContextHub"),
    ("receipt", "OpenReceiptHub"), ("attestation", "OpenReceiptHub"), ("provenance", "OpenReceiptHub"),
    ("route", "OpenRoutingHub"), ("router", "OpenRoutingHub"),
    ("sandbox", "OpenSandboxHub"), ("template", "OpenTemplatesHub"), ("endpoint", "OpenEndpointHub"),
    ("tool", "OpenToolsHub"),
]
_DEFAULT_HUB = "OpenToolsHub"


def normalize_repo_urls(text: str) -> list[dict]:
    """Extract clean github repos from messy input — strips ?fbclid/tracking + #frags, splits CONCATENATED urls
    (e.g. 'repoA?fbclid=...https://github.com/o/repoB'), drops .git, dedupes. Returns [{owner, repo, url}]."""
    out, seen = [], set()
    # the char class excludes '?', '#', '&' so a tracking query naturally terminates the repo capture
    for m in re.finditer(r"github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)", text or ""):
        owner, repo = m.group(1), m.group(2).removesuffix(".git")
        if owner.lower() in ("topics", "orgs", "sponsors", "settings", "features", "about"):
            continue  # not a repo path
        key = (owner.lower(), repo.lower())
        if key in seen:
            continue
        seen.add(key)
        out.append({"owner": owner, "repo": repo, "url": f"https://github.com/{owner}/{repo}"})
    return out


def classify_license(license_str: str | None) -> tuple[str, bool]:
    """(license_class, vendorable). permissive ⇒ vendorable; copyleft/unstated ⇒ NOT vendorable (technique-only)."""
    s = (license_str or "").upper().strip()
    if not s or s in ("NOASSERTION", "NONE", "UNKNOWN", "OTHER"):
        return "unstated", False
    if any(k in s for k in _COPYLEFT):
        return "copyleft", False
    if any(k in s for k in _PERMISSIVE):
        return "permissive", True
    return "unstated", False


def decompose(meta: dict, readme: str = "") -> dict:
    """Structured decomposition of a repo from its metadata + README (deterministic; no LLM needed)."""
    topics = [str(t).lower() for t in (meta.get("topics") or [])]
    license_str = meta.get("license") or ""
    lclass, vendorable = classify_license(license_str)
    what = (meta.get("description") or "").strip()
    excerpt = re.sub(r"\s+", " ", (readme or "")).strip()[:400]
    if not what and excerpt:
        what = excerpt[:160]
    # crude dependency signal from the README (import/require/pip/npm lines) — a hint, not authoritative
    dep_hits = re.findall(r"\b(pip install|npm install|cargo add|go get|import |require\()\s*([A-Za-z0-9_.\-/@]+)", readme or "")
    return {"name": meta.get("name") or meta.get("repo", ""), "owner": meta.get("owner", ""),
            "what": what or "(no description)", "language": meta.get("language") or "", "topics": topics,
            "license": license_str, "license_class": lclass, "vendorable": vendorable,
            "stars": int(meta.get("stars") or 0), "readme_excerpt": excerpt,
            "dependency_signals": [d[1] for d in dep_hits][:12], "serves_truth": False}


def map_to_hub(decomp: dict) -> str:
    """Which Open*Hub this repo most naturally feeds (keyword map over name+topics+what)."""
    hay = " ".join([str(decomp.get("name", "")), str(decomp.get("what", "")), " ".join(decomp.get("topics", []))]).lower()
    for kw, hub in _HUB_KEYWORDS:
        if kw in hay:
            return hub
    return _DEFAULT_HUB


def strategize(decomp: dict, hub: str | None = None) -> dict:
    """How this repo / a variation / our code could integrate + improve — with a governed disposition.

    COPYLEFT/UNSTATED ⇒ never ADOPT (technique-only / license-unclear). Permissive + on-thesis ⇒ ADOPT-CANDIDATE."""
    hub = hub or map_to_hub(decomp)
    vendorable = decomp.get("vendorable", False)
    lclass = decomp.get("license_class", "unstated")
    if lclass == "copyleft":
        disposition = "CONSIDER"  # study the technique, never vendor the code
        integ = f"study the technique behind a port; re-implement clean-room for {hub} (copyleft — never vendored)"
    elif lclass == "unstated":
        disposition = "WATCH"
        integ = f"license unclear — WATCH; request/confirm a license before any {hub} integration"
    else:  # permissive
        disposition = "ADOPT-CANDIDATE"
        integ = f"wrap as a CANDIDATE {hub} component behind a port (governed, serves_truth=false); evaluate lift vs our own"
    axes = []
    hay = (decomp.get("what", "") + " " + " ".join(decomp.get("topics", []))).lower()
    for kw, axis in [("compress", "tokens_in"), ("rout", "cost"), ("eval", "verifiability"), ("graph", "verifiability"),
                     ("cache", "latency"), ("agent", "reliability"), ("sandbox", "safety")]:
        if kw in hay:
            axes.append(axis)
    return {"feeds_hub": hub, "disposition": disposition, "integration_idea": integ,
            "improvement_axes": sorted(set(axes)) or ["(map to a descent axis on review)"],
            "rationale": f"{lclass} license → {('vendorable' if vendorable else 'technique-only')}; maps to {hub}",
            "serves_truth": False}


def build_record(owner: str, repo: str, url: str, meta: dict | None, readme: str = "", *, fetched: bool = True) -> dict:
    """ONE governed candidate record. adoptable = ADOPT-CANDIDATE AND vendorable (copyleft/unstated never adoptable)."""
    if not fetched or meta is None:
        return {"owner": owner, "repo": repo, "url": url, "fetched": False,
                "note": "not fetched (offline / unreachable / 404) — re-run --live to decompose", "serves_truth": False}
    d = decompose({**meta, "owner": owner, "repo": repo}, readme)
    strat = strategize(d)
    adoptable = strat["disposition"] == "ADOPT-CANDIDATE" and d["vendorable"]
    return {"owner": owner, "repo": repo, "url": url, "fetched": True, "decompose": d, "strategy": strat,
            "disposition": strat["disposition"], "adoptable": adoptable, "serves_truth": False}


__all__ = ["DISPOSITIONS", "normalize_repo_urls", "classify_license", "decompose", "map_to_hub",
           "strategize", "build_record"]
