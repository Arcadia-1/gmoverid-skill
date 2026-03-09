#!/usr/bin/env python3
"""
run_dc.py
=========
Entry point: run NMOS DC Id-Vds family curve simulations then generate plots.

Usage
-----
    python run_dc.py
"""

from simulate_dc_nmos_iv import simulate_all
from plot_dc_nmos_iv import plot_all

print("=" * 60)
print("  NMOS DC I-V Family Curves  –  PTM 180nm")
print("=" * 60)
print("  W = 10 µm,  L = 0.18 µm")
print("  Vgs = {0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8} V")
print()

results = simulate_all()
plot_all(results)

print("\n  Done.")
