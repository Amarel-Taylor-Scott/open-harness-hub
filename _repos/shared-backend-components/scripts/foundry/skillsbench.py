#!/usr/bin/env python3
"""SkillsBench bridge — interop between OpenHubForAI **Action** components and
BenchFlow **SkillsBench** skills (the Kaggle "Skill Lift" benchmark; arXiv:2602.12670).

Why this exists: SkillsBench is the field's external, third-party operationalisation of
*our* admission criterion. Its "lift" = paired pass-rate (agent WITH a skill minus
WITHOUT) is exactly our `pipeline_score − bare_model_score`; its public→private
generalisation is our durability axis; its ClawsBench safety gate is our governance
moat. The published result — +16.4pp average lift, **but 18 of 84 tasks regress and
model-self-authored skills net −1.3pp** — is the empirical case for everything we gate
on: a component can lift, do nothing, or quietly break, so lift must be *measured*, not
asserted (see _repos/shared-backend-components/context/strategy/skillsbench-alignment.md).

Two directions, both stdlib-only:

  EXPORT  `action_to_skill(component)`  — an OpenHubForAI Action (harness / processor /
          persona / tool / rubric) → a SkillsBench `skills/<slug>/SKILL.md` (+ _repos/shared-backend-components/scripts/,
          references/) bundle. Makes our catalog submittable to Skill Lift and
          interoperable with the SkillsBench ecosystem. The procedure is *derived*, not
          invented: a harness's input_verification → applied_layers → model_io →
          output_verification IS its procedure.

  IMPORT  `task_to_evidence(task)`  — a SkillsBench task (instruction.md + task.toml +
          the curated skill + a deterministic verifier + an oracle) → our evidence triple
          (gap, recorded source, measurable lift). A SkillsBench task is precisely a *gap
          with a deterministic verifier*: the lift is measurable by construction (paired,
          against tests/test.sh), which is the GOLD tier of `confirmation_source` and the
          strongest possible anti-filler signal.

Run `python -m scripts.foundry.skillsbench --self-test` (offline) or `--export <yaml>`.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

SKILLSBENCH_REPO = "https://github.com/benchflow-ai/skillsbench"

# SkillsBench task domains → our industry vocabulary (best-effort; the raw category is
# ALWAYS also kept as a tag, so an unmapped domain never silently vanishes). Single source:
# extend this map, never hand-map a domain at a call site.
_DOMAIN_TO_INDUSTRY: dict[str, str] = {
    "cybersecurity": "security.defensive",
    "finance-economics": "finance",
    "software-engineering": "software",
    "office-white-collar": "office",
    "industrial-physical-systems": "industrial",
    "natural-science": "science",
    "mathematics-or-formal-reasoning": "formal-reasoning",
}

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def _slug(s: str) -> str:
    """kebab-case the last path segment of an id/name (so 'harness/foo-bar' → 'foo-bar')."""
    s = (s or "skill").rsplit("/", 1)[-1].lower()
    return _SLUG_RE.sub("-", s).strip("-") or "skill"


def _one_sentence(s: str) -> str:
    s = " ".join((s or "").split())
    return s if len(s) <= 200 else s[:197].rstrip() + "..."


# ── EXPORT: Action component → SKILL.md ──────────────────────────────────────────────

def _when_to_use(c: dict) -> list[str]:
    explicit = c.get("when_to_use") or c.get("triggers")
    if explicit:
        return [explicit] if isinstance(explicit, str) else list(explicit)
    lines: list[str] = []
    caps = c.get("capability") or []
    inds = c.get("industry") or []
    if caps:
        lines.append(f"You need {', '.join(caps)} on the target input.")
    if inds:
        lines.append(f"You are working in: {', '.join(inds)}.")
    kind = c.get("kind")
    if kind:
        lines.append(f"This is a `{kind}` {c.get('type', 'action')} operating at the "
                     f"`{c.get('trust_boundary', 'local')}` trust boundary.")
    return lines or [_one_sentence(c.get("description") or "Use for the described task.")]


def _procedure(c: dict) -> list[str]:
    """Derive an ordered procedure from the component's real structure (no invention)."""
    explicit = c.get("procedure") or c.get("steps")
    if explicit:
        return [str(x) for x in (explicit if isinstance(explicit, list) else [explicit])]
    steps: list[str] = []
    for v in c.get("input_verification", []) or []:
        steps.append(f"Verify input — {v}.")
    for layer in c.get("applied_layers", []) or []:
        steps.append(f"Apply the `{layer}` layer.")
    mio = c.get("model_io") or {}
    if mio.get("input") or mio.get("output"):
        steps.append(f"Run the model: {mio.get('input', 'input')} → {mio.get('output', 'output')}.")
    for v in c.get("output_verification", []) or []:
        steps.append(f"Check output — {v}.")
    if not steps:
        caps = c.get("capability") or []
        steps.append(f"Perform {', '.join(caps) or 'the described task'} on the target input.")
    return steps


def _worked_example(c: dict) -> str:
    explicit = c.get("worked_example") or c.get("example")
    if explicit:
        return str(explicit)
    mio = c.get("model_io") or {}
    if mio.get("input") or mio.get("output"):
        layers = ", ".join(c.get("applied_layers", []) or []) or "the procedure above"
        return (f"Input: {mio.get('input', '<the target input>')}\n"
                f"Approach: apply [{layers}] →\n"
                f"Output: {mio.get('output', '<the verified output>')}")
    return "Input → expected approach (fill in for the target task)."


def _references(c: dict) -> list[str]:
    refs: list[str] = []
    for kp in c.get("knowledge_packs", []) or []:
        refs.append(f"Knowledge Corpus: {kp.get('label') or kp.get('id')}")
    for ct in c.get("contributes_to", []) or []:
        refs.append(f"Pipeline: {ct}")
    for r in c.get("references", []) or []:
        refs.append(str(r))
    for s in c.get("scripts", []) or []:
        refs.append(f"`scripts/{s.get('path', s) if isinstance(s, dict) else s}`")
    return refs


def skill_md(component: dict) -> str:
    """Render an Action component as a SkillsBench SKILL.md (frontmatter + the four
    canonical sections). Faithful to the published starter template."""
    slug = _slug(component.get("id") or component.get("name") or "skill")
    desc = _one_sentence(component.get("description") or component.get("summary") or slug)
    parts = [f"---\nname: {slug}\ndescription: {desc}\n---\n", f"# {slug}\n"]
    parts.append("## When to use this skill\n" + "\n".join(f"- {x}" for x in _when_to_use(component)) + "\n")
    parts.append("## Procedure\n" + "\n".join(f"{i}. {s}" for i, s in enumerate(_procedure(component), 1)) + "\n")
    parts.append("## Worked example\n" + _worked_example(component) + "\n")
    refs = _references(component)
    if refs:
        parts.append("## References\n" + "\n".join(f"- {r}" for r in refs) + "\n")
    return "\n".join(parts)


def action_to_skill(component: dict) -> dict[str, str]:
    """Return a {relative_path: content} bundle: skills/<slug>/SKILL.md (+ _repos/shared-backend-components/scripts/, references/)."""
    slug = _slug(component.get("id") or component.get("name") or "skill")
    bundle: dict[str, str] = {f"skills/{slug}/SKILL.md": skill_md(component)}
    for s in component.get("scripts", []) or []:
        if isinstance(s, dict) and s.get("path") and s.get("content") is not None:
            bundle[f"skills/{slug}/scripts/{s['path']}"] = s["content"]
    for r in component.get("reference_files", []) or []:
        if isinstance(r, dict) and r.get("path") and r.get("content") is not None:
            bundle[f"skills/{slug}/references/{r['path']}"] = r["content"]
    return bundle


def write_skill_bundle(component: dict, skills_dir: str | Path) -> Path:
    """Write the bundle under `skills_dir` (the SkillsBench submission `skills/` root)."""
    root = Path(skills_dir)
    for rel, content in action_to_skill(component).items():
        dest = root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content, encoding="utf-8")
    return root / "skills" / _slug(component.get("id") or component.get("name") or "skill")


# ── IMPORT: SkillsBench task → evidence triple ───────────────────────────────────────

def task_to_evidence(task: dict) -> dict:
    """A SkillsBench task → our (gap, source, lift) evidence triple. `measured_lift`
    (a Δ pass-rate in [-1,1]) is recorded ONLY when supplied; otherwise the lift is
    flagged measurable-by-the-task's-own-verifier (we never fabricate a number)."""
    tid = task.get("id") or task.get("task_id") or "task"
    instr = task.get("instruction", "") or ""
    meta = task.get("metadata") or {}
    title = next((ln.lstrip("# ").strip() for ln in instr.splitlines() if ln.strip()), tid)
    domains = ([meta["category"]] if meta.get("category") else []) + list(meta.get("tags") or [])
    industry = sorted({_DOMAIN_TO_INDUSTRY[d] for d in domains if d in _DOMAIN_TO_INDUSTRY})

    gap = {
        "summary": title,
        "detail": instr[:1200],
        "industry": industry,
        "tags": ["skillsbench", *domains],
        "difficulty": meta.get("difficulty"),
        "confirmation_source": "recorded",   # external task + deterministic verifier ⇒ gold tier
        "probe": "skillsbench",
    }
    source = {
        "source_url": f"{SKILLSBENCH_REPO}/tree/main/tasks/{tid}",
        "author": meta.get("author_name") or "BenchFlow SkillsBench",
        "license": task.get("license") or "",
        "license_note": "SkillsBench repo license applies; confirm before redistribution.",
        "source_kind": "benchmark",
        "publisher_class": "benchmark",
    }
    measured = task.get("measured_lift")
    lift = {
        "status": "recorded" if measured is not None else "measurable_by_verifier",
        "delta": measured,
        "confirmation_source": "recorded",
        "method": "paired pass-rate: agent WITH the curated skill minus WITHOUT",
        "verifier": "tests/test.sh + tests/test_outputs.py",
        "oracle": "solution/solve.sh",
    }
    skills = task.get("skills") or []
    return {
        "task_id": tid,
        "gap": gap,
        "source": source,
        "lift": lift,
        # the curated, proven skill — a construction reference for our own Action
        "construction_reference": (skills[0].get("skill_md") if skills else None),
    }


def evidence_to_candidate(evidence: dict):
    """Wrap an imported evidence triple as a foundry Candidate so it flows through the
    standard gate. Lift is attached ONLY when measured — an unmeasured task is correctly
    held for measurement/review rather than promoted."""
    from scripts.foundry.contracts import Candidate
    g, s, lift = evidence["gap"], evidence["source"], evidence["lift"]
    measured = lift.get("delta") is not None
    return Candidate(
        target_type="harness",
        gap=g,
        source=s,
        lift=(lift if measured else None),
        body={
            "name": g["summary"],
            "description": g.get("detail", "")[:200],
            "industry": g.get("industry", []),
            "capability": ["evaluation"],
            "skillsbench_task": evidence["task_id"],
        },
    )


def load_task(task_dir: str | Path) -> dict:
    """Read a real SkillsBench task from disk (instruction.md + task.toml + skills/).
    Uses stdlib tomllib (Python ≥3.11)."""
    import tomllib  # noqa: PLC0415 - stdlib, lazy so the dict-path needs no toml

    d = Path(task_dir)
    instr = (d / "instruction.md").read_text(encoding="utf-8") if (d / "instruction.md").exists() else ""
    meta: dict[str, Any] = {}
    toml = d / "task.toml"
    if toml.exists():
        meta = (tomllib.loads(toml.read_text(encoding="utf-8")).get("metadata") or {})
    skills = []
    skills_root = d / "environment" / "skills"
    if skills_root.is_dir():
        for sk in sorted(skills_root.iterdir()):
            md = sk / "SKILL.md"
            if md.exists():
                skills.append({"name": sk.name, "skill_md": md.read_text(encoding="utf-8")})
    return {"id": d.name, "instruction": instr, "metadata": meta, "skills": skills}


# ── self-test / cli ──────────────────────────────────────────────────────────────────

def _self_test() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    # EXPORT: a real harness-shaped component → a valid SKILL.md
    harness = {
        "id": "harness/agent-tool-permissioning-review", "type": "harness",
        "name": "Agent Tool Permissioning review harness",
        "description": "Harness for benchmarkable agent tool permissioning review using persona, grep, RAG, and privacy.",
        "industry": ["ai", "security.defensive"], "capability": ["evaluation", "retrieval", "verification"],
        "kind": "model_harness", "trust_boundary": "local",
        "applied_layers": ["persona", "grep", "rag", "privacy"],
        "input_verification": ["redact direct identifiers", "normalize evidence items before retrieval"],
        "output_verification": ["citation span check passes", "rubric score emitted"],
        "model_io": {"input": "normalized packet evidence plus retrieved context",
                     "output": "findings, citations, score inputs, redaction status"},
        "knowledge_packs": [{"id": "frameworks", "label": "Agent Tool Permissioning framework"}],
        "contributes_to": ["pipeline/agent-tool-permissioning-review"],
    }
    md = skill_md(harness)
    check("SKILL.md has frontmatter name+description", md.startswith("---\nname: agent-tool-permissioning-review\ndescription: "))
    check("SKILL.md has the four canonical sections",
          all(h in md for h in ("## When to use this skill", "## Procedure", "## Worked example", "## References")))
    check("procedure is DERIVED from real structure (verify→layers→model→check)",
          "Verify input — redact direct identifiers." in md and "Apply the `rag` layer." in md
          and "citation span check passes" in md)
    check("worked example uses model_io", "normalized packet evidence" in md.split("## Worked example")[1])

    bundle = action_to_skill({**harness, "scripts": [{"path": "score.py", "content": "print(1)\n"}]})
    check("bundle places SKILL.md at skills/<slug>/SKILL.md", "skills/agent-tool-permissioning-review/SKILL.md" in bundle)
    check("bundle carries scripts/", bundle.get("skills/agent-tool-permissioning-review/scripts/score.py") == "print(1)\n")
    check("slug strips the type prefix", _slug("harness/agent-tool-permissioning-review") == "agent-tool-permissioning-review")

    # IMPORT: a SkillsBench task → evidence triple
    task = {
        "id": "invoice-fraud-detection",
        "instruction": "# Invoice fraud detection\nFlag invoices whose totals violate the stated terms.",
        "metadata": {"category": "finance-economics", "tags": ["fraud", "audit"],
                     "difficulty": "hard", "author_name": "SkillsBench contributor"},
        "skills": [{"name": "fraud-check", "skill_md": "---\nname: fraud-check\n---\n# fraud-check\n"}],
    }
    ev = task_to_evidence(task)
    check("import → gap summary from instruction title", ev["gap"]["summary"] == "Invoice fraud detection")
    check("import maps domain → industry (finance)", ev["gap"]["industry"] == ["finance"])
    check("import keeps raw category as a tag (never silently dropped)", "finance-economics" in ev["gap"]["tags"])
    check("import: gap is recorded-confirmation (deterministic verifier)", ev["gap"]["confirmation_source"] == "recorded")
    check("import: NO fabricated lift (measurable_by_verifier when none supplied)",
          ev["lift"]["status"] == "measurable_by_verifier" and ev["lift"]["delta"] is None)
    check("import: source points at the real task path", ev["source"]["source_url"].endswith("/tasks/invoice-fraud-detection"))
    check("import: curated skill captured as a construction reference", ev["construction_reference"].startswith("---\nname: fraud-check"))

    # a supplied measured lift IS recorded (the gold tier)
    ev2 = task_to_evidence({**task, "measured_lift": 0.164})
    check("supplied Δ pass-rate is recorded as lift", ev2["lift"]["status"] == "recorded" and abs(ev2["lift"]["delta"] - 0.164) < 1e-9)

    # evidence → Candidate: unmeasured ⇒ lift None (held for measurement); measured ⇒ lift set
    cand = evidence_to_candidate(ev)
    check("unmeasured task ⇒ Candidate.lift None (held, not promoted)", cand.lift is None and cand.target_type == "harness")
    check("Candidate body records the skillsbench task id", cand.body.get("skillsbench_task") == "invoice-fraud-detection")
    cand2 = evidence_to_candidate(ev2)
    check("measured task ⇒ Candidate.lift carries the Δ", cand2.lift is not None and abs(cand2.lift["delta"] - 0.164) < 1e-9)

    print(f"\n{'all skillsbench self-tests passed.' if not failures else f'{len(failures)} FAILURES: {failures}'}")
    return 0 if not failures else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="SkillsBench bridge — Action↔skill interop.")
    p.add_argument("--self-test", action="store_true")
    p.add_argument("--export", metavar="COMPONENT", help="render a catalog component YAML as a SKILL.md (stdout)")
    p.add_argument("--import-task", metavar="TASK_DIR", help="read a SkillsBench task dir → evidence triple (stdout)")
    args = p.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.export:
        import yaml  # lazy: only the YAML path needs it
        comp = yaml.safe_load(Path(args.export).read_text(encoding="utf-8"))
        print(skill_md(comp))
        return 0
    if args.import_task:
        print(json.dumps(task_to_evidence(load_task(args.import_task)), indent=2, sort_keys=True))
        return 0
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
