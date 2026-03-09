#!/usr/bin/env python3
"""
design_gmoverid.py
==================
gm/ID design / sizing API.  Wraps simulation data from simulate_gmoverid.py
into a lookup-table object (GmIdTable) for transistor sizing.

Public API
----------
GmIdTable(model, W, L, vds=None, vgs_bias_list=None, force_resim=False)
    .lookup(qty, gmid)           -> float
    .size(gmid, Id=None, W=None, gm=None)   -> dict
    .size_from_ft(ft_target, Id=None, W=None)   -> dict
    .size_from_gmro(gmro_target, Id=None, W=None) -> dict
    .operating_range()           -> dict

print_op(op)   -> None   (pretty-print a sizing result dict)

Usage
-----
    from design_gmoverid import GmIdTable, print_op

    # First call: simulates and caches to logs/cache/
    tbl = GmIdTable('nmos180', W=10.0, L=0.18, vds=0.9)

    # Second call: loads from cache (fast)
    tbl2 = GmIdTable('nmos180', W=10.0, L=0.18, vds=0.9)

    op = tbl.size(gmid=15.0, Id=100e-6)
    print_op(op)   # W ~ 20 µm, Id = 100 µA
"""

import json
import hashlib
import numpy as np
from pathlib import Path

from simulate_gmoverid import (
    MODEL_INFO, LOG_DIR, _parse_lib_params,
    sweep_vgs, sweep_vsg,
    run_vds_sweeps, run_vsd_sweeps,
)

# ─────────────────────────────────────────────────────────────────────────────
# Cache directory
# ─────────────────────────────────────────────────────────────────────────────
CACHE_DIR = LOG_DIR / 'cache'
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Keys that hold numpy arrays (for JSON round-trip reconstruction)
_ARRAY_KEYS = {
    'vgs', 'vds', 'id', 'gm', 'cgs', 'cgd', 'cgb', 'cgg',
    'gmid', 'ft', 'id_w', 'vov', 'gds', 'ro',
}


# ─────────────────────────────────────────────────────────────────────────────
# JSON cache helpers
# ─────────────────────────────────────────────────────────────────────────────
def _arr_to_list(obj):
    """Recursively convert numpy arrays → lists for JSON serialisation."""
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, dict):
        return {k: _arr_to_list(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_arr_to_list(v) for v in obj]
    if isinstance(obj, (np.floating, np.integer)):
        return obj.item()
    return obj


def _list_to_arr(obj):
    """Recursively convert lists → numpy arrays for known array keys."""
    if isinstance(obj, dict):
        return {
            k: (np.array(v) if k in _ARRAY_KEYS and isinstance(v, list)
                else _list_to_arr(v))
            for k, v in obj.items()
        }
    if isinstance(obj, list):
        return [_list_to_arr(v) for v in obj]
    return obj


def _float_tag(value, decimals):
    """Format a float as a path-safe tag: 0.18 → '0p1800' (4 dec)."""
    return f'{value:.{decimals}f}'.replace('.', 'p')


def _vgs_cache_path(model, w, l, vds):
    """logs/cache/vgs_<model>_W<w>_L<l>_Vds<vds>.json"""
    wtag = _float_tag(w,   2)
    ltag = _float_tag(l,   4)
    vtag = _float_tag(vds, 3)
    return CACHE_DIR / f'vgs_{model}_W{wtag}_L{ltag}_Vds{vtag}.json'


def _vds_cache_path(model, w, l, bias_list):
    """logs/cache/vds_<model>_W<w>_L<l>_<hash8>.json  (hash of bias list)"""
    blob = json.dumps(sorted(bias_list)).encode()
    h    = hashlib.md5(blob).hexdigest()[:8]
    wtag = _float_tag(w, 2)
    ltag = _float_tag(l, 4)
    return CACHE_DIR / f'vds_{model}_W{wtag}_L{ltag}_{h}.json'


def _save_sweep(data, path):
    """Serialise a sweep dict (or list of dicts) to JSON."""
    with open(path, 'w', encoding='utf-8') as fh:
        json.dump(_arr_to_list(data), fh, indent=2)


def _load_sweep(path):
    """Load and deserialise a cached sweep; returns None if file missing."""
    if not path.exists():
        return None
    with open(path, encoding='utf-8') as fh:
        return _list_to_arr(json.load(fh))


# ─────────────────────────────────────────────────────────────────────────────
# GmIdTable
# ─────────────────────────────────────────────────────────────────────────────
class GmIdTable:
    """
    Lookup table for gm/ID-based transistor sizing.

    Parameters
    ----------
    model           : key in MODEL_INFO (e.g. 'nmos180', 'pmos45hp')
    W               : simulation width [µm]
    L               : channel length [µm]
    vds             : Vds or |Vsd| for the Vgs sweep [V]; default = VDD/2
    vgs_bias_list   : list of Vgs (or |Vsg|) bias points used for Vds sweeps
                      (needed for gm·ro computation); default = 9 points
    force_resim     : ignore cache and re-simulate
    """

    def __init__(self, model, W, L, vds=None, vgs_bias_list=None,
                 force_resim=False):
        if model not in MODEL_INFO:
            raise KeyError(
                f'Unknown model: {model!r}.  '
                f'Available: {list(MODEL_INFO.keys())}')

        self.model  = model
        self.W      = float(W)
        self.L      = float(L)
        self._info  = MODEL_INFO[model]
        self._vdd   = float(self._info.get('vdd',  1.8))
        self._pol   = self._info.get('pol', 'nmos')
        _mparams    = _parse_lib_params(str(self._info['file']), model)
        self._vth0  = float(_mparams.get('vth0', 0.4))

        self.vds = round(self._vdd / 2.0, 3) if vds is None else float(vds)

        if vgs_bias_list is None:
            vgs_bias_list = self._default_vgs_bias()
        self._vgs_bias_list = [round(float(v), 3) for v in vgs_bias_list]

        print(f'[GmIdTable] {model}  W={self.W}um  L={self.L*1e3:.0f}nm  '
              f'Vds={self.vds}V')
        self._vgs_data = self._get_vgs_data(force_resim)
        self._vds_data = self._get_vds_data(force_resim)
        self._build_tables()

    # ── private ───────────────────────────────────────────────────────────────

    def _default_vgs_bias(self):
        """9 linearly-spaced Vgs bias points for Vds sweeps."""
        start = round(max(0.05, self._vth0 - 0.10), 3)
        stop  = round(0.92 * self._vdd, 3)
        return [round(float(v), 3) for v in np.linspace(start, stop, 9)]

    def _get_vgs_data(self, force):
        path = _vgs_cache_path(self.model, self.W, self.L, self.vds)
        if not force and path.exists():
            data = _load_sweep(path)
            if data is not None:
                print(f'  Vgs sweep  [cache]  ({path.name})')
                return data
        print(f'  Vgs sweep  [sim] ...')
        if self._pol == 'pmos':
            data = sweep_vsg(self.vds, self.W, self.L, self.model)
        else:
            data = sweep_vgs(self.vds, self.W, self.L, self.model)
        _save_sweep(data, path)
        print(f'               saved  {path.name}')
        return data

    def _get_vgs_data_at(self, vds):
        """
        Return (cached) Vgs sweep data at an arbitrary vds.
        Used for finite-difference gds computation.
        """
        path = _vgs_cache_path(self.model, self.W, self.L, vds)
        if path.exists():
            data = _load_sweep(path)
            if data is not None:
                return data
        if self._pol == 'pmos':
            data = sweep_vsg(vds, self.W, self.L, self.model)
        else:
            data = sweep_vgs(vds, self.W, self.L, self.model)
        _save_sweep(data, path)
        return data

    def _get_vds_data(self, force):
        path = _vds_cache_path(
            self.model, self.W, self.L, self._vgs_bias_list)
        if not force and path.exists():
            data = _load_sweep(path)
            if data is not None:
                print(f'  Vds sweeps [cache]  ({path.name})')
                return data
        print(f'  Vds sweeps [sim] {len(self._vgs_bias_list)} points ...')
        if self._pol == 'pmos':
            data = run_vsd_sweeps(
                self.W, self.L, self.model, self._vgs_bias_list)
        else:
            data = run_vds_sweeps(
                self.W, self.L, self.model, self._vgs_bias_list)
        _save_sweep(data, path)
        print(f'               saved  {path.name}')
        return data

    def _build_tables(self):
        """
        Extract the monotonically-descending right branch of gm/ID vs Vgs
        and build aligned 1-D numpy arrays for all design quantities.

        gds is computed via finite difference between two Vgs sweeps at
        vds and vds+GDS_DELTA, giving the same ~900-point density as gm
        and eliminating the interpolation kinks from the old sparse Vds approach.
        """
        GDS_DELTA = 0.05   # 50 mV perturbation for finite-difference gds

        d    = self._vgs_data
        vgs  = np.asarray(d['vgs'])
        gmid = np.asarray(d['gmid'], dtype=float)
        id_  = np.asarray(d['id'])
        gm   = np.asarray(d['gm'])
        ft   = np.asarray(d['ft'],  dtype=float)
        id_w = np.asarray(d['id_w'])
        vov  = np.asarray(d['vov'])

        # Finite-difference gds: run extra Vgs sweep at vds + delta
        info    = self._info
        vds_hi  = round(self.vds + GDS_DELTA, 3)
        vds_max = float(info.get('vds_stop', 1.8))
        if vds_hi <= vds_max:
            print(f'  Vgs sweep+δ [vds={vds_hi}V] ...')
            data_hi = self._get_vgs_data_at(vds_hi)
            id_hi   = np.asarray(data_hi['id'])
            # Both sweeps use identical Vgs grids → element-wise difference is valid
            gds_full = np.maximum((id_hi - id_) / GDS_DELTA, 0.0)
        else:
            gds_full = None   # fallback to sparse Vds interpolation

        valid = (
            (id_  > 1e-13) &
            np.isfinite(gmid) &
            (gmid >= 2.0) &
            (gmid <= 42.0)
        )

        # Locate peak gm/ID among valid points
        masked_gmid = np.where(valid, gmid, -np.inf)
        peak_idx    = int(np.argmax(masked_gmid))

        # Right branch: from peak onward (descending gm/ID = increasing Vgs)
        sel = valid[peak_idx:]

        self._vgs_arr  = vgs [peak_idx:][sel]
        self._gmid_arr = gmid[peak_idx:][sel]   # descending
        self._id_arr   = id_ [peak_idx:][sel]
        self._gm_arr   = gm  [peak_idx:][sel]
        self._ft_arr   = ft  [peak_idx:][sel]
        self._idw_arr  = id_w[peak_idx:][sel]
        self._vov_arr  = vov [peak_idx:][sel]
        self._gds_arr  = gds_full[peak_idx:][sel] if gds_full is not None else None

        if len(self._vgs_arr) < 2:
            raise RuntimeError(
                f'Too few valid gm/ID points (got {len(self._vgs_arr)}) '
                f'for model={self.model}.  '
                f'Check Vds={self.vds}V setting or simulation output.')

        self._gmro_arr = self._compute_gmro()
        src = f'finite-diff (Δvds={GDS_DELTA}V)' if self._gds_arr is not None \
              else 'Vds sweep (sparse, fallback)'
        print(f'  Table built: {len(self._vgs_arr)} points  '
              f'gm/ID in [{self._gmid_arr[-1]:.1f}, '
              f'{self._gmid_arr[0]:.1f}] V^-1  [gds: {src}]')

    def _compute_gmro(self):
        """
        Compute gm·ro array aligned to self._vgs_arr.

        Preferred path: use gds from the same Vgs sweep (@m1[gds] in netlist).
        This gives gm and gds at the same density (~500 pts) from one source,
        producing a smooth gm·ro curve with no interpolation artifacts.

        Fallback (old cache without gds): interpolate gds from sparse Vds sweeps
        (9 bias points by default), which can introduce visible kinks.
        """
        # ── preferred: single-source gds from Vgs sweep ──────────────────────
        if self._gds_arr is not None:
            gds = np.maximum(self._gds_arr, 1e-15)
            return np.clip(self._gm_arr / gds, 0.0, 1000.0)

        # ── fallback: interpolate from sparse Vds sweeps ─────────────────────
        vds_results = self._vds_data
        if not vds_results:
            return np.zeros(len(self._gm_arr))

        pts = []
        for r in vds_results:
            vds_arr = np.asarray(r['vds'])
            gds_arr = np.asarray(r['gds'])
            vds_ref = self.vds
            if len(vds_arr) < 3:
                continue
            idx = int(np.argmin(np.abs(vds_arr - vds_ref)))
            if vds_arr[idx] < 0.5 * vds_ref:   # not yet in saturation
                continue
            pts.append((float(r['vgs']), float(gds_arr[idx])))

        if len(pts) < 2:
            return np.zeros(len(self._gm_arr))

        pts.sort()
        vgs_pts = np.array([p[0] for p in pts])
        gds_pts = np.array([p[1] for p in pts])
        log_gds = np.log(np.maximum(gds_pts, 1e-30))
        gds_interp = np.exp(
            np.interp(self._vgs_arr, vgs_pts, log_gds,
                      left=log_gds[0], right=log_gds[-1])
        )
        gds_interp = np.maximum(gds_interp, 1e-15)
        return np.clip(self._gm_arr / gds_interp, 0.0, 1000.0)

    # ── public API ────────────────────────────────────────────────────────────

    def lookup(self, qty, gmid):
        """
        Interpolate a device quantity at a given gm/ID operating point.

        Parameters
        ----------
        qty  : str
            One of: 'id_w', 'ft', 'vgs', 'vov', 'gmro', 'gm', 'id'
        gmid : float  [V⁻¹]

        Returns
        -------
        float
        """
        qty_map = {
            'id_w': self._idw_arr,
            'ft':   self._ft_arr,
            'vgs':  self._vgs_arr,
            'vov':  self._vov_arr,
            'gmro': self._gmro_arr,
            'gm':   self._gm_arr,
            'id':   self._id_arr,
        }
        if qty not in qty_map:
            raise ValueError(
                f'Unknown quantity {qty!r}. '
                f'Choose from {sorted(qty_map)}')
        arr = qty_map[qty]
        # _gmid_arr is descending → flip to ascending for np.interp
        x = self._gmid_arr[::-1]
        y = arr[::-1]
        return float(np.interp(float(gmid), x, y,
                               left=y[0], right=y[-1]))

    def size(self, gmid, Id=None, W=None, gm=None):
        """
        Size a transistor given gm/ID and exactly one of: Id, W, or gm.

        Parameters
        ----------
        gmid : float  [V⁻¹]  — target gm/ID
        Id   : float  [A]    — desired drain current
        W    : float  [µm]   — desired transistor width
        gm   : float  [S]    — desired transconductance

        Returns
        -------
        dict with keys:
          model, L_um, W_um, Id_A, Vgs_V, Vov_V, gmid, gm_S,
          ft_Hz, gmro, id_w_Apm
        """
        n_given = sum(x is not None for x in (Id, W, gm))
        if n_given != 1:
            raise ValueError(
                'Provide exactly one of Id [A], W [µm], or gm [S].')

        id_w = self.lookup('id_w', gmid)   # [A/m] == [µA/µm] numerically

        if Id is not None:
            Id   = float(Id)
            W_um = Id / id_w * 1e6
        elif W is not None:
            W_um = float(W)
            Id   = id_w * W_um * 1e-6
        else:   # gm given
            Id   = float(gm) / float(gmid)
            W_um = Id / id_w * 1e6

        gm_S = float(gmid) * Id

        return dict(
            model     = self.model,
            L_um      = self.L,
            W_um      = W_um,
            Id_A      = Id,
            Vgs_V     = self.lookup('vgs',  gmid),
            Vov_V     = self.lookup('vov',  gmid),
            gmid      = float(gmid),
            gm_S      = gm_S,
            ft_Hz     = self.lookup('ft',   gmid),
            gmro      = self.lookup('gmro', gmid),
            id_w_Apm  = id_w,
        )

    def size_from_ft(self, ft_target, Id=None, W=None):
        """
        Return the most power-efficient operating point (highest gm/ID)
        that still achieves fT >= ft_target [Hz].

        Parameters
        ----------
        ft_target : float [Hz]
        Id        : float [A]   — exactly one of Id/W must be given
        W         : float [µm]

        Returns
        -------
        dict  — same format as size()
        """
        ft_arr = np.where(np.isfinite(self._ft_arr), self._ft_arr, 0.0)
        mask   = ft_arr >= float(ft_target)

        if not np.any(mask):
            ft_max = float(np.nanmax(self._ft_arr))
            raise ValueError(
                f'ft_target={ft_target/1e9:.2f} GHz exceeds max achievable '
                f'fT={ft_max/1e9:.2f} GHz for model={self.model}')

        # _gmid_arr is descending → first valid index = highest gm/ID
        valid_idx = np.where(mask)[0]
        best_idx  = int(valid_idx[0])
        opt_gmid  = float(self._gmid_arr[best_idx])
        return self.size(opt_gmid, Id=Id, W=W)

    def size_from_gmro(self, gmro_target, Id=None, W=None):
        """
        Return the most power-efficient operating point (highest gm/ID)
        that still achieves gm·ro >= gmro_target.

        Parameters
        ----------
        gmro_target : float  — minimum required intrinsic voltage gain
        Id          : float [A]   — exactly one of Id/W must be given
        W           : float [µm]

        Returns
        -------
        dict  — same format as size()
        """
        mask = self._gmro_arr >= float(gmro_target)

        if not np.any(mask):
            gmro_max = float(np.max(self._gmro_arr))
            raise ValueError(
                f'gmro_target={gmro_target:.1f} exceeds max achievable '
                f'gm·ro={gmro_max:.1f} for model={self.model}')

        valid_idx = np.where(mask)[0]
        best_idx  = int(valid_idx[0])
        opt_gmid  = float(self._gmid_arr[best_idx])
        return self.size(opt_gmid, Id=Id, W=W)

    def operating_range(self):
        """
        Return a summary of the table's valid operating range.

        Returns
        -------
        dict with keys: gmid_min, gmid_max, ft_max_Hz, gmro_at_15
        """
        return dict(
            gmid_min  = float(np.min(self._gmid_arr)),
            gmid_max  = float(np.max(self._gmid_arr)),
            ft_max_Hz = float(np.nanmax(self._ft_arr)),
            gmro_at_15 = float(self.lookup('gmro', 15.0)),
        )


# ─────────────────────────────────────────────────────────────────────────────
# Pretty-print operating point
# ─────────────────────────────────────────────────────────────────────────────
def print_op(op):
    """
    Print a formatted transistor operating-point summary.

    Parameters
    ----------
    op : dict returned by GmIdTable.size() / size_from_ft() / size_from_gmro()

    Example output
    --------------
    ============================================
      Transistor Operating Point
    --------------------------------------------
      Model    : nmos180    L = 180 nm
      gm/ID    : 15.0 V^-1
      Vgs      : 0.623 V    Vov = 0.183 V
    --------------------------------------------
      W        : 20.00 um
      Id       : 100.00 uA    Id/W =  5.00 uA/um
      gm       : 1.500 mS
      fT       : 8.23 GHz
      gm.ro    : 38.5
    ============================================
    """
    model  = op['model']
    L_nm   = op['L_um']  * 1e3
    W_um   = op['W_um']
    Id_uA  = op['Id_A']  * 1e6
    id_w   = op['id_w_Apm']            # A/m == uA/um numerically
    gm_mS  = op['gm_S']  * 1e3
    ft_GHz = op['ft_Hz'] / 1e9
    gmid   = op['gmid']
    vgs    = op['Vgs_V']
    vov    = op['Vov_V']
    gmro   = op['gmro']

    print('=' * 44)
    print('  Transistor Operating Point')
    print('-' * 44)
    print(f'  Model    : {model:<12s}  L = {L_nm:.0f} nm')
    print(f'  gm/ID    : {gmid:.1f} V^-1')
    print(f'  Vgs      : {vgs:.3f} V    Vov = {vov:.3f} V')
    print('-' * 44)
    print(f'  W        : {W_um:.2f} um')
    print(f'  Id       : {Id_uA:.2f} uA    Id/W = {id_w:.2f} uA/um')
    print(f'  gm       : {gm_mS:.3f} mS')
    print(f'  fT       : {ft_GHz:.2f} GHz')
    print(f'  gm.ro    : {gmro:.1f}')
    print('=' * 44)
