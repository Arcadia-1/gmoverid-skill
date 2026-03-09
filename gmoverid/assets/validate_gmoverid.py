#!/usr/bin/env python3
"""
validate_gmoverid.py
====================
Five-point physical sanity check for a gm/ID characterization table.

For the theoretical basis of each test see references/validation.md.

Usage
-----
    python validate_gmoverid.py [model] [L_um]
    python validate_gmoverid.py                    # nmos180 @ 180 nm (default)
    python validate_gmoverid.py nmos45hp 0.045
    python validate_gmoverid.py pmos180  0.36

Exit code: 0 = all pass, 1 = one or more failures.
"""

import re
import sys
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from design_gmoverid import GmIdTable
from simulate_gmoverid import MODEL_INFO, VDD

# ── ANSI colour (degrades gracefully on terminals without colour support) ─────
_G = '\033[32m'   # green
_R = '\033[31m'   # red
_B = '\033[1m'    # bold
_E = '\033[0m'    # reset


def _tag(ok):
    return f'{_G}PASS{_E}' if ok else f'{_R}FAIL{_E}'


def _report(ok, text):
    print(f'  [{_tag(ok)}]  {text}')
    return ok


# ─────────────────────────────────────────────────────────────────────────────
# Test 1 — Weak-inversion limit (1/Ut test)
# ─────────────────────────────────────────────────────────────────────────────
def test1_weak_inversion(tbl):
    """
    Peak gm/ID must lie in [25, 32] V^-1 at room temperature.

    Physics: gm/ID_max = 1/(n·Ut), n in [1.2, 1.5], Ut = 25.85 mV at 300 K.
    """
    gmid_max = tbl.operating_range()['gmid_max']
    ok = 25.0 <= gmid_max <= 32.0
    return _report(ok,
        f'Test 1  Weak-inversion limit  :  '
        f'peak gm/ID = {gmid_max:.2f} V^-1  '
        f'(expected 25–32)')


# ─────────────────────────────────────────────────────────────────────────────
# Test 2 — ID/W monotonicity
# ─────────────────────────────────────────────────────────────────────────────
def test2_idw_monotonicity(tbl):
    """
    Id/W must decrease strictly as gm/ID increases (strong → weak inversion).

    Internally _idw_arr is aligned to the descending _gmid_arr, so _idw_arr
    itself must be monotonically increasing (no negative diffs).
    Any negative step is a numerical artefact (interpolation / extraction noise).
    """
    diffs      = np.diff(tbl._idw_arr)
    violations = int(np.sum(diffs < 0))
    ok = violations == 0
    return _report(ok,
        f'Test 2  ID/W monotonicity     :  '
        f'{violations} non-monotone step(s)  '
        f'(expected 0)')


# ─────────────────────────────────────────────────────────────────────────────
# Test 3 — Channel-length doubling scaling
# ─────────────────────────────────────────────────────────────────────────────
def test3_length_scaling(model, L_um, vds):
    """
    At gm/ID = 15 V^-1, doubling L must produce:
      gmro(2L) / gmro(L)  in [1.5, 5.0]   — ro scales with L via CLM
      fT(2L)   / fT(L)    in [0.15, 0.70]  — Cgg grows with L
    """
    GMID_REF = 15.0
    L2 = round(L_um * 2.0, 6)

    tbl1 = GmIdTable(model, W=10.0, L=L_um, vds=vds)
    tbl2 = GmIdTable(model, W=10.0, L=L2,   vds=vds)

    gmro1 = tbl1.lookup('gmro', GMID_REF)
    gmro2 = tbl2.lookup('gmro', GMID_REF)
    ft1   = tbl1.lookup('ft',   GMID_REF)
    ft2   = tbl2.lookup('ft',   GMID_REF)

    r_gain = gmro2 / gmro1 if gmro1 > 0 else 0.0
    r_ft   = ft2   / ft1   if ft1   > 0 else 0.0

    ok_gain = 1.5 <= r_gain <= 5.0
    ok_ft   = 0.15 <= r_ft  <= 0.70

    _report(ok_gain,
        f'Test 3a L-doubling gain       :  '
        f'gmro {gmro1:.1f} → {gmro2:.1f},  ratio = {r_gain:.2f}  '
        f'(expected 1.5–5.0)')
    _report(ok_ft,
        f'Test 3b L-doubling fT         :  '
        f'fT {ft1/1e9:.2f} → {ft2/1e9:.2f} GHz,  ratio = {r_ft:.2f}  '
        f'(expected 0.15–0.70)')
    return ok_gain and ok_ft


# ─────────────────────────────────────────────────────────────────────────────
# Test 4 — fT × gm/ID peak in mid-inversion
# ─────────────────────────────────────────────────────────────────────────────
def test4_ft_gmid_peak(tbl):
    """
    The product fT × (gm/ID) must peak in the mid-inversion region,
    gm/ID in [8, 18] V^-1.

    Physics: strong inversion → fT high, gm/ID low; weak inversion →
    gm/ID high, fT collapses.  The product peaks where the two trade-offs
    cross, which is mid-inversion for bulk CMOS at room temperature.
    """
    product   = tbl._ft_arr * tbl._gmid_arr
    peak_idx  = int(np.nanargmax(product))
    peak_gmid = float(tbl._gmid_arr[peak_idx])
    ok = 8.0 <= peak_gmid <= 18.0
    return _report(ok,
        f'Test 4  fT × gm/ID peak       :  '
        f'peak at gm/ID = {peak_gmid:.1f} V^-1  '
        f'(expected 8–18)')


# ─────────────────────────────────────────────────────────────────────────────
# Test 5 — Vds sensitivity
# ─────────────────────────────────────────────────────────────────────────────
def test5_vds_sensitivity(model, L_um):
    """
    gm·ro at gm/ID = 10 must change by >= 10 % when Vds is stepped
    from 0.25·VDD to 0.75·VDD.

    A model that ignores channel-length modulation will show near-zero change.
    The test is direction-agnostic (gmro may rise or fall with Vds).
    """
    GMID_REF = 10.0
    vdd    = float(MODEL_INFO[model].get('vdd', VDD))
    vds_lo = round(vdd * 0.25, 3)
    vds_hi = round(vdd * 0.75, 3)

    tbl_lo = GmIdTable(model, W=10.0, L=L_um, vds=vds_lo)
    tbl_hi = GmIdTable(model, W=10.0, L=L_um, vds=vds_hi)

    gmro_lo = tbl_lo.lookup('gmro', GMID_REF)
    gmro_hi = tbl_hi.lookup('gmro', GMID_REF)
    ratio   = gmro_hi / gmro_lo if gmro_lo > 0 else 0.0
    pct     = abs(ratio - 1.0) * 100.0

    ok = pct >= 10.0
    return _report(ok,
        f'Test 5  Vds sensitivity        :  '
        f'gmro @ Vds={vds_lo}V = {gmro_lo:.1f},  '
        f'@ Vds={vds_hi}V = {gmro_hi:.1f},  '
        f'change = {pct:.1f}%  (expected >= 10%)')


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────
def main():
    # ── parse CLI arguments ──────────────────────────────────────────────────
    model = sys.argv[1] if len(sys.argv) > 1 else 'nmos180'

    if model not in MODEL_INFO:
        avail = list(MODEL_INFO.keys())
        print(f'Unknown model "{model}".  Available: {avail}')
        return 1

    if len(sys.argv) > 2:
        L_um = float(sys.argv[2])
    else:
        m = re.search(r'(\d+)', model)
        L_um = int(m.group(1)) / 1000.0 if m else 0.18

    vdd = float(MODEL_INFO[model].get('vdd', VDD))
    vds = round(vdd * 0.5, 3)

    # ── header ───────────────────────────────────────────────────────────────
    print()
    print(f'  {_B}gm/ID Physical Validation{_E}')
    print(f'  Model: {model},  L = {L_um*1e3:.0f} nm,  '
          f'Vds = {vds} V,  T = 27 C')
    print('  ' + '─' * 68)

    # Build primary table (reused by tests 1, 2, 4)
    tbl = GmIdTable(model, W=10.0, L=L_um, vds=vds)
    print()

    # ── run tests ────────────────────────────────────────────────────────────
    results = [
        test1_weak_inversion(tbl),
        test2_idw_monotonicity(tbl),
        test3_length_scaling(model, L_um, vds),   # builds extra tables
        test4_ft_gmid_peak(tbl),
        test5_vds_sensitivity(model, L_um),        # builds extra tables
    ]

    # ── summary ──────────────────────────────────────────────────────────────
    n_pass  = sum(results)
    n_total = len(results)
    print('  ' + '─' * 68)
    if n_pass == n_total:
        print(f'  Result: {_G}{_B}{n_pass}/{n_total} passed  —  ALL PASS{_E}')
    else:
        print(f'  Result: {_R}{_B}{n_pass}/{n_total} passed  —  '
              f'{n_total - n_pass} FAILED{_E}')
    print()
    print('  See references/validation.md for pass-threshold rationale.')
    print()

    return 0 if n_pass == n_total else 1


if __name__ == '__main__':
    sys.exit(main())
