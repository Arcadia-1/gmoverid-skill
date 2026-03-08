# gm/ID Characterization — Conventions & Design Reference

## Table of Contents
1. [Project File Structure](#1-project-file-structure)
2. [NMOS/PMOS Sign Conventions](#2-nmospmos-sign-conventions)
3. [Model Registry](#3-model-registry)
4. [Netlist Templates](#4-netlist-templates)
5. [Data Dict Keys](#5-data-dict-keys)
6. [Sweep Configuration Constants](#6-sweep-configuration-constants)
7. [Plot Conventions](#7-plot-conventions)
8. [Physical Sanity Checks](#8-physical-sanity-checks)
9. [Common Errors & Fixes](#9-common-errors--fixes)
10. [Extending the Skill](#10-extending-the-skill)
11. [Design API Reference](#11-design-api-reference)

---

## 1. Project File Structure

```
<project>/
├── simulate_gmoverid.py    # ngspice runner + data extraction + MODEL_INFO
├── plot_gmoverid.py        # all matplotlib figures
├── run_gmoverid.py         # 180nm single-node orchestration (entry point)
├── run_multinode.py        # multi-node orchestration (45/32/22/16nm HP)
├── models/
│   ├── nmos180.lib         # BSIM3v3 PTM 180nm NMOS (SVT + LVT + HVT)
│   ├── pmos180.lib         # BSIM3v3 PTM 180nm PMOS (SVT + LVT + HVT)
│   ├── nmos45hp.lib  pmos45hp.lib   # BSIM4 PTM 45nm HP  (VDD=1.0V)
│   ├── nmos32hp.lib  pmos32hp.lib   # BSIM4 PTM 32nm HP  (VDD=0.9V)
│   ├── nmos22hp.lib  pmos22hp.lib   # BSIM4 PTM 22nm HP  (VDD=0.8V)
│   └── nmos16hp.lib  pmos16hp.lib   # BSIM4 PTM 16nm HP  (VDD=0.7V)
├── netlist/
│   ├── gmoverid_vgs.cir.tmpl       # NMOS Vgs sweep at fixed Vds
│   ├── gmoverid_vds.cir.tmpl       # NMOS Vds sweep at fixed Vgs
│   ├── gmoverid_pmos_vsg.cir.tmpl  # PMOS |Vsg| sweep at fixed |Vsd|
│   └── gmoverid_pmos_vsd.cir.tmpl  # PMOS |Vsd| sweep at fixed |Vsg|
├── plots/                  # output PNGs (150 dpi)
└── logs/                   # ngspice .cir / .dat / .log intermediates
```

**No path configuration needed**: all paths resolve automatically via
`Path(__file__).resolve().parent`. Output goes to `plots/` and `logs/` relative to the
project root. Simply copy the assets and run.

---

## 2. NMOS/PMOS Sign Conventions

### NMOS (`sweep_vgs`, `sweep_vds`)
- Netlist: `i(Vds)` is **negative** (current flows into + terminal of Vds source)
- Code: `id_ = np.maximum(-icur, 0.0)` → positive Id values
- `vov = vgs - vth` (positive in strong inversion)

### PMOS (`sweep_vsg`, `sweep_vsd`)
- Netlist: source at VDD, gate swept from VDD→0, drain at `VDD - |Vsd|`
- `i(Vdrain)` is **positive** (current flows into + terminal of Vdrain source)
- Code: `id_ = np.maximum(icur, 0.0)` → **no negation**
- `|Vsg| = VDD - Vgate_absolute` (ascending 0→VDD as Vgate sweeps VDD→0)
- `|Vsd| = VDD - Vdrain_absolute`
- `vov = |Vsg| - |Vth|` (positive in strong inversion)

### Unified return dict convention
All sweep functions return the same key names so plotting code is polarity-agnostic:
- `vgs` → Vgs for NMOS, |Vsg| for PMOS (always positive, ascending)
- `vds` → Vds for NMOS, |Vsd| for PMOS (always positive)
- `vov` → Vov = Vgs - Vth for NMOS, |Vsg| - |Vth| for PMOS
- `id`  → |Id| (always positive µ-amps)
- `id_w` → |Id|/W [A/m] = |Id|/(w_um × 1e-6)

---

## 3. Model Registry

`MODEL_INFO` in `simulate_gmoverid.py`. Full entry example:
```python
'nmos45hp': dict(pol='nmos', vth0=0.469, cgso=1.1e-10, cgdo=1.1e-10,
                 nch=3.24e18*1e6, mu=0.054, file=_mf('nmos45hp.lib'),
                 vdd=1.0, vgs_stop=1.2, vds_stop=1.2, tox=1.25e-9)
```

### PTM 180nm BSIM3v3 (VDD=1.8V, TOX=4.1nm)

| Key           | pol   | vth0 [V] | mu [m²/Vs] | cgso/cgdo [F/m] | NCH [cm⁻³]    |
|---------------|-------|----------|------------|-----------------|----------------|
| nmos180       | nmos  | 0.40     | 270e-4     | 7.9e-10         | 2.3549e17      |
| nmos180_lvt   | nmos  | 0.30     | 270e-4     | 7.9e-10         | 2.3549e17      |
| nmos180_hvt   | nmos  | 0.55     | 270e-4     | 7.9e-10         | 2.3549e17      |
| pmos180       | pmos  | 0.42     | 117.5e-4   | 6.8e-10         | 6.0165e16      |
| pmos180_lvt   | pmos  | 0.32     | 117.5e-4   | 6.8e-10         | 6.0165e16      |
| pmos180_hvt   | pmos  | 0.57     | 117.5e-4   | 6.8e-10         | 6.0165e16      |

### PTM HP BSIM4 nodes

| Key        | pol   | vth0 [V] | mu [m²/Vs] | cgso/cgdo [F/m] | NCH [cm⁻³] | VDD  | TOX [nm] |
|------------|-------|----------|------------|-----------------|------------|------|----------|
| nmos45hp   | nmos  | 0.469    | 0.054      | 1.1e-10         | 3.24e18    | 1.0V | 1.25     |
| pmos45hp   | pmos  | 0.492    | 0.020      | 1.1e-10         | 2.44e18    | 1.0V | 1.30     |
| nmos32hp   | nmos  | 0.494    | 0.050      | 8.5e-11         | 4.12e18    | 0.9V | 1.15     |
| pmos32hp   | pmos  | 0.492    | 0.014      | 8.5e-11         | 3.07e18    | 0.9V | 1.20     |
| nmos22hp   | nmos  | 0.503    | 0.040      | 7.0e-11         | 5.02e18    | 0.8V | 1.05     |
| pmos22hp   | pmos  | 0.490    | 0.012      | 7.0e-11         | 3.70e18    | 0.8V | 1.10     |
| nmos16hp   | nmos  | 0.480    | 0.030      | 6.0e-11         | 6.00e18    | 0.7V | 0.95     |
| pmos16hp   | pmos  | 0.480    | 0.010      | 6.0e-11         | 4.50e18    | 0.7V | 1.05     |

- vgs_stop = vdd + 0.2V (e.g. 45nm: vgs_stop=1.2V); vds_stop = vgs_stop
- Threshold extraction: constant-current method at Id/(W/L) = 100 nA

### Using user-provided model parameters
If the user provides a `.lib` file or model parameters (vth0, tox, nch, cgso, mu, VDD),
use those directly. The built-in PTM parameters above are **fallback defaults only**.
To use a user model: create/add its entry to `MODEL_INFO` and point `file` to the user's
`.lib`; all plotting and sweep functions are model-agnostic.

### Adding a new model variant
1. Add `.MODEL` card to the appropriate `.lib` file (or provide user's `.lib`)
2. Add an entry to `MODEL_INFO` in `simulate_gmoverid.py`
3. Add it to the run script (`NMOS_MODELS`/`PMOS_MODELS` in `run_gmoverid.py`, or a new
   entry in `NODE_CFG` in `run_multinode.py`)

---

## 4. Netlist Templates

Templates use Python `str.format()` placeholders. **Never put `{...}` in SPICE
comment lines** — they will be interpreted as format placeholders and raise `KeyError`.

### NMOS Vgs sweep template placeholders
`{model_path}`, `{model}`, `{vds_v}`, `{w_um}`, `{l_um}`,
`{vgs_start}`, `{vgs_stop}`, `{vgs_step}`, `{dat_path}`

### NMOS Vds sweep template placeholders
`{model_path}`, `{model}`, `{vgs_v}`, `{w_um}`, `{l_um}`,
`{vds_start}`, `{vds_stop}`, `{vds_step}`, `{dat_path}`

### PMOS Vsg sweep template placeholders
`{model_path}`, `{model}`, `{vdd_v}`, `{vd_v}`, `{w_um}`, `{l_um}`,
`{vg_start}`, `{vg_stop}`, `{vg_step}`, `{dat_path}`

### PMOS Vsd sweep template placeholders
`{model_path}`, `{model}`, `{vdd_v}`, `{vg_v}`, `{w_um}`, `{l_um}`,
`{vd_start}`, `{vd_stop}`, `{vd_step}`, `{dat_path}`

### ngspice settings
- Solver: `method=gear`, `itl4=100` (robust convergence)
- Data written with `wrdata` → 4-column output; col0 = sweep var, col3 = current
- `_parse_wrdata_2vec()` handles the parsing

---

## 5. Data Dict Keys

Returned by all sweep functions:

| Key    | Type          | Description                              |
|--------|---------------|------------------------------------------|
| model  | str           | model name                               |
| pol    | 'nmos'/'pmos' | polarity                                 |
| vgs    | array         | Vgs (NMOS) or \|Vsg\| (PMOS), ascending |
| vds    | scalar        | fixed Vds or \|Vsd\| for this sweep      |
| id     | array         | \|Id\| [A]                               |
| gm     | array         | transconductance [S]                     |
| cgs    | array         | gate-source cap [F] (analytical)         |
| cgd    | array         | gate-drain cap [F] (analytical)          |
| cgb    | array         | gate-bulk cap [F] (analytical)           |
| cgg    | array         | total gate cap [F] (analytical)          |
| gmid   | array         | gm/Id [V⁻¹]                             |
| ft     | array         | transit freq [Hz]                        |
| id_w   | array         | \|Id\|/W [A/m]                           |
| vov    | array         | overdrive voltage [V]                    |
| vth    | scalar        | extracted threshold [V]                  |

Vds sweep adds: `gds` [S], `ro` [Ω] (no cap fields).

---

## 6. Sweep Configuration Constants

In `simulate_gmoverid.py` (180nm defaults — overridden per model via MODEL_INFO):
```python
VGS_START, VGS_STOP, VGS_STEP = 0.0, 1.8, 0.002   # 900 points
VDS_START, VDS_STOP, VDS_STEP = 0.0, 1.8, 0.002
VDS_LIST  = [0.1, 0.5, 0.9, 1.8]   # Vgs-sweep: Vds values
VGS_BIAS  = [0.5, 0.6, 0.8, 1.0]   # Vds-sweep: Vgs bias points
```

In `run_gmoverid.py` (180nm single-node):
```python
W         = 10.0        # µm  (Vgs sweeps and main characterization)
L_MIN     = 0.18        # µm  (180 nm)
L_LIST    = [0.18, 0.36, 1.00]
VDS_COMP    = [0.9]     # primary Vds for comparison figures
VDS_COMP_HI = [1.0]     # secondary Vds for numerical gds (gm·ro panel)
W_IV        = 1.8       # µm  W/L=10 for output-characteristic figure
VGS_IV      = [0.6, 0.7, 0.8, 0.9, 1.0]
```

In `run_multinode.py` (HP multi-node), each node uses `NODE_CFG`:
```python
NODE_CFG = {
    '45nm': dict(nmos='nmos45hp', pmos='pmos45hp', l_nm=45, l_um=0.045,
                 W=1.0, vdd=1.0,
                 vds_list=[0.05, 0.3, 0.5, 1.0],   # Vgs-sweep Vds values
                 vgs_bias=[0.3, 0.4, 0.5, 0.6],    # Vds-sweep Vgs bias
                 vds_comp=[0.5], vds_comp_hi=[0.6], # comparison sweeps
                 vgs_iv=[0.4, 0.5, 0.6, 0.7, 0.8], # IV output curves
                 w_iv=0.45),                         # W for IV (W/L≈10)
    '32nm': dict(..., vdd=0.9, vds_list=[0.05, 0.25, 0.45, 0.9], w_iv=0.32),
    '22nm': dict(..., vdd=0.8, vds_list=[0.04, 0.2, 0.4, 0.8],  w_iv=0.22),
    '16nm': dict(..., vdd=0.7, vds_list=[0.1, 0.2, 0.35, 0.7],  w_iv=0.16),
}
```

---

## 7. Plot Conventions

### Style constants (plot_gmoverid.py)
```python
COLORS = ['#1565C0', '#E65100', '#2E7D32', '#C62828']  # + '#7B1FA2' for 5th curve
LSTYLE = ['-', '--', '-.', ':']
REF_C  = '#777777'   # reference/annotation curves
```
- All figures saved to `plots/` as PNG @ 150 dpi; `matplotlib.use('Agg')` mandatory
- Never use `plt.show()` or interactive backends
- Grid on, `axes.background = #F9F9F9`

### Axis label unit convention
Square brackets: `[V]`, `[GHz]`, `[V⁻¹]`, `[µA/µm]`, `[k·Ω]`, `[fF]`

### Three standard plot sets (per model)

For any technology model, three sets of figures are generated:

**Set 1 — Gate Capacitances** (`plot_caps`)
Single panel: Cgg, Cgs, Cgd, Cgb [fF] vs Vgs (0→VDD). Vth shown as dotted vertical line.
File: `gmoverid_caps_{model}_L{node}nm.png`

**Set 2 — gm/Id 4-panel** (`plot_main`)  — 2×2 layout:
```
(0,0) gm/Id [V⁻¹] vs Vov [V]       | (0,1) Id/W [µA/µm] vs gm/Id (log y)
(1,0) fT [GHz]    vs gm/Id          | (1,1) Intrinsic gain gm·ro vs Vds (0→VDD)
```
- Parametric curves: one per Vds value in `vds_list`; legend shows "Vds=X.XXV"
- (0,0) also shows BJT q/kT=38.6 reference and 2/Vov asymptote
- (0,1)(1,0) x-axis: xlim=[4,24], xticks=[4,6,8,...,24]
- (1,1) x-axis: xlim=[0, vds_stop]; parametric in Vgs bias; legend shows "Vgs=X.XXV"
File: `gmoverid_{model}_L{node}nm.png`

**Set 3 — IV Characteristics** (`plot_iv`) — 2×2 layout:
```
(0,0) Id [µA] vs Vov (linear)  | (0,1) Id [µA] vs Vov (log scale)
(1,0) Id [µA] vs Vgs (0→VDD)  | (1,1) Id [µA] vs Vds — output curves at fixed Vgs
```
File: `gmoverid_iv_{model}_L{node}nm.png`

### Figures produced by `run_gmoverid.py` (180nm)

| File | Content |
|------|---------|
| `gmoverid_nmos180_L180nm.png` | NMOS SVT 4-panel gm/Id characterization |
| `gmoverid_pmos180_L180nm.png` | PMOS SVT 4-panel gm/Id characterization |
| `gmoverid_caps_nmos180_L180nm.png` | NMOS analytical gate capacitances |
| `gmoverid_caps_pmos180_L180nm.png` | PMOS analytical gate capacitances |
| `gmoverid_iv_nmos180_L180nm.png` | NMOS 4-panel IV characteristics |
| `gmoverid_iv_pmos180_L180nm.png` | PMOS 4-panel IV characteristics |
| `gmid_nmos_vth_L180nm.png` | NMOS 4-panel comparison: LVT/SVT/HVT |
| `gmid_pmos_vth_L180nm.png` | PMOS 4-panel comparison: LVT/SVT/HVT |
| `gmid_nmos_length_svt.png` | NMOS 4-panel comparison: L=180/360/1000nm |
| `gmid_pmos_length_svt.png` | PMOS 4-panel comparison: L=180/360/1000nm |

### Additional figures produced by `run_multinode.py` (HP nodes)

Per node (45/32/22/16nm): 3 sets × 2 polarities = 6 figures each = 24 figures total.
Plus cross-node comparison and combined caps panel:

| File | Content |
|------|---------|
| `gmid_nmos_node_comp.png` | NMOS 4-panel cross-node comparison (180/45/32/22/16nm) |
| `gmid_pmos_node_comp.png` | PMOS 4-panel cross-node comparison |
| `gmid_nmos_caps_comp.png` | NMOS 2×2 caps panel: 45/32/22/16nm HP |
| `gmid_pmos_caps_comp.png` | PMOS 2×2 caps panel: 45/32/22/16nm HP |

### Combined caps comparison (`plot_caps_comparison`)
2×2 panel, one subplot per technology node.
Signature: `plot_caps_comparison(node_configs, polarity, out_path)`
`node_configs` = list of `(model, w_um, l_um)` tuples (up to 4 entries).

### 4-panel comparison layout (`plot_comparison`)
(0,0) gm/Id vs Vov | (0,1) Id/W vs gm/Id (log y)
(1,0) fT vs gm/Id  | (1,1) gm·ro vs gm/Id (numerical gds from two Vds sweeps)

### gm·ro computation (comparison figures)
Numerical gds from two Vgs sweeps at Vds_comp and Vds_comp_hi (ΔVds ≈ 0.1V):
```python
delta_id = medfilt(r2['id'] - r1['id'], kernel_size=21)
gds  = np.maximum(delta_id / dvds, 1e-15)
gmro = medfilt(r1['gm'] / gds, kernel_size=11)
```

---

## 8. Physical Sanity Checks

Expected results for PTM 180nm NMOS SVT, W=10µm, L=180nm:

| Quantity | Expected | Notes |
|----------|----------|-------|
| Vth (extracted, Vds=0.9V) | ~0.46V | constant-current method |
| gm/Id (weak inversion) | ~38 V⁻¹ | approaches q/kT = 38.6 V⁻¹ |
| gm/Id (strong inversion, Vov=0.3V) | ~5–7 V⁻¹ | ~2/Vov |
| fT at Vgs=0.9V | ~26 GHz | gm/(2π·Cgg) |
| Id at Vgs=0.9V, Vds=0.9V | ~1.1 mA | W=10µm |
| ro at Vgs=0.6V, Vds=0.9V | ~26 kΩ | depends strongly on Vgs |

PMOS at L=180nm shows stronger short-channel Vth rolloff (DVT0=2.48 vs NMOS 1.32):
- Nominal |VTH0| = 0.42V but extracted |Vth| ≈ 0.26V at Vds=0.9V — physically correct.

---

## 9. Common Errors & Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| `KeyError: 'vsd_v'` in netlist | `{vsd_v}` in a SPICE comment line | Remove placeholder from comment |
| `KeyError: 'vsg_v'` in netlist | Same for Vsg | Same fix |
| ngspice produces empty .dat | Convergence failure | Check itl4, try method=gear (see ngspice skill) |
| id_ all zeros | Wrong sign convention | Check `icur` sign; NMOS: `-icur`, PMOS: `+icur` |
| PMOS sweep not ascending | `vsg` sorted descending | Apply `[::-1]` flip after reading |
| `UnicodeEncodeError` on Windows | GBK console | Run with `PYTHONUTF8=1` |

---

## 10. Extending the Skill

### Add a new PDK / technology node
1. Create `models/<node>.lib` with BSIM3/BSIM4 `.MODEL` cards
   - If user provides their own `.lib`, use it directly; no need to create one
2. Add NMOS and PMOS entries to `MODEL_INFO` in `simulate_gmoverid.py`:
   ```python
   'nmos_xyz': dict(pol='nmos', vth0=..., cgso=..., cgdo=...,
                    nch=..., mu=..., file=_mf('nmos_xyz.lib'),
                    vdd=..., vgs_stop=..., vds_stop=..., tox=...)
   ```
3. For `run_multinode.py`: add a new entry to `NODE_CFG` with appropriate
   `vds_list`, `vgs_bias`, `vds_comp`, `vds_comp_hi`, `vgs_iv`, `w_iv` for the node
4. Verify physical results against §8 scaled for new node

### Use user-provided model parameters
If the user supplies model parameters (or a `.lib` file), do NOT fall back to PTM defaults.
Build the `MODEL_INFO` entry from user data and proceed. PTM values in §3 are fallbacks only.

### Add a new plot type
1. Write a new function in `plot_gmoverid.py` following the pattern:
   - Accept `vgs_results` and/or `vds_results` lists
   - Use `_pol_labels(pol)` for axis label strings
   - Save to `out_path`, return `out_path`
2. Import and call it from the relevant run script

### Add a new channel length (180nm only)
Add the value (in µm) to `L_LIST` in `run_gmoverid.py`. The comparison figures
will automatically include the new length curve.

---

## 11. Design API Reference

### Overview

`design_gmoverid.py` provides `GmIdTable` — a lookup-table class for sizing
transistors via the gm/ID methodology.  Simulation data is cached to JSON so
subsequent calls (same model/W/L/Vds) are instant.

### Constructor

```python
GmIdTable(model, W, L, vds=None, vgs_bias_list=None, force_resim=False)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model` | str | — | Key in `MODEL_INFO` |
| `W` | float | — | Simulation width [µm] |
| `L` | float | — | Channel length [µm] |
| `vds` | float | `VDD/2` | Vds or \|Vsd\| for the Vgs sweep [V] |
| `vgs_bias_list` | list[float] | 9 pts (Vth0−0.1 → 0.92·VDD) | Bias points for Vds sweeps |
| `force_resim` | bool | False | Ignore cache and re-simulate |

### Public methods

| Method | Returns | Description |
|--------|---------|-------------|
| `lookup(qty, gmid)` | float | Interpolate `qty` at given gm/ID |
| `size(gmid, Id=…\|W=…\|gm=…)` | dict | Size transistor; one of Id/W/gm required |
| `size_from_ft(ft_target, Id=…\|W=…)` | dict | Highest gm/ID achieving fT ≥ target |
| `size_from_gmro(gmro_target, Id=…\|W=…)` | dict | Highest gm/ID achieving gm·ro ≥ target |
| `operating_range()` | dict | `{gmid_min, gmid_max, ft_max_Hz, gmro_at_15}` |

### `lookup` quantities

| `qty` | Unit | Description |
|-------|------|-------------|
| `'id_w'` | A/m = µA/µm | Current density (Id/W) |
| `'ft'` | Hz | Transit frequency |
| `'vgs'` | V | Gate-source voltage (or \|Vsg\|) |
| `'vov'` | V | Overdrive voltage |
| `'gmro'` | — | Intrinsic voltage gain gm·ro |
| `'gm'` | S | Transconductance |
| `'id'` | A | Drain current (at reference W) |

### `size()` return dict keys

```
model     str     model name
L_um      float   channel length [µm]
W_um      float   transistor width [µm]
Id_A      float   drain current [A]
Vgs_V     float   gate-source voltage [V]
Vov_V     float   overdrive voltage [V]
gmid      float   gm/ID [V⁻¹]
gm_S      float   transconductance [S]
ft_Hz     float   transit frequency [Hz]
gmro      float   intrinsic gain gm·ro
id_w_Apm  float   Id/W [A/m] = [µA/µm]
```

### `print_op(op)` — standalone function

Pretty-prints a sizing result dict:
```
════════════════════════════════════════════
  Transistor Operating Point
────────────────────────────────────────────
  Model    : nmos180      L = 180 nm
  gm/ID    : 15.0 V⁻¹
  Vgs      : 0.623 V    Vov = 0.183 V
────────────────────────────────────────────
  W        : 20.00 µm
  Id       : 100.00 µA    Id/W = 5.00 µA/µm
  gm       : 1.500 mS
  fT       : 8.23 GHz
  gm·ro    : 38.5
════════════════════════════════════════════
```

### Cache file naming

Cached JSON files are written to `logs/cache/`:

| Type | Filename pattern |
|------|-----------------|
| Vgs sweep | `vgs_{model}_W{w:.2f}_L{l:.4f}_Vds{vds:.3f}.json` |
| Vds sweeps | `vds_{model}_W{w:.2f}_L{l:.4f}_{hash8}.json` |

Decimal points replaced by `p` (e.g. `W10p00`, `L0p1800`, `Vds0p900`).
The `hash8` is the first 8 hex digits of MD5(`json.dumps(sorted(bias_list))`).

Examples:
- `vgs_nmos180_W10p00_L0p1800_Vds0p900.json`
- `vds_nmos180_W10p00_L0p1800_a1b2c3d4.json`

### Unit conventions

| Symbol | Unit | Relation |
|--------|------|----------|
| `id_w` | A/m | 1 A/m = 1 µA/µm (same numeric value) |
| `W_um` | µm | — |
| `L_um` | µm | — |
| `Id_A` | A | — |
| `gm_S` | S | — |
| `ft_Hz` | Hz | — |

### Internal table construction

`_build_tables()` selects the **right branch** of gm/ID vs Vgs:
1. Locate peak gm/ID index (nanargmax over valid points)
2. From peak to end of sweep, keep points where `id > 1e-13` and `gmid ∈ [2, 42]`
3. Resulting `_gmid_arr` is **descending** (index 0 = weakest inversion)

`_compute_gmro()` uses log-space interpolation of gds from Vds output sweeps
(same algorithm as `_gds_at_vds()` in `plot_gmoverid.py`).

### Typical usage

```python
from design_gmoverid import GmIdTable, print_op

# First call: simulates and writes to logs/cache/
tbl = GmIdTable('nmos180', W=10.0, L=0.18, vds=0.9)

# Second call: reads from cache (fast)
tbl2 = GmIdTable('nmos180', W=10.0, L=0.18, vds=0.9)

# Lookup
print(tbl.lookup('id_w', 15.0))   # ~5 µA/µm  (nmos180)
print(tbl.lookup('ft',   15.0))   # ~10–15 GHz (nmos180)
print(tbl.lookup('gmro', 15.0))   # ~35–45     (nmos180 L=180nm)

# Sizing by drain current
op = tbl.size(gmid=15.0, Id=100e-6)
print_op(op)    # W ~ 20 µm

# Sizing by width
op = tbl.size(gmid=15.0, W=20.0)
print_op(op)    # Id ~ 100 µA

# Constrained sizing
op = tbl.size_from_ft(5e9, W=20.0)    # meet fT spec
op = tbl.size_from_gmro(30, Id=50e-6) # meet gain spec
```
