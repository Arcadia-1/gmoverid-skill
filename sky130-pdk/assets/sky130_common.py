#!/usr/bin/env python3
"""Shared helpers for Sky130A ngspice smoke examples."""

from __future__ import annotations

import csv
import json
import os
import re
import shutil
import statistics
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Callable


VERIFIED_SKY130_COMMIT = "c6d73a35f524070e85faff4a6a9eef49553ebc2b"
VALUE_RE = re.compile(
    r"^\s*([a-zA-Z0-9_]+)\s*=\s*([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)"
)


def run_text(cmd: list[str], timeout: int = 15) -> str | None:
    try:
        proc = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
    except Exception:
        return None
    if proc.returncode != 0:
        return None
    return proc.stdout.strip()


def candidate_sky130a_paths(explicit: str | None) -> list[Path]:
    candidates: list[Path] = []

    def add(path: str | Path | None) -> None:
        if not path:
            return
        p = Path(path).expanduser()
        candidates.append(p / "sky130A")
        candidates.append(p)

    add(explicit)
    add(os.environ.get("PDK_ROOT"))

    volare = shutil.which("volare")
    if volare:
        root = run_text([volare, "path"])
        version = run_text([volare, "output", "--pdk", "sky130"])
        if root and version:
            candidates.append(Path(root) / "volare" / "sky130" / "versions" / version / "sky130A")

    unique: list[Path] = []
    seen: set[str] = set()
    for path in candidates:
        key = str(path)
        if key not in seen:
            seen.add(key)
            unique.append(path)
    return unique


def find_sky130a(explicit: str | None = None) -> Path:
    for path in candidate_sky130a_paths(explicit):
        lib = path / "libs.tech" / "combined" / "continuous" / "sky130.lib.spice"
        if lib.is_file():
            return path
    tried = "\n".join(f"  - {p}" for p in candidate_sky130a_paths(explicit))
    raise SystemExit(
        "Could not find sky130A continuous ngspice model.\n"
        "Install/enable Sky130 with Volare or pass --pdk-root.\n"
        f"Tried:\n{tried}"
    )


def continuous_model_lib(sky130a: Path) -> Path:
    return sky130a / "libs.tech" / "combined" / "continuous" / "sky130.lib.spice"


def require_ngspice(path: str | None = None) -> str:
    ngspice = path or shutil.which("ngspice")
    if not ngspice:
        raise SystemExit("ngspice was not found in PATH. Install ngspice first.")
    return ngspice


def parse_measures(log: str, names: set[str]) -> dict[str, float]:
    values: dict[str, float] = {}
    for line in log.splitlines():
        match = VALUE_RE.match(line)
        if not match:
            continue
        key, value = match.groups()
        if key in names:
            values[key] = float(value)
    return values


def run_ngspice_deck(
    *,
    ngspice: str,
    workdir: Path,
    stem: str,
    deck: str,
    timeout: int,
) -> tuple[int, str, Path, Path]:
    workdir.mkdir(parents=True, exist_ok=True)
    cir_path = workdir / f"{stem}.spice"
    log_path = workdir / f"{stem}.log"
    cir_path.write_text(deck, encoding="utf-8")
    try:
        proc = subprocess.run(
            [ngspice, "-b", str(cir_path)],
            cwd=workdir,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout,
        )
        returncode = proc.returncode
        log = proc.stdout
    except subprocess.TimeoutExpired as exc:
        returncode = 124
        log = exc.stdout if isinstance(exc.stdout, str) else ""
        log += f"\nTIMEOUT after {timeout}s\n"
    log_path.write_text(log, encoding="utf-8")
    return returncode, log, cir_path, log_path


def default_jobs(max_jobs: int = 1) -> int:
    return max(1, min(max_jobs, os.cpu_count() or 1))


def run_parallel(items: list[Any], worker: Callable[[Any], dict[str, Any]], jobs: int) -> list[dict[str, Any]]:
    if jobs <= 1 or len(items) <= 1:
        return [worker(item) for item in items]
    results: list[dict[str, Any] | None] = [None] * len(items)
    with ThreadPoolExecutor(max_workers=jobs) as pool:
        futures = {pool.submit(worker, item): idx for idx, item in enumerate(items)}
        for future in as_completed(futures):
            results[futures[future]] = future.result()
    return [row for row in results if row is not None]


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")


def sample_stats(values: list[float]) -> dict[str, float | int]:
    if not values:
        return {"runs": 0}
    out: dict[str, float | int] = {
        "runs": len(values),
        "mean": statistics.mean(values),
        "min": min(values),
        "max": max(values),
    }
    out["stdev"] = statistics.stdev(values) if len(values) > 1 else 0.0
    return out
