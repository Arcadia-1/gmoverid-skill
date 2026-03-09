---
name: gmoverid
description: "gm/ID transistor characterization and design methodology, based on ngspice + Python. Two independent workflows: (1) Characterization — generates three standard curve sets for any MOSFET model: gate capacitance (Cgg/Cgs/Cgd/Cgb vs Vgs), gm/ID four-quadrant characteristics (gm/Id vs Vov, Id/W vs gm/Id, fT vs gm/Id, gm·ro vs gm/Id), and IV characteristics (linear/log Id vs Vov, output curves). Supports 180 nm single-node and 45/22 nm HP multi-node flows with built-in PTM model files (180/45/22 nm) — no extra downloads required. (2) Design — the GmIdTable class builds a lookup table from simulation data (cached to logs/cache/) and provides lookup(), size(), size_from_ft(), size_from_gmro() APIs for NMOS/PMOS transistor sizing using the gm/ID methodology. Only depends on the ngspice skill. Use this skill when setting up or extending a gm/ID characterization project, generating characteristic curves, interpreting design curves, or sizing transistors by the gm/ID method."
---

# gm/ID Characterization and Design Skill

> **Important — do not modify skill files during normal use.**
> All code edits, new scripts, plots, and simulation outputs should go into the user's **project working directory** (outside `.claude/`), not into this skill folder. Only modify the skill assets (`assets/`, `SKILL.md`, `references/`) when the user explicitly asks to improve or extend the skill itself.

**Dependency**: `ngspice` skill (netlist execution, wrdata parsing). Model files are built in — the `transistor-models` skill is not required.

## Asset Files

```
assets/
├── simulate_gmoverid.py   — ngspice simulation engine, data extraction, analytical caps, MODEL_INFO registry
├── plot_gmoverid.py       — all matplotlib plotting functions
├── run_gmoverid.py        — 180 nm single-node orchestration (NMOS/PMOS + channel-length sweep)
├── run_multinode.py       — multi-node orchestration (45/22 nm HP)
├── design_gmoverid.py     — GmIdTable lookup/sizing API + print_op()
├── models/                — built-in PTM model files (ready to use)
│   ├── nmos180.lib        — 180 nm BSIM3v3 (VDD = 1.8 V)
│   ├── pmos180.lib
│   ├── nmos45hp.lib       — 45 nm HP BSIM4 (VDD = 1.0 V)
│   ├── pmos45hp.lib
│   ├── nmos22hp.lib       — 22 nm HP BSIM4 (VDD = 0.8 V)
│   └── pmos22hp.lib
└── netlist/
    ├── gmoverid_vgs.cir.tmpl       — NMOS Vgs sweep (fixed Vds)
    ├── gmoverid_vds.cir.tmpl       — NMOS Vds sweep (fixed Vgs)
    ├── gmoverid_pmos_vsg.cir.tmpl  — PMOS |Vsg| sweep (fixed |Vsd|)
    └── gmoverid_pmos_vsd.cir.tmpl  — PMOS |Vsd| sweep (fixed |Vsg|)
```

Built-in models are from [PTM — Arizona State University (ptm.asu.edu)](https://ptm.asu.edu), free for academic research. When citing, use: W. Zhao and Y. Cao, "New Generation of Predictive Technology Model for Sub-45 nm Early Design Exploration," *IEEE Trans. Electron Devices*, vol. 53, no. 11, pp. 2816–2823, Nov. 2006. doi: 10.1109/TED.2006.884077. For nodes beyond the three built-in ones, install the `transistor-models` skill (full PTM library, requires manual MODEL_INFO configuration) or download from [mec.umn.edu/ptm](https://mec.umn.edu/ptm) and copy the `.lib` file into the project's `models/` directory.

---

## Workflow 1: Characterization (Simulation + Plotting)

### Deployment

1. Copy all assets (including the `models/` subdirectory) to `<project>/`
2. Create empty directories `plots/` and `logs/`
3. Run `python run_gmoverid.py` (180 nm) or `python run_multinode.py` (HP multi-node)

For additional nodes, simply copy the extra `.lib` file into `<project>/models/`.

All paths resolve automatically via `Path(__file__).resolve().parent` — no path configuration needed.

### Three Standard Plot Sets (per model)

| Set | Function | Output file |
|-----|----------|-------------|
| Gate capacitance | `plot_caps()` | `gmoverid_caps_{model}_L{node}nm.png` |
| gm/ID four-quadrant | `plot_main()` | `gmoverid_{model}_L{node}nm.png` |
| IV characteristics | `plot_iv()` | `gmoverid_iv_{model}_L{node}nm.png` |

**gm/ID four-quadrant layout (`plot_main`, 2×2):**
```
(0,0) gm/Id [V⁻¹] vs Vov     | (0,1) Id/W [uA/um] vs gm/Id  (log Y)
(1,0) fT [GHz]    vs gm/Id   | (1,1) gm·ro        vs gm/Id
```
- All four panels use Vds as the curve parameter (VDS_LIST)
- gm/Id X-axis: xlim = [4, 24], one grid division per 2 V⁻¹
- Panels (0,1), (1,0), (1,1) apply `_fall_mask(gmid)` before plotting — the gm/ID array is double-valued (same gm/ID appears on the subthreshold rising side and the inversion falling side); only the falling (inversion) side is kept to prevent curve fold-back. Panel (0,0) is exempt because its X-axis is Vov, which is monotonic.

### Adding a New Technology Node

1. Copy the model `.lib` into `models/` (download from [mec.umn.edu/ptm](https://mec.umn.edu/ptm) or install the `transistor-models` skill)
2. Add an entry to `MODEL_INFO` in `simulate_gmoverid.py` (see conventions.md §3)
3. Add an entry to `NODE_CFG` in `run_multinode.py`

---

## Plotting Conventions (required when creating new figures)

> When generating figures for a new project or plotting for a design report, follow the style of the existing figures produced by this skill.

**Format requirements:**
- Never call `plt.show()`; always use `fig.savefig(path, dpi=150, bbox_inches='tight')` and save to `plots/`
- Colors and line styles: cycle through `COLORS`/`LSTYLE` from `plot_gmoverid.py` in order (blue solid, orange dashed, green dash-dot, purple dotted)
- X-axis for gm/ID: always `xlim = [4, 24]` with one tick per 2 V⁻¹; Y-axis `ylim(bottom=0)`
- **Fold-back prevention**: whenever gm/ID is the X-axis, prepend `_fall_mask(gmid)` to the boolean mask. The gm/ID vs Vgs curve peaks and then descends — both sides can fall within [4, 24], causing matplotlib to draw a fold-back. `_fall_mask` discards the subthreshold rising side (before the peak); only the inversion falling side is plotted. This rule applies to `plot_main` panels (0,1)/(1,0)/(1,1) and to the equivalent panels in `plot_comparison`.
- Titles and axis labels: use **ASCII + LaTeX** (e.g. `$g_m/I_D$`); **do not write Chinese characters directly in matplotlib labels**
- **`µ` (U+00B5) fails to render in some terminals and fonts** — always use `u` in axis labels (e.g. `uA/um`, `W=10um`) or LaTeX `$\\mu$`; use Unicode µ only when the user explicitly requests it

**Chinese font warning:**
matplotlib does not include Chinese fonts by default; Chinese characters render as boxes (□□). If Chinese is needed, add at the top of the script:
```python
import matplotlib
matplotlib.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False
```
On Windows prefer `Microsoft YaHei`; on Linux/macOS verify the font is installed, otherwise boxes still appear. **The most robust approach is to use only ASCII/LaTeX labels and avoid font dependencies entirely.**

---

## Workflow 2: Design (Lookup-Table Sizing)

### Core Idea of the gm/ID Methodology

**gm/ID (transconductance efficiency) is the pivot quantity linking circuit specifications to device dimensions.**

Traditional design relies on long-channel model equations (gm = 2Id/Vov) to compute device sizes; errors are severe in advanced nodes (≤ 180 nm). The gm/ID method abandons equations in favor of simulation-generated design charts (lookup tables), using gm/ID as the single independent variable to express all key device performance parameters:

```
gm/ID  ──►  Id/W   (current-density curve → determines W)
       ──►  fT     (transit frequency → determines speed)
       ──►  gm·ro  (intrinsic gain → determines gain ceiling)
       ──►  Vgs    (uniquely determines the bias point)
```

All four curves are **independent of transistor width W** — devices of different W share exactly the same Id/W, fT, and gm·ro values at the same gm/ID point. This is the foundation of the methodology: the design chart needs to be generated only once (at unit width), and it applies directly to any W.

**gm/ID is the trade-off axis for three design objectives:**

| Design priority | Direction of gm/ID | Reason |
|----------------|:-----------------:|--------|
| High speed (fT↑) | Low gm/ID (strong inversion) | High Vov → fast |
| High gain (gm·ro↑) | High gm/ID (weak/moderate inversion) | Closer to subthreshold |
| Low power (Id↓, same W) | High gm/ID | Id/W decreases as gm/ID increases |
| Minimum area (W↓, same Id) | Low gm/ID | Id/W decreases as gm/ID increases |

> Note: area and power optimization point in opposite directions — this is the central trade-off in gm/ID design.

---

### Design Flow (Five Steps)

```
① Choose topology → ② Set L → ③ Choose gm/ID → ④ Derive gm / Id → ⑤ Look up Id/W → get W
```

**① Choose topology**
Select the circuit structure (common-source, differential pair, cascode, common-gate, etc.) based on gain, bandwidth, and swing requirements.

**② Set channel length L**
- Need high speed (high fT) → choose minimum L
- Need high gain (high gm·ro) → increase L moderately (each doubling of L raises gm·ro by roughly 2–4×, with a corresponding fT reduction)
- Verify feasibility first: `tbl.lookup('gmro', gmid_target)` to check the upper bound; if unsatisfied, increase L before considering cascode or multi-stage topologies
- With a PMOS load, also verify PMOS ro: effective gain = gm_n × (ro_n ∥ ro_p)

**③ Choose gm/ID**
Select the trade-off point on the fT–gm/ID and gm·ro–gm/ID curves based on the design priority:
```python
tbl = GmIdTable('nmos45hp', W=1.0, L=0.045, vds=0.5)

# Check boundary values before deciding
print(f"fT   @ gmid=6  : {tbl.lookup('ft',   6.0)/1e9:.1f} GHz")
print(f"fT   @ gmid=15 : {tbl.lookup('ft',  15.0)/1e9:.1f} GHz")
print(f"gmro @ gmid=6  : {tbl.lookup('gmro',  6.0):.1f}")
print(f"gmro @ gmid=15 : {tbl.lookup('gmro', 15.0):.1f}")
```

**④ Derive the required gm from circuit specs, then compute Id**
```python
# Example: BW and gain constraints → gm (ro-aware, see design example section)
Rout = 1 / (2 * 3.14159 * BW * CL)   # RL∥ro, set by bandwidth
gm   = Av / Rout                       # set by gain
Id   = gm / gmid                       # set by gm/ID
```

**⑤ Look up Id/W to get W, round to 100 nm grid**
```python
id_w    = tbl.lookup('id_w', gmid)              # uA/um (W-independent)
W_exact = Id / (id_w * 1e-6)                   # um
W       = round(W_exact / 0.1) * 0.1           # round to 100 nm
# W     = math.ceil(W_exact / 0.1) * 0.1       # or round up (conservative margin)
```

After rounding, recompute Id = W × id_w and verify Av and BW; a ΔW < 5% deviation is usually negligible.

---

### API Reference: `GmIdTable`

```python
from design_gmoverid import GmIdTable, print_op

# First call: runs ngspice automatically and caches to logs/cache/ (JSON)
# Subsequent calls: reads from cache, ~0.05 s
tbl = GmIdTable('nmos180', W=10.0, L=0.18, vds=0.9)
```

**Constructor parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model` | str | — | Key in `MODEL_INFO`, e.g. `'nmos180'`, `'pmos45hp'` |
| `W` | float | — | Simulation reference width [um] (results are W-independent; any value works) |
| `L` | float | — | Channel length [um] |
| `vds` | float | VDD/2 | Fixed Vds (NMOS) or \|Vsd\| (PMOS) during Vgs sweep [V] |
| `force_resim` | bool | False | If `True`, ignores cache and re-runs simulation |

**Single-quantity lookup (W-independent, depends only on gm/ID):**

```python
tbl.lookup('id_w', gmid)   # Id/W [uA/um]  <- use this to compute W
tbl.lookup('ft',   gmid)   # transit frequency fT [Hz]
tbl.lookup('gmro', gmid)   # intrinsic gain gm·ro
tbl.lookup('vgs',  gmid)   # Vgs (or |Vsg|) [V]  <- bias point
tbl.lookup('vov',  gmid)   # overdrive voltage Vov [V]
tbl.lookup('gm',   gmid)   # transconductance [S] (at reference width W)
```

**Sizing: fix gm/ID + one constraint**

```python
op = tbl.size(gmid=15.0, Id=100e-6)   # given Id, solve for W
op = tbl.size(gmid=15.0, W=20.0)      # given W, solve for Id
op = tbl.size(gmid=15.0, gm=1.5e-3)   # given gm, solve for Id and W
print_op(op)
```

**Constrained sizing: auto-search (highest gm/ID = lowest current)**

```python
op = tbl.size_from_ft(8e9,  W=20.0)    # fT >= 8 GHz, fixed W
op = tbl.size_from_gmro(35, Id=50e-6)  # gm·ro >= 35, fixed Id
```

- `size_from_ft`: suited for known-width, speed-constrained scenarios (LNA transconductor, OTA GBW)
- `size_from_gmro`: suited for high-gain stages (prefer fixing W to avoid excessively large W in weak inversion)

**Keys returned by `size()`:**
```
model, L_um, W_um, Id_A, Vgs_V, Vov_V, gmid, gm_S, ft_Hz, gmro, id_w_Apm
```

---

### Typical gm/ID Design Parameters by Node

**nmos180 (Vds = 0.9 V, L = 180 nm)**

| gm/ID [V⁻¹] | Id/W [uA/um] | fT [GHz] | gm·ro | Typical use |
|:-----------:|:------------:|:--------:|:-----:|-------------|
|  5–8  | 42–81 | 20–25 | 27–36 | High-speed circuits, sampling switches |
| 10–12 | 20–29 | 15–18 | 39    | OTA output stage, drivers |
| 13–16 | 8–17  |  9–13 | 39–46 | OTA input differential pair (balanced) |
| 18–20 |  3–6  |  4–6  | 53    | Low-power analog, voltage references |

**nmos45hp / nmos22hp (HP, minimum L)**

| Node | gm/ID [V⁻¹] | Id/W [uA/um] | fT [GHz] | gm·ro | Notes |
|------|:-----------:|:------------:|:--------:|:-----:|-------|
| 45 nm HP | 6–10 | 150–300 | 200–400 | 6–8 | Strong CLM, low gain — ro must be considered |
| 22 nm HP | 6–10 | 200–500 | 400–700 | 3–4 | Very strong DIBL, extremely low gain |

> Vds has a minor effect on Id/W (advanced nodes have lower output impedance): ignore it during initial design, then fine-tune after simulation.

---

## Design Example: 45 nm HP Common-Source Amplifier

**Specifications** (from textbook §5.2.1, 40 nm process, using PTM 45 nm HP as surrogate model):

| Specification | Value |
|---------------|-------|
| VDD | 1.1 V |
| Low-frequency voltage gain Av | 2 (linear, i.e. 6 dB) |
| −3 dB bandwidth BW | 100 MHz |
| Load capacitance CL | 10 pF |
| Total current Id | ≤ 2 mA |
| Channel length L | 45 nm (minimum gate length) |
| Design target | gm/ID = 10 V⁻¹ (balanced speed vs. power) |

### 1. Derive Design Constraints (ro-aware)

The gain equation includes the ro term and cannot be neglected:

```
|A_DC| = gm·(RL ∥ ro)

1/|A_DC| = 1/(gm·RL) + 1/(gm·ro)

=> gm·RL = 1 / (1/Av − 1/(gm·ro))
```

For 45 nm HP, intrinsic gain gm·ro ≈ 7 (confirmed via `tbl.lookup('gmro', gmid)`). Substituting:

```
gm·RL = 1 / (1/2 − 1/7) ≈ 2.80
```

Bandwidth determines the total output-node impedance (RL ∥ ro), i.e. the actual Rout:

```
Rout = RL ∥ ro = 1 / (2pi × BW × CL)
     = 1 / (2pi × 100 MHz × 10 pF) ≈ 159 Ohm

gm = Av / Rout = 2 / 159 ≈ 12.6 mA/V

RL = gm·RL / gm = 2.80 / 12.6 mS ≈ 222 Ohm
```

> **Why not simply set RL = Rout?** Rout = 159 Ω is RL∥ro, not RL itself. RL must be larger than Rout and is back-calculated from the gain equation using the gm·ro term.

### 2. Size with GmIdTable

```python
from design_gmoverid import GmIdTable
import math

VDD = 1.1;  Av = 2.0;  BW = 100e6;  CL = 10e-12

tbl = GmIdTable('nmos45hp', W=1.0, L=0.045, vds=0.5)

gmid = 10.0
gmro = tbl.lookup('gmro', gmid)   # => 7.11
id_w = tbl.lookup('id_w', gmid)   # => 155.4 uA/um
vgs  = tbl.lookup('vgs',  gmid)   # => 0.499 V  (bias Vgs)
vov  = tbl.lookup('vov',  gmid)   # => 0.244 V

# Step 1: derive gm and RL (ro-aware)
Rout   = 1 / (2 * 3.14159 * BW * CL)   # 159 Ohm = RL||ro
gm_RL  = 1 / (1/Av - 1/gmro)           # 2.80 (gain constraint including ro)
gm     = Av / Rout                      # 12.6 mA/V
RL     = gm_RL / gm                     # 222 Ohm

# Step 2: compute Id and W
Id      = gm / gmid                     # 1.26 mA
W_exact = Id / (id_w * 1e-6)           # 8.09 um
W       = round(W_exact / 0.1) * 0.1   # => 8.1 um (100 nm grid)

# Step 3: verify with rounded W
Id_r  = W * id_w * 1e-6                # 1.259 mA
gm_r  = Id_r * gmid                    # 12.59 mA/V
ro_r  = gmro / gm_r                    # 565 Ohm
Av_r  = gm_r * (RL * ro_r / (RL + ro_r))  # 2.00 ✓
Vd_DC = VDD - Id_r * RL                # 0.821 V  (margin 577 mV >> Vov 244 mV ✓)
```

### 3. Design Summary

| Parameter | Value |
|-----------|-------|
| gm/ID | 10 V⁻¹ |
| **W / L** | **8.1 um / 45 nm** |
| Id | 1.26 mA (< 2 mA ✓) |
| gm | 12.6 mA/V |
| gm·ro | 7.11 |
| RL | 222 Ohm |
| Av (verified) | 2.00 ✓ |
| Vgs (bias) | 0.499 V |
| Vd_DC | 0.821 V |

### 4. Post-Design Simulation (hand off to ngspice skill)

With W, RL, and Vgs in hand, use the `ngspice` skill to build a `.control` block netlist and simulate:

- **DC operating point**: verify `@m1[id]`, `@m1[gm]`, `@m1[gds]` against design values
- **AC frequency response**: `ac dec 200 1e5 1e10` → read `vdb(vout)` → verify low-frequency gain and −3 dB frequency
- **Plotting**: save frequency-gain data with `wrdata`, plot a Bode magnitude response using matplotlib

---

## Self-Validation

This skill can verify its own simulation output against semiconductor physics
without any external reference.  Run from the project working directory:

```bash
python validate_gmoverid.py [model] [L_um]
python validate_gmoverid.py                    # nmos180 @ 180 nm
python validate_gmoverid.py nmos45hp 0.045
```

Five tests are executed automatically and each prints PASS / FAIL:

| # | Test | What a failure means |
|---|------|----------------------|
| 1 | Weak-inversion limit — peak gm/ID in [25, 32] V^-1 | gm extraction error near Id ≈ 0 |
| 2 | ID/W strict monotonicity (zero non-monotone steps) | Interpolation oscillation in gm or Id |
| 3 | L-doubling scaling of gm·ro (×1.5–5) and fT (×0.15–0.70) | Model ignores CLM or capacitance grows unexpectedly |
| 4 | fT × gm/ID product peaks at gm/ID in [8, 18] V^-1 | Cgg or gm mismatch vs physics |
| 5 | gm·ro changes ≥ 10 % when Vds sweeps from 0.25·VDD to 0.75·VDD | Model ignores channel-length modulation |

For the physics derivation and failure-diagnosis guidance behind each threshold,
see `references/validation.md`.

---

## Reference Documents

See `references/conventions.md` for full details:
- §1–5  Project structure, symbol conventions, MODEL_INFO, netlist templates, data-dict keys
- §6–7  Sweep configuration constants (NODE_CFG), plotting conventions and figure list
- §8–9  Physical sanity-check values, common errors and fixes
- §10   Extending the skill (new nodes, new plot types, new channel lengths)
- §11   Full design API reference (GmIdTable, print_op, cache naming, unit conventions)
