---
name: ngspice
description: "ngspice circuit simulation tutorial and template skill for analog and mixed-signal design. Provides nine ready-to-run simulation examples covering transient, DC, AC, and noise analyses: RC charging, NMOS Id-Vds family curves, RC low-pass filter frequency response, noise spectral density and kT/C, sample-and-hold switch comparison, kT/C noise time-domain statistics, NMOS current mirror, common-source amplifier frequency response, and transmission gate on-resistance. Built-in PTM 180/45/22nm MOSFET models included. Use when the user wants to simulate a circuit with ngspice, run SPICE analysis, model transistor behavior, perform analog circuit simulation, generate IV curves, analyze frequency response, measure noise, or needs a netlist template for any standard simulation type."
---

# ngspice Simulation Skill

> **Important — do not modify skill files during normal use.**
> All new scripts, netlists, simulation outputs, and plots should go into the
> user's **project working directory** (outside `.claude/`).  Do not modify
> the skill's `assets/` folder or `SKILL.md`.  Only edit skill-internal files
> when the user explicitly asks to improve or extend the skill itself.

---

## Prerequisites & Installation

**Dependencies:** system-installed `ngspice`, Python 3 with `numpy ≥ 1.20`, `matplotlib ≥ 3.3`, `scipy ≥ 1.7` (NumPy 1.x and 2.x both supported).

If `ngspice` is not found when a script starts, `check_ngspice()` will print a brief
error and exit.  Full platform-specific install instructions — including a portable
Windows install that requires no PATH change, Chinese-network pip mirror fallbacks,
and `python-dateutil`/`six` troubleshooting — are in:

```
references/installation.md
```

---

```
assets/
├── ngspice_common.py                   — shared utilities: path constants, runner, parsers, template renderer
├── models/
│   ├── ptm180.lib                      — PTM 180nm BSIM3v3
│   ├── ptm45hp.lib                     — PTM 45nm HP BSIM4
│   └── ptm22hp.lib                     — PTM 22nm HP BSIM4
├── netlist/
│   ├── tran_rc_charging.cir.tmpl       — Transient: RC charging voltage and current
│   ├── dc_nmos_iv.cir.tmpl             — DC: NMOS Id-Vds family curves
│   ├── ac_rc_filter.cir.tmpl           — AC: RC low-pass frequency response
│   ├── noise_rc_filter.cir.tmpl        — Noise: RC output noise spectral density
│   ├── tran_sample_hold_nmos.cir.tmpl  — Transient: 180nm NMOS sample-and-hold
│   ├── tran_sample_hold_ideal.cir.tmpl — Transient: ideal switch sample-and-hold
│   ├── tran_ktc_noise.cir.tmpl         — Transient: kT/C noise time-domain statistics
│   ├── dc_current_mirror.cir.tmpl      — DC: NMOS current mirror
│   ├── ac_cs_amp.cir.tmpl              — AC: common-source amplifier frequency response
│   └── dc_tgate_ron.cir.tmpl           — DC: transmission gate on-resistance
├── simulate_tran_rc_charging.py        — RC charging simulation engine
├── plot_tran_rc_charging.py            — RC charging plotting
├── run_tran_rc_charging.py             — RC charging entry point
├── simulate_dc_nmos_iv.py              — DC family-curve simulation engine
├── plot_dc_nmos_iv.py                  — DC family-curve plotting
├── run_dc_nmos_iv.py                   — DC family-curve entry point
├── simulate_ac_rc_filter.py            — AC + noise simulation engine
├── plot_ac_rc_filter.py                — AC + noise plotting
├── run_ac_rc_filter.py                 — AC + noise entry point
├── simulate_tran_sample_hold.py        — sample-and-hold simulation engine
├── plot_tran_sample_hold.py            — sample-and-hold plotting
├── run_tran_sample_hold.py             — sample-and-hold entry point
├── simulate_tran_ktc_noise.py          — kT/C noise simulation engine
├── plot_tran_ktc_noise.py              — kT/C noise plotting
├── run_tran_ktc_noise.py               — kT/C noise entry point
├── simulate_dc_current_mirror.py       — current mirror simulation engine
├── plot_dc_current_mirror.py           — current mirror plotting
├── run_dc_current_mirror.py            — current mirror entry point
├── simulate_ac_cs_amp.py               — common-source amplifier simulation engine
├── plot_ac_cs_amp.py                   — common-source amplifier plotting
├── run_ac_cs_amp.py                    — common-source amplifier entry point
├── simulate_dc_tgate_ron.py            — transmission gate Ron simulation engine
├── plot_dc_tgate_ron.py                — transmission gate Ron plotting
├── run_dc_tgate_ron.py                 — transmission gate Ron entry point
├── logs/                               — simulation logs (auto-created)
└── plots/                              — output figures (auto-created)
```

**Naming convention:** netlist templates are prefixed by simulation type (`dc_`, `ac_`, `noise_`, `tran_`); Python files follow the same naming (e.g. `run_dc_nmos_iv.py`).

---

## Deployment and Running

1. Copy all files under `assets/` to the project directory.
2. Run any entry-point script:

```bash
python run_tran_rc_charging.py    # RC charging (simplest — good for verifying ngspice install)
python run_dc_nmos_iv.py          # DC family curves
python run_ac_rc_filter.py        # AC + noise
python run_tran_sample_hold.py    # sample-and-hold
python run_tran_ktc_noise.py      # kT/C noise statistics
python run_dc_current_mirror.py   # current mirror
python run_ac_cs_amp.py           # common-source amplifier
python run_dc_tgate_ron.py        # transmission gate Ron
```

On Windows, set `PYTHONUTF8=1` to avoid GBK encoding errors.

All paths resolve automatically via `Path(__file__).resolve().parent` — no configuration needed.

---

## Simulation Examples

Nine ready-to-run examples are included, each following the pattern: netlist template (`.cir.tmpl`) → simulation engine (`simulate_*.py`) → plotting (`plot_*.py`) → entry point (`run_*.py`).

| # | Type | Example | Entry point | Output plot | Key sanity check |
|---|------|---------|-------------|-------------|-----------------|
| 1 | Transient | RC charging (1kΩ/10kΩ + 1pF) | `run_tran_rc_charging.py` | `plots/tran_rc_charging.png` | V reaches 63.2% at t = τ |
| 2 | DC | NMOS Id-Vds family curves (180nm) | `run_dc_nmos_iv.py` | `plots/nmos_dc_iv.png` | Saturation region visible, Vgs=1.0V → Id ≈ 2.45mA |
| 3 | AC | RC low-pass filter bandwidth | `run_ac_rc_filter.py` | `plots/rc_ac_bw.png` (top) | −3dB at fc = 1/(2πRC); −20dB/dec roll-off |
| 4 | Noise | RC filter output noise spectral density | `run_ac_rc_filter.py` | `plots/rc_ac_bw.png` (bottom) | √(kT/C) = 64.3µVrms (1pF) |
| 5 | Transient | Sample-and-hold NMOS vs ideal switch | `run_tran_sample_hold.py` | `plots/sample_hold_compare.png` | Clock feedthrough visible in NMOS, absent in ideal |
| 6 | Transient | kT/C noise time-domain statistics | `run_tran_ktc_noise.py` | `plots/tran_ktc_noise_hist.png` | σ ≈ 64µV (1pF), Gaussian histogram |
| 7 | DC | NMOS current mirror output (180nm) | `run_dc_current_mirror.py` | `plots/dc_current_mirror.png` | Iout ≈ 100µA in saturation, CLM slope visible |
| 8 | AC | Common-source amplifier frequency response | `run_ac_cs_amp.py` | `plots/ac_cs_amp_bode.png` | |Av| ≈ 12.9dB, −3dB ≈ 132MHz |
| 9 | DC | Transmission gate Ron (180/45/22nm) | `run_dc_tgate_ron.py` | `plots/dc_tgate_ron.png` | Min Ron: 38Ω (180nm), 52Ω (45nm), 103Ω (22nm) |

> Examples 3 & 4 share a single entry script (same circuit, natural teaching flow). Example 1 is the simplest — use it to verify ngspice is installed correctly.

---

## Troubleshooting and Error Recovery

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| `ngspice: command not found` | ngspice not installed or not in PATH | See `references/installation.md` for platform-specific install instructions |
| `Error: can't open ...` in ngspice output | Model file path not resolved | Verify `models/` directory was copied alongside scripts; check `spath()` on Windows |
| Simulation hangs or takes very long | Convergence failure or step size too small | Add `.options reltol=1e-3 abstol=1e-12` to netlist; reduce sweep range |
| `KeyError` in Python template rendering | `{...}` inside SPICE comment lines | Remove or escape braces in comment lines of `.cir.tmpl` files |
| Plot shows flat lines or NaN | Simulation produced no valid data | Check `logs/` for ngspice error messages; verify netlist syntax |
| GBK encoding error on Windows | Python default encoding mismatch | Set `PYTHONUTF8=1` environment variable before running |

---

## Shared Module: ngspice_common.py

| Function / Constant | Purpose |
|---------------------|---------|
| `BASE_DIR`, `NETLIST_DIR`, `MODEL_DIR`, `LOG_DIR`, `PLOT_DIR` | Path constants via `Path(__file__).resolve().parent` |
| `strip_ansi(text)` | Remove ANSI colour codes |
| `find_ngspice()` | Prefer `ngspice_con`, fall back to `ngspice` |
| `run_ngspice(netlist, log, timeout)` | Batch-mode execution: `-b`, `stdin=DEVNULL`, Windows `CREATE_NO_WINDOW` |
| `parse_print_table(log_path)` | Parse `.print` table output → ndarray |
| `parse_wrdata(data_path)` | Parse `wrdata` two-column output → ndarray |
| `spath(p)` | `str(p).replace('\\', '/')` for netlist paths |
| `render_template(tmpl_name, **kw)` | Read `.cir.tmpl` and fill placeholders with `str.format(**kw)` |

---

## Netlist Template Conventions

- Template filenames are prefixed by simulation type: `dc_`, `ac_`, `noise_`, `tran_`
- Use Python `str.format()` placeholders: `{R}`, `{model_path}`
- **Never put `{...}` inside SPICE comment lines** — they are parsed as format placeholders and raise `KeyError`
- Convert paths with `spath()` to forward slashes (Windows compatibility)
- Temporary netlists are written to `tempfile.NamedTemporaryFile(suffix='.cir')` before execution

---

## Plotting Conventions

- Never call `plt.show()`; always use `fig.savefig(path, dpi=150, bbox_inches='tight')`
- Save figures to `plots/`
- Axis labels in ASCII + LaTeX (e.g. `$V_{DS}$`, `$I_D$`)
- Do not use Chinese characters in matplotlib labels

---

## Reference Documents

See `references/conventions.md` for full details:
- §1  Project structure and path conventions
- §2  ngspice execution modes and command-line arguments
- §3  Netlist template placeholder list
- §4  Output parsing formats
- §5  Physical sanity-check values quick reference
- §6  Common errors and fixes

See `references/installation.md` for installation details:
- §1  Windows (portable 7z, official installer, choco, winget)
- §2  Verifying the installation
- §3  Python dependencies, `six`/dateutil, pip mirror fallbacks
- §4  PATH troubleshooting table
