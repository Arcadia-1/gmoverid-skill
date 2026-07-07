#!/usr/bin/env python3
"""Run a Sky130A five-transistor OTA AC-gain smoke across PVT and MC."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from sky130_common import continuous_model_lib, default_jobs, find_sky130a, parse_measures, require_ngspice
from sky130_common import run_ngspice_deck, run_parallel, sample_stats, write_csv, write_json


def spice_deck(lib: Path, corner: str, seed: int | None, vbias: float) -> str:
    seed_line = f"setseed {seed}" if seed is not None else ""
    return f"""* Sky130A 5-transistor OTA smoke.
.lib "{lib}" {corner}
.options method=gear reltol=2e-3 abstol=1e-12 vntol=1e-6 chgtol=1e-15
.param vdd=1.8
.param vcm=0.9
.param vbias={vbias}

VDD vdd 0 {{vdd}}
VIP inp 0 {{vcm}} AC 0.5
VIN inn 0 {{vcm}} AC -0.5
VBIAS vb 0 {{vbias}}

* NMOS input pair.
XN1 left inp tail 0 sky130_fd_pr__nfet_01v8 l=0.5 w=8 nf=1
XN2 out  inn tail 0 sky130_fd_pr__nfet_01v8 l=0.5 w=8 nf=1

* PMOS current-mirror active load.
XP3 left left vdd vdd sky130_fd_pr__pfet_01v8 l=0.5 w=16 nf=1
XP4 out  left vdd vdd sky130_fd_pr__pfet_01v8 l=0.5 w=16 nf=1

* NMOS tail current source.
XN5 tail vb 0 0 sky130_fd_pr__nfet_01v8 l=0.5 w=16 nf=1

CL out 0 100f

.ac dec 40 1 1e9

.control
{seed_line}
run
meas ac gain10_v FIND vm(out) AT=10
meas ac gain10_db FIND vdb(out) AT=10
meas ac gain1k_v FIND vm(out) AT=1k
meas ac gain1k_db FIND vdb(out) AT=1k
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
    run_id: int | None,
    timeout: int,
    vbias: float,
) -> dict[str, Any]:
    suffix = corner if run_id is None else f"{corner}_{run_id:03d}"
    deck = spice_deck(lib, corner, None if run_id is None else 3000 + run_id, vbias)
    returncode, log, _cir, log_path = run_ngspice_deck(
        ngspice=ngspice,
        workdir=workdir,
        stem=f"ota5_{suffix}",
        deck=deck,
        timeout=timeout,
    )
    measures = parse_measures(log, {"gain10_v", "gain10_db", "gain1k_v", "gain1k_db"})
    row: dict[str, Any] = {
        "corner": corner,
        "run": "" if run_id is None else run_id,
        "status": "ok" if returncode == 0 and "gain1k_db" in measures else "fail",
        "returncode": returncode,
        "vbias": vbias,
        "log": str(log_path),
    }
    row.update(measures)
    return row


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdk-root", help="Path containing sky130A/, or direct path to sky130A/.")
    parser.add_argument("--workdir", default="/tmp/sky130-pdk-ota5-smoke")
    parser.add_argument("--mc-runs", type=int, default=20)
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--ngspice")
    parser.add_argument("--vbias", type=float, default=0.72)
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
            run_id=None if job["run_id"] is None else int(job["run_id"]),
            timeout=args.timeout,
            vbias=args.vbias,
        )

    rows = run_parallel(jobs, worker, args.jobs)

    fields = ["corner", "run", "status", "returncode", "vbias", "gain10_v", "gain10_db", "gain1k_v", "gain1k_db", "log"]
    csv_path = workdir / "ota5_results.csv"
    summary_path = workdir / "ota5_summary.json"
    write_csv(csv_path, rows, fields)

    pvt: dict[str, Any] = {}
    for row in rows:
        if row["corner"] == "mc" or row["status"] != "ok":
            continue
        pvt[row["corner"]] = {"gain1k_v": row.get("gain1k_v"), "gain1k_db": row.get("gain1k_db")}
    mc_gain_db = [float(row["gain1k_db"]) for row in rows if row["corner"] == "mc" and row["status"] == "ok"]
    summary = {
        "sky130a": str(sky130a),
        "model_lib": str(lib),
        "workdir": str(workdir),
        "csv": str(csv_path),
        "circuit": "5T OTA: NMOS input pair, PMOS mirror load, NMOS tail source",
        "vbias": args.vbias,
        "total_runs": len(rows),
        "ok_runs": sum(1 for row in rows if row["status"] == "ok"),
        "failed_runs": sum(1 for row in rows if row["status"] != "ok"),
        "pvt_gain": pvt,
        "monte_carlo_gain1k_db": sample_stats(mc_gain_db),
    }
    write_json(summary_path, summary)

    print(f"sky130A: {sky130a}")
    print(f"5T OTA AC gain smoke, vbias={args.vbias} V")
    print("corner  gain@1k(V/V)  gain@1k(dB)")
    for corner in ["tt", "ff", "ss", "fs", "sf"]:
        item = pvt.get(corner)
        if not item:
            print(f"{corner:<6} FAIL")
            continue
        print(f"{corner:<6} {item['gain1k_v']:12.4f}  {item['gain1k_db']:11.3f}")
    print(f"MC gain@1k dB: {summary['monte_carlo_gain1k_db']}")
    print(f"CSV: {csv_path}")
    print(f"Summary: {summary_path}")
    return 0 if summary["failed_runs"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
