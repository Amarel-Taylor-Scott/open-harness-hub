#!/usr/bin/env python3
"""scripts.check_portfolio_website_discovery.py — PROOF (portfolio websites): discovery.
Thin stub; logic lives in scripts/portfolio_checks.py (single source). Deterministic + offline. Exit 0/1."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts import portfolio_checks as C

if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(C.run("discovery"))
    print("usage: python3 scripts/check_portfolio_website_discovery.py --self-test")
    raise SystemExit(0)
