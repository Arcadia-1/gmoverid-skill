# Five-Transistor OTA Testbench Guidance

The included five-transistor OTA example is intentionally small and standalone:

```text
examples/ota-5t/
├── circuit.scs
├── circuit.spi
├── tb.scs
└── tb.spi
```

`tb.scs` and `tb.spi` run the same open-loop differential-input to single-ended-output AC smoke test. This is enough to verify that the Sky130 models load, the OTA biases, and low-frequency gain can be measured from a cloned `gmoverid-skill` checkout.

Run it directly:

```bash
cd sky130-pdk
export PDK_ROOT="$(volare path)/volare/sky130/versions/$(volare output --pdk sky130)"
cd examples/ota-5t
ngspice -b tb.spi
```

Convert the Spectre-style source and run the converted deck:

```bash
cd sky130-pdk
python3 assets/scs_sky130_to_ngspice_sky130.py examples/ota-5t/tb.scs -o /tmp/ota-5t_tb.spi
ngspice -b /tmp/ota-5t_tb.spi
```

For fuller OTA characterization, add separate benches under `examples/ota-5t/` rather than creating a second OTA directory. Useful extensions include closed-loop settling, CMRR, PSRR+, PSRR-, output swing, input common-mode range, load sweep, and bias sweep.

Implementation notes:

- Keep the OTA bias interface explicit. The included OTA uses a voltage-bias port named `vbias`.
- CMRR is `Adiff / Acm`; PSRR+ and PSRR- are the inverse of the corresponding supply-to-output gains.
- Raw open-loop phase is not the same as loop phase margin. Measure phase margin in a defined feedback loop or label it as transfer-function phase.
