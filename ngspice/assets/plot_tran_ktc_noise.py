#!/usr/bin/env python3
"""
plot_tran_ktc_noise.py
======================
Plotting routines for kT/C noise time-domain statistical measurement.

Public API
----------
plot_all(results)
    Three-panel figure: time-domain trace, histogram, and fitted Gaussian.
    results: list of dicts from simulate_tran_ktc_noise.simulate_all()
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.stats import norm

from ngspice_common import PLOT_DIR

OUT_PNG = PLOT_DIR / "tran_ktc_noise_hist.png"


def plot_all(results):
    n_caps = sum(1 for r in results if r["samples"] is not None)
    if n_caps == 0:
        print("  ERROR: no valid data to plot")
        return

    wall_time = results[0].get("total_wall_time", 0)

    # Layout: 2 rows x n_caps columns — traces on top, histograms on bottom
    fig, axes = plt.subplots(2, n_caps, figsize=(6 * n_caps, 10))
    if n_caps == 1:
        axes = axes[:, np.newaxis]
    fig.suptitle(
        "kT/C Noise — Time-Domain Statistical Measurement\n"
        f"R auto-tuned per cap ($\\tau$ = 50 ps),  DC input = 0.9 V,  "
        f"{n_caps} sims in parallel — wall time {wall_time:.1f} s",
        fontsize=13,
    )

    col = 0
    for r in results:
        if r["samples"] is None:
            continue

        samples = r["samples"]
        sigma_theory = r["sigma_theory"]
        sigma_meas = np.std(samples)
        mean_meas = np.mean(samples)
        color = r["color"]
        label = r["label"]
        sim_time = r.get("sim_time", 0)

        # ── Top row: time-domain trace (first 500 samples) ──
        ax1 = axes[0, col]
        n_show = min(500, len(samples))
        ax1.plot(np.arange(n_show), (samples[:n_show] - mean_meas) * 1e6,
                 color=color, linewidth=0.5, alpha=0.8)
        ax1.axhline(0, color="gray", linestyle=":", linewidth=0.8)
        ax1.axhline(sigma_meas * 1e6, color="red", linestyle="--", linewidth=1,
                     label=f"$\\pm\\sigma$ = {sigma_meas*1e6:.1f} $\\mu$V")
        ax1.axhline(-sigma_meas * 1e6, color="red", linestyle="--", linewidth=1)
        ax1.set_xlabel("Sample index")
        ax1.set_ylabel("$V_{out} - \\overline{V}$ ($\\mu$V)")
        ax1.set_title(f"{label} — Noise Trace  [{sim_time:.1f} s]")
        ax1.legend(fontsize=8)
        ax1.grid(True, alpha=0.3)

        # ── Bottom row: histogram ──
        ax2 = axes[1, col]
        noise_uv = (samples - mean_meas) * 1e6
        n_bins = 80
        counts, bin_edges, patches = ax2.hist(
            noise_uv, bins=n_bins, density=True,
            color=color, alpha=0.6, edgecolor="white", linewidth=0.3,
        )
        # Fitted Gaussian
        x_fit = np.linspace(noise_uv.min(), noise_uv.max(), 300)
        pdf_fit = norm.pdf(x_fit, loc=0, scale=sigma_meas * 1e6)
        ax2.plot(x_fit, pdf_fit, color="red", linewidth=2,
                 label=f"Gaussian fit ($\\sigma$ = {sigma_meas*1e6:.1f} $\\mu$V)")
        # Theory Gaussian
        pdf_theory = norm.pdf(x_fit, loc=0, scale=sigma_theory * 1e6)
        ax2.plot(x_fit, pdf_theory, color="black", linewidth=1.5, linestyle="--",
                 label=f"Theory $\\sqrt{{kT/C}}$ = {sigma_theory*1e6:.1f} $\\mu$V")
        ax2.set_xlabel("$V_{out} - \\overline{V}$ ($\\mu$V)")
        ax2.set_ylabel("Probability density")
        ax2.set_title(f"{label} — Histogram ({len(samples)} samples)")
        ax2.legend(fontsize=8)
        ax2.grid(True, alpha=0.3)

        col += 1

    plt.tight_layout()
    plt.savefig(OUT_PNG, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved → {OUT_PNG.name}")
