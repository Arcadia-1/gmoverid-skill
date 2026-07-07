---
name: sky130-pdk
description: "Sky130A open PDK workflow for ngspice-based analog simulation. Use when an agent needs to install or locate Sky130A via Volare/open_pdks, run process-corner PVT simulations, run process Monte Carlo or mismatch-aware smoke tests, instantiate sky130_fd_pr devices, or validate Sky130A examples such as MOS Id-Vgs, ring oscillators, and five-transistor OTAs."
---

# Sky130A PDK Skill

Use this skill for Sky130A ngspice work with the open-source SkyWater/open_pdks PDK. It covers PDK installation, model-path discovery, process corners, process Monte Carlo, and small smoke examples.

Do not commit the PDK data itself. The `sky130A/` runtime tree is installed outside the project, usually through Volare.

## Quick Start

Install the PDK with Volare:

```bash
python3 -m pip install --user volare
export PATH="$HOME/.local/bin:$PATH"
volare enable --pdk sky130 c6d73a35f524070e85faff4a6a9eef49553ebc2b
```

Run smoke examples from the skill directory:

```bash
cd sky130-pdk
python3 assets/run_sky130_mos_iv_pvt_mc.py
python3 assets/run_sky130_ringosc_pvt_mc.py
python3 assets/run_sky130_five_transistor_ota_pvt_mc.py
```

Each script also accepts:

```bash
--pdk-root <path-containing-sky130A-or-sky130A-itself>
--workdir <output-directory>
--mc-runs <N>
--jobs <parallel-ngspice-jobs>
```

Run direct ngspice examples:

```bash
export PDK_ROOT="$(volare path)/volare/sky130/versions/$(volare output --pdk sky130)"
cd examples/ota-5t
ngspice -b tb.spi
```

## Model Entry

Prefer the continuous model library for PVT/Monte Carlo smoke:

```text
sky130A/libs.tech/combined/continuous/sky130.lib.spice
```

Use `.lib` sections:

```spice
.lib ".../sky130.lib.spice" tt
.lib ".../sky130.lib.spice" ff
.lib ".../sky130.lib.spice" ss
.lib ".../sky130.lib.spice" fs
.lib ".../sky130.lib.spice" sf
.lib ".../sky130.lib.spice" mc
```

Common primitive devices:

```spice
Xn d g s b sky130_fd_pr__nfet_01v8 l=0.15 w=1.0 nf=1
Xp d g s b sky130_fd_pr__pfet_01v8 l=0.15 w=2.0 nf=1
```

The continuous Sky130 models use micron-valued `l` and `w` parameters in these examples.

## Included Smoke Examples

- `run_sky130_mos_iv_pvt_mc.py`: NMOS Id-Vgs smoke across `tt/ff/ss/fs/sf` plus MC current spread.
- `run_sky130_ringosc_pvt_mc.py`: three-stage CMOS ring oscillator PVT/MC frequency smoke.
- `run_sky130_five_transistor_ota_pvt_mc.py`: five-transistor OTA low-frequency AC gain PVT/MC smoke.
- `examples/`: three circuit folders, each with `circuit.scs/.spi` and a standalone `tb.scs/.spi`.

The ring oscillator and OTA examples belong in this skill because they are Sky130A PDK smoke/application examples. They are not generic ngspice tutorials and should not be placed in the PTM transistor-model library.

## Sky130 SCS To ngspice Sky130

ngspice does not parse full Spectre `.scs` syntax. This skill includes a small Sky130-oriented converter for user circuit netlists:

Use `--fragment` when converting a user circuit/subcircuit file that will be
included by another testbench. Fragment mode suppresses the auto-inserted model
library, control block, and final `.end`:

```bash
python3 assets/scs_sky130_to_ngspice_sky130.py examples/ring_oscillator/circuit.scs \
  --fragment -o /tmp/ring_oscillator.spi
```

The converter intentionally supports only a practical subset: `parameters`, `include ... section=`, local `.scs` includes, `options`, `subckt`/`ends`, Sky130 subcircuit instances, `vsource`/`isource`, `vcvs`, R/C/L passives, `save`, `ic`, `measure`/`meas`, simple `tran`/`dc`/`ac`/`noise` analyses, and basic ngspice `.control` pass-through. It does not translate the Sky130 PDK model files themselves; output netlists reference the installed ngspice model library.

Standalone examples are in `examples/`:

- `ring_oscillator/circuit.scs` plus `ring_oscillator/tb.scs`.
- `ota-5t/circuit.scs` plus `ota-5t/tb.scs`.
- `amp-2s-miller/circuit.scs` plus `amp-2s-miller/tb.scs`.

Convert a standalone Spectre-style testbench directly:

```bash
python3 assets/scs_sky130_to_ngspice_sky130.py examples/ota-5t/tb.scs -o /tmp/ota-5t_tb.spi
ngspice -b /tmp/ota-5t_tb.spi
```

## References

Read these only when needed:

- `references/installation.md`: installing Volare/Sky130A and locating `PDK_ROOT`.
- `references/ngspice-corners.md`: ngspice `.lib` sections, PVT/MC usage, and troubleshooting.
- `references/five-transistor-ota-testbenches.md`: guidance for extending the included OTA smoke bench.
