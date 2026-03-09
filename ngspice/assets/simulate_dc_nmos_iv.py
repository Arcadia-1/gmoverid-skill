#!/usr/bin/env python3
"""
simulate_dc.py
==============
Simulation engine for NMOS DC Id-Vds family curves.

Sweeps Vds at multiple Vgs bias points using the PTM 180nm NMOS model.

Public API
----------
simulate_all() -> list of result dicts
    Each dict: {vgs, color, data (ndarray N×2: [vds, id])}
"""

import tempfile
import os
import numpy as np

from ngspice_common import (
    LOG_DIR, MODEL_DIR, render_template, run_ngspice, parse_print_table, spath,
)

# ─────────────────────────────────────────────────────────────────────────────
# Device and sweep parameters
# ─────────────────────────────────────────────────────────────────────────────
W_UM      = 10.0
L_UM      = 0.18
VDS_STOP  = 1.8
VDS_STEP  = 0.01

VGS_LIST  = [0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8]

COLORS = [
    "#bdbdbd",     # 0.4V — near Vth, barely on
    "#9ecae1",     # 0.6V
    "#6baed6",     # 0.8V
    "#3182bd",     # 1.0V
    "#e6550d",     # 1.2V
    "#fd8d3c",     # 1.4V
    "#d62728",     # 1.6V
    "#8b0000",     # 1.8V
]


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────
def simulate_all():
    """Sweep Vds at each Vgs bias point. Returns list of result dicts."""
    results = []
    for i, vgs in enumerate(VGS_LIST):
        print(f"    Vgs = {vgs:.1f} V ...", end=" ", flush=True)

        log_path = LOG_DIR / f"nmos_dc_vgs{vgs:.1f}.log"

        text = render_template(
            "dc_nmos_iv.cir.tmpl",
            model_path=spath(MODEL_DIR / "ptm180.lib"),
            W=W_UM, L=L_UM,
            vgs=vgs,
            vds_stop=VDS_STOP,
            vds_step=VDS_STEP,
        )
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".cir", delete=False, encoding="utf-8"
        ) as f:
            f.write(text)
            tmp = f.name
        try:
            rc = run_ngspice(tmp, log=log_path)
        finally:
            os.unlink(tmp)

        data = parse_print_table(log_path)
        n = len(data) if data is not None else 0
        print(f"exit {rc},  {n} pts")

        # ngspice reports current into Vds source (negative for NMOS drain current)
        # Take absolute value so Id is positive
        if data is not None and data.shape[1] >= 2:
            data[:, 1] = np.abs(data[:, 1])

        results.append({
            "vgs":   vgs,
            "color": COLORS[i % len(COLORS)],
            "data":  data,
        })
    return results
