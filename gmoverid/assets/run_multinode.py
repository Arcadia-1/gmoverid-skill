#!/usr/bin/env python3
"""
run_multinode.py
================
gm/Id characterization across technology nodes:
  45nm HP  (VDD=1.0V)
  22nm HP  (VDD=0.8V)

All models use PTM BSIM4 (level=54).

Output figures (saved to plots/)
----------------------------------
  gmoverid_nmos45hp_L45nm.png    NMOS 45nm HP  4-panel full characterization
  gmoverid_pmos45hp_L45nm.png    PMOS 45nm HP  4-panel full characterization
  gmoverid_nmos22hp_L22nm.png    NMOS 22nm HP  4-panel full characterization
  gmoverid_pmos22hp_L22nm.png    PMOS 22nm HP  4-panel full characterization
  gmid_nmos_node_comp.png        NMOS 4-panel comparison: 180/45/22nm
  gmid_pmos_node_comp.png        PMOS 4-panel comparison: 180/45/22nm
"""

import sys
from pathlib import Path

from simulate_gmoverid import (
    run_vgs_sweeps, run_vds_sweeps,
    run_vsg_sweeps, run_vsd_sweeps,
    MODEL_INFO,
)
from plot_gmoverid import (
    plot_main, plot_comparison, plot_iv, plot_caps, plot_caps_comparison,
    print_summary, PLOT_DIR,
)

# ─────────────────────────────────────────────────────────────────────────────
# Per-node sweep configuration
# ─────────────────────────────────────────────────────────────────────────────
# Each entry:  (nmos_model, pmos_model, l_nm, W_um, vds_list, vgs_bias,
#               vds_comp, vds_comp_hi, vgs_iv, w_iv_um, l_label)
NODE_CFG = {
    '45nm': dict(
        nmos='nmos45hp',   pmos='pmos45hp',
        l_nm=45,           l_um=0.045,
        W=1.0,
        vdd=1.0,
        vds_list =[0.2, 0.3, 0.4],
        vds_gds  =[0.4, 0.5, 0.6, 0.7, 0.8, 1.0],  # saturation Vds for lstsq gds
        vgs_bias =[0.15, 0.25, 0.35, 0.45, 0.55, 0.65, 0.75, 0.85, 0.95],
        vds_comp =[0.5],
        vgs_iv   =[0.4, 0.5, 0.6, 0.7, 0.8],
        w_iv=0.45,         # W/L=10
    ),
    '22nm': dict(
        nmos='nmos22hp',   pmos='pmos22hp',
        l_nm=22,           l_um=0.022,
        W=1.0,
        vdd=0.8,
        vds_list =[0.2, 0.3, 0.4],
        vds_gds  =[0.3, 0.4, 0.5, 0.6, 0.7, 0.8],  # saturation Vds for lstsq gds
        vgs_bias =[0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80],
        vds_comp =[0.4],
        vgs_iv   =[0.3, 0.4, 0.5, 0.6, 0.7],
        w_iv=0.22,         # W/L=10
    ),
}


# ─────────────────────────────────────────────────────────────────────────────
# Helper: run full 6-panel sweep for a node
# ─────────────────────────────────────────────────────────────────────────────
def _run_full(cfg, polarity):
    model  = cfg['nmos'] if polarity == 'nmos' else cfg['pmos']
    W      = cfg['W']
    l_um   = cfg['l_um']
    if polarity == 'nmos':
        vg     = run_vgs_sweeps(W, l_um, model=model, vds_list=cfg['vds_list'])
        vd     = run_vds_sweeps(W, l_um, model=model, vgs_bias_list=cfg['vgs_bias'])
        vg_gds = run_vgs_sweeps(W, l_um, model=model, vds_list=cfg['vds_gds'])
    else:
        vg     = run_vsg_sweeps(W, l_um, model=model, vsd_list=cfg['vds_list'])
        vd     = run_vsd_sweeps(W, l_um, model=model, vsg_bias_list=cfg['vgs_bias'])
        vg_gds = run_vsg_sweeps(W, l_um, model=model, vsd_list=cfg['vds_gds'])
    return vg, vd, vg_gds


def _run_comp(cfg, polarity):
    model  = cfg['nmos'] if polarity == 'nmos' else cfg['pmos']
    W      = cfg['W']
    l_um   = cfg['l_um']
    if polarity == 'nmos':
        vg     = run_vgs_sweeps(W, l_um, model=model, vds_list=cfg['vds_comp'])
        vd     = run_vds_sweeps(W, l_um, model=model, vgs_bias_list=cfg['vgs_bias'])
        vg_gds = run_vgs_sweeps(W, l_um, model=model, vds_list=cfg['vds_gds'])
    else:
        vg     = run_vsg_sweeps(W, l_um, model=model, vsd_list=cfg['vds_comp'])
        vd     = run_vsd_sweeps(W, l_um, model=model, vsg_bias_list=cfg['vgs_bias'])
        vg_gds = run_vsg_sweeps(W, l_um, model=model, vsd_list=cfg['vds_gds'])
    return vg, vd, vg_gds


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────
def main():
    print('=' * 66)
    print('  PTM Multi-Node gm/Id Characterization')
    print('  Nodes: 45nm / 22nm  (HP BSIM4)')
    print('=' * 66)

    nmos_comp_data = {}   # {node_label: (vg_comp, vd_sweeps)} for cross-node plot
    pmos_comp_data = {}

    for node, cfg in NODE_CFG.items():
        l_nm   = cfg['l_nm']
        l_um   = cfg['l_um']
        W      = cfg['W']
        w_iv   = cfg['w_iv']
        vdd    = cfg['vdd']
        nm     = cfg['nmos']
        pm     = cfg['pmos']

        print(f'\n{"─"*66}')
        print(f'  Node: {node}  VDD={vdd}V  W={W}um  L={l_nm}nm')
        print(f'{"─"*66}')

        node_dir = PLOT_DIR / f'{l_nm}nm'

        # ── NMOS full characterization ────────────────────────────────────
        print(f'\n  [{node}] NMOS full sweep ...')
        nmos_vg, nmos_vd, nmos_vg_gds = _run_full(cfg, 'nmos')
        if not nmos_vg:
            print(f'  [ERROR] {node} NMOS sweep failed, skipping.'); continue
        plot_main(nmos_vg, nmos_vd, W, l_um, nm,
                  node_dir / f'gmoverid_{nm}_L{l_nm}nm.png',
                  vgs_gds_results=nmos_vg_gds)
        plot_caps(W, l_um, nm,
                  out_path=node_dir / f'gmoverid_caps_{nm}_L{l_nm}nm.png')
        print_summary(nmos_vg, nmos_vd, nm)

        nmos_vd_iv = run_vds_sweeps(w_iv, l_um, model=nm,
                                    vgs_bias_list=cfg['vgs_iv'])
        plot_iv(nmos_vg, nmos_vd_iv, W, l_um, w_iv_um=w_iv, model=nm,
                out_path=node_dir / f'gmoverid_iv_{nm}_L{l_nm}nm.png')

        # ── PMOS full characterization ────────────────────────────────────
        print(f'\n  [{node}] PMOS full sweep ...')
        pmos_vg, pmos_vd, pmos_vg_gds = _run_full(cfg, 'pmos')
        if pmos_vg:
            plot_main(pmos_vg, pmos_vd, W, l_um, pm,
                      node_dir / f'gmoverid_{pm}_L{l_nm}nm.png',
                      vgs_gds_results=pmos_vg_gds)
            plot_caps(W, l_um, pm,
                      out_path=node_dir / f'gmoverid_caps_{pm}_L{l_nm}nm.png')
            print_summary(pmos_vg, pmos_vd, pm)

            pmos_vd_iv = run_vsd_sweeps(w_iv, l_um, model=pm,
                                        vsg_bias_list=cfg['vgs_iv'])
            plot_iv(pmos_vg, pmos_vd_iv, W, l_um, w_iv_um=w_iv, model=pm,
                    out_path=node_dir / f'gmoverid_iv_{pm}_L{l_nm}nm.png')
        else:
            print(f'  [WARN] {node} PMOS sweep failed.')

        # ── Collect comparison data ───────────────────────────────────────
        print(f'\n  [{node}] Collecting comparison sweep data ...')
        nmos_comp_data[node] = _run_comp(cfg, 'nmos')
        pmos_comp_data[node] = _run_comp(cfg, 'pmos')

    # ── Cross-node comparison: also pull 180nm data for reference ────────
    print('\n  Collecting 180nm reference data for cross-node comparison ...')
    _W180  = 10.0;  _L180 = 0.18
    _VGS180 = [0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 1.00, 1.10]
    _VDS_GDS_180 = [0.5, 0.7, 0.9, 1.1, 1.3, 1.5]
    n180_c   = run_vgs_sweeps(_W180, _L180, model='nmos180', vds_list=[0.9])
    n180_vd  = run_vds_sweeps(_W180, _L180, model='nmos180', vgs_bias_list=_VGS180)
    n180_gds = run_vgs_sweeps(_W180, _L180, model='nmos180', vds_list=_VDS_GDS_180)
    p180_c   = run_vsg_sweeps(_W180, _L180, model='pmos180', vsd_list=[0.9])
    p180_vd  = run_vsd_sweeps(_W180, _L180, model='pmos180', vsg_bias_list=_VGS180)
    p180_gds = run_vsg_sweeps(_W180, _L180, model='pmos180', vsd_list=_VDS_GDS_180)

    # ── NMOS cross-node comparison plot ──────────────────────────────────
    print('\n  Generating NMOS cross-node comparison ...')
    n_sweeps, n_vd_sweeps, n_gds_sweeps, n_labels = [], [], [], []
    n_sweeps.append(n180_c);  n_vd_sweeps.append(n180_vd)
    n_gds_sweeps.append(n180_gds);  n_labels.append('180nm SVT')
    for node in NODE_CFG:
        if node in nmos_comp_data:
            vg, vd, vg_gds = nmos_comp_data[node]
            n_sweeps.append(vg);  n_vd_sweeps.append(vd)
            n_gds_sweeps.append(vg_gds);  n_labels.append(f'{node} HP')

    plot_comparison(
        sweep_list   = n_sweeps,
        vds_list     = n_vd_sweeps,
        vgs_gds_list = n_gds_sweeps,
        param_labels = n_labels,
        polarity     = 'nmos',
        title        = 'NMOS Node Comparison  (PTM, SVT/HP, L=min)',
        out_path     = PLOT_DIR / 'gmid_nmos_node_comp.png',
    )

    # ── PMOS cross-node comparison plot ──────────────────────────────────
    print('\n  Generating PMOS cross-node comparison ...')
    p_sweeps, p_vd_sweeps, p_gds_sweeps, p_labels = [], [], [], []
    p_sweeps.append(p180_c);  p_vd_sweeps.append(p180_vd)
    p_gds_sweeps.append(p180_gds);  p_labels.append('180nm SVT')
    for node in NODE_CFG:
        if node in pmos_comp_data:
            vg, vd, vg_gds = pmos_comp_data[node]
            p_sweeps.append(vg);  p_vd_sweeps.append(vd)
            p_gds_sweeps.append(vg_gds);  p_labels.append(f'{node} HP')

    plot_comparison(
        sweep_list   = p_sweeps,
        vds_list     = p_vd_sweeps,
        vgs_gds_list = p_gds_sweeps,
        param_labels = p_labels,
        polarity     = 'pmos',
        title        = 'PMOS Node Comparison  (PTM, SVT/HP, L=min)',
        out_path     = PLOT_DIR / 'gmid_pmos_node_comp.png',
    )

    # ── Combined capacitance comparison: 180nm + HP nodes ────────────────
    print('\n  Generating capacitance comparison figures ...')
    nmos_caps_cfg = [('nmos180', 10.0, 0.18)] + [
        (cfg['nmos'], cfg['W'], cfg['l_um']) for cfg in NODE_CFG.values()]
    pmos_caps_cfg = [('pmos180', 10.0, 0.18)] + [
        (cfg['pmos'], cfg['W'], cfg['l_um']) for cfg in NODE_CFG.values()]
    plot_caps_comparison(nmos_caps_cfg, polarity='nmos',
                         out_path=PLOT_DIR / 'gmid_nmos_caps_comp.png')
    plot_caps_comparison(pmos_caps_cfg, polarity='pmos',
                         out_path=PLOT_DIR / 'gmid_pmos_caps_comp.png')

    # ── Summary ───────────────────────────────────────────────────────────
    print('\n' + '=' * 66)
    print('  Done.  Output figures:')
    for p in sorted(PLOT_DIR.rglob('gmoverid_*.png')) + \
             sorted(PLOT_DIR.rglob('gmid_*.png')):
        print(f'    {p}')
    print('=' * 66)


if __name__ == '__main__':
    main()
