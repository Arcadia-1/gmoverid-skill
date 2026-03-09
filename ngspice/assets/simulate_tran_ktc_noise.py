#!/usr/bin/env python3
"""
simulate_tran_ktc_noise.py
==========================
Simulation engine for kT/C noise time-domain statistical measurement.

Models the thermal noise of a switch Ron using a trnoise voltage source
in series with a noiseless resistor, charging a sampling capacitor.
After settling, v(out) fluctuates around Vdc with std = sqrt(kT/C).

Public API
----------
simulate_all() -> list of result dicts
    Each dict: {label, C_val, C_si, sigma_theory, samples (1-D array), time, vout}
"""

import tempfile
import os
import time
from concurrent.futures import ThreadPoolExecutor
import numpy as np

from ngspice_common import (
    LOG_DIR, render_template, run_ngspice, parse_wrdata, spath,
)

# ─────────────────────────────────────────────────────────────────────────────
# Physical constants and circuit parameters
# ─────────────────────────────────────────────────────────────────────────────
K_B   = 1.38064852e-23   # Boltzmann constant [J/K]
T     = 300.0            # Temperature [K]
VDC   = 0.9              # DC input voltage [V]

# kT/C is independent of R, so we choose R per cap to target a uniform tau.
# This keeps the number of internal ngspice steps identical for every config.
TAU_TARGET = 50e-12      # Target RC time constant [s] (50 ps)

# Sampling parameters
N_SAMPLES  = 10000        # Number of samples to extract
SAMPLE_DT  = 0.1e-9       # Fixed sample interval [s] (0.1 ns)

# ─────────────────────────────────────────────────────────────────────────────
# Capacitor configurations
# ─────────────────────────────────────────────────────────────────────────────
CONFIGS = [
    {
        "label":  "C = 10 fF",
        "C_val":  "10f",
        "C_si":   10e-15,
        "color":  "forestgreen",
        "log":    LOG_DIR / "tran_ktc_10f.log",
        "wrdata": LOG_DIR / "tran_ktc_10f.txt",
    },
    {
        "label":  "C = 1 pF",
        "C_val":  "1p",
        "C_si":   1e-12,
        "color":  "royalblue",
        "log":    LOG_DIR / "tran_ktc_1p.log",
        "wrdata": LOG_DIR / "tran_ktc_1p.txt",
    },
    {
        "label":  "C = 100 pF",
        "C_val":  "100p",
        "C_si":   100e-12,
        "color":  "darkorange",
        "log":    LOG_DIR / "tran_ktc_100p.log",
        "wrdata": LOG_DIR / "tran_ktc_100p.txt",
    },
]


def _sim_params(C_si):
    """Compute simulation timing parameters for a given capacitance.

    R is chosen so that tau = TAU_TARGET for every config.  Since kT/C is
    independent of R, this does not affect the noise result — it only
    equalises the internal step count across configs.
    """
    R = TAU_TARGET / C_si                    # R chosen to hit target tau
    tau = TAU_TARGET
    nt_dt = tau / 10.0                       # noise update interval (5 ps)
    nt_rms = np.sqrt(2 * K_B * T * R / nt_dt)
    settle_time = max(50 * tau, 10e-9)       # skip initial transient (min 10 ns)
    tstep = SAMPLE_DT                        # output resolution = sample interval
    tstop = settle_time + N_SAMPLES * SAMPLE_DT + SAMPLE_DT
    return R, tau, nt_dt, nt_rms, settle_time, tstep, tstop


def _run_sim(cfg):
    """Render template and run ngspice for one capacitor value."""
    C_si = cfg["C_si"]
    R, tau, nt_dt, nt_rms, settle_time, tstep, tstop = _sim_params(C_si)
    sigma_theory = np.sqrt(K_B * T / C_si)

    text = render_template(
        "tran_ktc_noise.cir.tmpl",
        Vdc=VDC,
        R_val=R,
        C_val=cfg["C_val"],
        nt=f"{nt_rms:.6e}",
        nt_dt=f"{nt_dt:.4e}",
        tstep=f"{tstep:.4e}",
        tstop=f"{tstop:.4e}",
        sigma_uv=f"{sigma_theory*1e6:.1f}",
        wrdata_path=spath(cfg["wrdata"]),
    )
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".cir", delete=False, encoding="utf-8"
    ) as f:
        f.write(text)
        tmp = f.name
    try:
        return run_ngspice(tmp, log=cfg["log"], timeout=300)
    finally:
        os.unlink(tmp)


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────
def _run_one(cfg):
    """Run simulation + post-processing for one config. Returns result dict."""
    C_si = cfg["C_si"]
    R, tau, nt_dt, nt_rms, settle_time, tstep, tstop = _sim_params(C_si)
    sigma_theory = np.sqrt(K_B * T / C_si)

    print(f"\n  [{cfg['label']}]  R = {R:.1f} ohm,  tau = {tau*1e12:.0f} ps,  "
          f"theory sigma = {sigma_theory*1e6:.1f} uVrms")
    print(f"    nt_dt = {nt_dt*1e12:.1f} ps,  tstop = {tstop*1e6:.1f} us,  "
          f"sample dt = {SAMPLE_DT*1e9:.1f} ns")
    print(f"    Running ...", flush=True)

    t0 = time.perf_counter()
    rc = _run_sim(cfg)
    elapsed = time.perf_counter() - t0

    # Parse wrdata output: [time, v(out)]
    raw = parse_wrdata(cfg["wrdata"]) if cfg["wrdata"].exists() else None
    n_pts = len(raw) if raw is not None else 0
    print(f"    [{cfg['label']}] exit {rc},  {n_pts} pts,  {elapsed:.1f} s")

    if raw is None or n_pts < 100:
        print(f"    WARNING: insufficient data for {cfg['label']}")
        return {**cfg, "sigma_theory": sigma_theory,
                "samples": None, "time": None, "vout": None,
                "sim_time": elapsed}

    time_arr = raw[:, 0]
    vout_arr = raw[:, 1]

    # Extract samples at fixed 0.1 ns intervals, after settling
    sample_times = settle_time + np.arange(N_SAMPLES) * SAMPLE_DT
    samples = np.interp(sample_times, time_arr, vout_arr)

    measured_std = np.std(samples)
    measured_mean = np.mean(samples)

    if measured_std < sigma_theory * 0.01:
        print(f"    WARNING: measured noise ({measured_std*1e6:.2f} uV) is "
              f"near zero — trnoise may not be active in your ngspice version")

    print(f"    Measured: mean = {measured_mean:.6f} V,  "
          f"std = {measured_std*1e6:.1f} uVrms")
    print(f"    Theory:   sigma = {sigma_theory*1e6:.1f} uVrms  "
          f"(ratio = {measured_std/sigma_theory:.2f})")

    return {
        **cfg,
        "sigma_theory": sigma_theory,
        "samples":      samples,
        "time":         time_arr,
        "vout":         vout_arr,
        "sim_time":     elapsed,
    }


def simulate_all():
    """Run kT/C noise simulations for all capacitor configs in parallel."""
    t_total = time.perf_counter()

    with ThreadPoolExecutor(max_workers=len(CONFIGS)) as pool:
        results = list(pool.map(_run_one, CONFIGS))

    wall_time = time.perf_counter() - t_total
    print(f"\n  Total wall time: {wall_time:.1f} s "
          f"({len(CONFIGS)} sims in parallel)")

    # Attach total wall time so the plot can display it
    for r in results:
        r["total_wall_time"] = wall_time
    return results
