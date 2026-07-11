#!/usr/bin/env python3
"""scripts.check_portfolio_launch_full_stack.py — PROOF (portfolio websites): launch_full_stack.
Thin stub; logic lives in _repos/shared-backend-components/scripts/portfolio_checks.py (single source). Deterministic + offline. Exit 0/1."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts import portfolio_checks as C

if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(C.run("launch_full_stack"))
    print("usage: python3 scripts/check_portfolio_launch_full_stack.py --self-test")
    raise SystemExit(0)
