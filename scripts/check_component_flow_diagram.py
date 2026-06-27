#!/usr/bin/env python3
"""scripts.check_component_flow_diagram — proof for #12: the Hub→Teleon→Baltor component-flow diagram exists and
correctly shows the architecture (the 4 brand pillars + the dependency-law direction, as SVG). serves_truth=false."""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DIAG = REPO / "dist" / "sites" / "aidoneright-design" / "diagrams" / "component-flow.html"


def self_test() -> int:
    assert DIAG.exists(), "component-flow diagram missing"
    t = DIAG.read_text(encoding="utf-8")
    for node in ("Open*Hubs", "Teleon", "Baltor", "AIDevObserver"):
        assert node in t, f"diagram missing pillar {node}"
    assert "Baltor → Teleon → OpenHarnessHub" in t, "diagram must state the dependency law"
    assert "<svg" in t and "</svg>" in t, "diagram must be SVG"
    print("check_component_flow_diagram self-test: OK (4 pillars + dependency law + SVG)")
    return 0


def main(argv: list[str]) -> int:
    if "--self-test" in argv:
        return self_test()
    print("usage: check_component_flow_diagram.py --self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
