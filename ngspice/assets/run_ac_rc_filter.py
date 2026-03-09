#!/usr/bin/env python3
"""
run_rc_filter.py
================
Entry point: run RC low-pass AC + noise simulations then generate plots.

Usage
-----
    python run_rc_filter.py
"""

from simulate_ac_rc_filter import simulate_all
from plot_ac_rc_filter import plot_all

print("=" * 60)
print("  RC Low-Pass Filter  –  AC + Noise Simulation")
print("=" * 60)

results = simulate_all()
plot_all(results)

print("\n  Done.")
