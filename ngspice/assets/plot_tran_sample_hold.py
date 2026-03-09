#!/usr/bin/env python3
"""
plot_sample_hold.py
===================
Plotting routines for the sample-and-hold switch comparison.

Public API
----------
plot_all(results)
    Three-panel figure: full waveform / clock / zoom.
    results: list of dicts from simulate_sample_hold.simulate_all()
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from ngspice_common import PLOT_DIR

OUT_PNG  = PLOT_DIR / "sample_hold_compare.png"
ZOOM_NS  = 50   # ns


def _shade_on_periods(ax, t, vclk, ylo, yhi):
    ax.fill_between(t, ylo, yhi, where=(vclk > 0.9),
                    color="limegreen", alpha=0.13, linewidth=0,
                    label="Switch ON")


def plot_all(results):
    d0 = results[0]["data"]
    if d0 is None:
        print("ERROR: no data from first simulation")
        return

    time0 = d0[:, 0] * 1e9   # ns
    vclk  = d0[:, 2]

    fig, axes = plt.subplots(
        3, 1, figsize=(13, 10),
        gridspec_kw={"height_ratios": [3, 1.2, 3]},
    )
    fig.suptitle(
        "Sample-and-Hold — Switch Model Comparison\n"
        "Input: 10 MHz sine  |  Clock: 100 MHz, 25 % duty  |  $C_{samp}$ = 1 pF\n"
        "Models: 180nm NMOS  vs  Ideal (SPICE subckt)",
        fontsize=11,
    )

    # Panel 1: full waveform
    ax1 = axes[0]
    ax1.plot(time0, d0[:, 1], color="black", lw=1.0, ls="--",
             label="$V_{in}$ (10 MHz sine)", alpha=0.6)
    for r in results:
        if r["data"] is not None:
            t = r["data"][:, 0] * 1e9
            ax1.plot(t, r["data"][:, 3],
                     color=r["color"], lw=1.2, ls=r.get("ls", "-"),
                     label=r["label"])
    ax1.set_ylabel("Voltage (V)")
    ax1.set_title("Full simulation  (0 – 250 ns)")
    ax1.legend(loc="upper right", fontsize=9)
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(time0[0], time0[-1])

    # Panel 2: clock
    ax2 = axes[1]
    ax2.fill_between(time0, 0, vclk, color="gray", alpha=0.35, linewidth=0)
    ax2.plot(time0, vclk, color="dimgray", lw=0.8)
    ax2.set_ylabel("Gate (V)")
    ax2.set_ylim(-0.3, 2.5)
    ax2.set_yticks([0, 0.9, 1.8])
    ax2.set_title("Gate clock  (100 MHz, 25 % duty)")
    ax2.grid(True, alpha=0.3)
    ax2.set_xlim(time0[0], time0[-1])

    # Panel 3: zoom
    ax3 = axes[2]
    zm0  = time0 <= ZOOM_NS
    ylo  = d0[zm0, 1].min() - 0.05
    yhi  = d0[zm0, 1].max() + 0.05
    _shade_on_periods(ax3, time0[zm0], vclk[zm0], ylo, yhi)
    ax3.plot(time0[zm0], d0[zm0, 1], color="black", lw=1.0, ls="--",
             label="$V_{in}$", alpha=0.6)
    for r in results:
        if r["data"] is not None:
            t  = r["data"][:, 0] * 1e9
            zm = t <= ZOOM_NS
            ax3.plot(t[zm], r["data"][zm, 3],
                     color=r["color"], lw=1.8, ls=r.get("ls", "-"),
                     label=r["label"])
    ax3.set_xlabel("Time (ns)")
    ax3.set_ylabel("Voltage (V)")
    ax3.set_title(f"Zoom: 0 – {ZOOM_NS} ns  (green = switch ON)")
    ax3.legend(loc="upper right", fontsize=9)
    ax3.grid(True, alpha=0.3)
    ax3.set_xlim(0, ZOOM_NS)

    plt.tight_layout()
    plt.savefig(OUT_PNG, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved → {OUT_PNG.name}")
