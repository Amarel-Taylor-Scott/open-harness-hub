"""Source sync/status helpers for the Baltor admin demo."""
from __future__ import annotations

import datetime as _dt
import hashlib
import re
import time


def _iso_now() -> str:
    return _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sync_label(ts: float | None) -> str:
    if not ts:
        return "not synced yet"
    seconds = max(0, int(time.time() - ts))
    if seconds < 60:
        return "just now"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    hours = minutes // 60
    if hours < 24:
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    days = hours // 24
    return f"{days} day{'s' if days != 1 else ''} ago"


def _compact_space(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _source_hash(source: dict, text: str = "") -> str:
    seed = "\n".join([
        str(source.get("type") or ""),
        str(source.get("name") or ""),
        str(source.get("size") or ""),
        str(source.get("last_modified") or ""),
        str(source.get("text") or text or ""),
    ])
    return hashlib.sha1(seed.encode("utf-8", errors="ignore")).hexdigest()[:12]


def _source_version_label(digest: str) -> str:
    return f"v-{digest[:7]}"


def source_statuses(sources: list[dict], text: str) -> list[dict]:
    now = time.time()
    normalized: list[dict] = []
    fallback_source = {"type": "text", "name": "raw-text-fallback.txt", "status": "text ready", "text": text}
    for i, source in enumerate(sources or [fallback_source]):
        name = _compact_space(str(source.get("name") or f"source-{i + 1}"))[:160]
        source_type = _compact_space(str(source.get("type") or "source"))[:40]
        status = _compact_space(str(source.get("status") or "selected"))[:160]
        has_text = bool(str(source.get("text") or "").strip()) or bool(text.strip())
        pending_extractor = "queued for extractor" in status.lower()
        connector = source_type == "connector"
        digest = str(source.get("content_hash") or _source_hash(source, text if i == 0 else ""))
        last_synced_at = float(source.get("last_synced_at") or 0) or (now if has_text and not pending_extractor else 0)
        sync_state = "pending_extractor" if pending_extractor else "connector_ready" if connector and not has_text else "synced"
        change_state = "new" if sync_state == "synced" else "waiting"
        normalized.append({
            "id": f"src-{digest[:8]}",
            "type": source_type,
            "name": name,
            "sync_state": sync_state,
            "change_state": change_state,
            "version": _source_version_label(digest),
            "content_hash": digest,
            "size": int(source.get("size") or len(str(source.get("text") or "")) or 0),
            "last_synced_at": last_synced_at,
            "last_synced_iso": _iso_now() if last_synced_at else "",
            "last_sync_label": _sync_label(last_synced_at),
            "next_action": (
                "extract text before graph processing"
                if pending_extractor else
                "authorize connector and schedule first sync"
                if connector and not has_text else
                "track diff and refresh when source hash changes"
            ),
        })
    return normalized[:40]
