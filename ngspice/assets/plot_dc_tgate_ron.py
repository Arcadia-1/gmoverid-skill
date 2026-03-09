#!/usr/bin/env python3
"""
plot_dc_tgate_ron.py
====================
Plotting routines for transmission gate Ron vs pass voltage.

Public API
----------
plot_all(results)
    Single figure: Ron vs Vpass for 180nm, 45nm HP, and 22nm HP.
    results: list of dicts from simulate_dc_tgate_ron.simulate_all()
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from ngspice_common import PLOT_DIR

OUT_PNG = PLOT_DIR / "dc_tgate_ron.png"


def plot_all(results):
    fig, ax = plt.subplots(1, 1, figsize=(10, 6))
    fig.suptitle(
        "Transmission Gate $R_{on}$ vs Pass Voltage\n"
        "NMOS + PMOS complementary switch,  W/L = 100",
        fontsize=13,
    )

    for r in results:
        vpass = r["vpass"]
        ron = r["ron"]
        if vpass is None or ron is None:
            continue
        vdd = r["vdd"]
        ax.plot(vpass, ron, color=r["color"], linewidth=2,
                label=r["label"])

    ax.set_xlabel("$V_{pass}$ (V)")
    ax.set_ylabel("$R_{on}$ ($\\Omega$)")
    ax.set_title("$R_{on}$ vs Pass Voltage")
    ax.legend(loc="upper center", fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.set_ylim(bottom=0)

    plt.tight_layout()
    plt.savefig(OUT_PNG, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved → {OUT_PNG.name}")
