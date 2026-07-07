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

Run smoke examples from this skill's `assets/` directory:

```bash
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

The ring oscillator and OTA examples belong in this skill because they are Sky130A PDK smoke/application examples. They are not generic ngspice tutorials and should not be placed in the PTM transistor-model library.

## SCS To ngspice SPI

ngspice does not parse full Spectre `.scs` syntax. This skill includes a small Sky130-oriented converter for user circuit netlists:

```bash
python3 assets/scs130_to_ngspice.py examples/ringosc_sky130.scs -o /tmp/ringosc_sky130.spi
python3 assets/scs130_to_ngspice.py examples/ota5_sky130.scs -o /tmp/ota5_sky130.spi
```

The converter intentionally supports only a practical subset: `parameters`, `include ... section=`, `subckt`/`ends`, Sky130 subcircuit instances, `vsource`/`isource`, R/C/L passives, `save`, `ic`, and simple `tran`/`ac` analyses. It does not translate the Sky130 PDK model files themselves; output netlists reference the installed ngspice model library.

Paired examples are in `examples/`:

- `ringosc_sky130.scs` and `ringosc_sky130.spi`.
- `ota5_sky130.scs` and `ota5_sky130.spi`.

## References

Read these only when needed:

- `references/installation.md`: installing Volare/Sky130A and locating `PDK_ROOT`.
- `references/ngspice-corners.md`: ngspice `.lib` sections, PVT/MC usage, and troubleshooting.
- `references/five-transistor-ota-testbenches.md`: recommended full characterization benches for a five-transistor OTA.
