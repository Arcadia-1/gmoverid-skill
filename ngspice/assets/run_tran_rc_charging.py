#!/usr/bin/env python3
"""
run_tran_rc_charging.py
=======================
Entry point: run RC charging transient simulations then generate plots.

Usage
-----
    python run_tran_rc_charging.py
"""

from simulate_tran_rc_charging import simulate_all
from plot_tran_rc_charging import plot_all

print("=" * 60)
print("  RC Charging Transient — Voltage & Current")
print("=" * 60)
print("  Vin = 1 V (DC step)")
print("  Configs: R=1k/C=1p (tau=1ns),  R=10k/C=1p (tau=10ns)")
print()

results = simulate_all()
plot_all(results)

print("\n  Done.")
