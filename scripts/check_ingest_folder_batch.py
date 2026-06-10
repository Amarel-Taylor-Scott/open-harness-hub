#!/usr/bin/env python3
"""scripts.check_ingest_folder_batch — proof: a mixed-extension local folder is ONE source whose files are
CLASSIFIED by extension and ROUTED to the correct EXISTING source adapter (json/csv/markdown/html/pdf/txt)
via the existing ``normalize()`` port. The batch emits a ``folder_manifest`` source artifact (every file +
classified source_type + per-file idempotency key + content hash + consumable status), the per-file governed
artifacts produced by each routed adapter, and a batch summary. PARTIAL failure is HONEST: a ``.pdf`` (parser
unavailable) and a ``.txt`` (no batch parser) are NON-consumable manifest entries with the raw stored — they
do NOT abort the batch and NO claim is faked. One file that raises is captured as an ``error`` entry, again
without aborting. Idempotency key per file = ``tenant_id + relpath + content_hash``; re-running the same
folder is byte-identical (deterministic; content-addressed; time injected). Runs against an in-memory fixture
and the on-disk ``demo-data/folder-batch/`` fixture.

CLI: python3 scripts/check_ingest_folder_batch.py --self-test
"""
from __future__ import annotations

import argparse
from pathlib import Path

from scripts.ingest.source_adapters import SourceAdapter
from src.baltor.adapters.source.folder_batch import LocalFolderBatchAdapter

_REPO = Path(__file__).resolve().parents[1]
_BATCH_DIR = _REPO / "demo-data" / "folder-batch"
_NOW = 1_000_000  # injected ingest time (no wall-clock)


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    adapter = LocalFolderBatchAdapter()
    check("LocalFolderBatchAdapter satisfies the SourceAdapterPort", isinstance(adapter, SourceAdapter))
    check("source_type=folder", adapter.source_type == "folder")

    # ── mixed folder: json + csv + md + a fake .pdf (parser unavailable) + a .txt (no batch parser) ──
    folder = {
        "facts.json": '{"id": "X1", "deadline_days": 10}',
        "rows.csv": "id,amount,note\n1,35,Unfair fee. No refund.\n",
        "readme.md": "---\ntitle: Readme\nstructured: true\n---\n# Readme\n\nA note. It links to [[Other]].\n",
        "scan.pdf": b"%PDF-1.4 fake bytes (no real parser)",
        "plain.txt": "Just text, no structured parser in the router.",
    }
    r = adapter.ingest(folder, tenant_id="acme", source_id="upload1", scope="tenant_private", now=_NOW)
    by_relpath = {e["relpath"]: e for e in r["manifest"]}

    # ── manifest artifact created ──
    manifest_arts = [a for a in r["artifacts"] if a["artifact_type"] == "folder_manifest"]
    check("a folder_manifest source artifact is created (one)",
          len(manifest_arts) == 1 and r["source_artifacts"] == manifest_arts, str(len(manifest_arts)))
    check("manifest source handle is ctx://.../#folder.manifest",
          "#folder.manifest" in manifest_arts[0]["source_handle"], manifest_arts[0]["source_handle"])
    check("manifest lists every file with its classified source_type",
          manifest_arts[0]["file_count"] == 5
          and {e["relpath"]: e["source_type"] for e in manifest_arts[0]["files"]}
          == {"facts.json": "json", "rows.csv": "csv", "readme.md": "markdown",
              "scan.pdf": "pdf", "plain.txt": "txt"},
          str({e["relpath"]: e["source_type"] for e in manifest_arts[0]["files"]}))

    # ── mixed files routed to the correct existing adapter (per-file artifacts produced) ──
    check("json/csv/md routed → consumable in the manifest",
          all(by_relpath[f]["consumable"] for f in ("facts.json", "rows.csv", "readme.md")),
          str({k: v.get("consumable") for k, v in by_relpath.items()}))
    # the routed adapters produced governed artifacts (atomic_fact from json/csv, allegation from md prose)
    a_types = {a["artifact_type"] for a in r["artifacts"]}
    check("routed files produced governed per-file artifacts (atomic_fact + narrative_allegation present)",
          "atomic_fact" in a_types and "narrative_allegation" in a_types, str(sorted(a_types)))
    # per-file source_id namespacing keeps handles disjoint
    json_facts = [a for a in r["artifacts"]
                  if a["artifact_type"] == "atomic_fact" and "facts.json" in a.get("source_handle", "")]
    check("a routed file's artifacts are namespaced under <sid>/file/<relpath>",
          json_facts and all("/file/facts.json" in a["source_handle"] for a in json_facts),
          json_facts[0]["source_handle"] if json_facts else "none")

    # ── HONEST non-consumable: .pdf (parser unavailable) is a non-consumable manifest entry, NOT faked ──
    pdf_entry = by_relpath["scan.pdf"]
    check(".pdf is HONESTLY non-consumable in the manifest (reason present, no faked claim)",
          pdf_entry["consumable"] is False and "reason" in pdf_entry
          and not any(a["artifact_type"] == "atomic_fact" and "/file/scan.pdf" in a.get("source_handle", "")
                      for a in r["artifacts"]), str(pdf_entry))
    txt_entry = by_relpath["plain.txt"]
    check(".txt (no batch parser) is honestly non-consumable, raw stored as a source_record",
          txt_entry["consumable"] is False and "reason" in txt_entry
          and any(a["artifact_type"] == "source_record" and "/file/plain.txt" in a.get("source_handle", "")
                  for a in r["artifacts"]), str(txt_entry))

    # ── one bad file does NOT abort the batch ──
    check("the batch is still consumable as a SOURCE despite non-consumable files",
          r["consumable"] is True and r["summary"]["file_count"] == 5
          and r["summary"]["consumable"] == 3 and r["summary"]["non_consumable"] == 2, str(r["summary"]))

    # ── a file that RAISES is captured as an error entry, not an abort ──
    # a bytes subclass whose .decode raises: the CSV adapter takes the bytes branch (payload.decode("utf-8")),
    # so routing this file raises mid-batch and MUST be caught as an error entry, not abort the whole batch.
    class _Boom(bytes):
        def decode(self, *a, **k):  # pragma: no cover - exercised via routing
            raise RuntimeError("simulated decode failure")

    folder_bad = {"good.json": '{"id": "ok"}', "bad.csv": _Boom(b"x")}
    rbad = adapter.ingest(folder_bad, tenant_id="acme", source_id="u2", now=_NOW)
    bad_by = {e["relpath"]: e for e in rbad["manifest"]}
    check("a file that raises becomes an error manifest entry (batch not aborted)",
          rbad["consumable"] is True and bad_by["bad.csv"]["consumable"] is False
          and "error" in bad_by["bad.csv"].get("reason", "") and bad_by["good.json"]["consumable"] is True
          and rbad["summary"]["errors"] == 1, str(rbad["summary"]))

    # ── idempotency key per file = tenant_id + relpath + content_hash ──
    keys = {e["relpath"]: e["idempotency_key"] for e in r["manifest"]}
    check("each file has a tenant_id+relpath+content_hash idempotency key",
          all(keys.values()) and len(set(keys.values())) == len(keys), str(keys))

    # ── duplicate folder run is idempotent (byte-identical manifest + artifacts) ──
    r_again = adapter.ingest(folder, tenant_id="acme", source_id="upload1", scope="tenant_private", now=_NOW)
    check("re-running the same folder is idempotent (identical artifacts + manifest)", r == r_again)
    # same bytes at the same relpath → same idempotency key across runs
    keys2 = {e["relpath"]: e["idempotency_key"] for e in r_again["manifest"]}
    check("idempotency keys are stable across runs (content-addressed)", keys == keys2)
    # changed content at a relpath → a different idempotency key (change is detectable)
    folder_changed = dict(folder)
    folder_changed["facts.json"] = '{"id": "X1", "deadline_days": 20}'
    r_changed = adapter.ingest(folder_changed, tenant_id="acme", source_id="upload1", scope="tenant_private", now=_NOW)
    keys3 = {e["relpath"]: e["idempotency_key"] for e in r_changed["manifest"]}
    check("changed file content → a different idempotency key (others unchanged)",
          keys3["facts.json"] != keys["facts.json"] and keys3["rows.csv"] == keys["rows.csv"])

    # ── routed artifacts carry the batch tenant scope (tenant_private stays private) ──
    routed = [a for a in r["artifacts"] if a["artifact_type"] != "folder_manifest" and "scope" in a]
    check("routed per-file artifacts carry tenant_private scope (no global leak)",
          routed and all(a["scope"] == "tenant_private" for a in routed))

    # ── on-disk fixture: real connector behind the same port ──
    if _BATCH_DIR.is_dir():
        rd = adapter.ingest(str(_BATCH_DIR), tenant_id="acme", source_id="upload1", scope="tenant_private", now=_NOW)
        d_by = {e["relpath"]: e for e in rd["manifest"]}
        check("on-disk demo-data/folder-batch/ routes a mix incl. a non-consumable .pdf",
              rd["consumable"] and rd["summary"]["file_count"] >= 4
              and d_by.get("scan.pdf", {}).get("consumable") is False
              and any(e["consumable"] for e in rd["manifest"]), str(rd["summary"]))
    else:
        check("on-disk demo-data/folder-batch/ fixture exists", False, str(_BATCH_DIR))

    ok = not fails
    print(f"\n{'PASS — check_ingest_folder_batch: a mixed-extension folder is classified + routed to existing '
          'adapters behind normalize(); a folder_manifest source artifact + per-file artifacts + batch summary '
          'are produced; a .pdf/.txt is HONESTLY non-consumable (raw stored, never faked) and one bad/raising '
          'file does NOT abort the batch; per-file idempotency key = tenant+relpath+content_hash; a duplicate '
          'run is byte-identical (deterministic).' if ok else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if ok else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: governed local-folder-batch ingestion.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
