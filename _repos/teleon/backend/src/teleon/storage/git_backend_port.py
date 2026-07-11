"""src.teleon.storage.git_backend_port — a PLUGGABLE git backend for Teleon capability units.

The insight: a capability UNIT's storage / versioning / diffs / metadata ARE git primitives. So abstract them
behind ONE port, and let the SAME unit be backed by our INTERNAL git OR by the CLIENT's own GitHub / GitLab /
Bitbucket / self-hosted Gitea — meeting teams where their code already lives (familiar UI/UX = adoption) while the
GOVERNANCE abstraction (verification, lift, receipts, provenance) rides ABOVE git, consistently, on any backend.

Two governance invariants make this safe:
  * The client's CODE stays clean — governed metadata (receipt / measured lift / provenance) is attached in a
    SIDECAR namespace (a `teleon/governance` notes ref), never mixed into the code blob. Tenant-private lineage
    stays tenant-private (it never has to live in the client's repo at all).
  * A backend is a STORAGE choice, not a source of truth — serves_truth is always False; promotion/verification
    happens in Teleon's control plane regardless of where the bytes rest.

LocalGitBackend is a full in-memory, content-addressed implementation (our internal-git default AND the DEFER-GATE
local equivalent of the live external backends). ClientPlatformBackend maps the port onto GitHub/GitLab/Gitea; the
LIVE calls need network + the client's credentials, so they are OWNER-GATED — offline it mirrors to a LocalGitBackend
so the whole abstraction is testable. Pure + deterministic (timestamps passed in); Teleon-layer (never imports baltor).
"""
from __future__ import annotations

import difflib
import hashlib
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

#: client platforms the abstraction can target (all behind the same port).
SUPPORTED_PLATFORMS = ("internal", "github", "gitlab", "bitbucket", "gitea", "forgejo")
#: the sidecar ref where governed metadata rides (git-notes style) — keeps the client's code clean.
GOVERNANCE_NOTES_REF = "refs/notes/teleon/governance"


def _sha(parent: str, content: str) -> str:
    return hashlib.sha256(f"{parent}\n{content}".encode("utf-8")).hexdigest()[:16]


@dataclass(frozen=True)
class CommitRef:
    unit: str
    rev: str                         # content-addressed revision id (sha)
    parent: str
    message: str
    backend: str                     # which backend holds it (internal / github / gitlab / ...)
    serves_truth: bool = False

    def as_dict(self) -> dict:
        return {"unit": self.unit, "rev": self.rev, "parent": self.parent, "message": self.message,
                "backend": self.backend, "serves_truth": False}


@runtime_checkable
class GitBackendPort(Protocol):
    """The minimal VCS surface a capability unit needs — implementable on internal git OR any client platform."""
    platform: str

    def commit(self, unit: str, content: str, *, message: str, now: str) -> CommitRef: ...
    def read(self, unit: str, rev: str) -> str: ...
    def history(self, unit: str) -> list[CommitRef]: ...
    def diff(self, unit: str, rev_a: str, rev_b: str) -> str: ...
    def tag(self, unit: str, rev: str, name: str) -> None: ...
    def attach_governance(self, unit: str, rev: str, meta: dict) -> None: ...   # sidecar notes — not in the code blob
    def read_governance(self, unit: str, rev: str) -> dict: ...


class LocalGitBackend:
    """In-memory, content-addressed git backend (our internal-git default + the DEFER-GATE local equivalent of the
    live external backends). Fully deterministic + offline."""

    def __init__(self, platform: str = "internal") -> None:
        self.platform = platform
        self._commits: dict[str, list[CommitRef]] = {}
        self._blobs: dict[tuple, str] = {}              # (unit, rev) -> content
        self._notes: dict[tuple, dict] = {}             # (unit, rev) -> governed meta (the sidecar)
        self._tags: dict[tuple, str] = {}               # (unit, name) -> rev

    def commit(self, unit: str, content: str, *, message: str, now: str) -> CommitRef:
        parent = self._commits.get(unit, [])[-1].rev if self._commits.get(unit) else ""
        rev = _sha(parent, content)
        ref = CommitRef(unit=unit, rev=rev, parent=parent, message=message, backend=self.platform)
        self._commits.setdefault(unit, []).append(ref)
        self._blobs[(unit, rev)] = content
        return ref

    def read(self, unit: str, rev: str) -> str:
        return self._blobs[(unit, rev)]

    def history(self, unit: str) -> list[CommitRef]:
        return list(self._commits.get(unit, []))

    def diff(self, unit: str, rev_a: str, rev_b: str) -> str:
        a, b = self._blobs[(unit, rev_a)].splitlines(), self._blobs[(unit, rev_b)].splitlines()
        return "\n".join(difflib.unified_diff(a, b, lineterm="", fromfile=rev_a, tofile=rev_b))

    def tag(self, unit: str, rev: str, name: str) -> None:
        self._tags[(unit, name)] = rev

    def attach_governance(self, unit: str, rev: str, meta: dict) -> None:
        self._notes[(unit, rev)] = dict(meta, serves_truth=False)   # sidecar; code blob is untouched

    def read_governance(self, unit: str, rev: str) -> dict:
        return dict(self._notes.get((unit, rev), {}))


class ClientPlatformBackend:
    """Maps the port onto a CLIENT platform (github/gitlab/gitea/...). The unit's code lives in THE CLIENT'S repo;
    our governance rides in the sidecar notes ref. Live calls need network + the client's creds → OWNER-GATED;
    offline it mirrors to a LocalGitBackend (the DEFER-GATE equivalent) so the abstraction is fully testable."""

    def __init__(self, platform: str, repo: str, *, live: bool = False) -> None:
        if platform not in SUPPORTED_PLATFORMS:
            raise ValueError(f"unsupported platform {platform!r}; one of {SUPPORTED_PLATFORMS}")
        self.platform = platform
        self.repo = repo
        self.live = live
        self._mirror = LocalGitBackend(platform)        # offline mirror (and the local equivalent)

    def _guard(self) -> None:
        if self.live:
            raise PermissionError(
                f"live {self.platform} calls need network + the client's credentials (owner-gated); "
                f"run offline (live=False) to mirror, or provision creds in the control plane")

    def commit(self, unit, content, *, message, now):
        self._guard(); return self._mirror.commit(unit, content, message=message, now=now)

    def read(self, unit, rev):
        self._guard(); return self._mirror.read(unit, rev)

    def history(self, unit):
        self._guard(); return self._mirror.history(unit)

    def diff(self, unit, rev_a, rev_b):
        self._guard(); return self._mirror.diff(unit, rev_a, rev_b)

    def tag(self, unit, rev, name):
        self._guard(); self._mirror.tag(unit, rev, name)

    def attach_governance(self, unit, rev, meta):
        self._guard(); self._mirror.attach_governance(unit, rev, meta)

    def read_governance(self, unit, rev):
        self._guard(); return self._mirror.read_governance(unit, rev)


@dataclass
class CapabilityUnitVCS:
    """Govern a capability unit's lifecycle on ANY git backend: commit the code, version it, diff it, and attach the
    governed metadata in the SIDECAR (so the client's code stays clean). The backend is a storage choice; truth lives
    in the control plane (serves_truth False)."""
    backend: object
    governed_meta_keys: tuple = ("verified", "measured_lift", "receipt_id", "provenance")

    def commit_unit(self, unit: str, code: str, *, message: str, now: str, governance: dict | None = None) -> dict:
        ref = self.backend.commit(unit, code, message=message, now=now)
        gov = {k: governance[k] for k in self.governed_meta_keys if governance and k in governance} if governance else {}
        if gov:
            self.backend.attach_governance(unit, ref.rev, gov)
        return {"ref": ref.as_dict(), "backend": self.backend.platform, "governance_sidecar": gov,
                "code_blob_has_governance": False, "serves_truth": False}

    def history(self, unit: str) -> list[dict]:
        return [r.as_dict() for r in self.backend.history(unit)]

    def diff(self, unit: str, rev_a: str, rev_b: str) -> str:
        return self.backend.diff(unit, rev_a, rev_b)
