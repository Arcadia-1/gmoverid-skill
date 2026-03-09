#!/usr/bin/env python3
"""
run_dc_tgate_ron.py
===================
Entry point: run transmission gate Ron vs pass voltage simulation.

Usage
-----
    python run_dc_tgate_ron.py
"""

from simulate_dc_tgate_ron import simulate_all
from plot_dc_tgate_ron import plot_all

print("=" * 60)
print("  Transmission Gate Ron — DC Sweep")
print("=" * 60)
print("  NMOS + PMOS complementary switch,  W/L = 100")
print("  Nodes: 180nm / 45nm HP / 22nm HP")
print()

results = simulate_all()
plot_all(results)

print("\n  Done.")
