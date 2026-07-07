# Sky130A Examples

This directory keeps Sky130A examples grouped by circuit.

Each circuit folder contains:

- `circuit.scs` / `circuit.spi`: the circuit or subcircuit.
- `tb.scs` / `tb.spi`: a standalone ngspice-runnable testbench.

Circuits:

- `ring_oscillator/`
- `ota-5t/`
- `amp-2s-miller/`

Run a direct ngspice example:

```bash
cd sky130-pdk
export PDK_ROOT="$(volare path)/volare/sky130/versions/$(volare output --pdk sky130)"
cd examples/ring_oscillator
ngspice -b tb.spi
```

Convert and run a Spectre-style testbench:

```bash
cd sky130-pdk
python3 assets/scs_sky130_to_ngspice_sky130.py examples/ring_oscillator/tb.scs \
  -o /tmp/ring_oscillator_tb.spi
ngspice -b /tmp/ring_oscillator_tb.spi
```
