"""src.teleon.digestion.digester — parse a SKILL.md (parse-only), extract deterministic substeps, and build a
cheaper runtime candidate that keeps the original skill as fallback. Pure + deterministic; never executes a skill.
"""
from __future__ import annotations

import hashlib
import re
from typing import Any

#: the cheap→expensive runtime cascade a digested skill can compile to
RUNTIME_CASCADE = ["cache", "deterministic", "browser", "llm", "human"]
#: deterministic-substep detectors: pattern → substep id
_DET_PATTERNS = [
    (("allowlist", "official domain"), "domain_allowlist"),
    (("rank", "authority"), "deterministic_source_ranking"),
    (("parser", "parse"), "deterministic_parser_rule"),
    (("fetch the official page first", "http fetch", "http.fetch"), "http_fetch_first"),
    (("schema", "validate"), "schema_validation"),
    (("retry", "backoff"), "retry_policy"),
    (("hold out", "conflict"), "deterministic_conflict_holdout"),
]
#: adaptive (non-deterministic) step detectors → cascade tier
_ADAPTIVE = [(("renders client-side", "browser"), "browser"), (("ambiguous", "summarize", "llm"), "llm"),
             (("human",), "human")]
#: unsafe patterns (parse-time refusal → quarantine; never executed)
_UNSAFE = [("reads secret env", re.compile(r"(read|exfil|post).{0,40}(api[_ ]?key|secret|credential|token)", re.I)),
           ("secret env var name", re.compile(r"(OPENAI_API_KEY|AWS_SECRET|AWS_SECRET_ACCESS_KEY|GITHUB_TOKEN)")),
           ("exfil to external", re.compile(r"post.{0,40}https?://", re.I)),
           ("destroys audit log", re.compile(r"delete.{0,30}(audit|log)", re.I))]


def parse_skill_md(text: str) -> dict[str, Any]:
    """Parse a SKILL.md (YAML-ish frontmatter + markdown body). PARSE ONLY — never executes the skill."""
    fm: dict[str, Any] = {}
    body = text
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if m:
        body = m.group(2)
        for line in m.group(1).splitlines():
            if ":" not in line:
                continue
            k, v = line.split(":", 1)
            k, v = k.strip(), v.strip()
            if v.startswith("[") and v.endswith("]"):
                fm[k] = [x.strip() for x in v[1:-1].split(",") if x.strip()]
            else:
                fm[k] = v
    return {"name": fm.get("name", "unnamed"), "description": fm.get("description", ""),
            "required_tools": fm.get("required_tools", []), "required_models": fm.get("required_models", []),
            "license": fm.get("license", ""), "body": body, "raw": text}


def is_unsafe(skill: dict) -> list[str]:
    """Parse-time safety flags (secret reads/exfil/log-destruction). Detection only — the skill is NEVER run."""
    hay = skill["raw"] + " " + " ".join(skill.get("required_tools", []))
    return [label for label, rx in _UNSAFE if rx.search(hay)]


def extract_determinism(skill: dict) -> dict[str, Any]:
    body = skill["body"].lower()
    det = sorted({sid for pats, sid in _DET_PATTERNS if any(p in body for p in pats)})
    adaptive = sorted({tier for pats, tier in _ADAPTIVE if any(p in body for p in pats)})
    cascade = [t for t in RUNTIME_CASCADE if t == "cache" or t == "deterministic" and det or t in adaptive]
    if det and "deterministic" not in cascade:
        cascade.insert(1, "deterministic")
    return {"schema_version": "DeterminismExtractionReport", "skill_id": skill["name"],
            "deterministic_substeps": det,
            "unresolved_adaptive_steps": adaptive or ["llm_for_ambiguous"],
            "recommended_cascade": cascade or ["llm", "human"],
            "confidence": "high" if len(det) >= 3 else ("medium" if det else "low")}


def digest_skill(skill: dict, *, source_ref: str, now: str) -> dict[str, Any]:
    """Digest a parsed skill → SkillDigestRun. Unsafe → quarantine. Else a candidate (never active) with the
    original kept as fallback and a proof_to_promote ladder (sandbox + eval + redteam)."""
    unsafe = is_unsafe(skill)
    det = extract_determinism(skill)
    skill_id = skill["name"]
    fallback_ref = f"skill:{skill_id}@fallback"
    proof = ["sandbox_run", "behavioral_eval", "redteam", "contract_validation", "keep_original_fallback"]
    if unsafe:
        decision = "quarantine"
    else:
        decision = "intake_as_skill_candidate"
    return {"schema_version": "SkillDigestRun", "skill_id": skill_id, "source_ref": source_ref,
            "source_hash": "sha256:" + hashlib.sha256(skill["raw"].encode()).hexdigest(),
            "capability_slots": [skill_id.replace("-", "_")],
            "required_tools": skill.get("required_tools", []), "required_models": skill.get("required_models", []),
            "inferred_input_contracts": [{"type": "object"}], "inferred_output_contracts": [{"type": "object"}],
            "unsafe_flags": unsafe, "determinism_extraction": det,
            "recommended_runtime_paths": det["recommended_cascade"],
            "promotion_decision": decision, "proof_to_promote": proof, "fallback_skill_ref": fallback_ref,
            "llm_assist": "advisory_only_via_inference_gateway", "is_truth": False, "digested_at": now}


def build_runtime_candidate(digest: dict, *, now: str) -> dict[str, Any]:
    """A cheaper runtime candidate distilled from the digest — status candidate, original kept as fallback."""
    cid = "rtcand_" + hashlib.blake2b(f"{digest['skill_id']}|{now}".encode(), digest_size=10).hexdigest()
    return {"schema_version": "SkillToRuntimeCandidate", "candidate_id": cid, "skill_id": digest["skill_id"],
            "capability_slot": digest["capability_slots"][0], "runtime_cascade": digest["recommended_runtime_paths"],
            "fallback_skill_ref": digest["fallback_skill_ref"], "status": "candidate",
            "proof_to_promote": digest["proof_to_promote"], "is_truth": False, "created_at": now}


__all__ = ["parse_skill_md", "digest_skill", "build_runtime_candidate", "extract_determinism", "is_unsafe",
           "RUNTIME_CASCADE"]
