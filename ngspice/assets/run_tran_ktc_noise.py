#!/usr/bin/env python3
"""
run_tran_ktc_noise.py
=====================
Entry point: run kT/C noise time-domain statistical measurement.

Usage
-----
    python run_tran_ktc_noise.py
"""

from simulate_tran_ktc_noise import simulate_all
from plot_tran_ktc_noise import plot_all

print("=" * 60)
print("  kT/C Noise — Time-Domain Statistical Measurement")
print("=" * 60)
print("  DC input = 0.9 V,  R auto-tuned per cap (tau = 50 ps)")
print("  Capacitors: 10 fF  /  1 pF  /  100 pF")
print("  10000 samples per cap value, 3 sims in parallel")
print()

results = simulate_all()
plot_all(results)

print("\n  Done.")
