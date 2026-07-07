# Sky130A Five-Transistor OTA Testbench Examples

This directory contains Spectre-style `.scs` and ngspice `.spi` versions of common five-transistor OTA characterization testbenches.

The OTA contract is:

```text
five_transistor_ota vss vbias vdd vinn vinp vout
```

The examples use a voltage-bias port `vbias`. They are application examples for learning and smoke validation, not signoff-grade measurement decks.

Core benches:

- `tb_open_loop`: DC operating point, open-loop AC gain, noise run.
- `tb_closed_loop`: unity-gain follower transient response.
- `tb_dm_to_se_gain`: differential-mode input to single-ended output AC gain.
- `tb_common_mode_gain`: common-mode input to output gain for CMRR.
- `tb_psrr_plus`: VDD ripple to output gain.
- `tb_psrr_minus`: VSS ripple to output gain.
- `tb_output_swing`: closed-loop output swing under DC input sweep.
- `tb_input_common_mode_range`: output behavior across input common-mode sweep.
- `tb_load_sweep`: representative AC checks at several load capacitors.
- `tb_bias_sweep`: bias-voltage sweep.

Run ngspice examples from this directory:

```bash
export PDK_ROOT=/path/to/volare/sky130/versions/<commit>
ngspice -b tb_open_loop.spi
ngspice -b tb_closed_loop.spi
```

The `.scs` versions can be converted with:

```bash
python3 ../../assets/scs_sky130_to_ngspice_sky130.py tb_dm_to_se_gain.scs -o /tmp/tb_dm_to_se_gain.spi
ngspice -b /tmp/tb_dm_to_se_gain.spi
```
