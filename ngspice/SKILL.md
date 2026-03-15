---
name: ngspice
description: "ngspice simulation tutorial and template skill. Provides nine standard simulation examples: (1) Transient — RC charging voltage and current; (2) DC — NMOS Id-Vds family curves; (3) AC — RC low-pass filter frequency response; (4) Noise — RC filter output noise spectral density and kT/C; (5) Transient — sample-and-hold switch comparison; (6) Transient — kT/C noise time-domain statistical measurement; (7) DC — NMOS current mirror output characteristics; (8) AC — common-source amplifier frequency response; (9) DC — transmission gate on-resistance. Built-in PTM 180/45/22nm models included."
---

# ngspice Simulation Skill

> **Important — do not modify skill files during normal use.**
> All new scripts, netlists, simulation outputs, and plots should go into the
> user's **project working directory** (outside `.claude/`).  Do not modify
> the skill's `assets/` folder or `SKILL.md`.  Only edit skill-internal files
> when the user explicitly asks to improve or extend the skill itself.

**Dependencies:** system-installed `ngspice`, Python 3 with `numpy`, `matplotlib`, `scipy`.

---

## Prerequisites & Installation

### Installing ngspice

**Windows**

Option A — official installer (recommended):
1. Download the latest installer from https://ngspice.sourceforge.io/download.html
2. Run the installer; note the install path (e.g. `C:\Program Files\ngspice\bin`)
3. Add that `bin` folder to your system PATH:
   - Search "environment variables" → Edit the system environment variables → Environment Variables → select `Path` → Edit → New → paste the path

Option B — Chocolatey:
```
choco install ngspice
```

Option C — winget:
```
winget install ngspice
```

> **Windows note:** the installer provides two executables: `ngspice.exe` (opens a console window) and `ngspice_con.exe` (console-subsystem, no popup window — preferred for scripted use). The skill's `find_ngspice()` automatically prefers `ngspice_con` when it is on PATH.

Option D — 中国网络环境 / winget 不可用时的替代方案：

在中国网络环境下，winget 源连接可能失败（`0x8a15000f`），Chocolatey 未预装，SourceForge 下载页面重定向也会导致工具无法直接下载。以下方法通过获取直链 + curl 下载 7z 包 + Python 解压来完成安装。

1. 获取真实下载直链：
```bash
curl -s -L -I "https://sourceforge.net/projects/ngspice/files/ng-spice-rework/45.2/ngspice-45.2_64.7z/download" 2>&1 | grep -i "location"
```
输出中最后一个 `location:` 即为直链，形如 `https://twds.dl.sourceforge.net/project/ngspice/ng-spice-rework/45.2/ngspice-45.2_64.7z?viasf=1`（`twds` 为台湾镜像，从中国大陆访问速度较快）。

2. 用 curl 下载（约 9.8 MB）：
```bash
curl -L -o ngspice-45.2_64.7z "https://twds.dl.sourceforge.net/project/ngspice/ng-spice-rework/45.2/ngspice-45.2_64.7z?viasf=1"
```

3. 用 Python 解压（系统无 7-Zip 时的替代方案）：
```bash
pip install py7zr
python -c "
import py7zr, pathlib
out = pathlib.Path('ngspice')
out.mkdir(exist_ok=True)
with py7zr.SevenZipFile('ngspice-45.2_64.7z', 'r') as z:
    z.extractall(path=str(out))
print('done')
"
```
解压后结构：`ngspice/Spice64/bin/ngspice.exe` 和 `ngspice_con.exe`。

4. 将 bin 目录加入当前 shell 的 PATH：
```bash
export PATH="$(pwd)/ngspice/Spice64/bin:$PATH"
ngspice_con -v   # 验证：应输出 ngspice-45.2
```
若需永久生效，将该路径加入系统环境变量（控制面板 → 系统 → 高级系统设置 → 环境变量 → Path）。

> **安装说明请阅读** `H:\gmoverid-skill\ngspice\SKILL.md`

**macOS**
```bash
brew install ngspice
```

**Ubuntu / Debian**
```bash
sudo apt install ngspice
```

**Fedora / RHEL**
```bash
sudo dnf install ngspice
```

---

### Verifying the Installation

**From the terminal** — check the executable is on PATH and print its version:
```bash
ngspice -v          # most platforms
ngspice_con -v      # Windows (preferred)
```

Expected output (version number will vary):
```
ngspice-44 : Circuit level simulation program
```

**From Python** — `ngspice_common.py` provides `check_ngspice()` for a one-shot pre-flight check. Run it once after installing to confirm everything is working:
```python
from ngspice_common import check_ngspice
check_ngspice()     # prints version, or exits with install instructions
```

**Quick smoke test** (simplest simulation, good for confirming the install end-to-end):
```bash
python run_tran_rc_charging.py
# Expected: ngspice runs, plots/tran_rc_charging.png is created
```

---

### PATH Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `ngspice: command not found` | Not installed or not on PATH | Install ngspice; add bin dir to PATH |
| Script hangs at simulation step | `ngspice` found but wrong binary (GUI mode) | Use `ngspice_con` on Windows, or ensure `-b` flag works |
| `UnicodeEncodeError` on Windows | GBK console encoding | Set `PYTHONUTF8=1` before running |
| Plots not created, exit code ≠ 0 | ngspice ran but netlist failed | Check `logs/` for the simulation log |

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

## Example 1: Transient — RC Charging

**Circuit:** R + C to ground, 1V DC step input, initial Vcap = 0.

**Configurations:**

| Config | R | C | τ = RC |
|--------|---|---|--------|
| 1 | 1 kΩ | 1 pF | **1 ns** |
| 2 | 10 kΩ | 1 pF | **10 ns** |

**Simulation:** `.tran` to 10τ (slow config), UIC + IC=0.

**Output:** `plots/tran_rc_charging.png` (top panel: voltage; bottom panel: current).

**Sanity checks:**
- V(out) = Vin × (1 − e^(−t/τ)); reaches 63.2% at t = τ
- I = Vin/R × e^(−t/τ); initial current = 1V/1kΩ = 1mA (or 100µA for 10kΩ)
- Capacitor essentially fully charged (>99%) after 5τ

**Files:** `tran_rc_charging.cir.tmpl` → `simulate_tran_rc_charging.py` → `plot_tran_rc_charging.py` → `run_tran_rc_charging.py`

---

## Example 2: DC — NMOS Id-Vds Family Curves

**Circuit:** PTM 180nm NMOS, W=10µm, L=0.18µm.

**Simulation:** `.dc Vds 0 1.8 0.01`, Vgs = {0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8} V.

**Output:** `plots/nmos_dc_iv.png`.

**Sanity checks:**
- Vgs = 0.4V (near Vth ≈ 0.4V): Id ≈ 59 µA (near threshold / weak inversion)
- Vgs = 0.6V, Vds = 0.9V (saturation): Id ≈ 561 µA, Id/W ≈ 56 µA/µm
- Vgs = 1.0V, Vds = 0.9V (saturation): Id ≈ 2.45 mA, Id/W ≈ 245 µA/µm
- Saturation region clearly visible (curves flatten for Vds > Vgs − Vth)

**Files:** `dc_nmos_iv.cir.tmpl` → `simulate_dc_nmos_iv.py` → `plot_dc_nmos_iv.py` → `run_dc_nmos_iv.py`

---

## Example 3: AC — RC Low-Pass Filter Bandwidth

**Circuit:** R + C to ground, AC source amplitude 1V.

**Configurations:**

| Config | R | C | fc = 1/(2πRC) |
|--------|---|---|--------------|
| 1 | 1 kΩ  | 1 pF | **159.2 MHz** |
| 2 | 10 kΩ | 1 pF | **15.92 MHz** |

**Simulation:** `.ac dec 100 1Meg 10G`.

**Output:** `plots/rc_ac_bw.png` (top panel: gain).

**Sanity checks:**
- −3 dB point matches theoretical fc: 159.2 MHz (1kΩ), 15.92 MHz (10kΩ)
- Roll-off above fc: −20 dB/decade (first-order filter)
- Low-frequency gain = 0 dB

---

## Example 4: Noise — RC Filter Output Noise

**Circuit:** same as AC example (R + C to ground).

**Simulation:** `.noise v(out) Vin dec 100 1Meg 10G`.

**Output:** `plots/rc_ac_bw.png` (bottom panel: noise spectral density).

**Sanity checks:**
- White noise floor = √(4kTR): **4.07 nV/√Hz** (R=1kΩ), **12.87 nV/√Hz** (R=10kΩ)
- Integrated noise = √(kT/C): **64.3 µVrms** (C=1pF) — classic kT/C noise
- Noise bandwidth = π/2 × fc (first-order filter)
- Noise rolls off at −20 dB/decade above fc

> AC and noise share a single entry script `run_ac_rc_filter.py` (same circuit, natural teaching flow).

---

## Example 5: Transient — Sample-and-Hold Switch Comparison

**Circuit:** NMOS switch (180nm, W=4µm) + Csamp=1pF, 10MHz sinusoidal input, 100MHz clock.

**Simulation:** `.tran 0.1n 250n`.

**Output:** `plots/sample_hold_compare.png`.

**Model comparison:**

| Model | Ron | Characteristics |
|-------|-----|----------------|
| 180nm NMOS | ~400 Ω | real parasitics |
| Ideal switch SPICE subckt | 50 Ω | no parasitics |

**Sanity checks:**
- Hold voltage remains flat during switch OFF (1pF capacitor charge conservation)
- 180nm NMOS Ron ≈ 400Ω → acquisition time constant τ = Ron × C = 400 × 1p = 0.4 ns
- Clock feedthrough (ΔV = Cov/Csamp × Vclk) visible as small step at clock edges
- Ideal switch shows no clock feedthrough or charge injection

**Files:** `tran_sample_hold_nmos/ideal.cir.tmpl` → `simulate_tran_sample_hold.py` → `plot_tran_sample_hold.py` → `run_tran_sample_hold.py`

---

## Example 6: Transient — kT/C Noise Time-Domain Statistics

**Circuit:** noisy R (400Ω, equivalent switch Ron) + Csamp; DC input 0.9V. A `trnoise` voltage source injects thermal noise into the resistor.

**Principle:** Resistor thermal noise density 4kTR, bandwidth-limited by RC, gives capacitor noise variance = kT/C. Sample v(out) every 5τ over a long transient to obtain 10000 independent samples.

**Configurations:**

| Csamp | τ = RC | √(kT/C) theoretical |
|-------|--------|---------------------|
| 1 pF   | 0.4 ns  | **64.3 µVrms** |
| 100 fF | 0.04 ns | **203.5 µVrms** |

**Output:** `plots/tran_ktc_noise_hist.png` (noise trace + histogram + fitted Gaussian + statistics summary).

**Sanity checks:**
- 1 pF: measured σ ≈ 64 µV (±10% statistical variation)
- 100 fF: measured σ ≈ 203 µV (±10% statistical variation)
- Histogram is Gaussian; fitted curve matches theoretical √(kT/C)
- Measured/theoretical ratio in [0.85, 1.15]

**Files:** `tran_ktc_noise.cir.tmpl` → `simulate_tran_ktc_noise.py` → `plot_tran_ktc_noise.py` → `run_tran_ktc_noise.py`

---

## Example 7: DC — NMOS Current Mirror Output Characteristics

**Circuit:** PTM 180nm NMOS 1:1 current mirror; M1 diode-connected (reference), M2 output.

**Parameters:** W=10µm, L=0.5µm (longer channel for better matching), Iref=100µA.

**Simulation:** `.dc Vout 0 1.8 0.01`.

**Output:** `plots/dc_current_mirror.png` (Iout vs Vout + mirror ratio).

**Sanity checks:**
- Vout > Vov (≈0.2V), M2 in saturation: Iout ≈ 100 µA
- Channel-length modulation causes Iout to increase slightly with Vout (slope ≈ 1/ro)
- Output resistance ro ≈ VA/Id ≈ 50–100 kΩ
- Vout < Vov: M2 enters triode, Iout < Iref

**Files:** `dc_current_mirror.cir.tmpl` → `simulate_dc_current_mirror.py` → `plot_dc_current_mirror.py` → `run_dc_current_mirror.py`

---

## Example 8: AC — Common-Source NMOS Amplifier Frequency Response

**Circuit:** PTM 180nm NMOS common-source amplifier with resistive load and load capacitance.

**Parameters:** W=10µm, L=0.18µm, Vgs=0.6V, Rd=2kΩ, CL=1pF, VDD=1.8V.

**Simulation:** `.ac dec 100 1k 100G`.

**Output:** `plots/ac_cs_amp_bode.png` (gain Bode plot + phase).

**Sanity checks:**
- DC gain |Av| = gm × Rd ≈ 12.9 dB
- −3 dB frequency ≈ 132 MHz (theoretical 1/(2πRdCL) ≈ 80 MHz; higher in practice due to MOSFET parasitic capacitance)
- Low-frequency phase ≈ 180° (inverting amplifier)
- High-frequency roll-off at −20 dB/decade (single pole)

**Files:** `ac_cs_amp.cir.tmpl` → `simulate_ac_cs_amp.py` → `plot_ac_cs_amp.py` → `run_ac_cs_amp.py`

---

## Example 9: DC — Transmission Gate On-Resistance

**Circuit:** NMOS + PMOS complementary transmission gate, W/L=100, fully on (clk=VDD, clkb=0).

**Method:** Apply 10mV across the gate, sweep Vpass; Ron = 10mV / I.

**Technology node comparison:**

| Node | VDD | L | W | Model |
|------|-----|---|---|-------|
| 180nm   | 1.8V | 0.18µm | 18µm  | PTM BSIM3v3 |
| 45nm HP | 1.0V | 45nm   | 4.5µm | PTM BSIM4   |
| 22nm HP | 0.8V | 22nm   | 2.2µm | PTM BSIM4   |

**Output:** `plots/dc_tgate_ron.png` (Ron vs Vpass, log scale, 3 curves).

**Sanity checks:**
- 180nm: min Ron ≈ 38 Ω; lowest resistance in the mid-Vpass range
- 45nm HP: min Ron ≈ 52 Ω
- 22nm HP: min Ron ≈ 103 Ω (lower VDD limits gate drive)
- Ron rises at Vpass near 0 and VDD (NMOS / PMOS turning off respectively)
- Complementary structure ensures conduction across the full Vpass range

**Files:** `dc_tgate_ron.cir.tmpl` → `simulate_dc_tgate_ron.py` → `plot_dc_tgate_ron.py` → `run_dc_tgate_ron.py`

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
