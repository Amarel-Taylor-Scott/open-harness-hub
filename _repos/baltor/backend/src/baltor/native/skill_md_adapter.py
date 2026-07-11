#!/usr/bin/env python3
"""src/baltor/native/skill_md_adapter — interoperate with Anthropic's SKILL.md (Agent Skills) format at the EDGES,
the same way okf_adapter does for OKF and ftm_adapter does for FollowTheMoney: map a governed Baltor skill /
CapabilityTask <-> a SKILL.md file, WITHOUT making SKILL.md our core object. SKILL.md is a projection (like OKF /
FtM / PROV-JSON), not the source of truth.

Why now: SKILL.md won the cross-vendor skill-format war (Anthropic 2025-12; adopted by Microsoft/OpenAI/~32 tools;
governed by the Linux Foundation's Agentic AI Foundation). The format is settled, so it is NOT a moat — assurance
is. A SKILL.md is a markdown file with YAML frontmatter: `name` + `description` (the "when to use this skill" Claude
reads to decide invocation) are REQUIRED; `license`/`allowed-tools`/`version` are optional; arbitrary keys allowed;
the markdown body is the skill instructions. We:
  * IMPORT a SKILL.md as a governed candidate skill (consume the open format), and
  * EXPORT a governed skill as a conformant SKILL.md whose frontmatter ALSO carries our assurance (verified /
    measured lift / source-authority / receipt) under an arbitrary key the spec permits — the governance SKILL.md
    itself does not mandate. We become the only SKILL.md producer whose skills prove their measured lift + safety.

  "They standardize the skill FORMAT; Baltor governs whether the skill actually LIFTS and is safe."

LOSSLESS: import->export->import preserves name/description/body, the governance sidecar, AND any arbitrary
frontmatter keys (kept in ``extra``). Deterministic + offline + stdlib only (no PyYAML: a minimal frontmatter codec;
the governance sidecar travels as a one-line JSON string). serves_truth is always False — a format adapter never
serves truth; an imported skill is a CANDIDATE (discovery != trust) until it passes the gap/lift + safety gates.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field

#: SKILL.md's required frontmatter keys (the spec's hard rule).
SKILL_REQUIRED_KEYS = ("name", "description")
#: an arbitrary frontmatter key (SKILL.md allows arbitrary keys) carrying our assurance as a one-line JSON string.
GOVERNANCE_KEY = "x_baltor_governance_json"
#: recommended/optional SKILL.md scalar keys we map to named fields (others preserved verbatim in ``extra``).
_KNOWN_SCALARS = ("license", "version")
_LIST_KEYS = ("allowed-tools",)


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass
class GovernedSkill:
    """A Baltor skill / CapabilityTask — the CORE. SKILL.md is one projection of it, never its definition."""
    skill_id: str
    name: str
    description: str                                   # the "when to use this skill" (SKILL.md's required field)
    body: str = ""                                     # the markdown skill instructions
    license: str = ""
    version: str = ""
    allowed_tools: tuple = ()
    governance: dict = field(default_factory=dict)     # verified / measured_lift / source_authority / receipt
    extra: dict = field(default_factory=dict)          # any other frontmatter keys — preserved verbatim (lossless)

    def content_hash(self) -> str:
        return _sha256(json.dumps(self.as_dict(), sort_keys=True))

    def as_dict(self) -> dict:
        return {"skill_id": self.skill_id, "name": self.name, "description": self.description, "body": self.body,
                "license": self.license, "version": self.version, "allowed_tools": list(self.allowed_tools),
                "governance": dict(self.governance), "extra": dict(self.extra), "serves_truth": False}


# ── frontmatter codec (minimal, deterministic, lossless for the shapes we emit) ──────────────────────────────
def _fmt_scalar(v) -> str:
    return json.dumps(v) if isinstance(v, str) and (":" in v or v.strip() != v) else str(v)


def _parse_scalar(raw: str):
    raw = raw.strip()
    if raw.startswith("[") and raw.endswith("]"):
        inner = raw[1:-1].strip()
        return tuple(p.strip().strip('"') for p in inner.split(",") if p.strip()) if inner else ()
    if raw.startswith('"') or raw.startswith("{") or raw.startswith("["):
        try:
            return json.loads(raw)
        except Exception:
            return raw.strip('"')
    return raw


def _split_frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---"):
        return {}, text
    lines = text.splitlines()
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if end is None:
        return {}, text
    fm: dict = {}
    for ln in lines[1:end]:
        if not ln.strip() or ":" not in ln:
            continue
        k, _, v = ln.partition(":")
        fm[k.strip()] = v.strip()
    return fm, "\n".join(lines[end + 1:]).lstrip("\n")


# ── IMPORT: SKILL.md → governed skill ────────────────────────────────────────────────────────────────────────
def skill_md_import(path: str, text: str) -> GovernedSkill:
    """Parse a SKILL.md file into a GovernedSkill. Enforces the spec's name+description-required rule."""
    fm, body = _split_frontmatter(text)
    missing = [k for k in SKILL_REQUIRED_KEYS if not str(fm.get(k, "")).strip()]
    if missing:
        raise ValueError(f"SKILL.md {path!r} is missing required key(s): {missing}")
    gov = {}
    if GOVERNANCE_KEY in fm:
        try:
            gov = json.loads(fm[GOVERNANCE_KEY])
        except Exception:
            gov = {}
    tools = _parse_scalar(fm.get("allowed-tools", "")) if "allowed-tools" in fm else ()
    known = {*SKILL_REQUIRED_KEYS, *_KNOWN_SCALARS, *_LIST_KEYS, GOVERNANCE_KEY}
    extra = {k: _parse_scalar(v) for k, v in fm.items() if k not in known}
    return GovernedSkill(
        skill_id=path.rsplit("/", 1)[-1].removesuffix(".md").removesuffix("SKILL").rstrip("/-") or fm["name"],
        name=str(fm["name"]).strip(), description=str(fm["description"]).strip(),
        license=str(fm.get("license", "")).strip(), version=str(fm.get("version", "")).strip(),
        allowed_tools=tuple(tools) if isinstance(tools, (list, tuple)) else (),
        body=body, governance=gov, extra=extra)


# ── EXPORT: governed skill → SKILL.md (with our assurance in the frontmatter) ─────────────────────────────────
def _frontmatter(skill: GovernedSkill) -> str:
    rows = [f"name: {skill.name}", f"description: {_fmt_scalar(skill.description)}"]
    for key in _KNOWN_SCALARS:
        val = getattr(skill, key)
        if val:
            rows.append(f"{key}: {_fmt_scalar(val)}")
    if skill.allowed_tools:
        rows.append("allowed-tools: [" + ", ".join(skill.allowed_tools) + "]")
    for k in sorted(skill.extra):
        rows.append(f"{k}: {_fmt_scalar(skill.extra[k])}")
    if skill.governance:
        gov = dict(skill.governance)
        gov.setdefault("serves_truth", False)
        rows.append(f"{GOVERNANCE_KEY}: {json.dumps(gov, sort_keys=True)}")
    return "---\n" + "\n".join(rows) + "\n---\n"


def skill_md_export(skill: GovernedSkill) -> str:
    """Export a governed skill as a conformant SKILL.md whose frontmatter ALSO proves its lift/safety."""
    return _frontmatter(skill) + (skill.body or "")


def round_trip(skill: GovernedSkill) -> GovernedSkill:
    """import(export(x)) — must preserve name/description/body + the governance sidecar + arbitrary extras."""
    return skill_md_import(f"{skill.skill_id}/SKILL.md", skill_md_export(skill))
