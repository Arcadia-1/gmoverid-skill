#!/usr/bin/env python3
"""
simulate_tran_rc_charging.py
============================
Simulation engine for RC charging transient — voltage and current waveforms.

Public API
----------
simulate_all() -> list of result dicts
    Each dict: {label, color, R, C, tau, Vin, data (ndarray N×3: [time, v(out), i(Vin)])}
"""

import tempfile
import os
import numpy as np

from ngspice_common import (
    LOG_DIR, render_template, run_ngspice, parse_print_table,
)

# ─────────────────────────────────────────────────────────────────────────────
# RC configurations
# ─────────────────────────────────────────────────────────────────────────────
VIN = 1.0

CONFIGS = [
    {
        "label":   "R=1k, C=1p  (tau=1ns)",
        "R":       1e3,  "C":       1e-12,
        "R_spice": "1k", "C_spice": "1p",
        "color":   "royalblue",
        "log":     LOG_DIR / "tran_rc_1k_1p.log",
    },
    {
        "label":   "R=10k, C=1p  (tau=10ns)",
        "R":       1e4,  "C":       1e-12,
        "R_spice": "10k", "C_spice": "1p",
        "color":   "darkorange",
        "log":     LOG_DIR / "tran_rc_10k_1p.log",
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────
def simulate_all():
    """Run RC charging transient for all configurations."""
    results = []
    # Use the same stop time for all configs (10× the slowest tau)
    tau_max = max(c["R"] * c["C"] for c in CONFIGS)
    tstop = 10 * tau_max
    tstep = tau_max / 500       # fine enough for the fastest config too

    for cfg in CONFIGS:
        tau = cfg["R"] * cfg["C"]

        print(f"\n  [{cfg['label']}]  tau = {tau*1e9:.1f} ns")
        print(f"    Running ...", end=" ", flush=True)

        text = render_template(
            "tran_rc_charging.cir.tmpl",
            Vin=VIN,
            R=cfg["R_spice"],
            C=cfg["C_spice"],
            tau_ns=f"{tau*1e9:.1f}",
            tstep=f"{tstep:.4e}",
            tstop=f"{tstop:.4e}",
        )
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".cir", delete=False, encoding="utf-8"
        ) as f:
            f.write(text)
            tmp = f.name
        try:
            rc = run_ngspice(tmp, log=cfg["log"])
        finally:
            os.unlink(tmp)

        data = parse_print_table(cfg["log"])
        n = len(data) if data is not None else 0
        print(f"exit {rc},  {n} pts")

        # ngspice i(Vin): current flows from + to - inside source (into circuit),
        # so it's negative (current leaves the + terminal into the resistor).
        # Take absolute value for a clean plot.
        if data is not None and data.shape[1] >= 3:
            data[:, 2] = np.abs(data[:, 2])

        results.append({
            **cfg,
            "tau":  tau,
            "Vin":  VIN,
            "data": data,
        })
    return results
