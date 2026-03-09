#!/usr/bin/env python3
"""
plot_ac_cs_amp.py
=================
Plotting routines for common-source NMOS amplifier AC frequency response.

Public API
----------
plot_all(result)
    Two-panel Bode plot: gain (dB) and phase (degrees).
    result: dict from simulate_ac_cs_amp.simulate_all()
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from ngspice_common import PLOT_DIR

OUT_PNG = PLOT_DIR / "ac_cs_amp_bode.png"


def plot_all(result):
    freq = result["freq"]
    gain_db = result["gain_db"]
    phase_deg = result["phase_deg"]

    if freq is None:
        print("  ERROR: no data to plot")
        return

    gain_dc = result.get("gain_dc", 0)
    f3db = result.get("f3db")
    W = result.get("W", 10)
    L = result.get("L", 0.18)
    Rd = result.get("Rd", "2k")
    CL = result.get("CL", "1p")
    vgs = result.get("vgs_bias", 0.6)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
    fig.suptitle(
        f"Common-Source NMOS Amplifier — PTM 180nm\n"
        f"W={W}$\\mu$m, L={L}$\\mu$m,  $V_{{GS}}$={vgs}V,  "
        f"$R_D$={Rd},  $C_L$={CL}",
        fontsize=13,
    )

    # Panel 1: Gain (dB)
    ax1.semilogx(freq, gain_db, color="royalblue", linewidth=2, label="Gain")
    ax1.axhline(gain_dc - 3, color="gray", linestyle=":", linewidth=1)
    ax1.text(freq[1], gain_dc - 4.5, "$-$3 dB", color="gray", fontsize=9)
    if f3db:
        ax1.axvline(f3db, color="red", linestyle="--", linewidth=1.2, alpha=0.7,
                     label=f"$f_{{3dB}}$ = {f3db/1e6:.1f} MHz")
    ax1.set_ylabel("Gain (dB)")
    ax1.set_title(f"Voltage Gain  (DC gain = {gain_dc:.1f} dB)")
    ax1.legend(loc="lower left", fontsize=10)
    ax1.grid(True, which="both", alpha=0.3)
    ax1.set_xlim(freq[0], freq[-1])

    # Panel 2: Phase
    ax2.semilogx(freq, phase_deg, color="darkorange", linewidth=2)
    ax2.axhline(180, color="gray", linestyle=":", linewidth=0.8)
    ax2.axhline(90, color="gray", linestyle=":", linewidth=0.8)
    if f3db:
        ax2.axvline(f3db, color="red", linestyle="--", linewidth=1.2, alpha=0.7)
    ax2.set_xlabel("Frequency (Hz)")
    ax2.set_ylabel("Phase (degrees)")
    ax2.set_title("Phase Response")
    ax2.grid(True, which="both", alpha=0.3)
    ax2.set_xlim(freq[0], freq[-1])

    plt.tight_layout()
    plt.savefig(OUT_PNG, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved → {OUT_PNG.name}")
