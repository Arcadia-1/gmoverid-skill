---
name: transistor-models
description: "Complete PTM (Predictive Technology Model) MOSFET model library for circuit simulation, covering all nodes: bulk conventional 180/130/90/65nm, bulk HP/LP 45/32/22nm (BSIM4), and PTM-MG multi-gate FinFET 7/10/14/16/20nm (BSIM-CMG, HP + LSTP). No manual downloads required after installing this skill. Independent of the gmoverid skill — can be used directly in any ngspice/HSPICE project. Use when the user needs transistor models or SPICE models for circuit simulation, asks about process technology nodes, wants to set up a new SPICE simulation project, needs MOSFET device models for analog or digital design, or references PTM, BSIM, or FinFET models."
---

# Transistor Models Skill — Complete PTM Library

> **Important — do not modify skill files during normal use.**
> When using models, **copy** the required `.lib` files into the user's project
> directory (outside `.claude/`).  Do not modify or delete files inside the
> skill's `assets/models/` directory.  Only update the skill's internal files
> when the user explicitly asks to refresh the model library.

**Source:** All model files are from [PTM — Arizona State University (ptm.asu.edu)](https://ptm.asu.edu), free for academic research.

**Citations:**
- Bulk CMOS nodes: W. Zhao and Y. Cao, "New Generation of Predictive Technology Model for Sub-45 nm Early Design Exploration," *IEEE Trans. Electron Devices*, vol. 53, no. 11, pp. 2816–2823, Nov. 2006. doi: 10.1109/TED.2006.884077
- PTM-MG FinFET nodes: S. Sinha, G. Yeric, V. Chandra, B. Cline and Y. Cao, "Exploring sub-20nm FinFET design with Predictive Technology Models," *DAC 2012*, pp. 283–288. doi: 10.1145/2228360.2228414

---

## Directory Structure

```
assets/models/
├── bulk_cmos/              — Bulk CMOS (BSIM3v3 / BSIM4)
│   ├── ptm180.lib          — 180nm conventional
│   ├── ptm130.lib          — 130nm conventional
│   ├── ptm90.lib           — 90nm conventional
│   ├── ptm65.lib           — 65nm conventional
│   ├── ptm45hp.lib         — 45nm HP
│   ├── ptm45lp.lib         — 45nm LP
│   ├── ptm32hp.lib         — 32nm HP
│   ├── ptm32lp.lib         — 32nm LP
│   ├── ptm22hp.lib         — 22nm HP
│   └── ptm22lp.lib         — 22nm LP
└── finfet/
    ├── models              — PTM-MG library entry point (.LIB ptm{n}hp / ptm{n}lstp)
    ├── param.inc           — Shared parameters (fin_height/fin_width/lg/vdd, per node)
    ├── hp/                 — HP nodes: {7,10,14,16,20}nfet.pm / pfet.pm
    └── lstp/               — LSTP nodes: {7,10,14,16,20}nfet.pm / pfet.pm
```

---

## Model Reference

### Bulk CMOS — Conventional (BSIM3v3/BSIM4, combined NMOS+PMOS)

| File | Node | VDD | Model names |
|------|------|-----|-------------|
| `bulk_cmos/ptm180.lib` | 180nm | 1.8V | `NMOS` / `PMOS` |
| `bulk_cmos/ptm130.lib` | 130nm | 1.3V | `nmos` / `pmos` |
| `bulk_cmos/ptm90.lib`  | 90nm  | 1.2V | `nmos` / `pmos` |
| `bulk_cmos/ptm65.lib`  | 65nm  | 1.1V | `nmos` / `pmos` |

### Bulk CMOS — HP/LP (BSIM4, combined NMOS+PMOS)

| File | Node | Type | VDD | Model names |
|------|------|------|-----|-------------|
| `bulk_cmos/ptm45hp.lib` | 45nm | HP | 1.0V | `nmos` / `pmos` |
| `bulk_cmos/ptm45lp.lib` | 45nm | LP | 1.1V | `nmos` / `pmos` |
| `bulk_cmos/ptm32hp.lib` | 32nm | HP | 0.9V | `nmos` / `pmos` |
| `bulk_cmos/ptm32lp.lib` | 32nm | LP | 1.0V | `nmos` / `pmos` |
| `bulk_cmos/ptm22hp.lib` | 22nm | HP | 0.8V | `nmos` / `pmos` |
| `bulk_cmos/ptm22lp.lib` | 22nm | LP | 1.0V | `nmos` / `pmos` |

### FinFET — PTM-MG Multi-Gate (BSIM-CMG)

Entry file: `finfet/models` — select node and type via `.lib` section tag:

| Tag | Node | Type | VDD |
|-----|------|------|-----|
| `ptm20hp`   | 20nm | HP   | 0.9V  |
| `ptm16hp`   | 16nm | HP   | 0.85V |
| `ptm14hp`   | 14nm | HP   | 0.8V  |
| `ptm10hp`   | 10nm | HP   | 0.75V |
| `ptm7hp`    |  7nm | HP   | 0.7V  |
| `ptm20lstp` | 20nm | LSTP | 0.9V  |
| `ptm16lstp` | 16nm | LSTP | 0.85V |
| `ptm14lstp` | 14nm | LSTP | 0.8V  |
| `ptm10lstp` | 10nm | LSTP | 0.75V |
| `ptm7lstp`  |  7nm | LSTP | 0.7V  |

FinFET model names are `nfet` / `pfet` (subckt-wrapped); use `NFIN` to set the number of fins.

---

## ngspice Usage

### Loading a Bulk CMOS File

```spice
* Load 45nm HP (contains both nmos and pmos models)
.include "models/bulk_cmos/ptm45hp.lib"

* Instantiate NMOS
M1  drain  gate  source  bulk  nmos  W=1u  L=45n
```

### Loading a PTM-MG FinFET

```spice
* Load 7nm HP FinFET
.lib "models/finfet/models" ptm7hp

* PTM-MG model names are nfet / pfet
* Use NFIN (number of fins) instead of W
M1  drain  gate  source  bulk  nfet  NFIN=1  L=7n
```

---

## Model Type Quick Reference

| Model | ngspice LEVEL | Applicable nodes | Notes |
|-------|:------------:|-----------------|-------|
| BSIM3v3 | 8  | 180nm–250nm | Mature bulk CMOS |
| BSIM4   | 54 | 65nm–22nm   | Bulk HP/LP |
| BSIM-CMG | 72 | 7nm–20nm   | FinFET / multi-gate |

---

## Key Parameter Quick Reference

| Parameter | Meaning | Typical range |
|-----------|---------|--------------|
| `vth0` | Nominal threshold voltage [V] | NMOS: 0.3–0.5;  PMOS: −0.5 to −0.3 |
| `toxe` | Equivalent gate-oxide thickness [m] | 1–4 nm (deep submicron) |
| `u0` | Low-field mobility [m²/Vs] | NMOS: 0.03–0.05;  PMOS: 0.01–0.02 |
| `vsat` | Saturation velocity [m/s] | 1e5–2.5e5 |

Full parameter table in `references/model_params.md`.

---

## Using a Custom PDK Model

If you have your own `.lib` file (foundry PDK or measured):
1. Copy it into the project `models/` directory.
2. Verify the file was copied: `ls -la models/` and confirm the `.lib` file is present and non-empty.
3. Find the `.model` name inside the file (e.g. `.model mynmos NMOS level=54`).
4. Instantiate using that name: `M1 d g s b mynmos W=... L=...`
5. Run a quick DC operating-point check (`.op`) to verify the model loads without errors before running full simulations.
6. Configure sweep ranges based on `vth0`, `tox`, etc.
