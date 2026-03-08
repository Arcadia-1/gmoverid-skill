#!/usr/bin/env python3
"""
plot_gmoverid.py
================
Plotting functions for NMOS/PMOS gm/Id characterization.

Exports
-------
plot_main(vgs_results, vds_results, w_um, l_um, model, out_path)
    6-panel full characterization figure (works for NMOS and PMOS).

plot_comparison(sweep_list, w_um, l_um, sweep_param, param_labels,
                polarity, out_path)
    4-panel comparison figure: overlay curves for L sweep or Vth sweep.
    sweep_param : 'length' | 'vth'
    Each entry in sweep_list is a list of vgs_results from run_vgs_sweeps()
    at a single Vds/Vsd value (0.9 V).

plot_caps(w_um, l_um, model, out_path)
    Analytical gate capacitances vs Vgs/|Vsg|.

plot_caps_comparison(node_configs, polarity, out_path)
    2×2 panel: one cap subplot per technology node.

print_summary(vgs_results, vds_results)
    ASCII table to console.
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
from pathlib import Path

from simulate_gmoverid import (COX, MODEL_INFO, VDD, VDS_STOP,
                                compute_caps, W_UM, L_UM,
                                _parse_lib_params)

# ─────────────────────────────────────────────────────────────────────────────
# Style
# ─────────────────────────────────────────────────────────────────────────────
COLORS = ['#1565C0', '#E65100', '#2E7D32', '#C62828']
LSTYLE = ['-', '--', '-.', ':']
REF_C  = '#777777'
# Extended palette for cross-node plots with 5+ curves
_COLORS_EXT = COLORS + ['#7B1FA2', '#00838F', '#37474F']
_LSTYLE_EXT = LSTYLE + LSTYLE
GRID_C = '#DDDDDD'

plt.rcParams.update({
    'font.size':         10,
    'axes.linewidth':    0.8,
    'axes.grid':         True,
    'grid.color':        GRID_C,
    'grid.linewidth':    0.6,
    'legend.framealpha': 0.85,
    'legend.fontsize':   8,
})

PLOT_DIR = Path(__file__).resolve().parent / 'plots'
PLOT_DIR.mkdir(parents=True, exist_ok=True)


# ─────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────────────────
def _gds_at_vds(vds_results, vgs_arr, vds_ref, gm_arr=None):
    """
    Interpolate gds(Vgs) at a fixed VDS operating point using VDS output sweeps.

    Parameters
    ----------
    vds_results : list of dicts from run_vds_sweeps() / run_vsd_sweeps().
                  Each dict has: vgs (scalar bias), vds (array), gds (array).
    vgs_arr     : 1D array of Vgs (or |Vsg|) values from the primary VGS sweep.
    vds_ref     : float, the VDS at which to evaluate gds.
    gm_arr      : optional gm array (same length as vgs_arr). When provided,
                  the subthreshold extrapolation below the measured Vgs range
                  scales gds proportionally to gm so that gm·ro remains
                  constant (physically correct: in subthreshold gds ∝ Id ∝ gm).

    Returns gds array, same shape as vgs_arr, clipped to >= 1e-15.
    """
    pts = []
    for r in vds_results:
        vds_arr = np.asarray(r['vds'])
        gds_arr = np.asarray(r['gds'])
        if vds_ref <= 0 or len(vds_arr) < 3:
            continue
        idx = np.argmin(np.abs(vds_arr - vds_ref))
        if vds_arr[idx] < 0.5 * vds_ref:   # not yet in saturation
            continue
        pts.append((float(r['vgs']), float(gds_arr[idx])))
    if len(pts) < 2:
        return np.full(len(vgs_arr), 1e-15)
    pts.sort()
    vgs_pts = np.array([p[0] for p in pts])
    gds_pts = np.array([p[1] for p in pts])
    # gds ∝ exp(Vgs/Vth) in weak inversion → interpolate in log space
    log_gds = np.log(np.maximum(gds_pts, 1e-30))
    log_gds_interp = np.interp(vgs_arr, vgs_pts, log_gds,
                                left=np.nan, right=log_gds[-1])

    # Below lowest measured Vgs (subthreshold region): gds ∝ Id ∝ gm, so
    # gm·ro should remain constant at gm·ro(Vgs_min).
    # Scale gds proportionally to gm relative to its value at Vgs_min.
    below = vgs_arr < vgs_pts[0]
    if np.any(below):
        gds_at_min = np.exp(log_gds[0])
        if gm_arr is not None:
            gm_at_min = float(np.interp(vgs_pts[0], vgs_arr, gm_arr))
            if gm_at_min > 0:
                scale = gm_arr[below] / gm_at_min
                log_gds_interp[below] = np.log(np.maximum(gds_at_min * scale, 1e-30))
            else:
                log_gds_interp[below] = log_gds[0]
        else:
            # Fallback: linear extrapolation in log space using measured slope
            slope = ((log_gds[1] - log_gds[0]) / (vgs_pts[1] - vgs_pts[0])
                     if len(vgs_pts) >= 2 else 25.0)
            log_gds_interp[below] = log_gds[0] + slope * (vgs_arr[below] - vgs_pts[0])

    return np.maximum(np.exp(log_gds_interp), 1e-15)


def _gds_from_sweeps(vgs_gds_results):
    """
    Compute gds(Vgs) via lstsq regression of Id vs Vds across multiple
    saturation-bias Vgs sweeps.  Returns a 1-D gds array at every Vgs point,
    perfectly smooth (no interpolation artefacts).

    Parameters
    ----------
    vgs_gds_results : list of dicts (output of run_vgs_sweeps / run_vsg_sweeps),
                      each at a different saturation Vds value.

    Returns
    -------
    gds : 1-D numpy array, same length as vgs_gds_results[0]['id'], clipped >= 1e-15.
    """
    vds_vals = np.array([float(r['vds']) for r in vgs_gds_results])
    id_mat   = np.column_stack([r['id'] for r in vgs_gds_results])  # (n_vgs, n_vds)
    A        = np.vstack([vds_vals, np.ones_like(vds_vals)]).T       # (n_vds, 2)
    coeffs, _, _, _ = np.linalg.lstsq(A, id_mat.T, rcond=None)
    return np.maximum(coeffs[0], 1e-15)   # slope row = gds at each Vgs


def _gm_at_vg(vgs_results, vg_target, vds_target=0.9):
    """Return gm from vgs_results at (vg_target, vds≈vds_target)."""
    r = next((x for x in vgs_results if abs(x['vds'] - vds_target) < 0.15),
             vgs_results[0] if vgs_results else None)
    if r is None:
        return None
    idx = np.argmin(np.abs(r['vgs'] - vg_target))
    return float(r['gm'][idx])


def _pol_labels(pol):
    """Return axis label strings for given polarity."""
    if pol == 'pmos':
        return dict(vg='|$V_{SG}$| [V]', vd='|$V_{SD}$| [V]',
                    vov='|$V_{OV}$| = |$V_{SG}$|−|$V_{tp}$|  [V]',
                    id_lbl='|$I_D$|/W  [$\\mu$A/$\\mu$m]',
                    bias_prefix='|Vsg|=',
                    vds_pfx='|$V_{SD}$|=')
    return dict(vg='$V_{GS}$ [V]', vd='$V_{DS}$ [V]',
                vov='$V_{OV}$ = $V_{GS}$−$V_{th}$  [V]',
                id_lbl='$I_D/W$  [$\\mu$A/$\\mu$m]',
                bias_prefix='Vgs=',
                vds_pfx='$V_{DS}$=')


# ─────────────────────────────────────────────────────────────────────────────
# 4-panel gm/Id characterization figure
# ─────────────────────────────────────────────────────────────────────────────
def plot_main(vgs_results, vds_results, w_um, l_um, model='nmos180',
              out_path=None, vgs_gds_results=None):
    pol      = MODEL_INFO[model]['pol']
    lbl      = _pol_labels(pol)
    info     = MODEL_INFO[model]
    vds_stop = info.get('vds_stop', VDS_STOP)

    fig, axes = plt.subplots(2, 2, figsize=(12, 9))
    (ax00, ax01, ax10, ax11) = axes.flat

    _gmid_ticks = list(range(4, 25, 2))

    # ── (0,0) gm/Id vs Vov ───────────────────────────────────────────────────
    for i, r in enumerate(vgs_results):
        c, ls = COLORS[i % 4], LSTYLE[i % 4]
        vov = r['vov'];  gmid = r['gmid']
        mask = np.isfinite(gmid) & (vov > -0.5) & (vov < 0.8)
        ax00.plot(vov[mask], gmid[mask], color=c, ls=ls, lw=1.8,
                  label=f'{lbl["vds_pfx"]}{r["vds"]:.2f}V')

    ax00.axhline(1.0/0.02585, color=REF_C, ls=':', lw=1.2, label='BJT $q/kT$=38.6')
    vov_ref = np.linspace(0.005, 0.4, 200)
    ax00.plot(vov_ref, 2.0/vov_ref, color=REF_C, ls='--', lw=1.2, label='$2/V_{OV}$')
    ax00.set_xlabel(lbl['vov'])
    ax00.set_ylabel('$g_m / I_D$  [V$^{-1}$]')
    ax00.set_xlim(-0.45, 0.75);  ax00.set_ylim(0, 42)
    ax00.set_title('$g_m/I_D$ vs $V_{OV}$')
    ax00.legend(loc='upper right', ncol=2)

    # ── (0,1) Id/W vs gm/Id  (log y) ─────────────────────────────────────────
    for i, r in enumerate(vgs_results):
        c, ls = COLORS[i % 4], LSTYLE[i % 4]
        id_w = r['id_w'];  gmid = r['gmid']
        mask = np.isfinite(gmid) & (id_w > 1e-6) & (gmid >= 4) & (gmid <= 24)
        ax01.semilogy(gmid[mask], id_w[mask], color=c, ls=ls, lw=1.8,
                      label=f'{lbl["vds_pfx"]}{r["vds"]:.2f}V')

    ax01.set_xlabel('$g_m / I_D$  [V$^{-1}$]')
    ax01.set_ylabel(lbl['id_lbl'])
    ax01.set_xlim(4, 24);  ax01.set_xticks(_gmid_ticks)
    ax01.set_title('$I_D/W$ vs $g_m/I_D$')
    ax01.legend()

    # ── (1,0) fT vs gm/Id ────────────────────────────────────────────────────
    for i, r in enumerate(vgs_results):
        c, ls = COLORS[i % 4], LSTYLE[i % 4]
        ft = r['ft'];  gmid = r['gmid']
        mask = (np.isfinite(ft) & (ft > 1e8) &
                np.isfinite(gmid) & (gmid >= 4) & (gmid <= 24))
        ax10.plot(gmid[mask], ft[mask]/1e9, color=c, ls=ls, lw=1.8,
                  label=f'{lbl["vds_pfx"]}{r["vds"]:.2f}V')

    ax10.set_xlabel('$g_m / I_D$  [V$^{-1}$]')
    ax10.set_ylabel('$f_T$  [GHz]')
    ax10.set_xlim(4, 24);  ax10.set_xticks(_gmid_ticks);  ax10.set_ylim(bottom=0)
    ax10.set_title('$f_T$ vs $g_m/I_D$')
    ax10.legend()

    # ── (1,1) Intrinsic gain gm·ro vs gm/Id  (parametric in VDS) ────────────
    # Compute gds via lstsq from dense saturation Vds sweeps (smooth, no kinks)
    # Fall back to _gds_at_vds interpolation if dense sweeps not provided.
    if vgs_gds_results and len(vgs_gds_results) >= 2:
        gds_smooth = _gds_from_sweeps(vgs_gds_results)
        # gds_smooth is indexed on the same Vgs grid as vgs_results[0]
        ref_vgs = vgs_results[0]['vgs']
    else:
        gds_smooth = None

    from scipy.signal import medfilt
    for i, r_vgs in enumerate(vgs_results):
        c, ls   = COLORS[i % 4], LSTYLE[i % 4]
        vds_ref = float(r_vgs['vds'])
        gmid    = r_vgs['gmid']
        gm_arr  = r_vgs['gm']
        vgs_arr = r_vgs['vgs']

        if gds_smooth is not None:
            # Interpolate smooth gds onto this sweep's Vgs grid (grids may differ)
            gds = np.interp(vgs_arr, ref_vgs, gds_smooth)
            gds = np.maximum(gds, 1e-15)
            gmro = gm_arr / gds
        else:
            gds  = _gds_at_vds(vds_results, vgs_arr, vds_ref, gm_arr=gm_arr)
            gmro = medfilt(gm_arr / gds, kernel_size=11)

        mask = (np.isfinite(gmro) & np.isfinite(gmid) &
                (gmid >= 4) & (gmid <= 24) & (gmro > 0) & (gmro < 500))
        ax11.plot(gmid[mask], gmro[mask], color=c, ls=ls, lw=1.8,
                  label=f'{lbl["vds_pfx"]}{r_vgs["vds"]:.2f}V')

    ax11.set_xlabel('$g_m / I_D$  [V$^{-1}$]')
    ax11.set_ylabel('Intrinsic Gain  $g_m r_o$')
    ax11.set_xlim(4, 24);  ax11.set_xticks(_gmid_ticks);  ax11.set_ylim(bottom=0)
    ax11.set_title('Intrinsic Gain vs $g_m/I_D$')
    ax11.legend()

    pol_str  = 'NMOS' if pol == 'nmos' else 'PMOS'
    node_str = model.replace('nmos', '').replace('pmos', '').replace('_', ' ').strip().upper() or 'SVT'
    fig.suptitle(
        f'{pol_str} gm/Id Characterization  ({node_str},  '
        f'W={w_um:.0f}$\\mu$m,  L={l_um*1000:.0f}nm,  T=27$\\degree$C)',
        fontsize=13, y=1.01)
    plt.tight_layout()

    if out_path is None:
        out_path = PLOT_DIR / f'gmoverid_{model}_L{l_um*1000:.0f}nm.png'
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f'  Saved -> {out_path}')
    return out_path


# ─────────────────────────────────────────────────────────────────────────────
# 4-panel comparison figure (L sweep or Vth sweep)
# ─────────────────────────────────────────────────────────────────────────────
def plot_comparison(sweep_list, param_labels, polarity, title, out_path,
                    vds_list=None):
    """
    Parameters
    ----------
    sweep_list   : list of vgs_results lists, one per curve.
                   Each element is the output of run_vgs_sweeps() at one Vds value.
                   The first result in each list (index 0) is used.
    vds_list     : optional list of vds_results lists (from run_vds_sweeps/run_vsd_sweeps),
                   one per curve, used to compute gm*ro for panel 4.
    param_labels : list of strings, one per curve (legend entries)
    polarity     : 'nmos' | 'pmos'
    title        : figure suptitle
    out_path     : output PNG path
    """
    lbl = _pol_labels(polarity)
    fig, axes = plt.subplots(2, 2, figsize=(12, 9))
    (ax00, ax01, ax10, ax11_) = axes.flat

    for i, (res_list, lab) in enumerate(zip(sweep_list, param_labels)):
        if not res_list:
            continue
        r  = res_list[0]
        c  = _COLORS_EXT[i % len(_COLORS_EXT)]
        ls = _LSTYLE_EXT[i % len(_LSTYLE_EXT)]

        id_w = r['id_w']
        gmid = r['gmid']
        vov  = r['vov']
        ft   = r['ft']

        # ── (0,0) gm/Id vs Vov ──
        mask = np.isfinite(gmid) & (vov > -0.55) & (vov < 0.8)
        ax00.plot(vov[mask], gmid[mask], color=c, ls=ls, lw=2.0, label=lab)

        # ── (0,1) Id/W vs gm/Id ──
        mask2 = np.isfinite(gmid) & (id_w > 1e-6) & (gmid >= 4) & (gmid <= 24)
        ax01.semilogy(gmid[mask2], id_w[mask2], color=c, ls=ls, lw=2.0, label=lab)

        # ── (1,0) fT vs gm/Id ──
        mask3 = np.isfinite(ft) & (ft > 1e8) & np.isfinite(gmid) & (gmid >= 4) & (gmid <= 24)
        ax10.plot(gmid[mask3], ft[mask3]/1e9, color=c, ls=ls, lw=2.0, label=lab)

    # ── (1,1) gm*ro vs gm/Id  (gds from VDS output-curve sweeps) ──
    # vds_list holds VDS output sweeps (run_vds_sweeps / run_vsd_sweeps),
    # one list per curve.  gds is extracted at the primary Vds via interpolation
    # over many Vgs bias points — numerically stable for HVT and long channel.
    if vds_list:
        from scipy.signal import medfilt
        for i, (vgs_res, vd_sweeps, lab) in enumerate(
                zip(sweep_list, vds_list, param_labels)):
            if not vgs_res or not vd_sweeps:
                continue
            r1   = vgs_res[0]
            c    = _COLORS_EXT[i % len(_COLORS_EXT)]
            ls   = _LSTYLE_EXT[i % len(_LSTYLE_EXT)]
            vds_ref = float(r1['vds'])
            gds  = _gds_at_vds(vd_sweeps, r1['vgs'], vds_ref, gm_arr=r1['gm'])
            gmro = medfilt(r1['gm'] / gds, kernel_size=5)
            gmid = r1['gmid']
            mask = (np.isfinite(gmro) & np.isfinite(gmid) &
                    (gmid >= 4) & (gmid <= 24) & (gmro > 0) & (gmro < 300))
            ax11_.plot(gmid[mask], gmro[mask], color=c, ls=ls, lw=2.0, label=lab)

    # Reference lines for panel (0,0)
    ax00.axhline(1.0/0.02585, color=REF_C, ls=':', lw=1.2, label='BJT $q/kT$')
    vov_ref = np.linspace(0.005, 0.4, 200)
    ax00.plot(vov_ref, 2.0/vov_ref, color=REF_C, ls='--', lw=1.2, label='$2/V_{OV}$')
    ax00.axvline(0.0, color=REF_C, ls=':', lw=1.0, alpha=0.6)

    _gmid_ticks = list(range(4, 25, 2))

    ax00.set_xlabel(lbl['vov']);            ax00.set_ylabel('$g_m / I_D$  [V$^{-1}$]')
    ax00.set_xlim(-0.4, 0.6);              ax00.set_ylim(0, 42)
    ax00.set_title('$g_m/I_D$ vs $V_{OV}$')
    ax00.legend()

    ax01.set_xlabel('$g_m / I_D$  [V$^{-1}$]');  ax01.set_ylabel(lbl['id_lbl'])
    ax01.set_xlim(4, 24);  ax01.set_xticks(_gmid_ticks)
    ax01.set_title('Current Density vs $g_m/I_D$')
    ax01.legend()

    ax10.set_xlabel('$g_m / I_D$  [V$^{-1}$]');  ax10.set_ylabel('$f_T$  [GHz]')
    ax10.set_xlim(4, 24);  ax10.set_xticks(_gmid_ticks);  ax10.set_ylim(bottom=0)
    ax10.set_title('Transit Frequency vs $g_m/I_D$')
    ax10.legend()

    ax11_.set_xlabel('$g_m / I_D$  [V$^{-1}$]');  ax11_.set_ylabel('Intrinsic Gain  $g_m r_o$')
    ax11_.set_xlim(4, 24);  ax11_.set_xticks(_gmid_ticks);  ax11_.set_ylim(bottom=0)
    ax11_.set_title('Intrinsic Gain vs $g_m/I_D$')
    ax11_.legend()

    fig.suptitle(title, fontsize=13, y=1.01)
    plt.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f'  Saved -> {out_path}')
    return out_path


# ─────────────────────────────────────────────────────────────────────────────
# Gate capacitance plot
# ─────────────────────────────────────────────────────────────────────────────
def plot_caps(w_um, l_um, model='nmos180', vds_fixed=0.2, out_path=None):
    info    = MODEL_INFO[model]
    pol     = info['pol']
    vdd     = info.get('vdd', VDD)
    mp      = _parse_lib_params(str(info['file']), info['model_name'])
    tox     = mp.get('tox',  4.1e-9)
    vth0    = mp.get('vth0', 0.40)
    cgso    = mp.get('cgso', 7.9e-10)
    cgdo    = mp.get('cgdo', 7.9e-10)
    nch     = mp.get('nch',  2.35e17) * 1e6

    vgs = np.linspace(0, vdd, 500)
    cgs, cgd, cgb, cgg = compute_caps(vgs, vds_fixed, w_um, l_um,
                                       vth=vth0,
                                       cgso=cgso, cgdo=cgdo,
                                       nch=nch, tox=tox)

    fig, ax = plt.subplots(figsize=(7, 5))
    for (y, ls, lbl_), c in zip(
            [(cgg*1e15,'solid','$C_{gg}$'), (cgs*1e15,'dashed','$C_{gs}$'),
             (cgd*1e15,'dashdot','$C_{gd}$'), (cgb*1e15,'dotted','$C_{gb}$')],
            COLORS):
        ax.plot(vgs, y, color=c, ls=ls, lw=1.8, label=lbl_)

    vg_lbl = '|$V_{SG}$|' if pol == 'pmos' else '$V_{GS}$'
    ax.set_xlabel(f'{vg_lbl} [V]')
    ax.set_ylabel('Capacitance [fF]')
    ax.set_xlim(0, vdd);  ax.set_ylim(bottom=0)
    ax.axvline(vth0, color=REF_C, ls=':', lw=1.0, alpha=0.7)
    pol_str = 'NMOS' if pol == 'nmos' else 'PMOS'
    vth_tag = model.split('_')[-1].upper() if '_' in model else 'SVT'
    ax.set_title(f'{pol_str} Gate Caps  (W/L={w_um:.0f}/{l_um:.2f}, '
                 f'{vth_tag}, $V_{{DS}}$={vds_fixed}V)')
    ax.legend()
    plt.tight_layout()

    if out_path is None:
        out_path = PLOT_DIR / f'gmoverid_caps_{model}_L{l_um*1000:.0f}nm.png'
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f'  Saved -> {out_path}')
    return out_path


# ─────────────────────────────────────────────────────────────────────────────
# Combined caps comparison: 2×2 panel, one subplot per technology node
# ─────────────────────────────────────────────────────────────────────────────
def plot_caps_comparison(node_configs, polarity='nmos', out_path=None):
    """
    Parameters
    ----------
    node_configs : list of (model, w_um, l_um) tuples, up to 4 entries.
    polarity     : 'nmos' | 'pmos'  — used only for axis labels/title.
    out_path     : output PNG path.
    """
    fig, axes = plt.subplots(2, 2, figsize=(12, 9))
    axes_flat = axes.flat

    for ax, (model, w_um, l_um) in zip(axes_flat, node_configs[:4]):
        info  = MODEL_INFO[model]
        pol   = info['pol']
        vdd   = info.get('vdd', VDD)
        mp    = _parse_lib_params(str(info['file']), info['model_name'])
        tox   = mp.get('tox',  4.1e-9)
        vth0  = mp.get('vth0', 0.40)
        cgso  = mp.get('cgso', 7.9e-10)
        cgdo  = mp.get('cgdo', 7.9e-10)
        nch   = mp.get('nch',  2.35e17) * 1e6
        vds_fixed = vdd * 0.3

        vgs = np.linspace(0, vdd, 500)
        cgs, cgd, cgb, cgg = compute_caps(vgs, vds_fixed, w_um, l_um,
                                           vth=vth0,
                                           cgso=cgso, cgdo=cgdo,
                                           nch=nch, tox=tox)

        for (y, ls, lbl_), c in zip(
                [(cgg*1e15, 'solid',  '$C_{gg}$'),
                 (cgs*1e15, 'dashed', '$C_{gs}$'),
                 (cgd*1e15, 'dashdot','$C_{gd}$'),
                 (cgb*1e15, 'dotted', '$C_{gb}$')],
                COLORS):
            ax.plot(vgs, y, color=c, ls=ls, lw=1.8, label=lbl_)

        vg_lbl = '|$V_{SG}$|' if pol == 'pmos' else '$V_{GS}$'
        ax.set_xlabel(f'{vg_lbl} [V]')
        ax.set_ylabel('Capacitance [fF]')
        ax.set_xlim(0, vdd);  ax.set_ylim(bottom=0)
        ax.axvline(vth0, color=REF_C, ls=':', lw=1.0, alpha=0.7)

        node_tag = (model.replace('nmos', '').replace('pmos', '')
                         .replace('hp', ' HP').strip())
        ax.set_title(f'{node_tag}  VDD={vdd:.1f}V  (W/L={w_um:.0f}/{l_um:.3f})')
        ax.legend(fontsize=8)

    pol_str = 'NMOS' if polarity == 'nmos' else 'PMOS'
    fig.suptitle(f'{pol_str} Gate Capacitances — Node Comparison  (PTM HP, T=27°C)',
                 fontsize=13, y=1.01)
    plt.tight_layout()

    if out_path is None:
        out_path = PLOT_DIR / f'gmid_{polarity}_caps_comp.png'
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f'  Saved -> {out_path}')
    return out_path


# ─────────────────────────────────────────────────────────────────────────────
# 4-panel IV characteristics figure
# ─────────────────────────────────────────────────────────────────────────────
def plot_iv(vgs_results, vds_iv_results, w_um, l_um, w_iv_um=None,
            model='nmos180', out_path=None):
    """
    4-panel IV characteristics figure.

    Panel 1 (0,0): Id [µA] vs Vov  – linear y-axis
    Panel 2 (0,1): Id [µA] vs Vov  – log y-axis
    Panel 3 (1,0): Id [µA] vs Vgs  – full 0 → VDD sweep, linear
    Panel 4 (1,1): Id [µA] vs Vds  – output curves at fixed Vgs biases,
                                      device W = w_iv_um (default W/L=10)

    Parameters
    ----------
    vgs_results     : list of dicts from run_vgs_sweeps() / run_vsg_sweeps()
                      (multiple Vds/Vsd values; used for panels 1-3)
    vds_iv_results  : list of dicts from run_vds_sweeps() / run_vsd_sweeps()
                      at specific Vgs bias points (used for panel 4)
    w_um            : channel width for Vgs sweeps [µm]
    l_um            : channel length [µm]
    w_iv_um         : channel width for panel 4 output curves [µm]
    model           : model name string
    out_path        : output PNG path
    """
    info    = MODEL_INFO[model]
    pol     = info['pol']
    lbl     = _pol_labels(pol)
    vdd     = info.get('vdd', VDD)
    vds_stop= info.get('vds_stop', VDS_STOP)
    if w_iv_um is None:
        w_iv_um = w_um

    fig, axes = plt.subplots(2, 2, figsize=(12, 9))
    (ax00, ax01, ax10, ax11_) = axes.flat

    # ── Panels 1, 2, 3: from Vgs/Vsg sweeps ──
    for i, r in enumerate(vgs_results):
        c, ls    = COLORS[i % 4], LSTYLE[i % 4]
        vov      = r['vov']
        id_ua    = r['id'] * 1e6          # A → µA
        vgs      = r['vgs']
        bias_lbl = f'{lbl["vds_pfx"]}{r["vds"]:.2f}V'

        # (0,0) linear Id vs Vov
        mask1 = np.isfinite(id_ua) & (vov > -0.4) & (vov < 0.6)
        ax00.plot(vov[mask1], id_ua[mask1], color=c, ls=ls, lw=1.8, label=bias_lbl)

        # (0,1) log Id vs Vov
        mask2 = (id_ua > 1e-4) & (vov > -0.4) & (vov < 0.6)
        ax01.semilogy(vov[mask2], id_ua[mask2], color=c, ls=ls, lw=1.8,
                      label=bias_lbl)

        # (1,0) linear Id vs Vgs full sweep
        mask3 = np.isfinite(id_ua) & (vgs >= 0) & (vgs <= vdd + 0.01)
        ax10.plot(vgs[mask3], id_ua[mask3], color=c, ls=ls, lw=1.8, label=bias_lbl)

    # Build Vds annotation string for panel titles
    _vd_short  = '|$V_{SD}$|' if pol == 'pmos' else '$V_{DS}$'
    _vds_vals  = ', '.join(f'{r["vds"]:.1f}' for r in vgs_results)
    _vds_annot = f'{_vd_short} = {_vds_vals} V'

    ax00.axvline(0.0, color=REF_C, ls=':', lw=1.0, alpha=0.7)
    ax00.set_xlabel(lbl['vov'])
    ax00.set_ylabel('$I_D$  [$\\mu$A]')
    ax00.set_xlim(-0.4, 0.6)
    ax00.set_ylim(bottom=0)
    ax00.set_title(f'$I_D$ vs $V_{{OV}}$ (linear)\n{_vds_annot}', fontsize=10)
    ax00.legend(fontsize=8)

    ax01.axvline(0.0, color=REF_C, ls=':', lw=1.0, alpha=0.7)
    ax01.set_xlabel(lbl['vov'])
    ax01.set_ylabel('$I_D$  [$\\mu$A]')
    ax01.set_xlim(-0.4, 0.6)
    ax01.set_title(f'$I_D$ vs $V_{{OV}}$ (log scale)\n{_vds_annot}', fontsize=10)
    ax01.legend(fontsize=8)

    ax10.set_xlabel(lbl['vg'])
    ax10.set_ylabel('$I_D$  [$\\mu$A]')
    ax10.set_xlim(0, vdd)
    ax10.set_ylim(bottom=0)
    ax10.set_title(f'$I_D$ vs $V_{{GS}}$ (W={w_um:.0f}$\\mu$m)\n{_vds_annot}', fontsize=10)
    ax10.legend(fontsize=8)

    # ── Panel 4: output characteristics ──
    for i, r in enumerate(vds_iv_results):
        c, ls = _COLORS_EXT[i % len(_COLORS_EXT)], _LSTYLE_EXT[i % len(_LSTYLE_EXT)]
        vds_p = r['vds']
        id_ua = r['id'] * 1e6             # A → µA
        vgs_b = r['vgs']
        mask  = np.isfinite(id_ua) & (vds_p >= 0) & (vds_p <= vds_stop + 0.01)
        ax11_.plot(vds_p[mask], id_ua[mask], color=c, ls=ls, lw=1.8,
                   label=f'{lbl["bias_prefix"]}{vgs_b:.1f}V')

    wl = w_iv_um / l_um
    ax11_.set_xlabel(lbl['vd'])
    ax11_.set_ylabel('$I_D$  [$\\mu$A]')
    ax11_.set_xlim(0, vds_stop)
    ax11_.set_ylim(bottom=0)
    ax11_.set_title(f'Output Characteristics  (W/L={wl:.0f}, L={l_um*1000:.0f}nm)')
    ax11_.legend(fontsize=8)

    pol_str = 'NMOS' if pol == 'nmos' else 'PMOS'
    node_str = model.replace('nmos', '').replace('pmos', '').replace('_', ' ').strip().upper() or 'SVT'
    fig.suptitle(
        f'{pol_str} IV Characteristics  ({node_str}, T=27$\\degree$C)',
        fontsize=13, y=1.01)
    plt.tight_layout()

    if out_path is None:
        out_path = PLOT_DIR / f'gmoverid_iv_{model}_L{l_um*1000:.0f}nm.png'
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f'  Saved -> {out_path}')
    return out_path


# ─────────────────────────────────────────────────────────────────────────────
# Summary table
# ─────────────────────────────────────────────────────────────────────────────
def print_summary(vgs_results, vds_results, model='nmos180'):
    info  = MODEL_INFO[model]
    pol   = info['pol']
    vdd   = info.get('vdd', VDD)
    # Pick the sweep closest to 0.5*VDD as the representative bias
    vds_rep = vdd * 0.5
    r_rep = next((r for r in vgs_results if abs(r['vds'] - vds_rep) < vdd * 0.2),
                 vgs_results[-1] if vgs_results else None)
    if r_rep is None:
        return

    vg_lbl = '|Vsg|/V' if pol == 'pmos' else 'Vgs/V'
    vd_lbl = '|Vsd|' if pol == 'pmos' else 'Vds'
    vd_str = f'{vd_lbl}={r_rep["vds"]:.2f}V'

    print()
    print(f'  Vth (extracted) = {r_rep["vth"]:.3f} V  [{model}]')
    print()
    print(f'  gm/Id Table  ({vd_str},  VDD={vdd:.1f}V)')
    print('  ' + '-'*72)
    print(f'  {vg_lbl:>7}  {"Vov/V":>6}  {"Id/uA":>8}  {"gm/mS":>8}'
          f'  {"gm/Id":>8}  {"ft/GHz":>8}  {"gm*ro":>8}')
    print('  ' + '-'*72)

    # Generate Vgs sample points evenly spaced over [0.2*vdd, vdd]
    vg_pts = np.linspace(0.2 * vdd, vdd, 9)
    for vg in vg_pts:
        idx  = np.argmin(np.abs(r_rep['vgs'] - vg))
        id_  = r_rep['id'][idx]
        gm_  = r_rep['gm'][idx]
        gmid = r_rep['gmid'][idx]
        ft_  = r_rep['ft'][idx]
        vov  = r_rep['vov'][idx]

        rds = None
        for rv in vds_results:
            if abs(rv['vgs'] - vg) < vdd * 0.12:
                idx2 = np.argmin(np.abs(rv['vds'] - vds_rep))
                rds  = rv['ro'][idx2]
                break
        gain_str = f'{gm_*rds:.1f}' if (rds and np.isfinite(gm_*rds)) else ' n/a'
        gmid_s   = f'{gmid:.2f}'    if np.isfinite(gmid) else ' n/a'
        ft_s     = f'{ft_/1e9:.2f}' if np.isfinite(ft_) else ' n/a'

        print(f'  {vg:>7.3f}  {vov:>6.3f}  {id_*1e6:>8.3f}  {gm_*1e3:>8.4f}'
              f'  {gmid_s:>8}  {ft_s:>8}  {gain_str:>8}')
    print('  ' + '-'*72)
    print()
