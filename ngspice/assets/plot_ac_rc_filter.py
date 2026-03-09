#!/usr/bin/env python3
"""
plot_rc_filter.py
=================
Plotting routines for the RC low-pass filter AC + noise simulation.

Public API
----------
plot_all(results)
    Two-panel figure: gain (dB) and noise spectral density.
    results: list of dicts from simulate_rc_filter.simulate_all()
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from ngspice_common import PLOT_DIR

OUT_PNG = PLOT_DIR / "ac_rc_bw.png"


def plot_all(results):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
    fig.suptitle("RC Low-Pass Filter — Comparative Simulation  (C = 1 pF)",
                 fontsize=13)

    # Panel 1: Gain (dB)
    ax1.axhline(-3, color="gray", linestyle=":", linewidth=1)
    ax1.text(1.1e6, -4.5, "−3 dB", color="gray", fontsize=9)
    for r in results:
        if r["ac_data"] is not None and r["ac_data"].shape[1] >= 2:
            freq    = r["ac_data"][:, 0]
            gain_db = 20 * np.log10(r["ac_data"][:, 1] + 1e-30)
            ax1.semilogx(freq, gain_db, color=r["color_ac"], linewidth=2,
                         label=r["label"])
            ax1.axvline(r["fc"], color=r["color_ac"], linestyle="--",
                        linewidth=1.2, alpha=0.7,
                        label=f"  $f_c$ = {r['fc']/1e6:.1f} MHz")
    ax1.set_xlabel("Frequency (Hz)")
    ax1.set_ylabel("Gain (dB)")
    ax1.set_title("AC Frequency Response — Bandwidth")
    ax1.legend(loc="lower left", fontsize=9)
    ax1.grid(True, which="both", alpha=0.3)
    ax1.set_ylim(bottom=-60)

    # Panel 2: Output noise density
    for r in results:
        if r["noise_data"] is not None and r["noise_data"].shape[1] >= 2:
            freq      = r["noise_data"][:, 0]
            v_sqrt_hz = r["noise_data"][:, 1]
            floor         = np.sqrt(4 * 1.38e-23 * 300 * r["R"])
            ktc_uv_theory = np.sqrt(1.38e-23 * 300 / r["C"]) * 1e6
            ktc_uv_sim    = np.sqrt(np.trapezoid(v_sqrt_hz**2, freq)) * 1e6
            ax2.loglog(freq, v_sqrt_hz, color=r["color_noise"], linewidth=2,
                       label=(f"{r['label']}  "
                              f"(√4kTR={floor*1e9:.1f} nV/√Hz,  "
                              f"√(kT/C): theory={ktc_uv_theory:.1f} µV  "
                              f"sim={ktc_uv_sim:.1f} µV)"))
            ax2.axvline(r["fc"], color=r["color_noise"], linestyle="--",
                        linewidth=1.2, alpha=0.7)
    ax2.set_xlabel("Frequency (Hz)")
    ax2.set_ylabel("Noise spectral density (V/√Hz)")
    ax2.set_title("Output Noise Spectrum")
    ax2.legend(loc="lower left", fontsize=9)
    ax2.grid(True, which="both", alpha=0.3)

    plt.tight_layout()
    plt.savefig(OUT_PNG, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved → {OUT_PNG.name}")
