#!/usr/bin/env python3
"""
plot_dc_current_mirror.py
=========================
Plotting routines for NMOS current mirror DC output characteristic.

Public API
----------
plot_all(result)
    Single figure: Iout vs Vout with Iref reference line.
    result: dict from simulate_dc_current_mirror.simulate_all()
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from ngspice_common import PLOT_DIR

OUT_PNG = PLOT_DIR / "dc_current_mirror.png"


def plot_all(result):
    vout = result["vout"]
    iout = result["iout"]
    if vout is None or iout is None:
        print("  ERROR: no data to plot")
        return

    iref = result["iref"]
    W = result["W"]
    L = result["L"]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8),
                                    gridspec_kw={"height_ratios": [3, 1]})
    fig.suptitle(
        f"NMOS Current Mirror — PTM 180nm  (W={W}$\\mu$m, L={L}$\\mu$m)\n"
        f"$I_{{ref}}$ = {iref*1e6:.0f} $\\mu$A,  1:1 mirror ratio",
        fontsize=13,
    )

    # Panel 1: Iout vs Vout
    ax1.plot(vout, iout * 1e6, color="royalblue", linewidth=2, label="$I_{out}$")
    ax1.axhline(iref * 1e6, color="red", linestyle="--", linewidth=1.2,
                label=f"$I_{{ref}}$ = {iref*1e6:.0f} $\\mu$A")
    ax1.set_ylabel("$I_{out}$ ($\\mu$A)")
    ax1.set_title("Output Current vs Output Voltage")
    ax1.legend(loc="lower right", fontsize=10)
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(0, 1.8)
    ax1.set_ylim(bottom=0)

    # Panel 2: Iout / Iref ratio
    ratio = iout / iref
    ax2.plot(vout, ratio, color="seagreen", linewidth=2)
    ax2.axhline(1.0, color="red", linestyle="--", linewidth=1)
    ax2.set_xlabel("$V_{out}$ (V)")
    ax2.set_ylabel("$I_{out}$ / $I_{ref}$")
    ax2.set_title("Mirror Accuracy (ratio)")
    ax2.grid(True, alpha=0.3)
    ax2.set_xlim(0, 1.8)
    ax2.set_ylim(0.0, 1.3)

    plt.tight_layout()
    plt.savefig(OUT_PNG, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved → {OUT_PNG.name}")
