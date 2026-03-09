#!/usr/bin/env python3
"""
simulate_ac_cs_amp.py
=====================
Simulation engine for common-source NMOS amplifier AC frequency response.

Public API
----------
simulate_all() -> dict with keys: freq, gain_db, phase_deg, gain_dc, f3db, W, L, Rd, CL, vgs_bias
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
W_UM      = 10.0
L_UM      = 0.18
VDD       = 1.8
VGS_BIAS  = 0.6          # DC gate bias [V]
RD        = "2k"          # Load resistor
RD_SI     = 2e3
CL        = "1p"          # Load capacitor
CL_SI     = 1e-12
FREQ_START = "1k"
FREQ_STOP  = "100G"


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────
def simulate_all():
    """Run CS amp AC simulation. Returns result dict."""
    print(f"    W = {W_UM} um,  L = {L_UM} um")
    print(f"    Vgs_bias = {VGS_BIAS} V,  Rd = {RD},  CL = {CL}")
    print(f"    Running ...", end=" ", flush=True)

    log_path = LOG_DIR / "ac_cs_amp.log"

    text = render_template(
        "ac_cs_amp.cir.tmpl",
        model_path=spath(MODEL_DIR / "ptm180.lib"),
        W=W_UM, L=L_UM,
        vdd=VDD,
        vgs_bias=VGS_BIAS,
        Rd=RD,
        CL=CL,
        fstart=FREQ_START,
        fstop=FREQ_STOP,
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

    raw = parse_print_table(log_path)
    n = len(raw) if raw is not None else 0
    print(f"exit {rc},  {n} pts")

    if raw is None or raw.shape[1] < 3:
        return {"freq": None, "gain_db": None, "phase_deg": None}

    freq = raw[:, 0]
    # ngspice AC output: [freq, real(v), imag(v)]
    vreal = raw[:, 1]
    vimag = raw[:, 2]
    mag = np.sqrt(vreal**2 + vimag**2)
    gain_db = 20 * np.log10(mag + 1e-30)
    phase_deg = np.degrees(np.arctan2(vimag, vreal))

    # Extract DC gain and -3dB frequency
    gain_dc = gain_db[0]
    target = gain_dc - 3.0
    idx_3db = np.argmax(gain_db < target) if np.any(gain_db < target) else -1
    f3db = freq[idx_3db] if idx_3db > 0 else None

    print(f"    DC gain = {gain_dc:.1f} dB")
    if f3db:
        print(f"    f_3dB   = {f3db/1e6:.1f} MHz")
    f3db_theory = 1 / (2 * np.pi * RD_SI * CL_SI)
    print(f"    f_3dB theory (1/(2*pi*Rd*CL)) = {f3db_theory/1e6:.1f} MHz")

    return {
        "freq":      freq,
        "gain_db":   gain_db,
        "phase_deg": phase_deg,
        "gain_dc":   gain_dc,
        "f3db":      f3db,
        "W":         W_UM,
        "L":         L_UM,
        "Rd":        RD,
        "CL":        CL,
        "vgs_bias":  VGS_BIAS,
    }
