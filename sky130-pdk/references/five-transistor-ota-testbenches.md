# Five-Transistor OTA Testbench Set

A five-transistor OTA with differential input and single-ended output needs fewer benches than a fully differential Miller OTA because there is no `VOP/VON` output pair and usually no CMFB loop.

For a full characterization or benchmark task, use these six core benches:

| Testbench | Purpose |
|---|---|
| `tb_open_loop.scs` | DC operating point, open-loop differential gain, bandwidth, output noise |
| `tb_closed_loop.scs` | unity-gain or fixed-gain feedback, transient settling, slew rate, large-signal recovery |
| `tb_diff_gain.scs` | explicit differential-input to single-ended-output AC gain |
| `tb_common_mode_gain.scs` | input common-mode to output gain for CMRR |
| `tb_psrr_plus.scs` | VDD ripple to output gain for PSRR+ |
| `tb_psrr_minus.scs` | VSS/GND ripple to output gain for PSRR- |

Treat PVT, Monte Carlo, load sweep, bias sweep, temperature sweep, and VDD sweep as run dimensions around these benches rather than as separate bench topologies.

For a lightweight PDK smoke test, the single `ota5_sky130` example is enough: it verifies that the Sky130 models load, the devices bias, and an AC gain measurement can run. Do not confuse that smoke with a full OTA benchmark.

Implementation notes:

- Decide the bias interface first. Use either a voltage-bias port such as `VBIAS`, or an ideal current-bias port such as `IBIAS`; do not mix both names in the same subcircuit contract.
- For ngspice-compatible examples, prefer explicit dependent-source feedback and balun structures over Spectre-only helper primitives.
- Raw open-loop phase is not the same as loop phase margin. Measure phase margin in a well-defined feedback loop or clearly label it as transfer-function phase.
- CMRR is `Adiff / Acm`; PSRR+ and PSRR- are the inverse of the corresponding supply-to-output gains.
