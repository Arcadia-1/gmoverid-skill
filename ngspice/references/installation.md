# ngspice & Python — Installation Reference

This document is referenced by `ngspice_common.check_ngspice()` when ngspice is not
found, and by `SKILL.md` for all installation details.

---

## 1 — Installing ngspice

### Windows

> **Note:** the official package ships two executables:
> - `ngspice.exe` — opens a console pop-up window
> - `ngspice_con.exe` — console-subsystem binary, no pop-up (preferred for scripted use)
>
> `find_ngspice()` in `ngspice_common.py` automatically prefers `ngspice_con`.
> It also checks `<project>/ngspice/Spice64/bin/` so a portable (zip/7z) install
> works without modifying the system PATH at all.

**Option A — portable 7z (recommended for restricted networks or no-admin situations):**

Step 1: Download with curl (~9.8 MB).
In mainland-China networks the Taiwan SourceForge mirror (`twds`) is usually fast:

```bash
curl -L -o ngspice-45.2_64.7z \
  "https://twds.dl.sourceforge.net/project/ngspice/ng-spice-rework/45.2/ngspice-45.2_64.7z?viasf=1"
```

If you need to find the current direct URL first (redirects change):

```bash
curl -s -L -I \
  "https://sourceforge.net/projects/ngspice/files/ng-spice-rework/45.2/ngspice-45.2_64.7z/download" \
  2>&1 | grep -i "^location"
```

Step 2: Extract with py7zr (use a pinned version range to avoid the `pyzstd` build
error on machines without a C compiler):

```bash
pip install "py7zr>=0.11,<0.17"
```

If the default mirror fails (SSL/TLS error), try an alternative Chinese mirror:

| Mirror | Command |
|--------|---------|
| Aliyun | `pip install "py7zr>=0.11,<0.17" -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com` |
| Douban | `pip install "py7zr>=0.11,<0.17" -i http://pypi.douban.com/simple/ --trusted-host pypi.douban.com` |
| USTC   | `pip install "py7zr>=0.11,<0.17" -i https://pypi.mirrors.ustc.edu.cn/simple/` |

Then extract:

```bash
python -c "
import py7zr, pathlib
out = pathlib.Path('ngspice')
out.mkdir(exist_ok=True)
with py7zr.SevenZipFile('ngspice-45.2_64.7z', 'r') as z:
    z.extractall(path=str(out))
print('done')
"
```

Extracted layout: `ngspice/Spice64/bin/ngspice.exe` and `ngspice_con.exe`.

Step 3 (recommended): place the extracted `ngspice/` folder inside your project
directory (same level as the scripts). `find_ngspice()` will detect it automatically
— no PATH change required:

```
<project>/
├── ngspice/Spice64/bin/ngspice_con.exe   ← auto-detected
├── run_dc_nmos_iv.py
└── ...
```

Or, add the bin directory to PATH for the current shell session only:

```bash
export PATH="$(pwd)/ngspice/Spice64/bin:$PATH"
ngspice_con -v   # expected: ngspice-45.2
```

For a permanent PATH change: Control Panel → System → Advanced system settings →
Environment Variables → Path → New → paste the full `Spice64\bin` path.

---

**Option B — official installer:**

1. Download the latest `.exe` from the ngspice SourceForge page.
2. Run the installer; note the install path (e.g. `C:\Program Files\ngspice\bin`).
3. Add that `bin` folder to your system PATH:
   - Search "environment variables" → Edit the system environment variables →
     Environment Variables → select `Path` → Edit → New → paste the path.

**Option C — Chocolatey:**

```bash
choco install ngspice
```

**Option D — winget:**

```bash
winget install ngspice
```

### macOS

```bash
brew install ngspice
```

### Ubuntu / Debian

```bash
sudo apt install ngspice
```

### Fedora / RHEL

```bash
sudo dnf install ngspice
```

---

## 2 — Verifying the Installation

```bash
ngspice -v         # most platforms
ngspice_con -v     # Windows (preferred)
```

Expected output (version number varies):

```
ngspice-45 : Circuit level simulation program
```

From Python:

```python
from ngspice_common import check_ngspice
check_ngspice()    # prints version, or exits with install instructions
```

Quick smoke test (confirms end-to-end):

```bash
python run_tran_rc_charging.py
# Expected: ngspice runs, plots/tran_rc_charging.png created
```

---

## 3 — Python Dependencies

**Minimum versions:** numpy ≥ 1.20, matplotlib ≥ 3.3, scipy ≥ 1.7
(NumPy 1.x and 2.x are both supported.)

Install or upgrade:

```bash
pip install numpy matplotlib scipy
```

**`six` / `python-dateutil` error:** if matplotlib raises
`ModuleNotFoundError: No module named 'six'`, your `python-dateutil` is an old 2.x
build that requires `six`:

```bash
pip install six
# or upgrade dateutil to remove the dependency entirely:
pip install --upgrade python-dateutil
```

**pip mirror fallback** (China / restricted networks):

| Mirror | Command |
|--------|---------|
| Aliyun | `pip install numpy matplotlib scipy -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com` |
| Douban | `pip install numpy matplotlib scipy -i http://pypi.douban.com/simple/ --trusted-host pypi.douban.com` |
| USTC   | `pip install numpy matplotlib scipy -i https://pypi.mirrors.ustc.edu.cn/simple/` |

---

## 4 — PATH Troubleshooting

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| `ngspice: command not found` / `FileNotFoundError [WinError 2]` | Not installed or not on PATH | Install ngspice; or place `ngspice/Spice64/bin/` inside the project dir |
| Script hangs at simulation step | `ngspice` found but GUI mode (no `-b` support) | Use `ngspice_con` on Windows |
| `UnicodeEncodeError` on Windows | GBK console encoding | Set `PYTHONUTF8=1` before running |
| Plots not created, exit code ≠ 0 | ngspice ran but netlist failed | Check `logs/` for the simulation log |
| `export PATH` in bash not seen by Python subprocess | Git Bash / MSYS2 `export` does not persist across tool calls | Use the project-local `ngspice/Spice64/bin/` layout instead |
