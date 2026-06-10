#!/usr/bin/env python3
"""scripts.check_ingest_markdown_folder — proof: a markdown note folder (Obsidian-style vault) flows through the
SAME governed ingestion path behind the existing SourceAdapterPort. Each note → ``source_record``; frontmatter
**scalar** fields → ``source_field`` + ``atomic_fact`` (promotion-eligible only when the frontmatter marks the
note structured/promotable); note **prose** → ``narrative_allegation`` (held out, NEVER promotion-eligible —
a note's claims are not facts); ``[[wikilinks]]`` → ``note_links_to`` edge CANDIDATES; ``#tags`` recorded; a
``.obsidian/`` config dir (and any ``.md`` inside it) is IGNORED. Frontmatter ``source_scope`` /
``source_authority`` are honored; the vault default is ``tenant_private`` and a private note NEVER leaks to
``global_public``. Produced facts are gate-compatible; allegations are held out. Ingestion is deterministic
(content-addressed; time injected) and runs against BOTH an in-memory fixture and the on-disk
``demo-data/markdown-vault/`` fixture.

CLI: python3 scripts/check_ingest_markdown_folder.py --self-test
"""
from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

from scripts.ingest.source_adapters import SourceAdapter
from scripts.runtime.verification_gate import VerificationGate
from src.baltor.adapters.source.markdown_folder import MarkdownFolderAdapter

_REPO = Path(__file__).resolve().parents[1]
_VAULT_DIR = _REPO / "demo-data" / "markdown-vault"
_NOW = 1_000_000  # injected ingest time (no wall-clock)


def _types(r) -> dict:
    return dict(Counter(a["artifact_type"] for a in r.get("artifacts", [])))


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    adapter = MarkdownFolderAdapter()
    check("MarkdownFolderAdapter satisfies the SourceAdapterPort", isinstance(adapter, SourceAdapter))
    check("source_type=markdown / parser_provider=markdown_vault",
          adapter.source_type == "markdown" and adapter.parser_provider == "markdown_vault")

    # ── in-memory vault: a global structured note, a private prose note, + .obsidian/ to be ignored ──
    vault = {
        "reg-e-error-resolution.md": (
            "---\nsource_scope: global_public\nsource_authority: official\n"
            "regulation: Reg E\nresolution_days: 10\nstructured: true\ntags: [compliance, banking]\n---\n"
            "# Reg E Error Resolution\n\n"
            "The bank investigates a reported error. It links to [[Dispute Intake]].\n#compliance\n"
        ),
        "private-meeting-note.md": (
            "---\nproject: Acme\n---\n# Internal note\n\n"
            "We think the vendor overcharged us. Follow up with [[Vendor Contract]].\n#todo #billing\n"
        ),
        ".obsidian/workspace.json": '{"main": "ignored config"}',
        ".obsidian/cache-note.md": "# ignored md inside config dir\n\nMust not be ingested.\n",
    }
    r = adapter.ingest(vault, tenant_id="acme", source_id="vault1", now=_NOW)
    t = _types(r)

    # ── every governed artifact type is produced ──
    check("vault is consumable + produces source_record/source_field/atomic_fact/narrative_allegation",
          r["consumable"] and t.get("source_record", 0) >= 2 and t.get("source_field", 0) >= 1
          and t.get("atomic_fact", 0) >= 1 and t.get("narrative_allegation", 0) >= 1, str(t))

    # ── .obsidian/ ignored (config json AND the .md inside it) ──
    relpaths = {a.get("relpath") for a in r["artifacts"] if a["artifact_type"] == "source_record" and a.get("relpath")}
    check(".obsidian/ config dir is ignored (no note from it)",
          r["note_count"] == 2 and not any(".obsidian" in (rp or "") for rp in relpaths)
          and r["ignored_config_entries"] >= 1, str(relpaths))
    check("a .md file INSIDE .obsidian/ is also ignored",
          "cache-note.md" not in {(rp or "").split("/")[-1] for rp in relpaths}, str(relpaths))

    # ── frontmatter parsed (no yaml dep): scalars → atomic_facts ──
    facts = [a for a in r["artifacts"] if a["artifact_type"] == "atomic_fact"]
    fbyfield = {a["source_handle"].rsplit(".", 1)[-1]: a for a in facts}
    check("frontmatter scalar 'resolution_days' parsed as an int atomic_fact",
          any(a["value"] == 10 for a in facts if a["source_handle"].endswith("resolution_days")), str(fbyfield.keys()))
    check("frontmatter scalar 'regulation' parsed as an atomic_fact",
          any(a["value"] == "Reg E" for a in facts if a["source_handle"].endswith("regulation")))

    # ── note handle format: ctx://.../#note.<relpath>.<field-or-sN> ──
    reg_fact = next(a for a in facts if a["source_handle"].endswith("#note.reg-e-error-resolution.md.regulation")
                    or a["source_handle"].endswith(".reg-e-error-resolution.md.regulation"))
    check("note source handle is ctx://.../#note.<relpath>.<field>",
          "#note.reg-e-error-resolution.md.regulation" in reg_fact["source_handle"], reg_fact["source_handle"])

    # ── structured-note frontmatter facts ARE promotion-eligible; non-structured note's are NOT ──
    reg_facts = [a for a in facts if "reg-e-error-resolution.md" in a["source_handle"]]
    priv_facts = [a for a in facts if "private-meeting-note.md" in a["source_handle"]]
    check("structured: true note → frontmatter facts are promotion-eligible",
          reg_facts and all(a["promotion_eligible"] is True for a in reg_facts))
    check("note WITHOUT structured/promote flag → frontmatter facts NOT promotion-eligible",
          priv_facts and all(a["promotion_eligible"] is False for a in priv_facts))

    # ── note PROSE is held out: narrative_allegation, NEVER promotion-eligible, handle .sN ──
    alls = [a for a in r["artifacts"] if a["artifact_type"] == "narrative_allegation"]
    check("note prose → narrative_allegation (unverified_allegation), held out, NEVER promotion-eligible",
          alls and all(a["claim_status"] == "unverified_allegation" and a["promotion_eligible"] is False
                       and ".s" in a["source_handle"] for a in alls))

    # ── wikilinks captured as note_links_to edge CANDIDATES (not served edges) ──
    edges = r["link_edges"]
    pairs = {(e["from_note"], e["to_note"]) for e in edges}
    check("[[wikilinks]] captured as note_links_to edge candidates",
          ("reg-e-error-resolution.md", "Dispute Intake") in pairs
          and ("private-meeting-note.md", "Vendor Contract") in pairs
          and all(e["edge_type"] == "note_links_to" and e["status"] == "candidate" for e in edges), str(pairs))
    note_recs = [a for a in r["artifacts"] if a["artifact_type"] == "source_record" and a.get("relpath")]
    check("wikilinks also recorded on the note source_record metadata",
          any(nr.get("note_links_to") for nr in note_recs))
    check("#tags captured on note metadata",
          any(nr.get("note_tags") for nr in note_recs))

    # ── PRIVATE VAULT STAYS PRIVATE: default tenant_private; only the global_public note is public ──
    pub = [a for a in r["artifacts"] if a.get("scope") == "global_public"]
    priv = [a for a in r["artifacts"] if a.get("scope") == "tenant_private"]
    check("private note artifacts stay tenant_private (no global leak)",
          all("reg-e-error-resolution.md" in a.get("source_handle", "") or a.get("is_source_root")
              for a in pub) and priv, f"pub={len(pub)} priv={len(priv)}")
    check("the private note never produced a global_public artifact",
          not any(a.get("scope") == "global_public" for a in r["artifacts"]
                  if "private-meeting-note.md" in a.get("source_handle", "")))

    # ── frontmatter source_authority honored ──
    check("frontmatter source_authority honored (reg-e note authority=official)",
          any(nr.get("authority") == "official" for nr in note_recs
              if "reg-e-error-resolution.md" in (nr.get("relpath") or "")))

    # ── produced fact is gate-compatible; an allegation is held out ──
    gate = VerificationGate()
    pe_fact = next(a for a in facts if a["promotion_eligible"])
    gres = gate.evaluate(pe_fact, context={"now": _NOW, "requested_scope": "global_public"},
                         now="2026-06-05T00:00:00Z")
    check("a markdown frontmatter atomic_fact is gate-verifiable (allow)", gres["decision"].decision == "allow",
          str(gres["decision"].reasons))
    ares = gate.evaluate(alls[0], context={"now": _NOW, "requested_scope": "global_public"},
                         now="2026-06-05T00:00:00Z")
    check("a markdown note allegation is held out by the gate", ares["decision"].decision == "hold_out")

    # ── determinism: same input + same injected time → identical result; different content → different hash ──
    r2 = adapter.ingest(vault, tenant_id="acme", source_id="vault1", now=_NOW)
    check("same vault + same injected time → identical artifacts (deterministic content hashes)", r == r2)
    vault_changed = dict(vault)
    vault_changed["reg-e-error-resolution.md"] = vault_changed["reg-e-error-resolution.md"].replace("Reg E", "Reg Z")
    r3 = adapter.ingest(vault_changed, tenant_id="acme", source_id="vault1", now=_NOW)
    h2 = {a["source_handle"]: a["content_hash"] for a in r2["artifacts"]}
    h3 = {a["source_handle"]: a["content_hash"] for a in r3["artifacts"]}
    reg_h = next(k for k in h2 if k.endswith("regulation"))
    days_h = next(k for k in h2 if k.endswith("resolution_days"))
    check("changing one frontmatter field changes only its artifact hash (not a sibling)",
          h2[reg_h] != h3.get(reg_h) and h2[days_h] == h3[days_h])

    # ── on-disk fixture: real connector behind the same port ──
    if _VAULT_DIR.is_dir():
        rd = adapter.ingest(str(_VAULT_DIR), tenant_id="acme", source_id="vault1", now=_NOW)
        td = _types(rd)
        rd_relpaths = {a.get("relpath") for a in rd["artifacts"]
                       if a["artifact_type"] == "source_record" and a.get("relpath")}
        check("on-disk demo-data/markdown-vault/ ingests notes (>=2) and ignores .obsidian/",
              rd["consumable"] and rd["note_count"] >= 2
              and not any(".obsidian" in (rp or "") for rp in rd_relpaths)
              and td.get("narrative_allegation", 0) >= 1, str(td))
    else:
        check("on-disk demo-data/markdown-vault/ fixture exists", False, str(_VAULT_DIR))

    ok = not fails
    print(f"\n{'PASS — check_ingest_markdown_folder: notes flow through the governed path (source_record/field/'
          'atomic_fact/narrative_allegation, correct #note.<relpath> handles); .obsidian ignored; frontmatter '
          'parsed (no yaml dep); structured frontmatter promotion-eligible while note prose is held out and '
          'never promotable; wikilinks captured as edge candidates; private vault stays tenant_private (no '
          'global leak); facts gate-compatible; deterministic.' if ok else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if ok else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: governed markdown-folder ingestion.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
