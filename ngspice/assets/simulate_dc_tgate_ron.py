#!/usr/bin/env python3
"""
simulate_dc_tgate_ron.py
========================
Simulation engine for transmission gate Ron vs pass voltage.

Measures Ron of a complementary NMOS+PMOS transmission gate across
three technology nodes: 180nm, 45nm HP, and 22nm HP.

Method: apply 10 mV across the tgate, measure current, Ron = 10mV / I.

Public API
----------
simulate_all() -> list of result dicts
    Each dict: {label, color, vpass, ron, vdd, node}
"""

import tempfile
import os
import numpy as np

from ngspice_common import (
    LOG_DIR, MODEL_DIR, render_template, run_ngspice, parse_print_table, spath,
)

# ─────────────────────────────────────────────────────────────────────────────
# Perturbation voltage for Ron measurement
# ─────────────────────────────────────────────────────────────────────────────
DELTA_V = 0.01  # 10 mV

# ─────────────────────────────────────────────────────────────────────────────
# Technology node configurations (W/L = 100 for all)
# ─────────────────────────────────────────────────────────────────────────────
WL_RATIO = 100

NODES = [
    {
        "label":      "180nm  (VDD=1.8V)",
        "node":       "180nm",
        "model_file": "ptm180.lib",
        "nmos_model": "NMOS",
        "pmos_model": "PMOS",
        "L_um":       0.18,
        "vdd":        1.8,
        "color":      "royalblue",
        "log":        LOG_DIR / "dc_tgate_180nm.log",
    },
    {
        "label":      "45nm HP  (VDD=1.0V)",
        "node":       "45nm HP",
        "model_file": "ptm45hp.lib",
        "nmos_model": "nmos",
        "pmos_model": "pmos",
        "L_um":       0.045,
        "vdd":        1.0,
        "color":      "darkorange",
        "log":        LOG_DIR / "dc_tgate_45nm.log",
    },
    {
        "label":      "22nm HP  (VDD=0.8V)",
        "node":       "22nm HP",
        "model_file": "ptm22hp.lib",
        "nmos_model": "nmos",
        "pmos_model": "pmos",
        "L_um":       0.022,
        "vdd":        0.8,
        "color":      "seagreen",
        "log":        LOG_DIR / "dc_tgate_22nm.log",
    },
]


def _run_node(cfg):
    """Run DC sweep for one technology node."""
    W_um = WL_RATIO * cfg["L_um"]
    vdd = cfg["vdd"]

    text = render_template(
        "dc_tgate_ron.cir.tmpl",
        label=cfg["label"],
        model_path=spath(MODEL_DIR / cfg["model_file"]),
        nmos_model=cfg["nmos_model"],
        pmos_model=cfg["pmos_model"],
        W=W_um, L=cfg["L_um"],
        WL_ratio=WL_RATIO,
        vdd=vdd,
        vpass_start=0.0,
        vpass_stop=vdd,
        vpass_step=vdd / 200,
    )
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".cir", delete=False, encoding="utf-8"
    ) as f:
        f.write(text)
        tmp = f.name
    try:
        return run_ngspice(tmp, log=cfg["log"])
    finally:
        os.unlink(tmp)


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────
def simulate_all():
    """Run tgate Ron simulations for all technology nodes."""
    results = []
    for cfg in NODES:
        W_um = WL_RATIO * cfg["L_um"]
        print(f"\n  [{cfg['label']}]  W = {W_um:.2f} um,  L = {cfg['L_um']} um,  "
              f"W/L = {WL_RATIO}")
        print(f"    Running ...", end=" ", flush=True)

        rc = _run_node(cfg)
        data = parse_print_table(cfg["log"])
        n = len(data) if data is not None else 0
        print(f"exit {rc},  {n} pts")

        if data is not None and data.shape[1] >= 2:
            vpass = data[:, 0]
            i_delta = np.abs(data[:, 1])
            # Ron = Delta_V / I (avoid div by zero)
            ron = np.where(i_delta > 1e-15, DELTA_V / i_delta, np.nan)

            # Print min Ron
            valid = ~np.isnan(ron)
            if np.any(valid):
                min_ron = np.nanmin(ron)
                print(f"    Min Ron = {min_ron:.1f} ohm")
        else:
            vpass, ron = None, None

        results.append({
            **cfg,
            "vpass": vpass,
            "ron":   ron,
            "W_um":  W_um,
        })
    return results
