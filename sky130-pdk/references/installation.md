# Sky130A Installation With Volare

This skill expects a Sky130A runtime tree produced by open_pdks. The recommended way to obtain one is Volare, which downloads prebuilt PDK packages.

## Install Volare

```bash
python3 -m pip install --user volare
export PATH="$HOME/.local/bin:$PATH"
```

Check the tool:

```bash
volare --version
```

Install ngspice with your system package manager and verify it is visible:

```bash
ngspice -v
```

## Enable Sky130

The smoke examples in this skill were verified with:

```bash
volare enable --pdk sky130 c6d73a35f524070e85faff4a6a9eef49553ebc2b
```

Volare stores the PDK under its own root. Discover it with:

```bash
volare path
volare output --pdk sky130
```

A typical final path is:

```text
~/.volare/volare/sky130/versions/<commit>/sky130A
```

## Without Volare

If the PDK is installed another way, set `PDK_ROOT` to the directory that contains `sky130A/`:

```bash
export PDK_ROOT=/path/to/pdk/root
test -f "$PDK_ROOT/sky130A/libs.tech/combined/continuous/sky130.lib.spice"
```

The smoke scripts also accept a direct `sky130A` path:

```bash
python3 assets/run_sky130_ringosc_pvt_mc.py --pdk-root /path/to/sky130A
```

## Smoke Test From A Cloned Repo

```bash
git clone https://github.com/Arcadia-1/gmoverid-skill
cd gmoverid-skill/sky130-pdk
python3 assets/run_sky130_mos_iv_pvt_mc.py --mc-runs 3
python3 assets/run_sky130_ringosc_pvt_mc.py --mc-runs 3
python3 assets/run_sky130_five_transistor_ota_pvt_mc.py --mc-runs 3
```

Run one ngspice `.spi` deck directly:

```bash
export PDK_ROOT="$(volare path)/volare/sky130/versions/$(volare output --pdk sky130)"
cd examples/ota-5t
ngspice -b tb.spi
```

## What Not To Commit

Do not commit:

```text
sky130A/
~/.volare/
GDS/LEF/lib/SPICE PDK payloads copied from the PDK
```

Commit only scripts, netlists, and documentation that locate the PDK at runtime.
