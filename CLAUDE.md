# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Repo Is

Two Claude Code AI Agent Skills for analog IC design using the gm/ID methodology:

- **`gmoverid/`** — gm/ID characterization and transistor sizing. Runs ngspice simulations and produces characterization plots. Includes a `GmIdTable` design API for automated transistor sizing. Has built-in PTM models for 180/45/22nm.
- **`transistor-models/`** — A model-only skill: the complete PTM (Predictive Technology Model) library from mec.umn.edu/ptm, covering bulk 65–180nm, HP/LP 22–45nm, and PTM-MG FinFET 7–20nm. No Python scripts; pure model files.

Each skill has a `SKILL.md` (the skill prompt loaded by the agent) and an `assets/` folder with runnable scripts and model files.

## Running the gmoverid Characterization

```bash
# Deploy assets to a project directory first
cp -r gmoverid/assets/* <project>/
mkdir -p <project>/plots <project>/logs

# Run 180nm single-node (LVT/SVT/HVT + channel length sweep)
python run_gmoverid.py

# Run HP multi-node (45/32/22/16nm)
python run_multinode.py
```

On Windows, set `PYTHONUTF8=1` to avoid `UnicodeEncodeError` in GBK consoles.

**Dependencies**: `ngspice` (system-wide), Python 3 with `numpy`, `matplotlib`, `scipy`.

## Using the Design API

```python
from design_gmoverid import GmIdTable, print_op

# First call: runs ngspice and caches to logs/cache/; subsequent calls: reads cache (~0.05s)
tbl = GmIdTable('nmos180', W=10.0, L=0.18, vds=0.9)

op = tbl.size(gmid=15.0, Id=100e-6)       # fix gm/ID + drain current → solve W
op = tbl.size(gmid=15.0, W=20.0)          # fix gm/ID + width → solve Id
op = tbl.size_from_ft(5e9, W=20.0)        # fT ≥ target, highest gm/ID
op = tbl.size_from_gmro(30, Id=50e-6)     # gm·ro ≥ target, highest gm/ID
print_op(op)
```

## Architecture (gmoverid skill)

```
simulate_gmoverid.py   ← ngspice runner, data extraction, MODEL_INFO registry
plot_gmoverid.py       ← all matplotlib figures (never plt.show(); saves to plots/)
run_gmoverid.py        ← 180nm orchestration entry point
run_multinode.py       ← HP multi-node orchestration (NODE_CFG dict)
design_gmoverid.py     ← GmIdTable class + print_op()
netlist/*.cir.tmpl     ← SPICE netlist templates (str.format() placeholders)
models/*.lib           ← PTM model files
```

All paths resolve via `Path(__file__).resolve().parent` — no path configuration needed. Output goes to `plots/` and `logs/` relative to the script location.

## Key Design Patterns

**MODEL_INFO registry** (`simulate_gmoverid.py`): all supported models are registered here. Each entry has `pol`, `vth0`, `cgso`, `cgdo`, `nch`, `mu`, `file`, `vdd`, `vgs_stop`, `vds_stop`, `tox`. To add a new technology node: add `.lib` file, add entry to `MODEL_INFO`, then add to run script's `NODE_CFG` or model lists.

**NMOS/PMOS sign convention**: all sweep functions return unified keys (`vgs`, `vds`, `vov`, `id`, `id_w`) that are always positive and ascending. For PMOS, `vgs` = |Vsg|, `vds` = |Vsd|. Plotting code is polarity-agnostic.

**Netlist templates**: use Python `str.format()`. Never put `{...}` in SPICE comment lines — they will be parsed as format placeholders and raise `KeyError`.

**Simulation data flow**: `sweep_vgs/vds/vsg/vsd()` → raw data dict → `run_vgs/vds/vsg/vsd_sweeps()` → list of dicts → `plot_main/plot_iv/plot_caps()` → PNG in `plots/`.

**GmIdTable internals**: builds a lookup table from the right branch of the gm/ID vs Vgs curve (from peak gm/ID toward strong inversion). `_gmid_arr` is descending (index 0 = weak inversion). Cache files in `logs/cache/` use decimal-point-to-`p` substitution (e.g. `vgs_nmos180_W10p00_L0p1800_Vds0p900.json`).

## Reference Documents

- `gmoverid/references/conventions.md` — authoritative reference: sign conventions (§2), MODEL_INFO parameters (§3), netlist template placeholders (§4), data dict keys (§5), sweep constants (§6), plot conventions (§7), physical sanity check values (§8), common errors (§9), how to extend (§10), design API full reference (§11).
- `transistor-models/references/model_params.md` — PTM model parameter table.

## PTM Copyright

PTM models are from Arizona State University (ASU), evolved from UC Berkeley's BPTM. Free for academic research; commercial use requires permission. Cite:
- Bulk CMOS: W. Zhao and Y. Cao, *IEEE Trans. Electron Devices*, vol. 53, no. 11, pp. 2816–2823, Nov. 2006. doi: 10.1109/TED.2006.884077
- FinFET (PTM-MG): S. Sinha et al., *DAC 2012*, pp. 283–288. doi: 10.1145/2228360.2228414
