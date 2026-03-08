#!/usr/bin/env python3
"""
run_gmoverid.py
===============
Full gm/Id characterization sweep for PTM 180nm:
  - NMOS / PMOS (SVT only)
  - Multiple channel lengths: 180 nm, 360 nm, 1000 nm

Output figures (saved to plots/180nm/)
---------------------------------------
  gmoverid_nmos180_L180nm.png          NMOS gm/ID 主图（4-panel）
  gmoverid_pmos180_L180nm.png          PMOS gm/ID 主图（4-panel）
  gmoverid_caps_nmos180_L180nm.png     NMOS 栅电容
  gmoverid_caps_pmos180_L180nm.png     PMOS 栅电容
  gmoverid_iv_nmos180_L180nm.png       NMOS IV 特性
  gmoverid_iv_pmos180_L180nm.png       PMOS IV 特性
  gmid_nmos_length.png                 NMOS 沟道长度对比（180/360/1000nm）
  gmid_pmos_length.png                 PMOS 沟道长度对比（180/360/1000nm）
"""

import sys
from pathlib import Path

from simulate_gmoverid import (
    run_vgs_sweeps, run_vds_sweeps,
    run_vsg_sweeps, run_vsd_sweeps,
    W_UM, VDS_LIST, VDS_GDS, VGS_BIAS,
)
from plot_gmoverid import (
    plot_main, plot_comparison, plot_iv, plot_caps, print_summary, PLOT_DIR,
)

DIR_180 = PLOT_DIR / '180nm'

# ─────────────────────────────────────────────────────────────────────────────
# Sweep configuration
# ─────────────────────────────────────────────────────────────────────────────
W         = W_UM          # 10 um (fixed)
L_MIN     = 0.18          # 180 nm (minimum / main length)
L_LIST    = [0.18, 0.36, 1.00]   # for length comparison
VDS_COMP  = [0.9]         # primary Vds for comparison figures

# Dense Vgs bias list for VDS output sweeps used in gm*ro interpolation.
VGS_BIAS_DENSE = [0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 1.00, 1.10]

W_IV      = 1.8           # W for output-characteristic plot: W/L=10, L=180nm
VGS_IV    = [0.6, 0.7, 0.8, 0.9, 1.0]   # Vgs bias points for Vds output curves


# ─────────────────────────────────────────────────────────────────────────────
# Helper: run full 6-panel sweep (4 Vds + 4 Vds-bias)
# ─────────────────────────────────────────────────────────────────────────────
def _run_full(polarity, model, l_um):
    if polarity == 'nmos':
        vg     = run_vgs_sweeps(W, l_um, model=model, vds_list=VDS_LIST)
        vd     = run_vds_sweeps(W, l_um, model=model, vgs_bias_list=VGS_BIAS_DENSE)
        vg_gds = run_vgs_sweeps(W, l_um, model=model, vds_list=VDS_GDS)
    else:
        vg     = run_vsg_sweeps(W, l_um, model=model, vsd_list=VDS_LIST)
        vd     = run_vsd_sweeps(W, l_um, model=model, vsg_bias_list=VGS_BIAS_DENSE)
        vg_gds = run_vsg_sweeps(W, l_um, model=model, vsd_list=VDS_GDS)
    return vg, vd, vg_gds


# ─────────────────────────────────────────────────────────────────────────────
# Helper: run primary Vgs sweep + VDS output sweeps for comparison figures.
# ─────────────────────────────────────────────────────────────────────────────
def _run_comp(polarity, model, l_um):
    if polarity == 'nmos':
        vg = run_vgs_sweeps(W, l_um, model=model, vds_list=VDS_COMP)
        vd = run_vds_sweeps(W, l_um, model=model, vgs_bias_list=VGS_BIAS_DENSE)
    else:
        vg = run_vsg_sweeps(W, l_um, model=model, vsd_list=VDS_COMP)
        vd = run_vsd_sweeps(W, l_um, model=model, vsg_bias_list=VGS_BIAS_DENSE)
    return vg, vd


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────
def main():
    print('=' * 66)
    print('  PTM 180nm NMOS + PMOS  gm/Id Full Characterization')
    print(f'  W = {W} um   L_list = {[f"{l*1000:.0f}nm" for l in L_LIST]}')
    print('=' * 66)

    # ── 1. NMOS full characterization (L = 180 nm) ────────────────────────────
    print('\n[1/4] NMOS  L=180nm  full sweep ...')
    nmos_vg, nmos_vd, nmos_vg_gds = _run_full('nmos', 'nmos180', L_MIN)
    if not nmos_vg:
        print('[ERROR] NMOS sweep failed.'); sys.exit(1)
    out = plot_main(nmos_vg, nmos_vd, W, L_MIN, 'nmos180',
                    out_path=DIR_180 / 'gmoverid_nmos180_L180nm.png',
                    vgs_gds_results=nmos_vg_gds)
    plot_caps(W, L_MIN, 'nmos180',
              out_path=DIR_180 / 'gmoverid_caps_nmos180_L180nm.png')
    print_summary(nmos_vg, nmos_vd, 'nmos180')
    nmos_vds_iv = run_vds_sweeps(W_IV, L_MIN, model='nmos180',
                                 vgs_bias_list=VGS_IV)
    plot_iv(nmos_vg, nmos_vds_iv, W, L_MIN, w_iv_um=W_IV,
            model='nmos180',
            out_path=DIR_180 / 'gmoverid_iv_nmos180_L180nm.png')

    # ── 2. PMOS full characterization (L = 180 nm) ────────────────────────────
    print('\n[2/4] PMOS  L=180nm  full sweep ...')
    pmos_vg, pmos_vd, pmos_vg_gds = _run_full('pmos', 'pmos180', L_MIN)
    if not pmos_vg:
        print('[WARN] PMOS sweep failed.')
        pmos_vg, pmos_vd, pmos_vg_gds = [], [], []
    else:
        plot_main(pmos_vg, pmos_vd, W, L_MIN, 'pmos180',
                  out_path=DIR_180 / 'gmoverid_pmos180_L180nm.png',
                  vgs_gds_results=pmos_vg_gds)
        plot_caps(W, L_MIN, 'pmos180',
                  out_path=DIR_180 / 'gmoverid_caps_pmos180_L180nm.png')
        print_summary(pmos_vg, pmos_vd, 'pmos180')
        pmos_vsd_iv = run_vsd_sweeps(W_IV, L_MIN, model='pmos180',
                                     vsg_bias_list=VGS_IV)
        plot_iv(pmos_vg, pmos_vsd_iv, W, L_MIN, w_iv_um=W_IV,
                model='pmos180',
                out_path=DIR_180 / 'gmoverid_iv_pmos180_L180nm.png')

    # ── 3. Length comparison: NMOS  L = 180 / 360 / 1000 nm ──────────────────
    print('\n[3/4] NMOS  Length comparison ...')
    nmos_l180_c, nmos_l180_d = _run_comp('nmos', 'nmos180', 0.18)
    nmos_l360_c, nmos_l360_d = _run_comp('nmos', 'nmos180', 0.36)
    nmos_l1000_c, nmos_l1000_d = _run_comp('nmos', 'nmos180', 1.00)

    plot_comparison(
        sweep_list   = [nmos_l180_c, nmos_l360_c, nmos_l1000_c],
        vds_list     = [nmos_l180_d, nmos_l360_d, nmos_l1000_d],
        param_labels = ['L = 180 nm', 'L = 360 nm', 'L = 1000 nm'],
        polarity     = 'nmos',
        title        = ('NMOS  Channel Length Comparison  '
                        '(PTM 180nm, W=10$\\mu$m, $V_{DS}$=0.9V)'),
        out_path     = DIR_180 / 'gmid_nmos_length.png',
    )

    # ── 4. Length comparison: PMOS  L = 180 / 360 / 1000 nm ──────────────────
    print('\n[4/4] PMOS  Length comparison ...')
    pmos_l180_c, pmos_l180_d = _run_comp('pmos', 'pmos180', 0.18)
    pmos_l360_c, pmos_l360_d = _run_comp('pmos', 'pmos180', 0.36)
    pmos_l1000_c, pmos_l1000_d = _run_comp('pmos', 'pmos180', 1.00)

    plot_comparison(
        sweep_list   = [pmos_l180_c, pmos_l360_c, pmos_l1000_c],
        vds_list     = [pmos_l180_d, pmos_l360_d, pmos_l1000_d],
        param_labels = ['L = 180 nm', 'L = 360 nm', 'L = 1000 nm'],
        polarity     = 'pmos',
        title        = ('PMOS  Channel Length Comparison  '
                        '(PTM 180nm, W=10$\\mu$m, |$V_{SD}$|=0.9V)'),
        out_path     = DIR_180 / 'gmid_pmos_length.png',
    )

    # ── Summary ───────────────────────────────────────────────────────────────
    print('\n' + '=' * 66)
    print('  Done.  Output figures:')
    for p in sorted(DIR_180.glob('gmoverid_*.png')) + \
             sorted(DIR_180.glob('gmid_*.png')):
        print(f'    {p}')
    print('=' * 66)


if __name__ == '__main__':
    main()
