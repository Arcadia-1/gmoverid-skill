#!/usr/bin/env python3
"""
run_all.py
==========
Run all 9 ngspice simulation examples sequentially.

Usage:  python run_all.py

Examples
--------
#  Type   Description                              Output
1  Tran   RC charging voltage & current            plots/tran_rc_charging.png
2  DC     NMOS Id-Vds family curves                plots/nmos_dc_iv.png
3  AC     RC low-pass filter frequency response    plots/rc_ac_bw.png
4  Noise  RC filter output noise spectrum (#3)     plots/rc_ac_bw.png
5  Tran   Sample-and-hold switch comparison        plots/sample_hold_compare.png
6  Tran   kT/C noise time-domain statistics        plots/tran_ktc_noise_hist.png
7  DC     NMOS current mirror output characteristic plots/dc_current_mirror.png
8  AC     Common-source amplifier Bode plot        plots/ac_cs_amp_bode.png
9  DC     Transmission gate Ron vs pass voltage    plots/dc_tgate_ron.png

On Windows, set PYTHONUTF8=1 to avoid encoding errors.
"""

import subprocess
import sys
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent

EXAMPLES = [
    "run_tran_rc_charging.py",       # 1  Tran  RC charging
    "run_dc_nmos_iv.py",             # 2  DC    NMOS I-V curves
    "run_ac_rc_filter.py",           # 3+4 AC/Noise  RC filter
    "run_tran_sample_hold.py",       # 5  Tran  Sample & hold
    "run_tran_ktc_noise.py",         # 6  Tran  kT/C noise
    "run_dc_current_mirror.py",      # 7  DC    Current mirror
    "run_ac_cs_amp.py",              # 8  AC    CS amplifier
    "run_dc_tgate_ron.py",           # 9  DC    Tgate Ron
]


def main():
    print("=" * 60)
    print("  ngspice Simulation Examples — Run All")
    print("=" * 60)

    passed, failed = [], []
    t0 = time.time()

    for script in EXAMPLES:
        print(f"\n{'─' * 60}")
        print(f"  Running: {script}")
        print(f"{'─' * 60}")
        ret = subprocess.run(
            [sys.executable, str(SCRIPT_DIR / script)],
            cwd=str(SCRIPT_DIR),
        )
        if ret.returncode == 0:
            passed.append(script)
        else:
            print(f"  FAILED (exit code {ret.returncode})")
            failed.append(script)

    elapsed = time.time() - t0
    print(f"\n{'=' * 60}")
    print(f"  Summary:  {len(passed)} passed,  {len(failed)} failed")
    print(f"  Total time: {elapsed:.1f} s")
    if failed:
        print(f"  Failed: {', '.join(failed)}")
    print(f"{'=' * 60}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
