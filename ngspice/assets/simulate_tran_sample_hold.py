#!/usr/bin/env python3
"""
simulate_sample_hold.py
=======================
Simulation engine for the sample-and-hold switch comparison.

Runs ngspice for two switch models (180nm NMOS, ideal SPICE subckt)
and returns parsed waveform data.

Public API
----------
simulate_all() -> list of result dicts
    Each dict: {label, color, ls, data (ndarray or None)}
"""

import tempfile
import os

from ngspice_common import (
    LOG_DIR, MODEL_DIR, render_template, run_ngspice, parse_print_table, spath,
)

# ─────────────────────────────────────────────────────────────────────────────
# Circuit parameters
# ─────────────────────────────────────────────────────────────────────────────
VDD    = 1.8
W_UM   = 4.0
L_UM   = 0.18
CSAMP  = "1p"
FIN    = "10Meg"
FCLK   = "100Meg"
TCLK   = "10n"      # 1/100MHz
TON    = "2.5n"      # 25% duty
TSTEP  = "0.1n"
TSTOP  = "250n"
RON_IDEAL = 50       # ohm

# ─────────────────────────────────────────────────────────────────────────────
# Simulation configurations
# ─────────────────────────────────────────────────────────────────────────────
SIMS = [
    {
        "label":   f"180 nm NMOS  (W={W_UM}um, Ron~400 Ω)",
        "tmpl":    "tran_sample_hold_nmos.cir.tmpl",
        "log":     LOG_DIR / "sample_hold_180nm.log",
        "color":   "royalblue",
        "ls":      "-",
    },
    {
        "label":   f"Ideal switch - SPICE subckt  (Ron={RON_IDEAL} Ω)",
        "tmpl":    "tran_sample_hold_ideal.cir.tmpl",
        "log":     LOG_DIR / "sample_hold_ideal.log",
        "color":   "darkorange",
        "ls":      "-",
    },
]


def _run_sim(sim):
    """Render template, run ngspice, return exit code."""
    if "nmos" in sim["tmpl"]:
        text = render_template(
            sim["tmpl"],
            model_path=spath(MODEL_DIR / "ptm180.lib"),
            W=W_UM, L=L_UM,
            vdd=VDD,
            Csamp=CSAMP,
            fin=FIN, fclk=FCLK,
            tclk=TCLK, ton=TON,
            tstep=TSTEP, tstop=TSTOP,
        )
    else:
        # Ideal switch: Ron expression for voltage-controlled resistor
        # When ctrl > 0.9 → Ron, else 1G (open)
        ron_expr = f"v(ctrl) > 0.9 ? {RON_IDEAL} : 1G"
        text = render_template(
            sim["tmpl"],
            Ron_expr=ron_expr,
            Csamp=CSAMP,
            fin=FIN, fclk=FCLK,
            tclk=TCLK, ton=TON,
            tstep=TSTEP, tstop=TSTOP,
        )
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".cir", delete=False, encoding="utf-8"
    ) as f:
        f.write(text)
        tmp = f.name
    try:
        return run_ngspice(tmp, log=sim["log"])
    finally:
        os.unlink(tmp)


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────
def simulate_all():
    """Run both switch-model simulations. Returns list of result dicts."""
    results = []
    for sim in SIMS:
        print(f"  Running [{sim['label']}] ...", end=" ", flush=True)
        rc   = _run_sim(sim)
        data = parse_print_table(sim["log"])
        n    = len(data) if data is not None else 0
        print(f"exit {rc},  {n} pts")
        results.append({**sim, "data": data})
    return results
