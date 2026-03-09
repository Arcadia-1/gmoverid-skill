#!/usr/bin/env python3
"""
simulate_dc_current_mirror.py
=============================
Simulation engine for NMOS current mirror DC output characteristic.

Sweeps output voltage (Vout) and measures mirror output current (Iout).

Public API
----------
simulate_all() -> dict with keys: vout, iout, iref, W, L, vgs_m1
"""

import tempfile
import os
import numpy as np

from ngspice_common import (
    LOG_DIR, MODEL_DIR, render_template, run_ngspice, parse_print_table, spath,
)

# ─────────────────────────────────────────────────────────────────────────────
# Circuit parameters
# ─────────────────────────────────────────────────────────────────────────────
W_UM       = 10.0
L_UM       = 0.5        # longer channel for better mirror accuracy
VDD        = 1.8
IREF       = "100u"     # 100 µA reference current
IREF_SI    = 100e-6
VOUT_START = 0.0
VOUT_STOP  = 1.8
VOUT_STEP  = 0.01


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────
def simulate_all():
    """Run current mirror DC sweep. Returns result dict."""
    print(f"    W = {W_UM} um,  L = {L_UM} um,  Iref = {IREF}")
    print(f"    Vout sweep: {VOUT_START} – {VOUT_STOP} V,  step {VOUT_STEP} V")
    print(f"    Running ...", end=" ", flush=True)

    log_path = LOG_DIR / "dc_current_mirror.log"

    text = render_template(
        "dc_current_mirror.cir.tmpl",
        model_path=spath(MODEL_DIR / "ptm180.lib"),
        W=W_UM, L=L_UM,
        vdd=VDD,
        Iref=IREF,
        vout_start=VOUT_START,
        vout_stop=VOUT_STOP,
        vout_step=VOUT_STEP,
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

    if data is not None and data.shape[1] >= 2:
        vout = data[:, 0]
        # ngspice current convention: i(Vout) is negative for current into drain
        iout = np.abs(data[:, 1])
    else:
        vout, iout = None, None

    return {
        "vout":  vout,
        "iout":  iout,
        "iref":  IREF_SI,
        "W":     W_UM,
        "L":     L_UM,
    }
