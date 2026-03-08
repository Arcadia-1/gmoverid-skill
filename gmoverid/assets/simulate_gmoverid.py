#!/usr/bin/env python3
"""
simulate_gmoverid.py
====================
Simulation engine for gm/Id characterization.
Supports PTM 180nm BSIM3v3 and PTM 45/32/22/16nm HP BSIM4 models.

Public API
----------
sweep_vgs(vds, w_um, l_um, model)      -> dict  (NMOS Vgs sweep at fixed Vds)
sweep_vds(vgs_bias, w_um, l_um, model) -> dict  (NMOS Vds sweep at fixed Vgs)
sweep_vsg(vsd, w_um, l_um, model)      -> dict  (PMOS |Vsg| sweep at fixed |Vsd|)
sweep_vsd(vsg_bias, w_um, l_um, model) -> dict  (PMOS |Vsd| sweep at fixed |Vsg|)

run_vgs_sweeps(w_um, l_um, model)      -> list[dict]
run_vds_sweeps(w_um, l_um, model)      -> list[dict]
run_vsg_sweeps(w_um, l_um, model)      -> list[dict]
run_vsd_sweeps(w_um, l_um, model)      -> list[dict]

Return dict keys (unified NMOS/PMOS convention, all values positive):
  vds, vgs, id, gm, cgs, cgd, cgb, cgg, gmid, ft, id_w, vov, vth, model
  For PMOS: vgs = |Vsg|, vds = |Vsd|, vov = |Vsg| - |Vth|
"""

import subprocess, sys, re, shutil
import numpy as np
from pathlib import Path

# ─────────────────────────────────────────────────────────────────────────────
# Paths  (all relative to this script's directory — no hardcoded absolute paths)
# ─────────────────────────────────────────────────────────────────────────────
BASE_DIR        = Path(__file__).resolve().parent
MODEL_FILE_NMOS = BASE_DIR / 'models' / 'nmos180.lib'
MODEL_FILE_PMOS = BASE_DIR / 'models' / 'pmos180.lib'
TMPL_VGS        = BASE_DIR / 'netlist' / 'gmoverid_vgs.cir.tmpl'
TMPL_VDS        = BASE_DIR / 'netlist' / 'gmoverid_vds.cir.tmpl'
TMPL_VSG        = BASE_DIR / 'netlist' / 'gmoverid_pmos_vsg.cir.tmpl'
TMPL_VSD_P      = BASE_DIR / 'netlist' / 'gmoverid_pmos_vsd.cir.tmpl'
PLOT_DIR        = BASE_DIR / 'plots'
LOG_DIR         = BASE_DIR / 'logs'
for _d in (PLOT_DIR, LOG_DIR):
    _d.mkdir(parents=True, exist_ok=True)

def _mf(name):
    """Return Path to a model file in models/."""
    return BASE_DIR / 'models' / name

# ─────────────────────────────────────────────────────────────────────────────
# Model registry
# Each entry may include optional per-model overrides:
#   vdd      : supply voltage [V]  (default: 1.8)
#   vgs_stop : max Vgs for sweep  (default: 1.8)
#   vds_stop : max Vds for sweep  (default: 1.8)
#   tox      : gate oxide thickness [m]  (default: 4.1e-9)
# ─────────────────────────────────────────────────────────────────────────────
MODEL_INFO = {
    # ── 180nm BSIM3v3 (PTM) ─────────────────────────────────────────────────
    'nmos180':     dict(pol='nmos', vth0=0.40,  cgso=7.9e-10, cgdo=7.9e-10,
                        nch=2.3549e17*1e6, mu=270e-4, file=_mf('nmos180.lib'),
                        vdd=1.8, vgs_stop=1.8, vds_stop=1.8, tox=4.1e-9),
    'nmos180_lvt': dict(pol='nmos', vth0=0.30,  cgso=7.9e-10, cgdo=7.9e-10,
                        nch=2.3549e17*1e6, mu=270e-4, file=_mf('nmos180.lib'),
                        vdd=1.8, vgs_stop=1.8, vds_stop=1.8, tox=4.1e-9),
    'nmos180_hvt': dict(pol='nmos', vth0=0.55,  cgso=7.9e-10, cgdo=7.9e-10,
                        nch=2.3549e17*1e6, mu=270e-4, file=_mf('nmos180.lib'),
                        vdd=1.8, vgs_stop=1.8, vds_stop=1.8, tox=4.1e-9),
    'pmos180':     dict(pol='pmos', vth0=0.42,  cgso=6.8e-10, cgdo=6.8e-10,
                        nch=6.0165e16*1e6, mu=117.5e-4, file=_mf('pmos180.lib'),
                        vdd=1.8, vgs_stop=1.8, vds_stop=1.8, tox=4.1e-9),
    'pmos180_lvt': dict(pol='pmos', vth0=0.32,  cgso=6.8e-10, cgdo=6.8e-10,
                        nch=6.0165e16*1e6, mu=117.5e-4, file=_mf('pmos180.lib'),
                        vdd=1.8, vgs_stop=1.8, vds_stop=1.8, tox=4.1e-9),
    'pmos180_hvt': dict(pol='pmos', vth0=0.57,  cgso=6.8e-10, cgdo=6.8e-10,
                        nch=6.0165e16*1e6, mu=117.5e-4, file=_mf('pmos180.lib'),
                        vdd=1.8, vgs_stop=1.8, vds_stop=1.8, tox=4.1e-9),
    # ── 45nm HP BSIM4 (PTM) — VDD = 1.0 V ──────────────────────────────────
    'nmos45hp':    dict(pol='nmos', vth0=0.469, cgso=1.1e-10, cgdo=1.1e-10,
                        nch=3.24e18*1e6, mu=0.054, file=_mf('nmos45hp.lib'),
                        vdd=1.0, vgs_stop=1.2, vds_stop=1.2, tox=1.25e-9),
    'pmos45hp':    dict(pol='pmos', vth0=0.492, cgso=1.1e-10, cgdo=1.1e-10,
                        nch=2.44e18*1e6, mu=0.020, file=_mf('pmos45hp.lib'),
                        vdd=1.0, vgs_stop=1.2, vds_stop=1.2, tox=1.3e-9),
    # ── 32nm HP BSIM4 (PTM) — VDD = 0.9 V ──────────────────────────────────
    'nmos32hp':    dict(pol='nmos', vth0=0.494, cgso=8.5e-11, cgdo=8.5e-11,
                        nch=4.12e18*1e6, mu=0.050, file=_mf('nmos32hp.lib'),
                        vdd=0.9, vgs_stop=1.1, vds_stop=1.1, tox=1.15e-9),
    'pmos32hp':    dict(pol='pmos', vth0=0.492, cgso=8.5e-11, cgdo=8.5e-11,
                        nch=3.07e18*1e6, mu=0.014, file=_mf('pmos32hp.lib'),
                        vdd=0.9, vgs_stop=1.1, vds_stop=1.1, tox=1.2e-9),
    # ── 22nm HP BSIM4 (PTM) — VDD = 0.8 V ──────────────────────────────────
    'nmos22hp':    dict(pol='nmos', vth0=0.503, cgso=7.0e-11, cgdo=7.0e-11,
                        nch=5.02e18*1e6, mu=0.040, file=_mf('nmos22hp.lib'),
                        vdd=0.8, vgs_stop=1.0, vds_stop=1.0, tox=1.05e-9),
    'pmos22hp':    dict(pol='pmos', vth0=0.490, cgso=7.0e-11, cgdo=7.0e-11,
                        nch=3.70e18*1e6, mu=0.012, file=_mf('pmos22hp.lib'),
                        vdd=0.8, vgs_stop=1.0, vds_stop=1.0, tox=1.1e-9),
    # ── 16nm HP BSIM4 (PTM) — VDD = 0.7 V ──────────────────────────────────
    'nmos16hp':    dict(pol='nmos', vth0=0.480, cgso=6.0e-11, cgdo=6.0e-11,
                        nch=6.00e18*1e6, mu=0.030, file=_mf('nmos16hp.lib'),
                        vdd=0.7, vgs_stop=0.9, vds_stop=0.9, tox=9.5e-10),
    'pmos16hp':    dict(pol='pmos', vth0=0.480, cgso=6.0e-11, cgdo=6.0e-11,
                        nch=4.50e18*1e6, mu=0.010, file=_mf('pmos16hp.lib'),
                        vdd=0.7, vgs_stop=0.9, vds_stop=0.9, tox=1.05e-9),
}

# ─────────────────────────────────────────────────────────────────────────────
# Device defaults & sweep ranges  (180nm defaults; overridden per-model below)
# ─────────────────────────────────────────────────────────────────────────────
W_UM = 10.0
L_UM =  0.18
VDD  =  1.8

VGS_START = 0.0
VGS_STOP  = 1.8
VGS_STEP  = 0.002     # 2 mV -> 900 points

VDS_START = 0.0
VDS_STOP  = 1.8
VDS_STEP  = 0.002

VDS_LIST  = [0.1, 0.5, 0.9, 1.8]      # Vgs-sweep: multiple Vds values
VGS_BIAS  = [0.5, 0.6, 0.8, 1.0]      # Vds-sweep: multiple Vgs bias points

COX = 8.854e-12 * 3.9 / 4.1e-9        # ~8.42 mF/m²  (TOX = 4.1 nm, 180nm default)

def _cox(tox):
    """Oxide capacitance [F/m²] from physical oxide thickness."""
    return 8.854e-12 * 3.9 / tox

# ─────────────────────────────────────────────────────────────────────────────
# Utilities
# ─────────────────────────────────────────────────────────────────────────────
def _strip_ansi(t):
    return re.sub(r'\x1b\[[0-9;]*m', '', t)

def _run(args, timeout=120):
    kw = dict(args=args, capture_output=True, text=True,
              timeout=timeout, stdin=subprocess.DEVNULL)
    if sys.platform == 'win32':
        kw['creationflags'] = subprocess.CREATE_NO_WINDOW
    r = subprocess.run(**kw)
    return r.returncode, _strip_ansi((r.stdout + r.stderr).strip())

def _ngspice():
    for exe in ('ngspice_con', 'ngspice'):
        if shutil.which(exe):
            return exe
    raise RuntimeError('ngspice not found in PATH')

def _spath(p):
    return str(p).replace('\\', '/')

def _parse_wrdata_2vec(path):
    """
    Parse wrdata output (4 columns):
      col0 = sweep variable  col1 = v(x)  col2 = sweep variable  col3 = i(src)
    Returns (x, i) as 1-D numpy arrays.
    """
    rows = []
    with open(path, encoding='utf-8', errors='replace') as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                float(line.split()[0])
            except (ValueError, IndexError):
                continue
            v = []
            for tok in line.split():
                try:
                    v.append(float(tok))
                except ValueError:
                    v.append(0.0)
            if len(v) >= 4:
                rows.append(v[:4])
    if not rows:
        raise RuntimeError(f'No data in {path}')
    a = np.array(rows)
    return a[:, 0], a[:, 3]


# ─────────────────────────────────────────────────────────────────────────────
# Analytical capacitances (BSIM3v3 piecewise model)
# ─────────────────────────────────────────────────────────────────────────────
def compute_caps(vgs_arr, vds_fixed, w_um, l_um, vth=None,
                 cgso=7.9e-10, cgdo=7.9e-10, nch=2.3549e17*1e6, tox=4.1e-9):
    """
    Cgs, Cgd, Cgb, Cgg vs Vgs (or |Vsg| for PMOS) analytically.
    Works for both NMOS and PMOS when called with absolute overdrive values.

    Parameters
    ----------
    vgs_arr    : Vgs array (NMOS) or |Vsg| array (PMOS)
    vds_fixed  : Vds (NMOS) or |Vsd| (PMOS)
    vth        : threshold voltage magnitude (extracted from sim or model nominal)
    cgso/cgdo  : overlap caps [F/m] (device-specific)
    nch        : body doping [m^-3] (for depletion cap)
    tox        : gate oxide thickness [m] (for per-node COX)
    """
    if vth is None:
        vth = 0.40   # fallback

    W       = w_um * 1e-6
    L       = l_um * 1e-6
    cox_i   = _cox(tox) * W * L
    cov_s   = cgso * W
    cov_d   = cgdo * W

    eps_si  = 11.7 * 8.854e-12
    phi_f   = 0.02585 * np.log(max(nch, 1e15) / 1.45e16)
    W_dep   = np.sqrt(2 * eps_si * max(2 * phi_f, 0.3) / (1.6e-19 * max(nch, 1e15)))
    Cdep_a  = eps_si / W_dep
    cox_val = _cox(tox)
    cgb_dep = cox_val * Cdep_a / (cox_val + Cdep_a) * W * L

    def _sig(x, x0, w):
        return 1.0 / (1.0 + np.exp(np.clip(-(x - x0) / w, -50, 50)))

    inv_on  = _sig(vgs_arr, vth, 0.05)
    inv_lin = _sig(vgs_arr - vth - vds_fixed, 0.0, 0.04)

    cgs_on  = ((2.0/3.0)*cox_i + cov_s) + inv_lin*(0.5*cox_i + cov_s - ((2.0/3.0)*cox_i + cov_s))
    cgd_on  = cov_d               + inv_lin*(0.5*cox_i + cov_d - cov_d)

    cgs = cov_s + inv_on * (cgs_on - cov_s)
    cgd = cov_d + inv_on * (cgd_on - cov_d)
    cgb = cgb_dep * (1.0 - inv_on)
    cgg = cgs + cgd + cgb
    return cgs, cgd, cgb, cgg


# ─────────────────────────────────────────────────────────────────────────────
# Vth extraction (constant-current method)
# ─────────────────────────────────────────────────────────────────────────────
def extract_vth(vgs, id_arr, w_um, l_um, id_ref_norm=1e-7):
    """Vgs (or |Vsg|) where Id/(W/L) = id_ref_norm. Falls back to 0.40 V."""
    wl   = w_um / l_um
    inrm = id_arr / wl
    if np.max(inrm) < id_ref_norm:
        return 0.40
    idx = np.searchsorted(inrm, id_ref_norm)
    if idx == 0:
        return 0.40
    vth = np.interp(id_ref_norm,
                    inrm[max(0, idx-1):idx+2],
                    vgs [max(0, idx-1):idx+2])
    return float(np.clip(vth, 0.05, 1.0))


# ─────────────────────────────────────────────────────────────────────────────
# NMOS Vgs sweep
# ─────────────────────────────────────────────────────────────────────────────
def sweep_vgs(vds, w_um=W_UM, l_um=L_UM, model='nmos180'):
    info     = MODEL_INFO[model]
    vgs_stop = info.get('vgs_stop', VGS_STOP)
    tox      = info.get('tox', 4.1e-9)
    tmpl     = TMPL_VGS.read_text(encoding='ascii')
    tag      = f'{model}_L{l_um*1000:.0f}nm_vds{vds:.2f}'.replace('.', 'p')
    cir      = LOG_DIR / f'_vgs_{tag}.cir'
    dat      = LOG_DIR / f'_vgs_{tag}.dat'
    log      = LOG_DIR / f'_vgs_{tag}.log'
    if dat.exists():
        dat.unlink()

    nl = tmpl.format(
        model_path=_spath(info['file']), model=model,
        vds_v=f'{vds:.4f}', w_um=f'{w_um:.4f}', l_um=f'{l_um:.4f}',
        vgs_start=f'{VGS_START:.3f}', vgs_stop=f'{vgs_stop:.3f}',
        vgs_step=f'{VGS_STEP:.5f}', dat_path=_spath(dat),
    )
    cir.write_text(nl, encoding='ascii')

    rc, out = _run([_ngspice(), '-b', '-o', _spath(log), _spath(cir)])
    if not dat.exists():
        lt = log.read_text(encoding='utf-8', errors='replace') if log.exists() else ''
        raise RuntimeError(f'ngspice failed (model={model} Vds={vds}V):\n'
                           + '\n'.join((out+'\n'+lt).splitlines()[:30]))

    vgs, icur = _parse_wrdata_2vec(dat)
    id_  = np.maximum(-icur, 0.0)
    gm   = np.maximum(np.gradient(id_, vgs), 0.0)

    vth  = extract_vth(vgs, id_, w_um, l_um)
    cgs, cgd, cgb, cgg = compute_caps(vgs, vds, w_um, l_um, vth=vth,
                                       cgso=info['cgso'], cgdo=info['cgdo'],
                                       nch=info['nch'], tox=tox)
    id_thresh = 1e-13
    gmid = np.where(id_ > id_thresh, gm / id_, np.nan)
    ft   = np.where(cgg > 0, gm / (2.0 * np.pi * cgg), np.nan)
    id_w = id_ / (w_um * 1e-6)
    vov  = vgs - vth

    return dict(model=model, pol='nmos', vds=vds, vgs=vgs,
                id=id_, gm=gm, cgs=cgs, cgd=cgd, cgb=cgb, cgg=cgg,
                gmid=gmid, ft=ft, id_w=id_w, vov=vov, vth=vth)


# ─────────────────────────────────────────────────────────────────────────────
# NMOS Vds sweep
# ─────────────────────────────────────────────────────────────────────────────
def sweep_vds(vgs_bias, w_um=W_UM, l_um=L_UM, model='nmos180'):
    info     = MODEL_INFO[model]
    vds_stop = info.get('vds_stop', VDS_STOP)
    tmpl = TMPL_VDS.read_text(encoding='ascii')
    tag  = f'{model}_L{l_um*1000:.0f}nm_vgs{vgs_bias:.2f}'.replace('.', 'p')
    cir  = LOG_DIR / f'_vds_{tag}.cir'
    dat  = LOG_DIR / f'_vds_{tag}.dat'
    log  = LOG_DIR / f'_vds_{tag}.log'
    if dat.exists():
        dat.unlink()

    nl = tmpl.format(
        model_path=_spath(info['file']), model=model,
        vgs_v=f'{vgs_bias:.4f}', w_um=f'{w_um:.4f}', l_um=f'{l_um:.4f}',
        vds_start=f'{VDS_START:.3f}', vds_stop=f'{vds_stop:.3f}',
        vds_step=f'{VDS_STEP:.5f}', dat_path=_spath(dat),
    )
    cir.write_text(nl, encoding='ascii')

    rc, out = _run([_ngspice(), '-b', '-o', _spath(log), _spath(cir)])
    if not dat.exists():
        lt = log.read_text(encoding='utf-8', errors='replace') if log.exists() else ''
        raise RuntimeError(f'ngspice failed (model={model} Vgs={vgs_bias}V):\n'
                           + '\n'.join((out+'\n'+lt).splitlines()[:30]))

    vds, icur = _parse_wrdata_2vec(dat)
    id_  = np.maximum(-icur, 0.0)
    gds  = np.maximum(np.gradient(id_, vds), 1e-12)
    ro   = 1.0 / gds

    return dict(model=model, pol='nmos', vgs=vgs_bias, vds=vds, id=id_, gds=gds, ro=ro)


# ─────────────────────────────────────────────────────────────────────────────
# PMOS |Vsg| sweep
# ─────────────────────────────────────────────────────────────────────────────
def sweep_vsg(vsd, w_um=W_UM, l_um=L_UM, model='pmos180'):
    """
    PMOS |Vsg| sweep at fixed |Vsd|.
    Returns same dict format as sweep_vgs() for unified plotting:
      vgs = |Vsg|, vds = |Vsd|, vov = |Vsg| - |Vth|
    """
    info     = MODEL_INFO[model]
    vdd      = info.get('vdd', VDD)
    tox      = info.get('tox', 4.1e-9)
    tmpl     = TMPL_VSG.read_text(encoding='ascii')
    tag      = f'{model}_L{l_um*1000:.0f}nm_vsd{vsd:.2f}'.replace('.', 'p')
    cir      = LOG_DIR / f'_vsg_{tag}.cir'
    dat      = LOG_DIR / f'_vsg_{tag}.dat'
    log      = LOG_DIR / f'_vsg_{tag}.log'
    if dat.exists():
        dat.unlink()

    vd_v = vdd - vsd          # absolute drain voltage = VDD - |Vsd|

    nl = tmpl.format(
        model_path=_spath(info['file']), model=model,
        vdd_v=f'{vdd:.4f}', vd_v=f'{vd_v:.4f}',
        w_um=f'{w_um:.4f}', l_um=f'{l_um:.4f}',
        vg_start=f'{vdd:.3f}', vg_stop='0.000', vg_step=f'{-VGS_STEP:.5f}',
        dat_path=_spath(dat),
    )
    cir.write_text(nl, encoding='ascii')

    rc, out = _run([_ngspice(), '-b', '-o', _spath(log), _spath(cir)])
    if not dat.exists():
        lt = log.read_text(encoding='utf-8', errors='replace') if log.exists() else ''
        raise RuntimeError(f'ngspice failed (model={model} |Vsd|={vsd}V):\n'
                           + '\n'.join((out+'\n'+lt).splitlines()[:30]))

    # vg_abs sweeps from VDD to 0 → vsg = VDD - vg_abs sweeps from 0 to VDD
    vg_abs, icur = _parse_wrdata_2vec(dat)
    vsg  = vdd - vg_abs                  # |Vsg|, ascending 0 → VDD
    id_  = np.maximum(icur, 0.0)         # positive for PMOS

    # Ensure ascending order (should already be, but guard against edge cases)
    if vsg[0] > vsg[-1]:
        vsg  = vsg[::-1]
        id_  = id_[::-1]

    gm   = np.maximum(np.gradient(id_, vsg), 0.0)
    vth  = extract_vth(vsg, id_, w_um, l_um)
    cgs, cgd, cgb, cgg = compute_caps(vsg, vsd, w_um, l_um, vth=vth,
                                       cgso=info['cgso'], cgdo=info['cgdo'],
                                       nch=info['nch'], tox=tox)
    id_thresh = 1e-13
    gmid = np.where(id_ > id_thresh, gm / id_, np.nan)
    ft   = np.where(cgg > 0, gm / (2.0 * np.pi * cgg), np.nan)
    id_w = id_ / (w_um * 1e-6)
    vov  = vsg - vth

    return dict(model=model, pol='pmos', vds=vsd, vgs=vsg,
                id=id_, gm=gm, cgs=cgs, cgd=cgd, cgb=cgb, cgg=cgg,
                gmid=gmid, ft=ft, id_w=id_w, vov=vov, vth=vth)


# ─────────────────────────────────────────────────────────────────────────────
# PMOS |Vsd| sweep
# ─────────────────────────────────────────────────────────────────────────────
def sweep_vsd(vsg_bias, w_um=W_UM, l_um=L_UM, model='pmos180'):
    """
    PMOS |Vsd| sweep at fixed |Vsg|.
    Returns same dict format as sweep_vds().
    """
    info     = MODEL_INFO[model]
    vdd      = info.get('vdd', VDD)
    vds_stop = info.get('vds_stop', VDS_STOP)
    tmpl     = TMPL_VSD_P.read_text(encoding='ascii')
    tag      = f'{model}_L{l_um*1000:.0f}nm_vsg{vsg_bias:.2f}'.replace('.', 'p')
    cir      = LOG_DIR / f'_vsd_{tag}.cir'
    dat      = LOG_DIR / f'_vsd_{tag}.dat'
    log      = LOG_DIR / f'_vsd_{tag}.log'
    if dat.exists():
        dat.unlink()

    vg_v    = vdd - vsg_bias          # absolute gate voltage = VDD - |Vsg|
    vd_stop = vdd - vds_stop          # VD_min: negative when vds_stop > vdd

    nl = tmpl.format(
        model_path=_spath(info['file']), model=model,
        vdd_v=f'{vdd:.4f}', vg_v=f'{vg_v:.4f}',
        w_um=f'{w_um:.4f}', l_um=f'{l_um:.4f}',
        vd_start=f'{vdd:.4f}', vd_stop=f'{vd_stop:.4f}', vd_step=f'{-VDS_STEP:.5f}',
        dat_path=_spath(dat),
    )
    cir.write_text(nl, encoding='ascii')

    rc, out = _run([_ngspice(), '-b', '-o', _spath(log), _spath(cir)])
    if not dat.exists():
        lt = log.read_text(encoding='utf-8', errors='replace') if log.exists() else ''
        raise RuntimeError(f'ngspice failed (model={model} |Vsg|={vsg_bias}V):\n'
                           + '\n'.join((out+'\n'+lt).splitlines()[:30]))

    # vd_abs sweeps from VDD down to (VDD - vds_stop) → vsd = VDD - vd_abs from 0 to vds_stop
    vd_abs, icur = _parse_wrdata_2vec(dat)
    vsd  = vdd - vd_abs                  # |Vsd|, ascending
    id_  = np.maximum(icur, 0.0)

    if vsd[0] > vsd[-1]:
        vsd = vsd[::-1]
        id_ = id_[::-1]

    gds = np.maximum(np.gradient(id_, vsd), 1e-12)
    ro  = 1.0 / gds

    return dict(model=model, pol='pmos', vgs=vsg_bias, vds=vsd, id=id_, gds=gds, ro=ro)


# ─────────────────────────────────────────────────────────────────────────────
# Top-level runners
# ─────────────────────────────────────────────────────────────────────────────
def run_vgs_sweeps(w_um=W_UM, l_um=L_UM, model='nmos180', vds_list=None):
    if vds_list is None:
        vds_list = VDS_LIST
    results = []
    for vds in vds_list:
        print(f'  {model} L={l_um*1000:.0f}nm  Vgs sweep  Vds={vds:.1f}V ...',
              end='', flush=True)
        try:
            r = sweep_vgs(vds, w_um, l_um, model)
            results.append(r)
            print(f'  ok  Vth={r["vth"]:.3f}V  Id_max={r["id"].max()*1e3:.2f}mA')
        except RuntimeError as e:
            print(f'\n  [ERROR] {e}')
    return results


def run_vds_sweeps(w_um=W_UM, l_um=L_UM, model='nmos180', vgs_bias_list=None):
    if vgs_bias_list is None:
        vgs_bias_list = VGS_BIAS
    results = []
    for vgs in vgs_bias_list:
        print(f'  {model} L={l_um*1000:.0f}nm  Vds sweep  Vgs={vgs:.2f}V ...',
              end='', flush=True)
        try:
            r = sweep_vds(vgs, w_um, l_um, model)
            results.append(r)
            ro_mid = r['ro'][int(len(r['ro'])*0.6)]
            print(f'  ok  ro(mid)={ro_mid/1e3:.1f}kohm')
        except RuntimeError as e:
            print(f'\n  [ERROR] {e}')
    return results


def run_vsg_sweeps(w_um=W_UM, l_um=L_UM, model='pmos180', vsd_list=None):
    if vsd_list is None:
        vsd_list = VDS_LIST
    results = []
    for vsd in vsd_list:
        print(f'  {model} L={l_um*1000:.0f}nm  |Vsg| sweep  |Vsd|={vsd:.1f}V ...',
              end='', flush=True)
        try:
            r = sweep_vsg(vsd, w_um, l_um, model)
            results.append(r)
            print(f'  ok  |Vth|={r["vth"]:.3f}V  Id_max={r["id"].max()*1e3:.2f}mA')
        except RuntimeError as e:
            print(f'\n  [ERROR] {e}')
    return results


def run_vsd_sweeps(w_um=W_UM, l_um=L_UM, model='pmos180', vsg_bias_list=None):
    if vsg_bias_list is None:
        vsg_bias_list = VGS_BIAS
    results = []
    for vsg in vsg_bias_list:
        print(f'  {model} L={l_um*1000:.0f}nm  |Vsd| sweep  |Vsg|={vsg:.2f}V ...',
              end='', flush=True)
        try:
            r = sweep_vsd(vsg, w_um, l_um, model)
            results.append(r)
            ro_mid = r['ro'][int(len(r['ro'])*0.6)]
            print(f'  ok  ro(mid)={ro_mid/1e3:.1f}kohm')
        except RuntimeError as e:
            print(f'\n  [ERROR] {e}')
    return results
