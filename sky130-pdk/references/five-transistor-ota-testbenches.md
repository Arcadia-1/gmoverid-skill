# Five-Transistor OTA Testbench Set

A five-transistor OTA with differential input and single-ended output needs fewer benches than a fully differential Miller OTA because there is no `VOP/VON` output pair and usually no CMFB loop.

Example files live under `examples/ota5_testbenches/`. Each bench has a Spectre-style `.scs` file and an ngspice `.spi` file.

For a full characterization or benchmark task, start with these six core benches:

| Testbench | Purpose |
|---|---|
| `tb_open_loop.scs` | DC operating point, open-loop differential-mode to single-ended gain, bandwidth, output noise |
| `tb_closed_loop.scs` | unity-gain or fixed-gain feedback, transient settling, slew rate, large-signal recovery |
| `tb_dm_to_se_gain.scs` | explicit differential-mode input to single-ended-output AC gain |
| `tb_common_mode_gain.scs` | input common-mode to output gain for CMRR |
| `tb_psrr_plus.scs` | VDD ripple to output gain for PSRR+ |
| `tb_psrr_minus.scs` | VSS/GND ripple to output gain for PSRR- |

Treat PVT, Monte Carlo, load sweep, bias sweep, temperature sweep, and VDD sweep as run dimensions around these benches rather than as separate bench topologies.

This skill also includes four useful run/sweep decks:

| Testbench | Purpose |
|---|---|
| `tb_output_swing.scs` | closed-loop output swing under input DC sweep |
| `tb_input_common_mode_range.scs` | output behavior across input common-mode sweep |
| `tb_load_sweep.scs` | representative AC checks at several load capacitors |
| `tb_bias_sweep.scs` | bias-voltage sweep |

Run the ngspice versions from the example directory:

```bash
cd sky130-pdk/examples/ota5_testbenches
export PDK_ROOT=/path/to/volare/sky130/versions/<commit>
ngspice -b tb_open_loop.spi
ngspice -b tb_psrr_plus.spi
```

For a lightweight PDK smoke test, the single `ota5_sky130` example is enough: it verifies that the Sky130 models load, the devices bias, and an AC gain measurement can run. Do not confuse that smoke with a full OTA benchmark.

Implementation notes:

- Decide the bias interface first. Use either a voltage-bias port such as `VBIAS`, or an ideal current-bias port such as `IBIAS`; do not mix both names in the same subcircuit contract.
- For ngspice-compatible examples, prefer explicit dependent-source feedback and balun structures over Spectre-only helper primitives.
- Raw open-loop phase is not the same as loop phase margin. Measure phase margin in a well-defined feedback loop or clearly label it as transfer-function phase.
- CMRR is `Adiff / Acm`; PSRR+ and PSRR- are the inverse of the corresponding supply-to-output gains.
