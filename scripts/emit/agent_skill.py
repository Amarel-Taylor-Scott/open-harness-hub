#!/usr/bin/env python3
"""Emit Agent Skills (SKILL.md folders) from every `harness/*` and
`pipeline/*` manifest.

Agent Skills is an OPEN standard originally from Anthropic, adopted by
40+ tools including Claude Code, Claude (claude.ai), OpenAI Codex,
GitHub Copilot, Gemini CLI, Cursor, VS Code, OpenHands, Roo Code,
Goose, Letta, Amp, Junie, Workshop, Tabnine, OpenCode, Factory, and
more. Spec: https://agentskills.io/specification

Outputs:
  dist/agent-skills/<slug>/SKILL.md
  dist/agent-skills/<slug>/references/manifest.yaml   (copy of source)
  dist/agent-skills/INDEX.md
  dist/agent-skills/.claude-plugin/marketplace.json   (Claude-Code-specific bundle)

Run:
  python scripts/emit/agent_skill.py
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path
from textwrap import dedent

import yaml

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from scripts.emit._lib import DIST, by_type, load_catalog, slug_only  # noqa: E402


def render_harness_skill(manifest: dict) -> str:
    slug = slug_only(manifest["id"])
    description = " ".join((manifest.get("description") or "").strip().split())
    if len(description) > 1400:
        description = description[:1397] + "..."

    when_to_use_lines: list[str] = []
    for cap in manifest.get("capability", []) or []:
        when_to_use_lines.append(f"Use when the user needs {cap}.")
    for ind in manifest.get("industry", []) or []:
        if ind != "cross_industry":
            when_to_use_lines.append(f"Particularly relevant for {ind}.")

    front: dict = {
        "name":        slug,
        "description": description,
    }
    if when_to_use_lines:
        front["when_to_use"] = " ".join(when_to_use_lines)

    body_lines: list[str] = []
    body_lines.append(f"# {manifest.get('name', slug)}")
    body_lines.append("")
    body_lines.append(manifest.get("description", "").strip())
    body_lines.append("")

    if manifest.get("applied_layers"):
        body_lines.append("## Applied layers")
        body_lines.append("")
        for layer in manifest["applied_layers"]:
            body_lines.append(f"- `{layer}`")
        body_lines.append("")

    for path in manifest.get("logic_paths", []) or []:
        body_lines.append(f"## {path.get('label', path['id'])}")
        body_lines.append("")
        body_lines.append(f"*model_call:* `{path.get('model_call', 'n/a')}`")
        body_lines.append("")
        if path.get("steps"):
            body_lines.append("**Steps**")
            body_lines.append("")
            for i, step in enumerate(path["steps"], 1):
                body_lines.append(f"{i}. {step}")
            body_lines.append("")
        if path.get("verification"):
            body_lines.append("**Verification**")
            body_lines.append("")
            for v in path["verification"]:
                body_lines.append(f"- {v}")
            body_lines.append("")

    pb = manifest.get("privacy_boundaries") or {}
    if pb:
        body_lines.append("## Privacy boundaries")
        body_lines.append("")
        for k, v in pb.items():
            body_lines.append(f"- **{k}**: {v}")
        body_lines.append("")

    if manifest.get("model_targets"):
        body_lines.append("## Model targets")
        body_lines.append("")
        body_lines.append("| id | transport | trust | required | default |")
        body_lines.append("|---|---|---|---|---|")
        for m in manifest["model_targets"]:
            body_lines.append(
                f"| `{m['id']}` | `{m['transport']}` | {m.get('trust_boundary','—')} | "
                f"{m.get('required', False)} | {m.get('default', False)} |"
            )
        body_lines.append("")

    body_lines.append("## Provenance")
    body_lines.append("")
    body_lines.append(f"- Hub artifact: `{manifest['id']}` v{manifest.get('version','?')}")
    body_lines.append(f"- License: `{manifest.get('license','?')}`")
    body_lines.append(f"- Lifecycle: `{manifest.get('lifecycle','experimental')}`")
    if manifest.get("links"):
        for k, v in manifest["links"].items():
            if v:
                body_lines.append(f"- {k}: {v}")
    body_lines.append("- Full source manifest: see `references/manifest.yaml`")

    frontmatter = yaml.safe_dump(front, sort_keys=False, allow_unicode=True).strip()
    return f"---\n{frontmatter}\n---\n\n" + "\n".join(body_lines) + "\n"


def render_pipeline_skill(manifest: dict) -> str:
    slug = slug_only(manifest["id"])
    description = " ".join((manifest.get("task") or manifest.get("description") or "").strip().split())
    if len(description) > 1400:
        description = description[:1397] + "..."

    front: dict = {
        "name":        slug,
        "description": description,
    }
    if manifest.get("pipeline_kind"):
        front["when_to_use"] = f"Pipeline kind: {manifest['pipeline_kind']}."

    body_lines: list[str] = []
    body_lines.append(f"# {manifest.get('name', slug)}")
    body_lines.append("")
    body_lines.append((manifest.get("description") or "").strip())
    body_lines.append("")

    if manifest.get("task"):
        body_lines.append("## Task")
        body_lines.append("")
        body_lines.append(manifest["task"].strip())
        body_lines.append("")

    if manifest.get("steps"):
        body_lines.append("## Steps")
        body_lines.append("")
        for i, step in enumerate(manifest["steps"], 1):
            when = step.get("when")
            line = f"{i}. **{step['id']}** — `{step['kind']}` → `{step['ref']}`"
            if when:
                line += f" (when `{when}`)"
            body_lines.append(line)
        body_lines.append("")

    if manifest.get("defaults"):
        body_lines.append("## Defaults")
        body_lines.append("")
        for k, v in manifest["defaults"].items():
            if isinstance(v, list):
                v = ", ".join(f"`{i}`" for i in v)
            body_lines.append(f"- **{k}**: {v if v else '—'}")
        body_lines.append("")

    if manifest.get("success_criteria"):
        body_lines.append("## Success criteria")
        body_lines.append("")
        for c in manifest["success_criteria"]:
            if "rubric" in c and "threshold" in c:
                body_lines.append(f"- rubric `{c['rubric']}` threshold {c['threshold']}")
            elif c.get("kind") == "deterministic":
                body_lines.append(f"- deterministic `{c.get('target','?')}` {c.get('op','?')} `{c.get('value','?')}`")
            elif c.get("kind") == "regex":
                body_lines.append(f"- regex `{c.get('pattern','?')}` against `{c.get('target','?')}`")
            elif c.get("kind") == "semantic":
                body_lines.append(f"- semantic must_cover {c.get('must_cover',[])} against `{c.get('target','?')}`")
            elif c.get("kind") == "llm_judge":
                body_lines.append(f"- llm_judge rubric `{c.get('rubric','?')}` threshold {c.get('threshold','?')}")
            elif c.get("kind") == "tool_validate":
                body_lines.append(f"- tool_validate `{c.get('tool','?')}` against `{c.get('target','?')}`")
            elif c.get("kind") == "composite":
                body_lines.append(f"- composite `{c.get('op','?')}` over {len(c.get('children',[]))} child criteria")
            else:
                body_lines.append(f"- criterion: {c}")
        body_lines.append("")

    body_lines.append("## Provenance")
    body_lines.append("")
    body_lines.append(f"- Hub artifact: `{manifest['id']}` v{manifest.get('version','?')}")
    body_lines.append(f"- License: `{manifest.get('license','?')}`")
    body_lines.append(f"- Industry: {', '.join(manifest.get('industry', []) or []) or 'cross_industry'}")
    body_lines.append("- Full source manifest: see `references/manifest.yaml`")

    frontmatter = yaml.safe_dump(front, sort_keys=False, allow_unicode=True).strip()
    return f"---\n{frontmatter}\n---\n\n" + "\n".join(body_lines) + "\n"


def write_skill(skill_dir: Path, body: str, manifest_path: Path) -> None:
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(body)
    refs = skill_dir / "references"
    refs.mkdir(exist_ok=True)
    shutil.copy(manifest_path, refs / "manifest.yaml")


MARKETPLACE_README = dedent("""\
    # Open Harness Hub — Agent Skills bundle

    This directory is the **Agent Skills export** of every harness and
    pipeline in the hub. Agent Skills is an open standard (agentskills.io)
    adopted by 40+ tools including Claude Code, OpenAI Codex, GitHub
    Copilot, Gemini CLI, Cursor, VS Code, OpenHands, Roo Code, Goose,
    Letta, Amp, Junie, Workshop, Tabnine, OpenCode, Factory, and more.

    ## Use as Claude Code skills

    Copy any `<slug>/` directory under `~/.claude/skills/` or your
    project's `.claude/skills/`:

    ```bash
    cp -r dist/agent-skills/text-safety-review ~/.claude/skills/
    ```

    Restart Claude Code; the skill is now available as
    `/text-safety-review`.

    ## Use as a Claude Code plugin marketplace

    The `.claude-plugin/marketplace.json` in this directory makes the
    whole bundle a Claude Code plugin marketplace. Users can add it
    with:

    ```
    /plugin marketplace add <git-url-of-this-repo>
    ```

    ## Use in other Agent Skills-compatible tools

    Every other tool that implements Agent Skills (Cursor, OpenHands,
    Gemini CLI, Roo Code, etc.) accepts the same SKILL.md folder
    layout. Check each tool's docs for the exact install path — the
    contents are identical.
    """)


def main() -> int:
    out_root = DIST / "agent-skills"
    if out_root.exists():
        shutil.rmtree(out_root)
    out_root.mkdir(parents=True)

    catalog = load_catalog()

    written: list[tuple[str, str, str]] = []  # (kind, slug, artifact_id)

    for path, m in by_type(catalog, "harness"):
        slug = slug_only(m["id"])
        body = render_harness_skill(m)
        write_skill(out_root / slug, body, path)
        written.append(("harness", slug, m["id"]))

    for path, m in by_type(catalog, "pipeline"):
        slug = slug_only(m["id"])
        body = render_pipeline_skill(m)
        write_skill(out_root / slug, body, path)
        written.append(("pipeline", slug, m["id"]))

    # INDEX.md
    index_lines = ["# Agent Skills bundle", "", MARKETPLACE_README.strip(), "", "## Skills in this bundle", ""]
    for kind, slug, artifact_id in written:
        index_lines.append(f"- `{slug}/SKILL.md` — {kind} (`{artifact_id}`)")
    (out_root / "INDEX.md").write_text("\n".join(index_lines) + "\n")

    # Claude-Code-specific plugin marketplace manifest.
    cp_dir = out_root / ".claude-plugin"
    cp_dir.mkdir(parents=True, exist_ok=True)
    marketplace = {
        "name":        "open-harness-hub",
        "description": "Harnesses + pipelines from the Open Harness Hub.",
        "plugins": [
            {
                "name":        "open-harness-hub-skills",
                "description": "Bundle of harness + pipeline skills emitted from the Open Harness Hub catalog.",
                "source":      ".",
                "skills":      [f"{slug}/SKILL.md" for _, slug, _ in written],
            }
        ],
    }
    (cp_dir / "marketplace.json").write_text(json.dumps(marketplace, indent=2) + "\n")

    print(f"wrote {len(written)} Agent Skills to dist/agent-skills/")
    for kind, slug, artifact_id in written:
        print(f"  {kind:8s}  {slug:40s}  ({artifact_id})")
    print(f"\nINDEX.md and .claude-plugin/marketplace.json also written.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
