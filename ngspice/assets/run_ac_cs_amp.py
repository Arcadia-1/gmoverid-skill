#!/usr/bin/env python3
"""
run_ac_cs_amp.py
================
Entry point: run common-source NMOS amplifier AC frequency response simulation.

Usage
-----
    python run_ac_cs_amp.py
"""

from simulate_ac_cs_amp import simulate_all
from plot_ac_cs_amp import plot_all

print("=" * 60)
print("  Common-Source NMOS Amplifier — AC Frequency Response")
print("=" * 60)
print("  PTM 180nm,  W = 10 um,  L = 0.18 um")
print("  Vgs = 0.6 V,  Rd = 2k,  CL = 1p")
print()

result = simulate_all()
plot_all(result)

print("\n  Done.")
