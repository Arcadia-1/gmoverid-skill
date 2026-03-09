#!/usr/bin/env python3
"""
plot_tran_rc_charging.py
========================
Plotting routines for RC charging transient — voltage and current.

Public API
----------
plot_all(results)
    Two-panel figure: voltage and current vs time.
    results: list of dicts from simulate_tran_rc_charging.simulate_all()
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from ngspice_common import PLOT_DIR

OUT_PNG = PLOT_DIR / "tran_rc_charging.png"


def plot_all(results):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
    fig.suptitle("RC Charging Transient — Voltage & Current", fontsize=13)

    for r in results:
        data = r["data"]
        if data is None or data.shape[1] < 3:
            continue
        time_ns = data[:, 0] * 1e9
        vout = data[:, 1]
        icur_ua = data[:, 2] * 1e6   # convert to µA
        tau = r["tau"]
        color = r["color"]
        label = r["label"]

        # Panel 1: voltage
        ax1.plot(time_ns, vout, color=color, linewidth=2, label=label)
        # Mark tau point
        ax1.axvline(tau * 1e9, color=color, linestyle=":", linewidth=1, alpha=0.5)

        # Panel 2: current
        ax2.plot(time_ns, icur_ua, color=color, linewidth=2, label=label)
        ax2.axvline(tau * 1e9, color=color, linestyle=":", linewidth=1, alpha=0.5)

    # Voltage panel
    ax1.axhline(results[0]["Vin"], color="gray", linestyle="--", linewidth=0.8)
    ax1.set_ylabel("$V_{out}$ (V)")
    ax1.set_title("Capacitor Voltage  —  $V_{out} = V_{in}(1 - e^{-t/\\tau})$")
    ax1.legend(fontsize=9)
    ax1.grid(True, alpha=0.3)
    ax1.set_ylim(bottom=0)

    # Current panel
    ax2.axhline(0, color="gray", linestyle="--", linewidth=0.8)
    ax2.set_xlabel("Time (ns)")
    ax2.set_ylabel("$I$ ($\\mu$A)")
    ax2.set_title("Charging Current  —  $I = (V_{in}/R) \\cdot e^{-t/\\tau}$")
    ax2.legend(fontsize=9)
    ax2.grid(True, alpha=0.3)
    ax2.set_ylim(bottom=0)

    plt.tight_layout()
    plt.savefig(OUT_PNG, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved → {OUT_PNG.name}")
