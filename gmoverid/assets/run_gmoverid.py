#!/usr/bin/env python3
"""
run_gmoverid.py
===============
Full gm/Id characterization sweep:
  - NMOS / PMOS
  - LVT / SVT / HVT threshold variants
  - Multiple channel lengths: 180 nm, 360 nm, 1000 nm

Output figures (saved to plots/180nm/)
---------------------------------------
  gmoverid_nmos180_L180nm.png          NMOS SVT gm/ID 主图（4-panel）
  gmoverid_pmos180_L180nm.png          PMOS SVT gm/ID 主图（4-panel）
  gmoverid_caps_nmos180_L180nm.png     NMOS SVT 栅电容
  gmoverid_caps_pmos180_L180nm.png     PMOS SVT 栅电容
  gmoverid_iv_nmos180_L180nm.png       NMOS SVT IV 特性
  gmoverid_iv_pmos180_L180nm.png       PMOS SVT IV 特性
  gmid_nmos_vth_L180nm.png             NMOS LVT/SVT/HVT 阈值对比
  gmid_pmos_vth_L180nm.png             PMOS LVT/SVT/HVT 阈值对比
  gmid_nmos_length_svt.png             NMOS SVT 沟道长度对比（180/360/1000nm）
  gmid_pmos_length_svt.png             PMOS SVT 沟道长度对比（180/360/1000nm）
"""

import sys
from pathlib import Path

from simulate_gmoverid import (
    run_vgs_sweeps, run_vds_sweeps,
    run_vsg_sweeps, run_vsd_sweeps,
    W_UM, VDS_LIST, VGS_BIAS,
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
VDS_COMP    = [0.9]       # primary Vds for comparison figures

# Dense Vgs bias list for VDS output sweeps used in gm*ro interpolation.
# Covers gm/ID = 4..24 for all three Vth variants (LVT/SVT/HVT).
VGS_BIAS    = [0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 1.00, 1.10]

W_IV        = 1.8         # W for output-characteristic plot: W/L=10, L=180nm
VGS_IV      = [0.6, 0.7, 0.8, 0.9, 1.0]   # Vgs bias points for Vds output curves

NMOS_MODELS = {
    'lvt': 'nmos180_lvt',
    'svt': 'nmos180',
    'hvt': 'nmos180_hvt',
}
PMOS_MODELS = {
    'lvt': 'pmos180_lvt',
    'svt': 'pmos180',
    'hvt': 'pmos180_hvt',
}

# ─────────────────────────────────────────────────────────────────────────────
# Helper: run full 6-panel sweep (4 Vds + 4 Vds-bias)
# ─────────────────────────────────────────────────────────────────────────────
def _run_full(polarity, model, l_um):
    if polarity == 'nmos':
        vg  = run_vgs_sweeps(W, l_um, model=model, vds_list=VDS_LIST)
        vd  = run_vds_sweeps(W, l_um, model=model, vgs_bias_list=VGS_BIAS)
    else:
        vg  = run_vsg_sweeps(W, l_um, model=model, vsd_list=VDS_LIST)
        vd  = run_vsd_sweeps(W, l_um, model=model, vsg_bias_list=VGS_BIAS)
    return vg, vd


# ─────────────────────────────────────────────────────────────────────────────
# Helper: run primary Vgs sweep + VDS output sweeps for comparison figures.
# Returns (vgs_primary, vd_sweeps).
# vd_sweeps: list of VDS output-curve sweeps at many Vgs bias points,
# used to interpolate gds(Vgs) for the gm*ro vs gm/Id panel.
# ─────────────────────────────────────────────────────────────────────────────
def _run_comp(polarity, model, l_um):
    if polarity == 'nmos':
        vg = run_vgs_sweeps(W, l_um, model=model, vds_list=VDS_COMP)
        vd = run_vds_sweeps(W, l_um, model=model, vgs_bias_list=VGS_BIAS)
    else:
        vg = run_vsg_sweeps(W, l_um, model=model, vsd_list=VDS_COMP)
        vd = run_vsd_sweeps(W, l_um, model=model, vsg_bias_list=VGS_BIAS)
    return vg, vd


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────
def main():
    print('=' * 66)
    print('  PTM 180nm NMOS + PMOS  gm/Id Full Characterization')
    print(f'  W = {W} um   L_list = {[f"{l*1000:.0f}nm" for l in L_LIST]}')
    print(f'  Vth types: LVT / SVT / HVT')
    print('=' * 66)

    # ── 1. NMOS SVT full characterization (L = 180 nm) ───────────────────────
    print('\n[1/6] NMOS SVT  L=180nm  full sweep ...')
    nmos_svt_vg, nmos_svt_vd = _run_full('nmos', 'nmos180', L_MIN)
    if not nmos_svt_vg:
        print('[ERROR] NMOS SVT sweep failed.'); sys.exit(1)
    out = plot_main(nmos_svt_vg, nmos_svt_vd, W, L_MIN, 'nmos180',
                    DIR_180 / 'gmoverid_nmos180_L180nm.png')
    plot_caps(W, L_MIN, 'nmos180',
              out_path=DIR_180 / 'gmoverid_caps_nmos180_L180nm.png')
    print_summary(nmos_svt_vg, nmos_svt_vd, 'nmos180')
    nmos_vds_iv = run_vds_sweeps(W_IV, L_MIN, model='nmos180',
                                 vgs_bias_list=VGS_IV)
    plot_iv(nmos_svt_vg, nmos_vds_iv, W, L_MIN, w_iv_um=W_IV,
            model='nmos180',
            out_path=DIR_180 / 'gmoverid_iv_nmos180_L180nm.png')

    # ── 2. PMOS SVT full characterization (L = 180 nm) ───────────────────────
    print('\n[2/6] PMOS SVT  L=180nm  full sweep ...')
    pmos_svt_vg, pmos_svt_vd = _run_full('pmos', 'pmos180', L_MIN)
    if not pmos_svt_vg:
        print('[WARN] PMOS SVT sweep failed.')
        pmos_svt_vg, pmos_svt_vd = [], []
    else:
        plot_main(pmos_svt_vg, pmos_svt_vd, W, L_MIN, 'pmos180',
                  DIR_180 / 'gmoverid_pmos180_L180nm.png')
        plot_caps(W, L_MIN, 'pmos180',
                  out_path=DIR_180 / 'gmoverid_caps_pmos180_L180nm.png')
        print_summary(pmos_svt_vg, pmos_svt_vd, 'pmos180')
        pmos_vsd_iv = run_vsd_sweeps(W_IV, L_MIN, model='pmos180',
                                     vsg_bias_list=VGS_IV)
        plot_iv(pmos_svt_vg, pmos_vsd_iv, W, L_MIN, w_iv_um=W_IV,
                model='pmos180',
                out_path=DIR_180 / 'gmoverid_iv_pmos180_L180nm.png')

    # ── 3. Vth comparison: NMOS  L=180nm  LVT / SVT / HVT ───────────────────
    print('\n[3/6] NMOS  Vth comparison (LVT/SVT/HVT)  L=180nm ...')
    nmos_lvt_c, nmos_lvt_d = _run_comp('nmos', 'nmos180_lvt', L_MIN)
    nmos_svt_c, nmos_svt_d = _run_comp('nmos', 'nmos180',     L_MIN)
    nmos_hvt_c, nmos_hvt_d = _run_comp('nmos', 'nmos180_hvt', L_MIN)

    plot_comparison(
        sweep_list   = [nmos_lvt_c, nmos_svt_c, nmos_hvt_c],
        vds_list     = [nmos_lvt_d, nmos_svt_d, nmos_hvt_d],
        param_labels = ['LVT  $V_{th}$=0.30V', 'SVT  $V_{th}$=0.40V',
                        'HVT  $V_{th}$=0.55V'],
        polarity     = 'nmos',
        title        = ('NMOS  Vth Comparison  (PTM 180nm, W=10$\\mu$m, '
                        'L=180nm, $V_{DS}$=0.9V)'),
        out_path     = DIR_180 / 'gmid_nmos_vth_L180nm.png',
    )

    # ── 4. Vth comparison: PMOS  L=180nm  LVT / SVT / HVT ───────────────────
    print('\n[4/6] PMOS  Vth comparison (LVT/SVT/HVT)  L=180nm ...')
    pmos_lvt_c, pmos_lvt_d = _run_comp('pmos', 'pmos180_lvt', L_MIN)
    pmos_svt_c, pmos_svt_d = _run_comp('pmos', 'pmos180',     L_MIN)
    pmos_hvt_c, pmos_hvt_d = _run_comp('pmos', 'pmos180_hvt', L_MIN)

    plot_comparison(
        sweep_list   = [pmos_lvt_c, pmos_svt_c, pmos_hvt_c],
        vds_list     = [pmos_lvt_d, pmos_svt_d, pmos_hvt_d],
        param_labels = ['LVT  |$V_{tp}$|=0.32V', 'SVT  |$V_{tp}$|=0.42V',
                        'HVT  |$V_{tp}$|=0.57V'],
        polarity     = 'pmos',
        title        = ('PMOS  Vth Comparison  (PTM 180nm, W=10$\\mu$m, '
                        'L=180nm, |$V_{SD}$|=0.9V)'),
        out_path     = DIR_180 / 'gmid_pmos_vth_L180nm.png',
    )

    # ── 5. Length comparison: NMOS SVT  L = 180 / 360 / 1000 nm ─────────────
    print('\n[5/6] NMOS SVT  Length comparison ...')
    nmos_l180_c, nmos_l180_d = nmos_svt_c, nmos_svt_d   # reuse from step 3
    nmos_l360_c, nmos_l360_d = _run_comp('nmos', 'nmos180', 0.36)
    nmos_l1000_c, nmos_l1000_d = _run_comp('nmos', 'nmos180', 1.00)

    plot_comparison(
        sweep_list   = [nmos_l180_c, nmos_l360_c, nmos_l1000_c],
        vds_list     = [nmos_l180_d, nmos_l360_d, nmos_l1000_d],
        param_labels = ['L = 180 nm', 'L = 360 nm', 'L = 1000 nm'],
        polarity     = 'nmos',
        title        = ('NMOS SVT  Channel Length Comparison  '
                        '(PTM 180nm, W=10$\\mu$m, $V_{DS}$=0.9V)'),
        out_path     = DIR_180 / 'gmid_nmos_length_svt.png',
    )

    # ── 6. Length comparison: PMOS SVT  L = 180 / 360 / 1000 nm ─────────────
    print('\n[6/6] PMOS SVT  Length comparison ...')
    pmos_l180_c, pmos_l180_d = pmos_svt_c, pmos_svt_d   # reuse from step 4
    pmos_l360_c, pmos_l360_d   = _run_comp('pmos', 'pmos180', 0.36)
    pmos_l1000_c, pmos_l1000_d = _run_comp('pmos', 'pmos180', 1.00)

    plot_comparison(
        sweep_list   = [pmos_l180_c, pmos_l360_c, pmos_l1000_c],
        vds_list     = [pmos_l180_d, pmos_l360_d, pmos_l1000_d],
        param_labels = ['L = 180 nm', 'L = 360 nm', 'L = 1000 nm'],
        polarity     = 'pmos',
        title        = ('PMOS SVT  Channel Length Comparison  '
                        '(PTM 180nm, W=10$\\mu$m, |$V_{SD}$|=0.9V)'),
        out_path     = DIR_180 / 'gmid_pmos_length_svt.png',
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
