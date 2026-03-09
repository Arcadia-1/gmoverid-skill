#!/usr/bin/env python3
"""
run_dc_current_mirror.py
========================
Entry point: run NMOS current mirror DC output characteristic simulation.

Usage
-----
    python run_dc_current_mirror.py
"""

from simulate_dc_current_mirror import simulate_all
from plot_dc_current_mirror import plot_all

print("=" * 60)
print("  NMOS Current Mirror — DC Output Characteristic")
print("=" * 60)
print("  PTM 180nm,  W = 10 um,  L = 0.5 um")
print("  Iref = 100 uA,  1:1 mirror ratio")
print()

result = simulate_all()
plot_all(result)

print("\n  Done.")
