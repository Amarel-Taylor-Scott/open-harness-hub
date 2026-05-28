"""The paste-to-flow showcase — modular package (one file per concern).

  pages.py    HTML templates (Build + Browse)
  index.py    Index — load the vector store + hybrid search
  builder.py  retrieve → orchestrate → cost → narrate → build_flow
  export.py   export_flow (assembled flow → portable pipeline component)
  server.py   HTTP handler + serve()
"""
from __future__ import annotations

from scripts.showcase.builder import build_flow
from scripts.showcase.export import export_flow
from scripts.showcase.index import Index
from scripts.showcase.server import main, serve

__all__ = ["Index", "build_flow", "export_flow", "serve", "main"]
