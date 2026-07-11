#!/usr/bin/env python3
"""Backs `processor/package-agent-skill` (process_kind ``deliver.skill_package``).

Package a governed corpus + its tools as ONE installable Claude Code skill —
the Repomix pattern: corpus + tools + usage contract distributed as a single
governed, versioned unit. Output is a deterministic in-memory bundle
(path → content) with a content-addressed bundle hash; writing it to disk /
a registry is the caller's transport. Only ``status: published`` corpus
documents are packaged (candidates never ship); every exclusion is reported.

Bundle shape (Claude Code skill conventions):
  SKILL.md                — frontmatter (name, description) + usage contract
  corpus/<id>.md          — one file per published document (with source handle)
  tools/tools.json        — the tool descriptors, verbatim
  PROVENANCE.json         — bundle hash, source corpus id, held-out list

Contract: deterministic; side_effects=none; on_error=raise.
Inputs corpus, tools → output skill_bundle.

CLI / self-test: python3 _repos/shared-backend-components/scripts/processors/deliver/package_agent_skill.py
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any

# ── Constants (No-Magic-Values) ───────────────────────────────────────────────

PUBLISHABLE_STATUS = "published"
HELD_OUT_NOT_PUBLISHED = "status is not 'published' — candidates never ship in a skill bundle"

#: Skill names: kebab-case, the Claude Code convention.
_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")

HASH_ALGORITHM = "sha256"
BUNDLE_HASH_PREFIX = "skb:"


def run(*, corpus: dict[str, Any], tools: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Build the skill bundle for ``corpus`` ({"skill_name","description",
    "version","documents":[...]}) plus optional tool descriptors."""
    if not isinstance(corpus, dict):
        raise TypeError("corpus must be a dict")
    name = corpus.get("skill_name", "")
    if not isinstance(name, str) or not _NAME_RE.match(name):
        raise ValueError(f"skill_name must be kebab-case, got {name!r}")
    if not corpus.get("description"):
        raise ValueError("corpus needs a description (the skill's trigger text)")
    docs = corpus.get("documents")
    if not isinstance(docs, list):
        raise TypeError("corpus.documents must be a list")
    tools = tools or []
    if not isinstance(tools, list):
        raise TypeError("tools must be a list of descriptor dicts")

    files: dict[str, str] = {}
    shipped: list[str] = []
    held_out: list[dict[str, Any]] = []
    for i, d in enumerate(docs):
        if not isinstance(d, dict) or "id" not in d or "text" not in d:
            raise ValueError(f"documents[{i}] needs id and text")
        if d.get("status") != PUBLISHABLE_STATUS:
            held_out.append({"id": d["id"], "reason": HELD_OUT_NOT_PUBLISHED})
            continue
        handle = d.get("source_handle", "(no source handle recorded)")
        files[f"corpus/{d['id']}.md"] = (f"# {d.get('title', d['id'])}\n\n"
                                         f"> source: {handle}\n\n{str(d['text']).rstrip()}\n")
        shipped.append(str(d["id"]))
    if tools:
        files["tools/tools.json"] = json.dumps(tools, indent=2, sort_keys=True) + "\n"
    version = str(corpus.get("version", "0.1.0"))  # version lives in METADATA, never the name
    corpus_lines = "\n".join(f"- corpus/{sid}.md" for sid in sorted(shipped)) or "- (no published documents)"
    files["SKILL.md"] = (
        f"---\nname: {name}\ndescription: {corpus['description']}\n"
        f"version: {version}\n---\n\n"
        f"# {name}\n\n{corpus['description']}\n\n"
        "## Governed corpus\n"
        "Answer ONLY from the files under corpus/ — cite the source handle in each "
        "file's header; if the corpus does not support an answer, say so.\n\n"
        f"{corpus_lines}\n"
        + ("\n## Tools\nDescriptors in tools/tools.json (metadata — wire per environment).\n"
           if tools else ""))
    digest = hashlib.new(HASH_ALGORITHM, json.dumps(files, sort_keys=True).encode("utf-8")).hexdigest()
    files["PROVENANCE.json"] = json.dumps({
        "bundle_hash": BUNDLE_HASH_PREFIX + digest,
        "skill_name": name, "version": version,
        "shipped_documents": sorted(shipped), "held_out": held_out,
    }, indent=2, sort_keys=True) + "\n"
    return {"skill_bundle": {"files": files, "bundle_hash": BUNDLE_HASH_PREFIX + digest,
                             "shipped": sorted(shipped), "held_out": held_out,
                             "install_as": f".claude/skills/{name}/"}}


def _selftest() -> None:
    corpus = {
        "skill_name": "reg-e-timing", "version": "1.2.0",
        "description": "Answer Regulation E error-resolution timing questions from the governed corpus.",
        "documents": [
            {"id": "rule", "title": "The 10-day rule", "status": "published",
             "source_handle": "ctx://reg-e/1005.11", "text": "Provisional credit within 10 business days."},
            {"id": "draft", "title": "Unverified note", "status": "candidate", "text": "maybe 30 days?"},
        ],
    }
    tools = [{"name": "lookup_rule", "description": "Exact statute lookup"}]
    out = run(corpus=corpus, tools=tools)["skill_bundle"]
    files = out["files"]
    # The bundle is complete: SKILL.md with frontmatter + cite-or-abstain, corpus
    # file with its source handle, tools verbatim, provenance with the hash.
    assert files["SKILL.md"].startswith("---\nname: reg-e-timing\n")
    assert "version: 1.2.0" in files["SKILL.md"] and "say so" in files["SKILL.md"]
    assert "ctx://reg-e/1005.11" in files["corpus/rule.md"]
    assert json.loads(files["tools/tools.json"])[0]["name"] == "lookup_rule"
    prov = json.loads(files["PROVENANCE.json"])
    assert prov["bundle_hash"] == out["bundle_hash"] and prov["shipped_documents"] == ["rule"]
    # Governance: the candidate never ships and the exclusion is recorded.
    assert "corpus/draft.md" not in files
    assert out["held_out"] == [{"id": "draft", "reason": HELD_OUT_NOT_PUBLISHED}]
    # Version lives in metadata, never the name/path.
    assert out["install_as"] == ".claude/skills/reg-e-timing/"
    # Deterministic bundle hash.
    assert run(corpus=corpus, tools=tools)["skill_bundle"]["bundle_hash"] == out["bundle_hash"]
    # on_error=raise: bad name, missing description.
    for bad in (
        lambda: run(corpus={**corpus, "skill_name": "Reg E!"}),
        lambda: run(corpus={"skill_name": "x", "documents": []}),
    ):
        raised = False
        try:
            bad()
        except ValueError:
            raised = True
        assert raised
    print("PASS — package_agent_skill: one installable bundle (SKILL.md frontmatter + "
          "cite-or-abstain contract + per-doc source handles + tools + provenance), "
          "published-only shipping, content-addressed bundle hash verified")


if __name__ == "__main__":
    _selftest()
