# ngspice Skill — Conventions Reference

## §1 Project Structure & Path Conventions

All paths resolve via `Path(__file__).resolve().parent` — no hardcoded absolute paths.

```
assets/
├── ngspice_common.py       # shared utilities
├── verify_ngspice.py       # installation check
├── models/ptm180.lib       # PTM 180nm NMOS BSIM3v3
├── netlist/*.cir.tmpl       # templates (str.format placeholders)
├── netlist/test_rc.cir      # static netlist (verify only)
├── simulate_*.py            # simulation engines
├── plot_*.py                # plotting routines
├── run_*.py                 # entry points
├── logs/                    # auto-created
└── plots/                   # auto-created
```

Path constants from `ngspice_common.py`:
- `BASE_DIR` = script directory
- `NETLIST_DIR` = `BASE_DIR / 'netlist'`
- `MODEL_DIR` = `BASE_DIR / 'models'`
- `LOG_DIR` = `BASE_DIR / 'logs'`
- `PLOT_DIR` = `BASE_DIR / 'plots'`

## §2 ngspice Run Mode & Command Line

The `run_ngspice()` function invokes ngspice in batch mode:

```
ngspice_con -b -o <log_file> <netlist_file>
```

Key behaviors:
- `stdin=subprocess.DEVNULL` prevents interactive prompts
- Windows: `CREATE_NO_WINDOW` flag suppresses console popup
- Executable priority: `ngspice_con` (Windows console) > `ngspice`
- Default timeout: 120 seconds

## §3 Netlist Template Placeholders

Templates use Python `str.format()`. **Never put `{...}` in SPICE comment lines.**

### nmos_dc_ids.cir.tmpl
| Placeholder | Example | Description |
|-------------|---------|-------------|
| `{model_path}` | `D:/path/to/ptm180.lib` | Model include path (forward slashes) |
| `{W}` | `10.0` | Channel width [µm] |
| `{L}` | `0.18` | Channel length [µm] |
| `{vgs}` | `1.0` | Gate-source voltage [V] |
| `{vds_stop}` | `1.8` | Max drain-source voltage [V] |
| `{vds_step}` | `0.01` | DC sweep step [V] |

### rc_ac.cir.tmpl
| Placeholder | Example | Description |
|-------------|---------|-------------|
| `{label}` | `R=1kΩ, C=1pF` | Comment label |
| `{R}` | `1k` | Resistance (SPICE notation) |
| `{C}` | `1p` | Capacitance (SPICE notation) |
| `{fc_mhz}` | `159.15` | Corner frequency [MHz] |
| `{fstart}` | `1Meg` | AC sweep start frequency |
| `{fstop}` | `10G` | AC sweep stop frequency |

### rc_noise.cir.tmpl
| Placeholder | Example | Description |
|-------------|---------|-------------|
| `{label}` | `R=1kΩ, C=1pF` | Comment label |
| `{R}` | `1k` | Resistance (SPICE notation) |
| `{C}` | `1p` | Capacitance (SPICE notation) |
| `{fstart}` | `1Meg` | Noise sweep start frequency |
| `{fstop}` | `10G` | Noise sweep stop frequency |
| `{wrdata}` | `D:/path/to/noise.txt` | Output data file path |

### sample_hold_nmos.cir.tmpl
| Placeholder | Example | Description |
|-------------|---------|-------------|
| `{model_path}` | `D:/path/to/ptm180.lib` | Model include path |
| `{W}` | `4.0` | NMOS width [µm] |
| `{L}` | `0.18` | NMOS length [µm] |
| `{vdd}` | `1.8` | Supply voltage [V] |
| `{Csamp}` | `1p` | Sampling capacitor |
| `{fin}` | `10Meg` | Input signal frequency |
| `{fclk}` | `100Meg` | Clock frequency |
| `{tclk}` | `10n` | Clock period |
| `{ton}` | `2.5n` | Clock ON time (25% duty) |
| `{tstep}` | `0.1n` | Transient step |
| `{tstop}` | `250n` | Transient stop time |

### sample_hold_ideal.cir.tmpl
| Placeholder | Example | Description |
|-------------|---------|-------------|
| `{Ron_expr}` | `v(ctrl) > 0.9 ? 50 : 1G` | Voltage-controlled resistance expression |
| `{Csamp}` | `1p` | Sampling capacitor |
| `{fin}`, `{fclk}`, `{tclk}`, `{ton}`, `{tstep}`, `{tstop}` | Same as NMOS | Timing parameters |

## §4 Output Parse Formats

### `.print` tabular output (parse_print_table)
Tab-separated: `index \t value1 \t value2 ...`
```
0       0.000000e+00    1.234567e-04
1       1.000000e-02    2.345678e-04
```
Returns ndarray shape (N, n_cols).

### `wrdata` output (parse_wrdata)
Whitespace-separated two columns: `x_value  y_value`
```
1.000000e+06  4.070000e-09
1.100000e+06  4.070000e-09
```
Returns ndarray shape (N, 2).

## §5 Physical Sanity-Check Values

### DC — NMOS PTM 180nm (W=10µm, L=0.18µm)

| Condition | Expected |
|-----------|----------|
| Vth (typical) | ~0.4 V |
| Id @ Vgs=0.4V, Vds=0.9V | ~59 µA (near Vth, weak/subthreshold) |
| Id @ Vgs=0.6V, Vds=0.9V | ~561 µA, Id/W ≈ 56 µA/µm |
| Id @ Vgs=1.0V, Vds=0.9V | ~2.45 mA, Id/W ≈ 245 µA/µm |
| Saturation onset | Vds ≈ Vgs - Vth |

### AC — RC Low-Pass Filter

| Parameter | R=1kΩ, C=1pF | R=10kΩ, C=1pF |
|-----------|-------------|--------------|
| fc = 1/(2πRC) | 159.2 MHz | 15.92 MHz |
| Gain @ fc | -3 dB | -3 dB |
| Roll-off slope | -20 dB/decade | -20 dB/decade |

### Noise — RC Filter

| Parameter | R=1kΩ, C=1pF | R=10kΩ, C=1pF |
|-----------|-------------|--------------|
| Thermal noise floor √(4kTR) | 4.07 nV/√Hz | 12.87 nV/√Hz |
| Integrated noise √(kT/C) | 64.3 µVrms | 64.3 µVrms |
| Noise bandwidth | π/2 × fc | π/2 × fc |

### Transient — Sample-and-Hold (180nm NMOS)

| Parameter | Value |
|-----------|-------|
| Ron (NMOS, W=4µm) | ~400 Ω |
| Acquisition τ = Ron × Csamp | ~0.4 ns |
| Clock injection ΔV | Cov/Csamp × Vclk |
| Hold voltage droop | negligible (1pF cap) |

## §6 Common Errors & Fixes

| Symptom | Cause | Fix |
|---------|-------|-----|
| `KeyError` during template render | `{...}` in SPICE comment | Remove braces from comments |
| `ngspice: command not found` | ngspice not on PATH | Install ngspice or add to PATH |
| `UnicodeEncodeError` on Windows | GBK console encoding | Set `PYTHONUTF8=1` |
| Empty parse result (None) | Wrong log format or sim failed | Check log file, verify netlist syntax |
| Negative Id in DC results | ngspice current convention | `np.abs()` on parsed current |
| Backslash in model path on Windows | SPICE doesn't handle `\` | Use `spath()` to convert to `/` |
