#!/usr/bin/env python3
"""
plot_dc.py
==========
Plotting routines for NMOS DC Id-Vds family curves.

Public API
----------
plot_all(results)
    Single figure with Id vs Vds at multiple Vgs values.
    results: list of dicts from simulate_dc.simulate_all()
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from ngspice_common import PLOT_DIR

OUT_PNG = PLOT_DIR / "dc_nmos_iv.png"


def plot_all(results):
    fig, ax = plt.subplots(1, 1, figsize=(10, 6))
    fig.suptitle("NMOS DC I-V Family Curves — PTM 180nm  (W=10µm, L=0.18µm)",
                 fontsize=13)

    for r in results:
        if r["data"] is not None and r["data"].shape[1] >= 2:
            vds = r["data"][:, 0]
            ids = r["data"][:, 1] * 1e6  # convert to µA
            ax.plot(vds, ids, color=r["color"], linewidth=1.8,
                    label=f"Vgs = {r['vgs']:.1f} V")

    ax.set_xlabel("$V_{DS}$ (V)")
    ax.set_ylabel("$I_D$ (µA)")
    ax.set_title("$I_D$ vs $V_{DS}$ at Various $V_{GS}$")
    ax.legend(loc="upper left", fontsize=9, ncol=2)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(0, 1.8)
    ax.set_ylim(bottom=0)

    plt.tight_layout()
    plt.savefig(OUT_PNG, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved → {OUT_PNG.name}")
