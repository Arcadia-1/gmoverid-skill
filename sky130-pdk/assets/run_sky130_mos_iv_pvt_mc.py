#!/usr/bin/env python3
"""Run Sky130A NMOS Id-Vgs smoke across PVT process corners and MC."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from sky130_common import continuous_model_lib, default_jobs, find_sky130a, parse_measures, require_ngspice
from sky130_common import run_ngspice_deck, run_parallel, sample_stats, write_csv, write_json


MEASURE_POINTS = {
    "id_vgs06": 0.6,
    "id_vgs09": 0.9,
    "id_vgs12": 1.2,
    "id_vgs15": 1.5,
}


def spice_deck(lib: Path, corner: str, seed: int | None, vds: float) -> str:
    seed_line = f"setseed {seed}" if seed is not None else ""
    measures = "\n".join(f".meas dc {name} FIND i(VDS) AT={vgs}" for name, vgs in MEASURE_POINTS.items())
    return f"""* Sky130A NMOS Id-Vgs process/MC smoke.
.lib "{lib}" {corner}
.options reltol=1e-4 abstol=1e-12 vntol=1e-6
.param vdsval={vds}

VDS d 0 {{vdsval}}
VGS g 0 0
XN1 d g 0 0 sky130_fd_pr__nfet_01v8 l=0.15 w=1.0 nf=1

.dc VGS 0 1.8 0.01
{measures}

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
    run_id: int | None,
    timeout: int,
    vds: float,
) -> dict[str, Any]:
    suffix = corner if run_id is None else f"{corner}_{run_id:03d}"
    deck = spice_deck(lib, corner, None if run_id is None else 2000 + run_id, vds)
    returncode, log, _cir, log_path = run_ngspice_deck(
        ngspice=ngspice,
        workdir=workdir,
        stem=f"mos_iv_{suffix}",
        deck=deck,
        timeout=timeout,
    )
    measures = parse_measures(log, set(MEASURE_POINTS))
    row: dict[str, Any] = {
        "corner": corner,
        "run": "" if run_id is None else run_id,
        "status": "ok" if returncode == 0 and len(measures) == len(MEASURE_POINTS) else "fail",
        "returncode": returncode,
        "vds": vds,
        "log": str(log_path),
    }
    for name in MEASURE_POINTS:
        if name in measures:
            # Current through VDS is negative for drain current in this orientation.
            row[f"{name}_a"] = abs(measures[name])
            row[f"{name}_ua"] = abs(measures[name]) * 1e6
    return row


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdk-root", help="Path containing sky130A/, or direct path to sky130A/.")
    parser.add_argument("--workdir", default="/tmp/sky130-pdk-mos-iv-smoke")
    parser.add_argument("--mc-runs", type=int, default=20)
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--ngspice")
    parser.add_argument("--vds", type=float, default=0.9)
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
            vds=args.vds,
        )

    rows = run_parallel(jobs, worker, args.jobs)

    fields = ["corner", "run", "status", "returncode", "vds"]
    for name in MEASURE_POINTS:
        fields.extend([f"{name}_a", f"{name}_ua"])
    fields.append("log")
    csv_path = workdir / "mos_iv_results.csv"
    summary_path = workdir / "mos_iv_summary.json"
    write_csv(csv_path, rows, fields)

    pvt: dict[str, Any] = {}
    for row in rows:
        if row["corner"] == "mc" or row["status"] != "ok":
            continue
        pvt[row["corner"]] = {f"{name}_ua": row.get(f"{name}_ua") for name in MEASURE_POINTS}
    mc_id_vgs09 = [float(row["id_vgs09_ua"]) for row in rows if row["corner"] == "mc" and row["status"] == "ok"]
    summary = {
        "sky130a": str(sky130a),
        "model_lib": str(lib),
        "workdir": str(workdir),
        "csv": str(csv_path),
        "vds": args.vds,
        "device": "sky130_fd_pr__nfet_01v8 l=0.15 w=1.0 nf=1",
        "total_runs": len(rows),
        "ok_runs": sum(1 for row in rows if row["status"] == "ok"),
        "failed_runs": sum(1 for row in rows if row["status"] != "ok"),
        "pvt_id_ua": pvt,
        "monte_carlo_id_vgs09_ua": sample_stats(mc_id_vgs09),
    }
    write_json(summary_path, summary)

    print(f"sky130A: {sky130a}")
    print(f"NMOS Id-Vgs at VDS={args.vds} V, W=1.0um, L=0.15um")
    print("corner  Id@0.6V(uA)  Id@0.9V(uA)  Id@1.2V(uA)  Id@1.5V(uA)")
    for corner in ["tt", "ff", "ss", "fs", "sf"]:
        item = pvt.get(corner)
        if not item:
            print(f"{corner:<6} FAIL")
            continue
        print(
            f"{corner:<6} {item['id_vgs06_ua']:12.4f}  {item['id_vgs09_ua']:12.4f}  "
            f"{item['id_vgs12_ua']:12.4f}  {item['id_vgs15_ua']:12.4f}"
        )
    print(f"MC Id@VGS=0.9V uA: {summary['monte_carlo_id_vgs09_ua']}")
    print(f"CSV: {csv_path}")
    print(f"Summary: {summary_path}")
    return 0 if summary["failed_runs"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
