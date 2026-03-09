#!/usr/bin/env python3
"""
simulate_rc_filter.py
=====================
Simulation engine for the RC low-pass filter AC + noise study.

Two RC configurations: R=1kΩ/C=1pF  (fc≈159 MHz) and R=10kΩ/C=1pF (fc≈15.9 MHz).

AC netlists are generated from netlist/ac_rc_filter.cir.tmpl.
Noise netlists are generated from netlist/noise_rc_filter.cir.tmpl.

Public API
----------
simulate_all() -> list of result dicts
    Each dict contains parsed ac_data and noise_data arrays plus config info.
"""

import tempfile
import os
import numpy as np

from ngspice_common import (
    LOG_DIR, render_template, run_ngspice, parse_print_table, parse_wrdata, spath,
)

FREQ_START = "1Meg"
FREQ_STOP  = "10G"

# ─────────────────────────────────────────────────────────────────────────────
# Simulation configurations
# ─────────────────────────────────────────────────────────────────────────────
CONFIGS = [
    {
        "label":       "R=1kΩ,  C=1pF",
        "R": 1e3,  "C": 1e-12,
        "R_spice": "1k", "C_spice": "1p",
        "ac_log":      LOG_DIR / "rc_ac_1k.log",
        "noise_data":  LOG_DIR / "rc_noise_1k.txt",
        "noise_log":   LOG_DIR / "rc_noise_1k.log",
        "color_ac":    "royalblue",
        "color_noise": "seagreen",
    },
    {
        "label":       "R=10kΩ, C=1pF",
        "R": 1e4,  "C": 1e-12,
        "R_spice": "10k", "C_spice": "1p",
        "ac_log":      LOG_DIR / "rc_ac_10k.log",
        "noise_data":  LOG_DIR / "rc_noise_10k.txt",
        "noise_log":   LOG_DIR / "rc_noise_10k.log",
        "color_ac":    "darkorange",
        "color_noise": "crimson",
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# AC simulation (template → temp file → ngspice)
# ─────────────────────────────────────────────────────────────────────────────
def _run_ac(cfg, fc):
    text = render_template(
        "ac_rc_filter.cir.tmpl",
        label   = cfg["label"],
        R       = cfg["R_spice"],
        C       = cfg["C_spice"],
        fc_mhz  = f"{fc/1e6:.2f}",
        fstart  = FREQ_START,
        fstop   = FREQ_STOP,
    )
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".cir", delete=False, encoding="utf-8"
    ) as f:
        f.write(text)
        tmp = f.name
    try:
        return run_ngspice(tmp, log=cfg["ac_log"])
    finally:
        os.unlink(tmp)


# ─────────────────────────────────────────────────────────────────────────────
# Noise simulation (template → temp file → ngspice)
# ─────────────────────────────────────────────────────────────────────────────
def _run_noise(cfg):
    text = render_template(
        "noise_rc_filter.cir.tmpl",
        label  = cfg["label"],
        R      = cfg["R_spice"],
        C      = cfg["C_spice"],
        fstart = FREQ_START,
        fstop  = FREQ_STOP,
        wrdata = spath(cfg["noise_data"]),
    )
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".cir", delete=False, encoding="utf-8"
    ) as f:
        f.write(text)
        tmp = f.name
    try:
        return run_ngspice(tmp, log=cfg["noise_log"])
    finally:
        os.unlink(tmp)


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────
def simulate_all():
    """Run AC and noise simulations for all RC configurations."""
    results = []
    for cfg in CONFIGS:
        fc = 1 / (2 * np.pi * cfg["R"] * cfg["C"])
        print(f"\n  [{cfg['label']}]  fc = {fc/1e6:.2f} MHz")

        print("    AC  ...", end=" ", flush=True)
        rc = _run_ac(cfg, fc)
        raw = parse_print_table(cfg["ac_log"])
        # ngspice AC output: [freq, real, imag] → compute magnitude
        if raw is not None and raw.shape[1] >= 3:
            mag = np.sqrt(raw[:, 1]**2 + raw[:, 2]**2)
            ac_data = np.column_stack([raw[:, 0], mag])
        else:
            ac_data = raw
        print(f"exit {rc},  {len(ac_data) if ac_data is not None else 0} pts")

        print("    Noise ...", end=" ", flush=True)
        rc = _run_noise(cfg)
        noise_data = (parse_wrdata(cfg["noise_data"])
                      if cfg["noise_data"].exists() else None)
        print(f"exit {rc},  {len(noise_data) if noise_data is not None else 0} pts")

        results.append({**cfg, "fc": fc, "ac_data": ac_data, "noise_data": noise_data})
    return results
