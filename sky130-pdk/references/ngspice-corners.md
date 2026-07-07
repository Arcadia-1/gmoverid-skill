# Sky130A ngspice Corners and Monte Carlo

Use the continuous model library for compact PVT/MC smoke tests:

```text
sky130A/libs.tech/combined/continuous/sky130.lib.spice
```

Select process corners with `.lib`:

```spice
.lib ".../sky130.lib.spice" tt
.lib ".../sky130.lib.spice" ff
.lib ".../sky130.lib.spice" ss
.lib ".../sky130.lib.spice" fs
.lib ".../sky130.lib.spice" sf
```

Use process Monte Carlo with:

```spice
.lib ".../sky130.lib.spice" mc
```

The model library sets internal switches such as `MC_PR_SWITCH` for the `mc` section. The smoke scripts set an ngspice seed before each run:

```spice
.control
setseed 1001
run
quit
.endc
```

## Device Instantiation

For low-voltage CMOS examples:

```spice
Xn d g s b sky130_fd_pr__nfet_01v8 l=0.15 w=1.0 nf=1
Xp d g s b sky130_fd_pr__pfet_01v8 l=0.15 w=2.0 nf=1
```

The examples use micron-valued `l` and `w` because that is how the continuous Sky130 subcircuits are parameterized.

## Smoke Outputs

The assets write CSV and JSON files to `/tmp` by default. They are smoke tests, not signoff benchmarks.

Use `--jobs N` to run independent PVT/MC simulations in parallel. Keep the default at 1 unless you have measured a speedup locally; Sky130 continuous-model transient simulations can become slower or hit per-run timeouts when several ngspice processes compete for CPU.

Expected behavior:

- `ff` ring oscillator is usually faster than `ss`.
- NMOS Id at fixed VGS/VDS differs across process corners.
- MC runs show nonzero spread.
- OTA gain varies across process and MC.

If a measurement fails, inspect the per-run `.log` file in the script work directory.

## Spectre-Style Netlists

ngspice does not understand complete Spectre `.scs` syntax. For simple Sky130 user circuits, use:

```bash
python3 assets/scs_sky130_to_ngspice_sky130.py examples/ota-5t/tb.scs -o /tmp/ota-5t_tb.spi
ngspice -b /tmp/ota-5t_tb.spi
```

This converts a narrow circuit subset to ngspice `.spi`; it is not a general Spectre simulator replacement and it does not convert PDK model internals.
