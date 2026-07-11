"""Approved egress transport adapters.

Raw network libraries are isolated here so worker code cannot silently bypass
the egress intent, route decision, ledger, and observation contracts.
"""
from __future__ import annotations

import urllib.error
import urllib.request
from dataclasses import dataclass


class EgressTransportError(RuntimeError):
    """Raised when an approved transport cannot complete the request."""


@dataclass(frozen=True)
class EgressTransportResponse:
    status_code: int
    headers: dict[str, str]
    body: bytes

    @property
    def text(self) -> str:
        return self.body.decode("utf-8", errors="replace")

    @property
    def content_type(self) -> str:
        return self.headers.get("content-type") or self.headers.get("Content-Type") or ""


class UrllibHttpTransport:
    """Stdlib HTTP transport behind the egress broker."""

    transport_kind = "urllib_http"

    def request(
        self,
        *,
        method: str,
        url: str,
        body: bytes | None = None,
        headers: dict[str, str] | None = None,
        timeout_s: int = 30,
    ) -> EgressTransportResponse:
        req = urllib.request.Request(url, data=body, headers=headers or {}, method=method.upper())
        try:
            with urllib.request.urlopen(req, timeout=timeout_s) as response:  # noqa: S310 - approved transport adapter
                return EgressTransportResponse(
                    status_code=int(response.status),
                    headers={str(k): str(v) for k, v in response.headers.items()},
                    body=response.read(),
                )
        except urllib.error.URLError as exc:
            raise EgressTransportError(repr(exc)) from exc


__all__ = ["EgressTransportError", "EgressTransportResponse", "UrllibHttpTransport"]
