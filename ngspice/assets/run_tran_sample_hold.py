#!/usr/bin/env python3
"""
run_sample_hold.py
==================
Entry point: run sample-and-hold switch comparison then generate plots.

Usage
-----
    python run_sample_hold.py
"""

from simulate_tran_sample_hold import simulate_all
from plot_tran_sample_hold import plot_all

print("=" * 60)
print("  Sample-and-Hold  –  Switch Model Comparison")
print("=" * 60)
print("  Models: 180nm NMOS  /  Ideal SPICE subckt")
print()

results = simulate_all()
plot_all(results)

print("\n  Done.")
