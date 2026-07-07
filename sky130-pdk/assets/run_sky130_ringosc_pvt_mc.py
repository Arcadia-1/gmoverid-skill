#!/usr/bin/env python3
"""Run a Sky130A PVT + Monte Carlo smoke on a 3-stage ring oscillator."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from sky130_common import continuous_model_lib, default_jobs, find_sky130a, parse_measures, require_ngspice
from sky130_common import run_ngspice_deck, run_parallel, sample_stats, write_csv, write_json


def spice_deck(lib: Path, corner: str, tran_stop: str, seed: int | None) -> str:
    seed_line = f"setseed {seed}" if seed is not None else ""
    return f"""* Sky130A continuous-model 3-stage ring oscillator smoke.
.lib "{lib}" {corner}
.options method=gear reltol=2e-3 abstol=1e-12 vntol=1e-6 chgtol=1e-15
.save v(n1) v(n2) v(n3)
.param vdd=1.8

VDD vdd 0 {{vdd}}

.subckt inv in out vdd vss
XP out in vdd vdd sky130_fd_pr__pfet_01v8 l=0.15 w=1.26 nf=1
XN out in vss vss sky130_fd_pr__nfet_01v8 l=0.15 w=0.42 nf=1
.ends inv

XINV0 n3 n1 vdd 0 inv
XINV1 n1 n2 vdd 0 inv
XINV2 n2 n3 vdd 0 inv

C1 n1 0 2f
C2 n2 0 2f
C3 n3 0 2f

.ic v(n1)=0 v(n2)=1.8 v(n3)=0.6
.tran 2p {tran_stop} 0 4p uic
.meas tran t5 WHEN v(n1)=0.9 RISE=5
.meas tran t12 WHEN v(n1)=0.9 RISE=12
.meas tran period PARAM='(t12-t5)/7'
.meas tran freq_hz PARAM='1/period'

.control
{seed_line}
run
quit
.endc
.end
"""


def run_one(
    *,
    ngspice: str,
    lib: Path,
    workdir: Path,
    corner: str,
    tran_stop: str,
    run_id: int | None,
    timeout: int,
) -> dict[str, Any]:
    suffix = corner if run_id is None else f"{corner}_{run_id:03d}"
    deck = spice_deck(lib, corner, tran_stop, None if run_id is None else 1000 + run_id)
    returncode, log, _cir, log_path = run_ngspice_deck(
        ngspice=ngspice,
        workdir=workdir,
        stem=f"ringosc_{suffix}",
        deck=deck,
        timeout=timeout,
    )
    measures = parse_measures(log, {"t5", "t12", "period", "freq_hz"})
    row: dict[str, Any] = {
        "corner": corner,
        "run": "" if run_id is None else run_id,
        "status": "ok" if returncode == 0 and "freq_hz" in measures else "fail",
        "returncode": returncode,
        "log": str(log_path),
    }
    row.update(measures)
    if "period" in measures:
        row["period_ps"] = measures["period"] * 1e12
    if "freq_hz" in measures:
        row["freq_ghz"] = measures["freq_hz"] / 1e9
    return row


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdk-root", help="Path containing sky130A/, or direct path to sky130A/.")
    parser.add_argument("--workdir", default="/tmp/sky130-pdk-ringosc-smoke")
    parser.add_argument("--mc-runs", type=int, default=20)
    parser.add_argument("--tran-stop", default="6n")
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--ngspice")
    parser.add_argument("--jobs", type=int, default=default_jobs(), help="Maximum parallel ngspice jobs.")
    args = parser.parse_args()

    sky130a = find_sky130a(args.pdk_root)
    lib = continuous_model_lib(sky130a)
    ngspice = require_ngspice(args.ngspice)
    workdir = Path(args.workdir)

    jobs: list[dict[str, int | str | None]] = [{"corner": corner, "run_id": None} for corner in ["tt", "ff", "ss", "fs", "sf"]]
    jobs.extend({"corner": "mc", "run_id": idx} for idx in range(args.mc_runs))

    def worker(job: dict[str, int | str | None]) -> dict[str, Any]:
        return run_one(
            ngspice=ngspice,
            lib=lib,
            workdir=workdir,
            corner=str(job["corner"]),
            tran_stop=args.tran_stop,
            run_id=None if job["run_id"] is None else int(job["run_id"]),
            timeout=args.timeout,
        )

    rows = run_parallel(jobs, worker, args.jobs)

    fields = ["corner", "run", "status", "returncode", "period_ps", "freq_hz", "freq_ghz", "log"]
    csv_path = workdir / "ringosc_results.csv"
    summary_path = workdir / "ringosc_summary.json"
    write_csv(csv_path, rows, fields)

    pvt = {
        row["corner"]: {"period_ps": row.get("period_ps"), "freq_ghz": row.get("freq_ghz")}
        for row in rows
        if row["corner"] != "mc" and row["status"] == "ok"
    }
    mc_freqs = [float(row["freq_ghz"]) for row in rows if row["corner"] == "mc" and row["status"] == "ok"]
    summary = {
        "sky130a": str(sky130a),
        "model_lib": str(lib),
        "workdir": str(workdir),
        "csv": str(csv_path),
        "total_runs": len(rows),
        "ok_runs": sum(1 for row in rows if row["status"] == "ok"),
        "failed_runs": sum(1 for row in rows if row["status"] != "ok"),
        "pvt": pvt,
        "monte_carlo_freq_ghz": sample_stats(mc_freqs),
    }
    write_json(summary_path, summary)

    print(f"sky130A: {sky130a}")
    print("corner  period_ps  freq_ghz")
    for corner in ["tt", "ff", "ss", "fs", "sf"]:
        item = pvt.get(corner)
        if item:
            print(f"{corner:<6} {item['period_ps']:9.3f}  {item['freq_ghz']:8.3f}")
        else:
            print(f"{corner:<6} FAIL")
    print(f"MC freq GHz: {summary['monte_carlo_freq_ghz']}")
    print(f"CSV: {csv_path}")
    print(f"Summary: {summary_path}")
    return 0 if summary["failed_runs"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
